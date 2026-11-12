# One bounded Golden revision-3 installed-disk boot

Exactly one actual GoldenHandoff invocation, no retry. Actual attempt `20261027T193233Z-f1pd03a6`. Runner returned `diagnostic_limit`, exit `2`, elapsed 1449.804 seconds. Launcher exit `1`. CheckOnly passed first. This is an actual injection and kernel execution result; it does not establish an installed System boot or GUI.

## Actual checkpoints

Adapter: `{"args_address": "0x79cb0000", "boot_args_revision": 3, "boot_args_version": 2, "handoff_pc": "0xe0a00000", "handoff_pc_verified_for_golden": true, "kernel_entry": "0x77d70480", "new_boot_args_sha256": "ba7f1fb871422a4ea3dca7aa1873829f9a2ff920de02215de09fc342581195bb", "new_command_line_length": 208, "new_command_line_sha256": "9ac8463d3ed33076f74032836bbeef5d4e3b9f52bdbb5da140791094394158c1", "new_tree_length": 573440, "new_tree_sha256": "cd50c349dd9835feab4544f75671bcb8d1dc7c9e6d160773b2a0cfa36368e031", "no_sep_contract_verified": true, "no_sep_node_added": true, "old_boot_args_sha256": "4c305c2d33a6ee5361a6ced159c723d1c840c4ed3c7922405e4750263456a264", "old_command_line_length": 196, "old_command_line_sha256": "f9d1a06ea3335796693531411fa4a897c99ee7d39fd839969eb0e3934692f8c2", "old_tree_length": 573440, "old_tree_sha256": "79c05f221cedc276ff425a8c5e28f349ac55283ff666cc3c1ab137096ee712ab", "original_boot_args_preserved": true, "original_zero_padding_bytes": 11220, "parsed_tree_bytes": 562220, "readback_verified": true, "requested_boot_args": "-v serial=3", "tree_address": "0x74e2c000", "write_count": 9, "written_bytes": 43}`

- kernel: `attempt/serial.log:84`: Darwin Kernel Version 27.0.0: Tue Aug 11 21:00:07 PDT 2026; root:xnu-13432.1.9~1/RELEASE_ARM64_VMAPPLE
- root: `attempt/serial.log:397`: AppleFileSystemDriver: publishing boot-uuid-media=disk2s1 (Recovery)
- root: `attempt/serial.log:399`: Got boot device = IOService:/AppleVirtualPlatformARMPE/arm-io/AppleVirtualPlatformIO/pcie@30000000/AppleVirtualPlatformPCIE/scsi@3/AppleVirtIOPCITransport/AppleVirtIOStorageDevice/AppleVirtIODiskStorageDevice@1/IOBlockStorageDriver/Apple Inc. VirtIO BlockBSD root: disk2s1, major 1, minor 11
- root: `attempt/serial.log:415`: nx_volume_group_update:706: disk2s1 Volume Recovery role 0x4 is not a System or Data volume
- root: `attempt/serial.log:417`: apfs_log_op_with_proc:3279: disk2s1 mount-complete volume Recovery, requested by: kernel_task (pid 0); parent: kernel_task (pid 0)
- userspace: no matching checkpoint in all 426 retained serial lines. See `checkpoints.json` for the exact search criteria results.
- panic/reset markers: no matching checkpoint in all 426 retained serial lines. See `checkpoints.json` for the exact search criteria results.

Final serial line 426: `getVolumeGroupMountFrom:9463: disk0s2 nx_get_volume_group(5A4AFA30-AD31-4AF9-95A9-CD31DE8721E1) failed with error 2`. `installed_system_root_mounted=False`, `userspace_verified=False`, `full_gui_verified=false`. Recovery role 0x4 is explicitly reported as neither System nor Data. A GDB zero exit or PV panic GUEST_CRASHLOADED/action=run notification alone is not OS success or a kernel crash. The final runner result and QMP transcript are in `attempt/result.json`, `attempt/qmp.jsonl`, and `qmp-summary.json`.

## Exact commands

```powershell
& ./test-output/arm-macos/full-system/Launch-FullAttempt.ps1 -GoldenHandoff -CheckOnly -StreamVolume macos-golden-stream-large-state -ReadyName stream-ready-large-live5.json
& ./test-output/arm-macos/full-system/Launch-FullAttempt.ps1 -GoldenHandoff -ColdStreamedBoot -TraceStorage -Timeout 1800 -HookTimeout 1700 -StreamVolume macos-golden-stream-large-state -ReadyName stream-ready-large-live5.json
```

