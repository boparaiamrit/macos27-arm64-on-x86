# Reims vGPU on this PC's GPU: Mesa Dozen (Vulkan on Direct3D 12) through WSL

**Status, R12-gpu, 2026-10-29 16:50 UTC (details in §11).**
- **Framebuffer fetch without ordered access: implemented.** On devices without `VK_EXT_rasterization_order_attachment_access`, such as Dozen, a draw that reads its own colour attachments is now recorded one primitive at a time, with the render pass's own fetch barrier between primitives. That is exact, and it is gated on the capability, not a name.
  - Where splitting would be observable, the draw gets one of four typed refusals: a split-observable built-in, strip facing, wireframe, or more than 4096 draws.
  - On Dozen, the 10 MRT engine oracles now pass, including two overlapping triangles in one draw (maximum error 1/255), and 36 of the 38 earlier colour-input failures are gone.
  - All 46 colour-input draws refused in the R10b GPU boot fit the rung's structural conditions.
- **Texture access: not Dozen-specific, not fixed.** The 24 are draws skipped behind one refused pipeline that reads a fragment *storage* texture. Lavapipe refuses the same shape. Reims's render path has no storage-texture binding. A design is in §11.4.
- **R12-gpu artifacts** (R10b + host-allocation gate + the rung), linked like `m2v_run.py r10_link`, not booted:
  - `/work/gpu-dzn/artifacts/qemu-system-aarch64`, sha256 `db5cf415bcf40d68ae4bfb5e014ea910bcec24a77130f69450baade671b69edb`;
  - `libreims_vgpu.a`, sha256 `b4b77adf…3fac3`.
- **Tests, final bytes:**
  - **Dozen** 590 passed / 7 failed. The failures are host-capability fixtures: 2 need a feedback loop, 5 need a native host import.
  - **Lavapipe** 597 / 0.
  - Both runs: 0 validation messages (Core+SYNC).
  - rustfmt is clean, and clippy reports no warning from the patch.

**Earlier status (R10), 2026-10-29 15:25 UTC.** Route (a) works. Inside a Docker Desktop container, Reims binds the
**NVIDIA GeForce RTX 5070 Laptop GPU** through Mesa 26.2.5 Dozen, which is the same Mesa build as the
admitted Lavapipe. Reims needed one structural fix: a query that named a handle type the device lacks,
now gated test-first and passing fmt and clippy. The driver stack needed one environment fix
(`LD_PRELOAD` of the D3D12 runtime).

With the fixed binaries, R9's test set on the GPU gives **512 passed, 43 failed, 0 validation messages
(Core+SYNC)**. All 43 failures are typed capability refusals for two features Dozen does not have (see
the gap table). The biggest is **ordered colour-attachment access (framebuffer fetch)**, which has no
Reims fallback. Both boot launchers have a `-VulkanDriver gpu` option, and the default stays Lavapipe
with byte-identical `docker run` arguments.

**No boot was performed.** Host C: free space fell below the 10 GiB floor at about 15:06 UTC (see
"Disk event"), and the parent then ordered no boots. So no speed figure exists yet.

## 1. Route chosen and why the others failed

| Route | Result |
|---|---|
| **(a) Docker Desktop GPU + Mesa Dozen** | **Works; chosen.** Uses `--device /dev/dxg` plus read-only binds of the Docker VM's `/usr/lib/wsl/lib` (`libd3d12.so`, `libd3d12core.so`, `libdxcore.so`, NVIDIA D3D12 UMD `libnvwgf2umx.so`) and `/usr/lib/wsl/drivers` (the driver store the D3D12 runtime resolves the UMD from). `--gpus all` is not used. Docker's `nvidia` hook exposes `/dev/dxg` but mounts only CUDA/NVML files, not the D3D12 libraries (console-only probe at 14:12; `nvidia-smi -L` saw the RTX 5070). |
| (b) NVIDIA Vulkan ICD for WSL2 | **Not shipped by this driver** (Windows 32.0.16.1656; Linux side `libnvidia-gpucomp.so.615.65.06`). The driver store `nvaci.inf_amd64_b9b853632e3b644f` has CUDA, NVML, NVENC/NVDEC, OptiX loader, NGX and the D3D12 UMD. It has no Vulkan ICD JSON and no Vulkan library. |
| (c) Intel GPU through D3D12 | Available: Dozen enumerates `Microsoft Direct3D12 (Intel(R) Graphics)` (0x8086:0x7d67, integrated, 1.2.354). **Not selected and not separately qualified.** Reims ranks discrete (4) above integrated (3), and no device filter is installed. |

**Adapter selection.** `MESA_D3D12_DEFAULT_ADAPTER_NAME` **has no effect on Dozen**. With `NVIDIA`,
`Intel` or unset, it enumerates the same two adapters in the same order (`logs/vulkaninfo-vulkaninfo.json`).
That variable belongs to the Gallium d3d12 (OpenGL) driver. The adapter is chosen by Reims's own
`caps::device_select::rank_physical_device` (discrete > integrated > virtual > CPU).

**Verified from the loader log:** all **52** device creations in the final qualification used
`"Microsoft Direct3D12 (NVIDIA GeForce RTX 5070 Laptop GPU)" with driver
"/opt/gpu-dzn/lib/libvulkan_dzn.so"`.

## 2. Image

New image `gpu-dzn-runtime:mesa26.2.5-dzn`:
- **image ID `sha256:4f0f2b29f77de8388c712f9200a68566a7ee040a3f479441594fc71c02822e70`**
- config `sha256:94854379ad1c33ece0ea82aa65e5473f17d560024253c5d7b8522fd8a46f3109`
- manifest `sha256:5c1faccc46fa18184d2f1d28f6b8944dc2700de6978c7ddc9039d04d1a74c012`

