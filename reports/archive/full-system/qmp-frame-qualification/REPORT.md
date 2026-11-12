# Direct QMP PNG offline qualification

Qualified for later parent review: a single direct QMP PNG capture works on the
actual Apple/Reims console with the requested pinned QEMU. A separate running
AArch64 synthetic machine verifies retained running status, counter progress and
no observed STOP/SHUTDOWN during capture. The standalone helper and its failure
receipts are qualified offline. Production integration is not performed or
admitted here.

Completed UTC: 2026-10-28T04:52:42.912292+00:00.
Final qualification run: `runs/macos-frame-qual-qualify-3bba1c1c7115`. Final source probe: `runs/macos-frame-qual-probe-5fe25c2e6c7c`.
Only the newly created `qmp-frame-qualification` directory was written. No real
guest files, VM processes, sockets, screenshots, proxy/NBD endpoints or ports were
opened or inspected. The concurrent parent boot was not examined. No delegate,
install, download, build, new image, service or host setting change was used.

## Exact pins and source evidence

QEMU: `/work/orchard-golden-crypto/qemu/build/qemu-system-aarch64`.
SHA256: `b4c7d59055e30c931ecade17ecf08f806baba7814a1477513d85d57872e3e6f0`.
Existing runtime image:
`sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`.
Orchard Git HEAD: `c73a2bda1fd4afefd61204bb74afd74292ef2fe9`.
HEAD alone is not a clean-tree or build provenance claim; exact inspected source
content hashes and runtime library hashes are in `runs/macos-frame-qual-probe-5fe25c2e6c7c/probe-result.json`.

Exact read-only source fallback paths:
`/work/orchard-golden-crypto/qemu/hw/display/reims-vgpu-mmio.c:704-775,1323`,
`/work/orchard-golden-crypto/qemu/ui/ui-qmp-cmds.c:324-390`, and
`/work/orchard-golden-crypto/qemu/ui/console.c:168-177`.
Line-numbered excerpts and per-file SHA256 are retained in the probe output.
The codebase-memory skill was read; no graph tools were available. The supplied
Rust scanout fact was accepted from the task; two guessed source locations were
absent and are recorded as such, not presented as verified Rust evidence.
`warm-cache-boot/NEXT-GRAPHICS-CHECK.md` was read as required.

## Observed synthetic results

Apple/Reims: `apple-vm,uuid=1`, graphics enabled by default, display none, -S,
TCG single thread, one vCPU and 1 GiB virtual RAM. Inputs were a four-byte local
WFI fixture and two 16 KiB zero dummy disks, all pinned before/after unchanged.
The CPU remained prelaunch/paused; no Apple code executed. Own `info qtree`
confirmed `reims-vgpu-mmio` and excluded the dummy graphics device.

The exact request was `screendump` with arguments `filename` pointing into the
existing owned attempt directory and `format: png`, plus its unique request id.
The matching positive `return: {}` is retained in the receipt and QMP transcript.
The PNG is 1920x1080, 6121 bytes, SHA256
`c1161e09bb43363d2777bdb410b3e59e98b33eae3b374322b5e86079ab089a12`.
Capture/validation took 0.059953 seconds in this sample.
Signature, IHDR/dimensions, chunk bounds/CRCs, IDAT deflate size and final IEND
passed. Its RGB pixels are all black (`pixel-verification.json`). This proves
the initial console API surface only, with no guest rendering or desktop proof.

Running proof: generic `virt`, cortex-a72, TCG, one vCPU/1 GiB, ramfb. The only
executed code was the 24-byte AArch64 loop documented in `qualify.py`. Loader PC
was 0x40200000 and the RAM counter was 0x40201000; the generated DTB remained at
0x40000000. HMP **reads** bracketed capture. Counter before:
`40201000: 0x0000000007d40e48`; after: `40201000: 0x000000000c100a0a`;
delta 71,039,938. QMP status was running before and after, and no
STOP/SHUTDOWN event was observed from screendump through the follow-up reads.
The helper sent no stop/pause/step/reset or guest-input/state-write command.
Harness `cont` ran only this synthetic loop before the observed capture window.

