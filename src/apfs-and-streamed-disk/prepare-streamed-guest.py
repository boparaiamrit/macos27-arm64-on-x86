#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Extract matched boot inputs through a verified read-only NBD export."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import plistlib
import time

from nbd_source import NBDSource
from guest_artifacts import discover, save_boot_inputs

PIN = 'sha256:b78a521145ebef24e9916c0b3999e165bb12b587d11524c5fa3ba4fe7bf79bb9'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--socket', type=Path, required=True)
parser.add_argument('--ready', type=Path, required=True)
parser.add_argument('--plan', type=Path, required=True)
parser.add_argument('--inputs', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--system-root')
parser.add_argument('--trace-reads', action='store_true', help='Log logical read offsets and durations without payload bytes')
parser.add_argument('--cache-reads', action='store_true', help='Keep a preparation read-cache database capped at 32 MiB')
args = parser.parse_args()


class TracedNBDSource(NBDSource):
    def __init__(self, socket):
        super().__init__(socket)
        self.read_count = 0

    def read_at(self, offset, length):
        self.read_count += 1
        read_id = self.read_count
        started = time.monotonic()
        print(json.dumps({'event': 'nbd_read_start', 'read_id': read_id,
                          'offset': offset, 'length': length}), flush=True)
        try:
            data = super().read_at(offset, length)
        except BaseException as error:
            print(json.dumps({'event': 'nbd_read_error', 'read_id': read_id,
                              'error_type': type(error).__name__}), flush=True)
            raise
        print(json.dumps({'event': 'nbd_read_end', 'read_id': read_id, 'returned': len(data),
                          'elapsed_seconds': round(time.monotonic() - started, 6)}), flush=True)
        return data
ready = json.loads(args.ready.read_text())
plan = json.loads(args.plan.read_text())
assert ready['event'] == 'export_ready' and ready['readonly'] is True
assert ready['manifest_pin'] == plan['manifest_digest'] == PIN
assert ready['planDigest'] == plan['plan_digest']
assert ready['getsize'] == plan['logical_raw_bytes'] == 50_000_000_000
config_bytes = (args.inputs / 'config.json').read_bytes()
assert 'sha256:' + hashlib.sha256(config_bytes).hexdigest() == ready['config_pin'] == plan['config_digest']
config = json.loads(config_bytes)
ecid = plistlib.loads(base64.b64decode(config['ecid']))['ECID']
assert type(ecid) is int and ecid > 0
source_type = TracedNBDSource if args.trace_reads else NBDSource
source = source_type(str(args.socket))
if args.cache_reads:
    from preparation_read_cache import ReadCacheSource
    from host_space_sample import read_valid_sample
    try:
        source = ReadCacheSource(source, args.output.parent / 'preparation-read-cache',
                                 {'manifest': PIN, 'config': ready['config_pin'], 'plan': ready['planDigest']},
                                 lambda: read_valid_sample(args.inputs.parent / 'host-space-live.json'),
                                 lambda event, **fields: print(json.dumps({'event': event, **fields}), flush=True))
    except BaseException:
        source.close()
        raise
with source:
    assert source.getsize() == 50_000_000_000
    print(json.dumps({'event': 'readonly_stream_connected', 'logical_bytes': source.getsize()}), flush=True)
    census, candidates = discover(source, args.system_root, lambda event: print(json.dumps(event), flush=True))
    report = save_boot_inputs(args.output, args.inputs, census, candidates,
                              {'manifest_digest': PIN, 'plan_digest': ready['planDigest'],
                               'source_kind': 'readonly-streamed-nbd', 'nbd_socket': str(args.socket),
                               'logical_disk_bytes': source.getsize(), 'local_full_disk': False})
    print(json.dumps(report, indent=2), flush=True)
