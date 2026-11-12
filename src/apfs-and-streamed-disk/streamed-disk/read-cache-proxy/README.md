# Bounded returned-block NBD cache

This proxy is implemented and offline-qualified. No Golden payload was read, no live proxy was started, and no VM ran during this task. Parent review and deployment admission remain required.

The proxy sits between QEMU and the existing read-only, verified streamed backend. It caches only 64-KiB blocks covering actual guest requests, clipped to exact EOF. The source pins and cache geometry bind the cache identity. A cache hit verifies a SHA-256 over source identity, logical offset, valid length and the complete padded block before returning its bytes. This is local cache consistency and provenance from previously returned, upstream-verified bytes. It is not independent OCI/Merkle attestation and does not protect against coordinated malicious edits to both payload and index by a compromised host. The parent must bind the upstream socket to the original trusted verified backend; NBD read-only/size negotiation alone cannot authenticate image content.

The cache admits at most **8192 blocks / 512 MiB** of data. Once full, new blocks are served from the verified upstream without growing the cache. Existing blocks remain available. Flat payload slots avoid SQLite large-BLOB page amplification; SQLite stores only the bounded offset/slot/length/digest index and identity. Data is fsynced and read back before the validity transaction commits with SQLite FULL synchronous durability. Interrupted uncommitted suffixes are discarded only after validating the committed dense index. There is no LRU eviction, cache rebase, ASIF decoding, full RAW image, or guest-write caching.

The independent supervisor enforces a **1-GiB maximum** on both total nominal and allocated cache files, including SQLite journals. Unknown files, symlinks, hard links and identity/hash uncertainty fail closed. SQLite temporary storage stays in memory and its page cache is capped at 8 MiB; the index is capped at 64 MiB. The actual full-capacity check used **537,407,488 bytes** nominal and allocated, about 512.5 MiB including metadata. Extra uncached reads did not grow it, and a restart served a verified cache hit.

All requests are serialized by nbdkit and a Python reentrant lock; SQLite allows callback-thread access only under that lock. The exported NBD maximum request is **1 MiB**, reducing the risk of one request needing several slow upstream layers. The internal cache reader still rejects counts above 32 MiB. Covering-block fetches can include at most the bounded 64-KiB edge rounding. The proxy's 900-second deadline applies to each complete request, including cache/file I/O; it can be stricter than the upstream's 900-second *per-layer* deadline. Multi-gap request failure commits no new blocks and returns no successful partial reply.

Startup validates the production manifest/config/plan/50-GB logical size, actual upstream read-only status and size, cache identity and upstream socket identity. The ready event records the socket device/inode and readiness-file digest. Restart always reconnects and validates the upstream; an unavailable upstream cannot be waived by an old cache. After admitted startup, fully cached reads can succeed if the upstream later disappears, and uncached reads fail closed.

## Supervision and deployment contract

Use `serve.py`; bare `plugin.py` startup is refused before connecting upstream. A private inherited, parent/peer-validated lifecycle channel carries no disk payload. The separate supervisor covers initial connect/metadata/file I/O, active reads, cached reads, and idle service. Normal guard polling is 50 ms. Initialization and each operation are capped at 900 seconds. Guard failures, expired operations, invalid lifecycle events and read-integrity errors stop the owned process group, with one-second TERM grace, KILL and bounded reaping, including descendants. A blocked C-level libnbd call cannot prevent this external stop.

The live host sample must remain a current C: sample with the unconditional 10-GiB floor, age no more than 20 seconds and future skew no more than two seconds. Only denied/missing sample opens are retried for at most 0.5 seconds, matching the existing Windows sharing-contention policy. Invalid, low or stale samples are never retried into acceptance or replaced by old data. During contention, a guard read can take that extra bounded retry time. Mount the **full-system directory**, not an individual JSON file, so atomic sample replacement remains visible.

The process refuses unlimited/oversized cgroups: memory must be finite between 128 MiB and 1 GiB, extra swap must be zero, CPU quota at most one CPU, pids at most 128. Deployment should use exactly the task's 1-GiB/equal-memory-swap, one-CPU, 128-pid limits, read-only root, network none, dropped capabilities, no-new-privileges, 16-MiB tmpfs and Docker log rotation totaling at most 4 MiB. No image build or dependency installation is needed; the pinned existing image contains Python, nbdkit, libnbd and SQLite.

