#include <genesis.h>
#include <string.h>

#include "build_info.h"
#include "main.h"
#include "res_payload.h"
#include "res_ui.h"

/* Explicitly reference SBT-linked Genesis shadow symbols used by remap rules. */
extern volatile uint16_t genesistan_shadow_reg_c50000;
extern volatile uint16_t genesistan_shadow_reg_d01bfe;

#ifndef RASTAN_ENABLE_STARTUP_HOOK
#define RASTAN_ENABLE_STARTUP_HOOK 1
#endif

#define SCREEN_W 40
#define FACTORY_DIP1 0xFE
#define FACTORY_DIP2 0xFF
#define SETTING_MENU_COUNT 8
#define MENU_COUNT 13
#define GRAPHICS_TEST_TILE_INDEX (TILE_USER_INDEX + 4)
#define PC080SN_TILE_COUNT (524288 / 32)
#define PC090OJ_TILE_COUNT (524288 / 32)
#define PC090OJ_CELL_COUNT (524288 / 128)
#define GRAPHICS_TEST_COLS_PC080SN 18
#define GRAPHICS_TEST_ROWS_PC080SN 11
#define GRAPHICS_TEST_ITEMS_PER_PAGE_PC080SN (GRAPHICS_TEST_COLS_PC080SN * GRAPHICS_TEST_ROWS_PC080SN)
#define GRAPHICS_TEST_COLS_PC090OJ 9
#define GRAPHICS_TEST_ROWS_PC090OJ 5
#define GRAPHICS_TEST_ITEMS_PER_PAGE_PC090OJ (GRAPHICS_TEST_COLS_PC090OJ * GRAPHICS_TEST_ROWS_PC090OJ)
#define GRAPHICS_TEST_MAX_VRAM_TILES GRAPHICS_TEST_ITEMS_PER_PAGE_PC080SN
#define GRAPHICS_TEST_BLANK_TILE_INDEX (GRAPHICS_TEST_TILE_INDEX + GRAPHICS_TEST_MAX_VRAM_TILES)
#define DIP_TILE_ON_INDEX TILE_USER_INDEX
#define DIP_TILE_OFF_INDEX (TILE_USER_INDEX + 2)
#define FRONTEND_RUNTIME_SPRITE_TILE_BASE 1024
#define FRONTEND_RUNTIME_MAX_SPRITES SAT_MAX_SIZE
#define FRONTEND_RUNTIME_MAX_UNIQUE_CODES 64
#define FRONTEND_RUNTIME_MAX_PALETTE_BANKS 4
/* Arcade visible height is 240; Genesis visible height is 224 in this mode. */
#define RASTAN_VERTICAL_CROP_BIAS 8

typedef enum
{
    SCREEN_CONFIG = 0,
    SCREEN_GRAPHICS_TEST,
    SCREEN_SOUND_TEST,
    SCREEN_STARTUP_PREVIEW,
    SCREEN_FRONTEND_LIVE,
} AppScreen;

typedef enum
{
    GRAPHICS_REGION_PC080SN = 0,
    GRAPHICS_REGION_PC090OJ,
} GraphicsRegion;

typedef struct
{
    u8 dip1;
    u8 dip2;
    bool valid;
} UndoState;

typedef struct
{
    const char *label;
    const char *const *values;
    const char *help_text;
    const char *switches;
    u8 value_count;
} MenuItem;

static const char *const cabinet_values[] = {"UPRIGHT", "COCKTAIL"};
static const char *const monitor_values[] = {"NORMAL", "REVERSE"};
static const char *const game_mode_values[] = {"NORMAL", "TEST"};
static const char *const coinage_values[] = {"1C 1C", "1C 2C", "2C 1C", "2C 3C"};
static const char *const difficulty_values[] = {"EASIEST", "EASY", "DIFFICULT", "HARDEST"};
static const char *const bonus_values[] = {"100K", "150K", "200K", "250K"};
static const char *const lives_values[] = {"3", "4", "5", "6"};
static const char *const continue_values[] = {"ON", "OFF"};
static const u16 rastan_font_palette[16] = {
    0x0000,
    0x0EEE,
    0x0EEE,
    0x0EEE,
    0x0EEE,
    0x0EEE,
    0x0EEE,
    0x0EEE,
    0x0EEE,
    0x0EEE,
    0x0EEE,
    0x0EEE,
    0x0EEE,
    0x0EEE,
    0x0EEE,
    0x0EEE,
};

static const u16 rastan_selected_font_palette[16] = {
    0x0000,
    0x000E,
    0x000E,
    0x000E,
    0x000E,
    0x000E,
    0x000E,
    0x000E,
    0x000E,
    0x000E,
    0x000E,
    0x000E,
    0x000E,
    0x000E,
    0x000E,
    0x000E,
};

static const u16 rastan_active_dip_palette[16] = {
    0x0000,
    0x0EE0,
    0x0EE0,
    0x0EE0,
    0x0EE0,
    0x0EE0,
    0x0EE0,
    0x0EE0,
    0x0EE0,
    0x0EE0,
    0x0EE0,
    0x0EE0,
    0x0EE0,
    0x0EE0,
    0x0EE0,
    0x0EE0,
};

static const u16 rastan_graphics_test_palette[16] = {
    0x0000,
    0x0222,
    0x0444,
    0x0666,
    0x0888,
    0x0AAA,
    0x0CCC,
    0x0EEE,
    0x0022,
    0x0044,
    0x0066,
    0x0088,
    0x00AA,
    0x00CC,
    0x00EE,
    0x0EEE,
};

static const MenuItem menu_items[MENU_COUNT] = {
    {"CABINET TYPE", cabinet_values, "CABINET ORIENTATION FOR THE GAME.", "SW1 1", 2},
    {"MONITOR", monitor_values, "FLIPS MONITOR DISPLAY DIRECTION.", "SW1 2", 2},
    {"GAME MODE", game_mode_values, "NORMAL GAME OR BOARD TEST MODE.", "SW1 3", 2},
    {"COINAGE", coinage_values, "PRICING FOR CREDITS AND COINS.", "SW1 5-8", 4},
    {"DIFFICULTY", difficulty_values, "OVERALL GAME DIFFICULTY LEVEL.", "SW2 1-2", 4},
    {"BONUS LIFE", bonus_values, "SCORE NEEDED FOR BONUS LIFE.", "SW2 3-4", 4},
    {"LIVES", lives_values, "STARTING LIVES FOR EACH CREDIT.", "SW2 5-6", 4},
    {"CONTINUE", continue_values, "ALLOW CONTINUE AFTER GAME OVER.", "SW2 7", 2},
    {"COMPETITION SETTINGS", NULL, "APPLY ARCADE COMPETITION DEFAULT SETTINGS.", "", 0},
    {"FACTORY DEFAULTS", NULL, "RESTORE THE DEFAULT RASTAN DIP POSITIONS.", "", 0},
    {"GRAPHICS TEST", NULL, "OPEN THE RASTAN GRAPHICS TEST SCREEN.", "", 0},
    {"SOUND TEST", NULL, "OPEN THE RASTAN SOUND TEST SCREEN.", "", 0},
    {"START RASTAN", NULL, "LAUNCH THE RASTAN STARTUP AND GAME FLOW.", "", 0},
};

typedef struct {
    uint16_t rastan_font_tile_buffer[1024];
    /* 64 unique sprite cells * (2x2 tiles) * (8 u32 words per tile) = 2048 u32. */
    uint32_t frontend_runtime_sprite_tile_buffer[FRONTEND_RUNTIME_MAX_UNIQUE_CODES * 4 * 8];
    uint16_t frontend_runtime_sprite_codes[FRONTEND_RUNTIME_MAX_UNIQUE_CODES];
    char     status_line[80];
    /* Add any other scrubbed launcher globals here! */
} LauncherRuntime;

union WramOverlay {
    LauncherRuntime launcher;
} __attribute__((aligned(4)));

union WramOverlay wram_overlay;
extern union WramOverlay wram_overlay;

volatile u8 rastan_virtual_dip1 = FACTORY_DIP1;
volatile u8 rastan_virtual_dip2 = FACTORY_DIP2;
static u8 selected_menu = 0;
static UndoState undo_state = {0, 0, FALSE};
static u32 *graphics_test_tile_buffer = NULL;
static AppScreen current_screen = SCREEN_CONFIG;
static u16 graphics_page = 0;
static GraphicsRegion graphics_region = GRAPHICS_REGION_PC080SN;
volatile u8 rastan_virtual_sound_command = 0x00;
volatile u8 rastan_virtual_sound_pending = FALSE;
static u8 sound_test_last_command = 0x00;
static bool sound_test_has_triggered = FALSE;
static volatile u32 packed_romset_size_cache = 0;
static volatile u32 packed_romset_signature_cache = 0;
static volatile bool frontend_live_handoff_active = FALSE;
typedef struct
{
    u8 code;
    u8 src_tile;
} RastanFontGlyph;

static const RastanFontGlyph rastan_font_glyphs[] = {
    /* Proven from startup/title string tables plus the masked pc080sn font ref. */
    /* Only keep glyphs this UI actually uses until the rest are traced cleanly. */
    /* 0x40 is the copyright glyph in title strings, not a commercial at. */
    /* 0x2A is a separate symbol, not a standard ASCII asterisk. */
    {'(', 0x28},
    {')', 0x29},
    {'-', 0x2D},
    {'.', 0x2E},
    {':', 0x3B},
    {'=', 0x3D},
    {'0', 0x30},
    {'1', 0x31},
    {'2', 0x32},
    {'3', 0x33},
    {'4', 0x34},
    {'5', 0x35},
    {'6', 0x36},
    {'7', 0x37},
    {'8', 0x38},
    {'9', 0x39},
    {'A', 0x41},
    {'B', 0x42},
    {'C', 0x43},
    {'D', 0x44},
    {'E', 0x45},
    {'F', 0x46},
    {'G', 0x47},
    {'H', 0x48},
    {'I', 0x49},
    {'J', 0x4A},
    {'K', 0x4B},
    {'L', 0x4C},
    {'M', 0x4D},
    {'N', 0x4E},
    {'O', 0x4F},
    {'P', 0x50},
    {'Q', 0x51},
    {'R', 0x52},
    {'S', 0x53},
    {'T', 0x54},
    {'U', 0x55},
    {'V', 0x56},
    {'W', 0x57},
    {'X', 0x58},
    {'Y', 0x59},
    {'Z', 0x5A},
};

