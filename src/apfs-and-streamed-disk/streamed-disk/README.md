# Streamed read-only RAW guest disk

Implemented and tested with a 296,448-byte handmade ASIF served by an in-memory
loopback HTTP registry, exporting 165,376 oracle RAW bytes through real nbdkit and
libnbd. No live Golden layer retrieval, full metadata plan, APFS extraction, QEMU,
or GUI run was performed by this implementation task. Nothing here establishes
Golden firmware/guest compatibility or acceptable boot latency.

## Files and frozen dependencies

- `streamed_raw.py`: guarded HTTP/layer access, the logical extent index, and
  `RawDisk.read_at(offset, count)` (exact bytes, at most 32 MiB).
- `nbdkit_streamed.py`: API 2 plugin; one source and validated plan per server,
  shared across connections; `SERIALIZE_ALL_REQUESTS`; read-only capabilities.
- `serve.py`: external foreground supervisor, always `nbdkit -f -r` in its own
  process group; cancels blocked HTTP opens/reads during initialization and use.
- `supervision.py`: inherited Unix lifecycle socket, per-layer absolute deadline,
  and verification that the plugin has a real supervisor parent.
- `nbd_source.py`: `NBDSource(socket)` implements the staged fs-explorer
  `RandomAccess` class, `.size`, `.getsize()`, `.read_at(offset, length)`, inherited
  `.read_exact()`, `.close()`, and context management. Its reads clip at EOF per
  fs-explorer's API; reads over 32 MiB are rejected. The server itself rejects any
  out-of-bounds read. It refuses writable exports.
- `Build-Test.ps1`, `test_streamed_disk.py`, `tiny_fixture.py`: Docker-only tests,
  with metadata/log temporary files on tmpfs and all fixture payloads in RAM.
- `test_large_cache.py`, `Dockerfile.large-cache.offline`: small synthetic
  cache/resource tests and a Python-only image refresh over the verified base.

`frozen.py` verifies all three SHA256 hashes against the reviewed snapshot before
importing `oci_stream.py`, `asif_plan.py`, and `asif_to_raw.py`. It reuses their
`load_pins`, `GHCR`, `LayerSource`, complete-layer digest validation, `make_plan`,
and `layer_extents`. The converter CLI is never called. No frozen file was edited.
The staged BSD fs-explorer reader checks its own pinned source hash through the
frozen planner; upstream license remains `../apfs-tools/LICENSE`. Fixture builder
attribution is in `tiny_fixture.py`; original helper remains unchanged.

`CONVERTER_SNAPSHOT` defaults in Docker to `/frozen`; `APFS_TOOLS_SRC` to
`/apfs-src`. Mount both read-only. Host imports default to their sibling paths.
No Python bytecode is written.

The full export accepts only manifest
`sha256:b78a521145ebef24e9916c0b3999e165bb12b587d11524c5fa3ba4fe7bf79bb9`,
ASIF length **35,735,707,648**, RAW length **50,000,000,000**, and hash-verified
Tart config from `../full-system/inputs/config.json`. It does not access `aux.img`.
Test-only alternate manifests require both `STREAMED_DISK_TEST_MODE=1` and the
explicit plugin `fixture-url` option restricted to literal `127.0.0.1` HTTP.
The normal launcher exposes neither test option.
Bare `nbdkit ... python nbdkit_streamed.py` is refused before initialization or
HTTP. Always launch through `serve.py` (the image entrypoint). Internal
`initialize()`/`CheckedStream` helpers provide cooperative byte checks only;
calling them directly does not provide blocking-I/O cancellation.

## Reproduce the offline checks

From PowerShell in this repository:

```powershell
& .\test-output\arm-macos\streamed-disk\Build-Test.ps1
```

