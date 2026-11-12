# Bounded streamed Golden preparation: BLOCKED

The pinned live server reached validated read-only export readiness; real preparation connected and began guest reads. Preparation was interrupted by the external host-space monitor failing closed when Windows denied a read of the parent-owned sample. No APFS traversal exception was emitted before that stop.

- Server: `c9b40056252700cc6cb92fb8fee51030df692c4be5be8c401b002ec88b4c692c`; pinned image confirmed, left running.
- Ready event: `../../stream-ready.json` relative to this directory, saved verbatim from Docker stderr after manifest/config/plan/size/readonly validation.
- Actual readiness duration: 1552.472117 seconds from Docker server start; event UTC 2026-10-27T06:21:11.665074+00:00.
- Readiness downloads: eight completed verified fetches over seven distinct OCI disk layers (0, 26, 48, 52, 55, 59, 63); layer 0 fetched twice for configured warm-up.
- Helper: `macos-golden-prep-20261027t055902z-66388`, id `5db5bc1d5df0c2c39337286d1d104fca7e7571b7aab16c2dd742dccefa82150f`. Network none, root and sources read-only, stream RO, guest RW, 2 CPUs, 1 GiB RAM, 1 GiB memory+swap, 16 MiB tmpfs. `/usr/bin/timeout --signal=TERM --kill-after=5s 3600s /usr/bin/python3 ...prepare-streamed-guest.py` used the exact requested paths.
- Actual helper duration: 145.089329 seconds; stopped with exit 143, OOM false.
- First exact stopping event: `owned_helper_stop` at UTC 2026-10-27T06:23:48.401348+00:00, reason `[Errno 13] Permission denied: '<WORKSPACE>/macos\\test-output\\arm-macos\\full-system\\host-space-live.json'`.
- Last successful guard read before stop: 21186609152 free bytes, sample age 0.960387 seconds. This was unreadable guard evidence, not an observed low-space or stale sample. No guard bypass or helper retry was attempted.
- Helper stdout reached only `readonly_stream_connected` (50,000,000,000 bytes) and `inspect_volume` root `/`; stderr empty.
- Final read-only guest inventory: volume empty; `/guest/boot` does not exist. No volume census, prepared report, firmware or AUX copy was produced.
- Product/build, candidate volume, firmware length/hash/header/site at 0x2314 and Orchard patch compatibility remain unobserved. Expected version was not assumed.
- Original manifest, config and AUX hashes rechecked unchanged. No ECID or config body printed. No source, runner, ACTIVE-STATE, RESULT, sampler, backend or existing guest files changed. No firmware patch, QEMU/macOS/GUI launch, full RAW, or checkpoint created.
- Handoff layer counts: 9 starts; 9 completed verified fetches, 8 distinct layers. Layer 50 finished verification after the helper stop. See timestamped `handoff.json` for the final snapshot.

Evidence: `summary.json`, `handoff.json`, `monitor.jsonl`, `validated-inputs.json`, `export-ready.verbatim.json`, `helper-command.json`, `helper.created-inspect.json`, `helper.final-inspect.json`, `helper.stdout.log`, `helper.stderr.log`, `preparation-before.json`, `preparation-after.json`, `host-guard-samples.jsonl`, `resources.jsonl`, `server.stderr.log`, and `server.handoff-inspect.json`.
