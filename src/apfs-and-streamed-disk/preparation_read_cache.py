"""Small, transactional replay cache for verified preparation reads, never a disk image."""
import hashlib
import json
from pathlib import Path
import sqlite3
import stat
import threading

from fs_explorer.io.source import RandomAccess

MAX_DATABASE = 32 << 20
MAX_ITEM = 1 << 20
MAX_ENTRIES = 512


class ReadCacheSource(RandomAccess):
    def __init__(self, source, folder, identity, guard, report=lambda *a, **k: None,
                 database_bytes=MAX_DATABASE):
        if type(database_bytes) is not int or not 16384 <= database_bytes <= MAX_DATABASE:
            raise ValueError('Invalid preparation cache budget')
        self.source, self.guard, self.report = source, guard, report
        self.size = source.getsize()
        self.lock = threading.RLock()
        self.db = None
        self.writes_enabled = True
        encoded = json.dumps({'version': 1, 'size': self.size, 'pins': identity}, sort_keys=True)
        dataset = hashlib.sha256(encoded.encode()).hexdigest()
        folder = Path(folder)
        guard()
        if folder.is_symlink():
            raise ValueError('Preparation cache folder is a symlink')
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = folder / (dataset + '.sqlite3')
        for candidate in (path, Path(str(path) + '-journal'), Path(str(path) + '-wal'), Path(str(path) + '-shm')):
            if candidate.exists() or candidate.is_symlink():
                info = candidate.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise ValueError('Preparation cache must use private regular files')
        guard()
        db = sqlite3.connect(path, timeout=2, check_same_thread=False)
        try:
            db.execute('PRAGMA trusted_schema=OFF')
            db.execute('PRAGMA journal_mode=DELETE')
            db.execute('PRAGMA temp_store=MEMORY')
            db.execute('PRAGMA cache_size=-2048')
            db.execute('PRAGMA page_size=4096')
            if db.execute('PRAGMA page_size').fetchone()[0] != 4096:
                raise ValueError('Unexpected preparation cache page size')
            limit = database_bytes // 4096
            if db.execute(f'PRAGMA max_page_count={limit}').fetchone()[0] > limit:
                raise ValueError('Existing preparation cache exceeds its budget')
            if db.execute('PRAGMA quick_check').fetchone() != ('ok',):
                raise ValueError('Preparation cache database is corrupt')
            db.execute('CREATE TABLE IF NOT EXISTS identity (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS reads (offset INTEGER, requested INTEGER, digest BLOB NOT NULL, data BLOB NOT NULL, PRIMARY KEY(offset,requested))')
            old = db.execute('SELECT value FROM identity WHERE id=1').fetchone()
            if old is not None and old[0] != encoded:
                raise ValueError('Preparation cache identity mismatch')
            db.execute('INSERT OR IGNORE INTO identity VALUES(1,?)', (encoded,))
            db.commit()
            if db.execute('SELECT count(*) FROM reads').fetchone()[0] > MAX_ENTRIES:
                raise ValueError('Preparation cache has too many entries')
            self.db = db
            guard()
        except BaseException:
            db.close()
            raise
        self.report('preparation_cache_open', database_limit_bytes=limit * 4096,
                    entries=db.execute('SELECT count(*) FROM reads').fetchone()[0])

    def getsize(self):
        return self.size

    def read_at(self, offset, length):
        if type(offset) is not int or type(length) is not int or offset < 0 or not 0 <= length <= 32 << 20:
            raise ValueError('Invalid preparation read')
        with self.lock:
            if self.db is None:
                raise ValueError('Preparation cache is closed')
            self.guard()
            if offset >= self.size or length == 0:
                return b''
            row = self.db.execute('SELECT digest,data FROM reads WHERE offset=? AND requested=?', (offset, length)).fetchone()
            if row is not None:
                digest, data = row
                if (not 0 < len(data) <= MAX_ITEM or len(data) != min(length, max(0, self.size - offset))
                        or len(digest) != 32 or hashlib.sha256(data).digest() != digest):
                    raise ValueError('Preparation read cache digest/length mismatch')
                self.guard()
                self.report('preparation_cache_hit', offset=offset, requested=length, returned=len(data))
                return data
            data = self.source.read_at(offset, length)
            self.guard()
            if self.writes_enabled and 0 < len(data) <= MAX_ITEM:
                if len(data) != min(length, max(0, self.size - offset)):
                    raise ValueError('Unexpected short preparation read')
                count = self.db.execute('SELECT count(*) FROM reads').fetchone()[0]
                if count < MAX_ENTRIES:
                    try:
                        self.db.execute('INSERT INTO reads VALUES(?,?,?,?)',
                                        (offset, length, hashlib.sha256(data).digest(), data))
                        self.db.commit()
                    except sqlite3.OperationalError as error:
                        self.db.rollback()
                        if getattr(error, 'sqlite_errorcode', None) != sqlite3.SQLITE_FULL:
                            raise
                        self.writes_enabled = False
                        self.report('preparation_cache_full')
                self.guard()
            return data

    def close(self):
        with self.lock:
            if self.db is not None:
                self.db.close()
                self.db = None
            self.source.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
