/* ORIGINAL ARCADE PC: 0x000447F0 child / impact-component ACTIVATE.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Called (a) per component by 0x43F52, (b) on collision by 0x42E38, (c) by the boss-defeat handler
 * 0x469E8. It marks the record as a live sub-component and, unless it is rec_type 7, runs 0x448B2:
 *   0x448B2 init -> +0x07=0 (re-init), +0x08=0xFF, +0x3C=0, +0x05=0x0F (state 0x0F, handler 0x40CCC),
 *                   +0x09=1, sfx 0x10.
 * So a materialized/hit actor's component becomes a STATE 0x0F actor with an impact/settle animation
 * announced by sound 0x10. rec_type 7 keeps its parent-assigned state (no 0x448B2).
 * The child's graphics base/anim/palette are supplied by the PARENT before activation (component
 * template), not by 0x447F0 -- so the visible identity is parent-defined (IDENTITY PENDING). */
#include "raw_common.h"
extern void arcade_3a0ec(uint8_t sfx);

/* 0x448B2: component (re)init to state 0x0F + impact animation + sfx 0x10. */
void arcade_448b2(uint8_t *r){
    B(r,0x07)=0;
    B(r,0x08)=0xff;
    B(r,0x3c)=0;
    B(r,0x05)=0x0f;              /* state 0x0F -> 0x40CCC handler */
    B(r,0x09)=1;
    arcade_3a0ec(0x10);          /* impact/appearance sound */
}

void arcade_447f0(uint8_t *r){
    B(r,0x3d)=1;                 /* mark active sub-component */
    if (B(r,0x06)!=7)            /* rec_type 7 keeps its own state */
        arcade_448b2(r);
}
