# Andy — Build 0314 Palette Composer Pipeline Validation (scoping + gate correction)

**Type:** implementation/verification. Build counter 313. No build consumed yet. Layer B untouched.

## Purpose
Bounded proof that editor-authored R1/P1 palette/tile/sprite decisions reach real Genesis output. NOT an
R1/P1 palette-completion or whole-sprite-corpus task. Editor supported context: **R1/P1 ONLY**.

## Corrected coexistence gate (this session)
Per Tighe's instruction, `export_palette_policy.py`'s gate was corrected: Build-0313 / canonical target-line
assignments are the **baseline Genesis realization, not immutable arcade semantics**. A Test policy is no
longer rejected for choosing a different candidate target line. Only true hard conflicts among AUTHORED
consumers fail: (H1) Layer-A shares a line with an authored sprite; (H2) Line 2 touched; (H3) authored
sprites contradict at one entry; (H4) a line exceeds 15 nontransparent entries.

**`--check` result: PASS (0 hard conflicts).** Line-model differences vs Build 0313 are reported as
`candidate_realization_notes` (informational): Layer-A on Line 3 (baseline Line 1); Rastan on Line 0
(canonical proven Line 3); Lizardman on Line 1 (canonical decided Line 0). These are the intended
experiment, not errors.

## Authored coverage (frozen snapshot, SHA deb696452d7456b3…)
- Layer A: 1576 phase mappings on **Line 3**; target line Line 3 populated (15 entries).
- Sprites (authored subset): **Line 0** = rastan×3 (0x33), valkyrie (0x32), chimera (0x34), small/large bat
  (0x3E); **Line 1** = four_armed (0x3A), flying_demon (0x35), lizardman (0x36). Lines 0/1 = 15 entries each.
- Line 2 = Layer B, untouched (0 editor entries).
- **Explicitly unmapped (expected):** HUD, sprite-based text, score/number glyphs, items, weapons, effects,
  projectiles, and any other sprite families — future context-aware editor corpus work, NOT part of 0314
  acceptance. Their color mismatches are `EXPECTED UNMAPPED-CORPUS LIMITATION`, not failures.

## Remaining work to PRODUCE a verified Build 0314 (honest scope — not yet done)
The candidate layout **inverts** the Build-0313 palette routing (Layer-A FG Line1→Line3; sprites
Line3→Lines0/1; HUD off Line 0), and the editor authored **per-tile source→target index maps** (1576 Layer-A
+ 10 sprite) that the current canonical schema and `compile_pc080sn_genesis.py` do not consume. Producing an
editor-faithful ROM therefore requires, as a bounded but real implementation:
1. **Promotion**: `--apply` governed merge of the R1/P1 candidate realization (line assignments +
   per-usage index maps + Lines 0/1/3 CRAM) into `specs/palette_decisions.json`, ID-preserving, with a
   pre-promotion registry snapshot.
2. **Compiler extension**: teach the PC080SN/native-sprite compiler to apply the per-usage index maps when
   transforming 4bpp patterns, emit Layer-A to Line 3 and sprites to Lines 0/1, exact-dedup, and generate
   CRAM Lines 0/1/3 + Plane-A attribute palette bits + sprite SAT palette bits for the candidate layout.
3. **Route generation**: regenerate `palette_route`/attr so Layer-A→Line 3 and sprites→Lines 0/1 while
   Line 2 (Layer B) is byte-identical to Build 0313.
4. **Gates**: per-epoch VRAM capacity, outside-R1/P1 differential = 0, Layer-B differential = 0, then the
   Makefile build + canonical gate, then `genesis` MAME sanity.
5. Only after those pass: consume Build 0314.

This is a substantial production change; it was NOT completed/verified in this session. Build 0314 was
**not** consumed, because shipping an unverified numbered ROM risks the Build-0207 "consumed artifact lost"
failure.

## USER MUST VERIFY (once 0314 is produced)
Boot; R1/P1; compare Layer A vs editor Segment-Map Genesis; inspect the mapped sprite subset vs editor;
ignore unmapped HUD/text/item/effect color errors; confirm Layer B unchanged + time-of-day continues;
confirm performance. Judge mapped content only.

## Future editor/corpus work (record, not now)
Complete R1/P1 sprite corpus; player representations; context-aware sprite HUD/text; items; weapons;
effects/projectiles; then deliberate next-Round/Phase support via this same governed bridge.
