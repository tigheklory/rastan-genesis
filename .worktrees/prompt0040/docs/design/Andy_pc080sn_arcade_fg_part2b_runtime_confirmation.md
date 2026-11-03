# Andy — Arcade FG Decompile Part 2B: Runtime Confirmation

**Type:** Analysis / verification. **Production changes: NONE. ROM: NONE.** Accepted baseline: Build 0297.
Method: ORIGINAL ARCADE Rastan MAME (machine `rastan`, `roms/rastan.zip`), headless attract (the demo plays
Stage-1 gameplay), sampling arcade WRAM each frame via a read-only Lua
(`tools/mame/scripts/fg_state_sampler.lua`) — no production/ROM change. Two runs: 150s (9001 frames) + 110s
(6601 frames).

## 1. Phase-0 baseline
- **Relevant priors:** KF-015 (full-plane scroll, no per-line) — Confidence STRONG; applies (X scroll
  decrements per published column). KF-014 (tile LUT) — STRONG. KF-010 (FG→Plane A) — STRONG. KF-011 (arcade
  VBlank owns progression) — STRONG; applies (arcade state machine drives publication).
- **Rediscovery-Hazard HIGH touched:** KF-011 (respected — no Genesis lifecycle proposed).
- **Deferred-appendix entries relevant:** None.
- **Task classification:** EXTENDING (runtime confirmation of the Part-2 static FG model).
- **Open/Closed issues touched:** OPEN-017 (FG/collision progression) — evidence added, not closed.
  OPEN-001/018 (native map/FG) — context.
- **Contradiction of CONFIRMED/STRONG finding:** NONE. (One refinement of the *task's own* Part-2 note about
  a5@0x10E8; that is not a KNOWN_FINDINGS entry.)

## 2–3. Environment & sampled fields
Arcade a5 = 0x0010C000; FG state block at 0x0010D0xx. Sampled (each frame): selector `a5@0x10A8`
(0x0010D0A8), strip `a5@0x10CA` (0x0010D0CA), group `a5@0x10CC` (0x0010D0CC), direction bitmask `a5@0x10D0`
(0x0010D0D0), Y accum `a5@0x10BA`, X accum `a5@0x10B8`, FG X scroll `a5@0x10AE`, FG Y scroll `a5@0x10B0`,
mode `a5@0x10E8`, stage `a5@0x13E`, page ptr `a5@0x10C6`. All `arcade_WRAM`.

## 4. Selector observations
**OBSERVATION:** `a5@0x10A8` = **0** for all 9001 + 6601 sampled frames. Values 1/2/4/5/6 never observed.
**STATIC CORRELATION:** Stage-1 is the horizontal-scroll stage; `FUN_00055948` routes selector==0 →
`FUN_00055968` (the vertical-column writer). **INTERPRETATION:** selector 0 = the horizontal-scroll-stage
FG mode (publishes vertical columns as the map scrolls right). Selectors 1/2/4/5/6 belong to other
stages/axes not exercised by the Stage-1 attract demo.

## 5. Selector 0/1/2 analysis
Only **selector 0** was reachable. Its behavior is fully consistent with the static model (§7 below). 1/2
(vertical-scroll row publication) were NOT reached at runtime; they remain static-understood
(`FUN_00055990`→`FUN_00055a14`, row stride 2, parity `~idx&3` unless ==2).

## 6–7. Selector 4/5/6 + a5@0x10E8 analysis
**Selector 4/5/6 runtime coverage: NOT REACHED** (attract is Stage-1 only). Therefore the static branch
`FUN_00052732: if (0x10A8 ∈ {4,5,6}) a5@0x10E8 = 7` was **not exercised**.
**OBSERVATION:** `a5@0x10E8` varied across {0,1,2,3,4,5,6,8} during selector-0 Stage-1 play (rapid changes).
**INTERPRETATION:** `a5@0x10E8` is written by *other* Stage-1 code as well; it is NOT a stable
"selector-4/5/6 traversal mode" during Stage-1. Its `=7` role for selectors 4/5/6 is **UNCONFIRMED** (not
contradicted) — it can only be verified when a 4/5/6 stage runs (not available in attract). This refines,
but does not contradict, the Part-2 note.

