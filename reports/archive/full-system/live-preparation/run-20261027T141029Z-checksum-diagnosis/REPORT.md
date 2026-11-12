Read-only continuation of the Golden live5 APFS failure.

One bounded diagnostic process inside the existing backend used an identical copy of the existing NBDSource adapter. It read only the final 65,536-byte range from the failed preparation, at logical offset 1,532,690,432. The command had a 240-second TERM timeout and 5-second kill grace; the read completed in 0.129139 seconds. The host-space sample was 0.191753 seconds old with 36,811,378,688 bytes free. The original 10 GiB floor, 20-second freshness limit and backend guard remained active.

The range contains a normal metadata object at 1,532,731,392 whose checksum passes both checksum implementations, followed by a headerless root at 1,532,735,488. The root has a zero 32-byte object header, node flags 0x19 (ROOT, HASHED, NOHEADER), level 3, 16 keys, and tree flags 0x1c2 (including HASHED and NOHEADER). Four following leaves have flags 0x1a. Selected metadata and hashes are in probe-result.json; no payload file was saved.

Apple documents these headerless node flags and the zero object header. Sealed volumes use HASHED/NOHEADER filesystem trees. Reference: https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf, B-tree Node Flags and Sealed Volumes.

The current reader has a concrete compatibility gap. APFSVolume._fs_node passes the resolved mapping to Container.load_node (fs.py:333-338). Loading always calls check_object (container.py:141), and checksum_ok rejects a zero stored checksum (btree.py:95-97). This rejects the documented zero-header representation with the same exception as the failed preparation. Suppressing this check alone would still fail BNode's nonzero object-type requirement (btree.py:131-133). NOHEADER constants are defined but are not handled along this load/parse path.

This establishes that the live range contains a documented representation the current reader rejects. Attribution to the /p2/v1 failure is strongly supported by the final read and stack location. The exact object-map mapping selected by the failed process was not logged and was not independently recovered by this range-only probe. No repaired reader or successful firmware extraction has been demonstrated.

The backend's final layer event remains fetch_count 18, index 26: this probe caused no additional layer fetch. Sampler PID 32072 was confirmed running. Manifest/config/AUX and all four source/plan hashes recorded by the preparation monitor still match. AUX SHA-256 remains 2ca2b332f05e2d6e3663bb4db0982a5feec268a8d1b91460f140ad8d3cb49414.

No source edit, preparation rerun, firmware modification, extra watcher, restart, full RAW, checkpoint or guest execution was performed. The codebase-memory skill was read; graph tools are unavailable in this session, so the exact stack paths were inspected directly. Installed product/build, firmware and Golden desktop remain unobserved.

NEXT-STEP.md describes the focused reader change for review and the existing monitor's readiness-age constraint. The original instruction prohibits reader edits; applying that change requires an explicit scope expansion.
