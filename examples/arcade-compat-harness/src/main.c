#include <genesis.h>
#include <string.h>

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

typedef struct ShadowSpriteEntry {
    u16 word0;
    u16 word1;
    u16 word2;
    u16 word3;
} ShadowSpriteEntry;

typedef struct RenderSpritePart {
    s16 x;
    s16 y;
    u16 tile_index;
} RenderSpritePart;

static u8 arcade_workram[ARCADE_WORKRAM_BYTES];
static RegionCounter region_counters[REGION_COUNT];
static u16 input_shadow[3];
static u16 video_shadow[8];
static u16 sound_shadow[8];
static ShadowSpriteEntry sprite_list_0460[10];
static ShadowSpriteEntry sprite_list_0170[6];
static ShadowSpriteEntry sprite_list_0300[4];
static u16 frame_counter;
static u16 previous_pad;
static u16 gameplay_frames;
static u16 credits;
static bool game_started;
static bool stage_ready;
static bool start_request_latched;
static u16 sprite_group_counts[3];
static u16 sprite_part_counts[3];
static RenderSpritePart render_parts[64];
static u16 render_part_count;
static bool player_family1_rendered;
static bool stage_family1_rendered;
static u8 selected_02c8_slot;
static u8 rendered_actor_slot;
static u8 rendered_actor_class;
static u8 rendered_actor_family;
static u8 rendered_actor_state;
static u8 rendered_actor_frame;
static u16 rendered_actor_tile_base;
static u32 decoded_sprite_tiles[64 * 32];
static const s8 actor_05c8_offsets[5][2] = {
    { -3, -8 },
    { 7, -8 },
    { 16, -8 },
    { -7, -16 },
    { 2, -16 },
};
static const u16 arcade_sprite_palette[16] = {
    RGB24_TO_VDPCOLOR(0x000000), RGB24_TO_VDPCOLOR(0x404040), RGB24_TO_VDPCOLOR(0x686868), RGB24_TO_VDPCOLOR(0x909090),
    RGB24_TO_VDPCOLOR(0xB0B0B0), RGB24_TO_VDPCOLOR(0xD0D0D0), RGB24_TO_VDPCOLOR(0xF0F0F0), RGB24_TO_VDPCOLOR(0xC04040),
    RGB24_TO_VDPCOLOR(0x40A040), RGB24_TO_VDPCOLOR(0x4060C0), RGB24_TO_VDPCOLOR(0xC0A040), RGB24_TO_VDPCOLOR(0xC08040),
    RGB24_TO_VDPCOLOR(0x804020), RGB24_TO_VDPCOLOR(0xA06060), RGB24_TO_VDPCOLOR(0x60A0A0), RGB24_TO_VDPCOLOR(0xFFFFFF),
};

#define STAGE_VIEW_X_CHARS 23
#define STAGE_VIEW_Y_CHARS 5
#define STAGE_VIEW_W_CHARS 16
#define STAGE_VIEW_H_CHARS 14

