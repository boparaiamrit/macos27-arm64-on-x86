# Streaming ASIF to sparse RAW — parent review handoff

Implementation and fixture testing are complete. **No full Golden image conversion has been run.** The real-data check verified only disk layer 0 and the header/active tables; remaining real bitmaps and disk layers still need verification during the approved operation.

## Files and dependencies

- `asif_to_raw.py`: CLI, ext4 sparse writer, space guards, exclusive output lock, durable checkpoint/resume.
- `oci_stream.py`: manifest/config pinning, public GHCR streaming transport, Apple `bv41`/`bv4-`/`bv4$` framing, bounded verified layer cache.
- `asif_plan.py`: strict adapter around the pinned, bitmap-aware fs-explorer ASIF reader; builds extents in physical source order.
- `test_converter.py`, `Run-ConverterTests.ps1`: independent handmade fixture tests, offline on the small `macos-golden-full-guest` volume.
- `resource_probe.py`: offline maximum-layer/cache RSS check without payload files.
- `Watch-HostSpace.ps1`: live Windows C: free-space samples, used for large conversions.
- `real-table-inspect.json`, `verification.json`, `converter-tests.txt`: evidence from this implementation run.

Uses the existing `macos-arm-research:local` image (Python 3.13, requests, lz4) and read-only `../apfs-tools/src`. No host packages are installed. The dependency's `containers/asif.py` SHA256 is enforced at import:

`9c3d02b235d4808a97a688f1d6fd048d2113ad7fd26954224b7f1aeabf439505`

fs-explorer 0.5.0 is copyright 2026 Arthur Gouhier, BSD-3-Clause. Preserve `../apfs-tools/LICENSE`, `../apfs-tools/provenance.json`, and the existing `provenance/fs-explorer-LICENSE`. The source archive SHA256 is `1398600e798168823cad4b26b2db4b2c4ea13459e787156749b6e192e12382e9`. The dependency is not modified or copied into the converter. Existing specification/provenance files were preserved, and `source_probe.py` was not rerun.

Format references are the local `asif-spec-94bdfb5.md` (huven/asif-format commit `94bdfb52c0a654a01bef30c7ce537f756edcaacc`) and staged Tart `DiskV2.swift` at commit `95a0dac50acf832bfe151d25882bff0ba2f39a9b`.

## Integrity and resume behavior

The raw manifest bytes must match the explicit manifest digest. The **Tart guest config layer** must match its descriptor size/hash and declare `diskFormat=asif`, `darwin`, `arm64`; the OCI config is not a substitute. Unknown layer types, unsupported ASIF flags, invalid geometry/bounds, ambiguous equal-sequence directories, overlapping metadata/data, reused data chunks, missing/truncated bitmaps, and bitmap state `11` fail closed.

Highest directory sequence selects the active table copy. Zero directory entries and data states `00`/`10` are holes. Full chunks are valid without bitmap lookup; partial chunks use LSB-first two-bit sector states. Only `01` sectors are copied. EOF clips the exact guest size **before** interpreting a tail bitmap; initialized sectors outside the source fail rather than becoming zero padding. ASIF metadata above guest EOF is not exported.

Each OCI layer is streamed into a single preallocated decoded buffer; compressed bytes are never spooled. Both compressed SHA256 and Tart uncompressed SHA256 and both lengths must pass before its bytes become readable. A plan maps physical source extents to logical RAW offsets. Conversion processes every source layer in order, including layers with no guest extents, and splits writes at layer boundaries.

The RAW must be one regular file on Linux ext4, created exclusively and sparsely truncated. Only valid runs are written. Each layer batch is fsynced, read back and hashed, then checkpointed via fsynced temporary JSON, atomic rename and directory fsync. An exclusive `flock` prevents a second converter. The checkpoint binds manifest/config/plan digests, output path/inode/device/size, and a contiguous prefix of verified layers. Resume revalidates completed output hashes and uses ext4 `SEEK_DATA` to ensure guest holes still read zero. Uncheckpointed valid writes replay idempotently. Keep the same volume and `/out/disk.raw` mount path on resume. A RAW is usable only when its checkpoint says `complete: true`.

## Resource bounds and observed real layout

The manifest pins 67 layers: 30,867,739,355 compressed bytes and 35,735,707,648 ASIF bytes. The real active directory is sequence 2; guest RAW length is exactly 50,000,000,000 bytes. There are 34,058 mapped chunks and 1,733 partial chunks, with 1 MiB chunks and 512-byte sectors.

