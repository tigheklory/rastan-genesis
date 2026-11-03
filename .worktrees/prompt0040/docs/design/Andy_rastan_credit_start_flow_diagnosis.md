# Andy — Rastan Credit/Start Non-Progression Diagnosis

**Date**: 2026-04-06
**Scope**: `apps/rastan-direct` — credit accumulation and start-button flow
**State at diagnosis**: Game executes without crash, checkerboard renders, PC runs in 0x046FCxxx range, no transition to gameplay.

---

## 1. Executive Summary

The game does not progress because credits can never be incremented. The arcade code counts
credits through an **edge-detection mechanism** on bit 5 of 0x390007 (P1 coin gate), bit 6 of
0x390007 (P2 coin gate), and bit 0 of 0x390007 (service coin). All three bits require a
1→0→1 transition on the shadow byte to fire the credit increment. The current
`rastan_direct_update_inputs` writes `genesistan_shadow_input_390007 = 0xFF` unconditionally
every frame. The bit values never change. No 1→0 edge ever occurs. The credit counter
`a5@(0x12)` remains zero indefinitely.

A secondary defect also exists: the Genesis START button is mapped to bit 7 of
`genesistan_shadow_input_390001` (the joystick shadow byte), but the arcade code reads START
from bits 3+4 of `0x390007` (system byte) and bits 4+5 of `0x390001` (joystick byte). Bit 7 of
the joystick byte is never checked for START. Even if credits were somehow injected, pressing
the Genesis Start button would not trigger game start.

The single root cause blocking progression is the missing edge signal on
`genesistan_shadow_input_390007` bit 5.

---

## 2. Inputs Audited

1. `/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt` — full arcade 68000 disassembly.
   Traced coin read sites at 0x3A0A8, 0x3A0B2, 0x3A0C0, 0x3ACBA, 0x3ACBC,
   0x3AD1C, 0x3AD26; credit increment at 0x3AC04/0x3AC20, 0x3AC8A/0x3ACB2,
   0x3ACF4/0x3AD18; start detection at 0x3A490, 0x3A4A2, 0x3A91A.
2. `/home/tighe/projects/rastan-genesis/specs/rastan_direct_remap.json` — 30 opcode_replace entries.
   All coin and system read sites verified against patch table.
3. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/main_68k.s` — `rastan_direct_update_inputs`
   implementation audited in full (lines 248–305).
4. `docs/design/Andy_rastan_dip_defaults_and_flip_behavior.md` — DIP values, 0x380000 policy,
   active-low conventions confirmed.
5. `docs/design/Andy_sgdk_vs_rastan_direct_address_mapping_diagnosis.md` — prior root cause
   (incomplete TC0040IOC patches) confirmed resolved per Cody implementation log.
6. `AGENTS_LOG.md` — Cody's TC0040IOC full-coverage implementation entry read.

---

## 3. Coin Input Path Analysis

### 3.1 Coin read sites in the disassembly (from `build/maincpu.disasm.txt`)

| Arcade PC | Instruction | Shadow address | Purpose |
|-----------|-------------|----------------|---------|
| 0x03A0A8 | `btst #6, 0x390005` | `genesistan_shadow_input_390005` | Service coin lockout check |
| 0x03A0B2 | `btst #4, 0x390005` | `genesistan_shadow_input_390005` | Coin 1 lockout check |
| 0x03A0C0 | `btst #5, 0x390005` | `genesistan_shadow_input_390005` | Coin 2 lockout check |
| 0x03ACBA | `btst #6, 0x390005` | `genesistan_shadow_input_390005` | Service coin credit gate |
| 0x03ACBC | `btst #4, 0x390005` | `genesistan_shadow_input_390005` | Coin 1 credit gate |
| 0x03AD1C | `btst #6, 0x390005` | `genesistan_shadow_input_390005` | P2 service coin credit gate |
| 0x03AD26 | `btst #5, 0x390005` | `genesistan_shadow_input_390005` | P2 coin 2 credit gate |

