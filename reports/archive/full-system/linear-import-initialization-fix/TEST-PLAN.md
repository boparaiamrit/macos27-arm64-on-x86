# Native imported-image fallback fixture packet

Prepared statically only. No Docker, VM, compilation, tests, GPU calls, production
source edits or delegation occurred. The parent must compile and execute this
packet under its admitted R6 envelope before claiming any pass.

`fallback-tests.rs` SHA-256:
`b22aec4136ab8007416c06652e6d5cf6fecc0adced2fc864f587a0ea6d4b12bc`.

## Integration

Stage these exact bytes as
`crates/reims-vgpu/src/backend/vulkan/engine/linear-import-fallback-tests.rs` in
the existing isolated MRT source, then append only this test-module declaration
to `engine/mod.rs`:

```rust
#[cfg(test)]
#[path = "linear-import-fallback-tests.rs"]
mod linear_import_fallback_validation;
```

The existing `engine/r3-pixel-helpers.rs` is included by relative path and remains
unchanged. Its SPIR-V reader uses `CARGO_MANIFEST_DIR/tests/fixtures/mrt-order`,
not an environment variable or output directory. All four required binaries are
already in the 1,282-entry authority; generate no new shaders.

Freshly compile the existing locked/offline release unit binary as required by
the parent's source/binary provenance gate. Run each of the following in a fresh
owned process, serially, with the qualified Core+SYNC layer and runtime. Repeat
the two pixel cases under default GENERAL and narrow policies. No skip or
missing-host-import success is permitted: this qualification runtime already
admitted Unified host-pointer import in R5.

1. Exact test
   `backend::vulkan::engine::linear_import_fallback_validation::imported_image_fallback_actual_control`,
   environment `IMPORT_FALLBACK_CASE=primary-load`.
2. The same exact test with `IMPORT_FALLBACK_CASE=sampled-upload`.
3. Exact test
   `backend::vulkan::engine::linear_import_fallback_validation::imported_buffer_parent_actual_ownership_control`.
   It needs no case environment variable.

Do not run the case-selected method without its environment variable. Do not
interpret a Rust pass as API success; classify both native output streams first.

## Oracles and required receipts

Both draw cases allocate actual aligned host storage, create a checked
`GuestRamImport`, `GuestRef`, `GuestRunSource` and one real page-backed source.
The allocation remains live until queue-idle, pool/cache destruction and explicit
device destruction finish. On assertion failure the fixture deliberately does
not free storage a native device might still access; the bounded test process
owns failure-path cleanup.

Before the draw, the real direct-image factory is called with a fresh real
`HostRamImports`. It must return
`WindowRefusal::PreservedContentsUnsupported`, with imported bytes zero, counts
`(0, 0)` and no alias. Required receipt:
`IMPORT_FALLBACK_REFUSAL reason=preserved_contents_unimplemented parent_bytes=0`.
This is an unimplemented preservation-contract refusal, not unsupported hardware.

### Primary LOAD / partial draw

The request carries `guest_target_memory`, `load_guest_target_backing=true` and
`target_guest_seed`, with no CPU `target_rgba8`. Its source is actual guest bytes
`[51, 102, 153, 255]` per texel. The declared action is LOAD. The established
ordered-fetch shader computes RGB `source * 0.5 + 0.05` and alpha one. Its
16-by-16 scissor begins at `(2, 2)` inside a 20-by-20 image.

Expected 256 inner pixels: `[0.15, 0.25, 0.35, 1]`. Expected 144 untouched guard
pixels: `[0.2, 0.4, 0.6, 1]`. A missing or discarded seed therefore fails both the
inner computation and the nonzero border. The actual resulting registry slot
must be owned rather than guest-imported and must become content-ready only
through the completed real draw. Receipt: `IMPORT_FALLBACK_PRIMARY_OWNED`.

### Sampled upload

The request's `SampledSource::GuestRuns` carries a real `direct_image`, strong
serialized resource owner, and the same complete bounded fallback source. It
has no copied-content identity and a `GatherVouch::Fresh`. Existing
`sample.frag.spv` performs `texelFetch` at the current framebuffer coordinate from
binding one. The guest source contains `[128, 64, 192, 255]` per texel.

Expected 256 inner pixels:
`[128/255, 64/255, 192/255, 1]`; expected 144 guard pixels:
`[0.2, 0.4, 0.6, 1]`. There is no alternative sampled byte source in the request.

Both cases require the actual post-draw native buffer alias to exist for this
import identity (`IMPORT_FALLBACK_BUFFER_LIVE`), rather than creating a buffer
afterward to manufacture evidence. This witnesses that the native buffer rail
remains enabled while the invalid direct-image rail declines.

The existing oracle writes exact 1,600-byte RGBA readbacks and metadata under
`/out/engine-readbacks`, checks finite expected values and every channel with
tolerance `3/255`, and reports guard counts. The parent should independently
audit these files. The warmup draw also has its own exact oracle and is not the
fallback result.

### Native buffer-parent ownership

The separate control calls the real parent allocation factory twice on the same
actual aligned allocation. It requires identical non-null native buffer/memory
handles and counts `(0, 1)`. It then waits for the native queue, destroys imports,
requires zero remaining imports and explicitly destroys the device. Receipt:
`IMPORT_BUFFER_PARENT_ADMITTED` and `IMPORT_BUFFER_PARENT_COMPLETE`.

All three controls require actual mapped validation/runtime library receipts,
`IMPORT_FALLBACK_DEVICE_DESTROY_COMPLETE`, and exactly one terminal alias-release
notification for their real parent before freeing fixture storage:
`IMPORT_FALLBACK_ALIAS_RELEASE_BALANCED`. Existing cfg(test) parent-free tracing
must corroborate actual VkDeviceMemory ownership. The alias notification alone
does not prove the driver's API calls were valid.

Reject any unexpected VUID (including 01443 or 05137), SYNC hazard, native
allocation failure, missing receipt, test failure or missing required case.

## Verified source dependencies

Used bounded exact-source verification under the installed codebase-memory skill;
the parent reported graph tools unavailable. No graph/index coverage is claimed.
Relevant sources were compared with R4 `qualification-final-source3.json`.

| Current source | SHA-256 |
| --- | --- |
| `engine/exec.rs` | `679c9b59c6c7935ea87a65504dd36285dbec63ff5f0526695678ad58c0c8e3e8` |
| `engine/types.rs` | `a55fd3e8492ba5952d5852405061380cacdd43edcd087be37c34c436909fc660` |
| `engine/r3-pixel-helpers.rs` | `b9242d464729435a2f242686c115acd1d2265a1ad5b3e5f6880ca8465b333d27` |
| `engine/pools/submission_and_buffers.rs` | `ed8a76b346e5d3ba40f6c6fac6a4baff391685e3e70bd886fa8bef1e636506b1` |
| `reims-vgpu-memory/src/lib.rs` | `c468c5589540a6d3bd8615c9fe1060a99935eac1c387adc783eccd12647817ac` |
| `model/state.rs` | `b0625341bb0d8fa1c45306f4ee208b59cc9339a5021e681f3b83e6ddb4e39e28` |
| `runtime/guest_ram_map.rs` | `131b84c8929b2ac1a06e5d9e9d9eedf0641ea078c1013dca1413f4a06a5c999d` |
| `runtime/gather_witness.rs` | `a620fa3dcf013283f4c9524c11fc22628f7d6b8416de0398eab8c42a93921708` |

The `reims-study` types mirror did **not** match current authority and was not
used as the final field authority. Current types were read from the matching R3
source-view. Existing R4 ownership controls supplied the exact teardown and
test-accessor API. Those controls are unchanged by this packet.

Required existing shader pins:

| Fixture | SHA-256 |
| --- | --- |
| `fetch.vert.spv` | `30d7c2849ce1672ca80ef4db77957c459d32f9dac7275819b8ba011310f45597` |
| `r3-solid.frag.spv` | `ec4268936f722cc8238131b0d4511d4737f5e24b963f3e23774a23f21e632974` |
| `r3-primary.frag.spv` | `7f0b3e63524d9c45c7c6c4ba1813aee62dbf765c4a01c31a18ac0adb01ec9434` |
| `sample.frag.spv` | `f0d1c286376d22b60b7e65d27b0e2b4c843c333f791b8cb14fad9f240a1703a5` |

This packet establishes no compilation, runtime, macOS, GUI, or interaction pass.
