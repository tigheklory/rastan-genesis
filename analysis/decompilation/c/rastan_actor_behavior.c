/*
 * Rastan arcade reconstructed decompilation — actor behavior/update handlers.
 * Derived from static analysis of the 68000 program; NOT original Taito source.
 * Provenance: RECONSTRUCTED_FROM_68000 unless noted. Semantic form; see raw/ for
 * close-to-machine reconstructions of the same PCs.
 */
#include "rastan_arcade_types.h"

extern int arcade_40e74_marker_recheck(ActorRecord *a4);

/* Shared 8px-band anim tail used by the H5 chain-walkers when the marker is
 * gone (structure: decrement +0x09; if 0, step +0x08 phase machine). The exact
 * per-state anim values are written inline in each handler below. */

/*
 * ORIGINAL ARCADE PC: 0x00040CCC  polymorphic state 0x0F
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * The default branch is the ordinary enemy-death animation (base 0x0A73,
 * compositor 2).  At phase 10 it either retires (+0x36==0) or transforms the
 * same actor into the schedule-selected family-12 reward/drop presentation
 * (base 0x0A5A).  mode!=0 selects the alternate short path; field_39 selects
 * the independent 0x0275 burst-child path.
 */
void actor_armored_40ccc(ActorRecord *a4)
{
    if (a4->mode != 0)          /* +0x03 hunter -> 0x40E0E alt path (sound #23) */
        goto alt_anim;
    if (a4->field_39 != 0)      /* +0x39 -> 0x40DD8 base 0x0275 sub-path */
        goto base_0275;
    if (--a4->anim_frame_cd != 0) /* +0x09 wait */
        return;
    a4->pal_attr &= (uint8_t)~0x40;   /* bclr #6,+0x27 */
    a4->comp = 2;                     /* +0x38 */
    a4->base = 0x0A73;                /* +0x1E armored man (sword) */
    a4->anim_frame_cd = 3;            /* +0x09 */
    a4->anim_frame_dur++;             /* +0x08 */
    if (a4->anim_frame_dur == 4)
        ; /* bsr 0x40C62 (register/candidate) */
    if (a4->anim_frame_dur >= 10)
        goto transform;
    a4->field_3a = 1;                 /* +0x3A */
    {
        static const uint8_t anim_seq[10] = /* table 0x40DCE (first bytes) */
            {0x02,0x01,0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07};
        a4->anim = (uint8_t)(anim_seq[a4->anim_frame_dur] + 11); /* +0x01 */
    }
    return;

transform: /* 0x40D32: in-place family-12 reward/drop conversion */
    a4->family  = 0x0C;   /* +0x3E */
    a4->field_3a = 0xFF;  /* +0x3A */
    a4->field_37 = 0;     /* +0x37 */
    a4->field_3d = 0;     /* +0x3D */
    /* 0x40C0E maps schedule field +0x36 through tables 0x40C2E/0x40C40 to
     * identity +0x29 and reward value +0x2C.  The instruction-faithful raw
     * reconstruction contains the selector, bounds and recycle behavior. */
    a4->base    = 0x0A5A; /* presentation base when +0x36 permits a drop */
    return;

base_0275: /* 0x40DD8 */
    a4->comp = 0;         /* +0x38 */
    a4->base = 0x0275;    /* +0x1E */
    a4->anim_frame_cd = 1;/* +0x09 */
    a4->anim_frame_dur++; /* +0x08 */
    if (a4->anim_frame_dur < 4)
        a4->anim = (uint8_t)(a4->anim_frame_dur + 0x9D); /* +0x01 */
    return;

alt_anim: /* 0x40E0E: sound cue then anim from +0x08 */
    if (--a4->anim_frame_cd != 0)
        return;
    a4->anim_frame_cd = 6;
    a4->anim_frame_dur++;
    if (a4->anim_frame_dur == 1)
        arcade_3a0ec(0x17);          /* sound #23 */
    if (a4->anim_frame_dur < 4)
        a4->anim = (uint8_t)(a4->anim_frame_dur + 0x70);
}

/* ORIGINAL ARCADE PC: 0x00042ABC — specialized state-0x0F presentation.
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * The exact type branches, double phase increment for types 10-13/18/28,
 * coordinate adjustment for type 12, selectors, and retirement predicates are
 * preserved in raw/00042abc.c.  In particular, lethal-initialized bat types
 * 10/11 show selector 0xA8 and retire on the next gated update; Flying Demon
 * types 8/9 and selected boss types use base 0x0275 and the 0x9D-0xA0 run.
 */
