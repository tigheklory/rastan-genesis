# Build 0401 — Immutable WORK / READY / DISPLAYED Frame Ownership

Status: DESIGN + MECHANICAL VALIDATION (pre-build). Baseline Build 0400. No scheduling change in 0401
(worker stays in IRQ6; input unmoved; ISR wrapper unchanged). This is the ownership-only prerequisite
build. Supersedes the sprite-first ordering in `Andy_build0400_sprite_pipeline_root_cause_and_native_redesign.md`.

Goal: make publication state preemption-safe — producer writes WORK only, completed whole-frame state
becomes READY atomically, publisher reads READY only, DISPLAYED records what was committed — so the
NEXT build can flip scheduling (worker → preemptible mainline) without any further ownership work.

---

## 1. Exact dma_publish_frame read set (mechanically recovered) [S]

`dma_publish_frame` (dma.s:70) calls, in order, the six commit routines. Their complete runtime inputs:

| subsystem | publisher routine | mutable inputs consumed | size | class |
|---|---|---|---|---|
| palette | `vdp_commit_palette` | `palette_pending` (flag), `staged_palette_words` | 128 B | SINGLE, fully-rewritten |
| tiles | `vdp_commit_tiles_if_dirty` | `tiles_dirty` (flag), `staged_tile_words` | 96 B | SINGLE, fully-rewritten |
| Plane B | `vdp_commit_bg_strips_if_dirty` | `bg_row_dirty` (32-bit mask), **`staged_bg_buffer`** | 4096 B | SINGLE, **dual-role mirror** |
| Plane A | `vdp_commit_fg_narrow_strips` | `fg_row_dirty` (mask), `fg_col_dirty`, `fg_narrow_desc_table` (64·2), `fg_narrow_desc_count`, **`staged_fg_buffer`** | 4096 B | SINGLE, **dual-role mirror** |
| sprites | `vdp_commit_sprites_vram` | `pc090oj_sat_frame_ready`, `pc090oj_sat_bank`/`_front`, `staged_sprite_sat`/`_b` (2·640), `pc090oj_tile_dma_worklist` (12·4), `pc090oj_tile_dma_count`, **and publisher MUTATES** `sprite_tile_resident_code` (49·2) + reverse directory/pages + reservation map after DMA | — | SAT **DOUBLE**; worklist/count/residency SINGLE + publisher-mutated |
| scroll | `vdp_commit_scroll` | `staged_scroll_x_bg/fg`, `staged_scroll_y_bg/fg` | ~8 B | SINGLE, fully-rewritten |

WRAM headroom [S]: Genesis BSS top ≈ 0xFFC560; WRAM ends 0xFFFFFF → ~14 KB above BSS before the stack.
Sufficient for the generation-safe storage below. **No WRAM blocker.**

Classification per task:
- **Already immutable / double-buffered:** SAT banks (`pc090oj_sat_bank` flip).
- **SINGLE, fully-rewritten each frame (trivial to double-buffer by pointer swap):** palette, tiles, scroll.
- **SINGLE, publisher-mutated allocator/residency state:** `sprite_tile_resident_code`, reverse
  directory/pages, reservation map, `pc090oj_tile_dma_worklist`/`_count`.
- **SINGLE, DUAL-ROLE mirror (the hard one):** `staged_fg_buffer`, `staged_bg_buffer` — see §3.

---

## 2. WORK / READY / DISPLAYED model [design]

Generation counters (new BSS words): `work_generation`, `ready_generation`, `displayed_generation`.

- Producer (arcade worker, still in IRQ6 for 0401): at tick start, `work_generation = ready_generation+1`
  (conceptually "producing the next frame"); it writes only WORK-owned storage.
- **Atomic promotion** at the single point where the whole tick AND all CPU-side graphics production of
  that tick have finished (end of the arcade worker, just before RTE for 0401): one event sets
  `ready_generation = work_generation` and swaps the WORK storage to READY. No subsystem promotes early.
- Publisher (IRQ6, start of next frame): if `ready_generation != displayed_generation`, publish the
  READY generation and set `displayed_generation = ready_generation`; else **HOLD** (publish nothing,
  leave the previous complete frame displayed). Publisher reads only READY-owned storage.

Backpressure: READY N may wait for VBlank while WORK N+1 is produced → READY and WORK must not alias
mutable storage (hence the double-buffer / snapshot below). `tick_pending` stays saturating 0/1; no tick
skipping, no catch-up. (In 0401's sequential scheduling backpressure never actually triggers, but the
storage is made non-aliasing so the scheduling build is a pure scheduling flip.)

---

## 3. Smallest generation-safe package per subsystem [design]

