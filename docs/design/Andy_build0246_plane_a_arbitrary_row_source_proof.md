# Build 0246 — Plane A Arbitrary Row/Cell Source Proof (research; no source/build)

**Agent:** Andy. **Type:** focused architecture/source proof.
**Production source / remap spec / ROM / build / counter:** UNCHANGED (Build 0246 / counter 246).
**Authority:** original arcade Rastan (MAME `rastan`, world rev 1) opcodes + `build/rastan-direct/address_map.json`
(arcade→genesis) + `specs/rastan_direct_remap.json` + `build/rastan-direct/rastan_direct_patch_manifest.json`.
`0xC08000` / PC080SN C-window used **only as a runtime oracle**, never as production authority.
**Evidence:** `states/traces/build0246_arbitrary_row_source_20260801/` (`arb.lua`, `arb.txt`).

## Native-hardware-replacement acknowledgement (policy §10/§12)

- **Semantic cut retained (arcade-owned):** scene/stage selection, segment index `a5@0x13E`, the 16
  ROM strip-descriptor source tables, the map-column source cursor, the ring/scroll progression, and
  the logical terrain-cell identity + collision word. This proof shows the entire **tile/attr/collision
  source is a pure function of `(logical_row, logical_column, segment_index)` over ROM tables**.
- **Chip tail removed (below the cut):** the PC080SN destination cursor `a5@0x10A0/0x10A4` (the
  `0xC08000` C-window address), the word0/word1 name-RAM cell pairing, the `+0x100`/`−0x3FFC`
  C-window strides, and collision indexed through the chip address. None of these participate in the
  source formula proven here.
- **No transitional compatibility introduced.** `0x10D000/0x10D040/0x10D080` are classified below as
  semantic source cursor / bounded per-column caches of ROM content — **not** chip name-RAM.

---

## 1. Question and result

