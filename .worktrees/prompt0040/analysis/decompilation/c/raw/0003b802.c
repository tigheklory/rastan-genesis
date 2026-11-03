/* ORIGINAL ARCADE PC: 0x0003B802; also 0x0003B866, 0x0003B8EE,
 * 0x0003B902, and internal gameplay-HUD caller 0x0003A64C.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for the bounded lives/ROUND path.
 *
 * This preserves the byte-granular PC090OJ record behavior.  A record is
 * {control, Y, code, X}; 3B802 changes only Y-high/Y-low and code.  X and the
 * control word come from the fixed 3B984 template installed by 3B902.
 * This is an auditable reconstruction, not original Taito source. */
#include <stdint.h>

typedef struct ArcadeHudRecord {
    uint16_t control;
    uint16_t y;
    uint16_t code;
    uint16_t x;
} ArcadeHudRecord;

typedef struct ArcadeDigitConfig {
    uint8_t count_and_nibble;
    uint8_t y;
    uint32_t destination;
    uint32_t source;
} ArcadeDigitConfig;

/* Exact ten-byte entries at 0x3B87E..0x3B8AF.  Bit 0 selects the low
 * nibble; otherwise the high nibble is selected before the source pointer is
 * decremented.  A count of one also disables leading-zero suppression. */
static const ArcadeDigitConfig digit_config_3b87e[5] = {
    {6, 0x10, 0x00d00108, 0x0010c11e},
    {6, 0x10, 0x00d00150, 0x0010c11e},
    {6, 0x10, 0x00d000d8, 0x0010c142},
    {1, 0xe8, 0x00d000a8, 0x0010c117}, /* ROUND digit, record 21 */
    {1, 0xe4, 0x00d00088, 0x0010c103}, /* reserve-lives digit, record 17 */
};

extern uint8_t arcade_read_byte(uint32_t address);
extern ArcadeHudRecord *arcade_pc090oj_record(uint32_t address);
extern void arcade_4529c(void);
extern uint16_t g_a5_04, g_a5_34;

/* 0x3B866: returns the Y high byte.  Once a nonzero digit is encountered,
 * later zeroes stay visible. */
static uint8_t arcade_3b866_leading_zero(uint16_t *nonzero_seen,
                                         uint16_t digit)
{
    if (*nonzero_seen == 0 && digit == 0) return 1;
    *nonzero_seen = 1;
    return 0;
}

void arcade_3b802_digit_producer(uint16_t selector)
{
    const ArcadeDigitConfig *cfg = &digit_config_3b87e[selector];
    uint16_t remaining = cfg->count_and_nibble;
    uint16_t nonzero_seen = (remaining == 1);
    uint32_t source = cfg->source;
    uint32_t destination = cfg->destination;

    do {
        uint16_t digit = arcade_read_byte(source);
        const unsigned low_nibble = remaining & 1;
        digit = low_nibble ? (digit & 0x0f) : ((digit >> 4) & 0x0f);
        ArcadeHudRecord *record = arcade_pc090oj_record(destination);
        uint8_t *y_bytes = (uint8_t *)(void *)&record->y;
        y_bytes[0] = arcade_3b866_leading_zero(&nonzero_seen, digit);
        y_bytes[1] = cfg->y;
        record->code = (uint16_t)(0x002a + digit);
        if (low_nibble) source--;
        destination -= 8;
        remaining--;
    } while (remaining != 0);
}

/* Exact five-record template at 0x3B984. */
static const ArcadeHudRecord lower_hud_template_3b984[5] = {
    {0, 0x00ec, 0x002a, 0x0000},
    {0, 0x00e8, 0x0034, 0x0100},
    {0, 0x00e8, 0x0035, 0x0110},
    {0, 0x00e8, 0x0036, 0x0120},
    {0, 0x00e8, 0x002b, 0x0128},
};

/* 0x3B902: D1==0 restores the five defaults; nonzero changes only Y-high
 * for records 17..21.  D1==1 therefore hides all five as Y=0x01xx. */
void arcade_3b902_lower_hud_visibility(uint16_t d1)
{
    ArcadeHudRecord *out = arcade_pc090oj_record(0x00d00088);
    if (d1 == 0) {
        for (unsigned i = 0; i < 5; i++) out[i] = lower_hud_template_3b984[i];
    } else {
        for (unsigned i = 0; i < 5; i++) {
            uint8_t *y_bytes = (uint8_t *)(void *)&out[i].y;
            y_bytes[0] = (uint8_t)d1;
        }
    }
}

/* Internal 0x3B8EE entry: show/reset the group, then refresh the ROUND and
 * reserve-life digits through selectors 3 and 4. */
void arcade_3b8ee_show_lower_hud(void)
{
    arcade_3b902_lower_hud_visibility(0);
    arcade_3b802_digit_producer(3);
    arcade_3b802_digit_producer(4);
}

/* 0x3A64C..0x3A662: gameplay presentation boundary. */
void arcade_3a64c_show_gameplay_lower_hud(void)
{
    if (g_a5_34 != 0) arcade_3b8ee_show_lower_hud();
    arcade_4529c();
    g_a5_04 = 5;
}
