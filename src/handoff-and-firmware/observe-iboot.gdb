# SPDX-License-Identifier: GPL-2.0-or-later
# Read-only diagnostic for the observed Golden 26A428 Stage2 panic stack.
python
import gdb
import hashlib
import json
import os
from pathlib import Path
import struct
import time

gdb.execute('set architecture aarch64', to_string=True)
gdb.execute('set pagination off', to_string=True)
gdb.execute('set tcp auto-retry on', to_string=True)
gdb.execute('set tcp connect-timeout 10', to_string=True)
gdb.execute('target remote :' + os.environ['HANDOFF_GDB_PORT'], to_string=True)
site = 0x700d9164
bp = gdb.Breakpoint('*0x700d9164', type=gdb.BP_HARDWARE_BREAKPOINT, internal=True)
handoff_bp = gdb.Breakpoint('*0xaca00000', type=gdb.BP_HARDWARE_BREAKPOINT, internal=True)
golden_bp = gdb.Breakpoint('*0xe0a00000', type=gdb.BP_HARDWARE_BREAKPOINT, internal=True)
destination = Path(os.environ['HANDOFF_RESULT'])
kind = 'iboot_panic'
boot_candidates = []
monitor_state = None
for skipped in range(256):
    gdb.execute('continue', to_string=True)
    pc = int(gdb.parse_and_eval('$pc')) & (2**64 - 1)
    if pc in (0xaca00000, 0xe0a00000):
        boot_candidates = []
        golden_stage2 = False
        if pc == 0xe0a00000:
            serial = destination.with_name('serial.log')
            serial_bytes = serial.read_bytes()[:8 * 1024 * 1024] if serial.exists() else b''
            if b'Start of iBootStage2 serial output' in serial_bytes:
                for _ in range(20):
                    if b'End of iBootStage2 serial output' in serial_bytes:
                        golden_stage2 = True
                        break
                    time.sleep(0.05)
                    serial_bytes = serial.read_bytes()[:8 * 1024 * 1024]
                if not golden_stage2:
                    raise gdb.GdbError('Golden transfer has no actual Stage2 end marker')
        hit = {'pc': hex(pc), 'hit': skipped, 'observed_at': time.time(), 'candidate_prefixes': [],
               'golden_stage2_end_marker': golden_stage2}
        for register in ('x0', 'x1'):
            pointer = int(gdb.parse_and_eval('$' + register)) & (2**64 - 1)
            if not 0x70000000 <= pointer <= 0x270000000 - 128:
                continue
            try:
                prefix = bytes(gdb.selected_inferior().read_memory(pointer, 128))
            except gdb.MemoryError:
                continue
            hit['candidate_prefixes'].append({'register': register, 'address': hex(pointer), 'prefix_hex': prefix.hex()})
            if len(prefix) != 128 or struct.unpack_from('<HH', prefix) != (2, 2):
                continue
            virtual, physical, memory, top = struct.unpack_from('<QQQQ', prefix, 8)
            tree, tree_length = struct.unpack_from('<QI', prefix, 96)
            tree_pa = tree - virtual + physical
            if (virtual >= 0xffff000000000000 and physical == 0x70000000 and
                    0 < memory <= 8 * 1024**3 and physical <= top < physical + memory and
                    tree >= virtual and 0 < tree_length <= 4 * 1024**2 and
                    physical <= tree_pa <= physical + memory - tree_length):
                boot_candidates.append({'register': register, 'address': hex(pointer),
                                        'prefix_hex': prefix.hex(), 'device_tree_physical': hex(tree_pa),
                                        'device_tree_length': tree_length})
        hit_name = 'golden-transfer-hit-' if pc == 0xe0a00000 else 'trampoline-hit-'
        with destination.with_name(hit_name + str(skipped) + '.json').open('x') as output:
            json.dump(hit, output, indent=2)
        if pc == 0xe0a00000:
            if not golden_stage2:
                continue
            kind = 'golden_transfer'
            break
        if boot_candidates:
            kind = 'boot_args_candidate'
            break
        continue
    if pc != site:
        if os.environ.get('OBSERVE_RESET') == '1':
            status = gdb.execute('monitor info status', to_string=True)
            if 'VM status: shutdown' in status:
                monitor_state = 'shutdown'
                kind = 'guest_reset_paused'
                break
        raise gdb.GdbError('Unexpected iBoot diagnostic stop')
    # The same VA is reused by Stage1. Require this attempt's actual Stage2
    # serial marker and replacement of the observed Stage1 instruction.
    instruction = bytes(gdb.selected_inferior().read_memory(site, 4))
    if instruction != bytes.fromhex('c30100b0'):
        time.sleep(0.2)  # Allow the owning runner's bounded FIFO collector to drain.
        serial = destination.with_name('serial.log')
        if serial.exists() and b'Start of iBootStage2 serial output' in serial.read_bytes()[:8 * 1024 * 1024]:
            if instruction != bytes.fromhex('61198052') or int(gdb.parse_and_eval('$x0')) != 0x4962211b03d706d:
                raise gdb.GdbError('Unexpected Stage2 panic-caller signature')
            break
else:
    raise gdb.GdbError('Stage2 not identified within bounded breakpoint hits')
