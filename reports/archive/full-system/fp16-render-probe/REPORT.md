The synthetic FP16 graphics oracle **passed on both pinned software-driver stacks** at 128-bit vector width. The old driver also passes, so this fixture does **not** reproduce the guest's `fs_variant_partial` abort and does not prove the newer driver fixes it.

Actual configurations:

- Old: Mesa `25.2.8-0ubuntu0.24.04.4`, LLVM `20.1.2`, reported `llvmpipe (LLVM 20.1.2, 128 bits)`.
- New: Mesa `26.2.5 - kisak-mesa PPA`, LLVM `21.1.8`, reported `llvmpipe (LLVM 21.1.8, 128 bits)`.

Both devices advertised and enabled `robustBufferAccess` and `shaderFloat16`. Required RGBA16F/R16F color-attachment blending, sampling and transfer features were checked before allocation. No feature was disabled or fabricated.

The same executable and validated shaders ran on both stacks. The first pass draws a full-screen triangle into **13×7 RGBA16F and R16F MRT attachments**, using explicit half arithmetic including half **1.0** and alpha blending. A runtime push constant supplies zero, which is converted to half and added to the half constant; the SPIR-V retains `Float16`, `OpTypeFloat 16` and half `OpFAdd`. It produces `(1.0, 0.5, 0.25, 1.0)` in RGBA16F and `1.0` in R16F. The odd extent exercises partial rasterization tiles without requiring a display or guest memory.

The second pass samples the RGBA16F texture with a nearest sampler and writes an RGBA8_UNORM target. After explicit layout/access transitions, image-to-buffer copies, a host-read barrier and successful fence completion, every pixel is checked:

- **364 RGBA16F channels** exactly equal binary16 words `3c00,3800,3400,3c00`.
- **91 R16F pixels** exactly equal `3c00`.
- **364 sampled RGBA8 channels** equal `255,128,64,255`, allowing one unit for UNORM rounding.
- **66 padding bytes** retain their sentinel.

The R16F shader output explicitly defines all components including alpha, even though the attachment stores only red, so blending never relies on an unwritten source-alpha value. Both MRT blend states are identical; the fixture does not require independent-blend support. Shaders compile with the installed `glslc`, and all three pass `spirv-val --target-env vulkan1.2`. No validation-layer library was installed; the fixture is a narrow functional oracle, not a complete Vulkan conformance run.

Final probe executable SHA-256:
`72221c6432fd9ad0976e0f06f7a9b3b7f604b21654f5ae333499f40267e50e29`.
Final C source SHA-256:
`11fd20689061ddfbde596422b8b461fa408f97fff372b2e1d7cc241f55166608`.
Exact shader source/SPIR-V hashes are in `shader-provenance.json`.

Native runtime hashes, observed after execution and matching the supplied pins:

- Old LVP: `5a218118760fee2398cc783820a1cc052de162d8c937dafcd6045576dfd9576c`.
- Old LLVM: `4b93481bd1c9d42c0951275dd275d4a9d30db78c309ae2cc0405669bc6dbbf8a`.
- New LVP: `9a805a2e19312658ed9715d6bc2892770d7d160d0222b74f0b69aa72d07d3007`.
- New LLVM: `f804d4247625bf0905c55655377618783ff3296a9c8aacdda9ac7cafa2e5e404`.

Commands used one compile container and fresh process/container/tmp for each final old/new execution. Limits: 2 CPUs, 2 GiB memory/equal swap, PID 128, no network, read-only root, 64 MiB tmpfs, 300-second command deadline, 2 MiB log bound and owned-process cleanup. A guard checked the shared sample every 0.2 seconds, required at least 10 GiB free and sample age within `[-2,20]` seconds. The minimum final command sample was **14,912,794,624 bytes**, above the floor. Execution took about one second per stack; those timings are observations, not a performance benchmark.

The supervisor sets/readbacks process-local `coredump_filter=0x10`, proves inheritance through an exec child, and the native binary sets/readbacks it again before loading Vulkan. No global core/WSL settings changed. No owned crash cores were produced. All owned containers ended and were removed. Production sources, admitted artifacts, launchers, existing runtimes, guest volumes, exporter and sampler were untouched.

The first provisional fixture passed too; a final correctness review explicitly defined the scalar attachment's unused alpha components and added blend-feature checks. Both stacks were then rerun once using the final identical executable and shaders. No failed-driver outcome was hidden.

This establishes a synthetic FP16 arithmetic/MRT/blend/sample/readback witness for the candidate runtime. Guest shader/state, Reims pass lifetime, native failure resolution, hardware acceleration, GUI and desktop operation remain unverified by this probe. See `handoff.json`, `old.log`, `new.log` and per-stage result files for compact machine-readable evidence.

Compilation/shader tools ran in builder image sha256:14ea78615d69de5eea70014968be23464751916c6c44793f19f5771a9b4eeb17. Both final old/new render executions ran in the actual guest runtime image sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635, with the selected runtime directory mounted read-only at /soft and /out/runtime. They were not executed in the builder image.
