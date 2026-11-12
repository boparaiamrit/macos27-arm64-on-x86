# Chapter 10 — Telemetry Benchmarks, Open Graphics Frontiers & Roadmap

## 1. End-to-End Boot & JIT Telemetry Summary

| Metric | Cold / Early Baseline | Warm Boot #10 (`FastJIT` + Lavapipe `LP128`) |
| :--- | :--- | :--- |
| **Firmware `AVPBooter` → `XNU` Handoff (`0xE0A00000`)** | Timed out at `1700s` (before Scratch RAM / RTC / `0x2370`) | **`5.0s`** (`rc=0`, `BootArgs_r3` + `NoSEP` + `wdt=-1`) |
| **vGPU Kernel Task (`define_task site=root tid=0`)** | Unreached | **`7.9s`** (`t=7948`) |
| **vGPU `WindowServer` Task (`define_task site=ch3 tid=1`)** | `210.0s` (cold cache) / `120.2s` (Boot #8) | **`88.5s`** (`t=88517`) |
| **First `1920×1080` `WindowServer` `present_content`** | Declined (`llvm-dis` missing / Dozen ordered access) | **`147.7s`** (`present-0001.png`, `6,910` B) |
| **In-RAM 64 KiB Disk Cache (`offline_cache_nbd.py`)** | `6,102` blocks (`0.38 GiB`), corrupt `zero_fills > 0` | **`41,755` blocks (`2.61 GiB`), `zero_fills = 0`** |
| **`FastJIT` Compiled Unique AArch64 Blocks** | N/A (pure TCG) | **`456,294` blocks** (32 MiB RWX buffer) |
| **`FastJIT` Executed Blocks / Native `x86_64` Insns** | N/A (pure TCG) | **`1.044B` blocks / `1.750B` native insns** |
| **Metal-to-Vulkan Shader Translation Failures** | `10` failed modules (`162` skipped draws) | **`0` failures** (`R10b` vector prefix-load + `llvm-dis`/`spirv-val`) |

## 2. Open Engineering Frontiers (Where Contributors Can Jump In!)

1. **Apple Dual-Plane Icon Texture Format (`OBJECT_TYPE_DUAL_PLANE_TEXTURE`, `object_type=12`, `pf=0x226` / `550`):**
   - Dock app icons (`32×32` through `256×224`) use a dual-plane Metal texture descriptor (`pf=0x226` with two equal-sized planes). `reims-vgpu` currently logs a clean, deterministic refusal (`dual_plane_texture_unexecutable pf=0x226`) rather than guessing pixel layout, which is why Dock slots render as crisp translucent placeholders. Decoding `0x226`'s exact plane layout (likely bi-planar compression/alpha-luma) will light up full-color Dock icons!
2. **Multi-Mip `SampledSourceRequest` Uploads:**
   - `R11` added `SampledClass::Rgba16Unorm` for level-0 magnification (`128×128` → `1920×1080`). Extending `SampledSourceRequest::Bytes` to upload full mip pyramids (`5` levels) will eliminate minification aliasing on multi-mip UI textures.
3. **Merging `R11` (Render Gaps) + `R12-gpu` (Dozen Framebuffer-Fetch Fallback) → `R13`:**
   - `r11-render-gaps-rgba16unorm-memoryless-clear.patch` and `r12-gpu-dozen-ordered-access-fallback.patch` touch disjoint source files in `reims-vgpu`. Combining them enables hardware-accelerated RTX/D3D12 Dozen rendering on WSL2 without `VK_EXT_rasterization_order_attachment_access`!
4. **Expanding `FastJIT` AArch64 Instruction Coverage & Direct Register Pinning:**
   - Keeping top hot AArch64 GPRs (`x0–x7`, `x16`, `x29`, `x30`, `sp`) pinned in x86_64 callee-saved registers across the 8-step superblock chain in `fastjit-a64.c` and adding inline TLB fast-paths (`LDR`/`STR`) can multiply full-system boot and UI responsiveness by another **3×–5×**!
5. **QMP Mouse Controller Late-Reply Tolerance:**
   - Under heavy software Lavapipe rendering, QMP `query-status` replies can occasionally exceed strict millisecond deadlines; relaxing synthetic `'unresponsive'` session quarantine unlocks automated QMP HID mouse/keyboard interaction tests.
