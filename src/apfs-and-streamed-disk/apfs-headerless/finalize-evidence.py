"""Generate bounded patch/provenance evidence without modifying reader sources."""
import datetime
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARM = HERE.parents[1]
SRC = ARM / "apfs-tools/src/fs_explorer/filesystems/apfs"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


before = json.loads((HERE / "before.json").read_text())
offline = json.loads((HERE / "offline-final.json").read_text())
restore = json.loads((HERE / "restore-final.json").read_text())
live = json.loads((HERE / "cached-probe.json").read_text())
live_result = json.loads((HERE / "cached-probe.log").read_text().strip())
assert before["exit_code"] == 1 and offline["exit_code"] == restore["exit_code"] == live["exit_code"] == 0
assert live_result["status"] == "PASS" and live["additional_layer_fetches"] == 0
assert "Ran 29 tests" in (HERE / "offline-final.log").read_text()
changes = {}
diff = []
for name in ("btree.py", "container.py", "fs.py"):
    original = HERE / (name[:-3] + ".before.py")
    current = SRC / name
    relative = str(current.relative_to(ARM)).replace("\\", "/")
    assert sha(original) == before["source_hashes_before"][str(current.relative_to(ARM))]
    assert sha(current) == offline["source_hashes_after"][str(current.relative_to(ARM))]
    assert sha(current) == restore["source_hashes_after"][str(current.relative_to(ARM))]
    assert sha(current) == live["sources"][str(current.relative_to(ARM))]
    changes[relative] = {"original_sha256": sha(original), "patched_sha256": sha(current)}
    diff.extend(difflib.unified_diff(original.read_text().splitlines(keepends=True),
                                    current.read_text().splitlines(keepends=True),
                                    fromfile="a/" + relative, tofile="b/" + relative))
(HERE / "reader.patch").write_text("".join(diff), encoding="utf-8")
unchanged = {name.replace("\\", "/"): value for name, value in before["source_hashes_before"].items()
             if "/apfs/" not in name.replace("\\", "/")}
for name, value in unchanged.items():
    assert sha(ARM / name) == value
expected = {
    "apfs-tools/src/fs_explorer/containers/asif.py": "9c3d02b235d4808a97a688f1d6fd048d2113ad7fd26954224b7f1aeabf439505",
    "apfs-tools/src/fs_explorer/filesystems/decmpfs.py": "5d8a156c40ab91b1e824f0ded9b4ce1be6691aa97d857ab394127d23bf744171",
    "full-system/converter-snapshot/oci_stream.py": "d14f7f083db4aa1c3f5f39a2faa958d75cdd8b7319b083546594a8bdffc62008",
    "full-system/converter-snapshot/asif_plan.py": "49f5ea5b5554207400fa95a5f5c93934947d570e896dda97cf8efe715f53988e",
    "full-system/converter-snapshot/asif_to_raw.py": "e4d8f2a1c314c0ba395a85043992a0055bab4ea40ad1baf961f3a35d260c06e4",
}
assert unchanged == expected
test = ARM / "full-system/test_apfs_headerless.py"
existing_test = ARM / "full-system/test_apfs_nbd_integration.py"
assert sha(existing_test) == "125be7317b90788c11a04d8808f5d79420f4d7e322ece31d27929b25263c8a2d"
provenance = {
    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "scope": "APFS sealed/headerless B-tree reader; ignored test-output staging only",
    "upstream": json.loads((ARM / "apfs-tools/provenance.json").read_text()),
    "license": "BSD-3-Clause; original Copyright (c) 2026, Arthur Gouhier retained",
    "license_sha256": sha(ARM / "apfs-tools/LICENSE"),
    "implementation_origin": "Independent implementation from Apple format contracts and manufactured fixtures; no GPL code copied",
    "primary_format_contract": {
        "url": "https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf",
        "printed_pages": [20, 48, 54, 59, 123, 124, 125, 126, 127, 131, 132, 133, 150, 151, 152, 153, 155],
        "interpretation": "Keep zero obj_phys_t bytes and field offsets; resolve virtual OIDs by OMAP; hash entire node; digest occupies algorithm length within a maximum 64-byte field",
        "measured_compact_values": "Same pinned cached range has 16 kvloc_t index values of length 40 (8-byte OID and SHA256); unused padding can be omitted",
    },
    "modules": changes, "unchanged_required_modules": unchanged,
    "support_files": {"full-system/test_apfs_headerless.py": sha(test),
                      "full-system/test_apfs_nbd_integration.py": sha(existing_test),
                      **{str(path.relative_to(ARM)).replace("\\", "/"): sha(path) for path in HERE.glob("*.py")}},
    "patch": {"path": str((HERE / "reader.patch").relative_to(ARM)).replace("\\", "/"),
              "sha256": sha(HERE / "reader.patch")},
    "validation": {
        "pinned_image": "sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635",
        "before": "16 methods; normal lookup PASS; sealed root checksum rejection; failures=3 errors=11",
        "focused_final": "29 methods PASS, including algorithm/padding/filename-hash subcases",
        "ordinary_restore": "Unchanged 373293056-byte fixture integration PASS; decmpfs type9 stored-raw plist SHA256 554f47cd7e516cee24e2d919a2a7493abb21da0c4a773406ff5fcf3ffe8bca92",
        "live_cached_final": live_result,
        "additional_layer_fetches_all_bounded_probes": 0,
        "resource_envelope": "offline network-none read-only 2 CPUs/1GiB; live network-none read-only 1 CPU/256MiB, 240s TERM + 5s kill; private tmpfs",
        "evidence": ["full-system/apfs-headerless/" + name for name in
                     ("before.json", "before.log", "offline-final.json", "offline-final.log", "restore-final.json", "restore-final.log", "cached-probe.json", "cached-probe.log", "cached-probe-initial72.json", "cached-probe-initial72.log")],
    },
    "integrity_limits": [
        "Checks consistency against checksummed on-volume integrity metadata, not external seal/signature trust",
        "File data hashes and fext contents are not cryptographically authenticated by this B-tree-only change",
        "Filename CRC hashes remain separate from sealed-tree SHA hashes",
        "Headerless acceptance requires sealed context plus OMAP NOHEADER for virtual nodes, never zero-byte guessing",
        "No live children traversed and no exact failed live OMAP mapping recovered",
        "No full preparation/extraction, installed Golden version, firmware, guest execution or GUI established",
    ],
}
(ARM / "apfs-tools/headerless-patch-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"modules": changes, "unchanged": unchanged, "patch_sha256": sha(HERE / "reader.patch")}, indent=2))
