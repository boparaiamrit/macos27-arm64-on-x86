# Source-and-offline-unit report

Result: **52 CPU-only tests passed**. No actual mouse API fixture, USB/HID
qualification, guest delivery, button effect, or GoldenDesktop proof exists
from this work. Those checkpoints are **unknown**. This is an offline freeze
for parent review, followed only by a separately authorized future controlled
API case. No future case was executed or scheduled.

## Scope and source evidence

All issued writes were confined to new files under this `mouse-guest/` directory.
No delegation was used. No Docker/QEMU/Cargo command, probe, download, real
socket, VM input, graphics operation, working CONTROL/state/RAW access,
existing service change, or external-process enumeration/signalling was issued.
The parallel real RGB10 VM, its frames and session were not read or touched.
The only terminated process was an owned offline Python test child after a
test-monitor inventory race. Tests remove their own generated temporary files
during normal teardown; no existing project/guest cleanup occurred.

The codebase-memory skill, applicable AGENTS instructions, and specifically
requested TDD skill were read. Graph tools were absent; exact source inspection
was the fallback. No graph coverage/completeness claim is made. The existing
interactive controller, fixed-file helper, CLI, entrypoint, README and parent
review were read only. No existing controller suite or historical fixture was
rerun. Reference source hashes are observations in
`reference-source-sha256.json`, not a binary/build/runtime validation.

The new adapter wraps the unchanged `frame_qmp` factory and forwards its kwargs,
including capture binding. It uses one original QMP constructor/socket,
sequence, receive buffer, guard, pump and transcript. The wrapper retains sibling
import paths, MTTCG configuration, core filter, shader capture bind-before-QMP,
and original `run_with_capture` extraction in finally. It restores temporary
factory/loader/attempt hooks even on error. No old source was changed.

The launcher was cloned from inspected RGB10 source. Its complete source parity
test admits only these differences: mouse container/launcher/controller metadata,
metadata destination inside this owned directory, new entrypoint, enable flag,
fixed cleanup4 readiness validation, and 900/800 default/upper bounds. Guest,
profile, readiness filename, image pin, resources, mounts, MTTCG/SIMD/copy/shader
flags, RAW readiness/ownership checks, and remaining argv are preserved. The
PowerShell test intercepts **every Docker/admission-file/creation/metadata call**;
no real Docker resolution or parent metadata write occurs. Neither a real
CheckOnly nor a real launcher run occurred.

The inspected profile source and parent identify RGB10 QEMU SHA256
`87614fc2db5efc0f7293aad13d1f70ffd43d4e3e09380dfd5522ffd419d7202b`.
The binary itself was not opened or rehashed. The Apple metadata report says
LSUIElement=true and also records an authored Quit menu item with q/0x100000/
terminate:. This implementation therefore does not claim a button-only app,
invalid Cmd+Q, broken keyboard, or focus cause. Its purpose is one future
visible-button click with stronger approval and effect evidence.

## TDD evidence

Production controller/helper/CLI/wrapper/launcher files did not exist during the
initial red runs. Missing product behavior was asserted as a failing feature,
not hidden by import failures. The chronological logs are preserved:

| Phase under `evidence/` | Observed result |
| --- | --- |
| `red-contract` | 34 tests, 34 expected missing-feature failures before product code |
| `red-launcher` | 36 tests, 36 expected missing-feature failures before product code |
| `green-contract-01` | Aborted by monitor inventory race with test-owned directory removal; partial log and samples retained; no result JSON |
| `green-contract-02` | 36 tests passed after monitor race correction |
| `red-cleanup-audit` | 46 tests, four reproduced behavioral failures: unsafe cleanup quit bytes, missing cleanup guard bypass block, stale paused approval, paused post capture |
| `green-cleanup-audit` | 46 tests, one test-helper error because the now-invalidated latest frame was assumed present; retained, then helper corrected |
| `red-cleanup-guard` | 50 tests, one reproduced pre-wire guard failure |
| `green-50` | 50 tests passed |
| `red-post-proof` | 52 tests, missing post-error receipt surfaced as a test dereference error; retained |
| `red-post-proof-receipt` | 52 tests, corrected assertion reproduced one explicit missing-receipt failure before the receipt fix |
| `green-final-52` | **52 tests passed**, exit 0 |

The aborted run left a small `tests/cpu-far4kjed/` directory containing only
authored fake transport/PNG/state data. It is retained as aborted-run evidence,
not a real guest session or operator approval. No fixture from an existing
attempt was used. The freeze manifest includes it separately as generated test
evidence. Diagnostic lines in tests deliberately exercise refusal paths.

Meaningful coverage includes separate down/up IDs and exact event shapes;
inclusive endpoints/rounding; bool/float/outside/NaN/schema/nonce refusal;
missing/stale/dimension-mismatched/disabled/link-rejected frame zero-down;
fresh running queries; STOP/RESET/panic and unknown status; ID/replay/capture
caps and restart denial; durable owed state/deadline before any down bytes;
partial press without blind up; lost press ACK followed by one up with late
press ACK skipped; future IDs not crediting unsent up; release errors/loss/
interrupt/deadline expiry forcing fatal cleanup; exact critical owner/transcript
error propagation; interrupts/SystemExit; failing frame receipts; up+3s proof;
explicit post-failure receipt; 40-character IDs and proof fitting 4 KiB;
Windows stable-reader atomic replacement; host CLI preview without QMP;
factory/binding/import/finally/deadline preservation; original owned cleanup
extraction proving no further bytes and owned termination; and mocked PS argv.

## Measured offline bounds

Final child unittest runtime: **5.102 seconds**. Monitored harness wall time:
**5.5535661 seconds**, 24 samples, minimum C: free **14,113,878,016 bytes**,
peak Python test-child working set **46,755,840 bytes**. The latter does not
include the separate short PowerShell mock child's working set. Final test
stdout is empty and stderr is a small unittest log, far below 2 MiB. Source,
docs, tests, logs and generated fake evidence remain far below the 64 MiB cap.
See `green-final-52.result.json` and `.guards.jsonl` for raw observations.

The harness samples fresh host free space before launch and approximately every
0.2 seconds during the child, rejects <10 GiB, limits each child to 120 seconds,
and bounds owned outputs to 64 MiB and child logs to 2 MiB. It enumerates only
this new owned directory for byte accounting and observes only its own child
handle. Normal teardown races are ignored for disappearing entries; stable
evidence files remain counted. No test sleep occurs in the controller or owner
VM deadline. The original resource guard and cleanup reserve are retained.

## Remaining limits

All wire/process behavior here is simulated using in-memory JSON, generated
PNG bytes, and non-process doubles. Separate sync semantics, default tablet
routing, actual HID queue reports, pointer movement, guest focus, app receipt,
button effect, RGB10 rendering and the desktop remain unqualified in this work.
An ACK is never delivery proof. The parent must review source and the fatal
release protocol before owning any future controlled API case; this report
does not authorize or perform that case or a macOS input attempt.
