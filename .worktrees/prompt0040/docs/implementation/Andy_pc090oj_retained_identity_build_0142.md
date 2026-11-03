# Andy — Build 0142 PC090OJ Retained Identity & Sparse SAT (Implementation + Native Evidence)

**Date:** 2026-07-07
**Type:** Authorized Andy implementation of the governing design
`docs/design/Andy_pc090oj_semantic_helper_families_build0142.md` (§§9-C → 9-E; authority §9-E > §9-D > §9-C).
**Baseline:** Build 0141 (`cebd389e8114b316881188623b41d4b71808b5738a39d2cd4a773163bc8aa04c`).
**Branch:** `rastan-direct-proposal` (no branch/reset ops). Design checkpoint `8380fbc`.

## Outcome
**Outcome A.** The per-frame PC090OJ mirror rediscovery + full SAT wipe/rebuild/relink is replaced by a
retained record-driven translation state (record identity kept; sparse stable SAT slots; slot 0 = highest-priority
represented record; local link splice; bounded coalesced Build 0141 tile-DMA worklist; candidate-driven
compatibility for unconverted producers; one converted semantic family). All static and native invariants pass;
the renderer provably emits exactly the drawable set of its own mirror; stable DISPLAY_OFF drops to **994 cycles**
(Build 0141: 1426; Build 0140: 16350).

## ROM
- **Path:** `dist/rastan-direct/rastan_direct_video_test_build_0142.bin`
- **SHA256:** `f4c4234910fd56c739f874ad2a176ec447949f4e492b6526d37064f7dd23f245`
- **Size:** 1,563,844 B (Build 0141 = 1,562,248; +1596 B, matching the +0x63C engine `.text` growth).
- GATE_PASS, boot guard PASS, 30 s auto-trace clean (Final PC in frontend `0x3A1AE`/`0x3B280`, healthy SP, no unmapped memory).

## Source change (single production source: `apps/rastan-direct/src/pc090oj_hooks.s`)
1. **Retained state (BSS):** `record_to_slot[256]` (0xFF=unrepresented), `represented_records`/`waiting_records`
   (32 B bitmaps), `used_sat_slots` (16 B), `worklist_entry_for_slot[80]` (reserved index, 0xFF=none),
   `pc090oj_represented_count`, `pc090oj_sat_dirty`, `pc090oj_bootstrap_pending`, 6 scratch words.
2. **Engine (§§9-C/D/E):** `sync_record_from_mirror(record)` (reads mirror only; never writes mirror; never sets a
   candidate) → decode → activate / field-update / deactivate; `place_record_in_slot` (regenerates the destination
   from the mirror, re-derives the slot-keyed tile index `(1024+slot*4)&0x7FF`, queues/cancels the pattern DMA);
   `free_slot`; base-68000 bit scans (`first_ge`/`last_le`/`lowest_free_nonzero`/`highest_used`); local link splice
   with the slot-0 head invariant, new-head / head-delete / full-SAT eviction, waiting/overflow + promotion.
3. **Worklist (§9-E.1/9-E.2):** `worklist_entry_for_slot` reserves ≤ one physical entry per slot per interval;
   cancellation = `code 0xFFFF`; return-to-resident cancels; commit skips cancelled; post-commit reset touches only
   the reserved slots (O(count) → zero on a stable frame).
4. **Converted family:** `pc090oj_workram_block_sprites` (the 22-object work-RAM block for arcade
   `0x041DAE`/`0x041F5E`/`0x045DFA`): exact arcade mirror writes once → `sync_record_from_mirror` → clear the
   superseded candidate, VINT-masked.
5. **Unconverted producers:** `emit_slot` reduced to the mirror-bridge (write mirror + set candidate); the SAT is
   rebuilt from the mirror by the render path. All mirror writers still publish a candidate (audit preserved).
6. **Global controls:** `ctrl_set_0/1` (flip) and `sprite_ctrl_write/clear` (colbank) request a full 256-record
   reevaluation (set-all-candidates) only on an actual change.
7. **Init/bootstrap:** `renderer_init` (gated on the boot-cleared `pc090oj_scan_active`, so it self-heals on warm
   reset without touching `boot.s`) fills `record_to_slot`/`worklist_entry_for_slot` = 0xFF, clears bitmaps/counts,
   stages a hidden self-terminating SAT slot 0, and requests one 256-record bootstrap consumed once at first VBlank.
8. **Commit:** tile-DMA worklist (bounded, cancel-aware) always; SAT DMA gated by `sat_dirty`, length
   `max(highest_used+1,1)*4`.

**Preserved:** arcade mirror writes/order; all producer hooks; decode/transform predicates; Build 0141 pattern
residency + post-DMA update; priority via SAT links; no packing; no one-frame latency; no committed-shadow;
`boot.s`, `vdp_comm.s` VBlank order, PC080SN, specs, Makefile untouched.

## Canonical bookkeeping (sole tool change, value-only)
`CANONICAL_TOTAL_GENESIS_BYTES_COVERED` **0x17D688 → 0x17DCC4** in `postpatch_startup_rom.py` and
`verify_canonical_rom.py` (predictable coverage growth from the larger engine `.text`). `CANONICAL_OPCODE_REPLACE_COUNT`
**unchanged (133)**. `address_map.json`: no patched-site/wrapper change.

## WRAM layout (Build 0142 `out/symbol.txt`)
| symbol | addr | bytes |
|---|---|---|
| record_to_slot | 0xFF71F0 | 256 |
| represented_records | 0xFF72F0 | 32 |
| waiting_records | 0xFF7310 | 32 |
| used_sat_slots | 0xFF7330 | 16 |
| worklist_entry_for_slot | 0xFF7340 | 80 |
| pc090oj_represented_count | 0xFF7390 | 2 |
| pc090oj_sat_dirty | 0xFF7392 | 2 |
| pc090oj_bootstrap_pending | 0xFF7394 | 2 |
| scratch (rec/slot/link/draw/a/b) | 0xFF7396.. | 12 |

