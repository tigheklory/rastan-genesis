# PROMPT-ID-0042 — Plane A Initialization & R2-S1 Graphics: Independent Research

**Author:** Andy · **Date:** 2026-10-30 · **Method:** static source/artifact analysis (NO traces, NO ROM build).
**Role:** READ-ONLY engineering investigation. Implementation owner is **Cody** (concurrent PROMPT-ID-0041).
I did not modify any production ASM/C/ROM, sprites, audio, Palette Composer, `Test.json`, palette decisions,
the Bestiary, or Cody's worktree. Deliverables are this report + an `AGENTS_LOG.md` entry only.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0042`

---

## 0. Executive summary (the one-paragraph answer)

Build 0503 published the **entire** `staged_fg_buffer` to Plane A VRAM at every scene boundary. That
buffer is **arcade-authoritative for any round and any spawn point**, because it is filled by the native
descriptor-rebuild producer that walks the *live* arcade descriptor/metatile chain (arcade-owned pointer
table `0x00FF1040`) and **retains the arcade collision word** while looking up only the *visual* Genesis
name word. Build 0504 deleted that wholesale publication and replaced it with a **precompiled
`scene_fill_maps` reseed** plus an offline **authored visual LUT**. Both replacements are *partial
coverage* of what the wholesale publish covered for free:

- **Problem A** is a gap on the **progression/record axis**: the precompiled `scene_fill_maps` only carry
  stage/epoch-*entry* records `{0x00, 0x10, 0x16, 0x17, 0x27, 0x2d}`. Mid-stage records — including the
  R1-S1 segment-4 **checkpoint record `0x0B`** — are absent, so a respawn there finds a no-op reseed and
  **nothing is published** → incomplete Plane A.
- **Problem B** is a gap on the **round/scene axis**: the offline authored visual realization covers
  **only the two R1 scenes** (`context:gameplay.r01.p01`, `PAL-R1-S2-PLANEA-CASTLE`). R2-S1's descriptors
  have no authored visual, so their Genesis name word falls back to the raw base-LUT/epoch decode. Tiles
  that share R1's vocabulary render right; R2-specific tiles render **wrong** → "some correct, some
  incorrect." Collision is fine because the collision word is the *retained arcade word*, never the
  authored visual.

**They are not the same defect, but they share one root cause:** 0504 replaced an authoritative wholesale
publish with two independently-authored partial tables, each incomplete along a different axis. Fixing A
(add the missing records) does not fix B (add the missing rounds) and vice-versa.

---

## 1. Why the original scene initialization worked (Build 0503)

The normal-runtime producer of Plane A content is
`genesistan_hook_pc080sn_descriptor_rebuild` in `apps/rastan-direct/src/tilemap_hooks.s`. For each
entering/visible column it:

1. Reads the live scroll (`ARCADE_PC080SN_SCROLL_Y_FG_OFFSET(%a5)`) to pick the logical row window.
2. Walks the **arcade-owned rebuilt descriptor pointer table** (`PC080SN_DESC_REBUILD_PTR_TABLE` /
   `PC080SN_DESC_REBUILD_SRC_TABLE`, sourced from `0x00FF1040`).
3. For each descriptor cell it produces **two** outputs: the Genesis **visual name word** (`D0`, via the
   tile-VRAM LUT) and the **retained arcade collision word** (`D2`).
4. Writes the result into `staged_fg_buffer`.

Because step 2 reads the *arcade's own* descriptor chain for whatever progression `a5@0x13E` currently
holds, `staged_fg_buffer` is **authoritative for any round and any spawn**: it contains exactly what the
arcade scene fill staged, not a precomputed guess.

Build 0503's boundary install (`fg_boundary_install_post_reseed`, `apps/rastan-direct/src/fg_tile_cache.s`)
then performed a **full-plane DMA of the whole `staged_fg_buffer`** (`PLANE_NAME_WORDS` = 2048 words to
`VRAM_PLANE_A_BASE`) alongside the Plane-B publish. Publishing the complete authoritative buffer means
**every** spawn — top-of-stage entry, mid-stage checkpoint, R1 or R6 — got a complete, correct plane. The
segment-4 checkpoint worked in 0503 for this reason, not by luck: the checkpoint's staged buffer was as
authoritative as any stage-entry buffer, and the wholesale publish did not care *which* record it was.