**Palette / tiles / scroll (fully-rewritten, SINGLE):** pointer-swap double-buffer. Two buffers each
(`_a`/`_b`), a WORK pointer and a READY pointer; producer writes via WORK pointer, publisher reads via
READY pointer, promotion swaps the pointers. Cost: +128 B + 96 B + 8 B + a few pointer words.

**Sprites (the task's emphasized transaction):** one READY generation must atomically own: generation id,
READY SAT bank, tile-DMA worklist + count, the pattern-source descriptors the worklist references,
ready/dirty + cancellation state, and the **reservation-cleanup metadata**. SAT bank flip already
provides double-buffering of the SAT data; add a WORK/READY **worklist+count** pair (pointer-swap, +48 B)
and bind the SAT-bank identity to the generation. **Residency generation-safety:** the publisher writes
`sprite_tile_resident_code`/reverse-directory/reservation AFTER DMA; the producer reads/mutates the same
for allocation. **DECISION 2 — LOCKED (stronger invariant): publication must NEVER mutate state owned or
observed by an in-progress WORK generation** (the weaker "finishes before the next allocator begins" is
insufficient for the scheduling build, where WORK N+1 is already in progress while READY N awaits VBlank
and VBlank may preempt WORK N+1 to publish READY N). Three separated concepts: **WORK** residency =
producer's private mutable prediction; **READY** residency transaction = immutable description of the
VRAM residency changes READY N requires (pattern DMA destinations + post-commit result); **DISPLAYED**
residency = hardware truth after commit. Publication reads the READY transaction and writes only
READY/DISPLAYED-owned state — never the live WORK allocator (`sprite_tile_resident_code`, reverse
directory/pages, reservation map, `worklist_entry_for_slot`, cleanup metadata). WORK N+1 may base its
prediction on the state that WILL exist after READY N's ordered publication; the publisher's result is
adopted into WORK only at an ownership boundary where no active WORK generation observes a mid-change
structure. **45 residency/allocator sites in pc090oj_hooks.s are in scope.**

**Plane A / Plane B (DUAL-ROLE mirror — the key dependency):** `staged_fg_buffer`/`staged_bg_buffer` are
BOTH the producer's persistent VRAM-state mirror (read to compute incremental dirty rows/cols — Sonic-
style) AND the publication source (publisher DMAs the dirty rows). **Naive pointer-swap double-buffering
breaks the mirror** (the producer needs one consistent view of current VRAM; two swapping buffers
diverge). Smallest generation-safe solution that PRESERVES the incremental model + resolver + the
protected Build-0399 combined-X/Y fix (all of which live in the untouched producer):
> keep the single live mirror as WORK; at promotion, **snapshot only the dirty rows/cols** (those flagged
> by `fg_row_dirty`/`bg_row_dirty`/`fg_col_dirty`/`fg_narrow_desc_table`) plus their descriptors into a
> READY package; the publisher DMAs from the READY snapshot, not the live mirror.
The producer's incremental write logic and the resolver are **not touched**; only (a) a snapshot step at
promotion and (b) the publisher's source pointer change.

**DECISION 1 — LOCKED (option a): full worst-case independent READY snapshots.** Reserve Plane A READY
4096 B + Plane B READY 4096 B + their generation-owned descriptors/masks. IRQ6 never reaches back into
the mutable WORK mirror — no bulk-transition exception. For ordinary incremental frames the snapshot may
copy only the dirty payload into the reserved READY area, but the reserved storage MUST represent the
full 4 KB worst case. `staged_fg_buffer`/`staged_bg_buffer` remain the producer's persistent incremental
WORK mirrors (resolver/narrow-column/dirty-row/Build-0399/Sonic-streaming all untouched). After
implementation the actual linked WRAM map must be verified to have no overlap; if it does, STOP with the
map.

---

## 4. Publication behavior / no-new-READY hold [design]
Refactor the six `vdp_commit_*` so their inputs are the READY-owned pointers/snapshots (palette/tiles/
scroll via READY pointer; planes via READY snapshot; SAT via the generation's READY bank; worklist via
READY pair). If `ready_generation == displayed_generation`, skip publication entirely (hold the displayed
frame) — do not re-DMA unchanged data merely because another VBlank occurred, and never consume next-
frame descriptors. Keep the Build-0400 black-strobe fix (ordinary `fg_boundary_install` display-on;
scene-entry blanking under `genesistan_scene_present_pending`) — unchanged.

