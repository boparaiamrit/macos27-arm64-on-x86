# Isolated pristine-AUX selection control

The original working pair is preserved in `macos-golden-full-guest`. A separate
`macos-golden-pristine-guest` volume copies the same firmware, preparation report,
identity and unchanged small overlay. Its working AUX starts from the pinned
original (`2ca2b332f05e2d6e3663bb4db0982a5feec268a8d1b91460f140ad8d3cb49414`).
Source files were read-only and shared-locked during preparation.

The first 250-second observer wait ended during cold retrieval: inconclusive.
Its AUX was archived before restoring the original for the next trial. Attempt
`20261027T201625Z-nxu_x5bi` then captured the transfer after 287.965 seconds,
including two cold layers verified by the unchanged backend.

This pre-injection capture has a zeroed `osenvironment`, an empty original
command line, a boot UUID different from Recovery, and a real
`/chosen/secure-boot-hashes/system-volume-auth-blob`. The working-AUX capture
instead names `recoveryos` and an `arm64eBaseSystem.dmg` URI. The new tree has
9960 zero padding bytes inside its 573440-byte reservation; the NoSEP edit fits.

This supports normal selection from original AUX, not an installed-root mount
claim. `recovery-snag-key-pressed` remains one in both captures; it alone does
not establish the trigger. No GPIO, UUID, authentication blob, boot-volume tuple
or `fsboot` command was forged.

The control AUX was archived again and restored before the planned full boot.
Only this isolated experimental copy was restored; the main pair is untouched.
Do not generalize that action to a running or successfully booted guest pair.

The full boot uses lossless compressed Reims capture: at most 8 MiB total
compressed artifacts/previews/metadata, plus a separate 64 MiB raw hard cap.
No messages are filtered. Wall, host-space and overlay guards stay unchanged;
the original regular-file mode keeps its raw eight-MiB limit.
