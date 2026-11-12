# RGB10A2 runtime qualification and isolated artifact handoff

The frozen patch compiles in the full runtime. **92 tests passed** across the focused invocations, and the pinned Mesa 26 Vulkan oracle passed over the actual runtime-owned native bytes. A new isolated static archive and emulator were built and linked. No VM was started. The Golden Desktop goal remains incomplete; this build does not establish a rendering fix.

## New artifacts

- `/work/orchard-m27-pages-rgb10/artifacts/libreims_vgpu.a`: 174,891,956 bytes; SHA256 `fa8581e23cc7a136d7f0067cfa7fd05da65f5e53c201340ae3c4e2b9cfc63242`
- `/work/orchard-m27-pages-rgb10/artifacts/qemu-system-aarch64`: 70,844,192 bytes; SHA256 `87614fc2db5efc0f7293aad13d1f70ffd43d4e3e09380dfd5522ffd419d7202b`

`qemu-version.log` records only `--version`. `link-argv.json` records the exact original and qualified QEMU link arguments: exactly one `qemu-system-aarch64` row, with only its output and Rust archive path replaced. Existing QEMU objects were reused; no QEMU source or ABI was changed.

## Executed runtime tests

| Focus | Passed | Failed |
|---|---:|---:|
| frozen-runtime-tests | 10 | 0 |
| actual-runtime-integration | 4 | 0 |
| buffer-read-debt | 1 | 0 |
| buffer-texture-debt | 1 | 0 |
| writeback-debt | 20 | 0 |
| settle-site | 1 | 0 |
| shader-cache | 44 | 0 |
| shader-capture | 10 | 0 |
| buffer-descriptor | 1 | 0 |

The first full compilation used the exact frozen four-file overlay. The subsequent actual-loader tests call **load_buffer_texture_upload**, with real DeviceState, the existing FakeHost HostMemory/HostOps and page-table fixtures, actual resource descriptor lookup, actual named debt APIs and actual source reader. They do not adapt or duplicate the loader. All test invocations used `--release --locked --offline -p reims-vgpu --no-default-features --features backend-vulkan,host-window --lib` and `--test-threads=1`. Exact filters, commands, exits, logs and resource receipts are alongside this report.

The fixture is 106x106, source pitch512, offset64, allocation54400 and exact read span54184. The actual output is 44944 tight bytes. The actual reader's saved-extent counter is 152 bytes, proving exclusion of final row padding and tail. Every source prefix/padding/tail byte stayed unchanged; after overwriting guest memory, the owned upload still matched its independent expected words. Short allocation and unsupported capability controls refuse through actual loader branches without RGBA8 fallback.

Both named debts are taken by the actual ledger; unrelated debt remains. The generation guard declines landing because those fixtures deliberately omit a surface mapping, as the pre-existing debt regression does. The real 1/64 source-read census executes exactly once across 64 calls. The existing settle path executes with **no GPU write outstanding**. A pending GPU fence wait and successful resident-debt landing are **not verified** by these fixtures.

## Vulkan readback

The fixture emits its **actual returned upload bytes** before changing guest memory. `runtime-native.bin` SHA256 is `c311a35c9cdb9a3039e212e96caef4a4f021feafd54f7e6427e5bb0faa6b1540`. `gpu-admission.json` pins these bytes, geometry, authored shader, validated SPIR-V and probe executable. The oracle uploads those bytes to A2B10G10R10_UNORM_PACK32 and samples exact pixel centers with linear filtering into float32 RGBA vectors in a storage buffer.

All 11,236 pixels / 44,944 channels passed. Maximum absolute error was 5.10613123578e-06, against tolerance 2e-5. That bound accommodates float32 coordinate/division and interpolation error and remains over 48 times smaller than one 10-bit UNORM step; it cannot hide an 8-bit reduction of the authored R=1,2 values. Observed red values were 0.000977517106 and 0.00195503421; alpha was 0.333333343 and 1. Unequal R/G/B fields and every alpha/channel were checked. Guest-source guards, upload/readback guards and admitted input hashes stayed unchanged.

The actual format query passed SAMPLED_IMAGE, FILTER_LINEAR, TRANSFER_SRC, TRANSFER_DST and the combined image-usage query. Shader compilation and `spirv-val --target-env vulkan1.2` passed before execution. Only authored shader code executed.

The runtime image was `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`; Mesa runtime-26 was mounted RO at both `/soft` and `/out/runtime`. Driver SHA256 `9a805a2e19312658ed9715d6bc2892770d7d160d0222b74f0b69aa72d07d3007` and LLVM SHA256 `f804d4247625bf0905c55655377618783ff3296a9c8aacdda9ac7cafa2e5e404` matched. The device was llvmpipe (LLVM 21.1.8, 128 bits); LP vector width128 / 2 threads, no hardware devices. No original Mesa25 experiment was needed.

