/* ORIGINAL ARCADE PC: 0x00042E38 moving rec_type actor: animate + move + CONTACT.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * A variant of the 0x3CEB0 core (same frame timing / velocity table / band select) specialised for
 * moving rec_type actors (projectiles / thrown objects / low-rec_type enemies), with a contact tail:
 *   - frame timing identical to 0x3CEB0 (mid-frame -> rts; boundary -> advance via 0x3CF40 + apply
 *     via 0x3CF52 + reload +0x12 from +0x10/+0x11 by the 14-frame band);
 *   - motion gated by +0x26 (frozen flag): if 0, +0x16 += +0x14 (vx), +0x1A += +0x18 (vy);
 *   - CONTACT: for rec_type (+0x06) < 5, probe the collision grid (0x53A2E) at the new (X,Y); if the
 *     cell's low byte bit0 is set (solid) call 0x447F0 -> impact (state 0x0F + sfx 0x10).
 * Now COMPLETE: the anim-index core (0x3CF40/0x3CF52/0x3CEB0) it shares is fully lifted in H8. */
#include "raw_common.h"
extern uint8_t  arcade_3cf40(uint8_t d0);
extern void     arcade_3cf52(uint8_t d0, uint8_t *r);
extern uint32_t arcade_53a2e(uint16_t d1, uint16_t d2);
extern void     arcade_447f0(uint8_t *r);

static int band_hi_42e38(uint8_t f){ /* +0x10 vs +0x11 select, identical to 0x3CEB0 */
    if (f<8) return 0; if (f<22) return 1; if (f<36) return 0; if (f<50) return 1; return 0;
}

void arcade_42e38(uint8_t *r){
    if (B(r,0x07)==0){ B(r,0x09)=B(r,0x08); B(r,0x07)=1; goto apply; }
    if (--B(r,0x09)!=0) return;                    /* mid-frame: no change */
    B(r,0x09)=B(r,0x08);
    if (--B(r,0x12)!=0) goto motion;
    if (--B(r,0x0e)==0){ B(r,0x07)=0; return; }
    B(r,0x0d) = arcade_3cf40((uint8_t)(B(r,0x0f)+B(r,0x0d)));
apply:
    arcade_3cf52(B(r,0x0d), r);
    B(r,0x12) = band_hi_42e38(B(r,0x0d)) ? B(r,0x11) : B(r,0x10);
motion:
    if (B(r,0x26)==0){                             /* +0x26 frozen flag */
        W(r,0x16)=(uint16_t)(W(r,0x16)+W(r,0x14)); /* X += vx */
        W(r,0x1a)=(uint16_t)(W(r,0x1a)+W(r,0x18)); /* Y += vy */
        if (B(r,0x06)<5){                          /* collision-sensitive rec_types */
            uint16_t x=(uint16_t)(W(r,0x16)&0x1ff), y=(uint16_t)(W(r,0x1a)&0x1ff);
            uint32_t cell=arcade_53a2e(x,y);
            if (collision_word_at(cell) & 0x0100)  /* byte @cell+1 bit0 = solid */
                arcade_447f0(r);                   /* CONTACT -> impact */
        }
    }
}
