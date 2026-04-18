    .section .text.boot,"ax"

    .global _crash_stub_bus_error
    .global _crash_stub_address_error
    .global _crash_stub_illegal
    .global _crash_stub_zero_divide
    .global _crash_stub_chk
    .global _crash_stub_trapv
    .global _crash_stub_privilege
    .global _crash_stub_trace
    .global _crash_stub_line_a
    .global _crash_stub_line_f
    .global _crash_stub_trap_00
    .global _crash_stub_trap_01
    .global _crash_stub_trap_02
    .global _crash_stub_trap_03
    .global _crash_stub_trap_04
    .global _crash_stub_trap_05
    .global _crash_stub_trap_06
    .global _crash_stub_trap_07
    .global _crash_stub_trap_08
    .global _crash_stub_trap_09
    .global _crash_stub_trap_10
    .global _crash_stub_trap_11
    .global _crash_stub_trap_12
    .global _crash_stub_trap_13
    .global _crash_stub_trap_14
    .global _crash_stub_trap_15
    .global _crash_stub_other
    .global _crash_common
    .global genesistan_crash_handler_end

    .equ CRASH_RECORD_BASE,       0x00FF6800

    .equ CRASH_ACTIVE_FLAG,       0x00FF6800
    .equ CRASH_EXCEPTION_TYPE,    0x00FF6802
    .equ CRASH_STACKED_SR,        0x00FF6804
    .equ CRASH_STACKED_PC,        0x00FF6806
    .equ CRASH_PC_AT_HANDLER,     0x00FF680A
    .equ CRASH_SP_AT_ENTRY,       0x00FF680E
    .equ CRASH_USP,               0x00FF6812
    .equ CRASH_D0,                0x00FF6816
    .equ CRASH_D1,                0x00FF681A
    .equ CRASH_D2,                0x00FF681E
    .equ CRASH_D3,                0x00FF6822
    .equ CRASH_D4,                0x00FF6826
    .equ CRASH_D5,                0x00FF682A
    .equ CRASH_D6,                0x00FF682E
    .equ CRASH_D7,                0x00FF6832
    .equ CRASH_A0,                0x00FF6836
    .equ CRASH_A1,                0x00FF683A
    .equ CRASH_A2,                0x00FF683E
    .equ CRASH_A3,                0x00FF6842
    .equ CRASH_A4,                0x00FF6846
    .equ CRASH_A5,                0x00FF684A
    .equ CRASH_A6,                0x00FF684E
    .equ CRASH_FRAME_COUNTER,     0x00FF6852

    .equ CRASH_FAULT_ADDRESS,     0x00FF6854
    .equ CRASH_ACCESS_TYPE,       0x00FF6858

    .equ CRASH_ARCADE_DEST_BG,    0x00FF685A
    .equ CRASH_ARCADE_DEST_FG,    0x00FF685E
    .equ CRASH_BG_ROW_DIRTY,      0x00FF6862
    .equ CRASH_FG_ROW_DIRTY,      0x00FF6866
    .equ CRASH_PALETTE_DIRTY,     0x00FF686A
    .equ CRASH_TILES_DIRTY,       0x00FF686B

    .equ CRASH_RECORD_SIZE,       0x6C

_crash_stub_bus_error:
    moveq   #2, %d0
    bra.w   _crash_common

_crash_stub_address_error:
    moveq   #3, %d0
    bra.w   _crash_common

_crash_stub_illegal:
    moveq   #4, %d0
    bra.w   _crash_common

_crash_stub_zero_divide:
    moveq   #5, %d0
    bra.w   _crash_common

_crash_stub_chk:
    moveq   #6, %d0
    bra.w   _crash_common

_crash_stub_trapv:
    moveq   #7, %d0
    bra.w   _crash_common

_crash_stub_privilege:
    moveq   #8, %d0
    bra.w   _crash_common

_crash_stub_trace:
    moveq   #9, %d0
    bra.w   _crash_common

_crash_stub_line_a:
    moveq   #10, %d0
    bra.w   _crash_common

_crash_stub_line_f:
    moveq   #11, %d0
    bra.w   _crash_common

_crash_stub_trap_00:
    moveq   #32, %d0
    bra.w   _crash_common

_crash_stub_trap_01:
    moveq   #33, %d0
    bra.w   _crash_common

_crash_stub_trap_02:
    moveq   #34, %d0
    bra.w   _crash_common

_crash_stub_trap_03:
    moveq   #35, %d0
    bra.w   _crash_common

_crash_stub_trap_04:
    moveq   #36, %d0
    bra.w   _crash_common

_crash_stub_trap_05:
    moveq   #37, %d0
    bra.w   _crash_common

_crash_stub_trap_06:
    moveq   #38, %d0
    bra.w   _crash_common

_crash_stub_trap_07:
    moveq   #39, %d0
    bra.w   _crash_common

_crash_stub_trap_08:
    moveq   #40, %d0
    bra.w   _crash_common

