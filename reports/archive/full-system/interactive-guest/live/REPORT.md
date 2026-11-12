# One retained fresh-01 interactive Golden attempt

The authorized bounded scope is complete. One real VM ran, and the sole FrameQMP owner sent exactly one Cmd+Q after I viewed the current retained PNG with `view_image` and confirmed the front white Keyboard Setup Assistant window. QMP acknowledged it. **A visible interaction effect is unproven:** the immediate post-action PNG was byte-identical, and the later natural frame still showed Keyboard Setup Assistant. No login, credential entry, complete Setup Assistant flow, or usable full desktop was established. No further experiment or input was performed.

## Admission, commands, binding, and termination

Parent admission SHA256: `cfa39cfa15121468d0cec8edbfb03ee8f50e527385e373afbbe82a4c9e30d56d`. Its eleven protected host files matched before and after, as did the final parent-review source pins. The old child manifest is historical; the final controller/review pins governed this run. No tests or synthetic fixtures were rerun.

The fresh CheckOnly command was:

```powershell
& ./test-output/arm-macos/full-system/interactive-guest/Launch-InteractiveAttempt.ps1 -CheckOnly -QemuProfile m27-pages-io -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup4-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

CheckOnly `20261028T221331Z-v0qsazs5`, container `macos-golden-interactive-01-20261028T221331`, returned `inputs_validated_no_vm`, exit 0, elapsed 1.284 seconds. It created no input session and started no VM. The cleanup4 readiness record was used explicitly.

After recording the complete existing attempt-directory set, the actual command ran once, differing only by removal of `-CheckOnly`:

```powershell
& ./test-output/arm-macos/full-system/interactive-guest/Launch-InteractiveAttempt.ps1 -QemuProfile m27-pages-io -CaptureFinalShaders -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup4-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

The set difference contained exactly `20261028T221347Z-spxd9y08`. Its `command.json` selected the admitted m27-pages-io binary and `/guest/fresh-01/boot` AUX/overlay. Its input session matched the exact attempt, nonce, two-operation allowlist, and limits. `current-full-attempt.json` identified launcher `local-raw-interactive-01`, container `macos-golden-interactive-01-20261028T221346`, start `2026-10-28T22:13:46.564560Z`. Whole-CONTROL exclusion was clear before launch. No newest-by-time selection was used. See [binding.json](binding.json) and [launch-admission.json](launch-admission.json).

The unchanged runner owned stopping and cleanup. Canonical result: `timeout`, exit **124**, elapsed **890.232 seconds**, QEMU return **0**, handoff-hook return **0**. Its sole-owner cleanup `quit` was QMP ID 448; matching shutdown occurred `2026-10-28T22:28:37.245457Z`. The PowerShell launcher surfaced canonical exit 124 as an exception and tool exit **1**. No manual stop, extension, VM restart, or retry occurred. The result file closed at `22:28:37.469142Z`; a separate precise end-to-end container-duration receipt was not retained.

## Perception approval and wire proof

All frame paths below are under [the exact actual attempt](../../attempts/20261028T221347Z-spxd9y08). Times are UTC. Frame observations came from actual `view_image` calls, not OCR or historical pictures.

| Capture | Time | Observation / role |
|---|---|---|
| 1, natural | 22:15:49.492 | Viewed black frame; no approval. |
| 2, `capture-01` | 22:18:16.104 | Fresh capture duplicated frame 1; no approval. |
| 3, natural | 22:20:49.980 | Viewed Dock with placeholder icons, recognizable Safari/Downloads, and Quit/Continue buttons; no identifiable front KSA window, so no approval. |
| 4, `capture-02` | 22:22:54.932 | Viewed front white Keyboard Setup Assistant title and explanatory text. Black background, Dock placeholders, and incomplete button rendering remained. This authorized the one request. |
| 5, forced approval capture | 22:23:11.268 | Owner freshly captured the same SHA and retained frame 4. Running statuses bracketed approval. |
| 6, automatic post-action | 22:23:15.386 | Owner retained the same frame 4 SHA. Original-resolution viewing confirmed KSA remained visible. |
| 7, natural | 22:25:50.084 | Viewed KSA still present, with squared white window-edge artifacts and the Dock. No wizard closure or new login view established. |

The approved file was [frames/frame-0004.png](../../attempts/20261028T221347Z-spxd9y08/frames/frame-0004.png), SHA256 `738bf77a7f2168095fff04b98a08f221c7605c945f8a87f9d440666d1bffa101`. It was inspected before submitting:

```powershell
python -B ./test-output/arm-macos/full-system/interactive-guest/request.py --attempt 20261028T221347Z-spxd9y08 quit_keyboard_setup_assistant --id quit-01 --frame-sha256 738bf77a7f2168095fff04b98a08f221c7605c945f8a87f9d440666d1bffa101 --attest-view-image-keyboard-setup-assistant
```

