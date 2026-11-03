    .text
    .align 2

    .globl genesistan_run_original_startup_common
    .globl genesistan_startup_common_exit_normal
    .globl genesistan_startup_common_exit_test

genesistan_run_original_startup_common:
    movel #0xC0000000,0x00C00004
    movew #0x0E00,0x00C00000
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    jsr 0x03AE86
    movel #0xC0000000,0x00C00004
    movew #0x00E0,0x00C00000
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

genesistan_startup_common_exit_normal:
    addq.l #4,%sp
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

genesistan_startup_common_exit_test:
    addq.l #4,%sp
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts
