# Chapter 1 — Booting macOS 27.0.1 (`26A434`) Restore RAMDisk to an ARM64 Root Shell on x86_64

## Objective
Before attempting a 50 GB installed Apple Silicon desktop OS on an Intel/AMD Windows 11 + WSL2 host without Apple Hypervisor.framework (`HVF`), we needed an airtight proof that **Darwin 27.0.0 (`RELEASE_ARM64_T8112`)** boots to interactive userspace under software ARM64 translation.

## Key Learnings & Breakthroughs

### 1. Selective ZIP Member Fetching Instead of Downloading Full 15+ GB IPSWs
Apple's official restore manifests expose exact byte ranges inside the IPSW ZIP archive. Using HTTP range requests (`src/restore-ramdisk/fetch-restore-parts.py`), we fetched only the 6 required boot components for board `j473ap` (`T8112` M2 Mac mini) from macOS `27.0.1` (`26A434`) without downloading or unpacking a 15 GB IPSW.

### 2. Bypassing Mac-Only RAMDisk Re-Signing via Single-User `-s`
Many Apple Silicon QEMU guides require mounting and modifying the restore RAMDisk on a physical Mac. Instead:
- We paired [`darwin-vm`](https://github.com/jprx/darwin-vm) (`edfc1943`) with [`qemu-sptm`](https://github.com/jprx/qemu-sptm) (`bad6336f`, QEMU 11.1.0), which applies the in-memory `AppleImage4` ignition patch (`hw/arm/xnu_patch.c`) and Linux-compatible Apple Device Tree (ADT) fixups.
- Passing `-s` in boot-args dropped straight into the unmodified restore RAMDisk's built-in single-user root shell (`uid=0(root)`).

### 3. Fixing the `CRCRLF` (`\r\r\n`) Serial Terminal Framing Bug
Our initial automated serial expect driver (`src/restore-ramdisk/drive-serial.py`) timed out waiting for command completion even though commands had already succeeded.
- **Root Cause:** The Darwin serial line discipline + QEMU console emitted `\r\r\n` (`CRCRLF`), whereas standard regex line matchers expected `\r?\n`.
- **Fix:** Normalizing `+` before line matching enabled deterministic verification of `uname -a` (`Darwin 27.0.0 RELEASE_ARM64_T8112 arm64`), `/usr/bin/id`, and `/bin/ls /` (`src/restore-ramdisk/verify-evidence.py`).

### 4. Host Storage Safety Guard (`10 GiB` Unconditional Floor)
During early multi-container builds, Windows `C:\` pagefile expansion (`commit 145/154 GB`) + non-sparse WSL2 `docker_data.vhdx` growth pushed host free space dangerously low. We engineered `host_space_sample.py` enforcing an unconditional **10 GiB free-space floor** polled every `200 ms` across all subsequent builds and VM runs.
