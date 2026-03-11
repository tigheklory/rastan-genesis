#include <genesis.h>

#include "main.h"

static const u16 white_text_palette[16] = {
    RGB24_TO_VDPCOLOR(0x000000), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF),
    RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF),
    RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF),
    RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF), RGB24_TO_VDPCOLOR(0xFFFFFF),
};

static const u16 red_text_palette[16] = {
    RGB24_TO_VDPCOLOR(0x000000), RGB24_TO_VDPCOLOR(0xFF2020), RGB24_TO_VDPCOLOR(0xFF2020), RGB24_TO_VDPCOLOR(0xFF2020),
    RGB24_TO_VDPCOLOR(0xFF2020), RGB24_TO_VDPCOLOR(0xFF2020), RGB24_TO_VDPCOLOR(0xFF2020), RGB24_TO_VDPCOLOR(0xFF2020),
    RGB24_TO_VDPCOLOR(0xFF2020), RGB24_TO_VDPCOLOR(0xFF2020), RGB24_TO_VDPCOLOR(0xFF2020), RGB24_TO_VDPCOLOR(0xFF2020),
    RGB24_TO_VDPCOLOR(0xFF2020), RGB24_TO_VDPCOLOR(0xFF2020), RGB24_TO_VDPCOLOR(0xFF2020), RGB24_TO_VDPCOLOR(0xFF2020),
};


int main(bool hardReset)
{
    SYS_disableInts();

    VDP_setScreenWidth320();
    PAL_setPalette(PAL0, palette_black, CPU);
    VDP_setTextPalette(PAL1);
    PAL_setPalette(PAL1, palette_grey, CPU);

    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);

    VDP_drawText("RASTAN GENESIS", 11, 8);
    VDP_drawText("HELLO WORLD TEST", 9, 10);
    VDP_drawText("PRESS START OR A/B/C", 7, 13);
    VDP_drawText("TRY DPAD TOO", 13, 15);
    VDP_drawText("INPUT STATUS:", 11, 18);
    VDP_drawText("NO INPUT            ", 11, 20);

    SYS_enableInts();

    while (TRUE)
    {
        const u16 state = JOY_readJoypad(JOY_1);

        if (state & BUTTON_START)
        {
            PAL_setPalette(PAL1, red_text_palette, CPU);
            VDP_drawText("START DETECTED      ", 11, 20);
        }
        else if (state & BUTTON_A)
        {
            PAL_setPalette(PAL1, red_text_palette, CPU);
            VDP_drawText("BUTTON A DETECTED   ", 11, 20);
        }
        else if (state & BUTTON_B)
        {
            PAL_setPalette(PAL1, red_text_palette, CPU);
            VDP_drawText("BUTTON B DETECTED   ", 11, 20);
        }
        else if (state & BUTTON_C)
        {
            PAL_setPalette(PAL1, red_text_palette, CPU);
            VDP_drawText("BUTTON C DETECTED   ", 11, 20);
        }
        else if (state & BUTTON_UP)
        {
            PAL_setPalette(PAL1, red_text_palette, CPU);
            VDP_drawText("UP DETECTED         ", 11, 20);
        }
        else if (state & BUTTON_DOWN)
        {
            PAL_setPalette(PAL1, red_text_palette, CPU);
            VDP_drawText("DOWN DETECTED       ", 11, 20);
        }
        else if (state & BUTTON_LEFT)
        {
            PAL_setPalette(PAL1, red_text_palette, CPU);
            VDP_drawText("LEFT DETECTED       ", 11, 20);
        }
        else if (state & BUTTON_RIGHT)
        {
            PAL_setPalette(PAL1, red_text_palette, CPU);
            VDP_drawText("RIGHT DETECTED      ", 11, 20);
        }
        else
        {
            PAL_setPalette(PAL1, white_text_palette, CPU);
            VDP_drawText("NO INPUT            ", 11, 20);
        }

        SYS_doVBlankProcess();
    }

    return 0;
}
