# Andy — Class B Coverage Design: Parens LUT-Alias + TAITO Raw-Low-Code Preload (Design Only)

**Author:** Andy
**Date:** 2026-06-27
**Baseline:** Build 0107 (`dist/rastan-direct/rastan_direct_video_test_build_0107.bin`, SHA256 `4b4a588b1da2ccec6b31cac781bd53627993eaa6170ec013da56f349c99ef1e3`). rastan-direct.
**Scope:** DESIGN only. No source/spec/tool/ROM/build/bookmark/diagnostic/implementation. Outputs: this doc + one AGENTS_LOG entry. Class B (KF-033 / OPEN-019 / OPEN-020) only. Address spaces labeled. Labels: **[OBS]** grounded in build data this task; **[CODY]** Cody runtime evidence; **[INT]** interpretation.

**Address discipline applied:** (1) Code-PC refs via `address_map.json` (glyph renderer `runtime_genesis_pc 0x0003BD48` = `arcade_pc 0x0003BB48` patched_site; FG store worker `genesistan_hook_tilemap_fg_fill 0x0007065E` genesis_only; verified in prior tasks). (2) Tilemap-content (tile codes / VRAM slots / preload / staging offsets) grounded in `build/regions/pc080sn.bin`, `build/pc080sn_tile_vram_lut.bin`, `build/pc080sn_scene_preload_title.bin`, `build/pc080sn_attr_lut.bin` — never via cross-space arithmetic. PC080SN decode: `code = word & 0x3FFF`, `color = attr & 0x01FF`, `flip = (attr & 0xC000) >> 14`.

---

## Phase 0 — Baseline

**Classification:** EXTENDING (OPEN-019 / OPEN-020 / KF-033). **Contradiction:** NONE. **Settled evidence (not re-litigated)** [CODY]: the four TAITO cells write **raw low codes** directly (`0x0022→0xC09746`, `0x0027→0xC0975A`, `0x002C→0xC09762`, `0x003F→0xC09852`); `ROUTINE_0563CE_ENTRY count: 0`; writer attr store `arcade_pc 0x03BB66`, code store `arcade_pc 0x03BB68`, `d2 = 0x00000000` at all four → attr `0x0000`. Therefore **TAITO must preserve raw-low-code intent; do NOT alias TAITO to `0x2745/0x2746/0x2749/0x274B`.**

**Common compose path** [OBS]: `genesistan_hook_tilemap_fg_fill` composes the Genesis cell as `tile_vram_lut[code & 0x3FFF] | attr_lut[attr-bits]`. `attr_lut[0] = 0x0000` (verified) → arcade attr `0x0000` ⇒ Genesis palette line 0, no flip, low priority ⇒ composed cell = the bare slot. Both buckets compose through `attr_lut[0]`.

---

## Bucket A — Parens (LUT-alias only, no preload growth) [OBS]

**Grounding (verified in build data):**
- `tile_vram_lut[0x2747] = 0x0037` (Genesis-VRAM-slot), `tile_vram_lut[0x2748] = 0x0038`. ✓
- Byte-identity (pattern bytes at `(code & 0x3FFF)*32` in `pc080sn.bin`): `tile[0x0028] == tile[0x2747]` → **True**; `tile[0x0029] == tile[0x2748]` → **True**. ✓
- Current gap: `tile_vram_lut[0x0028] = 0x0000`, `tile_vram_lut[0x0029] = 0x0000`.
- `0x2747`/`0x2748` are already in the title preload at slots `0x0037`/`0x0038`; their patterns are in VRAM. [OBS]

**Designed LUT entries (additive, alias to existing slots):**
```
genesistan_pc080sn_tile_vram_lut[0x0028] -> Genesis-VRAM-slot 0x0037   (== slot of 0x2747)
genesistan_pc080sn_tile_vram_lut[0x0029] -> Genesis-VRAM-slot 0x0038   (== slot of 0x2748)
```
- **Preload/slot impact:** NONE. No preload growth, no new slots — the byte-identical patterns already occupy `0x0037`/`0x0038`.
- **Attr/compose:** parens are FG glyphs routed through the glyph renderer + `fg_fill`; compose `slot | attr_lut[0]` = `0x0037`/`0x0038` (palette line 0). No evidence of nonzero attr for parens; `attr_lut[0]` is correct. [INT]