_crash_stub_trap_09:
    moveq   #41, %d0
    bra.w   _crash_common

_crash_stub_trap_10:
    moveq   #42, %d0
    bra.w   _crash_common

_crash_stub_trap_11:
    moveq   #43, %d0
    bra.w   _crash_common

_crash_stub_trap_12:
    moveq   #44, %d0
    bra.w   _crash_common

_crash_stub_trap_13:
    moveq   #45, %d0
    bra.w   _crash_common

_crash_stub_trap_14:
    moveq   #46, %d0
    bra.w   _crash_common

_crash_stub_trap_15:
    moveq   #47, %d0
    bra.w   _crash_common

_crash_stub_other:
    moveq   #63, %d0
    bra.w   _crash_common

_crash_common:
    move.w  #0x2700, %sr
    move.l  %sp, %a0
    tst.b   CRASH_ACTIVE_FLAG
    bne.w   .Lminimal_halt
    move.b  #1, CRASH_ACTIVE_FLAG
    move.b  %d0, CRASH_EXCEPTION_TYPE

    clr.l   CRASH_FAULT_ADDRESS
    clr.w   CRASH_ACCESS_TYPE

    cmpi.b  #3, %d0
    bhi.s   .Lstandard_frame
    move.w  0(%a0), %d5
    move.l  2(%a0), %d4
    move.w  6(%a0), %d3
    move.w  8(%a0), %d1
    move.l  10(%a0), %d2
    move.l  %d4, CRASH_FAULT_ADDRESS
    move.w  %d5, CRASH_ACCESS_TYPE
    move.w  %d1, CRASH_STACKED_SR
    move.l  %d2, CRASH_STACKED_PC
    bra.s   .Lframe_done

.Lstandard_frame:
    move.w  0(%a0), %d1
    move.l  2(%a0), %d2
    move.w  %d1, CRASH_STACKED_SR
    move.l  %d2, CRASH_STACKED_PC

.Lframe_done:
    lea     .Lhandler_pc_marker(%pc), %a1
.Lhandler_pc_marker:
    move.l  %a1, CRASH_PC_AT_HANDLER

    move.l  %d0, CRASH_D0
    move.l  %d1, CRASH_D1
    move.l  %d2, CRASH_D2
    move.l  %d3, CRASH_D3
    move.l  %d4, CRASH_D4
    move.l  %d5, CRASH_D5
    move.l  %d6, CRASH_D6
    move.l  %d7, CRASH_D7
    move.l  %a0, CRASH_A0
    move.l  %a1, CRASH_A1
    move.l  %a2, CRASH_A2
    move.l  %a3, CRASH_A3
    move.l  %a4, CRASH_A4
    move.l  %a5, CRASH_A5
    move.l  %a6, CRASH_A6

    move.l  %a0, CRASH_SP_AT_ENTRY
    move.l  %usp, %a1
    move.l  %a1, CRASH_USP

    move.w  frame_counter, %d6
    move.w  %d6, CRASH_FRAME_COUNTER

    move.l  ARCADE_FIX_DEST_BG, %d6
    move.l  %d6, CRASH_ARCADE_DEST_BG

    move.l  ARCADE_FIX_DEST_FG, %d6
    move.l  %d6, CRASH_ARCADE_DEST_FG

    move.l  bg_row_dirty, %d6
    move.l  %d6, CRASH_BG_ROW_DIRTY

    move.l  fg_row_dirty, %d6
    move.l  %d6, CRASH_FG_ROW_DIRTY

    move.b  palette_dirty, %d6
    move.b  %d6, CRASH_PALETTE_DIRTY

    move.b  tiles_dirty, %d6
    move.b  %d6, CRASH_TILES_DIRTY

    lea     0x00FFFF00, %sp

    bsr     crash_vdp_reinit
    bsr     crash_init_cram
    bsr     crash_upload_font
    bsr     crash_render_screen

.Lcrash_halt:
    stop    #0x2700
    bra.s   .Lcrash_halt

.Lminimal_halt:
    stop    #0x2700
    bra.s   .Lminimal_halt

crash_vdp_reinit:
    move.w  #0x8004, VDP_CTRL
    move.w  #0x8174, VDP_CTRL
    move.w  #0x8238, VDP_CTRL
    move.w  #0x833C, VDP_CTRL
    move.w  #0x8406, VDP_CTRL
    move.w  #0x857C, VDP_CTRL
    move.w  #0x8700, VDP_CTRL
    move.w  #0x8A00, VDP_CTRL
    move.w  #0x8B00, VDP_CTRL
    move.w  #0x8C81, VDP_CTRL
    move.w  #0x8D3F, VDP_CTRL
    move.w  #0x8F02, VDP_CTRL
    move.w  #0x9001, VDP_CTRL
    rts

crash_init_cram:
    move.l  #0xC0000000, VDP_CTRL
    move.w  #0x0000, VDP_DATA
    move.w  #0x0EEE, VDP_DATA
    rts

crash_upload_font:
    move.l  #0x40000002, VDP_CTRL
    lea     crash_font_1bpp(%pc), %a1
    move.w  #95, %d7
.Lfont_char_loop:
    move.w  #7, %d6
.Lfont_row_loop:
    moveq   #0, %d0
    move.b  (%a1)+, %d0

    moveq   #0, %d1
    moveq   #7, %d2
.Lexpand_bit:
    lsl.l   #4, %d1
    btst    %d2, %d0
    beq.s   .Lbit_zero
    ori.b   #1, %d1
.Lbit_zero:
    dbra    %d2, .Lexpand_bit
    move.l  %d1, VDP_DATA

    dbra    %d6, .Lfont_row_loop
    dbra    %d7, .Lfont_char_loop
    rts

crash_render_screen:
    bsr     crash_clear_plane_a

    moveq   #0, %d0
    moveq   #0, %d1
    lea     crash_line_0(%pc), %a1
    bsr     crash_puts_at

    moveq   #1, %d0
    moveq   #0, %d1
    lea     crash_line_1_prefix(%pc), %a1
    bsr     crash_puts_at

    moveq   #0, %d0
    move.b  CRASH_EXCEPTION_TYPE, %d0
    bsr     crash_get_exception_name
    moveq   #1, %d0
    moveq   #11, %d1
    bsr     crash_puts_at

    moveq   #1, %d0
    moveq   #28, %d1
    lea     crash_line_1_vector(%pc), %a1
    bsr     crash_puts_at

    moveq   #1, %d0
    moveq   #36, %d1
    moveq   #0, %d2
    move.b  CRASH_EXCEPTION_TYPE, %d2
    bsr     crash_put_hex8_at

    moveq   #2, %d0
    moveq   #0, %d1
    lea     crash_line_2_faultpc(%pc), %a1
    bsr     crash_puts_at

    moveq   #2, %d0
    moveq   #11, %d1
    move.l  CRASH_STACKED_PC, %d2
    bsr     crash_put_hex32_at

    moveq   #2, %d0
    moveq   #26, %d1
    lea     crash_line_2_sr(%pc), %a1
    bsr     crash_puts_at

    moveq   #2, %d0
    moveq   #30, %d1
    moveq   #0, %d2
    move.w  CRASH_STACKED_SR, %d2
    bsr     crash_put_hex16_at

    moveq   #3, %d0
    moveq   #0, %d1
    lea     crash_line_3_faultaddr(%pc), %a1
    bsr     crash_puts_at

    moveq   #0, %d6
    move.b  CRASH_EXCEPTION_TYPE, %d6
    cmpi.b  #2, %d6
    blo.s   .Lfault_addr_blank
    cmpi.b  #3, %d6
    bhi.s   .Lfault_addr_blank

    moveq   #3, %d0
    moveq   #11, %d1
    move.l  CRASH_FAULT_ADDRESS, %d2
    bsr     crash_put_hex32_at
    bra.s   .Lfault_addr_done

.Lfault_addr_blank:
    moveq   #3, %d0
    moveq   #11, %d1
    lea     crash_eight_spaces(%pc), %a1
    bsr     crash_puts_at

