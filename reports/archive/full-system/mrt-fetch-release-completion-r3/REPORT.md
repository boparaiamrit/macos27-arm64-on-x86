# R3 renderer qualification blocked

**Core validation failed at explicit device destruction. No archive or QEMU was qualified or published.**

The probe-OFF mixed MRT/depth case produced expected pixels, then reported:

```text
Validation Error: [ VUID-vkDestroyDevice-device-05137 ]
vkDestroyDevice(): VkDeviceMemory 0x200000000020 has not been destroyed.
```

First canonical occurrence: `extra-default-fixed-mixed-depth-off-off-stdout.log:3`. The allocation owner is unresolved. This does not prove a leak in the new refused-probe disposal path: the required eight-refusal case was not reached.

## Current results

| Gate | Actual result |
|---|---|
| Initial exact-parent pure matrix | 16 default + 16 narrow passes |
| Final fixture pure matrix | 16 default + 16 narrow passes; no skips |
| Affected regressions before cfg fixture addition | 237 passing invocations across 17 filters; no skips |
| Original five engine cases before cfg fixture addition | 5 default + 5 narrow; active Core+SYNC; no relevant errors |
| Additional default selected0 seeded/readback/resident reuse | 6 API-clean probe OFF/ON invocations including repeats |
| Mixed-depth explicit teardown | 3 API-failed executions, despite Rust reporting passes |
| Eight refusals, remaining shapes and narrow extras | not reached / unqualified |

Existing cfg(test) PARENT_PROBE_RESTART_EXECUTED receipts occur for both CPU-seeded Preserve and resident LOAD with probe ON, and none with probe OFF. Default ON/OFF readbacks are byte-identical. Narrow probe equivalence remains unqualified.

All 39 raw readbacks were independently checked: 15600 pixels / 62400 channels, exact lengths, finite oracles, quantization tolerance and 144 guard pixels per image. Three mixed-depth readbacks are disqualified as API evidence. Full hashes and comparisons are in readback-independent-audit.json and primary-probe-pixel-equivalence.json.

## Source and compilation

Before source writes, all 1,275 entries and all six exact R2 before hashes matched with zero unknown paths. Only exec.rs was raw-byte copied from 614c0e3dac446f5b3ffe69ad48844b453873cd4994caf48452b99d2421b90f26 to 679c9b59c6c7935ea87a65504dd36285dbec63ff5f0526695678ad58c0c8e3e8. The sole changed line is the unit fixture format: vk::Format::D32_SFLOAT. The other five files retained bytes and mtimes.

Initial and final builds both compiled the unit library and actual vk_engine_parity binary using locked/offline Cargo, backend-vulkan,host-window, jobs=2, existing target and pinned compiler. Required executables have Cargo fresh=false and recorded source/binary fingerprints. Compiler errors: 0. No crate-type rewrite occurred. Normal optimized Cargo cache intermediates remain unqualified.

The final qualification delta is a cfg(test) include in engine/mod.rs plus six new fixture files: two shader sources, two SPIR-V files, a case module and reused pixel helpers. The six parent final file hashes remain exact. All 1,281 current entries match the frozen authority. production-vs-fixture.patch and qualification-only-source-delta.json separate this test delta. No production semantic fix was made.

## Validation and harness failure

The exact Debian layer bundle, Core+SYNC settings and six Mesa26 pins were preserved. Runtime aliases and validation mounts were read-only. Loader logs show actual instance/device insertion; additional cases capture actual layer/driver mappings and print settings. All stdout/stderr are retained. Actual error occurrences: 3, one unique VUID. Observed SYNC hazards: 0, which is not an overall API pass.

The layer wrote the VUID to stdout inside the Rust test-status line. The parser checked the whole-line test name before classifying validation diagnostics, so it first reported a parser assertion. Investigation initially inspected the primary subcase instead of mixed-depth; two additional serial runs repeated the VUID before identification. All failures are unchanged. The corrected harness saves/rejects stdout+stderr validation errors before test-line parsing. No GPU or release action ran after identifying the VUID. Failed mixed-depth runs are excluded from qualification.

The fixture idled the actual queue, destroyed caches and ResourcePools, called DeviceContext::destroy and recorded its return. Core validation reported live native memory at the actual vkDestroyDevice. Current pool source owners are exported for parent inspection. No allocation-owner causal conclusion or production correction is claimed.

## Preservation and resources

All 10 admitted artifacts, 1,261 baseline source entries, 618 compiler files and pinned Rust binaries match before/after. Root manifests/locks are exact. All 89 original container IDs and 28 volumes match. Sampler 84568/start, exporter PID679/start and unrelated Android79064 were verified; no monitor restart or renewal. Older R2 files and failures were host-pinned and preserved.

Measured peak memory: 5347999744 bytes. All max/oom/oom_kill/oom_group_kill events: 0. Minimum guarded host free: 57318711296 bytes, above 10 GiB. Freshness [-2,20], 0.2s polling, pinned CPU/memory/pid envelopes, no extra swap, network none, read-only root, tmp64MiB and core0/filter0x10 were retained. Actual gaps, cgroups and Docker admissions are recorded.

Measured new allocation at preservation: 24359210 bytes within 2 GiB; evidence then 7366808 bytes below 64 MiB. All 13 guarded owned containers were reaped/removed. The preliminary read-only --rm verifier is absent from the final unchanged inventory. No guard/resource/OOM/identity retry occurred.

Owned artifacts directory absent; count 0. No release Cargo action, release metadata, QEMU link/version or final host artifact copy ran. Cache files are independently pinned and explicitly unqualified.

Remaining gates are listed in handoff.json. Imported backing, held-open and feedback cases were not reached. No VM, guest input, guest filesystem read, profile migration, dependency/driver/backend/QEMU upgrade, infrastructure/service cleanup, deployment or commit occurred. Guest acceptance, desktop and interaction remain unverified. Installed codebase-memory skill used with named-source fallback; graph/index coverage unavailable.
