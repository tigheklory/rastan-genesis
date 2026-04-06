# TC0040IOC I/O Controller — Specification and No-SGDK Handling

## 1. Overview

The TC0040IOC is Taito's custom I/O controller chip used in Rastan (1987) and many other Taito arcade boards of the same era, including Rainbow Islands, Cadash, and Ninja Warriors. It sits on the 68000 address bus and handles all external I/O: joystick inputs, coin inputs, service/tilt switches, and DIP switch banks.

The chip is **purely memory-mapped**. There is no port instruction, no select/latch sequence, and no handshaking protocol. The 68000 reads or writes the chip's registers with ordinary `moveb` (byte) or `movew` (word) instructions to absolute addresses. From the CPU's perspective the TC0040IOC is indistinguishable from a byte-wide SRAM.

---

## 2. Register Map (Rastan arcade, confirmed from `build/maincpu.disasm.txt`)

All registers are 8-bit (byte reads/writes on odd addresses of the 16-bit bus).

| Address | Direction | Name | Contents |
|---------|-----------|------|----------|
| `0x380000` | Write | **Control / Coin lockout** | Word write. Controls coin lockout solenoids and flip-screen orientation. Bit patterns vary; `0x0000` = release lockout, specific bits = lock individual coin slots. |
| `0x390001` | Read | **Player 1 joystick + buttons** | Active-low byte. Bits: UP, DOWN, LEFT, RIGHT, BTN1 (attack), BTN2 (jump), BTN3, BTN4. |
| `0x390003` | Read | **Player 2 joystick + buttons** | Active-low byte. Same layout as Player 1. |
| `0x390005` | Read | **Coin inputs** | Active-low byte. Bit 4 = coin 1, bit 5 = coin 2, bit 6 = coin 3 / service coin. |
| `0x390007` | Read | **System switches** | Active-low byte. Bit 0 = service mode (soft), bit 1 = tilt, bit 2 = test button, bit 3 = service coin alt, bit 6 = flip screen state. |
| `0x390009` | Read | **DIP switch bank 1 (SW1 / DSWA)** | Active-low byte. All 8 physical switches. Open switch = bit 1, closed = bit 0. |
| `0x39000B` | Read | **DIP switch bank 2 (SW2 / DSWB)** | Active-low byte. All 8 physical switches. Same polarity as bank 1. |

**Active-low convention**: All input registers read `1` for an open (unpressed/off) switch and `0` for a closed (pressed/on) switch. The arcade code consistently follows each read with `notb %d0` to invert to active-high working values before storing into workram.

---

## 3. Observed Access Patterns in Rastan ROM

### 3.1 Startup / DIP Init (`0x03AF7A`)

Called once during `startup_common` to read DIP switches into workram. This is the only time DIP registers are read during normal operation:

```asm
3af7a:  1039 0039 0009   moveb 0x390009, %d0     ; read SW1 (active-low)
3af80:  4600             notb  %d0               ; invert to active-high
3af82:  3b40 0018        movew %d0, %a5@(24)     ; store DIP1 mirror at A5+0x18

3af86:  1039 0039 000b   moveb 0x39000b, %d0     ; read SW2 (active-low)
3af8c:  4600             notb  %d0               ; invert to active-high
3af8e:  3b40 001c        movew %d0, %a5@(28)     ; store DIP2 mirror at A5+0x1C
```

After this, all DIP-dependent logic reads from the workram mirrors (`%a5@(24)`, `%a5@(28)`) — never from the hardware again. DIP settings are effectively latched at boot.

### 3.2 Joystick + Button Reads (gameplay input polling, `0x03A4A2`, `0x03A778`)

Called every game tick from the main input handler:

```asm
3a4a2:  1039 0039 0001   moveb 0x390001, %d0     ; player 1 raw input
3a4a8:  1239 0039 0003   moveb 0x390003, %d1     ; player 2 raw input
```

