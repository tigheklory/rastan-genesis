# Andy — Native Genesis Gameplay-FG Plane-A Design

**Type:** Analysis / design ONLY. **No code, no ROM, no build number consumed.** Baseline: Build 0297.
Next implementation build if later authorized: **Build 0298**. Authority: original Rastan arcade semantics
(Parts 1/2/2B). Rainbow Islands + Sonic 1 are **structural references only**.

## 1. Phase-0 baseline
- **Relevant priors:** KF-010 (FG→Plane A base 0xE000 / BG→Plane B) STRONG — applies (target plane). KF-014
  (PC080SN tile-LUT O(1), code domain 0x0000..0x3FFF) STRONG — applies (tile realization). KF-015 (full-plane
  scroll, raw-Y negation +8 bias, no per-line) STRONG — applies (scroll staging). KF-011 (arcade Level-5
  VBlank owns progression) STRONG/HIGH — applies (VBlank stays arcade-owned).
- **Rediscovery-Hazard HIGH touched:** KF-011 (respected: no Genesis loop/VBlank identity), KF-020/21
  (contaminated plane evidence — avoided).
- **Deferred-appendix entries relevant:** None.
- **Task classification:** INFRASTRUCTURE (native-replacement design).
- **Open/Closed issues touched:** OPEN-001/018 (native map/FG), OPEN-017 (FG/collision) — design context, no
  closure.
- **Contradiction of CONFIRMED/STRONG finding:** NONE.

## 2. Scope and authority
Design one final-production native Genesis Plane-A gameplay-FG producer that realizes Rastan's already-proven
arcade FG semantic decisions directly in Genesis Plane-A form, removing the PC080SN chip tail. Frontend/text
FG (Plane-A) use is **out of scope** and must survive. Sonic 1 68k disassembly is **not present in-repo**
(only `tools/sgdk/sample/game/sonic`, an unrelated SGDK C sample); Sonic-1 level-drawing structure is cited
from established Genesis-development knowledge and clearly labeled as reference, not repo-verified.

## 3. Proven Rastan FG semantic contract (Parts 1/2/2B)
- Root: `arcade_pc FUN_00055650` (direction dispatch on `a5@0x10D0`).
- Directional publishers (accumulator/boundary/scroll logic): down `FUN_00055696`, up `FUN_0005572e`, right
  `FUN_000557ba`, left `FUN_00055854`.
- Publish/cursor chain: `FUN_00055948` (dispatch + strip++), `FUN_000558a2` (group advance at strip==4),
  `FUN_000558c6` (source-ptr advance), `FUN_00055904` (16-entry descriptor rebuild), `FUN_000558e0` (page
  wrap at group==0x10, reload `a5@0x10A8`).
- **PC080SN terminal writers (the chip tail):** selector-0 `FUN_00055968`→`FUN_000559b2` (4-tile vertical
  column, C-window stride 0x80); selector≠0 `FUN_00055990`→`FUN_00055a14` (4-tile horizontal row, stride 2,
  parity `~idx&3` unless ==2).
- **Arcade semantic state to RETAIN (Category D):** direction `a5@0x10D0`; X/Y strip accumulators
  `a5@0x10B8/0x10BA` (X threshold **0xA0** runtime-proven; Y 0x100 static); fine sub-accumulators
  `a5@0x10B2/B4/B6`; strip index `a5@0x10CA` (0..3, wrap 4); group/page `a5@0x10CC` (0..15, wrap 0x10);
  source table `a5@0x10D000` (16 ptrs) + attr `0x10D040` / tile `0x10D080` arrays + page ptr `a5@0x10C6`;
  selector `a5@0x10A8` (∈{0,1,2,4,5,6}); mode `a5@0x10E8`; FG scroll `a5@0x10AE/0x10B0`; the source descriptor
  block (A2, `0xFF` terminator at +0x20).
- **PC080SN mechanics to REMOVE:** the C-window destination computation (`a5@0x10A0/0x10A4 = 0xC08000 +
  geometry`) and the terminal name-word writes in `FUN_000559b2/55a14` (and the selector-writer wrappers
  `FUN_00055968/55990`).
