"""Bounded proxy configuration and independent host/cache guards."""
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import sys
import time

BLOCK = 65536
MAX_READ = 32 * 1024**2
MAX_WIRE_READ = 1024**2
DATA_LIMIT = 512 * 1024**2
DISK_LIMIT = 1024**3
MAX_BLOCKS = DATA_LIMIT // BLOCK
POLL = .05
MAX_OPERATION_SECONDS = 900.
MANIFEST = 'sha256:b78a521145ebef24e9916c0b3999e165bb12b587d11524c5fa3ba4fe7bf79bb9'
CONFIG = 'sha256:75c5c60b68bcfb795cfd58a93490d0dc7a977850ff1db164defad7ddf69e1601'
PLAN = 'sha256:700a601da177786c796ff441c0c8f1d4edd0a4970557f7f81fa0ebb1092153a3'
SIZE = 50_000_000_000
CACHE_NAMES = {'blocks.bin', 'index.sqlite3', 'index.sqlite3-journal', 'cache.lock'}


class Refused(RuntimeError):
    pass


def require(value, reason):
    if not value:
        raise Refused(reason)


def emit(event, **fields):
    print(json.dumps(dict(event=event, observed_at=time.time(), **fields), sort_keys=True),
          file=sys.stderr, flush=True)


def regular_bytes(path, maximum):
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        s = os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and 0 < s.st_size <= maximum,
                'nonregular or oversized input')
        data = os.read(fd, maximum + 1)
        require(0 < len(data) <= maximum, 'oversized input')
        return data
    finally:
        os.close(fd)


def check_directory(path):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve(), 'directory must be canonical')
    for part in (path, *path.parents):
        require(stat.S_ISDIR(part.lstat().st_mode), 'symlink/non-directory ancestor')
    return path


def admit_resources():
    root = Path('/sys/fs/cgroup')
    memory = (root/'memory.max').read_text().strip()
    swap = (root/'memory.swap.max').read_text().strip()
    quota, period = (root/'cpu.max').read_text().split()
    pids = (root/'pids.max').read_text().strip()
    require(memory.isdecimal() and 128*1024**2 <= int(memory) <= 1024**3,
            'proxy requires a finite 128MiB..1GiB memory limit')
    require(swap == '0', 'proxy requires no extra swap allowance')
    require(quota.isdecimal() and period.isdecimal() and 0 < int(quota) <= int(period),
            'proxy requires at most one CPU')
    require(pids.isdecimal() and 0 < int(pids) <= 128, 'proxy requires at most 128 processes')


def identity(ready_path, raw=None):
    r = json.loads(regular_bytes(ready_path, 65536) if raw is None else raw)
    require(r.get('event') == 'export_ready' and r.get('readonly') is True,
            'upstream readiness is not a readonly export event')
    require(type(r.get('getsize')) is int and 0 < r['getsize'] < 2**63, 'invalid source size')
    if os.environ.get('READ_CACHE_PROXY_TEST_MODE') != '1':
        require((r.get('manifest_pin'), r.get('config_pin'), r.get('planDigest'), r['getsize']) ==
                (MANIFEST, CONFIG, PLAN, SIZE), 'unadmitted source pins')
    for key in ('manifest_pin', 'config_pin', 'planDigest'):
        value = r.get(key)
        require(isinstance(value, str) and len(value) <= 100 and value, 'invalid source pin')
    fields = {k: r[k] for k in ('manifest_pin', 'config_pin', 'planDigest', 'getsize')}
    encoded = json.dumps(dict(fields, cache_block_bytes=BLOCK), sort_keys=True, separators=(',', ':')).encode()
    return fields, hashlib.sha256(encoded).digest()


class Guard:
    def __init__(self, sample, cache, disk_limit=DISK_LIMIT, now=time.time):
        require(type(disk_limit) is int and 0 < disk_limit <= DISK_LIMIT, 'invalid disk budget')
        self.sample, self.cache, self.limit, self.now = Path(sample), Path(cache), disk_limit, now

    def check(self):
        # Match the existing Windows sharing-contention policy: retry only an
        # unreadable/missing open, never cache/reuse or forgive invalid samples.
        deadline = time.monotonic()+.5
        while True:
            try:
                raw = regular_bytes(self.sample, 4096)
                break
            except (PermissionError, FileNotFoundError):
                left = deadline-time.monotonic()
                if left <= 0:
                    raise
                time.sleep(min(.01,left))
        r = json.loads(raw)
        require(str(r['drive']).upper().rstrip('\\/') == 'C:', 'wrong host drive')
        require(type(r['free_bytes']) is int and r['free_bytes'] >= 10 * 1024**3,
                'host space below 10 GiB')
        observed = r['observed_at']
        require(type(observed) in (int, float) and math.isfinite(observed) and
                -2 <= self.now() - observed <= 20, 'stale/future host sample')
        check_directory(self.cache)
        directory = self.cache.lstat()
        logical = allocated = 0
        entries = []
        for path in self.cache.iterdir():
            require(len(entries) < len(CACHE_NAMES), 'too many cache files')
            entries.append(path)
        for path in entries:
            require(path.name in CACHE_NAMES, 'unknown cache file')
            try:
                s = path.lstat()
            except FileNotFoundError:
                # SQLite DELETE mode legitimately unlinks this exact transient
                # file between directory enumeration and stat. No persistent
                # cache entry or other missing path receives this exception.
                if path.name == 'index.sqlite3-journal':
                    continue
                raise
            unlinked_journal = path.name == 'index.sqlite3-journal' and s.st_nlink == 0
            require(stat.S_ISREG(s.st_mode) and (s.st_nlink == 1 or unlinked_journal),
                    'unsafe cache file')
            # A stat may retain the regular journal inode just as it is unlinked.
            # Count that inode conservatively rather than skipping its budget.
            logical += s.st_size
            allocated += s.st_blocks * 512
        after = self.cache.lstat()
        require(stat.S_ISDIR(after.st_mode) and
                (after.st_dev, after.st_ino) == (directory.st_dev, directory.st_ino),
                'cache directory changed during scan')
        require(max(logical, allocated) <= self.limit, 'cache disk budget exceeded')
        return dict(logical_bytes=logical, allocated_bytes=allocated)
