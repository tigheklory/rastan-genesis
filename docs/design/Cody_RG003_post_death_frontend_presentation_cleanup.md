# PROMPT RG-003 — Cody — Post-Death / Front-End Presentation Cleanup

## Result

RG-003 proves and corrects a shared presentation-ownership omission after gameplay. Build 0462
retained the arcade control/state transitions, plane clears, text writers, and block producers, but
its native replacements did not restore the scene-0 pattern/palette owner and did not replace the
persistent gameplay SAT at the arcade-defined teardown boundaries. The first build attempt, 0463,
was preserved as a canonical-gate rejection because the verifier's duplicated opcode-site count was
not updated. Build 0464 is the passing candidate. Real-Genesis visual acceptance remains Tighe's.

## Accepted Build-0462 lock

Before RG-003 implementation, Tighe's hardware acceptance was recorded, OPEN-038 was moved to
CLOSED-038, and annotated tag `accepted/build-0462` was created at exact ROM-producing source
`faf556241a4f1666245d3424dfa41a5c248fa85e`. The accepted normal ROM SHA-256 was reverified as
`dede71fef20f40a829b07065dff3c3afd31c9f0d6623c30ba42caa7c7c7e5526`. The lock was committed
separately as `44d31fa8`.

## Arcade transition semantics

Static provenance used the existing Ghidra exports and raw disassembly; no new decompilation or
gameplay route was created.

- Normal death -> READY is controlled by arcade function `0x055DDC`. State 8 calls `0x056440`,
  state 9 loads the next presentation palette and clears the PC080SN maps, state 12 clears the maps
  again and emits ROUND/READY, and state 13 eventually calls `0x056440` again before retained
  gameplay re-entry.
- Final death -> Continue remains in the terminal controller rooted at `0x03A1C4`. The Continue
  setup at `0x03A304` selects its palette/plane block and emits the four retained text groups before
  entering the countdown phase.
- Continue -> GAME OVER uses setup `0x03A420`: the retained `0x05A442` presentation block, text IDs
  `0xBA` and `8`, and the 160-tick dwell remain authoritative.
- GAME OVER -> title exits terminal phase 6 into outer frontend state 0. The retained frontend clear
  `0x03AD4C`, plane clear path, and one-shot native title producer establish the next display.
- Title -> king/story performs the retained frontend clear, then the `0x05A3DE` story block and text
  IDs `17,63..70`.
- King/story -> BEST 5 performs the retained plane clear, ranking builder, and text IDs `60..62`.

The static scene-0 preload manifest already covers the relevant original PC080SN sources:
`0x5B0B2`, `0x5A7DA`, `0x5AC72` (Continue), `0x5AF62` (story), and `0x5AD62`
(GAME OVER/stage presentation). The content existed; ownership was not restored after gameplay.

## First wrong native stage

The first common divergence is at the arcade-defined teardown, before READY or later frontend
producers draw:

1. Original `0x056440` parks 72 PC090OJ records from `D00170` and calls `0x0561A0` to reset scroll
   and clear both PC080SN maps. Its Build-0458 native replacement cleared item/scroll/planes, but did
   not retire gameplay SAT ownership or restore scene-0 patterns/palette ownership.
2. Original `0x03AD4C` clears the front-end PC090OJ record bands for its eight lifecycle callers.
   The former Genesis replacement was an early `RTS/NOP`, based on the incorrect assumption that a
   later per-frame rebuild made the clear irrelevant.
3. Actual VDP SAT persists until DMA publication. Clearing arcade actor storage or software staging
   alone therefore cannot remove the prior gameplay list. In non-gameplay scene handling, the
   existing FRONTEND_FULL package is the bounded clean SAT representation: 30 HUD records, link
   `0..28 -> 1..29`, record 29 terminator link 0. Activation fills both staging banks, sets
   `pc090oj_emitted_count=30`, and arms `pc090oj_sat_frame_ready`/dirty for VBlank publication.
4. `genesistan_current_scene_id` was left at gameplay (`1`). That preserved gameplay's reclaimed
   pattern slots and palette-line gating. Retained Continue/GAME OVER/story/READY name words then
   referenced the wrong resident patterns, while frontend palette writes could remain under the
   gameplay ownership rule. This explains the random/green tiles and wrong colors without changing
   any Palette Composer decision.

