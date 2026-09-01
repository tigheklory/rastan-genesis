# Build 0331/0332 — Partial-Dynamic Line 2 Regression Fix + Bank-0x30 Audit

**Type:** Analysis / Runtime verification / Implementation. ROM produced (Build 0332). Classification: **EXTENDING**. Baseline Build 0330; working reference Build 0328.
**Result:** Layer-B Line-2 per-segment progression **RESTORED** while retaining event-driven Test ownership and no per-frame reassert. Bank-0x30 explosion relocation **DEFERRED** (no authored mapping).

> Build note: 0331 was an intermediate candidate (a first fix attempt targeting the wrong producer, `45dae`, which left Line 2 frozen). The proven fix targets `59ad4`; the delivered numbered ROM is **0332**.

## 1. Phase 0
- **Relevant findings:** KF-010 (BG→Plane B / FG→Plane A); KF-011 (arcade VBlank owns progression); the Build-0329 event-ownership work. HIGH-hazard priors honored (no VBlank ownership added, Line 2 semantics preserved).
- **Deferred (untouched):** Rastan/bats `(code,bank)` colors, HUD score/`1UP` (bank 0x30) + Axe first-class Palette Composer, waterfall animation, vertical-noise, late partial lizardman, epoch/cave/Segment-7.
- **Classification:** EXTENDING. **OPEN/CLOSED impact:** improves OPEN-006 palette ownership; none closed/opened. **Contradiction status:** none (Build-0330 "whole-hook suppression safe" assumption was corrected by runtime evidence, as anticipated).

## 2. Build-0330 regression
Build 0330 removed the every-VBlank Test reassert (correct) but gated `genesistan_palette_hook_59ad4` and `_45dae` **off entirely** during scene 1. That suppressed the arcade producer that loads the gameplay Layer-B (Line 2) palette, freezing the sky at its frontend values.

## 3. True segment-boundary Line-2 producer (PROVEN)
`genesistan_palette_hook_59ad4` (arcade `0x59AD4`) is the gameplay/segment palette producer. After its specific bank remaps (0x33→line3, 3→line1, 0x36→cache), banks 0/1/2 fall through and stage positionally at `line = bank`, so **arcade bank 2 → Genesis Line 2** — the gameplay sky loader. `45dae` (the `0x045DB8→0x3A2D0` copy) does **not** load gameplay Line 2 (proven: allowing its Line-2 writes in scene 1 left the sky frozen). `3ba64` bank 48 → Line 2 is the *frontend* loader and does not run for Line 2 during gameplay.

## 4. Build 0328 vs 0330 trace (states/traces/build0331_line2/)
Tool: `tools/mame/scripts/trace_line2_progression.lua` (coin=P1 A, start=P1 Start, walk=P1 Right; logs 16 Line-2 words + Lines 0/1/3 checksum on change). Write-taps do **not** fire under MAME's DRC 68000 (KF-019 class), so provenance was established by read-sampling + elimination, not write-taps.

| | Build 0328 (working) | Build 0330 (broken) | Build 0332 (fixed) |
|---|---|---|---|
| scene→1 (f322) Line 2 | frontend `0000 0000 0008 004E…` | frontend | frontend |
| gameplay sky load (~f387) | `0000 0642 0644…0CC0` | **never (frozen)** | `0000 0642 0644…0CC0` (=0328) |
| sunset step (~f1561/1579) | `…066A…0E26 08EE 0E68 0AA8` | **never** | `…066A…0E26 08EE 0E68 0AA8` (=0328) |
| Lines 0/1/3 (l013 checksum) | Test `0xC480` | Test `0xC480` | Test `0xC480` |

**First divergence:** classification **B — Build-0330 gate suppressed the legitimate gameplay Line-2 operation** (`59ad4` bank 2 → Line 2).

