# Normal-root publication diagnostic

The fresh-AUX normal boot executed Darwin 27 and then entered its Recovery
restart path. A read-only decode of the valid control NVRAM bank gives the
18-byte reason `missing-boot-media`. The serial log independently shows no
`boot-uuid-media` publication or `BSD root:` before that restart.

This is a root-resource publication failure, not evidence that physical disks
are absent. The selected identifier matches the original boot-volume tuple
and cached, checksum-verified System/Data superblock fields. The normal ADT
has a real System authentication blob; no UUID or authentication data is
being substituted.

Apple's public XNU implementation waits 60 seconds in release builds and
requests Recovery when the matching root service is missing (or repeated
mount attempts fail). It parses `wdt`; `wdt=-1` keeps waiting rather than
taking that Recovery fallback. The root-matching condition remains in place.
The exact Golden source is unavailable, but the observed panic site, persisted
reason and write sequence agree with this public path.

[Primary implementation](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/iokit/bsddev/IOKitBSDInit.cpp#L908)

One cold, fully authenticated streamed layer took 89.067 seconds in the failed
run. The main APFS container began initialization but did not report checkpoint
completion before Recovery was requested. Timing is therefore a testable
candidate, not a proven storage/crypto/driver cause.

The next isolated profile adds only the documented `wdt=-1` boot option while
retaining the qualified r3 handoff and all original arguments. No installed
kernel patch, panic NOP, seal bypass or forced root-device identifier is used.
Host wall, space, NBD, log and overlay bounds remain finite and unchanged.
Successful root publication and mount still require actual guest evidence.
