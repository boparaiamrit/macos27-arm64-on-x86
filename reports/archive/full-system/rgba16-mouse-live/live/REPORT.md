# One bounded RGBA16 visible-Quit mouse trial

The single actual attempt ended with **status `timeout`, runner exit 124, elapsed 890.244 seconds (14m 50.244s)**. PowerShell surfaced exit 1. **Zero input was sent: no fresh PNG viewed with `view_image` contained a clearly readable Quit label.** Six explicit captures completed. There was no click preview, click request, attestation, coordinate selection, press, release or input ACK. Mouse/HID effect remains untested, and a usable desktop is not established.

## Admission and exact attempt binding

Admission SHA256 `36eba3b809a7c1886d07e3e8e22b740db9eaf7776e7589706cc27b818556644f` matched. All requested admission/protocol/launcher/API records and both prior live reports were read. Their protected/context hashes remain unchanged. Parent evidence of 54 CPU tests, two real synthetic QMP fixtures and nine mocked launcher cases was not rerun. The historical positive fixture's outer Docker-inspect PIPE failure remains preserved; this report does not reinterpret it as complete host-launcher success.

| Operation | Exact attempt / owned container | Terminal result |
|---|---|---|
| Fresh CheckOnly | `20261029T020645Z-fozxf8dn` / `macos-golden-rgba16-mouse-01-20261029T020644` | `inputs_validated_no_vm`, 0, 1.131 s; no VM/input |
| Actual | `20261029T020702Z-kse8w8uk` / `macos-golden-rgba16-mouse-01-20261029T020701` | `timeout`, 124, 890.244 s; launcher 1, GDB 0, QEMU 0 |

The CheckOnly command was exactly:

