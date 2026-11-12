# Chapter 4 — Golden Gate `0xE0A00000` XNU Handoff, `BootArgs_r3`, `NoSEP` ADT & `wdt=-1`

## Objective
Bridge the final transition from `iBootStage2` to the installed macOS 27 XNU kernel (`Darwin Kernel Version 27.0.0`) and mount the sealed `Macintosh HD` (`disk3s1`) + `Data` (`disk3s5`) volumes instead of falling back to Recovery OS.

## Key Learnings & Breakthroughs

### 1. Handoff PC Moved from `0xACA00000` → `0xE0A00000` (`BootArgs_r3` / Version 2)
macOS 13-era `27on86` GDB injectors set a breakpoint at `0xACA00000` and expect `BootArgs` revision 2 / version 2. On macOS 27 Golden Gate (`8 GiB` RAM based at `0x70000000`), that breakpoint never fires!
- **Discovery:** Tracing the final `iBootStage2` jump revealed XNU entry at **`PC = 0xE0A00000`** with `x0` pointing to a **`BootArgs_r3` (revision 3, version 2)** structure featuring a 1024-byte command-line buffer.

### 2. Preserving the 196-Byte Root CLI & Injecting `NoSEP` into ADT Zero-Padding
Naive boot-arg injectors overwrite the entire `CommandLine` string with `-v serial=3`, **destroying** `iBoot`'s 196-byte root-volume UUID selector (`rd=uuid ...`) and forcing XNU into Recovery!
- **Fix (`src/handoff-and-firmware/adt_no_sep.py` & `handoff-r3-wdt-kernel-handoff.gdb`):**
  1. Preserved `iBoot`'s exact 196-byte root CLI and *appended* `-v serial=3 wdt=-1` cleanly within the `BootArgs_r3` command-line bounds.
  2. Verified `11,220` bytes of zero-padding at the tail of the in-memory Apple Device Tree (`DT_PA = DT_VA - virtBase + physBase`) and surgically inserted the **`NoSEP`** property/node (43 bytes modified total, verified by 34 offline + 70 runner tests) so `AppleKeyStore` / `sep` kexts don't hang waiting for a physical Secure Enclave Processor.

### 3. Solving the False `missing-boot-media` Recovery Redirect (`wdt=-1`)
On our first preserved-CLI boot, Darwin 27 booted, validated the APFS System/Data selectors (zero seal errors!), and yet rebooted into Recovery reporting `missing-boot-media`!
- **Root Cause:** XNU's `bsd_init` waits **60 seconds** for the root block device (`disk3s1`) to finish APFS container enumeration, whereas decompressing a cold 500 MiB LZFSE OCI layer under TCG took **~89 seconds**!
- **Fix:** Appending `wdt=-1` alongside our RAM-backed NBD read cache eliminated watchdog/timeout aborts. Result:
  - `serial.log:84`: `Darwin Kernel Version 27.0.0`
  - `serial.log:405–431`: `BSD root: disk3s1`, on-disk cryptographic root-hash validation **PASSED**, `Macintosh HD` mounted!
  - `serial.log:1402–1570`: `disk3s5` (`Data`) mounted, `Early boot complete`, `launchd` -> `WindowServer` started!
