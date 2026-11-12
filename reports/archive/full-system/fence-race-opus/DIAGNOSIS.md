# Fence race in the Reims Vulkan engine — diagnosis

Scope: open-source Reims sources only (tested tree `/work/orchard-m27-pages-mrt-order/reims-vgpu`,
verified byte-identical to the R8 authority `mrt-memory-release-completion-r8/final-source.json`,
1283 entries, 0 differences — `logs/inspect-tested-source-tested-source-authority.json`).
All runs below are labelled diagnostics in owned scratch copies under
`/work/orchard-m27-pages-mrt-fence`, outside the official gate. File:line citations are
against the tested tree (copies in `source-view/`).

## Root cause (two sentences)

`ResourcePools::batch_flush` hands an ended batch to the queue-owner thread and returns before
that thread has even called `vkQueueSubmit(queue, info, batch.fence)`, but the pool keeps
using the same ring fence from the calling thread with nothing ordering those uses after the
owner's call. In `held-open-off`, the readback that joined the batch calls
`vkWaitForFences(batch.fence)` immediately after the handoff, so the drain-side wait is
already in progress when the owner enters `vkQueueSubmit` with that fence: two threads use
an externally synchronized fence at once.

## Is it real? Yes — the specification forbids it, the layer is not over-reporting

* `vkQueueSubmit` — Host Synchronization: "Host access to `fence` **must** be externally
  synchronized" (refpage `vkQueueSubmit`). `vkResetFences`: each member of `pFences` must be
  externally synchronized, and must not be associated with a queue command that has not
  completed (`VUID-vkResetFences-pFences-01123`). `vkDestroyFence`: `fence` is externally
  synchronized.
* `vkWaitForFences` and `vkGetFenceStatus` have no Host Synchronization section (they are not
  externally synchronized), but they access the fence object.
* Fundamentals → Threading Behavior: when two commands access the same object and at least
  one declares it externally synchronized, the caller must guarantee that the commands do not
  execute simultaneously (and are separated by a memory barrier if needed); an implementation
  may update an externally synchronized object's state at any time during the command.

So `vkWaitForFences(F)` on thread A overlapping `vkQueueSubmit(.., F)` on thread B is a
specification violation, independent of any layer. The Khronos layer models exactly this rule
(VVL 1.4.309 generated `thread_safety.cpp`: `vkQueueSubmit` `StartWriteObject(fence)` in
PreCallRecord / `FinishWriteObject` in PostCallRecord; `vkWaitForFences` and
`vkGetFenceStatus` `StartReadObject`; `vkResetFences` and `vkDestroyFence` `StartWriteObject`;
`Counter::StartWrite` logs `UNASSIGNED-Threading-MultipleThreads-Write` when a reader or
writer from another recorded thread is present). The report is therefore a true positive.
The observed impact on Lavapipe was only the report (pixels correct in every run), but the
spec gives a driver licence to update fence state mid-call, so a concurrent wait/status/reset
may observe a torn state; a reset that lands while a driver that signals inside the call is
still returning is the more dangerous form (see the retire path below).

## The exact colliding pair and threads

| | thread (name / role) | call | engine site |
|---|---|---|---|
| first, holds the fence as a **reader** | libtest case thread `backend::vulkan::engine::r3_qualification::r3_actual_engine_case` (the engine caller; the drain worker in a VM) | `vkWaitForFences(&[F], true, 5 s)` | `ResourcePools::wait_entry_fence`, `pools/submission_and_buffers.rs:2153-2155` |
| second, takes the fence as a **writer**; the layer reports here ("current thread") | `reims-vgpu-submit` (queue owner) | `vkQueueSubmit(queue, &[info], F)` | `queue_owner::execute_submit`, `queue_owner.rs:469` |

`F` = `VkFence 0x80000000008`: the fence of ring slot 1, created in `ensure_init`
(`pools/submission_and_buffers.rs:696-713`) and the batch slot of this case (traced
`batch_flush slot=1`). It is the same handle as in R8.

## Evidence (diagnostic runs, strict R8 test envelope)

All under the R8 test envelope: image `13d68aa0…`, 2 CPU, 2 GiB, pids 128, network none,
read-only root, init, log none, core 0, tmp 64 MiB; Runtime26/LLVM21 Lavapipe from
`orchard-build/golden/runtime-26`; validation bundle `mrt-fetch-validation-layer-v2`
(`VK_LAYER_KHRONOS_validation`, `vk_layer_settings.txt` = Core + SYNC); the R8 `gpu_env`
variables verbatim; `r3_actual_engine_case --test-threads=1 --nocapture`, `R3_CASE=held-open-off`.
Host guard read through `host-space-io/Read-HostSpaceSample.ps1` on every 0.2 s poll
(`scripts/Launch-Fence.ps1`, `scripts/fence_run.py`).