All seven sites are patched in `rastan_direct_remap.json` to redirect to
`genesistan_shadow_input_390005`. Patch coverage for coin reads: **COMPLETE**.

### 3.2 What the coin read sites do

The `btst` instructions at 0x3A0A8/B2/C0 are in the **coin lockout management** subroutine, not
the credit counter. They control whether the hardware coin slot solenoid accepts or rejects
coins. These subroutines only write to `a5@(0x14)` (coin lockout state) and `0x380000` (hardware
register, suppressed by NOP patches).

The `btst` instructions at 0x3ACBA/BC and 0x3AD1C/26 are in the **credit accumulation** path.
They gate the final step of credit increment: if either coin 1 (bit 4) or service coin (bit 6)
of `shadow_390005` is low (active-low = pressed), the credit counter is incremented.

### 3.3 All coin read sites identified: YES
### 3.4 All correctly patched: YES

---

## 4. Credit Increment Logic Analysis

### 4.1 The credit increment mechanism

The credit counter is at `a5@(0x12)` (WRAM, A5+18). It is incremented in BCD at `0x3AC28`.

There are three independent entry paths into the credit increment routine:

**Path 1 — Service coin (via 0x390007 bit 0), at 0x3AC04:**
```
3ac04: btst #0, 0x390007    ; patched → btst #0, shadow_390007
3ac0c: bnes 0x3ac16         ; if bit=1 (inactive): check previous state
3ac0e: movew #1, a5@(0x20)  ; if bit=0 (active): set "was active" flag
3ac14: rts
3ac16: tstw a5@(0x20)       ; was previously active?
3ac1a: beqs 0x3ac14         ; no → return (no edge)
3ac1c: clrw a5@(0x20)       ; yes → clear flag
3ac20: → CREDIT INCREMENT   ; falling-edge detected
```

**Path 2 — P1 coin gate (via 0x390007 bit 5 + 0x390005 bit 4/6), at 0x3AC8A:**
```
3ac8a: cmpiw #153, a5@(0x12)  ; max credits check (99 BCD)
3ac90: bccw 0x3abf6            ; if >= 99, clear state and return
3ac94: btst #5, 0x390007       ; patched → btst #5, shadow_390007
3ac9c: beqs 0x3aca6            ; if bit=0 (active): check previous state
3ac9e: movew #1, a5@(0x22)     ; if bit=1 (inactive): set "was inactive" flag
3aca4: rts
3aca6: tstw a5@(0x22)          ; was previously inactive?
3acaa: beqw 0x3ac14            ; no → return (no edge)
3acae: clrw a5@(0x22)          ; yes → clear flag
3acb2: btst #6, shadow_390005  ; service coin pressed?
3acbc: btst #4, shadow_390005  ; coin 1 pressed?
3acc8: → bsr 0x3a08c           ; set a5@(702) flag
3accc: → lea a5@(6), a0        ; P1 coin count
3acd0: → addiw #1, a0@         ; increment P1 coin counter
3ace6: → movew a5@(18), d0     ; load credit count
3acf0: → braw 0x3ac2a          ; BCD increment credits
```

**Path 3 — P2 coin gate (via 0x390007 bit 6 + 0x390005 bit 5/6), at 0x3ACF4:**
```
3acf4: cmpiw #153, a5@(0x12)   ; max credits check
3acfe: btst #6, 0x390007        ; patched → btst #6, shadow_390007
3ad06: beqs 0x3ad10             ; if bit=0 (active): check previous state
3ad08: movew #1, a5@(0x24)      ; if bit=1 (inactive): set "was inactive" flag
3ad0e: rts
3ad10: tstw a5@(0x24)           ; was previously inactive?
3ad14: beqw 0x3ac14             ; no → return
3ad18: clrw a5@(0x24)           ; clear flag
3ad1c: btst #6, shadow_390005   ; service/P2 coin pressed?
3ad26: btst #5, shadow_390005   ; P2 coin 2 pressed?
3ad32: → credit increment for P2
```

### 4.2 Trigger type determination

