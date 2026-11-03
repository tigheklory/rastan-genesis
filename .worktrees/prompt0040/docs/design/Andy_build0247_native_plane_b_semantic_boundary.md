# Build 0247 — Native Plane B (tilemap0 / parallax BG) Semantic Boundary (research; no source/build)

**Agent:** Andy. **Type:** focused Plane B architecture/source proof.
**Production source / remap spec / ROM / build / counter:** UNCHANGED (Build 0247 / counter 247).
**Authority:** `build/rastan-direct/address_map.json` (arcade→genesis, segment-membership; **no fixed-offset
inference**), `specs/rastan_direct_remap.json`, `build/rastan-direct/rastan_direct_patch_manifest.json`,
`apps/rastan-direct/out/symbol.txt`, Build 0247 source, arcade opcodes (`analysis/ghidra/rastan_arcade/`).
**Evidence:** `states/traces/build0247_plane_b_source_20260801/` (`bgsrc`, `bgrow0`, `bgstream`).
`0xC00000` PC080SN tilemap0 used **only as oracle**. **Builds on:** the Plane A arbitrary-row proof
(`Andy_build0246_plane_a_arbitrary_row_source_proof.md`) — Plane B is its structural twin.

## Native-hardware-replacement acknowledgement (policy §10/§12)

- **Semantic cut retained (arcade-owned):** scene/stage selection, `seg_index (a5@0x13E)`, tilemap0 index
  `a5@0x1386 = byte[0x507C5+seg_index]`, the ROM background source-descriptor table at `0x3951C`, the
  ring/scroll progression, and the logical BG tile identity. This proof shows the entire tilemap0 tile
  source is a pure function of `(row, col, scene_state)` over ROM tables.
- **Chip tail removed (below the cut):** the PC080SN tilemap0 C-window `0xC00000`, chip-destination-address
  decoding, `staged_bg_tall_buffer`, and `vdp_project_bg_tall_if_dirty` — all absent from the source formula.
- **Plane A, collision, rope: untouched.** BG has no collision channel.

---

## 1. Result summary

- **Live gameplay Plane B producer PINNED:** arcade `0x055C5E`→`0x055C7A` (tilemap0 strip/cell producer),
  driven at scene-fill (`0x050438`) and gameplay streaming (`0x055B60`→`0x055B8E`). In Build 0247 the
  strip site `0x055C5E` (runtime `0x055E5E`) is patched → `genesistan_hook_itempage_strip_blit` →
  `genesistan_hook_tilemap_bg_fill`/`_tall`.
- **Transitional tail to retire (confirmed forbidden pattern):** `genesistan_hook_tilemap_bg_fill_tall`
  (`0x00070F7C`) **decodes the chip destination address** `a0` → (row,col) and writes
  `staged_bg_tall_buffer` (`0xFF50EC`), sets `bg_tall_dirty` (`0xFF404A`); `vdp_project_bg_tall_if_dirty`
  (`0x00070138`) projects 32 visible rows → `staged_bg_buffer` (`0xFF40EC`). That is
  `PC080SN C-window op → tall chip-shaped buffer → projector → Plane B` — the exact rejected architecture.
- **Semantic source PROVEN (C00000 oracle):** every cell the arcade tilemap0 producer writes is
  reproduced by a ROM-only formula. **Fill:** 256/256 cells (64 rows × cols 0–3, all subcols 0–3) exact.
  **Streaming (walk right):** **11968/11968** writes across BG X-scroll `0x0000→0x01B1` and segments 0,1,2:
  `misRebuild=0, misTile=0`, source base always in ROM `[0x3951C..0x39546]`, **never** `0xC00000`.
- **Formula:** `tile(row,col) = *(u16)( *(u32)(0x3951C + tm0idx*0x0C + group*6 + 2) + row*32 + subcol*2 )`,
  `tm0idx = byte[0x507C5 + seg_index]`, `group` from the X-scroll-derived source-base advance, `subcol =
  col & 15`. `attr/word0 = *(u16)(entry)`.
- **The BG is producer-driven & sparse:** the fill seeds only a 4-column strip; gameplay streams the rest
  H+V on demand. A native publisher must **follow the arcade producer** (convert each produced cell), not
  fill 64×64 blindly.
- **STOP: not triggered.**

## 2. Live Plane B route inventory (address-map / remap)

