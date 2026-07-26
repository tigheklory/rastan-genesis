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
- `core_publishers_assembly.md` — the authoritative assembly facts (register contracts, masks, increments, branch conditions).
- `core_publishers.c` — readable C-like reconstruction of the same routines (documentation).
- `address_index.md` — searchable PC → name/layer/role table.
- `unresolved.md` — genuine remaining unknowns with the exact next observation.

## Scope of THIS checkpoint
The **gameplay publication core**: `0x055948` (dispatch), `0x055968`/`0x055990` (column publishers), `0x0559B2`/`0x055A14` (cell producers + collision), and enough of `0x055904`/the triggers to fix the destination cursor, selector, and descriptors. **Proven result:** these core publishers write **`pc080sn_tilemap1_0xC08000`** and produce collision at `0x10DE00`. Writes to `pc080sn_tilemap0_0xC00000` come from a *separate* state-gated path (`0x055E54`, `a5@0x139A==2`), out of scope here.

## Next checkpoint (not done here)
Scene initialization (incl. the `0xC00000` filler), horizontal/vertical publication triggers, camera/scroll state, the 64-row ring behavior, runtime update patterns.
