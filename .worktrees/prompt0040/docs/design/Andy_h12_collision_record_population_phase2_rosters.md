# Andy — CHECKPOINT H12: Collision-Record Population + Phase-2 Rosters

**Agent:** Andy · **Type:** Static RE (arcade) + Cody reconciliation. **NO ROM/MAME/Genesis. Build
counter 360 (unchanged).** Cody files untouched. Authoritative: `maincpu.bin`.

> **Honest scope:** H12 **closed the H11 blocker** — the `A5+0x10D000` column-descriptor populator is
> decompiled and the ROM collision/marker source is located and confirmed to contain H6-range
> markers. The **clean six-round roster** is **not** finalized: extracting one exact collision-word
> per grid cell (0x559B2's precise offset into the real descriptor layout) is the remaining step, and
> I did **not** fabricate rosters or round-pin the H10 materialized actors without that proof.

---

## A. Cody-report reconciliation

There are ~350 Cody Markdown files. Reading every one (mostly Genesis-runtime build history) would
consume most of the remaining budget against the project's efficiency mandate, so I read the
**H12-relevant** set and verified each against the arcade code
(`analysis/actor_decompilation/h12_cody_report_reconciliation.tsv`):

- **`Andy_0010D000_pc080sn_descriptor_table_wram_mapping_design.md`** + **`Cody_build0116…`** +
  **`Cody_build0117…`** (CURRENT, H12 CORE): the `0x10D000` table = 16 column-descriptor pointers at
  `A5+0x1000`, built at runtime by A5-relative code, sourcing ROM descriptors `0x1691C`/`0x18BDC`/
  `0x2399C`/`0x3725C`… On Genesis it is KF-036 WRAM `0x00FF1000` (arcade authority stays `0x10D000`).
  **This directly answered the H11 blocker and I verified it in the arcade disassembly (§C).**
- **`Cody_boss_positions_and_palette_staging_decompilation.md`** (CURRENT, in the C tree): `0x43458`
  offset table `0x43484` (27 entries), R5 indices 13..17; palette publish direction
  `A5+0x1600 → CLCS` (0x3A2D0 is `(A0)+→(A1)+`), so **boss line F = `0x3BA88[round][15] → 0x4FD02`**
  (pools 11/3/2/11/3/11). This **supersedes my earlier "staged-master" boss-palette interpretation**
  (which was based on the reversed copy direction) — imported as current; not redone.
- **`Cody_build0374_marker_3a_rope_ledge.md`** (CURRENT): marker **`0x3A` = scheduled-hostile
  zero-X-offset positioning, NOT platform/terrain/special-solid**. Imported into the marker classifier.
- **`Cody_build0373…`** + rope-ledge docs (SUPERSEDED/DISPROVEN, **NOT H12**): the 0x2A290/0x3008
  block ID was falsified; rope-ledge investigation **SUSPENDED by Tighe** — not touched.
- **Builds 0366–0372** (Genesis WRAM-rebase history): reinforce the lesson that arcade absolute
  `0x10Cxxx/0x10Dxxx` accesses must map to Genesis A5-relative WRAM — relevant background, not arcade
  semantics.

Superseded findings explicitly rejected: my own H10/earlier "boss palette via staged 0x4EAF6"
interpretation (Cody's copy-direction correction wins); the Build-0373 rope block ID.

## B. H11 starting point

H11 proved `0x13E → 0x50EE0 → 0x50F6B` section selection, six Phase-2 starts (R1 0x11, R2 0x2B, R3
0x41, R4 0x5A, R5 0x6E, R6 0x85), and `0x559B2` writing the collision/marker grid. The blocker was
the ROM population of `A5+0x10D000`.

## C. A5+0x10D000 populator — `0x502CC` (COMPLETE, `raw/000502cc.c`)

```
0x502CC: d1 = A5+0x13E; d1 *= 0x40
   A5+0x1000 = 0x1691C + d1           (column 0)
   A5+0x1004 = 0x18BDC + d1           (column 1)   [+0x22C0]
   A5+0x1008 = 0x1AE9C + d1           (column 2)   [+0x22C0]
   ...        = 0x1691C + col*0x22C0 + d1
```

**descriptor(col, scene) = `0x1691C + col*0x22C0 + (A5+0x13E)*0x40`, col = 0..15.** Verified in the
disassembly (0x502DC…0x5030C) and matches Cody's ROM samples (0x1691C/0x18BDC/0x2399C/0x3725C).

## D. Live column-descriptor format

Each `A5+0x1000` entry is a **long ROM pointer** into the per-column PC080SN column source (word
pairs: tile/attribute, and — at marker cells — a collision word whose HIGH byte is the marker).
Per-column stride `0x22C0`; per-scene (0x13E) stride `0x40`. Genesis-WRAM binding (Cody): the 16
pointers live at `A5+0x1000`, the rebuilt records at `A5+0x1040`, the copied first words at
`A5+0x1080`, dest slots at `A5+0x10A0/A4`, section output at `A5+0x10A8`.

## E. ROM collision/marker source

`descriptor → 0x55904 → A5+0x1040 records → 0x559B2` writes the grid at `0x10DE00`, cell =
`col_record[20 + subcol*2 + row*8]`, **marker = high byte** (read by `0x41180`). A scan of the
Phase-2 descriptor data confirms the source contains **real H6-range markers**: R1 phase-2 shows
`0x3A`, `0x3B`, `0x3E`, `0x40`, `0x42`, `0x4F`, `0x50`, `0x51`, `0x52`, … i.e. the floor (0x31–0x3C)
and letter (0x4F–0x51 torch/light) marker families the H6 materialization decodes.

## F. Progression / scene / scroll → descriptor flow

`A5+0x13E` (progression) directly indexes the descriptor via `*0x40`; horizontal scroll advances the
map-column index `A5+0x10C6` (0x558E4) and mutates the 16 pointers `+4` per pass (0x558CE). Section
kind (`0x50EE0/0x50F6B`, H11) selects outdoor vs castle independently.

## G. Static enumeration algorithm

For a scene `p` and column `col`: `addr = 0x1691C + col*0x22C0 + p*0x40`; read the column source and,
at each grid cell offset `20 + subcol*2 + row*8`, take the word's high byte as the marker.
`tools/analysis/decode_rastan_scene_markers.py` already emits the section layer; the marker layer
extraction is drafted but **not yet locked to the exact per-cell offset** (see §N).

## H. Marker occurrence totals

**PARTIAL** — a whole-descriptor scan over-counts (tiles vs collision words); a precise per-cell
extraction is pending (§N). Confirmed present (not a clean roster): R1 phase-2 rich in 0x3A/0x3B/
0x4F–0x51; R3/R5 phase-2 sparse in that raw scan (indicating the collision words sit at specific
offsets the exact model must target).

## I. Marker → materialized actor mapping

Uses the H6 routes (not re-derived) + Cody's `0x3A` semantics: `0x3A` → scheduled-hostile zero-X
positioning (floor-follower `0x41180 → 0x41336`), **not** a platform/terrain block. `0x4F–0x51` →
state 0x20 torch/light (H6, `0x41BCA/0x41BEE`). Floor markers `0x31–0x3C` → `0x40A86` transitions.

## J. Six Phase-2 actor rosters

`analysis/actor_decompilation/h12_phase2_actor_rosters.tsv` — status **PARTIAL/OPEN pending §N**. The
descriptor address ranges per round are pinned (`h12_collision_record_sources.tsv`); the resolved
per-scene actor list awaits the exact collision-word offset. **No roster entries fabricated.**

## K. H10 materialized-actor round pinning

**Deferred** — the 12 materialized actors stay ROUND PENDING because clean per-scene marker
enumeration (§J/§N) is the evidence needed to pin them, and I will not pin without it.

## L. Exact round palette instances

None added (no new round placement proven this pass). H10's rules unchanged; boss palette follows
Cody's corrected `0x3BA88[round][15]` (line F) — reconciled, not applied to field actors.

## M. C / evidence files created

- `raw/000502cc.c` (COMPLETE) + `rastan_scene_map.c` (semantic `column_descriptor_addr`).
- `function_coverage.csv` (+1), `historical_claim_audit.csv` (+1), README.
- Evidence: `h12_column_descriptor_writers.tsv`, `h12_collision_record_sources.tsv`,
  `h12_cody_report_reconciliation.tsv` (+ `h12_phase2_actor_rosters.tsv` marked PARTIAL).

## N. Exact remaining dependency

**The precise per-cell collision-word offset within the real column-descriptor layout** — i.e. lock
`0x55904`'s record build + `0x559B2`'s `col_record[20 + subcol*2 + row*8]` against the actual
`0x1691C`-format data so a clean marker list (not an over-counting whole-descriptor scan) is emitted
per scene. That single step turns the confirmed marker source into the six rosters and round-pins the
H10 materialized cast. Next PC: `0x55904` record build vs the `0x1691C` column format.

## Validation

Coverage guard **PASS** (97 rows/82 COMPLETE); fidelity **PASS**; `gcc -fsyntax-only` **PASS** (100
files); manifest consistency **PASS**. No fabricated rosters; no round-pinning without evidence;
marker 0x3A classified per Cody's proven scheduled-hostile semantic.
