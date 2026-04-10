# Andy — Rastan DIP Defaults and Flip Behavior

## 1. Executive Summary

This document is the authoritative analysis of Rastan DIP switch definitions, factory defaults,
and flip-screen behavior, using MAME's `src/mame/taito/rastan.cpp` and `taitoipt.h` as the sole
authoritative source. It resolves three open questions from the current TC0040IOC patch plan:

1. **DIP1 = 0xFE is correct** as the active-low hardware byte for DIP Bank 1 factory defaults.
   After NOT → 0x01. Per MAME, bit 0 active-high = Cabinet=Upright (not Test mode). The
   TC0040IOC_specifications.md bit 0 label "Test mode" is wrong. MAME says bit 0 = Cabinet.

2. **DIP2 = 0xFF is correct** as the active-low hardware byte for DIP Bank 2 factory defaults.
   After NOT → 0x00. Per MAME, this decodes as: Difficulty=Medium (raw bits 0-1 = 0x03, not
   0x00), Bonus Life = 100k/200k/400k/600k/800k, Lives = 3, Continue = On.
   The TC0040IOC_specifications.md claim that 0x00 active-high = "Easy" is wrong; MAME says
   Medium. The TC0040IOC spec also incorrectly states Continue=OFF; MAME default is Continue=ON.

3. **NOPing 0x380000 writes is safe** when DIP1 bit 1 = 0 (active-low: bit 1 = 1 in raw byte)
   indicates flip-screen OFF. The arcade code reads the DIP at boot, stores the flip flag in WRAM
   at A5+0x1F bit 0, then uses that WRAM flag exclusively for coordinate math. The 0x380000 write
   path sets hardware flip registers and coin lockout solenoids. On Genesis hardware both are
   irrelevant: no hardware flip register exists, and coin lockout solenoids do not exist.

Current patch plan values (DIP1=0xFE, DIP2=0xFF) produce correct results despite the
TC0040IOC_specifications.md bit-label errors, because those errors are in the documentation only
and the actual byte values were derived correctly from MAME hardware behavior.

---

## 2. Inputs Audited

1. `/home/tighe/projects/rastan-genesis/docs/design/TC0040IOC_specifications.md` — READ COMPLETE.
   Full register map, DIP bit table, active-low convention, 0x380000 write description, factory
   default bytes stated as DIP1=0xFE/DIP2=0xFF, patch table at Section 5.

2. `/home/tighe/projects/rastan-genesis/docs/design/Andy_tc0040ioc_and_arcade_execution_plan.md`
   — READ (lines 0–199). Section 3.5 confirms DIP1=0xFE/DIP2=0xFF. Section 3.7 complete patch
   table. Section 3.2 confirms active-low convention and NOT inversion. Section 5.6 confirms
   0x380000 suppression policy.

3. MAME source: `https://raw.githubusercontent.com/mamedev/mame/master/src/mame/taito/rastan.cpp`
   — FETCHED. Complete DSWA and DSWB PORT_DIPNAME/PORT_DIPSETTING blocks extracted verbatim.

4. MAME source: `https://raw.githubusercontent.com/mamedev/mame/master/src/mame/taito/taitoipt.h`
   — FETCHED. TAITO_COINAGE_WORLD_LOC and TAITO_DIFFICULTY_LOC macro expansions extracted with
   all bit values and defaults.

---

## 3. MAME DIP Definitions

The following is extracted verbatim from MAME `rastan.cpp` and `taitoipt.h`.

### DSWA (DIP Bank 1, physical SW1, arcade address 0x390008/0x390009)

All values are active-low PORT values (the physical state the hardware presents to the 68000).
In MAME, `PORT_DIPNAME(mask, default, name)` — the `default` is the PORT value when the switch
is at factory setting.

