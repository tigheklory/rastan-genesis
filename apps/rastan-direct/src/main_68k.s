    .section .text,"ax"
    .global main_68k
    .global _VINT_handler
    .global sprite_dma_addr_high_bits_fix
    .global genesistan_hook_tilemap_plane_a
    .global genesistan_shadow_input_390001
    .global genesistan_shadow_input_390003
    .global genesistan_shadow_input_390005
    .global genesistan_shadow_input_390007
    .global genesistan_shadow_dip1
    .global genesistan_shadow_dip2
    .global rastan_direct_arcade_tick_entry

    .equ VDP_DATA,              0x00C00000
    .equ VDP_CTRL,              0x00C00004
    .equ IO_PAD1_DATA,          0x00A10003
    .equ IO_PAD2_DATA,          0x00A10005
    .equ IO_PAD1_CTRL,          0x00A10009
    .equ IO_PAD2_CTRL,          0x00A1000B

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
    .equ ARCADE_PC080SN_DESC_BG_LIST_OFFSET, 0x1000
    .equ ARCADE_PC080SN_DEST_BG_OFFSET,      0x10A0
    .equ ARCADE_PC080SN_STRIP_INDEX_OFFSET,  0x10CA
    .equ ARCADE_PC080SN_CWINDOW_BASE_BG,     0x00C00000
    .equ ARCADE_PC080SN_CWINDOW_BYTES,       0x00004000
    .equ ARCADE_MAINCPU_ROM_BASE,            0x00000200
    .equ rastan_direct_arcade_tick_entry, 0x0003A208

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

    bsr     vdp_commit_tiles_if_dirty
    bsr     vdp_commit_bg_strips_if_dirty

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

genesistan_hook_tilemap_plane_a:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00FF0000, %a5

    move.w  ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5), %d7
    move.l  ARCADE_PC080SN_DEST_BG_OFFSET(%a5), %d5

    move.l  %d5, %d0
    andi.l  #0x00FFFFFF, %d0
    cmpi.l  #ARCADE_PC080SN_CWINDOW_BASE_BG, %d0
    blo     .Lbg_hook_dest_invalid
    cmpi.l  #(ARCADE_PC080SN_CWINDOW_BASE_BG + ARCADE_PC080SN_CWINDOW_BYTES), %d0
    bhs     .Lbg_hook_dest_invalid

    move.l  %d0, %d4
    subi.l  #ARCADE_PC080SN_CWINDOW_BASE_BG, %d4
    move.l  %d4, %d0
    andi.l  #0x00000003, %d0
    bne     .Lbg_hook_dest_invalid

    lsr.l   #2, %d4
    move.w  %d4, %d1
    andi.w  #0x003F, %d1
    andi.w  #0x001F, %d1
    move.w  %d4, %d2
    lsr.w   #6, %d2
    andi.w  #0x003F, %d2

    lea     ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5), %a0
    movea.l #ARCADE_MAINCPU_ROM_BASE, %a1
    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     genesistan_pc080sn_attr_lut, %a3
    lea     staged_bg_buffer, %a6

    moveq   #15, %d6
.Lbg_hook_desc_loop:
    move.l  (%a0)+, %d3
    btst    #0, %d3
    bne     .Lbg_hook_invalid_desc
    cmpi.l  #0x0005FFFC, %d3
    bhi     .Lbg_hook_invalid_desc

    movea.l %a1, %a4
    adda.l  %d3, %a4
    move.w  (%a4), %d4
    move.w  2(%a4), %d3
    cmpi.w  #0x7FE0, %d3
    bhi     .Lbg_hook_invalid_desc

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
    move.w  %d0, -(%sp)

    moveq   #3, %d4
.Lbg_hook_row_loop:
    move.w  (%a4), %d3
    andi.w  #0x3FFF, %d3
    add.w   %d3, %d3
    move.w  0(%a2,%d3.w), %d3
    or.w    (%sp), %d3

    move.w  %d1, %d0
    lsl.w   #7, %d0
    add.w   %d2, %d0
    add.w   %d2, %d0
    move.w  %d3, 0(%a6,%d0.w)
    move.l  bg_row_dirty, %d0
    bset    %d1, %d0
    move.l  %d0, bg_row_dirty

    adda.w  #8, %a4
    addq.w  #1, %d1
    andi.w  #0x001F, %d1
    dbra    %d4, .Lbg_hook_row_loop

    addq.l  #2, %sp
    bra.s   .Lbg_hook_desc_done

.Lbg_hook_invalid_desc:
    addq.w  #4, %d1
    andi.w  #0x001F, %d1

.Lbg_hook_desc_done:
    addi.l  #0x00000400, %d5
    dbra    %d6, .Lbg_hook_desc_loop

    move.l  %d5, ARCADE_PC080SN_DEST_BG_OFFSET(%a5)
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

