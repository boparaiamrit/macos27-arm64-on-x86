**NOT INVOKED: an identical recovered-source boot was already running on the CONTROL guest, so this second launch was refused.**

The request "can u try now" arrived after the parent's transport recovery. That recovery comprised the cache audit, the failed-range probe, the proxy restart and CheckOnly `20261028T043507Z-km7n83rz`. This folder was prepared for one launch of the admitted command:

`& ./test-output/arm-macos/full-system/Launch-FullAttempt.ps1 -GoldenCrypto -CompressedReimsLog -ColdStreamedBoot -ExtendedColdBoot -TraceStorage -Timeout 7200 -HookTimeout 1700 -GuestVolume macos-golden-pristine-guest -StreamVolume macos-golden-stream-read-cache-state -ReadyName stream-ready-read-cache-recovered-live5.json`

The dry `capture.py before` admission check ran at about 2026-10-28T04:44:27Z. Its guest-volume guard found container `macos-golden-full-20261028T044228` running with `macos-golden-pristine-guest` mounted. That container is attempt `20261028T044229Z-f2xjcx4x`, started 2026-10-28T04:42:28.897Z with the same runner arguments and the recovered ready file. The parent delegated it at 04:41:09Z to the task "Boot Golden after verified source recovery", which owns `full-system/transport-recovery/live/`. The evidence is in [before-guest-volume-users.json](before-guest-volume-users.json).

A second VM on the same CONTROL AUX/overlay would corrupt shared guest state and duplicate the single admitted boot. `invoke-once.ps1` was therefore never run, `invocation.json` does not exist, and the launcher was not called.

The dry check's only actions were read-only:

- `docker inspect`/`logs` of both parent services
- a CIM query of sampler PID 104592
- a read of `host-space-live.json`
- short `docker exec` reads of cgroup files in both services and of `/cache` file metadata in the proxy

It aborted before the guest-volume hash helper container started. No guest volume was mounted by this task. No QMP, GDB, NBD, socket, SQLite or payload access occurred. No signal or input reached the running VM. The `before-*` files here are the refused check's snapshot, not a run baseline.

Read-only status snapshot of the other task's run, host time 2026-10-28T04:45:19Z:

- VM container, proxy (StartedAt 04:33:59.448Z) and backend are running.
- `serial.log` had 1507 lines, including Darwin (84), Data unlocked (719), `init-with-data-volume` (1425), `cache-start` (1461) and `auearlyboot` (1505–1507).
- No panic matched yet.
- Proxy cumulative counters since its restart: requests 8704, hits 12180, misses 3, upstream calls 2, cached blocks 5603.

These are host-observed upper bounds only, not results. That task owns the outcome, its evidence and its report. No causal cache claim is made.

## Later diagnosis: proxy stopped by its own guard race (confirmed offline)

That run ended as `guard_or_runtime_failure` after 1920.204 s. Its owning task requested a bounded runner cleanup at 05:14:28Z.

**Guest progress.** `auearlyboot` completed (serial lines 1508–1514). After it, `aidearlyboot`, `EndpointSecurity`, `tzinit`, `dirhelper` and `rootless-init` started (lines 1516–1551). Then disk3 I/O errors appeared. `rootless-init`, `sysstatuscheck` and `prng_seedctl` failed `posix_spawn()` with EIO (lines 2087–2103). No panic, WindowServer or frame was observed.

**What stopped.** The proxy logged `supervisor_stop` with `error_type` `FileNotFoundError` and reason "guard or runtime exception" at 05:12:32.835Z. It then terminated and killed its child, and exited with code 1. The source was healthy: the backend logged `layer_verified` for layer 52 at 05:12:32.823Z, and no `layer_error`/`read_error` occurred during the run. The proxy's final stats show 357 misses and 330 upstream calls since restart; cached blocks went 5945 → 5957 around the stop.

**Mechanism.**

- `cache.py` uses `PRAGMA journal_mode=DELETE`, so every write transaction creates and then deletes `index.sqlite3-journal`.
- The supervisor's `Guard.check()` runs every 50 ms in a separate process (`common.py` lines 117–127). It calls `iterdir()` on `/cache` and then `lstat()` on each entry.
- If the journal is deleted between those two steps, `lstat()` raises `FileNotFoundError`. Only the host-space sample read retries that error.
- A stat that lands mid-unlink can also report zero links, which raises `Refused('unsafe cache file')`.
- Either failure makes the supervisor fail closed.

**Reproduction.** [journal_race_repro.py](journal_race_repro.py) was run in an isolated container: network none, read-only root, 1 CPU, 256 MiB, private 16 MiB tmpfs, and `/proxy` mounted read-only. It used the production `common.py` (SHA-256 `f7113212…bdc42f`) with the production SQLite pragmas. In 10 s it recorded 159,819 guard checks against 304,843 commits. That produced 48,922 `FileNotFoundError` failures and 3,351 `Refused: unsafe cache file` failures. The first failure, after 70 checks, named `/tmp/race/cache/index.sqlite3-journal`. Results are in [journal-race-repro.json](journal-race-repro.json).

The tight-loop tmpfs rate is not a production probability. The race does not need any network fault, and it can recur whenever the cache commits new blocks.

**Proposed fix (not applied).** In `Guard.check()`, treat only `index.sqlite3-journal` vanishing between listing and stat as absent: either `FileNotFoundError` or a zero-link stat. Keep every other check strict. Add the reproduction as a regression test that must report zero errors. This changes the protected cache guard, so it needs parent admission: the offline tests, review and new pins.

## Coordination: fix owned by the parent

- 05:20:37Z: the parent stated it will handle the guard fix and regression test, and will not boot until the fix is verified and repinned. It then started a `journal_guard_review` reviewer.
- 05:20:51Z: the user told this task "fix whatever is required."
- To avoid two writers on the same protected files and services, this task made no edits to `streamed-disk/read-cache-proxy`. At 05:23:10Z, `common.py` was unchanged (`f7113212…bdc42f`).
- This task started no proxy restart, sampler renewal or VM.
- `journal_race_repro.py` can be rerun against the fixed `/proxy`. A correct fix should report zero errors.
- The sampler (PID 104592) stops at 12:52:14 IST. A full 7200 s boot needs it renewed first.
