# Build 0417 — A-0154 / LA-0092 Palette-Composer Authority Audit (Andy)

**Date:** 2026-10-12 · **Type:** READ-ONLY independent architecture/code review. No production
source, no ROM, no build number, no edits to Test.json / palette_decisions.json / generated artifacts
/ Cody's tree. Diagnosis + evidence + recommended next step only.

**Target:** PC080SN tile code **0x117** = physical pattern **A-0154** = logical usage **LA-0092**,
effective bank **0x003**, raw attr 0x0003, no flip, Line 3; secondary usage **LA-0543** (bank 0x005);
Composer marks A-0154 MULTI-PALETTE.

---

## 0. Headline

The **pixel reindex of tile 0x117 is correct and complete.** The defect is a **broken color-authority
bridge**: the Palette Composer authors *two* things for a Layer-A usage — a **pixel `index_map`**
(source→Line-3 index) **and** the **`target_palette_lines[3]` CRAM colors** — but production consumes
**only the pixel index_map** (`gen_reindexed_region.py`). CRAM Line-3 is installed at runtime by
`palette_route_table` from the **arcade FG bank-3 carrier**, *not* from the Composer's authored
Line-3 colors. The Composer authored purple at Line-3 entries **6,7,8,9,11**
(`0x0424/0x0624/0x0402/0x0202/0x0422`), where LA-0092's pixels now point — but production has a
documented palette decision only for Line-3 entries **1–5** (the cave-block ground, itself flagged
"Genesis color WRONG … deferred to Andy … not visually accepted"). So A-0154's pixels land on CRAM
entries whose colors were never authored into production → wrong color everywhere A-0154 is drawn.

---

## 1. Authored maps (from the build0400 snapshot == live Test.json; identical)

LA-0092 (bank 0x003), Line **3**: `4→7, 5→6, 6→11, 7→8, 8→9`
LA-0543 (bank 0x005), Line **3**: `4→7, 5→6, 6→11, 7→8, 8→9`
**Different: NO** (identical). So the two banks of A-0154 resolve to the *same* finalized pixel
pattern. (The separate `LA-0154` entry in Test.json is tile code **0x155**, a different tile — not
0x117; it is not involved here.)

## 2. Source pixels (build/regions/pc080sn.bin, tile 0x117)

Nibble histogram `{4:4, 5:20, 6:9, 7:15, 8:16}`. **Source zero (transparent) count: 0.** Used
indices exactly **{4,5,6,7,8}** — matches the Composer UI.

## 3. Transparency contract

`gen_reindexed_region.py`: `hi = imap.get(hi, hi) if hi != 0 else 0` — source 0 is preserved as 0
(transparent), and a non-zero source index with no map entry **passes through unchanged** (NOT forced
to 0). **Opaque used index may map to 0: NO** (no map sends 4–8 to 0; 0x117 has no index-0 pixels
anyway). Composer protection: it constrains authored maps to used colors. MRD protection: keeps
distinct colors distinct (see §4). Generator protection: never introduces a 0; unmapped non-zero
passes through (wrong color, not transparency). **This is not a transparency bug.**

## 4. MRD

"10 distinct-color pairs must stay distinct" = C(5,2)=10 pairs among the 5 used colors {4,5,6,7,8};
the validator checks no two *used* source colors map to the *same* target index (no color merging).
LA-0092's map is injective on {4,5,6,7,8}→{7,6,11,8,9} (all distinct) → MRD satisfied. **Does MRD
protect transparency: NO** — MRD is about not merging used colors; it does not check target index 0.
A map could satisfy MRD yet send a used color to target 0 (it does not here).

## 5. Multi-palette architecture

A-0154 appears under bank 0x003 (LA-0092) and bank 0x005 (LA-0543). **Separate finalized patterns
required: only if their index_maps differ — here they are identical, so one pattern suffices.**
Current implementation: `gen_reindexed_region.py` is **code-indexed with a most-frequent collapse**
(documented "Build-0315 checkpoint limitation"): per tile code it emits `ctr.most_common(1)` — one
index_map. For 0x117 the vote is **unanimous** (both usages identical) → correct. **But this is a
latent multi-palette bug for any tile code whose usages have *divergent* maps** (the sprite pipeline
`gen_reindexed_pc090oj.py` emits per-(code,bank) variant cells; the Layer-A pipeline does NOT). Not
the cause for 0x117; flag for other tiles. **Correct for 0x117: YES; architecture incomplete for
divergent-map codes: YES.**

