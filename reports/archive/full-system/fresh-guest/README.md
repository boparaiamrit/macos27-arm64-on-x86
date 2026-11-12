These scripts prepare a **separate fresh-01 pair** while retaining the failed
working pair at `/control/boot` unchanged. Implementation and synthetic testing
do not establish base-filesystem health, successful preparation, or a VM boot.

`prepare-fresh.py` requires explicit `--execute`. Its production roots are fixed:
CONTROL at `/control`, host ARM evidence at `/parent`, and owned results at `/out`.
It creates `/control/fresh-01/boot` from the two trusted firmware files and the
unchanged preparation report in `/control/boot`, plus the original host
`full-system/inputs/aux.img` (33,562,780 bytes, SHA256
`2ca2b332f05e2d6e3663bb4db0982a5feec268a8d1b91460f140ad8d3cb49414`).
The old working AUX is not copied. Neither the old overlay nor runner identity
is copied; the existing core runner creates new ones during a real attempt.
CheckOnly creates neither.

The preparer locks the source boot directory, refuses symlinks/hard links,
checks bounds and provenance, hashes sources before/after, and verifies every
independent copy by readback. File/directory fsync precedes atomic publication
using Linux `renameat2(RENAME_NOREPLACE)`. Any preexisting destination, including
an empty directory or dangling symlink, refuses. A failure retains its uniquely
owned staging evidence rather than deleting or replacing another pair.
Data payload is bounded to 40 MiB; two small JSON receipts and filesystem
metadata are additional. No RAW, disk payload, or previous working-AUX read is
needed. Original firmware patch validity is still verified by the core runner's
normal preflight; this tool copies rather than patches firmware.

All preparation I/O checks the original 10 GiB host-space floor, sample freshness
[-2,20] seconds, and a 60-second deadline. The explicit CLI also installs a
process-local 60-second SIGALRM and core filter 0x10. The parent must supervise
the exact owned preparation container and guard while it runs; kernel-level
uninterruptible operations cannot be made preemptible by a Python signal.
No floor, freshness, source or identity check is bypassed.

`Launch-FreshIoAttempt.ps1` is a separate launcher. The admitted original
`local-raw/Launch-LocalRawAttempt.ps1` and core runner remain unchanged. The new
launcher has only the `m27-pages-io` profile, fixes the guest directory to
`/guest/fresh-01`, retains whole-CONTROL-volume exclusion, and passes that path
through the existing wrapper. It retains the original resource/driver/capture
guards and accepts the usual validated `ReadyName`, including a freshly issued
`stream-ready-local-raw-cleanup3-live5.json` after maintenance.

After parent review and **separately authorized real preparation**, the future
CheckOnly command is:

```powershell
& ./test-output/arm-macos/full-system/fresh-guest/Launch-FreshIoAttempt.ps1 -CheckOnly -QemuProfile m27-pages-io -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup3-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

No VM command is executed merely by preparing these files. A future actual boot
requires the parent's exact bounded instruction and passing CheckOnly.

Synthetic tests use small authored files under container `/tmp` only. They
exercise independent copies, preservation of an old failed pair, existing
destinations, symlinks/hard links, lock conflicts, bad pins, write budgets,
source/destination mutation, partial-copy retention, atomic publish races, and
guard refusal. `test-launcher.ps1` executes the real new launcher with a mock
Docker function and intercepted parent-metadata writer. It verifies the fresh
path, resource/mount arguments and whole-volume conflict refusal without a
Docker/VM call or a write to the parent's current-attempt metadata.
