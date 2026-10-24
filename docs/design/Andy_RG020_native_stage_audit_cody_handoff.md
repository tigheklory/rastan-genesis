# Andy — RG-020: Native Stage Coverage Audit & Cody Implementation Handoff

**Task:** RG-020 (analysis/architecture/planning only — no production code, no new ROM) ·
**Agent:** Andy (Opus) · **Tested build:** 0495 · **Date:** 2026-10-24.

**Andy analyzes and designs; Cody implements in a later numbered assignment.** Every file/routine/offset
below is cited so Cody does not repeat the investigation.

---

## 0. One-paragraph architecture verdict

The native Genesis port is **Stage-1-only for backgrounds and palettes, but broadly covered for sprites.**
`tools/translation/compile_pc080sn_genesis.py` converts **Round 1 only** (hardcoded
`BOUNDARY_ROUND1_EPOCH_RECORDS`, records 0–20, `stage_index=0`); `apps/rastan-direct/src/scene_load.s`
dispatches scene-ids to **Stage-1-only** preload packages; `specs/palette_decisions.json` holds **23
Stage-1 decisions (mostly provisional)**; PC090OJ sprite conversion is a **universal frame-table index**
(player/enemies render across rounds). Hence later rounds are *playable but blank/wrong-colored*, not
crashed. Fixing later rounds is fundamentally an **offline data-coverage** problem (per-round PC080SN
patterns/LUT/CRAM + scene packages + scene-source ranges + palette decisions), not a renderer rewrite.

---

## 1. How native background rendering is wired (evidence)

1. **Offline BG compiler** `tools/translation/compile_pc080sn_genesis.py`:
   - Arcade tables it decodes: `STAGE_TABLE 0x5073A` (stage `a5@0x1242` → start segment `a5@0x13E`),
     `SEED_TABLE 0x50EE0`, `STREAM 0x50F6B`, `TM0_TABLE 0x507C5` (segment → Plane-B descriptor pair),
     `PLANE_B_DESC_TABLE 0x3951C`. `STAGE_GROUP_SIZE = 23` (round × 23, per `0x452A8`).
   - It decodes `decode_stage_records(mc, stage_index)` — **defaulted to `stage_index=0` (Round 1)** — and
     groups records into `BOUNDARY_ROUND1_EPOCH_RECORDS` = epochs over records **0–20** only, with
     hardcoded `BOUNDARY_TRANSITION_DEFS` (rope→waterfall, etc.). Outputs `patterns.bin`, `lut_base.bin`,
     `cram_epochs.bin` + metatile/plane-B records.
   - **Records 21–22 are NOT in any epoch** (epoch 5 = `range(16,21)`), so the tail of Round 1 (boss
     room, see §4) has no converted Plane-A.
2. **Scene preload packages** (`apps/rastan-direct/src/scene_load.s`): `title`, `gameplay`, `endround`,
   `gameplay_cave`, `stage1_cave_s4/s5/s6`, `stage1_seg1/seg2`. **All Stage-1.** Dispatched in
   `load_scene_tiles` by a scene index `%d6` (1=gameplay, 2=endround, 3=cave, 4/5/6=per-segment caves
   selected by `a5@0x13E`, 7/8=seg1/seg2). `move.b %d5, genesistan_current_scene_id` (scene_load.s:152).
3. **Scene identification + residency selection** (`apps/rastan-direct/src/tilemap_hooks.s`): the gameplay
   scene is detected by the arcade **strip-source address** falling inside `genesistan_scene_a0_ranges`
   (`genesistan_scene_a0_lo/hi`), setting `genesistan_current_scene_id = SCENE_GAMEPLAY_ID (1)`
   (tilemap_hooks.s:200–206, 1831–1840). Inside gameplay, the segment `a5@0x13E` selects the per-segment
   residency (ids 4/5/6; default outdoor id 1) at tilemap_hooks.s:1744–1748.
4. **Palette**: `apps/rastan-direct/src/palette_hooks.s` installs lines keyed on
   `genesistan_current_scene_id == 1` (e.g. :181/:197/:334/:441) from `specs/palette_decisions.json`
   (the sole registry; 23 decisions, all Stage-1; status mix proven 3 / decided 5 / provisional 14 /
   unknown 1).
