# Verified cancellation defect

VERIFIED: true

`artifacts/reproduce-blocking.py`, run in the offline owned Docker image with
`--network none`, reproduced a real HTTP body sending one byte every 0.03 s.
The socket idle timeout was 0.15 s and CheckedStream's deadline 0.2 s. The read
remained blocked after 0.7 s, when the experiment killed and reaped its child.
Exact evidence: `artifacts/reproduced-blocking.log`.

`CheckedStream.read()` checks only before/after `raw.read(count)`. Continuous
progress can prevent the frozen request's idle timeout without returning from
that read. HTTP open/token/header waits likewise occur inside frozen calls.
`get_ready()` calls initialize before `after_fork()` starts the guard thread,
so initialization also lacks independent cancellation. Post-read checks protect
returned bytes but cannot bound cancellation latency.

Correction: supervise a foreground nbdkit process in its own process group from
outside nbdkit, including initialization. Monitor the Windows host sample and
absolute monotonic initialization/layer deadlines; TERM then bounded KILL/reap.
Use an inherited lifecycle socket without introducing pre-fork threads. Require
that channel for plugin startup. Preserve frozen source and all mapping/hash
semantics. New tests must use real stalled/slow-drip loopback HTTP and real NBD.
