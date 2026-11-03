# Andy — Plane-A Segment 0/1 Source Contract Proof

**Task:** EXTENDING / DIAGNOSTIC PROOF · **Runtime C:** NO · builds 0348–0352 preserved.
Proof-first per Tighe's directive: no source-address change was made before this proof.

## 1. Independent per-cell oracle (located)
The Palette Composer's Segment Map is served by `tools/graphics_editor/server.py :: layera_map(seg)`
(the `/api/layera_map` endpoint used by `tools/graphics_editor/app.js`). Its per-cell formula, over
the authoritative arcade image `build/regions/maincpu.bin`:

```
ti = wr>>2; dr = wr&3;  tb = MAP_BASES[ti] + seg*0x40         # MAP_BASES = strip_src_table (0x1691C..)
dc = sc>>2; ds = sc&3;  entry = tb + dc*4
attr = be(entry); desc = be(entry+2)                          # {word0=attr, word1=metatile ptr}
code = be(desc + dr*8 + ds*2) & 0x3FFF
```

A segment is a 64×64 backing tilemap; `_MAP_STRIDE=0x40`. Because `world_col = seg*64 + sc`, the term
`seg*0x40 + (sc>>2)*4` collapses to `(world_col>>2)*4` — i.e. the oracle descriptor is
**`MAP_BASES[row>>2] + (world_col>>2)*4`, keyed to the true global world column**, with no runtime
segment counter. This is an independent oracle (it does not use the Genesis resolver).

## 2. Ground truth (arcade ROM, standalone replication of the oracle)
- **Segment 0:** world columns 0–63 all outdoor (code `0x00BD..0x00C0`).
- **Segment 1:** columns 4–31 outdoor (identical to seg 0), **columns 32–63 = cave** (`0x0411,
  0x0408, 0x040A…`). seg0 vs seg1 differ only at cols 0–3 and 32–63.

So "cave on the right of Segment 0" = Segment-0 columns 32–63 rendering Segment 1's cave codes.

## 3. Runtime ground truth (read-only MAME dump, Build 0352)
Driving the same inputs as the gameplay-entry gate (P1 A, P1 Start, brief P1 Right), captured at the
start of the level (`tools/mame/scripts/plane_a_seg_state_dump.lua`):

| frame | rec (0x13E) | strip_group (0x10CC) | scrollX | `a5@0x1000[0]` |
|---|---|---|---|---|
| 330 | 0 | 1 | 0 | `0x016920` (+1 block) |
| 360 | 0 | 7 | 0 | `0x016938` (+7) |
| 390 | 0 | 12 | 0 | `0x01694C` (+12) |
| 420 | 1 | 0 | 0 | `0x01695C` (**+16 = seg 1 base**) |

Proven relations:
- `a5@0x1000[i]` is the **raw arcade strip-source pointer**, initialized `MAP_BASES[i] + seg*0x40`
  and advanced +4 per streamed 4-col block (`map_advance_source_ptrs`, arcade 0x0558C6).
- `0x1000_block = 16*rec + strip_group` = total col-blocks streamed (matches the table exactly).
- The initial fill streams a full 64-col plane (16 blocks) **ahead** of the camera: at `scrollX=0`
  the camera-left edge is world col 0 (Segment 0) while `a5@0x1000[0]` already points at Segment 1
  base (`0x01695C`), `rec=1`. The stream front leads the camera-left by exactly **16 col-blocks**.
- `a5@0x1040[i]` (the rebuilt/remapped table selector-0 reads) holds small Genesis addresses
  (`0x001200…`), a different table from `a5@0x1000`.

## 4. Erroneous Segment-0 test cell — first exact divergence
Cell: physical/plane row 40, plane column 40 (world row 40, world col 40) at level start, `scrollX=0`.