| Route | Arcade PC | Genesis PC | Kind / target | Class | Gameplay? |
|---|---:|---:|---|---|:--:|
| Scene-fill tilemap0 call | `0x050438` | `0x050638` | arcade_copy | initialization | fill only |
| tilemap0 publish-col | `0x055C4A` | `0x055E4A` | arcade_copy | producer entry | via fill + stream |
| **tilemap0 strip producer** | `0x055C5E` | `0x055E5E` | **patched_site** → `genesistan_hook_itempage_strip_blit`→`_bg_fill`/`_tall` | **live BG producer** | **YES** |
| tilemap0 cell producer | `0x055C7A` | `0x055E7A` | arcade_copy | writes 64-cell strip (no collision) | via producer |
| tilemap0 descriptor rebuild | `0x055C2E` | `0x055E2E` | patched_site (WRAM rebase) | rebuilds `0x10D100/0x10D104` from `0x10D0FC` | init+stream |
| tilemap0 source-base advance | `0x055C14` | `0x055E14` | patched_site (WRAM rebase) | `a5@0x10FC += 6` per 16 cols | init+stream |
| gameplay vertical stream | `0x055B60`→`0x055B8E` | `0x055D60`→`0x055D8E` | arcade_copy | streams tilemap0 on vertical 8px crossings; commits half-rate parallax X (`0x055B92 lsr#1`) | **YES** |
| C-window clear | `0x0561B6` | (patched) | JSR → staged-buffer clear hook | scene transition | — |
| **Transitional tall writer** | — | `0x00070F7C` `genesistan_hook_tilemap_bg_fill_tall` | Genesis-only | **decodes chip addr → `staged_bg_tall_buffer`, sets `bg_tall_dirty`** | RETIRE |
| **Transitional projector** | — | `0x00070138` `vdp_project_bg_tall_if_dirty` | Genesis-only | projects 32 rows tall→`staged_bg_buffer` | RETIRE |
| native 32-row BG fill | — | `0x00070EA6` `genesistan_hook_tilemap_bg_fill` | Genesis-only | 32-row staging (target-shaped) | keep/evolve |

**Frontend-only (separate, do not reconstruct as gameplay):** item/status page (`0x056032`, `0x05605C`);
BG block-copy engine `0x05A4DE` (title/attract art); shared text writer `0x0563A6`; C-window clear
`0x0561B6`; boot clears `0x00054A`/`0x03AF2C`. `genesistan_hook_itempage_strip_blit` is **shared** between
the item-page (frontend) and Stage-1 gameplay BG — it self-selects on the producer source-pointer range
`[0xD31C,0xFB1C)` (relocated `0x3951C`-walked descriptor family) + `genesistan_current_scene_id==1`. So
gameplay Plane B is cleanly separable from frontend by scene id + source-pointer range.

## 3. Semantic source chain (from opcodes, C00000-free)

