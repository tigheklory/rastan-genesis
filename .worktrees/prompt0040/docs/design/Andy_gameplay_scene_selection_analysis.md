# Andy — Gameplay Scene-Selection Analysis: Preload/LUT Source-Model Mismatch (Outcome G, no build)

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** evidence-only analysis.
**No source, no JSON, no ROM, no build.**
**Baseline:** `rastan-direct-proposal` @ `5cad73d` (Build 0153 accepted, `9aa1a58`). Build 0153 ROM
`ee232cbdda4880a56c51f7be26ff6bb07f811dbad8d7987e600e61af33c5707a`, counter 153. Working tree clean.
**Evidence dir:** `states/traces/build_0154_gameplay_scene_selection/` (+ reused `.../build_0154_gameplay_pc080sn_output/`).

## Outcome

**Outcome G — larger design required; bounded stop, no build.** Making the gameplay producer "naturally select
scene 1" **cannot** render Stage 1, because the tile **LUT and gameplay manifest do not represent the runtime
producer's actual source codes at all**. The scene-preload/LUT/scene-range infrastructure was built from a
block-descriptor source model (`0x5635E` / source range `0x56A22..0x570C2`) that the **runtime Stage 1 BG
producer never uses** — it reads source `0xD11C` (Genesis `0xD31C`) via descriptor walker `0x03951C`, emitting
codes in the `0x04A6` family. Pattern residency is not the blocker; the LUT is. No build was produced.

## Decisive proof (controlled offline reproduction)
`states/traces/build_0154_gameplay_scene_selection/repro_lut_mismatch.py` reconstructs the exact producer read
(`cell = word at base + row*32 + col*2`, bases `0xD31C/0xDB1C/0xF31C`, 16 cols × 64 rows) from the **real Build
0153 ROM** and looks each code up in the **shipped** `pc080sn_tile_vram_lut.bin`:

```
cells=3072  lut_nonzero=18 (0%)  distinct_codes=834  covered=1/834
```

Only **1 of 834** distinct runtime Stage 1 codes is mapped by the LUT; every other code → LUT slot **0**. In
`genesistan_hook_tilemap_bg_fill` the Genesis tile index is `tile_vram_lut[code & 0x3FFF]` — chosen **from the
LUT, not from VRAM residency** — so these cells stage as tile 0 (`0x4000` with the priority bit) **regardless of
what `load_scene_tiles(1)` loads into VRAM**. This is why `staged_bg_buffer` is a uniform `0x4000` plane
(matches KF-040 / the Build 0153 analysis).

Sample (runtime code → LUT slot): `04A6→0, 04A7→0, 04A8→0, 04B2→0, 04C2→0, 04D2→0, 0558→0` … only `051C→331`.

## Why the infrastructure targets the wrong producer
`tools/translation/precompute_pc080sn_tile_lut.py` derives the **gameplay** tile set from
`GAMEPLAY_TABLE_START=0x5635E .. GAMEPLAY_TABLE_END=0x563A6` (12-byte block-write descriptors, `src32/dst32/
rows16/cols16`) plus strip/text discovery, and stamps `genesistan_scene_a0_ranges` gameplay = `0x56A22..0x570C2`.
- ROM at Genesis `0x56C22` (= arcade `0x56A22`) holds `00AD 00AD 00AD 2300 …` (the `0x00AD` family), i.e. the
  block-descriptor model's tiles — **not** the runtime `0x04A6` family.
- The runtime producer (item-page strip-blit `0x716CA`, at arcade `0x055C5E`) reads source slot `0xFF1100 =
  0xD31C` and descriptor walker `0x03951C`; its codes are the `0x04A6` family (arcade `0xD11C` data, correctly
  relocated `+0x200`). These are in **no** manifest (title/gameplay/end-round) and effectively absent from the LUT.

So there are **two disjoint gameplay-BG models**: (1) the generator's block-descriptor model (`0x5635E`/`0x56A22`,
codes `0x00AD…`), and (2) the runtime producer's item-page/column model (`0xD11C`/`0x3951C`, codes `0x04A6…`).
The Genesis staging, scene detection, manifests and LUT are all wired to model (1); the machine actually runs
model (2). Build 0153 correctly relocated model (2)'s **source pointer**, which is why the cells now stage
(non-blank source) — but the **content pipeline** (manifest + LUT + scene identity) was never built for model (2).

## Answers to the required questions
- **Phase 1 (item-page vs gameplay use of `0x055C5E`):** it is a **general PC080SN BG column/strip producer**
  reused for both the item page and Stage 1; both invocations feed `genesistan_hook_itempage_strip_blit` with a
  source from slot `0xFF1100`. At Stage 1 setup (`2/2/4`) that slot walks `0xD31C→0xDB1C→0xF31C`. The
  distinguishing input is the **source pointer / descriptor family in slot `0xFF1100` + walker `0x03951C`**, not
  the master state.
