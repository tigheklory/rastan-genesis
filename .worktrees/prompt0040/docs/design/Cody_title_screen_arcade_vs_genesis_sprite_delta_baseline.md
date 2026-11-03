# Cody - Title Screen Arcade vs Genesis Sprite-Delta Baseline

**Date:** 2026-07-01  
**Type:** Evidence / attribution only  
**Arcade set:** `rastan` / `Rastan (World Rev 1)`  
**Genesis baseline:** Build 0126, `dist/rastan-direct/rastan_direct_video_test_build_0126.bin`  
**Genesis SHA256:** `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921`  
**Evidence directory:** `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/`

## Phase 0

Relevant priors: `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, `docs/design/Cody_temp_sprite_sat_suppression_black_cover_test.md`, `docs/design/Cody_build0124_final_composite_black_cover_attribution.md`, `docs/design/Cody_pc090oj_blank_bitset_unmapped_guard_implementation.md`, `docs/design/Cody_pc090oj_object_ram_phase1_implementation.md`, `docs/design/Cody_build0123_pc090oj_transparent_pen_black_overdraw_evidence.md`, `docs/design/Andy_pc090oj_object_ram_to_genesis_sat_architecture.md`, and `docs/design/Andy_build0120_window_plane_coverage_design.md`.

High-rediscovery hazards: KF-011 frame ownership, KF-021 staged-vs-true-SAT hazard, KF-026/OPEN-024 PC090OJ coverage hazard, KF-032 raw hardware-write routing, KF-036 mapped-base discipline. No contradiction was detected.

Task classification: **EXTENDING OPEN-001 / OPEN-024** with evidence-only title-screen baseline/control. No source, spec, tool, Makefile, ROM, invariant, or build changes were made.

Open/Closed pre-check: OPEN-001 and OPEN-024 primary; OPEN-023 Window context only; OPEN-006 sprite palette context; OPEN-015 not touched; no issue opened or closed.

Build 0125 suppression context: acknowledged as a temporary diagnostic only. It proved the story-page black cover depends on Genesis sprite/SAT output, but it is not canonical and is not used as a baseline here.

Build 0126 canonical baseline: acknowledged. Build 0126 is byte-identical to Build 0124 and is the Genesis baseline for this audit.

Title-screen audit classification: baseline/control only. This task does not close the story-page black-cover attribution.

Story-page successor: still required separately: canonical Build 0126 story-page SAT-producing-chain evidence from PC090OJ object entry -> descriptor emission -> link chain -> staged SAT -> true SAT -> visible cover, plus post-SAT-DMA VDP-port writer watchpoints.

Window output: not treated as a leading hypothesis. The only writer check here is for title-screen raw SAT/VDP or PC090OJ bypass behavior.

Address mapping: `build/rastan-direct/address_map.json` was loaded. No arcade-to-Genesis arithmetic offset was used as proof. No arcade-vs-Genesis code-site correlation was required for the core evidence; Genesis writer PCs in the raw-writer summary are Genesis helper PCs identified from `apps/rastan-direct/out/symbol.txt`, not arcade-mapped sites.

## Evidence Artifacts

Primary artifacts:

- Arcade capture script: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/arcade/capture_arcade_title_series.lua`
- Arcade screenshot: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/arcade/arcade_0000.png`
- Arcade object dump: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/arcade/frame_060_pc090oj_d00000_0800.bin`
- Genesis capture script: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/genesis_build0126/capture_genesis_title_series.lua`
- Genesis screenshot: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/genesis_build0126/genesis_0000.png`
- Genesis mirror dump: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/genesis_build0126/frame_060_pc090oj_object_ram_ff674a.bin`
- Genesis staged SAT dump: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/genesis_build0126/frame_060_staged_sprite_sat_ff6104.bin`
- Genesis true VDP SAT dump: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/genesis_build0126/frame_060_true_vdp_sat_f800.bin`
- Reduced analysis JSON: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/title_sprite_delta_analysis.json`
- Reduced analysis Markdown: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/title_sprite_delta_analysis.md`
- Arcade decode CSV: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/arcade_frame060_pc090oj_decode.csv`
- Genesis mirror decode CSV: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/genesis_frame060_mirror_decode.csv`
- Genesis SAT decode CSV: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/genesis_frame060_sat_decode.csv`
- Annotated arcade screenshot: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/annotated/arcade_title_frame060_pc090oj_annotated.png`
- Annotated Genesis screenshot: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/annotated/genesis_build0126_frame060_sat_annotated.png`
- Sprite-cell contact sheet: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/tiles/title_relevant_pc090oj_cells_contact.png`

## PC090OJ Decode Source

The decode uses the local MAME reference only as documentation/reference, not copied runtime code:

- `docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp:184-193`: word0 flip/color, word1 Y, word2 code, word3 X, `code = word2 & 0x1fff`, signed X/Y wrap at `>0x140`.
- `docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp:196-202`: global flip when `m_ctrl & 1` is clear.
- `docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp:210-228`: transparent pen `0`.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:227-232`: `sprite_colbank = (sprite_ctrl & 0xe0) >> 1`, priority mask `0`.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:447-451`: screen size `320x256`, visible area `x=0..319`, `y=8..247`.

The title-frame sprite-cell exports use `build/regions/pc090oj.bin` for arcade source cells and `build/pc090oj_genesis.bin` for converted Genesis cells. Fully transparent/blank classification uses `build/pc090oj_blank_bitset.bin`.

## Title Frame Selection

Arcade:

- Emulator/tool: MAME `rastan` with local `roms/` path.
- Set: `rastan` / `Rastan (World Rev 1)`.
- Selected frame: MAME frame `60` from this capture.
- Screenshot: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/arcade/arcade_0000.png`.
- Why title: screenshot shows the RASTAN logo/sword, `1UP 00`, `HIGH SCORE 273100`, `2UP 00`, and `CREDIT 0`.
- Transition excluded: frame is already fully drawn and stable, not a story, high-score, item-scroll, or transition frame.
- Black cover: not present.

