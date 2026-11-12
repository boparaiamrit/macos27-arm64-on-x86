# Bounded Golden full-guest runner

`launch-full-attempt.sh` runs `run-full-attempt.py` inside the existing
`macos-orchard-runtime:local` image by default, or the already-built
`macos-streamed-guest:local` image with explicit `--streamed`. This implementation
has been tested with synthetic input files, pipes/FIFOs, locks, mocked child
processes/adapter negotiation, and a fake Docker CLI. Subsequent Windows-Docker
attempts are retained under `attempts/`; the eight-layer cached attempt reached
Golden 26A428 iBootStage2 and an observed data-abort panic. XNU and a GUI remain
unverified. See `iboot-diagnosis/REPORT.md` for the measured fault.

`Launch-FullAttempt.ps1` is the Windows Docker entry point. Its explicit
`-StreamVolume macos-golden-stream-large-state -ReadyName stream-ready-large-live5.json`
selection uses the separately validated eight-layer backend. `-IBootDiagnostic`
uses a read-only debugger observer instead of the XNU handoff helper and stops
after a verified Stage2 snapshot; it never counts as a kernel handoff.
An actual serial `iBoot Panic:` now stops the owned attempt promptly.

The optional `-GoldenScratch` profile uses a separate binary admitted by its
exact digest in `golden_scratch_profile.py`. Existing AUX and overlay state
are retained. `migrate-scratch-identity.py` first performs the complete original
profile preflight, preserves the old identity, and changes only `qemu_sha256`
with atomic replacement, readback, and before/after guest-file hashes. It never
resets AUX, rebases an overlay, changes a backing URI, or patches firmware.

Later profiles are explicit and mutually exclusive: `-GoldenAvpRtc` adds the
logged AVP RTC register-store diagnostic; `-GoldenCtrr` also maps the documented
CTRR probe as unimplemented (zero reads, discarded writes). These do not claim
complete RTC behavior or CTRR protection. Each profile binds a separate binary
and requires its corresponding deliberate one-field identity migration; an
older profile refuses the newer identity instead of replacing guest state.
The current experiment uses `-GoldenCtrr -IBootDiagnostic`, with the same large
stream volume/readiness selection above, until an actual handoff is qualified.

The captured Golden revision-3 handoff is now available as the separate
`-GoldenHandoff` profile. Its two helper digests are pinned in
`golden_handoff_profile.py`; `migrate-handoff-identity.py` preserves the old
identity and changes only those two helper hashes, keeping the same emulator,
firmware, AUX and overlay. It requires `0xe0a00000`, the actual r3/v2 structure,
and the staged adapter's content/range/readback checks. It preserves the existing
root-selection command line while appending verbose serial flags, and inserts
`DoNotUseSEP=1` inside validated zero padding. This is a guest-RAM edit; it does
not patch the installed kernel or prove kernel execution. Use this profile after
its successful migration, rather than an earlier profile with different pins.

## Required parent preparation

