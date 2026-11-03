# Build 0414 — Scroll + Enemy Performance Review (Andy)

**Date:** 2026-10-10 · **Type:** REVIEW / ANALYSIS ONLY. No production source edited, no ROM, no
build number consumed, Cody's working tree untouched. Real Sega Genesis hardware is the performance
authority; BlastEm is diagnostic only.

Baseline: committed Build 0414 (`1032731`). Measured (Cody): quiet/static IRQ median 72,593; one
enemy/static 87,443 (+14,850); scroll-only heavy ~230,000 with ~153,890 inside the native row/map
path (≈98.1% of the `0x556CE` call). Frame budget 128,009 cyc.

---

## 1. Effective-bank hoist review — **SAFE WITH CONDITIONS**

**Hoisted value:** `((pc090oj_sprite_ctrl_shadow & 0x00E0) >> 1)` — the normalized effective-bank
high bits. Formerly recomputed (`move.w shadow; andi #0xE0; lsr #1`) in each active actor probe and
in emitted-piece palette/variant decisions. Now computed once per pass and cached in the **high byte
of a repurposed packed `native_sprite_lane` word** (high byte = bank, low byte = semantic lane).

**Source owner/writer:** `pc090oj_sprite_ctrl_shadow` is written only by
`genesistan_pc090oj_sprite_ctrl_write_d0` / `_clear` (arcade-side call-site replacement hooks) — none
inside the native stage walk.

**Refresh lifetime / boundaries:** re-hoisted at the entry of each pass that uses it —
`native_stage_dispatch_41dae` (:708), `native_stage_dispatch_45dfa` (:844), and
`pc090oj_native_emit_pass` (:2076). Each pass reads a fresh shadow at entry and uses it only within
that straight-line pass. ✅

**Possible mid-lifetime writer:** none. The walk runs inside IRQ6 at IPL7 (no async preemption), and
no native pass calls back into the sprite-ctrl writer between hoist and use. The arcade sets the
sprite colour bank once per frame before sprite processing, so the shadow is stable across each pass.

**Consumers (all verified to read the correct byte):**
- lane selection: `native_sprite_emit` (:567) and `native_sprite_fast_context` (:634) read
  `native_sprite_lane+1` (LOW byte = lane) — the packing does **not** break lane dispatch; no
  full-word `cmpi.w #NATIVE_LANE_*` remains.
- bank: generic probe (:997 `move.b native_sprite_lane,%d0 /* dispatch-cached exact high bits */`)
  and the variant/residency emit paths (:2706, :2944 `move.b native_sprite_lane,%d7`) read the HIGH
  byte = cached bank.

**Palette/variant semantics preserved:** YES — the cached value is bit-identical to the former
recompute, and it feeds the same `pc090oj_variant_bank_slot[effective_bank]` selection.

**116–372 cyc (median ~232) plausibility:** YES. Removed work ≈ `move.w mem + andi + lsr` (~26–28
cyc incl. the memory read) per probe and per emitted piece. ~8–13 occurrences eliminated per worker
(scaling with emitted pieces) → 116–372 cyc, median ~232. Structurally consistent with "depends on
emitted load."

**Conditions:** (1) the hoist's correctness depends on `pc090oj_sprite_ctrl_shadow` being stable
across each pass — true under current single-write-per-frame arcade ordering + IPL7; if a future
change let an arcade sprite-ctrl write interleave *within* a dispatch/finalize pass (e.g. per-actor
colour-bank changes), the cache would be stale. (2) The `native_sprite_lane` word is now overloaded
{bank:lane}; any new consumer must read the correct byte (never `move.w` the full word for a lane
compare). Recommend the direct-dispatch verifier assert no `move.w native_sprite_lane` full-word
read and that all three dispatch/finalize entries re-hoist.

---

## 2. Scroll / Layer A-B structural analysis (PRIMARY)

### 2.1 Chain and routine identity
`0x51210 → 0x055650 → directional (0x055696/72E/7BA/854) → 0x0556CE → 0x055948 → 0x0559C8/0x055990 →`
native Plane-A strip rebuild. The runtime row/map path (`0x70418/0x70552`) is
`genesistan_hook_tilemap_plane_a_selector12_native` (hooked at arcade `0x055990`; horizontal column
producer) and its per-cell publishers, plus the vertical pan routines.

### 2.2 Vertical vs horizontal — vertical is already incremental
`genesistan_plane_a_pan_publish_entering_rows_up/down` (tilemap_hooks.s:508/544) loop **only over
entering rows** (`cmp old_visible_top,new_visible_top`), publishing one Plane-A + one Plane-B row per
tile crossed. Vertical scroll is already an incremental ring update and is **not** the bottleneck.

### 2.3 The horizontal producer rebuilds the full width (the structural problem)
`genesistan_hook_tilemap_plane_a_selector12_native` (:382): outer `.Lplane_a_sel12_segment_loop`
**d4 = 0..15 (16 segments)** × inner `.Lplane_a_sel12_cell_loop` **d5 = 0..3 (4 cells)** = **64
logical columns rebuilt per invocation.** A single one-tile horizontal camera crossing exposes only
**one new 4-column segment**; the other ~60 columns are recomputed identically and re-staged. This is
the Class-A over-work.