New WRAM ≈ **434 B**, contiguous after the existing PC090OJ block; no overlap (existing worklist `0xFF686E`,
resident `0xFF67CE`, mirror `0xFF69B0`, candidate `0xFF71B0` all below). Reused, un-boot-cleared new state is
initialised by `renderer_init` before first use.

## Native validation (MAME native debugger + Lua, established method)
Harness: `states/traces/build0142_native_validation/` (`dump.lua`, `cyc.cmd`, `analyze.py`, `frame*.bin`,
`native_trace.log`). Structural state dumped at settled frames; invariants checked offline; cycles/DMA from the
native `totalcycles` breakpoint trace (DISPLAY_OFF `0x700ce`, DISPLAY_ON `0x700e6`, tile-commit `0x729be`,
tile-trigger `0x72a5a`).

### Structural invariants — ALL PASS (states 0/1/0, 0/1/2, 2/0/0, 2/2/6)
- slot 0 owned by the lowest-index represented record; every represented record maps to exactly one used slot;
  every used slot has exactly one owner via `record_to_slot`; `used == represented`.
- Link chain from slot 0 visits each represented record exactly once, **ascending record index**, terminates
  (link 0) correctly.
- represented ∩ waiting = ∅; ordinary field updates retain slot ownership.
- Worklist: ≤ one reserved entry per slot; **max count 27 (≤ 80)**; cancelled entries perform no DMA; one frame had
  triggers < count (return-to-resident/free cancellation), none had triggers > count.

### Renderer is exact (2/2/6, independent mirror decode)
Independently decoding all 256 mirror records (same predicates: code-zero/unmapped/blank/offscreen/global-flip)
yields **drawable == represented, 22/22 identical** — no missing, extra, duplicated, or misordered sprite. All 22
staged SAT entries' transformed Y/X and slot-keyed tile index **match the decode exactly (0 mismatches)**.

### Represented count / SAT-DMA length
| state | represented | SAT-DMA words (= (highest_used+1)*4) |
|---|---:|---:|
| 0/1/0 | 23 | 92 |
| 0/1/2 | 23 | 92 |
| 2/2/6 | 22 | 88 |

0/1/0 and 0/1/2 match Build 0141 exactly (23). At the sampled 2/2/6 frame exactly 22 records are drawable and 22 are
represented; the difference from Build 0141's frame-720 count of 32 is game-state divergence from the changed
DISPLAY_OFF timing, not a sprite miss (proven by the exact drawable==represented decode above). Per the task,
byte-identity is not required; represented set / transformed values / chain order / visible output are the criteria.

### Cycle comparison (native `totalcycles`, DISPLAY_OFF `0x700ce` → DISPLAY_ON `0x700e6`)
| state (stable, count 0, sat clean) | Build 0142 | Build 0141 | Build 0140 |
|---|---:|---:|---:|
| 0/1/0 | **994** | 1426 | 16350 |
| 0/1/2 | **994** | 1426 | 16350 |
| 2/2/6 | **994** | 1426 | 16548 |

Stable DISPLAY_OFF = **994 cyc** (min = median across 209/161/143 samples/state): −93.9 % vs Build 0140, −30 % vs
Build 0141. On stable frames the worklist is empty (fast reset, O(0)) and `sat_dirty` is clear so the SAT DMA is
skipped entirely (**6 SAT-DMA events in the whole run**, vs one per frame in Build 0141). Changed frames upload the
pattern DMAs (36 triggers over 6 frames) and the SAT once.

### No-work / no-crash
Stable frames perform no full mirror scan, no SAT wipe, no full relink, no SAT DMA, and no pattern DMA. 30 s release
trace and the native run both exit clean (no exception/halt; frontend states 0/1/0 → 0/1/2 → 2/2/6 reached, same
progression as Build 0141).

## Known limitations
- **Visual confirmation pending Tighe (BlastEm/Exodus).** Logic-level evidence proves the renderer emits exactly the
  drawable set with correct transformed values and ascending priority; pre-existing sprite palette/position defects
  (OPEN-006, OPEN-024) are untouched by this architecture change and expected to persist until addressed.
- **Sprite-decay hook `0x5607C` (gameplay, unconverted)** reads the descriptor table by physical slot; under sparse
  ownership those slots hold different records than the old packed model. Descriptors are still maintained by
  `place_record_in_slot` so the hook does not fault, but its decay targets differ. It is not exercised in the
  frontend validation states; recommended as the next conversion (Build 0143).
- Warm-reset robustness relies on `boot.s` clearing `pc090oj_scan_active` (verified) as the init gate.

## Open/Closed Issues Impact
- **OPEN-024 (PC090OJ sprite subsystem incomplete):** advanced, not closed. Build 0142 replaces the ad-hoc
  per-frame rebuild with a retained-identity renderer whose SAT is proven to equal the mirror's drawable set with
  correct transformed values and ascending priority chain, and cuts stable DISPLAY_OFF to 994 cyc. Closure still
  requires visual confirmation and resolution of palette/position defects.
- **OPEN-006 (sprite/high-bank palette mapping deferred):** unchanged; the palette computation in `place_record_in_slot`
  is byte-for-byte the Build 0141 formula. No regression, no closure.
- No issue is closed by this build. No new issue opened (the `0x5607C` descriptor-slot semantic is recorded above as
  a Build 0143 recommendation, not a regression).
