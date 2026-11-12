# Single bounded Golden scratch boot

The authorized run completed in **17.458 seconds** with `iboot_observation_captured`, diagnostic kind `iboot_panic`. Launcher exit 0 means the diagnostic was captured; the guest remains blocked in iBootStage2. No retry was performed.

- Actual attempt: `20261027T181146Z-yt5vh29l`; CheckOnly: `20261027T181138Z-cqyo6t25` (`inputs_validated_no_vm`).
- Actual launch: 2026-10-27 18:11:46 UTC / 23:41:46 IST. Observation: 2026-10-27T18:12:03.748346+00:00. Completed well before 00:18 IST on 28 October.
- Serial reached **Microkernel iBootStage2 for vma2, mBoot-20457.1.29**, UUID `4B48E51D-1870-375E-B660-278677B2CCE0`; last marker `a60aa294185a059:986`.
- The read-only observer stopped at the content-validated Stage2 panic caller `0x700d9164`, source marker `4962211b03d706d:203`. Serial had not printed an `iBoot Panic:` line when the debugger stopped it.

## Exact blocker

`ESR_EL1=0x92000010`, `ELR_EL1=0x70087788`, `FAR_EL1=0x30240040`. The exception class is `0x24`, WnR is 0, and DFSC is `0x10`: a lower-EL read data abort with synchronous external abort. The saved exception context has `x8=0x30240040`.

The retained code snapshot disassembles as:

```text
0x70087780: mov  w8, #0x40
0x70087784: movk w8, #0x3024, lsl #16
0x70087788: ldr  w8, [x8]
```

This captured fault is the read of VA `0x30240040`, after the full Stage2 banner. The former write-abort instruction at `0x700b0200`/VA `0x4ffff8` is not this captured exception. The target device, physical translation, and reason the read aborts require separate diagnosis; no device-success response, register write, memory patch, or source fix was attempted.

There are **no trampoline-hit JSON files** and `boot_args_candidates=[]`. `handoff_verified=false`, `kernel_execution_verified=false`, `full_gui_verified=false`. Reims output records Vulkan rail selection and device reset only; it does not establish guest driver attachment, rendered graphics, or a GUI.

## Commands and containment

```powershell
& ./test-output/arm-macos/full-system/Launch-FullAttempt.ps1 -GoldenScratch -CheckOnly -StreamVolume macos-golden-stream-large-state -ReadyName stream-ready-large-live5.json
& ./test-output/arm-macos/full-system/Launch-FullAttempt.ps1 -GoldenScratch -IBootDiagnostic -ColdStreamedBoot -TraceStorage -Timeout 1800 -HookTimeout 1700 -StreamVolume macos-golden-stream-large-state -ReadyName stream-ready-large-live5.json
```

Both were invoked unchanged from `<WORKSPACE>/macos`; stdout/stderr was retained through `Tee-Object` under this directory. The actual launcher retained the immutable runtime image `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`, 12 GiB memory/same swap, 4 CPU limit, network none, read-only root, and the existing guest/work/stream mounts. QEMU and GDB both returned 0 during normal diagnostic cleanup. The CheckOnly, VM, and one post-run read-only metadata helper containers are all absent; see `owned-processes-final.json`. The helper used the same existing runtime image, network none, read-only mounts/root, 512 MiB memory/same swap, one CPU, and read/hash/disassembly operations only. It did not start a backend or guest.

Backend `b018c33c5b240dcda2bfea23ae2f8eeb3e673cd98fb8c1618cdf90e50d116d1d` remains alive on immutable image `sha256:7810c1732534d73f8cc50f213f1b682eca4e78df6f3b2369cc03285383ee26ac`, 6 GiB/same swap, 2 CPU, volume `macos-golden-stream-large-state`, socket `/stream/golden-live5.nbd`. The old `macos-golden-stream` remains stopped. Sampler PID **30680** remains alive with its original start time. Neither backend nor sampler was stopped, restarted, or refreshed.

## Storage progress and guard evidence

