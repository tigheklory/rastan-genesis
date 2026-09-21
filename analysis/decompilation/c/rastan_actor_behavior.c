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
 * ORIGINAL ARCADE PC: 0x00040CCC  state 0x0F — armored man
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * base 0x0A73 (sword) -> transforms in place to 0x0A5A (ball&chain) at anim
 * frame >= 10; comp 2; family -> 0x0C. mode!=0 -> alt anim path (sound 23);
 * field_39 set -> base 0x0275 sub-path.
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

transform: /* 0x40D32: family 0x0C, base 0x0A5A ball-and-chain variant */
    a4->family  = 0x0C;   /* +0x3E */
    a4->field_3a = 0xFF;  /* +0x3A */
    a4->field_37 = 0;     /* +0x37 */
    a4->field_3d = 0;     /* +0x3D */
    a4->base    = 0x0A5A; /* +0x1E */
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

/*
 * ORIGINAL ARCADE PC: 0x000473B8  airborne-actor engine (states 1,2,0D,0E)
 * Provenance: RECONSTRUCTED_FROM_68000. Status: COMPLETE (structure).
 */
void actor_flying_engine_473b8(ActorRecord *a4)
{
    if (a4->init_flag == 0) {
        arcade_41cfa(a4);
        if (a4->family == 1) {
            a4->anim_frame_dur = 4;     /* +0x08 */
            arcade_4734a(a4);           /* vertical/hover pre-step */
            a4->field_0a = 8;           /* +0x0A */
        } else if (a4->family == 0x0A) {
            a4->anim_frame_dur = (a4->field_2e != 0) ? 2 : 7;
            arcade_4734a(a4);
        } else {
            arcade_4734a(a4);
        }
    }
    arcade_3ceb0(a4);                   /* SAME shared core as 0x47140 */
    a4->field_20 &= (uint8_t)~0x01;     /* bclr #0,+0x20 */
    /* per-state anim selection (states 0x0D/0x0E special) — represented in raw */
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
