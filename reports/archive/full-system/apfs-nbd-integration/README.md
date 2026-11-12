# Local restore APFS / NBD integration evidence

Run from the repository root:

```powershell
python -B test-output/arm-macos/full-system/test_apfs_nbd_integration.py
```

The test uses the existing restore RAMdisk without copying payloads. It pins the
current `macos-streamed-guest:local` image ID, starts one read-only, network-none
container with 1 GiB RAM and two CPUs, and mounts `arm-macos` read-only at
`/parent`. A private 1 MiB `/tmp` holds only the nbdkit Unix socket. Windows free
space is checked throughout against the 10 GiB floor. Deadlines are 90 seconds
in Python, 100 seconds in the container, and 105 seconds on the host. Only this
test's named container is terminated if a deadline or reserve check fails.

## Verified run: 20261027T054625Z

- Result: PASS, exit code 0; 10.241 seconds on the host, 9.010 in the container.
- Image: `sha256:3588626af89be155e5f058e0afcef8c354178b6083192e876549ccd80b643312`.
- Input: 373,293,056-byte raw APFS `darwin/firmware/ramdisk.dmg`.
- Input SHA-256: `ba6ae4e7efea8fa20316b72f50e0c9d27f04378562221c7626a0764bf810ac50`.
- Actual SystemVersion: macOS 27.0.1, build 26A434, ReleaseType Restore.
- Plist: 654 bytes; SHA-256 `554f47cd7e516cee24e2d919a2a7493abb21da0c4a773406ff5fcf3ffe8bca92`.
- Shared `guest_artifacts.discover`: visited `/`, produced a 21-entry census,
  and returned zero firmware candidates. A direct APFS read independently
  confirmed the firmware path is absent.
- Both discovery and direct reads exercised the staged decmpfs type-9 decoder:
  655 encoded bytes beginning with `cc` became the same 654-byte XML plist.
  Observation wrappers call the existing decoder unchanged.
- Discovery: 13 real adapter reads, 786,436 returned bytes.
- Direct fs_explorer: 12 real adapter reads, 786,432 returned bytes.
- Total: 25 reads, 1,572,868 returned bytes; maximum request 65,536 bytes.
- Minimum sampled Windows free space: 23,861,526,528 bytes.
- All three frozen converter hashes exactly matched the test constants, loader,
  and reviewed manifest. Imported module paths and hashes, read transcript
  hashes, command, full census, and decoder observations are in the JSON.

No integration defect was observed. This fixture exposes one flattened APFS
volume at `/`; traversal across multiple volume entries is not exercised. This
test establishes local file-plugin / NBDSource / APFS / type-9 compression
integration. It does not establish remote streamed backing behavior or guest
boot behavior. No parent source was edited and no guest or VM was run.

Files: [JSON evidence](20261027T054625Z.json), [raw log](20261027T054625Z.log),
and [test](../test_apfs_nbd_integration.py).