## 6. Actual Build-0417 path

`0x117 → A-0154 → usage LA-0092 (plane_a_uses.json index 92) → index_map {4→7,5→6,6→11,7→8,8→9} →
gen_reindexed_region.py (code-indexed, unanimous) → build/regions/pc080sn_editor_layera.bin (pixels
reindexed) → incbin → ROM → VRAM → Plane-A name word`. **Every pixel stage is correct.** The stage
that is *bypassed* is the **CRAM color** stage: the finalized pixels reference Line-3 indices
6,7,8,9,11, but nothing installs the Composer's `target_palette_lines[3]` colors at those CRAM
entries. CRAM Line-3 is set by `vdp_install_test_lines` / `palette_route_table`
(`palette_hooks.s:61`: scene 1, PC080SN_FG, bank 3 → Genesis Line 3, CARRIER) = the **arcade bank-3
palette routed to Line 3**, not the Composer colors.

## 7. Build-0417 profile authority

Production consumes the **frozen snapshot `build/rastan-direct/build0400/Test.snapshot.json`**
(`Makefile:80 EDITOR_LAYERA_SNAPSHOT`), via `gen_reindexed_region.py --profile $(EDITOR_LAYERA_SNAPSHOT)`
(`Makefile:250-252`). **Current live Test.json consumed: NO** — a build0400 freeze is. Evidence:
Makefile var, the generator's `--profile` arg. (For A-0154 this doesn't matter — snapshot == live,
§8 — but it is a standing authority gap: Composer v0.4 edits won't reach the ROM until re-frozen.)

## 8. Baseline vs Test

The build0400 snapshot and the live Test.json are **byte-identical for LA-0092/LA-0154/LA-0543**
(verified). The live profile's `parent`/`immutable` baseline differs only where Test added LOCAL
overrides; LA-0092 is a LOCAL R1/P1 override and is present identically in both. **Build 0417 contains
the Test (local-override) pixel result.** So staleness is **ruled out** for A-0154.

## 9. Pixel-level golden check

Expected Genesis index per source: `4→7, 5→6, 6→11, 7→8, 8→9`. Applied to tile 0x117's
`{4:4,5:20,6:9,7:15,8:16}` → Genesis indices `{7:4, 6:20, 11:9, 8:15, 9:16}`. **Expected target zero
count: 0. Generated zero count: 0** (no 0 introduced; `gen_reindexed_region.py` maps every used index,
0 preserved). **Pixel-exact: YES** — the generated `pc080sn_editor_layera.bin` for code 0x117 equals
this golden reindex (same deterministic transform; no second reindex downstream). The *pixels* are
correct; what they index into (CRAM Line-3 6,7,8,9,11) is where the color is wrong.

## 10. Wrong-tile possibility

Not the cause. The source formula selects code 0x117 for segment 11 / X44 Y38, and the Layer-A
reindex operates on code 0x117 in place (code-indexed, `s = code*32`). The finalized pattern identity
is the same tile; the name word points at the correct VRAM slot for code 0x117. The defect is color,
not pattern identity. (The separate BG-A ring/placement regression — Andy_build0415/historical audits
— is a *different* bug about *where* cells appear; this audit is about the *color* of a correctly-
placed A-0154.)

## 11. Repeated-pattern evidence

A-0154 occurs 49× (all LA-0092 in segment 11) + LA-0543 elsewhere, all with the identical map → all
49 should (and do) get identical Genesis pattern bytes. The bad appearance repeats **wherever A-0154
is used** because the error is not per-occurrence — it is the **shared CRAM Line-3 color** behind the
(correct, identical) pixels. This points squarely at **palette/CRAM color**, not pattern bytes, usage
mapping, bank variant, or tile identity.

## 12. Canonical registry

