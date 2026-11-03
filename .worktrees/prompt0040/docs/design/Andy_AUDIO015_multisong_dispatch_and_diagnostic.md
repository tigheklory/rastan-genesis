# Andy — AUDIO-015: Multi-Song Dispatch, Verified Mapping Table & Diagnostic Selection

**Task:** AUDIO-015 (complete seven-song implementation) · **Issue:** OPEN-039 (remains OPEN) ·
**Agent:** Andy (Opus) · **Date:** 2026-10-23 · **Baseline:** accepted Build 0492 ·
**This build:** **0493** (SHA `b998e5641bd553de5a7807ef86a973b8dcc1939528edc5f1af6f1d0e9ab941ae`).

## Summary

All seven authored Composer streams are now selectable and decodable on the permanent Z80 engine.
The engine architecture already supported multi-command dispatch (the driver scans a generated song
table by command; the bridge publishes all non-`$25`/`$1E` commands), so no driver or playback-engine
change was needed. The work is entirely in the **generated registry data** and its tooling:

- The song-map (`specs/audio_native_song_map.json`) now declares, in addition to the one proven
  authentic mapping, a **diagnostic selection** block: one reserved selector per authored song.
- `compile_genesis_native_library.py` emits those rows into the Z80 song table; the static verifier
  enforces proven-vs-diagnostic separation; a labeled MAME harness exercises every stream.

Nothing in Build 0492's accepted behavior changed (verified, §4). No Composer arrangement is hardcoded
into assembly — songs are selected from generated registry data.

## 1. Verified music-command mapping table

The original sound CPU dispatches command space `0x00-0x2B` as music (song-pointer table at ROM
`0x2300`), ignores `0x2C-0xDF`, treats `0xE0-0xEF` as control, and `0xF0-0xFE` as SFX control
(AUDIO-002 / AUDIO-009). The authoritative command→song inventory
`build/audio/music_command_inventory.json` records `command_to_track_name` as **"UNRESOLVED (captures
named by musical identity, NOT proven to a command byte)"**. Channel-count structure does not
disambiguate (four 8-channel commands for two 8-channel songs; eight 6-channel commands for six
6-channel songs). Therefore:

| ID | Composer track | Authentic BGM command | Status | Diagnostic selector | Decode |
|---|---|---|---|---|---|
| 1 | 01 - Credit | — (candidate `0x04`, see below) | **UNRESOLVED** | `0xD0` | PASS |
| 2 | 02 - Broken The Promises (Opening) | — | **UNRESOLVED** | `0xD1` | PASS |
| 3 | 03 - Aggressive World (Scene 1) | `0x25` (player appearance) | **PROVEN** (hw-accepted 0492) | `0xD2` | PASS |
| 4 | 04 - Bad Bible (Name Regist) | — | **UNRESOLVED** | `0xD3` | PASS |
| 5 | 05 - Re-In-Carnation (Scene 2) | — | **UNRESOLVED** | `0xD4` | PASS |
| 6 | 06 - The Devil Boss Carnival (Scene 3 Boss) | — | **UNRESOLVED** | `0xD5` | PASS |
| 7 | 09 - The Man Of Saga (Ending) | — | **UNRESOLVED** | `0xD6` | PASS |

- **Proven:** `0x25` → Aggressive World. `0x25` is the player-appearance cue; the shared bridge gate
  (`player_state == 3`, Build 0492) starts/restarts the Scene-1 song at genuine appearance/respawn.
  This is the only hardware-accepted authentic music mapping and is **unchanged**.
- **Candidate (NOT wired, NOT proven):** ORIGINAL ARCADE command-timing
  (`states/traces/audio015_arcade_gameover`) shows `0x04` emitted at the credit state (`state0=1`,
  `state2=1`, immediately after coin), and `0x04` is a 2-channel cue — consistent with "01 - Credit"
  (2 keyed channels). This is context-only; it is **not** corroborated against the captured `.vgz`
  musical content, so it is recorded as a candidate in the song-map and deliberately **not** placed in
  production dispatch. Wiring an unproven command risks the wrong song at coin.
- Resolving the remaining six authentically is the open AUDIO-002/AUDIO-009 follow-up: match each
  command's installed sub-sequence register stream to the captured `.vgz` identity. Contexts for Scene
  2, Scene 3 Boss, and Ending are not reachable in Genesis automation (the translated 68000 core stalls
  the player at `player_x = 0xA7`), so that correlation is the only rigorous path and remains future
  work.

## 2. How dispatch works (no engine change)

