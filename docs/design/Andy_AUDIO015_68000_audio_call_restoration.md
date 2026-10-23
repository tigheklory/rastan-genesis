# Andy — AUDIO-015: 68000 Audio-Call Audit & `0x19` Delivery Root Cause (corrected by Cody)

> **Correction, 2026-10-23:** The sender-side timer/enable-handshake conclusion below was wrong.
> Original `0x03A0EC` rejects every ordinary queued command while `A5+0x34 == 0`; therefore the
> `0x055E26` `$00` and `0x055E30` `$19` calls cannot publish under the only state that reaches them.
> `0x059F5E`, `0x056176 -> 0x059AD4`, and `0x0561A0 -> 0x055AB4` do not change A5 or
> `A5+0x34`. ORIGINAL ARCADE MAME ring evidence confirms the live sequence is `$29` at Start and
> `$25` exactly at player appearance, with no `$19` publication through frame 1800. The permanent
> correction and complete evidence are in `Cody_build0488_audio_command_semantic_dispatch.md`.
> The historical text is retained below to show what was corrected; its claims that `$19` is the
> live R1-S1 publisher and that the YM2151 IRQ owns the 68000 flags are superseded.

**Task:** AUDIO-015 · **Issue:** OPEN-039 (remains OPEN) · **Agent:** Andy (Opus) · **Date:** 2026-10-23 ·
**Working reference:** Build 0486 (`$29`, plays on hardware at wrong times) · **Candidate:** Build 0487
(`$19`, silent on hardware). Investigation performed via the arcade disassembly
(`build/maincpu.disasm.txt` / `build/regions/maincpu.bin`), the semantic-remap specs, and Genesis NTSC
MAME. No ROM was hex-edited; all findings are at the semantic-remapper / arcade-source level.

## Executive finding

**The original 68000 sound-command execution path is intact. No audio *command* call was replaced with a
NOP.** The premise "audio helper calls were NOPed" does not hold against the evidence: the command
transport (producer → 6-entry queue → dispatcher → PC060HA sender → Z80 ring) is fully present, and it
demonstrably works — commands `EF/04/29/25/1A/0B/0C` reach the Z80 ring, and Build 0486's `$29` produced
audible music on real hardware. The only audio-related NOPs are arcade sound-**hardware** init writes
(TC0140SYT reset/bank/coin), which must stay replaced.

The command transport is intact. The former claim that `$19` was a live R1-S1 request blocked by a
sender-side handshake is superseded by the correction above.

## 1. Complete audio call-site inventory

| Arcade addr | Original operation | Function | Remap status | Correct? |
|---|---|---|---|---|
| `0x03A0EC` | `tst.w a5+0x34; …; move.b d0,(queue)` | command queue insert (6-slot `a5+0x292`) | **intact** (no rule) | ✓ preserved |
| `0x03A116` | `move.b d0,a5+0x292` | direct slot-0 (high-priority) insert | **intact** | ✓ preserved |
| `0x03A126` | queue drain → `bsr 0x3F084` per slot | command dispatcher | **intact** | ✓ preserved |
| `0x03F084` | PC060HA nibble send (`move.b d0,$3E0003`×2) | hardware sender | **shift_replacement → `JSR z80_write_command; RTS`** | ✓ bridged to Z80 ring |
| `0x03F0A4` | `move.b $3E0003,d0` (busy/status read) | sound-busy handshake | **opcode_replace → `andi.l #..FE,d0`** (busy always clear) | ✓ redirected |
| `0x03AEA2`, `0x03AEAA` | `move.b #4/#1,$3E0001/3` | TC0140SYT sound-CPU reset/bank | NOP | ✓ hardware, keep replaced |
| `0x03AEC6`, `0x03AECE` | same (second pass) | TC0140SYT reset/bank | NOP | ✓ hardware |
| `0x03A00C`, `0x03AE96` | `clr.w $350008` | TC0140SYT coin counter | NOP | ✓ hardware |
| `0x055E26` | `move.w #0,d0; jsr 0x3A0EC` | R1-S1 **stop** request (`$00`) | **intact** | ✓ preserved |
| `0x055E30` | `move.w #$19,d0; jsr 0x3A0EC` | R1-S1 **music** request (`$19`, Aggressive World) | **intact** | ✓ preserved |
| `0x03A614` / `0x03A61A` | `move.w #1,a5+0x1394` / `a5+0x13AA` | **music-change trigger** (unlocks the `$19` request) | **intact** | ✓ preserved |
| `0x03A460` | `clr.w a5+0x34` | disable sound (transition) | **intact** | ✓ preserved |
| `0x03A984` | `move.w #1,a5+0x34` | enable sound | **intact** | ✓ preserved |
| `0x05102E` | `move.w 0x10C016,d0` | Stage-1 command-source reader | opcode_replace → operand rebased `0x10C016→0x00FF0016` (KF-039) | ✓ WRAM rebase |

Every music/SFX command producer, the queue, the dispatcher, and the trigger are present. The sender is
correctly bridged to Cody's Z80 engine; the status read and the arcade sound-hardware pokes are correctly
handled. **There is no incorrectly-NOPed sound-command call to restore.**

## 2. The command transport works (evidence)

- PC060HA-port trace on the accepted gameplay baseline 0478 (which retains the original sender): the
  producer emits `EF`@f31, `04`@f120, `29`@f175 — reconstructed from the two-nibble PC060HA writes.
- Build 0486 ring-write trace: `EF,04,29,25,1A,0B,0C` delivered to the Z80 ring; driver active; 831 music
  periods; loop reached; YM2612+PSG writes — and **Tighe confirmed audible music on real Genesis.**
