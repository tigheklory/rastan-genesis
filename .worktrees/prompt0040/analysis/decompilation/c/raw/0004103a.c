/* ORIGINAL ARCADE PC: 0x0004103A marker consume / retarget (chain advance).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE (H7).
 * End-to-end proven now that 0x4092E is decompiled: it calls `bsr 0x4092E` (retire/clear = zero the
 * whole 0x40-byte record + its paired companion block), then FALLS THROUGH into 0x4103E which
 * RE-ARMS the freshly-cleared record as a latent hunter:
 *     +0x00=1 active, +0x03=1 mode(hunter), +0x04=1 class, +0x1C=1 timer, +0x20=1, +0x1A=0x180.
 * Because 0x4092E zeroed every field first, the re-arm produces a clean off-screen hunter; the
 * caller (0x40E9C/0x40F82/0x40FAC/0x40FCC) then writes the next base (+0x1E) and target char (+0x0D)
 * so the record hunts the NEXT marker in the chain. No dependency remains unresolved. */
#include "raw_common.h"
extern void arcade_4092e(uint8_t *r);   /* retire/clear (0x4092E) - proven in H7 */

void arcade_4103a(uint8_t *r){
    arcade_4092e(r);                     /* 0x4103A bsr 0x4092E: clear record + companion block */
    /* 0x4103E re-arm as latent hunter (identical to arcade_4103e) */
    B(r,0x00)=1;
    B(r,0x03)=1;
    B(r,0x04)=1;
    W(r,0x1c)=1;
    B(r,0x20)=1;
    W(r,0x1a)=0x0180;                    /* off-screen Y */
}
