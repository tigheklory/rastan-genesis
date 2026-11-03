# Cody - Full Arcade Rastan Ghidra Disassembly and Whole-Game Reference

**Date:** 2026-07-19  
**Type:** Infrastructure / static-analysis reference generation only  
**Primary source:** original arcade MAME `rastan` / `Rastan (World Rev 1)` ROM set  
**Scope:** Ghidra project + reproducible scripts + exported static reference artifacts. No source/spec/tool behavior/Makefile/ROM/build/invariant changes. No numbered build. No runtime probing.

Address labels: `arcade_pc` = original arcade maincpu address, `arcade_rom_offset` = offset in the assembled arcade maincpu image, `arcade_WRAM` = original arcade work RAM, `arcade_HW_ADDRESS` = original arcade hardware address, `runtime_genesis_pc`/`genesis_rom_offset` = Genesis translated spaces only when derived through `build/rastan-direct/address_map.json`.

## Phase 0

Relevant priors from `KNOWN_FINDINGS.md`:

- KF-010: BG/FG staging and VDP plane ownership context.
- KF-011: arcade VBlank owns lifecycle; Genesis code is helper/service only.
- KF-026/KF-047/KF-048/KF-064/KF-065/KF-067: PC090OJ sprite/object evidence and known open sprite/lizard boundaries.
- KF-032/KF-038/KF-040/KF-041/KF-042: PC080SN raw-write/staging/long-row/gameplay layout evidence.
- KF-036/KF-039/KF-044: work-RAM base/address-mapping discipline.
- KF-052/KF-053/KF-054: VBlank/SAT timing ownership context.

Rediscovery Hazard HIGH findings touched: KF-010, KF-011, KF-032, KF-036, KF-038, KF-039, KF-040, KF-041, KF-042, KF-044, KF-047, KF-052, KF-053, KF-054, KF-057, KF-058, KF-059, KF-060, KF-061, KF-062, KF-063, KF-064, KF-066, KF-067. None contradicted.

Deferred-appendix entries relevant: none directly; this task creates a reusable static reference rather than resolving a runtime defect.

Task classification: **INFRASTRUCTURE**. This task does not assert a new gameplay/rendering mechanism; it creates and documents a reproducible whole-arcade static-analysis reference.

Open/Closed issues touched: OPEN-001, OPEN-017, and OPEN-024 as broad reference consumers; OPEN-015 context only for crash-evidence discipline. No issue was opened, edited, or closed.

Contradiction of CONFIRMED/STRONG finding detected: **NONE**.

Architecture compliance: **CONFIRMED**. The original arcade program is treated as the source of truth. Genesis addresses are used only in a JSON-derived correlation report and no Genesis runtime behavior was changed.

## Image Identity

The arcade maincpu image was assembled from `roms/rastan.zip`, matching MAME `rastan` / `Rastan (World Rev 1)` LOAD16_BYTE layout.

- Source zip: `roms/rastan.zip`
- Source zip SHA256: `09a19edc7221694d3885c11f75e549fca3589161c6113275e857a44ee40051af`
- Assembled image: `analysis/ghidra/rastan_arcade/input/rastan_world_rev1_maincpu_68000.bin`
- Assembled image size: `0x60000` / `393216` bytes
- Assembled image SHA1: `63577d3f75a96b35398cf40126c40598ebd8089d`
- Assembled image SHA256: `4f30b9e7aa946aa33d20e125a1726ff094f9615980107d0842efe1721cf32063`
- Load base: `arcade_pc 0x000000`
- Initial SP vector: `arcade_WRAM 0x0010DE00`
- Reset vector: `arcade_pc 0x0003A000`

`build/regions/maincpu.bin` is byte-identical to the assembled image and has the same SHA256.

The full manifest is `analysis/ghidra/rastan_arcade/input/verified_image_manifest.json`.

## MAME Memory Map Source

MAME source inspected: `docs/reference/mame/rastan/src/mame/taito/rastan.cpp`, `rastan_state::main_map`.

Key map entries recorded in `analysis/ghidra/rastan_arcade/exports/memory_map.md`:

