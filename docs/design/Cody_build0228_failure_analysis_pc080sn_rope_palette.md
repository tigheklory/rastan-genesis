# Cody - Build 0228 Failure Analysis: PC080SN Producer, Rope Transition, and Palette Regression

**Date:** 2026-07-21  
**Type:** Evidence / analysis only  
**Accepted baseline:** Build 0227, `dist/rastan-direct/rastan_direct_video_test_build_0227.bin`, SHA256 `5ab997f6186bc6cd7f6342ed4149cd6d9baa764cf57ff7567dca8474ed5f6ec0`  
**Rejected comparison build:** Build 0228, `dist/rastan-direct/rastan_direct_video_test_build_0228.bin`, SHA256 `8a6f87d4db25a3253be54baaf2d2ec3b57953ca2119b7a27b104577ddc1244f5`, consumed/rejected  
**Scope:** No ROM build. No source/spec/Makefile fix. No deletion of numbered builds. Build 0228 source/generated state is preserved as rejected comparison evidence only.

## Phase 0

Classification: **EXTENDING**. This analysis extends OPEN-017 / KF-073 Stage 1 cave/rope/collision work and KF-066 lizard palette configuration context. Relevant priors loaded: KF-066 (HUD-sprite suppression option and PC090OJ bank `0x36` line-0 carrier), KF-067 (collision row/ground-band producer hazard), KF-072 (Build 0227 accepted N2 plane baseline), KF-073 (cave/rope/collision unresolved), plus the project address-mapping discipline. OPEN-017 is primary; OPEN-001 context only; OPEN-015 not touched. No contradiction of a CONFIRMED/STRONG finding was found; Build 0228 contradicts acceptance expectations and is rejected, not a new baseline.

Architecture compliance: **CONFIRMED**. The arcade code remains the program. This report treats Genesis code as helper/VDP-service state and does not propose scaffolding, hardcoded collision values, coordinate workarounds, or state forcing.

## Evidence Inspected

- `RULES.md`, `ARCHITECTURE.md`, `AGENTS_LOG.md` latest relevant entries.
- `CURRENT_STATE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md` excerpts for Builds 0210, 0218, 0227, and rope/cave state.
- Source/runtime consumers:
  - `tools/translation/precompute_pc080sn_tile_lut.py`
  - `apps/rastan-direct/src/tilemap_hooks.s`
  - `apps/rastan-direct/src/scene_load.s`
  - `apps/rastan-direct/src/palette_hooks.s`
  - `apps/rastan-direct/src/vdp_comm.s`
  - `apps/rastan-direct/src/pc090oj_hooks.s`
  - `apps/rastan-direct/Makefile`
  - `apps/rastan-direct/out/pc090oj_config.inc`
  - `build/rastan-direct/address_map.json`
- Prior rope/collision evidence:
  - `docs/design/Cody_build0228_rope_collision_address_mapping.md`
  - `states/traces/build0228_rope_death_cody_proof_20260721_135322/cody_rope_death_proof_summary.md`
- Raw descriptor bytes from `build/regions/maincpu.bin` at arcade ROM/data `0x03951C`.
- Focused Build 0228 runtime trace:
  - `states/traces/build0228_runtime_scene4_rope_transition_20260722_090545/native_debug_trace.log`
  - `states/traces/build0228_runtime_scene4_rope_transition_20260722_090545/reduced_events.log`
  - `states/traces/build0228_runtime_scene4_rope_transition_20260722_090545/runtime_summary.txt`

The focused Build 0228 runtime trace was added after the initial static-only report because the assigned task required proving whether scene 4 was requested during the user's rope-transition test.

## Build 0227 vs Build 0228 Comparison

Build 0228 changed PC080SN production residency and generated data, but it was also built with a different PC090OJ/HUD configuration from the accepted gameplay baseline.