The whole-chunk allocation ceiling is **35,712,401,408 bytes**. Clipping the final guest chunk gives 35,712,103,424 mapped guest bytes. The exact valid-sector total and ext4 block allocation prediction require the remaining bitmaps. The planner reports both valid bytes and the union of touched 4096-byte filesystem blocks; it does not confuse logical size with allocation.

Fifteen required bitmap chunks occupy 15 MiB across source layers **0, 26, 48, 52, 55, 59, 63**. A cold complete metadata plan therefore fetches 3,089,726,239 compressed bytes (these layers must be fully hashed), followed by the sequential conversion pass. Expect about **33,957,465,594 compressed network bytes** for a fresh full run, plus transport retries/restarts. This extra network pass does not create ASIF files. The default inspect fetch cap of 1 GiB deliberately stops before a complete real metadata plan; use `--tables-only` for the bounded check.

Default decoded cache: one 512 MiB layer; configurable maximum: two. Limits: 4 MiB Apple frame, 16 MiB source read/chunk, 64 MiB bitmap set, two cached ASIF tables, 262,144 guest chunks, 200,000 valid extents. A synthetic three-layer run with two cached 512 MiB layers measured **1,134,571,520 bytes peak process RSS**, with zero payload files. Full production RSS with metadata is not yet measured. Docker commands below enforce 1900 MiB RAM with no additional swap allowance.

Large conversion enforces at least 10 GiB free reserve. It checks ext4 capacity against remaining data allocation plus a 1 GiB filesystem overhead allowance. Live Windows samples additionally reserve 8 GiB for the other worker. Host samples older than 20 seconds stop the converter. Guards run before and after layer fetches, before any next writes; a stopped run resumes from the last durable batch. These checks assume the other worker stays within its stated 8 GiB budget and no unrelated process unexpectedly consumes the reserved space.

## Commands

Run tests from the repository root:

```powershell
& .\test-output\arm-macos\full-disk\Run-ConverterTests.ps1
```

Prepare common Docker arguments in PowerShell (no container starts here):

```powershell
$converterDir = (Resolve-Path .\test-output\arm-macos\full-disk).Path
$dependencyDir = (Resolve-Path .\test-output\arm-macos\apfs-tools\src).Path
$inputDir = (Resolve-Path .\test-output\arm-macos\full-system\inputs).Path
$dockerArgs = @(
  'run', '--rm', '--memory=1900m', '--memory-swap=1900m', '--entrypoint', 'python3',
  '--mount', "type=bind,source=$converterDir,target=/work,readonly",
  '--mount', "type=bind,source=$dependencyDir,target=/deps,readonly",
  '--mount', "type=bind,source=$inputDir,target=/inputs,readonly",
  '-e', 'PYTHONPATH=/deps', '-e', 'PYTHONDONTWRITEBYTECODE=1', '-w', '/work'
)
$pinArgs = @('--manifest', '/inputs/manifest.json', '--config', '/inputs/config.json')
```

Verify existing pins without a blob request:

```powershell
docker @dockerArgs macos-arm-research:local asif_to_raw.py pins @pinArgs
```

Bounded header/table inspection, verifying one 432,223,167-byte compressed layer in RAM:

```powershell
docker @dockerArgs macos-arm-research:local asif_to_raw.py inspect @pinArgs --tables-only --max-fetch-bytes 432223167
```

Complete bitmap-aware planning **after parent review** (up to 3.10 GB network, no RAW output):

```powershell
docker @dockerArgs macos-arm-research:local asif_to_raw.py inspect @pinArgs --max-fetch-bytes 3100000000
```

For a subsequent approved full conversion, run the host-space sampler concurrently in a background job. This only writes `host-space.json` and its atomic temporary file inside `full-disk`. A stale sample is never accepted:

```powershell
$spaceJob = Start-Job -FilePath (Join-Path $converterDir 'Watch-HostSpace.ps1') -ArgumentList 86400,2
```

After the sampler has written a fresh sample, use the parent-approved ext4 volume. The volume named below was used **only for small tests in this task**; the following large operation was **not run**:

```powershell
$conversionArgs = $dockerArgs + @('--mount', 'type=volume,source=macos-golden-full-guest,target=/out')
docker @conversionArgs macos-arm-research:local asif_to_raw.py convert @pinArgs --output /out/disk.raw --host-space-file /work/host-space.json
# Same command plus --resume resumes a stopped conversion.
# --stop-after-layers N checkpoints cleanly after N additional source layers.
```

Stop the sampler job when the operation ends: `Stop-Job $spaceJob; Remove-Job $spaceJob`. Do not delete a partial RAW to retry; retain its checkpoint and use `--resume`. The script never runs QEMU, publishes artifacts, changes host packages, or starts another worker.
