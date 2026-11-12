# Golden Gate on this Windows/Intel machine: verified limited boot

On 26 October 2026, macOS 27.0.1 restore inputs, build 26A434, booted under
software ARM emulation in Docker Desktop on the Intel Acer host. Three clean
process starts reached Darwin userspace or a single-user prompt. A live serial
session then executed `uname -a`, `/usr/bin/id`, and `/bin/ls /` successfully.

This is a restore RAM disk with a working root terminal. A full installed
macOS system, Finder, WindowServer and accelerated desktop have not been
demonstrated. `stty` and `sw_vers` are absent from this restore environment.

The running VM was stopped after the Windows system drive became critically
low on free space. Automatic approval review rejected removal of the six
duplicate downloaded components with `blocked by policy`; those files remain
under `darwin/parts/26A434__MacOS/`. No unrelated files were deleted.
After the tests, Docker's container-list API returned HTTP 500. The explicit
stop of the interactive VM had succeeded before that error. Final observed C:
free space was approximately 0.17 GiB; Docker service health needs checking
again after storage is available. The cause of the overall free-space decline
was not established by this experiment.

## Evidence

- `evidence/verified-results.json`: machine-readable verified scope.
- `evidence/golden-gate-command-session.txt`: original live command transcript.
- `evidence/golden-gate-interactive-serial.log`: complete serial record.
- `evidence/golden-gate-restore.log`: first kernel/restore-userspace start.
- `evidence/golden-gate-single-user.log`: second start, single-user prompt.
- `evidence/restore-payload-hashes.json`: decoded input sizes and SHA-256 hashes.
- `evidence/minimal-restore-inputs.json`: Apple source URL, build, matched board.
- `evidence/image-requirements.json`: full guest image metadata, including ASIF.
- `vulkan-probe/summary.txt`: the current WSL Vulkan device was CPU llvmpipe.

`uname` reported Darwin 27.0.0, RELEASE_ARM64_T8112, arm64. `id` reported
uid 0, root. Product version 27.0.1 and build 26A434 come from the matched Apple
BuildManifest; the Darwin kernel version is a different version field.

The serial test driver initially rejected command completion because the
terminal emitted CRCRLF, while its regular expression accepted at most one CR.
The command output is present in the saved transcript. The driver now normalizes
CRs, and `verify-evidence.py` independently verified the existing transcript,
boot checkpoints and all six decoded input hashes. The revised live driver
was not rerun because of the storage shortage.

## Implementation and provenance

The successful path uses [darwin-vm](https://github.com/jprx/darwin-vm), commit
`edfc19433da8d04d5927a7b1932acce4034f307c`, and its qemu-sptm submodule commit
`bad6336fb24211f8c4e8e946c259bd5b12417340`. QEMU reports version 11.1.0.
The emulator lives in Docker volume `macos-arm-research-build`, at
`/build/darwin-emulator/qemu-system-aarch64`. The local container image is
`macos-arm-research:local`, derived from the earlier local Snapintosh builder.

Apple inputs were selected from its official macOS restore manifest and fetched
as individual ZIP members, rather than downloading a complete IPSW. The M2 Mac
mini board is j473ap/T8112. The restore ramdisk was not mounted or edited by the
host. Upstream's Linux-compatible device-tree fixup was applied. Booting with
`-s` selected the ramdisk's existing single-user shell, avoiding Mac-only ramdisk
preparation and custom sysroot installation.

qemu-sptm applies its upstream AppleImage4 ignition boot patch in guest memory.
This result does not establish an entirely unmodified executing kernel.
See [the upstream patch](https://github.com/jprx/qemu-sptm/blob/bad6336fb24211f8c4e8e946c259bd5b12417340/hw/arm/xnu_patch.c).
There were no physical target, partition or firmware writes.

An earlier separate VMApple/TCG emulator was also built from 27on86 commit
`509a4ce52bc703dfc79eb8b4283f51acd88b8594`. Its repository-owned firmware smoke
test passed twice. That smoke test alone is not an OS boot. Its copied binary
is `evidence/qemu-system-aarch64`, SHA-256
`c4ed14c5f7109c30029a8a625d5f13c1abac656b1ada2326615b350a3f6f2f75`.

## Resume

Free at least 2 GiB on the Windows system drive before another small boot;
5 GiB or more gives better working room. `Start-RootShell.ps1` checks this,
checks the saved local inputs and build artifacts, then opens the terminal
using the same tested QEMU arguments. This launcher was syntax-checked and its
low-space rejection was tested; an interactive launch through this PowerShell
wrapper remains untested. Quit QEMU with Ctrl+A, then X.

```powershell
powershell -ExecutionPolicy Bypass -File test-output\arm-macos\Start-RootShell.ps1
python test-output\arm-macos\verify-evidence.py
```

The full desktop stage needs substantially more storage, a compatible full
guest disk and graphics integration. The inspected Golden Gate Tart image has
34,098,689,100 bytes of compressed disk layers, a 41,046,507,520-byte ASIF disk,
and has not been downloaded. Its ASIF format cannot be assumed to be raw.
An approximately 80 GiB free workspace is a practical starting allowance,
not a guarantee that the desktop port will work.

The current WSL installation has no Dozen Vulkan ICD or DRM render node. CUDA
visibility of the RTX 5070 does not establish Reims Vulkan support. A recent
[WSL Reims report](https://github.com/steelbrain/reims-vgpu/issues/32) succeeded
with patched legacy code around macOS 13; Golden Gate graphics on this host
remain unverified. Snapintosh's physical Adreno driver is not used in this boot.

All experiment files are beneath the repository's already ignored
`test-output/` tree. No tracked repository files or existing VM configuration
were changed or committed.
