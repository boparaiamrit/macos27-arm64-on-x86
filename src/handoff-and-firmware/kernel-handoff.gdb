# SPDX-License-Identifier: GPL-2.0-or-later
# Experimental TCG handoff adapter; validate the selected firmware trampoline.
# Based on the public boot_args layout used by 27on86's injection utility.
python
import gdb
import json
import os
import struct
import sys

sys.path.insert(0, os.environ['HANDOFF_SCRIPT_DIR'])
from adt_no_sep import add_no_sep

port = int(os.environ['HANDOFF_GDB_PORT'])
handoff_pc = int(os.environ.get('HANDOFF_PC', '0xaca00000'), 0)
ram_base = int(os.environ.get('HANDOFF_RAM_BASE', '0x70000000'), 0)
ram_size = int(os.environ.get('HANDOFF_RAM_SIZE', str(8 * 1024**3)), 0)
command_line = os.environ.get('HANDOFF_BOOT_ARGS', '-v serial=3').encode('ascii')
if b'\0' in command_line or len(command_line) >= 608:
    raise gdb.GdbError('Invalid boot command line')

def in_ram(address, length):
    return ram_base <= address and length >= 0 and address - ram_base <= ram_size - length

gdb.execute('set architecture aarch64', to_string=True)
gdb.execute('set pagination off', to_string=True)
gdb.execute('set tcp auto-retry on', to_string=True)
gdb.execute('set tcp connect-timeout 10', to_string=True)
gdb.execute(f'target remote :{port}', to_string=True)
breakpoint = gdb.Breakpoint(f'*{handoff_pc:#x}', type=gdb.BP_HARDWARE_BREAKPOINT, internal=True)
# The known firmware uses this trampoline for stage 2, then XNU. The second
# entry and boot_args version must both match before any write is permitted.
breakpoint.ignore_count = 1
gdb.execute('continue', to_string=True)
if int(gdb.parse_and_eval('$pc')) != handoff_pc:
    raise gdb.GdbError('Unexpected handoff stop')
args_address = int(gdb.parse_and_eval('$x1'))
if not in_ram(args_address, 716):
    raise gdb.GdbError('Boot arguments outside RAM')
inferior = gdb.selected_inferior()
args = bytes(inferior.read_memory(args_address, 716))
if struct.unpack_from('<HH', args) != (2, 2):
    raise gdb.GdbError('Unexpected boot_args revision/version')
virtual_base, physical_base = struct.unpack_from('<QQ', args, 8)
tree_virtual, tree_length = struct.unpack_from('<QI', args, 96)
if tree_virtual < virtual_base:
    raise gdb.GdbError('Invalid virtual device-tree pointer')
tree_physical = tree_virtual - virtual_base + physical_base
room = ((tree_physical + tree_length + 16383) & ~16383) - tree_physical
if tree_physical % 4 or not in_ram(tree_physical, room) or room > 4 * 1024**2:
    raise gdb.GdbError('Device tree reservation outside RAM')
original = bytes(inferior.read_memory(tree_physical, room))
edited, new_length, changed = add_no_sep(original, tree_length)
payload = (command_line + b'\0').ljust(608, b'\0')
if changed:
    inferior.write_memory(tree_physical, edited)
    if bytes(inferior.read_memory(tree_physical, room)) != edited:
        raise gdb.GdbError('Device tree readback failed')
    inferior.write_memory(args_address + 104, struct.pack('<I', new_length))
inferior.write_memory(args_address + 108, payload)
if bytes(inferior.read_memory(args_address + 104, 4)) != struct.pack('<I', new_length):
    raise gdb.GdbError('Device tree length readback failed')
if bytes(inferior.read_memory(args_address + 108, 608)) != payload:
    raise gdb.GdbError('Boot argument readback failed')
result = {'handoff_pc': hex(handoff_pc), 'boot_args_revision': 2, 'boot_args_version': 2,
          'old_tree_length': tree_length, 'new_tree_length': new_length,
          'no_sep_node_added': changed, 'boot_args': command_line.decode(), 'readback_verified': True}
with open(os.environ['HANDOFF_RESULT'], 'w') as destination:
    json.dump(result, destination, indent=2)
    destination.write('\n')
print(json.dumps(result))
breakpoint.delete()
gdb.execute('detach', to_string=True)
end