```
PORT_DIPNAME( 0x01, 0x00, DEF_STR( Cabinet ) )       PORT_DIPLOCATION("SW1:1")
PORT_DIPSETTING(    0x00, DEF_STR( Upright ) )
PORT_DIPSETTING(    0x01, DEF_STR( Cocktail ) )

PORT_DIPNAME( 0x02, 0x02, DEF_STR( Flip_Screen ) )   PORT_DIPLOCATION("SW1:2")
PORT_DIPSETTING(    0x02, DEF_STR( Off ) )
PORT_DIPSETTING(    0x00, DEF_STR( On ) )

PORT_SERVICE_DIPLOC( 0x04, IP_ACTIVE_LOW, "SW1:3" )
  (implicit: 0x04 = normal/off, 0x00 = service mode active)

PORT_DIPUNUSED_DIPLOC( 0x08, 0x08, "SW1:4" )
  (implicit: 0x08 = unused, default open)

TAITO_COINAGE_WORLD_LOC(SW1) expands to:
  PORT_DIPNAME( 0x30, 0x30, Coin_A )                 PORT_DIPLOCATION("SW1:5,6")
  PORT_DIPSETTING(    0x00, "4C_1C" )
  PORT_DIPSETTING(    0x10, "3C_1C" )
  PORT_DIPSETTING(    0x20, "2C_1C" )
  PORT_DIPSETTING(    0x30, "1C_1C" )    <- default

  PORT_DIPNAME( 0xc0, 0xc0, Coin_B )                 PORT_DIPLOCATION("SW1:7,8")
  PORT_DIPSETTING(    0x00, "1C_6C" )
  PORT_DIPSETTING(    0x40, "1C_4C" )
  PORT_DIPSETTING(    0x80, "1C_3C" )
  PORT_DIPSETTING(    0xc0, "1C_2C" )    <- default
```

**DSWA bit summary (active-low hardware values):**

| Bits (mask) | SW1 pos | Function         | Default PORT value | Meaning at default |
|-------------|---------|------------------|--------------------|--------------------|
| 0x01        | SW1:1   | Cabinet          | 0x00               | Upright (closed)   |
| 0x02        | SW1:2   | Flip Screen      | 0x02               | Off (open)         |
| 0x04        | SW1:3   | Service mode     | 0x04               | Normal (open)      |
| 0x08        | SW1:4   | Unused           | 0x08               | Open               |
| 0x30        | SW1:5,6 | Coin A           | 0x30               | 1C/1C (both open)  |
| 0xC0        | SW1:7,8 | Coin B           | 0xC0               | 1C/2C (both open)  |

**DSWA factory default PORT byte = 0x00 | 0x02 | 0x04 | 0x08 | 0x30 | 0xC0 = 0xFE**

### DSWB (DIP Bank 2, physical SW2, arcade address 0x39000A/0x39000B)

```
TAITO_DIFFICULTY_LOC(SW2) expands to:
  PORT_DIPNAME( 0x03, 0x03, Difficulty )              PORT_DIPLOCATION("SW2:1,2")
  PORT_DIPSETTING(    0x00, DEF_STR( Hardest ) )
  PORT_DIPSETTING(    0x01, DEF_STR( Hard ) )
  PORT_DIPSETTING(    0x02, DEF_STR( Easy ) )
  PORT_DIPSETTING(    0x03, DEF_STR( Medium ) )   <- default

PORT_DIPNAME( 0x0c, 0x0c, DEF_STR( Bonus_Life ) )    PORT_DIPLOCATION("SW2:3,4")
PORT_DIPSETTING(    0x0c, "100k 200k 400k 600k 800k" )   <- default
PORT_DIPSETTING(    0x08, "150k 300k 600k 900k 1200k" )
PORT_DIPSETTING(    0x04, "200k 400k 800k 1200k 1600k" )
PORT_DIPSETTING(    0x00, "250k 500k 1000k 1500k 2000k" )

PORT_DIPNAME( 0x30, 0x30, DEF_STR( Lives ) )          PORT_DIPLOCATION("SW2:5,6")
PORT_DIPSETTING(    0x30, "3" )                            <- default
PORT_DIPSETTING(    0x20, "4" )
PORT_DIPSETTING(    0x10, "5" )
PORT_DIPSETTING(    0x00, "6" )

PORT_DIPNAME( 0x40, 0x40, DEF_STR( Allow_Continue ) ) PORT_DIPLOCATION("SW2:7")
PORT_DIPSETTING(    0x00, DEF_STR( Off ) )
PORT_DIPSETTING(    0x40, DEF_STR( On ) )               <- default

PORT_DIPUNUSED_DIPLOC( 0x80, 0x80, "SW2:8" )
  (implicit: 0x80 = unused, default open)
```

**DSWB bit summary (active-low hardware values):**

