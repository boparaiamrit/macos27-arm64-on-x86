Golden live5 preparation finished BLOCKED at 2026-10-27T19:31:15.181+05:30.

The exact authorized command was run once from `<WORKSPACE>/macos` and allowed to exit on its own with code 1:

```text
python -B test-output/arm-macos/full-system/live-preparation/execute-bounded.py --server 3689f3ebdeeb08dbdac05341812a1aa48a7d653b1b6ac5d2658d9b5adaa4bdaf --socket /stream/golden-live5.nbd --ready-name stream-ready-live5.json
```

The first recorded failure is `fs_explorer.errors.CorruptDataError: apfs: checksum mismatch in fs tree` (`helper.stderr.log:37`). The first monitor failure event is `bounded_preparation_blocked` at 2026-10-27T14:01:14.739+00:00. The helper exited with code 1; OOMKilled was false. Its stack reached `guest_artifacts.py:28`, `list(image.entries(root, recursive=0, stat=False))`, while inspecting `/p2/v1`. The APFS fs-tree root path raised the checksum error at `fs_explorer/filesystems/apfs/btree.py:108`. The underlying cause remains unresolved; this report records the checksum rejection without inferring image corruption or a reader fix.

The last discovery marker is `inspect_volume` for `/p2/v1` (`helper.stdout.log:78`). There is no `volume_entries_read` marker for that root. Eight earlier roots emitted entry-count markers: / (3), /p1 (4), /p2 (6), /p3 (2), /p1/v1 (5), /p1/v2 (0), /p1/v3 (3), /p1/v4 (0). Eight `system_version_read` markers appeared, but no product/build values were observed. No firmware-read marker, candidate output, or completed census artifact was produced.

The final matching read pair is preserved verbatim at `helper.stdout.log:85-86`:

```json
{"event": "nbd_read_start", "read_id": 30, "offset": 1532690432, "length": 65536}
{"event": "nbd_read_end", "read_id": 30, "returned": 65536, "elapsed_seconds": 169.084804}
```

All 30 read starts have matching read ends; there are 0 NBD read-error events. Read 30 returned the full 65,536 bytes before the APFS checksum failure. The final backend event was layer 26 verified in 169.078 seconds at 2026-10-27T14:01:13.444+00:00, bringing cumulative fetched compressed bytes to 7,931,718,921. This timing is adjacent evidence, not a determination of the checksum mismatch's cause.

Export readiness was observed 1052.068487 seconds after server start (17 minutes 32.07 seconds), with 8 verified fetches over 7 distinct layers. The monitor validated the event at 2026-10-27T13:38:50.365+00:00. Preparation ran for 1342.413540 seconds (22 minutes 22.41 seconds). Monitor wall time was 2013.736729 seconds; server-start-to-finish was 2402.907406 seconds. The helper ended before its 3,600-second limit.

Final backend counts were 18 fetch attempts and 18 verified fetches across 10 distinct indices: [0, 26, 48, 49, 50, 52, 53, 55, 59, 63]. These include refetches. Full verification of all 67 disk layers was not performed. The socket was `/stream/golden-live5.nbd`; the image was `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`. The pinned manifest, config and semantic plan digest matched the live5 readiness record.

The existing host-space guard remained in force: 10 GiB floor and 20-second freshness limit. Across 1133 recorded samples, minimum free space was 37,020,905,472 bytes (34.478 GiB), and maximum sample age was 2.956213 seconds. No guard stop occurred.

Before/after inventory contains no guest top-level files and no `/guest/boot` directory. Installed Golden product/build, candidate volume, original firmware size/hash/header, and bytes at `0x2314` remain unobserved. No firmware was patched, no guest was executed, and no local full RAW or checkpoint was created. This attempt provides no Golden desktop result.

Post-run hashing confirmed manifest/config/AUX and all four source/plan files recorded by the monitor match their start hashes. AUX remains 33,562,780 bytes, SHA-256 `2ca2b332f05e2d6e3663bb4db0982a5feec268a8d1b91460f140ad8d3cb49414`. Config body and ECID were not printed or added to this report.

Final read-only inspection found backend running: True; sampler PID 32072 running: True. Helper final state was exited with code 1; its current inspection is recorded in `handoff.json`. Backend and sampler were left untouched for the parent. No additional watcher or replacement helper was started, and no retry, source change, host cleanup, firmware patch, QEMU, VM, or GUI action was performed.

Review `summary.json`, `helper.stdout.log`, `helper.stderr.log`, `server.stderr.log`, `validated-inputs.json`, `preparation-before.json`, `preparation-after.json`, `host-guard-samples.jsonl`, and `handoff.json` in this run folder. Parent review of the `/p2/v1` fs-tree checksum failure is the next decision; no bypass or reader optimization was attempted.
