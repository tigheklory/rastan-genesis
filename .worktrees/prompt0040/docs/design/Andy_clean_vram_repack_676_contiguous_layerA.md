# Clean VRAM Repack + 676-Slot Contiguous Layer-A — De-risked Findings + Scoped Implementation

**Agent:** Andy · **Date:** 2026-09-04 · **Status:** **BUILT as Build 0342** (all gates PASS). Implemented as
a **5-epoch** clean repack (keeps both proven streamed transitions) rather than the 4-epoch minimum probed
below — see the deviation rationale in the IMPLEMENTATION RESULTS section at the end. The sections 1–15
below are the original scoped plan (some detail, e.g. 4-epoch, superseded by the 5-epoch as-built results).

---

## 1/2. Old & New VRAM map (target)
| region | bytes | slots | owner |
|---|---|---|---|
| slot 0 | 32 | 0 | blank |
| Plane-B range 1 | | **1–662** | static B patterns |
| **Plane A (contiguous)** | | **663–1338 (676)** | Layer-A residency window |
| sprite patterns | | 1339–1535 | unchanged (49 16×16 cells) |
| Plane B nametable | 0xC000–0xCFFF | 1536–1663 | — |
| Plane-B range 2 | 0xD000–0xDFFF | **1664–1791** | static B patterns |
| Plane A nametable | 0xE000–0xEFFF | 1792–1919 | — |
| Plane-B range 3 | 0xF000–0xF7FF | **1920–1983** | static B patterns (Window unused) |
| SAT | 0xF800 | 1984+ | — |
| HScroll | 0xFC00 | | — |

Plane-B total = 662 + 128 + 64 = **854** (unchanged corpus, repacked into the three legal ranges). All
pattern writes land in gaps disjoint from every nametable/SAT/HScroll; every tile index < 2048.

## 3. Probe result — THE de-risking evidence (offline compile at cap 676)
- **min epochs = 4** (from 7 at 484). Chosen segmentation: **((0,3),(4,10),(11,12),(13,15))**; 2 minimum
  segmentations exist. Per-epoch union counts **[582, 639, 583, 639]**, all ≤ 676.
- **rope→waterfall streamed transition (record 2→3) DISAPPEARS** — it becomes internal to epoch 0
  (records 0–3). The complex column-45 handoff is eliminated entirely.
- **waterfall→next streamed transition (record 3→4) SURVIVES** — its arcade-proven scroll data
  (`scroll_x=0x0168, scroll_y=0x015D`) stays valid (3 is last of epoch 0, 4 first of epoch 1).
- The two new boundaries (10/11, 12/13) are **simple epoch swaps** (like the non-streamed boundaries in the
  7-epoch model) — no arcade scroll data required.

**Conclusion: the arcade-data coupling that made this risky is resolved.** The one surviving streamed
transition keeps valid data; the complex one is cleanly removed; the rest are simple swaps. Performance win
is real: **7→4 epochs, 6→3 transitions, and the hardest transition eliminated.**

## 6. Layer-A contiguous 663–1338 contract
Compiler capacity 484 → 676; `a_slot_first` decoupled from `b_last` and pinned to **663**; `a_slot_last`
1338; one contiguous range (no disjoint set). Sprite range 1339–1535 unchanged (Part 7).

## 5. TAITO / title-art note (needs verification, not yet done)
`b_slot` in the current compiler is **byte-sorted** (`{blob: 1+index for blob in sorted(b_blobs)}`), i.e. the
Plane-B corpus is already deterministic, **not** "repair-era appended." The "TAITO tiles separated at the end
of VRAM" concern therefore likely lives in the **frontend/title preload generator** (a separate subsystem),
not this Plane-B compiler. Part B/I should be scoped against that generator; it is **not** addressed by the
Plane-B repack alone. Flagged so it is not assumed done.

## 8. Compiler changes required (exact, scoped)
In `tools/translation/compile_pc080sn_genesis.py`:
1. `BOUNDARY_PHASE1_EPOCH_CAPACITY = 484 → 676`.
2. `b_slot`: assign byte-sorted blobs across `[(1,662),(1664,1791),(1920,1983)]` instead of `1+index`.
3. `a_slot_first = 663` (decouple from `b_last`), `a_slot_count = 676`, `a_slot_last = 1338`; update the
   `(855,1338)` assert → `(663,1338)`; keep the `< SPRITE_TILE_BASE` check; add B-range-vs-sprite/nametable
   non-overlap asserts.
4. `BOUNDARY_PHASE1_EPOCH_RECORDS` → `((0,1,2,3),(4,5,6,7,8,9,10),(11,12),(13,14,15))` (the 4-epoch seg).
5. `BOUNDARY_TRANSITION_DEFS`: drop `rope_to_waterfall`; keep `waterfall_to_next_rope` with
   `out_epoch=0, in_epoch=1` (records 3→4). The 10/11 and 12/13 boundaries are simple swaps.
6. Epoch-contract assert (`!= 7`) → validate against the recomputed 4-epoch minimum; update
   `expected_epoch_counts` and the transition `expected` set-size checks.
7. Downstream: `allocation_order`, package-id assignment, and the emitted constants follow automatically
   once (1)–(6) are set; the `.equ FG_BOUNDARY_SLOT_FIRST/COUNT` will emit 663/676.

