"""Tiny, offline Apple-LZ4 cache/resource tests; no Golden bytes or RAM stress."""
from dataclasses import replace
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from frozen import oci
import streamed_raw
from streamed_raw import HostSpaceGuard, VerifiedSource, initialize
from test_streamed_disk import MemoryBlobs, fixture_command, registry, write_space
from tiny_fixture import apple_stream, package

GIB = 1 << 30
EVIDENCE = {}


def layers_fixture(count=10):
    """Each layer has independent content and both real pinned SHA256 values."""
    payloads = [bytes([i]) * 16384 + bytes(range(256)) for i in range(count)]
    blobs, layers, offset = {}, [], 0
    for payload in payloads:
        packed = apple_stream(payload)
        digest = oci.sha256(packed)
        blobs[digest[7:]] = packed
        layers.append(oci.Layer(digest, len(packed), len(payload), oci.sha256(payload), offset))
        offset += len(payload)
    return oci.Pins(oci.sha256(b"fixture-manifest"), oci.sha256(b"fixture-config"), tuple(layers)), blobs, payloads


class LargeCache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="large-cache-")
        self.root = Path(self.tmp.name)
        self.space = self.root / "space.json"
        write_space(self.space)
        self.guard = HostSpaceGuard(self.space)
        self.pins, self.data, self.payloads = layers_fixture()
        self.blobs = MemoryBlobs(self.data)

    def tearDown(self):
        self.tmp.cleanup()

    def source(self, count=8, pins=None):
        return VerifiedSource(pins or self.pins, self.blobs, cache_layers=count,
                              guard=self.guard, report=lambda *a, **k: None)

    def test_eight_resident_hits_and_ninth_evicts_only_lru(self):
        source = self.source()
        for i in range(8):
            self.assertEqual(source.get_layer(i), self.payloads[i])
        self.assertEqual(self.blobs.calls, 8)
        # Progressing 4KiB reads touch each layer, keeping all eight resident.
        for _ in range(3):
            for i in range(8):
                self.assertEqual(source.read_at(self.pins.layers[i].offset + 123, 4096),
                                 self.payloads[i][123:123 + 4096])
        self.assertEqual(self.blobs.calls, 8)
        self.assertEqual(list(source.cache), list(range(8)))
        source.get_layer(0)  # 1 is now least recently used.
        self.assertEqual(source.get_layer(8), self.payloads[8])
        self.assertEqual(self.blobs.calls, 9)
        self.assertEqual(list(source.cache), [2, 3, 4, 5, 6, 7, 0, 8])
        for i in list(source.cache):
            source.get_layer(i)
        self.assertEqual(self.blobs.calls, 9)
        source.get_layer(1)
        self.assertEqual(self.blobs.calls, 10)
        self.assertNotIn(2, source.cache)
        self.assertEqual(len(source.cache), 8)
        self.assertLessEqual(source.peak_cache_bytes, 8 * len(self.payloads[0]))
        self.assertEqual({p.name for p in self.root.iterdir()}, {"space.json"})
        EVIDENCE["lru"] = {"resident_hits_fetch_count": 8, "after_ninth_layer": 9,
                           "after_evicted_layer_refetch": 10, "resident_layers": 8,
                           "peak_payload_cache_bytes": source.peak_cache_bytes,
                           "no_payload_files": True}

    def test_all_capacities_one_through_eight(self):
        for count in range(1, 9):
            with self.subTest(count=count):
                source = self.source(count)
                for i in range(10):
                    self.assertEqual(source.get_layer(i), self.payloads[i])
                    self.assertLessEqual(len(source.cache), count)
                self.assertEqual(list(source.cache), list(range(10 - count, 10)))

    def test_invalid_adapter_counts_fail_before_base_and_fetch(self):
        for count in (0, 9, -1, True, False, 2.0, 8.0, "8", None):
            with self.subTest(count=count), patch.object(oci.LayerSource, "__init__") as base:
                with self.assertRaises(oci.ConversionError):
                    self.source(count)
                base.assert_not_called()
        self.assertEqual(self.blobs.calls, 0)

    def test_budget_refusals_before_base_allocation_or_fetch(self):
        for limit in ("max", "", "0", "-1", "6GiB", "nan", str(6 * GIB - 1)):
            with self.subTest(limit=limit), patch.object(Path, "read_text", return_value=limit), \
                    patch.object(oci.LayerSource, "__init__") as base:
                with self.assertRaises(streamed_raw.CacheBudgetError):
                    self.source()
                base.assert_not_called()
        for error in (FileNotFoundError(), PermissionError(), UnicodeError()):
            with self.subTest(error=type(error).__name__), \
                    patch.object(Path, "read_text", side_effect=error), \
                    patch.object(oci.LayerSource, "__init__") as base:
                with self.assertRaises(streamed_raw.CacheBudgetError):
                    self.source()
                base.assert_not_called()
        self.assertEqual(self.blobs.calls, 0)

    def test_admission_threshold_for_every_extended_capacity(self):
        for count in range(3, 9):
            required = count * oci.MAX_LAYER + 2 * GIB
            with self.subTest(count=count), patch.object(Path, "read_text", return_value=str(required)) as read:
                source = self.source(count)
                self.assertEqual(source.cache_layers, count)
                self.assertEqual(source.cache_memory_limit, required)
                read.assert_called_once_with(encoding="ascii")
            with patch.object(Path, "read_text", return_value=str(required - 1)):
                with self.assertRaises(streamed_raw.CacheBudgetError):
                    self.source(count)

    def test_default_and_legacy_capacities_do_not_require_cgroup(self):
        with patch.object(Path, "read_text", side_effect=AssertionError("legacy must not read cgroup")):
            for count in (1, 2):
                self.assertEqual(self.source(count).cache_layers, count)
            source = VerifiedSource(self.pins, self.blobs, guard=self.guard)
            self.assertEqual(source.cache_layers, 2)
            self.assertIsNone(source.cache_memory_limit)

    def test_bad_compressed_hash_cannot_commit(self):
        damaged = bytearray(self.data[self.pins.layers[0].digest[7:]])
        damaged[10] ^= 1  # Valid raw frame, same size; both hashes disagree.
        self.data[self.pins.layers[0].digest[7:]] = bytes(damaged)
        source = self.source()
        with self.assertRaises(RuntimeError):
            source.get_layer(0)
        self.assertNotIn(0, source.cache)
        self.assertNotIn(0, source.verified)
        self.assertEqual(source.fetch_count, 1)

    def test_bad_raw_hash_cannot_commit_with_valid_compressed_hash(self):
        layer = replace(self.pins.layers[0], raw_digest=oci.sha256(b"wrong raw content"))
        source = self.source(pins=replace(self.pins, layers=(layer, *self.pins.layers[1:])))
        with self.assertRaises(RuntimeError):
            source.get_layer(0)
        self.assertNotIn(0, source.cache)
        self.assertNotIn(0, source.verified)

    def test_failed_ninth_layer_never_commits_and_retained_hits_stay_verified(self):
        source = self.source()
        for i in range(8):
            source.get_layer(i)
        key = self.pins.layers[8].digest[7:]
        self.data[key] = self.data[key][:-1]
        with self.assertRaises(RuntimeError):
            source.get_layer(8)
        self.assertNotIn(8, source.cache)
        self.assertNotIn(8, source.verified)
        self.assertEqual(list(source.cache), list(range(1, 8)))
        for i in list(source.cache):
            self.assertEqual(source.get_layer(i), self.payloads[i])
        self.assertEqual(self.blobs.calls, 9)

    def test_verified_hits_still_check_host_guard(self):
        source = self.source()
        source.get_layer(0)
        write_space(self.space, streamed_raw.RESERVE - 1)
        with self.assertRaises(streamed_raw.GuardError):
            source.get_layer(0)
        self.assertEqual(self.blobs.calls, 1)

    def test_initialize_rejects_budget_before_any_http(self):
        pins, blobs, _ = package(self.root)
        with registry(blobs) as (url, seen), patch.object(streamed_raw, "cgroup_memory_limit", return_value=6 * GIB - 1):
            with self.assertRaises(streamed_raw.CacheBudgetError):
                initialize({"manifest": str(self.root / "manifest.json"),
                            "config": str(self.root / "config.json"), "host-space": str(self.space),
                            "manifest-digest": pins.manifest_digest, "fixture-url": url, "cache-layers": "8"})
            self.assertEqual(seen, [])

    def test_plugin_accepts_one_to_eight_and_rejects_noncanonical_counts(self):
        import importlib.util
        import types
        with patch.dict(sys.modules, {"nbdkit": types.ModuleType("nbdkit")}):
            spec = importlib.util.spec_from_file_location("large_cache_plugin", Path(__file__).with_name("nbdkit_streamed.py"))
            plugin = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin)
        for count in [None, *map(str, range(1, 9)), "0", "9", "True", "8.0", "08", "+8", " 8"]:
            plugin.OPTIONS = {"manifest": "unused", "config": "unused", "host-space": "unused"}
            if count is not None:
                plugin.OPTIONS["cache-layers"] = count
            with patch.object(plugin.ChildControl, "from_environment", return_value=object()) as control:
                if count is None or count in tuple(map(str, range(1, 9))):
                    plugin.config_complete()
                    control.assert_called_once()
                else:
                    with self.assertRaises(ValueError):
                        plugin.config_complete()
                    control.assert_not_called()

    def test_cli_eight_layer_real_readonly_nbd(self):
        import nbd
        pins, blobs, expected = package(self.root)
        log = self.root / "server.log"
        with registry(blobs) as (url, seen), log.open("w") as output:
            process = subprocess.Popen(fixture_command(self.root, self.space, url, pins.manifest_digest,
                                       ["--cache-layers", "8"]), stdout=output, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 10
                while '"event": "export_ready"' not in log.read_text():
                    self.assertIsNone(process.poll(), log.read_text())
                    self.assertLess(time.monotonic(), deadline, log.read_text())
                    time.sleep(.02)
                handle = nbd.NBD()
                try:
                    handle.connect_unix(str(self.root / "disk.sock"))
                    self.assertTrue(handle.is_read_only())
                    self.assertEqual(handle.pread(len(expected), 0), expected)
                    count = len(seen)
                    self.assertEqual(handle.pread(len(expected), 0), expected)
                    self.assertEqual(len(seen), count)
                finally:
                    handle.shutdown()
                self.assertIn('"cache_layers": 8', log.read_text())
                self.assertIn('"memory_limit_bytes": 6442450944', log.read_text())
            finally:
                process.terminate()
                process.wait(7)

    def test_cli_invalid_counts_fail_without_launch(self):
        for count in ("0", "9", "True", "8.0"):
            result = subprocess.run([sys.executable, "serve.py", "--socket", "/tmp/unused-large.sock",
                                     "--manifest", "missing", "--config", "missing", "--host-space", "missing",
                                     "--cache-layers", count], capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("supervisor_started", result.stderr)


if __name__ == "__main__":
    os.environ["STREAMED_DISK_TEST_MODE"] = "1"
    signal.alarm(60)
    # A 6GiB cgroup ceiling is admission metadata, not a stress allocation.
    # Bound this runner and inherited test subprocess address spaces to 512MiB.
    resource.setrlimit(resource.RLIMIT_AS, (512 << 20, 512 << 20))
    limit = streamed_raw.cgroup_memory_limit()
    if limit != 6 * GIB:
        raise SystemExit("run this small-fixture suite in Docker --memory 6g")
    started = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LargeCache))
    peak_kib = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    memory_peak = int(Path("/sys/fs/cgroup/memory.peak").read_text().strip())
    within_memory_bound = memory_peak <= GIB
    report = {"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "skips": len(result.skipped), "successful": result.wasSuccessful(),
              "seconds": round(time.monotonic() - started, 3), "cgroup_memory_limit_bytes": limit,
              "memory_peak_bytes": memory_peak, "within_1gib_actual_memory_bound": within_memory_bound,
              "per_process_address_space_limit_bytes": 512 << 20,
              "max_process_peak_rss_kib": peak_kib, "network": "none; synthetic loopback only", **EVIDENCE}
    Path(os.environ.get("ARTIFACT_DIR", "/tmp"), "large-cache-tests.json").write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(0 if result.wasSuccessful() and within_memory_bound else 1)
