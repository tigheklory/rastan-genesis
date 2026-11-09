# R1-S2 Traps — Proven Sources, Fully Authorable (replaces disabled placeholders)

**Date:** 2026-11-06 · **Author:** Andy · **Scope:** `tools/graphics_editor` + bestiary

Tighe asked (earlier) for four traps — **floor spike, flame, water, ceiling/suspended spike** — to be
added to the palette tool. The previous attempt shipped **disabled "SOURCE SUBSET PENDING" placeholders**
(`authorable=False`, `base=None`, no colours). That was not completing the task. This pass resolves every
trap to a **proven arcade source** and makes all four **authorable, palette-mappable objects**. No
placeholders, no fabricated codes.

## What each trap actually is (proven from the arcade program)

## CORRECTION (2026-11-06, after Tighe review): flame & water are REAL TILES, not palette-only

The first version of this work shipped Pit Flame and Falling Water as **palette-only** objects (swatch strips,
no pixels). **That was wrong.** Tighe caught it: "no tiles are included." A palette cycle animates pixels that
already exist in VRAM — the tiles are authored graphics that must be included. They are now decoded from the
PC080SN character ROM and rendered as true tile composites. See the corrected table.

| Trap | Hardware | Proven source | Evidence |
|---|---|---|---|
| **Floor Spike** | PC090OJ sprite | graphics base `$09EA`, compositor anim `0x79` (up-pointing spike column) | `0x09EA` = spike/spear/stalagmite family, Tighe HUMAN IDENTITY (PROMPT-0086). Rendered by the compositor VM `0x3D054`. 9 pieces. |
| **Ceiling Spike / Crusher** | PC090OJ sprite | graphics base `$09EA`, compositor anim `0xD8` (overhead chain + spiked head) | The chained block that descends to crush the player (the R1-S2 "trap door"). Same family, different form. 10 pieces. |
| **Pit Flame** | **PC080SN Layer-A tiles** | tiles **`$093A–$0949`** (4×4 unit), palette **bank `0x014`**, screen rows 28–31, record 18 | Decoded from `build/regions/pc080sn.bin` via the R1-S2 scene corpus. Rendered → clearly flames (orange→yellow→white). The flicker is the **mode-8** palette cycle (cycler `0x59962` → loader `0x59AD4`, table `$59B1A`, CRAM line `0x14`) over these fixed tiles. The PC090OJ base-`$0224` pit-flame actor is a *separate* R2/R4 marker actor (retired in R1-S2), **not** the R1-S2 flames. |
| **Water Pit** (standing pool) | **PC080SN Layer-A tiles** | bank **`0x01F`** teal/cyan tiles (pool `$24BB–$24C2` + submerged channel `$24C3–$24CA`), rows 52–63, record 20 | Decoded from the character ROM. Animated by the **mode-9** palette cycle (dest lines `0x1A–0x1D`). This is the floor **pit**, not the falling streams. |
| **Falling Water** (streams) | **PC090OJ sprite** (base source-pending) | animated on CRAM lines **`0x1A–0x1D`** (mode-9, table `$59AA4` stage 1); sprite banks `0x1A`/`0x1B` hold the cyan colours | Proven to be a sprite, not Layer A (the only cyan Layer-A bank is the pit; `0x1A–0x1D` are sprite lines). Graphics base not yet pinned — resolve by an arcade PC090OJ sprite-RAM capture. **Not authored** until then. See `Andy_r1s2_trap_graphics_sources.md` §4b. |

### How the tile sources were proven (arcade evidence, not tracing)

- Background tilemap path: per-round map `0x562CA[round]` → decompressor `0x563A6` → PC080SN name table
  (`analysis/decompilation/c/rastan_scene_map.c`). The castle Layer-A corpus
  (`analysis/graphics_optimizer/subround_corpus/PAL-R1-S2-PLANEA-CASTLE/plane_a_uses.json`) records every tile
  code, palette bank, flip, and tilemap coordinate for the scene.
- Bank `0x014` = 16 usages, tiles `$093A–$0949`, rows 28–31 (screen bottom = the lava pit), warm fire colours —
  and `0x14` is exactly the mode-8 fire CRAM dest line. Decoding + rendering the 4×4 unit shows flames.
- Bank `0x01F` = 25 usages with teal/cyan colours `[0,115,132]…`, rows 52–63. Decoding the repetition unit shows
  the water pool + submerged channel (the **pit**). Its colours are not in any other Layer-A bank. The separate
  **falling-water streams** are a PC090OJ sprite on mode-9 lines `0x1A–0x1D` (base source-pending), not this.
- The `0x09EA` ceiling form (anim `0xD8`) renders as the chained spiked block = the descending crusher in the
  R1-S2 castle screenshots. There is **no** separate sprite "top row" for the fire pit: record 18 has tiles only
  at rows 28–31 (the fire), nothing above. The one R1-S2 marker-spawned sprite (the 'M' burst, `0x43ECC`,
  anim `0x7A`) is a coordinate-only 5-child burst with no static base — not a fire cap or a crusher.

