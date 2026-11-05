TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0090

# Build 0539 R1-S2/R1-S3 Runtime-Asset and Palette-Composer Handoff

## TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0090 Result

Build 0539 is **not accepted**. Tighe's GENESIS/BlastEm gameplay evidence proves that Plane-A stale
rows remain. The Build-0539 regression proved only the `N-32` alias at the downward visible edge; it
did not prove the whole scrolling system correct.

This source-only audit found four independent defects:

1. R1-S3's authored Palette Composer asset is generated, but production packages only the R1-S1 and
   R1-S2 assets. Stage 22 selects asset zero, so R1-S3 never installs its authored palette.
2. The gray backdrop is CRAM Line 0 entry 0 = `0x0888`, installed by the per-scene palette loader,
   while VDP register 7 correctly selects Line 0 entry 0. The required value is **BLACK (`0x0000`)**.
3. The claimed Green Sword Knight `29 programs / 109 codes` domain combines several unrelated
   `(base, program)` identities. Base `$033E` has 23 proven programs / 97 codes. The family-8 rope
   climber is base `$0241`, not `$033E`.
4. The 17 rewards are present in the Composer under incorrect palette groups and are omitted from
   the production sprite reindex generator. Runtime therefore displays raw pixels through a bank-only
   palette route that does not consume the reward object mappings.

No production, Composer, Bestiary, profile, generated asset, trace, ROM, or build-counter file was
changed. Existing project tools and evidence were reused; no new trace infrastructure was created.

For later native corrections, the semantic cuts remain:

- PC080SN: retained arcade scene/row/tile-animation decision -> final Genesis name words and CRAM;
- PC090OJ: retained actor base/state/program/pieces -> final Genesis pattern residency and SAT.

The removed tails are chip-specific name-RAM/SAT realization, not gameplay state. No new shadow map,
object-RAM mirror, or runtime graphics conversion is proposed.

## Current Repository State

| Item | Audited value |
|---|---|
| Local HEAD | `658fa468d68a4cd44eb8cfd0fea39343757fde35` |
| Relevant local commits | `b6ab9d94` Plane-A edge; `a3dcdbad` Test update; `86c0d680` Build 0539; `658fa468` report/log |
| Build counter | `539` |
| Test profile | `analysis/graphics_optimizer/editor_policy/Test.json` |
| Test SHA-256 | `e03dd2aa24f30adb3fd0566af0b917914b49d8cd1533441431be485dd2d6b730` |
| R1-S2 CRAM asset | `281f9f38c8e58101f6c01aa5d5578605313949ea9e32e26f287355a19767c26d` |
| R1-S3 CRAM asset | `de710ffccf6834b28ab32c95af52525e132ba645a6efb1f7a3c8779511ee0ad7` |
| Test Lines 0 / 1 / 3 | `273ab974...` / `3cb995de...` / `637a34db...` |
| Reindexed PC090OJ region | `9ee677ab17fb9083e176b3ed7f12c60de8830cc4aeda2c7663bb233639305b39` |
| Raw preconverted PC090OJ region | `916c0dcfeac887f5532ac1f525580c8db15ccc5acd950974a0be3234ce7b239b` |
| Scene selector | `646b33f903988ebc05ae6b6fa794ca87a4458256f50d6ae02fa854b920fd4a91` |

At the final status check, two unrelated runtime-output files were modified concurrently:
`build/mame/home/rastanmon/rastan_monitor.log` and `tools/mame/cheat/output.json`. They were not read as
task authority, modified, staged, or reverted.

## Build 0539 Gameplay Failures

- **Plane A:** stale/repeated rows remain in R1-S2. Build 0539 is a failed complete-fix candidate.
- **Green actors:** wrong rope-domain generation is proven; broken/mispositioned pieces remain a
  separate unresolved production presentation defect.
- **Rewards:** wrong colors are expected from current production coverage and routing.
- **Hazards:** the R1-S2 visual subsets have not been bound to source tile/palette domains, so the
  Composer cannot author them as meaningful objects and production cannot verify their mappings.
- **R1-S3 Layer A:** authored colors stop at packaging/scene selection.
- **Backdrop:** scene assets install gray at the VDP-selected backdrop entry.

Evidence labels used below:

- **PROVEN**: original 68000 instructions/tables or current production source/artifact establishes it.
- **PARTIAL**: mechanism is proven but scene reachability, complete states, or visible coverage is not.
- **PENDING**: no source-backed identity is currently available.
- **TIGHE-VISUAL**: Tighe's GENESIS/BlastEm or original-arcade visual identification, not by itself a
  source address.

## Issue Ownership Matrix

| Issue | Owner | Reason / next responsibility |
|---|---|---|
| Remaining Plane-A stale rows | **Cody production** | Native residency/publication sequencing; obtain first-bad row history, then correct source. |
| Broken Green Sword Knight geometry | **Cody production** | Palette tools cannot move pieces; compare expected pieces -> queue -> shadow SAT -> VDP SAT. |
| Invalid 29/109 semantic object | **Andy research/tool** | Split base `$033E` and family-8/base-`$0241`; remove unrelated programs from previews and claims. |
| Rope-climber palette reversion | Shared: Andy model, Cody integration | Andy supplies correct object/domain; Cody adds generated tiles/route after Tighe mapping. |
| Reward object grouping/source palettes | **Andy research/tool** | Replace three false bank groups with 17 exact kind/program records and correct embedded lines. |
| Reward runtime pixels/route | **Cody production** | Add rewards to offline reindex/variant coverage and consume scene-local authored mappings. |
| Hazard identities/groups | **Andy research/tool** | Create honest scene-local Plane-A candidates; keep PENDING source subsets explicit. |
| Hazard final colors | **Tighe authored decision** | Only Tighe selects target colors after source palettes are exposed. |
| Hazard runtime integration | **Cody production** | Compile the approved semantic mappings; do not invent colors. |
| R1-S3 Layer-A colors | **Tighe authored decision** | Already present in Test; preserve unchanged. |
| R1-S3 asset packaging/activation | **Cody production** | Add third asset/pointer/dependency/selector and verify natural/direct entry. |
| R1-S3 Plane-B/Line-2 policy | Cody evidence + Andy UI + Tighe allocation | No reclamation until pixel-coverage proof; Tighe chooses use if later proven free. |
| Round-1 boss object cards | **Andy research/tool** | Add body and type-15 auxiliary context with honest pending palette content. |
| Boss runtime palette/integration | **Cody production** | Scene-local sprite palette package and runtime install after authored mapping. |
| Black backdrop | **Cody production bug — fix required** | Normalize scene-package Line 0 index 0 to `0x0000`; not an author color decision. |

