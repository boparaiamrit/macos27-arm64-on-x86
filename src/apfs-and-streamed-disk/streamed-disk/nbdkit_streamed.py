"""nbdkit Python API 2; one initialized source shared across all connections."""
import errno
import sys
from pathlib import Path
import os
import faulthandler
import signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nbdkit
from streamed_raw import initialize, emit, MAX_READ, cache_layer_count
from supervision import ChildControl

API_VERSION = 2
OPTIONS = {}
DISK = None
CONTROL = None
if os.environ.get("STREAMED_DISK_TEST_MODE") == "1":
    faulthandler.register(signal.SIGUSR1, all_threads=True)
ALLOWED = {"manifest", "config", "host-space", "manifest-digest", "repository",
           "cache-layers", "warm-layer-zero", "fixture-url"}


def config(key, value):
    if key not in ALLOWED or key in OPTIONS:
        raise ValueError("unknown or duplicate plugin option")
    OPTIONS[key] = value


def config_complete():
    global CONTROL
    if not {"manifest", "config", "host-space"} <= OPTIONS.keys():
        raise ValueError("manifest, config and host-space are required")
    cache_layer_count(OPTIONS.get("cache-layers", "2"))
    if OPTIONS.get("warm-layer-zero", "false") not in ("true", "false"):
        raise ValueError("warm-layer-zero must be true or false")
    try:
        CONTROL = ChildControl.from_environment()
    except Exception as exc:
        emit("supervisor_required", error_type=type(exc).__name__)
        raise


def thread_model():
    return nbdkit.THREAD_MODEL_SERIALIZE_ALL_REQUESTS


def get_ready():
    global DISK
    try:
        DISK = initialize(OPTIONS, control=CONTROL)
    except Exception as exc:
        emit("initialization_error", error_type=type(exc).__name__)
        raise RuntimeError(f"initialization failed ({type(exc).__name__}); see JSON telemetry") from None


def stop_for_guard():
    nbdkit.set_error(errno.ENOSPC)
    nbdkit.shutdown()


def after_fork():
    DISK.guard.check()
    CONTROL.initialized()
    emit("export_ready", manifest_pin=DISK.source.pins.manifest_digest,
         config_pin=DISK.source.pins.config_digest, planDigest=DISK.plan.fingerprint(),
         getsize=DISK.size, readonly=True, max_read_bytes=MAX_READ,
         thread_model="SERIALIZE_ALL_REQUESTS", bitmap_bytes=DISK.plan.bitmap_bytes)


def open(readonly):
    try:
        DISK.guard.check()
    except Exception:
        stop_for_guard()
        raise
    return DISK


def get_size(h):
    return h.size


def block_size(h):
    return (1, 4096, MAX_READ)


def can_write(h):
    return False


def can_multi_conn(h):
    return True


def can_cache(h):
    return nbdkit.CACHE_NONE


def can_trim(h):
    return False


def can_zero(h):
    return False


def pread(h, buf, offset, flags):
    try:
        buf[:] = h.read_at(offset, len(buf))
    except Exception as exc:
        emit("read_error", error_type=type(exc).__name__, offset=offset, count=len(buf))
        try:
            h.guard.check()
        except Exception:
            stop_for_guard()
        raise RuntimeError(f"RAW read failed ({type(exc).__name__})") from None


def pwrite(h, buf, offset, flags):
    nbdkit.set_error(errno.EROFS)
    raise RuntimeError("read-only RAW export")


def cleanup():
    if DISK:
        DISK.close()
    if CONTROL:
        CONTROL.close()
