# Rainbow Islands Arcade vs Genesis Graphics Comparison

## 1) Purpose
Analyze Rainbow Islands as the primary comparative case to extract reusable arcade-to-Genesis graphics translation patterns for Rastan, while explicitly separating graphics pipeline behavior from C-Chip-dependent gameplay/protection behavior.

## 2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest sections first)
- `docs/research/graphics_translation_mapping_design.md`
- `docs/research/cadash_arcade_vs_genesis_graphics_comparison.md`
- Arcade ROM set from examples: `build/examples/rainbow.zip` / `build/examples/rbisland.zip`
- Genesis ROM from examples: `build/examples/Rainbow Islands - The Story of Bubble Bobble 2 (JU) [p1].ZIP`
- Arcade interleaved disassembly: `/tmp/rainbow_arcade_main.disasm.txt`
- Genesis disassembly: `/tmp/rainbow_genesis.disasm.txt`
- MAME primary reference: `/tmp/mame_rbisland.cpp`
- MAME C-Chip device reference: `/tmp/mame_taitocchip.cpp`
- MiSTer/FPGA cross-check references: `/tmp/jt_risle_rbisland.cpp`, `/tmp/jt_risle_tile_layers.kicad_sch`, `/tmp/jt_risle_sprites.kicad_sch`

## 3) Rainbow Islands Arcade Graphics Model
Rainbow Islands arcade graphics ownership is chip-driven, with the 68000 writing chip-mapped windows and the graphics devices rendering directly.

- Graphics-related main map ownership (MAME `rbisland_state::main_map`):
  - Palette RAM: `0x200000-0x200FFF` (`palette_device::write16`)
  - Tilemap RAM: `0xC00000-0xC0FFFF` (`PC080SN` word read/write)
  - Scroll/control: `0xC20000` (Y scroll), `0xC40000` (X scroll), `0xC50000` (control)
  - Sprite RAM: `0xD00000-0xD03FFF` (`PC090OJ`)
- Arcade CPU writes these windows directly in live code paths:
  - Scroll/control writes in disasm: `movew %d0,0xC50000` (`0x0F94`), `0xC40000` (`0x0FA0`), `0xC20000` (`0x0FA6`)
  - Bulk chip-RAM clear/init loops target `0xC00000`, `0xD00000`, `0x200000` (`0x108E`, `0x10CE`, `0x110E`)
  - Secret-room tile writes target C-window addresses (`0x55EE` onward uses `0xC00B08/0xC00D08/0xC00F08/0xC01108/0xC01308`)
- Rendering ownership in MAME `screen_update`:
  - `m_pc080sn->tilemap_update()`
  - `m_pc080sn->tilemap_draw(... layer 0 ...)`
  - `m_pc080sn->tilemap_draw(... layer 1 ...)`
  - `m_pc090oj->draw_sprites(...)`
  - This confirms graphics hardware, not CPU software rasterization, owns final composition.
- C-Chip mapped windows exist separately:
  - `0x800000-0x8007FF` C-Chip RAM window
  - `0x800800-0x800FFF` C-Chip ASIC window
  - Arcade disassembly shows frequent accesses (`0x800001/3/5/7/9/B/D`, `0x800803`), but these are not tile/sprite/palette device windows.

## 4) Rainbow Islands Genesis Graphics Model
Rainbow Islands Genesis uses direct VDP ownership through `0xC00004` (control) and `0xC00000` (data), with WRAM staging and transfer routines.

- Direct VDP port usage is pervasive:
  - Many `movew/movel -> 0xC00004` and `movew -> 0xC00000` sequences throughout disassembly.
- VDP/DMA register programming patterns are explicit:
  - Multiple blocks write `0x93xx/0x94xx/0x95xx/0x96xx/0x97xx` style values to `0xC00004` (e.g., around `0x070A`, `0x086C`, `0x08A6`), followed by VDP status waits.
  - This is consistent with Genesis DMA-capable setup and control flow.
- Tilemap/plane writes are structured helper routines:
  - Streaming routines at `0x28D6`, `0x28FA`, `0x291E`, `0x2942` write rows/regions to `0xC00000`.
  - Address setup helpers at `0x2966` and `0x2992` compute plane destinations with `+0xC000` and `+0xE000` bases.
  - VDP command builders at `0x29B0`/`0x29D4` compose control words before control-port writes.
