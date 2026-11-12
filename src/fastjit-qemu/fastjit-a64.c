/*
 * FastJIT AArch64 -> x86_64 Direct Native Basic-Block JIT Engine for QEMU
 *
 * Compiles eligible AArch64 register/immediate/bitfield/PC-relative/branch
 * basic blocks directly into native x86_64 machine code operating on
 * CPUARMState, bypassing TCG prologue/epilogue and IR dispatch.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#include "qemu/osdep.h"
#include "cpu.h"
#include "exec/translation-block.h"
#include "exec/fastjit-a64.h"
#include <sys/mman.h>

#define FASTJIT_CODE_BUFFER_SIZE (32u * 1024u * 1024u)
#define FASTJIT_MAX_INSNS        64
#define FASTJIT_MAX_BLOCK_BYTES  2048

typedef void (*fastjit_fn_t)(CPUARMState *env);

typedef struct FastJitRec {
    struct TranslationBlock *tb;
    uint64_t pc_first;
    uint32_t insns[FASTJIT_MAX_INSNS];
    int count;
    bool eligible;
    bool pcrel;
} FastJitRec;

static __thread FastJitRec tls_rec;

static uint8_t *g_fastjit_code_buf;
static uint32_t g_fastjit_code_used;
static int g_fastjit_init_state; /* 0 = uninit, 1 = initializing, 2 = ready, -1 = failed */

static uint64_t g_fastjit_blocks_compiled;
static uint64_t g_fastjit_blocks_executed;
static uint64_t g_fastjit_insns_executed;

typedef struct X64Buf {
    uint8_t data[FASTJIT_MAX_BLOCK_BYTES];
    size_t len;
    bool overflow;
} X64Buf;

static inline void emit_u8(X64Buf *b, uint8_t v)
{
    if (unlikely(b->len + 1 > sizeof(b->data))) {
        b->overflow = true;
        return;
    }
    b->data[b->len++] = v;
}

static inline void emit_u32(X64Buf *b, uint32_t v)
{
    if (unlikely(b->len + 4 > sizeof(b->data))) {
        b->overflow = true;
        return;
    }
    memcpy(&b->data[b->len], &v, 4);
    b->len += 4;
}

static inline void emit_u64(X64Buf *b, uint64_t v)
{
    if (unlikely(b->len + 8 > sizeof(b->data))) {
        b->overflow = true;
        return;
    }
    memcpy(&b->data[b->len], &v, 8);
    b->len += 8;
}

enum {
    X86_RAX = 0,
    X86_RCX = 1,
    X86_RDX = 2,
    X86_RSI = 6,
};

static inline void emit_mov_imm64(X64Buf *b, int x86_reg, uint64_t imm)
{
    if (imm == 0) {
        /* xor r32, r32 */
        emit_u8(b, 0x31);
        emit_u8(b, (uint8_t)(0xC0 | (x86_reg << 3) | x86_reg));
        return;
    }
    if (imm <= 0x7fffffffULL) {
        /* mov r32, imm32 (zero-extends to 64-bit) */
        emit_u8(b, (uint8_t)(0xB8 + x86_reg));
        emit_u32(b, (uint32_t)imm);
        return;
    }
    emit_u8(b, 0x48);
    emit_u8(b, (uint8_t)(0xB8 + x86_reg));
    emit_u64(b, imm);
}

static inline void emit_load_gpr(X64Buf *b, int x86_reg, int a64_reg,
                                 bool is_sp_ok, int sf)
{
    if (a64_reg == 31 && !is_sp_ok) {
        emit_u8(b, 0x31);
        emit_u8(b, (uint8_t)(0xC0 | (x86_reg << 3) | x86_reg));
        return;
    }
    int32_t disp = (int32_t)(offsetof(CPUARMState, xregs) + (size_t)a64_reg * 8);
    if (sf) {
        emit_u8(b, 0x48);
    }
    emit_u8(b, 0x8B);
    emit_u8(b, (uint8_t)(0x87 | (x86_reg << 3)));
    emit_u32(b, (uint32_t)disp);
}

static inline void emit_store_gpr(X64Buf *b, int x86_reg, int a64_reg,
                                  bool is_sp_ok, int sf)
{
    if (a64_reg == 31 && !is_sp_ok) {
        return;
    }
    int32_t disp = (int32_t)(offsetof(CPUARMState, xregs) + (size_t)a64_reg * 8);
    if (!sf) {
        /* mov r32, r32 to zero upper 32 bits before 64-bit store */
        emit_u8(b, 0x89);
        emit_u8(b, (uint8_t)(0xC0 | (x86_reg << 3) | x86_reg));
    }
    emit_u8(b, 0x48);
    emit_u8(b, 0x89);
    emit_u8(b, (uint8_t)(0x87 | (x86_reg << 3)));
    emit_u32(b, (uint32_t)disp);
}