static void arcade_3a2d0_clear_words(u32 start_addr, u16 count_words);
static void arcade_45dfa_build_shadow_lists(void);
static void arcade_4543e_refresh_actor_fields_generic(u32 actor_addr);

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
#define WRAM_FLAG_001F_ADDR       0x10C01F
#define WRAM_FLAG_0032_ADDR       0x10C032
#define WRAM_FLAG_0034_ADDR       0x10C034
#define WRAM_INPUT_LATCH_ADDR     0x10C016
#define WRAM_FRAME_0200_ADDR      0x10C200
#define WRAM_BYTE_0104_ADDR       0x10C104
#define WRAM_BYTE_0118_ADDR       0x10C118
#define WRAM_ACTOR_02C8_ADDR      0x10C2C8
#define WRAM_WORD_0214_ADDR       0x10C214
#define WRAM_WORD_0230_ADDR       0x10C230
#define WRAM_WORD_0272_ADDR       0x10C272
#define WRAM_WORD_0274_ADDR       0x10C274
#define WRAM_WORD_027C_ADDR       0x10C27C
#define WRAM_WORD_027E_ADDR       0x10C27E
#define WRAM_WORD_02A2_ADDR       0x10C2A2
#define WRAM_ACTOR_05C8_ADDR      0x10C5C8
#define WRAM_ACTOR_0648_ADDR      0x10C648
#define WRAM_ACTOR_0688_ADDR      0x10C688
#define WRAM_ACTOR_06C8_ADDR      0x10C6C8
#define WRAM_ACTOR_0708_ADDR      0x10C708
#define WRAM_WORD_071E_ADDR       0x10C71E
#define WRAM_WORD_0722_ADDR       0x10C722
#define WRAM_ACTOR_0748_ADDR      0x10C748
#define ACTOR_STRIDE              0x40
#define FAMILY1_TABLE_ADDR        0x04771C

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
    memset(sprite_list_0460, 0, sizeof(sprite_list_0460));
    memset(sprite_list_0170, 0, sizeof(sprite_list_0170));
    memset(sprite_list_0300, 0, sizeof(sprite_list_0300));
    memset(sprite_group_counts, 0, sizeof(sprite_group_counts));
    memset(sprite_part_counts, 0, sizeof(sprite_part_counts));
    memset(render_parts, 0, sizeof(render_parts));
    memset(decoded_sprite_tiles, 0, sizeof(decoded_sprite_tiles));
    render_part_count = 0;
    player_family1_rendered = FALSE;
    stage_family1_rendered = FALSE;
    selected_02c8_slot = 0;
    rendered_actor_slot = 0xFF;
    rendered_actor_class = 0xFF;
    rendered_actor_family = 0xFF;
    rendered_actor_state = 0xFF;
    rendered_actor_frame = 0xFF;
    rendered_actor_tile_base = 0xFFFF;

    previous_pad = 0;
    gameplay_frames = 0;
    credits = 0;
    game_started = FALSE;
    stage_ready = FALSE;
    start_request_latched = FALSE;
    workram_write16(WRAM_SUBMODE_ADDR, 0x0004);
    workram_write16(WRAM_MODE_ADDR, 0);
    workram_write16(WRAM_MODE_FLAG46_ADDR, 0);
    workram_write16(WRAM_FLAG_0034_ADDR, 1);
    workram_write16(WRAM_FLAG_0032_ADDR, 0);
    workram_write8(WRAM_FLAG_001F_ADDR, 0);
    workram_write8(WRAM_BYTE_0104_ADDR, 0);
    workram_write8(WRAM_BYTE_0118_ADDR, 1);
    workram_write16(WRAM_STAGE_ID_ADDR, 1);
    workram_write16(WRAM_SELECTED_STAGE_ADDR, 1);
    workram_write16(WRAM_WORD_0272_ADDR, 0);
    workram_write16(WRAM_WORD_02A2_ADDR, 2);
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

