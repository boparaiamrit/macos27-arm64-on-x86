# Matched Golden handoff contract

The prior end-of-Stage2/reset run did not hit the older `0xaca00000` observer.
Offline analysis of the matched firmware found that its final callback selects
`0xe0a00000`. A read-only live probe reached that site in 15.774 seconds;
a follow-up full capture took 16.736 seconds. Neither changed guest memory or
registers. No kernel execution is claimed from these diagnostic stops.

The complete capture is in `attempts/20261027T191514Z-naxjf_x5/`:

- `golden-boot-args.bin`: 1152 bytes, revision 3/version 2; SHA-256
  `53ef287d693feaf233088b9f67c0bd3c689dd9399f7756ad000ffc5ad48af375`.
- `golden-device-tree.bin`: 573440 bytes; SHA-256
  `9894587bda521056eb42a2bbe085730296d423b950f276d20837e642f0bed0a5`.
- `golden-trampoline.bin`: the bounded 4096-byte actual transfer page.
- `iboot-observation.json`: addresses, registers and capture hashes.

This boot's entry is `0x77554480`, arguments `0x79494000`, and ADT physical
address `0x74610000`. Addresses change between boots and must be derived again.
The entry, arguments and declared tree lie inside the observed kernel-data
interval `[0x70a04000,0x794a4000)`. The normal `physBase+memSize` is bounded
by configured RAM. `memSizeActual` is 8 GiB minus 10 MiB; it is not a contiguous
length to add to the shifted physical base.

Asahi's explicit revision-3 contract keeps the prefix but expands command-line
capacity to 1024 bytes, followed by padding at `0x46c`, flags at `0x470`, and
actual-memory size at `0x478`; total size is `0x480`. The actual capture fits
this layout. Apple's checked public header agrees with the 1024-byte layout,
but an exact released Golden header was unavailable. References:

- [Asahi revision-3 definition](https://github.com/AsahiLinux/m1n1/blob/1b7a258ea1a359beffa6b451890a8a53a6741d1b/proxyclient/m1n1/tgtypes.py#L58)
- [Established revision selection](https://github.com/AsahiLinux/m1n1/commit/dbafd058cfb0fae3b4ec211260e222d8a3733284)

The captured command line terminates after 196 ASCII bytes and contains the
existing root selector `rp0`. Its contents must be preserved, with diagnostic
flags appended within capacity. Flags and the four padding bytes are zero and
must remain unchanged. The obsolete helper's 608-byte replacement is unsuitable.

Strict parsing consumes 562220 bytes of the ADT, leaving 11220 zero bytes inside
its declared reservation. No root-level filesystems node exists. The existing
bounded `add_no_sep` planner succeeds offline: it adds the node in zero padding,
keeps the declared length 573440 and changes 31 byte values. No new allocation
or guessed memory reservation is needed.

Full trampoline disassembly preserves entry in x29 and arguments in x28, then
disables the MMU. Its clearing ranges `[0xe8608000,0xe8648000)`,
`[0xe864c000,0xe8a8c000)`, the x2 cleanup page `[0xe8654000,0xe8658000)` and
self-clear `[0xe0a00000,0xe0a00280)` do not overlap this boot's kernel data,
arguments or tree. At `+0x2a0` it moves x28 to x0 and at `+0x2b8` returns through
the saved entry. Thus the next stage receives the argument pointer in x0.

The separate synthetic PSCI reset test confirms `-no-reboot -no-shutdown`
preserves registers under QMP shutdown state and a GDB SIGQUIT stop. It improves
diagnostics; it does not resolve a guest's underlying reset.

Any activated adapter must select this handoff by content, preserve the root
arguments, validate all ranges and declared padding, and verify each write by
readback. The legacy helpers remain unchanged. New helpers require distinct
admission pins and an explicit identity migration before a real injected boot.