static inline void emit_store_pc(X64Buf *b, int x86_reg)
{
    int32_t disp = (int32_t)offsetof(CPUARMState, pc);
    emit_u8(b, 0x48);
    emit_u8(b, 0x89);
    emit_u8(b, (uint8_t)(0x87 | (x86_reg << 3)));
    emit_u32(b, (uint32_t)disp);
}

/* Decode ARM64 logical bitmask immediate (AND/ORR/EOR imm) */
static bool decode_bitmask_imm(int sf, int n, int immr, int imms, uint64_t *out_mask)
{
    if (!sf && n != 0) {
        return false;
    }
    int len = 31 - __builtin_clz((uint32_t)((n << 6) | (~imms & 0x3f)));
    if (len < 1) {
        return false;
    }
    int size = 1 << len;
    int levels = size - 1;
    int s = imms & levels;
    int r = immr & levels;
    if (s == levels) {
        return false;
    }
    uint64_t welem = (s == 63) ? ~0ULL : ((1ULL << (s + 1)) - 1ULL);
    if (r != 0) {
        if (size == 64) {
            welem = (welem >> r) | (welem << (64 - r));
        } else {
            uint64_t mask = (1ULL << size) - 1ULL;
            welem &= mask;
            welem = ((welem >> r) | (welem << (size - r))) & mask;
        }
    }
    uint64_t wmask = 0;
    for (int i = 0; i < (sf ? 64 : 32); i += size) {
        wmask |= (welem << i);
    }
    *out_mask = sf ? wmask : (wmask & 0xffffffffULL);
    return true;
}

