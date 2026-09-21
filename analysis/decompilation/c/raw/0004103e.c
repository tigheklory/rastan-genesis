/* ORIGINAL ARCADE PC: 0x0004103E latent child-hunter create. RECONSTRUCTED_FROM_68000. COMPLETE. */
#include "raw_common.h"
void arcade_4103e(uint8_t *r){ B(r,0x00)=1; B(r,0x03)=1; B(r,0x04)=1; W(r,0x1c)=1; B(r,0x20)=1; W(r,0x1a)=0x180; }
