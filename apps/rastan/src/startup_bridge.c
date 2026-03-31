#include "main.h"
#include "res_ui.h"
#include <string.h>

#ifndef RASTAN_ENABLE_STARTUP_HOOK
#define RASTAN_ENABLE_STARTUP_HOOK 1
#endif

const u8 *const rastan_pc090oj_genesis = rastan_pc090oj;

__attribute__((used, section(".rodata_bin")))
const uint16_t genesistan_pc080sn_tile_vram_lut[16384] = {
#include "../../../build/pc080sn_tile_vram_lut_words.inc"
};

__attribute__((used, section(".rodata_bin")))
const uint16_t genesistan_pc080sn_attr_lut[32] = {
#include "../../../build/pc080sn_attr_lut_words.inc"
};

__attribute__((used, section(".rodata_bin")))
const uint16_t genesistan_pc080sn_vram_preload[] = {
#include "../../../build/pc080sn_vram_preload_words.inc"
};

#if RASTAN_ENABLE_STARTUP_HOOK

volatile uint16_t genesistan_arcade_workram_words[0x2000]
    __attribute__((section(".bss.workram")));
volatile uint16_t genesistan_shadow_d00000_words[0x0400]
    __attribute__((section(".bss.patcher")));
volatile uint16_t genesistan_shadow_c20000_words[2]
    __attribute__((section(".bss.patcher")));
volatile uint16_t genesistan_shadow_c40000_words[2]
    __attribute__((section(".bss.patcher")));
volatile uint16_t genesistan_cwindow_null[2]
    __attribute__((section(".bss.patcher")));

volatile uint16_t genesistan_shadow_reg_c50000
    __attribute__((section(".bss.patcher")));
volatile uint16_t genesistan_shadow_reg_d01bfe
    __attribute__((section(".bss.patcher")));
volatile uint16_t genesistan_shadow_reg_350008
    __attribute__((section(".bss.patcher")));
volatile uint16_t genesistan_shadow_reg_380000
    __attribute__((section(".bss.patcher")));
volatile uint16_t genesistan_shadow_reg_3c0000
    __attribute__((section(".bss.patcher")));
volatile uint8_t genesistan_shadow_input_390001
    __attribute__((section(".bss.patcher")));
volatile uint8_t genesistan_shadow_input_390003
    __attribute__((section(".bss.patcher")));
volatile uint8_t genesistan_shadow_input_390005
    __attribute__((section(".bss.patcher")));
volatile uint8_t genesistan_shadow_input_390007
    __attribute__((section(".bss.patcher")));
volatile uint8_t genesistan_shadow_reg_3e0001
    __attribute__((section(".bss.patcher")));
volatile uint8_t genesistan_shadow_reg_3e0003
    __attribute__((section(".bss.patcher")));
volatile uint8_t genesistan_shadow_dip1
    __attribute__((section(".data.patcher"))) = GENESISTAN_DIP1_FACTORY;
volatile uint8_t genesistan_shadow_dip2
    __attribute__((section(".data.patcher"))) = GENESISTAN_DIP2_FACTORY;
volatile uint16_t genesistan_shadow_service_word
    __attribute__((section(".data.patcher"))) = GENESISTAN_SERVICE_FACTORY;
volatile uint16_t genesistan_startup_result_code
    __attribute__((section(".bss.patcher"))) = GENESISTAN_STARTUP_RESULT_NONE;
volatile uint8_t genesistan_sound_last_command
    __attribute__((section(".bss.patcher")));
volatile uint8_t genesistan_sound_last_low_nibble
    __attribute__((section(".bss.patcher")));
volatile uint8_t genesistan_sound_last_high_nibble
    __attribute__((section(".bss.patcher")));
volatile uint8_t genesistan_sound_status
    __attribute__((section(".bss.patcher")));
volatile uint16_t genesistan_sound_command_count
    __attribute__((section(".bss.patcher")));
/* Arcade A0 captured at genesistan_frontend_tick_return (Build 109). */
volatile uint32_t genesistan_arcade_last_a0
    __attribute__((section(".bss.patcher")));

/*
 * Palette ROM table (Build 113).
 * 2048 entries × 2 bytes = 4096 bytes, pre-converted to Genesis VDP format
 * (0000 BBB0 GGG0 RRR0) by the post-build patcher. Source: Taito xRGB-444.
 * Retained as fallback/debug data; Build 114 reads runtime CLCS capture.
 * Patcher fills in real values after link; declared as zero here for size.
 */
__attribute__((used, section(".rodata_bin")))
const uint16_t genesistan_palette_rom_table[2048] = {0};

/*
 * Tile cache (Build 113).
 * Maps Genesis VRAM slot → arcade PC080SN tile index.
 * 1164 slots: 20-1023 (1004 tiles) + 1280-1439 (160 tiles).
 * TILE_CACHE_EMPTY (0xFFFF) = free slot.
 */