static bool fastjit_compile_insns(const uint32_t *insns, int num_insns,
                                  uint64_t pc_first, bool pcrel,
                                  X64Buf *b, bool *out_backward)
{
    b->len = 0;
    b->overflow = false;
    *out_backward = false;

    /* Prologue: load R8 = entry guest PC */
    if (pcrel) {
        /* mov r8, [rdi + offsetof(CPUARMState, pc)] */
        emit_u8(b, 0x4C);
        emit_u8(b, 0x8B);
        emit_u8(b, 0x87);
        emit_u32(b, (uint32_t)offsetof(CPUARMState, pc));
    } else {
        /* movabs r8, pc_first */
        emit_u8(b, 0x49);
        emit_u8(b, 0xB8);
        emit_u64(b, pc_first);
    }

    bool terminated_with_branch = false;

    for (int idx = 0; idx < num_insns; idx++) {
        uint32_t insn = insns[idx];
        bool is_last = (idx == num_insns - 1);

        /* 1. NOP or BTI hints (when btype == 0) */
        if (insn == 0xd503201fu ||
            ((insn & 0xffffff3fu) == 0xd503241fu)) {
            continue;
        }

        /* 2. MOVZ / MOVN / MOVK: (insn & 0x1f800000) == 0x12800000 */
        if ((insn & 0x1f800000u) == 0x12800000u) {
            int sf = (insn >> 31) & 1;
            int opc = (insn >> 29) & 3;
            int hw = (insn >> 21) & 3;
            uint64_t imm16 = (insn >> 5) & 0xffffu;
            int rd = insn & 0x1f;
            if (opc == 1 || (!sf && (hw & 2))) {
                return false;
            }
            int sh = hw * 16;
            if (opc == 2) { /* MOVZ */
                uint64_t val = imm16 << sh;
                if (!sf) {
                    val &= 0xffffffffULL;
                }
                emit_mov_imm64(b, X86_RAX, val);
                emit_store_gpr(b, X86_RAX, rd, false, sf);
            } else if (opc == 0) { /* MOVN */
                uint64_t val = ~(imm16 << sh);
                if (!sf) {
                    val &= 0xffffffffULL;
                }
                emit_mov_imm64(b, X86_RAX, val);
                emit_store_gpr(b, X86_RAX, rd, false, sf);
            } else { /* MOVK */
                uint64_t clr = ~(0xffffULL << sh);
                uint64_t set = imm16 << sh;
                emit_load_gpr(b, X86_RAX, rd, false, sf);
                emit_mov_imm64(b, X86_RCX, clr);
                emit_u8(b, 0x48); emit_u8(b, 0x21); emit_u8(b, 0xC8); /* and rax, rcx */
                if (set != 0) {
                    emit_mov_imm64(b, X86_RCX, set);
                    emit_u8(b, 0x48); emit_u8(b, 0x09); emit_u8(b, 0xC8); /* or rax, rcx */
                }
                emit_store_gpr(b, X86_RAX, rd, false, sf);
            }
            continue;
        }

        /* 3. ADD / SUB Immediate (non-flag-setting): (insn & 0x3f800000) == 0x11000000 */
        if ((insn & 0x3f800000u) == 0x11000000u) {
            int sf = (insn >> 31) & 1;
            int is_sub = (insn >> 30) & 1;
            int sh = (insn >> 22) & 1;
            uint32_t imm12 = (insn >> 10) & 0xfffu;
            uint32_t imm = imm12 << (sh ? 12 : 0);
            int rn = (insn >> 5) & 0x1f;
            int rd = insn & 0x1f;
            emit_load_gpr(b, X86_RAX, rn, true, sf);
            if (imm != 0) {
                if (sf) {
                    emit_u8(b, 0x48);
                }
                emit_u8(b, 0x81);
                emit_u8(b, is_sub ? 0xE8 : 0xC0); /* sub/add rax/eax, imm32 */
                emit_u32(b, imm);
            }
            emit_store_gpr(b, X86_RAX, rd, true, sf);
            continue;
        }

        /* 4. ADR / ADRP: (insn & 0x1f000000) == 0x10000000 */
        if ((insn & 0x1f000000u) == 0x10000000u) {
            int is_adrp = (insn >> 31) & 1;
            uint64_t immlo = (insn >> 29) & 3u;
            uint64_t immhi = (insn >> 5) & 0x7ffffu;
            int rd = insn & 0x1f;
            int64_t imm21 = ((int64_t)(((immhi << 2) | immlo) << 43)) >> 43;
            /* mov rax, r8 */
            emit_u8(b, 0x4C); emit_u8(b, 0x89); emit_u8(b, 0xC0);
            if (!is_adrp) {
                uint64_t rel = (uint64_t)((int64_t)(idx * 4) + imm21);
                emit_mov_imm64(b, X86_RCX, rel);
                emit_u8(b, 0x48); emit_u8(b, 0x01); emit_u8(b, 0xC8); /* add rax, rcx */
            } else {
                if (idx != 0) {
                    emit_u8(b, 0x48); emit_u8(b, 0x81); emit_u8(b, 0xC0);
                    emit_u32(b, (uint32_t)(idx * 4));
                }
                /* and rax, -4096 (0x48 0x25 0x00 0xF0 0xFF 0xFF) */
                emit_u8(b, 0x48); emit_u8(b, 0x25); emit_u32(b, 0xfffff000u);
                uint64_t page_off = (uint64_t)imm21 << 12;
                emit_mov_imm64(b, X86_RCX, page_off);
                emit_u8(b, 0x48); emit_u8(b, 0x01); emit_u8(b, 0xC8); /* add rax, rcx */
            }
            emit_store_gpr(b, X86_RAX, rd, false, 1);
            continue;
        }

        /* 5. ADD / SUB Shifted Register (non-flag-setting): (insn & 0x3f200000) == 0x0b000000 */
        if ((insn & 0x3f200000u) == 0x0b000000u) {
            int sf = (insn >> 31) & 1;
            int is_sub = (insn >> 30) & 1;
            int shift_type = (insn >> 22) & 3;
            int rm = (insn >> 16) & 0x1f;
            int imm6 = (insn >> 10) & 0x3f;
            int rn = (insn >> 5) & 0x1f;
            int rd = insn & 0x1f;
            if (shift_type == 3 || (!sf && imm6 >= 32)) {
                return false;
            }
            emit_load_gpr(b, X86_RAX, rn, false, sf);
            emit_load_gpr(b, X86_RCX, rm, false, sf);
            if (imm6 > 0) {
                if (sf) {
                    emit_u8(b, 0x48);
                }
                emit_u8(b, 0xC1);
                emit_u8(b, (shift_type == 0) ? 0xE1 : (shift_type == 1 ? 0xE9 : 0xF9));
                emit_u8(b, (uint8_t)imm6);
            }
            if (sf) {
                emit_u8(b, 0x48);
            }
            emit_u8(b, is_sub ? 0x29 : 0x01);
            emit_u8(b, 0xC8); /* sub/add rax/eax, rcx/ecx */
            emit_store_gpr(b, X86_RAX, rd, false, sf);
            continue;
        }

        /* 6. Logical Shifted Register (non-flag-setting): (insn & 0x1f000000) == 0x0a000000 */
        if ((insn & 0x1f000000u) == 0x0a000000u) {
            int sf = (insn >> 31) & 1;
            int opc = (insn >> 29) & 3;
            int shift_type = (insn >> 22) & 3;
            int n_bit = (insn >> 21) & 1;
            int rm = (insn >> 16) & 0x1f;
            int imm6 = (insn >> 10) & 0x3f;
            int rn = (insn >> 5) & 0x1f;
            int rd = insn & 0x1f;
            if (opc == 3 || (!sf && imm6 >= 32)) {
                return false;
            }
            emit_load_gpr(b, X86_RAX, rn, false, sf);
            emit_load_gpr(b, X86_RCX, rm, false, sf);
            if (imm6 > 0) {
                if (sf) {
                    emit_u8(b, 0x48);
                }
                emit_u8(b, 0xC1);
                uint8_t modrm = (shift_type == 0) ? 0xE1 :
                                (shift_type == 1) ? 0xE9 :
                                (shift_type == 2) ? 0xF9 : 0xC9;
                emit_u8(b, modrm);
                emit_u8(b, (uint8_t)imm6);
            }
            if (n_bit) {
                if (sf) {
                    emit_u8(b, 0x48);
                }
                emit_u8(b, 0xF7);
                emit_u8(b, 0xD1); /* not rcx/ecx */
            }
            if (sf) {
                emit_u8(b, 0x48);
            }
            emit_u8(b, (opc == 0) ? 0x21 : (opc == 1 ? 0x09 : 0x31));
            emit_u8(b, 0xC8);
            emit_store_gpr(b, X86_RAX, rd, false, sf);
            continue;
        }

        /* 7. Logical Immediate (AND/ORR/EOR imm, non-flag-setting): (insn & 0x1f800000) == 0x12000000 */
        if ((insn & 0x1f800000u) == 0x12000000u) {
            int sf = (insn >> 31) & 1;
            int opc = (insn >> 29) & 3;
            int n = (insn >> 22) & 1;
            int immr = (insn >> 16) & 0x3f;
            int imms = (insn >> 10) & 0x3f;
            int rn = (insn >> 5) & 0x1f;
            int rd = insn & 0x1f;
            if (opc == 3) {
                return false;
            }
            uint64_t wmask = 0;
            if (!decode_bitmask_imm(sf, n, immr, imms, &wmask)) {
                return false;
            }
            emit_load_gpr(b, X86_RAX, rn, false, sf);
            emit_mov_imm64(b, X86_RCX, wmask);
            if (sf) {
                emit_u8(b, 0x48);
            }
            emit_u8(b, (opc == 0) ? 0x21 : (opc == 1 ? 0x09 : 0x31));
            emit_u8(b, 0xC8);
            emit_store_gpr(b, X86_RAX, rd, true, sf);
            continue;
        }

        /* 8. Bitfield UBFM / SBFM: (insn & 0x1f800000) == 0x13000000 */
        if ((insn & 0x1f800000u) == 0x13000000u) {
            int sf = (insn >> 31) & 1;
            int opc = (insn >> 29) & 3;
            int n = (insn >> 22) & 1;
            int immr = (insn >> 16) & 0x3f;
            int imms = (insn >> 10) & 0x3f;
            int rn = (insn >> 5) & 0x1f;
            int rd = insn & 0x1f;
            int width_bits = sf ? 64 : 32;
            if ((opc != 0 && opc != 2) || n != sf ||
                immr >= width_bits || imms >= width_bits) {
                return false;
            }
            emit_load_gpr(b, X86_RAX, rn, false, sf);
            if (imms >= immr) {
                int w = imms - immr + 1;
                if (immr > 0) {
                    if (sf) {
                        emit_u8(b, 0x48);
                    }
                    emit_u8(b, 0xC1); emit_u8(b, 0xE8); emit_u8(b, (uint8_t)immr); /* shr rax/eax, immr */
                }
                if (opc == 2) { /* UBFM */
                    if (w < width_bits) {
                        uint64_t mask = (1ULL << w) - 1ULL;
                        emit_mov_imm64(b, X86_RCX, mask);
                        emit_u8(b, 0x48); emit_u8(b, 0x21); emit_u8(b, 0xC8);
                    }
                } else { /* SBFM: sign-extend w bits to width_bits */
                    int shift_left = 64 - w;
                    if (shift_left > 0) {
                        emit_u8(b, 0x48); emit_u8(b, 0xC1); emit_u8(b, 0xE0); emit_u8(b, (uint8_t)shift_left);
                        emit_u8(b, 0x48); emit_u8(b, 0xC1); emit_u8(b, 0xF8); emit_u8(b, (uint8_t)shift_left);
                    }
                }
            } else {
                int shift = width_bits - immr;
                int w = imms + 1;
                if (opc == 2) { /* UBFM */
                    uint64_t mask = (1ULL << w) - 1ULL;
                    emit_mov_imm64(b, X86_RCX, mask);
                    emit_u8(b, 0x48); emit_u8(b, 0x21); emit_u8(b, 0xC8);
                    if (sf) {
                        emit_u8(b, 0x48);
                    }
                    emit_u8(b, 0xC1); emit_u8(b, 0xE0); emit_u8(b, (uint8_t)shift);
                } else { /* SBFM */
                    int shift_left = 64 - w;
                    if (shift_left > 0) {
                        emit_u8(b, 0x48); emit_u8(b, 0xC1); emit_u8(b, 0xE0); emit_u8(b, (uint8_t)shift_left);
                        emit_u8(b, 0x48); emit_u8(b, 0xC1); emit_u8(b, 0xF8); emit_u8(b, (uint8_t)shift_left);
                    }
                    emit_u8(b, 0x48); emit_u8(b, 0xC1); emit_u8(b, 0xE0); emit_u8(b, (uint8_t)shift);
                }
            }
            emit_store_gpr(b, X86_RAX, rd, false, sf);
            continue;
        }

        /* 9. Variable Shifts LSLV / LSRV / ASRV / RORV: (insn & 0x7fe0f000) == 0x1ac02000 */
        if ((insn & 0x7fe0f000u) == 0x1ac02000u) {
            int sf = (insn >> 31) & 1;
            int op2 = (insn >> 10) & 3;
            int rm = (insn >> 16) & 0x1f;
            int rn = (insn >> 5) & 0x1f;
            int rd = insn & 0x1f;
            emit_load_gpr(b, X86_RAX, rn, false, sf);
            emit_load_gpr(b, X86_RCX, rm, false, sf);
            if (sf) {
                emit_u8(b, 0x48);
            }
            emit_u8(b, 0xD3);
            uint8_t modrm = (op2 == 0) ? 0xE0 :
                            (op2 == 1) ? 0xE8 :
                            (op2 == 2) ? 0xF8 : 0xC8;
            emit_u8(b, modrm);
            emit_store_gpr(b, X86_RAX, rd, false, sf);
            continue;
        }

        /* 10. MADD / MSUB: (insn & 0x7fe00000) == 0x1b000000 */
        if ((insn & 0x7fe00000u) == 0x1b000000u) {
            int sf = (insn >> 31) & 1;
            int o0 = (insn >> 15) & 1;
            int rm = (insn >> 16) & 0x1f;
            int ra = (insn >> 10) & 0x1f;
            int rn = (insn >> 5) & 0x1f;
            int rd = insn & 0x1f;
            emit_load_gpr(b, X86_RAX, rn, false, sf);
            emit_load_gpr(b, X86_RCX, rm, false, sf);
            emit_load_gpr(b, X86_RDX, ra, false, sf);
            if (sf) {
                emit_u8(b, 0x48);
            }
            emit_u8(b, 0x0F); emit_u8(b, 0xAF); emit_u8(b, 0xC1); /* imul rax/eax, rcx/ecx */
            if (o0 == 0) {
                if (sf) {
                    emit_u8(b, 0x48);
                }
                emit_u8(b, 0x01); emit_u8(b, 0xD0); /* add rax/eax, rdx/edx */
            } else {
                if (sf) {
                    emit_u8(b, 0x48);
                }
                emit_u8(b, 0x29); emit_u8(b, 0xC2); /* sub rdx/edx, rax/eax */
                if (sf) {
                    emit_u8(b, 0x48);
                }
                emit_u8(b, 0x89); emit_u8(b, 0xD0); /* mov rax/eax, rdx/edx */
            }
            emit_store_gpr(b, X86_RAX, rd, false, sf);
            continue;
        }

        /* Terminal branch instructions must be the last instruction in the TB */
        if (!is_last) {
            return false;
        }

        /* 11. Unconditional B / BL imm26: (insn & 0x7c000000) == 0x14000000 */
        if ((insn & 0x7c000000u) == 0x14000000u) {
            int is_bl = (insn >> 31) & 1;
            int64_t imm26 = ((int64_t)((uint64_t)(insn & 0x03ffffffu) << 38)) >> 36;
            if (imm26 <= 0) {
                *out_backward = true;
            }
            if (is_bl) {
                /* X30 = R8 + idx * 4 + 4 */
                emit_u8(b, 0x4C); emit_u8(b, 0x89); emit_u8(b, 0xC0); /* mov rax, r8 */
                emit_u8(b, 0x48); emit_u8(b, 0x81); emit_u8(b, 0xC0);
                emit_u32(b, (uint32_t)(idx * 4 + 4));
                emit_store_gpr(b, X86_RAX, 30, false, 1);
            }
            uint64_t total_rel = (uint64_t)((int64_t)(idx * 4) + imm26);
            emit_u8(b, 0x4C); emit_u8(b, 0x89); emit_u8(b, 0xC0); /* mov rax, r8 */
            emit_mov_imm64(b, X86_RCX, total_rel);
            emit_u8(b, 0x48); emit_u8(b, 0x01); emit_u8(b, 0xC8); /* add rax, rcx */
            emit_store_pc(b, X86_RAX);
            emit_u8(b, 0xC3); /* ret */
            terminated_with_branch = true;
            continue;
        }

        /* 12. RET Xn: (insn & 0xfffffc1f) == 0xd65f0000 */
        if ((insn & 0xfffffc1fu) == 0xd65f0000u) {
            int rn = (insn >> 5) & 0x1f;
            emit_load_gpr(b, X86_RAX, rn, false, 1);
            emit_store_pc(b, X86_RAX);
            emit_u8(b, 0xC3);
            terminated_with_branch = true;
            continue;
        }

        /* 13. CBZ / CBNZ: (insn & 0x7e000000) == 0x34000000 */
        if ((insn & 0x7e000000u) == 0x34000000u) {
            int sf = (insn >> 31) & 1;
            int is_cbnz = (insn >> 24) & 1;
            int64_t imm19 = ((int64_t)((uint64_t)((insn >> 5) & 0x7ffffu) << 45)) >> 43;
            int rt = insn & 0x1f;
            if (imm19 <= 0) {
                *out_backward = true;
            }
            uint64_t fall_rel = (uint64_t)(idx * 4 + 4);
            uint64_t taken_rel = (uint64_t)((int64_t)(idx * 4) + imm19);
            emit_load_gpr(b, X86_RAX, rt, false, sf);
            /* rcx = r8 + fall_rel */
            emit_u8(b, 0x4C); emit_u8(b, 0x89); emit_u8(b, 0xC1); /* mov rcx, r8 */
            emit_u8(b, 0x48); emit_u8(b, 0x81); emit_u8(b, 0xC1);
            emit_u32(b, (uint32_t)fall_rel);
            /* rdx = r8 + taken_rel */
            emit_u8(b, 0x4C); emit_u8(b, 0x89); emit_u8(b, 0xC2); /* mov rdx, r8 */
            emit_mov_imm64(b, X86_RSI, taken_rel);
            emit_u8(b, 0x48); emit_u8(b, 0x01); emit_u8(b, 0xF2); /* add rdx, rsi */
            /* test rax, rax; cmovz/cmovnz rcx, rdx */
            emit_u8(b, 0x48); emit_u8(b, 0x85); emit_u8(b, 0xC0);
            emit_u8(b, 0x48); emit_u8(b, 0x0F);
            emit_u8(b, is_cbnz ? 0x45 : 0x44);
            emit_u8(b, 0xCA);
            emit_store_pc(b, X86_RCX);
            emit_u8(b, 0xC3);
            terminated_with_branch = true;
            continue;
        }

        /* 14. TBZ / TBNZ: (insn & 0x7e000000) == 0x36000000 */
        if ((insn & 0x7e000000u) == 0x36000000u) {
            int bit = (((insn >> 31) & 1) << 5) | ((insn >> 19) & 0x1f);
            int is_tbnz = (insn >> 24) & 1;
            int64_t imm14 = ((int64_t)((uint64_t)((insn >> 5) & 0x3fffu) << 50)) >> 48;
            int rt = insn & 0x1f;
            if (imm14 <= 0) {
                *out_backward = true;
            }
            uint64_t fall_rel = (uint64_t)(idx * 4 + 4);
            uint64_t taken_rel = (uint64_t)((int64_t)(idx * 4) + imm14);
            emit_load_gpr(b, X86_RAX, rt, false, 1);
            /* rcx = r8 + fall_rel */
            emit_u8(b, 0x4C); emit_u8(b, 0x89); emit_u8(b, 0xC1);
            emit_u8(b, 0x48); emit_u8(b, 0x81); emit_u8(b, 0xC1);
            emit_u32(b, (uint32_t)fall_rel);
            /* rdx = r8 + taken_rel */
            emit_u8(b, 0x4C); emit_u8(b, 0x89); emit_u8(b, 0xC2);
            emit_mov_imm64(b, X86_RSI, taken_rel);
            emit_u8(b, 0x48); emit_u8(b, 0x01); emit_u8(b, 0xF2);
            if (bit > 0) {
                emit_u8(b, 0x48); emit_u8(b, 0xC1); emit_u8(b, 0xE8);
                emit_u8(b, (uint8_t)bit);
            }
            emit_u8(b, 0xA8); emit_u8(b, 0x01); /* test al, 1 */
            emit_u8(b, 0x48); emit_u8(b, 0x0F);
            emit_u8(b, is_tbnz ? 0x45 : 0x44);
            emit_u8(b, 0xCA);
            emit_store_pc(b, X86_RCX);
            emit_u8(b, 0xC3);
            terminated_with_branch = true;
            continue;
        }

        /* Instruction not supported by FastJIT -> fall back to TCG for this TB */
        return false;
    }

    if (!terminated_with_branch) {
        /* Fallthrough TB: env->pc = R8 + num_insns * 4 */
        emit_u8(b, 0x4C); emit_u8(b, 0x89); emit_u8(b, 0xC0); /* mov rax, r8 */
        emit_u8(b, 0x48); emit_u8(b, 0x81); emit_u8(b, 0xC0);
        emit_u32(b, (uint32_t)(num_insns * 4));
        emit_store_pc(b, X86_RAX);
        emit_u8(b, 0xC3);
    }

    return !b->overflow;
}

