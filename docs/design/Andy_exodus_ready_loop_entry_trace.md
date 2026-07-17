# Andy/Opus — Exodus READY-Screen Loop Entry Trace (Build 0193)

**Date:** 2026-07-16
**Type:** Static mapping + MAME dynamic reproduction of the code path Tighe observed stuck in Exodus. **No build.** Andy cannot run Exodus; Exodus PCs are Tighe's external evidence.
**Baseline:** Build 0193 `ee3d236e…`, counter 193, mirror 256.

## Andy can run Exodus: NO. All Exodus PCs below are "Tighe observed in Exodus"; MAME results are Andy's reproduction.

## Executive result
The final Exodus lock at **runtime 0x0003A342 / 0x0003A346 is a TC0140SYT sound-chip busy-wait.** The arcade sound-command dispatcher polls the TC0140SYT status register (0x3E0003) waiting for the sound CPU's busy bit (bit 0) to clear. The Genesis has no TC0140SYT; 0x3E0003 is out-of-physical-ROM cartridge space whose read value is emulator-dependent open bus. **MAME/BlastEm return 0x00 (bit 0 = 0) → the loop exits → gameplay is reached. Exodus (strict open-bus) returns a value with bit 0 = 1 → the loop spins forever → lock.** The sound-status READ at runtime 0x3F2A4 (arcade 0x3F0A4) is NOT redirected on Genesis (the spec suppresses only the TC0140SYT WRITES).

## Primary classification — **A** (normal arcade sound-ready wait; Exodus is missing the exit event that MAME/BlastEm accidentally provide). Mechanism is F-flavored (the 0x3E0003 read value differs by emulator).

## Static mapping of the observed PCs (Build 0193 ROM)
| Runtime PC(s) | Owner | File | Kind | Meaning |
|---|---|---|---|---|
| 0x70090..0x700B4 | `vdp_set_vram_write_addr` (+ `sprite_dma_addr_high_bits_fix`) | vdp_comm.s | Genesis helper | VRAM write-address setup, called from the FG-strip commit |
| 0x70298..0x702D8 | `vdp_commit_fg_strips_if_dirty` | vdp_comm.s | Genesis helper | per-row FG strip commit; outer loop over 32 rows of `fg_row_dirty` (0xFF402C) |
| 0x702BA/0x702C0 | (inner of above) | vdp_comm.s | Genesis helper | `movew (a0)+,0xC00000` / `dbf d7,..` — **bounded 64-word DMA loop** (staged_fg_buffer→VDP) |
| 0x702F0/0x702F6 | `vdp_commit_palette` | vdp_comm.s | Genesis helper | `movew (a0)+,0xC00000` / `dbf d7,..` — **bounded 64-word CRAM copy** (staged_palette_words→CRAM) |
| 0x3A33E..0x3A346 | arcade sound dispatcher (arcade 0x3A13E..0x3A146) | translated arcade | arcade code | **the lock:** `bsr 0x3F29C; btst #0,d0; bne 0x3A33E` |
| 0x3F29C..0x3F2AA | TC0140SYT status read (arcade 0x3F09C) | translated arcade | arcade code | `moveb #4,0x3E0001` (port select, write); `moveb 0x3E0003,d0` (status read); `rts` |

The 0x702xx PCs Tighe saw first are the **normal per-frame VBlank commit `dbf` loops** (palette + FG strips) — bounded, they run and `rts` every frame. They are classification **G** (debugger sampling of valid bounded loops), not the lock. They indicate the game is idling at READY, running its VBlank service each frame, then entering the sound dispatch.

## The lock, disassembled (runtime)
```
3a326: tstw  %a5@(52)            ; A5+0x34 (state)
3a32a: bne   0x3a334
3a32c: cmpiw #1,%a5@(5012)       ; A5+0x1394 == 1 ?
3a332: bne   0x3a358             ; else return
3a334: lea   %a5@(658),%fp       ; fp = A5+0x292  (6-entry sound-command slot array)
3a338: moveq #6,%d1
3a33a: tstb  %fp@                ; pending command in this slot?
3a33c: beqs  0x3a352             ; no -> next slot
3a33e: bsrw  0x3f29c             ; YES: read TC0140SYT status  <-- LOOP HEAD
3a342: btst  #0,%d0             ; busy bit
3a346: bnes  0x3a33e             ; wait while busy  <-- SPINS if 0x3E0003 bit0 stuck 1
3a348: moveb %fp@,%d0            ; command byte
3a34a: bsrw  0x3f284             ; send command to sound (also TC0140SYT)
3a34e: clrb  %fp@                ; clear slot
3a350: rts
3a352: addqw #1,%fp ; subqw #1,%d1 ; bnes 0x3a33a   ; 6 slots

3f29c: moveb #4,0x3e0001         ; TC0140SYT: select master port 4 (write -> unmapped on Genesis, dropped)
3f2a4: moveb 0x3e0003,%d0        ; TC0140SYT master read (status) -> emulator-dependent open bus on Genesis
3f2aa: rts
```