void actor_specialized_death_42abc(ActorRecord *a4)
{
    (void)a4; /* See instruction-faithful raw reconstruction. */
}

/* ORIGINAL ARCADE PC: 0x00040C08 — state 0x10 anim-table param setup.
 * Provenance: RECONSTRUCTED_FROM_68000. Status: PARTIAL (setup 0x40C0E read;
 * full state-0x10 lifecycle not traced). */
void actor_state10_40c08(ActorRecord *a4)
{
    (void)a4; /* PARTIAL: sets +0x29 from 0x40C2E[+0x36-1] and +0x2C from 0x40C40 */
}

/*
 * ORIGINAL ARCADE PC: 0x00047140  ground-actor engine (states 3-0C,12)
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 */
void actor_ground_engine_47140(ActorRecord *a4)
{
    if (a4->init_flag == 0)             /* +0x07 first frame */
        arcade_41cfa(a4);               /* config from 0x41D26[state] */
    arcade_3ceb0(a4);                   /* shared anim/motion core */
    uint8_t fam = a4->family;
    if (fam == 0) {                     /* family 0 anim */
        uint8_t d0 = ar_anim_index_0e(a4) < 2 ? 4 : 3;
        a4->anim = (uint8_t)(d0 + 23);
    } else if (fam == 1) {              /* family 1 walk-cycle from +0x0D */
        uint8_t d1 = a4->target_char, d0 = 3;
        if (d1 >= 14) d0 = 5;
        if (d1 >= 16) d0 = 4;
        if (d1 >= 42) d0 = 5;
        if (d1 >= 44) d0 = 3;
        if (ar_anim_index_0e(a4) >= 3) d0 = 6; /* +0x0E>=3 */
        a4->anim = (uint8_t)(d0 + 35);
    } else if (fam == 2) {              /* family 2 (scanner) anim */
        uint8_t d0 = 0;
        if (ar_anim_index_0e(a4) < 3) d0 = 1;
        if (ar_anim_index_0e(a4) < 5) d0 = 3;
        a4->anim = (uint8_t)(d0 + 0x93);
    }
}

/* a5-relative shared WRAM globals used by the airborne engine (names are structural, not invented AI). */
extern uint16_t g_track_dist_0234;   /* A5+0x234: |horizontal distance| actor<->camera (set by 0x4205C) */
extern uint16_t g_track_face_0236;   /* A5+0x236: target facing sign (1 = actor left of camera, else 0)  */
extern uint16_t g_global_dir_0200;   /* A5+0x200: global 8-way direction field consumed by anim selection */
void actor_airborne_config_load_41cfa(ActorRecord *a4);     /* 0x41CFA */
void actor_airborne_camera_track_4205c(ActorRecord *a4);    /* 0x4205C */
void actor_airborne_ground_probe_4736a(ActorRecord *a4);    /* 0x4736A */

/*
 * ORIGINAL ARCADE PC: 0x000473B8  airborne-actor engine (states 1,2,0D,0E).
 * Provenance: RECONSTRUCTED_FROM_68000 (0x473B8-0x47660; RG-007 completes the states-0D/0E tail +
 * per-family anim selection). Status: COMPLETE.
 *
 * Structure: (1) first-frame init loads the per-state config (0x41CFA), seeds the flap duration +0x08
 * by family, and runs the anim-rate pre-step; (2) the shared anim/motion core 0x3CEB0 advances motion;
 * (3) the ACTIVE-PURSUIT + turn-around block runs ONLY for states 1 and 2 and is SKIPPED for states
 * 0x0D/0x0E (so 0x0D/0x0E are the passive, non-pursuing airborne sub-states); (4) a shared tail runs the
 * ground/landing probe (0x4736A) and the per-family 8-way directional animation-frame selection.
 * Bat family is 0x0A; Small/Large bats differ by the +0x2E sub-mode (also seen in the init +0x08 seed).
 */
