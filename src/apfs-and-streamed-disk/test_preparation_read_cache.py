import hashlib
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import time
import unittest
import plistlib

from preparation_read_cache import ReadCacheSource


class Oracle:
    def __init__(self, data=b'known verified bytes'):
        self.data, self.calls, self.closed = data, 0, False
    def getsize(self):
        return len(self.data)
    def read_at(self, offset, count):
        self.calls += 1
        return self.data[offset:offset + count]
    def close(self):
        self.closed = True


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checks = 0
    def guard(self):
        self.checks += 1
    def open(self, source=None, identity=None, **kwargs):
        source = source or Oracle()
        cache = ReadCacheSource(source, self.root, identity or {'manifest': 'pin'}, self.guard, **kwargs)
        self.addCleanup(cache.close)
        return cache
    def test_restart_replays_exact_bytes_without_source_read(self):
        first = self.open()
        expected = first.read_at(1, 8)
        self.assertEqual(first.source.calls, 1)
        first.close()
        second = self.open()
        self.assertEqual(second.read_at(1, 8), expected)
        self.assertEqual(second.source.calls, 0)
        self.assertGreaterEqual(self.checks, 7)
    def test_different_pins_do_not_reuse_bytes(self):
        self.open().read_at(0, 5)
        other = self.open(Oracle(b'other verified data!'), {'manifest': 'different'})
        self.assertEqual(other.read_at(0, 5), b'other')
        self.assertEqual(other.source.calls, 1)
    def test_corrupt_cache_fails_closed(self):
        cache = self.open()
        cache.read_at(0, 5)
        cache.db.execute('UPDATE reads SET data=?', (b'wrong',))
        cache.db.commit()
        with self.assertRaisesRegex(ValueError, 'digest'):
            cache.read_at(0, 5)
        self.assertEqual(cache.source.calls, 1)
    def test_guard_is_checked_on_hits(self):
        cache = self.open()
        cache.read_at(0, 5)
        def denied():
            raise RuntimeError('low/stale sample')
        cache.guard = denied
        with self.assertRaisesRegex(RuntimeError, 'low/stale'):
            cache.read_at(0, 5)
    def test_cache_budget_full_does_not_change_verified_read(self):
        data = bytes(range(256)) * 512
        cache = self.open(Oracle(data), database_bytes=16384)
        self.assertEqual(cache.read_at(0, len(data)), data)
        self.assertFalse(cache.writes_enabled)
        self.assertLessEqual(next(self.root.glob('*.sqlite3')).stat().st_size, 16384)
    def test_eof_and_invalid_reads(self):
        cache = self.open()
        self.assertEqual(cache.read_at(18, 100), b'es')
        self.assertEqual(cache.read_at(18, 100), b'es')
        self.assertEqual(cache.read_at(100, 100), b'')
        self.assertEqual(cache.read_at(1 << 64, 100), b'')
        for off, count in [(-1, 1), (0, -1), (0, 33554433), (True, 2)]:
            with self.assertRaises(ValueError):
                cache.read_at(off, count)
    def test_large_items_are_not_retained(self):
        cache = self.open(Oracle(bytes((1 << 20) + 1)))
        cache.read_at(0, (1 << 20) + 1)
        self.assertEqual(cache.db.execute('SELECT count(*) FROM reads').fetchone()[0], 0)
    def test_entry_budget_and_closed_source(self):
        cache = self.open(Oracle(bytes(range(256)) * 4))
        for off in range(513):
            cache.read_at(off, 1)
        self.assertEqual(cache.db.execute('SELECT count(*) FROM reads').fetchone()[0], 512)
        cache.close()
        with self.assertRaisesRegex(ValueError, 'closed'):
            cache.read_at(0, 1)
    def test_budget_cannot_be_relaxed(self):
        for value in (0, (32 << 20) + 4096):
            with self.assertRaises(ValueError):
                self.open(database_bytes=value)

    @unittest.skipUnless(Path('/parent/darwin/firmware/ramdisk.dmg').exists(), 'Existing local restore fixture')
    def test_real_apfs_over_nbd_replays_without_new_payload_reads(self):
        import fs_explorer as fs
        from nbd_source import NBDSource
        socket = self.root / 'oracle.sock'
        server = subprocess.Popen(['nbdkit', '-f', '-r', '-U', str(socket), 'file',
                                   '/parent/darwin/firmware/ramdisk.dmg'],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 3
            while not socket.exists():
                if server.poll() is not None or time.monotonic() > deadline:
                    self.fail('Local read-only NBD fixture did not start')
                time.sleep(.01)
            class ReplayOnly(NBDSource):
                def read_at(self, *args):
                    raise AssertionError('A cached APFS replay requested fresh payload bytes')
            for source_type in (NBDSource, ReplayOnly):
                with ReadCacheSource(source_type(socket), self.root / 'real-cache',
                                     {'fixture': 'restore-26A434'}, self.guard) as source:
                    with fs.open_source(source, backend='pure', threads=1, system_files=True) as image:
                        version = plistlib.loads(image.read_file('/System/Library/CoreServices/SystemVersion.plist'))
                        self.assertEqual(version['ProductVersion'], '27.0.1')
                        self.assertEqual(version['ProductBuildVersion'], '26A434')
        finally:
            server.terminate()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=2)
            server.stderr.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
