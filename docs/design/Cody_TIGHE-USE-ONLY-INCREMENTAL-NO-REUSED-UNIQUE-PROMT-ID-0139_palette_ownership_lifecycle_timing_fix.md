# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0139

# Palette ownership lifecycle timing correction

## Outcome

Build 0572 is the first candidate to separate gameplay graphics preparation from gameplay palette ownership. The retained arcade gameplay palette load, `FUN_00059de8 -> $059AD4`, now activates the Test 2.0 Lines 0/1/3 and the matching PC090OJ palette map. Merely preparing a gameplay graphics scene no longer does so. Original presentation writers therefore retain Lines 0/1/3 through READY, Stage Clear, and the inter-round presentation; Test 2.0 takes ownership only as gameplay begins. The PROMT-ID-0138 resident Layer-B Line 2 rule is unchanged.

This is a candidate, not visual acceptance. Tighe must test the normal ROM's complete natural R1-S3 to R2-S1 sequence and death/respawn cases.

## Starting repository state

- Branch: `rastan-direct-proposal`.
- Starting HEAD: `70d20c0a006f537104b68b4487febfc276a87e25`.
- Starting counter: 571.
- PROMT-ID-0138 source commit present: `538fac0c56153425b83ef84a06f71e739acfd147`.
- PROMT-ID-0137 source commit present: `79d750940ea4f7c83684245312e62bb6ca0c143c`.
- Concurrent PROMT-ID-0135 audio edits in `apps/rastan-direct/src/sound/sound_comm.s` were already dirty, were preserved byte-for-byte by this task, and were compiled into 0572.
- Existing generated outputs, `AGENTS_LOG.md`, the edited 0134 report, untracked 0135/0136 reports, and the two performance-roadmap documents were preserved. No reset, clean, rebase, rollback, deletion, or push was performed.

## Phase-0 priors

- Relevant findings: KF-010 (original state remains authority), KF-037 (stage-clear finite presentation), KF-043 (unconditional staged CRAM publication), KF-045/KF-046 (generated Test 2.0 Lines 0/1/3 ownership), and KF-081/KF-082 (retained Layer-B source/keep semantics).
- Relevant closed issues: CLOSED-015 (presentation flow must not be bypassed) and CLOSED-023 (finite presentation/display ownership remains distinct from ordinary transitions).
- OPEN-040 remains the Record-29 acceptance issue. Tighe has now said the 0138 checkpoint-respawn corruption is visually fixed, but has not supplied an explicit exact Record-29 plus later-progression acceptance against 0571/0572, so its literal closure condition is not silently weakened.
- OPEN-041 is added for Build 0572 lifecycle visual acceptance.
- Classification: this correction extends KF-046. It does not reopen the 0138 Line-2 residency root cause.

## Arcade palette lifecycle and semantic cut

The retained program has distinct palette events; it does not have one universal non-gameplay palette:

| Phase | Retained owner/event | Genesis realization after 0139 |
|---|---|---|
| Cold title / return title / no-human frontend | frontend presentation reset and retained palette producers | original converted palette writes; authored owner inactive |
| R1/R2 READY, including active-human respawn | retained READY producers, including banks `$04/$05/$33/$43` through `$059AD4` | original Lines 0/1/3; resident gameplay Line 2 retained for an active human per 0138 |
| Gameplay entry/resume | `FUN_00059de8`, gated by `A5+$13B0`, calls `$059AD4` with the current round Layer-B bank | this exact event activates authored Lines 0/1/3 and the PC090OJ authored map; the current-round source becomes Line 2 |
| Active gameplay | retained palette writers plus Test 2.0 ownership | authored Lines 0/1/3 protected; current-round Layer-B and permitted animation writers retain their existing routes |
| Boss fade | retained `$047004` cadence/state | generated final Line-1 fade words; unchanged |
| Stage Clear / round complete | retained End-Round states 9–13; `$056128` loads banks `$04/$05/$33/$43`; command `$27` starts Scene Clear | authored owner released by non-gameplay scene; original presentation writers may update Lines 0/1/3 |
| Next-round READY | retained presentation continues until gameplay palette load | presentation palette remains owner even when next gameplay graphics are already resident |
| GAME OVER | retained frontend/game-over writers | original converted presentation palette; authored owner inactive |

