# R9 boot test: stopped at VM-exclusion guard

**Terminal result: PREBOOT_GUARD_FAILED_OTHER_VM_RUNNING. No migration, CheckOnly, or actual guest boot was executed. No boot attempt directory was created.**

The requested unconditional exclusion of any other VM failed on existing host PID **79064**, `qemu-system-x86_64.exe`, at `C:/Users/bopar/AppData/Local/Android/Sdk/emulator/qemu/windows-x86_64/qemu-system-x86_64.exe`, creation time 2026-10-28T08:15:59.065206Z. This is the existing Android emulator identified by earlier preservation reports. It was neither stopped nor changed. The user required a guard failure to be terminal; no exception was inferred for Android, and no retry was made.

## Work completed before the terminal guard

Read the specified RGBA16 profile/migration, fresh-guest README/admission/report, mouse launcher/wrapper, exact prior live CheckOnly command, both RGBA16 synthetic test sources, and R9 REPORT/handoff. No test_m27_pages_rgba16 file exists; the matching tests are rgba16-live/test_rgba16_profile.py and test_rgba16_migration.py.

Created local-raw/golden_m27_pages_fence_profile.py and migrate-m27-pages-fence-identity.py, modelled on the RGBA16 sources. Admission accepts only the previous RGBA16 emulator SHA and changes only qemu_sha256; migration retains exact-byte backup, AUX/overlay hashes, locking, guards, atomic replace and readback. The production migration was **not invoked**.

Created test_fence_profile.py and test_fence_migration.py here. All **13 Linux synthetic tests passed**, including actual directory fsync, old identity/artifact refusal, concurrent mutation refusal, exact backup, state preservation and dispatch. No build occurred.

The only existing source edits are the additional ValidateSet key in mouse-guest/Launch-Rgba16MouseAttempt.ps1 and the additional dispatch branch in local-raw/run-crypto-frames-attempt.py. Exact before/after SHA256 values are in [existing-file-hashes.json](existing-file-hashes.json); exact original bytes are retained alongside this report. Both after hashes were rechecked. No controller, guard, resource, source-renderer or prior evidence edits were made. New source hashes are in [new-source-hashes.json](new-source-hashes.json).

## Verified admission and preservation

Host and native artifacts both match the requested pins: qemu-system-aarch64 **70,858,344 bytes**, SHA256 `14f12ffe37304d011c00c490539dd949138c552bac3788fb4d8c3dd7a7301b6b`; libreims_vgpu.a **174,997,218 bytes**, SHA256 `a0eac4d65171168b078f631ce41b69eeda0430dc8607f680dc725ae1d2ae5572`. Native paths remain under /work/orchard-m27-pages-mrt-order/artifacts. Host rehash evidence: [host-artifact-hashes.json](host-artifact-hashes.json).

Guest is volume `macos-golden-pristine-guest`, isolated `fresh-01/boot`. Before and final read-only hashes are identical:

| File | SHA256 before = after |
|---|---|
| aux.work.img | af5fd8b3bc11d5a5f8fc7db1ea9e3342891b1c3af3f5d31300481e7e5a10587b |
| root.overlay.qcow2 | 94934224acecba747335f03f3468767fa869cd230b0ea28cdae3e482e1146ca6 |
| runner-identity.json | 1a69aaaf1876996d68f7a2298c56bb02c1047b9ae4af2eb8c8e0418858040dae |

Identity qemu_sha256 remains `553102765a9da19efee87112f85190835d7d0bc3ca0e55539c375f948e302bfe`. **No identity field changed.** AUX size 33,562,780 and overlay size 703,528,960 are unchanged.

Readiness stream-ready-local-raw-cleanup4-live5.json SHA256 remains `989bea15cf0a5a56fe2c35cae4a59b29d00a9aeeff3c193d75fc7726dd73c731`. Exporter b8472de170f6ab1709e76bef8ca08f48df591ee4ea893f607eae2fddb21ce372 remains running, PID679, same start 2026-10-28T21:58:44.477275548Z. Sampler **84568** remains alive with the same start time. Final sampler record: free **40,794,710,016 bytes**, age about 2.06 seconds at inspection, above the unconditional 10 GiB floor. No other running guest container or holder of the guest volume was found; the host Android VM alone failed the exclusion guard.

Only owned short synthetic/read-only inspection containers were run and removed through --rm. No other container/process was touched. No Docker/exporter/sampler restart, guest input, second debugger or QMP client was used.

## Frames and guest checkpoints

No R9 frames, serial.log, Reims log, draws_ok/draws_fail counts, kernel/System/Data/early-boot or WindowServer/loginwindow observations exist because no R9 boot started. Consequently no R9 image was viewed and no visual improvement or regression can be assessed. The historical RGBA16 description is context from the supplied/prior report, not a newly viewed frame or an R9 observation. No desktop, login or interaction is claimed.

Evidence: [pre-state.json](pre-state.json), [post-state.json](post-state.json), [conflicting-vm-processes.json](conflicting-vm-processes.json), [synthetic-tests.txt](synthetic-tests.txt), [commands](COMMANDS.md), [run-once.ps1](run-once.ps1), [transcript](commands-transcript.txt). The script contains the exact migration and two intended launcher commands; execution stopped at line15, before all three. It must not be interpreted as evidence those later commands ran.

Codebase-memory skill read; graph tools unavailable, exact named-source fallback used. No delegation, retry, build, staging or commit.