**All three paths are EDGE-TRIGGERED.** Each path stores a "previous state" word in WRAM
(`a5@(0x20)`, `a5@(0x22)`, `a5@(0x24)`) and requires a specific transition:
- Path 1: bit 0 of `shadow_390007` must go 1→0 (rising edge on active-low input)
- Path 2: bit 5 of `shadow_390007` must go 1→0 (same)
- Path 3: bit 6 of `shadow_390007` must go 1→0 (same)

A sustained 0 (permanently active) does NOT increment credits. A sustained 1 (permanently
inactive) does NOT increment credits. Only a 1→0 transition increments credits.

### 4.3 Credit storage location: a5@(0x12) (WRAM word)
### 4.4 Increment logic traced: YES
### 4.5 Trigger type: EDGE (falling edge on active-low signal — bit must transition 1→0)

---

## 5. Start Condition Analysis

### 5.1 Start button reads in the disassembly

**Path A — System byte bits 3+4 (0x390007), at 0x3A490:**
```
3a490: moveb 0x390007, d0     ; patched → moveb shadow_390007, d0
3a496: andib #0x18, d0        ; mask bits 3+4 (P1 Start, P2 Start)
3a49a: cmpib #0x18, d0        ; are both inactive?
3a49e: bnew 0x3a504           ; if any bit is 0 → START PRESSED → game start path
```
If bits 3 and 4 are not both 1 (any start pressed), jumps to `0x3a504` which checks credits and
starts the game.

**Path B — Joystick byte bits 4+5 (0x390001), at 0x3A4C0:**
```
3a4a2: moveb 0x390001, d0     ; patched → moveb shadow_390001, d0
3a4c0: andiw #0x30, d0        ; mask bits 4+5 (P1 Start, P2 Start in joystick byte)
3a4c4: cmpiw #0x30, d0        ; are both inactive?
3a4c8: bnes 0x3a4f2           ; if any bit is 0 → start pressed via joystick path
```
This is the secondary check reached only when `shadow_390007` bits 3+4 are both 1 (0x18).

**Path C — Service start coins, at 0x3A91A:**
```
3a91a: moveb 0x390007, d0     ; patched → moveb shadow_390007, d0
3a920: btst #3, d0            ; P1 Start
3a924: beqs 0x3a92e           ; if bit=0 → P1 start → credit deduct + game init
3a926: btst #4, d0            ; P2 Start
3a92a: beqs 0x3a942           ; if bit=0 → P2 start → credit deduct + 2P game init
```
This path is in a different calling context (mid-game coin insert).

### 5.2 Summary of start conditions

The game starts when:
1. Path A: `shadow_390007` bit 3 or bit 4 = 0 (active-low) AND credits > 0
2. Path B: `shadow_390001` bit 4 or bit 5 = 0 (active-low) AND credits > 0

The TC0040IOC system byte (0x390007) layout confirmed from disassembly:
- Bit 0 = service mode coin (credit add trigger)
- Bit 1 = tilt (checked at 0x3A7B8)
- Bit 2 = test button (checked at 0x3AB96)
- Bit 3 = P1 Start (checked at 0x3A490, 0x3A91A)
- Bit 4 = P2 Start (checked at 0x3A490, 0x3A91A)
- Bit 5 = P1 coin gate (checked at 0x3AC94)
- Bit 6 = P2 coin gate / flip screen (checked at 0x3ACFE, 0x3AC94-0x3ACFE)

The joystick byte (0x390001) layout:
- Bits 0-3 = D-pad directions
- Bit 4 = P1 Start (checked at 0x3A4C0)
- Bit 5 = P2 Start (checked at 0x3A4C0)
- Bits 6-7 = attack / jump buttons

### 5.3 Start condition fully identified: YES

---

## 6. System Input Byte Analysis (0x390007)

### 6.1 All reads of 0x390007 in the disassembly

