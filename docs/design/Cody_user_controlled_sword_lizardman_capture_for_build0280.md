# Build 0279 User-Controlled Sword / Lizardman Capture for Build 0280

Status: **CORRECTED CAPTURE ANALYZED; EVIDENCE ONLY; NO BUILD**  
Task type: interactive user-controlled runtime evidence  
Accepted baseline: Build 0279  
Counter: 279

## Authoritative Corrected Capture

The action-labeled evidence for this report is the completed passive capture at:

`states/traces/build0279_user_controlled_sword_lizardman_corrected_20260812_092432/`

It contains 16 user markers across 16,256 external frames. The logger supplied no gameplay
input and performed no memory writes. Tighe performed the actions manually. The earlier
unmarked capture analyzed below remains useful supporting evidence, but this corrected capture
supersedes it wherever action labels or the bad-Lizardman interval are required.

### Marker map

| Marker(s) | Frame(s) | User label | Corrected-capture result |
|---|---|---|---|
| 1-4 | 5263, 5382, 6001, 6119 | standing attack | Both intended directions were marked. The retained windows contain `attack_type=4`, facing groups `0/2`, and transitions through `crouch=1`, but not the statically expected standing selector. Treat these as user-labeled standing windows, not proof of the exact standing table selector. |
| 5-9 | 7111, 7287, 7444, 7846, 7965 | crouch attack | Conclusive correlation: active rows have `action=5`, `attack_type=4`, `crouch=1`, and both canonical facings `3` and `2`. |
| 10 | 9182 | palette flash | The marked interval keeps `sprite_ctrl=0x0060` and `colbank_bits=0x0060`; exact player BODY matches nevertheless include nibble-3 SAT entries resolved to line 0. |
| 11-15 | 10007, 10072, 10168, 10295, 10385 | bad Lizardman club pose | Repeated markers preserve the user-observed bad pose interval. Live actors are family 0, classes `0x17/0x18`, base tile `0x004B`, attr `0x46`; code `0x004E` reaches SAT. |
| 16 | **15617** | downward thrust | This is the sole recorded `O` marker and the authoritative thrust marker. The actual thrust occurred after it, outside the logger's 90-frame post-marker window. |

The emulator was running at roughly 276%, the marker and action keys were far apart, and Tighe
warned that action onset could lag a marker by as much as about one second. That latency exceeds
the logger's 90-frame retention window in the downward-thrust case. The missed thrust rows are a
capture-window design limitation, not evidence that Tighe failed to perform the action.

### Corrected standing finding

Markers 1-4 identify Tighe's intended standing attacks in both directions. The recorded runtime
selector does not cleanly identify the standing mapping class: marker rows begin at `action=0`,
`attack_type=4`, `crouch=0x00FF`, and nearby retained rows transition through `crouch=1` while
`attack_type` remains 4. Facing is `0/2`, rather than a complete clean `2/3` pair.

The corresponding BODY queue is live and resident. For example, F5263 contains the mirrored
idle/body set `0x008E/0x008F/0x0090/0x009E/0x009F/0x0076..0x0079`; F6001 contains its unmirrored
counterpart. This proves the marker and player render path were captured, but it does **not**
authorize a standing-sword geometry change because the exact standing attack selector was not
isolated.

### Corrected crouch finding

The crouch windows conclusively cover both canonical facings:

- F7183: `action=5`, `attack_type=4`, `crouch=1`, facing `3`, phase `6`; live sword/body pieces
  include `0x00C0/0x00C1/0x00C2/0x00C3` with word0 `0x4003`.
- F7896: the same selector and phase with facing `2`; the same four pieces use word0 `0x0003`.

At F7183 the sword pieces occupy X/Y `0x73/0x69`, `0x63/0x69`, `0x6B/0x79`, and
`0x5B/0x79`; at F7896 they occupy `0x38/0x69`, `0x48/0x69`, `0x40/0x79`, and
`0x50/0x79`. This is direct evidence that the native BODY producer emits the crouch attack in
both directions with the expected horizontal-flip distinction. Combined with the earlier exact
queue-to-residency-to-SAT matches, no first mismatch is established in the captured BODY
geometry. The visibly malformed sword therefore remains unresolved at a later visual-composition
or missing-companion boundary; a coordinate/flip patch is not supported.

### Corrected downward-thrust finding

