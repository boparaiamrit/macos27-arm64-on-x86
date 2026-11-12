| case (R3_CASE, probe) | before: runs with a validation error | before: Rust ok | after: runs with a validation error | after: Rust ok | after: oracle failures |
|---|---|---|---|---|---|
| held-open-off | 50/50 (vkQueueSubmit 50) | 50/50 | 0/50 | 50/50 | 0 |
| clear-refusal-on | 0/20 | 20/20 | 0/20 | 20/20 | 0 |
| depth-refusal-eight-on | 0/20 | 20/20 | 0/20 | 20/20 | 0 |
| depth-stencil-refusal-on | 0/20 | 20/20 | 0/20 | 20/20 | 0 |
| dontcare-refusal-on | 0/20 | 20/20 | 0/20 | 20/20 | 0 |
| feedback-refusal-on | 0/20 | 20/20 | 0/20 | 20/20 | 0 |
| msaa-refusal-on | 0/20 | 20/20 | 0/20 | 20/20 | 0 |
| narrow-held-open-off | 30/30 (vkQueueSubmit 30) | 30/30 | 0/30 | 30/30 | 0 |
| primary-off | 0/20 | 20/20 | 0/20 | 20/20 | 0 |
| primary-on | 0/20 | 20/20 | 0/20 | 20/20 | 0 |
| resident-depth-refusal-on | 0/20 | 20/20 | 0/20 | 20/20 | 0 |
| secondary-clear-refusal-on | 0/20 | 20/20 | 0/20 | 20/20 | 0 |
| secondary-load-refusal-on | 0/20 | 20/20 | 0/20 | 20/20 | 0 |

**red3 (unfixed engine + test seams + new tests)**

| group | invocations | Rust ok | tests per invocation | runs with a validation error (stdout/stderr) | VUIDs | SYNC |
|---|---|---|---|---|---|---|
| ring-fence-handoff | 10 | 0 | 0 passed / 2 failed | 10/10 (vkQueueSubmit 20) | - | - |
| queue-owner | 1 | 1 | 8 passed / 0 failed | 0/1 | - | - |
| held-open-off | 20 | 20 | 1 passed / 0 failed | 20/20 (vkQueueSubmit 20) | - | - |

**fixed3 (fix.patch)**

| group | invocations | Rust ok | tests per invocation | runs with a validation error (stdout/stderr) | VUIDs | SYNC |
|---|---|---|---|---|---|---|
| queue-owner | 3 | 3 | 11 passed / 0 failed | 0/3 | - | - |
| stamp-completion | 1 | 1 | 15 passed / 0 failed | 0/1 | - | - |
| ring-fence-handoff | 20 | 20 | 2 passed / 0 failed | 0/20 | - | - |
| resource-pools | 3 | 3 | 171 passed / 0 failed | 0/3 | - | - |
| engine-exec | 2 | 2 | 58 passed / 0 failed | 0/2 | - | - |
| depth-readiness | 1 | 1 | 3 passed / 0 failed | 0/1 | - | - |
| slab | 1 | 1 | 22 passed / 0 failed | 0/1 | - | - |
| buffer-slab | 1 | 1 | 6 passed / 0 failed | 0/1 | - | - |
| host-imports | 1 | 1 | 9 passed / 0 failed | 0/1 | - | - |
| linear-import | 1 | 1 | 12 passed / 0 failed | 0/1 | - | - |
| mixed-default | 5 | 5 | 1 passed / 0 failed | 0/5 | - | - |
| mixed-narrow | 5 | 5 | 1 passed / 0 failed | 0/5 | - | - |
| core-handoff | 3 | 3 | 6 passed / 0 failed | 0/3 | - | - |
| core-lib-all | 1 | 1 | 643 passed / 0 failed | 0/1 | - | - |
| mrt-order-gpu-default | 3 | 3 | 5 passed / 0 failed | 0/3 | - | - |
| mrt-order-gpu-narrow | 3 | 3 | 5 passed / 0 failed | 0/3 | - | - |

| held-open-off counter (µs unless noted) | before median (n) | after median (n) | before mean | after mean |
|---|---|---|---|---|
| batch_flush_submit_us | 10.0 (50) | 12.0 (50) | 11.0 | 12.7 |
| batch_flush_finish_us | 26.0 (50) | 24.0 (50) | 29.1 | 26.5 |
| queue_async_queue_us | 40.5 (50) | 46.5 (50) | 62.6 | 49.3 |
| queue_async_driver_us | 2578.5 (50) | 1686.0 (50) | 2820.5 | 1758.8 |
| process_ms | 1123.0 (50) | 1224.0 (50) | 1151.7 | 1282.0 |
