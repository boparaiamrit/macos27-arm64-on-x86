Bounded final-shader capture, 28 October 2026.

QEMU `/work/orchard-m27-pages-capture/artifacts/qemu-system-aarch64`
SHA-256 `689d926f89da98fb6886919e54d8983c80b35b0666051634623e875d5e6297de`.
Archive SHA-256
`cbd1ec25328127d42e45521f5ca0f17d90b8f5ab3df27babf000ff5c9bc4e385`.
Predecessor source files and artifacts remain unchanged.

This is observation only, default off. REIMS_VGPU_FINAL_SHADER_CAPTURE=on
retains complete post-edit shader words after the final validation gate, keyed
by the cache's actual digest, with linked immutable pipeline creation state.
Files survive creation-call return. Normal DriverBreadcrumb disarm/quarantine
behavior and driver-operation results are unchanged. Metadata explicitly omits
dynamic draw, sampler and resource state, so it is not a complete reproducer.

Producer bounds: 32 modules, 256 KiB/module, 4 MiB module bytes; 64 pipeline
records, 16 KiB/record, 128 KiB aggregate metadata. Atomic publication refuses
foreign evidence/symlinked directories and reports caps or I/O failures without
changing guest work. No captured bytes were included in source or commits.

The launcher provides a dedicated 8 MiB tmpfs. Wrapper extraction binds to the
exact runner attempt supplied to FrameQMP, including constructor failure, and
runs before container removal after normal/failing exit. No newest-directory
guessing or extra QMP client is used. Extraction verifies source identity,
exact reads, exclusive destinations, fsync and SHA-256 readback. Limits are
128 files, 512 KiB/file and 8 MiB allocated retention including reserved small
receipts. Individual files are stable; the set is not a cross-file atomic
snapshot. Filesystem syscall deadlines are checked between operations.

Validation: formatting passed; 10 capture-owner, 44 cache, 8 breadcrumb and
15 config tests passed (77 Rust tests). Runner integration passed 22 new owner
tests and a 34-test frame/core combination. Parent admission reran 28 relevant
profile/extraction/core tests successfully. The offline stage-I/O census passed
15 tests with real spirv-as/val/dis. Only existing atomic deprecation warnings
remain. These are diagnostic tests, not desktop/conformance proof.

Hypothesis to test: both actual software stacks report storageInputOutput16=0,
shaderFloat16=1. The translator can preserve half stage interfaces while Reims
only enables storage-buffer16 access. This is a conditional feature gap; the
latest faulting module has not yet been captured. Inspect Input/Output pointee
types and capabilities; half arithmetic/private/SSBO values alone are not I/O.
The helper in full-system/shader-inspection/ distinguishes these cases and keeps
unknown type graphs explicit. Do not force an unsupported device feature.

CONTROL migration changed only qemu_sha256, with backup/readback. AUX remained
1449d71414e79058f9d55c2c031f8d1022d0edb64e15117de6ab76096d815661;
overlay remained 8eb60261093503978c698e4253c156a3b4c859f23fd68fa0dc75937c71694f67.
CheckOnly 20261028T180039Z-_lg4vrjr passed without a guest; capture correctly
reported not_started_check_only. The build minimum free space was
12,197,298,176 bytes and the unconditional 10 GiB floor was retained.

One diagnostic command after fresh CheckOnly:

    & ./test-output/arm-macos/full-system/local-raw/Launch-LocalRawAttempt.ps1 -QemuProfile m27-pages-capture -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800

After return, inspect the exact attempt's shader-capture-status.json and
shader-capture/ files, then run the offline census on that exact directory.
A driver failure is possible and not a capture success; only complete retained
bytes plus explicit scope establish evidence. GUI remains unverified.
