TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0141

# Build 0572 initialization and presentation-palette regression

## Result

Build 0572 is rejected exactly as Tighe directed. It contains two independent defects. PROMT-ID-0139 delayed a value that initial Plane-A generation requires, and its palette investigation followed Lines 0/1/3 even though the native top HUD selects Line 2. Source commit `579d1b4371dc35c7d4f39fb18f320bef0186579c` separates graphics visual selection from palette ownership and makes the existing native frontend-HUD owner publish the original PC090OJ bank-48 colors on visible CRAM Line 2 without changing the resident staged gameplay Line 2. Build 0573 is a candidate only; Tighe has not accepted it.

## Starting state and Phase-0 priors

- Branch: `rastan-direct-proposal`.
- Starting HEAD: `457d9eae992da66309339a103c9992af3973405a`.
- Starting Makefile counter: 572.
- Current source commit after the correction: `579d1b4371dc35c7d4f39fb18f320bef0186579c`.
- PROMT-ID-0138 source commit `538fac0c56153425b83ef84a06f71e739acfd147` and PROMT-ID-0139 source commit `a57a0934a83b23bdca2c86d55f91bf95bf97fb76` were both present.
- Concurrent PROMT-ID-0135 audio source was already dirty. It was not edited by 0141. Its post-build source SHA-256 is `08ab18d5491e4d561dca0ee4e93af31a14be39b619336cc491a5e882559826e9`; it was compiled into 0573.
- Existing dirty generated build outputs, `AGENTS_LOG.md`, the 0134 report, untracked 0135/0136 reports, and performance-roadmap documents were preserved. No reset, clean, rebase, broad restore, or push was performed.
- The required policies and prior 0134–0139 reports were used as the governing evidence. Later Tighe visual evidence overrides 0139's automated conclusion.

## Preserved ROM identities

| Build | Size | SHA-256 | Status |
|---|---:|---|---|
| 0571 | 4,443,832 | `ab778a5d84cdbc0f3a9917defa8831063e95b5946cc5f9744047b05e8934cf95` | known-good scene-initialization comparison |
| 0572 | 4,443,832 | `2ff752e7f018e9a78ddde2930bcec84957643e2a625da6a1a5806a91198d3833` | **REJECTED**: Plane-A initialization regression and wrong presentation top-HUD colors |

Both files and hashes were verified from disk. Build 0572 remains preserved.

## Complete 0139 source-diff audit

| Hunk | Build-0571 behavior | Build-0572 behavior | Direct effect and classification |
|---|---|---|---|
| `scene_load.s` scene-owner block | every scene load called `pc090oj_select_palette_map`; gameplay preparation later called `vdp_install_test_lines` | non-gameplay cleared active asset **and visual index**; gameplay preparation skipped map selection while no authored asset existed | palette-map ownership separation was intended; clearing/delaying the visual index also changed Plane-A initialization and graphics residency |
| `scene_load.s` gameplay preparation | cache reset, initial state, then Test palette installer | cache reset and state only; palette installer delayed | correctly stopped early Lines 0/1/3 acquisition, but also removed the installer's visual-index side effect |
| `palette_hooks.s:$059AD4` | current-round Layer-B load did not activate the authored owner | first current-round Layer-B load calls `vdp_install_test_lines` | retained gameplay activation, palette staging, owner flag, PC090OJ map selection, and pending publication |
| `palette_hooks.s` guards | `genesistan_current_scene_id==1` protected authored lines | `diagnostic_palette_active_asset!=0` protects them | palette ownership became event-based instead of residency-based; no direct Plane-A publication |
| `vdp_comm.s:vdp_install_test_lines` | set asset and visual index, copied Lines 0/1/3, set pending | additionally selected PC090OJ map | coupled palette owner/map activation correctly at `$059AD4`, but the same routine still contained a graphics input needed earlier |
| `vdp_comm.s:vdp_refresh_test_lines_if_scene_changed` | refreshed stage context whenever called | returned immediately while asset was zero | delayed both palette refresh and visual-index refresh; graphics consequence was unintended |
| `fg_tile_cache.s:fg_boundary_install` | package activation unconditionally called `vdp_install_test_lines` | call was skipped while asset was zero | preserved READY palette, but removed the last pre-publication path that made the authored Plane-A visual descriptor current |

The four-file 0139 boundary therefore was finite at source level. Its first graphics-relevant change was not a tile DMA or dirty flag; it was loss of the visual-descriptor pointer before initial map generation.

## Preserved-ROM 0571→0572 comparison

The two 4,443,832-byte ROMs differ at 1,328,262 byte positions in 394,555 exact adjacent runs. Grouping exact runs separated by at most 256 unchanged bytes yields 318 broad regions. Counts by broad ROM ownership are:

- header `$000000–$0001FF`: 2 bytes;
- copied maincpu `$000200–$06FFFF`: 117 bytes;
- native helpers `$070000–$0FFFFF`: 177,323 bytes;
- generated assets/tail `$100000–EOF`: 1,150,820 bytes.

The largest merged regions are `$30AF40–$35E4FF`, `$1B7627–$1F80AF`, `$143FB6–$17C663`, `$2D51FC–$309FAD`, `$208900–$238BFF`, and `$0700C9–$0846E2`. Raw same-offset ROM diffing is much broader than the semantic edit because helper-size changes move linker payloads and generated profile data. The authoritative finite semantic boundary is therefore the four production-source files and the 0139 commit diff above, correlated through the generated address map rather than interpreting shifted tail bytes as independent changes.

## Plane-A failure mechanism and first divergent event

`MAP_GET_AUTHORED_VISUAL_A0` in `tilemap_hooks.s` directly loads `diagnostic_palette_active_visual_index`. A zero pointer returns no authored visual record. Despite its diagnostic-era name, this is production graphics state.

| Semantic event | Build 0571 | Build 0572 |
|---|---|---|
| scene preparation begins | gameplay package selected | same |
| graphics package prepared | cache/package state prepared | same |
| authored visual context | selected as a side effect of `vdp_install_test_lines` | asset and visual pointer cleared; installer owner-gated |
| Plane-A initial map generation | valid visual index available | visual lookup can see zero and omit authored contents |
| palette presentation | Test palette acquired too early | retained presentation writers remain eligible |
| package install | installer reasserts visual + palette | installer skipped while asset zero |
| VBlank/display | publishes prepared map | faithfully publishes incomplete staging |
| later `$059AD4` | gameplay palette already active | activates palette/map/visual too late for the already-generated initial map |

The first divergence is visual-context selection, before Plane-A initial-map population. The failure class is primarily **B/F**: active authored LUT/visual context was not initialized, so staging was generated from missing source state; later DMA could correctly publish an incomplete buffer. It was not caused by Plane-B, scroll, palette invisibility, or a missing DMA request.

## Exact responsible 0139 hunks

The responsible combination is:

1. `scene_load.s` cleared `diagnostic_palette_active_visual_index` and removed the gameplay-preparation `vdp_install_test_lines` call;
2. `fg_tile_cache.s:fg_boundary_install` skipped `vdp_install_test_lines` while `diagnostic_palette_active_asset==0`;
3. `vdp_comm.s:vdp_refresh_test_lines_if_scene_changed` returned under the same zero-owner condition.

No single dirty flag was missing. All three paths made graphics visual selection wait for the later palette owner.

## `diagnostic_palette_active_asset` audit

- Original/established role: selected offline authored asset ID; the installer used it alongside the separate visual-index pointer.
- Writers: `vdp_install_test_lines` clears then sets it; non-gameplay scene preparation clears it.
- Readers: palette hooks protect Lines 0/1/3; scene/package refresh chooses map/refresh behavior; `fg_tile_cache.s` owner-gated installation.
- Lifetime after 0139: retained gameplay palette load to the next non-gameplay owner.
- Conclusion: it is usable as the existing authored **palette/map owner**, although its name is historical. It is not a graphics-residency discriminator. The production Plane-A consumer reads `diagnostic_palette_active_visual_index`, not the asset flag. 0139 incorrectly extended the asset owner's zero interval to that graphics pointer. No replacement lifecycle flag was added.

## Original arcade presentation ownership and element proof

Existing original-ROM provenance and prior original-arcade captures were reused rather than inventing another capture system:

- frontend plane/HUD bank 0 source: maincpu `$04EAF6`;
- frontend companion plane bank 1 source: `$04EB16`;
- frontend PC090OJ sprite bank 48 source: `$04FE62`;
- Stage Clear message: retained PC080SN attribute 0, therefore physical bank 0;
- Stage Clear figure: retained attribute/bank 5, with its independent Line-1 conversion;
- native `1UP`, P1 score, `HIGH SCORE`, high score, `2UP`, and P2 score: `native_hud_static_sat.bin` attributes are `0xC53B`, `0xC53F`, and the same `0xCxxx` family, which selects Genesis palette Line 2;
- the generated frontend Line 2 is exact converted original sprite bank 48: `0000 0000 0008 004E 008E 00EE 08EE 0EEE 0A00 0E40 0E80 0EC0 0EEA 0000 0000 0000`.