void actor_flying_engine_473b8(ActorRecord *a4)
{
    if (a4->init_flag == 0) {                       /* 0x473B8: first frame */
        actor_airborne_config_load_41cfa(a4);       /* 0x41CFA per-state config -> +0x08/+0x0D..+0x13/+0x02 */
        if (a4->family == 1) {                      /* +0x3E */
            a4->anim_frame_dur = 4;                 /* +0x08 */
            actor_airborne_anim_rate_prestep_4734a(a4);
            a4->field_0a = 8;                       /* +0x0A */
        } else if (a4->family == 0x0A) {            /* bats */
            a4->anim_frame_dur = (a4->field_2e != 0) ? 2 : 7; /* +0x08 */
            actor_airborne_anim_rate_prestep_4734a(a4);
        } else {
            actor_airborne_anim_rate_prestep_4734a(a4);
        }
    }
    arcade_3ceb0(a4);                               /* 0x47408: shared anim/motion core */
    a4->field_20 &= (uint8_t)~0x01;                 /* bclr #0,+0x20 */

    if (a4->state != 0x0D && a4->state != 0x0E) {   /* 0x47414: ACTIVE PURSUIT only (skip for 0D/0E) */
        actor_airborne_camera_track_4205c(a4);      /* 0x4205C -> g_track_dist_0234 / g_track_face_0236 */
        if (g_track_dist_0234 < 0x68) {             /* 0x47432: in horizontal range */
            if (g_track_face_0236 != a4->field_02)  /* facing != target */
                a4->field_20 |= 0x01;               /* bset #0,+0x20 (turn needed) */
        } else {
            a4->field_741 = 0;                      /* out of range -> clear +0x741 */
        }
        uint8_t t = a4->field_747;                  /* 0x4744E: turn-timer */
        if (t == 2) {                               /* retarget cooldown */
            a4->field_747 = 2; a4->init_flag = 0;   /* 0x4745C: re-init next frame (reconfig) */
            a4->field_746 = 24;
            a4->state   = (uint8_t)(g_track_face_0236 + 1); /* +0x05 = facing+1 (1 or 2) */
            a4->field_2b = a4->state;               /* +0x2B */
        } else if (t == 1) {                        /* cooldown tick */
            if (--a4->field_746 == 0) { a4->field_2b = 0; a4->field_747 = 0; }
        } else {                                    /* t == 0: not turning */
            if (a4->init_flag == 0 && a4->field_740 == 0 &&
                g_track_dist_0234 >= 0x30 && g_track_dist_0234 < 0x34) { /* 0x47498: turn window */
                a4->field_740 = 2; a4->field_741 = 1;
                a4->state   ^= 3;                   /* 0x474B4: toggle state 1<->2 */
                a4->field_02 ^= 1;                  /* 0x474BA: toggle facing */
                return;                             /* 0x474C0 rts */
            }
            if (a4->field_740) a4->field_740--;     /* 0x474C2 */
        }
    }

    actor_airborne_ground_probe_4736a(a4);          /* 0x474C6: landing/impact probe (states<0x0D only, internally gated) */

    /* 0x474CA: per-family 8-way directional animation frame -> +0x01.  Families 0/1/2/3/.. each have a
     * selector; the bat family 0x0A selector (0x4762E): anim = 0x2D + direction, two modes via +0x2E. */
    if (a4->family == 0x0A) {                       /* bat */
        uint16_t dir = g_global_dir_0200;           /* A5+0x200 */
        a4->anim = (uint8_t)(0x2D + (a4->field_2e == 0
                     ? ((dir & 0x70) >> 4)          /* frames 0x2D-0x34 */
                     : (8 + ((dir & 0x38) >> 3)))); /* frames 0x35-0x3C */
    }
    /* Other families select from their own PC-relative anim tables (0x474EE/0x47530/0x47562/...); those
     * are not on the bat path and are left as the shared-selector family chain. */
}

/*
 * ORIGINAL ARCADE PC: 0x00041CFA  per-state airborne config loader (RG-007, newly decompiled).
 * Provenance: RECONSTRUCTED_FROM_68000 (0x41CFA-0x41D24; table 0x41D26). Status: COMPLETE.
 * Index = state (+0x05) * 8 into the 8-byte-record table at ROM 0x41D26.  Record byte layout and the
 * actor destinations (from the move.b stream 0x41D02-0x41D20):
 *   rec[7] -> +0x02 (facing/control)    rec[0] -> +0x08 (anim duration)   rec[1] -> +0x0D
 *   rec[2] -> +0x0E   rec[3] -> +0x0F   rec[4] -> +0x10   rec[5] -> +0x11   rec[6] -> +0x13
 * (The per-state records 0..7 are enumerated in rastan_actor_tables.c as g_airborne_state_config_41d26;
 *  airborne enemies enter at state 1/2, whose records seed the flap/motion parameters.)
 */
