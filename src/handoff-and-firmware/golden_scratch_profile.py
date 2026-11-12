"""Pinned isolated experimental QEMU profile; filled only after build review."""
from pathlib import Path

QEMU = Path('/work/orchard-golden-scratch/qemu/build/qemu-system-aarch64')
QEMU_SHA = '673cfd8b73b03b72e89ef6c312dd73612e4c625725e675b424579b5ade1acc1f'
BASE_QEMU_SHA = '2fca0114c7f37fac34d9e13def8c5c66850ac5e2d2c8a19365c0631f02b57705'


def identity_with_scratch(current, new_digest):
    if current.get('qemu_sha256') != BASE_QEMU_SHA:
        raise ValueError('Identity does not bind the reviewed original Golden QEMU')
    if not isinstance(new_digest, str) or len(new_digest) != 64 or any(c not in '0123456789abcdef' for c in new_digest):
        raise ValueError('No reviewed scratch-QEMU digest')
    upgraded = dict(current)
    upgraded['qemu_sha256'] = new_digest
    return upgraded