/* Direct translation of arcade routine 0x3a772..0x3a79a. */
static void arcade_3a772_read_input_ports(void)
{
    u8 d0;
    u8 d1;

    if (workram_read16(WRAM_FLAG_0034_ADDR) == 0) return;

    d0 = arcade_read8(ARCADE_INPUT_PORT0);
    d1 = arcade_read8(ARCADE_INPUT_PORT1);

    if (workram_read8(WRAM_FLAG_001F_ADDR) & 0x01)
    {
        const u8 tmp = d0;
        d0 = d1;
        d1 = tmp;
    }

    if (workram_read16(WRAM_FLAG_0032_ADDR) != 0)
    {
        const u8 tmp = d0;
        d0 = d1;
        d1 = tmp;
    }

    (void)d1;
    arcade_write16(WRAM_INPUT_LATCH_ADDR, d0);
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

/* Minimal direct translation of the state-15 path used by 0x457d0 through 0x4543e. */
static void arcade_4543e_refresh_actor_fields(u32 actor_addr)
{
    const u8 state = workram_read8(actor_addr + 6);

    if (state == 15)
    {
        arcade_write16(actor_addr + 30, 0x043A);
        arcade_write8(actor_addr + 58, 0x02);
        arcade_write8(actor_addr + 1, 0x5F);
        arcade_write16(actor_addr + 40, 0x0302);
        arcade_write16(actor_addr + 44, 0x0005);
    }
}

/* Direct translation of arcade routine 0x45cfc..0x45d0e. */
static void arcade_45cfc_activate_actor(u32 actor_addr)
{
    arcade_write8(actor_addr + 0, 1);
    arcade_write8(actor_addr + 5, 3);
    arcade_write16(actor_addr + 28, 1);
}

static void arcade_453a8_seed_actor(u32 actor_addr)
{
    arcade_write8(actor_addr + 0, 1);
    arcade_write8(actor_addr + 5, 3);
    arcade_write16(actor_addr + 26, 0x0180);
    arcade_4543e_refresh_actor_fields_generic(actor_addr);
}

static void arcade_444e6_adjust_actor_variant(u32 actor_addr)
{
    u8 aux = workram_read8(actor_addr + 58);
    const u16 mode46 = workram_read16(WRAM_MODE_FLAG46_ADDR);

    if (aux == 0) return;
    if (mode46 == 0) return;

    aux = aux + (u8)(mode46 - 1);
    arcade_write8(actor_addr + 58, aux);
}

static void arcade_4449e_seed_stage_family_actor(void)
{
    static const u8 stage_class_seed[6] = { 0x0E, 0x13, 0x14, 0x15, 0x10, 0x17 };
    u8 stage_index = workram_read8(WRAM_BYTE_0118_ADDR);
    u32 actor_addr = 0x10C708;
    u8 family = 1;

    if ((stage_index < 1) || (stage_index > 6)) stage_index = 1;

    if (stage_index == 5)
    {
        actor_addr = 0x10C648;
        family = 2;
    }

    arcade_write16(0x10D3AC, 0);
    arcade_write8(actor_addr + 56, family);
    arcade_write8(actor_addr + 6, stage_class_seed[stage_index - 1]);
    arcade_write16(actor_addr + 28, 0x0080);
    arcade_453a8_seed_actor(actor_addr);
    arcade_444e6_adjust_actor_variant(actor_addr);
    arcade_write16(actor_addr + 22, arcade_read16(ARCADE_PLAYER_X_ADDR));
    arcade_write16(actor_addr + 26, arcade_read16(ARCADE_PLAYER_Y_ADDR));
}

/* Direct translation of arcade routine 0x457d0..0x4580a. */
static void arcade_457d0_seed_0748_actor(u32 actor_addr)
{
    u16 d0;

    arcade_write8(actor_addr + 56, 1);
    arcade_write8(actor_addr + 33, 0);
    arcade_write8(actor_addr + 6, 15);
    arcade_4543e_refresh_actor_fields(actor_addr);
    arcade_45cfc_activate_actor(actor_addr);

    d0 = workram_read16(WRAM_WORD_027C_ADDR);
    d0 <<= 2;
    d0 += 152;
    arcade_write16(actor_addr + 22, d0);
    arcade_write16(actor_addr + 50, 160);
    arcade_write16(actor_addr + 26, 16);
    arcade_write16(actor_addr + 48, 24);
}

/* Direct translation of arcade routine 0x457b2..0x457ce. */
static void arcade_457b2_seed_0748_group(void)
{
    u32 actor_addr = WRAM_ACTOR_0748_ADDR;

    arcade_write16(WRAM_WORD_027C_ADDR, 0);

    do
    {
        arcade_457d0_seed_0748_actor(actor_addr);
        actor_addr += ACTOR_STRIDE;
        arcade_write16(WRAM_WORD_027C_ADDR, workram_read16(WRAM_WORD_027C_ADDR) + 1);
    }
    while (workram_read16(WRAM_WORD_027C_ADDR) != 5);
}

/* Minimal direct translation of the state-17 path used by 0x423b2 through 0x4543e. */
static void arcade_4543e_refresh_actor_fields_state17(u32 actor_addr)
{
    arcade_write16(actor_addr + 30, 0x06E2);
    arcade_write8(actor_addr + 58, 0x02);
    arcade_write8(actor_addr + 1, 0x6E);
    arcade_write16(actor_addr + 40, 0x0402);
    arcade_write16(actor_addr + 44, 0x0007);
}

/* Direct translation of arcade routine 0x423b2..0x423ee using the 0x4236a source setup. */
static void arcade_423b2_seed_05c8_group(void)
{
    u32 actor_addr = WRAM_ACTOR_05C8_ADDR;
    u16 index;
    const s16 src_x = 272;
    const s16 src_y = 216;
    const u8 facing = 0;

    for (index = 0; index < 5; index++)
    {
        arcade_write8(actor_addr + 33, (u8)index);
        arcade_write8(actor_addr + 0, 1);
        arcade_write8(actor_addr + 56, 1);
        arcade_write8(actor_addr + 5, 17);
        arcade_write8(actor_addr + 6, 17);
        arcade_4543e_refresh_actor_fields_state17(actor_addr);
        arcade_write8(actor_addr + 2, facing);
        arcade_write16(actor_addr + 22, (u16)(src_x + actor_05c8_offsets[index][0]));
        arcade_write16(actor_addr + 26, (u16)(src_y + actor_05c8_offsets[index][1]));
        actor_addr += ACTOR_STRIDE;
    }
}

static void arcade_4543e_refresh_actor_fields_helper(u32 actor_addr)
{
    const u8 state = workram_read8(actor_addr + 6);
    const u8 family = workram_read8(actor_addr + 56);

    switch (state)
    {
        case 10:
            arcade_write16(actor_addr + 30, 0x033E);
            arcade_write8(actor_addr + 58, 0x02);
            arcade_write8(actor_addr + 1, 0x93);
            arcade_write16(actor_addr + 40, 0x0302);
            arcade_write16(actor_addr + 44, 0x0004);
            break;
        case 11:
            arcade_write16(actor_addr + 30, 0x02E8);
            arcade_write8(actor_addr + 58, 0x01);
            arcade_write8(actor_addr + 1, 0x5F);
            if (family == 0)
            {
                arcade_write16(actor_addr + 40, 0x0201);
                arcade_write16(actor_addr + 44, 0x0002);
            }
            else
            {
                arcade_write16(actor_addr + 40, 0x0403);
                arcade_write16(actor_addr + 44, 0x0006);
            }
            break;
        case 18:
            if (family == 0)
            {
                arcade_write16(actor_addr + 30, 0x0889);
                arcade_write8(actor_addr + 58, 0x02);
                arcade_write8(actor_addr + 1, 0x2D);
                arcade_write16(actor_addr + 40, 0x0303);
                arcade_write16(actor_addr + 44, 0x0005);
            }
            else
            {
                arcade_write16(actor_addr + 30, 0x050B);
                arcade_write8(actor_addr + 58, 0x01);
                arcade_write8(actor_addr + 1, 0xBC);
                arcade_write16(actor_addr + 40, 0x0000);
                arcade_write16(actor_addr + 44, 0x0000);
            }
            break;
        default:
            break;
    }
}

static void arcade_45be8_position_helper(u32 actor_addr)
{
    const u16 x = workram_read16(WRAM_WORD_071E_ADDR);
    const u16 y = workram_read16(WRAM_WORD_0722_ADDR) + 20;

    arcade_write16(actor_addr + 22, x);
    arcade_write16(actor_addr + 50, x);
    arcade_write16(actor_addr + 26, y);
    arcade_write16(actor_addr + 48, y);
    arcade_write8(actor_addr + 39, workram_read8(actor_addr + 39) | 0x80);
}

static void arcade_seed_multipart_helper_actor(u32 actor_addr, u8 slot_index, u8 state, u8 family)
{
    arcade_3a2d0_clear_words(actor_addr, 31);
    arcade_write8(actor_addr + 33, slot_index);
    arcade_write8(actor_addr + 6, state);
    arcade_write8(actor_addr + 56, family);
    arcade_4543e_refresh_actor_fields_helper(actor_addr);
    arcade_45cfc_activate_actor(actor_addr);
    arcade_45be8_position_helper(actor_addr);
}

/* Direct translation of arcade routine 0x45b2e..0x45bdc on its startup path. */
static void arcade_45b2e_seed_multipart_helpers(void)
{
    const u8 base_slot = (u8)workram_read16(0x10C200);
    const u8 state18 = workram_read8(WRAM_BYTE_0118_ADDR) == 2 ? 18 : 10;
    const u8 family18 = workram_read8(WRAM_BYTE_0118_ADDR) == 2 ? 1 : 0;
    const u8 actor_level = workram_read8(WRAM_BYTE_0118_ADDR);

    arcade_write16(WRAM_WORD_071E_ADDR, arcade_read16(ARCADE_PLAYER_X_ADDR));
    arcade_write16(WRAM_WORD_0722_ADDR, arcade_read16(ARCADE_PLAYER_Y_ADDR));

    arcade_seed_multipart_helper_actor(WRAM_ACTOR_06C8_ADDR, base_slot, state18, family18);
    arcade_seed_multipart_helper_actor(0x10C9C8, base_slot + 1, 11, 0);

    if (actor_level >= 4)
        arcade_seed_multipart_helper_actor(0x10C988, base_slot + 2, 11, 0);

    if (actor_level >= 6)
        arcade_seed_multipart_helper_actor(0x10C948, base_slot + 3, 11, 0);
}

static void emulate_stage_init_master(void)
{
    arcade_504fa_load_stage_spawn_record();
    arcade_5053a_seed_stage_runtime_defaults();
    load_scripted_drop_coords();
    arcade_423b2_seed_05c8_group();
    arcade_457b2_seed_0748_group();
    arcade_4449e_seed_stage_family_actor();
    arcade_45b2e_seed_multipart_helpers();
    arcade_45dfa_build_shadow_lists();
    arcade_write16(WRAM_MODE_FLAG46_ADDR, 0);
}

static bool arcade_469e8_start_gate(void)
{
    if (workram_read16(WRAM_WORD_02A2_ADDR) != 2) return FALSE;
    if (workram_read16(WRAM_WORD_0272_ADDR) == 0) return FALSE;
    return TRUE;
}

static void arcade_3a2d0_clear_words(u32 start_addr, u16 count_words)
{
    u16 i;

    for (i = 0; i <= count_words; i++) arcade_write16(start_addr + ((u32)i * 2), 0);
}

static void shadow_sprite_blank(ShadowSpriteEntry *entry)
{
    entry->word0 = 0;
    entry->word1 = 0;
    entry->word2 = 0x0180;
    entry->word3 = 0;
}

static void shadow_sprite_emit(ShadowSpriteEntry *entry, u8 d0, u8 d6, u8 d7, u16 d2)
{
    entry->word0 = ((u16)d6 << 8) | d7;
    entry->word1 = d2;
    entry->word2 = d0;
    entry->word3 = 0;
}

static void push_render_part(s16 x, s16 y, u16 tile_index)
{
    if (render_part_count >= (sizeof(render_parts) / sizeof(render_parts[0]))) return;

    render_parts[render_part_count].x = x;
    render_parts[render_part_count].y = y;
    render_parts[render_part_count].tile_index = tile_index;
    render_part_count++;
}

static u16 maincpu_be16(u32 addr)
{
    return ((u16)rastan_maincpu[addr] << 8) | rastan_maincpu[addr + 1];
}

static s16 signed_byte(u8 value)
{
    return (value & 0x80) ? (s16)(value - 0x100) : (s16)value;
}

static void arcade_4543e_refresh_actor_fields_generic(u32 actor_addr)
{
    u32 table_addr = 0x45502;
    u8 index;

    if (workram_read8(actor_addr + 62) == 2)
    {
        const u8 family = workram_read8(actor_addr + 56);
        table_addr = 0x454BA;
        if (family != 0)
        {
            table_addr = 0x454D2;
            if (family != 3) table_addr = 0x454EA;
        }
        index = workram_read8(actor_addr + 0x0752);
    }
    else
    {
        if (workram_read8(actor_addr + 0x0752) != 0) table_addr = 0x45562;
        index = workram_read8(actor_addr + 6) - 8;
    }

    table_addr += ((u32)index * 8);
    arcade_write16(actor_addr + 30, maincpu_be16(table_addr));
    arcade_write8(actor_addr + 58, rastan_maincpu[table_addr + 2]);
    arcade_write8(actor_addr + 1, rastan_maincpu[table_addr + 3]);
    arcade_write16(actor_addr + 40, maincpu_be16(table_addr + 4));
    arcade_write16(actor_addr + 44, maincpu_be16(table_addr + 6));
}

static u16 arcade_family1_emit_shadow(ShadowSpriteEntry *entry, u32 actor_addr)
{
    s16 x = (s16)workram_read16(actor_addr + 22);
    s16 y = (s16)workram_read16(actor_addr + 26);
    const u8 state = workram_read8(actor_addr + 6);
    u16 tile = workram_read16(actor_addr + 30);
    u16 parts = 1;

    switch (state)
    {
        case 10:
            x += -18;
            y += -48;
            tile = 0x0345;
            parts = 5;
            break;
        case 11:
            x += -8;
            y += -32;
            tile = 0x02E8;
            parts = 8;
            break;
        case 15:
            x += -8;
            y += -32;
            tile = 0x043A;
            parts = 8;
            break;
        default:
            break;
    }

    entry->word0 = (u16)y;
    entry->word1 = tile;
    entry->word2 = (u16)x;
    entry->word3 = ((u16)workram_read8(actor_addr + 56) << 8) | state;
    return parts;
}

static u16 arcade_family1_push_parts(u32 actor_addr)
{
    const u8 frame_code = workram_read8(actor_addr + 1);
    const u16 tile_base = workram_read16(actor_addr + 30);
    s16 base_x = (s16)workram_read16(actor_addr + 22);
    s16 base_y = (s16)workram_read16(actor_addr + 26);
    const u32 frame_offset = FAMILY1_TABLE_ADDR + maincpu_be16(FAMILY1_TABLE_ADDR + ((u32)frame_code * 2));
    u32 record_offset = frame_offset;
    u16 count = 0;

    rendered_actor_family = workram_read8(actor_addr + 56);
    rendered_actor_class = workram_read8(actor_addr + 6);
    rendered_actor_state = workram_read8(actor_addr + 5);
    rendered_actor_frame = frame_code;
    rendered_actor_tile_base = tile_base;

    while (rastan_maincpu[record_offset] != 0xFF)
    {
        const s16 part_y = signed_byte(rastan_maincpu[record_offset + 1]);
        const u16 tile_index = tile_base + rastan_maincpu[record_offset + 2];
        const s16 part_x = signed_byte(rastan_maincpu[record_offset + 3]);

        push_render_part(base_x + part_x, base_y + part_y, tile_index);
        record_offset += 4;
        count++;

        if (count >= 16) break;
    }

    return count;
}

static void decode_arcade_16x16_tile(u16 tile_index, u32 *dst_words)
{
    const u8 *src = rastan_pc090oj + ((u32)tile_index * 128);
    u8 *dst = (u8 *)dst_words;
    u16 y;

    for (y = 0; y < 8; y++)
    {
        memcpy(dst + (y * 4), src + (y * 8), 4);
        memcpy(dst + 32 + (y * 4), src + (y * 8) + 4, 4);
        memcpy(dst + 64 + (y * 4), src + ((y + 8) * 8), 4);
        memcpy(dst + 96 + (y * 4), src + ((y + 8) * 8) + 4, 4);
    }
}

static void draw_arcade_render_parts(void)
{
    u16 i;
    u16 vram_tile = 256;
    const s16 stage_origin_x = STAGE_VIEW_X_CHARS * 8;
    const s16 stage_origin_y = STAGE_VIEW_Y_CHARS * 8;

    VDP_resetSprites();

    for (i = 0; i < render_part_count; i++)
    {
        const s16 screen_x = stage_origin_x + (render_parts[i].x >> 1);
        const s16 screen_y = stage_origin_y + (render_parts[i].y >> 1);

        decode_arcade_16x16_tile(render_parts[i].tile_index, &decoded_sprite_tiles[i * 32]);
        VDP_loadTileData(&decoded_sprite_tiles[i * 32], vram_tile, 4, CPU);
        VDP_setSpriteFull(
            i,
            screen_x,
            screen_y,
            SPRITE_SIZE(2, 2),
            TILE_ATTR_FULL(PAL0, FALSE, FALSE, FALSE, vram_tile),
            (i + 1 < render_part_count) ? (i + 1) : 0
        );
        vram_tile += 4;
    }

    if (render_part_count == 0)
        VDP_setSpriteFull(0, 0, 0, SPRITE_SIZE(1, 1), TILE_ATTR_FULL(PAL0, FALSE, FALSE, FALSE, 0), 0);

    VDP_updateSprites(render_part_count ? render_part_count : 1, CPU);
}

static void record_render_candidate(u32 actor_addr, u8 slot)
{
    rendered_actor_slot = slot;
    rendered_actor_class = workram_read8(actor_addr + 6);
    rendered_actor_family = workram_read8(actor_addr + 56);
    rendered_actor_state = workram_read8(actor_addr + 5);
    rendered_actor_frame = workram_read8(actor_addr + 1);
    rendered_actor_tile_base = workram_read16(actor_addr + 30);
}

static void arcade_select_02c8_render_candidate(void)
{
    const u32 actor_addr = WRAM_ACTOR_02C8_ADDR + ((u32)selected_02c8_slot * ACTOR_STRIDE);

    record_render_candidate(actor_addr, selected_02c8_slot);

    if (!workram_read8(actor_addr)) return;
    if (workram_read8(actor_addr + 3)) return;
    if (!workram_read8(actor_addr + 5)) return;
    if (workram_read8(actor_addr + 56) != 1) return;

    arcade_family1_push_parts(actor_addr);
}

static void arcade_45dfa_process_group(u32 actor_base, u16 group_slots, u16 d2_low, u16 d2_high, ShadowSpriteEntry *target, u16 target_slots, u16 count_index)
{
    u16 i;

    arcade_write16(WRAM_WORD_0214_ADDR, 0);
    sprite_group_counts[count_index] = 0;
    sprite_part_counts[count_index] = 0;

    for (i = 0; i < target_slots; i++)
    {
        const u32 actor_addr = actor_base + ((u32)i * ACTOR_STRIDE);
        const u16 actor_index = workram_read16(WRAM_WORD_0214_ADDR);

        if (i >= group_slots)
        {
            shadow_sprite_blank(&target[i]);
            continue;
        }

        if (workram_read8(actor_addr) == 0)
        {
            shadow_sprite_blank(&target[i]);
        }
        else
        {
            const u8 d0 = workram_read8(actor_addr + 1);
            const u8 d6 = workram_read8(actor_addr + 32);
            const u8 d7 = workram_read8(actor_addr + 2);
            const u16 d2 = actor_index < 3 ? d2_low : d2_high;
            const u8 family = workram_read8(actor_addr + 56);

            if (family == 1)
            {
                sprite_part_counts[count_index] += arcade_family1_emit_shadow(&target[i], actor_addr);
            }
            else
                shadow_sprite_emit(&target[i], d0, d6, d7, d2);
            sprite_group_counts[count_index]++;
        }

        arcade_write16(WRAM_WORD_0214_ADDR, actor_index + 1);
    }
}

static void arcade_3b902_stub(u16 d1)
{
    (void)d1;
}

static void arcade_41f5e_stub(void)
{
    stage_ready = TRUE;
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
    const u16 mode = workram_read16(WRAM_MODE_ADDR);

    if ((pad & (BUTTON_A | BUTTON_B | BUTTON_C | BUTTON_START)) == (BUTTON_A | BUTTON_B | BUTTON_C | BUTTON_START))
    {
        seed_initial_state();
        return;
    }

    if ((mode == 2) && (pressed & BUTTON_A))
    {
        selected_02c8_slot = (selected_02c8_slot + 8) % 9;
    }

    if ((mode == 2) && (pressed & (BUTTON_B | BUTTON_C)))
    {
        selected_02c8_slot = (selected_02c8_slot + 1) % 9;
    }

    if ((mode != 2) && (pressed & BUTTON_C))
    {
        credits++;
        sound_shadow[0] = 0x0001;
    }

    if ((pressed & BUTTON_START) && credits && !game_started)
    {
        start_request_latched = TRUE;
        arcade_write16(WRAM_WORD_0272_ADDR, 1);
    }
}

static void arcade_41f0e_gameplay_tick(u16 pad)
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
        gameplay_frames++;
        arcade_write16(WRAM_PLAY_READY_ADDR, 3 + (gameplay_frames >> 1));
        arcade_write16(WRAM_PLAY_READY_MIRROR, arcade_read16(WRAM_PLAY_READY_ADDR));
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

    arcade_write16(ARCADE_VIDEO_REG_START, (u16)(frame_counter & 0x1F));
    arcade_write16(ARCADE_VIDEO_REG_START + 2, (u16)player_x);
    arcade_write16(ARCADE_VIDEO_REG_START + 4, (u16)player_y);
    arcade_write8(ARCADE_SOUND_LATCH_START, (u8)(pad & 0xFF));
}