.Lfault_addr_done:
    moveq   #4, %d0
    moveq   #0, %d1
    lea     crash_separator(%pc), %a1
    bsr     crash_puts_at

    moveq   #5, %d0
    moveq   #0, %d1
    lea     crash_d0_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #5, %d0
    moveq   #3, %d1
    move.l  CRASH_D0, %d2
    bsr     crash_put_hex32_at

    moveq   #5, %d0
    moveq   #12, %d1
    lea     crash_d1_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #5, %d0
    moveq   #15, %d1
    move.l  CRASH_D1, %d2
    bsr     crash_put_hex32_at

    moveq   #5, %d0
    moveq   #24, %d1
    lea     crash_d2_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #5, %d0
    moveq   #27, %d1
    move.l  CRASH_D2, %d2
    bsr     crash_put_hex32_at

    moveq   #6, %d0
    moveq   #0, %d1
    lea     crash_d3_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #6, %d0
    moveq   #3, %d1
    move.l  CRASH_D3, %d2
    bsr     crash_put_hex32_at

    moveq   #6, %d0
    moveq   #12, %d1
    lea     crash_d4_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #6, %d0
    moveq   #15, %d1
    move.l  CRASH_D4, %d2
    bsr     crash_put_hex32_at

    moveq   #6, %d0
    moveq   #24, %d1
    lea     crash_d5_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #6, %d0
    moveq   #27, %d1
    move.l  CRASH_D5, %d2
    bsr     crash_put_hex32_at

    moveq   #7, %d0
    moveq   #0, %d1
    lea     crash_d6_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #7, %d0
    moveq   #3, %d1
    move.l  CRASH_D6, %d2
    bsr     crash_put_hex32_at

    moveq   #7, %d0
    moveq   #12, %d1
    lea     crash_d7_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #7, %d0
    moveq   #15, %d1
    move.l  CRASH_D7, %d2
    bsr     crash_put_hex32_at

    moveq   #8, %d0
    moveq   #0, %d1
    lea     crash_a0_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #8, %d0
    moveq   #3, %d1
    move.l  CRASH_A0, %d2
    bsr     crash_put_hex32_at

    moveq   #8, %d0
    moveq   #12, %d1
    lea     crash_a1_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #8, %d0
    moveq   #15, %d1
    move.l  CRASH_A1, %d2
    bsr     crash_put_hex32_at

    moveq   #8, %d0
    moveq   #24, %d1
    lea     crash_a2_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #8, %d0
    moveq   #27, %d1
    move.l  CRASH_A2, %d2
    bsr     crash_put_hex32_at

    moveq   #9, %d0
    moveq   #0, %d1
    lea     crash_a3_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #9, %d0
    moveq   #3, %d1
    move.l  CRASH_A3, %d2
    bsr     crash_put_hex32_at

    moveq   #9, %d0
    moveq   #12, %d1
    lea     crash_a4_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #9, %d0
    moveq   #15, %d1
    move.l  CRASH_A4, %d2
    bsr     crash_put_hex32_at

    moveq   #9, %d0
    moveq   #24, %d1
    lea     crash_a5_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #9, %d0
    moveq   #27, %d1
    move.l  CRASH_A5, %d2
    bsr     crash_put_hex32_at

    moveq   #10, %d0
    moveq   #0, %d1
    lea     crash_a6_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #10, %d0
    moveq   #3, %d1
    move.l  CRASH_A6, %d2
    bsr     crash_put_hex32_at

    moveq   #10, %d0
    moveq   #12, %d1
    lea     crash_sp_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #10, %d0
    moveq   #15, %d1
    move.l  CRASH_SP_AT_ENTRY, %d2
    bsr     crash_put_hex32_at

    moveq   #10, %d0
    moveq   #24, %d1
    lea     crash_usp_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #10, %d0
    moveq   #28, %d1
    move.l  CRASH_USP, %d2
    bsr     crash_put_hex32_at

    moveq   #11, %d0
    moveq   #0, %d1
    lea     crash_separator(%pc), %a1
    bsr     crash_puts_at

    moveq   #12, %d0
    moveq   #0, %d1
    lea     crash_dest_bg_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #12, %d0
    moveq   #8, %d1
    move.l  CRASH_ARCADE_DEST_BG, %d2
    bsr     crash_put_hex32_at

    moveq   #12, %d0
    moveq   #20, %d1
    lea     crash_dest_fg_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #12, %d0
    moveq   #28, %d1
    move.l  CRASH_ARCADE_DEST_FG, %d2
    bsr     crash_put_hex32_at

    moveq   #13, %d0
    moveq   #0, %d1
    lea     crash_bg_dirty_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #13, %d0
    moveq   #9, %d1
    move.l  CRASH_BG_ROW_DIRTY, %d2
    bsr     crash_put_hex32_at

    moveq   #13, %d0
    moveq   #20, %d1
    lea     crash_fg_dirty_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #13, %d0
    moveq   #29, %d1
    move.l  CRASH_FG_ROW_DIRTY, %d2
    bsr     crash_put_hex32_at

    moveq   #14, %d0
    moveq   #0, %d1
    lea     crash_pal_dirty_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #14, %d0
    moveq   #6, %d1
    moveq   #0, %d2
    move.b  CRASH_PALETTE_DIRTY, %d2
    bsr     crash_put_hex8_at

    moveq   #14, %d0
    moveq   #12, %d1
    lea     crash_tile_dirty_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #14, %d0
    moveq   #19, %d1
    moveq   #0, %d2
    move.b  CRASH_TILES_DIRTY, %d2
    bsr     crash_put_hex8_at

    moveq   #14, %d0
    moveq   #23, %d1
    lea     crash_frame_label(%pc), %a1
    bsr     crash_puts_at
    moveq   #14, %d0
    moveq   #29, %d1
    moveq   #0, %d2
    move.w  CRASH_FRAME_COUNTER, %d2
    bsr     crash_put_hex16_at

    moveq   #15, %d0
    moveq   #0, %d1
    lea     crash_separator(%pc), %a1
    bsr     crash_puts_at

    moveq   #16, %d0
    moveq   #0, %d1
    lea     crash_stack_dump_label(%pc), %a1
    bsr     crash_puts_at

    move.l  CRASH_SP_AT_ENTRY, %a2
    moveq   #0, %d7
.Lstack_row_loop:
    moveq   #17, %d0
    add.w   %d7, %d0
    moveq   #0, %d1
    bsr     crash_set_cursor

    moveq   #'[', %d2
    bsr     crash_put_char_ascii

    moveq   #0, %d6
.Lstack_col_loop:
    move.l  (%a2)+, %d2
    bsr     crash_put_hex32_inline

    cmpi.w  #3, %d6
    beq.s   .Lstack_no_space
    moveq   #' ', %d2
    bsr     crash_put_char_ascii
