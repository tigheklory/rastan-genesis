# Andy — Native FG Design Addendum: Sonic-1 Source Verification + Rastan Publication Unit

**Type:** Analysis / verification / design. **No code, no ROM, no Build 0298 consumed.** Baseline: Build 0297.
Closes two pre-Build-0298 questions: (1) replace "established Sonic-1 knowledge" with direct s1disasm source
evidence; (2) prove Rastan's exact FG publication unit (4 cells vs a complete entering edge).

## 1. Phase-0 baseline
- **Relevant priors:** KF-010 (FG→Plane A), KF-014 (tile LUT), KF-015 (full-plane scroll +8), KF-011 (arcade
  VBlank owns progression) — all STRONG, all apply.
- **Rediscovery-Hazard HIGH:** KF-011 (respected).
- **Deferred appendix:** none relevant.
- **Task classification:** EXTENDING (verifies/refines the existing native FG design).
- **Open/Closed issues touched:** OPEN-017 (FG/collision — collision base pinned), OPEN-001/018 (native FG).
- **Contradiction of CONFIRMED/STRONG finding:** NONE.

## 2. Scope
Verify Sonic-1 structural technique from primary source; prove Rastan's terminal-writer call cardinality and
the exact cells per semantic publication; correct the native FG design if it over-/under-expands the unit.

## 3. Sonic-1 repository / source provenance
- Repository: `sonicretro/s1disasm`; branch/ref: **AS**; file:
  `_inc/Level Drawing (REV00).asm` (fetched read-only via
  `https://raw.githubusercontent.com/sonicretro/s1disasm/AS/_inc/Level%20Drawing%20(REV00).asm`).
- Not the RSDK 2013 decomp; not the SGDK Sonic sample. No vendor files added to the Rastan repo.

## 4. Sonic-1 source routines inspected
`LoadTilesAsYouMove`, `DrawBlocks_LR`, `DrawBlocks_TB`, `Calc_VRAM_Pos`, `LoadTilesFromStart`, `DrawChunks`.

## 5. Sonic-1 source-backed findings (with source citations)
- **Flag-gated incremental draw:** `LoadTilesAsYouMove` tests `tst.b (a2); beq.s .return` then `bclr #0..#3,
  (a2)` for top/bottom/left/right edges — **no plane work when no edge flag is set** (Sonic claim A verified;
  B/C/D/E verified: each direction bit draws its exposed edge).
- **DrawBlocks_TB = vertical column** (`moveq #((224+16+16)/16)-1,d6` = 16 blocks; `addi.w #16,d4` step Y) —
  drawn on **horizontal** camera movement. **DrawBlocks_LR = horizontal row** (`moveq #((320+16+16)/16)-1,d6`
  = 22 blocks; `addi.w #16,d5` step X) — drawn on **vertical** movement.
- **Block = 4 name-table cells** (16×16 = 2×2 tiles; per-block advance `addq.b #4,d1` / `addi.w #$100,d1`).
- **Calc_VRAM_Pos = direct wrapped VRAM address** (`andi.w #$F0,d4; andi.w #$1F0,d5; lsl.w #4,d4; lsr.w #2,d5;
  add.w d5,d4`) → a **64×32** wrapped plane, no virtual map (claim F verified).
- **Init separate** (`LoadTilesFromStart`/`DrawChunks` full-screen load) vs incremental `LoadTilesAsYouMove`
  (claim G verified).

## 6. Sonic-1 exact publication unit
Per 16-px block boundary, **one entering edge**: vertical column = 16 blocks × 4 = **64 cells**; horizontal
row = 22 blocks × 4 = **88 cells**. Occurs when the corresponding edge flag is set (camera crossed a 16-px
boundary). **This is Sonic's unit; it is NOT imported into Rastan** — used only to confirm the structural
technique (flag-gated, entering-edge-only, wrapped direct addressing).

## 7. Rastan publication call graph (proven from `full_listing.tsv`)
```
FUN_00055650 (direction dispatch on a5@0x10D0)
 └─ FUN_000557ba (RIGHT, Stage-1) ── on X-accum == 0xA0 ──▶ FUN_00055948
      FUN_00055948: if a5@0x10A8==0 → FUN_00055968 ; else → FUN_00055990 ; then a5@0x10CA++ ; FUN_000558a2
        FUN_00055968 (selector 0):  move.w #0x10,d1 ; .loop bsr FUN_000559b2 ; a5@0x10A0=a0 ;
                                    addq.l #4,a3 ; addq.l #2,a1 ; subq.w #1,d1 ; bne .loop ; rts   ← 16 iterations
          FUN_000559b2 (terminal):  clr.w d2 ; .loop write tile→(a0), collision→(0x10DE00+((a0-0xC08000)>>1)),
                                    attr→(a0)+... ; addq.w #1,d2 ; cmpi.w #4,d2 ; bne .loop ; rts  ← 4 cells
        FUN_00055990 (selector≠0):  moveq #0x10,d1 ; .loop bsr FUN_00055a14 ; ... subq.w #1,d1 ; bne ; rts  ← 16
          FUN_00055a14 (terminal):  4-cell loop (row stride, parity ~idx&3 unless ==2)
```

