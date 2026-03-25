#include <genesis.h>
#include <string.h>

#include "build_info.h"

#ifndef RASTAN_EXCEPTION_DUMPER_MODE
#define RASTAN_EXCEPTION_DUMPER_MODE 0
#endif

#if RASTAN_EXCEPTION_DUMPER_MODE == 2
#include "qrcodegen.h"
#endif

#if RASTAN_EXCEPTION_DUMPER_MODE != 0

#define RASTAN_QR_EX_BUS       1
#define RASTAN_QR_EX_ADDR      2
#define RASTAN_QR_EX_ILL       3
#define RASTAN_QR_EX_ZDIV      4
#define RASTAN_QR_EX_CHK       5
#define RASTAN_QR_EX_TRAPV     6
#define RASTAN_QR_EX_PRIV      7
#define RASTAN_QR_EX_TRACE     8
#define RASTAN_QR_EX_LINE1010  9
#define RASTAN_QR_EX_LINE1111 10
#define RASTAN_QR_EX_ERROR    11

volatile u16 rastan_qr_exc_type;
volatile u32 rastan_qr_exc_d[8];
volatile u32 rastan_qr_exc_a[8];
volatile u32 rastan_qr_exc_ssp;
volatile u32 rastan_qr_exc_usp;
volatile u16 rastan_qr_exc_frame_words[16];

static u32 words_to_u32(u16 hi, u16 lo)
{
    return (((u32)hi) << 16) | (u32)lo;
}

static const char *exception_name_from_type(u16 ex_type)
{
    switch (ex_type)
    {
        case RASTAN_QR_EX_BUS: return "BUS_ERROR";
        case RASTAN_QR_EX_ADDR: return "ADDRESS_ERROR";
        case RASTAN_QR_EX_ILL: return "ILLEGAL_INST";
        case RASTAN_QR_EX_ZDIV: return "ZERO_DIVIDE";
        case RASTAN_QR_EX_CHK: return "CHK_INST";
        case RASTAN_QR_EX_TRAPV: return "TRAPV_INST";
        case RASTAN_QR_EX_PRIV: return "PRIVILEGE";
        case RASTAN_QR_EX_TRACE: return "TRACE";
        case RASTAN_QR_EX_LINE1010: return "LINE_1010";
        case RASTAN_QR_EX_LINE1111: return "LINE_1111";
        case RASTAN_QR_EX_ERROR: return "ERROR";
        default: return "UNKNOWN";
    }
}

static void decode_exception_frame(u16 *sr, u32 *pc, u32 *fault_addr, u16 *ext1, u16 *ext2)
{
    const volatile u16 *fw = rastan_qr_exc_frame_words;
    const u16 ex_type = rastan_qr_exc_type;

    *sr = fw[0];
    *pc = words_to_u32(fw[1], fw[2]);
    *fault_addr = 0;
    *ext1 = 0;
    *ext2 = 0;

    if ((ex_type == RASTAN_QR_EX_BUS) || (ex_type == RASTAN_QR_EX_ADDR))
    {
        *ext1 = fw[0];
        *fault_addr = words_to_u32(fw[1], fw[2]);
        *ext2 = fw[3];
        *sr = fw[4];
        *pc = words_to_u32(fw[5], fw[6]);
    }
    else if ((ex_type == RASTAN_QR_EX_ILL) || (ex_type == RASTAN_QR_EX_CHK) || (ex_type == RASTAN_QR_EX_TRAPV))
    {
        *sr = fw[0];
        *pc = words_to_u32(fw[1], fw[2]);
        *ext1 = fw[3];
    }
}

#if RASTAN_EXCEPTION_DUMPER_MODE == 1
static bool is_probable_rom_addr(u32 value)
{
    return (value >= 0x000200UL) && (value <= 0x3FFFFFUL);
}

