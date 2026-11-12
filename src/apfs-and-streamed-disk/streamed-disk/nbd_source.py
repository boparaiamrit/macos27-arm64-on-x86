"""libnbd RandomAccess adapter accepted directly by fs_explorer.open_source."""
import argparse
import json
import threading
import nbd
from frozen import APFS  # verifies reviewed sources and locates the staged reader
from fs_explorer.io.source import RandomAccess

MAX_READ = 32 << 20


class NBDSource(RandomAccess):
    def __init__(self, socket):
        self._lock = threading.RLock()
        self._h = nbd.NBD()
        try:
            self._h.connect_unix(str(socket))
            if not self._h.is_read_only():
                raise ValueError("refusing a writable NBD backing export")
            self.size = self._h.get_size()
        except BaseException:
            self._h = None
            raise

    def getsize(self):
        return self.size

    def read_at(self, offset, length):
        if type(offset) is not int or type(length) is not int or offset < 0 or length < 0:
            raise ValueError("invalid NBD read")
        if length > MAX_READ:
            raise ValueError("NBD adapter read exceeds 32 MiB")
        with self._lock:
            if self._h is None:
                raise ValueError("NBD source is closed")
            # RandomAccess returns short bytes only at EOF; read_exact rejects that.
            count = min(length, max(0, self.size - offset))
            return self._h.pread(count, offset) if count else b""

    def close(self):
        with self._lock:
            if self._h is not None:
                h, self._h = self._h, None
                try:
                    h.shutdown()
                finally:
                    del h  # libnbd Python owns/closes the C handle on collection.

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("socket")
    args = parser.parse_args()
    with NBDSource(args.socket) as source:
        print(json.dumps({"getsize": source.getsize(), "readonly": True,
                          "prefix_hex": source.read_at(0, 512).hex()}))