- **Phase 2 (authoritative scene identity):**
  1. The runtime Stage 1 setup **never holds a pointer in `0x56A22..0x570C2`** — it carries `0xD11C`-family tile
     data via `0xFF1100`/`0x03951C` (confirmed: no descriptor-slot `0x10A0/0x10A4` writes in the gameplay range
     during entry; producer source is `0xD31C`).
  2. n/a (no such pointer).
  3. The Stage 1 graphics family is selected by the **producer's source/descriptor family** (`0xD11C` via walker
     `0x03951C`), staged/selected by stage/substage flow, **not** by an A0-range pointer.
  4. **Yes** — `genesistan_scene_a0_ranges` gameplay = `0x56A22..0x570C2` and the gameplay manifest were derived
     from the **block-descriptor frontend model (`0x5635E`)** that does not drive the runtime item-page/column
     Stage 1 path.
  5. Scene identity here is **producer-source/descriptor based** (`0xD11C`/`0x03951C`), not A0-range or the
     modeled block-descriptor.
- **Phase 3 (manifest/LUT contract):** manifests are `(src_tile, dst_slot)` pairs DMA'd into VRAM by
  `load_scene_tiles`; the LUT is **global** (`lut[arcade_tile] → VRAM slot`, 0 = unmapped) with scene-aware,
  conflict-free slot assignment. The uniform `0x4000` is caused by **LUT entry zero** for the runtime codes
  (834/834 - 1 uncovered), **not** by a code/attr reversal, extraction error, or missing pattern at a nonzero
  slot. `covered=1/834`.
- **Phase 4 (controlled experiment):** the offline reproduction against the real ROM + shipped LUT shows the
  staged plane is uniform tile-0 by construction. **Pattern residency alone is insufficient** — `load_scene_tiles`
  changes VRAM contents but not the LUT, and `bg_fill` picks the tile index from the LUT. No committed change was
  made; no scene load was forced in a shipped path.

## Cause classification
**Outcome G** (with an **Outcome F** core): scene selection would run, but the **manifest and LUT do not
represent the runtime Stage 1 codes**, and correcting that requires re-modeling the generator's gameplay
tile-analysis around the **actual runtime producer source family** (`0xD11C` + descriptor `0x03951C`, codes
`0x04A6…`) — plus establishing the authoritative producer-source scene selector. That is a design step spanning
the tile-analysis tool, the manifests, the LUT, and the scene-identity mechanism, not a bounded scene-selection
wrapper. The task's stop conditions "the current scene manifests or LUT require a larger redesign" and
"authoritative scene identity remains unproven" both apply.

## Why no build
- Forcing scene selection / `load_scene_tiles(1)` would render nothing: `covered=1/834`, so the cells stay
  uniform tile-0. The task forbids a build whose only effect is forcing scene selection.
- A correct fix must first **prove the `0x03951C` descriptor-walker format** (6-byte entries observed:
  `A4=0x3951C→0x39522→0x39528`) and the `0xD11C` source structure, then **extend the tile-analysis generator**
  to model this producer, **regenerate** the gameplay manifest + LUT to cover the `0x04A6` family, and **wire a
  producer-source scene selector** — a multi-artifact redesign. Doing any subset alone (e.g. scene selection, or
  a partial LUT patch) would be known-wrong or unfaithful.

## Smallest next design task (bounded design, then implement)
1. **Prove the runtime Stage 1 content descriptor:** decode the `0x03951C` walker (entry format, count, dims) and
   the `0xD11C` source layout it selects; enumerate the exact Stage 1 tile-code set the producer emits (the
   `0x04A6` family) and confirm each has a valid pattern in `build/regions/pc080sn.bin`.
2. **Extend `precompute_pc080sn_tile_lut.py`** to model this producer as the gameplay source (alongside or
   replacing the `0x5635E` block model), so the regenerated gameplay manifest + global LUT cover the runtime
   codes and assign conflict-free VRAM slots.
3. **Establish the authoritative producer-source scene selector** (the `0xFF1100`/`0x03951C` family or a proven
   stage/substage field) and, reusing the existing scene-detection primitive + `load_scene_tiles` lifecycle,
   drive `genesistan_current_scene_id → 1` naturally at the producer entry — no state-number test, no forced ID.
4. Re-verify the staged plane becomes non-uniform and matches representative arcade cells, patterns resident,
   palette intact, frontend unaffected — then a bounded Build 0154 is possible.

## Confirmation (no forcing, no changes)
No source, JSON, ROM, or build was produced. `load_scene_tiles(1)` was **not** called in any shipped path, scene
ID was **not** forced, no state-number scene test was added, no second renderer/loader/commit path was created,
`genesistan_scene_a0_ranges` was **not** changed, no cells/patterns/scroll/palette were hardcoded, and the raw
writer `0x03D04C` was untouched. Build 0153 relocations and Build 0152 `0xC08C62` routing remain intact and
unmodified. The Phase-4 experiment was an uncommitted offline reproduction only.

## Open issue impact
- **OPEN-017 (ROM does not run on real hardware / gameplay):** advanced — the gameplay-BG boundary is now
  root-caused past scene selection to a **preload/LUT source-model mismatch**: the manifests, global tile LUT,
  and `scene_a0_ranges` model a block-descriptor gameplay source (`0x5635E`/`0x56A22`, codes `0x00AD…`) that the
  runtime never runs, while the live producer reads `0xD11C`/`0x03951C` (codes `0x04A6…`), only 1/834 of which the
  LUT maps. `load_scene_tiles(1)` cannot help until the tile-analysis pipeline is re-modeled around the runtime
  producer. Bounded next design task defined. Not closed; no duplicate opened.