static u16 collect_backtrace(u32 out_bt[6], u32 pc)
{
    u16 i;
    u16 count = 0;

    memset(out_bt, 0, sizeof(u32) * 6);

    out_bt[count++] = pc & 0x00FFFFFFUL;

    for (i = 0; (i < 15) && (count < 6); i++)
    {
        u16 j;
        bool duplicate = FALSE;
        const u32 candidate = words_to_u32(rastan_qr_exc_frame_words[i], rastan_qr_exc_frame_words[i + 1]) & 0x00FFFFFFUL;

        if (!is_probable_rom_addr(candidate))
        {
            continue;
        }

        for (j = 0; j < count; j++)
        {
            if (out_bt[j] == candidate)
            {
                duplicate = TRUE;
                break;
            }
        }

        if (!duplicate)
        {
            out_bt[count++] = candidate;
        }
    }

    return count;
}

static void draw_text_mode(u16 sr, u32 pc)
{
    char line[41];
    u32 bt[6];

    (void)collect_backtrace(bt, pc);

    VDP_setScreenWidth320();
    VDP_setPlaneSize(64, 32, FALSE);
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);

    PAL_setColor(0, RGB24_TO_VDPCOLOR(0x000000));
    PAL_setColor(15, RGB24_TO_VDPCOLOR(0xFFFFFF));

    sprintf(line, "EX %-13s C%02X  B%u", exception_name_from_type(rastan_qr_exc_type), (unsigned)rastan_qr_exc_type, (unsigned)RASTAN_BUILD_NUMBER);
    VDP_drawText(line, 0, 0);

    sprintf(line, "PC %08lX  SR %04X", (unsigned long)pc, (unsigned)sr);
    VDP_drawText(line, 0, 1);

    sprintf(line, "A0 %08lX  A1 %08lX", (unsigned long)rastan_qr_exc_a[0], (unsigned long)rastan_qr_exc_a[1]);
    VDP_drawText(line, 0, 2);

    sprintf(line, "A5 %08lX  SP %08lX", (unsigned long)rastan_qr_exc_a[5], (unsigned long)rastan_qr_exc_ssp);
    VDP_drawText(line, 0, 3);

    sprintf(line, "D0 %08lX  D1 %08lX", (unsigned long)rastan_qr_exc_d[0], (unsigned long)rastan_qr_exc_d[1]);
    VDP_drawText(line, 0, 4);

    sprintf(line, "BT %06lX %06lX %06lX",
            (unsigned long)(bt[0] & 0x00FFFFFFUL),
            (unsigned long)(bt[1] & 0x00FFFFFFUL),
            (unsigned long)(bt[2] & 0x00FFFFFFUL));
    VDP_drawText(line, 0, 6);

    sprintf(line, "   %06lX %06lX %06lX",
            (unsigned long)(bt[3] & 0x00FFFFFFUL),
            (unsigned long)(bt[4] & 0x00FFFFFFUL),
            (unsigned long)(bt[5] & 0x00FFFFFFUL));
    VDP_drawText(line, 0, 7);

    sprintf(line, "S0 %04X %04X %04X %04X",
            (unsigned)rastan_qr_exc_frame_words[0],
            (unsigned)rastan_qr_exc_frame_words[1],
            (unsigned)rastan_qr_exc_frame_words[2],
            (unsigned)rastan_qr_exc_frame_words[3]);
    VDP_drawText(line, 0, 9);

    sprintf(line, "S1 %04X %04X %04X %04X",
            (unsigned)rastan_qr_exc_frame_words[4],
            (unsigned)rastan_qr_exc_frame_words[5],
            (unsigned)rastan_qr_exc_frame_words[6],
            (unsigned)rastan_qr_exc_frame_words[7]);
    VDP_drawText(line, 0, 10);

    sprintf(line, "S2 %04X %04X %04X %04X",
            (unsigned)rastan_qr_exc_frame_words[8],
            (unsigned)rastan_qr_exc_frame_words[9],
            (unsigned)rastan_qr_exc_frame_words[10],
            (unsigned)rastan_qr_exc_frame_words[11]);
    VDP_drawText(line, 0, 11);

    VDP_waitDMACompletion();
}
#endif

#if RASTAN_EXCEPTION_DUMPER_MODE == 2

#define RASTAN_QR_TILE_BASE 1536
#define RASTAN_QR_TILE_VARIANTS 16
#define RASTAN_QR_QUIET_ZONE 2
#define RASTAN_QR_DRAW_START_Y 5

