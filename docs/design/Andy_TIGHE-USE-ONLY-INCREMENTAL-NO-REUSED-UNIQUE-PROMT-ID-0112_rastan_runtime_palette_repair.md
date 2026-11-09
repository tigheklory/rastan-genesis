# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0112 — Rastan gameplay palette repair

**Author:** Andy · **Date:** 2026-11-08 · **Scope:** production profile selection (1 Makefile line) + stale
profile-derived artifact regeneration. No 68000/Z80 ASM, no authored-palette edits, no build-counter edit.

## Result

Gameplay Rastan's colors were wrong because **production built every palette/sprite asset from the stale
`Test` profile** (`EDITOR_PALETTE_PROFILE_ID ?= Test` in `apps/rastan-direct/Makefile`), while Tighe had moved
authoring to **Test 2.0** (`Test_2_0.json`) — where **Line 0 is Rastan's palette, authored consistent across
all rounds/subrounds**. The Composer displayed Test 2.0 (correct); the ROM consumed Test (stale) → wrong
Rastan. Fix: `EDITOR_PALETTE_PROFILE_ID ?= Test_2_0`. Build **0560** reproduces the known-good Build-0554
player graphics (27/27 player tiles byte-identical) and Line-0 palette.

## Build 0555/0557 Rejection (and my 0558/0559 missteps)

- **0554** good (Tighe baseline). **0555** first broke Rastan (Tighe). **0556** = correct player *pixels* but a
  **scrambled Line-0 palette**. **0557** = correct Line-0 palette but **Cody permuted the player pixels** via
  `object:player.rastan` in `Test_2_0.json` — the wrong fix *and* the wrong file (production never reads
  `Test_2_0.json`). Cody's 0557 edit was already reverted in the working tree (§3); left untouched.
- My **0558** set `Test.json object:player.rastan` to identity (the stale build-538 value) — still wrong
  (Tighe confirmed). My **0559** aligned `Test.json`'s player keys to Test 2.0 — still wrong, because the
  **Line-0 colours and all other R1 sprites also come from the profile**, not just the player map. Both proved
  the defect was the *profile selection*, not a single mapping.

## Correct Authored Rastan State

Test 2.0 `object:player.rastan` = `{1:1,2:4,3:9,4:8,5:10,6:6,7:5,8:12,9:11,10:15,11:14,12:3,13:2,14:13,15:7}`,
line 0; Test 2.0 `target_palette_lines[0]` = `0000 0000 0666 0888 0CCC 0006 0008 000E 044A 08AE 0246 006E 00EE
0040 0060 0080`. This matches the Build-0554 runtime CRAM Line 0 exactly except idx 4 (`0CCC` vs `0554`'s
`0EEE`) — an intentional Test 2.0 authored value. `Test_2_0.json` was **not** edited. `Test.json` was reverted
to its pre-session (Cody) values and is now unused by production.

## VRAM Pixel Check

