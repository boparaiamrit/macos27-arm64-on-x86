# One bounded Golden CTRR absence-probe boot

The single authorized actual boot ended after **99.978 seconds**, result **guard_or_runtime_failure**, launcher exit 1. CheckOnly `20261027T185248Z-hdcfc457` passed without a VM. Actual attempt `20261027T185255Z-5f56pynj` ran once; no retry occurred. Exact commands are in `check-only-command.txt` and `actual-command.txt`.

## Actual result

QMP recorded GUEST_CRASHLOADED (action run), then guest=true SHUTDOWN (reason guest-reset). The debugger inferior exited; the observer failed with No registers before capturing a validated stop. No ESR/ELR/FAR, code/string snapshot or precise crash instruction is available from this attempt.

Terminal events (UTC): `2026-10-27T18:54:29.166772+00:00 GUEST_CRASHLOADED {"action": "run"}; 2026-10-27T18:54:29.168022+00:00 SHUTDOWN {"guest": true, "reason": "guest-reset"}`. Result status `guard_or_runtime_failure` is the runner's classification of the GDB failure; it does not establish a low-space guard failure. `Guest crash loaded` and the guest-reset event are the observed guest termination evidence. GDB's "exited normally" does not establish a successful OS exit. The guest's underlying crash/reset trigger remains unknown. QEMU final return code was -9 after the runner shutdown path; GDB returned 1. Final guest cgroup counters were unavailable after automatic removal, so the in-run zero-OOM sample is not a final-lifetime OOM measurement. No new debugger command, memory read after exit, breakpoint change or retry was attempted.

The serial evidence has Stage2=True, Stage2 end marker=True, serial panic marker=False. It records 0 bounded trampoline hits and 0 content-validated boot_args candidates. A candidate would establish the observer's data checks only. **handoff_verified=false, kernel_execution_verified=false, full_gui_verified=false, all_disk_layers_verified=false.**

```text
avp-rtc: read offset=0x40 width=4 value=0x0 cpu=0 pc=0x70087788
avp-ctrr unavailable: unimplemented device read  (size 4, offset 0x0000)
avp-ctrr unavailable: unimplemented device read  (size 4, offset 0x0000)
```

CTRR accesses: 2 reads, 0 writes. The admitted helper logs/returns zero and logs/discards writes; it advertises no magic, version, controller banks, ranges, locking or enforcement. Actual access logs establish the probe was reached. They do not alone prove every subsequent absence-path check succeeded. RTC accesses: 1 read, 0 writes, 0 rejected; this is diagnostic register storage, not a complete RTC/clock model.

Fault evidence:

No active-fault ESR/ELR/FAR observation was captured.

No observation, trampoline hit, code/string snapshot or fault disassembly exists for this attempt: the target exited before either recognized observer stop. No prior-attempt snapshot is represented as current evidence. `attempt/` retains the exact copied observer, result, validated inputs, command, GDB, serial and QMP/device/storage logs. No full RAM or disk/payload cache was copied.

## Preservation

QEMU pin: `dba936f79fdfecea6163360d4beea0495cf2e870c11816a6a1b0c08ca7a8b542` at `/work/orchard-golden-ctrr/qemu/build/qemu-system-aarch64`. Firmware original/patched hashes remain `6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845` / `593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e`, explicit offset `0x2370`. No identity migration/reset/rebase occurred; identity unchanged=True.

All 266 captured source/control hashes matched. The list includes launcher, runner, observer, profiles, reader/backend sources, frozen converter, guards, sampler and ACTIVE-STATE. `guest-metadata-before.json` and `guest-metadata-after.json` also record working guest files, identity/migration backups, five build binary/source paths and explicit missing paths. Four earlier full source-tree manifests are inherited root evidence; this run independently compares the listed files only.

Working AUX before: `9cbf8c7da5257fb61dde369c5cb2808e11aaba604f590c1a235781e7ec2538f0`; after: `f8b1bc3c414fc72175e6c9e59df70a0298336a31b8f8e3c1d4845699f76be144`. Length/allocation after: 33562780 / 33566720 bytes.

Working overlay before: `24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c`; after: `24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c`. Length/allocation after: 197360 / 200704 bytes. Only these working guest files were allowed to change through natural guest execution. Actual changes: `["/guest/boot/aux.work.img"]`.

## Guards, storage and processes

Every retained guard sample passed unchanged `host_space_sample.read_valid_sample`: C: >=10 GiB, age <=20 seconds, future <=2 seconds. Smallest captured free space: 28515246080 bytes; greatest captured age: 1.692 seconds. Continuous minimum was not measured. Existing runner/backend guards remained in force.

The original backend identity/start/resources/mounts/command matched=True; running after=True. Same URI `/stream/golden-live5.nbd`, volume `macos-golden-stream-large-state`, read-only root, 2 CPUs, 6 GiB memory/equal memory-swap limit and eight RAM layers were preserved. Verified fetch count 14 -> 15; verified fetched bytes 5868108106 -> 6304069925. Memory.current delta 12288 bytes; lifetime memory.peak delta 0 bytes. One new layer fetch (index 52, 435961819 compressed bytes) completed on the preserved backend after guest termination. The after-log has one additional NBD broken-pipe reply line; the earlier broken-pipe line was preexisting. No new backend guard/timeout event or restart was logged. Memory event deltas: `{"low": 0, "high": 0, "max": 0, "oom": 0, "oom_kill": 0, "oom_group_kill": 0}`. Details and bounded backend logs: `backend-deltas.json`, `backend-log-before.txt`, `backend-log-after.txt`.

NBD trace: 2166 read requests, 31903232 requested bytes including repeats, 25542144 unique requested bytes. Request-failure trace lines: 0. These are requested intervals, not independent acknowledged bytes or full payload verification. See `nbd-progress.json`.

Owned launcher/VM/helpers all absent=True; launcher PowerShell PIDs absent=True; QEMU return=-9, GDB return=1. Existing sampler PID 104360 alive with same creation time/command=True. Backend/sampler were never stopped, refreshed or replaced. `owned-processes-final.json` lists exact owned processes; VM cgroup evidence is an in-run sample, not final lifetime counters.

Text evidence was ECID-redacted before live output and retention. `retained-diagnostics.json` records original/retained file hashes, `handoff.json` is the structured result, and `final-verification.json` records the final artifact/privacy/process/guard check. Experiment completed at 2026-10-27T18:57:19.466295+00:00.