uint16_t genesistan_tile_cache_arcade[TILE_CACHE_SLOTS]
    __attribute__((section(".bss.patcher")));
uint16_t genesistan_tile_cache_lru[TILE_CACHE_SLOTS]
    __attribute__((section(".bss.patcher")));
uint16_t genesistan_tile_cache_clock
    __attribute__((section(".bss.patcher")));

/* Captured CLCS palette writes from arcade palette RAM space (Build 141). */
uint16_t genesistan_palette_clcs[2048]
    __attribute__((section(".bss.patcher")));

/* Tilemap hook cursors (Build 114). */
uint16_t genesistan_hook_col_a
    __attribute__((section(".bss.patcher")));
uint16_t genesistan_hook_row_a
    __attribute__((section(".bss.patcher")));
uint16_t genesistan_hook_col_b
    __attribute__((section(".bss.patcher")));
uint16_t genesistan_hook_row_b
    __attribute__((section(".bss.patcher")));

static uint8_t build_player_input_byte(uint16_t state)
{
    uint8_t value = 0xFF;

    /* Arcade inputs are active-low. Keep the mapping simple and final-port-friendly. */
    if ((state & BUTTON_UP) != 0) value &= (uint8_t)~0x01;
    if ((state & BUTTON_DOWN) != 0) value &= (uint8_t)~0x02;
    if ((state & BUTTON_LEFT) != 0) value &= (uint8_t)~0x04;
    if ((state & BUTTON_RIGHT) != 0) value &= (uint8_t)~0x08;
    if ((state & BUTTON_B) != 0) value &= (uint8_t)~0x10;
    if ((state & BUTTON_C) != 0) value &= (uint8_t)~0x20;

    return value;
}

static uint8_t build_aux_input_byte(uint16_t state)
{
    uint8_t value = 0xFF;

    /*
     * The title/service-side code also probes 0x390005 bits 4..6.
     * Mirror the three Genesis face buttons into that auxiliary byte for now.
     */
    if ((state & BUTTON_B) != 0) value &= (uint8_t)~0x10;
    if ((state & BUTTON_C) != 0) value &= (uint8_t)~0x20;
    if ((state & BUTTON_A) != 0) value &= (uint8_t)~0x40;

    return value;
}

static uint8_t build_system_input_byte(uint16_t p1_state, uint16_t p2_state)
{
    uint8_t value = 0xFF;

    /* Proven from the title/front-end code: bit0=coin1, bit3=start1, bit4=start2. */
    if ((p1_state & BUTTON_A) != 0) value &= (uint8_t)~0x01;
    if ((p1_state & BUTTON_START) != 0) value &= (uint8_t)~0x08;
    if ((p2_state & BUTTON_START) != 0) value &= (uint8_t)~0x10;

    /*
     * Use an intentional combo for the service-side trigger so normal play inputs
     * do not accidentally wander into operator/test flows.
     */
    if ((p1_state & (BUTTON_A | BUTTON_B | BUTTON_C)) == (BUTTON_A | BUTTON_B | BUTTON_C))
        value &= (uint8_t)~0x04;

    return value;
}

void genesistan_refresh_arcade_inputs(void)
{
    const uint16_t p1_state = JOY_readJoypad(JOY_1);
    const uint16_t p2_state = JOY_readJoypad(JOY_2);

    genesistan_shadow_input_390001 = build_player_input_byte(p1_state);
    genesistan_shadow_input_390003 = build_player_input_byte(p2_state);
    genesistan_shadow_input_390005 = build_aux_input_byte(p1_state);
    genesistan_shadow_input_390007 = build_system_input_byte(p1_state, p2_state);
}

static void fill_words(volatile uint16_t *words, uint16_t count, uint16_t value)
{
    uint16_t i;

    for (i = 0; i < count; i++) {
        words[i] = value;
    }
}

