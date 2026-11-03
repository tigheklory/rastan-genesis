# Cody Build 0436: Independent Frontend / Gameplay Vertical Origins

## 1. Baseline

Accepted baseline: Build 0435. Build 0436 is a presentation/configuration-only change. It does not
restore the lower HUD, change gameplay/world coordinates, or begin Phase D/E.

The graphics-policy boundary is unchanged: retained arcade scene, object-position, animation, and
scroll decisions remain above the semantic cut; the existing native tails produce final Genesis SAT
coordinates and Plane A/B VSRAM values below it. No PC080SN/PC090OJ chip-shaped tail, shadow, mirror,
projector, or transitional compatibility path was introduced.

## 2. Two build-time origin constants

`apps/rastan-direct/Makefile` now defines two positive-convention logical origins:

```make
RASTAN_FRONTEND_Y_ORIGIN ?= 8
RASTAN_GAMEPLAY_Y_ORIGIN ?= 8
```

The accepted defaults remain 8/8. Values are command-line overridable in the inclusive range 0..224;
zero is intentionally allowed for a controlled no-crop experiment. No origin-specific ROM suffix or
automatic variant cross-product was added.

## 3. Static confirmation of bottom-HUD inheritance

Confirmed before editing. The recovered arcade geometry is reserve lives Y=`0xE4`, energy/status
Y=`0xE8`, four pickup/status slots Y=`0xE8`, and persistent ROUND label/digit Y=`0xE8`.

The existing direct-native energy producer writes its semantic raw Y into `native_queue_hud` without
the fixed-screen top-HUD marker. Gameplay lanes are consumed by `.Lnq_emit_lane` and the single shared
SAT finalizer. Reserve lives, pickup/status, and ROUND are not restored here; their future native
representation must use the same unmarked semantic queue contract. They will therefore derive
`screen_y = raw_arcade_y - RASTAN_GAMEPLAY_Y_ORIGIN` with no separate HUD-origin control.

## 4. Static confirmation of scene-selection boundaries

`pc090oj_native_emit_pass` is the complete sprite presentation split:

- scene 1 selects `.Lnq_gameplay` and `RASTAN_GAMEPLAY_Y_ORIGIN`;
- scene 0 title/attract frontend states and scene 2 select the native frontend paths and
  `RASTAN_FRONTEND_Y_ORIGIN`.

Gameplay queues and direct frontend producers converge on the same final SAT coordinate realization.
No raw-coordinate native sprite producer bypass was found. `vdp_commit_scroll` uses the same existing
scene distinction for the Plane A/B VSRAM values. A no-human demo while the game is actually in scene 1
correctly remains a gameplay presentation and uses the gameplay origin.

## 5. Frontend origin path

At the sprite pass boundary, non-gameplay scenes select `RASTAN_FRONTEND_Y_ORIGIN` into
`native_active_y_origin`. Every non-fixed frontend sprite reaches the shared finalizer and subtracts
that value. At VSRAM publication, non-gameplay scenes select the frontend constant and add the same
value to both Plane A and Plane B scroll derivations.

## 6. Gameplay origin path

At the same sprite boundary, scene 1 selects `RASTAN_GAMEPLAY_Y_ORIGIN`. Every raw-coordinate gameplay
lane (player, weapon/front effect, enemy, and raw lower-HUD semantic tuples) subtracts that one selected
value in the shared finalizer. No actor or world coordinate is modified.

## 7. Plane A/B derivation

`vdp_commit_scroll` selects one domain origin once, then uses it for both planes:

```text
Plane A VSRAM Y = -staged_scroll_y_fg + active_origin
Plane B VSRAM Y = -staged_scroll_y_bg + active_origin
```

The gameplay 9-bit VSRAM mask remains unchanged. Plane A and Plane B cannot drift to different
configurable origins.

## 8. Native sprite derivation

The final native SAT coordinate path is:

```text
raw screen sprite Y = arcade semantic Y - active_domain_origin
```

`native_active_y_origin` is a two-byte presentation value selected once per existing sprite pass. It
does not own scene lifecycle, frame progression, gameplay, or scheduling.

## 9. Top HUD isolation

The native top HUD already carries the finalizer's bit-14 fixed-screen marker. Those tuples retain the
accepted Build-0435 fixed `-8` SAT placement and do not read either new origin. Source HUD geometry was
not edited. Consequently changing only the gameplay origin does not move 1UP, P1 score, HIGH SCORE,
2UP, or their top labels/digits; `_full_hud` uses the same rule.

## 10. Collision/world isolation

Only `pc090oj_hooks.s` final SAT realization and `vdp_comm.s` final VSRAM realization reference the
generated origin constants. Actor/player/enemy logical Y, collision maps and probes, grounding,
hurtboxes, hitboxes, sword/contact geometry, camera gameplay state, world progression, and rope contact
do not reference them and were not changed.

## 11. Retired compensation check

Static search confirms `.Lb2c8_yfix`, `RASTAN_VERTICAL_CROP_BIAS`, and the retired object-specific /
`BACK_ENEMY -8` compensation are absent from production source/specs. None was restored or
parameterized. The Build-0282 collision-source correction remains independent.

## 12. Makefile/config receipt

