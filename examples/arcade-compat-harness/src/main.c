#include <genesis.h>

#include "main.h"
#include "res_arcade.h"

typedef struct RegionCounter {
    u32 reads8;
    u32 reads16;
    u32 writes8;
    u32 writes16;
    u32 last_addr;
    u16 last_value;
} RegionCounter;

static u8 arcade_workram[ARCADE_WORKRAM_BYTES];
static RegionCounter region_counters[REGION_COUNT];
static u16 input_shadow[3];
static u16 video_shadow[8];
static u16 sound_shadow[8];
static u16 frame_counter;
static u16 previous_pad;
static u16 gameplay_frames;
static u16 credits;
static bool game_started;
static bool stage_ready;

static const char *const region_names[REGION_COUNT] = {
    "ROM    ",
    "WORKRAM",
    "INPUT  ",
    "VIDEO  ",
    "SOUND  ",
    "UNKNOWN",
};

static const char *const mode_names[3] = {
    "TITLE ",
    "WAIT  ",
    "PLAY  ",
};

#define WRAM_MODE_ADDR            0x10C004
#define WRAM_SUBMODE_ADDR         0x10C002
#define WRAM_MODE_FLAG46_ADDR     0x10C046
#define WRAM_STAGE_ID_ADDR        0x10C13E
#define WRAM_SELECTED_STAGE_ADDR  0x10D242
#define WRAM_PLAYER_CTRL_ADDR     0x10D37A
#define WRAM_PLAY_READY_ADDR      0x10D0E8
#define WRAM_PLAY_READY_MIRROR    0x10D10E
#define WRAM_MODE9_ADDR           0x10D3AA
#define WRAM_MODE8_ADDR           0x10D3AC
#define WRAM_READY_FLAG_ADDR      0x10D394
#define WRAM_STAGE_EVENT_ADDR     0x10D388
#define WRAM_STAGE_EVENT2_ADDR    0x10D2F0
#define WRAM_STAGE_EVENT3_ADDR    0x10D30E
#define WRAM_DROP_STEP_ADDR       0x10D372
#define WRAM_10AE_ADDR            0x10D0AE
#define WRAM_10B0_ADDR            0x10D0B0
#define WRAM_10B2_ADDR            0x10D0B2
#define WRAM_10B4_ADDR            0x10D0B4
#define WRAM_10B6_ADDR            0x10D0B6
#define WRAM_10B8_ADDR            0x10D0B8
#define WRAM_10BA_ADDR            0x10D0BA
#define WRAM_10E4_ADDR            0x10D0E4
#define WRAM_10E6_ADDR            0x10D0E6
#define WRAM_10EC_ADDR            0x10D0EC
#define WRAM_10EE_ADDR            0x10D0EE
#define WRAM_10F2_ADDR            0x10D0F2
#define WRAM_1108_ADDR            0x10D108
#define WRAM_1278_ADDR            0x10D278
#define WRAM_1296_ADDR            0x10D296
#define WRAM_12E8_ADDR            0x10D2E8
#define WRAM_12EA_ADDR            0x10D2EA
#define WRAM_12EE_ADDR            0x10D2EE
#define WRAM_12FC_ADDR            0x10D2FC
#define WRAM_12FE_ADDR            0x10D2FE
#define WRAM_1302_ADDR            0x10D302
#define WRAM_1324_ADDR            0x10D324

static ArcadeRegionId region_for_addr(u32 addr)
{
    if (addr <= ARCADE_MAINCPU_ROM_END) return REGION_ROM;
    if (addr >= ARCADE_WORKRAM_START && addr <= ARCADE_WORKRAM_END) return REGION_WORKRAM;
    if (addr == ARCADE_INPUT_PORT0 || addr == ARCADE_INPUT_PORT1 || addr == ARCADE_INPUT_DIP) return REGION_INPUT;
    if (addr >= ARCADE_VIDEO_REG_START && addr <= ARCADE_VIDEO_REG_END) return REGION_VIDEO;
    if (addr >= ARCADE_SOUND_LATCH_START && addr <= ARCADE_SOUND_LATCH_END) return REGION_SOUND;
    return REGION_UNKNOWN;
}

static u8 rom_read8(u32 addr)
{
    if (addr >= ARCADE_MAINCPU_ROM_BYTES) return 0xFF;
    return rastan_maincpu[addr];
}

static u16 rom_read16(u32 addr)
{
    return ((u16)rom_read8(addr) << 8) | rom_read8(addr + 1);
}

