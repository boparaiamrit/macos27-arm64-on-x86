#!/usr/bin/env python3
"""Externally supervise the readonly NBD returned-block cache, including startup."""
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
from common import Guard, MAX_OPERATION_SECONDS, POLL, emit, require, check_directory, admit_resources, Refused


def seconds(value):
    value = float(value)
    if not math.isfinite(value) or not 0 < value <= MAX_OPERATION_SECONDS:
        raise argparse.ArgumentTypeError('deadline must be finite and in (0,900]')
    return value


def group_exists(process):
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


def stop_group(process, grace=1):
    if not group_exists(process):
        return
    emit('terminate', child_pid=process.pid)
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic()+grace
    while group_exists(process) and time.monotonic() < deadline:
        time.sleep(POLL)
    if group_exists(process):
        emit('kill', child_pid=process.pid)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=1)
    deadline = time.monotonic()+1
    while group_exists(process) and time.monotonic() < deadline:
        time.sleep(POLL)
    require(not group_exists(process), 'owned group not reaped')


def supervise(command, guard, operation_seconds=900, initialization_seconds=900):
    seconds(operation_seconds)
    seconds(initialization_seconds)
    process = None
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
    stopped = []
    previous = {}
    try:
        guard.check()
        require(ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0, 'subreaper unavailable')
        for sig in (signal.SIGTERM, signal.SIGINT):
            previous[sig] = signal.signal(sig, lambda value, frame: stopped.append(value))
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
                   READ_CACHE_SUPERVISOR_PID=str(os.getpid()), READ_CACHE_SUPERVISOR_FD=str(child.fileno()))
        begin = time.monotonic()
        parent.send(json.dumps(dict(event='hello', seconds=operation_seconds,
                                   initialization_deadline=begin+initialization_seconds)).encode())
        process = subprocess.Popen(command, env=env, pass_fds=(child.fileno(),), start_new_session=True)
        child.close()
        emit('supervisor_started', child_pid=process.pid, operation_seconds=operation_seconds,
             initialization_seconds=initialization_seconds, poll_seconds=POLL)
        initialized, active = False, None
        while True:
            guard.check()
            now = time.monotonic()
            if (not initialized and now >= begin+initialization_seconds) or (active is not None and now >= active):
                emit('deadline_stop', scope='operation' if active is not None else 'initialization')
                return 1
            if stopped:
                emit('signal_stop', signal=stopped[0])
                return 128+stopped[0]
            if process.poll() is not None:
                return process.returncode if process.returncode >= 0 else 128-process.returncode
            ready, _, _ = select.select([parent], [], [], POLL)
            if not ready:
                continue
            message = json.loads(parent.recv(4096))
            event = message['event']
            if event == 'ready' and not initialized and active is None:
                require(time.monotonic() < begin+initialization_seconds, 'late initialization')
                initialized = True
            elif event == 'start' and initialized and active is None:
                value = message['deadline']
                require(type(value) in (int, float) and math.isfinite(value), 'invalid operation deadline')
                active = min(value, time.monotonic()+operation_seconds)
            elif event == 'end' and active is not None:
                require(time.monotonic() < active, 'late operation completion')
                active = None
            elif event == 'fatal':
                emit('read_failure_stop')
                return 1
            else:
                raise ValueError('invalid control event')
    except Exception as exc:
        emit('supervisor_stop', error_type=type(exc).__name__,
             reason=str(exc) if isinstance(exc,Refused) else 'guard or runtime exception')
        return 1
    finally:
        try:
            if process is not None:
                stop_group(process)
                emit('supervisor_stopped', child_pid=process.pid, child_returncode=process.returncode)
        finally:
            parent.close()
            child.close()
            for sig, handler in previous.items():
                signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    for option in ('socket', 'upstream', 'ready', 'cache', 'host-space'):
        parser.add_argument('--'+option, required=True, type=Path)
    parser.add_argument('--operation-seconds', type=seconds, default=900.)
    parser.add_argument('--initialization-seconds', type=seconds, default=900.)
    args = parser.parse_args()
    admit_resources()
    output = args.socket
    require(output.is_absolute() and output.parent == output.parent.resolve(), 'noncanonical socket path')
    check_directory(output.parent)
    require(not output.exists() and not output.is_symlink(), 'export socket already exists')
    check_directory(args.cache)
    options = [f'{name}={getattr(args, name.replace("-", "_"))}'
               for name in ('upstream', 'ready', 'cache', 'host-space')]
    command = ['nbdkit', '-f', '-r', '--exit-with-parent', '--log=stderr', '-U', str(output),
               'python', str(Path(__file__).with_name('plugin.py')), *options]
    return supervise(command, Guard(args.host_space, args.cache), args.operation_seconds, args.initialization_seconds)


if __name__ == '__main__':
    raise SystemExit(main())
