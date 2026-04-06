# Cody Rainbow Islands Sound Translation Analysis

## 1. Executive Summary
This analysis disassembles Rainbow Islands Genesis sound ownership from the 68000 ROM and the uploaded Z80 driver blob.

Proven architecture:
- Sound synthesis is owned by Z80 driver code uploaded by 68000 from ROM offset `0x7E000`.
- 68000 emits sound commands into a WRAM queue, then transfers one command per VBlank to a Z80 mailbox.
- Z80 consumes mailbox commands and drives YM2612, PSG, and YM2612 DAC playback.
- Sound execution is asynchronous on Z80; VBlank participates only in mailbox transfer.

## 2. Rainbow Islands Sound Architecture

### Hardware usage
- Z80 used: YES
- YM2612 used: YES
- PSG used: YES
- PCM/DAC playback used: YES

### Evidence
- 68000 Z80 upload/init routine at `0x1195A`:
  - loads source from ROM `0x07E000` into Z80 RAM `0xA00000` for `0x2000` bytes.
  - controls `0xA11100` (bus request) and `0xA11200` (reset).
- Z80 blob contains YM writes:
  - `LD (0x4000),A` and `LD (0x4001),A` at offsets `0x0010/0x0017`, `0x0D4E/0x0D54`, `0x0D59/0x0D64`.
  - `LD (0x4002),A` and `LD (0x4003),A` at offsets `0x0D96/0x0D9C`, `0x0DA2/0x0DA8`.
- Z80 blob contains PSG writes:
  - `LD (0x7F11),A` at offsets `0x05FD`, `0x0601`, `0x062C`, `0x063D`, `0x0664`, `0x112E`, `0x1136`, `0x134E`, `0x1353`, `0x1358`, `0x135D`.
- DAC/PCM evidence:
  - YM register `0x2A` write sequence at Z80 offsets `0x0D57` / `0x0D59`, followed by sample stream writes to `0x4001` in loop (`0x0D63` onward).
  - YM register `0x2B` control sequence at `0x0D90`.

### Processor responsibilities
- 68000 responsibilities:
  - queue command words in WRAM.
  - transfer mailbox command to Z80-visible RAM.
  - initialize/reset/upload/start Z80 driver.
- Z80 responsibilities:
  - command decode.
  - music/SFX channel state.
  - YM2612/PSG register programming.
  - DAC sample streaming.

## 3. 68000 ↔ Z80 Communication Model

### 68000 command enqueue
- Routine: `0x118D6`
- Behavior:
  - receives command in `D0`.
  - pushes 16-bit command into ring buffer.
  - ring write pointer: `0xFFF6C0`.
  - ring read pointer: `0xFFF6C4`.
  - ring storage region: `0xFFF6C8` to `0xFFF6CF`.

### VBlank transfer to Z80 mailbox
- Routine: `0x1190A` (called from VBlank at `0x0408`).
- Behavior:
  - checks mailbox busy flag `0xA01FFE`.
  - if clear and queue non-empty, pops one word from queue.
  - writes command bytes to `0xA01FE0` and `0xA01FE1`.
  - sets `0xA01FFE = 1` (command pending).

### Z80 mailbox consume
- Z80 offsets `0x003A`-`0x0059`:
  - reads `0x1FFE` pending flag.
  - copies command word from `0x1FE0/0x1FE1` into internal `0x1F12/0x1F13`.
  - clears `0x1FFE`.

Communication model identified: YES.

Model type: mailbox + 68000-side ring queue.

## 4. Z80 Driver Structure

### Location and load
- ROM source: `0x07E000` to `0x07FFFF` (8KB).
- Uploaded to Z80 RAM `0x0000`-`0x1FFF` by 68000 `0x1195A`.

### Entry and core flow
- Z80 entry: offset `0x0000` = `JP 0x016E`.
- Register-write helper via `RST 0x08` path rooted at offset `0x0008`, with YM busy-wait then register/data write.
- Command latch stage: offsets `0x003A`-`0x0059`.
- Command parser/dispatcher: dense decode block around offsets `0x0BC4`-`0x0D24`, using internal variables `0x1F00`-`0x1F1F` and command bytes `0x1F12/0x1F13`.
- Runtime synthesis paths:
  - PSG control blocks include writes to `0x7F11`.
  - YM/FM control blocks include writes to `0x4000-0x4003`.
  - DAC streaming loop includes `0x2A` register programming and repeated data writes.

Z80 driver structure identified: YES.

## 5. Sound Command Format

### 68000-side payload
- Command unit is 16-bit word (`D0`) enqueued by `0x118D6`.

### Mailbox packing
- `0x1190A` writes swapped bytes to mailbox:
  - byte 0 to `0xA01FE0`
  - byte 1 to `0xA01FE1`
- Z80 loads mailbox word and stores internal bytes:
  - `0x1F12` = command class byte
  - `0x1F13` = command ID byte

