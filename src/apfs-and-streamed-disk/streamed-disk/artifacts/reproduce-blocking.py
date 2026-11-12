"""Bounded baseline experiment; synthetic HTTP bytes only, no Golden traffic."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", "4096")
        self.end_headers()
        try:
            for _ in range(4096):
                self.wfile.write(b"x")
                self.wfile.flush()
                time.sleep(.03)
        except (BrokenPipeError, ConnectionResetError):
            pass
    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
with tempfile.TemporaryDirectory() as root:
    sample = Path(root) / "space.json"
    sample.write_text(json.dumps({"drive": "C:", "free_bytes": 12 << 30, "observed_at": time.time()}))
    code = """
import requests, sys, time
from streamed_raw import CheckedStream, HostSpaceGuard
with requests.get(sys.argv[1], stream=True, timeout=(1, .15)) as response:
    print('read_started', flush=True)
    CheckedStream(response.raw, HostSpaceGuard(sys.argv[2]), time.monotonic() + .2).read(4096)
"""
    child = subprocess.Popen([sys.executable, "-u", "-c", code,
                             f"http://127.0.0.1:{server.server_port}/", str(sample)],
                            stdout=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == "read_started"
        started = time.monotonic()
        try:
            child.wait(.7)
            raise AssertionError("baseline unexpectedly cancelled read")
        except subprocess.TimeoutExpired:
            print(json.dumps({"baseline_still_blocked_seconds": round(time.monotonic() - started, 3),
                              "wall_deadline_seconds": .2, "socket_idle_timeout_seconds": .15,
                              "body_drip_seconds": .03, "reproduced": True}), flush=True)
    finally:
        child.kill()
        child.wait(1)
        child.stdout.close()
server.shutdown()
server.server_close()
