# Phase 1 Execution Results — Revert + Ordering Fix

## 1. Exact Changes Applied

All changes applied to `specs/startup_title_remap.json` and `apps/rastan/src/main.c`.
No other files were modified.

---

### D-5 — Descriptor Attr Force Revert (5 entries)

| arcade_pc | Before (replacement_bytes) | After (replacement_bytes) |
|-----------|---------------------------|--------------------------|
| 0x05A11A | `30FC0080` | `30FC0000` |
| 0x05A13E | `30FC0080` | `30FC0000` |
| 0x05A188 | `30FC0080` | `30FC0000` |
| 0x05A1AC | `30FC0080` | `30FC0000` |
| 0x05A1D0 | `30FC0080` | `30FC0000` |

- Array: `opcode_replace`
- original_bytes unchanged: `30FC0000` (real arcade value)
- Size: 4 bytes each → 4 bytes each (no shift)
- All five entries are now identity replacements (original bytes pass through unchanged)

---

### D-7 — RTS Trampoline Extension Revert (1 entry)

| arcade_pc | original_bytes | Before (replacement_bytes) | After (replacement_bytes) |
|-----------|---------------|---------------------------|--------------------------|
| 0x059F90 | `4E75` | `61000124610000044E75` (10 bytes) | `4E75` (2 bytes) |

- Array: `opcode_replace`
- Before: 10-byte replacement clobbered bytes at 0x059F92-0x059F99 (destroyed `cmpiw #255,a5@(5000)` at 0x059F92 and `beqs 0x059FDE` at 0x059F98)
- After: plain rts restores 0x059F90 to 2 bytes; bytes at 0x059F92-0x059F99 remain as original ROM content (restored by identity pass)
- The `jsr 0x059F92` path from 0x051060 is no longer corrupted

---

### T-9 — Function Body Restore (1 entry)

| arcade_pc | original_bytes | Before (replacement_bytes) | After (replacement_bytes) |
|-----------|---------------|---------------------------|--------------------------|
| 0x0560DA | (52 bytes) | 26×`4E71` (52 NOP bytes) | same as original_bytes |