- **Terrain-collision contract (proven):** the terminal writers also write the descriptor word to a 64-wide
  word ring at the published position; consumers read `&0x7F`: 1=floor, 2=wall, 0=empty; FG-exclusive.

## 4. Rainbow Islands reference analysis (structural)
From `docs/design/Cody_rainbow_islands_vdp_template_analysis.md` + comparison docs. **Adopted structural
principles (already Rastan-compatible):** (a) VBlank is **commit-only**; game/graphics production runs outside
VBlank; (b) tilemap/scroll are **staged in target-shaped WRAM** and published by **bounded strip commits**
(40 words per strip, destination stepping) — NOT full-plane DMA each frame; (c) scroll staged in WRAM,
committed in VBlank; (d) hardware publication isolated at the native VDP boundary. **Explicitly NOT copied:**
Rainbow's VBlank ROM ownership (`0x000380`), its fixed WRAM addresses/flag words (`0xFFFFF6xx`, SAT shadow
`0xFFFFF800`), its mode words, its scheduler/transfer order, its C-Chip semantics, and its plane constants —
all game-specific. Rastan's **arcade-owned** VBlank remains authoritative (Rainbow's is Genesis-owned; we do
NOT adopt that).

## 5. Sonic 1 level-drawing reference analysis (structural, from established knowledge)
Sonic 1's incremental level drawing (`LoadTilesAsYouMove` → `DrawBlocks_LR` / `DrawBlocks_TB`, with
`Calc_VRAM_Pos` and `LoadTilesFromStart`→`DrawChunks` for init): **structural principles adopted:** (a) an
initial resident-window draw at load; (b) **no tilemap work on frames with no entering edge**; (c) a camera
crossing a tile boundary publishes exactly **one entering row (vertical move) or column (horizontal move)**;
(d) the destination is a **directly-computed wrapped name-table address** (Sonic's `Calc_VRAM_Pos` masks the
plane dimensions), not a virtual map projected afterward; (e) only newly-exposed cells are written.
**Explicitly NOT copied:** Sonic's 16×16 block / 128×128 chunk formats, level-map structures, camera flags,
main loop, plane bases, object system, world dimensions, and scroll semantics. (Names are misleading;
behavior cited structurally, not transcribed.) **[Updated by the publication-unit addendum]** these claims
are now **source-verified** against the actual `sonicretro/s1disasm` (AS branch)
`_inc/Level Drawing (REV00).asm`: `LoadTilesAsYouMove` is flag-gated per edge (bits 0–3); `DrawBlocks_TB` =
vertical column of 16 blocks, `DrawBlocks_LR` = horizontal row of 22 blocks; each 16×16 block = 4 name-table
cells; `Calc_VRAM_Pos` masks directly to a 64×32 wrapped plane; init is a separate `LoadTilesFromStart`/
`DrawChunks` path. Notably Sonic's vertical column = 16×4 = 64 cells — structurally identical to Rastan's
own 64-cell column, but Rastan's count derives from its own `FUN_00055968` `d1=0x10` loop, not from Sonic.

