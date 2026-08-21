    .section .text,"ax"

    .global load_scene_tiles
    .extern fg_cache_reset

    .global genesistan_pc080sn_tile_vram_lut
    .global genesistan_pc080sn_attr_lut
    .global genesistan_pc080sn_tile_rom
    .global genesistan_scene_preload_title
    .global genesistan_scene_preload_title_end
    .global genesistan_scene_preload_gameplay
    .global genesistan_scene_preload_gameplay_end
    .global genesistan_scene_preload_gameplay_cave
    .global genesistan_scene_preload_gameplay_cave_end
    .global genesistan_scene_preload_stage1_cave_s4
    .global genesistan_scene_preload_stage1_cave_s4_end
    .global genesistan_scene_preload_stage1_cave_s5
    .global genesistan_scene_preload_stage1_cave_s5_end
    .global genesistan_scene_preload_stage1_cave_s6
    .global genesistan_scene_preload_stage1_cave_s6_end
    .global genesistan_scene_preload_stage1_seg1
    .global genesistan_scene_preload_stage1_seg1_end
    .global genesistan_scene_preload_stage1_seg2
    .global genesistan_scene_preload_stage1_seg2_end
    .global genesistan_scene_preload_endround
    .global genesistan_scene_preload_endround_end
    .global genesistan_scene_a0_ranges

    .global genesistan_current_scene_id
    .global genesistan_current_pc080sn_tileset_id
    .global genesistan_scene_a0_lo
    .global genesistan_scene_a0_hi

    .extern vdp_set_reg
    .extern vdp_set_vram_write_addr
    .extern fg_native_gameplay_owner

    .equ VDP_DATA,              0x00C00000
    .equ VDP_REG_MODE2,         1
    .equ VDP_MODE2_DISPLAY_OFF, 0x34
    .equ VDP_MODE2_DISPLAY_ON,  0x74
load_scene_tiles:
    movem.l %d1-%d7/%a0-%a4, -(%sp)

    move.w  %d0, %d6
    andi.w  #0x00FF, %d6

    lea     genesistan_scene_preload_title, %a0
    cmpi.w  #1, %d6
    bne.s   .Lload_scene_check_endround
    lea     genesistan_scene_preload_gameplay, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_endround:
    cmpi.w  #2, %d6
    bne.s   .Lload_scene_check_gameplay_cave
    lea     genesistan_scene_preload_endround, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_gameplay_cave:
    cmpi.w  #3, %d6
    bne.s   .Lload_scene_check_stage1_cave_s4
    lea     genesistan_scene_preload_gameplay_cave, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_stage1_cave_s4:
    /* Build 0299: Stage-1 first-cave per-segment residencies (ids 4/5/6), runtime-selected by
     * arcade segment a5@0x13E.  Each loads the outdoor BG + that segment's cave FG. */
    cmpi.w  #4, %d6
    bne.s   .Lload_scene_check_stage1_cave_s5
    lea     genesistan_scene_preload_stage1_cave_s4, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_stage1_cave_s5:
    cmpi.w  #5, %d6
    bne.s   .Lload_scene_check_stage1_cave_s6
    lea     genesistan_scene_preload_stage1_cave_s5, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_stage1_cave_s6:
    cmpi.w  #6, %d6
    bne.s   .Lload_scene_check_stage1_seg1
    lea     genesistan_scene_preload_stage1_cave_s6, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_stage1_seg1:
    /* Build 0300: outdoor per-segment residencies (ids 7=seg1, 8=seg2). */
    cmpi.w  #7, %d6
    bne.s   .Lload_scene_check_stage1_seg2
    lea     genesistan_scene_preload_stage1_seg1, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_check_stage1_seg2:
    cmpi.w  #8, %d6
    bne.s   .Lload_scene_force_title
    lea     genesistan_scene_preload_stage1_seg2, %a0
    bra.s   .Lload_scene_manifest_ready
.Lload_scene_force_title:
    moveq   #0, %d6
.Lload_scene_manifest_ready:
    move.w  %sr, -(%sp)
    ori.w   #0x0700, %sr

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg

.Lload_scene_pair_loop:
    move.w  (%a0)+, %d2
    cmpi.w  #0xFFFF, %d2
    beq.s   .Lload_scene_pairs_done
    move.w  (%a0)+, %d3

    lea     genesistan_pc080sn_tile_rom, %a2
    moveq   #0, %d4
    move.w  %d2, %d4
    lsl.l   #5, %d4
    adda.l  %d4, %a2

    moveq   #0, %d0
    move.w  %d3, %d0
    lsl.l   #5, %d0
    bsr     vdp_set_vram_write_addr

    moveq   #15, %d7
