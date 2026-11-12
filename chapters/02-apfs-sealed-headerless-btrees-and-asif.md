# Chapter 2 — Parsing macOS 27 ASIF Disks & Fixing Sealed Headerless APFS B-Trees

## Objective
Move from a stateless RAMDisk shell to a full installed **macOS 27 ("Golden Gate", builds `26A428` / `26A5277g`)** system stored inside a 67-layer LZFSE-compressed OCI/Tart image (~34.1 GB compressed, exposing a 41–50 GB Apple Sparse Image Format / raw APFS container) **without materializing a 50 GB raw file on disk**.

## Key Learnings & Breakthroughs

### 1. Why Standard Open-Source APFS Readers Fail on macOS 27 Sealed Volumes
When inspecting the Golden Gate System volume to extract paired VM firmware (`AVPBooter`) and verify `SystemVersion.plist`, existing Python/open-source APFS readers crashed or returned empty directories on the sealed System snapshot.
- **Root Cause 1 — Headerless B-Trees (`BTN_NOHEADER`):** Sealed macOS System snapshots store hash-tree / catalog subtrees using **headerless B-tree nodes** where the standard `btree_info_t` trailer/header assumptions fail.
- **Root Cause 2 — Root-Relative Virtual Child Identifiers:** Sealed APFS volumes resolve child node references via **root-relative virtual object identifiers** combined with SHA-256 cryptographic hash verification at every parent→child edge, rather than plain physical block addresses (`paddr`) in an `omap_phys_t`.
- **Root Cause 3 — `decmpfs` Compressed File Markers:** System plists (`SystemVersion.plist`) use transparent APFS `decmpfs` xattr/resource-fork compression that naive readers misread as 0-byte files.

### 2. The Fix (`src/apfs-and-streamed-disk/`)
- Implemented full support for sealed/headerless APFS B-trees, SHA-256 root & child node verification, root-relative virtual child ID resolution, and `decmpfs` decompression (`apfs-headerless/reader.patch`, `test_apfs_headerless.py`, `test_decmpfs_marker.py`).
- Added a bounded 32 MiB SQLite preparation read-cache (`preparation_read_cache.py`) so repeated metadata/firmware inspections replay instantaneously over NBD with **zero** fresh OCI layer reads (32 unit tests + live APFS-over-NBD replay verified).