**Question (this checkpoint's single goal):** prove or reject that an *arbitrary* semantic Plane A
cell/row source is derivable from retained Rastan map/source structures, using the existing Stage-1
**initial fill** as evidence, without a live PC080SN destination cursor, a live selector-1/2
publication event, `0xC08000`, or a reconstructed 64×64 chip image.

**Result: PROVEN (derivable).** The initial fill publishes **64 logical columns × 64 logical rows**
via selector-0, exposing the complete Stage-1 logical Plane A map (including the rows 33–54 that the
32-row Genesis ring is missing) **before** the camera pan. Every one of those 4096 cells' tiles is
reproduced exactly by a ROM-only formula keyed on `(row, col, segment_index)`:

```
seg  = row >> 2 ;  cell  = row & 3
grp  = col >> 2 ;  strip = col & 3
E    = strip_src_table[seg] + segment_index*0x40 + grp*4          ; ROM address (4-byte entry)
attr = *(u16)(E)                                                  ; source/control word (word0)
dp   = *(u16)(E + 2)                                              ; metatile descriptor pointer
tile = *(u16)(dp + (cell<<3) + (strip<<1))
coll = (*(u16)(dp+32) == 0x00FF) ? *(u16)(dp+34)
                                 : *(u16)(dp + 20 + (cell<<3) + (strip<<1))
```

`segment_index = a5@0x13E` is a single semantic scalar (the map-position segment). No `0xC08000`,
no `a5@0x10A0/0x10A4`, no selector-1/2 event, no chip image.

**Runtime oracle:** over all **4096** fill cells, `mismatch=0` vs the actual `0xC08000` tiles;
and over all 4096 cells the live rebuilt tables matched the constant recompute
(`misD000=0 misDp=0 misTile=0`). Details in §5.

## 2. Authority and routes used

Arcade→genesis resolved by **segment membership in `address_map.json`** (`relocation_delta = 0x200`;
`arcade_copy` segments preserve the copy 1:1, so genesis = arcade + delta there; `patched_site`
entries are the individually-routed hooks). **No fixed-offset inference is used as proof.**

| Arcade PC | Genesis PC | JSON kind | Role in the source chain |
|---:|---:|---|---|
| `0x0502CC` | `0x0504CC` | arcade_copy | `map_select_pointers` — seeds `0x10D000[i]` and map-stream ptr |
| `0x0502E4` | `0x0504E4` | arcade_copy | first `movel #0x1691C+seg*0x40, 0x10D000` (strip_src_table load) |
| `0x0503B4` | `0x0505B4` | arcade_copy | tilemap0 source base seed (`0x3951C + tm0idx*0xC`) |
| `0x0503D6` | `0x0505D6` | arcade_copy | map-stream ptr seed (`0x50F6B + 0x50EE0[seg]`) |
| `0x0558C6` | `0x055AC6` | arcade_copy | `map_advance_source_ptrs` — `0x10D000[i] += 4` per group |
| `0x0558E0` | `0x055AE0` | arcade_copy | ring-cycle end — `10CC=0`, `0x10C6 += 1`, `0x13E += 1` |
| `0x055904` | `0x055B04` | **patched_site** | descriptor rebuild → `genesistan_hook_pc080sn_descriptor_rebuild` (`0x00071F78`) |
| `0x055968` | `0x055B68` | **patched_site** | selector-0 strip → `genesistan_hook_tilemap_plane_a_selector0_native` (`0x000704E8`) |
| `0x055990` | `0x055B90` | **patched_site** | selector-1/2 strip → `genesistan_hook_tilemap_plane_a_selector12_native` (`0x0007061A`) |
| `0x0559B2` | `0x055BB2` | arcade_copy | selector-0 cell producer body (retained ROM copy) |
| `0x0559EC` | `0x055BEC` | arcade_copy | cell producer collision store (the oracle tap point) |

`specs/rastan_direct_remap.json` intents and manifest bytes for `0x055904/0x055968/0x055990` were
re-confirmed against `Cody_build0246_native_plane_a_vertical_source_proof.md` (unchanged).

## 3. The semantic map-source chain (top-down, from opcodes)

All facts below are decoded from the original arcade opcodes (`analysis/ghidra/rastan_arcade/exports/
linear_disassembly.tsv`) and cross-checked with `docs/arcade_reference/pc080sn/`.

**(a) Stage → segment index → 16 ROM source bases.** Scene-init `map_select_pointers` (`0x0502CC`):
```
d1 = a5@0x13E * 0x40                                   ; segment_index * 64
0x10D000[i] = strip_src_table[i] + d1     (i = 0..15)  ; 0x0502E4..0x050398
```
`strip_src_table[16]` (verified constants) = `{0x1691C, 0x18BDC, 0x1AE9C, 0x1D15C, 0x1F41C, 0x216DC,
0x2399C, 0x25C5C, 0x27F1C, 0x2A1DC, 0x2C49C, 0x2E75C, 0x30A1C, 0x32CDC, 0x34F9C, 0x3725C}` — the 16
tilemap1 strip-descriptor source tables in ROM (`0x22C0` bytes each). Index `i` = **row-segment**
(`i = row>>2`); the table entry stride is **4 bytes per column-group**.

**(b) Per-group source-cursor advance.** `map_advance_source_ptrs` (`0x0558C6`): each of the 16
`0x10D000[i] += 4` when `10CA==4` (once per column-group). Net `+0x40` per completed ring cycle,
after which `0x13E += 1` (`0x0558E0`). Therefore at column-group `grp` of the current ring cycle:
```
0x10D000[i]  ==  strip_src_table[i] + segment_index*0x40 + grp*4   ==  E(i, grp)
```
This is the identity verified live at runtime (§5, `misD000=0`).

**(c) Descriptor rebuild.** `map_rebuild_and_load_selector` (`0x055904`), fully decoded:
```
for i = 0..15:
    a4 = *(long)(0x10D000[i])              ; the ROM source-base pointer E(i,grp)
    0x10D080[i] = *(u16)(a4)               ; attr / source-control word  (word0)
    0x10D040[i] = *(u16)(a4 + 2)           ; metatile descriptor pointer (zero-extended 16-bit)
```
So `0x10D080[i] = *(u16)(E)` and `0x10D040[i] = *(u16)(E+2)`. The descriptor pointer is a 16-bit
value → the metatile blocks live in low ROM (`< 0x10000`). Verified live (`misDp=0`).

**(d) Cell producer.** `pc080sn_cell_forward` (`0x0559B2`), per sub-cell (`d2 = cell`, row-sub 0..3):
```
word0 = *(a1) = 0x10D080[seg]                                     ; attr
tile  = *(u16)(a2 + (cell<<3) + (strip<<1))     a2 = 0x10D040[seg] ; == dp
coll  = (a2[+32]==0xFF) ? a2[+34] : *(u16)(a2 + 20 + (strip<<1) + (cell<<3))
```
Substituting (c) gives the §1 formula. **None of these reads touch `0xC08000`** — `a0`
(`a5@0x10A0`) is the *destination* only. (Selector-1/2's `0x055A14` uses the same `dp`/`attr` with a
reversed sub-index `sub<<3 + d2<<1`; the SOURCE is identical, see §9.)

**Coordinate identities** (already proven in `Andy_plane_a_selector0_logical_coordinate_proof.md`,
re-used here): `logical_column = 10CC*4 + 10CA`, `logical_row = segment*4 + cell`, collision index
`0x10DE00 + (row*64+col)*2`, C-window cell `0xC08000 + row*256 + col*4` (word0 +0, tile +2).

## 4. Exact arbitrary-cell / arbitrary-row formula

**Arbitrary cell** — see §1. **Arbitrary row** (all 64 cells of `logical_row`, given
`segment_index`):
```
publish_plane_a_logical_row(logical_row, segment_index):
    seg = logical_row >> 2 ; cell = logical_row & 3
    for col in 0..63:
        grp = col >> 2 ; strip = col & 3
        E    = strip_src_table[seg] + segment_index*0x40 + grp*4
        dp   = *(u16)(E + 2) ; attr = *(u16)(E)
        tile = *(u16)(dp + (cell<<3) + (strip<<1))
        coll = (*(u16)(dp+32)==0x00FF) ? *(u16)(dp+34)
                                       : *(u16)(dp + 20 + (cell<<3) + (strip<<1))
        emit final Plane A name word = convert(tile, attr) into staged_fg_buffer[logical_row & 31][col]
```
`convert(tile, attr)` is the **already-implemented, palette-correct** selector-0 conversion in
`genesistan_hook_tilemap_plane_a_selector0_native` (Build 0246 proved its palette/attr routing). This
proof establishes the previously-open half — the **source** `(tile, attr, coll)` — not the
conversion, which was already settled.

## 5. Runtime proof (arcade oracle, `0xC08000` as oracle only)

**Method** (`arb.lua`, MAME `rastan` 0.276, headless): boot, coin, 1-player start, **no gameplay
input**. Tap the selector-0 collision store `0x0559EC` during the Stage-1 initial fill. For each
`(row,col)` verify the live descriptor tables equal the constant recompute `E(seg,grp)`. Three frames
after the 64th publication, sweep all 4096 `(row,col)` and compare the ROM-only `tile` formula to the
actual `0xC08000` tile the arcade wrote.

**Headline numbers (`arb.txt`):**
- `FILLSTART F=239 segment_index=0 stage=0 selector=0` — Stage-1 fill runs at `seg_index=0`, sel-0.
- `FILLDONE F=252 pubN=64` — full 64×64 captured; `segment_index` constant (0) throughout the fill.
- **`ORACLE_SUMMARY cells=4096 mismatch=0`** — every ROM-derived tile equals the `0xC08000` tile.
- **`LIVE checks=4096 misD000=0 misDp=0 misTile=0`** — `0x10D000[seg]==E`, `0x10D040[seg]==*(u16)(E+2)`,
  and the recomputed tile matched, for every cell.

**Sampled cells** (5 columns × 18 rows; `match=true` for all 90; `c08_w0=0x0003` uniformly):

| row | col | seg | cell | grp | strip | E | dp | rawtile | attr | C08000 tile | match |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|
| 0 | 0 | 0 | 0 | 0 | 0 | 0x1691C | 0x20FC | 0x041C | 0x0003 | 0x041C | ✓ |
| 0 | 32 | 0 | 0 | 8 | 0 | 0x1693C | 0x1000 | 0x0020 | 0x0003 | 0x0020 | ✓ |
| 16 | 0 | 4 | 0 | 0 | 0 | 0x1F41C | 0x20FC | 0x041C | 0x0003 | 0x041C | ✓ |
| 31 | 0 | 7 | 3 | 0 | 0 | 0x25C5C | 0x20FC | 0x0428 | 0x0003 | 0x0428 | ✓ |
| **33** | **0** | 8 | 1 | 0 | 0 | 0x27F1C | 0x20FC | 0x0420 | 0x0003 | 0x0420 | ✓ |
| **40** | **0** | 10 | 0 | 0 | 0 | 0x2C49C | 0x2048 | 0x00CC | 0x0003 | 0x00CC | ✓ |
| **40** | **4** | 10 | 0 | 1 | 0 | 0x2C4A0 | 0x2024 | 0x00BD | 0x0003 | 0x00BD | ✓ |
| **47** | **0** | 11 | 3 | 0 | 0 | 0x2E75C | 0x2048 | 0x00DC | 0x0003 | 0x00DC | ✓ |
| **48** | **0** | 12 | 0 | 0 | 0 | 0x30A1C | 0x2048 | 0x00CC | 0x0003 | 0x00CC | ✓ |
| **54** | **0** | 13 | 2 | 0 | 0 | 0x32CDC | 0x2048 | 0x00D8 | 0x0003 | 0x00D8 | ✓ |
| **54** | **63** | 13 | 2 | 15 | 3 | 0x32D18 | 0x2048 | 0x0123 | 0x0003 | 0x0123 | ✓ |

**Empty vs. visible terrain (both covered):** empty cells derive `rawtile=0x0020` via descriptor
`dp=0x1000` (48 of the 90 samples); visible terrain/floor cells derive `rawtile ∈
{0x00CC,0x00DC,0x00D8,0x00BD,0x00C0,0x041C,0x0420,0x0428,0x0112,0x0123,0x0125}` via terrain
descriptors `dp ∈ {0x20FC,0x2048,0x2024,0x28C8,0x2A88,...}`. The visible floor band sits at
**logical rows ≈ 31–55** (segments 7–13) — i.e. the rows the 32-row ring is starved of after the
pan (root cause of the initial-fill defect), and they are **fully derivable at `seg_index=0`**.

**Collision note:** where the descriptor sentinel `*(u16)(dp+32)==0x00FF` (e.g. `dp=0x20FC`), the
producer takes the `dp+34` branch; the sampled `coll` column shows the non-sentinel branch value,
while the collision word actually written by the arcade (captured as `collVal`) is the `dp+34` value
(e.g. `0x0001`). Either way the collision **value** is a sentinel-gated read of the same ROM-derived
descriptor block `dp`, and the collision **destination** is the logical index
`0x10DE00 + (row*64+col)*2` (proven in the selector-0 coordinate proof). Collision is therefore also
fully derivable from `(row, col, segment_index)`.

## 6. Classification of `0x10D000`, `0x10D040`, `0x10D080`

| Structure | What it holds | Classification | Final-path disposition |
|---|---|---|---|
| **`0x10D000`** (16 longs) | source-position cursor `= strip_src_table[i] + seg_index*0x40 + grp*4` | **Semantic source-position cursor.** Describes *where in the original Rastan map ROM to read* for row-segment `i` at the current map column. **Not** a PC080SN destination. Derivable from `(seg_index, grp)`. | Retain **or bypass** (recompute `E`). Allowed. |
| **`0x10D040`** (16 longs) | metatile descriptor pointer `= *(u16)(0x10D000[i]+2)` | **Transitional per-column working cache** of the ROM metatile pointer. Semantic content (points at the original metatile block in low ROM). Rebuilt each group by `0x055904`. **Not** chip name-RAM. | Bounded recompute allowed; cache permitted under policy §7 cache rule. |
| **`0x10D080`** (16 words) | attr / source-control word `= *(u16)(0x10D000[i])` | **Transitional per-column working cache** of the ROM attribute word. Semantic. | Same as `0x10D040`. |

**None of the three reconstruct PC080SN destination / name-RAM behavior.** The *only* chip-destination
state is `a5@0x10A0/0x10A4` (the `0xC08000` cursor) + the word0/word1 name-RAM pairing + C-window
strides — those are the removal targets and do **not** appear in the source formula. Per the task's
"important distinction": these structures are retained because they **describe original map content**,
not because "the arcade also used them while feeding PC080SN."

**Highest semantic source:** the 16 ROM strip-descriptor source tables (`0x1691C..0x3725C`, `0x22C0`
each) + the metatile descriptor blocks in low ROM (`< 0x10000`), indexed by
`(segment_index, row-segment, column-group, cell, strip)` — i.e. the original Rastan Stage map.

## 7. Are the descriptor tables semantic or transitional?

**Transitional caches of a semantic source.** `0x10D040`/`0x10D080` are provably a per-column rebuild
of `*(u16)(E+2)` / `*(u16)(E)`. They are valid only for the currently-rebuilt column, so as a
*standing structure* they are transitional; but their *content* is semantic (ROM map data), so a
native path may either (a) recompute `E` directly and skip the tables, or (b) keep them as a bounded
per-column cache under the policy §7 cache rule. They are **not** a chip name-RAM shadow.

## 8. Initial-pan native publisher boundary

**Source availability during the pan: PROVEN.** The pan does not complete a ring cycle (it publishes
nothing — Case B of the fill audit), so `a5@0x13E` stays at the fill value (`seg_index=0`).
Therefore every entering logical row 33–54 the 32-row ring needs is derivable *right now* at
`seg_index=0` by `publish_plane_a_logical_row(row, 0)` — exactly the cells the oracle reproduced.
An **edge-row publisher is viable**; a one-time full-window reseed is not required by the source
evidence (task condition satisfied to prefer edge-row publication).

**Helper contract** (bounded, arcade returns immediately):
```
publish_plane_a_logical_row(logical_row):
    seg_index = a5@0x13E                      ; arcade-owned semantic scalar
    movem save all non-owned registers        ; Build 0240 discipline
    for col in 0..63: derive (tile, attr) per §4 ; convert; write staged_fg_buffer[logical_row & 31]
    optional: write collision side-channel by logical index (already produced by arcade — see §11)
    mark fg_row_dirty bit (logical_row & 31) ; movem restore ; rts
```

**Highest safe call boundary.** The scripted pan exposes **no arcade publication event** to intercept
(selector-0, ring static, no dispatch — proven Case B). Two admissible trigger sites, in order of
preference:
1. **The arcade's own vertical-scroll write that drives the pan** — the highest *original-arcade*
   boundary. The fill audit established the pan updates the foreground camera Y without a producer
   dispatch; the *exact* pan-Y writer instruction was not pinned (the pan is a scripted selector-0
   camera move, not the `0x055718/0x0557A4` gameplay path). Pinning that writer is a narrow
   implementation-scoping step (§11), **not** a source blocker.
2. **A Genesis-side `visible_top` 8-px crossing detector reading the arcade-owned `staged_scroll_y_fg`**
   — Build 0246 already computes `visible_top = ((-staged_scroll_y_fg + 8) & 0x1FF) >> 3 & 0x3F`.
   Reacting to a crossing by calling the helper is a bounded entering-row publication driven by the
   arcade's own camera value; it is **not** a Genesis camera scheduler (the arcade still owns the
   camera, the scene, and `seg_index`). This is the safe fallback if (1)'s writer is not cleanly
   hookable.