.Lstack_no_space:
    addq.w  #1, %d6
    cmpi.w  #4, %d6
    blo.s   .Lstack_col_loop

    moveq   #']', %d2
    bsr     crash_put_char_ascii

    addq.w  #1, %d7
    cmpi.w  #4, %d7
    blo.s   .Lstack_row_loop

    moveq   #21, %d0
    moveq   #0, %d1
    lea     crash_separator(%pc), %a1
    bsr     crash_puts_at

    moveq   #27, %d0
    moveq   #0, %d1
    lea     crash_footer(%pc), %a1
    bsr     crash_puts_at

    move.w  #0x8174, VDP_CTRL
    rts

crash_clear_plane_a:
    move.l  #0x60000003, VDP_CTRL
    move.w  #0x8400, %d0
    move.w  #1791, %d7
.Lclear_loop:
    move.w  %d0, VDP_DATA
    dbra    %d7, .Lclear_loop
    rts

crash_get_exception_name:
    andi.w  #0x00FF, %d0
    cmpi.w  #63, %d0
    bhi.s   .Lexception_default
    lea     crash_vector_name_table(%pc), %a1
    lsl.w   #2, %d0
    move.l  0(%a1,%d0.w), %a1
    rts

.Lexception_default:
    lea     crash_name_other(%pc), %a1
    rts

crash_set_cursor:
    move.w  %d0, %d2
    mulu.w  #128, %d2

    move.w  %d1, %d3
    add.w   %d3, %d3
    add.w   %d3, %d2

    move.l  #VRAM_PLANE_A_BASE, %d0
    add.l   %d2, %d0
    move.l  %d0, %d1
    andi.l  #0x00003FFF, %d1
    swap    %d1

    move.l  %d0, %d3
    lsr.l   #8, %d3
    lsr.l   #6, %d3
    andi.l  #0x00000003, %d3

    ori.l   #0x40000000, %d1
    or.l    %d3, %d1
    move.l  %d1, VDP_CTRL
    rts

crash_puts_at:
    bsr     crash_set_cursor
.Lputs_loop:
    moveq   #0, %d2
    move.b  (%a1)+, %d2
    beq.s   .Lputs_done
    bsr     crash_put_char_ascii
    bra.s   .Lputs_loop
.Lputs_done:
    rts

crash_put_char_ascii_at:
    bsr     crash_set_cursor
    bsr     crash_put_char_ascii
    rts

crash_put_hex32_at:
    bsr     crash_set_cursor
    bsr     crash_put_hex32_inline
    rts

crash_put_hex16_at:
    bsr     crash_set_cursor
    bsr     crash_put_hex16_inline
    rts

crash_put_hex8_at:
    bsr     crash_set_cursor
    bsr     crash_put_hex8_inline
    rts

crash_put_hex32_inline:
    move.l  %d2, %d4
    moveq   #7, %d5
.Lhex32_loop:
    bsr     crash_extract_top_nibble
    bsr     crash_put_hex_nibble
    lsl.l   #4, %d4
    dbra    %d5, .Lhex32_loop
    rts

crash_put_hex16_inline:
    moveq   #0, %d4
    move.w  %d2, %d4
    swap    %d4
    moveq   #3, %d5
.Lhex16_loop:
    bsr     crash_extract_top_nibble
    bsr     crash_put_hex_nibble
    lsl.l   #4, %d4
    dbra    %d5, .Lhex16_loop
    rts

crash_put_hex8_inline:
    moveq   #0, %d4
    move.b  %d2, %d4
    lsl.w   #8, %d4
    swap    %d4
    moveq   #1, %d5
.Lhex8_loop:
    bsr     crash_extract_top_nibble
    bsr     crash_put_hex_nibble
    lsl.l   #4, %d4
    dbra    %d5, .Lhex8_loop
    rts

crash_extract_top_nibble:
    move.l  %d4, %d3
    swap    %d3
    lsr.w   #8, %d3
    lsr.b   #4, %d3
    move.b  %d3, %d2
    rts

crash_put_hex_nibble:
    andi.b  #0x0F, %d2
    cmpi.b  #9, %d2
    ble.s   .Lhex_digit
    addi.b  #7, %d2
.Lhex_digit:
    addi.b  #'0', %d2
    bsr     crash_put_char_ascii
    rts

crash_put_char_ascii:
    cmpi.b  #0x20, %d2
    blo.s   .Lchar_space
    cmpi.b  #0x7F, %d2
    bhi.s   .Lchar_space
    subi.b  #0x20, %d2
    bra.s   .Lchar_tile

.Lchar_space:
    moveq   #0, %d2

.Lchar_tile:
    andi.w  #0x00FF, %d2
    ori.w   #0x8400, %d2
    move.w  %d2, VDP_DATA
    rts

    .section .text.boot,"ax"
    .align 2

