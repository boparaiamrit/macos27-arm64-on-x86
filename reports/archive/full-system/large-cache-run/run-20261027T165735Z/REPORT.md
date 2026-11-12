# Bounded large-cache live5 execution

Status: **stopped_at_first_failure**.

First exact failure: Reviewed source hash mismatch: frozen.py.

The original backend was neither started nor reused. The new backend and existing host sampler were left under parent ownership. No runner, launcher, reader, backend, frozen converter, guard, firmware, or ACTIVE-STATE file was edited by this execution.

| Stage | Actual duration | Result |
|---|---:|---|
| Existing backend warmup | incomplete | No readiness claim |

Prewarm used 0 deduplicated observed boot reads, 0 requested bytes. List SHA256: `not created`. Response hashes, read counts, and timings are retained; payload bytes were never persisted.

Final backend verified fetches: 4; fetch starts: 5; unique verified layers: [0, 26, 48, 52].

Final cached payload: 2147483648 bytes. Actual cgroup memory peak: 2777952256 bytes; hard limit 6442450944 bytes. Memory events: low 0; high 0; max 0; oom 0; oom_kill 0; oom_group_kill 0.

Minimum observed valid host-space sample: 33612533760 bytes. No sampler refresh or reserve/freshness bypass was performed.

Protected source hashes unchanged: **True**. Exact before/after hashes are in source-hashes-before.json and source-hashes-after.json. Existing input/source identity is also checked by the unchanged real-input preflight.

## Actual guest evidence

No VM was started by this run.

Kernel banner, mounted installed root, launchd, and GUI remain separate unverified gates. `full_gui_verified` remains false. QEMU running or a debugger exit status is not kernel-boot proof.

## Evidence

See handoff.json, orchestration.jsonl, server.stderr.log, export-ready.verbatim.json (if ready), prewarm-reads.json, prewarm.stdout.log, per-stage cgroup/inspect snapshots, source hashes, and the unchanged runner attempt directory.