## R1-S2 Complete Visible-Object Census

This census uses **37 authoring/evidence units**. Reward kinds are counted separately because they have
different programs, codes, identities, values, and potentially different mappings. A controller-only row
is included when it changes visible graphics. `+$27=0` means embedded compositor palette wins; bit 6 set
means the actor byte overrides every piece.

Common scene: Round 1 / Sub-Round 2, `PAL-R1-S2-PLANEA-CASTLE`.

| Display / canonical ID | Technical identity; creator; state | Program / comp / code domain | Palette provenance / `+$27` | Hardware | Composer / Bestiary | Evidence / confidence |
|---|---|---|---|---|---|---|
| Rastan / `object:player.rastan` | player record; retained player state machine | H24 body vocabulary; native player frame path | source bank `$33`; player path | PC090OJ | PRESENT_CORRECT / PRESENT_CORRECT | H24 tables; `pc090oj_hooks.s`; PROVEN |
| Sword / `object:weapon.sword` | player FRONT overlay | H24 sword cells | source `$33`; player-owned | PC090OJ | PRESENT_CORRECT / PRESENT_CORRECT | `h24_player_weapon_cells.tsv`; PROVEN |
| Axe / `object:weapon.axe` | player FRONT overlay | H24 axe cells | source `$33` | PC090OJ | PRESENT_CORRECT / PRESENT_CORRECT | H24; PROVEN |
| Hammer / `object:weapon.hammer` | player FRONT overlay | H24 hammer cells | source `$33` | PC090OJ | PRESENT_CORRECT / PRESENT_CORRECT | H24; PROVEN |
| Fire Sword / `object:weapon.fire_sword` | player FRONT plus phase table `$54688-$546A7` | complete H24 + animated substitute codes | source `$33` | PC090OJ | PRESENT_CORRECT / PRESENT_CORRECT | H24; PROVEN |
| Green Sword Knight / `object:castle.green_sword_knight.r1.n3` | base `$033E`, family 2; field installer/common actor engines; states normal, `$0D/$0E`, `$0F`, `$1F` | **23 programs / 97 codes**: `$20-$23,$71-$73,$93-$9C,$A1-$A6`; comp 0 | embedded nibbles vary; creation `+$27` may override. Do not flatten provenance. | PC090OJ | PRESENT_WRONG_IDENTITY+GEOMETRY / PRESENT_WRONG_IDENTITY | source engines `$42EF8,$4684E,$47140,$473B8`; compositor VM; PROVEN domain |
| Family-8 rope climber / `object:castle.rope_climber.family8.r1` | base `$0241`, family 8; state `$11` handler `$4684E` | `$56,$59,$5A`; comp 0; 31 codes (`$194-$197,$241-$26A`) | embedded programs; current `$033E` generated mapping is inapplicable | PC090OJ | MISSING / PRESENT_WRONG_IDENTITY (folded into knight) | `$4684E/$468C8`; VM; PROVEN technical identity, human label TIGHE-VISUAL |
| Small Bat / `object:enemy.small_bat` | base `$0268`, rec types 10/11; airborne engine | scene-reachable anim corpus; comp 0 | effective bank `$3E`; override retained where set | PC090OJ | PRESENT_WRONG_SCENE (hidden as field-only) / PRESENT_WRONG_SCENE | user gameplay + existing bat tables; scene reachability PARTIAL |
| Large Bat / `object:enemy.large_bat` | base `$03F6`, rec types 10/11 | scene-reachable anim corpus; comp 0 | bank `$3E` | PC090OJ | PRESENT_WRONG_SCENE / PRESENT_WRONG_SCENE | same; PARTIAL scene reachability |
| Ordinary enemy death / `object:effect.ordinary_enemy_death` | dying actor in place; `$40CCC` default; base `$0A73`, family retained | `$0B-$12`; comp 2 | owning actor palette/override | PC090OJ | PRESENT_CORRECT through owner / PRESENT_CORRECT | `raw/00040ccc.c`; PROVEN |
| Bat death / `object:effect.bat_death` | `$42ABC`; base `$0275` | `$A8`; comp 0 | embedded line 0 | PC090OJ | PRESENT_CORRECT / PRESENT_CORRECT | H25; PROVEN |
| M-marker burst / `object:effect.burst` | marker `$4D` -> state `$1B/$43ECC`; up to five independent children; base `$0275` | `$9D-$A0`; comp 0 | embedded line 0; `+$27=0` | PC090OJ | PRESENT_CORRECT / PRESENT_CORRECT | H16; PROVEN |
| Floor spikes / `object:hazard.r1s2.floor_spikes` | no R1-reachable `$09EA` chain; exact owning cells/state PENDING | R1-S2 Plane-A record corpus subset PENDING | source bank/subset PENDING | PC080SN Plane A or mixed | NOT_A_SPRITE; semantic object MISSING / R1 identity MISSING | `$09EA` is R5, not R1; H21/H14; TIGHE-VISUAL |
| Suspended/moving spike trap / `object:hazard.r1s2.moving_spiked_trap` | owner PENDING; keep separate from floor spikes | record 16-21 Plane-A subset PENDING | PENDING | PC080SN Plane A or mixed | NOT_A_SPRITE; MISSING / MISSING | no R1 `$09EA`; screenshots; PENDING |
| Moving wooden gate / `object:hazard.r1s2.moving_wood_gate` | not proven to be collision `$7E` exit | record 16-21 animated tile subset PENDING | PENDING | PC080SN Plane A or mixed | NOT_A_SPRITE; MISSING / MISSING | H24 `$7E` proves transition only, not this art; PENDING |
| Falling water / `object:hazard.r1s2.falling_water` | R1-S1 `$59AD4` mechanism must not be reused without link | record 16-21 tile/palette animation subset PENDING | PENDING; may include palette animation | PC080SN Plane A + palette animation (PARTIAL) | NOT_A_SPRITE; MISSING / MISSING | screenshot + absence of actor owner; PENDING |
| Animated pit flame / `object:hazard.r1s2.pit_flame_animation` | **not** base `$0224` (`$0224` is R2/R4) | record 16-21 tile/palette subset PENDING | PENDING | PC080SN Plane A / palette animation | NOT_A_SPRITE; MISSING / PRESENT_WRONG_SCENE if `$0224` reused | H14/H21; PENDING source subset |
| Static pit/lava field / `scene:r1s2.pit_lava_static` | scene map, not actor | record 16-21 Plane-A patterns | scene Layer-A banks | PC080SN Plane A | raw tiles PRESENT, semantic group MISSING / MISSING | subround corpus; PROVEN map ownership |
| Rope/chain terrain / `scene:r1s2.rope_terrain` | collision/map traversal; player state owner | Plane-A rope cells; no actor base | Layer-A scene banks | PC080SN Plane A + collision | raw tiles PRESENT, semantic group MISSING / PARTIAL | H21/H24; PROVEN non-sprite |
| Exit/door controller / `controller:r1s2.stage_exit` | collision `$7E` -> state 7 / `$542E8` | no independent proven art | N/A | controller + map | CONTROLLER_ONLY / CONTROLLER_ONLY | H22/H24; PROVEN controller |

