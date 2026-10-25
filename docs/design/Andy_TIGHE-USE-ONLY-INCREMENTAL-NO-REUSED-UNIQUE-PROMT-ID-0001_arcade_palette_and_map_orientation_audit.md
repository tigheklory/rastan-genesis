# Andy — Arcade Palette & Map-Orientation Audit (PROMPT-ID-0001)

**Agent:** Andy (Opus) · **Date:** 2026-10-25 · **Type:** forensic investigation — **NO fixes applied,
no production code/palette/map/collision/ROM changed.** · **Editor baseline:** RG-022 `e71b837c` ·
**Genesis baseline:** Cody Build 0500. Evidence images: `analysis/rg_audit_0001_evidence/`.

## Executive summary

Two distinct, independently-proven R1-S1-centric assumptions in the shared Plane-A decode explain the
reported problems:

- **ROTATION (records 17/21 castle, and every castle):** the decoder assembles **every** record with
  the horizontal (selector-0) layout. Records 17 and 21 are the only **`selector=1` (vertical-scroll)**
  records in Round 1; rotating record 17 by 90° CCW yields the correct vertical-climb castle. The same
  `record_map` decode feeds Cody's native Genesis pipeline, so this very likely **also causes the
  Genesis vertical-chain climb failure** (shared root cause, HIGH confidence).
- **PALETTE (R2-S1):** the corpus generator decodes the **fixed startup base `0x4EAF6`** (verified
  correct for R1), which is nominally round-independent. The R2 divergence could **not** be reproduced
  with the subround ROMs because they set the stage index but not the round counter (the RG-019 quirk),
  so the exact R2 mechanism is **UNRESOLVED pending a genuine round-2 palette-RAM dump** (specified).
- **R2-S3 "incomplete":** FALSE ALARM — the decoded boss room is complete; the large dark area is
  legitimate repeating wall space.

---

## 1. R1-S2 record 17 — map orientation  [CONFIRMED ROTATED, HIGH confidence]

- **Expected (arcade):** a vertical-climb castle shaft — ladder/chain runs vertically, floors
  horizontal, barred windows in a horizontal row.
- **Editor (as decoded):** `analysis/rg_audit_0001_evidence/rec17_editor_as_decoded_rotated90cw.png` —
  windows stacked in a **vertical** column, ladder hatching **horizontal** (unclimbable).
- **Rotated 90° CCW:** `..._rec17_rotated_ccw90_correct_vertical_climb.png` — windows in a horizontal
  row, ladder vertical, horizontal floors = **the correct vertical-climb layout.** So the editor shows
  record 17 rotated ~90° CW, exactly as Tighe reported.
- **First proven divergence:** `decode_stage_records(mc, 0)` → record 17 has **`selector=1`**; records
  0–16, 18–20, 22 are `selector=0`. Records 17 and 21 are the ONLY selector-1 records in Round 1 — the
  exact two Tighe reports rotated. The STREAM at `0x50F6B` is the scroll **direction** (0/1/2); 1 =
  vertical.
- **Root cause:** `reconstruct_segment` (`tools/audit_round1_phase1_plane_a.py`) /
  `record_map` (`tools/translation/compile_pc080sn_genesis.py:544`) /
  `analyze_graphics.decode_plane_a` build the 64×64 map as `row = SOURCE_TABLE_BASES[row//4] + …`,
  `col = descriptor_column`, **for every record regardless of selector**. `record_map` never reads the
  selector; only Plane-B (`decode_plane_b_progression`, line 224) branches on it. A vertical record's
  backing map is laid out for a vertical camera (the advance axis is rows, not columns); reading it with
  the horizontal addressing transposes/rotates it.
- **Decoded correctly, displayed wrong vs. genuinely mis-decoded?** The *bytes* read are the right
  arcade data; the *assembly orientation* is wrong for selector-1 records. For the editor alone this
  could be masked with a display rotation, but because the same assembly feeds the Genesis name-table
  (§3), the correct fix is at the **decode/assembly** level, not a viewer rotation. **Do not rotate as
  a workaround.**

## 2. R1-S2 record 21 — map orientation  [CONFIRMED ROTATED, HIGH confidence]

