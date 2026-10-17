/* ORIGINAL ARCADE PC: 0x0005100A — containing gameplay per-tick update.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for 0x5100A..0x510C4.
 *
 * Ghidra's preserved function inventory incorrectly begins this body at the
 * unreachable 0x51090 label.  The raw call at 0x41F0E and contiguous 68000
 * control flow prove the true entry at 0x5100A.  This representation retains
 * all calls so the HUD ordering is auditable without expanding those callees.
 * This is an auditable reconstruction, not original Taito source. */
#include "raw_common.h"

extern uint16_t arcade_word_10c016(void);
extern void arcade_510fe(uint8_t *a5);
extern void arcade_5a502(uint8_t *a5);
extern void arcade_5a098_raw(uint8_t *a5);
extern void arcade_59f92_raw(uint8_t *a5);
extern void arcade_5126e(uint8_t *a5);
extern void arcade_52bb6(uint8_t *a5);
extern void arcade_52b38(uint8_t *a5);
extern void arcade_52b4a(uint8_t *a5);
extern void arcade_54a2c(uint8_t *a5);
extern void arcade_5121a(uint8_t *a5);
extern void arcade_5132a(uint8_t *a5);
extern void arcade_52732(uint8_t *a5);
extern void arcade_55650(uint8_t *a5);
extern void arcade_55ad6(uint8_t *a5);
extern void arcade_59de8(uint8_t *a5);
extern void arcade_512c8(uint8_t *a5);
extern void arcade_5a29c(uint8_t *a5);
extern void arcade_596f4(uint8_t *a5);
extern void arcade_51156(uint8_t *a5);
extern void arcade_5122a(uint8_t *a5);

void arcade_5100a(uint8_t *a5)
{
    if (W(a5, 0x13e2) == 1) return;
    if (W(a5, 0x1260) != 0) {
        W(a5, 0x1260)--;
        return;
    }

    W(a5, 0x1260) = 0;
    arcade_510fe(a5);
    W(a5, 0x137a) = arcade_word_10c016();
    if (W(a5, 0x0044) != 0) W(a5, 0x013a) = 0x3000;
    if (W(a5, 0x0034) == 0) arcade_5a502(a5);

    arcade_5a098_raw(a5);        /* 0x51054: energy/status first */
    W(a5, 0x12fc) = 0x00ff;      /* 0x5105A: after its refresh test */
    arcade_59f92_raw(a5);        /* 0x51060: four independent icons */

    arcade_5126e(a5);
    arcade_52bb6(a5);
    arcade_52b38(a5);
    arcade_52b4a(a5);
    arcade_54a2c(a5);
    arcade_5121a(a5);
    arcade_5132a(a5);
    /* Preserve the instruction at 0x51090 while making its entry-unreachable
     * status from 0x5100A explicit: 0x5108C always branches to 0x51096. */
    if (0) arcade_52732(a5);
    arcade_55650(a5);
    arcade_55ad6(a5);
    arcade_59de8(a5);
    arcade_512c8(a5);
    arcade_5a29c(a5);
    arcade_596f4(a5);
    arcade_51156(a5);
    arcade_5122a(a5);            /* may conditionally call clear 0x59F5E */
    W(a5, 0x1308)++;
}
