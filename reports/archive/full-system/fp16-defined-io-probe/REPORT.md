The separate defined-value oracle passed offline translation, module validation,
structural census and native compilation. **Portable stage-I/O functionality is
unverified:** an active Android QEMU VM (PID 79064, `twofold_pixel`) triggered the
required no-active-VM gate. The `new` command exited during host preflight, before
any runtime container or Vulkan call. Mesa26 and Mesa25 GPU runs were both
withheld. The VM was untouched. There is no actual pixel readback or new device
feature query from this task.

The earlier strict fixture remains a failure. Its retained `numerical-readback-failure/new.log`
and `root-followup.json` report completed pipelines/submission/fence, then pixel 0
red `0x24ec` versus expected `0x0000`, native exit 10. All 67 predecessor files
were hashed before and after this preparation and match. No earlier fixture,
expectation, log or result was overwritten or weakened.

This fixture supplies the same exactly representable half4 seed `(1/4,1/2,3/4,1)`
at every vertex, so interpolation is constant. The fragment computes
`(x+y,y*z,x+x,w+0)=(3/4,3/8,1/2,1)`, with half bits
`[3a00,3600,3800,3c00]`; the second R16F attachment receives `3c00`.
`expected-math.json` verifies the arithmetic using exact rational numbers and
binary16 encoding. The 1340-byte `expected-readback.bin` contains offline expected
data only. A successful future execution must check every one of 364 RGBA16F
channels, 91 R16F pixels, 364 sampled RGBA8 channels (expected `[191,96,128,255]`,
tolerance one), and 66 sentinel padding bytes, then retain actual raw bytes.
These checks are compiled but have not executed on a device.

Both AIR fixtures were translated by the same frozen production CLI, without
SPIR-V edits. All four modules passed `spirv-val --target-env vulkan1.2`.
`structural-proof.json` resolves every Input/Output variable to scalar width 32,
with zero half stage variables and no StorageInputOutput16 capability. The
vertex has numeric 32->16 and 16->32 conversions; the fragment has numeric
32->16 input and two 16->32 output conversions. The fragment retains three
half OpFAdd instructions and one half OpFMul. Both sampling modules are
byte-identical to the preserved oracle. The C binary compiled using
`cc -std=c11 -O2 -Wall -Wextra -Werror ... -lvulkan`.

The frozen compiler manifest SHA-256 is
`2d5e7d483b966177882ccfa50d3a49a9c81c853dcf57c4992712452b4475da93`;
all 618 source files matched it before and after preparation. Upstream is
`9e0e99a41dc3cb8bb7e288b531f1698a79fd4b1c`. The 20,250,992-byte CLI SHA-256 is
`3f849ed0c7cd523cc1e521c602d789017d6ff8be5c71b7d1024ad30b55159200`.
The new native binary SHA-256 is
`533306b77e18433b85771aa218e4d2722e825ed3c926153f85f4959e51042141`.
All module/source pins appear in `admission.json` and `artifact-pins.json`.
Both runtime folders were rehashed; `runtime-pins-verified.json` records every
runtime file, including LVP, LLVM, ICD and auxiliary dependencies.

The actual builder image is
`sha256:14ea78615d69de5eea70014968be23464751916c6c44793f19f5771a9b4eeb17`.
The unexecuted GPU configuration selects actual guest runtime image
`sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`.
The builder used 2 CPUs, 2 GiB memory/equal swap, PID128, network none,
read-only root, 64 MiB tmpfs and core ulimit zero. Process-local coredump_filter
0x10 was set/read back and verified across exec. The runtime C repeats local
readback, but that check was not executed. The runtime configuration mounts the
selected runtime read-only at both `/soft` and `/out/runtime`, selects vector
width 128 and two threads, and disables the Mesa shader cache. The C code
requires robustBufferAccess=1, shaderFloat16=1 and actual storageInputOutput16=0;
it never enables storageInputOutput16. Actual features and optional RTE/RTZ16/32
properties were not queried in this task. shaderInt16 stays disabled.

`host-prepare-argv.json` and every `*-command.json` contain exact commands;
`host-prepare-receipt.json` records exit 0 in 5.748 seconds. The guarded container
stage took 5.292 seconds. Both supervisors enforce the unconditional 10 GiB
floor, sample freshness [-2,20] seconds, 0.2-second polling during child work,
300-second command bounds and the 1500-second overall deadline. Minimum observed
free space was 13,895,237,632 bytes. The single exact owned builder container was
removed and verified absent. No new sampler, service, watcher, download, storage
cleanup, CONTROL mount or guest disk read was used. The protected exporter and
sampler remained live with their original identities. Final evidence is in
`final-state.json`.

An additional host-only proof helper initially called the Linux-only O_NOFOLLOW
reader on Windows and stopped before producing proof. Only that new helper was
adapted to read its hash-pinned local files. The Linux runtime admission reader,
admitted native source/binary/modules and all predecessor files stayed unchanged.
The corrected additional proof check passed; it generated no actual pixel proof.

The optional integer bit-observable discriminator is **unknown and deferred**:
the active-VM gate prevents the prerequisite device feature/property query. No
integer diagnostic module, unsupported capability or rounding decoration was
invented. No input FConvert was decorated with FPRoundingMode; no optional
entrypoint rounding or fast-math mode was requested.

The default Vulkan floating-point environment permits rearrangements and a
different number of intermediate rounding steps. FConvert presence alone does
not establish strict AIR/LLVM intermediate quantization. Exactly representable
values avoid that ambiguity in this narrow fixture, while leaving strict
nonrepresentable rounding untested. This follows the
[Vulkan precision rules](https://docs.vulkan.org/spec/latest/appendices/spirvenv.html#spirvenv-precision-operation)
and [SPV_KHR_float_controls2 floating-point environment](https://github.khronos.org/SPIRV-Registry/extensions/KHR/SPV_KHR_float_controls2.html#_fp_fast_math_mode).
No particular Mesa optimization pass has been established as the earlier cause.

Strict AIR precision, the actual captured Golden LLVM abort, the macOS 27
desktop and GUI remain unverified. No QEMU build, emulator source change,
VM launch, VM action, service action, production cache mutation or next task was
performed. Root AGENTS.md was absent on disk; the supplied root instructions and
`reims-study/AGENTS.md` were followed. Direct file inspection was used; no graph,
index or coverage claim is made. Parent review is required before any emulator work.
