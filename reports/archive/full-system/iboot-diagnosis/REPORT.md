# Golden 26A428 Stage2 data abort

The eight-layer cached boot reached iBootStage2 and panicked before XNU.
Its boot required zero additional OCI layer fetches. The 1701-second runner
timeout followed the guest panic; it does not identify the initiating defect.

Read-only debugger attempt `20261027T175212Z-honl93ys` stopped before the
panic routine in 12.493 seconds. The observer required this attempt's Stage2
serial marker and different loaded code from Stage1. It changed neither guest
registers nor memory. The normal XNU handoff helper was not invoked.

- ESR_EL1 `0x92000050`: lower-EL write data abort, synchronous external abort.
- ELR_EL1 `0x700b0200`: `str x0,[x8]`.
- FAR_EL1 `0x4ffff8`; saved exception-frame x8 is also `0x4ffff8`.
- The exception handler constructs panic identifier `0x4962211b03d706d`,
  sets line 203, and calls the panic routine. This ties the observed exception
  to the serial panic rather than guessing from the hash.

Actual 16 KiB page-table walk, from TTBR0_EL1 `0x70000000`:

| Level | Descriptor address | Descriptor |
|---|---|---|
| 1 | `0x70000000` | `0x8000000070004003` |
| 2 | `0x70004000` | `0x800000007000c003` |
| 3 | `0x7000c9f8` | `0x00e00000004fc46b` |

The faulting virtual address translates to physical `0x4ffff8`.

The destination is intentional: instructions at `0x70086a7c–0x70086a84`
construct base `0x4fc000` and call `0x700b0170`. That initializer installs
cursor/lower-bound `base+0x3ff8` and upper-bound `base+0x4000` in globals
at `0x70132cd8`. The caller submits a pointer to a request record at the
last eight bytes of this 16 KiB region. Its nonzero-status branch exists;
the complete request protocol and optional-service fallback remain unverified.

Orchard's configuration device is ordinary writable RAM only at physical
`0x400000–0x410000`, defined by `vmapple.c:120` and `cfg.c:24,158–164`.
Nothing covers the faulting physical region in the inspected machine map.

The separate experimental emulator adds only RAM at `0x4fc000–0x500000`.
This tests the missing-memory hypothesis; it does not implement a host service,
invent a successful response, change CPU/PAC behavior, or modify guest firmware.
The existing binary and guest AUX/overlay must be preserved, with an explicit
one-field binary identity migration before the next boot.

Related primary-source context: Reims records a contributor widening the config
window to 1 MiB, but omits it after a native-HVF boot succeeded. The inspected
HVF MMIO implementation discards failed transactions, so that success does not
establish TCG behavior. See the exact source links below.

- [Reims guest-version notes](https://github.com/steelbrain/reims-vgpu/blob/12adb1fb46953ae55d4a7b2d66d9110bb19b0b1a/docs/qemu.md)
- [HVF MMIO transaction handling](https://github.com/steelbrain/qemu-reims-vgpu/blob/c7a4f0700f8dc05f067a3266dffc51802ce64238/target/arm/hvf/hvf.c#L2718)

No XNU, installed root, launchd, or graphical desktop has been verified.

The separately built QEMU 673cfd8b73b03b72e89ef6c312dd73612e4c625725e675b424579b5ade1acc1f passed paused memory/read/write/reset and existing PCI checks. Explicit identity migration changed only qemu_sha256, with identical AUX and overlay hashes before/after. Its first real boot passed the former abort and printed the full iBootStage2 banner; subsequent boot-data reads are underway. This verifies the targeted abort correction, not XNU or GUI.