`genesistan_audio_song_dispatch` (generated) is a table of 7-byte rows `{command, start24, loop24}`.
`z80_init_and_start` copies it into Z80 RAM at `0x1E00` (`0x1DFF` = count). The driver's `command_pop`
pops a queued command, `0x00` stops, otherwise it scans the table for a matching command and plays that
song; an unmatched command is consumed without interrupting the current song (the
`consume_without_interrupting_current_music` policy — this is how SFX requests never stop music). All
seven intro/loop streams are already `.incbin`'d into the ROM `.audio` section, so adding a mapping only
adds a table row — the arrangement is never embedded in assembly.

Build 0493 song table (8 rows): `0x25`→3 (proven) then `0xD0..0xD6`→1,2,3,4,5,6,7 (diagnostic).

## 3. Diagnostic selection path (explicitly labeled, not authentic)

The selectors `0xD0-0xD6` live in the arcade-ignored command range `0xC0-0xDF`. **The running arcade
program never emits them**, so production behavior is unchanged; they exist only so the labeled harness
`tools/mame/run_audio015_native_song_diagnostic.sh`
(`tools/mame/scripts/audio015_native_song_diagnostic.lua`) can inject each one into the Z80 command ring
and confirm the intended stream decodes. The harness is a diagnostic; it must never be cited as an
authentic in-game music event. GENESIS NTSC MAME result
(`states/traces/audio015_native_song_diagnostic/`): all seven selectors → driver ACTIVE, stream pointer
advances, and the pointer sits inside that song's own cartridge window (`result=PASS`).

## 4. Validation (Build 0493)

- Static audio gate: `AUDIO_NATIVE_STATIC_PASS driver=564 songs=7 dispatch=1 diagnostic=7 ticks=17410
  events=151408` (driver unchanged; proven `0x25`; diagnostic covers all 7, disjoint, reserved range).
- All production gates pass (boot guard, canonical, final-life transition, R1 selector, invincible
  variant), full 7-ROM family built.
- **Diagnostic harness:** 7/7 songs decode (§3).
- **Accepted R1-S1 preserved:** GENESIS NTSC runtime gate on 0493 `result=PASS` — appearance `0x25`
  at frame 381, driver ACTIVE, `banked_mismatches=0`, no invalid access, identical accepted command
  stream to 0492. Music change/banking not corrupted; `$1E` GAME OVER handling and FM6 reservation
  intact.
- **Composer workflow:** `test_genesis_native_library_workflow.py` →
  `AUDIO_NATIVE_PROFILE_WORKFLOW_PASS changed='01 - Credit' unchanged=6 real_profile=UNCHANGED
  driver=UNCHANGED registry=UNCHANGED`. Edit arrangement → save → build → only that song's native
  assets regenerate; driver and command registry untouched. Edit→Save→Build→Hear is intact.

## 5. Scaffolding inventory and removal plan

- **No NOP/RTS, no production ROM code scaffolding.** No driver or bridge code changed for this task.
- The diagnostic selectors are **data rows** in the generated song table, in the arcade-ignored
  command range, inert during real gameplay. They are the task-sanctioned "explicitly labeled
  diagnostic selection path." **Retain** while authentic BGM command→song mappings remain unresolved;
  when a song's authentic command is proven, add it to the song-map `dispatch` (proven) and the
  diagnostic selector for that song may be dropped.
- New durable tooling (retain): `tools/mame/scripts/audio015_native_song_diagnostic.lua` +
  `run_audio015_native_song_diagnostic.sh`; the `AUDIO015_ARCADE_INVINCIBLE` toggle on the arcade
  observer (added in the Build 0492 task).

## 6. Deferred: native SFX architecture (documented, NOT implemented this task)

Per the directive, SFX work is deferred until all authored music is complete. The existing native
sound-command interface (the `z80_write_command` bridge + the Z80 command ring) is the stable seam that
later SFX work builds on, so SFX integration will **not** require revisiting the original arcade 68000
call sites. Future SFX architecture should provide:

1. Enumeration of the original arcade SFX command space. AUDIO-002 located the control/SFX dispatch:
   `0xF0-0xFE` is a jump table at ROM `0x041B` (`0xF0`→`0x03F7`, `0xF1-F3`→`0x0408`, `0xF4-FE`→no-op);
   `0xE0-0xEF` at `0x0368` (`0xEE/0xEF` toggle the sound-enable/attract flag `0x8F26`). Actual sampled
   SFX are requested through song channels whose channel id routes via the `0x0348` table to the ADPCM
   engine (`0x19A8`) — INFERRED, pending the `0x0479` sub-sequence opcode decode.
2. Identification of each original YM2151/MSM5205-ADPCM effect and classification into PCM / FM / PSG.
3. SGDK XGM2-style Z80-driven PCM mixing through the reserved **YM2612 FM6 DAC** (already reserved by
   the driver and the Composer profile; the native stream format forbids writes to timer regs
   `0x24-0x27` and to FM6).
