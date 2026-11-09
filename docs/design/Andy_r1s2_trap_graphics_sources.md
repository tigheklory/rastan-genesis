# R1-S2 Castle Trap Graphics — Proven Arcade Sources

**Author:** Andy · **Date:** 2026-11-06 · **Scope:** the interactive traps of the Round 1 castle
(sub-round 2, scene `PAL-R1-S2-PLANEA-CASTLE`) — floor spike, ceiling spike / crusher, pit flame, water pit,
and falling water.

> **Correction note (2026-11-06):** an interim version of this work labelled the bank-`0x01F` Layer-A tiles
> "Falling Water". That is the **water pit** (the standing pool in the floor). The **falling water** (the
> cyan streams that drop from above) is a *separate* graphic and is a **PC090OJ sprite**, not Layer A — see
> §4b. Two different things; both are documented below.

This is the authoritative reference for **what hardware draws each R1-S2 trap and where its graphics live in
the arcade program**. It exists because an earlier pass mis-modelled the pit flame and falling water as
"palette-only" effects with no pixels. That was wrong: a palette cycle animates tiles that already exist in
VRAM. Every trap below is now backed by decoded graphics from the original arcade ROM, proven by static
analysis (Ghidra decompilation + the arcade character ROM + the scene tilemap corpus) — not by runtime tracing.

Colour authority remains `specs/palette_decisions.json`; this document cites palette **banks** by id (a
graphics attribute) and does not reproduce any index→RGB mapping.

---

## 1. The five traps at a glance

| Trap | Hardware | Graphics source | Count |
|---|---|---|---|
| **Floor Spike** | PC090OJ sprite | base `$09EA`, compositor anim `0x79` | 9 pieces |
| **Ceiling Spike / Crusher** (descending "trap door") | PC090OJ sprite | base `$09EA`, compositor anim `0xD8` | 10 pieces |
| **Pit Flame** | **PC080SN Layer-A tiles** | tiles `$093A–$0949`, palette bank `0x014`, screen rows 28–31 (record 18) | 16 tiles (4×4) |
| **Water Pit** (standing pool) | **PC080SN Layer-A tiles** | palette bank `0x01F` (pool surface `$24BB–$24C2` + submerged channel `$24C3–$24CA`), rows 52–63 (record 20) | 36 tiles (4×12 unit) |
| **Falling Water** (streams) | **PC090OJ sprite** | animated on CRAM lines `0x1A–0x1D` (mode-9, table `$59AA4` stage 1). **Sprite base source-pending.** | — |

The split is the key point: pit flame and the water pit are fixed **background tiles** (PC080SN) whose colours
are animated by a palette cycle; the two spikes and the **falling water** are **sprites** (PC090OJ). Only the
falling-water sprite's graphics base is still unresolved (its palette is proven — see §4b).

---

## 2. The two spikes — PC090OJ sprites (base `$09EA`)

Base `$09EA` is the **spike / spear / stalagmite** family (Tighe HUMAN IDENTITY, PROMPT-0086). It is a single
marker-chain transform base whose visible *form* is selected by the entering marker + band + compositor index,
rendered by the compositor VM (`0x3D054` → `0x3C902`). Two forms are authored:

- **Floor Spike** — compositor anim `0x79`: the up-pointing floor spike / spear column.
- **Ceiling Spike / Crusher** — compositor anim `0xD8`: an overhead chain + spiked head. This is the block
  that **descends on its chain to crush the player** — the chained "trap door" crusher seen in the R1-S2
  castle. Rendering anim `0xD8` reproduces that chain-and-spiked-head assembly.

Both forms are decoded straight from the PC090OJ sprite graphics and composited; nothing here is fabricated.
Per-form behaviour (activation window, rise/descent cycle, collision rect, player damage) is still
source-pending and is deliberately **not** invented.

---

## 3. Pit Flame — PC080SN Layer-A tiles (bank `0x014`)

The R1-S2 pit flame is a **background (Layer-A) tile block**, not a sprite.

- **Tiles:** `$093A–$0949` — a 4×4 unit (16 tiles).
- **Palette bank:** `0x014` (warm orange → yellow → white).
- **Placement:** screen rows 28–31 (the bottom of the screen, where the lava pit sits), collision record 18.
  The unit repeats every 4 columns across the pit.
- **Animation:** the flicker is the **mode-8** palette cycle — scene cycler `0x59962` → per-line loader
  `0x59AD4`, colour table `$59B1A` — writing CRAM line `0x14`. The **tile pixels are fixed**; only the colours
  cycle.

Decoding and rendering this 4×4 unit from the character ROM produces an unmistakable orange/yellow flame
block, matching the arcade pit fire.

