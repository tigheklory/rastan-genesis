/* Build 0301: streaming PC080SN tile residency cache (Rev-3 design).
 *
 * Replaces the static code->slot LUT for gameplay Plane-A AND Plane-B production with a bounded,
 * source-driven streaming cache confined to sprite-safe Cache A (slots 0..1003; sprites live at
 * 1024+, Cache B 1344..1503 unused).  Key = arcade tile code & 0x3FFF (pattern is a pure function
 * of the code; palette/flip stay name-word attributes).  See
 * docs/design/Andy_streaming_fg_tile_residency_design.md (rev 3).
 *
 * Live-slot safety proof is the per-frame staged-buffer scan (fg_cache_mark_live), NOT resolve
 * frequency.  Eviction never touches a slot referenced by the displayed plane (fg_slot_live_frame
 * == frame) or this frame's production (fg_cache_touch == frame) or RESERVED/PINNED.
 */

    .section .text,"ax"

    .global fg_cache_reset
    .global fg_cache_resolve
    .global fg_cache_mark_live
    .global fg_hash_tbl
    .global fg_cache_rev
    .global fg_cache_touch
    .global fg_slot_live_frame
    .global fg_cache_state
    .global fg_upload_q
    .global fg_upload_count
    .global fg_frame_ctr
    .global fg_cache_occupancy
    .global fg_uploads_last
    .global fg_upload_overflow
    .global fg_evict_count
    .global fg_evict_live_attempts

    .extern staged_fg_buffer
    .extern staged_bg_buffer
    .extern genesistan_current_scene_id
    .extern genesistan_pc080sn_tile_vram_lut

    .equ HASH_BUCKETS,   2048           /* power of two */
    .equ HASH_MASK,      (HASH_BUCKETS-1)
    .equ SLOT_MIN,       64             /* 0..63 reserved: blank(0), HUD digits, frontend/text */
    .equ SLOT_MAX,       1003           /* Cache A top; sprites start at 1024 */
    .equ UPLOAD_CAP,     384            /* steady-state tiles/frame; warmup raises it */
    .equ ST_FREE,        0
    .equ ST_RESIDENT,    1
    .equ ST_RESERVED,    2

/* ---- fg_cache_reset: called on gameplay entry (display off).  Clears all runtime state,
 * marks slots 0..SLOT_MIN-1 RESERVED, empties the hash.  Warmup handled by caller raising cap. */
fg_cache_reset:
    movem.l %d0-%d2/%a0, -(%sp)
    /* hash -> 0xFFFF code sentinel (fill whole 8KB with 0xFF) */
    lea     fg_hash_tbl, %a0
    move.w  #(HASH_BUCKETS*2 - 1), %d0     /* words: 2 words/bucket */
    move.w  #0xFFFF, %d1
.Lrst_hash:
    move.w  %d1, (%a0)+
    dbra    %d0, .Lrst_hash
    /* rev -> 0xFFFF, state -> FREE, touch/live -> 0 for all 1004 slots */
    lea     fg_cache_rev, %a0
    move.w  #(1004 - 1), %d0
.Lrst_rev:
    move.w  #0xFFFF, (%a0)+
    dbra    %d0, .Lrst_rev
    lea     fg_cache_state, %a0
    move.w  #(1004 - 1), %d0
.Lrst_state:
    move.b  #ST_FREE, (%a0)+
    dbra    %d0, .Lrst_state
    lea     fg_cache_touch, %a0
    lea     fg_slot_live_frame, %a1
    move.w  #(1004 - 1), %d0
.Lrst_tl:
    move.w  #0, (%a0)+
    dbra    %d0, .Lrst_tl
    move.w  #(1004 - 1), %d0
    lea     fg_slot_live_frame, %a0
.Lrst_live:
    move.w  #0, (%a0)+
    dbra    %d0, .Lrst_live
    /* reserve slots 0..SLOT_MIN-1 */
    lea     fg_cache_state, %a0
    move.w  #(SLOT_MIN - 1), %d0