## 8. Rastan exact terminal-writer cardinality — PROVEN
Per one semantic publication (one `FUN_00055948` call): the selector writer (`FUN_00055968` or
`FUN_00055990`) calls the 4-cell terminal writer (`FUN_000559b2`/`FUN_00055a14`) **exactly 16 times**
(`d1 = 0x10`, `subq #1,d1; bne`). Each terminal writer writes **4 cells** (`d2` 0→4). Therefore **16 × 4 =
64 visual FG cells are written before control returns** to the retained arcade state machine. (The earlier
Ghidra decompiler `while (extraout_D1w != 1)` rendering was a mis-decompilation of the `moveq #0x10,d1 …
subq/bne` counted loop — corrected here from the raw listing.)

## 9. Rastan exact publication unit — CASE B
**CASE B — COMPLETE ENTERING EDGE IS THE SEMANTIC UNIT.** One arcade publication event emits **one complete
entering column (selector 0) or row (selector≠0) = 64 cells**, then returns. It is NOT 4 cells (CASE A), and
not another unit (CASE C). The native producer must realize this same complete 64-cell entering edge per
publication.

## 10. Strip / group / page relationship
- One publication = one 64-cell column/row = one **strip**; `a5@0x10CA` advances **once per 64-cell
  publication** (0→3, wrap 4).
- 4 strips = one **group**; `a5@0x10CC` advances every 4 strips (via `FUN_000558a2`), wraps at 0x10.
- 16 groups = one page; `FUN_000558e0` on page wrap reloads source + selector.
- The strip index (0..3) selects the sub-column within the current group's descriptor (used in the terminal
  writer's source-index math `strip*2 + i*8`); the 16-iteration loop walks the 16 descriptor entries
  (`a3 += 4`, `a1 += 2` per iteration) that compose the full 64-cell column.

## 11. Stage-1 runtime correlation (Part 2B)
Part 2B `xacc(0x10B8)=0xA0`, `dir=0x08`, `FG X scroll −8`, `a5@0x10CA++` per publication now resolves cleanly:
each 0xA0 X-accumulator crossing triggers **one** `FUN_00055948` = **one 64-cell entering column** + one
strip advance + one 8-px (one tile) FG-X-scroll step. The per-frame sampler could not see the 16 terminal
calls inside one frame's publication; the static call graph proves them. No contradiction — the runtime
scroll/strip cadence is exactly one 64-cell column per tile-column of scroll.

## 12. Sonic-vs-Rastan comparison
| Property | Sonic 1 | Rastan arcade | Transferable lesson | Must NOT copy |
|---|---|---|---|---|
| Movement boundary | 16-px block | tile boundary (X-accum 0xA0 / Y 0x100) | boundary-triggered publish | Sonic's 16-px unit |
| Publication trigger | edge flag bit | direction bit `a5@0x10D0` + accumulator | flag/boundary gate | Sonic flag layout |
| Publication unit | 64 (col) / 88 (row) cells | **64 cells** (col & row) | full entering edge per event | Sonic's 88 / block fmt |
| Horizontal-scroll update | DrawBlocks_TB column | FUN_00055968 column (16×4) | entering column | Sonic camera/blocks |
| Vertical-scroll update | DrawBlocks_LR row | FUN_00055990 row (16×4) | entering row | ″ |
| Dest calc | Calc_VRAM_Pos mask 64×32 | native wrap from arcade scroll/pos | direct wrapped address | Sonic plane dims/masks |
| Wrapping | mask $F0/$1F0 | mask Genesis Plane-A dims | power-of-two mask | Sonic exact masks |
| Initial resident draw | LoadTilesFromStart/DrawChunks | arcade source init (0x503A0) + native resident draw | separate init path | Sonic chunk fmt |
| Source/map ownership | Sonic level data | Rastan `a5@0x10D000`/descriptors | game keeps map | Sonic level structs |
| Cursor ownership | Sonic camera | Rastan strip/group/page (`FUN_000558a2/…`) | game keeps cursor | Sonic camera |
| Collision side effect | (none in this path) | Rastan `0x10DE00` ring, `&0x7F` | Rastan-unique | — |
| VBlank relationship | Sonic VBlank commit | **arcade-owned** VBlank | commit-only | Sonic VBlank ownership |
**Conclusion:** Sonic's structural lesson (direct wrapped entering-edge publication, no unchanged-cell work,
no virtual map) is adopted; Sonic's publication *quantity* (88-cell row / 16-px unit / 64×32 masks) is NOT —
Rastan's unit is its own proven **64 cells per column/row** from `FUN_00055968/55990`.