### Rewards 1-17 (also R1-S2 census rows 13-29)

All are the same dying actor transformed in place by `$40CCC->$40D32`: family 12, base `$0A5A`,
compositor 2, clear override. The current three-group `$30/$31/$37` claim is disproven by the compositor
programs: kinds 1-13 use embedded line 0; kinds 14-17 use embedded line 3.

| Kind / canonical ID | Anim | Code | Identity byte | Value | Embedded line | Current status / required Andy action |
|---|---:|---:|---:|---:|---:|---|
| 1 / `object:item.reward.kind01` | `$13` | `$A5A` | `$17` | `$0010` | 0 | PRESENT_WRONG_PALETTE_SOURCE; make individual frame under reward parent |
| 2 / `object:item.reward.kind02` | `$14` | `$A5B` | `$18` | `$0020` | 0 | same |
| 3 / `object:item.reward.kind03` | `$15` | `$A5C` | `$19` | `$0030` | 0 | same |
| 4 / `object:item.reward.kind04` | `$16` | `$A5D` | `$12` | `$0100` | 0 | same |
| 5 / `object:item.reward.kind05` | `$17` | `$A5E` | `$13` | `$0200` | 0 | current false bank `$31`; correct to embedded line 0 |
| 6 / `object:item.reward.kind06` | `$18` | `$A5F` | `$14` | `$0010` | 0 | same |
| 7 / `object:item.reward.kind07` | `$19` | `$A60` | `$15` | `$0020` | 0 | same |
| 8 / `object:item.reward.kind08` | `$1A` | `$A61` | `$1D` | `$0020` | 0 | same |
| 9 / `object:item.reward.kind09` | `$1B` | `$A62` | `$1C` | `$0020` | 0 | same |
| 10 / `object:item.reward.kind10` | `$1C` | `$A63` | `$16` | `$0010` | 0 | same |
| 11 / `object:item.reward.kind11` | `$1D` | `$A65` | `$1B` | `$0010` | 0 | same |
| 12 / `object:item.reward.kind12` | `$1E` | `$A67` | `$1A` | `$0050` | 0 | same |
| 13 / `object:item.reward.kind13` | `$1F` | `$A69` | `$11` | `$0030` | 0 | same |
| 14 / `object:item.reward.kind14` | `$20` | `$A6E` | `$0D` | `$0010` | 3 | current false bank `$37`; correct to embedded line 3 |
| 15 / `object:item.reward.kind15` | `$21` | `$A6F` | `$0E` | `$0015` | 3 | same |
| 16 / `object:item.reward.kind16` | `$22` | `$A70` | `$0F` | `$0020` | 3 | same |
| 17 / `object:item.reward.kind17` | `$23` | `$A71` | `$10` | `$0025` | 3 | same |

Exact kind-to-human item names remain PENDING; the UI must show `Kind NN / identity $NN` until source
cross-reference proves a name. Do not guess Axe/Hammer/etc from silhouette.

## R1-S3 Complete Visible-Object Census

This census contains **30 evidence units**, again counting 17 rewards individually. Scene key:
`PAL-R1-S3-PLANEA-BOSS`.

