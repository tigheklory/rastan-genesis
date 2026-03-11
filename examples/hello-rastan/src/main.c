#include <genesis.h>

#include "main.h"
#include "res_sprite.h"

static const u16 white_text_palette[16] = {
    RGB24_TO_VDPCOLOR(0x000000), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF),
    RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF),
    RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF),
    RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF),
};


int main(bool hardReset)
{
    s16 x = 144;
    s16 y = 88;

    SYS_disableInts();

    VDP_setScreenWidth320();
    VDP_setTextPalette(PAL1);
    PAL_setPalette(PAL1, white_text_palette, CPU);

    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    VDP_drawText("HELLO RASTAN", 13, 4);
    VDP_drawText("ARCADE SPRITE TEST", 10, 6);
    VDP_drawText("DPAD MOVES", 14, 23);
    VDP_drawText("START RECENTERS", 11, 25);

    SPR_init();

    Sprite *rastan = SPR_addSprite(&spr_rastan, x, y, TILE_ATTR(PAL0, FALSE, FALSE, FALSE));

    SYS_enableInts();

    while (TRUE)
    {
        const u16 state = JOY_readJoypad(JOY_1);

        if (state & BUTTON_LEFT) x--;
        if (state & BUTTON_RIGHT) x++;
        if (state & BUTTON_UP) y--;
        if (state & BUTTON_DOWN) y++;
        if (state & BUTTON_START)
        {
            x = 144;
            y = 88;
        }

        SPR_setPosition(rastan, x, y);
        SPR_update();
        SYS_doVBlankProcess();
    }

    return 0;
}
