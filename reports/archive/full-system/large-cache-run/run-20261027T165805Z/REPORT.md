# Bounded large-cache live5 execution

Status: **stopped_at_first_failure**.

First exact failure: iBoot Panic: : 4962211b03d706d:203.

The original backend was neither started nor reused. The new backend and existing host sampler were left under parent ownership. No runner, launcher, reader, backend, frozen converter, guard, firmware, or ACTIVE-STATE file was edited by this execution.

| Stage | Actual duration | Result |
|---|---:|---|
| Existing backend warmup | 816.944 s | Raw Docker-stderr export_ready event matched all manifest/config/plan/size/read-only pins |
| prewarm | 646.576 s | complete; exit 0 |
| preflight | 2.211 s | inputs_validated_no_vm; exit 0 |
| boot | 1702.415 s | hook_timeout; exit 1 |

Prewarm used 380 deduplicated observed boot reads, 1428992 requested bytes. List SHA256: `7a93ab69699fc170decc3dae36fe996df4fe13c875aca384a53ea61898b9b5e6`. Response hashes, read counts, and timings are retained; payload bytes were never persisted.

Prewarm helper execution: 645.558561 seconds; the table includes container launch/exit time. Additional verified prewarm fetches: 5. Additional boot fetches: 0.

Final backend verified fetches: 12; fetch starts: 12; unique verified layers: [0, 26, 48, 49, 50, 52, 53, 55, 59, 63, 66].

Final cached payload: 4060323840 bytes. Actual cgroup memory peak: 4383297536 bytes; hard limit 6442450944 bytes. Memory events: low 0; high 0; max 0; oom 0; oom_kill 0; oom_group_kill 0.

Minimum observed valid host-space sample during bounded orchestration: 33567125504 bytes. No sampler refresh or reserve/freshness bypass was performed.

Protected source hashes unchanged: **True**. Exact before/after hashes are in source-hashes-before.json and source-hashes-after.json. Existing input/source identity is also checked by the unchanged real-input preflight.

## Actual guest evidence

Final preservation verification passed at 2026-10-27T17:43:11.632212+00:00: new backend running with its pinned identity/image; original sampler PID 30680 alive; old backend stopped; owned prewarm and VM containers gone. See final-verification.json. No additional background jobs remain from this execution.

Attempt: `<WORKSPACE>/macos\test-output\arm-macos\full-system\attempts\20261027T171310Z-e0s5slwf`.

First observed guest failure: iBoot Panic: : 4962211b03d706d:203. The guest reached iBootStage2 and printed a double panic. Runner termination was separately caused by: GDB hook did not reach and verify the handoff within its deadline. Serial logs have no timestamps, so the exact panic time is not established.

Runner result:

```text
{
  "all_disk_layers_verified": false,
  "attempt": "/parent/full-system/attempts/20261027T171310Z-e0s5slwf",
  "cold_streamed_boot": true,
  "diagnostic_stream_cap_reached": false,
  "elapsed_seconds": 1701.327,
  "error": "GDB hook did not reach and verify the handoff within its deadline",
  "exit_code": 2,
  "first_boot_only": true,
  "full_gui_verified": false,
  "gdb_returncode": 0,
  "handoff_pc_verified_for_golden": false,
  "handoff_verified": false,
  "hook_timeout_seconds": 1700.0,
  "last_qmp_status": {
    "running": true,
    "status": "running"
  },
  "local_full_disk": false,
  "overlay_allocation_limit_bytes": 2147483648,
  "payload_verification": "on-demand by pinned streamed server; not all 67 layers read",
  "qemu_returncode": 0,
  "source_kind": "readonly-streamed-nbd",
  "status": "hook_timeout",
  "storage_trace_enabled": true,
  "timeout_seconds": 1800.0,
  "truncated_log_tails": [],
  "vm_started": true
}
```

Serial checkpoints:

```text
======== Start of iBootStage1 serial output. ========
:: 🔥🌸 Microkernel iBootStage1 for vma2 Copyright 2007-2026, Apple Inc.
::	Local boot, Board 0x20 (vma2ap)/Rev 0x0
::	BUILD_TAG: mBoot-20457.1.29
[ECID-bearing line omitted]
======== End of iBootStage1 serial output. ========
======== Start of iBootStage2 serial output. ========
iBoot Panic: : 4962211b03d706d:203
Board: vma2ap:0 
Build: RELEASE:mBoot-20457.1.29
```

Last retained serial output (ECID-bearing line removed):

```text
======== Start of iBootStage1 serial output. ========
9dd7a41e3b2bbad:223
eaa42379f549cbe:219
89994699affdef:140
eaa42379f549cbe:254
78faf5021313e82:74
78faf5021313e82:85
e62f453327738a:503
78faf5021313e82:235
9526cec925bde03:159
image <<PTR>>: bdev <<PTR>> type illb offset 0x20000 len 0x563aa
image <<PTR>>: bdev <<PTR>> type logo offset 0x763aa len 0x3773
ae71af5ee32b84:130
1aad73bb1002bf0:801


=======================================
::
:: ðŸ”¥ðŸŒ¸ Microkernel iBootStage1 for vma2 Copyright 2007-2026, Apple Inc.
::
::	Local boot, Board 0x20 (vma2ap)/Rev 0x0
::
::	BUILD_TAG: mBoot-20457.1.29
::
::	UUID: 903ADA1C-C0C7-3C90-B883-F7DAABB3C9A5
::
::	BUILD_STYLE: RELEASE
::
[ECID-bearing line omitted]
::
=======================================

1aad73bb1002bf0:1353
99180f7bfe1a22b:70
99180f7bfe1a22b:75
99180f7bfe1a22b:102
1d48c592ce4f38c:4070
1d48c592ce4f38c:4070
10d9a6f0bc00891:475
1d48c592ce4f38c:5460
10d9a6f0bc00891:462
======== End of iBootStage1 serial output. ========
======== Start of iBootStage2 serial output. ========
eaa42379f549cbe:219
89994699affdef:172
eaa42379f549cbe:254


iBoot Panic: : 4962211b03d706d:203
Board: vma2ap:0 
Chip: fe00:00 
Build: RELEASE:mBoot-20457.1.29
UUID: 4B48E51D-1870-375E-B660-278677B2CCE0



Stacktrace:
--> 0x0000000070080a90
--> 0x0000000070080ad8
--> 0x00000000700d9168
--> 0x00000000700d91d0
--> 0x00000000700d88dc


double panic in 

```

Last retained GDB output:

```text
0x0000000000100000 in ?? ()
```

Handoff result JSON: absent; no verified handoff result.

NBD progress: 1237 retained read requests, 385 unique offset/length pairs, last read (44651167744, 4096). Exact last unique offsets are in boot-trace-progress.json.

Kernel banner, mounted installed root, launchd, and GUI remain separate unverified gates. `full_gui_verified` remains false. QEMU running or a debugger exit status is not kernel-boot proof.

Original/patched firmware, original AUX/NVRAM, QEMU and handoff helper hashes are recorded in validated_source_identity in handoff.json and boot-retained-validated-inputs.json. The original/patched firmware hashes match the supplied 6d010540... / 593d1f9a... pair at offset 0x2370.

Two pre-read setup checks are retained in sibling run-20261027T165735Z and run-20261027T165748Z. Their new-script path/trace assumptions were corrected before any helper or VM was started; no existing source or guard changed.

## Evidence

See handoff.json, orchestration.jsonl, server.stderr.log, export-ready.verbatim.json (if ready), prewarm-reads.json, prewarm.stdout.log, per-stage cgroup/inspect snapshots, source hashes, and the unchanged runner attempt directory.