## 2. Why the Build 0504 replacement was not equivalent

0504 removed the Plane-A full-plane DMA from `fg_boundary_install_post_reseed` (Plane-B publish kept) and
introduced `genesistan_plane_a_scene_scroll_reseed_native` in `tilemap_hooks.s`, which:

- reads `a5@0x13E`, `subq #1`, and indexes `genesistan_plane_a_scene_fill_maps`;
- if the indexed offset is `0xFFFFFFFF` (**absent**) the reseed is a **no-op** — it returns without staging
  or publishing anything;
- otherwise it copies the precompiled map's 32-row window into `staged_fg_buffer` and sets
  `fg_row_dirty = 0xFFFFFFFF`.

This is a *precompiled-table* publish, not a wholesale publish of the authoritative buffer. It is only as
complete as the two offline tables behind it — and both are partial (§4, §5).

## 3. How the arcade's compact metatile data drives the Genesis presentation

Proven chain (`analysis/decompilation/c/rastan_scene_map.c`, H11/H12/H13; byte-faithful control flow in
`raw/000503bc.c`, `raw/000559b2.c`, `raw/000563a6.c`):

```
progression A5+0x13E
  -> scene index  = byte[0x50EE0 + 0x13E]                          (0x503BC)
  -> section kind = byte[0x50F6B + scene index]   (0 = outdoor, !=0 = castle / Phase 2)
background map:  table 0x562CA[round] -> (ptr0 ROM src, ptr1 name-table dst)
  -> 0x563A6 decompresses the compressed metatile stream into the name table
per-column descriptor page (0x502CC):
  0x10D000[col] = 0x1691C + col*0x22C0 + (A5+0x13E)*0x40      (col 0..15; 0x40-byte page)
  a 0x40-byte page = 16 four-byte entries { word0, word1 }:
    word0 (@base)   -> 0x10D080[col]  : the TILE word (visual) written to the name table (0x55904)
    word1 (@base+2) -> 0x10D040[col]  : 16-bit ROM pointer to that column's COLLISION record
  grid_word = col_record uniform/4x4 lookup (0x559B2); MARKER = grid_word >> 8
```

The arcade stores the scene **compactly**: a compressed metatile stream plus a per-column 0x40-byte
descriptor page of 16 `{tile-word, collision-record-pointer}` entries, re-based per progression by
`(A5+0x13E)*0x40`. The Genesis realization must, per cell, **translate `word0` into a Genesis Plane-A name
word** (tile id + palette line + flip/priority) while **carrying `word1`'s collision meaning through
unchanged**. The arcade data is the single source; the Genesis side only re-expresses the *visual* half.
This split is the crux of Problem B (§4).

## 4. Why R2-S1 can have working collision but incorrect Plane A graphics (Problem B)

In `genesistan_hook_pc080sn_descriptor_rebuild` the two halves of a cell come from different sources:

- **Collision word** = the **retained arcade `word1`/collision-record value** (`D2`). This is arcade data,
  authoritative for every round. R2-S1 collision therefore works.
- **Visual name word** = a lookup in an **offline-authored LUT**
  (`genesistan_plane_a_authored_descriptor_visuals` / `fg_boundary_active_lut` /
  `genesistan_pc080sn_tile_vram_lut`), selected by `genesistan_current_scene_id`.

The authored LUT is generated by `tools/translation/compile_pc080sn_genesis.py`, whose `AuthoredLayerA`
is documented in-source as *"Offline-only Palette Composer realization for the two authored R1 scenes."*
Its `SCENES` tuple authors **only**:

```
("context:gameplay.r01.p01",   range(0,16),  .../round1_phase1/plane_a_uses.json)
("PAL-R1-S2-PLANEA-CASTLE",    range(16,22), .../subround_corpus/PAL-R1-S2-PLANEA-CASTLE/plane_a_uses.json)
```

