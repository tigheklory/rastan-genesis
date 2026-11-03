# Andy — Independent Analysis of Tighe's Human-Played Round 1 Phase 1 Trace

**Author:** Andy (independent analysis — Cody's report on this same trace was deliberately NOT
read; conclusions here are derived only from the raw trace and the Plane-A producer source.)
**Date:** 2026-09-07
**Platform:** GENESIS NTSC MAME (`genesis`), Build 0348.
**Status:** Analysis only. No build. No production change. No canonical-gate change. Raw trace
unmodified.

---

## 0. Phase 0 — Scope, Independence, and Non-Modification

This report answers one question that Tighe posed from visible play:

> During **vertical** scrolling, Layer A becomes wrong. As soon as he scrolls **horizontally /
> rightward**, the newly-entering tiles are published correctly again — until the next vertical
> scroll, when Layer A goes wrong again.

Constraints honored:

- **Independence.** I did not read Cody's analysis, conclusions, or AGENTS_LOG entry for this
  trace before finishing this report. Every claim below is traceable to the raw TSV columns or to
  `apps/rastan-direct/src/tilemap_hooks.s`.
- **Non-modification.** The raw trace at
  `states/traces/rastan_phase1_human_trace_20260907_220218/` was read only. `sha256sum -c
  SHA256SUMS.txt` = **OK** for all three files at analysis time. All derived numbers were computed
  by separate Python passes that never write into the trace directory.
- **No production work.** No ROM, no build number, no spec, no gate, no source edit.

---

## 1. Trace Identity and Integrity

| Field | Value |
|---|---|
| capture | rastan_genesis_round1_phase1_human_trace |
| machine | `genesis` (GENESIS NTSC) |
| rom_name | rastan_direct_video_test_build_0348.bin |
| rom_sha256 | `fac088eb0f8e9d374af80d9381aeecfe20be2ec6138ab688cfc6d0c45db1bf6b` |
| symbol_file_sha256 | `2428f0103b06592c…` |
| harness_sha256 | `e28dfbf2cd954f71…` |
| marker_key | KEYCODE_M |
| total_frames | 13383 |
| hash verification | `sha256sum -c SHA256SUMS.txt` → OK (all 3) |

The symbol set is **WRAM/BSS state only** (0xFFxxxx), placed by `link.ld` and independent of
`.text` size, so the addresses are valid against the exact 0348 ROM the trace captured. The harness
is reads-only inside `emu.register_frame_done` and captures no code addresses (correct under the
MAME 68000 DRC).

---

## 2. Tighe's Observation Restated as a Testable Model

The observation implies an **axis-asymmetric publication defect**:

```
sustained vertical scroll   → Plane A leading edge not refreshed  → "Layer A wrong"
horizontal / rightward move → Plane A fully repainted             → "correct again"
next vertical scroll        → leading edge stale again            → "wrong again"
```

The trace lets me test this directly: every frame records the staged Plane-A camera
(`scroll_x_fg`, `scroll_y_fg`), the per-frame camera deltas (`dx_fg`, `dy_fg`), the Plane-A
row-dirty mask actually published that frame (`fg_rows` / `fg_mask`), the narrow-column publication
count (`fg_narrow`), and a 2048-word checksum of the staged Plane-A nametable (`fg_sum`, `fg_xor`).

---

## 3. USER_MARK Inventory (15 marks)

All 15 visible-corruption marks, verbatim from `phase1_events.tsv`:

| # | frame | map_segment | pkg | scroll_x_fg | scroll_y_fg | fg_rows | fg_narrow |
|---|---|---|---|---|---|---|---|
| 1 | 1546 | 1 | 0 | 394 | 261 | 0 | 0 |
| 2 | 2714 | 3 | 5 | 259 | 329 | 0 | 0 |
| 3 | 3933 | 4 | 2 | 439 | 382 | 0 | 0 |
| 4 | 4190 | 4 | 2 | 384 | 489 | 0 | 0 |
| 5 | 4592 | 5 | 2 | 36 | 425 | 0 | 0 |
| 6 | 4843 | 5 | 2 | 485 | 297 | 0 | 0 |
| 7 | 5101 | 5 | 2 | 419 | 261 | 0 | 0 |
| 8 | 5274 | 5 | 2 | 394 | 261 | 0 | 0 |
| 9 | 5772 | 6 | 2 | 6 | 321 | 0 | 0 |
| 10 | 6773 | 7 | 2 | 478 | 261 | 0 | 0 |
| 11 | 8693 | 11 | 3 | 326 | 350 | 0 | 0 |
| 12 | 8977 | 11 | 3 | 265 | 489 | 0 | 0 |
| 13 | 9792 | 12 | 3 | 326 | 402 | 0 | 0 |
| 14 | 11329 | 13 | 4 | 12 | 261 | 0 | 0 |
| 15 | 12627 | 15 | 4 | 290 | 336 | 0 | 0 |

