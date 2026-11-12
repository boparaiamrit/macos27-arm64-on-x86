# Offline direct QMP PNG qualification

This directory is a standalone review artifact. Nothing is integrated into an
existing runner. `REPORT.md` gives the observed result and `handoff.json` pins the
artifacts. The final successful run is
`runs/macos-frame-qual-qualify-3bba1c1c7115/`.

## Future parent integration contract

Import only `capture_once.py` after separate parent review and admission. The
module does not open sockets, discover processes, launch QEMU, pause/continue a
VM, access guest files, issue HMP/GDB, or clean up processes/files. Its only QMP
operation is one `screendump` with explicit PNG format, filename, and a unique id.
The harness's `cont`, HMP reads, and process termination are synthetic-test setup
and teardown; they are outside the helper and capture window.

The caller supplies these explicit inputs:

* An **existing exclusively leased owned QMP client** implementing
  `send(request, absolute_monotonic_deadline)` and
  `receive(absolute_monotonic_deadline)`. The transport must bound send and receive,
  preserve partial-line framing across timeouts, and return decoded JSON objects.
  `receive` raises `TimeoutError` when its slice expires. The tested socket
  adapter is in `qualify.py`; it is deliberately not a production connection
  manager. No competing polling task may consume responses during the lease.
* An existing, trusted, absolute, caller-owned POSIX output directory, visible
  at the **same pathname** to the helper and QEMU. All its ancestors must be real
  directories. `attempt` must be a fresh simple basename. The helper exclusively
  creates that attempt directory and reserves `frame.png` with O_EXCL/O_NOFOLLOW.
  It rejects preexisting attempts, traversal, symlink ancestors and changed
  destination/directory identity; it does not remove any rejected or partial
  artifact. Parent must keep this namespace free of other writers. Path-based
  QMP cannot atomically bind QEMU's later open to the helper's inode: these checks
  detect tested replacements, but are **not confinement against an adversary
  racing pathname replacement**. Do not admit an untrusted shared directory.
* A bounded `guard()` callback. The caller retains its existing independent host
  monitor throughout capture and late-write quarantine, enforcing the actual C:
  reserve >=10 GiB, sample age <=20 seconds, <=2 seconds future, and <=0.2 seconds
  between checks. The helper checks the callback around setup, receive slices
  (<=0.05 seconds), and validation. It does not replace the external monitor.
* A receipt publisher reserved **before** any QMP work. `ReceiptPublisher` seeds
  valid `success:false,state:incomplete` JSON at an exclusively created path, then
  writes a bounded temporary file, fsyncs it, and atomically replaces its own
  reserved receipt once. Allocate the receipt outside the attempt directory so a
  rejected output path still has a receipt. Failures and timeouts are published
  as structured JSON. A publisher/storage failure can leave the valid incomplete
  sentinel; it cannot guarantee durable completion through disk failure or
  process death. Such a receipt is always failure. The parent must surface any
  publisher exception. Never parse an empty temporary file as a receipt.

Example (the client and guard below must already be owned by the parent):

```python
publisher = ReceiptPublisher(owned_receipts_directory, "one-frame")
receipt = capture_once(
    owned_qmp_client,
    owned_root=owned_capture_directory,
    attempt="one-frame",
    publish_receipt=publisher,
    guard=existing_guard,
    timeout_seconds=4,
    max_bytes=8 * 1024**2,
)
```

Success requires the exact request id with `return:{}` and no error, followed by
size, regular-file/inode/link identity, signature, IHDR/dimensions/encoding,
chunk lengths/CRCs, final IEND, bounded deflate and scanline validation. Supported
encoding is noninterlaced 8-bit RGB/RGBA, dimensions 1..8192, <=8 MiB on disk and
<=64 MiB decoded. This is PNG integrity validation, not frame freshness or proof
that a surface came from a guest compositor. STOP/SHUTDOWN received during the
operation is failure; other bounded events are retained. Post-capture CPU status
verification remains the caller's responsibility. No automatic retries or
periodic capture scheduling exist.

## Deadlines, late activity, and physical budgets

A timeout is not QMP cancellation. A sent or partially sent command can finish
later, produce a matching late response, truncate/write the reserved file, or
leave a partial PNG. An id mismatch also taints the lease. The receipt sets
`owner_must_quarantine_lease` when command completion is uncertain. Retain the
attempt, request id and receipt; the existing connection owner must reconcile
the outstanding command and late writes under its own guard/deadline policy.
Do not reissue the capture, reuse the filename, delete a possibly active output,
open a second monitor, or kill a process whose ownership is ambiguous. This
helper intentionally performs no automatic drain or cancellation architecture.

Deadline checks are cooperative, relying on the bounded client/guard/publisher.
Filesystem syscalls, PNG validation, host scheduling, or a client violating its
contract can exceed the nominal deadline. A post-validation deadline failure
still means failure. Counter progress before/after and no STOP event do not
establish zero scheduling delay or continuous instruction progress.

The 8 MiB postcheck rejects oversized files; it does **not prevent QEMU from
writing too much first**, nor prevent late writes after timeout. The synthetic
containers additionally use RLIMIT_FSIZE=8 MiB per file and a 60 MiB aggregate
stop threshold under a <=64 MiB output budget. RLIMIT_FSIZE can terminate the
writer; it is only a test-container control and must not be blindly imposed on a
real parent VM with other outputs. Aggregate polling is not a filesystem quota;
a writer can overshoot between polls, and logical sizes differ from allocation.
Future admission needs an appropriate parent-owned physical output budget and
late-write policy. No claim is made that postchecks alone enforce physical
limits. The observed offline outputs are well below 64 MiB.

## Reproduction and evidence

From `<WORKSPACE>/macos` with the existing pinned image, build volume,
software libraries, and fresh host sampler already available:

```powershell
python test-output\arm-macos\full-system\qmp-frame-qualification\launch.py probe
python test-output\arm-macos\full-system\qmp-frame-qualification\launch.py qualify
```

Each launch creates a new unique `macos-frame-qual-*` container and run directory;
there are no capture retries within a run and no reused destinations. The exact
Docker argument arrays, environment/mount pins and QEMU argv arrays used for the
frozen result are in the selected run's `host.json`, `apple-paused-command.json`,
and `virt-running-command.json`. The launcher never pulls an image, lists other
containers, or uses network ports. It reads only `host-space-live.json` in the
read-only guard mount. It measures actual Windows C: free space independently.
Only exact unique owned container names may be inspected/removed. All original
failed attempts remain for review. Rerunning adds evidence and is separate from
the frozen handoff; verify its manifest first.

No macOS input, boot, WindowServer, rendered guest frame, Finder/Dock interaction,
real NBD/proxy delay, or cold-I/O latency is qualified here. Do not integrate this
helper into the concurrent real boot from this artifact alone.
