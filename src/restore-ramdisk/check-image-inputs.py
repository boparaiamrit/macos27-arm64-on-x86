#!/usr/bin/env python3
"""Inspect public Tart image metadata without downloading an OS disk."""
import hashlib
import json
from pathlib import Path
import urllib.request

OUT = Path('/work/evidence')
OUT.mkdir(exist_ok=True)
summaries = []
for repo in ['cirruslabs/macos-golden-gate-base', 'cirruslabs/macos-ventura-base']:
    token_url = 'https://ghcr.io/token?scope=repository:' + repo + ':pull'
    with urllib.request.urlopen(token_url, timeout=30) as response:
        token = json.load(response)['token']
    headers = {'Authorization': 'Bearer ' + token,
               'Accept': 'application/vnd.oci.image.manifest.v1+json'}
    url = 'https://ghcr.io/v2/' + repo + '/manifests/latest'
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        raw = response.read()
        digest = response.headers.get('Docker-Content-Digest')
    if digest and 'sha256:' + hashlib.sha256(raw).hexdigest() != digest:
        raise RuntimeError('manifest hash mismatch')
    manifest = json.loads(raw)
    descriptor = manifest['config']
    if descriptor['size'] > 1024 * 1024:
        raise RuntimeError('unexpectedly large OCI config')
    config_url = 'https://ghcr.io/v2/' + repo + '/blobs/' + descriptor['digest']
    with urllib.request.urlopen(urllib.request.Request(config_url, headers=headers), timeout=30) as response:
        config_raw = response.read(1024 * 1024 + 1)
    if 'sha256:' + hashlib.sha256(config_raw).hexdigest() != descriptor['digest']:
        raise RuntimeError('OCI config hash mismatch')
    config = json.loads(config_raw)
    disk = [layer for layer in manifest['layers'] if layer['mediaType'].endswith('disk.v2')]
    summary = {'repository': repo, 'manifest_digest': digest,
               'compressed_disk_bytes': sum(layer['size'] for layer in disk),
               'uncompressed_disk_bytes': int(manifest['annotations']['org.cirruslabs.tart.uncompressed-disk-size']),
               'disk_layers': len(disk), 'disk_downloaded': False,
               'oci_config': config,
               'metadata_layers': [{'type': layer['mediaType'], 'bytes': layer['size']}
                                   for layer in manifest['layers'] if layer not in disk]}
    (OUT / (repo.split('/')[-1] + '-manifest.json')).write_bytes(raw)
    summaries.append(summary)
(OUT / 'image-requirements.json').write_text(json.dumps(summaries, indent=2) + '\n')
print(json.dumps(summaries, indent=2))