| Arcade PC | Instruction | Patched in JSON | Purpose |
|-----------|-------------|-----------------|---------|
| 0x03A490 | `moveb 0x390007, d0` | YES (→ shadow_390007) | Mask bits 3+4, P1/P2 start check |
| 0x03A7B8 | `btst #1, 0x390007` | YES (→ shadow_390007) | Tilt switch |
| 0x03A91A | `moveb 0x390007, d0` | YES (→ shadow_390007) | Bits 3+4 start in mid-game context |
| 0x03AB96 | `btst #2, 0x390007` | YES (→ shadow_390007) | Test button |
| 0x03AC04 | `btst #0, 0x390007` | YES (→ shadow_390007) | Service coin edge detect |
| 0x03AC94 | `btst #5, 0x390007` | YES (→ shadow_390007) | P1 coin gate edge detect |
| 0x03ACFE | `btst #6, 0x390007` | YES (→ shadow_390007) | P2 coin gate edge detect |

All seven 0x390007 read sites are patched. Patch coverage: COMPLETE.

### 6.2 Expected inactive state

Active-low convention. All bits = 1 (0xFF) = all switches open = fully inactive. The current
`rastan_direct_update_inputs` writes `shadow_390007 = 0xFF` unconditionally every frame. This is
correct for tilt (bit 1), test (bit 2), and service mode (bit 0 and 2), which must remain
inactive. It is incorrect for bits 3, 4, 5, and 6 which must PULSE (not hold) in response to
Genesis button presses.

### 6.3 Bits that require pulsing

| Bit | Function | Required behavior |
|-----|----------|-------------------|
| 0 | Service coin | 1→0 pulse when service coin button pressed |
| 3 | P1 Start | 0 when P1 Start pressed (level, not edge) |
| 4 | P2 Start | 0 when P2 Start pressed (level, not edge) |
| 5 | P1 coin gate | 1→0 pulse when P1 coin inserted |
| 6 | P2 coin gate | 1→0 pulse when P2 coin inserted |

Bits 1 (tilt) and 2 (test) must remain 1 (inactive).

### 6.4 System byte requirements fully defined: YES

---

## 7. Input Shadow Implementation Validation

### 7.1 Genesis pad read mechanism

`rastan_direct_update_inputs` (main_68k.s lines 248–305) reads the Genesis 3-button pad using
TH toggle:
- TH=0 read (stored in `%d1`): bit 4 = A button, bit 5 = Start button
- TH=1 read (stored in `%d0`): bits 0-5 = D-pad directions (UP, DOWN, LEFT, RIGHT, B=attack,
  C=jump)

This is the correct 3-button Mega Drive pad read sequence.

### 7.2 Current mapping

**Shadow joystick byte (`shadow_390001`):**
```asm
move.b  %d0, %d2
ori.b   #0xC0, %d2        ; preset bits 6+7 = inactive (active-low 1=unpressed)
btst    #4, %d1           ; A button
bne.s   .Lp1_a_done
bclr    #6, %d2           ; A pressed → clear bit 6 (attack)
.Lp1_a_done:
btst    #5, %d1           ; Start button
bne.s   .Lp1_start_done
bclr    #7, %d2           ; Start pressed → clear bit 7
.Lp1_start_done:
move.b  %d2, genesistan_shadow_input_390001
```

- Genesis A maps to bit 6 of shadow_390001 (attack)
- Genesis Start maps to **bit 7** of shadow_390001

But the arcade code checks **bit 4 (P1 Start) and bit 5 (P2 Start)** of the joystick byte for start detection at 0x3A4C0 (`andiw #0x30, d0`). Bit 7 is never checked for start in any code path found in the disassembly.

**Genesis Start is mapped to bit 7; arcade expects start at bit 4. This mapping is wrong.**

**Shadow coin byte (`shadow_390005`):**
```asm
moveq   #-1, %d4          ; d4 = 0xFF (all inactive, active-low)
btst    #6, %d2           ; check bit 6 of shadow_390001 (A button)
bne.s   .Lp1_coin_done
bclr    #4, %d4           ; A pressed → clear bit 4 (coin 1)
bclr    #6, %d4           ; also clear bit 6 (service coin)
.Lp1_coin_done:
; same for P2
move.b  %d4, genesistan_shadow_input_390005
```