.Lrst_resv:
    move.b  #ST_RESERVED, (%a0)+
    dbra    %d0, .Lrst_resv
    move.w  #1, fg_frame_ctr
    clr.w   fg_upload_count
    clr.w   fg_cache_occupancy
    clr.w   fg_uploads_last
    clr.w   fg_upload_overflow
    clr.w   fg_evict_count
    clr.w   fg_evict_live_attempts
    movem.l (%sp)+, %d0-%d2/%a0
    rts

/* ---- fg_cache_hash: in d0.w=code (&0x3FFF) -> d0.w=bucket index (0..HASH_MASK). */
fg_cache_hash:
    /* Knuth multiplicative: (code*2654435761)>>21 & mask, done in 32-bit. */
    andi.l  #0x00003FFF, %d0
    move.l  %d0, %d1
    lsl.l   #4, %d1
    add.l   %d1, %d0                 /* *17 cheap spread */
    lsl.l   #7, %d0
    add.l   %d1, %d0
    lsr.l   #5, %d0
    andi.w  #HASH_MASK, %d0
    rts

/* ---- fg_cache_resolve: HOT.  in d3.w = arcade code; out d3.w = Genesis slot (0 = blank).
 * Clobbers d3 only; preserves all other registers (incl a2). */
fg_cache_resolve:
    movem.l %d0-%d2/%a0-%a1, -(%sp)
    andi.w  #0x3FFF, %d3
    beq     .Lrs_ret                /* code 0 = blank -> slot 0 */
    /* Gate: only the gameplay scene streams.  Title/end-round/frontend use the SAME producers, so
     * for them fall back to the static LUT (decision 3: frontend stays static). */
    cmpi.b  #1, genesistan_current_scene_id
    bne   .Lrs_static
    /* hash probe */
    move.w  %d3, %d0
    bsr     fg_cache_hash           /* d0 = bucket */
    lea     fg_hash_tbl, %a0
    move.w  %d3, %d2                /* d2 = code we want */
    moveq   #0, %d1                /* probe count guard */
.Lrs_probe:
    move.w  %d0, %a1
    add.w   %a1, %a1
    add.w   %a1, %a1               /* bucket*4 */
    lea     fg_hash_tbl, %a1
    move.w  %d0, %d3
    lsl.w   #2, %d3
    adda.w  %d3, %a1               /* a1 = &bucket[d0] */
    move.w  (%a1), %d3            /* bucket code */
    cmpi.w  #0xFFFF, %d3
    beq   .Lrs_miss             /* empty -> not resident */
    cmp.w   %d2, %d3
    beq   .Lrs_hit
    addq.w  #1, %d0
    andi.w  #HASH_MASK, %d0
    addq.w  #1, %d1
    cmpi.w  #HASH_BUCKETS, %d1
    blo   .Lrs_probe
    bra   .Lrs_miss             /* table full (shouldn't happen) */
.Lrs_hit:
    move.w  2(%a1), %d3           /* slot */
    /* touch[slot] = frame */
    move.w  %d3, %d0
    add.w   %d0, %d0
    lea     fg_cache_touch, %a0
    move.w  fg_frame_ctr, 0(%a0,%d0.w)
    bra     .Lrs_ret              /* d3 = slot */
.Lrs_miss:
    /* d2 = code, a1 = &bucket to insert (last probed empty slot) */
    move.w  fg_upload_count, %d0
    cmpi.w  #UPLOAD_CAP, %d0
    bhs     .Lrs_overflow
    /* allocate a slot */
    bsr     fg_cache_alloc        /* d3 = slot (0 = none) */
    tst.w   %d3
    beq     .Lrs_overflow_noinstall
    /* install hash entry at a1 (the empty bucket found) */
    move.w  %d2, (%a1)
    move.w  %d3, 2(%a1)
    /* rev[slot]=code, state=RESIDENT, touch=frame */
    move.w  %d3, %d0
    add.w   %d0, %d0
    lea     fg_cache_rev, %a0
    move.w  %d2, 0(%a0,%d0.w)
    move.w  fg_frame_ctr, %d1
    lea     fg_cache_touch, %a0
    move.w  %d1, 0(%a0,%d0.w)
    lea     fg_cache_state, %a0
    move.w  %d3, %d1
    move.b  #ST_RESIDENT, 0(%a0,%d1.w)
    /* queue (slot, code) */
    move.w  fg_upload_count, %d0
    lea     fg_upload_q, %a0
    move.w  %d0, %d1
    lsl.w   #2, %d1
    adda.w  %d1, %a0
    move.w  %d3, (%a0)+
    move.w  %d2, (%a0)
    addq.w  #1, fg_upload_count
    addq.w  #1, fg_cache_occupancy
    bra     .Lrs_ret              /* d3 = slot */