Thus stale actors, corrupt tiles, and wrong palette share one missing presentation-owner handoff,
expressed at two independent retained arcade teardown entry points.

## Semantic cut and removed chip tail

The cut is the retained arcade lifecycle call after the arcade program has chosen teardown/new-scene
presentation, but before retained plane/text producers populate that presentation. The removed chip
tail is the PC090OJ object-RAM parking/fill execution at `0x03AD4C` (both `D00000`/`D00170` loops and
their `0x03AD44` writer), plus the already-retired PC090OJ record clear inside `0x056440`. Arcade
game state, timers, input, credits, Continue choice, READY selection, and all later plane/text/block
production remain above the cut.

## Implementation

ROM-producing source commit: `e5358681` (`Restore frontend presentation ownership`).

- `scene_load.s` adds `genesistan_frontend_presentation_reset`. Once per arcade teardown it reloads
  the existing generated scene-0 residency, thereby selecting scene-0 sprite palette mapping and
  releasing gameplay palette ownership. It then deactivates/reactivates FRONTEND_FULL so both SAT
  staging banks are rebuilt and the clean list is published by the normal VBlank owner.
- `pc090oj_hooks.s` invokes the helper at retained `0x056440`, before its existing scroll and final
  Plane A/B clear consequences.
- `rastan_direct_remap.json` replaces the old `RTS/NOP` at `0x03AD4C` with a proper 4-to-8-byte
  shift-table call/return cut. Reflow-affected validated branch bytes were updated from generated
  evidence.
- Both canonical verifier constants now reflect moving one site from byte-neutral
  `opcode_replace` to `shift_replacements` (`229 -> 228`).

This is not a scene manager, state machine, full-VRAM reset, arbitrary display blank, per-frame
sprite hide, or screenshot-specific patch. `load_scene_tiles(0)` uploads only the established
scene-0 manifest at the retained lifecycle event. Plane contents remain arcade-owned.

`Test.json`, Andy's RG-001 mappings, and palette decisions were not modified.

## Build numbering

- Build 0463 was generated and permanently recorded as rejected:
  canonical FAIL (duplicated verifier count still 229), gameplay-entry PASS, epoch PASS. It was not
  renamed or reused. Preserved SHA-256:
  `c8ab7d370fafab407b2ad8ba806296fefc82de813d21ca15867def1dfc8c6031`.
- Build 0464 is the passing candidate. Normal ROM:
  `dist/rastan-direct/rastan_direct_video_test_build_0464.bin`, 2,739,896 bytes, SHA-256
  `744603425e7e9df9abd1378db07e973c691c4f7cd9359446e0c6ed1730f48302`.
- Counter: `464`. The complete canonical/`_d`/`_s`/`_do`/`_c`/`_full_hud`/`_invincible` set was
  generated and verified.

## Validation

- Assembly, generated-assets checks, boot guards, 77-site shift reflow, canonical gate, gameplay
  entry, seven-epoch gate, native title/HUD/item/BEST-5 checks, palette-family check, configured
  family check, and invincibility check: PASS.
- Final-life semantic verifier: PASS in all built variants; normal target maps
  `0x03A3C0 -> 0x03B320`.
- Fixed 30-second Genesis NTSC validation: PASS, 1,798 frames, no live C-window write.
- Existing normal-ROM `final_life_zero_input_regression`: PASS at 3,580 frames; three death entries;
  reached terminal tuple outer/phase/subphase `2/4/6` with zero lives.
- Existing deterministic `_invincible` rope benchmark: PASS, `798/798/798`, median
  `13,317.147 ms`, deterministic YES (unchanged from Build 0462).
- New gameplay routes, manual gameplay, save states, and broad traces: none.

Automated validation proves state progression and bounded publication contracts, not visual
correctness. It does not substitute for Tighe's real-hardware comparison.

## Hardware acceptance required

Build 0464 is pending Tighe's normal-ROM real-Genesis check for clean death->READY, intended-only
Continue Rastan, GAME OVER sword/bones, title, king/story, and BEST-5 presentation with correct
patterns/palettes and no stale gameplay actors. OPEN-033, OPEN-034, and OPEN-035 remain open until
that acceptance. Reward/death palette integration, Demon palette, 1UP/score geometry, Phase D, and
Phase E remain deferred.
