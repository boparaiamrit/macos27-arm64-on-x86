# One bounded fresh-01 Golden boot

The separate fresh working state **mounted Data and produced a composited Keyboard Setup Assistant window**. The runner ended at its own timeout. This run does not verify a completed initial OS Setup Assistant, login, full desktop, or interaction. Typed rendering refusals and visible window-border artifacts remain. The failed original AUX/overlay/identity are byte-identical before and after; fresh working state is retained. Parent review is next, with no additional experiment authorized in this handoff.

## Exact execution and ownership

Parent admission SHA-256: `f9d4e9a05be33ceb89d49d5e9c50d6cfe9e3bb3d26056fa06ae0e9016414e0e6`. `PARENT-ADMISSION.md` and the admission JSON were read; all ten admission host pins verified before and after. The supplied AGENTS instruction and installed codebase-memory skill were followed. Graph/index/coverage tools were unavailable in this runtime; named source fallback was used without an index-coverage claim.

| Operation | Exact attempt / container | Outcome |
|---|---|---|
| Fresh CheckOnly | `20261028T203334Z-pd4fp4q7` / `macos-golden-fresh-01-20261028T203333` | `inputs_validated_no_vm`, runner/launcher exit 0, runner 1.133 s, outer 2.411 s |
| Actual boot | `20261028T203357Z-4whjksl8` / `macos-golden-fresh-01-20261028T203356` | `timeout`, runner/launcher exit 124, runner 890.214 s, outer 892.208 s |
| Offline census | `golden-fresh-census-4whjksl8` | exit 0, complete, 32 modules |

Actual start `2026-10-28T20:33:55.8698942Z`; end `2026-10-28T20:48:48.087143Z`. The attempt ID was taken from the launcher's canonical result and matched its `result.json`; no latest-directory guess was used. QEMU and handoff/GDB return codes are both 0 after runner-owned cleanup. They do not establish boot completion. The configured overall/hook bounds remained **900/800 seconds**. The unchanged core reserves ten seconds for cleanup (`run-full-attempt.py:652`), explaining the timeout result at about 890 seconds. Core `full_gui_verified=false` remains untouched; the separate offline visual finding below records application UI composition.

Counts: **1 fresh CheckOnly, 1 actual launcher, 1 actual VM, 1 offline census**. Retries, restarts, extra boots, delegation, guest input, extra debugger/QMP clients/live observers, manual stop, repair, reset and revert actions: **0**. The preparer was not executed again. During the live run only the owned launcher command output was awaited; all analysis below occurred after its container was gone.

Fresh CheckOnly command:

```powershell
& ./test-output/arm-macos/full-system/fresh-guest/Launch-FreshIoAttempt.ps1 -CheckOnly -QemuProfile m27-pages-io -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup3-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

Actual command, with only `-CheckOnly` removed:

```powershell
& ./test-output/arm-macos/full-system/fresh-guest/Launch-FreshIoAttempt.ps1 -QemuProfile m27-pages-io -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup3-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

Exact [CheckOnly log](checkonly.log), [launcher log](launcher.log), [census log](census.log), [canonical result](../../attempts/20261028T203357Z-4whjksl8/result.json), and [structured handoff](handoff.json) are retained locally. Logs include the launcher's expected exit-124 exception. No retry followed it.

## Storage and boot checkpoints

All serial references are LF-delimited line numbers in the exact [serial.log](../../attempts/20261028T203357Z-4whjksl8/serial.log). Native line references below refer to the fully decoded canonical gzip, not the bounded preview files.

