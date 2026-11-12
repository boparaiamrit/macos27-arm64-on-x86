# AVP RTC diagnostic storage experiment

Build and paused synthetic qualification passed. No Apple guest was run by this task.

Binary: `/work/orchard-golden-avprtc/qemu/build/qemu-system-aarch64` in volume `macos-orchard-build`, exported as `artifacts/qemu-system-aarch64`. Linux and independent Windows SHA-256 agree:

```text
25fa22ad4790a877dc842dca3e97cc06e15fab7ef144a266c04e2790cc2d59a4
```

The only tracked source difference from the preserved scratch variant is `qemu/hw/vmapple/vmapple.c`. It adds per-machine, zeroed 4 KiB register storage at physical `[0x30240000, 0x30241000)`, with little-endian 4/8-byte access and explicit width, alignment and bounds validation. Accepted accesses log offset, width, value, CPU and PC under `LOG_UNIMP`; rejected transactions log direction, offset and width. Reset clears the store. It supplies no host time, clock progression, PL031 identity, success bits or claimed RTC protocol.

The existing PL031 at `0x20050000`, the 16 KiB scratch fix, configuration RAM, renderer and PCI changes remain unchanged. No CTRR region at `0x30260000` was added.

The diagnostic storage concept and logging are adapted from Yahia's GPL-2.0-or-later [commit 4671e2b](https://github.com/tqmane/qemu-vphone/commit/4671e2ba6a39e5998446d35ac93dd746f5ef6f47), specifically its AVP RTC portion. Source comments preserve attribution and identify unknown register semantics. No board identity, NVRAM, DFU/USB, AES or CTRR change was imported. `avprtc-only.diff` is the focused delta; `orchard-golden-avprtc.diff` includes the prior Golden/scratch changes against Orchard `c73a2bda1fd4afefd61204bb74afd74292ef2fe9`.

## Verification

`memory-result.json` and the QMP/qtest evidence cover a paused synthetic WFI machine, never resumed:

- Exact 4 KiB I/O mapping and zero initial storage, including the observed guest probe at offset `0x40`.
- Normal 4/8-byte little-endian read/write and reset clearing.
- Rejected byte/halfword, unaligned 32-bit, and outside-region writes do not change valid storage or crash.
- The actual C transaction-validation predicate was compiled with UBSan and exercised against valid endpoints, invalid sizes, unaligned addresses, boundary crossings and `UINT64_MAX`.
- Original PL031 IDs remain `31 10 14 00 0d f0 05 b1` before/after reset. The first test fixture incorrectly assumed PID2 `0x04`; source inspection established its existing value `0x14`. That failed fixture is preserved under `fixture-failure-1/`.
- The prior scratch range still starts zero, accepts first/final-word writes and clears on reset. Config bytes stay unchanged.
- Existing PCI smoke passes: ascending Golden root/AUX/network capabilities and both disks' Apple type-9/vendor-`0x106b`/length-14/flag-1 capabilities; baseline control remains descending.

**Bus decomposition limit:** qtest's memory API splits some unaligned or cross-region 64-bit requests into valid aligned 32-bit transactions. For example a write at offset `0xffc` can update its valid last four bytes before its outside half reaches unmapped space. The device cannot recover that original request width from the split callbacks. The final test verifies the exact permitted in-range effects and restores them; it does not claim atomic cross-region rejection. `fixture-failure-2/` preserves the earlier overly strong fixture assertion. Each transaction reaching the device is independently bounds checked; no out-of-array access was observed or permitted.

These results qualify a diagnostic register store, not a working clock, Apple firmware boot, XNU, mounted installed root, launchd or GUI.

## Preservation and resources

Full before/after regular-file and symlink manifests match for `/work/orchard`, `/work/orchard-golden` and `/work/orchard-golden-scratch`. Those three trees were read-only overmounts during building; the entire volume was read-only during smoke/audit. The final audit compared 12,031 tracked paths against scratch and found only `qemu/hw/vmapple/vmapple.c` different. Original binary and Reims archive hashes remain pinned in `final-audit.json`.

The existing builder image, local wheels/Python environment and static Reims archive were reused with networking disabled and `PIP_NO_INDEX=1`; no image/package download or Rust build occurred. Build duration was 220.125 seconds, with six CPUs / six GiB limits, equal swap cap and a 900-second outer bound. Peak cgroup memory was 4,410,064,896 bytes; no OOM events occurred. Fresh host-space checks retained the unchanged 10 GiB floor throughout; minimum during build was 29,661,986,816 bytes. Later audit measured 29,509,050,368 bytes free.

The final audit measured 440,373,248 allocated bytes for new source/build and 86,041,600 for host outputs, about 0.490 GiB combined before the small final report/records. These task-path allocations do not account for every host volume change. All owned containers are stopped and retained for evidence.

The parent owns runner admission, persistent identity migration and live boot. This task did not edit a guest, firmware, runner, launcher, observer, profile, guard, backend, sampler or ACTIVE-STATE file.
