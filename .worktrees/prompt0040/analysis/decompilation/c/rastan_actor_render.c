/* rastan_actor_render.c — CHECKPOINT H10
 * Semantic reconstruction of the actor sprite render dispatch (0x3D054) and the shared compositor
 * selector thunks (0x3F0BC / 0x4770E / 0x3FFDC / 0x3FFF0). NOT original Taito source; byte-faithful
 * control flow in raw/0003d054.c and raw/0003f0bc.c. The 68000 binary is final authority.
 *
 * PROVEN RENDER CHAIN (H10):
 *   per-actor render loop (0x41DAE...) : d0 = +0x01 anim, d6 = +0x20 mirror, d7 = +0x02 facing
 *     -> 0x3D054 : selector = +0x38; program table = COMPOSITOR_TABLE[selector]
 *                  { sel0:0x3D09E  sel1:0x4771C  sel2:0x3F0CE  sel3:0x40004  sel4:0x4002C }
 *     -> program = table + be16(table + anim*2)
 *     -> 0x3C902 : the SINGLE general compositor interpreter for ALL selectors
 *     -> PC090OJ SAT pieces (control/y/tile-delta/x records; the offline compositor_vm.py executes
 *        this exactly for every selector).
 * Key result: the five compositor selectors only pick the PROGRAM TABLE; the interpreter is shared.
 * The materialized H5/H6 actors (mostly selector 2, +0x38=2) therefore render as ordinary general
 * programs — no special/unimplemented rendering mode is required to assemble their legal frames.
 */
#include "rastan_arcade_types.h"

extern void     run_compositor(ActorRecord *a, unsigned program_addr);   /* 0x3C902 */
extern unsigned rom_word(unsigned addr);                                  /* be16 from maincpu */

static const unsigned COMPOSITOR_TABLE[5] = {
    0x03D09Eu, 0x04771Cu, 0x03F0CEu, 0x040004u, 0x04002Cu
};

/* 0x3C9E8: select the final SAT word-0 low byte.
 * +0x27 is an optional override, not the unconditional palette source. When
 * bit 6 is clear, the compositor program control byte (including its low
 * palette nibble) survives unchanged. When bit 6 is set, +0x27 replaces it.
 * The caller preserves D0's high byte and writes the result to PC090OJ SAT.
 *
 * H15 DISPLAY-PALETTE consequence: marker-chain-transformed family-2 actors have +0x27 = 0
 * (0x4092E cleared it during 0x4103A re-arm; 0x45684 is creation-only and is NOT re-run). So their
 * DISPLAYED palette line is the compositor program's control-byte low nibble here, NOT the
 * creation-time 0x45684 line. Proven display values (7 H14 Phase-2 instances) are in
 * analysis/actor_decompilation/h15_materialized_render_palettes.tsv.
 */
uint16_t apply_actor_attribute_override(const ActorRecord *a, uint16_t program_control){
    if ((a->pal_attr & 0x40u) == 0u) return program_control;
    return (uint16_t)((program_control & 0xFF00u) | a->pal_attr);
}

/* 0x3D054: pick program table by +0x38, index by +0x01, run the shared interpreter. */
void render_actor_sprite(ActorRecord *a){
    unsigned sel = a->comp;                 /* +0x38 compositor selector (0..4) */
    if (sel > 4) sel = 0;
    unsigned table = COMPOSITOR_TABLE[sel];
    unsigned program = table + rom_word(table + (a->anim & 0xFF) * 2);
    run_compositor(a, program);             /* 0x3C902 general interpreter (all selectors) */
}