.Lload_scene_tile_words:
    move.w  (%a2)+, VDP_DATA
    dbra    %d7, .Lload_scene_tile_words
    bra.s   .Lload_scene_pair_loop

.Lload_scene_pairs_done:
    move.b  %d6, genesistan_current_pc080sn_tileset_id
    move.w  %d6, %d5
    /* ids 3 (attr cave) and 4/5/6 (Stage-1 first-cave segments) are logically the gameplay
     * scene: they share the gameplay a0 source range and fg_native ownership. */
    cmpi.w  #3, %d5
    blo.s   .Lload_scene_logical_ready
    moveq   #1, %d5
.Lload_scene_logical_ready:
    move.b  %d5, genesistan_current_scene_id
    cmpi.w  #1, %d5
    beq.s   .Lload_scene_keep_fg_owner_state
    clr.b   fg_native_gameplay_owner
.Lload_scene_keep_fg_owner_state:
    lea     genesistan_scene_a0_ranges, %a3
    moveq   #0, %d4
    move.w  %d5, %d4
    lsl.w   #3, %d4
    adda.w  %d4, %a3
    move.l  (%a3)+, %d0
    move.l  (%a3), %d1
    move.l  %d0, genesistan_scene_a0_lo
    move.l  %d1, genesistan_scene_a0_hi

    /* Build 0301: reset the streaming tile cache on gameplay-scene entry (display still off). */
    cmpi.w  #1, %d5
    bne.s   .Lload_scene_no_cache_reset
    bsr     fg_cache_reset
.Lload_scene_no_cache_reset:

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_ON, %d1
    bsr     vdp_set_reg

    move.w  (%sp)+, %sr
    movem.l (%sp)+, %d1-%d7/%a0-%a4
    rts


    .section .rodata,"a"

    .align 2
genesistan_pc080sn_tile_vram_lut:
    .incbin "../../build/pc080sn_tile_vram_lut.bin"

    .align 2
genesistan_pc080sn_attr_lut:
    .incbin "../../build/pc080sn_attr_lut.bin"

    .align 2
genesistan_pc080sn_tile_rom:
    .incbin "../../build/regions/pc080sn.bin"

    .align 2
genesistan_scene_preload_title:
    .incbin "../../build/pc080sn_scene_preload_title.bin"
genesistan_scene_preload_title_end:

    .align 2
genesistan_scene_preload_gameplay:
    .incbin "../../build/pc080sn_scene_preload_gameplay.bin"
genesistan_scene_preload_gameplay_end:

    .align 2
genesistan_scene_preload_gameplay_cave:
    .incbin "../../build/pc080sn_scene_preload_gameplay_cave.bin"
genesistan_scene_preload_gameplay_cave_end:

    .align 2
genesistan_scene_preload_stage1_cave_s4:
    .incbin "../../build/pc080sn_scene_preload_stage1_cave_s4.bin"
genesistan_scene_preload_stage1_cave_s4_end:

    .align 2
genesistan_scene_preload_stage1_cave_s5:
    .incbin "../../build/pc080sn_scene_preload_stage1_cave_s5.bin"
genesistan_scene_preload_stage1_cave_s5_end:

    .align 2
genesistan_scene_preload_stage1_cave_s6:
    .incbin "../../build/pc080sn_scene_preload_stage1_cave_s6.bin"
genesistan_scene_preload_stage1_cave_s6_end:

    .align 2
genesistan_scene_preload_stage1_seg1:
    .incbin "../../build/pc080sn_scene_preload_stage1_seg1.bin"
genesistan_scene_preload_stage1_seg1_end:

    .align 2
genesistan_scene_preload_stage1_seg2:
    .incbin "../../build/pc080sn_scene_preload_stage1_seg2.bin"
genesistan_scene_preload_stage1_seg2_end:

    .align 2
genesistan_scene_preload_endround:
    .incbin "../../build/pc080sn_scene_preload_endround.bin"
genesistan_scene_preload_endround_end:

genesistan_scene_a0_ranges:
    .long 0x0005A7DA
    .long 0x0005B0B2
    .long 0x00056A22
    .long 0x000570C2
    .long 0x0005822A
    .long 0x00059614

    .section .bss
    .align 2

genesistan_current_scene_id:
    .byte 0
genesistan_current_pc080sn_tileset_id:
    .byte 0
    .align 2
genesistan_scene_a0_lo:
    .long 0
genesistan_scene_a0_hi:
    .long 0
