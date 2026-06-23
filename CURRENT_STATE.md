# CURRENT_STATE.md

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
