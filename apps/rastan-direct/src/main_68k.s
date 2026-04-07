    .section .text,"ax"
    .global main_68k
    .global _VINT_handler
    .global sprite_dma_addr_high_bits_fix

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

main_68k:
    move.w  #0x2700, %sr

    bsr     vdp_boot_setup
    bsr     init_staging_state

    move.w  #0x2000, %sr

.Lmain_loop:
    move.w  frame_counter, %d0
.Lwait_vblank:
    cmp.w   frame_counter, %d0
    beq.s   .Lwait_vblank

    bsr     arcade_tick_logic
    bra.s   .Lmain_loop

_VINT_handler:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    move.w  VDP_CTRL, %d0

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg

    bsr     vdp_commit_bg

    tst.b   palette_dirty
    beq.s   .Lskip_palette
    bsr     vdp_commit_palette
    clr.b   palette_dirty
.Lskip_palette:

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_ON, %d1
    bsr     vdp_set_reg

    bsr     vdp_commit_scroll

    addq.w  #1, frame_counter

    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rte

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

vdp_commit_bg:
    tst.b   bg_dirty
    beq.s   .Lbg_done

    bsr     vdp_commit_tiles_if_dirty

    move.l  #VRAM_PLANE_B_BASE, %d0
    bsr     vdp_set_vram_write_addr

    lea     staged_bg_buffer, %a0
    move.w  #(2048 - 1), %d7
.Lbg_copy:
    move.w  (%a0)+, VDP_DATA
    dbra    %d7, .Lbg_copy
    clr.b   bg_dirty
.Lbg_done:
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

arcade_tick_logic:
    addq.w  #1, staged_scroll_x_bg
    addq.w  #2, staged_scroll_x_fg

    move.w  staged_scroll_x_bg, %d0
    andi.w  #0x01FF, %d0
    move.w  %d0, staged_scroll_x_bg

    move.w  staged_scroll_x_fg, %d0
    andi.w  #0x01FF, %d0
    move.w  %d0, staged_scroll_x_fg

    addq.w  #1, tick_counter
    move.w  tick_counter, %d0
    andi.w  #0x003F, %d0
    move.w  %d0, staged_scroll_y_bg

    move.w  tick_counter, %d0
    lsr.w   #1, %d0
    andi.w  #0x001F, %d0
    move.w  %d0, staged_scroll_y_fg

    rts

init_staging_state:
    clr.w   frame_counter
    clr.w   tick_counter

    move.l  #0x00C00000, staged_dest_ptr_bg
    move.l  #0x00C08000, staged_dest_ptr_fg

    move.l  #0x00C00000, ARCADE_FIX_DEST_BG
    move.l  #0x00C08000, ARCADE_FIX_DEST_FG

    move.b  #1, palette_dirty
    move.b  #1, tiles_dirty
    move.b  #1, bg_dirty

    lea     palette_init_words, %a0
    lea     staged_palette_words, %a1
    move.w  #(64 - 1), %d7
.Lpal_init:
    move.w  (%a0)+, (%a1)+
    dbra    %d7, .Lpal_init

    lea     tile_init_words, %a0
    lea     staged_tile_words, %a1
    move.w  #(48 - 1), %d7
.Ltile_init:
    move.w  (%a0)+, (%a1)+
    dbra    %d7, .Ltile_init

    lea     staged_bg_buffer, %a0
    moveq   #31, %d6
.Lbg_row:
    moveq   #63, %d5
.Lbg_col:
    move.w  %d6, %d0
    eor.w   %d5, %d0
    andi.w  #0x0001, %d0
    bne.s   .Lbg_tile_two
    move.w  #0x0001, (%a0)+
    bra.s   .Lbg_next
.Lbg_tile_two:
    move.w  #0x0002, (%a0)+
.Lbg_next:
    dbra    %d5, .Lbg_col
    dbra    %d6, .Lbg_row

    lea     staged_fg_buffer, %a0
    move.w  #(2048 - 1), %d7
.Lfg_clear:
    clr.w   (%a0)+
    dbra    %d7, .Lfg_clear

    clr.w   staged_scroll_x_bg
    clr.w   staged_scroll_x_fg
    clr.w   staged_scroll_y_bg
    clr.w   staged_scroll_y_fg

    rts

    .section .rodata,"a"

palette_init_words:
    .word 0x0000,0x000E,0x00E0,0x0E00,0x00EE,0x0E0E,0x0EE0,0x020C
    .word 0x0022,0x0046,0x006A,0x008C,0x00A2,0x00C6,0x00EA,0x002E
    .word 0x0200,0x0400,0x0600,0x0800,0x0A00,0x0C00,0x0E00,0x0C20
    .word 0x0202,0x0404,0x0606,0x0808,0x0A0A,0x0C0C,0x0E0C,0x0C0E
    .word 0x0002,0x0004,0x0006,0x0008,0x000A,0x000C,0x000E,0x020A
    .word 0x0220,0x0440,0x0660,0x0880,0x0AA0,0x0CC0,0x0EE0,0x0AC2
    .word 0x0020,0x0040,0x0060,0x0080,0x00A0,0x00C0,0x00E0,0x0A20
    .word 0x0204,0x0406,0x0608,0x080A,0x0A0C,0x0C0A,0x0E08,0x0C06

tile_init_words:
    .rept 16
    .word 0x1111
    .endr
    .rept 16
    .word 0x2222
    .endr
    .rept 8
    .word 0x3030
    .word 0x0303
    .endr

    .section .bss
    .align 2

frame_counter:
    .word 0
tick_counter:
    .word 0

palette_dirty:
    .byte 0
tiles_dirty:
    .byte 0
bg_dirty:
    .byte 0

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
