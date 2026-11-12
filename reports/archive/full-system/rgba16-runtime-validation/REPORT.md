# RGBA16 native runtime qualification and isolated build

**Two distinct actual-loader baseline RED cases; 105 GREEN test invocations; both strict software-Vulkan cases passed; separate release archive and emulator built.** No VM or guest input. This does not establish guest acceptance, a rendering fix, or a usable Golden desktop.

## Artifacts

- `/work/orchard-m27-pages-rgba16/artifacts/libreims_vgpu.a` — 174,892,356 bytes; SHA256 `4ed34bcbca161a6b0e06df39c6ad13196ed691cbf69c9ce0b583b313ae64da99`
- `/work/orchard-m27-pages-rgba16/artifacts/qemu-system-aarch64` — 70,844,192 bytes; SHA256 `553102765a9da19efee87112f85190835d7d0bc3ca0e55539c375f948e302bfe`

Matching host copies are in `artifacts/`; hashes and sizes are in `pin-manifest.json`. The sole expanded `ninja -t compdb -x c_LINKER_RSP` QEMU row was linked with exactly two argument substitutions: executable output and Rust archive. Existing QEMU objects were reused. `qemu-version.log` records only `--version`. Linux-targeted locked/offline Cargo metadata proved the unchanged pinned local compiler; the broken host-target metadata route was not run.

## Runtime RED/GREEN

The unchanged RGB10 baseline already contained the cfg(test) capability seam. Only a separate RGBA16 fixture module was appended. Both real `load_buffer_texture_upload` cases first failed: `fmt=0x6e 384x384` and `fmt=0x6e 17x9` appear in `baseline-red-confirmed-fail-channel.log`. The frozen two-file delta was then copied byte-exact. No production correction was needed or made.

| Focus | Passed |
|---|---:|
| frozen-runtime-tests | 16 |
| actual-runtime-integration | 7 |
| rgb10-regression | 4 |
| buffer-read-debt | 1 |
| buffer-texture-debt | 1 |
| writeback-debt | 20 |
| settle-site | 1 |
| shader-cache | 44 |
| shader-capture | 10 |
| buffer-descriptor | 1 |

GREEN actual-loader output: 384×384, pitch3072, offset0, 1,179,648 native bytes; and 17×9, pitch160, offset48, 1,224 native bytes. Metadata names R16G16B16A16_UNORM, source ordinal110, eight bytes/texel. Actual returned vectors, source-before/after, geometry and SHA256 provenance are retained separately for both. Prefix, every row padding and tail remain unchanged; after guest-memory overwrite the returned bytes remain owned. Saved-extent counters prove exact final-row spans. Negative capability and one-byte-short allocation tests refuse through native typed branches without old-loader fallback. RGB10 and old RGBA8 behavior pass.

The RGBA16 fixture consults both real named debts 64 times: 128 generation-guard refusals, exactly one real source census, unrelated debt retained, current guest bytes unchanged. It also invalidates the actual source PTE and requires the next loader call to refuse rather than return stale upload data. Existing debt/resource-generation and settle regressions pass. **No successful resident debt landing or pending GPU-fence completion was established.**

## Strict GPU result

- 384: 147,456 pixels / 589,824 channels; max error 2.32834196368e-10; per-channel minimum adjacent gaps `[1.52587890625e-05, 1.52587890625e-05, 1.52587890625e-05, 1.52587890625e-05]`.
- odd: 153 pixels / 612 channels; max error 2.32834196368e-10; per-channel minimum adjacent gaps `[1.52587890625e-05, 1.52587890625e-05, 1.52587890625e-05, 1.52587890625e-05]`.

All channels are finite and within 1e-6 of u16/65535. Every channel checks adjacent pairs 0/1, 2/3, 32767/32768 and 65534/65535 with ordered gap ≥1/65535−2e-6. Authored Vulkan1.2 SPIR-V passed validation. The oracle consumes hashed actual runtime output, copies rows without conversion, queries R16G16B16A16_UNORM sampled/transfer support and combined image usage, then uses texelFetch/nearest into f32 storage/readback. This proves native sample conversion; filtering was not tested. GPU upload prefix, row padding and tail and readback guardbands pass. Runtime source guardbands and hashes are checked before and after both serial GPU cases.

Only pinned Mesa26 software Vulkan ran: CPU device, LP128, two threads, GPU container2 CPUs/2GiB/no extra swap/pids128. Driver and LLVM pins are in `gpu-environment.json`. No hardware GPU or Android interaction occurred.

## Preservation and resource evidence

All13 host pins, 424 baseline Rust/manifest/lock pins, the complete baseline source snapshot, 618 pinned compiler files, and 8 admitted archive/executable hashes match afterward. The RGB10 executable and archive retain their admitted hashes and sizes. The source copy excludes .git/target recursively and preserves symlinks. `owner.patch` is the exact production delta; `integration-only.patch` is the separate fixture module declaration plus test file. Qualified whole-tree pins include symlink identities. No graph coverage is claimed; graph tools were absent and exact-source fallback was used.

Allocation admission reserved 1,723,156,861 bytes against 3,256,442,880 bytes above the floor, including finite cache growth and volume/host final artifacts. The existing Cargo target was reused, not duplicated or deleted. Final measured allocation is in `allocation-final.json`.

Actual cgroup peaks: builder 2,919,993,344 bytes; GPU 130,183,168 bytes. Memory max/OOM events:0. Builder4CPUs/6GiB/no extra swap/jobs2/pids256. Actual Docker admission and cgroup readbacks are retained, including networknone, read-only root, tmp64MiB, core ulimit0 and inherited core filter0x10. Minimum host free 13,230,284,800 bytes stayed above the unconditional10GiB floor; fresh samples used age[-2,20]s, poll target0.2s. Longest command 187.03s <900; GPU 4.07s <300; guarded active total 522.62s <2400. Host evidence excluding final artifacts 8,679,193 bytes <64MiB. Actual observed poll gaps are in the receipts; hashing/scheduling can exceed the target interval.

Owned containers auto-removed; cleanup receipts and postflight confirm all89 original container IDs /28 volumes and pinned sampler, exporter and Android identities. Existing services, backends, apps, databases, admitted sources, artifacts and QEMU objects were not restarted, reset or changed. No CONTROL/RAW/NBD/state mounts, guest filesystem reads, profile migration, guest input, VM launch, delegation, commit or push.

Three harness corrections are retained transparently: UTC comparison normalization (`harness-time-comparison-error.json`); separate test fail-channel capture after an initial parser assertion stopped before applying production files; and Cargo mtime invalidation after copy2 caused stale baseline binary reuse. The stale results are explicitly prefixed `stale-cache-` and excluded from GREEN counts. Only two owned source mtimes changed; frozen byte hashes remained exact. No guard/resource/OOM/actual identity failure was retried. Existing deprecation warnings were retained.

## Handoff limits

The oracle composes actual runtime-loader output with a separate authored Vulkan sampler; it is not a runtime-engine draw, guest shader or Golden frame. Canonical live fmt0x6e refusals do not establish missing-button causality. Type2 linear RGBA16 with five mips, MRT, dualplane/type12, aggregate half loads and nested views remain outside this task. Return for parent review before any live case. Golden desktop acceptance remains unverified.
