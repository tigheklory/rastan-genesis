# Andy — Complete Arcade FG Decompile, Part 1: Ownership and Semantic Flow

**Type:** Analysis / decompilation only. **ROM/build: NONE. Production changes: NONE.**
**Scope:** arcade Rastan foreground / PC080SN **Plane-A** (FG) semantics. BG (Plane B) only where a shared
function/state requires it. Evidence: Ghidra `analysis/ghidra/rastan_arcade/exports/` (decompiler, full
listing, xrefs, call graph, function inventory) + `build/maincpu.disasm.txt`. All addresses `arcade_pc` /
arcade WRAM `a5@0xNNN` (a5 = 0x0010C000 arcade / 0x00FF0000 Genesis) unless labeled.

## Prior-state summary
The Genesis FG (Plane A) has accumulated partial hooks (Build 0155/0160 FG restoration, selector0/12 native,
pan-up/down, descriptor-rebuild, 6 inline writers) — the PC080SN census Part 1 lists them as Category-A
compatibility. This report recovers the *arcade* FG pipeline behind those hooks so a later task can design
one correct native Plane-A producer instead of another symptom fix. KF-010 (FG→Plane A), KF-014 (tile LUT),
KF-015 (full-plane scroll, +8 bias) are the governing findings. OPEN-001/017/018 track the incomplete map/FG.

## Complete FG call / ownership graph (gameplay)
```
player_main_update_51090
 ├─ FUN_00055650   FG ROOT — reads direction bitmask a5@0x10D0; sets dirty a5@0x13D0/0x1330
 │    ├─ (0x10D0 & 1) FUN_00055696   publish DOWN  (Y+)   [pan-down boundary branch @0x055704]
 │    ├─ (0x10D0 & 2) FUN_0005572e   publish UP    (Y−)   [pan-up   boundary branch @0x055790]
 │    ├─ (0x10D0 & 8) FUN_000557ba   publish RIGHT (X+)
 │    ├─ (0x10D0 & 4) FUN_00055854   publish LEFT  (X−)
 │    │      each → FUN_00055948 (when a tile boundary is crossed) and → FUN_000406a4 (shared post)
 │    │
 │    └─ FUN_00055948  PUBLISH DISPATCH — selector a5@0x10A8, strip a5@0x10CA
 │         ├─ a5@0x10A8==0 → FUN_00055968 (dest a5@0x10A0) → FUN_000559b2  [terminal FG write, vertical]
 │         ├─ else         → FUN_00055990 (dest a5@0x10A4) → FUN_00055a14  [terminal FG write, horizontal]
 │         │      both then a5@0x10CA++ (strip index)
 │         └─ FUN_000558a2  strip/group advance:
 │              if a5@0x10CA==4 → FUN_000558c6 (advance source ptrs 0x10D000/0x10D004),
 │                                FUN_00055904 (rebuild 16 descriptors 0x10D000→0x10D040/0x10D080),
 │                                a5@0x10CC++ (group/page); if ==0x10 → FUN_000558e0 (page wrap)
 │
 ├─ FUN_00055AD6   PARALLEL Plane-B/BG publisher (dest 0xC00000; state a5@0x10F0/F2/F4/F6/F8) —
 │                 mirrors FUN_00055650; FUN_00055b3c→FUN_00055c4a→item-page strips (0x055C2E/0x055C5E).
 │                 OUT OF FG SCOPE except as a structural twin (see §F).
 └─ FUN_00055AB4   scroll-register commit (a5@0x10AE/0x10B0/0x10EC/0x10EE → PC080SN scroll regs; already
                    rewritten to Genesis staged_scroll_* in the current build).
```

