The retained core establishes a host LLVM JIT abort during creation of Reims'
guest-page scatter/writeback pipeline. It does not establish a macOS kernel
panic or an unsupported memoryless descriptor as the immediate crash cause.

Attempt: `20261028T145920Z-kke64w8i`. QEMU returned signal 6; stderr reports
`LLVM ERROR: Cannot emit physreg copy instruction`. The completed 9,722,593,280-byte
WSL dump is an ELF64, little-endian, x86-64 core. Its first 4096-byte SHA-256 is
`825b5ca8d8453806f0140ab24a5cba6a6230d9e4a4875aff5e0f0de3a0994317`.
The executable matches the admitted SHA-256
`cda522b21daa41a26e71e5ff97aeef45eb8d7212d025782fa42ec68cec1c4fe3`.

Faulting thread LWP 67:

```text
abort
llvm::report_fatal_error
stripped target copy implementation (LLVM-relative address 0x4404123)
llvm::TargetInstrInfo::lowerCopy
llvm::MachineFunctionPass::runOnFunction
llvm::legacy::PassManagerImpl::run
llvm::MCJIT::emitObject / generateCodeForModule / finalizeObject
LLVMGetPointerToGlobal
libvulkan_lvp.so worker
```

The target method is invoked through the instruction-info vtable at offset
0x1a8. The recovered call-site register arguments are destination physical
register ID 194 and source ID 138. Their names were not resolved. The error
text and surrounding X86 target exports are consistent with
`X86InstrInfo::copyPhysReg`'s final refusal in LLVM 20.1.2, but the actual
target frame is stripped; no exact symbol/source-line resolution is claimed.
[LLVM 20.1.2 target source](https://github.com/llvm/llvm-project/blob/llvmorg-20.1.2/llvm/lib/Target/X86/X86InstrInfo.cpp#L4072).

Concurrently, QEMU's main thread LWP 12 is waiting inside the same Vulkan
driver, reached through:

```text
ResourcePools::scatter_pipeline
plan_guest_copy
copy_target_to_guest_pages
write_bgra8_from_resident_gpu
store_render_frame
writeback_debt::pay / settle_for_mapping
scanout::paint_mapping
```

This is the device's own 411-word `GUEST_SCATTER_SPIRV` kernel, used to move
rendered bytes into guest pages. It is not a translated guest AIR shader.
The complete retained trace records a first draw submitted through `PostPark`
before this writeback phase; submission is not desktop or frame-completion proof.
The driver aborts inside pipeline compilation, so the ordinary Vulkan-error
return and `scatter_refused` fallback cannot execute.

Smallest falsifiable next probe: retain the same QEMU and Lavapipe driver, but
set only `REIMS_VGPU_COMPUTE_SCATTER=off`. The existing configuration contract
(`reims-vgpu-config/src/lib.rs:488`) selects the byte-equivalent per-run transfer
implementation. `engine/mod.rs:3930` bypasses compute-scatter pipeline creation
and uses `plan_guest_linear_copies`; `:4399` parses the switch. This is an
existing narrowing switch, not invented backing or a CPU-context bypass.
It has not been executed by this investigation and is not yet a proven fix.
An even smaller isolated reproducer can create only `ScatterPipeline` with the
same driver/CPU capabilities; it needs no guest disk or macOS boot.

Matched library provenance from the retained runtime:

- Mesa Vulkan driver package `25.2.8-0ubuntu0.24.04.4`,
  `libvulkan_lvp.so` SHA-256
  `5a218118760fee2398cc783820a1cc052de162d8c937dafcd6045576dfd9576c`,
  ELF build ID `b3fb0cf7870efc6646e21939393d3d2ad05cf1dc`.
- LLVM package `1:20.1.2-0ubuntu1~24.04.3`, `libLLVM.so.20.1` SHA-256
  `4b93481bd1c9d42c0951275dd275d4a9d30db78c309ae2cc0405669bc6dbbf8a`,
  ELF build ID `3fcd3870b6181594738d6ab5e8275744cca4cb03`.

Evidence: `core-backtrace.txt` (57,891 bytes), `target-backtrace.txt`
(21,133 bytes), and both extraction JSONs. The first pass contains 24 bounded
thread backtraces and mapped-library information. The second retains the
lowerCopy virtual-call site and QEMU's writeback call path. Some disassembly
windows begin within a function; their first partial instruction is not used
as evidence. Libraries lack debugging information, so exact LLVM register
classes and the compiler defect's triggering condition remain unresolved.

Both GDB processes exited successfully; both owned containers are absent;
all core handles are closed. Root can reclaim the completed core after its
own final inventory. No large copy, source edit, build, live-process attachment,
guest operation, service action, driver/CPU switch, deletion or delegation was
performed. Each analysis container used one CPU, a 1 GiB memory/equal swap
limit, no network, read-only source/core mounts and bounded output. Process
argument lines were suppressed; no guest memory contents were dumped.
