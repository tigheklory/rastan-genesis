# CURRENT_STATE (2026-07-20, Stage 1 cave investigation — Build 0228 NOT consumed)

- Rolling UNCHANGED: Build 0227/256 `5ab997f6186bc6cd...` (counter 227). No patch this task.
- PROVEN: the cave is DOWNSTREAM-BLOCKED. Genesis 0227 Rastan cannot pass the FIRST outdoor pit — scroll oscillates, player mode (0xFF10E8) hits MODE 7 at the pit and the camera snaps backward (repeat); occasional mode-8 death->respawn; cave tileset 3 / source >=0xFB1C never reached. Arcade with same input reaches the cave/rope (rope=green vine, cave=pit drop). The Build 0218 cave tileset split exists but is unexercised.
- CONFIRMED (matched collision dumps): genesistan_stage_bg_collision_column diverges — ground-surface markers at collision row 39 (Genesis) vs 38 (arcade) = KF-067 at producer level; AND sparse 2-of-4 columns vs arcade contiguous. Solid floor matches. NOT proven to cause the pit stall -> NOT patched (speculative; KF-067 forbids blind row move). See KF-073.
- STOP: no patch-safe boundary. NEXT STEP NEEDS TIGHE: interactive matched MAME capture (arcade + Genesis 0227) through the pit/cave/rope, logging player mode + collision + progression; automation cannot pass the pit.
- DEFERRED (separate, unfixed): BG vertical-scroll shear; slight perf regression / 68k-Counter opt (later); gray fireball; gray death remnants (owner unproven); gem wrong palette; item-drop coverage; missing axe; missing large bat; small bat green-not-brown; sword hitbox; enemy->Rastan damage; wrong cave tiles; missing cave cover; pit resets; rope art/climb/lava.
- opcode 216; coverage 0x182BC4; builds 0223-0227 preserved.

---

# CURRENT_STATE (2026-07-20, post Build 0227 — N2 plane correctness)

- Rolling: Build 0227/256 `5ab997f6186bc6cd...` (counter 227, 1,584,068) — N1 native sprites + N2 native planes with the 0226 ring rewrite REVERTED. Display stays ON every frame; plane commits use bounded DMA over the proven 0223 coordinate model. Awaiting user hardware acceptance.
- FIXED vs 0226: cyan/white horizontal band (was the ring wrap seam), half-screen FG displacement (was a 32-row coordinate-space error from full-VSRAM vs window-placed producers), wrong terrain blocks. Root: display-off bracket was the ONLY black-bar cause; the 0226 ring was the ONLY band/displacement cause (KF-072).
- PROVEN (MAME): title/throne/story/BEST5/READY clean (no bar); gameplay coherent at rest + horizontal + jump scroll; N1 sprites unregressed. Peak plane+sprite DMA 4,736 B/frame < ~7,600 B VBlank budget; steady ~640 B (SAT) or 0.
- 0224/0225/0226: consumed N2 iterations, preserved. 0219-0227 all present.
- DEFERRED (recorded, not fixed — Cody/Tighe): gray orb/star projectile, sword hitbox, lizard/Rastan damage, projectile ownership/palette, audio, N3 composite merging.
- opcode 216; coverage 0x182BC4. USER MUST VERIFY on hardware/capture: no band, no FG displacement, no bars, coherent scroll, sprites stable, speed retained.

---

# CURRENT_STATE (2026-07-20, post Build 0226 — N2 native planes)