Neither invocation used IBootDiagnostic, PauseOnGuestReset or SingleUser. Requested guest options were exactly `-v serial=3`; the profile used the actual content-qualified transfer PC `0xe0a00000`. Exact redacted QEMU/GDB argv and environment: `attempt/command.json`. No guest commands were sent.

## Immutable sources and persistent bytes

All captured source hashes are identical before/after (`source-hashes-before.json`, `source-hashes-after.json`, `source-comparison.json`). This includes launcher, runner, profiles, r3 runtime pair, original helpers, ACTIVE-STATE, frozen converter, streamed reader and guard sources. Codebase graph tools were unavailable; relevant source was read directly. No build, installation, firmware edit, identity migration, prewarm, conversion, backend restart, cleanup or host restart was performed.

- `full-system/handoff-r3/kernel-handoff.gdb`: `e14fb3450b7876b2fd8285a33d851b8d78a768d45032936bc7bd64d3db0bac7f` before and after.
- `full-system/handoff-r3/golden_adt_args.py`: `5a242dd347cc49a2a03bc0a2a6b84e8ba32fc7df1ce59740a223a9dc433d439c` before and after.
- `full-system/Launch-FullAttempt.ps1`: `4abc769a0cfc001fe8e2ea1a719d03d81f57d52a018f162fa98defb2cd60a252` before and after.
- `full-system/run-full-attempt.py`: `224e0ccd209e8d7d7b5162eb1c28ad1cfb3e2bcd88b0df381a068bf9fbe0c06e` before and after.
- `full-system/run-handoff-attempt.py`: `26a1167af3d97ec378bd8657a39e7cab618cdc25c792c422946707a5313a01d3` before and after.
- `full-system/golden_handoff_profile.py`: `a6efcac585efd0adc12f8fa7958042e2d0b5f17f3da7272ec6f2f4d15442b1ff` before and after.

- `/work/orchard-golden-ctrr/qemu/build/qemu-system-aarch64`: SHA-256 `dba936f79fdfecea6163360d4beea0495cf2e870c11816a6a1b0c08ca7a8b542` -> `dba936f79fdfecea6163360d4beea0495cf2e870c11816a6a1b0c08ca7a8b542`; bytes 70479280 -> 70479280; allocated 70479872 -> 70479872.
- `/guest/boot/AVPBooter.original.bin`: SHA-256 `6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845` -> `6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845`; bytes 334960 -> 334960; allocated 335872 -> 335872.
- `/guest/boot/AVPBooter.patched.bin`: SHA-256 `593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e` -> `593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e`; bytes 334960 -> 334960; allocated 335872 -> 335872.
- `/guest/boot/runner-identity.json`: SHA-256 `85cdf3ee54faa6043837550cdb1c44eef5d6ce10f295ae5e3513b97ad44be3e9` -> `85cdf3ee54faa6043837550cdb1c44eef5d6ce10f295ae5e3513b97ad44be3e9`; bytes 1422 -> 1422; allocated 4096 -> 4096.
- `/guest/boot/aux.work.img`: SHA-256 `789fae1e482bb88f525fc99dbe754547db490a34c7f969baa4d09bbbb48b1660` -> `2cc56f592406aa515e67d75add8495eba7c32291e622cf79b0fe0817ae784b79`; bytes 33562780 -> 33562780; allocated 33566720 -> 33566720.
- `/guest/boot/root.overlay.qcow2`: SHA-256 `24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c` -> `24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c`; bytes 197360 -> 197360; allocated 200704 -> 200704.

Only persistent guest byte changes: `["/guest/boot/aux.work.img"]`. Runner identity is byte-identical; no remigration/rebase/reset. Original/patched AVP pin and offset 0x2370 remain unchanged. Full original/baseline binary and source hashes are in `guest-metadata-before.json` and `guest-metadata-after.json`.

## Backend, storage, and guards

Backend identity/start/resources/mounts/command preserved: True; alive afterward: True. Existing backend ID `b018c33c5b240dcda2bfea23ae2f8eeb3e673cd98fb8c1618cdf90e50d116d1d`, image `sha256:7810c1732534d73f8cc50f213f1b682eca4e78df6f3b2369cc03285383ee26ac`, eight RAM layers, 2 CPUs, 6 GiB RAM/equal swap limit, readonly root, same volume and `/stream/golden-live5.nbd` endpoint. No existing backend or sampler was replaced.