- Sprite/SAT-style path appears staged then uploaded:
  - WRAM structures/buffers at `0xFFFB00` and pointer-tracked writer at `0xFFFA80` are used by routines around `0x193A`, `0x1964`, `0x1984`, `0x19A2`.
  - The tuple write sequence in `0x19A2` (`y`, `attr`, `tile`, `x` style ordering) is consistent with sprite descriptor staging before VDP-visible output.
  - This SAT interpretation is inferred from tuple shape and VDP upload context.
- Palette and clear behavior:
  - Clear/load style routines at `0x19CC`, `0x19E8`, `0x1A06` set VDP command targets and stream many words.
  - This matches CRAM/VRAM clearing and initialization phases.
- WRAM staging areas seen in active graphics flow:
  - `0xFFF800` (larger staging region), `0xFFFB00` (descriptor/data block), `0xFFFA80` (append pointer/state)

## 5) Arcade-to-Genesis Translation Patterns
1. Arcade tile-plane RAM writes -> Genesis plane write streams.
- Arcade-side intent: CPU writes PC080SN tile RAM (`0xC00000+`) to update visible layers.
- Genesis-side implementation: compute VDP plane destination and stream words to `0xC00000` via helper loops.
- Reusable for Rastan: YES.
- Why: Rastan also has arcade tilemap intent that must become VDP plane ownership.

2. Arcade scroll/control writes -> Genesis VDP register/control writes.
- Arcade-side intent: update PC080SN scroll/control (`0xC20000`, `0xC40000`, `0xC50000`).
- Genesis-side implementation: register/control command writes through `0xC00004` helpers.
- Reusable for Rastan: YES.
- Why: direct mapping from chip-control semantics to VDP register semantics is core to remap architecture.

3. Arcade sprite RAM/object list updates -> Genesis SAT/descriptor staging + upload.
- Arcade-side intent: write PC090OJ sprite RAM (`0xD00000+`).
- Genesis-side implementation: build WRAM descriptor tuples (e.g., around `0xFFFA80/0xFFFB00`), then push to VDP path.
- Reusable for Rastan: YES (format adaptation required).
- Why: producer->descriptor->VDP pipeline is strongly analogous, but exact tuple/packing is game-specific.

4. Arcade palette RAM writes -> Genesis CRAM update sequences.
- Arcade-side intent: write palette RAM (`0x200000+`).
- Genesis-side implementation: VDP command + bulk data writes through control/data ports.
- Reusable for Rastan: YES.
- Why: same fundamental palette ownership translation, with conversion/packing differences as needed.

5. Arcade chip-RAM clear/fill -> Genesis active-owner clear/fill + upload.
- Arcade-side intent: clear tile/sprite/palette windows before compose.
- Genesis-side implementation: clear WRAM staging and/or issue VRAM/CRAM clears through VDP command path.
- Reusable for Rastan: YES.
- Why: startup/title stability depends on clear/fill ownership correctness before production writes.

6. C-Chip logic/service exchanges -> keep separate from graphics translation.
- Arcade-side intent: protection/gameplay/service-side state exchanges via C-Chip windows.
- Genesis-side implementation: game-logic-specific handling (not a graphics primitive).
- Reusable for Rastan graphics translation: NO.
- Why: Rastan graphics remap should not depend on C-Chip behavior assumptions.

## 6) MAME + MiSTer / FPGA Cross-Check
MAME is treated as the primary authority for arcade behavior.

- Proven from MAME source:
  - Exact Rainbow memory map ownership for palette/C-Chip/PC080SN/PC090OJ.
  - Render ordering and graphics ownership (`tilemap_draw` then `draw_sprites`).
  - C-Chip exposed as separate device window and device model.
- MiSTer/FPGA cross-check used:
  - `jtcores` Rainbow (`risle`) references include matching map/model file (`doc/rbisland.cpp`) and board-level schematics.
  - Schematics include PC080SN (`tile_layers`) and PC0900J + sprite SRAM (`sprites`), supporting chip ownership model consistency.
- What is inferred vs proven:
  - Proven: arcade chip ownership boundaries and rendering pipeline from MAME and mirrored `jtcores` doc source.
  - Inferred: detailed Genesis routine semantic labels (SAT builder names, exact DMA channel intent) from disassembly patterns rather than labeled source.
