The single Mesa 26 attempt reproduced the LLVM fragment abort. It did not establish a fix or a graphical desktop.

Fresh CheckOnly `20261028T171529Z-6vku77ab` passed in 1.665 seconds without starting a VM. Actual attempt `20261028T171541Z-g9_ahzet`, container `macos-golden-full-20261028T171540`, started at `2026-10-28T17:15:40.5959731Z`. The runner finished after **192.761 seconds** with status `qemu_exited_after_handoff`, exit code **3**, QEMU return code **-6 (SIGABRT)** and GDB return code **0**. The PowerShell launcher threw on runner exit 3 and returned 1. The saved result was written at `17:18:54.260610Z`. No retry ran.

The exact authorized command ran once with `-CheckOnly`, then once without it:

```powershell
& ./test-output/arm-macos/full-system/local-raw/Launch-LocalRawAttempt.ps1 -QemuProfile m27-pages-mem-safe -TransferCopies -LavapipeVectorBits 128 -SoftwareRuntime mesa26 -ReadyName stream-ready-local-raw-cleanup-live5.json -Smp 8 -TbMB 1024 -ContainerCpus 12 -MemoryGB 12 -LavapipeThreads 2 -Timeout 900 -HookTimeout 800
```

The selected candidate manifest was `5711c1e0cc73a67cd8643f1d84591651a75f0de2ad27315f0c7709035ba63a0e`. Its six component pins were checked by the launcher. The guest runtime image remained `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`. The actual VM log reports **Mesa 26.2.5 - kisak-mesa PPA (LLVM 21.1.8)** and **llvmpipe (LLVM 21.1.8, 128 bits)**. It records `robust_buffer_access=true`, `float16=true`, `compute_scatter=off` and `compute_gather=off` (canonical raw lines 1610â€“1619). The candidate driver and LLVM hashes match admission, respectively `9a805a2e19312658ed9715d6bc2892770d7d160d0222b74f0b69aa72d07d3007` and `f804d4247625bf0905c55655377618783ff3296a9c8aacdda9ac7cafa2e5e404`.

Saved stderr contains:

```text
LLVM ERROR: Cannot select: [process address omitted]: f32 = bitcast Constant:i16<15360>
In function: fs_variant_partial
```

This is the same failure signature supplied for the previous stock-runtime guest run. The synthetic FP16 probe passes both stacks and did not reproduce this failure. Version numbers, timing differences and mutable guest state do not establish an upstream fix, root cause or performance change. No additional debugger or shader capture was used.

Verified checkpoints are separate:

- **Handoff:** the existing GDB hook verified the Golden handoff at `0xe0a00000` and its readback.
- **Kernel:** serial line 84 records Darwin Kernel Version 27.0.0.
- **System:** serial line 449 records the read-only system volume mounted as root.
- **Data:** serial line 1634 records `mount-complete volume Data`.
- **Userspace:** launchd execution is recorded, followed by a `loginwindow[164]` process marker at serial line 1931.
- **GUI:** unverified. The sole retained 1920Ã—1080 PNG was viewed and is black. Its metadata/hash match: 6,121 bytes, SHA-256 `c1161e09bb43363d2777bdb410b3e59e98b33eae3b374322b5e86079ab089a12`, captured `2026-10-28T17:17:44.687521Z`, approximately 124 seconds after the attempt prefix. **All retained frames predate drawing**; the first target/draw evidence appears around QEMU log `t=165123`â€“`165892` ms. There is no retained post-draw frame.
- **Interaction:** unverified; no guest input was sent.

The first concrete engine draw refusal remains `draw_prepare_color_input_mrt_unsupported`, destination index **1**, pipeline **22**, geometry **1920Ã—60**, at `t=170031` ms (raw line 1722). The next line records draws skipped and a transparent-black clear/store fallback. This capability refusal is separate from the later native LLVM abort. The earlier anonymous-RAM alias failures and fragmented byte/copy fallback are not automatically blockers.

Saved mapping evidence records mapping 1/generation 2 with 29 pages, mapping 3/generation 2 with 64 pages, and mapping 2/generation 2 with 1,013 pages. The final context contains pipeline 40, target mapping 2 at 1920Ã—1080, and sampled reference 42/mapping 3 at 512Ã—512 using `route=bytes`. The complete mapper plan kind is not explicitly logged; these spans do not prove every plan or identify the faulting module/shader. PostPark is not guaranteed submission or completion. Ephemeral creation breadcrumbs are not retained and cannot identify the failing call.

`memoryless_pass_targets_retired=1` appears in two interval reports, at `t=166007` and `170053` ms (raw lines 1644 and 1739). No explicit memoryless retention/completion error is present. This is limited retirement evidence, not completion of the final pass or a composited desktop. No explicit `present_kind` is logged; clear/store fallback and scanout-paint counters are present. Neither is visual evidence of a login screen.

