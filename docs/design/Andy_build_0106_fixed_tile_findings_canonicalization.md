# Andy — Build 0106 Fixed-Tile Findings Canonicalization + Original-Audit Blind-Spot Verification

**Author:** Andy
**Date:** 2026-06-26
**Build:** 0106 canonical (`dist/rastan-direct/rastan_direct_video_test_build_0106.bin`, SHA256 `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`). rastan-direct.
**Scope:** EVIDENCE / DOCUMENTATION only. No source/spec/tool/ROM/build/bookmark/diagnostic changes; no fix design; no implementation. Allowed doc updates: KNOWN_FINDINGS.md, OPEN_ISSUES.md, CLOSED_ISSUES.md, AGENTS_LOG.md, this note. All instruction-PC correlation via `build/rastan-direct/address_map.json` (no ±0x200 as authority). Address spaces labeled explicitly. Labels: **[OBS]** observable (verified this task); **[INT]** interpretation.

---

## Phase 0 — Baseline

**Classification:** EXTENDING (OPEN-001). **Context:** OPEN-005 (BlastEm HV/port-8 fatal class), OPEN-016 (embedded-pointer relocation), OPEN-017. **OPEN-015 not touched.** **Contradiction:** NONE with the proven Build 0106 evidence; this note **supersedes** the Build 0095 "red TAITO = BG block staging issue" attribution for the *exact magenta cells* (see §4). Priors respected: KF-010, KF-013, KF-014, KF-028, KF-029.

**Independently verified this task (not merely restated from Cody docs):** the LUT/preload binaries, the `TEXT_SPECIAL_GLYPH_MAP` mechanism, the paren-vs-TAITO byte-identity, and all instruction-PC mappings below.

---

## 1. Two-class taxonomy (canonical)

The Build 0106 fixed-tile defects separate into two distinct, independently-verified classes:

- **Class A — raw copied PC080SN write bypassing Genesis staging.** A verbatim-copied arcade `move.w #imm,0xC0xxxx` executes as a raw Genesis 68000 write into VDP-mirror space. Strict targets (BlastEm/Nomad/real HW) fatal; the cell never reaches staging. *Same defect class as the Build 0106 PC080SN scroll-RAM clear (0x3AF3C) HV crash.*
- **Class B — low-code FG glyph/symbol LUT coverage failure.** The cell **is** correctly routed through the glyph renderer + FG staging helper, but the direct tile LUT maps the low arcade glyph/symbol code to slot `0x0000`, so the staged word is blank. **No crash** (the write is routed); the symptom is a missing glyph.

---

## 2. Class A — confirmed instance: story comma/special glyph [OBS]

| Item | Value |
|---|---|
| Writer (runtime_genesis_pc) | `0x0003ACEA` |
| JSON segment | `0x03AB20..0x03AD00`, kind `arcade_copy`, arcade_start `0x03A920` |
| arcade_pc (JSON) | **`0x0003AAEA`** (verified: `0x3A920 + (0x3ACEA − 0x3AB20)`) |
| Instruction | `move.w #0x2749, 0x00C09172` |
| HW_ADDRESS | `0x00C09172` (PC080SN FG region) |
| PC080SN decode | FG row 17, col 28; attr `0x0000`; code `0x2749`; color bank 0; no flip |
| Tile mapping (Build 0106) | tile `0x2749 → Genesis slot 0x0039` (LUT[0x2749]=0x0039, verified) |
| Failure | raw write to HW_ADDRESS bypasses staging → strict-emulator/HW crash class; cell never staged |

The tile pattern is fully preloaded (slot 0x0039); the defect is purely that the write is **raw, not routed**. This is the same class as the canonicalized scroll-RAM raw-fill crash. **Guardrail:** do not "fix" by NOP/suppression — route the arcade intent (write tile 0x2749 at FG row17/col28) into FG staging. [OBS+INT]

---

## 3. Class B — low-code FG glyph/symbol LUT coverage failure

### 3a. Root mechanism (verified) [OBS]

`tools/translation/precompute_pc080sn_tile_lut.py` builds the LUT (`lut[arcade_tile] → slot`, 0 = unmapped). Its `extract_text_writer_tiles` walks the 0x3BB48 text-writer descriptor table and applies `TEXT_SPECIAL_GLYPH_MAP` *before* registering tiles:

```
0x21→0x2744  0x22→0x2745  0x27→0x2746  0x28→0x2747
0x29→0x2748  0x2C→0x2749  0x2D→0x274A  0x3F→0x274B
```

It registers only the **mapped** tiles (0x2744–0x274B), assuming the runtime applies the same 0x563CE punctuation mapping. Glyph bytes **not** in the map are identity-registered. **Verified in the binaries:**
- `build/pc080sn_scene_preload_title.bin` low-code (<0x40) tiles present: `0x20,0x23,0x24,0x25,0x26,0x2B,0x2E,0x2F,0x30..0x3E`.
- **Missing exactly:** `0x21,0x22,0x27,0x28,0x29,0x2C,0x2D,0x3F` — i.e. **precisely the 8 keys of `TEXT_SPECIAL_GLYPH_MAP`.**
- `LUT[0x0022]=LUT[0x0027]=LUT[0x0028]=LUT[0x0029]=LUT[0x002C]=LUT[0x003F]=0x0000`; `LUT[0x2745..0x274B]=0x0035..0x003B`.

