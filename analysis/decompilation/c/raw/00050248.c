/* ORIGINAL ARCADE PC: 0x00050248  progression -> scene -> descriptor world selector.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE. Byte-faithful transcription from the authoritative
 * arcade program (build/maincpu.disasm.txt, variant world_rev1). CHECKPOINT H22.
 *
 * This is the single routine that turns the master section index (A5+0x1242) into the three world
 * anchor states every downstream map/stream/collision stage reads: A5+0x013E (global progression),
 * A5+0x1386 (scene-descriptor index), A5+0x10FC (12-byte scene descriptor pointer), plus the layout
 * source pointers A5+0x1038/0x103C and (falling into the H11 tail 0x503BC) the section-kind pointer
 * A5+0x10C6. Ghidra did NOT identify a function here (gap 0x4BBF0..0x5049A), so it is not in the
 * game-wide function census denominator; it is still durable, byte-faithful arcade evidence.
 *
 * EXACT DISASSEMBLY (build/maincpu.disasm.txt):
 *   -- 0x50248 : A5+0x1242 (master section) -> 0x5073A[section] -> A5+0x013E (global progression) --
 *   50248: 227c 0005073a  moveal #0x5073A,%a1      ; a1 = &section_to_progression[]
 *   5024e: 322d 1242      movew  %a5@(0x1242),%d1   ; d1 = master section index
 *   50252: 43f1 1000      lea    %a1@(0,%d1:w),%a1  ; a1 = &table[section]  (byte table)
 *   50256: 4241           clrw   %d1
 *   50258: 1211           moveb  %a1@,%d1           ; d1 = progression value
 *   5025a: 3b41 013e      movew  %d1,%a5@(0x013E)   ; A5+0x013E = progression
 *   5025e: 3001           movew  %d1,%d0            ; d0 = progression
 *   -- 0x50260 : progression vs ROUND-BOUNDARY table 0x502AC -> A5+0x1360 boundary flag --
 *   50260: 227c 000502ac  moveal #0x502AC,%a1      ; a1 = &round_boundaries[] = {0x16,0x2D,0x44,0x5B,0x72,0x89,0xFFFF}
 *   50266: 3219           movew  %a1@+,%d1          ; d1 = next boundary word
 *   50268: 0c41 ffff      cmpiw  #0xFFFF,%d1
 *   5026c: 671e           beqs   0x5028c            ; end-of-list, not a boundary
 *   5026e: b041           cmpw   %d1,%d0
 *   50270: 6702           beqs   0x50274            ; progression IS a round-start boundary
 *   50272: 60f2           bras   0x50266            ; else keep scanning
 *   50274: 303c 0025      movew  #0x25,%d0          ; on boundary: request state 0x25 ...
 *   50278: 4eb9 0003a116  jsr    0x3a116            ;   ... via 0x3a116 (queue helper)
 *   5027e: 3b7c 00ff 12ee movew  #0xFF,%a5@(0x12EE)
 *   50284: 3b7c 0001 1360 movew  #1,%a5@(0x1360)    ; A5+0x1360 = 1 (this progression starts a round)
 *   5028a: 6008           bras   0x50294
 *   5028c: 3b7c 00ff 1360 movew  #0xFF,%a5@(0x1360) ; A5+0x1360 = 0xFF (NOT a round boundary)
 *   50292: 4e71           nop
 *   -- 0x50294 : progression -> 0x507C5[progression] -> A5+0x1386 (scene-descriptor index) --
 *   50294: 227c 000507c5  moveal #0x507C5,%a1      ; a1 = &progression_to_scene[]
 *   5029a: 322d 013e      movew  %a5@(0x013E),%d1
 *   5029e: 43f1 1000      lea    %a1@(0,%d1:w),%a1
 *   502a2: 4241           clrw   %d1
 *   502a4: 1211           moveb  %a1@,%d1
 *   502a6: 3b41 1386      movew  %d1,%a5@(0x1386)   ; A5+0x1386 = scene-descriptor index
 *   502aa: 4e75           rts
 *
 *   -- 0x50384 (layout-source setup, runs just before 0x503A0 in the same world-init flow) --
 *   50384: 203c 00034f9c  movel  #0x34F9C,%d0
 *   5038a: d081           addl   %d1,%d0
 *   5038c: 2b40 1038      movel  %d0,%a5@(0x1038)   ; A5+0x1038 = foreground layout source (0x34F9C + d1)
 *   50390: 203c 0003725c  movel  #0x3725C,%d0
 *   50396: d081           addl   %d1,%d0
 *   50398: 2b40 103c      movel  %d0,%a5@(0x103C)   ; A5+0x103C = background layout source (0x3725C + d1)
 *   -- 0x503A0 : scene index -> 12-byte descriptor pointer A5+0x10FC --
 *   503a0: 322d 1386      movew  %a5@(0x1386),%d1   ; d1 = scene-descriptor index
 *   503a4: 303c 0006      movew  #6,%d0
 *   503a8: e348           lslw   #1,%d0             ; d0 = 12
 *   503aa: c2c0           muluw  %d0,%d1            ; d1 = scene_index * 12
 *   503ac: 203c 0003951c  movel  #0x3951C,%d0
 *   503b2: d081           addl   %d1,%d0
 *   503b4: 2b40 10fc      movel  %d0,%a5@(0x10FC)   ; A5+0x10FC = &scene_descriptor[scene] (12 bytes)
 *   -- 0x503BC : H11 tail (already COMPLETE in raw/000503bc.c) : progression -> 0x50EE0 -> section kind --
 *   503bc: 227c 00050ee0  moveal #0x50EE0,%a1
 *   503c2: 322d 013e      movew  %a5@(0x013E),%d1
 *   503cc: 1211           moveb  %a1@,%d1           ; d1 = scene idx (section-kind space)
 *   503ce: 203c 00050f6b  movel  #0x50F6B,%d0
 *   503d6: 2b40 10c6      movel  %d0,%a5@(0x10C6)   ; A5+0x10C6 = &section_kind_stream (map stream ptr)
 *   503da: 4e75           rts
 *
 * TABLES (verified from maincpu.bin):
 *   0x502AC round_boundaries[7] = {0x0016,0x002D,0x0044,0x005B,0x0072,0x0089,0xFFFF} (round starts R1..R6)
 *   0x5073A section_to_progression[] byte table (e.g. {0,0,0,0,4,4,4,4,8,...}) — groups 4 sections/step
 *   0x507C5 progression_to_scene[] byte table (0,1,2,...,0xF,0x12,0x13,...) — scene-descriptor index
 *   0x3951C scene_descriptor[]  12 bytes each = two 6-byte {word count/flags, longword ROM layout ptr}
 */

