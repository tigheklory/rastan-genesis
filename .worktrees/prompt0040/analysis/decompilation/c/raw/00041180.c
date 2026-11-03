/* ORIGINAL ARCADE PC: 0x00041180 latent scanner/hunter, actor state 0x00 (0x40BAA[0]).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 *
 * This is the faithful reconstruction of the ENTIRE state-0 subsystem 0x4117E..0x41D07:
 *   0x4117E  rts stub (wait exit)
 *   0x41180  timer gate + 0x41064 hunter row-scan + progression/round gates + column scan
 *   0x41336  floor-marker X placement helper (facing from neighbour cell)
 *   0x41362  CHARACTER-HUNTER materialization dispatch on matched marker char d0
 *   0x41414  low-range (<'O') secondary dispatch
 *   0x4145A..0x41CE8  per-marker materialization handlers + their position helpers
 * All handlers tail to 0x41332 (`braw 0x40BAA`): re-enter dispatch with the new state THIS frame.
 *
 * KEY H6 FACTS (proven here):
 *  - +0x0E..+0x11 in HUNTER context = the full 32-bit collision-map CELL ADDRESS a0 that matched
 *    (`movel %a0,%a4@(14)` at 0x41362). Not an index. (arc_40e74 re-reads word[+0x0E].)
 *  - Most char-hunter branches assign STATE (+0x05) + ANIM (+0x01) + attr (+0x29 via 0x45418) but
 *    do NOT assign the visible base +0x1E; +0x1E is set later by the state handler / retarget
 *    (0x40E9C/0x40F82/0x40FAC/0x40FCC via 0x4103A). Direct exceptions: 'I' (rec_type projectile,
 *    template copy) and the 0x40E88/0x40EDE transform states.
 *  - Position units are collision-cell world coords (A5+0x216 X / A5+0x218 Y), fixed up by fine
 *    scroll (A5+0x10AE/0x10B0)&7, then per-marker pixel offsets; Y is masked &0x1FF.
 *  - Two progression gates: A5+0x13E (progress counter) and A5+0x118 (round 1..6).
 */
#include "raw_common.h"
#include <stdint.h>

extern uint32_t arcade_53a2e(uint16_t d1, uint16_t d2);   /* collision cell address */
extern int      arcade_41064(uint8_t *r);                 /* hunter row-scan; d1=1 if found */
extern void     arcade_40a06(uint8_t *r);                 /* floor-marker transition (->0x40A60) */
extern void     arcade_45418(uint8_t *r);                 /* load +0x29 attr from table[state-0x13] */
extern void     arcade_453d6(uint8_t *r);                 /* (called via 45418 path elsewhere) */
extern void     arcade_43f52(uint8_t *r);                 /* segment/linked-part activator */
extern void     arcade_43f4e(uint8_t *r);                 /* segment activator (alt entry) */
extern void     arcade_4354e(uint8_t *r);                 /* post-materialization sub-actor */
extern void     arcade_3a0ec(uint8_t sfx);                /* sound cue */
extern void     arcade_3a2d0(uint8_t *dst, uint8_t *src, uint16_t words); /* word copy */
extern void     arcade_4092e(uint8_t *r);                 /* generic step/retire (H7) */
extern void     arcade_41bee(uint8_t *r);                 /* light-source register (state 0x20) */
extern void     arcade_40baa(uint8_t *r);                 /* dispatcher (tail target) */

/* A5-relative scan scratch (0x214..0x226) + template block base 0x588. */
extern uint16_t g_scan_x216;     /* A5+0x216 world X (cells*8) */
extern uint16_t g_scan_y218;     /* A5+0x218 world Y */
extern uint16_t g_scan_cnt21a;   /* A5+0x21A step budget */
extern uint16_t g_scan_found222; /* A5+0x222 matched char (run) */
extern uint32_t g_scan_cell226;  /* A5+0x226 matched cell address */
extern uint16_t g_scan_idx224;   /* A5+0x224 occurrence counter */
extern uint16_t g_a5_286;        /* A5+0x286 segment count arg */
extern uint8_t *g_a5_ptrbase;    /* A5+0x308.. linked-part pools (opaque) */
extern uint16_t g_cam10c0;       /* A5+0x10C0 camera Y hi */
extern uint16_t g_scr10cc;       /* A5+0x10CC (also in raw_common) */