## 8. (folded into §6)

## 9. Accumulator observations — X threshold PROVEN
**OBSERVATION (110s run, dozens of consecutive strip advances):** at EVERY publication event the direction
bitmask `a5@0x10D0 = 0x08` (bit 3) and the X accumulator `a5@0x10B8 = 160 = 0xA0`; `a5@0x10AE` (FG X scroll)
decremented by exactly **8** per published strip (216→208→…→15); `a5@0x10BA` (Y accum) constant (73), FG Y
scroll constant (329).
**STATIC CORRELATION:** `FUN_000557ba` (right/X+ publisher): `if (a5@0x10B8 < 0xA0) accumulate; else publish
+ a5@0x10AE -= delta`. Direction bit 3 = right.
**INTERPRETATION:** the **X strip-accumulator threshold is exactly 0xA0** (publication fires as it reaches
0xA0), each publication emits one tile column and advances FG X scroll by one tile (8 px) — exactly the
static model and KF-015 (full-plane scroll). The Y threshold (0x100) was **not exercised** (no vertical
scroll in the sampled horizontal segment; Y accum stayed 73), so the Y threshold is confirmed by symmetry
of the static code but not directly observed.

## 10. Strip / group / page observations — PROVEN
**OBSERVATION:** strip `a5@0x10CA` transitions `0→1 (93), 1→2 (91), 2→3 (91), 3→0 (92)` — a clean
0→1→2→3→wrap cycle; group `a5@0x10CC` ranged 0..15 and wrapped `15→0`. (Rare 1-count anomalies 0→2/1→3 at
page/init boundaries, negligible.) Group sometimes advanced by 2 between per-frame samples during fast
initial fill (two publications in one frame).
**STATIC CORRELATION:** `FUN_00055948` (strip++), `FUN_000558a2` (at strip==4 → advance source/rebuild,
group++; at group==0x10 → page wrap `FUN_000558e0`).
**INTERPRETATION:** strip index wraps at 4 and group/page wraps at 0x10 exactly as decompiled. CONFIRMED.

## 11. Source-table timing
**OBSERVATION:** group advance (→ source-pointer advance `FUN_000558c6` + descriptor rebuild `FUN_00055904`)
occurred once per completed 4-strip cycle, with a full 0→15 page walk during the initial stage fill
(frames ~2575–2587) and slower single-step advances during scrolling gameplay (correlated with FG scroll
change). **INTERPRETATION:** source-pointer advancement/rebuild timing matches the static model (per-4-strip
group step; per-16-group page wrap). CONFIRMED (timing), consistent.

## 12. Pan-up / pan-down
**NOT REACHED.** Stage-1 attract scrolled horizontally (direction bit 3 only; Y accum/scroll constant), so
the vertical pan boundaries `arcade_pc 0x055704` (down) / `0x055790` (up) did not trigger. Left (bit 2) and
up/down (bits 0/1) publication were not observed. These remain static-understood; runtime confirmation
requires a vertical-scroll stage (not in attract).

## 13. Observation vs interpretation
All numeric captures in §4–§11 are OBSERVED (arcade MAME); INTERPRETATION is separated inline and follows
directly from the decompiled routines. No intent/causality is asserted as observation.

## 14. Static-vs-runtime comparison
| Model item | Static (Part 2) | Runtime | Verdict |
|---|---|---|---|
| Selector 0 = Stage-1 horizontal, column publish | predicted | selector=0, dir=0x08, column stride | CONFIRMED |
| X accumulator threshold | 0xA0 | 0xA0 exactly at every publish | CONFIRMED |
| FG X scroll per publish | −1 tile | −8 px per column | CONFIRMED |
| Strip index wrap | at 4 | 0→1→2→3→0 | CONFIRMED |
| Group/page wrap | at 0x10 | 0..15→0 | CONFIRMED |
| Source advance/rebuild timing | per-4-strip / per-16-group | matches | CONFIRMED |
| Selector 1/2 (vertical row publish) | static | not reached | UNVERIFIED (static-only) |
| Selector 4/5/6 + a5@0x10E8=7 mode | static hypothesis | not reached; 0x10E8 has other Stage-1 uses | UNCONFIRMED (refined) |
| Y accumulator threshold 0x100 | static | not reached (no vertical scroll) | UNVERIFIED (static-only) |
| Pan-up/down 0x55704/0x55790 | static | not reached | UNVERIFIED (static-only) |
| Terrain-collision contract (Part 2 §10-12) | static-proven | not re-tested here | unchanged (not reopened) |

