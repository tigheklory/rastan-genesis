# Andy/Fable — Lizard Composite Vertical Alignment + Mirror-192 Comparison (task 0211/0212 → delivered **0213/256** + **0214/192**)

**Date:** 2026-07-19
**Trace dir:** `states/traces/lizard_vertical_alignment_mirror192_20260719_132947/`

## ⚠ Build-number deviation (honest report)
Two in-task iterations failed after receiving numbers (both preserved as rejected diagnostics):
- **Build 0211** `bbd3428b7304f9da2061bbac98ff03a20b068ee6fdb3e96c329bd2bf5dc20f4a` — REJECTED: the −8 loop read its count from d2 **after** the expansion engine call, but the engine counts d2 to 0 → dbra ran ~65535 iterations walking backward through WRAM applying −8 to every (addr%8)==2 word → global state corruption.
- **Build 0212** `5b028a4943ee579b7a8d560686d5ff4696b9b6572fdf6fa5043bcab85febe89c` — REJECTED: latching the budget in d3 also fails — the engine clobbers d3 (byte-fetch register) → same wild loop.
- **Build 0213/256** `4cb766d5866dd2950e8b177c961549e3819bc98c5ecbddd56c2f6d3050d6316b` (1,583,872, counter 213) — **corrected alignment candidate** (budget latched on the STACK, clobber-proof). GATE_PASS.
- **Build 0214/192** `1c51a28e453a7f628a8691490ecb96f875b309ba8801fc5b6833b03b04ffac96` (1,583,872, counter 214) — 192-mirror comparison, identical source. GATE_PASS. Rolling ROM = 0214 (byte-identical), per the task's rolling requirement for the 192 release.
No numbered ROM was deleted or overwritten. 0207 remains consumed/lost.

## Test environments
1. MAME + original arcade Rastan romset (`-rompath roms`) — authoritative position reference.
2. MAME + Genesis Build 0210/256 (`6dbe8ec3…`) — pre-fix baseline.
3. MAME + Genesis Build 0211/0212 (rejected iterations), 0213/256, 0214/192.

## Objective A — rendered 8-pixel difference PROVEN, and its origin
**Rendered pixel measurement** (PNG analysis, lizard = green-dominant pixels, ground = rock-red band top):
| | foot_bottom | ground_top | foot vs ground |
|---|---|---|---|
| ARCADE (authoritative) | **129** | 129–130 | ON ground (±1) |
| Genesis 0210 (pre-fix) | **137** | 130–131 | **+7..8 into the ground** |
| Genesis 0213 (fixed) | **129** | 130–131 | ON ground (±1) — arcade-identical |

**Divergence chain (all Y values verified at matched states):**
- Actor world-Y a4@(0x1E)=0x4B, camera fields (A5+0x10B0=0x149, A5+0x10BA=0x49, A5+0x218=0x130): **identical** arcade vs Genesis.
- Actor screen anchor a4@(0x1A): arcade **0x79** vs Genesis **0x81** (+8) — the actor STATE grounds 8 low.
- **Root:** full 8KB collision-map diff (arcade WRAM 0x0010DE00..0x0010FE00 vs Genesis WRAM 0x00FF1E00..0x00FF3E00, matched frames): the Stage-1 ground band words (0x3400/0x3A00…) sit at **arcade map row 38 vs Genesis row 39** — the Genesis-produced collision map (`genesistan_stage_bg_collision_column`) carries the ground **one 8px row lower** than arcade. Enemies ground on this map → 8 low; the visible BG and the player's tuned path are correct, so only map-grounded actors show the offset. (Also observed and recorded: a one-word X-edge difference at map column 0 — leftmost wall word missing on Genesis; X-direction, not part of this fix.)
- Composite engine, staging, decode, and SAT are faithful (they propagate the displaced anchor exactly; SAT geometry pre/post fix identical except Y).

## Objective B — correction boundary
Per the task boundary (and because re-basing the collision map itself would move the player's tuned contact — forbidden), the correction is at the **block-A5+0x02C8 composite-producer boundary** in `pc090oj_stage_block2c8` (pc090oj_hooks.s): after each validated actor's engine call, a uniform **−8** is applied to the Y field (low 9 bits, high bits preserved) of exactly the d2 records the engine emitted. Blank-fill and preserved windows untouched; internal component spacing preserved (uniform shift); actor collision/ground state untouched (stays self-consistent with the Genesis map); Rastan, record 46, bats, projectiles, HUD records, and all other PC090OJ families untouched. The record-count latch is on the **stack** (the engine clobbers d0–d7 — the KF-worthy lesson from the two rejected iterations).
The durable root (map row-base one row low + its player-path compensation) is recorded as the proper future fix; touching it was out of scope because it moves the player.

## Build 0213/256 validation (MAME)
GATE_PASS; config 256 + HUD sprites disabled; bank 0x36 → line 0 intact (CRAM line0 = `08CC 0020 0082 0060 00C6…`); lizard colors correct; **feet at arcade elevation (129 vs arcade 129)**; Rastan correct position/colors (SAT L3=9); multiple lizards spawn (lizrep 9→24); player controllable (walk/jump/attack inputs; mode transitions); record-46 route unregressed; rep 18→33, wait 0, producer_oob 0, SATn == rep (no representation loss at 256); coverage 0x182B00, opcode_replace 215 (unchanged).

## Build 0214/192 comparison (MAME, identical source; only PC090OJ_MIRROR_RECORDS=192)
- Counter advanced normally 213→214; rolling ROM = 0214 byte-identical.
- **Structural result: mirror 192 cannot hold the lizard composite span (records 140..238).** The family-apply OOB guard drops records 192..238 → **47 of the block's 99 records dropped every frame** (producer_oob climbing ~47/frame, 6.7k→14.2k in the window); only the group at records 180..191 partially survives.
- Measured: lizrep 0→2 (vs 24 at 256); rep 9→12; wait 9→12; SATn=15; Rastan intact (L3=9); palette intact; player controllable; record 46 represented.
- Flicker: trivially lower only because most lizard sprites never exist. **192 sacrifices most lizard bodies** — the Nomad comparison should expect missing/partial lizards in 0214.

## Deferred observations recorded (not investigated)
Gray lizard death-splat palette; dropped-item palettes; dropped items not scrolling to collectible positions; lizard→Rastan damage; hurry-up-bat palette; additional enemy palette-bank routes; rolling black bar; record 132.

## USER MUST VERIFY (Sega Nomad)
1. **0213/256:** lizard feet stand ON the visible ground (arcade-like), not sunk ~8px.
2. **0213/256:** lizard colors still correct; Rastan position/colors unchanged; kill a lizard.
3. **0213 vs 0214:** compare real-hardware flicker under multi-lizard load — note 0214/192 will show FAR FEWER lizards (most composite groups dropped by the 192 cap), so judge flicker only on what renders, and treat 192 as non-viable for lizards unless flicker gain is decisive.
4. Report whether the death-splat/dropped-item issues reproduce for their own follow-up tasks.

## Files changed
apps/rastan-direct/src/pc090oj_hooks.s (yalign block in pc090oj_stage_block2c8); tools/translation/postpatch_startup_rom.py + verify_canonical_rom.py (coverage 0x182AD4→0x182B00 paired); this doc; ledgers.
