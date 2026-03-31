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
    .globl genesistan_hook_text_writer_3bb48
    .globl genesistan_hook_text_writer_3bb48_impl
    .globl genesistan_render_sprites_vdp
    .globl genesistan_render_sprites_vdp_bridge
    .globl genesistan_sprite_commit_asm
    .globl genesistan_asm_tilemap_commit_bg
    .globl genesistan_asm_tilemap_commit_fg

#if RASTAN_ENABLE_STARTUP_HOOK

#define ARCADE_ROM_BASE 0x000200
#define FRONTEND_RUNTIME_SPRITE_LUT_OFFSET 0x28D0
#define FRONTEND_RUNTIME_SPRITE_ATTR_LUT_OFFSET 0x28F4
#define PC080SN_DESC_LIST_OFFSET 0x1000
#define PC080SN_MAINCPU_MAX_ADDR 0x00060000

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

/*
 * 0x03BB48 replacement bridge:
 * keep arcade A5 workram base stable across the C hook.
 */
genesistan_hook_text_writer_3bb48:
    move.l %a5,-(%sp)
    jsr genesistan_hook_text_writer_3bb48_impl
    movea.l (%sp)+,%a5
    rts

/*
 * Sprite replacement bridge:
 * keep full arcade register state stable around the C SAT renderer.
 */
genesistan_render_sprites_vdp_bridge:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    jsr genesistan_render_sprites_vdp
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

/*
 * Non-C SAT commit slice:
 *   - reads Block-A tuples from 0xE0FF11FE
 *   - reads per-entry VRAM tile indices from launcher WRAM LUT (18 entries)
 *   - skips hidden sentinel entries (word1 == 0x0180)
 *   - writes SAT entries directly to VDP data port at VRAM 0xF800
 *
 * Temporary limitations (intentional in this slice):
 *   - size fixed to 2x2 (0x0500 upper bits), link chain built from written entries
 *   - priority hardcoded on, palette hardcoded
 *   - no flipscreen/animation handling here
 */
genesistan_sprite_commit_asm:
    movem.l %d0-%d7/%a0-%a6,-(%sp)

    movea.l #0xC00004, %a1          /* VDP control port */
    movea.l #0xC00000, %a2          /* VDP data port */
    move.w  #0x8F02, (%a1)          /* auto-increment = 2 bytes */
    move.l  #0x78000003, (%a1)      /* VDP_WRITE_VRAM_ADDR(0xF800) */

    movea.l #0xE0FF11FE, %a0        /* Block-A base */
    lea     wram_overlay+FRONTEND_RUNTIME_SPRITE_LUT_OFFSET, %a3
    moveq   #17, %d7                /* 18 entries */
    moveq   #0, %d6                 /* valid/written entry count for link chain */

.Lsprite_count_loop:
    move.w  2(%a0), %d0             /* word1: y */
    cmpi.w  #0x0180, %d0
    beq.s   .Lsprite_count_skip

    move.w  (%a3), %d1              /* per-entry VRAM tile index from prepare step */
    tst.w   %d1
    beq.s   .Lsprite_count_skip

    addq.w  #1, %d6

.Lsprite_count_skip:
    adda.w  #8, %a0
    adda.w  #2, %a3
    dbra    %d7, .Lsprite_count_loop

    movea.l #0xE0FF11FE, %a0        /* Block-A base (write pass) */
    lea     wram_overlay+FRONTEND_RUNTIME_SPRITE_LUT_OFFSET, %a3
    lea     wram_overlay+FRONTEND_RUNTIME_SPRITE_ATTR_LUT_OFFSET, %a4
    moveq   #17, %d7                /* 18 entries */
    moveq   #0, %d5                 /* current written SAT entry index */

.Lsprite_commit_loop:
    move.w  2(%a0), %d0             /* word1: y */
    cmpi.w  #0x0180, %d0
    beq.s   .Lsprite_commit_skip

    addi.w  #0x0080, %d0            /* SAT y bias */

    move.w  (%a3), %d1              /* per-entry VRAM tile index from prepare step */
    tst.w   %d1
    beq.s   .Lsprite_commit_skip
    andi.w  #0x07FF, %d1
    ori.w   #0x8000, %d1
    or.w    (%a4), %d1              /* per-entry pal/flip bits from prepare step */

    move.w  6(%a0), %d2             /* word3: x */
    addi.w  #0x0080, %d2            /* SAT x bias */

    move.w  %d0, (%a2)              /* SAT word0: Y */
    cmpi.w  #1, %d6
    ble.s   .Lsprite_link_last

    move.w  %d5, %d3
    addq.w  #1, %d3
    andi.w  #0x007F, %d3
    ori.w   #0x0500, %d3
    bra.s   .Lsprite_link_ready

.Lsprite_link_last:
    move.w  #0x0500, %d3

.Lsprite_link_ready:
    move.w  %d3, (%a2)              /* SAT word1: size/link */
    move.w  %d1, (%a2)              /* SAT word2: tile/attr */
    move.w  %d2, (%a2)              /* SAT word3: X */
    addq.w  #1, %d5
    subq.w  #1, %d6

