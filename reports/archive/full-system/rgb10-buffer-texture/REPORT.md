# RGB10A2 buffer-texture source handoff

Implemented a narrow native RGB10A2 opcode-9 upload path in the existing dirty
`reims-study` tree. This is a source patch with GPU-free helper verification;
it is **not** a compiled emulator, Vulkan execution result, guest rendering fix,
or evidence about missing buttons/border artifacts.

## Changed owner files

- `runtime/draw/buffer_texture.rs`: private native storage plan, typed refusals,
  source-allocation/address checks, tight row gathering and byte-format result.
- `runtime/draw/buffer_texture_tests.rs`: ten owner regression tests.
- `runtime/draw/mod.rs`: gated helper module declaration only.
- `runtime/draw/vulkan.rs`: native-aware opcode-9 upload resolver, preserving
  the existing RGBA8 loader for every other pixel-format ordinal.

Only format `MTL_FORMAT_RGB10A2_UNORM` (0x5a) selects the new owner. It retains
the four-byte packed words and returns `SampledByteFormat` with
`TexelLayout::Rgb10a2Unorm` and the original RGB10A2 source format. The existing
Vulkan rail already maps this layout to `A2B10G10R10_UNORM_PACK32`; that owner
was read, not edited. No RowToRgba8 whitelist change or quantization was added.

The production resolver asks the existing
`engine::supports_sampled_layout_bind(Rgb10a2Unorm)` door only for this native
format. Unit tests inject that door's answer and never initialize Vulkan.
A declined host bind is a typed, fail-visible refusal, without RGBA8 fallback.

The native byte request represents one 2D, single-depth, single-array-element,
single-sample, single-mip texture. Other shapes and present descriptor swizzles
are typed refusals; this patch does not invent their semantics. Other formats
continue through the existing loader unchanged, including its historical
format-zero fallback and bounds behavior.

The native row span comes from the existing `TextureLevelLayout::read_span`:
`(height - 1) * bytes_per_row + tight_row_bytes`. It excludes final trailing
padding. Offset+span, allocation limits, guest-address addition, row pitch,
row-span overflow and host allocation addressability are checked before reading.
Only this exact source span is requested from the existing buffer reader.

The native runtime path pays the bound texture-reference debt before source
resolution, then uses the existing `read_buffer_bytes_resolved` buffer
census/pay/settle transaction. The resulting Vec/Arc owns its upload bytes
after the guest source can be released. No resource eviction, plane selection,
residency rule, other refusal class, external translator, VM or source cache
was changed. Debt preservation is source-reviewed here; actual ledger/engine
integration still requires the parent build and affected runtime checks.

## Executed verification

The parent admitted only small, GPU-free Rust execution, with <20 MiB owned
output, a 120-second per-command limit, a 2 MiB per-log limit and a fresh
unconditional 10 GiB C: free-space guard. `run_helper_tests.py` samples the
guard every 0.2 seconds while each compiler/test command runs and kills the
child on a guard, time, log or output bound breach.

Native Windows toolchain: `rustc 1.99.0 (b940084d7 2026-09-28)`.
Minimum sampled C: free was 12,202,950,656 bytes; maximum sample interval was
0.205 seconds. Frozen outputs are approximately 11.2 MB, below 20 MiB.
See exact receipts and hashes in the JSON files.

1. **RED before production edits**: compiled the exact old
   `load_buffer_texture_rgba` source verbatim, with minimal memory/debt adapters,
   using actual production pixel-format/endian/extent source and verbatim
   descriptor/TextureLevelLayout definitions. The 106x106, pitch512 native-word
   test failed at the intended `buftex convert_unsupported fmt=0x5a` guard:
   test exit101, 0 passed/1 failed. The initial harness compile had an ambiguous
   integer type; its diagnostic/receipt is preserved separately, then the
   fixture annotation was corrected before the meaningful RED execution.
2. **GREEN**: compiled the real new helper via `#[path]`, including its real
   owner test file, against those production types and the existing
   `host_alloc_len` source. **11 tests passed**: ten helper tests and an additional
   old-loader BGRA8 offset/padded-row conversion regression. After formatting
   and adding the host-addressability edge case, the same 11 tests passed again.
3. `rustfmt --edition 2021 --config skip_children=true --check` passed for all
   four changed owner files. Children were excluded to preserve unrelated
   existing dirty files.
4. `git diff --check -- <mod.rs> <vulkan.rs>` passed. The helper/test files were
   also formatted and contain no trailing whitespace.
5. The verbatim old RGBA8 loader hash is identical before and after:
   `b22eac9d4d2a5f2ec4c6d96412e7378d5908a592ecdf7648bc4b261866a14a32`.

The GREEN tests cover adjacent ten-bit component values that cannot both
survive unorm8 quantization; 106x106 geometry with pitch512; row padding and
last-row bounds; exact/short source allocation; nonzero buffer offset;
offset/address/row-span/tight-row/host-length overflow; tight-default pitch;
host refusal; unsupported shape/swizzle refusal; other-format route selection;
owned output after source release; and unique typed-refusal slugs.

These prove the helper contract and unchanged old row converter through an
adapted boundary. They do not compile the entire runtime module or execute its
device state, actual debt ledger, Vulkan format implementation or shaders.

## Frozen review inputs

- `owner.patch`: exact task delta against the initial already-dirty owner files;
  additions include both new source files. No baseline reset was used.
- `frozen-owner-files/`: exact resulting four files for a parent-owned builder
  overlay. Preserve the rest of the parent's prepared source baseline.
- `owner-sha256.json`: before/after file hashes and patch hash.
- `red-provenance.json`, `green-provenance.json`: executed source/harness hashes.
- `*-tests.log`, `*-test-build.log`, matching JSON: commands, exits and guards.
- `verification-summary.json`: guard floor/interval and unchanged-loader proof.

## Proposed parent checks, not executed

Under a separately admitted RAM target, debug=0, jobs=1 resource envelope and
fresh disk guard, compile the full current runtime against the frozen admitted
translator source, then run:

```text
cargo test -p reims-vgpu --no-default-features --features backend-vulkan --lib runtime::draw::buffer_texture::tests -- --test-threads=1
```

Run the existing buffer-read and buffer-backed-texture debt regressions,
affected draw tests and applicable feature/format gates. Add or execute an
actual native-path debt fixture through the runtime; the helper test's owned
Vec proof alone is not a ledger or GPU-completion lifetime test.

The GPU oracle must exercise the actual opcode-9/native upload resolver and
sample/read back raw packed ten-bit words, with red values 1 and 2, unequal
R/G/B fields, and alpha values 1 and 3. Use a 106x106 image, pitch512, nonzero
buffer offset, guard bytes before the source, row padding and tail guardbands.
Read exact pixel-center samples into a float or ten-bit target that can
distinguish 1/1023 from 2/1023; verify values, channel order and alpha, and
verify all source/row/tail guards remain unchanged. Include unsupported host
capability and short-allocation refusal controls. Execute GPU tests serially.

Only after full build/format/GPU checks and explicit resource admission should
a new emulator be produced and the bounded relevant guest pathway run. Compare
the specific RGB10A2 refusal population; no missing-button/border causality is
claimed. Secondary framebuffer fetch, type12 dual-plane formats, nested
buffer-texture views and aggregate-load translation failures remain out of scope.
