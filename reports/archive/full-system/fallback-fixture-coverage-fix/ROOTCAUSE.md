# Test fixture coverage correction

R6's first primary fallback test failed before rendering with
`TargetGuestSeedCoverage { covered: 4096, declared: 1600 }`. The fixture used
`GuestRun::whole` over its padded native allocation while declaring only the
20 x 20 x 4 pixel window. This was a parent-admitted fixture error. Its native
failure and incomplete warmup-only evidence remain preserved in R6.

The correction uses `GuestRun::in_mapping(base, allocation_size, 0, PIXEL_BYTES)`.
The checked run covers exactly 1600 bytes within the same aligned 4096-byte
allocation. Allocation size, alignment, retained import, GuestRef window,
row pitch, declared length, expected pixels and guard regions stay unchanged.
The native buffer can still import the complete aligned parent.

The constructor is the existing memory owner's bounded-window API; its exact
source matches SHA256 c468c5589540a6d3bd8615c9fe1060a99935eac1c387adc783eccd12647817ac.
The current seed validator requires the sum of run lengths to equal total_len.
No production validator, renderer, guard, limit or expected pixel is changed.

The corrected test must freshly compile and pass the same actual fallback
cases, native ownership/explicit teardown checks, and remaining renderer gates.
This source correction alone establishes no native pixel, desktop or interaction
success. No repeat of the old invalid native fixture is required.
