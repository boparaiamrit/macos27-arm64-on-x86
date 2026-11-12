Isolated software-Vulkan runtime candidate, 28 October 2026.

Mesa 26.2.5~kisak1~n with LLVM 21.1.8-6ubuntu1~kisak1~n is staged only in
this directory. The original Mesa 25.2.8 / LLVM 20.1.2 runtime is preserved.
No Windows driver, Docker base image or installed system package was changed.

The existing Mesa archive matched its recorded SHA-256
833b3e0d20361611055832033ed80dfd65b4925b3dd152f2263e6bbef798ee78.
The missing LLVM package was downloaded from the Kisak Launchpad repository,
size 30,991,142 bytes, SHA-256
4e5a777922367add6142183742807ea1fc19f216f914181f3a8368a3723b48a5,
as published in its HTTPS package index. Dependencies resolve in the actual
pinned guest runtime image 13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635.
Runtime files were extracted from checked archives and copied as real files;
the launcher validates every size/hash against the admitted manifest.

Manifest SHA-256: 5711c1e0cc73a67cd8643f1d84591651a75f0de2ad27315f0c7709035ba63a0e.
Driver SHA-256: 9a805a2e19312658ed9715d6bc2892770d7d160d0222b74f0b69aa72d07d3007.
LLVM SHA-256: f804d4247625bf0905c55655377618783ff3296a9c8aacdda9ac7cafa2e5e404.

Actual half-precision graphics qualification passed in image 13d68...:
13x7 mixed RGBA16F/R16F render targets, half arithmetic and blending, followed
by texture sampling into RGBA8 and fence-complete readback. Robustness and
shaderFloat16 stayed enabled. It verified 364 RGBA16F channels, 91 R16F pixels,
364 sampled channels and 66 sentinel padding bytes. See
../../../full-system/fp16-render-probe/REPORT.md and handoff.json.

The old driver passed the same synthetic test. No exact reproduction or
verified upstream fix for the guest failure is claimed. The latest guest's
half-constant SelectionDAG error in fs_variant_partial is consistent with a
conversion/lowering problem, but does not identify the guest shader or prove
invalid SPIR-V. Related release-note entries are leads only; branch numbers
do not establish backport state.

There is no current Reims/metal2vulkan type-preserving half-widening switch.
The native emitter produces OpTypeFloat16, so disabling only the advertised
feature would leave those instructions unchanged. This experiment therefore
uses a real newer driver stack rather than falsely clearing its feature bit.

Fresh CheckOnly 20261028T170948Z-6aq20f6z passed. One live candidate run will
keep QEMU f603fd8b6066b96a38bfbb20ad74c9c322643c0b120f8662ed079be99ddd648a,
transfer copies, 128-bit software vectors, guest inputs and resource bounds,
changing only the software runtime selection:

    & ./test-output/arm-macos/full-system/local-raw/Launch-LocalRawAttempt.ps1 -QemuProfile m27-pages-mem-safe -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800

Existing storage/core guards remain active. GUI and interaction remain
unverified before the live test.