static void build_rastan_font(void)
{
    u16 i;
    u8 *dst = (u8 *) wram_overlay.launcher.rastan_font_tile_buffer;

    memset(wram_overlay.launcher.rastan_font_tile_buffer, 0, sizeof(wram_overlay.launcher.rastan_font_tile_buffer));

    for (i = 0; i < sizeof(rastan_font_glyphs) / sizeof(rastan_font_glyphs[0]); i++)
    {
        const u8 code = rastan_font_glyphs[i].code;
        const u32 src_offset = (u32) rastan_font_glyphs[i].src_tile * 32;
        const u32 dst_offset = (u32) (code - 32) * 32;

        memcpy(dst + dst_offset, rastan_pc080sn + src_offset, 32);
    }
}

static char lookup_rastan_font_char(u8 source_tile)
{
    u16 i;

    for (i = 0; i < sizeof(rastan_font_glyphs) / sizeof(rastan_font_glyphs[0]); i++)
    {
        if (rastan_font_glyphs[i].src_tile == source_tile)
        {
            return (char)rastan_font_glyphs[i].code;
        }
    }

    return '\0';
}





static void draw_padded_text_palette(const char *text, u16 x, u16 y, u16 width, u16 palette);
static bool menu_controls_switch(u8 menu_index, bool bank2, u8 bit);
static u16 menu_row_y(u8 index);
static bool menu_item_is_action(u8 index);
static void render_dip_banks(void);
static void render_menu_row(u8 index);
static void render_help_panel(void);
static void activate_selected_menu(void);
static void request_start_rastan(void);
static void reset_launcher_runtime_state(void);
static void render_graphics_test_screen(void);
static void enter_graphics_test(void);
static void leave_graphics_test(void);
static const u8 *get_graphics_region_data(void);
static u16 get_graphics_region_item_count(void);
static u16 get_graphics_test_cols(void);
static u16 get_graphics_test_rows(void);
static u16 get_graphics_test_items_per_page(void);
static const char *get_graphics_region_name(void);
static const char *get_graphics_region_description(void);
static const char *get_graphics_region_unit_name(void);
static bool ensure_graphics_test_buffer(void);
static void free_graphics_test_buffer(void);
static void render_sound_test_screen(void);
static void enter_sound_test(void);
static void leave_sound_test(void);
static void trigger_sound_test_command(void);
static void render_startup_preview_screen(void)
    __attribute__((unused));
static void render_frontend_sprite_layer(void)
    __attribute__((unused));
void genesistan_hook_tilemap_plane_a(void);
void genesistan_hook_tilemap_plane_b(void);
static void clear_frontend_sprite_layer(void);
static void scrub_launcher_runtime_buffers(void);
static u16 convert_xbgr555_to_genesis(u16 raw);
static u16 convert_clcs_to_genesis(u16 raw);
static u16 frontend_palette_line_for_bank(u16 bank, u16 *bank_map, u16 *bank_count);
static void frontend_decode_pc090oj_cell(u16 code, u32 *dst_tiles);
static s16 frontend_runtime_tile_for_code(u16 code, u16 *unique_count);
static void refresh_frontend_sprite_palettes(const u16 *bank_map, u16 bank_count);
static void leave_startup_preview(void);
static u32 get_packed_romset_size(void);
static u32 get_packed_romset_signature(void);
static void restore_launcher_vdp_state(void);
static void genesistan_frontend_live_vint_handoff(void);
void rastan_draw_tile_xy(u16 tile_attr, int x, int y);

static void draw_padded_text(const char *text, u16 x, u16 y, u16 width)
{
    draw_padded_text_palette(text, x, y, width, PAL1);
}

static void draw_padded_text_palette(const char *text, u16 x, u16 y, u16 width, u16 palette)
{
    char line[SCREEN_W + 1];
    const size_t len = strlen(text);
    u16 i;

    for (i = 0; i < width && i < SCREEN_W; i++)
    {
        line[i] = (i < len) ? text[i] : ' ';
    }
    line[i] = '\0';

    VDP_drawTextEx(BG_A, line, TILE_ATTR_FULL(palette, FALSE, FALSE, FALSE, 0), x, y, CPU);
}

static void set_status(const char *text)
{
    strncpy(wram_overlay.launcher.status_line, text, SCREEN_W);
    wram_overlay.launcher.status_line[SCREEN_W] = '\0';
    draw_padded_text(wram_overlay.launcher.status_line, 0, 27, SCREEN_W);
}

static void save_undo_state(void)
{
    undo_state.dip1 = rastan_virtual_dip1;
    undo_state.dip2 = rastan_virtual_dip2;
    undo_state.valid = TRUE;
}

static u8 get_bit(u8 value, u8 bit)
{
    return (value >> bit) & 1;
}

static void set_bit(u8 *value, u8 bit, u8 raw)
{
    if (raw) *value |= (1 << bit);
    else *value &= ~(1 << bit);
}

static u8 get_field(u8 value, u8 shift, u8 mask)
{
    return (value >> shift) & mask;
}

static void set_field(u8 *value, u8 shift, u8 mask, u8 raw)
{
    *value = (*value & ~(mask << shift)) | ((raw & mask) << shift);
}

static u8 get_menu_value(u8 index)
{
    switch (index)
    {
        case 0: return get_bit(rastan_virtual_dip1, 0) ? 1 : 0;
        case 1: return get_bit(rastan_virtual_dip1, 1) ? 0 : 1;
        case 2: return get_bit(rastan_virtual_dip1, 2) ? 0 : 1;
        case 3:
        {
            const u8 raw = get_field(rastan_virtual_dip1, 4, 0x0F);
            if (raw == 0x0F) return 0;
            if (raw == 0x0A) return 1;
            if (raw == 0x05) return 2;
            return 3;
        }
        case 4:
        {
            const u8 raw = get_field(rastan_virtual_dip2, 0, 0x03);
            if (raw == 0x02) return 0;
            if (raw == 0x03) return 1;
            if (raw == 0x01) return 2;
            return 3;
        }
        case 5:
        {
            const u8 raw = get_field(rastan_virtual_dip2, 2, 0x03);
            if (raw == 0x03) return 0;
            if (raw == 0x02) return 1;
            if (raw == 0x01) return 2;
            return 3;
        }
        case 6:
        {
            const u8 raw = get_field(rastan_virtual_dip2, 4, 0x03);
            if (raw == 0x03) return 0;
            if (raw == 0x02) return 1;
            if (raw == 0x01) return 2;
            return 3;
        }
        case 7: return get_bit(rastan_virtual_dip2, 6) ? 0 : 1;
        default: return 0;
    }
}

static void set_menu_value(u8 index, u8 next_value)
{
    save_undo_state();

    switch (index)
    {
        case 0: set_bit((u8 *) &rastan_virtual_dip1, 0, next_value ? 1 : 0); break;
        case 1: set_bit((u8 *) &rastan_virtual_dip1, 1, next_value ? 0 : 1); break;
        case 2: set_bit((u8 *) &rastan_virtual_dip1, 2, next_value ? 0 : 1); break;
        case 3:
        {
            static const u8 raw_coinage[4] = {0x0F, 0x0A, 0x05, 0x00};
            set_field((u8 *) &rastan_virtual_dip1, 4, 0x0F, raw_coinage[next_value & 3]);
            break;
        }
        case 4:
        {
            static const u8 raw_difficulty[4] = {0x02, 0x03, 0x01, 0x00};
            set_field((u8 *) &rastan_virtual_dip2, 0, 0x03, raw_difficulty[next_value & 3]);
            break;
        }
        case 5:
        {
            static const u8 raw_bonus[4] = {0x03, 0x02, 0x01, 0x00};
            set_field((u8 *) &rastan_virtual_dip2, 2, 0x03, raw_bonus[next_value & 3]);
            break;
        }
        case 6:
        {
            static const u8 raw_lives[4] = {0x03, 0x02, 0x01, 0x00};
            set_field((u8 *) &rastan_virtual_dip2, 4, 0x03, raw_lives[next_value & 3]);
            break;
        }
        case 7: set_bit((u8 *) &rastan_virtual_dip2, 6, next_value ? 0 : 1); break;
        default: break;
    }
}

static u16 menu_row_y(u8 index)
{
    return (index < SETTING_MENU_COUNT) ? (u16)(9 + index) : (u16)(10 + index);
}

static bool menu_item_is_action(u8 index)
{
    return index >= SETTING_MENU_COUNT;
}

static void cycle_selected_setting(bool backwards)
{
    const u8 current_value = get_menu_value(selected_menu);
    const u8 count = menu_items[selected_menu].value_count;
    const u8 next_value = backwards ? ((current_value == 0) ? (count - 1) : (current_value - 1))
                                    : ((current_value + 1) % count);

    set_menu_value(selected_menu, next_value);
    render_dip_banks();
    render_menu_row(selected_menu);
    render_help_panel();
    set_status("SETTING UPDATED");
}

