#!/usr/bin/env python3
"""Boot macOS 27 (26A5277g ARM64) on qemu-system-aarch64 (apple-vm) with FastJIT active."""
import base64
import json
import os
from pathlib import Path
import plistlib
import shutil
import socket
import subprocess
import sys
import time

PARENT = Path('/parent')
FULL = PARENT / 'full-system'
INTEG = PARENT / 'fastjit/qemu-integration'
OUT = INTEG / 'run-logs'
QEMU = Path('/work/orchard-fastjit/artifacts/qemu-system-aarch64')
GUEST_BOOT = Path('/guest/fresh-01/boot')
STREAM_DIR = Path('/stream')
NBD_SOCK = STREAM_DIR / 'golden-live5.nbd'
WORK_TMP = Path('/tmp/fastjit-vm')

QMP_SEQ = 0


def redact(text: str, tokens: list[str]) -> str:
    for tok in tokens:
        text = text.replace(tok, '<ECID>')
    return text


def qmp_cmd(sock: socket.socket, cmd: str, args: dict | None = None) -> dict:
    global QMP_SEQ
    QMP_SEQ += 1
    req_id = QMP_SEQ
    payload = {'execute': cmd, 'id': req_id}
    if args:
        payload['arguments'] = args
    sock.sendall((json.dumps(payload) + '\n').encode('utf-8'))
    buf = b''
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            raise RuntimeError('QMP socket closed')
        buf += chunk
        while b'\n' in buf:
            line, buf = buf.split(b'\n', 1)
            msg = json.loads(line.decode('utf-8', errors='replace'))
            if ('return' in msg or 'error' in msg) and msg.get('id') == req_id:
                return msg


