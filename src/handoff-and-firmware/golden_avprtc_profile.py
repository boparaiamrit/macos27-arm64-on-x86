"""Separately admitted AVP RTC diagnostic emulator; no clock-completeness claim."""
from pathlib import Path
from golden_scratch_profile import QEMU as OLD_QEMU, QEMU_SHA as OLD_QEMU_SHA

QEMU = Path('/work/orchard-golden-avprtc/qemu/build/qemu-system-aarch64')
QEMU_SHA = '25fa22ad4790a877dc842dca3e97cc06e15fab7ef144a266c04e2790cc2d59a4'


def identity_with_avprtc(current, new_digest):
    if current.get('qemu_sha256') != OLD_QEMU_SHA:
        raise ValueError('Identity does not bind the reviewed scratch QEMU')
    if not isinstance(new_digest, str) or len(new_digest) != 64 or any(c not in '0123456789abcdef' for c in new_digest):
        raise ValueError('No reviewed AVP RTC QEMU digest')
    upgraded = dict(current)
    upgraded['qemu_sha256'] = new_digest
    return upgraded