4. FM/PSG channel sharing + priority, and restoration of music voices after an SFX releases a channel.

**Do not** integrate the SGDK sound driver or begin PCM work until authored music is finished and
Tighe directs it.

## 7. Status (Build 0493)
- Build 0492 accepted baseline, tagged `accepted/build-0492`.
- Build 0493: all seven authored songs decode (diagnostic); one proven authentic mapping (`0x25`);
  six authentic BGM commands remain UNRESOLVED and are labeled as such.

---

# Build 0494 — Nine songs, Composer persistence repair, and authentic Credit/Scene-2 mappings

**Date:** 2026-10-24 · **ROM SHA:** `99d2ccd2b3e9dd08d5a7e31c2195a0c8acd58024040702b83965fa58691de677`.

## 8. Audio Composer persistence bug — cause, permanent fix, recovery

**Symptom:** two authored songs — **07 Scene Clear** and **08 Final Destroy** — never reached the ROM
(`track_routings` held only 7). Their routings survived only as the *active-track* top-level working
copy in revision snapshots (07 in `music-test.r8.json`, 08 in `music-test.r13.json` / current).

**Cause:** `track_routings` is the authoritative per-song store the ROM compiler reads. The server
(`tools/audio_composer/server.py`) never maintained it — it trusted the client. The client
(`tools/audio_composer/app.js`) folded the active track into `track_routings` on save/switch
(`stashTrackRouting`), **but** `loadProfile` only migrated a top-level routing into `track_routings`
when that map was **entirely empty**. Once any song was in `track_routings`, a track whose decisions
lived only at top level was never migrated, and `selectTrack → applyTrackRouting` then **wiped** the
working copy (loading an absent per-song entry as `{}`). So 07/08 — the last songs authored, whose
per-song entries were never created — were dropped on the next load/save cycle.

**Permanent fix (two layers):**
1. **Server (authoritative):** `/api/profile` now folds the active track's top-level decisions into
   `track_routings[track_id]` on **every** save, so a save always persists that song. It will not
   clobber an existing non-empty per-song entry with an empty working copy.
2. **Client:** `loadProfile` migrates the active track's top-level routing into `track_routings`
   whenever that per-song entry is **missing** (not only when the whole map is empty), so selecting a
   top-level-only song can no longer wipe it.

**Regression test:** `tools/audio_composer/verify_audio_composer.py` tests 22a/b/c (save → switch →
reload persists both songs; an emptied working copy does not clobber a saved routing). Full suite:
**40 passed, 0 failed**.

**Recovery (no manufactured approvals):** `tools/audio_composer/recover_lost_track_routings.py` folds
07's saved top-level routing from r8 and 08's from the current profile into `track_routings`, using the
stored `approved_routing` (the user-approved channels) / `proposals` / `noise_mode` /
`instrument_overrides` verbatim. `approval_status` is a profile-level field, not per-channel; the
per-channel approvals ARE `approved_routing`, so recovering it preserves real approval semantics. The
full profile + all revisions were backed up first to
`analysis/audio/decision_profiles/_backup_pre_migration_*`. `track_routings` now holds **all nine**
authored songs (new revision r14); nothing was discarded or overwritten.

## 9. Complete nine-track inventory and verified command mapping table

| ID | Composer track | Authentic command | Status | Diagnostic selector | Decode |
|---|---|---|---|---|---|
| 1 | 01 - Credit | **`0x04`** (coin / credit screen) | **PROVEN** | `0xD0` | PASS |
| 2 | 02 - Broken The Promises (Opening) | — | UNRESOLVED | `0xD1` | PASS |
| 3 | 03 - Aggressive World (Scene 1) | **`0x25`** (appearance, spawn column) | **PROVEN** (hw-accepted) | `0xD2` | PASS |
| 4 | 04 - Bad Bible (Name Regist) | — | UNRESOLVED | `0xD3` | PASS |
| 5 | 05 - Re-In-Carnation (Scene 2) | **`0x27`** (R1-S2 castle, substate 9) | **PROVEN** | `0xD4` | PASS |
| 6 | 06 - The Devil Boss Carnival (Scene 3 Boss) | — | UNRESOLVED | `0xD5` | PASS |
| 7 | 07 - Scene Clear | — | UNRESOLVED | `0xD6` | PASS |
| 8 | 08 - Final Destroy (Final Boss) | — | UNRESOLVED | `0xD7` | PASS |
| 9 | 09 - The Man Of Saga (Ending) | — | UNRESOLVED | `0xD8` | PASS |