| Bits (mask) | SW2 pos | Function         | Default PORT value | Meaning at default        |
|-------------|---------|------------------|--------------------|---------------------------|
| 0x03        | SW2:1,2 | Difficulty       | 0x03               | Medium (both open)        |
| 0x0C        | SW2:3,4 | Bonus Life       | 0x0C               | 100k/200k/400k/600k/800k  |
| 0x30        | SW2:5,6 | Lives            | 0x30               | 3 lives                   |
| 0x40        | SW2:7   | Allow Continue   | 0x40               | On                        |
| 0x80        | SW2:8   | Unused           | 0x80               | Open                      |

**DSWB factory default PORT byte = 0x03 | 0x0C | 0x30 | 0x40 | 0x80 = 0xFF**

**DIP definitions extracted: YES**

---

## 4. Factory Default DIP Values

Factory defaults from MAME (authoritative):

| Register            | Active-low raw hardware byte | After NOT (active-high WRAM) |
|---------------------|------------------------------|------------------------------|
| DIP Bank 1 (DSWA)   | **0xFE**                     | **0x01**                     |
| DIP Bank 2 (DSWB)   | **0xFF**                     | **0x00**                     |

Decoded settings at these defaults:

| Setting          | Value per MAME                          |
|------------------|-----------------------------------------|
| Cabinet          | Upright                                 |
| Flip Screen      | Off (normal orientation)                |
| Service mode     | Off (normal play)                       |
| Coin A           | 1 Coin / 1 Credit                       |
| Coin B           | 1 Coin / 2 Credits                      |
| Difficulty       | Medium                                  |
| Bonus Life       | 100k / 200k / 400k / 600k / 800k        |
| Lives            | 3                                       |
| Allow Continue   | On                                      |

**Factory default DIP values identified: YES**

---

## 5. Flip / Cabinet Behavior Analysis

### 5.1 Which Bits Control Flip and Cabinet

Per MAME `rastan.cpp`:

- **SW1:1 (mask 0x01)** = Cabinet type: 0x00 active-low = Upright; 0x01 = Cocktail
- **SW1:2 (mask 0x02)** = Flip Screen: 0x02 active-low = Off; 0x00 active-low = On

These are **separate bits** for separate functions. Cabinet type and flip screen are independent.

### 5.2 Active-Low to Active-High Mapping

The arcade code reads DIP Bank 1 at 0x03AF7A, then executes `notb %d0` to invert to an
active-high working value stored in WRAM at A5+0x18. The game then reads that WRAM location for
all DIP-dependent logic.

For flip screen:
- Raw byte bit 1 = 1 (switch open, Flip OFF) → after NOT → active-high bit 1 = 0 → Flip OFF
- Raw byte bit 1 = 0 (switch closed, Flip ON) → after NOT → active-high bit 1 = 1 → Flip ON

The arcade code also stores a separate flip flag at A5+0x1F bit 0, derived from the DIP WRAM
mirror at A5+0x18. When A5+0x1F bit 0 = 1, the input handler at 0x03A4A2 swaps P1 and P2
inputs via `exg %d0, %d1`. This is the only runtime flip-screen behavior relevant to Genesis.

### 5.3 For Normal (Non-Flipped) Upright Display

Required bit states:
- SW1:1 (Cabinet): active-low 0x00 = Upright; after NOT → bit 0 = 1 in WRAM
- SW1:2 (Flip Screen): active-low 0x02 = Off; after NOT → bit 1 = 0 in WRAM

Combined in the active-low raw byte: bits 0-1 of 0xFE = 1110 = bit 0 clear, bit 1 set.
Specifically: bit 0 = 0 (Upright, switch closed), bit 1 = 1 (Flip OFF, switch open).

DIP1 = 0xFE produces exactly these values. After NOT → 0x01:
- Active-high bit 0 = 1 → Upright (MAME: 0x00 active-low = Upright → after NOT → bit 0 = 1)
- Active-high bit 1 = 0 → Flip Screen OFF
- Active-high bit 2 = 0 → Service mode OFF
- Active-high bits 3-7 = 0

**Flip/cabinet derivation fully understood: YES**

---

## 6. TC0040IOC Byte Mapping

### DIP Bank 1 — 0x390009

Bit-level breakdown of DIP1 = **0xFE** (active-low raw hardware byte):