The graphics semantic boundary remains `arcade semantic producer -> final Genesis VDP/SAT output`. No PC080SN/PC090OJ chip tail, shadow tilemap, palette buffer, or new lifecycle scheduler was introduced. The corrected palette cut is the retained `$59DE8->$59AD4` gameplay palette decision, not the earlier native graphics-residency event.

## Complete production writer ownership map

| Writer | Source semantic event | Destination | Authored data | Gate and lifecycle |
|---|---|---|---|---|
| boot clear (`boot/boot.s`) | cold reset | all staged lines; `palette_pending=1` | no | boot only |
| `load_scene_tiles` | native graphics residency/presentation scene selection | non-gameplay restores frontend Lines 0/1/3 and, without a human, L2; active human preserves L2 | no | scene class plus `A5+$34`; 0139 releases authored owner for non-gameplay but does not activate it for gameplay preload |
| `vdp_install_test_lines` | retained gameplay palette-load boundary | Lines 0/1/3, owner asset, PC090OJ map | Test 2.0 | stage-to-approved-asset table; now called by current-round `$59AD4` event, not bare scene load |
| `genesistan_palette_hook_59ad4` | retained bank/row palette loader | bank 4→L0, 5/3→L1, current-round Layer-B→L2, 33/43→L3; water animation L3 entries 14/15 | no, except it triggers the authored installer at the gameplay boundary | authored-owner-active protects L0/L1/L3; no longer `scene_id==1` |
| `genesistan_palette_hook_03ab00` | retained single palette entry | L1 entry 1 | no | original event |
| `genesistan_palette_hook_45dae` | retained positional bank-0 copy | staged palette range | no | permitted only while authored owner inactive |
| `genesistan_palette_hook_3ba64` | retained palette conversion/source copy | banks 0/1→L0/L1, bank 3→L1, bank 48→L2, bank 51→L3 | no | L0/L1/L3 writes suppressed only while authored owner active |
| `genesistan_palette_hook_47004` | retained R1 boss fade step | L1 | generated from arcade fade data | R1-S3 stage and original fade enable/cadence |
| `title_native.s` | native realization of retained title palette surface | L1 | no | title path |
| `fg_boundary_install` / context refresh | gameplay package or stage-context advance | refreshes Lines 0/1/3 | Test 2.0 | 0139 refreshes only if the retained gameplay owner is already active |
| `vdp_commit_palette` | VBlank publication | all 64 staged words to actual CRAM | n/a | `palette_pending`; clears pending after one DMA |
| diagnostic load bar/crash screen | explicit diagnostic state | direct CRAM | no | diagnostics only; not normal lifecycle |

`staged_palette_words` remains the only native resident palette. `palette_pending` remains the publication request. `vdp_commit_palette` remains the sole normal staged-to-CRAM publisher.

## First proven divergence in Build 0571

`load_scene_tiles` set `genesistan_current_scene_id=1` while READY/inter-round presentation was still active, then immediately called `vdp_install_test_lines`. The same early scene value also caused `$59AD4`, `$45DAE`, and `$3BA64` to suppress legitimate retained presentation writes. Thus graphics residency, authored palette ownership, and authored PC090OJ mapping were incorrectly treated as one event.

This explains all human controls:

- Cold R1 could look plausible because R1 authored colors overlap familiar gameplay/front-end uses and the interval was short; the activation was nevertheless early.
- Death/READY was wrong because an active player was not proof that gameplay presentation owned Lines 0/1/3.
- PROMT-ID-0138 made resumed/checkpoint R2 gameplay correct by preserving L2, but it did not correct the early Lines 0/1/3 owner.
- Natural R1-S3→R2 READY prepared scene-1 graphics early, installed R2 gameplay Lines 0/1/3, and suppressed the presentation banks which color `1UP`, `HIGH SCORE`, and `2UP`.
- Direct-start R2 human gameplay was correct because the same premature install eventually became the correct owner once gameplay began.
- The direct-start R2 no-human attract mismatch remains the 0138 harness combination: forced R2 graphics selector with retained Round-1/no-human semantics. No production special case was added.

