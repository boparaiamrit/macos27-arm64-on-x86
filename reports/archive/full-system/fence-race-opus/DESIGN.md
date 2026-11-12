# Fence race — fix options and recommendation

The invariant to restore (DIAGNOSIS.md): *a ring fence handed to the queue owner by
`batch_flush` may not be waited, queried, reset or destroyed by another thread until the
owner has returned from the `vkQueueSubmit` that took it.* Constraints: guest-visible
ordering and completion semantics unchanged; no deadlock when the owner stalls or the device
is lost; teardown still releases everything; no measurable hot-path cost; owner-level, no
call-site flags (repo `AGENTS.md`).

## Option A — per-submission host-return handoff, settled by the owner (recommended, implemented)

* **Base layer, `crates/reims-vgpu-core/src/handoff.rs` (new module).** The primitive is
  backend-neutral, so it lives in the semantic-model crate, which names no host object and
  whose dependency list stays exactly `reims-vgpu-protocol` (its own boundary test checks
  that): `Handoff::lend() -> (Handoff, HandBack)`; `Handoff::state()` (never blocks) and
  `Handoff::wait(deadline)` answer `HostCall::{Outstanding, Returned, Abandoned}`;
  `HandBack::returned()` settles once; dropping a `HandBack` unsettled is `Abandoned`;
  `Handoff::RETURNED` is the allocation-free "nothing outstanding". `Mutex` + `Condvar`,
  `#![forbid(unsafe_code)]`-clean. Its own unit tests pin outstanding-until-handed-back,
  cross-thread wake, the deadline, abandonment on drop, settle-once and identity.
* **Queue owner (`queue_owner.rs`).** `QueueOwner::submit_async` lends the fence and returns
  the `Handoff`; the request carries the `HandBack`. The owner settles it in `finish_submit`,
  *after* the driver call, the timeline note, the statistics and the failure latch — so a
  thread that sees the fence returned also sees whether the call failed. A latched failure
  that makes the owner skip the driver call still settles `Returned`; a request discarded
  with a dead owner thread is `Abandoned`. Synchronous rails need nothing (their reply
  already follows the call).
* **Fence owner (`pools`).** The handoff is stored with the fence it governs
  (`CmdSlot.handoff`) when `batch_flush_inner` hands the batch off, and reset to
  `Handoff::RETURNED` when the slot retires. The engine maps the neutral outcome to its own
  vocabulary at this boundary, and every ring access to a slot fence goes through one of two
  `ResourcePools` methods:
  * `await_slot_handoff` (blocking; bounded by `FENCE_TIMEOUT_NS`, the deadline of the fence
    wait it precedes; `Outstanding` at the deadline → `FenceTimeout` + always-on
    `vk_engine_submit_wedged` line, `Abandoned` → `DeviceLost`; then re-checks the failure
    latch) — before `vkWaitForFences` in `retire_slot` (hence before `vkResetFences`) and
    `wait_entry_fence`;
  * `slot_fence_signaled` (non-blocking) — answers `false` without calling
    `vkGetFenceStatus` while the handoff is outstanding; used by `retire_signaled_slots`
    and `begin_entry`.
* `context.rs`: `submit_guest_work_async` passes the handoff through (the no-owner fallback
  returns `Handoff::RETURNED`).
* **Test instrument at the bottom of the stack (`context.rs`, `cfg(test)` only).** A test
  build enables `VK_EXT_debug_utils` when the loader offers it (`DeviceContext::debug_utils`)
  and does nothing else with it. A test that needs to *fail* on a validation report holds a
  `validation_capture::Listening` for its own length: a messenger on the context's instance
  whose callback records every error-severity report (`id`, text, object handles) and
  re-emits it to stdout in the layer's own `Validation Error: [ id ] | MessageID = 0x…`
  format, because VVL 1.4.309 stops its default stdout logging while any application
  messenger is registered (its default `report_flags` is `error`, so the messenger listens to
  exactly that severity). The callback returns `VK_FALSE` (no call is skipped) and cannot
  unwind across FFI. Every other test runs with no messenger, so the gate's view of every
  other case is unchanged; non-test builds (the QEMU staticlib, `vk_engine_parity`) compile
  none of it.
  *Rejected v2 of this instrument:* installing the messenger in every test
  `DeviceContext` (global capture) silenced the layer's stdout for the whole lib test
  binary — the R9 gate would have gone blind. It was observed (red2 runs: reports captured,
  none printed), stopped, and replaced; its runs are not counted as API-clean evidence.

Trade-offs: exact (waits for the one call that owns the fence, not for unrelated FIFO work
such as a present blocked in `vkQueuePresentKHR`); the heartbeat stays non-blocking and keeps
its in-order `break`; no channel round trip; no caller outside the owners changes (the
readback, Store, draw and compute rails are untouched). Cost: one small `Arc` per batch
flush and one mutex/condvar settle on the owner thread per async submit; one uncontended
mutex check per slot-fence access (≤ 8 per `begin_entry`). The readback that joined a batch
now blocks on the condvar until the owner returns instead of blocking inside
`vkWaitForFences`; the fence cannot signal before it is submitted, so this adds at most the
tail of the driver call on a driver that signals inside `vkQueueSubmit`.

## Option B — `queue_barrier()` before every fence access after a handoff