```
Bit 7: 1  (Coin B bit 1, SW1:8, open = 1C/2C)
Bit 6: 1  (Coin B bit 0, SW1:7, open = 1C/2C)
Bit 5: 1  (Coin A bit 1, SW1:6, open = 1C/1C)
Bit 4: 1  (Coin A bit 0, SW1:5, open = 1C/1C)
Bit 3: 1  (Unused, SW1:4, open)
Bit 2: 1  (Service mode, SW1:3, open = normal play)
Bit 1: 1  (Flip Screen, SW1:2, open = Flip OFF)
Bit 0: 0  (Cabinet, SW1:1, closed = Upright)
```

Binary: 1111 1110 = 0xFE. After NOT → 0x01 = 0000 0001.

### DIP Bank 2 — 0x39000B

Bit-level breakdown of DIP2 = **0xFF** (active-low raw hardware byte):

```
Bit 7: 1  (Unused, SW2:8, open)
Bit 6: 1  (Allow Continue, SW2:7, open = Continue ON)
Bit 5: 1  (Lives bit 1, SW2:6, open = 3 lives)
Bit 4: 1  (Lives bit 0, SW2:5, open = 3 lives)
Bit 3: 1  (Bonus Life bit 1, SW2:4, open = 100k/200k...)
Bit 2: 1  (Bonus Life bit 0, SW2:3, open = 100k/200k...)
Bit 1: 1  (Difficulty bit 1, SW2:2, open = Medium)
Bit 0: 1  (Difficulty bit 0, SW2:1, open = Medium)
```

Binary: 1111 1111 = 0xFF. After NOT → 0x00 = 0000 0000.

**DIP return values for TC0040IOC defined: YES**

---

## 7. Comparison Against Current Assumption

### Current plan:
- DIP1 (0x390009) = 0xFE → after NOT → 0x01
- DIP2 (0x39000B) = 0xFF → after NOT → 0x00

### TC0040IOC_specifications.md discrepancies vs MAME:

**Discrepancy 1 — DIP Bank 1 bit 0 label:**
The TC0040IOC spec states: "Bit 0 | Test mode | Normal play | Service/test mode"
MAME states: Bit 0 (mask 0x01) = Cabinet: 0x00=Upright, 0x01=Cocktail

The spec's "test mode" label for bit 0 is wrong. MAME is authoritative. Bit 0 = Cabinet.
Service/test mode is at bit 2 (mask 0x04) via `PORT_SERVICE_DIPLOC`.

**Impact on byte values**: NONE. DIP1=0xFE is still correct. After NOT → 0x01 → bit 0 = 1.
Per MAME: bit 0 active-high = 1 = Upright. The game starts in upright mode. Correct.

**Discrepancy 2 — DIP Bank 1 bit layout shifts:**
The TC0040IOC spec lists: bit 0=test, bit 1=flip, bit 2=demo sound, bit 3=cabinet, bits 4-7=coin.
MAME lists:              bit 0=cabinet, bit 1=flip, bit 2=service, bit 3=unused, bits 4-7=coin.

Bit 1 (Flip Screen) is consistent between spec and MAME. Bits 4-7 (coinage) are consistent.
Bit 0 (cabinet vs test) and bit 2 (demo-sound vs service) differ. Bit 3 differs.

**Impact on byte values**: NONE. 0xFE has bit 0=0 (cabinet/upright closed) and all other
bits=1 (open/default). The byte value is correct regardless of which function is on bit 0.

**Discrepancy 3 — DIP Bank 2 difficulty labeling:**
The TC0040IOC spec says: "Bits 0-1 active-high 0x02=Easy, 0x03=Medium". After NOT of 0xFF
→ 0x00 at bits 0-1. The spec incorrectly labels 0x00 as "Easy".
MAME says: difficulty PORT value 0x03 (active-low both-open) = Medium. After NOT → 0x00.
So 0x00 active-high = Medium, not Easy. The spec label "Easy" is wrong.

**Impact on byte values**: NONE. DIP2=0xFF is still the correct factory default byte. The
game will run at Medium difficulty, which is the true MAME default. The spec's label was wrong
but the byte was right.

**Discrepancy 4 — Allow Continue:**
The TC0040IOC spec says "continue=OFF" for DIP2=0xFF default.
MAME says: Allow Continue bit 6 (mask 0x40), default 0x40 = Continue ON (switch open).
DIP2=0xFF has bit 6=1 (open) = Continue ON per MAME. Spec label is wrong.

