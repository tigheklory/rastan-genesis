# PROMPT RG-004 — Cody — Complete 0464 Front-End Presentation

## Result

RG-004 resumed the interrupted investigation without repeating the completed Build-0464 acceptance
lock. It proves three independent first-wrong stages behind the remaining frontend defects and
implements a bounded native lifecycle correction for each. The current accepted baseline remains
Build 0464 until the single authorized Build-0465 candidate passes the complete automated gate and
Tighe accepts its normal ROM on real Genesis hardware.

## Build-0464 acceptance lock and resume state

The existing immutable tag `accepted/build-0464` peels to exact ROM-producing source
`e535868192c54ee296b3230c7835c122ab018bb3`. Its accepted normal ROM is
`dist/rastan-direct/rastan_direct_video_test_build_0464.bin`, SHA-256
`744603425e7e9df9abd1378db07e973c691c4f7cd9359446e0c6ed1730f48302`. Acceptance-only
bookkeeping commit `a19250f3` and counter 464 were already present and were not recreated, amended,
or rebuilt.

The interrupted `tools/mame/scripts/rg004_frontend_probe.lua` was preserved and completed narrowly.
It observes only the existing zero-input final-life route or the bounded no-input attract route. It
does not navigate gameplay, create a save state, or provide a general instruction trace. Concurrent
Andy audio/Z80/tooling/report changes were detected, left unstaged and unmodified, and do not overlap
the RG-004 ROM-producing files.

## READY palette: first wrong stage

The completed static chain begins at original READY state 9. Function `0x056128` invokes retained
palette producer `0x059AD4` for banks `0x04`, `0x05`, `0x33`, and `0x43`. Bank 4 uses source
`0x05649E`, row 0. Banks 5, 0x33, and 0x43 use source `0x0564FE`, row 0; the latter two therefore
carry the same 16 source colors.

The first wrong native operation was `genesistan_palette_hook_59ad4`, before staging. Its accepted
policy handled banks below 4 and special bank 0x33, but rejected 4, 5, and 0x43 before it computed a
staging destination. Build-0464 runtime evidence separately proved that every staged line matched
actual VDP CRAM, so dirty publication was not the defect.

The correction retains the original four loads while compressing the duplicate source identities
into available Genesis CRAM: bank 4 to Line 0, bank 5 to Line 1, and banks 0x33/0x43 to Line 3. The
scene-0 PC090OJ selector table likewise maps sprite banks 0x33 and 0x43 to Line 3. No screenshot
colors or `Test.json` decisions are changed. Registry decision
`PAL-FRONTEND-READY-RETAINED-BANKS-001` records the source identity, consumers, and realization.

## Continue presentation: first wrong stage

The original Continue source at `0x05AC72` contains 120 panel cells and 83 distinct codes. The prior
static proof already established unique LUT and scene-0 residency coverage for all 83; RG-004 did not
repeat that enumeration.

The corrected VDP-port terminal probe followed representative panel cells end to end. At cell
`0x0492`, staged and actual Plane-B words were both `0x2158`, final slot `0x0158`, and the resident
pattern checksum was `0x00B6` in both views. At `0x0493`, both words were `0x2159`, slot `0x0159`,
pattern checksum `0x8992`. At `0x06D7`, both words were `0x21A8`, slot `0x01A8`, pattern checksum
`0x5333`. Across the full panel there were 83 distinct staged words, 83 distinct actual words, and
zero name mismatches. The result remained unchanged 120 frames into Continue. All four staged CRAM
lines matched actual CRAM.

The first wrong stage was outside the panel and earlier in the lifecycle: all 1,928 Plane-B cells
outside the 12x10 Continue block still contained nonblank gameplay names. Staging and actual VDP
Plane B matched exactly there as well (for example cells `0x0000..0x000F` began at
`0x41BB..0x41CA`). Thus the VDP correctly published stale final names, which the newly restored
scene-0 residency then reinterpreted around the valid Continue panel. This is not a bad name-word
translation, tile slot, pattern upload, plane base, or later overwrite.

The correction makes the accepted `genesistan_frontend_presentation_reset` perform the finite final
Plane A/B name-table clear before retained frontend producers repopulate them. The `0x056440` wrapper
uses the shared owner-only portion and retains its original scroll-zero-then-plane-clear ordering, so
each path clears exactly once. Pattern VRAM is not cleared, no Continue-only renderer is added, and
the original Continue producer remains authoritative.