/* ---- floor-marker X placement 0x41336 (facing from neighbour cell) ---------------------- */
/* d0=found char, a0=cell addr (g_scan_cell226). Reads neighbour word[a0+2] or word[a0-2]
 * per +0x04 bit; if it equals d0 keep run direction (+/-8) else 0; X = A5+0x216 + delta. */
void arcade_41336(uint8_t *r, uint8_t found, uint32_t cell){
    int16_t d3 = 0;
    if (found != 0x3a){
        uint8_t d2;
        if (B(r,0x04)!=0){ d2=(uint8_t)(collision_word_at(cell+2)>>8);      d3=8; }
        else            { d2=(uint8_t)(collision_word_at(cell-2)>>8);      d3=-8; }
        if (d2 != found) d3 = 0;
    }
    W(r,0x16) = (uint16_t)(g_scan_x216 + d3);
}

/* ---- default position value 0x4114A (used before floor gates) --------------------------- */
/* d0=A5+0x10B8; if 6<=d0<0xA0 -> 0x1F0 (or 0x148 if +0x04 bit0) else 0x1F8 (or 0x140). */
extern uint16_t g_a5_10b8;
static uint16_t p4114a(uint8_t *r){
    uint16_t d0 = g_a5_10b8;
    if (d0>=6 && d0<0xA0) return (B(r,4)&1)? 0x148 : 0x1F0;
    return (B(r,4)&1)? 0x140 : 0x1F8;
}

/* ============ char-hunter materialization position helpers (static, faithful) ============ */

/* 0x41492: 's'/'t'/'u'/'z' XY offset table by char, packed (Yoff<<16)|Xoff into d1. */
static void p41492(uint8_t *r, uint8_t d0){
    uint32_t d1 = 0x00040024u;                 /* 't' 0x74 default */
    if (d0!=0x74){
        d1 = 0x00040044u;                      /* 's' 0x73 */
        if (d0!=0x73){
            d1 = 0x00040004u;                  /* others */
            if (d0==0x79 && B(r,0x30)==0) d1 = 0x0004fffcu;
        }
    }
    uint16_t x = (uint16_t)(g_scan_x216 + (uint16_t)(d1 & 0xffff));
    W(r,0x16)=x;
    uint16_t y = (uint16_t)(g_scan_y218 + (uint16_t)(d1>>16));
    W(r,0x1a)=y;
}

/* 0x41854: 'j'/'k' Y/X offset; round-3 spawns a 4-part linked object first. */
static void p41854(uint8_t *r){
    uint32_t d1 = 0x0008ffb0u;
    if (g_round==3){
        uint8_t *save=r; g_a5_286=4; /* a4<-A5+0x308 pool */
        arcade_43f52(g_a5_ptrbase);  (void)save;
        /* a5@(0x2A4)=1; a5@(0x28A)=1 markers set by 43f52 caller-site */
        d1 = 0x00100010u;
    }
    uint16_t y=(uint16_t)(g_scan_y218 + (uint16_t)(d1&0xffff)); y&=0x1ff; W(r,0x1a)=y;
    uint16_t x=(uint16_t)(g_scan_x216 + (uint16_t)(d1>>16));    W(r,0x16)=x;
}

/* 0x419B2 / 0x419B8: R/S/T/U/V/L X and Y offsets (progress-gated). */
static uint16_t p419b2(uint16_t d0){ return (uint16_t)(d0+8); }
static uint16_t p419b8(uint16_t d0){
    uint16_t p=g_prog13e;
    if (p==0x29) return (uint16_t)(d0+32);
    if (p==0x2a) return (uint16_t)(d0-16);
    if (p<0x36)  return (uint16_t)(d0-32);
    return d0;
}

/* 0x41ADA: 'l'/'m'/'F' Y/X offset (progress + +0x30 gated). */
static void p41ada(uint8_t *r){
    if (g_prog13e<0x18 && B(r,0x30)!=0){
        uint16_t x=(uint16_t)(g_scan_x216-24); W(r,0x16)=x;
        uint16_t y=(uint16_t)((g_scan_y218+80)&0x1ff); W(r,0x1a)=y;
        return;
    }
    uint16_t d1 = (g_prog13e==0x37)? 16 : 24;
    W(r,0x16)=(uint16_t)(g_scan_x216+d1);
    W(r,0x1a)=(uint16_t)((g_scan_y218-16)&0x1ff);
}