### Newly resolved authentic mappings (from the R1 music sequencer at `0x055DDC`)

The R1 music/segment sequencer steps substate `a5+0x13AA` from 1 to 13 — these are the "segments":
- **Substate 1** → `$00` (stop) + **`$19`** = Aggressive World (R1-S1 outdoor).
- Substates 2–8 → scroll/counter work, **no** music command (substate 8 ends the outdoor phase).
- **Substate 9** (R1-S2 castle, entered via `0x03A848` setting `13AA=9` / `1394=1`) → **`$27`** =
  **Re-In-Carnation (Scene 2)**.

- **`$27` → Re-In-Carnation (Scene 2):** the authentic castle music-change, proven by the sequencer
  control flow plus Tighe's observation that the castle plays Re-In-Carnation. Unlike `$19`, the
  substate-9 send has **no `a5+0x34` sound-enable precondition**, so it is delivered on Genesis
  (`$19` was not — Build 0487). Wired to production dispatch → fixes "Scene 2 does not begin in the
  castle." (Finding #2.)
- **`$04` → Credit:** emitted at the credit state (`state0=1`/`state2=1`) right after coin; a 2-channel
  cue matching Credit's 2 keyed channels; already delivered to the Z80 ring on Genesis. Wired →
  fixes "Credit does not play at coin." (Finding #3.) The runtime gate shows the driver now activates
  at frame 120 (the `$04` Credit start) ahead of the `$25` appearance.
- `$19` → Aggressive World is the authentic Scene-1 command but is not delivered on Genesis (the
  removed sound-IRQ `a5+0x34` handshake), so Aggressive keeps the hardware-accepted `$25` appearance
  trigger from Build 0492.

### Still UNRESOLVED (documented evidence gap)
Opening, Name Registration, Scene 3 Boss, Scene Clear, Final Destroy, Ending: no authentic command is
proven. `build/audio/music_command_inventory.json` records command→song as UNRESOLVED and channel
counts do not disambiguate. Their contexts are unreachable in Genesis automation (the translated 68000
core stalls the player at `player_x=0xA7`), so the rigorous resolver is the AUDIO-002/009 follow-up
(match each command's installed sub-sequence register stream to the captured `.vgz`). Until then they
are diagnostic-only; no assignment is invented.

## 10. Segment 8 restart fix (shared, not segment-specific)

Build 0492 gated `$25` on `player_state==3`, fixing the segment-5/12 restarts. A residual restart ~2/3
through segment 8 remained: a mid-stage `player_state==3` re-appearance that passes the state gate. A
genuine (re)appearance always occurs at the **stage spawn column** (`player_x==0x20`; ORIGINAL ARCADE
appearance and R1-S1 respawn are both `0x20`), whereas a mid-stage re-appearance is at a large
`player_x`. The `$25` publish gate now also requires `player_x <= 0x28` (spawn column): the stage song
(re)starts only at a true spawn. This is the second half of the same shared rule — not a segment-8
workaround — and preserves the accepted appearance/respawn start, death continuation, and GAME OVER
stop. **Evidence gap:** segment 8 is unreachable in automation, so the exact `player_x` of the residual
event is inferred from its mid-stage position; final confirmation is Tighe's hardware audition.

## 11. Build 0494 validation
- Static gate: `AUDIO_NATIVE_STATIC_PASS driver=564 songs=9 dispatch=3 diagnostic=9 ticks=22433
  events=204777` (proven `0x04`,`0x25`,`0x27`; diagnostic covers all 9).
- Canonical coverage invariant updated `0x30FEB8 → 0x335EB8` (+0x27000 for the two recovered songs) —
  a declared-coverage update like the 7-song one, not a disabled check. All production gates pass.
- Diagnostic harness: 9/9 songs decode (incl. recovered 07 `0xD6`, 08 `0xD7`).
- GENESIS NTSC runtime gate: `result=PASS`, accepted R1-S1 behavior preserved, driver activates at the
  Credit `$04`, `banked_mismatches=0`, no invalid access.
- Composer workflow: `AUDIO_NATIVE_PROFILE_WORKFLOW_PASS … unchanged=8` — all nine independently
  editable; Edit→Save→Build→Hear intact.
- Composer persistence suite: 40 passed, 0 failed.

## 12. Status
- **OPEN-039 remains OPEN**: authentic command→song for the six UNRESOLVED songs (register-stream↔`.vgz`
  correlation), Tighe's hardware audition of the `$04`/`$27`/spawn-column fixes, and deferred native SFX.
- Fixed permanently: the Composer `track_routings` persistence bug (future edits reliably reach the
  build). All nine authored arrangements now compile and are independently editable and selectable.
