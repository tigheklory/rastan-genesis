#include <genesis.h>

#include "main.h"

#define SCREEN_COLS 40
#define SCREEN_ROWS 28

typedef enum MenuOptionId
{
    MENU_CABINET = 0,
    MENU_MONITOR_REVERSE,
    MENU_GAME_MODE,
    MENU_COINAGE,
    MENU_DIFFICULTY,
    MENU_BONUS_LIFE,
    MENU_LIVES,
    MENU_CONTINUE,
    MENU_COUNT
} MenuOptionId;

typedef struct MenuOption
{
    const char* label;
    const char* const* values;
    u16 value_count;
    const char* description;
    const char* switches;
} MenuOption;

static const u16 text_palette[16] = {
    RGB24_TO_VDPCOLOR(0x000000), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xB0B0B0), RGB24_TO_VDPCOLOR(0x808080),
    RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF),
    RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF),
    RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF),
};

static const char* const cabinet_values[] = { "UPRIGHT", "COCKTAIL" };
static const char* const monitor_values[] = { "OFF", "ON" };
static const char* const game_mode_values[] = { "NORMAL", "TEST" };
static const char* const coinage_values[] = { "1C 1C", "1C 2C", "2C 1C", "2C 3C" };
static const char* const difficulty_values[] = { "EASIEST", "EASY", "DIFFICULT", "HARDEST" };
static const char* const bonus_values[] = { "100000", "150000", "200000", "250000" };
static const char* const lives_values[] = { "3", "4", "5", "6" };
static const char* const continue_values[] = { "ON", "OFF" };

static const MenuOption menu_options[MENU_COUNT] = {
    { "CABINET TYPE", cabinet_values, 2, "Select upright or cocktail cabinet mode.", "SWITCHES: SW1-1" },
    { "MONITOR REVERSE", monitor_values, 2, "Mirror the display for reversed monitor wiring.", "SWITCHES: SW1-2" },
    { "GAME MODE", game_mode_values, 2, "Choose the normal game path or diagnostics.", "SWITCHES: SW1-3" },
    { "COINAGE", coinage_values, 4, "Set how many coins are needed for credits.", "SWITCHES: SW1-5 SW1-6 SW1-7 SW1-8" },
    { "DIFFICULTY", difficulty_values, 4, "Adjust enemy and progression difficulty.", "SWITCHES: SW2-1 SW2-2" },
    { "BONUS LIFE", bonus_values, 4, "Choose the score threshold for bonus lives.", "SWITCHES: SW2-3 SW2-4" },
    { "LIVES", lives_values, 4, "Select the starting number of player lives.", "SWITCHES: SW2-5 SW2-6" },
    { "CONTINUE", continue_values, 2, "Enable or disable continues after death.", "SWITCHES: SW2-7" },
};

volatile uint16_t genesistan_shadow_200000_words[0x400];
volatile uint16_t genesistan_arcade_workram_words[0x2000];
volatile uint16_t genesistan_shadow_d00000_words[0x400];
volatile uint16_t genesistan_shadow_c00000_words[0x800];
volatile uint16_t genesistan_shadow_c08000_words[0x2000];
volatile uint16_t genesistan_shadow_c04000_words[0x1000];
volatile uint16_t genesistan_shadow_c0c000_words[0x1000];
volatile uint16_t genesistan_shadow_c20000_words[2];
volatile uint16_t genesistan_shadow_c40000_words[2];
volatile uint16_t genesistan_shadow_reg_c50000;
volatile uint16_t genesistan_shadow_reg_d01bfe;
volatile uint16_t genesistan_shadow_reg_350008;
volatile uint16_t genesistan_shadow_reg_380000;
volatile uint16_t genesistan_shadow_reg_3c0000;
volatile uint8_t genesistan_shadow_reg_3e0001;
volatile uint8_t genesistan_shadow_reg_3e0003;
volatile uint8_t genesistan_shadow_dip1 = GENESISTAN_DIP1_FACTORY;
volatile uint8_t genesistan_shadow_dip2 = GENESISTAN_DIP2_FACTORY;
volatile uint16_t genesistan_shadow_service_word = GENESISTAN_SERVICE_FACTORY;
volatile uint16_t genesistan_startup_result_code = GENESISTAN_STARTUP_RESULT_NONE;
volatile uint16_t genesistan_panic_code;
volatile uint32_t genesistan_panic_original_sp;
volatile uint16_t genesistan_panic_frame_words[8];
volatile uint16_t genesistan_panic_entered;
volatile uint8_t genesistan_exception_stack[512];