The arcade does not have this collision: PC090OJ sprite bank 48 and PC080SN Layer-B palette storage are independent hardware surfaces. Genesis compressed both onto CRAM Line 2. During READY, Stage Clear, congratulations/inter-round, GAME OVER, and title presentation, the native frontend HUD remains the visible consumer and therefore needs the PC090OJ bank-48 line. During gameplay, the frontend HUD is deactivated and the resident staged PC080SN Layer-B line must be visible.

The retained event matrix remains:

| Phase | Graphics/palette fact |
|---|---|
| title | frontend HUD owner; bank 0/1 plane lines and PC090OJ bank 48 sprite line |
| R1/R2 READY, including respawn | frontend HUD visible; retained presentation plane writers active; active-human staged Layer-B L2 remains resident |
| first gameplay frame | retained `$059AD4` current-round palette load activates Test 2.0 Lines 0/1/3 and PC090OJ authored map; frontend HUD deactivates, exposing staged gameplay L2 |
| R1-S3 boss | gameplay owner; Test 2.0 and boss fade semantics remain |
| Stage Clear/congratulations | Stage Clear bank-0 text + bank-5 figure; frontend top HUD needs PC090OJ bank 48 |
| GAME OVER/return title | frontend owner again; original frontend line visible |

A fresh complete 13-phase ORIGINAL ARCADE dynamic capture was not completed in 0141. The correction is based on the already established original ROM sources, attributes, retained events, and prior captured lifecycle. This limitation remains explicit and does not weaken Tighe's required visual acceptance.

## Why Build 0572 top text remained wrong

0139 correctly delayed Test 2.0 Lines 0/1/3, but `1UP`, `HIGH SCORE`, and `2UP` do not use those lines in the native frontend package. They are PC090OJ-derived SAT records selecting Genesis Line 2. During an active-human READY/round transition, PROMT-ID-0138 intentionally preserved the resident gameplay Layer-B staged L2. Build 0572 then published that gameplay L2 to actual CRAM, so staged CRAM equaled actual CRAM while the sprite glyphs indexed the wrong palette. The automated equality was internally consistent and visually wrong.

`ROUND 1`, `ROUND 2`, `READY !`, and Stage Clear message/figure retain their established PC080SN/bank-0 and figure/bank-5 routing. The new correction does not recolor or remap those consumers.

## Production correction

### Graphics initialization

`vdp_prepare_test_visual_context` selects only the stage-authored Plane-A visual descriptor. It runs during gameplay scene preparation, package activation, and scene-context refresh. It does not set `diagnostic_palette_active_asset`, copy colors, select the authored PC090OJ map, or request palette publication. `vdp_install_test_lines` still acquires actual Test 2.0 Lines 0/1/3 and sprite-map ownership at the retained `$059AD4` gameplay palette-load event.

This preserves 0139's valid distinction while restoring the graphics side effect that Build 0571 supplied too early through a coupled palette installer.

### Presentation palette

The existing `native_hud_mode==FRONTEND_FULL` is the semantic visible consumer. Entering or leaving that owner requests one normal VBlank palette publication. `vdp_commit_palette` first publishes the sole 64-word staged palette. While FRONTEND_FULL owns the HUD, it then publishes only original frontend sprite bank 48 to actual CRAM Line 2. The staged Line 2 is never overwritten. Leaving frontend mode publishes the staged gameplay line again.

There is no new shadow palette, scheduler, READY/round/score hardcode, screen-content discriminator, palette-editor edit, freeze, or per-frame reload.

## PROMT-ID-0138 non-regression

PROMT-ID-0138 requires active-human presentation not to destroy resident gameplay Layer-B L2 because later R2 fade rows use `$FFFF` keep semantics. Build 0573 preserves that exact staged line. The frontend bank-48 overlay affects only actual CRAM while the frontend HUD is visible; it cannot become the source for a later sparse gameplay fade. When gameplay resumes, the unchanged resident staged line is republished. The source correction from `538fac0c` was not modified.

## Why the old gates missed both failures

- Gameplay-entry/selector gates checked eventual state, package, pattern residency, and successful entry. `$059AD4` eventually initialized the visual pointer, so they did not assert that the pointer existed before the first map generation/visible frame.
- The 0139 palette traces asserted staged palette equals actual CRAM. They had no oracle assertion that the top HUD selects Line 2 or that actual presentation L2 must equal original PC090OJ bank 48 while staged gameplay L2 remains resident.
- Direct starts and bounded attract tests reached stable later states; they did not compare the first visible Plane-A frame against 0571 or the arcade.
- Static scene-map gates prove generated map correctness, not runtime selection ordering.

No new test infrastructure was added. The existing functional entry probe was reused against the six required early contexts. It now records the expected stage/record/package, zero A/B misses, and populated direct-start Plane-A/Plane-B name tables. This is useful mechanical coverage but is not described as visual acceptance.

## Build 0573 verification

- Assembly and link: PASS.
- Canonical gate: PASS.
- Gameplay-entry gate: PASS.
- Mandatory 30-second USA/NTSC Genesis trace: PASS; no address/bus/illegal/crash-handler error reported.
- Palette-family verification using `Test_2_0.json` SHA-256 `4339688ebe07bc121d5108d464f57b320a6628f4c36cdd71a95cfe5ea8c964cf`: PASS.
- Complete canonical diagnostic family: PASS.
- All 18 direct-subround derivatives generated and selector-verified: PASS.
- Focused canonical, R1-S2, R1-S3, R2-S1, R2-S2, R2-S3 functional probes: PASS. Required stage/record/package selected; `miss_a=0`, `miss_b=0`; each direct-start target reported 2048 nonzero name-table words on both planes.
- Legacy phase-epoch automation: **FAIL/warning**, because the bounded automated route remained at record 0 and did not reach the requested later epoch. The ROM was correctly preserved. This is not represented as a graphics failure or as acceptance evidence.
- Natural R1-S1→R1-S2→R1-S3→Stage Clear→Round 2, death/respawn, exact Record-29 progression, GAME OVER/title return, and two complete attract cycles were not all rerun after the final 0573 source. Those remain Tighe tests/unproven items.
- Audio source was not edited. No audible listen was performed.

## Build artifacts

Every listed file is 4,443,832 bytes.

| Artifact | SHA-256 |
|---|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0573.bin` | `1b396536f2a3543e42e6cab9b73e2f9bd67e40486ec3b070aa323223bc985b2f` |
| `dist/rastan-direct/rastan_direct_video_test_build_0573_invincible.bin` | `b42ae3e18e38d28133079b91eca1ce8b64d666ad1b00a1624d4b9d884891fbc0` |
| `dist/rastan-direct/rastan_direct_video_test_build_0573_S1-2.bin` | `9da1d9890eb214682c658a40c50a222768d1bc1290a81772984cbadd91e3aa89` |
| `dist/rastan-direct/rastan_direct_video_test_build_0573_S1-3.bin` | `83fb121e2c575a0fd75c138265905d4fe4e0101798c6db976ab33537db76b9fe` |
| `dist/rastan-direct/rastan_direct_video_test_build_0573_S2-1.bin` | `1aac94b769561987fd6b7ea18063f0796cc0840dccee28d6ec20efdc0c2b23a7` |
| `dist/rastan-direct/rastan_direct_video_test_build_0573_S2-2.bin` | `d38283a6a8dd877c857ea72268e3f3d1bf87c483e9bb4f0cf9f6d71f0abb9f70` |
| `dist/rastan-direct/rastan_direct_video_test_build_0573_S2-3.bin` | `404c68191de7ef0eb01c2a146bad258b807797cad56faff95d861878588b02c0` |

Counter after delivery: 573. Build 0573 includes the preserved concurrent PROMT-ID-0135 audio source.

## Files changed and commits

Production source commit `579d1b43`:

- `apps/rastan-direct/src/vdp_comm.s`;
- `apps/rastan-direct/src/scene_load.s`;
- `apps/rastan-direct/src/fg_tile_cache.s`;
- `apps/rastan-direct/src/hud_native.s`;
- `apps/rastan-direct/src/dma.s`.

Documentation/ledger work:

- this report;
- `OPEN_ISSUES.md`;
- append-only `AGENTS_LOG.md` entry.

## Open/Closed Issues impact

- OPEN-040 remains open. Tighe reports the 0138 defect visually fixed, but its exact Record-29 plus later-progression closure condition remains.
- OPEN-041 records Build 0572's palette rejection and Build 0573's corrected Line-2 presentation candidate.
- OPEN-042 separately records the Build-0572 Plane-A initialization regression and candidate correction.
- No issue was silently closed.

## Required Tighe test

Test the normal 0573 ROM first. Follow title → R1 READY → first R1 frame → death/READY/resume → natural R1-S2 → R1-S3 → boss defeat → Stage Clear/congratulations → ROUND 2 READY → R2-S1 → progressed Record-29 death/respawn → later R2-S1 → R2-S2/R2-S3 → GAME OVER → title. At each presentation compare `1UP`, `HIGH SCORE`, `2UP`, READY text, Stage Clear text/figure, and the first visible Plane-A frame. Then allow two normal attract cycles. Build 0573 remains a candidate until that visual/gameplay pass.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0141
