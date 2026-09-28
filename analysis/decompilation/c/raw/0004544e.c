/* ORIGINAL ARCADE PC: 0x0004544E family/variant TEMPLATE loader (+ family-2 branch 0x45494).
 * GHIDRA_RAW(normalized) + H15 variant-source correction. Status: COMPLETE.
 *
 * Selects a per-actor template row and applies it. The row source depends on family +0x3E and the
 * PARALLEL variant byte +0x752 (read directly as a4@(0x752); H15: it is NOT an argument):
 *   family != 2 (0x45456..0x4546C): table 0x45502 (variant +0x752 == 0) or 0x45562 (variant != 0);
 *                                   row = table + family(+0x3E)*8
 *   family == 2 (branch 0x45494):   table by +0x38 compositor -> 0x454BA (0) / 0x454D2 (3) /
 *                                   0x454EA (else); row = table + variant(+0x752)*8
 * Shared apply tail 0x4546E:  +0x1E = row[0..1] (base) ; +0x3A = row[2] ; +0x01 = row[3] (anim) ;
 *                             +0x28 = row[4..5] ; +0x2C = row[6..7] ; then 0x453D6.
 *
 * H15 NOTE: 0x45494 has no independent caller -- it is the family-2 fall-in of 0x4544E (beqs at
 * 0x45454) and shares the 0x4546E tail; it is represented here as the family==2 path (same PC file).
 * The variant +0x752 is written once at creation (0x4A086 = schedule e[2]>>4) and survives clears. */
#include "raw_common.h"
extern const uint8_t fam0_45502[],famN_45562[],bc0_454ba[],bc3_454d2[],bce_454ea[]; extern void arc_453d6(uint8_t*);

void arcade_4544e(uint8_t *r){ const uint8_t*t; uint8_t var=B(r,0x752);   /* a4@(0x752) */
    if (B(r,0x3e)==2){                                   /* 0x45494 family-2 branch */
        const uint8_t*tb=bc0_454ba; if(B(r,0x38)!=0){ tb=bc3_454d2; if(B(r,0x38)!=3) tb=bce_454ea; }
        t=tb+(int16_t)((uint16_t)var<<3); }              /* row = table + variant*8 */
    else { const uint8_t*tb=fam0_45502; if(var!=0) tb=famN_45562; t=tb+(int16_t)((uint16_t)B(r,0x3e)<<3); }
    W(r,0x1e)=*(const uint16_t*)t; B(r,0x3a)=t[1]; B(r,0x01)=t[3];      /* 0x4546E apply tail */
    W(r,0x28)=*(const uint16_t*)(t+4); W(r,0x2c)=*(const uint16_t*)(t+6); arc_453d6(r); }