## 5. What 0401 does NOT change (protected)
Worker stays in IRQ6; RTE not converted to RTS; IPL/watchdog-NOP wrapper unchanged; input timing
unchanged (no move to tick-start). Plane-A resolver, Build-0399 combined-X/Y fix, Build-0400 rope-exit
fix, Build-0400 black-strobe fix, rope behavior, scene presentation, Sonic-style incremental scrolling —
all unchanged. No new permanent NOP scaffolding; any size change uses the shift-table reflow pipeline.

## 6. Mechanical validation checklist (the task's 12) — design-level status
1. publisher reads READY-owned only — **by construction (§3/§4)**.
2. producers write WORK-owned only — palette/tiles/scroll via WORK pointer; planes write the WORK mirror;
   sprite producer writes WORK SAT bank + WORK worklist — **by construction**.
3. READY immutable promotion→publication — palette/tiles/scroll (swapped-away buffer untouched); plane
   snapshot is a copy; SAT READY bank not written by producer until re-flip — **holds**.
4. WORK→READY atomic from IRQ6's view — single promotion event (pointer swaps + `ready_generation` set)
   — **holds**.
5. new WORK cannot overwrite unpublished READY — double-buffer/snapshot guarantees it — **holds** (plane
   bulk-transition special-case is the caveat to confirm, §3).
6. partial publication impossible — publisher reads only a promoted generation — **holds**.
7. SAT + worklist + count + descriptors same generation — bound to the generation id — **holds once the
   worklist pair + SAT-bank-id binding are added**.
8. publisher residency/reservation cannot race next WORK allocator — **requires the ownership-transfer
   invariant proof (§3 sprites)** — the main remaining proof obligation.
9. plane descriptors cannot point at WORK-overwritten source words — **the snapshot guarantees it**
   (that is the reason for the snapshot).
10. palette/scroll/pattern jobs cannot mix generations — pointer-swap per generation — **holds**.
11. no-READY preserves the displayed frame — explicit hold (§4) — **holds**.
12. Build-0400 scheduling otherwise unchanged — **by scope (§5)**.