### 2.4 Each cell is resolved TWICE (duplicate work)
Per cell the loop calls **`resolve_plane_a_collision_cell`** (:449, for the collision-map
side-channel at `ARCADE_COLLISION_MAP_BASE`) **and then `resolve_plane_a_cell`** (:464, "shared
authoritative resolver (name word only)"). Both walk the PC080SN descriptor-rebuild tables
(`PC080SN_DESC_REBUILD_SRC/PTR/WORD`), do strip-group/index arithmetic, descriptor range checks, a
second-word-base dereference, and uniform/non-uniform tile classification. The collision resolver
(:729) alone saves `d1-d7/a0-a2` and runs ~40+ instructions. So the heavy per-cell cost is **two full
descriptor resolves** + attr pack (`.Lplane_a_native_attr_from_word`) + residency-window test +
staged write + `fg_row_dirty` bset. (`genesistan_pc080sn_tile_vram_lut` is already a precomputed
tile→VRAM LUT — Class B is partly done — but the descriptor walk + double resolve + attr pack remain
at runtime.)

### 2.5 Data-volume estimate (one representative horizontal strip event)
- Source cells examined/translated: ~64 columns × (1 logical row for selector-1/2) per Plane-A
  invocation; the directional/strip path and Plane-B publisher add the paired plane. Plane-B
  (`.Lplane_b_row_col_loop`, :920) adds a full-width per-cell loop with its own blank/tile
  classification.
- Layer A cells **actually changed** by a one-tile crossing: ~1 segment (4 columns) × the resident
  rows; **examined/recomputed: all 64 columns.**
- Layer B: similar full-width per-cell loop.
- Each examined cell: **2 descriptor resolves** + collision-map write + name-word build + residency
  test + staged write. Duplicate/redundant: (a) ~60/64 columns recomputed but unchanged (Class A);
  (b) every cell resolved twice (Class G); (c) descriptor-walk arithmetic that is invariant per map
  position (Class B/C).

### 2.6 Why ~153,890 cycles
Not "tilemap work" — it is **full-width (64-column) re-resolution of both planes, with every cell run
through two independent descriptor resolvers, per scroll event**, when only a 4-column strip actually
changed. Order-of-magnitude: ~64 cells × 2 planes × (~2 resolves + pack + writes ≈ ~500–600 cyc) ≈
130–150K, consistent with the measurement. The cost is **CPU-side preparation** (descriptor
resolution + packing + staging), not VDP DMA transfer (the staged `fg_row_dirty`/buffer is published
later by the central publisher).

### Scroll optimization candidates (ranked by heavy-scroll recovery ÷ risk)

**#1 — Class A: incremental column-strip update (biggest structural lever).**
Routine: `genesistan_hook_tilemap_plane_a_selector12_native` (+ the Plane-B publisher). Current:
rebuilds all 16 segments × 4 cells (64 cols) per horizontal strip event. Proposed: rebuild only the
newly-exposed segment(s) (the entering 4-column strip), mirroring the already-incremental vertical
pan routine, preserving Genesis plane wrapping and the resident-window test. **Caveat to confirm:**
the collision-map side-channel (`resolve_plane_a_collision_cell` → `ARCADE_COLLISION_MAP_BASE`) may
require a wider span than the display strip; determine whether collision needs the full row or only
the entering columns before narrowing it. Estimated recovery: up to ~**90–110K** (≈15/16 of the
column work if collision allows strip-only). Python: NO. ROM: negligible. RAM: none. DMA: unchanged.
Risk: **MEDIUM** (wrapping + collision-span correctness). Enough alone to cross one frame:
**PLAUSIBLE** (it is the dominant term).

**#2 — Class G: fuse the double per-cell resolve.** Each cell runs `resolve_plane_a_collision_cell`
and `resolve_plane_a_cell` over the same descriptor state. Fuse into one resolver that yields both the
collision word and the Genesis name word. Estimated recovery: ~**20–40K** (roughly the second
resolve's share of per-cell cost). Python: NO. DMA: unchanged. Risk: **LOW–MEDIUM** (must keep the
collision word bit-identical). Compounds with #1 (fewer cells × cheaper cell).

**#3 — Class B/C: precompiled map-cell → {name word, collision word} table.** Python precomputes, per
arcade map cell, the invariant finalized Genesis name-table word (VRAM slot + palette + priority +
flip, via the existing `precompute_pc080sn_tile_lut.py` pipeline) and the collision word; runtime
does a direct indexed lookup instead of the descriptor walk + resolve + attr pack, applying only
genuinely dynamic tile overrides (e.g. the destroyable cave block) as exceptions. Estimated recovery:
~**30–60K** of the remaining resolve/pack cost. Python: **YES**. ROM: moderate (per-context map-word
table). RAM: small override set. DMA: unchanged. Risk: **MEDIUM** (dynamic-tile override coverage;
per-context scoping). This is the "express the map semantics directly" architecture, not a software
PC080SN.

**Can scrolling fit one real frame?** Required recovery from the ~230K event = **~102K** (to reach
128,009). #1 alone (~90–110K) is borderline-sufficient; **#1+#2 (~110–150K)** or **#1+#2+#3** take the
row/map path from ~153,890 to ~40–55K, total scroll IRQ ~116–126K < 128,009. **Verdict: PLAUSIBLE**,
and it is correctly a *structural* reduction (≈66% of the row/map path), not a micro-optimization.

---

## 3. Enemy scaling (SECONDARY)

First-enemy increment ~14,850 cyc (~10 emitted pieces). Per-actor cost components: retained
gameplay/AI (arcade, out of scope), native actor probe (`.Lnative_emit_actor_common` → generic then
universal), frame selection, per-piece queue generation (`native_sprite_emit_fast`), finalizer,
residency reverse-lookup, SAT, DMA. The effective-bank hoist already removed one per-actor/per-piece
cost.

**Enemy #1 — cache per-(family,anim) owning probe to avoid the double probe.** The wrapper calls
`.Lnative_generic_frame_try`; on a miss it calls `.Lnative_universal_general_try`. An enemy that is
owned by the universal path pays the full generic classification (base-LUT + usage-descriptor
validation + bank + selector normalization) as wasted work first. Record, per resolved
(family,anim), which probe owns it and dispatch straight to it. Estimated: ~**100–300 cyc/actor**.
Risk: LOW–MEDIUM. Generality: HIGH.

**Enemy #2 — hoist per-actor-invariant variant base out of the per-piece path.** Per emitted piece
the emit path resolves `(code,bank)→vi` via `group_base[code] + bank_slot[bank]`; the bank is now
cached, but the variant group base for the actor's code range is recomputable once per actor rather
than per piece where the actor's pieces share a code group. Estimated: scales with pieces (~tens of
cyc × pieces/actor). Risk: MEDIUM (must preserve divergent-variant correctness). Generality: MEDIUM.

