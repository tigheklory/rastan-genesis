# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0115 — R2 native Plane-A: scratch relocation + proven R2 epoch/scene integration

**Author:** Andy · **Date:** 2026-11-10 · **Baseline:** Build 0560 (HEAD `f8b07a84`) · **Produced:** Build 0561

This is the implementation task that resumes the historical PROMT-ID-0113 Round-2 native Plane-A work using
the PROMT-ID-0114 architecture recovery. Narrow goal: move the transition scratch out of
`fg_boundary_active_lut`, restore the proven Round-2 epoch/scene integration, and produce a testable Round-2
candidate **without** redesigning the LUT/residency architecture. No future ROM-resident epoch-LUT work was done.

---

## Result summary

- **Scratch is now completely outside the active LUT.** It lives in a dedicated transient WRAM buffer
  `fg_boundary_transition_scratch`. The active LUT is once again exclusively `tile/logical code -> VRAM slot`
  over the full `$0000..$27FF` index domain. Round-2's legitimate raw Plane-A codes can no longer alias scratch.
- **20 KB active LUT size is unchanged** (`FG_BOUNDARY_LUT_WORDS = 0x2800`, 20480 bytes).
- **Round-2 authored scenes + proven finer epoch split restored.** R2 epoch counts (recomputed) = **586 / 606 / 425**,
  all ≤ 676.
- **Round-1 is byte-for-byte preserved** (record native maps 0–22 identical; epoch unions `[283,366,665,634,640,590]`
  identical; R1 authored synthetic pattern region identical; rope/waterfall transition retention held).
- **Build 0561 numbered and preserved.** `canonical=PASS`; `entry`/`epoch` MAME gates were sandbox-wedged and
  killed (same label profile as the accepted Build 0560 — "gate killed", not a bad ROM).

---

## 1. Scratch defect correction (the core of PROMT-ID-0115)

### Before (R1-only assumption, the PROMT-ID-0114 finding)

`compile_pc080sn_genesis.py` placed the transition scratch at **word `0x1600`** inside the `0x2800`-word active
LUT, sized `len(pattern_id) + a_slot_count` words, and refused (Build-0308 guard) if that range overlapped any
legal Level-1 A/B tile code. This worked only because every real R1 Plane-A tile code is `< 0x1600`, making
`[0x1600,0x27FF]` a provably empty hole. Round 2 has legitimate raw Plane-A codes (e.g. `$24BB..$24C2`) that fall
inside that hole, so the guard correctly fired — the historical PROMT-ID-0113 blocker.

### After

The two transition bookkeeping maps now live in a dedicated `.bss` buffer:

```
fg_boundary_transition_scratch:  .space ((FG_BOUNDARY_PATTERN_IDENTITIES + FG_BOUNDARY_SLOT_COUNT) * 2)
```

Both logical structures are **preserved unchanged in meaning**:

1. `FG_BOUNDARY_IDENTITY_SCRATCH` (offset 0): canonical exact-pattern identity → incoming/new Genesis slot.
2. `FG_BOUNDARY_SLOT_TRANSLATION_SCRATCH` (offset `FG_BOUNDARY_PATTERN_IDENTITIES*2`): old Plane-A slot →
   incoming/new Genesis slot.

All seven `fg_boundary_active_lut + FG_BOUNDARY_*_SCRATCH` references in `fg_tile_cache.s` were retargeted to
`fg_boundary_transition_scratch + …`. The generator no longer computes a `scratch_word` placement or the
LUT-code overlap check; it emits only the size contract
(`FG_BOUNDARY_SCRATCH_IDENTITY_WORDS/SLOT_WORDS/TOTAL_WORDS`) for the manifest/report. The runtime sizes its own
buffer from the generated identity/slot constants.

### Scratch sizing (derived, not guessed)

Identity scratch is sized from the generated `FG_BOUNDARY_PATTERN_IDENTITIES` contract (the canonical exact-pattern
identity count), slot-translation from the generated `FG_BOUNDARY_SLOT_COUNT` (676). For the R1+R2 build:

| Structure | Words | Bytes | Address range |
|---|---|---|---|
| identity scratch | 3125 | 6250 | `0xFFB2B4 .. 0xFFBEFD` |
| slot-translation scratch | 676 | 1352 | `0xFFBEFE .. 0xFFD065` |
| **total buffer** | **3801** | **7602** | `0xFFB2B4 .. 0xFFD065` |

### WRAM budget and overlap proofs (exact)

| | `.bss` start | `.bss` end | `.bss` size | active LUT | scratch buffer |
|---|---|---|---|---|---|
| **Before (0560)** | `0xFF4000` | `0xFFC67A` | 34426 B | `0xFF62B4` (20480 B, scratch reused its tail — 0 extra B) | n/a (inside LUT) |
| **After (0561)** | `0xFF4000` | `0xFFE42C` | 42028 B | `0xFF62B4` (20480 B, unchanged) | `0xFFB2B4` (7602 B) |