Verified fetch count 15 -> 17; verified fetched bytes 6304069925 -> 6969278564; fetch starts 15 -> 17. Backend memory.current 4180250624 -> 4177891328 bytes (delta -2359296); lifetime peak delta 0. Memory event deltas `{"low": 0, "high": 0, "max": 0, "oom": 0, "oom_kill": 0, "oom_group_kill": 0}`. QEMU NBD trace request count 1822, requested bytes including repeats 30043648, types `{"read": 1820, "disconnect": 2}`. Complete retained startup events: True. See `backend-deltas.json`, bounded backend logs, `backend-event-summary.json`, `device-access-summary.json` and actual `stderr.log` for NBD/storage/device evidence.

- `guard-after.json`: free 27839258624 bytes; age 0.645s at capture.
- `guard-before.json`: free 27918487552 bytes; age 1.104s at capture.
- `guard-preactual.json`: free 27917328384 bytes; age 0.486s at capture.
- `guard-precheck.json`: free 27917975552 bytes; age 1.211s at capture.
- `guard-snapshot-20261027T193344Z.json`: free 27915505664 bytes; age 1.142s at capture.
- `guard-snapshot-20261027T193506Z.json`: free 27909124096 bytes; age 0.581s at capture.
- `guard-snapshot-20261027T193649Z.json`: free 27910692864 bytes; age 1.996s at capture.
- `guard-snapshot-20261027T193905Z.json`: free 27875917824 bytes; age 1.327s at capture.
- `guard-snapshot-20261027T194115Z.json`: free 27928129536 bytes; age 1.612s at capture.
- `guard-snapshot-20261027T194323Z.json`: free 27925241856 bytes; age 1.209s at capture.
- `guard-snapshot-20261027T194439Z.json`: free 27922702336 bytes; age 0.322s at capture.
- `guard-snapshot-20261027T194610Z.json`: free 27921948672 bytes; age 1.134s at capture.
- `guard-snapshot-20261027T194734Z.json`: free 27920195584 bytes; age 0.470s at capture.
- `guard-snapshot-20261027T194907Z.json`: free 27905593344 bytes; age 0.429s at capture.
- `guard-snapshot-20261027T195014Z.json`: free 27900727296 bytes; age 1.550s at capture.
- `guard-snapshot-20261027T195142Z.json`: free 27904385024 bytes; age 1.021s at capture.
- `guard-snapshot-20261027T195329Z.json`: free 27851816960 bytes; age 0.370s at capture.
- `guard-snapshot-20261027T195454Z.json`: free 27844374528 bytes; age 0.622s at capture.
- `guard-snapshot-20261027T195629Z.json`: free 27848097792 bytes; age 0.419s at capture.
- `guard-snapshot-20261027T195645Z.json`: free 27839651840 bytes; age 0.503s at capture.

The unchanged read_valid_sample enforced C: >=10 GiB, sample age <=20s and future skew <=2s on captured boundaries; launcher/runner/backend retained their existing runtime guards and deadlines. Existing sampler PID 104360 and original creation time were verified before/after. Owned VM resources were 12 GiB/equal swap, four CPUs, network none, readonly root. `owned-vm-live.json` and synchronous `snapshot-*.json` retain live cgroup/process evidence. No extra background job or watcher was created.

## First blocker and limits

The final observed outcome is `diagnostic_limit`, error `Reims diagnostic log reached its eight-MiB guard`. The owned runner issued QMP `quit` after this guard; the retained QMP log has no RESET or GUEST_PANICKED event. The eight-MiB Reims tail contains recurring `OFF` telemetry, including zero object-cache and bound-buffer counters; `terminal-evidence.json` records exact line quotes, prefix counts and the retained-tail limit. The Reims limit is the demonstrated termination cause. The guest stall at Recovery/APFS has no established root cause. This experiment stops here; there is no retry or unqualified patch.

- RTC model remains diagnostic storage, not a complete clock.
- Unavailable CTRR zero-read/discard-write probe does not implement protection.
- NBD layers are verified on demand; no complete RAW conversion or full-layer verification.
- Kernel execution is distinct from adapter contract; Recovery mount is distinct from installed System mount.
- No guest commands, display changes, composited frame, GUI or hardware acceleration evidence.
- VM peak/OOM evidence is sampled while live; --rm removes its final cgroup.
- No root-cause inference from last serial line or correlated layer fetch.

The owned actual/check-only/helper containers are gone; the pre-existing backend and sampler remain alive. `final-verification.json` records this. Retained guest logs were ECID-redacted and printed boot command lines are suppressed; only original CLI hash/length preservation metrics are reported. No payload cache, full RAM or disk capture was taken.