Genesis Build 0126:

- Emulator/tool: MAME Genesis driver with `dist/rastan-direct/rastan_direct_video_test_build_0126.bin`.
- Selected frame: MAME frame `60` from this capture.
- Screenshot: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/genesis_build0126/genesis_0000.png`.
- Runtime state: `%a5@(0)/(2)/(4) = 0/1/0`, credits `0`, watchdog/timer word `0x00C2`; this is the title/attract title state class.
- Why title: screenshot shows title-page lower text (`TAITO`, copyright, `ALL RIGHTS RESERVED`) and no story/high-score/item-scroll state; it corresponds to the title-screen state whose separated Plane A/B views were user-confirmed as complete.
- Transition limitation: this snapshot does not show the full final-composite logo/sword, but the runtime state and lower title text identify it as the corresponding title-screen state. Separated Exodus layer views remain the stronger visual proof that Plane A/B contain the complete title elements.
- Black cover: the story-page black cover is not present on this title frame. This audit is a title-screen sprite-delta baseline, not direct story-cover frame attribution.

## Arcade PC090OJ Title Audit

Arcade MAME frame `60` object-RAM summary:

| Category | Count |
|---|---:|
| object entries scanned | 256 |
| raw nonzero entries | 256 |
| nonzero code entries | 42 |
| blank/transparent nonzero-code entries | 6 |
| offscreen nonblank entries | 9 |
| MAME-drawable visible entries | 27 |
| visible entries intersecting top-score region | 27 |
| visible entries intersecting RASTAN logo/sword region | 0 |
| visible entries intersecting CREDIT region | 0 |

Visible arcade PC090OJ entries are all in the top-score strip. The RASTAN logo/sword title art is not PC090OJ output in this audit; it is PC080SN/tilemap art. `CREDIT 0` is not PC090OJ output in this audit; it is PC080SN/tilemap/text output.

Visible top-score PC090OJ entries:

| Entry | Code | X | Y | Words |
|---:|---:|---:|---:|---|
| 4 | `0x003B` | 136 | 0 | `0000 0000 003B 0088` |
| 5 | `0x003A` | 120 | 0 | `0000 0000 003A 0078` |
| 6 | `0x003C` | 152 | 0 | `0000 0000 003C 0098` |
| 7 | `0x003D` | 168 | 0 | `0000 0000 003D 00A8` |
| 8 | `0x003E` | 184 | 8 | `0000 0008 003E 00B8` |
| 22 | `0x002B` | 168 | 16 | `0000 0010 002B 00A8` |
| 23 | `0x002D` | 160 | 16 | `0000 0010 002D 00A0` |
| 24 | `0x0031` | 152 | 16 | `0000 0010 0031 0098` |
| 25 | `0x002C` | 144 | 16 | `0000 0010 002C 0090` |
| 28-33 | `0x002A` | 8..48 | 0 | six repeated entries for left score digits/spacing |
| 34 | `0x0039` | 64 | 16 | `0000 0010 0039 0040` |
| 35 | `0x0048` | 40 | 0 | `0000 0000 0048 0028` |
| 36 | `0x0046` | 56 | 0 | `0000 0000 0046 0038` |
| 37-42 | `0x002A` | 232..272 | 0 | six repeated entries for right score digits/spacing |
| 43 | `0x0039` | 288 | 16 | `0000 0010 0039 0120` |
| 44 | `0x0049` | 264 | 0 | `0000 0000 0049 0108` |
| 45 | `0x0047` | 280 | 0 | `0000 0000 0047 0118` |

Primary arcade answers:

1. Arcade title screen uses PC090OJ sprites: **YES**.
2. Visible arcade PC090OJ sprites on this title frame: **27**.
3. Top-score elements (`1UP`, `00`, `HIGH SCORE`, `273100`, `2UP`, `00`) are PC090OJ sprites in this frame.
4. `CREDIT 0` is not PC090OJ sprite output in this frame.
5. RASTAN logo/sword are not PC090OJ sprite output in this frame.

## Arcade Title-Sprite Tile Exports

Relevant PC090OJ code PNGs were exported under `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/tiles/`.

The key title top-score codes are:

- `0x002A`, `0x002B`, `0x002C`, `0x002D`, `0x0031`, `0x0039`, `0x003A`, `0x003B`, `0x003C`, `0x003D`, `0x003E`, `0x0046`, `0x0047`, `0x0048`, `0x0049`.

For each relevant code, both an arcade-source cell PNG and a Genesis-converted cell PNG are present, e.g.:

- `tiles/arcade_pc090oj_code_003B.png`
- `tiles/genesis_converted_pc090oj_code_003B.png`

Contact sheet:

- `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/tiles/title_relevant_pc090oj_cells_contact.png`

## Genesis Build 0126 Title Sprite/SAT Audit

Genesis Build 0126 frame `60` capture log line:

```text
CAPTURE 60 pc=071F5A s0=0000 s2=0001 s4=0000 credits=0000 timer2c=00C2 raw_nonzero=240 nonzero_code=4 active=0004 ctrl=0001 sprite_ctrl=0060 decoded=0100 zero=00FC blank=0000 unmapped=0000 offscreen=0000 drawable=0004 emitted=0004 dropped=0000 vdp_sat_dump=true
```

Genesis mirror/object summary:

| Category | Count |
|---|---:|
| mirror entries scanned | 256 |
| raw nonzero mirror entries | 240 |
| nonzero code mirror entries | 4 |
| blank-code skipped | 0 |
| unmapped-code skipped | 0 |
| offscreen skipped | 0 |
| drawable counter | 4 |
| emitted counter | 4 |
| dropped counter | 0 |

Genesis mirror visible candidates by PC090OJ semantics:

| Mirror entry | Code | Color | X | Y | Words |
|---:|---:|---:|---:|---:|---|
| 4 | `0x0001` | `0x30` | 0 | 0 | `0000 0000 0001 0000` |
| 14 | `0x0110` | `0x30` | 42 | 0 | `0000 0000 0110 002A` |
| 16 | `0x0080` | `0x30` | 0 | 128 | `0000 0080 0080 0000` |
| 17 | `0x0080` | `0x30` | 1 | 128 | `0000 0080 0080 0001` |

Final Genesis SAT state at the sampled boundary:

| Category | Staged SAT | True VDP SAT |
|---|---:|---:|
| raw nonzero SAT slots | 0 | 0 |
| reachable chain from slot 0 | `[0]` | `[0]` |
| reachable nonzero entries | 0 | 0 |
| visible reachable SAT entries | 0 | 0 |
| top-score SAT entries | 0 | 0 |
| logo/sword SAT entries | 0 | 0 |
| CREDIT-region SAT entries | 0 | 0 |

The true VDP SAT dump exists and matches staged SAT byte-for-byte:

- staged SAT SHA256: `9e132485d5107211de325a45e7917cbe3e4b5b9cde3e4ee91d7d2102317759ee`
- true VDP SAT SHA256: `9e132485d5107211de325a45e7917cbe3e4b5b9cde3e4ee91d7d2102317759ee`
- match: **YES**

Primary Genesis answers:

1. Genesis Build 0126 has four mirror/object candidates and counter-level emitted attempts on the title frame.
2. Genesis Build 0126 final staged SAT and true VDP SAT contain **zero visible/reachable sprites** at the sampled title boundary.
3. Genesis Build 0126 does not emit the arcade title top-score PC090OJ sprite set into final SAT on this frame.
4. Genesis Build 0126 does not show a Genesis-only visible final SAT sprite on this title frame.

Important interpretation: `emitted=4` is a scan/counter result, not proof of visible final SAT entries. The final staged/true SAT dumps are all zero at the sampled boundary.

## Arcade vs Genesis Comparison

| Category | Arcade MAME | Genesis Build 0126 |
|---|---:|---:|
| PC090OJ object entries scanned | 256 | 256 |
| raw nonzero entries | 256 | 240 |
| nonzero code entries | 42 | 4 |
| blank/transparent nonzero-code entries | 6 | 0 |
| offscreen nonblank entries | 9 | 0 |
| drawable/visible object candidates | 27 visible | 4 mirror candidates |
| descriptor-valid entries | N/A | 0 final descriptor-visible entries at sampled boundary |
| staged SAT entries | N/A | 0 nonzero |
| true/reachable SAT entries | N/A | 0 nonzero / chain `[0]` |
| visible sprites | 27 | 0 |
| sprites intersecting top-score region | 27 | 0 final SAT |
| sprites intersecting RASTAN logo/sword | 0 | 0 |
| sprites intersecting unexpected/phantom coverage region | 0 title-final visible | 0 title-final visible |

Answers:

1. Arcade title uses PC090OJ sprites: **YES**.
2. Arcade visible PC090OJ title sprites: **27**, all top-score strip.
3. Genesis title emits final visible SAT sprites: **NO** at this sampled title boundary.
4. Matching sprites: **0**.
5. Arcade-only / missing-on-Genesis sprites: **27** top-score sprites.
6. Genesis-only / unexpected final visible sprites: **0**.
7. Top-score elements are sprite-based in arcade: **YES**.
8. `CREDIT 0` is tilemap/text, not PC090OJ sprite output in this arcade frame.
9. RASTAN logo/sword is tilemap/PC080SN art, not PC090OJ sprite output in this arcade frame.

## Bidirectional Sprite Delta Check

Genesis-only suspect entries:

- Final SAT: none visible/reachable.
- Mirror-only candidates: entries `4`, `14`, `16`, `17` (`0x0001`, `0x0110`, `0x0080`, `0x0080`) are present in the Genesis mirror/counter path but do not appear in final staged/true SAT at the sampled boundary. Because they are not final visible SAT entries, they are **not classified as Genesis-only visible sprites**.

Arcade-only missing entries:

- Arcade entries `4`, `5`, `6`, `7`, `8`, `22`, `23`, `24`, `25`, `28..45` form the visible top-score strip and have no final Genesis SAT counterparts in Build 0126 frame `60`.
- Classification: **missing-on-Genesis final SAT** for the arcade title top-score sprite set.

Producer attribution:

- This audit did not trace producer PCs for the arcade top-score sprite entries. No producer address is claimed.
- No arcade-to-Genesis code correlation is used as proof here. Future producer tracing must use `build/rastan-direct/address_map.json` for every site.

## Raw Writer / Bypass Check

Genesis title-only writer watch artifacts:

- `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/genesis_build0126/title_raw_writer_watch.log`
- `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/genesis_build0126/title_writer_pc_summary.log`

Watch ranges:

- `HW_ADDRESS 0x00C00000..0x00C00007` VDP ports.
- `HW_ADDRESS 0x00D00000..0x00D007FF` raw PC090OJ hardware-address window.
- `Genesis-WRAM 0x00FF674A..0x00FF6F49` PC090OJ mirror.

Results over the title window:

- Raw PC090OJ hardware-address writes: **0**.
- PC090OJ WRAM mirror writes during frames 50-70: **0**.
- VDP port writes during frames 50-70: present and from Genesis helper/commit PCs only, including `0x07008E`, `0x0700B4`, `0x07020A`, `0x07021A`, `0x070224`, `0x070232`, `0x070240`, and `0x072188..0x072252` (inside `vdp_commit_sprites` / sprite commit helper region from `apps/rastan-direct/out/symbol.txt`).
- No title-window raw write to `HW_ADDRESS 0x00D00000..0x00D007FF` was observed.
- No title-window raw SAT/VDP bypass writer was proven. The observed VDP port writes are normal helper traffic, not Window-output evidence.

Classification: no title-screen raw PC090OJ bypass was observed. Any SAT-region issue in this pass would be a raw SAT/VDP writer issue, not a Window hypothesis; no such issue was proven here.

## Visual Artifacts

- Arcade annotated screenshot: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/annotated/arcade_title_frame060_pc090oj_annotated.png`
- Genesis annotated screenshot: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/annotated/genesis_build0126_frame060_sat_annotated.png`
- Sprite-cell sheet: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/tiles/title_relevant_pc090oj_cells_contact.png`
- Suspect-sprite sheet: not applicable; no Genesis-only final visible SAT sprite was found.
- Missing-on-Genesis sheet: the sprite-cell contact sheet covers all relevant missing arcade top-score codes.
- Raw dumps: `states/traces/title_screen_arcade_vs_genesis_sprite_delta_baseline_20260701_230410/raw_dumps/`