static bool fastjit_selftest(uint8_t *test_slot)
{
    /*
     * Self-test basic block:
     *   0: movz x0, #0x1234            (0xd2824680)
     *   1: movk x0, #0x5678, lsl #16   (0xf2aacf00)
     *   2: add  x1, x0, #0x10          (0x91004001)
     *   3: lsl  x2, x1, #3             (0xd37df022)
     *   4: madd x3, x0, x1, x2         (0x9b010803)
     *   5: adr  x4, #0x20              (0x10000104)
     *   6: ret                         (0xd65f03c0)
     */
    static const uint32_t test_insns[] = {
        0xd2824680u,
        0xf2aacf00u,
        0x91004001u,
        0xd37df022u,
        0x9b010803u,
        0x10000104u,
        0xd65f03c0u,
    };
    X64Buf b;
    bool backward = false;
    if (!fastjit_compile_insns(test_insns, 7, 0xfffffe0007001000ULL, true, &b, &backward)) {
        return false;
    }
    memcpy(test_slot, b.data, b.len);
    CPUARMState *dummy_env = g_new0(CPUARMState, 1);
    dummy_env->pc = 0xfffffe0007001000ULL;
    dummy_env->xregs[30] = 0xfffffe0007009990ULL;

    fastjit_fn_t fn = (fastjit_fn_t)test_slot;
    fn(dummy_env);

    uint64_t exp_x0 = 0x56781234ULL;
    uint64_t exp_x1 = exp_x0 + 0x10ULL;
    uint64_t exp_x2 = exp_x1 << 3;
    uint64_t exp_x3 = exp_x2 + (exp_x0 * exp_x1);
    uint64_t exp_x4 = (0xfffffe0007001000ULL + 5 * 4) + 0x20ULL;
    uint64_t exp_pc = 0xfffffe0007009990ULL;

    bool ok = dummy_env->xregs[0] == exp_x0 &&
              dummy_env->xregs[1] == exp_x1 &&
              dummy_env->xregs[2] == exp_x2 &&
              dummy_env->xregs[3] == exp_x3 &&
              dummy_env->xregs[4] == exp_x4 &&
              dummy_env->pc == exp_pc;
    g_free(dummy_env);
    return ok;
}

static bool fastjit_ensure_init(void)
{
    int state = qatomic_load_acquire(&g_fastjit_init_state);
    if (likely(state == 2)) {
        return true;
    }
    if (state == -1) {
        return false;
    }
    if (qatomic_cmpxchg(&g_fastjit_init_state, 0, 1) == 0) {
        void *mem = mmap(NULL, FASTJIT_CODE_BUFFER_SIZE,
                         PROT_READ | PROT_WRITE | PROT_EXEC,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (mem == MAP_FAILED) {
            qatomic_store_release(&g_fastjit_init_state, -1);
            return false;
        }
        g_fastjit_code_buf = (uint8_t *)mem;
        g_fastjit_code_used = 256; /* reserve first 256 bytes for selftest */
        if (!fastjit_selftest(g_fastjit_code_buf)) {
            fprintf(stderr, "[FastJIT] ERROR: startup self-test failed!\n");
            fflush(stderr);
            qatomic_store_release(&g_fastjit_init_state, -1);
            return false;
        }
        fprintf(stderr,
                "[FastJIT] AArch64->x86_64 native JIT engine initialized "
                "(buffer=%u MiB, selftest=PASS)\n",
                FASTJIT_CODE_BUFFER_SIZE >> 20);
        fflush(stderr);
        qatomic_store_release(&g_fastjit_init_state, 2);
        return true;
    }
    while ((state = qatomic_load_acquire(&g_fastjit_init_state)) == 1) {
        cpu_relax();
    }
    return state == 2;
}

void fastjit_tb_start(struct TranslationBlock *tb, uint64_t pc_first,
                      int btype, bool ss_active, bool pstate_il,
                      bool gcs_en, int bt)
{
    (void)bt;
    tls_rec.tb = tb;
    tls_rec.pc_first = pc_first;
    tls_rec.count = 0;
    tls_rec.pcrel = (tb_cflags(tb) & CF_PCREL) != 0;
    uint32_t bad_cflags = CF_USE_ICOUNT | CF_SINGLE_STEP | CF_MEMI_ONLY | CF_BP_PAGE;
    tls_rec.eligible = (btype == 0 && !ss_active && !pstate_il && !gcs_en &&
                        (tb_cflags(tb) & bad_cflags) == 0);
}

void fastjit_tb_insn(struct TranslationBlock *tb, uint64_t pc, uint32_t insn)
{
    (void)pc;
    if (!tls_rec.eligible || tls_rec.tb != tb) {
        return;
    }
    if (tls_rec.count >= FASTJIT_MAX_INSNS) {
        tls_rec.eligible = false;
        return;
    }
    tls_rec.insns[tls_rec.count++] = insn;
}

void fastjit_tb_stop(struct TranslationBlock *tb, int num_insns, int is_jmp)
{
    (void)is_jmp;
    if (!tls_rec.eligible || tls_rec.tb != tb ||
        tls_rec.count != num_insns || num_insns < 1) {
        tls_rec.eligible = false;
        return;
    }
    if (!fastjit_ensure_init()) {
        tls_rec.eligible = false;
        return;
    }

    X64Buf b;
    bool backward = false;
    if (!fastjit_compile_insns(tls_rec.insns, num_insns, tls_rec.pc_first,
                               tls_rec.pcrel, &b, &backward)) {
        tls_rec.eligible = false;
        return;
    }

    uint32_t aligned = (uint32_t)((b.len + 15u) & ~15u);
    uint32_t off = qatomic_fetch_add(&g_fastjit_code_used, aligned);
    if (unlikely(off + aligned > FASTJIT_CODE_BUFFER_SIZE)) {
        tls_rec.eligible = false;
        return;
    }

    uint8_t *dst = g_fastjit_code_buf + off;
    memcpy(dst, b.data, b.len);

    uint32_t flags = FASTJIT_FLAG_COMPILED | ((uint32_t)num_insns << 16);
    if (backward) {
        flags |= FASTJIT_FLAG_BACKWARD;
    }
    tb->fastjit_flags = flags;
    qatomic_store_release(&tb->fastjit_fn, (void *)dst);
    qatomic_fetch_add(&g_fastjit_blocks_compiled, 1);
    tls_rec.eligible = false;
}

void fastjit_exec_one(void *env, struct TranslationBlock *tb)
{
    fastjit_fn_t fn = (fastjit_fn_t)qatomic_load_acquire(&tb->fastjit_fn);
    if (likely(fn != NULL)) {
        fn((CPUARMState *)env);
        uint64_t execs = qatomic_fetch_add(&g_fastjit_blocks_executed, 1) + 1;
        uint32_t n_insns = tb->fastjit_flags >> 16;
        uint64_t total_insns = qatomic_fetch_add(&g_fastjit_insns_executed, n_insns) + n_insns;
        if (unlikely((execs & 0x3fffffULL) == 0)) {
            fprintf(stderr,
                    "[FastJIT] live telemetry: compiled_blocks=%" PRIu64
                    " executed_blocks=%" PRIu64
                    " native_insns=%" PRIu64 "\n",
                    qatomic_read(&g_fastjit_blocks_compiled),
                    execs, total_insns);
            fflush(stderr);
        }
    }
}