- MiSTer/HDL limitation in this pass:
  - No deep Verilog module execution-path analysis was performed; cross-check is doc/schematic-level only.

## 7) C-Chip Relevance Check
- Likely C-Chip-dependent areas in Rainbow Islands:
  - Protection/gameplay/state services, secret-room/game-rule behavior, service/input-related logic windows (`0x800000+`).
  - MAME C-Chip model (`taitocchip.cpp`) describes MCU + EPROM + banked shared SRAM behavior, consistent with logic-service responsibilities.
- Graphics/rendering path independent of C-Chip:
  - Tilemap rendering ownership: PC080SN windows and draw calls.
  - Sprite rendering ownership: PC090OJ windows and draw calls.
  - Palette ownership: palette RAM window and palette device writes.
  - Therefore, final graphics composition path is hardware-graphics-chip driven and separable from C-Chip internals.
- Reusable lesson for Rastan despite no C-Chip in Rastan:
  - Preserve strict graphics ownership translation (arcade graphics intent -> Genesis VDP intent) independent of non-graphics game-service devices.
  - Do not import C-Chip assumptions into Rastan unless separately proven necessary for gameplay logic.

## 8) Relevance To Rastan
Rainbow Islands reinforces that the highest-value reusable layer is intent translation by ownership class, not game-specific code reuse.

Most relevant to Rastan:
- Tile plane intent mapping (`chip tile RAM writes` -> `VDP plane writes`)
- Sprite intent mapping (`object RAM writes` -> `SAT/descriptor pipeline`)
- Scroll/control mapping (`chip control writes` -> `VDP register writes`)
- Palette mapping (`arcade palette writes` -> `CRAM updates`)
- Clear/fill ordering discipline (`active owner clear/fill before production`)

Less relevant/non-transferable:
- Rainbow-specific C-Chip gameplay/protection exchanges
- Rainbow-specific table formats and descriptor packing details

## 9) First Practical Lesson For Rastan
Adopt a strict producer->consumer graphics ownership validation rule: every translated arcade graphics producer (tile, sprite, palette, scroll, clear/fill) must prove it feeds the active Genesis VDP consumer path, not a legacy/stale buffer.

## 10) Comparison Against Cadash
- What Rainbow Islands reinforces from Cadash:
  - Arcade writes chip-owned graphics windows; Genesis writes unified VDP ports.
  - Reusable translation classes are tile, sprite, palette, scroll/control, and clear/fill.
  - Ownership/intent mapping is more robust than per-screen patching.
- What Rainbow Islands adds beyond Cadash in this study:
  - Explicit C-Chip separation requirement and evidence that graphics composition remains independent.
  - Strong PC080SN/PC090OJ ownership alignment with Rastan-like Taito graphics-chip expectations.
  - Clear examples of arcade-side tile RAM direct writes in gameplay/event code (e.g., secret-room tile writes).
- What appears more applicable to Rastan than Cadash:
  - Rainbow’s PC080SN + PC090OJ model alignment is a closer architectural analog for Rastan-era graphics translation than Cadash’s specific board differences.

## 11) What Not To Do
- Do not copy Rainbow Islands Genesis routines/tables blindly into Rastan.
- Do not assume Rainbow and Rastan data formats are identical (tile attrs, sprite tuples, table layouts).
- Do not assume C-Chip behavior applies to Rastan.
- Do not turn this into per-screen hacks; keep reusable intent-to-owner translation.
- Do not conflate “no crash” with correct graphics ownership translation.

## 12) Uncertainties
- Genesis symbol-level function names are inferred from disassembly structure; no official source labels were available in this pass.
- DMA semantics are strongly indicated by `0x93..0x97` VDP register programming patterns, but exact per-routine DMA mode labeling remains inferred without source-level names.
- MiSTer/FPGA cross-check was schematic/doc-level in this pass, not a full HDL execution trace.

## 13) Conclusion
Rainbow Islands confirms a reusable and Rastan-relevant translation strategy: map arcade graphics intent classes (tile/sprite/palette/scroll/clear) to explicit Genesis VDP owner primitives, validate producer->consumer continuity, and keep C-Chip/gameplay services strictly separated from graphics pipeline translation.
