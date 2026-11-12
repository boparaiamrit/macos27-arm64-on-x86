"""Offline diagnostic wrapper: retain each child's log before fixture cleanup."""
import json
import os
from pathlib import Path
import runpy
import sys
import time
import unittest

sys.path.insert(0, "/streamed-disk")
import test_streamed_disk
import test_cancellation

original_teardown = test_cancellation.Cancellation.tearDown


def capture_teardown(self):
    record = {
        "test": self.id(),
        "elapsed_seconds": time.monotonic() - getattr(self, "started", time.monotonic()),
        "returncode": self.proc.poll() if self.proc else None,
        "log": self.log_path.read_text(),
    }
    with (Path(os.environ["ARTIFACT_DIR"]) / "diagnostic-child-logs.jsonl").open("a") as output:
        output.write(json.dumps(record) + "\n")
    original_teardown(self)


test_cancellation.Cancellation.tearDown = capture_teardown
original_failure = unittest.TextTestResult.addFailure


def report_failure(self, test, error):
    original_failure(self, test, error)
    if hasattr(test, "log_path"):
        print("\nCHILD LOG FOR " + test.id() + ":\n" + test.log_path.read_text(), file=sys.stderr)


unittest.TextTestResult.addFailure = report_failure
runpy.run_path("/streamed-disk/test_streamed_disk.py", run_name="__main__")
