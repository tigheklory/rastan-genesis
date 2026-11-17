TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0154
# Arcade-derived PC090OJ round/subround appearance authority
> Authority order: original World Rev. 1 68000 binary, canonical Ghidra project/export, then the durable C decompilation. Composer, bestiary, Test 2.0, Build 0573, screenshots, and traces are audit inputs—not appearance authority. This report deliberately preserves unknowns.
## 1. Starting state
Branch `rastan-direct-proposal`; starting HEAD `275e2e35e65e46dab46ce685c035e554dea4110d`; Makefile counter `573`. The worktree already contained the uncommitted 0149/0151 reports and analyzer files, `AGENTS_LOG.md`, audio source/output, generated build/address-map/trace files, Andy 0134–0136 documents, and other concurrent documentation. Nothing was reset, cleaned, restored, or built.
## 2. Research methodology
The generator decodes the original `$4A104` 8-byte field schedule, follows `$4A086` into the family/template and palette selectors, and records direct per-record membership. Scripted actors use Ghidra decompilation of `$4580C`, `$45EFC`, `$46204`, and `$4650E`; bats then close through `$45B18`. Rewards use schedule byte `+$36` and the `$40CCC/$40D32` in-place death→reward transform. Bosses use the `$45592` record-type templates and round-specific S3 creators. A graphics base, palette mapping, screenshot, or existing label never creates an appearance claim.
## 3. Exact 18-subround progression/record mapping
`$50248` maps master section through `$5073A` to progression `$013E`; `$502AC` contains round endpoints `$16,$2D,$44,$5B,$72,$89`; `$507C5` selects the scene descriptor. The project coordinate is 23 retained records per round: 16 outside, 6 castle, 1 boss.
|Subround|Round|Environment|Retained records|Entry|Exit|
|---|---:|---|---|---:|---:|
|R1-S1|1|OUTSIDE|0–15|0|15|
|R1-S2|1|CASTLE|16–21|16|21|
|R1-S3|1|BOSS|22–22|22|22|
|R2-S1|2|OUTSIDE|23–38|23|38|
|R2-S2|2|CASTLE|39–44|39|44|
|R2-S3|2|BOSS|45–45|45|45|
|R3-S1|3|OUTSIDE|46–61|46|61|
|R3-S2|3|CASTLE|62–67|62|67|
|R3-S3|3|BOSS|68–68|68|68|
|R4-S1|4|OUTSIDE|69–84|69|84|
|R4-S2|4|CASTLE|85–90|85|90|
|R4-S3|4|BOSS|91–91|91|91|
|R5-S1|5|OUTSIDE|92–107|92|107|
|R5-S2|5|CASTLE|108–113|108|113|
|R5-S3|5|BOSS|114–114|114|114|
|R6-S1|6|OUTSIDE|115–130|115|130|
|R6-S2|6|CASTLE|131–136|131|136|
|R6-S3|6|BOSS|137–137|137|137|
## 4. Current Palette Composer roster architecture
The visible `v0.4` is hardcoded in `tools/graphics_editor/index.html`. New profiles and backend fallbacks also write schema `v0.4` (`app.js` branch creation and `server.py` profile response). Object membership is a mixture: exact `scene_key`, broad `membership=field_phase1`, `shared`, hardcoded Python constructors, bestiary-era labels, and a coverage endpoint. The subround table explicitly says `sprites (per-scene roster pending)`. Thus the UI version, profile schema tag, and feature maturity are effectively conflated.
## 5. Current bestiary roster architecture
`tools/graphics_optimizer/build_bestiary.py` combines hand-curated identities, historical prompt findings, graphics/program domains, and partial source tables. It is useful evidence but is not generated from a complete spawn/record authority. Human labels and graphics families can therefore be correct while round/subround membership is broad, narrow, or conflated.
## 6. Why current classifications became unreliable
The systems historically inferred gameplay membership from graphics availability, broad `shared` mappings, one captured phase, or manual scene tags. They did not keep identity, graphics, palette, Genesis realization, subround legality, and record-local legality as six independent facts. In particular, rewards were treated as globally shared, bats lacked record membership, and the family-8 rope-state label was manually attached to R1-S2 despite no R1-S2 family-8 schedule entry.
## 7. Complete arcade-derived PC090OJ gameplay-object inventory
This pass defines 57 canonical workload records: player/weapons, 12 field families, scripted bats/demon, 17 distinct reward kinds, shared death effects, six boss bodies and six auxiliary domains, plus five technical scripted/effect identities retained as unresolved rather than omitted. Presentation-only title/READY/Stage Clear actors are excluded.
## 8. Object identity table
|Stable ID|Name|Category|Base/type|Spawn source|Palette source|Test 2.0 usage/line|
|---|---|---|---|---|---|---|
|`player.rastan`|Rastan|PLAYER|—/—|retained player state / legal weapon grant state|record selector + PC090OJ program|`object:player.rastan` / 0|
|`weapon.sword`|Sword|PLAYER_WEAPON|—/—|retained player state / legal weapon grant state|record selector + PC090OJ program|`object:weapon.sword` / 0|
|`weapon.axe`|Axe|PLAYER_WEAPON|—/—|retained player state / legal weapon grant state|record selector + PC090OJ program|`object:weapon.axe` / 0|
|`weapon.hammer`|Hammer|PLAYER_WEAPON|—/—|retained player state / legal weapon grant state|record selector + PC090OJ program|`object:weapon.hammer` / 0|
|`weapon.fire_sword`|Fire Sword|PLAYER_WEAPON|—/—|retained player state / legal weapon grant state|record selector + PC090OJ program|`object:weapon.fire_sword` / 0|
|`enemy.field.family0`|Lizardman|ENEMY|0x004B/—|0x4A104 8-byte field schedule; 0x4A086|0x45684 family/round/variant/compositor selector|`usage:lizardman:bank0x36` / 1|
|`enemy.field.family1`|Chimera|ENEMY|0x00D0/—|0x4A104 8-byte field schedule; 0x4A086|0x45684 family/round/variant/compositor selector|`usage:chimera:bank0x34` / 0|
|`enemy.field.family2`|Green Sword Knight family|ENEMY|0x033E/—|0x4A104 8-byte field schedule; 0x4A086|0x45684 family/round/variant/compositor selector|`object:castle.green_sword_knight.r1.n3` / 0|
|`enemy.field.family3`|Four-Armed Insect|ENEMY|0x02E8/—|0x4A104 8-byte field schedule; 0x4A086|0x45684 family/round/variant/compositor selector|`usage:four_armed_insect:bank0x3A` / 1|
|`enemy.field.family4`|Horned field family|ENEMY|0x0420/—|0x4A104 8-byte field schedule; 0x4A086|0x45684 family/round/variant/compositor selector|`—` / —|
|`enemy.field.family5`|Field family 5|ENEMY|0x01CB/—|0x4A104 8-byte field schedule; 0x4A086|0x45684 family/round/variant/compositor selector|`—` / —|
|`enemy.field.family6`|Skeleton field family|ENEMY|0x03B3/—|0x4A104 8-byte field schedule; 0x4A086|0x45684 family/round/variant/compositor selector|`—` / —|
|`enemy.field.family7`|Field family 7|ENEMY|0x043A/—|0x4A104 8-byte field schedule; 0x4A086|0x45684 family/round/variant/compositor selector|`—` / —|
|`enemy.field.family8`|Family-8 Valkyrie / rope-state actor|ENEMY|0x0241/—|0x4A104 8-byte field schedule; 0x4A086|0x45684 family/round/variant/compositor selector|`object:castle.rope_climber.family8.r1` / 0|
|`enemy.field.family9`|Field family 9|ENEMY|0x06E2/—|0x4A104 8-byte field schedule; 0x4A086|0x45684 family/round/variant/compositor selector|`—` / —|
|`enemy.field.family10`|Field family 10|ENEMY|0x0889/—|0x4A104 8-byte field schedule; 0x4A086|0x45684 family/round/variant/compositor selector|`—` / —|
|`enemy.field.family11`|Serpent field family|ENEMY|0x0400/—|0x4A104 8-byte field schedule; 0x4A086|0x45684 family/round/variant/compositor selector|`—` / —|
|`enemy.small_bat`|Small Bat|ENEMY|0x0268/0x0B|0x4580C/0x45EFC scripted dispatch -> 0x45B18 fixed-slot group|embedded bank 0x3E|`usage:small_bat:bank0x3E` / 2|
|`enemy.large_bat`|Large Bat|ENEMY|0x03F6/0x0A|0x4580C/0x45EFC scripted dispatch -> 0x45B18 fixed-slot group|embedded bank 0x3E|`usage:large_bat:bank0x3E` / 2|
|`enemy.flying_demon`|Flying Demon|ENEMY|0x0129/0x08/0x09|0x45342 paired fixed-slot creator|embedded bank 0x35|`usage:flying_demon:bank0x35` / 1|
|`reward.kind01`|Gameplay Reward Kind 01|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind01` / 1|
|`reward.kind02`|Gameplay Reward Kind 02|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind02` / 0|
|`reward.kind03`|Gameplay Reward Kind 03|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind03` / 0|
|`reward.kind04`|Gameplay Reward Kind 04|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind04` / 0|
|`reward.kind05`|Gameplay Reward Kind 05|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind05` / 0|
|`reward.kind06`|Gameplay Reward Kind 06|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind06` / 2|
|`reward.kind07`|Gameplay Reward Kind 07|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind07` / 2|
|`reward.kind08`|Gameplay Reward Kind 08|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind08` / 0|
|`reward.kind09`|Gameplay Reward Kind 09|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind09` / 0|
|`reward.kind10`|Gameplay Reward Kind 10|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind10` / 2|
|`reward.kind11`|Gameplay Reward Kind 11|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind11` / 1|
|`reward.kind12`|Gameplay Reward Kind 12|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind12` / —|
|`reward.kind13`|Gameplay Reward Kind 13|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind13` / —|
|`reward.kind14`|Gameplay Reward Kind 14|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind14` / —|
|`reward.kind15`|Gameplay Reward Kind 15|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind15` / —|
|`reward.kind16`|Gameplay Reward Kind 16|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind16` / —|
|`reward.kind17`|Gameplay Reward Kind 17|GAMEPLAY_REWARD|0x0A5A/—|eligible ordinary enemy death; same record transforms at 0x40CCC|embedded line 0 (1-13) or line 3 (14-17)|`object:item.reward.kind17` / —|
|`effect.ordinary_death`|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73/—|actor lifecycle transform|effect program selector|`object:effect.item_drop_death` / 2|
|`effect.generic_burst`|Generic burst / impact|DEATH_EFFECT|0x0275/—|actor lifecycle transform|effect program selector|`—` / —|
|`effect.bat_death`|Bat death|DEATH_EFFECT|0x0275/—|actor lifecycle transform|effect program selector|`object:effect.bat_death` / 2|
|`boss.r1.body`|Round 1 Boss body|BOSS|0x061D/—|round-specific S3 boss state / component creator|boss-stage sprite-control bank|`object:boss.r1.body` / 1|
|`boss.r1.auxiliary`|Round 1 Boss auxiliary/projectile domain|BOSS_PROJECTILE|0x061D/—|round-specific S3 boss state / component creator|boss-stage sprite-control bank|`object:boss.r1.flying_daggers` / 1|
|`boss.r2.body`|Round 2 Boss body|BOSS|0x0753/—|round-specific S3 boss state / component creator|boss-stage sprite-control bank|`—` / —|
|`boss.r2.auxiliary`|Round 2 Boss auxiliary/projectile domain|BOSS_PROJECTILE|0x0753/—|round-specific S3 boss state / component creator|boss-stage sprite-control bank|`—` / —|
|`boss.r3.body`|Round 3 Boss body|BOSS|0x082C/—|round-specific S3 boss state / component creator|boss-stage sprite-control bank|`—` / —|
|`boss.r3.auxiliary`|Round 3 Boss auxiliary/projectile domain|BOSS_PROJECTILE|0x082C/—|round-specific S3 boss state / component creator|boss-stage sprite-control bank|`—` / —|
|`boss.r4.body`|Round 4 Boss body|BOSS|0x07BF/—|round-specific S3 boss state / component creator|boss-stage sprite-control bank|`—` / —|
|`boss.r4.auxiliary`|Round 4 Boss auxiliary/projectile domain|BOSS_PROJECTILE|0x07BF/—|round-specific S3 boss state / component creator|boss-stage sprite-control bank|`—` / —|
|`boss.r5.body`|Round 5 Boss body|BOSS|0x0988/—|round-specific S3 boss state / component creator|boss-stage sprite-control bank|`—` / —|
|`boss.r5.auxiliary`|Round 5 Boss auxiliary/projectile domain|BOSS_PROJECTILE|0x0988/—|round-specific S3 boss state / component creator|boss-stage sprite-control bank|`—` / —|
|`boss.r6.body`|Round 6 Boss body|BOSS|0x0B35/—|round-specific S3 boss state / component creator|boss-stage sprite-control bank|`—` / —|
|`boss.r6.auxiliary`|Round 6 Boss auxiliary/projectile domain|BOSS_PROJECTILE|0x0B35/—|round-specific S3 boss state / component creator|boss-stage sprite-control bank|`—` / —|
|`scripted.type0c`|Scripted type 0x0C|OTHER_GAMEPLAY|0x050B/0x0C|constructor exists; full round dispatcher/lifetime closure pending|UNRESOLVED|`object:scripted.type0c` / —|
|`scripted.type0d`|Scripted type 0x0D|OTHER_GAMEPLAY|0x0D5F/0x0D|constructor exists; full round dispatcher/lifetime closure pending|UNRESOLVED|`object:scripted.type0d` / —|
|`scripted.batch16`|Batch/swarm type 0x16|OTHER_GAMEPLAY|0x0D56/0x16|constructor exists; full round dispatcher/lifetime closure pending|UNRESOLVED|`object:scripted.batch16` / —|
|`effect.special019d`|Specialized death 0x019D|DEATH_EFFECT|0x019D/—|constructor exists; full round dispatcher/lifetime closure pending|UNRESOLVED|`object:effect.special019d` / —|
|`effect.special09dc`|Specialized death 0x09DC|DEATH_EFFECT|0x09DC/—|constructor exists; full round dispatcher/lifetime closure pending|UNRESOLVED|`object:effect.special09dc` / —|
## 9. Master 18-subround appearance matrix
Legend: `P` PROVEN_APPEARS; `C` CONDITIONAL_PROVEN; `A` PROVEN_ABSENT; `?` UNRESOLVED.

