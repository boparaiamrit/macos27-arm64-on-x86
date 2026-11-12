# Guest-input adapter: offline proof and one synthetic API qualification

Ready for parent source review, with actual guest input still unqualified and
unexecuted. Only new files under `interactive-guest` were written. No core runner,
old wrapper/launcher, Rust source, admitted binary, guest state, CONTROL, RAW,
exporter, sampler, unrelated process or service was modified. No download,
maintenance, real macOS VM or delegation was performed by this worker.

The supplied parent source findings establish that VMApple creates qemu-xhci,
usb-kbd and usb-tablet (`vmapple.c:531-549`); an unbound handler accepts a NULL
display source without a host window (`ui/input.c:113-135`). The candidate uses
the existing owner's `send-key` path, `meta_l` then `q`, explicit hold-time 100.
The supplied exact-fork source analysis (`ui/input.c:692-715`) reports presses in
order and reverse-order releases queued before acknowledgement with virtual-time
delays. This task did not independently re-probe that source or claim guest HID
delivery. A paused VM can stall those releases; running status and post-frame
inspection remain mandatory. `input-send-event.device` is not used.

The codebase-memory skill was read by the parent; graph/index/coverage tools were
unavailable. This worker read exact named source files and
`full-system/reims-study/AGENTS.md`, without a graph coverage claim. Relevant
prior QMP qualification guidance was checked in memory, then its current REPORT,
harness, loop bytes and PNG validator were read directly.

## Final offline evidence

**22 unittest methods pass** in `tests-green.txt`. Red evidence precedes each
implementation/fix in `tests-red.txt`, `host-tests-red.txt`,
`deadline-tests-red.txt`, `synthetic-tests-red.txt`,
`runtime-path-tests-red.txt`, `guard-propagation-tests-red.txt`,
`post-wire-guard-tests-red.txt`, `reader-sharing-tests-red.txt` and
`guard-value-error-tests-red.txt` and `wrapper-import-tests-red.txt`.

Coverage includes nonce/exact-attempt/schema/attestation/ID/path binding; stale
frame, wrong SHA, not-running and STOP-during-approval zero-send refusals; exact
wire chord/hold/strictly increasing shared sequence; replay and one-action limit;
partial send and lost acknowledgement quarantine; events/late IDs; bounded
captures and retained duplicate lookup; construction order; default and
CheckOnly off; original attempt/finally preservation and conservative deadline;
and PowerShell mocked-Docker argv parity. The mock intercepts metadata writes
and starts no container. The PowerShell test uses all optional runtime flags
with the original defaults for overall bounds (7200/1700); the proposed parent
command above uses the previous actual boot's 900/800 bounds.

Resource guards are wrapped only to remember their original exception, then
immediately re-raised. Red/green cases prove RuntimeError and ValueError are not
converted into request refusals, and guard failure after possible wire delivery
persists quarantine. KeyboardInterrupt and SystemExit also persist post-wire
quarantine and propagate unchanged. A final Windows-only regression verifies a
stable host reader cannot block atomic receipt publication. These guard and
original-directory import-path and Windows reader corrections followed the single synthetic run; they have final
offline proof, with no additional runtime experiment. The chord serialization
and send-key transport were unchanged after that run.

## One actual synthetic fixture

Owned container: `macos-input-synth-76a989e4c9e3`.
Evidence: `runs/macos-input-synth-76a989e4c9e3/host.json`,
`fixture-result.json`, `qemu-command.json`, guard journal, original-owner QMP
transcript and frame index. Container start
`2026-10-28T21:24:50.823784954Z`; finish
`2026-10-28T21:24:55.996508912Z`; exit 0; outer elapsed 5.737 seconds.

Pinned QEMU `/work/orchard-m27-pages-io/artifacts/qemu-system-aarch64` was
SHA-verified to `8db719ff2982a216e64aa2303c8731bdc0d8a2051919f69bc95bbcbd1dd3829b`.
Existing image:
`sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`.
Mesa26 runtime manifest SHA
`5711c1e0cc73a67cd8643f1d84591651a75f0de2ad27315f0c7709035ba63a0e`
and every listed runtime component were verified. Build volume and both runtime
mounts (`/soft`, `/out/runtime`) were read-only.

Generic virt/cortex-a72, TCG, one vCPU and 1 GiB virtual RAM ran only the same
24 authored AArch64 loop bytes as the earlier qualification, with PC
`0x40200000` and RAM counter `0x40201000`. The machine had ramfb, qemu-xhci and
usb-kbd, display/serial/monitor disabled, and no disks, Apple code or guest-state
volume. Fixture SHA:
`daac6d121cbb22bec1a85e87ccb4071c2c4da0082a51d11463e19228d13fa1fe`.

The sole client was the unchanged core QMP class, extended by the unchanged
FrameQMP factory and the new input subclass. Capabilities, status, synthetic-only
cont, HMP counter reads, captures and the chord were serial on that one socket.
The fixture durably consumed its synthetic action then directly called the exact
production chord method. It did **not** submit a fake Keyboard Setup Assistant
attestation or add a product bypass flag. This qualifies the transport and real
QMP reply, while the full approval policy is proven by offline tests.

The exact `send-key` wire request had integer ID **7**, ordered qcodes
**meta_l, q**, and hold-time **100**. There was exactly **one** send-key command
and its matching positive reply. Status was running before and after. Counter
before `0x0000000000dc68d9`, after `0x00000000b4b87749`, delta
**3,017,543,280**. Only RESUME was observed; no STOP/SHUTDOWN event was observed.
This does not prove continuous execution at every instant or guest HID delivery.

A three-second later owner capture completed, then fresh status was running.
It duplicated the first image and correctly reported retained
`frames/frame-0001.png` with capture index 2 and a fresh timestamp. PNG validation
verified signature, dimensions, chunk CRCs, IEND and deflate: **640x480**, **1569
bytes**, SHA
`39684f2364d14965a755c9b1034ae6aa1386d96a5f09625a3eed232881df1fba`.
The black synthetic ramfb surface qualifies API only. It is not macOS rendering,
Keyboard Setup Assistant, desktop, HID delivery or interaction evidence.

## Bounds and preservation

Container limits: 2 CPUs, 2 GiB memory/equal total swap (swap.max 0), pids 128,
network none, read-only root, cap-drop ALL/no-new-privileges, tmpfs 64 MiB,
RLIMIT_CORE 0 and 2 MiB per-file limit. The original helper set process
coredump_filter 0x10; QEMU inherited `00000010` with readback. Peak cgroup memory
145,543,168 bytes; all OOM counters zero. The fixture's process handle ended and
the exact uniquely named container was removed successfully. No other process
or container was enumerated or stopped.

Host guard: 124 fresh samples, maximum poll gap **0.0700651 s**, unconditional
10 GiB floor, allowed sample age [-2,20] s. Minimum sampled C: free bytes
**12,099,100,672**; independently measured minimum **11,875,876,864**. Outer bound
110 seconds plus at most eight-second owned cleanup stays within 120 seconds.
The host would stop only its exact unique container on low/stale/unreadable
sample, polling gap, timeout or 60 MiB retained-output threshold.

All ten original protected host files match the existing parent admission's
SHA256 values. `protected-source-verification.json` records exact current values
and comparisons. `artifact-manifest.json` freezes the new sources, docs, red/green
evidence and all fixture artifacts. It excludes itself; `handoff.json` records
the proposed parent command and scoped unknowns. No actual parent CheckOnly or
boot command was executed. Parent review owns any next live instruction.
