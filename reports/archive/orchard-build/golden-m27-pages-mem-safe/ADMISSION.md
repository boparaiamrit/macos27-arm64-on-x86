Memoryless pass-lifetime correction and transfer-copy experiment, 28 October 2026.

QEMU `/work/orchard-m27-pages-mem-safe/artifacts/qemu-system-aarch64`
SHA-256 `f603fd8b6066b96a38bfbb20ad74c9c322643c0b120f8662ed079be99ddd648a`.
Static archive SHA-256
`16743f65688ea0a3ade428e0fc168819dddc25dcd3deb7a8a07f6f0dc91855dc`.
All admitted predecessor source files and binaries remain unchanged.

The latest prior guest abort (`20261028T145920Z-kke64w8i`) was a host LLVM
MCJIT failure while QEMU waited in scatter-pipeline creation for pixel writeback.
Bounded native evidence is in `../../full-system/llvm-crash/`. After extraction
and closed-handle verification, its completed 9,722,593,280-byte core was
reclaimed. The exact standalone scatter shader and the transfer-copy oracle
both pass on the pinned Lavapipe/LLVM runtime, also with robustBufferAccess.
The broader QEMU process trigger remains unresolved. The transfer-only guest
experiment avoids the identified optional copy-kernel path; it is not yet a
demonstrated cure for the production crash.

Changes address two separately audited defects: unsupported declared
memoryless load/store/resolve actions are now refused at the attachment owner;
temporary images use a unique pass identity and are discarded after completion.
Runtime requests and the attachment template retain one Arc across internal
draw splits. Engine identities contain only its ID, preventing a resident from
keeping its own pass alive. Parent source inspection traced the synchronous
cleanup to `retire_all`: it flushes the active batch, retires every submitted
slot/fence and drains cleanup before authorizing discard. Failed completion or
unexpected holders retain the images and report a refusal. Normal sole-copy
preservation is unchanged. Unsupported Metal execution remains refused.

Formatting and affected tests pass: 210 draw, 106 execution, 1 completion,
65 resident-retirement and 12 identity tests (394 total). One existing draw
test remains ignored. Three profile-admission and three process-core-filter
tests also pass. Initial compile/test integration issues were corrected: a
missing test constant qualification, an exhaustive diagnostic identity arm,
observation expectations for the newly earlier typed action refusal, and a
one-time rail-selection diagnostic in a fixture. The newly introduced private
interface warning was fixed. Only two pre-existing atomic deprecation warnings
remain; no warnings/tests were disabled to pass.

The native Windows/WSL crash fixture confirmed process-local core filtering:
after allocating/touching 64 MiB, a supervised SIGABRT produced a 53,248-byte
core. The launcher wrapper writes/readbacks coredump_filter=0x10 before child
execution; Linux preserves it across fork/exec. It excludes guest RAM while
retaining headers/notes and leaves global WSL/core policy unchanged. This is
mapping exclusion, not a universal exact byte quota. The first PID-1 fixture
terminated with SIGSEGV; the production-like --init fixture used SIGABRT.
[Linux core-dump contract](https://man7.org/linux/man-pages/man5/core.5.html).

The launcher now exposes `-TransferCopies`, which sets both existing switches
REIMS_VGPU_COMPUTE_SCATTER=off and REIMS_VGPU_COMPUTE_GATHER=off. Those select
existing transfer-region implementations. Neither driver capabilities nor guest
acceptance are widened. Each standalone copy oracle verified 777 copied words
and 1,271 unchanged gap words; see `../../full-system/llvm-scatter-probe/`.

Offline build used 4 CPUs, 4 GiB memory/equal swap, no network, a 64 MiB tmpfs,
bounded logs and the unconditional fresh-sample 10 GiB host floor. Final build
minimum was 15,470,432,256 free bytes. Only Cargo's disposable cache was shared;
a separate output was linked from preserved QEMU objects.

CONTROL migration changed only qemu_sha256, with backup, fsync and readback.
AUX remained `f2fd8aa95a1a34e605cba93b34454229ed153ea2c2f1e98f6793cad61547d8b5`;
overlay remained `b45b85345dfc3326f5726f060efb5dc83b36ded1d5fcbce5ac8f26f764f45221`.
No guest ran during build/admission. A real graphical desktop remains unverified.

Live command after fresh CheckOnly:

    & ./test-output/arm-macos/full-system/local-raw/Launch-LocalRawAttempt.ps1 -QemuProfile m27-pages-mem-safe -TransferCopies -ReadyName stream-ready-local-raw-cleanup-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800

Run once. Require actual retained-frame inspection, absence/presence of the
native abort, validated mapping plans and pass-retirement evidence. Do not
credit submission, process exit or a non-black fragment as a working desktop.
