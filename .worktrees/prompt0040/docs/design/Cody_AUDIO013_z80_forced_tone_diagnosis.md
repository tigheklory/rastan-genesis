# AUDIO-013 — Existing Z80 forced-tone diagnosis and repair

## Result and scope

AUDIO-013 established and corrected concrete defects in the already-existing forced-tone path. It
did not add another Z80 program, audio driver, playback mode, mailbox, telemetry system, PSG fallback,
music, SFX, PCM, FM6 DAC, or production channel arbitration. Tighe audibly verified the resulting
tone on real Genesis hardware in Builds 0482 and 0483. Build 0483 is the final documented candidate
because its initialization follows the repository's established Genesis bus/reset sequence and is
also fully observable in Genesis NTSC MAME.

Accepted main-game baseline remains Build 0478: normal ROM
`dist/rastan-direct/rastan_direct_video_test_build_0478.bin`, SHA-256
`989842a323b2e27ad8461425271291c38840cc4e949bfcca160bf0124286634c`, exact source
`aab0eac15a9a332331cea5f773252a3010059dd8`. Tighe's RG-017 hardware acceptance is recorded;
annotated tag `accepted/build-0478` dereferences exactly to that source. The local tag push was
attempted but the configured SSH remote rejected authentication (`Permission denied (publickey)`).
No acceptance-only build number was consumed.

Phase-0 review associated this work with KF-027, KF-055, KF-056 and OPEN-039 without contradicting
them. AUDIO-008/009/010/012, the prior forced-tone report, the native-audio architecture report,
RG-017 evidence, source, Makefile, build policy and issue ledgers were reviewed. OPEN-039 remains open.

## Existing path and static findings

The intended path is `_bootstrap` -> `z80_init_and_start` -> copy `z80_driver_start..end` from ROM to
Genesis Z80 RAM `$A00000` -> release/start Z80 -> Z80 writes YM2612 port 0 at `$4000/$4001`. The
forced loop deliberately ignores mailbox `$1FF0`; lack of mailbox consumption was not a defect.

Three defects were statically proven:

1. Build 0478 contained `z80_init_and_start` but no boot call, so the driver was never uploaded or
   started.
2. The byte-authored Z80 program used stale literal `CALL` targets after its routines expanded.
   The actual offsets were `set_patch=$004A`, `ym_write=$00C9`, `key_on=$00D9`,
   `key_off=$00E1`, `tone_a=$00E9`; the prior operands entered data or routine middles.
3. Initial attempts exposed the Genesis bus/reset requirement. A reset-held Z80 cannot acknowledge
   BUSREQ. The established repository SGDK sequence requests the bus and releases reset, waits for
   acknowledgement, uploads while BUSREQ halts the Z80, asserts reset, releases the bus, delays, and
   releases reset.

The final driver is 263 bytes at normal-ROM offsets `$29B57A..$29B680`. Its ROM SHA-256 is
`cfc2621a4ebc375bbc03d3f1edda8ee26d3a8c751949b286f07d47e354d578b0`.

## Runtime evidence and intermediate builds

Builds 0479 and 0480 are permanently consumed and rejected: the 68000 remained in the bus-acquisition
loop, Z80 RAM stayed zero, marker/heartbeat stayed zero, and no YM writes occurred. Builds 0481 and
0482 passed the main-game gates while narrowing reset/upload ordering. Build 0482 produced an audible
tone on Tighe's Genesis, but MAME's reset-asserted upload observation showed zero Z80 RAM and no YM
traffic. This is a meaningful emulator-versus-hardware sequencing difference, not grounds to override
the hardware observation. Build 0483 uses the standard bus-held upload order and works in both.

Observed in Genesis NTSC MAME for Build 0483:

- 264 68000 writes: all 263 driver bytes plus mailbox clear;
- Z80 RAM `$0000..$0106` byte-for-byte equals the ROM driver and has the same SHA-256 above;
- frame 2: Z80 PC `$00CF`, marker `$5A`, heartbeat `$25`;
- frame 10: Z80 PC `$00D6`, marker `$5A`, heartbeat `$62`;
- frame 60: Z80 PC `$00D7`, marker `$5A`, heartbeat `$A4`;
- YM writes begin with patch setup and continue through key-on; the capture cap recorded 256 writes;
- no Z80 overwrite/reset after initialization was observed.

