# PROMPT-ID-0069 — Green Sword Knight: palette path + all-castle-section contexts

**Author:** Andy · **Date:** 2026-11-03 · **Method:** Ghidra/decompilation-first. No ROM build, no Test.json
change, no palette_decisions.json change, no Cody files touched.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0069`

## TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0069 Result

**RESOLVED.** The visible Green Sword Knight is family-2 base `0x033E`. It is **directly-scheduled, not
marker-transformed**, so its `+0x27` palette line (bit6 set by creation `0x45684`) **survives** and
`0x3C9E8` uses it — the knight's displayed palette is the **creation line**, not the compositor control-byte
line. Lines 4/2 (the c0/c3 variants) resolve to **green** pools; this matches the arcade green armor. The
per-section references below are green-confirmed and were added to the Palette Composer for all six castle
sections.

## Family-2 / Visible-Knight Semantics

- R1-S2 (prog `0x11–0x16`) field schedule (`0x4A104`) spawns **only** family-2 `0x033E` (variants c0/c3/c4);
  not the R1-S1 lizardman roster. `0x033E` appears in every castle section R1–R6 (variants v0→v2).
- Template: base `0x033E`, anim `0x93` → upright sword-knight geometry (matches screenshots).
- Lifecycle (§3): the castle `0x033E` is placed by the schedule as a **direct enemy** and rendered with its
  **creation** attribute. `0x4092E` clears `+0x27` only on a marker-chain *transform*; the castle knight is
  not transformed (R1 markers `'E'` retire, `'M'` is a separate burst; `h14_phase2_visible_bases` has no R1
  entry). So `+0x27` bit6 stays **set** ⇒ `0x3C9E8` returns `+0x27 & 0xF` (creation line), **not** the
  program control-byte nibble (which applies only to transformed actors, e.g. `0x0224`/`0x00F4`/`0x09EA`).
- Rejected identities stay rejected: `0x004B` (lizardman), `0x0A73` (red flame palette).

## Final Arcade Palette Selection Path

1. **Creation** `0x45684`: `nibble = pal_nib_456ec[variant*18 + (round-1)*3 + comp_adj]`,
   `comp_adj=(comp>=3)?comp-2:comp`; `+0x27 |= nibble|0x40` (bit6 marks "use this line").
2. **Display** `0x3C9E8`: `+0x27` bit6 **set** (directly-scheduled knight) ⇒ display line = `+0x27 & 0xF` =
   creation nibble. (bit6 clear, i.e. transformed, ⇒ control-byte nibble — not the knight's case.)
3. **Loader** `0x3BA20`: CRAM line `L` ← pool `0x3BA88[(round-1)*32 + L]`; colors at `0x4FD02 + pool*32`.

**Why my earlier preview looked red:** `compositor_vm`'s tile-index reconstruction for `0x033E` lands on the
non-green indices of the line, so the *preview* mis-colors; the line's *palette data* (below) is green. Per
§6 the ROM palette data — not the preview — is authority.

## Per-section palette references (creation route, green-confirmed)

nibble → pool via `0x3BA88[round]`; GREEN = the pool contains armor-green:

- **R1-S2:** c0 nib4 pool `0x12` GREEN · c3 nib2 pool `0x0F` GREEN · c4 nib1 pool `0x0B` (red/blue default)
- **R2-S2:** c0 nib4 `0x12` GREEN · c3 nib5 `0x10` GREEN · v1/c0 nib2 `0x0F` GREEN · c4 nib1 `0x0B`
- **R3-S2:** c3 nib5 `0x10` GREEN · v1/c0 nib2 `0x0F` GREEN · v1/c4 nib4 `0x12` GREEN · c4 nib1 `0x0B`
- **R4-S2:** v1/c0 nib2 `0x0F` GREEN · c3 nib5 `0x10` GREEN · v2/c0 nib1 `0x1B` GREEN · v1/c4 nib4 `0x13`
- **R5-S2:** v2/c0 nib1 `0x20` GREEN · v2/c3 nib7 `0x19` GREEN · v2/c4 nib2 `0x1C` GREEN · c3 nib5 `0x11` ·
  c4 nib4 `0x13`
- **R6-S2:** v2/c0 nib1 `0x20` GREEN · v2/c3 nib7 `0x19` GREEN · c3 nib0 `0x0B` · c4 nib5 `0x11`

Each distinct `(variant, nibble)` is a palette-distinct variant and is exposed individually (§5/§8); the
non-green ones are real alternate-colored instances of the same knight, not fake variants.

## Palette Composer Integration

Added `green_knight_usages()` in `tools/graphics_editor/server.py`: one semantic object
**`object:castle.green_sword_knight`** named **"Green Sword Knight"**, emitting, per castle section, one
browsable entry per palette-distinct `(variant,nibble)`. Each entry is `scene_key`-tagged to its section
(`PAL-R{n}-S2-PLANEA-CASTLE`), carries the knight frames (geometry from `0x033E`/anim `0x93` + route frames),
and shows **that section/variant's creation-route arcade palette** (16 pool colors) as the authoring
reference. Prepended into `build_usages`; the scene filter shows each entry only in its own castle section.

## Verification

- `verify_green_knight.py` (new): the object appears in all six castle sections with the authoritative
  per-section creation nibble/pool; R1-S2 c0/c3 are green; `Test.json` hash unchanged; no lizardman in the
  knight object. (Results in the commit.)
- Static evidence: `decode_field_schedule.py`, `decode_actor_templates.py`, raw `00045684.c`/`0003c9e8.c`/
  `0003ba20.c`, `h15_materialized_render_palettes.tsv`, direct `maincpu.bin` pool dumps.

## Files / Commits / Logs

- `tools/graphics_editor/server.py` (green_knight_usages), `verify_green_knight.py`, this report,
  AGENTS_LOG. No Test.json / palette_decisions.json / Cody files.

## Remaining uncertainty

- The non-green variants (c4 → pool `0x0B` etc.) are the ROM's alternate-colored knight instances; whether
  all are on-screen in every section is not visually confirmed (schedule-proven, not screenshot-proven).
- `compositor_vm` preview color fidelity for `0x033E` is approximate; the authoring reference uses the
  authoritative pool colors, not the preview.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0069`
