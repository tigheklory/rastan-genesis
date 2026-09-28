/* rastan_world_scroll.c — CHECKPOINT H23
 * Semantic reconstruction of the ORIGINAL ARCADE vertical (and paired horizontal) foreground scroll
 * contract. NOT original Taito source; byte-faithful control flow in raw/000557ba.c and
 * raw/00055ab4.c. All PCs from build/maincpu.disasm.txt (world_rev1). A5 = 0x10C000.
 *
 * ==================== VERTICAL SCROLL CONTRACT (PROVEN) ====================
 * FIELDS:
 *   A5+0x10AE  FG Y scroll value        -> PC080SN 0xC40002 (commit 0x55ACC); wrap mod 512
 *   A5+0x10EC  FG X scroll value        -> PC080SN 0xC40000 (commit 0x55ABC); wrap mod 512, half-rate
 *   A5+0x10BE  player screen-Y          band-clamped [32,304], target ~80 (0x539C2)
 *   A5+0x10DC  per-frame scroll delta   = min(pending, 4) px  (0x51880)
 *   A5+0x1266  pending scroll amount UP    (fed by player movement/climb)
 *   A5+0x1268  pending scroll amount DOWN
 *   A5+0x10D8  scroll step (px/frame; typ 4, set at 0x52958 / 0x539BA)
 *   A5+0x10B8  scroll direction accumulator (>=0 up, <0 down); UPPER LIMIT 160 (0xA0)
 *   A5+0x10B2  sub-row (8-px) accumulator (bit3 => row boundary; stream a row)
 *   A5+0x10D0  scroll flags: bit6 up-limit reached, bit7 down flag
 *   A5+0x13D0  row-stream direction mode (2 up / 3 down)
 *   A5+0x10F0  X half-step fraction accumulator (0x10AE Y is full-rate; 0x10EC X is half-rate)
 *
 * PER-FRAME SCROLL DECISION ORDER:
 *   1. Player movement (0x51880) queues vertical motion into A5+0x1266 (up) / A5+0x1268 (down),
 *      dispenses at most 4 px/frame into A5+0x10DC, and calls the clamp controller 0x539C2.
 *   2. Clamp controller 0x539C2 keeps player screen-Y (A5+0x10BE) in the band by comparing to the
 *      HARD-CODED thresholds: center 80, upper region 304 (0x539A0), lower 32 (0x53A0C). It sets the
 *      scroll step A5+0x10D8 and the pending flags A5+0x10D0 (bit3) accordingly.
 *   3. Scroll dispatch 0x557BA (Y) / 0x55B3C (X): if direction accumulator A5+0x10B8 >= 160 and the
 *      section-kind gate A5+0x10A8 != 0, stop (set A5+0x10D0 bit6). Otherwise accumulate A5+0x10B2 by
 *      the step; each 8-px crossing streams a new map ROW (0x406A4, dir A5+0x13D0). The Y value
 *      A5+0x10AE is then +step (up, 0x55854) or -step (down, 0x55832), wrapped mod 512.
 *   4. Commit 0x55AB4 writes A5+0x10EC->0xC40000 (X) and A5+0x10AE->0xC40002 (Y).
 *
 * COORDINATE SPACES (PROVEN from 0x461CE actor projection and 0x53A2E collision probe):
 *   actor_screen_y = (actor_world_y + A5+0x10AE) & 0x1FF                     (0x461CE)
 *   collision_grid_row_index = ((( (~A5+0x10AE + 1) & 0x1FF ) + world_y) >> 1) + 8) & 0xFC   (0x53A2E)
 *   => the collision probe uses (world_y - Yscroll) mod 512; visual and collision share the SAME
 *      Y-scroll field A5+0x10AE (identical origin, no separate offset).
 *   map_row (tile) = (Yscroll_px mod 512) / 8, i.e. a 64-tile vertical ring (512 px = 64 * 8).
 *
 * WRAP: both axes wrap the pixel scroll value mod 512 (&0x1FF). PC080SN name table is 64x64 tiles =
 *   512x512 px, so ring_row = (Yscroll & 0x1FF) / 8 in [0,63]. New rows become resident on each 8-px
 *   crossing (step 3) via 0x406A4; new columns via 0x55C4A (H22).
 *
 * SCENE-ENTRY INITIALIZATION (0x504FA, table 0x50850, indexed by A5+0x013E * 12):
 *   word0 -> A5+0x10AE (Y scroll init) and A5+0x10EC (X scroll init)
 *   word1 -> A5+0x10B0 / A5+0x10EE
 *   word2 -> A5+0x10B8 (direction accumulator init)
 *   word4 -> A5+0x10BE (player screen-Y init)
 *   Proven records: prog 2/3 (R1 Phase-2 climb scenes) => Yscroll init 0x0160 (352), screen-Y 0x78 (120).
 *   Scene transition 0x561A0 zeroes A5+0x10AE/0x10B0/0x10EC/0x10EE first, then 0x504FA re-inits.
 *
 * STATE-4 (climb) BEHAVIOR: while the player climbs, movement keeps feeding A5+0x1266 (up), so the
 * step dispenser (0x51880) emits up to 4 px/frame; 0x557BA/0x55854 keep advancing A5+0x10AE UPWARD
 * (mod 512) and streaming rows until the accumulator limit (A5+0x10B8 == 160 with A5+0x10A8 gate) or
 * the screen-Y band clamp stops it. THIRD-CHAIN CONTRACT: from the scene-init Yscroll 0x0160, an
 * upward climb decreases the committed Y toward ~0x010D and keeps moving; a value stuck at ~0x0026
 * means the up path (A5+0x1266 -> A5+0x10DC -> A5+0x10AE += step) is not being driven.
 *
 * PC080SN SEMANTIC CUT (H23 extension of H22):
 *   ARCADE GAMEPLAY DECISION (player motion -> pending A5+0x1266/0x1268, clamp to band [32,304])
 *     -> SEMANTIC foreground Y = A5+0x10AE (mod 512) + logical map row = (Yscroll/8) mod 64
 *       -> PC080SN EXECUTION = write A5+0x10AE to scroll reg 0xC40002 + stream ring rows (0x406A4).
 *   Everything before the cut is preserved in ReROM; only the 0xC40002 write + name-table row walk is
 *   hardware realization. NO Genesis code here.
 */

extern short A5[];

/* Vertical scroll step dispenser (0x51880): cap the pending motion at 4 px/frame. */
unsigned short y_scroll_step(unsigned short pending /*A5+0x1266 or 0x1268*/)
{
    return pending < 4 ? pending : 4;   /* A5+0x10DC */
}

/* Player screen-Y band clamp (0x539C2): keep A5+0x10BE within [32,304], center 80. */
int y_scroll_within_band(unsigned short screen_y /*A5+0x10BE*/)
{
    return screen_y >= 32 && screen_y <= 304;
}