Reuse the existing FIFO barrier (`QueueOwner::barrier`) in `wait_entry_fence` and the retire
paths. Smallest diff for the observed path (one line), but: the barrier waits for *every*
earlier request, including another thread's present transaction, adding display latency to
a guest-blocking readback; it costs an owner wake-up and round trip on every access, also on
the hot `begin_entry`/heartbeat paths, unless per-slot "was async" state is added — which is
Option A without its precision; it cannot be used on the non-blocking heartbeat without
making it block; and it does not order the failure latch before the fence access.

## Option C — wait the timeline semaphore instead of the fence

Readbacks could wait the batch's timeline point with `vkWaitSemaphores` (not externally
synchronized; wait-before-signal is legal for timeline semaphores), never touching the
fence. But the timeline is optional (`stamp_completion` is gated on `timelineSemaphore`), so
the fallback still needs A or B; it does not cover the ring's own `vkGetFenceStatus` /
`vkResetFences` — a semaphore reaching its value does not mean the host call has returned
(a driver may signal inside `vkQueueSubmit`), so retire could still reset a fence the owner is
inside; and it changes the completion source of the guest-visible readback, which would need
its own correctness argument.

## Option D — serialize all fence access through the queue owner

Add WaitFence / ResetFence / FenceStatus requests executed on the owner. No cross-thread
fence use at all, but a blocking wait on the owner stalls every later queue operation
(presents, other threads' submits) for the GPU's duration, which defeats the asynchronous
owner; every status poll pays a round trip; and a wait queued ahead of the work it depends on
deadlocks. Rejected.

(Moving the reset onto the owner, immediately before the next submit, only removes the
reset/submit overlap; the wait/status overlap that was observed remains. Not sufficient.)

## Recommendation: Option A

Why it meets each constraint:

* **Ordering/completion unchanged.** The FIFO, the timeline reservation/queued/submitted
  notes, the fence lifecycle (created unsignalled, waited, reset at retire) and every
  caller are unchanged; the handoff only delays the start of a fence access until the call
  that owns the fence is over. Stamps still use the timeline.
* **No deadlock.** All waits are bounded by `FENCE_TIMEOUT_NS` and report like a wedged
  fence; a lost device returns from the call and is seen through the failure latch before
  the fence is touched; a dead owner abandons its requests (immediate `DeviceLost`). The
  latch mutex is a leaf lock; the owner thread never takes the engine lock, so the drain
  holding the engine lock while it waits on the latch cannot form a cycle. A failed async
  submit no longer leads to a 5 s wait on a fence that was never submitted (it did before).
* **Teardown unchanged.** `pools/teardown.rs` is not modified: every `destroy_all` caller
  already drains the owner (`queue_barrier` / `queue_wait_idle`) first, which also settles
  every handoff, and the slots and fences are destroyed exactly as before.
* **Hot path.** Measured in VERIFY.md (per-run `batch_flush_submit_us`,
  `queue_async_queue_us`, `queue_async_driver_us`, test durations before and after).

Risk: low. The production change is confined to the two owners (`QueueOwner`,
`ResourcePools`) plus the new backend-neutral primitive in core; no caller of
`batch_flush`/`wait_entry_fence`/`retire_all` changes. The remaining risk is a future second
asynchronous handoff that bypasses `CmdSlot.handoff`; today `batch_flush_inner` is the only
caller of `submit_guest_work_async`, and the return type now carries the handoff, so a new
caller has to decide what to do with it. The host-window presenter's fences are a separate,
still-sound arrangement (the window thread waits `PendingPresent` before it touches its own
fence again); it would need the same treatment if a second thread ever presented. The
blocking paths now wait up to `FENCE_TIMEOUT_NS` for the handoff and then up to
`FENCE_TIMEOUT_NS` for the fence, so a pathologically stalled owner reports after at most
10 s instead of 5 s — still bounded, through the same `FenceTimeout`. Enabling
`VK_EXT_debug_utils` changes the instance of *test* builds only.

Tests that pin it (owner level, `cfg(test)`):

* `reims_vgpu_core::handoff::tests` (pure) — outstanding until handed back; a waiter on
  another thread wakes; a stalled borrower is still outstanding at the deadline; a dropped
  `HandBack` abandons the call at once; settle-once; `RETURNED` and identity.
* `queue_owner::tests` (pure) — an async fence is lent until the owner's `finish_submit`;
  a failure is latched before the fence is handed back; a submission the owner never
  reached is abandoned.
* `pools::submission_and_buffers::ring_fence_handoff_tests` (real device, multithreaded) —
  a test-only `QueueOwner::hold` parks the owner so the handoff is still in its FIFO when the
  drain side reaches the fence, and a third thread releases it 200 ms later: (1) the joined
  readback path (`batch_flush` → `wait_entry_fence`), (2) the quiesce path (`retire_all` →
  wait + reset). Each listens for the layer for its own length and asserts, in Rust, that no
  `UNASSIGNED-Threading-*` report names the batch fence (and that listening is live
  wherever the layer is mapped), that the owner was back from `vkQueueSubmit` before the
  wait returned, and that the batch retired. On the unfixed engine the threading layer
  reports deterministically, the report is printed for the gate, and the Rust assertion
  fails; on the fixed engine both pass.