static u8 workram_read8(u32 addr)
{
    return arcade_workram[addr - ARCADE_WORKRAM_START];
}

static void workram_write8(u32 addr, u8 value)
{
    arcade_workram[addr - ARCADE_WORKRAM_START] = value;
}

static u16 workram_read16(u32 addr)
{
    const u32 offset = addr - ARCADE_WORKRAM_START;
    return ((u16)arcade_workram[offset] << 8) | arcade_workram[offset + 1];
}

static void workram_write16(u32 addr, u16 value)
{
    const u32 offset = addr - ARCADE_WORKRAM_START;
    arcade_workram[offset] = value >> 8;
    arcade_workram[offset + 1] = value & 0xFF;
}

static void record_access(ArcadeRegionId region, bool is_write, bool is_16bit, u32 addr, u16 value)
{
    RegionCounter *counter = &region_counters[region];

    if (is_write)
    {
        if (is_16bit) counter->writes16++;
        else counter->writes8++;
    }
    else
    {
        if (is_16bit) counter->reads16++;
        else counter->reads8++;
    }

    counter->last_addr = addr;
    counter->last_value = value;
}

static u8 arcade_read8(u32 addr)
{
    const ArcadeRegionId region = region_for_addr(addr);
    u8 value = 0xFF;

    switch (region)
    {
        case REGION_ROM:
            value = rom_read8(addr);
            break;
        case REGION_WORKRAM:
            value = workram_read8(addr);
            break;
        case REGION_INPUT:
            if (addr == ARCADE_INPUT_PORT0) value = input_shadow[0] & 0xFF;
            else if (addr == ARCADE_INPUT_PORT1) value = input_shadow[1] & 0xFF;
            else value = input_shadow[2] & 0xFF;
            break;
        case REGION_VIDEO:
            value = video_shadow[((addr - ARCADE_VIDEO_REG_START) >> 1) & 7] & 0xFF;
            break;
        case REGION_SOUND:
            value = sound_shadow[((addr - ARCADE_SOUND_LATCH_START) >> 1) & 7] & 0xFF;
            break;
        default:
            break;
    }

    record_access(region, FALSE, FALSE, addr, value);
    return value;
}

static u16 arcade_read16(u32 addr)
{
    const ArcadeRegionId region = region_for_addr(addr);
    u16 value = 0xFFFF;

    switch (region)
    {
        case REGION_ROM:
            value = rom_read16(addr);
            break;
        case REGION_WORKRAM:
            value = workram_read16(addr);
            break;
        case REGION_INPUT:
            if (addr == ARCADE_INPUT_PORT0) value = input_shadow[0];
            else if (addr == ARCADE_INPUT_PORT1) value = input_shadow[1];
            else value = input_shadow[2];
            break;
        case REGION_VIDEO:
            value = video_shadow[((addr - ARCADE_VIDEO_REG_START) >> 1) & 7];
            break;
        case REGION_SOUND:
            value = sound_shadow[((addr - ARCADE_SOUND_LATCH_START) >> 1) & 7];
            break;
        default:
            break;
    }

    record_access(region, FALSE, TRUE, addr, value);
    return value;
}

static void arcade_write8(u32 addr, u8 value)
{
    const ArcadeRegionId region = region_for_addr(addr);

    switch (region)
    {
        case REGION_WORKRAM:
            workram_write8(addr, value);
            break;
        case REGION_VIDEO:
            video_shadow[((addr - ARCADE_VIDEO_REG_START) >> 1) & 7] = value;
            break;
        case REGION_SOUND:
            sound_shadow[((addr - ARCADE_SOUND_LATCH_START) >> 1) & 7] = value;
            break;
        default:
            break;
    }

    record_access(region, TRUE, FALSE, addr, value);
}

static void arcade_write16(u32 addr, u16 value)
{
    const ArcadeRegionId region = region_for_addr(addr);

    switch (region)
    {
        case REGION_WORKRAM:
            workram_write16(addr, value);
            break;
        case REGION_VIDEO:
            video_shadow[((addr - ARCADE_VIDEO_REG_START) >> 1) & 7] = value;
            break;
        case REGION_SOUND:
            sound_shadow[((addr - ARCADE_SOUND_LATCH_START) >> 1) & 7] = value;
            break;
        default:
            break;
    }

    record_access(region, TRUE, TRUE, addr, value);
}