.Lsprite_commit_skip:
    adda.w  #8, %a0
    adda.w  #2, %a3
    adda.w  #2, %a4
    dbra    %d7, .Lsprite_commit_loop

    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

/*
 * PC080SN BG tilemap hot path.
 * Args (C ABI, all promoted to 32-bit):
 *   4(%sp):  dest_ptr
 *   8(%sp):  strip_index
 *  12(%sp):  dest_row (raw 0..31)
 *  16(%sp):  dest_col (0..63)
 * Returns:
 *   %d0 = updated dest_ptr
 */
genesistan_asm_tilemap_commit_bg:
    movem.l %d2-%d7/%a2-%a6,-(%sp)

    movea.l #0xC00004, %a5          /* VDP control port */
    movea.l #0xC00000, %a6          /* VDP data port */
    move.w  #0x8F02, (%a5)          /* auto-increment = 2 bytes */

    lea     genesistan_arcade_workram_words+PC080SN_DESC_LIST_OFFSET, %a0
    lea     rastan_maincpu, %a1
    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     genesistan_pc080sn_attr_lut, %a3

    move.l  48(%sp), %d5            /* dest_ptr accumulator */
    move.l  52(%sp), %d7            /* strip_index */
    move.l  56(%sp), %d1            /* dest_row (raw) */
    move.l  60(%sp), %d2            /* dest_col */
    andi.w  #0x001F, %d1
    andi.w  #0x003F, %d2

    moveq   #15, %d6                /* 16 descriptors */

.Lpc080sn_bg_desc_loop:
    move.l  (%a0)+, %d3             /* desc_addr */
    btst    #0, %d3
    bne     .Lpc080sn_bg_invalid
    cmpi.l  #0x0005FFFC, %d3
    bhi     .Lpc080sn_bg_invalid

    movea.l %a1, %a4
    adda.l  %d3, %a4
    move.w  (%a4), %d4              /* attr_word */
    move.w  2(%a4), %d3             /* table_base (u16) */
    cmpi.w  #0x7FE0, %d3
    bhi     .Lpc080sn_bg_invalid

    movea.l %a1, %a4
    move.w  %d3, %d0
    andi.l  #0x0000FFFF, %d0
    adda.l  %d0, %a4
    move.w  %d7, %d0
    lsl.w   #1, %d0
    adda.w  %d0, %a4

    move.w  %d4, %d0
    andi.w  #0x0003, %d0
    move.w  %d4, %d3
    lsr.w   #8, %d3
    lsr.w   #6, %d3
    andi.w  #0x0001, %d3
    lsl.w   #2, %d3
    or.w    %d3, %d0
    move.w  %d4, %d3
    lsr.w   #8, %d3
    lsr.w   #7, %d3
    andi.w  #0x0001, %d3
    lsl.w   #3, %d3
    or.w    %d3, %d0
    move.w  %d4, %d3
    lsr.w   #8, %d3
    lsr.w   #5, %d3
    andi.w  #0x0001, %d3
    lsl.w   #4, %d3
    or.w    %d3, %d0
    add.w   %d0, %d0
    move.w  0(%a3,%d0.w), %d0
    move.w  %d0, -(%sp)             /* attr partial */

    moveq   #3, %d4
.Lpc080sn_bg_row_loop:
    move.w  (%a4), %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    (%sp), %d3

    move.w  %d1, %d0
    cmpi.w  #4, %d0
    blo     .Lpc080sn_bg_skip_write

    subi.w  #4, %d0
    lsl.w   #7, %d0
    add.w   %d2, %d0
    add.w   %d2, %d0
    addi.w  #0xC000, %d0

    move.w  %d4, -(%sp)
    move.w  %d0, %d4
    andi.w  #0x3FFF, %d0
    lsl.l   #8, %d0
    lsl.l   #8, %d0
    lsr.w   #8, %d4
    lsr.w   #6, %d4
    andi.w  #0x0003, %d4
    or.w    %d4, %d0
    ori.l   #0x40000003, %d0
    move.l  %d0, (%a5)
    move.w  %d3, (%a6)
    move.w  (%sp)+, %d4

.Lpc080sn_bg_skip_write:
    adda.w  #8, %a4
    addq.w  #1, %d1
    andi.w  #0x001F, %d1
    dbra    %d4, .Lpc080sn_bg_row_loop

    addq.l  #2, %sp
    bra     .Lpc080sn_bg_desc_done

.Lpc080sn_bg_invalid:
    addq.w  #4, %d1
    andi.w  #0x001F, %d1

.Lpc080sn_bg_desc_done:
    addi.l  #0x00000400, %d5
    dbra    %d6, .Lpc080sn_bg_desc_loop

    move.l  %d5, %d0
    movem.l (%sp)+,%d2-%d7/%a2-%a6
    rts

/*
 * PC080SN FG tilemap hot path.
 * Args/return contract matches genesistan_asm_tilemap_commit_bg.
 */
