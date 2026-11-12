**INTERRUPTED_RUN_WITH_HOST_SAMPLE_GUARD_FAILURE.** Exactly one invocation of the exact authorized Golden command occurred at **2026-10-28 11:08:42.145 IST / 2026-10-28T05:38:42.1454243Z**. It was configured for 7200 seconds with a 1700-second startup handoff bound, but **did not complete the 7200-second run**. No retry, extra CheckOnly, delegation, additional debugger/observer/QMP/HMP connection, runtime capture or guest input occurred.

The actual source recorded **GuardError: missing or malformed host-space sample**, then `read_error`, `guard_stop`, and its supervisor's terminate/reap. The proxy recorded **OSError / supervisor_stop**, `read_failed`, terminate and stopped. These are actual terminal service failures; no bypass or restart was attempted. Proxy finished **2026-10-28T06:39:18.6972325Z**, source **2026-10-28T06:39:20.176777513Z**, both code **1**. The source error was first emitted at **2026-10-28T06:39:18.5073004Z / 12:09:18.507 IST** while fetching layer **27**, read offset **17,060,724,736**. The proxy event did not retain the OSError filename or detailed reason. This is not direct evidence of another journal race.

The tool call was reported **aborted**. On reconnection, the owned VM, launcher and evidence collector were absent; **sampler PID 128008 was also absent**, unexpectedly before its supplied expiry. Both exec session IDs were unknown. The **native result.json and native launcher finally-receipt.json are absent**. Their exit codes are **unknown**, including QEMU/runner/launcher. Startup hook return **0** and its revision-3 readback/handoff verification are retained; these do not establish guest boot success. The Docker event query returned no historical events, so it did not recover VM exit details.

**Cause and ordering remain unresolved:** the tool interruption, disappearance of host processes/VM, and parent guard failures are correlated observations, not a proven causal chain. The last stored host-space sample has observed_at **2026-10-28T06:39:11.584Z** and **28,352,643,072 bytes free**; later reads found a valid but stale sample. That does not establish what the source could read at its failure. No low-space condition is proved. No restart, new sampler, sample rewrite or cache recovery was attempted.

[Invocation](invocation.json), [interruption receipt](interruption-receipt.json), [terminal services](terminal-service-evidence.json), [reconciliation receipt](reconciliation-finally-receipt.json), [artifact verification](artifact-verification.json), [handoff](handoff.json).

The VM was last observed live at **2026-10-28T06:38:14.253938+00:00**, **3572.109 seconds** after invocation. It was first confirmed absent at **2026-10-28T06:43:54.446951+00:00**, **3912.302 seconds** after invocation. Its exact terminal time and elapsed duration are unknown. Guest log clock text is kept separate from conservative host observation bounds in [boot checkpoints](boot-checkpoints.json).

| Milestone | Status |
| --- | --- |
| 1 Docker environment | Parent verified |
| 2 ARM emulation on this Intel PC | Parent verified |
| 3 Pinned Golden image identity | Parent verified; no claim all 67 streamed layers are verified |
| 4 Streamed disk and persistent read cache | Parent verified; this run later lost parent services |
| 5 Firmware to macOS handoff | Verified readback retained this run |
| 6 Kernel and authenticated System mount | Retained this run |
| 7 Data, early userspace and FIPS | Retained this run |
| 8 Reliable full service-bootstrap completion | **Unverified** |
| 9 Actual graphical login/desktop frame | **Unverified; no capture admitted** |
| 10 Mouse, keyboard, apps and graphics behavior | **Unverified; no guest input admitted** |

This is a ten-item checklist, **not 70% of effort or time**. No composited interactive frame, desktop or hardware acceleration was established.

