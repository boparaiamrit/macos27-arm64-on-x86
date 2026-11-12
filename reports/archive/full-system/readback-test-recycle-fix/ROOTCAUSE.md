# R7 blocker root cause: the test never recycles its second readback slot

R7 stopped on two `VUID-vkDestroyDevice-device-05137` events (one live VkBuffer, one live
VkDeviceMemory) in `staging_mapping_tests::a_leased_readback_slot_leaves_the_pool_and_comes_back`.
The child's ROOTCAUSE.md gave the mechanism and left the ownership contract to the parent.
Parent decision, from the unchanged source:

## Contract

`acquire_readback` (pools/submission_and_buffers.rs) **replaces** `readback_live`: both its
free-list branch and its create branch end in `self.readback_live = Some(slot)`. Nothing moves
the previous live slot anywhere. `recycle_readback` is the call that moves the live slot (and
`readback_multi_live`) to the free list, and `destroy_all`/teardown frees only slots held by
free, live, multi-live or leased owners. So the contract is: **recycle between acquires**.
`acquire_readback_extra`, documented "without replacing the primary live slot", is the call for
holding a second one. The only production caller is `exec.rs:4314`, one acquire per readback.

## The test breaks the contract

1. `slot = acquire` (live = A); `lease_readback` takes A out of `live` into `leased`.
2. `other = acquire` (live = B, a new buffer; A is leased, so the free list is empty).
3. `return_readback_lease` + `reclaim` put A on the free list.
4. `back = acquire` pops A and sets live = A, **replacing B**. B is now in no owner.
5. `recycle_readback` frees A's entry to the list; `destroy_all` frees A. B leaks.

The native layer reports exactly one buffer and one memory object alive at `vkDestroyDevice`,
which is B. No SYNC hazards, and no production caller is implicated.

## Correction (test-only, one statement)

Add `pools.recycle_readback();` right after the exclusivity assertion on `other`, so B joins the
free list before A is returned. Free list is then [B, A]; `back` pops A (== `slot`), the existing
assertion `back.buffer == slot.buffer || back.buffer == other.buffer` still holds, `other` is
still asserted distinct from the leased slot, and teardown now owns both buffers. No assertion
is weakened or removed. Production source is not changed (`pools/mod.rs` before-hash equals the
frozen production pin `fcafe529...`; only its `#[cfg(test)]` module differs).

Hardening `acquire_readback` against replacing a live slot (for example a debug assertion) is a
separate production decision and is deliberately not part of this round.
