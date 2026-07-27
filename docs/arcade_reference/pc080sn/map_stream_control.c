/*
 * Rastan arcade — map-stream selection + progression (documentation reconstruction).
 * Reconstructed from original 68000 opcodes; opcodes authoritative. a5 = 0x10C000.
 * Companion prose + tables: map_stream_format.md. Word/byte widths preserved.
 *
 * MODEL: a scene's map data is a flat byte stream at ROM 0x50F6B. Records are variable-length
 * (LUT 0x50EE0): indices 0-137 proven = 120 one-byte + 18 two-byte [direction, event] records
 * (record 138 candidate [00 07]).
 * The stage number (a5@0x1242) picks a segment index (a5@0x13E) via LUT 0x5073A; that seeds
 * the stream pointer a5@0x10C6 (= 0x50F6B + 0x50EE0[seg]) and the 16 strip-source bases.
 * a5@0x10C6 and a5@0x13E then advance TOGETHER +1 per completed 64-publication ring cycle
 * (0x0558E4 / 0x0558FE) — the pointer is NOT recomputed from the LUT each frame (MAME-verified).
 * A DIRECTION byte (0/1/2) drives one 64-publication ring cycle. An EVENT byte (4/6/7) publishes
 * nothing, so the ring never completes and the walk FREEZES on the event byte (proven). The route
 * from encounter-completion back to the next direction byte is a DOWNGRADED model (not proven) —
 * scene-init (the only pointer re-seed) is reached only from the config-driven level-start 0x045316;
 * no event-completion call path is traced. See map_stream_format.md §6. Value 7 has no established
 * consumer; 0xFF is a candidate sentinel, never loaded. Records 0-137 proven (120 len-1 + 18 len-2);
 * record 138 is a candidate [00 07].
 */

/* ---- ROM tables (see map_stream_format.md §1) ---- */
#define STAGE_TO_SEG   ((const u8 *)0x5073A)   /* [stage]   -> segment index          */
#define SEG_TO_OFFSET  ((const u8 *)0x50EE0)   /* [seg]     -> stream byte offset (139)*/
#define MAP_STREAM     ((const u8 *)0x50F6B)   /* [offset]  -> selector byte           */
#define SEG_TO_TM0IDX  ((const u8 *)0x507C5)   /* [seg]     -> tilemap0 index          */
static const u32 strip_src_table[16] = {       /* [i] + seg*0x40 -> a5@0x1000+i*4      */
    0x1691C,0x18BDC,0x1AE9C,0x1D15C,0x1F41C,0x216DC,0x2399C,0x25C5C,
    0x27F1C,0x2A1DC,0x2C49C,0x2E75C,0x30A1C,0x32CDC,0x34F9C,0x3725C };

/*
 * Arcade PC: 0x050248  — scene-init prologue (inside routine 0x0501E2; gated a5@0x13E2 != 1).
 * Stage -> segment index; segment -> tilemap0 index; reset ring/tilemap0 accumulators.
 */
static void map_scene_prologue(void)
{
    a5_w(0x13E) = STAGE_TO_SEG[a5_w(0x1242)];        /* 0x05025A: STAGE -> segment index      */

    /* 0x050260..0x050292: membership test of the segment index against word table 0x502AC
     * (terminated 0xFFFF). On match: d0=0x25; jsr 0x3A116 (sound); a5@0x12EE=0xFF; a5@0x1360=1.
     * No match: a5@0x1360=0xFF. (Gate only; not decoded per entry.) */

    a5_w(0x1386) = SEG_TO_TM0IDX[a5_w(0x13E)];       /* 0x0502A6: segment -> tilemap0 index   */
    /* 0x0502BE: */ a5_w(0x10F4) = 0; a5_w(0x10CA) = 0; a5_w(0x10F6) = 0;
}

/*
 * Arcade PC: 0x0502CC  — source-pointer + map-pointer selection. Called at 0x050202,
 * immediately before the scene fill (0x0503DC, called at 0x050206).
 */
static void map_select_pointers(void)
{
    u32 d1 = (u32)a5_w(0x13E) * 0x40;                        /* 0x0502D0..0x0502DA */
    for (int i = 0; i < 16; i++)                             /* 0x0502E4..0x050398 */
        a5_l(0x1000 + i*4) = strip_src_table[i] + d1;        /* 16 tilemap1 strip-source bases */

    a5_l(0x10FC) = 0x3951C + (u32)a5_w(0x1386) * 0x0C;       /* 0x0503B4: tilemap0 source base */

    /* 0x0503B8..0x0503D6: MAP-STREAM POINTER */
    u8 off = SEG_TO_OFFSET[a5_w(0x13E)];                     /* segment -> stream byte offset  */
    a5_l(0x10C6) = (u32)MAP_STREAM + off;                   /* 0x0503D6: a5@0x10C6            */
    /* rts 0x0503DA */
}

/*
 * Arcade PC: 0x055904  — descriptor rebuild (16 entries) that FALLS THROUGH into the
 * initial selector load at 0x055938. So calling 0x055904 both rebuilds the strip descriptors
 * AND loads the current selector a5@0x10A8 = *(byte)a5@0x10C6 (no pointer advance).
 */
