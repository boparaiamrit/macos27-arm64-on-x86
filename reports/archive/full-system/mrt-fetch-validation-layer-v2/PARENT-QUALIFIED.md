# Isolated validation layer qualified for engine tests

Official Debian vulkan-validationlayers1.4.309.0-1 package bytes and published SHA256 matched. Data was extracted into this owned directory; no system/image installation occurred. The original bundle and manifest are preserved. Only library_path differs in the derived manifest.

The pinned runtime13 resolved all ELF/versioned dependencies. The actual layer library and pinned Mesa26/LLVM21 files were mapped, and a Vulkan1.2 instance plus CPU device succeeded. Core and synchronization validation were enabled. Probe capture reports2warnings/0errors and1manualdebugcallbackselftest. That selftest is capture proof, not VUID-negative-control proof. No render resources/draws ran.

The first global-inventory stop was our authorized concurrent RED-measurement helper; execution was serialized. A later owned settings parser initially counted preset references instead of the unique BOOL definitions. Both failures and their cleanup remain preserved. Parent corrected that parser and resumed from hash-verified extracted data. No driver/runtime bytes were substituted.

parent-pin-manifest.json supplies exact hashes, read-only mount paths and engine environment. parent-qualified-handoff.json, loader logs, dependency logs and qualify-receipt.json contain actual enablement/resource proof. Signature verification was not performed; authentication is officialHTTPS plus exact published SHA256. This bundle qualifies later API checking, not renderer correctness or desktop success.
