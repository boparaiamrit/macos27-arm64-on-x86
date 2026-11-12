# Render gaps after R10: causes, fixes, tests, R11

Status: **R11 built and qualified on Lavapipe; boot handed to the parent** (no boot was run here, on
the parent's instruction). Summary: target 1 (RGBA16Unorm linear sample) and target 3 (memoryless
Clear) fixed; target 4's CPU recoveries traced to refused draws (removed upstream by R10b + R11);
targets 2 and 5 are precise refusals of formats outside the contract (0x226 dual-plane, 0x21e).
R11 `qemu-system-aarch64` sha256 `3c05b681fa345f8cec85ae78cf2e93a0453294ea35eac9a2ceda23678cc22f5d`.

## Base and scope
- R11 is built on **R10b** (`/work/orchard-m27-pages-m2v-prefix2`, QEMU `99db7628…`), the parent's
  supersession of R10: the R9 tree plus the `green7` metal2vulkan storage-class correction. Staging
  verifies the R10b tree against `m2v-prefix-load/logs/r10b-final-source.json` (1284 entries).
- R11 changes exactly 6 files, all under `crates/` and byte-identical in R10 and R10b before the change:
  `reims-vgpu-protocol/src/pixel_format.rs`, `reims-vgpu/src/runtime/draw/{texture_view.rs,
  vulkan.rs, render_target.rs, tests.rs, memoryless_observation.rs}`. Manifests and lockfiles are
  unchanged (asserted at staging). Overlay pins: `overlay-green.json` (6 files), `overlay-red.json`
  (the 2 test files only, on unchanged R10b production code).
- Owned paths: `/work/orchard-m27-pages-r11` in `macos-orchard-build` and `full-system/render-gaps/`.
  Runner `scripts/rg_run.py`, launcher `scripts/Launch-Rg.ps1` (final envelope per the parent: every
  container 2 CPU / 4 GiB, builds at 2 jobs, one container at a time; tests on the R9 runtime image
  with Lavapipe + Khronos validation; host-floor, OOM and renewed-sampler-lease guards polled every
  0.2 s), GPU groups `scripts/Run-GpuGroups.ps1`, overlays `scripts/make_overlays.py`.
- The change as a patch against R10b: `r11-render-gaps.patch` (6 files, 16 hunks, sha256
  `6d5734bc28f8d86c828254f2433944f6ebecf583b2d5e0be29ad085c2fea4464`); the same files are in
  `overlay/green/` with pins in `overlay-green.json`.

## Evidence used
Only our own Reims logs (R9 `20261029T124845Z-vjqu894q`, R10 `20261029T141852Z-igslwjqy`), open
source Reims/metal2vulkan code and our tests. No guest files, shaders or Apple binaries were read.

## Target 1 — wallpaper candidate (RGBA16Unorm 128x128, 5 mips): FIXED (base level)
**Cause.** The full-screen draw (pipe 43/123, `mid3` 1920x1080 RGBA16Float MRT) samples a linear
texture (object type 2, `fmt=0x6e` RGBA16Unorm, 5 levels, 260-byte descriptor, tight `bpr=1024`).
`resolve_sampled_source` has four rungs for a linear texture and every one declined:
1. `try_gva_resident_sample` — no resident (guest-CPU texture).
2. `try_linear_sample_zero_copy` — needs a stable guest-page alias; this host has none
   (`guest_run_rail off reason=host_page_alias_not_stable`, `qemu_map_pages_alias_failed`), so it
   declines `zc_lin_packed_unavailable` / `zc_lin_no_alias` (R9: 71 / 468).
3. `load_linear_guest_memoized` → `native_scratch_to_upload`: `linear_native_upload_format` had no
   arm for RGBA16Unorm (`sampled_class(0x6e)` = None), and the CPU fallback `RowToRgba8` has none
   either (by design: an 8-bit arm would discard the low byte). → `lin_rung_memo_declined`.
4. `load_sampled_rgba_static` — same two tables, same decline.
So the draw became `draw_prepare_texture_resolve_missing … reason=linear_sample` and, because a
refused draw stops the pass, `draws_skipped_after_engine_refusal` for the rest of that pass plus a
CPU recovery of the 1920x1080 composite (see target 4).

**Fix (contract owner, native-or-nothing like RGBA32Float).**
- `pixel_format.rs`: `SampledClass::Rgba16Unorm` (eight bytes, already `R16G16B16A16_UNORM` order);
  `sampled_class(MTL_FORMAT_RGBA16_UNORM)` answers it.