The retained serial has **1925 lines**. It records root pivot, Data mount, FIPS pass, later early tasks, and **Early boot complete. Continuing system boot.** at lines **1907/1909**. Later `xpcproxy` unnest diagnostics are present, but no retained reliable full service-bootstrap completion, WindowServer, loginwindow, panic or disk-I/O-error marker was found. Three filesystem directory-iteration time-limit lines and seven explicitly non-fatal AMFI diagnostics are retained separately. They do not establish transport cause, a hang or a guest panic. Early boot complete remains an early-phase marker.

[Full comparison](new-checkpoint-comparison.json) found **no newly named boot tasks** relative to previous **044229Z-f2xjcx4x**. Earlier progress commentary that called finish-demo-restore new to the prior task list was incorrect and is corrected here. The current retained serial has no disk I/O error / failed spawn I/O error / Unable to load cache / No task-access server marker, whereas the previous failed attempt did. This limited log difference does not prove full startup or causal savings.

| Serial checkpoint or candidate | Matches | Lines |
| --- | ---: | --- |
| `darwin_kernel` | 1 | 84 |
| `normal_system_mount` | 1 | 463 |
| `root_hash_authentication_required` | 3 | 455, 467, 833 |
| `basesystem_pid1` | 1 | 680 |
| `installed_macos_root_pivot_request` | 1 | 834 |
| `root_pivot_success` | 2 | 577, 845 |
| `data_unlocked` | 1 | 810 |
| `data_mount_complete` | 1 | 1643 |
| `init_with_data_volume_started` | 1 | 1671 |
| `deferred_install_started` | 1 | 1673 |
| `fips_passed` | 1 | 1734 |
| `fips_result_true` | 1 | 1736 |
| `cache_start_started` | 1 | 1742 |
| `auearlyboot_fud_ended` | 1 | 1810 |
| `aidearlyboot_phase_ended` | 1 | 1834 |
| `endpointsecurity_no_clients` | 1 | 1846 |
| `filesystem_iteration_time_limit` | 3 | 1865, 1871, 1906 |
| `early_boot_complete_marker` | 2 | 1907, 1909 |
| `disk_io_error_exact` | 0 | none |
| `launchd_spawn_io_error` | 0 | none |
| `unable_to_load_cache` | 0 | none |
| `no_task_access_server` | 0 | none |
| `windowserver_marker` | 0 | none |
| `late_service_marker` | 0 | none |
| `fatal_marker` | 0 | none |

[Graphics evidence](graphics-evidence.json) covers only the decodable retained prefix. Requested protocol **252**, negotiated **62**, display-online signal/ack, and **9 setup packets** are retained. Selected allocation/create/draw/dispatch/compute/queue-submit/present/surface/device-lost/fence-timeout maxima remain **zero**. No error-signature candidate was retained by that scan. No new render checkpoint was found relative to prior setup evidence. OFF prefixes, negotiation and display-online are not frame proof; missing suffix data cannot be assessed.

**Reims artifact verification is incomplete/failed:** EOF/CRC check raised **EOFError: Compressed file ended before the end-of-stream marker was reached**. The archive is unchanged, not repaired. It decodes to a prefix of **21200694 bytes**, SHA-256 **d175541797ce8cf6f0bf381604347798681c09b14aa7b2ea5cb760384cef077b**, matching its last **active** metadata length/hash. Compressed length **591027 bytes** also matches that metadata. Metadata says gzip_finished=false and status=active; prefix agreement is not completed gzip/trailer CRC validation. No native result exists for metadata/result matching. No final lossless-retention claim is made. Last active retained count **657278 / 8388608 bytes** and decoded prefix below **64 MiB**; all retained attempt files total **2482828 bytes / 64 MiB**. No raw/private Reims output was materialized.

Cache began at **5,957 blocks / 390,397,952 payload bytes**. Stat-only initial metadata: **390864896 nominal / 390873088 allocated bytes**. Last live stat-only metadata at **2026-10-28T06:38:14.253938+00:00**: **409563136 / 409571328 bytes**, payload **409,075,712 bytes**; these observed values were below the unchanged 512-MiB payload and 1-GiB total caps. **Final cache stat was unavailable** after proxy exit; no replacement cache helper was admitted with absent sampler/failed guard. No SQLite queries, payload reads/copies/probes, cache clear or prewarm occurred. Cache and source volumes are preserved.

