# Commands

Executed once: `& ./test-output/arm-macos/full-system/r9-boot-test-run/run-once.ps1`. This new script records the corrected guards, migration once, CheckOnly once and actual launcher once. The actual timeout exception is terminal. No script retry occurred.

Before that, four recorded source hashes were compared using Get-FileHash and 13 synthetic tests rerun using the exact pinned image/arguments in the preparation COMMANDS.md, with owned container r9-resume-synthetic. Pre/post state used the preparation inspect-state.py with read-only guest/build/base mounts and pinned image, owned names r9-resume-prestate/r9-resume-poststate. Identity readback used a read-only guest mount and compared JSON with the migration backup. Get-Process/docker inspect/docker ps preserved before/after identities. No guest input, extra debugger or QMP client was invoked.

Post-run analysis: `python test-output/arm-macos/full-system/r9-boot-test-run/analyze.py`. Original-resolution image viewer inspected the sole R9 PNG, requested 013011 frame2, and all three 020702 PNGs. Source and retained evidence hashes are in hashes.json.
