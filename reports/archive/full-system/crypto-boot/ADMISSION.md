# Real-cipher emulator admission

The isolated build passed direct qualification and is admitted for one bounded Golden normal-System boot. This is an emulator correction; guest userspace and desktop success remain unverified.

- New QEMU: `/work/orchard-golden-crypto/qemu/build/qemu-system-aarch64` in `macos-orchard-build`.
- SHA-256: `b4c7d59055e30c931ecade17ecf08f806baba7814a1477513d85d57872e3e6f0`, independently checked against the exported Windows artifact.
- Same 12,031 tracked source paths as CTRR, no AES device changes. Nettle is explicitly required; other optional crypto providers are disabled.
- Twelve actual paused-device AES ECB/CBC encrypt/decrypt known-answer checks passed at 128/192/256-bit key sizes. The same first vector fails on the old binary with the observed cipher-creation error and unchanged output memory.
- Existing paused scratch, RTC, CTRR and PCI checks passed. Pinned runtime resolves the existing matching Nettle ABI.
- The original five source/build trees remained unchanged; the new build added about 0.5 GiB. No Apple guest ran during build qualification. Detailed provenance is in `../../orchard-build/golden-crypto/RESULT.md`.

CONTROL migration `20261027T215812Z` changed only `qemu_sha256`. AUX remains `b05b9e04a9cb268016e01235ec540f09456bca12a8528d4763f2e7a8be4f88c9`; overlay remains `24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c`. The old identity was backed up in the CONTROL boot directory. MAIN was not mounted by migration. CheckOnly `20261027T215814Z-533g77n9` passed.

The new optional `-GoldenCrypto` launcher profile preserves the exact WDT handoff script, helper, boot arguments and resource guards. Normal defaults and older profile pins remain unchanged. Its admission was closed until the new binary and tests were reviewed; closed startup refusal was checked before pinning it.

The runner now writes a small `handoff-hook-exit.json` receipt only after the original GDB process exits zero and handoff validation succeeds. This lets an optional read-only observer verify the exit result while the VM still runs. Failure and missing-handoff cases produce no receipt. The Linux runner/identity regression suite passed 87 tests. The first test invocation had an execution-denied fixture because Docker's test `/tmp` mount was nonexecutable; rerunning with an executable, isolated test tmpfs passed. No production tmpfs setting changed.

The separate post-root observer passed 23 offline tests. It requires confirmed original-hook exit zero and matching actual System-mount evidence, reads registers and bounded code/stack regions, and attempts detach in `finally`. It must have a 20-second in-container process deadline; a forced termination or failed detach ends that owned VM without retry. No real guest has been observed with it yet.

Actual boot command:

```powershell
& ./test-output/arm-macos/full-system/Launch-FullAttempt.ps1 -GoldenCrypto -CompressedReimsLog -ColdStreamedBoot -TraceStorage -Timeout 1800 -HookTimeout 1700 -GuestVolume macos-golden-pristine-guest -StreamVolume macos-golden-stream-large-state -ReadyName stream-ready-large-live5.json
```

The 10 GiB storage floor, sample freshness, NBD deadlines, 2 GiB overlay allocation cap and bounded lossless log retention remain enforced. The existing streamed backend and newly renewed sampler (PID 58156, started 2026-10-27T21:50:27Z) remain active. No AUX restore, overlay reset, root-UUID change, authentication change, kernel panic patch or host driver change is part of this experiment.