---

## Bucket B — TAITO (raw-code preload + new slots + LUT) [OBS]

**Grounding (verified in build data):**
- Raw tiles `0x0022`, `0x0027`, `0x002C`, `0x003F`: each `tile_vram_lut[code] = 0x0000` (gap); each pattern at `(code & 0x3FFF)*32` in `pc080sn.bin` is **nonblank**; each is **byte-different** from its mapped alias (`0x0022≠0x2745`, `0x0027≠0x2746`, `0x002C≠0x2749`, `0x003F≠0x274B`). ✓
- None of the four is currently in the title preload. ✓

### Current title-scene slot map [OBS]
- Title preload: **841 tiles → 841 distinct slots**, slots `0x0000..0x0348` (0..840), contiguous.
- Slot budget (generator `build_slot_sequence`): `range(0,1004) + range(1280,1440)` = **1164 slots**.
- **Free-for-title slots: 323** (slots 841..1003 and 1280..1439). First free: **841, 842, 843, 844** (`0x0349, 0x034A, 0x034B, 0x034C`).
- Mapped high-code region `0x0034..0x003B` (= `0x2744..0x274B`) is fully used and lies within the 0..840 used range; the paren aliases `0x0037`/`0x0038` are within it. The four new TAITO slots must avoid all of `0x0000..0x0348`.

### Four new slots assigned [OBS+INT]
Assign from the free-for-title range; the **generator's existing conflict-aware allocator is authoritative** (it assigns slots avoiding per-scene collisions and `SystemExit`s on budget overflow). Expected first-free assignment:
```
tile-code 0x0022 -> Genesis-VRAM-slot 0x0349 (841)
tile-code 0x0027 -> Genesis-VRAM-slot 0x034A (842)
tile-code 0x002C -> Genesis-VRAM-slot 0x034B (843)
tile-code 0x003F -> Genesis-VRAM-slot 0x034C (844)
```
- **Collision/budget check:** the four slots are outside `0x0000..0x0348` (existing title preload), outside `0x0034..0x003B` (mapped high codes), distinct from `0x0037/0x0038` (paren aliases), and distinct from each other. Budget: 841 used + 4 new = 845 ≤ 1164 (323 free → ample). ✓ **Budget is clean; no STOP.**
- The exact slot numbers are whatever the regenerated `pc080sn_tile_vram_lut.bin` / `pc080sn_scene_preload_title.bin` emit — Cody verifies the regenerated output matches a conflict-free assignment in the free range; `0x0349..0x034C` is the expected (first-free) result, not a hand-wired literal.

### Designed LUT entries (raw → new slots; NOT mapped aliases) [OBS]
```
genesistan_pc080sn_tile_vram_lut[0x0022] -> new raw slot (expected 0x0349)
genesistan_pc080sn_tile_vram_lut[0x0027] -> new raw slot (expected 0x034A)
genesistan_pc080sn_tile_vram_lut[0x002C] -> new raw slot (expected 0x034B)
genesistan_pc080sn_tile_vram_lut[0x003F] -> new raw slot (expected 0x034C)
```
**Explicitly NOT** `0x2745`/`0x2746`/`0x2749`/`0x274B` (those mapped tiles have different pattern bytes — aliasing would render the wrong glyph). [OBS]

### Preload additions [OBS]
Add the four raw tiles to the title-scene preload, sourcing pattern bytes from `pc080sn.bin`:
```
preload-index +0: tile-code 0x0022, bytes pc080sn.bin[0x0022*32 .. +32) -> slot 0x0349
preload-index +1: tile-code 0x0027, bytes pc080sn.bin[0x0027*32 .. +32) -> slot 0x034A
preload-index +2: tile-code 0x002C, bytes pc080sn.bin[0x002C*32 .. +32) -> slot 0x034B
preload-index +3: tile-code 0x003F, bytes pc080sn.bin[0x003F*32 .. +32) -> slot 0x034C
```
Title preload grows from **841 → 845** tiles (4 tiles).

