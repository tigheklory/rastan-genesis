# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0110 — Round-2 arcade palettes (static) + R2-S3 Composer mapping fix

**Author:** Andy · **Date:** 2026-11-08 · **Scope:** Palette Composer tooling + corpus generator only
(no production 68000/Z80 ASM, no build counter, no production ROM, no authored Genesis palette changed).

## Result

The real Round-2 arcade Plane-A palette source was found **statically** in the original program: a per-round
palette **base pointer table at `0x59C9A`**, indexed by `(round-1)*4`. The corpus generator was hardcoding
the Round-1 fixed base `0x4EAF6` for every round, so R2 showed Round-1 colors (teal foliage, black boss-room
bank 2). The generator now resolves the per-round base, and the regenerated R2 corpus matches the arcade
(green foliage, maroon trunk, brown ground; R2-S3 bank 2 no longer black). Round-1 colors are byte-identical.
Separately, the R2-S3 Composer "edits only show in Genesis Target" bug was a missing detail re-render in
`afterChange()`; fixed so palette/mapping edits repaint the mapped tile preview and mapping chips.

## Why the old R2 palette was wrong

Arcade palette RAM is `0x200000` (`hw_refs`). `derive_per_round_palette` had proved Round-1 visible bank 3 ==
the fixed startup base `0x4EAF6`, and the corpus generator reused `0x4EAF6 + bank*32` for **all** scenes. For
Round 1 that is correct; for Round 2+ it reproduced Round-1 colors. Concretely, R2-S1 foliage banks 4/5 are
teal in `0x4EAF6`, and the boss-room bank 2 is literally all-zero (`@0x4EB36` = `0000…`), which is why R2-S3
rendered black. The per-round pool `0x4FD02`/index `0x3BA88` path (`a5+0x1600`) is the **sprite** per-round
palette, not the background (buffer_round1 did not match the proven R1 background) — a red herring.

## Arcade R2 palette loader/descriptor chain (static, from build/regions/maincpu.bin)

```
round counter  a5@(0x118)
  -> per-round base pointer table 0x59C9A, entry = *(0x59C9A + (round-1)*4)        [loader FUN_00059c54]
  -> per-round palette base (0RGB words), converted 0RGB->xBGR555 (nibble*2, B<<10|G<<5|R)
  -> fade buffer 0x10D600  (= a5+0x1600)
  -> FUN_00045d7c fades 32 banks  0x10D600 -> visible palette RAM 0x200000
```

Pointer table `0x59C9A` (verified bytes):

| round | base | note |
|---|---|---|
| 1 | `0x4EAF6` | == the fixed startup base (so R1 is unchanged — explains the proven R1 capture) |
| 2 | `0x4EEF8` | the real R2 palette |
| 3 | `0x4F15A` | |
| 4 | `0x4F51C` | |
| 5 | `0x4F85E` | |
| 6 | `0x4FA80` | |

The loader `FUN_00059c54` reads the round counter, computes `0x59C9A + (round-1)*4`, dereferences the base,
and converts `-1`-terminated 0RGB words into `0x10D600`; `FUN_00045d7c` copies that buffer into `0x200000`.
Each scene's tile palette attribute (`attr & 0x1FF`) selects a bank within the active per-round base
(`base + bank*32`).

## R2-S1 Proven Palette Sources

- Base: **`0x4EEF8`** (round-2). Banks used by records 23–38: `0x003,0x004,0x005,0x006,0x007,0x008,0x009,0x00A,0x00E` (`base + bank*32`).
- Foliage banks 4/5 are **green** (e.g. bank 4 idx12/13 = `#009400 / #005200`); the ground (bank 3) and trunk
  are browns/maroons. Visual render of record 23 matches the supplied MAME screenshot (green canopy, maroon
  trunk, brown cobble ground), vs the old teal.

## R2-S2 Proven Palette Sources

- Base: **`0x4EEF8`** (round-2, same per-round table). Banks `0x00A,0x00B,0x00C,0x00D,0x00F` (records 39–44).
  Provenance is now the per-round base; no silent fall-back to `0x4EAF6`.

## R2-S3 Proven Palette Sources

- Base: **`0x4EEF8`** (round-2). Banks `0x002,0x00A` (record 45). Bank `0x002 @0x4EF38` now decodes to real
  colors (`#D6D6A5` tan, browns, reds) instead of the all-black `0x4EB36` fixed-base slot — this is why the
  R2-S3 arcade source previews were black.

