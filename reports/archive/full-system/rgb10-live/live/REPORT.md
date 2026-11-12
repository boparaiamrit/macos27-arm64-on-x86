# One bounded RGB10 rendering-only Golden attempt

The single authorized rendering attempt completed with runner-owned timeout and cleanup. It reached Darwin 27, authenticated System root, Data mount and userspace. The final retained frame contains readable **Quit / Continue**, a Dock with recognizable Safari/Downloads and mostly placeholder icons, and a clock over a black background. **No readable KSA title/body or intact application window was visible. Full desktop and interaction remain unverified.**

**Live RGB10 descriptor acceptance remains unverified.** The exact canonical native log has zero old `buftex convert_unsupported ... fmt=0x5a` records and zero new `buftex native_refused reason=...` records, but also no matching RGB10 descriptor or success evidence. The new path has no specific success marker. Absence of a refusal without a matching workload does not prove acceptance. No descriptor dimensions, mip/array/sample counts, layout or successful GPU fence completion are invented.

## Execution and binding

Parent admission SHA256 `14bae3ca66c5626e8647b1cd8adb4dc9c019320b97a742c9855a504ae897f44e` matched. Both admission files were read. All nine protected host pins matched before and after. Parent qualification (92 runtime/debt tests, 44,944 GPU channels, 39 runner/profile tests) is admitted background evidence, not guest proof; these tests were not rerun.

| Operation | Exact attempt / container | Result |
|---|---|---|
| Fresh CheckOnly | `20261028T234007Z-srt5rquj` / `macos-golden-rgb10-01-20261028T234006` | `inputs_validated_no_vm`; runner/tool exit 0; runner 1.188 s; outer command 2.647 s |
| One actual boot | `20261028T234016Z-utjf3mpx` / `macos-golden-rgb10-01-20261028T234015` | `timeout`; runner exit 124; QEMU 0; handoff hook 0; runner 890.156 s; PowerShell tool exit 1 |
| Offline SPIR-V census | None | Not needed for a descriptor/rendering check without a SPIR-V feature claim |

Actual launcher start: **2026-10-28T23:40:15.6193367Z**. Canonical result-file mtime: **2026-10-28T23:55:06.425232Z**; launcher terminal receipt was observed by the 23:55:14Z clock check. A precise separate outer-duration receipt was not retained. The unchanged core reserves ten seconds for cleanup (`run-full-attempt.py:652`), consistent with the approximately 890-second timeout under the configured 900/800-second bounds. PowerShell surfaced exit 124 as its expected exception; there was no retry.

The ID came from this launcher's canonical result, then its exact [result.json](../../attempts/20261028T234016Z-utjf3mpx/result.json) was read. The independent before/after attempt-set difference contains exactly the CheckOnly and actual IDs above. No latest-directory guess was used. Bound `command.json` selects `/work/orchard-m27-pages-rgb10/artifacts/qemu-system-aarch64` and only the existing `/guest/fresh-01/boot` working pair. CheckOnly and actual `validated-inputs.json` hashes both equal `c4ec210d2779d4fa944529c4e6aa965e105aa19b1b6abafe990582db1a9fd225`.

Fresh CheckOnly command:

```powershell
& ./test-output/arm-macos/full-system/rgb10-live/Launch-Rgb10Attempt.ps1 -CheckOnly -QemuProfile m27-pages-rgb10 -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup4-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

Actual command, differing only by removal of `-CheckOnly`:

```powershell
& ./test-output/arm-macos/full-system/rgb10-live/Launch-Rgb10Attempt.ps1 -QemuProfile m27-pages-rgb10 -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup4-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

Counts: **1 fresh CheckOnly, 1 actual launcher, 1 VM, 0 census runs**. Guest input, control CLI, extra QMP/HMP/GDB clients, added live observers, retries/restarts/additional boots, manual stops, repairs/resets/reverts, identity migrations and delegation: **0**. The parallel child was not inspected or polled. During the live run only the owned launcher output was awaited; all artifact analysis and image viewing occurred after its container was gone.

