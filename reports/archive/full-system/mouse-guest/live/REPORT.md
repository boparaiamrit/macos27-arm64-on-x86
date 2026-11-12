# Bounded Golden visible-Quit mouse trial

Completed one authorized actual attempt. **ZERO input was sent because no fresh viewed PNG contained a clearly readable Quit label.** Six capture requests completed. No click preview, click request, attestation, coordinates, press, release or input ACK exists. The intended mouse effect remains untested. No further experiment was performed.

## Admission and exact attempt

- Admission SHA256: `4fb909e88d2b058486d4b0887b41a9656568ae6795d7f7a0a496353bf650c845`. All ten protected host hashes matched before and after. API handoff SHA256: `e856e36bec90ad9928eb5e6858702afeb587e480a47984c01e030f04bc8af402`.
- Read parent-admission.json, PARENT-ADMISSION.md, PARENT-PROTOCOL.md and api-qualification/REPORT.md. The new visible-Quit scope supersedes historical title/body restrictions. Parent's 54 CPU tests and two synthetic fixtures were read as API/cleanup qualification only; they were not repeated. The historical positive host inspect-PIPE failure remains preserved.
- Fresh CheckOnly: `20261029T003107Z-dwiap9_0`, exit 0, `inputs_validated_no_vm`, 1.161 seconds. No VM/input in CheckOnly.
- Recorded all 90 existing attempt directory names after CheckOnly and before launch in handoff.json. Actual launch produced exactly one new directory at binding: `20261029T003214Z-emp1_c0b`. No latest-directory selection.
- Owned container: `macos-golden-mouse-01-20261029T003213`. Current launcher metadata had check_only=false, fresh-01 and RGB10 profile. Exact session attempt/allowlist and nonce matched for all six requests; nonce is redacted here.
- Canonical command SHA256: `77f04f910893d2a0ead6a1767d67e77c8a1db10a41b2f4eb50b2d6cd006a0941`. QEMU argv[0] is `/work/orchard-m27-pages-rgb10/artifacts/qemu-system-aarch64`; firmware/AUX/root overlay paths are all `/guest/fresh-01/boot/...`, with no original `/guest/boot/` path.

Both invocations used the exact supplied command; the actual invocation removed only `-CheckOnly`:

```powershell
& ./test-output/arm-macos/full-system/mouse-guest/Launch-MouseAttempt.ps1 -CheckOnly -QemuProfile m27-pages-rgb10 -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup4-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

## Actual terminal result and cleanup

Canonical attempt/result.json reports `status=timeout`, runner exit 124, elapsed **890.221 s**, timeout 900 s with its cleanup reserve, hook timeout 800 s, GDB return 0, QEMU return 0 and last QMP state `running=true/status=running`. PowerShell launcher exited 1 after surfacing the runner's 124. QEMU return 0 does not establish guest completion or desktop usability.

The unchanged owner performed cleanup. stderr.log records signal 15 from its `/usr/bin/python3` owner; no manual stop was issued. The exact container is absent, no matching launcher/hook host processes remain, and CONTROL has no users. All **89** original container IDs and **28** original volume names remain present. This proves inventory preservation, not a new health audit of their contents.

Exporter remains `b8472de170f6ab1709e76bef8ca08f48df591ee4ea893f607eae2fddb21ce372`, PID 679, started `2026-10-28T21:58:44.477275548Z`, running. Sampler 77088 retains actual creation `2026-10-28T18:26:02.680068Z`, with authorized expiry `2026-10-29T06:26:02.680068Z` / 11:56 IST. Android PID 79064 retains creation `2026-10-28T08:15:59.065206Z`. None was restarted, renewed or signaled.

Fresh prelaunch host sample age was 1.528 s with 14,050,181,120 free bytes. Post-cleanup sampled/actual free was 14,012,604,416 bytes. The frozen [-2,20]s/10 GiB guard ran unchanged; no guard failure was reported. No new continuous guard observer was added.

## Mouse wire and perception

Accepted IDs: `capture-01` through `capture-06`, mapped respectively to capture indices 2, 3, 5, 6, 8, 9. All matched `status=captured` responses were read before replacing the request slot. Request count 6/32; explicit captures 6/6; consumed clicks 0/1.

The complete 889-line, 77,384-byte QMP transcript contains only 1 qmp_capabilities, 430 query-status and 9 screendump sends. It contains **0 input-send-event, 0 send-key and 0 human-monitor-command** sends. Therefore wire presses=0, wire releases=0, press/release IDs=null, input ACK order=none. All nine capture commands have separate positive matching ACKs; exact IDs/line order are in handoff.json. Initial boot debugger STOP events precede the first frame; no subsequent STOP/RESET/SHUTDOWN/panic/crashload event appears in the retained QMP transcript.

Durable mouse/state.json ends `click_consumed=false`, `press_framing=not_started`, `release_owed=false`, `quarantined=false`, press/release IDs null, post_frame/post_status null. No release obligation was armed and no fatal mouse cleanup was triggered. This actual guest trial did not exercise the synthetic-qualified press/up or fatal cleanup path. No hidden input, shortcuts, credentials, setup consent, forms or terms were used.

All eight retained PNGs were actually inspected using tools.view_image. All are 1920x1080. No image supplied a readable Quit label. The setup title/body is directly readable in frames 3 and 5; intended target application identity remains unknown because no qualifying target button was observed. No coordinates were selected and no attestation was made.

| Capture index | UTC observation | Retained PNG | PNG SHA256 | Actual visual observation |
| --- | --- | --- | --- | --- |
| 1 | 2026-10-29T00:34:16.037+00:00 | [frame-0001.png](../../attempts/20261029T003214Z-emp1_c0b/frames/frame-0001.png) | `c1161e09bb43363d2777bdb410b3e59e98b33eae3b374322b5e86079ab089a12` | Black initial scanout; viewed offline after cleanup. |
| 2 | 2026-10-29T00:35:16.261+00:00 | [frame-0002.png](../../attempts/20261029T003214Z-emp1_c0b/frames/frame-0002.png) | `4f49f9e44d8e77a63112237804357ce788fa5317f9818c80ff457ba46a4a9560` | Apple logo and progress bar; no Quit label. |
| 3 | 2026-10-29T00:37:41.573+00:00 | [frame-0003.png](../../attempts/20261029T003214Z-emp1_c0b/frames/frame-0003.png) | `324a7f2007a18a42ac935c29735a9b675bbdfa65489d15b0878227f871294ac0` | Keyboard Setup Assistant title/body directly readable; lower control unlabeled; no Quit label. |
| 4 | 2026-10-29T00:39:16.643+00:00 | [frame-0004.png](../../attempts/20261029T003214Z-emp1_c0b/frames/frame-0004.png) | `eed3660c6f56d9eea235bd34e8f453261e9acdb376c866926cb630b7d0842113` | Dock and incomplete white window with title; no readable Quit label. |
| 5 | 2026-10-29T00:41:03.036+00:00 | [frame-0005.png](../../attempts/20261029T003214Z-emp1_c0b/frames/frame-0005.png) | `307cecc36fc58b6ffe7342bcc93d61282740195314d93c0943ec6baebac11328` | Keyboard Setup Assistant title/body directly readable, Dock largely placeholder icons; control unlabeled; no Quit label. |
| 6 | 2026-10-29T00:43:05.336+00:00 | [frame-0006.png](../../attempts/20261029T003214Z-emp1_c0b/frames/frame-0006.png) | `eed3660c6f56d9eea235bd34e8f453261e9acdb376c866926cb630b7d0842113` | Same PNG hash as frame 4; no readable Quit label. |
| 8 | 2026-10-29T00:45:03.521+00:00 | [frame-0008.png](../../attempts/20261029T003214Z-emp1_c0b/frames/frame-0008.png) | `a17b3289ea1e3a5e35bc0766ce40a6689cbb533e9839ecd5728589c4b0a996e7` | Black background, Dock/placeholder icons and clock; no Quit label. |
| 9 | 2026-10-29T00:46:28.138+00:00 | [frame-0009.png](../../attempts/20261029T003214Z-emp1_c0b/frames/frame-0009.png) | `eed3660c6f56d9eea235bd34e8f453261e9acdb376c866926cb630b7d0842113` | Same PNG hash as frame 4; no readable Quit label. |

Frame 7 was a recorded duplicate and was not retained. The pixel changes are natural rendering changes with zero input; there is no before/after mouse-effect pair or proof of guest HID delivery. The unchanged-looking/unlabeled control was never inferred to be Quit.

## Separate boot and desktop checkpoints

| Checkpoint | Actual evidence | Result |
| --- | --- | --- |
| Golden handoff | handoff.json/readback, PC 0xe0a00000, revision/version 3/2, NoSEP contract, hook return 0 | Verified |
| Kernel | serial.log:84 Darwin Kernel Version 27.0.0 | Verified |
| Installed System root | serial.log:405 BSD root disk3s1; :424 successful root hash validation; :431 Macintosh HD mount-complete | Verified |
| Installed Data | serial.log:1614 disk3s5 Data mount-complete | Verified |
| Userspace | serial.log:1642 init-with-data-volume; :1870 Early boot complete | Verified |
| WindowServer | Application/Dock pixels are visible; no extra process observer was used; no WindowServer-named line found in canonical serial/native logs | Visual GUI evidence; named service liveness not independently verified |
| Usable desktop | Incomplete window and mostly placeholder Dock icons; no verified usable Finder/app operation or input effect | **Not established** |

Rendering/RGB10 acceptance remains independent. The real native log contains 99 mapping_gpa_span and 8 rt_wrong_type text matches, no LLVM ERROR match, and no format_unsupported match. These are observations, not a diagnosis or rendering acceptance verdict. No profile, resource, runtime or renderer change was attempted.

## Preservation and resource scope

The QEMU 70,844,192-byte pin `87614fc2db5efc0f7293aad13d1f70ffd43d4e3e09380dfd5522ffd419d7202b` and archive 174,891,956-byte pin `fa8581e23cc7a136d7f0067cfa7fd05da65f5e53c201340ae3c4e2b9cfc63242` match before/after. Fresh runner identity remains `5c81e522ad43cf7ad8fd015f007de62a0842b5871c51db131eac64e2ef22d9cb`; patched firmware matches the canonical validated pin `593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e`.

Short 1-CPU read-only helpers hashed only named files, with CONTROL/build mounted read-only and no guest boot, filesystem mount or large RAW rehash. Original failed AUX/overlay/identity hashes remain exactly `c95c480ce3a57809f1845b902b8dfece159f66608fb4612ccf913d00c74d4abb`, `2ba20d8dc6ae2f548b367f068aab22c0da580ea1e18cdb6fd9d904f4e93ed41b`, `e9373f3a9cd189c76b2d14219dd433e0dbf699dea616bc9b6c8f529f09f2d066`. No reset, repair, revert or migration occurred.

Only the existing fresh writable AUX/overlay changed naturally:

| Named file | Before SHA256 | After SHA256 | After logical / allocated bytes |
| --- | --- | --- | --- |
| `/control/fresh-01/boot/aux.work.img` | `a38fd1c53bdca29b7847ea53189f8dfc341940ef03294d9bea6578ea778c0062` | `1017fa55a49f3a7365902a7e9009632ab53612107dc6e914eeb432226e8b6a16` | 33562780 / 33566720 |
| `/control/fresh-01/boot/root.overlay.qcow2` | `e28340b5ad170a022927e88934908568ef8d1447411af11ec4fedd21c7d12e57` | `acaaae5a170775b2e356a43df7311ad894b07977f460e233c635c5a205f4cbbe` | 631177216 / 631132160 |

Exact supplied resource flags and frozen launcher remained image 13d68aa..., 12 CPU/12 GiB/equal memory-swap, pids 256, network none, read-only container root/build, CONTROL as the only guest writable volume, core ulimit 0, 2 GiB overlay guard, LP128/2 threads/Mesa26/transfer copies/final shader capture. Canonical QEMU command independently records `-m 8G`, `-smp 8`, `tcg,thread=multi,tb-size=1024`. No second runtime resource inspector was attached. No MAIN host volume was mounted by this trial.

The separate readiness authority remains the converter-verified 50,000,000,000-byte RAW, 35,357,175,808 allocated, dev 2096/inode 1146219, checkpoint `82066b4eeda14ff1edb191564b4eaf2806f4bfc042e904a95e56ead9dd06c05d`, all 67 layers and six RO sample matches. Its readiness pin matched before/after. This trial did not repeat full payload/sample verification. Generic runner streamed/localfalse/alllayersfalse fields describe its access mode and do not negate that separate source authority.

Protected host files:

| Path under test-output/arm-macos | Before and after SHA256 |
| --- | --- |
| `full-system/mouse-guest/mouse_controller.py` | `a588d4c5c2bbe7c3fc7051fd8d457977f5dba50e60efda7560a77f51c72bceaa` |
| `full-system/mouse-guest/mouse_files.py` | `c2afa386bfafa85f8e69397830d991b98075e5f22dc5d480163b01d26dcf6b48` |
| `full-system/mouse-guest/mouse_request.py` | `4f35a4d03048325dbd3b6e5b9c96e3b186d98fa0c8471f548339d9f9899aa625` |
| `full-system/mouse-guest/run-mouse-attempt.py` | `eb386465e0daa358480fe057cbe11ea368f9385b80f96ab8b370b0f8842557cc` |
| `full-system/mouse-guest/Launch-MouseAttempt.ps1` | `2cd6e833f46ad1be5814397effe94ab9076dca091aa43d53fa9d089c250314e9` |
| `full-system/local-raw/run-crypto-frames-attempt.py` | `8b3cde5437e397bf050ae97aed7f0c2c2b5956a005ac34fd9aebb207046040bc` |
| `full-system/local-raw/shader_capture.py` | `0b9a84824b46533f32629eca6e2c6949d57046f7494fdf1037a90564f9a857c9` |
| `full-system/local-raw/golden_m27_pages_rgb10_profile.py` | `dcbcc7e59e5a2a4d292226600fe623df61aa63431e6b5eecfeb7d7f6c8fbbb40` |
| `full-system/run-full-attempt.py` | `bccc92b05386b74f06c1c9971c031d17cf08664e55a64fd78442e6922e0f9d5c` |
| `full-system/stream-ready-local-raw-cleanup4-live5.json` | `989bea15cf0a5a56fe2c35cae4a59b29d00a9aeeff3c193d75fc7726dd73c731` |

## Closed evidence integrity

- Native canonical gzip: 565,399 compressed bytes; gzip CRC/EOF valid; full decoded length **7,341,679 bytes**; raw SHA256 `43eeb94a3d24809bc1c8aaa9e9865aaa14a27d2634bcfa4013b3bf0d0e0aae0f`; compressed SHA256 `cb5714822e5e3f66c1403850ad97aec6d2c678cdce65d14c7f43ca32f802cae2`. All consumed bytes retained, no raw/log cap exhaustion; 8 MiB storage and 64 MiB raw limits satisfied. Reims capture source hash matches its result pin.
- Nine frame receipts, eight retained PNGs totaling **337,909 bytes**; complete PNG chunk CRC/IEND/deflate and exact IHDR/raw lengths validated; every receipt SHA/dimension/byte count matched. Per-file 8 MiB, retention 40 MiB and name-scan bounds satisfied.
- QMP 77,384 bytes <1 MiB; all five mouse JSON files <=4096 bytes; six requests <32; six requested captures <=6; zero presses <=1.
- Final shader extraction: 55 files, 397731 bytes; all copied-file hashes verified and extraction caps satisfied. Producer completion and atomic-set completeness are not inferred.
- handoff.json contains exact baseline/post inventory, hashes, resource evidence, receipts, input counts, observations and a SHA256 manifest of the actual attempt artifacts. Nonce, ECID and private boot arguments are omitted/redacted from this report and handoff; runner-created original evidence is preserved untouched.

No delegation, additional launch, retry, restart, second QMP/HMP/GDB client, direct input socket, extra live observer, source/profile/pin/guard/backend/runtime/resource edit or manual stopping occurred. The final blocker is visual approval: **Quit was not clearly readable in this actual bounded run.**