## Attract-demo exit and second frontend palette

One authorized bounded no-input Build-0464 route reached demo gameplay, natural demo death, and the
second title at frame 7,219. Neither mapped `0x056440` nor mapped `0x03AD4C` executed during the
demo-death return. Instead, retained control switched scene 1 to scene 0 at frame 7,204 while PC was
`0x0757D6`, inside existing `load_scene_tiles`, via its source-driven scene selector. That is the
third established ownership boundary; no new attract state machine or hook is required.

At first title, Lines 0/2 were the original frontend base colors and Line 3 was empty. At second
title, native title Line 1 was again correct, but Lines 0/2/3 remained the Test/gameplay values.
Actual terminal CRAM exactly matched staging. The first wrong stage is therefore scene-0 activation:
`load_scene_tiles(0)` restored pattern residency and owner IDs but omitted the frontend base palette.

The correction offline-generates a 64-word frontend base palette from original cold-start sources
`0x04EAF6` (Line 0), `0x04EB16` (Line 1), and `0x04FE62` (Line 2), with semantic-empty Line 3.
`load_scene_tiles(0)` copies it once to staging and arms the existing palette publisher. The generated
Line 0 and Line 2 reproduce the accepted first-title values byte-for-byte. Subsequent retained title,
READY, story, BEST-5, Continue, and item producers remain free to overwrite their owned lines.
Registry decision `PAL-FRONTEND-SCENE0-BASE-001` records this lifecycle ownership.

## Item-screen consequence

The existing native item contract remains unchanged: bank 0x30 uses Line 2, bank 0x33 uses Line 3,
and item entry reloads bank 0x33 row 4 into Line 3. Later post-ARMATURE icons use Line 2. The observed
later-item corruption is therefore a consequence of stale gameplay Line 2 surviving demo re-entry;
restoring the original frontend base at scene-0 activation supplies the correct precondition. No
independent post-ARMATURE writer defect was proven, and no accepted item mapping was modified.

## Root classification

- READY versus Continue: **INDEPENDENT**. READY loses three retained palette writes before staging;
  Continue faithfully publishes stale plane names outside its correct 12x10 panel.
- READY versus attract re-entry: **INDEPENDENT**. READY is unsupported-bank routing in a retained
  writer; attract re-entry omits base-palette restoration at scene-0 ownership activation.
- Continue versus attract re-entry: **INDEPENDENT**. One is final name-table lifecycle state; the
  other is CRAM lifecycle state. They share a semantic frontend boundary, not a first-wrong operation.

## Semantic cut and removed chip tail

The cut remains the established retained frontend lifecycle/scene-ownership boundary. Arcade state,
timers, inputs, credits, death choice, attract dispatch, Continue decisions, and frontend content
producers stay authoritative. Native helpers perform finite operations and return: select final
scene-0 residency, stage the original base CRAM lines, clear final Genesis name tables at the explicit
frontend reset, and translate retained READY palette intent.

The removed tails remain the PC090OJ object-RAM parking execution and PC080SN C-window/name-RAM
execution below their previously accepted semantic cuts. RG-004 adds no chip RAM, shadow map,
full-map projection, per-frame reset, scheduler, fallback, NOP/RTS bypass, or screenshot renderer.

## Implementation

Production changes are bounded to:

- `scene_load.s`: one scene-0 base-palette restore plus shared owner/full-reset entry points;
- `palette_hooks.s`: retained READY bank translation plus scene-0 0x33/0x43 SAT routing;
- `pc090oj_hooks.s`: retain the `0x056440` scroll-zero-then-plane-clear contract while reusing the
  owner-only handoff;
- `gen_native_title.py` and `verify_native_title.py`: generate and verify the original-source
  frontend base palette;
- the Makefile: declare the generated palette dependency and verifier input;
- `rastan_direct_remap.json` and `palette_decisions.json`: keep authoritative policy consistent.

