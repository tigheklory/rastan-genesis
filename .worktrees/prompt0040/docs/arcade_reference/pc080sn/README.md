# Rastan Arcade PC080SN — Canonical Reference

**ROM/version:** Taito Rastan **World Rev 1** (`rastan`, maincpu 68000), the ROM under the workspace Ghidra project. All addresses are arcade values.

## Authority order (do not invert)
1. **Original 68000 opcodes** — authoritative for arcade program behavior.
2. Verified Ghidra disassembly / call graph / xrefs.
3. **Official MAME device/driver source** (`github.com/mamedev/mame` `master`: `src/mame/taito/pc080sn.cpp`, `taito/rastan.cpp`) — authoritative for PC080SN **hardware semantics** (cell bit format, RAM→tilemap mapping, scroll registers, draw order).
4. Targeted MAME arcade runtime evidence.
5. C-like semantic pseudocode in this reference — **documentation only**, reconstructed from the assembly. It is **not** original Taito source and never overrides the opcodes.

## Address-space naming rules
- Arcade CPU PCs written as `0x0559B2` etc.
- Arcade hardware / WRAM as absolute (`0xC08000`, `0x10DE00`, `a5@0x10A0`). `a5 = 0x10C000`, so `a5@(4256)=a5+0x10A0=0x10D0A0`.
- **Tilemap names:** `pc080sn_tilemap0_0xC00000` (name RAM 0xC00000–0xC03FFF), `pc080sn_tilemap1_0xC08000` (name RAM 0xC08000–0xC0BFFF). **Layer roles ARE now established** (opcodes + MAME rastan.cpp draw order): tilemap0 = **BG** (opaque, half-rate parallax, drawn first); tilemap1 = **FG** playfield (transparent, full-rate, + collision, drawn over). "BG"/"FG" may be used as the proven roles — they are no longer inferred from Genesis docs but from the arcade itself.

## Document types here
- `access_inventory.md` — **whole-ROM inventory** of every PC080SN access (the full hardware map, direct + indirect sites, subsystem classification, readback conclusion, and recommended reconstruction order). Start here for "does routine X touch the PC080SN, and where?".
- `gameplay_control.c` / `gameplay_control_assembly.md` — the **gameplay control/ring logic**: the map-byte selector, the per-direction dispatcher (0x0556A6/0x055738/0x0557C4), tile-boundary triggers, ring-counter progression, descriptor rebuild (0x055904), and scroll commit (0x055AB4). Start here for "what makes a publication happen, and where does it land?".
- `state_fields.md` — canonical A5-relative field table for the gameplay graphics path.
- `scene_initialization.c` / `scene_initialization_assembly.md` — how both tilemaps are initialized (the 0x0503E4 64-column fill loop), the tilemap0 publisher chain (0x55C4A/0x55C5E/0x55C7A, no collision), the C-window clear (0x0561B6), selector 4/5/6 handling, and the scene→gameplay handoff.
- `tilemap0_producers.md` — canonical table of every tilemap0 (0xC00000) writer/cursor root.
- `map_stream_format.md` / `map_stream_control.c` — **how a scene selects its map data and how the selector byte stream is interpreted**: pointer sources, stage→segment→stream selection (LUTs 0x5073A/0x50EE0/0x50F6B), byte-value table, one-byte-per-ring-cycle relation, and start/end/transition behavior. Start here for "where does the direction feed come from, and what does each map byte mean?".
- `core_publishers_assembly.md` — the authoritative assembly facts (register contracts, masks, increments, branch conditions).
- `core_publishers.c` — readable C-like reconstruction of the same routines (documentation).
- `address_index.md` — searchable PC → name/layer/role table.
- `unresolved.md` — genuine remaining unknowns with the exact next observation.

## PC080SN hardware ranges (established; full detail in access_inventory.md) — SOURCE-CONFIRMED
Name RAM `0xC00000–0xC0FFFF` (device RAM 0x10000; device offset = `(addr−0xC00000)/2`). Per `pc080sn.cpp` header + `word_w`: **tilemap0 (BG) = 0xC00000–0xC03FFF; 0xC04000–0xC041FF = BG rowscroll RAM (`m_bgscroll_ram[0]`, Topspeed-only), 0xC04200–0xC07FFF unused; tilemap1 (FG) = 0xC08000–0xC0BFFF; 0xC0C000–0xC0C1FF = FG rowscroll RAM, 0xC0C200–0xC0FFFF unused.** Rastan uses global scroll only, so it never streams content into the rowscroll regions (boot/frontend clears only). R/W — the CPU compare-reads name RAM at 0x03A47E/0x03A552/0x03AC54. Scroll (write-only): **`0xC40000/2` = X-scroll** (`xscroll_word_w` off0=tilemap0, off1=tilemap1), **`0xC20000/2` = Y-scroll** (`yscroll_word_w` off0=tilemap0, off1=tilemap1); stored negated (`-data`). Matches runtime. **Cell = 2 words: word1 = code&0x3FFF; word0 = colour(&0x1FF) + flip(bit14=X, bit15=Y).** **Draw order (rastan.cpp):** tilemap0 OPAQUE (back) → tilemap1 transparent (playfield, over) → sprites (front). **Roles:** tilemap1 = full-rate playfield (+collision); tilemap0 = half-rate parallax background (scene-init fill + vertical streaming via 0x055B8E — NOT static).

## Reference status (cumulative)
**Done:** (1) whole-ROM access inventory; (2) tilemap1 publication core (0x055948/968/990/9B2/A14 + collision); (3) gameplay control/ring (triggers, selector-from-map, ring counters, descriptor rebuild, scroll commit); (4) scene initialization + tilemap0 producers (0x0503E4 fill loop, 0x55C4A chain, selectors 4/5/6, tilemap roles + scroll wiring); (5) hardware mapping verified vs official MAME source — cell bit format, RAM→tilemap mapping (incl. BG/FG rowscroll regions 0xC04000/0xC0C000), scroll registers, draw order all CONFIRMED; (6) selector-1 scene-fill geometry re-derived from opcodes (0x050420 = 0xC0BF00 = tilemap1 row 63; fills tilemap1 rows 63→0 = 0xC08000–0xC0BFFF); (7) **map-stream format & scene selection** (map_stream_format.md): stage a5@0x1242 → segment a5@0x13E (LUT 0x5073A, 139 B) → stream pointer a5@0x10C6 = 0x50F6B + 0x50EE0[seg]. **Variable-length records** — indices 0–137 proven: 120 one-byte direction records + 18 two-byte [direction,event] records (record 138 candidate `[00 07]`); a5@0x13E/a5@0x10C6 walk +1 per 64-publication ring cycle (MAME-verified — pointer not recomputed each frame); direction selectors 0/1/2 publish, event bytes 4/6/7 **freeze** the walk (proven). The route from event completion back to the next direction byte is a **downgraded model, not proven** — scene-init (the only pointer re-seed) is reached only from the config-driven level-start 0x045316; value 7 has no consumer established; 0xFF = candidate sentinel. Stream = **157 bytes proven** through offset 0x9C (158 if the candidate 0x07 is accepted). **Open (unresolved.md / map_stream_format.md §6/§8):** event-completion→re-seed route; record-138/0xFF boundary; tile 0x0020 gfx pixels; selector 5/7 live behaviour; stage cardinality.

## Suggested next checkpoint
The frontend/attract composition path (0x05A4DE block-copy + descriptors), or the HUD/text/number writers (0x03Cxxx) — the remaining unreconstructed PC080SN write families.