## 6. Three-way comparison
| Rastan semantic op | Rainbow analogue | Sonic 1 analogue | Structural lesson | Non-transferable | Native Rastan realization |
|---|---|---|---|---|---|
| Stage init FG population | staged tilemap init publish | LoadTilesFromStart→DrawChunks | draw resident window once from map source | Sonic chunk/level fmt; Rainbow WRAM/flags | populate staged_fg_buffer resident region from `a5@0x10D000`/descriptors (§11) |
| No-change frame | no strip commit when no flag | no draw when no camera edge | do nothing when arcade requests no publication | — | native producer only runs when the arcade directional publisher signals a boundary crossing |
| Scroll-right entering column | strip commit + scroll stage | DrawBlocks_LR entering column | one column at wrapped X | Sonic camera; Rainbow order | write entering column to staged_fg_buffer at wrapped X from `a5@0x10CA/CC` + `a5@0x10AE` |
| Scroll-left entering column | ″ | DrawBlocks_LR | ″ | ″ | mirror; left edge |
| Scroll-down/up entering row | ″ | DrawBlocks_TB | one row at wrapped Y | ″ | write entering row at wrapped Y from `a5@0x10B0` |
| strip/group/page advance | — | camera block/chunk step | cursor stays in game engine | — | **arcade retains** `FUN_00055948/558a2/558c6/55904/558e0` |
| Wrapped Plane-A dest | name-table addr | Calc_VRAM_Pos mask | mask to plane dims | Sonic dims | mask to Rastan's Plane-A dims (§10) from semantic map position |
| Scroll staging | WRAM scroll → VBlank | camera → HScroll/VSRAM | staged, committed in VBlank | Rainbow flags | existing `staged_scroll_x/y_fg` + `vdp_commit_scroll` (KF-015 +8) |
| Terrain collision publish | (n/a) | (n/a) | — | — | **Rastan-unique**: native producer writes the collision ring (§16) |
| Scene reset | re-init staging | LoadTilesFromStart | re-populate resident window | — | arcade re-inits source (§11), native re-draws resident FG |

**Answers:** (1) Rainbow proves native VDP realization + WRAM staging replaces the arcade chip (no PC080SN
software device). (2) Sonic proves direct entering-edge writes into a wrapped name table with no virtual map.
(3) Both fit Rastan's already-proven entering-strip publication semantics. (4) Neither's game-state/map/camera
machinery transfers. (5) The design converges on the native shape **because of Rastan's own semantics**
(Rastan already computes entering strips + scroll); it does not import another game's architecture.

## 7. Semantic cut
**Conceptual cut:** at the FG publication intent (Part-1/2 named `FUN_00055650`). **Implementation cut
(refinement):** replace only the **chip realization** — the selector writers `FUN_00055968`/`FUN_00055990`
and terminal writers `FUN_000559b2`/`FUN_00055a14` **plus the C-window dest computation** — with **one native
Plane-A producer**. Everything else (root, four directional publishers with their accumulators/boundary/scroll
logic, `FUN_00055948` dispatch/strip++, `FUN_000558a2/558c6/55904/558e0` cursor/source/page progression)
stays **arcade-owned and continues to run and advance the state.** Rationale: this keeps every genuine game
decision (when/what/where to publish, cursor progression, scroll) in the arcade and replaces ONLY the PC080SN
name-word emission — satisfying "arcade owns accumulators/cursor/scroll" better than replacing the whole
`FUN_00055650` subtree (which would pull the accumulator logic below the cut). The native producer **reads**
arcade state; it never **owns** it.

## 8. Arcade state retained (above/at the cut)
All of §3's Category-D state, unchanged, advanced by the retained arcade routines. The native producer reads:
selector `a5@0x10A8`, strip `a5@0x10CA`, group `a5@0x10CC`, source arrays `a5@0x10D040/0x10D080` + descriptor
block, FG scroll `a5@0x10AE/0x10B0`, direction `a5@0x10D0`.

## 9. PC080SN mechanics removed (below the cut)
`FUN_00055968`, `FUN_00055990`, `FUN_000559b2`, `FUN_00055a14`, and the `a5@0x10A0/0x10A4 = 0xC08000+geometry`
dest computation in the directional publishers. No C-window address, no virtual name RAM, no projection
remains in the FG path.

## 10. Native Plane-A geometry
- **Plane A** base `VRAM 0x0000E000`; plane-size register (`VDP_REG_PLANESIZE`=16) per current rastan-direct
  config; `staged_fg_buffer` is the **target-shaped WRAM shadow** (one name word per Plane-A cell, 64-column
  wrapped — the exact row/height from the current `.space` in `vdp_comm.s`).