registers = {}
unavailable = []
for name in ['pc', 'sp', 'cpsr'] + ['x' + str(i) for i in range(31)] + [
        'ESR_EL1', 'ELR_EL1', 'FAR_EL1', 'SPSR_EL1', 'SCTLR_EL1', 'TCR_EL1',
        'VBAR_EL1', 'TTBR0_EL1', 'TTBR1_EL1', 'SP_EL0']:
    try:
        registers[name] = hex(int(gdb.parse_and_eval('$' + name)) & (2**64 - 1))
    except Exception:
        unavailable.append(name)
inferior = gdb.selected_inferior()
# The current firmware MMU need not map the whole physical RAM range. QEMU's
# read-address mode changes debugger translation only, not guest CPU state.
reply = gdb.execute('maintenance packet Qqemu.PhyMemMode:1', to_string=True)
if 'OK' not in reply:
    raise gdb.GdbError('Physical debugger reads unavailable')
try:
    code = bytes(inferior.read_memory(0x70000000, 1024 * 1024))
    context_address = int(registers['x19'], 0) if kind == 'iboot_panic' else 0
    if kind == 'iboot_panic' and not 0x70000000 <= context_address <= 0x270000000 - 1024:
        raise gdb.GdbError('Exception context outside the known guest RAM')
    context = bytes(inferior.read_memory(context_address, 1024)) if context_address else b''
    ring_state = bytes(inferior.read_memory(0x70132c80, 256))
    static_strings = bytes(inferior.read_memory(0x70120000, 16384))
    transfer_code = bytes(inferior.read_memory(0xe0a00000, 4096)) if kind == 'golden_transfer' else b''
    golden_context = None
    golden_args = golden_tree = b''
    if kind == 'golden_transfer':
        args_address = int(registers['x1'], 0)
        entry_address = int(registers['x0'], 0)
        if 0x70000000 <= args_address <= 0x270000000 - 0x480:
            golden_args = bytes(inferior.read_memory(args_address, 0x480))
            if struct.unpack_from('<HH', golden_args) == (3, 2):
                virtual, physical, memory, top = struct.unpack_from('<QQQQ', golden_args, 8)
                tree, tree_length = struct.unpack_from('<QI', golden_args, 96)
                tree_pa = tree - virtual + physical
                if not (0x70000000 <= physical < top <= physical + memory <= 0x270000000 and
                        physical <= entry_address < top and physical <= args_address <= top - 0x480 and
                        virtual >= 0xffff000000000000 and tree >= virtual and
                        0 < tree_length <= 4 * 1024**2 and physical <= tree_pa <= top - tree_length):
                    raise gdb.GdbError('Golden revision-3 argument ranges failed validation')
                golden_tree = bytes(inferior.read_memory(tree_pa, tree_length))
                golden_context = {'revision': 3, 'version': 2, 'args_address': hex(args_address),
                                  'entry_address': hex(entry_address), 'tree_address': hex(tree_pa),
                                  'tree_bytes': tree_length}
            else:
                golden_args = b''
finally:
    gdb.execute('maintenance packet Qqemu.PhyMemMode:0', to_string=True)
if len(code) != 1024 * 1024:
    raise gdb.GdbError('Short iBoot code snapshot')
code_path = destination.with_name('iboot-code.bin')
with code_path.open('xb') as output:
    output.write(code)
strings_path = destination.with_name('iboot-strings.bin')
with strings_path.open('xb') as output:
    output.write(static_strings)
if golden_context is not None:
    for name, payload in [('golden-boot-args.bin', golden_args), ('golden-device-tree.bin', golden_tree)]:
        with destination.with_name(name).open('xb') as output:
            output.write(payload)
        golden_context[name] = {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}
result = {'read_only': True, 'pc': hex(pc), 'observed_at': time.time(), 'stage_verified': kind != 'guest_reset_paused',
          'kind': kind, 'boot_args_candidates': boot_candidates,
          'monitor_state': monitor_state, 'transfer_code_base': '0xe0a00000' if transfer_code else None,
          'transfer_code_hex': transfer_code.hex(),
          'golden_context': golden_context,
          'earlier_breakpoint_hits_skipped': skipped,
          'registers': registers, 'unavailable_registers': unavailable,
          'snapshot_base': '0x70000000', 'snapshot_bytes': len(code),
          'snapshot_sha256': hashlib.sha256(code).hexdigest(),
          'snapshot_file': code_path.name, 'exception_context_address': hex(context_address),
          'exception_context_hex': context.hex(), 'state_address': '0x70132c80',
          'state_hex': ring_state.hex(), 'strings_address': '0x70120000',
          'strings_bytes': len(static_strings), 'strings_file': strings_path.name,
          'strings_sha256': hashlib.sha256(static_strings).hexdigest()}
with destination.open('x') as output:
    json.dump(result, output, indent=2)
    output.write('\n')
print('Read-only iBoot panic-caller observation captured; no guest memory/register writes')
if kind != 'guest_reset_paused':
    print(gdb.execute('x/64i 0x700d90c0' if kind == 'iboot_panic' else 'x/16i ' + hex(pc), to_string=True))
gdb.execute('disconnect', to_string=True)
# disconnect leaves the target stopped; the owning runner shuts it down.
end
