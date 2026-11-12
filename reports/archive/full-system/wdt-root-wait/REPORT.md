# Single bounded WDT root-wait diagnostic

One admitted WDT boot executed Darwin 27, published the normal root resource, validated the on-disk root hash and completed mounting the installed Macintosh HD System snapshot. The existing runner stopped it at its bounded timeout after 1790.241 seconds. Data/userspace and GUI remain unverified; no panic or guest reset was observed.

Exactly one actual normal-selection boot used `GoldenHandoffWdt` on the isolated CONTROL volume, after one successful CheckOnly. Actual attempt `20261027T211303Z-e7unitba` ran for 1790.241 seconds. Runner status `timeout`, exit 124, QEMU return 0, GDB return 0. These process results are not boot success claims. Started 2026-10-27T21:13:01.994066+00:00; finished 2026-10-27T21:42:53.837664+00:00.

## Guest and adapter evidence

Actual serial.log:84 proves Darwin 27.0.0 / xnu-13432.1.9~1/RELEASE_ARM64_VMAPPLE execution. Normal-root discovery retained ARV enabled and basesystem ? 0. Root publication is at line 406; BSD root disk3s1 at line 408; root snapshot xid 459 at line 418; root-hash authentication required at line 425 and successfully validated at line 426. Line 429 explicitly identifies a read-only System volume mounted as root; Macintosh HD mount completion is at line 433. The final line 435 is AppleVPKeyStore safe xART support. No completed Data mount or launchd/initproc/userspace checkpoint appears in retained serial or the privately scanned canonical Reims stream. Root discovery is no longer the unresolved checkpoint at termination; the exact later execution location was not inspected.

Adapter artifact present: True; exact requested 18-byte `-v serial=3 wdt=-1` and readback verified: True. Details are in `adapter-verification.json` and the attempt's `handoff.json` if present. The exact prepared guest is 27.0/26A428; a Darwin 27 CPU-execution claim requires the retained serial banner. Root publication, BSD root, installed System/Data mounts and userspace are assessed separately in `kernel-root-evidence.json`; matches are evidence candidates unless explicitly assessed in `interpretation.json`.

Adapter write count 9, total 49 bytes; original/new command lengths 0/18. ADT reservation old/new 573440/573440, parsed bytes 563480, existing zero padding 9960; NoSEP reservation contract verified True. These remain adapter checks, separate from guest execution and filesystem proof.

The retained Darwin observations span at least 1413.972 seconds. `checkpoint-timing.json` records the discrete observation times; this is not a measurement of the exact root-wait-entry time. Serial Recovery request present: False; serial panic present: False.

Omitted: System root is verified, but Data and userspace did not become unambiguous. The authorized eligibility condition for a second GDB frame-capture connection was unmet. No frame capture or new GDB connection was attempted.

The diagnostic changes the admitted boot option only. Continued wait, driver attachment, GDB exit zero, a PV panic notification, and OFF idle do not prove a System mount or GUI. The unpublished exact Golden header and the prior cold-layer timing leave the underlying root failure unresolved; this run adds only the observations above.

## Commands

```powershell
& ./test-output/arm-macos/full-system/Launch-FullAttempt.ps1 -GoldenHandoffWdt -CompressedReimsLog -CheckOnly -GuestVolume macos-golden-pristine-guest -StreamVolume macos-golden-stream-large-state -ReadyName stream-ready-large-live5.json
& ./test-output/arm-macos/full-system/Launch-FullAttempt.ps1 -GoldenHandoffWdt -CompressedReimsLog -ColdStreamedBoot -TraceStorage -Timeout 1800 -HookTimeout 1700 -GuestVolume macos-golden-pristine-guest -StreamVolume macos-golden-stream-large-state -ReadyName stream-ready-large-live5.json
```

No retry, delegation, AUX restore, identity migration, overlay reset, build/install, prewarm, backend/sampler replacement, guest input, or host restart was performed. No single-user, iBoot diagnostic or reset-pause option was selected.

## Pins and preservation

Runtime `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`; read-only root, network none, 12 GiB memory/equal swap and 4 CPUs. The qualified guest command retains 8 GiB, one TCG vCPU, software Lavapipe and `REIMS_VGPU_WINDOW=0`. Existing scratch/RTC diagnostic/unavailable CTRR qualifications remain unchanged; hardware acceleration and complete CTRR/RTC behavior are unproved.

Qualified QEMU SHA256 `dba936f79fdfecea6163360d4beea0495cf2e870c11816a6a1b0c08ca7a8b542`, original firmware `6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845`, patched firmware `593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e`, offset `0x2370`, unchanged before/after. WDT helper `d629671ab3518ddc8abb40e74e30ec5557a068ec6ba07f3d95bb79f28eb7cf3b`; byte-identical R3 GDB `e14fb3450b7876b2fd8285a33d851b8d78a768d45032936bc7bd64d3db0bac7f`; capture source/snapshot `3ce7bab9c38da2c5ce5efa91464162ca64da9acba75ec50e231bc71f44455c35`.

