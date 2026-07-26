# PC080SN Core Publishers — Unresolved

Genuine unknowns only. Each: exact address · missing fact · why the asm here doesn't settle it · smallest next observation.

1. **`a5@0x10A8` (0x10D0A8) selector — write sites & value semantics.**
   - Missing: where 0/1/2/4/5/6 are written and what each means (dispatch §1 only tests `==0`; cell §5 tests `==2` for direction).
   - Why unsettled: this checkpoint captured the *reads/compares* (0x0503E4, 0x05043C, 0x05127C, 0x055738, 0x0557C4, 0x0556A6, 0x05275C…), not the stores.
   - Next: Ghidra search for `move*,a5@(4264)` stores; classify by caller (trigger vs scene-setup). Small static task.

2. **`pc080sn_tilemap0_0xC00000` producer.**
   - Missing: which routine(s) populate tilemap0 and whether it streams or is scene-init-only. Proven only that `0x055E54` (guard `a5@0x139A==2`) points the strip_A cursor at `0xC00400`.
   - Why unsettled: out of this checkpoint's scope (core publishers = tilemap1).
   - Next: the scene-init checkpoint — trace the `0x055E54` caller chain and the writes to 0xC00000–0xC03FFF.

3. **PC080SN name-RAM word semantics (word0 vs word1).**
   - Missing: hardware meaning of word0 (from source `a1@0x10D200`; runtime shows constant `0x0003`) vs word1 (tile). Whether word0 is a color/priority/attribute word and the bit layout.
   - Why unsettled: the producer copies opaque words; bit meaning is a PC080SN-hardware fact, not visible in the copy.
   - Next: read MAME `taito/pc080sn.cpp` tile-decode for the two-word entry format; confirm against a few live word pairs.

4. **`0x055A14` second collision write (constant `1`, index `((dest−0xC08000)−256)&0x3FFF`).**
   - Missing: why the direction-aware producer stamps a `1` one row back.
   - Why unsettled: no comment in the asm; likely a leading-edge/seam collision marker for reversed streaming.
   - Next: during a reversal capture, watch `0x10DE00` around the stamped index vs player collision behavior.

5. **`0x558A2` post-advance + `0x055904` descriptor rebuild — full logic.**
   - Missing: the exact descriptor/source-table rebuild and the `a5@0x10CA/0x10CC` advance/wrap.
   - Why unsettled: intentionally scope-limited here to the fields the publishers consume.
   - Next: fold into the triggers/ring-behavior checkpoint.