| Display / canonical ID | Technical identity | Program / comp / palette | Hardware | Composer / Bestiary | Evidence / confidence |
|---|---|---|---|---|---|
| Rastan + four held weapons (5 units) | same player/FRONT identities as R1-S2 | H24; source `$33` | PC090OJ | PRESENT_CORRECT / PRESENT_CORRECT | PROVEN shared identity; scene mapping may override |
| Entry Green Sword Knight / `object:castle.green_sword_knight.r1.n3` | base `$033E`, family 2 if retained at entry | 23/97 domain, not 29/109 | PC090OJ | PRESENT_WRONG_IDENTITY / PRESENT_WRONG_IDENTITY | Tighe gameplay + source domain; reachability PARTIAL |
| Ordinary enemy death | base `$0A73`, comp 2 | owner palette | PC090OJ | PRESENT_CORRECT / PRESENT_CORRECT | PROVEN |
| Generic impact/burst | base `$0275`, `$9D-$A0`, comp 0 | embedded line 0 unless boss context overrides | PC090OJ | PRESENT_CORRECT generic / PRESENT_CORRECT generic | PROVEN |
| Rewards 1-17 | same exact rows above | `$0A5A`, `$13-$23`, comp 2; lines 0/3 | PC090OJ | 17x PRESENT_WRONG_PALETTE_SOURCE / 17x same | PROVEN mechanism; reachability depends entry-enemy `+$36` |
| Round-1 boss body / `object:boss.r1.body` | slot A5+`$0708`; rec type `$0E`; base `$061D`; state 3 -> `$10` | initial anim `$00`; comp 1; program `$47908`; embedded line F; `+$27=0` | PC090OJ | MISSING / PRESENT_PARTIAL | `$4449E,$453A8,$4543E,$455C2`; PROVEN initial body |
| Round-1 boss auxiliary / `object:boss.r1.aux.type15` | type `$0F` records via `$457B2/$457D0`; base `$061D` | anim `$14`; comp 1; program `$47E54`; line F; `+$27=0` | PC090OJ | MISSING / PRESENT_PARTIAL | `Cody_boss_palette_next_target_recon.md`; PROVEN route, phase/role PARTIAL |
| Boss-context death/impact / `object:boss.r1.effect.death` | boss behavior later activates effects; exact R1 sequence not completely enumerated | do not assume field-enemy palette; generic `$0275` may be used | PC090OJ | PRESENT generic but wrong scene context / PARTIAL | boss update/death path; PARTIAL |
| Fight controller / `controller:boss.r1` | `$46BE0` Round-1 branch / `$4CE6C` | no independent graphics | controller | CONTROLLER_ONLY / CONTROLLER_ONLY | PROVEN |
| Post-boss transition / `controller:r1s3.postboss` | retained stage/scene progression and palette/scene package transition | no independent proven art | controller + planes | CONTROLLER_ONLY / PARTIAL | current source; PARTIAL exact phase inventory |

No source evidence establishes a separate persistent decorative PC090OJ actor in R1-S3. Plane animation
must stay under Plane A/B rather than being fabricated as a sprite object.

## Green Sword Knight Corruption

### Proven semantic/generation error

`gen_reindexed_pc090oj.py` currently invokes `ActorRenderState(0x033E, anim, 0)` for all 29 claimed
programs. Six of those programs are not a valid `$033E` domain. This generates/reindexes synthetic
`(base,program)` composites and leaves the real family-8/base-`$0241` rope cells uncovered.

Correct base `$033E` domain:

- normal `$93-$96`;
- short reaction `$71-$73`;
- airborne `$20-$23`;
- state-`$1F` sequences `$97-$9C` and `$A1-$A6`;
- total **23 programs / 97 codes**.

This directly explains wrong/reverting colors when the distinct family-8 climber displays. It also makes
the current `29/109` verifier circular: it verifies the generator's declared synthetic domain, not source
ownership.

### What it cannot explain

Offline reindexing changes pixel nibbles, not piece count, X/Y offsets, order, actor anchor, SAT link, or
tile residency. Therefore the screenshot's broken/misassembled geometry is **not diagnosed** by the
29/109 error and is not a Plane-A stale-row symptom.

The exact production root cause remains **OPEN** among:

- wrong selected generated frame/piece list;
- signed piece-offset/anchor error;
- 12-cell DMA worklist or 49-slot residency drop;
- SAT order/limit truncation;
- stale semantic queue or shadow-SAT bank.

The smallest decisive existing-path diagnostic is one first-bad GENESIS NTSC frame containing the actor's
64-byte record, selected generated frame ID and expected piece list, six lane queues, DMA worklist/count,
resident keys/used bits/drop count, emitted count, both shadow SATs, actual VDP SAT, and referenced VRAM
patterns. Compare expected -> queue -> shadow SAT -> VDP SAT. The first stage that changes coordinates or
drops pieces establishes the correction. This repeats the durable 0049/0050 discriminator; it does not
create a new tracing architecture.

## `$4D/$56-$5A` Re-Audit

| Program | Every proven writer/selector in inspected source | Owning base/family | Belongs to `$033E` Green Knight? |
|---:|---|---|---|
| `$4D` | direct `$4680E`, passed to creator `$45248` | base `$0234`; not family-2 `$033E` | **NO** |
| `$56` | computed only by family-8 branch `$468A2-$468C8` (`$4D+$09`) | live actor base `$0241`, family 8 | **NO**; belongs to separate rope-climber object |
| `$57` | direct `$465CE` and `$46830` | base `$01FC`; Flying-Demon/component/scripted path | **NO** |
| `$58` | direct `$46842` | base `$01FC` | **NO** |
| `$59` | family-8 compute (`$4D+$0C`); direct `$46418,$4C364` | base `$0241` family 8 **or** base `$0546`, depending writer | **NO**; `(base,program)` identity must be preserved |
| `$5A` | family-8 compute (`$4D+$0D`); direct `$46448,$464BE,$4C01E` | base `$0241` family 8 **or** base `$0546` | **NO** |

`$4684E` is the state-`$11` **boss/component handler**, despite older “rope knight” comments. Its family-2
branch selects `$94-$96`; its family-8 branch selects `$56,$5A,$5A,$59`. It never selects `$4D,$57,$58`.
Selector numbers can be shared across bases; they are not global visual identities.

