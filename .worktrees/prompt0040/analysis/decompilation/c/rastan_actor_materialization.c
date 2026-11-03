/* rastan_actor_materialization.c — CHECKPOINT H6
 * Semantic reconstruction of the ORIGINAL ARCADE marker -> state -> actor materialization
 * subsystem (state 0x00, PC 0x4117E..0x41D07) plus the two marker-chain transform states
 * (0x40E88 state 0x1E, 0x40EDE state 0x20) that assign the visible base +0x1E and retarget +0x0D.
 *
 * NOT original Taito source. Derived from build/regions/maincpu.bin + build/maincpu.disasm.txt.
 * Byte-faithful control flow lives in raw/00041180.c, raw/00040e88.c, raw/00040ede.c,
 * raw/0004103a.c, raw/00045418.c, raw/00041bee.c; this layer names the architecture.
 *
 * ARCHITECTURE (proven H6):
 *   latent hunter (state 0, base 0x033E, off-screen Y=0x180)
 *     -> timer gate (+0x1C) every 2 frames
 *     -> collision-map marker scan (0x41064 row-scan when armed; 0x4127E column-scan otherwise)
 *     -> marker char matched against +0x0D (hunter) or floor class 0x31..0x3C (mode==0)
 *     -> HUNTER: 0x41362 stores matched cell ADDRESS into +0x0E, then a 26-way char dispatch
 *        assigns state (+0x05) + anim (+0x01) + attr (+0x29); most branches DO NOT set base +0x1E.
 *        The visible base is assigned later by the state handler / retarget chain.
 *     -> FLOOR (mode==0): state = class(+0x04)+1, 0x41336 places X, 0x40A06 transition table.
 *     -> tail 0x41332 = braw 0x40BAA: re-dispatch with the new state THIS frame.
 */
#include "rastan_arcade_types.h"

/* ---- externs into other reconstructed subsystems ---- */
extern uint32_t collision_cell_addr(uint16_t x, uint16_t y);   /* 0x53A2E */
extern uint16_t collision_marker(uint32_t cell);               /* word[cell]>>8 */
extern int      hunter_row_scan(ActorRecord *a);               /* 0x41064: 1 if +0x0D found */
extern void     floor_transition(ActorRecord *a);              /* 0x40A06 -> 0x40A60 table */
extern void     load_state_attr(ActorRecord *a);               /* 0x45418: +0x29 = tbl[state-0x13] */
extern void     dispatch_actor(ActorRecord *a);                /* 0x40BAA */
extern void     spawn_linked_object(int parts);                /* 0x43F52 / 0x43F4E */
extern void     spawn_subactor(ActorRecord *a);                /* 0x4354E */
extern void     play_sfx(uint8_t id);                          /* 0x3A0EC */
extern void     copy_template(ActorRecord *dst, int words);    /* 0x3A2D0 from A5+0x588 */
extern void     retire_or_step(ActorRecord *a);                /* 0x4092E (H7) */
extern void     register_light_source(ActorRecord *a);         /* 0x41BEE */
extern int      marker_recheck(ActorRecord *a);                /* 0x40E74: 1 if marker gone */
extern void     consume_and_rearm(ActorRecord *a);             /* 0x4103A */

/* scan scratch (A5+0x214..0x226) */
extern uint16_t g_scan_x, g_scan_y, g_scan_budget, g_scan_found, g_scan_occ;
extern uint32_t g_scan_cell;
extern uint16_t g_prog, g_cam_y_hi, g_scr10cc, g_scrfine_x, g_scrfine_y;
extern uint8_t  g_round;

/* =====================================================================================
 * marker character -> materialized STATE, keyed by the 0x41362/0x41414 dispatch.
 * (base +0x1E is set later unless noted; see materialize_char below.)
 * ===================================================================================== */
typedef struct { uint8_t lo, hi; uint8_t state; const char *note; } MarkerBand;

/* The exact dispatch order/handlers (see raw/00041180.c materialize_41362 + dispatch_low_41414).
 * state 0x40 = record-type-1 projectile ('I'); state 0xFF here = "no route". */
static const MarkerBand k_bands[] = {
    {0x31,0x44, 0x1D, "<'E' -> 0x41A48"},
    {0x45,0x45, 0x18, "'E'  -> 0x41834"},
    {0x46,0x46, 0x1D, "'F'  -> 0x41A48"},
    {0x47,0x47, 0x1C, "'G'  -> 0x41A14"},
    {0x48,0x48, 0x1E, "'H'  -> 0x41B6C"},
    {0x49,0x49, 0x40, "'I'  -> 0x41B32 rec_type=1 projectile"},
    {0x4b,0x4b, 0x19, "'K'  -> 0x418A2"},
    {0x4c,0x4c, 0x1A, "'L'  -> 0x418F4"},
    {0x4d,0x4d, 0x1B, "'M'  -> 0x419E0"},
    {0x4f,0x51, 0x20, "'O'..'Q' -> 0x41BCA torch/light"},
    {0x52,0x56, 0x1A, "'R'..'V' -> 0x418F4"},
    {0x57,0x58, 0x19, "'W','X'  -> 0x418A2"},
    {0x59,0x5d, 0x17, "'Y'..']' -> 0x417D2"},
    {0x5e,0x60, 0x16, "'^','_','`' -> 0x41792"},
    {0x61,0x63, 0x15, "'a','b','c' -> 0x416B2"},
    {0x64,0x64, 0x14, "'d'  -> 0x4167E"},
    {0x65,0x66, 0x13, "'e','f' -> 0x41614"},
    {0x67,0x69, 0x1A, "'g','h','i' -> 0x41596"},
    {0x6a,0x6b, 0x18, "'j','k' -> 0x41834"},
    {0x6c,0x6d, 0x1D, "'l','m' -> 0x41A48"},
    {0x6e,0x70, 0x15, "'n','o','p' -> 0x416B2"},
    {0x71,0x72, 0x21, "'q','r' -> 0x414D4"},
    {0x73,0x75, 0x22, "'s','t','u' -> 0x4145A"},
    {0x76,0x77, 0x1A, "'v','w' -> 0x41596"},
    {0x78,0x78, 0x21, "'x'  -> 0x414D4"},
    {0x79,0x79, 0x22, "'y'  -> 0x4145A"},
    {0x7a,0x7a, 0x15, "'z'  -> 0x416B2"},
    {0x7b,0x7b, 0x21, "'{'  -> 0x414D4"},
};

