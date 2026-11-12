# Memoryless observation boot — 2026-10-28

Attempt `20261028T134856Z-a5vbno6z` (container
`macos-golden-full-20261028T134853`), profile `m27-pages-obs`, QEMU
SHA-256 `a8dceaccc28d12d3c71a4244150ff59e291566908cd14702de3c99d7416f8e99`.
Same bounded parameters as the m27-pages boot: 900s timeout, 800s hook
timeout, 8 guest CPUs, 1024 MB TB, 12 container CPUs, 12 GB, 1 Lavapipe
thread, readiness `stream-ready-local-raw-cleanup-live5.json`.

## Outcome

- `status=timeout`, `exit_code=124`, elapsed 890.436s. Guest was still
  running at the bound (`last_qmp_status=running`, QEMU exit 0).
- Handoff verified. Reims capture closed losslessly: 6,811,611 raw bytes,
  0 unretained.
- The observation fired exactly as designed: **8 complete shapes**, then
  the single `reason=cap_reached cap=8` line. No truncated or failed
  shape. Every descriptor is 44 bytes (`descriptor_limit=256`).
- Frame outcome unchanged by design (observation does not alter the
  refusal): retained 1920x1080 frame SHA-256
  `c1161e09bb43363d2777bdb410b3e59e98b33eae3b374322b5e86079ab089a12`,
  visually black; the two later captures are exact duplicates.
  `full_gui_verified=false`.

## Captured descriptor contract (observed)

All 8 shapes share: `object_type=9`, `identity=current_list_entry`,
`task_list=Some((337430, 1, 49152))`, `page_shift=14`, `level=0`,
`slice=0`, `depth_plane=0`, `resolve_texture_ref=0`, `load_action=0`,
`store_action=0`, clear colour all zero. They differ only in the
texture reference and one payload dword.

As little-endian u32s the 44-byte payload is:

```
0x00000001 0x0000002c <texture_ref> 0x00730542 0x00000780
<0x3c or 0x438> 0x00000001 0x00010001 0x00300001 0x00000000 0x00000000
```

`0x780`=1920 together with `0x438`=1080 / `0x3c`=60 is consistent with
width/height fields for a full-screen (and one 1920x60) pass-local
target; treat that as a strong field hypothesis to confirm against the
previously recovered guest creation serializer, not as proven layout.

Load/store actions of 0 with no resolve texture mean the observed
attachments never read prior contents and never resolve out — the
classic transient tile-memory pattern. A faithful implementation can
back them with a pass-local transient image whose contents are
discarded at pass end, without allocating guest-visible pages.

## Next gate

Implement type-9 memoryless attachment support in Reims from this
contract (decode + transient backing + load/store semantics), with
owner tests first. Keep the typed refusal for shapes outside the
observed contract. Then rebuild under a new profile, migrate the
identity pin, CheckOnly, and run one bounded boot; success is a
visually non-black frame plus type-9 refusals dropping to zero.

Current CONTROL identity pin is now the observation build
(`a8dceacc…`). Use `-QemuProfile m27-pages-obs` until the
implementation build replaces it.
