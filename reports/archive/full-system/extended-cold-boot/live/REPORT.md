Exactly one uninterrupted Golden crypto boot ended at the runner's **7200-second wall profile**: `timeout`, runner exit **124**, elapsed **7196.227 seconds**. No retry or delegated child was used. Attempt `20261027T224156Z-rcpgj51o`, owned container `macos-golden-full-20261027T224156`. Launch began **2026-10-28 04:11:55.854 IST**; the PowerShell launcher ended **06:11:53.068 IST** with exit 1 after reporting the runner's exit 124.

This run progressed beyond Base System PID 1. It proved authenticated normal System mounting, the Base System launchd/ignition phase, Data unlock, the successful root switch from `/System/Volumes/macOS` back to `/`, and **`disk3s5 mount-complete volume Data`** requested by `apfs_boot_util (pid 5)` under `launchd (pid 1)`. Later serial reported `swap enabled` and the start of **`init-with-data-volume`**. That boot task's completion, later service readiness, WindowServer/loginwindow, and an interactive composited desktop remain unproved. No guest frame was captured; **GUI remains unverified**.

The exact authorized command was executed once:

```powershell
& ./test-output/arm-macos/full-system/Launch-FullAttempt.ps1 -GoldenCrypto -CompressedReimsLog -ColdStreamedBoot -ExtendedColdBoot -TraceStorage -Timeout 7200 -HookTimeout 1700 -GuestVolume macos-golden-pristine-guest -StreamVolume macos-golden-stream-large-state -ReadyName stream-ready-large-live5.json
```

No extra switches or CheckOnly invocation were added. The parent's admitted CheckOnly was reused; the actual runner performed its mandatory preflight. No existing script, profile, emulator, firmware, identity, reader, backend, frozen file, guard, sampler, admission or ACTIVE-STATE file was edited. No build/install, restore/reset, prewarm, conversion, cache change, new backend, guest patch or host restart was performed. New scripts/evidence are confined to this `live/` directory; normal launcher attempt/current-pointer writes and natural CONTROL changes were preserved.

| Positive checkpoint | Host-observed elapsed seconds |
|---|---:|
| Original handoff rc 0 | 626.842 |
| Authenticated System | 929.733 |
| Base System PID 1 | 1234.916 |
| macOS root switch | 2743.542 |
| Data mount complete | 4955.252 |
| Data init task starts | 6868.150 |
| Runner wall timeout | 7196.227 |

Except the original-hook receipt and runner elapsed, these are first-observation upper bounds from bounded foreground snapshots, not exact guest event times. [Host checkpoint chart](timeline.html), [timing evidence](checkpoint-timing.json), [reviewed checkpoints](reviewed-checkpoints.json), [selected serial evidence](serial-evidence.txt), and [full retained serial](../../attempts/20261027T224156Z-rcpgj51o/serial.log) retain the source observations. The root-switch sequence explicitly shuffles `/System/Volumes/macOS <-> / <-> System/Volumes/BaseSystem` and completes with error 0. The earlier Base System pivot is not evidence of a proved iBoot Recovery fallback; this run subsequently returned toward the installed macOS root.

Both retained `shared_region...returned 0x1 / check_np errno 12` sequences were followed by **`dyld cache mapped system-wide`**. No fatal OOM or guest hang is established. No retained guest panic or RESET event was observed. Serial and backend fetches continued to advance during this run. The quiet intervals and Reims `OFF` lines were never used as stop conditions.

The original handoff returned **0**, with the runner's positive `handoff-hook-exit.json` receipt and revision 3/version 2, dynamic bounds, readback and original-CLI preservation contract verified. Requested injection remained `-v serial=3 wdt=-1`, PC `0xe0a00000`, firmware patch offset `0x2370`. There was **no second debugger, external QMP/HMP, runtime screenshot, guest input or manual runtime pause**. STOP/RESUME events in the retained runner log belong to the original startup handoff. The terminal event is runner-owned `host-qmp-quit` with `guest=false`; QEMU return **-9** records the owned bounded shutdown, not evidence of a guest crash. QMP status polling remained suspended as implemented. The result's last `prelaunch` status is stale and does not describe the late guest state. [Handoff contract](adapter-verification.json), [events](qmp-events.json), [invocation/finally receipt](invocation-finally-receipt.json).

