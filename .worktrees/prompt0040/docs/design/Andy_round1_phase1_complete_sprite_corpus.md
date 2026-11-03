# Andy — Round 1 / Phase 1 Complete Original-Arcade Sprite Corpus (PARTIAL + armed capture, 2026-08-25)

Analysis/artifact only. NO production change, NO ROM, Build counter 313, Build 0314 not consumed.
**ARCADE-ONLY**: maincpu.bin, pc090oj.bin, real emitted PC090OJ records, MAME `rastan` source. NO Genesis anything.

## 1. Phase 0
- Relevant KNOWN_FINDINGS: KF-1214/1220 (sprite palette source buffer/bank 0x36; ARCADE), KF-050/051 (player
  block A5+0x11B2 -> records 120-137; ARCADE ownership fact, Genesis-dup portion forbidden here), KF-060/061
  (compositor 0x3D054/0x3C902; ARCADE). Palette loader FUN_0003ba20/56/64 (accepted last task).
- HIGH hazards: reuse accepted enemy pipeline + palette loader; do NOT re-derive. Do NOT reuse unverified
  compositor-table addresses.
- Task classification: EXTENDING.
- Open/Closed impact: OPEN-024/026/027 remain deferred (production). No closure of production issues.
- Contradiction: No CONFIRMED/STRONG contradiction.

## 2. Evidence boundary (decisive)
The saved trace `flying_demon_trace/observations.csv` captured only **5 actor blocks** (actor_2c8/508/5c8/748/8c8).
It did **NOT** capture the PLAYER block (A5+0x11B2), HUD (records 0-45), or item/weapon blocks. Therefore
PLAYER / WEAPONS (sword, Flame Sword, Flail) / AXE + item pickups / HUD sprites cannot be reconstructed from it.
Per the user's decision: close the captured world-sprites now, and ARM a new capture for the rest.

## 3. Accepted enemy baseline (reused, unchanged)
Lizardman 0x36, Four-armed 0x3A, Valkyrie 0x32, Chimera 0x34, Flying Demon 0x35 (A=body/B=wings, wings behind),
Small Bat 0x3E, Large Bat 0x3E — round-1 index 0x3BA88 -> pool 0x4FD02, FUN_0003ba64, MAME pal5bit. See
`enemies.json`/`enemy_palettes.json`. sprites.json enemy `compositor_status` reconciled to COMPLETE (real records).

## 4-14. Captured producers closed (sprite_census_captured.json; r1p1_all_sprites.png)
21 producers across the 5 blocks, real palettes, PC090OJ lower-record-on-top priority:
- **ENEMY (7)**: the accepted seven.
- **ENEMY_FORM (5)**: 0A73 anim frames of Lizardman/Four-armed/Chimera; 0275 forms of Flying Demon and Large Bat.
- **HAZARD (3)**: cave-entrance block **0x0179 = PC090OJ SPRITE** (bank 0x3C, rec1, renders as brick);
  **swinging rope/chain 0x00F4** (bank 0x30, rec5 = Section 6/Record 5); **Boulder 0x0D5F** (bank 0x3C, rec5).
- **PROJECTILE (3)**: 0x050B (spear/mace, bank 0x33), 0x019D (fireball/orb, bank 0x34), 0x02E8-748 (bank 0x3A).
- **EFFECT (3)**: 0x0A5A glow orb (bank 0x30), 0x0275-748 burst (bank 0x3E), 0x0A73/3e08 Valkyrie burst (bank 0x30).
Names marked `user_verify` are visual IDs (structural ownership + real composite + real palette proven; the
semantic NAME awaits Tighe). Cave-entrance block is a SPRITE (not PC080SN terrain) — proven by real emitted records.

## 15-19. Coverage/palette/priority
Complete cell/pattern coverage per producer (all trace cell codes + SHA-1) in `sprite_census_captured.json`.
Palette per producer via the accepted round-1 loader; banks seen: 0x30,0x33,0x34,0x35,0x36,0x3A,0x3C,0x3E.
Palette stability for these banks: covered by the accepted enemy census (stage-load, no gameplay override) — extend
to 0x30/0x33/0x3C in the armed-capture analysis. MAME RGB = pal5bit(nibble*2). Priority = lower record on top.

## 20. Contact sheets
`contact_sheets/r1p1_all_sprites.png` (categorized), per-producer `census_*.png`. Tool:
`tools/graphics_optimizer/render_r1p1_sprite_census.py`.

## 21. NOT captured -> ARMED CAPTURE required (blocker to total coverage)
PLAYER (all R1/P1 states), normal sword, Flame Sword, Flail, AXE + item pickups, HUD/UI. Prior evidence: the AXE
is a specialized-type actor (compositor 0x3C9E8, attr from a4@39; docs/design/Andy_complete_native_graphics_retirement_STOP.md).
Instrument: `tools/graphics_optimizer/r1p1_full_sprite_capture.lua` (full OBJ RAM 0..255 + actor/player blocks).
Runner: `tools/graphics_optimizer/run_r1p1_full_capture_wsl.sh`. Tighe plays R1/P1 (coin 5/start 1), triggering the
axe pickup, each weapon, the swinging rope, and the cave, then closes MAME to flush.

## 22. Open/Closed Issues Impact
None changed. OPEN-024/026/027 remain deferred.

## 23. Next boundary
Analyze the armed full capture -> close PLAYER/WEAPONS/ITEMS/HUD -> total R1/P1 sprite corpus -> then Genesis optimization.

## 24. Armed full capture analyzed (2026-08-26)
Tighe played R1/P1 (full_capture/: 16778 frames, 131005 distinct emitted records, 2081 owner states).
Full OBJ-RAM sweep + player/HUD blocks closed the previously-missing classes:
- **PLAYER = Rastan**, emitted records **120-131, bank 0x33** (30+ cell codes: idle/walk/jump/crouch/attack/thrust).
  Rendered with per-piece palette (records mix bank 0x33 body + bank 0x30 sparkle). `player_rastan.png`, `player_poses.png`.
- **Weapons**: the blade is drawn inside Rastan's attack composite (bank 0x33). Both the **normal steel sword**
  (pose strip) and the **Flame Sword** variant (`player_rastan.png`, flaming blade) were captured. Names user_verify.
- **Sword sparkle effect** = records 132-133, bank 0x30.
- **HUD** = records **0-45**, banks 0x30/0x33 (score/text/1UP cells spread across the screen top; not one composite).
- Confirmed Flying Demon 57-69 (body) + 70-82 (wings) bank 0x35; enemies 140-239 (banks 0x30/32/34/36/3A).
- New enemy producers observed (not yet classified): actor_2c8 base 0x0234, 0x0236, 0x0266, 0x0DAB.
Per-piece palette (each PC090OJ record uses its own word0 nibble | colbank) is the general-correct rule and is now used.
Master sheet: `contact_sheets/r1p1_all_sprites_master.png`. Summary: `sprite_corpus_r1p1.json`.

### Still open (targeted follow-up, not guessed)
Flail equipped variant; Axe pickup + item pickups as distinct ground-item actors (may not all have been triggered);
classification of the 4 new enemy producers. These need a targeted pass over full_capture or a note of which items Tighe collected.