**Not the `$0224` sprite.** PC090OJ base `$0224` ("pit flame", Tighe identity) is a *separate* marker-chain
actor that materialises in **R2 and R4** and is retired in R1-S2 by the handler progress guard
(`0x44082`: `if (progress_13e < 0x18) …`; R1-S2 progress is 0x11–0x16). So the R1-S2 pit fire is entirely
these Layer-A tiles. There is **no separate sprite "top row"** for it: record 18 carries tiles only at rows
28–31. (The one R1-S2 marker-spawned sprite, the "M" burst at `0x43ECC` anim `0x7A`, is a coordinate-only
5-child burst with no static base — not a fire cap.)

---

## 4a. Water Pit — PC080SN Layer-A tiles (bank `0x01F`)

The **standing water pool in the floor** is a **background (Layer-A) tile feature**.

- **Palette bank:** `0x01F` (teal / cyan).
- **Tiles:** pool surface `$24BB–$24C2`, submerged channel `$24C3–$24CA`, plus stone-channel edging
  (`$0819`–`$0848`, `$153A`).
- **Placement:** rows 52–63 of collision record 20 (the screen floor); the unit repeats every 12 columns.
- **Animation:** the shimmer is the **mode-9** palette cycle — cycler `0x599B2` → loader `0x59AD4`,
  colour table `$59B7A`, dest CRAM lines `0x1A–0x1D` (table `$59AA4` stage 1). The tiles are fixed; the colour
  line cycles.

All bank-`0x01F` tiles in the scene live in record 20 at rows 52–63 — one feature, the pit.

## 4b. Falling Water — PC090OJ sprite (palette lines `0x1A–0x1D`), base source-pending

The **falling-water streams** (the cyan water that drops from openings above) are **a PC090OJ sprite, not
Layer A.**

- **Proven palette:** CRAM lines `0x1A–0x1D`, the 4 lines the **mode-9** water cycle drives (table `$59AA4`
  stage 1 = `{0x1A,0x1B,0x1C,0x1D}`; disassembly `0x599B2`). Sprite banks `0x1A`/`0x1B` hold the cyan water
  colours (`[0,181,198]`, `[0,82,247]`, `[0,148,247]`, `[0,214,247]`). These are **sprite** palette lines
  (`sprite_bank_colors()` lists `0x1A–0x1D`), not background banks (castle Layer-A banks stop at `0x014`/`0x01F`).
- **Why it must be a sprite:** the only cyan Layer-A bank in the scene (`0x01F`) is entirely the water pit
  (§4a); there are no other cyan background tiles. The mode-9 dest lines `0x1A–0x1D` are sprite lines. So the
  falling water is drawn by the object chip.
- **The one missing fact:** *which PC090OJ sprite base supplies the falling-water graphics.* No current editor
  usage or hazard-census entry references lines `0x1A–0x1D`, and the per-round palette records bind those lines
  to a shared pool (blocks 22/11/35/1 @ `0x4FFC2`/`0x4FE62`/`0x50162`/`0x4FD22`), not to one actor. Static data
  pins the palette but not the sprite base.
- **How to get it (next step):** the sprite-base↔palette-line binding for the falling water is a dynamic fact
  static analysis has not settled. Capture ORIGINAL ARCADE PC090OJ sprite RAM in R1-S2 while the falling water
  is on screen (established arcade-capture tooling under `tools/mame/`), read the sprite entries whose colour
  attribute selects lines `0x1A–0x1D`, and take their tile codes → the falling-water sprite graphics. That base
  is **not fabricated** here; the Water Pit object does not stand in for it.

---

## 5. How the tile sources were proven (method)

Static analysis only — the discipline is Ghidra/ROM first, runtime only for genuinely dynamic facts.

1. **Tilemap path.** The per-round background map loads via table `0x562CA[round]` → decompressor `0x563A6`
   into the PC080SN name table (`analysis/decompilation/c/rastan_scene_map.c`). This establishes that the
   castle background is a decompressed tilemap of fixed character tiles.
2. **Scene corpus.** `analysis/graphics_optimizer/subround_corpus/PAL-R1-S2-PLANEA-CASTLE/plane_a_uses.json`
   records, for every Layer-A tile in the scene, its tile code, palette bank, flip, collision record, and
   tilemap `coordinate_samples`. The tile pixels come from `build/regions/pc080sn.bin` (8×8 4bpp).
3. **Bank identification.** Bank `0x014` = 16 usages at the screen bottom with warm colours, and `0x14` is the
   mode-8 fire CRAM line — fire. Bank `0x01F` = teal/cyan usages, the only water-coloured Layer-A bank, all in
   record 20 rows 52–63 — the water **pit**.
