# Cody — Build 0488 AUDIO-015 live sound-command semantic dispatch

## Result

Build 0488 corrects the permanent Genesis Z80 driver's native music-start classification from dead
normal-gameplay command `0x19` to the live original `0x25` player-appearance command. This is a candidate
for Tighe's real-Genesis test, not a hardware acceptance claim.

Baseline: Build 0487 (silent rejected candidate); accepted gameplay baseline remains Build 0478.
Produced build: 0488. Exact ROM-producing source: `13eb6ebf1890213b51700189e7933b058ca8cd3a`.

- Normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0488.bin`
- SHA-256: `c70a271551bf2a10b971ccffa990a7ddf3855c00b134b0004b5407b08ad687e0`
- Size: 2,813,624 bytes
- Build counter: 487 -> 488
- Family: canonical, `_d`, `_s`, `_do`, `_c`, `_full_hud`, `_invincible`
- Canonical coverage: 228 expected opcode-replacement sites; `0x2AEEB8` Genesis bytes covered;
  coverage delta `0x0`

## Root cause and original semantic proof

The previous diagnosis treated arcade `0x055E30` as a live Aggressive World publisher. It is not.
The exact original control flow is:

1. `0x055DE6` permits the `0x055E26/$00` and `0x055E30/$19` calls only on the branch where
   `A5+0x34 == 0`, `A5+0x1394 == 1`, and `A5+0x13AA == 1`.
2. Both calls target `0x03A0EC`.
3. `0x03A0EC` begins `tst.w A5+0x34; beq 0x03A114`, so it returns without queueing any ordinary
   command whenever `A5+0x34 == 0`.
4. The intervening `0x059F5E`, `0x056176 -> 0x059AD4`, and
   `0x0561A0 -> 0x055AB4` paths do not change A5 or `A5+0x34`. The translated `0x059AD4` palette
   helper and `0x055AB4` scroll helper likewise do not change the audio gate.

Thus `$19` can execute as an attempted call but cannot become a queued or delivered sound command on
that path. `A5+0x1394` is a meta/transition controller and `A5+0x13AA` is its substate; neither is an
audio-IRQ handshake. The former claim that a removed YM2151 timer IRQ needed to phase these 68000 flags
is retracted.

The durable ORIGINAL ARCADE MAME route then established the actual live command timing:

| Frame | Command | Retained state |
|---:|---:|---|
| 614 | `0x04` | coin/front-end |
| 656 | `0x29` | Start accepted; before player appearance |
| 787 | `0x25` | exact first player appearance (`state0/2/4=2/3/0`, player state 3, X `0x20`) |
| 788 | `0x1A` | post-entry request |

No external or internally republished `0x19` appeared through frame 1800. Static evidence makes the
dead-under-gate conclusion authoritative; the dynamic result corroborates it. The original Z80 command
inventory itself explicitly says command-to-track-name mapping is unresolved, so the older assertion
that descriptor `0x2DF0` proved `$19 == Aggressive World` was stronger than the evidence.

The live `$25` producer is arcade `0x03A1C4` (`move.b #0x25,D0; bsr 0x03F084`). The live `$29`
producer is `0x03A976/0x03A97A`. The existing shared semantic cut remains arcade `0x03F084`, where the
complete PC060HA nibble-send hardware tail is replaced by `JSR z80_write_command; RTS`; no gameplay
call site or scene state was patched.

Current generated address-map correlations:

| Arcade PC | Runtime Genesis PC | Meaning |
|---|---|---|
| `0x03A0EC` | `0x03A2EC` | six-slot queued insert |
| `0x03A126` | `0x03A326` | queue drain |
| `0x03A1C4` | `0x03A3C4` | live direct `$25` publisher |
| `0x03A97A` | `0x03AB9E` | direct `$29` sender call |
| `0x03F084` | `0x03F298` | PC060HA tail replaced by Genesis ring publication |
| `0x055DDC` | `0x055E66` | transition controller |
| `0x055E30` | `0x055EBA` | dead-under-queue-gate `$19` attempt |
| `0x056176` | `0x056206` | palette setup caller |
| `0x0561A0` | `0x056230` | scroll/plane clear caller |

