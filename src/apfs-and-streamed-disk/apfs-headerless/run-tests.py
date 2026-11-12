"""Pinned, bounded, offline reader validation. Writes only this evidence directory."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ARM = HERE.parents[1]
IMAGE = "sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635"
label = sys.argv[1]
integration = "--integration" in sys.argv
test = "test_apfs_nbd_integration.py" if integration else "test_apfs_headerless.py"
sources = [ARM / "apfs-tools/src/fs_explorer/filesystems/apfs" / name for name in ("btree.py", "container.py", "fs.py")]
sources += [ARM / "apfs-tools/src/fs_explorer/containers/asif.py", ARM / "apfs-tools/src/fs_explorer/filesystems/decmpfs.py"]
sources += [ARM / "full-system/converter-snapshot" / name for name in ("oci_stream.py", "asif_plan.py", "asif_to_raw.py")]

def hashes():
    return {str(p.relative_to(ARM)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}

before = shutil.disk_usage(ARM).free
assert before >= 10 * 1024**3, "host below 10 GiB floor"
name = "apfs-headerless-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
cmd = ["docker", "run", "--rm", "--name", name, "--network", "none", "--ipc", "none", "--read-only",
       "--memory", "1g", "--memory-swap", "1g", "--cpus", "2", "--pids-limit", "128", "--cap-drop", "ALL",
       "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=1048576,mode=0700",
       "--mount", f"type=bind,source={ARM},target=/parent,readonly",
       "--env", "CONVERTER_SNAPSHOT=/parent/full-system/converter-snapshot",
       "--env", "APFS_TOOLS_SRC=/parent/apfs-tools/src",
       "--env", "PYTHONPATH=/parent/apfs-tools/src:/parent/streamed-disk:/parent/full-system",
       "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "PYTHONUNBUFFERED=1", "--workdir", "/parent/full-system",
       "--entrypoint", "/usr/bin/timeout", IMAGE, "--signal=KILL", "100s", "/usr/bin/python3", "-B",
       "/parent/full-system/" + test]
if integration:
    cmd += ["--inside"]
report = {"command": cmd, "source_hashes_before": hashes(), "free_before": before,
          "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "minimum_free": before}
started = time.monotonic()
with (HERE / (label + ".log")).open("w", encoding="utf-8") as log:
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
    try:
        while proc.poll() is None:
            free = shutil.disk_usage(ARM).free
            report["minimum_free"] = min(report["minimum_free"], free)
            assert free >= 10 * 1024**3, "host below 10 GiB floor"
            assert time.monotonic() - started < 105, "host deadline"
            time.sleep(.2)
        report["exit_code"] = proc.returncode
    except BaseException:
        subprocess.run(["docker", "kill", name], timeout=5, check=False)
        proc.kill()
        proc.wait(timeout=3)
        raise
report.update(elapsed_seconds=time.monotonic() - started, free_after=shutil.disk_usage(ARM).free,
              source_hashes_after=hashes())
assert report["free_after"] >= 10 * 1024**3
(HERE / (label + ".json")).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print((HERE / (label + ".log")).read_text(encoding="utf-8"))
sys.exit(report["exit_code"])
