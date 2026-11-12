# One bounded RGBA16 rendering-only Golden attempt

One fresh CheckOnly and one actual boot were executed with the exact authorized flags. The actual runner ended with **status `timeout`, exit 124, elapsed 890.251 seconds**; PowerShell surfaced exit 1. The runner performed cleanup. Handoff, Darwin 27, installed System, Data and userspace are evidenced. The retained UI is incomplete: frame 2 has readable Quit over a black window body; frame 3 retains the outline, Dock placeholders and clock without readable title/body or buttons. **A usable desktop and interaction are not established.**

**Live RGBA16 buffer-texture acceptance remains unverified.** There are zero direct old fmt0x6e conversion-refusal records and zero direct native buffer-refusal records, but no recorded matching buffer descriptor or native acceptance marker. Refusal absence does not prove that the new path executed. The remaining type2 linear RGBA16 five-mip refusal is a separate texture class.

## Admission, exact binding and terminal outcome

- Admission SHA256 `b8f73e0f714ab07adbb1ff3ff85cff0ae3e364c0f273372cc737016f4ecb7609` matched. All six requested parent records, the full runtime-qualification REPORT, and the prior mouse/RGB10 reports were read. Their hashes are preserved in handoff.json.
- Parent qualification is background evidence: 105 focused tests and 590,436 strict UNORM16 software-Vulkan channel checks, maximum error 2.32834196368e-10 within 1e-6. Source/evidence reviews found no verified findings. This is not guest, GPU-fence, filtering or desktop proof; none of those tests or a GPU probe/build was repeated.
- Parent profile verification reports 27 affected Python tests and 7 mocked launcher cases. The already completed identity migration changed only qemu_sha256. This trial did not migrate, reset or copy the working pair.

| Operation | Exact attempt / container | Actual result |
|---|---|---|
| Fresh CheckOnly | `20261029T012950Z-hg6s0hb7` / `macos-golden-rgba16-01-20261029T012950` | `inputs_validated_no_vm`, exit 0, 1.072 s; no VM |
| Actual boot | `20261029T013011Z-bv_zid_f` / `macos-golden-rgba16-01-20261029T013010` | `timeout`, runner 124, launcher 1, 890.251 s; GDB 0, QEMU 0 |

The exact ID came from the owned launcher's canonical result and was checked against owned metadata and the sole new attempt-set entry, never a latest-directory guess. [result.json](../../attempts/20261029T013011Z-bv_zid_f/result.json) records configured timeout900/hook800, verified handoff, last QMP status running and full_gui_verified=false. The unchanged runner reserves cleanup time inside the 900-second bound. Owner QMP shutdown was **2026-10-29T01:45:01.471814Z**, reason host-qmp-quit; result mtime was 01:45:01.840688Z. QEMU exit 0 is not guest completion.

Both invocations used this exact command; CheckOnly added only `-CheckOnly`:

```powershell
& ./test-output/arm-macos/full-system/rgba16-live/Launch-Rgba16Attempt.ps1 -QemuProfile m27-pages-rgba16 -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup4-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

Canonical command SHA256: `62853c09b6f460218bd818784927fc8394e7873742a461b00e3c55f7974a67e5`. It selects the RGBA16 executable and only `/guest/fresh-01/boot` firmware/AUX/overlay paths. CheckOnly and actual validated-inputs.json are byte-identical. Counts: 1 CheckOnly, 1 actual boot, 0 input, 0 controllers, 0 extra QMP/HMP/GDB clients or live observers, 0 delegation, 0 retries/restarts/additional boots, 0 manual stops. During the live run only the owned launcher output was awaited. All inspection below occurred after launcher exit and verified owned-container absence.

## Separate guest checkpoints

| Checkpoint | Exact retained evidence and limit |
|---|---|
| Handoff | Runner handoff/readback: PC 0xe0a00000, revision/version 3/2, NoSEP contract, 9 writes / 49 bytes, readback verified; hook return 0. |
| Kernel | serial.log:84 Darwin Kernel Version 27.0.0 / RELEASE_ARM64_VMAPPLE. |
| Installed System | serial.log:402 BSD root disk3s1; :423 on-disk root hash validated; :430 Macintosh HD mount-complete. |
| Data | serial.log:1613 disk3s5 Data mount-complete. |
| Userspace | serial.log:1641 init-with-data-volume; :1867/:1869 Early boot complete. loginwindow references :2149/:2151 do not prove completed login. |
| WindowServer | serial.log:1892 names WindowServer[158] triggering shared-region unnest. This proves a boot-time named-process observation, not continued or end-of-run service liveness. Later composited pixels are separate evidence. |
| Composited UI | All 3 PNGs viewed offline with view_image at original resolution. Frame2 Quit/Dock and frame3 Dock/clock are visible; window body/title text is missing. |
| Usable desktop | Not established. No readable KSA title/body or intact usable application, verified Finder operation, or full desktop. |
| Interaction | Untested; zero input authorized or sent. |

No LLVM ERROR / Cannot emit physreg copy instruction / LLVM abort, kernel-panic or disk/read-error signature matched the exact closed serial, stderr, GDB and decoded canonical native logs. QMP has no RESET or guest-panic event. This is scoped to the retained workload. stderr.log records read-only /root/.cache disabling shader cache; no repair was attempted.

## Direct native rendering evidence

Line references below are LF-delimited lines in the fully decoded canonical native gzip. Counts use anchored direct prefixes. Exact regular expressions and every selected direct record are in handoff.json. OFF store_routes counters, refused_by replays, copied substrings and addresses resembling format values are excluded. These are emitted records, not unique failing draws or complete event totals.

The buffer anchor is `^buftex convert_unsupported\b.*\bfmt=0x6e(?:\s|$)`; format need not immediately follow convert_unsupported. Draw classes use the full recorded `^linux_m2v_draw reason=draw_prepare_...` prefix. In the prior mouse canonical log the fmt0x6e anchor matches **9** records, at 3966, 4392, 6332, 8484, 11207, 12479, 13722, 13808 and 15702.

| Direct diagnostic class | Prior mouse | Prior RGB10 | Current RGBA16 |
|---|---:|---:|---:|
| Old buffer conversion fmt0x6e | 9 | 9 | 0 |
| Old buffer conversion fmt0x5a | 0 | 0 | 0 |
| New native buffer refusal | 0 | 0 | 0 |
| MRT destination1 unsupported | 8 | 7 | 7 |
| Texture resolution missing | 5 | 5 | 4 |
| Type2 linear RGBA16 five-mip subset | 1 | 1 | 1 |
| Type12 texture-resolution subset | 2 | 2 | 2 |
| Type11 mapper/view texture-resolution subset | 1 | 1 | 1 |
| Fragment translation | 5 | 6 | 4 |
| Aggregate half-load subset | 5 | 5 | 4 |
| Pending-at-sync translation subset | 0 | 1 | 0 |
| Dual-plane texture unexecutable | 3 | 3 | 2 |
| Render-target wrong type8 | 4 | 4 | 4 |
| Render-target wrong type12 | 4 | 4 | 4 |

- **Buffer RGBA16:** no direct buftex records, matching current buffer shape/stride metadata or native success marker are recorded. The prior mouse buffer record had ref112/buf111/fmt0x6e/384x384, while the current log does not provide an associated buffer descriptor. Do not borrow the prior 384x384/pitch3072 shape as current acceptance evidence.
- **Type2 linear RGBA16:** :4164 records texture_ref114, type2, descriptor length260, fmt0x6e, 5 mips, handle0x707, allocation180224, L0 128x128, bpr1024, reason=linear_sample. This is a direct texture-resolution refusal, separate from the native buffer loader.
- **MRT:** 7 destination_index=1 refusals at :979/:1430/:2502/:5129/:8872/:8885/:12499. No speculative relation to window pixels is assigned.
- **Type8/type12 render targets:** 4 direct rt_resolve reason=rt_wrong_type records each. Type8 lines :4767/:4885/:4918/:4957; type12 :4690/:4700/:5581/:5585. Descriptor size does not establish unsupported descriptor semantics.
- **Aggregate half load:** :3921/:5777/:6347/:6377 refuse reinterpretation of nested Struct storage to Vector(Half,4). These 4 fragment-translation records are separate from buffer-texture format acceptance.
- **Dual-plane/type12 and mapper/view:** :4641/:4653 name pf0x226, 128x128 and160x160 plane pairs, one level. :4708/:4748 refuse type12/descriptor176 texture objects. :13274 is type11/mid66/descriptor56/geom1/256x256/fmt0x226/mapped1/pages20/reason mapper_ref_texture_sample. None proves nested-view dispatch support.
- **Pending translation / debt:** no direct pending-at-sync fragment refusal is present in this run. Aggregate pending/debt counters are not native-acceptance or completed GPU-fence/debt-settlement proof. Filtering and GPU-fence completion remain unverified.

Prior canonical attempts are mouse `20261029T003214Z-emp1_c0b` and RGB10 `20261028T234016Z-utjf3mpx`; their gzip hashes and recomputed direct counts are retained in handoff.json. Prior mouse sent zero input and showed readable KSA title/body without readable Quit. Prior RGB10 showed Quit/Continue without readable title/body. Current frame2 has Quit only; current body/title is unreadable. Working state, times and capture schedules differ. No controlled A/B, rendering improvement or causal claim is made.

## Every retained PNG, viewed offline

All images are 1920x1080 RGB8. All 3 captures were positively acknowledged and retained; no extra capture was requested. Each passed PNG signature, every chunk CRC, IHDR/IEND, deflate EOF and exact 6,221,880-byte decoded scanline checks, plus frame-index size/SHA readback.

| Frame / UTC | Size / SHA256 | Exact visual observation |
|---|---|---|
| [frame-0001.png](../../attempts/20261029T013011Z-bv_zid_f/frames/frame-0001.png) / 2026-10-29T01:32:13.639025Z | 6532 B / `716f54c663a102bdc65a2363dc0b4f431e06cb7a9704eb14efa998fdb443d785` | Black background with a gray partially filled progress bar near the bottom. No Apple logo, title/body, Dock or controls visible. |
| [frame-0002.png](../../attempts/20261029T013011Z-bv_zid_f/frames/frame-0002.png) / 2026-10-29T01:37:14.438635Z | 25739 B / `04436e0bc38a1181552de437b8a37bc9a033ba25c26972cc38cba9a7d1ee2006` | Black window body and faint rectangular border with two small round controls near top left; readable Quit button. No readable application title/body or Continue. Dock shows Safari, Downloads and Trash shapes, with most icons generic placeholders. |
| [frame-0003.png](../../attempts/20261029T013011Z-bv_zid_f/frames/frame-0003.png) / 2026-10-29T01:42:15.279880Z | 28281 B / `7c901af13a6e48ba9f5d3b9715f4d487b8c048be9d3da71567e4c1bdc228313c` | Black window body and faint border; no readable application title/body and no visible Quit or Continue. Dock retains Safari, Downloads, Trash shapes and mostly placeholders; top-right Thu Oct 29 1:42 AM is readable. |

Exact black-pixel counts out of 2,073,600 are 2,067,996; 1,934,656; 1,932,640. Frame1 is a progress-bar frame, not entirely black. Unique-color counts are32/1398/1456. Frame2 nonblack bbox is [173,224,1747,1075]; frame3 [173,6,1900,1075], with exclusive right/bottom. The final frame has neither readable Quit nor Continue. Retained PNG bytes total60,552, below per-file8MiB and total40MiB bounds.

## Closed log, shader and QMP integrity

Canonical [native gzip](../../attempts/20261029T013011Z-bv_zid_f/reims-vgpu-fail.log.gz): **552,594 compressed bytes**, SHA256 `1d75773512ecc958250363613ff16736e7d586277b53604ed6ba4790279910e3`. Full single-member EOF/CRC/ISIZE validation produced **7,302,390 raw bytes**, SHA256 `dd77dac8447e9ad31d7cb3cbdbc809d7ac0f2ea813d026b9c139eff3a9c1bdd1`, matching both metadata and result. Both preview files exactly match canonical raw offsets. All consumed bytes are retained, unretained0, no exhaustion/error/truncated tail. Actual retained file bytes618,841 match accounting; recorded Linux allocation692,224 is below8MiB. Compressed and raw limits pass8MiB storage/64MiB raw.

All **56** shader extraction files match size/SHA readbacks: **32 modules / 273,108 bytes**, **23 pipeline records / 129,851 bytes**, plus the299-byte producer index. Copied total403,258 bytes; recorded allocation561,152. Bounds pass32modules/256KiB each/4MiB total and64pipelines/16KiB each/128KiB metadata. The32-module cap was reached and metadata129,851 is near131,072. Extraction is complete/nonempty, capture_set_atomic=false, producer_capture_complete=not_interpreted. Producer refusal_mask644 is retained without invented decoding. **This is not complete shader history**; no semantic census or GPU probe was run.

Closed QMP transcript: 77,518 bytes/896 lines, one greeting, contiguous owner IDs1-443, 1 capabilities, 438 query-status, 3 screendump and1 cleanup quit. Every send has a later positive matching reply. Screendump IDs62/211/360 have ACK lines133/431/729. Owner quit ID443 at line894 has ACK896 and host-qmp-quit SHUTDOWN at line895. Three STOP/four RESUME events precede captures during handoff. Zero send-key/input-send-event/human-monitor-command; no input/controller/session artifacts. Existing FrameQMP was the sole QMP owner; the existing handoff hook was the only GDB client.

All **78 actual-attempt files** and **2 CheckOnly files** were read back and SHA256-manifested in handoff.json. ECID/private boot-argument values are omitted from this report and the test handoff; original runner artifacts remain untouched.

## Resources, source authority and guards

Pinned launcher/profile and canonical command retain runtime image13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635; 12containerCPUs/12GiB/equal total memory-swap/pids256/networknone/read-only root/build; CONTROL-only guest RW at fresh-01. Canonical guest command retains8G RAM/8vCPUs/MTTCG/TB1024. Mesa26 manifest5711c1e0cc73a67cd8643f1d84591651a75f0de2ad27315f0c7709035ba63a0e, LP128/two threads, compute scatter/gather off, capture tmpfs8MiB, tmp16MiB, coreulimit0/filter0x10 remain configured/enforced. No added live resource observer or independent cgroup-peak measurement was used.

Unconditional host floor10GiB, sample age[-2,20]s and allocated-overlay guard2GiB remain unchanged. Before preservation sample: 13,199,003,648 free bytes, age0.214s; immediately before actual: 13,197,774,848 bytes, age0.226s; after cleanup: 13,204,905,984 bytes, age0.493s. No independent continuous minimum was retained. Sampler77088 retains actual start2026-10-28T18:26:02.680068Z/duration43200/expiry2026-10-29T06:26:02.680068Z. Run and cleanup ended before expiry; no renewal/restart/guard override/host cleanup occurred.

Cleanup4 ready pin989bea15cf0a5a56fe2c35cae4a59b29d00a9aeeff3c193d75fc7726dd73c731 matches before/after, NBD socket /stream/golden-live5.nbd. Separate parent converter authority remains50,000,000,000 logical RAW bytes,35,357,175,808 allocated, dev2096/inode1146219, checkpoint82066b4eeda14ff1edb191564b4eaf2806f4bfc042e904a95e56ead9dd06c05d, all67 layers/six RO matches. Generic runner streamed/local_full_disk=false/all_disk_layers_verified=false describes its access mode and does not negate that separate authority. No35GB RAW rehash, MAIN mount or guest-filesystem read outside the VM occurred.

## Preservation and retained natural writes

All10 admission host pins match byte count/SHA before and after. Qualification pin manifest remains69ad1d02320ca14224d90a7f07a798f0b869a184617aedbb14fc3026bdf4511b. Both prior reports, six parent records, qualification REPORT/handoff/GPU result and runtime manifest retain their hashes. Full named before/after records are in handoff.json.

Both RGBA16 artifacts remain QEMU553102765a9da19efee87112f85190835d7d0bc3ca0e55539c375f948e302bfe/70,844,192B and archive4ed34bcbca161a6b0e06df39c6ad13196ed691cbf69c9ce0b583b313ae64da99/174,892,356B. Admitted RGB10 executable87614fc2db5efc0f7293aad13d1f70ffd43d4e3e09380dfd5522ffd419d7202b and archivefa8581e23cc7a136d7f0067cfa7fd05da65f5e53c201340ae3c4e2b9cfc63242 remain unchanged. All14 immutable named-volume files match hash/size/allocation/device/inode.

Fresh identity remains **1a69aaaf1876996d68f7a2298c56bb02c1047b9ae4af2eb8c8e0418858040dae,1422B**; read-only semantic verification also rechecked the exact old-byte migration backup and qemu_sha256-only change. Original failed /control/boot AUX c95c480ce3a57809f1845b902b8dfece159f66608fb4612ccf913d00c74d4abb, overlay2ba20d8dc6ae2f548b367f068aab22c0da580ea1e18cdb6fd9d904f4e93ed41b and identitye9373f3a9cd189c76b2d14219dd433e0dbf699dea616bc9b6c8f529f09f2d066 remain byte-exact and were never selected. Both pairs' booter/prepared files remain unchanged.

| Natural fresh-01 file | Before SHA256 | Retained after SHA256 | After logical / allocated bytes |
|---|---|---|---:|
| `/control/fresh-01/boot/aux.work.img` | `1017fa55a49f3a7365902a7e9009632ab53612107dc6e914eeb432226e8b6a16` | `507a9491ea7563ee99a321a6e56ad3f82dbf83220c8ab4c7c29897a957d8e764` | 33,562,780 / 33,566,720 |
| `/control/fresh-01/boot/root.overlay.qcow2` | `acaaae5a170775b2e356a43df7311ad894b07977f460e233c635c5a205f4cbbe` | `6fcc0168040e6d3849c0d50a3db0e01916a0d3a317c9e4b3fa47d563bb19009a` | 699,269,120 / 699,224,064 |

Overlay grew naturally by68,091,904 logical/allocated bytes and remains below2GiB allocated. AUX size/allocation and both file identities are unchanged. Natural guest writes are retained without reset, repair, copy or revert.

Exporter b8472de170f6ab1709e76bef8ca08f48df591ee4ea893f607eae2fddb21ce372/PID679/start2026-10-28T21:58:44.477275548Z remains running and unchanged. Sampler77088 and allowed Android79064/start2026-10-28T08:15:59.065206Z retain their process identities. All89 original container IDs/28volumes and mounts remain. Existing restart-loop counters may advance independently; no unrelated lifecycle action was performed. This is an inventory/pin audit, not a new health audit of applications or databases.

Exact CheckOnly/actual containers and both read-only named-file preservation helpers are absent; no matching owned host launcher/hook processes and no running CONTROL users remain. Helpers mounted only build/CONTROL/parent paths read-only and did not mount guest filesystems or MAIN. First post-cleanup Windows process listing hit a local cp1252 decode error before any helper or state write; explicit UTF-8 read-only listing completed the audit. This was not a boot retry or lifecycle correction.

Only the two new test evidence files and this runner's exact attempt artifacts/pointer were written. Others' changes were preserved; no source/profile/pin/firmware/identity/runtime/resource/guard edits, staging or commits. Installed codebase-memory guidance was read; graph/index/coverage tools were unavailable, so exact named-source fallback was used without a graph-coverage claim. No further experiment.
