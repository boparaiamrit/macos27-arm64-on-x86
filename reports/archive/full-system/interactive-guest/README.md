# Opt-in, single-action guest input

This is a separate adapter for parent review. Existing launchers do not enable
it. No real macOS guest was launched or given input during this work. The one
synthetic API fixture is documented in [REPORT.md](REPORT.md).

`Launch-InteractiveAttempt.ps1` preserves the fresh-01 launcher arguments,
resources, QEMU profile, fixed `/guest/fresh-01`, RAW-export readiness checks and
10 GiB reserve. Its changes are the owned container prefix, launcher metadata,
new Python entrypoint and `INTERACTIVE_GUEST_INPUT=on`. CheckOnly passes through
the original preflight and does not create an input session or frame.

`run-interactive-attempt.py` loads the unchanged frame wrapper. It wraps the
wrapper's frame factory, retaining capture bind-before-QMP-construction, the
sole QMP socket, sequence, transcript, MTTCG arguments, core filter, original
runner lifecycle and shader extraction in `finally`. The loaded attempt entry
records a conservative deadline immediately before the unchanged runner sets
its own deadline. Input RPCs share a ten-second operation budget capped by that
deadline. The overall VM deadline is never extended.

## Host protocol

Use an exact attempt directory name from the owned launch result. The CLI has
no latest-attempt discovery. It cannot open a second QMP connection.

```powershell
$inputCli = './test-output/arm-macos/full-system/interactive-guest/request.py'
python -B $inputCli --attempt EXACT_ATTEMPT show
python -B $inputCli --attempt EXACT_ATTEMPT capture --id capture-01
python -B $inputCli --attempt EXACT_ATTEMPT show
```

Wait for the matching `response.json` request ID before submitting another
request. The runner polls only after its own `query-status` returns, on the
same thread and socket. A submitted request is not a delivery receipt.

For an actual action the parent must first open the exact retained file named
by `current-frame.json` using `view_image`, observe Keyboard Setup Assistant,
and copy its exact SHA256. Historical images, OCR, inferred text and timed
automatic input are insufficient. Only then may the parent submit:

```powershell
python -B $inputCli --attempt EXACT_ATTEMPT quit_keyboard_setup_assistant --id quit-01 --frame-sha256 EXACT_CURRENT_SHA256 --attest-view-image-keyboard-setup-assistant
```

The attestation flag asserts exactly:

> I inspected this exact retained frame with view_image and saw Keyboard Setup Assistant.

The fixed request slot is `attempt/input/request.json`. For capture its complete
schema is:

```json
{"version":1,"id":"capture-01","attempt":"EXACT_ATTEMPT","nonce":"64-lowercase-hex-from-session.json","operation":"capture"}
```

The action adds exactly `frame_sha256` (64 lowercase hex) and `attestation`
(the exact sentence above), and changes `operation` to
`quit_keyboard_setup_assistant`. Unknown fields, duplicate JSON keys, nonfinite
numbers, invalid IDs, wrong nonce/attempt, links, nonregular or oversized files
are refused. Request files are at most 4096 bytes. The host atomically replaces
this slot. Direct file authors must use the same atomic publication and wait
for matching responses; do not append a journal or create another inbox.

The session publishes an exact allowlist and limits: six requested captures,
32 accepted request IDs and one total action. IDs and individual files are
bounded; the adapter keeps fixed state/current-frame/latest-response files.
Directory identities are pinned, POSIX access uses directory descriptors and
`O_NOFOLLOW`, and Windows opens reject reparse paths and pin directories against
replacement. Regular file readers allow atomic replacement using stable handles.

Before input, the owner requires observed running status, captures again through
its existing frame owner, checks running status again and compares that fresh
image SHA to the approved SHA. A clock update can make this refuse as
`frame_stale`; no key is sent and no retry occurs automatically. A fresh duplicate
capture points to an existing retained same-SHA image with the new capture
timestamp. It never invents a missing duplicate file.

The action is durably consumed before any wire send. The exact command is:

```json
{"execute":"send-key","arguments":{"keys":[{"type":"qcode","data":"meta_l"},{"type":"qcode","data":"q"}],"hold-time":100},"id":"next owner integer sequence"}
```

The actual ID is the owner's next integer, not the illustrative string. No
device selector, arbitrary key, pointer, focus, stop, reset or retry action is
accepted. A positive matching acknowledgement means
`acknowledged_interaction_unproven`. A partial send, lost acknowledgement or
ambiguous reply means `uncertain_delivery`, consumes the action and quarantines
input for the rest of the attempt. It is never labeled failed/no-delivery.

Three seconds later, a normal status poll attempts one owner capture and status
proof without sleeping inside the controller or changing the VM deadline. See
`state.json`'s `post_action_frame` and `post_action_status`. The parent must inspect
the resulting image and actual guest state to establish interaction; the
adapter never sets `interaction_proven=true`. An expired deadline or failed proof
stays explicit. Underlying resource/host guards and interrupts propagate to the
original lifecycle. If an interruption or guard occurs after possible wire
delivery, quarantine is persisted before re-raising; the durable consumed state
still prevents another action if a small quarantine receipt cannot be written.

## Proposed parent command, NOT executed

Parent review and a new live instruction own actual guest execution. The exact
proposed first command is the separate CheckOnly path:

```powershell
& ./test-output/arm-macos/full-system/interactive-guest/Launch-InteractiveAttempt.ps1 -CheckOnly -QemuProfile m27-pages-io -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup3-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

If admitted by the parent, the proposed boot command differs only by removing
`-CheckOnly`. Neither command was executed in this task. The retained fresh-01
working pair is reused; this adapter does not prepare, reset or repair it.

Offline tests:

```powershell
python -B -m unittest discover -s ./test-output/arm-macos/full-system/interactive-guest -p 'test_*.py' -v
```

The synthetic harness already ran once. Do not run it again as an automatic
validation step. Its only owned container has been removed.