5. **Sprites**: PC090OJ (`pc090oj_hooks.s`, `pc090oj_assets.s`, `tools/translation/
   preconvert_pc090oj_tiles.py`, `precompute_pc090oj_frame_table.py`) is a **dense universal index over
   program descriptors** (not round-scoped). This is why gameplay/sprites run in later rounds.
6. **DMA/publication**: `apps/rastan-direct/src/dma.s` is the single VBlank publisher; `scene_load.s`
   runs a presentation-readiness handshake (`genesistan_presentation_mark_unsafe` /
   `publish_complete` / `readiness`, scene_load.s:6–9, 200–259) while display is off.

---

## 2. 18-subround native coverage matrix

Status codes: **(1)** functioning · **(2)** converted-but-not-selected · **(3)** selected-but-loaded/
published-wrong · **(4)** not-yet-converted · **(5)** partial · **(6)** blocked by dependency.

Evidence classes: **S**=static source/asset, **E**=emulator-init observation (this audit), **H**=Tighe
hardware (BlastEm). Sprites/gameplay are a separate column from backgrounds because they have separate
pipelines.

| Sub | BG Layer A/B | Sprites/gameplay | Palette | Evidence / cause |
|---|---|---|---|---|
| 1-1 | (1) | (1) | (1) decided/proven | S+H baseline |
| 1-2 | (5) castle Plane-A wrong | (1) | (3/5) provisional/missing castle | §3 |
| 1-3 | (5) boss-room records 21–22 unconverted | (1) | (5) provisional | §4 |
| 2-1 | (4) content not converted | (1) | (4) no R2 decisions | **E: scene_id=1, seg=0x18** → selected, no data |
| 2-2 | (4) | (5?) | (4) | S (round-1-only); needs E |
| 2-3 | (4) + (6) post-boss | (5?) | (4) | S; needs E |
| 3-1 | (2) scene not recognized | (?) | (4) | **E: scene_id=0, seg=0x2F** → source outside `scene_a0_ranges` → blank screen |
| 3-2/3-3 | (2)/(4) | (?) | (4) | needs E (likely same scene-detection gap as 3-1) |
| 4-1 | (4) content not converted | (1) | (4) | **E: scene_id=1, seg=0x46** → selected, no data; H "no music" |
| 4-2 | (4) | (1) | (4) wrong palette | H "Aggressive World, missing BG, wrong palette" |
| 4-3 | (4) + (6) post-boss | (5) | (4) | H "frozen boss killable, no progression" |
| 5-1…6-3 | (4) and/or (2) | (?) | (4) | **UNRESOLVED per-stage** — run the §10 init probe per ROM to split (2) vs (4) |

**Two distinct later-round BG failure modes, proven by emulator init (this audit):**
- **Mode A — selected, content absent (R2, R4):** `genesistan_current_scene_id = 1`, gameplay inits,
  sprites run, but PC080SN patterns/LUT/CRAM for that round were never generated → blank/garbage planes.
- **Mode B — scene not recognized (R3):** the round's arcade strip-source falls outside
  `genesistan_scene_a0_ranges`, so `genesistan_current_scene_id` stays 0 → no residency load → blank
  screen with music. R5/R6 are unclassified; the §10 probe splits them cheaply.

Do not assume all missing backgrounds share one cause: at minimum Modes A and B both exist.

---

## 3. Deep dive — R1-S2 (castle) [Phase A, highest priority]

R1-S2 is *within Round 1* (stage `0x10`), so some conversion exists, but three independent defects:

### 3a. Incorrect Layer A tiles
- **Root cause (verified at the architecture level):** the castle segments are selected through the
  gameplay residency path (`tilemap_hooks.s:1744–1748`, `a5@0x13E` → residency id). The converted Round-1
  epochs/residencies (`BOUNDARY_ROUND1_EPOCH_RECORDS`, records 0–20; scene packages `gameplay_cave`,
  `stage1_cave_s4/5/6`, `stage1_seg1/2`) were authored for the **outdoor + small-cave** segments. The
  castle-interior segment(s) either select a small-cave residency (wrong tileset) or fall on an epoch
  whose Plane-A set does not contain the castle metatiles.
