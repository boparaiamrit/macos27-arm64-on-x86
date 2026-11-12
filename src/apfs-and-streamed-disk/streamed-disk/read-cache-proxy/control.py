"""Inherited private lifecycle channel: no threads, payload or network input."""
import json
import math
import os
import socket
import struct
import time
from common import MAX_OPERATION_SECONDS, require


class Control:
    @classmethod
    def environment(cls):
        parent = int(os.environ['READ_CACHE_SUPERVISOR_PID'])
        require(parent == os.getppid(), 'wrong supervisor parent')
        channel = socket.socket(fileno=int(os.environ['READ_CACHE_SUPERVISOR_FD']))
        require(channel.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) == socket.SOCK_DGRAM,
                'wrong control socket')
        peer, _, _ = struct.unpack('3i', channel.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        require(peer == parent, 'wrong supervisor peer')
        channel.settimeout(2)
        hello = json.loads(channel.recv(4096))
        seconds = hello['seconds']
        deadline = hello['initialization_deadline']
        require(hello['event'] == 'hello' and type(seconds) in (int, float) and
                math.isfinite(seconds) and 0 < seconds <= MAX_OPERATION_SECONDS and
                type(deadline) in (int, float) and math.isfinite(deadline) and
                0 < deadline-time.monotonic() <= MAX_OPERATION_SECONDS, 'invalid supervisor hello')
        channel.settimeout(None)
        result = cls()
        result.channel, result.seconds, result.initialization_deadline = channel, seconds, deadline
        return result

    def send(self, event, **fields):
        self.channel.send(json.dumps(dict(event=event, **fields)).encode())

    def start(self):
        self.send('start', deadline=time.monotonic()+self.seconds)

    def end(self):
        self.send('end')

    def ready(self):
        require(time.monotonic() < self.initialization_deadline, 'initialization deadline')
        self.send('ready')
