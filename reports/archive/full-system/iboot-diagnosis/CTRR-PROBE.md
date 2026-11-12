# Unavailable CTRR probe

The AVP RTC diagnostic model cleared its observed offset-0x40 read. The next
actual guest attempt, `20261027T183601Z-xqka79lw`, stopped after 37.882 seconds
at a lower-EL read external abort: ESR `0x92000010`, ELR `0x700863f4`,
FAR `0x30260000`, instruction `ldr w8,[x8]`. The captured page tables map
that virtual address to the same physical address.

The enclosing firmware routine begins at `0x700862dc`. It compares the probe
with magic `0x63747272`; a mismatch branches from `0x70086404` to `0x7008680c`.
That path skips all advertised-controller version, bank and range checks,
calls shared platform handling with argument zero, and returns normally through
`0x70086888`. Its sole direct caller in the captured MiB ignores that return.
Shared platform-state checks can still assert independently, so the static
absence path does not prove a successful boot.

The primary qemu-vphone platform maps precisely physical
`0x30260000–0x3026ffff` with QEMU's generic unimplemented-device helper.
That helper logs and returns zero on reads and logs/discards writes. It does
not advertise the controller magic, version, banks, protected ranges, locking
or enforcement. The new isolated emulator tests the same unavailable-controller
probe semantics; it does not claim to implement CTRR.

- [Primary platform map](https://github.com/tqmane/qemu-vphone/blob/3ed85774c2989addec3056a866991762b60c4b5c/hw/vmapple/vresearch101.c#L151)
- [Primary placeholder setup](https://github.com/tqmane/qemu-vphone/blob/3ed85774c2989addec3056a866991762b60c4b5c/hw/vmapple/vresearch101.c#L376)
- [QEMU model semantics](https://github.com/tqmane/qemu-vphone/blob/3ed85774c2989addec3056a866991762b60c4b5c/hw/misc/unimp.c#L21)

Earlier emulator builds, working guest AUX/overlay, original firmware and
storage guards are preserved. A new binary requires paused validation, a
reviewed digest, explicit one-field identity migration, and preflight before
the next actual guest attempt. XNU and GUI remain unverified.
