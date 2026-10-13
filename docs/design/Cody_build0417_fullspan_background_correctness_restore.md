# Cody Build 0417 — Full-Span Background Correctness Restore

## Result

Build 0417 reverses the unsafe Build-0415/0416 assumption that the immediate
40x28 or 41x29 VDP-visible window is also the logical maintenance domain.  The
current background representation derives cells from moving arcade source,
segment, and package state.  Under that representation every producer must
retain the proven 64-cell logical coordinate model (KF-072).

This change does **not** return to whole-plane publication.  Logical production
is full-span, while physical publication remains incremental: independent row
and column dirty state, a separately regenerated gather for every dirty column,
one 32-word DMA per dirty column, and VDP destination autoincrement 128.

Tighe's real-Genesis visual acceptance is required.  In the `_do` ROM, black
horizontal regions are the intentional IRQ6-overrun indicator.  They are
performance evidence only and are excluded from every Layer-A/Layer-B visual
judgment.

## KF-072 and the rejected narrow model

Build 0226 previously demonstrated this failure class: a partial ring/column-
dirty conversion produced coherent displaced scenery and was reverted. KF-072
requires every producer to share one coordinate space. Builds 0415 and 0416
again shortened selected producers to 40x28 and 41x29 while the surviving
moving-source, 64-row, collision, reseed, and trailing-retention contracts
remained full-span. The Build-0416 fine-scroll `+1` correction was valid, but
it did not restore the missing logical invariant.

## Coordinate-space repair

The production changes are confined to `tilemap_hooks.s`:

- `selector0`: collision still resolves all 64 rows; Plane-A name resolution
  again occurs for all 64 logical rows **before** the 32-row physical projection
  test. This preserves distinct semantic/cache handling for logical rows N and
  N+32 while staging only the current physical half.
- `selector1/2`: the viewport-local 41-column gate is removed. An accepted
  physical row resolves/stages all 64 logical columns.
- Plane-A pan row producer: starts at logical column 0 and traverses 64 columns.
- Plane-B pan row producer: independently starts at logical column 0 and
  traverses 64 columns through its own descriptor/package context.
- Plane-B directional column producer: traverses all 64 logical source rows;
  the existing helper stages only its independently selected 32-row physical
  projection, and `bg_col_dirty` owns publication.
- Collision remains the existing full 64x64 logical ring and was not redesigned.

The existing scene-entry path performs 64 selector-0 column publications. With
selector-0 again resolving 64 rows, the initial semantic seed covers 64x64
logical cells. Existing scene/segment/package reseed and camera-pan entry
points are retained; their producers now share the full-span model. The
ring-unwrapped Plane-A source reference and independent Plane-B boundary
package state remain unchanged, preserving prior-segment trailing terrain when
the stream front advances.

## Physical publication retained

The safe Build-0415/0416 publication work is unchanged:

- `MAP_GET_NAME_A`, `MAP_GET_NAME_B`, and `MAP_GET_COLLISION` accessor seam;
- `fg_col_dirty` and `bg_col_dirty` 64-bit masks;
- independent row and column dirtiness;
- per-dirty-column gather regenerated immediately before that column's DMA;
- 32 gathered words from the 64x32 staging plane;
- VDP destination autoincrement 128, restored to 2 after column publication;
- Plane-A and Plane-B separate gather buffers and lifecycle.

Thus 64 logical resolves never imply a 64-row physical DMA. The Genesis plane
remains 64x32.

## Enhanced verifier

`verify_bg_a_incremental_background.py` now tests logical coherence instead of
only immediate visibility. It statically requires each production producer's
64-cell traversal and verifies:

- rejected Build 0415 40x28 model: **FAIL**;
- rejected Build 0416 41x29 model: **FAIL**;
- Build 0417 64x64 model: **PASS**;
- initial 64x64 semantic seed and 64x32 physical projection: **PASS**;
- distinct N/N+32 logical identities: **PASS**;
- moving source-context replacement across the complete strip: **PASS**;
- prior-context trailing-column retention: **PASS**;
- independent Plane-B row/column package context: **PASS**;
- multi-dirty gather lifetime and 32-word/autoincrement-128 DMA: **PASS**.

## Performance

The exact 0417 controlled trace is under
`states/traces/build0417_fullspan_performance_exact/`. The same cold-boot,
record-2, 300-rendered-frame route used for 0416 produced:

- 211 complete worker pairs / 300 display frames (`0.7033`);
- worker median/p95/max: `147,248 / 286,286 / 307,732` cycles;
- IRQ median/p95/max: `157,405 / 297,317 / 314,479` cycles;
- worker over 128,009 cycles: `80.1%`;
- IRQ over 128,009 cycles: `87.7%`;
- VDP ownership violations: `0`;
- DMA words/frame average/max: `640.45 / 1120`.

Because the restored work slows gameplay progression, this fixed 300-display-
frame route no longer reaches the historical 22-event vertical-pan interval.
The 0417 entry in that exact pan table is therefore **N/A**, not an inferred
number:

| Representative pan metric | 0414 | 0415 rejected | 0416 rejected | 0417 |
|---|---:|---:|---:|---:|
| Row/map median | 153,890 | 98,298 | 100,704 | N/A (route did not reach pan) |
| Worker median | 230,636 | 172,396 | 174,892 | N/A |
| IRQ median | 233,829 | 179,471 | 181,967 | N/A |

The directly comparable selector-0 horizontal event does occur. Its full-span
row/map average is `135,751.6` cycles (40 events), versus `135,704.0` in Build
0414: effectively all logical resolver cost removed by the unsafe narrowing is
restored (`+0.04%` versus 0414). Build 0416's rejected 29-row average was
`94,034.0`; restoring correctness costs `+44.36%` for this producer. The safe
physical publication mechanisms remain, but full-span semantic resolution is
again the dominant cost. BG-B and Background Phase C were not started.

Black `_do` band frequency/extent and the real-hardware static-enemy threshold
remain Tighe tests. A larger band would mean more IRQ6 overrun, not background
corruption.

## Gates and artifacts

- full-span verifier: PASS;
- canonical gate: PASS;
- gameplay-entry gate: PASS, address/bus/illegal/crash `0/0/0/0`;
- pre-existing seven-epoch label: FAIL (unchanged known gate);
- transition retention generator: PASS, rope 12 and waterfall 224 retained;
- sprite generator/direct-dispatch/packed-bank/A4-A5 contracts: PASS;
- generated sprite set: 49 cells retained;
- VDP ownership: PASS, zero armed violations;
- Build 0417 `_c` fast closeout: COMPLETE, 18/18 subrounds, player fallback
  `0`, generic fallback `0`, piece adapter `0`, crash `0000`.

All five ROMs are 1,998,520 bytes:

| Variant | SHA-256 |
|---|---|
| canonical | `36f8300bedc077c9b3af99c83c1b0fc9d2623e2acfa4541e7cea86f8d78b4835` |
| `_d` | `8485a146333918e2cec3782fdf29485d04a92ff9551b16973e2907e353be6f7e` |
| `_s` | `c72d8340f297a5ff8b61debc06011a4d38a68e388a3b8b89b3d2c55160da04d9` |
| `_do` | `d7fd99773ba612ffa411b06966fc89fbec8b393e75cd53367472716cfa2f8e8f` |
| `_c` | `90c2eba88205ad50c6db66e6a72928a8a2954df64e02dc3909377ccfbf51973f` |

Tighe must judge only rendered scenery for Layer-A/Layer-B correctness on the
real Genesis, separately recording `_do` overrun bands as performance data.
