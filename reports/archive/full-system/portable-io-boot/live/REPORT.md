# Portable stage-I/O Golden checkpoint

One fresh CheckOnly and exactly one actual boot were executed. The guest reached Darwin and early launchd, then panicked after the Data-volume mount failed. This checkpoint did **not** establish shader-I/O correction, WindowServer composition, or a macOS desktop. The broader desktop objective remains incomplete; parent review is the next step.

## Exact execution

- Parent admission: `orchard-build/golden-m27-pages-io/parent-admission.json`, SHA-256 `8bd6832a39fb7ac446e268c4da9bf11de1724246d7e3de5972029b3a9a833000`; unchanged afterward.
- Fresh CheckOnly: `20261028T194955Z-fn588crp`, container `macos-golden-full-20261028T194955`; runner status `inputs_validated_no_vm`, VM false, runner exit 0, runner elapsed 1.349 s, outer elapsed 2.636 s.
- Actual attempt: `20261028T195021Z-86xt55a4`, container `macos-golden-full-20261028T195021`. The attempt path comes from the launcher's canonical result, not a latest-directory guess.
- Started `2026-10-28T19:50:20.7250218Z`; ended `2026-10-28T19:50:52.6117644Z`. Runner elapsed **30.256 s**; outer launcher elapsed 31.681 s.
- Actual launcher count **1**, actual VM count **1**, fresh CheckOnly count **1**. No retry, restart, delegation, second debugger/QMP client, live observer, guest input, manual stop, or extra boot.
- Runner status `qemu_exited_after_handoff`; runner exit 0, outer launcher exit 0, QEMU exit 0, hook/GDB exit 0. These process exit codes coexist with the guest panic and do not prove successful OS boot. The 900 s/800 s deadlines were not reached; the exact runner owned shutdown and cleanup.

Fresh CheckOnly command:

```powershell
& ./test-output/arm-macos/full-system/local-raw/Launch-LocalRawAttempt.ps1 -CheckOnly -QemuProfile m27-pages-io -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup2-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

Actual command, differing only by removal of `-CheckOnly`:

```powershell
& ./test-output/arm-macos/full-system/local-raw/Launch-LocalRawAttempt.ps1 -QemuProfile m27-pages-io -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup2-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

Canonical evidence: `../../attempts/20261028T195021Z-86xt55a4/`; exact logs `checkonly.log`, `launcher.log`, and `census.log` are retained beside this report. `handoff.json` records all artifact lengths/hashes, both source snapshots, commands, counts, and checks.

## Separate checkpoints

| Checkpoint | Observed result | Evidence within exact attempt |
|---|---|---|
| Handoff | Verified PC 0xe0a00000; hook/readback successful | handoff.json; handoff-hook-exit.json |
| Kernel | Darwin 27.0.0 executed | serial.log:84 |
| System | disk3s1 mounted read-only as System root | serial.log:420, serial.log:462 |
| Base System | Later macOS Base System disk5s1 mount and root pivot | serial.log:566, serial.log:569, serial.log:757 |
| Data | disk3s5 mount failed; extentref wrong object, errno 92 | serial.log:1431, serial.log:1433, serial.log:1436, serial.log:1438 |
| Userspace | Early launchd reached; mount-phase-2 aborted and userspace panicked | serial.log:623, serial.log:804; serial.log:1441, serial.log:1443, serial.log:1548, serial.log:1553, serial.log:1567 |
| WindowServer | Not observed | No marker in retained serial/native scope |
| Composited Setup Assistant/login/desktop | Unverified | No retained frame |
| Interaction | Unverified | No guest input authorized or sent |

Serial references use LF-delimited canonical-file line numbers. Selected failure chain:

- `serial.log:1431`: `obj_init:3519: disk3s5 wrong object at 0x29ab7 - wanted oid 0x29ab7 type 0x40000002:0xf xid 0 - got oid 0x29ab7 type 0x40000002:0xb xid 4230`
- `serial.log:1433`: `apfs_mount_livefs:29660: disk3s5 failed to fetch the extentref tree (error 92)`
- `serial.log:1436`: `mount_by_role:536: unable to mount /dev/disk3s5 on /System/Volumes/Data (Illegal byte sequence), failing bootstrap for root device /dev/disk3s1`
- `serial.log:1438`: `mount_phase_two:2407: Data volume mount failed - error 49244 (errno 92)`
- `serial.log:1567`: `panic(cpu 0 caller 0xfffffe002892a410): panic(cpu 0 caller 0xfffffe002892a410): userspace panic: boot task failure: mount-phase-2 - exited due to SIGABRT`

