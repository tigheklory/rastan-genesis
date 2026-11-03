# Andy — Build 0159: Collision Buffer WRAM Rebase (0x0010DE00 → 0x00FF1E00) — STOP, NO BUILD

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `48a3278`, clean (only gitignored MAME trace churn). Accepted Build 0158
ROM `2bf5a06fd5d8ea759c4a9c1c82ce00c34257f338bcaee42d64de9093f17e23ab`, counter 158. **No source/spec/tool/ROM
edit, no build** (STOP reached at the pre-build runtime gate). KNOWN_FINDINGS touched: KF-039/KF-036 (raw
WRAM-literal class), KF-040/KF-041 (pipeline step present but does not run on Genesis). OPEN issue: OPEN-017.

## 2. Address mapping method
`build/rastan-direct/address_map.json`: `relocation_delta = 0x000200`, arcade_source `[0,0x60000)`, arcade_copy
at Genesis `+0x200`. Each Genesis site's arcade PC = Genesis−0x200, confirmed against `build/maincpu.disasm.txt`
(bytes match at every site, §3). A5 WRAM: arcade `0x0010C000` → Genesis `0x00FF0000` (KF-039), so the collision
buffer `0x0010DE00` → `0x00FF1E00`.

## 3. Verified site table
All 9 raw `0x0010DE00` literal sites (exhaustive — Python scan of long-immediate WRAM literals found no others,
and confirmed the buffer is a single 0x2000-byte region [0x10DE00,0x10FE00) via the wrap-checks in the compares):