Same as §1: record 21 is `selector=1` (with event `6`, a scene-reentry freeze). Same decoder, same
horizontal-layout error → same ~90° rotation. (Record 21 is the second vertical climb / top of the
castle.)

## 3. Relationship to the Genesis vertical-chain climb failure  [HIGH confidence they share a cause]

**Yes — the rotation and the climb failure are almost certainly the same root cause.**

- Cody's native Genesis Plane-A assembly uses `compile_pc080sn_genesis.record_map` — the **same**
  function proven in §1 to ignore the selector-1 vertical orientation. So the Genesis name table for the
  castle climb (record 17, selector 1) is built with the horizontal orientation → the climbable
  geometry (the chain column, the floors Rastan lands on) is **rotated 90° from where the game's
  vertical movement/collision logic expects it.**
- Cody's diagnostic fits exactly: active record 17, selector 1, FG scroll advances `0x0100 → ~0x0166`
  (the camera *is* climbing), Rastan in climb state with Up held, **but further upward movement is
  rejected.** With the map rotated, the tiles that should be the continuing vertical chain/standable
  surface are instead laid along the horizontal axis, so after a short climb the vertical geometry runs
  out / hits a non-climbable cell → movement rejected. The earlier "authentic collision ceiling"
  reading was wrong because the ceiling is an artifact of the rotated map, not real arcade geometry.
- **Prediction to confirm (for Cody):** on Build 0500, the record-17 name table / collision side-channel
  will match the **rotated** `record_map(17)` output, not the CCW-correct layout. Comparing the walkable
  rows the collision side-channel reports against the two orientations will prove it.
- **Confidence:** HIGH that they share the cause; the exact fix (the precise axis transform for
  selector-1 records — transpose vs transpose+flip) must be derived from the arcade scroll producer and
  validated, which is Cody's implementation step. This is the single highest-value finding.

## 4. R2-S1 arcade palette mismatch  [PARTIAL — root cause identified; exact R2 values need a round-2 dump]

- **What the generator does:** `gen_subround_layera_corpus.py` decodes each Plane-A bank's colors from
  the **startup/default base `0x4EAF6 + bank*32`** (0RGB nibble → rgb8). This is the power-on default.
- **Verified correct for R1:** startup base bank 3 = `0869…` → xBGR-555 `4990 414E 390C …` = the **live
  arcade R1 palette RAM** bank `0x003` (MAME dump `states/traces/palram_R1`) = the editor's authoritative
  R1 capture (purple cave rock). All three agree. `decode_arcade_palette_bank(mc, 3, 1)` returns the
  same "startup base @0x4EB56". For banks < 48 this function **always** returns the startup base,
  independent of scene.
- **Why R2 could not be reproduced here:** the `_Sx-y` subround ROMs set the **stage index** (`0x10D242`
  → `0x0017`) but **not the round counter** (`0x10C118` stays `1`, the same RG-019 quirk). A MAME dump
  via the R2 stage-select shows palette RAM **byte-identical** to R1 for all 128 banks
  (`diff palram_R1 palram_R2` = empty). So the per-round palette reload never fires under stage-select,
  and I cannot capture R2's live palette this way.
- **Where the divergence must be (hypotheses, not yet proven):**
  1. Round 2 reloads the Plane-A banks at genuine round entry from a **per-round BG palette source** the
     decoder assumes is the fixed R1 startup base (an R1-centric assumption — §7). Most likely.
  2. R2 tiles select **effective banks 48–79** (scene-selected, published at palette RAM `0x200600`)
     rather than source banks 0–47; those effective banks differ (e.g. live `0x033` = `0842 739C …` ≠
     source `0x003` = `4990 …`). Less likely for Plane-A since R1 Plane-A uses source banks 0–47
     (R1 looks purple = source bank 3, not the brighter effective 0x033).
- **First divergence / evidence NEEDED (Tighe can provide):** a palette-RAM dump at a **genuine Round-2
  playthrough** (round counter `0x10C118 == 2`), banks `0x003..0x00E` of `0x200000`, compared to the
  generator's `plane_palette_banks.json` for `PAL-R2-S1-PLANEA-OUTDOOR`. The first bank whose live R2
  value differs from the startup base is the proof, and identifies whether it is hypothesis 1 or 2.