.Lrs_overflow:
.Lrs_overflow_noinstall:
    addq.w  #1, fg_upload_overflow
    moveq   #0, %d3               /* blank slot 0; no install; retry next frame */
.Lrs_ret:
    movem.l (%sp)+, %d0-%d2/%a0-%a1
    rts
.Lrs_static:
    /* static LUT passthrough for non-gameplay scenes: d3 = LUT[code] */
    move.w  %d3, %d0
    add.w   %d0, %d0
    lea     genesistan_pc080sn_tile_vram_lut, %a0
    move.w  0(%a0,%d0.w), %d3
    movem.l (%sp)+, %d0-%d2/%a0-%a1
    rts

/* ---- fg_cache_alloc: out d3.w = slot (0 = none evictable).  Live proof from mark_live + touch. */
fg_cache_alloc:
    movem.l %d0-%d2/%a0-%a2, -(%sp)
    /* pass 1: first FREE non-reserved slot */
    lea     fg_cache_state, %a0
    move.w  #SLOT_MIN, %d0
.Lal_free:
    cmpi.w  #SLOT_MAX, %d0
    bhi   .Lal_no_free
    move.w  %d0, %d1
    move.b  0(%a0,%d1.w), %d2
    cmpi.b  #ST_FREE, %d2
    beq   .Lal_take
    addq.w  #1, %d0
    bra   .Lal_free
.Lal_take:
    move.w  %d0, %d3
    bra   .Lal_ret
.Lal_no_free:
    /* pass 2: oldest-touch NON-LIVE resident slot */
    move.w  fg_frame_ctr, %d2      /* current frame */
    moveq   #0, %d3               /* best slot */
    move.w  #0xFFFF, %a2          /* best touch (unsigned max in a2 as scratch) */
    move.w  #SLOT_MIN, %d0
.Lal_scan:
    cmpi.w  #SLOT_MAX, %d0
    bhi   .Lal_done
    move.w  %d0, %d1
    lea     fg_cache_state, %a0
    move.b  0(%a0,%d1.w), %d1
    cmpi.b  #ST_RESIDENT, %d1
    bne   .Lal_next
    /* live? live_frame==frame OR touch==frame -> skip */
    move.w  %d0, %d1
    add.w   %d1, %d1
    lea     fg_slot_live_frame, %a0
    move.w  0(%a0,%d1.w), %a1
    cmp.w   %d2, %a1
    beq   .Lal_next             /* displayed-live */
    lea     fg_cache_touch, %a0
    move.w  0(%a0,%d1.w), %a1
    cmp.w   %d2, %a1
    beq   .Lal_next             /* in-production */
    /* candidate; pick oldest touch (a1 = its touch) */
    cmp.w   %a2, %a1
    bhs   .Lal_next
    move.w  %a1, %a2
    move.w  %d0, %d3
.Lal_next:
    addq.w  #1, %d0
    bra   .Lal_scan
.Lal_done:
    tst.w   %d3
    beq   .Lal_none             /* nothing evictable -> live-eviction would be needed */
    /* evict d3: delete its old hash entry (rev[d3] = old code) */
    move.w  %d3, %d1
    add.w   %d1, %d1
    lea     fg_cache_rev, %a0
    move.w  0(%a0,%d1.w), %d0     /* old code */
    cmpi.w  #0xFFFF, %d0
    beq   .Lal_evdone
    bsr     fg_hash_delete        /* d0 = code to remove */
    subq.w  #1, fg_cache_occupancy