| Area | Build 0228 change capable of effect | Runtime consumer | Assessment |
|---|---|---|---|
| PC080SN scene selection | Added `SCENE_GAMEPLAY_AFTER_ROPE = 4`, attr `0x000A -> 4`, source range ceiling to `0x00011200` | `precompute_pc080sn_tile_lut.py` | Real generated-data change; post-rope sources become an independent manifest. |
| PC080SN runtime tileset selection | Added source-pointer range `[0x00010B1C,0x00011400)` -> tileset `4` | `genesistan_hook_itempage_strip_blit` in `tilemap_hooks.s` | Real runtime behavior change; selected from relocated strip source only. |
| PC080SN VRAM allocation | Added `pc080sn_scene_preload_gameplay_after_rope.bin` | `load_scene_tiles(4)` in `scene_load.s` | Real VRAM/cache residency change. |
| CRAM / lizard palette | `apps/rastan-direct/out/pc090oj_config.inc` says `RASTAN_GAMEPLAY_HUD_SPRITES=1` | `palette_hooks.s`, `vdp_comm.s`, `pc090oj_hooks.s` | Exact cause of lizard palette regression; the bank-`0x36` carrier is compiled out. |
| PC090OJ sprite palette routing | Route lookup for general bank `0x36` is guarded by `RASTAN_GAMEPLAY_HUD_SPRITES == 0` | `.Lnative_palsel` | With config `1`, lizard effective bank `0x36` falls back to `(bank >> 4) & 3 = line 3`, not line 0. |
| Scroll/camera/collision/death code | No direct source fix in Build 0228 | Native arcade code + Genesis collision helper side-channel | Focused runtime shows visual state remains scene/tileset 1 while invisible rope interaction and lava death occur; Build 0228 does not repair the proven source-list/collision divergence. |

Tile residency counts from the current generated model:

| Scene | Tile count | Budget `1164` |
|---|---:|---:|
| Title | `845` | PASS |
| Gameplay outdoor | `962` | PASS |
| End-Round | `1067` | PASS |
| Gameplay-Cave | `568` | PASS |
| Gameplay-After-Rope | `955` | PASS |

The after-rope scene fits independently. The rejected behavior is not explained by a scene-4 overbudget condition.

## Descriptor Structure and Stride

Resolved result: the live Stage 1 descriptor list at arcade ROM/data `0x03951C` is consumed as **6-byte descriptors**:

```text
{ attr16, src32 }
```

This matches the current generator constants:

```text
RUNTIME_GAMEPLAY_DESC_TABLE = 0x3951C
RUNTIME_GAMEPLAY_DESC_STRIDE = 6
RUNTIME_GAMEPLAY_DESC_ATTR_SCENES = {0x0002, 0x0003, 0x000A}
```

Raw table evidence:

```text
entry 000 @ 0x03951C: attr=0002 src=00D11C
entry 001 @ 0x039522: attr=0002 src=00D91C
entry 056 @ 0x03966C: attr=0003 src=00F91C
entry 057 @ 0x039672: attr=0003 src=01011C
entry 112 @ 0x0397BC: attr=000A src=01091C
entry 113 @ 0x0397C2: attr=000A src=01111C
```

Descriptor runs:

```text
entries 0..55:    attr 0x0002, outdoor sources
entries 56..111:  attr 0x0003, cave/rope sources 0x00F91C / 0x01011C
entries 112..127: attr 0x000A, post-rope sources 0x01091C / 0x01111C
```

The apparent 12-byte pattern is two adjacent 6-byte descriptors viewed together. It may reflect a paired producer grouping, but it is not the descriptor stride used by the live descriptor rebuild path. The original code at arcade `0x055904` rebuilds from the descriptor source list into attr/pointer tables, and the Genesis hook mirrors that model with 6-byte descriptor dereferences.

## Arcade Rope-Transition Sequence Known So Far

The authoritative original arcade progression around this producer is:

| Stage | Arcade address | State / action | Evidence status |
|---|---:|---|---|
| Source-list advance | `arcade_pc 0x0558CE` | `addq.l #4,(%a0)` advances 16 source-list longwords under `0x0010D000` | Statically proven and JSON mapped to `runtime_genesis_pc 0x055ACE`. |
| Descriptor rebuild | `arcade_pc 0x055904` | Reads source-list descriptors and rebuilds attr/source pointer tables (`0x10D080`, `0x10D040`) | Statically proven; Genesis patched site jumps to descriptor rebuild helper. |
| BG/collision producer | `arcade_pc 0x055968..0x0559EC` | Uses rebuilt tables to write collision side-channel and visible tile data | Runtime arcade rope-band samples captured at `arcade_pc 0x0559EC`. |
| Rope-band source blocks | `arcade_rom/data 0x00002648`, `0x00001C14` | Rows 37-39 write `0x0008`; row 40 writes `0x0006` | Original arcade runtime evidence. |
| Genesis lethal divergent block | `runtime_data/genesis_rom_offset 0x00003A88` | Genesis helper writes `0x0107` to collision cell `Genesis-WRAM 0x00FF30DA` | Build 0227 rope-death proof. |
| Native death chain | `runtime_genesis_pc 0x053D70/0x053DD0 -> 0x0550C4` | Native reads `0x0107`, masks to code `0x07`, later writes player mode 8 | Proven in prior rope-death trace. |

