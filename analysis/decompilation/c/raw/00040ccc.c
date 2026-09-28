/* ORIGINAL ARCADE PC: 0x00040CCC state 0x0F. RECONSTRUCTED_FROM_68000. COMPLETE.
 * Three sub-behaviours selected by mode +0x03 and the child/component flag +0x39:
 *   +0x03 != 0            -> 0x40E0E "alt": preserve base, sfx 0x17 at +0x08==1, anim 0x70+n,
 *                           self-limited at +0x08>=4 (0x40E8E).
 *   +0x03 == 0, +0x39 !=0 -> 0x40DD8 BURST/IMPACT-EFFECT CHILD (H16): sel 0, base 0x0275, expanding
 *                           anim 0x9E/0x9F/0xA0 (8/9/10 pieces), SELF-RETIRES at +0x08>=4 (0x4092E).
 *   else (armored man)    -> base 0x0A73 sword -> 0x0A5A ball&chain at +0x08>=10; family->0x0C; comp2.
 *
 * H16: the +0x39 path is the identity of the Round-1 marker-0x4D burst children. They are activated
 * by 0x43ECC(state 0x1B)->0x43F4E/0x43F52->0x447F0->0x448B2 (which set +0x39=1 and state 0x0F). Their
 * visible identity is ASSIGNED HERE (base 0x0275 short-lived expanding burst effect, palette line 0
 * via +0x27=0 -> control nibble), NOT inherited from the preloaded pool slot. Each activated slot is
 * an independent transient effect that self-retires in ~4 frames; they are NOT five persistent
 * enemies and NOT a composite. See docs/design/Andy_h16_round1_burst_spawner_child_identity.md. */
#include "raw_common.h"
extern void arc_3a0ec(uint8_t sfx);
extern void arcade_4092e(uint8_t *r);              /* retire/clear */
static const uint8_t seq_40dce[10]={0x02,0x01,0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07};
void arcade_40ccc(uint8_t *r){
    if (B(r,0x03)!=0) goto alt;            /* 0x40E0E */
    if (B(r,0x39)!=0) goto b0275;          /* 0x40DD8 burst/impact child */
    if (--B(r,0x09)!=0) return;
    B(r,0x27)&=(uint8_t)~0x40; B(r,0x38)=2; W(r,0x1e)=0x0a73; B(r,0x09)=3;
    if (++B(r,0x08)>=10) goto xform;
    B(r,0x3a)=1; B(r,0x01)=(uint8_t)(seq_40dce[B(r,0x08)]+11); return;
xform: B(r,0x3e)=0x0c; B(r,0x3a)=0xff; B(r,0x37)=0; B(r,0x3d)=0; W(r,0x1e)=0x0a5a; return;
b0275:                                     /* 0x40DD8: burst/impact-effect child */
    if (--B(r,0x09)!=0) return;            /* frame gate */
    B(r,0x38)=0; W(r,0x1e)=0x0275; B(r,0x09)=1;   /* sel 0, base 0x0275 effect */
    if (++B(r,0x08)>=4){ arcade_4092e(r); return; }   /* 0x40E08 self-retire */
    B(r,0x01)=(uint8_t)(B(r,0x08)+0x9d); return;      /* expanding frames 0x9E..0xA0 */
alt:                                       /* 0x40E0E: +0x03 alt short-lived path */
    if (--B(r,0x09)!=0) return; B(r,0x09)=6;
    if (++B(r,0x08)==1) arc_3a0ec(0x17);
    if (B(r,0x08)<4) B(r,0x01)=(uint8_t)(B(r,0x08)+0x70);   /* +0x08>=4 -> 0x40E8E */
}