Records 22+ (R1-S3 boss tail and **all of R2–R6**) have **no authored realization** — `realize()` returns
`None` for them and the visual falls back to the raw base-LUT/epoch-patch decode
(`precompute_pc080sn_tile_lut.py`, `RECORD_EPOCHS`). That raw decode is correct **only where R2's tile
codes/palette lines coincide with R1's vocabulary**. R2-specific tiles — new metatiles, or shared tile
codes that need a different palette line in R2 — are realized wrong. Result: *some Plane A tiles correct,
some incorrect, collision unaffected* — exactly the reported symptom.

So R2-S1 is **not** the checkpoint-absence defect. Record `0x17` (R2-S1 entry) **is present** in
`scene_fill_maps` (§5). R2-S1's problem is the **round/scene authoring gap** in the visual LUT, not a
missing reseed map.

## 5. Why the segment-4 checkpoint regressed (Problem A)

`build/pc080sn_boundary/scene_fill_maps.bin` is a 46-record offset table. Enumerated (read-only):

```
PRESENT records: 0x00, 0x10, 0x16, 0x17, 0x27, 0x2d
ABSENT  records: 0x01..0x0F, 0x11..0x15, 0x18..0x26, 0x28..0x2c   (offset == 0xFFFFFFFF)
checkpoint 0x0B present? NO      R2-S1 entry 0x17 present? YES
```

The present records are the **stage/epoch-entry representatives** (R1-S1 start `0x00`, R1-S2 castle start
`0x10`, boss-tail `0x16`, R2 start `0x17`, and the later epoch heads `0x27`/`0x2d`), matching the
generator's `RECORD_EPOCHS` boundaries and the `STAGE_TABLE` (`0x5073A`) start-segment semantics. The R1-S1
segment-4 **checkpoint is a *mid-stage* progression `0x0B`**, which is not a stage/epoch entry, so it is
absent. When the player respawns there, `genesistan_plane_a_scene_scroll_reseed_native` indexes
`scene_fill_maps[0x0A]`, finds `0xFFFFFFFF`, and returns without staging/publishing — Plane A is left
incomplete. 0503 never had this problem because it published the authoritative `staged_fg_buffer` wholesale,
with no dependence on the record being an "entry."

## 6. Do Problem A and Problem B share a cause?

**Shared root, distinct defects — along two orthogonal axes.**

| | Problem A (checkpoint) | Problem B (R2-S1) |
|---|---|---|
| Axis of the gap | progression / **record** | **round** / scene |
| Failing table | `scene_fill_maps` (entry-only) | authored visual LUT (R1-only) |
| Symptom | **nothing** published → incomplete | **wrong** visual published → partially incorrect |
| Collision | n/a (nothing drawn) | **correct** (retained arcade word) |
| Fixing one fixes the other? | No | No |

Both exist **only because** 0504 replaced one authoritative wholesale publish (0503's full-plane DMA of the
arcade-driven `staged_fg_buffer`) with two independently-authored partial tables. Neither table alone
reconstitutes what the wholesale publish gave for free.

## 7. Defect classification for R2-S1 (Problem B)

Per the visual-realization failure modes, R2-S1 is a **source-coverage** defect, not a projection bug:

- **Not** wrong tile *placement* (descriptor walk is arcade-driven and shared with R1 → geometry/collision correct).
- **Not** wrong *residency/scroll* (reseed ran; record `0x17` present).
- **Is** wrong **tile-code → Genesis name-word realization and/or palette-line** for R2-specific descriptors,
  because the authored LUT has no R2 entries and the raw fallback decode does not reproduce R2's intended
  visual/palette for tiles that diverge from R1.

## 8. Was 0503's staged data complete and authoritative, or did it only happen to work?

**Authoritative, by construction — not coincidence.** `staged_fg_buffer` is filled by the arcade
descriptor-chain producer for the *current* progression and retains the arcade collision word, so it is
correct for any record and any round. 0503's only "luck" was that it published *all* of it; the data itself
was never checkpoint- or round-specific. This matters for the fix: restoring a wholesale (or at least
record-agnostic) publish of the authoritative buffer addresses the **record axis** of Problem A directly,
but it does **not** fix Problem B, because the buffer's *visual half* still comes from the R1-only authored
LUT. Problem B must be fixed at the authoring/LUT source regardless of how the publish is shaped.