Andy action: delete `$4D,$56-$5A` from the `$033E` card and 29/109 assertion. Add a distinct family-8,
base-`$0241` object with `$56,$59,$5A`. Keep `$0234/$01FC/$0546` objects in research view until their exact
human identities/scene uses are proven.

## Reward / Pickup Runtime Palette Audit

Complete path:

`schedule +$36 -> $40CCC/$40D32 -> family 12/base $0A5A -> anim $13-$23 -> compositor 2 -> embedded
line 0 (kinds 1-13) or line 3 (14-17) -> scene sprite lane -> Genesis route/reindexed pattern -> SAT`.

Build 0539 diverges twice:

1. **Tool model:** `server.py` and H25 split rewards into false effective-bank groups `$30` kinds 1-4,
   `$31` kinds 5-13, `$37` kinds 14-17. Direct VM decode proves 1-13 line 0 and 14-17 line 3.
2. **Production generation:** `gen_reindexed_pc090oj.py::resolve()` has no reward entries in
   `USAGE_BANK`, `USAGE_UID`, or `code_sets`. The Test mappings for the three reward objects therefore do
   not transform `$A5A-$A71`. `gen_pc090oj_palsel_lut.py` consumes bank-shaped mapping keys, while the
   reward object keys are semantic IDs; its Build-0539 report lists only `$30,$32,$33,$34,$35,$36,$3A,
   $3C,$3E`. Runtime routes kinds 1-13 as effective `$30` and kinds 14-17 as `$33`, both to Line 0 in the
   current generated LUT, while their raw pixel indices remain untransformed.

Thus the wrong reward colors are a **proven generation/integration omission plus a wrong Composer source
model**, not evidence that Tighe chose bad colors. Test currently contains reward mappings to protected
Line 2, but those mappings are neither a valid per-scene ownership decision nor consumed by production.

Required sequence later: Andy corrects the 17 exact source records; Tighe maps them in the applicable
scene; Cody adds all 17 `(code,embedded-line,scene)` identities to offline reindex/variant generation and
the scene-local palette-line lookup. No runtime recoloring.

## R1-S2 Trap / Hazard Audit

The important negative result is source-proven:

- `$0224` pit flame materializes in R2/R4, not R1-S2.
- `$09EA` spike/spear/stalagmite materializes in R5, not R1-S2.
- neither may be assigned to Tighe's R1-S2 screenshots.

The current source evidence therefore supports the R1-S2 hazards as PC080SN scene graphics (and possibly
palette animation/collision coupling), not as those PC090OJ actor bases. The record-16..21 corpus proves
the graphics are in the R1-S2 Plane-A domain, but it does not label which `(tile,bank,flip)` subset is each
hazard. Exact source palettes remain PENDING.

| Visual | Current owner conclusion | Composer requirement | Status/root cause |
|---|---|---|---|
| floor spikes | Plane A or mixed; not R1 `$09EA` | `Layer A > Hazards > Floor Spikes`, disabled until subset pinned | wrong color open; semantic subset absent |
| suspended spike trap | Plane A or mixed | separate object, never merge with floor spikes | open |
| moving wooden gate | Plane A or mixed; not automatically exit `$7E` | separate gate object | open |
| falling water | likely Plane A + palette animation; not proven R1-S1 `$59AD4` | graphics frames + palette-animation substate | open |
| pit flames | Plane A/palette animation; not R2/R4 `$0224` | separate from static lava | open |
| static lava | Plane A scene map | scene environment group | current raw tiles exist; semantic grouping absent |

Smallest resolving evidence: use the already-established ORIGINAL ARCADE marked-frame capture at one
world position through a full cycle, correlate PC080SN cell/CRAM writes and collision word, then follow
the observed writer/table in Ghidra. Until that exists, neither Andy nor Cody may fabricate codes/banks.

## R1-S3 Layer-A Authored Mapping Activation

| Boundary | Result | Evidence |
|---|---|---|
| Context key | **YES**: `PAL-R1-S3-PLANEA-BOSS` | Test context and `palette_subround_map.json` record 22 |
| Test authored mapping | **YES** | many `LA-*` maps; context Line 3 entries 1-14 authored |
| Generator reflects it | **YES** | 96-byte asset SHA `de710f...`; Line 3 is `0000,0004,0008,000E,00AE,0444,046A,04EE,0600,0644,0666,068A,08AC,0CCC,0884` after index 0 |
| Generated artifact exists | **YES** | `build/palette_export/cram/PAL-R1-S3-PLANEA-BOSS.bin` |
| Generated ROM data includes it | **NO** | Makefile prerequisites and `palette_hooks.s` incbin only R1-S1/R1-S2 |
| Runtime selects/installs it | **NO** | `palette_scene_select.bin[22]=0`; pointer table has only two assets |
| Runtime later overwrites it | **NO / not applicable** | it is never installed; arcade hooks are gated from Test-owned lines |

The exact first divergence is **generated artifact -> production package/pointer/selector**. The exporter
works; the production compiler's `AuthoredLayerA.SCENES` contains only S1 and S2, and the assembly pointer
table contains only two assets.

Natural progression and direct-start both reach stage index 22 and therefore select zero. Their inherited
palette may differ according to prior state, but neither installs the authored R1-S3 package. Boss entry
does not reinstall a third asset because none exists in the ROM package.

## R1-S3 Layer-B Usage

Answers:

- Plane B visually unused for the complete interval: **PARTIAL / not proven**.
- Plane-B tile data active: **YES**.
- Plane-B scene-entry publication active: **YES**.
- Plane-B scroll/row publication path active: **YES**.
- CRAM Line 2 required: **CONDITIONAL** pending composited pixel-coverage proof.

