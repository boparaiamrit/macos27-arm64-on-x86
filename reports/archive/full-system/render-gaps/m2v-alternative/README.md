# Unshipped metal2vulkan variant (not in R11)

Written before the parent's R10b was known, for the same failure: R10's prefix load
(`emit_first_vector_aggregate_reinterpret_load`) refused every storage class but Function/Private,
so a `<4 x half>` read of a `{ { <4 x float>, … }, … }` union reached through a local pointer into a
buffer or threadgroup memory still fell back with the guest's exact error.

R10b (shipped, what R11 is built on) drops the restriction and loads the whole leading vector in
every storage class, following `emit_narrowing_vector_load`'s existing over-read convention.

This variant instead keeps the whole-vector load for invocation-private storage and, for shared
storage, loads each kept lane through its own component access chain and assembles the prefix with
`OpCompositeConstruct` — reading exactly the bytes the source load reads. Files (bases are R10's
vendored copies): `vendor/metal2vulkan-io/src/native/emitter/body/vector_store.rs`,
`vendor/metal2vulkan-io/src/native/tests/buffers.rs` (new test
`native_leading_vector_aggregate_load_reads_shared_prefix_lane_by_lane`; the R10 threadgroup refusal
case moved into it). Not compiled or run: its first RED run was stopped when R10b appeared.