Frame **15617** is the authoritative recorded `DOWN_THRUST` marker. Frames 15617-15707 contain
`action=0`, `attack_type=4`, `crouch=0x00FF`, facing `3`, phase `0x18`, and the ordinary
player BODY codes `0x008E..0x009F` plus `0x0076..0x0079`. Tighe confirmed that the thrust was
successfully triggered after this marker, but it occurred after the retained 90-frame interval.

Consequently:

- downward thrust performed by Tighe: **YES**;
- authoritative marker: **F15617**;
- actual thrust queue/SAT rows retained: **NO**;
- missing thrust-tip source/lane/SAT boundary: **UNRESOLVED**;
- a palette, geometry, or `0x54810` assignment for the thrust: **NOT AUTHORIZED**.

### Corrected palette-shadow finding

All sampled corrected-capture rows, including marker 10 and all sword markers, retain
`sprite_ctrl=0x0060` and `colbank_bits=0x0060`. The shadow did not fall to zero. Despite that
stable source state, unambiguous exact BODY-to-SAT matches for source nibble 3 include transient
line-0 output in the marked palette interval. At F9198, codes `0x0076..0x0079` keep their tile,
X/Y, and Hflip but reach SAT on line 0; the same corrected capture otherwise overwhelmingly
resolves nibble 3 to line 3.

**PROVEN boundary:** the transient line change occurs downstream of the retained `0x0060`
sprite-control/colbank shadow. It is not caused by that shadow being cleared. The correct normal
Stage-1 Rastan/sword decision remains effective bank `0x33` to Genesis line 3; the line-0 frame
is a known output-routing/commit defect, not a new palette assignment.

### Corrected bad-Lizardman finding

Markers 11-15 now tie Tighe's visibly bad club pose to live Stage-1 Lizardmen rather than merely
to a general actor interval. Across those markers:

- actor family is 0;
- actor classes are `0x17` and `0x18`;
- base tile is `0x004B` and attr is `0x46`;
- code `0x004E` appears in `BACK_ENEMY` with word0 `0x4046`;
- at F10007, two code-`0x004E` pieces are queued at X `0xEA/0xB0`, Y `0x69`, resident
  cell 58 / Genesis tile 1256;
- the same-frame SAT contains tile 1256 at screen X `236/176`, screen Y 97, H1/V0,
  source nibble 6, palette line 0.

This closes the prior marker-correlation gap. The bad pose is real and belongs to the recorded
family-0 class-`0x17/0x18` Lizardman stream. The native queue, residency, flip, and SAT output
for the identified `0x004E` club/upper-body piece still match the original descriptor contract,
so the first visual mismatch remains beyond that transform boundary. The corrected evidence does
not support flipping, negating, recoloring, or moving `0x004E`. Stage-1 Lizardman palette bank
`0x36` to line 0 remains the confirmed correct palette decision.

## Earlier Unmarked Capture (Supporting Evidence)

### Capture Environment

