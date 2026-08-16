# Build 0281 Attack Hitbox Coordinate Alignment

## BASELINE / CONTROL METHOD

- **PROVEN:** Accepted baseline: Build 0281, SHA-256
  `8f4997566386f30c0c3dd37f922762d7f6b0677f8bbd9c4a8995046dfb9ab790`, counter 281.
- **PROVEN:** No production source, specification, ROM, or counter change was made.
- **PROVEN:** Two deterministic Genesis NTSC MAME runs used the same scripted startup and
  spacing. Both pressed P1 B on external frames 790..793. The crouch case additionally held
  P1 Down on frames 765..825; the standing case never pressed Down. No memory was seeded or
  forced. Both captures ended at external frame 880.
- **PROVEN:** Evidence is preserved under
  `states/traces/build0281_hitbox_coordinate_alignment_20260814_185710/`, principally
  `standing_frames.csv`, `crouch_frames.csv`, the corresponding `*_actors.csv` and
  `*_queues.csv`, and `capture.lua`.
- **LIMITATION:** This MAME configuration did not expose 68000 opcode execution through the
  attempted Lua read taps, so `*_selectors.csv` and `*_overlap.csv` contain headers only and
  `event_count=0` does **not** mean the collision routine did not execute. The runtime result
  below is instead proven from the live fields consumed by retained code, the exact retained
  table/function, and the actor's observed hit-state transition. No direct-PC claim is made.

## STATIC BACK_ENEMY -8 PROVENANCE

- **PROVEN:** `native_sprite_emit` in
  `apps/rastan-direct/src/pc090oj_hooks.s:441` receives each already-expanded semantic piece
  as word0/Y/code/X. Only the `NATIVE_LANE_BACK_ENEMY` branch at lines 492..499 subtracts 8
  from D2 before storing the queue word. It does not write actor state or collision data.
- **PROVEN:** The adjustment is after semantic actor-piece expansion. The retained direct
  expander in `apps/rastan-direct/src/tilemap_hooks.s:2206` computes piece Y as signed
  descriptor Y plus actor A4+0x1A (and conditionally A4+0x18) at lines 2241..2248, then calls
  `native_sprite_emit` at line 2258.
- **PROVEN:** Every lane later receives the separate global
  `PC090OJ_TO_GENESIS_Y_OFFSET=-8` at `pc090oj_hooks.s:1784`, then the final screen coordinate
  is encoded as Genesis SAT Y plus `0x80` at lines 1896..1900.
- **PROVEN:** The global -8 is the documented arcade-visible-origin conversion: arcade
  raster Y=8 maps to Genesis display line 0 (`pc090oj_hooks.s:166..180`). This is a shared
  viewport convention, not the BACK_ENEMY correction.
- **PROVEN:** The BACK_ENEMY-only subtraction applies to every piece published through that
  lane, across actor families. It is not limited to family 0, one actor, or one tile.
- **PROVEN:** `build/rastan-direct/address_map.json` maps the retained family-0 actor renderer
  and collision code as executable spaces; no arithmetic address assumption was used. Key
  correlations include `arcade_pc 0x0446BC -> runtime_genesis_pc 0x0448BC`,
  `arcade_pc 0x044CBA -> runtime_genesis_pc 0x044EBA`, and
  `arcade_pc 0x054864 -> runtime_genesis_pc 0x054A1A`.

## ORIGINAL ARCADE RENDER-vs-COLLISION COORDINATE CONTRACT

- **PROVEN:** Original actor rendering and actor hurtboxes share A4+0x1A as their logical Y
  anchor. The renderer adds signed per-piece descriptor Y to A4+0x1A; the hurtbox consumer
  adds signed extent-table Y to A4+0x1A. The PC090OJ visible-area conversion occurs after
  this shared semantic coordinate.
- **PROVEN:** KF-067's matched arcade/Genesis evidence measured the grounded Stage-1 actor
  anchor as arcade `0x79` (121) versus Genesis `0x81` (129), with identical world/camera
  inputs. It also measured arcade visible foot Y=129, pre-correction Genesis foot Y=137, and
  corrected Genesis foot Y=129.
- **PROVEN:** Thus the corresponding arcade relationship is: logical/hurtbox anchor 121,
  rendered composition bottom 129. Build 0281 instead has logical/hurtbox anchor 129 and
  rendered composition bottom 129 because only representation was moved upward.
- **DISPROVEN:** The arcade intentionally has the additional Genesis relationship where the
  hurtbox anchor is 8 pixels lower relative to the visible actor. That extra relative delta
  was introduced by the Genesis collision-map/actor-placement defect plus render-only
  compensation.

## BUILD0281 PLAYER COORDINATE FLOW

