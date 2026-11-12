# Verified leaked allocation owner

VERIFIED: true. The one intentional default, probe-OFF `mixed-depth-off` execution reproduced one native Core validation error occurrence, VUID-vkDestroyDevice-device-05137. No other VUID or synchronization hazard occurred. Rust reported one passing test; API qualification was RED.

The actual VUID memory handle was parsed from stdout, not assumed from R3. `PARENT_MEMORY_ALLOC` on stderr line 130 identifies `0x200000000020`, 2560 bytes, site `mrt_secondary`. The exact diagnostic source maps `AllocSite::MrtSecondary` to index 1 and index 1 to `mrt_secondary`. `PARENT_REGISTRY_TERMINAL` on stderr line 155 identifies image `0x1f000000001f` with the same memory handle. This is the mixed MRT secondary, not the transient depth allocation (`0x100000000010`) or shared slab (`0x1c000000001c`).

Exact source evidence: `pools/images_and_registry.rs:1707-1760` directly allocates and binds dedicated attachment memory, then registers `ResidentMemory::Recyclable(memory)`. The diagnostic `pools/teardown.rs` registry drain destroys alternate views, the primary view and image, but contains no backing-release call. The final slab teardown owns only its tracked blocks. Dedicated attachment memory never entered that ledger. The hot deferred-handle path already uses slab-ledger release with a raw dedicated fallback.

The approved conditional fix gate is satisfied: a known allocating site, exact site/enum association, exact native image/memory terminal witness, direct dedicated ownership and missing wholesale release all agree. This proves this allocator-terminal ownership defect; it makes no claim about guest desktop causality.

Canonical receipts: `baseline-rootcause.json`, `baseline-mixed-depth-off-{stdout,stderr}.log`, `diagnostic-staged-source.json`, `diagnostic-frozen-source.json`, `diagnostic-binaries.json`, `diagnostic-validation-{before,after}.json`.