- Array: `opcode_replace`
- Before: entire function body silenced (NOP fill)
- After: function body restored — pointer-range check (cmpa.l #0xE0FF71A2) and conditional fill-call sequence are live
- Size: 52 bytes → 52 bytes (no shift)
- With T-7 NOPs already in place (A5@(0x10A0) pointer stale/zero), the cmpa comparison
  is expected to fail (stale pointer < 0xE0FF71A2), so the fill-call branch is skipped
  and the function returns cleanly without side effects

---

### C-3 — Tilemap Plane-A Hook Revert (1 entry)

| arcade_pc | original_bytes size | Before (replacement) | After (replacement) |
|-----------|--------------------|--------------------|-------------------|
| 0x055968 | 38 bytes | `4EB9{symbol:genesistan_hook_tilemap_plane_a}` + `4E75` + 14×`4E71` (36 bytes) | 19×`4E71` (38 bytes) |

- Array: `shift_replacements`
- Before: 36-byte replacement (−2 shift from original 38 bytes)
- After: 38-byte NOP fill (same size as original, 0 shift delta)
- Hook call `jsr genesistan_hook_tilemap_plane_a` removed
- Size restored to original: all shift_replacement entries after 0x055968 gain +2 bytes of shift budget

---

### C-4 — Tilemap Plane-B Hook Revert (1 entry)

| arcade_pc | original_bytes size | Before (replacement) | After (replacement) |
|-----------|--------------------|--------------------|-------------------|
| 0x055990 | 32 bytes | `4EB9{symbol:genesistan_hook_tilemap_plane_b}` + `4E75` + 11×`4E71` (30 bytes) | 16×`4E71` (32 bytes) |

- Array: `shift_replacements`
- Before: 30-byte replacement (−2 shift from original 32 bytes)
- After: 32-byte NOP fill (same size as original, 0 shift delta)
- Hook call `jsr genesistan_hook_tilemap_plane_b` removed
- Combined with C-3 restore: all entries after 0x055990 gain +4 bytes total vs before

---

### Order Fix Patch A — Producer into Renderer Slot (shift_replacements)

| arcade_pc | original_bytes | Before (replacement) | After (replacement) |
|-----------|---------------|---------------------|-------------------|
| 0x03A8E0 | `61001020` (4 bytes) | `4EB9{symbol:genesistan_render_sprites_vdp_bridge}` (6 bytes) | `4EB900059F5E` (6 bytes) |

- Array: `shift_replacements`
- Size: 4→6 bytes (+2 shift) — same net shift as before (no change to shift budget for subsequent entries)
- Replacement calls `jsr 0x059F5E` (producer: clear + B-block init)
- `rom_absolute_call_relocation` will update 0x059F5E to its correct relocated genesis address
- Producer now occupies the FIRST call slot in the title init state-0 sequence

---

### Order Fix Patch B — Renderer into Producer Slot (opcode_replace, new entry)

| arcade_pc | original_bytes | replacement_bytes |
|-----------|---------------|------------------|
| 0x03A8E4 | `4EB900059F5E` (6 bytes) | `4EB9{symbol:genesistan_render_sprites_vdp_bridge}` (6 bytes) |

- Array: `opcode_replace` (NEW entry, inserted before 0x03AD3C)
- Size: 6→6 bytes (no shift)
- Renderer now occupies the SECOND call slot (after producer)
- `{symbol:genesistan_render_sprites_vdp_bridge}` resolves at link time

---

### main.c — Col/Row Counter Reset Lines Removed

```c
// REMOVED from SCREEN_FRONTEND_LIVE loop:
genesistan_hook_col_a = 0;  // line 1932 (old)
genesistan_hook_row_a = 8;  // line 1933 (old)
genesistan_hook_col_b = 0;  // line 1934 (old)
genesistan_hook_row_b = 8;  // line 1935 (old)
```

- These were dead code once C-3/C-4 hooks no longer fire
- The hook functions `genesistan_hook_tilemap_plane_a/b` remain in main.c but are never called
- No other changes to main.c

---

## 2. Byte-Level Before/After Summary

### Title Init State-0 Execution Sequence (arcade 0x03A8D2–0x03A8F6)

**Before Phase 1**:
```
0x03A8D6  bsrw 0x03AD4C                           [T-1: clears descriptor windows]
0x03A8DA  bsrw 0x03AE5A                           [T-2: clears text shadow]
0x03A8DE  moveq #1, D1
0x03A8E0  jsr genesistan_render_sprites_vdp_bridge  [RENDERER — WRONG: fires first]
0x03A8E4  jsr 0x059F5E                             [PRODUCER — fires second, too late]
0x03A8EA  moveq #9, D0
0x03A8EC  bsrw 0x3BB48                             [text dispatch]
```

**After Phase 1**:
```
0x03A8D6  bsrw 0x03AD4C                           [T-1: clears descriptor windows]
0x03A8DA  bsrw 0x03AE5A                           [T-2: clears text shadow]
0x03A8DE  moveq #1, D1
0x03A8E0  jsr 0x059F5E (relocated)                [PRODUCER — fires FIRST: correct]
0x03A8E4  jsr genesistan_render_sprites_vdp_bridge [RENDERER — fires SECOND: correct]
0x03A8EA  moveq #9, D0
0x03A8EC  bsrw 0x3BB48                             [text dispatch — unchanged]
```

### Producer at 0x059F5E — state after D-7 revert

**Before Phase 1 (D-7 active)**:
```
0x059F5E  movew #8, D1
0x059F62  moveal #0xE0FF11FE, A0          [D-1 retarget]
0x059F68  clrl D0
0x059F6A  movel D0, a0@+                  [x8: clears block-A]
...
0x059F72  movew #4, D1
0x059F76  moveal #0xE0FF01BC, A0          [D-2 retarget]
0x059F7C  movew #0x0080, a0@+             [4 B-block entries]
0x059F80  movew #0x0000, a0@+
0x059F84  movew #0x0000, a0@+
0x059F88  movew #0x0000, a0@+
0x059F8C  subqw #1, D1
0x059F8E  bnes 0x059F7C
0x059F90  bsr +0x124                      [D-7: calls block-A builder]
0x059F94  bsr +0x004                      [D-7: calls block-B builder continuation]
0x059F98  rts
```

**After Phase 1 (D-7 reverted)**:
```
0x059F5E  movew #8, D1
0x059F62  moveal #0xE0FF11FE, A0          [D-1 retarget]
0x059F68  clrl D0
0x059F6A  movel D0, a0@+                  [x8: clears block-A to zero]
...
0x059F72  movew #4, D1
0x059F76  moveal #0xE0FF01BC, A0          [D-2 retarget]
0x059F7C  movew #0x0080, a0@+             [4 B-block entries with initial values]
0x059F80  movew #0x0000, a0@+
0x059F84  movew #0x0000, a0@+
0x059F88  movew #0x0000, a0@+
0x059F8C  subqw #1, D1
0x059F8E  bnes 0x059F7C
0x059F90  rts                             [D-7 removed: plain return]
0x059F92  cmpiw #255, a5@(5000)           [RESTORED: original block-B path]
0x059F98  beqs 0x059FDE                   [RESTORED: original conditional]
0x059F9A  moveal #0xE0FF01BC, A0          [D-2 retarget continues here]
```

---

## 3. Execution Trace (Ordering Proof)

**Expected execution trace for Build 272 (Phase 1 applied)**:

```
TITLE INIT STATE=0 PASS:
  [T-1] jsr 0x03AD4C  → clears descriptor windows (0xE0FF11FE, 0xE0FF01BC)
  [T-2] jsr 0x03AE5A  → clears text shadow (0xE0FFC84C)
  [Patch A] jsr 0x059F5E (relocated)  → PRODUCER: re-clears block-A, writes initial B-block
  [Patch B] jsr genesistan_render_sprites_vdp_bridge  → RENDERER: reads descriptor windows

EXECUTION ORDER PROOF:
  HIT 059F5E = N  (producer)
  HIT genesistan_render_sprites_vdp_bridge = N  (renderer, fires AFTER producer)
  → producer HIT count increments before renderer HIT count within same state=0 pass
```

**Expected descriptor state at renderer entry point**:
- block-A (0xE0FF11FE): zero (producer cleared it, D-7 builder removed — Phase 2 adds content)
- block-B (0xE0FF01BC): 4 entries each `0080 0000 0000 0000`
- No 0x0080 attr contamination from D-5 (all descriptor attr writes now produce 0x0000)

**Expected visual**: Title text still renders (`CREDI` or equivalent — T-4/T-5/C-1 path
unaffected). Logo sprites not visible yet (block-A content building is Phase 2).
This is correct and expected for Phase 1.

---

## 4. Validation Results

| Check | Result |
|-------|--------|
| D-5: no `30FC0080` in spec | PASS — grep confirms all 5 entries show `30FC0000` |
| D-7: 0x059F90 = plain `4E75` | PASS — grep confirms `"replacement_bytes": "4E75"` |
| T-9: 0x0560DA = original bytes | PASS — replacement_bytes matches original_bytes |
| C-3: 0x055968 = 38-byte NOP fill | PASS — 19×`4E71` = 38 bytes confirmed |
| C-4: 0x055990 = 32-byte NOP fill | PASS — 16×`4E71` = 32 bytes confirmed |
| Patch A: 0x03A8E0 calls producer | PASS — `4EB900059F5E` in replacement_bytes |
| Patch B: 0x03A8E4 calls renderer | PASS — `{symbol:genesistan_render_sprites_vdp_bridge}` |
| main.c col/row resets removed | PASS — 4 lines removed from SCREEN_FRONTEND_LIVE |
| No other files modified | PASS — only startup_title_remap.json and main.c changed |
| No new hooks introduced | PASS — zero new functions or helper calls added |
| No Phase 2 items touched | PASS — WRAM buffers, VBlank, tilemap, palette unchanged |

**Size correctness**:
- C-3 restored to 38 bytes (was 36): +2 to accumulated shift after 0x055968
- C-4 restored to 32 bytes (was 30): +2 to accumulated shift after 0x055990
- Net: all entries after 0x055990 see +4 bytes more accumulated shift than before
- shift_table_patcher recomputes all displacements on rebuild — this is handled automatically

**D-7 byte clobber restoration**:
- Before: 0x059F90-0x059F99 were `61 00 01 24 61 00 00 04 4E 75` (trampoline)
- After: 0x059F90 = `4E 75`, 0x059F92 = `0C 6D 00 FF 13 88` (cmpiw), 0x059F98 = `67 44` (beqs)
- The `jsr 0x059F92` at 0x051060 now calls valid code (cmpiw gate for block-B path)

---

## 5. Anomalies

### Anomaly 1: Block-A content is zero after ordering fix

After D-7 revert, the block-A builder (which D-7 was calling via bsr) is no longer
invoked from the 0x059F5E producer path. Block-A remains zero after the producer runs.
The renderer will build an empty SAT from zero descriptors. Logo sprites will not be
visible.

**This is expected and correct for Phase 1.** Block-A content building is Phase 2 work.
The ordering fix establishes the clean call sequence that Phase 2 will build upon.

### Anomaly 2: B-block initial values from 0x059F7C fill loop

The fill loop writes `0x0080 0x0000 0x0000 0x0000` into each B-block entry. The first
word 0x0080 was the value before D-2 retargets (it came from `movew #128, a0@+` at
original 0x059F7C). The renderer will read this. In Genesis SAT format, 0x0080 as
the first word is the Y-coordinate (128). This places sprites mid-screen. The tile code
(word 2) is zero — which resolves to tile 0 in VRAM. These may appear as garbage sprites
or be invisible depending on tile 0 content.

**No action needed for Phase 1.** Phase 2 will populate the B-block with real content.

### Anomaly 3: genesistan_hook_tilemap_plane_a/b dead code

These C functions remain in main.c but are now never called. No compiler warning is
expected (they are `externally_visible`). They can be removed in a later cleanup pass
but are harmless in place.
