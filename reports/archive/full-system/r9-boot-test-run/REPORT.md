# R9 single bounded boot

**Terminal result: timeout, exit 124, elapsed 890.453 seconds under the 900-second launcher bound.** Actual attempt [20261029T122831Z-1nnef1lw](../attempts/20261029T122831Z-1nnef1lw/result.json). QEMU and GDB returned 0 during runner cleanup; this is not boot/GUI success. No retry, build, delegation, guest input, second debugger or QMP client occurred. The owned attempt container is gone.

All four prepared new/edited source SHA256 records matched before execution. All 13 pinned Linux synthetic tests passed again. The exact native QEMU pin was verified: 70,858,344 bytes, SHA256 14f12ffe37304d011c00c490539dd949138c552bac3788fb4d8c3dd7a7301b6b. Library pin and readiness pin also matched. Existing preparation evidence was preserved.

The corrected guards passed: no competing macOS attempt container, no container holding the guest volume, no host aarch64 QEMU, boot flock available, exporter running PID679, sampler84568 alive with a fresh sample, live C: free space above 10 GiB. Android PID79064, Android SDK emulator AVD twofold_pixel: **allowed, untouched**, before and after. Its start time remains 2026-10-28 13:45:59 local. Sampler start time remains 2026-10-29 11:05:08 local. Exporter ID/start/PID unchanged. Final sample is 40,638,373,888 free bytes, approximately 1.59 seconds old at inspection.

Migration ran once, backed up the exact old identity bytes, preserved AUX/overlay through migration, atomically replaced/read back identity. Final comparison against backup confirms **only qemu_sha256 changed**, from 553102765a9da19efee87112f85190835d7d0bc3ca0e55539c375f948e302bfe to the R9 SHA. Backup SHA is the original admitted identity SHA. CheckOnly ran once and passed: [20261029T122827Z-utuisp2q](../attempts/20261029T122827Z-utuisp2q/result.json), inputs_validated_no_vm, exit0, 2.043 seconds, no VM. Actual launcher ran once with the same exact arguments minus CheckOnly. Its timeout raised the launcher's terminal exception, so the script's trailing actual-exit/Stop-Transcript statements were not reached; this does not indicate a retry.

## Viewed frames and limitations

I viewed **every retained R9 PNG at original resolution**: only [frame-0001.png](../attempts/20261029T122831Z-1nnef1lw/frames/frame-0001.png), 1920x1080, 6,121 bytes, SHA256 c1161e09bb43363d2777bdb410b3e59e98b33eae3b374322b5e86079ab089a12. It is entirely black. No Dock, Apple logo, window, menu bar, wallpaper, login UI or readable text is visible. No desktop, login or interaction is established.

I also personally viewed the requested reference [013011 frame2](../attempts/20261029T013011Z-bv_zid_f/frames/frame-0002.png): Dock with real Safari icon and many placeholder icons, Downloads and dark Trash, partial window border/two title-bar circles and readable Quit, black contents/background, no menu bar/wallpaper. I viewed all three later [020702 frames](../attempts/20261029T020702Z-kse8w8uk/frames/): frame1 black; frame2 Apple logo/progress bar; frame3 partial Dock with Safari/placeholders/Downloads, bright colored blocks at left and red Trash shape, otherwise black, no window or Quit. R9's retained pixels show less UI than either reference's later images. This is a retained-capture comparison, not proof the guest never rendered other pixels.

Important capture limit: result.json records qmp_status_polling_suspended=true. The QMP transcript ends with query-status ID68 sent without a retained matching reply; ID67 had replied running. Only one successful automatic capture was retained. No fresh end-of-run frame exists. Do not infer a final guest GUI state from the early black capture or stale last_qmp_status. Mouse state captures=0, click_consumed=false, press_framing=not_started; QMP has zero input-send-event, send-key or human-monitor-command mentions. No input request was created.

## Serial checkpoints

Line numbers refer to [serial.log](../attempts/20261029T122831Z-1nnef1lw/serial.log).

