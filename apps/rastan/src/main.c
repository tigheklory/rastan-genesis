#include <genesis.h>
#include <string.h>

#include "main.h"
#include "res_ui.h"

#define SCREEN_W 40
#define FACTORY_DIP1 0xFE
#define FACTORY_DIP2 0xFF
#define MENU_COUNT 8
#define DIP_TILE_ON_INDEX TILE_USER_INDEX
#define DIP_TILE_OFF_INDEX (TILE_USER_INDEX + 2)

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

static const MenuItem menu_items[MENU_COUNT] = {
    {"CABINET TYPE", cabinet_values, "CABINET ORIENTATION FOR THE GAME.", "SW1 1", 2},
    {"MONITOR", monitor_values, "FLIPS MONITOR DISPLAY DIRECTION.", "SW1 2", 2},
    {"GAME MODE", game_mode_values, "NORMAL GAME OR BOARD TEST MODE.", "SW1 3", 2},
    {"COINAGE", coinage_values, "PRICING FOR CREDITS AND COINS.", "SW1 5-8", 4},
    {"DIFFICULTY", difficulty_values, "OVERALL GAME DIFFICULTY LEVEL.", "SW2 1-2", 4},
    {"BONUS LIFE", bonus_values, "SCORE NEEDED FOR BONUS LIFE.", "SW2 3-4", 4},
    {"LIVES", lives_values, "STARTING LIVES FOR EACH CREDIT.", "SW2 5-6", 4},
    {"CONTINUE", continue_values, "ALLOW CONTINUE AFTER GAME OVER.", "SW2 7", 2},
};

volatile u8 rastan_virtual_dip1 = FACTORY_DIP1;
volatile u8 rastan_virtual_dip2 = FACTORY_DIP2;
static u8 selected_menu = 0;
static UndoState undo_state = {0, 0, FALSE};
static char status_line[SCREEN_W + 1] = "READY";
static u32 rastan_font_data[FONT_LEN * 8];

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
    u8 *dst = (u8 *) rastan_font_data;

    memset(rastan_font_data, 0, sizeof(rastan_font_data));

    for (i = 0; i < sizeof(rastan_font_glyphs) / sizeof(rastan_font_glyphs[0]); i++)
    {
        const u8 code = rastan_font_glyphs[i].code;
        const u32 src_offset = (u32) rastan_font_glyphs[i].src_tile * 32;
        const u32 dst_offset = (u32) (code - 32) * 32;

        memcpy(dst + dst_offset, rastan_pc080sn + src_offset, 32);
    }
}

static void draw_padded_text_palette(const char *text, u16 x, u16 y, u16 width, u16 palette);
static bool menu_controls_switch(u8 menu_index, bool bank2, u8 bit);

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
    strncpy(status_line, text, SCREEN_W);
    status_line[SCREEN_W] = '\0';
    draw_padded_text(status_line, 0, 25, SCREEN_W);
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
        case 2: return get_bit(rastan_virtual_dip1, 2) ? 1 : 0;
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
        case 2: set_bit((u8 *) &rastan_virtual_dip1, 2, next_value ? 1 : 0); break;
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

    draw_padded_text(title, title_x, 3, 12);
    draw_padded_text("ON", label_x, 4, 3);
    draw_padded_text("OFF", label_x, 5, 3);

    for (i = 0; i < 8; i++)
    {
        draw_dip_icon((u16)(icon_x + (i * 2)), 4, ((bank_value >> i) & 1) == 0, menu_controls_switch(selected_menu, bank2, i));
    }
}

static void render_dip_banks(void)
{
    VDP_fillTileMapRect(BG_A, TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, TILE_FONT_INDEX), 0, 3, SCREEN_W, 3);
    render_dip_bank(rastan_virtual_dip1, FALSE, 2, 0, 4, "DIP SWITCH 1");
    render_dip_bank(rastan_virtual_dip2, TRUE, 24, 21, 25, "DIP SWITCH 2");
}

static void render_menu_row(u8 index)
{
    char line[SCREEN_W + 1];
    const MenuItem *item = &menu_items[index];
    const u8 value = get_menu_value(index);

    sprintf(line, "%c %-13s %-11s", (index == selected_menu) ? ')' : ' ', item->label, item->values[value]);
    draw_padded_text_palette(line, 1, (u16)(8 + index), 27, (index == selected_menu) ? PAL3 : PAL1);
}