- **Entering edge → wrapped cell:** the arcade's decided map position (strip index `a5@0x10CA` + group
  `a5@0x10CC` + FG scroll `a5@0x10AE/0x10B0`) maps to a Plane-A **column** (horizontal scroll, selector 0) or
  **row** (vertical scroll, selector ≠0). The wrapped Plane-A column = `(scroll-derived tile column) mod
  plane_width`; wrapped row = `(scroll-derived tile row) mod plane_height` — a direct mask (Sonic
  `Calc_VRAM_Pos` structure), computed from the **semantic** position, NOT from `0xC08000`.
- **X wrap / Y wrap:** modulo the Plane-A width/height (power-of-two mask). **Scroll relationship:** the
  existing `staged_scroll_x_fg`/`staged_scroll_y_fg` + `vdp_commit_scroll` already publish FG scroll with the
  KF-015 raw-Y negation + `+8` bias; the producer must keep the published edge one tile ahead of the visible
  window (same lead the arcade's `0xA0`/`0x100` thresholds already give). **Unchanged cells** are never
  regenerated (only the entering column/row is written each publication — Sonic principle). **Init vs
  incremental:** §11 vs §12.
- **Forbidden:** no 64-row tall compatibility projection, no C-window interpretation, no virtual name RAM, no
  modulo-folding of a PC080SN virtual dest, no changed-cell scanning.

## 11. Initial FG population
On stage/scene FG init (arcade `0x0503A0` selects the map source → `a5@0x10C6`/`0x10FC`; `FUN_000558e0/55904`
build `a5@0x10D000`), the native producer draws the **initially resident Plane-A window** (all visible columns
for the starting map position) into `staged_fg_buffer` + the collision ring from the arcade source descriptors
— the native equivalent of Sonic `LoadTilesFromStart`/`DrawChunks` and Rainbow's staged init. The existing
PC080SN blank-fill/full-window hooks (arcade `0x3AE80/0x3AF48` via `0x03AD44` FG-names fill) are **retired**
by this (they only cleared the C-window); a native resident-window draw replaces them. No full-plane rebuild
per frame.

## 12. Entering-edge producer (incremental)
One producer, invoked at the publication point (where `FUN_00055968/55990` were called). Per direction:
**PUBLICATION UNIT (proven — see the Sonic-1/publication-unit addendum, CASE B):** one arcade publication
event = **one complete entering column (selector 0) or row (selector≠0) = exactly 16 four-cell groups = 64
arcade FG cells.** This is the arcade's own `FUN_00055968`/`FUN_00055990` hardcoded `d1=0x10` (16) loop over
the 4-cell terminal writer `FUN_000559b2`/`FUN_00055a14` — NOT 4 cells, and NOT an expansion imported from
Sonic. The native producer's unit of work is exactly this 64-cell entering edge (what `FUN_00055968/55990`
did), mapped to the Genesis Plane-A height/width (the arcade FG plane is 64-tall; the exact Genesis
`staged_fg_buffer` row count is read at implementation, §24).
| Dir (a5@0x10D0) | Edge | Source | Cells/event | Plane-A dest | Writes |
|---|---|---|---|---|---|
| RIGHT (0x08) | entering vertical column (right) | descriptor for strip `a5@0x10CA`,group `a5@0x10CC` | 16×4 = 64 (arcade col) | wrapped X col from `a5@0x10AE` | staged_fg_buffer col + collision ring |
| LEFT (0x04) | entering vertical column (left) | ″ | 16×4 = 64 | wrapped X col (left edge) | ″ |
| DOWN (0x01) | entering horizontal row (bottom) | descriptor (row order) | 16×4 = 64 (arcade row) | wrapped Y row from `a5@0x10B0` | ″ |
| UP (0x02) | entering horizontal row (top) | ″ | 16×4 = 64 | wrapped Y row (top) | ″ |
Cells/ordering/selector-parity come from the arcade source descriptor + `a5@0x10CA`/selector exactly as
`FUN_000559b2/55a14` computed (source index `A2+0x20+strip*2+i*8`, `~idx&3` unless selector==2, `0xFF`-run →
`A2+0x22`). **The arcade advances the cursor** (`a5@0x10CA++` once per 64-cell publication, group/source
progression) — the producer does not invent a cursor. Tile/attr realized per §15; collision per §16.