## Pins, source and isolation

- Baseline: pinned non-Git copy `/work/orchard-m27-pages-io/reims-vgpu`, excluding target/.git and preserving symlinks without following vendor/qemu. The new variant did not exist before staging.
- All 421 admitted source pins, 618 vendored compiler pins, six protected archive/executable hashes, frozen inputs and the four original study owner files match after the build.
- Compiler: `/work/orchard-m27-pages-rgb10/reims-vgpu/vendor/metal2vulkan-io`. Root manifest SHA256 `e0e4c1fba85a506f757e521fef78d95a9ef55b1945e85eb22bd8153f2c7f5a9c` and lock SHA256 `53d2c510fa18ddb7a1c067b21a266e271bdd47030dfd0d6e30443b0b3eb29e65` remain unchanged. Cargo's selected package is a local path package with no source/checksum in the lock. No lock update, old translator switch, manual Git-cache change or network admission occurred.
- `owner.patch` / `owner-sha256.json` preserve the frozen delta. `integration-only.patch` separates the additional test capability seam and actual-loader tests. Release code still forwards to engine::supports_sampled_layout_bind. No other production behavior was corrected. `source/` contains the qualified owner files, fixture and authored oracle. `qualified-source-pins.json` and `pin-manifest.json` identify the resulting source exactly.
- The old RGBA8 loader is byte-identical between the actual admitted baseline and qualified copy (`unchanged-rgba8-proof.json`); raw function SHA256 `4ba0a8e6e3d05b2c1f592008402ba432e2d920c8fbb8562c829b6ae1d8bb51ca`. The exported/frozen/original copies also match.
- Structural exploration used exact-source fallback; no graph/index coverage is claimed.

## Commands, guards and preservation

Builder image `14ea78615d69de5eea70014968be23464751916c6c44793f19f5771a9b4eeb17`, Rust1.99.1 path `/work/rust/stable-x86_64-unknown-linux-gnu/bin`, CARGO_HOME `/work/cargo`, CARGO_INCREMENTAL=0, jobs2, 4 CPUs, 6 GiB memory/equal total swap, pids256. GPU: 2 CPUs, 2 GiB/equal total swap, pids128. Both: read-only root, network none, tmp64MiB, core ulimit0 and core filter16 with readback/inheritance checks. The normal disposable Cargo target was recreated only at `/work/orchard-m27/reims-vgpu/target`.

The fresh unconditional 10 GiB floor stayed clear: minimum sampled free bytes 14,171,820,032. The child monitor polls every0.2s (receipt maximum-gap fields can also include pre-command pin hashing). The full frozen compile's observed interval maximum was 0.216s; the actual integration compile's was 0.252s. Builder peak memory was 3,375,886,336 bytes; GPU peak 122,138,624 bytes. No OOM events, guard-floor failure, memory increase or resource/OOM retry occurred. Longest command 313.07s <900; total guarded action time 786.56s <2400; GPU 3.35s <300. Builder logs stayed below16MiB and GPU log below2MiB. GPU owned outputs were 1,377,186 bytes <64MiB; the RO `/out/runtime` input libraries were excluded.

The initial metadata failure is retained: my unrestricted `cargo metadata --locked --offline` tried resolving uncached macOS `block 0.1.6` and exited101. The corrected query added the tested Linux target/features and passed, before the release build. No dependency, lock, resource or network setting changed. Existing Rust deprecation warnings were retained, not weakened. Postflight timestamp comparison also required explicit UTC normalization after two shell comparison/parsing errors; both original records are retained as `host-postflight-timeparse-error*.json`. The sampler's actual start timestamp matched; no process was restarted.

Owned containers auto-removed and their tmpfs was discarded. New source, evidence, artifacts and the allowed disposable Cargo target are retained. `host-postflight.json` records the original sampler and Android process identities and absence of owned containers. No existing exporter/backend, launcher, service, storage, admission, identity, original source tree, admitted binary, interactive adapter, CONTROL/RAW/state volume, profile, guest filesystem, input or trace configuration was changed. No commit/push/delegation occurred.

## Limits and next handoff

The specified bounded gzip has 17 direct RGB10A2 refusals, including native LF4584, and no matching raw opcode9 descriptor blob; the actual live descriptor's full shape acceptance remains unverified. `live-log-evidence.json` retains the compressed hash and exact refusal rows. No descriptor was invented, inferred from length or allowed by loosening rejection.

This is composite runtime-byte / Vulkan sampling proof and an isolated artifact build. It is not a runtime-engine draw or a Golden frame. Pending GPU writeback fence completion, actual Golden rendering and border/button/icon causality remain unverified. MRT attachment1, dual-plane tag12/privatefmt226, nested opcode9 view dispatch and aggregate pointer loads remain out of scope. Parent review must precede any profile migration or bounded live case. The broader Golden Desktop goal is not complete.
