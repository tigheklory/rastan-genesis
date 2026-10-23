# RG-017 — Attract Demo-to-Title Display Ownership

## Result and baseline

Cody produced Build 0478 as an automated-validation candidate. The accepted baseline remains Build
0473 (`accepted/build-0473` -> `f6e975b864af2aca7bdf24b0a40a9db43bd62f59`); Builds 0474–0477 remain
consumed and unaccepted. The counter advanced `477 -> 478`. No accepted tag was created or moved.

The exact ROM-producing source is `aab0eac15a9a332331cea5f773252a3010059dd8`. The title source edit
was accidentally swept into Tighe's published audio commit `902bf040` during the interrupted session.
Published commits `902bf040` and cleanup `34576108` were preserved without reset, revert, amend, or
history rewriting. Follow-up RG-017 commits complete the regression and bookkeeping cleanly.

## Static root cause and retained control flow

The retained no-input path is:

1. title dwell `0/1/0`;
2. attract setup and demo gameplay, reaching `2/3/0`;
3. natural demo death (`A5+0x10E8 == 8`) and terminal controller states `2/4/0 -> 2/4/1 -> 2/4/2`;
4. retained terminal-death producer `0x051998` (Build-0478 runtime `0x051BB4`) requests the native
   presentation HOLD and writes VDP display OFF;
5. retained control returns to `0/0/0`; the existing source-range scene selector calls
   `load_scene_tiles(0)`, changing scene 1 to scene 0 without executing retained `0x056440` or
   `0x03AD4C`;
6. scene-0 patterns/base palette and frontend ownership are installed while HOLD remains asserted;
7. the retained title entry at `0x03AA54` (runtime `0x03AC7E`) invokes
   `genesistan_title_present_once`, then title dwell becomes `0/1/0`;
8. fixed-order `dma_publish_frame` publishes CRAM, patterns, Plane B, Plane A, SAT and scroll.

The HOLD at `0x051998` is legitimate: the demo's gameplay presentation has ended and scene-0 native
resources are not coherent yet. `load_scene_tiles(0)` is also correct to leave an inherited nonzero
readiness latch blank. The defect was that Build 0477 had no later title-complete event that changed
the latch from HOLD (`1`) to READY (`2`), so `genesistan_presentation_publish_complete` continually
reasserted display OFF even after title state and CRAM were correct.

The title-complete boundary is the existing native replacement for retained `0x03AA54`. Before its
return, `genesistan_title_present_once` has installed title patterns, copied complete BG/FG maps,
staged title CRAM, armed BG/FG/palette publication, zeroed scroll, rebuilt frontend HUD/SAT state,
and reproduced retained `A5+0x0004`, `A5+0x0002`, and `A5+0x002C` title dwell state. It is therefore
the first authoritative complete-title producer, not an elapsed-frame inference.

Human final death works because its distinct path executes frontend reset and then complete retained
presentation producers: Continue `0x03A374`, terminal GAME OVER `0x03A448`, and READY `0x03A74E` each
request publication-gated visibility. The attract return bypasses those producers and reaches title
through the scene selector, which is why only the attract path inherited HOLD indefinitely.

## Presentation ownership correction

`apps/rastan-direct/src/title_native.s` now calls
`genesistan_presentation_mark_ready_after_publish` after every title resource and retained title-dwell
state is complete. The helper only writes readiness `2` while preserving SR/CCR; the existing
`dma_publish_frame` completion remains the sole display-enable owner. The change introduces no direct
display write at `0x03AA54`, timer, wait-N delay, attract polling, second state machine, chip shadow,
fallback, NOP, RTS bypass, or broad frontend clear.

The semantic cut remains retained title intent -> final Genesis title presentation. No additional
PC080SN/PC090OJ tail was introduced or removed: the already-established `0x03AA54` native title cut
continues to retire the original title palette/logo/text chip tail. Existing RG-014 register
preservation and all RG-016 READY/Continue/GAME-OVER/gameplay ownership boundaries remain unchanged.

## RG-004 regression upgrade

`tools/mame/scripts/rg004_frontend_probe.lua` retains natural demo/death, second-title semantic-state,
first-versus-second title palette, and staged-versus-terminal CRAM checks. It now also keeps its MAME
tap objects strongly reachable, decodes actual VDP register-1 writes, records display OFF/ON after
natural demo death, rejects unsafe ON writes while latch `1` is active, and requires a post-demo VDP
display-enable write plus final latch `0` at the second title. Optional retained-PC observers now take
current address-map-derived runtime PCs instead of stale Build-0464 constants.

On the same Genesis-driver MAME route:

- Build 0477: natural demo/death and second title at frame 7,216; palettes and CRAM match; final VDP
  display OFF; latch `01`; 15 post-demo OFF writes, 0 ON writes; visibility **FAIL**.
- Build 0478: natural demo/death and second title at frame 7,216; all four first/second title lines
  and terminal CRAM match; final VDP display ON; latch `00`; 8 post-demo OFF writes, 1 ON write;
  zero unsafe ON writes; visibility **PASS**.

This is an ownership assertion, not an attract-specific force-ON: the required ON is the consequence
of the completed producer's READY request being consumed after fixed-order publication.

## Build 0478 artifacts

All files are 2,739,896 bytes.

| Variant | ROM | SHA-256 |
|---|---|---|
| normal | `dist/rastan-direct/rastan_direct_video_test_build_0478.bin` | `989842a323b2e27ad8461425271291c38840cc4e949bfcca160bf0124286634c` |
| `_c` | `dist/rastan-direct/rastan_direct_video_test_build_0478_c.bin` | `3bcf037fd93cf60407b6b1575ac3ff22164b89d98ae5f5d445ee9b57daaa8419` |
| `_d` | `dist/rastan-direct/rastan_direct_video_test_build_0478_d.bin` | `954c980a4b97718acfc6d05dc2aa59f42bcbfc4f2a54c9e86daef0d946687ad8` |
| `_do` | `dist/rastan-direct/rastan_direct_video_test_build_0478_do.bin` | `97c80b803e50e3af4a4954955479747c9b58a45bdf80d4b54ed3f3de2c93e87b` |
| `_full_hud` | `dist/rastan-direct/rastan_direct_video_test_build_0478_full_hud.bin` | `f244085e79ee2b6248585e6fdab2f121151dccee80f66a2b88b374496ab5a5c6` |
| `_invincible` | `dist/rastan-direct/rastan_direct_video_test_build_0478_invincible.bin` | `6de7f18c1670ce818be21a19b0a7ebb066811bd10f5c6a900f914bfbb14d6902` |
| `_s` | `dist/rastan-direct/rastan_direct_video_test_build_0478_s.bin` | `a919281c08f9ff07c65a127c7b8b84ed824354853bf88940ed376ccadfbf3238` |

Canonical inventory remains 228 byte-neutral opcode sites plus 86 shift replacements, with expected
Genesis coverage `0x29CEB8`. The complete configured seven-ROM family verifier passes.

## Validation

- Static: canonical Ghidra exports, original disassembly, current spec, generated address map, native
  title/scene/publisher source, and RG-003/RG-004/RG-016 evidence agree on the cut and divergence.
- Build/static pipeline: assembly, link, pre/post boot guards, 86-site shift reflow, 29 declared
  jump-table repairs, 7,202 relative-branch repairs, 2 declared-branch repairs, 628 absolute-long
  repairs, canonical gate, native title/HUD/item, palette, DMA boundary, final-life transition,
  configured-family verification: **PASS**.
- Genesis-driver MAME R1-S1 entry: **PASS**, 569 frames, 240 post-entry frames, no exceptions.
- Genesis-driver MAME seven production epochs: **PASS**.
- Genesis-driver MAME fixed 30-second trace: completed with no unmapped-memory report.
- Upgraded RG-004 natural attract route: **PASS**, frame 7,216, second title visible, CRAM exact,
  unsafe display-enable writes 0.
- RG-016 final-life/READY route: **PASS**, three deaths, 220 visible READY frames, 140 post-READY
  blank frames, two coherent visible restarts, 966 visible Continue frames, unsafe visibility 0.
- Writer-triggered HUD/Continue re-entry: **PASS**, score `001234`, both SAT banks, 25 visible Continue
  frames, 71 blank loading frames, coherent re-entry at frame 4,417.
- Genesis-driver MAME `_invincible` rope: `795/795/795`, median `13,267.083 ms`, deterministic YES;
  identical to Build 0477, so no route-level performance regression or improvement.

No new gameplay bot or new gameplay route was created. Original arcade meaning was established from
existing Ghidra/disassembly evidence; runtime validation used Genesis NTSC MAME only. No real-hardware
success is claimed.

## USER MUST VERIFY

On real Genesis, Tighe must verify title -> visible attract demo -> natural demo termination -> next
title visibly returns, preferably allowing one more attract cycle. Then verify only the affected
ownership regressions: non-final death disintegration with no torso/legs reconstruction, visible
READY, black unsafe post-READY loading, coherent respawn, and final human death with visible
GAME OVER/Continue/frontend recovery. Build 0478 remains unaccepted until that test.

STOP: RG-017 complete as an automated-validation candidate; hardware acceptance pending. No audio,
`_full_hud`, bat, PC080SN, PC090OJ, or unrelated optimization work was started.
