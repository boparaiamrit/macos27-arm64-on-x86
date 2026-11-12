# Stage2 AVP RTC probe

The scratch-RAM fix cleared the original write abort. The next cached boot
(`20261027T181146Z-yt5vh29l`) stopped in 17.458 seconds at another validated
Stage2 exception. A focused follow-up (`20261027T181925Z-fk929ubr`) captured
the referenced static strings without guest memory/register writes.

- ESR_EL1 `0x92000010`: lower-EL read data abort, synchronous external abort.
- ELR_EL1 `0x70087788`: `ldr w8,[x8]`.
- FAR_EL1 and saved x8: `0x30240040`.
- Actual table descriptors at `0x70000000` and `0x700040c0` are
  `0x8000000070004003` and `0x00e0000030000469`; they map this VA to the same PA.

The following code compares the value with `0xf001`. Equal selects the string
at `0x70122f67`, **pl031-rtc**; otherwise it selects `0x70122f71`, **avp-rtc**.
Both strings are present in the bounded `iboot-strings.bin` capture.
The meaning of the selector beyond that branch remains unverified.

This is an AVP RTC region. Golden 26A428 device-tree analysis independently
lists `avp-rtc` at physical `0x30240000`, length 4096, matched by
`AppleVirtualPlatformRTC`. AES has different addresses. Existing Orchard
provides one AES instance with two windows, and neither window defines offset
`0x40`; adding another AES instance would merely return an unknown-register zero.

The isolated next experiment ports only the logged AVP RTC register store from
qemu-vphone commit `4671e2ba6a39e5998446d35ac93dd746f5ef6f47`. That source explicitly
states that its register layout is unknown and reports only iBoot probing
offset `0x40`. Initial zero is not fabricated `0xf001` identity or a successful
clock operation. Reads/writes are logged; ordinary PL031 RTC remains unchanged.
Bounds, access widths, alignment and reset are checked in paused synthetic tests
before any guest launch. Complete RTC functionality remains unimplemented.

Primary sources:

- [Golden device tree](https://github.com/rungruch/Snapintosh/blob/1977c38b84b6ed5daeda2ea608f7efbe86fc36fe/docs/GAOKUN3-PHASE0B.md#L357)
- [Logged AVP RTC register implementation](https://github.com/tqmane/qemu-vphone/commit/4671e2ba6a39e5998446d35ac93dd746f5ef6f47)

No XNU, mounted installed root, launchd or graphical desktop has been verified.
