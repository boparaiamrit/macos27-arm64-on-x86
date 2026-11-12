# GoldenGate virtio storage and network implementation

Completed in the isolated shared clone `/work/orchard-golden` in Docker volume `macos-orchard-build`, based on Orchard `c73a2bda1fd4afefd61204bb74afd74292ef2fe9`. The clone has its own index and working files, with read-only access to the baseline's Git objects. Only this Windows `golden/` directory and the new volume subdirectory were written.

The deliverable is `artifacts/qemu-system-aarch64`, an x86-64 Linux executable with AArch64 TCG and Reims linked in. SHA-256:

```text
2fca0114c7f37fac34d9e13def8c5c66850ac5e2d2c8a19365c0631f02b57705
```

The build completed with the existing `macos-orchard-builder:local` image. Configuration and full C/C++ compile output are in `compile.log`; the required Orchard network-default follow-up compile is in `network-rebuild.log`. The full compile took 1m55s, and the incremental follow-up took 1.62s. `reims-link-rule.txt` identifies the unchanged baseline archive directly in the linker inputs; there was no Cargo build rule or Rust compilation.

## Demonstrated behavior

`smoke-result.json` records passing before/after assertions against live PCI configuration read through ECAM using QMP's HMP `xp` command. The byte dumps, QMP transcript, command arguments, stderr, and device trees are retained. The baseline control confirms descending lists and absence of the new Apple vendor capability. The final Golden binary confirms:

- Network `00:01.0`, ECAM `0x40008000`: `0x40 -> 0x50 -> 0x60 -> 0x70 -> 0x84 -> 0`.
- AUX `00:03.0`, ECAM `0x40018000`: `0x40 -> 0x50 -> 0x60 -> 0x70 -> 0x84 -> 0x98 -> 0xa4 -> 0`.
- Root `00:04.0`, ECAM `0x40020000`: the same ascending chain as AUX.
- Both storage devices: Apple vendor capability at `0xa4`, PCI capability ID `0x09`, length `14`, virtio `cfg_type = 9`, vendor `0x106b`, disabled-transport-encryption flag `1`, subsystem ID `0x1100`.
- Network inherits `x-ascending-capabilities = true` from the Apple machine. No `-global` or device property override was supplied.

The original patch-only binary's failed network assertion is preserved in `attempt-1/`. This exposed the Orchard subclass compatibility-array issue, fixed as documented in `PATCH-PROVENANCE.md`.

The final smoke used `apple-vm`, `-accel tcg,thread=single`, one vCPU, 1 GiB guest RAM, `-S`, `-display none`, and `REIMS_VGPU_WINDOW=0`. The real `reims-vgpu-mmio` device was realized, with GPU enabled at its default; no graphics stubs were selected. Its ARM64E guest page shift remains 14, with the transport source and ABI header byte-identical to baseline (`guest-page-evidence.txt`).

Only a four-byte synthetic WFI firmware and two zero-filled 16 KiB disks were supplied. QMP confirmed `running=false`, and all three synthetic files remained byte-identical. QEMU was never resumed. Each smoke attempt has a 30-second bound and completed in approximately 0.1 second, then exited cleanly via QMP `quit`.

Software Vulkan was Mesa Lavapipe 25.2.8 with LLVM 20.1.2, reporting Vulkan 1.4.318, 8-bit storage support, viewport-index output support, and `VK_EXT_external_memory_host`. See `lavapipe-summary.txt`, `lavapipe-features.txt`, and `runtime/`. Required Vulkan features were not disabled or bypassed.

This proves compilation, device realization, and PCI capability configuration. It does not demonstrate Apple firmware execution, disk I/O, DRIVER_OK, macOS boot, a GUI, shader execution, or hardware acceleration. No Apple OS input, full-disk conversion, kernel handoff helper, or HVF patch was used.

## Baseline preservation

`baseline-volume-before.json` and `baseline-volume-after.json` match exactly: 16,944 regular-file/symlink manifest entries across `/work/orchard`, including its Git metadata, binaries, Reims archive, and Rust target cache. The baseline tree was mounted read-only for setup, compilation, and verification; the entire volume was read-only for smoke runs.

`baseline-windows-check.json` confirms all 53 pre-existing Windows Orchard build files match their original sizes and SHA-256 hashes, with no additions outside this `golden/` folder.

Unchanged baseline binary SHA-256:

```text
6e84c533ce4f9fe1c7a01745219a8ce5a9fe06b38bd80db14720147df8ce42dd
```

Unchanged Reims staticlib SHA-256 (both original and baseline QEMU copy):

```text
32720f5ea9a0dfd7d388714e9c2b7818c98e9cf1e761140318ead212cb799a47
```

The supplied source patch copies also match their originals; see `patch-hashes.json`. Upstream author and license information is preserved.

## Resources and reproduction

All retained task containers have 6 CPU / 6 GiB limits with swap capped at the same 6 GiB. The full-build cgroup peak was 1,564,721,152 bytes (1.46 GiB); incremental rebuild peak was 413,847,552 bytes; final smoke peak was 83,660,800 bytes. No OOM events occurred. Container settings and writable sizes are in `containers.json` and `limits.json`; allocation accounting is in `footprint.json`.

The new source/build directory used 453,910,528 allocated bytes. Windows output, including exported executable and copied software-driver libraries, used approximately 232,443,904 bytes at export. Existing images and baseline archives were reused. Sampled host C: free space remained approximately 59 GiB, above the requested 10 GiB floor.

Reproduction scripts are `setup.sh`, `prebuilt-reims.py`, `apple-network-default.py`, `compile.sh`, `run-smoke.sh`, and `smoke-pci.py`. `setup.sh` is intentionally guarded to require a new `/work/orchard-golden` path; do not rerun it on this completed tree. The complete source patch is `orchard-golden.diff`. Supply this folder at `/out`, the volume at `/work`, and mount `/work/orchard` read-only. Build with `PKG_CONFIG_PATH=/work/orchard-golden/pkgconfig`; the smoke requires the owned `runtime/` folder at `/out/runtime`. `docker start -a orchard-golden-smoke` repeats the saved smoke within its original caps and read-only volume mount.

No host packages, upgrades, Docker restarts, prune operations, unrelated deletions, or other workers' artifacts were changed. Task containers are retained stopped for evidence and reproducibility.
