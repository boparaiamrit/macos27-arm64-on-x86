Docker cleanup completed on 28 October 2026.

The data VHDX fell from 120,175,198,208 to 104,332,263,424 bytes after services restarted: 15,842,934,784 bytes reclaimed (15.84 GB / 14.76 GiB). C: had 24,857,473,024 bytes free at verification, compared with 9,800,298,496 in the initial sample. Other host activity continued; the volume-free-space change is distinct from VHDX reduction.

Removed only unused build cache, three inventoried unreferenced image layers, and the public timescale/timescaledb-ha:pg17.11-ts2.29.2 image used by no container. Docker reported 17.11 GB of cache records removed; shared cache accounting is not the Windows recovery figure. No containers, volumes, databases, project sources or macOS artifacts were deleted.

The public image can be retrieved by its preserved digest: timescale/timescaledb-ha@sha256:078e1753d0cf680103e1d70121ead63335ad5952328650d43ccab593097e7ae2.

After filesystem trim, all active containers were stopped gracefully and Docker Desktop stopped. Automatic compaction was skipped. The detached VHDX passed an exclusive-open check, then Windows OpenVirtualDisk/CompactVirtualDisk succeeded with METAOPS access and default flags. No elevation, mounting, guest-capacity resize, sparse-mode change or disk-file deletion was used. [Microsoft compaction contract](https://learn.microsoft.com/en-us/windows/win32/api/virtdisk/nf-virtdisk-compactvirtualdisk).

Docker and all 12 previously active containers were restored. All 81 container IDs and all 28 volume names remain unchanged. The eight database/Redis/mail containers report healthy. The three mstreetinvest containers already in restart loops before maintenance retain those pre-existing failures.

The macOS RAW exporter runs in the same container. Fresh readiness verifies all 67 checkpoint layers, unchanged RAW inode/device, 50,000,000,000-byte logical size, read-only negotiation and six NBD/direct-file sample comparisons. Future attempts use full-system/stream-ready-local-raw-cleanup-live5.json. The checkpoint SHA-256 remains 82066b4eeda14ff1edb191564b4eaf2806f4bfc042e904a95e56ead9dd06c05d.

Both admitted QEMU binaries and working AUX/overlay match their pre-maintenance SHA-256 values. Windows sampler PID 74040 remains running. Fresh CheckOnly 20261028T122458Z-v_nlsbvt passed after cleanup; no VM launched. The 10 GiB reserve remains unconditional.

Exact evidence: result.json, macos-preservation.json, running-after.txt, inventories and scoped cleanup logs in this directory. Container metadata receipts omit environment variables and credentials.
