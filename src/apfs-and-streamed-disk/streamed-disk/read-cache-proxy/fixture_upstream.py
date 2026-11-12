"""Synthetic test source only. Never used by the live proxy."""
import json
from pathlib import Path
import time
import nbdkit

API_VERSION = 2
OPTIONS = {}


def config(key, value):
    OPTIONS[key] = value


def open(readonly):
    return json.loads(Path(OPTIONS['config']).read_text())


def get_size(h):
    if h.get('stall_connect'):
        Path(h['marker']).write_text('connect')
        time.sleep(60)
    return h['size']


def can_write(h):
    return h.get('writable', False)


def pread(h, buf, offset, flags):
    with Path(h['reads']).open('a') as output:
        output.write(json.dumps({'offset': offset, 'count': len(buf)})+'\n')
    if h.get('stall_read'):
        Path(h['marker']).write_text('read')
        time.sleep(60)
    if h.get('fail_read'):
        raise RuntimeError('synthetic upstream failure')
    with Path(h['data']).open('rb') as source:
        source.seek(offset)
        data = source.read(len(buf))
    if len(data) != len(buf):
        raise RuntimeError('short synthetic source')
    buf[:] = data


def pwrite(h, buf, offset, flags):
    return
