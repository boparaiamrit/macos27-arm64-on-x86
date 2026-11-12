This is a frozen source-only extension of the qualified RGB10 buffer-texture
plan to native RGBA16Unorm. Start with [REPORT.md](REPORT.md), then review
[owner.patch](owner.patch) and [source-sha256.json](source-sha256.json).

RED was recorded before changing the helper: the actual RGBA16 plan test
failed because the old selector returned `None`. GREEN compiled the real
changed helper and all 16 tests passed. Exact data/types/source hashes,
commands, logs and fresh disk-guard samples are preserved in the phase receipts.
No real guest inputs, GPU execution or new emulator were used.

Only `source/buffer_texture.rs` and `source/buffer_texture_tests.rs` differ
from the qualified baseline. `mod.rs`, `vulkan.rs` and the actual runtime/debt
test file remain byte-identical. Apply the two-file patch to a copy of the
admitted RGB baseline, preserving its existing injection seam.

`run_helper_tests.py green` rechecks the current helper without Cargo or GPU.
The historical RED command is recorded with its then-current source hashes;
it expects the pre-change helper and should not be rerun against GREEN source.
`verify_freeze.py` checks formatting, baseline immutability, scope and hashes.
Both scripts write only under this new owned directory.

Full runtime/debt/GPU and guest checks remain future parent work. RGBA16 GPU
adjacency requires tolerance below `7.629510948348211e-6`; use `1e-6` with
finite, ordering and gap checks. The existing RGB10 `2e-5` tolerance is invalid.