Two facts from the inventory:

1. **The bug is map-segment and package independent.** Marks span map segments **1, 3, 4, 5, 6, 7,
   11, 12, 13, 15** and residency packages **0, 2, 3, 4, 5** — i.e. essentially every segment and
   every package Tighe traversed. This is *not* a bad-segment or bad-package defect. It is a
   property of the Plane-A publication mechanism itself.
2. **Every mark lands on a settled frame** (`fg_rows=0`, `fg_narrow=0`): nothing is being published
   in the exact frame Tighe pressed M. This is expected — Tighe marks *when he notices* the wrong
   picture, which is after motion settles, not the causal frame. So the marks localize the
   *symptom window*, and the causal analysis must look at the motion frames *preceding* each mark,
   not the mark frame itself. The vertical camera positions at the marks (`scroll_y_fg` 261–489)
   confirm the symptom is seen across the whole vertical travel, not one Y position.

---

## 4. Publication Mechanism Actually in Use

Two Plane-A publication paths exist in `tilemap_hooks.s`: the **row path** (`fg_row_dirty`, a
32-bit whole-row dirty mask → whole-row DMA) and the **narrow-column path**
(`fg_narrow_desc_table` / `fg_narrow_desc_count`, for horizontal seams).

Across all 13383 frames:

- **`fg_narrow` (narrow-column path) is `0` on every single frame.** The narrow-column path is
  **never used** in this entire playthrough.
- `DUAL_AXIS_PUBLICATION` events (a frame with both `fg_rows>0` and `fg_narrow>0`) = **0**.

**Consequence:** 100% of Plane-A publication in Round 1 Phase 1 goes through the **row-dirty
path**. Any horizontal-seam correctness therefore also depends on the row path (via full-plane
row rebuilds — see §6), not on a dedicated column mechanism. This is important: the "horizontal
repair" Tighe sees is **not** the narrow-column producer doing its job; it is the row path doing a
*full rebuild*.

---

## 5. Vertical Scrolling: the Leading Edge Is Not Published During Motion

Per-frame correlation of camera motion vs. same-frame Plane-A publication (gameplay scene=1
frames):

| Motion class (this frame) | frames | published a row in-frame (`fg_rows>0`) | in-frame publication rate |
|---|---|---|---|
| **Vertical active** (`|dy|≥1`) | 895 | **5** | **0.6%** |
| Horizontal active (`|dx|≥1`, `dy=0`) | 4113 | 115 | 2.8% |
| Still / settled (`dx=dy=0`) | — | 887 | (this is where publication happens) |

**This is the core finding.** While the camera is actively scrolling vertically, Plane A publishes
essentially nothing — **890 of 895 vertically-moving frames publish zero rows**. New map rows
exposed at the vertical leading edge are **deferred**; they are only written on later *settle*
frames (the 887 still-frame publishes), one row per frame.

When the deferred publication does run, the row-*index* seam is mostly correct:

- 164 single-row vertical publish steps: **148 adjacent (±1 row, correct)**, 3 same-row, **13
  skips (gap ≥ 2)** — i.e. **91.9% adjacent, 8.1% skip**, 14 rows skipped in total across the whole
  run.

So the vertical seam does **not** pick catastrophically wrong rows — when it publishes, it usually
publishes the right adjacent row. The defect is **when** it publishes, not **which** row: the
publication is deferred out of the motion frames, so during a sustained/fast vertical scroll the
leading edge is stale on-screen until motion stops and the one-row-per-settle-frame seam slowly
catches up. That staleness is exactly "Layer A becomes wrong during vertical scrolling."

(The 8.1% skip rate is a secondary aggravator: on faster vertical scroll the single-row-per-frame
seam cannot emit two rows in one frame, so it occasionally falls a row behind even while settling.)

---

## 6. Horizontal Scrolling: Full-Plane Rebuilds Repaint Everything