.Lbg_hook_dest_invalid:
    addi.l  #0x00004000, %d5
    move.l  %d5, ARCADE_PC080SN_DEST_BG_OFFSET(%a5)
    movem.l (%sp)+, %d0-%d7/%a0-%a6
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

rastan_direct_update_inputs:
    move.b  #0x40, IO_PAD1_CTRL
    move.b  #0x40, IO_PAD2_CTRL

    move.b  #0x00, IO_PAD1_DATA
    nop
    move.b  IO_PAD1_DATA, %d1
    move.b  %d1, %d6
    move.b  #0x40, IO_PAD1_DATA
    nop
    move.b  IO_PAD1_DATA, %d0

    move.b  %d0, %d2
    ori.b   #0xC0, %d2
    btst    #4, %d1
    bne.s   .Lp1_a_done
    bclr    #6, %d2
.Lp1_a_done:
    move.b  %d2, genesistan_shadow_input_390001

    move.b  #0x00, IO_PAD2_DATA
    nop
    move.b  IO_PAD2_DATA, %d1
    move.b  %d1, %d7
    move.b  #0x40, IO_PAD2_DATA
    nop
    move.b  IO_PAD2_DATA, %d0

    move.b  %d0, %d3
    ori.b   #0xC0, %d3
    btst    #4, %d1
    bne.s   .Lp2_a_done
    bclr    #6, %d3
.Lp2_a_done:
    move.b  %d3, genesistan_shadow_input_390003

    moveq   #-1, %d4
    btst    #6, %d2
    bne.s   .Lp1_coin_done
    bclr    #4, %d4
    bclr    #6, %d4
.Lp1_coin_done:
    btst    #6, %d3
    bne.s   .Lp2_coin_done
    bclr    #5, %d4
    bclr    #6, %d4
.Lp2_coin_done:
    move.b  %d4, genesistan_shadow_input_390005

    moveq   #-1, %d5
    btst    #5, %d6
    bne.s   .Lp1_start_sys_done
    bclr    #3, %d5
.Lp1_start_sys_done:
    btst    #5, %d7
    bne.s   .Lp2_start_sys_done
    bclr    #4, %d5
.Lp2_start_sys_done:

    moveq   #0, %d0
    btst    #6, %d2
    bne.s   .Lp1_a_state_ready
    moveq   #1, %d0
.Lp1_a_state_ready:
    tst.b   prev_coin_p1_a_pressed
    bne.s   .Lcoin_prev_pressed
    tst.b   %d0
    beq.s   .Lcoin_prev_store
    bclr    #5, %d5
.Lcoin_prev_store:
    move.b  %d0, prev_coin_p1_a_pressed
    bra.s   .Lsys_store_done
.Lcoin_prev_pressed:
    move.b  %d0, prev_coin_p1_a_pressed
.Lsys_store_done:
    move.b  %d5, genesistan_shadow_input_390007

    rts

arcade_tick_logic:
    bsr     rastan_direct_update_inputs
    pea     .Ltick_return
    move.w  %sr, -(%sp)
    jmp     rastan_direct_arcade_tick_entry
.Ltick_return:
    rts

init_staging_state:
    lea     0x00FF0000, %a5
    clr.w   frame_counter
    clr.w   tick_counter

    move.l  #0x00C00000, staged_dest_ptr_bg
    move.l  #0x00C08000, staged_dest_ptr_fg

    move.l  #0x00C00000, ARCADE_FIX_DEST_BG
    move.l  #0x00C08000, ARCADE_FIX_DEST_FG

    move.b  #1, palette_dirty
    move.b  #1, tiles_dirty
    move.l  #0xFFFFFFFF, bg_row_dirty

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

    move.l  #VRAM_PLANE_A_BASE, %d0
    bsr     vdp_set_vram_write_addr
    move.w  #(2048 - 1), %d7
.Lplane_a_clear:
    move.w  #0x0000, VDP_DATA
    dbra    %d7, .Lplane_a_clear

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

    .align 2
genesistan_pc080sn_tile_vram_lut:
    .incbin "../../build/pc080sn_tile_vram_lut.bin"

    .align 2
genesistan_pc080sn_attr_lut:
    .incbin "../../build/pc080sn_attr_lut.bin"

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
    .align 2
bg_row_dirty:
    .long 0
genesistan_shadow_input_390001:
    .byte 0
genesistan_shadow_input_390003:
    .byte 0
genesistan_shadow_input_390005:
    .byte 0
genesistan_shadow_input_390007:
    .byte 0
prev_coin_p1_a_pressed:
    .byte 0
genesistan_shadow_dip1:
    .byte 0
genesistan_shadow_dip2:
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
