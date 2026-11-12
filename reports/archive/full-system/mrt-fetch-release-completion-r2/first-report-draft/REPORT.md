# Final renderer packet qualification blocked

The approved final packet does not compile as a unit-test library. The locked, offline release-profile qualification build exited **101** with **E0277** at `crates/reims-vgpu/src/backend/vulkan/engine/exec.rs:8854`:

```text
error[E0277]: the trait bound `ash::vk::Format: From<u16>` is not satisfied
    --> crates/reims-vgpu/src/backend/vulkan/engine/exec.rs:8854:75
     |
8854 |             format: crate::protocol::pixel_format::MTL_FORMAT_RGBA8_UNORM.into(),
     |                                                                           ^^^^ the trait `From<u16>` is not implemented for `ash::vk::Format`
     |
     = note: required for `u16` to implement `Into<ash::vk::Format>`
```

This expression is in the parent-provided new ownership test. Its source SHA-256 is `614c0e3dac446f5b3ffe69ad48844b453873cd4994caf48452b99d2421b90f26`. The parent must supply corrected approved fixture bytes. No production fix or local change to this test was made.

## Gate results

- Parent admission SHA-256 matched `fb655e5a748c1f5653e35baea2ee68454404c137b9c607934afe27bb15becf97`.
- All 1,275 initial source entries were checked against initial qualified authority plus the six authorized files. Unknown source paths: **0**. The six files were approved green states.
- Three already-final files were left byte-identical; the remaining three were staged directly from their final packets. Exact hashes, sizes and current mtime receipts are in `staged-source-hashes.json`.
- Final source check: all 1,275 entries match that exact final authority. Qualification fixture source delta: **0**.
- Fresh unit-lib and actual `vk_engine_parity` compilation was attempted in one locked/offline Cargo action using `backend-vulkan,host-window`, jobs=2, existing target cache and pinned local compiler. Unit-lib compile failed. Cargo observations are preserved; no cached binary was used to claim qualification.
- Required pure default/narrow matrix: **0 tests executed**. Required engine default/narrow and resource-disposal cases: **0 tests executed**. Required regressions: **not run**.
- Core+SYNC runtime validation, actual layer mapping/enablement, GPU disposal, native owner receipts, pixel/quantization/guardband checks and raw readbacks: **not reached**. No zero-VUID or API-validity claim is made.
- Optimized archive publication and QEMU link/version stages: **not run**. New optimized artifacts: **none**. The owned artifacts directory was absent at final inspection.

## Preservation and resources

All **10 admitted artifacts**, the **1261 baseline source entries**, all **618 selected compiler files**, and the pinned Rust tool binaries were independently rehashed and matched before/after. Full paths/hashes/sizes are in `protected-before.json` and `protected-after.json`.

The compile ran 57.239s with actual cgroup peak **3562119168 bytes**; max/oom/oom_kill/oom_group_kill events were **0**. Builder envelope: 4 CPU, 6 GiB memory, equal memory+swap, 256 pids, network none, read-only root, 64 MiB tmpfs, core 0/filter 0x10. GPU containers were not started.

Final measured new allocation: **150363 bytes** against the 2 GiB budget. Owned evidence stayed below 64 MiB. Build guard minimum host free: **57048891392 bytes**, above 10 GiB; 0.2s polling remained active. All three owned containers were reaped and removed, with no remaining owned IDs.

Validation bundle/settings files were host-hash checked on each host check. All six runtime driver pins were verified by final host read. No validation package was downloaded or installed. Actual engine Core+SYNC enablement remains unqualified because compilation failed. Authentication scope remains official HTTPS plus exact package hash; no signed-metadata claim.

## Harness evidence

The initial read-only measure imported guard scalar counters into a separate namespace; actual guards and outer watchdog ran, but its summary scalar counters were not authoritative. The namespace was corrected before build; original files and the cause note remain. Prospective test actions were drafted during compilation without changing source inputs. `run-build-loaded-reconstruction.py` records the loaded build runner; compiler JSON diagnostics are canonical.

Final preservation completed its source/compiler/artifact and allocation checks, then its directory enumeration raised `FileNotFoundError` because the owned artifacts directory did not exist. No retry or source correction followed. Its failure and owned cleanup receipts are preserved.

No VM, guest input, profile migration, QEMU upgrade, dependency update, backend/guard/service cleanup, lease extension or sampler restart occurred. Guest acceptance, desktop rendering and interaction remain unverified. The installed codebase-memory skill was read; graph/index coverage tools were unavailable, so exact named source reads were used without a graph claim.