| Genesis PC | arcade PC | original bytes | instr | role |
|---|---|---|---|---|
| 0x53C64 | 0x53A64 | `207C0010DE00` | `moveal #imm,a0` | reader base (dispatch lookup 0x53C2E) |
| 0x5A4CE | 0x5A2CE | `06800010DE00` | `addil #imm,d0` | reader (base+index, reads cell, btst #7) |
| 0x55BE4 | 0x559E4 | `06870010DE00` | `addil #imm,d7` | producer (→ `moveal d7,fp; movew d0,fp@`) |
| 0x55C5A | 0x55A5A | `06870010DE00` | `addil #imm,d7` | producer |
| 0x55C7A | 0x55A7A | `06870010DE00` | `addil #imm,d7` | producer (neighbor cell) |
| 0x52A82 | 0x52882 | `06800010DE00` | `addil #imm,d0` | converter VRAM→buffer: `buf = 0x10DE00 + (vram−0xC08000)/2` |
| 0x5A536 | 0x5A336 | `04800010DE00` | `subil #imm,d0` | converter buffer→VRAM: `vram = 0xC08000 + (buf−0x10DE00)*2` |
| 0x414E8 | 0x412E8 | `B1FC0010DE00` | `cmpal #imm,a0` | bounds-wrap: `a0−=0x80; if a0<0x10DE00: a0+=0x2000` |
| 0x45F52 | 0x45D52 | `B1FC0010DE00` | `cmpal #imm,a0` | bounds-wrap (same) |

Rebase (each byte-neutral, 6→6): immediate `0010DE00` → `00FF1E00`. The `0x00C08000` (FG-plane VRAM) term in
the two converters is the VRAM side and is deliberately NOT touched. Target WRAM window `0xFF1E00..0xFF3E00` is
**free of helper symbols** (helper slots are ≤0xFF1104 or ≥0xFF4000 per `out/symbol.txt`).

## 4. Included sites
None applied — STOP before any edit. Had the build proceeded, all 9 sites above would move together (a
reader-only rebase is unsafe; the compares and converters must stay consistent with the buffer base).

## 5. Excluded sites and why
None excluded on static grounds — the two `cmpal` compares and both converters ARE part of this one buffer
(the wrap-check +0x2000 defines the buffer size; the converters map buffer↔FG-VRAM 1:1). The set is complete
and coherent. The blocker is not the site set — it is runtime production (§9).

## 6. State-causality answers
1. **What state should exist?** A collision map produced into Genesis WRAM `0x00FF1E00`, read by the dispatch
   lookup `0x00FF1E00 + index`; type-8 should come from a real map, not ROM.
2. **Which earlier code should create it?** The producer stores at Genesis `0x55BEC / 0x55C62 / 0x55C82`
   (`movew d0,fp@`, fp = `0x10DE00 + (vram−0xC08000)/2`), fed by the FG tilemap population.
3. **Why does that state not exist?** **Not** "producers write to ROM and the write is dropped" (the prior
   analysis' hypothesis). Runtime proof (§9): the producer store instructions **never execute** on Genesis in
   an entire boot→gameplay run — the collision-map producer routine is **dead** on Genesis (KF-040 class). The
   reader therefore consumes **static ROM graphics data** left at `0x10DExx`, not dropped writes. WRAM
   `0x00FF1E00` is empty because nothing ever writes it.

**Classification: C (site set complete but the rebase is UNSAFE) — with a D correction to prior analysis.**
Because the producer path is dead, rebasing the reader to `0x00FF1E00` reads an **empty** buffer (all type-0 =
no collision), and rebasing the producers changes nothing (they never run). The coordinated rebase would
**remove collision entirely** (player would have no floor/hazard detection) — strictly worse than the current
spurious type-8. This trips the explicit STOP condition "runtime validation cannot prove WRAM production." **A
and B are NOT satisfied → no implementation.**

## 7. Exact opcode/spec changes
**NONE.** No `opcode_replace` entries added; `CANONICAL_OPCODE_REPLACE_COUNT` stays 136;
`CANONICAL_TOTAL_GENESIS_BYTES_COVERED` stays 0x182070; spec `expectations.opcode_replace_count` stays 136.

## 8. Static validation
Site set verified byte-exact against `maincpu.disasm.txt` (§3); target WRAM window free (§3); buffer proven to
be one 0x2000-byte region. All preconditions for a *static* rebase were met — the block is purely runtime.

## 9. Runtime producer proof (the STOP evidence)
`states/traces/build_0159_collision_rebase/`:
- `gen_producer_probe.txt`: a write-tap on the whole buffer range `0x0010DE00..0x0010FDFF` for a full
  boot→coin→start→gameplay run (F=0..840) recorded **zero write attempts** ("first write-attempt … at F=nil").
  On the arcade this range is written continuously; on Genesis it is never touched.
- `gen_producer_exec.txt`: a full-address-space write-tap filtered to the producer store PCs
  `0x55BEC/0x55C62/0x55C82` recorded **"NEVER executed (routine dead on Genesis)."**
Conclusion: the collision-map producer pipeline does not run on Genesis; WRAM `0x00FF1E00` cannot be populated
by rebasing.

## 10. Runtime reader proof
From the prior origin analysis (`Andy_build0159_floor_collision_map_origin.md`): at F=698 the reader dispatch
loads `A0=0x0010F20A` (ROM), `*(A0)=0x1888` (`&0x7F=8`) → spurious type-8 → `mode=0x0008`. The reader consumes
static ROM content; it does not read a produced map. (Reader consumption of `0x00FF1E00` was never established
because that buffer is empty.)

## 11. Early type-8 before/after
No build → no "after." Before (Build 0158): spurious type-8 at F≈698 from ROM `0x0010F20A`. A rebase would
replace it with type-0 from empty `0x00FF1E00` (no collision), not the arcade map — not an acceptable "after."

## 12. 2/3/0 duration before/after
No build. Before: Genesis 2/3/0 ≈ 313 frames vs arcade ≈ 588. A rebase would not restore the arcade duration
(the map would be empty, changing behavior unpredictably, likely removing floor collision).

## 13. Visible validation
Not run (no build).

## 14. Regression validation
Not run (no build). No accepted build was modified; Builds 0142–0158 untouched; canonical constants unchanged.

## 15. Open/Closed Issues Impact
OPEN-017 advanced (and prior root-cause refined): the collision-map buffer at arcade WRAM `0x0010DE00` is not
just un-rebased — its **producer pipeline is dead on Genesis** (stores `0x55BEC/0x55C62/0x55C82` never run), so
the buffer is never built in WRAM and the reader consumes static ROM graphics data (spurious type-8). A
literal-only rebase is therefore **unsafe** (empty target removes collision). The real fix must make the
collision-map producer path run/populate on Genesis (KF-040/KF-041 dead-pipeline class), or hook the collision
reader to a genuinely produced map — a deeper task than a coordinated literal rebase. No new issue, none closed.

## 16. KNOWN_FINDINGS impact
Option A — no new finding indexed; this is a new **instance** of KF-040/KF-041 (pipeline present in copied code
but not executed on Genesis), layered on the KF-039 raw-WRAM-literal class. If later pursued, it warrants a
named finding: "Stage-1 collision-map producer (0x559E4/0x55A5A/0x55A7A) dead on Genesis; buffer 0x10DE00 never
populated."

## 17. Architecture compliance
CONFIRMED. Analysis only — no source, spec, tool, or ROM edit; no build; runtime evidence via MAME write-taps +
static disasm; arcade program remains the reference. Did not touch the mode=0x0008 handler, stage controller,
player position, camera/scroll, sprites, tilemaps, continue/game-over, D00298, Exodus, or audio. STOP honored.
