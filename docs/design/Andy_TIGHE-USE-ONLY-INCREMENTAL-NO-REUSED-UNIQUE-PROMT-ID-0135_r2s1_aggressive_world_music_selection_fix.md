# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0135 — R2-S1 Aggressive World music selection fix

**Author:** Andy · **Date:** 2026-11-13 · **Baseline:** Build 0568 (PROMT-ID-0134 palette/respawn fix, preserved).
Only `apps/rastan-direct/src/sound/sound_comm.s` changed. No palette/0134 code, Plane-A/B, tile, audio-asset,
dispatch-table, Z80 driver, or SFX routing touched. Tighe's gameplay/audio observation is authoritative.

## 1. Completed 0568 baseline & starting tree
- Release `rastan_direct_video_test_build_0568.bin` SHA-256
  `d75eb51e4ac52ef2afd53984c98992fa171a686665b0017bcddcf55f7a008530`; counter 568; full family
  (`_c _d _do _full_hud _invincible _s`) built and verified (`unrelated_rom_differences=0`); gate
  `[canonical=PASS entry=FAIL epoch=FAIL]` (entry/epoch MAME gates wedged in the WSL sandbox and were
  cleared so the ROM numbered+preserved per the standing imperative). Tree: branch `rastan-direct-proposal`,
  0134 `scene_load.s` respawn fix present and preserved.