> **Whenever the runtime stages the RAW low code (not the mapped 0x274x), the LUT returns 0 → blank.** The 8 affected codes are exactly the map keys; the 6 confirmed-failing codes are a subset, and **0x21 ('!') and 0x2D ('-') are latent gaps** (LUT=0, not yet observed failing). [OBS]

### 3b. INSERT COIN(S) parens — low-code alias/LUT omission (NOT a preload gap) [OBS]

| Code | LUT | Byte-identical alias | Alias LUT slot |
|---|---|---|---|
| `0x0028` `(` | `0x0000` | **`0x2747` (pattern bytes equal — verified)** | `0x0037` |
| `0x0029` `)` | `0x0000` | **`0x2748` (pattern bytes equal — verified)** | `0x0038` |

The paren glyph **patterns already exist in VRAM** (slots 0x37/0x38, via the preloaded aliases). Only the LUT entry for the low code is missing. **Do not call the parens a preload gap.** They route through the glyph renderer + FG staging helper; the staged word is blank solely because `LUT[0x0028]/LUT[0x0029]=0`. [OBS]

### 3c. Red TAITO magenta cells — low-code FG glyph LUT failure, may need preload+LUT [OBS]

Four exact user-marked magenta cells (`build_106_missing_TAITO_logo_tiles_highlighted_in_magenta_hex_code_#ff00ff.png`), HIGH-confidence two-context coordinate reconciliation:

| Target | Layer | FG row/col | Attr HW_ADDRESS | Code HW_ADDRESS | Attr | Code | Tile | Color | Flip |
|---|---|---|---|---|---|---|---|---|---|
| A | FG | 23,17 | `0x00C09744` | `0x00C09746` | 0x0000 | 0x0022 | 0x0022 | 0 | none |
| B | FG | 23,22 | `0x00C09758` | `0x00C0975A` | 0x0000 | 0x0027 | 0x0027 | 0 | none |
| C | FG | 23,24 | `0x00C09760` | `0x00C09762` | 0x0000 | 0x002C | 0x002C | 0 | none |
| D | FG | 24,20 | `0x00C09850` | `0x00C09852` | 0x0000 | 0x003F | 0x003F | 0 | none |

- All four route through the opcode-replaced glyph renderer (runtime_genesis_pc `0x0003BD48..0x0003BD7C`, JSON: patched_site, arcade_pc `0x0003BB48`; the span the prompt cites as arcade `0x0003BB66/0x0003BB68`); actual FG store is `runtime_genesis_pc 0x00070952` (genesis_only). Adjacent visible anchors take the same path and stage nonzero. [OBS — mappings JSON-verified]
- `LUT[0x0022]=LUT[0x0027]=LUT[0x002C]=LUT[0x003F]=0x0000` → staged blank.
- **Distinct from the parens:** these low codes are **NOT byte-identical** to their mapped-punctuation tiles (verified: `0x0022≠0x2745`, `0x0027≠0x2746`, `0x002C≠0x2749`, `0x003F≠0x274B`), and each has its **own nonblank pattern** in `build/regions/pc080sn.bin`. So even though the mapped tiles (0x2745/0x2746/0x2749/0x274B) are preloaded, their patterns are the wrong glyph (ASCII punctuation, not the TAITO logo fragment). **The TAITO half may require preload/slot coverage of the low-code tiles themselves *in addition to* LUT entries — do not assume LUT-only.** [OBS]

**Refuted for these exact four cells** (see §6): not the BG `0x22CB..0x22CE` block; not raw/unrouted; not no-op/suppression; not mirror/flip; not attr/flip loss.

---

## 4. Task 1 — original-audit blind-spot verification

**Verdict: CONFIRMED** — the original Build 0095 analysis was blind to the low-code FG glyph cells. The blind spot is **dual-mechanism**:

**(i) Wrong-cell / wrong-layer scope.** `Cody_build_0095_arcade_title_tile_usage_audit.md` scoped the "red TAITO logo" to the **BG block** `0x5B0B2` geometry, rows 18–19 / cols 13–14 → tile codes **`0x22CB,0x22CC,0x22CD,0x22CE`** (PC080SN BG C-window, block-copy path), and resolved Fork **B** (codes preloaded+LUT-assigned; failure = BG block-copy staging/dirty). The **actual** magenta-missing cells are **FG low-code glyphs** (`0x0022,0x0027,0x002C,0x003F`) on the **glyph-renderer / FG staging path** (store `0x70952`) — a different layer and a different writer. The 0095 audit never examined the FG glyph path for these cells. This is the coordinate/layer-reconciliation hazard (now KF-034). [OBS]