- Kernel: line84 Darwin27.0.0.
- Installed System: line405 BSD root disk3s1; line424 validated on-disk root hash; line431 Macintosh HD mount-complete.
- Installed Data: line1615 disk3s5 Data mount-complete; line1643 init-with-data-volume.
- Early userspace: lines1869-1870 Early boot complete, continuing system boot.
- WindowServer: line1902 names WindowServer[158] in a DYLD shared-region unnest warning. This is process evidence, not composited desktop evidence.
- loginwindow: lines2191 and2193 AppleVPKeyStore unexpected session uid -1 requested by loginwindow(161). This does not establish login completion.
- No kernel-panic or watchdog match in serial. No I/O error/Input-output-error/extentref-fetch failure signature found. Lines400,402,420 contain nx_get_volume_group failed error2; these precede the successful installed System/Data mounts. AppleVPKeyStore and MACF/AMFI warnings are present; no causal attribution is made.

## Reims log comparison

Canonical gzip logs were read through EOF and their decompressed byte counts/SHA256 verified against each result.json. R9 retains 8,685,034 raw bytes, SHA256 faff3870fb0dab58d01364df2e41ffc2f35347099031141baa7e81e6ab710257; gzip finished, no consumed bytes lost, no cap reached.

These are **sums of explicit draws_ok/draws_fail fields on retained exec_indirect2 records**, not an inferred total for every successful draw in the VM. The failure log can omit success-only batches. They are observational comparisons, not causal or performance proof.

| Attempt | logged draws_ok sum | logged draws_fail sum | counter records |
|---|---:|---:|---:|
| 20261029T122831Z-1nnef1lw | 359 | 1628 | 1628 |
| 20261029T020702Z-kse8w8uk | 67 | 93 | 93 |
| 20261029T013011Z-bv_zid_f | 445 | 194 | 194 |

R9 explicit linux_m2v_draw reason records: draw_prepare_fragment_translate6, draw_prepare_texture_resolve_missing5, draw_prepare_texture_access_unsupported1. draw_encode_fail reason=draw_vk_nothing_stored appears12 times. Later RGBA16 mouse: color_input_mrt_unsupported4, fragment_translate3, texture_resolve_missing3; nothing_stored10. Earlier 013011: color_input_mrt_unsupported7, fragment_translate4, texture_resolve_missing4. These detailed refusal messages are sparse, not an exhaustive one-to-one account of failed draws.

R9's most frequent literal reason tokens (all record types, including summaries/diagnostics) are fragment_func_zero1339, frag_declared_descriptor_unbound472, frag_neutral_texture_substituted402, draws_skipped_after_engine_refusal318, heap_query_no_metal_device244, rt_memoryless_load_action161, rt_wrong_type126, target_unresolved108. They must not be added to the draw-failure count. The absence of the old MRT refusal in R9 does not establish correct rendering or fence causality. Full counts and exact extraction are in analysis.json/analyze.py.

## Guest hashes after boot

AUX and overlay were unchanged by migration, but **changed during the actual writable boot**. No rollback or repair was attempted.

| File | Before | After |
|---|---|---|
| aux.work.img | af5fd8b3bc11d5a5f8fc7db1ea9e3342891b1c3af3f5d31300481e7e5a10587b (33562780 bytes) | 22e5f9b4ddd2b375dc55350162eef9bf043fb01b22aac2ca685808a50bd52087 (33562780 bytes) |
| root.overlay.qcow2 | 94934224acecba747335f03f3468767fa869cd230b0ea28cdae3e482e1146ca6 (703528960 bytes) | 9c81f3d772d01839f105fb0636ce03af34c6bc454dbe1b8a40bc5a7847426ba4 (710279168 bytes) |
| runner-identity.json | 1a69aaaf1876996d68f7a2298c56bb02c1047b9ae4af2eb8c8e0418858040dae (1422 bytes) | 5d3a99a5999b520798f661d370dcbed0a7b0b0a5f64d7c73d742b3470a5b5518 (1422 bytes) |

Identity's only semantic field change is qemu_sha256, verified against its exact backup after boot. Exporter, sampler and Android process remain running with identical identities/start times; Android allowed, untouched. Ready/artifact pins remain unchanged. Only owned short read-only inspection containers were removed via --rm; the bounded runner cleaned its own attempt.

Evidence: [commands](COMMANDS.md), [execution script](run-once.ps1), [transcript](commands-transcript.txt), [source hash check](source-hash-verification.json), [tests](synthetic-tests.txt), [pre](pre-state.json), [migration](migration.txt), [CheckOnly](check-only.txt), [launch](actual-launch.txt), [post](post-state.json), [identity readback](identity-readback.json), [analysis](analysis.json), [retained frame](../attempts/20261029T122831Z-1nnef1lw/frames/frame-0001.png), [result](../attempts/20261029T122831Z-1nnef1lw/result.json).