Runtime/gate (data-driven, but bounds encoded):
8. `build0310_epoch_gate.lua` `verify_maps`/`verify_fixed_b` slot-validity bounds assume a contiguous
   `[SLOT_FIRST, SLOT_FIRST+SLOT_COUNT)` for A and `< SLOT_FIRST` for B — update to accept A=[663,1338] and
   B=[1,662]∪[1664,1983].
9. `tools/mame/run_build0310_epoch_gate.sh` `cases=(...)` — the hardcoded **7-case** list
   (`0:0:0 3:1:7 4:2:8 10:3:3 11:4:4 12:5:5 15:6:6`) must become the **4-case** list matching the new
   record/epoch/package ids.
10. `verify_build0311_transition_retention.py` references the old streamed transitions — reconcile to the
    single surviving streamed transition.

## 9/10. Performance before/after (projected from probe)
- epochs: 7 → **4**; transitions: 6 → **3** (one of them the eliminated complex rope handoff).
- Per-transition uploads and DMA bytes: to be reported from the rebuilt boundary report; structurally fewer
  and lighter (bigger resident window → less swapped in). Within-epoch DMA stays 0; no runtime allocator.

## 11. Hard safety assertions (to add in Part H)
Plane-B count 854; A capacity 676; sprite range unchanged; no pattern/nametable/SAT/HScroll overlap; every
tile index < 2048; no dropped required pattern; within-epoch A DMA = 0; ordinary B DMA = 0; runtime
allocator/search/LRU/visibility = false.

## 12. Builds
None yet. Counter unchanged = 341.

## 13. Why not built in this pass
The probe (offline, cheap) proved viability and resolved the only genuine risk. The remaining work is a large
tightly-coupled edit across the compiler, runtime constants, two MAME gates, and the transition-retention
verifier, each with build/gate cycles. Rather than plunge into that at the end of a very long session and
risk a stuck mid-state (money spent, no ROM), the de-risked scope above is handed off for a focused build
pass. This is a concrete scoped plan with the hard unknown resolved — not open research.

## 15. OPT-003
Deferred (unchanged).

---

# IMPLEMENTATION RESULTS — Build 0342 (BUILT, all gates PASS)

**ROMs (counter now 342, ledger records 0342):**
- `dist/rastan-direct/rastan_direct_video_test_build_0342.bin` sha256 `dea2711b749cae22...`
- `..._0342_d.bin` (CPU-load bar) `33db4980ef403910...`
- `..._0342_s.bin` (score metric) `30c57ab869f4ec0c...`
- Size 1,666,744 B (was 1,670,840 for 0341 — smaller ROM). **OPT-003 is NOT in 0342 (deferred).**

**Implemented (as designed):**
- Plane B: 854 patterns repacked into slots **[1–662] ∪ [1664–1791] ∪ [1920–1983]**, ordered by original
  arcade source tile code (b_repr), not byte-sort or historical slot. 0 dropped.
- Layer A: contiguous **663–1338 (676 slots)**. Sprites 1339–1535 unchanged.
- Residency recomputed at 676: **5 stable epochs** `((0-2),(3),(4-10),(11-12),(13-15))`, unions
  `[282,333,639,583,639]` (all ≤676). Both streamed transitions preserved (rope 2→3 peak 394; waterfall
  3→4 peak 478); the later simple epochs merged (old 7 → 5). record_to_package
  `[0,0,0,5,6,2,2,2,2,2,2,3,3,4,4,4]`.
- Generated PC080SN boundary binary: **49,732 → 47,268 B**.
- Hard non-overlap asserts added in the compiler (A/B/sprite/nametable/SAT/HScroll, tile index < 2048).
- Canonical coverage invariant updated 0x197EB8 → 0x196EB8 (smaller boundary binary).

**Residency/DMA before → after:**
- epochs 7 → **5**; residency transitions 6 → **4** (two simple boundaries eliminated: old 9/10 and 11/12
  merged away). Both streamed transitions retained. Larger 676-slot window retains more patterns across
  each transition → fewer/lighter pattern DMAs (the DMA-halt win). Within-epoch pattern DMA remains 0;
  ordinary Plane-B DMA 0; runtime allocator/search/LRU/visibility all false.

**Gates:** transition-retention PASS (rope 12 / waterfall 224 retained; peaks 394/478 ≤ 676); canonical
GATE_PASS; gameplay-entry gate PASS; **seven-epoch gate PASS** (all 6 cases: epochs 0-4 + both transitions,
full Plane-A + fixed Plane-B LUT PASS, code 0x034C→slot resolved, exceptions/address/bus errors 0).

**TAITO / title cleanup (Part C/K): NOT done in 0342.** The gameplay Plane-B corpus is now source-code
ordered, but the frontend/title TAITO/RASTAN/sword grouping lives in the separate title-preload generator
(`pc080sn_scene_preload_title.bin`), which 0342 does not modify. Per the SCOPE SPLIT this is a separate
follow-up build; 0342 is the R1/P1 performance ROM. **Formerly separated TAITO repair tiles folded back:
NO (deferred to the title-preload pass).**

**OPT-003:** deferred; reverted from the working tree for this build (its 0x034C clobber otherwise fails the
epoch gate — the same defect documented in Andy_opt003_code_rodata_layout_divergence_and_landing.md).