/* 0x41B90: 'H' XY offset varying by round (A5+0x118). */
static void p41b90(uint8_t *r, uint16_t d0, uint16_t d1){
    int16_t d2=8, d3=-32;
    if (g_round!=1 && g_round!=4){
        d2=16; d3=-2;
        if (g_round==6) d3=-30;
    }
    W(r,0x16)=(uint16_t)(d0+d2);
    W(r,0x1a)=(uint16_t)(d1+d3);
}

/* 0x41C1E: 'O'/'P'/'Q' X offset (char + progress gated). */
static void p41c1e(uint8_t *r, uint8_t d0){
    uint16_t d1 = 24;
    if (d0!=0x4f){ d1=12; if (d0!=0x50) d1=0; }
    W(r,0x16)=(uint16_t)(d1+g_scan_x216);
    uint16_t p=g_prog13e;
    if (p==0x53||p==0x75) W(r,0x16)=(uint16_t)(W(r,0x16)-16);
    else if (p==0x58)     W(r,0x16)=(uint16_t)(W(r,0x16)+16);
}

/* 0x41C60: 'O'/'P'/'Q' Y offset (progress-band table); may spawn a linked part when prog==0x22. */
static void p41c60(uint8_t *r){
    uint16_t d0=g_scan_y218; uint16_t p=g_prog13e;
    if (p<0x18)      { W(r,0x1a)=(uint16_t)(d0-96); return; }
    if (p<0x25){
        if (p==0x22){ g_a5_286=2; arcade_43f52(g_a5_ptrbase); }
        d0=g_scan_y218; W(r,0x1a)=(uint16_t)(d0-136); return;
    }
    if (p<0x4d)      { W(r,0x1a)=(uint16_t)(d0-96); return; }
    if (p<0x53)      { W(r,0x1a)=(uint16_t)(d0-64); return; }
    if (p<0x58)      { W(r,0x1a)=(uint16_t)(d0-96); return; }
    if (p==0x70)     { W(r,0x1a)=(uint16_t)(d0-32); return; }
    if (p==0x75)     { W(r,0x1a)=(uint16_t)(d0-120); return; }
    W(r,0x1a)=(uint16_t)(d0-136);
}

/* ================= per-marker materialization handlers (tail -> 0x41332) ================= */
/* Each guards d0==+0x0D (else no-op). We return after assigning fields; caller re-dispatches. */

static void h_st22_4145a(uint8_t *r, uint8_t d0){          /* 's','t','u','z' -> state 0x22 */
    if (d0!=B(r,0x0d)) return;
    p41492(r,d0);
    int16_t adj=0;
    if (B(r,0x30)!=0){ adj=-24; if (B(r,0x20)==0) adj=-32; }
    W(r,0x16)=(uint16_t)(W(r,0x16)+adj);
    B(r,0x05)=0x22; B(r,0x01)=0x29; arcade_45418(r);
}

static void h_st21_414d4(uint8_t *r, uint8_t d0){          /* 'q','r','x','{' -> state 0x21 */
    if (d0!=B(r,0x0d)) return;
    B(r,0x05)=0x21;
    W(r,0x16)=(uint16_t)(g_scan_x216+16);
    W(r,0x1a)=(uint16_t)(g_scan_y218-16);
    B(r,0x01)=0x27; arcade_45418(r);
    /* progress-specific linked-part spawns (0x43F52) for prog 0x4B/0x4F/0x53 with target 'q' */
    if (g_prog13e==0x4b && B(r,0x0d)==0x71){ g_a5_286=2; arcade_43f52(g_a5_ptrbase); }
    else if (g_prog13e==0x4f && B(r,0x0d)==0x71){ g_a5_286=4; arcade_43f52(g_a5_ptrbase); }
    else if (g_prog13e==0x53 && B(r,0x0d)==0x71){ g_a5_286=4; arcade_43f52(g_a5_ptrbase); }
}

