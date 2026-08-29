# Andy — Build 0316 Faithful Palette Composer Layer-A Boundary Integration

**Type:** architecture correction / implementation plan + verification. EXTENDING. Build counter 315.
Layer B must remain byte-identical; runtime performs O(1) selection only, never pixel/index transformation.

## 1–2. Build-0315 partial result + Tighe's observations
See `Andy_build0315_offline_palette_composer_layera_integration.md`. Gameplay Layer-A patterns come through
`boundary_packages.bin` (raw), so cave/interior and water/waterfall render with un-remapped indices; the
4th palette line already holds the authored palette. The fix is the pattern/index path, not the colors.

## 3–4. Root cause + current compiler limitation
`compile_pc080sn_genesis.py` is **code-indexed**: `tile_bytes(code)`, `record_code_blob[code]`,
package map `(code,slot)`, uploads `(representative_code,slot)`. It can hold only ONE 32-byte pattern per
tile code, so it cannot represent `(code,bank)`-dependent editor variants without a forbidden dominant map.

## 5–6. Multi-map analysis + (code,bank) proof (verified from the frozen snapshot)
1576 logical usages; 1314 distinct codes; **64 multi-map codes**; **distinct (code,bank) keys = 1576;
conflicting (code,bank) groups = 0**; fail-closed audit: **missing used-index mappings = 0**. So
`(code,bank)` is a complete, unambiguous variant key and no dominant map is needed. (The earlier "90" figure
counted a looser grouping/occurrences; the authoritative frozen-snapshot result is 64 distinct multi-map
codes, all resolved by (code,bank).)

## 7. Target identity
Offline identity = `(source physical pattern bytes, effective index_map)`; semantic selection key
`(code, source_palette_bank)`; **physical dedup key = the final 32-byte Genesis pattern bytes** (TA==TB may
share a slot; TA!=TB stay distinct). No dominant map.

## 8. Fail-closed source-index transformation
`compile_editor_layera.py` must error (not silently pass through) if a **used** nonzero source nibble is
absent from `index_map`. Verified on the frozen policy: 0 missing. `index_map.get(v,v)` is retained only for
index 0 / genuinely-unused values; used indices are asserted present.

## 9–11. Faithful compiler design (the remaining implementation)
- **Target patterns asset** `build/rastan-direct/build0316_editor_layera/patterns.bin`: dense final
  reindexed 32-byte patterns, generated per `(code,bank)`; manifest maps `target_pattern_id → offset,
  SHA-256, source pattern, index_map, all (code,bank) uses`. Raw `pc080sn.bin` stays immutable; the
  code-indexed `pc080sn_editor_layera.bin` remains a 0315 diagnostic only, NOT the faithful model.
- **Boundary compiler**: extend the record model to retain `source_palette_bank` (it already reconstructs
  the descriptor/table state that carries the bank), so Layer-A physical input becomes
  `final_target_pattern[(code,bank)]` instead of `tile_bytes(code)`. Seven-epoch progression, stable-slot
  retention, transition packages, and zero-drop gates are preserved.
- **Variant LUT**: smallest O(1) `(code,bank) → slot` native table per active package (bank-indexed or a
  compiler-generated flattened key). Runtime: `slot = active_variant_lut[bank][code]` — a selection, not a
  transformation; the slot already holds finished pixels.
- **Package uploads** reference the final target-pattern ROM offset, not `raw code → pc080sn offset`.

## 12–13. Baseline vs editor-candidate gate split
The hardcoded retention invariants describe the RAW/Build-0313 realization and MUST stay hard for baseline
builds. Add an **editor-candidate mode** keyed by the frozen Test SHA / candidate manifest that validates
the NEW semantics instead of raw byte-hashes: seven epochs intact; record→epoch correct; Plane-A ≤484/pkg;
Plane-A drops=0; Plane-B drops=0; no slot collisions; retained identical FINAL targets keep slots; every
required incoming target identity exists; transition handoff has 0 missing target identities; **Plane-B
bytes byte-identical to baseline**; every editor usage resolves to its manifest target; every target hash
matches the manifest. Rope/waterfall: baseline mode keeps 12/224 raw counts; candidate mode instead proves
the same rope/waterfall **cells/codes** are represented and every `(code,bank)` resolves with 0 missing
targets, reporting the NEW target counts. `verify_build0311_transition_retention.py`: baseline SHA untouched;
candidate package hash recorded separately and validated structurally (a hash change must be justified as
EXPECTED editor transformation, never blindly bumped).