static void draw_dip_icon(u16 x, u16 y, bool active, bool highlighted)
{
    const u16 tile_index = active ? DIP_TILE_ON_INDEX : DIP_TILE_OFF_INDEX;
    const u16 palette = highlighted ? PAL0 : PAL2;

    VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(palette, FALSE, FALSE, FALSE, tile_index), x, y);
    VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(palette, FALSE, FALSE, FALSE, tile_index + 1), x, y + 1);
}

static void render_dip_bank(u8 bank_value, bool bank2, u16 title_x, u16 label_x, u16 icon_x, const char *title)
{
    u16 i;

    draw_padded_text(title, title_x, 4, 12);
    draw_padded_text("ON", label_x, 5, 3);
    draw_padded_text("OFF", label_x, 6, 3);

    for (i = 0; i < 8; i++)
    {
        draw_dip_icon((u16)(icon_x + (i * 2)), 5, ((bank_value >> i) & 1) == 0, menu_controls_switch(selected_menu, bank2, i));
    }
}

static void render_dip_banks(void)
{
    VDP_fillTileMapRect(BG_A, TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, TILE_FONT_INDEX), 0, 4, SCREEN_W, 3);
    render_dip_bank(rastan_virtual_dip1, FALSE, 2, 0, 4, "DIP SWITCH 1");
    render_dip_bank(rastan_virtual_dip2, TRUE, 24, 21, 25, "DIP SWITCH 2");
}

static void render_menu_row(u8 index)
{
    char line[SCREEN_W + 1];
    const MenuItem *item = &menu_items[index];
    const bool is_action = menu_item_is_action(index);
    const u16 y = menu_row_y(index);

    if (is_action)
    {
        sprintf(line, "%c %-21s", (index == selected_menu) ? ')' : ' ', item->label);
        draw_padded_text_palette(line, 1, y, 27, (index == selected_menu) ? PAL3 : PAL1);
    }
    else
    {
        const u8 value = get_menu_value(index);
        sprintf(line, "%c %-13s %-11s", (index == selected_menu) ? ')' : ' ', item->label, item->values[value]);
        draw_padded_text_palette(line, 1, y, 27, (index == selected_menu) ? PAL3 : PAL1);
    }
}

static void render_help_panel(void)
{
    const MenuItem *item = &menu_items[selected_menu];
    char line[SCREEN_W + 1];

    if (item->switches[0] != '\0')
        sprintf(line, "HELP: %-28s", item->switches);
    else
        sprintf(line, "HELP");

    draw_padded_text(line, 0, 24, SCREEN_W);
    draw_padded_text(item->help_text, 0, 25, SCREEN_W);
    draw_padded_text("", 0, 26, SCREEN_W);
}

static void render_static_layout(void)
{
    u16 build_x;

    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);

    draw_padded_text("RASTAN STARTUP CONFIG", 9, 1, 22);
    build_x = (u16)((SCREEN_W - strlen(RASTAN_BUILD_LINE)) / 2);
    draw_padded_text(RASTAN_BUILD_LINE, build_x, 2, (u16)strlen(RASTAN_BUILD_LINE));
    draw_padded_text("SETTINGS", 1, 8, 8);
}

static void restore_launcher_vdp_state(void)
{
    SYS_disableInts();
    VDP_init();
    VDP_setScreenWidth320();
    PAL_setPalette(PAL0, rastan_active_dip_palette, CPU);
    PAL_setPalette(PAL1, rastan_font_palette, CPU);
    PAL_setPalette(PAL2, rastan_dip_palette.data, CPU);
    PAL_setPalette(PAL3, rastan_selected_font_palette, CPU);
    VDP_setTextPalette(PAL1);
    build_rastan_font();
    VDP_loadFontData((const u32 *)wram_overlay.launcher.rastan_font_tile_buffer, FONT_LEN, CPU);
    VDP_loadTileSet(&rastan_dip_on, DIP_TILE_ON_INDEX, CPU);
    VDP_loadTileSet(&rastan_dip_off, DIP_TILE_OFF_INDEX, CPU);
    VDP_updateSprites(0, CPU);
    SYS_enableInts();
}

static void load_arcade_palette(void)
{
    uint16_t buf[64];
    uint16_t i;
    uint16_t block = 0xFFFFU;
    uint16_t b;

    for (b = 0; b < (2048U / 64U); b++) {
        const uint16_t base = (uint16_t)(b * 64U);
        for (i = 0; i < 64U; i++) {
            if (genesistan_palette_clcs[base + i] != 0) {
                block = b;
                break;
            }
        }
        if (block != 0xFFFFU) {
            break;
        }
    }

    if (block == 0xFFFFU) {
        SYS_disableInts();
        PAL_setColors(0, (const u16 *)genesistan_palette_rom_table, 64, DMA);
        VDP_waitDMACompletion();
        SYS_enableInts();
        return;
    }

    for (i = 0; i < 64U; i++) {
        const uint16_t c = genesistan_palette_clcs[(block * 64U) + i];
        buf[i] = convert_clcs_to_genesis(c);
    }

    SYS_disableInts();
    PAL_setColors(0, (const u16 *)buf, 64, DMA);
    VDP_waitDMACompletion();
    SYS_enableInts();
}

static void render_full_screen(void)
{
    u16 i;

    render_static_layout();
    render_dip_banks();

    for (i = 0; i < MENU_COUNT; i++)
    {
        render_menu_row((u8)i);
    }

    render_help_panel();
    set_status(wram_overlay.launcher.status_line);
}

static u16 get_graphics_test_page_count(void)
{
    return (get_graphics_region_item_count() + get_graphics_test_items_per_page() - 1) / get_graphics_test_items_per_page();
}

static const u8 *get_graphics_region_data(void)
{
    return (graphics_region == GRAPHICS_REGION_PC080SN) ? rastan_pc080sn : rastan_pc090oj;
}

static u16 get_graphics_region_item_count(void)
{
    return (graphics_region == GRAPHICS_REGION_PC080SN) ? PC080SN_TILE_COUNT : PC090OJ_CELL_COUNT;
}

static u16 get_graphics_test_cols(void)
{
    return (graphics_region == GRAPHICS_REGION_PC080SN) ? GRAPHICS_TEST_COLS_PC080SN : GRAPHICS_TEST_COLS_PC090OJ;
}

static u16 get_graphics_test_rows(void)
{
    return (graphics_region == GRAPHICS_REGION_PC080SN) ? GRAPHICS_TEST_ROWS_PC080SN : GRAPHICS_TEST_ROWS_PC090OJ;
}

static u16 get_graphics_test_items_per_page(void)
{
    return (graphics_region == GRAPHICS_REGION_PC080SN) ? GRAPHICS_TEST_ITEMS_PER_PAGE_PC080SN : GRAPHICS_TEST_ITEMS_PER_PAGE_PC090OJ;
}

static const char *get_graphics_region_name(void)
{
    return (graphics_region == GRAPHICS_REGION_PC080SN) ? "PC080SN" : "PC090OJ";
}

static const char *get_graphics_region_description(void)
{
    return (graphics_region == GRAPHICS_REGION_PC080SN) ? "BG AND TEXT LAYER ROM" : "SPRITE OBJECT ROM";
}

static const char *get_graphics_region_unit_name(void)
{
    return (graphics_region == GRAPHICS_REGION_PC080SN) ? "TILES" : "CELLS";
}

static bool ensure_graphics_test_buffer(void)
{
    if (graphics_test_tile_buffer != NULL)
    {
        return TRUE;
    }

    graphics_test_tile_buffer = MEM_alloc(sizeof(u32) * GRAPHICS_TEST_MAX_VRAM_TILES * 8);
    return graphics_test_tile_buffer != NULL;
}

static void free_graphics_test_buffer(void)
{
    if (graphics_test_tile_buffer != NULL)
    {
        MEM_free(graphics_test_tile_buffer);
        graphics_test_tile_buffer = NULL;
    }
}

