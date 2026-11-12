"""Real slow-drip/header stalls and process cleanup, on tiny offline fixtures."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

import nbd
from frozen import oci
from streamed_raw import RESERVE
from supervision import LAYER_SECONDS, INIT_SECONDS, KILL_GRACE_SECONDS
from serve import bounded_seconds
from test_streamed_disk import fixture_command, write_space
from tiny_fixture import package

STARTUP_WAIT_SECONDS = 5


@contextmanager
def stalled_registry(blobs, mode, digest=None):
    stop, entered = threading.Event(), threading.Event()
    state = {"entered": entered, "body_bytes": 0, "requests": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            key = self.path.lstrip("/")
            body = blobs.get(key)
            state["requests"] += 1
            if body is None:
                self.send_error(404)
                return
            stall = digest is None or key == digest
            if stall:
                entered.set()
            if stall and mode == "headers":
                stop.wait(3)  # No response headers: requests.get/open stays blocked.
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                if stall and mode == "drip":
                    # Actual body progress every 30ms, well within the fixture's
                    # 5s socket idle timeout, but far short of a complete layer.
                    for value in body:
                        self.wfile.write(bytes([value]))
                        self.wfile.flush()
                        state["body_bytes"] += 1
                        if stop.wait(.03):
                            break
                else:
                    self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=lambda: server.serve_forever(poll_interval=.02), daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", state
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
        worker.join(1)
        if worker.is_alive():
            raise AssertionError("fixture HTTP worker not reaped")


class Cancellation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="streamed-cancel-")
        self.root = Path(self.tmp.name)
        self.pins, self.blobs, self.expected = package(self.root)
        self.space = self.root / "space.json"
        write_space(self.space)
        self.proc = None
        self.log_path = self.root / "server.log"
        self.log = self.log_path.open("w")

    def tearDown(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(1)
                self.fail("supervisor did not stop its child within test bound")
        self.log.close()
        self.tmp.cleanup()

    def launch(self, url, layer=.5, init=10):
        self.started = time.monotonic()
        self.proc = subprocess.Popen(fixture_command(self.root, self.space, url, self.pins.manifest_digest,
                                     ["--layer-deadline-seconds", str(layer),
                                      "--initialization-deadline-seconds", str(init)]),
                                     stdout=self.log, stderr=subprocess.STDOUT)

    def wait_entered(self, state):
        deadline = time.monotonic() + STARTUP_WAIT_SECONDS
        while not state["entered"].wait(.01):
            if self.proc.poll() is not None:
                self.fail("server stopped before fixture HTTP: " + self.log_path.read_text())
            if time.monotonic() >= deadline:
                self.fail("fixture HTTP startup exceeded 5s: " + self.log_path.read_text())

    def wait_ready(self):
        deadline = time.monotonic() + STARTUP_WAIT_SECONDS
        while time.monotonic() < deadline:
            if '"event": "export_ready"' in self.log_path.read_text():
                return
            if self.proc.poll() is not None:
                self.fail("server failed before ready: " + self.log_path.read_text())
            time.sleep(.01)
        self.fail("fixture failed to initialize within 5s: " + self.log_path.read_text())

    def stopped(self, event, state=None, since=None, scope=None, initialized=False):
        # Allow interpreter/plugin startup independently of the cancellation bound.
        self.assertNotEqual(self.proc.wait(STARTUP_WAIT_SECONDS + 2), 0)
        launch_elapsed = time.monotonic() - self.started
        content = self.log_path.read_text()
        events = [json.loads(line) for line in content.splitlines() if line.startswith("{")]
        self.assertIn(event, [item["event"] for item in events], content)
        stop = next(item for item in events if item["event"] == event)
        # Deadline cleanup starts at expiry; guard/signal cleanup starts at the
        # test's actual injection. Neither includes unrelated process startup.
        elapsed = time.time() - stop["observed_at"] if since is None else time.monotonic() - since
        self.assertLess(elapsed, 3, content)
        if scope:
            self.assertTrue(any(item["event"] == event and item.get("scope") == scope for item in events), content)
        started = next(item for item in events if item["event"] == "supervisor_started")
        deadline_elapsed = None
        if event == "supervisor_deadline_stop":
            initialization = stop["scope"] == "initialization"
            beginning = started if initialization else next(
                item for item in reversed(events) if item["event"] == "layer_fetch_start")
            budget = started["initialization_deadline_seconds" if initialization else "layer_deadline_seconds"]
            deadline_elapsed = stop["observed_at"] - beginning["observed_at"]
            self.assertGreaterEqual(deadline_elapsed, budget - .05, content)
            self.assertLess(deadline_elapsed, budget + .5, content)
        self.assertEqual('"event": "export_ready"' in content, initialized, content)
        self.assertIn("supervisor_stopped", [item["event"] for item in events])
        leader = started["child_pid"]
        with self.assertRaises(ProcessLookupError):
            os.killpg(leader, 0)
        artifacts = Path(os.environ.get("ARTIFACT_DIR", "/tmp"))
        with (artifacts / "offline-cancellation-telemetry.jsonl").open("a") as output:
            output.write(json.dumps({"test": self.id(), "seconds_to_stop": round(elapsed, 3),
                                    "launch_to_stop_seconds": round(launch_elapsed, 3),
                                    "stop_clock": ("deadline_expiry" if since is None else "blocked_http"
                                                   if event == "supervisor_deadline_stop" else "injected_guard_or_signal"),
                                    "deadline_elapsed_seconds": round(deadline_elapsed, 3) if deadline_elapsed is not None else None,
                                    "body_bytes_sent": state["body_bytes"] if state else None,
                                    "process_group_gone": True, "log": content}) + "\n")
        return events

    def test_slow_drip_initialization_layer_deadline(self):
        with stalled_registry(self.blobs, "drip") as (url, state):
            self.launch(url)
            self.wait_entered(state)
            self.stopped("supervisor_deadline_stop", state, scope="layer")
            self.assertGreaterEqual(state["body_bytes"], 3)
            self.assertLess(state["body_bytes"], 100)

    def test_hung_headers_open_layer_deadline(self):
        with stalled_registry(self.blobs, "headers") as (url, state):
            self.launch(url)
            self.wait_entered(state)
            self.stopped("supervisor_deadline_stop", state, scope="layer")
            self.assertEqual(state["body_bytes"], 0)

    def test_initialization_has_its_own_deadline(self):
        with stalled_registry(self.blobs, "drip") as (url, state):
            # Leave enough room for real plugin imports, then prove that the
            # total startup budget expires before this longer layer budget.
            self.launch(url, layer=10, init=5)
            self.wait_entered(state)
            self.stopped("supervisor_deadline_stop", state, scope="initialization")
            self.assertGreaterEqual(state["body_bytes"], 3)

    def test_low_guard_interrupts_open_during_initialization(self):
        with stalled_registry(self.blobs, "headers") as (url, state):
            self.launch(url, layer=2)
            self.wait_entered(state)
            since = time.monotonic()
            write_space(self.space, RESERVE - 1)
            self.stopped("guard_stop", state, since=since)

    def test_stale_guard_interrupts_drip_during_initialization(self):
        with stalled_registry(self.blobs, "drip") as (url, state):
            self.launch(url, layer=2)
            self.wait_entered(state)
            time.sleep(.1)
            since = time.monotonic()
            write_space(self.space, observed=time.time() - 21)
            self.stopped("guard_stop", state, since=since)
            self.assertGreaterEqual(state["body_bytes"], 3)

    def cold_read(self, guard_failure):
        # Planning loads layers 0/1. RAW offset 0 maps to uncached layer 3.
        cold = self.pins.layers[3].digest[7:]
        with stalled_registry(self.blobs, "drip", cold) as (url, state):
            self.launch(url, layer=2 if guard_failure else .5)
            self.wait_ready()
            done, result = threading.Event(), []

            def read():
                handle = nbd.NBD()
                try:
                    handle.connect_unix(str(self.root / "disk.sock"))
                    try:
                        result.append(handle.pread(512, 0))
                    except nbd.Error:
                        result.append("NBD error")
                finally:
                    try:
                        handle.shutdown()
                    except nbd.Error:
                        pass
                    del handle
                    done.set()

            worker = threading.Thread(target=read, daemon=True)
            worker.start()
            self.wait_entered(state)
            since = time.monotonic()
            if guard_failure:
                write_space(self.space, RESERVE - 1)
            self.stopped("guard_stop" if guard_failure else "supervisor_deadline_stop", state,
                         since=since, scope=None if guard_failure else "layer", initialized=True)
            self.assertTrue(done.wait(1), "blocked NBD client was not disconnected")
            worker.join(1)
            self.assertEqual(result, ["NBD error"], "no partial/successful NBD bytes may escape")

    def test_deadline_interrupts_active_nbd_read_without_partial_response(self):
        self.cold_read(False)

    def test_guard_interrupts_active_nbd_read_without_partial_response(self):
        self.cold_read(True)

    def test_signal_during_initialization_reaps_child(self):
        with stalled_registry(self.blobs, "headers") as (url, state):
            self.launch(url, layer=2)
            self.wait_entered(state)
            since = time.monotonic()
            self.proc.send_signal(signal.SIGTERM)
            self.stopped("supervisor_signal_stop", state, since=since)

    def test_term_ignoring_child_and_descendant_killed_and_reaped(self):
        descendant = "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)"
        child = ("import json,signal,subprocess,sys,time; "
                 "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                 f"p=subprocess.Popen([sys.executable,'-c',{descendant!r}]); "
                 "print(json.dumps({'event':'test_descendant','pid':p.pid}),flush=True); time.sleep(30)")
        supervisor = ("import sys; from serve import supervise; from streamed_raw import HostSpaceGuard; "
                      f"sys.exit(supervise([sys.executable,'-c',{child!r}],HostSpaceGuard({str(self.space)!r}),"
                      "layer_seconds=2,init_seconds=.6,grace=.15))")
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            self.started = time.monotonic()
            self.proc = subprocess.Popen([sys.executable, "-c", supervisor], stdout=self.log, stderr=subprocess.STDOUT)
            events = self.stopped("supervisor_deadline_stop", scope="initialization")
            self.assertIn("supervisor_kill", [event["event"] for event in events])
            self.assertIn("supervisor_group_reaped", [event["event"] for event in events])
            descendant_pid = next(event["pid"] for event in events if event["event"] == "test_descendant")
            self.assertFalse(Path(f"/proc/{descendant_pid}").exists(), "descendant or zombie survived")
            self.assertIsNone(unrelated.poll(), "unrelated process must remain alive")
        finally:
            unrelated.terminate()
            unrelated.wait(1)

    def test_bare_plugin_is_refused_before_http(self):
        with stalled_registry(self.blobs, "headers") as (url, state):
            command = ["nbdkit", "-f", "-r", "--log=stderr", "-U", str(self.root / "disk.sock"),
                       "python", str(Path(__file__).with_name("nbdkit_streamed.py")),
                       f"manifest={self.root / 'manifest.json'}", f"config={self.root / 'config.json'}",
                       f"host-space={self.space}", f"fixture-url={url}",
                       f"manifest-digest={self.pins.manifest_digest}"]
            self.proc = subprocess.Popen(command, stdout=self.log, stderr=subprocess.STDOUT)
            self.assertNotEqual(self.proc.wait(2), 0)
            self.assertIn("requires the serve.py supervisor", self.log_path.read_text())
            self.assertEqual(state["requests"], 0)

    def test_limits_cannot_be_relaxed(self):
        self.assertEqual(LAYER_SECONDS, 900.0)
        self.assertEqual(INIT_SECONDS, 3600.0)
        for maximum in (LAYER_SECONDS, INIT_SECONDS, KILL_GRACE_SECONDS):
            self.assertEqual(bounded_seconds(str(maximum), maximum), maximum)
            for value in (maximum + .001, "nan", "inf", 0, -1):
                with self.subTest(value=value, maximum=maximum), self.assertRaises(argparse.ArgumentTypeError):
                    bounded_seconds(value, maximum)