uint8_t marker_to_state(uint8_t ch){
    for (unsigned i=0;i<sizeof k_bands/sizeof*k_bands;i++)
        if (ch>=k_bands[i].lo && ch<=k_bands[i].hi) return k_bands[i].state;
    return 0xFF;                                     /* >= '|' : no route */
}

/* =====================================================================================
 * 0x41362 character-hunter materialization. Stores cell ADDRESS in +0x0E, assigns state.
 * Position math and per-progress linked-object spawns are in raw/00041180.c (faithful).
 * ===================================================================================== */
void materialize_char(ActorRecord *a, uint8_t ch, uint32_t cell){
    if (ch != a->target_char) return;                /* every branch guards d0==+0x0D */
    a->field_0e[0]=(uint8_t)(cell>>24); a->field_0e[1]=(uint8_t)(cell>>16);
    a->field_0e[2]=(uint8_t)(cell>>8);  a->field_0e[3]=(uint8_t)cell;  /* +0x0E = cell address (movel) */
    a->init_flag = 1; a->anim_frame_cd = 1;

    uint8_t st = marker_to_state(ch);
    if (st == 0xFF) return;
    if (st == 0x40){                                  /* 'I' projectile: full record from template */
        a->rec_type = 1;
        copy_template(a, 32);
        retire_or_step(a);
        return;
    }
    a->state = st;
    /* anim (+0x01) and position are branch-specific (raw). Attr (+0x29) via 0x45418 for the
     * branches that call it; state 0x1B/0x1C/0x1E/0x20 set anim directly without 0x45418. */
    if (st!=0x1B && st!=0x1C && st!=0x1E && st!=0x20) load_state_attr(a);
    if (st==0x20) register_light_source(a);           /* torch */
}

/* =====================================================================================
 * state 0x00 main (0x41180): timer -> scan -> materialize / floor-follow.
 * ===================================================================================== */
void actor_state0_scanner(ActorRecord *a){
    if (--a->timer != 0) return;                      /* 0x41180 */
    a->timer = 2;

    if (hunter_row_scan(a)){                           /* armed hunter found +0x0D in its row */
        materialize_char(a, (uint8_t)g_scan_found, g_scan_cell);
        dispatch_actor(a); return;                     /* 0x41332 */
    }
    if (a->mode != 0 && a->field_30 != 0) return;   /* still hunting: wait next frame */

    /* progression gates before the column scan */
    if (a->mode==0 && g_prog==133 && g_scr10cc>=1) return;
    if (g_prog==110 && g_scr10cc>=13) return;

    /* seed + column scan (0x4127E). Detailed position math in raw. */
    /* ... see raw/00041180.c: vertical scan for floor marker 0x31..0x3C (mode==0) or +0x0D. */
    uint16_t x=g_scan_x, y=(uint16_t)(g_scan_y & 0x1ff);
    uint32_t cell = collision_cell_addr(x,y);
    for(;;){
        uint8_t ch = (uint8_t)(collision_marker(cell)>>0);
        int found = (ch>=0x35) &&
                    ((a->mode==0) ? (ch<0x3d) : (ch==a->target_char));
        if (found) break;
        if (a->mode==0 && g_cam_y_hi>=176){ cell-=0x80; if(cell<0x0010de00u) cell+=0x2000; }
        else                                 { cell+=0x80; if(cell>=0x0010fe00u) cell-=0x2000; }
        if (--g_scan_budget==0) return;
    }
    uint8_t ch = (uint8_t)collision_marker(cell);
    if (a->mode != 0){                              /* hunter via column scan */
        materialize_char(a, ch, cell);
        dispatch_actor(a); return;
    }
    a->state = (uint8_t)(a->klass + 1);             /* floor follower: state = class+1 */
    floor_transition(a);
    dispatch_actor(a);
}

/* =====================================================================================
 * marker-chain TRANSFORM states (assign visible base +0x1E, retarget +0x0D).
 * ===================================================================================== */
/* 0x40E88 state 0x1E: when the tracked marker vanishes, advance the chain by progress band. */
void actor_state1e_transform(ActorRecord *a){
    if (marker_recheck(a)==0) return;                  /* marker still present: stay */
    if (g_prog < 0x18){ consume_and_rearm(a); a->base=0x00f4; a->target_char=0x4f; return; }
    if (g_prog < 0x2f){ retire_or_step(a); spawn_linked_object(5); return; }
    retire_or_step(a);
}

/* 0x40EDE state 0x20 torch: register light, animate; on marker-gone advance the base/target chain
 *   prog<0x10 -> base 0xDAB target 'I'; 0x18..0x26 -> base 0x9EA target 'a';
 *   0x4E..0x53 -> base 0x9EA target 'q' comp=2; other bands -> step. (raw/00040ede.c) */
void actor_state20_torch(ActorRecord *a){ (void)a; /* see raw/00040ede.c for exact bands */ }