static u8 dip_bank1 = GENESISTAN_DIP1_FACTORY;
static u8 dip_bank2 = GENESISTAN_DIP2_FACTORY;
static u8 undo_bank1 = GENESISTAN_DIP1_FACTORY;
static u8 undo_bank2 = GENESISTAN_DIP2_FACTORY;
static bool can_undo = FALSE;
static u16 menu_cursor = 0;
static u16 previous_pad = 0;
static bool screen_dirty = TRUE;
static char status_line[SCREEN_COLS + 1];

static void fill_words(volatile uint16_t* words, u16 count, u16 value)
{
    u16 i;

    for (i = 0; i < count; i++) words[i] = value;
}

void genesistan_reset_startup_shadows(uint8_t dip1, uint8_t dip2, uint16_t service_word)
{
    fill_words(genesistan_shadow_200000_words, 0x400, 0);
    fill_words(genesistan_arcade_workram_words, 0x2000, 0);
    fill_words(genesistan_shadow_d00000_words, 0x400, 0);
    fill_words(genesistan_shadow_c00000_words, 0x800, 0);
    fill_words(genesistan_shadow_c08000_words, 0x2000, 0);
    fill_words(genesistan_shadow_c04000_words, 0x1000, 0);
    fill_words(genesistan_shadow_c0c000_words, 0x1000, 0);
    fill_words(genesistan_shadow_c20000_words, 2, 0);
    fill_words(genesistan_shadow_c40000_words, 2, 0);
    fill_words(genesistan_panic_frame_words, 8, 0);

    genesistan_shadow_reg_c50000 = 0;
    genesistan_shadow_reg_d01bfe = 0;
    genesistan_shadow_reg_350008 = 0;
    genesistan_shadow_reg_380000 = 0;
    genesistan_shadow_reg_3c0000 = 0;
    genesistan_shadow_reg_3e0001 = 0;
    genesistan_shadow_reg_3e0003 = 0;
    genesistan_shadow_dip1 = dip1;
    genesistan_shadow_dip2 = dip2;
    genesistan_shadow_service_word = service_word;
    genesistan_startup_result_code = GENESISTAN_STARTUP_RESULT_NONE;
    genesistan_panic_code = 0;
    genesistan_panic_original_sp = 0;
    genesistan_panic_entered = 0;
}

static void set_status(const char* text)
{
    strncpy(status_line, text, SCREEN_COLS);
    status_line[SCREEN_COLS] = 0;
    screen_dirty = TRUE;
}

static void sync_shadow_dips(void)
{
    genesistan_shadow_dip1 = dip_bank1;
    genesistan_shadow_dip2 = dip_bank2;
}

static u8 get_masked_value(u8 value, u8 mask, u8 shift)
{
    return (value >> shift) & mask;
}

static void set_masked_value(u8* value, u8 mask, u8 shift, u8 raw)
{
    *value = (*value & ~(mask << shift)) | ((raw & mask) << shift);
}

static void snapshot_for_undo(void)
{
    undo_bank1 = dip_bank1;
    undo_bank2 = dip_bank2;
    can_undo = TRUE;
}

static u16 option_value(MenuOptionId option)
{
    static const u8 coinage_raw[4] = { 0x0F, 0x0A, 0x05, 0x00 };
    static const u8 difficulty_raw[4] = { 0x02, 0x03, 0x01, 0x00 };
    static const u8 bonus_raw[4] = { 0x03, 0x02, 0x01, 0x00 };
    static const u8 lives_raw[4] = { 0x03, 0x02, 0x01, 0x00 };
    const u8* table = NULL;
    u16 count = 0;
    u8 raw = 0;
    u16 i;

    switch (option)
    {
        case MENU_CABINET: return (dip_bank1 & 0x01) ? 1 : 0;
        case MENU_MONITOR_REVERSE: return (dip_bank1 & 0x02) ? 0 : 1;
        case MENU_GAME_MODE: return (dip_bank1 & 0x04) ? 0 : 1;
        case MENU_COINAGE:
            table = coinage_raw;
            count = 4;
            raw = get_masked_value(dip_bank1, 0x0F, 4);
            break;
        case MENU_DIFFICULTY:
            table = difficulty_raw;
            count = 4;
            raw = get_masked_value(dip_bank2, 0x03, 0);
            break;
        case MENU_BONUS_LIFE:
            table = bonus_raw;
            count = 4;
            raw = get_masked_value(dip_bank2, 0x03, 2);
            break;
        case MENU_LIVES:
            table = lives_raw;
            count = 4;
            raw = get_masked_value(dip_bank2, 0x03, 4);
            break;
        case MENU_CONTINUE: return (dip_bank2 & 0x40) ? 0 : 1;
        default: return 0;
    }

    for (i = 0; i < count; i++)
    {
        if (table[i] == raw) return i;
    }

    return 0;
}

