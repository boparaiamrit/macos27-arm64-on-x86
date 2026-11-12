# Indexed ordered framebuffer-fetch implementation: review handoff

**Release build blocked.** The isolated implementation and required actual-engine GPU oracles passed, but an affected existing descriptor-arena test failed. No new release archive or QEMU executable was built or linked. No VM or guest input occurred.

## Build blocker and baseline control

`qualified-descriptor-arena.log` records `arena_grows_on_exhaustion_and_frees_route_correctly` failing at `exhausting a block must report growth`. The native driver served **2048 sets from one pool declaring max_sets1024**, so the arena never received an exhaustion error and reported no growth. Its separate existing unservable-set test printed SKIP because the driver did not enforce its per-type budget condition. The harness reports5 passes/1 failure; one of those5 passes did not exercise its stated condition and is excluded from semantic success claims.

The bounded component A/B in `pool-baseline-control.log` used the **exact original pinned create_block body** for the baseline first pool, and the production input-reservation creator for the other. Both used the same actual allocation/free owner and current admitted device context. Both served2048/1024 sets in one block with no growth. This isolates the failing test assumption from the new input reservation; it is not a full baseline-renderer binary run. Provenance and original function bytes are in `pool-control-provenance.json` / `baseline-pool-creator.rs`. No existing assertion, skip, arena growth policy, resource eviction, or descriptor lifetime was changed to pass this test. It remains a failed qualification gate, requiring parent review before release build work.

## Production change and review files

`production-review.patch` is the production plus owner-regression delta against the exact RGBA16 baseline. `qualification-only.patch` adds authored actual-engine fixtures and the pool component control. `instrumentation-only.patch` separately records temporary native-struct/descriptor logging; that logging was removed for the production-byte GPU runs. Byte-authoritative exports are in `production-source/`, `qualified-source/`, and `instrumented-source/`; manifests identify each.

- `reims-vgpu-core::pass` owns a private bounded8-slot ColorInputs set and typed ordinal, derived from the decoded pass capacity. Runtime parses reflected ColorInput ordinals once and carries the set into DrawRequest. Invalid>=8 ordinals decline rather than truncate.
- An opaque OrderedColorInputs plan admits every nonempty set, including0, against actual DeviceFeatures, physical color capacity, materialized slots and both input-descriptor limits. Missing targets/capacity and unavailable ordered access have stable typed Unsupported reasons. Empty input behavior remains admitted without requiring ordering.
- DeviceFeatures queries the EXT color-order feature only when advertised, couples its extension selection to the queried answer and chains the color-only feature on actual device creation. No depth/stencil enablement, name gate, force environment variable, ARM-alias expansion or duplicate HostGpuCaps field.
- Pass/pipeline/compatibility keys retain the exact set. Sparse input tables preserve InputAttachmentIndex; selected slot1 is table index1 with index0 UNUSED, and slot7 retains all preceding holes. Descriptors bind the actual materialized selected view/layout at192+N. Selected attachments use GENERAL or the existing feedback layout while other attachments retain their established layout. Secondary LOAD initial layout matches its recorded input transition.
- Admitted plans supply the actual legacy subpass color-order flag16 and color-blend-state order flag1. The descriptor arena reserves INPUT_ATTACHMENT capacity through checked bounded multiplication. Per-draw selection respects the real input limits; an empty-input host is not required to enable ROAA.
- Existing contiguous-secondary, geometry, format, identity, alias, LOAD-readiness, memoryless identity, generation/debt and retirement owners remain in place. The exact returned secondary attachment views are carried into descriptor selection. No fake readiness, debt completion, early view free or arbitrary eviction was introduced.

## RED and focused qualification

Baseline default policy:1 behavior RED /1 pass; the descriptor owner emits192 where the desired indexed contract requires193. The documented COLOR_GENERAL=off control exposes the layout defect as well:0 passes/2 behavior failures. No compile/harness error or GPU-unbound descriptor execution was counted as RED. The old descriptor API has no ordinal argument; these owner tests demonstrate its missing indexed contract, not a rerun of the parent's seven runtime refusals.

Initial focused GREEN:6 engine-owner tests and1 semantic-set test. Sets empty,0,1,0+1,sparse1+7,high7, invalid ordinals, missing targets, limited physical/descriptor capacity, unavailable capability, native enable fields, flags, key separation, per-slot layouts and exact descriptor index/view are checked.

The prior105 focused base cases remain passing, with2 new cache cases in the same filter: **107 base/cache invocations**. Additional affected tests are below. Counts are invocations, not a deduplicated test census; the indexed cache cases appear in more than one filter. The existing descriptor-arena failure and conditional not-exercised case remain visible.