/* Direct translation of arcade routine 0x45dfa..0x45ef8 using shadow sprite lists. */
static void arcade_45dfa_build_shadow_lists(void)
{
    render_part_count = 0;
    player_family1_rendered = FALSE;
    stage_family1_rendered = FALSE;
    rendered_actor_slot = 0xFF;
    rendered_actor_class = 0xFF;
    rendered_actor_family = 0xFF;
    rendered_actor_state = 0xFF;
    rendered_actor_frame = 0xFF;
    rendered_actor_tile_base = 0xFFFF;
    arcade_select_02c8_render_candidate();

    arcade_45dfa_process_group(WRAM_ACTOR_05C8_ADDR, 6, 10, 20, sprite_list_0460, 10, 0);
    arcade_45dfa_process_group(WRAM_ACTOR_0748_ADDR, 6, 6, 6, sprite_list_0170, 6, 1);
    arcade_45dfa_process_group(0x10C8C8, 5, 4, 4, sprite_list_0300, 4, 2);
}

/* Direct translation of arcade routine 0x3a7fa..0x3a830 with local stubs. */
static void arcade_3a7fa_commit_start(void)
{
    if (!start_request_latched) return;
    if (!arcade_469e8_start_gate()) return;

    start_request_latched = FALSE;
    credits--;
    game_started = TRUE;
    stage_ready = FALSE;
    gameplay_frames = 0;

    arcade_write16(WRAM_ACTOR_02C8_ADDR, 0);
    arcade_3a2d0_clear_words(WRAM_ACTOR_02C8_ADDR, 0x03FF);
    arcade_3b902_stub(1);
    arcade_write16(WRAM_MODE8_ADDR, 8);
    arcade_write16(WRAM_MODE_ADDR, 1);
    emulate_stage_init_master();
}

