# AUDIO-014 — Permanent Genesis sound driver — BLOCKED

## Historical result

AUDIO-014 ended **BLOCKED** without a source change, numbered ROM, or build-number consumption. The
repository still contained only AUDIO-013's forced-tone bring-up driver. The blocker was not Genesis
Z80/YM2612 initialization: Build 0483 and Tighe's hardware test had already proved that foundation.

The missing prerequisite was original arcade semantic evidence. At the stop point, the maintained
Z80 C file still had declarations only; command `0x19` had not been proven through the song table and
channel descriptors; command `0x00` stop semantics, the timer/interrupt relationship, sequence loop
behavior, and music/SFX channel ownership had not been recovered sufficiently to choose a permanent
runtime representation without assumptions.

Consequently AUDIO-014 correctly produced no temporary VGM player, captured-song runtime, forced
Scene-1 trigger, fake PC060HA, placeholder SFX/PCM, second driver, or Build 0484. AUDIO-015 owns the
semantic recovery and any evidence-supported production implementation. This report preserves the
original AUDIO-014 result as BLOCKED; it does not relabel that work as AUDIO-015.

Build 0483 remained intact at
`dist/rastan-direct/rastan_direct_video_test_build_0483.bin`, SHA-256
`aefad54c6494db7af916764c1e745edf1ef2b1c0f56db29d34ec7c16290202fb`, exact source
`e0b122fca18d942a3ccd28ed246fdcee94192580`.
