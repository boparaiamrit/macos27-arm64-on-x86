128-bit software-vector experiment, 28 October 2026.

The pinned Mesa 25.2.8 / LLVM 20.1.2 driver accepted
LP_NATIVE_VECTOR_WIDTH=128 and reported
`llvmpipe (LLVM 20.1.2, 128 bits)`. The exact embedded scatter shader compiled
and executed with robustBufferAccess enabled. All 2,048 destination words
were checked: 777 copied words matched and 1,271 gaps retained their sentinel.
See compute-robust-128.log/result.json. This does not reproduce or resolve the
broader QEMU compiler failure by itself.

Mesa documents this vector-width control in its
[LLVMpipe environment variables](https://docs.mesa3d.org/drivers/llvmpipe.html#environment-variables).
The launcher admits only its default (0) or the qualified narrower value 128.
It records the choice and passes the environment variable to the existing
software-Vulkan container. No emulator, driver library, guest capability,
robustness setting, guest disk reset or identity-pin change is required.

Fresh CheckOnly 20261028T163519Z-_olcu3et passed. The next actual run uses
the same f603fd8b6066b96a38bfbb20ad74c9c322643c0b120f8662ed079be99ddd648a
emulator and transfer-copy configuration as the preceding failed run, adding
only the qualified software-vector setting. Natural working disk changes
prevent treating duration differences as a controlled performance benchmark.

    & ./test-output/arm-macos/full-system/local-raw/Launch-LocalRawAttempt.ps1 -QemuProfile m27-pages-mem-safe -TransferCopies -LavapipeVectorBits 128 -ReadyName stream-ready-local-raw-cleanup-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800

Run once after fresh CheckOnly; retain the existing 10 GiB floor, core-memory
exclusion, input pins, owned QMP frame capture and cleanup. Actual graphical
login/desktop and interaction remain unverified before this run.
