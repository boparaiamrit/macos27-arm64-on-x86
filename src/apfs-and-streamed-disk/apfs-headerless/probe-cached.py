"""Optional single-range reader check. No guest traversal; metadata result only."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time
from types import SimpleNamespace

IMAGE = "sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635"
SERVER = "3689f3ebdeeb08dbdac05341812a1aa48a7d653b1b6ac5d2658d9b5adaa4bdaf"
RANGE_SHA = "8b26de163d14d85e68e0b0659631776286d46522723d5df3d32d5a39198322fe"
HERE = Path(__file__).resolve().parent
ARM = HERE.parents[1]


def guard():
    sample = json.loads((ARM / "full-system/host-space-live.json").read_text())
    age = time.time() - sample["observed_at"]
    assert 0 <= age <= 20 and sample["free_bytes"] >= 10 * 1024**3, "host guard stale/low"
    return {**sample, "age_seconds": age}


def inside():
    from nbd_source import NBDSource
    from fs_explorer.filesystems.apfs.btree import BTree, NodeFormat, check_object
    from fs_explorer.filesystems.apfs.container import Container
    from fs_explorer.filesystems.apfs.fs import APFSVolume, fs_keyfn
    from fs_explorer.filesystems.apfs.omap import Mapping
    from fs_explorer.io.cache import Cache
    from fs_explorer.io.source import BytesRA

    before = guard()
    started = time.monotonic()
    with NBDSource("/stream/golden-live5.nbd") as source:
        data = source.read_at(1532690432, 65536)  # The only guest read.
    assert len(data) == 65536 and hashlib.sha256(data).hexdigest() == RANGE_SHA
    imeta = data[40960:45056]
    rootdata = data[45056:49152]
    oid, xid, kind, _ = check_object(imeta, "cached integrity metadata")
    assert kind & 0xffff == 0x1e
    # RAM-only harness for the real bytes: this is explicitly NOT a recovered
    # guest OMAP mapping. The failed process's mapping is still unobserved.
    c = Container.__new__(Container)
    c.ra = BytesRA(imeta + rootdata)
    c.block_size, c.nblocks = 4096, 2
    c.ctx = SimpleNamespace(cache=Cache())
    c.token = c.ctx.cache.token()
    volume = APFSVolume.__new__(APFSVolume)
    volume.c, volume.xid, volume.vek = c, xid, None
    volume._vsb = bytearray(4096)
    struct.pack_into("<Q", volume._vsb, 0x400, oid)

    def ram_mapping(requested, transaction, what):
        assert requested == oid and transaction == xid
        return Mapping(0, 4096, 0)

    volume.omap = SimpleNamespace(resolve=ram_mapping)
    algorithm, expected = volume._integrity_meta()
    context = NodeFormat(noheader=True, hashed=True, root=True, tree_type=2, node_size=4096,
                         mapping_flags=8, hash_type=algorithm)
    root = c.load_node(1, fs_keyfn(True), None, "cached sealed root", context=context)

    def no_children(*args):
        raise AssertionError("live child traversal prohibited")

    tree = BTree(root, no_children, "cached sealed root", hash_type=algorithm, root_hash=expected)
    after = guard()
    print(json.dumps({"status": "PASS", "offset": 1532690432, "length": len(data), "guest_read_calls": 1,
                      "range_sha256": RANGE_SHA, "integrity_checksum": True, "hash_type": algorithm,
                      "root_hash": expected.hex(), "actual_root_sha256": hashlib.sha256(root.data).hexdigest(),
                      "root_flags": root.flags, "root_level": root.level, "root_nkeys": root.nkeys,
                      "index_value_lengths": [len(root.val(i)) for i in range(root.nkeys)],
                      "tree_flags": tree.info[0], "payload_saved": False, "children_traversed": 0,
                      "real_volume_omap_recovered": False, "guard_before": before, "guard_after": after,
                      "elapsed_seconds": time.monotonic() - started}, sort_keys=True))


def host():
    for label in ("offline-final", "restore-final"):
        assert json.loads((HERE / (label + ".json")).read_text())["exit_code"] == 0, "offline pass required"
    expected_sources = json.loads((HERE / "offline-final.json").read_text())["source_hashes_after"]
    assert all(hashlib.sha256((ARM / name).read_bytes()).hexdigest() == value
               for name, value in expected_sources.items()), "sources changed since offline PASS"
    assert shutil.disk_usage(ARM).free >= 10 * 1024**3
    before = guard()
    inspected = json.loads(subprocess.check_output(["docker", "inspect", SERVER], timeout=5))[0]
    assert inspected["State"]["Running"] and inspected["Image"] == IMAGE

    def fetches():
        logs = subprocess.run(["docker", "logs", SERVER], capture_output=True, text=True, timeout=5, check=True)
        events = []
        for line in (logs.stdout + logs.stderr).splitlines():
            if line.startswith("{"):
                event = json.loads(line)
                if event.get("event") == "layer_verified":
                    events.append(event)
        assert events
        return events[-1]

    fetch_before = fetches()
    assert fetch_before["fetch_count"] == 18
    name = "apfs-headerless-cached-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
    cmd = ["docker", "run", "--rm", "--name", name, "--network", "none", "--ipc", "none", "--read-only",
           "--memory", "256m", "--memory-swap", "256m", "--cpus", "1", "--pids-limit", "64",
           "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
           "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=1048576,mode=0700",
           "--mount", f"type=bind,source={ARM},target=/parent,readonly",
           "--mount", "type=volume,source=macos-golden-stream-state,target=/stream,readonly",
           "--env", "CONVERTER_SNAPSHOT=/parent/full-system/converter-snapshot",
           "--env", "APFS_TOOLS_SRC=/parent/apfs-tools/src",
           "--env", "PYTHONPATH=/parent/apfs-tools/src:/parent/streamed-disk:/parent/full-system",
           "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "PYTHONUNBUFFERED=1",
           "--workdir", "/parent/full-system", "--entrypoint", "/usr/bin/timeout", IMAGE,
           "--signal=TERM", "--kill-after=5s", "240s", "/usr/bin/python3", "-B",
           "/parent/full-system/apfs-headerless/probe-cached.py", "--inside"]
    result = {"command": cmd, "guard_before": before, "sources": expected_sources,
              "fetch_before": fetch_before, "backend_started_at": inspected["State"]["StartedAt"]}
    started = time.monotonic()
    with (HERE / "cached-probe.log").open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        try:
            while proc.poll() is None:
                guard()
                assert time.monotonic() - started < 250, "host deadline"
                time.sleep(.2)
            result["exit_code"] = proc.returncode
        except BaseException:
            subprocess.run(["docker", "kill", name], timeout=5, check=False)
            proc.kill()
            proc.wait(timeout=3)
            raise
    result.update(guard_after=guard(), fetch_after=fetches(), elapsed_seconds=time.monotonic() - started)
    result["additional_layer_fetches"] = result["fetch_after"]["fetch_count"] - fetch_before["fetch_count"]
    (HERE / "cached-probe.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print((HERE / "cached-probe.log").read_text())
    assert result["exit_code"] == 0 and result["additional_layer_fetches"] == 0


if __name__ == "__main__":
    inside() if "--inside" in sys.argv else host()
