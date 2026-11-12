#!/usr/bin/env python3
"""Verify recorded boot checkpoints; does not start a VM or imply GUI support."""
import hashlib
import json
from pathlib import Path
import re

work = Path(__file__).resolve().parent
evidence = work / 'evidence'
session = (evidence / 'golden-gate-command-session.txt').read_bytes().replace(b'\r', b'')
start = session.find(b'\n__GOLDEN_COMMANDS_BEGIN__\n')
end = session.find(b'\n__GOLDEN_COMMANDS_END__\n', start)
assert start >= 0 and end > start, 'Incomplete recorded command session'
command_output = session[start:end]
assert re.search(rb'Darwin localhost 27\.0\.0 .*RELEASE_ARM64_T8112 arm64', command_output)
assert b'uid=0(root)' in command_output
assert b'System' in command_output and b'private' in command_output
restore = (evidence / 'golden-gate-restore.log').read_text(errors='replace')
single = (evidence / 'golden-gate-single-user.log').read_text(errors='replace')
assert 'Darwin Kernel Version 27.0.0' in restore and 'pid: 1' in restore
assert 'Entering single-user mode' in single and 'root#' in single
assert 'panic(cpu' not in restore and 'panic(cpu' not in single
metadata = json.loads((evidence / 'minimal-restore-inputs.json').read_text())
assert metadata['product_version'] == '27.0.1' and metadata['product_build'] == '26A434'
for item in json.loads((evidence / 'restore-payload-hashes.json').read_text()):
    path = work / 'darwin/firmware' / item['output']
    assert path.stat().st_size == item['bytes']
    with path.open('rb') as source:
        assert hashlib.file_digest(source, 'sha256').hexdigest() == item['sha256']
result = {'kernel_boot': True, 'restore_launchd_pid_1': True, 'single_user_shell': True,
          'live_uname_arm64_darwin_27': True, 'live_id_root': True, 'live_ls_root': True,
          'local_input_hashes_verified': True, 'macos_product_version': metadata['product_version'],
          'macos_product_build': metadata['product_build'], 'desktop_verified': False,
          'gpu_acceleration_verified': False, 'full_installed_system': False,
          'limitations': ['Restore RAM disk only', 'stty and sw_vers absent in restore environment',
                          'Emulator applies upstream in-memory boot patch',
                          'Interactive driver initially rejected CRCRLF completion; transcript verified offline',
                          'VM stopped because host storage became critically low']}
(evidence / 'verified-results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
