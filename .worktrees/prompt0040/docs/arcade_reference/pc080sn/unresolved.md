# PC080SN Reference — Unresolved

Genuine remaining unknowns only (not a history of corrected items). Hardware mapping, cell format, scroll registers, and draw order are established — see README + scene_initialization_assembly.md §7–§10.

1. **`clear_fill_tile_0x0020` decoded pixel bytes.** Layer behavior is fully determined (tilemap1 transparent → open cells reveal background; tilemap0 opaque). Whether tile 0x20's own 8×8×4 pixels are all pen-0 is a decoded-gfx-ROM byte detail, not yet inspected. Next: decode the `"pc080sn"` gfx region tile 0x20 (`gfx_8x8x4_packed_msb`).

2. **Selectors 4/5/6 exact event effects** *(outside PC080SN rendering scope)*. They are non-publication map commands consumed by event/scene logic (0x05127C position-gated spawns; 0x527CC sets a5@0x10E8=7). The exact per-value game effect is scene/event behavior, not a rendering question.

3. **Per-cell targets inside the text/number writers (0x03C4D2…0x03C950, 0x03BB48, 0x03C2E2).** Classified by base pointer (tilemap1 0xC08xxx/0xC09xxx); per-cell enumeration out of scope.

4. **Map-stream — resolved vs downgraded** *(see map_stream_format.md §6/§7/§8)*. RESOLVED: variable-length record format (indices 0–137: 120 len-1 + 18 len-2 `[dir,event]`); +1 walk drives the pointer (MAME-verified, not recomputed each frame); event bytes freeze the walk (proven); byte-value roles. **DOWNGRADED / still open:** (a) the exact route from event/encounter completion to the pointer re-seed — scene-init (the only re-seed) is reached only from config-driven level-start 0x045316; no event→scene-init path is traced; (b) record 138 length and the 0xFF boundary (candidate `[00 07]` + candidate sentinel; 157 bytes proven through 0x9C, 158 only if the candidate is accepted); (c) encounter-completion condition per event value (enemy/scene engine, out of scope); (d) selector **5** live behaviour (absent from stream); selector **7** (no consumer established — do not label it); (e) stage cardinality (0x5073A = 139 B, 48 targets, max 0x8A).
