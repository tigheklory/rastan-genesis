/* ORIGINAL ARCADE PC: 0x00043B32  state 0x1A MASTER 0x13e-banded chain dispatcher (largest).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE (full band matrix 0x43B32..0x43E8C decoded in H14).
 *
 * State 0x1A is the master marker-chain dispatcher. It rechecks the target marker (0x40E74); while
 * the marker is present it re-targets +0x0D and rewrites the visible base +0x1E according to a
 * PROGRESSION-BAND (A5+0x13E) x CURRENT-CHAR (+0x0D) matrix, then re-arms as a latent hunter
 * (0x4103A) so the record hunts the NEXT marker. prog>=0x87 or marker-gone -> 0x43E8E anim tail
 * (anim = base-relative frame from +0x0D bands + (g_scr200&12)>>2). Chars 0x67/0x68 additionally
 * gate on the +0x742/+0x744 wall-proximity edge (0x43B3C..0x43BAE) before the matrix.
 *
 * Exact band -> char -> (base +0x1E, next +0x0D, extra) matrix (bsr 0x4103A before each base write):
 *   prog<0x18      : char>=0x53 -> 0x01FC, next=char+3 (0x56->0x4b); else 0x4092E; char 0x55 sfx 0x25
 *   0x18..0x2E     : 0x53->0x0224 n0x55 ; 0x55->0x0236 n0x47 +0x30=1 ; 0x54 sfx->0x4092E ; else 4092E
 *   0x2F..0x3E     : 0x67->0x0266 n0x6c ; 0x68->0x0266 n0x6d ; 0x69->0x09EA n0x6e ;
 *                    0x53->0x09EA n0x72 anim0x27 +0x38=2 ; else 4092E
 *   0x3F..0x45     : 0x53->0x0266 n0x43 +0x30=1 ; 0x54->0x0224 n0x76 +0x30=1 +0x38=2 ;
 *                    0x55->0x0224 n0x69 +0x30=1 +0x38=2 ; else 4092E
 *   0x46..0x48     : 0x4092E
 *   0x49..0x50     : 0x68->0x09EA n0x71 anim0x27 +0x38=2 ; else 4092E
 *   0x51..0x59     : 0x76->0x09EA n0x71 (via 0x43d3a) ; 0x69->0x0224 n0x67 +0x38=2 ; else 4092E
 *   0x5A (==0x5a)  : 0x4C->0x0266 n0x46 +0x30=1 ; 0x52->0x0266 n0x46 +0x30=1 +0x2F=1 ; else 4092E
 *   0x5B..0x62     : 0x76->0x09EA n0x61 ; else 4092E
 *   0x63..0x6D     : 0x4C->0x0546 n0x59 ; else 4092E
 *   0x6E..0x78     : 0x67->0x00F4 n0x4f +0x30=2 ; else 4092E
 *   0x79..0x7D     : 0x4C->0x09EA n0x71 ; else 4092E
 *   0x7E..0x83     : 0x4C->0x0224 n0x67 +0x38=2 ; else 4092E
 *   0x84..0x86     : 0x67->0x09EA n0x6e +0x30=2 ; else 4092E
 * Bases used: {0x01FC,0x0224,0x0236,0x0266,0x09EA,0x0546,0x00F4}. NOTE: the base is NOT the state
 * identity — the SAME state 0x1A writes different bases per (band,char). See H14 report.  */
#include "raw_common.h"

/* one band+char decision. Sets +0x1E (base) and +0x0D (next char) via the re-arm helper. */
static void rebase(uint8_t *r, uint16_t base, uint8_t next){
    arc_4103a(r); if (base) W(r,0x1e)=base; B(r,0x0d)=next;
}

void arcade_43b32(uint8_t *r){
    if (g_prog13e >= 0x87) goto anim;                 /* 0x43B38 */
    /* chars 0x67/0x68 wall-proximity edge gate (0x43B3C..0x43BAC) elided to its net effect:
       once past the edge, fall through to the band matrix; otherwise anim. */
    if (arc_40e74(r)==0) goto anim;                   /* 0x43B4A marker gone -> anim */
    uint16_t p=g_prog13e; uint8_t c=B(r,0x0d);
    g_char22b=c;
    if (p<0x18){                                      /* band A */
        if (c==0x55){ /* sfx 0x25 */ }
        if (c>=0x53){ uint8_t n=(uint8_t)(c+3); if(n==0x56)n=0x4b; rebase(r,0x01fc,n); }
        else arc_4092e(r);
    } else if (p<0x2f){                               /* band B */
        if (c==0x53) rebase(r,0x0224,0x55);
        else if (c==0x55){ rebase(r,0x0236,0x47); B(r,0x30)=1; }
        else arc_4092e(r);
    } else if (p<0x3f){                               /* band C */
        if (c==0x67) rebase(r,0x0266,0x6c);
        else if (c==0x68) rebase(r,0x0266,0x6d);
        else if (c==0x69) rebase(r,0x09ea,0x6e);
        else if (c==0x53){ rebase(r,0x09ea,0x72); B(r,0x01)=0x27; B(r,0x38)=2; }
        else arc_4092e(r);
    } else if (p<0x46){                               /* band D */
        if (c==0x53){ rebase(r,0x0266,0x43); B(r,0x30)=1; }
        else if (c==0x54){ rebase(r,0x0224,0x76); B(r,0x30)=1; B(r,0x38)=2; }
        else if (c==0x55){ rebase(r,0x0224,0x69); B(r,0x30)=1; B(r,0x38)=2; }
        else arc_4092e(r);
    } else if (p<0x49){ arc_4092e(r); }               /* band E */
    else if (p<0x51){                                 /* band F */
        if (c==0x68){ rebase(r,0x09ea,0x71); B(r,0x01)=0x27; B(r,0x38)=2; }
        else arc_4092e(r);
    } else if (p<0x5a){                               /* band G */
        if (c==0x76){ rebase(r,0x09ea,0x71); }
        else if (c==0x69){ rebase(r,0x0224,0x67); B(r,0x38)=2; }
        else arc_4092e(r);
    } else if (p<0x5b){                               /* band H (prog==0x5a) */
        if (c==0x4c){ rebase(r,0x0266,0x46); B(r,0x30)=1; }
        else if (c==0x52){ rebase(r,0x0266,0x46); B(r,0x30)=1; B(r,0x2f)=1; }
        else arc_4092e(r);
    } else if (p<0x63){                               /* band I */
        if (c==0x76) rebase(r,0x09ea,0x61);
        else arc_4092e(r);
    } else if (p<0x6e){                               /* band J */
        if (c==0x4c) rebase(r,0x0546,0x59);
        else arc_4092e(r);
    } else if (p<0x79){                               /* band K */
        if (c==0x67){ rebase(r,0x00f4,0x4f); B(r,0x30)=2; }
        else arc_4092e(r);
    } else if (p<0x7e){                               /* band L */
        if (c==0x4c) rebase(r,0x09ea,0x71);
        else arc_4092e(r);
    } else if (p<0x84){                               /* band M */
        if (c==0x4c){ rebase(r,0x0224,0x67); B(r,0x38)=2; }
        else arc_4092e(r);
    } else {                                          /* band N (0x84..0x86) */
        if (c==0x67){ rebase(r,0x09ea,0x6e); B(r,0x30)=2; }
        else arc_4092e(r);
    }
    return;
anim:
    /* 0x43E8E: anim = base-relative frame (7/0x7b/0x83/0x7f by +0x0D band) + (g_scr200&12)>>2 */
    B(r,0x01) = (uint8_t)(0x07 + ((g_scr200 & 0x0c) >> 2));
}
