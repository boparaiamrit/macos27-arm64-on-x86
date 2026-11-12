# Isolated stage-interface build result

The one exact parent-prepared build passed. Attempt count: 1; retries: 0. Elapsed time: 413.021 seconds (6.88 minutes), including container startup and cleanup.
Started 2026-10-28T19:25:39.0518109Z; finished 2026-10-28T19:32:32.0762429Z.

The new artifacts remain in Docker volume `macos-orchard-build`, under `/work/orchard-m27-pages-io/artifacts/`:

- `qemu-system-aarch64`: 70,830,832 bytes; SHA256 `8db719ff2982a216e64aa2303c8731bdc0d8a2051919f69bc95bbcbd1dd3829b`.
- `libreims_vgpu.a`: 174,861,242 bytes; SHA256 `d9bfdcc73209bf4ead5e52469ae66a6cbfe3566430b9f2e0e0c1ad98bec9abaf`.

`qemu-version.log` records `QEMU emulator version 11.1.50`. The only QEMU execution was the script's `--version` check. QEMU linking used the admitted base objects and the new archive, with the output directed solely to the new variant.

## Verification

- Shader-cache suite: **44 passed, 0 failed**, 0 ignored; 2,223 filtered out; test execution 0.12 s.
- Capture suite: **10 passed, 0 failed**, 0 ignored; 2,257 filtered out; test execution 0.02 s.
- Release build, QEMU link, and version check passed. The logs retain deprecation warnings. The earlier 211 compiler tests and GPU oracle were not rerun by this task.
- Selected compiler: `metal2vulkan v0.1.0` at `/work/orchard-m27-pages-io/reims-vgpu/vendor/metal2vulkan-io`. The sole compiler lock entry has neither `source` nor `checksum`. All **214 other packages**, all remaining lock metadata, and the compiler package's other fields are unchanged.
- The root manifest has exactly the expected vendor workspace exclusion and Git-URL-to-path patch. `selected-compiler-proof.json` and the captured admitted/selected Cargo files provide independent proof.
- Both dependency manifests match SHA256 `2d5e7d483b966177882ccfa50d3a49a9c81c853dcf57c4992712452b4475da93`. All **618** reviewed compiler files match before and after. The frozen script also verified the vendored compiler copy before and after compilation.
- All 421 admitted capture-source pins and the three admitted artifact pins below passed the frozen script's before/after checks. The build scripts and both manifests also retained their approved hashes.

## Preserved admitted artifact pins

- `/work/orchard-m27-pages-capture/artifacts/qemu-system-aarch64`: `689d926f89da98fb6886919e54d8983c80b35b0666051634623e875d5e6297de` (unchanged).
- `/work/orchard-m27-pages-capture/artifacts/libreims_vgpu.a`: `cbd1ec25328127d42e45521f5ca0f17d90b8f5ab3df27babf000ff5c9bc4e385` (unchanged).
- `/work/orchard-m27/qemu/build/qemu-system-aarch64`: `b4af10846ed7cb121cfc61ecf4bdf59e48df28232b40789c41423945f9816578` (unchanged).

## Resources and cleanup

- Cgroup memory peak: **4,294,967,296 bytes (4.00 GiB)**.
- Minimum free host space observed by the frozen guard: **11,815,194,624 bytes (11.003757 GiB)**; required floor: 10 GiB.
- Guard retained: host sample age -2 to 20 seconds, 0.2-second child checks, 1,500-second deadline, 16 MiB per-log bound. All recorded logs are within that bound.
- Pinned builder image: `sha256:14ea78615d69de5eea70014968be23464751916c6c44793f19f5771a9b4eeb17`; 4 CPUs, 4 GiB memory with equal memory-plus-swap limit, 256 PIDs, no network, read-only root, 64 MiB tmpfs, core ulimit 0. The script set and verified local core filter `0x10`.
- Owned container `macos-stage-io-build-1708fd443600` (`942e88c99326195ff71643af852338fe5f8c549cdf26d4de9a0984f26cfc8133`) is absent after script cleanup. All **89** original container IDs, names, and image references remain present. No active CONTROL or owned-build conflict remains.
- Protected exporter retains its exact approved ID, PID 657, and start timestamp. Sampler PID 77088 retains its approved start timestamp; neither was renewed or restarted.
- The only work-volume mounts were the build volume at `/work`, owned host output at `/out`, and read-only parent/compiler inputs at `/parent` and `/m2vio`. No CONTROL guest or RAW volume was mounted or read. No manual Cargo Git-cache edit or cleanup command was issued.

Exact invocation:

```powershell
& ./test-output/arm-macos/orchard-build/golden-m27-pages-io/Build.ps1
```

The expanded Docker argv is stored in `handoff.json`; inspected resource settings and mount proof are in `resource-command.json`. The only shared mutable build cache admitted by the script was `/work/orchard-m27/reims-vgpu/target`.

## Parent handoff

The QEMU profile remains **closed as `None`**, pending parent review. No VM, GPU workload, WindowServer, GUI, identity/profile migration, launcher/readiness change, source fix, service action, retry, or subsequent experiment was performed. No partial variant or cache cleanup was performed.

`build-result.json` is the untouched script-produced result. `handoff.json` includes artifact hashes and sizes, compiler/lock proof, actual test counts, resources, elapsed time, preservation checks, and cleanup verification. `preflight-verification.json`, `postflight-verification.json`, `execution.json`, captured Cargo files, and the original build logs retain the supporting evidence.

The installed codebase-memory skill was read. Its graph, coverage, and index tools were unavailable, so the named sources were inspected directly; no graph coverage is claimed.