void genesistan_reset_startup_shadows(uint8_t dip1, uint8_t dip2, uint16_t service_word)
{
    fill_words(genesistan_arcade_workram_words, 0x2000, 0);
    fill_words(genesistan_shadow_d00000_words, 0x0400, 0);
    fill_words(genesistan_shadow_c20000_words, 2, 0);
    fill_words(genesistan_shadow_c40000_words, 2, 0);
    fill_words(genesistan_cwindow_null, 2, 0);
    memset(genesistan_palette_clcs, 0, sizeof(genesistan_palette_clcs));

    genesistan_shadow_reg_c50000 = 0;
    genesistan_shadow_reg_d01bfe = 0;
    genesistan_shadow_reg_350008 = 0;
    genesistan_shadow_reg_380000 = 0;
    genesistan_shadow_reg_3c0000 = 0;
    genesistan_shadow_input_390001 = 0xFF;
    genesistan_shadow_input_390003 = 0xFF;
    genesistan_shadow_input_390005 = 0xFF;
    genesistan_shadow_input_390007 = 0xFF;
    genesistan_shadow_reg_3e0001 = 0;
    genesistan_shadow_reg_3e0003 = 0;
    genesistan_shadow_dip1 = dip1;
    genesistan_shadow_dip2 = dip2;
    genesistan_shadow_service_word = service_word;
    genesistan_startup_result_code = GENESISTAN_STARTUP_RESULT_NONE;
    genesistan_sound_last_command = 0;
    genesistan_sound_last_low_nibble = 0;
    genesistan_sound_last_high_nibble = 0;
    genesistan_sound_status = 0;
    genesistan_sound_command_count = 0;
    genesistan_hook_col_a = 0;
    genesistan_hook_row_a = 8;
    genesistan_hook_col_b = 0;
    genesistan_hook_row_b = 8;
    genesistan_refresh_arcade_inputs();
}

void genesistan_init_workram_direct(uint8_t dip1, uint8_t dip2)
{
    /*
     * Initialise genesistan_arcade_workram_words
     * to the state that startup_common would have
     * produced after completing its init sequence
     * and setting state=2, sub-state=0.
     *
     * A5 base = genesistan_arcade_workram_words
     * All offsets are byte offsets from that base.
     *
     * DIP values are active-low on the arcade
     * hardware, so invert before use.
     */
    uint8_t ndip1 = (uint8_t)~dip1;
    uint8_t ndip2 = (uint8_t)~dip2;
    uint16_t diff_idx;
    uint16_t bonus_idx;
    uint16_t mode;

    /* Difficulty: notted DIP2 bits 3:2, shifted right 1 */
    static const uint16_t diff_table[4] = {
        0x1000, 0x1500, 0x2000, 0x2500};
    /* Bonus life: notted DIP2 bits 5:4, shifted right 3 */
    static const uint16_t bonus_table[4] = {
        0x0003, 0x0004, 0x0005, 0x0006};

    /* Clear entire work RAM first */
    memset((void *)genesistan_arcade_workram_words,
           0, sizeof(genesistan_arcade_workram_words));

    /*
     * Hold the Z80 in reset to silence the sound CPU.
     * The shadow register approach from Build 97
     * never reached the actual hardware.
     * Z80_startReset() asserts /RESET and stops Z80
     * execution, eliminating the MAME buzzing.
     */
    Z80_startReset();

    /* Main state machine: state=0, sub=0, step=0 */
    genesistan_arcade_workram_words[0] = 0; /* A5@(0)  main state */
    genesistan_arcade_workram_words[1] = 0; /* A5@(2)  sub-state */
    genesistan_arcade_workram_words[2] = 0; /* A5@(4)  inner step */

    /* Coinage: factory default = 1C:1C */
    genesistan_arcade_workram_words[4] = 1; /* A5@(8)  coin1 */
    genesistan_arcade_workram_words[5] = 1; /* A5@(10) coin2 */
    genesistan_arcade_workram_words[7] = 1; /* A5@(14) */
    genesistan_arcade_workram_words[8] = 1; /* A5@(16) */

    /* Display control mirror */
    genesistan_arcade_workram_words[10] = 0x0060; /* A5@(20) */

    /* DIP mirror (notted) */
    genesistan_arcade_workram_words[12] = ndip1; /* A5@(24) */
    genesistan_arcade_workram_words[14] = ndip2; /* A5@(28) */

    /* Init flag */
    genesistan_arcade_workram_words[19] = 1; /* A5@(38) */

    /* Initial delay timer */
    genesistan_arcade_workram_words[22] = 160; /* A5@(44) = 0xA0 */

    /* Mode from DIP2 bits 1:0 */
    mode = ndip2 & 0x03;
    if (mode == 0) mode = 1;
    else if (mode == 1) mode = 0;
    genesistan_arcade_workram_words[23] = mode; /* A5@(46) */

    /* Cabinet type: DIP1 bit 0 */
    genesistan_arcade_workram_words[24] = ndip1 & 0x01; /* A5@(48) */

    /* Monitor flip: DIP1 bit 1 */
    genesistan_arcade_workram_words[25] = ndip1 & 0x02; /* A5@(50) */

    /* Bonus life from DIP2 bits 5:4 */
    bonus_idx = ((uint16_t)ndip2 & 0x30U) >> 3;
    if (bonus_idx > 3) bonus_idx = 3;
    genesistan_arcade_workram_words[27] = /* A5@(54) */
        bonus_table[bonus_idx];

    /* Difficulty from DIP2 bits 3:2 */
    diff_idx = ((uint16_t)ndip2 & 0x0CU) >> 1;
    if (diff_idx > 3) diff_idx = 3;
    genesistan_arcade_workram_words[28] = /* A5@(56) */
        diff_table[diff_idx];

    /* Competition/alt flags (0 for standard ROM) */
    genesistan_arcade_workram_words[32] = 0; /* A5@(64) */
    genesistan_arcade_workram_words[34] = 0; /* A5@(68) */

    /* Sprite init marker */
    genesistan_arcade_workram_words[37] = 0x00AA; /* A5@(74) */

    /*
     * Transition-buffer baseline (Option 2):
     * Recreate the proven non-video startup template used by 0x03A99A/0x03A9E6
     * for the first 32-word swap window consumed by 0x03A294/0x03A2B2.
     *
     * Source proof (arcade disassembly):
     * - 0x03A99A: clear transition region
     * - 0x03A9E6: seed block A (A5+0x80) from A5+0x36/A5+0x38 and bytes 0x17/0x18
     * - 0x03A294/0x03A2B2: operate on 32 words (64 bytes) per block
     */
    {
        uint8_t *workram_bytes = (uint8_t *)genesistan_arcade_workram_words;

        /* Keep first swap window deterministic in block A/B. */
        memset(workram_bytes + 0x80, 0, 0x80); /* A5+0x80..0x0FF */

        /* Block A (A5+0x80) seeded fields from proven arcade init helper. */
        genesistan_arcade_workram_words[0x80 / 2] = genesistan_arcade_workram_words[0x36 / 2];
        workram_bytes[0x97] = 1; /* A5+0x80+23 */
        workram_bytes[0x98] = 1; /* A5+0x80+24 */
        genesistan_arcade_workram_words[0xB2 / 2] = genesistan_arcade_workram_words[0x38 / 2];

        /*
         * Mirror only the first 32-word window into block B (A5+0xC0),
         * matching the exact window size used by swap helpers.
         */
        memcpy(workram_bytes + 0xC0, workram_bytes + 0x80, 0x40);
    }

    /* Title init flags */
    genesistan_arcade_workram_words[128] = 1; /* A5@(256) */
    /*
     * Keep A5@(260) clear here so the original runtime path can
     * open-gate selector seeding at 0x04527E.
     */

    /*
     * Copy 39 bytes of config data from ROM
     * table at original arcade address 0x3b0d4
     * (relocated to 0x3b2d4 in Genesis ROM)
     * to A5@(320) = workram word offset 160.
     * Cast to byte pointer for byte-accurate copy.
     */
    {
        extern const uint8_t rastan_maincpu[];
        const uint8_t *cfg_src =
            rastan_maincpu + 0x3b0d4;
        uint8_t *cfg_dst =
            (uint8_t *)genesistan_arcade_workram_words
            + 320;
        uint16_t i;
        for (i = 0; i < 39; i++)
            cfg_dst[i] = cfg_src[i];
    }

}

