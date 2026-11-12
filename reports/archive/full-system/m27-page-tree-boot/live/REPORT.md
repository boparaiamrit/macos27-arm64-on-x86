# One bounded Golden27 page-tree boot

The live page-mapping gate **passed**: the complete canonical trace contains **45 nonempty validated `mapping_gpa_span ... src=mapper` records**, across **39 mapping IDs**, with 1-2,560 pages per record. The old `iosurface_page_table_fields_invalid` refusal is absent. **GUI remains unverified:** the retained console PNG is black.

## Run and ownership

- Actual attempt `20261028T113004Z-b9vpceay`, profile `m27-pages`.
- Command start **2026-10-28T11:30:03.1506951Z**, return **2026-10-28T11:44:55.1317692Z** (17:00:03-17:14:55 IST).
- Fresh CheckOnly `20261028T112947Z-_zw4nuvy`: `inputs_validated_no_vm`, exit 0. Exactly **one actual launch**, no retry.
- Configured bound **900 seconds**, hook **600 seconds**; runner elapsed **890.493 seconds**. Terminal status **timeout**, native exit **124**. GDB return 0; QEMU return 0 during runner shutdown. Return codes do not establish a GUI.

Exact actual command:

```powershell
& ./test-output/arm-macos/full-system/local-raw/Launch-LocalRawAttempt.ps1 -QemuProfile m27-pages -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 600
```

The supplied ADMISSION.md, build-result.json, qualification.json and CURRENT-STATUS.md were read. The prior 623 offline tests were not rerun. No source edits, speculative fixes, additional debugger, live observer, extra QMP connection, guest input, service restart, unrelated cleanup, guest reset or retry occurred. Writes were limited to this new live evidence directory and the launcher's runner-owned attempt outputs/current-attempt metadata. `ACTIVE-STATE.json` is unchanged.

## Canonical trace integrity and page plans

The **entire** new `reims-vgpu-fail.log.gz` was decompressed through EOF, validating its gzip CRC/footer. Decoded length **6,350,924 bytes**, SHA-256 `6759c2793785d6b520d1aa15f490f312c056584ad43dcac57d01ccd9128dfa2d`, compressed length **368,575 bytes** all match `reims-capture.json`. Capture is closed, gzip-finished, error-free and non-exhausted, with **zero unretained bytes**. The old full trace also passes EOF/length/SHA validation: **12,912,833 bytes**, SHA-256 `d6274064ed7ff8b4965549a9a163d799cb6f41d8ac8b989f1bf89d15a2f7d339`. Analyses use canonical traces, not preview tails.

First successful mapper span, canonical line **1500**:

```text
OFF mapping_gpa_span mid=1 gen=2 pages=29 src=mapper prev_pages=0 changed=1 lo=0x14e5c0000 hi=0x14ebb4000 pn_lo=0x53970 pn_hi=0x53aec t=157362
```

All 45 records have `src=mapper`, positive page counts and increasing GPA bounds within admitted 8 GiB RAM. These records are emitted at validated page-plan adoption. There are 30 descriptor-1 physical-route summary lines whose delta values total **46**; those deltas are separate from the 45 deduplicated footprint records. No `iosurface_descriptor2_unqualified`, `mem_no_cpu`, or old page-table-field refusal occurs in the new trace. That absence is limited to this workload.

| Complete-trace observation | Prior m27 | New m27-pages |
|---|---:|---:|
| Nonempty validated mapper GPA-span records | 0 | 45 |
| `iosurface_page_table_fields_invalid` | 128 | 0 |
| `rt_wrong_type`, all types | 182 | 95 |
| type 9 | 137 | 82 |
| type 8 | 28 | 7 |
| type 12 | 17 | 6 |
| `qemu_map_pages_alias_failed` | 0 | 21 |
| compute `desc_decode` | 844 | 4 |
| `m2v_fragment_translate` | 7 | 10 |

The prior attempt had a different duration and mutable guest state. Counts are observations, not causal speed benchmarks or general compatibility proof. [Chart](TRACE-COMPARISON.html), [new full-trace analysis](new-trace-analysis.json), [old full-trace analysis](old-trace-analysis.json).

## First surviving blockers

1. **Type-9 render attachment refusal**, canonical line **1528**, after the first successful page plan:

   ```text
   rt_resolve reason=rt_wrong_type base=11 object_type=9 task=1 ref=11 t=157554
   ```

   The supplied prior exact guest recovery identifies type 9 as **memoryless texture**; mapper-ref texture remains tag 11. This run did not repeat that reverse engineering. No retagging or fabricated pages are justified. New trace totals: 82 type-9, seven type-8, six type-12 refusals.

2. **Host page-alias rejection**, first at canonical line **1866**, 21 total:

   ```text
   qemu_host_adapter reason=qemu_map_pages_alias_failed rc=-1 stage=alias errno=0 first_gpa=0x16233c000 page_count=1013 page_size=16384 page_index=0 t=183228
   ```

   This is a concrete downstream host rejection after a nonempty plan. `rc=-1`, `stage=alias`, `errno=0` do not establish the underlying cause. No CPU-context guard was bypassed.

3. Other compatibility failures survive: AIR/fragment translation (10), compute descriptor decode (4), compute pipeline load (2), used binding absent from layout (8) with compute engine failure (8), format incompatibility (3), compute-view format (6). Exact first examples and counts are retained in the new analysis. No single refusal is asserted to be the sole cause of the black console.