static void set_option_value(MenuOptionId option, u16 selection)
{
    static const u8 coinage_raw[4] = { 0x0F, 0x0A, 0x05, 0x00 };
    static const u8 difficulty_raw[4] = { 0x02, 0x03, 0x01, 0x00 };
    static const u8 bonus_raw[4] = { 0x03, 0x02, 0x01, 0x00 };
    static const u8 lives_raw[4] = { 0x03, 0x02, 0x01, 0x00 };

    switch (option)
    {
        case MENU_CABINET:
            if (selection == 0) dip_bank1 &= ~0x01;
            else dip_bank1 |= 0x01;
            break;
        case MENU_MONITOR_REVERSE:
            if (selection == 0) dip_bank1 |= 0x02;
            else dip_bank1 &= ~0x02;
            break;
        case MENU_GAME_MODE:
            if (selection == 0) dip_bank1 |= 0x04;
            else dip_bank1 &= ~0x04;
            break;
        case MENU_COINAGE:
            set_masked_value(&dip_bank1, 0x0F, 4, coinage_raw[selection]);
            break;
        case MENU_DIFFICULTY:
            set_masked_value(&dip_bank2, 0x03, 0, difficulty_raw[selection]);
            break;
        case MENU_BONUS_LIFE:
            set_masked_value(&dip_bank2, 0x03, 2, bonus_raw[selection]);
            break;
        case MENU_LIVES:
            set_masked_value(&dip_bank2, 0x03, 4, lives_raw[selection]);
            break;
        case MENU_CONTINUE:
            if (selection == 0) dip_bank2 |= 0x40;
            else dip_bank2 &= ~0x40;
            break;
        default:
            break;
    }
}

static void line_clear(char* line)
{
    u16 i;

    for (i = 0; i < SCREEN_COLS; i++) line[i] = ' ';
    line[SCREEN_COLS] = 0;
}

static void line_put_text(char* line, s16 x, const char* text)
{
    while (*text && (x < SCREEN_COLS))
    {
        if (x >= 0) line[x] = *text;
        x++;
        text++;
    }
}

static void line_put_centered(char* line, const char* text)
{
    const s16 len = strlen(text);
    const s16 x = (SCREEN_COLS - len) / 2;

    line_put_text(line, x, text);
}

static void format_switch_pattern(char* out, u8 dip, bool active_row)
{
    u16 i;

    out[0] = 0;
    for (i = 0; i < 8; i++)
    {
        const bool active = (dip & (1u << i)) == 0;
        const char glyph = (active_row ? active : !active) ? '#' : '.';
        const u16 len = strlen(out);

        out[len] = glyph;
        out[len + 1] = ' ';
        out[len + 2] = 0;
    }
}

static void draw_menu_row(u16 row, MenuOptionId option)
{
    char line[SCREEN_COLS + 1];

    line_clear(line);
    line_put_text(line, 0, (option == menu_cursor) ? "> " : "  ");
    line_put_text(line, 2, menu_options[option].label);
    line_put_text(line, 26, menu_options[option].values[option_value(option)]);
    VDP_drawText(line, 0, row);
}

static void render_screen(void)
{
    char line[SCREEN_COLS + 1];
    char pattern[24];
    u16 row;

    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);

    line_clear(line);
    line_put_centered(line, "RASTAN STARTUP CONFIG");
    VDP_drawText(line, 0, 0);

    line_clear(line);
    line_put_text(line, 0, "DIP SWITCH BANK 1");
    VDP_drawText(line, 0, 2);

    pattern[0] = 0;
    format_switch_pattern(pattern, dip_bank1, TRUE);
    line_clear(line);
    line_put_text(line, 0, "ON  ");
    line_put_text(line, 4, pattern);
    VDP_drawText(line, 0, 3);

    pattern[0] = 0;
    format_switch_pattern(pattern, dip_bank1, FALSE);
    line_clear(line);
    line_put_text(line, 0, "OFF ");
    line_put_text(line, 4, pattern);
    VDP_drawText(line, 0, 4);

    VDP_drawText("    1 2 3 4 5 6 7 8", 0, 5);

    line_clear(line);
    line_put_text(line, 0, "DIP SWITCH BANK 2");
    VDP_drawText(line, 0, 7);

    pattern[0] = 0;
    format_switch_pattern(pattern, dip_bank2, TRUE);
    line_clear(line);
    line_put_text(line, 0, "ON  ");
    line_put_text(line, 4, pattern);
    VDP_drawText(line, 0, 8);

    pattern[0] = 0;
    format_switch_pattern(pattern, dip_bank2, FALSE);
    line_clear(line);
    line_put_text(line, 0, "OFF ");
    line_put_text(line, 4, pattern);
    VDP_drawText(line, 0, 9);

    VDP_drawText("    1 2 3 4 5 6 7 8", 0, 10);
    VDP_drawText("SETTINGS", 0, 12);

    for (row = 0; row < MENU_COUNT; row++) draw_menu_row(13 + row, (MenuOptionId) row);

    line_clear(line);
    line_put_text(line, 0, "STATUS: ");
    line_put_text(line, 8, status_line);
    VDP_drawText(line, 0, 22);

    VDP_drawText("A/LEFT/RIGHT CHANGE   B UNDO", 0, 23);
    VDP_drawText("C FACTORY RESET       START RUN", 0, 24);

    line_clear(line);
    line_put_text(line, 0, menu_options[menu_cursor].description);
    VDP_drawText(line, 0, 25);

    line_clear(line);
    line_put_text(line, 0, menu_options[menu_cursor].switches);
    VDP_drawText(line, 0, 26);

    line_clear(line);
    line_put_text(line, 0, "BANK1 ");
    line[6] = "0123456789ABCDEF"[dip_bank1 >> 4];
    line[7] = "0123456789ABCDEF"[dip_bank1 & 0x0F];
    line_put_text(line, 11, "BANK2 ");
    line[17] = "0123456789ABCDEF"[dip_bank2 >> 4];
    line[18] = "0123456789ABCDEF"[dip_bank2 & 0x0F];
    line_put_text(line, 22, can_undo ? "UNDO READY" : "UNDO EMPTY");
    VDP_drawText(line, 0, 27);

    screen_dirty = FALSE;
}

