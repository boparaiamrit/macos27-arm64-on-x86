# Bounded persistent read-cache admission

The prior two-hour boot proved Data mounting and the start of `init-with-data-volume`, then reached its wall bound during continuing APFS and source-fetch activity. Its 7,318 read sends cover about 202 MiB of unique logical RAW addresses; acquisition/decoding/verification fetched about 31 GB including repeated layers. These figures do not by themselves identify avoided HTTP costs.

The new proxy retains only blocks obtained from the existing verified, read-only NBD export. It uses 64-KiB covering blocks, a 512-MiB payload cap, and a 1-GiB total nominal/allocated cache-file cap. The observed prior read set rounds to 283.375 MiB at this geometry. That fits the payload budget but does not guarantee future coverage or boot-time savings. New unique source blocks can still require large source-layer fetches. The proxy advertises a one-MiB NBD request maximum; each complete request has a 900-second deadline, which is stricter than the upstream's per-layer deadline.

The offline implementation passed 30 actual nbdkit/libnbd and integrity/cancellation tests. Full capacity used 537,407,488 bytes including metadata, peak memory 732,381,184 bytes, and no OOM. Maximum recorded cancellation was 1.719 seconds with owned descendants reaped. An independent static review found no verified findings in the frozen five-file implementation. Its scope and test limitations are in `../../streamed-disk/read-cache-proxy/README.md` and `artifacts/handoff.json` there.

The first production metadata check caught a missing `sha256:` prefix in the proxy's expected PLAN constant. The proxy refused startup before connecting to the source or creating cache data. The failed container and logs are preserved as `macos-golden-read-cache-pin-refusal-20261028T010904Z` and `initial-pin-refusal*`. Both newly owned volumes were inspected read-only and confirmed empty before reuse. Parent corrected only that constant, rechecked the other four source hashes, retained the original admission snapshot, and updated `admission.json`. Thirty oracle tests passed with this correction; two additional tests using the actual production readiness record passed, including strict refusal of a missing prefix. The initial extra unittest file invocation and an incorrect test assumption about the private hash preimage were corrected in the test harness; neither changed production behavior.

Live parent checks verified:

- Proxy `macos-golden-read-cache`, container ID `f640975cae8b2fdeead196cf9771367f179e9ffc3dcfbdbf9cd5f39055884d09`, original pinned runtime image, one CPU, one GiB memory/equal swap, 128 pids, read-only root, no network, dropped capabilities, no-new-privileges, 16-MiB tmpfs and four-MiB rotated Docker log budget.
- Original backend identity and read-only upstream-state mount; original readiness bytes match the proxy's recorded digest. No fixture-mode environment is present.
- Actual upstream read-only/50-GB size negotiation, matching manifest/config/plan pins, and the proxy's `export_ready` event with zero cached blocks and `all_disk_layers_verified=false`.
- The whole `full-system` directory is mounted read-only so atomic host-sample replacement remains visible. The existing source backend was not restarted or changed.
- Proxy-backed CheckOnly `20261028T011154Z-yhzpd31j` passed. It negotiated metadata and started no VM; it performed no payload prewarm.

The new socket is in volume `macos-golden-stream-read-cache-state`, still at `/stream/golden-live5.nbd` inside the VM. The existing overlay URI, guest identity, crypto emulator and r3/WDT handoff are unchanged. Cache payload/index lives only in `macos-golden-stream-read-cache-data`. Source-bound per-block SHA-256 checks detect local corruption; they are provenance from bytes previously verified upstream, not independent OCI/Merkle attestation against a compromised host.

The same 10-GiB host floor, 20-second freshness, two-second future tolerance, existing VM/overlay/log limits and source cancellation remain enforced. Proxy normal polling is 50 ms; transient sample-open sharing retries can add up to 0.5 seconds without accepting stale or low-space data. Sampler PID 99168 started 2026-10-28T00:52:07Z for four hours, beyond the planned next run.

The next actual command is one bounded attempt, with no second debugger, runtime screenshot, quiet-log stop or guest input:

```powershell
& ./test-output/arm-macos/full-system/Launch-FullAttempt.ps1 -GoldenCrypto -CompressedReimsLog -ColdStreamedBoot -ExtendedColdBoot -TraceStorage -Timeout 7200 -HookTimeout 1700 -GuestVolume macos-golden-pristine-guest -StreamVolume macos-golden-stream-read-cache-state -ReadyName stream-ready-read-cache-live5.json
```

CONTROL's naturally changed AUX and overlay from the Data-mounting boot are preserved. MAIN remains protected. GUI and hardware acceleration remain unverified. The proxy and original backend are parent-owned services to preserve after the bounded VM attempt; requested stop or guard failure still ends owned work safely.
