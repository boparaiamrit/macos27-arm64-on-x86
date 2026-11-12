#!/usr/bin/env python3
"""Stage the pinned BSD filesystem reader for offline inspection of guest disks."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request

url = 'https://files.pythonhosted.org/packages/b0/de/916f5ce39ac1ea1748f2bbd89d91ee1088658f02ff521a31ff5655ca7dfd/fs_explorer-0.5.0.tar.gz'
expected = '1398600e798168823cad4b26b2db4b2c4ea13459e787156749b6e192e12382e9'
with urllib.request.urlopen(url, timeout=30) as response:
    data = response.read()
assert hashlib.sha256(data).hexdigest() == expected
out = Path(__file__).resolve().parent / 'apfs-tools'
out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
    for member in archive.getmembers():
        path = PurePosixPath(member.name)
        if not member.isfile() or path.is_absolute() or '..' in path.parts:
            continue
        relative = path.relative_to('fs_explorer-0.5.0')
        if str(relative).startswith('src/fs_explorer/') or str(relative) == 'LICENSE':
            destination = out.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.extractfile(member).read())
(out / 'provenance.json').write_text(json.dumps({'version': '0.5.0', 'sha256': expected,
                                               'source_url': url, 'license': 'BSD-3-Clause'}, indent=2) + '\n')
print(out)