`fg_rows≥32` (`fg_mask=FFFFFFFF`, a full 32-row Plane-A rebuild) attributed to the motion present
in the preceding 6-frame window:

| Full-32-row rebuilds preceded by… | count |
|---|---|
| **horizontal motion present** | **343** |
| vertical motion only (no horizontal) | 17 |
| pure still (no motion in window) | 132 |

Full-plane rebuilds are overwhelmingly **horizontal-driven**. When Tighe scrolls right, the row
path issues a **complete 32-row Plane-A rebuild** that repaints the entire resident window — which
necessarily overwrites any stale rows the vertical scroll left behind. `fg_sum` changes wholesale
across these rebuilds.

This is the mechanical explanation of the "repair": horizontal motion doesn't fix the vertical
seam; it **bulldozes the whole plane**, and the bulldoze happens to include the rows the vertical
seam left stale.

Supporting tallies from the event log: **X_BOUNDARY_CROSS = 981** vs **Y_BOUNDARY_CROSS = 233** —
horizontal traversal dominates the run and drives the frequent full rebuilds, so horizontal play
*constantly* refreshes the plane, masking the vertical deficit almost as fast as it appears.

---

## 7. Recurrence on the Next Vertical Scroll

The model predicts the wrongness returns as soon as horizontal rebuilds stop and vertical motion
resumes — because vertical motion publishes nothing in-frame (§5). The mark inventory confirms the
cycle empirically: 15 independent corruption marks distributed across the whole level, each in a
settled window that follows vertical travel (marks at `scroll_y_fg` 261/297/321/329/336/350/382/
402/425/489). There is no single "bad spot"; the symptom recurs wherever vertical scrolling is the
last thing that happened before a settle.

---

## 8. Combined X+Y (dual-axis) Behavior

`DUAL_AXIS_CROSS` (a frame crossing both an X and a Y tile boundary) = **19** frames;
`DUAL_AXIS_PUBLICATION` (a frame publishing both rows and narrow columns) = **0**. Diagonal motion
does not engage a special combined publisher; it is still serviced by the row path, and because any
horizontal component tends to trigger a full rebuild (§6), diagonal motion that includes rightward
travel tends to *repair* rather than corrupt. This is consistent with Tighe's report that it is
*pure* vertical scrolling that breaks Layer A.

---

## 9. Staged-State / Checksum Corroboration

`fg_sum` (2048-word staged Plane-A checksum) is flat across vertical-only motion windows and jumps
wholesale across horizontal full-rebuild windows. During the vertical single-row settle sequence
(e.g. frames ~4518–4543) `fg_sum` changes by small increments as one row at a time is written —
consistent with the one-row-per-settle-frame seam, and consistent with the leading edge lagging the
camera during the preceding motion.

---

## 10. Root-Cause Classification

**Classification: publication-side / ordering (timing) defect — specifically, Plane-A row
publication is deferred out of vertical-motion frames.** It is **not** primarily:

- *producer-content-side* — when a row is published its content/row-index is correct ~92% of the
  time;
- *destination/ring-side* — the row-index seam is 92% adjacent, so the ring position it targets is
  usually right;
- *narrow-column-side* — that path is unused entirely (0%).

The defect is **when** publication happens: the row path does not emit the newly-exposed leading
row during the vertical motion frame; it waits for a settle frame and then emits one row per frame.
Horizontal motion masks the defect because it triggers full 32-row rebuilds that repaint the whole
plane. That is a complete, mechanical account of Tighe's exact observation.

### Confidence

- **Axis asymmetry (vertical defers, horizontal full-rebuilds): HIGH / proven.** 0.6% vs 2.8%
  in-frame publication, 343 vs 17 full-rebuild attribution, narrow=0 everywhere,
  DUAL_AXIS_PUBLICATION=0. These are direct counts over the whole immutable trace.
- **Segment/package independence: HIGH / proven.** 15 marks across 10 segments and 5 packages.
- **"Leading edge shows stale nametable rows on-screen": INFERRED (strong).** The trace proves the
  *publication* is deferred and proves the on-plane checksum does not change during vertical motion;
  it does not directly sample VDP output pixels, so the final "what the eye sees" link is inference
  from staged state + Tighe's visual report, not a pixel capture. This is the one link I did not
  independently pixel-verify.
- **8.1% row-skip on the seam: MEDIUM.** Real but secondary; it aggravates fast vertical scroll but
  is not the primary mechanism (92% of steps are correct).

