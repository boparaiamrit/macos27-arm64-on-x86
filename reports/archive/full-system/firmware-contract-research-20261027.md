# Golden AVPBooter contract investigation

Read-only delegated primary-source research, 27 October 2026. No verified patch
offset, original bytes, or handoff PC was found for Golden 27.0 build 26A428's
`AVPBooter.vmapple2.bin`. Inspect the actual extracted binary and runtime
arguments before mutation. No firmware or helper changes follow from this note.

The existing `kernel-handoff.gdb` is experimental. Its `0xACA00000` address,
first-hit skip and `x1` revision/version 2/2 check come from a macOS 13-era
27on86 path; they have not established a Golden handoff.

- [27on86 injector at 509a4ce](https://github.com/steelbrain/experiment-macOS-arm64-on-linux-x86/blob/509a4ce52bc703dfc79eb8b4283f51acd88b8594/scripts/27on86/inject-xnu-boot-args.gdb#L8)
- [Roadmap scope](https://github.com/steelbrain/experiment-macOS-arm64-on-linux-x86/blob/509a4ce52bc703dfc79eb8b4283f51acd88b8594/docs/roadmap.md#L24)

Steelbrain's HVF path recognizes a kernel entry using an `x0` boot-argument
pointer and an instruction-fetch address within `[physBase, topOfKernelData)`.
It uses device-tree pointer/length offsets `0x60`/`0x68` and the translation
`DT_PA = DT_VA - virtBase + physBase`. Its callback uses HVF APIs, so these
inspection contracts do not supply a TCG callback or a trampoline address.

- [VMApple implementation at 4895365](https://github.com/steelbrain/qemu-reims-vgpu/blob/4895365e5bf9d344e494a39eceacb475079fedb5/hw/vmapple/vmapple.c#L533)
- [Measured 27.0.1/26A434 on M3 Max/HVF](https://github.com/steelbrain/reims-vgpu/blob/12adb1fb46953ae55d4a7b2d66d9110bb19b0b1a/docs/qemu.md#L2240)

Two candidate binary locators have different scopes and must not be treated as
patch authorization or proof of equivalence to Orchard's callback:

- [vphone DGST locator](https://github.com/Lakr233/vphone-cli/blob/f92d82cd754d05d9eae43a2d4766b6cac476a2d1/sources/FirmwarePatcher/AVPBooter/AVPBooterPatcher.swift#L77)
  matches immediate-loading instructions for `0x4447`, then bounded forward
  return/backward result-setter searches. Its motivating Golden beta report
  concerns `AVPBooter.vresearch1.bin`, not `vmapple2`.
  [Report](https://github.com/Lakr233/vphone-cli/issues/373).
- [vz-kext-loader VBO locator](https://github.com/openzfsonosx/vz-kext-loader/blob/ff9795fe27ba65408e6eb2ee4b878edb9595452a/engine/vzkl/avpbooter.py#L13)
  requires a unique `e50304aa04008052` anchor and resolves aligned relative BL
  callers. Its read-only `info()` path is an inspection lead; zero callers
  alone do not establish an already-patched untouched binary. The Golden clone
  report does not pin this guest's exact AVPBooter build.

No checked source established a new Golden VMApple boot-argument layout.
[Apple xnu-12377.121.6 boot.h](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/arm64/boot.h#L18)
has the familiar prefix but a 1024-byte command line. This earlier source does
not establish a 26A428 ABI, and the helper's 608-byte write is not a universal
capacity declaration.

Next inspection: record extracted size/hash/build banner; disassemble candidate
functions and callers; establish the actual final-stage transfer and register
contract; validate the bounded ADT and padding before any write. A matching
function prologue or hit ordinal alone is insufficient evidence.
