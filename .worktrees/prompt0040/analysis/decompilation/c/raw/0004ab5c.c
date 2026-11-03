/* ORIGINAL ARCADE PC: 0x0004AB5C scripted-encounter dispatcher (keyed on A5+0x13E).
 * RECONSTRUCTED_FROM_68000. Status: PARTIAL (dispatch cascade proven; handler bodies not all traced;
 * historical Andy_4A000_4C700 doc marked non-exhaustive). Proven: cmpiw #N,0x13E; bcs 0x4ABD8; beq H.
 * 0x2F->0x4AE28 0x30->0x4ADDC 0x33->0x4ADAA 0x34->0x4AD7C 0x36->0x4AD5C 0x38->0x4AD2E 0x3A->0x4ACF4
 * 0x3B->0x4ACDA 0x3C->0x4AC6A 0x3D->0x4AC4E 0x40->0x4AC14 (continues). */
#include "raw_common.h"
extern void scripted_handler(uint32_t pc);
void arcade_4ab5c(void){ uint16_t d0=g_prog13e;
    switch(d0){ case 0x2f: scripted_handler(0x4ae28); break; case 0x30: scripted_handler(0x4addc); break;
    case 0x33: scripted_handler(0x4adaa); break; case 0x34: scripted_handler(0x4ad7c); break;
    case 0x36: scripted_handler(0x4ad5c); break; case 0x38: scripted_handler(0x4ad2e); break;
    case 0x3a: scripted_handler(0x4acf4); break; case 0x3b: scripted_handler(0x4acda); break;
    case 0x3c: scripted_handler(0x4ac6a); break; case 0x3d: scripted_handler(0x4ac4e); break;
    case 0x40: scripted_handler(0x4ac14); break; default: scripted_handler(0x4abd8); break; } /* PARTIAL */
}
