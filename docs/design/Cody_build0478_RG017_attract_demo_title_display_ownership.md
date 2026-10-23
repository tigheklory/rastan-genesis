# Cody Build 0478 — RG-017 Attract Demo-to-Title Display Ownership

Agent/task: Cody, RG-017. Baseline: accepted Build 0473; immediate failing candidate: Build 0477.
Produced: Build 0478 from exact source `aab0eac15a9a332331cea5f773252a3010059dd8`, counter `477 ->
478`. Normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0478.bin`, SHA-256
`989842a323b2e27ad8461425271291c38840cc4e949bfcca160bf0124286634c`, size 2,739,896 bytes.

The semantic subsystem is Genesis presentation ownership. The retained `0x03AA54` native title
producer now requests READY only after final title planes, patterns, CRAM, SAT/HUD, scroll and dwell
state are prepared; fixed-order VBlank completion remains the sole display-enable owner. No new chip
tail is removed: this reuses the already-established native title cut, whose retired legacy tail is
the original PC080SN/PC090OJ title palette/logo/text realization. Retained attract control, timing,
scene selection, gameplay HOLD, READY, Continue, GAME OVER and publication logic remain.

Changed production file: `apps/rastan-direct/src/title_native.s`. Changed regression:
`tools/mame/scripts/rg004_frontend_probe.lua`. Inventory: 228 opcode sites, 86 shift replacements,
coverage `0x29CEB8`. Complete normal/`_d`/`_s`/`_do`/`_c`/`_full_hud`/`_invincible` family passes.
All seven filenames and hashes, full static provenance, exact control flow, and validation details are
recorded in `docs/design/Cody_RG017_attract_demo_title_display_ownership.md`.

Static proof used canonical Ghidra/disassembly, generated address map and current native source.
Genesis NTSC MAME validation passed canonical/boot/R1-S1/seven-epoch/native-title/final-life/READY/
Continue/re-entry and upgraded natural-attract visibility checks. The upgraded route fails 0477 with
display OFF/latch 1 and passes 0478 with one publication-gated VDP Reg1 ON, latch 0, exact CRAM and
zero unsafe ON writes. Rope is deterministic `795/795/795`, median `13,267.083 ms`, unchanged from
0477. No original-arcade MAME, BlastEm, Exodus, or real hardware was run for RG-017.

Hardware acceptance (2026-10-22): Tighe tested Build 0478 on real Sega Genesis hardware and
accepted the RG-017 behavior it was designed to correct. The immutable acceptance tag
`accepted/build-0478` points to exact ROM-producing source
`aab0eac15a9a332331cea5f773252a3010059dd8`, not to later regression or bookkeeping commits.

STOP: Build 0478 candidate and reports only; no unrelated optimization or audio work.