## 5. Line-2 entry-by-entry table (Build 0328/0332)
| Index | Frontend | Gameplay sky (f387) | Sunset (f1561) | Dynamic? | Bank-0x30 effect uses? |
|---:|---:|---:|---:|---|---|
| 0 | 0000 | 0000 | 0000 | no | (raw, not enumerated) |
| 1 | 0000 | 0642 | 0642 | no | " |
| 2 | 0008 | 0644 | 0644 | no | " |
| 3 | 004E | 0644 | 0644 | no | " |
| 4 | 008E | 0646 | 0646 | no | " |
| 5 | 00EE | 0644 | 0644 | no | " |
| 6 | 08EE | 0868 | 0868 | no | " |
| 7 | 0EEE | 0668 | **066A** | **YES** | " |
| 8 | 0A00 | 066A | 066A | no | " |
| 9 | 0E40 | 068C | 068C | no | " |
| 10 | 0E80 | 068E | 068E | no | " |
| 11 | 0EC0 | 0AAC | 0AAC | no | " |
| 12 | 0EEA | 0E00 | **0E26** | **YES** | " |
| 13 | 0000 | 0AEE | **08EE** | **YES** | " |
| 14 | 0000 | 0E80 | **0E68** | **YES** | " |
| 15 | 0000 | 0CC0 | **0AA8** | **YES** | " |

**Dynamic (sunset) index set = {7,12,13,14,15}. Stable = {0,1,2,3,4,5,6,8,9,10,11}.** Layer B is partial-dynamic, exactly as modelled. (Only the first sunset step was captured in this window; the dynamic set is those five entries.)

## 6. Implementation (Build 0332)
`palette_hooks.s`, three producers, all context-gated on `genesistan_current_scene_id == 1`:
- **`59ad4`** — replaced the whole-hook scene-1 skip with a **per-destination gate at `.L59_dest_ready`**: in scene 1 stage **only** the Line-2 target (`d0==2`), skip Lines 0/1/3. Added **change-detection** to the staging loop (`cmp.w (%a1),%d1` → write + set dirty only when the value actually changes; advance `a1` on every real entry, preserving the `0xFFFF`-skip semantics). So a static sky costs zero per-frame commits, and only the entries the arcade changes are rewritten.
- **`45dae`** — kept the whole-hook scene-1 skip (it is **not** the Line-2 loader; proven). Protects Lines 0/1/3.
- **`3ba64`** — unchanged from Build 0329 (Line-2 allowed, Lines 0/1/3 skipped in scene 1).
Test install (`vdp_install_test_lines` at `load_scene_tiles`) and the removal of the per-VBlank reassert are unchanged from Build 0329.

## 7. Verification (Build 0332)
ROM `dist/rastan-direct/rastan_direct_video_test_build_0332.bin`, SHA256 `65d07d0127a36fbbbf61dc30781fd906cd12652f1498c6b2a12874ba5b63aed8`. GATE_PASS (canonical); seven-epoch PASS (records 0,3,4,10,11,12,15); Plane-A full LUT PASS; Plane-B fixed LUT PASS; address/bus errors 0. Runtime (states/traces/build0331_line2/b0332): Line 2 == Build 0328 at both the gameplay load and the sunset step; Lines 0/1/3 static Test (`l013=0xC480`); `palette_dirty` asserted only at the two Line-2 change events (f387, f1561), zero between → **no per-frame commit**.

## 8. Bank-0x30 explosion audit + decision (Part C)
Bank-0x30 effects select **Line 2** via the legacy `.Lnative_palsel` special case (`effective_bank==0x30 → line 2`, Build-0210 semantics). Bank 0x30 is **not** in the Test reindex (covered banks: 0x32/0x33/0x34/0x35/0x36/0x3A/0x3E), so these effects render with **raw** arcade patterns against Line 2. Frontend and gameplay-sky Line-2 differ at **every** index 1–15, so the "correct-looking" explosions in Build 0330 were an artifact of the frozen frontend palette, not a valid mapping. **Collision: plausible but not per-index enumerated; no authored alternative mapping exists.** Per the task's rule, **restore Layer B (done) and DEFER** bank-0x30 effect relocation to a first-class Palette Composer representation. No colors hardcoded; no explosion routing changed.

## 9. Items / Rastan / bats
Items/treasure select **Line 0** (`.Lnq_transient_items_emit` hardcodes attr=0) — preserved, unchanged. Rastan and bats remain incorrect (deferred `(code,bank)` sprite architecture) — out of scope.

## 10. Performance
Stable R1/P1: **0** Test-line commits and **0** Line-2 commits (change-detected). Commits occur only at genuine Line-2 change events (gameplay entry + each sunset step) and the one-shot Test install. The Build-0325 64-word every-frame CRAM PIO remains removed. Overall slowdown not claimed solved.

## 11. Vertical-noise task — PRESERVED (not touched here).
## 12. Deferred Palette Composer work — PRESERVED: complete `(code,bank)` sprite architecture; HUD `1UP`/score (bank 0x30) + Axe first-class representations; bank-0x30 effect representation (this audit).
