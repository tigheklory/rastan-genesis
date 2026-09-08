# Andy — Build 0349: Plane A Vertical Source Unification (first step toward Sonic-style edge streaming)

**Task classification:** EXTENDING
**Build authorized:** YES · **Build produced:** 0349 (numbered + preserved) · **Production source changed:** YES (one hunk in `tilemap_hooks.s`)
**Platform:** GENESIS NTSC (`genesis`), USA/NTSC target.

---

## 0. Phase 0 — governance

- **Classification:** EXTENDING (extends the Plane-A native producer family; OPEN-001 / OPEN-018).
- **Relevant KNOWN_FINDINGS:** KF-010 (FG→Plane A), KF-015 (scroll model, `+8` bias), **KF-072
  (HIGH hazard: the Build 0226 ring/column-dirty rewrite was reverted; a ring/full-VSRAM/col-dirty
  layer must not be reintroduced piecemeal — every producer must convert together)**, KF-071,
  KF-074 (sprite ownership, unrelated). KF-072 is the governing constraint on the transfer-model
  change and is the reason for the sequencing in §7.
- **HIGH rediscovery hazards:** KF-072 ring rejection; the shift-table reflow pipeline
  (variable-length replacement is supported — no equal-length constraint); the synthetic
  seven-epoch gate / OPT-003 `0x034C` canary (previously classified a synthetic artifact).
- **Touched open issues:** OPEN-001, OPEN-018 (advanced, not closed).
- **Contradiction check:** none. This build does **not** reintroduce a ring model; it corrects a
  source-selection defect within the existing proven coordinate model, so KF-072 is preserved.
- **Independence reconciliation:** Andy and Cody independently root-caused the Build 0348 vertical
  corruption to the same missing term; this build implements the fix both recommended.

---

## 1. What Build 0349 changes (the fix)

