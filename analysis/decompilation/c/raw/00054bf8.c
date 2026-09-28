/* ORIGINAL ARCADE PC: 0x00054BF8 player special-solid contact consumer.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for 0x54BF8..0x54DA8.
 * The address at 0x54BF8 is an absolute arcade-work-RAM LEA, not PC090OJ hardware state:
 *     LEA 0x0010C242,A0
 * The original 68000 binary remains authoritative. */
#include <stdint.h>

typedef struct SpecialContactRecord {
    uint16_t active;
    uint16_t actor_state;
    uint16_t actor_x;
    uint16_t actor_y;
    int8_t x_left, x_right;
    int8_t y_top, y_bottom;
} SpecialContactRecord;

typedef struct PlayerSolidResponse {
    uint16_t mode_1312;
    uint16_t y_neg_1314, y_pos_1316;
    uint16_t x_neg_1318, x_pos_131a;
    int16_t prior_x_extent_131c, prior_y_extent_131e;
    uint16_t side_1320;
    uint16_t flag_13b2, flag_13b4;
} PlayerSolidResponse;

extern void arcade_54daa_normalize_state(SpecialContactRecord *r);
extern int arcade_54c12_state_in_first_table(uint16_t state);
extern int arcade_54c34_state_in_second_table(uint16_t state);

/* Direct reconstruction of the state/geometry result written by 0x54BF8..0x54D84.
 * player_x/y are A5+0x10BE/+0x10C0; player_bottom_adjust is signed A5+0x124B - 2. */
void arcade_54bf8_consume_special_contact(SpecialContactRecord *r,
                                           uint16_t player_x, uint16_t player_y,
                                           int8_t player_bottom_adjust,
                                           PlayerSolidResponse *o)
{
    if (r->active != 1) {
        o->flag_13b2 = o->flag_13b4 = 0x00FF;
        o->mode_1312 = o->side_1320 = 0x00FF;
        return;
    }

    arcade_54daa_normalize_state(r);    /* state 0x1E becomes 0x009E in rounds >=4 only */
    o->flag_13b2 = arcade_54c12_state_in_first_table(r->actor_state) ? 1 : 0x00FF;
    o->flag_13b4 = arcade_54c34_state_in_second_table(r->actor_state) ? 1 : 0x00FF;

    uint16_t actor_bottom = (uint16_t)((r->actor_y + r->y_bottom) & 0x01FF);
    uint16_t player_bottom = (uint16_t)((player_y + player_bottom_adjust - 2) & 0x01FF);
    int side_branch = (r->actor_state == 0x1B || r->actor_state == 0x1C ||
                       r->actor_state == 0x009E) && player_bottom > actor_bottom;

    if (side_branch) {                  /* 0x54D28: left/right obstruction */
        o->y_neg_1314 = o->y_pos_1316 = 0;
        if ((r->actor_x & 0x01FF) >= player_x) {
            o->x_neg_1318 = 0; o->x_pos_131a = 3; o->side_1320 = 2;
        } else {
            o->x_neg_1318 = 3; o->x_pos_131a = 0; o->side_1320 = 3;
        }
        return;
    }

    if (o->mode_1312 == 1) {            /* 0x54C9C: preserve delta from previous extents */
        if (r->x_left <= o->prior_x_extent_131c) {
            o->x_pos_131a = (uint16_t)(o->prior_x_extent_131c - r->x_left); o->x_neg_1318 = 0;
        } else {
            o->x_neg_1318 = (uint16_t)(r->x_left - o->prior_x_extent_131c); o->x_pos_131a = 0;
        }
        if (r->y_top <= o->prior_y_extent_131e) {
            o->y_neg_1314 = (uint16_t)(o->prior_y_extent_131e - r->y_top); o->y_pos_1316 = 0;
        } else {
            o->y_pos_1316 = (uint16_t)(r->y_top - o->prior_y_extent_131e); o->y_neg_1314 = 0;
        }
    } else {
        o->x_neg_1318 = o->x_pos_131a = o->y_neg_1314 = o->y_pos_1316 = 0;
    }
    o->prior_x_extent_131c = r->x_left;
    o->prior_y_extent_131e = r->y_top;
    o->mode_1312 = 1;
    o->side_1320 = 0x00FF;
}