| Address space | Range | Meaning |
|---|---:|---|
| `arcade_pc` | `0x000000-0x05FFFF` | maincpu ROM |
| `arcade_WRAM` | `0x10C000-0x10FFFF` | work RAM / common A5 base |
| `arcade_HW_ADDRESS` | `0x200000-0x200FFF` | CLCS palette RAM |
| `arcade_HW_ADDRESS` | `0x380000-0x380001` | sprite palette bank / coin / lockout control |
| `arcade_HW_ADDRESS` | `0x390000-0x39000B` | input and DIP ports |
| `arcade_HW_ADDRESS` | `0x3C0000-0x3C0001` | watchdog reset |
| `arcade_HW_ADDRESS` | `0x3E0000-0x3E0003` | PC060HA sound communication |
| `arcade_HW_ADDRESS` | `0xC00000-0xC0FFFF` | PC080SN tilemap C-window |
| `arcade_HW_ADDRESS` | `0xC20000-0xC20003` | PC080SN Y scroll |
| `arcade_HW_ADDRESS` | `0xC40000-0xC40003` | PC080SN X scroll |
| `arcade_HW_ADDRESS` | `0xC50000-0xC50003` | PC080SN control |
| `arcade_HW_ADDRESS` | `0xD00000-0xD03FFF` | PC090OJ sprite RAM |

## Ghidra Project

- Ghidra install: `/home/tighe/tools/ghidra_12.0.4_PUBLIC`
- Ghidra version: `12.0.4 PUBLIC`
- Headless runner: `/home/tighe/tools/ghidra_12.0.4_PUBLIC/support/analyzeHeadless`
- Local JDK from project setup: `tools/local/java/jdk-21.0.10+7`
- Ghidra language/compiler: `68000:BE:32:default:default`
- Ghidra project: `analysis/ghidra/rastan_arcade/ghidra_project/rastan_arcade_world_rev1.gpr`
- Ghidra database: `analysis/ghidra/rastan_arcade/ghidra_project/rastan_arcade_world_rev1.rep/`
- Headless log: `analysis/ghidra/rastan_arcade/logs/headless_export.log`

The run uses workspace-local Ghidra user config under `analysis/ghidra/rastan_arcade/.home/` via `HOME` and `XDG_CONFIG_HOME`, avoiding writes to the real user Ghidra config.

## Reproducible Workflow

Run from the repository root:

```bash
analysis/ghidra/rastan_arcade/run_headless_export.sh
```

The runner:

- loads `tools/setup_env.sh` for Java/toolchain path;
- imports `analysis/ghidra/rastan_arcade/input/rastan_world_rev1_maincpu_68000.bin` as raw 68000 big-endian at `arcade_pc 0x000000`;
- runs `analysis/ghidra/rastan_arcade/scripts/RastanArcadeSeed.java` before auto-analysis;
- runs `analysis/ghidra/rastan_arcade/scripts/RastanArcadeExport.java` after auto-analysis;
- writes exports under `analysis/ghidra/rastan_arcade/exports/`.

The seed script adds the MAME main CPU memory map as named Ghidra blocks, labels major hardware addresses, and creates/disassembles known entrypoints such as `arcade_pc 0x03A000`, `0x03A008`, `0x039F80`, `0x03AE86`, `0x03ACAE`, `0x03BD48`, `0x03B930`, `0x03B802`, and `0x0565A6`.

## Exported Artifacts

Directory: `analysis/ghidra/rastan_arcade/exports/`

- `full_listing.tsv`: Ghidra-classified instruction listing with bytes, mnemonic, function, and refs.
- `linear_disassembly.tsv`: full `0x000000..0x05FFFF` linear disassembly derived from the verified image mirror `build/maincpu.disasm.txt`; use this as the whole-ROM byte-range reference, not as proof that every line is executable code.
- `function_inventory.tsv`: Ghidra function inventory.
- `call_graph_edges.tsv` and `call_graph.dot`: Ghidra call graph.
- `xrefs.tsv`: references emitted by Ghidra.
- `hw_refs.tsv`: references/scalars touching the known arcade WRAM/HW spaces.
- `scalar_constants.tsv`: ROM/HW/WRAM scalar constants observed in instructions.
- `jump_tables_and_indirects.tsv`: indirect call/jump/table-looking sites for manual review.
- `decompiler_export.c`: decompiler output for Ghidra-created functions.
- `memory_map.md`: MAME-derived memory map and Ghidra block map.
- `unresolved_regions.tsv`: Ghidra-unclassified ROM gaps.
- `coverage_report.md`: conservative Ghidra coverage summary.
- `subsystem_map.md`: subsystem anchor map.
- `address_correlation_report.json`: JSON-derived arcade-to-Genesis mapping report using `build/rastan-direct/address_map.json` only.
- `export_summary.md`: compact export summary.

Supplemental input artifact:

- `analysis/ghidra/rastan_arcade/input/entrypoints_from_linear_disasm.tsv`: control-flow targets extracted from the full linear disassembly for future Ghidra refinement.

## Coverage Stats

From `coverage_report.md` and post-processing:

- Ghidra function count: `181`
- Ghidra instruction count: `4094`
- Ghidra-classified code bytes: `0x3974` / `14708`
- Conservative Ghidra code coverage: `3.74%`
- Ghidra unresolved/data gap count: `139`
- Largest unresolved/data gap: `0x398C6` bytes
- Full linear disassembly rows: `121605`
- Linear control-flow target anchors extracted: `4688`

