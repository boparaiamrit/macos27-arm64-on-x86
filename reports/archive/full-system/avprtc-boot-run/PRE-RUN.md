One authorized AVP RTC diagnostic boot, followed by stop at the first validated diagnostic, serial panic, guard failure, or bound. No retry.

Pinned QEMU: /work/orchard-golden-avprtc/qemu/build/qemu-system-aarch64, SHA256 25fa22ad4790a877dc842dca3e97cc06e15fab7ef144a266c04e2790cc2d59a4.
Guest: macOS 27.0 / 26A428, /p2/v1. Original/patched firmware SHA256 6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845 / 593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e, offset 0x2370.
Existing identity migration is preserved. No migration/reset/rebase will be performed.

Existing unowned backend: macos-golden-stream-large, b018c33c5b240dcda2bfea23ae2f8eeb3e673cd98fb8c1618cdf90e50d116d1d, image sha256:7810c1732534d73f8cc50f213f1b682eca4e78df6f3b2369cc03285383ee26ac; volume macos-golden-stream-large-state; /stream/golden-live5.nbd. Preserve eight-layer RAM cache, 6 GiB memory and equal swap, 2 CPU, read-only root, external 50 ms guard, 900 s/layer, 3600 s initialization. No prewarm.
Existing unowned sampler: Windows PID 104360, started 2026-10-27T18:32:44.6757233Z, Watch-HostSpace.ps1 -DurationSeconds 14400. Preserve it. Boundary evidence uses unchanged host_space_sample.read_valid_sample: C: >= 10 GiB, age <= 20 seconds, future <= 2 seconds. Existing runner and backend retain their own guards. No extra sampler/watcher.

Owned processes: only new short-lived read-only evidence helpers listed by exact container name in helper-*.json; launcher-created CheckOnly and actual run containers recorded from current-full-attempt.json. No other processes may be stopped. Launcher owns and reaps its QEMU/GDB pair. Finish before 2026-10-27T19:20:00Z (00:50 IST 28 October); actual run <=1800 seconds, observer <=1700 seconds.

Observer is copied by the existing runner; it reads registers/memory and stops at a content-validated Stage2 panic caller 0x700d9164 or at 0xaca00000 with content-validated v2/2 boot arguments. It does not invoke the mutating handoff helper. Code capture is bounded to 1 MiB, strings to 16 KiB. Boot argument candidates do not prove kernel execution. handoff_verified, kernel_execution_verified, full_gui_verified remain false unless their corresponding evidence establishes otherwise.

Ownership: NEW scripts/evidence only in this directory. Existing launcher may naturally write attempts/current-full-attempt.json and working AUX/overlay. All other files/processes remain preserved. No edits, builds, installs, conversion, identity changes, fabricated responses, or retries.