- **Oracle:** world col 40, Segment 0 → `entry = MAP_BASES[10] + (40>>2)*4 = 0x2C49C + 0x28 = 0x2C4C4`;
  code `0x00BF` (outdoor). (Same cell in Segment 1 would be `0x040A`, cave.)
- **0352 resolution:** `entry = a5@0x1000[10] + ((40>>2) − strip_group)*4`. With `a5@0x1000[10]`
  advanced to Segment 1 and `strip_group=0`: `entry = (MAP_BASES[10] + 0x40) + (10)*4` =
  `MAP_BASES[10] + 0x68` = **Segment 1, col-block 10** → cave code `0x040A`.

**First divergence:** 0352 selects the descriptor **16 col-blocks (one whole segment) too far ahead**,
because it references `strip_group` (the leading stream block) instead of the camera. The exact fix
falls straight out of §3:

```
correct:  entry = a5@0x1000[row>>2] + ((col>>2) − 16)*4      (16 = plane width in col-blocks = the
                                                              constant stream-lead; rec & strip_group
                                                              cancel algebraically)
0352:     entry = a5@0x1000[row>>2] + ((col>>2) − strip_group)*4      (wrong by (16 − strip_group))
```

At `scrollX=0` this makes every plane column read Segment 0: `a5@0x1000[i]` (+16 blocks) `+ ((col>>2)
− 16)*4 = MAP_BASES[i] + (col>>2)*4` = the oracle exactly. Verified against §2.

## 5. State-variable semantics (proven)
- **`a5@0x1000[i]`**: raw arcade strip-source pointer, `MAP_BASES[i] + (total_blocks_streamed)*4`;
  leads the camera by one plane (16 blocks). NOT the camera position.
- **`a5@0x10CA`** (strip_index): within-block column 0..3 of the streaming front.
- **`a5@0x10CC`** (strip_group): the streaming front's col-block 0..15; `= 0x1000_block mod 16`.
  It is the LEADING edge, not the resident-column origin.
- **`a5@0x013E`** (segment counter): `= 0x1000_block div 16`; the leading/streamed segment, ahead of
  the camera's visible segment by the fill lead. Using it (0351) or `a5@0x1000` (0352) to source
  resident columns injects the leading segment (cave) into still-visible earlier-segment columns.

## 6. Architectural conclusion
- **Is `(col_block − strip_group)*4` correct? NO.** It references the leading stream block; resident
  columns need the camera-relative `(col_block − 16)`.
- **Is `resolve_plane_a_cell(current_state, row, col)` valid for arbitrary resident cells? NO.** The
  current stream state (`a5@0x1000`/`a5@0x013E`/`strip_group`) is the leading/streamed edge, which
  runs one plane ahead of the visible camera. Reconstructing a resident column from it is wrong.
- **Does the arcade preserve source identity through edge-publication? Effectively YES.** The arcade
  publishes each column at entry (when the stream front matched that column) and its 64×64 hardware
  tilemap retains it; vertical scroll needs no row redraw. The Genesis error is *re-resolving*
  resident columns from the now-advanced stream front.
- **Correct Genesis contract:** the horizontal producer (`selector0`) legitimately publishes only the
  **leading-edge** entering column, so its `strip_group` reference (delta 0 = stream front) is
  correct. The **vertical** producers publish **resident** columns and must be keyed to the camera:
  `entry = a5@0x1000[row>>2] + ((col>>2) − 16)*4` (exact at `scrollX=0`; a ring-rotation term is
  required once `scrollX` is not a multiple of the plane width — a follow-up refinement).

## 7. Collision comparison
Collision is produced by `selector0`/`selector12` from the live descriptor at entry and is correct
(cave only in Segment 1). It is left unchanged. Its correctness is consistent with the finding: the
entering-edge path is right; only the vertical *name* re-resolution from stream state is wrong.

## 8. Proposed correction (smallest, evidence-backed)
Split the delta reference by producer role (they are not the same operation, §6):
- **`selector0` (horizontal, leading edge):** keep `ref = strip_group` (delta 0 = stream front =
  the entering column). Unchanged.
