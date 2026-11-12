# metal2vulkan leading-vector prefix load, and the R10 Reims/QEMU build

## The failure
Boot `20261029T124845Z-vjqu894q` (R9 build) refused 10 fragment pipelines (115, 118, 128, 132, 154,
171, 183, 187, 190, 213; 195 skipped draws) with one translator error:

`cannot reinterpret load … from Local(…) with non-bitcastable pointee
Struct([Struct([Vector(Float, 4), Vector(Half, 4), Array(Int(8), 8)]), Array(Int(8), 32)]) to Vector(Half, 4)`

That is a `<4 x half>` read at offset 0 of a local union whose leading member is a `<4 x float>`:
bytes 0..8, the bits of float lanes 0 and 1. `emit_first_vector_aggregate_reinterpret_load` only
handled a result of the leading vector's own type or the same lane count.

## The fix (`prefix-load.patch`, sha256 `99a2a42f94a635b05adf8d5c48c0d6a98809788ac86aa51089e6bea0629c9447`)
- `src/native/emitter/body/mod.rs`: `leading_vector_prefix` returns `(k, <k x elem>)` when a
  numeric-vector result is exactly `k` whole lanes of the leading vector with `2 <= k < lanes`, and
  one `OpBitcast` can relate the prefix and the result (one component count divides the other).
  Bool lanes are excluded. One-lane results stay on the existing first-scalar path.
- `src/native/emitter/body/vector_store.rs`: the prefix case access-chains to the leading vector,
  loads it, `OpVectorShuffle`s lanes `0..k`, and `OpBitcast`s to the result unless the prefix already
  has its type. (R10 limited this to Function/Private storage; that blocked the guest's shader and
  R10b removes it, see below.) Direct and same-lane-count
  cases emit the same instructions in the same id order as before, so previously translating inputs
  are byte-identical.
- `src/native/tests/buffers.rs`: 5 tests, a narrower prefix as a complete kernel (structural chain
  plus spirv-val), a same-type prefix (no self-bitcast), a one-lane result kept on the scalar path,
  refusal of bytes outside the vector (past the vector, split lane, threadgroup), and the existing
  same-lane test.

## Evidence (receipts in `logs/`)
- RED: the new tests failed on pristine 9e0e99a with exactly the guest's error text (`red3-test-1`).
- GREEN on the final tree `green6`: `cargo fmt --all -- --check` clean, `cargo clippy --all-targets
  -- -D warnings` clean, `cargo test --no-fail-fast`: lib 1774/1776, all integration test targets
  green. The 2 failures (`owned_memory_check_matches_vulkan_validation`,
  `owned_pointer_check_matches_vulkan_validation`: "spirv-val must reject …") fail identically on
  pristine upstream (`base-owned-1`, 1772 tests, no overlay): this image's spirv-val accepts those
  invalid modules. Not caused by this change.
- A shared-target hazard was found and fixed in the harness: a pristine copy with old mtimes
  silently reused the previous variant's binaries (`base-test-nff` is therefore void); the runner now
  forces a rebuild when the variant changes.

## R10 build
- Source: R9 authority (1284 entries, sha256 `0ccafbb1…`) with exactly the three files above changed
  under `vendor/metal2vulkan-io/` (identical to 9e0e99a before the change). Manifests and lockfiles
  unchanged. Authority: `logs/r10-final-source.json`.
- `cargo build --release --locked --offline -p reims-vgpu` from a seeded copy of the R9 cache;
  metal2vulkan and reims_vgpu rebuilt (`fresh: false`).
- Artifacts (`/work/orchard-m27-pages-m2v-prefix/artifacts`, host copies in `artifacts/`):
  `libreims_vgpu.a` sha256 `24afefd96a49cb2b8a97910f5bfc44529375dd524e004309bd8df258197d5471`;
  `qemu-system-aarch64` sha256 `aec0032f7604b950a64ad552ae45e0d210b8f0c20d6e239b5c4943ceca00f052`,
  linked with the R9 link row with only the output and library arguments changed; `--version` QEMU
  11.1.50.
- Not run for R10: the R9 renderer qualification groups (Reims GPU tests). The change is confined to
  the translator, and previously translating shaders produce identical output; the boot comparison
  in `../r10-boot-test/` is the integration check.

## R10 boot result: the fix did not reach the guest's shader (corrected in R10b)
Boot `20261029T141852Z-igslwjqy` ran the R10 QEMU (`aec0032f…`, confirmed in validated-inputs) and
still logged the same 10 failures, byte-identical text. The cause was my own restriction: the
prefix case accepted only Function/Private storage, and a `Local("%N")` operand takes its storage
from its root, so a pointer into a constant buffer, device buffer or threadgroup memory was refused.
A new test reading the same union through a GEP'd constant-buffer pointer failed on the R10 code
with the guest's exact error text (`red5-test-1`). The existing `emit_narrowing_vector_load` already
over-reads a whole vector for every storage class and discards the extra lanes, so R10b follows
that convention and drops the restriction.

R10 boot by-products: pipelines ready 237 (R9: 129), first GPU work at 122.5 s on the vGPU clock
(R9: 130.3 s), 251 skipped draws (R9: 195; the guest drew more). Lavapipe threads were NOT 6: the
runner pins `LP_NUM_THREADS=2` for QEMU, so the launcher option never applied. The frames wrapper
now applies `LOCAL_RAW_LP_THREADS` to the emulator process only (3 new wrapper tests; 13 pass).

## R10b (`prefix-load-v2.patch`, sha256 `87966151ab69595a4024910a36e6b8b5ff76a99e5fe3d00bfbda9674551f304c`)
- Tests: 6 prefix tests (new: constant buffer, device buffer and threadgroup through a local GEP
  pointer, each a validated kernel; the threadgroup refusal case removed). `green7`: fmt and clippy
  clean, lib 1775/1777 with the same 2 pre-existing spirv-val failures, 19 other targets green.
- Build: `/work/orchard-m27-pages-m2v-prefix2` (seeded from the R10 cache), exactly the same three
  vendored files changed vs R9. `libreims_vgpu.a` `9fd226fd1849c6a3d76faccf456192eff12534da6739756d227e50f8b6cf15c9`,
  `qemu-system-aarch64` `99db7628328eb9c6f6d5dee7e491c80518c4d74fbb3a31c890b3fc02f47aff9a`
  (host copies in `artifacts-r10b/`). Boot profile `m27-pages-prefix2`.