def main():
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    Path('/proc/self/coredump_filter').write_text('0x10\n', encoding='ascii')

    OUT.mkdir(parents=True, exist_ok=True)
    WORK_TMP.mkdir(parents=True, exist_ok=True)
    STREAM_DIR.mkdir(parents=True, exist_ok=True)

    # Read ECID from inputs/config.json (redact before writing any logs)
    cfg = json.loads((FULL / 'inputs/config.json').read_text(encoding='utf-8'))
    ecid = plistlib.loads(base64.b64decode(cfg['ecid']))['ECID']
    tokens = sorted({str(ecid), f'{ecid:x}', f'{ecid:X}'}, key=len, reverse=True)

    # 1. Start offline cached NBD server on /stream/golden-live5.nbd
    if NBD_SOCK.exists():
        NBD_SOCK.unlink()
    nbd_ready_path = WORK_TMP / 'nbd_ready'
    if nbd_ready_path.exists():
        nbd_ready_path.unlink()
    nbd_cmd = [
        'nbdkit', '-t', '16', '-r', '-U', str(NBD_SOCK),
        'python', str(INTEG / 'offline_cache_nbd.py'),
        'cache=/cache',
    ]
    subprocess.run(nbd_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    for _ in range(900):
        if NBD_SOCK.exists() and nbd_ready_path.exists():
            break
        time.sleep(0.1)
    assert NBD_SOCK.exists() and nbd_ready_path.exists(), 'NBD server did not finish loading cache'
    print(f'[Runner] Offline macOS 27 cached NBD server ready ({nbd_ready_path.read_text()} blocks in RAM)', flush=True)

    # 2. Prepare ephemeral writable aux + qcow2 overlay in /tmp/fastjit-vm
    aux_work = WORK_TMP / 'aux.work.img'
    shutil.copy2(GUEST_BOOT / 'aux.work.img', aux_work)

    top_overlay = WORK_TMP / 'top.overlay.qcow2'
    subprocess.run([
        'qemu-img', 'create', '-f', 'qcow2',
        '-F', 'qcow2', '-b', str(GUEST_BOOT / 'root.overlay.qcow2'),
        str(top_overlay),
    ], check=True)

    serial_path = WORK_TMP / 'serial.log'
    stderr_path = WORK_TMP / 'stderr.log'
    gdb_log_path = WORK_TMP / 'gdb.log'
    handoff_path = WORK_TMP / 'handoff.json'
    qmp_path = WORK_TMP / 'qmp.sock'

    backing_uri = 'nbd+unix:///?socket=/stream/golden-live5.nbd'
    qemu_argv = [
        str(QEMU),
        '-M', f'apple-vm,uuid={ecid}',
        '-accel', 'tcg,thread=multi,tb-size=1024',
        '-smp', '10',
        '-m', '8G',
        '-bios', str(GUEST_BOOT / 'AVPBooter.patched.bin'),
        '-drive', f'file={aux_work},if=pflash,format=raw',
        '-drive', f'file={backing_uri},if=pflash,format=raw,readonly=on',
        '-drive', f'file={aux_work},if=none,id=aux,format=raw',
        '-device', 'vmapple-virtio-blk-pci,variant=aux,drive=aux,share-rw=on',
        '-drive', f'file={top_overlay},if=none,id=root,format=qcow2,cache=writeback',
        '-device', 'vmapple-virtio-blk-pci,variant=root,drive=root',
        '-netdev', 'user,id=net0,ipv6=off,restrict=on',
        '-device', 'virtio-net-pci,netdev=net0,romfile=',
        '-display', 'none',
        '-serial', f'file:{serial_path}',
        '-monitor', 'none',
        '-qmp', f'unix:{qmp_path},server=on,wait=off',
        '-gdb', 'tcp:127.0.0.1:1234',
        '-S',
        '-no-reboot',
    ]

    qemu_env = os.environ.copy()
    if Path('/usr/share/vulkan/icd.d/lvp_icd.json').exists():
        qemu_env.update({
            'VK_DRIVER_FILES': '/usr/share/vulkan/icd.d/lvp_icd.json',
            'VK_ICD_FILENAMES': '/usr/share/vulkan/icd.d/lvp_icd.json',
            'LP_NUM_THREADS': '4',
            'LP_NATIVE_VECTOR_WIDTH': '128',
            'REIMS_VGPU_WINDOW': '0',
            'REIMS_VGPU_COMPUTE_SCATTER': 'off',
            'REIMS_VGPU_COMPUTE_GATHER': 'off',
            'XDG_RUNTIME_DIR': '/tmp',
        })
        vulkan_mode = 'Mesa-25.0.7-Lavapipe-LP128'
    elif Path('/soft/lvp_icd.json').exists():
        qemu_env.update({
            'VK_DRIVER_FILES': '/soft/lvp_icd.json',
            'VK_ICD_FILENAMES': '/soft/lvp_icd.json',
            'LD_LIBRARY_PATH': '/soft/lib',
            'LP_NUM_THREADS': '4',
            'LP_NATIVE_VECTOR_WIDTH': '128',
            'REIMS_VGPU_WINDOW': '0',
            'REIMS_VGPU_COMPUTE_SCATTER': 'off',
            'REIMS_VGPU_COMPUTE_GATHER': 'off',
            'XDG_RUNTIME_DIR': '/tmp',
        })
        vulkan_mode = 'Mesa-26.2.5-Lavapipe-LP128'
    elif Path('/dev/dxg').exists() and Path('/opt/gpu-dzn/dzn_icd.json').exists():
        qemu_env.update({
            'VK_DRIVER_FILES': '/opt/gpu-dzn/dzn_icd.json',
            'VK_ICD_FILENAMES': '/opt/gpu-dzn/dzn_icd.json',
            'LD_LIBRARY_PATH': '/opt/gpu-dzn/lib:/usr/lib/wsl/lib',
            'LD_PRELOAD': '/usr/lib/wsl/lib/libd3d12core.so:/usr/lib/wsl/lib/libd3d12.so:/usr/lib/wsl/lib/libdxcore.so',
            'REIMS_VGPU_WINDOW': '0',
            'REIMS_VGPU_COMPUTE_SCATTER': 'off',
            'REIMS_VGPU_COMPUTE_GATHER': 'off',
            'XDG_RUNTIME_DIR': '/tmp',
        })
        vulkan_mode = 'RTX-5070-Dozen-D3D12'
    else:
        vulkan_mode = 'Default'

    print(f'[Runner] Starting FastJIT qemu-system-aarch64 (MTTCG smp=10, Vulkan={vulkan_mode})...', flush=True)
    stderr_file = stderr_path.open('wb')
    vm = subprocess.Popen(qemu_argv, stdout=stderr_file, stderr=subprocess.STDOUT, env=qemu_env)

    # Connect QMP
    qmp_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    qmp_connected = False
    for _ in range(300):
        if qmp_path.exists():
            try:
                qmp_sock.connect(str(qmp_path))
                qmp_connected = True
                break
            except OSError:
                pass
        time.sleep(0.1)
    assert qmp_connected, f'Failed to connect to QMP socket; stderr={stderr_path.read_text(errors="replace") if stderr_path.exists() else ""}'
    qmp_sock.settimeout(4.0)
    greeting = qmp_sock.recv(4096)
    assert b'QMP' in greeting, f'Unexpected QMP greeting: {greeting}'
    qmp_cmd(qmp_sock, 'qmp_capabilities')

    # Attach GDB handoff script (0xe0a00000 Golden Gate iBoot -> XNU handoff)
    bootargs = '-v serial=3 wdt=-1'
    hook_env = os.environ.copy()
    hook_env.update({
        'HANDOFF_SCRIPT_DIR': str(FULL / 'handoff-r3-wdt'),
        'HANDOFF_GDB_PORT': '1234',
        'HANDOFF_PC': '0xe0a00000',
        'HANDOFF_RAM_BASE': '0x70000000',
        'HANDOFF_RAM_SIZE': str(8 * 1024**3),
        'HANDOFF_RESULT': str(handoff_path),
    })
    gdb_argv = [
        'gdb-multiarch', '-nx', '-q', '-batch',
        '-iex', 'python import sys; sys.dont_write_bytecode = True',
        '-x', str(FULL / 'handoff-r3-wdt/kernel-handoff.gdb'),
    ]
    gdb_file = gdb_log_path.open('wb')
    hook = subprocess.Popen(gdb_argv, stdout=gdb_file, stderr=subprocess.STDOUT, env=hook_env)

    frames_dir = OUT / 'frames'
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old_f in frames_dir.glob('frame-*.png'):
        old_f.unlink(missing_ok=True)
    for old_p in frames_dir.glob('present-*.png'):
        old_p.unlink(missing_ok=True)
    frame_idx = 0
    present_idx = 0
    seen_present_lines = 0
    next_frame_t = 70.0
    next_status_t = 5.0
    reims_log_path = Path('/tmp/reims-vgpu-fail.log')

    start_t = time.monotonic()
    handoff_done = False
    nbd_stats_path = WORK_TMP / 'nbd_stats.json'
    while time.monotonic() - start_t < duration:
        if vm.poll() is not None:
            print(f'[Runner] QEMU exited with code {vm.returncode}', flush=True)
            break
        if not handoff_done and hook.poll() is not None:
            handoff_done = True
            print(f'[Runner] GDB handoff hook finished (rc={hook.returncode}) at {time.monotonic() - start_t:.1f}s', flush=True)
        time.sleep(0.15)
        elapsed = time.monotonic() - start_t

        # Immediate (<150ms) screendump whenever WindowServer logs a new present_content frame
        if reims_log_path.exists():
            try:
                reims_text_now = reims_log_path.read_text(encoding='utf-8', errors='replace')
                present_lines = [ln for ln in reims_text_now.splitlines() if 'present_content' in ln]
                if len(present_lines) > seen_present_lines:
                    seen_present_lines = len(present_lines)
                    present_idx += 1
                    p_target = frames_dir / f'present-{present_idx:04d}.png'
                    qmp_cmd(qmp_sock, 'screendump', {'filename': str(p_target), 'format': 'png'})
                    if p_target.exists():
                        p_sz = p_target.stat().st_size
                        shutil.copy2(p_target, OUT / 'fastjit-macos27-frame.png')
                        print(f'[Runner] *** PRESENT_CONTENT #{present_idx} captured -> {p_target.name} ({p_sz} bytes) at {elapsed:.2f}s | {present_lines[-1]} ***', flush=True)
            except Exception as e:
                print(f'[Runner] Immediate present_content screendump note: {e}', flush=True)

        if elapsed >= next_frame_t:
            next_frame_t = elapsed + 25.0
            frame_idx += 1
            f_target = frames_dir / f'frame-{frame_idx:04d}.png'
            try:
                qmp_cmd(qmp_sock, 'screendump', {'filename': str(f_target), 'format': 'png'})
                if f_target.exists():
                    f_sz = f_target.stat().st_size
                    best_path = OUT / 'fastjit-macos27-frame.png'
                    if (not best_path.exists() or f_sz > 6200) and present_idx == 0:
                        shutil.copy2(f_target, best_path)
                    print(f'[Runner] Captured {f_target.name} ({f_sz} bytes) at {elapsed:.1f}s', flush=True)
            except Exception as e:
                print(f'[Runner] Periodic screendump note: {e}', flush=True)
            for src, name in [(stderr_path, 'stderr.log'), (serial_path, 'serial.log'), (reims_log_path, 'reims-vgpu-fail.log')]:
                if src.exists():
                    try:
                        content = redact(src.read_text(encoding='utf-8', errors='replace'), tokens)
                        (OUT / name).write_text(content[-4 * 1024 * 1024:], encoding='utf-8')
                    except Exception:
                        pass

        if elapsed >= next_status_t:
            next_status_t = elapsed + 5.0
            st_text = stderr_path.read_text(encoding='utf-8', errors='replace') if stderr_path.exists() else ''
            ser_text = serial_path.read_text(encoding='utf-8', errors='replace') if serial_path.exists() else ''
            nbd_info = nbd_stats_path.read_text(encoding='utf-8') if nbd_stats_path.exists() else '{}'
            nbd_layer_path = WORK_TMP / 'nbd_layer.log'
            nbd_layer_lines = nbd_layer_path.read_text(encoding='utf-8', errors='replace').splitlines() if nbd_layer_path.exists() else []
            reims_sz = reims_log_path.stat().st_size if reims_log_path.exists() else 0
            reims_note = ''
            if reims_sz > 0:
                try:
                    with reims_log_path.open('rb') as rf:
                        rf.seek(max(0, reims_sz - 65536))
                        rtail = rf.read().decode('utf-8', errors='replace').splitlines()
                    rhits = [l for l in rtail if 'define_task' in l or 'present_content' in l]
                    if rhits:
                        reims_note = f' | gpu={rhits[-1]}'
                except Exception:
                    pass
            fastjit_lines = [ln for ln in st_text.splitlines() if '[FastJIT]' in ln]
            latest_fj = fastjit_lines[-1] if fastjit_lines else 'waiting...'
            layer_note = f' | {nbd_layer_lines[-1]}' if nbd_layer_lines else ''
            print(f'[{elapsed:5.1f}s] serial={len(ser_text)}B | reims={reims_sz}B{reims_note} | nbd={nbd_info}{layer_note} | {latest_fj}', flush=True)

    # Capture final screendump before stopping
    qmp_sock.settimeout(3.0)
    frame_idx += 1
    frame_path = frames_dir / f'frame-{frame_idx:04d}.png'
    try:
        qmp_cmd(qmp_sock, 'screendump', {'filename': str(frame_path), 'format': 'png'})
        if frame_path.exists():
            f_sz = frame_path.stat().st_size
            best_path = OUT / 'fastjit-macos27-frame.png'
            if (not best_path.exists() or f_sz > 6200) and present_idx == 0:
                shutil.copy2(frame_path, best_path)
    except Exception as e:
        print(f'[Runner] screendump note: {e}', flush=True)

    try:
        qmp_cmd(qmp_sock, 'quit')
    except Exception:
        pass
    try:
        vm.wait(timeout=3)
    except subprocess.TimeoutExpired:
        vm.kill()
    if hook.poll() is None:
        hook.kill()
    subprocess.run(['pkill', '-9', '-f', 'nbdkit'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    stderr_file.close()
    gdb_file.close()

    # Save redacted logs to OUT
    for src, name in [(stderr_path, 'stderr.log'), (serial_path, 'serial.log'), (gdb_log_path, 'gdb.log'), (handoff_path, 'handoff.json'), (reims_log_path, 'reims-vgpu-fail.log')]:
        if src.exists():
            content = redact(src.read_text(encoding='utf-8', errors='replace'), tokens)
            (OUT / name).write_text(content[-4 * 1024 * 1024:], encoding='utf-8')

    st_final = (OUT / 'stderr.log').read_text(encoding='utf-8') if (OUT / 'stderr.log').exists() else ''
    ser_final = (OUT / 'serial.log').read_text(encoding='utf-8') if (OUT / 'serial.log').exists() else ''
    fj_all = [ln for ln in st_final.splitlines() if '[FastJIT]' in ln]
    nbd_final = json.loads(nbd_stats_path.read_text(encoding='utf-8')) if nbd_stats_path.exists() else {}
    nbd_layer_final = (WORK_TMP / 'nbd_layer.log').read_text(encoding='utf-8', errors='replace').splitlines() if (WORK_TMP / 'nbd_layer.log').exists() else []
    captured_frames = [
        {'name': p.name, 'bytes': p.stat().st_size}
        for p in sorted(list(frames_dir.glob('present-*.png')) + list(frames_dir.glob('frame-*.png')))
    ]
    summary = {
        'status': 'RUN_COMPLETE',
        'vulkan_mode': vulkan_mode,
        'smp': 10,
        'handoff_verified': handoff_path.exists(),
        'nbd_stats': nbd_final,
        'nbd_layer_events': nbd_layer_final[-20:],
        'reims_vgpu_log_bytes': reims_log_path.stat().st_size if reims_log_path.exists() else 0,
        'frames_captured': captured_frames,
        'serial_bytes': len(ser_final),
        'serial_lines': len(ser_final.splitlines()),
        'fastjit_telemetry_lines': fj_all,
        'serial_preview_head': ser_final.splitlines()[:15],
        'serial_preview_tail': ser_final.splitlines()[-25:],
    }
    (OUT / 'fastjit-boot-summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
