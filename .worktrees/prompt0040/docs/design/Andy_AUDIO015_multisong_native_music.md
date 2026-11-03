# Andy — AUDIO-015: Multi-Song Native Genesis Music + Audio Composer Integration

**Task:** AUDIO-015 (continuing) · **Issue:** OPEN-039 (remains OPEN) · **Agent:** Andy (Opus) ·
**Date:** 2026-10-23 · **Accepted gameplay baseline:** Build 0478 · **Starting point:** Build 0486
(commit `26ca2ac2`). Builds on Cody's working permanent Genesis Z80 audio engine — **not** a rearchitecture.

This document is written incrementally as the phased work lands. Phase A is complete; Phases B and C are
pending Tighe's hardware confirmation of the Phase-A trigger timing.

---

## Phase A — Correct the Aggressive World trigger (`0x29` → `0x19`) — **REJECTED (Build 0487)**

> **Cody correction, 2026-10-23:** the `$19` attribution was not proven and Build 0487 was silent on
> hardware. Static original-code proof shows `0x055E30` calls a queue that rejects the command under
> the only gate state that reaches it. ORIGINAL ARCADE MAME then showed `$29` at Start and live `$25`
> exactly at player appearance, with no `$19` publication. Build 0488 therefore translates the shared
> live `$25` command to the currently implemented native Aggressive World asset. See
> `Cody_build0488_audio_command_semantic_dispatch.md`.

### Problem (confirmed on real hardware by Tighe, 0486)
| Event | 0486 behavior | Correct behavior |
|---|---|---|
| Press Start | music begins immediately | should not begin |
| Rastan appears | already playing | Aggressive World begins |
| Rastan dies | music restarts | should not restart |
| Rastan respawns | already playing | Aggressive World restarts |

### Root cause
The driver compared the incoming wire command against `0x29`. Evidence:
- **Static (authoritative):** the sole `move.w #$19,d0; jsr` R1-S1 music producer is at arcade `0x055E30`
  (runtime ROM `0x055ECA`), paired with the `0x00` stop at `0x055E26`/`0x055EC0`. `0x19` selects the
  8-channel descriptor `0x2DF0` = Aggressive World (Cody's semantic-recovery doc + my disasm). The bridge
  at `0x03F084` forwards `d0` to the Z80 command ring **unchanged** (no transform).
- **Dynamic (PC060HA-port trace on accepted 0478 with gameplay input):** the retained producer emits
  `EF`@f31, `04`@f120, `29`@f175 (the Start press) — a game-start/ready cue. `0x29` is a *different*
  3-channel descriptor (`0x29F0`), **not** Aggressive World. So matching `0x29` started the Aggressive
  World asset on the start cue and re-fired it on the death event.

### Fix (smallest change; Cody's engine preserved)
- `apps/rastan-direct/src/sound/z80_driver.asm`: `cp $29` → `cp $19`.
- `tools/audio/verify_genesis_native_audio.py`: driver-classification check `\xFE\x29` → `\xFE\x19`.
- `tools/audio/compile_genesis_native_music.py`: report `authentic_wire_command` `0x29` → `0x19`.
- No change to control flow, Timer B, banking, streaming, or the native stream format.

### Build & verification
- Commit `8f6d946e`; **Build 0487**, 7-ROM family, gates canonical=PASS entry=PASS epoch=PASS.
- Normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0487.bin`
  SHA-256 `fd4536f8652029ed39ce92364ee623cb0b7f46adce6353e8c56585e8a36630cc`.
- Static: build's audio gate confirms the driver classifies `0x19` (FE19 present, FE29 absent), 511-byte
  driver within its executable region.
- **Synthetic** (labeled, not authentic delivery): injecting `0x19` into the Z80 command ring at frame 200
  made the driver go active at frame 201 and stream 668 YM2612 data writes + PSG writes → plays on `0x19`.
- **Not claimed:** start/death/respawn timing correctness — that requires Tighe's hardware listening test.
  MAME gameplay does not advance far enough to deliver the authentic `0x19` from `0x055ECA` (player barely
  moves across thousands of frames), so the authentic trigger could only be validated synthetically; the
  `0x29` game-start cue no longer triggers music.

### Status
Delivered for Tighe's hardware test. Phase B gated on his confirmation that `0x19` fires at stage-start and
that death/respawn sync correctly.

**Hardware result (Tighe):** Build 0487 (`0x19`) is SILENT on real Genesis; Build 0486 (`0x29`) plays but
at the wrong moments. Root cause established in `Andy_AUDIO015_68000_audio_call_restoration.md`: the
command transport is intact (no NOPed call); `0x19` is never issued because the retained R1-S1 one-shot at
`0x055DE6` requires `a5+0x1394==1` with sound momentarily disabled, but the `a5+0x34`/`a5+0x1394`
handshake (formerly driven by the removed arcade sound IRQ) leaves `a5+0x1394=0x00FF`. Fix is a sender-side
state-handshake reconciliation (scoped follow-up), not a remapper call-restore. Phase B still gated.

---

## Phase B — Add all authored songs + native multi-song dispatch — **PENDING**

Planned (not yet implemented):
- Inventory completed Composer arrangements under `analysis/audio/decision_profiles/` (authoritative,
  editable source of truth).
- Extend `tools/audio/compile_genesis_native_music.py` to compile every completed song to the common
  native tick-stream format, per-song routing/levels/noise/pitch from the saved profile.
- Auto-generate a native song registry (per-song cartridge pointer + intro/loop metadata + stable song id)
  and the `audio_assets.s` incbin set from structured metadata — no hand-edited pointers/offsets/labels.
- Extend the Z80 driver's command dispatch to select per-song pointers from the registry (command→song via
  the arcade sound-command inventory; report any unknown authentic mapping honestly, never fabricate one).
- Build dependency tracking so a saved Composer edit regenerates only the affected song and a normal ROM
  build picks it up (content-based, not timestamp-only).

## Phase C — Validate the Composer edit→build workflow — **PENDING**
- Temporary-profile editing test (never touching Tighe's real profile): edit one song → rebuild → only
  that song's native data changes, others unchanged, registry valid, Z80 driver unchanged, reverts
  reproducibly.

---

## Song inventory (to be completed in Phase B)
| Song | Composer status | Original command | Native compile | Intro/loop | Verified |
|---|---|---|---|---|---|
| Aggressive World (R1-S1) | authored (music-test, rev 11) | track-name mapping unresolved; native start intent is live `0x25` | ✅ | ✅ | authentic MAME delivery; hardware pending (0488) |
| _(others)_ | _Phase B inventory_ | | | | |

## Build identifiers
| Build | Commit | What | Normal ROM SHA-256 |
|---|---|---|---|
| 0486 | `26ca2ac2` | Cody's engine, trigger `0x29` | `d0072ac1…ebd7449` |
| 0487 | `8f6d946e` | rejected: trigger `0x19`, silent on hardware | `fd4536f8…a36630cc` |
| 0488 | `13eb6ebf` | live appearance/respawn intent `0x25` | `c70a2715…8ad687e0` |

## Known limitations / unfinished
- The original command-to-track-name registry remains unresolved. `$19` is not a live normal-gameplay
  publisher on the proven path; Build 0488 uses the live `$25` appearance/respawn intent at the shared
  native command boundary.
- Multi-song registry, dispatch, and Composer build integration are Phase B/C (not yet implemented).
- SFX, voices, and FM6 DAC/PCM are out of scope for this assignment (FM6 remains reserved).