The extentref object at `0x29ab7` was reported as type `0x40000002:0xb` where `0x40000002:0xf` was wanted. Earlier APFS corruption/checkpoint diagnostics also remain in the serial log. These are observed guest diagnostics; this run does not assign their underlying cause to RAW, retained overlay, renderer, or another component. No repair or filesystem inspection outside the boot was performed.

## Native shader and frame evidence

The canonical Reims log selects the **Vulkan** rail (`VulkanOnly`) and records protocol negotiation requested 252 / negotiated 62, display online signal/ack, and native guest control calls. Its last object-cache record at `t=28278` has `m2v=0`, `shaders=0`, `pipelines=0`; all 19 retained drain-duty records report draws=0 and computes=0. Attachment and control calls do not establish rendering.

- Old `fs_variant_partial` / LLVM abort signature: **absent within the retained canonical native log only**. No shader-JIT workload was witnessed; this is not evidence that the earlier LLVM failure is fixed.
- MRT destination-index 1 and half-aggregate typed refusals: no matching refusal observed in this bounded native log; later behavior remains unknown. No speculative correction is proposed.
- Extraction status `empty_capture`, complete=false, atomic=false, copied bytes=0, allocated bytes=0, files=[]; only the 480-byte `.extraction-index.json` exists. Its SHA-256 is `fd09626ae32b8a8a4189b35168ea4162d5b8bdf93b48dc8008fa065ec04c3506`. Status agrees with index, names and sizes match the empty set, index bounds hold, and there are no module or pipeline links to validate.
- Producer admission bounds retained: 32 modules / 256 KiB each / 4 MiB total, 64 pipeline metadata files / 16 KiB each / 128 KiB total. These are evidence bounds, not a guest-completeness guarantee.
- Pinned census helper `faf0302b833c7fea076047da83ffb0a0ab9d06c97dee2ed86e0e1b0a4b2e5446` ran once on this exact extracted directory. Builder image `sha256:14ea78615d69de5eea70014968be23464751916c6c44793f19f5771a9b4eeb17`; 2 CPUs, 512 MiB RAM and equal swap, pids128, network none, read-only root, 64 MiB temporary storage, ARM source read-only, exact attempt writable; no GPU, Work, CONTROL or MAIN mount.
- Census exit **2**, status **incomplete**, module_count **0**, issue `no_module_files`. I/O width census is **unknown**, not a verified result of zero 16-bit interfaces. `--host-storage-input-output16 0` was supplied from parent admission; generic validation cannot establish physical capabilities, and no SPIR-V validation/disassembly was possible without modules.
- Retained PNG count **0**, no frame index or capture timestamps. The runner ended at 30.256 s before the first scheduled frame at 120 s. There are no retained pixels to inspect using `view_image`, and no extra frame was requested. No composited Setup Assistant, login, desktop, or interaction claim is supported.

## Canonical capture integrity

`reims-vgpu-fail.log.gz` was decompressed through EOF with gzip CRC validation. Compressed bytes **6114**, SHA-256 `87e5aa51fe1bf02a03814cf403e73f919b2141a6462338cc7aa6a3937564c032`; raw bytes **115860**, SHA-256 `436e33ab5e8a033c8bd453729aa2cb8b5e8d6452076637539497f7cfce5d86c4`. Raw length/hash agree with canonical metadata and result, both 32,768-byte previews exactly match the raw head/tail, capture closed successfully, exhausted=false, error=null, unretained bytes=0. Allocated capture storage 110592 B, retained bytes 72352 B, all below original limits. No diagnostic cap or truncated tail was reported. `stderr.log` is empty. The handoff lists lengths/hashes of every exact-attempt retained artifact.

## Resource, readiness and preservation results

