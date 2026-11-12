# Golden Stage2 scratch-RAM experiment

Built and paused synthetic checks passed. No Apple guest was run by this task.

The new binary is `/work/orchard-golden-scratch/qemu/build/qemu-system-aarch64` in volume `macos-orchard-build`, also exported as `artifacts/qemu-system-aarch64`. Final SHA-256:

```text
673cfd8b73b03b72e89ef6c312dd73612e4c625725e675b424579b5ade1acc1f
```

The only tracked source change from the existing Golden tree is `qemu/hw/vmapple/vmapple.c`: add exactly 16 KiB of ordinary RAM at physical `[0x4fc000, 0x500000)`, and zero that region on machine reset. Existing configuration RAM stays at `[0x400000, 0x410000)`, 64 KiB. No host-service response, CPU behavior, firmware patch, guest input, renderer or PCI transport change was added. `scratch-only.diff` is the focused delta; `orchard-golden-scratch.diff` includes the existing Golden patch set against Orchard commit `c73a2bda1fd4afefd61204bb74afd74292ef2fe9`.

This tests the parent's measured hypothesis: Golden 26A428 Stage2 intentionally writes a pointer at physical `0x4ffff8`, where the previous machine has no RAM. It does not prove the higher-level protocol, a successful host service, or macOS boot. The existing Reims report mentions an earlier donor widening config to 1 MiB, but that broader mapping was not adopted here: <https://github.com/steelbrain/reims-vgpu/blob/12adb1fb46953ae55d4a7b2d66d9110bb19b0b1a/docs/qemu.md#macos-27-guests-2026-10-14>.

## Verification

`memory-result.json` records a paused synthetic WFI machine with no Apple input:

- The full 16 KiB scratch range starts zero.
- Writes to its first and final eight bytes read back through qtest; HMP `xp` independently shows the final value.
- Reset clears the full range, while the original 64 KiB config bytes remain unchanged.
- `info mtree` confirms both exact ranges. The baseline tree has no new scratch region.
- QMP reports `running=false`; the machine was never resumed.

`smoke-result.json` also records the existing PCI contract check: the baseline remains descending without the Apple transport capability; the new binary retains ascending root/AUX/network lists, with both disks' Apple capability type 9, vendor `0x106b`, length 14, flag 1 and subsystem `0x1100`.

The first paused smoke caught a RAM migration-owner assertion. That failed attempt is retained under `failed-smoke-1/`; the corrected code registers the machine-owned RAM with a NULL owner. The initially reported `58b8...` binary is superseded by the final hash above. No Apple input was used in either attempt.

## Preservation and resources

Both original trees were read-only overmounts during setup/build and the whole volume was read-only during smoke/audit. Full regular-file/symlink manifests before and after match for `/work/orchard` and `/work/orchard-golden`. A separate final audit compared 12,031 tracked paths and found only the intended new-tree `vmapple.c` difference. Original hashes remain:

```text
baseline QEMU 6e84c533ce4f9fe1c7a01745219a8ce5a9fe06b38bd80db14720147df8ce42dd
Golden QEMU   2fca0114c7f37fac34d9e13def8c5c66850ac5e2d2c8a19365c0631f02b57705
Reims archive 32720f5ea9a0dfd7d388714e9c2b7818c98e9cf1e761140318ead212cb799a47
```

The existing builder image and static Reims archive were reused; there was no Rust build or image/package download. Fresh host samples and the unchanged 10 GiB floor were checked throughout compilation. Build limits were six CPUs / six GiB with swap capped at the same value; main compile peak was 1,768,620,032 bytes, with no OOM. Minimum guarded host free space during successful build phases was 31,160,115,200 bytes. All owned containers are stopped and retained for evidence.

`final-audit.json` measures 440,430,592 allocated bytes for the new source/build tree and 81,171,456 bytes for host output at that audit (before this small report and final container record). The aggregate is about 0.486 GiB. These task-path allocations are not a complete account of host volume changes.

The first offline configure found missing Python build packages in the new checkout. The retained configure failure was resolved by using already acquired wheels and the existing Golden Python environment read-only, with `PIP_NO_INDEX=1`. No network was enabled. The successful configure/compile, owner correction, exact Docker mounts/caps, source manifests and QMP transcripts are retained alongside this report.

The parent owns persistent runner identity admission and the next guarded live boot. No runner, launcher, guest AUX/overlay, firmware, backend, sampler or ACTIVE-STATE file was edited by this task.