### Decoder evidence
- Z80 compares class byte (`0x1F12`) against control values:
  - at `0x0BEB`: `CP 0x50`
  - at `0x0D3E`: `CP 0x50`
- 68000 emits command `0x5000` at `0x1DF2` / `0x1E3A`, matching class-`0x50` control path.
- Many gameplay calls emit low-ID commands (`1`, `3`, `4`, `5`, `6`, `7`, `21`..`40`) via `JSR 0x118D6`.

Command format identified: YES.

Format conclusion: 16-bit message = class byte + command ID byte.

## 6. Arcade-to-Genesis Translation Model
Rainbow sound behavior on Genesis uses event-level command translation, not chip-register emulation.

### Proven mapping style
- 68000 gameplay emits abstract sound event commands.
- Z80 driver translates command class/ID into YM2612/PSG/DAC operations through internal tables/state.
- No 68000 path writes YM2612 registers directly in gameplay logic.

### Translation characteristic
- Arcade intent preserved at command/event level (BGM/SFX/control events).
- Hardware realization replaced with Genesis-native Z80 + YM2612/PSG(+DAC) driver actions.

Arcade-to-genesis translation model identified: YES.

## 7. Timing and Synchronization Model
- Command issue timing:
  - gameplay code enqueues commands whenever events occur (outside VBlank).
- Mailbox transfer timing:
  - one command transfer opportunity per VBlank in `0x1190A`.
- Sound synthesis timing:
  - runs on Z80 independently of VBlank once command is consumed.

Answers:
- Sound depends on VBlank: NO (synthesis path), YES (68000 mailbox transfer cadence).
- Sound processing blocks gameplay: NO.

Timing model identified: YES.

## 8. Template Patterns for `rastan-direct`

| Pattern | Directly reusable | Why | Required adaptation |
|---|---|---|---|
| 68000 ring queue + VBlank mailbox transfer | YES | Decouples gameplay event burst from single mailbox flag | Queue depth and overflow policy for Rastan event rate |
| Mailbox contract at top of Z80 RAM (`cmd bytes + pending flag`) | YES | Minimal shared-state protocol | Address contract and endian packing rules must be fixed in Rastan spec |
| Z80-owned command decode and synthesis | YES | Keeps audio independent from 68000 video/VBlank workload | New command tables mapped to Rastan BGM/SFX set |
| YM write helper with busy-wait gate | YES | Deterministic YM register programming | Integrate with Rastan driver timing and channel allocation |
| PSG write path through Z80 | YES | Matches hardware ownership model | Replace Rainbow PSG patterns with Rastan-authored instruments/SFX |
| DAC command class (`0x50` control path + DAC register use) | YES | Supports effects requiring sampled playback | Reassign class IDs and sample format/tables for Rastan content |
| Upload 8KB Z80 image from ROM at boot | YES | Simple no-SGDK bring-up path | Rastan-direct must define its own Z80 blob image and versioning |

Template patterns extracted: YES.

## 9. Non-Transferable Assumptions
- Rainbow command IDs and class semantics are game-specific.
- Rainbow Z80 variable map (`0x1F00` region layout) is driver-specific.
- Rainbow music/SFX data tables and pointer layouts are content-specific.
- Rainbow DAC sample loop assumptions and sample banks are content-specific.
- Rainbow queue size (4 words effective in observed ring) is not automatically valid for Rastan event density.

Non-transferable assumptions identified: YES.

## 10. Rastan Direct Sound Model

### Proposed single concrete model
1. Capture arcade sound events at translated opcode/memory-write sites into 16-bit event words in 68000 WRAM queue.
2. During VBlank (video commit phase), perform only mailbox transfer work:
   - if Z80 pending flag is clear, pop one queued event and write to Z80 mailbox bytes.
   - set pending flag.
3. Z80 main loop polls pending flag, latches command class/ID, clears flag, dispatches command.
4. Z80 owns all YM2612/PSG/DAC writes and all channel state.
5. Sound execution runs fully independent of VBlank after command latch.

### Command-ID policy
- Keep arcade IDs unchanged at capture boundary when ID space is stable.
- Add a Z80-side translation table from arcade IDs to Genesis driver actions.
- Reserve non-arcade class bytes for control-plane commands (pause/fade/driver-state).

Rastan direct sound model defined: YES.

## 11. Single Final Recommendation
Use Rainbow Islands’ **68000 ring-queue + VBlank mailbox transfer + Z80-owned synthesis** architecture as the `rastan-direct` sound template, and implement a Rastan-specific Z80 translation table that maps captured arcade sound events to YM2612/PSG/DAC actions without SGDK ownership.

## 12. Final Verdict
Rainbow Islands provides a complete direct-execution sound ownership template for `rastan-direct`: 68000 event enqueue, VBlank mailbox handoff, and autonomous Z80 synthesis on YM2612/PSG/DAC.