The running PNG is 640x480, 1569 bytes, SHA256
`39684f2364d14965a755c9b1034ae6aa1386d96a5f09625a3eed232881df1fba`; capture/validation took
0.033784 seconds. This second console is ramfb,
so running Apple/Reims capture is not separately claimed. Counter bracketing
does not prove continuous execution at every instant or zero BQL delay.

## Tests, guards, budgets, cleanup

13 unittest methods passed, including looped fault matrices:
positive capture; missing/partial/CRC/malformed/oversized PNG, IEND/trailing/deflate
errors; mismatched id; response timeout, partial-send error and simulated late
file write/reply; STOP/SHUTDOWN; symlink ancestors/destination, file/directory
replacement, traversal and preexisting attempt; guard failure before/during;
bounded QMP reply and invalid deadlines; valid seeded/atomic JSON receipts and
preservation/no retry/no helper cleanup. Oversize uses a lower configured 1024
byte fixture ceiling to avoid creating an actual >8 MiB output. Detailed results
are in `fake-tests.log` and `fake-tests-result.json` in the selected run.

Every owned container used read-only root, network none, cap-drop ALL, no-new-
privileges, <=2 CPUs, 1 GiB memory/equal total swap (zero swap allowance), pids
128, and a 64 MiB noexec/nosuid/nodev tmpfs. Build volume, software runtime and
guard directory were read-only mounts. The guard mount's only read was
`host-space-live.json`. Test processes had an 8 MiB per-file RLIMIT_FSIZE.
Final qualification peak cgroup memory: 82,845,696 bytes;
zero OOM events. All argv/resource evidence is retained.

The final run checked the host guard 28 times; minimum sampled
C: free bytes 29,477,855,232, independently measured minimum
29,477,711,872, maximum poll gap
0.108841 seconds. Every recorded run's maximum gap
was <=0.2 seconds; sample age <=20 seconds and future tolerance <=2 seconds were
enforced, with bounded <=0.04-second sharing retries. All guard JSONL is retained.
Across all runs the minimum sampled free bytes was
29,135,654,912 and actual minimum was
29,135,278,080.

Windows owned-file allocation before final documents was 363,710 bytes;
the conservative file/entry/final-document allowance is 8,080,574 bytes,
below 64 MiB. See `storage-verification.json`. Maximum actual captured PNG is
6121 bytes. Polling/postchecks are not a physical filesystem quota and cannot
prevent all write overshoot or late writes; see README for future admission.

All 8 exact uniquely owned containers were removed and independently
confirmed absent; final QEMU processes exited and were reaped. No other container
or process was enumerated or signalled. See `cleanup-verification.json`.

## Preserved setup failures and material limits

The initial fake-test run was stopped when Windows accounting followed a Linux
test symlink (WinError 1920); accounting was corrected to lstat regular files
only. A later fake-test run exposed an empty-name test-harness substitution and
uncaught raw zlib exception; both were corrected before the final tests. Initial
VM realization rejected read-only dummy pflash and a loader/DTB overlap. Only
synthetic dummy-node access and synthetic addresses were corrected. Every failed
run and receipt is retained, with new unique destinations used for later runs.
An earlier corrected run also passed; the final 13-test run pins the final
helper including atomic receipt publication.

No real cold block I/O, main-loop/BQL tail latency, NBD delay, Apple/Reims running
render/update path, WindowServer, compositor frame, Finder/Dock interaction or
macOS desktop is proved. The PNG validator cannot establish frame freshness or
remove the source's potential concurrent-surface-update caveat. Timeouts do not
cancel QMP and can leave late replies/writes. Parent must handle exclusive lease
ownership, quarantine/reconciliation, deadlines, trusted paths and physical
budgets before any later integration. `README.md` is the bounded contract.

## Reproduction and frozen artifact pins

Run the two explicit offline commands in README with the existing sampler and
pinned inputs. Exact Docker/QEMU argument arrays, socket paths (Unix, private to
each container), environment, fixtures, transcripts and receipts are retained.
`artifact-manifest.json` SHA256-pins all regular artifact files except itself and
`handoff.json`; symlinks are listed without following them. `handoff.json` pins
the manifest. These are content-frozen review artifacts; no read-only attribute
or host setting was changed. No runner integration or real-VM admission occurs.
