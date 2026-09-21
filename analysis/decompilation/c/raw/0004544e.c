/* ORIGINAL ARCADE PC: 0x0004544E family template loader. GHIDRA_RAW(normalized). COMPLETE. */
#include "raw_common.h"
extern const uint8_t fam0_45502[],famN_45562[],bc0_454ba[],bc3_454d2[],bce_454ea[]; extern void arc_453d6(uint8_t*);
void arcade_4544e(uint8_t *r, uint8_t var752){ const uint8_t*t;
    if (B(r,0x3e)==2){ const uint8_t*tb=bc0_454ba; if(B(r,0x38)!=0){ tb=bc3_454d2; if(B(r,0x38)!=3) tb=bce_454ea; }
        t=tb+(int16_t)((uint16_t)(var752&3)<<3); }
    else { const uint8_t*tb=fam0_45502; if(var752!=0) tb=famN_45562; t=tb+(int16_t)((uint16_t)B(r,0x3e)<<3); }
    W(r,0x1e)=*(const uint16_t*)t; B(r,0x3a)=t[1]; B(r,0x01)=t[3];
    W(r,0x28)=*(const uint16_t*)(t+4); W(r,0x2c)=*(const uint16_t*)(t+6); arc_453d6(r); }