## Production correction

Source commit: `a57a0934a83b23bdca2c86d55f91bf95bf97fb76`.

1. `load_scene_tiles` still prepares required graphics early, but a gameplay preload no longer installs Test 2.0 or changes the PC090OJ authored mapping. A non-gameplay scene clears the existing authored-owner asset and selects the presentation mapping.
2. The retained current-round Layer-B path in `genesistan_palette_hook_59ad4` activates Test 2.0 only when `$59DE8` performs the real gameplay palette load.
3. `$59AD4`, `$45DAE`, and `$3BA64` now protect authored lines according to `diagnostic_palette_active_asset`, the existing exact authored owner, rather than `genesistan_current_scene_id`.
4. `vdp_install_test_lines` installs the authored Lines 0/1/3 and calls `pc090oj_select_palette_map` as one ownership acquisition.
5. Package/stage refresh paths refresh Test 2.0 only when authored gameplay ownership is already active.

There is no round, READY, record, checkpoint, score-color, or screenshot special case. No palette color or Palette Composer mapping changed.

## Runtime timelines and evidence

### Direct R2-S1 human start

`states/traces/build0572_promt0139_r2s1_direct_initial/events.tsv` shows presentation contents remain through scene-1 preparation. At frame 407, the first retained gameplay state appears and staged L2 becomes:

`0000,0220,0440,0460,0024,0022,0026,0440,0220,0220,0240,0420,0002,0444,046A,0000`

Terminal actual CRAM L2 equals staged L2. This proves the delayed activation reaches correct R2 gameplay rather than losing it.

### Natural R1-S3 completion to R2

The normal automated route reached the boss but did not defeat it within the bounded input route. The same unchanged lifecycle was completed with the 0572 invincible derivative solely to observe the retained presentation states:

- frame 1544: End-Round entry and state 9;
- frame 1549: state 10;
- frame 1550: command `$27` (Scene Clear);
- frame 1558: state 11;
- frame 1806: state 12;
- frame 1808: Round 2 READY;
- frame 1815: state 13;
- frame 1964: Round 2 entered.

At states 9–13, each captured staged 64-word palette exactly equals actual VDP CRAM. State 9 reflects the preceding transition; states 10–13 share the retained presentation palette SHA-256 `3961989ab34a22db0cc9572dc4d6da9e625a34805d466fd50fd5a9fefbcdccba`. L2 remains the resident gameplay layer as required by 0138 while presentation Lines 0/1/3 change independently.

### Normal attract/title

Build 0572 completed two no-input title→R1 demo→title cycles at frame 14,450. The first and second title staged palettes are identical; terminal CRAM equals the staged second-title palette; display is on; presentation readiness is clear; unsafe display-enable writes are zero; no trap was observed. Evidence: `states/traces/build0572_promt0139_normal_attract/summary.txt`.

### Other lifecycle cases

The cold-entry, R1 and R2 direct subround entry checks passed as part of the generated 18-ROM selector matrix. PROMT-ID-0138's exact R1 and progressed R2 respawn traces remain applicable because the Line-2 preservation source is unchanged. This task did not automate a fresh complete R1 death/READY, exact Record-29 death, GAME OVER, or return-title human route. These remain mandatory visual checks and are not claimed accepted.

## Element-to-line path

Stage Clear/READY text uses retained PC080SN attributes routed by the established frontend map: bank 4 supplies Genesis Line 0, bank 5 and bank 3 supply Line 1, and sprite banks `$33/$43` supply Line 3. The native gameplay HUD labels are authored sprite/foreground consumers and therefore use the PC090OJ map selected with the active owner. The Build-0571 defect did not originate in the tiles or their line selectors: it installed gameplay CRAM contents and their map before the presentation owner had ended. Build 0572 keeps presentation bank writers enabled until the retained gameplay loader activates Test 2.0.

