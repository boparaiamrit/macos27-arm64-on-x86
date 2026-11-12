# Offline freeze: one visible Keyboard Setup Assistant Quit click

This new directory contains a source-and-offline-unit implementation only.
No real QEMU fixture, VM, GPU, guest input, CONTROL/state/RAW access, service,
download, or guest cleanup was performed. The parallel RGB10 VM and its frames,
session, and metadata were not inspected. No delegation was used.

The only input operation is `click_keyboard_setup_quit`. A future operator must
use `view_image` on the current exact retained PNG and simultaneously see
Keyboard Setup Assistant and its visibly labeled Quit button. They approve a
pixel center inside that actual button, with the exact attempt, session nonce,
PNG SHA256, and verified width/height. There are no default coordinates, historical
approval, automatic target recognition, focus inference, or arbitrary input API.
If both elements are not visible simultaneously, stop without input.

The parent reports an acknowledged Cmd+Q with unchanged KSA pixels. That leaves
input effect unproven. It establishes neither broken keyboard delivery nor a
focus cause. Apple's authored menu contains Quit Keyboard Setup Assistant,
`q`, modifier `0x100000`, and `terminate:` despite `LSUIElement=true`; shortcut
runtime availability and the earlier event's recipient remain unknown.

Files:

- `mouse_controller.py`: same-client frame approval, two distinct input RPCs,
  durable one-click consumption and release obligation, fatal cleanup protocol.
- `mouse_files.py`: new bounded copy of the inspected fixed-file helper, with
  a 4096-byte publication cap and the Windows shared-reader/ReplaceFileW fix.
- `mouse_request.py`: host-only exact-attempt show/capture/preview/submit CLI.
- `run-mouse-attempt.py`: opt-in adapter around the unchanged frame wrapper.
- `Launch-MouseAttempt.ps1`: future RGB10 launcher clone, never launched for real.
- `tests/`: generated PNGs and in-memory JSON transport only; PowerShell mocks.
- [PROTOCOL.md](PROTOCOL.md): complete approval, bounds, release/error rules.
- [REPORT.md](REPORT.md): red/green evidence, limitations and preservation.
- [HANDOFF.md](HANDOFF.md): parent gate and exact unexecuted future commands.
- `reference-source-sha256.json`: source-inspection observations only.
- `source-sha256.json`: final owned source, documentation and evidence hashes.

The Python entrypoint defaults off. Only `MOUSE_GUEST_INPUT=on` enables it;
`--check-only` always disables the controller, and creates no mouse session.
The separate future launcher intentionally sets that enable flag. Existing
launchers and protected source were not edited. Its fixed guest is
`/guest/fresh-01`, profile is `m27-pages-rgb10`, readiness is cleanup4, and upper
bounds/defaults are 900 seconds overall and 800 seconds for handoff.
Its future launcher metadata path is this directory's `current-mouse-attempt.json`.

The admitted RGB10 artifact SHA256 from the parent and inspected profile source
is `87614fc2db5efc0f7293aad13d1f70ffd43d4e3e09380dfd5522ffd419d7202b`.
This is a binary identity pin, **not a frame digest or live binary revalidation**.

## Offline verification

Final: **52 tests passed**, CPU only. See
`evidence/green-final-52.stderr.log` and `evidence/green-final-52.result.json`.
Tests never import/run the real runner's main, open a real socket, or resolve a
real Docker invocation. The original QMP/cleanup class/function source is read
and exercised only with authored in-memory transport and process doubles.
The existing controller's tests and historical QEMU fixture were not run.

A repeat, if separately needed, must use a new evidence label:

```powershell
& ./test-output/arm-macos/full-system/mouse-guest/Run-OfflineTests.ps1 -Phase NEW-LOWERCASE-LABEL
```

Replace the uppercase placeholder with a new lowercase label. The harness
rejects existing evidence paths. Each test child is bounded to 120 seconds,
2 MiB stdout/stderr, and 64 MiB of owned outputs, with a fresh host free-space
sample before launch and approximately every 0.2 seconds during the child.
Below 10 GiB, stop; this task supplies no reserve recovery or cleanup procedure.

No QMP mouse API qualification, USB/HID delivery qualification, click effect,
or GoldenDesktop success is claimed. All remain **unknown**. Work stops at
this offline freeze for parent review and a separately authorized future
controlled API case. No live case, migration, or additional guest action is
part of this deliverable.