Either way the published rows come from `seg_index` + ROM — no `0xC08000`, no chip image.

## 9. Relationship to selector-1/2

**Selector-1/2 can share the same semantic source: YES.** The selector-1/2 helper
(`genesistan_hook_tilemap_plane_a_selector12_native`, `0x0007061A`) currently consumes the rebuilt
`0x10D040/0x10D080` tables — which this proof shows are `*(u16)(E+2)` / `*(u16)(E)`, i.e. the *same*
ROM-derived source, cached. Its cell producer (`0x055A14`) reads `tile`/`coll` from the same `dp` with
a reversed sub-index. Therefore:

- **Target:** both the initial-pan publisher and ordinary selector-1/2 movement call **one** semantic
  row routine that derives cells from `strip_src_table[seg] + seg_index*0x40 + grp*4` (the
  Rainbow-Islands/Sonic-1 dual-axis wrapped-map model). This unifies vertical publication.
- **Now:** the existing selector-1/2 helper is a correct **event-local wrapper** around that source
  (its descriptor-table dependency is a semantic-source cache, not a chip dependency), so it can be
  refactored to call the shared routine rather than replaced wholesale. Its rebuilt tables are
  **transitional** (a cache), not the authority.

Ordinary down/up/reversal *runtime* alignment (which Cody could not reach) remains a **later
validation** task; it is not a prerequisite for the source proof, and the source formula already
covers arbitrary rows the movement path would request.

