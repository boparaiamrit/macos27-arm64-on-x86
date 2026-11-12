# Native RGBA16Unorm buffer-texture extension

The source patch is frozen for parent review. Only new owned copies under
`full-system/rgba16-buffer-texture/` were edited. The qualified RGB10 source,
study tree, translator, admitted emulator/library, VM, disk sources and live
input/control state were not changed or executed.

## Scope and contract

The parent identified nine direct opcode-9 buffer-texture conversion refusals
with format 0x6e, width 384, height 384 and bytesPerRow 3072. This report does not
independently claim guest-field acceptance or visual causality: depth, sample,
array, mip and swizzle fields were not logged for those records.

The existing protocol names 0x6e as `MTL_FORMAT_RGBA16_UNORM` and provides
`TexelLayout::Rgba16Unorm`: eight little-endian bytes containing R/G/B/A UNORM16
channels. The existing Vulkan rail maps it to `R16G16B16A16_UNORM`. Those owners
were used read-only; the patch changes neither their declarations nor mappings.

The exact native selector now admits:

| Guest format | Native byte layout |
| --- | --- |
| 0x5a RGB10A2Unorm | `Rgb10a2Unorm`, four packed bytes |
| 0x6e RGBA16Unorm | `Rgba16Unorm`, eight channel bytes |

The private `NativeBufferTexture` stores the selected layout and source ordinal.
Its tight-row geometry, host sampled-layout capability query, padded-row copy
and returned `SampledByteFormat` all derive from that selected plan. The new
RGBA16 branch never routes through an RGBA8 conversion or narrows any channel.
Every other ordinal remains on the prior loader; an exhaustive u16 ordinal
test verifies exactly two native selections and no host query for other formats.

The existing exact `TextureLevelLayout::read_span`, source offset/range,
guest-address arithmetic, row/host-length overflow, padding exclusion and
owned output semantics remain in force. Native host or shape refusals remain
terminal typed refusals, without a lossy fallback.

The existing 2D/single-depth/single-array/single-sample/single-mip and absent
descriptor-swizzle gates are unchanged. The qualified `vulkan.rs`, `mod.rs` and
`rgb10_runtime_tests.rs`, including the existing capability injection seam and
debt-paying runtime reader, are byte-identical to their qualified originals.
Only `buffer_texture.rs` and `buffer_texture_tests.rs` differ.

## Actual verification

Used native Windows `rustc 1.99.0 (b940084d7 2026-09-28)` with debug information
disabled, no Cargo, GPU, Docker, QEMU, VM or guest input/control work. Each
compiler/test command had a 120-second limit, 2 MiB log limit and a 0.2-second
unconditional C: free-space guard at 10 GiB. All owned outputs are below 20 MiB.
The recorded free-space samples remained above 13 GiB, the maximum observed
guard interval was 0.204 seconds, and owned outputs were approximately 11.2 MB.

- **RED before helper changes:** compiled the actual unmodified qualified
  helper copy through `#[path]` with the newly added regression tests. The
  384x384/pitch 3072 test failed because native RGBA16 selection returned `None`:
  exit 101, 0 passed/1 failed, 15 tests filtered. This was the intended missing
  native-plan failure, with no harness compile errors.
- **GREEN:** compiled the actual changed helper and its real test file through
  `#[path]`. **16 tests passed**, including all ten original RGB10/helper tests
  and six new RGBA16/two-format tests.
- `rustfmt --edition 2021 --config skip_children=true --check` passed for both
  changed files. Exact command arguments are recorded in `format-check.json`.
- Freeze verification found no trailing whitespace, exactly two changed files,
  and all three qualified runtime/injection/debt-test files unchanged.

The harness compiles real production pixel-format/endian/extent sources into
a small rlib. It extracts the actual production `TextureLevelLayout` and its
`read_span`, `BufferTextureDescriptor`, serialized texture descriptor type,
`Decline` trait and `host_alloc_len` verbatim. It does not contain another
implementation of the planner or converter. Exact full-source and extracted
fragment hashes are in the RED/GREEN provenance receipts.

The new tests cover:

- A 384x384/pitch 3072 bit-exact eight-byte upload, using adjacent u16 codes in
  every channel: `[1,511,32767,65534]` and `[2,512,32768,65535]`. All output
  bytes, layout, source-format metadata, per-channel ordering and one-code gaps
  are checked.
- Odd 3x3 rows with pitch 32, nonzero offset 29, padding removal, exact final
  tight-row footprint 88 bytes and short source/allocation refusal.
- Native capability refusal and all existing unsupported shape/swizzle gates,
  including mip-count 5 refusal.
- Source offset/range/address and eight-byte tight-row/span/host-length
  overflow, plus zero geometry refusal.
- Tight default pitch and output ownership after modifying/dropping the source.
- Exact two-format selection across all 65,536 possible ordinals, retaining
  all original RGB10 regression cases.

These are helper-contract proofs. The full runtime module, real debt ledger,
Vulkan upload/sample/readback, actual host capability behavior, new emulator
and guest rendering were not compiled or executed in this task. The unchanged
debt reader/injection seam is preserved for the parent's subsequent checks.

## Review and build inputs

- `owner.patch`: delta against the qualified RGB10 source copies, containing
  only the native helper and its owner tests.
- `source/`: five qualified owner-file copies; only two have changed.
- `before/`: exact read-only-start baseline copies.
- `source-sha256.json`: baseline/after hashes, unchanged-file evidence and
  patch hash.
- `red-provenance.json`, `green-provenance.json`: all actual source and extracted
  fragment hashes used by the tests.
- `*-test-build.log`, `*-tests.log` and matching JSON receipts: commands,
  results, duration and disk-guard samples.
- `verification-summary.json`: guard and scope summary.

Future parent builds should copy the admitted qualified RGB baseline and apply
this two-file delta. The helper runtime API and injection seam were not changed.

## Future checks, not run

Run the focused owner tests in the full qualified runtime and the actual
RGBA16 native-path debt/allocation/capability fixtures under a separately
admitted build resource envelope. Run GPU work serially only after admission.

The RGBA16 GPU oracle needs stricter precision than the existing RGB10 oracle:

- One UNORM16 code is `1/65535 = 1.5259021896696422e-5`.
- Error tolerance must be below half that gap,
  `7.629510948348211e-6`; use finite output checks and recommended absolute
  tolerance `1e-6` per channel.
- Explicitly require adjacent outputs to remain ordered with a gap at least
  `1/65535 - 2e-6`.
- Use `texelFetch` or nearest sampling to isolate adjacent values. Qualify
  filtering separately. Read into float32 or raw UNORM16 storage that preserves
  the distinction; half-float output does not preserve all adjacent sixteen-bit
  codes near the top of the unit interval.
- Exercise the actual buffer-texture resolver with 384x384/pitch 3072, then odd
  padded rows/nonzero offsets. Verify prefix, row-padding and tail guardbands.
  Include unsupported capability and short-allocation controls.

The RGB10 tolerance `2e-5` is invalid for this 16-bit adjacency oracle and must
not be reused. Full GPU/debt/runtime success and a bounded guest pathway remain
future parent validation; this patch alone establishes none of them.

The separate type 2 linear RGBA16 texture at 128x128/pitch 1024 with five mips is
out of scope and is not claimed fixed. The native buffer plan still refuses
five mips. MRT framebuffer fetch, dual-plane textures, aggregate loads, nested
buffer-texture views and artifact causality remain untouched and unclaimed.
