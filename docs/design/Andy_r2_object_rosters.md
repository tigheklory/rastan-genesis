# Round 2 Object rosters — R2-S1 field + R2-S3 boss

**Date:** 2026-11-08 · **Author:** Andy · **Scope:** `tools/graphics_editor/` (Palette Composer tooling only —
NO ROM / build number / Z80 / 68000 ASM change; arcade captures read-only)

## Request (Tighe)

Cody made Round-2 progression work, so R2-S1 / R2-S2 / R2-S3 now function in the Palette Composer. Tighe asked
to populate Round 2 "using the same methods we used to populate Round 1," and (scoping answer) to **also
reverse-engineer the R2 Objects rosters**, the way R1-S2 / R1-S3 got dedicated roster RE.

## Starting state (already done by the generator pipeline)

The Layer-A / background + palette scaffolding for R2 was already generated and committed (commit `4d449e18`)
and regenerates **byte-identically** against today's rebuilt regions. So the "same generator methods as
Round 1" were already applied to R2; the only real gap vs Round 1 was the **Objects (enemy/actor) roster**:

| Scene | Before | After |
|---|---|---|
| R2-S1 OUTDOOR | shared R1 field census only (PENDING, substitution-flagged) | **64 usages / 8 objects** scene-tagged |
| R2-S2 CASTLE | 47 usages (green knight $033E + castle $0224) | unchanged (already populated) |
| R2-S3 BOSS | 0 (PENDING) | **2 objects** (boss body + aux) |

## Proven evidence consumed (no new RE loop, no fabrication)

Per the project's build-on-existing-work mandate, the roster membership is anchored to evidence already in the
repo, not re-derived:

- **`analysis/enemy_sprite_lexicon/dynamic_signature_map.json`** — the captured `round|subround|slot|base|anim`
  signatures. `round2_phase1` → actor_2c8 bases **$004B, $0400** (+ compositor-2 $0A5A/$0A73); `round2_boss`
  → base **$061D** (body, comp1 anim $01) + actor_748 aux **$0275**. (The R2 boss reuses the same $061D boss
  program as the R1 boss.)
- **Field schedule table `0x4A104`** (installer `0x4A086`), block `= (0x13E-round)>>1`, decoded by
  `tools/analysis/decode_field_schedule.py`, cross-checked against the family base tables `0x45502` (var0) /
  `0x45562` (varN). The R2-S1 OUTDOOR band (`0x13E` = `0x18..0x27`) schedules families **0/1/3/4/8/11**
  (bases $004B/$00D0/$02E8/$0420/$0241/$0400); the castle band (`0x28..0x2d`) schedules family 2 (the knight,
  already covered by `green_knight_usages`) + family 5 — so family 5 is **R2-S2, not S1** and is excluded.

## What was built (`tools/graphics_editor/server.py`)

Two new scene-tagged roster producers, wired into `build_usages()` next to the R1 producers, mirroring
`r1s2_castle_usages()` / `r1_boss_usages()`:

- **`r2_field_usages()`** — R2-S1 OUTDOOR. One browsable multi-frame object per proven field base, scene-tagged
  `PAL-R2-S1-PLANEA-OUTDOOR`, round 2, with the Round-2 per-round arcade palette. Frames come from a new
  **`_r2_field_frames()`** picker that ranks for a **coherent single-enemy** preview (tight bounding box + rich
  tile count over compositors 0/1 across the real animation range) instead of `_castle_frames`' busiest-frame
  ranking — each base renders its **own** tiles ($004B→~$4D, $0420→~$422 …), so frames are base-faithful. The
  two dynamically-captured frames ($004B comp0 anim $00, $0400 comp1 anim $01) are guaranteed present and
  labeled "(dynamic capture)". Compositor-2 specials ($0A5A/$0A73) do not statically decode, so they are honest
  **incomplete** nodes with no fabricated art.
- **`r2_boss_usages()`** — R2-S3 BOSS, scene `PAL-R2-S3-PLANEA-BOSS`, round 2. Body = base **$061D** comp1
  anim $01 (renders a real boss figure); aux = base **$0275** (boss sub-component, captured frame minimal →
  marked **partial**, no fabricated pose). **Palette is PENDING**: the R1 boss used a ROM-proven target table
  (`0x4708C`, Cody PROMT-ID-0095); the R2 boss reuses $061D but its per-round fade is **not** independently
  proven here, so no colors are asserted and the group is **not authorable** (no invented colors).

`tools/graphics_editor/scene_sprite_coverage.py` now reads the dynamic signature map and reports R2-S1 / R2-S3
as a new honest status **`ROSTER_CAPTURED`** (roster built from the capture + schedule; frames provisional,
boss palette PENDING), clearing their old PENDING/substitution banner. R2-S2 stays `SCHEDULE_ONLY`.

## Verification

- `tools/graphics_editor/verify_r2_rosters.py` (NEW): **12/12 PASS** — membership anchored to the proven
  capture/schedule, composites render multi-piece, comp2 specials incomplete, boss body proven + palette
  PENDING + not authorable, R2 boss bases ⊆ the dynamic capture, nothing auto-claims authorable.
- `verify_scene_automap` (44), `verify_r1s2_castle_browser` (15), `verify_independent_scopes` (9),
  `verify_per_piece_palette` (6): PASS. `node --check app.js`: OK. `scene_sprite_coverage` regenerates with
  `ROSTER_CAPTURED: 2`.
- Rendered proofs (scratchpad, not committed): R2 boss body = a real robed trident-wielder; R2-S1 field leads =
  coherent 48×48 single-enemy sprites, base-distinct tiles.
- **Pre-existing, NOT caused by this task** (both key off files from the prior palette session that this task
  never touched): `verify_palette_families` (LUT `pc090oj_palsel_lut.inc` SHA vs the working-tree-modified
  `Test_2_0.json`) and `verify_subround_palette_coverage` check 7 (`palette_decisions.json` migration backup).

## Scaffolding / removal plan

**None.** Durable, reusable tool code only (two roster producers + one frame picker in `server.py`, a coverage
status in `scene_sprite_coverage.py`, and a committed `verify_r2_rosters.py`). No production ROM, build number,
Z80/68000 ASM, capture, or palette registry (`specs/palette_decisions.json`) was touched; arcade captures
remain read-only; the compositor-VM render is the same provisional source-of-truth path the Bestiary and R1
rosters already use. Palette colors remain Tighe-authored (R2 boss fade stays PENDING). Nothing to remove.