### How the spike/flame identity was proven distinct

The compositor VM computes `tile = base_graphics + tile_delta` (compositor_vm.py). Flame base `0x0224` and
spike base `0x09EA` **share one animation program table** (identical frame geometry across all 256 anims)
but point at **different VRAM tile graphics** (offset `0x7C6`). So they are genuinely different art with the
same motion vocabulary — not the same object. The two spike forms use **different palette nibbles**
(floor `0x79` → nibble 13, suspended `0xD8` → nibble 6), i.e. different arcade palette lines, which is why
they are two authorable objects, not one.

## Implementation (corrected — real tiles)

**`tools/graphics_editor/server.py`**:

- `_layera_trap_tiles(scene, bank_hex, period, row_lo, row_hi)` — decodes ONE arcade repetition unit of a
  Layer-A animated-hazard block from the scene corpus. Each tile is placed from its real tilemap
  `coordinate_samples` (gx = col % period, gy = row − row_lo), **not** a guessed order, so the assembled block is
  geometrically faithful. Returns the tiles, the 16-colour arcade bank palette, `used_colors` keyed on the real
  tile nibble index, and pixel bounds.
- `render_layera_block(tiles, pal, boundaries)` + `layera_block_hitmap(tiles)` — the 8px analogue of
  `render_composite` / `composite_hitmap`: decode each tile 4bpp (`tile_indices8`), draw at its 8px slot with
  H/V flips, index the 16-colour palette (arcade bank for the source image, mapped Genesis palette for the
  target). The hitmap drives pixel-pick.
- `hazard_trap_usages()` — the four authorable traps. Spikes = PC090OJ composites (`_manifest_vm_pieces` +
  `_castle_used_colors`). Fire/water now carry `plane_tiles` + `bank_palette` + `layera_tiles:True` +
  `composite_proven:True`; `used_colors` are the real tile colours. The dead `_anim_pal_distinct_colors` /
  `_palette_anim_used_colors` palette-only helpers were removed.
- `/api/render` and `/api/hitmap` render `plane_tiles` through the Layer-A block renderer — so the existing
  sprite preview path (arcade image + mapped-target image + pixel-pick) works unchanged for the tile traps.

**`tools/graphics_editor/app.js`** — `renderPreviews()`: the old `palette_animation` swatch-strip branch is
gone; an object with `plane_tiles` now flows through the normal **TRUE ARCADE COMPOSITE** + **GENESIS TARGET**
image path (same `/api/render?usage=…[&target=…]` contract as a sprite). The pending gate now treats
`plane_tiles` as real art. Preview labels say "tiles" for Layer-A objects. `node --check` passes.

**Why tiles, not palette-only:** a palette cycle animates pixels that already exist in VRAM. The flame and water
pixels are authored PC080SN background tiles; shipping only the palette (no pixels) was the mistake Tighe
rejected. The colours still map onto a Genesis line exactly as before — now over the real decoded graphics.

## Verification

- `hazard_trap_usages()` → 4 objects, all `authorable=True`, all with real graphics: Floor Spike (9 pieces/
  7 colours), Ceiling Spike / Crusher (10 pieces/8), **Pit Flame (16 Layer-A tiles/15 colours)**, **Water Pit
  (36 Layer-A tiles/11 colours)**. (Falling Water = a PC090OJ sprite, base source-pending — not authored yet.)
- `/api/render` returns a real PNG for all four (spikes via `render_composite`, flame/water via
  `render_layera_block`); `/api/hitmap` returns a per-pixel source-index buffer for all four. Verified over HTTP:
  arcade image + mapped-target image + non-empty hitmap for both tile traps.
- `verify_0091_handoff.py` **25 PASS** (HZ1 now asserts real graphics: 2 `$09EA` spike sprites with `pieces` +
  2 Layer-A tile traps with non-empty `plane_tiles` and `composite_proven`).
- `verify_0092_bestiary_artifact.py` **28 PASS**, `verify_0098_r1_boss_green_knight.py` **39 PASS**,
  `verify_r1s2_castle_browser.py` **15 PASS**.
- **`Test.json` byte-unchanged** in every verifier — this is tool/authoring surface only; no production ROM,
  CRAM, build counter, or palette-decision registry was mutated.

## Bestiary

Per the living-bestiary rule, `build_bestiary.py`'s R1-S2 hazard block now states the corrected reality
(fire/water = real PC080SN Layer-A tiles, spikes = PC090OJ sprites, the crusher = the chained descending
block), and the HTML was regenerated on disk (`consistency_check: PASS`, 39 actors,
`docs/design/rastan_actor_bestiary.html`).

## No scaffolding

No temporary production scaffolding was added. All new code is durable tool code in the established
`tools/graphics_editor` surface, reusing the existing compositor VM, per-round palette decode, and
`used_colors`/derive pipeline. Nothing to remove.