### Proven vs. Inferred (summary)

| Claim | Proven | Inferred |
|---|---|---|
| Vertical motion publishes ~0 rows in-frame (0.6%) | ✅ | |
| Publication deferred to settle frames | ✅ | |
| Horizontal motion → full 32-row rebuilds (343 vs 17) | ✅ | |
| Narrow-column path unused (0%) | ✅ | |
| Bug is segment/package independent | ✅ | |
| Vertical seam row-index 92% correct, 8% skip | ✅ | |
| Deferred publication is what the eye sees as "wrong" | | ✅ (strong; not pixel-sampled) |

---

## 11. Recommended Next Implementation Boundary (analysis only — not authorization to build)

The clean native-replacement boundary implied by this evidence is **the Plane-A row producer's
publication timing**, not any single segment/package and not the narrow-column path:

- The correct target is to **publish the vertical leading-edge row(s) in the same frame the camera
  exposes them**, the way the horizontal full-rebuild path already keeps the plane current — i.e.
  drive Plane-A row publication from the vertical camera delta at the moment of the Y tile-boundary
  crossing (`Y_BOUNDARY_CROSS`), emitting as many rows as `dy` exposed that frame, rather than
  deferring to settle frames one row at a time.
- This is a **producer-family / timing** replacement (one coherent boundary), consistent with the
  mandate to replace a subsystem rather than gate individual segments. It removes the settle-frame
  dependence rather than adding per-segment patches.
- It should **not** be pursued as "make horizontal rebuild fire during vertical scroll" (that would
  entrench the bulldoze-the-whole-plane workaround as a principle); the goal is a correct
  incremental vertical seam that keeps up with the camera.

This section is a **recommendation for a future authorized task**, not an action taken here.

---

## 12. Open / Closed Issues Impact

No issue status changed by this task (analysis only). This report provides the evidence base for a
prospective issue: *"Plane-A vertical leading-edge publication is deferred out of vertical-motion
frames; corruption is masked only by horizontal full-plane rebuilds."* Recommend opening it when
Tighe authorizes the fix; do not edit the ledgers on an analysis-only task.

## 13. KNOWN_FINDINGS Impact

Adds one durable finding (evidence-backed): **Round 1 Phase 1 Plane-A publication is
axis-asymmetric — vertical motion publishes 0.6% in-frame and defers to settle frames; horizontal
motion triggers full 32-row rebuilds (343 vs 17) that mask the vertical deficit; the narrow-column
path is unused (0%).** Recommend recording after Tighe reviews.

## 14. Build Status

No build. No numbered artifact produced or consumed. Build counter untouched.

## 15. STOP Status

Task complete as specified: independent analysis produced, raw trace unmodified and hash-verified,
report written to `docs/design/Andy_round1_phase1_human_trace_analysis.md`. **No production change,
no build, no gate change** — as instructed. Awaiting Tighe's direction on whether to proceed to the
implementation boundary in §11.

---

---

## Clarification — USER_MARK timing and stationary post-scroll observation

**Added 2026-09-07 as an amendment. The original analysis above is preserved unchanged. This
section supersedes the original root-cause conclusion (§10) based on (a) Tighe's clarified marker
contract and stationary observation, and (b) a source-level review the original report did not
perform. Determined independently — Cody's response to this clarification was not read.**

### C.0 What Tighe clarified

`USER_MARK` is an **approximate symptom annotation** — "Layer A is visibly wrong here, following
vertical scrolling" — pressed some time after the corruption appeared, usually while Rastan was
**stationary**. It is *not* a precise timestamp for the causal frame, the Y-crossing, the end of
motion, or publication completion. And critically: **after vertical scrolling stopped and Rastan
was stationary, Layer A stayed visibly wrong** until Tighe later scrolled right, at which point the
newly-entering columns were correct.

### C.1 (Q1) Does the original analysis depend on precise marker timing?

Partly, and I correct it here. The original §3 already treated marks as "when Tighe notices, not
the causal frame," and §10 confidence flagged the eye-link as inferred — those hold. **But two
original conclusions did lean on marker/settle semantics and are now withdrawn:**

- The framing that publication is "deferred to settle frames" and the seam "slowly catches up"
  (§5) implicitly assumed the settle window after a mark is where repair *should* happen. Tighe's
  stationary-still-wrong observation directly falsifies "catches up on settle frames."