## Separately established stages

| Stage | Current evidence and limit |
|---|---|
| Handoff | Exact handoff report: PC `0xe0a00000`, revision/version 3/2, NoSEP contract, nine writes / 49 bytes and readback verified; hook return 0. |
| Darwin kernel | `serial.log:84`: Darwin 27.0.0 / RELEASE_ARM64_VMAPPLE. |
| System root | `serial.log:404`: BSD root disk3s1; :425 root hash validated; :428 RO System root; :432 Macintosh HD mount-complete. |
| Data | `serial.log:1615`: disk3s5 mount-complete volume Data. |
| Userspace | :623/:880 launchd; :1643 init-with-data-volume; :1871 Early boot complete; :2153/:2155 loginwindow references. No completed login is established. |
| WindowServer | No direct named WindowServer marker in retained serial, stderr, GDB or decoded native log. Named-process checkpoint remains unverified; visible UI fragments are separate evidence. |
| Composited UI fragments | Direct `view_image` inspection of all three retained PNGs shows the Dock, buttons and later clock. |
| Identifiable composited application | No readable KSA title/body or intact application window in this run's retained frames. Not established. |
| Finder / full desktop | No Finder marker and no usable full desktop established. |
| Interaction | No input authorized or sent; unverified. |

QEMU return 0, marker activity, counters and a nonblack frame do not establish desktop readiness. The core's `full_gui_verified=false` is preserved.

## RGB10 and separate rendering findings

Counts below use **direct line prefixes**, recomputed from the three exact canonical gzip logs. For draw classes the anchor is `^linux_m2v_draw reason=CLASS`; other anchors are `^buftex convert_unsupported`, `^buftex native_refused reason=` and `^dual_plane_texture_unexecutable `. `OFF store_routes` counters, `refused_by=` replays and substring mentions are excluded. These are emitted diagnostic records, not unique failing draws or complete event totals.

| Direct diagnostic class | Prior fresh-01 | Prior interactive | Current RGB10 |
|---|---:|---:|---:|
| Buffer conversion unsupported, fmt 0x5a | 45 | 19 | **0** |
| Buffer conversion unsupported, fmt 0x6e | 0 | 7 | 9 |
| New buffer native refusal | 0 | 0 | 0 |
| Draw MRT color-input unsupported | 5 | 7 | 7 |
| Draw texture resolve missing | 38 | 13 | 5 |
| Of texture resolve: type 12 | 17 | 5 | 2 |
| Direct dual-plane texture unexecutable | 19 | 11 | 3 |
| Draw fragment translate | 4 | 6 | 6 |
| Of fragment translate: aggregate load reinterpretation | 4 | 6 | 5 |
| Of fragment translate: pending at sync boundary | 0 | 0 | 1 |

Historical logs: `20261028T203357Z-4whjksl8` and `20261028T221347Z-spxd9y08`. Their associated [fresh report](../../fresh-guest/live-boot/REPORT.md) and [interactive report](../../interactive-guest/live/REPORT.md) were read and preserved. Working state changed between boots; the interactive run also used input and extra captures. This is no controlled A/B comparison, timing improvement proof or causal attribution. The earlier reports describe readable white KSA windows; this run's retained frames do not show one. A rendering improvement is not established.

Current native references use LF-delimited line numbers in the **fully decoded canonical gzip**:

- :998 first direct MRT refusal; seven direct records total.
- :3889, :5794, :11779, :11793 and :11977: aggregate load cannot be reinterpreted from nested `Struct([...Vector(Half,4)...])` to `Vector(Half,4)`.
- :11759: `m2v_translation_pending_at_sync_boundary`, pipeline 216. This translation record does not verify pending GPU-fence debt completion.
- :3907 and eight later direct records: buffer conversion unsupported **fmt=0x6e**. The associated :3908 draw detail supplies type 8, descriptor length 64, buffer 114, offset 0, bytes-per-row 3072, 384×384, fmt 0x6e and `reason=buftex_load`. These are separate from RGB10.
- :3913: type 2, descriptor length 260, fmt 0x6e, five mips, handle 0x708, allocation 180224, L0 128×128, bpr 1024, `reason=linear_sample`.
- :5291/:5332: type 12 / descriptor length 176 / unsupported-object-type texture-resolution records. Direct dual-plane records at :5220/:5229/:13071 report pf 0x226, plane pairs 128×128, 160×160 and 1×1, one level.
- :13232: type 11, mid 65, descriptor length 56, geom 1, 256×256, fmt 0x226, mapped 1, pages 20, `reason=mapper_ref_texture_sample`. This does not establish nested-view dispatch support.