static void change_selected_option(s16 delta)
{
    const MenuOptionId option = (MenuOptionId) menu_cursor;
    const MenuOption* meta = &menu_options[option];
    u16 value = option_value(option);
    s16 next = (s16) value + delta;

    snapshot_for_undo();

    if (next < 0) next = meta->value_count - 1;
    if (next >= (s16) meta->value_count) next = 0;

    set_option_value(option, (u16) next);
    sync_shadow_dips();
    set_status("SETTING UPDATED");
}

static void factory_reset(void)
{
    snapshot_for_undo();
    dip_bank1 = GENESISTAN_DIP1_FACTORY;
    dip_bank2 = GENESISTAN_DIP2_FACTORY;
    sync_shadow_dips();
    set_status("FACTORY DEFAULTS RESTORED");
}

static void undo_last_change(void)
{
    if (!can_undo)
    {
        set_status("NOTHING TO UNDO");
        return;
    }

    dip_bank1 = undo_bank1;
    dip_bank2 = undo_bank2;
    sync_shadow_dips();
    can_undo = FALSE;
    set_status("LAST CHANGE REVERTED");
}

static void launch_stub(void)
{
    set_status("START REQUESTED - GAME LAUNCH NOT HOOKED YET");
}

static void handle_button_press(u16 pressed)
{
    if (pressed & BUTTON_UP)
    {
        if (menu_cursor == 0) menu_cursor = MENU_COUNT - 1;
        else menu_cursor--;
        screen_dirty = TRUE;
    }

    if (pressed & BUTTON_DOWN)
    {
        menu_cursor = (menu_cursor + 1) % MENU_COUNT;
        screen_dirty = TRUE;
    }

    if (pressed & BUTTON_LEFT) change_selected_option(-1);
    if ((pressed & BUTTON_RIGHT) || (pressed & BUTTON_A)) change_selected_option(1);
    if (pressed & BUTTON_B) undo_last_change();
    if (pressed & BUTTON_C) factory_reset();
    if (pressed & BUTTON_START) launch_stub();
}

void genesistan_exception_enter(void)
{
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    VDP_drawText("GENESISTAN PANIC", 11, 12);
    VDP_drawText("RESTART ROM TO RECOVER", 9, 14);

    while (TRUE)
    {
        SYS_doVBlankProcess();
    }
}

int main(bool hardReset)
{
    const u16 unused_hard_reset = hardReset;

    (void) unused_hard_reset;

    SYS_disableInts();

    VDP_setScreenWidth320();
    PAL_setPalette(PAL0, palette_black, CPU);
    VDP_setTextPalette(PAL1);
    PAL_setPalette(PAL1, text_palette, CPU);
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    JOY_init();

    genesistan_reset_startup_shadows(dip_bank1, dip_bank2, GENESISTAN_SERVICE_FACTORY);
    strncpy(status_line, "READY", SCREEN_COLS);
    status_line[SCREEN_COLS] = 0;
    screen_dirty = TRUE;

    SYS_enableInts();

    while (TRUE)
    {
        const u16 pad = JOY_readJoypad(JOY_1);
        const u16 pressed = pad & ~previous_pad;

        if (pressed) handle_button_press(pressed);
        if (screen_dirty) render_screen();

        previous_pad = pad;
        SYS_doVBlankProcess();
    }

    return 0;
}
