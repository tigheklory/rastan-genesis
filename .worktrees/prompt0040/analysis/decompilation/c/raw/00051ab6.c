/* ORIGINAL ARCADE PC: 0x00051AB6 PC090OJ contact-coordinate extractor.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 *
 * A5+0x1280 is a global enable word.  The three six-byte registrations begin
 * at A5+0x1282 and contain {active.w, object_band_address.l}.  For an active
 * registration the routine copies Y@+2 and X@+6 from the first nine consecutive
 * eight-byte PC090OJ records to A5+0x1134. Inactive entries contribute nine
 * parked (0x1FF,0x1FF) pairs. */
#include "raw_common.h"

extern uint8_t  g_contact_reg_1282[18];
extern uint16_t g_contact_xy_1134[54];
extern uint16_t pc090oj_word_at(uint32_t arcade_address);

static uint32_t be32_51ab6(const uint8_t *p){
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

void arcade_51ab6(void){
    uint16_t *dst = g_contact_xy_1134;
    const uint8_t *registration = g_contact_reg_1282;
    for (unsigned source = 0; source < 3; ++source, registration += 6){
        uint16_t active = (uint16_t)((registration[0] << 8) | registration[1]);
        if (active != 1){
            for (unsigned piece = 0; piece < 9; ++piece){
                *dst++ = 0x01ff;
                *dst++ = 0x01ff;
            }
            continue;
        }
        uint32_t record = be32_51ab6(registration + 2);
        for (unsigned piece = 0; piece < 9; ++piece, record += 8){
            *dst++ = pc090oj_word_at(record + 2);       /* Y */
            *dst++ = pc090oj_word_at(record + 6);       /* X */
        }
    }
}
