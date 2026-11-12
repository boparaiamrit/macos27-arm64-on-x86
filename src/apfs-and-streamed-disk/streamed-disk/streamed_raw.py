"""Guarded, bounded RAM-only OCI -> ASIF -> logical RAW access."""
from bisect import bisect_right
from contextlib import contextmanager
import json
import math
from pathlib import Path
import threading
import time
import sys
from urllib.parse import urlsplit

import requests
from frozen import oci, planner, converter
from supervision import LAYER_SECONDS

MAX_READ = 32 * oci.MiB
RESERVE = 10 * oci.GiB
MAX_AGE = 20.0
GOLDEN_RAW_SIZE = 50_000_000_000
GOLDEN_ASIF_SIZE = 35_735_707_648
CACHE_HEADROOM = 2 * oci.GiB
CGROUP_MEMORY_MAX = Path("/sys/fs/cgroup/memory.max")


def emit(event, **fields):
    # Intentionally never include URLs, request headers, tokens or exception text.
    # nbdkit redirects stdout after get_ready, including foreground mode.
    print(json.dumps(dict(event=event, observed_at=time.time(), **fields), sort_keys=True),
          file=sys.stderr, flush=True)


class GuardError(RuntimeError):
    pass


class CacheBudgetError(RuntimeError):
    pass


def cache_layer_count(value):
    """Canonical CLI/plugin values; do not coerce booleans or fractional counts."""
    if type(value) is int and 1 <= value <= 8:
        return value
    if type(value) is str and value in tuple(str(n) for n in range(1, 9)):
        return int(value)
    raise ValueError("cache-layers must be an integer from 1 through 8")


def cgroup_memory_limit():
    """Only the known cgroup v2 hard limit is an admission authority.

    Docker exposes this path in its cgroup namespace. Host RAM, memory.high,
    environment hints, and missing/unlimited limits never authorize a big cache.
    """
    try:
        value = CGROUP_MEMORY_MAX.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError) as exc:
        raise CacheBudgetError("large cache requires a readable finite cgroup v2 memory.max") from exc
    if value == "max":
        raise CacheBudgetError("large cache requires an explicit finite cgroup memory limit")
    if not value.isascii() or not value.isdecimal() or len(value) > 20 or int(value) <= 0:
        raise CacheBudgetError("large cache cgroup memory limit is unknown or invalid")
    return int(value)


class HostSpaceGuard:
    """Fail closed against the parent's fresh Windows C: sample, not Linux statvfs."""
    def __init__(self, path, now=time.time):
        self.path, self.now = Path(path), now

    def check(self):
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(4097)
            if len(raw) > 4096:
                raise GuardError("oversized host-space sample")
            sample = json.loads(raw)
            free, observed = sample["free_bytes"], sample["observed_at"]
            if str(sample["drive"]).upper().rstrip("\\/") != "C:":
                raise GuardError("host-space sample is not for C:")
            if type(free) is not int or free < RESERVE:
                raise GuardError("Windows C: reserve below 10 GiB or invalid")
            if type(observed) not in (int, float) or not math.isfinite(observed):
                raise GuardError("invalid host-space timestamp")
            age = self.now() - observed
            if not -2 <= age <= MAX_AGE:
                raise GuardError("host-space sample stale beyond 20 seconds or from future")
            return free
        except GuardError:
            raise
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise GuardError("missing or malformed host-space sample") from exc


class GuardedSession(requests.Session):
    def __init__(self, guard, report=emit):
        super().__init__()
        self.guard, self.report = guard, report
        self.trust_env = False

    def send(self, request, **kwargs):
        # send() also covers redirect hops followed internally by requests.
        self.guard.check()
        self.report("http_request", method=request.method, host=urlsplit(request.url).hostname)
        return super().send(request, **kwargs)

    def request(self, method, url, **kwargs):
        self.guard.check()
        self.report("http_fetch_start", method=method, host=urlsplit(url).hostname)
        response = super().request(method, url, **kwargs)
        try:
            self.guard.check()
        except BaseException:
            response.close()
            raise
        self.report("http_response", status=response.status_code)
        return response