| Checkpoint | Evidence / outcome |
|---|---|
| Handoff | Verified PC `0xe0a00000`, boot-args revision 3 / version 2, readback verified, original boot args preserved; exact `handoff.json` and `handoff-hook-exit.json` |
| Darwin | 27.0.0 executed, serial:84 |
| System | BSD root disk3s1, serial:403; read-only System root, :424; mount-complete, :428 |
| Base System / root pivot | Base System mount-complete, :528; pivot and installed-root return, :531-542 and :717-729 |
| Main APFS checkpoint | disk0s2/disk3 largest and best xid **2718**, index **19**; disk3 stable desc18/data15741, :395-396 and :410-411 |
| Data | `/dev/disk3s5` mounted on `/System/Volumes/Data`, :1390; **mount-complete volume Data**, :1398 |
| Installed Data userspace | `init-with-data-volume` boot task, :1421; subsequent service progress |
| WindowServer / loginwindow | WindowServer PID156, :1589; loginwindow PID159, :1882 and :1884; actual composition corroborated by frames |
| Composited application | Keyboard Setup Assistant window visible in frames 0002 and 0003 |
| Initial OS Setup Assistant, actual login, full desktop | Unverified; the Keyboard Setup Assistant utility is distinct from initial OS onboarding |
| Interaction | Unverified; no input was sent |

The prior rejection of checkpoints 4232..4227, selection of 4226, wrong extentref object at `0x29ab7`, Data errno92 failure, and mount-phase-2 panic were **not observed in this retained serial workload**. Data mounted successfully. This supports that the new working state avoids the previously observed retained-overlay failure for this one experiment. It does not qualify the entire base filesystem or identify the writer/root cause of the old corruption.

The parent's separate bounded block comparison in `portable-io-boot/storage-probe/` remains parent evidence: immutable RAW subtypef/xid2704 versus old overlay subtypeb/xid4230 at the specified block, supplied at QEMU map depth0. It was not rerun. Guest-generated snapshot/mount activity in serial is natural VM activity, not a manual filesystem action by this task.

Separate complete converter authority remains: **67 layers verified**, checkpoint `82066b4eeda14ff1edb191564b4eaf2806f4bfc042e904a95e56ead9dd06c05d`; RAW **50,000,000,000 logical / 35,357,175,808 allocated bytes**, device2096/inode1146219, read-only `/stream/golden-live5.nbd`, six matched startup samples. Ready-file pin matches before/after. Generic runner `streamed`, `local_full_disk=false`, `all_disk_layers_verified=false` labels do not negate that separate converter authority. RAW was not rehashed or mounted, and no guest filesystem was read outside the VM.

## Actual graphics, remaining refusals and retained frames

There was real shader work: **293** successful asynchronous translation records; last object-cache levels at native line25251 show m2v300/shaders72/pipelines78/compute_pipelines3. Native line25245 records draw work near the end. These counters describe the observed workload; retained frame pixels provide the composition evidence.

The old `fs_variant_partial` / LLVM abort/assert signature has **0 matches** in the **25,256-line** canonical native log. It was absent during this observed shader workload and application composition. This does not establish universal LLVM correctness or change the parent's earlier nonrepresentable strict-precision fixture failure.

Remaining typed diagnostic records:

- **5** `draw_prepare_color_input_mrt_unsupported destination_index=1` draw refusals; first native line1081.
- **7** asynchronous fragment translation failures plus **4** corresponding draw-translation refusals. Across those **11** diagnostic records, the native emitter refuses a non-bitcastable aggregate containing Float4/Half4 and byte arrays reinterpreted as Half4; first lines9483-9485.
- **38** `draw_prepare_texture_resolve_missing` draw refusals; first line4442 reports unsupported object type12.

These are diagnostic record counts, not deduplicated unique bugs or per-pixel attribution. No fixes were attempted, and the visible artifact is not assigned to a particular refusal. `stderr.log` contains only the read-only `/root/.cache` shader-cache creation warning and cache disabling.

All three retained **1920x1080** PNGs were viewed offline using `view_image`, and their bytes, SHA-256, PNG header dimensions and index were checked. No extra capture was requested.

| Frame | Capture UTC | Bytes | SHA-256 | Offline visual finding |
|---|---|---|---|---|
| [0001](../../attempts/20261028T203357Z-4whjksl8/frames/frame-0001.png) | 2026-10-28T20:36:00.239670+00:00 | 6,121 | `c1161e09bb43363d2777bdb410b3e59e98b33eae3b374322b5e86079ab089a12` | black frame |
| [0002](../../attempts/20261028T203357Z-4whjksl8/frames/frame-0002.png) | 2026-10-28T20:41:00.703672+00:00 | 40,119 | `4390b42192e873c4c0e68bcab4368cb36fa12a3346393410a390de948c992315` | composited Keyboard Setup Assistant window with title, text, rounded border on black background |
| [0003](../../attempts/20261028T203357Z-4whjksl8/frames/frame-0003.png) | 2026-10-28T20:46:02.193640+00:00 | 42,177 | `8d0e6cb9d5c8f016a85995af91fd0bc3c9904d27fb100050c1cc0deecd3fed7e` | Keyboard Setup Assistant window plus top-right day/time; window border has visible rectangular protrusions |