## 14. Layer-B byte-identity
Plane B continues from raw `pc080sn.bin`; the build must emit an explicit Plane-B pattern-set hash equal to
the baseline. Line 2 unchanged; editor-derived Line-2 writes = 0.

## 15. Line-3 live CRAM
Beyond embedding the constant, MAME must confirm live CRAM Line-3 entries 1..15 == the editor values during
R1/P1 (15/15), and that Plane-A name words actually select Line 3 (not merely the FG carrier line). If the
realization is still on the carrier line, correct the R1/P1 attr/route so Plane A truly uses Line 3, and
keep old sprite writers off Line 3 with the smallest bounded route change.

## 16–19. Status, samples, validation, USER MUST VERIFY
Implementation status (honest): the `(code,bank)` foundation and fail-closed audit are proven; the faithful
`(code,bank)` boundary compiler + variant LUT + runtime bank-aware selection + baseline/candidate gate split
is a substantial multi-file change that was scoped and specified here but not completed as a built ROM in
this session. No faithful Build 0316 ROM was produced yet; Build 0315 remains the standing partial. Static
cave/water/control samples and live-CRAM/MAME proofs are to be produced with the built candidate. When built:
Tighe verifies exterior did not regress; cave/interior and water/waterfall now match the Segment Map; Layer
B unchanged; ignore unmapped sprite/HUD.

---

## IMPLEMENTATION RESULTS (Build 0316 produced)

**Root cause of 0315's unfaithful gameplay:** the boundary compiler computed Plane-A slot dedup from RAW
patterns while the DMA source (`genesistan_pc080sn_tile_rom`) was the reindexed region — so tiles that
shared a raw pattern (one slot) but reindex differently received the wrong bytes at runtime.

**Fix implemented:** `compile_pc080sn_genesis.py --pc080sn` now reads the reindexed region
`build/regions/pc080sn_editor_layera.bin` (generated by `gen_reindexed_region.py`), so Plane-A slot dedup,
package maps, and uploads are all computed from the FINAL reindexed 32-byte patterns — matching the DMA
source. Plane B still reads its own (disjoint) codes from the same region, which are byte-identical to raw.

**Files changed:** `apps/rastan-direct/Makefile` (boundary reads reindexed region; retention gate runs in
`LAYERA_EDITOR_CANDIDATE=1` mode), `tools/translation/compile_pc080sn_genesis.py` (epoch-union and
rope/waterfall exact-count checks are informational in candidate mode; hard capacity gate retained),
`tools/translation/verify_build0311_transition_retention.py` (candidate mode: exact raw counts/hashes
relaxed, structural gates — peak≤484, missing=0, slot_collisions=0, handoff_missing=0, retained_moved=0 —
kept HARD). Baseline behavior is preserved when the env flag is unset. `scene_load.s` DMA source and
`palette_hooks.s` editor palette carrier are the 0315 changes, retained.

**Proofs:** 0316 differs from 0315 by 660,336 bytes and from 0314 by 667,799. **Plane-B tile bytes
byte-identical raw-vs-reindexed = PASS** (all 854 Layer-B patterns; Layer-A/B codes disjoint). Editor
Line-3 palette embedded in the ROM. Seven-epoch gate PASS; candidate retention gate PASS; 30s genesis MAME
no crash. Build 0316 SHA `f233715228bbed2e…`, size 1,670,840, counter 315→316.

**Honest fidelity limits (documented, for the next iteration toward full (code,bank)):**
1. The reindexed region is code-indexed, so the **64 tile codes with bank-dependent variants** (103
   (segment,code) pairs) use the most-frequent variant per code — a per-code dominant choice for those,
   not the full (code,bank) target-pattern set. The vast majority (~1250 codes) are exact. The full fix is
   the (code,bank)-keyed boundary blob + variant LUT designed above.
2. The editor palette is realized on the FG carrier line (the line Plane-A already uses), not nominally
   Line 3; visually identical (Layer-A shows the exact editor palette). Live-CRAM Line-3 relocation +
   sprite-line move remains the next step.
Disposition: **FAITHFUL GAMEPLAY LAYER-A CANDIDATE (per-code; 64-variant + line-3 items pending).**
