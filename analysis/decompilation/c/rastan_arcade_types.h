/*
 * Rastan arcade reconstructed decompilation — shared types.
 *
 * Derived from static analysis of the original Motorola 68000 program
 * (build/regions/maincpu.bin + build/maincpu.disasm.txt + the Ghidra export).
 * Auditable representation of program semantics, NOT original Taito source; not
 * guaranteed to compile back into an identical ROM. The 68000 binary is final
 * authority.
 *
 * A5 = 0x0010C000 (arcade work-RAM base). Actor records are exactly 0x40 bytes.
 * Field offsets are preserved EXACTLY (see _Static_assert offsetof block). Names
 * are used only where a single semantic is proven; POLYMORPHIC bytes keep a
 * neutral name + documented per-context views, so a convenient name never
 * becomes false architecture.
 */
#ifndef RASTAN_ARCADE_TYPES_H
#define RASTAN_ARCADE_TYPES_H

#include <stdint.h>
#include <stddef.h>

/* ---- ActorRecord: exactly 0x40 bytes; offsets match the 68000 A4 record ---- */
typedef struct ActorRecord {
    uint8_t  active;          /* +0x00 nonzero = live */
    uint8_t  anim;            /* +0x01 animation / compositor-program index */
    uint8_t  facing;          /* +0x02 */
    uint8_t  mode;            /* +0x03 0 = floor-follower, !=0 = char-hunter */
    uint8_t  klass;           /* +0x04 class / update selector (state = class+1) */
    uint8_t  state;           /* +0x05 behavior state -> 0x40BAA dispatch */
    uint8_t  rec_type;        /* +0x06 record type (0x4543E loader) */
    uint8_t  init_flag;       /* +0x07 first-frame/init flag (0x3CEB0) */
    uint8_t  anim_frame_dur;  /* +0x08 anim frame duration (also handler-local phase state) */
    uint8_t  anim_frame_cd;   /* +0x09 anim frame countdown */
    uint8_t  field_0a;        /* +0x0A */
    uint8_t  anim_phase;      /* +0x0B anim phase (handler-local sub-index) */
    uint8_t  field_0c;        /* +0x0C */
    uint8_t  target_char;     /* +0x0D hunter target marker char (0x31-0x3c / 0x45-0x7b) */
    uint8_t  field_0e[4];     /* +0x0E..+0x11 POLYMORPHIC (see notes below) */
    uint8_t  anim_subcount;   /* +0x12 anim sub-counter (0x3CEB0) */
    uint8_t  field_13;        /* +0x13 */
    uint16_t home_x;          /* +0x14 home / anchor X */
    uint16_t x;               /* +0x16 position X */
    uint16_t home_y;          /* +0x18 home / anchor Y */
    uint16_t y;               /* +0x1A position Y (0x180 = off-screen hidden) */
    uint16_t timer;           /* +0x1C countdown timer */
    uint16_t base;            /* +0x1E graphics base tile code */
    uint8_t  field_20;        /* +0x20 */
    uint8_t  comp_index;      /* +0x21 component/sibling index (boss parts) */
    uint16_t field_22;        /* +0x22 */
    uint8_t  field_24;        /* +0x24 off-screen retire flag */
    uint8_t  field_25;        /* +0x25 */
    uint8_t  sched_slot;      /* +0x26 field-schedule slot id (0..4) */
    uint8_t  pal_attr;        /* +0x27 palette attribute (0x40|nibble) */
    uint16_t cfg_28;          /* +0x28..+0x29 template word; +0x29 is its low byte (68000 big-endian) */
    uint8_t  field_2a;        /* +0x2A schedule bit0 flag */
    uint8_t  field_2b;        /* +0x2B */
    uint16_t cfg_2c;          /* +0x2C..+0x2D template word */
    uint8_t  field_2e;        /* +0x2E */
    uint8_t  variant_2f;      /* +0x2F difficulty / variant select */
    uint8_t  field_30;        /* +0x30 */
    uint8_t  field_31;        /* +0x31 */
    uint16_t field_32;        /* +0x32 */
    uint16_t field_34;        /* +0x34 template word */
    uint8_t  field_36;        /* +0x36 */
    uint8_t  field_37;        /* +0x37 */
    uint8_t  comp;            /* +0x38 compositor selector */
    uint8_t  field_39;        /* +0x39 armored/base sub-select */
    uint8_t  field_3a;        /* +0x3A template byte */
    uint8_t  field_3b;        /* +0x3B */
    uint8_t  field_3c;        /* +0x3C */
    uint8_t  field_3d;        /* +0x3D */
    uint8_t  family;          /* +0x3E family (0x4544E selector) */
    uint8_t  field_3f;        /* +0x3F */
} ActorRecord;

