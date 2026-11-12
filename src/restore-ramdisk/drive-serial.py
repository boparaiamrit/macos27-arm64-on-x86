#!/usr/bin/env python3
"""Verify live commands in the temporary macOS restore single-user shell."""
import pathlib
import re
import socket
import time

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(1)
for attempt in range(40):
    try:
        sock.connect('/work/evidence/serial.sock')
        break
    except (FileNotFoundError, ConnectionRefusedError):
        time.sleep(0.25)
else:
    raise RuntimeError('No live serial socket')
sock.sendall(b'\n')
received = b''
deadline = time.monotonic() + 55
while time.monotonic() < deadline and b'root#' not in received:
    try:
        chunk = sock.recv(65536)
        if not chunk:
            break
        received += chunk
    except socket.timeout:
        pass
if b'root#' not in received:
    raise RuntimeError('No live shell prompt')
sock.sendall(b"printf '\\n__GOLDEN_COMMANDS_BEGIN__\\n'; uname -a; /usr/bin/id; /bin/ls /; printf '__GOLDEN_COMMANDS_END__\\n'\n")
output = b''
deadline = time.monotonic() + 20
end = rb'\n__GOLDEN_COMMANDS_END__\r?\n'
while time.monotonic() < deadline:
    try:
        chunk = sock.recv(65536)
        if not chunk:
            break
        output += chunk
    except socket.timeout:
        pass
    if re.search(end, output.replace(b'\r', b'')):
        break
pathlib.Path('/work/evidence/golden-gate-command-session.txt').write_bytes(output)
print(output.decode('utf8', 'replace'), flush=True)
if not re.search(end, output.replace(b'\r', b'')):
    raise RuntimeError('Commands did not complete')
