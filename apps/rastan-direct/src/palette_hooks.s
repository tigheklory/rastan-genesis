    .section .text,"ax"

    .global genesistan_palette_hook_59ad4
    .global genesistan_palette_hook_03ab00
    .global genesistan_palette_hook_45dae
    .global genesistan_palette_hook_3ba64
    .global palette_route_lookup

    .include "pc090oj_config.inc"

    .extern genesistan_current_scene_id
    .extern staged_palette_words
    /* Build 0336: palette_dirty and the fg-bank3 / bank-0x36 carrier caches were retired. */

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
    .equ PROUTE_FG_LINE,          3        /* Build 0325: shared Layer-A master palette on Genesis CRAM Line 3 */

    .section .rodata
    .align 2
/* rows: scene_id, owner, arcade_bank, genesis_line, flags; 0xFFFF terminator */
palette_route_table:
    /* Build 0325: FINAL frozen-Test R1/P1 line ownership.
     *   Line 0 = Test shared sprite palette (source banks 0x32,0x33,0x34,0x3E)
     *   Line 1 = Test shared sprite palette (source banks 0x35,0x36,0x3A)
     *   Line 2 = Layer B (arcade BG bank 48) - PROTECTED
     *   Line 3 = Test shared Layer-A master palette (PC080SN FG carrier)
     * Sprite rows select the SAT palette line for the OFFLINE-reindexed sprite art (not raw arcade
     * bank->CRAM). Build 0329: static Test Lines 0/1/3 are installed ONCE at the gameplay-scene
     * activation event (load_scene_tiles -> vdp_install_test_lines); during scene 1 the arcade
     * palette hooks below are gated off Lines 0/1/3 (Layer-B Line 2 still flows), so no per-VBlank
     * reassert is needed. */
    .word 1, PROUTE_OWNER_PC080SN_FG, 3,  3, PROUTE_FLAG_CARRIER
    .word 1, PROUTE_OWNER_PC080SN_BG, 48, 2, 0
    /* R1/P1 Test sprite source-bank ownership -> Line 0 */
    .word 1, PROUTE_OWNER_PC090OJ,    0x33, 0, 0
    .word 1, PROUTE_OWNER_PC090OJ,    0x32, 0, 0
    .word 1, PROUTE_OWNER_PC090OJ,    0x34, 0, 0
    .word 1, PROUTE_OWNER_PC090OJ,    0x3E, 0, 0
    /* R1/P1 Test sprite source-bank ownership -> Line 1 */
    .word 1, PROUTE_OWNER_PC090OJ,    0x36, 1, 0
    .word 1, PROUTE_OWNER_PC090OJ,    0x35, 1, 0
    .word 1, PROUTE_OWNER_PC090OJ,    0x3A, 1, 0
    .word 1, PROUTE_OWNER_HUD,        0,  0, 0
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

    /* Build 0145: the arcade's bank-51 sprite-palette update reaches this helper with d0 = 0x33;
     * route it to Genesis staged line 3.  Build 0174: Stage-1 PC080SN FG bank 3 -> Genesis line 1.
     * Build 0336: the fg-bank3 / bank-0x36 carrier-cache side path was removed with the dead
     * reasserts; bank 0x36 now simply falls through to the normal reject. */
    cmpi.w  #0x0033, %d0
    bne.s   .L59_not_bank51
    moveq   #3, %d0                 /* arcade bank 51 -> Genesis line 3 */
    bra.s   .L59_dest_ready
.L59_not_bank51:
    cmpi.w  #3, %d0
    bne.s   .L59_not_bank3
    moveq   #1, %d0                 /* arcade bank 3 -> Genesis line 1 */
    bra.s   .L59_dest_ready
.L59_not_bank3:
    /* Build 0334 EXPERIMENTAL: type-9 waterfall route.  In scene 1 the arcade water banks 0x1A-0x1D
     * carry the type-9 frame data whose only non-0xFFFF entries are 14 and 15.  Publish those two
     * animated colors POSITIONALLY to Line-3 entries 14/15 (dominant authored mapping = identity),
     * preserving every other Line-3 entry and the 0xFFFF keep.  NOT the general (compacting) loop;
     * NOT a permanent mapping; the arcade owns the timing (D1 = frame index). */
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .L59_not_water
    cmpi.w  #0x001A, %d0
    blo.s   .L59_not_water
    cmpi.w  #0x001D, %d0
    bhi.s   .L59_not_water
    bra.w   .L59_water