**(ii) Reliance on the preload/LUT generator's coverage assertions, which embed the mapping assumption.** The 0095 audit's "present in title preload / assigned in LUT" columns came from `precompute_pc080sn_tile_lut.py` output. That tool applies `TEXT_SPECIAL_GLYPH_MAP`, so the 8 raw low glyph codes are absent from the preload and `LUT=0` (§3a). The audit's "no undercount" conclusion was true **for the BG block source `0x5B0B2`** it examined, but the tool's mapping assumption silently drops the low-code FG glyphs, and the audit never reached the path where that bites. [OBS]

**Answers to the Task-1 sub-questions:**
1. *Did 0095 rely on the same LUT/range assumption that maps low codes to 0?* PARTIALLY — it derived TAITO codes from arcade BG geometry (`0x5B0B2`), not the LUT, but it took its preload/LUT *coverage assertions* from the tool that carries the mapping assumption, and never audited the FG glyph codes. [OBS]
2. *Did the manifest include alias tiles 0x2747/0x2748?* **YES** — both are preloaded (slots 0x0037/0x0038); the tool registers them via `0x28→0x2747`, `0x29→0x2748`. [OBS]
3. *Did it omit direct low-code entries 0x0022/0x0027/0x0028/0x0029/0x002C/0x003F?* **YES** — all six (and 0x21,0x2D) are absent from the preload and have `LUT=0`. [OBS]
4. *Why?* **Reused defective LUT/mapping assumption + range/scope miss:** the shared preload/LUT generator applies `TEXT_SPECIAL_GLYPH_MAP` and registers only mapped punctuation tiles; the 0095 title audit scoped TAITO to the BG block and validated only those codes, never auditing the FG low-code glyph path where `LUT=0` produces blanks. [OBS+INT]

**Classification: CONFIRMED** (not overclaimed: the 0095 audit did not look at the low codes and trust a bad LUT result — it never looked at them at all, while relying on a tool whose mapping assumption drops them). Recorded as durable process guardrail KF-035.

---

## 5. Coordinate reconciliation (method that succeeded) [OBS+INT]

The correct magenta-cell identification required **two independent transforms before comparison**, validated by adjacent visible anchors:
- Build 0106 rendered screen → Build 0106 staged FG row/col (Genesis display scroll/origin/title positioning).
- Arcade rendered title position → arcade PC080SN FG row/col (arcade PC080SN scroll / visible-area / title positioning).

The earlier wrong-cell audit applied naive pixel→row/col on the **BG** block (`0x22CB..0x22CE`); the correct audit used the two-context transform + anchors and landed on **FG** low-code glyphs. Canonicalized as KF-034.

---

## 6. Refuted/bounded hypotheses for the exact four magenta cells

- **Mirror/flip — REFUTED:** attr `0x0000`, no flip bits, no H/V flip relationship; unique low-code glyphs (`0x0022,0x0027,0x002C,0x003F`). [OBS]
- **No-op/suppression — REFUTED:** original writer is the glyph-renderer span (arcade_pc `0x0003BB66/0x0003BB68`; runtime `0x0003BD48..0x0003BD7C`, patched_site arcade `0x3BB48`); actual store `0x00070952`; historical NOP/suppression sites (e.g. CLOSED-003) do not match these writers. Failure is a blank LUT result, not suppression. (Historical no-op/suppression precedent exists, but not for these cells.) [OBS]
- **Earlier BG `0x22CB..0x22CE` audit — BOUNDED, not closure:** those BG cells stage correctly, but they are **not** the exact visually-missing magenta cells. Bounded evidence, not closure for the visual TAITO symptom. [OBS]

---

## 7. Documentation actions taken (this note + ledgers)

- **KNOWN_FINDINGS.md:** added **KF-032** (raw PC080SN writes must route through staging — Class A, consolidating the scroll-RAM raw-fill class + the story-comma instance), **KF-033** (low-code FG glyph/symbol LUT coverage gaps — Class B), **KF-034** (two-context coordinate reconciliation for rendered-cell audits), **KF-035** (process guardrail: tile usage/preload audits must derive "what should render" from arcade tilemap/runtime intent, not Genesis-side LUT/staging results — Task-1 confirmed).
- **OPEN_ISSUES.md:** added **OPEN-018** (route raw story-comma write 0x3ACEA), **OPEN-019** (repair low-code FG glyph LUT coverage), **OPEN-020** (comprehensive low-code FG glyph audit, all 8 map keys).
- **CLOSED_ISSUES.md:** added **CLOSED-012** (TAITO mirror/flip refuted), **CLOSED-013** (TAITO no-op/suppression refuted), **CLOSED-014** (earlier BG `0x22CB..0x22CE` audit bounded/superseded for the visual symptom).
- **AGENTS_LOG.md:** one summary entry.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 (active — TAITO/paren symptom reattributed to Class-B low-code LUT failure; not closed), OPEN-005 (context — Class A is the same strict-crash family), OPEN-016/OPEN-017 (context). OPEN-015 not touched.
- New issues opened: OPEN-018, OPEN-019, OPEN-020.
- Issues closed: NONE (CLOSED-012/013/014 are refuted-hypothesis / bounded-evidence records, not OPEN-issue resolutions).
- Intentionally deferred: the actual routing fix for the story-comma write; the LUT/preload repair; per-line-scroll work; implementation (all design/fix work out of scope for this evidence task).

## STOP triggered

NO.