static void render_graphics_test_screen(void)
{
    static const u32 blank_tile[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    char line[SCREEN_W + 1];
    const u8 *graphics_data = get_graphics_region_data();
    const u16 region_item_count = get_graphics_region_item_count();
    const u16 cols = get_graphics_test_cols();
    const u16 rows = get_graphics_test_rows();
    const u16 items_per_page = get_graphics_test_items_per_page();
    const u16 page_count = get_graphics_test_page_count();
    const u16 page_base_item = graphics_page * items_per_page;
    const u16 item_count = (page_base_item + items_per_page <= region_item_count)
                               ? items_per_page
                               : (region_item_count - page_base_item);
    const u16 item_end = (item_count == 0) ? page_base_item : (page_base_item + item_count - 1);
    const u32 rom_start = (graphics_region == GRAPHICS_REGION_PC080SN) ? ((u32)page_base_item * 32) : ((u32)page_base_item * 128);
    const u32 rom_end = (item_count == 0)
                            ? rom_start
                            : ((graphics_region == GRAPHICS_REGION_PC080SN)
                                   ? (((u32)(page_base_item + item_count) * 32) - 1)
                                   : (((u32)(page_base_item + item_count) * 128) - 1));
    u16 row;
    u16 col;

    if (!ensure_graphics_test_buffer())
    {
        VDP_clearPlane(BG_A, TRUE);
        VDP_clearPlane(BG_B, TRUE);
        draw_padded_text("RASTAN GRAPHICS TEST", 10, 1, 20);
        draw_padded_text("NOT ENOUGH FREE WRAM", 8, 12, 24);
        set_status("GFX TEST NEEDS MORE WRAM");
        return;
    }

    memset(
        graphics_test_tile_buffer,
        0,
        sizeof(u32) * GRAPHICS_TEST_MAX_VRAM_TILES * 8
    );

    VDP_clearPlane(BG_A, TRUE);
    PAL_setPalette(PAL2, rastan_graphics_test_palette, CPU);
    VDP_loadTileData(blank_tile, GRAPHICS_TEST_BLANK_TILE_INDEX, 1, CPU);

    if (graphics_region == GRAPHICS_REGION_PC080SN)
    {
        if (item_count > 0)
        {
            VDP_loadTileData((const u32 *)(graphics_data + rom_start), GRAPHICS_TEST_TILE_INDEX, item_count, CPU);
        }
    }
    else if (item_count > 0)
    {
        u16 cell;

        for (cell = 0; cell < item_count; cell++)
        {
            const u8 *src = graphics_data + (((u32) page_base_item + cell) * 128);
            u8 *dst = ((u8 *)graphics_test_tile_buffer) + ((u32) cell * 4 * 32);
            u16 y;

            for (y = 0; y < 16; y++)
            {
                const u8 *src_row = src + (y * 8);
                u8 *tile_left;
                u8 *tile_right;

                if (y < 8)
                {
                    tile_left = dst + (0 * 32) + (y * 4);
                    tile_right = dst + (1 * 32) + (y * 4);
                }
                else
                {
                    tile_left = dst + (2 * 32) + ((y - 8) * 4);
                    tile_right = dst + (3 * 32) + ((y - 8) * 4);
                }

                memcpy(tile_left, src_row, 4);
                memcpy(tile_right, src_row + 4, 4);
            }
        }

        VDP_loadTileData(graphics_test_tile_buffer, GRAPHICS_TEST_TILE_INDEX, item_count * 4, CPU);
    }

    draw_padded_text("RASTAN GRAPHICS TEST", 10, 1, 20);
    sprintf(line, "%s RAW TILE BROWSER", get_graphics_region_name());
    draw_padded_text(line, 8, 2, 24);
    draw_padded_text(get_graphics_region_description(), 9, 3, 22);

    sprintf(line, "PAGE %02u OF %02u", graphics_page + 1, page_count);
    draw_padded_text(line, 12, 17, 16);
    sprintf(line, "%s %04X-%04X", get_graphics_region_unit_name(), page_base_item, item_end);
    draw_padded_text(line, 11, 18, 18);
    sprintf(line, "ROM %05lX-%05lX", (unsigned long)rom_start, (unsigned long)rom_end);
    draw_padded_text(line, 10, 19, 20);

    for (row = 0; row < rows; row++)
    {
        for (col = 0; col < cols; col++)
        {
            const u16 item_offset = (row * cols) + col;

            if (graphics_region == GRAPHICS_REGION_PC080SN)
            {
                const u16 tile_index = (item_offset < item_count)
                                           ? (GRAPHICS_TEST_TILE_INDEX + item_offset)
                                           : GRAPHICS_TEST_BLANK_TILE_INDEX;

                VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL2, FALSE, FALSE, FALSE, tile_index), (u16)(10 + col), (u16)(4 + row));
            }
            else
            {
                const u16 tile_base = (item_offset < item_count)
                                          ? (GRAPHICS_TEST_TILE_INDEX + (item_offset * 4))
                                          : GRAPHICS_TEST_BLANK_TILE_INDEX;
                const u16 x = (u16)(10 + (col * 2));
                const u16 y = (u16)(4 + (row * 2));

                VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL2, FALSE, FALSE, FALSE, tile_base + 0), x, y);
                VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL2, FALSE, FALSE, FALSE, tile_base + 1), x + 1, y);
                VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL2, FALSE, FALSE, FALSE, tile_base + 2), x, y + 1);
                VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL2, FALSE, FALSE, FALSE, tile_base + 3), x + 1, y + 1);
            }
        }
    }

    draw_padded_text("LEFT RIGHT PAGE", 11, 22, 16);
    draw_padded_text("UP DOWN PLUS 10", 11, 23, 16);
    draw_padded_text("A TOGGLE REGION", 11, 24, 16);
    draw_padded_text("B C START BACK", 11, 25, 16);
    sprintf(line, "GRAPHICS TEST %s", get_graphics_region_name());
    set_status(line);
    VDP_waitDMACompletion();
}

static void enter_graphics_test(void)
{
    current_screen = SCREEN_GRAPHICS_TEST;
    render_graphics_test_screen();
}

static void leave_graphics_test(void)
{
    current_screen = SCREEN_CONFIG;
    free_graphics_test_buffer();
    PAL_setPalette(PAL2, rastan_dip_palette.data, CPU);
    render_full_screen();
    set_status("READY");
}

static void render_sound_test_screen(void)
{
    char line[SCREEN_W + 1];

    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);

    draw_padded_text("RASTAN SOUND TEST", 11, 2, 18);
    draw_padded_text("SOUND COMMAND BROWSER", 9, 4, 22);

    sprintf(line, "CURRENT COMMAND %02X", rastan_virtual_sound_command);
    draw_padded_text(line, 10, 8, 20);

    if (sound_test_has_triggered)
    {
        sprintf(line, "LAST TRIGGER %02X", sound_test_last_command);
        draw_padded_text(line, 12, 10, 16);
    }
    else
    {
        draw_padded_text("LAST TRIGGER NONE", 11, 10, 18);
    }

    draw_padded_text("LEFT RIGHT PLUS 01", 10, 18, 20);
    draw_padded_text("UP DOWN PLUS 10", 11, 19, 18);
    draw_padded_text("A B C TRIGGER", 12, 21, 14);
    draw_padded_text("START BACK", 14, 22, 10);
    draw_padded_text("READY TO HOOK INTO SOUND LATCH", 5, 24, 30);
    draw_padded_text(wram_overlay.launcher.status_line, 0, 27, SCREEN_W);
}

static void enter_sound_test(void)
{
    current_screen = SCREEN_SOUND_TEST;
    strncpy(wram_overlay.launcher.status_line, "SOUND TEST", SCREEN_W);
    wram_overlay.launcher.status_line[SCREEN_W] = '\0';
    render_sound_test_screen();
}

static void leave_sound_test(void)
{
    current_screen = SCREEN_CONFIG;
    render_full_screen();
    set_status("READY");
}

static void trigger_sound_test_command(void)
{
    char line[SCREEN_W + 1];

    rastan_virtual_sound_pending = TRUE;
    sound_test_last_command = rastan_virtual_sound_command;
    sound_test_has_triggered = TRUE;
    sprintf(line, "COMMAND %02X QUEUED", rastan_virtual_sound_command);
    strncpy(wram_overlay.launcher.status_line, line, SCREEN_W);
    wram_overlay.launcher.status_line[SCREEN_W] = '\0';
    render_sound_test_screen();
}

static const char *startup_result_label(void)
{
    switch (genesistan_startup_result_code)
    {
        case GENESISTAN_STARTUP_RESULT_NORMAL: return "NORMAL";
        case GENESISTAN_STARTUP_RESULT_TEST: return "TEST";
        default: return "UNKNOWN";
    }
}

static void render_startup_preview_screen(void)
{
#if RASTAN_ENABLE_STARTUP_HOOK
    char line[SCREEN_W + 1];

    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);

    draw_padded_text("RASTAN STARTUP PREVIEW", 9, 1, 22);
    sprintf(line, "RESULT %-6s  DIPS %02X %02X", startup_result_label(), rastan_virtual_dip1, rastan_virtual_dip2);
    draw_padded_text(line, 5, 2, 30);
    sprintf(line, "3E %02X/%02X  C5 %04X  3C %04X", genesistan_shadow_reg_3e0001, genesistan_shadow_reg_3e0003, genesistan_shadow_reg_c50000, genesistan_shadow_reg_3c0000);
    draw_padded_text(line, 2, 3, 36);
    draw_padded_text("CWIN SHADOW REMOVED (Build 109)", 5, 4, 31);
    sprintf(line, "BG %04X/%04X FG %04X/%04X",
            genesistan_arcade_workram_words[0x10EC / 2],
            genesistan_arcade_workram_words[0x10EE / 2],
            genesistan_arcade_workram_words[0x10AE / 2],
            genesistan_arcade_workram_words[0x10B0 / 2]);
    draw_padded_text(line, 8, 5, 24);
    sprintf(line, "PAL %04X %04X %04X %04X",
            genesistan_palette_rom_table[0],
            genesistan_palette_rom_table[1],
            genesistan_palette_rom_table[2],
            genesistan_palette_rom_table[3]);
    draw_padded_text(line, 7, 6, 26);

    draw_padded_text("A/START RERUN   B/C BACK", 7, 26, 26);
    draw_padded_text(wram_overlay.launcher.status_line, 0, 27, SCREEN_W);
#else
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    draw_padded_text("NO HOOK PREVIEW IN PAYLOAD BUILD", 4, 12, 32);
    draw_padded_text(wram_overlay.launcher.status_line, 0, 27, SCREEN_W);
#endif
}

static u16 convert_xbgr555_to_genesis(u16 raw)
{
    const u16 r = (raw >> 0) & 0x1F;
    const u16 g = (raw >> 5) & 0x1F;
    const u16 b = (raw >> 10) & 0x1F;
    const u16 rn = (u16)(((r >> 2) & 0x07) << 1);
    const u16 gn = (u16)(((g >> 2) & 0x07) << 1);
    const u16 bn = (u16)(((b >> 2) & 0x07) << 1);

    return (u16)((bn << 8) | (gn << 4) | rn);
}

static u16 convert_clcs_to_genesis(u16 raw)
{
    return (u16)(((raw >> 1) & 0x000EU)
               | ((raw >> 2) & 0x00E0U)
               | ((raw >> 3) & 0x0E00U));
}

