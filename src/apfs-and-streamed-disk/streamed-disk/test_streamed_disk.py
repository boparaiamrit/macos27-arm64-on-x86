"""Offline unit and real nbdkit/libnbd smoke tests. No VM or real guest fetch."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

import nbd
from frozen import oci, planner
from streamed_raw import (RawDisk, HostSpaceGuard, GuardError, VerifiedSource,
                          MAX_READ, RESERVE, initialize, CheckedStream)
from nbd_source import NBDSource
from tiny_fixture import package, fixture, CS, BS


class MemoryBlobs:
    def __init__(self, blobs):
        self.blobs, self.calls = blobs, 0

    def open(self, layer):
        self.calls += 1
        return io.BytesIO(self.blobs[layer.digest[7:]])


def write_space(path, free=RESERVE + (2 << 30), observed=None):
    data = {"drive": "C:\\", "free_bytes": free,
            "observed_at": time.time() if observed is None else observed}
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data))
    temporary.replace(path)


def fixture_command(root, space, url, digest, extra=()):
    return [sys.executable, str(Path(__file__).with_name("serve.py")),
            "--socket", str(root / "disk.sock"), "--manifest", str(root / "manifest.json"),
            "--config", str(root / "config.json"), "--host-space", str(space),
            "--fixture-url", url, "--manifest-digest", digest,
            "--termination-grace-seconds", ".15", *extra]


@contextmanager
def registry(blobs):
    requests_seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests_seen.append(self.path)
            body = blobs.get(self.path.lstrip("/"))
            if body is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests_seen
    finally:
        server.shutdown()
        server.server_close()
        worker.join(2)


class Units(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="streamed-test-")
        self.root = Path(self.tmp.name)
        self.space = self.root / "space.json"
        write_space(self.space)
        self.guard = HostSpaceGuard(self.space)
        self.pins, self.blobs, self.expected = package(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def disk(self, cache=2):
        source = oci.LayerSource(self.pins, MemoryBlobs(self.blobs), cache_layers=cache)
        return RawDisk(source, planner.make_plan(source), self.guard)

    def test_oracle_all_bytes_and_physical_order(self):
        d = self.disk()
        self.assertEqual(d.read_at(0, d.size), self.expected)
        self.assertNotEqual([e.target for e in d.plan.extents], sorted(e.target for e in d.plan.extents))
        self.assertEqual(d.starts, sorted(d.starts))

    def test_partial_sectors_holes_and_truncated_tail(self):
        d = self.disk()
        for offset, count in [(CS - 9, CS + 40), (2 * CS, 8 * BS),
                              (3 * CS, CS), (5 * CS, 3 * BS), (d.size, 0)]:
            self.assertEqual(d.read_at(offset, count), self.expected[offset:offset + count])

    def test_misaligned_oci_layer_boundary(self):
        d = self.disk()
        # Physical 6*CS crosses the OCI boundary at 3*65537, just three bytes in.
        self.assertEqual(d.read_at(4 * CS, 17), b"B" * 17)

    def test_seeded_random_ranges(self):
        d, rng = self.disk(), random.Random(735)
        for _ in range(200):
            a = rng.randrange(d.size + 1)
            n = rng.randrange(min(d.size - a, 12000) + 1)
            self.assertEqual(d.read_at(a, n), self.expected[a:a + n])

    def test_read_bounds_and_32_mib_limit(self):
        d = self.disk()
        for a, n in [(-1, 1), (0, -1), (d.size, 1), (d.size + 1, 0),
                     (0, MAX_READ + 1), (False, 1), (1, True)]:
            with self.subTest(a=a, n=n), self.assertRaises(oci.ConversionError):
                d.read_at(a, n)

    def test_cache_is_one_or_two_layers(self):
        for limit in (1, 2):
            d = self.disk(limit)
            self.assertEqual(d.read_at(0, d.size), self.expected)
            self.assertLessEqual(len(d.source.cache), limit)
            self.assertLessEqual(d.source.peak_cache_bytes, limit * 65537)

    def test_corrupt_layer_returns_no_bytes(self):
        d = self.disk()
        d.source.clear_cache()
        i = d.source.layer_at(7 * CS)
        key = self.pins.layers[i].digest[7:]
        bad = bytearray(self.blobs[key])
        bad[10] ^= 1
        self.blobs[key] = bytes(bad)
        with self.assertRaises(oci.ConversionError):
            d.read_at(0, 512)
        self.assertNotIn(i, d.source.cache)

    def test_reject_logical_overlap(self):
        d = self.disk()
        e = d.plan.extents[0]
        d.plan.extents.append(planner.Extent(e.source + 1, e.target, 1))
        d.plan.extents.sort(key=lambda x: x.source)
        with self.assertRaises(oci.ConversionError):
            RawDisk(d.source, d.plan, self.guard)

    def test_guard_low_space_even_for_zero_hole(self):
        d = self.disk()
        write_space(self.space, RESERVE - 1)
        with self.assertRaises(GuardError):
            d.read_at(CS, 512)

    def test_guard_exact_threshold_and_age(self):
        write_space(self.space, RESERVE, 100)
        HostSpaceGuard(self.space, now=lambda: 120).check()
        with self.assertRaises(GuardError):
            HostSpaceGuard(self.space, now=lambda: 120.001).check()

    def test_guard_missing_malformed_wrong_drive_future(self):
        for content in ["{}", "oops", json.dumps({"drive": "D:\\", "free_bytes": RESERVE,
                      "observed_at": time.time()}), json.dumps({"drive": "C:\\", "free_bytes": True,
                      "observed_at": time.time()}), json.dumps({"drive": "C:\\", "free_bytes": RESERVE,
                      "observed_at": time.time() + 30}), "x" * 4097]:
            self.space.write_text(content)
            with self.assertRaises(GuardError):
                self.guard.check()
        self.space.unlink()
        with self.assertRaises(GuardError):
            self.guard.check()

    def test_guard_stream_before_and_after_read_and_deadline(self):
        raw = io.BytesIO(b"abc")
        stream = CheckedStream(raw, self.guard, time.monotonic() + 10)
        write_space(self.space, RESERVE - 1)
        with self.assertRaises(GuardError):
            stream.read(1)
        self.assertEqual(raw.tell(), 0)
        write_space(self.space)
        with self.assertRaises(TimeoutError):
            CheckedStream(raw, self.guard, time.monotonic() - 1).read(1)

    def test_verified_telemetry_only_after_success(self):
        events = []
        source = VerifiedSource(self.pins, MemoryBlobs(self.blobs), guard=self.guard,
                                report=lambda event, **fields: events.append((event, fields)))
        source.get_layer(0)
        source.get_layer(0)
        self.assertEqual([e[0] for e in events], ["layer_fetch_start", "layer_verified"])
        self.assertEqual(source.fetch_count, 1)

    def test_http_initialization_and_no_payload_files(self):
        with registry(self.blobs) as (url, requests_seen):
            options = {"manifest": str(self.root / "manifest.json"),
                       "config": str(self.root / "config.json"), "host-space": str(self.space),
                       "manifest-digest": self.pins.manifest_digest, "fixture-url": url}
            d = initialize(options)
            self.assertEqual(d.read_at(0, d.size), self.expected)
            self.assertGreater(len(requests_seen), 0)
            d.close()
        self.assertEqual({p.name for p in self.root.iterdir()},
                         {"manifest.json", "config.json", "space.json"})


class RealNBD(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="streamed-nbd-")
        self.root = Path(self.tmp.name)
        self.pins, self.blobs, self.expected = package(self.root)
        self.space = self.root / "space.json"
        write_space(self.space)
        self.proc = None

    def tearDown(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(5)
        if hasattr(self, "log"):
            self.log.close()
        self.tmp.cleanup()

    def start(self, url, bad_digest=False):
        self.socket = self.root / "disk.sock"
        self.log_path = self.root / "server.log"
        self.log = self.log_path.open("w")
        command = fixture_command(self.root, self.space, url,
                                  oci.sha256(b"wrong") if bad_digest else self.pins.manifest_digest)
        self.proc = subprocess.Popen(command, stdout=self.log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            content = self.log_path.read_text()
            if '"event": "export_ready"' in content:
                return
            if self.proc.poll() is not None:
                if bad_digest:
                    return
                self.fail("nbdkit failed before ready: " + content)
            time.sleep(.02)
        self.fail("nbdkit export-ready timeout (15 seconds): " + self.log_path.read_text())

    def test_real_nbd_reads_writes_bounds_reconnects_concurrent_and_no_cache(self):
        with registry(self.blobs) as (url, seen):
            self.start(url)
            with NBDSource(self.socket) as source:
                self.assertEqual(source.getsize(), len(self.expected))
                self.assertEqual(source.read_at(0, source.size), self.expected)
                for a, n in [(CS - 3, CS + 20), (4 * CS - 3, 18), (2 * CS, 8 * BS),
                             (5 * CS, 3 * BS), (source.size - 1, 5), (source.size, 1)]:
                    self.assertEqual(source.read_at(a, n), self.expected[a:a + n])
                with self.assertRaises(Exception):
                    source.read_exact(source.size - 1, 2)
                # The adapter is an actual fs-explorer RandomAccess, not duck typing.
                from fs_explorer import open_source
                with open_source(source, backend="pure", threads=1, spool_limit=0) as fs:
                    self.assertIs(fs._phys, source)
            with self.assertRaises(ValueError):
                source.read_at(0, 1)
            def check_connection(seed):
                rng = random.Random(seed)
                with NBDSource(self.socket) as peer:
                    for _ in range(40):
                        a = rng.randrange(peer.size)
                        n = min(4096, peer.size - a)
                        if peer.read_at(a, n) != self.expected[a:a + n]:
                            raise AssertionError("concurrent byte mismatch")
            with ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(check_connection, [17, 29]))
            handle = nbd.NBD()
            handle.set_strict_mode(0)  # Force commands to the server for rejection.
            handle.connect_unix(str(self.socket))
            self.assertTrue(handle.is_read_only())
            rejected = []
            for data, offset in [(b"Z" * BS, 0), (b"Z" * BS, len(self.expected))]:
                with self.assertRaises(nbd.Error) as caught:
                    handle.pwrite(data, offset)
                rejected.append({"operation": "write", "offset": offset, "error": str(caught.exception)})
            with self.assertRaises(nbd.Error) as caught:
                handle.pread(BS, len(self.expected))
            rejected.append({"operation": "read", "offset": len(self.expected), "error": str(caught.exception)})
            self.assertEqual(handle.pread(BS, 0), b"A" * BS)
            handle.shutdown()
            del handle
            content = self.log_path.read_text()
            self.assertEqual(content.count('"event": "plan_start"'), 1)
            self.assertEqual(content.count('"event": "export_ready"'), 1)
            self.assertIn('"readonly": true', content)
            self.assertGreater(len(seen), 0)
            self.assertEqual({p.name for p in self.root.iterdir()},
                             {"manifest.json", "config.json", "space.json", "server.log", "disk.sock"})
            artifacts = Path(os.environ.get("ARTIFACT_DIR", "/tmp"))
            (artifacts / "offline-nbd-telemetry.jsonl").write_text(content)
            (artifacts / "offline-oracle.json").write_text(json.dumps({
                "raw_bytes": len(self.expected), "oracle_sha256": hashlib.sha256(self.expected).hexdigest(),
                "network": "Docker --network none; in-memory loopback fixture only",
                "whole_disk_match": True, "two_concurrent_connections_match": True,
                "libnbd_strict_mode": 0, "server_received_invalid_writes": True,
                "rejections": rejected, "no_payload_cache_files": True}, indent=2) + "\n")

    def test_idle_guard_low_space_stops_server(self):
        with registry(self.blobs) as (url, seen):
            self.start(url)
            write_space(self.space, RESERVE - 1)
            self.assertNotEqual(self.proc.wait(3), 0)
            self.assertIn('"event": "guard_stop"', self.log_path.read_text())

    def test_idle_guard_stale_stops_server(self):
        with registry(self.blobs) as (url, seen):
            self.start(url)
            write_space(self.space, observed=time.time() - 21)
            self.assertNotEqual(self.proc.wait(3), 0)

    def test_bad_manifest_fails_before_http(self):
        with registry(self.blobs) as (url, seen):
            self.start(url, bad_digest=True)
            self.assertNotEqual(self.proc.wait(3), 0)
            self.assertEqual(seen, [])
            self.assertNotIn('"event": "export_ready"', self.log_path.read_text())


if __name__ == "__main__":
    os.environ["STREAMED_DISK_TEST_MODE"] = "1"
    signal.alarm(90)  # Hard bound for offline test subprocess/network regressions.
    (Path(os.environ.get("ARTIFACT_DIR", "/tmp")) / "offline-cancellation-telemetry.jsonl").write_text("")
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    sys.modules.setdefault("test_streamed_disk", sys.modules[__name__])
    suite.addTests(unittest.defaultTestLoader.loadTestsFromName("test_cancellation"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "skips": len(result.skipped), "successful": result.wasSuccessful(),
              "live_guest_network_run": False, "vm_run": False}
    output = Path(os.environ.get("ARTIFACT_DIR", "/tmp")) / "test-results.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(0 if result.wasSuccessful() else 1)