## 9. Handoff for Cody (what to inspect / change)

**A. Confirm the two axes independently.** Record axis: `scene_fill_maps` present set
`{0x00,0x10,0x16,0x17,0x27,0x2d}` vs. checkpoint `0x0B`. Round axis:
`compile_pc080sn_genesis.py::AuthoredLayerA.SCENES` = R1 only.

**B. Problem A — record-axis fix.** Either (preferred, matches the holistic mandate) restore a
**record-agnostic publish of the authoritative `staged_fg_buffer`** at the boundary so mid-stage respawns
publish the already-correct buffer (this is what 0503 did; confirm it fits the current VBlank/DMA budget per
the central `dma.s` publisher), **or** extend `scene_fill_maps` generation to emit maps for mid-stage
records too. Prefer the former: it removes the entry-only precompiled dependency rather than growing it.

**C. Problem B — round-axis fix.** Extend `AuthoredLayerA.SCENES` (and the corresponding
`analysis/graphics_optimizer/.../plane_a_uses.json` corpora) to author R2-S1 (and onward) so R2-specific
descriptor visuals have a real Palette-Composer realization instead of the raw fallback. Verify against the
R2 `0x562CA[round]` background table and the R2 descriptor pages.

**D. Keep collision untouched.** The retained arcade `word1`/collision word is authoritative; do not route
collision through the authored LUT. R2-S1 collision correctness is the proof this separation already holds.

**E. Minimum correct behavior to validate.** Mid-stage R1-S1 checkpoint respawn publishes a complete Plane A
(Problem A); R2-S1 Plane A tiles all correct with collision unchanged (Problem B). Validate on
**GENESIS NTSC MAME** (`genesis`), not PAL.

**F. Do not create a hybrid of per-scene gates.** Both fixes should make the realization *more* complete
along their axis, not add scene-specific conditionals that select legacy vs. native per record/round.

**G. Watch the VBlank budget.** If B restores a wholesale publish, confirm it commits within VBlank through
the central `dma.s` publish-first path; a full-plane DMA was part of why display-ON workarounds appeared
earlier, so measure rather than assume.

## 10. Evidence index (all read-only)

- `apps/rastan-direct/src/tilemap_hooks.s` — `genesistan_hook_pc080sn_descriptor_rebuild` (authoritative
  producer: arcade pointer table `0x00FF1040`, visual `D0` via LUT, retained collision `D2`);
  `genesistan_plane_a_scene_scroll_reseed_native` (0504 precompiled reseed, no-op on absent record).
- `apps/rastan-direct/src/fg_tile_cache.s` — `fg_boundary_install_post_reseed` (0503 full-plane DMA removed in 0504).
- `build/pc080sn_boundary/scene_fill_maps.bin` — present records `{0x00,0x10,0x16,0x17,0x27,0x2d}`; `0x0B` absent.
- `tools/translation/compile_pc080sn_genesis.py` — `AuthoredLayerA` "two authored R1 scenes"; `SCENES`; `RECORD_EPOCHS`.
- `tools/translation/precompute_pc080sn_tile_lut.py` — raw base-LUT/epoch fallback decode.
- `analysis/decompilation/c/rastan_scene_map.c` — H11/H12/H13 proven descriptor/metatile/collision chain (§3).
- `tools/translation/verify_plane_a_scene_fill_maps.py` — `RECORDS=46`, map geometry.

## 11. Honest limits

- No traces and no ROM build were run (per prompt). All claims are static: source, generated artifacts, and
  the committed decompilation.
- I did not enumerate *which specific* R2-S1 tiles diverge from R1 vocabulary; that requires decoding R2's
  `plane_a_uses` corpus, which is authoring work owned by Cody. §7 classifies the defect; it does not list
  every affected tile code.
- "Later epoch heads `0x27`/`0x2d` present" is reported as-is from the offset table; their round/subround
  attribution beyond R1–R2 was not needed for A/B and is not asserted here.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0042`
