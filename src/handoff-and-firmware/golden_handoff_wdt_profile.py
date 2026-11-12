"""Opt-in root-service wait diagnostic; no root match or seal bypass."""
from golden_ctrr_profile import QEMU, QEMU_SHA
from golden_handoff_profile import SCRIPT_SHA as OLD_SCRIPT_SHA, HELPER_SHA as OLD_HELPER_SHA

SCRIPT_NAME = 'handoff-r3-wdt/kernel-handoff.gdb'
HELPER_NAME = 'handoff-r3-wdt/golden_adt_args.py'
SCRIPT_SHA = 'e14fb3450b7876b2fd8285a33d851b8d78a768d45032936bc7bd64d3db0bac7f'
HELPER_SHA = 'd629671ab3518ddc8abb40e74e30ec5557a068ec6ba07f3d95bb79f28eb7cf3b'
BOOT_ARGS = '-v serial=3 wdt=-1'


def identity_with_wdt(current, script_sha, helper_sha):
    if (current.get('qemu_sha256') != QEMU_SHA or current.get('handoff_script_sha256') != OLD_SCRIPT_SHA or
            current.get('adt_helper_sha256') != OLD_HELPER_SHA):
        raise ValueError('Control identity does not match the qualified original r3 profile')
    if script_sha != OLD_SCRIPT_SHA:
        raise ValueError('The wait diagnostic must preserve the exact GDB script')
    if (not isinstance(helper_sha, str) or len(helper_sha) != 64 or
            any(c not in '0123456789abcdef' for c in helper_sha) or helper_sha == OLD_HELPER_SHA):
        raise ValueError('Unadmitted wait-diagnostic helper digest')
    updated = dict(current)
    updated['adt_helper_sha256'] = helper_sha
    return updated
