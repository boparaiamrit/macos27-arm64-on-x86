Root-relative sealed child identifiers
====================================

The first live retry passed integrity-metadata and root SHA256 validation, then failed resolving encoded child identifier3422 directly in the volume object map. The maintained7-Zip APFS implementation adds the volume's root-tree OID to a hashed index child identifier before resolving that virtual OID. This behavior is absent from the older Apple specification text; it is not a physical-address fallback.

Primary implementation inspected at commit b88c6bc09339de32f7d18bbab900686b244f42ba:
https://github.com/ip7z/7zip/blob/b88c6bc09339de32f7d18bbab900686b244f42ba/CPP/7zip/Archive/ApfsHandler.cpp

The local correction applies only to sealed virtual filesystem children, adds the SAME root-tree OID at every depth, rejects uint64 overflow, then uses the existing volume object map and parent-child SHA verification. Ordinary absolute virtual pointers remain unchanged. Sealed physical-pointer trees are explicitly unsupported.

Manufactured root-relative fixtures failed before the correction (3failures,23errors);32tests pass afterward, including deep traversal, a decoy mapping at the unadjusted number, no alternate-address fallback, overflow, bad hashes, and corrupt normal metadata. The real ordinary restore regression passes. Files: relative-before.log, relative-after.log, relative-restore.log.

A new targeted live attempt is running from run-20261027T150946Z. Successful live traversal and firmware extraction are still pending; no desktop claim follows from these fixtures.