## 13. Direction handling
Direction is read from `a5@0x10D0` (runtime-proven bit3=right for Stage 1); the producer branches on the same
bits the arcade directional publishers set. No new direction state.

## 14. Selector 0/1/2/4/5/6 handling
One producer consumes the arcade selector `a5@0x10A8` at runtime: selector 0 → column orientation
(`FUN_00055968` shape); 1/2/4/5/6 → row orientation (`FUN_00055990` shape) with parity `~idx&3` unless ==2.
**PROVEN STATIC:** the writer orientation for all six. **RUNTIME-CONFIRMED (Part 2B):** selector 0 only.
**REQUIRES VALIDATION ON REACHABLE STAGE:** 1/2/4/5/6 (vertical/alternate stages) and the `a5@0x10E8` role.
Because the producer is **data-driven by the arcade-owned selector/mode state** (it realizes whatever value is
present, using the same source-index math the arcade writers used), it does **not** need a higher-level label
for 4/5/6 to be correct — so the design does NOT invent 4/5/6 semantics. **The one design-blocking question:**
whether selector 4/5/6 change ONLY the source-index parity (already handled by `~idx&3`) or ALSO the
Plane-A dest orientation/geometry beyond row-vs-column. Part-2B could not reach 4/5/6. **Design position:** the
producer mirrors the exact arcade writer math (`FUN_00055a14`) which already encodes the 4/5/6 parity, so it
is expected correct; this MUST be validated on a 4/5/6 stage during implementation (Phase 13 E–I). This is a
validation obligation, not a guess — no invented behavior is added.

## 15. Tile / attribute realization
Retain (Category C, genuine data-format translation, not a virtual device): `genesistan_pc080sn_tile_vram_lut`
+ `pc080sn_attr_lut` + `pc080sn_tile_rom` (KF-014) — arcade tile identity → Genesis VRAM tile identity is a
static translation table that would exist even without PC080SN compatibility (the arcade tile codes must map
to Genesis VRAM slots regardless). The producer converts each source tile/attr word through this LUT into the
final Plane-A name word (tile index + palette/priority/flip attributes). No projection, no C-window.

## 16. Terrain collision-ring realization
The native producer reproduces the FG-exclusive collision contract: for each published cell it writes the
**descriptor collision word** (the same source word `FUN_000559b2/55a14` used) into the collision ring at
**arcade WRAM base `0x0010DE00`** (proven from the raw `FUN_000559b2` listing: `addi.l #0x0010DE00`; index =
`(dest − 0xC08000) >> 1`), i.e. the position derived from the FG scroll (`a5@0x10AE/0x10B0`) — the SAME ring
the consumers (`collision_map_lookup_53a2e`) index by actor position + FG scroll. Value `&0x7F`: 0=empty/passable,
1=floor/ground, 2=wall/solid. Blank/`0xFF`-run cells write the run value (passable/uniform). Visual and
collision writes stay synchronized because both are emitted in the same per-cell publication loop from the same
source. **BG/Plane-B is NOT made a terrain producer.** No second collision state machine; the producer realizes
the collision side effect that already belongs to the FG publication event.

## 17. Staging / VBlank contract
| Component | Class |
|---|---|
| `staged_fg_buffer` | **FINAL NATIVE** (target-shaped Plane-A shadow) |
| `staged_scroll_x/y_fg` + `vdp_commit_scroll` | **FINAL NATIVE** (KF-015) |
| `vdp_commit_fg_strips_if_dirty` / `vdp_commit_fg_narrow_strips` + FG dirty flags | **FINAL NATIVE if they accept the target shape** — audit obligation: confirm they commit `staged_fg_buffer` cells to Plane-A by row/column strips (they should); if any still encodes a C-window/PC080SN dest assumption, that part is **TRANSITIONAL** and must move to pure Plane-A geometry. |
| `genesistan_hook_tilemap_fg_fill` (C-window FG-names fill hook) | **OBSOLETE AFTER NATIVE FG** (replaced by §11 resident draw) |
| tile/attr LUT (KF-014) | **FINAL NATIVE** |
Structure mirrors the Rainbow principle (produce outside VBlank → target-shaped WRAM → bounded VBlank commit),
but **Rastan's arcade-owned VBlank remains authoritative** — no Rainbow scheduler/ownership imported.

