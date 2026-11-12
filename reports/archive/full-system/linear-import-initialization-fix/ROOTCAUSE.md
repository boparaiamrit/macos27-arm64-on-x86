# Preserved pixels are not a valid initial external-image layout

R5's admitted imported-parent control emitted two native
VUID-VkImageCreateInfo-pNext-01443 errors. The exact frozen factory passed
HOST_ALLOCATION_EXT and PREINITIALIZED together. This is outside Vulkan's image
creation contract, which requires UNDEFINED for a nonzero external handle type.
See [VkImageCreateInfo](https://docs.vulkan.org/refpages/latest/refpages/source/VkImageCreateInfo.html).

Changing only the constant would not preserve the contract used by the callers:
registry birth marks guest-imported images content-ready with GuestBacking
(PREINITIALIZED/HOST_WRITE), and the direct sampled path also starts its first
transition at PREINITIALIZED. No defined operation establishes existing pixels
after a discard transition, and HOST_ALLOCATION_EXT has no implied external image
layout in Vulkan's [external image layout rules](https://docs.vulkan.org/spec/latest/chapters/resources.html#resources-image-layouts).

The prepared correction returns the typed reason
`preserved_contents_unimplemented` before allocating an imported parent or
creating a child. Both current consumers need the existing pixels. The primary
resident fallback creates an unready owned image and performs its normal seed
copy; the sampled fallback retains the existing guest-buffer or CPU upload.
Host-pointer buffer imports remain available. The reason describes a missing
initialization contract, not missing hardware support.

The factory's image-create parameters also take their initial layout from the
same checked decision. Discardable external contents resolve to UNDEFINED;
preserved contents are refused. No caller is changed to request discardable
contents or to claim initialized contents.

R5 provides the native failing witness. The packet adds owner-level layout tests
and includes the new reason in the unique-slug test. Native qualification must
prove primary partial-draw seed preservation, sampled upload fallback and normal
resource cleanup under Core and synchronization validation. Neither the static
fallback trace nor a refused optional import is a successful imported-image or
desktop result.

Production scope: one file, linear_target_import.rs. Existing memory-release
fixes, image consumers, buffer import owners, queue/lifetime behavior, capability
queries and configuration parsing are preserved. Prepared bytes are host-side
only until exact source staging is authorized by the parent.