## Implementation

At the established Z80 command-dispatch boundary, `cp $19` became `cp $25`. Command `0x00` still stops
and silences playback. Every other authentic command is consumed and safely ignored for now, so
unsupported SFX, voice, and control requests do not restart or interrupt active music. Cody's 511-byte
driver control flow, Timer B rearm, cartridge banking, stream decoder, intro/loop assets, FM6 reservation,
and the 68000 ring bridge are unchanged.

Files changed for the ROM source:

- `apps/rastan-direct/src/sound/z80_driver.asm`
- `tools/audio/compile_genesis_native_music.py`
- `tools/audio/verify_genesis_native_audio.py`

Durable evidence tooling added/updated:

- `tools/mame/scripts/audio015_arcade_command_timing.lua`
- `tools/mame/run_audio015_arcade_command_timing.sh`
- `tools/mame/scripts/audio015_native_runtime_gate.lua`

No PC080SN/PC090OJ semantic producer or chip tail was changed or removed; graphics legacy-removal fields
are not applicable to this audio-only build. The existing sound semantic cut retires only the PC060HA
nibble-send tail.

## Validation

Static/build validation:

- Z80 assembly: PASS, 511 bytes.
- Native stream verification: PASS, 798 intro ticks + 2402 loop ticks, 18,909 events.
- Boot guards and canonical gate: PASS.
- R1-S1 gameplay-entry gate: PASS, frame 569 plus 240 post-entry frames, zero exceptions.
- Seven production epochs: PASS.
- Variant family: PASS.

ORIGINAL ARCADE MAME:

- Established coin/Start/right route with stock invincibility cheat; player appearance frame 787.
- Ring sequence proves `$29` at Start, `$25` at appearance, no `$19` through frame 1800.

GENESIS NTSC MAME, Build 0488 normal ROM:

- Authentic retained commands published and consumed: `EF,04,29,25,1A,0B,0C...`.
- `$29` at frame 175 did not activate music.
- `$25` at frame 381 and the first active write occurred on frame 381.
- Later unsupported `1A/0B/0C` requests left `final_active=01`.
- 623 measured music periods versus 626 expected in the observed window (difference -3), 4,416 YM2612
  data writes, 922 PSG writes, 6,614 banked reads, zero bank mismatches, and no invalid Z80 PC/SP.
- Result: PASS. This proves native command generation/delivery and engine activation, not audible quality.

Existing project tools reused:

- canonical Ghidra exports and original disassemblies;
- generated address map;
- established arcade rope-route input/cheat method;
- existing AUDIO-015 Genesis native runtime gate;
- Makefile-owned release, canonical, gameplay-entry, epoch, and trace workflow.

New tooling created:

- one repository-owned ORIGINAL ARCADE command-timing script/wrapper.

Why new tooling was necessary:

- existing tools did not correlate original PC060HA/Z80-ring commands with the exact first-player-
  appearance frame. Ring-slot polling was needed because MAME DRC bypasses later memory taps; consumed
  slots retain bytes and therefore provide durable post-frame evidence.

## Limitations and USER MUST VERIFY

The command-to-track-name table for the original Z80 remains unresolved; this build translates the
proven live appearance/respawn intent to the one currently implemented native track. Multi-song dispatch,
SFX/voice playback, and PCM remain later AUDIO-015 work. Unsupported commands are represented and safely
consumed but not yet sounded.

USER MUST VERIFY on real NTSC Genesis hardware:

1. music is silent at Start/READY and begins when Rastan first appears;
2. death does not spuriously restart the track;
3. respawn starts/restarts Aggressive World at Rastan's reappearance;
4. the music is audible and remains stable while ordinary gameplay SFX commands are generated;
5. Continue/game-over/front-end transitions do not leave stuck notes or unexpected playback.

STOP status: no implementation blocker. Build 0488 awaits hardware acceptance; broader AUDIO-015 remains
open.
