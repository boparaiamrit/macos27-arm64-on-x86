# One bounded Golden AVP RTC boot

The single authorized boot completed in **37.882 seconds**, stopping at a content-validated iBootStage2 panic caller. `iboot_observation_captured` and exit 0 establish successful diagnostic capture; macOS remains blocked. No retry occurred.

Actual attempt `20261027T183601Z-xqka79lw` began 2026-10-27 18:36:00 UTC / 00:06:00 IST on 28 October. CheckOnly `20261027T183545Z-94fvmbkq` passed without starting a VM. Exact commands are in `commands.txt`. Completed before 00:50 IST.

## Observed progress and blocker

The guest reached Microkernel iBootStage2 for vma2, build `mBoot-20457.1.29`. The new AVP RTC register log records exactly one read and no writes or rejected accesses:

```text
avp-rtc: read offset=0x40 width=4 value=0x0 cpu=0 pc=0x70087788
```

Execution passed the previously faulting RTC access. The observer stopped at `0x700d9164` with **ESR_EL1 `0x92000010`, ELR_EL1 `0x700863f4`, FAR_EL1 `0x30260000`**: lower-EL read data abort, synchronous external abort. The saved exception context has `x8=0x30260000`. The captured instruction word `0xb9400108` is `ldr w8,[x8]`.

Offline disassembly of the hash-verified 1 MiB code snapshot shows:

```text
700863f0: mov  w8, #0x30260000
700863f4: ldr  w8, [x8]                 <-- observed abort
700863f8: mov  w9, #0x7272
700863fc: movk w9, #0x6374, lsl #16
70086400: cmp  w8, w9                  // expected 0x63747272, ctrr FourCC
```

This establishes execution of the read at the prospective CTRR probe. The subsequent comparison was not executed; the captured code does not establish successful identity/status responses or a complete CTRR contract. No CTRR mapping, fabricated response, breakpoint change, or source fix was made. Full disassembly: `fault-disassembly.txt`; machine-readable fault: `fault-summary.json`.

No trampoline-hit files or bootargs candidates were captured. The observer reached the panic caller before serial printed `iBoot Panic:`. **handoff_verified=false, kernel_execution_verified=false, full_gui_verified=false, all_disk_layers_verified=false**. The 1 MiB code and 16 KiB string snapshots are bounded diagnostics, not full RAM.

## Preservation and guards

QEMU remained pinned to `25fa22ad4790a877dc842dca3e97cc06e15fab7ef144a266c04e2790cc2d59a4`; source `vmapple.c`, prior Golden/scratch binaries, firmware, current identity and migration backups matched before/after. All **227 captured host source/control-file hashes** matched, including runner, launcher, observer, profiles, readers, frozen converter, guards and ACTIVE-STATE. Manifests: `source-hashes-before.json`, `source-hashes-after.json`, `guest-metadata-before.json`, `guest-metadata-after.json`. The optional guessed baseline path was absent in both snapshots and proves nothing about other unmeasured paths.

Authorized guest execution changed working AUX SHA256 from `457d9c95823b6b59665f77595b047bb5c1fd039a5eeea49c5cb18a675ddfda5b` to `9cbf8c7da5257fb61dde369c5cb2808e11aaba604f590c1a235781e7ec2538f0`; its length/allocation remained 33562780 / 33566720 bytes. The working overlay byte hash remained `24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c` with length 197360 and allocated 200704 bytes. Identity and original/patched firmware were unchanged; no migration/reset/rebase occurred.

Boundary guards used unchanged `host_space_sample.read_valid_sample`: C: >=10 GiB, age <=20 s, future <=2 s. The smallest captured free space was 29329137664 bytes; maximum captured age 1.686 s. Existing runner/backend guards remained active without a reported failure. A continuous free-space minimum was not measured.

Backend `macos-golden-stream-large` remained the same running container/image, start time and resources: 6 GiB memory and equal memory-swap limit (zero additional swap), 2 CPUs, read-only root and eight-layer RAM cache. Verified fetch count stayed **14 -> 14**, verified fetched bytes stayed 5868108106; no new layer fetch, guard/timeout event, restart, or cgroup memory/OOM event was logged. The prior broken-pipe line existed before this run and was unchanged. Backend lifetime memory peak was 4383297536 bytes; it is not this run's isolated peak. Detailed resource/OOM evidence: `backend-deltas.json`.

The owned VM cgroup sample captured peak 1887875072 bytes and zero OOM events while it was running; final counters were unavailable after automatic removal. This sample is not asserted to be the final peak.

Storage trace records 1788 read requests totaling 30369280 requested bytes including repeats, covering 25517568 unique requested bytes. These are QEMU request intervals, not independent acknowledgments or complete disk verification. `nbd-progress.json` retains bounded ranges and trace failures.

Every owned launcher/VM/evidence/disassembly container is absent, the owned launcher PowerShell process is gone, and QEMU/GDB returned 0. Existing backend and sampler PID **104360** remained alive with unchanged identity. No backend or sampler was stopped/replaced. `owned-processes-final.json` records exact owned names.

## Evidence

`attempt/` contains the result, content-validated observation, exact copied observer, code/string snapshots, command, QMP, serial, storage/device logs and any trampoline captures (none). `check-only/` contains the successful validation. `retained-diagnostics.json` hashes every retained file and its original source; text was ECID-redacted before copying/output. No disk or payload cache was copied. `handoff.json` is the machine-readable handoff.