Keep the existing Windows host-space watcher running. The runner reads
`full-system/host-space-live.json` before subprocess creation and during every
supervisor iteration. It requires a Windows `C:\` sample no older than twenty
seconds, at least 10 GiB free, and no timestamp more than two seconds ahead.
The watcher, converter, preparation helper and handoff helper are parent-owned.

The default strict **local RAW mode** requires the guest volume
`macos-golden-full-guest` to contain:

```text
/guest/golden-gate-27.raw                  # logical size 50,000,000,000
/guest/golden-gate-27.raw.checkpoint.json  # complete: true; all 67 layers
/guest/boot/prepared-inputs.json           # prepare-full-guest.py report
/guest/boot/AVPBooter.original.bin         # extracted matching guest firmware
/guest/boot/AVPBooter.patched.bin          # separately inspected/patched by parent
/guest/boot/aux.work.img                  # persistent working copy
```

The pinned manifest is
`sha256:b78a521145ebef24e9916c0b3999e165bb12b587d11524c5fa3ba4fe7bf79bb9`.
The original `full-system/inputs/{manifest.json,config.json,aux.img}` must
remain available. Validation covers the actual manifest bytes, config and
original AUX descriptor hashes, all checkpoint layer pins/readback digest
records, RAW inode/device/size, the prepared report, firmware, and the Golden
QEMU binary. The checkpoint's original `/out/golden-gate-27.raw` path is accepted
because the same volume is mounted at `/guest` here. This is a checkpoint
verification, **not a fresh full-disk RAW readback**; the converter owns that
verification. The RAW is held with a shared `flock` throughout the attempt, so
an active converter's exclusive lock blocks launch.

### Explicit read-only streamed NBD mode

The runner never converts a disk, creates a checkpoint, or treats a partial RAW
conversion as complete. Without `--streamed`, all local RAW requirements above
remain mandatory, including the complete 67-layer checkpoint and shared RAW lock.

For `--streamed`, the parent instead supplies a prepared `boot/` directory on
`macos-golden-full-guest`, with the same firmware/AUX/report filenames above and
**no local full disk required**. `prepare-streamed-guest.py` is parent-owned and
must have completed independently. Its report must retain the existing version,
firmware, AUX and paired-identity fields and additionally contain:

```text
source_kind = "readonly-streamed-nbd"
manifest_digest = <the pinned manifest above>
plan_digest = sha256:700a601da177786c796ff441c0c8f1d4edd0a4970557f7f81fa0ebb1092153a3
nbd_socket = /stream/golden-live2.nbd  # or the exact explicit --socket path
logical_disk_bytes = 50000000000
local_full_disk = false
```

The parent captures the live server's `export_ready` stderr event as
`full-system/stream-ready.json` (or passes another `--ready` path). The runner
requires `event=export_ready`, `readonly=true`, the manifest and actual config
hashes in `manifest_pin`/`config_pin`, the pinned digest in `planDigest`, and
`getsize=50000000000`. It compares these to the prepared report and
`full-system/validated-asif-plan.json`, or the explicit `--plan` path. The plan
report must have `status=metadata_verified`, the matching manifest/config hashes,
the pinned `plan_digest` and matching `logical_raw_bytes`. The fixed plan digest
is the cryptographic plan identity, not the hash of the report JSON file; the
report file's own SHA-256 is also recorded in the persistent runner identity.

Finally, the runner negotiates the actual export using the staged
`streamed-disk/nbd_source.py` `NBDSource` adapter and libnbd. Its constructor must
refuse a writable export, and `getsize()` must independently match the expected
size. This check performs no `read_at`, `read_exact` or `pread`. A stalled
negotiation has a five-second ceiling within the overall deadline, with the
space/log/overlay guards checked while waiting. The probe uses a daemon thread
and no subprocess; the private launcher container exits with the runner even if
the connection remains blocked. No external adapter exception text is logged.

Readiness is evidence of metadata planning, not a full payload readback. Streamed
attempt results explicitly retain `all_disk_layers_verified=false` and describe
payload verification as on demand by the pinned server. Neither readiness nor
this runner establishes that all 67 layers have been read or verified.

The parent owns the separate HTTP-capable server container and its cancellation
review gate. **Do not run live preparation, guest reads or boot until that gate
passes.** The VM profile has `--network none`; it reaches the export only through
the shared Linux `macos-golden-stream-state` volume, mounted read-only at
`/stream`. A server socket must be an actual Unix socket at an absolute canonical
path; its URI is `nbd+unix:///?socket=/stream/golden-live2.nbd` for this example.
No host port mapping is added. The guest's optional user-mode NIC uses
`restrict=on` in this profile; no Internet access is needed for the first probe.

Firmware is never patched by this runner. Both ROMs must have the reported
length; the original SHA-256 must match `prepared-inputs.json`. At exactly
`--patch-offset` (default `0x2314`), the original must contain
`7f2303d5ff4303d1` and the patched file `000080d2c0035fd6`. Every byte outside
that eight-byte site must match. The checker uses the retained Orchard
`scripts/patch-avpbooter.py` byte contract. A differing firmware revision or
offset requires the parent's explicit investigation; there is no pattern
search or fallback offset.

