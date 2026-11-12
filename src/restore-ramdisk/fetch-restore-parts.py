#!/usr/bin/env python3
"""Fetch only the matched kernel and restore ramdisk for the serial experiment."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

work = Path('/work')
metadata = json.loads((work / 'evidence/minimal-restore-inputs.json').read_text())
if metadata['product_version'] != '27.0.1' or metadata['device_class'] != 'j473ap':
    raise RuntimeError('Unexpected restore identity')
if shutil.disk_usage(work).free < 2800 * 1024**2:
    raise RuntimeError('Insufficient space for the bounded restore experiment')
components = metadata['components']
parts = {
    'bootkc': components['KernelCache'],
    'dtree.raw': components['DeviceTree'],
    'ramdisk.dmg': components['RestoreRamDisk'],
    'ramdisk.tc': components['RestoreTrustCache'],
    'sptm': 'Firmware/sptm.t8112.release.im4p',
    'txm': 'Firmware/txm.macosx.release.im4p',
}
destination = work / 'darwin/parts'
firmware = work / 'darwin/firmware'
firmware.mkdir(parents=True, exist_ok=True)
pattern = '^(' + '|'.join(re.escape(value) for value in parts.values()) + ')$'
subprocess.run(['/build/tools/ipsw', 'extract', '--remote', metadata['ipsw_url'],
                '--output', str(destination), '--flat', '--pattern', pattern], check=True)
results = []
for name, member in parts.items():
    source = next(destination.rglob(Path(member).name))
    output = firmware / name
    subprocess.run(['/build/tools/ipsw', 'img4', 'im4p', 'extract', str(source), '-o', str(output)], check=True)
    results.append({'output': name, 'source_member': member, 'bytes': output.stat().st_size,
                    'sha256': hashlib.file_digest(output.open('rb'), 'sha256').hexdigest()})
(work / 'evidence/restore-payload-hashes.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2), flush=True)