Remaining proof obligations before code: (a) confirm the Plane A/B snapshot-vs-bulk-transition choice
(§3), (b) establish the sprite residency/reservation ownership-transfer invariant (§3/#8).

## 7. Implementation surface (files)
- New BSS: generation counters; palette/tiles/scroll `_a`/`_b` + pointers; worklist/count `_a`/`_b` +
  pointer; plane READY snapshot buffers + READY descriptor copies; DISPLAYED.
- `dma.s` / `vdp_comm.s`: publisher source → READY pointers/snapshots; add the no-READY hold gate.
- `palette_hooks.s`, `tilemap_hooks.s`, `fg_tile_cache.s`: producers write via WORK pointer (planes keep
  writing the live mirror; add the promotion-time snapshot).
- `pc090oj_hooks.s`: WORK/READY worklist pair + generation binding; residency ownership-transfer.
- The promotion event (pointer swaps + snapshot + `ready_generation`) at the arcade-worker completion
  point; DISPLAYED update + hold gate in the publisher.
Size-changing edits go through `specs/rastan_direct_remap.json` + the shift-table reflow — no NOP padding.

---

# IMPLEMENTED (Build 0401, counter 401, canonical SHA aa6876b7…07b65) [canonical=PASS entry=PASS epoch=FAIL]

Design realized with a **copy-at-promotion** model so the producers (and thus the protected resolver,
Build-0399 X/Y fix, narrow-column/dirty-row/Sonic-streaming logic) are **untouched** — they keep writing
the existing `staged_*` WORK structures exactly as in Build 0400.

**Promotion point:** `_vblank_service` top, immediately after `vdp_prepare_sprites` and **before**
publication (`bsr frame_promote_work_to_ready`). In Build-0400 scheduling the previous worker has fully
completed before `_vblank_service` runs, so this captures that frame. (The scheduling build will move
this to the worker-completion boundary in mainline.)

**WORK state (producer-private, unchanged):** `staged_palette_words`/`palette_pending`,
`staged_tile_words`/`tiles_dirty`, `staged_bg_buffer`/`bg_row_dirty`, `staged_fg_buffer`/`fg_row_dirty`/
`fg_col_dirty`/`fg_narrow_desc_table`/`fg_narrow_desc_count`, `staged_scroll_*`,
`pc090oj_tile_dma_worklist`/`pc090oj_tile_dma_count`, SAT back bank, `sprite_tile_resident_code`,
`worklist_entry_for_slot`.

**READY state (independent immutable snapshot, new BSS in vdp_comm.s):** `ready_palette_words`/
`ready_palette_pending`, `ready_tile_words`/`ready_tiles_dirty`, `ready_bg_buffer` (full 4096 B)/
`ready_bg_row_dirty`, `ready_fg_buffer` (full 4096 B)/`ready_fg_row_dirty`/`ready_fg_col_dirty` (8 B)/
`ready_fg_narrow_desc_table`/`ready_fg_narrow_desc_count`, `ready_scroll_*`, `ready_tile_dma_worklist`/
`ready_tile_dma_count`. Promotion full-copies each plane into its READY buffer (worst-case capacity,
DECISION 1 — no live-mirror fallback), copies palette/tiles only when their flag is set, copies scroll
and the worklist, transfers the dirty flags to READY, and **clears the WORK flags** so the next producer
restarts cleanly; then `work_generation++`, `ready_generation = work_generation`. SAT is the existing
double-buffered bank/front mechanism (the front bank after the publisher's swap is the READY SAT).

**DISPLAYED state:** `displayed_generation` (committed generation) + `displayed_sprite_tile_resident_code`
(hardware-truth residency). Publication (`.Lvcs_tile_dma`) now writes the residency result **only** to
`displayed_sprite_tile_resident_code` — never the live WORK `sprite_tile_resident_code`.

**Plane snapshot representation:** full independent 4096-byte READY buffers per plane; the publishers
(`vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_columns_if_dirty`, `vdp_commit_fg_narrow_strips`,
`vdp_commit_fg_strips_if_dirty`) now read `ready_bg_buffer`/`ready_fg_buffer` + the READY masks/
descriptors and clear the READY flags. No publication path reads the WORK mirrors.

**Sprite residency representation:** WORK = `sprite_tile_resident_code` + reverse/reservation (producer-
private, unchanged); READY transaction = `ready_tile_dma_worklist` + `ready_tile_dma_count` + the SAT
front bank; DISPLAYED = `displayed_sprite_tile_resident_code`. The publisher's per-slot reservation
cleanup was removed from `.Lvcs_tile_reset` (it mutated WORK); publication now only clears the READY
count it consumed.

**DISPLAYED → future-WORK synchronization:** `frame_adopt_residency`, called from `_vblank_service`
after publication and before the tail-jmp to the worker (where no WORK generation is active): copies
`displayed_sprite_tile_resident_code` → `sprite_tile_resident_code` (adopt hardware truth) and resets the
entire `worklist_entry_for_slot` reservation map to free (0xFF). In Build-0400 sequential scheduling this
is idempotent (DISPLAYED equals the producer's confirmed predictions).

**No-new-READY hold:** `_vblank_service` publishes only when `ready_generation != displayed_generation`,
then sets `displayed_generation = ready_generation`; otherwise it skips publication and holds. (In
Build-0400 scheduling a frame is produced every IRQ6, so this always publishes.)

**Actual WRAM map:** Genesis BSS base 0xFF4000 (arcade a5-WRAM 0xFF0000–0xFF4000 is below and disjoint);
READY buffers at 0xFF6304 (`ready_bg_buffer`)/0xFF7304 (`ready_fg_buffer`); `displayed_sprite_tile_
resident_code` 0xFFD970; BSS top 0xFFE77A → ~6 KB headroom below the stack. Build "Range overlap check:
PASS (disjoint)"; gameplay-entry gate PASS; 30 s MAME trace address_errors=0 bus_errors=0.

**Known behavioral notes vs Build 0400 (expected, for Tighe's verification):** (1) 0401 adds a full
two-plane snapshot copy (~40 K cycles/frame), so it runs **slower** than 0400 under load (ownership test;
performance is not a goal for this build and is addressed by the later scheduling/sprite phases). (2) A
canceled worklist entry (code 0xFFFF, no DMA) now leaves `sprite_tile_resident_code` at the DISPLAYED
truth after adopt rather than the producer's unconfirmed prediction — a minor edge difference.

**Scheduling retained:** YES — worker still tail-jmped at 0x3A208, input timing unchanged, RTE not
converted, IPL/watchdog wrapper unchanged.

**Files changed:** `apps/rastan-direct/src/vdp_comm.s` (READY BSS, `frame_promote_work_to_ready`,
publisher redirects for tiles/bg/fg-strips/scroll, `_vblank_service` hook + gate),
`apps/rastan-direct/src/dma.s` (palette publisher → READY), `apps/rastan-direct/src/tilemap_hooks.s`
(Plane-A column/narrow publishers → READY), `apps/rastan-direct/src/pc090oj_hooks.s`
(`displayed_sprite_tile_resident_code` BSS, sprite publisher worklist→READY + residency→DISPLAYED,
`frame_adopt_residency`). No remap-spec change was required (ownership code lives in the native wrapper).

**Status:** built, canonical+entry gates PASS, numbered + preserved. NOT self-declared accepted — Tighe
performs the gameplay/visual verification.