QEMU must exist at
`/work/orchard-golden/qemu/build/qemu-system-aarch64` with SHA-256
`2fca0114c7f37fac34d9e13def8c5c66850ac5e2d2c8a19365c0631f02b57705`.
The existing build volume is mounted read-only. No image build is performed.

## Use from WSL, after preparation

First validate without starting any subprocess or creating an overlay:

```bash
bash /mnt/c/Users/bopar/Projects/macos/test-output/arm-macos/full-system/launch-full-attempt.sh --check-only
```

When the parent is ready to authorize an actual attempt:

```bash
bash /mnt/c/Users/bopar/Projects/macos/test-output/arm-macos/full-system/launch-full-attempt.sh --timeout 180
# Optional first-boot single-user request:
bash /mnt/c/Users/bopar/Projects/macos/test-output/arm-macos/full-system/launch-full-attempt.sh --timeout 180 --single-user
```

For the new profile, only after the parent gate and preparation above:

```bash
bash /mnt/c/Users/bopar/Projects/macos/test-output/arm-macos/full-system/launch-full-attempt.sh \
  --streamed --socket /stream/golden-live2.nbd \
  --ready /parent/full-system/stream-ready.json --check-only

# Parent-controlled first-boot experiment; not run during this implementation:
bash /mnt/c/Users/bopar/Projects/macos/test-output/arm-macos/full-system/launch-full-attempt.sh \
  --streamed --socket /stream/golden-live2.nbd \
  --ready /parent/full-system/stream-ready.json --timeout 180 --hook-timeout 60
```

`--streamed` requires both `--socket` and `--ready`. Those options and `--plan`
are rejected in local RAW mode. There is no implicit mode fallback. The launcher
selects `macos-streamed-guest:local` and distribution `/usr/bin/python3` for its
installed `python3-libnbd`; no image build or package installation is performed.

The validation-only command still starts the launcher container; **the Python
runner itself invokes no subprocess** in `--check-only` mode. Missing images
or volumes fail rather than being built, fetched or implicitly created.
`--check-only` writes an attempt report and acquires the boot-directory lock.
It does not create the persistent identity or change AUX/overlay state.
It checks an existing overlay's allocation, but the `qemu-img` backing metadata
inspection runs only on the launch path, before QEMU starts.

The Docker bounds are four CPUs, 12 GiB RAM with swap capped to the same amount,
256 PIDs, a read-only container root, no network connectivity, disabled core dumps and a private 16 MiB
`/tmp` tmpfs. No GPU or Windows devices are mounted. `/parent` is the entire
experiment directory, mounted read-only, with only `full-system/attempts`
overmounted read-write for reports. Build and software Vulkan sources are
read-only. `PYTHONPATH=/parent/apfs-tools/src:/parent/streamed-disk`,
`CONVERTER_SNAPSHOT=/parent/full-system/converter-snapshot` and
`APFS_TOOLS_SRC=/parent/apfs-tools/src` select the staged, read-only helpers
rather than the image's server defaults. Launching does not run preparation. Bytecode
writes are disabled in Python and explicitly in GDB's embedded Python.

Software Vulkan uses the parent-owned
`orchard-build/golden/runtime` mounted read-only at `/soft`, with:

```text
VK_DRIVER_FILES=/soft/lvp_icd.json
VK_ICD_FILENAMES=/soft/lvp_icd.json
LD_LIBRARY_PATH=/soft/lib
LP_NUM_THREADS=2
REIMS_VGPU_WINDOW=0
```

That unmodified ICD contains an absolute `/out/runtime/lib/libvulkan_lvp.so`
path, so the same runtime is also mounted read-only at `/out/runtime`.

## State and supervision