The script builds only `macos-streamed-guest:local` over the existing
`macos-orchard-runtime:local` and runs with `--network none`, a read-only root,
read-only source mounts, 64 MiB `/tmp` tmpfs, a 512 MiB memory limit, and no added
capabilities. Loopback HTTP remains available inside the network-isolated test
container. It uses no host packages or Docker daemon changes. It refuses to start
below 11 GiB host free space, reserving the requested 10 GiB plus 1 GiB allowance.

For the startup regression, rebuilding dependencies with networking disabled
missed the install cache and failed without downloading packages. The successful
offline refresh instead used the existing pinned local streamed image and copied
only Python files, then ran the same suite and package checks:

```powershell
docker build --network none --pull=false -t macos-streamed-guest:local `
  -f .\test-output\arm-macos\streamed-disk\artifacts\Dockerfile.offline-refresh `
  .\test-output\arm-macos\streamed-disk
& .\test-output\arm-macos\streamed-disk\Build-Test.ps1 -SkipBuild
```

Check C: has at least 11 GiB free before that build. The refresh requires the
pinned local image; it installs no packages and preserves the existing entrypoint.

Evidence lives in `artifacts/test-results.json`, `offline-tests.log`,
`offline-oracle.json`, `offline-nbd-telemetry.jsonl`, `image-inspect.json`, and
`implementation-hashes.json`. Tests include whole-disk oracle equality, 200
seeded random ranges, partial-sector zeros, swapped physical order, truncated
ASIF tail, misaligned OCI layer boundaries, corrupted layer refusal, bounds,
cache limits, two concurrent real NBD clients, repeated opens without rebuilding
the plan, actual invalid NBD writes/reads, and idle reserve/staleness shutdown.
The follow-up suite preserves those **18 checks** and adds **11 cancellation
checks**, for **29 passed tests**. Real loopback HTTP tests include a body sending
one byte every 30 ms (inside its 5-second idle timeout), hung response headers,
per-layer and overall initialization deadlines, low/stale samples during blocked
initialization, and cancellation of a cold real NBD read. Blocked NBD clients
receive errors without partial successful responses. A TERM-ignoring child and
grandchild are killed and reaped while an unrelated process remains alive.
Layer deadline tests use 0.5 seconds; total initialization uses 5 seconds with a
10-second layer budget, and the TERM-ignoring process fixture uses 0.6 seconds.
Termination grace is 0.15 seconds. Fixture HTTP/readiness waits allow up to five
seconds for interpreter/plugin startup and include child logs on failure.
Deadline expiry is checked against its configured budget (50 ms early tolerance,
500 ms late tolerance); cancellation cleanup must still finish in under three
seconds from expiry or the injected guard/signal. Launch-to-stop time is recorded
separately. Evidence is in
`offline-cancellation-telemetry.jsonl` (including process-group disappearance).
`reproduced-blocking.log` records the pre-fix real HTTP slow-drip reproduction.
The invalid command tests set libnbd strict mode to zero so rejection occurs at
the real server. Errors are recorded in `offline-oracle.json`.

The first smoke runs timed out waiting for readiness: nbdkit redirects stdout
after `get_ready`, even in foreground mode. JSON now goes explicitly to stderr;
the diagnostic run is retained in `initial-readiness-timeouts.log`. This was a
readiness-observation failure, and the corrected complete suite passed.

The startup-budget rerun exposed another test timing assumption: real fixture
launches took 1.51–2.20 seconds to reach HTTP, beyond a one-second assertion.
The former 0.6-second initialization fixture could also expire during plugin
imports, before its intended slow-drip request. The corrected tests separate
startup allowance from measured deadline/cancellation behavior; production
supervision and guard behavior are unchanged. The failing parent run, diagnostic
child logs, and measured startup probes are retained under
`artifacts/startup-regression-before/`.

## Bounded larger RAM cache (offline validation only)

