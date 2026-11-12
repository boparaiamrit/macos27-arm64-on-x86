# Fixed mouse approval protocol, version 1

## Files and authority

The original runner creates an exact attempt. The controller exclusively creates
`attempt/mouse/`; an existing directory prevents a restarted session gaining
another click. Session creation failure disables input. No latest-attempt lookup,
reconnect, second QMP client, external PID discovery, or external signal is used.

The bounded fixed names are `session.json`, `state.json`, `current-frame.json`,
`request.json`, and `response.json`. Each JSON file is at most **4096 bytes**.
Nonce is 64 lowercase hex characters. IDs/attempt names are 1–40 characters,
`[A-Za-z0-9][A-Za-z0-9_-]*`. There are at most 32 accepted IDs, six requested
captures, and one durably consumed click for the entire attempt. Repeated IDs
are refused. Identical request bytes are not polled repeatedly. Unknown fields,
duplicate JSON keys, nonfinite JSON, and nonregular/oversized files are refused.

Directory chains are pinned by identity, without links/reparse points. POSIX
uses directory handles and `O_NOFOLLOW`. Windows pins directory handles without
DELETE sharing and opens regular readers with READ|WRITE|DELETE sharing (7),
then uses `ReplaceFileW` to publish over a stable open reader. Publication fsyncs
the temporary file before atomic replacement; POSIX also fsyncs the directory.
No request can supply a path. Frame reads use the original attempt's `frames/`,
the original 8 MiB/file cap, a 512 retained-name scan cap, exact SHA256 matching,
and PNG IHDR signature/CRC/dimensions. A pruned duplicate can identify an existing
same-SHA retained image with this capture's new observation time. Missing files
are never invented. A frame-receipt publication failure clears approval and
quarantines input even if frame processing had already begun.

`session.json` lists exactly `capture` and `click_keyboard_setup_quit` and the
exact attestation. `state.json` retains accepted IDs, requested captures,
`click_consumed`, `quarantined`, `release_owed`, `release_deadline`, press framing,
press/release QMP IDs, and post-proof results. It does not claim guest delivery.
File readers must wait for the matching response ID before replacing the single
request slot. Submission/preview is not an owner response or delivery receipt.

## Request schema

Every request has exactly these base fields:

| Field | Required value |
| --- | --- |
| `version` | integer 1; bool is refused |
| `id` | new valid request ID |
| `attempt` | exact selected attempt directory name |
| `nonce` | exact nonce from that attempt's `mouse/session.json` |
| `operation` | `capture` or `click_keyboard_setup_quit` |

For a click, add exactly these fields:

| Field | Required value |
| --- | --- |
| `frame_sha256` | exact current retained PNG SHA256, 64 lowercase hex |
| `width`, `height` | actual verified PNG integer dimensions, each >1 |
| `x`, `y` | integer pixel center inside the human-observed labeled Quit button |
| `attestation` | exact sentence below |

> I inspected this exact retained PNG with view_image, saw Keyboard Setup Assistant and its visibly labeled Quit button simultaneously, and approve this pixel center inside that button.

`capture` has no additional fields. All coordinate/dimension values must be
integers, not bool or float; NaN/Infinity are refused. Require `0 <= x < width`
and `0 <= y < height`. The fresh PNG dimensions must equal the requested
dimensions, whether 1920×1080 or another verified size. Absolute values are
`round(x*32767/(width-1))` and `round(y*32767/(height-1))`: both endpoints are
inclusive, 0 through 32767. There is no clamp or guessed display scaling.

The host CLI requires an explicitly supplied nonce and compares it with the
selected session. `--preview` constructs/validates the request but publishes
nothing. Neither preview nor submit opens QMP. The boolean attestation option
is an assertion by a future human operator; it is never inferred from pixels,
OCR, old approvals, colors, an earlier shortcut ACK, or a timer. Unit tests use
clearly authored fake requests and generated images, never human testimony.

## Before a down event

After schema/session validation, durably record the new ID. Refuse quarantined
sessions, exhausted limits, nonrunning status, an already consumed click, or
missing/mismatched current approval. Capture again through the **same FrameQMP**
instance. Require unchanged exact PNG SHA/dimensions, no invalidating event,
and an independent `query-status` result with `running is True` and
`status == 'running'`. Suspended does not qualify, even though QEMU's API permits
input in that state. Nonrunning observations clear approval. Unknown status
quarantines; STOP, RESET, SHUTDOWN, guest panic/crashload quarantine and invalidate
approval even if an old scanout survives.

Run the original guard. Require at least eight seconds remaining in both the
ten-second operation budget and the original owner's deadline. Durably save
`click_consumed=true`, `release_owed=true`, and a cleanup deadline of the minimum
of operation/owner deadlines and now+5 seconds **before any down bytes**.
The original deadline is conservatively set immediately before the original
runner starts its clock: `start + timeout - 10` for an actual run. No poll sleeps,
deadline extension, floor override, or mouse hold delay is added. Each down/up
ACK budget is at most two seconds, additionally capped by the armed cleanup
deadline. Every adapter receive, capture receive, and status command is capped
by the original owner deadline. The original socket's short send timeout remains.

