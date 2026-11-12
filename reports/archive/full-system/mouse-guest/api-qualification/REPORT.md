# Synthetic mouse QMP API qualification

Two distinct generic AArch64 fixtures qualified the frozen controller's QMP transport and original owned cleanup. This is not macOS input, HID report, button, KSA identity, desktop or compositor proof. No human approval was claimed or supplied.

| Fixture | Result | Actual QEMU runtime | Memory peak | One click |
|---|---|---:|---:|---|
| positive | separate down/up ACKs, post-capture, running and counter progress | 4.468190s | 152821760 bytes | IDs 8 and 9 |
| release uncertainty | actual up ACK read; controller credit suppressed; original owned cleanup | 1.072790s | 152629248 bytes | IDs 8 and 9 |

Both QMP sessions confirmed `QEMU HID Tablet`, `absolute=true`, `current=true` before input. Each used the actual unchanged core QMP loaded from `run-full-attempt.py`, unchanged `frame_qmp` factory, and frozen `mouse_qmp` class over its sole owned AF_UNIX socket. The fixture-only counter HMP read used the same socket, sequence, recorder, receiver and integer-ID matcher. No extra client, monitor port, GDB, reconnect or input retry occurred.

For transport qualification only, the harness explicitly saved SYNTHETIC `click_consumed=true`, `release_owed=true` and a bounded release deadline before actual `Controller.dispatch`. It supplied pixel center `(320,240)` in a 640x480 generic surface, yielding native absolute `(16409,16418)`. It did not call the human approval request path or attest that the default surface contained a Quit button. The result field named `approved_frame` comes from the frozen dispatch return and is synthetic fixture data, not approval evidence.

The positive wire order is down send → down positive ACK → up send → up positive ACK, with IDs 8 and 9. There is no union containing both states or delay event. Counter advanced from 360477853 to 6177113204 (+5816635351); the same client observed `running` before, during the scheduled post-up capture and afterward. The post capture was performed at index 2; the unchanged duplicate-frame retention kept the original PNG path with a fresh capture receipt. Both PNG receipts validate CRCs, dimensions, IEND and deflate. The interaction event window contains no STOP/RESET/SHUTDOWN/panic event; normal positive cleanup SHUTDOWN lies outside that window.

The negative wrapper called the unchanged receive chain first. Core JSON parsing and its actual wire recorder read the full positive up ACK before the harness raised a SYNTHETIC credit-uncertainty exception. Actual `MouseCleanupRequired` is outside core `GuardError`. The next lifecycle operation was unchanged `stop_children(None, owned_Popen, qmp)` (0.000008133s after catching the fatal error). `release_owed=true` refused cleanup `quit` before recording or sending bytes; original cleanup called the exact Popen's actual `terminate` and reaped it in 0.007436992s. The final wire line is the actual up ACK. No RPC or input followed the fatal condition. Durable final state retains quarantine and release owed, reflecting controller uncertainty even though real QEMU acknowledged release.

## Resources and pins

Image: `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`. QEMU: `/work/orchard-m27-pages-rgb10/artifacts/qemu-system-aarch64`, SHA256 `87614fc2db5efc0f7293aad13d1f70ffd43d4e3e09380dfd5522ffd419d7202b`; actual `--version` reports 11.1.50. Six frozen source files hash identically before, inside both fixtures, after and at final verification; exact values are in `source-sha256-final.json`.

Each exact uniquely named container had 2 CPU, 1 GiB memory and equal memory-swap total (cgroup swap 0), pids 128, network none, root read-only, tmpfs 64 MiB, cap drop ALL, no-new-privileges, core ulimit 0 and 2 MiB file/log limit. Process-local coredump_filter 0x10 was read back in Python and inherited/read back in QEMU. Actual cgroup limits, peak and OOM counters are preserved; OOM and OOM kill stayed zero. Only macos-orchard-build mounted as a read-only volume; ARM code/atomic host sample mounted read-only; owned output mounted writable. No guest/GPU/CONTROL/RAW/state volume was mounted. The authored 24-byte loop and its hash exactly reuse existing `qmp-frame-qualification/qualify.py`; generic virt/cortex-a72, single-threaded TCG, smp1, 256 MiB guest RAM, ramfb, qemu-xhci and usb-tablet. PC 0x40200000; counter 0x40201000.

CONTROL volume-unused metadata was empty before each fixture. Existing parent host-space samples stayed fresh within [-2,20]s and above 10 GiB; actual C: free was independently measured. Positive host guard max gap 0.042846s; negative 0.047805s. Minimum actual host free across both was 14040317952 bytes. Both exact containers are confirmed absent. Total elapsed from first container launch to second completion was approximately 125s, below 300s.

## Preserved host harness failure

The positive VM itself completed and reaped in 4.468190s. The first Windows launcher waited for full Docker inspect output on an undrained stdout PIPE. That metadata JSON filled the pipe. Its host-space watcher continued until the 110s owner bound, removed only the already-exited owned container, then raised `subprocess.TimeoutExpired` waiting one second for the blocked inspect helper before it could publish the final host receipt. Thus positive `host.json` remains the initial incomplete receipt; it is not represented as a fully successful host launcher run. Exact positive cleanup duration was not published; archived limits and the subsequent inspect-wait error establish removal returned within the 110+7+1s path. Recovered exact-container metadata proves exit 0, no OOM and actual settings.

`launch-v1-inspect-pipe.py`, the original guard log, `host-harness-failure.json`, and recovered `container-inspect-metadata.json` preserve the failure. Only the owned launcher changed to stream selected inspect metadata to an owned file. The positive VM/click was not repeated. Only the second, previously unused release-uncertainty fixture then ran; its host launcher completed in 1.828089s and removed its exact container. No frozen source changed.

## Evidence and limits

- `handoff.json`: machine-readable result and scoped unknowns.
- `runs/macos-mouse-api-positive-c129eb0a85/result.json` and `attempt/qmp.jsonl`: positive counters, frames, state, wire.
- `runs/macos-mouse-api-release-uncertain-ba333c2796/result.json` and `attempt/qmp.jsonl`: actual release ACK, fatal cleanup trace and no post-fatal RPC.
- Each run's `artifact-verification.json`: independent artifact-order, guard, resource and absence checks.
- `source-sha256-final.json` and `artifact-manifest.json`: frozen source and owned evidence hashes.

Before CONTROL was clarified to mean the guest volume, host listener/process-name metadata was read while resolving that term. No connection, command line/state read, signal or action on those processes occurred. All writes remained in this owned directory.

Actual guest HID reports/USB consumption, macOS interaction, a visible Quit button, KSA identity and desktop responsiveness remain UNKNOWN. Parent CPU tests cover approval policy and initial GDB STOP behavior; these synthetic no-GDB fixtures do not add live proof for those paths. No live instruction is issued by this handoff.
