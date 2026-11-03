# Rastan Sound Command Execution — Verified Analysis

**Author:** Andy (Analysis Agent)  
**Date:** 2026-04-06  
**Source:** `/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt`  
**Prior art:** `Andy_rastan_arcade_sound_and_rainbow_bridge.md`

---

## 1. Entry Point Confirmation

`0x3F084` is confirmed as the single send routine for all sound commands. Exact disassembly:

```
3f084:  13fc 0000 003e 0001   moveb #0, 0x3e0001        ; write 0 to TC0140SYT control port
3f08c:  13c0 003e 0003        moveb %d0, 0x3e0003       ; write full command byte to data port
3f092:  e808                  lsrb #4, %d0              ; shift right 4: high nibble → low
3f094:  13c0 003e 0003        moveb %d0, 0x3e0003       ; write high nibble (now in low pos)
3f09a:  4e75                  rts
```

The busy-poll helper at `0x3F09C` (used only by the queue flush path):

```
3f09c:  13fc 0004 003e 0001   moveb #4, 0x3e0001        ; write 4 to control port (status request)
3f0a4:  1039 003e 0003        moveb 0x3e0003, %d0       ; read status byte
3f0aa:  4e75                  rts
```

The caller polls `btst #0, %d0; bnes loop` — busy when bit 0 = 1, ready when bit 0 = 0.

---

## 2. Register State at Call

- **Register used:** D0 (byte, lower 8 bits)
- **No stack argument:** command is never pushed to stack; all call sites load D0 immediately before the call (via `moveb #N, %d0`, `movew #N, %d0`, or `moveb mem, %d0`)
- **D0 is consumed and destroyed** by `lsrb #4` during execution; callers do not depend on D0 after the call
- No other registers are read or modified by `0x3F084`

---

## 3. Exact Command Value Format

- **Width:** 8-bit command byte (D0[7:0])
- **Nibble split:** LOW nibble written first, HIGH nibble written second
  - Write 1 to `0x3E0003`: the full byte D0 (bits [3:0] = low nibble; bits [7:4] are present but TC0140SYT uses only the nibble)
  - Write 2 to `0x3E0003`: D0 >> 4 (bits [3:0] = original high nibble; upper 4 bits are 0)
- **Prefix write:** `moveb #0, 0x3E0001` is issued before both data writes; this selects the write-to-Z80 channel on the TC0140SYT

**Reconstruction by Z80:** `command = (write2 & 0x0F) << 4 | (write1 & 0x0F)` = original D0 byte.

**Observed command byte range** (all confirmed from disassembly):

| Hex  | Dec | Source type    | Context                                   |
|------|-----|----------------|-------------------------------------------|
| 0x00 | 0   | Direct & queue | Stop all sound (state transitions, game over, attract reset) |
| 0x04 | 4   | Direct         | SFX (coin/start event area)               |
| 0x05 | 5   | Queue          | SFX                                       |
| 0x0D | 13  | Queue          | SFX / BGM                                 |
| 0x10 | 16  | Queue          | BGM / SFX                                 |
| 0x11 | 17  | Queue          | BGM / SFX                                 |
| 0x12 | 18  | Queue          | BGM / SFX                                 |
| 0x13 | 19  | Queue          | BGM / SFX                                 |
| 0x14 | 20  | Queue          | BGM / SFX                                 |
| 0x15 | 21  | Queue          | BGM / SFX                                 |
| 0x16 | 22  | Queue          | BGM / SFX                                 |
| 0x17 | 23  | Queue          | BGM / SFX                                 |
| 0x18 | 24  | Queue          | BGM / SFX                                 |
| 0x1E | 30  | Direct         | State transition BGM                      |
| 0x1F | 31  | Direct         | High score entry BGM                      |
| 0x23 | 35  | Filtered       | Enqueue guard excludes this value (see §8) |
| 0x25 | 37  | Direct & queue | Attract/title BGM (most frequent, ~10+ sites) |
| 0x29 | 41  | Direct & queue | In-game BGM (player active)               |
| 0x2A | 42  | Queue          | BGM variant                               |
| 0x2B | 43  | Queue          | BGM variant                               |
| 0xEF | 239 | Direct         | Game-over specific (demo over sequence)   |

---

## 4. Write Sequence to Sound Hardware

**Full hardware transaction sequence** (3 bus cycles total):