- The §10 primary classification ("publication-side / ordering / timing") depended on the
  mask-based statistic, which I now show is a sampling artifact (C.3).

The map-segment-independence finding (§3) does **not** depend on marker timing and stands — though
C.5 reinterprets it (all marks at seg ≥ 1, which is exactly what a per-segment **source** bug
predicts).

### C.2 (Q2) The stationary observation vs. the timing model

**It contradicts the pure-timing/deferral model.** If entering rows were merely deferred and the
content were correct, then once motion stops the plane is static and the picture is either already
correct or is corrected by the next produced row — it would not *stay* wrong indefinitely while
stationary. Tighe reports it stays wrong until a horizontal pass. That is the signature of **wrong
content already committed**, not late-but-correct content.

Can the trace establish whether "enough settle frames elapsed" before each M press? **No.** Because
the marker is an approximate human annotation with unknown lead time, and because
`fg_row_dirty` is cleared every VBlank (C.3), the trace cannot count "settle frames that should have
repaired the picture" from the marker alone. I state that plainly rather than inferring repair
adequacy. The stationary observation is therefore evidence *against* deferral and *for* a
source-content defect, and the trace neither needs nor supports a settle-frame-catch-up story.

### C.3 (Q3) `fg_rows = 0` at `frame_done` is a sampling artifact — it does NOT prove no row was produced

