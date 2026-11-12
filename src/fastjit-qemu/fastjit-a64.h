/*
 * FastJIT AArch64 -> x86_64 Direct Native Basic-Block JIT Engine for QEMU
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#ifndef EXEC_FASTJIT_A64_H
#define EXEC_FASTJIT_A64_H

#include <stdint.h>
#include <stdbool.h>

struct TranslationBlock;

#define FASTJIT_FLAG_COMPILED (1u << 0)
#define FASTJIT_FLAG_BACKWARD (1u << 1)

void fastjit_tb_start(struct TranslationBlock *tb, uint64_t pc_first,
                      int btype, bool ss_active, bool pstate_il,
                      bool gcs_en, int bt);
void fastjit_tb_insn(struct TranslationBlock *tb, uint64_t pc, uint32_t insn);
void fastjit_tb_stop(struct TranslationBlock *tb, int num_insns, int is_jmp);
void fastjit_exec_one(void *env, struct TranslationBlock *tb);

#endif /* EXEC_FASTJIT_A64_H */