Current proxy-session first-to-last complete emitted deltas: **{"cached_blocks": 287, "hits": 13834, "misses": 287, "requests": 10472, "returned_bytes": 288339456, "upstream_calls": 244}**. First complete emission was after invocation and recorded one request/one hit; its initial interval is not measured by that difference. Last complete emission reports **6,244 blocks**. Historical pre-restart counters are excluded. Source last-complete-emission deltas: **{"cached_bytes": 234643456, "fetch_count": 37, "fetched_bytes": 16956088327}**. Source fetch count includes repeated layers; cached_bytes is occupancy. Emissions may lag in-flight work. These are not success/all-layer/checkpoint, bandwidth-saving or causal A/B proofs. At most 500 events per service are retained for each bounded snapshot. See [source counters](source-counter-deltas.json) and handoff.

Across **75 last-live observations**, minimum C: free **28319395840 bytes**, maximum sample age **2.624s**. This sampled interval ended before the terminal evidence gap. The 10-GiB floor, 20-second age / two-second future limits, source/proxy 900s deadlines, cancellation, finite memory/CPU/cache/overlay/log bounds were not edited or bypassed. Quiet/OFF/errno12/unproved hang did not trigger a manual stop. Last-available OOM/OOM-kill/group-kill deltas were zero for VM and both parents; **terminal cgroups are unavailable**, so the unobserved terminal gap is not asserted OOM-free. Docker parent states retain OOMKilled=false.

Preservation: **all 344 pre-existing protected source/admission hashes match**, supplemental admission/config comparison has no changes, and there are **no new unexpected source additions during this run**. Previously disclosed orphan-agent additions are preserved separately in preexisting-orphan-additions.json; they are not hidden, removed or claimed as authored here. Only own live and the parent's frozen qmp-frame-qualification scope are excluded; normal attempt/current pointer/CONTROL writes are authorized. The exact production, runner, firmware, QEMU and image pins were verified before invocation. No tests/builds/installs or existing-file edits were performed by this task.

The shared-lock six-file before/after snapshot verifies MAIN AUX/overlay/identity unchanged, CONTROL identity unchanged, QEMU and both firmware hashes unchanged. Natural CONTROL AUX and overlay changes remain paired and preserved without restore: AUX **c2bcfda51c641a8ab6ee524576e7fdc6a724528eb110ac61e254706bdbad1ece**, overlay **f7f36e48eeb555b477a3fd1677964c43aee55e14daa94dd68e4cf53c6a835eb4**. Overlay allocated **21,176,320 bytes**, below 2 GiB. The bounded read-only after-volume hash helper exited; no VM or parent service was started for that evidence collection.

[Final process verification](final-process-verification.json): owned VM/launcher/monitor/hash helpers absent and no running container owns CONTROL. **Parent proxy/source are exited and sampler 128008 is absent**; parent IDs/images/configs/mounts/restart counts/StartedAt are unchanged, and nothing was restarted. No manual VM cleanup signal was needed after reconnection because it was already absent. The natural finally cleanup path could not be proven from missing receipts.

**Remaining blocker:** Actual parent source GuardError: missing or malformed host-space sample; proxy also stopped with OSError. Sampler 128008 is absent. Tool execution was interrupted and owned VM/launcher disappeared without native result/finally or a completed gzip trailer. The disappearance cause and exact ordering are unproved. Reliable full service bootstrap remains unverified; GUI frame/interaction were not admitted or observed. Parent sampler/transport lifetime and access must be re-admitted by the parent before any future boot.

The independent SQLite journal defect and its admitted 40/40 tests remain separate evidence. The previous production missing filename was unretained, so direct attribution to that individual runtime journal is still inferred. This run's new source GuardError and proxy OSError do not establish a journal regression.