The generated palette is 128 bytes. Static verification reproduces the accepted first-title Line 0
and Line 2 words exactly; Line 3 is zero until retained frontend producers author it. Assembly of all
three changed source objects passes. The generated direct PC090OJ selector verifies all 512 mapping
combinations and 16,777,216 SAT word-2 combinations with zero mismatches, including scene-0 bank
0x43 -> Line 3. Native-title generation verification passes.

## Build 0465, Build 0466, and validation

The first authorized attempt reached postpatch verification but failed before numbered publication:
the existing attract Plane-B structural gate still required the `0x056440` plane-clear call in its
original wrapper, while the initial correction had moved it into the shared reset. The Makefile's
`.DELETE_ON_ERROR` removed the rolling ROM before it could be preserved or hashed. Build 0465 is
therefore **REJECTED / NOT ACCEPTED / artifact missing** and permanently recorded as consumed; it
was not reused. The correction split the shared owner-only handoff from the full reset and restored
the original wrapper's scroll-zero-then-plane-clear order. The unchanged established verifier then
passed.

ROM-producing source is `3bd0166e7df19553ba8066f24d1f47b7cb2d5ea5` (with the main RG-004
implementation in parent `eb5a9a2a`). The passing candidate is Build 0466:

- normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0466.bin`;
- SHA-256: `9ca337969058d206588d886dec6f38f6f2b73e3648c46ef25a01ae6a1e27c4f2`;
- size: 2,739,896 bytes;
- counter: 466;
- counter transition: accepted 464 -> rejected/missing 465 -> candidate 466;
- canonical replacement inventory: 228 byte-neutral opcode sites plus 77 shift replacements;
  expected Genesis coverage `0x29CEB8` bytes;
- complete normal, `_d`, `_s`, `_do`, `_c`, `_full_hud`, and `_invincible` family present and
  configuration-verified.

Validation results:

All runtime checks below used the MAME Genesis/Genesis NTSC driver. Original-arcade meaning was
established from the canonical existing Ghidra/disassembly evidence and retained ROM data; RG-004
did not create another arcade gameplay trace.

- canonical gate, pre/post boot guards, gameplay-entry, seven-epoch, selector relocation, native
  title/HUD/item/BEST-5, palette-family, DMA-boundary, attract Plane-B, and configured seven-ROM
  family checks: **PASS**;
- final-life semantic verifier: **PASS**, arcade `0x03A3C0` maps to `0x03B320`, for normal and all
  generated variants;
- fixed30 Genesis NTSC trace: **PASS**, 1,798 frames, zero live FG C-window writes;
- existing `final_life_zero_input_regression`: **PASS**, GAME OVER transition reached at frame
  3,585 after three death entries, tuple `2/4/6`, zero lives;
- bounded RG-004 Continue probe: **PASS**, tuple `2/4/8`, all 83 names and resident patterns match
  actual VDP data, zero nonblank outside-panel cells, all staged CRAM equals actual CRAM;
- bounded no-input attract route: **PASS**, natural demo/death and second title reached at frame
  7,222; second-title Lines 0/1/2/3 equal first-title Lines 0/1/2/3 byte-for-byte and actual CRAM;
- established `_invincible` rope benchmark: **PASS**, `798/798/798`, median 13,317.147 ms,
  deterministic **YES**.

The zero-input route proves READY progression, Continue entry, and unchanged GAME OVER control flow.
The clean frontend SAT construction and its publication verifier remain intact. Automated evidence
cannot establish final visual correctness or replace Tighe's real-hardware acceptance.

## Hardware acceptance — accepted

Tighe accepted normal Build 0466 on real Sega Genesis hardware and reported that it runs great; the
RG-004 frontend fixes are accepted. Immutable annotated ref `accepted/build-0466` peels to exact
ROM-producing source `3bd0166e7df19553ba8066f24d1f47b7cb2d5ea5`. The normal-ROM SHA-256 was
reverified as `9ca337969058d206588d886dec6f38f6f2b73e3648c46ef25a01ae6a1e27c4f2` before
subsequent production work began. READY, Continue, GAME OVER, first title, attract demo, second title,
story, BEST 5, scrolling-item palette continuity, final-life behavior, and frontend SAT cleanup are
now accepted regression locks.

Reward/death Palette Composer production integration, Demon palette, 1UP/score geometry, audio,
Phase D, and Phase E remain outside RG-004.
