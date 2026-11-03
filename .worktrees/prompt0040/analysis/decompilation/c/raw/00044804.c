/* ORIGINAL ARCADE PC: 0x00044804 enemy damage accumulator / lethal transition.
 * RECONSTRUCTED_FROM_68000. COMPLETE.  NOT original Taito source.
 *
 * This routine is called by the player-vs-actor collision manager.  It is not
 * a death-animation completion stepper: it applies 1/2/3 damage according to
 * A5+0x1310, compares accumulated +0x3C against threshold +0x3A, and starts
 * state 0x0F immediately on lethal damage.  rec_type 8/9 additionally starts
 * the fixed paired Flying-Demon body at A5+0x508; rec_type 11 shares the score
 * branch.  Build 0386 rebases the Genesis copy of the absolute body address.
 */
#include "raw_common.h"

extern void arcade_3a0ec(uint8_t sfx);
extern void arcade_3b726(uint16_t value);
extern void arcade_448b2(uint8_t *r);

void arcade_44804(uint8_t *r, uint8_t *a5){
    B(r,0x3d)=0x10;
    uint8_t damage=1;
    if(W(a5,0x1310)!=2){ damage=2; if(W(a5,0x1310)!=4) damage=3; }
    B(r,0x3c)=(uint8_t)(B(r,0x3c)+damage);
    if(B(r,0x3c)<B(r,0x3a)){
        uint8_t cue=(uint8_t)(7+(B(r,0x3e)!=2));
        arcade_3a0ec(cue);
        if(W(a5,0x0214)<9) B(r,0x747)=1;
        return;
    }

    arcade_448b2(r);                   /* lethal: state 0x0F now */
    if(W(a5,0x0214)<0x12 || B(r,0x06)==11){
        arcade_3b726(W(r,0x2c));
        if(W(a5,0x140c)==1) arcade_3b726(W(r,0x2c));
    }
    if(B(r,0x06)==8 || B(r,0x06)==9){
        uint8_t *body=a5+0x0508;       /* arcade absolute 0x10C508 */
        B(body,0x3d)=1;
        arcade_448b2(body);            /* paired body also enters state 0x0F */
        W(r,0x1a)=(uint16_t)(W(r,0x1a)-0x10);
    }
}
