# Offline larger-cache review gate: PASS

Implemented `--cache-layers 1..8`, default 2, in the CLI/plugin and guarded source
adapter. Capacities above two require a finite cgroup v2 hard memory limit of at
least `layers * 512 MiB + 2 GiB`. Eight layers require 6 GiB. Unknown, unlimited,
malformed, unreadable, or inadequate budgets fail before base allocation/fetch.
The frozen constructor receives `min(requested, 2)`; the adapter assigns the
admitted capacity afterward. No cryptographic or byte-mapping check changes.

The final **43 tests passed**: 29 existing NBD/cancellation tests and 14 new
cache/integrity/admission tests, with zero failures, errors, or skips. Ten tiny
manufactured Apple-LZ4 layers prove eight resident hits without refetch, one LRU
eviction at the ninth distinct layer, and verified re-fetch after eviction.
Bad compressed/raw hashes and truncated layers never commit. A real eight-layer
read-only NBD fixture passes; an actual 512 MiB Docker cgroup refuses capacities
3 through 8 before the frozen constructor. Mocked missing/unlimited/invalid
budgets and exact admission boundaries cover the other resource cases.

Both suites used `--network none`, read-only roots, two CPUs, tmpfs metadata,
read-only frozen/reader mounts, internal 60/90-second alarms and external
70/100-second timeouts. Final cgroup peaks were **93,843,456 bytes** for legacy
and **93,634,560 bytes** for larger-cache tests, below 90 MiB each. Each process
inherited a 512 MiB address-space limit; the test container's 6 GiB ceiling did
not allocate 6 GiB. Maximum measured cancellation was **0.715 seconds**; all nine
recorded cancelled process groups disappeared.

Required original image, still unchanged:
`sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`.
New `macos-streamed-guest-large:local` image:
`sha256:7810c1732534d73f8cc50f213f1b682eca4e78df6f3b2369cc03285383ee26ac`.
The new filesystem has exactly one COPY layer over that base; no apt/dependency
build ran. All **10 packaged Python files** match host hashes.

The three frozen converter hashes, `frozen.py`, `nbd_source.py`, `supervision.py`,
existing test sources, and observed ASIF-reader/decmpfs hashes are unchanged.
An AST audit against original-image source verifies 28 protected guard, read,
and cancellation functions/classes. The 10 GiB / 20-second host guard,
900-second layer and 3600-second initialization limits, 50 ms polling, 5-second
grace, read-only behavior, pins, mapping, and verified commit remain intact.

`handoff.json` contains exact source/frozen/reader hashes, image IDs and resource
results. `source-review.diff` contains the three production Python diffs.
`test-commands.json`, `packaged-files.json`, both test logs, resource JSON, and
cancellation telemetry provide the underlying evidence. `validate.ps1` repeats
the bounded offline validation. The initial expected regression failure and two
fixture-harness setup errors are preserved in their own logs.

`proposed-live-profile.ps1.txt` contains the unexecuted 6 GiB / two-CPU / eight-layer
read-only profile, using the existing state volume and a new name/socket. Parent
review, live warmup, and cutover remain next. No live Golden fetch, backend
restart, guest read, VM run, host restart, full-system/state edit, cleanup, or
delegation was performed. Live boot latency and XNU handoff remain unvalidated.