Use the five production files listed in `artifacts/source-pins.json` from a read-only source mount. Never set `READ_CACHE_PROXY_TEST_MODE` in production; it exists only for clearly labelled small offline fixtures. In production, constants fix the exact previously admitted Golden source pins.

Proposed container layout, **not launched here**:

```text
Pinned image:
  sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635

/proxy       this source directory, read-only
/parent      test-output/arm-macos, read-only (directory mount)
/upstream    original streamed-state volume, read-only
/stream      NEW proxy state volume, writable
/stream/cache an already-created empty private real directory for first admission

python3 -B /proxy/serve.py \
  --socket /stream/golden-live5.nbd \
  --upstream /upstream/golden-live5.nbd \
  --ready /parent/full-system/stream-ready-large-live5.json \
  --cache /stream/cache \
  --host-space /parent/full-system/host-space-live.json
```

The exported socket deliberately retains `/stream/golden-live5.nbd` inside the VM so the existing overlay's backing URI can remain stable. The parent owns deployment volume/socket bindings and runner admission. Wait for the JSON `export_ready` event on stderr. Its `all_disk_layers_verified=false` and provenance text are intentional: metadata readiness is neither a complete image checkpoint nor proof that all payload layers were fetched. Bounded `cache_stats` telemetry is emitted on the first successful request, every 128 requests or after 60 seconds of request activity, and at cleanup. It contains counters, not payload.

## Verification and limits

Final offline suite: **30/30 tests pass in 22.701 seconds**. It includes real nbdkit/libnbd oracle reads, sparse zero regions, unaligned/tail reads, advertised request maximum, concurrent clients, write refusal, cache hits after upstream loss, restart revalidation, wrong pins/size/writable upstream, payload/index corruption, interrupted payload and SQLite transactions, full-admission behavior, and cancellation during blocked initial connect/read, low/stale space, disk overrun and an unresponsive descendant. The maximum recorded stop interval was **1.719 seconds** after the test injection/entry observation; shortened operation/startup fixtures are separate from production 900-second limits. Every checked owned process group was gone. The first run's only failure was a fixture attempting graceful upstream shutdown while clients were connected; the corrected test uses a hard upstream loss and production code was not changed for that fixture.

The full 512-MiB capacity check completed in 4.126 seconds, with **732,381,184 bytes peak cgroup memory**, no OOM/max events and no extra swap, below the one-GiB cap. Counters include filesystem cache. The disposable capacity volume was removed after evidence collection; all owned test containers are gone. This task retained only source and small evidence files, although Docker's backing VHD allocation may not immediately shrink after deleting a test volume.

The measured prior trace's 64-KiB-rounded union was about 283 MiB, which fits this cap. That projects only potential cache reuse: it does not promise HTTP savings or a boot-time speedup. Most previously observed raw reads were new addresses; this cache mainly avoids replay after a reboot and some repeated metadata reads. Cold unique blocks still require the original whole-layer verification/download path. Live cache performance, full boot progression and GUI compatibility remain untested.

Reproduce the offline suite with the pinned image, no network, source mounted read-only at `/proxy`, one CPU, one GiB memory/equal memory-swap, 128 pids and a 128-MiB `/tmp` tmpfs:

```text
python3 -B -m unittest -v test_proxy
```

For the separate capacity check, use a NEW empty volume mounted at `/capacity`, writable evidence directory `/artifacts`, and the same finite resources with a 16-MiB tmpfs:

```text
python3 -B /proxy/capacity_check.py
```

Both commands run inside the container with working directory `/proxy` and `PYTHONDONTWRITEBYTECODE=1`. The capacity script intentionally refuses a nonempty volume. Fixture samples and source data are synthetic; they are never substitutes for the production host guard or real upstream verification. No Golden payload, live backend, sampler, guest pair, source reader or frozen module was modified or accessed by these tests. Codebase graph tools were unavailable, so related contracts were read directly from source.

The exact Docker argument assembly is also supplied as `Test-Offline.ps1`:

```powershell
& ./test-output/arm-macos/streamed-disk/read-cache-proxy/Test-Offline.ps1
& ./test-output/arm-macos/streamed-disk/read-cache-proxy/Test-Offline.ps1 -Capacity
```

The reproduction wrapper checks Windows headroom, creates only a uniquely named owned capacity-test volume, and removes that volume after recording results. Its PowerShell syntax was checked; the underlying Docker invocations above are the commands actually used for qualification.
