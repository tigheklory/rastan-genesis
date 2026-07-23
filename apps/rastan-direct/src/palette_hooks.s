    .section .text,"ax"

    .global genesistan_palette_hook_59ad4
    .global genesistan_palette_hook_03ab00
    .global genesistan_palette_hook_45dae
    .global genesistan_palette_hook_3ba64
    .global palette_route_lookup

    .include "pc090oj_config.inc"

    .extern palette_dirty
    .extern staged_palette_words
    .extern fg_bank3_line_cache
    .extern fg_bank3_cache_valid
    .extern fg_bank3_route_seen
    .extern pc090oj_bank36_line0_cache
    .extern pc090oj_bank36_cache_valid

/* ------------------------------------------------------------------------- *
 * Build 0175: arcade palette-bank -> Genesis CRAM-line route table.
 *
 * Prior builds (0173/0174) chose a Genesis FG line by hand (FG_PLANE_ATTR_HI
 * guess) and had two palette hooks independently deciding which staged line a
 * bank landed in.  This table is the single source of truth for
 *   (scene_id, owner, arcade_bank) -> genesis_line (+ carrier flag)
 * so the FG-attribute line, the palette-staging line, and the gameplay carrier
 * re-assert all agree.  For Stage 1 gameplay the evidence
 * (states/traces/build0174_fg_palette_source_20260715_195606) is:
 *   line 0 = arcade bank 0  (HUD/frontend white)
 *   line 1 = FG cells point here, but it holds a STALE pre-gameplay frontend
 *            palette; nothing writes line 1 during gameplay -> free to carry
 *            arcade FG bank 3, but must be re-asserted at the gameplay boundary
 *   line 2 = arcade BG bank  (terrain/sky)
 *   line 3 = arcade bank 51  (PC090OJ sprites)
 * So arcade PC080SN FG bank 3 is routed to Genesis line 1 with the CARRIER flag
 * (classification A).  The carrier re-assert (vdp_reassert_fg_bank3_line) keeps
 * line 1 populated with the converted bank 3 during scene 1 only; frontend line
 * 1 (arcade bank 1 / story) is untouched before gameplay.
 * ------------------------------------------------------------------------- */
    .equ PROUTE_OWNER_HUD,        0
    .equ PROUTE_OWNER_PC080SN_BG, 1
    .equ PROUTE_OWNER_PC080SN_FG, 2
    .equ PROUTE_OWNER_PC090OJ,    3
    .equ PROUTE_OWNER_FRONTEND,   4
    .equ PROUTE_FLAG_CARRIER,     1        /* line needs gameplay carrier re-assert */
    .equ PROUTE_SCENE_GAMEPLAY,   1
    .equ PROUTE_FG_BANK,          3        /* arcade PC080SN Stage 1 FG color bank */
    .equ PROUTE_FG_LINE,          1        /* Genesis CRAM line carrying FG bank 3 */

    .section .rodata
    .align 2
/* rows: scene_id, owner, arcade_bank, genesis_line, flags; 0xFFFF terminator */
palette_route_table:
    .word 1, PROUTE_OWNER_PC080SN_FG, 3,  1, PROUTE_FLAG_CARRIER
    .word 1, PROUTE_OWNER_PC080SN_BG, 48, 2, 0
    .word 1, PROUTE_OWNER_PC090OJ,    51, 3, 0
    .word 1, PROUTE_OWNER_HUD,        0,  0, 0
.if RASTAN_GAMEPLAY_HUD_SPRITES != 1
    /* Build 0208/0230: with gameplay HUD sprites suppressed or limited to the
     * 1UP-only representation, CRAM line 0 is free during gameplay; carry
     * PC090OJ effective sprite bank 0x36 (lizard men, hurry-up family) there.
     * CARRIER: the converted bank-0x36 palette is cached by the palette hooks
     * and re-asserted each gameplay VBlank (vdp_reassert_bank36_line0), never
     * staged in non-gameplay scenes. */
    .word 1, PROUTE_OWNER_PC090OJ,    0x36, 0, PROUTE_FLAG_CARRIER
.endif
    .word 0xFFFF, 0, 0, 0, 0

    .section .text,"ax"

/* palette_route_lookup: resolve (scene,owner,bank) -> line/flags via the table.
 * in:  D0 = scene_id, D1 = owner, D2 = arcade_bank
 * out: D0 = genesis_line (0..3) and D3 = flags if a row matches;
 *      D0 = -1 (0xFFFFFFFF) if no row matches (D3 undefined).
 * Clobbers: D0, D3, A0.
 */
