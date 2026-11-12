# P1 cancellation follow-up verification

Final command: `./Build-Test.ps1` in the owned streamed-disk directory.
Result: **29 tests passed, zero failures/errors/skips**, in 16.186 seconds.
All original 18 tests remain; 11 new checks are in `test_cancellation.py`.
Tests ran with Docker `--network none`, read-only source/root, bounded RAM,
and tmpfs fixture metadata. No real Golden payload, live NBD service, VM,
APFS extraction, or GUI was run by this worker.

The genuine slow-drip and hung-header tests demonstrate cancellation before
the fixture's five-second idle timeout. Separate tests cover initialization's
total deadline, low/stale host samples during initialization, deadline/guard
cancellation during a real cold NBD read, signal cleanup, refusal of a bare
plugin, and refusal to relax limits. The NBD client receives an error without
successful partial bytes. A TERM-ignoring child and grandchild require KILL;
their process group and descendant /proc entry disappear, while an unrelated
process survives. Nine measured cancellation records have a maximum stop time
of **1.392 seconds**, each asserted below three seconds.

The image was rebuilt as `macos-streamed-guest:local`, ID
`sha256:8ef6a1114d247bdab49f08ff87f77dc804733826c42a5db21dee8b4e8f51b2fb`.
All nine packaged Python files match host SHA256 hashes, checked without a code
bind mount. Evidence: `packaged-files.json`, `implementation-hashes.json`,
`image-inspect.json`, `test-results.json`, `offline-tests.log`, and
`offline-cancellation-telemetry.jsonl`. Full final hashes are in `handoff.json`.

Source review: mapping, integrity verification, 32 MiB RAW bound, serialization,
one/two-layer RAM cache, 10 GiB floor, and 20-second freshness threshold remain.
`nbd_source.py` and `frozen.py` retain the supplied reviewed hashes. All three
frozen converter files retain their pinned hashes. Only the owned streamed-disk
directory and owned image were modified; parent sampler and APFS reader were
untouched. No delegation occurred.

The supported entrypoint is now necessarily `serve.py`; the plugin validates an
inherited supervisor socket/parent before initialization. The supervisor polls
the guard every 50 ms, enforces 900 seconds per layer beginning before HTTP open,
and adds a strict 900-second overall initialization deadline. Smaller limits are
accepted; larger/nonfinite limits are refused. Cancellation sends group TERM,
then KILL after at most five seconds, plus at most two seconds for reap checks.
No watchdog thread is created inside nbdkit. Cancellation emits terminal JSON
on stderr and returns nonzero. See `../README.md` for lifecycle/launch details.

Implementation/offline verification is complete. Independent parent re-review
remains required before resuming any live NBD work; this worker did not restart
the parent-owned server.
