# Cody — Rastan arcade rope-race Silver Standard

## Result

The original-arcade MAME Silver Standard is **771 frames / 12,850.000 ms**
from the first controllable gameplay state to the first legitimate rope attach.
Five official trials are identical. The stock MAME `Invincibility` cheat was
enabled solely to prevent enemy contact from exhausting Rastan before the rope;
the route remains Coin, Start, continuous Right, no jump, and no attack.

Build 0425 takes 13,634.222 ms. It is **784.222 ms / 6.102895% slower**, a gap
equivalent to **47.053 arcade 60-Hz frames**. This is a **MATERIAL SLOWDOWN** by
the predeclared greater-than-2% band.

No production source or Genesis gameplay was changed, no ROM was built, and
Build 0426 was not consumed.

## Exact arcade revision

The benchmark uses MAME set `rastan`, **Rastan (World Rev 1)**. Exact source
identity was already proven:

- MAME and `build/rom_inventory.json` agree on all six main-CPU filenames and
  SHA-1 hashes: `b04-38.19`, `b04-37.7`, `b04-40.20`, `b04-39.8`,
  `b04-42.21`, and `b04-43-1.9`;
- reconstructed `build/regions/maincpu.bin` has SHA-1
  `63577d3f75a96b35398cf40126c40598ebd8089d`, matching the authoritative
  `world_rev1` entry in `specs/variants.json`.

## Machine, timing, and DIP conditions

MAME 0.276 reports an 8,000,000 Hz Motorola 68000 and exactly 60.000000 Hz
refresh. Runs used `-speed 1.0`, `-norefreshspeed`, and MAME emulated attotime;
host wall-clock time was not measured.

Each trial used an isolated MAME configuration directory so the user's local
Coin-A override could not leak into the test.

| Setting | Factory-default value |
|---|---|
| Cabinet | Upright |
| Flip screen | Off |
| Service mode | Off |
| Coin A | 1 Coin / 1 Credit |
| Coin B | 1 Coin / 2 Credits |
| Difficulty | Medium |
| Bonus life | 100k, 200k, 400k, 600k, 800k |
| Lives | 3 |
| Allow Continue | On |
| Region/revision | World Rev 1 |

## Invincibility mechanism and scope

The runner launches MAME with its cheat plugin and the existing Rastan cheat
database, then enables the stock cheat named `Invincibility` through
`emu.plugin.cheat`. It continuously sets bit 6 at arcade A5+`0x0040`
(`0x10C040`). The official rows prove the plugin remained enabled and the word
remained `0x0040` at the stop.

Static arcade code shows that A5+`0x0040` is tested inside the player damage,
hazard, and death handlers. A nonzero value branches around health subtraction,
damage reaction setup, knockback/velocity setup, and state-8 death entry. It
does not modify enemy actors, enemy AI, the game timer, ordinary player speed,
camera, scroll, collision lookup, or rope logic.

| Property | Result |
|---|---|
| Enemies remain active | YES |
| Enemy collision/contact detection remains active | YES |
| Damage prevented | YES |
| Life loss from enemy contact prevented | YES |
| Death from enemy contact prevented | YES |
| Hit-stun | SUPPRESSED |
| Knockback | SUPPRESSED |
| Ordinary player velocity directly altered | NO |
| Movement timing at damaging contacts altered | YES—damage reactions are suppressed |
| Gameplay timer altered | NO |
| Enemy timing altered | NO |

The stock cheat notes that water can still kill the player; the measured route
does not enter water before the first rope.

## Semantic boundaries and false-positive exclusion

Arcade work RAM uses A5=`0x10C000`; Genesis retained work RAM uses
`0xFF0000`. The start timer uses the same A5-relative fields as the existing
Genesis benchmark:

- A5+`0x0000/0x0002/0x0004` = `2/3/0`;
- scene byte A5+`0x3865` = `1`;
- player X A5+`0x10BE` = `0x0020`;
- player state A5+`0x10E8` is 1–3.

This is the first alive, spawned, controllable gameplay frame. It occurs at
external frame 787 in every arcade run; Right begins from this semantic gate.

