# Reconciled-v2 baseline RED regression packet

Confirmed the five authorized behavioral RED cases: **0 passed, 5 failed**, test exit **101**. The locked offline unit-lib compilation exited **0**.

The parent reconciliation receipt and v2 manifest match the supplied SHA-256 values. All four actual destination before hashes matched v2 before any copy. The new harness verified qualified and production metadata, frozen raw production exports, and `old_before.decode("utf-8").encode("cp1252") == exact_raw_before` for all four files. The original packet and original failed red-run remain preserved.

## Exact staged source

Four files were copied with read_bytes/write_bytes and current mtimes; three changed content. The packet assertions and helper logic were staged unchanged. All other isolated source files, Cargo manifests and locks, the admitted RGBA16 baseline, protected artifacts, and all 618 compiler-source pins passed preservation checks.

`crates/reims-vgpu/src/backend/vulkan/engine/color_input.rs`

Before SHA-256: `9285223cadaa8cb4de41e13fb5200c7c09dabe6961b8ee1e08912a54a97eb645`

Staged SHA-256: `6c44f2f5e98350fdd4ad5f2adada55b6edabaf1280f17fa1db21b0d344148db4`

`crates/reims-vgpu/src/backend/vulkan/engine/caches.rs`

Before SHA-256: `96f5c9b5aa5846713f529bfe79b64b9deddbfa0a5491432b5234d5e87b0ae1ca`

Staged SHA-256: `1274d37048a8eca6555f867b2f5a1e91d640eee172833eb122349241ea102809`

`crates/reims-vgpu/src/backend/vulkan/engine/exec.rs`

Before SHA-256: `3480b46d821c2115c76bd530a79cd6ae078cebd732adc7a36b1a2491d0a10309`

Staged SHA-256: `188ce22fa466527c3b1bf93883a871484943660c09bd5d889e35aab2fd2938d7`

`crates/reims-vgpu/src/backend/vulkan/caps/device_features.rs`

Before SHA-256: `a5102fa9fa23e9f98e31784ad7a15ad5638e7be0c4fa44417cc19a2249c6638f`

Staged SHA-256: `a5102fa9fa23e9f98e31784ad7a15ad5638e7be0c4fa44417cc19a2249c6638f`

## Test outcome and assertions

A fresh binary process ran only `parent_review_ --test-threads=1 --nocapture` with `REIMS_VGPU_COLOR_GENERAL=off`. The narrow-mode preconditions passed; a wrong-mode precondition is classified as a harness error. These five cases only construct owner plans/barrier structures and create no Vulkan resources. Mesa 26 was mounted read-only at both /soft and /out/runtime for dynamic dependencies, with LD_LIBRARY_PATH=/soft/lib.

Counts: `{"failed": 5, "filtered_out": 2301, "ignored": 0, "measured": 0, "passed": 0}`.

```text
thread 'backend::vulkan::engine::caches::parent_review_primary_load_tests::parent_review_primary_load_names_the_recorded_entry_layout' (10) panicked at crates/reims-vgpu/src/backend/vulkan/engine/caches.rs:4596:9:
assertion `left == right` failed
  left: (LOAD, COLOR_ATTACHMENT_OPTIMAL)
 right: (LOAD, GENERAL)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

```text
thread 'backend::vulkan::engine::color_input::parent_review_span_tests::parent_review_sparse_input_table_obeys_stage_span_limit' (11) panicked at crates/reims-vgpu/src/backend/vulkan/engine/color_input.rs:176:9:
one descriptor still requires eight input-reference table entries
```

```text
thread 'backend::vulkan::engine::exec::parent_review_primary_layout_tests::parent_review_empty_restart_uses_final_to_entry_transition' (12) panicked at crates/reims-vgpu/src/backend/vulkan/engine/exec.rs:8720:9:
assertion `left == right` failed
  left: GENERAL
 right: COLOR_ATTACHMENT_OPTIMAL
```

```text
thread 'backend::vulkan::engine::exec::parent_review_primary_layout_tests::parent_review_readback_starts_and_restores_the_actual_pass_exit' (13) panicked at crates/reims-vgpu/src/backend/vulkan/engine/exec.rs:8705:9:
assertion `left == right` failed
  left: GENERAL
 right: COLOR_ATTACHMENT_OPTIMAL
