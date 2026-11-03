# Cody — Independent VRAM Budget Verification (Prompt 202R2)

## Executive Summary

Global PC080SN preload using the **current LUT as-is** is **not safe across all modes**.

Reason: the LUT is scene-aliased. It maps different tile indices from different modes onto the same VRAM slots (779 multi-tile slot collisions across scene manifests). A one-time global preload cannot hold all colliding tiles simultaneously.

Separately, full-PC080SN preload of the raw universe is impossible in Genesis VRAM:
- PC080SN full tile universe: 16,384 tiles x 32 bytes = 524,288 bytes
- Available tile region in `rastan-direct`: `0x0020..0xBFFF` = 49,120 bytes

So the safe direction is mode-aware loading/swapping, not one-shot global preload.

## Inputs Audited

- `build/pc080sn_tile_vram_lut.bin`
- `build/regions/pc080sn.bin`
- `build/regions/pc090oj.bin`
- `build/maincpu.disasm.txt`
- `tools/translation/precompute_pc080sn_tile_lut.py`
- `apps/rastan-direct/src/main_68k.s`
- `apps/rastan/src/main.c` (scene preload behavior reference)
- MAME references:
  - `https://raw.githubusercontent.com/mamedev/mame/master/src/mame/taito/rastan.cpp`
  - `https://raw.githubusercontent.com/mamedev/mame/master/src/mame/taito/pc080sn.cpp`
  - `https://raw.githubusercontent.com/mamedev/mame/master/src/mame/taito/pc090oj.cpp`

Note: Ghidra executable is not available in this workspace session; reverse-engineering was done from `build/maincpu.disasm.txt` with address-level correlation.

## Task 1 — LUT Completeness Validation

### How LUT is generated

From `tools/translation/precompute_pc080sn_tile_lut.py`, LUT generation is based on:
- hardcoded static source blocks (`TITLE_STATIC_BLOCKS`)
- hardcoded table ranges (`GAMEPLAY_TABLE_START/END`, `ENDROUND_TABLE_RANGES`)
- heuristic strip-table discovery (`discover_descriptor_tables`, valid >= 14/16)
- hardcoded text writer table extraction (`TEXT_WRITER_3BB48_TABLE_SOURCE`)

### Reproducibility check

Re-running the generator to `/tmp` with identical inputs produced byte-identical outputs:
- LUT: identical
- scene manifests: identical
- source-scene map: identical

### Completeness verdict

- LUT completeness verified: **NO**
- LUT limitation clearly defined: **YES**

It is deterministic and valid for its modeled sources, but not proven complete for all possible dynamic references because it relies on fixed ranges and heuristics.

## Task 2 — True PC080SN Tile Space

### Hard bounds

- `build/regions/pc080sn.bin` size = 524,288 bytes
- 8x8 tile size = 32 bytes
- Total tile indices physically present = 16,384 (`0..16383`)

### Arcade semantics evidence

- MAME `pc080sn.cpp`: tile code uses `code & 0x3fff` (14-bit space)
- Rastan disassembly also masks tile-related words with 14-bit behavior in tile paths (e.g. around `0x55A74` path)

### LUT coverage ratio

- LUT entries: 16,384
- Nonzero mappings: 2,326 (14.2%)
- Nonzero mapped tile index max: 16,383

### Verdict

- Maximum possible tile index: **16383**
- LUT under-representation risk: **YES** (not a proof of full dynamic coverage)

## Task 3 — PC090OJ Sprite Usage Derivation

### Hardware/format bounds

- `build/regions/pc090oj.bin` size = 524,288 bytes
- 16x16 cell = 128 bytes
- ROM contains 4,096 sprite cells
- MAME `pc090oj.cpp` decodes sprite code as `code = ram[...] & 0x1fff` (13-bit code field)

### Disassembly producer evidence