palette_route_lookup:
    lea     palette_route_table, %a0
.Lproute_scan:
    cmpi.w  #0xFFFF, (%a0)                  /* terminator? */
    beq.s   .Lproute_miss
    cmp.w   (%a0), %d0                     /* scene match? */
    bne.s   .Lproute_next
    cmp.w   2(%a0), %d1                     /* owner match? */
    bne.s   .Lproute_next
    cmp.w   4(%a0), %d2                     /* bank match? */
    bne.s   .Lproute_next
    move.w  8(%a0), %d3                     /* flags */
    andi.l  #0x0000FFFF, %d3
    move.w  6(%a0), %d0                     /* genesis_line */
    andi.l  #0x0000FFFF, %d0
    rts
.Lproute_next:
    lea     10(%a0), %a0
    bra.s   .Lproute_scan
.Lproute_miss:
    moveq   #-1, %d0
    rts

/* Convert xBGR-555 in D0 to Genesis CRAM (0000_BBB0_GGG0_RRR0) in D1.
 * Clobbers: D1, D2, D3
 */
.Lxbgr555_to_cram:
    move.w  %d0, %d1
    andi.w  #0x001F, %d1
    lsr.w   #2, %d1
    lsl.w   #1, %d1

    move.w  %d0, %d2
    lsr.w   #5, %d2
    andi.w  #0x001F, %d2
    lsr.w   #2, %d2
    lsl.w   #1, %d2
    lsl.w   #4, %d2
    or.w    %d2, %d1

    move.w  %d0, %d3
    lsr.w   #8, %d3
    lsr.w   #2, %d3
    andi.w  #0x001F, %d3
    lsr.w   #2, %d3
    lsl.w   #1, %d3
    lsl.w   #8, %d3
    or.w    %d3, %d1
    rts

/* 0x59AD4 replacement
 * in: A0=source base, D0=arcade bank, D1=source row
 */
genesistan_palette_hook_59ad4:
    movem.l %d0-%d7/%a0-%a2, -(%sp)
    clr.b   fg_bank3_route_seen

    /* Build 0145: the arcade's bank-51 sprite-palette update reaches this helper
     * with d0 = 0x33; route it to Genesis staged line 3 (destination d0 = 3)
     * through the existing conversion/staging body, keeping the arcade's own
     * source (a0 + d1*32).  Every other high bank keeps the existing <4
     * rejection. Build 0174: Stage-1 PC080SN FG uses arcade color bank 3,
     * while Genesis line 3 is reserved for sprite bank 51, so carry arcade
     * bank 3 in otherwise-free gameplay line 1. */
    cmpi.w  #0x0033, %d0
    bne.s   .L59_not_bank51
    moveq   #3, %d0                 /* arcade bank 51 -> Genesis line 3 */
    bra.s   .L59_dest_ready
.L59_not_bank51:
    cmpi.w  #3, %d0
    bne.s   .L59_not_bank3
    moveq   #1, %d0                 /* arcade bank 3 -> Genesis line 1 */
    move.b  #1, fg_bank3_route_seen /* remember bank-3 route for line-1 cache */
    bra.s   .L59_dest_ready
.L59_not_bank3:
.if RASTAN_GAMEPLAY_HUD_SPRITES != 1
    /* Build 0208: arcade sprite bank 0x36 (lizard men) -> cache only.  The
     * bank is written once at stage load, possibly while the frontend still
     * owns line 0, so it is never staged directly; the gameplay carrier
     * (vdp_reassert_bank36_line0) applies the cache during scene 1. */
    cmpi.w  #0x0036, %d0
    beq     .L59_bank36_cache
.endif
    cmpi.w  #4, %d0
    bcc.s   .L59_done
.L59_dest_ready:

    move.w  %d1, %d2
    mulu.w  #32, %d2
    adda.w  %d2, %a0

    lea     staged_palette_words, %a1
    move.w  %d0, %d2
    lsl.w   #5, %d2
    adda.w  %d2, %a1

    moveq   #0, %d5
    moveq   #15, %d6