- Therefore the producer→queue→dispatcher→bridge→ring→driver path is functional end-to-end.

## 3. Superseded hypothesis about missing `0x19` delivery

The `$19` request at `0x055E30` sits inside a one-shot stage-music-start block gated by the R1-S1 state at
`0x055DE6`:

```
0x055DE6  cmpi.w #0, a5+0x34      ; sound enabled?
0x055DEC  beq    0x055DFE         ; if sound DISABLED -> check the music-change flag
0x055DEE  move.w #255, a5+0x1394  ; (sound ENABLED) force music-change = 0x00FF
0x055DFA  bra    0x05602A         ;   and skip the music request this pass
0x055DFE  cmpi.w #1, a5+0x1394    ; music-change pending?
0x055E04  bne    0x05602A         ; if != 1 -> skip
0x055E08  cmpi.w #1, a5+0x13AA    ; R1-S1 substate == 1?
0x055E0E  bne    0x055E48
...       bsr 0x56176; bsr 0x561A0
0x055E26  move.w #0,d0;  jsr 0x3A0EC   ; STOP  ($00)
0x055E30  move.w #$19,d0; jsr 0x3A0EC  ; MUSIC ($19)   <-- never reached on Genesis
0x055E3A  move.w #2, a5+0x13AA         ; mark done
```

So `$19` fires **only** when, at this state, `a5+0x1394 == 1` **and** `a5+0x13AA == 1` **and** sound is
momentarily **disabled** (`a5+0x34 == 0`). The music-change trigger `0x03A614` sets `a5+0x1394=1` and
`a5+0x13AA=1`; the arcade briefly disables sound during the stage transition so this block runs with
`a5+0x34 == 0` and issues `$00`+`$19`, then re-enables.

**On the Genesis (Build 0487), the end-of-run state is `a5+0x34 = 1` (sound enabled), `a5+0x1394 = 0x00FF`,
`a5+0x13AA = 1`.** Because sound is enabled when this state runs, the `0x055DEE` path force-sets
`a5+0x1394 = 0x00FF` and **skips** the music request — so `0x055E30` (`$19`) is never executed and `$19` is
never queued. This matches the hardware result: 0487 is silent (authentic `$19` never delivered), while
0486 played on the unrelated game-start cue `$29`.

**Why the handshake doesn't complete:** the arcade's disable→request→enable sequencing around this one-shot
was driven by the arcade **YM2151 timer IRQ / sound sequencer** (vector `0x01F9` → `0x0479`), which
AUDIO-015 deliberately removed when it moved synthesis to the permanent Z80 engine. The retained 68000
command dispatcher (`0x03A126`) still runs (hence `EF/04/29` get out), but the *timed disable/enable of
`a5+0x34` around the stage-music one-shot* no longer lands with the phase the `0x055DE6` block expects, so
`a5+0x1394` is 0x00FF rather than 1 at the decisive moment.

This is a **sender-side state/timing issue, not a NOPed call** — so there is nothing in the semantic
remapper to "restore" for the command path. Fixing it means making the retained R1-S1 one-shot see the
music-change flag as pending with sound disabled at the right moment, i.e. reconciling the
`a5+0x34`/`a5+0x1394` handshake now that the arcade sound IRQ is gone — without hardcoding music at scene
entry.

## 4. Methodology caveat (honesty)

MAME's dynamically-translated 68000 core bypasses memory read/execute taps (and some write taps) after
warm-up (documented in `build0309_gameplay_entry_gate.lua`). So MAME-side "never written / never executed"
observations are corroborating, not conclusive. The **authoritative** evidence is Tighe's real hardware:
0487 (`$19`) silent, 0486 (`$29`) audible. The static gate analysis in §3 is derived from the arcade
disassembly, which is not subject to the tap limitation.

## 5. No new ROM produced by this task (and why)

Acceptance criterion #4 ("the original 68000 can generate and dispatch its sound commands to the permanent
Genesis engine") is already met by Build 0487's source: the transport is intact and verified. There is **no
incorrectly-NOPed call to restore**, so there is no remapper change to build. Re-emitting a numbered ROM
with no source change would not alter behavior. Build 0487 (`dist/rastan-direct/
rastan_direct_video_test_build_0487.bin`, commit `8f6d946e`, SHA
`fd4536f8652029ed39ce92364ee623cb0b7f46adce6353e8c56585e8a36630cc`) remains the current candidate with the
correct authentic `$19` driver.

## 6. Recommended next step (scoped)

The real fix is a **sound-state-handshake reconciliation**, not a call restoration:
1. Determine where the arcade cleared/re-set `a5+0x34` around the R1-S1 one-shot (the removed timer-IRQ
   path `0x01F9`/`0x0479`) and which retained 68000 code now owns that sequencing on Genesis.
2. Make the retained R1-S1 transition present `a5+0x1394 == 1` with `a5+0x34 == 0` at `0x055DE6` exactly
   once per stage start (and on respawn), through the existing semantic remapper, so the original code
   issues `$00`+`$19` at the authentic moment — no scene-ID hardcode.
3. Validate on hardware (Tighe): music starts when Rastan appears, no restart on death, restart on respawn.

That is a targeted follow-up to be scoped with Tighe, since it touches the retained sound state machine
rather than the (correct, working) command transport.

## 7. Corrected status
- Command transport intact: retained.
- `$19` sender-side handshake claim: **RETRACTED**.
- Build 0487: silent/rejected candidate.
- Build 0488: live `$25` appearance-command candidate; see Cody's Build 0488 report. OPEN-039 remains
  open pending Tighe's real-Genesis timing/audio acceptance and the broader multi-song work.
