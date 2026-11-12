# Startup-budget regression verification

Final result: **29 passed, zero failures/errors/skips**, in 39.573 seconds.
Command: Build-Test.ps1 -SkipBuild, after a network-disabled Python refresh.
The original 18 checks and all 11 cancellation checks are preserved.

The parent failure log recorded 5 failed one-second HTTP-entry assertions in
17.966 seconds. The diagnostic rerun retained child logs and recorded 6 such
failures plus a two-second process-wait timeout, in 26.925 seconds. Direct probes
with generous test-only startup budgets reached the first real loopback request
in 1.520872, 1.506710, and 2.202710 seconds. The original one-second wait included
both the supervisor interpreter and the nbdkit Python plugin starting. The
0.6-second initialization test could expire during plugin imports, before HTTP.
This is a fixture startup timing defect; raising the production maximum from
900 to 3600 does not change the tests' explicit smaller deadlines.

Only test_cancellation.py and README.md changed among the top-level source
files. Production supervision.py retains the parent's 3600-second total startup
budget; serve.py, the external cancellation design, mapping, guards, and frozen
imports remain unchanged. Tests now allow five seconds for fixture startup,
report child logs if startup exits or times out, and use a five-second total
initialization test with a ten-second per-layer budget. Layer cancellation tests
retain 0.5 seconds; the TERM-ignoring process fixture retains 0.6 seconds.
Deadline elapsed time must match the configured limit within 50 ms early /
500 ms late tolerance. Cleanup remains below three seconds from deadline expiry
or the injected failure; the cold-read deadline test includes its 0.5-second
blocked HTTP wait. Nine records show a maximum of **0.716 seconds** by those
trigger-relative measures. Launch-to-stop durations are retained separately;
the initialization fixture intentionally lasts more than five seconds overall.
All owned process groups disappear, including the TERM-ignoring descendant;
the unrelated process survives. Active NBD clients receive errors without
successful partial bytes.

The final image is macos-streamed-guest:local:
sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635
All nine packaged Python files match source hashes without a source bind mount.
A separate import from the packaged image verifies the 3600-second startup cap,
900-second per-layer cap, 50 ms polling, fixed 10 GiB floor, 20-second sample age,
and unchanged hashes of all three frozen converter modules. Full final source
and frozen hashes are in handoff.json and implementation-hashes.json.

Tests used Docker --network none, a read-only root and source mounts, 512 MiB
memory, 128 PIDs, no capabilities, no-new-privileges, and a 64 MiB tmpfs.
Builds began above the 11 GiB C: threshold; captured final free space is
22773420032 bytes, above the 10 GiB floor. The standard Dockerfile was first tried
with networking disabled; its package-install layer missed cache and failed
without downloads. That log is docker-offline-full-build-failed.log. The
successful Dockerfile.offline-refresh reused the pinned existing local streamed
image and copied Python files only, with --network none and --pull=false.
No packages, live Golden fetch, live NBD service, VM, APFS extraction, large
downloads, cleanup, host changes, or delegation were performed. Parent sampler
and backend work were outside this worker's scope.

Evidence: offline-tests.log, test-results.json,
offline-cancellation-telemetry.jsonl, packaged-files.json, image-inspect.json,
runtime-and-frozen-verification.json, implementation-hashes.json, and handoff.json.
Original failing evidence, child logs, startup probes, and the previous handoff
are preserved under startup-regression-before/. The first successful run before
a telemetry label correction is retained under startup-regression-first-pass/.
The original P1 diagnosis and reproduction remain in ROOT_CAUSE.md and
reproduced-blocking.log; that production design was preserved.
