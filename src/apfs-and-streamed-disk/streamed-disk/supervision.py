"""Small inherited lifecycle channel; no worker threads or payload bytes."""
import json
import math
import os
import socket
import struct
import time

LAYER_SECONDS = 900.0
# Seven cold metadata layers plus warmup measured roughly 150 s per layer.
# Startup gets a separate finite budget; each individual layer remains bounded.
INIT_SECONDS = 3600.0
POLL_SECONDS = .05
KILL_GRACE_SECONDS = 5.0


class ChildControl:
    def __init__(self, channel, layer_seconds, initialization_deadline):
        self.channel, self.layer_seconds = channel, layer_seconds
        self.initialization_deadline = initialization_deadline

    @classmethod
    def from_environment(cls):
        try:
            parent = int(os.environ["STREAMED_DISK_SUPERVISOR_PID"])
            if parent != os.getppid():
                raise ValueError("wrong supervisor parent")
            channel = socket.socket(fileno=int(os.environ["STREAMED_DISK_SUPERVISOR_FD"]))
            if channel.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) != socket.SOCK_DGRAM:
                raise ValueError("wrong supervisor socket type")
            peer, _, _ = struct.unpack("3i", channel.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            if peer != parent:
                raise ValueError("wrong supervisor peer")
            channel.settimeout(2)
            hello = json.loads(channel.recv(4096))
            seconds = hello["layer_seconds"]
            init_deadline = hello["initialization_deadline"]
            if (hello["event"] != "supervisor_hello" or type(seconds) not in (int, float)
                    or not math.isfinite(seconds) or not 0 < seconds <= LAYER_SECONDS
                    or type(init_deadline) not in (int, float) or not math.isfinite(init_deadline)
                    or not 0 < init_deadline - time.monotonic() <= INIT_SECONDS):
                raise ValueError("invalid supervisor hello")
            channel.settimeout(None)
            return cls(channel, seconds, init_deadline)
        except (KeyError, OSError, ValueError, TypeError) as exc:
            raise RuntimeError("plugin requires the serve.py supervisor; bare nbdkit is unsupported") from exc

    def notify(self, event, **fields):
        self.channel.send(json.dumps(dict(event=event, **fields)).encode())

    def layer_start(self):
        deadline = time.monotonic() + self.layer_seconds
        self.notify("layer_start", deadline=deadline)
        return deadline

    def layer_end(self):
        self.notify("layer_end")

    def initialized(self):
        if time.monotonic() >= self.initialization_deadline:
            raise TimeoutError("initialization exceeded its wall deadline")
        self.notify("initialized")

    def close(self):
        self.channel.close()