Captured actual VDP VRAM (original-arcade-independent Genesis capture) for the known-good **0554** and the
rejected 0556/0557 via `genesis_player_palette_probe.lua` (symbols resolved dynamically — the legacy
`0xFF60E4`/`0xFFB26C` addresses are stale, confirming §5). Player tiles `0x0547..0x0567`:
0554 == 0556 (0 diffs → 0556 regression was palette, not pixels); 0554 vs 0557 = 20/40 diffs (Cody's permute).
**Final:** the **0560 ROM contains 27/27 of the distinctive 0554-good player tiles** (0558 identity: 2/27).

## SAT Palette-Line Check

Rastan's far-left sprite cluster (idx 3/4/8/10) carries `pal=0` → **CRAM Line 0**, matching the authored owner.
SAT selection was never wrong.

## VDP CRAM Check

Actual VDP CRAM (read via VDP control/data ports) at steady R1-S1 gameplay: **staged shadow == actual CRAM**
(publication is correct). 0554 Line 0 = good; 0556 Line 0 scrambled (13/16); 0557 Line 0 = 0554 (good). The
regenerated Test 2.0 `test_palette_line0.bin` == 0554 Line 0 except idx 4 (authored).

## First Divergence / Root Cause

The four runtime links (graphics source, VRAM upload, SAT line, CRAM publication) were each individually
correct. The divergence is **upstream, at asset generation**: `pc090oj_editor.bin` (reindexed sprite pixels),
`pc090oj_palsel_lut.inc`, and `test_palette_line0/1/3.bin` were all produced from the **wrong profile (`Test`)**.
This is a **profile-selection defect, not a runtime-ownership/writer defect** — so §8 (runtime writer) and §9
(SAT line) remediation did not apply.

## Fix

`apps/rastan-direct/Makefile`: `EDITOR_PALETTE_PROFILE_ID ?= Test` → `?= Test_2_0`. Because several
profile-derived artifacts are mtime-gated (they did not rebuild on the ID change alone), the stale
`pc090oj_palsel_lut.inc` and `test_palette_cram_report.json` were removed and `Test_2_0.json` touched (mtime
only) to force deterministic regeneration; the normal build then regenerates them from Test 2.0
(`PALETTE_FAMILY_VERIFY_PASS`). No authored-palette workaround; no ASM.

**Blast radius (intended, per Tighe):** the switch also moves R1 enemy/object palettes (green sword knight,
chimera, large/small bat, valkyrie, cave block) to their Test 2.0 authored values, and the HUD/game-over
text. Tighe confirmed these are intentional. R2 rosters exist only in Test 2.0; R2 gameplay still uses the
retained arcade conversion (RG-021, round ≥ 23), so R2 is not reworked here.

## Stage Clear Non-Regression

`palette_hooks.s`, `scene_load.s`, and `Test_2_0.json`'s `context_policies` are untouched; the PROMT-ID-0111
Stage Clear text fix is intact. `verify_round1_completion_semantics.py` runs as a build gate and reports
`source=full-bright target=Test_2_0.json line=1 … bank4F=line1 line2=untouched` (Stage Clear text bank 0 → Line
0, figure bank 5 → Line 1) — **PASS**.

## Builds / SHA-256

Build **0560** (normal + variants), gate labels `canonical=PASS entry=FAIL epoch=FAIL` — the `entry`/`epoch`
MAME gates were killed, not failed (see below).

| ROM | SHA-256 |
|---|---|
| normal | `59cf10310051d864d4724726e2c1ef9cfb9440fb26bdb513a315cf8d5cba0fb9` |
| invincible | `0c08d0d799fdb04646c0f795990e6206e659d0dd3c3482a4feb37da8cbfafec8` |
| R1-S2 direct (`_S1-2`) | `6521c647977d37adea8c12f4eb8d8eecbef679879840d9c9e262cedbeec4b3c5` |
| R1-S3 direct (`_S1-3`) | `00ac72be84465059c40627765084ca0e44abfffa7f2a461512ef25a0262a8177` |

All four carry byte-identical fixed player graphics (27/27 player tiles == 0554). R1-S2/S3 direct were built
via `tools/translation/build_subround_variant.py` (patches the numbered parent; no recompile/MAME). Tighe
visually confirmed 0560 normal Rastan is correct.

## MAME environment note (honesty)

This sandbox's MAME wedged mid-session (hangs at init, 0% CPU, ignores `timeout` SIGTERM) after a gate MAME had
to be `kill -9`'d. Every subsequent MAME run here hangs, so the build's `entry`/`epoch` gates and my §16 runtime
gate could not complete and were killed (hence `entry=FAIL epoch=FAIL` labels; the ROM is numbered+preserved per
CLAUDE.md). The same build runs in seconds in Cody's environment. All 0560 verification here is therefore
**offline** (byte-exact tile + palette match to the 0554 ground truth). Runtime/visual acceptance is Tighe's.

## New/updated tooling

- `tools/mame/scripts/genesis_player_palette_probe.lua` + `tools/mame/run_genesis_player_palette_probe.sh`
  (dynamic-symbol player-palette capture; no hard-coded WRAM).
- `tools/translation/verify_player_palette_runtime.py` (§16 gate: SAT line, publication, CRAM==authored,
  cross-scene) — ready to run once MAME is available (Cody's env or next healthy session).

## Deferred Issues

Torches NOT TOUCHED; R2 palette NOT TOUCHED; R2 boss NOT TOUCHED; score/high-score NOT TOUCHED; Continue text
NOT TOUCHED. The sandbox MAME hang is environmental (not a ROM/build defect).

## Tighe Acceptance Pending

BlastEm / real-hardware / MAME visual acceptance of 0560 Rastan (R1-S1, R1-S2 direct, R1-S3 direct) + enemy
spot-check is pending Tighe.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0112`
