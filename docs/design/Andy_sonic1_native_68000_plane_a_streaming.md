# Andy — Native 68000 Sonic-Style Plane A Streaming (architecture + Build 0350)

**Task classification:** EXTENDING · **Implementation language:** 68000 assembly only (no C runtime) ·
**Build authorized:** YES · **Platform:** GENESIS NTSC (`genesis`).
**Builds this task:** 0350 (produced, numbered, preserved, all gates PASS). 0349 preserved unchanged.

---

## 1. Phase 0 — governance

- **Classification:** EXTENDING (Plane-A native producer family; OPEN-001 / OPEN-018).
- **Relevant KFs:** KF-010 (FG→Plane A), KF-015 (scroll model, `+8` bias), **KF-072 (HIGH: the
  Build 0226 ring/col-dirty rewrite was reverted; never reintroduce a ring/full-VSRAM/col-dirty
  coordinate layer piecemeal)**, KF-071.
- **HIGH rediscovery hazards:** KF-072 (ring); the synthetic seven-epoch gate / OPT-003 `0x034C`
  canary (fragile — see §14); the shift-table pipeline.
- **Touched issues:** OPEN-001, OPEN-018 (advanced, not closed).
- **Contradiction check:** none. Build 0350 changes only **publication granularity** for the
  horizontal edge (a 32-word column write instead of ≤32 row DMAs). It does **not** change the
  Plane-A coordinate/ring model — the VRAM destination is byte-identical to the row-DMA path — so
  KF-072 is preserved.
- **C prohibition:** honored. The entire app is 68000 assembly; no C source exists in
  `apps/rastan-direct/src`, and none was added.

## 1a. Build 0350 manual result (Tighe, 2026-09-08)

Tighe played Build 0350:

- plays essentially the same as 0349;
- same `D00462` crash (unchanged / separate PC090OJ-space failure);
- **no perceptible speed improvement** (despite the ~64× structural horizontal transfer cut — some
  other subsystem dominates frame time; profiling deferred);
- Layer A still **visually worse than earlier pre-0349 builds**;
- the Sonic-style column publisher itself produced **no obvious additional visual regression** vs
  0349 (evidence that publication and content are separable);
- **forward decision:** retain the efficient native column publisher; the remaining defect is
  upstream of publication — the horizontal and vertical producers do not resolve the world through
  one identical authoritative path. Build 0350 is an architectural transfer experiment, **not** the
  visual-correctness target.

## 2. Build 0349 manual result (Tighe)

> Layer A renders differently, more wrong overall. Vertical rendering is more accurate, but
> horizontal rendering is partially wrong.

The `a5@0x013E*0x40` term improved the vertical source (as predicted) but did not make the
architecture coherent: horizontal resolves via the live rebuilt descriptor table (`0x00FF1040`),
vertical via the static `.Lplane_a_strip_src_table`, so the two producers can disagree cell-for-cell
and the vertical row overwrites the horizontal column with slightly different tiles. **The source
finding is kept; the coherent shared resolver is the remaining work (§8, Build 0351+).** Build 0349
is preserved unchanged as a permanent diagnostic artifact. The `D00462` freeze Tighe hit is a
separate, known PC090OJ-space failure (§ not addressed here).

## 3. Sonic 1 assembly studied (vendored `docs/reference/s1disasm/_inc/Level Drawing (REV00).asm`)

- **`LoadTilesAsYouMove`** (line 31): tests a per-plane scroll-flag byte with bits 0/1/2/3 =
  top/bottom/left/right; for each set bit it `bclr`s it and draws that edge.
- **`Calc_VRAM_Pos`**: world (x,y) → ring-wrapped plane VRAM address.
- **`DrawBlocks_LR`** (line 373): a horizontal row of blocks (camera moved up/down). Writes tiles
  contiguously, advances the plane address by `+4` (2 tiles) per block, `andi.b #$7F` column wrap.
- **`DrawBlocks_TB`** (line 415): a vertical column of blocks (camera moved left/right). Advances
  the plane address **down** by `+$100` (2 rows × `$80` stride) per block, `andi.w #$FFF` plane
  wrap (0x1000 = 64×32×2).
- **`DrawBlock`** (line 451): the actual VDP write — `move.l d0,(a5)` sets the control-port write
  address, `move.l (a1)+,(a6)` dumps two tiles to the data port, `add.l d7,d0` (d7=`$00800000`)
  bumps the address by one plane row (`$80`), repeat; plus H/V flip handling.

### Call graph
`LoadTilesAsYouMove → DrawBG_Top/Bottom → {Calc_VRAM_Pos, DrawBlocks_LR/LR_2, DrawBlocks_TB/TB_2}`;
each `DrawBlocks_* → GetBlockData → DrawBlock → VDP`.

### Reusable low-level mechanic (adapted)
The essential Genesis technique is **advancing the VDP write address by the plane row stride to
walk down a column**. Sonic re-addresses per block because its blocks are 2 cells wide; for
Rastan's single 8×8 cells the equivalent is **set VDP autoincrement = row stride (`0x80`), set the
column's base address once, then stream N cells** — the address self-advances down the column.
This is what Build 0350 implements.