## Verification

- Build 0572 canonical gate: PASS.
- Gameplay-entry gate: PASS.
- Mandatory 30-second USA/NTSC Genesis trace: PASS.
- Test 2.0 palette validation: PASS; input provenance `49f38ea9b8c889eb24dbe232a25c590b79755b642abb8d42743d0d8b6a17c04f`.
- Same-number normal/diagnostic/score/direct-object/full-HUD/invincible family: generated and verified.
- All 18 direct subround derivatives: generated and selector verification PASS.
- Natural invincible completion through all End-Round states, Scene Clear command, Round 2 READY, and Round 2 entry: PASS.
- Normal two-cycle attract and return-title palette/visibility: PASS.
- Existing synthetic phase-epoch gate still reports its prior injected-state failure; this is not gameplay evidence and was not hidden.
- Audio source was not edited by 0139. No audible listen was performed.

## Build artifacts

All listed artifacts are 4,443,832 bytes and use source commit `a57a0934` plus the preserved concurrent 0135 audio working-tree input.

| Artifact | SHA-256 |
|---|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0572.bin` | `2ff752e7f018e9a78ddde2930bcec84957643e2a625da6a1a5806a91198d3833` |
| `dist/rastan-direct/rastan_direct_video_test_build_0572_invincible.bin` | `7712a69e59a7d0b767548b7a43aa2268916627eed5613d38cb87dbf8f345e967` |
| `dist/rastan-direct/rastan_direct_video_test_build_0572_S1-2.bin` | `7894badbfe4d2327a70b38a9e1f12cf3f9a8abf9f96a54e5bcd531b507205f74` |
| `dist/rastan-direct/rastan_direct_video_test_build_0572_S1-3.bin` | `95b2dbf183111ecba6d31556a060b53dd7815686b61df42771b38488f7015f7c` |
| `dist/rastan-direct/rastan_direct_video_test_build_0572_S2-1.bin` | `e5d6032adca14fde0c48be3bf30020c2bf1f33ae4fee2537211bef4d7668af07` |
| `dist/rastan-direct/rastan_direct_video_test_build_0572_S2-2.bin` | `dc8acc4a4f2b9a6909191b00feaf68b42f057d49a814799101188db3d44fb1d2` |
| `dist/rastan-direct/rastan_direct_video_test_build_0572_S2-3.bin` | `da7f9abe294e1f96ab929721308b2577edc035b4d7f111ee2dbd0836dd50b339` |

Counter: 572. Normal ROM is the primary acceptance artifact.

## Files changed by PROMT-ID-0139

- `apps/rastan-direct/src/scene_load.s`
- `apps/rastan-direct/src/palette_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/src/fg_tile_cache.s`
- this report
- `OPEN_ISSUES.md`
- append-only `AGENTS_LOG.md`

Generated build outputs and numbered ROMs changed normally. No Test 2.0 JSON, audio source, remap spec, tile routing, gameplay, collision, IRQ, DMA scheduling, or performance-roadmap implementation was changed by 0139.

## Open/Closed Issues Impact

- OPEN-040: remains open under its exact Record-29/later-progression closure wording, while recording Tighe's broader statement that the 0138 checkpoint-respawn defect is visually fixed.
- OPEN-041: new; Build 0572 corrects the proven lifecycle coupling, but awaits Tighe's complete visual sequence.
- No CLOSED issue was reopened or silently broadened.

## Required Tighe test

Test the normal ROM first. Verify: title → R1 READY → R1 gameplay → death → READY → resumed gameplay → natural R1-S2/R1-S3 → boss defeat → Stage Clear/congratulations → ROUND 2 READY → R2-S1 gameplay → progressed Record-29 death/READY/respawn → GAME OVER → title. Specifically compare READY text, `1UP`, `HIGH SCORE`, `2UP`, Stage Clear figure/text, and the first active gameplay frame. Also listen for the already-concurrent 0135 audio behavior. Report any first divergent screen and whether it occurs before or after gameplay movement begins.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0139
