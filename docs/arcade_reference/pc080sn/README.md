# Rastan Arcade PC080SN — Canonical Reference

**ROM/version:** Taito Rastan **World Rev 1** (`rastan`, maincpu 68000), the ROM under the workspace Ghidra project. All addresses are arcade values.

## Authority order (do not invert)
1. **Original 68000 opcodes** — authoritative.
2. Verified Ghidra disassembly / call graph / xrefs.
3. Targeted MAME arcade runtime evidence.
4. C-like semantic pseudocode in this reference — **documentation only**, reconstructed from the assembly. It is **not** original Taito source and never overrides the opcodes.

## Address-space naming rules
- Arcade CPU PCs written as `0x0559B2` etc.
- Arcade hardware / WRAM as absolute (`0xC08000`, `0x10DE00`, `a5@0x10A0`). `a5 = 0x10C000`, so `a5@(4256)=a5+0x10A0=0x10D0A0`.
- **Neutral tilemap names until ownership is proven scene-wide:** `pc080sn_tilemap0_0xC00000` (name RAM 0xC00000–0xC03FFF), `pc080sn_tilemap1_0xC08000` (name RAM 0xC08000–0xC0BFFF). **No "BG"/"FG" labels** — layer *roles* (background vs playfield) are not established by this checkpoint and must not be inferred from prior Genesis docs.

## Document types here
- `access_inventory.md` — **whole-ROM inventory** of every PC080SN access (the full hardware map, direct + indirect sites, subsystem classification, readback conclusion, and recommended reconstruction order). Start here for "does routine X touch the PC080SN, and where?".
- `gameplay_control.c` / `gameplay_control_assembly.md` — the **gameplay control/ring logic**: the map-byte selector, the per-direction dispatcher (0x0556A6/0x055738/0x0557C4), tile-boundary triggers, ring-counter progression, descriptor rebuild (0x055904), and scroll commit (0x055AB4). Start here for "what makes a publication happen, and where does it land?".
- `state_fields.md` — canonical A5-relative field table for the gameplay graphics path.
- `scene_initialization.c` / `scene_initialization_assembly.md` — how both tilemaps are initialized (the 0x0503E4 64-column fill loop), the tilemap0 publisher chain (0x55C4A/0x55C5E/0x55C7A, no collision), the C-window clear (0x0561B6), selector 4/5/6 handling, and the scene→gameplay handoff.
- `tilemap0_producers.md` — canonical table of every tilemap0 (0xC00000) writer/cursor root.
- `core_publishers_assembly.md` — the authoritative assembly facts (register contracts, masks, increments, branch conditions).
- `core_publishers.c` — readable C-like reconstruction of the same routines (documentation).
- `address_index.md` — searchable PC → name/layer/role table.
- `unresolved.md` — genuine remaining unknowns with the exact next observation.

## PC080SN hardware ranges (established; full detail in access_inventory.md)
Name RAM `0xC00000–0xC0FFFF` (content-bearing quadrants `pc080sn_tilemap0_0xC00000` and `pc080sn_tilemap1_0xC08000`; R/W — the CPU compare-reads name RAM at 0x03A47E/0x03A552/0x03AC54). Scroll `0xC20000/2` (layer-A X/Y) and `0xC40000/2` (layer-B X/Y) — **write-only**. **Roles (MAME-confirmed):** tilemap1@0xC08000 ↔ layer B = scrolling foreground/playfield (streamed + collision); tilemap0@0xC00000 ↔ layer A = background (scene-init fill, static in the tested segment).

## Reference status (cumulative)
**Done:** (1) whole-ROM access inventory; (2) tilemap1 publication core (0x055948/968/990/9B2/A14 + collision); (3) gameplay control/ring (triggers, selector-from-map, ring counters, descriptor rebuild, scroll commit); (4) scene initialization + tilemap0 producers (0x0503E4 fill loop, 0x55C4A chain, selectors 4/5/6, tilemap roles + scroll wiring). **Open:** see `unresolved.md` (0x055B8E tilemap0 gameplay activation; 4/5/6 exact event semantics; word0 bit meaning; 0xC0C000 quadrant; per-cell text-writer targets).

## Suggested next checkpoint
The map data format itself (the byte stream at `a5@0x10C6`): how selector/direction/event bytes are encoded, and how a scene's map data is selected — this ties the ring feed to level progression.