It is built `FROM` the pinned runtime image `sha256:13d68aa0…dc50635`, and all 12 base layers were
verified identical. Three layers are added, all under `/opt/gpu-dzn`. Unique size is **15.87 MB**; the
other 2.531 GB is shared with the pinned image. Built with `--network none` (`image/Dockerfile`,
`logs/image-build.log`). The pinned runtime and builder images are unchanged.

| File | SHA-256 | Source |
|---|---|---|
| `lib/libvulkan_dzn.so` | `a09f72ab32be4fdbbfe8a08db6f79cc44daf9ff93622d7a924acf585d347eddf` | `mesa-vulkan-drivers_26.2.5~kisak1~n_amd64.deb` (`833b3e0d…`, already on disk). The same .deb's `libvulkan_lvp.so` was asserted equal to the admitted runtime-26 Lavapipe `9a805a2e…`. |
| `dzn_icd.json` | `3b8defde80dc39afc8f1c09da7b1ecceabf79955ed9664e122ff2f6323155a9e` | The package ICD with an absolute `library_path` |
| `lib/libdrm.so.2`, `lib/libdisplay-info.so.1` | `0603c4dc…`, `2b42e262…` | Byte-identical to the runtime-26 pins |
| `bin/vulkaninfo` | `f850851cd176c646851f42287902d5ee737849f275c1a64cb319b4985bdfbb4c` | `vulkan-tools_1.3.275.0+dfsg1-1_amd64.deb` (`994e429b…`, on disk) |

Provenance is recorded in `logs/image-inputs.json`.

## 3. vulkaninfo summary (GPU 0)

From `logs/vulkaninfo-full-nvidia-stdout.log` and `logs/formats2-formats.json`.

- **Device:** `Microsoft Direct3D12 (NVIDIA GeForce RTX 5070 Laptop GPU)`, 0x10de:0x2d58, DISCRETE_GPU, **apiVersion 1.2.354**, driver Dozen, "Mesa 26.2.5 - kisak-mesa PPA", conformance 0.0.0.0. Dozen prints "not a conformant Vulkan implementation".
- **Extensions:** 48 device extensions.
- **Memory:** heap0 47.43 GiB host; heap1 7.71 GiB DEVICE_LOCAL; no host-visible device-local type, so the topology is `discrete`.
- **Queues:** family 0 is graphics/compute/transfer ×4; family 1 is compute/transfer ×8.
- **Limits:** maxColorAttachments 8, maxImageDimension2D 16384, maxComputeSharedMemorySize 32768, maxComputeWorkGroupInvocations 1024.
- **Timing:** the first instance takes about 3.0 s (D3D12 init); later instances about 1.0–1.2 s.

## 4. Feature gaps against what Reims needs

Every row is gated structurally in Reims (`caps::device_features`, `caps::host_pointer`, `caps::push_descriptor`).

| Capability | RTX 5070 / Dozen | Lavapipe 26.2.5 | What Reims does on Dozen |
|---|---|---|---|
| API version | 1.2.354 | 1.4 | Accepted: the floor is 1.2 (`caps::api_floor`) |
| robustBufferAccess | yes | yes | Enabled |
| robustImageAccess (`VK_EXT_image_robustness`) | **no** | Core13 | Reported `image_robustness=Unsupported`. Metal's out-of-bounds texture-read guarantee is not promised on this host; no fallback, logged by design. |
| shaderFloat16 / storageBuffer16BitAccess | yes / yes | yes / yes | Enabled; native fp16 reported to the guest |
| storageInputOutput16 | **no** | yes | No gate in Reims. A translated module declaring `StorageInputOutput16` would be invalid usage. **Unverified risk**; seen only on a live boot. |
| storageBuffer8BitAccess / shaderInt8 | **no / no** | yes | Same class. `api_floor.rs` says decoding needs 8-bit storage. **Unverified risk.** |
| shaderOutputViewportIndex / Layer | **no** | yes | Same class. **Unverified risk.** |
| External host-memory import (`VK_EXT_external_memory_host`) | **no** | yes | `host_pointer_import=no_host_pointer_extension`, so the copying rails are used (designed fallback). The 5 import-fallback fixtures are not applicable. |
| Timeline semaphores | yes | yes | Stamp-completion rail active |
| **Ordered colour attachment access** (`VK_EXT_rasterization_order_attachment_access`, Metal framebuffer fetch) | **no** (no ARM alias, no `fragment_shader_interlock`) | yes | R10/R10b: **no fallback**; `color_input::OrderedColorInputs::admit` refuses `color_input_ordered_access_unavailable`, and every guest draw that reads its colour attachments is dropped. **R12-gpu: an exact per-primitive rung, with typed refusals where splitting would be observable (§11.1).** |
| Push descriptors | no | yes | Descriptor-set fallback |
| Extended dynamic state 1/3 | no | yes | Pipeline variants (fallback) |
| Attachment feedback-loop layout | no | yes | Snapshot-copy rail (fallback) |
| Vertex attribute divisor | **EXT only** (KHR absent) | KHR | Reims asks for the KHR name only, so the divisor rail is off. A small structural follow-up could accept the EXT spelling. |
| dualSrcBlend / multiViewport / wideLines / logicOp | no | — | Declined by name per pipeline or draw |
| timeline, descriptorBindingPartiallyBound, samplerMirrorClampToEdge (Core12), BC compression, depthClamp, independentBlend, int64, fragmentStoresAndAtomics, storage read/write without format | yes | yes | Enabled |
| **RGBA16Unorm** (also RGBA16F, RG16, R16, R32F) | Optimal: sampled, **linear filter**, colour attachment and blend, **blit src/dst** (mip generation), storage, transfer | yes | Supported |
| **BGRA8 Unorm** (sRGB) | All of the above plus storage (sRGB has no storage) | yes | Supported; BGRA storage composite available |
| **RGB10A2** (`A2B10G10R10`) | Full optimal support | yes | Supported |
| BGR10A2 (`A2R10G10B10`) | **No features at all**; D3D12 has no BGR10A2 | yes | The capability probes mark the layout false. Sampled binds decline by name; render targets fall back to the 8-bit resident (fidelity loss). |
| Linear-tiled images | Transfer only | sampled | The report-only alias probes read "not sampled"; not used for rendering |