```

```text
thread 'backend::vulkan::engine::exec::parent_review_primary_layout_tests::parent_review_ready_primary_transitions_when_next_pass_layout_differs' (14) panicked at crates/reims-vgpu/src/backend/vulkan/engine/exec.rs:8713:9:
assertion failed: !pass_exit_needs_no_barrier(super::super::pools::ResidentAccess::ColorWrite(key.color_final_layout(0)),
        key.color_layout(0))
```

The ready-elision case is coupled to the new explicit-entry contract. It does not establish an independent existing old ready-path defect. The other cases expose the captured owner conditions. No correction followed this RED run.

## Fresh compilation and native envelope

Unit binary: `/work/orchard-m27/reims-vgpu/target/release/deps/reims_vgpu-adceb44d491f78fa`.

SHA-256: `07cb8f9e69d6e143a97d1c9f6c25158172e908191c007606a73c0c8d92c8275b`.

Size: 24248240 bytes. Cargo compiler-artifact fresh=false, the binary timestamp follows compilation start, and its bytes differ from the prior unit executable. See fresh-compile-proof.json.

Compile command: `cargo test --release --locked --offline -p reims-vgpu --no-default-features --features backend-vulkan,host-window --lib --no-run --message-format=json`. This uses the existing cached release test profile for the unit-lib executable only; no release archive or QEMU link ran.

Builder/measurement: image sha256:14ea78615d69de5eea70014968be23464751916c6c44793f19f5771a9b4eeb17, 4 CPUs, 6 GiB RAM, memory-swap equal to RAM, pids 256, jobs 2. Test: pinned image sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635, 2 CPUs, 2 GiB RAM, memory-swap equal to RAM, pids 128. Every action had read-only root, network none, init, /tmp 64 MiB, core limit 0 and coredump_filter 0x10. /parent was a full directory read-only mount; /out was writable; /work was writable only for the build. Docker inspect and native cgroup receipts verify the envelope.

measure: native memory peak 1402585088 bytes; max/OOM events {"high": 0, "low": 0, "max": 0, "oom": 0, "oom_group_kill": 0, "oom_kill": 0}; guard elapsed 23.484s; maximum native guard gap 0.221639s; maximum host watchdog gap 0.412018s.

build: native memory peak 3033595904 bytes; max/OOM events {"high": 0, "low": 0, "max": 0, "oom": 0, "oom_group_kill": 0, "oom_kill": 0}; guard elapsed 329.985s; maximum native guard gap 0.351675s; maximum host watchdog gap 1.226721s.

test: native memory peak 15003648 bytes; max/OOM events {"high": 0, "low": 0, "max": 0, "oom": 0, "oom_group_kill": 0, "oom_kill": 0}; guard elapsed 5.407s; maximum native guard gap 0.210273s; maximum host watchdog gap 0.400544s.

## Guards, preservation and cleanup

Minimum sampled host free: 45914603520 bytes. The unconditional floor remained 10 GiB with sample age [-2,20] and 0.2-second polls. Command/test/active caps were 900/60/1200 seconds. The admitted growth cap was 800000000 bytes; maximum sampled source-plus-target logical growth was 58127947 bytes. Host evidence stayed under 16 MiB and each canonical log stayed under 2 MiB. See allocation-premeasure.json and allocation-after-test.json.

All owned containers ended, attach clients were reaped, owned containers were removed, and no owned container IDs remained. TERM/KILL details are recorded per action. The original 89 container IDs and 28 volumes, sampler PID 77088 and original start, exporter PID 679 and original start, and Android PID 79064 were preserved by postflight. No Golden VM, GPU rendering, guest input, CONTROL/RAW/state/NBD mounts, guest filesystem reads, source fixes, runtime changes, or infrastructure changes occurred.

## Parent handoff

Review behavior-red.json and the canonical parent-review stdout/stderr logs, then apply coordinated corrections as source owner. This test agent ends after RED; no corrective implementation or rerun was attempted. handoff.json contains structured counts, hashes, assertions, resource evidence, and cleanup references. evidence-sha256.json indexes this owned evidence directory.