No current RGB10 descriptor fields were emitted. MRT, type-12 dual plane, aggregate bitcast and nested-view dispatch remain separate out-of-scope classes. No source or renderer change was made.

No `LLVM ERROR`, `Cannot emit physreg copy instruction` or `LLVM abort` signature appears in this exact serial/stderr/GDB/native workload. This is a scoped observation, not qualification of unexecuted or later shaders. Stderr separately reports that read-only `/root/.cache` disabled the shader cache; it was not repaired.

## All retained frames, viewed after exit

All three images are 1920×1080 RGB8. Timestamps below are the runner's capture observations, UTC. Every retained PNG was actually viewed using `view_image` at original resolution after cleanup; no additional capture was requested.

| Retained PNG | Capture time UTC | Exact black pixels | Unique colors | Direct visual observation |
|---|---|---:|---:|---|
| [frames/frame-0001.png](../../attempts/20261028T234016Z-utjf3mpx/frames/frame-0001.png) | 2026-10-28 23:42:18.447161Z | 2,073,600/2,073,600 (100.0000%) | 1 | Entirely black. No visible application, buttons, Dock, clock, or window border. |
| [frames/frame-0002.png](../../attempts/20261028T234016Z-utjf3mpx/frames/frame-0002.png) | 2026-10-28 23:47:19.915559Z | 1,933,264/2,073,600 (93.2323%) | 1,316 | Black background with Dock; recognizable Safari and Downloads, most other icons are generic placeholders. Two gray button shapes contain only tiny marks; no readable KSA title/body or white window/border. |
| [frames/frame-0003.png](../../attempts/20261028T234016Z-utjf3mpx/frames/frame-0003.png) | 2026-10-28 23:52:21.554582Z | 1,931,093/2,073,600 (93.1276%) | 1,403 | Black background; readable Quit and Continue buttons, Dock with recognizable Safari/Downloads and mostly placeholders, and top-right date/clock. No readable Keyboard Setup Assistant title/body, white application window, or window-border detail. |

Frame 2 has nonblack bounding box [173,800,1747,1075]; frame 3 [173,6,1900,1075], in pixel coordinates with exclusive right/bottom. Frame 1 is entirely black. Frame 3's label/clock appearance establishes a change within the retained UI sequence. It does not attribute that change to RGB10, establish KSA identity, or prove interaction.

All three PNGs passed signature, chunk CRC, IHDR/IEND, deflate and decoded scanline-length checks. Each has 6,221,880 decoded scanline bytes and matches its frame-index size/SHA256. All three captures were retained and positively acknowledged.

## Native capture, shader extraction and QMP integrity

The canonical [native gzip](../../attempts/20261028T234016Z-utjf3mpx/reims-vgpu-fail.log.gz) is **592,654 compressed bytes**, SHA256 `f1a4706b50aa16c06cb66aad70af89f1420025b0846c1716f75a1844f223b772`. Reading through EOF verified gzip CRC/ISIZE, **7,476,408 raw bytes**, SHA256 `d202e2969f5c47dba0afe6c53279de4aed4f62b8c2ba6d8668a6683d270bbe9e`, matching both capture metadata and canonical result. All consumed bytes were retained; unretained bytes 0, no exhaustion/error and no truncated tails. Native capture allocation **757,760 bytes** is below the 8 MiB storage bound, and raw bytes are below 64 MiB.