/* Direct translation of arcade routine 0x3a832..0x3a85e with local stubs. */
static void arcade_3a832_wait_for_play(u16 pad)
{
    arcade_3a772_read_input_ports();
    arcade_41f0e_gameplay_tick(pad);
    if (arcade_read16(WRAM_PLAY_READY_ADDR) != 16) return;

    arcade_write16(WRAM_MODE_FLAG46_ADDR, 2);
    arcade_write16(WRAM_READY_FLAG_ADDR, 1);
    arcade_write16(WRAM_MODE9_ADDR, 9);
    arcade_41f5e_stub();
    arcade_write16(WRAM_MODE_ADDR, 2);
    copy_drop_to_live_player();
}

/* Direct translation of arcade routine 0x3a79c..0x3a85e with local stubs. */
static void arcade_3a79c_mode_dispatch(u16 pad)
{
    u16 d0 = workram_read16(WRAM_MODE_ADDR);

    if (d0 == 0)
    {
        arcade_3a772_read_input_ports();
        arcade_write16(WRAM_FRAME_0200_ADDR, workram_read16(WRAM_FRAME_0200_ADDR) + 1);
        arcade_41f0e_gameplay_tick(pad);

        if ((arcade_read8(ARCADE_INPUT_DIP) & 0x02) == 0)
        {
            arcade_write16(WRAM_MODE_ADDR, 0);
            arcade_write16(WRAM_SUBMODE_ADDR, 4);
            return;
        }

        arcade_write16(WRAM_MODE_FLAG46_ADDR, 0);
        if (arcade_read16(WRAM_PLAY_READY_ADDR) == 7)
        {
            arcade_write16(WRAM_SELECTED_STAGE_ADDR, workram_read16(WRAM_STAGE_ID_ADDR));
            arcade_write16(WRAM_MODE_FLAG46_ADDR, 1);
            arcade_write16(WRAM_MODE_ADDR, 2);
            arcade_write8(WRAM_BYTE_0104_ADDR, 1);
            arcade_write16(WRAM_SUBMODE_ADDR, 2);
            return;
        }

        arcade_3a7fa_commit_start();
        return;
    }

    d0--;
    if (d0 == 0)
    {
        arcade_3a832_wait_for_play(pad);
        return;
    }

    arcade_41f0e_gameplay_tick(pad);
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
    s16 x;
    s16 y;

    for (y = 0; y < STAGE_VIEW_H_CHARS; y++)
    {
        for (x = 0; x < STAGE_VIEW_W_CHARS; x++)
        {
            if (y == STAGE_VIEW_H_CHARS - 1) VDP_drawText("#", STAGE_VIEW_X_CHARS + x, STAGE_VIEW_Y_CHARS + y);
            else if (x == 0 || x == STAGE_VIEW_W_CHARS - 1) VDP_drawText("|", STAGE_VIEW_X_CHARS + x, STAGE_VIEW_Y_CHARS + y);
            else VDP_drawText(".", STAGE_VIEW_X_CHARS + x, STAGE_VIEW_Y_CHARS + y);
        }
    }

    VDP_drawText("D", STAGE_VIEW_X_CHARS + (drop_x >> 4), STAGE_VIEW_Y_CHARS + (drop_y >> 4));
    VDP_drawText("P", STAGE_VIEW_X_CHARS + (player_x >> 4), STAGE_VIEW_Y_CHARS + (player_y >> 4));
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
    sprintf(line, "SPR GROUPS %u %u %u", sprite_group_counts[0], sprite_group_counts[1], sprite_group_counts[2]);
    VDP_drawText(line, 1, 9);
    sprintf(line, "SPR PARTS  %u %u %u", sprite_part_counts[0], sprite_part_counts[1], sprite_part_counts[2]);
    VDP_drawText(line, 1, 10);
    sprintf(line, "SEL %u 02C8 %u C%u F%u",
        selected_02c8_slot,
        rendered_actor_slot == 0xFF ? 0 : rendered_actor_slot,
        rendered_actor_class == 0xFF ? 0 : rendered_actor_class,
        rendered_actor_family == 0xFF ? 0 : rendered_actor_family);
    VDP_drawText(line, 1, 11);
    sprintf(line, "S%u FR%02X TB%04X",
        rendered_actor_state == 0xFF ? 0 : rendered_actor_state,
        rendered_actor_frame == 0xFF ? 0 : rendered_actor_frame,
        rendered_actor_tile_base == 0xFFFF ? 0 : rendered_actor_tile_base);
    VDP_drawText(line, 1, 12);

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

    VDP_drawText("PLAY: A/B/C=02c8 slot  START=start", 1, 27);
}

int main(bool hardReset)
{
    const u16 unused_hard_reset = hardReset;

    (void)unused_hard_reset;

    SYS_disableInts();
    VDP_setScreenWidth320();
    PAL_setPalette(PAL0, arcade_sprite_palette, CPU);
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
        arcade_3a79c_mode_dispatch(pad);
        draw_arcade_render_parts();
        draw_debug_hud();
        previous_pad = pad;
        frame_counter++;
        SYS_doVBlankProcess();
    }

    return 0;
}