static void seed_initial_state(void)
{
    memset(arcade_workram, 0, sizeof(arcade_workram));
    memset(region_counters, 0, sizeof(region_counters));
    memset(input_shadow, 0xFF, sizeof(input_shadow));
    memset(video_shadow, 0, sizeof(video_shadow));
    memset(sound_shadow, 0, sizeof(sound_shadow));

    previous_pad = 0;
    gameplay_frames = 0;
    credits = 0;
    game_started = FALSE;
    stage_ready = FALSE;
    workram_write16(WRAM_SUBMODE_ADDR, 0x0004);
    workram_write16(WRAM_MODE_ADDR, 0);
    workram_write16(WRAM_MODE_FLAG46_ADDR, 0);
    workram_write16(WRAM_STAGE_ID_ADDR, 1);
    workram_write16(WRAM_SELECTED_STAGE_ADDR, 1);
    workram_write16(WRAM_PLAYER_CTRL_ADDR, 0);
    workram_write16(WRAM_PLAY_READY_ADDR, 3);
    workram_write16(WRAM_PLAY_READY_MIRROR, 3);
    workram_write16(WRAM_MODE8_ADDR, 0);
    workram_write16(WRAM_MODE9_ADDR, 0);
    workram_write16(WRAM_READY_FLAG_ADDR, 0);
    workram_write16(ARCADE_PLAYER_X_ADDR, 160);
    workram_write16(ARCADE_PLAYER_Y_ADDR, 128);
    workram_write16(ARCADE_STAGE_DROP_X_ADDR, 160);
    workram_write16(ARCADE_STAGE_DROP_Y_ADDR, 128);
}

static void update_input_shadow(u16 state)
{
    u8 port0 = 0xFF;
    u8 port1 = 0xFF;
    u16 latched = 0;

    if (state & BUTTON_UP) port0 &= ~0x01;
    if (state & BUTTON_DOWN) port0 &= ~0x02;
    if (state & BUTTON_LEFT) port0 &= ~0x04;
    if (state & BUTTON_RIGHT) port0 &= ~0x08;
    if (state & BUTTON_A) port0 &= ~0x10;
    if (state & BUTTON_B) port0 &= ~0x20;

    if (state & BUTTON_LEFT) latched |= 0x0001;
    if (state & BUTTON_RIGHT) latched |= 0x0002;
    if (state & BUTTON_UP) latched |= 0x0004;
    if (state & BUTTON_DOWN) latched |= 0x0008;
    if (state & BUTTON_A) latched |= 0x0010;
    if (state & BUTTON_B) latched |= 0x0020;

    if (state & BUTTON_C) port1 &= ~0x01;
    if (state & BUTTON_START) port1 &= ~0x02;

    input_shadow[0] = port0;
    input_shadow[1] = port1;
    input_shadow[2] = 0xFF;
    workram_write16(WRAM_PLAYER_CTRL_ADDR, latched);
}

static void load_scripted_drop_coords(void)
{
    arcade_write16(ARCADE_STAGE_DROP_X_ADDR, 160);
    arcade_write16(ARCADE_STAGE_DROP_Y_ADDR, 128);
}

static void copy_drop_to_live_player(void)
{
    arcade_write16(ARCADE_PLAYER_X_ADDR, arcade_read16(ARCADE_STAGE_DROP_X_ADDR));
    arcade_write16(ARCADE_PLAYER_Y_ADDR, arcade_read16(ARCADE_STAGE_DROP_Y_ADDR));
}

static u16 stage_table_word(u16 stage_id, u16 word_index)
{
    const u32 addr = ARCADE_STAGE_TABLE_ADDR + ((u32)stage_id * 12) + ((u32)word_index * 2);
    return arcade_read16(addr);
}

/* Direct translation of arcade routine 0x504fa..0x50538. */
static void arcade_504fa_load_stage_spawn_record(void)
{
    const u16 stage_id = workram_read16(WRAM_STAGE_ID_ADDR);

    arcade_write16(0x10D0AE, stage_table_word(stage_id, 0));
    arcade_write16(0x10D0EC, stage_table_word(stage_id, 0));
    arcade_write16(0x10D0B0, stage_table_word(stage_id, 1));
    arcade_write16(0x10D0EE, stage_table_word(stage_id, 1));
    arcade_write16(0x10D0B8, stage_table_word(stage_id, 2));
    arcade_write16(0x10D0BA, stage_table_word(stage_id, 3));
    arcade_write16(ARCADE_PLAYER_X_ADDR, stage_table_word(stage_id, 4));
    arcade_write16(ARCADE_PLAYER_Y_ADDR, stage_table_word(stage_id, 5));
}

