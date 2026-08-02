# Selector-0 Plane A Logical Coordinate Proof (research; no source/build)

**Type:** original-arcade runtime proof. **Production / build / counter:** unchanged (240).
**Authority:** original arcade Rastan (MAME `rastan`, world rev1) + opcodes + `address_map.json`.
**Scope:** selector-0 Plane A **columns only** (scene-fill + gameplay entering-columns). No
selector-1/2 rows. No implementation. Governed by `RULES.md` §11 +
`PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`.
**Evidence:** `states/traces/plane_a_selector0_logical_coord_20260728_105839/` (`sel0.lua`,
`sel0.txt`). Method: tap the arcade selector-0 collision write (PC `0x0559EC`, in producer
`0x0559B2`); per write compute the **semantic-derived** logical (row,col) and compare to the
logical (row,col) **decoded temporarily from the C08000 cursor / collision address** (oracle).

`a5 = 0x10C000`: `10CA→0x10D0CA`, `10CC→0x10D0CC`, selector `10A8→0x10D0A8`, cursor
`10A0→0x10D0A0`, collision base `0x10DE00`, C-window base `0xC08000`.

---

## Exact selector-0 semantic inputs

- **selector** `a5@0x10A8 == 0` (column publish; dispatch 0x055948 → driver 0x055968).
- **ring strip / sub-column** `a5@0x10CA` (0..3) — also the producer's block `strip` index.
- **ring group** `a5@0x10CC` (0..15).
- **segment** `s` = 0..15 (driver 0x055968 16-iteration loop counter).
- **cell** `c` = 0..3 (producer 0x0559B2 inner counter `d2`).
- **descriptor/source tables** `0x10D040` (block ptr per segment), `0x10D080` (source word per
  segment) — supply tile/attr/collision **data**.
- scroll: **not required** for the column identity (proven below).

## Scene-fill logical-column formula

```
logical_column = (a5@0x10CC * 4 + a5@0x10CA) & 63
```
Proven for all 64 scene-fill publications (cols 0..63). `10CA` cycles 0,1,2,3; `10CC`
increments 0→15 as `10CA` wraps. Sample: pub1 `10CC=0,10CA=0→col0`; pub5 `10CC=1,10CA=0→col4`;
pub64 `10CC=15,10CA=3→col63`.

## Gameplay logical-column formula

**Identical** — same formula, no scroll term:
```
logical_column = (a5@0x10CC * 4 + a5@0x10CA) & 63
```
Proven across 141 gameplay entering-column publications covering **all 64 columns**, including
two full 63→0 ring cycles. (The ring column *is* the Plane A column; camera position is applied
separately via HSCROLL, not by choosing which ring column is written — confirmed because the
oracle a0-column equals the ring formula with no scroll offset.)

## Logical-row formula

```
logical_row = segment * 4 + cell        (segment 0..15, cell 0..3 → 0..63)
```
Proven: within every publication the 64 collision writes emit `logical_row = 0,1,2,…,63` in
order (the producer walks `d2` 0..3 per segment, +1 row/cell; segments run 0..15 contiguously).
`rowseq_ok=true` for every sampled publication (64 rows each).

## Ring-counter timing (resolved — no assumption)