.L59_not_water:
    cmpi.w  #4, %d0
    bcc.s   .L59_done
.L59_dest_ready:
    /* Build 0331: R1/P1 (scene 1) -> only Layer-B Line 2 (arcade bank 2, the gameplay sky) may be
     * staged by this arcade producer; Lines 0/1/3 are Test-owned (installed once at scene
     * activation).  Frontend / other scenes stage all lines.  Line 2 is partial-dynamic: the loop
     * rewrites only the entries the arcade actually changes and marks palette_dirty only on a real
     * change, so a static sky costs no per-frame CRAM commit. */
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .L59_dest_ok
    cmpi.w  #2, %d0
    bne     .L59_done
.L59_dest_ok:
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
    cmp.w   (%a1), %d1              /* Build 0331: write + dirty only when the value actually changes */
    beq.s   .L59_adv
    move.w  %d1, (%a1)
    moveq   #1, %d5
.L59_adv:
    addq.l  #2, %a1
.L59_next:
    dbra    %d6, .L59_loop

.L59_done:
    /* Build 0336: publication is the unconditional VBlank CRAM DMA -- no palette_dirty here; the
     * retired fg-bank3 carrier-cache snapshot was removed with the dead reasserts. */
    movem.l (%sp)+, %d0-%d7/%a0-%a2
    rts

/* Build 0334 EXPERIMENTAL type-9 waterfall handler.  a0 = frame table base, d1 = frame row.
 * Reads arcade animated entries 14 (offset 0x1C) and 15 (0x1E) from frame source a0 + row*0x20;
 * converts arcade 0RGB444 -> Genesis CRAM; writes ONLY Line-3 entries 14/15 (offsets 0x1C/0x1E in
 * the 32-byte line), change-detected.  Every other Line-3 entry and Line 2 are untouched.
 * d0-d7/a0-a2 are restored by the .L59_done movem. */
.L59_water:
    move.w  %d1, %d2
    mulu.w  #32, %d2
    adda.w  %d2, %a0                     /* a0 = frame source (16 words) */
    lea     staged_palette_words + (3 * 32), %a1  /* Line 3 base */
    moveq   #0, %d5
    move.w  28(%a0), %d1                 /* arcade entry 14 */
    cmpi.w  #0xFFFF, %d1
    beq.s   .L59_water_e15
    bsr     .L59_water_cvt
    cmp.w   28(%a1), %d1                 /* Line 3 index 14 */
    beq.s   .L59_water_e15
    move.w  %d1, 28(%a1)
    moveq   #1, %d5
.L59_water_e15:
    move.w  30(%a0), %d1                 /* arcade entry 15 */
    cmpi.w  #0xFFFF, %d1
    beq.s   .L59_water_fin
    bsr     .L59_water_cvt
    cmp.w   30(%a1), %d1                 /* Line 3 index 15 */
    beq.s   .L59_water_fin
    move.w  %d1, 30(%a1)
    moveq   #1, %d5
.L59_water_fin:
    /* Build 0336: the staged Line-3 14/15 writes above are published by the unconditional VBlank
     * CRAM DMA (no palette_dirty).  This restores the Build-0334 waterfall animation. */
    bra.w   .L59_done

/* arcade 0RGB444 in d1 -> Genesis CRAM in d1; clobbers d0/d2/d3 (same conversion as the main body). */
.L59_water_cvt:
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
    bra     .Lxbgr555_to_cram           /* tail-call: converts d0 -> d1, then rts */

/* Build 0336: the bank-0x36 line-0 carrier cache handler (.L59_bank36_cache) was removed with the
 * dead bank36 reassert; bank 0x36 now falls through to the normal reject. */

/* 0x03AB00 replacement
 * original: movew #1023,0x200022 (bank 1, entry 1), already xBGR-555
 */