Immediately followed by flip-screen swap logic: if flip-screen is active (workram flag at A5+0x1F bit 0), players 1 and 2 are swapped (`exg %d0, %d1`). The raw active-low bytes are used directly without `notb` in this path — the input processing logic checks for zero bits (pressed) rather than set bits.

### 3.3 Coin Input Polling (`0x03A0A8`)

Called from the credit management routine:

```asm
3a0a8:  0839 0006 0039   btst #6, 0x390005       ; coin 3 / service coin
3a0b2:  0839 0004 0039   btst #4, 0x390005       ; coin 1
3a0c0:  0839 0005 0039   btst #5, 0x390005       ; coin 2
```

Uses `btst` (bit test) against the memory address directly — no full byte read required. A result of zero (bit clear) means the coin switch is closed (coin inserted).

### 3.4 Service / Tilt / Test Reads (`0x03A490`, `0x03A7B8`, `0x03AB96`, `0x03AC04`)

Several distinct call sites read `0x390007` for different purposes:

```asm
; Service mode check (andib #0x18 = bits 3+4 = service + test)
3a490:  1039 0039 0007   moveb 0x390007, %d0
3a496:  0200 0018        andib #24, %d0

; Tilt detection
3a7b8:  0839 0001 0039   btst #1, 0x390007       ; tilt switch (bit 1)

; Test mode entry
3ab96:  0839 0002 0039   btst #2, 0x390007       ; test button (bit 2)

; Soft service trigger
3ac04:  0839 0000 0039   btst #0, 0x390007       ; service switch (bit 0)
```

### 3.5 Control / Coin Lockout Writes (`0x380000`)

Word writes to the control register appear throughout the code:

```asm
3a1d8:  33c0 0038 0000   movew %d0, 0x380000     ; update coin lockout / flip state
3ae9c:  4279 0038 0000   clrw 0x380000           ; release all lockouts
3af1e:  33c0 0038 0000   movew %d0, 0x380000     ; set during startup sequence
```

Writing `0x0000` releases all coin lockouts (coins accepted). Non-zero values engage specific lockouts and/or set flip-screen hardware.

---

## 4. DIP Switch Bit Definitions

### DIP Bank 1 (`0x390009`, stored at A5+0x18 after inversion)

| Bit (active-high after NOT) | Function | 0 = | 1 = |
|-----------------------------|----------|-----|-----|
| 0 | Test mode | Normal play | **Service / test mode** |
| 1 | Flip screen | Normal | Flipped |
| 2 | Demo sound | Silent attract | Sound in attract |
| 3 | Cabinet type | Upright | Cocktail |
| 4–7 | Coin mode | Various ratios | (see table below) |

**Coin mode (bits 4–7, active-high):**

| Bits 4–7 | Coins / Credits |
|----------|----------------|
| `0x0F` (all set) | 1 coin / 1 credit (factory default) |
| `0x0A` | 2 coins / 1 credit |
| `0x05` | 1 coin / 2 credits |
| `0x00` | Free play |

### DIP Bank 2 (`0x39000B`, stored at A5+0x1C after inversion)

| Bits (active-high after NOT) | Function | Values |
|------------------------------|----------|--------|
| 0–1 | Difficulty | `0x02`=Easy, `0x03`=Medium, `0x01`=Hard, `0x00`=Hardest |
| 2–3 | Bonus HP threshold | `0x03`=30k, `0x02`=50k, `0x01`=70k, `0x00`=None |
| 4–5 | Starting lives | `0x03`=3, `0x02`=4, `0x01`=5, `0x00`=2 |
| 6 | Continue | `0x01`=OFF, `0x00`=ON |
| 7 | Unused | — |

**Factory defaults (from Rastan operator manual):**

| Register | Raw hardware value (active-low) | After NOT (active-high workram value) |
|----------|---------------------------------|--------------------------------------|
| DIP Bank 1 | `0xFE` | `0x01` |
| DIP Bank 2 | `0xFF` | `0x00` |

Decoded: test=OFF, flip=OFF, demo sound=OFF, upright, 1C/1C, Easy, 30k bonus, 3 lives, continue=OFF.

