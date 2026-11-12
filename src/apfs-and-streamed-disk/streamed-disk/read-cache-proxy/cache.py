"""Durable returned-block cache; no source decoding or upstream trust changes."""
import fcntl
import hashlib
import os
from pathlib import Path
import sqlite3
import stat
import struct
import threading
from functools import wraps

from common import BLOCK, MAX_READ, DATA_LIMIT, MAX_BLOCKS, require, check_directory


def synchronized(function):
    @wraps(function)
    def call(self, *args, **kwargs):
        with self._lock:
            return function(self, *args, **kwargs)
    return call


class BlockCache:
    def __init__(self, folder, source_id, size, guard, data_limit=DATA_LIMIT):
        self.folder = check_directory(folder)
        self._lock = threading.RLock()
        self.source_id, self.size, self.guard = source_id, size, guard
        require(len(source_id) == 32 and type(size) is int and size > 0, 'invalid cache identity')
        require(type(data_limit) is int and BLOCK <= data_limit <= DATA_LIMIT and
                data_limit % BLOCK == 0, 'invalid data limit')
        self.max_blocks = data_limit // BLOCK
        self.lock_fd = self.data_fd = self.db = None
        self.hits = self.misses = self.upstream_calls = 0
        self.failed = False
        try:
            guard.check()
            self.lock_fd = self.open_file('cache.lock')
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            db_path = self.folder / 'index.sqlite3'
            existed = db_path.exists()
            if existed:
                s = db_path.lstat()
                require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_size > 0,
                        'invalid cache index')
            elif (self.folder / 'blocks.bin').exists():
                require((self.folder / 'blocks.bin').stat().st_size == 0, 'payload without identity index')
            self.db = sqlite3.connect(str(db_path), isolation_level=None, timeout=1, check_same_thread=False)
            os.chmod(db_path, 0o600)
            self.db.execute('PRAGMA page_size=4096')
            self.db.execute('PRAGMA journal_mode=DELETE')
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.execute('PRAGMA temp_store=MEMORY')
            self.db.execute('PRAGMA cache_size=-8192')
            self.db.execute('PRAGMA mmap_size=0')
            self.db.execute('PRAGMA max_page_count=16384')  # index <=64 MiB
            if not existed:
                self.db.execute('BEGIN IMMEDIATE')
                self.db.execute('CREATE TABLE identity (id INTEGER PRIMARY KEY CHECK(id=1), source BLOB NOT NULL, size INTEGER NOT NULL, block INTEGER NOT NULL)')
                self.db.execute('CREATE TABLE blocks (off INTEGER PRIMARY KEY, slot INTEGER UNIQUE NOT NULL, n INTEGER NOT NULL, digest BLOB NOT NULL)')
                self.db.execute('INSERT INTO identity VALUES (1,?,?,?)', (source_id, size, BLOCK))
                self.db.execute('COMMIT')
            require(self.db.execute('PRAGMA quick_check').fetchall() == [('ok',)], 'corrupt cache index')
            require(self.db.execute('SELECT * FROM identity').fetchall() == [(1, source_id, size, BLOCK)],
                    'cache identity changed')
            count, minimum, maximum = self.db.execute('SELECT count(*),min(slot),max(slot) FROM blocks').fetchone()
            require(0 <= count <= self.max_blocks and (count == 0 or (minimum == 0 and maximum == count-1)),
                    'invalid cache slots/count')
            for off, slot, n, digest in self.db.execute('SELECT off,slot,n,digest FROM blocks'):
                require(type(off) is int and 0 <= off < size and off % BLOCK == 0 and
                        type(slot) is int and 0 <= slot < count and n == min(BLOCK, size-off) and
                        isinstance(digest, bytes) and len(digest) == 32, 'invalid cache record')
            self.count = count
            self.data_fd = self.open_file('blocks.bin')
            require(count * BLOCK <= os.fstat(self.data_fd).st_size <= DATA_LIMIT + MAX_READ,
                    'truncated or excessive cache payload')
            # Only unindexed suffixes from an interrupted, never-committed batch
            # are discarded. Dense committed slots were checked above.
            os.ftruncate(self.data_fd, count * BLOCK)
            os.fsync(self.data_fd)
            directory = os.open(self.folder, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            guard.check()
        except BaseException:
            self.close()
            raise

    def open_file(self, name):
        fd = os.open(self.folder / name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        s = os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, 'unsafe cache file')
        return fd

    def digest(self, off, n, data):
        return hashlib.sha256(self.source_id + struct.pack('>QQ', off, n) + data).digest()

    @synchronized
    def get(self, off):
        row = self.db.execute('SELECT slot,n,digest FROM blocks WHERE off=?', (off,)).fetchone()
        if row is None:
            self.misses += 1
            return None
        slot, n, digest = row
        require(type(slot) is int and 0 <= slot < self.count and n == min(BLOCK, self.size-off) and
                isinstance(digest, bytes) and len(digest) == 32, 'invalid cached record')
        data = os.pread(self.data_fd, BLOCK, slot * BLOCK)
        require(len(data) == BLOCK and data[n:] == bytes(BLOCK-n) and
                self.digest(off, n, data) == digest, 'cached block hash mismatch')
        self.hits += 1
        return data[:n]

    @synchronized
    def put_batch(self, records, after_payload_sync=lambda: None):
        selected = records[:max(0, self.max_blocks-self.count)]
        if not selected:
            return
        self.guard.check()
        original_count = self.count
        try:
            self.db.execute('BEGIN IMMEDIATE')
            rows = []
            for i, (off, payload) in enumerate(selected):
                self.guard.check()
                require(off % BLOCK == 0 and 0 <= off < self.size and
                        len(payload) == min(BLOCK, self.size-off), 'invalid new cache block')
                require(self.db.execute('SELECT 1 FROM blocks WHERE off=?', (off,)).fetchone() is None,
                        'duplicate new cache block')
                padded = payload + bytes(BLOCK-len(payload))
                slot = original_count+i
                require(os.pwrite(self.data_fd, padded, slot*BLOCK) == BLOCK, 'short payload write')
                rows.append((off, slot, len(payload), self.digest(off, len(payload), padded)))
            os.fsync(self.data_fd)
            after_payload_sync()
            for off, slot, n, digest in rows:
                self.guard.check()
                data = os.pread(self.data_fd, BLOCK, slot*BLOCK)
                require(len(data) == BLOCK and self.digest(off, n, data) == digest, 'cache write readback failed')
                self.db.execute('INSERT INTO blocks VALUES (?,?,?,?)', (off, slot, n, digest))
            self.db.execute('COMMIT')
            for row in rows:
                require(self.db.execute('SELECT off,slot,n,digest FROM blocks WHERE off=?', (row[0],)).fetchone() == row,
                        'cache index readback failed')
            self.count += len(rows)
            self.guard.check()
        except BaseException:
            if self.db.in_transaction:
                self.db.execute('ROLLBACK')
            self.failed = True
            raise

    @synchronized
    def read(self, upstream, offset, count):
        require(not self.failed, 'cache is failed')
        require(type(offset) is int and type(count) is int and 0 <= count <= MAX_READ and
                0 <= offset <= self.size and offset+count <= self.size, 'read bounds')
        self.guard.check()
        if count == 0:
            return b''
        first, last = offset//BLOCK*BLOCK, (offset+count-1)//BLOCK*BLOCK
        blocks = {}
        try:
            for off in range(first, last+1, BLOCK):
                self.guard.check()
                value = self.get(off)
                if value is not None:
                    blocks[off] = value
            missing = [off for off in range(first, last+1, BLOCK) if off not in blocks]
            records, i = [], 0
            while i < len(missing):
                end = i+1
                while end < len(missing) and missing[end] == missing[end-1]+BLOCK and end-i < MAX_READ//BLOCK:
                    end += 1
                start = missing[i]
                size = min(missing[end-1]+BLOCK, self.size)-start
                self.guard.check()
                self.upstream_calls += 1
                payload = bytes(upstream.pread(size, start))
                require(len(payload) == size, 'short upstream read')
                self.guard.check()
                for off in missing[i:end]:
                    value = payload[off-start:off-start+min(BLOCK, self.size-off)]
                    records.append((off, value))
                    blocks[off] = value
                i = end
            # No entry from this request becomes valid until ALL upstream gaps
            # returned successfully, so a failed multi-gap read commits nothing.
            self.put_batch(records)
            result = bytearray(count)
            for off, value in blocks.items():
                left, right = max(offset, off), min(offset+count, off+len(value))
                result[left-offset:right-offset] = value[left-off:right-off]
            self.guard.check()
            return bytes(result)
        except BaseException:
            self.failed = True
            raise

    @synchronized
    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None
        for name in ('data_fd', 'lock_fd'):
            fd = getattr(self, name, None)
            if fd is not None:
                os.close(fd)
                setattr(self, name, None)
