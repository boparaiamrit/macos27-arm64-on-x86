#!/usr/bin/env python3
"""Build QEMU (apple-vm / vmapple) with the FastJIT AArch64->x86_64 native engine wired in."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

START = time.monotonic()
WORK = Path('/work')
ORCHARD = WORK / 'orchard'
NEW = WORK / 'orchard-fastjit'
PARENT = Path('/parent')
INTEG = PARENT / 'fastjit/qemu-integration'
R10B_LIB = PARENT / 'full-system/m2v-prefix-load/artifacts-r10b/libreims_vgpu.a'
CRYPTO_DIFF = PARENT / 'orchard-build/golden-crypto/orchard-golden-crypto.diff'


def run(argv, *, cwd=None):
    print('+', ' '.join(str(x) for x in argv), flush=True)
    subprocess.run(argv, cwd=cwd, check=True)


def patch_once(path: Path, old: str, new: str):
    text = path.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{path}: expected 1 occurrence of target block, found {count}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


def main():
    if NEW.exists():
        shutil.rmtree(NEW)

    run(['git', 'clone', '--shared', '--no-checkout', str(ORCHARD), str(NEW)])
    run(['git', 'checkout', '--detach', 'c73a2bda1fd4afefd61204bb74afd74292ef2fe9'], cwd=NEW)
    run(['git', 'apply', '--check', str(CRYPTO_DIFF)], cwd=NEW)
    run(['git', 'apply', str(CRYPTO_DIFF)], cwd=NEW)

    # Copy pre-fetched subprojects from 27on86 so configure needs no network
    for sub in ('keycodemapdb', 'dtc', 'berkeley-softfloat-3', 'berkeley-testfloat-3'):
        src = PARENT / '27on86/subprojects' / sub
        dst = NEW / 'qemu/subprojects' / sub
        if src.is_dir() and not dst.exists():
            shutil.copytree(src, dst, symlinks=True)

    # Copy FastJIT header and implementation into QEMU source tree
    shutil.copy2(INTEG / 'fastjit-a64.h', NEW / 'qemu/include/exec/fastjit-a64.h')
    shutil.copy2(INTEG / 'fastjit-a64.c', NEW / 'qemu/target/arm/tcg/fastjit-a64.c')

    # 1. Patch include/exec/translation-block.h
    tb_h = NEW / 'qemu/include/exec/translation-block.h'
    patch_once(
        tb_h,
        '    uintptr_t jmp_list_head;\n'
        '    uintptr_t jmp_list_next[2];\n'
        '    uintptr_t jmp_dest[2];\n'
        '};',
        '    uintptr_t jmp_list_head;\n'
        '    uintptr_t jmp_list_next[2];\n'
        '    uintptr_t jmp_dest[2];\n'
        '    void *fastjit_fn;\n'
        '    uint32_t fastjit_flags;\n'
        '};'
    )

    # 2. Patch accel/tcg/translate-all.c
    trans_all_c = NEW / 'qemu/accel/tcg/translate-all.c'
    patch_once(
        trans_all_c,
        '    tb->cs_base = s.cs_base;\n'
        '    tb->flags = s.flags;\n'
        '    tb->cflags = s.cflags;',
        '    tb->cs_base = s.cs_base;\n'
        '    tb->flags = s.flags;\n'
        '    tb->cflags = s.cflags;\n'
        '    tb->fastjit_fn = NULL;\n'
        '    tb->fastjit_flags = 0;'
    )
    patch_once(
        trans_all_c,
        ' restart_translate:\n'
        '    trace_translate_block(tb, s.pc, tb->tc.ptr);',
        ' restart_translate:\n'
        '    tb->fastjit_fn = NULL;\n'
        '    tb->fastjit_flags = 0;\n'
        '    trace_translate_block(tb, s.pc, tb->tc.ptr);'
    )

    # 3. Patch accel/tcg/cpu-exec.c
    cpu_exec_c = NEW / 'qemu/accel/tcg/cpu-exec.c'
    patch_once(
        cpu_exec_c,
        '#include "exec/translation-block.h"\n',
        '#include "exec/translation-block.h"\n'
        '#include "exec/fastjit-a64.h"\n'
    )
    patch_once(
        cpu_exec_c,
        '    tb = tb_lookup(cpu, s);\n'
        '    if (tb == NULL) {\n'
        '        return tcg_code_gen_epilogue;\n'
        '    }\n',
        '    tb = tb_lookup(cpu, s);\n'
        '    if (tb == NULL) {\n'
        '        return tcg_code_gen_epilogue;\n'
        '    }\n'
        '    if (qatomic_read(&tb->fastjit_fn) != NULL &&\n'
        '        likely(qatomic_read(&cpu->neg.icount_decr.u16.high) == 0)) {\n'
        '        for (int fj_step = 0; fj_step < 8; fj_step++) {\n'
        '            fastjit_exec_one(env, tb);\n'
        '            if (unlikely(qatomic_read(&cpu->neg.icount_decr.u16.high) != 0) ||\n'
        '                (tb->fastjit_flags & FASTJIT_FLAG_BACKWARD)) {\n'
        '                return tcg_code_gen_epilogue;\n'
        '            }\n'
        '            s = cpu->cc->tcg_ops->get_tb_cpu_state(cpu);\n'
        '            s.cflags = curr_cflags(cpu);\n'
        '            if (unlikely(check_for_breakpoints(cpu, s.pc, &s.cflags))) {\n'
        '                cpu_loop_exit(cpu);\n'
        '            }\n'
        '            tb = tb_lookup(cpu, s);\n'
        '            if (tb == NULL) {\n'
        '                return tcg_code_gen_epilogue;\n'
        '            }\n'
        '            if (qatomic_read(&tb->fastjit_fn) == NULL) {\n'
        '                break;\n'
        '            }\n'
        '        }\n'
        '    }\n'
    )
    patch_once(
        cpu_exec_c,
        '    qemu_thread_jit_execute();\n'
        '    ret = tcg_qemu_tb_exec(cpu_env(cpu), tb_ptr);\n',
        '    qemu_thread_jit_execute();\n'
        '    if (qatomic_read(&itb->fastjit_fn) != NULL &&\n'
        '        likely(qatomic_read(&cpu->neg.icount_decr.u16.high) == 0) &&\n'
        '        !icount_enabled()) {\n'
        '        for (int fj_step = 0; fj_step < 8; fj_step++) {\n'
        '            fastjit_exec_one(cpu_env(cpu), itb);\n'
        '            if (unlikely(qatomic_read(&cpu->neg.icount_decr.u16.high) != 0) ||\n'
        '                (itb->fastjit_flags & FASTJIT_FLAG_BACKWARD)) {\n'
        '                cpu->neg.can_do_io = true;\n'
        '                *tb_exit = 0;\n'
        '                return NULL;\n'
        '            }\n'
        '            TCGTBCPUState fj_s = cpu->cc->tcg_ops->get_tb_cpu_state(cpu);\n'
        '            fj_s.cflags = curr_cflags(cpu);\n'
        '            if (unlikely(check_for_breakpoints(cpu, fj_s.pc, &fj_s.cflags))) {\n'
        '                cpu->neg.can_do_io = true;\n'
        '                *tb_exit = 0;\n'
        '                return NULL;\n'
        '            }\n'
        '            itb = tb_lookup(cpu, fj_s);\n'
        '            if (itb == NULL) {\n'
        '                cpu->neg.can_do_io = true;\n'
        '                *tb_exit = 0;\n'
        '                return NULL;\n'
        '            }\n'
        '            if (qatomic_read(&itb->fastjit_fn) == NULL) {\n'
        '                tb_ptr = itb->tc.ptr;\n'
        '                break;\n'
        '            }\n'
        '            if (fj_step == 7) {\n'
        '                cpu->neg.can_do_io = true;\n'
        '                *tb_exit = 0;\n'
        '                return NULL;\n'
        '            }\n'
        '        }\n'
        '    }\n'
        '    ret = tcg_qemu_tb_exec(cpu_env(cpu), tb_ptr);\n'
    )

    # 4. Patch target/arm/tcg/translate-a64.c
    trans_a64_c = NEW / 'qemu/target/arm/tcg/translate-a64.c'
    patch_once(
        trans_a64_c,
        '#include "translate-a64.h"\n',
        '#include "translate-a64.h"\n'
        '#include "exec/fastjit-a64.h"\n'
    )
    patch_once(
        trans_a64_c,
        'static void aarch64_tr_tb_start(DisasContextBase *db, CPUState *cpu)\n'
        '{\n'
        '}\n',
        'static void aarch64_tr_tb_start(DisasContextBase *db, CPUState *cpu)\n'
        '{\n'
        '    DisasContext *dc = container_of(db, DisasContext, base);\n'
        '    (void)cpu;\n'
        '    fastjit_tb_start(db->tb, db->pc_first, dc->btype, dc->ss_active,\n'
        '                     dc->pstate_il, dc->gcs_en, dc->bt);\n'
        '}\n'
    )
    patch_once(
        trans_a64_c,
        '    s->pc_curr = pc;\n'
        '    /* Code is always little-endian on Aarch64 */\n'
        '    insn = translator_ldl_end(env, &s->base, pc, MO_LE);\n'
        '    s->insn = insn;\n'
        '    s->base.pc_next = pc + 4;\n',
        '    s->pc_curr = pc;\n'
        '    /* Code is always little-endian on Aarch64 */\n'
        '    insn = translator_ldl_end(env, &s->base, pc, MO_LE);\n'
        '    fastjit_tb_insn(s->base.tb, pc, insn);\n'
        '    s->insn = insn;\n'
        '    s->base.pc_next = pc + 4;\n'
    )
    patch_once(
        trans_a64_c,
        'static void aarch64_tr_tb_stop(DisasContextBase *dcbase, CPUState *cpu)\n'
        '{\n'
        '    DisasContext *dc = container_of(dcbase, DisasContext, base);\n',
        'static void aarch64_tr_tb_stop(DisasContextBase *dcbase, CPUState *cpu)\n'
        '{\n'
        '    DisasContext *dc = container_of(dcbase, DisasContext, base);\n'
        '    fastjit_tb_stop(dc->base.tb, dc->base.num_insns, dc->base.is_jmp);\n'
    )

    # 5. Patch target/arm/tcg/pauth_helper.c with FastJIT VA-parameter cache
    pauth_c = NEW / 'qemu/target/arm/tcg/pauth_helper.c'
    patch_once(
        pauth_c,
        'static uint64_t pauth_addpac(CPUARMState *env, uint64_t ptr, uint64_t modifier,\n'
        '                             ARMPACKey *key, bool data)\n'
        '{\n'
        '    ARMCPU *cpu = env_archcpu(env);\n'
        '    ARMMMUIdx mmu_idx = arm_stage1_mmu_idx(env);\n'
        '    ARMVAParameters param = aa64_va_parameters(env, ptr, mmu_idx, data, false);\n',
        'typedef struct FastJitPAuthSlot {\n'
        '    const CPUARMState *env;\n'
        '    uint64_t tcr;\n'
        '    ARMMMUIdx mmu_idx;\n'
        '    ARMVAParameters param;\n'
        '} FastJitPAuthSlot;\n\n'
        'static __thread FastJitPAuthSlot tls_pauth_cache[4];\n\n'
        'static inline ARMVAParameters fastjit_va_parameters(CPUARMState *env,\n'
        '                                                    uint64_t ptr,\n'
        '                                                    bool data)\n'
        '{\n'
        '    ARMMMUIdx mmu_idx = arm_stage1_mmu_idx(env);\n'
        '    uint64_t tcr = regime_tcr(env, mmu_idx);\n'
        '    unsigned idx = (((unsigned)(ptr >> 55) & 1u) << 1) | (unsigned)data;\n'
        '    FastJitPAuthSlot *slot = &tls_pauth_cache[idx];\n'
        '    if (likely(slot->env == env && slot->tcr == tcr && slot->mmu_idx == mmu_idx)) {\n'
        '        return slot->param;\n'
        '    }\n'
        '    ARMVAParameters param = aa64_va_parameters(env, ptr, mmu_idx, data, false);\n'
        '    slot->env = env;\n'
        '    slot->tcr = tcr;\n'
        '    slot->mmu_idx = mmu_idx;\n'
        '    slot->param = param;\n'
        '    return param;\n'
        '}\n\n'
        'static uint64_t pauth_addpac(CPUARMState *env, uint64_t ptr, uint64_t modifier,\n'
        '                             ARMPACKey *key, bool data)\n'
        '{\n'
        '    ARMCPU *cpu = env_archcpu(env);\n'
        '    ARMVAParameters param = fastjit_va_parameters(env, ptr, data);\n'
    )
    patch_once(
        pauth_c,
        '    ARMMMUIdx mmu_idx = arm_stage1_mmu_idx(env);\n'
        '    ARMVAParameters param = aa64_va_parameters(env, ptr, mmu_idx, data, false);\n'
        '    ARMPauthFeature pauth_feature = cpu_isar_feature(pauth_feature, cpu);',
        '    ARMVAParameters param = fastjit_va_parameters(env, ptr, data);\n'
        '    ARMPauthFeature pauth_feature = cpu_isar_feature(pauth_feature, cpu);'
    )
    patch_once(
        pauth_c,
        'static uint64_t pauth_strip(CPUARMState *env, uint64_t ptr, bool data)\n'
        '{\n'
        '    ARMMMUIdx mmu_idx = arm_stage1_mmu_idx(env);\n'
        '    ARMVAParameters param = aa64_va_parameters(env, ptr, mmu_idx, data, false);\n',
        'static uint64_t pauth_strip(CPUARMState *env, uint64_t ptr, bool data)\n'
        '{\n'
        '    ARMVAParameters param = fastjit_va_parameters(env, ptr, data);\n'
    )

    # 6. Patch target/arm/tcg/meson.build
    meson_b = NEW / 'qemu/target/arm/tcg/meson.build'
    patch_once(
        meson_b,
        "  'gengvec64.c',\n"
        "  'translate-a64.c',\n",
        "  'gengvec64.c',\n"
        "  'fastjit-a64.c',\n"
        "  'translate-a64.c',\n"
    )

    # 7. Set up pkgconfig pointing to R10b libreims_vgpu.a
    artifacts = NEW / 'artifacts'
    artifacts.mkdir(parents=True, exist_ok=True)
    lib_dst = artifacts / 'libreims_vgpu.a'
    shutil.copy2(R10B_LIB, lib_dst)

    pkg = NEW / 'pkgconfig'
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / 'reims-vgpu.pc').write_text(
        f'prefix={NEW}\n'
        f'includedir=${{prefix}}/reims-vgpu/crates/reims-vgpu/include\n'
        f'libdir={artifacts}\n'
        f'Name: reims-vgpu\n'
        f'Description: Orchard R10b Reims static library\n'
        f'Version: 0.0.0\n'
        f'Libs: ${{libdir}}/libreims_vgpu.a -lm -ldl -lpthread\n'
        f'Cflags: -I${{includedir}}\n',
        encoding='utf-8'
    )

    pydeps_path = NEW / 'qemu/pythondeps.toml'
    pydeps = pydeps_path.read_text(encoding='utf-8')
    pydeps = pydeps.replace(
        '"qemu" = { path = "python/" }\n"setuptools" = { accepted = ">=63.1.0" }\n"wheel" = { accepted = ">=0.41.2" }\n# pip should be guaranteed by mkvenv, this is merely a sanity check for\n# which version we are counting on being present.\n"pip" = { accepted = ">=23.2.1" }',
        ''
    )
    pydeps_path.write_text(pydeps, encoding='utf-8')

    os.environ['PKG_CONFIG_PATH'] = str(pkg)
    os.environ['PYTHONNOUSERSITE'] = '1'
    os.environ['PIP_NO_INDEX'] = '1'
    os.environ['NINJA_STATUS'] = '[%f/%t %e sec] '

    build = NEW / 'qemu/build'
    build.mkdir(parents=True, exist_ok=True)

    cfg_argv = [
        '../configure',
        '--target-list=aarch64-softmmu',
        '--disable-docs',
        '--enable-slirp',
        '--disable-werror',
        '--enable-tcg',
        '--disable-kvm',
        '--disable-debug-info',
        '--disable-tests',
        '--disable-guest-agent',
        '--disable-tools',
        '--disable-gtk',
        '--disable-sdl',
        '--enable-vnc',
        '--disable-opengl',
        '--enable-nettle',
        '--disable-gcrypt',
        '--disable-gnutls',
    ]
    run(cfg_argv, cwd=build)
    run(['/usr/bin/ninja', '-j8', 'qemu-system-aarch64'], cwd=build)

    qemu_bin = build / 'qemu-system-aarch64'
    shutil.copy2(qemu_bin, artifacts / 'qemu-system-aarch64')

    # Also populate /work/orchard-m27-pages-m2v-prefix2/artifacts so existing profiles work
    r10b_work = WORK / 'orchard-m27-pages-m2v-prefix2/artifacts'
    r10b_work.mkdir(parents=True, exist_ok=True)
    shutil.copy2(qemu_bin, r10b_work / 'qemu-system-aarch64')
    shutil.copy2(lib_dst, r10b_work / 'libreims_vgpu.a')

    # Copy to host integration folder
    host_art = INTEG / 'artifacts'
    host_art.mkdir(parents=True, exist_ok=True)
    shutil.copy2(qemu_bin, host_art / 'qemu-system-aarch64')

    sha = hashlib.sha256((artifacts / 'qemu-system-aarch64').read_bytes()).hexdigest()
    res = {
        'status': 'BUILD_PASS',
        'qemu_sha256': sha,
        'libreims_sha256': hashlib.sha256(lib_dst.read_bytes()).hexdigest(),
        'elapsed_seconds': round(time.monotonic() - START, 2),
    }
    (INTEG / 'build-result.json').write_text(json.dumps(res, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(res, indent=2), flush=True)


if __name__ == '__main__':
    main()
