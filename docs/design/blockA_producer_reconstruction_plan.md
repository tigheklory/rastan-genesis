# Block-A Producer Reconstruction Plan

## 1. Purpose

Document the complete analysis of the block-A sprite descriptor builder subroutine, define
the entry format for block-A descriptor buffers, specify the minimal Phase 2 patch required to
restore logo sprite production, and provide a full validation plan.

Phase 1 established the correct execution order (producer before renderer) and cleared block-A
to zero on each title-init pass. Phase 2 must restore the actual sprite descriptor content
by calling the block-A builder before the producer returns.

---

## 2. Block-A Memory Structure (entry format — all words defined)

Block-A base address: `0xE0FF11FE` (A5+0x11B2, where A5=0xE0FF004C)

Each entry is **8 bytes (4 words)**:

| Offset | Word | Field name | Meaning |
|--------|------|-----------|---------|
| +0 | word0 | attr/flags (`data`) | Sprite attribute byte. If `data == 0`, renderer forces `y_raw = 0x0180` (off-screen sentinel, effectively hidden). Must be nonzero for visible sprites. |
| +2 | word1 | y_raw (`y position`) | Raw Y coordinate. Value `0x0180` forces off-screen. Renderer applies sign extension: if `y_raw > 0x0140`, `y = y_raw - 0x0200`. |
| +4 | word2 | tile code (`code & 0x3FFF`) | Tile index for the sprite graphic. If `tile_base < 0` (tile not loaded), entry is skipped. |
| +6 | word3 | x position | Raw X coordinate. Renderer applies sign extension: if `x > 0x0140`, `x = x - 0x0200`. |

The renderer (`genesistan_render_sprites_vdp` at genesis `0x202B80`) reads:
- Block-A: 18 entries at workram offset `0x11B2` = address `0xE0FF11FE`
- Block-B: 4 entries at workram offset `0x0170` = address `0xE0FF01BC`

Source in `apps/rastan/src/main.c`, line 1563:
```c
// word0: attr/flags
// word1: y position (0x0180 sentinel = hidden)
// word2: tile code
// word3: x position
```

Entry visibility rule: `if (data == 0) y_raw = 0x0180;` forces off-screen. Both the attr field
and valid tile code must be nonzero for a sprite to appear on screen.

---

## 3. Arcade Block-A Build Path (what the builder does step by step)

### Function layout

The block-A builder spans arcade `0x05A098`–`0x05A258` (genesis post-Phase-2: `0x05A2B4`–`0x05A474`).

**Preamble (arcade `0x05A098`, genesis pre-Phase-2 `0x05A2AE`, post-Phase-2 `0x05A2B4`, 32 bytes):**

```
302D 013A   MOVE.W a5@(0x013A), D0    ; load substate/animation counter
0800 000F   BTST   #15, D0            ; test reset flag
6704        BEQ.S  +4                  ; skip clear if not set
426D 013A   CLR.W  a5@(0x013A)        ; clear counter if reset flagged
343C 0010   MOVE.W #0x0010, D2        ; D2 = 16 (tile/column count)
363C 00E8   MOVE.W #0x00E8, D3        ; D3 = 0xE8 (Y-base)
207C E0FF 11FE  MOVEA.L #0xE0FF11FE, A0  ; A0 -> block-A base (self-contained setup)
302D 013A   MOVE.W a5@(0x013A), D0    ; reload counter (may now be 0)
```

This preamble is **critical**: it sets `A0 = 0xE0FF11FE` (the block-A write destination),
initializes `D2` and `D3`, and manages the animation counter. Without running the preamble,
the function body writes to whatever `A0` currently points to — which is `0xE0FF01DC` (past
the B-block area) after the producer runs, NOT the block-A region.

**D-7 historical entry point:** The old D-7 patch called via `BSR +0x0124` from arcade
`0x059F90`, landing at arcade `0x05A0B8` (genesis pre-Phase-2 `0x05A2CE`), which is **32 bytes
into the function, after the preamble**. This mid-function entry relies on `A0`, `D2`, `D3`
already being correctly set, which they were not in the producer context. Phase 2 must call
the **full entry** at arcade `0x05A098`.

**Function body (arcade `0x05A0B8`, genesis pre-Phase-2 `0x05A2CE`):**

