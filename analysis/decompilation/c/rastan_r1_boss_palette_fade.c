/* rastan_r1_boss_palette_fade.c — maintained semantic reconstruction of
 * ORIGINAL ARCADE 0x47004/0x4703C/0x47076 and its R1 timing owner.
 * NOT original Taito source.  build/regions/maincpu.bin is final authority.
 */
#include "rastan_arcade_types.h"

/* ROM 0x46F84: result = g_boss_component_fade[source_nibble][step]. */
static const uint8_t g_boss_component_fade[16][8] = {
    {0,0,0,0,0,0,0,0}, {0,0,0,0,1,1,1,1},
    {0,0,1,1,1,2,2,2}, {0,0,1,1,2,2,3,3},
    {0,1,1,2,2,3,3,4}, {0,1,2,2,3,4,4,5},
    {0,1,2,3,4,4,5,6}, {0,1,2,3,4,5,6,7},
    {0,1,3,4,5,6,7,8}, {0,1,3,5,6,7,8,9},
    {0,1,3,5,7,8,9,10}, {0,1,3,5,7,9,10,11},
    {0,1,3,5,7,9,11,12}, {0,1,3,5,7,9,12,13},
    {0,1,3,5,7,10,12,14}, {0,1,3,5,8,11,13,15}
};

/* R1 target at ROM 0x4708C.  These are source indices 1..15; live index 0
 * is retained black at CLCS 0x2009E0. */
static const uint16_t g_r1_boss_target_0rgb[15] = {
    0x0870,0x0CC7,0x0FFF,0x07CE,0x007C,
    0x0117,0x0FF4,0x0C42,0x0900,0x0665,
    0x0545,0x0500,0x0AB9,0x0750,0x0000
};

static uint16_t boss_faded_clcs_word(uint16_t source_0rgb, unsigned step)
{
    unsigned r = g_boss_component_fade[(source_0rgb >> 8) & 15u][step];
    unsigned g = g_boss_component_fade[(source_0rgb >> 4) & 15u][step];
    unsigned b = g_boss_component_fade[source_0rgb & 15u][step];
    return (uint16_t)((b << 11) | (g << 6) | (r << 1));
}

/* Semantic output of one 0x47004 pass for Round 1. */
void r1_boss_palette_fade_render(unsigned step, uint16_t live_line_4f[16])
{
    if (step > 7) step = 7;
    live_line_4f[0] = 0; /* retained by the arcade writer, known black at entry */
    for (unsigned i = 1; i < 16; ++i)
        live_line_4f[i] = boss_faded_clcs_word(g_r1_boss_target_0rgb[i-1], step);
}

/* 0x46ED2..0x46F04: the boss actor's +0x09 counter advances the global
 * fade step every eight actor updates.  Reaching step 7 sets A5+0x272=4 and,
 * for Round 1, calls 0x457B2 to create five type-15 flying daggers. */
int r1_boss_palette_fade_tick(uint8_t *actor_counter_09, uint16_t *fade_step_0270,
                              uint16_t *boss_state_0272)
{
    *actor_counter_09 = (uint8_t)(*actor_counter_09 + 1u);
    if (*actor_counter_09 < 8u) return 0;
    *actor_counter_09 = 0;
    *fade_step_0270 = (uint16_t)(*fade_step_0270 + 1u);
    if (*fade_step_0270 < 7u) return 0;
    *boss_state_0272 = 4;
    return 1; /* original caller invokes 0x457B2 here */
}

/* Faithful later Genesis quantization: reproduce the arcade nibble trajectory
 * first, then reduce the resulting nibble to the Genesis 3-bit channel.
 * Adjacent arcade states may deliberately collapse to the same CRAM value. */
uint16_t r1_boss_faded_genesis_word(uint16_t source_0rgb, unsigned step)
{
    if (step > 7) step = 7;
    unsigned r = g_boss_component_fade[(source_0rgb >> 8) & 15u][step] >> 1;
    unsigned g = g_boss_component_fade[(source_0rgb >> 4) & 15u][step] >> 1;
    unsigned b = g_boss_component_fade[source_0rgb & 15u][step] >> 1;
    return (uint16_t)((b << 9) | (g << 5) | (r << 1));
}