Pinned runtime `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`; exact launcher configured 12 CPUs, 12 GiB RAM/equal swap, pids256, network none, read-only root, build volume read-only, CONTROL the only guest RW volume, no MAIN mount. Dedicated shader tmpfs 8 MiB, `/tmp` 16 MiB, core ulimit 0, process-local core filter 0x10 written/read back by the unchanged wrapper. Overlay allocation guard 2 GiB; diagnostics storage 8 MiB / raw 64 MiB. Mesa26 manifest `5711c1e0cc73a67cd8643f1d84591651a75f0de2ad27315f0c7709035ba63a0e` and all 6 manifest components match afterward; launcher also verified them before CheckOnly and live. LP128, two software threads, both optional compute-copy paths off. No independent live resource observer was added.

The unconditional host floor remained configured at **10,737,418,240 B** with sample age [-2,20] s. Before CheckOnly sampled free space 11734630400 B (age 0.880 s); immediately pre-live 11730980864 B (age 1.869 s); minimum of retained pre/post verification values 11439636480 B; final sample 11445207040 B (age 0.047 s). No runner floor/freshness/overlay/resource guard failure was reported. A continuous live minimum is not retained by this runner and is not inferred from these samples. Post-run overlay allocated bytes 1028161536 B are below 2 GiB.

Readiness separately retains complete converter authority: all 67 layers verified; checkpoint `82066b4eeda14ff1edb191564b4eaf2806f4bfc042e904a95e56ead9dd06c05d`, RAW 50,000,000,000 logical / 35,357,175,808 allocated B, device2096/inode1146219, read-only export `/stream/golden-live5.nbd`. The ready-file pin is unchanged. Generic runner `streamed`, `local_full_disk=false`, and `all_disk_layers_verified=false` transport labels do not negate that separate complete authority. The 35 GB RAW was not rehashed or mounted.

All ten protected host pins match before and after:

| ARM-relative file | Before SHA-256 | After SHA-256 | Unchanged |
|---|---|---|---|
| `full-system/local-raw/golden_m27_pages_io_profile.py` | `3b6fb7b6c20a3b34641acc7712e4b8e3b5d2655d8ff8b485af5a3c99e06d0dbe` | `3b6fb7b6c20a3b34641acc7712e4b8e3b5d2655d8ff8b485af5a3c99e06d0dbe` | yes |
| `full-system/local-raw/Launch-LocalRawAttempt.ps1` | `203fa06146072adc60d13ae0c94c9491593f0c28785ab6d6f5599e73b32aff03` | `203fa06146072adc60d13ae0c94c9491593f0c28785ab6d6f5599e73b32aff03` | yes |
| `full-system/local-raw/run-crypto-frames-attempt.py` | `a23c34ead897ff188e97a3ac82ec7c0bd54666e5651b6c01e91cef78f2343fc3` | `a23c34ead897ff188e97a3ac82ec7c0bd54666e5651b6c01e91cef78f2343fc3` | yes |
| `full-system/local-raw/migrate-m27-pages-io-identity.py` | `0c411758078ac347bc167dc6a413aaffd517716830b549644b2ab05ec23ae3a8` | `0c411758078ac347bc167dc6a413aaffd517716830b549644b2ab05ec23ae3a8` | yes |
| `full-system/local-raw/shader_capture.py` | `0b9a84824b46533f32629eca6e2c6949d57046f7494fdf1037a90564f9a857c9` | `0b9a84824b46533f32629eca6e2c6949d57046f7494fdf1037a90564f9a857c9` | yes |
| `full-system/shader-inspection/census.py` | `faf0302b833c7fea076047da83ffb0a0ab9d06c97dee2ed86e0e1b0a4b2e5446` | `faf0302b833c7fea076047da83ffb0a0ab9d06c97dee2ed86e0e1b0a4b2e5446` | yes |
| `full-system/run-full-attempt.py` | `bccc92b05386b74f06c1c9971c031d17cf08664e55a64fd78442e6922e0f9d5c` | `bccc92b05386b74f06c1c9971c031d17cf08664e55a64fd78442e6922e0f9d5c` | yes |
| `full-system/golden_handoff_wdt_profile.py` | `833906880284305f7d8264e7d13d90619fe622c502a6f1a95ae49e3eb05fb33e` | `833906880284305f7d8264e7d13d90619fe622c502a6f1a95ae49e3eb05fb33e` | yes |
| `full-system/local-raw/golden_m27_pages_capture_profile.py` | `1e3bcfc3029f06d3c5ca2b6c1ba46cd5de7c7dc6866c8d932c6c9f52b6c9117c` | `1e3bcfc3029f06d3c5ca2b6c1ba46cd5de7c7dc6866c8d932c6c9f52b6c9117c` | yes |
| `full-system/stream-ready-local-raw-cleanup2-live5.json` | `dc63ac3e17369c99c11fb53512d3dba390fba290c9630e72bc48bbebe383b981` | `dc63ac3e17369c99c11fb53512d3dba390fba290c9630e72bc48bbebe383b981` | yes |