Confirmed ROM bytes at genesis `0x05A2CE`:
```
E048        ASR.W  #8, D0             ; extract palette/attr byte from animation counter
E648        LSR.W  #3, D0
0240 0007   ANDI.W #7, D0             ; mask to 3 bits (palette bank index 0-7)
0040 0008   ORI.W  #8, D0             ; set attr flag bit
3B40 12A6   MOVE.W D0, a5@(0x12A6)   ; store computed attr byte
066D 0010 12A4  ADDI.W #0x0010, a5@(0x12A4)  ; advance animation phase counter
4281        CLR.L  D1                 ; clear entry iterator
4284        CLR.L  D4
4240        CLR.W  D0
322D 12A4   MOVE.W a5@(0x12A4), D1   ; load sprite table base index
382D 12A6   MOVE.W a5@(0x12A6), D4   ; load computed attr
3C2D 1306   MOVE.W a5@(0x1306), D6   ; load sprite control flags
```

The function iterates through up to 13 sprite entries (clamped from `D4` if > 0x0C),
testing control bits in `D6`, loading sprite positions from `a5@(0x130A)` and related offsets,
and writing 4-word descriptor entries to `(A0)+`:

**Active sprite write path (around genesis `0x05A330`):**
```
30FC 0000   MOVE.W #0x0000, (A0)+    ; word0 = 0 (attr placeholder)
30C3        MOVE.W D3, (A0)+          ; word1 = D3 (Y base = 0xE8)
0640 03CA   ADDI.W #0x03CA, D0       ; compute tile row offset
30C0        MOVE.W D0, (A0)+          ; word2 = tile code + row offset
30C2        MOVE.W D2, (A0)+          ; word3 = D2 (X coordinate)
0642 0010   ADDI.W #0x0010, D2       ; advance X by 0x10 for next sprite
```

**Hidden/skip write path (around genesis `0x05A354`):**
```
30FC 0000   MOVE.W #0x0000, (A0)+    ; word0 = 0 (hidden)
30C3        MOVE.W D3, (A0)+          ; word1 = D3
30FC 03CC   MOVE.W #0x03CC, (A0)+    ; word2 = 0x03CC (fixed tile reference)
30C2        MOVE.W D2, (A0)+          ; word3 = D2
0642 0010   ADDI.W #0x0010, D2
```

**Function ends at arcade ~`0x05A258`:** `RTS` (4E75).

The function reads A5-relative state: animation counter at `a5@(0x013A)`, sprite table index
at `a5@(0x12A4)`, attr byte at `a5@(0x12A6)`, control flags at `a5@(0x1306)`, sprite positions
at `a5@(0x130A)`. A5 is always the workram base in this context, so all reads succeed.

**Registers used on entry:**
- `A5`: workram base (required, always present in arcade context)
- `A0`: block-A base `0xE0FF11FE` — set by preamble, NOT by caller
- `D0`: loaded by preamble from `a5@(0x013A)` — NOT from caller
- `D2`, `D3`: set by preamble — NOT from caller

**Calling convention:** The function is self-contained when called at the full entry
(arcade `0x05A098`). No pre-setup by caller is required beyond `A5` pointing to workram.

---

## 4. What Was Lost in Phase 1 (D-7 removal removed the call to the builder)

**D-7 original bytes** at arcade `0x059F90`:
```
61 00 01 24  BSR.W +0x0124   ; calls arcade 0x05A0B8 (mid-entry, bypassing preamble)
61 00 00 04  BSR.W +0x0004   ; calls arcade 0x059F9A (block-B continuation)
4E 75        RTS
```

**D-7 problem:** The 10-byte trampoline overwrote bytes at arcade `0x059F92`–`0x059F99`,
destroying the `CMPI.W #255, a5@(5000)` instruction at `0x059F92` and `BEQ.S` at `0x059F98`.
This corrupted the `JSR 0x059F92` path from `0x051060`.

**Phase 1 action:** Reverted `0x059F90` to plain `4E75` (2 bytes). This:
- Restored the `cmpiw` at `0x059F92` and `beqs` at `0x059F98`
- Removed both BSR calls — block-A builder call silenced
- Block-A remains zero after producer runs (expected Phase 1 baseline)

The D-7 note in the spec explicitly states: *"Block-A/B builder calls from this path are
gone; will be added explicitly in Phase 2."*

---

## 5. Minimal Required Logic (is calling the full entry sufficient?)

**YES.** Calling the FULL entry at arcade `0x05A098` IS sufficient because:

1. The preamble sets `A0 = 0xE0FF11FE` unconditionally — correct block-A base address.
2. The preamble sets `D2 = 0x0010` (tile column width) unconditionally.
3. The preamble sets `D3 = 0x00E8` (Y base) unconditionally.
4. The preamble loads `D0 = a5@(0x013A)` (animation counter from workram).
5. `A5` is always the workram base in this context — all A5-relative reads succeed.
6. The function ends with `RTS` — returns cleanly to the producer's caller.

