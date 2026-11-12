"""Read-only imports of the reviewed converter; never run its conversion CLI."""
import hashlib
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SNAPSHOT = Path(os.environ.get("CONVERTER_SNAPSHOT", ROOT.parent / "full-system/converter-snapshot"))
APFS = Path(os.environ.get("APFS_TOOLS_SRC", ROOT.parent / "apfs-tools/src"))
EXPECTED = {
    "oci_stream.py": "d14f7f083db4aa1c3f5f39a2faa958d75cdd8b7319b083546594a8bdffc62008",
    "asif_plan.py": "49f5ea5b5554207400fa95a5f5c93934947d570e896dda97cf8efe715f53988e",
    "asif_to_raw.py": "e4d8f2a1c314c0ba395a85043992a0055bab4ea40ad1baf961f3a35d260c06e4",
}
sys.dont_write_bytecode = True
for name, expected in EXPECTED.items():
    if hashlib.sha256((SNAPSHOT / name).read_bytes()).hexdigest() != expected:
        raise RuntimeError(f"reviewed converter hash mismatch: {name}")
sys.path[:0] = [str(SNAPSHOT), str(APFS)]
import oci_stream as oci
import asif_plan as planner
import asif_to_raw as converter