This proves actual Z80 initialization and execution through `set_patch`, `key_off`, `tone_a`,
`key_on`, and the forced loop. Tighe's separate real-hardware listening result proves audibility for
Builds 0482 and 0483.

## YM2612 audit

The program addresses Z80-side YM2612 port 0 correctly at `$4000/$4001`, selecting channel 0 with
key register `$28`. Observed ordering is: algorithm/feedback `$B0=$07`; stereo output enabled
`$B4=$C0`; DT/MUL `$30/$34/$38/$3C=$01`; all operator TL registers
`$40/$44/$48/$4C=$00` (maximum operator level, not mute); attack
`$50/$54/$58/$5C=$1F`; sustain/release programming `$80/$84/$88/$8C=$0F`; key-off
`$28=$00`; frequency `$A4=$22`, `$A0=$69`; then key-on `$28=$F0`. The routine inserts address/data
spacing and a delay after each pair. Algorithm 7 makes all four operators carriers, pan enables both
outputs, frequency/block are valid, and the envelope remains capable of sustained output. No random
volume, pitch, channel, patch, or PSG change was warranted.

## Correction

- `apps/rastan-direct/src/boot/boot.s`: call the existing `z80_init_and_start` once during cold boot.
- `apps/rastan-direct/src/sound/z80_driver.s`: derive all Z80 `CALL` operands from routine labels,
  preserving the existing forced-tone program and markers.
- `apps/rastan-direct/src/sound/sound_comm.s`: use the correct live BUSREQ acknowledgement polarity;
  remove the invalid `$A14000` post-start writes (that address is TMSS, not a diagnostic port); and
  implement the established request/acknowledge, bus-held upload, reset/release/delay/start order.

Exact final ROM-producing source is `e0b122fca18d942a3ccd28ed246fdcee94192580`.

## Build 0483

Counter transition for the final candidate is `482 -> 483`. Every intermediate number remains
consumed. All seven files are 2,739,896 bytes:

| Variant | SHA-256 |
|---|---|
| normal | `aefad54c6494db7af916764c1e745edf1ef2b1c0f56db29d34ec7c16290202fb` |
| `_c` | `ae092475183118ab28ca30e586eb8c22ce9482b5e5880e5f203a22757ac86cfe` |
| `_d` | `84f085c3e303588faf6258e60278767220c6f0d64c04d203f93d70e04a15b442` |
| `_do` | `7ed3f75bf9596b7214bc8f5f36313376b5644c97c0522f4a41f04d5b2ffd124b` |
| `_full_hud` | `e81d2a3968c2241ff22fc96eadcb075519240101c90b7fdb6f561c3cffbf3530` |
| `_invincible` | `014af8a1b742dcb7f22b0d077b5d6494123a44e3390425b97d540fc7a156f934` |
| `_s` | `0a8abb47001a4f4e9bb2da05699ae01a22a2184f22e3def82dbfa5ab78d47633` |

Normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0483.bin`. No candidate acceptance tag
was created; accepted Build 0478 remains the main-game baseline.

## Validation and remaining work

Assembly/link, boot guards, canonical gate, R1-S1 entry (569 frames plus 240 post-entry), seven
production epochs, fixed 30-second trace, configured seven-ROM family, and invincibility-variant
verification pass with no CPU exception or boot hang. The established RG-017 natural attract route
passes at frame 7,216: second title visible, display ON, readiness zero, exact CRAM, one safe display
enable and zero unsafe enables. Thus the accepted Build-0478 display behavior is retained.

Hardware result from Tighe: **AUDIBLE FORCED TONE on Builds 0482 and 0483**. This accepts the narrow
Z80/YM2612 bring-up repair; it does not implement or accept production audio. Remaining work under
OPEN-039 includes arcade sequencing, production music/SFX, PCM/FM6 DAC voices, channel arbitration,
and the separately deferred deterministic original-MAME YM2151 capture-to-build integration.
