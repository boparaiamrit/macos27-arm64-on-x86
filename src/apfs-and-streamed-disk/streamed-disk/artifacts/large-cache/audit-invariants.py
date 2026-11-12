"""Compare protected behavior to the required base image's original Python."""
import ast
import difflib
import json
from pathlib import Path

root = Path("/streamed-disk")
evidence = Path("/artifacts")
before = json.loads((evidence / "base-image-source.json").read_text(encoding="utf-8-sig"))
protected = {
    "streamed_raw.py": ["emit", "HostSpaceGuard", "GuardedSession", "CheckedStream", "GuardedBlobs",
                        "FixtureHTTPBlobs", "RawDisk", "VerifiedSource.get_layer"],
    "serve.py": ["group_exists", "stop_group", "bounded_seconds", "supervise"],
    "nbdkit_streamed.py": ["config", "thread_model", "get_ready", "stop_for_guard", "after_fork",
                           "open", "get_size", "block_size", "can_write", "can_multi_conn", "can_cache",
                           "can_trim", "can_zero", "pread", "pwrite", "cleanup"],
}


def find(tree, name):
    node = tree
    for part in name.split("."):
        node = next(n for n in node.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name == part)
    return ast.dump(node, include_attributes=False)


unchanged, diffs = [], []
for name, symbols in protected.items():
    old, new = before[name], (root / name).read_text()
    old_tree, new_tree = ast.parse(old), ast.parse(new)
    for symbol in symbols:
        assert find(old_tree, symbol) == find(new_tree, symbol), (name, symbol)
        unchanged.append(name + ":" + symbol)
    diffs.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                      fromfile="required-base/" + name, tofile="large-cache/" + name))
(evidence / "source-review.diff").write_text("".join(diffs))
(evidence / "invariant-audit.json").write_text(json.dumps({"status": "PASS", "unchanged_symbols": unchanged,
    "comparison": "AST of protected behavior against required base image source; packaged files already match host"}, indent=2) + "\n")
print("PASS: " + str(len(unchanged)) + " protected functions/classes unchanged against base image")