The CLI's `show` operation was used only with that exact attempt. Requested captures were only `capture-01` and `capture-02`, each submitted through the admitted CLI and followed by a matching response before another request. Host snapshots in [host-protocol.jsonl](host-protocol.jsonl) preserve all three request/response pairs, request-file hashes, and nonce-binding verification with nonce text redacted. Final accepted IDs are exactly those three; capture count is 2/6. No `quit-02`, stale-frame retry, refusal, partial-send, lost-ack, or uncertain-delivery case occurred.

The closed [qmp.jsonl](../../attempts/20261028T221347Z-spxd9y08/qmp.jsonl) has one greeting and contiguous owner IDs 1–448: one capabilities command, 438 status queries, seven screendumps, **one send-key**, and one runner cleanup quit. Lines 578–579 contain exactly:

```json
{"execute":"send-key","id":285,"arguments":{"keys":[{"type":"qcode","data":"meta_l"},{"type":"qcode","data":"q"}],"hold-time":100}}
{"return":{},"id":285}
```

Statuses 282 and 284 were running before dispatch; forced screendump 283 matched the approved SHA. Statuses 286/287 and post-capture status 289 were running afterward. The pinned controller persists consumed state before entering the wire method (`controller.py:133–137`); final `action_consumed=true`, `quarantined=false`. The response is correctly `acknowledged_interaction_unproven`, QMP ID 285. Parent-reviewed exact-fork policy queues presses in order and reverse-order releases in virtual time before acknowledgement. This run proves the exact request/acknowledgement, not guest HID processing or execution of each release.

There were three STOP/four RESUME events during the existing initial handoff hook at 22:13:49–53, **none from approval onward**. No RESET or guest-panic event appears. The final SHUTDOWN belongs to the runner's cleanup quit. No second QMP/HMP/GDB client, live serial/kernel observer, arbitrary RPC, mouse, focus operation, other key, or credential entry was used.

The post-action receipt was published about 4.118 seconds after the fresh approval capture through the owner's normal polling timer. It has the approved SHA and running-before/running-after statuses. Later frame 7 differs visually at the window edges but still displays KSA; that rendering change does not prove the key caused an effect. [observations.json](observations.json) and [post-action-state.json](post-action-state.json) retain the observation/receipt details. A transient reduced-detail tool display was inconsistent with the unchanged file; an actual SHA check and original-resolution re-view confirmed the retained KSA image. No conclusion relies on that inconsistent display.

## Independently separated checkpoints

| Stage | Evidence and limit |
|---|---|
| Source storage authority | Pinned cleanup4 readiness independently records the complete 50,000,000,000-byte local RAW, 67 converter-verified layers, checkpoint SHA `82066b4eeda14ff1edb191564b4eaf2806f4bfc042e904a95e56ead9dd06c05d`, device/inode 2096/1146219, six matched samples, and read-only `/stream/golden-live5.nbd`. No full RAW rehash or MAIN mount was performed. Generic runner streamed/local-disk-false/all-layers-false fields do not supersede that separate converter authority. |
| Handoff | Exact attempt `handoff.json`: verified PC `0xe0a00000`, revision/version 3/2, NoSEP contract and write readback; hook return 0. Existing admitted in-memory handoff behavior remained in place. |
| Kernel | Exact `serial.log:84` identifies Darwin 27.0.0 / RELEASE_ARM64_VMAPPLE. |
| Root and Data | `serial.log:404` identifies BSD root disk3s1; line 426 identifies the RO System root; line 1615 explicitly records disk3s5 **mount-complete volume Data**. |
| Userspace | `serial.log:623,880` records launchd; lines 2152/2154 identify loginwindow. These do not establish an actual login. |
| GUI | Actual composited KSA window, readable application text, and a Dock with Safari/Downloads plus placeholders were viewed. Black background and window/button/icon defects remain. |
| Interaction | Exactly one approved chord and positive QMP acknowledgement; no visible wizard closure or other attributable screen effect. Guest HID delivery remains unproven. |
| Full desktop | **Unverified.** Dock visibility alone does not establish a usable Finder/application session, completed setup, login, or working interactions. |

## Bounds, capture integrity, and rendering limits

The pinned launcher retained 12 CPUs, 12 GiB memory/equal total swap, pids 256, network none, read-only root/build, CONTROL RW, eight vCPUs, 1024 MiB TB, Mesa26, vector width 128, two lavapipe threads, and both optional compute-copy paths off. Capture tmpfs was 8 MiB and `/tmp` 16 MiB; core limit 0 and the wrapper's process-local core filter/readback remained enforced. The runner retained the unconditional 10 GiB host floor and sample age [-2,20] seconds, 2 GiB allocated-overlay guard, and 900/800-second bounds. These are configured/enforced bounds, not newly measured cgroup peaks; no live resource-probe client was added. Launch sample was fresh and above floor. Post-run sample reported 15,732,727,808 bytes free. An independent continuous host-space minimum was not retained.

All four retained 1920×1080 RGB8 PNGs passed signature, chunk CRC, IHDR/IEND, deflate, and decoded scanline-length checks. All seven capture records resolve to retained same-SHA files; captures 2/5/6 correctly reuse an existing image. The seven capture requests all received positive screendump replies.

