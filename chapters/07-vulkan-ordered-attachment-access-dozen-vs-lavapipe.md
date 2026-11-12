# Chapter 7 — Programmable Blending: Why WSL2 Dozen Declined `pipe=43` & How Lavapipe + `R12-gpu` Solved It

## Objective
Understand why `WindowServer` compiled shaders cleanly on WSL2's hardware RTX 5070 D3D12 Dozen driver (`dzn_icd.json`) yet skipped the main desktop composite draw (`pipe=43`), and solve it on both software and hardware Vulkan paths.

## Key Learnings & Breakthroughs

### 1. The Exact Decline Reason: `color_input_ordered_access_unavailable`
On Apple Silicon TBDR GPUs, `WindowServer` relies heavily on **Metal Programmable Blending** (reading the current pixel's color attachment `[[color(0)]]` inside the fragment shader for vibrancy, blur, menu bar translucency `pipe=19` `1920×60`, and full-screen desktop compositing `pipe=43` `1920×1080`).
- In Vulkan, race-free single-pass programmable blending requires **`VK_EXT_rasterization_order_attachment_access`** (`ordered_color_attachment_access = true`) and **`VK_EXT_attachment_feedback_loop_layout`**.
- **WSL2 D3D12 Dozen (`Microsoft Direct3D12 NVIDIA GeForce RTX 5070`):** Advertises `ordered_color_attachment_access = false`! Consequently, `reims-vgpu` lawfully declined `46` draws (`pipe=19` and `pipe=43`) with `reason=color_input_ordered_access_unavailable`, rendering the rounded Keyboard Setup window + titlebar buttons (`assets/macos27-keyboard-setup-dock.png`) while leaving ordered-blend passes unpainted!

### 2. Solution A — Mesa Lavapipe `LP128` (`VK_EXT_rasterization_order_attachment_access = true`)
Mesa's LLVM-JIT Vulkan rasterizer (`lvp_icd.json`, configured with `LP_NATIVE_VECTOR_WIDTH=128` and `LP_NUM_THREADS=4`) natively implements **both** `VK_EXT_rasterization_order_attachment_access` and `VK_EXT_attachment_feedback_loop_layout`!
- Switching `run-fastjit-macos27.py` to `lvp_icd.json` (`Mesa-25.0.7-Lavapipe-LP128`) immediately executed `pipe=40` + `pipe=43` (`1920×1080` with 12 bound textures `t45.26...29.27`) and emitted:
  `OFF present_content mid=3 1920x1080 gen=0 rgb_nz=271 max_rgb=255 px0=[0,0,0,255] encoded=1`!

### 3. Solution B — Hardware D3D12 Dozen Barrier/Fallback Path (`r12-gpu-dozen-ordered-access-fallback.patch`)
For hardware D3D12/Dozen GPUs lacking `VK_EXT_rasterization_order_attachment_access`, we also engineered `reims-r12-gpu.patch` (`57 KB`) + `reims-host-allocation-gate.patch`, implementing a non-ordered attachment-fetch fallback and texture-access lowering for D3D12!