### Attr / palette decision — **A (with stated dependency)** [OBS+INT]
- attr `0x0000` is **evidence-supported** (`d2=0x00000000` at all four code stores) → PC080SN `color = attr & 0x01FF = 0` ⇒ **color bank 0**; `flip = 0`. Compose through `attr_lut[0] = 0x0000` ⇒ Genesis palette line 0. This is **correct, not assumed**. No red color bank is invented.
- **Red preservation (decision A):** the TAITO red comes from the **raw tile's 4bpp pixel values** (`gfx_8x8x4_packed_msb`) indexing the **title-scene palette under bank 0** (Genesis palette line 0). The Genesis palette is converted offline from the arcade palette **per CRAM entry**, independent of which tiles are preloaded; the arcade renders these cells red under bank 0, so the converted Genesis palette line 0 contains the same red entries. The new raw tiles' pixels therefore index the existing red — same path the already-rendering bank-0 FG content (e.g. the Build 0107 comma `0x2749`, attr 0) uses successfully.
- **Stated residual dependency (does NOT make this B or C):** decision A holds *provided* Genesis palette line 0 actually contains the converted TAITO red at the tiles' pixel indices. This is highly likely (per-entry conversion of the full arcade palette incl. bank 0; bank-0 FG already renders in 0107) and is made an **explicit TAITO validation gate** ("red, not gray"). There is **no contradictory palette evidence** → **decision is A, not C; STOP not triggered.** If the TAITO validation observes gray, *then* it reclassifies to B (a palette-line-0 dependency to handle) — but current evidence supports A.

---

## Shared design

**Existing mapped high-code LUT entries — PRESERVED (unchanged):**
```
0x2744->0x0034  0x2745->0x0035  0x2746->0x0036  0x2747->0x0037
0x2748->0x0038  0x2749->0x0039  0x274A->0x003A  0x274B->0x003B
```

**Six-entry LUT coverage delta (one coherent set):**
```
+ 0x0028 -> 0x0037   (Bucket A, alias, byte-identical to 0x2747)
+ 0x0029 -> 0x0038   (Bucket A, alias, byte-identical to 0x2748)
+ 0x0022 -> 0x0349   (Bucket B, raw, new slot+preload)   [expected slot]
+ 0x0027 -> 0x034A   (Bucket B, raw, new slot+preload)
+ 0x002C -> 0x034B   (Bucket B, raw, new slot+preload)
+ 0x003F -> 0x034C   (Bucket B, raw, new slot+preload)
```
All additive; no existing entry changed.

**Generator vs data-change approach — GENERATOR change (durable), in `tools/translation/precompute_pc080sn_tile_lut.py`:** [INT]
- Root cause [OBS]: `extract_text_writer_tiles` (line ~330) does `mapped = TEXT_SPECIAL_GLYPH_MAP.get(glyph, glyph); text_tiles.add(mapped & 0x3FFF)` — it registers only the **mapped** tile, never the raw low code, for the 8 map keys.
- **Bucket A change:** after slot assignment, for punctuation keys whose **raw low-code tile is byte-identical** to the mapped tile, emit a LUT **alias** `lut[low] = lut[mapped]` (no preload growth). Covers `0x0028`/`0x0029`.
- **Bucket B change:** add the **raw low codes** that are written raw and are **byte-different** from their mapped tiles (`0x0022,0x0027,0x002C,0x003F`) to the **title scene tile set**, so the allocator assigns new conflict-free slots + preload + LUT for the raw tiles (mapped `0x274x` entries remain for genuine text usage).
- Naturally generalizes to all 8 `TEXT_SPECIAL_GLYPH_MAP` keys (also covering the latent `0x0021`/`0x002D` gaps per KF-033) — recommended robust form; scope-validated on the 6 codes here.
- **Direct LUT/preload data edit is rejected** as the fix (non-durable: overwritten on next generator run; risks hand-wired slot collisions the allocator would otherwise prevent). A direct edit could be a *temporary* probe but must not be the committed fix.

