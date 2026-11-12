# CTRR absence-probe experiment

Build and paused synthetic qualification passed. No Apple guest was run by this task.

Binary: `/work/orchard-golden-ctrr/qemu/build/qemu-system-aarch64` in volume `macos-orchard-build`, exported as `artifacts/qemu-system-aarch64`. Linux and independent Windows SHA-256 agree:

```text
dba936f79fdfecea6163360d4beea0495cf2e870c11816a6a1b0c08ca7a8b542
```

The only tracked source difference from the preserved AVP RTC variant is `qemu/hw/vmapple/vmapple.c`: include the existing `hw/misc/unimp.h` and map `create_unimplemented_device("avp-ctrr unavailable", 0x30260000, 0x10000)`. `CONFIG_UNIMP` was already selected, so no Kconfig change was needed.

This is a logged placeholder for an absent device. Reads return zero and writes are logged/discarded through QEMU's unchanged generic implementation. It advertises no CTRR identification magic, version or banks, and implements no protection, locking or enforcement. No RTC, PL031, scratch RAM, PCI, CPU, firmware, board identity, NVRAM or host feature was changed.

The exact mapping/helper precedent is the GPL-2.0-or-later [tqmane/qemu-vphone commit 3ed8577](https://github.com/tqmane/qemu-vphone/commit/3ed85774c2989addec3056a866991762b60c4b5c), `hw/vmapple/vresearch101.c` AVP_CTRR map and `create_avp_stubs`. QEMU's generic helper and implementation retain their existing Peter Maydell/Linaro copyright and license. `ctrr-only.diff` is the focused delta; `orchard-golden-ctrr.diff` includes prior changes against Orchard `c73a2bda1fd4afefd61204bb74afd74292ef2fe9`.

## Verification

The paused synthetic WFI machine was never resumed and received no Apple input. `memory-result.json`, `memory-mtree.txt`, QMP evidence and `memory-stderr.log` establish:

- Exact `[0x30260000, 0x30270000)` I/O mapping at priority `-1000`.
- First/last valid byte, word and qword probes return zero.
- Writing `0x63747272` at offset zero does not advertise that magic: readback stays zero. Final-byte/qword writes are also discarded.
- Reads remain zero after reset; actual generic read/write logs are retained.
- Prior RTC storage, reset and transaction validation; real PL031 IDs; scratch RAM read/write/reset; config preservation and PCI contracts still pass.

`test-transaction-bounds.py` again compiles the unchanged RTC predicate with UBSan. Existing bus decomposition limits remain: qtest can split an unaligned or cross-region request into legal smaller transactions. No stronger atomic rejection or out-of-bounds guarantee is claimed for QEMU's generic helper.

This qualifies only the mapped absence probe. It does not establish that Golden's subsequent state/security checks succeed or that XNU, installed root, launchd or GUI boot.

## Preservation and resources

Full before/after regular-file and symlink manifests match for all four earlier trees: `/work/orchard`, `/work/orchard-golden`, `/work/orchard-golden-scratch` and `/work/orchard-golden-avprtc`. They were read-only overmounts throughout setup/build. The whole volume was read-only during smoke/audit. A final audit compared 12,031 tracked paths against AVP RTC and found only the intended `vmapple.c` delta. Original binary and static Reims archive hashes remain pinned in `final-audit.json`.

The existing builder image, offline Python environment/wheels and Reims archive were reused, with networking disabled and `PIP_NO_INDEX=1`. No Rust build, image/package download, host change or cleanup occurred. Build duration was 213.762 seconds under six CPUs / six GiB, equal swap cap and a 900-second outer bound. Peak cgroup memory was 1,883,414,528 bytes, with no OOM. Fresh host samples retained the unchanged 10 GiB floor; minimum guarded build free space was 28,876,910,592 bytes. The later audit measured 28,849,184,768 bytes free.

Final audit allocation: new source/build 440,217,600 bytes; host outputs 90,407,936 bytes, about 0.494 GiB combined before the small final report/records. These task-path allocations are not a complete account of host volume changes. All owned build/smoke/audit containers are stopped and retained.

The parent owns review, runner admission, identity migration and live boot. This task did not edit profiles, identities, guest state, firmware, runner, launcher, observer, guards, backend, sampler or ACTIVE-STATE.
