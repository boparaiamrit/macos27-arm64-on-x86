"""Opt-in real-cipher build; preserves the admitted Golden WDT handoff."""
from pathlib import Path
from golden_handoff_wdt_profile import (
    QEMU as OLD_QEMU, QEMU_SHA as OLD_QEMU_SHA,
    SCRIPT_NAME, HELPER_NAME, SCRIPT_SHA, HELPER_SHA, BOOT_ARGS,
)

QEMU = Path('/work/orchard-golden-crypto/qemu/build/qemu-system-aarch64')
# Same device source as CTRR; twelve actual-device NIST checks and paused
# platform tests passed. The original cipher-stub failure was reproduced.
QEMU_SHA = 'b4c7d59055e30c931ecade17ecf08f806baba7814a1477513d85d57872e3e6f0'


def identity_with_crypto(current, new_digest):
    if (current.get('qemu_sha256') != OLD_QEMU_SHA or
            current.get('handoff_script_sha256') != SCRIPT_SHA or
            current.get('adt_helper_sha256') != HELPER_SHA):
        raise ValueError('Control identity does not match the admitted WDT pair')
    if (not isinstance(QEMU_SHA, str) or len(QEMU_SHA) != 64 or
            any(c not in '0123456789abcdef' for c in QEMU_SHA) or
            new_digest != QEMU_SHA or new_digest == OLD_QEMU_SHA):
        raise ValueError('Real-cipher build has not been admitted with this digest')
    updated = dict(current)
    updated['qemu_sha256'] = new_digest
    return updated
