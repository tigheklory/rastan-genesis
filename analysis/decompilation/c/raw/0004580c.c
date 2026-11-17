/* ORIGINAL ARCADE PC: 0x0004580C
 * Ghidra 12 selected-function decompile, normalized for durable syntax.
 * PARTIAL: appearance decisions only; coordinate/sound tails are elided.
 */
#include <stdint.h>
extern uint16_t g_prog13e, g_scr10cc;
extern void scripted_bat_group_create_45b18(void), paired_flying_demon_init_45342(void);
void arcade_4580c_appearance_dispatch(void) {
    switch (g_prog13e) {
    case 2: if(g_scr10cc>=8) scripted_bat_group_create_45b18(); break;
    case 5: if(g_scr10cc>=11) scripted_bat_group_create_45b18(); break;
    case 7: if(g_scr10cc>=9) scripted_bat_group_create_45b18(); break;
    case 9: paired_flying_demon_init_45342(); break;
    case 13: if(g_scr10cc==6){paired_flying_demon_init_45342();scripted_bat_group_create_45b18();} break;
    case 17: if(g_scr10cc>=6) scripted_bat_group_create_45b18(); break;
    default: break;
    }
}