.L59_loop:
    move.w  (%a0)+, %d1
    cmpi.w  #0xFFFF, %d1
    beq.s   .L59_next

    move.w  %d1, %d2
    move.w  %d1, %d3
    andi.w  #0x0F00, %d1
    lsr.w   #7, %d1
    andi.w  #0x00F0, %d2
    lsl.w   #2, %d2
    andi.w  #0x000F, %d3
    lsl.w   #8, %d3
    lsl.w   #3, %d3
    add.w   %d1, %d3
    add.w   %d2, %d3

    move.w  %d3, %d0
    bsr     .Lxbgr555_to_cram
    move.w  %d1, (%a1)+
    moveq   #1, %d5
.L59_next:
    dbra    %d6, .L59_loop

    tst.b   %d5
    beq.s   .L59_done
    move.b  #1, palette_dirty
.L59_done:
    /* Build 0175: if this call staged arcade FG bank 3 into staged line 1,
     * snapshot line 1 into the carrier cache so the gameplay re-assert can
     * restore it after any later frontend line-1 write. */
    tst.b   fg_bank3_route_seen
    beq.s   .L59_no_cache
    lea     staged_palette_words, %a0
    lea     (PROUTE_FG_LINE * 16 * 2)(%a0), %a0
    lea     fg_bank3_line_cache, %a1
    moveq   #(16 - 1), %d7
.L59_cache_copy:
    move.w  (%a0)+, (%a1)+
    dbra    %d7, .L59_cache_copy
    move.b  #1, fg_bank3_cache_valid
.L59_no_cache:
    movem.l (%sp)+, %d0-%d7/%a0-%a2
    rts

.if RASTAN_GAMEPLAY_HUD_SPRITES != 1
/* Build 0208: convert arcade bank 0x36 (source = a0 + d1*32, same entry format
 * as the main body) into the gameplay line-0 carrier cache.  Never stages the
 * live palette here; the scene-1 re-assert owns line 0 during gameplay. */
.L59_bank36_cache:
    move.w  %d1, %d2
    mulu.w  #32, %d2
    adda.w  %d2, %a0
    lea     pc090oj_bank36_line0_cache, %a1
    moveq   #15, %d6
.L59_b36_loop:
    move.w  (%a0)+, %d1
    cmpi.w  #0xFFFF, %d1
    beq.s   .L59_b36_next
    move.w  %d1, %d2
    move.w  %d1, %d3
    andi.w  #0x0F00, %d1
    lsr.w   #7, %d1
    andi.w  #0x00F0, %d2
    lsl.w   #2, %d2
    andi.w  #0x000F, %d3
    lsl.w   #8, %d3
    lsl.w   #3, %d3
    add.w   %d1, %d3
    add.w   %d2, %d3
    move.w  %d3, %d0
    bsr     .Lxbgr555_to_cram
    move.w  %d1, (%a1)
.L59_b36_next:
    addq.l  #2, %a1
    dbra    %d6, .L59_b36_loop
    move.b  #1, pc090oj_bank36_cache_valid
    bra     .L59_done
.endif

/* 0x03AB00 replacement
 * original: movew #1023,0x200022 (bank 1, entry 1), already xBGR-555
 */
genesistan_palette_hook_03ab00:
    movem.l %d0-%d3/%a0, -(%sp)

    move.w  #0x03FF, %d0
    bsr     .Lxbgr555_to_cram
    lea     staged_palette_words, %a0
    move.w  %d1, 34(%a0)
    move.b  #1, palette_dirty

    movem.l (%sp)+, %d0-%d3/%a0
    rts

/* 0x045DB8 replacement
 * replaces jsr 0x3A2D0 copy-call.
 * in: A0=source, A1=arcade destination (0x200000 + idx*0x80), D0=count(words)
 */
genesistan_palette_hook_45dae:
    movem.l %d0-%d4/%a0-%a2, -(%sp)

    cmpa.l  #0x00200000, %a1
    bne.s   .L45_done

    tst.w   %d0
    beq.s   .L45_done

    lea     staged_palette_words, %a2
    move.w  %d0, %d4
    subq.w  #1, %d4
.L45_loop:
    move.w  (%a0)+, %d0
    bsr     .Lxbgr555_to_cram
    /* Build (lines 0/1): this bank-0 chunk copies the sprite-palette SOURCE buffer
     * (a5@0x1600 = Genesis 0x00FF1600) -> staged lines 0..3. On Genesis that source
     * buffer is never populated (all zero), so the original unconditional write here
     * ZEROED lines 0/1 (and 2/3) that genesistan_palette_hook_3ba64 had correctly
     * staged from the arcade direct palette-RAM writes. Only write NON-zero converted
     * colors (advance the staged slot positionally regardless), so an empty source no
     * longer clobbers the real palette; a populated source still writes normally. */
    tst.w   %d1
    beq.s   .L45_skip_write
    move.w  %d1, (%a2)