An exclusive, nonblocking `flock` on `/guest/boot/.full-runner.lock` permits one
runner per boot directory. `/guest/boot/runner-identity.json` binds subsequent
attempts to the same immutable pins, config, RAW inode, firmware, preparation
report and helper hashes. It records hashes rather than the full ECID.
Streamed identity substitutes the exact backing URI/socket, manifest/config/
plan pins and plan-report hash for the local RAW inode/checkpoint fields.
The identity is written only after complete validation. A changed pairing
fails closed; the runner never deletes the identity or resets storage.
The ECID is decoded locally with Base64 and `plistlib` and passed to QEMU's
machine UUID. The saved argv and collected logs redact its decimal and common
hexadecimal forms; no config/identity plist is copied into attempt logs.

`root.overlay.qcow2` is created only when absent, using:

```text
qemu-img create -f qcow2 -F raw -b /guest/golden-gate-27.raw /guest/boot/root.overlay.qcow2
```

In streamed mode the explicit RAW-format backing is the NBD URI instead:

```text
qemu-img create -f qcow2 -F raw -b 'nbd+unix:///?socket=/stream/golden-live2.nbd' /guest/boot/root.overlay.qcow2
```

An existing overlay is inspected for qcow2 format, virtual size and exact RAW
backing path/format and preserved. Streamed overlays must have the exact URI from
the matching persistent pinned runner identity. An existing streamed overlay
without that identity is refused. URI or pin mismatches never cause a reset,
replacement or rebase. The working AUX is size-checked and preserved;
its content may legitimately change between attempts. Input AUX hash validation
always checks the original `inputs/aux.img`. The per-attempt report also records
the working AUX hash before startup. The local RAW or streamed NBD pflash drive is explicitly
`format=raw,readonly=on`; the root block device writes through the qcow2 overlay
with `cache=writeback`. No command opens a physical device or writes the RAW.

The first experiment uses `apple-vm`, one vCPU, 8 GiB guest RAM, single-thread
TCG, headless display, the paired AUX pflash/virtio devices, root virtio device,
and an isolated user-mode NIC with IPv6 off and `romfile=`. QEMU starts paused
with GDB on container-local `127.0.0.1:1234`; QMP uses a short, unique Linux
socket. `-no-reboot` confines the experiment to its first boot.

GDB runs the unmodified parent `kernel-handoff.gdb` in batch mode. Its environment
sets RAM base `0x70000000`, RAM size 8 GiB, `-v serial=3` (plus `-s` for
`--single-user`), and a unique `HANDOFF_RESULT`. `--handoff-pc` defaults to
`0xaca00000`, **still unverified for the Golden firmware**. The parent's helper
uses X1 on the second trampoline hit and validates boot_args revision/version
2/2, NoSEP edits and readback before detaching. A successful GDB exit alone
does not count: the runner requires the matching result JSON and verified
readback. There is no persistent reboot hook.

`--hook-timeout` defaults to 60 seconds and cannot exceed 60. `--timeout`
defaults to 180 seconds and cannot exceed 300. Ten seconds of this overall
budget are reserved for shutdown; validation, qemu-img and startup also consume
the budget. Very short budgets can expire before QEMU starts. The runner
requests QMP quit (or TERM if QMP is unavailable), signals its own GDB child,
allows a shared five-second graceful wait, then kills/reaps only its owned
children. As with any user-space timeout, an uninterruptible kernel/filesystem
stall cannot be given a real-time guarantee.

Live supervision checks space and diagnostic usage at 100 ms intervals;
individual QMP exchanges can take up to about one second. Serial uses QEMU's
`file:` backend on a unique FIFO, drained into the attempt's regular `serial.log`.
Serial, QEMU stderr and GDB logs each have an enforced 8 MiB capture cap;
qemu-img logs each have a 1 MiB cap. Pipe backpressure prevents runaway host
log writes. Reaching a stream cap stops the attempt. Reims's private log is
guarded at 8 MiB and its entire `/tmp` filesystem is capped at 16 MiB. Aggregate
diagnostics are also checked against a 48 MiB stop threshold, reserving room
for a final bounded Reims tail and JSON, with less than 64 MiB retained per
attempt. The qcow2 overlay also has a separate **2 GiB allocation stop guard**,
measured with Linux `st_blocks * 512`, not its 50 GB virtual size or apparent file
length. It is checked before subprocesses, during qemu-img, before VM launch and
on every live guard iteration. Crossing it stops only this runner's owned
processes; the overlay and AUX remain preserved for inspection. This is a polling
guard rather than a filesystem quota, so in-flight writes can overshoot between
checks or during shutdown. The 10 GiB host floor and 20-second freshness guard
still cover external allocations and AUX writes. Historical
attempt directories are preserved and are not pruned automatically.

