/* ORIGINAL ARCADE PC: 0x00044548 (internal mode!=0 arm of collision manager 0x449B4).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for the target-character selector, table-82
 * rectangle load, qualifying-state filter at 0x444F8, and A5+0x0242 record write used by the
 * Stage-1 cave block. This is an internal control-flow entry, not a standalone RTS function.
 * The original 68000 binary remains authoritative. */
#include "raw_common.h"

typedef struct SpecialContactRecord {
    uint16_t active;       /* +0: 1 when the record is present */
    uint16_t actor_state;  /* +2 */
    uint16_t actor_x;      /* +4 */
    uint16_t actor_y;      /* +6 */
    uint16_t x_extents;    /* +8: two signed bytes {left,right} */
    uint16_t y_extents;    /* +A: two signed bytes {top,bottom} */
} SpecialContactRecord;

extern const uint8_t target_char_rect_index_44582[];
extern const int8_t actor_rect_table_44ce0[][4];

/* Byte-faithful semantic of 0x44548 -> 0x4463A/0x4461C for target 'H'. */
int arcade_44548_select_mode_actor_rect(uint8_t *actor, int8_t out_rect[4])
{
    uint8_t selector = target_char_rect_index_44582[(uint8_t)(B(actor, 0x0D) - 0x43)];

    if (B(actor, 0x38) != 2 && selector == 0)
        return 0;                       /* 0x4455E -> 0x44A5C */

    if (selector != 0x52)
        return 0;                       /* other proven arms stay in the containing manager */

    /* 0x4463A..0x44644 chooses d3=0x52; 0x4461C loads table index 82. */
    for (unsigned i = 0; i != 4; ++i)
        out_rect[i] = actor_rect_table_44ce0[82][i];
    return 1;
}

/* 0x444F8..0x44544. A5+0x0242 is A2 at this arm. */
int arcade_444f8_write_special_contact(uint8_t *actor,
                                        const int8_t rect[4],
                                        SpecialContactRecord *dst_a5_0242)
{
    const uint8_t state = B(actor, 0x05);
    if (!(state == 0x15 || state == 0x17 || state == 0x1B ||
          state == 0x1C || state == 0x1E))
        return 0;                       /* original continues ordinary damage scan at 0x44A26 */

    dst_a5_0242->active = 1;
    dst_a5_0242->actor_state = state;
    dst_a5_0242->actor_x = W(actor, 0x16);
    dst_a5_0242->actor_y = W(actor, 0x1A);
    dst_a5_0242->x_extents = (uint16_t)(((uint8_t)rect[0] << 8) | (uint8_t)rect[1]);
    dst_a5_0242->y_extents = (uint16_t)(((uint8_t)rect[2] << 8) | (uint8_t)rect[3]);
    return 1;                           /* original skips to 0x44A5C */
}