## 18. PC080SN gameplay-FG retirement map
| Component | Producer | Consumer | Why it exists | Native replacement | Earliest safe retirement |
|---|---|---|---|---|---|
| `FUN_00055968`/`55990` selector writers | arcade `FUN_00055948` | `FUN_000559b2/55a14` | route to C-window writer | native producer | when native producer exists + all-selector validated |
| `FUN_000559b2`/`55a14` terminal writers | selector writers | C-window + collision | PC080SN name-word write | native producer (§12/16) | ″ |
| `a5@0x10A0/0x10A4` C-window dest compute | directional publishers | terminal writers | chip dest | native wrapped-plane compute | ″ |
| gameplay FG-names fill (`0x3AE80/0x3AF48` via `0x03AD44`) | stage init | C-window | blank/full FG fill | native resident draw (§11) | when §11 exists |
| `genesistan_hook_tilemap_fg_fill` | dispatch C-range | C-window | FG-names → staging | native resident/edge writes | ″ |
| gameplay FG descriptor-rebuild-for-C-window portions of `genesistan_hook_pc080sn_descriptor_rebuild` **iff** gameplay-FG-only | — | — | PC080SN realization | native (arcade rebuild stays) | verify not shared with BG/frontend first |
**Do NOT retire** frontend/text FG (inline writers, text writers, high-score FG) — they own separate Plane-A
content and are out of scope. The `0x03AD44` dispatch stays (BG/other C-range) per the PC080SN census handoff.

## 19. Transitional compatibility boundary
1. The native producer supports ALL statically-proven selectors/directions from its first implementation
   (data-driven by `a5@0x10A8`/`0x10D0`). 2. Once it exists, the gameplay-FG terminal writers + C-window dest
   + FG-names fill can be removed. 3. **No stage-specific retention** is designed: the producer handles every
   selector, so there is **no** "native for Stage 1, PC080SN for others" hybrid. 4. If, during validation,
   a 4/5/6 stage reveals a genuine unmodeled geometry difference (§14), that is a **bug to fix in the one
   producer**, not a reason to keep a second renderer. 5. No two competing gameplay-FG renderers are proposed.
**A stage-gated hybrid renderer is prohibited and not used.**

## 20. Validation matrix (for Build 0298+; no ROM here)
For each: ORIGINAL ARCADE MAME = Rastan semantic/visual truth; GENESIS NTSC MAME = candidate; manual/visual
where noted. A) Stage-1 sel-0 right (appearance, entering-column timing, scroll, collision) — arcade-reachable
(attract). B) left C) down D) up — need player input/stages. E–I) selectors 1/2/4/5/6 — on their stages.
J/K) pan-up/down. L) strip wrap M) group/page wrap N) stage init O) stage transition P) collision {standing
floor, landing, wall, enemy terrain, empty} Q) frontend→gameplay R) gameplay→frontend. **Stage-1 success is
NOT sufficient** to declare the subsystem complete (E–K explicitly required).

## 21. Future implementation slicing (build numbers, none consumed now)
- **Build 0298:** implement the one native Plane-A producer at the §7 cut (init resident draw §11 + entering-
  edge §12 + tile/attr §15 + collision §16), writing `staged_fg_buffer` + collision ring; the retained arcade
  state machine calls it in place of `FUN_00055968/55990`. Validate Stage-1 (attract) A/L/M/N + collision P.
  **Do not** retire the PC080SN FG tail yet (keep it inert/unreached or behind the same call site) until
  validated.