The CLI, plugin, and `VerifiedSource` adapter accept an explicit integer cache
capacity from **1 through 8**, with **2 still the default**. Booleans, fractional
values, and out-of-range counts are rejected. The adapter calls the frozen
`LayerSource` constructor with `min(requested, 2)`, then sets its mutable LRU
capacity after resource admission. This adapts resource policy; it changes no
cryptographic check, pin, layer-byte mapping, decode bound, or verified commit.
The frozen source and its three expected hashes remain unchanged.

For **more than two layers**, admission requires a readable, positive finite
cgroup v2 `/sys/fs/cgroup/memory.max` of at least
`requested_layers * 512 MiB + 2 GiB`. Eight layers require **6 GiB**, retaining at
most **4 GiB** of verified decompressed layers and reserving **2 GiB** for decode
and safety headroom. Admission runs before frozen source allocation or network
fetch. Missing, unreadable, malformed, unbounded (`max`), or insufficient limits
fail closed. cgroup v1 and host-RAM estimates do not authorize the extension.
One- and two-layer operation retains its existing resource-admission behavior.
`cache_resource_admitted` records the capacity, required bytes, and observed hard
limit. No payload files, persistent cache, background prefetch, or full RAW is
introduced. The eight-layer working set can still evict when nine or more layers
are used; this profile does not establish boot success or bounded guest latency.

Use the dedicated offline validator for this profile:

```powershell
& .\test-output\arm-macos\streamed-disk\artifacts\large-cache\validate.ps1
```

It verifies base image ID
`sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`,
builds only **`macos-streamed-guest-large:local`** with `--network none`,
`--pull=false`, and `COPY *.py`, and leaves the original image tag intact. No apt
step runs. All ten packaged Python files must match their host SHA256 hashes.
This is the profile-specific validator; the older build examples above target
the original image and are not used for this extension.

The existing **29 NBD/cancellation tests** and **14 cache/resource tests** run in
separate `--network none`, read-only, two-CPU containers with 512 MiB and 6 GiB
memory ceilings respectively. Fixtures manufacture ten tiny Apple-LZ4 layers,
verify eight resident hits without refetching, and prove ninth-layer LRU eviction,
compressed/raw hash refusal, strict count validation, pre-fetch resource refusal,
and real read-only NBD operation at capacity eight. The large-capacity ceiling
does not allocate that memory: test processes have an inherited 512 MiB address
space limit, and evidence gates actual cgroup peak memory below 1 GiB. Internal
60/90-second alarms plus external 70/100-second timeouts bound the suites.
`artifacts/large-cache/` contains exact test commands, logs, resource measurements,
source/frozen hashes, image identities, and a machine-readable `handoff.json`.

`artifacts/large-cache/proposed-live-profile.ps1.txt` is a **proposed, unexecuted**
6 GiB / two-CPU / eight-layer read-only backend command for parent review. It
uses a new container name and socket. The parent owns sampler freshness, live
warmup, backend cutover, and the running guest. This implementation task performs
no live Golden fetch, backend restart, guest read, QEMU launch, or cleanup.

## Parent-owned live launch (not executed here)

The parent must keep its Windows C: watcher updating atomically, and mount the
**directory** containing `host-space-live.json`, rather than mounting that file
alone (atomic replacement would otherwise leave a stale inode). The required
JSON schema is `{"drive":"C:\\","free_bytes":16700000000,"observed_at":<Unix seconds>}`.
Startup, requests, verified cache hits, and streamed HTTP reads fail closed below
**10 GiB** or when that timestamp is older than **20 seconds**. Future timestamps
over two seconds, malformed samples, and missing samples are refused. The
external supervisor checks every **50 ms**, from child launch through
initialization and idle/active service. On guard failure or deadline expiry it
sends **SIGTERM to its owned process group**, then **SIGKILL after at most five
seconds** if still alive; leader/descendant reaping has an additional bounded
two-second wait and reports failure explicitly. This interrupts blocked HTTP
open/read calls independently of the socket idle timeout. No watchdog threads
are created in nbdkit before or after its fork lifecycle. Post-read guards still
prevent returning new bytes after a failed guard.