**One hunk** in `.Lplane_a_publish_logical_row_native` ([tilemap_hooks.s:596+](../../apps/rastan-direct/src/tilemap_hooks.s#L596)),
the selector-0 vertical entering-row producer reached from the vertical pan hooks
`genesistan_plane_a_pan_publish_entering_rows_up/down`.

Before, the vertical source pointer was:

```
strip_src_table[row_segment] + source_group*4      (segment-0 relative)
```

After, it is the authoritative arcade formula from `map_select_pointers` (arcade PC `0x0502CC`,
`docs/arcade_reference/pc080sn/map_stream_control.c:51-61`):

```
strip_src_table[row_segment] + a5@0x013E*0x40 + source_group*4
```

Added instructions:

```asm
    moveq   #0, %d1
    move.w  0x013E(%a5), %d1          /* active map segment (arcade-owned) */
    lsl.l   #6, %d1                   /* * 0x40 */
    adda.l  %d1, %a0
```

This makes the vertical entering-row producer derive from the **same authoritative per-segment map
semantics** as the horizontal selector-0 producer (which reads the live rebuilt table at
`0x00FF1040`, itself `strip_src_table[i] + a5@0x013E*0x40`). It removes exactly the Build 0348
split the task named ("horizontal = live descriptor state, vertical = segment-0 table").

**Why this is correct, not a guess:** it is the literal arcade formula; Cody's independent raw-data
proof shows segment-0 vs active-segment descriptors differ for 62–179 of 256 entries in every
marked segment (e.g. seg1 base `0x1695C = 0x1691C + 0x40`); and it matches Tighe's observation
(vertical wrong at seg>0, worse deeper in the level, repaired by horizontal which already used the
live per-segment source).

**Not touched:** row/column orientation, physical-row destination (`logical_row & 31`), dirty-bit,
VBlank commit, horizontal publication, residency, collision, coordinate/ring model. No NOP, no RTS,
no scaffolding, no PC080SN shadow, no tall buffer.

---

## 2. Sonic 1 study (vendored `docs/reference/s1disasm`)

`LoadTilesAsYouMove` ([_inc/Level Drawing (REV00).asm:31](../../docs/reference/s1disasm/_inc/Level%20Drawing%20(REV00).asm)):

```
LoadTilesAsYouMove:
  test FG scroll-flags byte (v_fg_scroll_flags_dup)   ; bits 0/1/2/3 = top/bottom/left/right
  for each set bit: bclr it, then
     Calc_VRAM_Pos    ; world (x,y) -> ring-wrapped plane VRAM address
     DrawBlocks_LR    ; bit0/1: a horizontal ROW edge (row of blocks above/below screen)
     DrawBlocks_TB    ; bit2/3: a vertical COLUMN edge (column of blocks left/right of screen)
```

Call graph: `LoadTilesAsYouMove → {DrawBG_Top, DrawBG_Bottom} → Calc_VRAM_Pos, DrawBlocks_LR/TB`;
FG section → `Calc_VRAM_Pos`, `DrawBlocks_LR` (rows), `DrawBlocks_TB` (columns).

Dataflow: the scroll-position updater sets a **draw-flag bit** whenever the camera crosses a 16px
block boundary in a direction; `LoadTilesAsYouMove` consumes exactly the set edges and writes
**only** the newly-exposed row or column. `Calc_VRAM_Pos` produces the wrapped plane address;
`DrawBlocks_TB` writes a **vertical column** using VDP **autoincrement = plane row stride** so
consecutive data-port writes step down a column; `DrawBlocks_LR` writes a **horizontal row** with
autoincrement = 2 (contiguous).

### Reusable Genesis mechanics
Edge draw-flag model (per-direction bit set at crossing, consumed by the writer); world→ring VRAM
address (`Calc_VRAM_Pos`); the **vertical-column writer with autoinc = row stride**; the
horizontal-row writer with autoinc = 2; bounded edge iteration; VRAM wraparound.

### Sonic-specific — must NOT import
256×256 chunk model, 16×16 block hierarchy, `v_lvllayout_*` level format, Sonic camera ownership,
Sonic's VBlank scheduling/screen-update ownership, scroll-state ownership.

---

## 3. First engineering question — answered

Yes: Sonic's writer factors cleanly into a Genesis-generic boundary
`publish_plane_a_column(physical_column, name_words[32])` (autoinc = 0x80) and
`publish_plane_a_row(physical_row, name_words[64])` (autoinc = 2), where the caller supplies
already-Rastan-correct Genesis name words. The writer is semantics-agnostic — Rastan's arcade
descriptor resolver produces the words, Sonic's ring-address + strided-write mechanic transfers
them. That is the intended hybrid: **Rastan semantic source + Sonic-style Genesis edge publication.**

---

## 4. Current Build 0348/0349 paths (measured against the transfer model)

- **Horizontal** (`selector0/12_native`): computes one entering **column** (64 cells, correct
  `PTR[seg]`), writes one cell per resident row into `staged_fg_buffer`, and dirties **every**
  touched physical row → `fg_row_dirty = 0xFFFFFFFF`. VBlank then DMAs up to 32 × 64-word rows
  (≤2048 words) to publish what is semantically one 32-word column. This is **row-DMA coverage from
  a full-height column write**, not a plane rebuild (Q4).
- **Vertical** (`.Lplane_a_publish_logical_row_native`): computes one entering **row** (64 cells)
  and dirties one row → one 64-word DMA. Correct granularity already; Build 0349 fixes only its
  **source**.

The transfer inefficiency is therefore concentrated in the **horizontal** path: a 32-word column
change costs up to 2048 words of DMA because dirty granularity is whole-row.

---

## 5. Proposed Sonic-style transfer optimization (design; NOT in Build 0349)

Introduce a generic bounded edge job + writer, shared by both axes and reusable for Plane B:

```
edge job = { kind: ROW|COLUMN, phys_index, name_words[] }   staged outside VBlank
VBlank:  publish_plane_a_column → set VDP autoinc = 0x80, DMA/PIO 32 words to E000 + col*2 (ring-wrapped)
         publish_plane_a_row    → set VDP autoinc = 2,    DMA 64 words to E000 + row*0x80
```

- **Horizontal** target: emit one COLUMN job (32 words) instead of dirtying 32 rows → **~2048 → 32
  words** in the full-column case (measure actual resident height per KF-015 `+8` bias).
- **Vertical** target: emit ROW job(s) (64 words each) for each newly exposed row (already close).
- **Simultaneous X/Y:** one COLUMN job + one ROW job; the single shared corner cell is written by
  both — define ROW-wins (row job runs last) so the corner is deterministic; no plane redraw.

### KF-072 gate on this step
KF-072 (CONFIRMED) proves the Build 0226 ring/column-dirty rewrite failed **because producers were
converted piecemeal**. A column-job transfer model changes the publication representation for
Plane A. Therefore this step MUST convert the horizontal producer, the vertical producer, and the
VBlank commit **together**, and must be validated that the resident-row coordinate space is
unchanged (no ring/VSRAM change is required — the optimization is a *transfer-granularity* change,
not a coordinate change, which keeps it clear of the 0226 failure class). This is sequenced as
Build 0350+ **after** 0349's source fix is visually validated, so the two variables (source
correctness, transfer representation) are never entangled in one build.

---

## 6. VBlank / VDP considerations

- Column publication: Genesis VDP DMA honors the autoincrement register for the VRAM destination
  step, so a 32-word column DMA with autoinc = 0x80 is feasible; PIO with autoinc = 0x80 is the
  Sonic mechanism and is the fallback. Choice measured in Build 0350.
- Row publication: keep the existing 64-word contiguous DMA (`vdp_commit_fg_strips_if_dirty`,
  autoinc = 2).
- VBlank stays **publication authority only**; the resolver runs on the arcade mainline edge event
  and stages a bounded job. No map decoding moves into VBlank.

---

## 7. Build 0349 status vs. the synthetic seven-epoch gate

Build 0349 **passes** the canonical gate (`verify_canonical_rom.py`), the boot guard, and the
start-to-gameplay entry gate. It **fails only** the Phase-1 seven-epoch gate at
`target_record=3`, `full_plane_a_lut=FAIL, index=308 code=034C expected=0420 actual=0000`.

Analysis: the gate compares the runtime code→slot LUT against the generated package-5 mapping.
Build 0348 (buggy seg-0 vertical producer) passed this gate; Build 0349 (correct per-segment
producer) is the only change, so the fix deterministically changes which codes the vertical
producer resolves at the gate's synthetic record-3 state. Code `0x034C` is the **OPT-003 canary**
previously classified as a synthetic-gate artifact. The most likely reading is that the synthetic
record-3 driving relied on the old producer coincidentally resolving `0x034C`, and the correct
producer does not resolve it in that truncated synthetic window. **This is not proven to be benign**
— the deciding test is real-gameplay visual validation (below). Per Tighe's 2026-09-08 imperative
(now in RULES.md/CLAUDE.md), Build 0349 is **numbered and preserved regardless of the gate
failure** so Tighe can evaluate it; the gate result is recorded as evidence, not used to delete or
un-number the build.

**Tooling conflict raised:** the Makefile currently *deletes* the release ROM and does not advance
the counter when a gate fails. That behavior conflicts with the new imperative. Build 0349 was
therefore numbered/preserved by regenerating the postpatched release ROM (identical postpatch
inputs; boot guard PASS) and copying it to the numbered slot with a labeled ledger entry.

---

## 8. Acceptance instructions for Tighe

Play `dist/rastan-direct/rastan_direct_video_test_build_0349.bin` on GENESIS NTSC, Round 1 Phase 1,
and repeat the exact failure sequence:

```
vertical scroll → (was: Layer A wrong) → stop, stationary → (was: still wrong)
   → scroll right → vertical scroll again
```

Expected if the fix is correct: Layer A is correct during/after vertical scrolling at every map
segment, stationary Layer A stays correct, and no horizontal "repair" is needed. Watch for any
regression in horizontal scrolling, segment boundaries, rope/waterfall transitions, or collision.

Optional A/B: re-run the human trace harness on 0349
(`tools/mame/run_rastan_phase1_trace_wsl.sh dist/rastan-direct/rastan_direct_video_test_build_0349.bin`)
and compare Plane-A checksums during vertical scroll against the 0348 capture.

---

## 9. Open/Closed Issues; KNOWN_FINDINGS; legacy

- **OPEN-001 / OPEN-018:** advanced (vertical source now segment-correct); not closed.
- **KNOWN_FINDINGS:** propose a new finding after visual validation — *"Build 0349: Plane-A vertical
  entering-row source unified to the authoritative `strip_src_table[row_seg] + a5@0x013E*0x40 +
  group*4`; fixes the Build 0348 seg>0 vertical Layer-A corruption."* Not indexed yet (awaiting
  Tighe's runtime confirmation). KF-072 preserved.
- **Legacy retirement:** none yet. The Sonic-style column-job transfer (Build 0350+) is what will
  materially shrink the whole-row-DMA-from-column-write dependency; deferred behind KF-072 coherent
  conversion + 0349 validation.

## 9a. Build 0349 manual result (Tighe, 2026-09-08)

Tighe played Build 0349. Observed result:

> Layer A renders **differently — more wrong overall**. **Vertical** rendering is **more accurate**,
> but **horizontal** rendering is **partially wrong**.

Interpretation (recorded without altering the ROM — 0349 is a permanent diagnostic artifact):

- Adding the active map-segment term (`a5@0x013E*0x40`) **did** improve the vertical semantic
  source, as predicted — vertical is more accurate.
- But it did **not** make the Plane-A architecture coherent. The horizontal and vertical producers
  resolve the world through **different source tables** (horizontal via the live rebuilt descriptor
  table at `0x00FF1040`; vertical via the static `.Lplane_a_strip_src_table` + a manually-added
  segment term). Even with both now segment-aware, the two producers can disagree cell-for-cell, so
  where the vertical producer overwrites cells the horizontal producer had drawn, the horizontal
  result now looks partially wrong.
- **Conclusion:** the source finding is correct and must be kept; but simply inserting the term into
  the old vertical helper is insufficient. The fix belongs in a **replacement architecture with one
  shared semantic resolution** for both axes — which is the follow-on work (Build 0350+). Do not
  revert the 0349 source finding; do not keep patching the old renderer.

During 0349 testing Tighe also hit `machine freeze due to read from address D00462` (PC090OJ
hardware space `0xD00000-0xD00800`). This is a separate, previously-known PC090OJ-class failure,
not part of the Plane-A streaming work; tracked separately, not addressed here.

## 10. STOP status

Not a STOP. Build 0349 produced, numbered, preserved, and testable. Awaiting (a) Tighe's visual
validation of the source fix and (b) Tighe's decision on the Makefile auto-delete conflict and on
proceeding to the Build 0350+ Sonic-style transfer conversion.