4. **Animation dest lines (from the real disassembly).** `0x599B2` (mode 9) reads 4 dest CRAM lines per stage
   from table `$59AA4`; stage 1 = `{0x1A,0x1B,0x1C,0x1D}`. Mode-8 fire dest table `$59A98` stage 1 = `0x14`.
   These are read from `build/regions/maincpu.bin`, not the mis-bounded C export. Lines `0x1A–0x1D` are
   **sprite** palette lines (`sprite_bank_colors()` lists them; they hold cyan water colours) — which is how
   the falling water is placed as a sprite, separate from the Layer-A pit.
5. **Geometry.** Each tile is placed from its real `coordinate_samples` (grid x = col mod period, grid
   y = row − row_lo), so the assembled unit is faithful to the arcade tilemap, not a guessed ordering.
6. **Visual confirmation.** Both tile units were decoded and rendered from the character ROM before being wired
   into the tool; the fire unit reads as flames and the pit unit reads as a pool + submerged channel.

Note on the generic Ghidra decompiler export: `FUN_00059962`/`FUN_000599b2` and neighbours are mis-bounded in
`decompiler_export.c` (they appear self-recursive). The trustworthy sources for the palette-animation loader
are the hand-reconstructed `analysis/decompilation/c/raw/00059ad4.c` plus the corroborating corpus evidence
(bank `0x014` ↔ fire line `0x14`).

---

## 6. Tool realization (Palette Composer)

Four authorable traps live under the **Hazards / Traps** group in `tools/graphics_editor` (the falling-water
sprite is deliberately **not** authored until its base is pinned — §4b):

- **Spikes** carry sprite `pieces` (compositor VM) and render through `render_composite` / `composite_hitmap`.
- **Pit Flame / Water Pit** carry `plane_tiles` + `bank_palette` + `layera_tiles`, decoded by
  `_layera_trap_tiles()`, and render through `render_layera_block` / `layera_block_hitmap` — the 8×8 analogue
  of the sprite path. `/api/render` and `/api/hitmap` detect `plane_tiles` and use the Layer-A renderers, so the
  existing preview contract (arcade image + mapped-Genesis image + click-a-pixel) works unchanged.

`used_colors` key on the real tile nibble index, so Derive / Recommend / the mapping table operate identically
for tile traps and sprite traps. This is tool/authoring surface only: no production ROM, CRAM, build counter, or
palette-decision registry is mutated, and `Test.json` is byte-unchanged.

---

## 7. Open items (honest)

- **Falling-water sprite base** (§4b) — palette proven (`0x1A–0x1D`, mode-9, cyan), graphics base not pinned.
  Resolve by an ORIGINAL ARCADE PC090OJ sprite-RAM capture in R1-S2 with the water on screen. Until then it is
  not authored; the Water Pit object does not substitute for it.
- **Trap behaviour** for the spikes (activation window, descent/rise timing, collision rect, player
  damage/knockback) is source-pending; graphics are proven, behaviour is not yet, and is not fabricated.
- **"Moving wooden gate"** is listed among R1-S2 hazards but its actor base is still source-unpinned; it is not
  represented as an object yet (the chained crusher of §2 is the descending spiked block, not this gate).
- **Animation frames.** The authored palette maps the static tile bank. The mode-8/mode-9 colour cycle is a
  runtime effect; if a per-frame animation preview is wanted later, the colour tables `$59B1A` / `$59B7A` are
  the proven source.

---

## 8. Evidence index

- `analysis/decompilation/c/rastan_scene_map.c` — background tilemap decode path (`0x562CA` → `0x563A6`).
- `analysis/decompilation/c/rastan_hazard_actors.c` — `$09EA` spike family + `$0224` round reachability.
- `analysis/decompilation/c/raw/00059ad4.c` — the per-line palette-animation loader (fire/water cycle).
- `analysis/graphics_optimizer/subround_corpus/PAL-R1-S2-PLANEA-CASTLE/plane_a_uses.json` +
  `plane_palette_banks.json` — the Layer-A tile/bank/coordinate corpus for the scene.
- `build/regions/pc080sn.bin` — PC080SN character ROM (tile pixels).
- `build/maincpu.disasm.txt` — real 68000 disassembly of the palette-animation routines (`0x599B2` mode-9,
  dest tables `$59A98`/`$59AA4`); authoritative where the generic C export is mis-bounded.
- `analysis/graphics_optimizer/round1_phase1/palette_states.json` — per-round palette line records, incl. lines
  `0x1A–0x1D` (the mode-9 water lines / falling-water sprite palette).
- `analysis/actor_decompilation/r1s2_actor_roster.json` — R1-S2 marker-actor roster (progress-guard retirement
  of `$0224`/`$00F4`; "M" burst `0x43ECC`).
- Implementation note: `docs/design/Andy_r1s2_traps_proven_authorable.md`.