## Producer-family table
| Family | arcade_pc | Callers | Semantic purpose | Executes when |
|---|---|---|---|---|
| FG root | FUN_00055650 | player_main_update_51090 | Dispatch FG publication by scroll direction | every gameplay frame |
| Down (Y+) | FUN_00055696 | 55650 | Publish FG rows entering at bottom | 0x10D0 bit0 set |
| Up (Y−) | FUN_0005572e | 55650 | Publish FG rows entering at top | 0x10D0 bit1 set |
| Right (X+) | FUN_000557ba | 55650 | Publish FG cols entering at right | 0x10D0 bit3 set |
| Left (X−) | FUN_00055854 | 55650 | Publish FG cols entering at left | 0x10D0 bit2 set |
| Publish dispatch | FUN_00055948 | 55696/0572e/057ba | Route to selector writer, advance strip | a boundary crossed |
| Selector-0 writer | FUN_00055968 → FUN_000559b2 | 55948 | Emit a 4-tile FG **column** (stride 0x80) | a5@0x10A8==0 |
| Selector-1/2 writer | FUN_00055990 → FUN_00055a14 | 55948 | Emit a 4-tile FG **row** (stride 2, dir per sel 1/2) | a5@0x10A8≠0 |
| Strip/group advance | FUN_000558a2 (+558c6/55904/558e0) | 55948 | Advance source ptrs / rebuild descriptors / page wrap | strip index hits 4 |
| Shared post | FUN_000406a4 | all four directions | Post-publish shared work (BG/collision/step) | after each direction |
| Frontend inline FG | 0x03A350/0x03A6FE/0x03A708/0x03A72A/0x03AAEA/0x03D04C | title/VBlank | Fixed single-cell FG writes | frontend/title only |
| Frontend FG text | 0x03C3FE (+ text writers 3c4d2…3c950, glyph 3bd48, number 3c2e2) | frontend | Text/high-score onto FG plane | frontend/text screens |

## A5 / work-RAM FG state table
| Offset | Meaning | Read by | Written by |
|---|---|---|---|
| 0x10D0 | **Direction request bitmask** (b0 down,b1 up,b3 right,b2 left; b4/b5/b6/b7 = deferred-publish pending) | 55650, 55AD6 | direction fns set defer bits; upstream sets requests |
| 0x10DA | Y scroll delta (per-frame) | 55696/0572e | upstream movement |
| 0x10D8 | X scroll delta (per-frame) | 057ba/05854 | upstream movement |
| 0x10BA | Y strip accumulator (row progress, boundary at 0x100 / 8) | 55696/0572e | 55696/0572e |
| 0x10B8 | X strip accumulator (col progress, boundary 0xA0 / <0) | 057ba/05854 | 057ba/05854 |
| 0x10B4/0x10B6/0x10B2/0x10F2 | per-direction fine sub-accumulators (&8 = tile boundary) | dir fns | dir fns |
| 0x10CA | **Strip index** 0..3 (wraps at 4) | 55948/55968/55a14/559b2 | 55948 (++) |
| 0x10CC | **Strip group / page** 0..0x0F (wraps at 0x10) | 55696/0572e/057ba, 558a2 | 558a2 (++) |
| 0x10A8 | **Selector** (0 / 1 / 2) — writer orientation/parity | 55948/55696/0572e/057ba/55a14 | upstream/scene |
| 0x10A0 | FG dest ptr (selector-0 / horizontal) = 0xC08000 + (0x10CA*4 + 0x10CC*0x10) | 55968 | 057ba |
| 0x10A4 | FG dest ptr (selector-1/2 / vertical) = 0xC08000 + (0x3F00 − (0x10CA*0x100 + 0x10CC*0x400)) or ascending | 55990 | 55696/0572e |
| 0x10AE | FG **X scroll** register (accumulated, &0x1FF) | 55AB4 commit | 057ba/05854 |
| 0x10B0 | FG **Y scroll** register (accumulated, &0x1FF) | 55AB4 commit | 55696/0572e |
| 0x10C6 | page/tile pointer (→ 0x10D0A8 in rebuild) | 55904 | stage init |
| 0x13D0 | current-direction tag (0=down,1=up,2=left,3=right) + dirty | 406a4 | dir fns |
| 0x1330 | FG-dirty flag | — | 55650/55a14 |
| 0x020C | left-edge/limit gate | 55854 | scene |

## ROM / data-table inventory (FG source)
- **0x10D000..0x10D03C** — 16-entry **source pointer table** (WRAM), each entry a pointer to a tile/attr
  descriptor. Advanced by FUN_000558c6 (READ_WRITE 0x10D000/0x10D004) when a strip completes.
- **0x10D040..0x10D07C** — 16 derived **word1 (attr)** values; **0x10D080..0x10D0BC** — 16 derived **word0
  (tile)** values. Both rebuilt by FUN_00055904 from 0x10D000.
