# Orchard baseline build

Local build only. No guest disk/firmware downloads, VM boot, source patches,
commits, or publication are part of this task. Read `RESULT.md` for the actual
outcome and qualification limits.

## Inputs and ownership

- Source: https://github.com/yaelliethy/orchard
- Commit: `c73a2bda1fd4afefd61204bb74afd74292ef2fe9` (detached, shallow fetch).
- Base image: `macos-graphics-research:local`, observed ID
  `sha256:b8c22d84d3d2c8fe9df501f10072597bed1610c981d33104453ff9b72a113544`.
- New image: `macos-orchard-builder:local`.
- New Linux Docker volume: `macos-orchard-build`, mounted at `/work`.
- Containers: `macos-orchard-*` only.
- Windows output: `<WORKSPACE>/macos\test-output\arm-macos\orchard-build`.
- Rust: existing WSL toolchain
  `/home/boparaiamrit/.rustup/toolchains/stable-x86_64-unknown-linux-gnu`,
  mounted **read-only** at `/opt/rust`; no writes to the user's Cargo/Rustup homes.
  Actual compiler version is in `build.log`.

All mutating container operations have `--cpus=6 --memory=6g
--memory-swap=6g --pids-limit=512`. The source, Cargo downloads and compiler
outputs stay in the Linux volume so tracked symlinks remain real symlinks.
`resources.jsonl` samples cgroup memory and `du` every 15 seconds. The guard
terminates compilation above 6 GiB for `/work` plus this output folder, reserving
2 GiB of the 8 GiB task allowance for new image layers and overhead.

## Reproduction

For the first run, from Windows PowerShell:

```powershell
$build = '/mnt/c/Users/bopar/Projects/macos/test-output/arm-macos/orchard-build/control.sh'
wsl -d Ubuntu -- bash $build fetch
wsl -d Ubuntu -- bash $build prepare
wsl -d Ubuntu -- bash $build build
docker logs macos-orchard-build
docker inspect macos-orchard-build --format '{{json .State}}'
Get-Content test-output\arm-macos\orchard-build\build.log -Tail 50
# After exit 0:
wsl -d Ubuntu -- bash $build smoke
```

The retained `macos-orchard-build` container can be restarted for an incremental
rebuild with `docker start macos-orchard-build`; its output goes to `build.log`.
Preparation and build initially use fixed container names and intentionally
fail if another container already owns them. They never replace or remove
existing resources. `Dockerfile` records the equivalent dependency installation;
the actual run uses capped `docker run` then `docker commit`, avoiding an
uncapped BuildKit operation. `builder-packages.tsv` records resolved packages.

`compile.sh` first compiles the exact Rust feature set used by Orchard's Meson
rule, then invokes the unchanged upstream `scripts/build.sh`. This separates
the Rust release link from QEMU compilation under the RAM cap. Rust retains
upstream release optimization, fat LTO, one codegen unit, and unwind semantics;
incremental artifacts are disabled to bound disk use. Cargo uses the checked-in
lock file. The Ninja wrapper limits parallelism to four jobs and load six.

```bash
cargo build --locked --release --manifest-path reims-vgpu/Cargo.toml \
  -p reims-vgpu --no-default-features --features backend-vulkan,host-window
scripts/build.sh --enable-tcg --disable-kvm \
  --disable-debug-info --disable-tests --disable-guest-agent \
  --disable-tools --disable-gtk --disable-sdl --disable-vnc --disable-opengl
```

GTK/SDL/OpenGL/VNC are not needed for Reims's own winit/Vulkan presentation
window. The executable is a Linux **x86-64 host** binary for **aarch64 guests**.

## Evidence and retained source

- `upstream-instructions.txt`: root README/CONTRIBUTING/ATTRIBUTION, scripts
  README/build script, QEMU and Reims AGENTS, and Reims manifests read before
  the build.
- `source-commit.txt`, `source-symlinks.txt`: pinned source and verified tracked
  symlink types. `source-status.txt` is written by smoke checks.
- `build.log`, `build-result.json`, `resources.jsonl`: compile output, exit
  status, disk and memory samples.
- `builder-image.json`, `prepare-container.json`, `build-container.json`:
  image identity, resource limits and mount properties.
- `smoke.log` and registration/property/dependency outputs: executable checks
  that do not instantiate a VM.
- `runtime-source-evidence.txt`: page geometry, memory fallback, capability
  query and upstream launch defaults from the pinned source.
- `artifacts/`: executable, Rust static library, SHA-256 sums, and provenance.

Corresponding Orchard/QEMU/Reims source remains in the volume at
`/work/orchard`. Cargo dependency source, including pinned `metal2vulkan`, is
retained at `/work/cargo`. Original license notices remain intact. The upstream
documents describe QEMU as GPL-2.0 with Orchard changes GPL-2.0-or-later and
Reims as LGPL-3.0-or-later; the Reims product Cargo manifest independently says
GPL-2.0-or-later. Both original declarations are preserved for review rather
than resolving that upstream inconsistency here. No artifacts are published.

This build does not qualify a GoldenGate/macOS 27 desktop, a WSL GPU driver,
Docker GPU forwarding, or a boot path. Orchard's documented baseline is Ventura.
