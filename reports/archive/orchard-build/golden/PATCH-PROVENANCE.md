# GoldenGate virtio port provenance

Base: Orchard `c73a2bda1fd4afefd61204bb74afd74292ef2fe9`.

The two original upstream mail patches are retained byte-for-byte:

- `golden-virtio-storage.patch`: commit `d235e51310886f289dcc7c30f9d97edfaea4efa6`, authored by Anees Iqbal, co-authored by Jesus Martinez (the original mail header retains the accented spelling).
- `golden-virtio-network.patch`: commit `fbda9c8b28351baab659dbd8e591914f44ee7fdb`, authored by Anees Iqbal.

Their original attribution, provenance statements, and source copyright/license headers are preserved. The affected QEMU files retain GPL-2.0 / GPL-2.0-or-later terms as stated in their headers. QEMU's COPYING and LICENSE, Orchard ATTRIBUTION.md, and Reims LICENSE accompany the binary in `artifacts/provenance/`.

`golden-virtio-network-ported.patch` changes just the following context line in the upstream mail patch, because Orchard removed the tablet getter. Its five added lines are unchanged:

```diff
-static char *vmapple_get_tablet(Object *obj, Error **errp)
+static bool vmapple_get_gfx(Object *obj, Error **errp)
```

Two local implementation changes are recorded separately in the complete `orchard-golden.diff`:

- `qemu/hw/vmapple/vmapple.c`: explicitly apply the new network default to Orchard's `apple-vm` subclass. QEMU's `machine_class_base_init()` gives each concrete machine a fresh `compat_props` array. The first live test showed `x-ascending-capabilities = false` with only the upstream patch; the local fix changes this to true without a command-line override. Existing compatibility defaults are not otherwise changed.
- `qemu/hw/display/meson.build`: optionally consume `reims-vgpu.pc` via `PKG_CONFIG_PATH`. This links the original baseline archive and headers; the original Cargo rule remains as the fallback. No GPU implementation or required Vulkan features were changed.

`network-machine.diff`, `virtio-storage.diff`, and `prebuilt-reims.diff` split those portions for inspection. The complete diff is authoritative. Local changes follow the existing files' license terms.

Lavapipe and LLVM were copied from already installed WSL libraries into this owned folder. No packages were installed or upgraded. Versions, dependencies, and original Debian copyright files are in `runtime/`. These libraries were used only for the synthetic smoke environment and are not part of the QEMU binary.

Important patch application detail: Orchard is one git repository containing `qemu/`. Invoke `git apply --directory=qemu` from the Orchard root. Invoking `git -C qemu apply --check` silently skipped these relative paths; its zero status alone did not establish compatibility. Actual root-relative application and reverse checks were performed here.
