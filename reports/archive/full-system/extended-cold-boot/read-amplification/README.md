# Offline read-amplification accounting

Existing attempt `20261027T224156Z-rcpgj51o` only. No live server/VM access,
NBD fetches, or existing source changes. Reproduce with `python -B analyze.py`.
`analysis.json` records input hashes and the calculations;
`requested-raw-intervals.json` records the 1,735 merged requested intervals.

- 7,318 read sends, 220,597,760 requested bytes including overlap/repeats.
- Union of requested RAW address intervals: **211,774,976 bytes**.
- Repeated requested bytes: **8,822,784 bytes (4.00%)**.
- At 4 KiB granularity: **51,708 blocks / 211,795,968 payload bytes**. The
  observed set fits a **512 MiB payload** cap; metadata and durability overhead
  are additional. Alignment requires 20,992 more bytes than the exact union.
- A cold, retaining block cache projects 2,191 fully cached read sends, 46
  partially cached sends and 5,081 sends with no cached blocks. It assumes every
  earlier read completed and its whole block was verified/cached; these sends
  do not prove those completions. Future reads may exceed this observed set.
- All 72 verified-fetch counters (39 through 110) are present and contiguous.
  They cover 30 distinct OCI layer indices. 42 are repeat fetches of an index
  already verified during this boot: **17,653,088,082 compressed bytes**, of
  **31,149,157,515** total. First-in-this-window does not mean first-ever.
- Summed reported fetch durations: **7,074.807 seconds**, including
  **3,986.093 seconds** for repeat-layer events. These are reported acquisition,
  decode and verification durations, not isolated wire time or a proof that
  guest CPU could not run concurrently. The runner wall elapsed was 7,196.227s.
- Within 16 consecutive miss/fetch events there are 11–15 distinct indices
  (median 13); within 32, 17–23 (median 21). Repeated-index reuse distances in
  this miss-only sequence range 3–28. Actual layer-cache hits are unlogged, so
  these are lower-bound working-set observations, not a complete LRU simulation.
- Most fetched indices: 52 and 56 six times each; 26, 49 and 53 five each;
  55 four times. Full per-layer counts and sequence are in `analysis.json`.
- Layer 24 was in flight at the final snapshot; it is excluded from verified
  fetched-byte totals.

**Projection limit:** caching already requested RAW blocks would preserve this
observed 202 MiB set across evictions/restarts and avoid backing work for exact
repeats after successful caching. It does **not** eliminate fetching an evicted
512 MiB ASIF/OCI layer for a previously unseen RAW block in the same layer.
Only 4% of requested bytes repeat; a small expensive repeated request can still
trigger a whole layer, but the existing trace has neither request completion
timing nor request-to-ASIF-layer attribution. Therefore neither the 17.65 GB of
repeated-layer traffic nor its 3,986s duration is a justified raw-cache savings
estimate. No boot-completion time is projected. RAW offsets are guest-disk
addresses; they are not ASIF physical-source offsets, and ASIF is never treated
as RAW.

The terminal serial contains `swap enabled`, the start of
`init-with-data-volume`, then additional APFS transaction-close messages of
107.05s and 85.32s. Earlier transactions took approximately 72.64–184.34s.
No matching panic, Recovery request, initproc-exit or cipher-creation fatal
marker appears. Both empty shared-region messages were followed by successful
system-wide cache mapping. This supports **bounded timeout with continued
storage/boot progress**, not a concrete failed init task or proved guest hang.
Data mount is verified; `init-with-data-volume` completion and GUI are not.

## Rounded-block fill projection

`python -B project-block-sizes.py` replays the same 7,318 sends through an
initially empty 512 MiB payload LRU, assuming that every miss fills its entire
aligned block successfully before the next send. All four observed unions fit,
so this replay causes zero evictions.

| Fill block | Rounded unique payload | Fully cached sends | Partially cached sends | Sends needing backing | Payload cap headroom |
|---|---:|---:|---:|---:|---:|
| 4 KiB | 201.984 MiB | 2,191 | 46 | 5,127 | 310.016 MiB |
| 16 KiB | 221.766 MiB | 2,990 | 1,747 | 4,328 | 290.234 MiB |
| 64 KiB | **283.375 MiB** | **4,174** | 1,332 | **3,144** | **228.625 MiB** |
| 256 KiB | 461.250 MiB | 5,685 | 366 | 1,633 | 50.750 MiB |

The 64 KiB policy projects **1,983 fewer sends needing any backing access**
than 4 KiB, at 81.391 MiB more retained payload. This is send-level RAW-cache
locality, not HTTP avoidance or measured boot-time savings. A larger RAW block
can cross ASIF validity/extent boundaries even within a 1 MiB logical chunk;
whether its source bytes remain inside already cached OCI layers is unproved
by this trace. Preserve ASIF bitmap/hole semantics in any implementation.
Index/integrity/durability overhead and future demand are outside these payload
figures. Exact results and the input hash are in `block-size-projections.json`.