The record-22 Plane-B scene-fill payload is 4096 bytes at offset 8376 in
`plane_b_scene_fill_maps.bin`, SHA-256
`85ecebe6b4776499359758f0f0316cbd6700c2643409ec8c265468bb4e254309`, and is not blank. At scene entry,
`genesistan_plane_a_scene_scroll_reseed_native` copies 1024 longwords into `staged_bg_buffer` and marks all
BG rows dirty (`tilemap_hooks.s:957-979`). Pan helpers continue to call the native Plane-B row publisher.

Tighe's observation strongly suggests Plane A may occlude Plane B in the visible boss room, but active,
nonblank data and publication disprove “Layer B does not exist.” Source inspection alone does not prove
that every Plane-A pixel is opaque through entry, fight, flash/death, and post-boss transition.

## Scene-Local CRAM Line-2 Reclamation

Current answer: **CONDITIONAL, not presently reclaimable**. Safe ownership interval: **none proven**.

Before reclamation, Cody must perform a finite compositing coverage audit for record 22 across:

1. entry/initial publication;
2. all reachable Plane-A animation states and camera positions;
3. boss-intro/fight/damage/death states;
4. post-boss/transition frames;
5. any forced blank or clear interval.

Only if Plane B contributes no visible pixel and no transition depends on Line 2 may a scene-local policy
mark it free from the first completed R1-S3 package publication through the last frame before scene-exit
teardown. Scene exit must restore the next scene's Plane-B/Line-2 owner before display enable. Plane A or
sprites could then use it only through an explicit R1-S3 local mapping. It must never become globally free.

Other boss rounds also have generated per-round Plane-B records and publication architecture. R1-S3
cannot be generalized; other scenes are **UNKNOWN individually**.

## Round 1 Boss and Component Inventory

Andy must represent the boss as a scene-local group, not as a field enemy:

```
object:boss.r1
  object:boss.r1.body
  object:boss.r1.aux.type15
  object:boss.r1.effect.death   (PARTIAL until phase sequence is closed)
```

### Body — PROVEN initial state

- Round 1, Sub-Round 3 only.
- A5+`$0708`, record type `$0E`, base `$061D`.
- creator chain `$45330->$4449E->$453A8->$4543E`, template `$455C2`.
- initial anim `$00`, compositor 1, program `$47908`.
- `+$27=0`, family `+$3E=0`; embedded program line F controls pieces.
- do **not** apply family-2 `$45684/$456EC` field-enemy palette logic.

### Type-15 auxiliaries — PROVEN route, PARTIAL semantics

- later records created through `$457B2/$457D0`;
- record type `$0F`, base `$061D`, anim `$14`, compositor 1, program `$47E54`;
- clear `+$27`, embedded line F;
- auxiliary/projectile records, not required for the initial body pose;
- exact count, lifetime, visual role, and full phase ordering remain PENDING and must be shown as such.

Body and auxiliaries share proven line F source selection, but their mappings must remain separate
scene usages until identical required colors are proven. Exact displayed line-F palette content comes from
the master/staged boss palette path, not the ordinary per-round field pool; it remains PENDING. Andy must
not invent colors or reuse the Green Knight mapping.

## Black Backdrop Regression

**CODY PRODUCTION BUG — FIX REQUIRED.** Target: **BLACK**.

- VDP register 7 writer: `apps/rastan-direct/src/vdp_comm.s:115-117` writes `0x00`, selecting CRAM
  Line 0 entry 0. This register value is correct.
- Current gray value: R1-S2 and R1-S3 scene assets begin with big-endian `0x0888`.
- Exact runtime writer: `vdp_install_test_lines`, `vdp_comm.s:429-433`, copies the asset's first word to
  `staged_palette_words` Line 0 entry 0 and sets `palette_pending` at line 444. VBlank publishes it.
- Cause: `gen_test_palette_cram.py` normalizes each global test line's index 0 to `0x0000`, but
  `export_subround_palette_manifest.py` preserves the scene context's effective index 0. The per-scene
  install bypasses the global normalized line.
- Why the earlier black direction did not survive: it was satisfied in the global line generator but not
  made an invariant of scene-package export/install.

Narrow later correction: enforce CRAM entry 0 = `0x0000` for every installed scene line (at minimum Line
0, preferably the package-format invariant for all three exported lines), verify the exported bytes and
runtime staged value, and leave VDP register 7 at zero. Do not change Tighe's authored nonzero entries.

## Remaining Plane-A Stale-Row Failure

Build 0539 added revalidation of the downward newly visible `new_top+27` row while retaining `top+31`
prefetch. That fixes the demonstrated `N-32` ownership history only. Tighe's gameplay proves another
history remains.

The current screenshots do not contain the internal record/selector/front/logical-row tuple, so assigning
the new failure to another edge or record transition would be speculation. The exact next target is:

> the **first visible wrong 8-pixel row in Build 0539**, with special attention to the record-21/final-
> segment transition and the already reported stale pipe row.

At the update immediately before it becomes visible, capture from the existing trace path:

- frame and old/new camera top;
- direction and number of row crossings this frame;
- current, completed, and predecessor record; selector and front;
- requested logical row `N`, physical row `N&31`, and source `(record,row)`;
- residency tag before/after `.Lplane_a_publish_logical_row_native`;
- staging row SHA/words and `fg_row_dirty` before VBlank;
- published VRAM row after VBlank.

This distinguishes wrong edge/multi-row skip, wrong predecessor selection, correct source but stale
staging, and correct staging but missed publication. It is **Cody-owned**. No production fix is claimed.

## Current Palette Composer Architecture Review

Current strengths:

- v0.4 profile has target lines, sprite mappings, Plane-A mappings, context-local policies, and
  inherited contexts;
- the 18-subround panel exposes real scene keys and record bands;
- R1-S2/R1-S3 have independent Plane-A corpora and context mappings;
- object frames share a canonical `object_id`/mapping key;
- “All Assets” exists as a research switch;
- Line 2 is server-authoritatively protected and can only reuse populated colors.

Current deficiencies:

- navigation selects a PLANEA environment, then shows one flat sprite list; it is not a coherent
  Round -> Sub-Round -> hardware/object view;
- all `membership=shared` items appear in every ordinary scene, including irrelevant unresolved content;
- unresolved `O.objects` are appended to normal view even when “All Assets” is off;
- no first-class boss/body/component hierarchy;
- rewards are three false bank cards rather than 17 exact frames under one reward family;
- hazards are raw Plane-A banks/patterns, not human scene objects;
- `RESERVED_LINES=[2]` and `LINE_OWNERS` are global, so the model cannot express a proven scene-local free
  line;
- provenance/status is shallow and several current “PROVEN” labels are circular or stale;
- the object model lacks an explicit distinction among canonical identity, scene usage, inherited
  mapping, local override, and production-integration status.

## Proposed Human-Oriented Composer Information Architecture

Final hierarchy:

```
Round
  Sub-Round / Boss
    Scene package and palette ownership
      Layer A
      Layer B
      Player
      Player Weapons
      Field / Scene Enemies
      Boss (body, components, projectiles/effects)
      Hazards / Traps
      Rewards / Pickups
      Projectiles
      Effects / Deaths
      HUD / Truly Shared
      Controllers (diagnostic only)
        Object
          Pose / Frame / State
```

Selecting `Round 1 > Sub-Round 2` must show only R1-S2 usages plus a collapsed “shared in this scene”
section. Selecting `Round 1 > Sub-Round 3 / Boss` must show the boss group and R1-S3 ownership panel.
Unrelated rounds never appear unless Research view is enabled.

Identity/mapping model:

- **canonical object**: stable semantic identity and complete source frame domain;
- **scene usage**: reachability, source palette, hardware owner, and state subset in one scene;
- **shared mapping**: explicit mapping used by all declared usages;
- **inherited mapping**: read-only display of which ancestor supplies it;
- **local override**: scene-owned delta, visibly labeled “affects this scene only”;
- every edit preview states impact: `this scene`, `Round N`, or `all declared uses`.

Normal cards show name, preview, hardware badge, scene, mapping owner/scope, source palette, target line,
and one compact confidence badge. Expanded provenance shows base/family/type/state/program/compositor,
creator PCs, `+$27`, exact codes, evidence files, and separate source/runtime/Tighe statuses.

## Required Andy Object Handoff

This is the primary implementation list. Shared technical details for the 17 rewards are in the exact
table above; each reward is one row semantically even if the UI presents one parent with 17 frames.

| Round | Sub | Scene | Display / canonical object | Hardware | Base/domain; family/state; comp/program | Source palette / runtime source | Genesis requirement | Composer | Bestiary | Required Andy action | Evidence / confidence |
|---:|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | 2/3 | R1-S2/R1-S3 | Rastan `object:player.rastan` | sprite | H24 player; retained states | `$33`; player route | scene usage may inherit shared map | PRESENT_CORRECT | PRESENT_CORRECT | mark truly shared, preserve scene override ability | H24 / PROVEN |
| 1 | 2/3 | both | four `object:weapon.*` | sprite | H24 FRONT overlays | `$33` | same | PRESENT_CORRECT | PRESENT_CORRECT | group beneath Player Weapons | H24 / PROVEN |
| 1 | 2/3 | both | Green Sword Knight `object:castle.green_sword_knight.r1.n3` | sprite | `$033E`; family2; 23 programs/97 codes; comp0 | embedded + optional `+$27` override | one correct 23-program generated domain | WRONG_IDENTITY/GEOMETRY | WRONG_IDENTITY | remove six foreign programs and 29/109 claim | 68000 engines + VM / PROVEN |
| 1 | 2 | R1-S2 | Rope Climber `object:castle.rope_climber.family8.r1` | sprite | `$0241`; family8/state11; `$56,$59,$5A`; comp0 | embedded piece nibbles | independent mapping and generated coverage | MISSING | folded into wrong knight | add scene object and frames; label human identity PARTIAL | `$4684E` / PROVEN technical |
| 1 | 2 | R1-S2 | Small/Large Bat | sprite | `$0268/$03F6`; airborne | `$3E` | scene usages | WRONG_SCENE | WRONG_SCENE | attach to R1-S2 usage instead of field-only | tables + user gameplay / PARTIAL scene |
| 1 | 2/3 | both | ordinary death | sprite | `$0A73`, comp2, `$0B-$12` | owning actor | inherit owner mapping | PRESENT_CORRECT | PRESENT_CORRECT | no new palette object | `$40CCC` / PROVEN |
| 1 | 2 | R1-S2 | M burst `object:effect.burst` | sprite | `$0275`, comp0, `$9D-$A0` | embedded 0 | scene usage | PRESENT_CORRECT | PRESENT_CORRECT | classify Effects, not enemy | H16 / PROVEN |
| 1 | 2/3 | both | Rewards kind01-kind17 | sprite | `$0A5A`, family12, comp2, `$13-$23`, codes `$A5A-$A71` | kinds1-13 line0; 14-17 line3; clear override | Tighe-authored scene target; production later reindexes all | WRONG_PALETTE_SOURCE | WRONG_PALETTE_SOURCE | replace three bank objects with reward parent + 17 exact children | VM + `$40C2E/$40C40` / PROVEN |
| 1 | 2 | R1-S2 | six hazard/environment units | Plane A / mixed | exact tile subsets PENDING; `$0224/$09EA` excluded | scene Plane-A banks PENDING subset | separate scene-local mappings after proof | NOT_A_SPRITE/MISSING | MISSING/WRONG_SCENE | add disabled semantic groups; never invent source codes | H14/H21 + user visuals |
| 1 | 2 | R1-S2 | Rope terrain | Plane A+collision | map/collision | Layer-A scene bank | scene environment | raw only | PARTIAL | group as terrain, not sprite | H21/H24 / PROVEN class |
| 1 | 2 | R1-S2 | Exit controller | controller | `$7E` -> state7 | N/A | none | CONTROLLER_ONLY | CONTROLLER_ONLY | research view only | H22/H24 / PROVEN |
| 1 | 3 | R1-S3 | Boss body `object:boss.r1.body` | sprite | `$061D`, type0E, state10, comp1, anim00/prog47908 | line F, staged boss source | R1-S3 boss mapping, not field mapping | MISSING | PARTIAL | add boss group/body card | boss tables / PROVEN initial |
| 1 | 3 | R1-S3 | Boss auxiliary `object:boss.r1.aux.type15` | sprite | `$061D`, type0F, comp1, anim14/prog47E54 | line F | separate scene usage/context | MISSING | PARTIAL | add child card with role/count PARTIAL | `$457D0` / PROVEN route |
| 1 | 3 | R1-S3 | Boss death/effect | sprite | phase inventory PARTIAL; do not infer field logic | boss staging / effect program | scene usage | generic only | PARTIAL | nested Effects card, disabled until full phase proof | boss update path / PARTIAL |
| 1 | 3 | R1-S3 | fight/post-boss controllers | controller | `$46BE0/$4CE6C` and progression | N/A | none | CONTROLLER_ONLY | PARTIAL | research view only | source / PARTIAL |

