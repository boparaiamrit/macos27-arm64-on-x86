from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sqlite3
import struct
import threading
import lz4.block
import requests
from requests.adapters import HTTPAdapter
import nbdkit

API_VERSION = 2
BLOCK = 65536
CHUNK = 1048576
LAYER_SIZE = 536870912
DISK_SIZE = 50_000_000_000
RANGE_CHUNK = 2 * 1048576  # 2 MiB parallel HTTP Range chunks to avoid per-connection CDN throttling
REPO = 'cirruslabs/macos-golden-gate-vanilla'

CACHE_DIR = '/cache'
INTEG_DIR = '/parent/fastjit/qemu-integration'
INPUTS_DIR = '/parent/full-system/inputs'

SLOTS = {}
DATA_FD = None
ASIF_MAP = {}
LAYERS = []

LOCK = threading.Lock()
AUTH_LOCK = threading.Lock()
DOWNLOAD_SEM = threading.Semaphore(4)
LAYER_LOCKS = [threading.Lock() for _ in range(128)]
ZERO_BLOCK = b'\x00' * BLOCK
EXTRA_DB = None
EXTRA_MEM = {}
LAYER_DECODERS = {}  # layer_idx -> LayerDecoder
SESSION = None
TOKEN = None
POOL = None

HITS = 0
EXTRA_HITS = 0
SPARSE_HOLES = 0
FETCHED_BLOCKS = 0
ZERO_FILLS = 0
LAST_MISS = None


def thread_model():
    return getattr(nbdkit, 'THREAD_MODEL_PARALLEL', 3)


TLS = threading.local()


def get_thread_session():
    sess = getattr(TLS, 'session', None)
    if sess is None:
        sess = requests.Session()
        adapter = HTTPAdapter(pool_connections=16, pool_maxsize=16)
        sess.mount('https://', adapter)
        sess.mount('http://', adapter)
        TLS.session = sess
    return sess


def get_session_and_token(force_refresh=False):
    global SESSION, TOKEN, POOL
    with AUTH_LOCK:
        if SESSION is None:
            SESSION = requests.Session()
            adapter = HTTPAdapter(pool_connections=32, pool_maxsize=32)
            SESSION.mount('https://', adapter)
            SESSION.mount('http://', adapter)
        if POOL is None:
            POOL = ThreadPoolExecutor(max_workers=32)
        if TOKEN is None or force_refresh:
            r = SESSION.get(
                'https://ghcr.io/token',
                params={'service': 'ghcr.io', 'scope': f'repository:{REPO}:pull'},
                timeout=(5, 15),
            )
            r.raise_for_status()
            TOKEN = r.json()['token']
        return SESSION, TOKEN