- **PROVEN:** Player offensive rectangles anchor directly to A5+0x10BE (X) and A5+0x10C0
  (Y). The controlled runs observed player X=`0x0020` (32) and Y=`0x0070` (112).
- **PROVEN:** Original BODY piece expansion uses signed descriptor Y plus A5+0x10C0 and
  signed/facing-adjusted descriptor X plus A5+0x10BE. The retained player adapter
  `native_player_piece` (`pc090oj_hooks.s:404..411`) copies the expanded Y from D6 to D2 and
  publishes it without a player-lane bias.
- **PROVEN:** PLAYER_BODY queue samples at standing frame 804 retain semantic Y values
  `0x51/0x61/0x71/0x81`; the shared viewport -8 yields screen Y
  `73/89/105/121`. The observed opaque BODY span is approximately Y=81..128.
- **PROVEN:** Rastan's rendering and offensive collision therefore share the retained
  logical player coordinate system. The only render transform is the common arcade-visible
  origin conversion. There is no Genesis-only PLAYER_BODY semantic-lane Y divergence.

## BUILD0281 ENEMY COORDINATE FLOW

The measured flow for actor record 8 is:

```text
original arcade logical actor Y / hurtbox anchor       121 (0x79)
Genesis collision-map-grounded logical actor Y         129 (0x81)  delta +8
Genesis hurtbox anchor                                  129         delta  0
expanded semantic piece Y                               actor Y + descriptor Y
BACK_ENEMY queue Y                                      semantic piece Y - 8
screen Y                                                queue Y - 8 (shared viewport)
SAT Y                                                   screen Y + 0x80
```

- **PROVEN:** Collision and hurtbox code never sees the BACK_ENEMY queue subtraction.
- **PROVEN:** The reason for the extra lane -8 is KF-067 category C/E/F: it compensates an
  earlier Genesis collision-map/grounded-actor placement error so all BACK_ENEMY actors
  appear at arcade Y. It is neither the global SAT convention (A) nor an original semantic
  renderer offset.
- **PROVEN:** For semantic equivalence, the actor logical coordinate must ultimately move
  with the corrected collision-map ground row. Applying -8 only to the hurtbox would be a
  symptom patch and is not authorized.

## LIVE SELECTOR VALIDATION

- **PROVEN:** Standing frames 804..805 have broad action 0, attack-active 1, phase 6,
  facing 0, variant 4, selector `0x05`, and offensive-enable 1.
- **PROVEN:** Crouch frames 803..804 have broad action 5, attack-active 1, phase 6,
  facing 0, variant 4, selector `0x0B`, and offensive-enable 1.
- **PROVEN:** The expected maximum-extension selectors are correct. The first divergence is
  not in action, enable, phase, variant, facing, or offensive selector production.

## LIVE STANDING OFFENSIVE RECTANGLE

- **PROVEN:** At standing frame 804, player anchor=(32,112), signed extents are
  X=`+24..+56`, Y=`-10..-8` for the observed facing.
- **PROVEN:** World offensive rectangle: X=56..88, Y=102..104. Maximum horizontal reach is
  56 pixels.

## LIVE CROUCH OFFENSIVE RECTANGLE

- **PROVEN:** At crouch frame 803, player anchor=(32,112), signed extents are
  X=`+24..+56`, Y=`+4..+6`.
- **PROVEN:** World offensive rectangle: X=56..88, Y=116..118. Maximum horizontal reach is
  also 56 pixels. The X intervals are identical; crouch is exactly 14 pixels lower.

## ACTOR-SCOPED HURTBOX

- **PROVEN:** The representative is exact actor record index 8. At standing frame 804 it is
  active, visual renderer class `0x18`, facing 0, state+3=0, byte+5=`0x02`, byte+6=`0x00`,
  X=`0x005C` (92), Y=`0x0081` (129), tile/code state `0x004B`, and state bytes
  +0x30/+0x37/+0x38/+0x3D/+0x3E/+0x3F are zero.
- **PROVEN:** This record is visually identified as the captured complete Stage-1 family-0
  Lizardman composition. It is **not** mislabeled collision actor type 17: the captured
  actor type byte +6 is zero.
- **PROVEN:** For actor index 8 and the captured zero states, retained selector logic at
  `arcade_pc 0x0446BC` (mapped runtime `0x0448BC`) reaches selector 0. The Build 0281 normal
  hurtbox table at `genesis_rom_offset 0x044EE0` begins `F4 0C EC 10`, signed extents
  X=`-12..+12`, Y=`-20..+16`.
- **PROVEN:** Logical hurtbox world rectangle: X=80..104, Y=109..145.

## VISIBLE ACTOR vs LOGICAL HURTBOX

