# PC080SN Core Publishers — Unresolved

Genuine unknowns only. Each: exact address · missing fact · why the asm here doesn't settle it · smallest next observation.

1. **`a5@0x10A8` selectors 4/5/6 — exact per-value event semantics.**
   - RESOLVED (scene_initialization): 4/5/6 are NON-publication map commands (the direction dispatcher matches only 0/1/2, so they publish nothing). 4/5 are position-gated event/spawn triggers (0x05127C, gated by a5@0x11DE); 4/5/6 also set a5@0x10E8=7 (0x527CC).
   - Missing: the exact game effect of each (which spawn/event/scene-state); this is scene/event logic, not PC080SN.
   - Next: a scene/event-logic checkpoint (out of the PC080SN reference scope).

2. **`0x055B8E` → tilemap0 publisher (0x55C4A) gameplay activation.**
   - RESOLVED (tilemap0_producers): tilemap0 is populated by the chain 0x55C4A→0x55C5E→0x55C7A (64 sub-cells, no collision, tables 0x10D100/0x10D104), driven by the scene fill loop 0x0503E4. Tilemap0 = layer A = background.
   - Missing: whether the SECOND caller `0x055B8E` runs during gameplay (would mean tilemap0 streams). MAME shows layer-A scroll static during Stage 1, suggesting not — unproven.
   - Next: reconstruct 0x055B8E's caller/guard, or MAME-tap 0xC00000 writes during gameplay.

3. **PC080SN name-RAM word semantics (word0 vs word1).**
   - Missing: hardware meaning of word0 (from source `a1@0x10D080`; runtime shows constant `0x0003`) vs word1 (tile). Whether word0 is a color/priority/attribute word and the bit layout. (Known: clear-state word0=0x0000 (0x0561B6), streamed word0=0x0003; blank/base TILE = 0x0020.)
   - Why unsettled: the producer copies opaque words; bit meaning is a PC080SN-hardware fact, not visible in the copy.
   - Next: read MAME `taito/pc080sn.cpp` tile-decode for the two-word entry format; confirm against a few live word pairs.

4. **0xC0C000 quadrant content.**
   - RESOLVED (scene_initialization §7): **0xC04000 IS content-written** — the sel==1 scene-fill path (0x050420) uses it as the tilemap1 cursor a5@0x10A4, so some scenes render from it.
   - Missing: whether 0xC0C000 ever holds content (only boot-lea'd/cleared; no scene/gameplay cursor targets it).
   - Next: confirm from taito/pc080sn.cpp whether 0xC0C000 is a hardware mirror/auxiliary region.

5. **Per-cell targets inside the text/number writers (0x03C4D2…0x03C950, 0x03BB48, 0x03C2E2).**
   - Missing: the individual computed cell addresses (base+offset) each writer hits.
   - Why unsettled: classified by base pointer (all tilemap1 0xC08xxx/0xC09xxx); per-cell enumeration is out of inventory scope.
   - Next: the HUD/text reconstruction checkpoint.