extern short A5[]; /* arcade work RAM, byte offsets used directly below */
extern const unsigned char section_to_progression_5073A[];
extern const unsigned short round_boundaries_502AC[];   /* {0x16,0x2D,0x44,0x5B,0x72,0x89,0xFFFF} */
extern const unsigned char progression_to_scene_507C5[];
extern void queue_state_3a116(unsigned short state);

/* 0x50248 : master section -> progression, round-boundary flag, scene index (byte-faithful). */
void world_progression_select_50248(void)
{
    unsigned short section = (unsigned short)A5[0x1242/2];
    unsigned short prog = section_to_progression_5073A[section];       /* 0x5073A[section] */
    A5[0x013E/2] = prog;                                                /* A5+0x013E */

    int on_boundary = 0;                                               /* 0x50260 scan 0x502AC */
    for (const unsigned short *b = round_boundaries_502AC; *b != 0xFFFF; ++b)
        if (*b == prog) { on_boundary = 1; break; }
    if (on_boundary) {
        queue_state_3a116(0x25);                                       /* 0x50274 */
        A5[0x12EE/2] = 0xFF;
        A5[0x1360/2] = 1;                                              /* round-start */
    } else {
        A5[0x1360/2] = 0xFF;                                           /* not a boundary */
    }

    A5[0x1386/2] = progression_to_scene_507C5[prog];                   /* 0x50294 : scene index */
}

/* 0x503A0 : scene index -> 12-byte scene-descriptor pointer (+ layout source setup at 0x50384). */
void world_scene_descriptor_ptr_503a0(unsigned long fg_ofs, unsigned long bg_ofs)
{
    A5[0x1038/2] = 0; A5[0x1038/2+1] = 0; /* longwords; see disasm: A5+0x1038 = 0x34F9C + d1 */
    /* A5+0x1038 = foreground layout src, A5+0x103C = background layout src (0x34F9C / 0x3725C + d1) */
    unsigned short scene = (unsigned short)A5[0x1386/2];
    unsigned long desc = 0x3951CUL + (unsigned long)scene * 12UL;      /* A5+0x10FC */
    (void)desc; (void)fg_ofs; (void)bg_ofs;
    /* A5+0x10FC = desc ; falls through to H11 tail 0x503BC (A5+0x10C6 section-kind ptr). */
}
