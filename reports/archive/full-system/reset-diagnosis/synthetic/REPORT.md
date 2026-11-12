# Synthetic reset/register preservation

PASS: QEMU `dba936f79fdfecea6163360d4beea0495cf2e870c11816a6a1b0c08ca7a8b542` with `-no-reboot -no-shutdown` preserved debugger access to CPU registers after a synthetic guest reset.

The 16-byte firmware at `0x100000` contains only:

```text
movz w0, #9
movk w0, #0x8400, lsl #16
hvc #0
b .
```

The encodings were independently disassembled with the runtime's AArch64 objdump; the firmware requests PSCI `SYSTEM_RESET` (`0x84000009`). Inputs are synthetic UUID 1 and zero-filled 16 KiB AUX/root files. No Apple firmware, disk, guest or user identity was used.

Observed results:

- GDB received **SIGQUIT** after `continue` and successfully read PC, SP, CPSR and x0–x30. There was no “No registers” failure.
- Retained PC was **`0x10000c`**, immediately after the HVC; x0 remained **`0x84000009`**.
- QMP reported **`status=shutdown`, `running=false`**, while the QEMU process was still alive.
- The debugger disconnected successfully; the owner then issued QMP `quit`. Both GDB and QEMU exited 0 and were reaped. The task container is stopped.
- Firmware/AUX/root bytes remained unchanged.

Actual orchestration elapsed time was **0.472 seconds**, inside the 50-second internal lifetime bound and requested 60-second maximum. Limits were one CPU / two GiB, swap capped at two GiB, network none, read-only root and build volume, and 16 MiB tmpfs. Peak cgroup memory was 80,035,840 bytes with no OOM. Fresh guard checks used the existing robust sample reader and unconditional 10 GiB floor; minimum sampled C: free was 28,143,992,832 bytes.

Evidence: `result.json`, `gdb.log`, `registers.json`, `qmp.jsonl`, `command.json`, `firmware-disassembly.txt`, `host-guards.json`, and `container.json`. Only this new synthetic directory was written. No QEMU source, previous artifacts, real guest, backend or sampler was changed.

This proves the terminal-reset fallback for the tested synthetic PSCI path and exact binary. It does not establish the cause, reset path, or register contents of the Golden guest's earlier exit, and does not qualify the proposed Golden transfer breakpoint.