293 protected source/identity/readiness/ACTIVE-STATE/guard/reader/backend/frozen-source files have identical before/preactual/after hashes. MAIN was mounted read-only only by shared-locked evidence helpers and all six captured files are byte-identical. CONTROL AUX was asserted pristine both before CheckOnly and immediately before actual launch. `volume-metadata-*.json`, `source-hashes-*.json` and `preservation-proof.json` provide the exact inventory.

| File | MAIN before = after | CONTROL before | CONTROL after |
|---|---|---|---|
| aux.work.img | `2cc56f592406aa515e67d75add8495eba7c32291e622cf79b0fe0817ae784b79` | `2ca2b332f05e2d6e3663bb4db0982a5feec268a8d1b91460f140ad8d3cb49414` | `b05b9e04a9cb268016e01235ec540f09456bca12a8528d4763f2e7a8be4f88c9` |
| root.overlay.qcow2 | `24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c` | `24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c` | `24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c` |
| runner-identity.json | `85cdf3ee54faa6043837550cdb1c44eef5d6ce10f295ae5e3513b97ad44be3e9` | `208658d83a348d183382cbf6355f46309ed4f542bf90561acdb0c923187eff55` | `208658d83a348d183382cbf6355f46309ed4f542bf90561acdb0c923187eff55` |

Only natural CONTROL changes listed in `preservation-proof.json` are observed; content-change attribution to individual guest writes is not inferred. The admitted parent migration was not repeated.

## Compressed integrity and resources

Canonical gzip `20261027T211303Z-e7unitba/reims-vgpu-fail.log.gz` was privately streamed through EOF: CRC/footer valid, 8563910 raw bytes, SHA256 `7d28b15870e4fed4a9b255a2d79351b4478acbb421eda3d1960ec2a16b6dd1e3` matching capture metadata and result. No raw file was materialized. All consumed bytes are retained, zero unretained read bytes. Exact retained bytes 308662, allocated 331776, below 8 MiB; raw below 64 MiB. Metadata/result/final file-size accounting matches exactly. Canonical gzip SHA256 `f7fd3338518de95ab1e298e526b925774ab7660c9a90477ddc5fbc04e330981e`. Source-queue bytes never delivered are not claimed captured. Private ECID and source boot paths are excluded from readable evidence; no canonical raw text was printed.

Existing backend `b018c33c5b240dcda2bfea23ae2f8eeb3e673cd98fb8c1618cdf90e50d116d1d`, image `sha256:7810c1732534d73f8cc50f213f1b682eca4e78df6f3b2369cc03285383ee26ac`, same volume/socket, 8 RAM layers, 6 GiB/equal swap, 2 CPUs/read-only root remain unchanged. Verified fetch count 22 to 27, compressed-byte delta 2008707688. New authenticated events are recorded in `backend-deltas.json`; all 67 layers are not verified. NBD trace observed 2457 reads / 33095168 requested bytes including repeats; these are sends, not completed or unique-byte proof.

Backend memory current 4176969728 to 4177670144; peak 4383297536 to 4383297536. OOM/memory-event deltas `{'low': 0, 'high': 0, 'max': 0, 'oom': 0, 'oom_kill': 0, 'oom_group_kill': 0}`; restarts 0 to 0. VM counters in `vm-memory-evidence.json` are sampled only; terminal auto-removed cgroup counters are unavailable.

The unchanged 10 GiB floor, sample age <=20 seconds/future <=2 seconds, 2 GiB overlay, 48 MiB stop/64 MiB retention, 1800-second wall, 1700-second hook, 50 ms backend supervision/900-second layer/3600-second initialization bounds applied. 33 saved guard samples have minimum free 26769059840 bytes and maximum age 1.970 seconds. Any terminal guard error is recorded in the runner result/handoff rather than bypassed.

`final-process-verification.json` proves owned VM/GDB, CheckOnly, launchers and hash helpers ended. Original backend and sampler PID 104360/start identity are alive. Only new scripts/evidence in this directory and the existing launcher's normal attempt/current-pointer/CONTROL writes were used.

## Limits

- No Data mount, installed-system userspace, login/desktop frame, or hardware acceleration is proved.
- The final AppleVPKeyStore line is a progress boundary, not a root-cause diagnosis; no later guest registers/PC were inspected.
- Eventual authenticated root publication here does not isolate the cause of the earlier Recovery panic or prove timing as its sole cause.
- Serial line 432 reports insecure boot enabled in the qualified baseline. On-disk root-hash validation is not complete secure-boot-chain attestation; firmware/authentication/SSV policy was unchanged.
- The exact Golden XNU header remains unpublished; public XNU behavior is parent-supplied background context.
- QMP status polling suspended after an early bounded response timeout during synchronous storage I/O. Retained serial, process exit, storage and guards provide the run observations.
- All 67 layers are not verified; this was not a full RAW conversion.
- VM memory counters are discrete samples; terminal auto-removed cgroup peak/events are unavailable.
