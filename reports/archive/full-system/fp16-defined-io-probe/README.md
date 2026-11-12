This directory owns a separate, exactly representable stage-I/O functional fixture.
It does not replace or weaken `../fp16-io-render-probe/` or its retained strict
numerical readback failure. No product source or SPIR-V binary is repaired here.

`production/io_vertex.ll` and `production/half.ll` are authored textual AIR.
They pass through the frozen production `translate_sanitized_native` CLI. The
first vertex shader narrows the runtime seed to half4 and returns a half4
varying. The fragment consumes that half4 and returns two half4 color targets.
Production emission provides float32 stage transport and numeric conversions.
The sampling shaders and two-pass Vulkan framework come from the earlier oracle.

Every vertex seed is (1/4, 1/2, 3/4, 1). Interpolation is constant. The fragment
computes red=x+y=3/4, green=y*z=3/8, blue=x+x=1/2, alpha=w+0=1. All operands and
results are finite, normal, exactly representable binary16 values. Half math
is explicitly present in the admitted SPIR-V. This fixture intentionally cannot
distinguish removal of nonrepresentable intermediate half rounding.

The preserved 13x7 framework renders RGBA16F and R16F, then samples RGBA16F into
RGBA8. Fence completion precedes CPU reads. A successful native run checks 364
exact half channels, 91 exact R16F values, 364 sampled channels (UNORM tolerance
one), and 66 sentinel padding bytes. It writes the complete 1340-byte actual
readback into an exclusive, stack-specific file; Python independently checks it.
`expected-readback.bin` is offline expected data and is never actual GPU evidence.

Executed from the project root:

    python -B test-output/arm-macos/full-system/fp16-defined-io-probe/control.py prepare
    python -B test-output/arm-macos/full-system/fp16-defined-io-probe/control.py new
    python -B test-output/arm-macos/full-system/fp16-defined-io-probe/verify_offline.py

Preparation passed. `new` stopped in host preflight on the active Android QEMU
VM, before creating any runtime container. `old` was not requested after that
blocker. Neither stack executed this fixture. See REPORT.md and handoff.json.

The host supervisor uses the original absolute task deadline (19:23:40Z on
2026-10-28), a 300-second command bound, the unconditional 10 GiB host reserve,
fresh sample age [-2,20] seconds, and 0.2-second checks while a child runs.
Artifacts are limited to 64 MiB and each log to 2 MiB. Only the unique owned
container name can be removed. Container children have their own process group.
The builder mounts only this directory, the single read-only host sample file,
and the read-only frozen CLI. There are no CONTROL or guest disk mounts.

Runtime stages are implemented but unexecuted. They select the actual guest
runtime image, mount the selected runtime at both /soft and /out/runtime
read-only, use LP_NATIVE_VECTOR_WIDTH=128, LP_NUM_THREADS=2, disable Mesa shader
cache, and require actual robustBufferAccess=1, shaderFloat16=1 and
storageInputOutput16=0. shaderInt16 and optional float rounding properties are
queried for reporting only; this fixture enables neither shaderInt16 nor optional
rounding execution modes. Mesa25 requires a successful same-fixture Mesa26 result.

No active VM may be touched. The bit-observable integer diagnostic was deferred
because device features could not be queried under the active-VM gate. Its result
and strict AIR precision remain unknown. No emulator build or VM launch follows.
