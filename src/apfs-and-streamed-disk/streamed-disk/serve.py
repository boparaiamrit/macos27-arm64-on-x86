#!/usr/bin/env python3
"""Supervise a read-only nbdkit process, including blocked initialization/I/O."""
import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import time

from streamed_raw import HostSpaceGuard, GuardError, emit, cache_layer_count
from supervision import LAYER_SECONDS, INIT_SECONDS, POLL_SECONDS, KILL_GRACE_SECONDS


def group_exists(process):
    # A Linux subreaper lets us reap descendants as well as the nbdkit leader.
    if process.poll() is not None:
        while True:
            try:
                pid, _ = os.waitpid(-process.pid, os.WNOHANG)
                if not pid:
                    break
            except ChildProcessError:
                break
    try:
        os.killpg(process.pid, 0)
        return True
    except ProcessLookupError:
        return False


def stop_group(process, grace):
    if not group_exists(process):
        return
    emit("supervisor_terminate", child_pid=process.pid, grace_seconds=grace)
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + grace
    while group_exists(process) and time.monotonic() < deadline:
        time.sleep(min(POLL_SECONDS, max(0, deadline - time.monotonic())))
    if group_exists(process):
        emit("supervisor_kill", child_pid=process.pid)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=1)
    deadline = time.monotonic() + 1
    while group_exists(process) and time.monotonic() < deadline:
        time.sleep(POLL_SECONDS)
    if group_exists(process):
        raise RuntimeError("owned process group survived SIGKILL/reap bound")
    emit("supervisor_group_reaped", child_pid=process.pid)


def bounded_seconds(value, maximum):
    result = float(value)
    if not math.isfinite(result) or not 0 < result <= maximum:
        raise argparse.ArgumentTypeError(f"seconds must be positive and at most {maximum:g}")
    return result


def supervise(command, guard, layer_seconds=LAYER_SECONDS, init_seconds=INIT_SECONDS,
              grace=KILL_GRACE_SECONDS):
    # This is a separate process, never a thread created before nbdkit forks.
    for value, maximum in [(layer_seconds, LAYER_SECONDS), (init_seconds, INIT_SECONDS),
                           (grace, KILL_GRACE_SECONDS)]:
        bounded_seconds(value, maximum)
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
    process, received_signal = None, []
    previous = {}
    try:
        guard.check()
        if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
            raise RuntimeError("cannot enable owned-descendant reaping")
        for signum in (signal.SIGTERM, signal.SIGINT):
            previous[signum] = signal.signal(signum, lambda sig, frame: received_signal.append(sig))
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1",
                   STREAMED_DISK_SUPERVISOR_FD=str(child.fileno()),
                   STREAMED_DISK_SUPERVISOR_PID=str(os.getpid()))
        started = time.monotonic()
        parent.send(json.dumps({"event": "supervisor_hello", "layer_seconds": layer_seconds,
                                "initialization_deadline": started + init_seconds}).encode())
        process = subprocess.Popen(command, env=env, pass_fds=(child.fileno(),), start_new_session=True)
        child.close()
        emit("supervisor_started", child_pid=process.pid, layer_deadline_seconds=layer_seconds,
             initialization_deadline_seconds=init_seconds, guard_poll_seconds=POLL_SECONDS,
             termination_grace_seconds=grace)
        initialized, layer_deadline = False, None
        while True:
            # Late completions cannot disarm expired deadlines. No payload
            # traverses this status socket.
            guard.check()
            now = time.monotonic()
            scope = ("initialization" if not initialized and now >= started + init_seconds else
                     "layer" if layer_deadline is not None and now >= layer_deadline else None)
            if scope:
                emit("supervisor_deadline_stop", scope=scope, child_pid=process.pid)
                return 1
            if received_signal:
                emit("supervisor_signal_stop", signal=received_signal[0], child_pid=process.pid)
                return 128 + received_signal[0]
            if process.poll() is not None:
                return process.returncode if process.returncode >= 0 else 128 - process.returncode
            wait = min(POLL_SECONDS, max(0, started + init_seconds - now)) if not initialized else POLL_SECONDS
            if layer_deadline is not None:
                wait = min(wait, max(0, layer_deadline - now))
            ready, _, _ = select.select([parent], [], [], wait)
            if not ready:
                continue
            message = json.loads(parent.recv(4096))
            event = message["event"]
            if event == "layer_start" and layer_deadline is None:
                value = message["deadline"]
                if type(value) not in (int, float) or not math.isfinite(value):
                    raise ValueError("invalid layer deadline")
                layer_deadline = min(value, time.monotonic() + layer_seconds)
            elif event == "layer_end" and layer_deadline is not None:
                if time.monotonic() >= layer_deadline:
                    emit("supervisor_deadline_stop", scope="layer", child_pid=process.pid)
                    return 1
                layer_deadline = None
            elif event == "initialized" and not initialized and layer_deadline is None:
                if time.monotonic() >= started + init_seconds:
                    emit("supervisor_deadline_stop", scope="initialization", child_pid=process.pid)
                    return 1
                initialized = True
            else:
                raise ValueError("invalid supervisor lifecycle event")
    except GuardError as exc:
        emit("guard_stop", owner="supervisor", reason=str(exc))
        return 1
    except Exception as exc:
        emit("supervisor_error", error_type=type(exc).__name__)
        return 1
    finally:
        try:
            if process is not None:
                stop_group(process, grace)
                emit("supervisor_stopped", child_pid=process.pid, child_returncode=process.returncode)
        finally:
            parent.close()
            child.close()
            for signum, handler in previous.items():
                signal.signal(signum, handler)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--socket", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--host-space", required=True)
    p.add_argument("--repository", default="cirruslabs/macos-golden-gate-vanilla")
    p.add_argument("--cache-layers", type=cache_layer_count, choices=range(1, 9), default=2)
    p.add_argument("--warm-layer-zero", action="store_true")
    p.add_argument("--layer-deadline-seconds", type=lambda v: bounded_seconds(v, LAYER_SECONDS), default=LAYER_SECONDS)
    p.add_argument("--initialization-deadline-seconds", type=lambda v: bounded_seconds(v, INIT_SECONDS), default=INIT_SECONDS)
    p.add_argument("--termination-grace-seconds", type=lambda v: bounded_seconds(v, KILL_GRACE_SECONDS), default=KILL_GRACE_SECONDS)
    if os.environ.get("STREAMED_DISK_TEST_MODE") == "1":
        p.add_argument("--fixture-url")
        p.add_argument("--manifest-digest")
    args = p.parse_args()
    path = Path(args.socket)
    if not path.is_absolute() or path.exists() or path.is_symlink():
        p.error("socket must be a new absolute path on a Linux filesystem")
    options = [f"manifest={Path(args.manifest).resolve()}", f"config={Path(args.config).resolve()}",
               f"host-space={Path(args.host_space).resolve()}", f"repository={args.repository}",
               f"cache-layers={args.cache_layers}",
               f"warm-layer-zero={str(args.warm_layer_zero).lower()}"]
    if getattr(args, "fixture_url", None):
        options.append(f"fixture-url={args.fixture_url}")
    if getattr(args, "manifest_digest", None):
        options.append(f"manifest-digest={args.manifest_digest}")
    command = ["nbdkit", "-f", "-r", "--exit-with-parent", "--log=stderr", "-U", str(path),
               "python", str(Path(__file__).resolve().with_name("nbdkit_streamed.py")), *options]
    return supervise(command, HostSpaceGuard(args.host_space), args.layer_deadline_seconds,
                     args.initialization_deadline_seconds, args.termination_grace_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
