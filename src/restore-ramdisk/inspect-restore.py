#!/usr/bin/env python3
"""Select firmware paths from Apple's current macOS 27 restore manifest."""
import json
import plistlib
from pathlib import Path
import subprocess
import urllib.request

feed_url = 'https://mesu.apple.com/assets/macos/com_apple_macOSIPSW/com_apple_macOSIPSW.xml'
with urllib.request.urlopen(feed_url, timeout=30) as response:
    feed = plistlib.loads(response.read())

def firmware(node):
    if isinstance(node, dict):
        if str(node.get('ProductVersion', '')).startswith('27.') and 'FirmwareURL' in node:
            return node
        for value in node.values():
            result = firmware(value)
            if result:
                return result
    elif isinstance(node, list):
        for value in node:
            result = firmware(value)
            if result:
                return result

asset = firmware(feed)
if not asset or not asset['FirmwareURL'].startswith('https://updates.cdn-apple.com/'):
    raise RuntimeError('No official macOS 27 restore asset found')
out = Path('/work/darwin/root-ipsw')
out.mkdir(parents=True, exist_ok=True)
subprocess.run(['/build/tools/ipsw', 'extract', '--remote', asset['FirmwareURL'],
                '--output', str(out), '--flat', '--pattern', '^BuildManifest[.]plist$'], check=True)
manifest_path = next(out.rglob('BuildManifest.plist'))
manifest = plistlib.loads(manifest_path.read_bytes())
identities = [identity for identity in manifest['BuildIdentities']
              if identity.get('Info', {}).get('DeviceClass') == 'j473ap']
if not identities:
    raise RuntimeError('Missing M2 Mac mini identity j473ap')
identity = next((item for item in identities if item.get('Info', {}).get('RestoreBehavior') == 'Erase'), identities[0])
components = {name: item.get('Info', {}).get('Path') for name, item in identity['Manifest'].items()
              if name in ['KernelCache', 'RestoreKernelCache', 'DeviceTree', 'SPTM', 'TXM',
                          'RestoreRamDisk', 'RestoreTrustCache', 'RestoreDeviceTree']}
result = {'source_feed': feed_url, 'ipsw_url': asset['FirmwareURL'],
          'product_version': manifest.get('ProductVersion'),
          'product_build': manifest.get('ProductBuildVersion'),
          'device_class': identity['Info']['DeviceClass'], 'components': components}
Path('/work/evidence/minimal-restore-inputs.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2), flush=True)
