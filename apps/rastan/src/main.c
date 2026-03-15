#include <genesis.h>
#include <string.h>

#include "main.h"

#define SCREEN_W 40
#define FACTORY_DIP1 0xFE
#define FACTORY_DIP2 0xFF
#define MENU_COUNT 8

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

static const MenuItem menu_items[MENU_COUNT] = {
    {"CABINET TYPE", cabinet_values, "Cabinet orientation for the game.", "SW1-1", 2},
    {"MONITOR REV", monitor_values, "Flips monitor display direction.", "SW1-2", 2},
    {"GAME MODE", game_mode_values, "Normal game or board test mode.", "SW1-3", 2},
    {"COINAGE", coinage_values, "Pricing for credits and coins.", "SW1-5..8", 4},
    {"DIFFICULTY", difficulty_values, "Overall game difficulty level.", "SW2-1..2", 4},
    {"BONUS LIFE", bonus_values, "Score needed for bonus life.", "SW2-3..4", 4},
    {"LIVES", lives_values, "Starting lives for each credit.", "SW2-5..6", 4},
    {"CONTINUE", continue_values, "Allow continue after game over.", "SW2-7", 2},
};

static u8 dip1 = FACTORY_DIP1;
static u8 dip2 = FACTORY_DIP2;
static u8 selected_menu = 0;
static UndoState undo_state = {0, 0, FALSE};
static char status_line[SCREEN_W + 1] = "READY";

static void draw_padded_text(const char *text, u16 x, u16 y, u16 width)
{
    char line[SCREEN_W + 1];
    const size_t len = strlen(text);
    u16 i;

    for (i = 0; i < width && i < SCREEN_W; i++)
    {
        line[i] = (i < len) ? text[i] : ' ';
    }
    line[i] = '\0';

    VDP_drawText(line, x, y);
}

static void set_status(const char *text)
{
    strncpy(status_line, text, SCREEN_W);
    status_line[SCREEN_W] = '\0';
    draw_padded_text(status_line, 0, 24, SCREEN_W);
}

static void save_undo_state(void)
{
    undo_state.dip1 = dip1;
    undo_state.dip2 = dip2;
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
        case 0: return get_bit(dip1, 0) ? 1 : 0;
        case 1: return get_bit(dip1, 1) ? 1 : 0;
        case 2: return get_bit(dip1, 2) ? 1 : 0;
        case 3:
        {
            const u8 raw = get_field(dip1, 4, 0x0F);
            if (raw == 0x0F) return 0;
            if (raw == 0x0A) return 1;
            if (raw == 0x05) return 2;
            return 3;
        }
        case 4:
        {
            const u8 raw = get_field(dip2, 0, 0x03);
            if (raw == 0x02) return 0;
            if (raw == 0x03) return 1;
            if (raw == 0x01) return 2;
            return 3;
        }
        case 5:
        {
            const u8 raw = get_field(dip2, 2, 0x03);
            if (raw == 0x03) return 0;
            if (raw == 0x02) return 1;
            if (raw == 0x01) return 2;
            return 3;
        }
        case 6:
        {
            const u8 raw = get_field(dip2, 4, 0x03);
            if (raw == 0x03) return 0;
            if (raw == 0x02) return 1;
            if (raw == 0x01) return 2;
            return 3;
        }
        case 7: return get_bit(dip2, 6) ? 0 : 1;
        default: return 0;
    }
}

static void set_menu_value(u8 index, u8 next_value)
{
    save_undo_state();

    switch (index)
    {
        case 0: set_bit(&dip1, 0, next_value ? 1 : 0); break;
        case 1: set_bit(&dip1, 1, next_value ? 1 : 0); break;
        case 2: set_bit(&dip1, 2, next_value ? 1 : 0); break;
        case 3:
        {
            static const u8 raw_coinage[4] = {0x0F, 0x0A, 0x05, 0x00};
            set_field(&dip1, 4, 0x0F, raw_coinage[next_value & 3]);
            break;
        }
        case 4:
        {
            static const u8 raw_difficulty[4] = {0x02, 0x03, 0x01, 0x00};
            set_field(&dip2, 0, 0x03, raw_difficulty[next_value & 3]);
            break;
        }
        case 5:
        {
            static const u8 raw_bonus[4] = {0x03, 0x02, 0x01, 0x00};
            set_field(&dip2, 2, 0x03, raw_bonus[next_value & 3]);
            break;
        }
        case 6:
        {
            static const u8 raw_lives[4] = {0x03, 0x02, 0x01, 0x00};
            set_field(&dip2, 4, 0x03, raw_lives[next_value & 3]);
            break;
        }
        case 7: set_bit(&dip2, 6, next_value ? 0 : 1); break;
        default: break;
    }
}

