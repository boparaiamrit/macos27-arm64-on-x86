"""Read a fresh Windows guard sample across brief file-sharing contention."""
import json
import math
from pathlib import Path
import time


def read_valid_sample(path, retry_seconds=.5):
    """Retry only denied/missing opens; never reuse an old or invalid sample."""
    if not math.isfinite(retry_seconds) or not 0 <= retry_seconds <= .5:
        raise ValueError('Sample-open retry must be between zero and 0.5 seconds')
    deadline = time.monotonic() + retry_seconds
    while True:
        try:
            data = Path(path).read_bytes()
            break
        except (PermissionError, FileNotFoundError):
            left = deadline - time.monotonic()
            if left <= 0:
                raise
            time.sleep(min(.01, left))
    sample = json.loads(data)
    if str(sample['drive']).upper().rstrip('\\/') != 'C:':
        raise RuntimeError('host guard: sample is not C:')
    free = sample['free_bytes']
    if type(free) is not int or free < 10 * 1024**3:
        raise RuntimeError('host guard: reserve below 10 GiB or invalid')
    observed = sample['observed_at']
    if type(observed) not in (int, float) or not math.isfinite(observed) or not -2 <= time.time() - observed <= 20:
        raise RuntimeError('host guard: sample stale beyond 20 seconds or from future')
    return sample
