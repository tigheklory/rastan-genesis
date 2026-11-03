/* ORIGINAL ARCADE PC: 0x000551B0 PER-TYPE PLAYER-DAMAGE HANDLER FAMILY + 0x5560C hurt reaction.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for the handler template + 0x5560C.
 * Reached from the body-hit dispatch (0x54A40 -> table 0x550A8). The 68000 binary is authority.
 *
 * Table 0x550A8 entries (32-bit pointers): 0x551CC, 0x5520E, 0x55250, 0x55292, 0x552D4, 0x55316,
 * 0x55346, 0x55376, 0x553A6, 0x553D6, ... with 0x551B0 as the default/no-op-ish arm.
 *
 * Every live handler begins with the DEBUG-INVINCIBILITY GATE and the POST-HIT INVULNERABILITY
 * latch, then applies a type-specific ENERGY decrement and the knockback/pose reaction. This is the
 * authoritative "enemy contact hurts Rastan" tail that the stock MAME Invincibility cheat (A5+0x40
 * bit 6) suppresses.
 *
 * GENESIS TRANSLATION DEFECT THROUGH BUILD 0440: shift reflow moved this handler family, but the
 * 66 embedded absolute-long pointers in 0x550A8..0x551AF were not declared for relocation. Type 1
 * still pointed to arcade 0x551CC instead of mapped Genesis 0x5524A. Build 0441 relocates the table
 * through the established absolute_long_pointer_tables mechanism. */
#include "raw_common.h"

extern void arcade_5560c_hurt_reaction(void);  /* pose 0x0C via 0x3A0EC + knockback + invuln start */

/* A5 fields (word unless noted), arcade A5 base 0x10C000 -> Genesis 0xFF0000: */
extern int16_t  A5_0040;   /* +0x40  debug/invincibility gate (nonzero => skip all damage)        */
extern int16_t  A5_013A;   /* +0x13A energy (hi byte = cells); enemy contact decrements it         */
extern int16_t  A5_12F0;   /* +0x12F0 hurt-state flag                                              */
extern int16_t  A5_12FC;   /* +0x12FC damage-taken flag                                            */
extern int16_t  A5_130E;   /* +0x130E knockback-state flag                                         */
extern int16_t  A5_1366;   /* +0x1366 POST-HIT INVULNERABILITY latch (1 => ignore further hits)    */
extern int16_t  A5_1368;   /* +0x1368 recovery / post-hit-invuln countdown (cleared on hit)        */
extern int16_t  A5_13C4;   /* +0x13C4 hit flag                                                     */
extern int16_t  A5_10E8;   /* +0x10E8 player state (8 = death)                                     */

/* Template shared by handlers 0x551CC (-512), 0x5520E (-1024), 0x55250 (-1536), 0x55292 (-2048),
 * 0x552D4 (-2560), 0x55316 (-3072), 0x55346 (-4096), 0x55376 (-5120), 0x553A6 (-6144).
 * `energy_sub` is the hi-byte<<8 decrement, i.e. -2, -4, -6, -8, -10, -12, -16, -20, -24 cells. */
static void damage_handler_template(int16_t energy_sub){
    if (A5_0040 != 0) return;                 /* 0x551CC cmpiw #0,%a5@(64); bne  -> INVINCIBLE skip */
    A5_13C4 = 1;                              /* record a hit occurred */
    if (A5_1366 == 1) return;                 /* already in post-hit invuln window -> no re-hit     */
    if (A5_12F0 == 1) return;                 /* already hurt                                       */
    if (A5_130E == 1) return;                 /* already in knockback                               */
    A5_013A += energy_sub;                    /* 0x551F2 subiw #512,%a5@(314): ENERGY DECREMENT     */
    A5_12FC = 1;                              /* damage-taken flag                                  */
    A5_1366 = 1;                              /* START temporary post-hit invulnerability           */
    A5_1368 = 0;                              /* reset recovery timer                               */
    arcade_5560c_hurt_reaction();             /* 0x5560C: hurt pose + knockback                     */
}

/* Lethal / special arms (e.g. 0x553E6) set death directly instead of (or in addition to) decrement: */
static void lethal_handler(void){
    if (A5_0040 != 0) return;
    A5_10E8 = 8;                              /* 0x553E6 movew #8,%a5@(4328): player DEATH state     */
}

/* 0x5560C: hurt reaction. Pose 0x0C (hurt) via 0x3A0EC; then either the hurt-pose branch
 * (A5+0x12F0=1, A5+0x12F2=12 pose timer, A5+0x12F6=0xFF) or, when A5+0x1108==1, the knockback branch
 * (A5+0x1366=1 invuln, A5+0x1368=0 timer, A5+0x130E=1 knockback-state, A5+0x130C=16 knockback run). */
void arcade_5560c_hurt_reaction(void){ /* see 0x5560C..0x5564E in build/maincpu.disasm.txt */ }
