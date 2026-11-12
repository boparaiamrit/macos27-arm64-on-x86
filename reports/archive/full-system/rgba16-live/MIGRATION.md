# Parent-only migration recipe

This worker did not execute migration, CheckOnly, Docker, a VM or guest input.

Use existing runtime `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`, a unique owned helper name, network none, read-only root, 1 CPU/512 MiB/equal total memory-swap, pids128, core0 and bounded tmp16MiB. Preserve the normal process-local core filter0x10 and a bounded owner deadline. Mount only:

- `macos-orchard-build` -> `/work`, read-only.
- `macos-golden-pristine-guest` -> `/control`, writable.
- `macos-golden-stream-read-cache-state` -> `/stream`, read-only.
- Host `test-output/arm-macos` directory -> `/parent`, read-only (directory mount preserves atomic guard samples).

The exact entry command is:

```bash
python3 -B /parent/full-system/local-raw/migrate-m27-pages-rgba16-identity.py --parent /parent --guest /control/fresh-01 --socket /stream/golden-live5.nbd --ready /parent/full-system/stream-ready-local-raw-cleanup4-live5.json
```

The command takes the normal existing boot lock, checks fresh host space and the 30-second migration deadline, exact old identity `5c81e522ad43cf7ad8fd015f007de62a0842b5871c51db131eac64e2ef22d9cb`, exact ready record, old/new emulator/archive and handoff pins, original firmware/AUX/prepared metadata and actual read-only NBD negotiation. It then backs up the exact old identity bytes, fsyncs backup and replacement, verifies AUX/overlay unchanged, atomically replaces only the QEMU field, fsyncs the directory, and verifies readback. No CLI override for old identity/ready digest exists. Original failed `/control/boot` is never selected.

After parent review/migration, the exact rendering-only CheckOnly is:

```powershell
& ./test-output/arm-macos/full-system/rgba16-live/Launch-Rgba16Attempt.ps1 -CheckOnly -QemuProfile m27-pages-rgba16 -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup4-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

No actual CheckOnly or boot was run by this worker. Parent owns admission and the live decision.