Frame0002 visibly contains text and window chrome, beyond a black/clear-only surface. Frame0003 also shows top-right day/time and visible rectangular window-border protrusions. The aggregate retained PNG size is **88,417 bytes**, below the unchanged 40 MiB retention budget; every frame is below 8 MiB. There is no input/interaction or completed desktop evidence.

## Shader extraction and one offline census

Exact retained directory: [`attempts/20261028T203357Z-4whjksl8/shader-capture/`](../../attempts/20261028T203357Z-4whjksl8/shader-capture/). Extraction status `extracted`, complete=true, capture_set_atomic=false. The **13,502-byte** extraction index SHA-256 is `f83d877aa4bf98466adb7b5f45a2a35ec634203b1983e2fc088045a001758d32`. Index, status and launcher receipt agree; every retained filename/size/hash matches; no extra file exists outside the index except the index itself.

- **32 modules**, **168,456 bytes** total; **25 pipeline metadata files**, **129,543 bytes** total; 299-byte producer index. Total copied **298,298 bytes**, extraction allocated **430,080 bytes**, **58 payload files**.
- All **48** vertex/fragment/kernel module references in the 25 pipeline records resolve to retained, hash-verified modules. Two pipeline records are compute records. Filename encoded module lengths match file bytes.
- Producer bounds hold: 32 modules / 256 KiB each / 4 MiB total; 64 metadata records / 16 KiB each / 128 KiB total. Extraction limits also hold: 128 files, 512 KiB each, 8 MiB retained, 64 KiB index, 8 KiB status.
- The producer index reports `refusal_mask=644`, `eviction=false`, process lifetime, and the module count is at its cap. This is a bounded retained sample. Successful extraction does not establish complete producer/workload capture or atomicity.

Pinned census script `faf0302b833c7fea076047da83ffb0a0ab9d06c97dee2ed86e0e1b0a4b2e5446` ran **once**, only after VM cleanup, on that exact retained directory. [Census JSON](../../attempts/20261028T203357Z-4whjksl8/shader-io-census.json) status **complete**, exit **0**: all **32/32** modules valid under its `vulkan1.2` target environment; **21 fragment, 9 vertex, 2 compute**. Analysis of all **94** input/output interface variables completed: **82 float-width32 interfaces**, **12 int-width32 interfaces**, **0** 16-bit stage-I/O modules, **0** `StorageInputOutput16` declarations, **0** host-contract mismatches for the supplied parent capability. Census module hashes agree with extraction.

This witnesses actual final-module floating stage interfaces at **f32** in the retained sample. Internal half arithmetic and half-precision vertex-buffer storage are different from stage interface width; no full precision or shader semantic-equivalence claim follows.

Census builder `sha256:14ea78615d69de5eea70014968be23464751916c6c44793f19f5771a9b4eeb17`: 2 CPUs, 512 MiB RAM/equal swap, pids128, network none, read-only root, core ulimit0, 64 MiB `/tmp`, ARM source RO and **only exact attempt output RW**; no work/CONTROL/MAIN/GPU mount. Exact argv is in `handoff.json`. CLI used `--output /parent/full-system/attempts/20261028T203357Z-4whjksl8/shader-io-census.json --host-storage-input-output16 0 --host-space-sample /parent/full-system/host-space-live.json`. Generic SPIR-V validation is not proof of physical device capabilities.

## Canonical gzip and retention integrity