```
cycle 1: WRITE  byte 0x00  →  address 0x3E0001  (TC0140SYT: select Z80 write channel)
cycle 2: WRITE  byte D0    →  address 0x3E0003  (low nibble of command byte)
cycle 3: WRITE  byte D0>>4 →  address 0x3E0003  (high nibble of command byte)
```

No read cycle occurs within `0x3F084`. The busy-poll (read cycle at `0x3F09C`) is performed only by the queue flush caller, not by `0x3F084` itself.

**Hardware addresses:**
- `0x3E0001` = TC0140SYT command/address port
- `0x3E0003` = TC0140SYT data port

---

## 5. Timing Characteristics

**All sound commands — without exception — are issued from within the Level 5 autovector interrupt handler.**

The interrupt vector table (ROM offset 0x74, vector 29) points to `0x3A008`, the Level 5 handler entry:

```
3a008:  007c 0f00   oriw #3840, %sr       ; mask all interrupts (IPL=7)
3a00c:  ...         [game logic body]
3a07a:  027c f0ff   andiw #-3841, %sr     ; unmask interrupts
3a07e:  4e73        rte
```

The complete game logic — including all sound state-machine dispatch, queue flush, and direct sound calls — executes between `0x3A008` and `0x3A07E` on every interrupt frame.

**Interrupt origin:** Level 5 autovector, periodic hardware timer. All other interrupt levels (1–4, 6) route to a fatal error handler (`0x3A080`). Level 7 is unused.

**Interrupt rate:** One interrupt per display frame (~60 Hz at Taito F1 arcade clock rates).

**There is no main loop.** The reset entry (`0x3AE86`) runs hardware initialization once, then idles. All runtime behavior is interrupt-driven.

**Calls are synchronous** relative to game state. Sound commands are issued on the frame in which a game event occurs, not on a deferred or queued basis for direct calls. The queue path defers by at most N frames where N = position of command in queue (max 6).

---

## 6. Command Frequency

**Per interrupt frame (per ~60Hz tick):**

- **Queue path:** At most **1 command** per frame. The flush routine at `0x3A12C` scans the 6-slot buffer, finds the first non-zero entry, busy-polls for ready, sends it, clears the slot, and returns immediately. Subsequent slots are deferred to the next frame.

- **Direct call path:** At most **1 command** per state-machine transition event. State transitions occur at most once per frame (game state is a single word at `a5@(0)` advanced by the interrupt handler). In practice, multiple direct calls within a single frame are possible if the state machine transitions through intermediate states without looping, but this is unusual.

**Enqueue call sites:** ~72 calls to `0x3A0EC` (primary enqueue) and ~7 calls to `0x3A116` (alternate enqueue, which overwrites slot 0 directly) = ~79 enqueue origination points across the ROM.

**Direct `0x3F084` call sites:** 10 total.

| ROM address | Call type | Command     | Context                          |
|-------------|-----------|-------------|----------------------------------|
| 0x3A14A     | bsrw      | from queue  | Queue flush (1 per frame max)    |
| 0x3A1C8     | bsrw      | 0x25        | Game state dispatch handler      |
| 0x3A238     | bsrw      | 0x1E        | Game state dispatch handler      |
| 0x3A25E     | bsrw      | 0x00        | State transition (stop)          |
| 0x3A97A     | bsrw      | 0x29        | Player-active BGM trigger        |
| 0x3ABA4     | bsrw      | 0x00        | Attract/coin-test branch         |
| 0x3AC6C     | bsrw      | 0x04        | Coin/start event handler         |
| 0x3B060     | bsrw      | 0xEF        | Demo/game-over sequence          |
| 0x3B170     | jsr       | 0x00        | Score-range check stop           |
| 0x3B318     | jsr       | 0x1F        | High score entry screen          |

---

## 7. Multi-Write or Queue Behavior

**Two parallel paths exist:**

### Path A: Direct write (bypasses queue)

All 9 non-flush direct call sites call `0x3F084` immediately with no intermediate buffer and no busy poll. The command byte is written to hardware within the same instruction sequence. There is no intermediate WRAM staging.

### Path B: WRAM queue + per-frame flush

