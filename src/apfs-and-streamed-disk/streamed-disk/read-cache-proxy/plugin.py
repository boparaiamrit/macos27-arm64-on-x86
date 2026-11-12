"""Serialized readonly API2 NBD proxy. Bare startup intentionally unsupported."""
import errno
import hashlib
import os
from pathlib import Path
import stat
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nbd
import nbdkit
from cache import BlockCache
from common import Guard, MAX_WIRE_READ, BLOCK, emit, identity, require, regular_bytes, Refused
from control import Control

API_VERSION = 2
OPTIONS = {}
CONTROL = SOURCE = CACHE = GUARD = FIELDS = None
REQUESTS = RETURNED = 0
LAST_STATS = 0.


def config(key, value):
    require(key in {'upstream', 'ready', 'cache', 'host-space'} and key not in OPTIONS, 'invalid proxy option')
    OPTIONS[key] = value


def config_complete():
    global CONTROL, GUARD, FIELDS, SOURCE_ID, READY_SHA
    require(len(OPTIONS) == 4, 'proxy options missing')
    CONTROL = Control.environment()
    GUARD = Guard(OPTIONS['host-space'], OPTIONS['cache'])
    GUARD.check()
    raw_ready = regular_bytes(OPTIONS['ready'],65536)
    READY_SHA = hashlib.sha256(raw_ready).hexdigest()
    FIELDS, SOURCE_ID = identity(OPTIONS['ready'], raw_ready)
    upstream = Path(OPTIONS['upstream'])
    require(upstream.is_absolute() and upstream == upstream.resolve() and
            stat.S_ISSOCK(upstream.lstat().st_mode), 'invalid upstream socket')


def thread_model():
    return nbdkit.THREAD_MODEL_SERIALIZE_ALL_REQUESTS


def after_fork():
    global SOURCE, CACHE
    GUARD.check()
    before = Path(OPTIONS['upstream']).lstat()
    SOURCE = nbd.NBD()
    SOURCE.connect_unix(OPTIONS['upstream'])
    require(SOURCE.is_read_only() and SOURCE.get_size() == FIELDS['getsize'], 'upstream readonly/size mismatch')
    after = Path(OPTIONS['upstream']).lstat()
    require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino), 'upstream socket changed during connection')
    CACHE = BlockCache(OPTIONS['cache'], SOURCE_ID, FIELDS['getsize'], GUARD)
    require(hashlib.sha256(regular_bytes(OPTIONS['ready'],65536)).hexdigest() == READY_SHA,
            'upstream readiness changed during initialization')
    CONTROL.ready()
    emit('export_ready', **FIELDS, readonly=True, max_read_bytes=MAX_WIRE_READ,
         cache_data_limit_bytes=512*1024**2, cache_disk_limit_bytes=1024**3,
         cached_blocks=CACHE.count, source_kind='readonly-returned-block-cache',
         cache_block_bytes=BLOCK, cache_source_id=SOURCE_ID.hex(),
         upstream_socket_device=after.st_dev, upstream_socket_inode=after.st_ino,
         upstream_ready_sha256=READY_SHA,
         payload_verification='upstream verifies cold source; cached returned blocks checked by local source-bound SHA256',
         all_disk_layers_verified=False)


def open(readonly):
    GUARD.check()
    return CACHE


def get_size(h):
    return FIELDS['getsize']


def block_size(h):
    return (1, 4096, MAX_WIRE_READ)


def can_write(h):
    return False


def can_multi_conn(h):
    return True


def can_cache(h):
    return nbdkit.CACHE_NONE


def pread(h, buf, offset, flags):
    global REQUESTS, RETURNED, LAST_STATS
    CONTROL.start()
    try:
        require(len(buf) <= MAX_WIRE_READ, 'wire read exceeds advertised one MiB maximum')
        data = h.read(SOURCE, offset, len(buf))
        GUARD.check()
        CONTROL.end()
        buf[:] = data
        REQUESTS += 1
        RETURNED += len(data)
        if REQUESTS % 128 == 0 or time.monotonic()-LAST_STATS >= 60:
            emit('cache_stats', requests=REQUESTS, returned_bytes=RETURNED, cached_blocks=h.count,
                 hits=h.hits, misses=h.misses, upstream_calls=h.upstream_calls)
            LAST_STATS = time.monotonic()
    except Exception as exc:
        emit('read_failed', error_type=type(exc).__name__, offset=offset, count=len(buf),
             reason=str(exc) if isinstance(exc,Refused) else 'upstream or runtime failure')
        CONTROL.send('fatal')
        nbdkit.set_error(errno.EIO)
        nbdkit.shutdown()
        raise RuntimeError('verified read cache failed closed') from None


def pwrite(h, buf, offset, flags):
    nbdkit.set_error(errno.EROFS)
    raise RuntimeError('readonly proxy')


def cleanup():
    if CACHE:
        emit('cache_stats', cached_blocks=CACHE.count, hits=CACHE.hits, misses=CACHE.misses,
             upstream_calls=CACHE.upstream_calls)
        CACHE.close()
    # Process exit closes the upstream handle; do not introduce a blocking
    # remote shutdown wait while nbdkit is already terminating.
