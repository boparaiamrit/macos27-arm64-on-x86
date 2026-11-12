# RGBA16 one-click-controller launcher

Implemented a separate `Launch-Rgba16MouseAttempt.ps1`. No CheckOnly, Docker
process, VM, GPU operation, live metadata write or guest input was performed.
The parent owns admission and any live execution.

The launcher restricts selection to `m27-pages-rgba16`, keeps `fresh-01` and
cleanup4 readiness, and invokes the unchanged `run-mouse-attempt.py`. Its
defaults are 8 guest CPUs, TB1024, 12 container CPUs/12 GiB, LP128, Mesa26 and
two software threads. Transfer copies and final shader capture remain explicit
switches. The existing 900/800 upper bounds, 10 GiB host floor, CONTROL conflict
check, runtime pins, read-only root/build and CONTROL-only guest write mount
remain in place. No MAIN source volume is added.

The new container prefix is `macos-golden-rgba16-mouse-01-`. Metadata is confined
to `mouse-guest/current-rgba16-mouse-attempt.json`, with `input_enabled` recording
the requested mode. `MOUSE_GUEST_INPUT=on` is added only without CheckOnly;
the existing entrypoint independently suppresses input for `--check-only`.
The old launcher, controller, request protocol and release/cleanup lifecycle
are unchanged. This addition does not authorize a click or change the existing
fresh-frame, visible-Quit, nonce, SHA/dimensions, one-press and explicit-release
requirements in `PARENT-PROTOCOL.md`.

## Verification

- Meaningful RED: the new mocked admission case invoked the real original
  launcher with explicit `m27-pages-rgba16`. Parameter binding rejected it
  against the original RGB10-only ValidateSet; exit 1, before any mock Docker
  call. The failure is retained in `rgba16-launcher-red.log`.
- GREEN: **nine mocked cases passed** against the real new launcher source:
  CheckOnly selection/defaults/paths/resources and disabled input; actual-form
  opt-in input; explicit feature switches; resource/deadline overrides;
  whole-CONTROL conflict; and four invalid profile/readiness/deadline cases.
  `rgba16-launcher-green.log` records the result.
- The test mocks Docker, New-Item and Set-Content. No Docker executable or
  live metadata writer ran. The new metadata file is absent after the tests.
- PowerShell parsing passed as part of the test. All ten protected existing
  source/protocol/profile/core/readiness files retain their exact bytes and
  hashes. `rgba16-launcher-sha256.json` records before/after and new file pins.
- Launcher SHA256: `8872a12963653a9bda61ae5951b2b81b56a79969f76b23fe8df636ad9149d46f`
  (7,488 bytes). Test SHA256:
  `2015645f741023dd3cffcba1aee68e14b74564a5b33741dc6d097f67816bedf4`.

These are launcher argument/admission proofs, not an actual controller, HID,
click-effect, RGBA16 guest-acceptance or usable-desktop result. Existing mouse
lifecycle qualification was not repeated. No identity migration, source pin,
frame wrapper, profile, guest file or prior evidence was changed. All new files
are under ignored test-output; no staging or commit occurred. The installed
codebase-memory and test-first guidance were used; graph/index/coverage tools
were unavailable, so exact source fallback was used without a coverage claim.

## Unexecuted parent CheckOnly command

```powershell
& ./test-output/arm-macos/full-system/mouse-guest/Launch-Rgba16MouseAttempt.ps1 -CheckOnly -QemuProfile m27-pages-rgba16 -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup4-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

This command is provided for parent review only. No live action is issued by
this handoff.