**Impact on byte values**: NONE. 0xFF is still correct. Continue will be ON, which is the
correct MAME default.

### Verdict on current assumption:

The byte values **DIP1=0xFE and DIP2=0xFF are correct and match MAME factory defaults exactly.**
The TC0040IOC_specifications.md contains several wrong bit-label annotations in its DIP table,
but the actual byte values were derived correctly from hardware behavior and produce the correct
game state. The concern raised in the task prompt about "bit 0 = test mode ON" is based on the
incorrect bit labeling in that spec document; bit 0 per MAME is Cabinet (not test mode), and
DIP1=0xFE → 0x01 active-high means Upright cabinet, not test mode.

**Current DIP assumption validated: YES**

---

## 8. Dependency on 0x380000 Writes

### What 0x380000 controls

Per TC0040IOC_specifications.md Section 3.5 and Section 5.6:
- Word writes to 0x380000 control coin lockout solenoids and flip-screen hardware register.
- The arcade code writes to this register at: 0x03A1D8, 0x03AE9C, 0x03AF1E.
- `clrw 0x380000` (0x03AE9C) releases all coin lockouts.
- Non-zero writes engage coin lockouts and/or set the hardware flip-screen register.

### How flip-screen actually works in the arcade code

The flip-screen path in Rastan works as follows:
1. At boot (0x03AF7A): DIP Bank 1 is read, inverted, stored in WRAM at A5+0x18.
2. During init: The code extracts bit 1 of A5+0x18 (active-high Flip value) and stores it as
   a flip flag in WRAM at A5+0x1F bit 0.
3. During gameplay input polling (0x03A4A2): If flip flag (A5+0x1F bit 0) = 1, P1 and P2
   inputs are swapped via `exg %d0, %d1`.
4. The 0x380000 write path sets a **hardware flip register** on the arcade board (TC0040IOC
   or a separate video chip register) that physically inverts the display scan direction.

On Genesis hardware:
- Address 0x380000 is unmapped. Writes to this address cause a bus error or are silently ignored
  depending on the Genesis address decoder behavior.
- There is no hardware flip register on Genesis. The VDP does not respond to 0x380000.
- The Genesis VDP flip-screen (if needed) requires a separate VDP register write to Mode Register 2.

### Is NOPing 0x380000 writes safe when DIP indicates non-flipped?

With DIP1=0xFE → after NOT → flip bit = 0 (Flip OFF):
- The arcade code stores flip flag = 0 at A5+0x1F.
- The input swap code (`exg %d0, %d1`) is never executed.
- No coordinate inversion logic is triggered.
- The only function that 0x380000 writes would serve is: (a) setting the physical arcade hardware
  flip register (irrelevant on Genesis), and (b) controlling coin lockout solenoids (irrelevant
  on Genesis).

Since the DIP constant ensures the flip flag stored in WRAM is 0 (flip OFF), all game-logic
consequences of flip-screen are suppressed at the WRAM flag level. The 0x380000 writes are
the hardware manifestation of that same setting — writing to them would only affect physical
arcade hardware that does not exist on Genesis.

**NOPing 0x380000 writes is safe.** Coin lockout is irrelevant on Genesis. The hardware flip
register at 0x380000 is irrelevant on Genesis when the DIP-derived WRAM flip flag is 0.

**Dependency on 0x380000 writes determined: YES**

---

## 9. Final DIP Values for Implementation

```
DIP1 (return at 0x390009) = 0xFE  (active-low hardware value)
DIP2 (return at 0x39000B) = 0xFF  (active-low hardware value)

After NOT:
  DIP1 → 0x01
    Bit 0 = 1  → Cabinet = Upright
    Bit 1 = 0  → Flip Screen = OFF (normal orientation)
    Bit 2 = 0  → Service mode = OFF
    Bit 3 = 0  → (Unused)
    Bits 4-5 = 0  → Coin A = 1C/1C (working copy; coinage irrelevant on Genesis)
    Bits 6-7 = 0  → Coin B = 1C/2C (working copy; coinage irrelevant on Genesis)

  DIP2 → 0x00
    Bits 0-1 = 0  → Difficulty = Medium  (raw MAME PORT 0x03 = Medium; after NOT = 0x00)
    Bits 2-3 = 0  → Bonus Life = 100k/200k/400k/600k/800k
    Bits 4-5 = 0  → Lives = 3
    Bit 6 = 0     → Allow Continue = ON  (raw MAME PORT 0x40 = On; after NOT = bit 6 clear)
    Bit 7 = 0     → (Unused)

Result: cabinet=Upright, flip=OFF, service=OFF, difficulty=Medium, bonus=100k series,
        lives=3, continue=ON.
```

