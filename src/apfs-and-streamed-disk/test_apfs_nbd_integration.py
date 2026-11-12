"""Offline Apple restore APFS -> nbdkit file -> NBDSource integration.

Run with host Python; Docker is the only execution environment for the reader.
Only this test and apfs-nbd-integration evidence are written on the host.
The image is pinned before launch so concurrent image rebuilds cannot swap it.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import struct
import subprocess
import sys
import time
import traceback
import uuid


FROZEN_HASHES = {
    "oci_stream.py": "d14f7f083db4aa1c3f5f39a2faa958d75cdd8b7319b083546594a8bdffc62008",
    "asif_plan.py": "49f5ea5b5554207400fa95a5f5c93934947d570e896dda97cf8efe715f53988e",
    "asif_to_raw.py": "e4d8f2a1c314c0ba395a85043992a0055bab4ea40ad1baf961f3a35d260c06e4",
}
GIB = 1024**3
RAMDISK_BYTES = 373293056


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024**2), b""):
            digest.update(block)
    return digest.hexdigest()


def emit(event, **values):
    print(json.dumps({"event": event, **values}, sort_keys=True), flush=True)


def inside():
    """One server, two real adapter sessions; never invoke converter or guest."""
    started = time.monotonic()
    report = {"status": "FAIL", "started_at": datetime.now(timezone.utc).isoformat()}
    server = None
    sources = []
    phase = {"name": "setup", "path": None}
    compression = []
    decodes = []
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("90s integration deadline")))
    signal.alarm(90)
    try:
        parent = Path("/parent")
        ramdisk = parent / "darwin/firmware/ramdisk.dmg"
        require(ramdisk.stat().st_size == RAMDISK_BYTES, "unexpected restore RAMdisk size")
        report["input"] = {"path": str(ramdisk), "bytes": RAMDISK_BYTES,
                           "sha256": file_hash(ramdisk)}
        snapshot = Path(os.environ["CONVERTER_SNAPSHOT"])
        actual = {name: file_hash(snapshot / name) for name in FROZEN_HASHES}
        report["frozen_hashes"] = actual
        require(actual == FROZEN_HASHES, "frozen converter hashes differ from reviewed constants")
        require(json.loads((snapshot / "reviewed-sha256.json").read_text()) == FROZEN_HASHES,
                "reviewed hash manifest differs from exact three pinned hashes")

        import nbd_source
        import frozen
        import fs_explorer as fs
        import guest_artifacts
        from fs_explorer.filesystems import decmpfs
        from unittest.mock import patch

        require(frozen.EXPECTED == FROZEN_HASHES, "NBDSource frozen loader pins changed")
        require(frozen.SNAPSHOT.resolve() == snapshot.resolve(), "wrong converter snapshot imported")
        require(frozen.APFS.resolve() == (parent / "apfs-tools/src").resolve(), "wrong APFS staging")
        modules = {"nbd_source": nbd_source, "frozen": frozen, "fs_explorer": fs,
                   "guest_artifacts": guest_artifacts, "decmpfs": decmpfs,
                   "oci_stream": frozen.oci, "asif_plan": frozen.planner,
                   "asif_to_raw": frozen.converter}
        report["modules"] = {}
        for name, module in modules.items():
            path = Path(module.__file__).resolve()
            require(path.is_relative_to(parent), f"{name} imported outside read-only staging")
            report["modules"][name] = {"path": str(path), "sha256": file_hash(path)}
        report["test_sha256"] = file_hash(__file__)
        report["nbdkit_version"] = subprocess.check_output(["nbdkit", "--version"], text=True).strip()
        report["python"] = {"executable": sys.executable, "version": sys.version}

        class CountedSource(nbd_source.NBDSource):
            def __init__(self, socket, label):
                self.metrics = {"session": label, "read_calls": 0, "bytes_returned": 0,
                                "max_requested_bytes": 0}
                self.transcript = hashlib.sha256()
                super().__init__(socket)
                sources.append(self)

            def read_at(self, offset, length):
                data = super().read_at(offset, length)
                self.metrics["read_calls"] += 1
                self.metrics["bytes_returned"] += len(data)
                self.metrics["max_requested_bytes"] = max(self.metrics["max_requested_bytes"], length)
                self.transcript.update(struct.pack("<QQQ", offset, length, len(data)))
                self.transcript.update(data)
                return data

        # Observation only: each wrapper calls the staged decoder unchanged.
        original_open, original_decode = decmpfs.open_compressed, decmpfs._decode

        def observe_open(xattr, resource_fork, ctx):
            magic, kind, logical_bytes = struct.unpack_from("<4sIQ", xattr)
            compression.append({**phase, "magic_hex": magic.hex(), "type": kind,
                                "logical_bytes": logical_bytes, "attribute_bytes": len(xattr),
                                "payload_prefix_hex": xattr[16:24].hex()})
            return original_open(xattr, resource_fork, ctx)

        def observe_decode(codec, data, out_size, ctx):
            output = original_decode(codec, data, out_size, ctx)
            decodes.append({**phase, "codec": codec, "input_bytes": len(data),
                            "input_prefix_hex": data[:8].hex(), "output_bytes": len(output),
                            "output_sha256": hashlib.sha256(output).hexdigest()})
            return output

        socket = Path("/tmp/apfs-nbd-integration.sock")
        command = ["nbdkit", "--foreground", "--readonly", "--threads", "1",
                   "--unix", str(socket), "file", str(ramdisk)]
        report["server_command"] = command
        server = subprocess.Popen(command, stdout=subprocess.DEVNULL)
        deadline = time.monotonic() + 5
        while not socket.exists():
            require(server.poll() is None, "nbdkit exited before its socket was ready")
            require(time.monotonic() < deadline, "nbdkit Unix socket startup exceeded 5s")
            time.sleep(0.02)

        with patch.object(decmpfs, "open_compressed", observe_open), patch.object(decmpfs, "_decode", observe_decode):
            phase.update(name="common_discover", path=None)
            progress = []
            with CountedSource(socket, "common_discover") as source:
                require(source.getsize() == RAMDISK_BYTES, "NBD export size mismatch")
                require(source._h.is_read_only(), "NBD export is writable")
                require(source.read_at(32, 4) == b"NXSB", "RAMdisk is not raw APFS")
                census, candidates = guest_artifacts.discover(source, progress=progress.append)
            report["discovery"] = {"census": census, "progress": progress,
                                   "firmware_candidate_count": len(candidates)}
            require(candidates == [], "restore unexpectedly contains a firmware candidate")
            roots = [entry["root"] for entry in census]
            require(roots and roots[0] == "/" and len(roots) == len(set(roots)), "invalid traversal roots")
            require(all("unsupported" not in entry for entry in census), "unsupported filesystem in census")
            expected_roots = {"/"} | {entry["path"] for volume in census
                                             for entry in volume["entries"] if entry["type"] == "volume"}
            require(set(roots) == expected_roots, "discover did not traverse all exposed volumes")
            require([event["root"] for event in progress if event["event"] == "inspect_volume"] == roots,
                    "discover progress differs from volume census")
            emit("common_discover_pass", roots=roots, firmware_candidates=0)

            versions = []
            missing_firmware = []
            with CountedSource(socket, "direct_fs_explorer") as source:
                with fs.open_source(source, backend="pure", threads=1, system_files=True,
                                    cache_size=128 * 1024**2, spool_limit=0) as image:
                    require(image._phys is source, "fs_explorer did not accept NBDSource directly")
                    for root in roots:
                        prefix = root.rstrip("/")
                        path = prefix + guest_artifacts.VERSION
                        phase.update(name="direct_version", path=path)
                        try:
                            entry = image.stat(path)
                            require(entry.format == "apfs", "SystemVersion was not read from APFS")
                            data = image.read_file(path, max_size=1024**2, verify=True)
                        except fs.TargetNotFoundError:
                            continue
                        version = plistlib.loads(data)
                        versions.append({"root": root, "path": path, "bytes": len(data),
                                         "sha256": hashlib.sha256(data).hexdigest(),
                                         "plist": version, "entry": entry.to_dict()})
                        require(version.get("ProductVersion") == "27.0.1", "incorrect restore ProductVersion")
                        require(version.get("ProductBuildVersion") == "26A434", "incorrect restore build")
                        phase.update(name="direct_firmware", path=prefix + guest_artifacts.FIRMWARE)
                        try:
                            image.read_file(phase["path"], max_size=32 * 1024**2, verify=True)
                        except fs.TargetNotFoundError:
                            missing_firmware.append(phase["path"])
                        else:
                            raise AssertionError("Virtualization.framework firmware unexpectedly present")
            report["system_versions"] = versions
            report["missing_firmware_paths"] = missing_firmware
            require(len(versions) == 1, "expected exactly one actual restore SystemVersion")
            require(len(missing_firmware) == 1, "firmware absence was not independently confirmed")
            plist_hash = versions[0]["sha256"]
            require(any(event["name"] == "direct_version" and event["type"] == 9
                        for event in compression), "real SystemVersion did not exercise decmpfs type 9")
            for name in ("common_discover", "direct_version"):
                require(any(event["name"] == name and event["codec"] == "raw_cc"
                            and event["input_prefix_hex"].startswith("cc")
                            and event["input_bytes"] == event["output_bytes"] + 1
                            and event["output_sha256"] == plist_hash for event in decodes),
                        f"{name} did not decode the actual stored-raw plist correctly")
            emit("system_version_pass", product_version="27.0.1", build="26A434", sha256=plist_hash)
        report["status"] = "PASS"
    except BaseException as error:
        report["error"] = {"type": type(error).__name__, "message": str(error),
                           "traceback": traceback.format_exc()}
    finally:
        signal.alarm(0)
        for source in sources:
            source.close()
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=2)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=2)
        report["reads"] = [{**source.metrics, "transcript_sha256": source.transcript.hexdigest()}
                           for source in sources]
        report["compression_observations"] = compression
        report["decode_observations"] = decodes
        report["tmp_entries"] = sorted(path.name for path in Path("/tmp").iterdir())
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        emit("apfs_nbd_integration_result", **report)
    return 0 if report["status"] == "PASS" else 1


def host():
    arm = Path(__file__).resolve().parents[1]
    evidence = arm / "full-system/apfs-nbd-integration"
    evidence.mkdir(exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = evidence / run_id
    space = shutil.disk_usage(arm).free
    require(space >= 10 * GIB, "host has less than the mandatory 10 GiB floor")
    inspected = json.loads(subprocess.check_output(
        ["docker", "image", "inspect", "macos-streamed-guest:local"], text=True, timeout=5))[0]
    image_id = inspected["Id"]
    name = "apfs-nbd-integration-" + uuid.uuid4().hex[:12]
    command = ["docker", "run", "--rm", "--name", name, "--network", "none", "--ipc", "none",
               "--read-only", "--memory", "1g", "--memory-swap", "1g", "--cpus", "2",
               "--pids-limit", "128", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=1048576,mode=0700",
               "--mount", f"type=bind,source={arm},target=/parent,readonly",
               "--env", "CONVERTER_SNAPSHOT=/parent/full-system/converter-snapshot",
               "--env", "APFS_TOOLS_SRC=/parent/apfs-tools/src",
               "--env", "PYTHONPATH=/parent/apfs-tools/src:/parent/streamed-disk:/parent/full-system",
               "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "PYTHONUNBUFFERED=1",
               "--workdir", "/parent/full-system", "--entrypoint", "/usr/bin/timeout", image_id,
               "--signal=KILL", "100s", "/usr/bin/python3", "-B",
               "/parent/full-system/test_apfs_nbd_integration.py", "--inside"]
    run = {"command": command, "container_name": name, "image_id": image_id,
           "image_created": inspected["Created"], "windows_free_bytes_before": space,
           "minimum_windows_free_bytes": space, "host_timeout_seconds": 105,
           "container_timeout_seconds": 100, "python_deadline_seconds": 90,
           "test_sha256": file_hash(__file__)}
    started = time.monotonic()
    with stem.with_suffix(".log").open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        try:
            while proc.poll() is None:
                free = shutil.disk_usage(arm).free
                run["minimum_windows_free_bytes"] = min(run["minimum_windows_free_bytes"], free)
                require(free >= 10 * GIB, "host crossed mandatory 10 GiB reserve")
                require(time.monotonic() - started < 105, "host integration exceeded 105s")
                time.sleep(0.2)
            run["exit_code"] = proc.returncode
        except BaseException as error:
            run["host_error"] = f"{type(error).__name__}: {error}"
            subprocess.run(["docker", "kill", name], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=5, check=False)
            proc.kill()
            proc.wait(timeout=3)
            run["exit_code"] = 1
    run["elapsed_seconds"] = round(time.monotonic() - started, 3)
    run["windows_free_bytes_after"] = shutil.disk_usage(arm).free
    text = stem.with_suffix(".log").read_text(encoding="utf-8")
    reports = []
    for line in text.splitlines():
        if line.startswith("{"):
            event = json.loads(line)
            if event.get("event") == "apfs_nbd_integration_result":
                reports.append(event)
    run["result"] = reports[-1] if reports else {"status": "FAIL", "error": "no container result"}
    run["log_sha256"] = file_hash(stem.with_suffix(".log"))
    stem.with_suffix(".json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    print(text, end="")
    print(f"Evidence: {stem.with_suffix('.json')}")
    return 0 if run["exit_code"] == 0 and run["result"]["status"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    sys.exit(inside() if args.inside else host())