1. **Unmodified tested source, 50 runs** (`logs/test-baseline-held-open-50-test.json`, binary
   sha256 `a8da824e…`): **50/50** runs carry exactly one validation error,
   `UNASSIGNED-Threading-MultipleThreads-Write`, reported from `vkQueueSubmit()` on
   `VkFence 0x80000000008`; 0 VUIDs, 0 SYNC hazards; Rust `ok`, pixel oracle and all case
   markers pass in 50/50. The defect is not rare: it is deterministic in this envelope; R8
   simply ran this case once. Uninstrumented owner pickup (`queue_async_queue_us`) median
   40.5 µs (25–637), owner `vkQueueSubmit` (`queue_async_driver_us`) median 2.58 ms.
2. **Instrumented scratch copy, 40 + 5 runs** (`overlays/instrumented/`,
   `logs/test-instrumented-held-open-40-test.json`, `…-trace-analysis.json`): every fence call
   and the handoff logged with pthread id (the id the layer prints), thread name and a
   monotonic timestamp. In **40/40** held-open-off runs the layer's "current thread" is
   `reims-vgpu-submit` and the "other thread" is the case thread, and the only overlapping
   pair is `vkWaitForFences` (`site=wait_entry_fence`, case thread) followed by
   `vkQueueSubmit` (`site=queue_owner`, `reims-vgpu-submit`). Relative to the handoff
   (medians, with tracing overhead): owner dequeue 404 µs, drain enters `vkWaitForFences`
   735 µs, owner enters `vkQueueSubmit` 1094 µs, owner returns 4251 µs, wait returns 38.6 ms.
   The wait entered first in 40/40 and was still blocked when the submit returned in 40/40.
   `primary-off` (5 runs, synchronous submits only): 0 reports.
3. R8 logs: only `green-extra-default-held-open-off-off` shows `queue_async_submits > 0`
   (`batch_readback_joins: 1`); no other R8 group printed an async submission. The case was
   first executed in R8, which is why no earlier round saw it. The R7 test-only
   `recycle_readback` line is unrelated (the baseline above reproduces with the exact R8 tree).

Why it is deterministic here: after the handoff the drain thread needs only `seal_entry`,
`finish_entry_async` and a phase note to reach `vkWaitForFences`, whose layer PreCallRecord
registers the read at once and then blocks until the GPU finishes. The owner must first be
woken, and the layer then runs the whole `vkQueueSubmit` PreCallValidate (Core + SYNC) before
its PreCallRecord registers the write. The reader is therefore always first and always still
present.

## Control flow in `held-open-off`

`r3-qualification.rs:71-78`: two `execute_draw_request` calls with `skip_readback = true`,
`render_pass_continues = true`, then `read_target`.

1. Draw 1 → `exec::execute_draw_inner`: batch-eligible, so `begin_entry`
   (`pools/submission_and_buffers.rs:1555`) claims slot 1 and the draw defers its submit
   (`exec.rs:5623`, `5838-5875`): `batch_append` opens the batch (`batch_opens: 1`).
2. Draw 2 joins the open batch (`exec.rs:2972-2973`, `batch_joins: 1`) and defers again.
3. `read_target` (`mod.rs:5570`) → `read_target_inner` (`mod.rs:5528`) →
   `copy_image_level0_to_host` (`mod.rs:3053`) → `copy_image_level0_to_host_delivered`
   (`mod.rs:3097`): a batch is recording, so the copy appends to it
   (`mod.rs:3150-3156`, `batch_readback_joins: 1`) and takes the batch's `(cb, fence)`.
4. `pools.batch_flush(ctx, counters)` (`mod.rs:3289`) → `batch_flush_inner`
   (`pools/submission_and_buffers.rs:2047`) → `ctx.submit_guest_work_async(&cbs, batch.fence)`
   (`:2084`) → `DeviceContext::submit_guest_work_async` (`context.rs:1711-1724`) →
   `QueueOwner::submit_async` (`queue_owner.rs:191-221`), which only sends the request and
   publishes the queued timeline point, then returns `Ok(())`.
5. Back on the case thread: `seal_entry` + `finish_entry_async` mark slot 1 pending, then
   `pools.wait_entry_fence(ctx, counters, fence)` (`mod.rs:3310`) →
   `ctx.device.wait_for_fences(&[fence], …)` (`pools/submission_and_buffers.rs:2153-2155`).
   **No happens-before exists between this call and the owner's `vkQueueSubmit`.**