- **Cody references:** confirm the castle start segment via `STAGE_TABLE 0x5073A[stage 0x10]` →
  `a5@0x13E`; cross-check which epoch in `compile_pc080sn_genesis.py` owns that record and which
  `scene_preload_*` the `load_scene_tiles` dispatch (`scene_load.s:66–103+`) selects for it; compare the
  epoch's `planeA` cell set against the arcade castle metatiles for those records.
- **Likely correction:** give the castle its **own residency epoch + preload package** (a new
  `genesistan_scene_preload_stage1_castle*` with the castle Plane-A set), and route the castle segment to
  it in both `scene_load.s` and `tilemap_hooks.s:1744–1748`, instead of reusing a small-cave residency.
- **UNRESOLVED:** exact castle record range and whether the castle metatiles are already in
  `patterns.bin` (Cody must diff the epoch `planeA_codes` in `build/.../pc080sn/manifest` against the
  arcade castle records). Evidence to settle: the compiler's per-epoch `planeA` dump vs the castle
  records' TM0/Plane-B descriptors.

### 3b. Incorrect palette
- **Root cause:** `palette_decisions.json` has no castle-specific family (all 23 are Scene-1; castle/cave
  entries are provisional). `palette_hooks.s` installs lines gated on scene_id==1 with the Scene-1 lines.
- **Correction (needs Tighe):** author castle palette families in **Palette Composer** as new scene-
  scoped decisions, then add a castle scene-id branch in `palette_hooks.s`. **Do NOT invent RGB mappings**
  — cite the Palette Decision IDs and let Tighe approve in Composer. Preserve the approved R1-S1 mappings
  (separate scene key; do not edit existing decision rows).
- **Dependency:** requires a distinct castle scene-id/line set so the castle palette does not overwrite
  R1-S1's.

### 3c. Impassable point
- **Candidate causes, in priority order (NOT a position/collision hack):**
  1. **Native scene-readiness stall** — if the castle segment transition re-enters `load_scene_tiles`
     for a residency that never completes `genesistan_presentation_publish_complete`/`readiness`
     (scene_load.s:200–259), the arcade progression can wait on the presentation latch. Check whether the
     castle segment maps to a residency id that exists.
  2. **Missing BG collision side-channel** — `tilemap_hooks.s:1792–1970` reconstructs the original
     `0x559B2` collision-map side-channel from the BG producer, scoped to `SCENE_GAMEPLAY_ID` and
     `a5@0x13E`. If the castle segment's BG strip isn't recognized, the collision side-channel may be
     absent/incorrect → the arcade thinks a wall/floor is present.
  3. Incorrect scene/segment transition (castle segment index not advancing).
- **Evidence Tighe must provide to localize it:** the approximate `player_x`/on-screen location of the
  impassable point and whether the **camera stops scrolling** there (scroll-stop ⇒ cause 1/3;
  player-stops-but-camera-free ⇒ cause 2). Cody can then read `a5@0x13E`, `genesistan_presentation_
  readiness`, and the collision side-channel at that point via a targeted MAME probe.

---

## 4. Deep dive — R1-S3 (boss) [Phase B]

### 4a. Incorrect Layer A (boss room)
- **Root cause (verified):** `BOUNDARY_ROUND1_EPOCH_RECORDS` stops at record 20; **records 21–22 (the
  Round-1 boss tail) are unconverted.** Boss plays on leftover/incorrect Plane-A.
- **Correction:** add the boss records to the epoch set in `compile_pc080sn_genesis.py` (a new epoch
  covering 21–22, with its Plane-A/Plane-B descriptors and a boss-room preload package in `scene_load.s`).
- **Dependency:** boss-room palette family (Composer, Tighe).

### 4b. Post-boss freeze + backgrounds vanish + Re-In-Carnation
- **Verified distinction (this is the key deliverable for Phase B):** it is **NOT a 68000 lockup.**
  Evidence that the game-state machine advances past the boss:
  - Rastan + HUD stay visible and animate → the retained arcade gameplay/sprite code is still running.
  - Music eventually changes to Re-In-Carnation → the arcade **sound request state advanced** (the
    producer at the R1 music sequencer `0x055DDC` reaches a new substate and emits a BGM command; see
    §8). A frozen 68000 could not emit a later sound command.
  - Therefore the failure is a **native scene-load/content failure for the post-boss scene**: the arcade
    requests the next scene, the background planes are torn down (`mark_unsafe`), and the new scene's
    PC080SN content/residency does not exist (post-R1 not converted) → planes never republish, and the
    native presentation-readiness latch may never re-arm, stalling visible progression while sprites run.