### Driver-stack defect found and worked around

Dozen `dlclose`s the D3D12 runtime at `vkDestroyInstance` while D3D12 worker threads are still alive.
Those threads then execute unmapped code. Under gdb the crashing thread's PC is in no mapped object,
with and without the validation layer (`logs/d1-val-stdout.log`, `logs/d1-noval-stdout.log`).

Every GPU test process crashed at teardown with SIGSEGV. WSL wrote two 84 MB crash dumps at 14:28 UTC;
they were deleted at 15:12 after diagnosis.

With `LD_PRELOAD=/usr/lib/wsl/lib/libd3d12core.so:/usr/lib/wsl/lib/libd3d12.so:/usr/lib/wsl/lib/libdxcore.so`
(preloaded objects are never unmapped), the same test passes and exits normally (`logs/d1-preload-d3d12-*`).
The test harness and the boot wrapper both set it, for QEMU and test processes only.

## 5. Reims GPU tests: real GPU against Lavapipe

Harness: `scripts/gpu_run.py tests`, the same group definitions as R9 (`mrt-memory-release-validation/green-run.py`),
`--test-threads=1`, Khronos validation `VK_LAYER_KHRONOS_validation` with
`validate_core = true` and `validate_sync = true` from R9's pinned bundle. Logs are classified with
R4's regex.

| Run | Binaries | Driver | Groups OK | Tests passed / failed | Validation messages | Notes |
|---|---|---|---|---|---|---|
| R9 receipts (`../mrt-memory-release-completion-r9/REPORT.md`) | R9 | Lavapipe | 71/71 | **567 / 0** | 0 VUID, 0 SYNC | 44 API-clean 20×20 pixel oracles pass |
| `t1-regressions` (RED evidence) | R9 | **Dozen** | 15/17 | 219 in 15 groups; 2 groups crashed | **16× `VUID-VkPhysicalDeviceExternalImageFormatInfo-handleType-parameter`** | No `LD_PRELOAD`; SIGSEGV at teardown in `indexed-owner` and `descriptor-arena` |
| `t2-core` + `t3-rest` | R10 + fix | Dozen | 35/70 | 512 / 43 | **0** | Idle host |
| **`q-dzn` (final)** | **R10 + fix (final bytes)** | **Dozen** | **35/70** | **512 / 43** | **0 VUID, 0 SYNC-HAZARD** | 52 device creations, all on the RTX 5070 |

Final per-family results on Dozen (`logs/q-dzn-results.json`):

- **regressions 237/237**: engine-exec 58, shader-cache 48, native-format 16, rgba16-actual-runtime 7, rgb10-actual-runtime 4, device-features 22, indexed-owner 7, descriptor-arena 11, and the rest.
- **resource 220/220**: resource-pools 171, slab 22, linear-import 12, host-imports 9, buffer-slab 6.
- **new 19/19**: core handoff 6, queue-owner 11, the 2 multithreaded ring-fence GPU tests.
- **pure 32/32**.

Failures, with the panic message of each in `logs/r10final-dzn-*-stderr.log`:

- **38 refused as `Unsupported(ColorInput(OrderedAccessUnavailable))`**: MRT engine parity 10, mixed 2, R3 extra cases 22 of 24, memory controls 4. The R3 msaa-refusal cases and the dedicated-live/retired controls pass. The `resident-depth-retention` control expected a `PassChurn` refusal and got the earlier colour-input refusal from the same request.
- **5 import-fallback fixtures**: these qualify the native host-import rail, which this device does not have (`Unsupported { rung: NoHostPointerExtension }`, `qualified native host import required`).

**Pixels.** Every 20×20 oracle draw in R9's audit lives in the fixtures that stop at those two refusals,
so **no non-warm-up oracle was reached on the GPU.** The only GPU readbacks are the 8
`import-fallback-warm` renders. An independent audit of all 400 pixels (256 inner, 144 guard) gives a
maximum error of **0.5/255 against a 3/255 tolerance**, identical to Lavapipe's warm-up files. The bytes
differ only by UNORM rounding (63.75 → 64).

**Timings** (`seconds` in the results JSON) are dominated by process start and D3D12 device creation
(about 1 s), so they are **not** a rendering-speed measure. For example, resource-pools takes 6.4 s on
an idle-host Dozen run against 2.5 s for R9 Lavapipe. Runs during the 14:54 boot were 4–38 s.

## 6. Reims change (patch and tests)

`reims-host-allocation-gate.patch` (sha256 `08074acc…c4d7c3`, +128/−52, 4 files) applies to the R10 tree
`/work/orchard-m27-pages-m2v-prefix/reims-vgpu`. The file pairs, before → after:

| File | Before | After |
|---|---|---|
| `host_pointer.rs` | `7ae834072e2092af…` | `c2cac7ebf015e1b0…` |
| `linear_sampled.rs` | `3e0680f05ea817b6…` | `5a53f01ce4004dfb…` |
| `linear_target.rs` | `87632ee98354b872…` | `e0c29820efec00ea…` |
| `context.rs` | `7238a2720a0b8ebd…` (= R9) | `952f503b46c49257…` |

What it does:

- **Defect.** `caps::linear_sampled::report` and `caps::linear_target::report` ran at every device create and asked `vkGetPhysicalDeviceImageFormatProperties2` about `HOST_ALLOCATION_EXT` without checking that `VK_EXT_external_memory_host` is advertised. That is invalid usage on any host without the extension, and Lavapipe hid it by having the extension.
- **Fix, in the handle type's owner.** `caps::host_pointer::host_allocation_image_features` asks the question only when the extension that spells the handle type is advertised, the same gate `host_pointer::query` already uses for the buffer half. Both reports route through it, take the `has_device_extension` closure `context.rs` already holds, and add `host_pointer_extension=` to their log line. No name keys and no behaviour change on hosts that have the extension.
- **Test first.**
  - **RED:** the owner-level test `the_image_import_question_needs_the_extension_that_spells_its_handle_type` alone failed to compile (E0425, `logs/build-red-binaries.json`). The behavioural RED is t1's 16 VUIDs.
  - **GREEN:** the final build `logs/r10-final-build-binaries.json` (`reims_vgpu` `3b084ea0…`, `vk_engine_parity` `95a2c06a…`, `reims_vgpu_core` `e964ddbe…`) gives 0 validation messages on Dozen and the test passes inside `regressions`/`resource`.
  - **Lint:** `rustfmt --check` is clean on the 4 files. `cargo clippy --release -p reims-vgpu --lib --test vk_engine_parity` exits 0, with **no diagnostic in the changed files**; the 67 warnings elsewhere are pre-existing. The 4 compiler warnings are the same before and after.
- **Not in any QEMU build.** No admitted QEMU contains this fix. Without a validation layer, the old query returns from Dozen harmlessly (observed in t1), so it does not block a boot.
- **Staged copy:** `/work/gpu-dzn/reims-vgpu` holds R10 plus this patch; nothing outside `/work/gpu-dzn` was written.

## 7. Launcher wiring (and the exact command)

Both launchers gained `[ValidateSet('lavapipe','gpu')] $VulkanDriver = 'lavapipe'`. Backups of the bytes
before my edit are in `launcher-before/`.

