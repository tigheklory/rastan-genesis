/* rastan_boss_composite.c — boss multi-record positioning and palette publication.
 * Semantic reconstruction; byte-faithful control flow in raw/000423b2.c (creators) and
 * raw/0003ba20.c (palette loader). NOT original Taito source. 68000 is final authority.
 *
 * MULTI-RECORD BOSSES (proven): the visible boss is a BODY record + structural component records:
 *   R5: 0x423B2 creates 5x rec_type 0x11 (base 0x0988 anim 0x89, comp 1, state 0x11) in A5+0x5C8.
 *   R6: 0x423F4 creates 4 records rec_type 0x17..0x1A (0x0B35/0x0AED/0x0CCB/0x0BEB) in A5+0x648.
 *   Bases/anims come from the record-type table 0x45592 (loader 0x4543E).
 *   R1-R4 bodies are single-record for the normal state (their component-creator calls are not on
 *   the normal-body path); R6/R5 are the multi-record cases.
 *
 * PALETTE DIRECTION CORRECTION: 0x3A2D0 is `move.w (A0)+,(A1)+`.  Consequently 0x45D7C and
 * 0x45DC4 publish A5+0x1600 TO CLCS palette RAM, never the reverse.  With sprite_ctrl=0x60 the
 * PC090OJ combines compositor nibble F with bank base 0x30, selecting physical bank 0x3F.
 * 0x45DC4 maps working line 15 to that bank: 48+15=63.  Thus the six normal boss sources really
 * are 0x3BA88[round][15] -> 0x4FD02+pool*32 (pools 11,3,2,11,3,11).  The later staged-master
 * interpretation was based on the reversed copy and is superseded.
 */
#include "rastan_arcade_types.h"

extern void load_record_type(ActorRecord *a);   /* 0x4543E */

typedef struct BossOffset { int8_t dx, dy; } BossOffset;
static const BossOffset boss_offsets_43484[27] = {
    {40,-16},{34,28},{48,-16},{20,-5},{6,-16},{20,-20},{8,-20},{20,-11},{8,-11},
    {8,32},{52,-60},{76,-4},{48,-4},{-3,-8},{7,-8},{16,-8},{-7,-16},{2,-16},
    {42,-19},{24,-36},{8,-44},{-8,-52},{0,-61},{-46,-61},{-62,-34},{-72,-20},{0,-72}
};

/* 0x43458 internal entry: pure per-frame position update. */
void boss_place_component_43458(const ActorRecord *parent, ActorRecord *child, unsigned index)
{
    int16_t dx = boss_offsets_43484[index].dx;
    if (parent->facing == 0) dx = (int16_t)-dx;
    child->x = (uint16_t)(parent->x + dx);
    child->y = (uint16_t)(parent->y + boss_offsets_43484[index].dy);
}

/* 0x43450 containing-function entry adds the two child initializations. */
void boss_init_and_place_component_43450(const ActorRecord *parent, ActorRecord *child,
                                         unsigned index)
{
    child->comp = 0;
    ((uint8_t *)(void *)child)[0x23] = (uint8_t)index;
    boss_place_component_43458(parent, child, index);
}

void boss_r5_sync_components_42380(const ActorRecord *body, ActorRecord parts[5])
{
    for (unsigned i=0; i<5; ++i) if (parts[i].active) {
        parts[i].facing = body->facing;
        parts[i].mode = body->mode;
        boss_place_component_43458(body, &parts[i], 13+i);
    }
}

typedef struct DragonTailPlacement { int16_t dx, dy; } DragonTailPlacement;
static const DragonTailPlacement dragon_tail_right[5] =
    {{64,-48},{56,-64},{48,-80},{56,-32},{40,-8}};
static const DragonTailPlacement dragon_tail_left[5] =
    {{-64,-48},{-56,-64},{-48,-80},{-56,-32},{-40,-8}};

unsigned boss_r6_tail_phase_index_4e976(uint16_t phase)
{
    if (phase==0) return 0;
    if (phase==3) return 1;
    if (phase==6) return 2;
    if (phase==9) return 3;
    return 4;
}

