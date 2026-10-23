# AUDIO-015 — Permanent Genesis audio architecture

## Selected boundary and runtime

The semantic cut is the complete retained 68000 PC060HA send routine at arcade `0x03F084` (24 bytes),
called by the existing dispatcher at `0x03A126`. A proper shift replacement changes that routine to
`JSR z80_write_command; RTS`. All original gameplay producers, the retained six-entry event queue,
dispatch order, command values, and timing remain above the cut. The retired tail is only the
PC060HA nibble transaction at hardware `3E0001/3E0003`.

The permanent bridge is a 16-entry Genesis Z80-RAM ring. The 68000 acquires BUSREQ, publishes one
byte, advances head, and releases the bus. It never polls for audio completion and performs no music
scheduling. A full ring drops the newest publication, preserving bounded latency and the retained
68000 queue's nonblocking policy.

The Z80 driver is real assembled Z80 code, 401 bytes, uploaded using the accepted AUDIO-013
bus/reset sequence. It owns YM2612 Timer B at approximately 61.09 Hz, consumes commands, implements
authentic `00` stop and `19` start/restart, writes YM2612/PSG, and reads cartridge-resident assets
through the Genesis 32 KiB Z80 bank window. The window bank changes only on a 32 KiB crossing. FM6
is never allocated to music and remains reserved for the future DAC/PCM service. The ring and driver
layout leave more than 7 KiB of Z80 RAM for future music state, SFX owners/priorities, restoration
state, and DAC buffering.

## Production data representation

One deterministic offline compiler consumes the canonical Aggressive World YM2151 capture, the
source track's loop metadata, and persisted Audio Composer profile
`music-test.r11.20261022T220736Z`. It reuses the maintained chip conversion to produce compact native
YM2612/PSG tick packets, then discards the VGM container. Runtime format is:

`event_count; {port0 register value | port1 register value | PSG byte}...`, once per original timer
tick, with `FF` stream termination. Intro and loop are separate symbols. The ROM never parses VGM,
never translates YM2151 registers, and never runs an arcade sound-board model. Generated original or
authored data remains uncommitted build output.

The saved Aggressive World decision has no explicit level overrides (`{}`), so none are invented.
It routes arcade channel 0 to PSG tone 1 and channels 1..5 to YM2612 FM1..5; saved profile semantics
drop channels 6 and 7 and reserve FM6 DAC. The browser renderer remains a provisional listening
source, so real-Genesis acceptance is required for the in-ROM result.

Generated bounds: 3,200 ticks; loop at tick 798; 18,910 native writes; maximum 133 writes in one
tick; 8,839-byte intro; 47,368-byte loop; 56,207 bytes total. Publication is one bounded byte plus
BUSREQ acquisition. Normal scheduler load is proportional only to that tick's authored native writes;
the worst packet is bounded by 133. The timer delta from arcade is about +0.09%, with no gameplay or
VBlank dependence.

## Permanent extension contracts

- The command byte namespace and ring remain valid for the full original music/SFX command set.
- Music playback state is independent of hardware ownership, so future SFX can preempt chosen
  channels while music pointers continue, then mark patches/pitch/volume dirty for restoration as
  the arcade does.
- FM6 is reserved and DAC disabled until the real MSM5205 samples and commands are compiled; no
  placeholder samples are present.
- Additional songs use the same generated intro/loop representation and command dispatch table; no
  scene-specific trigger or second engine is required.
- The compiler is reproducible from user-supplied source assets and the persisted profile. The
  generated binary music is deliberately not committed.

## Acceptance boundary

Automated Genesis validation can prove command publication, Z80 consumption, timer progress, native
chip writes, loop pointer transition, gameplay entry, and absence of CPU/graphics regressions. It
cannot establish audible quality on Tighe's Genesis. Any Build 0484 produced from this design remains
a candidate with Build 0478 as the accepted gameplay baseline and no acceptance tag.
