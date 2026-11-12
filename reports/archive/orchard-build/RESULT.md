# Orchard ARM/TCG + Reims build result

**Build and non-VM smoke checks passed.** This is an unmodified, locally built
Orchard baseline with Vulkan and its host-owned GUI window compiled in. It is
not a boot-tested or graphics-tested guest environment. No guest image was
downloaded, no VM was instantiated, and no claim of GoldenGate/macOS 27 support
follows from this result. [Orchard's README](https://github.com/yaelliethy/orchard/blob/c73a2bda1fd4afefd61204bb74afd74292ef2fe9/README.md)
documents a Ventura baseline.

## Exact source and artifacts

- Orchard repository: `https://github.com/yaelliethy/orchard.git`
- Commit: **`c73a2bda1fd4afefd61204bb74afd74292ef2fe9`**.
- Source: Docker volume **`macos-orchard-build`**, at `/work/orchard` when
  mounted at `/work`. Detached shallow fetch; all 14 tracked symlinks verified
  as symlinks. Final tracked-source diff and status are clean.
- Translator: `steelbrain/metal2vulkan` commit
  `9e0e99a41dc3cb8bb7e288b531f1698a79fd4b1c`, retained under
  `/work/cargo/git/checkouts/metal2vulkan-ec622ce80a554d9d/9e0e99a`.
- Built QEMU: `/work/orchard/qemu/build/qemu-system-aarch64`.
- Built Reims: `/work/orchard/reims-vgpu/target/release/libreims_vgpu.a`.
- Meson-linked copy: `/work/orchard/qemu/build/hw/display/libreims_vgpu.a`;
  byte comparison against the Rust output passed.
- Exported QEMU:
  `<WORKSPACE>/macos\test-output\arm-macos\orchard-build\artifacts\qemu-system-aarch64`
  (70,470,792 bytes).
- Exported static library:
  `<WORKSPACE>/macos\test-output\arm-macos\orchard-build\artifacts\libreims_vgpu.a`
  (174,368,172 bytes).
- Builder image: **`macos-orchard-builder:local`**, ID
  `sha256:0a0cabc8b884c695e9264ef533d91c4fa672e57d067f0d6b5bc429628ca8817e`.

This is a Linux **x86-64 host** executable emulating **aarch64 guests**. It
reports QEMU **11.1.50** and is not stripped. Debian 13 runtime libraries are
available in the retained builder image. The full corresponding source and
Cargo dependency sources remain in the owned volume.

SHA-256, checked both inside Linux and independently with Windows Get-FileHash:

```text
6e84c533ce4f9fe1c7a01745219a8ce5a9fe06b38bd80db14720147df8ce42dd  qemu-system-aarch64
32720f5ea9a0dfd7d388714e9c2b7818c98e9cf1e761140318ead212cb799a47  libreims_vgpu.a
```

## Exact build

The build entry point, from Windows PowerShell, was:

```powershell
wsl -d Ubuntu -- bash /mnt/c/Users/bopar/Projects/macos/test-output/arm-macos/orchard-build/control.sh build
```

The capped container executes `build.sh`, whose guard invokes `compile.sh`.
With `/work/orchard` as the working directory:

```bash
export PATH=/work/bin:/opt/rust/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export CARGO_HOME=/work/cargo CARGO_BUILD_JOBS=2 CARGO_INCREMENTAL=0
export PYTHONNOUSERSITE=1 REIMS_VGPU_DIR=/work/orchard/reims-vgpu
cargo build --locked --release --manifest-path reims-vgpu/Cargo.toml \
  -p reims-vgpu --no-default-features --features backend-vulkan,host-window
scripts/build.sh --enable-tcg --disable-kvm \
  --disable-debug-info --disable-tests --disable-guest-agent \
  --disable-tools --disable-gtk --disable-sdl --disable-vnc --disable-opengl
```

`/work/bin/ninja` delegates to `/usr/bin/ninja -j4 -l6`. No upstream build
script or source file was patched. Rust release optimization, fat LTO, one
codegen unit, and panic unwind remain as upstream specified. Reims is built
first to avoid its expensive release compilation overlapping QEMU compiler
jobs. The unmodified Meson rule then reuses it. QEMU's own separate Rust-device
subsystem reports disabled; that does not disable the Reims custom Cargo rule.

Compiler: WSL **Rust 1.99.1 / Cargo 1.99.1**, mounted read-only, and Debian GCC
**14.2.0**, Meson **1.7.0**, Ninja **1.12.1**. Both build commands exited **0**.
Rust took **4m16.42s**, then QEMU configure/build took **2m22.21s**. The build
ran 2026-10-26 15:44:26–15:51:06 UTC, with the guard/container exiting at
15:51:12 UTC. Two unique upstream Rust `fetch_update` deprecation warnings were
emitted and repeated by the cached Meson Cargo invocation. No C implicit
declaration warnings appeared. Tests were not compiled or run.

## Actual smoke checks

Executed via `control.sh smoke`; exit **0**, 15:51:13–15:51:17 UTC:

- QEMU `--version`, `-accel help`: executable loads; **TCG** is present.
- `-machine help`: **apple-vm** and **vmapple** are registered.
- `-machine apple-vm,help`: machine property introspection succeeds.
- `-device reims-vgpu-mmio,help`: Reims MMIO device property introspection
  succeeds. This sysbus device need not appear in the user-creatable device list.
- Block/network device registration: `vmapple-virtio-blk-pci` and
  `virtio-net-pci` are present.
- `ldd`: all dynamic dependencies resolve in the builder image.
- `nm`: Reims QEMU C ABI symbols, including
  `reims_vgpu_qemu_device_create`, are present in the executable.
- Rust archive and Meson-linked archive compare identically; Linux and Windows
  export hashes agree.
- Final tracked-source status is empty; build-harness Bash/Python syntax checks
  pass.

These checks do not initialize the guest, execute guest firmware, exercise a
Vulkan physical device, create a presentation window, or prove a desktop boot.

## Resource accounting and isolation

Every retained task container has CPU quota **6 CPUs**, memory limit **6 GiB**
and equal memory+swap limit (**no extra swap**). All are stopped. The build
cgroup recorded peak memory **3,121,537,024 bytes (2.91 GiB)** with **zero OOM
events**. Its disk guard was not triggered.

Final volume usage was **1,638,092,800 bytes**; exported files/logs were about
**245,804,544 bytes**. The new image adds **139,745,616 logical bytes** above its
existing base. Conservatively counting retained container writable layers again
gives **2,135,951,184 bytes (1.99 GiB)** total additional logical footprint.
Image/preparation snapshots can share storage; Docker/VHD filesystem allocator
overhead is not measured. This leaves substantial headroom below the 8 GiB
task allowance. See `footprint.json`, `resources.jsonl` and
`final-containers.json` for inspectable inputs.

Only this output directory, the new `macos-orchard-build` volume, the new builder
image, and `macos-orchard-*` containers were written. No existing images,
volumes, checkout scripts, host packages, WSL configuration, or Docker daemon
settings were changed. No prune, daemon restart, commit or publication occurred.
Original GPL/LGPL licenses, attribution and manifests are preserved under
`artifacts/provenance`; see README for the upstream license declaration mismatch.

## Requirements before any later run

1. Keep the volume attached at `/work`, use the Linux executable in the builder
   or a compatible runtime, and supply QEMU data files if needed via
   `-L /work/orchard/qemu/pc-bios`. The executable alone is not an installed QEMU
   data package.
2. Supply an appropriately matched guest disk, persistent aux/NVRAM/LocalPolicy,
   ECID/config and AVPBooter firmware. The upstream launcher also uses a writable
   overlay and `qemu-img`; QEMU tools are present in the base image but were not
   rebuilt here. No such Apple inputs were obtained or tested by this task.
3. ARM MMIO device creation explicitly uses page shift **14** (**16 KiB guest
   pages**); x86 uses shift 12. Preserve the ARM contract when integrating.
4. Reims owns the GUI through `backend-vulkan,host-window`. Upstream enables it
   with `REIMS_VGPU_WINDOW=1`, early framebuffer presentation with
   `REIMS_VGPU_FORCE_SCANOUT=1`, and uses QEMU `-display none`. Supply a working
   X11/Wayland session/socket/environment and an actual supported Vulkan ICD/GPU
   through the parent-owned Docker GPU integration. GTK/SDL being disabled does
   not remove the compiled Reims window path.
5. Vulkan API **1.2** is the source's baseline, but the API version alone does
   not prove shader capability. The parent's reported Dozen results
   `storageBuffer8BitAccess=false` and `shaderOutputViewportIndex=false` remain
   **unresolved runtime/translation qualification gaps**, not build failures.
   This task did not remeasure them, enable missing features, spoof capabilities,
   or alter shader behavior. The source queries these fields and enables only
   reported support; its floor documentation says both are needed for the guest
   command stream.
6. `VK_EXT_external_memory_host` is **optional in the current source**. The
   capability owner requires the extension, an importable host-pointer handle,
   and valid alignment before offering direct aliasing. Without that capability,
   guest-memory work must use copying paths. Fragmented Linux alias maps need
   shared file-backed guest RAM; ordinary anonymous RAM can refuse aliasing and
   fall back to copying. Do not infer zero-copy or correctness from a successful
   build. A live run must inspect named declines/import metrics and rendered
   frames. The root README/launcher describes measured whole-RAM import on a
   different AMD reference host; that measurement does not qualify Dozen.
7. Upstream defaults to a **10 GiB guest and 12 vCPUs**, outside this build task's
   limits. No VM run is authorized or attempted here; the six-CPU/six-GiB caps
   qualify only the build environment. Runtime sizing and guest compatibility
   remain for the parent task.

There are **no remaining compilation blockers**. Live WSL/Docker graphics,
capability handling and a matched guest boot remain unverified. This baseline
does not establish compatibility between Orchard's Ventura boot path and the
parent's separate current-root macOS 27 / qemu-sptm path.
