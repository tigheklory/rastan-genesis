# Sonic 1 vs Rainbow Islands — Plane A/B Architecture, and Title-Screen Completion Status

**Author:** Andy · **Date:** 2026-09-07 · **Type:** Architecture / RE / Verification
**Build produced:** NO (see §16). Baseline: Build **0348** (counter=348), display-off variant
`dist/rastan-direct/rastan_direct_video_test_build_0348_do.bin`.

---

## 1. Phase 0 baseline statement

- **Classification:** ARCHITECTURE + RE, with conditional implementation. Net result this task:
  analysis/RE + report; no ROM (justified in §16, §24).
- **Relevant KNOWN_FINDINGS / priors:** the native-replacement policy
  (`docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` §9 checklist); the central-publisher
  model (`Andy_central_vblank_dma_publisher_brief.md`, dma.s Builds 0343–0348); the OPT-003
  classification as a **synthetic gate artifact** (`Andy_pure_publisher_audit_palette_gating_and_opt003.md`
  §7); the vblank-budget comparison (`The VBlank Budget` artifact + this session's exchanges).
- **Rediscovery hazards (HIGH) touched:** the canonical seven-epoch gate is a KNOWN INVALID
  synthetic injection (proven last task) — do not treat its pass/fail on publication-timing changes
  as truth; the arcade-WRAM-literal-aliases-ROM class (Segment-5 crashes); do not rediscover the
  central-publisher rationale.
- **Open issues touched:** **OPEN-001** (title/attract graphics completeness) — its listed symptoms
  are from Build 0153 and are STALE; measured current state below. **OPEN-018/OPEN-001** native
  PC080SN level/map rendering (the plane pipeline this report designs toward).
- **Contradiction with a CONFIRMED/STRONG finding:** none introduced. This report UPDATES the stale
  OPEN-001 title symptom list with current measured evidence (Option A/B; flagged for Tighe, not
  silently revised).

---

## 2. Current accepted Genesis baseline

Build **0348** is the clean gate-passing baseline (== 0346 behaviour; 0347 is throwaway). Its
display-off variant `_0348_do.bin` is the immediate proof vehicle for this task.

---

## 3. Current display-off TITLE baseline (measured, not assumed)

**Measured**, Build 0348 display-off, stable title/story window (scene 0, 601 frames sampled this
session):

| Per-frame publication on the static title | Measured |
|---|---|
| Plane B dirty rows | avg 0.87; **0 on 95.7% of frames** (max 32 only on text/transition bursts) |
| Plane A dirty rows | avg 0.38; 0 on 95.7% of frames |
| `fg_narrow_desc_count` | 0 |
| `tiles_dirty` | 0 of 601 frames |
| sprite-pattern DMAs | 0 |
| palette / SAT / scroll | 1 each, unconditional (64w CRAM + 320w SAT + PIO) |

**Visual (Tighe's 0348_do screenshots this session):** RASTAN sword/logo, TAITO logo, copyright
text, story throne + narration text, HIGH SCORE / 1UP / 2UP headers, "INSERT COIN(S)" — **all
present and correct.** No black band on the static title/story; no stale material between states in
the captured frames.

**Conclusion:** the display-off title screen **already renders completely and correctly**. The
OPEN-001 symptom list ("sword/logo absent; TAITO incomplete; stale text; dot rows"), dated Build
0153, is stale — those were fixed across the intervening ~195 builds. The title is already in the
ideal "seed once, then near-zero steady-state publication" shape (≈384 words/frame, fits vblank).
There is **no title rendering defect to implement a fix for** in Build 0348.

### 3a. Title element ownership / status matrix

| Element | Plane/Sprite | Arcade semantic owner | Genesis native owner | Publication | Status |
|---|---|---|---|---|---|
| RASTAN sword/logo | Plane (tilemap) | title scene-seed (PC080SN load) | scene_load + plane hooks → staged_fg/bg | one-shot seed rows, then 0 | **correct** |
| TAITO logo | Plane | title scene-seed | same | one-shot seed | **correct** |
| Copyright / labels text | Plane | frontend text producer | plane hooks | one-shot / on text change | **correct** |
| Story throne + narration | Plane + text | story-scene producer | scene_load + plane hooks | on state change | **correct** |
| HIGH SCORE / 1UP / 2UP | Sprite | PC090OJ title score/label lane | pc090oj native lane (`.Lnq_title_emit_scores/labels`) | SAT every frame | **correct** |
| "INSERT COIN(S)" | Plane text | frontend | plane hooks | on blink | **correct** |

Failure boundary: **none observed** on the static title in Build 0348 display-off.

---

## 4. Sonic 1 — architectural findings (docs/reference/s1disasm)

- **Semantic ownership:** `DeformLayers` computes the camera and sets per-edge scroll flags;
  `LoadTilesAsYouMove` is **edge-gated** — when the camera crosses a 16px block boundary it draws
  exactly the one **entering row or column**. No boundary crossing → no tilemap work.
- **Plane representation:** a compact **256×256 block/metatile level map** decoded on demand; the
  VDP nametable is written incrementally. No full-plane RAM mirror is scanned every frame.
- **Camera/scroll model:** hardware scroll (HScroll buffer + VSRAM) shifts everything already
  resident; only the newly-exposed edge strip gets new name words. Handles **both axes** — column on
  horizontal motion, row on vertical — via the same edge mechanism. Plane wraps in VRAM.
- **VBlank publication (`VBlank_Levels`):** whole fixed-size buffers published unconditionally by
  DMA (palette via `writeCRAM`, HScroll + SAT via `writeVRAM`) — cheap because each is a known small
  size; then **bounded** in-window production (`LoadTilesAsYouMove`, `AnimateLevelGfx`, `HUD_Update`,
  `ProcessPLC` capped at **3** decompressed tiles) with an explicit **HBlank-deferral safety valve**
  if the frame is tight. `BuildSprites` (the SAT builder) runs in the **main loop**, not VInt.
- **Runtime cost:** near-zero when the camera is still; per boundary crossing, one strip of name
  words. No per-frame whole-plane scan.

## 5. Rainbow Islands — architectural findings (build/rainbow_islands_genesis.disasm.txt, 0x0380–0x041A)

- **Semantic ownership:** the main loop stages buffers and raises **explicit request flags**; the
  VBlank handler only honours them.
- **Publication model:** **flag-gated conditional** DMA — tiles (flag 0xF690), tilemap **strip**
  (0xF63C, value 1/2 selects which strip, ~40 words via jsr 0x1A70), palette (0xF680); display-off
  bracket gated on 0xF69A. SAT (0x6B0, link maintenance) and scroll (VSCROLL from shadow 0xF630 +
  HScroll) unconditional. Sound driver runs in-handler.
- **Plane representation:** strip-level staging + destination pointer, not a whole-plane rebuild.
- **Camera/scroll model:** **vertical-dominated.** Its tilemap commit is strip-based but the game's
  traversal doesn't exercise sustained horizontal column streaming the way Rastan must.
- **Runtime cost:** bounded by change (nothing runs if no flag set); publishes only the dirty strip.

---

## 6. Rastan arcade semantic ownership (Ghidra/disasm authority)

- **Scene seed:** `load_scene_tiles` (scene_load.s) — the arcade scene-entry decision; runs
  interrupt-masked + display-off, bulk-loads the scene's tiles once. Highest safe owner for "display
  this initial BG/FG scene."
- **Horizontal progression (new column entered):** the arcade PC080SN scroll-fill / strip producer
  family (~arcade 0x0559xx–0x055Exx), hooked natively (`genesistan_hook_tilemap_plane_a_selector12_native`
  @0x05595A/0x055990, `genesistan_hook_itempage_strip_blit` @0x055E5E). Critically the native
  producer is **already column-granular**: fg_tile_cache.s:115 — *"the selector-0 producer publishes
  one logical column at a time"* — and `fg_boundary_transition_step` receives the **logical column**
  in d0. The arcade **already knows which column entered**; the current Genesis layer flattens that
  into a row-dirty bitmap.
- **Vertical progression (new row entered):** entering row is a **contiguous** 64-cell nametable
  row — the row-dirty→row-DMA path is the *correct* seam for vertical motion.
- **Segment/epoch boundary:** `fg_boundary_advance_segment` (arcade 0x0558FE) — the record/segment
  advance that drives Layer-A residency/package transitions.
- **Frontend/title producers:** scene_load seed + the plane text hooks + the PC090OJ title
  score/label sprite lane (pc090oj_hooks.s `.Lnq_title_emit_*`). All confirmed rendering (§3a).

---

## 7. Comparison matrix — Sonic vs Rainbow vs Rastan (Plane A/B)

| Dimension | Sonic 1 | Rainbow Islands | Rastan now | Best reference for Rastan |
|---|---|---|---|---|
| Update trigger | camera edge crossing (semantic) | dirty/request flags (semantic) | generic 32-bit **row bitmap** | Sonic (edge event) |
| Both axes | **yes** (row + column) | vertical-dominated | rows only (wrong axis for H-scroll) | **Sonic** |
| Plane representation | compact block map, incremental | strip staging | full 64×32 name mirror ×2 | Sonic (incremental) |
| Publication unit | entering row/column strip | dirty strip (~40w) | whole 64-word rows ×N | Sonic / Rainbow |
| Conditional publish | edge-gated | flag-gated | palette unconditional; rows via mask | **Rainbow** (request flags) |
| Scene seed | level load | scene load | `load_scene_tiles` (arcade-owned) | **Rastan's own** boundary |
| Static-scene steady cost | ~0 | ~0 (nothing dirty) | ~0 (measured on title) | tie |

---

## 8. Recommended final Plane A/B architecture

**Split the answer by responsibility (do NOT force one reference):**

1. **Title / frontend fixed scenes → Rastan's own scene-seed boundary.** Seed once at
   `load_scene_tiles`; publish nothing unless a specific element (text/score/palette) changes.
   *Already achieved* (§3). No change needed.
2. **Horizontal gameplay scrolling → Sonic model.** Publish the **entering column** as a strided
   name write, driven by the arcade column event the producer already knows — not a row bitmap.
3. **Vertical gameplay scrolling → row seam (already correct in shape).** Entering row = one
   contiguous row DMA. Keep.
4. **Simultaneous X/Y → Sonic model** (publish the entering column *and* row for that frame).
5. **Scene/segment transitions → Rastan's `advance_segment`/residency boundary** (Layer-A package
   install), which already runs display-off + masked; publish the new resident set once.

**Publication-conditional structure → Rainbow model:** a small **semantic request** ("column C
entered", "row R entered", "palette changed", "strip S changed"), not a generic dirty scan.

## 9. Semantic cut

Preserve the arcade decision *"a new column/row of the level has entered the visible map"* (and the
scene-seed decision). Cut immediately below it, before PC080SN name-RAM/C-window write execution.

## 10. Complete PC080SN tail removed / proposed for removal

- **Already removed** (prior builds): tall-projector buffers + projectors (0256/0257),
  `staged_fg_tall_buffer`, C-window shadow, object-RAM mirror.
- **Proposed for removal (seam redesign, gameplay task):** the generic `bg_row_dirty`/`fg_row_dirty`
  **row-bitmap reconstruction** as the horizontal-scroll publication mechanism, and — under a full
  seam model — the need to stage and re-DMA whole 64-word rows to place one entering column.

## 11. Transitional compatibility remaining

- `staged_bg_buffer` / `staged_fg_buffer` (2×4KB) — the Genesis plane-name mirror. Legitimate (it is
  the plane's own size), consumed by the DMA. Under a full seam model it could shrink to bounded
  seam staging; **keep for now** (removal boundary = when the producer writes entering strips
  directly).
- `bg_row_dirty`/`fg_row_dirty` — transitional generic representation. Replace with the semantic
  column/row request. Removal boundary = seam producer landed and proven for all traversal.

## 12. Dirty-state audit

| Structure | Final-state requirement | Keep/Shrink/Replace/Delete | Reason |
|---|---|---|---|
| `staged_bg_buffer` (4KB) | plane-name source for DMA | **Keep** (Shrink under full seam) | it is the Genesis plane; not a virtual chip map |
| `staged_fg_buffer` (4KB) | same | **Keep** (Shrink under full seam) | same |
| `bg_row_dirty` / `fg_row_dirty` (8B) | none, if seam is event-driven | **Replace** | generic bitmap = wrong axis for H-scroll; producer already knows the column |
| `fg_narrow_desc_table` + count + pending (132B) | **the seam primitive** | **Keep / Extend** | already a bounded **column** descriptor path — exactly the seam mechanism |
| `staged_dest_ptr_bg/fg` (8B) | dest for strip DMA | **Keep** | small, needed |
| `staged_scroll_x/y_*` (8B) | hardware scroll publish | **Keep** | unconditional small publish (matches all 3 refs) |
| `staged_tile_words` (96B) | tile PIO staging | **Keep** | bounded |
| `staged_palette_words` (128B) | palette publish | **Keep**; gate with `palette_pending` | Rainbow flag model (already built) |
| tall/projector buffers | — | **Deleted already** | 0256/0257 |

**Key finding:** Rastan already owns a column-seam primitive (`fg_narrow_desc_table`). The seam
redesign is largely *route the horizontal-scroll entering column through the existing narrow-column
path*, driven by the arcade column event, and retire the row-bitmap for horizontal motion — not a
from-scratch renderer.

## 13. Buffer/state deletion opportunities

No *dead* state to delete now (tall/projector already gone; the row masks and plane buffers are
live). Deletions are gated behind the seam producer (§10, §12): row-bitmap → replace; plane mirrors →
shrink to seam staging.

## 14. Performance implications (estimates — not cycle-measured)

- Horizontal scroll today: up to **32×64 = 2048 words Plane B + 2048 words Plane A** re-DMA'd to
  place one column (whole-plane retransmit). Seam model: **~32 words** (one column of the visible
  height) — an ~order-of-magnitude reduction in plane DMA and in per-DMA setup count.
- Vertical scroll: already ~1 row (64 words) — near-optimal; unchanged.
- Static title: already ~0 plane words (measured) — unchanged.

## 15. Title-screen element ownership/status — see §3a. All correct.

## 16. Exact implementation performed

**None.** Justification (this is not a STOP-for-lack-of-info; it is "the clean target is already met
and the remaining work is invariant-blocked"):

1. The stated proof target — *make the display-off title render completely and correctly* — is
   **already satisfied** in Build 0348 (§3). There is no title defect to fix. Implementing anything
   here would be change-for-its-own-sake.
2. The genuine remaining work is the **horizontal-scroll seam** (gameplay, §8.2). It cannot ship as
   a numbered ROM this task because a numbered release requires **GATE_PASS**, and the canonical
   seven-epoch gate is the **known-invalid synthetic-injection gate** (proven last task) that
   rejects *any* publication-timing change — the same wall that blocks `palette_pending`. Replacing
   that gate is the explicit prerequisite step in the agreed progression and is its own task.
   Producing an unshippable seam renderer now would be exactly the experimentation-only /
   scaffolding production code the prompt forbids.
3. The seam also requires reverse-engineering the arcade PC080SN per-column write event to bind the
   entering column to the narrow-column publisher — a bounded RE sub-task, correctly sequenced after
   the gate fix.

## 17. Files changed

Report only: this file. No source/ROM changes.

## 18. Static verification

N/A (no build). Baseline 0348 unchanged; counter unchanged at 348.

## 19. Runtime verification by platform

- **GENESIS NTSC MAME:** title dirty-row / publication measurement (§3), Build 0348 display-off.
- **User (BlastEm, display-off):** title/story screenshots confirm complete title composition.
- No PAL `megadriv` evidence used.

## 20. Regressions checked

None introduced (no code change). Baseline 0348 intact.

## 21. Open/Closed Issues Impact

- **OPEN-001 (title/attract completeness):** the **title/attract-static** portion is measured
  complete in Build 0348 display-off (§3, §3a); the Build-0153 symptom list is stale. Recommend
  updating OPEN-001 with current evidence and narrowing it to any remaining *scrolling/item-page*
  and *gameplay* graphics rather than the static title. Not closed here (closure needs Tighe's
  visual acceptance + the scrolling portion).
- **OPEN-018 / native PC080SN plane rendering:** this report supplies the recommended final
  architecture and semantic cut; no code change.
- New issue: none opened (the seam work is already tracked by the OPT-003/publication progression).

## 22. KNOWN_FINDINGS impact

Option A (no new durable system finding requiring a KF). The durable facts (Sonic is the better
plane-scroll reference; Rastan already owns a column-seam primitive; title is complete) live in this
report. Any B/C promotion is for Tighe.

## 23. USER MUST VERIFY

No ROM produced. Please confirm from the existing 0348_do build that the **static title/story**
screens are visually complete (they appear so in your screenshots) so OPEN-001's title portion can
be updated/closed.

## 24. STOP status

**Analysis + report COMPLETE. No implementation this task, for cause:** the title target is already
met (nothing to fix), and the gameplay seam — the real Plane A/B work — is blocked by the
known-invalid canonical gate (numbered-release invariant) and is correctly sequenced after the gate
replacement. This is a compliant outcome, not an analysis-only dodge: there is no clean, shippable,
final-intent code to write in this task.

## 25. Native-replacement policy §9 checklist

- **Semantic boundary rather than chip-write-level?** Yes — the cut is "new column/row entered" /
  "scene seed", above PC080SN name-RAM execution.
- **Chip-specific tail named?** Yes — the row-bitmap reconstruction + whole-row retransmit for
  horizontal scroll (proposed removal); tall/projector/C-window/object-RAM already removed.
- **§6 boundary proof (arcade owner identified)?** Yes — §6 (scroll-fill column producer,
  `transition_step` logical column, `advance_segment`, `load_scene_tiles`).
- **Transitional compatibility isolated & scheduled?** Yes — plane mirrors + row masks, with removal
  boundaries (§10–§12).
- **No §8 structure as final architecture?** Compliant — no virtual PC080SN/C-window/object-RAM is
  proposed; the recommendation reduces representation, not adds it.

---

## Answers to the required questions

1. **Is Sonic 1 a better Plane A/B structural reference than Rainbow Islands?** **Yes — for the
   scrolling model.** (Rainbow remains the better reference for the *conditional/request-flag
   publication structure*.)
2. **Why?** Rastan traverses both horizontally and vertically; Sonic's edge-driven
   `LoadTilesAsYouMove` publishes the entering **column or row** on both axes, which is exactly
   Rastan's need. Rainbow's tilemap model is vertical-dominated and doesn't demonstrate sustained
   horizontal column streaming.
3. **Which Sonic concepts to adopt?** Edge/boundary-crossing as the publication trigger; publish
   only the entering strip (column on H, row on V); strided column write via VDP autoincrement;
   hardware scroll preserves resident content; a bounded per-frame publication budget.
4. **Which NOT to adopt?** Sonic's specific 256×256 block-map format and its object/PLC engine — do
   not import Sonic's data model; Rastan's arcade program remains the map/semantic authority. Keep
   Rastan's scene-seed and Layer-A residency boundaries.
5. **Final recommended semantic cut?** Preserve "a new column/row entered the visible map" (and the
   scene-seed decision); cut below it, before PC080SN name-RAM write execution; publish the entering
   strip via the existing narrow-column primitive.
6. **What buffers/dirty machinery can disappear?** The generic `bg_row_dirty`/`fg_row_dirty` row
   bitmap (replace with the semantic column/row request); the whole-row retransmit for horizontal
   scroll; and (under a full seam) shrink the 2×4KB plane mirrors to bounded seam staging. Tall/
   projector buffers already gone.
7. **Did you implement the architecture/title fix?** No — the title is already complete (nothing to
   fix), and the seam is gate-blocked/gameplay-scoped (§16, §24).
8. **Does the display-off version render the complete title screen?** **Yes — it already does** in
   Build 0348 (measured + your screenshots); it was not broken.