## 13. Publication-unit verdict
**CASE B** — one complete entering column/row (**64 cells = 16 × 4**) per arcade publication event.

## 14. Impact on the existing native FG design
The design's full-column/row model was **correct** (CASE B); it did **not** shrink the unit to 4 cells. The
only ambiguity was the wording "4-tile column × plane-height/4," which could be misread. Corrected to the
exact arcade cardinality (16×4=64) and the proven collision base.

## 15. Exact corrections made to `Andy_native_genesis_fg_plane_a_design.md`
- **§12:** added an explicit "PUBLICATION UNIT (proven, CASE B): 64 cells = 16 four-cell groups per event"
  statement; the per-direction table "cells" column changed from "4-tile column ×(plane height/4)" to
  "16×4 = 64"; cursor note clarified to "once per 64-cell publication."
- **§16:** collision ring base pinned to **`0x0010DE00`** with the proven index `(dest−0xC08000)>>1`.
- **§5:** Sonic reference marked source-verified against s1disasm AS `_inc/Level Drawing (REV00).asm` with
  the specific routine/mask citations.
No other sections changed; design history preserved.

## 16. Semantic-cut revalidation
**Unchanged.** The cut still replaces `FUN_00055968` / `FUN_00055990` (the 16× loops) + `FUN_000559b2` /
`FUN_00055a14` (the 4-cell terminals) + the `a5@0x10A0/0x10A4 = 0xC08000+geometry` dest computation, with the
arcade retaining `FUN_00055650`, the directional publishers, `FUN_00055948` (dispatch/strip++), and
`FUN_000558a2/558c6/55904/558e0`. The publication-unit proof does not move the cut — it confirms the native
producer's unit of work at that cut is the 64-cell entering edge (exactly what `FUN_00055968/55990` produced).

## 17. Build-0298 readiness
The publication contract is now unambiguous: per arcade FG publication event, the native producer emits one
complete entering column/row of 64 cells (16 groups × 4), reading the arcade descriptor/strip/selector/scroll
state, writing `staged_fg_buffer` + the `0x10DE00` collision ring, while the arcade advances the cursor.

## 18. Open/Closed Issues impact
OPEN-017: collision base pinned (`0x0010DE00`) — evidence added, not closed. OPEN-001/018: publication unit
resolved for the native FG design. No issue closed; no new issue (the 4/5/6 geometry validation remains a
Build-0299 obligation).

## 19. KNOWN_FINDINGS impact
**Option A — No new finding to index.** This confirms/refines the existing design and STRONG findings; the
FG-owns-collision fact was already proposed in the Part-2 decompile. (The `0x10DE00` base and the 64-cell unit
are design-record details, not new durable system-behavior findings warranting a KF entry.)

## 20. Remaining uncertainty
- Exact Genesis `staged_fg_buffer` plane-size (64×32 vs 64×64) — read at implementation; determines how many
  of the arcade's 64 column rows map to the Genesis plane.
- Selector 4/5/6 Plane-A geometry beyond source parity (Build-0299 validation obligation).
- FG strip-commit shape audit (Build-0298).
None block the Build-0298 single-producer implementation.

---

**Sonic 1 original 68000 source directly inspected: YES.**
**Sonic incremental drawing behavior source-verified: YES.**
**Sonic wrapped name-table addressing source-verified: YES.**
**Rastan terminal-writer call cardinality proven: YES** (16 calls per publication).
**Rastan exact cells per semantic publication proven: YES** (64 = 16 × 4).
**Rastan complete-edge composition proven: YES** (CASE B).
**Native producer publication unit unambiguous: YES.**
**Current FG design corrected if required: YES** (§5/§12/§16 wording pinned; architecture unchanged).
**Semantic cut revalidated: YES** (unchanged).
**Ready for Build 0298 implementation prompt: YES.**