static u16 frontend_palette_line_for_bank(u16 bank, u16 *bank_map, u16 *bank_count)
{
    u16 i;

    for (i = 0; i < *bank_count; i++)
    {
        if (bank_map[i] == bank)
        {
            return i;
        }
    }

    if (*bank_count < FRONTEND_RUNTIME_MAX_PALETTE_BANKS)
    {
        bank_map[*bank_count] = bank;
        (*bank_count)++;
        return (u16)(*bank_count - 1);
    }

    return (u16)(bank & 0x0003);
}

static void frontend_decode_pc090oj_cell(u16 code, u32 *dst_tiles)
{
    const u16 cell = (u16)(code % PC090OJ_CELL_COUNT);
    const u8 *src = rastan_pc090oj + ((u32)cell * 128);
    u8 *dst = (u8 *)dst_tiles;
    u16 y;

    for (y = 0; y < 16; y++)
    {
        const u8 *src_row = src + (y * 8);
        u8 *tile_left;
        u8 *tile_right;

        if (y < 8)
        {
            tile_left = dst + (0 * 32) + (y * 4);
            tile_right = dst + (1 * 32) + (y * 4);
        }
        else
        {
            tile_left = dst + (2 * 32) + ((y - 8) * 4);
            tile_right = dst + (3 * 32) + ((y - 8) * 4);
        }

        memcpy(tile_left, src_row, 4);
        memcpy(tile_right, src_row + 4, 4);
    }
}

static s16 frontend_runtime_tile_for_code(u16 code, u16 *unique_count)
{
    u16 i;

    for (i = 0; i < *unique_count; i++)
    {
        if (wram_overlay.launcher.frontend_runtime_sprite_codes[i] == code)
        {
            return (s16)(FRONTEND_RUNTIME_SPRITE_TILE_BASE + (i * 4));
        }
    }

    if (*unique_count >= FRONTEND_RUNTIME_MAX_UNIQUE_CODES)
    {
        return -1;
    }

    wram_overlay.launcher.frontend_runtime_sprite_codes[*unique_count] = code;
    frontend_decode_pc090oj_cell(
        code,
        ((u32 *)wram_overlay.launcher.frontend_runtime_sprite_tile_buffer) + ((u32)(*unique_count) * 4 * 8)
    );
    (*unique_count)++;

    return (s16)(FRONTEND_RUNTIME_SPRITE_TILE_BASE + ((*unique_count - 1) * 4));
}

static void refresh_frontend_sprite_palettes(const u16 *bank_map, u16 bank_count)
{
    u16 line;

    for (line = 0; line < FRONTEND_RUNTIME_MAX_PALETTE_BANKS; line++)
    {
        const u16 bank = (line < bank_count) ? bank_map[line] : line;
        const u16 base = (u16)((bank & 0x03U) << 4);
        u16 color;

        for (color = 0; color < 16; color++)
        {
            const u16 clcs = genesistan_palette_clcs[base + color];
            const u16 gen = (clcs != 0)
                ? convert_clcs_to_genesis(clcs)
                : genesistan_palette_rom_table[base + color];
            PAL_setColor((line * 16) + color, gen);
        }
    }
}

static void clear_frontend_sprite_layer(void)
{
    VDP_updateSprites(0, CPU);
}

/*
 * Tile cache helpers (Build 113).
 * Linear scan over 1164 VRAM slots.
 * Slots 0-1003 → VRAM 20-1023 (TILE_CACHE_BASE_A + slot).
 * Slots 1004-1163 → VRAM 1280-1439 (TILE_CACHE_BASE_B + slot - SIZE_A).
 */
static uint16_t tile_cache_slot_to_vram(uint16_t slot)
{
    if (slot < TILE_CACHE_SIZE_A)
        return (uint16_t)(TILE_CACHE_BASE_A + slot);
    return (uint16_t)(TILE_CACHE_BASE_B + (slot - TILE_CACHE_SIZE_A));
}

/*
 * Look up arcade tile index in the VRAM tile cache.
 * On hit: update LRU and return VRAM slot.
 * On miss: evict LRU slot, DMA-load tile from rastan_pc080sn, return slot.
 * Must be called with interrupts already disabled.
 */
static uint16_t tile_cache_get(uint16_t arcade_tile)
{
    uint16_t i;
    uint16_t lru_slot = 0;
    uint16_t lru_val  = genesistan_tile_cache_lru[0];
    uint16_t vram_slot;

    for (i = 0; i < TILE_CACHE_SLOTS; i++) {
        if (genesistan_tile_cache_arcade[i] == arcade_tile) {
            genesistan_tile_cache_lru[i] = ++genesistan_tile_cache_clock;
            return tile_cache_slot_to_vram(i);
        }
        if (genesistan_tile_cache_lru[i] < lru_val) {
            lru_val  = genesistan_tile_cache_lru[i];
            lru_slot = i;
        }
    }

    /* Cache miss — evict LRU slot and DMA-load tile from ROM. */
    vram_slot = tile_cache_slot_to_vram(lru_slot);
    genesistan_tile_cache_arcade[lru_slot] = arcade_tile;
    genesistan_tile_cache_lru[lru_slot]    = ++genesistan_tile_cache_clock;

    VDP_loadTileData(
        (const u32 *)(rastan_pc080sn + (u32)arcade_tile * 32U),
        vram_slot, 1, DMA);
    VDP_waitDMACompletion();

    return vram_slot;
}

/*
 * JSR hooks called from arcade tilemap write functions
 * (0x055968 → plane_a, 0x055990 → plane_b).
 *
 * Build 140: Reads tile codes directly from Genesis ROM.
 *
 * Root cause of prior blank output (Build 116-139): workram[0x1040/0x1080]
 * are NEVER populated.  The setup routine at 0x55904 (which fills them) is
 * NOPped, and even if it ran, the absolute addresses 0x10D040/0x10D080 are
 * not remapped to Genesis WRAM — so 0x55904's writes miss the buffer entirely.
 *
 * Fix: read the same ROM data the arcade code would have accessed.
 * Arcade code at 0x502CC computes, for each of 16 tile slots i=0..15:
 *   row_ptr[i] = (0x1691C + i*0x22C0) + frame_ctr*64   (arcade ROM addr)
 *   tile_code  = word at row_ptr[i]+0
 *   attr_raw   = word at row_ptr[i]+2
 *
 * In Genesis ROM the maincpu copy is relocated by +0x200, so:
 *   genesis_addr = arcade_addr + 0x200
 *   → TILEMAP_ROM_BASE = 0x1691C + 0x200 = 0x16B1C
 *
 * frame_ctr = A5@(0x13E) = genesistan_arcade_workram_words[0x9F]
 * (byte value 0-255, populated each tick by game code at 0x50248-0x5025A).
 *
 * Layer mapping (AGENTS.md):
 *   mode==0 (0x55968) → arcade BG layer 0 → Genesis Plane B (BG_B)
 *   mode!=0 (0x55990) → arcade FG layer 1 → Genesis Plane A (BG_A)
 *
 * Position: cursor-driven, reset once per frontend tick.
 */
#define TILEMAP_ROM_BASE   0x16B1CUL  /* 0x1691C + 0x200 reloc */
#define TILEMAP_ROW_STRIDE 0x22C0UL   /* bytes between successive row entries */
#define TILEMAP_FRAME_STEP 64UL       /* bytes advanced per frame_ctr unit */

__attribute__((used, externally_visible, section(".text.patcher")))
void genesistan_hook_tilemap_plane_a(void)
{
    const uint16_t frame_ctr = genesistan_arcade_workram_words[0x9FU]; /* A5@(0x13E) */
    const uint16_t mode = genesistan_arcade_workram_words[0x854U];
    const uint16_t col = genesistan_hook_col_a;
    const uint16_t row = genesistan_hook_row_a;
    uint16_t i;

    if (mode != 0) {
        return;
    }

    SYS_disableInts();
    for (i = 0; i < 16; i++) {
        const uint32_t rom_addr  = TILEMAP_ROM_BASE
                                 + (uint32_t)i * TILEMAP_ROW_STRIDE
                                 + (uint32_t)frame_ctr * TILEMAP_FRAME_STEP;
        const uint16_t code      = *(const uint16_t *)rom_addr;
        const uint16_t attr_raw  = *(const uint16_t *)(rom_addr + 2UL);
        const uint16_t arcade_tile = code & 0x3FFFU;
        const uint16_t vram_tile   = tile_cache_get(arcade_tile);
        const uint16_t pal         = (attr_raw >> 7) & 0x3U;
        const uint16_t vflip       = (attr_raw >> 15) & 1U;
        const uint16_t hflip       = (attr_raw >> 14) & 1U;

        /* mode==0 → arcade BG layer 0 → Genesis Plane B */
        VDP_setTileMapXY(BG_B,
            TILE_ATTR_FULL(pal, 1, vflip, hflip, vram_tile),
            col + i, row);
    }

    genesistan_hook_col_a = (uint16_t)(genesistan_hook_col_a + 16U);
    if (genesistan_hook_col_a >= 64U) {
        genesistan_hook_col_a = 0;
        genesistan_hook_row_a = (uint16_t)(genesistan_hook_row_a + 1U);
        if (genesistan_hook_row_a >= 32U) {
            genesistan_hook_row_a = 8;
        }
    }

    SYS_enableInts();
}