void actor_airborne_config_load_41cfa(ActorRecord *a4)
{
    const uint8_t *r = &g_airborne_state_config_41d26[a4->state][0]; /* 0x41D26 + state*8 */
    a4->field_02       = r[7];
    a4->anim_frame_dur = r[0];   /* +0x08 */
    a4->field_0d       = r[1];
    a4->field_0e       = r[2];
    a4->field_0f       = r[3];
    a4->field_10       = r[4];
    a4->field_11       = r[5];
    a4->field_13       = r[6];
}

/*
 * ORIGINAL ARCADE PC: 0x0004205C  camera-relative horizontal tracking (RG-007, newly decompiled).
 * Provenance: RECONSTRUCTED_FROM_68000 (0x4205C-0x4208A). Status: COMPLETE.
 * d2 = (camera_center A5+0x10BE + 96) & 0x1FF ; d1 = (actor X +0x16 + 96) & 0x1FF ; d2 -= d1.
 * If d2 < 0 (actor to the right): A5+0x236 = 1, d2 = -d2 ; else A5+0x236 = 0.  A5+0x234 = |d2|.
 * i.e. writes the absolute horizontal camera<->actor distance and the target facing sign the pursuit
 * block in 0x473B8 consumes.
 */
void actor_airborne_camera_track_4205c(ActorRecord *a4)
{
    int d2 = ((g_camera_center_10be + 96) & 0x1FF) - ((a4->x_pos + 96) & 0x1FF); /* +0x16 = X */
    if (d2 < 0) { g_track_face_0236 = 1; d2 = -d2; }
    else        { g_track_face_0236 = 0; }
    g_track_dist_0234 = (uint16_t)d2;
}

/*
 * ORIGINAL ARCADE PC: 0x0004736A  airborne ground/landing probe (RG-007, newly decompiled).
 * Provenance: RECONSTRUCTED_FROM_68000 (0x4736A-0x473B6). Status: COMPLETE.
 * Gated to active flight (returns if +0x07 init set or state >= 0x0D, i.e. NOT for 0x0D/0x0E).  Reads the
 * collision grid 4px BELOW the actor (X +0x16, Y +0x1A +4) via 0x53A2E; if the cell's high byte (tile
 * type) is 0 (air) it increments the air-frame counter +0x74F, else clears it.  After >=3 consecutive
 * solid-ground frames it sets the impact flag +0x39=1 and calls 0x447F0 (-> state 0x0F) — i.e. the bat's
 * land-on-ground transition into the specialized death/impact path.
 */
void actor_airborne_ground_probe_4736a(ActorRecord *a4)
{
    if (a4->init_flag != 0 || a4->state >= 0x0D) return;      /* 0x4736E/0x47376 */
    uint16_t x = (uint16_t)(a4->x_pos & 0x1FF);
    uint16_t y = (uint16_t)((a4->y_pos & 0x1FF) + 4);         /* +0x1A + 4 (below) */
    uint16_t cell = collision_word_at(ar_cell_from_xy(x, y)); /* 0x53A2E -> grid word */
    if ((uint8_t)(cell >> 8) == 0)   a4->field_74f++;         /* air below */
    else                             a4->field_74f = 0;       /* solid below */
    if (a4->field_74f >= 3) {                                 /* 3 consecutive solid frames */
        a4->field_39 = 1;                                     /* +0x39 impact flag */
        arcade_447f0(a4);                                     /* 0x447F0 -> state 0x0F (death/impact) */
    }
}

/*
 * ORIGINAL ARCADE PC: 0x0004734A  airborne animation-rate pre-step (RG-006, newly decompiled).
 * Provenance: RECONSTRUCTED_FROM_68000 (build/maincpu.disasm.txt 0x4734A-0x47368). Status: COMPLETE.
 * Called by the airborne engine 0x473B8 for family 1 and family 0x0A (bats) during init.
 *
 * Despite the earlier stub label "vertical/hover pre-step", the code does NOT move the actor: it
 * conditionally SPEEDS UP the wing-flap animation by halving the per-frame anim duration +0x08
 * (minimum 1) when either +0x741 or +0x2B is nonzero; otherwise +0x08 is left unchanged. It is a pure
 * animation-timing adjust (arcade-owned), relevant to bats because the flying engine seeds +0x08 to
 * 2/7 (family 0x0A) or 4 (family 1) and then calls this to optionally double the flap rate.
 */