Expected real-hardware effect: each saved ~few-hundred cyc/enemy widens the static-camera margin by
roughly one extra enemy; secondary to scroll.

---

## 4. Hammer/flail BlastEm discrepancy (DIAGNOSTIC ONLY)

**Hammer/flail Layer A/B interaction: NO.** Weapons are PC090OJ player-composite sprites
(`native_player_*` / weapon overlay), not Layer A/B tilemap. Therefore the hammer discrepancy is
**unrelated to the scrolling plane bottleneck.** The swing most likely emits more / longer-lived
sprite pieces (and possibly a weapon-effect actor) than the sword, raising the sprite/finalizer/DMA
cost of those frames. Real Genesis is clean; BlastEm shows a bar most likely due to a stricter
VDP/DMA-slot or beam-timing model (or diagnostic display-timing) flagging an overrun the real
console's tolerance absorbs. **Production optimization warranted: NO.** Do not optimize to make
BlastEm clean.

---

## 5. Hardware threshold model

Base quiet ~72,593; first-enemy increment ~14,850 (includes some fixed finalize/DMA, so later
enemies likely cost somewhat less — do not treat as strictly linear). Budget 128,009.

| State | Est IRQ | Margin | Real-HW |
|---|---|---|---|
| quiet/static | 72,593 | +55,416 | PASS |
| 1 enemy | 87,443 | +40,566 | PASS |
| 2 enemies | ~102,293 | +25,716 | PASS |
| 3 enemies | ~117,143 | +10,866 | PASS (tight) |
| 4 enemies | ~131,993 | −3,984 | first overrun |
| scroll-only | ~230,000 | −101,991 | OVERRUN |

Quiet margin / per-enemy ≈ 55,416/14,850 ≈ **3.7 enemies** before overrun → matches Tighe's "more
than 3 enemies before the black bar begins." **Model agrees with hardware observations.** Required
scroll reduction ≈ **102K** → a structural cut of the ~153,890 row/map path (≈66%).

---

## 6. Recommended next implementation order

**#1 — Scroll / Layer A-B incremental column-strip rebuild (Class A), then fuse the double resolve
(Class G).** Why: the only ~100K-class recoverable cost; scrolling is the current real-hardware
FAIL; #1 is structural with the largest upside. Expected hardware result: scrolling stops producing
the black overrun bar (or is substantially reduced), approaching one-frame fit; add Class B/C
precompute if the strip-only cut + fusion do not fully clear 128,009.

**#2 — Enemy scaling: per-(family,anim) single-probe dispatch, then per-actor variant-base hoist.**
Why: secondary real-HW limit; LOW-risk, general, widens the static-camera enemy margin. Expected
result: a few more enemies before the static-camera bar.

**#3 — Hammer/flail BlastEm discrepancy: diagnostic only, no production change.** Why: real hardware
is already clean; investigate cheaply if at all; do not spend production effort to satisfy BlastEm.

---

**Cody working tree modified: NO. Production source modified: NO. ROM built: NO. Build number
consumed: NO. Phase D: NO. Phase E: NO.**
