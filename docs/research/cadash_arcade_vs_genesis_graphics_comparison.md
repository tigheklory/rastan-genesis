# Cadash Arcade vs Genesis Graphics Comparison

## 1) Purpose
Compare Cadash arcade and Genesis graphics pipelines to extract reusable arcade-intent to Genesis-VDP translation patterns that can inform Rastan, without copying Cadash-specific logic.

## 2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest sections)
- `docs/research/graphics_translation_mapping_design.md`
- `build/examples/cadash-arcade.zip`
- `build/examples/Cadash-Genesis.bin`
- Extracted arcade program interleave: `/tmp/cadash_arcade/main_a.bin` (from `c21-14` + `c21-16`)
- Arcade disassembly: `/tmp/cadash_arcade_main.disasm.txt`
- Genesis disassembly: `/tmp/cadash_genesis.disasm.txt`
- MAME source (primary reference): `/tmp/mame_asuka.cpp` (`src/mame/taito/asuka.cpp`)
- MiSTer/JT cores repository tree metadata: `/tmp/jtcores_tree.json`

## 3) Cadash Arcade Graphics Model
Cadash arcade uses dedicated Taito graphics devices with the 68000 writing into chip-owned address windows.

- Tile planes and text:
  - MAME map for Cadash binds `0xC00000-0xC0FFFF` to `TC0100SCN` RAM and `0xC20000-0xC2000F` to `TC0100SCN` control.
  - MAME comments for this hardware family note TC0100SCN FG layer carries text.
  - Arcade disassembly reset/init (`0x0A86+`, `0x0B6C+`) shows direct setup and bulk clears of `0xC00000`, `0xC08000`, `0xC0C000`, `0xC04000`, `0xC06000`, plus repeated control writes to `0xC20000..0xC2000E`.

- Sprites:
  - MAME Cadash map binds `0xB00000-0xB03FFF` to `PC090OJ` sprite RAM.
  - Arcade disassembly init (`0x0C40+`, `0x0CF4+`) clears/fills `0xB00000` region with structured words.

- Palette:
  - MAME Cadash map binds `0xA00000-0xA0000F` to `TC0110PCR` palette device.
  - Arcade disassembly writes to `0xA00000` and stages palette-like initialization sequences.

- Scroll/control:
  - `TC0100SCN` control window at `0xC20000..0xC2000F` is actively written at reset and runtime (`0x0A86+`, `0x1154+`, `0x11A4+`, etc.), consistent with scroll/layer control semantics.

In short: arcade CPU expresses graphics intent by writing chip-mapped RAM/control regions, not by directly talking to a VDP-like unified port.

## 4) Cadash Genesis Graphics Model
Cadash Genesis drives a single VDP path directly via VDP control/data ports and staging buffers.

- Direct VDP ownership:
  - Repeated direct writes to `0xC00004` (control) and `0xC00000` (data) are pervasive.
  - Representative routines: `0x2C48`, `0x2C74`, `0x2DBC`, `0x2DE0`, `0x8D78`, `0x2EA6`.

- DMA-capable setup present:
  - Function block `0x2CA4..0x2D5C` programs VDP registers in the `0x93/0x94/0x95/0x96/0x97` range before issuing control/data writes, matching Genesis DMA register programming patterns.

- Tile/plane writes:
  - Multiple loops convert source words/bytes and stream to `0xC00000` after VRAM command setup (`0x2C48`/`0x2C74` families).

- Sprite/SAT path:
  - VDP command writers and scripted output routines (`0x8C9A..0x8F60`, including `0x8D78 -> movel %d0,0xC00004; movew %d1,0xC00000`) indicate descriptor/script driven sprite/graphics output to VDP.

- Palette and scroll:
  - Palette-like staged words in WRAM (`0xFF05F0`, `0xFF0640`, etc.) are pushed to VDP (`0x8BC..0x9F2`, `0x3E44+`).
  - Register write helpers (`0x2D5E` region) compose control-register writes compatible with scroll/control programming.