__attribute__((used, externally_visible, section(".text.patcher")))
void genesistan_hook_tilemap_plane_b(void)
{
    const uint16_t frame_ctr = genesistan_arcade_workram_words[0x9FU]; /* A5@(0x13E) */
    const uint16_t mode = genesistan_arcade_workram_words[0x854U];
    const uint16_t col = genesistan_hook_col_b;
    const uint16_t row = genesistan_hook_row_b;
    uint16_t i;

    if (mode == 0) {
        return;
    }

    SYS_disableInts();
    for (i = 0; i < 16; i++) {
        const uint32_t rom_addr  = TILEMAP_ROM_BASE
                                 + (uint32_t)i * TILEMAP_ROW_STRIDE
                                 + (uint32_t)frame_ctr * TILEMAP_FRAME_STEP;
        const uint16_t code      = *(const uint16_t *)rom_addr;
        const uint16_t attr_raw  = *(const uint16_t *)(rom_addr + 2UL);
        const uint16_t arcade_tile = code & 0x3FFFU;
        const uint16_t vram_tile   = tile_cache_get(arcade_tile);
        const uint16_t pal         = (attr_raw >> 7) & 0x3U;
        const uint16_t vflip       = (attr_raw >> 15) & 1U;
        const uint16_t hflip       = (attr_raw >> 14) & 1U;

        /* mode!=0 → arcade FG layer 1 → Genesis Plane A */
        VDP_setTileMapXY(BG_A,
            TILE_ATTR_FULL(pal, 1, vflip, hflip, vram_tile),
            col + i, row);
    }

    genesistan_hook_col_b = (uint16_t)(genesistan_hook_col_b + 16U);
    if (genesistan_hook_col_b >= 64U) {
        genesistan_hook_col_b = 0;
        genesistan_hook_row_b = (uint16_t)(genesistan_hook_row_b + 1U);
        if (genesistan_hook_row_b >= 32U) {
            genesistan_hook_row_b = 8;
        }
    }

    SYS_enableInts();
}

void rastan_draw_tile_xy(u16 tile_attr, int x, int y)
{
    if (x < 0 || x >= 64 || y < 0 || y >= 32)
        return;

    VDP_setTileMapXY(BG_A, tile_attr, (u16)x, (u16)y);
}

#define TEXT_WRITER_3BB48_TABLE_SOURCE  0x003BD92UL /* shifted runtime table (build-time relocated) */
#define TEXT_WRITER_3C3FE_TABLE_SOURCE  0x003C66CUL /* shifted runtime table (build-time relocated) */
#define TEXT_WRITER_CWINDOW_PAGE2_BASE  0x00C08000UL
#define TEXT_WRITER_CWINDOW_PAGE_BYTES  0x00008000UL
#define TEXT_WRITER_SHADOW_PAGE2_OFFSET 0x0000C800UL /* 0x10C000 + 0xC800 = arcade 0xC08000 alias */
#define TEXT_WRITER_VISIBLE_ROW_BIAS    4U /* 0x400 byte page viewport offset / 0x100 bytes per row */
#define TITLE_PLANE_A_VRAM_ADDR         0xE000U
#define TITLE_PLANE_B_VRAM_ADDR         0xC000U
#define TITLE_SAT_VRAM_ADDR             0xF800U

static u16 text_writer_read_be16(const u8 *src)
{
    return (u16)(((u16)src[0] << 8) | src[1]);
}

static u32 text_writer_read_be32(const u8 *src)
{
    return ((u32)src[0] << 24)
         | ((u32)src[1] << 16)
         | ((u32)src[2] << 8)
         | (u32)src[3];
}

static bool text_writer_ptr_to_xy(u32 raw_ptr, s16 *out_x, s16 *out_y, u32 *out_offset)
{
    const u32 shadow_base24 =
        (((u32)genesistan_arcade_workram_words + TEXT_WRITER_SHADOW_PAGE2_OFFSET) & 0x00FFFFFFU);
    const u32 shadow_base_e = 0xE0000000U | shadow_base24;
    const u32 raw24 = raw_ptr & 0x00FFFFFFU;
    u32 offset;
    u32 cell;
    u32 row;
    const u32 col_bias = 32U;

    if (raw_ptr >= TEXT_WRITER_CWINDOW_PAGE2_BASE
        && raw_ptr < (TEXT_WRITER_CWINDOW_PAGE2_BASE + TEXT_WRITER_CWINDOW_PAGE_BYTES))
    {
        offset = raw_ptr - TEXT_WRITER_CWINDOW_PAGE2_BASE;
    }
    else if (raw_ptr >= shadow_base_e
             && raw_ptr < (shadow_base_e + TEXT_WRITER_CWINDOW_PAGE_BYTES))
    {
        offset = raw_ptr - shadow_base_e;
    }
    else if (raw24 >= shadow_base24
             && raw24 < (shadow_base24 + TEXT_WRITER_CWINDOW_PAGE_BYTES))
    {
        offset = raw24 - shadow_base24;
    }
    else
    {
        return FALSE;
    }

    if ((offset & 1U) != 0U)
    {
        return FALSE;
    }

    cell = offset >> 2; /* 2 words per text cell (attr + tile). */
    row = (cell >> 6) & 0x1FU;
    if (row < TEXT_WRITER_VISIBLE_ROW_BIAS)
    {
        return FALSE;
    }
    {
        u32 col = cell & 0x3FU;
        if (col < col_bias)
        {
            col += 64U;
        }
        *out_x = (s16)(col - col_bias);
    }
    *out_offset = offset;
    *out_y = (s16)(row - TEXT_WRITER_VISIBLE_ROW_BIAS);
    return TRUE;
}

static u16 text_writer_build_tile_attr(u16 attr_word, u8 glyph_code)
{
    u16 i;
    u16 arcade_tile = (u16)glyph_code;
    u16 vram_tile;
    const u16 palette   = attr_word & 0x3U;
    const u16 priority  = (attr_word >> 13) & 1U;
    const u16 vflip     = (attr_word >> 15) & 1U;
    const u16 hflip     = (attr_word >> 14) & 1U;

    for (i = 0; i < sizeof(rastan_font_glyphs) / sizeof(rastan_font_glyphs[0]); i++)
    {
        if (rastan_font_glyphs[i].code == glyph_code)
        {
            arcade_tile = rastan_font_glyphs[i].src_tile;
            break;
        }
    }

    vram_tile = tile_cache_get(arcade_tile);

    return TILE_ATTR_FULL(palette, priority, vflip, hflip, vram_tile);
}

static u16 text_writer_build_tile_attr_from_arcade_code(u16 attr_word, u16 arcade_code)
{
    const u16 vram_tile = tile_cache_get(arcade_code & 0x3FFFU);
    const u16 palette   = attr_word & 0x3U;
    const u16 priority  = (attr_word >> 13) & 1U;
    const u16 vflip     = (attr_word >> 15) & 1U;
    const u16 hflip     = (attr_word >> 14) & 1U;

    return TILE_ATTR_FULL(palette, priority, vflip, hflip, vram_tile);
}

static void genesistan_sync_title_vdp_layout(void)
{
    SYS_disableInts();
    VDP_setPlaneSize(64, 32, FALSE);
    VDP_setBGAAddress(TITLE_PLANE_A_VRAM_ADDR);
    VDP_setBGBAddress(TITLE_PLANE_B_VRAM_ADDR);
    VDP_setSpriteListAddress(TITLE_SAT_VRAM_ADDR);
    VDP_setWindowOff();
    SYS_enableInts();
}

__attribute__((used, externally_visible, section(".text.patcher")))
void genesistan_hook_text_writer_3bb48_impl(void)
{
    register u16 raw_text_id __asm__("d0");
    const u16 table_index = raw_text_id & 0x7FU;
    const bool space_fill = (raw_text_id & 0x0080U) != 0;
    const u8 *const table = (const u8 *)TEXT_WRITER_3BB48_TABLE_SOURCE;
    const u32 descriptor_ptr = text_writer_read_be32(table + ((u32)table_index << 2));
    const u8 *descriptor;
    u32 dst_ptr;
    const u8 *src;
    u16 attr_word;
    u8 glyph;

    if ((descriptor_ptr == 0U) || (descriptor_ptr >= 0x00800000U))
        return;

    descriptor = (const u8 *)descriptor_ptr;
    dst_ptr    = text_writer_read_be32(descriptor + 0U);
    attr_word  = text_writer_read_be16(descriptor + 4U);
    src        = descriptor + 6U;

    SYS_disableInts();
    while ((glyph = *src++) != 0U)
    {
        s16 x;
        s16 y;
        u32 offset;

        if (text_writer_ptr_to_xy(dst_ptr, &x, &y, &offset))
        {
            const u32 shadow_addr =
                (((u32)genesistan_arcade_workram_words
                  + TEXT_WRITER_SHADOW_PAGE2_OFFSET
                  + offset) & 0x00FFFFFFU);
            const u8 out_glyph = space_fill ? 0x20U : glyph;

            /*
             * Preserve the original 0x03BB48 side effect (text cell staging in RAM)
             * for routines that still read the text backing buffer.
             */
            if (shadow_addr >= 0x00FF0000U)
            {
                volatile u16 *const shadow_cell = (volatile u16 *)shadow_addr;
                shadow_cell[0] = attr_word;
                shadow_cell[1] = (u16)out_glyph;
            }

            rastan_draw_tile_xy(text_writer_build_tile_attr(attr_word, out_glyph), x, y);
        }

        dst_ptr += 4U;
    }
    SYS_enableInts();
}

__attribute__((used, externally_visible, section(".text.patcher")))
void genesistan_render_sprites_vdp(void);

__attribute__((used, externally_visible, section(".text.patcher")))
void genesistan_scroll_from_workram_vdp(void)
{
    const int16_t vertical_bias = RASTAN_VERTICAL_CROP_BIAS;
    const int16_t scroll_y_bg =
        (int16_t)(-(int16_t)genesistan_arcade_workram_words[0x10EEU / 2U] + vertical_bias);
    const int16_t scroll_x_bg =
        -(int16_t)genesistan_arcade_workram_words[0x10ECU / 2U];
    const int16_t scroll_y_fg =
        (int16_t)(-(int16_t)genesistan_arcade_workram_words[0x10B0U / 2U] + vertical_bias);
    const int16_t scroll_x_fg =
        -(int16_t)genesistan_arcade_workram_words[0x10AEU / 2U];

    VDP_setHorizontalScroll(BG_B, scroll_x_bg);
    VDP_setVerticalScroll(BG_B, scroll_y_bg);
    VDP_setHorizontalScroll(BG_A, scroll_x_fg);
    VDP_setVerticalScroll(BG_A, scroll_y_fg);
}

