    .section .text,"ax"

    .global vdp_boot_setup
    .global vdp_set_reg
    .global vdp_set_vram_write_addr
    .global sprite_dma_addr_high_bits_fix
    .global vdp_commit_tiles_if_dirty
    .global vdp_commit_bg_strips_if_dirty
    .global vdp_commit_fg_strips_if_dirty
    .extern vdp_commit_sprites
    .global vdp_commit_palette
    .global vdp_commit_scroll
    .global _vblank_service

    .global palette_dirty
    .global tiles_dirty
    .global bg_row_dirty
    .global fg_row_dirty
    .global staged_dest_ptr_bg
    .global staged_dest_ptr_fg
    .global staged_scroll_x_bg
    .global staged_scroll_x_fg
    .global staged_scroll_y_bg
    .global staged_scroll_y_fg
    .global staged_bg_buffer
    .global staged_fg_buffer
    .global staged_palette_words
    .global staged_tile_words

    .equ VDP_DATA,              0x00C00000
    .equ VDP_CTRL,              0x00C00004

    .equ VDP_REG_MODE1,         0
    .equ VDP_REG_MODE2,         1
    .equ VDP_REG_PLANE_A,       2
    .equ VDP_REG_WINDOW,        3
    .equ VDP_REG_PLANE_B,       4
    .equ VDP_REG_SAT,           5
    .equ VDP_REG_BG_COLOR,      7
    .equ VDP_REG_HINT,          10
    .equ VDP_REG_MODE3,         11
    .equ VDP_REG_MODE4,         12
    .equ VDP_REG_HSCROLL,       13
    .equ VDP_REG_AUTOINC,       15
    .equ VDP_REG_PLANESIZE,     16
    .equ VDP_REG_WINDOW_X,      17
    .equ VDP_REG_WINDOW_Y,      18

    .equ VRAM_PLANE_B_BASE,     0x0000C000
    .equ VRAM_PLANE_A_BASE,     0x0000E000
    .equ VRAM_HSCROLL_BASE,     0x0000FC00
    .equ VRAM_TILE_BASE,        0x00000020

    .equ ARCADE_FIX_DEST_BG,    0x00FF10A0
    .equ ARCADE_FIX_DEST_FG,    0x00FF10A4

    .equ VDP_MODE2_DISPLAY_OFF, 0x34
    .equ VDP_MODE2_DISPLAY_ON,  0x74

    .include "src/crash_handler.s"
    .section .text,"ax"
vdp_boot_setup:
    moveq   #VDP_REG_MODE1, %d0
    moveq   #0x04, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_PLANE_A, %d0
    moveq   #0x38, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_WINDOW, %d0
    moveq   #0x3C, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_PLANE_B, %d0
    moveq   #0x06, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_SAT, %d0
    moveq   #0x7C, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_BG_COLOR, %d0
    moveq   #0x00, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_HINT, %d0
    move.w  #0x00FF, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_MODE3, %d0
    moveq   #0x00, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_MODE4, %d0
    move.w  #0x0081, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_HSCROLL, %d0
    moveq   #0x3F, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_AUTOINC, %d0
    moveq   #0x02, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_PLANESIZE, %d0
    moveq   #0x01, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_WINDOW_X, %d0
    moveq   #0x00, %d1
    bsr     vdp_set_reg

    moveq   #VDP_REG_WINDOW_Y, %d0
    moveq   #0x00, %d1
    bsr     vdp_set_reg

    rts

vdp_set_reg:
    move.w  %d0, %d2
    lsl.w   #8, %d2
    or.w    %d1, %d2
    ori.w   #0x8000, %d2
    move.w  %d2, VDP_CTRL
    rts

vdp_set_vram_write_addr:
    move.l  %d0, %d1
    andi.l  #0x00003FFF, %d1
    swap    %d1

    move.l  %d0, %d2
    lsr.l   #8, %d2
    lsr.l   #6, %d2
    andi.l  #0x00000003, %d2

    ori.l   #0x40000000, %d1
    or.l    %d2, %d1
    move.l  %d1, VDP_CTRL
    rts

sprite_dma_addr_high_bits_fix:
    move.l  %d0, %d2
    lsr.l   #8, %d2
    lsr.l   #6, %d2
    andi.w  #0x0003, %d2
    rts


_vblank_service:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     rastan_direct_update_inputs

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg

    bsr     vdp_commit_tiles_if_dirty
    bsr     vdp_commit_bg_strips_if_dirty
    bsr     vdp_commit_fg_strips_if_dirty
    bsr     vdp_commit_sprites

    tst.b   palette_dirty
    beq.s   .Lvs_skip_palette
    bsr     vdp_commit_palette
    clr.b   palette_dirty
