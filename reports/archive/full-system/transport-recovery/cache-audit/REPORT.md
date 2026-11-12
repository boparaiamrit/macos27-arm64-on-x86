# Preserved returned-block cache: PASS

The bounded, offline audit verified all **5,600 committed records** and the exact
**367,001,600-byte (350 MiB)** payload. It completed in **1.961 seconds**.

The original proxy `f640975cae8b2fdeead196cf9771367f179e9ffc3dcfbdbf9cd5f39055884d09`
was confirmed exited, PID zero, exit code one, before and after. No running
container held a read-write mount of the cache at admission. The helper mounted
the preserved cache volume read-only and acquired `cache.lock` with shared,
nonblocking `flock`. All three entries were singly linked regular files; no
symlinks, rollback journal, WAL, SHM or unknown entries were present.

The five proxy source hashes match the existing read-cache admission. Calling
the admitted `common.identity` on the actual retained upstream ready event
verified the production manifest/config/plan pins, 50,000,000,000-byte logical
size, 65,536-byte geometry and source identity
`ae8cc1b18fcd87b2a1f4e49a706085304691856b1da92289238213f59d08a5cd`.
The cache-ready event's upstream readiness digest matched as well.

SQLite was opened with `mode=ro&immutable=1` only after the no-journal gate.
`quick_check` returned `ok`; the sole identity row matched exactly. Slots were
dense from zero through 5,599. Every logical offset was unique, aligned and
within EOF; every valid length was exact. Every record's SHA-256 over source ID,
big-endian offset/valid length and its complete padded block matched. No partial
EOF blocks were present; the padding requirement was checked for every record.

Whole-file SHA-256 values before and after were identical:

| File | SHA-256 |
| --- | --- |
| blocks.bin | `473f02f3ca375ea5205186ce68c06a297a06cdab72bf296b509c55a069f479bd` |
| index.sqlite3 | `0ea8adf12be32f335452f9a53d298fa5db2d6a1fb2a8d9a0ff215ffd55dc220d` |
| cache.lock | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

Inodes, device IDs, modes, link counts, ownership, lengths, allocated blocks,
modification and change times also matched. Access times are excluded because
this was a read audit. Nominal cache usage was **367,435,776 bytes**; allocated
usage **367,443,968 bytes**, below the unchanged one-GiB budget. Payload usage is
below 512 MiB. No payload was printed, copied or retained in audit artifacts.

The helper used the existing pinned runtime, network none, read-only root and
source mounts, one CPU, 512 MiB memory/equal swap, a 64-process cap, 16 MiB tmpfs
and an external 115-second timeout plus two-second kill bound. Its internal
audit deadline was 110 seconds. Peak cgroup memory was **395,669,504 bytes**;
all memory/max/OOM counters were zero. All **1,063** guard checks passed: minimum
C: free **29,183,188,992 bytes**, maximum observed sample age **2.011 seconds**.
The existing 10-GiB floor, 20-second age and two-second future limits were used.

The owned helper is gone. Sampler PID 104592 and its recorded start/command
remain alive. No backend, sampler, cache proxy or VM was started/restarted; no
journal recovery, source mutation, NBD payload read or network access occurred.
Only scripts and evidence in this new audit directory were written.

`result.json` contains the complete checks and before/after evidence;
`final-process-verification.json` records lifecycle and final hashes. This PASS
establishes internal cache consistency and unchanged admitted provenance; it
does not independently attest every OCI layer or authorize a source mismatch.
