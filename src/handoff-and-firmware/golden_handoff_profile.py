"""Admission pins for the captured Golden revision-3 handoff; initially closed."""
from golden_ctrr_profile import QEMU, QEMU_SHA

SCRIPT_NAME = 'handoff-r3/kernel-handoff.gdb'
HELPER_NAME = 'handoff-r3/golden_adt_args.py'
SCRIPT_SHA = 'e14fb3450b7876b2fd8285a33d851b8d78a768d45032936bc7bd64d3db0bac7f'
HELPER_SHA = '5a242dd347cc49a2a03bc0a2a6b84e8ba32fc7df1ce59740a223a9dc433d439c'
OLD_SCRIPT_SHA = 'aaca7baaeec6b7e7699f84e05cc36c481d8d77482e87c13a36cfd67d5eaf1550'
OLD_HELPER_SHA = '1801c61af828bc1c9ef27c65cbb27be93ebef1c99a1a44e3c6efbe2cd56d698c'


def identity_with_r3(current, script_sha, helper_sha):
    if (current.get('qemu_sha256') != QEMU_SHA or current.get('handoff_script_sha256') != OLD_SCRIPT_SHA or
            current.get('adt_helper_sha256') != OLD_HELPER_SHA):
        raise ValueError('Current pair does not match the admitted emulator and legacy adapter')
    for value in (script_sha, helper_sha):
        if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('Unadmitted revision-3 adapter digest')
    updated = dict(current)
    updated.update(handoff_script_sha256=script_sha, adt_helper_sha256=helper_sha)
    changed = sorted(k for k in current if current[k] != updated[k])
    if changed != ['adt_helper_sha256', 'handoff_script_sha256']:
        raise ValueError('Migration must change exactly the two adapter pins')
    return updated
