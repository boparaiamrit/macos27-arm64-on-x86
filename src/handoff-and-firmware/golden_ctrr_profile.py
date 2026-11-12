"""Pinned unavailable-CTRR probe profile; does not implement CTRR protection."""
from pathlib import Path
from golden_avprtc_profile import QEMU as OLD_QEMU, QEMU_SHA as OLD_QEMU_SHA

QEMU = Path('/work/orchard-golden-ctrr/qemu/build/qemu-system-aarch64')
QEMU_SHA = 'dba936f79fdfecea6163360d4beea0495cf2e870c11816a6a1b0c08ca7a8b542'


def identity_with_ctrr(current, new_digest):
    if current.get('qemu_sha256') != OLD_QEMU_SHA:
        raise ValueError('Identity does not bind the reviewed AVP RTC QEMU')
    if not isinstance(new_digest, str) or len(new_digest) != 64 or any(c not in '0123456789abcdef' for c in new_digest):
        raise ValueError('No reviewed CTRR probe QEMU digest')
    upgraded = dict(current)
    upgraded['qemu_sha256'] = new_digest
    return upgraded