.L45_skip_write:
    addq.l  #2, %a2
    dbra    %d4, .L45_loop

    move.b  #1, palette_dirty

.L45_done:
    movem.l (%sp)+, %d0-%d4/%a0-%a2
    rts

/* 0x03BA64 replacement (runtime 0x03BC64)
 * in: A0=arcade palette destination pointer, A3=arcade source pointer, D3=loop count (long)
 * out: matches original side effects: A0/A3 advanced by count*2, D3 exits as 0.
 * note: preserves Build 55 locked conversion path:
 *   raw 0RGB-444 -> xBGR-555 (original 0x03BA64 body) -> Genesis CRAM (via .Lxbgr555_to_cram).
 */
genesistan_palette_hook_3ba64:
    movem.l %d4-%d7/%a1, -(%sp)
    clr.l   %d5
    clr.b   fg_bank3_route_seen

.L3ba64_loop:
    /* Reproduce original 0x03BA64 conversion in D0/D1/D2. */
    move.w  (%a3)+, %d0
    move.w  %d0, %d2
    andi.w  #0x0F00, %d0
    lsr.w   #7, %d0
    move.w  %d2, %d1
    andi.w  #0x00F0, %d1
    lsl.w   #2, %d1
    andi.w  #0x000F, %d2
    ror.w   #5, %d2
    or.w    %d1, %d0
    or.w    %d2, %d0

    /* Preserve pointer side effect regardless of bank filtering. */
    move.l  %a0, %d4
    addq.l  #2, %a0

    /* Build 0161: the arcade sprite palette bank 51 is written by this routine only
     * to the sprite-palette SOURCE buffer (arcade 0x10D660 = Genesis a5@0x1600 =
     * 0x00FF1660), then memcpy'd to arcade palette RAM 0x200660 (unmapped on
     * Genesis -> dropped) -- so Genesis CRAM line 3 (=arcade bank 51, used by
     * gameplay FG and sprites/Rastan) was never populated. Stage the bank-51
     * source-buffer writes (a0 in 0x00FF1660..0x00FF167F) directly to staged line 3
     * (d6=3) via the existing xBGR->CRAM/line-3 path. Bank 48 (line 2) is unaffected
     * (it is written to palette RAM 0x200600 by a separate caller). */
    cmpi.l  #0x00FF1660, %d4
    blo.s   .L3ba64_chk_b36src
    cmpi.l  #0x00FF1680, %d4
    bhs.s   .L3ba64_chk_b36src
    moveq   #3, %d6
    bra.w   .L3ba64_line_ok

.L3ba64_chk_b36src:
.if RASTAN_GAMEPLAY_HUD_SPRITES != 1
    /* Build 0208: sprite bank 0x36 (lizard men) follows the same source-buffer
     * path as bank 51 (Build 0161): the arcade writes it to the sprite-palette
     * SOURCE buffer at a5@0x1600 + (bank-0x30)*0x20 -- bank 0x36 = Genesis
     * 0x00FF16C0..0x00FF16DF -- then memcpy's to palette RAM 0x2006C0 (dropped
     * on Genesis).  Catch the source-buffer write and cache it for the
     * gameplay line-0 carrier (never staged directly). */
    cmpi.l  #0x00FF16C0, %d4
    blo.s   .L3ba64_chk_palram
    cmpi.l  #0x00FF16E0, %d4
    bhs.s   .L3ba64_chk_palram
    bra     .L3ba64_bank36_cache    /* entry = (addr & 0x1F) >> 1, same math */
.endif

