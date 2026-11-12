The failing physical APFS block is supplied by the retained QCOW2 overlay.

The bounded read-only probe validated GPT CRCs and the 4096-byte APFS container in partition2. It compared physical block0x29ab7 at absolute offset1,223,409,664. RAW contains a checksummed extentref-subtype0xf object at xid2704; the working overlay supplies a different checksummed subtype0xb object at xid4230. QEMU range mapping reports depth0/present/data for those4096 bytes. This matches the panic after checkpoint rollback from4232 to4226.

This localizes the observed replacement to the working overlay. It does not identify the writer/write ordering, prove complete base-filesystem health, or establish a graphics regression. Earlier logs already contained checkpoint corruption and unclean-unmount history while Data still mounted; this exact fatal mismatch was absent from the three preceding inspected boots.

The NBDSource reader performed4 reads totaling25,088 bytes. QEMU operations were restricted to a qualified4096-byte offset-wrapper read and4096-byte range map. The wrapper syntax first passed an authored RAM fixture. RAW and CONTROL mounts were read-only, the old runner lock held exclusively, and overlay inode/length/mtime stayed unchanged. No filesystem mount, repair, VM, download or replacement occurred. The failed pair remains preserved; a separate fresh working pair is the next experiment.
