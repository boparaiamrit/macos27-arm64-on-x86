**FAILED_PROXY_SUPERVISOR_FILENOTFOUND_GUEST_IO_ERRORS**. Exactly one invocation used the unchanged **7200-second maximum** and **1700-second startup handoff bound**. Runner status **guard_or_runtime_failure**, elapsed **1920.204 seconds**. Invocation **2026-10-28T04:42:28.4786725Z**; launcher terminal return **2026-10-28T05:14:29.4024051Z**. No retry, delegation or additional boot occurred.

[Exact invocation](invocation.json), [finally receipt](finally-receipt.json), [native runner result](../../attempts/20261028T044229Z-f2xjcx4x/result.json), and [handoff.json](handoff.json) retain the outcome. Launcher code **2**, runner code **130**, QEMU **0**, startup GDB **0**. Process codes do not establish successful boot. The runner received the bounded SIGTERM cleanup request only after the actual proxy failure. Its own cleanup returned QEMU 0 and runner 130; the wrapper reported 2. [Exact runner identification](cleanup-runner-identification.json) and [cleanup request](bounded-cleanup-request.json) verify /usr/bin/python3.13 and the complete runner argv, excluding docker-init. No extra guest control connection was used.

The retained serial supports these separate checkpoints:

- `darwin_kernel`: observed; serial lines 84.
- `normal_system_mount`: observed; serial lines 434.
- `root_hash_authentication_required`: observed; serial lines 426, 438, 794.
- `basesystem_pid1`: observed; serial lines 651.
- `installed_macos_root_pivot_request`: observed; serial lines 795.
- `root_pivot_success`: observed; serial lines 548, 816.
- `data_unlocked`: observed; serial lines 787.
- `data_mount_complete`: observed; serial lines 1614.
- `init_with_data_volume_started`: observed; serial lines 1642.
- `deferred_install_started`: observed; serial lines 1644.
- `fips_passed`: observed; serial lines 1705.
- `fips_result_true`: observed; serial lines 1707.
- `cache_start_started`: observed; serial lines 1713.
- `task_usermanagerd`: observed; serial lines 1716, 1753.
- `task_dirs_cleaner`: observed; serial lines 1725, 1755.
- `task_xpcroleaccountd`: observed; serial lines 1758, 1759.
- `task_init_featureflags`: observed; serial lines 1762, 1763.
- `task_auearlyboot`: observed; serial lines 1767, 1768.
- `auearlyboot_fud_started`: observed; serial lines 1771.
- `auearlyboot_fud_ended`: observed; serial lines 1781.
- `auearlyboot_exiting`: observed; serial lines 1783.
- `task_aidearlyboot`: observed; serial lines 1785, 1786.
- `aidearlyboot_phase_ended`: observed; serial lines 1805.
- `endpointsecurity_no_clients`: observed; serial lines 1817.
- `task_tzinit`: observed; serial lines 1823, 1826.
- `tzinit_data_fallback`: observed; serial lines 1830.
- `task_dirhelper`: observed; serial lines 1832, 1833.
- `filesystem_iteration_time_limit`: observed; serial lines 1836, 1837, 1838, 1839.
- `early_boot_complete_marker`: observed; serial lines 2412, 2413.
- `launchd_spawn_io_error`: observed; serial lines 2374, 2378, 2388, 2390, 2398, 2402.
- `unable_to_load_cache`: observed; serial lines 2410.
- `no_task_access_server`: observed; serial lines 2416.
- `windowserver_marker`: no retained marker; serial lines none.
- `late_service_marker`: no retained marker; serial lines none.
- `fatal_marker`: no retained marker; serial lines none.

[New checkpoint comparison](new-checkpoint-comparison.json) records the exact FudEarlyBoot starting signature and its absence/presence in the prior retained serial. Entry/end/exit markers establish only the recorded early-firmware-update phase; they do not establish installed service-bootstrap or desktop completion.

The later Early boot complete marker occurred among failed task spawns and disk I/O errors; it is not a successful bootstrap-completion checkpoint. No guest panic was retained; AMFI non-fatal diagnostics are classified separately.

Installed root pivot completed after its request: **True**. Task-start, bootstrap-name or WindowServer matches require contextual interpretation; installed service-bootstrap completion remains unverified. [Boot evidence](boot-checkpoints.json) separates host observation upper bounds from guest clock text. No composited interactive frame was captured; GUI and hardware acceleration remain unverified.

Repeated directory-iteration time-limit diagnostics, if present, are retained with exact serial lines; they do not by themselves establish transport cause or a guest hang.

