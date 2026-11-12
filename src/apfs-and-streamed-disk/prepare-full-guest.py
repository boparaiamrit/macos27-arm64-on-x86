#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Inspect a completed converted guest and extract its matching VM firmware."""
import argparse
import base64
import fcntl
import hashlib
import json
from pathlib import Path
import plistlib
from guest_artifacts import discover, save_boot_inputs

PIN = 'sha256:b78a521145ebef24e9916c0b3999e165bb12b587d11524c5fa3ba4fe7bf79bb9'

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--disk', type=Path, required=True)
parser.add_argument('--inputs', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--system-root', help='optional exact virtual-volume root reported by fs-explorer')
args = parser.parse_args()
checkpoint = json.loads(Path(str(args.disk) + '.checkpoint.json').read_text())
assert checkpoint['complete'] is True and checkpoint['manifest_digest'] == PIN
assert len(checkpoint['completed']) == 67
assert args.disk.stat().st_size == checkpoint['logical_size'] == 50_000_000_000
config_bytes = (args.inputs / 'config.json').read_bytes()
assert 'sha256:' + hashlib.sha256(config_bytes).hexdigest() == checkpoint['config_digest']
config = json.loads(config_bytes)
ecid = plistlib.loads(base64.b64decode(config['ecid']))['ECID']
assert isinstance(ecid, int) and ecid > 0

with args.disk.open('rb') as disk:
    fcntl.flock(disk, fcntl.LOCK_SH | fcntl.LOCK_NB)
    census, candidates = discover(disk, args.system_root)
    report = save_boot_inputs(args.output, args.inputs, census, candidates,
                              {'manifest_digest': PIN, 'source_kind': 'local-raw'})
    print(json.dumps(report, indent=2))
