# Staged lossless Reims FIFO/gzip capture

PASS: **21 offline tests**, plus an actual paused synthetic Reims/QEMU writer check. Staged only; no active runner/profile, guest, binary, library, backend or sampler was edited. No Apple input or guest execution was used.

Frozen runtime module:

```text
reims_log_capture.py
fb2ff806ad0176a5477983f53dde85c1a3c647141afb7ecb40d50158076163c8
```

## Actual writer contract

The inspected source is `/work/orchard/reims-vgpu/crates/reims-vgpu-observe/src/sink.rs`, SHA-256 `07eafa99adb1c3dab1687fecd02cd2b79d04cbd426c2f6a1f506773daab29b34`. Product `writer::open`, lines 328–334, uses `OpenOptions.create(true).append(true).open(path)` and `BufWriter`; lines 420–427 only write line bytes and a newline. There is no seek, truncation or regular-file requirement in that path. `source-contract.json` records the finding.

The real-library check created `/tmp/reims-vgpu-fail.log` as a FIFO before realizing the unchanged qualified QEMU. Reims startup/heartbeat output wrote **516 raw bytes**; gzip recovered all 516 with matching SHA-256. The compressed artifact was 344 bytes. QMP remained `prelaunch/running=false`, the CPU was never resumed, and QEMU exited 0. The check finished in 3.258 seconds under a 20-second internal bound, one CPU / two GiB, read-only root/build volume, network none and 16 MiB tmpfs. Peak cgroup memory was 80,846,848 bytes; no OOM. Fresh existing host samples retained the 10 GiB floor, with minimum 27,749,990,400 bytes free. All owned containers are stopped.

## Integration API

Import `BoundedGzipCapture` and `CaptureError` from this module. Its standard-library dependencies are zlib/gzip-compatible compression, selectors, file descriptors and hashing; FIFO execution requires Linux/POSIX.

1. Construct `BoundedGzipCapture(fifo_path, attempt_dir)` **before starting QEMU**, with the source path `/tmp/reims-vgpu-fail.log`. The constructor refuses existing source/artifact paths and symlinks. It opens its FIFO `RDWR|NONBLOCK|CLOEXEC|NOFOLLOW`, so the library's append/create open has an existing reader and cannot wait for one.
2. Call `capture.pump()` from the existing runner loop/guard. Each call reads at most 256 KiB by default, in chunks no larger than 64 KiB, with no wait for source input. It owns its selector; `capture.fd` is also available if needed. There is no background worker or watcher.
3. Treat **any `CaptureError`, `capture.exhausted` or `capture.error` as a fatal capture condition**. Stop/reap only the runner's owned writer processes immediately. Do not keep running the guest with a failed capture.
4. After all writers have stopped, call `capture.close()`. It drains only a bounded pipe tail, finishes gzip, closes its descriptors and removes only its matching FIFO. It refuses to unlink a replacement. `close(suppress_errors=True)` exists solely for a cleanup path that already records the failure; inspect the returned failure status. Close is idempotent.
5. Retain `capture.paths` and `capture.stats()`. Paths identify the canonical gzip, first/last previews and metadata. Stats include captured/read raw bytes, any unretained read bytes, raw SHA-256, chunk count, compressed/preview bytes, last-preview raw offset, retained/allocated counts, error/exhaustion and gzip finalization state.

Keep the existing regular-file mode as the default. This class is opt-in. The parent must integrate the new artifacts into its existing total diagnostic accounting and failure handling; copying/statting the source FIFO as though it were the old regular log is not appropriate. This class never starts/stops processes or changes the parent's host-space floor, wall deadline or resource guard.

## Storage and byte-preservation semantics

The default cap is **8 MiB of retained compressed capture files**, not the old 8 MiB uncompressed regular-file cap. The separate uncompressed hard stop is **64 MiB**. File lengths and measured allocated blocks are checked, with bounded allowances for sidecars and filesystem rounding:

- Canonical single gzip stream: at most 8,290,304 bytes with the observed 4 KiB block size. This includes its final footer; a separate 128-byte in-stream finish allowance is held before further reads.
- First and last raw previews: at most 32 KiB each.
- Metadata allowance: 16 KiB; additional rounding allowance: four filesystem blocks, normally 16 KiB.

The module treats input as opaque bytes. It does **not** parse, filter, sample, classify or discard `OFF`, failure, startup, state-transition, unknown-prefix, binary or unterminated-line data. It has no growing line buffer. Every committed raw chunk is `Z_SYNC_FLUSH`ed, so in-run previews and a streaming zlib decoder can inspect current bytes before the final gzip footer exists. Ordinary strict `gzip.decompress` verification is available after close.

Before reading a new chunk, conservative expansion admission and exact trial-compressor/footer checks reserve its storage. On a normal budget stop, the finished gzip retains the exact consumed prefix, with no lost consumed bytes. Unread FIFO bytes and messages still queued inside the library are not claimed as captured; the owner must stop on that explicit limit. An actual I/O/compressor failure may make capture incomplete; the class reports it, tracks unretained read bytes, and never labels that failure a complete lossless capture. It does not provide a separate cancellation supervisor for a kernel filesystem stall; the parent retains process/wall supervision.

Readable previews are bounded views only. The canonical gzip preserves the entire captured byte stream and full error visibility; a failure outside the first/last preview remains present there.

## Tests and evidence

`test_reims_log_capture.py` passed **21 tests in 1.163 seconds** in the existing immutable runtime image, network none, one CPU / one GiB. Coverage includes:

- 1,800 seconds' worth of synthetic idle telemetry exceeding 8 MiB raw, mixed with injected failure and unknown `OFF` binary bytes; exact decompressed oracle and SHA-256.
- Partial chunk boundaries, an unterminated line larger than 9 MiB, and byte-oriented processing without a line buffer.
- Noncompressible overflow at both a reduced fixture budget and the actual default 8 MiB budget; valid bounded footer and exact captured prefix.
- The actual 64 MiB raw hard stop, all sidecar/footer limits, in-run SYNC-flush decoding and previews.
- Existing regular/FIFO/symlink refusal, artifact preservation, append/create open, bounded pipe backpressure, writer-tail drain, cancellation of a busy writer, own-FIFO cleanup, replacement preservation, and explicit I/O failure reporting.

See `tests.log`, `containers.json`, `source-contract.json`, and `paused-capture/{result.json,command.json,reims-capture.json,reims-vgpu-fail.log.gz}`. The paused fixture proves actual FIFO compatibility, not macOS boot or guest graphics.

Parent accounting follow-up: _publish now converges its self-referential metadata counters before publishing, fixing the9-byte stale logical-retention field observed in normal-system-boot. Runtime sourceSHA3ce7bab9c38da2c5ce5efa91464162ca64da9acba75ec50e231bc71f44455c35;22module tests and82runner tests pass. Byte capture/compression and limits remain unchanged. Previousfb2 source is preserved in the earlier per-attempt source snapshot.