class ParallelRangeStream:
    """Downloads a blob via parallel 2 MiB HTTP Range requests directly from the resolved CDN URL."""
    def __init__(self, digest, total_size):
        self.digest = digest
        self.total_size = total_size
        self.num_chunks = (total_size + RANGE_CHUNK - 1) // RANGE_CHUNK
        self.futures = {}
        self.pos = 0
        self.cur_chunk_idx = -1
        self.cur_chunk_bytes = b''
        self.cur_chunk_off = 0
        self.cdn_url = None
        self.cdn_lock = threading.Lock()

    def _get_cdn_url(self, force_refresh=False):
        with self.cdn_lock:
            if self.cdn_url is not None and not force_refresh:
                return self.cdn_url
            url = f'https://ghcr.io/v2/{REPO}/blobs/{self.digest}'
            for attempt in range(4):
                sess, tok = get_session_and_token(force_refresh=(attempt > 0))
                resp = sess.get(
                    url,
                    headers={
                        'Authorization': f'Bearer {tok}',
                        'Range': 'bytes=0-0',
                    },
                    allow_redirects=False,
                    timeout=(5, 15),
                )
                if resp.status_code in (301, 302, 303, 307, 308) and 'Location' in resp.headers:
                    self.cdn_url = resp.headers['Location']
                    resp.close()
                    return self.cdn_url
                if resp.status_code == 401 and attempt == 0:
                    resp.close()
                    continue
                resp.close()
            return None

    def _fetch_chunk(self, idx):
        start = idx * RANGE_CHUNK
        end = min(self.total_size, start + RANGE_CHUNK) - 1
        tsess = get_thread_session()
        for attempt in range(4):
            try:
                cdn = self._get_cdn_url(force_refresh=(attempt > 0))
                if cdn:
                    resp = tsess.get(
                        cdn,
                        headers={
                            'Accept-Encoding': 'identity',
                            'Range': f'bytes={start}-{end}',
                        },
                        timeout=(5, 12),
                    )
                    if resp.status_code in (401, 403) and attempt < 3:
                        resp.close()
                        continue
                    resp.raise_for_status()
                    return resp.content
                url = f'https://ghcr.io/v2/{REPO}/blobs/{self.digest}'
                _, tok = get_session_and_token(force_refresh=(attempt > 0))
                resp = tsess.get(
                    url,
                    headers={
                        'Authorization': f'Bearer {tok}',
                        'Accept-Encoding': 'identity',
                        'Range': f'bytes={start}-{end}',
                    },
                    timeout=(5, 12),
                )
                if resp.status_code == 401 and attempt < 3:
                    resp.close()
                    continue
                resp.raise_for_status()
                return resp.content
            except Exception:
                if attempt == 3:
                    raise
        raise RuntimeError(f'Failed to fetch range chunk {idx}')

    def _schedule_ahead(self, from_idx):
        # Keep up to 32 chunks (64 MiB) pre-fetching in parallel per active layer
        limit = min(self.num_chunks, from_idx + 32)
        for idx in range(from_idx, limit):
            if idx not in self.futures:
                self.futures[idx] = POOL.submit(self._fetch_chunk, idx)

    def read_exact(self, n):
        out = bytearray()
        while len(out) < n:
            if self.pos >= self.total_size:
                raise RuntimeError('Unexpected EOF in ParallelRangeStream')
            need_idx = self.pos // RANGE_CHUNK
            if need_idx != self.cur_chunk_idx:
                self._schedule_ahead(need_idx)
                fut = self.futures.pop(need_idx)
                self.cur_chunk_bytes = fut.result()
                self.cur_chunk_idx = need_idx
                self.cur_chunk_off = self.pos - need_idx * RANGE_CHUNK
            avail = len(self.cur_chunk_bytes) - self.cur_chunk_off
            take = min(n - len(out), avail)
            out.extend(self.cur_chunk_bytes[self.cur_chunk_off:self.cur_chunk_off + take])
            self.cur_chunk_off += take
            self.pos += take
        return bytes(out)

    def close(self):
        for fut in list(self.futures.values()):
            fut.cancel()
        self.futures.clear()
        self.cur_chunk_bytes = b''


class LayerDecoder:
    """Incremental streaming Apple-LZ4 (bv41/bv4-) decoder backed by ParallelRangeStream."""
    def __init__(self, layer_idx, digest, compressed_size):
        self.layer_idx = layer_idx
        self.digest = digest
        self.compressed_size = compressed_size
        self.buf = bytearray()
        self.prev = b''
        self.eof = False
        self.stream = None

    def ensure(self, end_offset):
        if len(self.buf) >= end_offset or self.eof:
            return
        if self.stream is None:
            get_session_and_token()
            self.stream = ParallelRangeStream(self.digest, self.compressed_size)
        while len(self.buf) < end_offset and not self.eof:
            magic = self.stream.read_exact(4)
            if magic == b'bv4$':
                self.eof = True
                self.close_stream()
                break
            if magic not in (b'bv41', b'bv4-'):
                raise RuntimeError(f'Unsupported bv4 frame magic: {magic!r}')
            sz = struct.unpack('<I', self.stream.read_exact(4))[0]
            if magic == b'bv4-':
                blk = self.stream.read_exact(sz)
            else:
                psz = struct.unpack('<I', self.stream.read_exact(4))[0]
                packed = self.stream.read_exact(psz)
                blk = lz4.block.decompress(packed, uncompressed_size=sz, dict=self.prev)
            self.buf.extend(blk)
            self.prev = blk[-65536:]

    def read_slice(self, offset, length):
        self.ensure(offset + length)
        return bytes(self.buf[offset:offset + length])

    def close_stream(self):
        if self.stream is not None:
            self.stream.close()
            self.stream = None


