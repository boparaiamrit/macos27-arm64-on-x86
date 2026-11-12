"""Resource evidence around only the named offline fixture suite."""
import json
import os
from pathlib import Path
import resource
import runpy
import sys
import time

suite, script = sys.argv[1:]
if suite not in ("legacy", "large-cache"):
    raise SystemExit("unknown offline suite")
resource.setrlimit(resource.RLIMIT_AS, (512 << 20, 512 << 20))
sys.path.insert(0, str(Path(script).parent))
started = time.monotonic()
status = None
try:
    runpy.run_path(script, run_name="__main__")
except SystemExit as exc:
    status = exc.code
    raise
finally:
    memory_peak = int(Path("/sys/fs/cgroup/memory.peak").read_text())
    report = {"suite": suite, "exit_code": status, "seconds": round(time.monotonic() - started, 3),
              "cgroup_memory_max": Path("/sys/fs/cgroup/memory.max").read_text().strip(),
              "cgroup_cpu_max": Path("/sys/fs/cgroup/cpu.max").read_text().strip(),
              "cgroup_memory_peak_bytes": memory_peak,
              "within_1gib_actual_memory_bound": memory_peak <= 1 << 30,
              "per_process_address_space_limit_bytes": 512 << 20,
              "self_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "child_peak_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}
    Path(os.environ["ARTIFACT_DIR"], suite + "-resources.json").write_text(json.dumps(report, indent=2) + "\n")
    if memory_peak > 1 << 30:
        raise SystemExit("offline fixture exceeded the 1GiB actual memory bound")
