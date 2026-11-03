/* ORIGINAL ARCADE PC: 0x00045248 parameterized latent-hunter create (18 callers). RECONSTRUCTED_FROM_68000. COMPLETE.
 * d0=variant, d1=comp idx, d2=target char, d3=base. (0x0179 passed here at 0x46758/0x4678C via d3.) */
#include "raw_common.h"
void arcade_45248(uint8_t *r, uint8_t d0, uint8_t d1, uint8_t d2, uint16_t d3){
    B(r,0x00)=1; B(r,0x03)=1; B(r,0x2f)=d0; B(r,0x04)=1; W(r,0x1c)=1; B(r,0x20)=1;
    B(r,0x21)=d1; B(r,0x0d)=d2; W(r,0x1e)=d3; W(r,0x1a)=0x180; }
