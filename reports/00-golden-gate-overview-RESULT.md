# Golden Gate experiment status

Updated27October2026 evening. The installed image has been read successfully:
macOS27.0,build26A428. Its matching VM firmware and paired auxiliary storage are
prepared. A full-system Docker/TCG attempt is actively executing iBootStage1.
No installed-system Darwin kernel handoff or graphical desktop is verified yet.

The current30-minute diagnostic attempt uses software Vulkan and records NBD
request offsets plus guest/unimplemented-operation errors. Its previous15-minute
attempt reached the840-second handoff deadline without XNU. The new trace shows
reads advancing through disk metadata, including the main APFS container.
The two-layer RAM cache repeatedly evicts and refetches large OCI layers; an
explicit8-layer/6GiB bounded profile is being implemented and tested separately.
It will not replace the running backend before validation and parent review.

## Concrete progress

- Earlier27.0.1 restore inputs booted to an ARM64 root shell; live uname/id/ls
  passed. This remains separate from the installed Golden system.
- Fixed staged APFS support for sealed/headerless B-trees, root and child SHA
  verification, and root-relative virtual child identifiers.32focused tests
  and the real ordinary restore regression pass. Real sealed-directory and
  SystemVersion lookup now work on the Golden image.
- Added an optional preparation read-cache database capped at32MiB.10tests
  include a real APFS-over-NBD replay without fresh payload reads. The separate
  OCI backend still retains decoded layers only in RAM.
- Extracted original AVPBooter:334960bytes,SHA256
  `6d010540a047ec71a54cb96565171f8f2e0e191dd5dbef2403f3863409afa845`.
  Disassembly identifies a manifest-property validator at0x2370 by its CEPO,
  ECID,CHIP,BORD and DGST handling. The old0x2314 site is incompatible.
- Patched a separate firmware copy at0x2370, preserving the original and
  verifying the exact8-byte change. Patched SHA256:
  `593d1f9a870df0cf849c7aca2430b21a00da23b08edb7bf17498afd4a3fb222e`.
- Corrected runner validation to pin the original wrapped NVRAM, then require
  its exact16KiB-stripped AUX payload. Added bounded QMP startup handling and
  an explicit cold-I/O profile.62runner tests pass.
- Windows Docker CLI is the active launcher because Ubuntu WSL launch returned
  `Wsl/Service/CreateInstance/E_UNEXPECTED`. No WSL/Docker restart was attempted.

## Evidence and controls

Current process names/session identifiers are in `full-system/ACTIVE-STATE.json`.
The active storage sampler is identified in `host-space-sampler-process.json`.
The10GiB host reserve,20-second sample freshness, read-only pinned base,
2GiB overlay allocation cap, bounded diagnostics and owned-process cleanup
remain enforced. No full50GB RAW/checkpoint was created. Working AUX and small
qcow2 changes are preserved.

- `full-system/attempts/`: per-attempt serial,GDB,QMP,storage traces and results.
- `full-system/firmware-inspection/`: original summary, disassembly, patch proof
  and runner regression results.
- `full-system/live-preparation/run-20261027T151744Z/`: successful preparation.
- `full-system/apfs-headerless/`: reader reproduction, patch, tests and cache tests.
- `orchard-build/golden/RESULT.md`: isolated QEMU build and PCI capability proof.
- `evidence/reims-dozen-smoke.txt`: host RTX5070 renderer startup only, not a
  guest desktop. Hardware Dozen still lacks some guest-required features;
  software Vulkan is the current control.

All experiment changes remain under ignored `test-output/`. Tracked repository
files and default Docker Compose remain unchanged. The older restore report is
retained as `RESULT-restore-20261026.md`; its storage/graphics observations are
historical. Overall earlier host capacity loss remains unresolved.

Latest continuation: the30-minute diagnostic reached Microkernel iBootStage1
mBoot20457.1.29 and loaded illb/logo, then ended at its1700-second handoff deadline.
No installed XNU handoff or desktop is confirmed. The old backend is stopped.
The reviewed43-test8-layer backend is warming in a separate socket volume with
6GiB memory and two CPUs. Its internal URI remains unchanged, preserving the
existing overlay and AUX identities. A delegated bounded task will validate
readiness, prewarm only observed read offsets, and run the next guarded attempt.

Latest verified checkpoint: eight-layer cached boot reached iBootStage2, then panicked. Read-only debugger captured ESR 0x92000050, ELR 0x700b0200, FAR 0x4ffff8; actual page-table walk confirms missing physical scratch RAM. Isolated 16 KiB RAM variant is being built. See full-system/iboot-diagnosis/REPORT.md. XNU and GUI remain unverified.

Scratch-RAM experiment verified: QEMU673cfd8b passed the prior abort and printed the full Stage2 banner. The 250s diagnostic ended while fetching new boot data; layers1 and46 are now verified in RAM. All75 focused offline tests pass. A longer guarded read-only diagnostic is the next continuation. No XNU or graphical desktop is confirmed.

28 October: Stage2 read30240040 identified as AVP RTC by actual strings and Golden DT evidence. Isolated logged4KiB register-storage model25fa22ad passed paused RTC/storage/bounds/reset/PL031/scratch/PCI checks. It is not a complete clock model. QEMU-only identity migration preserved AUX/overlay and new-profile preflight passed. Guard sampler renewed (PID104360) with unchanged10GiB floor/freshness; next read-only boot continues.

CTRR absence-probe variant dba936f7 passed paused checks for the documented64KiB region and all earlier device contracts. It advertises no controller magic/protection. QEMU-only identity migration preserved AUX/overlay; preflight passed. Next guarded read-only boot is delegated. XNU and GUI remain unverified.

Golden transfer qualified atE0A00000 withcompleteBootArgs_r3/v2. Actual196-byte rootCLI preserved; NoSEPnode fits11220zeroADTpadding; planned43bytes changed. Finaladapter34offline tests and70runner tests pass. Onlytwohelperidentitypins migrated, AUX/overlay unchanged; newpreflightpassed. First actual preserving handoff boot delegated. Kernel/userspace/GUI still require liveproof.

Darwin27kernel andRecoverymount areliveverified. OriginalworkingAUXbootedRecoverybeforeouradapter. IsolatedpristineAUXcontrolcapturednormal selection withSystemauthdata,emptyCLI,anddifferentbootUUID. Mainpairpreserved. NextfullbootusesisolatedfreshAUXandlosslessboundedcompressedReimslogs; kernel/userspace/Systemroot/GUI areseparatecheckpoints.

Normal-System boot reachedDarwin27 butrequestedRecovery with decodedmissing-boot-media. Rootselector matchesSystem/Data metadata; no seal-broken evidence. PublicXNUrelease rootwait60s versusactualcoldlayer89s makeslatencytestable. Qualifiedwdt=-1 boot-optionprofile allowswaitingwithoutforcingrootmatching;allhostboundsremain. Nextcontrolledbootdelegated, Systemroot/userspace/GUIstillunverified.