The stop requires all of the following simultaneously:

- the same credited game remains active (`2/3/0`, scene 1, lives > 0);
- progression A5+`0x013E` is exactly record 3;
- A5+`0x10E8` first becomes rope/climb state 4;
- the MAME cheat is enabled and A5+`0x0040` bit 6 is set.

Original-arcade human evidence independently places the first rope transition
at record 3, state 4, X `0x00A7`. The official route stops at those same values
(Y `0x0070`, FG scroll `0x0145/0x0149`). Build 0425 uses the inherited record,
state, and player fields. Thus start and stop semantic equivalence is proven.
The credited-game/lives conditions reject the previously observed post-game
attract-mode state-4 false positive.

## Preliminary no-cheat trials

The five preliminary trials remain preserved in
`preliminary_no_cheat_trials.tsv`. All were identical: after 2,902 timed frames
/ 48,366.667 ms, the player had exhausted all lives in record 2/state 8 while
Right remained active (`P1=0xF7`). These are failure endpoints, not timing
samples. A later attract-mode rope state seen during the initial smoke work was
identified and rejected.

## Invincibility smoke and official trials

The single controlled smoke run passed at 771 frames / 12,850.000 ms with
record 3, state 4, X `0x00A7`, lives 3, Right `0xF7`, cheat enabled, and
invincibility word `0x0040`. The five official trials then reproduced it:

| Trial | Start frame | Stop frame | Elapsed frames | Emulated ms | Record/state | X/Y | Cheat/flag |
|---:|---:|---:|---:|---:|---|---|---|
| 1 | 787 | 1,558 | 771 | 12,850.000 | 3 / 4 | A7/70 | YES / 0040 |
| 2 | 787 | 1,558 | 771 | 12,850.000 | 3 / 4 | A7/70 | YES / 0040 |
| 3 | 787 | 1,558 | 771 | 12,850.000 | 3 / 4 | A7/70 | YES / 0040 |
| 4 | 787 | 1,558 | 771 | 12,850.000 | 3 / 4 | A7/70 | YES / 0040 |
| 5 | 787 | 1,558 | 771 | 12,850.000 | 3 / 4 | A7/70 | YES / 0040 |

Median/min/max are all **771 frames / 12,850.000 ms**. Determinism: **YES**.

## Build 0425 comparison and target

| System | Native frames | Emulated ms |
|---|---:|---:|
| Arcade MAME Silver Standard | 771 at 60.000 Hz | 12,850.000 |
| Genesis Build 0425 | 817 at ~59.92 Hz | 13,634.222 |

Primary elapsed-time gap: `13,634.222 - 12,850.000 = 784.222 ms`.
Relative to arcade: `784.222 / 12,850.000 = 6.102895%` slower. At 60 Hz the
gap is 47.053 frames; Genesis elapsed time corresponds to approximately
818.053 arcade frames.

Current Silver Standard target: **12,850.000 ms / 771 arcade frames**. A future
physical-PCB measurement may supersede this MAME target. No gameplay-speed or
physics changes are proposed; any future reduction must come from execution or
presentation overhead.

## Tool and evidence

- Runner: `tools/mame/run_arcade_rope_attach_reference_benchmark.sh`
- Lua: `tools/mame/scripts/arcade_rope_attach_reference_benchmark.lua`
- Evidence: `states/traces/arcade_rastan_rope_attach_reference/`
- Official rows: `states/traces/arcade_rastan_rope_attach_reference/trials.tsv`
- No-cheat rows: `states/traces/arcade_rastan_rope_attach_reference/preliminary_no_cheat_trials.tsv`
- Smoke: `states/traces/arcade_rastan_rope_attach_reference/invincibility_smoke/`
- Provenance/DIPs: `states/traces/arcade_rastan_rope_attach_reference/provenance.txt`

Production modified: **NO**. Genesis gameplay modified: **NO**. Build number
advanced: **NO**. ROM family produced: **NO**. Phase D/E started: **NO**.
Counter remains **425**.