## Branch-condition proof
- **0x702F0/0x702F6:** `dbf %d7,0x702f0` with d7=63 → exactly 64 iterations then `rts`. Exit value: d7 counts to −1. Writer: none needed (self-terminating). Not a lock. (Same shape for 0x702BA/0x702C0, per dirty FG row.)
- **0x3A342/0x3A346:** `btst #0,%d0; bnes 0x3a33e`. Tested value: **bit 0 of d0, loaded from byte 0x3E0003**. Exit requires 0x3E0003 bit 0 = 0. Writer of 0x3E0003: on real arcade, the **TC0140SYT / Z80 sound CPU** clears busy when ready; **on Genesis nothing writes it — it is pure emulator open-bus for an out-of-physical-ROM cartridge address** (ROM is 1.58 MB; 0x3E0003 ≈ 3.87 MB). MAME open-bus = 0x00 (bit 0 = 0) → exits. Exodus open-bus apparently has bit 0 = 1 → spins.

## MAME reproduction (Andy)
- 0x3E0003 reads during the READY→gameplay window: value histogram **0x00 (bit0=0) ×297, 0xFF (bit0=1) ×3**; first read 0xFF then 0x00.
- Loop `0x3A346` bne-loopback hits = 3; `0x3A348` loop-exit hits = 3 → **loop EXITS in MAME every time**.
- At 0x3A342 first hit: **D0 = 0x00010000, bit 0 = 0** → `bne` not taken → fall through to send-command and exit.
- MAME (and, per Tighe, BlastEm) reach gameplay because 0x3E0003 reads bit 0 = 0.

## Exodus-only evidence available: NONE (Andy cannot run Exodus). Tighe's observation is the 0x3A342/0x3A346 spin.

## State fields (MAME, at the loop)
- A5@(0x34) and A5@(0x1394) gate entry to the dispatcher (READY-phase state). A5+0x292..0x297 = the 6 sound-command slots; a non-zero slot triggers the wait+send. These are game-state and behave normally in MAME (the dispatcher runs and completes).
- SR/interrupts: not the issue (the loop is a data-poll busy-wait, not interrupt-gated).
- VDP/DMA: not involved in this loop (the 0x702xx VDP loops are earlier and bounded).

## Ownership / metadata
- Arcade routine (0x3A126 region) = sound-command dispatcher; 0x3F09C = TC0140SYT master-status read; 0x3F084 = TC0140SYT send. Normal arcade sound handshake.
- Genesis has SUPPRESSED the TC0140SYT **write** side (spec opcode_replace: `13FC0004003E0001`, `13FC0001003E0003`, etc. — "Suppress arcade TC0140SYT sound-CPU reset/bank write"). The **status-read busy-wait (0x3F0A4, 0x3E0003) is NOT redirected** — confirmed absent from specs/rastan_direct_remap.json. So the loop's exit is left to emulator open-bus. **Structured metadata is not wrong, but incomplete for this class:** the read-side handshake has no Genesis owner. No metadata change made (no build).

## Exodus inspection checklist for Tighe (specific, minimal)
1. **Break at PC `0x0003A342`** (`btst #0,%d0`).
   - Inspect **D0** (low byte). Expected MAME/BlastEm: **0x00** (bit 0 = 0) → falls through, loop exits. Exodus stuck: **bit 0 = 1** (odd value, e.g. 0x…01 / 0x…FF).
2. **Inspect memory byte `0x003E0003`.**
   - Expected MAME: **0x00**. If Exodus shows **bit 0 = 1** (0x01, 0x03, 0xFF, …) → confirmed root: the TC0140SYT status read returns busy.
3. **Break at PC `0x0003F2A4`** (`moveb 0x3E0003,%d0`) — the exact read. Confirm the byte Exodus returns for out-of-ROM 0x3E0003.
4. **Writer check:** no Genesis code writes 0x3E0003 (search your trace for writes to 0x3E0003 — expect none). The value is Exodus open-bus for a cartridge address beyond the 1.58 MB ROM.
5. **Interpretation:**
   - If Exodus 0x3E0003 bit 0 = 1 → **confirmed**: the unredirected TC0140SYT sound busy-wait never exits because Exodus's out-of-ROM open-bus has bit 0 set. Fix = redirect the read (see below).
   - If Exodus 0x3E0003 bit 0 = 0 but it still spins → a different problem (unexpected; would need a fresh trace).
6. (Optional context) At `0x0003A334`, `A5+0x292..0x297` are the 6 sound-command slots; a non-zero slot is what enters the wait. Confirm at least one is non-zero (a queued sound command) — expected.

## Proposed fix (NOT built; for Tighe's decision)
Redirect the TC0140SYT master-status read so the busy bit always reads clear on Genesis — e.g. an opcode_replace at arcade 0x3F0A4 turning `moveb 0x3E0003,%d0` into a helper (or immediate) that returns bit 0 = 0 (sound always ready), OR route the whole handshake (0x3F084 send / 0x3F09C status) through the existing Genesis Z80 sound path (z80_write_command / sound_comm.s). This makes the loop exit deterministically on ALL emulators including Exodus, independent of open-bus. Consistent with the existing "suppress TC0140SYT writes; drive sound via the Z80 driver" strategy. Do NOT NOP the loop or force the branch.

## Not touched
No source change; no metadata change; Build 0193 intact; mirror 256. No gameplay/palette/VBlank/PC090OJ/PC080SN changes.