/* Direct translation of arcade routine 0x5053a..0x505a4. */
static void arcade_5053a_seed_stage_runtime_defaults(void)
{
    arcade_write16(WRAM_10B2_ADDR, 0x0008);
    arcade_write16(WRAM_10F2_ADDR, 0x0008);
    arcade_write16(WRAM_10B4_ADDR, 0x0008);
    arcade_write16(WRAM_10B6_ADDR, 0x0008);
    arcade_write16(WRAM_10E6_ADDR, 0x0000);
    arcade_write16(WRAM_10E4_ADDR, 0x0000);
    arcade_write16(0x10D0D2, 0x00FF);
    arcade_write16(0x10D0D6, 0x00FF);
    arcade_write16(WRAM_PLAY_READY_ADDR, 0x0003);
    arcade_write16(WRAM_PLAY_READY_MIRROR, 0x0003);
    arcade_write16(WRAM_1108_ADDR, 0x00FF);
    arcade_write16(WRAM_1296_ADDR, 0x00FF);
    arcade_write16(WRAM_12E8_ADDR, 0x0000);
    arcade_write16(WRAM_12EA_ADDR, 0x0000);
    arcade_write16(WRAM_12EE_ADDR, 0x00FF);
    arcade_write16(WRAM_1324_ADDR, 0x00FF);
    arcade_write16(WRAM_STAGE_EVENT2_ADDR, 0x00FF);
    arcade_write16(WRAM_1278_ADDR, 0x0000);
    arcade_write16(WRAM_12FC_ADDR, 0x0001);
    arcade_write16(WRAM_12FE_ADDR, 0x00FF);
    arcade_write16(WRAM_1302_ADDR, 0x0001);
}

static void emulate_stage_init_master(void)
{
    arcade_504fa_load_stage_spawn_record();
    arcade_5053a_seed_stage_runtime_defaults();
    load_scripted_drop_coords();
    arcade_write16(WRAM_MODE_FLAG46_ADDR, 0);
}

static void emulate_mode0_to_mode1(void)
{
    if (credits == 0) return;

    credits--;
    game_started = TRUE;
    stage_ready = FALSE;
    gameplay_frames = 0;

    arcade_write16(WRAM_MODE_FLAG46_ADDR, 0);
    arcade_write16(WRAM_MODE8_ADDR, 8);
    arcade_write16(WRAM_MODE_ADDR, 1);
    emulate_stage_init_master();
}

static void emulate_mode1_wait_to_mode2(void)
{
    arcade_write16(WRAM_MODE_FLAG46_ADDR, 2);
    arcade_write16(WRAM_READY_FLAG_ADDR, 1);
    arcade_write16(WRAM_MODE9_ADDR, 9);
    arcade_write16(WRAM_MODE_ADDR, 2);
    copy_drop_to_live_player();
    stage_ready = TRUE;
}

static void advance_mode_flow(void)
{
    u16 mode = workram_read16(WRAM_MODE_ADDR);

    if (mode == 1)
    {
        gameplay_frames++;
        arcade_write16(WRAM_PLAY_READY_ADDR, 3 + (gameplay_frames >> 1));
        arcade_write16(WRAM_PLAY_READY_MIRROR, arcade_read16(WRAM_PLAY_READY_ADDR));

        if (arcade_read16(WRAM_PLAY_READY_ADDR) >= 16)
        {
            emulate_mode1_wait_to_mode2();
            gameplay_frames = 0;
        }
    }
}

static void evaluate_entry_thresholds(void)
{
    const u16 player_x = arcade_read16(ARCADE_PLAYER_X_ADDR);

    if (player_x >= 216)
    {
        arcade_write16(ARCADE_ENTRY_ARM_ADDR, 1);
        arcade_write16(ARCADE_ENTRY_SIDE_ADDR, 1);
        arcade_write16(ARCADE_ENTRY_EVENT_ADDR, 1);
    }
    else if (player_x <= 80)
    {
        arcade_write16(ARCADE_ENTRY_ARM_ADDR, 1);
        arcade_write16(ARCADE_ENTRY_SIDE_ADDR, 2);
        arcade_write16(ARCADE_ENTRY_EVENT_ADDR, 1);
    }
    else
    {
        arcade_write16(ARCADE_ENTRY_ARM_ADDR, 0);
        arcade_write16(ARCADE_ENTRY_SIDE_ADDR, 0);
        arcade_write16(ARCADE_ENTRY_EVENT_ADDR, 0);
    }
}

