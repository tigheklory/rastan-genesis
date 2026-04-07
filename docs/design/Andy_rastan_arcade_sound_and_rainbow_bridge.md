# Andy — Rastan Arcade Sound and Rainbow Bridge Analysis

## 1. Executive Summary

This document is a complete disassembly-evidence-based analysis of the Rastan (1987) arcade sound
hardware path, command write sites, command format, command flow, and command categories.  It maps
those findings onto the Rainbow Islands-style Genesis sound architecture defined in
`Cody_rainbow_islands_sound_translation_analysis.md` and produces a single concrete capture and
bridge model for `rastan-direct`.

Key findings:

- Rastan arcade sound hardware: **TC0140SYT** at `0x3E0001` / `0x3E0003`, nibble-pair write
  protocol with optional handshake status read at `0x3E0001 = 4`.
- Two distinct write paths: **direct** (via `0x3F084`, no busy-wait) and **queued** (via `0x3A0EC`
  ring buffer, flushed to `0x3F084`).
- Command unit: **one byte**, transmitted as two 4-bit nibbles.
- Commands divide into BGM events (direct, `0x00`–`0xEF` range) and SFX events (queued,
  `0x05`–`0x25` range observed).
- `rastan-direct` capture model: hook at `0x3F084` write sites and `0x3A0EC` queue sites;
  enqueue as 16-bit event words into 68000 WRAM ring; transfer one per VBlank to Z80 mailbox.
- Bridge model: translate arcade command byte (preserved) plus a class byte (arcade = `0x00`
  prefix) into a 16-bit Rainbow-style word; Z80 decodes class and ID from those two bytes.

---

## 2. Rastan Arcade Sound Hardware Path

**Hardware chip:** TC0140SYT (Taito custom sound arbiter / inter-CPU communication chip).

**Memory-mapped addresses (68000 bus view):**

| Address | Access | Role |
|---------|--------|------|
| `0x3E0001` | Write | Channel select / status strobe byte |
| `0x3E0003` | Write | Nibble data write to Z80 |
| `0x3E0001` | Write `#4` | Select read-status mode |
| `0x3E0003` | Read | Return Z80 status byte |

**Confirmed from disassembly:**

- `0x3F084` (primary write helper, used by all gameplay paths):
  ```asm
  3f084:  moveb #0, 0x3e0001   ; select write channel 0
  3f08c:  moveb D0, 0x3e0003   ; write low nibble (full byte; TC0140SYT latches low 4 bits)
  3f092:  lsrb #4, D0
  3f094:  moveb D0, 0x3e0003   ; write high nibble
  3f09a:  rts
  ```

- `0x1E2` (write + handshake, used in test/init paths only):
  Same two-nibble write sequence, followed by a busy-wait loop checking bit 0 of status byte
  returned from `0x3E0003` (with `0x3E0001 = 4`).

- `0x3F09C` (status read helper):
  ```asm
  3f09c:  moveb #4, 0x3e0001   ; select status read
  3f0a2:  moveb 0x3e0003, D0   ; read Z80 status
  3f0aa:  rts
  ```

**Execution trace confirmation** (`rastan_exec_trace.log`):
- `frame 0 pc=03aeaa`: first write `data=0x04` to `0x3e0000` (byte lane = `0x3e0001`).
- `frame 0 pc=03aeb2`: write `data=0x01` to `0x3e0002` (byte lane = `0x3e0003`).
- `frame 5`: diff on `0x3e0002` confirms Z80 status changes during init.

**0x380000 is NOT sound:** All writes to `0x380000` in the disassembly (`0x3A1D8`, `0x3AE34`,
`0x3AE9C`, `0x3AF1E`, `0x3EF28`, `0x3EF48`, `0x3EF8A`, `0x3EFAA`, `0x45306`) are
TC0040IOC coin-lockout / flip-screen control register writes, confirmed by
`docs/design/TC0040IOC_specifications.md`.

**Answer: Rastan arcade sound hardware path identified: YES**