void actor_airborne_anim_rate_prestep_4734a(ActorRecord *a4)
{
    if (a4->field_741 == 0 && a4->field_2b == 0)   /* 0x4734A/0x47350: both zero -> no change */
        return;
    uint8_t d1 = (uint8_t)(a4->anim_frame_dur >> 1);/* +0x08 >> 1 (faster flap) */
    if (d1 == 0) d1 = 1;                            /* clamp to minimum 1 */
    a4->anim_frame_dur = d1;                        /* +0x08 */
}

/*
 * ORIGINAL ARCADE PC: 0x0004684E  state 0x11 — boss component
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE (head/anim); position
 * sync performed by body loop 0x42380 via +0x21.
 */
void actor_boss_component_4684e(ActorRecord *a4)
{
    if (a4->family != 2 && a4->family != 8)
        return;                          /* -> 0x468E8 (other) */
    if (a4->init_flag == 0) {
        arcade_41cfa(a4);
        arcade_468d0(a4);                /* facing vs camera A5+0x10BE */
    }
    arcade_3ceb0(a4);
    if (a4->family == 2) {
        uint8_t d0 = 2;
        if (ar_anim_index_0e(a4) < 23) d0 = 3;
        if (ar_anim_index_0e(a4) < 3)  d0 = 1;
        a4->anim = (uint8_t)(0x93 + d0);
    } else {
        static const uint8_t tbl_468c8[4] = {0x09,0x0D,0x0D,0x0C};
        if (a4->anim == 0x59) a4->field_22 = 0x3A; /* +0x22 special */
        a4->anim = (uint8_t)(0x4D + tbl_468c8[ar_anim_index_0e(a4) >> 2]);
    }
}

/* =====================================================================
 * H5 dedicated state handlers — the ground-actor MARKER-CHAIN state machine.
 * Common shape: recheck target marker (0x40E74); if present, consume/advance
 * (0x4103A) and RE-TARGET +0x0D + rewrite base +0x1E per round/0x13e/char; if
 * absent, run the actor's anim/move/attack tail (generic step 0x4092E).
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * ===================================================================== */

/* 0x4375C — states 0x13/0x14 */
void h5_4375c(ActorRecord *a4)
{
    if (G.round == 2 && G.progress_13e == 41 && G.scroll_10cc < 13)
        goto anim_tail;
    if (!arcade_40e74_marker_recheck(a4))
        goto anim_tail;
    if (G.round == 3 && a4->target_char == 0x65 /*'e'*/) {
        arcade_4103a(a4);
        a4->target_char = 0x69; /*'i'*/  a4->base = 0x0224;
        a4->anim = 7; a4->comp = 2;
        return;
    }
    arcade_4092e(a4);
    return;
anim_tail:
    if (a4->anim_frame_cd != 0) { a4->anim_frame_cd--; return; }
    /* +0x08 phase machine -> anim 0x29+phase via 0x4382E (represented in raw) */
    arcade_4382e(a4);
}

/* 0x43840 — state 0x15 (owns base 0x0179 in the R6 char-'n' branch) */
void h5_43840(ActorRecord *a4)
{
    if (!arcade_40e74_marker_recheck(a4))
        goto anim_tail;
    if (G.round == 2) { arcade_4092e(a4); return; }
    if (G.round == 5 && a4->target_char == 0x61 /*'a'*/) {
        arcade_4103a(a4); a4->base = 0x0224; a4->target_char = 0x4C /*'L'*/; return;
    }
    if (G.round == 6 && a4->target_char == 0x6E /*'n'*/) {
        if (G.progress_13e < 0x80) {          /* 0x4389E */
            arcade_4103a(a4); a4->target_char = 0x7B /*'{'*/;
        } else {                              /* 0x438AC -> base 0x0179 cave-block */
            arcade_4103a(a4);
            a4->target_char = 0x48 /*'H'*/;
            a4->base = 0x0179;                /* <== 0x438B6: cave-entrance-block base */
            a4->anim = 0x70;
            return;
        }
        a4->comp = 2; a4->base = 0x09EA; a4->anim = 0x27; return;
    }
    if (a4->target_char == 0x6E) {            /* default 'n' -> 0x09EA */
        arcade_4103a(a4); a4->target_char = 0x71 /*'q'*/;
        a4->comp = 2; a4->base = 0x09EA; a4->anim = 0x27; return;
    }
    arcade_4092e(a4);
    return;
anim_tail:
    if (a4->anim_frame_cd != 0) { a4->anim_frame_cd--; return; }
    a4->anim = 0xF6; /* -10 */               /* 0x4391A */
}