static void map_rebuild_and_load_selector(void)
{
    /* 0x055904..0x055936: rebuild source/descriptor tables 0x10D040/0x10D080 from 0x10D000 */
    /* fall through: */
    const u8 *p = (const u8 *)a5_l(0x10C6);      /* 0x055938 */
    a5_w(0x10A8) = *p;                           /* 0x055940: load selector (no advance)     */
}

/*
 * Arcade PC: 0x0558A2  — post-publication advance. Called by the publish dispatch (0x055962)
 * after EACH publication. Ring counters gate source-pointer advance and map-byte advance.
 */
static void map_post_advance(void)
{
    if (a5_w(0x10CA) != 4) return;               /* 0x0558A2: 4 columns per group not done   */
    map_advance_source_ptrs();                   /* 0x0558C6                                  */
    map_rebuild_and_load_selector();             /* 0x055904 (rebuild + reload same selector) */
    a5_w(0x10CC) += 1;                           /* 0x0558B2: next group                     */
    if (a5_w(0x10CC) != 16) return;              /* 0x0558B6: 16 groups per ring cycle        */
    map_advance_byte();                          /* 0x0558E0: ring cycle done -> next selector*/
}

/*
 * Arcade PC: 0x0558C6  — advance the 16 strip-source base pointers by +4 (one column),
 * reset the column counter.
 */
static void map_advance_source_ptrs(void)
{
    u32 *base = (u32 *)0x10D000;
    for (int i = 16; i != 0; i--) { *base += 4; base += 1; }   /* 0x0558CE */
    a5_w(0x10CA) = 0;                                          /* 0x0558DA */
}

/*
 * Arcade PC: 0x0558E0  — one ring cycle finished (64 publications). Advance the map-stream
 * pointer by ONE byte and load the next selector. This is the ONLY per-byte advance.
 */
static void map_advance_byte(void)
{
    a5_w(0x10CC) = 0;                            /* 0x0558E0 */
    a5_l(0x10C6) += 1;                           /* 0x0558E4: advance stream pointer +1 byte */
    a5_w(0x132C) = a5_w(0x10A8);                 /* 0x0558EC: save PREVIOUS selector          */
    const u8 *p = (const u8 *)a5_l(0x10C6);      /* 0x0558F0 */
    a5_w(0x10A8) = *p;                           /* 0x0558F8: NEW selector = next stream byte */
    a5_w(0x13E) += 1;                            /* 0x0558FE: segment counter++               */
}

/*
 * Arcade PC: 0x0557C4 / 0x0556A6 / 0x055738 / 0x055854 — per-frame direction dispatcher.
 * Matches selector 0/1/2 (+ a 4th path); a non-matching selector latches a pending bit in
 * a5@0x10D0 and publishes nothing. (Full facts: gameplay_control.c.)
 */
static void map_direction_dispatch(void)
{
    switch (a5_w(0x10A8)) {
    case 0: /* horizontal   */ break;   /* 0x0557C4 -> strip_A on X crossings */
    case 1: /* vertical A    */ break;   /* 0x0556A6 -> strip_B on Y crossings */
    case 2: /* vertical B    */ break;   /* 0x055738 -> strip_B, flipped        */
    default:                             /* 3/4/5/6/7: latch pending bit, no publish */
        break;
    }
}

/*
 * Arcade PC: 0x05274C  — event selectors 4/5/6 (non-publication). No operand bytes; does NOT
 * touch a5@0x10C6 or a5@0x13E. Sets a5@0x10E8 = 7 (enables the event/spawn engine) then runs
 * scene logic. A second, position-gated handler at 0x05127C sets event flags for 4 (a5@0x10BE>=0xD8
 * -> a5@0x1376/0x1384/0x13C6 = 1) and 5 (a5@0x10BE>=0x50).
 *
 * Because 4/5/6 publish nothing, 0x0558E0 never fires while one is the selector: the walk is FROZEN
 * on the event byte (proven). How play then reaches the next direction byte is a DOWNGRADED model,
 * not proven: a5@0x10C6's only re-seed is scene-init (0x0503D6), whose routine 0x0501E2 has ONE
 * caller — 0x045316 — where the stage a5@0x1242 is computed from a config word, NOT from an
 * event-completion increment. No event->0x045316 call path is traced. The correlation supports the
 * model (every event boundary is a stage boundary; the seg-LUT +2 delta skips the event byte on a
 * re-seed), but the exact "encounter done -> pointer re-seed" route is UNRESOLVED (level-progression
 * / enemy subsystem, out of scope). See map_stream_format.md §6.
 *
 * Selector 7: a5@0x10A8 is only compared against 0/1/2/4/5/6 and copied to 0x132C — no consumer
 * established for 7. Selector 3 and 0xFF likewise have no consumer.
 */
static void map_event_selector(void)
{
    if (a5_w(0x10A8) == 4 || a5_w(0x10A8) == 5 || a5_w(0x10A8) == 6) {
        a5_w(0x10E8) = 7;                        /* 0x0527CC (then falls into scene/enemy logic) */
    }
    /* freeze persists until the scene/enemy engine completes and the stage re-seed advances. */
}
