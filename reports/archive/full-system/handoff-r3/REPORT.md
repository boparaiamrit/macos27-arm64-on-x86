# Staged Golden revision-3 handoff adapter

Staged only. **34 offline tests pass**, including a read-only real capture fixture and fake-GDB mutation/readback tests. No adapter was activated, no VM ran, and no active helper, runner, profile, identity, guest, backend or sampler was changed by this task.

The runtime pair is:

```text
golden_adt_args.py
5a242dd347cc49a2a03bc0a2a6b84e8ba32fc7df1ce59740a223a9dc433d439c

kernel-handoff.gdb
e14fb3450b7876b2fd8285a33d851b8d78a768d45032936bc7bd64d3db0bac7f
```

`golden_adt_args.py` is self-contained. Its first 3,668 bytes are an exact copy of the existing ADT helper, SHA-256 `1801c61af828bc1c9ef27c65cbb27be93ebef1c99a1a44e3c6efbe2cd56d698c`. The added parser/planner imports only standard-library modules. The old helper is not a runtime dependency. `r3-extension.txt` is a staging/provenance artifact already incorporated into the combined module, not an imported dependency.

## Qualified behavior

The GDB script selects `0xe0a00000` by the actual Stage2 end marker, its captured first-24-byte instruction fingerprint, and the complete revision-3/version-2 structure. It has no ignored-hit or ordinal assumption. It validates dynamic memory, entry, argument and translated ADT bounds before any mutation; reads only the exact declared ADT reservation; requires zero tail padding; and plans the entire edit first.

The command-line field is 1,024 bytes at `+0x6c`. Original bytes and arguments remain an exact prefix; missing `-v` and `serial=3` are appended without replacing or normalizing them. Conflicting serial values, ambiguous quoted/escaped serial spelling, non-ASCII/nonterminated input and overflow fail closed. Padding, video data, flags at `+0x470`, and actual memory at `+0x478` are preserved. `memSizeActual` is bounded independently to `(0, 8 GiB]`; it is not treated as a contiguous length from `physBase`.

ADT insertion retains the original helper's policy: add a new `/filesystems/DoNotUseSEP=1` node only when absent; an existing node must already contain the correct value. Missing/conflicting properties in an existing node require inspection. The declared reservation is never rounded or expanded.

Only differing ADT bytes, the permitted tree-length field, and changed command-line bytes can be written. Every complete input is rechecked before the first write, each write is immediately read back, and complete structures are checked afterward. A complete r3 candidate without a drained Stage2 end marker also fails stopped instead of continuing unpatched. A failure disconnects without resuming the stopped guest; no automatic rollback is claimed. Successful verified writes detach and resume. Local result JSON contains hashes, lengths, addresses and preservation/readback evidence; stdout contains only nonprivate metrics and requested options, never the original CLI.

Activation requires the parent's review and identity/profile transaction. `HANDOFF_SCRIPT_DIR` must point to this directory; this qualified profile accepts exactly `HANDOFF_BOOT_ARGS=-v serial=3`, transfer PC `0xe0a00000` and the existing 8 GiB physical RAM bounds. Additional requested options are deliberately refused.

## Actual captured fixture

The tests read original immutable files from `attempts/20261027T191514Z-naxjf_x5`. Their supplied hashes match and remain unchanged after testing:

```text
BootArgs: 53ef287d693feaf233088b9f67c0bd3c689dd9399f7756ad000ffc5ad48af375
ADT:      9894587bda521056eb42a2bbe085730296d423b950f276d20837e642f0bed0a5
```

The parser consumes 562,220 bytes of the 573,440-byte ADT reservation, leaving 11,220 zero bytes. Planning preserves the original 196-byte CLI and appends 12 bytes, for 208 total. It changes 43 bytes across nine minimal ranges: 31 ADT bytes and 12 CLI bytes. The declared tree length stays 573,440. Flags, padding and actual-memory fields stay byte-identical.

`actual-fixture-plan.json` deliberately has `readback_verified=false`: it is only a pure plan. `actual-fixture-apply.json` records successful application to fake in-process memory and is explicitly marked `offline_fixture_only=true`. Neither file establishes guest execution or a real injected handoff.

## Verification and provenance

The 34 tests cover complete r3 layout and dynamic addresses, old revision/version refusal, CLI preservation/conflicts/capacity/encoding, entry/argument/ADT bounds and overlap, malformed trees, nonzero padding, no room, existing NoSEP contracts, changed input before mutation, exact readback failure, byte-identical base-helper copying, real captured data, fake-GDB content selection, detach only after verification, and disconnect without resume on failed readback.

Run:

```powershell
python -B test-output/arm-macos/full-system/handoff-r3/test_handoff_r3.py
```

The observed successful run took 0.578 seconds. All temporary fixtures are confined to this owned directory.

Layout provenance was independently checked against [m1n1 tgtypes.py at 1b7a258](https://github.com/AsahiLinux/m1n1/blob/1b7a258ea1a359beffa6b451890a8a53a6741d1b/proxyclient/m1n1/tgtypes.py) and [revision-3 support commit dbafd05](https://github.com/AsahiLinux/m1n1/commit/dbafd058cfb0fae3b4ec211260e222d8a3733284). The historical support commit carries MIT attribution; the current referenced Python layout file is GPL-2.0-or-later. The new validator is original code from layout facts, with source references retained; the copied ADT implementation and staged adapter remain GPL-2.0-or-later.

The exact Golden header remains unavailable. This adapter qualifies the supplied capture and strict profile; trampoline cleanup-range analysis and actual kernel/userspace/GUI execution remain separate parent-controlled gates. `handoff_pc_verified_for_golden` means the transfer point and inputs were validated, not that XNU executed.
