# Single bounded normal-selection Golden boot

Exactly one actual boot ran with the supplied isolated `macos-golden-pristine-guest` pair. CheckOnly passed first. The actual VM ended after **110.498 seconds**, following an explicit kernel Recovery reboot panic. There was no retry, restore, migration, build, prewarm, backend restart, or change to the supplied limits.

## Result and line evidence

The adapter contract passed at PC `0xe0a00000`, revision 3/version 2: original command line length zero was preserved as the prefix, `-v serial=3` was appended, the NoSEP node fit the existing reservation, and all nine writes (42 bytes) passed readback. Tree reservation 573440 bytes, parsed 563480, original zero padding 9960. These checks prove only the adapter contract.

Darwin 27.0.0 actually executed: attempt `serial.log:84`. The exact guest kernel banner is `xnu-13432.1.9~1/RELEASE_ARM64_VMAPPLE`; prepared guest version/build remains 27.0/26A428.

Normal selection is supported by the empty original command line in `handoff.json`, root selection at `serial.log:379`, ARV enabled at line 391, and `importing root hash (basesystem ? 0)` at line 392. APFS device/container work appears at lines 367-390 and 396-397. This proves attempted normal root discovery, not a completed installed System root mount.

The decisive sequence in `serial.log` is:

- Line 399: write `boot-picker-bringup-reason` (18-byte data).
- Line 402: write `boot-command` to `recover-system`.
- Line 406: `About to reboot into Recovery!`
- Line 407: `panic(cpu 0 caller 0xfffffe001e62ec38): Reboot into Recovery (this panic is expected) @IOKitBSDInit.cpp:671`
- Line 408: `Debugger message: panic`.

There is no `BSD root:`, completed root mount, Data mount, launchd/initproc/userspace evidence, or composited frame. **Installed System root, userspace, and GUI are unverified.** The observed Recovery request is a real kernel panic, despite the parenthetical expected-panic text. The underlying root/policy condition that selected it is not established by the call site. No GPIO, UUID, authentication blob, fsboot, or boot-volume tuple cause is inferred.

QMP records `GUEST_CRASHLOADED`/action `run`, then `SHUTDOWN` with `guest=true`, `reason=guest-reset`; see `qmp-events.json` for transcript line numbers. The crash-loaded event alone is only a paravirtual panic notification. The panic is independently proved by serial. The first reset ended the VM, with no reboot cycle. Runner status `qemu_exited_after_handoff`, QEMU return 0, and launcher exit 0 describe clean process exit, **not successful boot**. QMP polling was suspended after its bounded response timeout during synchronous storage I/O; process/log/storage/space/wall guards stayed in force.

## Exact commands

CheckOnly:

```powershell
& ./test-output/arm-macos/full-system/Launch-FullAttempt.ps1 -GoldenHandoff -CompressedReimsLog -CheckOnly -GuestVolume macos-golden-pristine-guest -StreamVolume macos-golden-stream-large-state -ReadyName stream-ready-large-live5.json
```

Actual (one invocation):

```powershell
& ./test-output/arm-macos/full-system/Launch-FullAttempt.ps1 -GoldenHandoff -CompressedReimsLog -ColdStreamedBoot -TraceStorage -Timeout 1800 -HookTimeout 1700 -GuestVolume macos-golden-pristine-guest -StreamVolume macos-golden-stream-large-state -ReadyName stream-ready-large-live5.json
```

Actual attempt: `20261027T203823Z-9q97nh_r`. Started 2026-10-27T20:38:22.360601+00:00; finished 2026-10-27T20:40:13.876426+00:00. Both commands explicitly used the private control volume. No diagnostic/single-user/reset-pause mode was selected. Exact wrapper invocations and PIDs are in `*-invocation.json`; launcher outputs and exit records are retained.

## Pins and preservation

- Runtime image: `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`; 12 GiB memory/same swap, 4 CPUs, network none, read-only root; qualified QEMU still uses 8 GiB guest RAM/one TCG vCPU, software Lavapipe, `REIMS_VGPU_WINDOW=0`.
- QEMU `/work/orchard-golden-ctrr/qemu/build/qemu-system-aarch64`: `dba936f79fdfecea6163360d4beea0495cf2e870c11816a6a1b0c08ca7a8b542` before and after.
- Firmware original: `6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845`; patched: `593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e`; existing offset `0x2370`, unchanged.
- R3 GDB adapter: `e14fb3450b7876b2fd8285a33d851b8d78a768d45032936bc7bd64d3db0bac7f`; combined ADT helper: `5a242dd347cc49a2a03bc0a2a6b84e8ba32fc7df1ce59740a223a9dc433d439c`, unchanged.
- Capture source and per-attempt snapshot: `fb2ff806ad0176a5477983f53dde85c1a3c647141afb7ecb40d50158076163c8`.
- Protected source manifest: 279 files, exact before/after equality (`source-hashes-before.json`, `source-hashes-after.json`). This includes launcher/runner/profiles/helpers, guards, ACTIVE-STATE, readiness, converter snapshot and readers/backend sources.
- Existing scratch 16 KiB at `0x4fc000`, diagnostic AVPRTC 4 KiB at `0x30240000`, unavailable CTRR 64 KiB at `0x30260000` remain qualified platform limitations; there is no claim of complete RTC or CTRR protection.