```powershell
& ./test-output/arm-macos/full-system/mouse-guest/Launch-Rgba16MouseAttempt.ps1 -CheckOnly -QemuProfile m27-pages-rgba16 -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup4-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

The actual invocation removed only `-CheckOnly`, once. All 96 attempt-directory names were recorded after CheckOnly and before actual launch. Exactly one new directory identified this attempt. New `current-rgba16-mouse-attempt.json`, canonical command and mouse session independently matched that identity; the historical `current-mouse-attempt.json` was not used. Command SHA256 `b72984b3090a46c4254cd20f2ba8ef098fdd516020dd6cbbe2df73245bf4bbe8` selects `/work/orchard-m27-pages-rgba16/artifacts/qemu-system-aarch64`, only `/guest/fresh-01/boot` writable state, and no original `/guest/boot` path. The session's exact attempt, local nonce, operations `[capture, click_visible_quit]`, 6-capture/32-request/1-click bounds matched. CheckOnly and actual validated-inputs files are byte-identical.

## Perception and zero-input evidence

Every explicit response was read before replacing the request slot. Each exact referenced PNG was personally viewed with `view_image` at original resolution. Current same-SHA duplicate receipts were viewed again; historical images/positions never supplied approval.

| Explicit ID | Capture index | Fresh receipt UTC | Retained PNG |
|---|---:|---|---|
| `capture-01` | 2 | 2026-10-29T02:11:42.617666+00:00 | `frames/frame-0002.png` |
| `capture-02` | 3 | 2026-10-29T02:13:07.319730+00:00 | `frames/frame-0003.png` |
| `capture-03` | 5 | 2026-10-29T02:14:08.685284+00:00 | `frames/frame-0003.png` |
| `capture-04` | 6 | 2026-10-29T02:15:30.522916+00:00 | `frames/frame-0003.png` |
| `capture-05` | 7 | 2026-10-29T02:17:40.775928+00:00 | `frames/frame-0003.png` |
| `capture-06` | 9 | 2026-10-29T02:20:29.146253+00:00 | `frames/frame-0003.png` |

| Retained frame / first receipt UTC | Bytes / SHA256 | Actual viewed pixels |
|---|---|---|
| [frame 1](../../attempts/20261029T020702Z-kse8w8uk/frames/frame-0001.png) / 2026-10-29T02:09:06.127929+00:00 | 6,121 / `c1161e09bb43363d2777bdb410b3e59e98b33eae3b374322b5e86079ab089a12` | Entirely black; no readable Quit. |
| [frame 2](../../attempts/20261029T020702Z-kse8w8uk/frames/frame-0002.png) / 2026-10-29T02:11:42.617666+00:00 | 8,574 / `bd256b96e651058bb55ba0dc77016b23461642ab816c6809258c1e9ce3801a16` | Apple logo and progress bar; no Quit. |
| [frame 3](../../attempts/20261029T020702Z-kse8w8uk/frames/frame-0003.png) / 2026-10-29T02:13:07.319730+00:00 | 27,698 / `7c13f5dcb9df13cc548700764c3c0ff52c98a0e1e1ae231c30f2aff3d3e92685` | Black background with a partial Dock, mostly placeholder icons; no window, application title/body or Quit. |

Automatic capture indices were 1, 4 and 8. Captures 4 through 9 were exact duplicates of frame 3 and retained no additional PNG. Automatic frame 1 and automatic capture 8's referenced PNG were also viewed. Thus there are nine capture receipts and three retained 1920x1080 PNGs, totaling **42,393 bytes**. No readable Quit appeared and no application identity is claimed.

The complete **78,080-byte, 897-line** QMP transcript has contiguous IDs 1–444: 1 capabilities, 434 query-status and 9 screendump sends, each with a later positive matching reply. It contains **zero input-send-event, send-key, human-monitor-command or other input sends**. Wire presses/releases = 0/0, press/release IDs = null, input ACK order = none. Screenshot RPC IDs were 62, 140, 182, 211, 214, 255, 320, 362 and 404. Exact send/ACK line pairs are in handoff.json. Initial three STOP/four RESUME events occurred before any frame; no later STOP/RESET/SHUTDOWN/panic event is recorded. The NIC filter event is unrelated input evidence.

Durable final mouse state: captures=6, six accepted capture IDs, click_consumed=false, press_framing=not_started, press_id/release_id=null, release_owed=false, quarantined=false, post_frame/post_status=null. No release obligation was armed and no fatal mouse cleanup was exercised. The qualified press/up and uncertain-release paths therefore remain untested in macOS by this run. There is no before/after click pair or named target-application exit evidence; natural image differences and RPC ACKs do not establish HID delivery or action effect.

## Separate guest checkpoints

Line references below use LF-delimited physical serial.log lines.

| Checkpoint | Retained evidence / limit |
|---|---|
| Golden handoff | Canonical handoff/readback verified, PC 0xe0a00000, boot-args revision/version 3/2, NoSEP contract, hook return 0. |
| Kernel | serial.log:84 Darwin Kernel Version 27.0.0. |
| Installed System | :405 BSD root disk3s1, :424 successful on-disk root-hash validation, :431 Macintosh HD mount-complete. |
| Installed Data | :1402 disk3s5 Data mount-complete. |
| Userspace | :1425 init-with-data-volume; :1569/:1570 Early boot complete. |
| Named WindowServer | :3314 names WindowServer[158]/thread724 using more than 50% CPU over180s. This is a named-process observation/warning, not a proven cause of the pixels or an end-of-run liveness check. |
| Composited UI | Partial Dock with Safari/Downloads/Trash shapes and mostly placeholder icons, black remainder. No readable application window or Quit. |
| Input effect | Untested; zero input. |
| Usable desktop | Not established: no verified Finder operation, complete app UI or responsive desktop. |

Scoped searches of closed serial/native/stderr/GDB logs found no LLVM ERROR/physreg-copy abort, kernel-panic or source-read-failure signature. No causal renderer diagnosis is assigned. RGBA16 guest buffer acceptance, filtering and GPU-fence completion remain **unverified**. No MRT route was implemented or probed.

## Owner cleanup and preservation

The original owner ended the run within its 900-second bound, including its normal cleanup reserve. Result mtime is `2026-10-29T02:21:52.851085+00:00`. stderr records QEMU terminating on signal15 from its Python owner. The transcript has no cleanup `quit` send; no synthetic shutdown/cleanup receipt is invented. QEMU return0 is not guest completion. No manual stop, repair, reset, retry, restart or additional boot occurred.

Exact CheckOnly/actual containers and both short read-only preservation helpers are absent. No owned launcher/hook process or running CONTROL user remains. Exporter `b8472de170f6ab1709e76bef8ca08f48df591ee4ea893f607eae2fddb21ce372`, PID679/start2026-10-28T21:58:44.477275548Z remains running. Sampler77088/start2026-10-28T18:26:02.680068Z retains expiry2026-10-29T06:26:02.680068Z; Android79064/start2026-10-28T08:15:59.065206Z is unchanged. All 89 original container IDs and mounts and all 28 volume names remain; this is preservation evidence, not a new application/database health audit.

All **13 protected host pins** match before/after. All16 named volume records matched before launch, and all14 immutable records retain hash/size/allocation/device/inode after cleanup, including original failed boot state, RGB10/RGBA16 executable/archive and both pairs' firmware/prepared files. Fresh runner identity remains `1a69aaaf1876996d68f7a2298c56bb02c1047b9ae4af2eb8c8e0418858040dae`, 1422 bytes. The read-only helper also verified the existing old backup and qemu_sha256-only historical migration; this trial did not migrate identity. Prior live REPORT hashes are unchanged.

Only fresh AUX and overlay changed naturally, retaining original device/inode. No reset/revert/copy was performed:

| Natural file retained after cleanup | After SHA256 | Logical / allocated bytes |
|---|---|---:|
| `/control/fresh-01/boot/aux.work.img` | `af5fd8b3bc11d5a5f8fc7db1ea9e3342891b1c3af3f5d31300481e7e5a10587b` | 33,562,780 / 33,566,720 |
| `/control/fresh-01/boot/root.overlay.qcow2` | `94934224acecba747335f03f3468767fa869cd230b0ea28cdae3e482e1146ca6` | 703,528,960 / 703,483,904 |

Overlay logical/allocated growth was4,259,840 bytes, remaining below the2GiB allocation guard. Named-file helpers used read-only build/CONTROL/parent mounts, no guest filesystem mount, MAIN mount or large RAW rehash.

## Resources, guards and source authority

The admitted image13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635; 12CPU/12GiB/equal total memory-swap/pids256/networknone/read-only root/build/CONTROL-only guest RW; guest8G/8vCPU/MTTCG/TB1024; Mesa26 manifest5711c1e0cc73a67cd8643f1d84591651a75f0de2ad27315f0c7709035ba63a0e; LP128/two threads; compute scatter/gather off; capture tmpfs8MiB/tmp16MiB/core0/filter0x10 and all original capture/resource/deadline bounds were unchanged. No independent live resource observer was attached.

The unconditional10GiB floor and sample age[-2,20]s were unchanged. Prelaunch sample free13,167,595,520 bytes/age0.100s; after-cleanup sample13,160,812,544 bytes/age0.433s. No independent continuous minimum was recorded. The lease covered the entire run and cleanup; no renewal, override or host cleanup occurred.

Cleanup4 readiness pin989bea15cf0a5a56fe2c35cae4a59b29d00a9aeeff3c193d75fc7726dd73c731 and socket `/stream/golden-live5.nbd` remain. The parent's separate complete50,000,000,000-byte RAW/67verified layers/sixRO matches/checkpoint82066b4eeda14ff1edb191564b4eaf2806f4bfc042e904a95e56ead9dd06c05d remains source authority, not reverified here. Generic runner streamed/localfalse/alllayersfalse fields describe its access mode and do not negate that authority.

## Closed artifact integrity

- Native gzip: **410,010 compressed /6,837,768 raw bytes**, full gzip EOF/CRC/ISIZE validated. Compressed SHA256 `3653d823836e4658166203068ee9f869ba882567a803bab4d2d5f98bddc9b08b`; raw SHA256 `6b0c0ea937d521b52da916b4d2954d030de794fea3ac035770938f92dc7c1fd8`. Both previews match exact raw offsets. Metadata/result/source hash match; all consumed bytes retained, no exhaustion/error,8MiB storage/64MiB raw caps pass.
- All PNG chunk CRCs, IHDR/IEND, deflate EOF and exact6,221,880-byte decoded scanline lengths pass, as do every receipt's dimensions/bytes/SHA and8MiB-per-file/40MiB-retention bounds.
- All56 extracted shader files match hashes/sizes:32modules/274,616bytes,23pipeline records/130,715bytes,298-byte producer index. Copied405,629bytes. Extraction and producer bounds pass;32-module cap reached, metadata near128KiB. Capture set atomic=false and producer completeness remains uninterpreted; this is not complete shader history or GPU completion proof.
- QMP<1MiB; five mouse JSON files<=4096bytes;6requests<32,6explicitcaptures<=6,0presses<=1. All83actual and2CheckOnly files were read back and SHA256-manifested in handoff.json.

Only this live REPORT/handoff and exact runner-produced attempt/pointer artifacts were written. No source/controller/protocol/profile/pin/runtime/firmware/identity/guard/resource/backend/service changes, staging or commits; others' edits are preserved. Codebase-memory guidance was read; graph/index/coverage tools were unavailable, so exact named-source fallback was used without graph coverage claims. Initial local-time/schema assertion assumptions and a process query self-match were resolved by read-only metadata reconciliation before any dependent input; no trial or failed guard was retried. Nonce, ECID and private boot arguments are excluded from derived report/handoff; original evidence is untouched.
