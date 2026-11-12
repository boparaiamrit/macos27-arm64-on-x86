# Keyboard Setup Assistant metadata

The immutable Apple bundle authors a **Quit Keyboard Setup Assistant** menu item with key equivalent **q**, modifier mask **1048576 / 0x100000**, and a control connection labeled **terminate:**. `LSUIElement=true` therefore does not establish that this assistant requires its on-screen Quit button or lacks an authored quit shortcut. These offline bytes do not establish whether the menu was installed or enabled at runtime, which application received the earlier QMP input, or why that input caused no visible change.

`Info.plist` explicitly contains `LSUIElement=true`, `NSMainNibFile="MainMenu"`, `NSPrincipalClass="NSApplication"`, and `CFBundleIdentifier="com.apple.KeyboardSetupAssistant"`. `LSBackgroundOnly` and `NSMainStoryboardFile` are absent. The source is `/p2/v1/System/Library/CoreServices/KeyboardSetupAssistant.app/Contents` on the immutable System volume, read through the existing read-only `/stream/golden-live5.nbd` export.

## Exact Apple archive evidence

The named resource is `Resources/Base.lproj/MainMenu.nib`. It is a 4046-byte `NIBArchive` v1, coder version 10. A small local decoder consumed its object, key, value, and class tables to their exact declared boundaries: 116 objects, 52 keys, 370 values, 17 classes. The complete decoded records, original byte offsets, and reference indices are in `main-nib-decoded.json`; `decode-local.py` retains the parser. This is an offline decode, not Apple `ibtool` or an AppKit runtime test.

| Relationship | Authored archive record |
| --- | --- |
| Menu item | Object 13, `NSMenuItem`, object-table byte offset 89 |
| Title | Object 13 `NSTitle` -> object 14, `NSLocalizableString` with `NS.bytes="Quit Keyboard Setup Assistant"`; title value record offset 1566 |
| Key | Object 13 `NSKeyEquiv` -> object 17, `NSString` with `NS.bytes="q"` (hex `71`); reference record offset 1534, string value record offset 1661 |
| Modifiers | Object 13 `NSKeyEquivModMask=1048576` (`0x100000`); int32 value record offset 1540 |
| Action connection | Object 12, `NSNibControlConnector`, `NSSource` -> object 13, `NSLabel` -> object 27; value record offsets 1506 and 1512 |
| Action label | Object 27, `NSString`, `NS.bytes="terminate:"`; value record offset 1795 |
| Menu membership | Object 73 items array includes object 13; object 70 `NSMenuItems` -> 73 and `NSName` -> object 86 (`_NSAppleMenu`) |
| Main-menu relationship | Object 60 `NSName` -> object 87 (`_NSMainMenu`); its items array 64 includes object 65, whose `NSSubmenu` -> menu 70 |

The connector does not encode a destination field. No runtime responder-chain target or implementation behavior is inferred. `NSHiddenInRepresentation=true` is also encoded on the menu item; this report does not treat that archive property as proof of runtime visibility or shortcut availability.

## Retained exact files

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `Info.plist` | 1588 | `aa1010c8337b58c2da2a480f867682b54ad9422cf8304705cecd7a3ec1ac0362` |
| `main-nib-0.nib` | 4046 | `346b7ae9de2d3697b9c6ce54355d63db3c06f398fa641a7e24bfefca77c55661` |

Both files were read using the existing `fs_explorer.open_source(..., backend='pure', threads=1, system_files=True)` reader and `read_file(..., verify=True)`. Filesystem metadata was read as needed to resolve these targets and the specifically named nib; no executable, Assets.car, other nib, or localization content was copied. The sealed APFS reader performed its existing hash verification; this report makes no new complete-disk verification claim.

## Bounds and preservation

One helper container used image `sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635`, network none, read-only root, 2 CPUs, 512 MiB RAM/equal memory-swap, pids 128, cap-drop ALL, no-new-privileges, 64 MiB noexec/nosuid/nodev `/tmp`, and coredump filter `0x10`. It mounted only the state/socket volume at `/stream` read-only, ARM source at `/parent` read-only, and this newly owned output directory at `/out` writable. It never mounted the working CONTROL, build, or RAW volume. The helper is absent after its successful `--rm` exit.

Actual NBD reads totaled **3,355,648 bytes in 38 calls**, maximum request **966,656 bytes**, in **2.531778 seconds** of helper runtime. The fixed caps were 32 MiB actual bytes, 256 calls, 1 MiB/request, and 60 seconds. `probe-result.json` records every offset, requested length, and returned length. A fresh C: sample was checked before launch and every NBD read; observed minimum free space was **15,731,232,768 bytes**, sample ages **0.473175–1.034302 seconds**, above the 10 GiB floor and inside [-2,20] seconds. Local parsing only reused the retained 4046-byte NIB; it did not reconnect to NBD.

The exporter remained running at PID 679 with unchanged start time `2026-10-28T21:58:44.477275548Z`. Existing exporter and host-space sampler were not stopped, restarted, replaced, or modified. No VM, guest command, GPU operation, guest input, APFS mount/repair, service change, source edit, pagefile change, payload download, or cleanup was performed. All new files are confined to this ignored output directory. No credentials, ECID, or private boot arguments were read into the report.

The original export-ready provenance records manifest pin `sha256:b78a521145ebef24e9916c0b3999e165bb12b587d11524c5fa3ba4fe7bf79bb9`, plan digest `sha256:700a601da177786c796ff441c0c8f1d4edd0a4970557f7f81fa0ebb1092153a3`, 50,000,000,000 logical bytes, and the converter's prior verification of all 67 layers. Those are provenance from the existing export-ready record, not verification repeated by this metadata probe.

This result supplies primary Apple bundle evidence for choosing a separately approved next action. It does not authorize or perform another input attempt.