The qualified QEMU stayed at SHA-256 `b4c7d59055e30c931ecade17ecf08f806baba7814a1477513d85d57872e3e6f0`, in runtime image `13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`. Firmware originals/patched hashes remain `6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845` / `593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e`. All **477 protected source files** match before/after, including the explicit extended profile and WDT/helper/Reims pins; own live evidence is excluded. MAIN's six files are identical and both evidence-helper volume mounts were read-only under shared locks. CONTROL identity, firmware and preparation files are unchanged. Only its AUX and overlay changed naturally and were preserved:

- AUX: `fd7814f78eb58e1ccb8b061409024116b84e9c86286c797ee61290cba83df68b` to `831d6f43f70bc8c80e9e37cc84ccef8aa43c4879a533c0d3ecd5a7f0d4663a89`.
- Overlay: `24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c` to `0f1685493bfad1cf9354ec219aadd5d8d3b3521eafc2869be544a06c53746fd0`; allocation **6,955,008 bytes**, below the unchanged 2 GiB cap.

[Preservation proof](preservation-proof.json), [before](volume-metadata-before.json), [after](volume-metadata-after.json), [source hashes](source-hashes-after.json).

The existing backend retains exact ID `b018c33c5b240dcda2bfea23ae2f8eeb3e673cd98fb8c1618cdf90e50d116d1d`, image `7810c1732534d73f8cc50f213f1b682eca4e78df6f3b2369cc03285383ee26ac`, original start, mounts, command and limits. It remains alive, with restart count 0 and **zero OOM/OOM-kill/max-memory event deltas**. Its cumulative verified-fetch counter changed from **38 to 110**, and reported `fetched_bytes` increased by **31,149,157,515** to **47,570,025,868**, including repeated layers. Layer **24** was in flight in the last snapshot. These counters do not prove every NBD request completed, unique downloaded bytes, all 67 source layers verified, or a complete local RAW checkpoint. The NBD trace contains **7,417 sends**, including **7,318 read sends** requesting **220,597,760 bytes including repeats**; sends are not completion receipts. [Backend deltas](backend-deltas.json), [NBD accounting](nbd-progress.json).

All **128 saved guard samples** passed: minimum free **22,212,141,056 bytes**, maximum sample age **2.701 seconds**. The 10 GiB floor, 20-second maximum age, two-second future tolerance, 900-second layer deadline, finite resources, cancellation/shutdown and all log budgets stayed unchanged. VM container limits remained 12 GiB/equal swap/4 CPUs; guest 8 GiB/one TCG CPU, software Lavapipe and `REIMS_VGPU_WINDOW=0`. No acceleration is claimed. Sampler **58156**, exact original command/start **2026-10-27T21:50:27.7977719Z**, remains alive and untouched.

The lossless Reims gzip was read through EOF with CRC verification. Its raw SHA-256 **`d633693f93affd8896b693bbf917d9d1893c07cb3781acb509a5da7bb68da59d`** covers **38,506,506 consumed and retained raw bytes**; metadata and runner result agree, with **zero unretained bytes**. Gzip SHA-256 is **`1115f28fd0b6362c037d0b443f61c287b593f213af85df2d2a02cd3669e1afb1`**. Retained capture is **1,121,162 bytes**, allocated **1,183,744 bytes**, with no exhaustion or capture error. No raw file was materialized. Cipher-creation failure counts are **zero** in serial, stderr and the full decoded gzip. Reims diagnostic words (`OFF` 67,816; `ON` 0; `frame` 0) supply no desktop proof. [Capture validation](compressed-capture-validation.json), [guard summary](guard-summary.json).

One evidence-output formatting wrapper raised a TypeError after successfully writing the timeline/report files. Its receipt is retained in `evidence-output-wrapper-failure.json`; it created no live resources and did not affect the runner classification or cleanup.

All owned VM/evidence containers, launcher and invocation process have ended. The invocation and summary `finally` receipts show no emergency cleanup action was required; the existing runner owned VM shutdown. The backend and original sampler remain alive. [Final process checks](final-process-verification.json), [final validation](final-validation.json), [artifact hashes](artifact-manifest.json), [machine-readable handoff](handoff.json).

The remaining concrete blocker is proof of completion beyond `init-with-data-volume` and of later services/a composited interactive desktop within this profile. The two-hour deadline expired while cold reads and APFS activity were still occurring. The exact execution/wait location was not observed, so this is **bounded timeout with substantial installed-root/Data userspace progress**, not a proved guest hang, fatal OOM, Recovery-only boot, or verified GUI boot. No additional boot was attempted.
