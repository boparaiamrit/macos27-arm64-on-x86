# Chapter 3 — Disassembling `AVPBooter`, Patching `0x2370`, and Emulating Missing Apple Silicon Hardware

> [!CAUTION]
> **Interoperability Research Notice:** The hardware and boot-chain notes below document clean-room systems interoperability analysis of QEMU's open-source `vmapple` / `apple-vm` machine model (`hw/vmapple`). No Apple firmware binaries (`AVPBooter`, `iBoot`) are included in this repository. Only run macOS guests on official Apple-branded hardware in compliance with Apple's Software License Agreement (see [`LEGAL.md`](../LEGAL.md)).

## Objective
Get Apple's `AVPBooter.vmapple2.bin` -> `iBootStage1` -> `iBootStage2` firmware chain to boot cleanly into XNU on `qemu-system-aarch64` (`-M apple-vm`).

## Key Learnings & Breakthroughs

### 1. Firmware Patch Offset Migration: `0x2314` (macOS 13–15) → `0x2370` (macOS 27)
Legacy `vmapple` scripts blindly patch `AVPBooter` at offset `0x2314`. On macOS 27 (`AVPBooter` size `334,960` bytes, SHA-256 `6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845`), `0x2314` lands inside unrelated instructions!
- **Discovery:** Disassembling the binary identified the Image4 manifest-property validator (`CEPO`, `ECID`, `CHIP`, `BORD`, `DGST`) at **`0x2370`**.
- **Fix:** Applying an exact 8-byte return-0 stub (`mov w0, #0; ret`) at `0x2370` (`SHA-256: 593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e`) unlocked `iBootStage1` (`mBoot 20457.1.29`) and loaded `illb` + `logo`.
- **AUX Storage Contract:** `aux.img` wraps its payload with a 16 KiB header; QEMU's `pflash` / `vmapple-virtio-blk-pci,variant=aux` requires the exact 16 KiB-stripped AUX image paired to the machine UUID/ECID.

### 2. `iBootStage2` Data Abort (`ESR 0x92000050`, `FAR 0x4ffff8`) → Missing 16 KiB Scratch RAM
Once `iBootStage2` started, it immediately panicked! Attaching a read-only GDB observer (`src/handoff-and-firmware/observe-iboot.gdb`) captured:
- `ELR_EL1 = 0x700b0200`, `ESR_EL1 = 0x92000050` (Data Abort), `FAR_EL1 = 0x4ffff8`.
- Walking the guest page tables proved `iBootStage2` maps a **16 KiB low physical scratch SRAM region** around `0x4fc000–0x500000` that upstream `apple-vm` never mapped!
- **Fix (`src/qemu-apple-vm-patches/scratch-ram-16k.diff`):** Mapping a dedicated 16 KiB RAM region in `apple-vm` immediately got past `0x700b0200` and printed the full `iBootStage2` banner!

### 3. `0x30240040` Unmapped MMIO Hang → AVP Real-Time Clock (`avprtc`)
Next, `iBootStage2` faulted/spun reading physical MMIO `0x30240040`. Cross-referencing Golden Gate's Apple Device Tree (ADT) strings identified `0x30240000` (`4 KiB`) as the **AVP RTC** block.
- **Fix (`src/qemu-apple-vm-patches/avprtc-mmio.diff`):** Adding a bounded 4 KiB logged register-storage MMIO model satisfied `iBootStage2` RTC probes cleanly (verified under UBSan).

### 4. CTRR 64 KiB Absence Probe (`ctrr-probe-64k.diff`)
`iBootStage2` / early kernel probes Apple's Configurable Text Readonly Region (`CTRR`) 64 KiB MMIO aperture. Mapping a clean 64 KiB probe region advertising zero active lock magic prevented unmapped physical bus aborts.

### 5. `AppleVPKeyStore` & Silent `cipher-stub.c.inc` Failure → `--enable-nettle`
Even after reaching Darwin, `vmapple`'s hardware AES DMA engine (`hw/vmapple/aes.c`) logged `Failed to create cipher object`!
- **Root Cause:** Building QEMU without `nettle-dev` (`libnettle`) caused QEMU's `crypto/cipher.c` to silently link `cipher-stub.c.inc`, which unconditionally fails every AES-CBC/ECB request!
- **Fix (`orchard-build/golden-crypto`):** Building QEMU with `--enable-nettle` (`nettle 3.10.1`) passed **12/12 NIST SP800-38A** AES-128/192/256 ECB/CBC known-answer DMA tests over QTest (`test-aes-mmio.py`).
