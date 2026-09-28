/* ORIGINAL ARCADE PC: 0x00051B04 world/contact scan, plus classifier 0x51B74.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * Consumes the 27 Y/X pairs built at A5+0x1134 by 0x51AB6. */
#include "raw_common.h"

extern uint16_t g_contact_xy_1134[54];
extern uint16_t g_player_y_10c0;
extern uint16_t g_player_x_10be;
extern uint16_t g_contact_prior_13bc;
extern uint16_t g_contact_class_13be;
extern uint16_t *g_contact_match_11ac;
extern uint16_t g_contact_found_11b0;

static uint16_t abs16_51b04(uint16_t v){
    return (v & 0x8000u) ? (uint16_t)(~v + 1u) : v;
}

void arcade_51b74(uint16_t remaining){
    if (remaining <= 9) g_contact_class_13be = 1;
    else if (remaining < 19) g_contact_class_13be = 2;
    else g_contact_class_13be = 3;
}

void arcade_51b04(void){
    uint16_t *p = g_contact_xy_1134;
    uint16_t player_y = (uint16_t)(g_player_y_10c0 - 24u - 6u);
    for (uint16_t remaining = 27; remaining != 0; --remaining, p += 2){
        if (abs16_51b04((uint16_t)(p[0] + 8u - player_y)) >= 16u) continue;
        if (abs16_51b04((uint16_t)(p[1] + 8u - g_player_x_10be)) >= 24u) continue;
        arcade_51b74(remaining);
        if (g_contact_prior_13bc != g_contact_class_13be){
            g_contact_match_11ac = p;
            g_contact_found_11b0 = 1;
            return;
        }
    }
    g_contact_found_11b0 = 0x00ff;
}