## 10. Architecture classification and compatibility

- **Compatibility layer required: NO.** No software PC080SN, no name-RAM shadow, no 64×64 mirror, no
  tall-buffer projector, no chip-address decoding, no Genesis renderer/scheduler.
- **Architecture:** `original Rastan semantic map decision (seg_index + ROM tables) → bounded native
  Genesis row publication (publish_plane_a_logical_row) → final Plane A name words → existing dirty-row
  + VBlank commit → native HSCROLL/VSRAM`. Compliant with the native-replacement policy and the
  dual-axis wrapped-map target.

## 11. Smallest safe Cody implementation task (only because the source is proven)

**Prerequisite met:** arbitrary row/cell source is proven (§1–§5); STOP is **not** triggered.

Recommended next Cody task (narrow, implementation-scoping — still analysis-heavy, gated):
1. **Pin the arcade pan-Y writer** (the instruction that ramps the foreground camera Y during the
   Stage-1 scripted settle) via a JSON-mapped runtime trace, to select boundary (1) of §8; if it is
   not cleanly hookable, adopt boundary (2) (the `visible_top` crossing detector).
2. **Prototype `publish_plane_a_logical_row(logical_row)`** deriving cells directly from
   `strip_src_table[seg] + seg_index*0x40 + grp*4` (bypassing the live cache), reusing the proven
   selector-0 `convert(tile, attr)`, with full `movem` register discipline; call it for each entering
   row 33–54 during the pan.
3. **Collision:** do **not** duplicate — the arcade collision producer already fills
   `0x10DE00 + (row*64+col)*2` for all 64 rows during the fill; the publisher writes Plane A only
   unless a later semantic event requires a collision update.
4. Byte-neutrality and register discipline per Build 0240; validate the initial fill visually and by
   re-running this oracle (expect `mismatch=0`).

Do **not** implement the vertical publisher before pinning the trigger boundary (step 1); the SOURCE
is proven, the TRIGGER site is the remaining scoping item.

## 12. STOP status

**STOP not triggered.** The logical row and column trace back to semantic stage data with **0
mismatches over 4096 cells** (including rows 33–54); no first missing relationship remains on the
source question. Per the task, selector-1/2 runtime unavailability is explicitly *not* a STOP reason.
No `0xC08000` production dependency, no shadow/projection/compatibility decoding proposed.