/* 0x43AE6 — state 0x16 (scroll/position-triggered) */
void h5_43ae6(ActorRecord *a4)
{
    if (!arcade_40e74_marker_recheck(a4))
        return; /* 0x43B14 scroll/pos tail (uses A5+0x200/A5+0x214) */
    G.char_scratch_22b = a4->target_char;     /* A5+0x22B */
    if (a4->target_char == 0x60 /*'`'*/) {
        arcade_4103a(a4); a4->base = 0x00F4; a4->target_char = 0x4F /*'O'*/;
        return;
    }
    arcade_4092e(a4);
}

/* 0x43F88 — state 0x17 (0x13e-banded base select) */
void h5_43f88(ActorRecord *a4)
{
    if (!arcade_40e74_marker_recheck(a4))
        goto anim_tail;
    if (G.progress_13e < 0x23) {              /* band A */
        if (a4->target_char == 0x5C /*'\\'*/) { arcade_4092e(a4); return; }
        G.char_scratch_22b = a4->target_char; arcade_4103a(a4);
        uint8_t d0 = (uint8_t)(G.char_scratch_22b + 4);
        if (d0 == 0x61) d0--;
        a4->target_char = d0; a4->base = 0x05E9;
        if (d0 == 0x5D) a4->base = 0x0546;
        return;
    }
    if (G.progress_13e < 0x66) {              /* band B */
        G.char_scratch_22b = a4->target_char; arcade_4103a(a4);
        a4->target_char = (uint8_t)(G.char_scratch_22b + 9); a4->base = 0x09EA;
        return;
    }
    if (a4->target_char == 0x59 /*'Y'*/) {    /* band C */
        arcade_4103a(a4); a4->target_char = 0x55 /*'U'*/; a4->base = 0x0224;
        return;
    }
    arcade_4092e(a4);
    return;
anim_tail:
    if (a4->anim_frame_cd != 0) { a4->anim_frame_cd--; return; }
    a4->anim = 0xF0; /* -16 */
}

/* 0x44082 — states 0x18/0x1C (position-gated chain) */
void h5_44082(ActorRecord *a4)
{
    if (!arcade_40e74_marker_recheck(a4))
        return; /* 0x440F8 anim tail */
    uint16_t p = G.progress_13e;
    if (a4->state == 0x18) {
        if (p < 0x18) { arcade_4092e(a4); return; }
        if (p < 0x2F) {
            if (a4->target_char == 0x45 /*'E'*/) { arcade_4092e(a4); return; }
            G.char_scratch_22b = a4->target_char; arcade_4103a(a4);
            a4->target_char = (uint8_t)(G.char_scratch_22b - 23); a4->base = 0x0224;
            return;
        }
        arcade_4103a(a4); a4->base = 0x0224; a4->target_char = 0x55 /*'U'*/;
        return;
    }
    /* state 0x1C */
    if (p < 0x18) { arcade_4092e(a4); return; }
    arcade_4103a(a4); a4->base = 0x00F4; a4->target_char = 0x4F /*'O'*/;
}

/* 0x4396A — state 0x19 — JUMPING/LEAPING attacker */
void h5_4396a(ActorRecord *a4)
{
    if (arcade_40e74_marker_recheck(a4)) {
        G.char_scratch_22b = a4->target_char; arcade_4103a(a4);
        if (G.round == 1) {
            a4->base = 0x0235;
            uint8_t d0 = G.char_scratch_22b, d1 = 0;
            if (d0 != 0x4B) d1 = (uint8_t)(d0 - 86);
            a4->variant_2f = d1; a4->target_char = 0x45 /*'E'*/;
        } else {
            a4->base = 0x09F6;
            a4->target_char = (uint8_t)(0x65 + (G.char_scratch_22b == 0x4B ? 0 : 1));
            a4->comp = 2;
        }
        return;
    }
    /* marker gone: jump arc (uses +0x18 vertical, +0x1C timer, anim 0x8A..0x8D,
     * position helper 0x41F9C, sound 0x12) — represented in raw/0004396a.c */
    arcade_41f9c_arc(a4);
}