## Wire contract

Both commands use the existing socket, original sequence/IDs, JSON framing,
transcript, guards, and receive correlation. No `device` or `head` is sent:
QEMU's device selector identifies a display, not `usb-tablet`. The default
unbound tablet route is intended. There is no HMP, arbitrary RPC operation,
keyboard chord, relative pointer operation, or delay event.

First RPC, with the next integer owner ID:

```text
execute: input-send-event
arguments.events:
  abs x = approved transformed X
  abs y = approved transformed Y
  btn left down = true
```

Second, distinct sequential RPC, with the next integer owner ID:

```json
{"execute":"input-send-event","arguments":{"events":[{"type":"btn","data":{"button":"left","down":false}}]},"id":"illustrative only: the next integer owner ID"}
```

The actual release ID is an integer, not the explanatory string. Each command
requires its own positive matching `{return:{}}` ACK. Unrelated, earlier, late,
or future IDs do not acknowledge the current command. QMP events are processed
while waiting. Down and up are never combined into one array: one command has
one final sync, which can collapse a combined array to the last button state.
Two commands preserve separate down/up syncs under the supplied QEMU contract;
this has **not** been qualified on any actual QEMU/HID instance in this task.

The parent-supplied source contract is qapi/ui.json 1133–1142 inclusive absolute
range, tablet logical/physical max 0x7fff, public key/btn/rel/abs/mtt union without
delay, and hw/input/hid.c 111–155,164–220 separate synced queue entries. It was
accepted as authoritative for implementation, not rediscovered or runtime-tested.

## Release obligation and fatal fallback

QMP has no send-key-style automatic up for this primitive. HMP `mouse_button 0`
is forbidden because its separate static state can ignore this QMP press.

| Outcome | Mandatory handling |
| --- | --- |
| Proven zero-down refusal | Click remains unconsumed; no automatic retry. A later new ID and fresh human approval can be considered if not quarantined. |
| `sendall` fails/interrupts during press | Outbound framing is uncertain. Keep owed/consumed/quarantined durable; no more bytes, reconnect, or repeated down. Raise fatal cleanup (or propagate KeyboardInterrupt/SystemExit). |
| Full press frame written, ACK lost/negative/uncertain | Unless guard, deadline, or guest invalidation forbids it, send exactly one explicit up with the next ID on the same socket. Skip late press replies while correlating up. Never repeat down. |
| Up positively acknowledged | Persist `release_owed=false`. A lost press ACK still quarantines the session; release cleanup is not another click. |
| Up unconfirmed/error/lost/partial/late | Retain `release_owed=true`, quarantine, and raise `MouseCleanupRequired` immediately. This is a RuntimeError outside the core GuardError hierarchy, so the status loop cannot suspend polling and leave the button down until 900 seconds. |
| Critical original guard or transcript failure | Persist quarantine best effort and propagate the exact original error immediately. Do not send an up or bypass the failed floor to try cleanup RPCs. |
| STOP/RESET/panic after possible down | Keep the obligation, quarantine, and force original owned lifecycle cleanup. |
| Interrupt/SystemExit after possible down | Keep durable consumed/owed state. If a complete press was written and limits/guards allow, try the one up; propagate the interrupt. Partial press/up never gets a blind retry. |

The adapter never enumerates/signals processes. During original `stop_children`,
if release is still owed or a critical guard already failed, `command('quit')`
raises a pre-wire Refusal (ValueError). The unchanged owner catches it and
terminates **its existing Popen**. This also prevents appending quit to uncertain
JSON framing. A new host guard failure is checked before cleanup can send bytes.
The original shared graceful wait/kill/reap remains inside its reserved cleanup
time. No manual external cleanup procedure is supplied.

## Post proof and bounds

Only after up ACK, schedule one proof attempt at up-ACK time+3 seconds, serviced
by an ordinary later owner poll. Require running before capture, then capture
through the same owner and query running again. Persist the frame and bounded
status evidence. Capture failure leaves an explicit `post_proof_unavailable`
receipt; critical/original exceptions still propagate unchanged. If the owner
ends before the proof can be collected, null proof fields remain unproven.
The controller never writes `interaction_proven=true`. The parent must observe
the post-effect pixels and actual state to establish delivery/effect.

The six-capture limit applies to explicit capture requests. Each accepted click
approval attempt can additionally force one fresh capture; a clock/pixel change
refuses with zero down and can require another human approval. Across 32 IDs,
there are at most 32 controller request captures plus one post-up capture. A
normal one-click path adds one validation capture and one post-up capture.
Original periodic frames, 8 MiB/file, 40 MiB retention, and 1 MiB QMP transcript
bounds remain owned by the original classes. No tracing or QEMU source change
was added.