The publication uses the counter values **as they stand while the driver 0x055968 runs**, i.e.
**pre-increment**: dispatch 0x055948 publishes *first*, then `a5@0x10CA += 1` (0x055954), then
0x558A2 bumps `a5@0x10CC` only when `10CA` reaches 4. The tap read `10CA/10CC` *during* the
collision write (inside 0x055968, before those increments); they matched the oracle for every
publication — so the **active column uses the pre-dispatch-increment `10CA` and the current
`10CC`.** (`10CA` doubles as the producer's `strip`, so column and strip are consistent.)

## Collision-index formula

```
collision_address = 0x10DE00 + ((logical_row * 64 + logical_column) * 2)
```
The collision map is row-major, 64 cells wide, 2 bytes/cell. This matched the arcade's actual
collision destination (`(a0−0xC08000)>>1 + 0x10DE00`) for **every** sampled cell — it is
**C08000-free** (uses only logical row/col).

## Comparison results

Runtime (`sel0.txt`), tap on PC 0x0559EC, `semantic` vs `C08000 oracle`:

- **Scene-fill:** 64 publications, `semcol == ocol == a0col` for all; **0 mismatches**.
- **Gameplay:** 141 publications, all 64 columns, **0 mismatches**.
- **Row sequence:** `logical_row = segment*4+cell` = 0..63 per publication; **0 row mismatches**.
- **SUMMARY:** `pubs=205 colMismatch=0 rowMismatch=0`.
- Cursor cross-check: `a5@0x10A0` advanced `C08000, C08004, C08008, …` (+4/column) in both fill
  and gameplay; `a0col = (a5@0x10A0−0xC08000)/4 & 63` equalled the semantic column throughout.

## Wrap results

- **Ring-group transition** (`10CA 3→0`, `10CC++`): every 4th publication; formula holds across
  it (e.g. fill pub5 and gameplay pub69 → col 4 at `10CC=1,10CA=0`). 0 mismatches.
- **63→0 column wrap:** scene-fill pub64 (col63, `10CC=15,10CA=3`) → pub65 (col0,
  `10CC=0,10CA=0`); **and in continuous gameplay** at pubs 128 and 192 (col63 → col0, `10CC`
  15→0). All `colmatch=true`.

## Semantic tile/attribute source — independent of C08000

Confirmed from the producer opcodes (0x0559B2): per cell it reads
`tile = *(block + 0 + cell*8 + strip*2)`, `word0/attr = *(a1)`, and
`collision = block+32==0xFF ? *(block+34) : *(block + 20 + cell*8 + strip*2)`, where
`block = a2` (from `0x10D040`) and `a1` (from `0x10D080`). **None of the tile/attr/collision
*source* reads use `a0`/C08000** — `a0` is only the destination. So the semantic tile identity
and attribute are supplied by the descriptor/source tables, fully independent of the PC080SN
destination address.

## Graphics-ROM patterns remain retained assets

Explicitly: the original tile-pattern artwork in the arcade graphics ROMs, the semantic arcade
tile identity, and palette/flip/priority meaning are **retained authoritative assets** — not
PC080SN behavior. This task did **not** investigate, classify, or change graphics-pattern
conversion, VRAM loading, tile residency, or the Genesis-VRAM mapping. Only the PC080SN
*realization* (C08000 name-RAM addresses, C-window geometry, word-pair destination
representation) is a removal target; the eventual native path maps the retained tile identity to
its Genesis VRAM tile and emits a final Plane A name word.

## Remaining blockers (not coordinate blockers)

The **coordinate** blocker from `Andy_plane_a_semantic_cut_contract.md` §5/§8(#1,#2) is
**RESOLVED for selector-0 columns**. Remaining items are non-coordinate implementation concerns,
out of this task's scope:

1. `a5@0x10A0` loop bookkeeping — the arcade still seeds/advances it and the scene-fill loop
   does the `−0x3FFC` back-step + driver save. A native replacement must not break that (the
   helper no longer *needs* it for coordinates, but the surrounding arcade loop still expects it
   advanced).
2. Plane A residency logical→physical mapping (row 0..63 → resident 32-row window) for visual
   writes, while collision is written for all 64 logical rows.
3. Register discipline — the proven Build 0240 root (a helper clobbering caller registers). Any
   in-loop helper must save/restore every non-owned register.
4. selector-1/2 rows — explicitly out of scope; not proven here.

## Whether selector-0 can now cut at 0x055948

**YES — from the coordinate standpoint.** The logical column, logical row, and collision index
for every selector-0 published cell are now proven derivable from semantic ring state
(`10CA`/`10CC` + segment/cell iteration) and the descriptor/source tables, **without `a5@0x10A0`,
C08000 subtraction, C-window strides, or PC080SN name-RAM addresses** (0 mismatches over 205
publications, fill + gameplay + wraps). A selector-0 native column producer can therefore be
driven by semantic state at the dispatch/driver boundary. Final boundary *selection and
implementation* still require resolving the non-coordinate items above (esp. the `a5@0x10A0`
loop bookkeeping and register discipline) — but the PC080SN-geometry dependency for *coordinates*
is removed.

## STOP status

**Not triggered.** The formula needs no `a5@0x10A0`/C08000; fill and gameplay share one formula;
ring timing is resolved (pre-increment); collision matches exactly; the 63→0 wrap is proven in
both phases; tile/attribute selection is separable from the destination address.
