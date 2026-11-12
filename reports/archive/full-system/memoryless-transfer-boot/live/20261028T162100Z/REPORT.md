The single live attempt **20261028T161919Z-x_lwfcqe failed with a native LLVM abort**. The candidate is not live-qualified. `LLVM ERROR: Cannot emit physreg copy instruction` recurred with both optional compute-copy switches confirmed `off`. This establishes recurrence of the error, not the same internal callsite as the predecessor: current crash contents were not inspected.

- Fresh CheckOnly `20261028T161905Z-1qi7zblj` passed: `inputs_validated_no_vm`, exit 0.
- Live launcher start: 2026-10-28T16:19:18.587462Z. Result saved: 2026-10-28T16:23:05.977182+00:00.
- Elapsed 226.117 seconds of the authorized 900-second bound; hook bound 800 seconds. Runner `guard_or_runtime_failure`, exit 2; launcher shell exit 1; QEMU -6 (SIGABRT); GDB 0. Runner error: connection reset by peer.
- One live invocation; no retry, manual stop, guest input, added debugger/QMP client, source/configuration edit, rebuild, or service restart. Exact command: [launch-record.json](launch-record.json).

The [serial log](../../../attempts/20261028T161919Z-x_lwfcqe/serial.log) establishes separate checkpoints: Darwin 27.0.0 at line 84; BSD root disk3s1 at 408; successful root-hash validation at 434; read-only System mount at 437–441. The guest pivots through BaseSystem and returns to installed root at 805–816. Data disk3s5 finishes mounting at 1621, init-with-data-volume runs at 1649, launchd reports early boot complete at 1881, and WindowServer activity appears at 1926. Handoff passed. Compact excerpts: [serial-checkpoints.json](serial-checkpoints.json). Kernel, System root, Data and userspace are supported; GUI and interaction are unverified.

The only [retained frame](../../../attempts/20261028T161919Z-x_lwfcqe/frames/frame-0001.png), captured 2026-10-28T16:21:23.981629+00:00, is entirely black at 1920×1080. It was inspected with view_image; all RGB channel extrema are zero. SHA-256: `c1161e09bb43363d2777bdb410b3e59e98b33eae3b374322b5e86079ab089a12`. This frame predates graphics activity near Reims t=221–222 seconds. No post-draw frame was saved before the abort; the image cannot establish the final console state.

The canonical [Reims gzip](../../../attempts/20261028T161919Z-x_lwfcqe/reims-vgpu-fail.log.gz) passes a complete read through EOF: **1,199,026 raw bytes**, SHA-256 `404b58d66019d49d7e5a7b8fd0a6ed7a110be0eb89da59801ffcb6f09d040b6b`. Both match reims-capture.json; capture finished without exhaustion, truncation or unretained consumed bytes. See [log-verification.json](log-verification.json).

[key-diagnostics.json](key-diagnostics.json) records the graphics evidence:

- Mapping 1, generation 2 captured 29 physical pages with Descriptor1PhysicalTree (raw lines 2124–2125); guest-page seeding follows at 2156. Page capture and consumption are supported. No explicit validation-completion marker was emitted, so independent page-by-page validation is not claimed.
- No memoryless trace or memoryless_pass_targets_retired counter was emitted. An increase cannot be demonstrated. No vk_memoryless_pass_retire retention/error event appeared before abort. This run does not qualify the pass-lifetime correction.
- One pipeline lease became ready and one 1920×60 pass_target appeared. DontCare load was raised to CLEAR. No explicit unsupported attachment/shader/compute refusal appeared before abort. Two memo type probes and three extent notices do not establish the native crash cause.
- qemu_map_pages_alias_failed and contig_view_refused were followed by guest_pages seeding. This is the expected anonymous-RAM copying fallback, not an identified new blocker.
- compute_scatter=off and compute_gather=off are confirmed at raw line 2171. Robust buffer access remained true. No present-content-kind event was emitted; GPU activity is not visible-output proof.

[pre.json](pre.json), [post.json](post.json) and [preservation.json](preservation.json) contain compact hashes. All 15 reviewed Rust sources match changes.json before/after. QEMU remains `f603fd8b6066b96a38bfbb20ad74c9c322643c0b120f8662ed079be99ddd648a`; archive remains `16743f65688ea0a3ade428e0fc168819dddc25dcd3deb7a8a07f6f0dc91855dc`. All 27 local input hashes, original/patched firmware, prepared report and CONTROL identity pin are unchanged. Only natural working-state changes were observed in the captured set, and preserved:

- AUX: `f2fd8aa95a1a34e605cba93b34454229ed153ea2c2f1e98f6793cad61547d8b5` to `040abcb61258f3e5feb98573af0c6661711a87237bdfa208e13bd8eea2d441c7`; 33,562,780 bytes.
- Overlay: `b45b85345dfc3326f5726f060efb5dc83b36ded1d5fcbce5ac8f26f764f45221` to `f13725c2084633e175c9864270f85a3f51e945944f32089ce2aa50511047b05c`; logical length 1,026,162,688 to 1,026,424,832 bytes.

[cleanup.json](cleanup.json) confirms QEMU/GDB ended, the owned container is removed, and no active CONTROL user remains. Exporter b8472de170f6ab1709e76bef8ca08f48df591ee4ea893f607eae2fddb21ce372, PID 1187, start 2026-10-28T12:19:53.487560899Z, resources and mounts are preserved; MAIN remains read-only. Sampler PID 74040 retains start 2026-10-28T06:54:20.5951215Z. At 2026-10-28T16:28:38.7215025+00:00, sampled free space was 15,166,496,768 bytes, age 1.893 seconds, above the unchanged 10 GiB floor.

The new this-QEMU WSL core is **331,776 bytes**: wsl-crash-1793204585-12-_work_orchard-m27-pages-mem-safe_artifacts_qemu-system-aarch64-6.dmp. Created 2026-10-28T16:23:05.6696134Z; last modified 2026-10-28T16:23:05.6712032Z. Size remained stable across metadata inspections, consistent with guest-RAM exclusion. Wrapper filter 0x10 and --ulimit core=0 remain unchanged. Only metadata was inspected; nothing was deleted.

Readiness separately pins the 50,000,000,000-byte local RAW with all 67 layers converter-verified, checkpoint `82066b4eeda14ff1edb191564b4eaf2806f4bfc042e904a95e56ead9dd06c05d`, and unchanged NBD URI. Generic streamed-source labels in result.json do not override that provenance. No RAW rehash was performed. Counts and elapsed time are observations, not a speed benchmark. Machine-readable handoff: [handoff.json](handoff.json).