/*
 * POLYMORPHIC field notes (proven multi-use; do NOT assign one global name):
 *  +0x0E..+0x11 (field_0e): in the HUNTER context (0x41180 stores it, 0x40E74
 *      rechecks it) it holds the found collision-map cell reference (0x41180
 *      writes a full pointer here, overlapping 0x0E-0x11). In the MATERIALIZED
 *      ground/component engines (0x47140 / 0x4684E) its low byte is reused as an
 *      animation/sequence index (a4@(0x0E) read as a byte, cmpib). Use the
 *      accessors below rather than a single typed field.
 *  +0x08/+0x09/+0x0B/+0x12: animation timing in 0x3CEB0, but reused as generic
 *      phase counters by several H5 handlers. Named for the animation role.
 *  +0x26 (sched_slot): schedule-slot id for field-schedule actors; not meaningful
 *      for scripted/child actors.
 *  +0x2F (variant_2f): difficulty/variant select; also a saved-char scratch in
 *      some H5 re-target branches.
 */

/* Compile-time layout contract: sizeof and key offsets must match the arcade. */
_Static_assert(sizeof(ActorRecord) == 0x40, "ActorRecord must be 0x40 bytes");
_Static_assert(offsetof(ActorRecord, active)     == 0x00, "active @0x00");
_Static_assert(offsetof(ActorRecord, mode)       == 0x03, "mode @0x03");
_Static_assert(offsetof(ActorRecord, state)      == 0x05, "state @0x05");
_Static_assert(offsetof(ActorRecord, rec_type)   == 0x06, "rec_type @0x06");
_Static_assert(offsetof(ActorRecord, target_char)== 0x0D, "target_char @0x0D");
_Static_assert(offsetof(ActorRecord, field_0e)   == 0x0E, "field_0e @0x0E");
_Static_assert(offsetof(ActorRecord, x)          == 0x16, "x @0x16");
_Static_assert(offsetof(ActorRecord, y)          == 0x1A, "y @0x1A");
_Static_assert(offsetof(ActorRecord, timer)      == 0x1C, "timer @0x1C");
_Static_assert(offsetof(ActorRecord, base)       == 0x1E, "base @0x1E");
_Static_assert(offsetof(ActorRecord, comp_index) == 0x21, "comp_index @0x21");
_Static_assert(offsetof(ActorRecord, sched_slot) == 0x26, "sched_slot @0x26");
_Static_assert(offsetof(ActorRecord, pal_attr)   == 0x27, "pal_attr @0x27");
_Static_assert(offsetof(ActorRecord, cfg_28)     == 0x28, "cfg_28 @0x28");
_Static_assert(offsetof(ActorRecord, variant_2f) == 0x2F, "variant_2f @0x2F");
_Static_assert(offsetof(ActorRecord, comp)       == 0x38, "comp @0x38");
_Static_assert(offsetof(ActorRecord, family)     == 0x3E, "family @0x3E");

/* ---- arcade address / value helpers (make the mechanism explicit, do NOT
 * silently turn a stored 16/32-bit arcade value into a host pointer) ---- */
#define ARCADE_A5_BASE      0x0010C000u
#define COLLISION_GRID_BASE 0x0010DE00u   /* A5+0x1E00 */

/* +0x0E hunter view: the arcade stores the found collision-cell address across
 * +0x0E..+0x11. This reads it back as the stored 32-bit arcade address. */
static inline uint32_t ar_cell_addr(const ActorRecord *a)
{ const uint8_t *p = a->field_0e; return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3]; }
/* +0x0E materialized view: low byte reused as an anim/sequence index. */
static inline uint8_t  ar_anim_index_0e(const ActorRecord *a) { return a->field_0e[3]; }
/* difficulty low byte of the +0x28 template word (68000 big-endian low byte). */
static inline uint8_t  ar_cfg29(const ActorRecord *a) { return (uint8_t)(a->cfg_28 & 0xFF); }

/* ---- 8-byte graphics template (0x45592 record-type, 0x45502/62 family) ---- */
typedef struct ActorTemplate {
    uint16_t base;      /* +0 -> actor.base (+0x1E) */
    uint8_t  field_3a;  /* +2 -> actor.field_3a (+0x3A) */
    uint8_t  anim;      /* +3 -> actor.anim (+0x01) */
    uint16_t cfg_28;    /* +4 -> actor.cfg_28 (+0x28) */
    uint16_t cfg_2c;    /* +6 -> actor.cfg_2c (+0x2C) */
} ActorTemplate;
_Static_assert(sizeof(ActorTemplate) == 8, "ActorTemplate must be 8 bytes");

