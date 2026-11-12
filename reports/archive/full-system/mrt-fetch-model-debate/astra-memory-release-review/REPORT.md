# Astra bounded memory-release review

Verdict: **bounded static review passes; no material verified findings in the proposed two-file fix.** Runtime qualification, allocation-trace attribution, and admitted import coverage remain outstanding. This is not release approval and does not establish that VkDeviceMemory 0x200000000020 was allocated by the suspected site.

## Scope and authority

Read-only source analysis of `mrt-memory-release-fix/{parent-admission.json,source-manifest.json,owner-memory-release.patch,before,diagnostic-source,fixed-source}`, R3 REPORT/handoff, R3 source-view pool/caller files and qualification fixture, and hash-matched host study slab/import/presenter owners. All paths below are relative to `test-output/arm-macos/full-system` unless noted.

- Admission SHA256 matches `fabd9eb3db1299aa0744fe46ab82864cbaadf17c3a3842c6c79e6eec9fc79bad`.
- Manifest SHA256 matches `959521aedd8937bd53cbecb9fb98264ff64ae0dec029c9871d8597d3124281c5`.
- Patch SHA256 matches admission: `e2e4f96a561f4bf733429627c1b1beef28a8e3f23a0d09c38e6d587cd9591b4f`.
- Both before hashes match R3 `qualification-final-source.json`. All six before/diagnostic/fixed file hashes match the supplied manifest. In-memory hunk application confirms the patch transforms diagnostic-source into fixed-source exactly (text comparison; fixed raw bytes separately hash-verified).
- Fixed pools/mod.rs SHA256: `fcafe529e1fa624ec23f4a8109562df884dc0050c9fdd72f1c9221137b966436`.
- Fixed pools/teardown.rs SHA256: `1aa3c93ed74485f43642338f6580f81218607e1ecf892e9c11f26d2a4f28ad49`.
- Supporting R3 pool chapters match final authority. The source-view engine/mod.rs predates the qualification include; appending the exact documented cfg(test) include in memory reproduces its final authority hash. Source-view exec.rs also predates the documented fixture-only format correction; it was not used to establish production caller ordering. `qualification-cases.rs` matches the final r3-qualification.rs hash.
- Host study slab.rs, host_ram.rs and window_present.rs were read only after their hashes matched R3 authority. Their hashes are recorded in findings.json.

Installed codebase-memory skill read. Graph/index/coverage tools unavailable in this session; parent also reported unavailable coverage. Named-source read/search fallback only, no graph coverage or repository-wide completeness claim.

## Challenges resolved within this scope

Line references in this section use `crates/reims-vgpu/src/backend/vulkan/engine/` as the source prefix. Fixed files are under `mrt-memory-release-fix/fixed-source`; unchanged chapters/callers are R3 source-view; slab/import/presenter are hash-matched reims-study.

1. **Shared slab and final drain:** fixed pools/mod.rs:118-137 calls `free_image` first and raw-frees only on false. slab.rs:605-612 removes an image token from the host map; this is not a driver operation on a destroyed image. slab.rs:642-663 frees a block only after its allocation plan becomes empty, and takes the block out of storage before freeing. slab.rs:770-775 drains only remaining blocks. Thus another registered live image keeps its block occupied; an early-freed block cannot be freed again by the final drain. Sampled/snapshot wholesale paths remain unchanged and keep their tokens until final slab destruction, conservatively preventing early release of their blocks.

2. **Allocation classes:** pools/images_and_registry.rs:1713-1760 allocates and binds independent memory for MRT secondary/depth residents and marks it Recyclable. Depth enters that same path at :1846-1866. Retirement removes the resident and transfers its handles to RecycleTarget at :1110-1131; reuse can transfer that dedicated backing into the primary registry at :1407-1414. Therefore registry and target_free really need both slab and dedicated handling. Ordinary targets and multisample targets currently allocate through `bind_image_slab` (pools/submission_and_buffers.rs:3888 and :4023), whose successful bind registers the image at :1003-1013. They are not independently demonstrated raw-dedicated producers; their new helper calls use the slab branch, including any dedicated-sized block still tracked by SlabPool. No import producer enters these target containers in the inspected paths.

3. **Image/view/framebuffer ordering:** fixed pools/teardown.rs:123-127 drains ad-hoc framebuffers before wholesale image drains; :148-150, :186-196 and :218-225 destroy relevant framebuffers/views/images before releasing backing. Registry alternate views are explicitly destroyed at :219-220. `attachment_view` is stored among those alternate views by pools/images_and_registry.rs:1036-1049. The three hot-path replacements at fixed pools/mod.rs:1380, :1404, :1409 preserve the previous slab-or-raw release logic and order; framebuffer purging remains at :1366-1367.

4. **Guest parent lifetime:** fixed pools/teardown.rs:224-225 matches only Recyclable. GuestImported never reaches raw release. Guest sampled children are destroyed at :165-168, registry children at :218-223, and host parent allocations only at :233. Hot GuestImage/barrier handling remains unchanged at fixed pools/mod.rs:1382-1399. host_ram.rs:335-359 requires retirement, no child images, and cleared retirement fences before returning a parent; wholesale :426-429 owns the remaining parents. The patch adds no second parent owner or child-count mutation.

5. **Quiescence and command references:** fixed teardown retains open-batch discard, fence waits, pending-list folding and graveyard drain at :18-65. Engine flush ordering is queue barrier, presenter destruction, caches, then pools (engine/mod.rs:402-414); the presenter begins destruction with queue idle (window_present.rs:1774-1777). Guest reset idles at engine/mod.rs:1113 before :1122; healthy test reset idles at :5741 before :5747. The final hash-matched R3 qualification fixture requires successful queue idle before cache/pool/device destruction at r3-qualification.rs:42-44. The new helper does not move any release ahead of these boundaries. Never-submitted command buffers are discarded and later destroyed with their pool; they do not become new submissions through this patch.

6. **Borrow/state/readiness:** the helper borrows only the disjoint slab field while each target container drains; no call reacquires a mutable ResourcePools borrow. The three hot calls are otherwise expression-equivalent to the old branches. No readiness flag, resident invalidation epoch, queue policy, capacity, allocator policy, pool admission, or arbitrary eviction changes appear in the patch. Diagnostic additions are cfg(test) receipts only.

## Remaining limits and parent gate

No tests, builds, compiler checks, Docker calls, volume inspection, VM execution, guest input, or delegation were performed. Only this REPORT.md and findings.json were written.

Existing teardown logs failed fence/queue waits and proceeds; this review does not upgrade that behavior into a guarantee of successful quiescence on every failure path. No new wait-error behavior is introduced. Borrow checking and API behavior still require the separately authorized qualification.

The R3 reported handle remains **UNMAPPED for this review**. The case name and source-level dedicated-allocation gap do not attribute that specific handle. Preserve the admission gate: the one trace-only diagnostic must map the actual leaked handle to its allocation site and registry/recycled terminal owner before applying the prepared fix. If it maps elsewhere, stop for parent review. No pending parallel run results were inferred or consumed.

Still required externally: clean explicit destruction for live dedicated resident, dedicated resident retired to target_free, two images sharing a slab, import handling where actually admitted, existing mixed default/narrow controls, and 8+ refused transient-depth cases. R3 has no admitted imported-backing runtime case; static parent/child preservation is not imported API qualification. Synchronous readback is not pending-fence, guest-debt, desktop, or interaction proof.

Minimal parent source fix requested: **none from this bounded review**.