Mechanical coverage counts using the census units above:

- R1-S2: **37** visible/graphics-affecting units; **28 missing or wrong in Composer**; **28 missing or
  wrong in Bestiary**.
- R1-S3: **30** units; **20 missing or wrong in Composer**; **20 missing or wrong in Bestiary**.

These counts treat each of 17 rewards as an individual object requirement and the four held weapons as
four units. They do not claim 37 or 30 simultaneous actor records.

## Required Andy UI Specification

### Navigation hierarchy

Use `Round -> Sub-Round/Boss -> scene package`. Round 1 expands to `Sub-Round 1`, `Sub-Round 2`, and
`Sub-Round 3 / Boss`. Keep PLANEA/PLANEB/PC090OJ environment keys behind the human scene label.

### Scene asset groups

Order: Scene/ownership summary; Layer A; Layer B; Player; Player Weapons; Scene Enemies; Boss; Hazards;
Rewards; Projectiles; Effects/Deaths; HUD/Shared. Controllers appear only in Research.

### Object card design

Normal card: preview, display name, hardware icon, scene badge, source palette label, target line, mapping
scope, authored/inherited indicator, and compact confidence. Frame/state selector stays inside the card.

### Advanced provenance

Expandable details: canonical ID, base, family, record type, creator, state, program, compositor, code
domain, `+$27`, palette-loader chain, scene reachability, evidence paths/PCs, and separate badges for
source-proven, runtime-verified, Tighe visual identity, and Tighe-authored target.

### Palette line ownership panel

Show Lines 0-3 as scene-local rows with columns: current owner(s), backdrop index, Plane A, Plane B,
sprites, editable/protected/free/conditional, inherited/local, and animated indices. A line can have
multiple consumers; do not label it merely “editable.” Index 0 must show `Backdrop: BLACK invariant`.

### Scene-local free-line behavior

R1-S3 Line 2 currently displays `CONDITIONAL — Plane B active; visual occlusion not proven`, remains
locked, and links to the coverage evidence. If Cody later proves freedom, show `FREE IN THIS SCENE ONLY`
with start/end states and restoration owner. Never alter global Line-2 protection from this scene badge.

### Shared versus local mapping

Every mapping shows its owner scope. Editing offers explicit `override this scene` by default; promotion
to shared/round scope requires a deliberate action and lists all affected usages. Removing a local
override reveals the inherited mapping without deleting it.

### Boss representation

One `Round 1 Boss` group with Body, Type-15 Auxiliaries, Projectiles/Effects, and Death/Post-boss states.
Body and auxiliary cards may share a palette only after evidence establishes identical required indices.
Do not present them as field enemies.

### Reward representation

One `Gameplay Rewards` parent, 17 selectable children. Each child shows kind, identity byte, value, anim,
code, embedded line, preview, and human name status. One mapping may be intentionally shared only when
the resulting transformed pixels/colors are proven compatible.

### Hazard representation

Separate `Sprite Hazards`, `Plane-A Hazards`, `Plane-B Hazards`, and `Palette Animations`. R1-S2 floor
spikes/gate/water/flames initially appear as disabled Plane-A candidates with “source subset pending,” not
as `$0224/$09EA` sprites.

### Research-only objects

Unresolved producers, raw bases, synthetic compositor candidates, controllers, and cell sheets are hidden
from Authoring view. Research view is a separate mode with warnings and cannot silently create production
mappings for a PENDING identity.

## Cody-Owned Production Follow-Up

Recommended order, each in a separate implementation task with normal gates:

1. Fix backdrop package invariant to black and add R1-S3 asset packaging/selector/pointer/install tests.
2. Capture the first bad Build-0539 Plane-A row and correct only the proven publication/selection fault.
3. Capture the first bad Green Knight frame and correct the first divergent queue/residency/SAT stage.
4. After Andy/Tighe provide corrected source mappings, replace synthetic 29/109 generation with the
   23/97 `$033E` domain plus independent family-8/base-`$0241` coverage.
5. Add all 17 reward `(base,program,embedded-line,scene)` variants to offline generation and palette route.
6. Integrate hazard subsets only after original-arcade write/cell provenance and Tighe color decisions.
7. Do not reclaim R1-S3 Line 2 until the full composited-coverage audit proves a safe interval.

## Files / Local Commit / Logs

Task-intended files:

- this report;
- append-only `AGENTS_LOG.md` entry.

No ROM was built, no build number was consumed, and no generated artifact was changed. Any local commit
must stage only these two paths. No GitHub push is authorized.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0090
