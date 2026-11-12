# Chapter 9 — Why Periodic Screendumps Missed `present_content` & Sub-150ms Event-Triggered Frame Capture

## Objective
Deterministically capture live `1920×1080` `WindowServer` composited frames over QEMU Machine Protocol (`QMP`) without missing transient scanout windows during cold disk streaming.

## Key Learnings & Breakthroughs

### 1. The `1.374s` Scanout Overwrite Mystery (Warm Boot #9)
In Warm Boot #9, `reims-vgpu-fail.log` proved beyond a shadow of a doubt that `WindowServer` rendered and presented a non-black `1920×1080` frame at `t=150.314s`:
```text
OFF present_field_witness mid=3 1920x1080 map_gen=2 epoch=1 seq=3 why=changed unpainted=4/4 draws=2 passes=[p40/v6/s0+0+1920x1080/l0x2/c[0.000,0.000,0.000,0.000]/t-none p43/v6/s0+0+1920x1080/l0x1/t45.26.26.26.27.26.26.26.26.27.29.27] t=150286
OFF present_content mid=3 1920x1080 gen=0 rgb_nz=271 max_rgb=255 px0=[0,0,0,255] encoded=1 t=150314
```
Yet `frame-0005.png` (taken at `175.2s`) was solid black (`6,121` bytes)! Why?
- **Root Cause:** Our runner originally polled `time.sleep(5)` and issued QMP `screendump` every `25.0s` (`146.7s`, then `175.2s`). At `t=151.688s` (`1.374s` after `present_content`), `WindowServer` submitted `mid=3 gen=1` while NBD was still streaming layer 30 (`slot_empty_claimants task=1 ref=48`), overwriting the scanout buffer before the `175.2s` timer fired!

### 2. The `<150ms` Event-Triggered QMP Screendump (`src/fastjit-qemu/run-fastjit-macos27.py`)
We refactored the runner loop to poll `/tmp/reims-vgpu-fail.log` every **`150ms` (`0.15s`)** while keeping status logging on a `5.0s` cadence:
- The instant a new `present_content` line is appended by `libreims_vgpu`, `run-fastjit-macos27.py` dispatches `qmp_cmd(qmp_sock, 'screendump', ...)` within `<150ms` — **9× faster** than the `1,374ms` hold window!
- **Warm Boot #10 Verification:** At `t=147.69s`, `PRESENT_CONTENT #1` fired and immediately captured `present-0001.png` (`6,910` bytes, `1920×1080`, `rgb_nz=271`, `max_rgb=255`)!

### 3. Progression of Visual Checkpoints Captured Across the Project
1. **Apple Boot Logo + Progress Bar (`8,574` B):** `assets/macos27-apple-boot-progress.png`
2. **RGBA16 Composited Dock (`27,698` B):** `assets/macos27-dock-rgba16.png`
3. **Dozen RTX 5070 Keyboard Setup Assistant Window + Dock (`47,398` B):** `assets/macos27-keyboard-setup-dock.png`
4. **R11 Lavapipe Full Composited Desktop + Dock (`75,882` B):** `assets/macos27-r11-desktop-composited.png`
5. **FastJIT + QEMU `apple-vm` `WindowServer` Initial `present_content` (`6,910` B @ `147.7s`):** `assets/fastjit-present-content-1080p.png`