## Successor Task

If Genesis-only title sprites found: not applicable; no final visible Genesis-only SAT sprites were found.

If arcade-only missing sprites found: **YES.** Successor is to trace why the arcade title top-score PC090OJ entries do not reach Genesis final descriptor/SAT. The narrow path is: arcade top-score producer -> Genesis mirror write coverage -> mirror scan -> descriptor validity -> link chain -> staged SAT -> true SAT.

Regardless of title-screen result: story-page black-cover attribution still requires canonical Build 0126 story-page SAT-producing-chain evidence: PC090OJ object entry -> descriptor emission -> link chain -> staged SAT -> true SAT -> visible cover, plus post-SAT-DMA VDP-port writer watchpoints. This title audit does **not** close the story-page cover.

## Classification

Final classification: **Arcade-only title PC090OJ sprite set missing from Genesis final SAT.**

Confidence: HIGH for the title-frame delta: original arcade runtime frame `60` visibly uses 27 PC090OJ sprites for top-score text; Genesis Build 0126 frame `60` has matching title state but zero nonzero staged/true SAT entries.

Whether arcade title should have sprites: **YES**, top-score strip uses PC090OJ.

Whether Genesis emits extra sprites: **NO final visible/reachable SAT sprites** on this title frame. Genesis mirror-only candidates exist but are not visible final SAT.

Whether Genesis misses arcade sprites: **YES**, the arcade top-score sprite set is absent from final Genesis SAT.

Next recommended target: trace the top-score sprite producer path and Genesis mirror/descriptor/SAT validity for arcade entries corresponding to codes `0x002A`, `0x002B`, `0x002C`, `0x002D`, `0x0031`, `0x0039`, `0x003A`, `0x003B`, `0x003C`, `0x003D`, `0x003E`, `0x0046`, `0x0047`, `0x0048`, `0x0049`.

Do not implement yet: no fix is designed or implemented in this task.

## Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-024. OPEN-023, OPEN-006, and OPEN-015 context only.
- Closed issues touched: none.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: story-page SAT-producing-chain attribution, producer tracing/fix for title top-score sprites, D00298, Window, PC080SN changes.

## KNOWN_FINDINGS Impact

Option A: no `KNOWN_FINDINGS.md` update in this task. This is a baseline/control evidence pass; a durable finding should wait until the missing title top-score sprite producer path is traced and the mechanism is settled.

## STOP Status

STOP triggered: **NO**.
