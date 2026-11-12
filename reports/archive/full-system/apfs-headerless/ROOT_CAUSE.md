VERIFIED: true (reader representation defect; exact failed live OMAP selection remains unobserved)

The independent manufactured virtual OMAP fixture passes normal inode/directory lookup and fails
sealed root lookup at Container.load_node -> check_object: checksum mismatch in fs tree. See
before.log and before.json for the pinned offline command, source hashes, resources and status.
The zero header is required by Apple's BTNODE_NOHEADER contract; offsets remain unchanged.
_fs_node loses OMAP_VAL_NOHEADER, load_node always requires Fletcher, BNode requires a nonzero
object type, and BTree._child ignores binv_child_hash. The parent-provided root-hash-probe.json
separately verifies a cached live root against adjacent checksummed integrity metadata. This does
not prove the unlogged OMAP selection of the failed preparation.

Authority: https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf
printed pp. 48, 54, 59, 123-133, 150-153. Original reader is fs-explorer 0.5.0, BSD-3-Clause.
No GPL implementation source was used. No fetch/traversal is needed to reproduce the defect.