The trace contains **1788 read requests**, **397 unique offset/length pairs**, **30,369,280 requested bytes including repeats**, and **25,517,568 bytes in the union of requested ranges**. The highest requested end is `44675690496` (exclusive). There are 0 `nbd_co_request_fail` trace lines. `nbd-progress.json` retains the merged intervals. These are requests, not an independent completed-byte counter.

Backend verified fetch count stayed **14 to 14**, with no new layer fetch starts. The final verified event remains layer 46, cumulative compressed fetched bytes **5,868,108,106**, cached bytes **4,060,323,840**. Earlier layer-1/layer-46 fetches and the historical Broken pipe belong to the preceding completed attempt and were not counted as new progress. `all_disk_layers_verified=false`; no payload caches or disk images were copied.

The before/after guard samples were read using unchanged `host_space_sample.read_valid_sample`. Minimum **captured** free space was **31,151,538,176 bytes**, maximum captured sample age **1.798 seconds**, above the unconditional **10,737,418,240-byte** floor and within 20 seconds / 2 seconds future tolerance. No guard bypass, backend deadline failure, or new guard/timeout event was observed. The runner's continuous checks do not retain individual successful samples, so the true continuous minimum is unavailable.

Backend `memory.current` was 4,157,140,992 before and 4,158,676,992 after; container-lifetime `memory.peak` stayed **4,383,297,536 bytes**. `memory.events` remained all zero, including OOM/OOM-kill; swap current was zero. The guest container was removed promptly before a cgroup peak/OOM snapshot could be taken. Its configured limits and clean child exits are recorded; its peak is unknown. Existing 900-second per-layer, 3600-second initialization, and external supervisor source hashes were not changed.

## Pins, retained files, and limitations

All **168 captured host source/input hashes** match before and after, including launcher, runner, observer, scratch profile, guard helper, backend/reader/supervisor, frozen converter files, APFS sources, manifest/config, readiness file, and ACTIVE-STATE. See `source-hashes-before.json`, `source-hashes-after.json`, and `source-comparison.json`.

CheckOnly and actual `validated-inputs.json` are identical. Post-run direct read-only hashes confirm scratch QEMU **673cfd8b73b03b72e89ef6c312dd73612e4c625725e675b424579b5ade1acc1f**, original firmware **6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845**, and existing patched firmware **593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e** remain equal to their validated pre-run values. The current identity differs from the preserved pre-scratch identity only in `qemu_sha256`; no migration/reset/rebase was run.

Observer snapshot SHA256: **cbc68cbde6f8d3b3e86606096006fc6bc86065c7d5c527515996b53b177264e1**, equal to both before/after source hashes. The one-MiB diagnostic code snapshot SHA256 is **899d569847efb4ad7d806c070f73b163b9a6db5da1e3d69632983e1214d3bf31** and is verified against its observation JSON. This is a bounded diagnostic capture, not a full RAM dump. Total copied attempt/CheckOnly diagnostic bytes: **1,301,657**. Serial/text diagnostics have been checked and redacted for the private ECID.

Working AUX changed from **6ca0a44e1a0ab39909cf43538a06d5cabafc99af9547c430aa2ca50eecd04044** before boot to **673e2b716943e5f99c70300b9f3febc4aa616798e3b44bd4e8223b9c3a2195b3** after the authorized run. Overlay allocation stayed **200,704 bytes**, far below 2 GiB. The post-run file is **197,360 bytes**, SHA256 **24a0cbc2df59906167a958a2ae21dcca64f1c76fa59807337df7f688a1b6407c**; pre-QEMU qemu-img reported child virtual-size 197,632 bytes. A pre-run overlay byte hash was not captured, so byte-for-byte preservation is not claimed. The launcher was allowed to mutate working guest state naturally.

The next blocker is the Stage2 read abort at **0x30240040**. Kernel execution, a normal handoff, full disk verification, continuous resource minima, and GUI operation remain unverified. This task stopped at its first completed diagnostic without any retry or source change.