Interpretation: the Ghidra project is a conservative static model seeded from verified entrypoints and MAME memory blocks. The full linear disassembly export covers the complete maincpu byte range. The unresolved gaps are not evidence of absent code; they include tables, descriptors, literal pools, text, data, and code that Ghidra did not discover from seeded control flow.

## Hardware Reference Summary

`hw_refs.tsv` contains `453` rows. Counts by target space:

- `PC080SN_tilemap`: `124`
- `arcade_WRAM`: `101`
- `PC090OJ_sprite_RAM`: `52`
- `arcade_inputs`: `46`
- `arcade_sound_comm`: `34`
- `arcade_palette_RAM`: `34`
- `arcade_watchdog`: `16`
- `arcade_sprite_ctrl`: `14`
- `PC080SN_yscroll`: `11`
- `PC080SN_xscroll`: `11`
- `PC080SN_ctrl`: `6`
- `arcade_unknown_350008`: `4`

Caveat: direct absolute references are easier for Ghidra to enumerate than register-indirect hardware writes. Treat `hw_refs.tsv` as a starting index, not an exhaustive proof that no other register-indirect hardware writers exist.

## Address Correlation

Correlation source: `build/rastan-direct/address_map.json`.

`address_correlation_report.json` does not use a fixed `+0x200` or `-0x200` rule. For each Ghidra function entry and extracted linear-disassembly anchor, it finds the containing segment in `address_map.json` and records the mapped `runtime_genesis_pc` only when the segment range supports it.

Summary:

- Ghidra functions total: `181`
- Ghidra functions with JSON-derived mapping: `157`
- Linear control-flow anchors total: `4688`
- Linear control-flow anchors with JSON-derived mapping: `4600`

Any address absent from a JSON segment is left unmapped by this report.

## Subsystem Map

`subsystem_map.md` records these initial anchor groups:

- startup/reset: `arcade_pc 0x03A000`, `0x03AE86`, `0x039F80`
- VBlank/lifecycle: `arcade_pc 0x03A008`
- title/attract text: `arcade_pc 0x03ACAE`, `0x03BD48`, `0x0565A6`
- PC080SN tilemaps: `arcade_HW_ADDRESS 0xC00000-0xC0FFFF`
- PC080SN scroll: `arcade_HW_ADDRESS 0xC20000`, `0xC40000`
- PC090OJ sprites: `arcade_pc 0x03B930`, `0x03B802`; `arcade_HW_ADDRESS 0xD00000-0xD03FFF`
- palette: `arcade_HW_ADDRESS 0x200000-0x200FFF`, `0x380000`
- input/sound/watchdog: `arcade_HW_ADDRESS 0x390000`, `0x3E0000`, `0x3C0000`

## Major Observations

- The original arcade image identity is now pinned and reproducible from `roms/rastan.zip` and MAME's LOAD16_BYTE layout.
- The reset vector lands at `arcade_pc 0x03A000`; the initial stack is `arcade_WRAM 0x10DE00`.
- MAME's main CPU memory map is captured directly into the Ghidra project and exported documentation.
- The Ghidra function model is useful for named seeded regions and discovered call graph, but it remains conservative; the full linear disassembly is required when looking outside discovered functions.
- Hardware-reference exports provide a fast index for PC080SN, PC090OJ, palette, input, sound, and watchdog references, but register-indirect writers still require targeted analysis/runtime proof.
- JSON-derived correlation is available for most function/control-flow anchors and explicitly avoids fixed-offset assumptions.

## Non-Actions

No source, spec, Makefile, runtime tool behavior, ROM artifact, invariant, rolling ROM, or build counter was modified. No numbered build was produced. No emulator runtime trace was run. No issue was opened or closed. `KNOWN_FINDINGS.md` was not edited.

## CURRENT_STATE Impact

`CURRENT_STATE.md` was updated only to point to the new arcade Ghidra reference location and to record that Build 0214/counter 214 remain unchanged.

## OPEN / CLOSED Issues Impact

- Open issues touched: OPEN-001, OPEN-017, OPEN-024 as future consumers of the reference; OPEN-015 context only.
- Closed issues touched: NONE.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: all runtime/gameplay/visual implementation work, including PC080SN, PC090OJ, collision, palette, D00298, continue/game-over, and hardware/Exodus/Nomad follow-ups.

No issue ledger edit was required.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. Rationale: this is infrastructure/static-reference generation. It provides a reusable evidence base but does not establish or refine a durable runtime mechanism.

## STOP

STOP triggered: **NO**.