6. Owner thread `reims-vgpu-submit`: `run` (`queue_owner.rs:332`, `Submit` arm `341-366`) →
   `execute_submit` (`:449`) → `device.queue_submit(queue, &[info], submit.fence)` (`:469`):
   the layer finds the case thread's read and reports
   `vkQueueSubmit(): THREADING ERROR : object of type VkFence is simultaneously used in current
   thread <reims-vgpu-submit> and thread <case thread>`.
7. The wait returns when the GPU finishes; the test reads correct pixels; teardown
   (`r3-qualification.rs:38-46`) idles the queue through the owner before `destroy_all`, so
   it is clean.

## Other paths sharing the hazard

The invariant that is missing: *a ring fence handed to `submit_async` may not be waited,
queried, reset or destroyed by another thread until the owner has returned from the
`vkQueueSubmit` that took it.* Every `batch_flush` is such a handoff; the fence accessors
that can follow it are all in `ResourcePools`:

| path | handoff then fence access | status |
|---|---|---|
| readback joined to a batch: `read_target` and `read_target_leased` (`mod.rs:3053`, `3543-3571` → `3289`, `3310`) | `batch_flush` → `wait_entry_fence` → `vkWaitForFences` | **observed** (this case, 50/50) |
| quiesce before completion stamps / host access (`quiesce_guest_writes` `:3009`, `quiesce_guest_reads` `:3044`, entry `mod.rs:1734`), compute (`exec_compute.rs:1451`), memoryless (`memoryless.rs:48`), test hook `test_quiesce_ring` (`mod.rs:5772-5783`) → `retire_all` (`:3064-3082`) | `batch_flush` (`:3071`) → `retire_slot` → `vkWaitForFences` (`:1466-1487`) then `vkResetFences` (`:1488-1490`) on the batch's fence | the wait collision is reproduced deterministically by the new red test (red3: 10/10, `vkQueueSubmit` `MultipleThreads-Write`, VERIFY.md); the reset racing the tail of `vkQueueSubmit` was not observed on Lavapipe (its fence signals ~35 ms after the call returns) and rests on the specification argument above |
| `begin_entry` (`:1555-1608`), every slot claim | `batch_flush` (`:1564`) → `retire_signaled_slots` (`:1587-1589`) → `vkGetFenceStatus` (`:1524-1527`) on each pending slot, reaching the just-handed-off slot once older ones retire; then `vkGetFenceStatus(next)` (`:1595-1600`) and `retire_slot(next)` (`:1601`) when the owner lags a full ring | static analysis; same class (read during the write) |
| maintenance heartbeat `advance_graveyard_maintenance` (`:621-641`) | `batch_flush` (`:626`) → `retire_signaled_slots` → `vkGetFenceStatus` | static analysis |
| guest-page Store `copy_image_level0_to_buffer` (`mod.rs:4705`, `4793`), end-of-tranche `flush_batched_draws_with` (`mod.rs:1415-1445`), completion-stamp flushes `write_completion_stamp` (`mod.rs:1883-1915`) and `submit_batch_for_waiting_stamp` (`mod.rs:1953-1972`) | handoff only (the stamp then waits the timeline semaphore); the later fence access is one of the rows above | covered by those rows |
| draw tails `exec.rs:5934`, `5966`; compute `exec_compute.rs:1384`; non-joined readback (`mod.rs:3296`) | synchronous submits (`submit_sync` / `submit_sync_ordered` reply only after `vkQueueSubmit` returned, `queue_owner.rs:153-189`, `223-245`) | not affected |
| host-window present (`window_present.rs:1380-1391` → `enqueue_present`) | presenter fence; the window thread waits `PendingPresent::wait` (`mod.rs:1288`) before it next queries (`window_present.rs:853-868`, `882-896`) or resets (`:1213-1216`) that fence; the drain never touches it | not affected while one thread presents |
| teardown `destroy_all` (`pools/teardown.rs:27-35`, `241-243`) | every caller drains the owner first: `flush_device_derived` `queue_barrier` (`mod.rs:407`), `reset_guest_state` `queue_wait_idle` (`mod.rs:1092-1122`), test hook `test_reset_engine_with` (`mod.rs:5741-5747`), `r3-qualification.rs:42` | not affected; it is the function's stated precondition (`teardown.rs:51-64`) |
| stamp completion thread | waits a timeline semaphore, never a ring fence (`stamp_completion.rs:39-52`) | not affected |

## What the fix must preserve

Guest-visible order is the queue-owner FIFO and must not change; completion is still the
fence (and the timeline for stamps); no wait may become unbounded (a stalled owner or a lost
device must still surface as `FenceTimeout` / `DeviceLost`); teardown must still release
everything. See DESIGN.md.
