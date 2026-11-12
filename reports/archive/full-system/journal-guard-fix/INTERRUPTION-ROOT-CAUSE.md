# Attempt 20261028T053842Z-0cawuywg: interruption root cause

The child report (`live/REPORT.md`) left the cause unresolved. It is a host restart:

| UTC | Source | Event |
|---|---|---|
| 06:39:11.69 | `host-space-live.json` | Last sample written by sampler PID 128008 |
| 06:39:12 | System log, User32 1074 | `StartMenuExperienceHost.exe` initiated **restart** on behalf of `bopar`; reason "Other (Unplanned)" |
| 06:39:18.5 | `macos-golden-stream-large` | `GuardError: missing or malformed host-space sample`, fail-closed stop; read-cache proxy then failed closed |
| 06:39:27 / 06:39:36 | EventLog 6006, Kernel-General 13 | Event log stopped; OS shutting down |
| 06:39:58.5 | Kernel-General 12 | OS started (`LastBootUpTime`) |
| 06:42:47 | Process table | T3 Code restarted; delegated turn resumed at 06:42:58 |

The guards behaved as designed: the sampler died with the shutdown, the source refused
to serve without a fresh sample, and the VM stopped. Not a guest, proxy or runner defect.

## What the interrupted run established

- Furthest guest point so far: launchd `Early boot complete. Continuing system boot.`,
  followed by xpcproxy launches, `usermanagerd`, `endpointsecurity`, `ifcstart`, `dynamic_pager`.
- Storage latency dominates: APFS `tx_flush` on disk3 took 979.7 s (xid 2778), 95.7 s
  (xid 2779); a transaction waited 93.3 s to prepare; `attrlistbulk` gave up after 123 s.
  Each cold layer costs 80–90 s to fetch from GHCR.

## Consequence

After the reboot, Windows reset its system-managed pagefile and C: free space rose from
about 28 GB to 63 GB. The reviewed converter's 50.39 GB guard now passes, so the next
attempt uses a local verified RAW (`../local-raw/`) instead of the streamed source.
