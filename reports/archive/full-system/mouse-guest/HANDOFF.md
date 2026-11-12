# Parent handoff: offline freeze only

Delivered: new controller, bounded helper, host CLI, same-frame-factory entrypoint,
future RGB10 launcher, 52 passing offline tests, chronological red/green logs,
protocol, report, reference-source observations and final hash manifest.

The owner must review `mouse_controller.py` and [PROTOCOL.md](PROTOCOL.md),
especially the durable consumed/owed state before down, uncertain framing with
zero additional bytes, one cleanup up after full-write/lost-ACK, exact guard
propagation, and the pre-wire cleanup Refusal that makes the unchanged owner
terminate its owned Popen. `MouseCleanupRequired` is deliberately outside core
GuardError, so release uncertainty cannot become suspended status polling.

No human approval was obtained or asserted in this task. All attestation strings
in tests are authored fake data. The real parallel VM and its frames/session
must stay outside this deliverable. No synthetic QMP/mouse/HID qualification has
occurred; all actual-delivery checkpoints are unknown. Stop here for parent
review, then a separately authorized future controlled API case. No such case
or guest work is implemented/executed/scheduled by this handoff.

## Recorded future commands — UNEXECUTED, not authorization

These exact launcher commands are retained for review only. They must not run
beside the parallel VM or before the parent's independent review/qualification
gate. The existing launcher ownership checks also reject concurrent guest use.
No state preparation, identity migration, cleanup, trace, or repair is supplied.

Future CheckOnly, **not executed**:

```powershell
& ./test-output/arm-macos/full-system/mouse-guest/Launch-MouseAttempt.ps1 -CheckOnly -QemuProfile m27-pages-rgb10 -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup4-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

Future actual owned launcher, **not executed**:

```powershell
& ./test-output/arm-macos/full-system/mouse-guest/Launch-MouseAttempt.ps1 -QemuProfile m27-pages-rgb10 -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup4-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

No actual launcher run, including CheckOnly, took place. The only launcher
execution was inside `tests/launcher_mock.ps1` with Docker/admission/file-write
commands intercepted and output checked offline. Parent metadata was not written.

## Future operator protocol — schematic placeholders only

The following arguments deliberately contain placeholders. They convey no
coordinate, image, nonce, attempt or approval from this task. The binary identity
SHA256 `87614fc2db5efc0f7293aad13d1f70ffd43d4e3e09380dfd5522ffd419d7202b`
must never substitute for a PNG digest.

After any separately approved future owned run, select only its exact attempt:

```powershell
python -B ./test-output/arm-macos/full-system/mouse-guest/mouse_request.py --attempt EXACT_ATTEMPT show
python -B ./test-output/arm-macos/full-system/mouse-guest/mouse_request.py --attempt EXACT_ATTEMPT capture --id capture-01 --nonce EXACT_SESSION_NONCE
python -B ./test-output/arm-macos/full-system/mouse-guest/mouse_request.py --attempt EXACT_ATTEMPT show
```

Wait for the matching response. Use `view_image` on the exact retained path
named by current-frame.json. See both **KSA and a visibly labeled Quit button
simultaneously**. Choose the pixel center inside that actual button. Verify
the current PNG dimensions and SHA256. An old image, presumed location, gray
color, menu shortcut evidence, or earlier approval is insufficient. If both
elements are not visible, stop with zero input; there is no fallback.

Only after that human observation, a preview and submission would be:

```powershell
python -B ./test-output/arm-macos/full-system/mouse-guest/mouse_request.py --attempt EXACT_ATTEMPT click_keyboard_setup_quit --id click-01 --nonce EXACT_SESSION_NONCE --frame-sha256 EXACT_CURRENT_PNG_SHA256 --width VERIFIED_WIDTH --height VERIFIED_HEIGHT --x APPROVED_INTEGER_X --y APPROVED_INTEGER_Y --attest-view-image-ksa-and-visible-quit --preview
python -B ./test-output/arm-macos/full-system/mouse-guest/mouse_request.py --attempt EXACT_ATTEMPT click_keyboard_setup_quit --id click-01 --nonce EXACT_SESSION_NONCE --frame-sha256 EXACT_CURRENT_PNG_SHA256 --width VERIFIED_WIDTH --height VERIFIED_HEIGHT --x APPROVED_INTEGER_X --y APPROVED_INTEGER_Y --attest-view-image-ksa-and-visible-quit
```

Preview opens no QMP socket and publishes nothing; it is not an approval source.
The owner repeats a same-client capture and independent running check, compares
the exact approved SHA/dimensions, and can refuse a changing clock/pixel region
with proven zero down. Such a refusal can require a new human view/approval and
ID, never an automatic retry. Once possibly down, never retry the click.

After confirmed up, the owner schedules one frame/running proof at +3 seconds.
The parent must inspect the actual resulting pixels and state; ACKs and an
unchanged KSA do not prove effect. This controller always leaves
`interaction_proven=false`. If release is uncertain, the original owner must
clean up its owned VM immediately, without waiting for 900 seconds and without
manual signalling of any external process.
