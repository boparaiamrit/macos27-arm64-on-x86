# Windows monitor sample-open failure

Verified source defect: execute-bounded-20261027.py's guard read used one
Path.read_bytes() call. Every PermissionError stopped the owned helper, with no
opportunity to read the next fresh sample. The saved run stopped with Errno 13
while its preceding sample was 0.960 seconds old and reported 21,186,609,152 free
bytes. It did not observe low space or stale data at that stop.

Windows sample replacement and file-sharing contention are a possible source
of the denied open; the captured event does not identify which handle denied
it. A real temporary exclusive Windows file handle reproduces the same denied
read and tests recovery after release. The correction retries only denied or
missing opens for at most 0.5 seconds, then validates the newly read sample.
It never uses cached sample data, accepts stale samples, relaxes the 10 GiB
floor, or retries invalid/low/stale content.

The later backend shutdown was a separate stale-sample event after the T3
restart cancelled the sampler. The backend's fail-closed behavior is retained.
