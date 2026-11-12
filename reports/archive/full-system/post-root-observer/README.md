# Bounded read-only post-root observer

This utility observes one already-running Golden guest after its installed
System root mounts. It does not start a guest. No real guest has been observed
with this utility yet; validation below uses fake GDB and temporary host files.

Only use it when the original handoff GDB process has **actually exited 0** and
QEMU still runs. Pass that observed result as `POST_ROOT_HANDOFF_RC=0`. The
utility additionally verifies the same attempt's `handoff.json` Golden/r3
readback flags and `serial.log` root-hash, read-only System root and Macintosh HD
mount-completion markers. These markers authorize observation; they do not
prove Data mounting or userspace.

Inside the same owned VM container, with existing `/parent` source/attempt
mounts, run:

```text
POST_ROOT_HANDOFF_RC=0
POST_ROOT_RESULT=/parent/full-system/attempts/<attempt>/post-root-one.json
gdb-multiarch -nx -q -batch -x /parent/full-system/post-root-observer/observe.gdb
```

Set the two variables in the child process environment, not merely as unrelated
shell assignments. `<attempt>` must be the existing single attempt directory.
The result must be a **new** `post-root-<suffix>.json` directly within it; the
utility refuses replacement, symlink ancestors/output/evidence, hard-linked
evidence, nonregular evidence, and evidence outside size limits. Source imports
come from the fixed `/parent/full-system/post-root-observer` path. Set
`PYTHONDONTWRITEBYTECODE=1` to avoid import-cache writes.

The parent must impose an external **20-second deadline on the GDB process
inside the container**, kill/reap that owned process on expiry, and keep the
normal VM/storage/log guards active. A timeout on the Windows `docker exec`
client alone does not reliably terminate its in-container process. One pattern
is for an existing parent-owned Python helper inside the VM container to use:

```python
subprocess.run([
    'gdb-multiarch', '-nx', '-q', '-batch', '-x',
    '/parent/full-system/post-root-observer/observe.gdb',
], env=observer_environment, timeout=20, check=False)
```

`subprocess.run` kills and reaps its direct child on `TimeoutExpired`. Bound the
outer Docker-exec helper as well, allowing this cleanup to finish. Do not retry
the observer if its detach fails or it times out; let the owning bounded runner
stop its VM. No port is published: the only debugger target is
`127.0.0.1:1234` **inside that container**.

The script selects AArch64, disables pagination and TCP retries, sets remote and
connect timeouts to three seconds, attaches, and uses a twelve-second internal
capture budget. Remote calls are individually bounded by GDB's timeout; the
external process deadline remains mandatory. It always attempts `detach` in a
`finally` block after any attach attempt, including partial attach failure.
QEMU's remote detach resumes execution. A failed detach is reported explicitly;
successful resumption cannot be promised after an unresponsive remote or an
external forced termination.

The private JSON contains general registers (`pc`, `sp`, `fp`, `x0` through
`x30`, `cpsr`), sixteen AArch64 instructions around PC, at most sixteen frame
records, and optional 256-byte PC/SP regions with Base64 and SHA-256. Reads are
restricted to `[0xfffffe0000000000, 0xffffffffffffffff]`, including the whole
requested region. Frame cycles stop traversal. PAC-signed values are recorded
verbatim; no pointer stripping, address guessing or fallback writes are used.
Unsupported registers, disassembly and memory are recorded as bounded errors.
All guest operations are reads; there are no breakpoints, steps, guest input,
register writes or memory writes. Attaching temporarily stops the CPU.

The result is created exclusively with mode `0600` and cannot exceed 64 KiB.
Only status, path, SHA-256 and byte count are printed; keep the JSON private
because register, stack and code bytes can contain guest data. With no symbols,
this is an execution-location snapshot, not a reliable kernel backtrace, thread
inventory, wait-cause diagnosis or proof of userspace/graphics.

Validation: `python3 -B -m unittest -v test_observer` passed **23/23** tests in
the pinned existing runtime, with network disabled, read-only source/root,
one CPU, 512 MiB memory/equal swap and a 16 MiB temporary filesystem. Tests cover
the exact GDB command allowlist, eligibility and path refusal, cleanup after
attach/memory/disassembly failures, failed detach reporting, canonical read
bounds, frame cycles and limits, PAC refusal, time budgeting, output caps,
exclusive creation and privacy of printed output. No real guest, new backend,
existing runner/profile/identity, build artifact or guard was changed.
