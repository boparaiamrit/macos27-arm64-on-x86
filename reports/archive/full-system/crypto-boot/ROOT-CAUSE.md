# Missing emulator cipher backend

The 28 October normal-System attempt `20261027T211303Z-e7unitba` executed Darwin 27, published its normal root, mounted the installed Macintosh HD System snapshot, and validated its on-disk root hash. It reached the existing 1800-second host bound without a panic. Data mount, userspace and a desktop were not observed. The final serial message is AppleVPKeyStore's safe-xART support announcement; that message alone does not identify the blocked execution location.

The same attempt's stderr records five `cmd_data: Failed to create cipher object` failures. The qualified CTRR binary's configuration disables GCRYPT, NETTLE, GNUTLS_CRYPTO and AF_ALG. Its unchanged `crypto/cipher.c` consequently selects `cipher-stub.c.inc`; the stub always rejects cipher creation. The emulated AES device calls that function with a null error sink, reducing the precise unsupported-backend error to the observed generic failure. No AES payload output is DMA-written after this failure. This is a confirmed build defect independently of the final guest wait location.

The three preceding `No payload` messages occur while the command's three payload words arrive. Unknown writes at offsets `0x20` and `0x8` are separately unimplemented register behavior; neither is established as the cause of this stall.

Evidence:

- `../attempts/20261027T211303Z-e7unitba/serial.log:426` validates the root hash; line 433 completes System mounting; line 435 is the last serial message.
- The same attempt's `stderr.log:2466` through line 2470 records cipher creation failures.
- `../../orchard-build/golden-ctrr/configure.log:472` through line 477 records the disabled crypto backends.
- Qualified binary SHA-256: `dba936f79fdfecea6163360d4beea0495cf2e870c11816a6a1b0c08ca7a8b542`.
- Read-only inspection of the exact build found the backend macros undefined and the stub error string present in this binary.

The source contract is visible in Orchard's pinned [cipher implementation](https://github.com/yaelliethy/orchard/blob/c73a2bda1fd4afefd61204bb74afd74292ef2fe9/qemu/crypto/cipher.c#L132) and [stub](https://github.com/yaelliethy/orchard/blob/c73a2bda1fd4afefd61204bb74afd74292ef2fe9/qemu/crypto/cipher-stub.c.inc#L14). A separate VMApple project documents the same AppleVPKeyStore boundary when QEMU was built without a cipher backend. Its demonstrated guest is macOS 13 with ARM KVM, so this is corroboration rather than proof of Golden's complete failure cause. [Pinned report](https://github.com/DenrianWeiss/w515y-vmapple-scripts/blob/c309bbb59f276762d87e88962e3f4181993b69da/README.md#L195).

The next controlled change enables a real Nettle backend in a new emulator build, with no AES device source changes. Direct known-answer crypto checks and existing paused platform tests must pass before its pin is admitted. The normal-System CONTROL AUX/overlay pair is preserved. The same WDT handoff, root selection, on-disk authentication behavior, streamed backing and host resource bounds remain in use. The retained MAIN guest pair remains protected.

If the bounded boot still stops after System mounting, a separate read-only GDB observation can record the execution location. No recovery-panic, UUID, authentication, seal, or AES-success patch is justified by the current evidence.