genesistan_asm_tilemap_commit_fg:
    movem.l %d2-%d7/%a2-%a6,-(%sp)

    movea.l #0xC00004, %a5          /* VDP control port */
    movea.l #0xC00000, %a6          /* VDP data port */
    move.w  #0x8F02, (%a5)          /* auto-increment = 2 bytes */

    lea     genesistan_arcade_workram_words+PC080SN_DESC_LIST_OFFSET, %a0
    lea     rastan_maincpu, %a1
    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     genesistan_pc080sn_attr_lut, %a3

    move.l  48(%sp), %d5            /* dest_ptr accumulator */
    move.l  52(%sp), %d7            /* strip_index */
    move.l  56(%sp), %d1            /* dest_row (raw) */
    move.l  60(%sp), %d2            /* dest_col */
    andi.w  #0x0003, %d7
    andi.w  #0x001F, %d1
    andi.w  #0x003F, %d2

    moveq   #15, %d6                /* 16 descriptors */

.Lpc080sn_fg_desc_loop:
    move.l  (%a0)+, %d3             /* desc_addr */
    btst    #0, %d3
    bne     .Lpc080sn_fg_invalid
    cmpi.l  #0x0005FFFC, %d3
    bhi     .Lpc080sn_fg_invalid

    movea.l %a1, %a4
    adda.l  %d3, %a4
    move.w  (%a4), %d4              /* attr_word */
    move.w  2(%a4), %d3             /* table_base (u16) */
    cmpi.w  #0x7FE0, %d3
    bhi     .Lpc080sn_fg_invalid

    movea.l %a1, %a4
    move.w  %d3, %d0
    andi.l  #0x0000FFFF, %d0
    adda.l  %d0, %a4
    move.w  %d7, %d0
    lsl.w   #3, %d0
    adda.w  %d0, %a4

    move.w  %d4, %d0
    andi.w  #0x0003, %d0
    move.w  %d4, %d3
    lsr.w   #8, %d3
    lsr.w   #6, %d3
    andi.w  #0x0001, %d3
    lsl.w   #2, %d3
    or.w    %d3, %d0
    move.w  %d4, %d3
    lsr.w   #8, %d3
    lsr.w   #7, %d3
    andi.w  #0x0001, %d3
    lsl.w   #3, %d3
    or.w    %d3, %d0
    move.w  %d4, %d3
    lsr.w   #8, %d3
    lsr.w   #5, %d3
    andi.w  #0x0001, %d3
    lsl.w   #4, %d3
    or.w    %d3, %d0
    add.w   %d0, %d0
    move.w  0(%a3,%d0.w), %d0
    move.w  %d0, -(%sp)             /* attr partial */

    moveq   #3, %d4
.Lpc080sn_fg_col_loop:
    move.w  (%a4), %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    (%sp), %d3

    move.w  %d1, %d0
    cmpi.w  #4, %d0
    blo     .Lpc080sn_fg_skip_write

    subi.w  #4, %d0
    lsl.w   #7, %d0
    add.w   %d2, %d0
    add.w   %d2, %d0
    addi.w  #0xE000, %d0

    move.w  %d4, -(%sp)
    move.w  %d0, %d4
    andi.w  #0x3FFF, %d0
    lsl.l   #8, %d0
    lsl.l   #8, %d0
    lsr.w   #8, %d4
    lsr.w   #6, %d4
    andi.w  #0x0003, %d4
    or.w    %d4, %d0
    ori.l   #0x40000003, %d0
    move.l  %d0, (%a5)
    move.w  %d3, (%a6)
    move.w  (%sp)+, %d4

.Lpc080sn_fg_skip_write:
    adda.w  #2, %a4
    addq.w  #1, %d2
    cmpi.w  #64, %d2
    blo     .Lpc080sn_fg_no_wrap
    moveq   #0, %d2
    addq.w  #1, %d1
    andi.w  #0x001F, %d1

.Lpc080sn_fg_no_wrap:
    addi.l  #4, %d5
    dbra    %d4, .Lpc080sn_fg_col_loop

    addq.l  #2, %sp
    bra     .Lpc080sn_fg_desc_done

.Lpc080sn_fg_invalid:
    addi.l  #0x10, %d5
    addi.w  #4, %d2
    cmpi.w  #64, %d2
    blo     .Lpc080sn_fg_desc_done
    subi.w  #64, %d2
    addq.w  #1, %d1
    andi.w  #0x001F, %d1

.Lpc080sn_fg_desc_done:
    dbra    %d6, .Lpc080sn_fg_desc_loop

    move.l  %d5, %d0
    movem.l (%sp)+,%d2-%d7/%a2-%a6
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
    move.l %a0, genesistan_arcade_last_a0   /* capture sprite ptr before restore (Build 109) */
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

genesistan_sprite_commit_asm:
    rts

genesistan_asm_tilemap_commit_bg:
    move.l 4(%sp), %d0
    rts

genesistan_asm_tilemap_commit_fg:
    move.l 4(%sp), %d0
    rts

#endif
