/* rastan_player_solid_object.c — Build 0366 semantic reconstruction.
 * NOT original Taito source. See raw/00044548.c and raw/00054bf8.c; the original 68000 binary is
 * final authority.
 *
 * The destructible Stage-1 cave block is actor_2c8/base 0x0179, target character 'H', state 0x1E.
 * It is not made solid by PC090OJ object RAM or by a map-cell injection. The once-per-frame actor
 * collision manager 0x449B4 routes mode actors through 0x44548. Character 'H' selects rectangle
 * index 82 from 0x44CE0: {left=-20,right=+20,top=-16,bottom=+16}. When the live actor's state is one
 * of {0x15,0x17,0x1B,0x1C,0x1E}, 0x444F8 writes a single special-contact record at A5+0x0242:
 * {active,state,live actor X,live actor Y,X extents,Y extents}. Because this is regenerated from the
 * current actor every frame and the manager clears the record before scanning, it follows scrolling
 * and disappears automatically when destruction changes/retire clears the qualifying actor state.
 *
 * Player update 0x5100A reaches the consumer at 0x54BF8. It tests the record, preserves the original
 * state-specific top/side choice, and writes response state A5+0x1312..0x1320. The Genesis port kept
 * both producer and consumer semantics, but the consumer's absolute LEA still named arcade work RAM
 * 0x0010C242. Genesis work RAM is relocated to 0x00FF0000, so Build 0366 changes only that operand to
 * 0x00FF0242. Sword damage/destruction is a separate later pass in 0x449B4 and is unchanged. */
#include "rastan_arcade_types.h"

typedef struct CaveBlockSolidRecord {
    uint16_t active, state, x, y;
    int8_t left, right, top, bottom;
} CaveBlockSolidRecord;

static const int8_t cave_block_rect_index_82[4] = {-20, 20, -16, 16};

int cave_block_state_registers_solid(const ActorRecord *a)
{
    if (!a->active || a->mode == 0 || a->target_char != 'H')
        return 0;
    return a->state == 0x15 || a->state == 0x17 || a->state == 0x1B ||
           a->state == 0x1C || a->state == 0x1E;
}

void cave_block_write_original_solid_record(const ActorRecord *a, CaveBlockSolidRecord *r)
{
    r->active = 1; r->state = a->state; r->x = a->x; r->y = a->y;
    r->left = cave_block_rect_index_82[0]; r->right = cave_block_rect_index_82[1];
    r->top = cave_block_rect_index_82[2]; r->bottom = cave_block_rect_index_82[3];
}