`reims-vgpu-fail.log.gz` was decoded through EOF with gzip CRC verification. Compressed **821,235 bytes**, SHA-256 `d1f2a519c133cde555bcb58b4dc0145bcffddf1c0f4eb57e9137d3adfe74c292`; raw **8,690,825 bytes**, SHA-256 `b798571a674e3ed6b0ff1bd3e0c0f8edd61c3318ceef86a74f6658a1a3184a33`. Length/hash agree with both canonical capture metadata and native result. Both 32,768-byte head/tail previews exactly match raw bytes and offsets.

Capture closed, gzip_finished=true, all_consumed_bytes_retained=true, exhausted=false, error=null, unretained bytes0. Allocated capture storage **970,752 bytes**, retained **887,482 bytes**; original storage 8 MiB / raw64 MiB limits hold. No diagnostic stream cap or truncated log tail was reported. `handoff.json` records byte lengths and hashes for every retained exact-attempt artifact, including census, frames and module/metadata files. No decompressed duplicate log was written.

## Limits, readiness, preservation and cleanup

Unchanged pinned runtime `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`; 12 CPUs / 12 GiB RAM and equal swap / pids256 / network none / read-only root / build volume RO / CONTROL mounted RW. Actual `command.json` uses **only `/guest/fresh-01/boot/`** for patched firmware, AUX and overlay. Emulator path is `/work/orchard-m27-pages-io/artifacts/qemu-system-aarch64`; its validated hash matches admission. MTTCG8, TB1024 MiB are recorded in argv. No MAIN mount.

Shader tmpfs8 MiB, `/tmp`16 MiB, core ulimit0, local core filter0x10, overlay allocation polling guard2 GiB, diagnostics8 MiB storage/64 MiB raw remain unchanged. Mesa26 manifest `5711c1e0cc73a67cd8643f1d84591651a75f0de2ad27315f0c7709035ba63a0e` and all six components match; the unchanged launcher checked them before both commands. LP128/two threads and both optional compute-copy paths off were configured by the pinned launcher. No independent live cgroup observer was added; configured limits are not continuous peak-usage measurements.

The host reserve/freshness rule remains unconditional **10,737,418,240 bytes**, sample age **[-2,20] seconds**. Immediately pre-actual free bytes **11,718,656,000**, sample age **1.129 s**, direct free **11,720,916,992**. Final postverification sampled **11,418,017,792 bytes**, age **0.158 s**; minimum of retained pre/post samples **11,418,017,792 bytes**. No reserve/freshness/overlay guard failure was reported. A continuous live free-space minimum is not retained and is not inferred. No cleanup, capacity override, or restart was performed.

All ten protected host pins match before and after:

| ARM-relative file | Verified SHA-256, before and after | Result |
|---|---|---|
| `full-system/fresh-guest/Launch-FreshIoAttempt.ps1` | `9337cd939b57d235bc6dab7e1aef594a8ba04fe39b4002cae57eb595b4b8ca1c` | match |
| `full-system/fresh-guest/prepare-fresh.py` | `a26d22ac1d7cf3a5764d242958909c13733b55d65e61cf7d643329b8002ab5ec` | match |
| `full-system/local-raw/Launch-LocalRawAttempt.ps1` | `203fa06146072adc60d13ae0c94c9491593f0c28785ab6d6f5599e73b32aff03` | match |
| `full-system/local-raw/run-crypto-frames-attempt.py` | `a23c34ead897ff188e97a3ac82ec7c0bd54666e5651b6c01e91cef78f2343fc3` | match |
| `full-system/local-raw/golden_m27_pages_io_profile.py` | `3b6fb7b6c20a3b34641acc7712e4b8e3b5d2655d8ff8b485af5a3c99e06d0dbe` | match |
| `full-system/local-raw/shader_capture.py` | `0b9a84824b46533f32629eca6e2c6949d57046f7494fdf1037a90564f9a857c9` | match |
| `full-system/shader-inspection/census.py` | `faf0302b833c7fea076047da83ffb0a0ab9d06c97dee2ed86e0e1b0a4b2e5446` | match |
| `full-system/run-full-attempt.py` | `bccc92b05386b74f06c1c9971c031d17cf08664e55a64fd78442e6922e0f9d5c` | match |
| `full-system/golden_handoff_wdt_profile.py` | `833906880284305f7d8264e7d13d90619fe622c502a6f1a95ae49e3eb05fb33e` | match |
| `full-system/stream-ready-local-raw-cleanup3-live5.json` | `4ddd5b5785ba9418ce733cbb4c522a6c806d136f2063c5c1af5144a4eccfbdaa` | match |