| Launcher | Before | After |
|---|---|---|
| `mouse-guest/Launch-Rgba16MouseAttempt.ps1` | `81e8bdfb…` (the parent's 14:51 version) | `b8688de3b230ba0a…` |
| `local-raw/Launch-LocalRawAttempt.ps1` | `203fa061…` | `70bf66034534969…` |

`scripts/Test-LauncherArgs.ps1` evaluates only the argument-building statements, with no docker call
and no state file. It shows the **default `docker run` arguments are identical** (76 and 72 args). The
attempt record only gains `vulkan_driver`.

`gpu` adds exactly `--device /dev/dxg`, two read-only mounts (`/usr/lib/wsl/lib`, `/usr/lib/wsl/drivers`),
the GPU image, and the entry `/parent/full-system/gpu-dzn/run-gpu-attempt.py --entry mouse|frames`.

`run-gpu-attempt.py` (`4743f74d…`):
- loads the existing entrypoint unchanged;
- hands the runner a `subprocess` proxy whose `Popen` rewrites QEMU's environment only: Dozen ICD, `LD_LIBRARY_PATH=/opt/gpu-dzn/lib:/usr/lib/wsl/lib`, the D3D12 `LD_PRELOAD`, and drops `LP_*`;
- records what QEMU really received in `<attempt>/gpu-vulkan-environment.json`. The runner's own `command.json` still lists the Lavapipe values it built.

It composes with the parent's new `QemuEnvironment` (Lavapipe threads) shim. 5 offline tests pass
(`test_run_gpu_attempt.py`). `run-full-attempt.py`, `run-crypto-frames-attempt.py` and
`run-mouse-attempt.py` were **not** modified.

**Envelope checks.** The boot launchers contain none. The qualification launchers (`Launch-M2v.ps1`,
the R-round `Launch.ps1`, `Launch-Fence.ps1`) reject any `Devices`/`DeviceRequests` and were not
changed. This task's own `scripts/Launch-Gpu.ps1` relaxes the check **only for `-Gpu`**: exactly one
device `/dev/dxg`→`/dev/dxg`, still no `DeviceRequests`, `CapAdd` or privilege.

**Not yet done:** an in-container `-CheckOnly` of the GPU entry (it holds the guest volume) and a boot,
both because of the parent's hold.

Command to boot with the GPU, after the parent lifts the hold:

    & .\test-output\arm-macos\full-system\mouse-guest\Launch-Rgba16MouseAttempt.ps1 -VulkanDriver gpu -CheckOnly
    & .\test-output\arm-macos\full-system\mouse-guest\Launch-Rgba16MouseAttempt.ps1 -VulkanDriver gpu -QemuProfile m27-pages-fence -Smp 8 -ContainerCpus 12 -MemoryGB 12 -Timeout 900 -HookTimeout 800

`-VulkanDriver gpu` does not change input behaviour: this launcher sets `MOUSE_GUEST_INPUT=on` unless
`-CheckOnly`. `LavapipeThreads` and `LavapipeVectorBits` do not reach QEMU on the GPU route.

To compare against the about 95 s Lavapipe first draw, count `color_input_ordered_access_unavailable`
in `reims-vgpu-fail.log.gz` and read the `vk_caps` line, which should say `name="Microsoft Direct3D12
(NVIDIA …)" memory=discrete host_pointer_import=no_host_pointer_extension`.

On an R12-gpu build, that slug no longer exists. Count `color_input_unordered_` instead: each refusal
names its built-in or term. The census counter `color_input_primitive_draws` shows the split draws.

## 8. Measured speed

None. No boot was performed, for two reasons:
1. Until 15:04 the parent's guests were running (14:18 and 14:54 boots).
2. At about 15:06 C: free space fell below 10 GiB, and the parent's 15:12 order forbids boots.

## 9. Disk event (my share)

Timeline of C: free space:

| Time (UTC) | Free | Context |
|---|---|---|
| 14:44 | 26.05 GB | — |
| 14:50 | 23.2 GB | — |
| 14:50–14:58 | min 19.2 GB | My final 8 GB builder (6 CPUs); the parent's guest started 14:54 |
| 14:58–15:04 | min 11.26 GB | My `q-dzn` test run (4 GB, 2 CPUs) |
| 15:07 | **9.80 GiB** | — |

Most of the loss was **`C:\pagefile.sys` growing**. It is system-managed and allocated at 91.1 GB, with
21.6 GB in use (peak 23.5 GB). Windows grew it to raise the commit limit when commit reached
145.2 / 154.5 GB, with 922 processes holding 122.9 GB private and `vmmemWSL` at 23.4 GB.

My 8 GB build containers added to the WSL VM's commit at that peak. My GPU tests hold no host GPU
memory: no WSL process appears in the GPU commit counters.

I deleted my two WSL crash dumps (2 × 84.2 MB) at 15:12. After that I ran only two 1 GB, about 5 s
format queries (`formats`, `formats2`; free space was 11.2 GiB before each) and no builds.

## 10. What I hold, and what the remaining steps need

*This is a snapshot from the R10 work. Holdings after R12-gpu are in §11.6. The R10 copy listed here
was deleted before R10b was staged.*

| Held | Size |
|---|---|
| Image `gpu-dzn-runtime:mesa26.2.5-dzn` | 2.55 GB nominal; **15.87 MB unique** |
| `/work/gpu-dzn` in volume `macos-orchard-build` (R10 source + patch, a copy of R10's target, the test builds) | **2,126,606,512 bytes**; `target/release/deps` 1.84 GB |
| Host `full-system\gpu-dzn\` (`source-view` 19.2 MB, `image\ctx` 12.8 MB, logs 3.6 MB, patch tree 0.4 MB, scripts, `launcher-before`) | **39.6 MB** |
| Running containers | **none** (`gpu-dzn-*` all removed) |

Remaining steps and their disk:

| Step | Status | Disk |
|---|---|---|
| This report | Done | 0 |
| Optional: same-binary Lavapipe run of the final binaries | Needs parent OK | About 5 MB of logs; a 4 GB container (commit, no VHDX growth) |
| Optional: `-VulkanDriver gpu -CheckOnly` | Needs parent OK | KB |
| GPU boot | Needs parent OK | Same as any boot |
| Optional: rebuild the staticlib and relink QEMU with the patch | Needs parent OK | About 0.3–0.5 GB inside the VHDX; reuses blocks if superseded artifacts in `/work/gpu-dzn` are deleted first. Use ≤4 GB memory and 2 jobs to avoid commit spikes. |

## 11. R12-gpu: framebuffer fetch without ordered access, texture access, artifacts

**Source.** R12-gpu is three layers, staged in `/work/gpu-dzn/reims-vgpu` with its target seeded from
`/work/orchard-m27-pages-m2v-prefix2/target`:
1. R10b (`/work/orchard-m27-pages-m2v-prefix2/reims-vgpu`, authority `m2v-prefix-load/logs/r10b-final-source.json`);
2. the host-allocation gate from §6;
3. the per-primitive colour-input rung below.

`reims-r12-gpu.patch` (sha256 `eaffa35e5dcb120fb23c11853fa64e8de38e069d25884d51ea5323aea47ef391`, 57,025 bytes,
+894/−94, 10 files) applies to R10b. Every base file equals its R10b authority bytes. The staging
receipt is `logs/r12f-apply-apply.json`.

### 11.1 The per-primitive rung (framebuffer fetch on a device without ordered access)

**Contract.** A Metal fragment that reads `[[color(n)]]` sees every earlier write to its sample, both
from earlier draws and from earlier primitives of the same draw. Vulkan gives the in-draw half only
with `VK_EXT_rasterization_order_attachment_access`. Dozen does not have it (§4), so R10b refused every
such draw as `color_input_ordered_access_unavailable`.

**Mechanism.**
- **Choosing the rung.** `color_input::InputOrder::of(caps)` picks the rung once per device, from the capability `DeviceFeatures::ordered_color_attachment_access`; nothing is keyed on a device name.
  - `Rasterization`: the extension, unchanged behaviour.
  - `PerPrimitive`: no extension.
- **The split.** On `PerPrimitive` a draw that reads its attachments is recorded as one draw per primitive per instance. Each draw is preceded by an in-pass `vkCmdPipelineBarrier`: `COLOR_ATTACHMENT_OUTPUT`/`COLOR_ATTACHMENT_WRITE` → `FRAGMENT_SHADER`/`INPUT_ATTACHMENT_READ`, `BY_REGION`.
- **Why the barrier is valid.** That barrier is exactly the render pass's existing framebuffer-fetch self-dependency. `caches.rs` now builds that dependency from the same two constants (`INPUT_ORDER_SRC`/`INPUT_ORDER_DST`), so the in-pass barrier cannot leave the subpass's declared scope.
- **Why it is exact.** A point, a line segment or a filled triangle covers each sample at most once, so no fragment of a primitive reads another fragment of the same primitive. The barrier orders each primitive after every earlier one. This is rasterization order, spelled as barriers.
- **What a sub-draw preserves.** Each sub-draw keeps the original first vertex or index, the vertex offset and `firstInstance + i`, so `VertexIndex` and `InstanceIndex` are unchanged. The provoking vertex is unchanged too, because strip triangle *i* starts at vertex *i* either way. Primitive restart is always off in Reims.
- **When it is decided.** Admission is decided per draw, right after `OrderedColorInputs::admit` and before anything is recorded, so a refusal costs no GPU work.

**Typed refusals.** These apply only where the split would be observable. Each is a `ColorInputDecline` with a slug and fields:

| Slug | Fields | When |
|---|---|---|
| `color_input_unordered_builtin` | `builtin=primitive_id` | a module declares `PrimitiveId` and the draw splits into more than one draw (it restarts at 0 per draw) |
| | `builtin=base_vertex` | a non-indexed draw with more than one primitive declares `BaseVertex` (it follows each draw's first vertex) |
| | `builtin=base_instance` | more than one instance, and `BaseInstance` declared |
| `color_input_unordered_strip_facing` | `term=cull`, `two_sided_stencil` or `front_facing` | a triangle strip with more than one triangle where facing decides something; an odd triangle drawn alone has reversed winding |
| `color_input_unordered_wireframe` | — | triangles in line fill mode (two edges can cover one sample) |
| `color_input_unordered_split_limit` | `draws`, `limit=4096` | the split would exceed 4096 draws, or its ranges overflow |

A declared built-in counts as read. `spirv_bind::declares_builtin` scans both modules for
`OpDecorate`/`OpMemberDecorate BuiltIn`. A module it cannot decode answers "declared", so the draw is
refused rather than given a promise that can't be checked.

The old decline `OrderedAccessUnavailable` (`color_input_ordered_access_unavailable`) no longer exists.
A colour-input draw now takes one of the two rungs or gets one of the refusals above. A new windowed
counter, `color_input_primitive_draws`, is declared through `engine_counters!`, so it reaches the census
line through the generated `delta_fields`.

**Files.** All are under `crates/reims-vgpu/`:
- `src/backend/vulkan/engine/color_input.rs`: the rung, plan, barrier, declines and tests.
- `src/backend/vulkan/engine/exec.rs`, at two sites:
  - `primitive_shape` and the plan, right after admission;
  - the draw site, which loops over the planned draws.
- `src/backend/vulkan/engine/caches.rs`: the fetch dependency, built from the shared constants.
- `src/backend/vulkan/engine/counters.rs`: the counter.
- `src/runtime/spirv_bind.rs`: `declares_builtin`, the built-in ids and tests.
- `tests/mrt_order_gpu.rs`: the rung-aware check.
- The four host-allocation-gate files.

**`runtime/draw/vulkan.rs` (R11's file) is not touched.**

**Test first.**
- **RED:** `patch/r12-red` (the new tests, no implementation) fails to compile with 109 errors (E0425/E0422 on `DrawShape`, `PrimitiveSplit`, `SplitReads`, `PrimitiveDraw` and the built-in ids), in `logs/r12-red-build-binaries.json`. The behavioural RED is R10+fix on Dozen: 38 failures as `OrderedAccessUnavailable` (§5).
- **GREEN, unit tests:** `color_input::per_primitive_tests` (9, new), `mrt_order_plan_tests` (updated: a host without the extension now admits on the other rung) and `spirv_bind::builtin_tests` (2).
- **GREEN, engine oracles:** the MRT engine oracles in `tests/mrt_order_gpu.rs` now assert that the draw took the rung its device decides. The counter delta is 0 with the extension and equals the primitive count with the split. The pixel oracle is the same for both rungs.
- **Lint:** `rustfmt --check` is clean on the 10 files. `cargo clippy --release -p reims-vgpu --lib --test vk_engine_parity` exits 0 with 67 warnings, none from this patch (`logs/r12f-lint-lint.json`). The three warnings in changed files sit on R10b lines that the patch does not touch:
  - `exec.rs`: `chunks_exact_mut`;
  - `exec.rs`: `ad_hoc_attachment_views` has 8 arguments;
  - `mrt_order_gpu.rs`: `chunks_exact`.

  The first R12 lint (`logs/r12-lint-lint.json`) found 8 rustfmt hunks and one dead-code warning. Both were fixed, and every result below is from the fixed bytes.

### 11.2 Results with the final binaries (`r12f`)

**Binaries.** `logs/r12f-build-binaries.json`:
- `reims_vgpu` `ede3b075b2dff584…`
- `vk_engine_parity` `63cbcba9112ba18e…`
- `reims_vgpu_core` `e964ddbe…` (unchanged)

The compiler gives 4 warnings, all of which predate this patch; the `order` dead-code warning is gone.

**Harness.** The same harness as §5: R9's groups plus `r12-new`, `--test-threads=1`, and Khronos
validation with Core and SYNC enabled.

| Run | Driver | Groups OK | Passed / failed | Validation | Devices | Colour-input rung |
|---|---|---|---|---|---|---|
| **`q12f-dzn`** | **Dozen, RTX 5070** | **68/75** | **590 / 7** | **0 messages, 0 VUID, 0 SYNC-HAZARD** | 52 creations, all `Microsoft Direct3D12 (NVIDIA GeForce RTX 5070 Laptop GPU)` | `per_primitive` |
| **`q12f-lvp`** | **Lavapipe 26.2.5** | **75/75** | **597 / 0** | **0 messages, 0 VUID, 0 SYNC-HAZARD** | 52 creations, all `llvmpipe (LLVM 21.1.8, 128 bits)` | `rasterization_order` (unchanged) |

Per family on Dozen (`logs/q12f-dzn-results.json`):

| Family | R10 + fix (§5) | R12-gpu |
|---|---|---|
| regressions | 237/237 | 237/237 |
| resource | 220/220 | 220/220 |
| new | 19/19 | 19/19 |
| pure | 32/32 | 32/32 |
| **MRT engine oracles** | **0/10** | **10/10** |
| **mixed** | **0/2** | **2/2** |
| **memory controls** | **2/6** | **6/6** |
| **R3 extra cases** | **2/24** | **22/24** |
| import fallback | 0/5 | 0/5 |
| `r12-new` owner tests | — | 42/42 |

**What changed.** Of R10's 38 colour-input failures on Dozen, **36 now pass**.

The two that remain are the R3 `feedback-refusal` case (default and narrow). They now get past colour
input and stop at their own precondition: "host feedback support required for this admitted case". Dozen
has no attachment feedback-loop layout (§4).

The 5 import-fallback fixtures are unchanged. They assert a unified-memory host with a native host import
(`left: Discrete, right: Unified`, or `Unsupported { rung: NoHostPointerExtension }`). Neither the
`r12-new` group nor any other group fails on Lavapipe.

**Pixels.** The 24 MRT pixel oracles per driver (20×20, 256 inner and 144 guard pixels each) all pass
with a **maximum error of 1/255** against a tolerance of 3/255, on both rungs. That includes `overlap`:
two overlapping triangles in **one** draw, where the second reads what the first wrote. It ran as two
primitive draws on Dozen and one ordered draw on Lavapipe.

The secondary-LOAD refusal test still gives its typed refusal (`vk_draw_exec_load_secondary_content_not_ready`).

**The earlier R12 bytes, before rustfmt.** `q12-dzn` gave 548/7 on the same 70 groups and `q12-lvp` gave
555/0, both with 0 validation messages. `q12n-*` gave `r12-new` 42/42 on both drivers. They agree with
the final run.

### 11.3 Guest-relevant cases covered

The R10b GPU boot `20261029T152916Z-47419j9y` refused 12 pipelines at their first colour-input draw. It
then skipped **46 draws** behind those refusals.

The 12 refusal lines record the whole draw:
- every one is single-instance, indexed with 16-bit indices, first index 0;
- 11 are triangle lists, and pipe 77 is a triangle strip.

The skipped-draw lines record only the pipeline and the element count:

| Shape (from the pipeline's refusal line and the skipped draw's count) | Draws | Primitives each | Primitive draws |
|---|---|---|---|
| Triangle list, 6 elements (9 pipelines) | 33 | 2 | 66 |
| Triangle list, 24 elements (pipes 43, 88, 180) | 8 | 8 | 64 |
| Triangle list, 168 elements (pipe 43) | 1 | 56 | 56 |
| Triangle strip, 4 elements (pipe 77) | 4 | 2 | 8 |
| **Total** | **46** | | **194** |

**All 46 fit the rung's structural conditions.** At most 56 primitives against a limit of 4096, and
the strip is the only topology with a facing condition.

The log does not record what still decides each draw:
- a declared `PrimitiveId` (every one of the 46 has more than one primitive);
- `BaseVertex` on a non-indexed draw, or `BaseInstance` with more than one instance (the refusal lines show neither shape);
- line fill mode on triangles;
- for the four strip draws, cull mode, two-sided stencil and a `FrontFacing` read.

A draw that one of these refuses now names its cause with the slugs above, instead of the old blanket
refusal.

### 11.4 Texture access: why `draw_prepare_texture_access_unsupported` fired 24 times on Dozen

**It is not a Dozen problem.** The R10b GPU log has one refused draw shape, repeated:

    linux_m2v_draw reason=draw_prepare_texture_access_unsupported stage=fragment index=3 texture_ref=77
      binding=483 access=storage pipe=142 vtx=24 prim=3 (indexed triangle list), two RGBA16F (fmt 0x73) 1920x1080 targets

The 24 are the draws skipped behind it, from t=796 s to t=885 s; the log ends at 888 s. The R10
**Lavapipe** boot `20261029T141852Z-igslwjqy` refuses the same shape: fragment stage, texture index 3,
binding 483, `access=storage`, 24 indices, two RGBA16F targets, on pipe 152. It skips one draw there, at
t=494 s. **The count is how often the guest redrew that element in the observed window, not a driver
difference.**

**Cause.** Reims's render path binds fragment textures only as sampled images. `runtime/draw/vulkan.rs`
refuses before recording when a stage's reflection reports a storage (read/write) texture. It does so
at two sites:
- the pre-scan `spirv_bind::first_non_sampled_texture_descriptor`;
- the per-texture bind in `push_tex`.

**The device is not the limit.** Dozen on the RTX 5070 reports:
- `fragmentStoresAndAtomics`;
- `shaderStorageImageReadWithoutFormat` and `shaderStorageImageWriteWithoutFormat`;
- `STORAGE_IMAGE` on RGBA16F, RGBA16, RGBA8 and BGRA8 (`logs/formats2-formats.json`);
- `maxPerStageDescriptorStorageImages` 1,000,000.

**Not fixed in R12, for these reasons.** A correct fix is a new render-path resource kind, not a gate:
1. `DrawRequest` must carry fragment storage textures.
2. The pipeline layout needs a `STORAGE_IMAGE` descriptor at the reflected binding.
3. The image must be created with `STORAGE` usage, gated on the format's `STORAGE_IMAGE` feature, and kept in `GENERAL` layout for the pass.
4. If the module writes, the texture becomes GPU-authoritative. That means hazard barriers before any later sample or attachment use, resident-content tracking and writeback to guest memory. Metal's ordering of fragment writes to a texture also needs an answer, for example raster order groups.

The refusal sites are in `runtime/draw/vulkan.rs`, which R11 is editing, so this would not be a narrow
change.

**Recommended first step.** Carry the access direction (read / write / read-write, from the module's
`NonWritable`/`NonReadable` decorations and image ops) in the `TextureAccessUnsupported` fields. The
next boot will then show whether a read-only `STORAGE_IMAGE` rung would cover this draw. That rung would
need only items 1–3; item 4 is the large part.

### 11.5 Artifacts (not booted)

Both artifacts are in my owned subpath of volume `macos-orchard-build`, which a boot's read-only `/work`
mount can see. There are no host copies.

| Artifact | sha256 | Bytes |
|---|---|---|
| **`/work/gpu-dzn/artifacts/qemu-system-aarch64`** | **`db5cf415bcf40d68ae4bfb5e014ea910bcec24a77130f69450baade671b69edb`** | 70,867,688 |
| `/work/gpu-dzn/artifacts/libreims_vgpu.a` | `b4b77adfefee60cfd1daefb6cd7f39789a88daf7eec23c3f603ea65364b3fac3` | 175,043,638 |

- **Staticlib.** Built with `cargo build --release --locked --offline -p reims-vgpu --no-default-features --features backend-vulkan,host-window` from the staged tree (receipt `r12f-apply`): 1 job, 98.6 s. Its 2 compiler warnings predate this patch.
- **Link.** Done exactly as `m2v_run.py r10_link` does it. The `qemu-system-aarch64` command comes from `ninja -t compdb -x c_LINKER_RSP` in `/work/orchard-m27/qemu/build`, with 2 of its 1,363 arguments swapped (`logs/r12-link-link-argv.json`):
  - `-o qemu-system-aarch64` → `/work/gpu-dzn/artifacts/qemu-system-aarch64`;
  - `/work/orchard-m27/reims-vgpu/target/release/libreims_vgpu.a` → the R12 staticlib.
- **`--version`:** `QEMU emulator version 11.1.50`. No guest code ran (`logs/r12-artifacts.json`).
- **Identity check** (`logs/r12-holdings-holdings.json`): the QEMU binary contains each of the four new decline slugs and does not contain `color_input_ordered_access_unavailable`.
- **Resources.** The link container peaked at 1.77 GB of memory.

**Not booted.** To boot, the parent's profile pattern (`local-raw/golden_m27_pages_prefix2_profile.py`)
applies unchanged:
- `QEMU = Path('/work/gpu-dzn/artifacts/qemu-system-aarch64')`, with the QEMU sha above;
- `LIBRARY = QEMU.parent / 'libreims_vgpu.a'`, with the staticlib sha above.

On `-VulkanDriver gpu` a colour-input draw takes the per-primitive rung. On Lavapipe it takes the
rasterization-order rung, exactly as before. I added no profile and did not edit the launchers or runners.

### 11.6 Disk and what I hold now

- **Containers.** Every R12 container ran alone, with at most 4 GB of memory and 2 CPUs; builds used 1 job.
- **Free space.** The lowest host free space during the R12 work was **23.01 GiB**, during the RED build at 16:12 UTC. No guard tripped and there were no OOM events.
- **Reuse.** Before R10b was staged, the superseded R10 copy (2,126,606,512 bytes) was deleted, so the volume reused those blocks (`logs/r12-stage-stage.json`).

| Held | Size |
|---|---|
| `/work/gpu-dzn` (volume `macos-orchard-build`) | **2,146,564,635 bytes**: `target` 1,855,008,049 (R10b's seeded target plus the R12 builds); `artifacts` 245,911,326; `reims-vgpu` 45,645,260 (R10b plus R12); `tmp` 0 |
| Image `gpu-dzn-runtime:mesa26.2.5-dzn` | 2.55 GB nominal; 15.87 MB unique (unchanged) |
| Host `full-system\gpu-dzn\` | 47.5 MB: `source-view` 20.2, `image` 13.5, `logs` 7.1, `patch` 2.7, `engine-readbacks` 0.19 and `scripts` 0.06 MB |
| Running containers | none |

**Remaining steps need no new disk from me.** A boot is the parent's. Once the parent has admitted the
artifacts, `/work/gpu-dzn/target` (1.86 GB) can be deleted so the volume can reuse its blocks.

## Files

- `scripts/Launch-Gpu.ps1` (`434cd6a1…`): guarded launcher.
- `scripts/gpu_run.py`: runner (`prepare-image`, `vulkaninfo`, `formats`, `stage`, `stage12`, `apply`, `build`, `lint`, `link12`, `holdings`, `tests`, `debug`).
- `reims-r12-gpu.patch` (`eaffa35e…`): the R12-gpu change against R10b. `patch/r12` is the GREEN file tree and `patch/r12-red` the RED one (tests only).
- `image/`: Dockerfile and context; `image/image-id.txt`.
- `run-gpu-attempt.py` and `test_run_gpu_attempt.py`.
- `scripts/Test-LauncherArgs.ps1`.
- `reims-host-allocation-gate.patch`; `patch/red` and `patch/after` file trees.
- `source-view/`: the R10 crates exported read-only.
- `logs/`: every receipt, guard record and test log.
- `engine-readbacks/`.