All **56** extraction-index files match their recorded sizes and SHA256: **32 SPIR-V modules**, **23 pipeline records**, and one producer index. Modules total **273,872 bytes**; pipeline metadata **129,661 bytes**. Total copied bytes **403,832**, allocated **561,152**. Extraction reports complete/nonempty, but `capture_set_atomic=false`, `producer_capture_complete=not_interpreted`. Producer index records `refusal_mask=644` without an invented decoding.

Producer bounds remain 32 modules, 256 KiB each, 4 MiB total; 64 pipelines, 16 KiB each, 128 KiB total metadata. The module count reached its 32-file cap and pipeline metadata was bounded. **Extraction completeness is not complete shader history.** No semantic census was needed or run; integrity checks make no f32-only-interface or physical-feature-legality claim.

Closed [QMP trace](../../attempts/20261028T234016Z-utjf3mpx/qmp.jsonl): one greeting, contiguous owner IDs **1–443**; one capabilities command, **438 query-status**, **3 screendump**, **1 cleanup quit**; **zero send-key, input-send-event or human-monitor-command**. No input session/controller/request files exist in the exact attempt. Three STOP/four RESUME events belong to initial handoff. No RESET/guest-panic event appears. Owner quit ID443 at line894 received a positive response; shutdown at **2026-10-28T23:55:06.209518Z** says `host-qmp-quit`. Cleanup was not manual.

All **78 actual-attempt files** and the **2 CheckOnly files** were read back and hashed. Their full integrity records, exact frame hashes and sanitized handoff fields are in [handoff.json](handoff.json). ECID and private boot-argument bytes are omitted.

## Resource and source authority

The pinned launcher retained actual runtime image `13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`, 12 container CPUs, 12 GiB memory/equal total swap, pids256, network none, read-only root/build, CONTROL RW with existing fresh-01 paths, and no source MAIN mount in the guest container. Canonical command independently records eight guest vCPUs, **8G guest RAM**, MTTCG and TB1024. Container memory and guest RAM are separate settings.

Mesa26 manifest `5711c1e0cc73a67cd8643f1d84591651a75f0de2ad27315f0c7709035ba63a0e`, LP128/two threads, compute scatter/gather off, 8 MiB capture tmpfs, 16 MiB /tmp, core ulimit0 and process-local filter0x10 remain enforced by the pinned launcher/wrapper. Guards remain unconditional 10 GiB host reserve, sample age [-2,20] seconds, 2 GiB allocated-overlay limit and 900/800-second bounds. These are configured/enforced limits, not independently measured cgroup peaks.

Preflight sample: **14,149,857,280 bytes**, age 1.565 s; postflight: **14,085,431,296 bytes**, age 1.846 s. No independent continuous minimum was retained. The preflight required start+960 seconds to fit before the user's conservative 2026-10-29 01:26Z / 06:56 IST deadline; actual termination at 23:55Z fit. The sampler was not renewed or restarted.

The separate pinned cleanup4 readiness authority records a complete **50,000,000,000-byte local RAW**, **35,357,175,808 allocated bytes**, device/inode **2096/1146219**, **67 converter-verified layers**, six RO matched samples and checkpoint `82066b4eeda14ff1edb191564b4eaf2806f4bfc042e904a95e56ead9dd06c05d`. The NBD socket remains `/stream/golden-live5.nbd`. Generic runner streamed/local-full-disk-false/all-layers-false fields do not negate this separate complete-source authority. No 35 GB RAW rehash, MAIN mount or guest-filesystem read outside the VM occurred.

## Compact preservation and cleanup

All nine admission host pins were read back before and after with identical bytes/hashes:

| Protected path relative to arm-macos | SHA256 before = after | Bytes |
|---|---|---:|
| `full-system/rgb10-live/Launch-Rgb10Attempt.ps1` | `18dd82b0fd8eb202d3ae3bbbc130c7c5d2f517fb7c2f5930d7a53fefbb7ba3f1` | 7,419 |
| `full-system/local-raw/golden_m27_pages_rgb10_profile.py` | `dcbcc7e59e5a2a4d292226600fe623df61aa63431e6b5eecfeb7d7f6c8fbbb40` | 1,031 |
| `full-system/local-raw/migrate-m27-pages-rgb10-identity.py` | `25cc94d1a061301cc95b30931d7808b8d00ab66c4f88a611838193d41dc55fb1` | 4,081 |
| `full-system/local-raw/run-crypto-frames-attempt.py` | `8b3cde5437e397bf050ae97aed7f0c2c2b5956a005ac34fd9aebb207046040bc` | 9,300 |
| `full-system/local-raw/shader_capture.py` | `0b9a84824b46533f32629eca6e2c6949d57046f7494fdf1037a90564f9a857c9` | 12,666 |
| `full-system/shader-inspection/census.py` | `faf0302b833c7fea076047da83ffb0a0ab9d06c97dee2ed86e0e1b0a4b2e5446` | 19,678 |
| `full-system/run-full-attempt.py` | `bccc92b05386b74f06c1c9971c031d17cf08664e55a64fd78442e6922e0f9d5c` | 53,817 |
| `full-system/golden_handoff_wdt_profile.py` | `833906880284305f7d8264e7d13d90619fe622c502a6f1a95ae49e3eb05fb33e` | 1,282 |
| `full-system/stream-ready-local-raw-cleanup4-live5.json` | `989bea15cf0a5a56fe2c35cae4a59b29d00a9aeeff3c193d75fc7726dd73c731` | 956 |

Qualification pin manifest remains `60983a473d8678c7d5b2fad79da129bb28ca8e25cc34b659731822ee72a8c46b`; both prior reports and Mesa runtime manifest also remain unchanged. The new QEMU/archive, old failed state and fresh immutable inputs were checked with two short read-only/network-disabled, CPU-only preservation helpers. They read the named artifact bytes and CONTROL image files, without mounting a guest filesystem.

The actual already-migrated fresh identity is **`5c81e522ad43cf7ad8fd015f007de62a0842b5871c51db131eac64e2ef22d9cb`**, unchanged before/after. It is distinct from the old failed identity `e937...`. No migration was performed again.

