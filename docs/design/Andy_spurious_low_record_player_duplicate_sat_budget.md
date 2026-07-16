# Andy — Spurious Low-Record Rastan Duplicate / SAT Budget Cleanup (Build 0192)

**Date:** 2026-07-16
**Type:** Analysis + bounded fix + before/after measurement.
**Baseline:** Build 0181/256 `1ef9085e…` (default). Produced Build 0192 `42f0b662d0886bbc1a4e1ec5fa2759e9b5c2785911ea404c20dc98b8500eafc1`, size 1,582,860, counter 192, GATE_PASS. Repo mirror default remains 256.

## Primary question — answered: classification **C** (wrong helper at hook_target_45dfa, and hook_target_41dae)
The low-record Rastan duplicate is a Genesis-only artifact from the wrong helper being used at `hook_target_45dfa` AND `hook_target_41dae`: both call the default `pc090oj_workram_block_sprites`, which copies the player block A5+0x11B2 -> records 0..17 (and A5+0x0170 -> 18..21). Arcade 0x045DFA / 0x041DAE do NOT copy A5+0x11B2 (they copy A5+0x508/0x5C8 -> records 57/96/140/46 via 0x3D054). So the low copy is an exact duplicate of what `hook_target_41f5e` already stages to the canonical records 120..137 / 92..95. (Effect overlaps classification E "same block replayed twice"; root is C.)

## State-causality answers
1. Records at this arcade PC/state: the arcade Stage-1 player lives in PC090OJ records **120,121,124,125,126** (codes 009E/009F/008E/008F/0090). Arcade records 0..17 are **empty** at this state.
2. Original arcade routine that creates the player records: 0x041F5E (lea A5@(0x11B2) -> 0xD003C0 = record 120).
3. Why Genesis creates extra low copies: `hook_target_41dae`/`hook_target_45dfa` call the default `pc090oj_workram_block_sprites` (A5+0x11B2 -> records 0..17), duplicating the player. This is a Build 0164 lineage artifact: Build 0164 split the shared helper so 0x041F5E uses the `_41f5e` variant (records 120..137), but left 41dae/45dfa on the default 0..17 base.
4. Does arcade create records 0..17 at this state? **No** (confirmed empty at F1100).
5. Wrong route or necessary effect? **Wrong helper route** — arcade 41dae/45dfa are different routines; the Genesis low copy is spurious.

## Evidence
- Arcade PC090OJ (F1100): records 0..17 empty; player only at 120,121,124,125,126.
- Genesis 256 (F1200): records 0..11 hold the player duplicate (same codes as 120..126); represented from BOTH low (0,1,4,5,6,8..11) and canonical (120..129).
- Producer: writers to records 0..17 = `pc090oj_workram_block_sprites` / `.Lpc090oj_family_apply_record` (33817 writes), called by `hook_target_41dae` (line 474) and `hook_target_45dfa` (line 482). Canonical records 120..137 written at the same rate (33880) by `hook_target_41f5e` -> `_41f5e` variant, so the canonical player is independently maintained every frame (removing the low copy cannot make the player stale).
- Overlap: the low duplicate draws at the same screenX (16..32), palette line 3, hflip=1 as the canonical -> no unique visible pixel; pure redundancy.

## Fix (bounded, gameplay-gated)
`hook_target_41dae` and `hook_target_45dfa` skip the default block copy when `genesistan_current_scene_id == PC090OJ_SCENE_GAMEPLAY_ID (1)`; other scenes keep existing behavior (the low copy is only proven spurious in Stage 1 gameplay, so non-gameplay scenes are left untouched to avoid any high-score/menu regression). Canonical records 120..137 / 92..95 from `hook_target_41f5e` are unchanged. No SAT faking, no forced position, no tile hardcoding, no mirror-size change.

## Before/after measurement (MAME gameplay, matched coin/start, F1200/F1400)
| Metric | BEFORE (0181/256) | AFTER (0192) |
|---|---:|---:|
| represented | 28 | 15 |
| SAT chain slots | 28 | 15 |
| player (pal3) SAT slots | 18 | 6 |
| VINT-service rate (1.0=60Hz) | 0.484 | 0.588 (+21%) |
| vdp_prepare_sprites prep section | 11.67 ms | 10.44 ms |
| records 0..17 gameplay writes | continuous (33817) | 0 |

Player SAT slots 18 -> 6 (matches the arcade's ~5-6 for records 120..126). Total SAT chain halved (28 -> 15). VINT rate +21%. Enemy represented: unchanged (~9 non-player represented before and after) -- enemies still do not spawn (separate frozen-progression root); the freed ~13 SAT slots are now available for them.

## Visual validation (screenshots states/traces/build0181_dup/snap92/)
- Title (F90): RASTAN/TAITO renders correctly.
- READY (F300): ROUND 1 READY renders correctly.
- Stage 1 gameplay (F1200): Rastan on the LEFT, coherent barbarian, sword raised -- identical to Build 0181; no player/BG/FG/palette regression.

## 256/128 equivalence impact
The fix is orthogonal to mirror size (operates on scene-gated hook routing, not record count). 128 and 256 both keep records 120..137 and both apply the same gameplay-gated suppression, so they remain equivalent for the player. Mirror default remains 256; floor 122 (KF-049) unchanged.

## Owner classification summary
- Route creating records 120..137: `hook_target_41f5e` -> `pc090oj_workram_block_sprites_41f5e` (correct, canonical).
- Route creating records 0..17: `hook_target_41dae` + `hook_target_45dfa` -> default `pc090oj_workram_block_sprites` (spurious in gameplay).
- Both routes arcade-faithful? 41f5e yes; 41dae/45dfa no (wrong helper).
- hook_target_45dfa using wrong helper? YES (and 41dae). A faithful re-implementation of arcade 0x041DAE/0x045DFA (records 57/96/140/46) is a separate future task; this fix only removes the proven-spurious gameplay duplicate.
- Low-copy source an address-split artifact from Build 0164? YES.

## Not touched
Build 0175 palette route, 0171/0172 projections, Build 0178 tile-DMA, Build 0180 SAT-dirty gating, configurable mirror mechanism/default 256 — all preserved. No input/collision/enemy-forcing/sky/D00298/continue/Exodus work.
