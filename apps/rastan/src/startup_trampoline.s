    .text
    .align 2

#ifndef RASTAN_ENABLE_STARTUP_HOOK
#define RASTAN_ENABLE_STARTUP_HOOK 1
#endif

    .globl genesistan_run_original_startup_common
    .globl genesistan_run_original_frontend_tick
    .globl genesistan_startup_common_continue_normal
    .globl genesistan_startup_common_exit_normal
    .globl genesistan_startup_common_exit_test
    .globl genesistan_sound_send_command
    .globl genesistan_sound_read_status

#if RASTAN_ENABLE_STARTUP_HOOK

#define ARCADE_ROM_BASE 0x000200

genesistan_sound_send_command:
    move.b #0, genesistan_shadow_reg_3e0001
    move.b %d0, genesistan_sound_last_command
    move.b %d0, genesistan_sound_last_low_nibble
    move.b %d0, genesistan_shadow_reg_3e0003
    lsr.b #4, %d0
    move.b %d0, genesistan_sound_last_high_nibble
    move.b %d0, genesistan_shadow_reg_3e0003
    addq.w #1, genesistan_sound_command_count
    rts

genesistan_sound_read_status:
    move.b #4, genesistan_shadow_reg_3e0001
    moveq #0, %d0
    move.b genesistan_sound_status, %d0
    move.b %d0, genesistan_shadow_reg_3e0003
    rts

genesistan_run_original_startup_common:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    jsr (0x03AE86 + ARCADE_ROM_BASE)
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

genesistan_run_original_frontend_tick:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    lea genesistan_arcade_workram_words, %a5
    moveq #0, %d0
    move.l #genesistan_frontend_tick_return, -(%sp)
    move.w %sr, -(%sp)
    jmp (0x03A008 + ARCADE_ROM_BASE)

genesistan_frontend_tick_return:
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

genesistan_startup_common_continue_normal:
    move.w #1, genesistan_startup_result_code
    move.w #0x00EF, %d0
    jsr (0x03F084 + ARCADE_ROM_BASE)
    move.w #0x00AA, 74(%a5)
    jsr (0x03B8B0 + ARCADE_ROM_BASE)
    jsr (0x03B098 + ARCADE_ROM_BASE)
    jsr (0x03ADD8 + ARCADE_ROM_BASE)
    jsr (0x03AE28 + ARCADE_ROM_BASE)
    jmp genesistan_startup_common_exit_normal

genesistan_startup_common_exit_normal:
    addq.l #4,%sp
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

genesistan_startup_common_exit_test:
    addq.l #4,%sp
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

#else

genesistan_run_original_startup_common:
    rts

genesistan_run_original_frontend_tick:
    rts

genesistan_startup_common_continue_normal:
    rts

genesistan_startup_common_exit_normal:
    rts

genesistan_startup_common_exit_test:
    rts

#endif