static u8 rastan_qr_temp[qrcodegen_BUFFER_LEN_MAX];
static u8 rastan_qr_data[qrcodegen_BUFFER_LEN_MAX];
static u8 rastan_qr_tiles[RASTAN_QR_TILE_VARIANTS * 32];

static void build_qr_tiles(void)
{
    u16 variant;

    for (variant = 0; variant < RASTAN_QR_TILE_VARIANTS; variant++)
    {
        u8 *tile = &rastan_qr_tiles[variant * 32];
        const u8 tl = (variant & 0x1) ? 2 : 1;
        const u8 tr = (variant & 0x2) ? 2 : 1;
        const u8 bl = (variant & 0x4) ? 2 : 1;
        const u8 br = (variant & 0x8) ? 2 : 1;
        u16 y;

        for (y = 0; y < 8; y++)
        {
            const u8 left = (y < 4) ? tl : bl;
            const u8 right = (y < 4) ? tr : br;
            const u16 row = y * 4;

            tile[row + 0] = (u8)((left << 4) | left);
            tile[row + 1] = (u8)((left << 4) | left);
            tile[row + 2] = (u8)((right << 4) | right);
            tile[row + 3] = (u8)((right << 4) | right);
        }
    }
}

static bool qr_module_is_dark(const u8 *qrcode, s16 size, s16 x, s16 y)
{
    if ((x < 0) || (y < 0) || (x >= size) || (y >= size))
    {
        return FALSE;
    }

    return qrcodegen_getModule(qrcode, x, y) ? TRUE : FALSE;
}

static void draw_qr_code(const u8 *qrcode)
{
    const s16 size = qrcodegen_getSize(qrcode);
    const s16 total_modules = size + (RASTAN_QR_QUIET_ZONE * 2);
    const s16 tile_w = (total_modules + 1) / 2;
    const s16 tile_h = (total_modules + 1) / 2;
    const s16 start_x = (40 - tile_w) / 2;
    const s16 start_y = RASTAN_QR_DRAW_START_Y;
    s16 ty;

    for (ty = 0; ty < tile_h; ty++)
    {
        s16 tx;
        for (tx = 0; tx < tile_w; tx++)
        {
            const s16 mx = (tx * 2) - RASTAN_QR_QUIET_ZONE;
            const s16 my = (ty * 2) - RASTAN_QR_QUIET_ZONE;
            const u16 b0 = qr_module_is_dark(qrcode, size, mx + 0, my + 0) ? 1 : 0;
            const u16 b1 = qr_module_is_dark(qrcode, size, mx + 1, my + 0) ? 1 : 0;
            const u16 b2 = qr_module_is_dark(qrcode, size, mx + 0, my + 1) ? 1 : 0;
            const u16 b3 = qr_module_is_dark(qrcode, size, mx + 1, my + 1) ? 1 : 0;
            const u16 variant = b0 | (b1 << 1) | (b2 << 2) | (b3 << 3);
            const u16 tile_attr = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, (u16)(RASTAN_QR_TILE_BASE + variant));

            VDP_setTileMapXY(BG_A, tile_attr, (u16)(start_x + tx), (u16)(start_y + ty));
        }
    }
}

static void build_full_payload(char *payload,
                               u16 sr,
                               u32 pc,
                               u32 fault_addr,
                               u16 ext1,
                               u16 ext2)
{
    sprintf(
        payload,
        "V1|E%02X|P%08lX|S%04X|0%08lX|1%08lX|A0%08lX|A1%08lX|A5%08lX|T%08lX|U%08lX|W%04X%04X%04X%04X|F%08lX|B%u",
        (unsigned)rastan_qr_exc_type,
        (unsigned long)pc,
        (unsigned)sr,
        (unsigned long)rastan_qr_exc_d[0],
        (unsigned long)rastan_qr_exc_d[1],
        (unsigned long)rastan_qr_exc_a[0],
        (unsigned long)rastan_qr_exc_a[1],
        (unsigned long)rastan_qr_exc_a[5],
        (unsigned long)rastan_qr_exc_ssp,
        (unsigned long)rastan_qr_exc_usp,
        (unsigned)rastan_qr_exc_frame_words[0],
        (unsigned)rastan_qr_exc_frame_words[1],
        (unsigned)rastan_qr_exc_frame_words[2],
        (unsigned)rastan_qr_exc_frame_words[3],
        (unsigned long)fault_addr,
        (unsigned)RASTAN_BUILD_NUMBER
    );

    (void)ext1;
    (void)ext2;
}