- **PROVEN:** Standing frame 804 queue entries 27..43 are the actor-8 composition. Their
  semantic Ys are 97/98, 113/114, and 129/130; BACK_ENEMY queue Ys are each 8 lower, and
  final screen Ys are another 8 lower for the shared viewport. Cell bounds are Y=81..129;
  opaque bounds are Y=82..129.
- **PROVEN:** The visibly corrected Genesis actor bottom is Y=129, matching the arcade.
  The Genesis logical hurtbox anchor is also Y=129, whereas the arcade semantic relationship
  places the hurtbox anchor at 121 for a visible bottom of 129.
- **PROVEN:** The Genesis logical hurtbox is therefore displaced 8 pixels **below** its
  arcade-equivalent relationship to the visible actor. This equals the magnitude of the
  BACK_ENEMY representation correction, with opposite responsibility: rendering moved up
  8 while logical collision remained 8 low.

## 8-PIXEL COUNTERFACTUAL

Same player anchor and actor spacing:

| Coordinates | Player X | Player Y | Hurtbox X | Hurtbox Y | X overlap | Y overlap |
|---|---:|---:|---:|---:|---|---|
| current standing | 56..88 | 102..104 | 80..104 | 109..145 | YES | NO |
| current crouching | 56..88 | 116..118 | 80..104 | 109..145 | YES | YES |
| visual-aligned standing | 56..88 | 102..104 | 80..104 | 101..137 | YES | YES |
| visual-aligned crouching | 56..88 | 116..118 | 80..104 | 101..137 | YES | YES |

- **PROVEN:** The counterfactual changes no emulated memory; it applies only the established
  8-pixel semantic alignment (`129 -> 121`) to the captured hurtbox.
- **PROVEN:** It makes the collision result match the visible arcade-equivalent scene: both
  attacks overlap at the same X spacing, while retaining the intended 14-pixel Y difference.
- **PROVEN:** Tighe's 8-pixel hypothesis explains the observed standing-tiny/crouch-large
  behavior. The perceived reach differential is vertical, not horizontal.

## ACTUAL OVERLAP TEST

- **PROVEN:** Retained `arcade_pc 0x044CBA`, mapped exactly to
  `runtime_genesis_pc 0x044EBA`, sign-extends the captured player and selected actor extent
  bytes, adds the captured logical anchors, and tests interval overlap on both axes.
- **PROVEN:** At standing frame 804 those exact inputs produce X overlap and Y miss. Actor 8
  remains byte+5=`0x02`, byte+0x3D=`0x00` through frames 800..806.
- **PROVEN:** At crouch frame 803 the exact inputs produce X and Y overlap. On that frame
  actor 8 changes byte+5 from `0x02` to `0x0F` and byte+0x3D from `0x00` to `0x10`,
  corroborating entry into retained hit/damage response.
- **LIMITATION:** This is an exact live-input and behavioral proof of the retained overlap
  result, not a claimed debugger breakpoint hit at `runtime_genesis_pc 0x044EBA`; opcode
  fetch taps were unavailable in the capture environment.

## FIRST GENESIS-vs-ARCADE DIVERGENCE

- **DISPROVEN:** Wrong standing/crouch selectors, horizontal extents, attack-enable timing,
  facing, player Y anchor, or a player render-only offset are the first divergence.
- **PROVEN:** The first relevant semantic divergence is earlier: the Genesis collision map
  grounds the representative enemy one 8-pixel row lower (actor A4+0x1A 129 versus arcade
  121). The native BACK_ENEMY lane then repairs only visible representation by subtracting
  8, leaving the actor hurtbox 8 pixels low relative to the arcade-equivalent visible actor.
- **PROVEN:** Root cause of the reported standing/crouch differential is established.
- **NOT YET SAFE TO IMPLEMENT:** The correct semantic boundary is the shared collision-map
  row/grounded-actor coordinate producer, followed by joint verification/retuning of the
  separately tuned player/map relationship, then retirement of the BACK_ENEMY compensation.
  A hurtbox-only -8, wider sword box, or lane-specific collision derivation would preserve
  the underlying split and is forbidden. The exact bounded production byte change is not
  available from this task alone because KF-067 proves that map, actor grounding, and player
  contact are coupled.

## CONCLUSION

- **PROVEN:** Native BACK_ENEMY render-only correction: queue Y -8, all lane pieces.
- **PROVEN:** Player render-vs-logical semantic divergence: none beyond shared viewport.
- **PROVEN:** Enemy hurtbox is 8 pixels below the arcade-equivalent visible relationship.
- **PROVEN:** Standing and crouch horizontal reach are both 56 pixels.
- **PROVEN:** Current standing misses only Y; current crouch overlaps both axes.
- **PROVEN:** Counterfactual 8-pixel semantic alignment makes both overlap.
- **PROVEN:** Tighe's hypothesis and the observed behavior are explained.
- **PROVEN:** No production change or Build 0282 was made; counter remains 281.