New service/source faults since this invocation, excluding historical recovered failures, are retained in [terminal-service-evidence.json](terminal-service-evidence.json). The runner retained its wall/guest-exit/guard handling, and its owned cleanup was requested after the terminal proxy exit. Quiet logs, OFF prefixes and errno 12 were not grounds for a manual stop. Remaining blocker: **Proxy supervisor_stop recorded FileNotFoundError with generic reason guard or runtime exception at 2026-10-28T05:12:32.834811Z, then terminated/killed its child and exited 1. The missing path and detailed cause were not retained. The original source stayed alive and last recorded layer 52 verified; no new source layer_error/read_error was retained in the bounded log. Guest disk I/O errors, failed boot-task spawns, Unable to load cache and No task-access server followed. No panic was retained. Exact Python runner SIGTERM requested bounded owned cleanup after this actual terminal failure; runner returned 130 after 1920.204s. No bypass, restart or retry occurred.**

Current proxy restart-session cache deltas from the last complete before/after observations: **{"cached_blocks": 356, "hits": 12857, "misses": 356, "requests": 9631, "returned_bytes": 269543424, "upstream_calls": 329}**. Exact emission times, partial terminal events and metadata are in the handoff. Initial populated cache: **5601 blocks**. Metadata before **367,501,312 nominal / 367,509,504 allocated bytes**; after **390,864,896 nominal / 390,873,088 allocated bytes**. The unchanged 512-MiB payload and 1-GiB total caps passed. No SQLite query/copy, cache payload read/copy, cache clear, probe or prewarm was performed. Totals are observations, not completion or causal A/B savings. Host persistent cache and guest cache-start are distinct. No all-layer verification or full-cache coverage claim is made.

[Graphics evidence](graphics-evidence.json) records requested protocol **252**, negotiated **62**, display-online signal/ack and **9 setup packets** in the sole nonzero packet interval. Selected allocation/create/draw/compute/dispatch/queue-submit/present, surface and device-lost/fence-timeout maxima remain **zero**. No error-signature candidate was retained by the documented scan. No new render/protocol checkpoint is established relative to the prior retained setup trace; negotiation, display-online and clamping alone do not establish rendering or fault cause.

Both parent IDs, images, configs, mounts, restart counts and start times match admission. Source alive: **True**; proxy alive: **False**. Sampler **104592** retains its original exact command and start identity and remains alive. All owned VM/launcher/evidence/hash helpers ended; VM container is absent. [Final process verification](final-process-verification.json) and [service inspection](final-services.json) retain the evidence. OOM/OOM-kill/group-kill deltas: **{"macos-golden-read-cache": {"oom": 0, "oom_group_kill": 0, "oom_kill": 0}, "macos-golden-stream-large": {"oom": 0, "oom_group_kill": 0, "oom_kill": 0}, "vm": {"oom": 0, "oom_group_kill": 0, "oom_kill": 0}}**. Unavailable terminal VM cgroups are distinguished from last-live observations.

Across **39 observations**, minimum C: free was **29,132,808,192 bytes** and sample ages ranged **0.039–2.498 seconds**. Original 10-GiB floor, freshness/future limits, source/proxy deadlines and resource/log caps remained unchanged. Service log snapshots retain at most 500 events/lines each.

Preservation comparison: all **324 pre-existing protected source/evidence files** remained unchanged; supplemental admissions/config comparison also passed. The full comparison is **not clean**: it retains **4 new scripts** under `warm-cache-boot/live/recovered-replay/`, outside the allowed exclusions. Their separate report says its proposed launch was refused because this VM was already active; no invocation receipt exists there. These files were preserved and not executed by this task. Exact paths/hashes remain in artifact-verification.json; they have not been hidden by an added exclusion. Only the owned live directory and parent's new offline qmp-frame-qualification directory are excluded new source scopes; normal attempt/current-pointer/CONTROL writes are authorized. All six MAIN/CONTROL shared-lock before/after hashes, QEMU and firmware are in [before-volumes.json](before-volumes.json) / [after-volumes.json](after-volumes.json). MAIN, CONTROL identity, firmware and QEMU remained unchanged. Natural CONTROL AUX/overlay changes were preserved, with no restore. Actual changed CONTROL files: **["aux.work.img", "root.overlay.qcow2"]**.

The original finally receipt records post-run evidence collector code 1: its metadata test reached a synthetic link before applying the offline-scope exclusion. Only owned capture.py was corrected to prune excluded directories before traversal; the read-only post-run collection was repeated successfully. [Recovery receipt](after-capture-recovery.json) preserves this separately from the VM/proxy failure. No boot or CheckOnly was repeated.

Reims gzip was streamed through EOF/CRC without materializing raw/private logs: **11,152,612 expanded bytes**, raw SHA-256 **`2b4c05bc1efe68f07770f4efb5e3ad69505c5e9b6f4db9e67a302c4603119c65`**. Raw SHA, expanded/compressed lengths and metadata/native-result match passed. Retained capture **375,485 bytes** within 8 MiB; expanded data within 64 MiB; all attempt files **1,931,815 bytes** within 64 MiB. All consumed bytes retained: **True**; unretained read bytes **0**; exhausted **False**. [Artifact verification](artifact-verification.json) retains the detailed budget, preservation and guard observations.
