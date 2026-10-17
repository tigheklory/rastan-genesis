/* ORIGINAL ARCADE PC: 0x00054A40 ENEMY-CONTACT -> PLAYER-DAMAGE consumer (body-hit list A5+0x12A8).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for the 0x12A8 dispatch loop (0x54A40..0x54B1C).
 * The 68000 binary (build/maincpu.disasm.txt) is final authority.
 *
 * This is the consumer of the body-hit list produced A5-relative by 0x449B4 pass 1
 * (enemy hurtbox ∩ player body box). Each of up to 4 8-byte records is {active, type|pal,
 * X&0x1FF, Y&0x1FF}. For a live record (active==1) with type in 1..12 it dispatches a per-type
 * player-damage handler through the jump table at 0x550A8; type>12 takes the 0x54B04 arm.
 *
 * !!! GENESIS TRANSLATION DEFECT (KF-044 class). The list base is read with an ABSOLUTE LONG LEA:
 *       0x54A40:  LEA 0x0010D2A8,A0      (41F9 0010D2A8)
 *     On Genesis the arcade A5 work-RAM (0x10C000..) is rebased to 0xFF0000.., so A5+0x12A8 lives
 *     at 0x00FF12A8. The producer writes it A5-relative (correct), but THIS absolute read was left
 *     pointing at ROM (0x0010D2A8), so the consumer never sees the real hit and NO player-damage
 *     handler ever runs. The SIBLING read at 0x54B1E (LEA 0x0010D2C8 -> item events) was already
 *     rebased to 0x00FF12C8 in Build 0368; the body-hit read at 0x54A40 was missed. See
 *     docs/design/Andy_arcade_enemy_contact_player_damage_decompilation_and_repair_design.md. */
#include "raw_common.h"

extern void  arcade_550a8_dispatch(uint16_t type_index); /* jump table 0x550A8 -> per-type handler */

struct BodyHitRecord { uint16_t active; uint16_t type_pal; uint16_t x; uint16_t y; };

/* A5+0x12A8 body-hit list (absolute 0x0010D2A8 on arcade; MUST be 0x00FF12A8 on Genesis). */
extern struct BodyHitRecord g_body_hitlist_12a8[4];

void arcade_54a40_consume_body_hits(void){
    struct BodyHitRecord *a0 = g_body_hitlist_12a8;   /* 0x54A40 LEA 0x0010D2A8 (absolute) */
    for (int d4 = 0; d4 < 4; d4++, a0++){
        uint16_t active = a0->active;
        uint16_t d1 = a0->type_pal & 0x00FF;          /* type */
        /* X = a0->x & 0x1FF, Y = a0->y & 0x1FF read but only used by the handlers */
        if (active != 1) continue;                     /* 0x54A60 cmpiw #1,%d0 ; bne */
        if (d1 == 0 || d1 > 30) continue;              /* 0x54A68/0x54A70 range gate */
        if (d1 > 12){ /* 0x54B04 arm: index = (d1<<1)-1 path */ }
        /* else state-gated bookkeeping at 0x54A80.. then: */
        uint16_t idx = (d1 <= 12) ? d1 : ((uint16_t)(d1<<1)-1);
        arcade_550a8_dispatch(idx);                    /* 0x54B08 moveal #0x550A8,a1; jsr a1@(idx*4) */
    }
    /* 0x54B1E: the parallel item/weapon event list (A5+0x12C8, absolute 0x0010D2C8 -> rebased
     * 0x00FF12C8 in Build 0368) is consumed by the same function body with its own handlers. */
}
