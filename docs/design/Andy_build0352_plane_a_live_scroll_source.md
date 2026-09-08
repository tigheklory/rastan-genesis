# Andy — Build 0352: Live Scroll-Advanced Plane-A Source (fix "cave on Segment 0")

**Task:** EXTENDING · **Language:** 68000 assembly only (no C) · **Build:** 0352 (numbered, preserved).
Master: [Andy_sonic1_native_68000_plane_a_streaming.md](Andy_sonic1_native_68000_plane_a_streaming.md) ·
Prior: [Andy_build0351_plane_a_shared_live_resolver.md](Andy_build0351_plane_a_shared_live_resolver.md).

## What this fixes
Build 0351 (shared resolver) made the level "a lot more accurate" (Tighe) but left one bug: **Segment 0
visually showed Segment 1's cave** on Layer A (collision correct). Diagnosed to the resolver sourcing
the strip descriptor statically as `strip_src_table[row>>2] + a5@0x013E*0x40 + (col>>2)*4`, which
applies the **global leading-edge segment counter** `a5@0x013E` uniformly to every plane column — so
once that counter ticks into the cave segment while segment-0 columns are still on screen, the cave
base bleeds across the plane.

## Change (arcade-grounded)
`resolve_plane_a_cell` now sources the strip descriptor from the **live** table `a5@0x1000`
(`PC080SN_DESC_REBUILD_SRC_TABLE = 0xFF1000`), which the running arcade program maintains as
`strip_src_table[i] + seg*0x40` at scene init and then **advances +4 per scrolled 4-column metatile
block** (`map_advance_source_ptrs`, arcade 0x0558C6) — a continuous, boundary-correct source that
never needs the global segment term.

Per-cell source = `a5@0x1000[row_group] + (col_block - strip_group)*4`, where `strip_group`
(`a5@0x10CC`) is the plane column-block the live pointer currently sits at:
- **Horizontal entering column:** `col_block == strip_group` → delta 0 → exactly `selector0`'s
  original current-block source ⇒ **0351 horizontal correctness preserved**.
- **Vertical row:** the delta walks each plane column's own block ⇒ every column gets its own correct
  segment, with **no global segment term** ⇒ the cave no longer bleeds into Segment 0.

The static `.Lplane_a_strip_src_table` + `a5@0x013E*0x40` reconstruction is removed from the resolver.
All four gameplay producers (selector-0, selector-1/2, pan-up, pan-down) still share this one resolver
(0351 coherence retained); the 0350 Sonic-style column publisher is unchanged.

## Build / validation
- **0352** release SHA `9f6487564b4fcaad378b14e98d8479fe4cafa4f1cfd79bff1eefb71025adbf85`;
  variants `_d 086536…`, `_s 3492ce…`, `_do ede587…`. Counter = 352. 68000 asm only; no C.
- assemble/link OK; boot guard PASS pre+post; canonical **PASS**; gameplay-entry **PASS**; seven-epoch
  **FAIL** (the fragile synthetic record-3/`0x034C` gate — non-blocking label, ROM preserved by the
  fixed Makefile); 30s Genesis smoke `exceptions=0`, `crash_handler_entries=0`, boots to gameplay.
- Ledger: `0352 PRODUCED 2026-09-08 auto-recorded-by-release [canonical=PASS entry=PASS epoch=FAIL]`.
- Builds 0348–0352 (+variants) all preserved; nothing deleted/overwritten/renumbered.

## KF-072 / Plane B / D00462
KF-072 preserved (source-selection change only; no coordinate/ring change; VRAM dests unchanged).
Plane B unchanged. `D00462` Segment-5 crash: separate, known PC090OJ-space failure; not addressed.

## Slowness / vblank overrun (noted, not this task)
Tighe observed slowness and black bars on the `_do` (display-off) variant = the publication phase
overrunning vblank. This is a pre-existing whole-frame budget issue, not caused by the Plane-A
resolver/publisher (the column publisher reduced Plane-A transfer ~64×). Profiling deferred; correctness
prioritized per the task.

## Manual test (Tighe)
ROM: `dist/rastan-direct/rastan_direct_video_test_build_0352.bin` (GENESIS NTSC), R1P1. Key check:
**Segment 0 should now be outdoor-only (no cave); Segment 1 keeps its cave.** Also re-verify the 0351
accuracy gains (horizontal columns, vertical rows, axis-switch coherence) did not regress — delta 0 on
the horizontal path is designed to keep them identical. Compare 0352 vs 0351 vs earlier pre-0349 look.

## Uncertainty / next
The one unproven quantity is the exact plane-column↔`strip_group` alignment and delta wrap for
off-screen margin columns; visible columns (delta small) should be correct. If Segment 0 still shows
any cave, or a boundary seam appears, the alignment reference (`strip_group` vs a scroll-derived block
index) is the next thing to pin via a short runtime check → Build 0353.

## STOP
Not a STOP. 0352 produced, numbered, preserved, gate-labeled, smoke-clean, playable. Awaiting Tighe's
R1P1 result (does Segment 0 lose the cave without regressing 0351?).