| Filter | Harness passes | Failures | Conditional not exercised |
|---|---:|---:|---:|
| qualified-buffer-descriptor | 1 | 0 | 0 |
| qualified-buffer-read-debt | 1 | 0 | 0 |
| qualified-buffer-texture-debt | 1 | 0 | 0 |
| qualified-depth-readiness | 3 | 0 | 0 |
| qualified-descriptor-arena | 5 | 1 | 1 |
| qualified-descriptor-retention | 6 | 0 | 0 |
| qualified-device-features | 22 | 0 | 0 |
| qualified-engine-exec | 58 | 0 | 0 |
| qualified-indexed-owner-narrow | 6 | 0 | 0 |
| qualified-indexed-owner | 6 | 0 | 0 |
| qualified-memoryless-identity | 21 | 0 | 0 |
| qualified-native-format | 16 | 0 | 0 |
| qualified-rgb10-actual-runtime | 4 | 0 | 0 |
| qualified-rgba16-actual-runtime | 7 | 0 | 0 |
| qualified-settle-site | 1 | 0 | 0 |
| qualified-shader-cache | 46 | 0 | 0 |
| qualified-shader-capture | 10 | 0 | 0 |
| qualified-writeback-debt | 20 | 0 | 0 |

Native pool-control comparison:1 pass. Existing GPU parity cases: framebuffer fetch0, secondary resident sampling, RG16Float secondary and unchanged single target all executed and passed without skip. No broad unrelated suite ran.

## Actual-engine GPU evidence

Five required cases executed: attachment1; both0/1 with distinct seeds; sparse high7; overlapping primitives in one draw; and unready secondary LOAD typed refusal. They drive actual execute_draw_request -> pass/layout/descriptors/pipeline -> draw/readback. The authored shader fixtures do not replace the engine with a separate Vulkan composition. Existing AIR lookup fixtures were preserved.

The instrumented run measured actual VkDeviceCreateInfo pNext color/depth/stencil **1/0/0**, EXT selection, actual subpass flag16, blend flag1, input references and descriptors193/199. Its source/binary hashes and native receipts are frozen. Production source with native logging removed then passed the same required cases under default and narrow resting-layout policies, including actual subsequent secondary sampling and a second ready LOAD with known changed pixels.

The overlap case emits two full triangles in **one draw, vertex_count6**, with distinct primitive-dependent transforms. Expected sequential destination update differs from the seed, an unbound-zero read and an unordered last-primitive result. It covers256 inner pixels and144 untouched guard pixels per20x20 readback. UNORM8 quantization is accounted for; every channel, exact readback length, finite expected values, guard band and 3/255 tolerance is checked. Subsequent sampling binds the secondary resident directly with1 GPU bind /0 reuploads.

Total:12800 readback pixel checks across instrumented/default/narrow runs. The two production-policy runs retain **24 raw RGBA8 readbacks =9600 pixels /38400 channels**, with sidecar geometry/expected values, independent Python readback validation and SHA256 entries. Raw files are in `engine-readbacks/`. This is ordered software-engine proof, not a Golden frame or missing-button causal proof.

Only the pinned Mesa26/LLVM21 software runtime was used, with LP128/two threads, no hardware GPU mount. All six runtime files match before/after every GPU phase, and the runtime was mounted read-only at **both /soft and /out/runtime**. No Vulkan validation layer was available/enabled; no clean API-validation claim is made.

## Preservation, compiler and resources

All1261 baseline source entries, all618 pinned compiler files, every baseline Cargo.toml/Cargo.lock,8 current host pins,10 admitted artifacts,89 original container IDs and28 volumes match after the work. The current wrapper c41d... pin was used; the old historical8b3... host snapshot was not falsely required. Source staging excluded .git/target recursively and preserved symlinks. No graph/index/coverage tool was available; installed codebase-memory guidance was used with Verify-tier exact-source fallback, with no coverage claim.

Linux-targeted locked/offline Cargo metadata proves the local vendored metal2vulkan package with no registry source/checksum. All compiler/root manifests and locks remain byte-exact. Compiler and Cargo versions are in their toolchain logs. No dependency download/update, compiler/shim change, QEMU source/object rebuild, release link or live-profile migration occurred.

Allocation premeasure reserved1723174740B within the1800000000B cap and current2425044992B headroom. The existing target was reused. Final measured logical additional allocation before final report generation: 363861737B; source blocks 48242688B; current target blocks 1890496512B. Exact physical target growth is unavailable because original target st_blocks were not recorded. Actual host free samples are retained separately; no causal attribution to unrelated processes is made.