| Named artifact | Before SHA256 | After SHA256 | After bytes / st_blocks / allocated bytes |
|---|---|---|---:|
| `/work/orchard-m27-pages-rgb10/artifacts/qemu-system-aarch64` | `87614fc2db5efc0f7293aad13d1f70ffd43d4e3e09380dfd5522ffd419d7202b` | `87614fc2db5efc0f7293aad13d1f70ffd43d4e3e09380dfd5522ffd419d7202b` | 70,844,192 / 138,376 / 70,848,512 |
| `/work/orchard-m27-pages-rgb10/artifacts/libreims_vgpu.a` | `fa8581e23cc7a136d7f0067cfa7fd05da65f5e53c201340ae3c4e2b9cfc63242` | `fa8581e23cc7a136d7f0067cfa7fd05da65f5e53c201340ae3c4e2b9cfc63242` | 174,891,956 / 341,600 / 174,899,200 |
| `/control/boot/aux.work.img` | `c95c480ce3a57809f1845b902b8dfece159f66608fb4612ccf913d00c74d4abb` | `c95c480ce3a57809f1845b902b8dfece159f66608fb4612ccf913d00c74d4abb` | 33,562,780 / 65,560 / 33,566,720 |
| `/control/boot/root.overlay.qcow2` | `2ba20d8dc6ae2f548b367f068aab22c0da580ea1e18cdb6fd9d904f4e93ed41b` | `2ba20d8dc6ae2f548b367f068aab22c0da580ea1e18cdb6fd9d904f4e93ed41b` | 1,028,194,304 / 2,008,128 / 1,028,161,536 |
| `/control/boot/runner-identity.json` | `e9373f3a9cd189c76b2d14219dd433e0dbf699dea616bc9b6c8f529f09f2d066` | `e9373f3a9cd189c76b2d14219dd433e0dbf699dea616bc9b6c8f529f09f2d066` | 1,422 / 8 / 4,096 |
| `/control/boot/AVPBooter.original.bin` | `6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845` | `6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845` | 334,960 / 656 / 335,872 |
| `/control/boot/AVPBooter.patched.bin` | `593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e` | `593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e` | 334,960 / 656 / 335,872 |
| `/control/boot/prepared-inputs.json` | `b5df53f6cd0754ac6160cb1ec0f0f0789dd098a43cd43d04ea736aae1d5687da` | `b5df53f6cd0754ac6160cb1ec0f0f0789dd098a43cd43d04ea736aae1d5687da` | 684 / 8 / 4,096 |
| `/control/fresh-01/boot/aux.work.img` | `da6f45c139956df6b3d4a9a19325fe8087ecedb0a506e1d1e6da70fe0cafaac7` | `a38fd1c53bdca29b7847ea53189f8dfc341940ef03294d9bea6578ea778c0062` | 33,562,780 / 65,560 / 33,566,720 |
| `/control/fresh-01/boot/root.overlay.qcow2` | `8002120f1a24ca2a43f9f87c9b7e3d81afacc20c1b4f92987fe1eb91344e4acd` | `e28340b5ad170a022927e88934908568ef8d1447411af11ec4fedd21c7d12e57` | 620,101,632 / 1,211,048 / 620,056,576 |
| `/control/fresh-01/boot/runner-identity.json` | `5c81e522ad43cf7ad8fd015f007de62a0842b5871c51db131eac64e2ef22d9cb` | `5c81e522ad43cf7ad8fd015f007de62a0842b5871c51db131eac64e2ef22d9cb` | 1,422 / 8 / 4,096 |
| `/control/fresh-01/boot/AVPBooter.original.bin` | `6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845` | `6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845` | 334,960 / 656 / 335,872 |
| `/control/fresh-01/boot/AVPBooter.patched.bin` | `593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e` | `593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e` | 334,960 / 656 / 335,872 |
| `/control/fresh-01/boot/prepared-inputs.json` | `b5df53f6cd0754ac6160cb1ec0f0f0789dd098a43cd43d04ea736aae1d5687da` | `b5df53f6cd0754ac6160cb1ec0f0f0789dd098a43cd43d04ea736aae1d5687da` | 684 / 8 / 4,096 |

Only the fresh AUX/overlay changed naturally. Their final hashes/allocation are retained without reset, copy, repair or revert. Fresh overlay allocation **620,056,576 bytes** remains below 2 GiB. The old failed AUX/overlay/identity, both booter files and prepared reports are unchanged.

Exporter ID `b8472de170f6ab1709e76bef8ca08f48df591ee4ea893f607eae2fddb21ce372`, PID **679**, start **2026-10-28T21:58:44.477275548Z**, remains unchanged. Sampler PID **77088**, start **2026-10-28T18:26:02.6800680Z**, duration argument43200, and allowed Android PID **79064**, start **2026-10-28T08:15:59.0652060Z**, remain unchanged. No service/backend/process lifecycle action was taken.

All **89 original container IDs** and **28 volumes** match. The same 12 original active/restarting entries remain; three pre-existing restart loops advanced counters110→125 independently. The other original active entries, including databases and exporter, retain their recorded identities, starts/restarts and mounts. No unrelated lifecycle or storage change was performed.

Both exact launcher containers and both preservation helpers are absent. Runner/hook exits are recorded, and whole CONTROL has no running users before or after. No manual cleanup occurred. This is a compact named-pin/artifact audit, not a 9,000-file workspace snapshot.

The supplied AGENTS instruction and installed codebase-memory skill were read. Graph/index/coverage tools were unavailable; exact named-source fallback was used without a graph coverage claim. Only these two new evidence files and runner-owned artifacts/pointer were written. Third-party artifacts and report paths are locally ignored; no staging or commit occurred. The requested single experiment ends here for parent review, with no additional boot, GPU test, input or corrective experiment.