`specs/palette_decisions.json`: **no exact A-0154 / LA-0092 / 0x117 entry.** The only Stage-1 Layer-A
Line-3 decisions are: the **cave-block ground** (source 9–13 → Line-3 entries **1–5**; status: the
genesis_realization is explicitly "**Genesis color WRONG … deferred to Andy per Cody build0366 … NOT
visually accepted**", line ~471), and the Rastan nibble-3 carrier (Line 3, line ~71–73). **There is
no canonical decision authoring Line-3 entries 6,7,8,9,11** (the purple-rock targets). **Authority
mismatch: YES** — Test.json authors a LOCAL LA-0092 index_map (and target_palette_lines[3] purple at
6–11) with **no corresponding canonical palette decision** and **no production CRAM installation** of
those colors.

## 13. Architecture compliance

**PARTIALLY COMPLIANT / BYPASSES COMPOSER (color half).** The pixel-index half of the Composer
authority IS honored (gen_reindexed_region.py). The **target-line COLOR authority
(`target_palette_lines[3]`) is NOT bridged to production** — `compile_editor_layera.py` (the tool that
reads `target_palette_lines[3]`) is **not** in the production Makefile; runtime CRAM Line-3 comes from
the arcade bank-3 carrier via `palette_route_table`. Combined with the missing canonical decision for
Line-3 6–11, A-0154's authored purple never reaches CRAM. (Consistent with the known standing gap:
"Test.json has no compiler bridge to production.")

---

## Likely root cause (ranked)

**#1 — Broken color-authority bridge (HIGH).** The Composer's `target_palette_lines[3]` colors
(purple at entries 6,7,8,9,11) are not installed into production CRAM Line 3; production Line 3 =
arcade FG bank-3 carrier (`palette_route_table`). A-0154's correctly-remapped pixels index CRAM
entries that hold the wrong/arcade colors → wrong everywhere. No canonical decision exists for Line-3
6–11.

**#2 — Line-3 realization known-wrong & incomplete (HIGH, related).** The only Line-3 decision (ground
1–5) is itself flagged "Genesis color WRONG, not visually accepted, deferred to Andy"; entries 6–11
were never addressed. Line 3 is over-shared (ground 1–5 + purple-rock 6–11 + sprite carrier) with
only part of it authored into production.

**#3 — Layer-A code-indexed most-frequent collapse (MEDIUM, latent; not 0x117).** For any tile code
with *divergent* usage index_maps, `gen_reindexed_region.py` emits only the most-frequent map, so a
minority usage renders with the wrong map. 0x117's vote is unanimous, so it is unaffected — but this
is a real multi-palette gap vs the sprite pipeline (which emits per-(code,bank) variants).

---

## Recommended next action (no implementation)

1. **Confirm #1 with one cheap runtime read:** dump CRAM Line-3 entries 6,7,8,9,11 during Stage-1
   gameplay and compare to the Composer's authored `target_palette_lines[3]` =
   `{6:0x0424, 7:0x0624, 8:0x0402, 9:0x0202, 11:0x0422}`. A mismatch confirms the color-bridge defect;
   a match would reopen #3/other.
2. **Decide the authority model** (project-level, Tighe): either (a) bridge `target_palette_lines`
   into production — compile the authored Line-3 colors into the CRAM install path (`vdp_install_test_lines`)
   and record a canonical palette decision for Line-3 6–11 — or (b) constrain the Composer's Layer-A
   authoring so Line-3 index_maps only target CRAM entries that production actually installs (the
   arcade carrier), i.e. make the index_map and the installed line agree.
3. **Separately schedule the Layer-A per-(code,bank) variant fix** (#3) to match the sprite pipeline,
   before any tile with divergent usage maps is relied upon.
4. **Close the snapshot-staleness gap** (§7): re-freeze the snapshot from live Test.json (or point the
   Makefile at live) so Composer v0.4 edits reach the ROM — orthogonal to A-0154 but a standing risk.

Do not change code/palette until Cody's and Andy's diagnoses are compared (Tighe's instruction).

---

**CODY TREE MODIFIED: NO. PRODUCTION MODIFIED: NO. PALETTE PROFILE MODIFIED: NO. ROM BUILT: NO.
BUILD NUMBER CONSUMED: NO.**
