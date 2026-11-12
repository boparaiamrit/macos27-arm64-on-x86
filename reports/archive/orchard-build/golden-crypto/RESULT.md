# Required nettle backend qualification

The isolated QEMU build passes real VMApple AES known-answer tests. The previous CTRR executable reproduces the cipher failure on the same synthetic input. No Apple guest was booted by this task.

New executable in volume `macos-orchard-build`:

```text
/work/orchard-golden-crypto/qemu/build/qemu-system-aarch64
b4c7d59055e30c931ecade17ecf08f806baba7814a1477513d85d57872e3e6f0
```

The exported `artifacts/qemu-system-aarch64` is 70,531,000 bytes. Linux hashing and independent Windows `Get-FileHash` agree. The parent owns profile admission, identity migration and any actual boot.

## Cause and scope

The preserved CTRR configuration has no nettle, gcrypt, GNUTLS crypto or AF_ALG backend. Existing `crypto/cipher.c` consequently selects `cipher-stub.c.inc`, which always refuses cipher creation. Existing VMApple `aes.c` discards that error detail and reports `Failed to create cipher object`. This establishes defective AES operations; it does not independently identify the precise guest wait location.

The new source is byte-identical to CTRR across all 12,031 tracked paths. Its complete tracked diff is identical to `golden-ctrr/orchard-golden-ctrr.diff`. There are no AES FIFO/context, CPU, board, storage, firmware, authentication, renderer or guest-source patches. Configure retains the prior arguments and adds `--enable-nettle --disable-gcrypt --disable-gnutls`. Both other libraries were already absent. The generated configuration requires `CONFIG_NETTLE`; configure reports nettle 3.10.1. Selecting nettle also selects QEMU's existing nettle hash/HMAC/PBKDF implementations.

The separate VMApple report at [pinned upstream README](https://github.com/DenrianWeiss/w515y-vmapple-scripts/blob/c309bbb59f276762d87e88962e3f4181993b69da/README.md#L195) describes the same AppleVPKeyStore boundary without a crypto backend. That report concerns macOS 13/KVM and is supporting evidence, not Golden/TCG boot proof.

## Actual verification

`test-aes-mmio.py` launches each actual executable with synthetic four-byte firmware and two 16-KiB synthetic disks. Both CPUs remain paused throughout. Qtest writes the actual VMApple AES FIFO and DMA buffers; QMP verifies paused status before and after. Public NIST SP800-38A first-block vectors qualify AES-128/192/256, ECB/CBC, encryption/decryption: **12/12 pass** on the new executable. The old executable leaves the destination sentinel unchanged and logs the expected cipher-creation failure on the identical first ECB-AES128 request. This tests the actual compiled device/backend path, rather than merely nettle's standalone API or ELF linking. Context switching, multi-request IV chaining and all possible FIFO sequences are outside these tests.

The existing paused synthetic suites also pass: scratch RAM/reset/config preservation; diagnostic RTC storage/reset and transaction predicate under UBSan; unavailable-CTRR probes; and ascending root/AUX/network PCI capabilities with Apple transport fields. No CPU was resumed and no Apple OS input was supplied.

Qualification used the exact existing runtime image `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`. Its existing `libnettle.so.8.10` is 3.10.1-1; `ldd-runtime.log` resolves all dependencies, including nettle, under the same software-library environment. No runtime libraries or host software were installed or replaced.

## Dependency and reproducibility

Existing builder image `sha256:0a0cabc8b884c695e9264ef533d91c4fa672e57d067f0d6b5bc429628ca8817e` remains untouched. A new disposable preparation container installed only the required pinned Debian development package and was committed as `macos-orchard-crypto-builder:local`, image `sha256:14ea78615d69de5eea70014968be23464751916c6c44793f19f5771a9b4eeb17`.

Package: `nettle-dev=3.10.1-1`, 1,317,924 bytes, SHA256 `686dc13aaa2804161dbc7c916a664bf37fb7bb9a8128b6e025fa45ab06804e3a`. The hash and size were checked against authenticated Debian apt metadata before installation. Retained apt indexes plus payload total 21,575,611 bytes, below the 100-MiB fetch budget. Preparation took 7.711 seconds. Actual configure/build and all tests ran with networking disabled. Existing subprojects, offline wheels/Python environment and unchanged Reims static archive were reused; no Rust build occurred.

`prepare.py`, `build.py` and `finish.py` preserve the commands and guards. Build mounts the volume at `/work` RW only for the new tree, and overmounts `/work/orchard`, `/work/orchard-golden`, `/work/orchard-golden-scratch`, `/work/orchard-golden-avprtc` and `/work/orchard-golden-ctrr` read-only from their volume subpaths. Bind the ARM experiment directory at `/parent` RO, this directory at `/out` RW, prior golden directory at `/golden` RO and CTRR directory at `/ctrr` RO. Run with the new builder, `--network none --cpus=6 --memory=6g --memory-swap=6g --pids-limit=512`, entrypoint `python3 /out/build.py`. It deliberately refuses to overwrite the existing new tree.

For repeat qualification of the preserved artifact, mount the build volume `/work` RO, ARM directory `/parent` RO, this directory `/out` RW, and the existing `golden/runtime` directory `/out/runtime` RO. Use the pinned runtime image above, `--read-only --network none --cpus=4 --memory=6g --memory-swap=6g --pids-limit=256 --tmpfs /tmp:rw,exec,nosuid,nodev,size=64m`, entrypoint `python3 /out/qualify.py`. The explicit temporary `exec` permits the bounded UBSan C predicate test; no guest CPU is run.

## Preservation, resources and resolved orchestration errors

Full before/after regular-file and symlink manifests match for all five previous trees. The previous executable and static renderer remain unchanged. Source graph tools were unavailable; exact source and build evidence were inspected directly.

The initial orchestration asserted that a generated macro included a literal `1`; QEMU emits a valueless define. Configure had succeeded, and the task stopped before compilation. The owned guard was corrected, and `finish.py` resumed that prepared tree without changing source/configuration. The first runtime test attempt failed because Docker's temporary mount defaulted to `noexec`; no machine test had started. That log/container are preserved in `qualification-initial-tmp-noexec/`. An explicit executable temporary mount fixed only the test environment. Final qualification passes.

Successful finish/build: 104.670 seconds, peak memory 1,535,819,776 bytes under 6-GiB/6-CPU limits, zero OOM. Runtime qualification: 3.453 seconds, peak memory 94,580,736 bytes under finite 6-GiB/4-CPU limits, zero OOM. Host samples retain the unconditional 10-GiB floor, maximum 20-second age and two-second future tolerance; the process supervisor checks every 200 ms during preparation/build/tests. Minimum successful-build free space was 27,015,430,144 bytes.

Measured task allocation: new tree 440,889,344 bytes; host outputs 94,941,238 nominal bytes at measurement; new builder image size delta 44,126,735 bytes, about 0.54 GiB combined before small final reports. These are task-path/image measurements, not complete host VHDX growth or physical NTFS accounting. All seven owned containers are stopped and retained. The existing backend and sampler were never changed. No guest files, identities, profiles, runner, launcher or host settings were modified.