The canonical native artifact is `reims-vgpu-fail.log.gz`: **809,049 compressed bytes**, SHA256 `0c3410b6be43fcbf71d53e41c07412e1f4a0bf449923832268d570025beb635e`; decompression verified gzip CRC/ISIZE, **9,212,983 raw bytes**, SHA256 `db6075e355c6f4b7e496275673da2441f1a0ffb480af693b77f979deb4dd768f`, matching capture metadata/result. All consumed bytes were retained; no cap exhaustion or truncated tails occurred. Compressed storage allocation was 954,368 bytes, within the 8 MiB storage/64 MiB raw bounds.

All **58** extracted files match their index sizes/hashes, including **32** SPIR-V modules. Extraction reports complete and nonempty, but `capture_set_atomic=false` and producer completeness is not interpreted. No new shader semantic census/validator helper was needed or run; these counts do not assert f32-only interfaces. No `LLVM ERROR`/`LLVM abort` text appears in this exact canonical log.

Current native refusal strings include MRT (`draw_prepare_color_input_mrt_unsupported`, 131 matching lines), dual-plane textures (`dual_plane_texture_unexecutable`, 11), and buffer-texture load details (`reason=buftex_load`, five). Counts are literal matching lines, including repeated diagnostic mentions, not distinct failures. The inherited native aggregate-load limitation remains outside scope; that string did not occur in this run. No causal claim links these refusals to the input outcome. The separate RGB10 study patch was not built, edited, or admitted into this binary.

See [artifact-audit.json](artifact-audit.json) for wire lines, exact serial checkpoints, all frame/hash checks, gzip checks, and hashes of the 88 exact CheckOnly/actual artifact files.

## Preservation and cleanup

[preservation-before.json](preservation-before.json) and [preservation-after.json](preservation-after.json) record file sizes, allocated bytes, and hashes from read-only, network-disabled preservation helpers before launch and after VM cleanup. These helpers only hashed the admitted emulator/archive and six pair files; no guest filesystem was mounted/read and no RAW payload was read.

QEMU remains 70,830,832 bytes, SHA256 `8db719ff2982a216e64aa2303c8731bdc0d8a2051919f69bc95bbcbd1dd3829b`; archive remains 174,861,242 bytes, SHA256 `d9bfdcc73209bf4ead5e52469ae66a6cbfe3566430b9f2e0e0c1ad98bec9abaf`. Original `/guest/boot` AUX remains `c95c480ce3a57809f1845b902b8dfece159f66608fb4612ccf913d00c74d4abb`; overlay remains `2ba20d8dc6ae2f548b367f068aab22c0da580ea1e18cdb6fd9d904f4e93ed41b`. Both old and fresh runner identities remain `e9373f3a9cd189c76b2d14219dd433e0dbf699dea616bc9b6c8f529f09f2d066`.

Natural fresh-01 changes were retained without repair/reset/copy/revert:

| File | After SHA256 | Size / allocated bytes |
|---|---|---|
| AUX | `da6f45c139956df6b3d4a9a19325fe8087ecedb0a506e1d1e6da70fe0cafaac7` | 33,562,780 / 33,566,720 |
| Overlay | `8002120f1a24ca2a43f9f87c9b7e3d81afacc20c1b4f92987fe1eb91344e4acd` | 552,730,624 / 552,685,568 |

Exporter ID `b8472de170f6ab1709e76bef8ca08f48df591ee4ea893f607eae2fddb21ce372`, PID 679, start `2026-10-28T21:58:44.477275548Z` is unchanged. Sampler PID 77088/start `2026-10-28T18:26:02.6800687Z` and Android PID 79064/start `2026-10-28T08:15:59.0652064Z` are unchanged. No lease or process was restarted or extended.

Before/after container ID sets are identical: 89 containers, 12 running; 28 volumes remain. The 86 containers outside the three known pre-existing restart loops retained starts/restart counts; those three loops continued independently. All eight database/Redis/mail containers remain healthy. The exact actual and CheckOnly containers and both preservation helpers are absent; whole CONTROL is unused after cleanup. QEMU/hook exits and the removed owning container establish owned child cleanup. No other service/storage cleanup occurred.

[preflight-host.json](preflight-host.json), [postflight-host.json](postflight-host.json), [preserved-host-processes.json](preserved-host-processes.json), and [cleanup-verification.json](cleanup-verification.json) preserve the checks. This is a compact protected-pin/critical-artifact audit, not a whole-workspace hash claim. Only owned live evidence, exact attempt artifacts, and the CLI request slot were written. No source/renderer/backend/identity changes, rebuilds, external communications, stage/commit, or delegation occurred. Raw third-party artifacts remain locally ignored and uncommitted. This report and handoff redact ECID, private boot arguments, and clear nonce values.

The broader independent Golden desktop goal remains incomplete. Parent review owns any subsequent step; this worker stopped after this report and handoff.