Observed object-RAM write groups include:
- `0x3B8B0`: writes 24 + 9 + 9 descriptor groups to `0xD00020/0xD000E0/0xD00128`
- `0x41F5E`: writes 18 + 4 groups to `0xD003C0/0xD002E0`
- `0x41DE0..0x41EB4`: additional grouped writes (6/9/11 style loops) into `0xD00300/0xD00460/0xD00170`

### Estimated working-set statement

- Practical observed grouped-write estimate: **~22 to ~42 concurrent descriptors** depending on path
- Absolute hardware upper bound from PC090OJ active RAM: **256 descriptors**

Because full runtime mode traversal measurement was not performed in this prompt, absolute all-mode peak remains unproven.

## Task 4 — Mode-Based Variation

Mode variation is significant.

From generated scene manifests:
- Title: 841 tile-slot pairs
- Gameplay: 829 tile-slot pairs
- End-round: 1067 tile-slot pairs

From source-scene map:
- Title range: `0x5A7DA..0x5B0B2`
- Gameplay range: `0x56A22..0x570C2`
- End-round range: `0x5822A..0x59614`

Verdict: mode variation significant = **YES**

## Task 5 — VRAM Budget Re-Derivation

From `apps/rastan-direct/src/main_68k.s`:
- Tile VRAM begins at `VRAM_TILE_BASE = 0x0020`
- Plane B begins at `0xC000`
- Tile region bytes: `0xC000 - 0x20 = 49,120`
- Tile slots available: `49,120 / 32 = 1,535`

### Budget scenarios

1. Full raw PC080SN preload (16,384 tiles):  
   16,384 x 32 = 524,288 bytes -> **FAIL**

2. Global preload of all LUT-referenced tiles (2,326 unique indices) with unique slots:  
   would require 2,326 slots if unique-resident -> exceeds 1,535 -> **FAIL**

3. Existing scene-aliased LUT occupancy model:
- unique occupied slots = 1,067
- bytes = 34,144
- free slots by count = 468
- but slot alias collisions exist across modes (see Task 6), so one-time global correctness still fails.

### Global preload safety decision (prompt target)

- Global preload safe: **NO**
- Global preload risky: **YES**
- Global preload proven safe: **NO**

## Task 6 — Failure Scenarios

1. Cross-mode slot alias overwrite:
- 779 slots map to multiple different tiles across scene manifests.
- A one-time global preload leaves only one tile resident per colliding slot.
- Mode transitions then render wrong graphics for the other scene’s tile IDs.

2. LUT incompleteness risk:
- If runtime references tile IDs outside LUT-modeled sources, those tiles will not be correctly resident/mapped.

3. Sprite headroom uncertainty:
- If real all-mode concurrent sprite uniqueness rises beyond reserved strategy assumptions, sprite uploads can conflict with BG residency planning.

## Task 7 — Rainbow Islands Comparison

Evidence from local port code (`apps/rastan/src/main.c`) shows scene-specific preload manifests and reload on scene transitions (`genesistan_preload_scene_tiles`, `genesistan_bulk_preload_check`) rather than permanent global one-shot residency.

Comparison:
- Rainbow-style model: mode/scene scoped loading
- Current Rastan LUT shape: also scene-partitioned (title/gameplay/endround manifests) with intentional cross-scene slot reuse

Conclusion: Rastan data shape aligns more with **mode-based loading** than with global all-tile preload.

## Task 8 — Single Root Risk

The biggest architectural risk is:

**Treating a scene-aliased LUT as if it were a globally unique residency map.**

That causes deterministic wrong-tile rendering at scene transitions.

## Task 9 — Single Verified Next Step

Selected next step: **B. Require mode-based loading system**

Why:
- Global all-tile preload from current LUT cannot be correct across all modes due proven slot alias collisions.
- Mode manifests already exist and encode the correct partitioning.

## Final Verdict

Global preload of “all PC080SN tiles based on the existing LUT” is a trap for correctness, not a safe all-mode solution.

The independent data supports mode-based preload/swap using scene manifests, with sprite budget then validated against measured concurrent sprite working set in real runtime progression.