(Some banks legitimately share values across rounds; the fix does not assume every bank is unique — it reads
each bank from the per-round base. The **R2 boss sprite palette** is unchanged and still unauthored: this task
only corrected the Plane-A background provenance, not the boss fade.)

## Corpus Generator Correction

`tools/graphics_editor/gen_subround_layera_corpus.py`: new `_per_round_palette_base(mc, round)` reads the
`0x59C9A` table; the bank loop now uses `round_base + bank*32` (round from `specs/palette_subround_map`),
and each `plane_palette_banks.json` entry's `source` cites the per-round base (e.g.
`per-round base r2 @0x4EEF8 + bank*32 (@0x4EF38)`). Regenerating the corpus is automatic and deterministic;
generated JSON was **not** hand-edited. Round-1 scenes regenerate with identical color values (round-1 base is
`0x4EAF6`); only the `source` label text changed.

## R2-S3 Mapping Bug Root Cause

`afterChange()` (the central post-edit hook) called `renderTarget()`/`renderSource()`/`validate()` but **not**
the active detail renderer. So editing a Genesis color (or mapping) updated the Genesis Target swatches while
the mapped tile preview (`laGenPal` → `effCramAt`) and the source→target mapping chips kept their previous
render. The all-black appearance was compounded by the palette bug (R2-S3 bank 2 was black) — now fixed at the
source. Scope/serialization were already correct (scene-local `context_policies[SCENE]`).

## Composer Mapping Fix

`tools/graphics_editor/app.js`: `afterChange()` now calls `refreshDetail()`, which re-renders the active
Layer-A detail (`renderLADetail`) — or, in map view, the Genesis-mode segment map — and, for sprites, the
sprite `renderMapTable()` + `renderPreviews()`. The Arcade Source preview is bank-addressed
(`/api/render_tile?...&bank=`) and is unaffected by Genesis edits.

## Save/Reload Verification

`tools/graphics_editor/verify_r2s3_mapping.js` (headless DOM shim, **temporary in-memory fixture** — never
touches Test.json/Test_2_0.json): maps an R2-S3 source index to a distinctive Genesis color, verifies
`afterChange()` re-renders the detail, that `effCramAt`/`laGenPal` reflect the edit (mapped index changes,
unmapped index keeps its arcade color), that the mapping is stored scene-local, and that a JSON serialize/reload
preserves both the scoped color and the mapping. 9/9 PASS.

## MAME Visual Corroboration

Rendering R2-S1 record 23 with the per-round base `0x4EEF8` yields green foliage, a maroon/brown trunk, and a
brown cobblestone ground — matching the supplied **GENESIS/ARCADE** Round-2 MAME screenshot — whereas the old
fixed-base render was teal with an orange trunk. Corroboration only; the ROM pointer chain at `0x59C9A` is the
authority.

## R2 Objects Non-Regression

`r2_field_usages` / `r2_boss_usages`, the R2-S2 roster, scene tagging, and `verify_r2_rosters.py` are untouched;
`verify_r2_rosters.py` still 12/12 PASS. The palette fix is independent of the sprite rosters.

## Files / Verification / Safety

**Changed:** `tools/graphics_editor/gen_subround_layera_corpus.py` (per-round base), `tools/graphics_editor/app.js`
(`afterChange`→`refreshDetail`), regenerated `analysis/graphics_optimizer/subround_corpus/*/plane_palette_banks.json`
(R2 colors; R1 label-only). **New:** `tools/graphics_editor/verify_r2_arcade_palette.py` (12/12),
`tools/graphics_editor/verify_r2s3_mapping.js` (9/9).
**Verification:** verify_r2_arcade_palette 12/12; verify_r2s3_mapping 9/9; verify_r2_rosters 12/12;
verify_scene_automap 44; verify_independent_scopes 9; verify_r1s2_castle_browser 15; verify_per_piece_palette 6;
`node --check app.js` OK. Pre-existing, unrelated failures (prior-session palette files, not touched here):
verify_palette_families (LUT SHA vs `Test_2_0.json`/`pc090oj_palsel_lut.inc`) and verify_subround_palette_coverage
check 7 (`palette_decisions.json` migration backup).
**Safety:** no production ASM/ROM/build-counter change; no authored Genesis palette or palette_decisions change;
R1 colors byte-identical; explicit file staging only; no GitHub push.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0110`
