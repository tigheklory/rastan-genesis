    .section .text.boot,"ax"
    .global _start
    .extern _vblank_service
    .extern vdp_boot_setup
    .extern vdp_set_vram_write_addr
    .extern load_scene_tiles
    .extern palette_dirty
    .extern tiles_dirty
    .extern bg_row_dirty
    .extern fg_row_dirty
    .extern staged_dest_ptr_bg
    .extern staged_dest_ptr_fg
    .extern staged_scroll_x_bg
    .extern staged_scroll_x_fg
    .extern staged_scroll_y_bg
    .extern staged_scroll_y_fg
    .extern staged_bg_buffer
    .extern staged_fg_buffer
    .extern staged_palette_words
    .extern staged_tile_words
    .extern _crash_stub_bus_error
    .extern _crash_stub_address_error
    .extern _crash_stub_illegal
    .extern _crash_stub_zero_divide
    .extern _crash_stub_chk
    .extern _crash_stub_trapv
    .extern _crash_stub_privilege
    .extern _crash_stub_trace
    .extern _crash_stub_line_a
    .extern _crash_stub_line_f
    .extern _crash_stub_trap_00
    .extern _crash_stub_trap_01
    .extern _crash_stub_trap_02
    .extern _crash_stub_trap_03
    .extern _crash_stub_trap_04
    .extern _crash_stub_trap_05
    .extern _crash_stub_trap_06
    .extern _crash_stub_trap_07
    .extern _crash_stub_trap_08
    .extern _crash_stub_trap_09
    .extern _crash_stub_trap_10
    .extern _crash_stub_trap_11
    .extern _crash_stub_trap_12
    .extern _crash_stub_trap_13
    .extern _crash_stub_trap_14
    .extern _crash_stub_trap_15
    .extern _crash_stub_other

    .equ HW_VERSION,  0x00A10001
    .equ TMSS_REG,    0x00A14000
    .equ VDP_DATA,    0x00C00000
    .equ VRAM_PLANE_A_BASE, 0x0000E000
    .equ ARCADE_FIX_DEST_BG, 0x00FF10A0
    .equ ARCADE_FIX_DEST_FG, 0x00FF10A4

    .org 0x000000
    .long 0x00FF0000
    .long _start
    .long _crash_stub_bus_error         /*  2 */
    .long _crash_stub_address_error     /*  3 */
    .long _crash_stub_illegal           /*  4 */
    .long _crash_stub_zero_divide       /*  5 */
    .long _crash_stub_chk               /*  6 */
    .long _crash_stub_trapv             /*  7 */
    .long _crash_stub_privilege         /*  8 */
    .long _crash_stub_trace             /*  9 */
    .long _crash_stub_line_a            /* 10 */
    .long _crash_stub_line_f            /* 11 */
    .long _crash_stub_other             /* 12 */
    .long _crash_stub_other             /* 13 */
    .long _crash_stub_other             /* 14 */
    .long _crash_stub_other             /* 15 */
    .long _crash_stub_other             /* 16 */
    .long _crash_stub_other             /* 17 */
    .long _crash_stub_other             /* 18 */
    .long _crash_stub_other             /* 19 */
    .long _crash_stub_other             /* 20 */
    .long _crash_stub_other             /* 21 */
    .long _crash_stub_other             /* 22 */
    .long _crash_stub_other             /* 23 */
    .long _crash_stub_other             /* 24 */
    .long _crash_stub_other             /* 25 */
    .long _crash_stub_other             /* 26 */
    .long _crash_stub_other             /* 27 */
    .long _crash_stub_other             /* 28 */
    .long _crash_stub_other             /* 29 */
    .long _vblank_service
    .long _crash_stub_other             /* 31 */
    .long _crash_stub_trap_00           /* 32 */
    .long _crash_stub_trap_01           /* 33 */
    .long _crash_stub_trap_02           /* 34 */
    .long _crash_stub_trap_03           /* 35 */
    .long _crash_stub_trap_04           /* 36 */
    .long _crash_stub_trap_05           /* 37 */
    .long _crash_stub_trap_06           /* 38 */
    .long _crash_stub_trap_07           /* 39 */
    .long _crash_stub_trap_08           /* 40 */
    .long _crash_stub_trap_09           /* 41 */
    .long _crash_stub_trap_10           /* 42 */
    .long _crash_stub_trap_11           /* 43 */
    .long _crash_stub_trap_12           /* 44 */
    .long _crash_stub_trap_13           /* 45 */
    .long _crash_stub_trap_14           /* 46 */
    .long _crash_stub_trap_15           /* 47 */
    .long _crash_stub_other             /* 48 */
    .long _crash_stub_other             /* 49 */
    .long _crash_stub_other             /* 50 */
    .long _crash_stub_other             /* 51 */
    .long _crash_stub_other             /* 52 */
    .long _crash_stub_other             /* 53 */
    .long _crash_stub_other             /* 54 */
    .long _crash_stub_other             /* 55 */
    .long _crash_stub_other             /* 56 */
    .long _crash_stub_other             /* 57 */
    .long _crash_stub_other             /* 58 */
    .long _crash_stub_other             /* 59 */
    .long _crash_stub_other             /* 60 */
    .long _crash_stub_other             /* 61 */
    .long _crash_stub_other             /* 62 */
    .long _crash_stub_other             /* 63 */

    .org 0x000100
    .ascii "SEGA MEGA DRIVE "
    .ascii "(C)CDX 2026.APR"
    .ascii "RASTAN DIRECT VIDEO TEST                      "
    .ascii "RASTAN DIRECT VIDEO TEST                      "
    .ascii "RDVD00000000  "
    .word  0x0000
    .ascii "J               "
    .long  0x00000000
    .long  0x0003FFFF
    .long  0x00FF0000
    .long  0x00FFFFFF
    .ascii "            "
    .ascii "                                        "
    .ascii "JUE             "

    .org 0x000200