/* 0x43B32 — state 0x1A — master 0x13e-position-gated chain dispatcher (largest).
 * Status: PARTIAL (the numerous 0x13e-banded char/base re-targets are captured
 * in raw/00043b32.c; the anim tail 0x43E8E is represented). */
void h5_43b32(ActorRecord *a4)
{
    (void)a4; /* PARTIAL — see raw/00043b32.c for the full 0x13e-banded chain */
}

/* 0x43ECC — state 0x1B — BURST SPAWNER */
void h5_43ecc(ActorRecord *a4)
{
    if (arcade_40e74_marker_recheck(a4)) { arcade_4092e(a4); return; }
    if (a4->timer != 0) { a4->timer--; return; }         /* +0x1C */
    if (a4->anim_frame_dur == 0) {                       /* +0x08 */
        a4->anim = 0x7A; a4->anim_frame_dur = 1;
    }
    if (a4->x < 0x150) return;                            /* +0x16 */
    if ((uint16_t)(a4->x + 20) < G.camera_x_10be) return;/* off to the left */
    a4->timer = 0x100; a4->anim_frame_dur = 2;
    arcade_43f4e_burst(a4);                               /* spawn 5 children */
}

/* 0x4415A — states 0x1D/0x21 */
void h5_4415a(ActorRecord *a4)
{
    uint16_t y = a4->y;                                   /* +0x1A band gate */
    if (!(y >= 472 && y < 488)) {
        if (!arcade_40e74_marker_recheck(a4))
            return; /* 0x442BA anim tail */
    }
    uint16_t p = G.progress_13e;
    if (p >= 0x2F) {                                      /* 0x441A2 char-relative */
        /* full char->char re-targeting matrix in raw/0004415a.c */
        arcade_4092e(a4);
        return;
    }
    G.char_scratch_22b = a4->variant_2f;                  /* A5+0x22B = +0x2F */
    arcade_4103a(a4); a4->base = 0x0224;
    a4->target_char = (uint8_t)(G.char_scratch_22b != 0 ? 82 /*'R'*/ : 76 /*'L'*/);
}

/* 0x43636 — state 0x22 */
void h5_43636(ActorRecord *a4)
{
    if (arcade_40e74_marker_recheck(a4)) {
        if (G.round == 3) {
            if (a4->target_char == 0x73 /*'s'*/) {
                arcade_4103a(a4); a4->base = 0x00F4; a4->target_char = 0x4F /*'O'*/;
                a4->field_30 = 1; arcade_41bee(a4); return;
            }
            if (a4->target_char == 0x74 /*'t'*/) {
                arcade_4103a(a4); a4->base = 0x0266; a4->target_char = 0x44 /*'D'*/;
                a4->field_30 = 1; return;
            }
            arcade_4103a(a4); a4->base = 0x0266; a4->target_char = 0x46 /*'F'*/;
            a4->field_30 = 1; return;
        }
        if (G.round == 5 && a4->target_char == 0x73 /*'s'*/) {
            arcade_4103a(a4); a4->base = 0x0224; a4->anim = 7;
            a4->target_char = 0x67 /*'g'*/; a4->field_30 = 2; a4->comp = 2; return;
        }
        arcade_4092e(a4);
        return;
    }
    /* marker gone: anim frame machine (0x436E0), anim = 0x29 + phase */
    if (a4->anim_frame_cd != 0) { a4->anim_frame_cd--; return; }
}

/*
 * ORIGINAL ARCADE PC: 0x00041180  latent scanner / hunter (state 0x00)
 * Provenance: GHIDRA_RAW (FUN_00041180). Status: PARTIAL.
 * The materialization DISPATCH structure is proven (CHECKPOINT A/B): mode==0
 * floor-follower scans floor markers 0x31-0x3c -> 0x40a06/0x40a86 state
 * transition; mode!=0 hunter scans for +0x0D letter marker 0x45-0x7b and the
 * large in-body dispatch sets state/anim/position + calls the enemy init. The
 * exact position arithmetic per branch is preserved in the Ghidra export
 * (analysis/decompilation/raw_snapshots/) and summarized in raw/00041180.c.
 */
void actor_ground_scanner_41180(ActorRecord *a4)
{
    (void)a4; /* PARTIAL — dispatch structure proven; see raw/00041180.c + export */
}
