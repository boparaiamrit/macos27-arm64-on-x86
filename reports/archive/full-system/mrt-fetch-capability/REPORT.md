# Pinned software-Vulkan attachment-ordering capabilities

**PASS: the current software driver advertises color rasterization-order attachment access, and one device successfully enabled that advertised feature.** This is capability/device-creation proof only. No rendering, overlapping-fragment ordering oracle, runtime-engine change, VM, guest input or desktop verification occurred.

## Actual API result

- Vulkan instance requested **1.2**. Actual single CPU device: `llvmpipe (LLVM 21.1.8, 128 bits)`, driver `Mesa 26.2.5 - kisak-mesa PPA (LLVM 21.1.8)`. Driver/API identity and all six pinned runtime files matched before and after.
- Both `VK_EXT_rasterization_order_attachment_access` and its ARM alias were enumerated. `vkGetPhysicalDeviceFeatures2` returned color/depth/stencil **true/true/true**.
- Exactly **one** device was created and destroyed, using the graphics queue and **only the advertised EXT color ordering feature**. Depth/stencil feature fields remained zero. `vkCreateDevice` returned `VK_SUCCESS` (0).
- `maxColorAttachments=8`; `maxPerStageDescriptorInputAttachments=1015808`; `maxDescriptorSetInputAttachments=1015808`.
- Optimal 2D image-property queries accepted combined `COLOR_ATTACHMENT | INPUT_ATTACHMENT | TRANSFER_SRC | TRANSFER_DST` usage (147) for RGBA8_UNORM, BGRA8_UNORM, RGB10A2_UNORM, RGBA16_UNORM and RGBA16_SFLOAT. Each reported max extent16384x16384x1 and sample mask13. No image was created.
- The C program invokes no image/buffer/memory allocation, render-pass/pipeline/command-buffer construction or draw API. Its `gpu_resources_created=false` flag means no such application rendering resources; instance/device creation naturally permits driver-internal work.

Installed Vulkan C headers define the feature ABI: header version309, feature sType1000342000, feature struct size32. `header-pins.json` records all three header hashes. No ctypes layout or enum value was guessed. The binary was compiled once with installed headers and libvulkan; source and executable hashes remained identical across both loader attempts.

## Preserved harness failure and authorized correction

The initial query returned `vkCreateInstance=-9` before physical-device enumeration. The pinned ICD's absolute library path is `/out/runtime/lib/libvulkan_lvp.so`; the first harness supplied only the `/soft` read-only mount. The actual mount receipt and pinned ICD establish that namespace mismatch. All six runtime hashes had matched. This was not an unsupported-feature/device result, a resource/guard/OOM failure or a substituted driver.

Every initial file is frozen in `first-query/`. The parent expressly authorized one harness-path correction: mount the **same pinned directory read-only at both `/soft` and `/out/runtime`**, matching the existing qualified Gpu.ps1 route. One corrected query then used the exact same binary. No recompilation, driver/runtime/source edit, resource widening or third query occurred. `corrected-query-attempt.json` consumes that one corrected execution before launch. The first failure remains in root/archived receipts; it is not overwritten as a success.

## Bounds, preservation and cleanup

Three exact owned containers ran: one compiler, one failed loader query, one corrected query. Their cleanup receipts confirm absence. All **89** original container IDs and **28** volumes match the initial inventory. Exporter ID/PID/start, sampler77088/start and Android79064/start remain unchanged. No CONTROL, RAW, state, build volume or host GPU device was mounted; no existing service/process was signaled.

Actual Docker admission and inner cgroup readbacks show1CPU/512MiB/equal memory-swap (extra swap0), pids128, networknone, read-only root, tmp16MiB, core ulimit0 and inherited process-local filter0x10. Mounts were only owned outputRW, full-system directoryRO, and pinned runtimeRO aliases. Compiler peak **72974336B**; corrected-query peak **140529664B**. Their post-event receipts report max/OOM/OOM-kill counts0. The first failed-loader wrapper did not retain post-cgroup peak/events; its pre-event values were0 and Python reported the explicit child exit2. No unsupported post-event claim is made for that first failure.

Compiler elapsed0.319s <60; corrected inner query7.775s <30; cumulative active host time **18.016s** including the first failed run <180. Minimum corrected outer sampled/actual free **13157863424B**, above unconditional10GiB. Samples were checked at age[-2,20]s. Guard target0.2s; observed corrected outer max gap0.214s and inner max gap0.250s. Poll targets are not strict scheduling guarantees. Logs remained below1MiB and owned output below10MiB (read-only runtime mount excluded).

## What this permits next

The advertised host feature and one explicit device-creation gate passed. The production renderer still must query and enable the feature/extension and implement the correct render-pass/pipeline ordering contract. Indexed input-reference/descriptor/layout/cache-key behavior and overlapping-fragment correctness need their own owner tests and GPU oracle. No current renderer ordering, MRT acceptance, filtering, missing-pixel causality, guest compatibility or usable desktop is established.

Primary contract references supplied/read by the parent: [Khronos extension](https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_rasterization_order_attachment_access.html) and [ordering sample](https://docs.vulkan.org/samples/latest/samples/extensions/rasterization_order_attachment_access/README.html). This task measured the stated API facts rather than treating documentation as host support.

Only new owned capability files were written. Installed codebase-memory guidance was read; parent reported graph/index/coverage tools unavailable, so named-source fallback was used and no graph-coverage claim is made. No delegation, production edit, buildvolume access, VM/input, commit or push.