When Genesis A is pressed, bits 4 AND 6 of `shadow_390005` are simultaneously cleared.
This creates a conflict: at 0x3A0A8, `btst #6, shadow_390005` fires first (Z flag set = bit 6
is 0 = active), and `beqs 0x3A0CE` returns immediately — bypassing the coin 1 (bit 4) check
entirely. The coin lockout function exits without processing the coin 1 signal. (Note: this is
the lockout path, not the credit path, but the conflict is present.)

**Shadow system byte (`shadow_390007`):**
```asm
moveq   #-1, %d5          ; d5 = 0xFF
move.b  %d5, genesistan_shadow_input_390007
```

Shadow_390007 is always 0xFF regardless of any Genesis button state.

### 7.3 Default state analysis

| Shadow byte | Default (no buttons) | Correct default? |
|-------------|---------------------|-----------------|
| shadow_390001 | Dynamically computed; directions from pad | YES |
| shadow_390003 | Dynamically computed; P2 directions from pad | YES |
| shadow_390005 | 0xFF (no coins) | YES |
| shadow_390007 | 0xFF (no coins, no start) | YES for tilt/test; NO for coin gate/start bits |

### 7.4 Implementation valid: NO

Two defects confirmed:
1. `shadow_390007` is always 0xFF — coin gate bits (5, 6) never pulse, no credits ever add
2. `shadow_390001` bit 7 = Start, but arcade expects Start at bits 4 or 5

---

## 8. Root Cause

The credit increment mechanism requires a 1→0 falling edge on bit 5 of
`genesistan_shadow_input_390007` (P1 coin gate) to trigger the credit counter at `0x3AC94`.
The current `rastan_direct_update_inputs` writes `shadow_390007 = 0xFF` every frame without
exception, so bit 5 is always 1. The required 1→0 transition never occurs. The credit counter
`a5@(0x12)` remains at zero. With zero credits, the arcade code cannot proceed to gameplay
from the attract state.

### 8.1 Exact blocking condition identified: YES

---

## 9. Single Root Cause

The `rastan_direct_update_inputs` function in `apps/rastan-direct/src/main_68k.s` writes
`genesistan_shadow_input_390007 = 0xFF` unconditionally on every frame. The arcade code
increments the credit counter when it detects a 1→0 falling edge on bit 5 of this shadow
byte (P1 coin gate, at 0x3AC94). Since the bit value never changes, no falling edge is ever
detected, the credit counter stays zero, and the game state machine never transitions from
attract mode to gameplay.

---

## 10. Single Next Correction

**File**: `apps/rastan-direct/src/main_68k.s`

**Location**: `rastan_direct_update_inputs` function, specifically the section that writes to
`genesistan_shadow_input_390007` (currently lines 303–304).

**Exact behavioral change required**:

When the Genesis A button is pressed (bit 4 of the TH=0 read, which is the same button already
used for coin input), the coin gate bits of `shadow_390007` must PULSE: bit 5 (P1 coin gate)
must be held LOW (0) for exactly 1 frame when A is first pressed, then return to HIGH (1) on
the next frame. This provides the 1→0→1 transition that the edge-detector at `0x3AC94` requires.

The specific pulse protocol:
- Frame N: A is pressed → bit 5 of shadow_390007 = 0 (active-low, coin gate active)
- Frame N+1: regardless of A state → bit 5 of shadow_390007 = 1 (inactive)
- Edge detector sees: bit was 1 (stored `a5@(0x22)=1`), now is 0 → fires credit increment

This must be implemented as a single-frame pulse: detect A pressed AND previous-frame state was
"not pulsing" → set bit 5 low for one frame → then restore to 1. Do NOT keep bit 5 low for
multiple frames (would not re-fire due to edge detection storing `a5@(0x22)=0` after first
edge). Each A press should produce exactly one 1→0→1 cycle in bit 5 of `shadow_390007`.

