# R7 blocker: live native readback buffer at explicit device destruction

The guarded fresh compile passed. The 12 owner tests, four primary-load/sampled-upload
fallback cases, separate buffer-parent ownership control, six memory controls, two mixed
policies, 32 pure invocations and 237 baseline regressions completed successfully.

Qualification stopped in the resource-pools filter. Rust reported 169 passed, zero failed
and zero ignored, but its native stdout contains two actual validation error events:
`VUID-vkDestroyDevice-device-05137`. During
`staging_mapping_tests::a_leased_readback_slot_leaves_the_pool_and_comes_back`, device
destruction still owns VkBuffer `0x220000000022` and VkDeviceMemory `0x230000000023`.
There are zero SYNC hazards. Four classified error lines include the two duplicated spec
references; the actual validation error-event count is two. Both streams were classified
before accepting Rust status, so this invocation and resource group are not API-qualified.

The exact unchanged source explains an ownership-loss sequence. In pools/mod.rs,
the test acquires and leases A, then acquires B at line 4329. After returning/reclaiming A
(4336-4344), it calls acquire_readback again at 4345 without recycling or leasing B.
The free-list branch in submission_and_buffers.rs:3714-3717 pops A and assigns
readback_live=Some(A), replacing B. recycle_readback only moves the then-current live
slot to the free list (3801-3805); teardown drains recorded free/live/multi-live/leased
slots (teardown.rs:82-122). The overwritten slot is no longer in those owners.
The single native buffer/memory pair left live agrees with this sequence. The run did
not instrument per-acquire handle correspondence and establishes no unrelated production
caller failure. Parent review must decide the ownership contract and any correction;
this test task made no correction or production semantic change.

The resource filter's earlier slab 22 and buffer-slab 6 tests are API-clean. Its trailing
host-import and linear-import filters were not run; the exact owner 12 filter had passed
separately. The engine 5+5 and both extended GPU groups remain unrun. No aggregate
all-green receipt, release metadata/staticlib build, QEMU link or publication occurred.
No test retry or waiver followed. The invalid R6 fixture and old production-01443 RED
were not repeated, and all R6 evidence remains frozen.

The new fallback cases did complete their actual pixels, mapped Core+SYNC, native buffer
aliases, parent terminal free, balanced alias release and explicit device destruction.
Those successes remain separate from this later resource failure. Imported-image
preservation still declines with preserved_contents_unimplemented; that is a missing
initialization contract and is neither imported-image qualification nor unsupported hardware.

See blocker-source-and-native-proof.json for exact source hashes/ranges, native messages,
declared counts and retained log hashes. Final read-only preservation, original host
identity checks and owned cleanup completed without retry. No VM or GUI claim.