Visual/collision/scroll/object coherence is not proven at the rope transition. Existing evidence proves that collision/source selection can diverge before the native death chain, but it does not prove that an attr-`0x000A` strip source is the same event as the legitimate arcade transition beyond the rope.

## Focused Build 0228 Runtime Evidence

User correction, now reflected as the observed runtime target: the rope is **not visually rendered** in Build 0228. Rastan can grab/attach to an invisible rope from inside the cave/top-rope area. Climbing input triggers the climbing animation, but the player does not move up/down. Near the invisible rope, the level can reset to the beginning without death. Jumping off to the right/top still produces instant lava death.

The focused trace captured the user's sequence: reset-to-beginning behavior first, then invisible-rope attach at the top, climb-animation attempts without positional movement, jump/fall off to the right, then lava death.

Event counts:

| Event | Count |
|---|---:|
| `LOAD_SCENE_CALL_FROM_STRIP` | `1` |
| `LOAD_SCENE_ENTRY` | `1` |
| `LOAD_SCENE_COMPLETE_PRESTORE` | `1` |
| `TILESET_BYTE_WRITE` | `2` |
| `SCENE_BYTE_WRITE` | `2` |
| `STRIP_BLIT_ENTRY` | `96` |
| `COLL_WRITE_HELPER` | `28288` |
| `COLL_READ_ROPE` | `63088` |
| `MODE_WRITE` | `3727` |

Measured scene/tile residency:

| Question | Runtime answer |
|---|---|
| Was scene 4 requested? | **NO**. No `SCENE4_SELECTED_IN_STRIP` or after-rope tall-fill event appears in `reduced_events.log`. |
| What scene was requested? | Only `load_scene_tiles(1)` from strip source `runtime_data 0x0000D31C`, attr `0x0002`, at `runtime_genesis_pc 0x071D42 -> 0x072EBA`. |
| Did `load_scene_tiles(4)` complete? | **NO**. The only completed load is `loaded=1` at `runtime_genesis_pc 0x072F42`; current scene/tileset then become `1/1`. |
| Were later strips translated using tileset 4? | **NO**. Observed strip entries remain `curScene=01 curTileset=01`. |
| What visible source range was active? | Outdoor/gameplay attr-`0x0002` sources such as `runtime_data 0x0000F31C` and `0x0000E31C`, not cave/rope or after-rope sources. |

Representative events:

```text
EVENT LOAD_SCENE_CALL_FROM_STRIP cyc=51159810 pc=071D42 req=00000001 src=0000D31C attr=0002 curScene=00 curTileset=00
EVENT LOAD_SCENE_ENTRY cyc=51159828 pc=072EBA req=1 curScene=00 curTileset=00 src=0000D31C attr=0002
EVENT LOAD_SCENE_COMPLETE_PRESTORE cyc=51898966 pc=072F42 loaded=00000001 curSceneBefore=00 curTilesetBefore=00 src=0000D31C attr=0002
EVENT TILESET_BYTE_WRITE cyc=51898966 pc=072F46 data=00000001
EVENT SCENE_BYTE_WRITE cyc=51899020 pc=072F5C data=00000001
EVENT STRIP_BLIT_ENTRY cyc=315946080 pc=071CF8 src=0000F31C attr=0002 curScene=01 curTileset=01 mode=0007 worldX=0021 worldY=0121
```

Measured player/control events:

| Runtime event | Evidence | Interpretation |
|---|---|---|
| Reset-to-beginning without death | `MODE_WRITE pc=05226C data=0007` at `worldX=0183/worldY=0120`, then again at `worldX=0021/worldY=0121`; subsequent strips reload beginning-ish outdoor source `0x0000F31C` while scene/tileset stay `1/1`. | Observable mode-7 reset/fall/out-of-bounds path; exact semantic label remains native-code interpretation. |
| Invisible rope attach / climb animation | `MODE_WRITE pc=05205A data=0004 post=0003` at `worldX=0114/worldY=0148`, `flags10CE=0020`, `ptr111C=00FF2F58`. User observed climbing animation while up/down movement did not occur. | Rope/object interaction state is active even though rope graphics are absent. |
| Rope exit / jump-fall | `MODE_WRITE pc=052474 data=0002 post=0004` at the same `worldX=0114/worldY=0148`. | Player leaves mode 4 into jump/fall mode 2. |
| Lava death | Repeated `MODE_WRITE pc=0550C4 data=0008` starting at `cyc=527351344`, `post=0002`, `worldX=0114/worldY=0148`. | Native death mode still fires after leaving the invisible rope. |