- Rolling: Build 0226/256 `67017c78746fed2f...` (counter 226) — N1 native sprites + N2 native planes (ring rows, display-ON bounded DMA; display-off bracket DELETED). Awaiting user acceptance.
- 0224/0225: consumed REJECTED N2 iterations (preserved; narrow-strip ring-row lesson in KF-071).
- PROVEN: title/READY no bar; gameplay full frames (0223's near-black fall frame class eliminated); N1 sprites stable throughout.
- RESIDUAL (queued next): single-row seam at fixed plane row during gameplay scroll + possible right-edge column staleness; staged-pair deletion (DMA from tall); KF-067 joint retune; N3 merging; audio.
- opcode 216. USER MUST VERIFY: bars gone on hardware/capture, seam visibility, speed.

---

# CURRENT_STATE (2026-07-20, post Build 0223 — N1 residency stabilized)

- Rolling: Build 0223/256 `4bd3e58e78883790...` (counter 223) — N1 native sprite pipeline + stabilized residency; awaiting user acceptance.
- 0219/0220/0222: consumed REJECTED iterations (preserved; lessons in KF-069/070). 0221 = accepted architectural proof (superseded by 0223).
- Residency: 32x4-way code-keyed, reference-protected, emit-on-miss (invisible misses, 0 steady-state drops). Sprite pipeline per KF-069.
- Pending: N2 native planes (black bar, cave defects), N3 composite merging (per-scanline limit) + optional pinned manifests.
- USER MUST VERIFY (Nomad/BlastEm/Exodus): no vanishing tiles, no wrong art, bats, attract, speed retained.

---

# CURRENT_STATE (2026-07-20, post Build 0221 — N1 native sprite pipeline)

- Rolling: Build 0221/256 `60d14fb0f9294631...` (counter 221) — N1 NATIVE SPRITE PIPELINE candidate; NOT yet user-accepted.
- 0219/0220: consumed, REJECTED N1 iterations (preserved; d5-clobber / colbank display-latch lessons in KF-069).
- Sprite renderer: object table (arcade state) -> per-frame ascending emit pass -> double-buffered shadow SAT -> constant 640B display-on DMA; code-keyed residency; mirror/represent engine DELETED. HUD suppression + bank-0x36 palette + KF-067 alignment preserved.
- Planes/PC080SN: unchanged (N2 pending; cave defects remain). N3 pending: composite merging + per-scene residency manifests.
- opcode 216; coverage per gate scripts. USER MUST VERIFY list in the N1 doc (bats, attract, Nomad flicker A/B).

---

# CURRENT_STATE (2026-07-19, post Build 0218 cave-residency candidate)

- Build 0218/256 was produced and preserved: `dist/rastan-direct/rastan_direct_video_test_build_0218.bin`, SHA256 `30a84f86cc34e8dc9861f945138e7aafabe6f072b466fa6d161b8b0e8ed60a95`, size `1,586,184`, counter `218`, config `PC090OJ_MIRROR_RECORDS=256`, `RASTAN_GAMEPLAY_HUD_SPRITES=0`. Rolling ROM is byte-identical to the numbered artifact.
- Build 0217 remains preserved and rejected/incomplete: `dist/rastan-direct/rastan_direct_video_test_build_0217.bin`, SHA256 `c74adc58b3852c5c3a1a39699de26fd6e41ebbb42cbe379e32c08c9b08dcd369`, size `1,583,868`. Do not delete, overwrite, rebuild, or reuse it.
- Build 0218 materializes the corrected split PC080SN cave residency data: cave source LUT coverage is `0x00F91C 404/404` and `0x01011C 414/414`; outdoor gameplay fits at `962` tiles, cave gameplay at `568`, and max scene usage remains `1067/1164`.
- Build 0218 first release invocation stopped before numbered artifact production at the canonical invariant gate (`0x182AFC -> 0x183408`, opcode_replace `216` unchanged); paired invariants were corrected to `0x183408`, then release passed with `GATE_PASS`.
- Automated runtime validation did not reach the Genesis cave source family. Original arcade with the same input envelope reached a cave entrance/drop visual by frame `900`, while Build 0218 remained in outdoor Stage 1/lizard area through frame `12005` (`strip_ptr1100=0x0000D31C`, tileset `1`). Therefore Build 0218 cave visual acceptance is **USER MUST VERIFY**; no cave visual success is claimed from automation.
- No Build 0219 was produced because the validation blocker is a separate gameplay/progression/input/combat delta, not a concrete proven defect in the split cave PC080SN source/tileset boundary.

# CURRENT_STATE (2026-07-19, post Build 0217 STOP)

- Build 0217/256 was produced and preserved: `dist/rastan-direct/rastan_direct_video_test_build_0217.bin`, SHA256 `c74adc58b3852c5c3a1a39699de26fd6e41ebbb42cbe379e32c08c9b08dcd369`, size `1,583,868`, counter `217`, config `PC090OJ_MIRROR_RECORDS=256`, `RASTAN_GAMEPLAY_HUD_SPRITES=0`. Rolling ROM was byte-identical at production time.
- Build 0217 is **not accepted as the cave-fix artifact**. It was produced before the PC080SN generated-data dependency gap was discovered, so its cave-source LUT coverage still matched stale Build 0216-era data.
- Proven cave root boundary: the runtime Stage 1 descriptor table at `arcade_pc/ROM 0x03951C` continues after outdoor attr `0x0002` into cave/interior attr `0x0003` sources `0x00F91C` and `0x01011C`; Build 0216-era generator/gate omitted those sources. Pre-fix cave LUT coverage was `1/404` and `0/414`.
- Source is staged for the corrected split PC080SN residency model: outdoor gameplay set fits at `962` tiles, cave gameplay set fits at `568`, and naive combined outdoor+cave exceeds budget at `1422/1164`. Touched source assembles (`out/scene_load.o`, `out/tilemap_hooks.o`), but no corrected numbered ROM was produced after the STOP boundary.
- Next ROM-producing task must preserve Build 0217 and use the next authorized build number. Required validation: matched arcade/Genesis cave state, cave visual screenshots, outdoor regression, Build 0216 IRQ/bat-swarm continuity, player/lizard/collision/VBlank checks.

# CURRENT_STATE (2026-07-19, post Build 0215)

- Rolling ROM: Build 0215/256 `dist/rastan-direct/rastan_direct_video_test_build_0215.bin`, SHA256 `10e5307fae240ae418b31b66df0cabe267785a3cd5e68d08f69a21e7b740e99d`, size `1,583,868`, counter `215`. Rolling ROM is byte-identical to the numbered artifact.
- Build config: `PC090OJ_MIRROR_RECORDS=256`, `RASTAN_GAMEPLAY_HUD_SPRITES=0`. Builds 0207-0214 remain preserved/consumed as previously recorded; Build 0214/192 is comparison-only and not the gameplay baseline for 0215.
- Build 0215 restores Stage 1 FG horizontal source progression: `genesistan_stage_fg_src_column` now consumes the arcade-owned rebuilt PC080SN pointer table at `Genesis_WRAM 0x00FF1040` and source-column index `a5@0x10CA`, rather than recomputing a static source from the folded destination column.
- Evidence: `states/traces/build0215_fg_progression_restoration_20260719_153538/`. Scripted right-held MAME comparison shows Build 0213 and 0215 pre-boundary hashes match at frames 429/1000, then post-boundary hashes diverge at 1400/1800; screenshots show the old repeated lower-floor pattern is no longer simply replayed.
- Still open/deferred: gray/wrong lower-block content, black display band, lizard combat/damage, splat/item palettes/scroll, bat palette, record 132, collision-map row-base/player retune, broader Stage 1 terrain visual correctness.

# CURRENT_STATE (2026-07-19, post arcade Ghidra reference)

- Arcade whole-game static reference created under `analysis/ghidra/rastan_arcade/` (docs/design/Cody_full_arcade_ghidra_disassembly.md). Original MAME `rastan` / World Rev 1 maincpu image SHA256 `4f30b9e7aa946aa33d20e125a1726ff094f9615980107d0842efe1721cf32063`, reset vector `arcade_pc 0x03A000`, SP `arcade_WRAM 0x10DE00`.
- Ghidra project: `analysis/ghidra/rastan_arcade/ghidra_project/rastan_arcade_world_rev1.gpr`; exports: `analysis/ghidra/rastan_arcade/exports/`.
- No ROM build/source/spec/runtime change from the Ghidra task. Counter remains 214; rolling ROM remains Build 0214 SHA `1c51a28e453a7f628a8691490ecb96f875b309ba8801fc5b6833b03b04ffac96`.

# CURRENT_STATE (2026-07-19, post Build 0214)

- Candidates: Build 0213/256 `4cb766d5...` (lizard alignment fixed; validated) and Build 0214/192 `1c51a28e...` (mirror comparison; drops 47/99 lizard records — expect missing lizards). Rolling ROM = 0214 (per task); counter 214.
- 0211/0212: consumed, REJECTED (engine d2/d3 clobber -> WRAM corruption; preserved). 0207 consumed/lost.
- opcode_replace 215; coverage 0x182B00.
- Working: control/jump/attack, lizard staging + palette (bank36->line0) + vertical alignment (0213), HUD suppression, record 46.
- Pending Tighe (Nomad): 0213 foot alignment, 0213-vs-0214 flicker, kill-a-lizard, bat palette.
- Known deferred: collision-map row-base root (+player retune), death-splat palette, dropped-item palette/scroll, lizard damage, black bar, record 132.

---

# CURRENT_STATE (2026-07-19, post Build 0210)

- Rolling ROM: Build 0210/256 `6dbe8ec35c04f52dcca503e6958c1da5bf622bd6a6fee9409d87e14c22b7806e` (counter 210), NOT yet visually accepted.
- Build 0208/0209: consumed, REJECTED in-task iterations (preserved in dist). Build 0207: consumed/artifact lost.
- Config: PC090OJ_MIRROR_RECORDS=256; RASTAN_GAMEPLAY_HUD_SPRITES=0 (0210) / default 1.
- opcode_replace 215; coverage 0x182AD4.
- Working: control/jump/attack, lizard staging (blocks 0x2C8/0x748), lizard palette (bank 0x36 -> CRAM line 0 carrier), gameplay HUD-sprite suppression, record 46, player sprites.
- Pending Tighe verification: lizard visuals on Exodus/Nomad, bat-swarm palette, kill-a-lizard.
- Known deferred: lizard damage/Y-alignment, rolling black bar, bat palette confirmation, record 132, sky-reset/progression, window/white HUD.

---

# CURRENT_STATE.md

## Build Numbering Correction (Current)

- Build 0207 is treated as **produced/consumed and artifact-lost** per Tighe's
  correction and `docs/design/Cody_emergency_build0207_artifact_recovery.md`.
- No recoverable `dist/rastan-direct/rastan_direct_video_test_build_0207.bin`
  was found in the workspace recovery search.
- `build/rastan-direct/build_counter.txt` is corrected to `207`; the next
  ROM-producing build must be Build 0208.
- `build/rastan-direct/consumed_build_numbers.txt` records `0207` so the
  release guard can reject counter rollback/reuse.
- Do not delete, overwrite, rebuild-over, or reuse consumed numbered builds.

## Build 0094 Baseline (Current)

- **Current valid ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0094.bin`
- **SHA256:** `558c88b39b359af7ee1f2cee1fa2318dde34b20ebfab7d25e25c0a18e0a819e2`
- **Current phase:** graphics completion for title/attract.

## Proven Working State

- Build 0094 contains the Option B FG cell-composition fix at runtime `0x707DA` / `0x707DC` / `0x707E0`.
- FG store `0x70794` now writes composed nonzero cells during title entry: 213 nonzero `%d1` stores out of 258.
- Producer `0x3ACAE` and first render `0x3ACB6` execute in the title-entry trace.
- `tilemap_hooks.s` stale-object build integrity is fixed by forced assembler object rebuilds.

## User-Visual Working Observations

- Title/attract progression reaches visible output.
- Text renders.
- Large TAITO logo partly renders.
- Credits work.
- Coin/start input works.

## Not Working / Deferred

- Sword/logo artwork is absent.
- TAITO logo is incomplete / missing tiles.
- Text persists between attract states.
- Scrolling/item page shows rows of dots.
- Gameplay start reaches the exception handler; crash triage is deferred and must verify real fields from WRAM because OPEN-015 makes on-screen crash fields suspect.
- Build 0094 does not currently run on real Genesis hardware (OPEN-017).

## Next Step

Run a graphics-only diagnostic for Build 0094 title/attract completion. The next task is not the gameplay exception: first classify missing/incomplete visuals through producer -> staging -> clear/dirty -> VBlank commit -> tile-pattern availability -> palette -> plane/priority/scroll.

---

## Historical / Superseded Content

The content below predates the Build 0094 baseline and is retained only as historical context.

# CURRENT_STATE.md

## Status

### Working

- Arcade vblank execution
- Block-A population
- SAT staging
- DMA transfer

### Not Working

- Visible sprites
- Tile correctness
- Palette correctness

---

## Current Phase

Transition from prototype to final architecture

---

## Next Step

Replace C helper with opcode/vblank-driven commit