__attribute__((used, externally_visible, section(".text.patcher")))
void genesistan_hook_text_writer_3c3fe(void)
{
    register u16 raw_text_id __asm__("d0");
    const bool space_fill = (raw_text_id & 0x0080U) != 0;
    const u16 table_index = raw_text_id & 0x7FU;
    const u8 *const table = (const u8 *)TEXT_WRITER_3C3FE_TABLE_SOURCE;
    const u8 *const entry = table + ((u32)table_index * 6U);
    u16 count             = text_writer_read_be16(entry + 0U);
    const u16 dst_off     = text_writer_read_be16(entry + 2U);
    const u16 src_off     = text_writer_read_be16(entry + 4U);
    u32 dst_ptr           = TEXT_WRITER_CWINDOW_PAGE2_BASE + (u32)dst_off;
    const u8 *src         = (const u8 *)((u32)genesistan_arcade_workram_words + (u32)src_off);

    SYS_disableInts();
    while (count-- > 0U)
    {
        u16 arcade_tile = (u16)(*src++);
        s16 x;
        s16 y;
        u32 offset;

        if (arcade_tile == 0x003FU)
        {
            arcade_tile = 0x274BU;
        }
        else if (arcade_tile == 0x0021U)
        {
            arcade_tile = 0x2744U;
        }

        if (space_fill)
        {
            arcade_tile = 0x0020U;
        }

        if (text_writer_ptr_to_xy(dst_ptr, &x, &y, &offset))
        {
            (void)offset;
            rastan_draw_tile_xy(text_writer_build_tile_attr_from_arcade_code(0U, arcade_tile), x, y);
        }

        dst_ptr += 4U;
    }
    SYS_enableInts();
}

__attribute__((used, externally_visible, section(".text.patcher")))
void genesistan_hook_frontend_sprite_sat_refresh(void)
{
    genesistan_render_sprites_vdp();
}

__attribute__((used, externally_visible, section(".text.patcher")))
void genesistan_render_sprites_vdp(void)
{
#if RASTAN_ENABLE_STARTUP_HOOK
    const u16 sprite_ctrl = genesistan_arcade_workram_words[10]; /* A5@(20), source for 0x380000 writes */
    const u16 sprite_colbank = (u16)((sprite_ctrl & 0x00E0) >> 1);
    const bool flipscreen = (genesistan_arcade_workram_words[15] != 0); /* A5@(30), paired control for 0xD01BFE path */
    u16 palette_bank_map[FRONTEND_RUNTIME_MAX_PALETTE_BANKS] = {0, 1, 2, 3};
    u16 palette_bank_count = 0;
    u16 unique_count = 0;
    u16 sprite_count = 0;
    const u8 *workram_bytes = (const u8 *)genesistan_arcade_workram_words;
    static const struct
    {
        u16 offset;
        u16 count;
    } sprite_blocks[] =
    {
        /* 0x41F5E: A5+0x11B2, count 18 -> D003C0 */
        {0x11B2, 18},
        /* 0x41F6E: A5+0x0170, count 4 -> D002E0 */
        {0x0170, 4},
    };
    u16 block;

    memset(wram_overlay.launcher.frontend_runtime_sprite_tile_buffer, 0, sizeof(wram_overlay.launcher.frontend_runtime_sprite_tile_buffer));

    /*
     * Title/front-end sprite descriptors come from workram blocks copied by 0x41F5E.
     * Entry layout (validated from 0x41F7A/0x41F8C):
     *   word0: attr/flags
     *   word1: y position (0x0180 sentinel = hidden)
     *   word2: tile code
     *   word3: x position
     */
    for (block = 0; block < (u16)(sizeof(sprite_blocks) / sizeof(sprite_blocks[0])); block++)
    {
        const u8 *entry = workram_bytes + sprite_blocks[block].offset;
        u16 idx;

        for (idx = 0; idx < sprite_blocks[block].count; idx++, entry += 8)
        {
            u16 data = (u16)(((u16)entry[0] << 8) | entry[1]);
            u16 y_raw = (u16)(((u16)entry[2] << 8) | entry[3]);
            const u16 code = (u16)((((u16)entry[4] << 8) | entry[5]) & 0x3FFF);
            const u16 x_raw = (u16)(((u16)entry[6] << 8) | entry[7]);
            s16 x = (s16)(x_raw & 0x01FF);
            s16 y;
            bool flipy = (data & 0x8000) != 0;
            bool flipx = (data & 0x4000) != 0;
            const u16 color = (u16)((data & 0x000F) | sprite_colbank);
            const u16 palette_line = frontend_palette_line_for_bank((u16)(color >> 4), palette_bank_map, &palette_bank_count);
            const s16 tile_base = frontend_runtime_tile_for_code(code, &unique_count);
            const u16 link = (sprite_count >= (FRONTEND_RUNTIME_MAX_SPRITES - 1)) ? 0 : (u16)(sprite_count + 1);
            u16 tile_attr;

            /* Hide only truly empty tuples; valid arcade tuples can have word0 == 0. */
            if ((data == 0) && (y_raw == 0) && (code == 0) && (x_raw == 0))
                y_raw = 0x0180;
            y = (s16)(y_raw & 0x01FF);

            if (tile_base < 0)
            {
                continue;
            }

            if (x > 0x140) x -= 0x0200;
            if (y > 0x140) y -= 0x0200;

            if (flipscreen)
            {
                x = (s16)(320 - x - 16);
                y = (s16)(256 - y - 16);
                flipx = !flipx;
                flipy = !flipy;
            }

            if ((x <= -16) || (x >= 320) || (y <= -16) || (y >= 256))
            {
                continue;
            }

            tile_attr = TILE_ATTR_FULL(palette_line, TRUE, flipy, flipx, (u16)tile_base);

            SYS_disableInts();
            VDP_setSpriteFull(sprite_count, x, y, SPRITE_SIZE(2, 2), tile_attr, (u8)link);
            SYS_enableInts();

            sprite_count++;
            if (sprite_count >= FRONTEND_RUNTIME_MAX_SPRITES)
            {
                break;
            }
        }

        if (sprite_count >= FRONTEND_RUNTIME_MAX_SPRITES)
        {
            break;
        }
    }

    if (unique_count > 0)
    {
        SYS_disableInts();
        VDP_loadTileData(
            (const u32 *)wram_overlay.launcher.frontend_runtime_sprite_tile_buffer,
            FRONTEND_RUNTIME_SPRITE_TILE_BASE,
            unique_count * 4,
            DMA
        );
        VDP_waitDMACompletion();
        SYS_enableInts();
    }

    SYS_disableInts();
    refresh_frontend_sprite_palettes(palette_bank_map, palette_bank_count);
    VDP_updateSprites(sprite_count, DMA);
    VDP_waitDMACompletion();
    SYS_enableInts();
#endif
}

static void render_frontend_sprite_layer(void)
{
    genesistan_render_sprites_vdp();
}

static void leave_startup_preview(void)
{
#if RASTAN_ENABLE_STARTUP_HOOK
    current_screen = SCREEN_CONFIG;
    restore_launcher_vdp_state();
    render_full_screen();
    set_status("READY");
#endif
}

static void render_all_menu_rows(void)
{
    u16 i;

    for (i = 0; i < MENU_COUNT; i++)
    {
        render_menu_row((u8) i);
    }
}

static void apply_factory_defaults(void)
{
    save_undo_state();
    rastan_virtual_dip1 = FACTORY_DIP1;
    rastan_virtual_dip2 = FACTORY_DIP2;
}

static void apply_competition_settings(void)
{
    save_undo_state();

    /*
     * Arcade competition settings match the default board DIP positions:
     * BANK1: 10000000
     * BANK2: 00000000
     *
     * In the raw active-low bytes used by the game code, that is the same as
     * the factory defaults.
     */
    rastan_virtual_dip1 = FACTORY_DIP1;
    rastan_virtual_dip2 = FACTORY_DIP2;
}

static bool menu_controls_switch(u8 menu_index, bool bank2, u8 bit)
{
    switch (menu_index)
    {
        case 0: return !bank2 && (bit == 0);
        case 1: return !bank2 && (bit == 1);
        case 2: return !bank2 && (bit == 2);
        case 3: return !bank2 && (bit >= 4) && (bit <= 7);
        case 4: return bank2 && (bit <= 1);
        case 5: return bank2 && (bit >= 2) && (bit <= 3);
        case 6: return bank2 && (bit >= 4) && (bit <= 5);
        case 7: return bank2 && (bit == 6);
        default: return FALSE;
    }
}

static void activate_selected_menu(void)
{
    switch (selected_menu)
    {
        case 8:
            apply_competition_settings();
            render_dip_banks();
            render_all_menu_rows();
            render_help_panel();
            set_status("COMPETITION SETTINGS APPLIED");
            break;
        case 9:
            apply_factory_defaults();
            render_dip_banks();
            render_all_menu_rows();
            render_help_panel();
            set_status("FACTORY DEFAULTS RESTORED");
            break;
        case 10:
            enter_graphics_test();
            break;
        case 11:
            enter_sound_test();
            break;
        case 12:
            request_start_rastan();
            break;
        default:
            break;
    }
}

