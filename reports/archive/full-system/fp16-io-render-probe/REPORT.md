Admission passed; the first actual Mesa26 invocation failed before Vulkan device
or shader creation. No rendering result or pixel comparison was reached.

Commands were issued exactly once in order:

    Invoke-Probe.ps1 -Stage admit
    Invoke-Probe.ps1 -Stage new -ExecuteGpu

Admission took 2.1783 seconds, validated all four modules, found no 16-bit stage
I/O, verified the sampling pair unchanged, retained one half OpFAdd and one half
OpFMul in the production fragment, and compiled the binary. Its SHA-256 is
`9a1f447290fe1e877dfc36e680b7b231cb31a1b107d5d3efa272f64452e0ae18`.
The production compiler pin manifest matched the root's frozen SHA-256
`2d5e7d483b966177882ccfa50d3a49a9c81c853dcf57c4992712452b4475da93`.

The actual invocation completed process-local core-filter readback as 0x10, then
`vkCreateInstance` returned -9 (`VK_ERROR_INCOMPATIBLE_DRIVER`). Native exit was
2; the Python harness/PowerShell launcher returned failure. `new.log` and
`last-error.json` preserve this result. The host-space guard's minimum reported
sample was 13,977,784,320 bytes, above the unconditional 10 GiB floor.

The owned harness has a concrete mount-path defect: both pinned ICD manifests
name `/out/runtime/lib/libvulkan_lvp.so`, but Invoke-Probe.ps1 mounted the runtime
only at `/soft`. The original sibling oracle mounted the same runtime at both
paths. No runtime, ICD, shader or compiler change is needed to correct this
binding. The parent has been informed; no correction or retry was performed
under the task's single-run/no-speculative-edits instruction.

The old Mesa25 stack was not run because Mesa26 had not passed. No VM, guest
volume, exporter, sampler, unrelated container or existing source/artifact was
changed. All exact owned oracle containers are absent. GUI, host-driver feature
enumeration, GPU shader execution, pixel correctness and LLVM abort resolution
remain unverified by this invocation.

Root follow-up: corrected only the launcher by adding a read-only /out/runtime alias matching the pinned ICD. The first failure is preserved in before-runtime-mount-fix/. One corrected Mesa26 run created both graphics pipelines, submitted, and completed its fence. Its strict numerical check failed: pixel0 red half24ec, expected0000; native exit10. This result is preserved in numerical-readback-failure/ and root-followup.json. No Mesa25 run or VM followed. Explicit FConvert instructions and retained half arithmetic are structurally verified; default Vulkan floating-point contraction permissions mean strict intermediate rounding cannot be inferred solely from such instructions. The observed optimization has not been attributed to a specific Mesa pass. Neither a guest fix nor complete numerical equivalence is demonstrated.