**All-open / missing switches (hardware floats to `0xFF` both banks):**

| Register | Raw hardware value | After NOT | Difference from factory |
|----------|--------------------|-----------|------------------------|
| DIP Bank 1 | `0xFF` | `0x00` | Test mode bit cleared (test=OFF, same result) |
| DIP Bank 2 | `0xFF` | `0x00` | Identical to factory default |

All-open is safe — the game boots to normal attract mode, not test mode.

---

## 5. Handling in the No-SGDK Direct Execution Branch

### 5.1 Design Principle

On Genesis hardware there is no TC0040IOC. The Genesis has its own I/O chip at `0xA10000` for joypads, and no physical DIP switch banks. Reads to `0x380000`–`0x39000F` will hit unmapped address space and the 68000 will return bus error or undefined data.

The no-SGDK branch must **intercept every TC0040IOC read and write at the opcode level** before the arcade code executes them. The mechanism is the same opcode patch system already used in the current SGDK branch, applied at the same ROM addresses.

There are two categories:

1. **DIP reads** — replace with ROM constants (values never change at runtime)
2. **Live input reads** — replace with stubs that read Genesis pad shadow and return the correct active-low byte

### 5.2 DIP Switch Patches (ROM Constants)

The two DIP reads at `0x03AF7A` and `0x03AF86` are replaced with immediate loads. These are one-time reads at startup that are never called again; patching them to constants is complete and correct.

**Patch at `0x03AF7A` (DIP Bank 1 read):**

```
Original (6 bytes):  1039 0039 0009   moveb 0x390009, %d0
Replacement:         103C 00FE        moveb #0xFE, %d0     ; factory default active-low
                     4E71             nop                  ; pad to 6 bytes
```

`0xFE` is the active-low raw value; the existing `notb %d0` at `0x03AF80` will invert it to `0x01` as expected.

**Patch at `0x03AF86` (DIP Bank 2 read):**

```
Original (6 bytes):  1039 0039 000b   moveb 0x39000b, %d0
Replacement:         103C 00FF        moveb #0xFF, %d0     ; factory default active-low
                     4E71             nop                  ; pad to 6 bytes
```

`0xFF` inverts to `0x00`, giving Easy difficulty / 3 lives / no continue.

These two patches eliminate all TC0040IOC DIP reads. No runtime variable. No workram flag. The constants are in the ROM binary and cannot change.

### 5.3 Joystick / Button Input Patches

The joystick reads appear at multiple call sites:

| ROM address | Register | Replacement target |
|-------------|----------|-------------------|
| `0x03A4A2` | `0x390001` (P1) | Genesis pad 1 stub |
| `0x03A4A8` | `0x390003` (P2) | Genesis pad 2 stub (or mirror of P1) |
| `0x03A778` | `0x390001` (P1) | Genesis pad 1 stub |
| `0x03A77E` | `0x390003` (P2) | Genesis pad 2 stub |

Each `moveb 0x390001, %d0` (6 bytes) is replaced with `jsr genesistan_read_p1_input` (6 bytes, `4EB9 xxxx xxxx`) which returns the active-low byte in `%d0`. The stub reads the Genesis pad at `0xA10003`, translates button mapping (B=attack, C=jump, A=coin, Start=start, D-pad=D-pad), and returns the result in active-low format to match the TC0040IOC convention.

The existing `genesistan_refresh_arcade_inputs` mechanism from the current branch is reused here in assembly form, without the SGDK `JOY_update` dependency.

### 5.4 Coin Input Patches

Coin reads at `0x03A0A8` / `0x03A0B2` / `0x03A0C0` use `btst` directly against `0x390005`. These are replaced with:

```
Option A (simplest): Patch to btst against a Genesis-side shadow byte
    btst #6, coin_shadow       ; shadow byte updated by main loop when Genesis Start pressed
    
Option B (for single-player home release): Patch to always return "no coin"
    btst #6, %d7              ; d7 = 0 at this call site, always "no coin inserted"
    nop nop nop nop           ; pad
```

