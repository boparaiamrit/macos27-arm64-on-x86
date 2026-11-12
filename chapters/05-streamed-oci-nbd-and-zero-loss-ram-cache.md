# Chapter 5 — Zero-Loss Streamed NBD Disk Architecture (`41,755` Blocks in RAM, `zero_fills = 0`)

## Objective
Serve a 50 GB macOS 27 APFS disk from 67 LZFSE-compressed OCI layers (`/guest/fresh-01/layers/000..069.lzfse`) to QEMU at RAM speed **without** extracting a 50 GB raw image on the Windows SSD and **without** returning corrupt zeros on uncached offsets.

## Key Learnings & Breakthroughs

### 1. Diagnosing the Two-Layer LRU Thrash & Startup Blocking Bugs
1. **LRU Thrashing:** An early 2-layer RAM cache repeatedly decoded and evicted the same 450–512 MiB LZFSE layers whenever APFS metadata and system libraries interleaved reads across layers `0`, `10`, `27`, `30`, and `66`.
2. **Journal Guard & Cancellation Races (`src/apfs-and-streamed-disk/streamed-disk/`):** If a client disconnected or timed out mid-fill, partial upstream reads could block startup or leave stale lock state (`ROOT_CAUSE.md`, `REGRESSION.md`).
3. **Why `zero_fills > 0` Stalls `WindowServer`:** An offline replay cache (`read-cache.sqlite3`) initially held only the `6,102` 64 KiB blocks (~381 MiB) observed during early kernel boot. Returning zeros (`zero_fills`) for any newly requested dyld shared cache or Metal framework page silently corrupted Mach-O pages in guest RAM!

### 2. The Zero-Loss `offline_cache_nbd.py` Engine (`src/fastjit-qemu/offline_cache_nbd.py`)
We built a 16-thread `nbdkit` Python server combining instant RAM lookups with on-demand parallel LZFSE streaming:
- **Preloaded Base + Persistent Delta Cache:** Loads `read-cache.sqlite3` (`6,102` 64 KiB blocks) plus `extra_cache.sqlite3` directly into Python `dict[int, bytes]` in container RAM before QEMU starts.
- **ASIF Extent Index (`asif_chunk_map.json`):** Maps every 1 MiB virtual disk `vchunk` to its exact `(layer_idx, byte_offset, length)` inside `/guest/fresh-01/layers/*.lzfse`.
- **Stateful Streaming Decoder Pool (`32` Active Layer Decoders) + `8×` Adjacent `vchunk` Prefetch:** On any cache miss, streams forward through the `lzfse -d` pipe up to the target offset, caches up to **8 adjacent 1 MiB `vchunk`s (128 × 64 KiB blocks)** in `EXTRA_MEM`, and commits them atomically to `extra_cache.sqlite3` (`WAL` mode).
- **Result Across Warm Boots #1 → #10:**
  - Cached blocks grew organically: `6,102` → `14,597` → `26,712` → `33,654` → `39,665` → **`41,755` blocks (`2.61 GiB` in RAM)**.
  - **`zero_fills = 0`** across every single boot!
