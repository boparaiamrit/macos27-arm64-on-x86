# Prepared RED baseline stopped before staging

The read-only measurement container exited 1 because three actual isolated source hashes differ from `red-source-manifest.json`. This is an identity refusal, not behavioral RED. The explicit stop-before-overwrite rule was followed. No retry or corrective implementation was attempted.

All four destination hashes were collected before the first comparison could stop execution. The root `before` copies match the manifest's expected before hashes, and the prepared copies match its RED hashes. The isolated destination differs for `caches.rs`, `exec.rs`, and `device_features.rs`.

| File under `crates/reims-vgpu/src/backend/vulkan/` | Expected before SHA-256 | Actual isolated before SHA-256 |
| --- | --- | --- |
| `engine/color_input.rs` | `9285223cadaa8cb4de41e13fb5200c7c09dabe6961b8ee1e08912a54a97eb645` | `9285223cadaa8cb4de41e13fb5200c7c09dabe6961b8ee1e08912a54a97eb645` |
| `engine/caches.rs` | `9837057f28f4a7bba03e7a0dbb14135f4b159bebefe5361a8a7a831f45d34166` | `96f5c9b5aa5846713f529bfe79b64b9deddbfa0a5491432b5234d5e87b0ae1ca` |
| `engine/exec.rs` | `c92067b231fa16c3f4222fbb3f52ab3468ccc750df3ba31d330b46413e1c4fc7` | `3480b46d821c2115c76bd530a79cd6ae078cebd732adc7a36b1a2491d0a10309` |
| `caps/device_features.rs` | `4755710e013af0ded15e58e53a0254c1ce4533ba747193ff1ac134875b5a92b9` | `a5102fa9fa23e9f98e31784ad7a15ad5638e7be0c4fa44417cc19a2249c6638f` |

Copied files: 0. Compilations: 0. Tests executed: 0; passed: 0; failed: 0. The requested five behavioral failures remain unverified. No post-copy hashes exist because the build volume remained read-only throughout the sole measurement container. No allocation admission was reached, and no source/target growth was caused by this run. Compiler/source/artifact preservation checks scheduled after the four-file identity check were not reached.

The measurement container used builder image `sha256:14ea78615d69de5eea70014968be23464751916c6c44793f19f5771a9b4eeb17`, actual 4 CPUs, 6 GiB RAM, zero additional swap, pids 256, network none, read-only root, `/tmp` 64 MiB, core limit 0, and filter `0x10`. `/work` and `/parent` were read-only; only `/out` was writable. Docker driver was observed as `overlayfs`. The cgroup memory peak was 29,937,664 bytes; all memory max/OOM counters were zero. The container ended naturally, its attach client was reaped, and the owned container was removed with no remaining ID. TERM/KILL was unnecessary.

Postflight verified all original 89 container IDs and 28 volume names, protected host input hashes, root prepared/before files and manifest, and original orchestration scripts. Sampler PID 77088 retained start `2026-10-28T18:26:02.6800687Z`; exporter retained PID 679/start `2026-10-28T21:58:44.477275548Z`. Android PID 79064 was untouched. No Golden VM was active. The final live sample had 37,357,563,904 free bytes, above the unconditional 10 GiB floor.

Canonical refusal/assertion and exit: `measure-docker-stderr.log`, `measure-failure.json`, `measure-container-state.json`, and `measure-host-watchdog.json`. Full source hashes: `measure-before-source-hashes.json`. Actual envelope/process/cleanup receipts: `measure-docker-observed.json`, `measure-cgroup.json`, `measure-remaining-processes.json`, `measure-owned-cleanup.json`. Preserved inventory/pins: `host-before.json` and `host-after.json`. Structured handoff: `handoff.json`.

Parent handoff: reconcile the actual isolated destination identity with the prepared before manifest before authorizing any new stage. No source, assertion, root manifest, original harness, release artifact, GPU rendering, VM, input, disk/backend/profile/guard, or host-setting change was made.
