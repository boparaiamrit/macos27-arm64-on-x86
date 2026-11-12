# Guard sample reader correction

The R4 outer watchdog stopped on a Windows sharing violation while opening the
host-space sample. Its exact historical locking process was not captured.
Scratch tests establish a concrete incompatible access contract: `Get-Content`
opens with `FileShare.ReadWrite`, while replacement can hold DELETE access.

`Read-HostSpaceSample.ps1` reads once with `ReadWrite | Delete` sharing. It has no
retry, cached sample, stale grace or capacity override. Consumers retain the
existing freshness range [-2, 20] seconds and unconditional 10 GiB floor. The
sampler source and running process are unchanged. This helper does not promise
that arbitrary exclusive handles or every overlapping replacement will succeed.

`Test-HostSpaceSample.ps1 -Legacy` reproduced the reader failure: 9 passed, 1
failed. The corrected reader passes 12 cases, including exclusive-lock, missing,
malformed, stale, future and low-capacity rejection. A separate 13-case diagnosis
is preserved in `../guard-sharing-diagnosis/`.

The initial corrected fixture incorrectly expected overlapping File.Move to
always succeed. This host rejected that operation while a reader was open. The
failed receipt is retained as `corrected-initial-test.json`; the final control
instead checks complete old/new snapshots and publication after the handle
closes. The sampler's existing replacement retries remain unchanged.

Apply the helper only to new continuation-harness reads. Preserve old harnesses
and their failure evidence. This correction qualifies guard I/O, not macOS boot
or renderer correctness.