**Static FG model materially contradicted: NO.** Runtime confirms every reachable prediction and refines
only the a5@0x10E8 field-usage note (which was a Part-2 caveat, not a KNOWN_FINDINGS entry).

## 15. Semantic cut / future chip-tail (policy §)
- **Semantic cut retained above chip execution:** `arcade_pc FUN_00055650` — arcade keeps the FG state
  machine (direction 0x10D0, accumulators, strip/group cursor, source table 0x10D000 / page ptr 0x10C6,
  selector 0x10A8, scroll regs 0x10AE/0x10B0) and the terrain-collision semantics as input.
- **Chip-specific tail to remove (future):** the PC080SN C-window destination/publication path culminating
  in `arcade_pc FUN_000559b2` / `FUN_00055a14` (the terminal C-window writes), plus associated compatibility
  routing, once the native Plane-A producer replaces it. The native producer must write staged_fg_buffer AND
  the terrain collision ring (value = descriptor word, `&0x7F` terrain, ring geometry via FG scroll).
- **Transitional compatibility retained:** the existing Build-0297 PC080SN FG path is **unchanged** in this
  analysis task. Removal boundary = when the native Plane-A producer exists at the FUN_00055650 cut.
- **Policy §9 checklist:** (1) semantic decision retained: arcade FG state machine — YES; (2) chip tail
  removed: none removed here (analysis only); future = FUN_000559b2/55a14 C-window writes; (3) transitional
  compatibility: entire current PC080SN FG path, untouched, removed at the native cut. **No implementation is
  authorized by this task.**

## 16. Open/Closed Issues impact
OPEN-017: runtime evidence added confirming the FG state-machine progression (strip/group/threshold);
terrain-collision contract unaffected. Not closed. No new issue opened (no defect found). No issue closed.

## 17. KNOWN_FINDINGS impact
**Option A — No new finding to index.** Rationale: this task confirms (does not refine) the existing STRONG
scroll/tilemap findings (KF-015/KF-014/KF-010) and the Part-2 static FG model; the design-relevant new
system-behavior fact (FG terminal writers own the terrain collision map) was already proposed as a finding
in Part 2 and is unchanged here.

## 18. Remaining uncertainty
Selector 1/2/4/5/6 and the a5@0x10E8=7 mode; the Y accumulator 0x100 threshold; pan-up/down boundaries —
all require a vertical-scroll / alternate stage not reachable in Stage-1 attract. These are **static-
understood and design-sufficient** (the native producer at FUN_00055650 reads the arcade state at runtime and
realizes whatever selector/direction is present); they should be validated on the native build when those
stages run — a build-time validation, not a design blocker.

---

**Selector runtime semantics verified: PARTIAL** — selector 0 (Stage-1 horizontal) fully confirmed; 1/2/4/5/6
NOT REACHED in attract.
**Selector 4/5/6 mode verified: NOT REACHED.**
**Accumulator thresholds verified: YES** for X (0xA0 confirmed exactly per publication) + per-column −8px
scroll; Y threshold (0x100) not reached (static-only).
**Strip-index timing verified: YES** (0→1→2→3→0).
**Group/page timing verified: YES** (0..15 wrap at 0x10).
**Static FG model materially contradicted: NO.**
**Ready for native FG design: YES** — the primary gameplay-FG state machine is runtime-confirmed; the
alternate selectors/pan paths are static-understood and realized at runtime by the arcade state the native
producer reads, to be validated on their stages during implementation.