static void build_fallback_payload(char *payload, u16 sr, u32 pc)
{
    sprintf(
        payload,
        "V1|E%02X|P%08lX|S%04X|A1%08lX|A5%08lX|T%08lX|B%u",
        (unsigned)rastan_qr_exc_type,
        (unsigned long)pc,
        (unsigned)sr,
        (unsigned long)rastan_qr_exc_a[1],
        (unsigned long)rastan_qr_exc_a[5],
        (unsigned long)rastan_qr_exc_ssp,
        (unsigned)RASTAN_BUILD_NUMBER
    );
}

static void draw_qr_mode(u16 sr, u32 pc, u32 fault_addr, u16 ext1, u16 ext2)
{
    char line[41];
    char payload[196];
    bool qr_ok;

    build_qr_tiles();

    VDP_setScreenWidth320();
    VDP_setPlaneSize(64, 32, FALSE);
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);

    PAL_setColor(0, RGB24_TO_VDPCOLOR(0x000000));
    PAL_setColor(16 + 1, RGB24_TO_VDPCOLOR(0xFFFFFF));
    PAL_setColor(16 + 2, RGB24_TO_VDPCOLOR(0x000000));

    VDP_loadTileData((const u32 *)rastan_qr_tiles, RASTAN_QR_TILE_BASE, RASTAN_QR_TILE_VARIANTS, CPU);

    VDP_drawText("RASTAN QR CRASH DUMP", 9, 0);

    sprintf(line, "EX %s  CODE %02X", exception_name_from_type(rastan_qr_exc_type), (unsigned)rastan_qr_exc_type);
    VDP_drawText(line, 0, 1);

    sprintf(line, "PC %08lX  SR %04X", (unsigned long)pc, (unsigned)sr);
    VDP_drawText(line, 0, 2);

    sprintf(line, "A1 %08lX  A5 %08lX", (unsigned long)rastan_qr_exc_a[1], (unsigned long)rastan_qr_exc_a[5]);
    VDP_drawText(line, 0, 3);

    sprintf(line, "SP %08lX  USP %08lX", (unsigned long)rastan_qr_exc_ssp, (unsigned long)rastan_qr_exc_usp);
    VDP_drawText(line, 0, 4);

    build_full_payload(payload, sr, pc, fault_addr, ext1, ext2);
    qr_ok = qrcodegen_encodeText(
        payload,
        rastan_qr_temp,
        rastan_qr_data,
        qrcodegen_Ecc_LOW,
        1,
        6,
        qrcodegen_Mask_AUTO,
        true);

    if (!qr_ok)
    {
        build_fallback_payload(payload, sr, pc);
        qr_ok = qrcodegen_encodeText(
            payload,
            rastan_qr_temp,
            rastan_qr_data,
            qrcodegen_Ecc_LOW,
            1,
            6,
            qrcodegen_Mask_AUTO,
            true);
    }

    if (qr_ok)
    {
        draw_qr_code(rastan_qr_data);
        VDP_drawText("SCAN QR FOR FULL DUMP", 9, 27);
    }
    else
    {
        VDP_drawText("QR ENCODE FAILED", 13, 14);
        VDP_drawText(payload, 0, 27);
    }

    VDP_waitDMACompletion();
}

#endif

void rastan_exception_render(void)
{
    u16 sr;
    u32 pc;
    u32 fault_addr;
    u16 ext1;
    u16 ext2;

    SYS_disableInts();

    decode_exception_frame(&sr, &pc, &fault_addr, &ext1, &ext2);

#if RASTAN_EXCEPTION_DUMPER_MODE == 1
    draw_text_mode(sr, pc);
#elif RASTAN_EXCEPTION_DUMPER_MODE == 2
    draw_qr_mode(sr, pc, fault_addr, ext1, ext2);
#endif
}

#endif