crash_line_0:
    .asciz "==== RASTAN CRASH =========================="
crash_line_1_prefix:
    .asciz "EXCEPTION: "
crash_line_1_vector:
    .asciz "VECTOR: "
crash_line_2_faultpc:
    .asciz "FAULT PC:  "
crash_line_2_sr:
    .asciz "SR: "
crash_line_3_faultaddr:
    .asciz "FAULT ADDR:"
crash_separator:
    .asciz "=========================================="
crash_eight_spaces:
    .asciz "        "

crash_d0_label: .asciz "D0:"
crash_d1_label: .asciz "D1:"
crash_d2_label: .asciz "D2:"
crash_d3_label: .asciz "D3:"
crash_d4_label: .asciz "D4:"
crash_d5_label: .asciz "D5:"
crash_d6_label: .asciz "D6:"
crash_d7_label: .asciz "D7:"
crash_a0_label: .asciz "A0:"
crash_a1_label: .asciz "A1:"
crash_a2_label: .asciz "A2:"
crash_a3_label: .asciz "A3:"
crash_a4_label: .asciz "A4:"
crash_a5_label: .asciz "A5:"
crash_a6_label: .asciz "A6:"
crash_sp_label: .asciz "SP:"
crash_usp_label: .asciz "USP:"

crash_dest_bg_label: .asciz "DEST_BG:"
crash_dest_fg_label: .asciz "DEST_FG:"
crash_bg_dirty_label: .asciz "BG_DIRTY:"
crash_fg_dirty_label: .asciz "FG_DIRTY:"
crash_pal_dirty_label: .asciz "PAL_D:"
crash_tile_dirty_label: .asciz "TILE_D:"
crash_frame_label: .asciz "FRAME:"
crash_stack_dump_label: .asciz "STACK DUMP:"
crash_footer: .asciz "HALTED -- BUILD 0038"

crash_name_other:           .asciz "OTHER"
crash_name_bus_error:       .asciz "BUS ERROR"
crash_name_address_error:   .asciz "ADDRESS ERROR"
crash_name_illegal:         .asciz "ILLEGAL INSTR"
crash_name_zero_divide:     .asciz "ZERO DIVIDE"
crash_name_chk:             .asciz "CHK"
crash_name_trapv:           .asciz "TRAPV"
crash_name_privilege:       .asciz "PRIVILEGE"
crash_name_trace:           .asciz "TRACE"
crash_name_line_a:          .asciz "LINE 1010"
crash_name_line_f:          .asciz "LINE 1111"
crash_name_trap_00:         .asciz "TRAP #0"
crash_name_trap_01:         .asciz "TRAP #1"
crash_name_trap_02:         .asciz "TRAP #2"
crash_name_trap_03:         .asciz "TRAP #3"
crash_name_trap_04:         .asciz "TRAP #4"
crash_name_trap_05:         .asciz "TRAP #5"
crash_name_trap_06:         .asciz "TRAP #6"
crash_name_trap_07:         .asciz "TRAP #7"
crash_name_trap_08:         .asciz "TRAP #8"
crash_name_trap_09:         .asciz "TRAP #9"
crash_name_trap_10:         .asciz "TRAP #10"
crash_name_trap_11:         .asciz "TRAP #11"
crash_name_trap_12:         .asciz "TRAP #12"
crash_name_trap_13:         .asciz "TRAP #13"
crash_name_trap_14:         .asciz "TRAP #14"
crash_name_trap_15:         .asciz "TRAP #15"

    .align 2
crash_vector_name_table:
    .long crash_name_other
    .long crash_name_other
    .long crash_name_bus_error
    .long crash_name_address_error
    .long crash_name_illegal
    .long crash_name_zero_divide
    .long crash_name_chk
    .long crash_name_trapv
    .long crash_name_privilege
    .long crash_name_trace
    .long crash_name_line_a
    .long crash_name_line_f
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_trap_00
    .long crash_name_trap_01
    .long crash_name_trap_02
    .long crash_name_trap_03
    .long crash_name_trap_04
    .long crash_name_trap_05
    .long crash_name_trap_06
    .long crash_name_trap_07
    .long crash_name_trap_08
    .long crash_name_trap_09
    .long crash_name_trap_10
    .long crash_name_trap_11
    .long crash_name_trap_12
    .long crash_name_trap_13
    .long crash_name_trap_14
    .long crash_name_trap_15
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other
    .long crash_name_other

    .align 2