**Why the mid-entry `0x05A0B8` / `0x05A2CE` is NOT sufficient alone:**
Calling only `0x05A2CE` (the post-preamble body) skips `A0`, `D2`, and `D3` initialization.
At the time of the producer's execution, `A0 = 0xE0FF01DC` (past the B-block fill area).
The body would write sprites to the wrong WRAM location entirely.

**Additional requirement:** None. A single `JSR` to the full entry immediately before the
producer's `RTS` is the complete Phase 2 change. No register pre-setup by the caller is needed.

---

## 6. Phase 2 Implementation Target (exact spec patch definition)

### Location

The patch modifies the existing `shift_replacements` entry at `arcade_pc = 0x059F90`.
This entry was created during Phase 1 (D-7 revert) with identity replacement (`4e75` → `4e75`).
The D-7 note explicitly reserved this slot for Phase 2.

**Entry type: `shift_replacement`** (NOT `opcode_replace`), because the replacement grows from
2 bytes to 8 bytes (delta = +6). This size change shifts all subsequent arcade code addresses
by +6 in genesis ROM space. `opcode_replace` is for same-size substitutions only.

### Address computation

| Step | Value |
|------|-------|
| Callsite arcade address | `0x059F90` |
| shift_before(`0x059F90`) | 22 bytes |
| Callsite genesis address | `0x05A1A6` (= `0x059F90 + 0x200 + 22`) |
| Target arcade address (block-A builder full entry) | `0x05A098` |
| Accumulated shift before `0x05A098` (before Phase 2) | 22 bytes |
| Phase 2 delta at `0x059F90` (2 → 8 bytes) | +6 bytes |
| Accumulated shift before `0x05A098` (after Phase 2) | **28 bytes** |
| Correct genesis address for target (after Phase 2) | `0x05A2B4` (= `0x05A098 + 0x200 + 28`) |

### Embedded address formula (critical — see absolute_call_target_fix_plan.md)

The patcher (`rom_absolute_call_relocation`) applies exactly **+0x200** (base relocation) to
raw addresses embedded in `replacement_bytes`. It does NOT apply accumulated shift. Therefore:

```
correct_genesis_addr = 0x05A098 + 0x200 + 28 = 0x05A2B4
embedded_value       = correct_genesis_addr - 0x200 = 0x05A0B4
```

This mirrors the proven formula from `absolute_call_target_fix_plan.md` Strategy B:
- TC1: embedded `0x059F5E` → ROM output `0x05A15E` = embedded + 0x200
- Formula: `embedded = correct_genesis_addr - 0x200`

### Spec change (shift_replacements entry at `0x059F90`)

**BEFORE (Phase 1, current):**
```json
{
  "arcade_pc": "0x059F90",
  "original_bytes": "4E75",
  "replacement_bytes": "4E75",
  "note": "D-7 REVERT: ... Block-A/B builder calls ... will be added explicitly in Phase 2."
}
```

**AFTER (Phase 2):**
```json
{
  "arcade_pc": "0x059F90",
  "original_bytes": "4e75",
  "replacement_bytes": "4eb90005a0b44e75",
  "note": "PHASE 2: JSR to block-A builder full entry (arcade 0x05A098, genesis 0x05A2B4 post-Phase-2). embedded=0x05A0B4; patcher adds +0x200 -> ROM target 0x05A2B4. Formula: embedded = 0x05A2B4 - 0x200 = 0x05A0B4. delta: +6 (2->8 bytes)."
}
```

**Replacement bytes breakdown:**
```
4eb9        JSR abs.l opcode (2 bytes)
0005a0b4    pre-compensated embedded address (4 bytes): patcher adds +0x200 -> 0x05A2B4
4e75        RTS (2 bytes): producer return
```

**IMPORTANT — do NOT embed `0x05A2B4` directly.** If `0x05A2B4` were embedded, the patcher
would produce `0x05A4B4` (wrong). The pre-compensation formula is mandatory.

**Shift impact:** delta changes from `0` to `+6`. All genesis code for arcade addresses
> `0x059F90` shifts by +6 bytes. The block-A builder itself shifts from `0x05A2AE` to
`0x05A2B4`, which is exactly the target the embedded value resolves to.

**No other changes required.** No `.c` files, Makefile, or other spec files need modification.

---