.Lal_evdone:
    addq.w  #1, fg_evict_count
    bra   .Lal_ret
.Lal_none:
    addq.w  #1, fg_evict_live_attempts
    moveq   #0, %d3
.Lal_ret:
    movem.l (%sp)+, %d0-%d2/%a0-%a2
    rts

/* ---- fg_hash_delete: in d0.w = code to remove from the hash (linear-probe tombstone-free:
 * since we never leave holes mid-cluster, use backward-shift deletion is complex; instead mark
 * the removed bucket empty and rely on the low load factor + reinsert-on-miss). */
fg_hash_delete:
    movem.l %d0-%d2/%a0-%a1, -(%sp)
    move.w  %d0, %d2              /* code */
    bsr     fg_cache_hash        /* d0 = bucket */
    moveq   #0, %d1
.Lhd_probe:
    lea     fg_hash_tbl, %a1
    move.w  %d0, %a0
    lsl.w   #2, %d0
    adda.w  %d0, %a1
    move.w  (%a1), %d0
    cmpi.w  #0xFFFF, %d0
    beq   .Lhd_done            /* not found */
    cmp.w   %d2, %d0
    beq   .Lhd_hit
    move.w  %a0, %d0
    addq.w  #1, %d0
    andi.w  #HASH_MASK, %d0
    addq.w  #1, %d1
    cmpi.w  #HASH_BUCKETS, %d1
    blo   .Lhd_probe
    bra   .Lhd_done
.Lhd_hit:
    move.w  #0xFFFF, (%a1)       /* empty the bucket */
.Lhd_done:
    movem.l (%sp)+, %d0-%d2/%a0-%a1
    rts

/* ---- fg_cache_mark_live: called once per frame at VBlank end (after commits, before next
 * production).  Increments frame counter, then scans the full staged FG+BG buffers and marks every
 * referenced slot live for the new frame.  This is the eviction safety proof. */
fg_cache_mark_live:
    movem.l %d0-%d2/%a0-%a1, -(%sp)
    addq.w  #1, fg_frame_ctr
    move.w  fg_frame_ctr, %d2
    lea     fg_slot_live_frame, %a1
    /* Plane A */
    lea     staged_fg_buffer, %a0
    move.w  #(2048 - 1), %d0
.Lml_fg:
    move.w  (%a0)+, %d1
    andi.w  #0x07FF, %d1
    beq   .Lml_fg_next
    add.w   %d1, %d1
    move.w  %d2, 0(%a1,%d1.w)
.Lml_fg_next:
    dbra    %d0, .Lml_fg
    /* Plane B */
    lea     staged_bg_buffer, %a0
    move.w  #(2048 - 1), %d0
.Lml_bg:
    move.w  (%a0)+, %d1
    andi.w  #0x07FF, %d1
    beq   .Lml_bg_next
    add.w   %d1, %d1
    move.w  %d2, 0(%a1,%d1.w)
.Lml_bg_next:
    dbra    %d0, .Lml_bg
    move.w  fg_upload_count, fg_uploads_last
    movem.l (%sp)+, %d0-%d2/%a0-%a1
    rts

    .section .bss
    .align 2
fg_hash_tbl:          .space (HASH_BUCKETS * 4)   /* {code:u16, slot:u16} */
fg_cache_rev:         .space (1004 * 2)
fg_cache_touch:       .space (1004 * 2)
fg_slot_live_frame:   .space (1004 * 2)
fg_cache_state:       .space 1004
    .align 2
fg_upload_q:          .space (UPLOAD_CAP * 4)     /* {slot:u16, code:u16} */
fg_upload_count:      .space 2
fg_frame_ctr:         .space 2
fg_cache_occupancy:   .space 2
fg_uploads_last:      .space 2
fg_upload_overflow:   .space 2
fg_evict_count:       .space 2
fg_evict_live_attempts: .space 2