genesistan_palette_hook_03ab00:
    movem.l %d0-%d3/%a0, -(%sp)

    move.w  #0x03FF, %d0
    bsr     .Lxbgr555_to_cram
    lea     staged_palette_words, %a0
    move.w  %d1, 34(%a0)
    /* Build 0336: no palette_dirty; the unconditional VBlank CRAM DMA publishes this staged word. */

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

    /* Build 0329/0331: this bank-0 positional copy targets the Test-owned Lines 0..3.  The gameplay
     * Layer-B (Line 2) sky is NOT loaded here (proven: allowing this hook's Line-2 writes in scene 1
     * left the sky frozen; the real loader is genesistan_palette_hook_59ad4 bank 2 -> Line 2).  In
     * R1/P1 (scene 1) Lines 0/1/3 are Test-owned, so skip the whole copy; frontend / other scenes
     * are unaffected. */
    cmpi.b  #1, genesistan_current_scene_id
    beq.s   .L45_done

    lea     staged_palette_words, %a2
    move.w  %d0, %d4
    subq.w  #1, %d4
.L45_loop:
    move.w  (%a0)+, %d0
    bsr     .Lxbgr555_to_cram
    /* Only write NON-zero converted colors (advance the staged slot positionally regardless) so an
     * empty source cannot clobber the real palette; a populated source writes normally. */
    tst.w   %d1
    beq.s   .L45_skip_write
    move.w  %d1, (%a2)
.L45_skip_write:
    addq.l  #2, %a2
    dbra    %d4, .L45_loop

    /* Build 0336: no palette_dirty; the unconditional VBlank CRAM DMA publishes the staged lines. */

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
    /* Build 0336: the bank-0x36 source-buffer carrier cache was removed with the dead reasserts;
     * such writes now fall through to the palette-RAM check (and are skipped). */
.L3ba64_chk_palram:
    /* Only map arcade palette RAM 0x200000..0x200FFF into Genesis staging. */
    cmpi.l  #0x00200000, %d4
    blo.w   .L3ba64_next
    cmpi.l  #0x00201000, %d4
    bhs.w   .L3ba64_next

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
    bra.s   .L3ba64_next            /* all other banks skipped (incl. bank 0x36) */
.L3ba64_to_line1:
    moveq   #1, %d6                 /* arcade bank 3 -> Genesis line 1 */
    bra.s   .L3ba64_line_ok
.L3ba64_to_line2:
    moveq   #2, %d6                 /* arcade bank 48 -> Genesis line 2 */
    bra.s   .L3ba64_line_ok
.L3ba64_to_line3:
    moveq   #3, %d6                 /* arcade bank 51 -> Genesis line 3 */
.L3ba64_line_ok:
    /* Build 0329: during R1/P1 (scene 1), Test owns Lines 0/1/3 (installed at scene activation).
     * Only Layer-B Line 2 may still be written by this arcade producer; skip any 0/1/3 target so
     * the static Test palette is not re-owned per stage/segment load.  Frontend / other scenes are
     * unaffected (they keep full arcade palette staging). */
    cmpi.b  #1, genesistan_current_scene_id
    bne.s   .L3ba64_line_store
    cmpi.w  #2, %d6
    bne     .L3ba64_next
.L3ba64_line_store:

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

.L3ba64_done:
    /* Build 0336: no palette_dirty and no fg-bank3 carrier-cache snapshot (both retired with the
     * dead reasserts); the unconditional VBlank CRAM DMA publishes the staged palette. */
    movem.l (%sp)+, %d4-%d7/%a1
    rts


    .section .rodata
    .align 2
    .global editor_layera_palette
editor_layera_palette:
    .word 0x0000, 0x028C, 0x044C, 0x0026, 0x0004, 0x0002, 0x0424, 0x0624
    .word 0x0402, 0x0202, 0x0200, 0x0422, 0x0440, 0x0660, 0x0AA6, 0x0884

/* Build 0325: frozen-Test shared R1/P1 sprite palettes. Static ROM data (frozen Test profile
 * target_palette_lines[0] and [1]); staged onto Genesis Lines 0/1 each gameplay VBlank. The offline
 * PC090OJ reindex (pc090oj_editor.bin) remaps sprite pixels into these exact target entries. */
    .global test_sprite_line0
test_sprite_line0:
    .word 0x0000, 0x006C, 0x0226, 0x0224, 0x068A, 0x0466, 0x002C, 0x0000
    .word 0x0EEE, 0x08AE, 0x044A, 0x0008, 0x00EE, 0x0080, 0x0060, 0x0040
    .global test_sprite_line1
test_sprite_line1:
    .word 0x0000, 0x08CC, 0x0242, 0x0486, 0x0064, 0x04A6, 0x04A0, 0x0662
    .word 0x0CCA, 0x0CCC, 0x0028, 0x024C, 0x0422, 0x0AA6, 0x0640, 0x0AC4
