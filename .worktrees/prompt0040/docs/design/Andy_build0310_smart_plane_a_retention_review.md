# Andy — Build 0310 Smart Plane-A Retention Review

**Type:** compiler/VRAM residency analysis. No production change, no ROM, Build 0310 not consumed.
Baseline 0309 (`d7b7bd39…dbd02`). Scope: Level-1 **Phase-1 Plane-A** residency only. Plane B, scrolling,
collision, palettes, PC090OJ, Stage-2 unchanged.

## Verdict: **B — full union does NOT fit, but future-aware (Belady) retention removes most of the waste.**
Not Model A (won't fit), not the current per-record policy (52% of its uploads are pure reload waste).

## Decisive numbers (arcade data + canonical 32-byte decode, records 0–15)
- **Phase-1 A union = 1315** canonical identities (per-record 49…483; cross-record dedup already applied).
- **Interval-overlap peak = 720** at record 10 (max identities simultaneously "live" between first and
  last use under full retention).
- **A budget = 1535 − 854 (fixed B) − 196 (current 49-cell sprite) = 485 slots.**
- **Full union (1315) does NOT fit (485).** Even zero-reload retention (peak 720) does not fit (and not
  even with all sprite space reclaimed: 1535−854 = 681 < 720). So some streaming is unavoidable.
- **But per-record demand ≤ 483 ≤ 485 → zero drops are always feasible.** The question is reload count.

## The waste (why VRAM looks empty while A churns)
- **Current per-record policy: 3535 total A uploads for 1315 unique = 2220 redundant reuploads (63%).**
- **698 identities have a usage gap** (used in record i and j>i but not in between) — the current policy
  evicts them at i+1 and reloads them later, **even though 300–400 slots sit empty at light records**
  (record 5 = 89 A → 396 free; record 9 = 78 A → 407 free). That empty VRAM is exactly where the
  future-use patterns should have stayed. This is the compiler policy failing to use available VRAM.

## Belady-optimal future-aware retention (offline, deterministic — NOT a runtime cache)
Keep each identity resident from first to last use while capacity permits; when a record's own set needs
space, evict the resident identity whose **next use is furthest** (offline-known). Result:

| A budget (sprite policy) | total A uploads | vs current 3535 | records still needing DMA |
|---|---|---|---|
| 485 (keep 49-cell sprite) | **1690** | −1845 (−52%) | 15 (but many tiny) |
| 681 (reclaim sprite) | **1354** | −2181 (−62%) | 14 |
| 720 (= peak, hypothetical) | 1315 | −2220 (−63%, zero reloads) | 13 |

Per-record new uploads at budget 485: `[49,79,154,300,82,26,6,83,19,38,55,209,100,98,73,319]`.
**Wasteful reload transitions collapse** (record 6: 239→6, record 8: 132→19, record 5: 89→26), while
**genuine new-tile introductions remain** (record 3 = 300, record 11 = 209, record 15 = 319). Retention
converts ~half the DMA and most of the *reload* transitions into no-ops, using the empty VRAM.

## Brick bridge (Tighe's recollection, before castle)
The large **+319 new identities at record 15** (just before the Phase-2 castle at record 16) is the
strongest candidate for the bridge's distinct graphics. It **fits** (record-15 live = 349 ≤ 485) and is
**one transient addition**, not a reason to keep 15 per-record epochs. Its tiles, if unused afterward,
are ideal eviction candidates at castle entry. (Exact bridge column set needs the column decoder to
separate from ordinary record-15 terrain — a bounded follow-up; it does not change the verdict.)

## Slot stability
Under retention, a retained identity **keeps its physical slot** across records (no churn); only genuine
new uploads and forced evictions touch slots. This eliminates the current model's per-record repack of
the whole A band — cutting name-table remap and DMA at every boundary.

## Black frame
Retention does **not** eliminate every transition (Phase-1 A genuinely grows to 1315, so new tiles
appear at most records), but it (a) removes the wasteful reload transitions and (b) shrinks the
remaining per-record DMA (mostly <100 patterns; a few ~300). Small deltas can commit in VBlank; only the
few genuine large introductions (records 3, 11, 15) need Strategy-C prepare/commit later. **Do not build
a preload engine around the reload transitions that retention deletes.**

## Sprite lever
Current 49-cell (196-slot) reservation is capacity, not proven Phase-1 need (static families:
player 0x8A–0x9F, lizard-man 0x4B–0x6D, hurry-up bat — the coexisting peak is well under 49 cells).
Reclaiming it lifts the A budget 485→681 and cuts uploads 1690→1354. Bound it statically; validate with
the driven harness later. Do not block Build 0310 on the exact sprite peak — 485 already gives −52%.

## Phase 2 / Phase 3 (bounded)
Phase-2 A (records 16–20) and boss (21–22) add to the 1315→1855 full Level-1 A union. Retention should
**carry over** Phase-1 A identities reused in the castle and evict only outdoor-only tiles at castle
entry (future-use is offline-known). No assumption that castle entry discards all Phase-1 A. Exact
Phase-2 overlap is a bounded follow-up after Phase 1 lands.

## Verdict / Build-0310 recommendation
**B — future-aware sticky retention.** Build 0310 = replace the per-record load/discard with an **offline
Belady lifetime-retention schedule** over the A budget:
1. Compiler: compute each Phase-1 A identity's first/last/next-use (records 0–15); assign **stable slots**;
   at each boundary emit only the **new uploads** and the **minimal evictions** (furthest-next-use), never
   discard a future-use identity while free slots exist; **zero drops** (assert per-record set ⊆ budget).
2. Generated data: emit per-boundary **delta** (new (code,slot) + evicted slots) instead of full
   per-record packages — shrinks the 52,272-byte per-record A data substantially and removes duplicated
   re-upload metadata.
3. Runtime: at each boundary install **only the delta** (small DMA + LUT patch for changed slots); no
   full-band repack; retained slots untouched. No per-frame residency/LRU/eviction — the schedule is
   fully precomputed.
4. Optional (or 0311): reclaim the sprite band to budget 681; move the few remaining genuine-new
   transitions to VBlank prepare/commit (no-black).
Plane B, scrolling, collision, palettes, PC090OJ, Stage-2: unchanged.

---

## Physical Bit-Pattern Audit — Round 1 Phase 1 Plane A (2026-08-23)

Tighe challenged whether "1315 canonical identities" are real distinct graphics or compiler-created
duplicates. Answer computed by hashing the **decoded 32-byte 8×8 pattern bytes themselves**
(pc080sn tile ROM = the bytes the runtime DMAs), independent of the compiler's identity numbers.

### Result — the 1315 are genuinely unique bit patterns (verdict A, with a modest flip saving)
- Round-1 Phase-1 (records 0–15) Plane A: **1316 arcade tile codes → 1315 unique exact 32-byte patterns**.
  **Only 1** arcade code is a byte-identical duplicate (**1 dup group**). The compiler's canonical ID
  already *is* the exact 32-byte pattern, so **there is no meaningful exact-bit compiler duplication** —
  the "1315" is the true physical pattern count, not an inflated ID count. **Tighe's duplication
  hypothesis is REJECTED for exact bytes.**
- **Flip-normalized (H/V/HV): 1246** — H/V flips that Genesis name-table attributes can represent without
  a second VRAM pattern save **69** physical patterns (~5%). Record 11: 483 exact → **464** flip-norm
  (−19). Record 15 (bridge candidate): 349 exact → **349** (−0; bridge tiles have no flip partners, i.e.
  they are genuinely 349 distinct new graphics — the +319 is real, not duplication).
- Palette/priority: **not** part of the pattern identity (the compiler keys on the 32 pixel bytes only;
  palette/flip/priority are name-word attributes). So palette/priority create **no** physical duplicates.
- Plane-B quick check (unchanged): 854 arcade codes → **854 exact patterns** (0 exact dups; 844
  flip-normalized). B is duplicate-free; not touched.

### Capacity — the VRAM pressure is REAL, not artificial
A budget = 1535 − 854 (B) − 196 (sprite) = **485**.
- Exact A union **1315 ≫ 485** → does not fit.
- Flip-normalized A union **1246 ≫ 485** → still does not fit (flip saves only 69).
- So Round-1 Phase-1 Plane A genuinely needs streaming/retention; **compiler duplication is NOT the
  cause of the VRAM pressure.** The empty-VRAM problem Tighe saw is the *retention policy* (reload
  waste, quantified above), not fake pattern inflation.

### Belady retention recommendation — STANDS
The prior future-aware retention analysis used exact-byte identities, so it holds unchanged (Phase-1 A =
1315 real patterns; peak-overlap 720; current 3535 uploads / 2220 redundant; Belady 1690 @cap 485).
Flip-normalization is a **small independent optimization** (−69 physical patterns; −19 at the peak
record 11) that can be folded in later as a many-logical-code→one-physical-slot-with-flip-bits mapping —
it does not by itself make Phase-1 A fit and is not required for Build 0310.

### Artifacts
- `analysis/round1_phase1_plane_a/round1_phase1_plane_a_pattern_hashes.csv` (per-code: records, exact
  hash, flip-normalized hash, dup group).
- `analysis/round1_phase1_plane_a/round1_phase1_plane_a_duplicate_groups.csv` (the single exact dup
  group). A visual atlas is a deterministic byproduct of the same decode (one 8×8 per unique exact /
  flip-normalized hash) — generatable on request; the numeric result already settles the question.