Emulator **70,830,832 bytes** / SHA-256 `8db719ff2982a216e64aa2303c8731bdc0d8a2051919f69bc95bbcbd1dd3829b` and archive **174,861,242 bytes** / SHA-256 `d9bfdcc73209bf4ead5e52469ae66a6cbfe3566430b9f2e0e0c1ad98bec9abaf` match before and after. Both fresh firmware files and the 684-byte prepared report match the admission hashes and sizes. Compiler manifest `2d5e7d483b966177882ccfa50d3a49a9c81c853dcf57c4992712452b4475da93` and **all618 member files** verified before and after. Parent 211 compiler /54 build /37 runner test results and earlier pixel witnesses were not rerun or relabeled as guest evidence. Existing prior report hash and tracked git status are unchanged. No source, pin, guard, renderer, driver, firmware, identity policy, backend, preparation or launcher edit was performed. No existing attempt was written.

Original failed state `/control/boot/` remains byte-identical:

| File | Same SHA-256 before/after | Bytes after | Actual st_blocks ×512 |
|---|---|---|---|
| `aux.work.img` | `c95c480ce3a57809f1845b902b8dfece159f66608fb4612ccf913d00c74d4abb` | 33,562,780 | 33,566,720 |
| `root.overlay.qcow2` | `2ba20d8dc6ae2f548b367f068aab22c0da580ea1e18cdb6fd9d904f4e93ed41b` | 1,028,194,304 | 1,028,161,536 |
| `runner-identity.json` | `e9373f3a9cd189c76b2d14219dd433e0dbf699dea616bc9b6c8f529f09f2d066` | 1,422 | 4,096 |

New working state `/control/fresh-01/boot/` is retained, including natural writes/creation:

| File | Before SHA-256 | After SHA-256 | Bytes after | Actual st_blocks ×512 |
|---|---|---|---|---|
| `aux.work.img` | `2ca2b332f05e2d6e3663bb4db0982a5feec268a8d1b91460f140ad8d3cb49414` | `38f7d45b7f5fa79f1a7a74ba6943411fb89ff1747f147907620ebe51d0b58a9d` | 33,562,780 | 33,566,720 |
| `root.overlay.qcow2` | `absent` | `1e6eeebfabb20d8931a124c08cc34052675bf65fc386c1c6e7a2678b272c9416` | 377,421,824 | 377,372,672 |
| `runner-identity.json` | `absent` | `e9373f3a9cd189c76b2d14219dd433e0dbf699dea616bc9b6c8f529f09f2d066` | 1,422 | 4,096 |

Fresh identity content naturally equals the old identity bytes under the unchanged core policy; the file was absent after CheckOnly and created by this actual run. It was not copied or manually invented. Fresh overlay allocation **377,372,672 bytes** is below 2 GiB. No pair was repaired, reset, replaced or reverted by this task.

Exporter ID `b8472de170f6ab1709e76bef8ca08f48df591ee4ea893f607eae2fddb21ce372`, PID630, start `2026-10-28T20:15:30.613115349Z`, remains running and unchanged. Sampler PID77088 start `2026-10-28T18:26:02.6800687Z` remains unchanged, with its43200-second lease validated before launch. Allowed Android QEMU PID79064 start `2026-10-28T08:15:59.0652064Z` remains untouched. All89 original container IDs and28 volumes match. No unowned service/process/container lifecycle action was taken.

Owned boot, CheckOnly, census and hash-verification helper containers are absent; QEMU/hook were reaped by the runner, and no running container uses whole CONTROL. The compact hash scope is the named protected files/artifacts, old pair, fresh immutable inputs and618 compiler files; no9,000-file snapshot or all-workspace coverage claim is made. Reports omit ECID/private boot arguments. Third-party bytes remain local, ignored and uncommitted; no staging or commit occurred.

The one requested experiment is complete. Full desktop and interaction remain unverified. Stop here for parent review; no additional boot or corrective experiment followed.
