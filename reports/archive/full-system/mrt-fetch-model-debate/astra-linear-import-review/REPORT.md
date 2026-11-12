# Bounded independent static review

Verdict: **BOUNDED STATIC PASS**. No verified actionable production findings. Confidence: high for the refusal boundary and the inspected consumer control flow; runtime behavior is unqualified by this review. No production change is requested.

Scope: the pinned one-file `linear-import-initialization-fix/production.patch` and its before/fixed source, with the named consumer snapshots and R5 witness. Only this report and findings.json were created. No Docker, VM, build, tests, services, staging, production edits, or delegation occurred. Any separate future test fixture is outside this verdict.

## Evidence identity

SHA-256 verified from local bytes:

- source-manifest.json: `fb4d03763495a74b5b4aebfdc0d209e31273c8fb46378840d6cb66ac3118b1b1`
- production.patch: `100588f31f9f5f4f4f4a60fe91ec73c37a46f3612f79c9015cc9318ee690c913`
- before linear_target_import.rs: `e9a45a63d55a1d20fbdcf5fe4903b35e72aad14b5d848e22483157f9e86a7887`
- fixed linear_target_import.rs: `217119bd48b826bf100f5cd95e966b7deb815e6814f8d15017bc3e7edefc7778`
- qualification-final-source3.json: `0dd19cc6548bf3010a10be416f5246932fa08f85e405d3c5e3ad49761a4ae4c6`

The complete unified diff of before/fixed text equals production.patch. The before image-import file and submission_and_buffers.rs match the R5 authority; the selected fixed pools/mod.rs and compile-fix-source exec.rs also match that authority. Exact per-file hashes are in findings.json.

The images_and_registry.rs study mirror hashes to `38308f57f193a346373a328620879a5c4bcd9cc6fba93d3ebbc71f71b1b654af`, not R5's `22eb8902cd17113335be976ade28b10051f1e1445332552e978deff8a45de7a0`. Both hashes and sizes match the recorded known test-only delta in mrt-memory-release-validation/source-preservation-status.json and qualification-test-delta3.json. Its use here relies on that recorded classification and the parent's append-only-test-accessor description; this review did not independently reconstruct the later 551-byte addition. Production line references below are to this explicitly identified mirror. R5 source-preservation-status reports all 1282 entries equal; this review verified the selected duplicates, not all 1282 actual source files.

The installed codebase-memory skill was read. No graph tools were available in this session, so structural review used bounded read/search on these sources; no graph coverage is claimed. The relevant root instructions were read from actual-source-instructions.json. A targeted memory search returned no relevant entries.

## Challenges resolved

All Rust references below are relative to `crates/reims-vgpu/src/backend/vulkan/engine/`; snapshot locations are listed in findings.json.

1. **Legitimate fallback versus hiding a validator error.** Fixed `linear_target_import.rs:325-330` names the missing preservation contract; `:393` always requests preservation and returns before `imports.allocation` at `:395`. Thus the correction deliberately disables new direct image imports, including hosts where R5 admitted one. It does not reclassify R5 as hardware-unsupported or API-clean. The old native stdout contains two real 01443 errors despite Rust reporting a pass. The new slug at `:73` states an implementation limitation, and both callers emit it (`images_and_registry.rs:1357-1368`, `submission_and_buffers.rs:4136-4147`). Earlier environment/topology/extension/parent-identity refusals still describe their own valid preconditions; replacing later alignment failures with the preservation refusal is not a false cause, because preservation is independently unsupported.

2. **Invalid creation reachability.** The only three calls to private `create_with_layout` in the reviewed factory are `linear_target_import.rs:410`, `:430`, and `:449`, all after the unconditional preservation gate. They receive the checked layout; the image-create builder uses it at `:494`. The discard branch returns UNDEFINED but no production caller selects it. There is no newly accepted image to which the old PREINITIALIZED tracking can be incorrectly applied. Future admission requires a new preservation/initialization contract and coordinated consumer changes; flipping the boolean alone would not be an approved extension.

3. **Primary content and birth state.** Factory Err becomes None at `images_and_registry.rs:1345-1372`; owned/recycled allocation follows at `:1407`, with new image UNDEFINED at `:1433`. `register_resident` derives guest-backed status from actual memory ownership at `:1033`, and initializes content_ready/access at `:1057-1062`. Recyclable birth is false/Untouched, including a recycled allocation. In exact `exec.rs:3735-3743`, only actual GuestImported ownership enables the direct seed bypass. Refusal leaves it false; guest buffer import or CPU staging supplies seed bytes at `:3865-3910`, and the full attachment seed is copied at `:4967-5021`. LOAD with unready alleged GPU content still refuses at `:3745-3750`; no false readiness was introduced.

4. **Sampled fallback.** `submission_and_buffers.rs:4136-4147` returns Ok(None) before creating a view or inserting guest_sampled. Consequently `exec.rs:4156-4188` cannot select GuestDirect for a new image. It reaches owned acquisition at `:4223`, imported-buffer/CPU staging at `:4243-4267`, GuestGather construction at `:4270`, and upload at `:5034-5058`. The existing copied-content cache remains subject to its existing identity checks; refusal does not insert a success or fabricated initialization entry.

5. **Cleanup and unchanged buffer capability.** The refusal acquires no imported parent, creates no child, and increments no child reference, so it creates no new partial-object cleanup obligation. The primary and sampled imported success blocks remain unentered. Owned fallback retains its existing error cleanup, including framebuffer failure at `images_and_registry.rs:1559-1579`. No buffer import code or queue/allocation policy is changed; both fallback paths still invoke import_sampled_guest_window. This is a static ownership argument, not measured buffer lifetime proof.

6. **Remaining PREINITIALIZED consumers.** Exact fixed `pools/mod.rs:2090` still maps GuestBacking to PREINITIALIZED; exact `exec.rs:4818-4834` still transitions GuestDirect from it. Both require an admitted direct image. Production insertions examined in the two consumers are downstream of factory success, so neither applies to a new direct image under this patch. Sampled cache reuse before the factory (`submission_and_buffers.rs:4108-4114`) does not create a bypass in a freshly started process built from these sources: no new entry can be admitted. Live migration of pre-patch objects is neither implemented nor claimed.

## Specification and limits

The current official [VkImageCreateInfo valid usage](https://docs.vulkan.org/refpages/latest/refpages/source/VkImageCreateInfo.html) requires UNDEFINED for nonzero external handle types (01443). The official [image layout and external ownership rules](https://docs.vulkan.org/spec/latest/chapters/resources.html#resources-image-layouts) do not make an UNDEFINED discard transition preserve preexisting host pixels. Existing external-image layout/ownership mechanisms must not be inferred merely from HOST_ALLOCATION. No such acquisition/initialization mechanism is established by the inspected factory. Refusal is therefore a defensible bounded correction; changing only the initial constant and retaining GuestBacking readiness would not be.

No compilation, lint, test execution, GPU validation, pixel oracle, performance measurement, or guest run was performed. Additional copies and owned allocation pressure are an intentional consequence, with magnitude unmeasured. The helper tests in the pinned patch cover its decision, not end-to-end pixels. Required subsequent qualification includes actual primary LOAD/partial-draw guest-seed preservation, sampled fallback upload pixels, independent actual imported-buffer parent lifetime, Core plus synchronization validation, and the full MRT/resource qualification before publication. A refusal/skip or zero 01443 events cannot qualify imported images, memory lifetime, or a desktop. No source-staging or publication approval is implied.