class CheckedStream:
    """Cooperative byte checks; serve.py supplies blocking-I/O cancellation."""
    def __init__(self, raw, guard, deadline):
        self.raw, self.guard, self.deadline = raw, guard, deadline

    def read(self, count):
        self.check()
        result = self.raw.read(count)
        self.check()
        return result

    def check(self):
        self.guard.check()
        if time.monotonic() > self.deadline:
            raise TimeoutError("layer retrieval exceeded wall deadline (at most 900 seconds)")


class GuardedBlobs:
    def __init__(self, blobs, guard, control=None):
        self.blobs, self.guard, self.control = blobs, guard, control

    @contextmanager
    def open(self, layer):
        self.guard.check()
        # Announce before HTTP open (including authentication/headers), not just
        # before read. serve.py can kill the child even inside frozen blocking I/O.
        deadline = self.control.layer_start() if self.control else time.monotonic() + LAYER_SECONDS
        try:
            with self.blobs.open(layer) as raw:
                checked = CheckedStream(raw, self.guard, deadline)
                yield checked
                checked.check()
            checked.check()
        finally:
            if self.control:
                self.control.layer_end()


class FixtureHTTPBlobs:
    """Tiny loopback-only test registry; no payload files and no live registry."""
    def __init__(self, url, session):
        parts = urlsplit(url)
        oci.require(parts.scheme == "http" and parts.hostname == "127.0.0.1"
                    and parts.port and not parts.username and not parts.password
                    and parts.path in ("", "/") and not parts.query and not parts.fragment,
                    "test registry must be literal loopback HTTP")
        self.url, self.session = url.rstrip("/"), session

    @contextmanager
    def open(self, layer):
        with self.session.get(self.url + "/" + layer.digest[7:], stream=True,
                              timeout=(2, 5), allow_redirects=False) as response:
            oci.require(response.status_code == 200, "test registry HTTP error")
            oci.require(int(response.headers["Content-Length"]) == layer.compressed_size,
                        "test registry blob length mismatch")
            yield response.raw


class VerifiedSource(oci.LayerSource):
    def __init__(self, pins, blobs, cache_layers=2, max_fetch_bytes=None, *, guard, report=emit):
        oci.require(type(cache_layers) is int and 1 <= cache_layers <= 8,
                    "layer cache must be an integer from 1 through 8")
        # Admit before the frozen base allocates state or any layer can be fetched.
        memory_limit = None
        if cache_layers > 2:
            required = cache_layers * oci.MAX_LAYER + CACHE_HEADROOM
            memory_limit = cgroup_memory_limit()
            if memory_limit < required:
                raise CacheBudgetError(f"large cache needs at least {required} cgroup memory bytes")
            report("cache_resource_admitted", cache_layers=cache_layers,
                   memory_limit_bytes=memory_limit, required_bytes=required)
        # Resource-policy adaptation only: the frozen decoder, pins, hashes,
        # bounds, verified commit and get_layer LRU implementation are unchanged.
        super().__init__(pins, blobs, cache_layers=min(cache_layers, 2), max_fetch_bytes=max_fetch_bytes)
        self.cache_layers = cache_layers
        self.cache_memory_limit = memory_limit
        self.guard, self.report = guard, report

    def get_layer(self, index):
        self.guard.check()
        miss = index not in self.cache
        start = time.monotonic()
        if miss:
            self.report("layer_fetch_start", index=index,
                        compressed_bytes=self.pins.layers[index].compressed_size)
        try:
            data = super().get_layer(index)
            self.guard.check()
        except Exception as exc:
            safe_reason = str(exc)[:300] if isinstance(exc, (GuardError, TimeoutError, oci.ConversionError)) else None
            self.report("layer_error", index=index, error_type=type(exc).__name__, reason=safe_reason)
            raise RuntimeError(f"layer {index} failed ({type(exc).__name__}); see JSON telemetry") from None
        if miss:
            self.report("layer_verified", index=index, seconds=round(time.monotonic() - start, 3),
                        fetched_bytes=self.fetch_bytes, fetch_count=self.fetch_count,
                        cached_bytes=sum(map(len, self.cache.values())))
        return data


