# Chapter 6 — `reims-vgpu`, `metal2vulkan` Shader Compiler Fixes & macOS 27 `WindowServer` Pipes

## Objective
Translate macOS 27 `WindowServer` & `SkyLight` Apple Metal `.air` shaders and render graphs into Vulkan 1.3 pipelines in real time via `reims-vgpu` (`libreims_vgpu.a`).

## Key Learnings & Breakthroughs

### 1. macOS 27 Multi-Level GPU Page Trees (`reims-m27-page-trees.diff`)
macOS 27 updated its paravirtualized vGPU page-table depth and task-binding descriptors (`define_task site=root` for kernel `tid=0`, `define_task site=ch3` for `WindowServer` `tid=1` with `page_shift=14`, 16 KiB Apple Silicon pages). Adapting the page-tree walker unlocked guest GVA→GPA resolution for `WindowServer` command buffers.

### 2. Fixing `metal2vulkan` Vector Prefix-Load Failures (`m2v-prefix-load-v2.patch`)
In Warm Boots R9/R10, 10 `WindowServer` compositor shaders (`162` of `251` skipped draws across pipes `115`, `128`, `187`) failed `.air` → SPIR-V compilation!
- **Root Cause:** `metal2vulkan`'s vector prefix-load emitter restricted whole-vector over-reads by storage class, rejecting valid Apple Metal shaders loading窄 vectors from `device`/`threadgroup` buffers.
- **Fix (`R10b` / `prefix-load-v2.patch`):** Generalizing leading-vector prefix loads across all storage classes (matching `emit_narrowing_vector_load`) reduced shader translation failures from **10 → 0 (100% shader compilation success)**!

### 3. Discovering the Hidden Subprocess Toolchain Dependency (`llvm-dis` + `spirv-val`)
When booting inside a slim runtime Docker container (`gpu-dzn-runtime`), `WindowServer` connected at `t=120s` and suddenly logged:
`cannot_run_llvm-dis_(llvm-dis): No such file or directory (os error 2)`!
- **Root Cause:** `metal2vulkan` shells out at runtime to **`llvm-dis`** (to disassemble Apple `.air` LLVM bitcode) and **`spirv-val`** (to validate generated SPIR-V modules before `vkCreateShaderModule`)!
- **Fix (`src/fastjit-qemu/Dockerfile.runtime`):** Installing `llvm` (`LLVM 19.1.7 /usr/bin/llvm-dis`) and `spirv-tools` (`v2025.1 /usr/bin/spirv-val`) immediately unlocked live SPIR-V module compilation (`spv=876208` bytes on `pipe=43`)!

### 4. Closing `RGBA16Float`, `RGB10A2`, `RGBA16Unorm` & Memoryless `Clear` Gaps (`r11-render-gaps.patch`)
- **Wallpaper Linear Upload (`RGBA16Unorm`, `fmt=0x6e`):** Full-screen compositor `pipe=43` samples a `128×128` `RGBA16Unorm` linear texture. Without a stable host 16 KiB→4 KiB page alias (`zc_lin_no_alias`), zero-copy declined and `linear_native_upload_format` lacked an `Rgba16Unorm` arm. Adding `SampledClass::Rgba16Unorm` + `NativeUploads::unorm16` fixed `pipe=43/123`!
- **Memoryless `MTLLoadActionClear`:** `resolve_memoryless_target` originally admitted only `DontCare`, refusing 92 MRT draws where macOS 27 declared `Clear` (`value=2`) on tile/memoryless attachments. Admitting `Clear` mapped cleanly to Vulkan render-pass `VK_ATTACHMENT_LOAD_OP_CLEAR`.