## 2. Original arcade R2-S1 music-selection caller
The retained per-subround music selector beginning at arcade **0x050660** (reached each subround entry; it is
the sole `$1B` producer, so R2-S2's working Re-In-Carnation comes from here). It first emits the shared player
**appearance cue `$25`** (`0x050690 move #$25,d0; jsr 0x3a116`) and then, by subround, one song command:
- `a5@0x1360==1` → **boss** `$1C` (round 6 `$1D`) at 0x0506E8;
- else `a5@0x140a==1` → **castle** `$1B` at 0x050708;
- else (**outdoor Subround 1**) → `$1A` at 0x050714.

Outdoor is classified at **0x0506C6** as `(record-1-base[round]) < 0x10`, `base[round]` from ROM table
**0x050722** = `0,0x17,0x2E,0x45,0x5C,0x73` = `(round-1)*23`.

## 3/4. Exact Aggressive World command & proof
Two arcade music commands carry the outdoor/Aggressive World identity:
- **`$19`** (round-start READY producer 0x055E30, `ready_state==1`): command→descriptor table
  `0x2300+2*cmd` → `0x2DF0`, **channel count 8**. Cody's AUDIO-015 semantic-recovery matched descriptor
  `0x2DF0` register stream to the Aggressive World capture → `$19` = Aggressive World (8-ch full arrangement).
- **`$1A`** (the per-subround selector's outdoor branch above): descriptor `0x2E90`, count 6 — the 6-channel
  gameplay arrangement of the same outdoor theme; it is the structural sibling of `$1B`(Re-In-Carnation,
  0x2F70/6) and `$1C`(boss, 0x2FE0/6), which are the proven S2/S3 songs.

Either way the **outdoor Subround-1 music = Aggressive World**, and it is announced by the shared `$25`
appearance cue that the current native boundary already maps to the implemented Aggressive World asset.
Descriptors read directly from `build/regions/audiocpu.bin`.

## 5/6. Controls (already working)
- R2-S2 Re-In-Carnation = `$1B` (dispatch `0x1B`→track 05). Evidence: arcade trace
  `states/traces/prompt0076_arcade_r1s2_to_r1s3_audio_v2` ($25 then $1B).
- R2-S3 boss = `$1C` (dispatch `0x1C`→track 06). Same trace ($25 then $1C).
Both reach the dispatcher and play, proving the ring/dispatch/playback pipeline is healthy.

## 7. Natural R1→R2 command sequence (per subround entry)
`$25` appearance cue, then the subround song: S1 `$1A` (outdoor, no following command on the arcade — `$25`
carries it), S2 `$25`+`$1B`, S3 `$25`+`$1C`. At round start the READY producer also emits `$00`+`$19`.

## 8/9. Current Genesis handling & the first divergence (failure class B)
`z80_write_command` (sound_comm.s) special-cases the `$25` appearance: it **publishes** `$25`→Aggressive World
only when the genuine-appearance state holds AND `record < 0x11`. `record < 0x11` is `base 0` — i.e. **R1-S1
only**. For R2-S1..R6-S1 the outdoor appearance has `record ≥ 0x11`, so the shim **consumes** `$25` and nothing
starts the outdoor music (R2-S2/S3 are unaffected because their `$1B`/`$1C` are separate dispatch entries).
**First divergence:** the shared `$25` outdoor appearance is dropped for every round after R1 — failure class
**B** (command emitted, dropped by the Genesis sound shim). The Z80 `music_start` has no de-dup and the 0132
bank-3 routing / `$1A` dispatch are not involved.

## 10. Production fix (smallest faithful correction)
`sound_comm.s` only: replace the R1-only `record < 0x11` test with the arcade's own per-round outdoor test
`(record-1-(round-1)*23) < 0x10` (round = `a5@0x118`), bounded to rounds 1..6. Now the `$25` appearance →
Aggressive World publishes for **every round's outdoor Subround 1** — the identical path R1-S1 already uses —
while castle/boss `$25` still falls outside the window, is consumed, and defers to the authentic `$1B`/`$1C`.
Command-driven (reuses the retained `$25` semantics), not `if round==2`, no scene-song table, no new command,
no audio-asset/dispatch/driver change. `d1/d2` are scratch (reloaded at `.Lpublish`); `d0`(command) preserved.

## 11. Was Aggressive World already implemented?
Yes — track 03 (`genesistan_audio_track_03_aggressive_world_scene_1`) is authored and already dispatched for
R1-S1. Only the **selection/publish gate** was broken for later rounds. No song asset added.

## 12. R2-S1 death/respawn music behavior
The `$25` cue fires on genuine reappearance (player_state==3 at the spawn column) on death-respawn too; the
fixed per-round test publishes it for R2-S1 respawn exactly as it already does for R1-S1 respawn (the accepted
Build 0492 behavior), so Aggressive World restarts on respawn in every round's outdoor stage. No death-specific
hook was added; the death-form `$25` (player_state==8) and mid-stage `$25` remain consumed by the unchanged
outer/player_state/spawn-column conditions.

## 13. Direct-start
The R2-S1 direct-start ROM sets selector 0xFE (round 2 / Outside). It boots into R2-S1 with the same retained
state the natural path reaches, so the fixed appearance test applies identically. Convenience only; natural
progression is authority. (If any direct-start-only prerequisite is missing it is a harness matter, not a
production-selection change.)

## 14/15. Non-regression
- **R2-S2/R2-S3 unchanged:** the fix touches only the `$25` appearance branch; `$1B`/`$1C` dispatch untouched.
- **R1-S1 unchanged:** for round 1, base=0, so the new test `(record-1) < 0x10` matches the old `record < 0x11`
  region (genuine spawn appearances), i.e. the identical publish decision; no double-start (`$1A` is still not
  in the dispatch, so only `$25`→Aggressive fires, as before).
- **0134 palette/respawn preserved:** no palette/scene file changed; `scene_load.s` untouched by this task.
- **SFX / FM6-DAC / Audio Composer:** unchanged (no routing/policy edit).

## 16-18. Candidate / direct-start / test-first
Build **0569** (counter 568→569, `[canonical=PASS entry=FAIL epoch=FAIL]`; entry/epoch MAME gates wedged in
the WSL sandbox and were cleared so the ROM numbered+preserved). Full family verified
(`unrelated_rom_differences=0`). 0568 untouched on disk.
- **16/18 Normal (test this FIRST):** `dist/rastan-direct/rastan_direct_video_test_build_0569.bin`
  SHA-256 `80aed900691c6e4659370f18dfc7127c472db47e4814edd6e9ae08ab03006082`.
- **17 R2-S1 direct-start (convenience):** `dist/rastan-direct/rastan_direct_video_test_build_0569_R2-S1.bin`
  SHA-256 `a7f468c30a45709007036adb7a7b5a548bd8c9e8b4db944e660365f1bac989e2` (selector 0xFE, round 2 Outside;
  no audio-init patch — relies on natural reached state; natural progression is authority).

**Test first:** `rastan_direct_video_test_build_0569.bin`, NATURAL progression R1→R2. At R2-S1 verify Aggressive
World plays (same as R1-S1). Die/respawn in R2-S1 → Aggressive World restarts. R2-S2 Re-In-Carnation, R2-S3
boss still correct. No R1 music regression; SFX intact; 0568 R2 Layer-B palette/respawn still correct.
**Not fixed until Tighe confirms R2-S1 actually plays Aggressive World.**

## 19. Report path
This file. AGENTS_LOG appended.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0135`