static void render_switch_bank(u8 bank_value, u16 y, const char *title)
{
    char line[SCREEN_W + 1];
    int i;

    draw_padded_text(title, 1, y, 18);
    draw_padded_text("1 2 3 4 5 6 7 8", 21, y, 15);

    strcpy(line, "   ");
    for (i = 0; i < 8; i++)
    {
        const char glyph = ((bank_value >> i) & 1) ? '.' : '#';
        const size_t len = strlen(line);

        line[len] = glyph;
        line[len + 1] = (i == 7) ? '\0' : ' ';
        line[len + 2] = '\0';
    }

    draw_padded_text(line, 21, y + 1, 15);

    sprintf(line, "RAW $%02X", bank_value);
    draw_padded_text(line, 1, y + 1, 12);
}

static void render_menu_row(u8 index)
{
    char line[SCREEN_W + 1];
    const MenuItem *item = &menu_items[index];
    const u8 value = get_menu_value(index);

    sprintf(line, "%c %-13s %-11s", (index == selected_menu) ? '>' : ' ', item->label, item->values[value]);
    draw_padded_text(line, 1, (u16)(9 + index), 27);
}

static void render_help_panel(void)
{
    const MenuItem *item = &menu_items[selected_menu];
    char line[SCREEN_W + 1];

    sprintf(line, "HELP: %-28s", item->switches);
    draw_padded_text(line, 0, 20, SCREEN_W);
    draw_padded_text(item->help_text, 0, 21, SCREEN_W);
    draw_padded_text("UP/DOWN MOVE  LEFT/RIGHT/A CHANGE", 0, 22, SCREEN_W);
    draw_padded_text("B UNDO  C FACTORY RESET  START RUN", 0, 23, SCREEN_W);
}

static void render_static_layout(void)
{
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);

    draw_padded_text("RASTAN STARTUP CONFIG", 9, 0, 22);
    draw_padded_text("KNOWN-GOOD SGDK TEXT SANITY BUILD", 3, 1, 34);
    draw_padded_text("DIP BANKS", 1, 3, 9);
    draw_padded_text("SETTINGS", 1, 8, 8);
    draw_padded_text("A/LR CHANGE  B UNDO  C RESET", 1, 26, 30);
    draw_padded_text("START = RUN STUB (NO ARCADE CODE YET)", 1, 27, 38);
}

static void render_full_screen(void)
{
    u16 i;

    render_static_layout();
    render_switch_bank(dip1, 4, "DIP SWITCH BANK 1");
    render_switch_bank(dip2, 6, "DIP SWITCH BANK 2");

    for (i = 0; i < MENU_COUNT; i++)
    {
        render_menu_row((u8)i);
    }

    render_help_panel();
    set_status(status_line);
}

static void apply_factory_defaults(void)
{
    save_undo_state();
    dip1 = FACTORY_DIP1;
    dip2 = FACTORY_DIP2;
}

static void undo_last_change(void)
{
    if (undo_state.valid)
    {
        const u8 prev_dip1 = dip1;
        const u8 prev_dip2 = dip2;

        dip1 = undo_state.dip1;
        dip2 = undo_state.dip2;
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
    PAL_setPalette(PAL0, palette_black, CPU);
    VDP_setTextPalette(PAL1);
    PAL_setPalette(PAL1, palette_grey, CPU);

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
            render_menu_row(previous_menu);
            render_menu_row(selected_menu);
            render_help_panel();
            set_status("SELECTION MOVED");
        }
        else if (pressed & BUTTON_DOWN)
        {
            const u8 previous_menu = selected_menu;
            selected_menu = (selected_menu + 1) % MENU_COUNT;
            render_menu_row(previous_menu);
            render_menu_row(selected_menu);
            render_help_panel();
            set_status("SELECTION MOVED");
        }
        else if (pressed & (BUTTON_LEFT | BUTTON_RIGHT | BUTTON_A))
        {
            const u8 current_value = get_menu_value(selected_menu);
            const u8 count = menu_items[selected_menu].value_count;
            const bool backwards = (pressed & BUTTON_LEFT) != 0;
            const u8 next_value = backwards ? ((current_value == 0) ? (count - 1) : (current_value - 1))
                                            : ((current_value + 1) % count);

            set_menu_value(selected_menu, next_value);
            render_switch_bank(dip1, 4, "DIP SWITCH BANK 1");
            render_switch_bank(dip2, 6, "DIP SWITCH BANK 2");
            render_menu_row(selected_menu);
            render_help_panel();
            set_status("SETTING UPDATED");
        }
        else if (pressed & BUTTON_B)
        {
            undo_last_change();
            render_switch_bank(dip1, 4, "DIP SWITCH BANK 1");
            render_switch_bank(dip2, 6, "DIP SWITCH BANK 2");
            render_menu_row(selected_menu);
            render_help_panel();
            set_status("LAST CHANGE UNDONE");
        }
        else if (pressed & BUTTON_C)
        {
            apply_factory_defaults();
            render_switch_bank(dip1, 4, "DIP SWITCH BANK 1");
            render_switch_bank(dip2, 6, "DIP SWITCH BANK 2");
            render_menu_row(selected_menu);
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