Both values are emitted into `out/pc090oj_config.inc` and copied into every existing variant receipt.
`verify-variant-set` now verifies them in canonical, `_d`, `_s`, `_do`, `_c`, and `_full_hud` receipts.
Every Build-0436 receipt records frontend 8 and gameplay 8. `_full_hud` inherits the canonical gameplay
origin; its only intended difference remains HUD mode 1.

## 13. Default 8/8 equivalence

Default presentation math is equivalent to Build 0435:

- frontend raw sprites: `Y - 8`;
- gameplay raw sprites: `Y - 8`;
- fixed top HUD: unchanged fixed `Y - 8` placement;
- Plane A/B: `-scroll_y + 8`;
- viewport: unchanged top 0, bottom-exclusive 224.

The whole ROM is not byte-identical because selection/configuration instructions and build metadata
were added. The default coordinate results and clipping bounds are behaviorally identical.

## 14. Alternate compile-time configuration proof

Without linking or numbering a ROM, these two affected objects were assembled with
`RASTAN_FRONTEND_Y_ORIGIN=8 RASTAN_GAMEPLAY_Y_ORIGIN=0`. The generated receipt recorded 8/0 and both
objects assembled successfully. Static inspection proved the frontend immediate remained 8, gameplay
changed to 0, fixed-HUD placement remained independent, and no collision/world source acquired an
origin reference. The default 8/8 objects were then rebuilt before the release workflow. This is only a
compile/configuration proof, not accepted alternate gameplay behavior.

## 15. Build artifacts

All artifacts are 2,698,936 bytes:

| Artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0436.bin` | `af98cd46add652b031d22c11af4655387a655ada596b9a190ab746f0ad8d3dd0` |
| `rastan_direct_video_test_build_0436_d.bin` | `3d2c06ce34a55e1abb384219dc638ab65ed6ec462c67f4a6ab24d9a37337b663` |
| `rastan_direct_video_test_build_0436_s.bin` | `fa27c8348a59637d8e73a8291b4d422d30ec14d4bf2948102d3f11fe450441ed` |
| `rastan_direct_video_test_build_0436_do.bin` | `e04d869001caff1bbfa66acafeb9120551e0cdb34170afcca6a81781ab980214` |
| `rastan_direct_video_test_build_0436_c.bin` | `bda51e7191c6f93dc3c21e02cb1cede296306a790505eb46c9e975d986630789` |
| `rastan_direct_video_test_build_0436_full_hud.bin` | `aca6f611bbc6414ea7b49976527feb765d69a560752c394518d033412e0c597a` |

Counter: 436. Ledger: canonical PASS, gameplay-entry PASS, known seven-epoch gate FAIL.

## 16. Standard validation result

The Makefile-owned fixed 30-second Genesis NTSC MAME trace completed normally at 1,798 frames:
`states/traces/rastan_direct_video_test_build_0436_mame_30s_20261016_211633/`. No new trace script,
route, manual gameplay, or benchmark was created. The rope benchmark is not part of the normal release
workflow and was not run.

## 17. Deterministic rope-race addendum

The established Genesis NTSC MAME rope-attachment benchmark was run unchanged for three trials on
each already-built ROM. The canonical ROM produced `807,807,807` frames, with a median of
13,467.341 ms. This is a deterministic regression of 4 frames / 66.753 ms / 0.498% versus Build
0435 canonical, and leaves a 36-frame / 617.341 ms gap versus the 771-frame arcade silver standard.

The `_full_hud` ROM produced `861,861,861` frames, with a median of 14,368.501 ms. This is a
deterministic regression of 7 frames / 116.817 ms / 0.820% versus Build 0435 `_full_hud`, and leaves
a 90-frame / 1,518.501 ms gap versus arcade. Build 0436 full HUD is 54 frames / 901.160 ms / 6.691%
slower than Build 0436 canonical. The full-HUD penalty therefore increased from Build 0435's 51
frames to 54 frames: +3 frames / +50.064 ms, with the percentage separation increasing from about
6.351% to 6.691%.

The result is deterministic and shows that the vertical-origin split is not performance-neutral in
this benchmark. Per the benchmark-only stop rule, no cause investigation or implementation was
performed.

- Existing project tools reused: `tools/mame/run_rope_attach_performance_benchmark.sh`,
  `tools/mame/scripts/rope_attach_performance_benchmark.lua`, and
  `tools/mame/summarize_rope_attach_benchmark.py`.
- New tooling created: none.
- Why new tooling was necessary: not applicable.
- Evidence:
  `states/traces/build0436_rope_attach_benchmark_reduced_hud/` and
  `states/traces/build0436_rope_attach_benchmark_full_hud/`.

## 18. Hardware acceptance requirements

Tighe must verify on real Genesis hardware that the default 8/8 candidate preserves Build-0435 title,
attract, gameplay, plane/sprite alignment, and top-HUD placement. No alternate gameplay origin is
accepted by this task. Bottom-HUD restoration remains a separate future task. Phase D and Phase E were
not started.

### Native-replacement policy checklist

- Semantic cut: retained arcade scene/object/scroll decisions to final native SAT/VSRAM realization.
- Chip tail removed/bypassed: unchanged from the established native paths; no PC080SN/PC090OJ tail was
  reintroduced.
- Chip-shaped state consumed: no.
- New mirror/shadow/projector/device dispatcher: no.
- Transitional compatibility added: none.
- Arcade gameplay/frame/VBlank ownership preserved: yes.
- Final Genesis SAT/VSRAM output produced directly: yes.