|Object|R1-S1|R1-S2|R1-S3|R2-S1|R2-S2|R2-S3|R3-S1|R3-S2|R3-S3|R4-S1|R4-S2|R4-S3|R5-S1|R5-S2|R5-S3|R6-S1|R6-S2|R6-S3|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|P|P|P|P|P|P|P|P|P|P|P|P|P|P|P|P|P|P|
|Sword|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|
|Axe|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|
|Hammer|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|
|Fire Sword|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|C|
|Lizardman|P|A|A|P|A|A|P|A|A|P|A|A|P|A|A|P|A|A|
|Chimera|P|A|A|P|A|A|P|A|A|P|A|A|P|A|A|P|P|A|
|Green Sword Knight family|A|P|A|A|P|A|A|P|A|A|P|A|A|P|A|P|P|A|
|Four-Armed Insect|P|A|A|P|A|A|P|A|A|P|A|A|P|A|A|P|P|A|
|Horned field family|A|A|A|P|A|A|P|A|A|A|A|A|P|A|A|P|A|A|
|Field family 5|A|A|A|A|P|A|A|P|A|A|P|A|A|P|A|A|P|A|
|Skeleton field family|A|A|A|A|A|A|P|A|A|P|A|A|P|P|A|P|A|A|
|Field family 7|A|A|A|A|A|A|A|A|A|A|A|A|P|A|A|A|A|A|
|Family-8 Valkyrie / rope-state actor|P|A|A|P|A|A|P|A|A|P|A|A|A|A|A|A|A|A|
|Field family 9|A|A|A|A|A|A|A|A|A|P|A|A|A|A|A|A|A|A|
|Field family 10|A|A|A|A|A|A|A|A|A|P|A|A|P|A|A|P|A|A|
|Serpent field family|A|A|A|P|A|A|P|A|A|P|A|A|P|A|A|P|A|A|
|Small Bat|C|C|A|C|C|A|?|?|?|?|?|?|?|?|?|?|?|?|
|Large Bat|C|C|A|A|A|A|?|?|?|?|?|?|?|?|?|?|?|?|
|Flying Demon|C|?|A|C|?|A|?|?|?|?|?|?|?|?|?|?|?|?|
|Gameplay Reward Kind 01|C|A|A|C|A|A|A|A|A|C|A|A|A|C|A|C|A|A|
|Gameplay Reward Kind 02|C|A|A|C|A|A|C|A|A|C|A|A|C|A|A|C|C|A|
|Gameplay Reward Kind 03|C|C|A|A|A|A|C|A|A|C|A|A|C|C|A|C|A|A|
|Gameplay Reward Kind 04|A|C|A|A|A|A|A|C|A|A|A|A|A|A|A|C|A|A|
|Gameplay Reward Kind 05|A|A|A|C|A|A|A|A|A|C|A|A|A|C|A|A|A|A|
|Gameplay Reward Kind 06|C|C|A|C|A|A|C|A|A|C|A|A|C|A|A|C|A|A|
|Gameplay Reward Kind 07|C|A|A|C|C|A|C|A|A|C|A|A|C|A|A|C|A|A|
|Gameplay Reward Kind 08|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|
|Gameplay Reward Kind 09|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|
|Gameplay Reward Kind 10|A|A|A|C|C|A|C|C|A|C|C|A|C|C|A|C|C|A|
|Gameplay Reward Kind 11|C|C|A|A|C|A|C|A|A|C|A|A|A|C|A|C|C|A|
|Gameplay Reward Kind 12|C|A|A|C|A|A|C|C|A|C|A|A|C|A|A|C|A|A|
|Gameplay Reward Kind 13|A|C|A|C|A|A|A|A|A|C|C|A|C|A|A|C|C|A|
|Gameplay Reward Kind 14|C|A|A|C|A|A|C|A|A|C|A|A|A|A|A|C|A|A|
|Gameplay Reward Kind 15|C|A|A|A|C|A|A|C|A|C|C|A|C|A|A|C|A|A|
|Gameplay Reward Kind 16|A|A|A|A|A|A|C|A|A|A|A|A|A|A|A|A|C|A|
|Gameplay Reward Kind 17|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|
|Ordinary enemy death / item-drop transition|C|C|A|C|C|A|C|C|A|C|C|A|C|C|A|C|C|A|
|Generic burst / impact|C|C|A|C|C|A|C|C|A|C|C|A|C|C|A|C|C|A|
|Bat death|C|C|A|C|C|A|C|C|A|C|C|A|C|C|A|C|C|A|
|Round 1 Boss body|A|A|P|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|
|Round 1 Boss auxiliary/projectile domain|A|A|C|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|
|Round 2 Boss body|A|A|A|A|A|P|A|A|A|A|A|A|A|A|A|A|A|A|
|Round 2 Boss auxiliary/projectile domain|A|A|A|A|A|C|A|A|A|A|A|A|A|A|A|A|A|A|
|Round 3 Boss body|A|A|A|A|A|A|A|A|P|A|A|A|A|A|A|A|A|A|
|Round 3 Boss auxiliary/projectile domain|A|A|A|A|A|A|A|A|C|A|A|A|A|A|A|A|A|A|
|Round 4 Boss body|A|A|A|A|A|A|A|A|A|A|A|P|A|A|A|A|A|A|
|Round 4 Boss auxiliary/projectile domain|A|A|A|A|A|A|A|A|A|A|A|C|A|A|A|A|A|A|
|Round 5 Boss body|A|A|A|A|A|A|A|A|A|A|A|A|A|A|P|A|A|A|
|Round 5 Boss auxiliary/projectile domain|A|A|A|A|A|A|A|A|A|A|A|A|A|A|C|A|A|A|
|Round 6 Boss body|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|P|
|Round 6 Boss auxiliary/projectile domain|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|A|C|
|Scripted type 0x0C|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|
|Scripted type 0x0D|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|
|Batch/swarm type 0x16|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|
|Specialized death 0x019D|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|
|Specialized death 0x09DC|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|?|
## 10. R1-S1 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|0,15|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|0,15|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|0,15|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|0,15|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|0,15|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Lizardman|ENEMY|0x004B / —|0x4A104 8-byte field schedule; 0x4A086|0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Chimera|ENEMY|0x00D0 / —|0x4A104 8-byte field schedule; 0x4A086|4,5,6,7,8,9,10,11,12,13,14,15|no|0x45684 family/round/variant/compositor selector|0|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Four-Armed Insect|ENEMY|0x02E8 / —|0x4A104 8-byte field schedule; 0x4A086|2,3,4,5,6,7,8,9,10,11,12,13,14,15|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Family-8 Valkyrie / rope-state actor|ENEMY|0x0241 / —|0x4A104 8-byte field schedule; 0x4A086|6,7|no|0x45684 family/round/variant/compositor selector|0|CONFLATED_IDENTITY|CONFLATED_IDENTITY|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Small Bat|ENEMY|0x0268 / 0x0B|0x4580C/0x45EFC scripted dispatch -> 0x45B18 fixed-slot group|1,4,8,12|yes|embedded bank 0x3E|2|TOO_BROAD|TOO_BROAD|0x4580C progression branches -> 0x45B18; round 1 selects type 0x0A and 0x0B|
|Large Bat|ENEMY|0x03F6 / 0x0A|0x4580C/0x45EFC scripted dispatch -> 0x45B18 fixed-slot group|1,4,8,12|yes|embedded bank 0x3E|2|TOO_BROAD|TOO_BROAD|0x4580C progression branches -> 0x45B18; round 1 selects type 0x0A and 0x0B|
|Flying Demon|ENEMY|0x0129 / 0x08/0x09|0x45342 paired fixed-slot creator|8,12|yes|embedded bank 0x35|1|TOO_NARROW|TOO_NARROW|dispatcher -> 0x45342 paired creator|
|Gameplay Reward Kind 01|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|0,1,2,3,6,7,10,11|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 02|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|2,3,10,11|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 03|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|4,5,10,11|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 06|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|8,9,14,15|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 07|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|14,15|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 11|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|8,9|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 12|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|4,5|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 14|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|6,7|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 15|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|12,13|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73 / —|actor lifecycle transform|0,15|yes|effect program selector|2|CORRECT|CORRECT|legal field enemy lifecycle; 0x40CCC/actor behavior C|
|Generic burst / impact|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|0,15|yes|effect program selector|unresolved|MISSING|CORRECT|legal damage/effect producer lifecycle; 0x40CCC/actor behavior C|
|Bat death|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|0,15|yes|effect program selector|2|CORRECT|CORRECT|legal Small or Large Bat lifecycle; 0x40CCC/actor behavior C|
## 11. R1-S2 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|16,21|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|16,21|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|16,21|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|16,21|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|16,21|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Green Sword Knight family|ENEMY|0x033E / —|0x4A104 8-byte field schedule; 0x4A086|16,17,18,19,20,21|no|0x45684 family/round/variant/compositor selector|0|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Small Bat|ENEMY|0x0268 / 0x0B|0x4580C/0x45EFC scripted dispatch -> 0x45B18 fixed-slot group|16|yes|embedded bank 0x3E|2|TOO_BROAD|TOO_BROAD|0x4580C progression branches -> 0x45B18; round 1 selects type 0x0A and 0x0B|
|Large Bat|ENEMY|0x03F6 / 0x0A|0x4580C/0x45EFC scripted dispatch -> 0x45B18 fixed-slot group|16|yes|embedded bank 0x3E|2|TOO_BROAD|TOO_BROAD|0x4580C progression branches -> 0x45B18; round 1 selects type 0x0A and 0x0B|
|Gameplay Reward Kind 03|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|18,19|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 04|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|16,17|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 06|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|16,17,20,21|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 11|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|16,17|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 13|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|18,19|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73 / —|actor lifecycle transform|16,21|yes|effect program selector|2|CORRECT|CORRECT|legal field enemy lifecycle; 0x40CCC/actor behavior C|
|Generic burst / impact|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|16,21|yes|effect program selector|unresolved|MISSING|CORRECT|legal damage/effect producer lifecycle; 0x40CCC/actor behavior C|
|Bat death|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|16,21|yes|effect program selector|2|CORRECT|CORRECT|legal Small or Large Bat lifecycle; 0x40CCC/actor behavior C|
## 12. R1-S3 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|22,22|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|22,22|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|22,22|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|22,22|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|22,22|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Round 1 Boss body|BOSS|0x061D / —|round-specific S3 boss state / component creator|22|no|boss-stage sprite-control bank|1|CORRECT|CORRECT|record-type templates 0x45592; round boss creator/component path|
|Round 1 Boss auxiliary/projectile domain|BOSS_PROJECTILE|0x061D / —|round-specific S3 boss state / component creator|22|yes|boss-stage sprite-control bank|1|CORRECT|TOO_NARROW|record-type templates 0x45592; round boss creator/component path|
## 13. R2-S1 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|23,38|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|23,38|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|23,38|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|23,38|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|23,38|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Lizardman|ENEMY|0x004B / —|0x4A104 8-byte field schedule; 0x4A086|23,24,25,26,27,28,31,32,33,34,35,36,37,38|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Chimera|ENEMY|0x00D0 / —|0x4A104 8-byte field schedule; 0x4A086|29,30,31,32,33,34,37,38|no|0x45684 family/round/variant/compositor selector|0|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Four-Armed Insect|ENEMY|0x02E8 / —|0x4A104 8-byte field schedule; 0x4A086|25,26,27,28,29,30,31,32,35,36,37,38|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Horned field family|ENEMY|0x0420 / —|0x4A104 8-byte field schedule; 0x4A086|27,28,35,36|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Family-8 Valkyrie / rope-state actor|ENEMY|0x0241 / —|0x4A104 8-byte field schedule; 0x4A086|29,30,33,34|no|0x45684 family/round/variant/compositor selector|0|CONFLATED_IDENTITY|CONFLATED_IDENTITY|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Serpent field family|ENEMY|0x0400 / —|0x4A104 8-byte field schedule; 0x4A086|23,24,25,26,27,28,29,30,31,32,33,34,35,36|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Small Bat|ENEMY|0x0268 / 0x0B|0x4580C/0x45EFC scripted dispatch -> 0x45B18 fixed-slot group|25,29,32,34,36,37|yes|embedded bank 0x3E|2|TOO_BROAD|TOO_BROAD|0x45EFC -> 0x45B18 always creates type 0x0B|
|Flying Demon|ENEMY|0x0129 / 0x08/0x09|0x45342 paired fixed-slot creator|26,29,33,36|yes|embedded bank 0x35|1|TOO_NARROW|TOO_NARROW|dispatcher -> 0x45342 paired creator|
|Gameplay Reward Kind 01|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|23,24|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 02|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|23,24|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 05|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|27,28|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 06|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|37,38|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 07|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|29,30,33,34,37,38|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 10|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|31,32,35,36|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 12|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|29,30|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 13|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|33,34|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 14|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|25,26|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73 / —|actor lifecycle transform|23,38|yes|effect program selector|2|CORRECT|CORRECT|legal field enemy lifecycle; 0x40CCC/actor behavior C|
|Generic burst / impact|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|23,38|yes|effect program selector|unresolved|MISSING|CORRECT|legal damage/effect producer lifecycle; 0x40CCC/actor behavior C|
|Bat death|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|23,38|yes|effect program selector|2|CORRECT|CORRECT|legal Small or Large Bat lifecycle; 0x40CCC/actor behavior C|
## 14. R2-S2 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|39,44|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|39,44|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|39,44|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|39,44|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|39,44|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Green Sword Knight family|ENEMY|0x033E / —|0x4A104 8-byte field schedule; 0x4A086|39,40,41,42,43,44|no|0x45684 family/round/variant/compositor selector|0|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Field family 5|ENEMY|0x01CB / —|0x4A104 8-byte field schedule; 0x4A086|39,40,43,44|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Small Bat|ENEMY|0x0268 / 0x0B|0x4580C/0x45EFC scripted dispatch -> 0x45B18 fixed-slot group|41|yes|embedded bank 0x3E|2|TOO_BROAD|TOO_BROAD|0x45EFC -> 0x45B18 always creates type 0x0B|
|Gameplay Reward Kind 07|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|41,42|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 10|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|43,44|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 11|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|41,42|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 15|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|41,42|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73 / —|actor lifecycle transform|39,44|yes|effect program selector|2|CORRECT|CORRECT|legal field enemy lifecycle; 0x40CCC/actor behavior C|
|Generic burst / impact|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|39,44|yes|effect program selector|unresolved|MISSING|CORRECT|legal damage/effect producer lifecycle; 0x40CCC/actor behavior C|
|Bat death|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|39,44|yes|effect program selector|2|CORRECT|CORRECT|legal Small or Large Bat lifecycle; 0x40CCC/actor behavior C|
## 15. R2-S3 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|45,45|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|45,45|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|45,45|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|45,45|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|45,45|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Round 2 Boss body|BOSS|0x0753 / —|round-specific S3 boss state / component creator|45|no|boss-stage sprite-control bank|unresolved|MISSING|CORRECT|record-type templates 0x45592; round boss creator/component path|
|Round 2 Boss auxiliary/projectile domain|BOSS_PROJECTILE|0x0753 / —|round-specific S3 boss state / component creator|45|yes|boss-stage sprite-control bank|unresolved|MISSING|TOO_NARROW|record-type templates 0x45592; round boss creator/component path|
## 16. R3-S1 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|46,61|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|46,61|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|46,61|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|46,61|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|46,61|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Lizardman|ENEMY|0x004B / —|0x4A104 8-byte field schedule; 0x4A086|46,47,54,55,58,59|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Chimera|ENEMY|0x00D0 / —|0x4A104 8-byte field schedule; 0x4A086|46,47,52,53,54,55,56,57,60,61|no|0x45684 family/round/variant/compositor selector|0|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Four-Armed Insect|ENEMY|0x02E8 / —|0x4A104 8-byte field schedule; 0x4A086|48,49,50,51,56,57,60,61|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Horned field family|ENEMY|0x0420 / —|0x4A104 8-byte field schedule; 0x4A086|48,49,50,51,52,53,56,57|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Skeleton field family|ENEMY|0x03B3 / —|0x4A104 8-byte field schedule; 0x4A086|50,51,52,53,58,59|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Family-8 Valkyrie / rope-state actor|ENEMY|0x0241 / —|0x4A104 8-byte field schedule; 0x4A086|56,57,60,61|no|0x45684 family/round/variant/compositor selector|0|CONFLATED_IDENTITY|CONFLATED_IDENTITY|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Serpent field family|ENEMY|0x0400 / —|0x4A104 8-byte field schedule; 0x4A086|50,51,52,53,54,55,56,57,58,59|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Gameplay Reward Kind 02|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|54,55|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 03|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|50,51,58,59|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 06|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|52,53|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 07|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|54,55,60,61|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 10|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|56,57|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 11|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|46,47|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 12|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|56,57|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 14|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|48,49|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 16|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|58,59|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73 / —|actor lifecycle transform|46,61|yes|effect program selector|2|CORRECT|CORRECT|legal field enemy lifecycle; 0x40CCC/actor behavior C|
|Generic burst / impact|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|46,61|yes|effect program selector|unresolved|MISSING|CORRECT|legal damage/effect producer lifecycle; 0x40CCC/actor behavior C|
|Bat death|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|46,61|yes|effect program selector|2|CORRECT|CORRECT|legal Small or Large Bat lifecycle; 0x40CCC/actor behavior C|
## 17. R3-S2 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|62,67|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|62,67|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|62,67|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|62,67|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|62,67|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Green Sword Knight family|ENEMY|0x033E / —|0x4A104 8-byte field schedule; 0x4A086|62,63,64,65,66,67|no|0x45684 family/round/variant/compositor selector|0|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Field family 5|ENEMY|0x01CB / —|0x4A104 8-byte field schedule; 0x4A086|66,67|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Gameplay Reward Kind 04|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|64,65|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 10|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|66,67|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 12|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|64,65|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 15|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|62,63|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73 / —|actor lifecycle transform|62,67|yes|effect program selector|2|CORRECT|CORRECT|legal field enemy lifecycle; 0x40CCC/actor behavior C|
|Generic burst / impact|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|62,67|yes|effect program selector|unresolved|MISSING|CORRECT|legal damage/effect producer lifecycle; 0x40CCC/actor behavior C|
|Bat death|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|62,67|yes|effect program selector|2|CORRECT|CORRECT|legal Small or Large Bat lifecycle; 0x40CCC/actor behavior C|
## 18. R3-S3 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|68,68|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|68,68|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|68,68|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|68,68|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|68,68|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Round 3 Boss body|BOSS|0x082C / —|round-specific S3 boss state / component creator|68|no|boss-stage sprite-control bank|unresolved|MISSING|CORRECT|record-type templates 0x45592; round boss creator/component path|
|Round 3 Boss auxiliary/projectile domain|BOSS_PROJECTILE|0x082C / —|round-specific S3 boss state / component creator|68|yes|boss-stage sprite-control bank|unresolved|MISSING|TOO_NARROW|record-type templates 0x45592; round boss creator/component path|
## 19. R4-S1 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|69,84|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|69,84|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|69,84|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|69,84|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|69,84|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Lizardman|ENEMY|0x004B / —|0x4A104 8-byte field schedule; 0x4A086|69,70,71,72,73,74,75,76,77,78,79,80,83,84|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Chimera|ENEMY|0x00D0 / —|0x4A104 8-byte field schedule; 0x4A086|69,70,73,74,81,82,83,84|no|0x45684 family/round/variant/compositor selector|0|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Four-Armed Insect|ENEMY|0x02E8 / —|0x4A104 8-byte field schedule; 0x4A086|69,70,71,72,75,76,77,78,79,80,81,82,83,84|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Skeleton field family|ENEMY|0x03B3 / —|0x4A104 8-byte field schedule; 0x4A086|71,72,75,76,77,78,79,80,81,82,83,84|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Family-8 Valkyrie / rope-state actor|ENEMY|0x0241 / —|0x4A104 8-byte field schedule; 0x4A086|69,70,73,74,77,78|no|0x45684 family/round/variant/compositor selector|0|CONFLATED_IDENTITY|CONFLATED_IDENTITY|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Field family 9|ENEMY|0x06E2 / —|0x4A104 8-byte field schedule; 0x4A086|73,74,83,84|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Field family 10|ENEMY|0x0889 / —|0x4A104 8-byte field schedule; 0x4A086|77,78,81,82|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Serpent field family|ENEMY|0x0400 / —|0x4A104 8-byte field schedule; 0x4A086|79,80,81,82|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Gameplay Reward Kind 01|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|71,72|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 02|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|71,72,77,78|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 03|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|69,70|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 05|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|81,82|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 06|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|75,76|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 07|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|73,74,75,76|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 10|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|79,80,83,84|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 11|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|83,84|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 12|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|77,78|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 13|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|69,70,73,74|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 14|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|73,74|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 15|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|79,80|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73 / —|actor lifecycle transform|69,84|yes|effect program selector|2|CORRECT|CORRECT|legal field enemy lifecycle; 0x40CCC/actor behavior C|
|Generic burst / impact|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|69,84|yes|effect program selector|unresolved|MISSING|CORRECT|legal damage/effect producer lifecycle; 0x40CCC/actor behavior C|
|Bat death|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|69,84|yes|effect program selector|2|CORRECT|CORRECT|legal Small or Large Bat lifecycle; 0x40CCC/actor behavior C|
## 20. R4-S2 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|85,90|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|85,90|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|85,90|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|85,90|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|85,90|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Green Sword Knight family|ENEMY|0x033E / —|0x4A104 8-byte field schedule; 0x4A086|85,86,87,88,89,90|no|0x45684 family/round/variant/compositor selector|0|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Field family 5|ENEMY|0x01CB / —|0x4A104 8-byte field schedule; 0x4A086|85,86,89,90|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Gameplay Reward Kind 10|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|87,88|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 13|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|85,86|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 15|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|85,86,89,90|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73 / —|actor lifecycle transform|85,90|yes|effect program selector|2|CORRECT|CORRECT|legal field enemy lifecycle; 0x40CCC/actor behavior C|
|Generic burst / impact|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|85,90|yes|effect program selector|unresolved|MISSING|CORRECT|legal damage/effect producer lifecycle; 0x40CCC/actor behavior C|
|Bat death|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|85,90|yes|effect program selector|2|CORRECT|CORRECT|legal Small or Large Bat lifecycle; 0x40CCC/actor behavior C|
## 21. R4-S3 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|91,91|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|91,91|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|91,91|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|91,91|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|91,91|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Round 4 Boss body|BOSS|0x07BF / —|round-specific S3 boss state / component creator|91|no|boss-stage sprite-control bank|unresolved|MISSING|CORRECT|record-type templates 0x45592; round boss creator/component path|
|Round 4 Boss auxiliary/projectile domain|BOSS_PROJECTILE|0x07BF / —|round-specific S3 boss state / component creator|91|yes|boss-stage sprite-control bank|unresolved|MISSING|TOO_NARROW|record-type templates 0x45592; round boss creator/component path|
## 22. R5-S1 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|92,107|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|92,107|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|92,107|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|92,107|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|92,107|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Lizardman|ENEMY|0x004B / —|0x4A104 8-byte field schedule; 0x4A086|92,93,96,97,98,99,100,101,104,105|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Chimera|ENEMY|0x00D0 / —|0x4A104 8-byte field schedule; 0x4A086|92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107|no|0x45684 family/round/variant/compositor selector|0|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Four-Armed Insect|ENEMY|0x02E8 / —|0x4A104 8-byte field schedule; 0x4A086|92,93,98,99,100,101,102,103,104,105,106,107|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Horned field family|ENEMY|0x0420 / —|0x4A104 8-byte field schedule; 0x4A086|94,95,96,97|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Skeleton field family|ENEMY|0x03B3 / —|0x4A104 8-byte field schedule; 0x4A086|94,95,96,97,102,103,106,107|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Field family 7|ENEMY|0x043A / —|0x4A104 8-byte field schedule; 0x4A086|94,95,102,103|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Field family 10|ENEMY|0x0889 / —|0x4A104 8-byte field schedule; 0x4A086|98,99,104,105|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Serpent field family|ENEMY|0x0400 / —|0x4A104 8-byte field schedule; 0x4A086|94,95,96,97,100,101,106,107|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Gameplay Reward Kind 02|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|92,93,104,105|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 03|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|98,99,104,105|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 06|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|102,103|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 07|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|96,97|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 10|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|98,99,106,107|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 12|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|100,101|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 13|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|106,107|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 15|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|100,101|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73 / —|actor lifecycle transform|92,107|yes|effect program selector|2|CORRECT|CORRECT|legal field enemy lifecycle; 0x40CCC/actor behavior C|
|Generic burst / impact|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|92,107|yes|effect program selector|unresolved|MISSING|CORRECT|legal damage/effect producer lifecycle; 0x40CCC/actor behavior C|
|Bat death|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|92,107|yes|effect program selector|2|CORRECT|CORRECT|legal Small or Large Bat lifecycle; 0x40CCC/actor behavior C|
## 23. R5-S2 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|108,113|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|108,113|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|108,113|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|108,113|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|108,113|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Green Sword Knight family|ENEMY|0x033E / —|0x4A104 8-byte field schedule; 0x4A086|108,109,110,111,112,113|no|0x45684 family/round/variant/compositor selector|0|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Field family 5|ENEMY|0x01CB / —|0x4A104 8-byte field schedule; 0x4A086|110,111,112,113|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Skeleton field family|ENEMY|0x03B3 / —|0x4A104 8-byte field schedule; 0x4A086|108,109|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Gameplay Reward Kind 01|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|108,109|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 03|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|112,113|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 05|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|108,109|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 10|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|110,111|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 11|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|108,109|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73 / —|actor lifecycle transform|108,113|yes|effect program selector|2|CORRECT|CORRECT|legal field enemy lifecycle; 0x40CCC/actor behavior C|
|Generic burst / impact|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|108,113|yes|effect program selector|unresolved|MISSING|CORRECT|legal damage/effect producer lifecycle; 0x40CCC/actor behavior C|
|Bat death|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|108,113|yes|effect program selector|2|CORRECT|CORRECT|legal Small or Large Bat lifecycle; 0x40CCC/actor behavior C|
## 24. R5-S3 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|114,114|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|114,114|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|114,114|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|114,114|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|114,114|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Round 5 Boss body|BOSS|0x0988 / —|round-specific S3 boss state / component creator|114|no|boss-stage sprite-control bank|unresolved|MISSING|CORRECT|record-type templates 0x45592; round boss creator/component path|
|Round 5 Boss auxiliary/projectile domain|BOSS_PROJECTILE|0x0988 / —|round-specific S3 boss state / component creator|114|yes|boss-stage sprite-control bank|unresolved|MISSING|TOO_NARROW|record-type templates 0x45592; round boss creator/component path|
## 25. R6-S1 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|115,130|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|115,130|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|115,130|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|115,130|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|115,130|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Lizardman|ENEMY|0x004B / —|0x4A104 8-byte field schedule; 0x4A086|115,116,119,120|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Chimera|ENEMY|0x00D0 / —|0x4A104 8-byte field schedule; 0x4A086|115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130|no|0x45684 family/round/variant/compositor selector|0|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Green Sword Knight family|ENEMY|0x033E / —|0x4A104 8-byte field schedule; 0x4A086|125,126,127,128,129,130|no|0x45684 family/round/variant/compositor selector|0|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Four-Armed Insect|ENEMY|0x02E8 / —|0x4A104 8-byte field schedule; 0x4A086|115,116,119,120,121,122,123,124|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Horned field family|ENEMY|0x0420 / —|0x4A104 8-byte field schedule; 0x4A086|117,118,119,120,123,124|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Skeleton field family|ENEMY|0x03B3 / —|0x4A104 8-byte field schedule; 0x4A086|117,118,119,120,121,122,125,126,129,130|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Field family 10|ENEMY|0x0889 / —|0x4A104 8-byte field schedule; 0x4A086|115,116,121,122,125,126,127,128|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Serpent field family|ENEMY|0x0400 / —|0x4A104 8-byte field schedule; 0x4A086|117,118,123,124,125,126|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Gameplay Reward Kind 01|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|117,118|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 02|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|117,118|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 03|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|115,116,123,124|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 04|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|125,126|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 06|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|119,120|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 07|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|119,120|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 10|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|127,128|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 11|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|123,124|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 12|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|117,118|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 13|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|121,122,129,130|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 14|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|121,122|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 15|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|115,116|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73 / —|actor lifecycle transform|115,130|yes|effect program selector|2|CORRECT|CORRECT|legal field enemy lifecycle; 0x40CCC/actor behavior C|
|Generic burst / impact|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|115,130|yes|effect program selector|unresolved|MISSING|CORRECT|legal damage/effect producer lifecycle; 0x40CCC/actor behavior C|
|Bat death|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|115,130|yes|effect program selector|2|CORRECT|CORRECT|legal Small or Large Bat lifecycle; 0x40CCC/actor behavior C|
## 26. R6-S2 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|131,136|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|131,136|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|131,136|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|131,136|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|131,136|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Chimera|ENEMY|0x00D0 / —|0x4A104 8-byte field schedule; 0x4A086|131,132,133,134,135,136|no|0x45684 family/round/variant/compositor selector|0|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Green Sword Knight family|ENEMY|0x033E / —|0x4A104 8-byte field schedule; 0x4A086|131,132,133,134,135,136|no|0x45684 family/round/variant/compositor selector|0|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Four-Armed Insect|ENEMY|0x02E8 / —|0x4A104 8-byte field schedule; 0x4A086|131,132,133,134|no|0x45684 family/round/variant/compositor selector|1|CORRECT|CORRECT|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Field family 5|ENEMY|0x01CB / —|0x4A104 8-byte field schedule; 0x4A086|131,132,135,136|no|0x45684 family/round/variant/compositor selector|unresolved|TOO_NARROW|TOO_NARROW|0x4A104 schedule -> 0x4A086 installer -> 0x4544E template|
|Gameplay Reward Kind 02|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|131,132|yes|embedded line 0 (1-13) or line 3 (14-17)|0|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 10|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|133,134|yes|embedded line 0 (1-13) or line 3 (14-17)|2|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 11|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|131,132|yes|embedded line 0 (1-13) or line 3 (14-17)|1|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 13|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|133,134|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Gameplay Reward Kind 16|GAMEPLAY_REWARD|0x0A5A / —|eligible ordinary enemy death; same record transforms at 0x40CCC|131,132|yes|embedded line 0 (1-13) or line 3 (14-17)|unresolved|TOO_BROAD|TOO_BROAD|schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform|
|Ordinary enemy death / item-drop transition|DEATH_EFFECT|0x0A73 / —|actor lifecycle transform|131,136|yes|effect program selector|2|CORRECT|CORRECT|legal field enemy lifecycle; 0x40CCC/actor behavior C|
|Generic burst / impact|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|131,136|yes|effect program selector|unresolved|MISSING|CORRECT|legal damage/effect producer lifecycle; 0x40CCC/actor behavior C|
|Bat death|DEATH_EFFECT|0x0275 / —|actor lifecycle transform|131,136|yes|effect program selector|2|CORRECT|CORRECT|legal Small or Large Bat lifecycle; 0x40CCC/actor behavior C|
## 27. R6-S3 detailed roster
|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|
|---|---|---|---|---|---|---|---|---|---|---|
|Rastan|PLAYER|— / —|retained player state / legal weapon grant state|137,137|no|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|137,137|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Axe|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|137,137|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Hammer|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|137,137|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Fire Sword|PLAYER_WEAPON|— / —|retained player state / legal weapon grant state|137,137|yes|record selector + PC090OJ program|0|CORRECT|CORRECT|player/weapon retained state; rastan_player_weapon_state.c|
|Round 6 Boss body|BOSS|0x0B35 / —|round-specific S3 boss state / component creator|137|no|boss-stage sprite-control bank|unresolved|MISSING|CORRECT|record-type templates 0x45592; round boss creator/component path|
|Round 6 Boss auxiliary/projectile domain|BOSS_PROJECTILE|0x0B35 / —|round-specific S3 boss state / component creator|137|yes|boss-stage sprite-control bank|unresolved|MISSING|TOO_NARROW|record-type templates 0x45592; round boss creator/component path|
## 28. Small Bat proof
Type `$0B`, base `$0268`. `$4580C` reaches `$45B18` at Round-1 progression 2, 5, 9, 13, and 17 (conditional local thresholds); progression 17 is retained record 16, the R1-S2 entry. `$45B18` always creates the type-$0B slot. It is therefore conditional-proven in R1-S1 and R1-S2. `$45EFC` similarly proves R2-S1/S2 occurrences. Current `shared` metadata is too broad because it has no legal record set.
## 29. Large Bat proof
Type `$0A`, base `$03F6`, is created by the same `$45B18` group in Round 1, so it is conditional-proven in R1-S1 and R1-S2, including retained record 16. In Round 2, `$45B18` deliberately substitutes record type `$12` for `$0A`; therefore the Large Bat is proven absent from the R2 calls even though the Small Bat remains. This independent representation prevents the old Small/Large conflation.
## 30. Green Sword Knight proof
Family 2/base `$033E` is installed directly by `$4A086` from schedule `$4A104` across all six R1-S2 retained records 16–21 (progression `$11..$16`). The technical family is proven; the exact human pose names remain secondary. Test 2.0 maps the R1 knight object to Line 0.
## 31. Rope Climber proof
The current separate `object:castle.rope_climber.family8.r1` claim is not source-proven for R1-S2. Family 8/base `$0241` occurs in the Round-1 schedule only in outside records 6–7, not castle records 16–21. The R1-S2 screenshots show a rope-climbing pose, but source membership says it cannot be used to create a separate family-8 R1-S2 actor without another persistence/constructor path. The correct R1-S2 rope pose may belong to scheduled family 2; until that state identity is closed, the current metadata is `CONFLATED_IDENTITY`, and Andy must not preserve the family-8 R1-S2 listing as authority.
## 32. Blue Crystal proof
The arcade executable exposes 17 technical reward kinds, identity bytes, anims and codes, but no human string that identifies which kind is called “Blue Crystal.” R1-S2 legally permits kinds 3, 4, 6, 11 and 13 through schedule `+$36` and `$40CCC/$40D32`. Thus the collectible class and its R1-S2 legality are proven, while the Blue-Crystal→kind alias remains UNRESOLVED and must not be guessed from pixels. An enemy-only roster misses it because the dying enemy record transforms in place into family 12/base `$0A5A`.
## 33. All gameplay reward/item appearance rules
Each reward row in the matrix is computed from exact schedule byte `+$36`. Status is conditional because the owning enemy must be killed and the death path must reach the transform. Kinds 1–13 use embedded source line 0 and kinds 14–17 line 3; Test 2.0 may remap individual kinds differently. Human names remain unresolved.
## 34. Projectiles, children, and effects
Ordinary item-drop/death and generic/bat death are independent workload identities. The bat effect is base `$0275` anim `$A8`; generic burst uses `$0275` anim `$9D..$A0`; ordinary reward transition uses `$0A73` then `$0A5A`. Five constructor-visible technical domains remain `?` because this pass did not falsely promote an unclosed dispatcher to absence or universal membership.
## 35. Boss/boss-projectile appearance rules
Each boss body is constrained to the one S3 record of its round. Auxiliary/component/projectile domains are conditional in that same record and absent elsewhere. R1 body and flying-dagger mappings exist in Test 2.0; later boss mappings are missing from the current Composer authority.
## 36. Current Composer discrepancies
Object-level audit: 45 of 57 records are MISSING/TOO_BROAD/TOO_NARROW/CONFLATED (MISSING 16, TOO_BROAD 19, TOO_NARROW 9, CONFLATED 1); 12 are classified CORRECT at this granularity. Most serious: pending per-scene roster, bats without records, rewards marked shared, family-8 rope actor assigned to R1-S2, and later bosses/scripted identities absent.
## 37. Current bestiary discrepancies
Object-level audit: 40 of 57 records are MISSING/TOO_BROAD/TOO_NARROW/CONFLATED (MISSING 5, TOO_BROAD 19, TOO_NARROW 15, CONFLATED 1); 17 are CORRECT at this granularity. The bestiary contains valuable technical identities but is not a complete spawn matrix.
## 38. Current Test 2.0 / Build-0573 Genesis mapping cross-reference
The identity table records exact Test 2.0 usage IDs and lines when a matching key exists. The manifest separately marks `PROVEN_GENERATOR_KEY` only where the current offline generator contains that exact usage key; all others are `NOT_PROVEN_BY_CURRENT_GENERATOR`. The generator explicitly consumes player, four weapons, Lizardman, Chimera, Four-Armed Insect, Flying Demon, Small Bat, Large Bat, and R1 Green Sword Knight. It does not consume the reward-kind keys or the family-8 rope key. Crucially, R1-S2-legal reward kind 11 is mapped to Line 1 in Test 2.0 but is not proven consumed by Build 0573's current generator—mapping existence and production consumption are distinct.
## 39. Palette Composer v0.4/versioning audit
`index.html` supplies the visible version; `app.js` and `server.py` also use `v0.4` as profile schema. The tool has since gained contexts, per-scene packages, object domains, local overrides, validation, and many specialized rosters without separating application release from data schema. Andy should introduce independent fields such as application `0.5.0` (or `1.0.0` after the authority integration), profile schema `palette-profile/v1`, and appearance-manifest schema `pc090oj-subround-appearance/v1`, with explicit migration. No version was changed here.
## 40. Machine-readable manifest schema/path/SHA
Path: `analysis/graphics_optimizer/pc090oj_subround_appearance_manifest.json`. Schema `pc090oj-subround-appearance/v1`. SHA-256 `6137deaa10f17039e27e072a4d56af40c68dfc8fc384a3a7fb869420d618a45f`. Generator: `tools/analysis/build_pc090oj_subround_appearance_manifest.py`.
Artifact validation PASS: 57 objects × 18 cells, allowed status vocabulary, evidence on every P/C cell, separate Small/Large Bat identities, 49 report sections, report/manifest matrix agreement, Python compile, selected new-C syntax, and byte-identical regeneration. Repository-wide legacy decompilation guards are not clean at this starting state: coverage already reports six older COMPLETE rows without raw files; fidelity reports the older `raw/00047004.c` annotation gap; whole-tree C syntax has older airborne/attract reconstruction errors. Those pre-existing failures were not hidden or repaired outside this task.
## 41. Remaining unresolved identities/appearances
Eight object records retain at least one `UNRESOLVED` cell: Small Bat, Large Bat, Flying Demon, and five technical scripted/effect domains. Later-round scripted dispatchers must be decompiled before those cells can become P/C/A. Reward human names—including Blue Crystal—also remain unresolved aliases even where technical kinds are exact.
## 42. Impact on historical PROMT-ID-0151
0151’s Line-1 capacity conclusion is contradicted by the corrected roster: reward kind 11 can legally appear in R1-S2 and Test 2.0 maps it to Line 1. The prior roster also omitted conditional bats, although their current mapping is Line 2. Therefore 0151 cannot authorize the fire pit on Line 1 until reward identity/residency and all remaining conditional R1-S2 objects are included. No fire-pit decision is made here.
## 43. Exact instructions for Andy’s subsequent correction task
Consume this JSON as the sole appearance input; keep identity/graphics/palette/Genesis mapping/subround/record facts separate; render P/C/A/? explicitly; replace `field_phase1` and `shared` roster shortcuts with manifest membership; preserve authored palette mappings; remove the family-8 R1-S2 rope assertion pending a proven path; expose reward kinds 3/4/6/11/13 in R1-S2; add record-window UI; migrate app and schema versions independently; update bestiary from the same manifest; never convert `?` to absent.
## 44. Production source changed
NONE.
## 45. Palette Composer changed
NONE.
## 46. Bestiary changed
NONE.
## 47. Test 2.0 changed
NONE.
## 48. ROM produced
NONE.
## 49. Build number consumed
NONE.
TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0154