static void render_help_panel(void)
{
    const MenuItem *item = &menu_items[selected_menu];
    char line[SCREEN_W + 1];

    sprintf(line, "HELP: %-28s", item->switches);
    draw_padded_text(line, 0, 17, SCREEN_W);
    draw_padded_text(item->help_text, 0, 18, SCREEN_W);
    draw_padded_text("", 0, 19, SCREEN_W);
    draw_padded_text("(UP DOWN) MOVE (LEFT RIGHT) CHANGE", 0, 20, SCREEN_W);
    draw_padded_text("(A) COMPETITION SETTINGS", 0, 21, SCREEN_W);
    draw_padded_text("(B) UNDO  (C) FACTORY DEFAULTS", 0, 22, SCREEN_W);
    draw_padded_text("(START) RUN RASTAN", 0, 23, SCREEN_W);
}

static void render_static_layout(void)
{
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);

    draw_padded_text("RASTAN STARTUP CONFIG", 9, 0, 22);
    draw_padded_text("WORLD REV1 BASELINE UI", 8, 1, 24);
    draw_padded_text("SETTINGS", 1, 7, 8);
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
    set_status(status_line);
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

static void undo_last_change(void)
{
    if (undo_state.valid)
    {
        const u8 prev_dip1 = rastan_virtual_dip1;
        const u8 prev_dip2 = rastan_virtual_dip2;

        rastan_virtual_dip1 = undo_state.dip1;
        rastan_virtual_dip2 = undo_state.dip2;
        undo_state.dip1 = prev_dip1;
        undo_state.dip2 = prev_dip2;
        undo_state.valid = FALSE;
    }
}

int main(bool hardReset)
{
    u16 previous_state = 0;

    (void) hardReset;

    SYS_disableInts();

    VDP_setScreenWidth320();
    PAL_setPalette(PAL0, rastan_active_dip_palette, CPU);
    PAL_setPalette(PAL1, rastan_font_palette, CPU);
    PAL_setPalette(PAL2, rastan_dip_palette.data, CPU);
    PAL_setPalette(PAL3, rastan_selected_font_palette, CPU);
    VDP_setTextPalette(PAL1);
    build_rastan_font();
    VDP_loadFontData(rastan_font_data, FONT_LEN, CPU);
    VDP_loadTileSet(&rastan_dip_on, DIP_TILE_ON_INDEX, CPU);
    VDP_loadTileSet(&rastan_dip_off, DIP_TILE_OFF_INDEX, CPU);

    render_full_screen();

    SYS_enableInts();

    while (TRUE)
    {
        const u16 state = JOY_readJoypad(JOY_1);
        const u16 pressed = state & ~previous_state;

        if (pressed & BUTTON_UP)
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
            const u8 current_value = get_menu_value(selected_menu);
            const u8 count = menu_items[selected_menu].value_count;
            const bool backwards = (pressed & BUTTON_LEFT) != 0;
            const u8 next_value = backwards ? ((current_value == 0) ? (count - 1) : (current_value - 1))
                                            : ((current_value + 1) % count);

            set_menu_value(selected_menu, next_value);
            render_dip_banks();
            render_menu_row(selected_menu);
            render_help_panel();
            set_status("SETTING UPDATED");
        }
        else if (pressed & BUTTON_A)
        {
            apply_competition_settings();
            render_dip_banks();
            render_all_menu_rows();
            render_help_panel();
            set_status("COMPETITION SETTINGS APPLIED");
        }
        else if (pressed & BUTTON_B)
        {
            undo_last_change();
            render_dip_banks();
            render_all_menu_rows();
            render_help_panel();
            set_status("LAST CHANGE UNDONE");
        }
        else if (pressed & BUTTON_C)
        {
            apply_factory_defaults();
            render_dip_banks();
            render_all_menu_rows();
            render_help_panel();
            set_status("FACTORY DEFAULTS RESTORED");
        }
        else if (pressed & BUTTON_START)
        {
            set_status("START REQUESTED - GAME LAUNCH NOT HOOKED YET");
        }

        previous_state = state;
        SYS_doVBlankProcess();
    }

    return 0;
}