class RawDisk:
    def __init__(self, source, plan, guard):
        self.source, self.plan, self.guard = source, plan, guard
        self.size = plan.logical_size
        # Reuse the frozen converter's physical-layer splitting and bounds check.
        groups = converter.layer_extents(plan, source.pins)
        self.extents = sorted((e for group in groups for e in group), key=lambda e: e.target)
        self.starts = [e.target for e in self.extents]
        end = 0
        for e in self.extents:
            oci.require(type(e.length) is int and e.length > 0 and e.target >= end
                        and e.target + e.length <= self.size and e.source >= 0
                        and e.source + e.length <= source.size,
                        "logical RAW extents overlap or exceed bounds")
            end = e.target + e.length
        self.lock = threading.RLock()

    def read_at(self, offset, count):
        oci.require(type(offset) is int and type(count) is int and 0 <= offset <= self.size
                    and 0 <= count <= MAX_READ and offset + count <= self.size,
                    "RAW read outside disk or above 32 MiB")
        with self.lock:
            self.guard.check()
            result = bytearray(count)  # Every hole, including stale ASIF sectors, starts zero.
            end, cursor = offset + count, offset
            index = max(0, bisect_right(self.starts, offset) - 1)
            while index < len(self.extents):
                e = self.extents[index]
                if e.target >= end:
                    break
                start, stop = max(cursor, e.target), min(end, e.target + e.length)
                while start < stop:
                    self.guard.check()
                    n = min(stop - start, oci.MAX_READ)
                    data = self.source.read_at(e.source + start - e.target, n)
                    oci.require(len(data) == n, "short verified ASIF read")
                    result[start - offset:start - offset + n] = data
                    start += n
                cursor = max(cursor, stop)
                index += 1
            self.guard.check()  # No partial/unverified reply on errors or guard failure.
            return bytes(result)

    def close(self):
        with self.lock:
            self.source.clear_cache()
            self.source.blobs.blobs.session.close()


def initialize(options, control=None):
    """Internal constructor. Live plugin use requires serve.py's control channel."""
    guard = HostSpaceGuard(options["host-space"])
    guard.check()
    fixture_url = options.get("fixture-url")
    digest = options.get("manifest-digest", oci.GOLDEN_DIGEST)
    if fixture_url:
        import os
        oci.require(os.environ.get("STREAMED_DISK_TEST_MODE") == "1", "fixture mode not enabled")
    else:
        oci.require(digest == oci.GOLDEN_DIGEST, "only the pinned Golden manifest is supported")
    pins = oci.load_pins(options["manifest"], options["config"], digest)
    session = GuardedSession(guard)
    if fixture_url:
        blobs = FixtureHTTPBlobs(fixture_url, session)
    else:
        oci.require(pins.size == GOLDEN_ASIF_SIZE, "pinned ASIF size mismatch")
        blobs = oci.GHCR(options.get("repository", "cirruslabs/macos-golden-gate-vanilla"))
        blobs.session.close()
        blobs.session = session
    source = VerifiedSource(pins, GuardedBlobs(blobs, guard, control),
                            cache_layers=cache_layer_count(options.get("cache-layers", "2")), guard=guard)
    emit("plan_start", manifest_pin=pins.manifest_digest, source_bytes=pins.size,
         payload_cache="RAM-only", cache_layers=source.cache_layers)
    plan = planner.make_plan(source)
    emit("plan_validated", logical_bytes=plan.logical_size, extent_count=len(plan.extents))
    if not fixture_url:
        oci.require(plan.logical_size == GOLDEN_RAW_SIZE, "pinned RAW size mismatch")
    disk = RawDisk(source, plan, guard)
    emit("logical_index_ready", extent_count=len(disk.extents))
    if options.get("warm-layer-zero", "false") == "true":
        source.get_layer(0)
    guard.check()
    return disk
