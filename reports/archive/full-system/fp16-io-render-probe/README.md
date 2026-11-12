This is a focused, headless stage-I/O compatibility oracle. No GPU execution has
been performed as part of preparation.

The source-owned production compiler must translate `production/io_vertex.ll`
and `production/half.ll` using the pinned/modified metal2vulkan text API into
`legalized/io_vertex.spv` and `legalized/half.spv`. The public API is
`translate_sanitized_native(&str, Stage, &Path)`. No SPIR-V rewriting happens here.
The `prepare` stage compiles an unchanged GLSL sampling pair and puts those
two modules in the same directory. The separate `raw/` GLSL modules deliberately
retain unsupported half stage I/O as a negative census fixture; they are never
loaded into a Vulkan device.

The production first pass accepts two float4 vertex attributes, locations 0/1,
stride 32 bytes. Attribute 0 is position and attribute 1 is a seed. The vertex
shader numerically converts the seed to half4, and declares a half4 varying.
The fragment shader declares that varying and two half4 render-target outputs.
The owner fix should widen their transport types while preserving the half
conversions and arithmetic inside the shader. No push constants, SSBOs or
samplers are required by this first pass.

Readback after fence completion checks all 13x7 pixels and padding. It exercises
three independently visible properties:

- Runtime vertex-buffer value 1.0006 is rounded to half 1.0009765625. The
  fragment's green result must be exactly 0.25, which distinguishes removal
  of that half-rounding step.
- Half endpoint values 1.0/1.00390625 are interpolated. Converting each pixel's
  input back to half must yield red bands 0, 0.25, 0.5 across 3,7,3 columns.
  Twelve of thirteen columns differ if fragment input rounding is omitted;
  none lies on a rounding tie.
- Half addition/multiplication remains in the authored fragment; blue is 0.5,
  alpha is 1.0, and the R16F attachment receives 1.0.

An unchanged second GLSL pass samples the first RGBA16F attachment to RGBA8.
There are 364 exact half-channel comparisons, 91 exact R16F comparisons, 364
sampled UNORM channel comparisons (one-unit rounding tolerance), and 66 padding
sentinel checks. Both first-pass blend states are identical, avoiding an
independentBlend requirement. Image layout/access transitions, host-read barrier
and fence completion precede every CPU read.

The native probe requires actual `shaderFloat16=1`, `robustBufferAccess=1`, and
`storageInputOutput16=0`. It enables only the supported float16 arithmetic and
robustness bits. `admit` rejects any remaining 16-bit stage I/O, preserves the
unaffected sampling modules byte-for-byte, verifies retained half arithmetic,
validates all four modules with spirv-val, and compiles the exact binary. GPU
execution rechecks all module/source/binary pins and the selected LVP/LLVM hashes.

Commands, in order after the compiler worker has provided the two modules:

    & ./test-output/arm-macos/full-system/fp16-io-render-probe/Invoke-Probe.ps1 -Stage prepare
    & ./test-output/arm-macos/full-system/fp16-io-render-probe/Invoke-Probe.ps1 -Stage admit

GPU execution is intentionally a separate parent-coordinated action:

    & ./test-output/arm-macos/full-system/fp16-io-render-probe/Invoke-Probe.ps1 -Stage new -ExecuteGpu

`old` selects pinned Mesa25/LLVM20; `new` selects pinned Mesa26/LLVM21. Runtime
containers use the actual guest runtime image; compilation uses the pinned
existing builder. Limits are 2 CPUs, 2 GiB memory/equal swap, PID128, read-only
root, no network, 64 MiB tmpfs, 300-second child supervision and 2 MiB logs.
The 10 GiB sample floor and freshness [-2,20] seconds are checked every 0.2s
while children run. Process-local core filtering is set/read back as 0x10 and
verified across exec; the native probe repeats that check. Cleanup names only
the exact owned container.

Preparation validation: final prepare passed in 2.7784s; native C syntax passes
with -Wall -Wextra -Werror. Eight offline tests passed. They check raw
I/O graphs, retained half arithmetic, independent numerical witnesses, malformed
or unknown graph rejection, and rejection of unsupported raw I/O before driver
or compiler invocation. Minimum final preparation sample: 11,129,958,400 bytes.
No GPU, VM, guest volumes, services or existing sources/artifacts were changed.
This fixture is a narrow functional witness, not complete Vulkan conformance or
desktop proof.