- **Queue buffer:** 6 bytes at `a5@(0x292)` through `a5@(0x297)` (WRAM addresses `0x10C292`–`0x10C297` given `a5 = 0x10C000`)
- **Zero = empty slot** convention
- **Enqueue (`0x3A0EC`):** Linear scan for first 0-byte slot; writes command byte there. No wraparound — if all 6 slots are full, the command is silently dropped.
- **Flush (`0x3A12C`):** Called once per interrupt frame from `0x3A028`. Scans for first non-zero slot, busy-polls via `0x3F09C` (write 4 to `0x3E0001`, read `0x3E0003`, wait for bit 0 = 0), then calls `0x3F084` to send, clears the slot, and returns. Only ONE slot is processed per frame.

**The two paths are not mutually exclusive within a single frame:** a direct call and a queue flush can both occur in the same interrupt frame (e.g., a state-machine BGM command via direct call AND an in-game SFX via queue flush in the same tick). However, the busy-poll before queue flush provides ordering protection for queued commands; direct calls have no such protection and assume the hardware is ready.

**Initialization:** At reset (`0x3AE86`), the TC0140SYT is initialized with direct byte writes (not via `0x3F084`):
```
3aea2:  moveb #4, 0x3E0001    ; reset command
3aeaa:  moveb #1, 0x3E0003
3aec6:  moveb #4, 0x3E0001    ; status clear
3aece:  moveb #0, 0x3E0003
```

---

## 8. Edge Cases

### Command 0x23 (35) is excluded from queueing

The enqueue function at `0x3A0EC` contains an explicit guard:
```
3a0f2:  cmpib #35, %d0
3a0f6:  beqs 0x3a114          ; if d0 == 0x23, skip (return without storing)
```
Command 0x23 is also excluded when the game is not in active gameplay state (`a5@(52) == 0`). Despite appearing at some enqueue call sites (e.g., `0x45952`), it is always filtered before reaching the buffer. Command 0x23 is never sent to the TC0140SYT through the queue path.

### Command 0x00 (stop all sound)

Sent from three direct call sites on state transitions:
- `0x3A25E`: transitioning away from active gameplay
- `0x3ABA4`: on attract mode reset when coin-insert test fails
- `0x3B170`: when score-range condition exceeded

There is no guard preventing 0x00 from being sent multiple times if the state machine re-enters one of these paths. No debounce logic is visible.

### Repeated BGM commands

Command 0x25 (attract/title BGM) appears at 10+ enqueue sites. There is no guard preventing the same BGM command from being enqueued multiple times across different event triggers within the same gameplay session. Each state-machine transition that calls `0x25` enqueues it independently. The TC0140SYT / Z80 sound driver is responsible for determining whether to restart or ignore a repeat of the currently-playing BGM.

### Queue overflow (silent drop)

If all 6 queue slots are occupied when a new enqueue is attempted, the scan reaches the end of the buffer and the command is silently discarded (the loop exits at `0x3A10C/0x3A110` without writing). No overflow flag or error indicator is set.

### Direct calls without busy poll

Nine of the ten `0x3F084` call sites write to hardware without checking TC0140SYT readiness. If the Z80 side is still processing a previous nibble pair when a direct call fires, the second nibble of the previous command or the first nibble of the new command may be overwritten. The busy-poll path (queue flush only) provides correct handshake for queued commands; direct calls rely on timing assumptions.

---

## Strict Contract

```
68000 provides: D0[7:0] = one-byte command value, loaded immediately before call.
                Three hardware writes issued atomically within 0x3F084:
                  1. moveb #0  → 0x3E0001  (channel select)
                  2. moveb D0  → 0x3E0003  (low nibble: D0[3:0])
                  3. moveb D0>>4 → 0x3E0003  (high nibble: original D0[7:4])
                All writes occur within the Level 5 interrupt handler, once per frame.
                Queue path: busy-polled (bit 0 of status read via 0x3E0003 after writing
                  #4 to 0x3E0001) before write; at most 1 queued command per frame.
                Direct path: no busy poll; command written unconditionally.

Z80 must receive: two sequential nibble writes to the data register (0x3E0003),
                  low nibble first, high nibble second.
                  Command byte = (nibble2 << 4) | (nibble1 & 0x0F).
                  Timing requirement: for queue path, Z80 must clear the busy flag
                  (bit 0 of status byte) before the next queued command is issued;
                  for direct path, Z80 must complete processing before the next
                  direct write occurs (no hardware handshake is enforced by 68000).
                  Command 0x00 = stop all sound. Command 0x23 is never transmitted.
                  Maximum queued depth pending at any time: 6 commands.
                  Maximum rate: 1 queued command per 60Hz frame + 1 direct call
                  per state transition event (infrequent; not per-frame).
```