- **Build 0299:** broaden validation to reachable directions/stages (B–K as reachable) via input-driven
  ARCADE-vs-GENESIS comparison; fix the one producer for any selector 1/2/4/5/6 geometry difference.
- **Build 0300:** retire the now-obsolete gameplay-FG PC080SN tail (§18) once all reachable cases validate;
  final zero-debt FG audit.
Prefer "one producer complete → retire tail → broaden validation → retire remaining isolated compat" over
per-stage patches (which would recreate the compatibility architecture). Exactly one sequential number per ROM.

## 22. Open/Closed Issues impact
OPEN-001/018 (native FG/map): this design provides the single-producer plan. OPEN-017 (FG/collision): the
collision-ring realization is specified. None closed (design only). No new issue (the §14 4/5/6-geometry
validation obligation is tracked as a Build-0299 validation item, not a defect).

## 23. KNOWN_FINDINGS impact
**Option A — No new finding to index.** This design consumes existing STRONG findings (KF-010/014/015/011) and
the Part-2 FG-collision fact (already proposed there); no new system-behavior fact emerged.

## 24. Remaining uncertainties
- Whether `vdp_commit_fg_strips_if_dirty`/`_narrow_strips` already accept pure Plane-A geometry or still carry
  a C-window assumption (Build-0298 audit obligation, §17).
- Selector 4/5/6 Plane-A geometry beyond source parity (§14) — validation obligation on a reachable 4/5/6
  stage (not a design guess).
- Exact `staged_fg_buffer` height/plane-size register value (read from `vdp_comm.s` at implementation).
- Whether `genesistan_hook_pc080sn_descriptor_rebuild` is gameplay-FG-only or shared (verify before retiring).

## 25. Final architecture (target)
```
arcade FG semantic decision (stage/map, direction, movement, accumulators,
  strip/group/page cursor, source table, selector/mode, FG scroll)   [ARCADE — unchanged]
        │  (arcade calls the native producer at the former FUN_00055968/55990 point)
        ▼
one native Genesis Plane-A producer  [replaces FUN_00055968/55990/559b2/55a14 + C-window dest]
   ├─ init: draw resident Plane-A window from arcade source descriptors
   └─ incremental: write the entering column/row (wrapped Plane-A) from arcade strip/group/scroll
        ├──▶ staged_fg_buffer (target-shaped Plane-A shadow; tile/attr via KF-014 LUT)
        └──▶ terrain collision ring (descriptor word; &0x7F = floor/wall/empty; FG-exclusive)
        ▼
existing FG strip commit + scroll commit  [FINAL NATIVE, KF-015]
        ▼
arcade-owned Level-5 VBlank commit  [ARCADE — unchanged, KF-011]
        ▼
Genesis VDP Plane A
```

---

**Rastan arcade FG semantic authority preserved: YES.**
**Rainbow Islands structural comparison completed: YES.**
**Sonic 1 structural comparison completed: YES** (from established knowledge; the Sonic-1 68k disassembly is
NOT in-repo — stated in §2/§5; Rastan remains authority, no Sonic structures copied).
**Native design depends on Rainbow-specific game logic: NO.**
**Native design depends on Sonic-specific game logic/map format: NO.**
**Native Plane-A geometry fully specified: YES** (modulo the exact plane-height constant, read at impl).
**Initial FG population fully specified: YES.**
**Incremental entering-edge publication fully specified: YES.**
**All selectors accounted for in design: YES** (data-driven; 4/5/6 Plane-A geometry carries a validation
obligation, not an invented behavior).
**Terrain collision side effect fully specified: YES.**
**Final-form staging/VBlank contract identified: YES** (one audit obligation on the FG strip-commit shape).
**PC080SN gameplay-FG retirement boundary fully specified: YES.**
**Stage-specific hybrid renderer required: NO.**
**Ready for implementation prompt starting Build 0298: YES** — with the two Build-0298 audit obligations (FG
strip-commit shape; descriptor-rebuild sharing) and the 4/5/6 validation obligation explicitly carried
forward, none of which blocks starting the single-producer implementation.