### Sonic-specific logic rejected
16×16 block/`GetBlockData`, 256×256 chunk hierarchy, `v_lvllayout_*` level format, the H/V flip
`eori` block transforms, Sonic's camera/scroll-flag ownership, its VBlank scheduling, and its
map/world progression. Rastan's arcade PC080SN map state remains the sole semantic authority.

## 4. Rastan authoritative semantic source contract

Every Plane-A cell resolves from arcade-owned state (a5 = `0x00FF0000`):
`code = ROM_word(PTR[seg] + colidx*2 + row*8)`, `PTR[seg]` the live rebuilt descriptor pointer
table at `0x00FF1040` (`= strip_src_table[i] + a5@0x013E*0x40`, arcade `map_select_pointers`
0x0502CC), then `fg_cache_resolve` → residency slot, then Genesis attribute bits. This produces the
**final Genesis name word** staged in `staged_fg_buffer[(row&31)*64 + col]`.

## 5. Shared horizontal/vertical resolution contract (target) and 0350's scope

The coherent target is one resolver both axes call, agreeing on segment / selector / descriptor
state / world↔plane coordinates / residency. **Build 0350 does not yet unify the resolver** — it
takes the horizontal producer (`selector0_native`, already authoritative per Cody's analysis) as-is
and changes only how its column reaches VRAM. Unifying the vertical producer onto the same live
`PTR[seg]` resolution is Build 0351 (the fix for 0349's "horizontal partially wrong"). 0350 isolates
the column-writer variable so a regression in it is unambiguous.

## 6. Horizontal publisher (Build 0350)

- **Semantic event:** `selector0_native` (arcade selector 0, horizontal strip) produces one
  entering logical column into `staged_fg_buffer` (authoritative `PTR[seg]` source, unchanged).
- **Resolved cells:** 32 (the entering column's resident rows).
- **Publication:** `selector0` now sets one bit in `fg_col_dirty` (64-bit mask) for that column
  instead of 32 bits in `fg_row_dirty`. New VBlank routine `vdp_commit_fg_columns_if_dirty`
  ([tilemap_hooks.s](../../apps/rastan-direct/src/tilemap_hooks.s)) sets VDP autoinc = `0x80`, sets
  the write address to `0xE000 + col*2`, and PIO-streams 32 name words down the column from
  `staged_fg_buffer` (stride 128 bytes), then restores autoinc = 2. Reuses existing `vdp_set_reg` /
  `vdp_set_vram_write_addr`.
- **Words transferred:** **32** (was up to **2048**).
- **VDP mechanism:** PIO with autoincrement = plane row stride (Sonic `DrawBlocks_TB` technique).

## 7. Vertical publisher (Build 0350 = unchanged from 0349)

- **Semantic event:** selector-1/2 (`selector12_native`) and the pan hooks produce one entering
  logical row; each writes a full 64-cell row into `staged_fg_buffer` and sets one `fg_row_dirty`
  bit.
- **Active map segment honored:** YES (0349's `a5@0x013E*0x40` term; the pan-row helper).
- **Publication:** existing `vdp_commit_fg_strips_if_dirty` — one 64-word contiguous DMA per dirty
  row (autoinc = 2). A contiguous row is naturally a DMA; kept.
- **Words transferred:** 64 per entering row.
- **Coherence caveat:** vertical still resolves via the static strip table, so it is not yet
  cell-for-cell coherent with horizontal (Build 0351).

## 8. Simultaneous X + Y

One entering column (→ one column publication) plus one entering row (→ one row publication), both
read from the **same `staged_fg_buffer`**, so the shared corner cell is identical whichever producer
wrote it — a bounded, correct duplicate write, no plane redraw. `fg_col_dirty` and `fg_row_dirty`
are independent masks; both commits run each VBlank.

## 9. KF-072 handling

Build 0350 changes **publication granularity only**. The staged buffer coordinates and the VRAM
destination (`0xE000 + row*0x80 + col*2`) are byte-identical to the existing row-DMA path — no ring,
no full-VSRAM, no column-*coordinate* remap. This is deliberately clear of the 0226 failure class
(which was a coordinate-space rewrite applied to some producers but not others). If a future build
touches coordinates, KF-072 requires converting every producer together.

## 10. VBlank ownership

`selector0` resolves and stages on the arcade mainline (outside VBlank) and returns via RTS, exactly
as before. The new column publication runs only inside the arcade-owned VBlank publisher
(`dma_publish_frame → vdp_commit_fg_narrow_strips → vdp_commit_fg_columns_if_dirty`). No map
decoding moved into VBlank.

## 11. Performance evidence (one horizontal boundary crossing, full resident column)

| | semantic changed cells | VDP words transferred | VDP operations |
|---|---|---|---|
| Build 0348/0349 (row path) | 32 | up to **2048** (32 rows × 64) | up to 32 row DMAs |
| Build 0350 (column path) | 32 | **32** | 1 autoinc set + 1 addr set + 32 PIO + 1 restore |

**~64× reduction** in Plane-A words transferred for a horizontal crossing; the new path transfers
exactly the changed cells. Vertical unchanged (64 words/row). Verified structurally from the code;
the 30s Genesis smoke trace ran with `exceptions=0`, `crash_handler_entries=0`.

## 12. Build numbers / SHA / results

| Build | SHA-256 | gates | smoke | preserved |
|---|---|---|---|---|
| 0349 (source fix, diagnostic) | `81e7655365101ba2c760b94cebb4f1c96bfb8ed645d2e4ce803421810da409d6` | epoch FAIL (fragile), canonical/entry PASS | — | YES |
| **0350 (column publisher)** | `24e2f9bdb90c7f395988963fa709388a53573f5141e5a067dd4e2158f95f437d` | **canonical/entry/epoch PASS** | 0 exceptions, 564 frames | YES |

Variants (share 0350, gate-free): `_d` `702732…`, `_s` `d16d46…`, `_do` `ad1d4c…`. Counter = 350.
Nothing deleted, overwritten, or renumbered.

## 13. Build-system number preservation (fixed this task)

The `$(BIN)` recipe previously deleted the ROM and refused numbering on any gate failure. Per
Tighe's 2026-09-08 imperative it now **numbers + preserves every built ROM** and runs the three
gates as **labels** (recorded in the ledger, e.g. `[canonical=PASS entry=PASS epoch=PASS]`), never
deleting or withholding. The MAME trace step is likewise non-fatal. Validated: Build 0350 numbered
with gate labels; the 0349 fragile-gate scenario would now number+preserve automatically.

## 14. Automated validation

`make all` → assemble/link (RWX LOAD warning is pre-existing), boot guard PASS (pre+post),
`GATE_PASS` (canonical), gameplay-entry gate PASS, seven-epoch gate PASS, 30s Genesis smoke
`exceptions=0`. Note the seven-epoch gate FAILED for 0349 but PASSED for 0350 with the same vertical
source — reinforcing the prior classification of the record-3 / `0x034C` gate as a **fragile
synthetic artifact**, now non-blocking regardless.

## 15. Tighe acceptance test

ROM: `dist/rastan-direct/rastan_direct_video_test_build_0350.bin` (GENESIS NTSC). Play R1P1:
- **Horizontal:** newly entering columns should look correct and update as before, now via the
  compact column writer. Watch for column seams, a missing/partial rightmost column, or wrap glitches.
- **Vertical:** unchanged from 0349 (more accurate than 0348; not yet coherent with horizontal).
- **Combined H+V:** should not corrupt the corner or redraw the plane.
- Report anything worse than 0349 so the column writer can be corrected in a further numbered build.

Expected: 0350 ≈ 0349 visually (same staged content) but with far less Plane-A DMA. The "horizontal
partially wrong" coherence symptom is **not** expected to be fixed until Build 0351 (shared resolver).

## 16. Legacy dirty-row dependency

- `fg_row_dirty` is still used by the vertical selector-1/2 and pan-row producers and the scene-entry
  full publish — retained.
- The horizontal-column path no longer uses `fg_row_dirty`; its ≤2048-word row-DMA cost for column
  changes is eliminated.
- **Retirable once Build 0351 lands** (shared resolver + confirmed coherence): the static
  `.Lplane_a_strip_src_table` in the vertical helper (replaced by live `PTR[seg]`), and potentially
  the whole-row DMA for purely-vertical single-row edges could move to the same edge-job model.

## 17. Open/Closed issues; KNOWN_FINDINGS

OPEN-001 / OPEN-018 advanced (native Plane-A now edge-streams the horizontal axis), not closed. No
issue closed/reopened. KNOWN_FINDINGS: propose after Tighe validation — *"Build 0350: horizontal
Plane-A edge published as a bounded 32-word column (Sonic `DrawBlocks_TB` autoinc technique),
replacing ≤2048-word row DMA; coordinates unchanged (KF-072 preserved)."* Not indexed yet.

## 18. STOP status

Not a STOP.

**Build 0350** produced, numbered, preserved, gate-clean, smoke-clean, playable (efficient
Sonic-style horizontal column publisher).

**Build 0351** produced, numbered, preserved — **one shared authoritative resolver
(`resolve_plane_a_cell`) now used by every gameplay Plane-A producer** (selector-0, selector-1/2,
pan-up, pan-down), ending the 0349/0350 horizontal/vertical source split. Retains 0350's efficient
publisher. Gates `[canonical=PASS entry=PASS epoch=FAIL]` (the epoch FAIL is the fragile synthetic
record-3/`0x034C` gate, now non-blocking); 30s smoke `exceptions=0`. Full detail:
[Andy_build0351_plane_a_shared_live_resolver.md](Andy_build0351_plane_a_shared_live_resolver.md).

Awaiting Tighe's R1P1 visual result on 0351 (compared against earlier pre-0349 builds). If a residual
divergence remains, the next candidate is the resolver's column mapping vs the arcade live-table
column, proven by an earlier-build oracle comparison → Build 0352.