- **Cody references:** trace the original post-boss transition — the outer-controller scene re-entry the
  compiler already models (`decode_stage_records` "event bytes freeze publication and cause an outer-
  controller scene re-entry"), and the `STAGE_TABLE`/`a5@0x1242` advance after boss death. In the native
  layer, instrument `load_scene_tiles` / `genesistan_presentation_readiness` across the boss-death frame.
- **Testable expected state sequence (for Cody to assert):** boss HP→0 ⇒ `a5@0x1242` advances to the next
  stage ⇒ `a5@0x13E` moves to the new start segment ⇒ a BGM command is emitted (§8) ⇒ `load_scene_tiles`
  is invoked for the new scene. The break is at the last step (no native content/residency).
- **UNRESOLVED:** the exact next stage/scene index after R1 boss and whether it is R2-S1 or a round-end
  interstitial. Evidence to settle: a MAME trace latching `a5@0x1242`, `a5@0x13E`, `genesistan_current_
  scene_id`, and the PC060HA command across the boss-death transition (bounded, _S1-3 ROM, no long play).

---

## 5. Deep dive — R2-S1 (blank backgrounds) [Phase C — establishes the reusable approach]

- **Verified (E):** `scene_id=1` (gameplay recognized), `seg=0x18`. So **selection works; the PC080SN
  content for Round 2 was never generated** (compiler `stage_index=0` only). Mode A.
- **Reusable architecture for all later rounds (design intent — do NOT convert all six now):**
  1. **Parameterize the compiler per round.** `compile_pc080sn_genesis.py` already takes `stage_index`
     and decodes `STAGE_GROUP_SIZE`-sized groups. The hardcoded `BOUNDARY_ROUND1_EPOCH_RECORDS` /
     `BOUNDARY_TRANSITION_DEFS` must become **per-round tables** (derive epoch grouping from the round's
     records + transitions, or supply a per-round constants file). Emit per-round `patterns/lut/cram`
     asset sets under a round-keyed directory.
  2. **Per-round scene packages.** Add `genesistan_scene_preload_stageN_*` symbols + `load_scene_tiles`
     dispatch entries (scene_load.s), selected by round (derivable from `a5@0x1242 / 23` or the segment
     range) — NOT a copy of the renderer, only new data + a dispatch row.
  3. **Per-round residency selection.** Extend the `a5@0x13E` → residency mapping (tilemap_hooks.s:1744)
     to the round's segment range.
  4. **Scene-source ranges.** Extend `genesistan_scene_a0_ranges` / `scene_a0_lo/hi` so each round's map
     strip-source is recognized as gameplay (fixes Mode B, e.g. R3).
  5. **Per-round palette decisions** authored by Tighe in Palette Composer (new scene keys), consumed by
     `palette_hooks.s` via a scene/round branch.
  - **Reuse, don't duplicate:** the renderer, LUT format, metatile/plane-B record format, DMA publisher,
    and residency machinery are round-agnostic. Only the **data** (patterns/LUT/CRAM/packages/ranges/
    palette) is per-round. Avoid a second renderer or runtime tilemap reconstruction.
- **Palette decisions requiring Tighe:** all Round-2 families (none exist). Cite new Decision IDs; no
  invented mappings.

---

## 6. Later-round failure map (R3–R6)

- **Shared prerequisite for every later round:** per-round PC080SN content (§5.1) + scene package (§5.2)
  + residency range (§5.3) + palette decisions (§5.5). This is the dominant missing-content cause (Mode
  A), repairable once as reusable infrastructure.
- **Additionally for rounds like R3 (Mode B):** `genesistan_scene_a0_ranges` extension (§5.4) is a
  *separate* prerequisite — without it the scene is never recognized and no amount of content helps.
- **Boss sub-rounds (x-3):** add the post-boss transition handling (§4b) once; it recurs each round.
- **Classify R5/R6 and R3-2/3-3 with the §10 init probe before Cody starts**, so each is tagged Mode A
  (content) vs Mode B (scene-source) vs boss-transition. Do not full-playthrough-debug them.

---

## 7. Phased, Cody-ready worklist

Each item: **Problem / Root cause / Arcade ref / Genesis ref / Correction / Dependencies / Performance /
Verification / Regression risk.**

### PHASE A — R1-S2 castle (graphics + palette + impassable)
- **A1 — Castle Plane-A tiles.**
  1. *Problem:* R1-S2 Layer A shows wrong tiles. 2. *Root cause:* castle segment reuses a small-cave
  residency / epoch lacking castle metatiles (§3a). 3. *Arcade ref:* `STAGE_TABLE 0x5073A[0x10]`→segment,
  that record's `TM0_TABLE 0x507C5` / `PLANE_B_DESC_TABLE 0x3951C` pair. 4. *Genesis ref:*
  `compile_pc080sn_genesis.py` (epoch owning the castle record), `scene_load.s` dispatch,
  `tilemap_hooks.s:1744–1748`. 5. *Correction:* dedicated castle residency epoch + `scene_preload`
  package + route the castle segment to it. 6. *Deps:* castle palette (A2). 7. *Perf:* offline data +
  one residency load at scene entry (display-off); no added per-frame 68000 cost. 8. *Verify:* static —
  epoch `planeA` set == arcade castle metatiles; emulator-init — `_S1-2` shows castle residency id and
  non-blank Plane-A; **H** Tighe visual. 9. *Regression:* must not change R1-S1 residencies/packages
  (separate scene id).
- **A2 — Castle palette.** Problem: wrong colors. Root cause: no castle palette family (§3b). Correction:
  Tighe authors castle families in **Palette Composer**; add castle scene branch in `palette_hooks.s`;
  update `palette_decisions.json` (new IDs, in the same task). Deps: A1 scene id. Perf: none (CRAM at
  scene entry). Verify: registry IDs present + `palette_hooks` installs them for the castle scene; H
  visual. Regression: do not edit approved R1-S1 decision rows. **Requires Tighe's Composer review.**
- **A3 — Impassable point.** Problem: progression blocked. Root cause: UNRESOLVED (§3c, three
  candidates). Correction: pending Tighe's location/scroll observation (§3c) + a targeted probe; then fix
  the identified cause (readiness latch / collision side-channel / segment transition). Do not add a
  position workaround. Verify: _S1-2 playthrough past the point (H). Regression: R1-S1 traversal.

### PHASE B — R1-S3 boss + post-boss
- **B1 — Boss-room Plane-A (records 21–22).** Root cause: records 21–22 unconverted (§4a). Arcade ref:
  records 21–22 TM0/Plane-B. Genesis ref: add epoch in `compile_pc080sn_genesis.py` + boss preload in
  `scene_load.s`. Correction: convert boss records; route boss segment. Deps: boss palette (Composer).
  Perf: offline. Verify: static epoch coverage; _S1-3 non-blank boss Plane-A; H. Regression: R1 Phase-2
  epochs 16–20 unchanged.
- **B2 — Post-boss progression.** Problem: freeze + planes vanish. Root cause: native post-boss
  scene-load/content failure, NOT 68000 lockup (§4b, verified via sprite+audio advancement). Arcade ref:
  post-boss outer-controller scene re-entry + `a5@0x1242` advance. Genesis ref: `load_scene_tiles` /
  `genesistan_presentation_readiness`; next-scene content. Correction: provide the post-boss scene
  content/residency (ties into Phase C/D) and ensure the readiness latch re-arms for it. Deps: next-scene
  conversion. Perf: offline + scene load. Verify: trace asserts the expected sequence (§4b); H. Regression:
  endround/normal scene transitions.

### PHASE C — R2-S1 + reusable per-round approach
- **C1 — Parameterize the BG compiler per round** (§5.1). Root cause: `stage_index=0` + hardcoded Round-1
  epoch/transition tables. Genesis ref: `compile_pc080sn_genesis.py`. Correction: per-round epoch/
  transition derivation + per-round asset output. Perf: offline only. Verify: generates R2 assets;
  `verify_pc080sn_native_metatiles.py`/`verify_pc080sn_plane_b_visual_records.py` pass for R2. Regression:
  R1 output byte-stable (snapshot test).
- **C2 — R2 scene package + dispatch + residency + a0-range** (§5.2–5.4). Genesis ref: `scene_load.s`,
  `tilemap_hooks.s` (residency + `scene_a0_ranges`). Correction: add R2 package/dispatch/residency/range.
  Verify: `_S2-1` `scene_id=1` with non-blank planes (E) + H. Regression: R1 dispatch/ranges unchanged.
- **C3 — R2 palette** (Composer, Tighe). As A2 for R2 families.

### PHASE D — shared infra for remaining rounds (bounded)
- **D1 — Scene-source range coverage for Mode-B rounds (R3, +others per §10):** extend
  `genesistan_scene_a0_ranges` so each round registers as gameplay. Verify: init probe shows `scene_id=1`.
- **D2 — Generalize the per-round data generation** proven in Phase C to R3–R6 (data only; one round at a
  time, each gated by Tighe palette authoring). **Do NOT expand D into an unbounded rewrite** — it is
  per-round data + dispatch rows + palette, reusing the Phase-C mechanism.
- **D3 — Reusable post-boss transition** (from B2) applied to each boss sub-round.

---

## 8. Audio observations (recorded only — do NOT modify audio here)

- Most music-producing later stages play Aggressive World because the native dispatch maps the
  appearance cue `$25` → Aggressive World (AUDIO-015) and the authentic per-round BGM commands are not
  all mapped. R1-S2 castle uses `$27` → Re-In-Carnation (AUDIO-015); the R1 music sequencer is at arcade
  `0x055DDC` (substate `a5@0x13AA`: substate 1→`$19` Aggressive, substate 9→`$27`).
- **R1-S3 post-boss "eventually Re-In-Carnation" is positive evidence the 68000 advanced** past the boss
  (§4b) — the sequencer reached a later substate and emitted a BGM command. Relevant to Phase B diagnosis
  only. Audio mapping fixes are out of scope and will be separately numbered.

---

## 9. Regression & performance guardrails (apply to all phases)

- Preserve Build 0492 accepted behavior, the seven-ROM family, the nine-song audio, Palette Composer
  approved decisions, and the `_Sx-y` variant system. R1-S1 must stay byte/behavior-stable (snapshot the
  R1 PC080SN assets before changing the compiler; the canonical gate + `verify_*` must still pass).
- The 68000 is cycle-constrained: **all new work is offline conversion + scene-entry (display-off) loads
  + precomputed LUT/CRAM.** Do not add per-frame tilemap reconstruction or runtime translation. VRAM:
  reuse the existing BG tile region (slots 20–1342) and residency model; per-round data swaps at scene
  entry, not per frame. DMA stays owned by `dma.s`.

## 10. Verification tooling & evidence discipline

- **Static:** `verify_pc080sn_native_metatiles.py`, `verify_pc080sn_plane_b_visual_records.py`,
  `verify_subround_variants.py`, canonical gate.
- **Emulator-init (cheap, reliable, no long play):** the `_Sx-y` ROMs + a scene-id/segment probe
  (pattern used in this audit: read `genesistan_current_scene_id` @ `0x00FFC63C`, `a5@0x1242`,
  `a5@0x13E`, `state0/2` at ~frame 300–900 after the standard coin/start). **Cody/Tighe should run this
  per R3-2/3-3 and R5–R6 ROM to tag Mode A vs Mode B before implementation.**
- **Gameplay validation / hardware:** Tighe in BlastEm / real Genesis (the only authority for "stage is
  correct and playable"). This audit changed no production code and makes **no claim that any defect is
  repaired.**

## 11. Unresolved questions (explicit) and evidence needed
1. Exact castle record range and whether castle metatiles already exist in `patterns.bin` — *diff the
   compiler's per-epoch `planeA` dump vs the arcade castle records.*
2. R1-S2 impassable-point cause — *Tighe: location + does the camera stop scrolling there.*
3. Post-R1-boss next stage/scene index and the precise stall step — *bounded MAME trace of `a5@0x1242`,
   `a5@0x13E`, `scene_id`, PC060HA command across boss-death on `_S1-3`.*
4. R3-2/3-3, R5-x, R6-x Mode A vs Mode B — *run the §10 init probe per ROM.*
5. Whether R2/R4 "glitched vs blank" differences imply partial residual R1 data vs pure absence — *E
   observation of the published plane contents per ROM.*
