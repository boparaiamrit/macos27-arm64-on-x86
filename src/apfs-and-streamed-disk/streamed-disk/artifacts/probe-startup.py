"""Measure fixture launch separately from cancellation; never contact a live registry."""
import json
import os
from pathlib import Path
import signal
import sys
import time

sys.path.insert(0, "/streamed-disk")
from test_cancellation import Cancellation, stalled_registry

os.environ["STREAMED_DISK_TEST_MODE"] = "1"
signal.alarm(40)
records = []
for index in range(3):
    case = Cancellation("test_hung_headers_open_layer_deadline")
    case.setUp()
    try:
        with stalled_registry(case.blobs, "headers") as (url, state):
            case.launch(url, layer=2, init=10)
            until = time.monotonic() + 8
            while not state["entered"].wait(.01):
                if case.proc.poll() is not None or time.monotonic() >= until:
                    break
            entered_seconds = time.monotonic() - case.started
            if case.proc.poll() is None:
                case.proc.send_signal(signal.SIGTERM)
            returncode = case.proc.wait(3)
            record = {"probe": index, "entered": state["entered"].is_set(),
                      "launch_to_http_seconds": entered_seconds, "returncode": returncode,
                      "log": case.log_path.read_text()}
            records.append(record)
            print(json.dumps(record), flush=True)
    finally:
        case.tearDown()
Path(os.environ["ARTIFACT_DIR"], "startup-timings.json").write_text(json.dumps(records, indent=2) + "\n")
if not all(record["entered"] for record in records):
    raise SystemExit(1)
