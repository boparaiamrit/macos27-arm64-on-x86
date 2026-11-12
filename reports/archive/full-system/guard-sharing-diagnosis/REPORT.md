# Verified Windows reader/publication sharing incompatibility

Scope: source inspection and scratch files in this directory only. No Docker, VM, service, live sample, sampler, or production source action occurred. The installed codebase-memory skill applies; graph tools were absent in the parent's tool discovery, so this is exact-source fallback with no index-coverage claim.

The outer failing read is `mrt-memory-release-validation/Launch.ps1:30`, using `Get-Content -Raw`. Its preflight counterpart is `Host.ps1:54`. The installed PowerShell 7.6.9 FileSystem content-provider reader was inspected directly through `SessionState.InvokeProvider.Content.GetReader()` and its actual private fields: `_mode=Open`, `_access=Read`, `_share=ReadWrite`. It does not share deletion. The sampler publishes using `Watch-HostSpace.ps1:22-23`, writing a separate temporary file and calling `File.Move(temp, target, true)`. Its existing catches at lines 26-30 handle replacement conflicts; failure to publish leaves consumers responsible for rejecting stale samples.

The R4 historical report captured the failing read stack and sharing violation, but no locking process or native handle identity was captured. Therefore, the specific process that held the conflicting handle during that failure remains unconfirmed. The reader/publication protocol incompatibility is verified; attributing that historical handle to the sampler specifically would exceed the evidence.

## Deterministic scratch evidence

`diagnose.ps1` completed with **13/13 expected results**, recorded in `evidence.json`:

- The actual installed provider reader prevents the producer's `File.Move` overwrite while open.
- A native handle requesting DELETE access and sharing read/write/delete reproduces the same `Get-Content` sharing violation, HRESULT `0x80070020`, with the same provider/FileStream stack family.
- A single-open reader using `FileAccess.Read` and `FileShare.ReadWrite | FileShare.Delete` reads successfully while that DELETE-access handle is held.
- A genuine exclusive lock still rejects the corrected reader. Missing, malformed, stale, future-dated, and below-10-GiB samples also still fail closed with no retries or fallback.
- On this host, `File.Move(source, target, true)` still returns AccessDenied while even a delete-sharing read handle remains open. The old snapshot stays complete; after the reader is disposed the same publication succeeds and a fresh open reads the complete new snapshot. Do not claim delete sharing guarantees overlapping Move overwrite success. The existing sampler retry behavior is unchanged.
- A separate, explicitly supplemental `File.Replace` control demonstrates a complete old snapshot from the held handle and a complete new snapshot from the new path. This is not the sampler's API and is not proposed as a sampler change.

The initial scratch parser error and the initial incorrect expectation of overlapping Move success were corrected before the final run. They were fixture-development failures, not production behavior passes. No historical R4 run was retried.

## Minimal correction and bounded review

The parent-owned `host-space-io/Read-HostSpaceSample.ps1` was inspected after creation. Lines 7-8 use exactly one `FileStream(Open, Read, ReadWrite|Delete)`, lines 10-12 use strict UTF-8 and terminating JSON conversion, and lines 13-14 dispose both stream objects in `finally`. There is no retry, cached sample, grace period, or error suppression. The consumer must retain its existing freshness interval [-2, 20] seconds, floor 10,737,418,240 bytes, process identity, and cleanup behavior.

No material verified issue was found in that bounded helper inspection. The change removes the demonstrated DELETE-access/read-open incompatibility; it cannot make truly exclusive locks readable and must continue to stop on them. The live sampler and all original evidence should remain unchanged.

Hashes at completion:

- `diagnose.ps1`: `2a102dc187beed6a48d1e1c770a9ade1f9199e3d135c178d6281dcdac5b5f5e1`
- `evidence.json`: `1f0ed05195c2c1a69efbfa6626a234582a460961b901970964010347fcfd7e27`