The canonical gzip was read through EOF with CRC validation. Its decompressed length **1,058,717 bytes**, compressed length **48,285 bytes**, and raw SHA-256 **`d62dd3891dfec760fb995d31c3ff8d6c6de0afe17022a13a3f95b457ddac2011`** match capture metadata. All consumed bytes were retained. No capture error, exhausted budget, diagnostic stream cap, truncated tail or retention error was reported. Capture bounds remained 64 MiB raw and 8 MiB retained storage. FrameQMP alone owned captures, first at 120 seconds and then every 300 seconds; the attempt ended before the next scheduled capture.

Pre/post snapshots verify all **15 reviewed Rust source pins**, the QEMU binary `f603fd8b6066b96a38bfbb20ad74c9c322643c0b120f8662ed079be99ddd648a`, static archive `16743f65688ea0a3ade428e0fc168819dddc25dcd3deb7a8a07f6f0dc91855dc`, firmware, handoff/input pins, launcher/wrapper/profiles and both software runtime directories unchanged. The stock runtime has no `runtime-pins.json`; its provenance file and component files were hashed. The candidate manifest and all six pinned components were hashed, along with its other existing files. The 38 local-file hashes and stable volume-file hashes are retained in the paired snapshots. Read-only hash helpers ran only before/after the VM, with no QEMU/GDB client.

Natural CONTROL changes were preserved:

- AUX: `e64e47ce05b6def55557796312743702124301a2f39c37fd5ad8cc87d19e8c2e` â†’ `1449d71414e79058f9d55c2c031f8d1022d0edb64e15117de6ab76096d815661`; size remains 33,562,780 bytes.
- Overlay: `65e7ec07d1fcb8be9df109418d3a9789c22dcbd73621a24407a6eee5d7e39cc3` â†’ `8eb60261093503978c698e4253c156a3b4c859f23fd68fa0dc75937c71694f67`; size 1,026,949,120 â†’ 1,027,080,192 bytes.

The launcher retained 8 vCPUs, 1,024 MiB TCG TB, 8 GiB guest RAM, 12 container CPUs, 12 GiB memory/equal swap, 2 Lavapipe threads, PID limit 256, read-only root, no container network and 16 MiB tmpfs. The unchanged wrapper sets/readbacks process-local `coredump_filter=0x10` before execution; the launcher retained core ulimit 0. No global core policy changed. No new file appeared in the Windows WSL crash directory after this attempt's start as of the bounded post-run inspection; no core was deleted or debugged.

The runner owned shutdown. QEMU and GDB have terminal return codes; the attempt container is absent and no CONTROL container user remains. Exporter ID `b8472de170f6ab1709e76bef8ca08f48df591ee4ea893f607eae2fddb21ce372`, PID **1187**, start **2026-10-28T12:19:53.487560899Z**, and sampler PID **74040**, start **2026-10-28T06:54:20.5951215Z**, are unchanged. The post-run host sample at `2026-10-28T17:20:11.093Z` reports **14,652,817,408 free bytes**, age **0.738 seconds** at collection; the direct reading was 14,651,899,904 bytes. Both exceed the 10 GiB floor. Freshness bounds remained age â‰¤20 seconds and future â‰¤2 seconds; no bypass or restart occurred. These snapshots are not a recorded minimum for the entire run.

The separate readiness record still establishes all 67 converter layers verified, 50,000,000,000 logical RAW bytes and checkpoint SHA-256 `82066b4eeda14ff1edb191564b4eaf2806f4bfc042e904a95e56ead9dd06c05d`. The runner's generic streamed-mode `all_disk_layers_verified=false` field does not attest this separate local-RAW readiness. No whole-RAW rehash was performed. MAIN stayed read-only in the exporter and was absent from the VM container; the guest used the stable NBD URI and existing CONTROL overlay.

Machine-readable handoff: [handoff.json](handoff.json). Compact saved-log excerpts: [evidence-excerpts.txt](evidence-excerpts.txt), [saved-evidence-analysis.json](saved-evidence-analysis.json). Preservation and cleanup: [hash-comparison.json](hash-comparison.json), [post-topology.json](post-topology.json), [core-metadata.json](core-metadata.json). Native evidence: [result.json](../../../attempts/20261028T171541Z-g9_ahzet/result.json), [stderr.log](../../../attempts/20261028T171541Z-g9_ahzet/stderr.log), [canonical gzip](../../../attempts/20261028T171541Z-g9_ahzet/reims-vgpu-fail.log.gz), [retained frame](../../../attempts/20261028T171541Z-g9_ahzet/frames/frame-0001.png).

Final bounded check `2026-10-28T17:24:26.3376772+00:00` again confirmed no owned container or CONTROL user, unchanged exporter/sampler identities, and a fresh host sample of **14,570,635,264 free bytes** (age **0.021 seconds**). See [final-check.json](final-check.json).