.Lvs_skip_palette:

    bsr     vdp_commit_scroll

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_ON, %d1
    bsr     vdp_set_reg

    movem.l (%sp)+, %d0-%d7/%a0-%a6
    jmp     (0x00003A208).l

vdp_commit_tiles_if_dirty:
    tst.b   tiles_dirty
    beq.s   .Ltiles_done

    move.l  #VRAM_TILE_BASE, %d0
    bsr     vdp_set_vram_write_addr

    lea     staged_tile_words, %a0
    move.w  #(48 - 1), %d7
.Ltile_copy:
    move.w  (%a0)+, VDP_DATA
    dbra    %d7, .Ltile_copy

    clr.b   tiles_dirty
.Ltiles_done:
    rts

vdp_commit_bg_strips_if_dirty:
    move.l  bg_row_dirty, %d6
    beq.s   .Lbg_done

    moveq   #0, %d5
.Lbg_row_scan:
    btst    %d5, %d6
    beq.s   .Lbg_next_row

    moveq   #0, %d4
    move.w  %d5, %d4
    lsl.l   #7, %d4

    move.l  #VRAM_PLANE_B_BASE, %d0
    add.l   %d4, %d0
    bsr     vdp_set_vram_write_addr

    lea     staged_bg_buffer, %a0
    adda.l  %d4, %a0
    move.w  #(64 - 1), %d7
.Lbg_row_copy:
    move.w  (%a0)+, VDP_DATA
    dbra    %d7, .Lbg_row_copy

    move.l  %d6, %d0
    bclr    %d5, %d0
    move.l  %d0, %d6
    move.l  %d6, bg_row_dirty
    beq.s   .Lbg_done

.Lbg_next_row:
    addq.w  #1, %d5
    cmpi.w  #32, %d5
    blo.s   .Lbg_row_scan
.Lbg_done:
    rts

vdp_commit_fg_strips_if_dirty:
    move.l  fg_row_dirty, %d6
    beq.s   .Lfg_done

    moveq   #0, %d5
.Lfg_row_scan:
    btst    %d5, %d6
    beq.s   .Lfg_next_row

    moveq   #0, %d4
    move.w  %d5, %d4
    lsl.l   #7, %d4

    move.l  #VRAM_PLANE_A_BASE, %d0
    add.l   %d4, %d0
    bsr     vdp_set_vram_write_addr

    lea     staged_fg_buffer, %a0
    adda.l  %d4, %a0
    move.w  #(64 - 1), %d7
.Lfg_row_copy:
    move.w  (%a0)+, VDP_DATA
    dbra    %d7, .Lfg_row_copy

    move.l  %d6, %d0
    bclr    %d5, %d0
    move.l  %d0, %d6
    move.l  %d6, fg_row_dirty
    beq.s   .Lfg_done

.Lfg_next_row:
    addq.w  #1, %d5
    cmpi.w  #32, %d5
    blo.s   .Lfg_row_scan
.Lfg_done:
    rts

vdp_commit_palette:
    move.l  #0xC0000000, VDP_CTRL

    lea     staged_palette_words, %a0
    move.w  #(64 - 1), %d7
.Lpal_copy:
    move.w  (%a0)+, VDP_DATA
    dbra    %d7, .Lpal_copy
    rts

vdp_commit_scroll:
    move.l  #VRAM_HSCROLL_BASE, %d0
    bsr     vdp_set_vram_write_addr

    move.w  staged_scroll_x_fg, VDP_DATA
    move.w  staged_scroll_x_bg, VDP_DATA

    move.l  #0x40000010, VDP_CTRL
    move.w  staged_scroll_y_fg, VDP_DATA
    move.w  staged_scroll_y_bg, VDP_DATA
    rts

    .section .bss
    .align 2

palette_dirty:
    .byte 0
tiles_dirty:
    .byte 0
    .align 2
bg_row_dirty:
    .long 0
fg_row_dirty:
    .long 0

    .align 2
staged_dest_ptr_bg:
    .long 0
staged_dest_ptr_fg:
    .long 0

staged_scroll_x_bg:
    .word 0
staged_scroll_x_fg:
    .word 0
staged_scroll_y_bg:
    .word 0
staged_scroll_y_fg:
    .word 0

    .align 2
staged_bg_buffer:
    .space (2048 * 2)
staged_fg_buffer:
    .space (2048 * 2)
staged_palette_words:
    .space (64 * 2)
staged_tile_words:
    .space (48 * 2)
