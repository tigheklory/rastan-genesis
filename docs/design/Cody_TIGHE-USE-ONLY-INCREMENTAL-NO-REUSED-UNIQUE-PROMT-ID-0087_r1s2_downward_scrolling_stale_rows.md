# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0087

## Result

Build 0539 is the gameplay-test candidate for the R1-S2 downward Plane-A stale-row defect. The
production correction validates the actual 28-row visible bottom before it becomes visible while
retaining the independent four-row prefetch edge. It adds no tilemap shadow, full-scene backing map,
PC080SN emulation, duplicate graphics buffer, input special case, or coordinate special case.

Historical prompt `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0082` is replaced. The current
prompt is `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0087`.

Automated evidence proves the defective ownership rule and the corrected ordered history. Build 0539
is not accepted until Tighe verifies slow descent, fast fall/landing, reversal, and the final segment
in gameplay.

## Repository and Build-0538 baseline

- Starting repository HEAD: `07965e45735f6b9ec9f823472dfb56465ac6b708` (Andy 0086).
- Exact committed Build-0538 generated state: `c6aaddd100e88436905834aeb9c0196e79749d45`.
- `c6aaddd1` has parent `ab1c923c6fe3bbbff65ed9a6adb2d906016ab56f`; its changes are generated
  Build-0538 outputs/counter state. Current HEAD retains it as an ancestor and also preserves later
  Andy 0086 analysis.
- Build-0538 normal ROM was rechecked as
  `8279100957f710e768dece23a8b39d1b4c9e978228f0be89f31ec53926747ee6`.

Tighe established that Build 0538 initially renders R1-S2 correctly, then exposes a stale higher
logical row at the newly visible bottom while descending. Both a fast weapon-route fall/landing and a
slow chain descent reproduce it, so weapon acquisition, jumping, falling, and landing are not the
semantic cause.

## First bad downward transition and runtime path

The established Build-0529 runtime capture remains applicable because Build 0538 retained the same
no-publication hook direction and edge formula. In
`states/traces/r1s2_rope_build_0529/jump/frames.tsv`, frame 2530 records the first concrete
increasing-visible-top crossing in this history:

| Field | Value |
|---|---|
| old/new foreground Y | `$019C` -> `$0194` |
| old/new visible top | 13 -> 14 |
| newly visible bottom | logical 41 (`14+27`) |
| physical Plane-A slot | 9 (`41 & 31`) |
| record / selector / completed selector | 17 / 1 / 0 |
| strip / group / next-to-author front | 2 / 13 / 54 |
| executed runtime arm | arcade `$055790`; `genesistan_plane_a_pan_publish_entering_rows_up` |
| Build-0538 materializer target | logical 45 (`14+31`), physical 13 |
| required visible target | logical 41, physical 9 |

The helper name describes the retained arcade scroll arm, not the player-visible direction. `$055790`
subtracts the foreground scroll delta; `.Lplane_a_visible_top_from_scroll_d0` therefore increments the
visible top. That is Tighe's downward traversal: the entering display edge is the bottom at `top+27`.

Build 0538 invoked the row publisher and dirtied/published only the `top+31` prefetch row. It never
checked the newly visible `top+27` owner. VBlank ordering remained `FG_COMMIT>SCROLL_COMMIT`; the defect
is not a missed or reordered DMA.

## Stale provenance and N/N+32 result

The exact invariant is `physical = logical & 31`. A row authored or retained as logical `N-32` uses
the same physical slot as required logical `N`. Build 0538's provenance early-out is correct when the
requested logical owner is checked; the failure was that downward visibility checked the wrong edge.

The deterministic exact-asset history uses record 17, selector 1, completed record 16, front 52:

1. logical 44 is prefetched into physical 12;
2. ordinary legal authoring/retention installs logical 12 into physical 12;
3. visible top advances 13 -> 17;
4. Build 0538 validates only logical 45..48 (`top+31`), leaving logical 12 in physical 12 when logical
   44 becomes the newly visible bottom;
5. corrected code validates logical 41..44 (`top+27`) before visibility and also retains logical 45..48
   as prefetch.

The exact 128-byte generated row assets are discriminating:

- stale record-17 logical 12: SHA-256
  `e01c67747fe70b2353277748393bf667a0d00ed8f79b845bc1574a0be4af6c54`;
- required record-17 logical 44: SHA-256
  `ff3a46d77dc67365ea2296c0feab9a554354fb30787ed08058afffa7f051fc3a`.

Therefore the demonstrated stale owner is **N-32 aliasing**, not merely a valid but visually surprising
tile row. The first visible transition above has the same rule: required logical 41/physical 9 can
retain logical 9/physical 9 while the old helper updates logical 45/physical 13.

## Slow, fast, and reversal comparison

Slow descent and fast downward motion share `$055790` and the same loop. The delta only changes how
many row boundaries the loop consumes in one invocation. The regression runs four one-row crossings
and one four-row traversal from identical ownership history and requires identical final tags and
128-byte rows.

Direction reversal exposes the issue because ordinary selector-1/2 authoring may legally reuse an
offscreen physical slot after it was prefetched. On the next downward crossing, the old helper assumed
that four-row-old prefetch was still authoritative. The corrected helper asks the existing provenance
vector again at the moment the row reaches `top+27`. Exact ownership is a no-op; N/N-32 disagreement
materializes the required row. The opposite-direction entering-top path is unchanged and is explicitly
checked by the regression.

## Production correction and semantic cut

Source: `apps/rastan-direct/src/tilemap_hooks.s`,
`genesistan_plane_a_pan_publish_entering_rows_up`.

For every increasing-top crossing the helper now:

1. calls `.Lplane_a_publish_logical_row_native` for `new_top+27`, the newly visible bottom;
2. retains the existing call for `new_top+31`, the independent fourth prefetch row;
3. retains the existing Plane-B publication at its established prefetch edge.

The semantic cut remains:

`arcade camera/row-authoring decision -> final native Genesis Plane-A row ownership and words`.

The retired chip tail remains the PC080SN C08000/name-RAM destination machinery. Existing
`staged_fg_buffer`, the 32-byte logical-owner vector, dirty-row publication, and immutable native row
assets are reused. The correction does not recreate arcade name RAM.

Source/regression commit: `b6ab9d94502f0b597261059a0426e14547561385`.

## Regression and verification

`tools/translation/verify_bg_a_incremental_background.py` now contains an ordered history which fails
under Build-0538's `top+31`-only behavior and verifies:

- single-row and multi-row downward crossings;
- slow and fast traversal equivalence;
- up-to-down alias history and reversal;
- record 16/17, selector 1, current/predecessor selection, and a partial-record front;
- exact N/N-32 ownership and exact native row contents;
- visible bottom `top+27`;
- preserved four-row prefetch `top+28..top+31`;
- unchanged opposite-direction entering-top behavior.

Passed for Build 0539:

- full-span incremental Plane-A gate, selector-0/selector-1/2 equivalence, scene/pan/native maps;
- canonical gate, gameplay-entry gate, six Round-1 package/epoch cases;
- mandatory 30-second Genesis NTSC MAME trace;
- normal and invincible R1-S2 direct starts at stage `$0010`, record `$0011`, package 5, complete Plane
  A/B, zero map misses;
- natural transition gate: R1-S2 stable with generated palette MATCH and authentic `$25,$1B`; R1-S3
  stable with authentic `$25,$1C`;
- direct-start audio gate: `$27,$1B`, correct stream and zero bank mismatches.

These automated results prove source/build contracts, not visual gameplay acceptance.

## Final-segment pipe row

**OPEN.** No source-backed first-bad capture proves that the known final-segment stale 8-pixel pipe row
has this same history. Build 0539 may fix it if its owner reaches visibility through the corrected
`$055790` path, but this report does not claim that before Tighe retests it.

## Updated Test profile and 29/109 warrior integration

Tighe's updated Test profile initially cleared the shared/base R1-S1 Line 3 while editing the R1-S3
context. At Tighe's explicit request, only that Line 3 was restored byte-for-byte to its prior values;
the new R1-S3 context palette, weapon mapping changes, and all other updated data remain intact.

- Build profile SHA-256:
  `e03dd2aa24f30adb3fd0566af0b917914b49d8cd1533441431be485dd2d6b730`.
- Profile/restoration commit: `a3dcdbad`.
- Build-0539 generated-output/counter commit: `86c0d680`.
- Palette Composer source modified by Cody: **NO**.
- Current post-0084 warrior generation: **29 programs / 109 distinct codes**.
- `$97-$9C` included: **YES**.
- `$A1-$A6` included: **YES**.
- `$74` excluded: **YES**.
- sword `26B-274` covered: **YES**.
- `verify_green_knight.py`: 31 PASS.
- `verify_reindexed_pc090oj.py`: PASS, 109/109 exact, zero stray writes.

## Build 0539 artifacts

Every listed ROM is 3,841,720 bytes. Counter/ledger: 0539, produced 2026-11-05.

| Purpose | ROM | SHA-256 |
|---|---|---|
| Normal natural progression | `dist/rastan-direct/rastan_direct_video_test_build_0539.bin` | `9ef1bc1aad1faed9a71ba49faae2b4d354931d6a12e0d5ce5af5076075e99bd9` |
| Normal-play invincible | `dist/rastan-direct/rastan_direct_video_test_build_0539_invincible.bin` | `2e273e34e737c06b782469a30b3bce69f76cfd9ef85b8c36d80dee1e62c57235` |
| R1-S2 direct start | `dist/rastan-direct/rastan_direct_video_test_build_0539_S1-2.bin` | `e8035dc4ebcd39824cb388d40b5505bbb954dcea0f73e2ead13ec068f23af116` |
| Invincible R1-S2 direct start | `dist/rastan-direct/rastan_direct_video_test_build_0539_invincible_S1-2.bin` | `9d33e71913373fa4164ba3120d39a90ec5b680cf6e667f822af8d954be0a0182` |

## Manual test for Tighe

Primary ROM: `rastan_direct_video_test_build_0539_invincible_S1-2.bin`.

1. Climb through the currently correct area, stop, reverse, and descend slowly on the chain.
2. Inspect every newly exposed bottom row for chain fragments or higher-level scenery.
3. Climb again, jump/fall, and repeat the weapon-upgrade landing route.
4. Continue through the final segment and report whether the known stale pipe row remains.
5. Observe warriors in normal, reaction/low, airborne, state-$1F weapon-action, and rope states.
6. Use the normal ROM for natural R1-S1 -> R1-S2 -> R1-S3 and confirm scenery/palette plus
   Re-In-Carnation and The Devil Boss Carnival.

Andy 0086 analysis is preserved. No GitHub push was performed.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0087`