static void handle_action_buttons(u16 pad)
{
    const u16 pressed = (pad ^ previous_pad) & pad;

    if ((pad & (BUTTON_A | BUTTON_B | BUTTON_C | BUTTON_START)) == (BUTTON_A | BUTTON_B | BUTTON_C | BUTTON_START))
    {
        seed_initial_state();
        return;
    }

    if (pressed & BUTTON_C)
    {
        credits++;
        sound_shadow[0] = 0x0001;
    }

    if ((pressed & BUTTON_START) && credits && !game_started)
        emulate_mode0_to_mode1();
}

static void simulate_arcade_frame(u16 pad)
{
    s16 player_x = (s16)arcade_read16(ARCADE_PLAYER_X_ADDR);
    s16 player_y = (s16)arcade_read16(ARCADE_PLAYER_Y_ADDR);
    s16 drop_x = (s16)arcade_read16(ARCADE_STAGE_DROP_X_ADDR);
    s16 drop_y = (s16)arcade_read16(ARCADE_STAGE_DROP_Y_ADDR);
    const u8 port = arcade_read8(ARCADE_INPUT_PORT0);
    const u16 mode = workram_read16(WRAM_MODE_ADDR);

    if (mode == 2)
    {
        if (!(port & 0x04)) player_x -= 1;
        if (!(port & 0x08)) player_x += 1;
        if (!(port & 0x01)) player_y -= 1;
        if (!(port & 0x02)) player_y += 1;
    }

    if (mode == 1)
    {
        if (drop_y < 160) drop_y += 1;
        if (drop_x > 80) drop_x -= 1;
        arcade_write16(ARCADE_STAGE_DROP_X_ADDR, (u16)drop_x);
        arcade_write16(ARCADE_STAGE_DROP_Y_ADDR, (u16)drop_y);
        copy_drop_to_live_player();
        player_x = drop_x;
        player_y = drop_y;
    }

    if (player_x < 32) player_x = 32;
    if (player_x > 288) player_x = 288;
    if (player_y < 32) player_y = 32;
    if (player_y > 192) player_y = 192;

    if (drop_x < 0) drop_x = 0;
    if (drop_x > 320) drop_x = 320;
    if (drop_y < 0) drop_y = 0;
    if (drop_y > 224) drop_y = 224;

    arcade_write16(ARCADE_PLAYER_X_ADDR, (u16)player_x);
    arcade_write16(ARCADE_PLAYER_Y_ADDR, (u16)player_y);
    if (mode != 1)
    {
        arcade_write16(ARCADE_STAGE_DROP_X_ADDR, (u16)drop_x);
        arcade_write16(ARCADE_STAGE_DROP_Y_ADDR, (u16)drop_y);
    }

    evaluate_entry_thresholds();
    advance_mode_flow();

    arcade_write16(ARCADE_VIDEO_REG_START, (u16)(frame_counter & 0x1F));
    arcade_write16(ARCADE_VIDEO_REG_START + 2, (u16)player_x);
    arcade_write16(ARCADE_VIDEO_REG_START + 4, (u16)player_y);
    arcade_write8(ARCADE_SOUND_LATCH_START, (u8)(pad & 0xFF));
}

static void draw_counter_line(s16 y, ArcadeRegionId region)
{
    char line[40];
    const RegionCounter *counter = &region_counters[region];

    sprintf(
        line,
        "%s %4lu %4lu %4lu %4lu",
        region_names[region],
        counter->reads8,
        counter->reads16,
        counter->writes8,
        counter->writes16
    );
    VDP_drawText(line, 1, y);
}

static void draw_rom_probe_line(s16 y, const char *label, u32 addr)
{
    char line[40];

    sprintf(line, "%s %06lX %04X", label, addr, arcade_read16(addr));
    VDP_drawText(line, 1, y);
}

