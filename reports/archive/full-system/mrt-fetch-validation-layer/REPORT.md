# Validation layer preparation — blocked at preflight

No package was downloaded, extracted, installed, or loaded. No container was created by this task. No Vulkan probe, renderer, VM, input, build profile, or production change ran. The bundle is **not qualified** and must not be admitted for engine testing on this evidence.

## Terminal admission mismatch

The bounded host preflight recorded **90 containers / 28 volumes**, against the supplied **89 / 28** admission. It stopped at `host.py:59`, before runtime file hashing, image checks in the harness, download, container creation, or any Vulkan call. The failure and command outputs are retained unchanged. Per the task's no identity retry instruction, the harness was not run again and no admission was widened.

Read-only comparison of the captured inventory with the existing `mrt-fetch-runtime-validation/host-after.json` found:

- All 89 baseline container IDs remained present.
- One additional ID: `409da3cef8f5bfbeb2226d31d1510eadc924c15ad7869049d72486be0b246c8e`.
- No volume-name difference; 28 volumes were present.

The extra container's owner and workload were not inspected. Concurrent CPU work was mentioned in the admission, but this evidence does not identify the extra container as that work. No additional Docker query or execution retry was used to resolve it.

## Preserved identities and guard evidence

The recorded preflight matched sampler PID 77088, created `2026-10-28T18:26:02.680068Z`, and Android PID 79064, created `2026-10-28T08:15:59.065206Z`. The exporter was running with PID 679 and start `2026-10-28T21:58:44.477275548Z`. No control action was issued to any of them.

`budget.json` records 2.76564 seconds for the attempted harness, minimum sampled host free space 45,957,124,096 bytes, maximum polling gap 0.2194 seconds, and requested polling interval 0.2 seconds. Every sample read in that attempt passed drive C:, age [-2,20] seconds, and the unconditional 10 GiB floor. This does not re-admit later execution.

The existing runtime manifest was read manually during source inspection. Its supplied SHA256 pin is `5711c1e0cc73a67cd8643f1d84591651a75f0de2ad27315f0c7709035ba63a0e`, listing six files, Mesa 26.2.5 and LLVM 21.1.8. The harness stopped before verifying those six byte pins. No preservation hash comparison is claimed.

Both exact image IDs were confirmed present by read-only host image inspection. An earlier manual inventory query accidentally omitted the `13` prefix from the runtime image digest and returned `No such image`; the subsequent exact-ID presence query succeeded. Neither query pulled, started, or changed an image. Exact admitted IDs:

- Builder: `sha256:14ea78615d69de5eea70014968be23464751916c6c44793f19f5771a9b4eeb17`.
- Runtime: `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`.

## Files prepared, but unexecuted

`host.py`, `container.py`, and `probe.c` are staged implementation drafts. Only the first host preflight ran. No compiler, extraction tool, runtime dependency check, loader, or callback path ran. These drafts have not passed a successful end-to-end test. Existing evidence files use exclusive creation to prevent silent overwrite on another invocation.

The intended package is the exact parent-admitted official HTTPS URL:

<https://deb.debian.org/debian/pool/main/v/vulkan-validationlayers/vulkan-validationlayers_1.4.309.0-1_amd64.deb>

Expected size: **5,707,192 bytes**. Expected SHA256: `ff7e18ef011ff448ac799daf16134a676ccf9c5987e1a9f4b779611ed5fc3b0d`. These are supplied pins, not a completed download verification. No Debian signature verification was performed, no authentication metadata was fetched, and no public keys or credentials were exported or persisted. The draft only inventories available authentication tooling; implementing an available signed Release-to-Packages-to-deb verification chain remains required before any signature claim.

The staged scripts express the requested small envelope: 1 CPU, 512 MiB memory and equal memory-swap, PID cap 128, read-only root, network none, 16 MiB tmpfs, core ulimit zero, core filter 0x10, no devices or Docker volumes. They inspect actual container configuration before starting. Runtime loading uses the bundle read-only and the admitted runtime read-only at both `/soft` and `/out/runtime`. None of that envelope has been exercised by this task.

## Qualification and capture coverage gaps

All of the following remain **unverified**:

- Exact HTTPS package bytes and SHA256; Debian signature chain.
- Archive path safety, data-only extraction, original manifest and copyright retention/hashes.
- Original manifest settings names/types, core and synchronization validation configuration.
- Actual runtime13 glibc, libstdc++, loader versions and all ELF/versioned dependencies.
- Six admitted runtime file hashes before and after loading.
- Layer enumeration, version, loading, explicit enablement, and valid Vulkan 1.2 CPU device creation.
- Loader/debug-utils/validation output, warning/error counts, callback selftest, resource/OOM receipts.

`probe.c` is designed to request the exact layer in `VkInstanceCreateInfo`, capture creation/destruction messages, enumerate the CPU device and driver identity, create one device, and verify the loaded layer's negotiation symbol using `RTLD_NOLOAD` plus process maps. It creates no images, buffers, command pools, pipelines, queues of work, or draws. Its manual debug-utils message is labeled capture-only and would provide no VUID negative-control evidence.

No verified settings file or loader recipe was generated because the package's original manifest was never acquired. The unexecuted container draft gates `validate_core` and `validate_sync` on the original manifest's documented BOOL keys before writing a settings file; those names must not be treated as verified from this report. Later engine admission needs a qualified settings file, exact loader environment, original/derived manifest hashes and semantic diff, dependency evidence from runtime13, and real enablement/callback receipts before capturing actual engine messages. Zero messages from the present task establish nothing about API validity.

## Cleanup and handoff

The failed host process exited, `failure.json` has an empty owned-container list, and execution never reached container creation or the download worker. No owned background helper was started. No deletion, stop, restart, system installation, image build, apt operation, or non-owned write was performed. Existing sampler/exporter/Android processes were left running.

`handoff.json` records the terminal state. `artifact-hashes.json` hashes every owned file except itself; it also records aggregate bytes. Only this new directory was written. Return to the parent for resolution of the inventory admission before any further preparation or test admission. There is no qualified validation-layer bundle to use yet.
