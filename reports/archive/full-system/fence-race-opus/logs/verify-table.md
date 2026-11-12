| receipt | variant / plan | case | runs | Rust ok | runs with validation error | threading reports (call: n) | VUIDs | SYNC | oracle failures | skipped |
|---|---|---|---|---|---|---|---|---|---|---|
| `test-baseline-held-open-50-test.json` | baseline | held-open-off | 50 | 50 | 50 | vkQueueSubmit: 50 | - | - | 0 | 0 |
| `test-instrumented-held-open-40-test.json` | instrumented | held-open-off | 40 | 40 | 40 | vkQueueSubmit: 40 | - | - | 0 | 0 |
| `test-instrumented-held-open-40-test.json` | instrumented | primary-off | 5 | 5 | 0 | 0 | - | - | 0 | 0 |