crash_font_1bpp:
    .byte 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    .byte 0x00, 0x18, 0x18, 0x18, 0x18, 0x00, 0x18, 0x00
    .byte 0x00, 0x66, 0x66, 0x66, 0x00, 0x00, 0x00, 0x00
    .byte 0x00, 0x66, 0xFF, 0x66, 0x66, 0xFF, 0x66, 0x00
    .byte 0x18, 0x3E, 0x60, 0x3C, 0x06, 0x7C, 0x18, 0x00
    .byte 0x00, 0x66, 0x6C, 0x18, 0x30, 0x66, 0x46, 0x00
    .byte 0x1C, 0x36, 0x1C, 0x38, 0x6F, 0x66, 0x3B, 0x00
    .byte 0x00, 0x18, 0x18, 0x18, 0x00, 0x00, 0x00, 0x00
    .byte 0x00, 0x0E, 0x1C, 0x18, 0x18, 0x1C, 0x0E, 0x00
    .byte 0x00, 0x70, 0x38, 0x18, 0x18, 0x38, 0x70, 0x00
    .byte 0x00, 0x66, 0x3C, 0xFF, 0x3C, 0x66, 0x00, 0x00
    .byte 0x00, 0x18, 0x18, 0x7E, 0x18, 0x18, 0x00, 0x00
    .byte 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x30
    .byte 0x00, 0x00, 0x00, 0x7E, 0x00, 0x00, 0x00, 0x00
    .byte 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x00
    .byte 0x00, 0x06, 0x0C, 0x18, 0x30, 0x60, 0x40, 0x00
    .byte 0x00, 0x3C, 0x66, 0x6E, 0x76, 0x66, 0x3C, 0x00
    .byte 0x00, 0x18, 0x38, 0x18, 0x18, 0x18, 0x7E, 0x00
    .byte 0x00, 0x3C, 0x66, 0x0C, 0x18, 0x30, 0x7E, 0x00
    .byte 0x00, 0x7E, 0x0C, 0x18, 0x0C, 0x66, 0x3C, 0x00
    .byte 0x00, 0x0C, 0x1C, 0x3C, 0x6C, 0x7E, 0x0C, 0x00
    .byte 0x00, 0x7E, 0x60, 0x7C, 0x06, 0x66, 0x3C, 0x00
    .byte 0x00, 0x3C, 0x60, 0x7C, 0x66, 0x66, 0x3C, 0x00
    .byte 0x00, 0x7E, 0x06, 0x0C, 0x18, 0x30, 0x30, 0x00
    .byte 0x00, 0x3C, 0x66, 0x3C, 0x66, 0x66, 0x3C, 0x00
    .byte 0x00, 0x3C, 0x66, 0x3E, 0x06, 0x0C, 0x38, 0x00
    .byte 0x00, 0x00, 0x18, 0x18, 0x00, 0x18, 0x18, 0x00
    .byte 0x00, 0x00, 0x18, 0x18, 0x00, 0x18, 0x18, 0x30
    .byte 0x06, 0x0C, 0x18, 0x30, 0x18, 0x0C, 0x06, 0x00
    .byte 0x00, 0x00, 0x7E, 0x00, 0x00, 0x7E, 0x00, 0x00
    .byte 0x60, 0x30, 0x18, 0x0C, 0x18, 0x30, 0x60, 0x00
    .byte 0x00, 0x3C, 0x66, 0x0C, 0x18, 0x00, 0x18, 0x00
    .byte 0x00, 0x3C, 0x66, 0x6E, 0x6E, 0x60, 0x3E, 0x00
    .byte 0x00, 0x18, 0x3C, 0x66, 0x66, 0x7E, 0x66, 0x00
    .byte 0x00, 0x7C, 0x66, 0x7C, 0x66, 0x66, 0x7C, 0x00
    .byte 0x00, 0x3C, 0x66, 0x60, 0x60, 0x66, 0x3C, 0x00
    .byte 0x00, 0x78, 0x6C, 0x66, 0x66, 0x6C, 0x78, 0x00
    .byte 0x00, 0x7E, 0x60, 0x7C, 0x60, 0x60, 0x7E, 0x00
    .byte 0x00, 0x7E, 0x60, 0x7C, 0x60, 0x60, 0x60, 0x00
    .byte 0x00, 0x3E, 0x60, 0x60, 0x6E, 0x66, 0x3E, 0x00
    .byte 0x00, 0x66, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00
    .byte 0x00, 0x7E, 0x18, 0x18, 0x18, 0x18, 0x7E, 0x00
    .byte 0x00, 0x06, 0x06, 0x06, 0x06, 0x66, 0x3C, 0x00
    .byte 0x00, 0x66, 0x6C, 0x78, 0x78, 0x6C, 0x66, 0x00
    .byte 0x00, 0x60, 0x60, 0x60, 0x60, 0x60, 0x7E, 0x00
    .byte 0x00, 0x63, 0x77, 0x7F, 0x6B, 0x63, 0x63, 0x00
    .byte 0x00, 0x66, 0x76, 0x7E, 0x7E, 0x6E, 0x66, 0x00
    .byte 0x00, 0x3C, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x00
    .byte 0x00, 0x7C, 0x66, 0x66, 0x7C, 0x60, 0x60, 0x00
    .byte 0x00, 0x3C, 0x66, 0x66, 0x66, 0x6C, 0x36, 0x00
    .byte 0x00, 0x7C, 0x66, 0x66, 0x7C, 0x6C, 0x66, 0x00
    .byte 0x00, 0x3C, 0x60, 0x3C, 0x06, 0x06, 0x3C, 0x00
    .byte 0x00, 0x7E, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00
    .byte 0x00, 0x66, 0x66, 0x66, 0x66, 0x66, 0x7E, 0x00
    .byte 0x00, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x18, 0x00
    .byte 0x00, 0x63, 0x63, 0x6B, 0x7F, 0x77, 0x63, 0x00
    .byte 0x00, 0x66, 0x66, 0x3C, 0x3C, 0x66, 0x66, 0x00
    .byte 0x00, 0x66, 0x66, 0x3C, 0x18, 0x18, 0x18, 0x00
    .byte 0x00, 0x7E, 0x0C, 0x18, 0x30, 0x60, 0x7E, 0x00
    .byte 0x00, 0x1E, 0x18, 0x18, 0x18, 0x18, 0x1E, 0x00
    .byte 0x00, 0x40, 0x60, 0x30, 0x18, 0x0C, 0x06, 0x00
    .byte 0x00, 0x78, 0x18, 0x18, 0x18, 0x18, 0x78, 0x00
    .byte 0x00, 0x08, 0x1C, 0x36, 0x63, 0x00, 0x00, 0x00
    .byte 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00
    .byte 0x00, 0x18, 0x3C, 0x7E, 0x7E, 0x3C, 0x18, 0x00
    .byte 0x00, 0x00, 0x3C, 0x06, 0x3E, 0x66, 0x3E, 0x00
    .byte 0x00, 0x60, 0x60, 0x7C, 0x66, 0x66, 0x7C, 0x00
    .byte 0x00, 0x00, 0x3C, 0x60, 0x60, 0x60, 0x3C, 0x00
    .byte 0x00, 0x06, 0x06, 0x3E, 0x66, 0x66, 0x3E, 0x00
    .byte 0x00, 0x00, 0x3C, 0x66, 0x7E, 0x60, 0x3C, 0x00
    .byte 0x00, 0x0E, 0x18, 0x3E, 0x18, 0x18, 0x18, 0x00
    .byte 0x00, 0x00, 0x3E, 0x66, 0x66, 0x3E, 0x06, 0x7C
    .byte 0x00, 0x60, 0x60, 0x7C, 0x66, 0x66, 0x66, 0x00
    .byte 0x00, 0x18, 0x00, 0x38, 0x18, 0x18, 0x3C, 0x00
    .byte 0x00, 0x06, 0x00, 0x06, 0x06, 0x06, 0x06, 0x3C
    .byte 0x00, 0x60, 0x60, 0x6C, 0x78, 0x6C, 0x66, 0x00
    .byte 0x00, 0x38, 0x18, 0x18, 0x18, 0x18, 0x3C, 0x00
    .byte 0x00, 0x00, 0x66, 0x7F, 0x7F, 0x6B, 0x63, 0x00
    .byte 0x00, 0x00, 0x7C, 0x66, 0x66, 0x66, 0x66, 0x00
    .byte 0x00, 0x00, 0x3C, 0x66, 0x66, 0x66, 0x3C, 0x00
    .byte 0x00, 0x00, 0x7C, 0x66, 0x66, 0x7C, 0x60, 0x60
    .byte 0x00, 0x00, 0x3E, 0x66, 0x66, 0x3E, 0x06, 0x06
    .byte 0x00, 0x00, 0x7C, 0x66, 0x60, 0x60, 0x60, 0x00
    .byte 0x00, 0x00, 0x3E, 0x60, 0x3C, 0x06, 0x7C, 0x00
    .byte 0x00, 0x18, 0x7E, 0x18, 0x18, 0x18, 0x0E, 0x00
    .byte 0x00, 0x00, 0x66, 0x66, 0x66, 0x66, 0x3E, 0x00
    .byte 0x00, 0x00, 0x66, 0x66, 0x66, 0x3C, 0x18, 0x00
    .byte 0x00, 0x00, 0x63, 0x6B, 0x7F, 0x3E, 0x36, 0x00
    .byte 0x00, 0x00, 0x66, 0x3C, 0x18, 0x3C, 0x66, 0x00
    .byte 0x00, 0x00, 0x66, 0x66, 0x66, 0x3E, 0x0C, 0x78
    .byte 0x00, 0x00, 0x7E, 0x0C, 0x18, 0x30, 0x7E, 0x00
    .byte 0x00, 0x18, 0x3C, 0x7E, 0x7E, 0x18, 0x3C, 0x00
    .byte 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18
    .byte 0x00, 0x7E, 0x78, 0x7C, 0x6E, 0x66, 0x06, 0x00
    .byte 0x08, 0x18, 0x38, 0x78, 0x38, 0x18, 0x08, 0x00
    .byte 0x10, 0x18, 0x1C, 0x1E, 0x1C, 0x18, 0x10, 0x00

genesistan_crash_handler_end:
