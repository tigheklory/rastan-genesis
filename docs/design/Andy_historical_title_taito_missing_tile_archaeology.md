# Andy — Archaeology: Historical Missing Red-TAITO Title Tiles + Correct Native Repair Design

**Date:** 2026-10-18 · **Agent:** Andy · **Type:** READ-ONLY historical archaeology + architecture
design. **No** production source/generator/spec/manifest change, **no** ROM, **no** MAME, **no**
trace/route, **no** build number/counter change, **no** implementation. Cody's active title candidate
untouched.

**Baseline:** Build **0446** (counter 446; commit `f9686893` "Build 446 — Fix native title glyph
table mapping"). Scope: the **large red TAITO title logo missing/incorrect-tile** history only. The
malformed 1UP/2UP HUD is **NOT PROVEN RELATED** (see §Related).

**Tool reuse (RULES §18):** reused `tools/translation/gen_native_title.py`, `verify_native_title.py`,
`precompute_pc080sn_tile_lut.py`, the generated `build/pc080sn_tile_vram_lut.bin` and
`native_title_report.json`, `specs/startup_title_remap.json`, `apps/rastan-direct/src/title_native.s`,
and prior reports (`Cody_build_0106_missing_fixed_tiles_attr_flip_inventory.md`, build 0095/0444/0445/
0446 title reports). New tooling: none. No run performed.

---

## 1. EXECUTIVE RESULT

The red TAITO title logo is drawn from **low PC080SN tile codes that collide with the general
punctuation/text font**. Four of those codes (`0x22`, `0x27`, `0x2C`, `0x3F`) are *also* the arcade
punctuation `" ' , ?`. Because a Genesis tile-LUT maps one PC080SN code to exactly one VRAM slot, the
same code cannot be both a punctuation glyph and a TAITO-logo fragment. The **historical workaround**
(now baked into the native pipeline) resolves the four colliding codes by:

1. placing their **TAITO-logo fragment patterns in free Genesis slots `0x0349–0x034C`**, and mapping
   the raw codes there in the tile-LUT; and
2. **redirecting the punctuation** to alias codes `0x2744–0x274B` (their own slots `0x0035/0x0036/
   0x0039/0x003B`), so normal text still gets the punctuation glyphs.

The native title generator preserves this via `TAITO_RAW_TEXT_IDS = (0x12, 0x13)` (do not alias the
two TAITO rows), `TEXT_SPECIAL_GLYPH_MAP` (punctuation → alias codes), and the verifier hard-codes the
four expected cells → `0x0349–0x034C`.

**Why Build 0446's logo is still wrong, and why the verifier still PASSes:** the pipeline fixed only
the **four colliding codes**. The **other ~16 TAITO-logo codes** (`0x23,0x24,0x25,0x26,0x2B,0x2F,
0x3A,0x3C,0x3E,0x5B–0x60`) map to **low slots `0x0001–0x0033`, shared with the general font**, and the
verifier validates **name-table words and a self-consistent reconstruction from the same tile-LUT** —
it **never checks the pattern bytes at those slots**. So if those low slots hold general-font patterns
rather than the logo fragments, the logo renders incorrect tiles while every map-word check passes.

**Correct modern fix (design only):** the Python pipeline must own a **logical→physical allocation for
the whole TAITO logo** (all its fragment codes, not just the four colliding ones), upload the
authoritative arcade logo-fragment **patterns** to generated slots, emit the map words, and the
verifier must validate the **pattern bytes**, not just the words. Retire the hand-split workaround
(`TAITO_RAW_TEXT_IDS` + `SPECIAL_ALIASES` + hard-coded `taito_expected`). **Answer: YES-BUT-GENERATED.**

---

## 2. WHAT THE RED TAITO LOGO ACTUALLY IS

Two historical representations appear in the evidence:

- **Build-0106 era (BG 2×2):** `Cody_build_0106_missing_fixed_tiles_attr_flip_inventory.md` audited a
  red TAITO 2×2 in PC080SN **BG** at rows/cols 21–22 / 23–24, arcade codes **`0x22CB,0x22CC,0x22CD,
  0x22CE`**, attr `0x0001` (color bank 1), no flip, pixel ~184–192/168–176. Those **high** codes mapped
  to Genesis slots `0x0157–0x015A` and **staged correctly** by 0106 (no defect for those four cells).
- **Current native era (Plane-A two rows):** `gen_native_title.py` draws the TAITO logo as **Plane-A
  text IDs 18 and 19** (`TAITO_RAW_TEXT_IDS`), a two-row block of **low** PC080SN codes. This is the
  element Tighe sees wrong in 0446.

The current native-title logo therefore depends on the **low-code** path (rows 18/19), which is the
collision-prone one. The 0106 BG high-code cells are a separate/earlier representation and are not the
current defect.

---

## 3. LOGICAL vs PHYSICAL LAYERS (the central distinction)

For each TAITO cell there are five layers; the workaround made several look like one number:

1. **Original arcade graphic identity** — the TAITO-logo fragment pattern in the arcade PC080SN tile
   ROM.
2. **Logical Genesis title identity** — the PC080SN **code** the arcade writes for that cell (proven
   reached unchanged at arcade `0x03BB48`/`0x03BB68`), e.g. `0x22,0x23,…,0x60`.
3. **ROM/package pattern identity** — the decoded pattern bytes the precompute extracts for that code.
4. **Physical Genesis VRAM tile index** — the slot the pattern is uploaded to (`tile_lut[code]`), e.g.
   `0x0349` or `0x0001`.
5. **Name-table tile index** — the word written into the plane (`slot | attr`).

The workaround collapsed (2)↔(4) for the four colliding codes by **hand-choosing** physical slots
`0x0349–0x034C`, and it never guaranteed (3) (the pattern content) for the non-colliding codes.

---

## 4. EXACT MAPPING (from `build/pc080sn_tile_vram_lut.bin` + `verify_native_title.py`)

TAITO logo cells (Plane-A rows 18/19). "Alias" = the `TEXT_SPECIAL_GLYPH_MAP`/`SPECIAL_ALIASES`
punctuation redirect used by **non-TAITO** text.

| TAITO cell | code | collides w/ punctuation? | tile_lut slot (logo) | punctuation alias code → its slot | verifier-pinned? |
|---:|---:|---|---:|---|---|
| 1489 | `0x22` | yes (`"`) | **`0x0349`** (free) | `0x2745 → 0x0035` | **yes → word 0x0349** |
| 1490–1493 | `0x23–0x26` | no | `0x0001–0x0004` | — | no |
| 1494 | `0x27` | yes (`'`) | **`0x034A`** (free) | `0x2746 → 0x0036` | **yes → 0x034A** |
| 1495 | `0x2B` | no | `0x0005` | — | no |
| 1496 | `0x2C` | yes (`,`) | **`0x034B`** (free) | `0x2749 → 0x0039` | **yes → 0x034B** |
| 1497 | `0x2F` | no | `0x0007` | — | no |
| 1498 | `0x3A` | no | `0x0012` | — | no |
| 1553 | `0x20` (blank) | — | `0x0000` (intended blank) | — | no |
| 1554–1555 | `0x3C,0x3E` | no | `0x0014,0x0015` | — | no |
| 1556 | `0x3F` | yes (`?`) | **`0x034C`** (free) | `0x274B → 0x003B` | **yes → 0x034C** |
| 1557–1562 | `0x5B–0x60` | no | `0x002E–0x0033` | — | no |

Only the **four colliding codes** were given dedicated free slots `0x0349–0x034C`. The **non-colliding
logo codes resolve to low slots `0x0001–0x0033`**, which are the same slots the general title font
uses — these are the cells whose pattern content is unverified and the likely source of "incorrect
tiles."

> Note: the free region `0x0349–0x034C` sits exactly at the gameplay conflict/dense-code boundary
> flagged by OPT-003 (`CONFLICT_CODE_FIRST 0x031A + COUNT 0x0032 = 0x034C`). The hand-chosen TAITO free
> slots abut that boundary — a fragile coincidence that a generated allocator should remove.

---

## 5. WHY THE ORIGINAL SLOTS WERE BLANK / WRONG (first cause)

From `Cody_build_0106_missing_fixed_tiles_attr_flip_inventory.md`: the INSERT-COIN parens (codes
`0x0028/0x0029`) "stage `0x0000` because the Build-0106 tile LUT does not provide nonzero slots for
arcade tile codes `0x0028` and `0x0029`." I.e. the PC080SN tile-LUT precompute's residency/upload set
**did not include the low title-only codes** that collide with punctuation — they resolved to slot 0
(blank). The TAITO logo uses the same class of low codes, so the colliding logo fragments were blank
for the same reason: **the precompute never allocated/uploaded a Genesis slot for those codes**. The
first cause is therefore an **allocation/upload gap in the global PC080SN tile-LUT**, not a palette,
flip, or runtime-overwrite problem. **[DOC 0106; SRC tile_lut]**

---

## 6. WAS THE WORKAROUND MADE AUTHORITATIVE? (yes — in four places)

The relocate-to-free-slots workaround is now embedded in:

1. **`build/pc080sn_tile_vram_lut.bin`** (generated by `precompute_pc080sn_tile_lut.py`): maps
   `0x22→0x0349, 0x27→0x034A, 0x2C→0x034B, 0x3F→0x034C` and uploads those patterns there.
2. **`gen_native_title.py`**: `TAITO_RAW_TEXT_IDS = (0x12, 0x13)` (don't alias rows 18/19) +
   `TEXT_SPECIAL_GLYPH_MAP` (punctuation → `0x2744–0x274B`).
3. **`verify_native_title.py`**: `TAITO_RAW_TEXT_IDS`, `SPECIAL_ALIASES`, and the **hard-coded**
   `taito_expected = {1489:0x0349, 1494:0x034A, 1496:0x034B, 1556:0x034C}`.
4. **`native_title_report.json`**: `taito_raw_text_ids` field (asserted by the verifier to equal
   `["0x12","0x13"]`).

So the workaround is **partly generated** (the tile-LUT allocation) and **partly hard-coded** (the four
cell/word constants, the two alias tables, the raw-id list). It is distributed, not owned by one
authority.

---

## 7. BUILD-0446 RELATIONSHIP + VERIFIER GAP

- **Map owner:** `native_title_fg_map` (generated by `gen_native_title.py` from arcade text IDs 18/19
  via `apply_text`), consumed once by `genesistan_title_present_once` (`title_native.s`).
- **Name words:** the four colliding cells reference slots `0x0349–0x034C`; the rest reference
  `0x0001–0x0033`.
- **Where the patterns come from:** the title scene tile upload driven by the global
  `pc080sn_tile_vram_lut.bin` / title preload. The four free slots are explicitly allocated; the low
  slots are shared with the general font.
- **Build-0446 defect class:** **map references slots whose pattern content is not the TAITO logo for
  the non-colliding codes** (and/or the free-slot logo patterns are not actually uploaded to the title
  VRAM). The map is internally consistent; the **patterns are the unverified layer**.
- **Why the verifier PASSes:** `verify_native_title.py` (a) compares the generated planes to an
  **authoritative reconstruction built from the same `tile_lut`** (so any wrong-pattern mapping is
  reproduced identically in both → no mismatch), (b) hard-checks only the **four** colliding cells'
  **words**, and (c) checks spec/report/source markers. **It never reads the VRAM pattern bytes at the
  referenced slots.** The missing contract is **pattern-content validation**: that slot `0x0349`
  actually holds the arcade `0x22` logo-fragment pattern, that slot `0x0001` holds the `0x23` fragment,
  etc. **[SRC verify_native_title.py:51–167]**

---

## 8. AUTHORITATIVE VISUAL SOURCE

Available and usable: the **arcade PC080SN tile ROM** (`build/regions/*` + the decoders in
`precompute_pc080sn_tile_lut.py`), which contains the real TAITO-logo fragment patterns for the codes
the arcade writes at `0x03BB48`/`0x03BB68` (proven). The logical identities are those arcade codes.
Prefer **arcade pattern data → precompute → generated package**, not the historical hand-chosen free
slot numbers. **[SRC]**

---

## 9. CORRECT MODERN DESIGN (no implementation)

Target ownership chain:

```
authoritative arcade TAITO logo-fragment patterns (PC080SN tile ROM, codes from 0x03BB48)
  -> precompute_pc080sn_tile_lut.py: allocate Genesis slots for ALL title-logo fragment codes
     (colliding AND non-colliding), upload their patterns, emit the code->slot LUT
  -> gen_native_title.py: emit final name-table words from the generated LUT
  -> verify_native_title.py: validate the name words AND the uploaded pattern bytes at each slot
  -> title_native.s: consume generated maps/symbols only (no raw slot literals) [already true]
```

Key changes (for Cody, later):

- **Allocate the whole logo, not four cells.** The precompute should treat the title-logo code set as
  a package and give every fragment a deterministic slot with its correct pattern — so the
  non-colliding codes `0x23…0x60` no longer borrow general-font slots. Ideally per-scene/title-package
  allocation so the title-logo codes never share slots with gameplay/text, dissolving the collision
  instead of hand-patching four cases.
- **Keep the punctuation redirect generated.** The `"'`,`?` aliasing is only needed because title text
  and the logo share code space; if a generated per-scene allocation separates them, the alias tables
  can be derived (or eliminated) by the pipeline rather than hand-listed.
- **Extend the verifier to pattern bytes.** Add a check that each referenced slot's VRAM pattern equals
  the authoritative arcade fragment for that code. This is the contract whose absence lets 0446 pass
  while rendering wrong tiles.
- **No runtime raw indices.** `title_native.s` already consumes `native_title_fg_map`/`bg_map`; keep it
  that way. No "TAITO tile lives in slot 0x034B" knowledge in assembly.

### Should the free-space placement survive?

**YES-BUT-GENERATED (B).** The collision between logo codes and punctuation codes is real as long as
they share one global PC080SN code space, so *some* slot allocation/remap is required — but it must be
**fully allocated and emitted by the Python pipeline** (including the pattern upload and every map
word), not hand-split across `TAITO_RAW_TEXT_IDS` + `SPECIAL_ALIASES` + a hard-coded `taito_expected`.
The *specific* numbers `0x0349–0x034C` have **no architectural significance** and should not survive as
constants. (Not A, because the collision genuinely requires a remap; not C, because nothing requires
those exact historical slots.)

### VRAM constraint

The workaround exists because of a **code-space collision**, not a VRAM-space shortage: every TAITO
code already resolves to a nonzero slot and the four free slots fit. So special placement is required
only to disambiguate shared codes, which a generated per-scene allocation removes. (A full title/
frontend VRAM free-space census is a small follow-up if per-scene allocation is pursued; not required
to accept the design.)

### Future-proofing / authoritative owner

Make **`precompute_pc080sn_tile_lut.py` + its generated `pc080sn_tile_vram_lut.bin`/title preload
manifest** the single authority for logo code→slot allocation and pattern upload, and have
`gen_native_title.py` derive all map words from it. This survives ROM reflow, pattern reordering, and
title-map regeneration with no hand-edited index. Prefer this **existing** mechanism; do not add a
parallel registry.

---

## 10. RELATED / NOT PROVEN RELATED

- **1UP/2UP malformed HUD (0446):** **NOT PROVEN RELATED.** Those are SAT glyph/label elements
  (`static_sat_labels` / `native_frontend_hud_emit`), a different subsystem from the PC080SN plane
  tile-LUT logo path. No historical evidence links them to the TAITO free-slot allocation. Out of scope
  per the task.

---

## FINAL STATUS

Production source modified: NO. Generator modified: NO. Spec/manifest modified: NO. ROM built: NO. MAME
run: NO. New trace/route: NO. Build number consumed: NO. Build counter changed: NO. Cody title work
modified: NO. Phase D: NO. Phase E: NO.