## 7. Validation Plan (static + memory + renderer + visual)

### 7.1 Static check (post-build ROM inspection)

After Phase 2 rebuild, verify ROM bytes at the callsite:

```python
import struct
with open('dist/Rastan_NNN.bin', 'rb') as f:
    # Callsite: genesis 0x05A1A6
    f.seek(0x05A1A6)
    data = f.read(8)
print(data.hex())
# Expected: 4eb90005a2b44e75
# Meaning:  JSR 0x05A2B4 + RTS
# (patcher took embedded 0x05A0B4 + 0x200 = 0x05A2B4 ✓)
```

Also verify the builder preamble is at the post-Phase-2 target genesis address:
```python
with open('dist/Rastan_NNN.bin', 'rb') as f:
    f.seek(0x05A2B4)
    data = f.read(8)
print(data.hex())
# Expected: 302d013a0800000f
# Meaning:  MOVE.W a5@(0x013A),D0 / BTST #15,D0  (start of preamble)
# (preamble shifts from 0x05A2AE to 0x05A2B4 after Phase 2 adds 6 bytes)
```

Pass: callsite contains `4eb9 0005a2b4 4e75`, target contains `302d 013a`.
Fail: callsite still contains only `4e75`, or ROM at `0x05A2B4` is not preamble bytes.

### 7.2 Memory check (runtime probe via MAME/BlastEm tap)

Probe condition: tap at `0x202B80` (genesistan_render_sprites_vdp_bridge entry).

```
EXPECT at renderer entry (after producer has run):
  0xE0FF11FE: nonzero (at least one word in block-A entries is nonzero)
  0xE0FF1200: nonzero (word2 = tile code, should be nonzero for logo sprite)

FAIL if:
  0xE0FF11FE..0xE0FF123E: all zeros (builder did not run)
```

In BlastEm Lua probe: `memory.read_word(0xE0FF11FE)` at renderer entry should be nonzero.

In MAME Lua probe:
```lua
cpu:space(AS_PROGRAM):read_u16(0xE0FF11FE)  -- should be nonzero
```

### 7.3 Renderer check (sprite cache nonzero)

Using the existing sprite cache probe (build probe script):
- `sprite_cache_nonzero_words` should be `> 0` (was `0` in pre-Phase 2 builds)
- `sprite_code0` (first tile code) should be nonzero

Pass: `sprite_cache_nonzero_words > 0`
Fail: `sprite_cache_nonzero_words = 0` (renderer still sees all-zero block-A)

### 7.4 Visual check (emulator display)

Run in BlastEm or Exodus with title screen path active.

**Expected:** Logo sprite tiles appear on screen (partial or full Rastan logo).
**Acceptable partial pass:** Any nonzero sprite pixels in the expected logo position.
**Fail:** Title text renders (CREDIT/TILT still works from Phase 1) but no sprite tiles appear.

---

## 8. Final Conclusion

The block-A builder function (arcade entry `0x05A098`, pre-Phase-2 genesis `0x05A2AE`,
post-Phase-2 genesis `0x05A2B4`) is a fully self-contained sprite descriptor producer. Its
32-byte preamble unconditionally initializes `A0 = 0xE0FF11FE`, `D2 = 0x0010`, and
`D3 = 0x00E8` before the main loop writes 4-word sprite entries. The function reads animation
state from `A5`-relative workram locations and writes populated descriptor tuples to block-A.
With `A5` always pointing to workram base, the function is self-sufficient when called at
the full entry — no pre-setup by the caller is needed.

Phase 1 removed the D-7 BSR call (which targeted the mid-entry `0x05A0B8`, bypassing the
preamble entirely), leaving block-A at zero. Phase 2 requires a single spec change: replace
the identity `4e75` at the `0x059F90` shift_replacements entry with `4eb90005a0b44e75`
(JSR pre-compensated + RTS). The embedded value `0x05A0B4` is pre-compensated per
absolute_call_target_fix_plan.md Strategy B: the patcher adds +0x200 producing final ROM
target `0x05A2B4` (the post-Phase-2 genesis address of the full builder entry preamble).

0x05A2CE sufficiency verdict: NO — mid-entry lacks preamble; A0/D2/D3 not set. Full entry 0x05A098 IS sufficient (YES).
Phase 2 patch target: shift_replacement at arcade 0x059F90 → JSR 0x05A2B4 (embedded 0x05A0B4) + RTS (8 bytes)
Block-A builder at 0x05A2CE is confirmed as the missing sprite producer; Phase 2 requires restoring its execution in the producer path.
