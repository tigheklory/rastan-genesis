/* ORIGINAL ARCADE PC: 0x00045EFC
 * Ghidra 12 selected-function decompile, normalized for durable syntax.
 * PARTIAL: exact appearance gates only; placement/latches are elided.
 */
#include <stdint.h>
extern uint16_t g_prog13e, g_scr10cc;
extern void scripted_bat_group_create_45b18(void), paired_flying_demon_init_45342(void);
void arcade_45efc_appearance_dispatch(void) {
    switch(g_prog13e) {
    case 0x1a: if(g_scr10cc>=10) scripted_bat_group_create_45b18(); break;
    case 0x1b: paired_flying_demon_init_45342(); break;
    case 0x1e: if(g_scr10cc>=8) scripted_bat_group_create_45b18(); break;
    case 0x20: paired_flying_demon_init_45342(); break;
    case 0x21: if(g_scr10cc>=13) scripted_bat_group_create_45b18(); break;
    case 0x22: if(g_scr10cc==6) paired_flying_demon_init_45342(); break;
    case 0x23: if(g_scr10cc>=13) scripted_bat_group_create_45b18(); break;
    case 0x25: if(g_scr10cc==8) paired_flying_demon_init_45342(); break;
    case 0x2a: if(g_scr10cc>=11) scripted_bat_group_create_45b18(); break;
    default: break;
    }
}