- `texture_view.rs`: `NativeUploads::unorm16` gate; `linear_native_upload_format` maps the class to
  `TexelLayout::Rgba16Unorm` only when the gate is open. Still no CPU convert arm.
- `vulkan.rs`: `native_uploads_asking_host` sets `unorm16` from
  `supports_sampled_layout_linear_filter(Rgba16Unorm)` (Vulkan mandates neither the sample nor the
  filter for 16-bit UNORM; the device probe already covers every `TexelLayout`). The host-gated set is
  derived (`native_bind_is_host_gated`), so 0x6e now asks the host automatically.
- Engine side unchanged: `SampledSourceRequest::Bytes` with `TexelLayout::Rgba16Unorm` is the path
  the RGBA16 buffer-texture rail already uses live.

**Mip levels — precise statement.** The decoded contract carries all 5 levels and the loader reads
level 0 through `level_gva(0)`. Every CPU/byte sampled rail on the draw path uploads one 2D image
(single-level `VkImage`, `mip_levels(1)` in the sampled pools; only compute carries pyramids), and
this is unchanged for every other format. A 128x128 texture drawn across 1920x1080 is magnified, so
the sampler reads level 0. Carrying all levels needs a multi-level `SampledSourceRequest` + pool
image + per-level upload; not done in R11 (see "Remaining").

## Target 2 — icons candidate (pipe 50 tex1 unbound, rt_wrong_type object_type=12): PRECISE REFUSAL (contract unknown)
- Object type 12 is `OBJECT_TYPE_DUAL_PLANE_TEXTURE` (`decode/resource/mod.rs`): a normal texture
  whose descriptor carries two dimension blocks; Reims decodes it (`decode_dual_plane_texture_descriptor`)
  and reports `dual_plane_texture_unexecutable`. R10 decoded seven shapes, all **pf=0x226** with two
  equal-size planes: 32x32, 64x64, 96x96, 128x128, 160x128, 160x160, 256x224 — icon/thumbnail sizes.
- The icon passes render *into* these (`rt_resolve reason=rt_wrong_type base=15|32|60|83
  object_type=12`, R10: 85 lines) and sample them (`draw_prepare_texture_resolve_missing … type=12
  … reason=unsupported_object_type`, pipes 48/54).
- Pipe 50's `frag_declared_descriptor_unbound tex1` is a different, lawful case: the guest bound only
  texture 0 (`provided_tex={0}`) and Reims substitutes a 1x1 neutral texture for the declared-unbound
  slot, as Metal leaves an unbound unread slot undefined. Its output went to tex_ref 41/42
  (RG16Float GVA) with `rgb_nz=0`, consistent with its real input (the dual-plane icon) being absent.
- Pixel format 0x226 (550) is not in Reims's pixel-format contract (no width, layout or per-plane
  format), and the two planes' meaning is not decoded anywhere in open source. Implementing it would
  mean guessing; the existing refusals (`dual_plane_texture_unexecutable pf=0x226 plane0=… plane1=…`,
  `rt_wrong_type object_type=12`) already name the object, format and geometry. No code change.

## Target 3 — memoryless Clear: FIXED
**Cause.** `resolve_memoryless_target` admitted only `MTLLoadActionDontCare`; the guest declares
Clear (2) on memoryless attachments (`rt_resolve reason=rt_memoryless_load_action value=2`; R9: 8,
R10: 92), so the attachment — and the MRT draw using it — was refused.
**Fix.** Admit DontCare **and** Clear; only Load (needs pre-pass contents) stays refused. Downstream
already implements a memoryless Clear without guest bytes: `mrt_draw_request` carries
`load_action=Clear` + the declared colour and never seeds a memoryless target; the Vulkan draw maps
`LoadAction::Clear` to `target_clear` (render-pass clear), secondary attachments to `with_clear`.