The MAIN volume was mounted **read-only only**, shared-locked for hashes. All six captured files, including AUX, overlay, identity and firmware, are byte-identical before, immediately before actual, and after. No MAIN guest execution or write mount occurred.

| File | MAIN SHA256 before and after |
|---|---|
| AUX | `2cc56f592406aa515e67d75add8495eba7c32291e622cf79b0fe0817ae784b79` |
| Overlay | `24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c` |
| Identity | `85cdf3ee54faa6043837550cdb1c44eef5d6ce10f295ae5e3513b97ad44be3e9` |

The CONTROL AUX was asserted equal to original `2ca2b332f05e2d6e3663bb4db0982a5feec268a8d1b91460f140ad8d3cb49414` both before CheckOnly and immediately before actual boot. Its natural post-boot hash is `1252e33b3fbd58372b5ff2f68252c1e66b1317b321554123fba35bed1f8eefbe`. This change is consistent with the observed guest NVRAM writes; individual byte attribution is not claimed. CONTROL overlay remains `24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c`, and identity remains `85cdf3ee54faa6043837550cdb1c44eef5d6ce10f295ae5e3513b97ad44be3e9`. They were not restored or remigrated. Parent preparation/restore records were read and retained as metadata in `volume-metadata-*.json`; only parent had restored this private AUX before the run. It now contains the naturally changed state and must be preserved.

## Lossless bounded compressed capture

Canonical capture is `../attempts/20261027T203823Z-9q97nh_r/reims-vgpu-fail.log.gz` (13060 bytes). Streaming decompression through EOF verified its gzip CRC/footer, exactly **351795 raw bytes**, and SHA256 `e761b613dedbe48c509d457bda17696bb130d8afacea030d25c3242f46786c34` against both capture metadata and runner result. `gzip_finished=true`, `all_consumed_bytes_retained=true`, raw/read counts match, and `unretained_read_bytes=0`. No raw file was materialized. Canonical gzip SHA256 is `25a90e5823e08a5873400f16d072f219a9b84169d8662d831c7469373e538e1f`.

Actual canonical/previews/metadata total is 79301 bytes, below the **8 MiB total retained** limit; raw consumption is below the separate **64 MiB hard cap**. The unchanged legacy regular-file raw 8 MiB limit was not used. Metadata reports 79292 retained bytes while result and independently measured final file sizes both give 79301: `_publish` serializes metadata before refreshing its retained-size counters (`reims_log_capture.py:170-177`), so the serialized field lags final fstat. Canonical gzip integrity is verified independently. Full validation and sanitized semantic counts are in `compressed-capture-validation.json`. There are 683 OFF lines and three display shared-state/online/ack messages; these establish neither GPU failure nor a composited frame. No log-level/sampling/filtering/GPU changes were applied. Every consumed FIFO byte is retained, but source-writer queue bytes never written to the FIFO are outside the claim. Canonical gzip was scanned privately; readable excerpts redact ECID/private command lines.

## NBD progress and resources

The original backend ID and image are unchanged: `b018c33c5b240dcda2bfea23ae2f8eeb3e673cd98fb8c1618cdf90e50d116d1d`, `sha256:7810c1732534d73f8cc50f213f1b682eca4e78df6f3b2369cc03285383ee26ac`. Existing 8 RAM layers, 6 GiB memory/same swap, 2 CPUs, read-only root and `/stream/golden-live5.nbd` were reused. Readiness pins were validated by CheckOnly and actual runner; no prewarm was run.

Backend fetch count advanced **21 to 22**, with 435961819 compressed bytes retrieved. New authenticated layer 52 completed in 89.067 seconds. Last-500 event snapshots include the complete run; all 67 layers are not verified. NBD trace contains 2166 read requests, totaling 31903232 requested bytes including repeats, and 408 unique offset/length pairs. These are send observations, not proof of completed or unique byte reads. See `nbd-progress.json` and `backend-deltas.json`.

Backend current memory 4180123648 -> 4180422656 bytes (delta 299008); cgroup peak stayed 4383297536 bytes. All backend memory-event deltas, including OOM/OOM-kill, are zero; restart count stayed 0. The one retained live VM sample had zero OOM counters and about 1.97 GB current memory. Because the VM was automatically removed on exit, final VM cgroup peak/events are unavailable; no full-run VM peak is claimed.

## Guards and terminal ownership

The unchanged 10 GiB floor, sample freshness <=20 seconds/future tolerance <=2 seconds, 48 MiB global stop/64 MiB retention, 2 GiB overlay allocation, 1800-second wall/1700-second hook bounds, and backend 50 ms/900-second layer/3600-second initialization supervision remained active. Saved guard samples: 7, minimum free 27436539904 bytes, maximum saved age 1.988 seconds. No guard, raw/compressed capture cap, or diagnostic retention cap fired. Boundary samples are discrete; continuous enforcement comes from the unchanged runner/backend.

`final-process-verification.json` confirms actual VM/GDB, launcher PowerShell, CheckOnly and all three read-only evidence helpers ended. Existing backend and sampler PID 104360 with its original creation time remain alive. Other containers/processes were preserved. The only experiment-induced guest writes were the authorized CONTROL working pair; this run observed only AUX content change. New scripts/evidence live only in this directory, with normal attempt artifacts/current pointer written by the existing launcher as authorized.

The durable handoff is `handoff.json`; sanitized serial evidence is `serial-evidence.txt`. The experiment is complete at the first actual kernel panic/reset. No further boot or remediation was attempted.
