# Cody — Runtime Report: Build 0091 OPEN-016 Part 2 Immediate Crash

**Date:** 2026-06-19  
**Type:** Runtime video evidence extraction/reporting only  
**Video:** `states/screenshots/build_91/build_91.mp4`  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0091.bin`  
**ROM SHA256:** `942dcb1aefebec7cbd808d016ff41f4bc22ec9ffd92c98be8a423297a56590cc`  
**Scope:** 30 FPS screenshot extraction and visible PC/crash-screen reporting. No source/spec/tool/build/ROM changes. No runtime probing beyond the provided video.

## Phase 0

Classification: **EXTENDING / evidence extraction for OPEN-016 Part 2**. Relevant priors: KF-028 (input-shim/title-text arc), KF-013 (text dispatch inside VBlank), KF-010 (FG maps to Plane A), OPEN-016 (active), OPEN-015 (crash-handler reliability caveat), OPEN-001 (rendering context). No contradiction detected.

## Source Video

- Resolution: `5118x1398`
- Framerate: `30 FPS`
- Duration: `11.900 s`
- Extracted frames: `358`
- Frame directory: `states/screenshots/build_91/build_91_30fps/`
- Representative crops: `states/screenshots/build_91/build_91_30fps/representative/`
- Machine-readable PC artifacts:
  - `states/screenshots/build_91/build_91_30fps/pc_value_summary.json`
  - `states/screenshots/build_91/build_91_30fps/pc_run_segments.json`
  - `states/screenshots/build_91/build_91_30fps/pc_decode_cluster_summary.json`
  - `states/screenshots/build_91/build_91_30fps/pc_cluster_contact_sheet.png`
  - `states/screenshots/build_91/build_91_30fps/crash_transition_contact_sheet.png`

## Timing Summary

- Initial emulator/file-open/transition frames: `001-102` (`0.000s-3.367s`), PC `0xFFFFFFFF`.
- First actual ROM-running frame: `103` (`3.400s`), PC `0x00000306`.
- First sampled arcade/runtime body PC: `108` (`3.567s`), PC `0x0003B0E0`.
- First sampled service/helper-region PC: `114` (`3.767s`), PC `0x00070624`.
- Pre-crash transition: frames `116-117` (`3.833s-3.867s`), PC `0x000005C6`.
- First readable crash report: frame `118` (`3.900s`).
- First stable crash-halt PC: frame `121` (`4.000s`), PC `0x00000518`.
- Stable crash halt persists through final frame `358` (`11.900s`).

**Immediate-crash measurement:** from first ROM-running frame (`3.400s`) to first stable crash-halt PC (`4.000s`) is approximately `0.600 s`.

## PC Value Summary

| PC address | Frames | Share |
|---|---:|---:|
| `0x00000518` | 238 | 66.48% |
| `0xFFFFFFFF` | 102 | 28.49% |
| `0x0003B0E0` | 6 | 1.68% |
| `0x00000306` | 5 | 1.40% |
| `0x000005C6` | 5 | 1.40% |
| `0x00070624` | 2 | 0.56% |

## Time-Ordered PC Run Segments

| Frames | Time range | PC |
|---|---|---|
| 001-102 | 0.000s-3.367s | `0xFFFFFFFF` |
| 103-107 | 3.400s-3.533s | `0x00000306` |
| 108-113 | 3.567s-3.733s | `0x0003B0E0` |
| 114-115 | 3.767s-3.800s | `0x00070624` |
| 116-120 | 3.833s-3.967s | `0x000005C6` |
| 121-358 | 4.000s-11.900s | `0x00000518` |

## Hook / Helper PC Observability

Requested hook/helper PCs checked against 30 FPS samples:

- `0x0003BD48` — not observed
- `0x00070B8E` — not observed
- `0x00070BC8` — not observed
- `0x00070BD4` — not observed
- `0x000707BC` — not observed
- `0x00070800` — not observed
- `0x00070794` — not observed
- `0x0007079E` — not observed

Nearby helper-region sample observed: `0x00070624` for 2 frames. The absence of exact hook PCs in a 30 FPS video does **not** prove they did not execute; it only means they were not sampled visibly in this video.

## Crash Screen Summary

The visible crash screen shows:

```text
==== RASTAN CRASH =========================
EXCEPTION: ADDRESS ERROR        VECTOR: C8
FAULT PC: 00000116        SR: 013C
FAULT ADDR:00000196
...
DEST_BG:00000610      DEST_FG:00000638
BG_DIRTY:00000692     FG_DIRTY:000006BA
PAL_D:0C      TILE_D:26    FRAME:073A
...
HALTED -- BUILD 0038
```

The screenshot/visible crash output again matches the OPEN-015 cursor-offset artifact pattern: `VECTOR=C8`, `FAULT PC=00000116`, and `FAULT ADDR=00000196` are screen-position-looking values, not reliable crash-record values.

### Reliability Caveat

Per OPEN-015, treat the following as visible text only until WRAM is checked: `VECTOR`, `FAULT PC`, `FAULT ADDR`, `SR`, `D0-D7`, `A0-A6`, `SP`, `USP`, `DEST_BG`, `DEST_FG`, dirty flags, `PAL_D`, `TILE_D`, and `FRAME`.

Reliable screenshot evidence:

- Exception name string: `ADDRESS ERROR`.
- Stack dump region is visible as crash-screen evidence, but the video crop does not preserve the full-width longwords legibly enough for a no-guess transcription. Do not promote a stack-dump interpretation from this report alone.
- The full stack dump and real crash values should be recovered from WRAM, not from the displayed numeric fields.

Required WRAM verification addresses:

- `0xFF6804` = `CRASH_STACKED_SR` word
- `0xFF6806` = `CRASH_STACKED_PC` long
- `0xFF6854` = `CRASH_FAULT_ADDRESS` long
- `0xFF6816..0xFF684E` = saved register block, with OPEN-015 saved-register caveat

## Comparison To OPEN-016 Part 1 Capture

Prior OPEN-016 Part 1 capture (`states/screenshots/build_unknown_2026-06-18_loop_report.md`) reported:

- First actual ROM execution around frame `111` / `3.667s`.
- Stable title/attract execution for roughly 45 seconds.
- Crash only after later state progression/input.
- PC cadence dominated by Level-6/service helper and arcade main-loop PCs.

Build 0091 differs materially:

- First actual ROM execution appears at frame `103` / `3.400s`.
- Stable crash halt begins at frame `121` / `4.000s`.
- No stable title/attract loop is visible before the crash.
- The clip does not visibly sample the new glyph hook path, but the crash occurs almost immediately after the runtime reaches post-start execution.

## Regression Assessment

**Likely regression introduced by Build 0091 / OPEN-016 Part 2 hook: YES as an operational comparison, unresolved as a mechanism from video alone.**

Basis:

- Build 0091 SHA matches the OPEN-016 Part 2 ROM.
- Prior Part 1 capture with SHA `c9fab1b4...` reached a stable title/attract window.
- Build 0091 crashes within about `0.600 s` of first ROM-running frame with no button input reported.

Limit:

- 30 FPS video does not show exact execution at `0x3BD48` or `0x70B8E`.
- The real fault PC/address cannot be read from the on-screen numeric fields because OPEN-015 is still active.
- Mechanism requires WRAM crash-record verification and then static review against the recovered fault PC/address.

## Recommended Next Step

1. In Exodus memory viewer at the halted crash screen, dump the WRAM crash record:
   - `0xFF6804` word
   - `0xFF6806` long
   - `0xFF6854` long
   - `0xFF6816..0xFF684E` register block
2. Use the real `CRASH_STACKED_PC`, `CRASH_FAULT_ADDRESS`, and IR/SSW context to decide whether the new glyph-renderer hook caused a bad write/return/register state.
3. Then run a bounded static review of `genesistan_hook_glyph_renderer_3bd48` and its helper call path (`0x70B8E`, `0x70BC8`, `0x70BD4`, `0x707BC`, `0x70800`, `0x70794`, `0x7079E`).

## Scope Discipline

- Source/spec/tool/Makefile changes: NO
- Build run: NO
- ROM modified: NO
- Runtime probing beyond video analysis: NO
- Bookmark cycle: NO
- Issues opened/closed: NONE
- KNOWN_FINDINGS updated: NO

## Open / Closed Issues Impact

- Open issues touched: OPEN-016 (context/evidence), OPEN-015 (crash reliability caveat), OPEN-001 (rendering context)
- Closed issues touched: NONE
- New issues opened: NONE
- Issues closed: NONE
- Issues intentionally deferred: Start-C-A crash, broader embedded data-pointer survey, broader unhooked-writer survey

## STOP Triggered

NO.