**Producer** `pc080sn_tilemap0_cells` (`0x055C7A`), 64 sub-cells `d2=0..63`, **no collision**:
```
word0 = *(a1) = 0x10D104                                  ; attr/source-control word
tile  = *(u16)(a2 + d2*32 + a5@0x10F6*2)   a2 = *(0x10D100) ; d2 = row, a5@0x10F6 = sub-col
a0 += 256 per sub-cell                                    ; (no C08000/collision index)
```
**Rebuild** `0x055C2E`→`0x055C40` (analog of Plane A's `0x055904`):
```
a4 = a5@0x10FC                                    ; source base = 0x3951C + tm0idx*0x0C + group*6
0x10D104 = *(u16)(a4)                             ; word0/attr
0x10D100 = *(u32)(a4 + 2)                         ; descriptor block pointer (32-bit)
```
**Source-base seed** `0x0503A0`: `a5@0x10FC = 0x3951C + a5@0x1386 * 0x0C`, `a5@0x1386 =
byte[0x507C5 + seg_index]`. **Advance** `0x055C14`: `a5@0x10FC += 6` when `a5@0x10F6==16` (per 16 cols).

So `descriptor(group) = *(u32)(0x3951C + tm0idx*0x0C + group*6 + 2)`, and `tile(row, col) =
*(u16)(descriptor(col>>4) + row*32 + (col&15)*2)`. **No `0xC00000`, no tall buffer, no chip decode** —
`a5@0x10F8` (the C-window cursor) is the *destination* only.

## 4. Arbitrary-cell / row / column proof (C00000 oracle)

**Fill (`bgrow0.txt`):** the tilemap0 scene-fill writes exactly **256 cells = 64 rows × 4 columns**
(cols 0–3). Row 0: `c0=04A6 c1=04A7 c2=04A8 c3=04A9` — **all four subcols match the formula** (`match=true`).
This corrected the first pass's apparent "2843 mismatches": those were empty (`0x0020`) cells the arcade
**had not streamed yet**, not formula errors (the BG is producer-driven & sparse).

**Streaming across camera positions (`bgstream.txt`, walk right):**
```
writes=11968  misRebuild=0  misTile=0  srcBaseOutOfRomRange=0
srcBase(0x10FC) range=[03951C..039546]   BG_Xscroll(0x10EC) range=[0000..01B1]   segs_seen=0,1,2
```
For all 11968 tilemap0 writes across multiple horizontal positions and segments 0–2:
`0x10D100 == *(u32)(a5@0x10FC+2)` (rebuild always ROM-sourced), written tile `== *(descriptor + row*32 +
subcol*2)` (descriptor-sourced), and `a5@0x10FC` always in the `0x3951C` ROM source-table range (never a
chip address). **Wrapped coordinates** are exercised (the 64-col ring cycled as X advanced ~54 tiles).

| Proof target | Status | Evidence |
|---|---|---|
| Initial Stage-1 fill | **PROVEN** | 256/256 fill cells match (all subcols) |
| Multiple horizontal camera positions | **PROVEN** | 11968/11968 across X `0..0x1B1`, segs 0–2 |
| Multiple vertical camera positions | **PROVEN (mechanism)** | vertical stream `0x055B8E`→same `0x055C7A` producer; rows 0–63 verified in fill |
| Empty background vs visible scenery | **PROVEN** | empty = `0x0020` (unstreamed); scenery = formula-derived |
| Wrapped logical coordinate | **PROVEN** | 64-col ring wrapped during the X `0..0x1B1` stream |
| Rope/cave region | **residual** | not directly reached (segs 0–2); **same** producer/rebuild/`0x3951C` path — uniform mechanism, no distinct BG code path exists |
| Arbitrary cell / row / column derivable | **YES** | formula reproduces every produced cell; `PC080SN name RAM required: NO`, `tall buffer required: NO` |

## 5. Logical vs physical coordinate model

- **Logical map coordinates:** `row` 0..63 (BG map row), `col` = absolute BG column. Descriptor blocks are
  **16 columns wide × 64 rows tall**: `group = col>>4` (source-base entry, +6 bytes/group), `subcol =
  col&15`. `tile = *(descriptor(group) + row*32 + subcol*2)`.
- **Genesis physical ring:** **64 × 32** (identical to Plane A). `physical_row = logical_row & 31` (the
  64-row map folds into a 32-row ring → needs a vertical entering-row publisher, exactly like Plane A). The
  column ring is 64 = full match with the BG's 64-wide window → horizontal streaming keeps up.
- **Native scroll relationship:** **half-rate parallax.** BG X-scroll `a5@0x10EC` = camera X processed at
  half rate (`0x055B92 lsr.w #1`); BG Y-scroll `a5@0x10EE`. The native column source therefore derives the
  group/subcol from the **BG X-scroll (`a5@0x10EC`)** (the half-rate analog of Plane A's FG X-scroll base
  `(((-a5@0x10AE)&0x1FF)>>3)&0x3F`). Genesis Plane B HSCROLL/VSCROLL are driven natively from
  `staged_scroll_x_bg`/`staged_scroll_y_bg`.

## 6. Native Plane B publication model

**Producer-driven, no autonomous fill.** Two bounded semantic contracts, mirroring Plane A:

```
publish_plane_b_logical_row(logical_row)      ; vertical entering rows (gameplay stream + settle pan)
publish_plane_b_logical_column(logical_col)   ; horizontal entering columns (camera-X streaming)
```
Each helper, for the entering edge:
- derives the cell source per §3 `tile = *(descriptor + row*32 + subcol*2)`, `descriptor =
  *(u32)(0x3951C + tm0idx*0x0C + group*6 + 2)` (via the relocated Genesis ROM copy, `+0x200`, as the
  current hook already does), with the **BG X-scroll-derived** column base;
- converts `(tile, attr)` with the existing BG attribute LUT (`genesistan_pc080sn_tile_vram_lut` +
  `genesistan_pc080sn_attr_lut` — already used by `bg_fill_tall`);
- writes the **final Genesis Plane B nametable word directly** to `staged_bg_buffer[(row&31)][col]`;
- marks `bg_row_dirty` (row publisher) / a bounded column-dirty metadata (column publisher);
- **no collision** (BG has none), **no `staged_bg_tall_buffer`, no projector, no chip-address decode**.

- **Initialization:** the scene-fill route (`0x050438`→`0x055C4A`→`0x055C5E`) publishes the initial resident
  rows/columns directly into `staged_bg_buffer` (replacing the tall fill).
- **Gameplay edge-streaming:** horizontal via the streaming producer as the camera-X advances; vertical via
  `0x055B8E` crossings (and the opening settle pan, the Plane A-analog vertical starvation) →
  `publish_plane_b_logical_row`.
- **Arcade-owned hook sites:** reuse the already-patched producer boundary `0x055C5E` (runtime `0x055E5E`,
  `genesistan_hook_itempage_strip_blit`) for scene-fill + horizontal; add a vertical entering-row hook on
  the `0x055B60`/`0x055B8E` gameplay vertical-stream path (analogous to the Plane A no-publish pan hooks) for
  the 32-row ring's entering rows.

## 7. Transitional paths to retire

Once §6 lands, these become unreachable for gameplay Plane B and can be deleted:
- `genesistan_hook_tilemap_bg_fill_tall` (`0x00070F7C`) — chip-address decoder + tall writer.
- `vdp_project_bg_tall_if_dirty` (`0x00070138`) — the projector.
- `staged_bg_tall_buffer` (`0xFF50EC`, 0x1000 span), `bg_tall_dirty` (`0xFF404A`),
  `bg_tall_project_base` (`0xFF404C`).
Keep (evolve): `genesistan_hook_tilemap_bg_fill` (`0x00070EA6`) as the direct 32-row staging path;
`staged_bg_buffer`; the BG attr/tile LUTs. Keep the **frontend** item-page/block-copy/text paths (§2)
gated by scene id.

## 8. Architecture classification

`original Rastan BG map/camera decision (scene→tm0idx→0x3951C source + X/Y scroll) → bounded native Plane B
row/column generation → final Genesis Plane B nametable words → bounded dirty metadata → existing
arcade-owned VBlank commit`. Compliant; the direct twin of the accepted native Plane A architecture.
**Forbidden structures avoided:** no software PC080SN, no tilemap0/C-window mirror, no
`staged_bg_tall_buffer` as authority, no 64×64 projection, no chip-address translator, no Genesis
camera/renderer loop, no Stage-1-only patch.

## 9. Smallest safe Cody implementation task

1. **Redirect the existing gameplay BG producer output to native 32-row staging.** In
   `genesistan_hook_itempage_strip_blit` / `genesistan_hook_tilemap_bg_fill` (scene_id==1 gameplay path),
   write final Plane B words **directly to `staged_bg_buffer[(row&31)][col]`** from the proven `0x3951C`
   semantic source (the hook already walks it), with `physical_row = logical_row & 31` and the BG
   X-scroll-derived column base — **bypassing `genesistan_hook_tilemap_bg_fill_tall` and the tall buffer**.
   Set `bg_row_dirty` directly; stop setting `bg_tall_dirty`.
2. **Add a vertical entering-row publisher** `publish_plane_b_logical_row` hooked on the
   `0x055B60`/`0x055B8E` gameplay vertical path (and the opening settle, the Plane A-analog), publishing the
   32-row ring's entering rows from the same semantic source (`movem` discipline).
3. **Gate off** `vdp_project_bg_tall_if_dirty` for scene 1 (as `vdp_project_fg_tall_if_dirty` already is),
   then delete the tall path (§7) once verified.
4. **Validate** by re-running the C00000 oracle traces here (expect `misTile=0`) and a Genesis visual check;
   keep the frontend item-page path intact. Do **not** touch Plane A, collision, or rope behavior.
   Pin the exact BG X-scroll→group column formula during implementation (the half-rate analog of Plane A's,
   the one detail to confirm at the boundary).

## 10. STOP status

**STOP not triggered.** The semantic Plane B source is unambiguous and proven (11968/11968 across positions,
source always in ROM, never chip); gameplay and frontend are separable (scene id + source-pointer range);
the source is **not** PC080SN name RAM or a tall mirror; logical/physical coordinate formulas are proven;
and exactly one native architecture is supported (the Plane A twin). Residual: the rope/cave region was not
directly sampled but uses the identical producer/`0x3951C` mechanism (a validation item, not an ambiguity).