def config(key, value):
    global CACHE_DIR
    if key == 'cache':
        CACHE_DIR = value


def after_fork():
    global DATA_FD, EXTRA_DB
    db_path = f'file:{CACHE_DIR}/index.sqlite3?mode=ro&immutable=1'
    conn = sqlite3.connect(db_path, uri=True)
    for off, slot, n in conn.execute('SELECT off, slot, n FROM blocks'):
        SLOTS[int(off)] = (int(slot), int(n))
    conn.close()
    DATA_FD = os.open(f'{CACHE_DIR}/blocks.bin', os.O_RDONLY)

    cmap_path = Path(f'{INTEG_DIR}/asif_chunk_map.json')
    if cmap_path.exists():
        cmap = json.loads(cmap_path.read_text(encoding='utf-8'))
        for v, st, ph, bm in cmap['mapped']:
            ASIF_MAP[int(v)] = (int(st), int(ph), int(bm))

    manifest_path = Path(f'{INPUTS_DIR}/manifest.json')
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        for item in manifest.get('layers', []):
            if item.get('mediaType') == 'application/vnd.cirruslabs.tart.disk.v2':
                LAYERS.append((item['digest'], int(item['size'])))

    extra_db_path = Path(f'{INTEG_DIR}/extra_cache.sqlite3')
    EXTRA_DB = sqlite3.connect(str(extra_db_path), check_same_thread=False)
    EXTRA_DB.execute('CREATE TABLE IF NOT EXISTS blocks (off INTEGER PRIMARY KEY, data BLOB NOT NULL)')
    EXTRA_DB.commit()
    for off, data in EXTRA_DB.execute('SELECT off, data FROM blocks'):
        EXTRA_MEM[int(off)] = bytes(data)
    Path('/tmp/fastjit-vm').mkdir(parents=True, exist_ok=True)
    Path('/tmp/fastjit-vm/nbd_ready').write_text(str(len(SLOTS) + len(EXTRA_MEM)), encoding='utf-8')


def open(readonly):
    return 1


def get_size(h):
    return DISK_SIZE


def can_write(h):
    return False


def can_multi_conn(h):
    return True


def can_cache(h):
    return nbdkit.CACHE_NATIVE