## Boot checkpoints

| Checkpoint | Evidence | Limit |
|---|---|---|
| Handoff | Admitted `0xe0a00000` handoff verified; GDB return 0 | Handoff is not desktop proof |
| Kernel | Darwin Kernel Version 27.0.0, serial line 84 | Kernel execution verified |
| Root | `disk3s1` BSD root line 407, root hash validated 427, Macintosh HD mount complete 436 | macOS Base System `disk5s1` is subsequently mounted at 536 |
| Userspace | BaseSystem launchd starts at 653; Data `disk3s5` mount complete at `/System/Volumes/Data` at 1617; loginwindow PID 163 messages at 2230/2232 | BaseSystem userspace/Data mount observed; installed graphical session not established |
| GUI | Three captures, one retained 1920x1080 PNG and two identical duplicates | Retained PNG inspected visually with `view_image`: entirely black; no login/desktop or interaction verified |

Frame SHA-256 `c1161e09bb43363d2777bdb410b3e59e98b33eae3b374322b5e86079ab089a12`. RGB extrema are zero in all channels; those statistics corroborate the visual inspection and are not themselves desktop proof. [Actual PNG](../../attempts/20261028T113004Z-b9vpceay/frames/frame-0001.png), [frame analysis](frame-analysis.json), [checkpoint evidence](checkpoint-evidence.json), [root/userspace detail](root-userspace-evidence.json).

## Preservation and cleanup

- Before launch: no active CONTROL user, current pointer referenced a completed CheckOnly, CONTROL lock free. After return: owned guest container absent, no active CONTROL user, CONTROL lock free. No manual stop.
- Exporter `b8472de170f6ab1709e76bef8ca08f48df591ee4ea893f607eae2fddb21ce372` remains running with unchanged PID/start time. Sampler PID **74040**, start **2026-10-28T06:54:20.595121Z**, is unchanged. Old remote source/cache proxy were not started.
- **42 existing local protected files unchanged**; one additional optional path was absent at both snapshots. **50 existing volume files unchanged**; one old-tree-only source was absent at both snapshots. Only working AUX/overlay changed. All seven reviewed local and copied Rust sources match admission. Launcher, profiles/wrapper, full runner, handoff sources, manifest/config/AUX originals, converter checkpoint, firmware and CONTROL identity are unchanged. See [protected diff](protected-diff.json) and pre/post snapshots.
- New QEMU SHA-256 `b4b7e761567f4dcdf28dc88c15aa7446426884b3c13ee7b6e1deac6ebfddf0f5` and original QEMU SHA-256 `b4af10846ed7cb121cfc61ecf4bdf59e48df28232b40789c41423945f9816578` were verified before/after. Pinned runtime image: `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`.
- MAIN/local-RAW was never mounted by the guest. Read-only evidence helpers examined checkpoint/boot metadata and RAW stat identity only. No full 35 GB RAW rehash. Complete converter checkpoint still proves all 67 layers verified and a **50,000,000,000-byte** RAW; device/inode/size unchanged.
- Runner fields `all_disk_layers_verified=false`, `local_full_disk=false` and streamed-source wording are legacy transport metadata. The separate converter checkpoint/readiness independently establish the completed local RAW. The report does not promote streamed metadata into conversion proof.

Working CONTROL files were preserved in their natural post-boot state:

| Working file | Before SHA-256 | After SHA-256 | After allocated bytes |
|---|---|---|---:|
| AUX | `b4c1b7e9bf845f0568d6538431f4d81e11a691882bc4903272d5ed6bd4675f6f` | `008ad01b1bb7fd6cd8cd50241760cd110211554376d519f582f2e2c3866c2ea6` | 33,566,720 |
| overlay | `23f9f4f4e3d1f2e2c5afebd9a4a0dc2df4881ed1ad8ddd442811480c26a46d32` | `009b25c3d5b1c84336d592794f2566b21ce4a8acf21dec085da3fe6d5a244bec` | 1,007,386,624 |

## Resource evidence and limits

- Saved free-space samples: before **12,994,764,800 bytes**, launch **12,912,799,744**, post **12,450,029,568** (post age **0.278s**); direct post C: free **12,449,660,928 bytes**. Saved samples satisfy the unconditional 10 GiB floor, age <=20s, future <=2s. Runner ended by timeout, not terminal resource-guard failure. No continuous minimum or peak resource history was retained.
- No OOM marker in retained serial/stderr; no Windows Resource-Exhaustion-Detector ID 2004 event in the queried interval. **Docker event history does not cover the run:** 252 retained container events begin after command completion, and no owned-container event survived. Removed-container cgroup OOM/peak counters are unavailable; the event query cannot definitively prove OOM absence. [Event coverage](owned-container-events.json), [Windows query](windows-resource-events.json).
- Configured 900-second bound and actual runner elapsed 890.493 seconds are reported verbatim; no timeout/CPU/memory/GPU/environment/guest arguments were changed.
- Reporting-only PowerShell display/date-format and Windows encoding errors were corrected; neither launcher command was repeated. ECID and private boot arguments are excluded from the new reports.

Machine-readable result: [handoff.json](handoff.json). No retry or further guest work was performed.