## Target 4 — `writeback_chain_rgba … cause=no_metal` (111 in R9, 105 in R10): CAUSE FOUND, removed upstream
`cause=no_metal` is the label of the `EncodeStatus::NoMetal` carrier, which a **refused Vulkan draw**
returns; it is not a Metal dependency of the resident chain. Every one of the 111 R9 recoveries
follows a refused draw (`draws_skipped_after_engine_refusal` or `draw_vk_nothing_stored`): by pipe,
128 (38), 187 (34+1), 115 (23), 123 (8+1), 44 (3+1), 43 (1), 152 (1). Pipes 115/128/187 are the m2v
translation refusals and 43/123 the target 1 texture refusal; the refusal kind of pipes 44 and 152
was not separated. The chain is abandoned and
its last frame is read back to
the guest mapping on the CPU (`resident_chain_abandoned_cpu_recovery`, 1920x1080 RGBA16Float). R10b
removes the translation refusals and R11 removes the RGBA16Unorm ones, so the recoveries should fall
with them (to be measured by the parent's R11 boot). No separate Vulkan resident path is needed
for this population.

## Target 5 — compute 0x21e, scanout 550: PRECISE REFUSALS (contract unknown)
- `compute_stage_tex view_fail reason=format_incompatible term=base_undeclared_here base=0x21e role=sampled
  … 512x512` (R10: 39): format 0x21e (542) has no entry in the contract's block-geometry table; the
  refusal already names the term.
- `capture_bpp_unknown format=550` (R9: 14) did not occur in R10; 550 = 0x226, the dual-plane format above.

## metal2vulkan (not a listed target, largest skip cause in R10)
R10 still logged the 10 R9 translation failures byte-for-byte (162 of its 251 skipped draws). The
cause was R10's storage-class restriction on the prefix load. The parent's R10b fixes it (whole-vector
over-read for every storage class, matching `emit_narrowing_vector_load`); R11 inherits that. An
independent variant written here before R10b was known (per-lane loads for shared storage, reading
exactly the source bytes) is kept unshipped in `m2v-alternative/`.

## Process log (shared-host events that shaped the order of work)
- 14:50Z: R10 boot finished; its log showed the m2v failures unchanged, so the work was first staged
  on R10 with an m2v correction of its own.
- 14:54Z: the parent's R10b (same storage-class root cause) appeared; R11 was re-based on R10b and
  the local m2v variant set aside (`m2v-alternative/`).
- 15:05–15:12Z: host C: fell below the 10 GiB floor (non-sparse `docker_data.vhdx`; seeds and builds
  from several agents). My guard stopped my RED build at the floor; I deleted my RED tree/target and
  an aborted m2v target (2.15 GB inside the VHD, no host gain) and moved to one target for both trees.
- 15:21–15:26Z: the parent stopped Docker/WSL (no compaction ran; stopping the VM returned the space:
  23 GiB free). My RED build was killed and restarted, then stopped again at 15:27Z at the parent's
  request for quiet CPU during its R10b boot; restarted after `actual-exit-r10b2.json`.
- 15:47Z: the parent capped every container at 4 GiB / 2 build jobs, one at a time (host commit), and
  renewed the sampler (PID 113232, lease to 2026-10-30T03:46:20Z); both applied to the launcher and
  runner, the over-cap build was stopped and rerun. Boots handed to the parent.

## Tests (RED then GREEN)
New owner-level tests (all in the `reims-vgpu` lib test binary):
- `runtime::draw::tests::a_sixteen_bit_normalized_sampled_texture_is_native_or_refused` — the
  contract: RGBA16Unorm → native `Rgba16Unorm` with the gate open, `None` with it shut, no CPU arm.
- `…::the_host_gated_sampled_formats_are_the_ones_whose_bind_the_host_decides` — 0x6e added to the
  host-gated list (so the loader asks the host, as for RGBA32Float).
- `…::rgba16_unorm_mip_chain_linear_texture_loads_its_base_level_natively` — the guest's shape
  (5 levels, 260-byte descriptor, tight rows) through `load_linear_from_host_caches` on Lavapipe:
  layout `Rgba16Unorm`, level-0 words exact (incl. 65534/65535), memo identity present.
- `…::mrt_draw_request_memoryless_clear_is_seedless_and_carries_its_colour` — the captured memoryless
  shape declaring Clear builds a request: memoryless, pass owner, no seed, `load_action=Clear`,
  declared colour.
- `runtime::draw::render_target::memoryless_observation::tests::*` — the fixture declares Clear and
  store 3; its first refusal is now the store action it declares (helper matches the declared value).

**RED** (R10b production + the two test files; binary `reims_vgpu-adceb44d491f78fa`, sha256
`e27aaccf…`, built `red-testbuild-5`, kept as `bin/red-bin-…`; run `gpu-red`, Lavapipe + Khronos
validation, 0 validation diagnostics): all four new tests fail with their own assertion — `left: None,
right: Some(Rgba16Unorm)`; `0x6e has a host-gated native bind and must ask`; `an RGBA16Unorm linear
texture must load on the byte rung`; `a memoryless Clear is inside the contract and must build a draw
request` — and 8 of 9 observation tests fail with `tag 9 must refuse at its own contract check:
MemorylessLoadAction { value: 2 }` (the ninth, the non-tag-9 type, passes).
**A harness defect found and fixed on the way.** The first RED/GREEN rounds ran with no Vulkan
driver: Lavapipe's `lvp_icd.json` names `/out/runtime/lib/libvulkan_lvp.so`, and my launcher mounted
the runtime only at `/soft` (R9's mounts it at both). The engine logged
`vk_engine_probe reason=vk_init_create_instance vk_result=Unable_to_find_a_Vulkan_driver`, so the
host capability query answered `false`: the RGBA16Unorm loader test failed on GREEN, and two R9
`desc_arena` "real driver" tests failed. With the second mount every group reports
`vulkan_instance_failures=0` (now recorded per group from the test's own fail log) and the loader
inserts `VK_LAYER_KHRONOS_validation` (settings `validate_core = true`, `validate_sync = true`). The
driverless rounds (`gpu-red`, `gpu-green`) are void; `gpu-red2` / `gpu-green2` replace them.

**RED (`gpu-red2`, with the driver):** the same 12 tests fail on their own assertions, 0 validation
diagnostics.

## GPU test results (Lavapipe, Khronos validation Core+SYNC, `--test-threads=1`)
GREEN `gpu-green2` (binary built from the R11 tree, `green-testbuild-1`): **491 passed, 0 failed**
(1 ignored, in the draw module), 0 validation diagnostics, 0 instance failures:
- new tests: 5 groups, 13 tests, all pass;
- `runtime::draw::` (whole draw module): 240 passed, 1 ignored;
- the R9 qualification regression list (17 groups; R9 counted 237): native-format 16,
  rgba16-actual-runtime 7, rgb10-actual-runtime 4, buffer-read-debt 1, buffer-texture-debt 1,
  writeback-debt 20, settle-site 1, shader-cache 48, shader-capture 10, buffer-descriptor 1,
  indexed-owner (`mrt_order_`) 7, device-features 22, engine-exec 58, depth-readiness 3,
  descriptor-arena 11, descriptor-retention 6, memoryless-identity 22 — all pass.
- `reims-vgpu-protocol` lib (`green-protocol-1`): 398 passed, 0 failed (includes the exhaustive
  `sampled_class` / layout cross-checks that now name `Rgba16Unorm`).
- `cargo fmt --all -- --check`: my two test-only formatting diffs (one assert, one tuple) were fixed
  and re-staged (`green-fmt-2`); the remaining diffs are in 11 files R11 does not touch (byte-identical
  to the R10b authority), i.e. pre-existing in R10b.
- **Final round `gpu-green3`** on the final (re-formatted) tree, binary `green-testbuild-2`
  (`reims_vgpu-adceb44d491f78fa`, sha256 `5d702375f24e397b…`): **491 passed, 0 failed**, 0 validation
  diagnostics, 0 instance failures, every group exit 0 — identical counts to `gpu-green2`.
- Compiler warnings: none in the six files; the test build shows 5 and the staticlib 2, all
  pre-existing (the staticlib's pair is identical to R10b's own build log).
- Not run: clippy (would need a check-mode build of every dependency under the 2-job/4 GiB envelope);
  the `vk_engine_parity` integration binary (not affected by these files).
## R11 artifacts (`/work/orchard-m27-pages-r11/artifacts`, receipts `logs/build-1-*`, `logs/link-1-*`, `logs/r11-artifacts.json`)
| file | sha256 | bytes |
|---|---|---|
| `qemu-system-aarch64` | `3c05b681fa345f8cec85ae78cf2e93a0453294ea35eac9a2ceda23678cc22f5d` | 70 858 672 |
| `libreims_vgpu.a` | `de0ac8ab9b7ff712869f37d511d109478bb47cd72174a7bdf200b79e88ec9d7b` | 175 004 322 |

- Staticlib: `cargo build --release --locked --offline -p reims-vgpu --no-default-features --features
  backend-vulkan,host-window` from the final staged tree (`stage-green-d`, 1284 entries = R10b + the
  six files; asserted equal before and after the build; `reims_vgpu` staticlib not fresh).
- QEMU: R9's link row from `/work/orchard-m27/qemu/build` (`ninja -t compdb`), exactly two
  arguments changed (output → `artifacts/qemu-system-aarch64`, library → `artifacts/libreims_vgpu.a`);
  `--version`: QEMU emulator version 11.1.50. Hashes re-verified after the scratch target was deleted.
- No Windows-side copies (disk floor); the library in `artifacts/` was a hard link to the build
  output and now stands alone (link count 1).
- Remaining footprint: `/work/orchard-m27-pages-r11` = `artifacts/` 235 MB + R11 source tree 47 MB
  (kept for the R11+R12 merge); target and RED binary deleted (1.70 GB). `render-gaps/` on C: 13 MB.

## Boot (the parent boots R11; not run here per the parent's instruction)
Ready-made admission, chained from the current pin (R10b `99db7628…`; fresh-01 identity
`5a0b7cb447770180416d35cfa93639854d394482edc3491d82c1b479cbee02e0` per
`r10-boot-test/identity-check-r10b2.txt`):
1. `python render-gaps/boot/make_r11_sources.py <QEMU_SHA> <LIBRARY_SHA> 5a0b7cb4…` writes
   `local-raw/golden_m27_pages_r11_profile.py`, `local-raw/migrate-m27-pages-r11-identity.py`,
   `render-gaps/boot/test_r11_{profile,migration}.py`, and adds the `m27-pages-r11` branch to
   `local-raw/run-crypto-frames-attempt.py` (dry-run verified: every substitution matches once).
2. Add `'m27-pages-r11'` to the `QemuProfile` ValidateSet in `mouse-guest/Launch-Rgba16MouseAttempt.ps1`
   (not edited here: the shared launcher belongs to the parent's merge).
3. `render-gaps/boot/run-once.ps1` — the R10b flow (guards, lock check, migration, CheckOnly,
   launcher), exporter identity by name + running state, Lavapipe route by default (add
   `VulkanDriver='gpu'` for the RTX 5070/Dozen route). `render-gaps/boot/inspect-state.py` is the
   read-only pre/post state probe adapted from R9.
Compare with `r10-boot-test/compare.py OUT.json attempts/20261029T152916Z-47419j9y <R11 attempt>`;
the checks that matter: `linux_m2v_draw reason=draw_prepare_texture_resolve_missing … fmt=0x6e`
→ 0, `rt_memoryless_load_action` → 0, `draws_skipped_after_engine_refusal` and
`resident_chain_abandoned_cpu_recovery` down by the wallpaper pass's share, and the frames' wallpaper.
## Cross-check on the parent's R10b boots (no R11 boot yet; the parent boots R11)
- R10b on Lavapipe was stopped by the disk floor (`20261029T145420Z-i19c705t`, guard failure).
- R10b2 on the RTX 5070 via Dozen (`20261029T152916Z-47419j9y`): 0 translation failures (R10b's fix
  confirmed live), 83 skipped draws: 46 `color_input_ordered_access_unavailable` and 24
  `draw_prepare_texture_access_unsupported` (Dozen; the GPU agent's), **13
  `draw_prepare_texture_resolve_missing`** — the RGBA16Unorm 0x6e wallpaper texture (target 1) and the
  0x226 dual-plane objects (target 2) — plus `rt_memoryless_load_action` 6 (target 3) and 48
  `resident_chain_abandoned_cpu_recovery` (target 4). Dozen also reports
  `host_pointer_import=no_host_pointer_extension`, so it uses the same CPU byte rung the target 1
  fix serves.

## Remaining
1. **Boot R11** (parent): Lavapipe route (`run-once.ps1` as is) and/or the RTX 5070 route
   (`VulkanDriver='gpu'`), compared against R10 (Lavapipe) / R10b2 (`20261029T152916Z-47419j9y`, GPU).
2. **Mip levels of sampled linear textures** (target 1): the draw path's byte rails carry one 2D
   image for every format, so levels 1..N are not uploaded. Carrying the decoded chain needs a
   multi-level `SampledSourceRequest`, a multi-level pool image/view and per-level copies; worth doing
   if the boot shows minified samples of these textures.
3. **Dual-plane 0x226** (target 2): needs the per-plane format contract of pixel format 550, which no
   open-source decode states. Until then the refusal stands (`dual_plane_texture_unexecutable`,
   `rt_wrong_type object_type=12`). The dual-plane device-info bit (key 12) follows the negotiated
   protocol version (62), not a host capability, so it is not a lever to steer the guest away.
4. **Format 0x21e** (target 5): outside the block-geometry table; compute refusal `base_undeclared_here`.
5. **Not run:** clippy (check-mode build of every dependency does not fit the 2-job/4 GiB envelope
   quickly), `vk_engine_parity`, conformance. `cargo fmt --check` debt in 11 untouched files is R10b's.
6. **R10b2's other refusals** (`color_input_ordered_access_unavailable` 46,
   `draw_prepare_texture_access_unsupported` 24) are Dozen-specific and the GPU agent's (R12-gpu).