_boot_guard_legacy_rte:
    rte

_start:
    move.w  #0x2700, %sr
    lea     0x00FF0000, %sp

    move.b  HW_VERSION, %d0
    andi.b  #0x0F, %d0
    beq.s   .Ltmss_done
    move.l  #0x53454741, TMSS_REG
.Ltmss_done:

    jsr     _bootstrap

_bootstrap:
    jsr     vdp_boot_setup
    bsr     _bootstrap_clear_staging
    moveq   #0, %d0
    jsr     load_scene_tiles
    lea     0x00FF0000, %a5
    move.w  #0x2000, %sr
    jmp     (0x00003A200).l

_bootstrap_clear_staging:
    move.l  #0x00C00000, staged_dest_ptr_bg
    move.l  #0x00C08000, staged_dest_ptr_fg

    move.l  #0x00C00000, ARCADE_FIX_DEST_BG
    move.l  #0x00C08000, ARCADE_FIX_DEST_FG

    clr.b   palette_dirty
    clr.b   tiles_dirty
    clr.l   bg_row_dirty
    clr.l   fg_row_dirty

    lea     staged_palette_words, %a0
    move.w  #(64 - 1), %d7
.Lboot_pal_clear:
    clr.w   (%a0)+
    dbra    %d7, .Lboot_pal_clear

    lea     staged_tile_words, %a0
    move.w  #(48 - 1), %d7
.Lboot_tile_clear:
    clr.w   (%a0)+
    dbra    %d7, .Lboot_tile_clear

    lea     staged_bg_buffer, %a0
    move.w  #(2048 - 1), %d7
.Lboot_bg_clear:
    clr.w   (%a0)+
    dbra    %d7, .Lboot_bg_clear

    lea     staged_fg_buffer, %a0
    move.w  #(2048 - 1), %d7
.Lboot_fg_clear:
    clr.w   (%a0)+
    dbra    %d7, .Lboot_fg_clear

    move.l  #VRAM_PLANE_A_BASE, %d0
    jsr     vdp_set_vram_write_addr
    move.w  #(2048 - 1), %d7
.Lboot_plane_a_clear:
    move.w  #0x0000, VDP_DATA
    dbra    %d7, .Lboot_plane_a_clear

    clr.w   staged_scroll_x_bg
    clr.w   staged_scroll_x_fg
    clr.w   staged_scroll_y_bg
    clr.w   staged_scroll_y_fg
    rts

.Lhang:
    bra.s   .Lhang