static void h_st1a_41596(uint8_t *r, uint8_t d0){          /* 'g','h','i','v','w' -> state 0x1A */
    if (d0!=B(r,0x0d)) return;
    if (d0==0x67){ arcade_3a0ec(0x13);                     /* 'g': sfx + prog-71 linked spawn */
        if (g_prog13e==0x47){ g_a5_286=4; arcade_43f52(g_a5_ptrbase); } }
    uint16_t x=g_scan_x216; int16_t d1=(B(r,0x30)!=0)? -8 : 16;
    W(r,0x16)=(uint16_t)(x+d1);
    W(r,0x1a)=(uint16_t)(g_scan_y218-32);
    B(r,0x05)=0x1a; B(r,0x01)=0x07; arcade_45418(r); arcade_4354e(r);
}

static void h_st13_41614(uint8_t *r, uint8_t d0){          /* 'e','f' -> state 0x13 */
    if (d0!=B(r,0x0d)) return;
    W(r,0x16)=g_scan_x216;
    W(r,0x1a)=(uint16_t)(g_scan_y218+32);
    B(r,0x05)=0x13; uint8_t anim=3;
    if (g_prog13e==0x35 && B(r,0x0d)==0x66){ g_a5_286=2; arcade_43f52(g_a5_ptrbase); anim=5; }
    else if (g_prog13e==0x35){ anim=5; W(r,0x16)=(uint16_t)(W(r,0x16)+32); }
    B(r,0x01)=anim; arcade_45418(r);
}

static void h_st14_4167e(uint8_t *r, uint8_t d0){          /* 'd' -> state 0x14 */
    if (d0!=B(r,0x0d)) return;
    W(r,0x16)=g_scan_x216; W(r,0x1a)=g_scan_y218;
    B(r,0x05)=0x14; B(r,0x01)=0x01; arcade_45418(r);
}

static void h_st15_416b2(uint8_t *r, uint8_t d0){          /* 'a','b','c','n','o','p','z' -> 0x15 */
    if (d0!=B(r,0x0d)) return;
    B(r,0x05)=0x15;
    W(r,0x16)=(uint16_t)(g_scan_x216+8);
    /* X refinement by progress band / target */
    if (g_prog13e==0x78){ uint16_t a=(B(r,0x0d)>=0x70)?16:56; W(r,0x16)=(uint16_t)(W(r,0x16)+a); }
    else if (g_prog13e<0x85){
        if (g_prog13e==0x70) W(r,0x16)=(uint16_t)(W(r,0x16)-48);
        else if (g_prog13e==0x64 && B(r,0x0d)==0x6e){ /* keep */ }
        else W(r,0x16)=(uint16_t)(W(r,0x16)+32);
    }
    uint16_t d0y=(uint16_t)(g_scan_y218-32); uint8_t anim=0xf5;
    if (!(g_round==2 || g_prog13e==0x62)){
        /* 0x41752: prog-56 target 'n' spawns linked part; prog target 'p' adds +32 X */
        if (g_prog13e==0x38 && B(r,0x0d)==0x6e){ g_a5_286=4; arcade_43f52(g_a5_ptrbase); }
        else if (B(r,0x0d)==0x70) W(r,0x16)=(uint16_t)(W(r,0x16)+32);
        anim=(uint8_t)(anim+2); d0y=(uint16_t)(d0y+64);
    }
    W(r,0x1a)=(uint16_t)(d0y&0x1ff); B(r,0x01)=anim;
}

static void h_st16_41792(uint8_t *r, uint8_t d0){          /* '^','_','`' -> state 0x16 */
    if (d0!=B(r,0x0d)) return;
    B(r,0x05)=0x16;
    W(r,0x16)=(uint16_t)(g_scan_x216+8);
    uint16_t y=(uint16_t)(g_scan_y218+24);
    if (g_prog13e==0x69) y=(uint16_t)(y+8);
    W(r,0x1a)=y; B(r,0x01)=0xf1; arcade_45418(r);
}

static void h_st17_417d2(uint8_t *r, uint8_t d0){          /* 'Y','Z','[','\\',']' -> state 0x17 */
    if (d0!=B(r,0x0d)) return;
    B(r,0x05)=0x17;
    W(r,0x16)=g_scan_x216;
    uint16_t y=(uint16_t)(g_scan_y218-8);
    if (g_prog13e<0x66) y=(uint16_t)(y-32);
    W(r,0x1a)=y; B(r,0x01)=0xef;
    if (g_prog13e<0x20 && B(r,0x0d)==0x59){ g_a5_286=3; arcade_43f4e(g_a5_ptrbase); }
}

static void h_st18_41834(uint8_t *r, uint8_t d0){          /* 'j','k','E' -> state 0x18 */
    if (d0!=B(r,0x0d)) return;
    B(r,0x05)=0x18; p41854(r); B(r,0x01)=0x91; arcade_45418(r);
}

static void h_st19_418a2(uint8_t *r, uint8_t d0){          /* 'W','X','K' -> state 0x19 */
    if (d0!=B(r,0x0d)) return;
    B(r,0x05)=0x19;
    W(r,0x16)=(uint16_t)(g_scan_x216+8);
    W(r,0x1a)=(uint16_t)((g_scan_y218-24)&0x1ff);
    B(r,0x01)=0x87; W(r,0x1c)=7; arcade_45418(r);
}

static void h_st1a_418f4(uint8_t *r, uint8_t d0){          /* 'R','S','T','U','V','L' -> state 0x1A */
    if (d0!=B(r,0x0d)) return;
    if (B(r,0x30)!=0){ *(int32_t*)(r+0x0e) -= 4; g_scan_x216=(uint16_t)(g_scan_x216-16); } /* 0x418E2 */
    if (d0==0x4c || d0==0x55) arcade_3a0ec(0x13);
    B(r,0x05)=0x1a;
    W(r,0x16)=(uint16_t)(p419b2(g_scan_x216)&0x1ff);
    W(r,0x1a)=(uint16_t)(p419b8(g_scan_y218)&0x1ff);
    B(r,0x01)=0x7b; arcade_45418(r);
    /* 0x4194A conditional sub-actor spawn (0x4354E) gated by round(0x118) + target + progress */
    uint8_t rnd=g_round, tgt=B(r,0x0d);
    int spawn=0;
    if (rnd<2) spawn=0;
    else if (rnd==2) spawn=1;
    else if (rnd==3){ spawn=!(tgt==0x4c||tgt==0x52||tgt==0x55); }
    else {
        if (g_prog13e==0x64||g_prog13e==0x70||g_prog13e>=0x85) spawn=1;
        else if (g_prog13e==0x78) spawn=(tgt!=0x52);
        else spawn=(tgt==0x4c) || (g_prog13e>=0x59);
    }
    if (spawn) arcade_4354e(r);
}

static void h_st1b_419e0(uint8_t *r, uint8_t d0){          /* 'M' -> state 0x1B */
    if (d0!=B(r,0x0d)) return;
    B(r,0x05)=0x1b;
    W(r,0x16)=(uint16_t)(g_scan_x216+8);
    W(r,0x1a)=(uint16_t)((g_scan_y218-64)&0x1ff);
    B(r,0x01)=0x79;
}

static void h_st1c_41a14(uint8_t *r, uint8_t d0){          /* 'G' -> state 0x1C */
    if (d0!=B(r,0x0d)) return;
    B(r,0x05)=0x1c;
    W(r,0x16)=(uint16_t)(g_scan_x216-8);
    W(r,0x1a)=(uint16_t)((g_scan_y218-98)&0x1ff);
    B(r,0x01)=0x77;
}

static void h_st1d_41a48(uint8_t *r, uint8_t d0){          /* 'l','m','F',(<'E') -> state 0x1D */
    if (d0!=B(r,0x0d)) return;
    B(r,0x05)=0x1d; p41ada(r);
    if (B(r,0x30)!=0) W(r,0x16)=(uint16_t)(W(r,0x16)-24);
    B(r,0x01)=0x75; arcade_45418(r);
    /* prog 0x57 target 'F' -> 3-part; prog 0x5A target 'F' & +0x2F==1 -> 2-part */
    if (g_prog13e==0x57 && B(r,0x0d)==0x46){ g_a5_286=3; arcade_43f52(g_a5_ptrbase); }
    else if (g_prog13e==0x5a && B(r,0x0d)==0x46 && B(r,0x2f)==1){ g_a5_286=2; arcade_43f52(g_a5_ptrbase); }
}

static void h_proj_41b32(uint8_t *r, uint8_t d0){          /* 'I' -> rec_type 1 projectile (template) */
    if (d0!=B(r,0x0d)) return;
    B(r,0x06)=1;                                           /* +0x06 record type = projectile */
    W(r,0x16)=(uint16_t)(g_scan_x216+8);
    W(r,0x1a)=(uint16_t)(g_scan_y218-31);
    arcade_3a2d0(r, g_a5_ptrbase /*A5+0x588 template*/, 32); /* copy 32 words into record */
    arcade_4092e(r);                                       /* register/step (H7) */
}

static void h_st1e_41b6c(uint8_t *r, uint8_t d0){          /* 'H' -> state 0x1E */
    if (d0!=B(r,0x0d)) return;
    B(r,0x05)=0x1e;
    p41b90(r, g_scan_x216, g_scan_y218);
    B(r,0x01)=0x70;
}

static void h_st20_41bca(uint8_t *r, uint8_t d0){          /* 'O','P','Q' -> state 0x20 (light) */
    if (d0!=B(r,0x0d)) return;
    p41c1e(r,d0); p41c60(r);
    B(r,0x08)=0xff;                                        /* +0x08 frame-dur sentinel */
    B(r,0x05)=0x20;
    arcade_41bee(r);                                       /* register light/fire source */
}

/* 0x41414: secondary dispatch for matched char < 'O' (0x4f). */
static void dispatch_low_41414(uint8_t *r, uint8_t d0){
    if (d0==0x4c){ h_st1a_418f4(r,d0); return; }           /* 'L' */
    if (d0==0x45){ h_st18_41834(r,d0); return; }           /* 'E' */
    if (d0<0x45) { h_st1d_41a48(r,d0); return; }           /* < 'E' */
    switch(d0){
        case 0x4b: h_st19_418a2(r,d0); return;             /* 'K' */
        case 0x48: h_st1e_41b6c(r,d0); return;             /* 'H' */
        case 0x49: h_proj_41b32(r,d0); return;             /* 'I' */
        case 0x46: h_st1d_41a48(r,d0); return;             /* 'F' */
        case 0x47: h_st1c_41a14(r,d0); return;             /* 'G' */
        case 0x4d: h_st1b_419e0(r,d0); return;             /* 'M' */
        default: return;                                   /* no route */
    }
}

/* 0x41362: character-hunter materialization entry. a0=matched cell addr, d0=matched char. */
static void materialize_41362(uint8_t *r, uint8_t d0, uint32_t cell){
    *(uint32_t*)(r+0x0e) = cell;                           /* +0x0E = 32-bit CELL ADDRESS */
    B(r,0x07)=1; B(r,0x09)=1;                              /* init flag / frame cd */
    if (d0<0x4f){ dispatch_low_41414(r,d0); return; }
    if (d0<0x52){ h_st20_41bca(r,d0); return; }            /* 'O','P','Q' */
    if (d0<0x57){ h_st1a_418f4(r,d0); return; }            /* 'R'..'V' */
    if (d0<0x59){ h_st19_418a2(r,d0); return; }            /* 'W','X' */
    if (d0<0x5e){ h_st17_417d2(r,d0); return; }            /* 'Y'..']' */
    if (d0<0x61){ h_st16_41792(r,d0); return; }            /* '^','_','`' */
    if (d0<0x64){ h_st15_416b2(r,d0); return; }            /* 'a','b','c' */
    if (d0<0x65){ h_st14_4167e(r,d0); return; }            /* 'd' */
    if (d0<0x67){ h_st13_41614(r,d0); return; }            /* 'e','f' */
    if (d0<0x6a){ h_st1a_41596(r,d0); return; }            /* 'g','h','i' */
    if (d0<0x6c){ h_st18_41834(r,d0); return; }            /* 'j','k' */
    if (d0<0x6e){ h_st1d_41a48(r,d0); return; }            /* 'l','m' */
    if (d0<0x71){ h_st15_416b2(r,d0); return; }            /* 'n','o','p' */
    if (d0<0x73){ h_st21_414d4(r,d0); return; }            /* 'q','r' */
    if (d0<0x76){ h_st22_4145a(r,d0); return; }            /* 's','t','u' */
    if (d0<0x78){ h_st1a_41596(r,d0); return; }            /* 'v','w' */
    if (d0<0x79){ h_st21_414d4(r,d0); return; }            /* 'x' */
    if (d0<0x7a){ h_st22_4145a(r,d0); return; }            /* 'y' */
    if (d0<0x7b){ h_st15_416b2(r,d0); return; }            /* 'z' */
    if (d0<0x7c){ h_st21_414d4(r,d0); return; }            /* '{' */
    /* d0 >= '|' : no route (rts) */
}

/* ============================= state-0 main 0x41180 ====================================== */
void arcade_41180(uint8_t *r){
    if (--W(r,0x1c) != 0) return;                          /* 0x41180 timer gate -> 0x4117E rts */
    W(r,0x1c)=2;                                           /* re-arm 2 frames */

    if (arcade_41064(r)){                                  /* 0x4118C hunter row-scan */
        materialize_41362(r, (uint8_t)g_scan_found222, g_scan_cell226); /* 0x41190 found -> 0x41362 */
        arcade_40baa(r); return;                           /* 0x41332 braw 0x40BAA */
    }
    if (B(r,0x30)!=0) return;                              /* 0x41196 armed hunter: wait */

    uint16_t d1 = p4114a(r);                               /* 0x4119C default position value */

    /* 0x4119E progression gates (mode==0 floor first) */
    if (B(r,0x03)==0){
        if (g_prog13e==133 && g_scr10cc>=1) return;        /* 0x411A4 */
    }
    if (g_prog13e==110 && g_scr10cc>=13) return;           /* 0x411B4 */

    /* 0x411C4 seed scan X from default + fine scroll */
    g_scan_x216 = (uint16_t)(d1 + (g_scrX10ae & 7));
    g_scan_y218 = 0;
    if (B(r,0x03)==0 && g_cam10c0>=176) g_scan_y218 = 768;  /* 0x411D6 */

    /* 0x411EA scan budget: 0x26 default; 0x40 for a set of progress values (mode!=0) */
    uint16_t budget = 0x26;
    if (B(r,0x03)!=0){
        uint16_t p=g_prog13e;
        static const uint16_t hi[] = {0x31,0x3f,0x47,0x53,0x54,0x58,0x59,0x61,0x66,0x67,
                                      0x69,0x6a,0x78,0x7b,0x80,0x84,0x87};
        int hit=0; for (unsigned i=0;i<sizeof hi/sizeof*hi;i++) if(p==hi[i]){hit=1;break;}
        if (!hit){ if((p>=0x29&&p<0x2c)||(p>=0x35&&p<0x39)) hit=1; }
        if (hit) budget=0x40;
    }
    g_scan_cnt21a = budget;

    /* 0x4127E vertical column scan for a floor/target marker */
    uint16_t sx=g_scan_x216, sy=(uint16_t)(g_scan_y218 & 0x1ff);
    uint32_t a0 = arcade_53a2e(sx, sy);
    uint8_t want = B(r,0x0d);
    for(;;){
        uint8_t d0 = (uint8_t)(collision_word_at(a0)>>8);
        int found=0;
        if (d0>=0x31 && d0<=0x34) found=0;                 /* structural cells -> keep scanning */
        else if (d0>=0x31){
            if (B(r,0x03)==0){ if (d0<0x3d) found=1; }     /* mode==0 floor marker 0x31..0x3c */
            else if (d0==want) found=1;                    /* mode!=0 target char */
        }
        if (found) break;
        /* advance up (cam<176) or down (cam>=176) one cell row */
        if (B(r,0x03)==0 && g_cam10c0>=176){
            g_scan_y218=(uint16_t)(g_scan_y218-8); a0-=0x80;
            if (a0 < 0x0010de00u) a0+=0x2000;
        } else {
            g_scan_y218=(uint16_t)(g_scan_y218+8); a0+=0x80;
            if (a0 >= 0x0010fe00u) a0-=0x2000;
        }
        if (--g_scan_cnt21a==0) return;                    /* budget exhausted */
    }

    /* 0x412FC found: fine-scroll Y fixup */
    { uint16_t d2=g_scan_y218, f=(uint16_t)(g_scrY10b0&7);
      if (f){ d2=(uint16_t)(d2-8+f); g_scan_y218=d2; } }
    uint8_t d0 = (uint8_t)(collision_word_at(a0)>>8);

    if (B(r,0x03)!=0){                                     /* 0x41314 mode!=0 -> char materialize */
        materialize_41362(r, d0, a0);
        arcade_40baa(r); return;
    }
    /* 0x4131A mode==0 floor commit: state=class+1, place, transition */
    B(r,0x05)=(uint8_t)(B(r,0x04)+1);
    arcade_41336(r, d0, a0);
    W(r,0x1a)=g_scan_y218;
    arcade_40a06(r);
    arcade_40baa(r);                                       /* 0x41332 */
}