- Platform: Genesis NTSC in interactive MAME
- MAME machine: `genesis`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0279.bin`
- SHA-256: `2107c36638ea2994c3ca3f0884f48f3317f52213896747976e7522f4e89f58d0`
- ROM size: 1,591,520 bytes
- Trace directory: `states/traces/build0279_user_controlled_sword_lizardman_20260811_133221/`
- Tighe controlled gameplay: **YES**
- Scripted gameplay input: **NO**
- Headless gameplay: **NO**
- Logger memory writes: **NO**

The first interactive run covered 6,752 external frames and preserved 360 attack frames,
27 observed attack windows, and 600 frames containing Lizardman actor classes `0x17` or
`0x18`. A bounded follow-up ran for 1,167 frames but did not observe an on-screen Lizardman
at its finalizer breakpoint. It adds no contradictory evidence. Both loggers were passive.

### User capture and instrumentation limitation

**USER-OBSERVED FACT:** Tighe performed all six requested attacks, in both directions, and
captured the visibly bad Lizardman club pose. Those gameplay observations are authoritative.

**LOGGER FACT:** every row in `attack_state.csv` has `a5+0x10E8 = 0x0005`. The logger did
not distinguish Tighe's standing, crouching, and downward-thrust actions as the statically
expected values 5, 4, and 8. Facing values `0x0002` (native unmirrored path) and `0x0003`
(native mirrored path) were both recorded, but the trace has no manual event marker assigning
individual segments to the six user-performed cases.

This is an instrumentation/correlation deficiency, not a failure by Tighe to perform the
tests. The captured runtime rows remain valid, but the action-specific conclusions below are
limited where the logger failed to preserve the visible-action identity.

### Verified runtime data

| Data | Genesis-WRAM address |
|---|---:|
| `native_queue_player_front` | `0x00FF6A2A` |
| `native_queue_middle` | `0x00FF6B1A` |
| `native_queue_player_body` | `0x00FF6BDA` |
| `native_queue_back_enemy` | `0x00FF6C7A` |
| native queue counts | `0x00FF68BA..0x00FF68C0` |
| `pc090oj_object_ram` | `0x00FF6F92` |
| compatibility records 44-47 | `0x00FF70F2..0x00FF7111` |
| staged SAT banks | `0x00FF61CC`, `0x00FF644C` |
| resident-code table | `0x00FF6782` |

## Sword Controlled Capture

| Action | Facing | State/sub | BODY pieces | FRONT pieces | `0x54810` aux | SAT result |
|---|---|---|---|---|---|---|
| Standing/action 5 | unmirrored (`0x0002`) | `5`, substates `0x10..0x18` in the captured segment | codes include `0xB0..0xBB`; word0 `0x0003` for unmirrored sword pieces | none | records 44-47 all code zero | clean exact match example at F2936: code `0xB0` -> tile 1280, X 127, Y 97, H0/V0, line 3 |
| Standing/action 5 | mirrored (`0x0003`, also transient `0x0000`) | `5`, substates across `0x00..0x18` | codes include `0xAC..0xC3`; sword pieces carry word0 `0x4003` | none | records 44-47 all code zero | clean exact match example at F767: code `0xC0` -> tile 1024, X 40, Y 97, H1/V0, line 3 |
| Crouching attack | both directions performed by Tighe | logger recorded only action `0x0005`; requested case not separately tagged | captured rows cannot be assigned uniquely | none in all logged attack rows | records 44-47 blank in all logged attack rows | visual case captured; SAT rows not uniquely attributable |
| Downward thrust | both directions performed by Tighe | logger recorded only action `0x0005`; requested case not separately tagged | captured rows cannot be assigned uniquely | none in all logged attack rows | records 44-47 blank in all logged attack rows | visible broken thrust captured; SAT rows not uniquely attributable |

Across captured action-5 rows, the live sword/body range included `0xAC..0xC3` plus
companion body codes. For sword-class BODY rows in `0xA0..0xC3` with word0 `0x4003`,
1,161 source rows were observed; 944 already had a resident tile at the sampling point.
Of those, 726 have an exact same-sample SAT match on Genesis tile, X, Y-8, H/V flip, and
source nibble. The non-matches cluster around residency turnover and the queue/SAT sampling
phase, so this aggregate is not used as a loss rate. The representative exact matches below
are the authoritative geometry evidence.

## Downward-Thrust Tip

- Visible defect reproduced by Tighe: **YES (user-observed and authoritative)**
- Expected/source piece: action-8 arcade codes were statically identified by Andy as
  `0x04DB..0x04E0`, but no action-8 row exists in this capture.
- Native lane presence: **UNKNOWN for the user-identified thrust window because the logger
  did not tag it separately**
- `pc090oj_object_ram` presence: records 44-47 were blank throughout the logged attack
  windows; the logger recorded no row labeled action 8, so it cannot isolate the thrust.
- SAT presence: **UNKNOWN for the user-identified thrust window**
- Exact disappearance/mismatch boundary: **not established by this run**

Cause indicated by capture: the visible failure was captured, but the logger lost the
action-specific identity needed to isolate its queue/SAT rows. The run closes the `0x54810`
hypothesis only for rows conclusively attributable to action 5; it does not close it for the
user-performed downward thrust.

## Sword Geometry

| Action/frame | Arcade/native code | Expected tile | Genesis tile | word0 | source X/Y -> SAT X/Y | flip | Match? |
|---|---:|---:|---:|---:|---|---|---|
| action 5, F767, mirrored | `0x00C0` | resident cell 0 -> 1024 | 1024 | `0x4003` | 40/105 -> 40/97 | H1/V0 | **YES** |
| action 5, F767, mirrored | `0x00C2` | resident cell 8 -> 1056 | 1056 | `0x4003` | 32/121 -> 32/113 | H1/V0 | **YES** |
| action 5, F2936, unmirrored | `0x00B0` | resident cell 64 -> 1280 | 1280 | `0x0003` | 127/105 -> 127/97 | H0/V0 | **YES** |
| action 5, F1947, palette transition | `0x00C2` | resident cell 8 -> 1056 | 1056 | `0x4003` | 160/121 -> 160/113 | H1/V0 | **YES; palette line differs** |

- Standing/action-5 cause indicated: the tested BODY code-to-residency and geometry path is
  capable of exact realization in both native orientations. This capture does not prove a
  wrong tile or transform for the representative standing pieces.
- Crouching cause indicated: **user action captured, but logger did not identify its rows**.
- Down-thrust cause indicated: **user action captured, but logger did not identify its rows**.

## Sword Palette

| Action/frame | source code | source nibble | resolved Genesis palette line |
|---|---:|---:|---:|
| action 5, F1946 | `0x00C2`, `0x00C3` | 3 | 3 |
| action 5, F1947 | `0x00C2`, `0x00C3` | 3 | **0** |
| action 5, F1948 | `0x00C2`, `0x00C3` | 3 | 3 |
| action 5, F2168 | `0x00B8..0x00BB` | 3 | **0** |
| action 5, F2169 (same resident tiles retained in SAT) | prior `0x00B8..0x00BB` | 3 | 3 |

**PROVEN:** source nibble remains 3 for all 1,161 captured sword-class BODY rows. In
720 exact source-to-SAT matches the resolved line is 3; six exact matches resolve to line 0.
The strongest isolated example is F1946 -> F1947 -> F1948: codes `0xC2/0xC3`, Genesis
tiles 1056/1072, X/Y, and H/V remain unchanged while only the resolved line changes
`3 -> 0 -> 3`. This is a rendering-line transition, not a tile-identity transition.

Cause indicated: the visible action-5 palette flash has a concrete commit-time palette-line
boundary. The source nibble is stable; the resolved SAT palette line transiently falls to 0.
This report does not infer which palette-route owner changes that resolution.

## `0x54810` Auxiliary

- Participates in captured melee sword/slash/tip: **NO for action 5**
- Exact proof: all 360 captured action-5 frames have `aux_anim=0`, `aux_gate=0`,
  `weapon=0x00FF`; all 1,440 sampled compatibility records (slots 44-47) have code zero;
  `native_queue_player_front` has zero captured entries.
- Observed semantic role: no active role in captured action 5. Static evidence still
  classifies it as a general player sub-object/weapon/effect family. Action 4 and action 8
  remain untested, so the family must not be globally removed or converted from this result.

## Lizardman Club

### Runtime identity

- On-screen positive-control actor: actor index 8 at F519/F520
- Actor family: `0x00`
- Actor class: `0x17` at F519/F520; class `0x18` also occurs later in the capture
- Facing: `0x00` (mirrored actor path)
- Base tile: `0x004B`
- Actor attr: `0x46`
- Actor-8 position at F519: X `0x013E`, Y `0x00D1`
- Native lane: `BACK_ENEMY`

### Club piece and original table

The family-0 descriptor table is original arcade ROM/data offset `0x0003D09E` and
Genesis relocated runtime-data address `0x0003D29E`. This is a data relocation, not a PC
mapping assumption.

- Class `0x17`: table offset `0x054D`; original descriptor `0x0003D5EB`; Genesis
  relocated descriptor `0x0003D7EB`.
- Class `0x18`: table offset `0x056E`; original descriptor `0x0003D60C`; Genesis
  relocated descriptor `0x0003D80C`.
- In both descriptors, mapping piece index 2 has control `0x01`, code offset `0x03`,
  X offset 0, and Y offset -15 (class 17) or -16 (class 18).
- Base `0x004B + 0x03` gives club/upper-body source and emitted code `0x004E`.

At F519, class-17 piece index 2 is queued as:

```text
word0=0x4046  Y=0x00BA  code=0x004E  X=0x012E
resident_cell=58  Genesis_tile=1256
```

The committed SAT sample at F520 contains the exact corresponding entry:

```text
SAT index=16  Genesis_tile=1256  palette_line=0
screen_X=302  screen_Y=178  H=1  V=0  source_nibble=6
```

The one-sample offset is due to the logger observing the newly built enemy queue after the
currently committed SAT bank. Across the run, 1,435 of 1,520 resident code-`0x004E` queue
rows have an exact next-sample SAT match on tile, X, Y-8, H/V, and nibble.

### Transform conclusion

- Flip mechanism: facing `0x00` selects the mirrored actor branch, which always sets Hflip
  and computes `X = baseX - signed(mapX) - 0x10`.
- Club word0: `0x4046` (Hflip set, Vflip clear, source nibble 6).
- Code-negation/mirrored artwork used: **NO**. Control `0x01` is not type `0x40`, so code
  offset `0x03` is added unchanged.
- Expected arcade orientation: Hflip=1, Vflip=0, code `0x004E`, X `baseX-0x10` for facing 0.
- Build 0279 mismatch: **none proven at semantic mapping, native queue, residency, or SAT
  transform for this club piece**. Build 0279 exactly realizes the original mirrored-table
  contract in the captured frames.

Tighe captured and identified the visibly incorrect club pose. The logger did not include a
manual event marker tying that observation to one exact external frame. Therefore the capture
identifies the relevant Lizardman family and club piece and disproves a simple native
H/V/code-negation error in the correlated rows, but it does not establish the remaining visual
mismatch boundary for the exact user-observed pose. This is a logger-correlation limitation;
it is not a rejection of Tighe's observation. A flip patch is not supported by the recorded
values.

Evidence images in the trace directory:

- `lizard_candidate_tiles.png`
- `lizard_candidate_tiles_index_palette.png`
- `lizard_class17_18_composite_index_palette.png`

## Final Evidence Answers

- Standing swing cause indicated: corrected markers 1-4 preserve the user-labeled standing
  windows and live player rendering in both intended directions, but the exact standing selector
  was not isolated; no BODY transform cause was proven.
- Crouching swing cause indicated: **corrected markers 5-9 conclusively correlate action 5,
  crouch=1, and both canonical facings 3/2**. Codes `0xC0..0xC3` are emitted with the expected
  mirrored/unmirrored distinction; no queue/residency/SAT geometry mismatch is proven.
- Downward-thrust cause indicated: **performed and visibly reproduced by Tighe; authoritative
  marker F15617**. The actual thrust occurred after the logger's 90-frame retention interval, so
  its queue/SAT rows are not present.
- Missing-tip cause indicated: **not established**.
- Sword palette-flash cause indicated: **YES at the output boundary**; corrected marker 10 keeps
  `sprite_ctrl` and `colbank_bits` at `0x0060`, while exact nibble-3 player entries transiently
  resolve to SAT palette line 0. The shadow itself did not clear.
- `0x54810` sword-related: **NO for captured action 5; UNKNOWN for actions 4/8**.
- Lizardman club root cause indicated: the club is family 0, class 17/18, piece index 2,
  code `0x004E`. Corrected markers 11-15 tie the visible bad pose to that live actor stream and
  prove tile 1256 reaches SAT as line 0, H1/V0. Its captured transform is arcade-faithful, so the
  visible orientation defect is not explained by native Hflip/Vflip/code-negation.
- Shared sword/club cause: **NO evidence of a shared transform cause**.

## Evidence Andy Should Use

1. Do not route `0x54810` as the standing sword based on anchoring: it is inactive and blank
   throughout captured action 5.
2. Do not change crouch BODY geometry or flip from this evidence: corrected markers 5-9 prove
   clean mirrored and unmirrored emission for codes `0xC0..0xC3`.
3. Investigate the palette resolution/commit owner downstream of the stable `0x0060` shadow;
   corrected marker 10 includes nibble-3 player entries reaching line 0 at F9198.
4. Do not flip, negate, move, or recolor Lizard code `0x004E`: corrected markers 11-15 prove it
   reaches SAT as line 0, H1/V0 with unchanged code during the user-identified bad pose interval.
5. Tighe performed the downward thrust after the sole `O` marker at F15617. The 90-frame logger
   window expired before action onset due accelerated execution and key spacing; do not infer a
   missing-tip fix from the ordinary BODY rows retained at F15617-F15707.

## Change Control

- Source changes: **NO**
- Spec changes: **NO**
- Tool changes: **NO**
- Production generated-file changes: **NO**
- Build produced: **NO**
- Counter: **279**