Build 0228 top/right lava death still follows the previously proven bad collision-code path:

```text
EVENT COLL_READ_ROPE cyc=527164934 pc=053D70 addr=00FF30DA mem=0107 masked=07 mode=0002 worldX=0114 worldY=0148 ptr111C=00FF2DD8 src=0000E31C attr=0002
EVENT COLL_READ_ROPE cyc=527165258 pc=053DD0 addr=00FF30DA mem=0107 masked=07 mode=0002 worldX=0114 worldY=0148
EVENT MODE_WRITE cyc=527351344 pc=0550C4 addr=00FF10E8 data=00000008 post=0002 worldX=0114 worldY=0148
```

So the measured Build 0228 coherence state is:

| Subsystem | Build 0228 measured state |
|---|---|
| Visual PC080SN state | Rope absent; scene/tileset remain `1/1`; strips use attr `0x0002` outdoor sources. |
| Rope/object interaction state | Invisible rope is grabbable/attachable; native mode 4 is reached. |
| Climbing behavior | Climb animation occurs, but user-observed up/down position movement does not occur; trace shows the attach window remains around `worldX=0x0114`, `worldY=0x0148`. |
| Collision/death state | Top/right still reads `0x0107`, masks to code `0x07`, then writes player mode 8. |
| Progression/reset state | Mode 7 at `runtime_genesis_pc 0x05226C` correlates with reset-to-beginning behavior without death. |

## Precise Build 0228 Divergence Point

Build 0228 contains a static after-rope residency selector from the relocated strip source pointer:

```asm
move.l  (PC080SN_ITEMPAGE_STRIP_PTR_SLOT), %d0
cmpi.l  #GAMEPLAY_STRIP_SRC_LO, %d0
cmpi.l  #GAMEPLAY_STRIP_SRC_HI, %d0
cmpi.l  #GAMEPLAY_STRIP_SRC_CAVE_LO, %d0
cmpi.l  #GAMEPLAY_STRIP_SRC_AFTER_ROPE_LO, %d0
moveq   #SCENE_GAMEPLAY_AFTER_ROPE_TILESET_ID, %d1
bsr     load_scene_tiles
```

The effective ranges are:

```text
[0x0000D31C, 0x0000FB1C) -> outdoor gameplay tileset 1
[0x0000FB1C, 0x00010B1C) -> cave/rope tileset 3
[0x00010B1C, 0x00011400) -> after-rope tileset 4
```

However, in the measured Build 0228 reproduction, this selector never reached the scene-4 range. The precise runtime divergence is therefore not "scene 4 selected too early." It is:

```text
visual strip/source state stays in outdoor gameplay scene 1
while native rope interaction state reaches mode 4
and collision/death state still sees lethal 0x0107
```

That is a visual/object/collision progression mismatch. The raw source-range scene-4 switch remains a weak implementation boundary, but the focused runtime trace proves the user's observed invisible-rope failure occurs before any scene-4 load.

The key uncorrected upstream issue remains from Build 0227:

```text
Genesis source path:
Genesis-WRAM 0x00FF1024 = 0x0002A288
-> descriptor at genesis_rom_offset 0x0002A488
-> word 0x0005 / raw block pointer 0x3888
-> rebuilt pointer runtime_data 0x00003A88
-> collision value 0x0107

Original arcade rope samples:
slot 9/10 select arcade_rom/data 0x00002648 / 0x00001C14
-> collision values 0x0008 / 0x0006
```

Build 0228 does not fix that source-list/descriptor-selection divergence. In this focused run, it also does not load scene 4 at all, so the missing rope graphics cannot be blamed on the after-rope preload contents; the visible strip/source progression never reaches the cave/rope visual state while the native rope interaction does.

## Lizard Palette Regression

Exact cause: Build 0228 was generated with `RASTAN_GAMEPLAY_HUD_SPRITES=1`:

```asm
/* GENERATED from PC090OJ_MIRROR_RECORDS=256 RASTAN_GAMEPLAY_HUD_SPRITES=1 ... */
.equ RASTAN_GAMEPLAY_HUD_SPRITES, 1
```

KF-066’s accepted lizard palette path requires gameplay HUD sprite suppression (`RASTAN_GAMEPLAY_HUD_SPRITES=0`). With `0`, the following code is compiled in:

- `palette_route_table` row `(scene 1, PC090OJ, bank 0x36 -> Genesis line 0, CARRIER)`.
- Palette hook bank-`0x36` cache capture.
- VBlank `vdp_reassert_bank36_line0` carrier restore.
- `.Lnative_palsel` route-table lookup for general effective banks.
- Gameplay HUD records `0..45` suppression, freeing line 0.

With Build 0228 config `1`, those blocks are compiled out. The lizard effective bank `0x36` therefore reaches the fallback in `.Lnative_palsel`:

```asm
lsr.w #4,%d0
andi.w #0x0003,%d0
```

`0x36 >> 4 = 0x03`, so lizards select Genesis CRAM line 3 instead of the KF-066 line-0 bank-`0x36` carrier. This directly explains the initial outdoor lizard palette regression. It is not caused by PC080SN scene 4 itself.

## Does Scene 4 Represent a Real Producer Boundary?

**Static residency boundary:** YES. Attr `0x000A` descriptors and sources `arcade_rom/data 0x01091C/0x01111C` are real entries in the same descriptor list, and the independent after-rope working set fits within the 1,164-tile cache budget.

**Complete runtime transition boundary:** NO, not as implemented in Build 0228. The focused runtime trace shows scene 4 is not requested during the reproduced invisible-rope/death sequence. Existing rope evidence still shows the real transition depends on source-list slot progression, rebuilt descriptor tables, collision side-channel values, scroll/camera state, player mode/position, and object progression. Those are not advancing coherently in the measured Build 0228 run.

## Architecture Verdict

**Verdict: B. The existing scene loader needs a generated descriptor-driven correction.**

Reasoning:

- Not A: Build 0228 is not merely a small wiring mistake inside an otherwise sufficient source-range switch. The rejected runtime behavior shows the opposite coherence failure: visual strip/source state stays in outdoor scene 1 while rope/object interaction and lethal collision state progress.
- Not C: The residency-scene architecture is not proven too coarse. The after-rope working set is `955/1164`, so the tile budget can hold it independently.
- B fits the evidence: the manifests and loader can remain useful, but runtime selection must be generated from the arcade descriptor/source-list lifecycle and gated at a coherent producer/progression boundary. Build 0228 proves that a visual source-range selector alone does not keep visual, rope interaction, and collision/death state coherent.

## Narrow Build 0229 Scope

Build 0229 should not use Build 0228 as an accepted source baseline. The smallest safe implementation scope is:

1. Preserve numbered Build 0228 for comparison, but restore the accepted gameplay build configuration: `RASTAN_GAMEPLAY_HUD_SPRITES=0` for the next candidate.
2. Do not re-merge after-rope into cave; keep scene-4 manifest generation as a candidate data product only if the selection authority is corrected.
3. Replace the raw source-address runtime switch with a generated descriptor/source-list driven selection model, and ensure the cave/rope visual scene is activated when the native rope/object state becomes reachable.
4. Reconcile the rope-window source-list divergence first: Genesis slot 9 selecting `0x00003A88` versus original arcade rope slots selecting `0x00002648/0x00001C14`.
5. Validate visual/collision/scroll/object coherence at the rope boundary before accepting any after-rope graphics improvement.
6. Do not patch collision values, hardcode rope coordinates, force player state, or compensate lizard palette independently; the palette issue is a build-config regression.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017 primary; OPEN-001 context.
- New issues opened: none.
- Issues closed: none.
- Intentionally deferred: OPEN-015, PC090OJ enemy/damage/sprite palette beyond the Build 0228 config regression, audio, broad level playthrough, map atlas.

## KNOWN_FINDINGS Impact

**Option A - No new finding to index.** This is a rejected-build failure analysis and correction of the 12-byte-vs-6-byte interpretation for the current task. KF-066, KF-072, and KF-073 remain applicable. A durable KF update should wait for Build 0229's proven descriptor-driven correction or a confirmed replacement of the scene-selection architecture.

## STOP

STOP triggered: **NO** for this analysis task. No ROM was built and no implementation was attempted.