**DIP return values defined: YES**

---

## 10. What Must Not Be Changed Yet

The following aspects of TC0040IOC handling must remain fixed and must not be altered during
any implementation work that follows this analysis:

1. **DIP1 patch constant = 0xFE** at ROM address 0x03AF7A. Do not change to 0xFF or any other
   value. 0xFE is the MAME-verified factory default for DIP Bank 1.

2. **DIP2 patch constant = 0xFF** at ROM address 0x03AF86. Do not change. 0xFF is the
   MAME-verified factory default for DIP Bank 2.

3. **The `notb %d0` at 0x03AF80 and 0x03AF8C must not be patched or removed.** The DIP init
   code reads the active-low byte and inverts it before storing to WRAM. The patch replaces only
   the `moveb 0x390009, %d0` instruction; the `notb` and `movew` store instructions remain
   intact. If the `notb` is accidentally NOPed, the WRAM mirror will contain 0xFE/0xFF
   (active-low) instead of 0x01/0x00 (active-high), corrupting all DIP-dependent logic.

4. **0x380000 writes must remain NOPed** (suppressed). Do not redirect them to WRAM mirrors or
   attempt to interpret them as Genesis VDP commands. They have no useful function on Genesis
   when DIP flip=OFF.

5. **WRAM flip flag at A5+0x1F bit 0 is set by the arcade code itself** from the DIP WRAM
   mirror. Do not pre-set or post-set this flag from Genesis code. The arcade init sequence
   between 0x03AF7A and the flag derivation must run unmodified.

6. **All 19–22 TC0040IOC patch sites** defined in Andy_tc0040ioc_and_arcade_execution_plan.md
   Section 3.7 must be patched. Adding the DIP patches without patching joystick, coin, and
   service reads will cause bus errors during gameplay on Genesis hardware.

7. **The active-low convention on all input reads (0x390001, 0x390003, 0x390005, 0x390007)**
   must be preserved. Genesis pad stubs must return active-low bytes. Any stub that returns
   active-high values will invert all input logic (pressed = released).

8. **The TC0040IOC_specifications.md bit table for DIP Bank 1** contains incorrect bit-label
   annotations at bits 0, 2, and 3. Do not use that table to derive new DIP byte values. Use
   MAME `rastan.cpp` PORT_DIPNAME blocks as the authoritative source for bit assignments.
   The byte values 0xFE / 0xFF in the spec are correct; only the per-bit label column is wrong.

**What-must-not-be-changed-yet defined: YES**

---

## 11. Final Verdict

| Question                                             | Answer                                                 |
|------------------------------------------------------|--------------------------------------------------------|
| DIP definitions extracted from MAME?                 | YES — full DSWA and DSWB PORT_DIPNAME blocks           |
| Factory default bytes identified?                    | YES — DIP1=0xFE, DIP2=0xFF (both MAME-confirmed)      |
| Flip-screen bit identified?                          | YES — DSWA bit 1 (mask 0x02), Off=0x02, On=0x00       |
| Cabinet bit identified?                              | YES — DSWA bit 0 (mask 0x01), Upright=0x00            |
| Flip separate from cabinet?                          | YES — separate independent bits                        |
| TC0040IOC spec bit table accurate?                   | NO — bit 0 and bit 2 labels are wrong per MAME        |
| Current patch DIP1=0xFE, DIP2=0xFF valid?            | YES — byte values are correct despite label errors     |
| Test mode risk from DIP1=0xFE → 0x01?                | NO — bit 0 active-high = Upright (not test mode)       |
| NOPing 0x380000 writes safe with flip=OFF DIP?       | YES — hardware flip register irrelevant on Genesis     |
| Single authoritative final value set?                | DIP1=0xFE, DIP2=0xFF                                   |
