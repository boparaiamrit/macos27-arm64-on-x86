#!/usr/bin/env python3
"""Fetch and hash only the paired VM identity and auxiliary storage, not the OS disk."""
import hashlib
import json
from pathlib import Path
import urllib.request

repo = 'cirruslabs/macos-golden-gate-vanilla'
manifest_digest = 'sha256:b78a521145ebef24e9916c0b3999e165bb12b587d11524c5fa3ba4fe7bf79bb9'
out = Path(__file__).resolve().parent / 'full-system' / 'inputs'
out.mkdir(parents=True, exist_ok=True)
with urllib.request.urlopen('https://ghcr.io/token?scope=repository:' + repo + ':pull', timeout=30) as response:
    token = json.load(response)['token']
headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.oci.image.manifest.v1+json'}

def fetch(path, digest, maximum):
    request = urllib.request.Request('https://ghcr.io/v2/' + repo + '/' + path, headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read(maximum + 1)
    assert len(raw) <= maximum, 'Unexpected metadata size'
    assert 'sha256:' + hashlib.sha256(raw).hexdigest() == digest, 'Metadata digest mismatch'
    return raw

raw = fetch('manifests/' + manifest_digest, manifest_digest, 4 * 1024**2)
manifest = json.loads(raw)
(out / 'manifest.json').write_bytes(raw)
results = []
for kind, filename in [('config.v1', 'config.json'), ('nvram.v1', 'nvram.original')]:
    descriptors = [item for item in manifest['layers'] if item['mediaType'].endswith(kind)]
    assert len(descriptors) == 1, 'Ambiguous metadata layer'
    descriptor = descriptors[0]
    raw = fetch('blobs/' + descriptor['digest'], descriptor['digest'], 64 * 1024**2)
    assert len(raw) == descriptor['size']
    (out / filename).write_bytes(raw)
    results.append({'kind': kind, 'file': filename, 'bytes': len(raw), 'digest': descriptor['digest']})
nvram = (out / 'nvram.original').read_bytes()
bank = 0xA00000
if b'nvram' in nvram[bank:bank + 64]:
    stripped = nvram
    wrapper = 0
elif b'nvram' in nvram[bank + 0x4000:bank + 0x4000 + 64]:
    stripped = nvram[0x4000:]
    wrapper = 0x4000
else:
    raise RuntimeError('Unknown auxiliary NVRAM layout; original preserved for inspection')
(out / 'aux.img').write_bytes(stripped)
summary = {'repository': repo, 'manifest_digest': manifest_digest,
           'metadata': results, 'aux_bytes': len(stripped), 'removed_wrapper_bytes': wrapper,
           'full_disk_downloaded': False}
(out / 'metadata-hashes.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
