# Andy — Build 0317-0319 Layer-A Color Path Proof + Fix

**Type:** runtime verification / implementation. EXTENDING. Pattern compiler NOT changed. Line 2 protected.

## Build-0316 user result
Patterns mostly correct; palette/colors wrong (Rastan wrong palette; cave/water wrong; some correct tiles
next to green wrong tiles). 0316 realized Layer A on the FG carrier line (line 1), not the authored Line 3.

## Root cause (proven from source)
Plane-A name-word palette line comes from `palette_route_lookup` (`palette_route_table`, palette_hooks.s).
0316 routed FG bank 3 -> line 1 and sprites bank 51 -> line 3. So Layer-A tiles selected line 1 while line
3 held sprites -> wrong colors. Classification: **L/C (palette-line + CRAM ownership), not pattern (P).**

## Fix implemented (0317 -> 0319)
- `palette_hooks.s`: `PROUTE_FG_LINE` 1->3; route table FG bank 3 -> **line 3**; sprites bank 51 -> **line 0**
  (off line 3). Layer B (bank 48 -> line 2) untouched.
- `vdp_comm.s`: the gameplay-VBlank path stages the precompiled `editor_layera_palette` (the exact 15 editor
  words) onto CRAM **line 3** during scene 1 (0318 via the reassert unconditionally; 0319 adds a direct
  forced copy into `staged_palette_words` line 3 + `palette_dirty` right before `vdp_commit_palette`, which
  commits all 4 lines). Precompiled CRAM words only; no runtime conversion. Pattern bytes unchanged from 0316.

## VERIFICATION — corrected
My genesis CRAM probe injected coin/start but the scene histogram showed **scene 0 for all 1000 frames** —
the game never entered gameplay (scene 1), so it was reading the attract/title palette, NOT gameplay. The
editor palette is staged only in scene 1. My earlier "editor palette not in live CRAM" reading was therefore
invalid (wrong scene). Tighe confirms the authored palette IS present once the game is coined up and started.
A gameplay-reaching CRAM probe (the epoch gate reaches scene 1 via symbol-driven install; my simple input
injection did not) is the correct future verification.

## Builds
- 0317: route table Line-3 change.
- 0318: reassert stages editor palette to line 3 unconditionally in scene 1.
- 0319: + direct forced editor-palette publish to CRAM line 3 each gameplay VBlank. **USER TEST CANDIDATE.**
All: seven-epoch gate PASS, 30s MAME no crash, Layer B (line 2) intact, pattern compiler unchanged.

## USER MUST VERIFY (in actual gameplay — coin up + start)
1. Layer-A terrain (exterior/cave/water) now uses the editor Line-3 palette.
2. The green/wrong neighboring-tile issue is resolved (or, if some remain, they are the 64 (code,bank)
   pattern variants — a separate pattern task, not this palette-routing fix).
3. Layer B unchanged. Sprites/HUD may be wrong (sprites moved to line 0 for this checkpoint).
