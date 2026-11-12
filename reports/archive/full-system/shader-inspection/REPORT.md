Offline SPIR-V interface census is ready and frozen for parent use.

All 15 tests pass in pinned runtime image13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635, with zero skips. Actual spirv-as/spirv-val/spirv-dis integration validates synthetic half-vector Output, half arithmetic converted to float32 Output, private half and storage-buffer half controls. Additional tests cover nested matrix/array/struct graphs, malformed/missing/cyclic types, symlink/count/size refusal, deadline/output enforcement, non-overwriting reports and exact-directory CLI use. No shaders or GPU/VM code were executed.

The helper records complete module SHA-256, separate Vulkan1.2 validation status, raw-ID entry points/capabilities, every Input/Output variable, reachable type nodes, numeric widths, array-length constants and relevant decorations. It walks only stage-variable type graphs: unrelated half arithmetic/private/SSBO types do not imply half stage I/O. Missing, cyclic, unfamiliar or budget-limited graph information cannot silently become 'no16bitIO'. Both actual16bitstage variables and a declared StorageInputOutput16 capability are evidence of that feature requirement, even when an otherwise unused capability is present. Host support must be passed explicitly; unknown host support remains unknown when required.

Resource limits: 256KiB/module,32modules,128directory entries; twoMiB combined tool output per invocation, shared10-second tool deadline per module, twoMiB final JSON. Reachable types, interface variables and graph depth are bounded. Tools use argument arrays and private bounded snapshots, never shader-built shell commands. Input files use O_NOFOLLOW and fstat/exact-read/change checks. Output creation is exclusive and cannot overwrite an earlier report. Traversal names and symlinks are refused. Empty captures are incomplete, not evidence of absence.

A fresh Windows sample is checked before external commands and while their pipes are read:10GiBfloor,20-second maximum age,2-second maximum future timestamp. The final command minimum was12,484,472,832free bytes. Core filter0x10 is set/readback before tools. Tests used1CPU,256MiB/equal swap,64PIDs, no network, read-only root,32MiB tmpfs; only this owned evidence directory was writable. No guest/work volume was mounted and no production files changed.

Usage inside the existing runtime image:

    python3 -B /parent/full-system/shader-inspection/census.py /parent/full-system/attempts/EXACT/shader-capture --output /parent/full-system/attempts/EXACT/shader-io-census.json --host-storage-input-output16 0 --host-space-sample /parent/full-system/host-space-live.json

Use an exact attempt path. The source can instead be an explicit regular .spv file. The output parent must exist, and the output must not already exist. A nonzero exit or incomplete report requires investigation; do not treat it as absence of half interfaces. Per-module validation and analysis may independently fail. This is observation only, with no legalization, capability changes, shader execution or claim about the actual guest crash.

Exact final hashes and limits are in handoff.json; final-test-result.json/final-tests.log retain fresh verification. Earlier test-result.json/tests.log record the first12-test pass before extra API/declared-capability boundary coverage was added.