- Z80 handoff integration:
  - Frequent `0xA11100/0xA11200` bus request/reset sequencing wraps graphics/audio-adjacent operations, showing standard Genesis bus arbitration behavior.

In short: Genesis implementation expresses graphics intent through VDP command/data transactions (plus staged WRAM sources), not through arcade chip windows.

## 5) Arcade-to-Genesis Translation Patterns
1. Arcade tile/text RAM write intent -> Genesis plane write stream.
- Arcade intent: write TC0100SCN RAM words/cells.
- Genesis implementation: compute VDP destination command, stream converted words to `0xC00000`.
- Reusable for Rastan: yes, strongly.

2. Arcade sprite RAM list intent -> Genesis SAT/scripted descriptor emit.
- Arcade intent: update PC090OJ sprite RAM entries.
- Genesis implementation: stage/interpret descriptor/script data then emit SAT/pattern-related words through VDP port.
- Reusable for Rastan: yes, with format adaptation.

3. Arcade palette register writes -> Genesis CRAM load sequence.
- Arcade intent: update TC0110PCR entries.
- Genesis implementation: staged palette words copied to CRAM via VDP command/data path.
- Reusable for Rastan: yes, strongly.

4. Arcade scroll/control register writes -> Genesis VDP register writes.
- Arcade intent: update TC0100SCN control (scroll/layer mode).
- Genesis implementation: helper composes VDP register commands and writes control port.
- Reusable for Rastan: yes.

5. Arcade bulk clear/fill on chip RAM -> Genesis clear/fill primitives targeting active owners.
- Arcade intent: clear graphics RAM regions before compose.
- Genesis implementation: VDP fill/plane clear or staged WRAM clear then upload.
- Reusable for Rastan: yes, but only with correct final ownership.

## 6) Relevance To Rastan
Likely reusable patterns:
- Intent-to-owner mapping (text/tile/sprite/palette/scroll) rather than per-screen hacks.
- Shared VDP primitives: command setup, stream copy, fill, and DMA setup.
- Explicit producer/consumer ownership checks (producer writes must feed active renderer-owned buffers).

Maybe reusable patterns:
- Cadash-style script/interpreter driven text/sprite emission; useful only if Rastan already has analogous command streams.
- Cadash WRAM staging layouts; structure idea is reusable, exact addresses/formats are not.

Likely NOT reusable patterns:
- Cadash-specific command tables and hardcoded constants (e.g., local table bases around `0x8F62/0x9052`).
- Cadash networking/Z180 side behavior (`0x800000` share RAM) which is game/platform specific.
- Any direct assumption that Cadash descriptor tuple packing equals Rastan’s translated format.

## 7) First Practical Lesson For Rastan
The most useful immediate lesson is to formalize a small set of shared VDP output primitives (command-setup, tile/plane stream write, SAT emit, CRAM load, scroll write, clear/fill) and map arcade intents to those primitives with explicit producer->consumer ownership validation, instead of patching isolated callsites ad hoc.

## 8) What Not To Do
- Do not copy Cadash code/data tables directly into Rastan.
- Do not assume identical arcade chip behavior or descriptor formats between games.
- Do not assume Cadash’s local staging addresses or script tables are portable.
- Do not regress into per-screen fake rendering hacks instead of intent-based translation.

## 9) Uncertainties
- No Cadash-specific MiSTer Verilog repository was identified in available public searches during this pass (`jotego/jtcores` tree and GitHub repository searches showed no Cadash/Asuka core path).
- This pass is static-analysis only; no dynamic trace from a Cadash runtime emulator session was collected here.
- Some Genesis disassembly regions are data/script blobs that require deeper labeling for full semantic naming.

## 10) Conclusion
Cadash confirms the architecture direction already emerging for Rastan: translate arcade graphics intents into a consistent Genesis VDP primitive layer with strict output ownership checks. The reusable value is the mapping strategy and validation discipline, not Cadash-specific code.