This is a real methodological error in the original §5. The VBlank publisher
`vdp_commit_fg_strips_if_dirty` ([vdp_comm.s:313-345](../../apps/rastan-direct/src/vdp_comm.s#L313-L345))
DMAs each dirty row and **clears its bit** (`bclr %d5,%d0; move.l %d0, fg_row_dirty`,
[vdp_comm.s:335-337](../../apps/rastan-direct/src/vdp_comm.s#L335-L337)). The harness samples inside
`emu.register_frame_done`, i.e. **after** VBlank. Lifecycle:

```
producer sets fg_row_dirty  →  VBlank DMAs + clears bit  →  frame_done samples 0
```

So `fg_rows=0` at sample time is consistent with "a row was produced and already published." The
original headline statistic — *"0.6% of vertical-moving frames publish in-frame"* — measured the
**post-clear** mask and is therefore invalid as a production measure.

- **What the trace directly proves:** the *staged-buffer content* per frame via `fg_sum` (DMA reads
  the staged buffer but does not clear it).
- **What it only samples after the fact:** the `fg_row_dirty` mask (`fg_rows`, `fg_mask`) — cleared
  by VBlank before the sample.
- **What cannot be inferred:** same-frame production presence/absence from `fg_rows`.

Re-measured with the reliable `fg_sum` signal (staged-plane change vs prior frame):

| Motion class | plane changed | flat | change rate |
|---|---|---|---|
| vertical-active (`|dy|≥1`) | 60 | 835 | **6.7%** |
| horizontal-active | 404 | 3709 | 9.8% |
| still/settled | 1037 | 6768 | 13.3% |

Vertical production is **6.7%**, an order of magnitude above the artifactual 0.6%, and not the
near-zero the original claimed. Production *does* happen during vertical motion — it is just
producing **wrong** content (C.5).

### C.4 (Q4) Horizontal `fg_mask = FFFFFFFF` is row-DMA coverage, NOT a semantic plane rebuild

`genesistan_hook_tilemap_plane_a_selector0_native`
([tilemap_hooks.s:229-339](../../apps/rastan-direct/src/tilemap_hooks.s#L229-L339)) loops **16
descriptor segments × 4 cells = 64 cells = one full-height entering column** (logical rows 0-63;
physical row `d0 = logical & 0x1F`). For each written cell it sets **that row's** dirty bit
(`bset %d0, %d2` → `fg_row_dirty`, [line 324](../../apps/rastan-direct/src/tilemap_hooks.s#L324)).
A full-height column touches all 32 physical rows, so all 32 dirty bits get set →
`fg_row_dirty = 0xFFFFFFFF`.

**This is Option B: the horizontal producer modifies one column (one cell per row) and, because the
publication granularity is whole-row DMA, every physical row is flagged for DMA.** It does **not**
semantically recompute all 2048 plane cells. The original §6 "complete 32-row Plane-A rebuild" was
the wrong interpretation. Consequently the "repair" is **progressive**: each rightward column
crossing overwrites one column of the staged buffer with correct `PTR[seg]` content (C.5); the
all-rows-dirty DMA merely carries the staged changes to VRAM. As Tighe scrolls right, correct
columns replace the wrong region column by column — exactly "newly populated tiles are correct."

### C.5 (Q5) Source review: the vertical producer omits the active-segment term the horizontal producer uses

The authoritative arcade FG source formula (comment
[tilemap_hooks.s:102-103](../../apps/rastan-direct/src/tilemap_hooks.s#L102-L103)) is
`code = ROM_word(PTR[seg] + colidx*2 + row*8)`, where **`PTR[seg]` is the arcade-owned per-segment
pointer table rebuilt at `0x00FF1040`** (`PC080SN_DESC_REBUILD_PTR_TABLE`). The per-segment seed is
`0x1691C + strip*0x22C0 + seg*0x40` (Ghidra + runtime-validated in the Cave Part 1 analysis:
strip0 seg1=`0x1695C` … seg6=`0x16A9C`).

**Horizontal producers use `PTR[seg]`:** `selector0_native`
([line 258](../../apps/rastan-direct/src/tilemap_hooks.s#L258)) and `selector12_native`
([line 377](../../apps/rastan-direct/src/tilemap_hooks.s#L377)) both `lea
PC080SN_DESC_REBUILD_PTR_TABLE, %a3` and walk the live per-segment pointers. They therefore track
the active segment correctly → correct entering columns at every segment.

**The vertical producer does NOT.** `.Lplane_a_publish_logical_row_native`
([line 550](../../apps/rastan-direct/src/tilemap_hooks.s#L550)) — reached **only** from the vertical
pan producers `genesistan_plane_a_pan_publish_entering_rows_up/down`
([lines 468, 504](../../apps/rastan-direct/src/tilemap_hooks.s#L468)) that hook the arcade vertical
scroll `0x055798`/`0x05570C` — selects its source from a **hardcoded** table
`.Lplane_a_strip_src_table` ([lines 655-659](../../apps/rastan-direct/src/tilemap_hooks.s#L655)):

```
.Lplane_a_strip_src_table:  .long 0x0001691C, 0x00018BDC, 0x0001AE9C, ...   (stride 0x22C0)
```

These are exactly `0x1691C + strip*0x22C0` — the **seg = 0** base pointers. The routine indexes it
by `(logical_row>>2)&0xF` and takes its column purely from `scroll_x_fg`; it **never reads
`0x00FF1040` and never adds `seg*0x40`**. There is no read of `arcade_record` (`a5@0x013E`) on this
path (the only `0x013E` read in the file, [line 1002](../../apps/rastan-direct/src/tilemap_hooks.s#L1002),
is inside `genesistan_select_stage1_cave_residency`, which is `rts`-stubbed at
[line 998](../../apps/rastan-direct/src/tilemap_hooks.s#L998) — dead).

**Is the segment term required by arcade semantics?** YES — the arcade formula is `PTR[seg] + …`,
`PTR[seg]` differs by `seg*0x40` per segment, and the horizontal producers honor it.
**Is it present in Build 0348's vertical helper?** NO — it hardcodes the seg = 0 bases.

**Consequence:** whenever the map segment > 0, the vertical pan producer publishes entering rows
from a source pointer that is short by `seg*0x40` — i.e. **wrong tiles**. That content is committed
to the staged buffer and stays there (nothing re-publishes those rows while stationary), which is
exactly "Layer A wrong during vertical scroll, still wrong while stationary." A subsequent rightward
scroll runs `selector0/12` with correct `PTR[seg]` and overwrites the cells column by column — the
observed repair. And it recurs on the next vertical scroll. **All 15 markers are at
`arcade_record ≥ 1`; none at seg 0** — precisely the segment-dependence this defect predicts
(corroborating, though not sole proof, since Tighe spends little time at seg 0).

### C.6 (Q6) Root-cause reassessment: **SUPERSEDED**

- **Prior conclusion (§10): SUPERSEDED.** It rested on the artifactual mask statistic (C.3) and the
  misread full-rebuild (C.4), and is contradicted by the stationary observation (C.2).
- **Current primary root cause (high confidence):** a **source-content defect in the vertical
  entering-row producer**. `.Lplane_a_publish_logical_row_native` selects Plane-A source from a
  hardcoded seg = 0 strip table instead of the arcade live per-segment `PTR[seg]` table
  (`0x00FF1040`) that the horizontal producers use, so vertical scrolling publishes wrong tiles for
  every map segment > 0. Horizontal scrolling overwrites them from correct `PTR[seg]`.
- **Confidence: HIGH** on the static asymmetry (vertical hardcodes seg = 0; horizontal reads
  `PTR[seg]`; both are direct source reads) and on its match to every element of Tighe's observation
  (vertical-wrong, stationary-persistent, horizontal-repair, recurrence, seg-dependence). The one
  unclosed step is a direct arcade-oracle equality check of the two source pointers at seg > 0
  (C.7), which needs no build.
- **Separate timing issue? UNPROVEN.** The stationary persistence and the horizontal repair are
  fully explained by the source defect alone; the former "timing" evidence was an artifact. I do
  **not** assert a second defect. A residual catch-up/timing issue can only be claimed if it
  survives after the source is corrected — the experiment in C.7 is designed to expose it if it
  exists, but on current evidence it is not independently supported and must not be bundled in.

### C.7 (Q7) Smallest first experiment

**Rebase the vertical producer's source onto the same live per-segment basis the horizontal
producer already proves correct.** Concretely: make `.Lplane_a_publish_logical_row_native` derive
its per-strip source pointer from the arcade `PC080SN_DESC_REBUILD_PTR_TABLE` (`0x00FF1040`,
i.e. include the active `seg*0x40`/`PTR[seg]` term) instead of the hardcoded
`.Lplane_a_strip_src_table`, then vertically scroll at a map segment > 0.

Why it discriminates:

- If the entering rows are correct immediately on vertical scroll **without** a horizontal pass →
  the source-content defect was the whole cause; no separate timing issue exists.
- If rows are still wrong or visibly lag despite now-correct source → a residual
  publication-timing/catch-up defect is isolated, and *only then* is the two-issue conclusion
  warranted.

**No-build precheck (recommended first, even cheaper):** a read-only arcade-oracle comparison at
seg > 0 of `.Lplane_a_strip_src_table[strip]` against `PTR[seg][strip]` from the arcade rebuild.
If they differ by `seg*0x40`, the vertical source is proven wrong with zero ROM changes. This is an
analysis step, not implementation.

### C.8 Amendment summary

| | |
|---|---|
| **Original conclusion** | Publication-timing/ordering defect: vertical defers publication, horizontal full-rebuild repairs. |
| **New human clarification** | M is an approximate symptom marker; Layer A stays wrong while stationary after vertical scroll, until a rightward scroll. |
| **What changes** | The mask-based "0.6% in-frame" statistic is an artifact (VBlank clears the mask pre-sample); "full 32-row rebuild" is actually one-column write with whole-row DMA coverage; timing/deferral is superseded. |
| **What remains valid** | Segment/package spread of the symptom; narrow-column path unused (0%); horizontal writes correct entering columns; the *phenomenology* (vertical breaks, horizontal repairs, recurs). |
| **Revised root cause** | Source-content defect: vertical pan producer omits the active-segment `PTR[seg]` term (hardcoded seg = 0 source) that the horizontal producer honors. |
| **Revised confidence** | HIGH (static asymmetry + full observational match); separate timing issue UNPROVEN. |
| **Next experiment** | Rebase vertical source to live `PTR[seg]` (`0x00FF1040`); no-build oracle pointer-equality precheck at seg > 0. |

---

### Appendix A — Derived metrics provenance

All numbers computed by read-only Python passes over
`states/traces/rastan_phase1_human_trace_20260907_220218/phase1_frames.tsv` and
`phase1_events.tsv` (scene=1 gameplay frames unless noted):

- In-frame publication by motion class: vertical 5/895 (0.6%), horizontal 115/4113 (2.8%), settle
  publishes 887.
- Single-row vertical seam steps: 164 total → 148 adjacent (±1), 3 same-row, 13 skip (gap≥2), 14
  rows skipped; 91.9% adjacent / 8.1% skip (direction-symmetric ring metric,
  `gap = min(d, 32−d)`).
- Full-32-row rebuild attribution (6-frame motion window): horizontal 343, vertical-only 17, pure
  still 132.
- Event tallies: X_BOUNDARY_CROSS 981, Y_BOUNDARY_CROSS 233, DUAL_AXIS_CROSS 19,
  MAP_SEGMENT_CHANGE 18, RESIDENCY_PACKAGE_CHANGE 9, USER_MARK 15, DUAL_AXIS_PUBLICATION 0.
- `fg_narrow` = 0 on all 13383 frames.