Guarded inner active time 1231.784s; measured outer container active time 1245.507s, both below2400s. Minimum observed host free 12647104512B stayed above10737418240B. Freshness age[-2,20] and target0.2s polling were enforced; actual observed gaps are in receipts and can exceed that target during hashing/scheduling. Each measured command stayed within900s, each GPU phase within300s. Builder admission4CPU/6GiB/equal memory-swap/jobs2/pids256 and GPU admission2CPU/2GiB/equal memory-swap/pids128 were read back, with networknone, read-only root, tmp64MiB, core0 and process filter0x10.

Maximum **measured command** cgroup peak 3167006720B; maximum measured GPU cgroup peak 226099200B. Every retained final command/GPU memory-event receipt has max/OOM/OOM-kill0. Several short staging/read-only/harness-only containers lack a final peak/events receipt because they exited outside the command recorder; their actual Docker admission and cleanup are recorded. Configured limits are not substituted for those missing measurements. All 24 owned-container cleanup receipts show absence; protected sampler77088, exporter b847.../PID679/start and Android79064 identities remain unchanged. No guard/resource/OOM/identity failure was retried.

Initial ordinary development/harness failures are retained: missing pools.rs export path; an overly strict baseline failure-count assertion before the documented narrow-policy run; test-module namespace/count checks; unavailable glslangValidator followed by the existing installed glslc route; and explicit Rust lifetimes in diagnostic-only pointer types. None count as behavior RED/GREEN. Each source change was written with current owned mtimes and rebuilt; fresh build receipts and changed executable hashes distinguish the instrumented and production binaries. No stale result was counted as GREEN.

## Protected admitted artifacts

- `/work/orchard-m27-pages-rgb10/artifacts/qemu-system-aarch64`: 70844192 bytes, SHA256 `87614fc2db5efc0f7293aad13d1f70ffd43d4e3e09380dfd5522ffd419d7202b`.
- `/work/orchard-m27-pages-rgb10/artifacts/libreims_vgpu.a`: 174891956 bytes, SHA256 `fa8581e23cc7a136d7f0067cfa7fd05da65f5e53c201340ae3c4e2b9cfc63242`.
- `/work/orchard-m27-pages-io/artifacts/qemu-system-aarch64`: 70830832 bytes, SHA256 `8db719ff2982a216e64aa2303c8731bdc0d8a2051919f69bc95bbcbd1dd3829b`.
- `/work/orchard-m27-pages-io/artifacts/libreims_vgpu.a`: 174861242 bytes, SHA256 `d9bfdcc73209bf4ead5e52469ae66a6cbfe3566430b9f2e0e0c1ad98bec9abaf`.
- `/work/orchard-m27-pages-capture/artifacts/qemu-system-aarch64`: 70829888 bytes, SHA256 `689d926f89da98fb6886919e54d8983c80b35b0666051634623e875d5e6297de`.
- `/work/orchard-m27-pages-capture/artifacts/libreims_vgpu.a`: 174844746 bytes, SHA256 `cbd1ec25328127d42e45521f5ca0f17d90b8f5ab3df27babf000ff5c9bc4e385`.
- `/work/orchard-m27/qemu/build/qemu-system-aarch64`: 70749088 bytes, SHA256 `b4af10846ed7cb121cfc61ecf4bdf59e48df28232b40789c41423945f9816578`.
- `/work/orchard/qemu/build/hw/display/libreims_vgpu.a`: 174368172 bytes, SHA256 `32720f5ea9a0dfd7d388714e9c2b7818c98e9cf1e761140318ead212cb799a47`.
- `/work/orchard-m27-pages-rgba16/artifacts/libreims_vgpu.a`: 174892356 bytes, SHA256 `4ed34bcbca161a6b0e06df39c6ad13196ed691cbf69c9ce0b583b313ae64da99`.
- `/work/orchard-m27-pages-rgba16/artifacts/qemu-system-aarch64`: 70844192 bytes, SHA256 `553102765a9da19efee87112f85190835d7d0bc3ca0e55539c375f948e302bfe`.

## Parent review limits

The release gate is failed, so there is no new releasable archive/QEMU hash to admit. Pending-fence lifetime and successful guest debt landing are not newly proven by synchronous readback cases. The source fixes the confirmed indexed-input refusal; missing-pixel causality, guest acceptance, usable desktop and interaction remain unverified. No VM/guest input, guest filesystem reads, CONTROL/RAW/state/NBD mounts, deployment, commit, push, delegation, infrastructure cleanup or service/settings change.

The user supplied the upstream11.1 changelog during handoff. The official QEMU homepage verified11.1.3 dated2026-10-28; the wiki changelog returned Anubis access denied, so specific ARM/macOS changes were not verified. No upgrade or substitution of the pinned baseline was performed.
