# Post-fix preserved-cache audit: PASS

The read-only offline audit verified all **5,957 committed blocks**, totaling
**390,397,952 bytes**, in **2.256 seconds**. The count came from the actual
database; no earlier snapshot count was assumed. The payload file has exactly
that length: **zero unindexed suffix bytes**. An unindexed crash suffix would
have been preserved and reported as uncommitted, never admitted as valid data.

The exact original proxy `f640975cae8b2fdeead196cf9771367f179e9ffc3dcfbdbf9cd5f39055884d09`
was confirmed exited, PID zero, exit code one, before and after. Admission found
no running cache writer mount. The cache volume was mounted read-only and held
with a shared nonblocking `cache.lock`. All entries were singly linked regular
files. No rollback journal, WAL/SHM, symlink or unknown entry was present.
Immutable SQLite access was permitted only after that conservative journal gate;
no recovery or cleanup was attempted.

The five production source pins matched the current admission, including fixed
`common.py` SHA-256
`8f1235e080aacc84d3b4060e1be6d7aaf1a6e58e90e67297a4417e1d19215f15`.
Calling its actual production `identity` on the retained upstream ready event
matched the manifest/config/plan pins, 50,000,000,000-byte logical disk, 65,536-byte
block geometry and source ID
`ae8cc1b18fcd87b2a1f4e49a706085304691856b1da92289238213f59d08a5cd`.
The cache-ready upstream digest and database identity row matched exactly.

SQLite `quick_check` passed. Slots were dense from zero through 5,956; all
logical offsets were unique, aligned and within EOF, and lengths were exact.
Every committed SHA-256 over source ID, big-endian offset/valid length and the
entire padded 64-KiB block matched. Padding was checked on every record; no
partial EOF block was present. Committed capacity remained below 8,192 blocks /
512 MiB, and the physical file was within its admitted crash-suffix bound.

Whole-file hashes matched before and after:

| File | SHA-256 |
| --- | --- |
| blocks.bin | `cc1168ac7bfee5311fee212d6ba9e04efb52a96f484f1b309b8315b4c79fa88c` |
| index.sqlite3 | `99e74bad2688cdf923599851006b18ad8a6abe48871a7344b1cfc0cc24c5e1d2` |
| cache.lock | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

Device/inode, mode, links, ownership, length, allocation, modification and change
times also matched. Access time was excluded from the comparison. Total nominal
usage was **390,864,896 bytes**, allocated **390,873,088 bytes**, below one GiB.

The helper used the existing pinned runtime with network none, read-only root /
cache / sources / full-system mounts, one CPU, 512 MiB memory/equal swap, 64 PIDs,
16 MiB tmpfs and a 115-second external timeout plus two-second kill bound. The
internal deadline was 110 seconds. Peak memory was **416,018,432 bytes** with
zero memory/max/OOM events. All **1,132** fresh host guard checks passed: minimum
C: free **29,397,831,680 bytes**, maximum age **2.016 seconds**, using unchanged
10-GiB / 20-second age / two-second future limits.

The owned helper is gone. Sampler PID **128008**, start
`2026-10-28T05:27:40.7599816Z`, remains alive. No VM, proxy/backend restart,
network or NBD payload access, production edit, payload copy or journal recovery
occurred. Only new scripts and evidence in this directory were written; the
earlier transport-recovery audit is preserved.

See `result.json` for the full audit and `final-process-verification.json` for
lifecycle/source hashes. This verifies local cache consistency and admitted
identity; it does not independently verify every OCI layer.
