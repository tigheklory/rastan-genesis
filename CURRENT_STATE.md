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