Additionally (secondary fix, same file, same function): the Genesis Start button (bit 5 of
TH=0 read) must also clear bit 3 of `shadow_390007` (P1 Start) while held down. Currently it
clears bit 7 of `shadow_390001`, which the arcade never checks for start. Clearing bit 3 of
`shadow_390007` will cause `0x3A490` to detect P1 start and transition to game start (given
credits > 0).

---

## 11. What Must Not Be Changed Yet

1. **All existing `opcode_replace` entries in `specs/rastan_direct_remap.json`** — All coin,
   system, joystick, and DIP patches are correctly placed. No entries must be removed or
   modified. The patch coverage is complete and correct.

2. **DIP constants (0x03AF7A = 0xFE, 0x03AF86 = 0xFF)** — Verified correct per MAME factory
   defaults. Do not change.

3. **The `not` instruction at 0x03AF80 and 0x03AF8C** — Must not be patched or removed. The
   arcade DIP init reads the active-low byte and inverts before storing to WRAM. The patch only
   replaces the `moveb 0x390009, d0` instruction; the `notb` and `movew` store instructions
   must remain intact.

4. **0x380000 write suppressions** — All NOP patches for 0x380000 writes are correct. Do not
   restore or redirect them.

5. **The `genesistan_shadow_input_390001` joystick byte mapping for directions + attack** —
   D-pad directions (bits 0-3) and the A button as attack (bit 6) are correctly mapped. Only
   the Start→bit7 assignment needs to be changed to Start→bit3-of-shadow_390007. The attack
   mapping (A→bit6-of-shadow_390001) is correct and must not be disturbed.

6. **The `genesistan_shadow_input_390005` coin byte logic** — The A button clearing bits 4 and
   6 simultaneously is the coin lockout trigger path (`0x3A0A8`). This path manages hardware
   coin lockout (suppressed anyway by NOP patches on 0x380000). Do not remove this mapping, but
   also note it is not the credit increment path. The credit increment is gated by `shadow_390007`
   bit 5, not `shadow_390005`.

7. **The whole-maincpu relocation delta (0x000200)** — Correct. Do not modify.

8. **`rastan_direct_arcade_tick_entry = 0x0003A208`** — Correct. Do not modify.

9. **`genesistan_hook_tilemap_plane_a` stub** — VDP path is working. Do not modify.

10. **The BSS section layout and symbol addresses** — All shadow byte symbols resolve to
    `0xFF0007`–`0xFF000A`. Any linker or BSS layout change would break symbol resolution.

---

## 12. Final Verdict

| Task | Answer |
|------|--------|
| Coin read sites identified | YES — 7 sites in disassembly |
| All coin sites correctly patched | YES — all redirect to genesistan_shadow_input_390005 |
| Credit storage location identified | YES — `a5@(0x12)`, BCD word in WRAM |
| Credit increment logic fully traced | YES — 3 independent edge-detected paths via 0x390007 bits 0/5/6 |
| Trigger type | EDGE — 1→0 falling edge on active-low system byte bits |
| Start condition identified | YES — 0x390007 bits 3+4 AND 0x390001 bits 4+5 |
| System input byte requirements defined | YES — bits 0/3/4/5/6 must pulse; bits 1/2 stay inactive |
| Input shadow implementation valid | NO — shadow_390007 always 0xFF; Start mapped to wrong bit |
| Exact blocking condition identified | YES — coin gate bit 5 of shadow_390007 never pulses; edge never fires; credits never increment |
| Single root cause | `rastan_direct_update_inputs` writes shadow_390007 = 0xFF every frame; bit 5 (P1 coin gate) never transitions 1→0; edge detector at 0x3AC94 never fires; credit counter never increments |
| Single next correction | In `main_68k.s` `rastan_direct_update_inputs`: when A is pressed, pulse bit 5 of shadow_390007 LOW for exactly 1 frame; also clear bit 3 of shadow_390007 while Start is held |
| What-must-not-be-changed-yet defined | YES |