- **Confidence:** HIGH that the generator uses the wrong (fixed R1) palette source for later rounds;
  MEDIUM on which replacement source is correct until the round-2 dump exists. **This is a reference-
  palette bug in the editor corpus, not Tighe's chosen Genesis palette.**

## 5. R2-S2 (castle)  [shares BOTH problems]

- **Map orientation:** Round 2's only selector-1 records are **43 and 44** (`decode_stage_records(mc,
  23)`), both inside R2-S2 (records 39–44). So R2-S2 has the **same vertical-record rotation** as R1-S2.
- **Palette:** same startup-base assumption as §4 → same provisional/likely-wrong R2 reference colors.
- Every castle in every round will have selector-1 vertical records → the rotation is **systemic to
  castles**, not specific to R1-S2.

## 6. R2-S3 (boss) — "incomplete graphics"  [NOT a defect — complete, HIGH confidence]

- `reconstruct_segment(45)` → **4096/4096 cells non-blank, 64/64 rows and columns used.** The render
  (`rec45_r2s3_boss_complete.png`) shows a complete boss room: central throne/altar doorway with a face
  motif, flanking stairs, columns, snake/medallion decor, and a large upper **dark repeating wall** —
  the tall chamber above the fight. This is **legitimate map space**, exactly Tighe's "apparently
  missing areas are legitimate unused map space." No missing graphics, no wrong record, no layer
  confusion. The "incomplete" impression is the full 64×64 backing map vs the small active arena +
  sprite-occupied space.

## 7. Shared decoder / coordinate-system problems  [the two R1-centric assumptions]

The R1-S1-developed tools bake in two assumptions that are valid for R1 outdoor but not generally:

1. **Orientation:** `record_map` / `reconstruct_segment` / `decode_plane_a` assume **all records scroll
   horizontally (selector 0)**. Selector-1 (vertical) records are assembled rotated. Affects the editor
   display AND Cody's native Genesis Plane-A/collision (the climb). Systemic to all castles.
2. **Palette residency:** the palette decode assumes the **fixed startup base (`0x4EAF6`, banks 0–47) is
   the live BG palette for every round**. True for R1; later rounds reload (mechanism to confirm). A
   single shared misunderstanding of *palette residency over rounds* — not coordinates.

These are two separate shared misunderstandings (one spatial, one palette); they are **not** the same
bug, but both come from "the tools were written around R1-S1."

## 8. Recommended next corrections (separated by owner) — **not implemented, pending Tighe review**

| # | Fix | Owner | Priority | Notes |
|---|---|---|---|---|
| A | Make Plane-A assembly orient **selector-1 records** correctly (derive the exact transpose/flip from the arcade scroll producer, validate against the arcade). Fix in `record_map`/`reconstruct_segment`/`decode_plane_a` so BOTH the Genesis name table and the editor corpus are correct. | **Cody** (native pipeline + climb) owns the decode fix; **Andy** regenerates the editor corpus from it. | **HIGH** | Very likely also fixes the Genesis vertical-chain climb (§3). Confirm against Cody's record-17 collision side-channel. |
| B | Replace the generator's startup-base palette with the correct **per-round/per-scene** Plane-A palette source for later rounds. | **Andy** (editor corpus) | HIGH | Blocked on the round-2 palette-RAM evidence (§4) to pick the right source. |
| C | R2-S3: no action — complete. | — | — | Document as not-a-defect. |

**Do not implement A or B until Tighe reviews and the round-2 palette evidence is captured.**

## Unresolved questions / evidence required
1. The exact arcade axis transform for selector-1 records (transpose vs transpose+flip) — from the
   arcade scroll/strip producer, to confirm the precise rotation for the fix.
2. R2's live Plane-A palette — a genuine Round-2 playthrough palette-RAM dump (§4) to prove the first
   divergence and choose the correct per-round palette source.
3. Confirmation on Build 0500 that record-17's collision side-channel matches the rotated (not CCW)
   map (Cody) — the direct link between the rotation and the climb failure.