**0x563CE — UNTOUCHED.** No change to `0x563CE` runtime behavior; the arcade does not use it for the watched TAITO cells, and the Genesis design does not alias TAITO to mapped forms. [OBS]

---

## Validation plan (parens and TAITO checked separately)

**Parens (Bucket A):**
- `INSERT COIN(S)` parentheses render.
- Staged cells compose to slots `0x0037`/`0x0038` through `attr_lut[0]` (palette line 0).
- **No preload growth** (preload tile count unchanged by Bucket A).

**TAITO (Bucket B):**
- The four magenta cells (FG `(23,17)/(23,22)/(23,24)/(24,20)`, codes `0x0022/0x0027/0x002C/0x003F`) render.
- Staged cells compose to the **four new raw-code slots** through `attr_lut[0]`.
- **TAITO appears RED, not gray** (the decision-A palette gate; gray ⇒ reclassify to B, palette-line-0 dependency).
- **No use of `0x274x` mapped aliases** for TAITO cells (verify `lut[0x0022..]` point at the new raw slots, not `0x2745/0x2746/0x2749/0x274B`).

**General:**
- Strict-target crash remains fixed; no Class A regression; no OPEN-018 raw-write changes.
- Build/invariant deltas predictable: **preload grows by exactly 4 tiles** (841→845); **LUT entries added: exactly 6**; slot allocation matches the regenerated data (4 new slots in the free range, e.g. `0x0349..0x034C`); existing mapped entries unchanged.
- Regenerate via `precompute_pc080sn_tile_lut.py` (the generator's budget check passes — 845 ≤ 1164); confirm `pc080sn_unique_tile_count` / scene budget print shows no overflow.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| TAITO slot collision / budget overflow | 323 free title slots; +4 = 845 ≤ 1164 budget; generator allocator is conflict-aware and `SystemExit`s on overflow — no hand-wired slots; Cody verifies regenerated slot map. |
| TAITO wrong color (gray not red) | Decision A grounded in attr=0 / bank 0 + per-entry offline palette conversion; explicit "red not gray" validation gate; if gray, reclassify to B (palette-line-0 dependency) — do not invent a color bank. |
| LUT generator / data inconsistency | Fix in the generator (single source of truth); regenerate LUT + preload together; reject hand-edited data as the committed fix. |
| Missing one of the six low-code LUT entries | Present as one coherent 6-entry delta (2 alias + 4 raw); validation asserts exactly 6 added and lists each. |
| Accidentally aliasing TAITO to mapped `0x274x` | Bucket B explicitly assigns raw tiles their OWN new slots; byte-difference verified (`0x0022≠0x2745` etc.); validation asserts TAITO slots ≠ `0x0035/0x0036/0x0039/0x003B`. |
| Generalization touches latent 0x21/0x2D | Additive and consistent with KF-033; if scoping strictly to 6, the generator change can gate on the explicit code set — either is safe. |

---

## Open / Closed Issues Impact

- Open issues touched: **OPEN-019** (active — concrete coverage design for parens + TAITO; not closed pending implementation + the red-palette validation gate), **OPEN-020** (active — the comprehensive low-code audit; this design covers 6 of the 8 keys and notes the generalized generator fix covers latent `0x0021`/`0x002D`), OPEN-001 (context — title visual completeness). OPEN-015 not touched.
- New issues opened: NONE.
- Issues closed: NONE.
- Intentionally deferred: implementation; the generalized 8-key generator form (recommended, scope-validated on 6); any palette-line-0 handling if TAITO validates gray (decision B fallback).

## KNOWN_FINDINGS impact

KF-033 reaffirmed and refined: the two fix shapes are now concretely designed — byte-identical low codes (parens) → LUT alias to the existing mapped slot (no preload growth); byte-different raw low codes (TAITO) → raw preload + new slots + raw LUT (never mapped aliases). Root remains the generator's `TEXT_SPECIAL_GLYPH_MAP` registering only mapped tiles. No KNOWN_FINDINGS.md edit required by this design (assess-only).

## STOP triggered

NO.
