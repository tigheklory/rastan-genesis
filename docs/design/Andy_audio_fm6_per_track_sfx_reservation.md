# Audio Composer — FM6 reserved for SFX only on gameplay tracks

**Date:** 2026-11-07 · **Author:** Andy · **Scope:** `tools/audio_composer/` + `tools/audio/render_genesis_vgm.py`
(development tooling only — NO ROM / build / Z80 / 68000 change)

## Request (Tighe)

Tighe re-authored **07 - Scene Clear** and disliked the channel assignment. The Audio Composer had been
hard-reserving **YM2612 FM6** on *every* track. But only the tracks that play **while the player is in
control** need a channel kept free for live sound effects. Those are the four gameplay tracks:

| # | Track | FM6 |
|---|---|---|
| 03 | Aggressive World (Scene 1) | **reserved for SFX** |
| 05 | Re-In-Carnation (Scene 2) | **reserved for SFX** |
| 06 | The Devil Boss Carnival (Scene 3 Boss) | **reserved for SFX** |
| 08 | Final Destroy (Scene 3 Round 6 Boss) | **reserved for SFX** |
| 01 | Credit | FM6 free for music |
| 02 | Broken The Promises (Opening) | FM6 free for music |
| 04 | Bad Bible (Name Regist) | FM6 free for music |
| 07 | Scene Clear | FM6 free for music |
| 09 | The Man Of Saga (Ending) | FM6 free for music |

So FM6 becomes a 6th FM **music** voice on the five non-gameplay tracks, and stays the SFX channel on the
four gameplay tracks.

## Why this is one policy, not a per-track patch

The reservation touched the whole routing subsystem: the destination list the UI offers, the validator
(FM6 legality + the FM budget), the save path, the provisional VGM render, and the per-channel/slot UI. All
of them read **one** source of truth now:

- `SFX_RESERVED_TRACK_NUMBERS = {"03","05","06","08"}` — keyed by the leading two-digit track **number** so a
  rename or re-authoring can never silently move the policy.
- `fm6_reserved_for(track)` — `True` for those four; **`True` for an unidentified track** (fail safe: a policy
  gap never silently steals the SFX channel from a gameplay song).
- `music_destinations_for(track)` — inserts `ym2612_fm6` after FM5 only when FM6 is not reserved.

## Changes

**`tools/audio_composer/server.py`**
- New constants/helpers: `FM6_MUSIC`, `FM_ALL`, `SFX_RESERVED_TRACK_NUMBERS`, `_track_number`,
  `fm6_reserved_for`, `music_destinations_for`.
- `validate_routing(routing, track, noise_mode, track_id=None)`: FM6-as-music is an error **only** when the
  track reserves it (`reserved_fm6_sfx`); the DAC path (`ym2612_fm6_dac`) is never music on any track
  (`reserved_fm6`); destination legality and the monophonic-collision set use the per-track valid set / `FM_ALL`;
  the FM budget is **5 on gameplay tracks, 6 elsewhere**. The `track`/`track_id` split keeps the time-overlap
  evidence (dict) separate from the song identity (string), and the overlap call is now guarded to a dict.
- Save endpoint passes `track_id` so the policy is enforced at persist time; render endpoint rejects FM6 only
  when reserved. `track_inventory` / `default_profile` / `backfill` / save now emit `fm6_reserved`, `fm6_role`,
  and a per-track `music_destinations` so the client is driven by server truth.
- `_s` now sends `Cache-Control: no-store` (same stale-`app.js` class already fixed in the graphics editor;
  without it the new FM6 option could silently fail to appear after a reload).

**`tools/audio/render_genesis_vgm.py`** — FM6 added as a real 6th FM voice: `FM_TARGET["ym2612_fm6"]=6`,
`YM_CH_PORT[6]=(1,2)`, `YM_KEYSEL[6]=6`. FM4–6 already share YM2612 port 1 and the emit path is generic over
those maps, and DAC is globally disabled in the init, so FM6 plays as an ordinary FM channel.

**`tools/audio_composer/app.js`** — `fm6Reserved()` / `destChoices()` / `slotList()` read `TRACK.fm6_reserved`
(default reserved). FM6 appears in the per-channel dropdown and as its own destination slot only on
non-gameplay tracks; gameplay tracks keep the read-only "FM6 — reserved for SFX" slot. `DEST_LABEL.ym2612_fm6`.

## Verification

- `fm6_reserved_for` / `music_destinations_for`: correct for all nine tracks + `None`/garbage (→ reserved).
- `validate_routing`: CH→FM6 on 03 → `reserved_fm6_sfx`; on 07 → no conflict; six FM voices on 07 → clean;
  six FM on 06 → `reserved_fm6_sfx` + `fm_budget`; `ym2612_fm6_dac` on 07 → `reserved_fm6`.
- Renderer: routing CH0→`ym2612_fm6` yields `fm_targets=[6]`, port-1 writes, key-on `0x28 0xF6` / key-off `0x06`.
- `inventory()` / `default_profile()` / `backfill()` carry the per-track fields.
- `verify_audio_composer.py`: **40 passed, 0 failed.** `node --check app.js` OK.

## Scaffolding / removal plan

**None.** Durable tool code only. No production ROM, build number, Z80/68000 ASM, capture, or palette registry
was touched; original arcade captures/ROMs remain read-only; audition remains the existing provisional YM2151→
YM2612/PSG translation (now including FM6). Nothing to remove.
