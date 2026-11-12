# Existing console capture route, not yet runtime-qualified

Read-only examination of the exact Orchard/Reims source found a QEMU console, not only a winit host window. `reims-vgpu-mmio.c:1323` creates the console and surface; `:704–775` copies completed `ScanoutUpdate` frames into it. Rust `runtime/drain/mod.rs:4588–4624` routes completed scanout toward that console when `REIMS_VGPU_WINDOW=0`.

The future capture candidate is the direct QMP `screendump` command with PNG format and an existing writable owned-attempt destination. This build has PNG support and needs no X11, Wayland or Xvfb just to expose this route. QEMU `ui/ui-qmp-cmds.c:324–390` and `ui/console.c:168–177` implement a coroutine and console-update bottom half; unlike GDB attachment, this does not call `vm_stop` or explicitly drain all block devices.

This is source evidence, not a live capture qualification. It still uses main-loop/BQL and update callbacks; bounded response latency and absence of disruption must be tested before admission. The existing runner owns a QMP connection and suspends periodic status polling on slow I/O, so a future feature should use that owned connection with explicit arguments, deadline/guard handling, output budgets and positive completion checks. A competing second debugger or monitor must not be improvised in the next warm-cache boot.

An initial black surface or Apple logo is not desktop proof. Require guest render/present activity, inspect an actual composited frame, and later verify interaction before claiming Finder/Dock desktop success. Current `REIMS_VGPU_WINDOW=0` does not itself prove that the guest cannot render or that no QEMU surface can be captured.

The next warm-cache attempt remains unchanged and has no admitted runtime screenshot or second debugger. Implementing and testing this capture route is a separate later gate once bootstrap/render evidence warrants it.