For the no-SGDK home release, Option B is acceptable for the initial bring-up phase. A Genesis button can be mapped to the coin shadow for a fully functional implementation.

### 5.5 Service / Tilt / Test Patches

These reads protect against accidental service mode entry and tilt resets:

| ROM address | Function | Replacement |
|-------------|----------|-------------|
| `0x03A490` | Service mode check (bits 3+4) | Replace with `moveq #0xFF, %d0` (no service, no test) |
| `0x03A7B8` | Tilt detection (bit 1) | Replace with `moveq #0xFF, %d0` (tilt not active) |
| `0x03AB96` | Test button (bit 2) | Replace with `moveq #0xFF, %d0` (test not pressed) |
| `0x03AC04` | Soft service (bit 0) | Replace with `moveq #0xFF, %d0` (service not active) |
| `0x03A91A` | System switches read | Replace with `moveq #0xFF, %d0` |

`0xFF` active-low means all switches open (unpressed). This permanently prevents test mode, tilt, and service mode from triggering on Genesis hardware. These are 6-byte `moveb abs, %d0` instructions replaced with 2-byte `moveq` + 4 bytes of `nop`.

### 5.6 Control Register Write Patches (`0x380000`)

Word writes to `0x380000` are coin lockout / flip-screen control writes. On Genesis hardware this address is unmapped. Options:

- **Suppress**: Patch `movew %d0, 0x380000` to `nop nop nop` (6 bytes each). Safe — coin lockout is irrelevant on Genesis, flip-screen is handled by the DIP bit already loaded as a constant.
- **Mirror to shadow**: Redirect to a WRAM shadow word for diagnostic purposes.

Suppression is the correct choice for the no-SGDK branch. No Genesis hardware behavior depends on these writes.

### 5.7 Summary of All TC0040IOC Patches Required

| Count | Category | Patch type | Effect |
|-------|----------|------------|--------|
| 2 | DIP reads (`0x390009`, `0x39000B`) | ROM constant immediate load | Factory defaults hardcoded, never read from hardware |
| 4 | Joystick reads (`0x390001`, `0x390003`) | `jsr` to Genesis pad stub | Genesis D-pad + buttons translated to active-low byte |
| 3 | Coin reads (`0x390005`) | Shadow byte `btst` or suppress | Coin input via Genesis button or disabled |
| 5+ | Service/tilt/test reads (`0x390007`) | `moveq #0xFF, %d0` + nops | All system switches permanently inactive |
| 5+ | Control writes (`0x380000`) | 3× `nop` | Coin lockout / flip-screen writes suppressed |

**Total TC0040IOC patch sites: approximately 19–22 instructions.**

All patches use the existing `startup_title_remap.json` patch infrastructure — same `replacement_bytes` format, same patcher toolchain, same build pipeline.

---

## 6. What Must NOT Be Done

- **Do not leave any `moveb 0x39000x, %d0` instruction unpatched.** On Genesis hardware these addresses are either unmapped (bus error) or map to unexpected memory. Either outcome corrupts registers or crashes the game.
- **Do not use SGDK `JOY_update` for input.** The no-SGDK branch has no SGDK. Input is read directly from `0xA10003` / `0xA10005` in the pad stub, or cached in a shadow byte updated once per main-loop frame.
- **Do not make DIP values runtime-configurable.** The purpose of this branch is a fixed factory-default ROM. Hardcoded constants in `replacement_bytes` fields are the correct and complete solution.

---

## 7. Reference: TC0040IOC in Rainbow Islands Genesis

Rainbow Islands Genesis (same Taito hardware) handles TC0040IOC identically:

- All DIP reads replaced with hardcoded immediate values in the patched binary
- Joystick reads replaced with Genesis pad read stubs
- Coin input routed to a Genesis button (typically Start or A)
- Service/test/tilt reads replaced with "inactive" constants
- Control register writes (`0x380000`) suppressed with NOPs

This confirms the patch approach described above is proven and correct for this hardware family.
