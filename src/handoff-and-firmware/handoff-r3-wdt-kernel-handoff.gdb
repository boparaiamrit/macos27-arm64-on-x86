# SPDX-License-Identifier: GPL-2.0-or-later
# Staged only: content-selected Golden r3/v2 handoff, preserving original CLI.
python
import gdb
import json
import os
from pathlib import Path
import struct
import sys
import time

directory = Path(os.environ['HANDOFF_SCRIPT_DIR'])
sys.path.insert(0, str(directory))
from golden_adt_args import (ARGS_SIZE, RAM_BASE, RAM_END, TRANSFER_PC,
                             TRANSFER_PREFIX, REQUESTED_ARGS, PlanError,
                             parse_boot_args_r3, plan_handoff, apply_handoff_plan)

def physical_mode(enabled):
    response = gdb.execute('maintenance packet Qqemu.PhyMemMode:' + ('1' if enabled else '0'), to_string=True)
    if 'OK' not in response:
        raise gdb.GdbError('QEMU physical debugger mode unavailable')

def stage2_ended(result_path):
    path = result_path.with_name('serial.log')
    for _ in range(10):
        if path.exists():
            with path.open('rb') as serial:
                if b'======== End of iBootStage2 serial output. ========' in serial.read(8 * 1024**2):
                    return True
        time.sleep(.05)
    return False

result_path = Path(os.environ['HANDOFF_RESULT'])
if result_path.exists():
    raise gdb.GdbError('Refusing to replace an existing handoff result')
if os.environ.get('HANDOFF_BOOT_ARGS', REQUESTED_ARGS) != REQUESTED_ARGS:
    raise gdb.GdbError('Unsupported requested options in the Golden r3 profile')
if int(os.environ.get('HANDOFF_PC', hex(TRANSFER_PC)), 0) != TRANSFER_PC:
    raise gdb.GdbError('Golden r3 profile requires its qualified transfer address')

gdb.execute('set architecture aarch64', to_string=True)
gdb.execute('set pagination off', to_string=True)
gdb.execute('set tcp auto-retry on', to_string=True)
gdb.execute('set tcp connect-timeout 10', to_string=True)
gdb.execute('target remote :' + os.environ['HANDOFF_GDB_PORT'], to_string=True)
breakpoint = gdb.Breakpoint('*' + hex(TRANSFER_PC), type=gdb.BP_HARDWARE_BREAKPOINT, internal=True)
try:
    for _ in range(256):
        # Selection is by stage marker, fingerprint and complete layout, never
        # by hit ordinal or an ignored first breakpoint.
        gdb.execute('continue', to_string=True)
        if int(gdb.parse_and_eval('$pc')) != TRANSFER_PC:
            raise gdb.GdbError('Unexpected stop before Golden handoff selection')
        entry = int(gdb.parse_and_eval('$x0')) & ((1 << 64) - 1)
        args_address = int(gdb.parse_and_eval('$x1')) & ((1 << 64) - 1)
        if not RAM_BASE <= args_address <= RAM_END - ARGS_SIZE or args_address % 8:
            continue
        physical_mode(True)
        try:
            inferior = gdb.selected_inferior()
            transfer = bytes(inferior.read_memory(TRANSFER_PC, 4096))
            if transfer[:len(TRANSFER_PREFIX)] != TRANSFER_PREFIX:
                raise PlanError('Golden transfer fingerprint mismatch')
            args_data = bytes(inferior.read_memory(args_address, ARGS_SIZE))
            if len(args_data) != ARGS_SIZE or struct.unpack_from('<HH', args_data) != (3, 2):
                continue
            parsed = parse_boot_args_r3(args_data, args_address, entry)
            if not stage2_ended(result_path):
                raise PlanError('Qualified r3 candidate lacks its Stage2 end marker')
            tree_data = bytes(inferior.read_memory(parsed['tree_physical'], parsed['tree_length']))
            plan = plan_handoff(args_data, args_address, entry, tree_data, transfer)
            # Every validator and all ADT/CLI planning have completed before
            # this is permitted to make its first guest write.
            result = apply_handoff_plan(inferior, plan)
        finally:
            physical_mode(False)
        with result_path.open('x') as output:
            json.dump(result, output, indent=2)
            output.write('\n')
        print(json.dumps({key: result[key] for key in (
            'boot_args_revision', 'boot_args_version', 'requested_boot_args',
            'original_boot_args_preserved', 'old_command_line_length',
            'new_command_line_length', 'old_command_line_sha256', 'new_command_line_sha256',
            'old_tree_sha256', 'new_tree_sha256', 'old_tree_length', 'new_tree_length',
            'written_bytes', 'readback_verified')}))
        breakpoint.delete()
        gdb.execute('detach', to_string=True)
        break
    else:
        raise PlanError('No content-validated Golden r3 handoff found within bounded hits')
except Exception as error:
    # Never resume a rejected or partially changed guest. The owning runner
    # remains responsible for shutdown; disconnect preserves the stopped CPU.
    try:
        gdb.execute('disconnect', to_string=True)
    except Exception:
        pass
    raise gdb.GdbError(str(error))
end
