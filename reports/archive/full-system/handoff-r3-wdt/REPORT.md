# Staged root-service wait diagnostic

STAGED PASS — **46 offline tests pass**. No active helper/profile/runner/identity, guest, AUX, VM, binary, backend or sampler was changed. Parent review and transactional activation remain separate.

Frozen runtime pair:

```text
golden_adt_args.py
d629671ab3518ddc8abb40e74e30ec5557a068ec6ba07f3d95bb79f28eb7cf3b

kernel-handoff.gdb
e14fb3450b7876b2fd8285a33d851b8d78a768d45032936bc7bd64d3db0bac7f
```

The GDB script is byte-identical to qualified `handoff-r3`. The combined helper differs only in `REQUESTED_ARGS = '-v serial=3 wdt=-1'` and `append_boot_arguments`: append missing `wdt=-1`, do not append it again when already present, and refuse conflicting values or ambiguous quoted/escaped settings. Original command-line bytes remain an exact prefix. Capacity checks include the added token. Every other byte of the helper outside that constant/function is unchanged; layout, ADT edits, bounds, fingerprint, input recheck, minimal writes, readback and stopped-on-failure behavior are inherited unchanged. No automatic rollback was added or claimed.

The parent must select this directory and exact requested string. The unchanged script hash permits a helper-hash-only identity change if the parent's remaining preflight/identity conditions match. This staging task performed no migration or activation.

## Why this is a controlled timing test

The parent supplied an observed `missing-boot-media` Recovery reason and a cold disk-layer fetch lasting 89.067 seconds. In the inspected [public Apple XNU reference](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/iokit/bsddev/IOKitBSDInit.cpp#L849), the release root-service wait interval is 60 seconds. That code parses `wdt`; the Recovery timeout branch runs when it is not `-1`, and the root-service loop continues while no service matches.

Thus this option permits a longer root-service wait to test the timing hypothesis. It does not create matching media, change its UUID, force a match, or establish mount/authentication eligibility. The exact Golden kernel source/header is unpublished; this public reference and the parent's observed reason are distinct evidence. Missing-media eligibility may still fail. No installed System root or GUI success is claimed.

No kernel NOP, SSV, UUID, GPIO or additional ADT modification was introduced. The parent's 1,800-second wall bound, 10 GiB host floor, 2 GiB overlay cap and 900-second NBD layer bound are unchanged by these staged files.

## Offline qualification

All **34 base r3 tests** were rerun with explicit new option expectations, including fake-GDB readback failure, content selection and missing-marker stopped behavior. Twelve additional tests cover watchdog conflict/deduplication, prefix/whitespace preservation, empty command line, quoted/escaped refusal, exact capacity boundary, wrong requested string, byte-identical GDB script, scoped helper diff, and both actual captures. The complete suite passed in **0.696 seconds** with Windows `python -B`.

The tests read captures without altering them:

| Fixture | Original CLI | New CLI | ADT reservation | Non-CLI plan |
|---|---:|---:|---:|---|
| Normal System `20261027T201625Z-nxu_x5bi` | 0 bytes | 18 bytes | 573,440 bytes | Identical to base r3 |
| Recovery `20261027T191514Z-naxjf_x5` | 196 bytes | 215 bytes | 573,440 bytes | Identical to base r3 |

The normal System fixture uses the trampoline bytes already captured in `iboot-observation.json`; the Recovery fixture has its separate trampoline file. Both validate the same captured transfer page hash. Original inputs retain their hashes. Each plan was successfully applied to fake in-process memory with exact readback; this is offline validation, not a live injected handoff. `actual-fixtures.json` records hashes and metrics without exposing the original CLI.

The tests compare complete ADT output/patches and all non-command-line BootArgs bytes against the original helper. Only CLI output differs. Normal/Recovery plans change 49/50 bytes respectively across nine bounded ranges; the previous NoSEP ADT changes remain identical.

Run:

```powershell
python -B -m unittest discover -s test-output/arm-macos/full-system/handoff-r3-wdt -p 'test_*.py'
```

The copied runtime files retain GPL-2.0-or-later attribution and the prior layout provenance. Apple source was consulted only for the public argument/control-flow contract; no Apple kernel code was copied or patched.