/* Global work-RAM (A5-relative) fields referenced by actor code, by A5 offset. */
typedef struct ArcadeGlobals {
    uint8_t  round;             /* A5+0x118 (1..6) */
    uint16_t progress_13e;      /* A5+0x13E global sub-round progression 0..0x89 */
    uint16_t camera_x_10be;     /* A5+0x10BE camera/scroll X */
    uint16_t scroll_10cc;       /* A5+0x10CC */
    uint16_t wave_2de;          /* A5+0x2DE wave counter */
    uint16_t scroll_200;        /* A5+0x200 scroll bits */
    uint16_t iter_214;          /* A5+0x214 loop counter */
    uint16_t occ_29a;           /* A5+0x29A occupied count */
    uint16_t sched_free_c56;    /* A5+0xC56 free schedule slot (0xFF = none) */
    uint16_t variant_sel_c5a;   /* A5+0xC5A paired-actor variant select */
    uint8_t  char_scratch_22b;  /* A5+0x22B saved target char */
    uint16_t scene_1386;        /* A5+0x1386 scene index */
    uint16_t transient_138a;    /* A5+0x138A transition sub-state sequencer */
    uint16_t transition_1394;   /* A5+0x1394 phase-transition-active flag */
    uint16_t checkpoint_13b8;   /* A5+0x13B8 0x13E checkpoint at scene boundary */
    uint16_t section_1242;      /* A5+0x1242 master section index */
    uint16_t micro_10e8;        /* A5+0x10E8 scroll/stop/transition micro-phase */
    uint16_t round_flag_1360;   /* A5+0x1360 round-boundary flag */
} ArcadeGlobals;

/* ---- externs: hardware / not-yet-fully-decompiled helpers (PARTIAL/STUB) ---- */
extern void arcade_3ceb0(ActorRecord *a4);   /* PARTIAL: anim-frame advancer + motion step */
extern void arcade_4092e(ActorRecord *a4);   /* STUB: generic active-actor step / retire */
extern void arcade_41cfa(ActorRecord *a4);   /* PARTIAL: config-table (0x41D26) load by state */
extern void arcade_4103a(ActorRecord *a4);   /* STUB: consume/advance current marker cell */
extern void arcade_41bee(ActorRecord *a4);   /* STUB: post-materialization setup */
extern void arcade_45418(ActorRecord *a4);   /* helper: sets +0x29 from 0x4542E[state-0x13] */
extern void arcade_453d6(ActorRecord *a4);   /* difficulty tune of cfg_28/cfg_29 */
extern void arcade_3a0ec(uint8_t sound_id);  /* sound trigger */
extern void arcade_4734a(ActorRecord *a4);   /* STUB: airborne vertical/hover pre-step */
extern void arcade_41f9c_arc(ActorRecord *a4);/* STUB: jump/arc position helper (0x41F9C) */
extern void arcade_43f4e_burst(ActorRecord *a4);/* PARTIAL: state-0x1B 5-child burst (A5+0x3C8) */
extern void arcade_447f0(ActorRecord *a4);   /* STUB: child activate/init (from burst) */
extern void arcade_4382e(ActorRecord *a4);   /* helper: state 0x13 anim-frame reload */
extern void arcade_468d0(ActorRecord *a4);   /* PARTIAL: component facing vs camera */
extern int8_t arcade_41f9c(uint8_t in);      /* returns rotated component index (state 0x19) */
extern uint32_t collision_map_lookup_53a2e(void); /* returns stored collision cell address */

extern ArcadeGlobals G;   /* A5 view */

/* Template tables (defined in rastan_actor_tables.c) */
extern const ActorTemplate record_type_45592[];   /* legal types 0x08..0x1D (index = type-8) */
extern const ActorTemplate family_var0_45502[12];
extern const ActorTemplate family_varN_45562[12];
extern const ActorTemplate boss_comp0_454ba[4];
extern const ActorTemplate boss_comp3_454d2[4];
extern const ActorTemplate boss_else_454ea[4];
extern const uint8_t boss_round_rectype_444e0[6]; /* {0x0E,0x13,0x14,0x15,0x10,0x17} */

#endif /* RASTAN_ARCADE_TYPES_H */