- **0x10D0A8** — current page/tile word = `*(a5@0x10C6)`.
- Terminal descriptor block (register A2 in FUN_000559b2/55a14): tile/attr strip source, terminator `0xFF`
  at `A2+0x20`; strip cells indexed `A2 + 0x20 + (strip_index*2 + i*8)` (order reversed for selector≠2).
- Stage-init population of 0x10D000 **from ROM** (the map/descriptor source, likely arcade 0x3951C-class
  tables) is **not covered by this trace** — deferred to Part 2 (see Unresolved).

## Source-pointer / cursor progression
Per frame, movement deltas (0x10DA Y / 0x10D8 X) accumulate into strip accumulators (0x10BA/0x10B8) and
per-direction fine sub-accumulators (0x10B4/B6/B2). When a sub-accumulator crosses a tile (`&8`), the
direction fn computes the FG dest (0x10A0 or 0x10A4 = 0xC08000 + strip/group geometry) and calls the
publish dispatch. The dispatch emits one 4-tile strip via the selector writer, then `strip_index (0x10CA)++`.
At `strip_index==4` the source pointers advance (558c6), the 16-entry descriptor is rebuilt (55904), and
`group (0x10CC)++`; at `group==0x10` the page wraps (558e0). So progression is **strip(4) → group(16) →
page**, walking the 0x10D000 source table, with scroll registers 0x10AE/0x10B0 tracking sub-tile offset.

## Initialization vs incremental publication
- **Incremental (per-frame):** the FUN_00055650 chain above — only the newly-entering strips are published,
  keyed by direction + accumulators. This is the normal gameplay scroll path.
- **Full initialization / reset:** (a) C-window blank-fill of the FG plane — arcade 0x3AF48 (`lea 0xC08000;
  d1=4096; d0=0x20`) via the 0x03AD44 fill, and 0x3AE80 (`0xC08100; d1=1900`) for partial; (b) stage-load
  population of the 0x10D000 source table + initial strip/group/scroll state (Part 2). These set up the
  plane before incremental scrolling takes over.

## Horizontal-scroll behavior
Right (FUN_000557ba): accumulate 0x10B8 += 0x10D8 until ≥0xA0; at a tile boundary (0x10B2&8) compute
`0x10A0 = 0xC08000 + (strip_index*4 + group*0x10)` and publish; then `0x10AE -= 0x10D8 & 0x1FF`.
Left (FUN_00055854): gated by a5@0x20C/0x10B8 sign; `0x10B8 -= 0x10D8`; `0x10AE += 0x10D8 & 0x1FF`; publish
via shared post. FG X scroll register = 0x10AE (committed by 55AB4). Consistent with KF-015 full-plane
model (no per-line).

## Vertical / pan behavior
Down (FUN_00055696): dest **descending** `0xC08000 + (0x3F00 − (strip_index*0x100 + group*0x400))` — new
rows fill from the bottom upward; boundary branch @0x055704 (pan-down publish). Up (FUN_0005572e): dest
**ascending** `0xC08000 + (strip_index*0x100 + group*0x400)`; boundary branch @0x055790 (pan-up publish).
FG Y scroll register = 0x10B0 (down +delta, up −delta, &0x1FF). Publication only fires at tile boundaries;
between boundaries only the scroll register moves (sub-tile smooth scroll).

## Frontend / text / item-page separation
- **Gameplay FG (target):** FUN_00055650 chain (dest 0xC08000). Collision side-channel included (below).
- **Frontend inline FG writers** (0x03A350/6FE/708/72A/AAEA/0x03D04C): fixed single-cell `move.w #tile,
  0xC08xxx` in the 0x3Axxx VBlank/title region — decorative/frontend, **independent** simple write tails,
  not gameplay-producer tails (answers G).
- **Frontend FG text** (high-score 0x03C3FE, text writers 0x03C4D2..0x03C950, glyph 0x03BB48, number
  0x03C2E2): text composited onto the FG plane on frontend/text screens — separate subsystem.
- **Item-page / Plane-B twin:** FUN_00055AD6 → FUN_00055b3c → item-page strips (dest **0xC00000** = BG /
  Plane B). Structurally identical to the FG chain but a different plane/state set (0x10F0/F2/F4/F6/F8) — BG
  scope, not FG; noted only because it shares the strip/descriptor machinery.