.L3ba64_chk_palram:
    /* Only map arcade palette RAM 0x200000..0x200FFF into Genesis staging. */
    cmpi.l  #0x00200000, %d4
    blo.s   .L3ba64_next
    cmpi.l  #0x00201000, %d4
    bhs.s   .L3ba64_next

    sub.l   #0x00200000, %d4
    move.l  %d4, %d6
    lsr.l   #5, %d6                  /* arcade bank index */
    /* Build 0144 frontend sprite-palette split: keep arcade banks 0/1 in
     * Genesis lines 0/1 (plane palettes), route arcade bank 48 -> line 2 and
     * arcade bank 51 -> line 3 (sprite banks), skip every other bank.
     * Build 0174: Stage-1 PC080SN FG uses arcade bank 3; line 3 is already
     * owned by bank 51, so route bank 3 to the free gameplay carrier line 1. */
    cmpi.l  #2, %d6
    blo.s   .L3ba64_line_ok         /* banks 0,1 -> lines 0,1 */
    cmpi.l  #3, %d6
    beq.s   .L3ba64_to_line1
    cmpi.l  #48, %d6
    beq.s   .L3ba64_to_line2
    cmpi.l  #51, %d6
    beq.s   .L3ba64_to_line3
.if RASTAN_GAMEPLAY_HUD_SPRITES != 1
    cmpi.l  #0x36, %d6              /* Build 0208: bank 0x36 -> carrier cache */
    beq     .L3ba64_bank36_cache
.endif
    bra.s   .L3ba64_next            /* all other banks skipped */
.L3ba64_to_line1:
    moveq   #1, %d6                 /* arcade bank 3 -> Genesis line 1 */
    move.b  #1, fg_bank3_route_seen /* remember bank-3 route for line-1 cache */
    bra.s   .L3ba64_line_ok
.L3ba64_to_line2:
    moveq   #2, %d6                 /* arcade bank 48 -> Genesis line 2 */
    bra.s   .L3ba64_line_ok
.L3ba64_to_line3:
    moveq   #3, %d6                 /* arcade bank 51 -> Genesis line 3 */
.L3ba64_line_ok:

    move.l  %d4, %d7
    andi.l  #0x001F, %d7
    lsr.l   #1, %d7                  /* entry within bank: 0..15 */

    move.l  %d3, %d4                 /* preserve long loop counter across BSR */
    bsr     .Lxbgr555_to_cram
    move.l  %d4, %d3
    move.w  %d1, %d2                 /* keep converted color */
    move.w  %d6, %d1
    lsl.w   #4, %d1
    add.w   %d7, %d1
    lsl.w   #1, %d1                  /* byte offset in staged_palette_words */
    lea     staged_palette_words, %a1
    move.w  %d2, 0(%a1,%d1.w)
    moveq   #1, %d5

.L3ba64_next:
    /* Keep original long-word loop semantics (not DBRA). */
    subq.l  #1, %d3
    bne     .L3ba64_loop

    tst.l   %d5
    beq.s   .L3ba64_done
    move.b  #1, palette_dirty

.L3ba64_done:
    /* Build 0175: snapshot staged line 1 into the FG bank-3 carrier cache when
     * this call routed arcade bank 3 there.  a0 (arcade return pointer) must be
     * preserved; a1 is restored by movem below. */
    tst.b   fg_bank3_route_seen
    beq.s   .L3ba64_no_cache
    move.l  %a0, -(%sp)
    lea     staged_palette_words, %a0
    lea     (PROUTE_FG_LINE * 16 * 2)(%a0), %a0
    lea     fg_bank3_line_cache, %a1
    moveq   #(16 - 1), %d7
.L3ba64_cache_copy:
    move.w  (%a0)+, (%a1)+
    dbra    %d7, .L3ba64_cache_copy
    move.b  #1, fg_bank3_cache_valid
    move.l  (%sp)+, %a0
.L3ba64_no_cache:
    movem.l (%sp)+, %d4-%d7/%a1
    rts

.if RASTAN_GAMEPLAY_HUD_SPRITES != 1
/* Build 0208: direct arcade palette-RAM write to bank 0x36 (lizard men) ->
 * gameplay line-0 carrier cache.  d0 = converted xBGR-555 color, d4 = arcade
 * destination address, d3 = live long loop counter (preserved across the
 * conversion BSR exactly like the staged path). */
.L3ba64_bank36_cache:
    move.l  %d4, %d7
    andi.l  #0x001F, %d7
    lsr.l   #1, %d7                  /* entry within bank: 0..15 */
    move.l  %d3, %d4                 /* preserve long loop counter across BSR */
    bsr     .Lxbgr555_to_cram
    move.l  %d4, %d3
    lsl.w   #1, %d7                  /* byte offset in the cache */
    lea     pc090oj_bank36_line0_cache, %a1
    move.w  %d1, 0(%a1,%d7.w)
    move.b  #1, pc090oj_bank36_cache_valid
    bra     .L3ba64_next
.endif
