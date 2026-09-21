/* ORIGINAL ARCADE PC: 0x0004092E actor RETIRE / CLEAR primitive.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * The shared deactivation primitive (40+ callers). It fully zeroes the 0x40-byte ActorRecord via a
 * PROPAGATING word fill (0x3A2D0: word[+0]=0 then copy-forward 31 words), then zeroes a paired
 * 16-word (0x20-byte) companion block at record + delta, where delta is chosen by which actor pool
 * the record lives in:
 *     record end < 0x10C508  -> delta 0x702
 *     otherwise              -> delta 0x4E2
 * The companion block is the actor's paired render/scratch structure. Clearing +0x00 (active) makes
 * the slot immediately reusable by the occupancy scan (0x49F30). No fields are preserved: callers
 * that must keep identity (e.g. 0x40A1E recycle) save/restore around this call. */
#include "raw_common.h"

/* 0x3A2D0: movew (a0)+,(a1)+ ; dbra d0 -- propagating fill when a1=a0+2. */
extern void arcade_3a2d0(uint8_t *dst, uint8_t *src, uint16_t words);
/* Which pool region the record sits in -> companion-block byte delta (0x702 or 0x4E2).
 * Exact arcade boundaries: record-end < 0x10C508 => 0x702, else 0x4E2. */
extern uint16_t actor_companion_delta(uint8_t *record);

void arcade_4092e(uint8_t *r){
    /* zero the 0x40-byte record (propagating fill from a cleared first word) */
    W(r,0) = 0;
    arcade_3a2d0(r+2, r, 31);                 /* copy word[+0]=0 forward 31 words -> 32 words zeroed */

    uint16_t delta = actor_companion_delta(r);
    uint8_t *comp = r + delta;
    W(comp,0) = 0;
    arcade_3a2d0(comp+2, comp, 15);           /* zero 16 words (0x20 bytes) of the companion block */
}
