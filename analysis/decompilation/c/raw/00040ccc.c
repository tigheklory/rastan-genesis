/* ORIGINAL ARCADE PC: 0x00040CCC state 0x0F. RECONSTRUCTED_FROM_68000. COMPLETE.
 * Three sub-behaviours selected by mode +0x03 and the child/component flag +0x39:
 *   +0x03 != 0            -> 0x40E0E "alt": preserve base, sfx 0x17 at +0x08==1, anim 0x70+n,
 *                           self-limited at +0x08>=4 (0x40E8E).
 *   +0x03 == 0, +0x39 !=0 -> 0x40DD8 BURST/IMPACT-EFFECT CHILD (H16): sel 0, base 0x0275, expanding
 *                           anim 0x9D/0x9E/0x9F/0xA0 (6/8/9/10 pieces), SELF-RETIRES at +0x08>=4.
 *   else                  -> ordinary enemy death: base 0x0A73, compositor 2, selectors
 *                           0x0D/0x0C/0x0B/0x0C/0x0D/0x0E/0x0F/0x10/0x11/0x12.
 *                           At phase 10 the SAME actor becomes family 12; +0x36 selects its
 *                           reward identity/value and, when nonzero and in bounds, presentation
 *                           base 0x0A5A with selector (+0x36-1)+0x13.  +0x36==0 retires it.
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
extern void arcade_40a1e(uint8_t *r);              /* schedule-preserving recycle */
extern uint8_t g_generation_013f;                   /* A5+0x013F */
static const uint8_t seq_40dce[10]={0x02,0x01,0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07};
static const uint8_t reward_identity_40c2e[17]={
    0x17,0x18,0x19,0x12,0x13,0x14,0x15,0x1d,0x1c,0x16,0x1b,0x1a,0x11,0x0d,0x0e,0x0f,0x10
};
static const uint16_t reward_value_40c40[17]={
    0x0010,0x0020,0x0030,0x0100,0x0200,0x0010,0x0020,0x0020,0x0020,
    0x0010,0x0010,0x0050,0x0030,0x0010,0x0015,0x0020,0x0025
};
void arcade_40ccc(uint8_t *r){
    if (B(r,0x03)!=0) goto alt;            /* 0x40E0E */
    if (B(r,0x39)!=0) goto b0275;          /* 0x40DD8 burst/impact child */
    if (--B(r,0x09)!=0) return;
    B(r,0x27)&=(uint8_t)~0x40; B(r,0x38)=2; W(r,0x1e)=0x0a73; B(r,0x09)=3;
    if (++B(r,0x08)>=10) goto xform;
    B(r,0x3a)=1; B(r,0x01)=(uint8_t)(seq_40dce[B(r,0x08)]+11); return;
xform: {
    uint8_t kind=B(r,0x36);
    uint8_t same_generation=1;
    if(B(r,0x753)!=g_generation_013f){
        B(r,0x753)=g_generation_013f;
        same_generation=0;
    }
    B(r,0x754)=same_generation;
    B(r,0x3e)=0x0c; B(r,0x3a)=0xff; B(r,0x37)=0; B(r,0x3d)=0;
    if(kind!=0){
        B(r,0x29)=reward_identity_40c2e[kind-1];
        W(r,0x2c)=reward_value_40c40[kind-1];
    }
    /* 0x40D64..0x40DC8: only a newly adopted generation and an on-world
     * position may survive as a reward.  The schedule constrains kind to the
     * 17-entry tables above, exactly as the original routine assumes. */
    uint16_t x=(uint16_t)(W(r,0x16)&0x01ff);
    uint16_t y=(uint16_t)(W(r,0x1a)&0x01ff);
    if(kind==0 || B(r,0x754)!=0 || B(r,0x08)>=0x80 || x>=0x0150 ||
       (y>=0x0110 && (y<0x0140 || y>=0x01c0))){
        arcade_40a1e(r); return;
    }
    B(r,0x01)=(uint8_t)((kind-1)+0x13); W(r,0x1e)=0x0a5a;
    W(r,0x1a)=(uint16_t)(W(r,0x1a)+((B(r,0x08)&2)?-0x0100:0x0100));
    return;
}
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