For an already prepared parent Linux container mounting this code, frozen code,
the reader, and full-system directory read-only:

```sh
/usr/bin/python3 /streamed-disk/serve.py \
  --socket /work/streamed-guest.nbd \
  --manifest /full-system/inputs/manifest.json \
  --config /full-system/inputs/config.json \
  --host-space /full-system/host-space-live.json \
  --cache-layers 2 --warm-layer-zero
```

The socket must be new and absolute, on a Linux filesystem (for example the
parent's `macos-orchard-build` volume mounted at `/work`). The launcher refuses
an existing socket/path and never deletes it. The plugin makes no payload files,
download cache, RAW, checkpoint, or overlay. A normal Docker run can use the image
entrypoint with those same arguments; mount `/frozen`, `/apfs-src`, and
`/full-system` as described above and the shared Linux volume at `/work`.
The parent must provide sufficient RAM: the offline 512 MiB test container limit
is inappropriate for real 512 MiB layers.

Wait for JSON `event=export_ready` on **stderr**, not socket-path existence alone.
It contains `manifest_pin`, `config_pin`, `planDigest`, `getsize`, `readonly:true`,
`max_read_bytes`, `thread_model`, and bitmap planning working-set bytes. Pins are
public hashes; URLs, signed redirect query strings, auth tokens, headers, config
contents, and payload bytes are omitted. Events include `http_fetch_start`,
`http_request` (including redirect requests), `http_response`, `layer_fetch_start`,
`layer_verified`, `layer_error`, `plan_validated`, `read_error`, and `guard_stop`.
Supervisor events include `supervisor_started`, `supervisor_deadline_stop`
(`scope=layer` or `initialization`), `guard_stop` (`owner=supervisor`),
`supervisor_signal_stop`, `supervisor_terminate`, `supervisor_kill`,
`supervisor_group_reaped`, `supervisor_stopped`, and `supervisor_error`.
Cancellation returns nonzero, including idle guard shutdown. A direct plugin
launch emits `supervisor_required` and fails. SIGTERM/SIGINT sent to `serve.py`
also perform bounded group cleanup; keep it running as the export's parent.
The lifecycle channel carries status only, never payloads or URLs.
`layer_verified` is emitted only after both compressed and decompressed hashes
pass. Logs may also contain nbdkit diagnostic lines; JSON consumers should select
JSON lines. Logs are not payload caches, but parent log retention should be bounded.

The parent can use this exact backing URI (a RAW byte export):

```text
nbd+unix:///?socket=/work/streamed-guest.nbd
```

For a direct read-only QEMU drive the parent may use
`-drive if=none,id=guest,format=raw,readonly=on,file=nbd+unix:///?socket=/work/streamed-guest.nbd`.
For a writable guest, the parent may create a small qcow2 overlay using
`qemu-img create -f qcow2 -F raw -b 'nbd+unix:///?socket=/work/streamed-guest.nbd' <new-overlay-path>`
and attach that overlay. These are integration examples, not executed QEMU tests.
The parent's QEMU choice/hash verification, device arguments, overlay allocation
guard, VM lifecycle, and GUI validation remain its responsibility. No VM was run.

Use the adapter inside Linux with python3-libnbd installed by this image:

```python
from nbd_source import NBDSource
from fs_explorer import open_source

with NBDSource('/work/streamed-guest.nbd') as raw:
    assert raw.getsize() == 50_000_000_000
    # Partition/volume paths must be discovered on the live disk by the parent.
    with open_source(raw, backend='pure', threads=1,
                     cache_size=16 << 20, spool_limit=0) as fs:
        # e.g. fs.read_file(<discovered AVPBooter/SystemVersion path>, max_size=...)
        pass
```

This adapter integration was accepted by `open_source` using the tiny fixture.
That fixture has no APFS filesystem: live AVPBooter/SystemVersion extraction is
explicitly untested. Closing the fs-explorer source also closes its NBD adapter;
the outer adapter context may safely close it again.

## Limits and latency advisory

All client requests are serialized across all connections because the reviewed
cache and HTTP session are not thread safe. The logical index is sorted by RAW
target; `bisect` skips earlier extents, and all holes return zeros without a
fetch. Physical-layer boundaries are split with the frozen converter helper.
Source reads are at most the frozen 16 MiB limit; RAW/NBD reads at most 32 MiB.
No block-status/extents acceleration, write, trim, zero, or cache command is
advertised. A source/guard/read error produces an NBD error, never partial data.

`--cache-layers` accepts 1 through 8 (default 2); maximum decompressed retained
layer storage is `capacity * 512 MiB`. Capacities above two require the finite
cgroup budget documented above. There is additional bounded
planner, extent-index, Python, decompression, network-buffer, and per-read memory.
The reviewed planner permits up to 64 MiB of bitmap working set and 200,000
extents; the task context reports about 15 MiB of Golden bitmap data and roughly
1.1 GiB observed elsewhere, which this task did **not** rerun or independently
measure. Completed bitmaps are represented by the validated plan; the full
bitmap working set is not needed for subsequent RAW reads. Cache eviction happens
before a new whole layer is decoded. No full OS payload is retained on disk.

The parent-provided cold-planning estimate is approximately **3.09 GB compressed
network traffic over seven bitmap layers**, potentially **5–10 minutes** before
readiness. This estimate is not a measurement from this task. Every cold guest
read may require downloading and hashing an entire compressed layer (up to
512 MiB decompressed), and a two-layer cache can thrash during random reads.
An optional layer-zero warmup may itself add a fetch; it does not guarantee fast
firmware reads if their mapped data is in different physical layers. Serialized
requests amplify stalls. Runtime/firmware timeouts and usable GUI performance
remain unproven. There is no persistent cache, background prefetch, or retry of
failed payload reads; an evicted layer is fetched and verified again.

The frozen GHCR implementation has connect/read-idle timeouts of 15/120 seconds
for blobs, 15/60 seconds for token requests, and one token refresh retry on 401.
The supervisor additionally enforces a **900-second per-layer wall deadline**
beginning before HTTP open, including authentication, redirects, response
headers, body streaming, hashing/decompression, and response cleanup. It also
enforces a separate **3600-second total initialization deadline**, including plan
building and optional layer-zero warmup. Thus a series of progressing layers
cannot keep initialization alive indefinitely. Both deadlines use monotonic
time; status completion cannot disarm an expired deadline. Child post-read and
initialization-completion checks retain byte/readiness protection.

`--layer-deadline-seconds` and `--initialization-deadline-seconds` may make those
limits smaller, never exceed 900 per layer or 3600 for initialization. The longer
startup cap accounts for measured cold metadata retrieval at about 150 seconds
per layer; it does not relax the host-space or per-layer guards.
`--termination-grace-seconds` may reduce the
grace, never exceed five seconds. Nonpositive/nonfinite values are refused.
The 10 GiB floor and 20-second freshness limit remain fixed. A deadline or failed
guard stops the entire shared export; restart only after the parent has repaired
the cause and supplies a new socket path. Timeout/error class is explicit in
JSON; external exception strings are omitted to avoid signed URL leakage.

Official API references consulted for this implementation:

- [nbdkit Python API 2, callbacks, threading, errors](https://libguestfs.org/nbdkit-python-plugin.3.html)
- [nbdkit plugin lifecycle and after_fork](https://libguestfs.org/nbdkit-plugin.3.html)
- [libnbd Python bindings](https://libguestfs.org/libnbd-python.3.html)
- [libnbd strict-mode server rejection testing](https://libguestfs.org/nbd_set_strict_mode.3.html)
- [libnbd bounded whole reads](https://libguestfs.org/nbd_pread.3.html)
