/* rastan_execution_spine.c — CHECKPOINT H21
 * Semantic reconstruction of the ORIGINAL ARCADE per-frame execution spine (the bottom-up engine
 * loop). NOT original Taito source; byte-faithful control flow lives in raw/0003a008.c. All PCs are
 * from build/maincpu.disasm.txt (variant world_rev1, authoritative arcade program). A5 = 0x10C000.
 *
 * SHAPE OF THE ENGINE (PROVEN, static):
 *   reset vector -> 0x3A000 : braw 0x3AE86            hardware init (see below)
 *                             braw 0x3A080            then fall into the idle loop
 *   0x3AE86  HW INIT: PC080SN scroll/plane regs @0xC50000, PC090OJ sprite regs @0xD0xxxx,
 *            int-ack latch 0x350008, sound sub-CPU 0x3E0001, palette RAM clear @0x200000; SSP=0x10DE00.
 *   0x3A080  IDLE LOOP (main thread): jsr 0x510C6 ; bra self.  The game is INTERRUPT-DRIVEN — the
 *            foreground thread does nothing but service 0x510C6 while the L5/VBlank ISR runs a frame.
 *   0x3A008  L5/VBLANK ISR (raw/0003a008.c, COMPLETE): per frame it
 *              (1) masks IRQs, acks 0x350008, latches D0 to 0x3C0000;
 *              (2) if A5+0x02 in [2,4): pre-pass 0x3A126, then if master-state!=0 and freeze flag
 *                  A5+0x1394 != 1 -> ACTOR UPDATE 0x41F30 (the whole live cast);
 *              (3) five fixed pre-frame subsystems: 0x3AB7C, 0x3ABE2, 0x3A0A8, 0x3EEFA, 0x3EF5C;
 *              (4) dispatches the master game-state handler via table @0x3A06C, tail-calling it so
 *                  the handler returns through the pushed RTE tail 0x3A074.
 *
 * MASTER GAME-STATE DISPATCH TABLE @0x3A06C (A5+0x00 selects; decoded from maincpu.bin):
 *   0 -> 0x3A9FE   1 -> 0x3A8AC   2 -> 0x3A15A   3 -> 0x3AB6E
 *   4 -> 0x3EF25   5 -> 0x3A071   6 -> 0x3FD0E   7 -> 0x3A2E8
 *   (These 8 handlers are the per-mode frame drivers: attract/frontend, play, transitions, etc.
 *    Their internals are on the code frontier — see analysis/decompilation/code_frontier.csv.)
 *
 * KEY WORK-RAM SELECTORS ON THE SPINE:
 *   A5+0x00    master game-state (0..7)      — chooses the dispatch handler
 *   A5+0x02    frame sub-state / phase word  — gates the actor pass to the window [2,4)
 *   A5+0x1394  actor-freeze flag             — when 1, actor update is skipped this frame
 *
 * WHY THIS MATTERS FOR THE REROM: this is the top of the call tree every other decompiled
 * subsystem hangs from. The actor update (0x41F30 -> per-actor 0x41F30 body), the collision/marker
 * producers, the compositor (0x3D054/0x3C902) and the palette resolver (0x45684) all execute
 * downstream of this ISR. Documenting the spine fixes the ORDER in which native Genesis realization
 * must run each frame (input/pre-pass -> actor update -> fixed subsystems -> state handler -> commit).
 *
 * STATUS: the ISR entry 0x3A008 and the idle loop 0x3A080 are COMPLETE (raw/0003a008.c). The reset
 * init 0x3AE86 is documented (h21_execution_spine.tsv) but not yet fully byte-transcribed; the 8
 * state handlers and the 5 pre-frame subsystems remain NOT_DECOMPILED / PARTIAL on the frontier.
 */

/* Logical spine (semantic view; see raw/0003a008.c for the byte-faithful ISR). */
enum { GS_ATTRACT0=0, GS_PLAY1, GS_S2, GS_S3, GS_S4, GS_S5, GS_S6, GS_S7 };

typedef void (*state_handler)(void);
/* addresses correspond to table @0x3A06C */
extern void gs0_3a9fe(void), gs1_3a8ac(void), gs2_3a15a(void), gs3_3ab6e(void),
            gs4_3ef25(void), gs5_3a071(void), gs6_3fd0e(void), gs7_3a2e8(void);
const state_handler vblank_state_dispatch[8] = {
    gs0_3a9fe, gs1_3a8ac, gs2_3a15a, gs3_3ab6e,
    gs4_3ef25, gs5_3a071, gs6_3fd0e, gs7_3a2e8,
};