## Evidence and interpretation

Each invocation creates a unique `full-system/attempts/<UTC-time>-<random>/`
directory. Depending on how far startup progressed, it contains:

- `result.json`: stop reason, timings, child return codes and observation flags.
- `validated-inputs.json`: input pins/hashes and starting AUX hash.
- `command.json`: exact argv with ECID redacted, Vulkan and handoff environment.
- `overlay-create.log` when new, and `overlay-info.log`.
- `serial.log`, `stderr.log`, `gdb.log` and the helper's `handoff.json`.
- `qmp-initial-status.json` and `qmp.jsonl` with periodic query-status responses.
- `reims-vgpu-fail.log`: up to the last 8 MiB, copied after stopping owned children.

The FIFO and QMP socket shown in argv live in a unique temporary directory
and are removed after shutdown. Their collected regular logs remain in the
attempt directory. Logs may be capped/truncated; this is recorded and treated
as a resource failure. Early preparation failures have no child logs. Lock
acquisition/path failures are returned as JSON on stdout before an attempt
directory can be created.

Exit codes: `0` means validation-only completed, or QEMU itself exited zero
after the verified hook; `2` means preparation/hook/resource/runtime guard
failure; `3` means QEMU exited nonzero after handoff; `124` means the overall
observation deadline; `130` means interruption. A timeout is never a pass.
`handoff_verified` describes only that helper contract. `full_gui_verified`
always remains false, and the default trampoline remains explicitly
unqualified. Serial or QMP activity cannot establish a working macOS desktop.

Run the synthetic suite from WSL without Docker or QEMU:

```bash
python3 -B /mnt/c/Users/bopar/Projects/macos/test-output/arm-macos/full-system/test_full_runner.py -v
bash -n /mnt/c/Users/bopar/Projects/macos/test-output/arm-macos/full-system/launch-full-attempt.sh
```

The 53 synthetic tests use small temporary files and a synthetic manifest/plan pin. Tests
exercise the real validation/collection/locking functions and supervisor with
mocked QEMU/GDB/QMP/overlay tools, the actual staged adapter with fake libnbd,
and launcher argument assembly through a fake Docker executable. They cover
streamed wrong pins/plan/size/read-only evidence, actual adapter writable-export
rejection, no payload reads, negotiation deadlines/live guards, URI/pin-bound
overlay preservation, and allocation-triggered owned-child shutdown. They do not qualify Golden firmware, the
trampoline, Vulkan guest shaders, kernel boot or GUI presentation.

The isolated selection control uses -GuestVolume macos-golden-pristine-guest; the original working pair remains preserved. Read recovery-control/REPORT.md before restoring any AUX. The opt-in -CompressedReimsLog mode preserves all consumed bytes in gzip, with8MiB total retained storage and a separate64MiB raw hard cap; it retains previews and metadata. It leaves the legacy raw-log mode unchanged. Frozen source fb2ff806ad0176a5477983f53dde85c1a3c647141afb7ecb40d50158076163c8,21module tests plus paused realReims FIFO proof and82runner tests passed.

The opt-in GoldenHandoffWdt profile appends only the documented wdt=-1 root-wait diagnostic alongside verbose serial flags. It retains matching/seal requirements and all host bounds. Its GDB script is byte-identical; only the isolated control's option-helper pin migrates. Use the explicit control volume and original-AUX preparation for this experiment; never reset the main pair. See recovery-control/MISSING-BOOT-MEDIA.md and handoff-r3-wdt/REPORT.md.
