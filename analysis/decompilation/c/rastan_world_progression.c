/* rastan_world_progression.c — CHECKPOINT H22
 * Semantic reconstruction of the ORIGINAL ARCADE progression -> scene -> descriptor chain (the head
 * of the world/map pipeline). NOT original Taito source; byte-faithful control flow in
 * raw/00050248.c. All PCs from build/maincpu.disasm.txt (world_rev1). A5 = 0x10C000.
 *
 * WORLD PROGRESSION OWNERSHIP (PROVEN, static):
 *   A5+0x1242  master section index    (advanced by transition/round logic; +16 at 0x452D4 round step)
 *       -> byte table 0x5073A[section]                       (0x50248)
 *   A5+0x013E  global progression      = 0x5073A[section]
 *       -> compare to round-boundary table 0x502AC = {0x16,0x2D,0x44,0x5B,0x72,0x89,0xFFFF}  (0x50260)
 *   A5+0x1360  round-start flag        = 1 on a boundary (also queues state 0x25 + A5+0x12EE=0xFF),
 *                                        else 0xFF
 *   A5+0x013E  -> byte table 0x507C5[progression]            (0x50294)
 *   A5+0x1386  scene-descriptor index  = 0x507C5[progression]
 *       -> A5+0x10FC = 0x3951C + scene*12  (12-byte scene descriptor pointer)   (0x503A0)
 *       -> A5+0x1038 = 0x34F9C + d1  (foreground layout source)                 (0x50384)
 *       -> A5+0x103C = 0x3725C + d1  (background layout source)
 *       -> A5+0x10C6 = 0x50F6B + 0x50EE0[progression]  (section-kind stream, H11 tail 0x503BC)
 *
 * ROUND vs SUB-ROUND (H22 section 16 — DISTINCT contracts, do not conflate):
 *   - ROUND BOUNDARY: A5+0x013E == one of {0x16,0x2D,0x44,0x5B,0x72,0x89} -> A5+0x1360=1 (R1..R6 start).
 *   - SUB-ROUND / SCENE change: A5+0x1386 changes (new descriptor) WITHOUT a round boundary — most
 *     0x507C5 steps are +1 within a round. A5+0x013E advances every scene; A5+0x1242 is the master
 *     section that maps many sections to one progression group via 0x5073A (4 sections per step in the
 *     sampled region).
 *   - BACKGROUND-BANK change is a property of the descriptor/stream, NOT the round (see
 *     project_scene_background_bank_map: mid-round bank change only R3/R5/R6).
 *
 * These are the exact input states section 6 of the checkpoint asked to verify; verified in use here
 * rather than trusting older labels: A5+0x1242 = master section (not "round"); A5+0x013E = global
 * progression; A5+0x1386 = scene-DESCRIPTOR index (the 0x3951C index, distinct from the 0x50EE0
 * section-kind index used for outdoor/castle).
 */

enum { PROG_TABLE_5073A=0x5073A, ROUND_BOUNDS_502AC=0x502AC, SCENE_TABLE_507C5=0x507C5,
       SCENE_DESCRIPTORS_3951C=0x3951C, SECTION_KIND_50EE0=0x50EE0 };

/* the six proven round-start progression values (R1..R6) */
static const unsigned short round_start_progression[6] = {0x16,0x2D,0x44,0x5B,0x72,0x89};

/* Full head-of-pipeline selector; see raw/00050248.c for the byte-faithful transcription. */
void world_select(unsigned short master_section /*A5+0x1242*/,
                  unsigned short *out_progression /*A5+0x013E*/,
                  unsigned short *out_round_start /*A5+0x1360*/,
                  unsigned short *out_scene_index /*A5+0x1386*/)
{
    extern const unsigned char section_to_progression_5073A[];
    extern const unsigned char progression_to_scene_507C5[];
    unsigned short prog = section_to_progression_5073A[master_section];
    *out_progression = prog;
    *out_round_start = 0xFF;
    for (int i = 0; i < 6; ++i) if (round_start_progression[i] == prog) { *out_round_start = 1; break; }
    *out_scene_index = progression_to_scene_507C5[prog];
    /* downstream: A5+0x10FC = 0x3951C + (*out_scene_index)*12 (descriptor ptr) */
}