- **Vertical producers (`pan up/down`, `selector12`):** `ref = 16` (plane width in col-blocks), i.e.
  `entry = a5@0x1000[row>>2] + ((col>>2) − 16)*4`. Camera-relative; oracle-exact at `scrollX=0`.

Implement by passing the reference block to `resolve_plane_a_cell` (a small global set by each
producer before its loop). Retain the Sonic-style 32-word column publisher (0350) and the shared
resolver body; only the delta reference changes. Build the result as the next number.

Known residual (documented, not yet fixed): during horizontal scroll (`scrollX` not a multiple of the
plane width) the vertical path needs a ring-rotation term `((col − camera_left_phys) mod 64)`; the
`−16` constant is exact only at plane-aligned scroll. The reported failure (Segment-0 start,
`scrollX=0`) is fixed exactly. This is the next validation step (0354) if Tighe sees scroll-time
artifacts.

## 8a. Correction implemented — Build 0353
`resolve_plane_a_cell` now takes a per-producer stream-lead reference `plane_a_src_ref_block`
(delta = `col_block − ref`):
- `selector0` sets `ref = strip_group` (delta 0 = stream front = its leading entering column) — unchanged behavior.
- the vertical producers (`pan up/down`, `selector12`) set `ref = 16` (one plane width) — camera-relative.

Verified algebraically against the oracle: at level start `a5@0x1000[row]=MAP_BASES[row]+0x40`, so for
every plane column `entry = MAP_BASES[row] + (col>>2)*4` = Segment 0 (outdoor) — matching §2/§4. The
Sonic-style 32-word column publisher and the shared resolver body are retained; only the delta
reference changed.

- **Build 0353** release SHA `28cf226cbb79edb3e937bb66df6250d6b026e33209aeff828b558d175a2ea582`
  (`_d 4ea5fa…`, `_s 03b6ae…`, `_do 1a0ff0…`). Counter=353. 68000 asm only.
- Gates: `[canonical=PASS entry=PASS epoch=PASS]` (all pass); 30s Genesis smoke `exceptions=0`,
  `crash_handler_entries=0`, boots to gameplay. Builds 0348–0353 all preserved.
- **Known residual:** the `−16` constant is oracle-exact only at plane-aligned scroll; a ring-rotation
  term `((col − camera_left_phys) mod 64)` is needed for arbitrary horizontal scroll (Build 0354 if
  Tighe sees scroll-time artifacts). The reported failure — Segment-0 start, `scrollX=0` — is fixed.

### Build 0353 manual result (Tighe, 2026-09-08)
- **Segment 0 looks good** — the cave bleed is fixed (proven column fix landed). ✅
- Residual: **dirt/black tiles inside the cave when dropping down in Segment 1**, and **vertical
  (up/down) scrolling is not fully stable**. These are the predicted scroll-time residuals — the
  camera↔plane mapping needs the ring-rotation term, and the **vertical (row) axis** almost certainly
  has the *same* leading-vs-resident/ring issue this proof established for the column axis (the fix so
  far only corrected the column/segment source; `world_row` from `scrollY` was not re-derived).
- `D00462` Segment-5 crash: still reproduced, unchanged, separate.

**Next (Build 0354) requires the same proof method on the vertical axis + ring** (not a guess): prove,
for a wrong "drop into cave" cell, the `world_row` (from `scrollY`) and ring-column mapping against the
oracle, then correct. Deferred to Tighe's go-ahead.

## 9. Performance / D00462 (recorded, deferred)
Game still visibly slow; `_do` still shows large vblank-overrun black bars; the horizontal Plane-A
transfer reduction did not visibly fix frame time — attribution requires measured VBlank accounting
(next major task), not assumed. `D00462` Segment-5 crash: REPRODUCED / UNCHANGED, separate.