Linux artifact and CONTROL hashes:

| File | Before SHA-256 | After SHA-256 | Final bytes |
|---|---|---|---|
| `/work/orchard-m27-pages-io/artifacts/qemu-system-aarch64` | `8db719ff2982a216e64aa2303c8731bdc0d8a2051919f69bc95bbcbd1dd3829b` | `8db719ff2982a216e64aa2303c8731bdc0d8a2051919f69bc95bbcbd1dd3829b` | 70830832 |
| `/work/orchard-m27-pages-io/artifacts/libreims_vgpu.a` | `d9bfdcc73209bf4ead5e52469ae66a6cbfe3566430b9f2e0e0c1ad98bec9abaf` | `d9bfdcc73209bf4ead5e52469ae66a6cbfe3566430b9f2e0e0c1ad98bec9abaf` | 174861242 |
| `/control/boot/aux.work.img` | `3448eeb59469b4b568de1940fe7d7bc8f4c5a403015e77a612669efe805189ea` | `c95c480ce3a57809f1845b902b8dfece159f66608fb4612ccf913d00c74d4abb` | 33562780 |
| `/control/boot/root.overlay.qcow2` | `0f3f74ea41f52513d7b8c81f795b9ffb610f839b89701fabe9a8ead1cf2b4993` | `2ba20d8dc6ae2f548b367f068aab22c0da580ea1e18cdb6fd9d904f4e93ed41b` | 1028194304 |
| `/control/boot/runner-identity.json` | `e9373f3a9cd189c76b2d14219dd433e0dbf699dea616bc9b6c8f529f09f2d066` | `e9373f3a9cd189c76b2d14219dd433e0dbf699dea616bc9b6c8f529f09f2d066` | 1422 |

QEMU and archive additionally match admitted sizes 70,830,832 / 174,861,242 B. CONTROL identity is unchanged. AUX and overlay changed naturally during the one boot and were **retained**; no reset or revert was performed. Overlay logical size and allocation remained 1,028,194,304 / 1,028,161,536 B.

All **9,286** preexisting snapshotted host source files have identical pre/post SHA-256 values; no source edit was made. Snapshot scope is source extensions `.py .ps1 .rs .c .h .cpp .m .mm .sh .toml`, `Cargo.lock`, and `AGENTS.md`, excluding build/cache/dependency directories and attempt/owned output. All **618** compiler manifest files match before and after; frozen manifest SHA-256 `2d5e7d483b966177882ccfa50d3a49a9c81c853dcf57c4992712452b4475da93`. Existing tracked git status remained unchanged. Parent's 211 compiler / 54 focused build / 37 Linux runner tests and both-stack exact-value pixel witnesses remain parent evidence; they were not rerun or promoted to this guest result. The nonrepresentable strict-precision failure remains preserved; no full LLVM precision claim.

Exporter ID `b8472de170f6ab1709e76bef8ca08f48df591ee4ea893f607eae2fddb21ce372`, PID657, start `2026-10-28T18:36:20.269766412Z` is unchanged/running. Sampler PID77088 start `2026-10-28T18:26:02.680068Z` is unchanged and untouched; UTC instants were compared despite JSON fractional-zero formatting. Allowed Android PID79064 start `2026-10-28T08:15:59.065206Z` is unchanged and untouched. Other apps, containers and databases were not targeted.

Owned QEMU/hook exited and were reaped by the runner. Both CheckOnly/live containers and the offline census container are absent, and no running container holds CONTROL. No cleanup, restart or lifecycle change targeted Docker, WSL, exporter, sampler, other apps or databases. Third-party shader/disassembly material remains local/ignored/uncommitted; this run captured no modules. No commit or staging was performed. Reports omit ECID/private boot-argument values.

This is one completed experimental checkpoint with a guest Data-mount panic and incomplete shader/frame evidence. Stop here for parent review; no additional experiment or observer was started.