static void request_start_rastan(void)
{
#if RASTAN_ENABLE_STARTUP_HOOK
    scrub_launcher_runtime_buffers();
    genesistan_reclaim_launcher_wram();
    genesistan_init_workram_direct(
        rastan_virtual_dip1,
        rastan_virtual_dip2);
    restore_launcher_vdp_state();
    current_screen = SCREEN_FRONTEND_LIVE;
    frontend_live_handoff_active = TRUE;
    SYS_setVIntCallback(genesistan_frontend_live_vint_handoff);
    SYS_enableInts();
    VDP_setHInterrupt(0);
    VDP_setHIntCounter(0xFF);
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    genesistan_sync_title_vdp_layout();
    clear_frontend_sprite_layer();
    VDP_waitDMACompletion();
#else
    char line[SCREEN_W + 1];

    sprintf(line, "PACKED ROMSET %luk SIG %04lX",
            (unsigned long)(get_packed_romset_size() / 1024UL),
            (unsigned long)(get_packed_romset_signature() & 0xFFFFUL));
    set_status(line);
#endif
}

static void scrub_launcher_runtime_buffers(void)
{
    if (graphics_test_tile_buffer != NULL)
    {
        MEM_free(graphics_test_tile_buffer);
        graphics_test_tile_buffer = NULL;
    }

}

static u32 get_packed_romset_size(void)
{
    return (u32) sizeof(rastan_maincpu)
         + (u32) sizeof(rastan_audiocpu)
         + (u32) sizeof(rastan_adpcm)
         + (u32) sizeof(rastan_pc080sn)
         + (u32) sizeof(rastan_pc090oj);
}

static u32 get_packed_romset_signature(void)
{
    u32 signature = 0;

    signature += rastan_maincpu[0];
    signature += rastan_maincpu[sizeof(rastan_maincpu) - 1];
    signature += rastan_audiocpu[0];
    signature += rastan_audiocpu[sizeof(rastan_audiocpu) - 1];
    signature += rastan_adpcm[0];
    signature += rastan_adpcm[sizeof(rastan_adpcm) - 1];
    signature += rastan_pc080sn[0];
    signature += rastan_pc080sn[sizeof(rastan_pc080sn) - 1];
    signature += rastan_pc090oj[0];
    signature += rastan_pc090oj[sizeof(rastan_pc090oj) - 1];

    return signature;
}

static void reset_launcher_runtime_state(void)
{
    /* Always start the launcher from known factory defaults. */
    frontend_live_handoff_active = FALSE;
    SYS_setVIntCallback(NULL);
    rastan_virtual_dip1 = FACTORY_DIP1;
    rastan_virtual_dip2 = FACTORY_DIP2;
    selected_menu = 0;
    undo_state.dip1 = 0;
    undo_state.dip2 = 0;
    undo_state.valid = FALSE;
    current_screen = SCREEN_CONFIG;
    graphics_page = 0;
    graphics_region = GRAPHICS_REGION_PC080SN;
    rastan_virtual_sound_command = 0x00;
    rastan_virtual_sound_pending = FALSE;
    sound_test_last_command = 0x00;
    sound_test_has_triggered = FALSE;
    strncpy(wram_overlay.launcher.status_line, "READY", SCREEN_W);
    wram_overlay.launcher.status_line[SCREEN_W] = '\0';
}

static void sanitize_arcade_workram(void)
{
    /*
     * After each frontend tick, scan the arcade
     * workram for any LONG values that fall in
     * the C-Window address range 0xC00000-0xC0FFFF.
     * These are display list / tile data pointers
     * that are valid on arcade hardware but map to
     * non-executable SRAM on Genesis (BlastEm crash).
     *
     * Zero them out so the arcade code uses address
     * 0x000000 (ROM) as a fallback instead of SRAM.
     * This is a stability bridge until full opcode
     * replacement covers all C-Window pointer stores.
     *
     * Scan as LONGs (2 words each). The workram is
     * 0x2000 words = 0x1000 LONGs.
     */
    uint16_t i;
    volatile uint32_t *wram32 =
        (volatile uint32_t *)genesistan_arcade_workram_words;
    const uint16_t count = sizeof(genesistan_arcade_workram_words)
                           / sizeof(uint32_t);

    for (i = 0; i < count; i++) {
        uint32_t v = wram32[i];
        if ((v & 0x00FF0000UL) == 0x00C00000UL) {
            wram32[i] = 0;
        }
    }
}

static void sync_arcade_scroll_to_vdp(void)
{
    genesistan_scroll_from_workram_vdp();
}

static void genesistan_frontend_live_vint_handoff(void)
{
#if RASTAN_ENABLE_STARTUP_HOOK
    if (!frontend_live_handoff_active || (current_screen != SCREEN_FRONTEND_LIVE))
    {
        return;
    }

    /* Post-launch frame ownership: arcade level-5 tick runs from V-Int only. */
    genesistan_refresh_arcade_inputs();
    genesistan_run_original_frontend_tick();
#endif
}

int main(bool hardReset)
{
    u16 previous_state = 0;

    (void) hardReset;

    SYS_disableInts();

    packed_romset_size_cache = get_packed_romset_size();
    packed_romset_signature_cache = get_packed_romset_signature();
    reset_launcher_runtime_state();
    restore_launcher_vdp_state();

    render_full_screen();

    while (TRUE)
    {
        const u16 state = JOY_readJoypad(JOY_1);
        const u16 pressed = state & ~previous_state;

        if (current_screen == SCREEN_GRAPHICS_TEST)
        {
            const u16 page_count = get_graphics_test_page_count();
            const u16 max_page = (page_count == 0) ? 0 : (page_count - 1);

            if ((pressed & BUTTON_A) != 0)
            {
                graphics_region = (graphics_region == GRAPHICS_REGION_PC080SN) ? GRAPHICS_REGION_PC090OJ : GRAPHICS_REGION_PC080SN;
                graphics_page = 0;
                render_graphics_test_screen();
            }
            else if ((pressed & (BUTTON_B | BUTTON_C | BUTTON_START)) != 0)
            {
                leave_graphics_test();
            }
            else if ((pressed & BUTTON_LEFT) != 0)
            {
                graphics_page = (graphics_page == 0) ? max_page : (graphics_page - 1);
                render_graphics_test_screen();
            }
            else if ((pressed & BUTTON_RIGHT) != 0)
            {
                graphics_page = (graphics_page >= max_page) ? 0 : (graphics_page + 1);
                render_graphics_test_screen();
            }
            else if ((pressed & BUTTON_UP) != 0)
            {
                graphics_page = (graphics_page >= 10) ? (graphics_page - 10) : 0;
                render_graphics_test_screen();
            }
            else if ((pressed & BUTTON_DOWN) != 0)
            {
                const u16 next_page = graphics_page + 10;
                graphics_page = (next_page > max_page) ? max_page : next_page;
                render_graphics_test_screen();
            }
        }
        else if (current_screen == SCREEN_FRONTEND_LIVE)
        {
            /*
             * Ownership handoff: launcher loop no longer drives live-frame
             * progression or post-launch display updates.
             */
        }
        else if (current_screen == SCREEN_STARTUP_PREVIEW)
        {
            if ((pressed & (BUTTON_A | BUTTON_START)) != 0)
            {
                request_start_rastan();
            }
            else if ((pressed & (BUTTON_B | BUTTON_C)) != 0)
            {
                leave_startup_preview();
            }
        }
        else if (current_screen == SCREEN_SOUND_TEST)
        {
            if ((pressed & BUTTON_START) != 0)
            {
                leave_sound_test();
            }
            else if ((pressed & BUTTON_LEFT) != 0)
            {
                rastan_virtual_sound_command--;
                render_sound_test_screen();
            }
            else if ((pressed & BUTTON_RIGHT) != 0)
            {
                rastan_virtual_sound_command++;
                render_sound_test_screen();
            }
            else if ((pressed & BUTTON_UP) != 0)
            {
                rastan_virtual_sound_command = (u8)(rastan_virtual_sound_command + 0x10);
                render_sound_test_screen();
            }
            else if ((pressed & BUTTON_DOWN) != 0)
            {
                rastan_virtual_sound_command = (u8)(rastan_virtual_sound_command - 0x10);
                render_sound_test_screen();
            }
            else if ((pressed & (BUTTON_A | BUTTON_B | BUTTON_C)) != 0)
            {
                trigger_sound_test_command();
            }
        }
        else if (pressed & BUTTON_UP)
        {
            const u8 previous_menu = selected_menu;
            selected_menu = (selected_menu == 0) ? (MENU_COUNT - 1) : (selected_menu - 1);
            render_dip_banks();
            render_menu_row(previous_menu);
            render_menu_row(selected_menu);
            render_help_panel();
            set_status("SELECTION MOVED");
        }
        else if (pressed & BUTTON_DOWN)
        {
            const u8 previous_menu = selected_menu;
            selected_menu = (selected_menu + 1) % MENU_COUNT;
            render_dip_banks();
            render_menu_row(previous_menu);
            render_menu_row(selected_menu);
            render_help_panel();
            set_status("SELECTION MOVED");
        }
        else if (pressed & (BUTTON_LEFT | BUTTON_RIGHT))
        {
            if (!menu_item_is_action(selected_menu))
            {
                cycle_selected_setting((pressed & BUTTON_LEFT) != 0);
            }
        }
        else if (pressed & (BUTTON_A | BUTTON_B | BUTTON_C))
        {
            if (menu_item_is_action(selected_menu))
            {
                activate_selected_menu();
            }
            else
            {
                cycle_selected_setting(FALSE);
            }
        }
        else if (pressed & BUTTON_START)
        {
            request_start_rastan();
        }

        previous_state = state;
        if (current_screen != SCREEN_FRONTEND_LIVE)
        {
            SYS_doVBlankProcess();
        }
    }

    return 0;
}