static void draw_stage_view(void)
{
    const u16 player_x = workram_read16(ARCADE_PLAYER_X_ADDR);
    const u16 player_y = workram_read16(ARCADE_PLAYER_Y_ADDR);
    const u16 drop_x = workram_read16(ARCADE_STAGE_DROP_X_ADDR);
    const u16 drop_y = workram_read16(ARCADE_STAGE_DROP_Y_ADDR);
    const s16 area_x = 23;
    const s16 area_y = 5;
    const s16 area_w = 16;
    const s16 area_h = 14;
    s16 x;
    s16 y;

    for (y = 0; y < area_h; y++)
    {
        for (x = 0; x < area_w; x++)
        {
            if (y == area_h - 1) VDP_drawText("#", area_x + x, area_y + y);
            else if (x == 0 || x == area_w - 1) VDP_drawText("|", area_x + x, area_y + y);
            else VDP_drawText(".", area_x + x, area_y + y);
        }
    }

    VDP_drawText("D", area_x + (drop_x >> 4), area_y + (drop_y >> 4));
    VDP_drawText("P", area_x + (player_x >> 4), area_y + (player_y >> 4));
}

static void draw_debug_hud(void)
{
    char line[40];
    const u16 mode = workram_read16(WRAM_MODE_ADDR);
    const u16 control = workram_read16(WRAM_PLAYER_CTRL_ADDR);
    const u16 player_x = workram_read16(ARCADE_PLAYER_X_ADDR);
    const u16 player_y = workram_read16(ARCADE_PLAYER_Y_ADDR);
    const u16 drop_x = workram_read16(ARCADE_STAGE_DROP_X_ADDR);
    const u16 drop_y = workram_read16(ARCADE_STAGE_DROP_Y_ADDR);
    const u16 entry_arm = workram_read16(ARCADE_ENTRY_ARM_ADDR);
    const u16 entry_side = workram_read16(ARCADE_ENTRY_SIDE_ADDR);
    const u16 entry_event = workram_read16(ARCADE_ENTRY_EVENT_ADDR);
    const u16 play_ready = workram_read16(WRAM_PLAY_READY_ADDR);
    const u16 mode46 = workram_read16(WRAM_MODE_FLAG46_ADDR);
    const u16 stage_id = workram_read16(WRAM_STAGE_ID_ADDR);

    VDP_clearTextArea(0, 0, 40, 28);
    VDP_drawText("ARCADE COMPAT HARNESS", 9, 1);
    VDP_drawText("0x3A79C + 0x501EA FLOW", 8, 2);

    sprintf(line, "MODE %s  CREDITS %u  STAGE %u", mode_names[mode < 3 ? mode : 0], credits, stage_id);
    VDP_drawText(line, 1, 4);
    sprintf(line, "CTRL %04X  M46 %u  10E8 %u", control, mode46, play_ready);
    VDP_drawText(line, 1, 5);
    sprintf(line, "PLAYER XY  %3u %3u", player_x, player_y);
    VDP_drawText(line, 1, 6);
    sprintf(line, "DROP   XY  %3u %3u", drop_x, drop_y);
    VDP_drawText(line, 1, 7);
    sprintf(line, "ENTRY FLAGS %u %u %u  R %u", entry_arm, entry_side, entry_event, stage_ready ? 1 : 0);
    VDP_drawText(line, 1, 8);

    draw_stage_view();

    draw_rom_probe_line(18, "MODE@", ARCADE_MODE_DISPATCH_ADDR);
    draw_rom_probe_line(19, "SINI@", ARCADE_STAGE_INIT_ADDR);
    VDP_drawText("R8   R16  W8   W16", 1, 20);
    draw_counter_line(21, REGION_ROM);
    draw_counter_line(22, REGION_WORKRAM);
    draw_counter_line(23, REGION_INPUT);
    draw_counter_line(24, REGION_VIDEO);
    draw_counter_line(25, REGION_SOUND);

    sprintf(
        line,
        "STAGE TBL %04X %04X %04X",
        stage_table_word(stage_id, 0),
        stage_table_word(stage_id, 4),
        stage_table_word(stage_id, 5)
    );
    VDP_drawText(line, 1, 26);

    VDP_drawText("A=attack  B=jump  C=coin  START=start", 1, 27);
}

int main(bool hardReset)
{
    const u16 unused_hard_reset = hardReset;

    (void)unused_hard_reset;

    SYS_disableInts();
    VDP_setScreenWidth320();
    PAL_setPalette(PAL0, palette_black, CPU);
    VDP_setTextPalette(PAL1);
    PAL_setPalette(PAL1, palette_grey, CPU);
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    seed_initial_state();
    SYS_enableInts();

    while (TRUE)
    {
        const u16 pad = JOY_readJoypad(JOY_1);

        update_input_shadow(pad);
        handle_action_buttons(pad);
        simulate_arcade_frame(pad);
        draw_debug_hud();
        previous_pad = pad;
        frame_counter++;
        SYS_doVBlankProcess();
    }

    return 0;
}