/* 0x4E7C6 is used by types 0x18/0x19 while boss_state != 0. */
void boss_r6_sync_anchor_4e7c6(const ActorRecord *primary, ActorRecord *part)
{
    part->facing=primary->facing; part->x=primary->x; part->y=primary->y;
}

/* Placement portion of 0x4E69C for type 0x1A. */
void boss_r6_place_tail_4e69c(const ActorRecord *primary, ActorRecord *tail,
                              uint16_t boss_state, uint16_t phase)
{
    if (boss_state==0) return;
    tail->facing=primary->facing;
    unsigned i=boss_r6_tail_phase_index_4e976(phase);
    const DragonTailPlacement *p = tail->facing ? dragon_tail_right : dragon_tail_left;
    tail->anim=(uint8_t)(48 + 9*i);
    tail->x=(uint16_t)(primary->x+p[i].dx);
    tail->y=(uint16_t)(primary->y+p[i].dy);
}

uint16_t boss_effective_palette_bank(uint16_t sprite_ctrl, uint8_t compositor_nibble)
{
    return (uint16_t)(((sprite_ctrl & 0x00e0u) >> 1) | (compositor_nibble & 0x0fu));
}

uint16_t boss_working_line_for_physical_bank(uint16_t physical_bank)
{
    /* 0x45D7C publishes working 0..31 -> physical 0..31; 0x45DC4 publishes
       working 0..31 -> physical 48..79. */
    return physical_bank >= 48 && physical_bank < 80
         ? (uint16_t)(physical_bank - 48) : physical_bank;
}

uint16_t boss_palette_convert_3ba64_59ade(uint16_t rom_0rgb)
{
    return (uint16_t)(((rom_0rgb & 0x0f00u) >> 7) |
                      ((rom_0rgb & 0x00f0u) << 2) |
                      ((rom_0rgb & 0x000fu) << 11));
}

/* Semantic form of 0x59AD4: direct table-row -> physical CLCS line update. */
void boss_palette_write_line_59ad4(uint16_t clcs[2048], unsigned dest_line,
                                   const uint16_t *rows, unsigned source_row)
{
    const uint16_t *src=rows+source_row*16;
    uint16_t *dst=clcs+dest_line*16;
    for (unsigned i=0;i<16;++i)
        if (src[i]!=0xffffu) dst[i]=boss_palette_convert_3ba64_59ade(src[i]);
}

/* Semantic form of 0x45D7C/0x45DC4 after both eight-chunk publishers finish. */
void boss_palette_publish_working(const uint16_t working[512], uint16_t clcs[2048])
{
    for (unsigned i=0;i<512;++i) clcs[i]=working[i];       /* physical lines 0..31 */
    for (unsigned i=0;i<512;++i) clcs[48*16+i]=working[i]; /* physical lines 48..79 */
}

/* 0x3BA20's exact line-selection contract, separated from ROM access. */
unsigned boss_round_pool_index(const uint8_t round_rows[6][32], unsigned round,
                               unsigned working_line)
{
    return round_rows[round-1][working_line];
}

/* R5 five structural segments (type 0x11). */
void boss_r5_components(ActorRecord *pool){
    for (int i=0;i<5;i++){
        ActorRecord *a = pool + i;
        a->comp_index = (uint8_t)i; a->active = 1; a->comp = 1; a->state = 0x11; a->rec_type = 0x11;
        load_record_type(a);   /* base 0x0988, anim 0x89 */
    }
}
/* R6 four structural parts (types 0x17..0x1A -> 0x0B35/0x0AED/0x0CCB/0x0BEB). */
void boss_r6_components(ActorRecord *pool){
    for (int i=0;i<4;i++){
        ActorRecord *a = pool + i;
        a->rec_type = (uint8_t)(0x17 + i);
        load_record_type(a);
    }
}

/* 0x42340: initialize the primary, then perform the deliberately overlapping
 * forward 0x3A2D0 copy.  Because destination is source+0x40 and 0x60 words are
 * copied, the first complete record is repeated into the next three slots. */
void boss_r6_create_42340(ActorRecord records[4])
{
    records[0].x=304; records[0].y=232; records[0].state=0x10;
    for (unsigned i=1;i<4;++i) records[i]=records[0];
    boss_r6_components(records);
}