- **Additional WRAM: +7602 bytes** (the whole dedicated buffer; the old in-LUT scratch had zero BSS footprint).
- **Final `.bss` end: `0xFFE42C`.**
- **Stack:** initial SP `0xFF0000` mirrors to the top of the 64 KB WRAM (`0xFFFFFE`) and grows downward.
  **Remaining margin from `.bss` end to top of WRAM = `0x1000000 − 0xFFE42C` = `0x1BD4` = 7124 bytes.**
  (0560's margin was `0x3986` = 14726 bytes; the dedicated scratch consumed 7602 of it.) A 7 KB headroom above the
  deepest stack is defensible for this program (no deep recursion); flagged here for Tighe's awareness, not a STOP.
- **No overlap with retained arcade A5 WRAM `$FF0000..$FF3FFF`:** the scratch (`0xFFB2B4+`) and the active LUT
  (`0xFF62B4+`) both sit far above `0xFF3FFF`.
- **No overlap with other Genesis BSS or the stack:** the linker placed the buffer contiguously between
  `fg_boundary_active_lut` (ends `0xFFB2B4`) and `fg_boundary_epoch_transitions` (`0xFFD066`); the whole `.bss`
  ends at `0xFFE42C`, below the stack region.

---

## 2. Restored Round-2 generator work (verified against current source)

- Added three authored Layer-A scenes to `AuthoredLayerA.SCENES` (same Palette Composer pipeline, `Test_2_0`
  profile): `PAL-R2-S1-PLANEA-OUTDOOR` (records 23–38), `PAL-R2-S2-PLANEA-CASTLE` (39–44),
  `PAL-R2-S3-PLANEA-BOSS` (45). Corpus usages: 797 (789 mapped / 8 raw), 234 (all mapped), 200 (all mapped).
- Restored the proven finer R2 epoch split `BOUNDARY_ROUND2_EPOCH_RECORDS = (23–32, 33–38, 39–45)`.
- **Recomputed R2 epoch pattern counts = 586 / 606 / 425** (all ≤ 676; `requested 9 epochs at cap 676`,
  per-round minima 5/3). These match the historical PROMT-ID-0113 measurement.
- The eight R2-S1 unmapped usages continue through the existing raw-arcade-pattern / Line-3 fallback (no new
  Palette Composer mappings authored).

### Round-stable synthetic-code assignment (required to preserve R1)

The authored synthetic-code band (`$1600+`) shares the arcade tile-code namespace. Round-1 record 22
(`PHASE3_ANIM_RECORD`, the boss animation) legitimately uses arcade codes **`$1AC0..$1AD1`**, which fall inside
that band. Globally re-sorting the authored pattern pool with Round-2 patterns silently reassigned the pattern
those boss-animation codes resolve to (`tile_bytes()` substitutes a synthetic pattern for any code in the band),
shifting Round-1 epoch 5 output (590→593). The fix: assign synthetic codes **round-stable** — Round-1 keeps its
exact byte-sorted order/codes (`r1_unique = sorted(set(pending_r1))`), Round-2-only patterns are appended after
(`r2_extra`). This restores Round-1 to byte-identical while giving Round 2 its own codes above the R1 pool. This
is the same namespace-overlap bug class as the scratch defect, resolved by preserving the R1 sub-pool rather than
redesigning the namespace.

---

## 3. Round selection (additive, R2-only)

- **Fixed Plane-B / package / epoch selection:** already present in the runtime
  (`fg_boundary_pending_round`, `FIXED_B_R2_*`); the generated `record_to_package`/epoch tables now cover
  records 23–45 with the finer split. No R1 selection semantics changed.
- **Authored scene / palette selection:** wired additively. `palette_scene_select.bin` now returns asset IDs
  4/5/6 for R2 records; `palette_hooks.s` adds `diagnostic_palette_r2s1/r2s2/r2s3` CRAM blobs (existing Composer
  exports, provisional pending RG-022) and three `diagnostic_palette_asset_ptrs` entries; `vdp_comm.s` generalizes
  the visual-index offset to `(asset-1)*FG_AUTHORED_DESC_INDEX_BYTES` for assets 4–6 (assets 1–3 keep their exact
  prior offsets). Makefile gains `PALETTE_R2S*_CRAM` deps.

---

## 4. Round-1 non-regression (proofs)

All comparisons are against a from-clean regeneration of the Build-0560 generator output.

- **Scratch relocation alone is byte-neutral:** with R2 reverted, every generated `.bin` artifact
  (`boundary_packages`, `record_native_maps`, `native_pattern_region`, authored visuals, scene-fill, pan-row,
  palette-scene-select) is byte-identical to 0560; only `boundary_constants.inc` changes (the scratch `.equ`
  lines).
- **R1 record native maps 0–22 byte-identical** (both stable and transition-overlap blocks) after the full R2
  integration.
- **R1 epoch unions `[283,366,665,634,640,590]` identical**; R1 `record_to_epoch` unchanged
  (`[0,0,0,1,2,2,2,2,2,2,2,3,3,4,4,4] + [5]*7`).
- **R1 authored synthetic pattern region identical** (`native_pattern_region` first byte difference is exactly at
  code `0x1D93` = the start of the appended R2-only pool).
- **Transition retention held:** rope→waterfall and waterfall→next overlap packages keep `stable[code] ==
  overlap[code]`; HARD per-transition checks pass (peaks `414/511/673/346 ≤ 676`, missing=0, collisions=0,
  incoming_stable_slots_changed=0, handoff_missing=0). R1 transition-overlap package **ids** shift +1
  (8,9,10,11 → 9,10,11,12) because Round 2 appends one stable package — harmless renumbering; the overlap-block
  rendering is byte-identical.

### Generated R1 artifacts that necessarily change (and why)

| Artifact | Change | Why it is harmless |
|---|---|---|
| `boundary_constants.inc` | scratch `.equ` lines replaced; `FG_BOUNDARY_EPOCHS 8→9`, `FG_BOUNDARY_PACKAGES 12→13`, R2 package ids | metadata; R1 record→epoch and record native maps unchanged |
| `record_native_maps.bin` | 552-byte record table (R1 transition package ids renumber) + appended R2 blocks | R1 **cell data** blocks byte-identical; only the package-id table field moved |
| `native_pattern_region.bin` | appended R2 synthetic patterns from code `0x1D93` | R1 region `[0, 0x1D93*32)` byte-identical |
| `authored_descriptor_visuals.bin` | grows 3→6 contexts | R1 context payloads resolved identically; offsets consistent via regenerated `FG_AUTHORED_DESC_*` constants |

---

## 5. Gate adjustments (declared, not rubber-stamped)

- **`verify_build0311_transition_retention.py`:** structural asserts updated for the 9-epoch/13-package layout
  (`FG_BOUNDARY_EPOCHS==9`, `FG_BOUNDARY_PACKAGES==13`, new `record_to_epoch`/`record_to_package`). All R1
  transition-retention semantics (`verify_object`, HARD peak/collision/handoff checks) are unchanged. The
  non-candidate baseline-lock (exact payload hashes + detailed peaks) is skipped by the production build
  (`LAYERA_EDITOR_CANDIDATE=1`) and is noted as pending re-lock after Tighe accepts the R2 candidate.
- **`Makefile GENESIS_COVERAGE_DELTA 0x53000 → 0xC3000`** (profile=1 branch, normal + full-HUD): +0x70000 for the
  native R2 authored data appended to the Genesis image. Drives both the postpatcher "Build 0029" coverage
  invariant and the manifest expectation; observed coverage `0x43CEB8` now matches the declared expectation.

---

## 6. Build 0561 artifacts

- Release ROM: `dist/rastan-direct/rastan_direct_video_test_build_0561.bin`
  - SHA-256 `b08e505eb648ba688a5862c951b97c62ad6b3f9667a4a4b85c0e609022c85565`, 4,443,832 bytes
  - Ledger: `0561 PRODUCED 2026-11-10 ... [canonical=PASS entry=FAIL epoch=FAIL]`
- `entry`/`epoch` are MAME gates run through the project's USA/NTSC `genesis` machine. In this sandbox MAME
  wedges at init (0% CPU, ignores its own `timeout`), so both were killed to let the Makefile number the ROM —
  identical label profile to the accepted Build 0560. These are **GENESIS NTSC MAME** gate labels, not a judgment
  that the ROM is bad, and they are **not** gameplay acceptance.

---

## 7. Scaffolding / audit trail

No production scaffolding was added. All investigation used throwaway probes written to the session scratchpad
(and briefly to `tools/translation/_*.py` so sibling imports resolved); every such file was removed, and
`git status` shows no stray probe files. Production source changes are limited to:
`tools/translation/compile_pc080sn_genesis.py`, `tools/translation/verify_build0311_transition_retention.py`,
`apps/rastan-direct/src/fg_tile_cache.s`, `apps/rastan-direct/src/vdp_comm.s`,
`apps/rastan-direct/src/palette_hooks.s`, `apps/rastan-direct/Makefile`.

---

## 8. What still requires Tighe gameplay verification

- Round-2 **gameplay** on the USA/NTSC `genesis` target (native Plane-A geometry + palette for R2-S1/S2/S3).
  Automated gate PASS is supporting evidence only; it is **not** gameplay acceptance.
- The Round-2 palette is **provisional** (RG-022 authoring pending). R2 colours may be wrong even with correct
  native geometry; this is a known authoring gap, iterable in the Composer, not a translation defect.
- Suggested first test: **R2-S1 direct-start** (largest authored content, 797 uses) to confirm native Round-2
  Plane-A geometry renders. Then R2-S2, then R2-S3.
- Confirm Round-1 is unchanged from the accepted 0560 baseline (expected byte-identical).

Deferred and NOT touched (per scope exclusions): future ROM-resident epoch LUT, 32 KB/page-table LUT, R1-S3
torches, R2 boss AI/movement, R2 post-boss progression/softlock, score/high-score, audio, palette redesign.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0115`
