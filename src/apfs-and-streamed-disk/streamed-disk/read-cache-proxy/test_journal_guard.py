"""Regression for SQLite DELETE-journal unlink versus the independent guard."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

from common import Guard, Refused


class JournalGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='journal-guard-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cache = self.root / 'cache'
        self.cache.mkdir()
        self.sample = self.root / 'sample.json'
        self.sample.write_text(json.dumps({'drive': 'C:', 'free_bytes': 30 * 1024**3,
                                           'observed_at': time.time()}))
        self.guard = Guard(self.sample, self.cache)
        for name in ('cache.lock', 'blocks.bin', 'index.sqlite3'):
            (self.cache / name).touch()
        self.journal = self.cache / 'index.sqlite3-journal'
        self.journal.write_bytes(b'J' * 4096)

    def test_journal_unlinked_between_listing_and_stat_is_absent(self):
        real = Path.lstat
        def changed(path, *args, **kwargs):
            if path == self.journal:
                self.journal.unlink()
            return real(path, *args, **kwargs)
        with mock.patch.object(Path, 'lstat', changed):
            self.assertEqual(self.guard.check()['logical_bytes'], 0)

    def zero_link(self, path, real):
        s = real(path)
        return types.SimpleNamespace(st_mode=s.st_mode, st_nlink=0,
                                     st_size=s.st_size, st_blocks=s.st_blocks)

    def test_unlinked_regular_journal_is_still_counted(self):
        real = Path.lstat
        def changed(path, *args, **kwargs):
            return self.zero_link(path, real) if path == self.journal else real(path, *args, **kwargs)
        with mock.patch.object(Path, 'lstat', changed):
            result = self.guard.check()
            self.assertEqual(result['logical_bytes'], 4096)
            self.assertGreaterEqual(result['allocated_bytes'], 4096)

    def test_zero_link_journal_cannot_bypass_disk_limit(self):
        real = Path.lstat
        def changed(path, *args, **kwargs):
            return self.zero_link(path, real) if path == self.journal else real(path, *args, **kwargs)
        with mock.patch.object(Path, 'lstat', changed), self.assertRaisesRegex(Refused, 'disk budget'):
            Guard(self.sample, self.cache, disk_limit=4095).check()

    def test_listed_persistent_entry_disappearing_still_fails(self):
        real = Path.lstat
        for name in ('blocks.bin', 'index.sqlite3', 'cache.lock'):
            target = self.cache / name
            target.touch()
            def changed(path, *args, **kwargs):
                if path == target:
                    target.unlink()
                return real(path, *args, **kwargs)
            with self.subTest(name=name), mock.patch.object(Path, 'lstat', changed):
                with self.assertRaises(FileNotFoundError):
                    self.guard.check()

    def test_zero_link_persistent_entries_still_fail(self):
        real = Path.lstat
        for name in ('blocks.bin', 'index.sqlite3', 'cache.lock'):
            target = self.cache / name
            def changed(path, *args, **kwargs):
                return self.zero_link(path, real) if path == target else real(path, *args, **kwargs)
            with self.subTest(name=name), mock.patch.object(Path, 'lstat', changed):
                with self.assertRaisesRegex(Refused, 'unsafe cache file'):
                    self.guard.check()

    def test_journal_symlink_and_multiple_links_still_fail(self):
        peer = self.root / 'outside'
        peer.write_bytes(b'X')
        self.journal.unlink()
        self.journal.symlink_to(peer)
        with self.assertRaisesRegex(Refused, 'unsafe cache file'):
            self.guard.check()
        self.journal.unlink()
        self.journal.hardlink_to(peer)
        with self.assertRaisesRegex(Refused, 'unsafe cache file'):
            self.guard.check()

    def test_unknown_file_is_not_treated_as_a_journal(self):
        (self.cache / 'index.sqlite3-journal-extra').touch()
        with self.assertRaises(Refused):
            self.guard.check()

    def test_parent_replacement_during_journal_unlink_is_refused(self):
        # Isolate the final directory-identity check. Otherwise a different
        # listed persistent file can legitimately fail first with ENOENT.
        for name in ('cache.lock', 'blocks.bin', 'index.sqlite3'):
            (self.cache / name).unlink()
        real = Path.lstat
        def changed(path, *args, **kwargs):
            if path == self.journal:
                self.cache.rename(self.root / 'old-cache')
                self.cache.mkdir()
                raise FileNotFoundError(str(path))
            return real(path, *args, **kwargs)
        with mock.patch.object(Path, 'lstat', changed), self.assertRaisesRegex(Refused, 'directory changed'):
            self.guard.check()

    def test_parent_removal_during_journal_unlink_is_refused(self):
        real = Path.lstat
        def changed(path, *args, **kwargs):
            if path == self.journal:
                self.cache.rename(self.root / 'old-cache')
                raise FileNotFoundError(str(path))
            return real(path, *args, **kwargs)
        with mock.patch.object(Path, 'lstat', changed), self.assertRaises(FileNotFoundError):
            self.guard.check()

    def test_actual_sqlite_delete_journal_churn(self):
        # The supplied reproduction uses a separate writer process and the exact
        # production guard; it runs only in this fresh offline container's tmpfs.
        script = '/parent/full-system/warm-cache-boot/live/recovered-replay/journal_race_repro.py'
        child = subprocess.run([sys.executable, '-B', script], capture_output=True,
                               text=True, timeout=15, check=True)
        result = json.loads(child.stdout)
        self.assertEqual(result['writer_wait_status'], 0)
        self.assertGreater(result['writer_commits'], 100)
        self.assertGreater(result['guard_checks'], 100)
        self.assertEqual(result['errors'], {})


if __name__ == '__main__':
    unittest.main()
