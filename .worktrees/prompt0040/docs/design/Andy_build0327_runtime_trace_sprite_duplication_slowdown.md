# Build 0327 — Runtime Trace: Sprite Vocabulary, Duplication & Slowdown

**Type:** Analysis / runtime verification. No production change, no ROM. Classification: **EXTENDING**. Baseline Build 0327.
**Status:** instrumentation prepared + self-verified; **awaiting Tighe's Build-0327 playthrough** before results sections are filled.

## 1. Phase 0
Priors/hazards: builds on the proven Build-0327 findings — 128-byte cell reindex fix, incomplete `(code,bank)` coverage, cross-bank shared codes (2675–2722, 577–594, 803–809, 1293–1303) requiring a `(code,bank)` variant selector. Deferred (record only): vertical-fill, epoch tile loss, noise band, waterfall animation, HUD red text, axe, cave tiles, garbled-text screen. Contradiction status: none.

## 2. Instrumentation (`tools/mame/scripts/trace_genesis_sprite_provenance.lua`, SHA `67b9a3fd…`)
**Constraint discovered:** MAME Lua here cannot tap 68000 opcode fetches — `install_read_tap` does **not** fire on instruction fetch (verified: tile_dma memory reads worked, execution taps at `.Lnq_emit_entry`/Plane-A publishers never fired), and `cpu.debug` is unavailable. So a clean register tap of `(d3=code, d1=bank)` at the emit boundary is not possible.
**Working approach (producer-boundary, not SAT-only):**
- `install_write_tap` on `pc090oj_tile_dma_worklist` (0xFFB884, 12×{slot,code}) records the **source artwork CODE** for every pattern the native producer uploads, at production time, and builds a persistent slot→code map. (Self-verified: captured HUD codes 43–73 in attract.)
- Per-frame read of `staged_sprite_sat` (0xFFB26C, 80×8B): active pieces, palette-line histogram, tile slot→X/Y → join slot→code → per-piece (code, line, X); duplication = same code at ≥2 X.
- Per-frame `pc090oj_tile_dma_count` (0xFFB8B4) and `fg_row_dirty` (0xFF404A popcount) as sprite-DMA and Plane-A vertical-fill workload proxies.
**Bank resolution:** offline — code → census family → effective bank, with the SAT palette line (0/1) as a cross-check. (The shared cross-bank codes are exactly where code→family is ambiguous — the known finding.)
**Self-test (attract, 88s):** active up to 72, tile_dma 12, fg_row_dirty active, 14 source codes captured — mechanism confirmed. Limitation: patterns resident before capture (or preloaded) have no slot→code entry until re-uploaded, so the per-piece duplication join is partial; the SAT active-count + per-code X-spread remain reliable duplication/workload signals.

Capture metadata + outputs: `states/traces/b0327_provenance/` (ROM SHA `2cb27f47…`, profile SHA `deb696452d7456b3…`).

## 3. Tighe-driven capture window (required)
Fresh Build-0327 start through Round 1 including: opening gameplay, lizardmen, the cave, bats, chimera, four-armed insect, flying demon if practical, the point where the moving-noise band / slowdown appears, and several Rastan actions (stand/walk/jump/attack/climb). Tighe decides when enough is captured.

## 4–9. Results (Tighe playthrough, 11,830 frames ≈ 3.3 min)

**Instrumentation outcome — partial.** The write-tap captured only the HUD digit codes (43–73); enemy/Rastan sprite patterns do **not** flow through `pc090oj_tile_dma_worklist` (they are resident/loaded via a different path at spawn), so **source-code coverage and Rastan's live vocabulary were NOT captured.** The **workload** channels (SAT active count, `tile_dma_count`, `fg_row_dirty`) worked and produced the decisive result below.

**Sprite-count saturation (the headline runtime finding).** Active SAT pieces per frame:
| window | frames | active avg/max |
|---|---|---|
| 0 (opening ~20 s) | 0–1183 | **20.7** / 42 |
| 1 | 1183–2366 | 58.4 / 70 |
| **2–9 (rest of run)** | 2366–11830 | **70.0 / 70 (pinned)** |

The native SAT pins at **70 active pieces for ~85 % of gameplay** (`NATIVE_SAT_MAX` = 80). Normal Rastan gameplay is ~10–30 pieces; a constant 70 is **massive sprite over-emission** — fully consistent with Tighe's "double spritesets offset horizontally" duplication affecting more enemies over time. Sprites are correctly on **Lines 0/1** (l0/l1 both heavily populated), so routing is fine; the problem is *count*.

**Slowdown classification: CONTRIBUTING FACTOR PROVEN = sprite over-emission (SAT saturation).** 85 % of frames run at 70 pieces; the game ramps from ~20 (opening) into a pinned 70 and stays there. Processing ~70 sprite pieces + SAT/DMA every frame is a strong, measured slowdown contributor.

**Noise / vertical-fill: CORRELATION ONLY, and DISTINCT from the slowdown.** `fg_row_dirty` is low most of the time (avg 1–3 bits) and spikes to 32 only intermittently (**3 %** of frames), i.e. during scrolling — this tracks the moving-noise band. Notably, average active is *lower* during high `fg_row_dirty` (56.9 vs 64.2), so vertical-fill and the sustained slowdown are **separate** phenomena. **Noise↔slowdown cause/effect: NOT proven; they are distinct** (slowdown = sprite saturation; noise = intermittent vertical-fill).

**Duplicate provenance (gameplay vs render): NOT PROVEN** from this trace (per-entry SAT positions weren't logged for non-HUD slots because the slot→code join only held HUD codes). The census shows every actor emits a **base form + anim form** record block with overlapping pieces — a strong candidate for *render* duplication (both emitted) — but this needs a corrected per-entry SAT capture to prove.

**Palette-vs-duplication:** unproven (needs per-entry provenance).

## 10. Build 0328 requirements (already established, independent of trace)
`(code,bank)` sprite reindex + bounded O(1) runtime variant selector + complete per-actor `(code,bank)` vocabulary (census + this trace's live confirmation incl. player). Keep Lines 0/1/3 + Layer-A unchanged.

## 11. Follow-ups preserved
HUD `1UP`/score (bank 0x30) → first-class Palette Composer editable representation (author white; no hardcode). Axe → same. Garbled-white-box text screen: recorded, not investigated.