def get_or_fetch_block(blk_off):
    global EXTRA_HITS, SPARSE_HOLES, FETCHED_BLOCKS, ZERO_FILLS, LAST_MISS
    # Lock-free fast path for already-cached blocks in EXTRA_MEM
    cached = EXTRA_MEM.get(blk_off)
    if cached is not None:
        EXTRA_HITS += 1
        return cached

    vchunk = blk_off // CHUNK
    in_chunk = blk_off - vchunk * CHUNK
    mapping = ASIF_MAP.get(vchunk)
    if mapping is None:
        SPARSE_HOLES += 1
        return ZERO_BLOCK

    st, physical, bm = mapping
    phys_off = physical * CHUNK + in_chunk
    layer_idx = phys_off // LAYER_SIZE
    in_layer = phys_off - layer_idx * LAYER_SIZE

    if not (0 <= layer_idx < len(LAYERS)):
        ZERO_FILLS += 1
        LAST_MISS = blk_off
        return ZERO_BLOCK

    with LAYER_LOCKS[layer_idx]:
        # Re-check after acquiring per-layer lock
        cached = EXTRA_MEM.get(blk_off)
        if cached is not None:
            EXTRA_HITS += 1
            return cached

        try:
            with LOCK:
                decoder = LAYER_DECODERS.get(layer_idx)
                if decoder is None:
                    if len(LAYER_DECODERS) >= 32:
                        for k in list(LAYER_DECODERS):
                            if k != layer_idx and not LAYER_LOCKS[k].locked():
                                old_dec = LAYER_DECODERS.pop(k)
                                old_dec.close_stream()
                                old_dec.buf.clear()
                                break
                    digest, csize = LAYERS[layer_idx]
                    decoder = LayerDecoder(layer_idx, digest, csize)
                    LAYER_DECODERS[layer_idx] = decoder
                else:
                    LAYER_DECODERS[layer_idx] = LAYER_DECODERS.pop(layer_idx)

            chunk_end_in_layer = (physical * CHUNK + CHUNK) - layer_idx * LAYER_SIZE
            need_end = min(LAYER_SIZE, chunk_end_in_layer + 16 * 1048576)
            if len(decoder.buf) < need_end and not decoder.eof:
                with DOWNLOAD_SEM:
                    if len(decoder.buf) < need_end and not decoder.eof:
                        try:
                            with Path('/tmp/fastjit-vm/nbd_layer.log').open('a') as lf:
                                lf.write(f'[NBD] Parallel-streaming layer {layer_idx} ({len(decoder.buf)//1048576} -> {need_end//1048576} MiB) for blk_off={blk_off}\n')
                        except Exception:
                            pass
                        decoder.ensure(need_end)

            batch = []
            for dv in range(8):
                cand_vchunk = vchunk + dv
                cand_map = ASIF_MAP.get(cand_vchunk)
                if cand_map is None:
                    continue
                _, cand_phys, _ = cand_map
                cand_layer = (cand_phys * CHUNK) // LAYER_SIZE
                if cand_layer != layer_idx:
                    continue
                chunk_base_voff = cand_vchunk * CHUNK
                chunk_base_in_layer = cand_phys * CHUNK - layer_idx * LAYER_SIZE
                if chunk_base_in_layer + CHUNK > len(decoder.buf):
                    continue
                for b_idx in range(16):
                    b_voff = chunk_base_voff + b_idx * BLOCK
                    if b_voff in SLOTS or b_voff in EXTRA_MEM:
                        continue
                    b_in_layer = chunk_base_in_layer + b_idx * BLOCK
                    if 0 <= b_in_layer < len(decoder.buf):
                        b_data = bytes(decoder.buf[b_in_layer:b_in_layer + BLOCK])
                        if len(b_data) < BLOCK:
                            b_data = b_data + b'\x00' * (BLOCK - len(b_data))
                        EXTRA_MEM[b_voff] = b_data
                        batch.append((b_voff, b_data))
            if batch:
                with LOCK:
                    try:
                        EXTRA_DB.executemany('INSERT OR REPLACE INTO blocks VALUES (?, ?)', batch)
                        EXTRA_DB.commit()
                    except Exception:
                        pass
                    FETCHED_BLOCKS += len(batch)

            LAST_MISS = blk_off
            return EXTRA_MEM.get(blk_off, ZERO_BLOCK)
        except Exception as exc:
            ZERO_FILLS += 1
            LAST_MISS = blk_off
            try:
                with Path('/tmp/fastjit-vm/nbd_layer.log').open('a') as lf:
                    lf.write(f'[NBD] ERROR layer {layer_idx} blk_off={blk_off}: {type(exc).__name__}: {exc}\n')
            except Exception:
                pass
            return ZERO_BLOCK


def pread(h, buf, offset, flags):
    global HITS
    length = len(buf)
    pos = 0
    while pos < length:
        cur = offset + pos
        blk_off = (cur // BLOCK) * BLOCK
        in_blk = cur - blk_off
        take = min(length - pos, BLOCK - in_blk)
        entry = SLOTS.get(blk_off)
        if entry is not None:
            slot, n = entry
            data = os.pread(DATA_FD, take, slot * BLOCK + in_blk)
            buf[pos:pos + take] = data
            HITS += 1
        else:
            blk_data = get_or_fetch_block(blk_off)
            buf[pos:pos + take] = blk_data[in_blk:in_blk + take]
        pos += take

    total_ops = HITS + EXTRA_HITS + SPARSE_HOLES + FETCHED_BLOCKS + ZERO_FILLS
    if total_ops % 128 == 0 or FETCHED_BLOCKS in (1, 5, 10, 25, 50, 100):
        try:
            Path('/tmp/fastjit-vm/nbd_stats.json').write_text(
                json.dumps({
                    'hits': HITS,
                    'extra_hits': EXTRA_HITS,
                    'sparse_holes': SPARSE_HOLES,
                    'fetched_blocks': FETCHED_BLOCKS,
                    'zero_fills': ZERO_FILLS,
                    'last_miss': LAST_MISS,
                    'cached_blocks': len(SLOTS) + len(EXTRA_MEM),
                })
            )
        except Exception:
            pass