void genesistan_reclaim_launcher_wram(void)
{
    const uint8_t saved_dip1 = genesistan_shadow_dip1;
    const uint8_t saved_dip2 = genesistan_shadow_dip2;
    const uint16_t saved_service = genesistan_shadow_service_word;

    /*
     * Reclaim launcher-only state once we hand off to live game flow.
     * Keep DIP/service configuration intact so startup/game behavior stays stable.
     */
    memset((void *)genesistan_shadow_c20000_words, 0, sizeof(genesistan_shadow_c20000_words));
    memset((void *)genesistan_shadow_c40000_words, 0, sizeof(genesistan_shadow_c40000_words));
    memset(genesistan_tile_cache_arcade, 0xFF, sizeof(genesistan_tile_cache_arcade));
    memset(genesistan_tile_cache_lru,    0,    sizeof(genesistan_tile_cache_lru));
    genesistan_tile_cache_clock = 0;
    genesistan_startup_result_code = GENESISTAN_STARTUP_RESULT_NONE;
    genesistan_sound_last_command = 0;
    genesistan_sound_last_low_nibble = 0;
    genesistan_sound_last_high_nibble = 0;
    genesistan_sound_status = 0;
    genesistan_sound_command_count = 0;

    genesistan_shadow_dip1 = saved_dip1;
    genesistan_shadow_dip2 = saved_dip2;
    genesistan_shadow_service_word = saved_service;
}

#else

void genesistan_reset_startup_shadows(uint8_t dip1, uint8_t dip2, uint16_t service_word)
{
    (void) dip1;
    (void) dip2;
    (void) service_word;
}

void genesistan_refresh_arcade_inputs(void)
{
}

void genesistan_init_workram_direct(uint8_t dip1, uint8_t dip2)
{
    (void) dip1;
    (void) dip2;
}

void genesistan_reclaim_launcher_wram(void)
{
}

#endif
