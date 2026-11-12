Golden descriptor-1 physical page-tree variant, 28 October 2026.

New QEMU: `/work/orchard-m27-pages/artifacts/qemu-system-aarch64`

SHA-256: `b4b7e761567f4dcdf28dc88c15aa7446426884b3c13ee7b6e1deac6ebfddf0f5`

New archive SHA-256:
`62e21367f1d7f20de6b4a8fd0b507fbed24b1d008367b11d77c466ead7943497`

The admitted producer register layout now selects a typed page contract stored
with the mapping. Descriptor 1's physical root is decoded through its bounded
span and H/T/N topology; head and leaf entries, RAM bounds, coverage and address
provenance are checked. The old pointer-holder layout remains explicit and
unchanged. Descriptor 2 is refused by name. No CPU-context bypass was introduced.

Independent source review found a stale cached-plan path after semantic
descriptor refusals. A new regression reproduced the incorrect acceptance before
the correction. Only NoCpu/Unmapped alias loss may preserve an already validated
plan; semantic refusal now fails revalidation and retires stale pages.

Final offline validation: formatting passed; 398 protocol, 54 mapper, 82 model,
86 objects and three admission tests passed. GPU-touching tests ran serially.
The first model run lacked the QEMU source fixture; the isolated source now
points to the same unchanged QEMU source used by its existing compiled objects.
The initial failure and before-fix regression evidence are retained separately.
Two existing Rust atomic deprecation warnings remain; no warnings were suppressed.

The original QEMU binary and original source tree were verified unchanged. Only
the disposable Cargo target cache was reused. Its original static archive was
copied to `artifacts/libreims_vgpu.admitted-m27.a` before reuse. Ninja expanded its
link command; the output and static-archive arguments were redirected to the new
artifact directory. No original QEMU object or binary was rebuilt/overwritten.
Copied sources were checked against their recorded hashes after copying.

Build limits: offline, four CPUs, 4 GiB memory/equal swap, PID limit 256, 64 MiB
temporary filesystem, 25-minute deadline, bounded logs and owned-process cleanup.
Fresh host-space samples enforced the unconditional 10 GiB floor. The successful
build's minimum observed free space was 13,322,756,096 bytes.

CONTROL admission changed only qemu_sha256, with atomic replacement, backup and
readback. AUX SHA-256 remained
`b4c1b7e9bf845f0568d6538431f4d81e11a691882bc4903272d5ed6bd4675f6f`;
overlay remained
`23f9f4f4e3d1f2e2c5afebd9a4a0dc2df4881ed1ad8ddd442811480c26a46d32`.
Migration did not launch a VM or modify guest data.

Live gate: one bounded 900-second local-RAW boot with the existing owned frame
capture. Require nonempty mapper page plans before crediting the ABI change.
A graphical desktop remains unverified. The prior trace also independently
requires memoryless attachment support: exact guest evidence identifies tag 9
as memoryless texture, while mapper-ref textures remain tag 11. It must not be
retagged or given fabricated guest pages. Other format/compute/shader refusals
remain compatibility work after backing qualification.
