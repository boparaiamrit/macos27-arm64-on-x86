Preparation read cache
======================

Optional --cache-reads stores successful raw preparation reads in a private SQLite database under /guest/preparation-read-cache. Its identity binds manifest,config,ASIF-plan fingerprint and logical size. It holds at most512reads, each at most1MiB, with a32MiB database-page cap and small transaction journals. It never creates a50GB RAW file. The backend's separate RAM-only layer cache is unchanged.

Every cache hit verifies read length and SHA256 and checks a current host-space sample. Cache corruption fails closed. The32MiB budget filling disables further cache inserts without changing freshly verified source bytes. SQLite transactions allow interrupted writes to roll back when the file reopens. Cache database bytes are locally trusted capture evidence from the pinned read-only export; this is not a new independent Apple seal signature.

Ten tests passed, including wrong dataset pins, corruption, low/stale guard rejection on hits, capacity exhaustion, bounds, and a real local restore APFS-over-NBD parse followed by a second parse that refuses all fresh payload reads. Evidence: read-cache-tests-final.log. The final EOF-only adjustment also preserves the adapter's empty-read behavior beyond the logical disk.

Only the preparation helper enables this cache. Firmware and VM boot remain separate gates. The original backend, frozen OCI/ASIF converter and decmpfs source remain unchanged.