## Exact final PC080SN write tails
Two terminal writers, both 4-iteration strip loops writing tile+attr words to the C-window FG plane and
**also** to the collision map (`collision_map_64x64_words_base + ((dest − 0x604000) >> 1)`):
- **FUN_000559b2** (selector-0): `*A0 = tile; A0[1] = attr`, then `A0 += 0x80` (vertical column of 4).
- **FUN_00055a14** (selector-1/2): same, then `A0 += 2` (horizontal row of 4); strip index bit-reversed
  (`~idx & 3`) when selector≠2.
These are pure hardware/collision tails of the semantic decision made upstream. **The collision-map write is
mixed into the FG terminal writer** — a native FG replacement MUST reproduce this collision side-channel
(relevant to OPEN-017).

## Whether chip mechanics are mixed into earlier logic
- Direction fns (55696/0572e/057ba/05854): mostly **semantic** (accumulators, boundary decisions, scroll
  registers) but they also compute the raw **C-window dest address** (0xC08000 + geometry) — a chip detail
  mixed into the semantic layer.
- Publish dispatch (55948) + strip/group advance (558a2/558c6/55904/558e0): **semantic** (cursor/source
  management) — no direct hardware writes.
- Terminal writers (559b2/55a14): **pure chip tail** (C-window write) + collision side-channel.

## Proposed semantic cut boundaries
- **Cut level 1 (current, symptom-prone):** at the selector writers (FUN_00055968/55990) + pan branches +
  descriptor rebuild — what the existing Genesis hooks do. Native code must reproduce strip emission +
  collision + descriptor read. This split across many hooks is what produced the incomplete FG.
- **Cut level 2 (recommended for the one correct native implementation):** at **FUN_00055650 (FG root)** —
  let the arcade retain the *state machine* (direction requests 0x10D0, accumulators, strip/group cursor,
  source-pointer table 0x10D000, advance/rebuild/page-wrap 558c6/55904/558e0, scroll registers 0x10AE/0x10B0)
  as Category-D semantic input, and replace the entire publication + terminal-write with **one native
  Plane-A producer** that reads that state each frame and writes staged_fg_buffer + the collision map. The
  removable chip tails are the C-window dest computation and FUN_000559b2/55a14. This is the highest cut
  that keeps every arcade semantic decision and removes only PC080SN mechanics.
- **Cut level 3 (too high):** replacing the arcade scroll/cursor state machine itself — rejected (would be a
  Genesis-owned gameplay loop, violating ARCHITECTURE/KF-011).

## Unresolved questions (for Part 2)
1. **Stage-init population of the 0x10D000 source-pointer table from ROM** (map/descriptor tables, likely
   0x3951C-class) — not in this trace; needed for the full init path.
2. Exact **selector (0x10A8) 0/1/2 semantics** — orientation/parity/scene mapping; dynamic values per scene.
3. The Genesis symbol naming **`ARCADE_PC080SN_DEST_BG_OFFSET=0x10A0`** vs the decompile showing 0x10A0 as an
   **FG (0xC08000)** dest in the gameplay chain — reconcile (possible cross-context reuse).
4. Relationship of the **FUN_00055AD6 / 0xC00000 twin** (BG/Plane B + item-page strips) to the FG chain and
   whether any state is genuinely shared.
5. Runtime confirmation of direction-bitmask values, accumulator thresholds, and page-wrap timing under
   actual Stage-1 scroll (ARCADE MAME) — dynamic edge cases.
6. Frontend FG text/inline exact cell inventory (separate producer family) — enumerate if it must survive
   native Plane-A production.

---

**Arcade gameplay FG semantic ownership fully enumerated: YES** (the FUN_00055650 producer family, its four
directional publishers, publish dispatch, selector writers, strip/group/source-pointer management, terminal
write tails, scroll registers, and the collision side-channel are all identified and traced).

**Arcade gameplay FG source/cursor progression fully understood: NO** — the *incremental* progression
(strip→group→page walk of 0x10D000, accumulators, wrap/rebuild) is understood, but the **stage-init
population of the 0x10D000 source table from ROM** and the **selector 0/1/2 scene mapping** are not yet
proven (items 1–3 above). Those specific routines/state/data must be recovered before native design.

**Ready for FG decompile Part 2 (dynamic / edge-case verification): YES** — Part 2 should resolve items 1–6,
primarily the ROM source-table init and selector semantics, with ARCADE MAME confirmation of the accumulator
thresholds and page-wrap timing.