Arcade sound hardware path: 68000 writes one byte per command to the TC0140SYT at
`0x3E0001`/`0x3E0003` using a two-nibble protocol. There is no direct YM2151 access from the 68000.
All synthesis is owned by the audio Z80 behind the TC0140SYT.

---

## 3. Rastan Sound Command Write Sites

Two independent write paths exist.

### 3.1 Direct write helper: `0x3F084`

Called by: `bsrw 0x3f084` or `jsr 0x3f084`.

| ROM address | Instruction before call | Command byte (D0) | Semantic context |
|-------------|------------------------|-------------------|-----------------|
| `0x3A1C8`   | `moveb #37, D0`         | `0x25` (37)       | State transition ending gameplay phase (clears queues, sets gameplay start flag) |
| `0x3A238`   | `moveb #30, D0`         | `0x1E` (30)       | Timer-driven gameplay state transition; continue/time-up BGM |
| `0x3A25E`   | `moveb #0, D0`          | `0x00`            | Stop/silence: player inactive path |
| `0x3A97A`   | `moveb #41, D0`         | `0x29` (41)       | Game start: credit deducted, game active flag set — stage BGM start |
| `0x3ABA4`   | `moveb #0, D0`          | `0x00`            | Stop/silence: test button triggered in gameplay |
| `0x3AC6C`   | `moveb #4, D0`          | `0x04`            | Coin insert credit-update path — coin sound |
| `0x3B060`   | `movew #239, D0`        | `0xEF` (239)      | Title/attract init sequence; audio system initialization command |
| `0x3B170`   | `moveb #0, D0`          | `0x00`            | Stop/silence: init path after display clear |
| `0x3B318`   | `moveb #31, D0`         | `0x1F` (31)       | High-score name entry: confirmation / UI event sound |

Additionally, the boot/test path uses `0x1E2` (write + handshake) at:

| ROM address | D0 value | Context |
|-------------|----------|---------|
| `0x14E`     | `0xEF`   | Early boot sequence — first audio init command |
| `0x190`     | `0xF0`   | Diagnostic probe to audio CPU |

### 3.2 Queue-based SFX dispatch: `0x3A0EC`

Called by `jsr 0x3a0ec` from gameplay object handlers. D0 holds the SFX command byte on entry.
Confirmed callers and command values:

| Caller ROM address | D0 (command) | Context |
|--------------------|-------------|---------|
| `0x3B792`          | `0x05`      | Player character event |
| `0x40E2A`          | `0x17` (23) | Object state change |
| `0x415AE`          | `0x13` (19) | Object interaction (cmpb #0x4C/#0x55 check on sprite data) |
| `0x41916`          | `0x13` (19) | Same interaction (different branch) |
| `0x425F4`          | `0x16` (22) | Object at zero-state trigger |
| `0x42B1C`          | `0x25` (37) | Object phase-8 trigger |
| `0x430A6`          | `0x11` (17) | Object phase-4 + flag check |
| `0x43AC0`          | `0x12` (18) | Object state `0x8D` match |
| `0x44142`          | `0x18` (24) | Object byte match `0x27` at offset 11 |
| `0x4483C`          | `0x07` or `0x08` (conditional) | Object flag check; two adjacent IDs |
| `0x448D0`          | `0x10` (16) | Object init |
| `0x4539A`          | `0x14` (20) | Object event |
| `0x4591A`          | `0x25` (37) | Object hit/death event (same ID as `0x42B1C`) |
| `0x45948`          | `0x14` (20) | Object event |
| `0x45952`          | `0x23` (35) | Paired call after `0x14` |
| `0x45AD4`          | `0x23` (35) | Object hit |
| `0x45BE0`          | `0x15` (21) | Object event |
| `0x4AC42`          | `0x13` (19) | Gameplay progression trigger |

**Answer: Rastan sound command write sites identified: YES**

---

## 4. Rastan Sound Command Format

**Unit:** One byte per command.

**Transmission encoding:** Two nibble writes to `0x3E0003` preceded by channel-select byte `0x00`
to `0x3E0001`.
- First write: byte value D0 (TC0140SYT latches lower 4 bits as low nibble).
- Second write: D0 >> 4 (upper nibble).

**Byte range observed in gameplay:**
- `0x00` (stop/silence), `0x04` (coin), `0x05`–`0x25` (SFX range), `0x29` (game BGM start),
  `0xEF` (audio init), `0xF0` (diagnostic probe).

**Format class structure:** Command byte is a unified flat ID space as seen by the 68000.
There is no explicit multi-byte command or word-size command from the 68000 side.
The TC0140SYT receives a single byte per command transaction.

**No multi-write sequences:** Each command is one complete transaction (two nibble writes).
There are no observed command+data-byte pairs from the 68000 side in gameplay paths.

**Answer: Rastan sound command format identified: YES**

Format: single byte, transmitted via TC0140SYT two-nibble protocol to `0x3E0001`/`0x3E0003`.

---

## 5. Rastan Sound Command Flow

**68000 gameplay logic** generates sound events in two ways:

### 5.1 Direct path (BGM and system commands)
- Game logic loads command byte into D0.
- Calls `bsr/jsr 0x3F084`.
- `0x3F084` writes immediately to TC0140SYT (`0x3E0001`, `0x3E0003`) without waiting.
- No queuing. No handshake. Write happens in-line within game logic execution.
- Used for BGM transitions, stop commands, coin sound, init.

### 5.2 Queue path (SFX during gameplay)
- Object handler loads SFX command byte into D0.
- Calls `jsr 0x3A0EC`.
- `0x3A0EC` scans a linear buffer at `A5 + 0x292` (7 slots, bytes) for an empty slot.
- Stores D0 into first empty slot.
- Separately, the flush path at `0x3A134`–`0x3A14A` iterates the buffer:
  - Checks each slot; if non-zero: calls `bsr 0x3F09C` (read status with busy-wait check,
    bit 0 of status); if Z80 ready, calls `bsr 0x3F084` to transmit the queued byte.
  - Clears the slot after transmission.

**Handshake semantics:**
- `0x3F084` (direct game-loop path): no handshake. Fire-and-forget.
- `0x1E2` (test/boot path only): full handshake — retries write until Z80 asserts bit 0 of
  status, then waits for busy-clear (bit 0 de-asserted) before returning.
- Queue flush path (`0x3A13E`): polls bit 0 of status via `0x3F09C` before transmitting each
  queued SFX byte; does not block if not ready (falls through).

**What consumes the command:**
- Audio Z80 behind TC0140SYT. The 68000 has no visibility into Z80 execution after write.
- Audio Z80 handles all YM2151, SFX synthesis, and any other sound-side processing.

**Answer: Rastan sound command flow identified: YES**

Flow: 68000 gameplay code → either direct `0x3F084` (BGM/system) or linear SFX buffer
(`0x3A0EC`) → TC0140SYT nibble write → audio Z80 command receive.

---

## 6. Rastan Sound Command Categories

Based on call-site context in the disassembly:

| Command | Hex | Category | Context evidence |
|---------|-----|----------|-----------------|
| `0`     | `0x00` | BGM stop / silence | Sent on player inactive, test button, init reset |
| `4`     | `0x04` | Coin insert sound | Sent in credit management routine after credit count update |
| `5`     | `0x05` | SFX — player event | Gameplay object handler |
| `7`     | `0x07` | SFX — object A | Conditional ID |
| `8`     | `0x08` | SFX — object B | Conditional ID (alternate branch of same check) |
| `16`    | `0x10` | SFX — object init | Object initialization |
| `17`    | `0x11` | SFX — gameplay event | Object phase completion |
| `18`    | `0x12` | SFX — gameplay event | Object state match |
| `19`    | `0x13` | SFX — gameplay event | Sprite interaction (two independent call sites) |
| `20`    | `0x14` | SFX — gameplay event | Two call sites |
| `21`    | `0x15` | SFX — gameplay event | Object hit/event |
| `22`    | `0x16` | SFX — gameplay event | Object zero-state trigger |
| `23`    | `0x17` | SFX — object state | Object state change |
| `24`    | `0x18` | SFX — gameplay event | Object byte match |
| `30`    | `0x1E` | BGM — continue/time-up | Timer-based state transition during gameplay |
| `31`    | `0x1F` | SFX/BGM — UI confirm | High-score name entry confirmation |
| `35`    | `0x23` | SFX — gameplay event | Two call sites (enemy hit) |
| `37`    | `0x25` | BGM — stage / SFX | Both direct BGM (state transition) and queued SFX use this ID |
| `41`    | `0x29` | BGM — game start | Sent immediately after credit deduction; sets gameplay start flag |
| `239`   | `0xEF` | System init | Audio CPU initialization; sent at boot and title entry |
| `240`   | `0xF0` | Diagnostic probe | Test/boot mode only; not issued in normal gameplay |

**Command space structure:**
- The ID space is unified (flat byte values, no class byte on the 68000 side).
- BGM and SFX share the same byte namespace.
- Low IDs (`0x00`–`0x25`) cover all observed gameplay commands.
- High IDs (`0xEF`, `0xF0`) are reserved for system init and diagnostic.
- No attract-vs-gameplay split is visible at the command byte level; context of call site
  determines the functional meaning.

**Two delivery classes by mechanism:**
- Direct (in-line, `0x3F084`): BGM transitions, stop, coin, init.
- Queued (SFX buffer, `0x3A0EC`): all gameplay SFX triggered from object handlers.

**Answer: Rastan sound command categories identified: YES**

---

## 7. `rastan-direct` Capture Model

### Where to capture

Two hook sites are required, not one:

**Hook site 1 — `0x3F084` (direct BGM/system path):**
- Replace `jsr 0x3f084` / `bsr 0x3f084` at all 10 confirmed call sites with a stub call.
- The stub receives D0 = command byte.
- Stub enqueues a 16-bit event word into the 68000-side WRAM ring.
- D0 must be preserved (restored) before the stub returns if any code after the call depends on D0
  (inspection shows D0 is overwritten immediately after all call sites — safe to clobber).

Alternatively: patch the entry of `0x3F084` itself to a Genesis stub (single patch point, 6 bytes).
This intercepts all callers including any undiscovered sites.

**Hook site 2 — `0x3A0EC` (queued SFX path):**
- Replace the TC0140SYT write within the flush path at `0x3A14A` (which calls `0x3F084`) with a
  WRAM enqueue operation.
- Since `0x3A14A` already calls `0x3F084`, patching `0x3F084` entry covers this path automatically
  if the single-entry-patch approach is used.

**Recommended single capture point:** Patch `0x3F084` entry (6 bytes available before the `rts`)
to redirect to a Genesis stub. All 10 direct call sites and all queue-flush calls converge here.

### What to enqueue

Unit: **16-bit word** = `(class_byte << 8) | command_byte`.
- `class_byte = 0x00` for all native Rastan arcade commands (preserves distinction from control
  plane commands).
- `command_byte = D0` at capture time (the original arcade command byte, unchanged).

### Timing

Enqueue: **immediate, in game-logic path** (outside VBlank). The ring must handle potential burst
of multiple SFX commands per frame from object handlers.

Ring depth: minimum 8 words (observed burst: up to 2 SFX per object handler call; with multiple
objects active, 4–6 per frame is plausible). Use 16-word ring for safety.

### No busy-wait on Genesis side

The TC0140SYT busy-wait in `0x3F084` (none present) and in `0x1E2` (handshake only in test mode)
is not needed on Genesis because the Z80 mailbox protocol (VBlank transfer, pending flag) replaces
hardware arbitration.

**Answer: `rastan-direct` capture model defined: YES**

Capture model: single entry-point patch at `0x3F084`; 16-bit word enqueue into 68000 WRAM ring;
immediate execution in game-logic path.

---

## 8. Bridge to Rainbow Islands-Style Genesis Sound Architecture

### Model selection

One model is chosen: **Preserve arcade command byte; translate in Z80.**

The 68000 enqueues `(0x00 << 8) | arcade_cmd_byte` into the WRAM ring. No translation on the 68000
side. The Z80 receives the two bytes via mailbox and maps `arcade_cmd_byte` to YM2612/PSG/DAC
actions through a Rastan-specific translation table.

### Full pipeline

```
[ Rastan 68000 game logic ]
     |
     | D0 = arcade command byte (0x00–0xEF)
     v
[ 0x3F084 patch stub (Genesis shim) ]
     |
     | enqueue word (0x00, D0) into WRAM ring
     | ring at: to-be-defined WRAM address (analogous to Rainbow 0xFFF6C8–0xFFF6CF)
     v
[ 68000 WRAM ring (16 words suggested depth) ]
     |
     | at VBlank, transfer one word if Z80 pending flag clear
     v
[ Z80 mailbox (analogous to Rainbow 0xA01FE0–0xA01FE1, pending flag 0xA01FFE) ]
     |
     | Z80 polls pending flag, latches command word, clears flag
     v
[ Z80 command decoder ]
     | class byte 0x00 → Rastan arcade command dispatch
     | command byte → lookup Rastan command table → YM2612 / PSG / DAC action
     v
[ Genesis-native synthesis ]
```

### Why this model and not 68000-side translation

- Arcade command bytes are small integers (`0x00`–`0x29` for gameplay, `0xEF` for init).
- They carry no hardware-specific register data — they are abstract event IDs.
- Preserving them unchanged at the capture boundary minimizes 68000-side code.
- The Z80 translation table can be updated independently without touching the 68000 patch layer.
- This matches the proven Rainbow Islands model exactly: 68000 emits abstract IDs; Z80 decodes.

### Divergence from Rainbow Islands model

Rainbow Islands uses a 16-bit command word with a class byte that distinguishes BGM/SFX/control.
For Rastan, the class byte can initially be fixed at `0x00` for all arcade-origin commands, with
`0x50` (or another reserved value) available for Genesis-side control-plane commands (pause, fade,
driver state) as in Rainbow Islands.

The VBlank mailbox contract (write pointer, read pointer, pending flag, mailbox address) can be
copied directly from the Rainbow Islands template with address reassignment for Rastan's WRAM
layout.

**Answer: Rainbow-style bridge model defined for Rastan: YES**

Bridge model: 68000 enqueues `(0x00 << 8) | arcade_cmd_byte` unchanged; VBlank transfers one word
to Z80 mailbox per frame; Z80 decodes class + ID and drives YM2612/PSG/DAC via Rastan-specific
command table. Translation happens on Z80 side only.

---

## 9. Risks and Non-Transferable Assumptions

### Proven by arcade disassembly evidence

- TC0140SYT at `0x3E0001`/`0x3E0003` is the sole 68000-to-audio-CPU communication path.
- `0x3F084` is the sole command write helper; all gameplay calls go through it.
- `0x3A0EC` is the SFX queue entry point; buffer at `A5 + 0x292`, 7 byte slots.
- 17 command byte values are confirmed from call-site analysis with D0 load context.
- Command byte `0xEF` is the audio init command, sent at boot and title entry.
- Command byte `0x00` is stop/silence, sent at multiple reset points.
- Command byte `0x04` is coin insert sound.
- Command byte `0x29` is game-start BGM trigger.
- Direct path has no busy-wait; queue flush path has lightweight status poll.

### Inferred from Rainbow Islands model (not directly proven for Rastan)

- Z80 is the synthesis processor on the arcade board. The TC0140SYT implies this but the Z80
  audio program is not available for disassembly (no `audiocpu.disasm.txt` exists in this project).
- YM2151 is the primary synthesis chip on the arcade board (Taito B-type hardware convention).
  Not directly observable from 68000 disassembly.
- The semantic meaning of individual SFX IDs (`0x05`–`0x23`) is inferred from object handler
  context, not confirmed by Z80-side decode analysis.

### High-risk unknowns

1. **No audio Z80 disassembly available.** The Z80 program for Rastan arcade is not present in the
   project. The command byte interpretation on the Z80 side is entirely unknown from this analysis.
   A Rastan-specific Genesis Z80 driver must be written from scratch; it cannot be derived by
   reading the arcade audio Z80.

2. **SFX ID semantic accuracy.** The SFX IDs `0x05`–`0x25` are assigned to object handlers by
   code context, but without Z80-side verification, the exact sounds those IDs produce in the
   arcade are not confirmed. A Rastan-specific Genesis command table must assign sounds to IDs
   based on game design intent, not arcade-side table inspection.

3. **Queue burst rate.** The SFX queue has 7 byte slots. In dense gameplay (multiple enemies,
   projectiles, hits simultaneously), more than 7 SFX events per frame is possible. The Genesis
   WRAM ring depth choice (16 words recommended) is a conservative estimate, not a measured
   maximum.

4. **Command `0x25` dual use.** Command byte `0x25` appears in both the direct BGM path
   (`0x3A1C8`) and the SFX queue path (`0x42B1C`, `0x4591A`). The Z80 translation table must
   handle this correctly — the same byte may need to route differently depending on whether it
   arrives as a BGM transition or as a per-object SFX.

5. **Command `0x1F` classification.** `0x1F` is sent from a high-score name entry context
   (`0x3B318`) via `jsr 0x3F084`. Whether this is a BGM track change or a UI confirm sound
   cannot be determined without Z80-side analysis.

### What cannot be copied from Rainbow Islands

- Rainbow Islands command IDs (`1`, `3`–`7`, `21`–`40`, `0x50` class) are Rainbow-specific.
  None map to Rastan arcade IDs.
- Rainbow Z80 variable layout (`0x1F00`–`0x1FFF`), channel allocation tables, and synthesis
  routines are Rainbow-specific content.
- Rainbow DAC sample banks and PCM data are Rainbow-specific.
- Rainbow queue depth (4-word effective ring) may be insufficient for Rastan SFX density.
- Rainbow VBlank mailbox address contract (`0xA01FE0`, `0xA01FFE`) can be reused structurally
  but the exact addresses must be confirmed against Rastan-direct WRAM layout.

---

## 10. Single Final Recommendation

> How should Rastan arcade sound commands be captured and mapped into the Rainbow Islands-style
> Genesis sound architecture for `rastan-direct`?

**Recommendation:**

Patch the entry point of `0x3F084` (6 bytes) with a `jsr` to a Genesis shim routine. The shim
receives D0 = arcade command byte, constructs a 16-bit word as `(0x00 << 8) | D0`, and pushes it
into a 16-word WRAM ring buffer at a fixed address in Rastan-direct's WRAM layout. During VBlank,
the video commit phase checks the Z80 pending flag (`0xA01FFE`); if clear and ring non-empty, it
pops one word, writes the two bytes to Z80 mailbox (`0xA01FE0`, `0xA01FE1`), and sets the pending
flag. The Genesis Z80 driver polls the pending flag, latches the command word, clears the flag, and
dispatches on class byte `0x00` to a Rastan-specific synthesis table that maps command IDs to
YM2612/PSG/DAC actions. No translation occurs on the 68000 side. All arcade command bytes are
preserved unchanged at the capture boundary and translated only within the Z80 driver.

This is a single-site patch on the 68000 side, a verbatim adoption of the Rainbow Islands VBlank
mailbox transfer contract, and a Genesis-native Z80 driver with a Rastan-specific command dispatch
table.

---

## 11. Final Verdict

Rastan arcade sound communication is a one-byte-per-command protocol through the TC0140SYT at
`0x3E0001`/`0x3E0003`. The 68000 uses a single write helper (`0x3F084`) and a 7-slot SFX queue
(`0x3A0EC`). Both paths converge at `0x3F084`. Patching `0x3F084`'s entry point is the minimal and
complete capture point for all arcade sound commands. The Rainbow Islands 68000 ring-queue +
VBlank mailbox transfer + Z80-owned synthesis model applies without structural change; only the Z80
driver's command dispatch table and synthesis content are Rastan-specific. No Z80-side arcade
disassembly exists in this project; the Genesis Z80 driver is a new composition, not a port.
