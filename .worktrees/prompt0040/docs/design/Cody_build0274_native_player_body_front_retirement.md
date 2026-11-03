# Build 0274 Native Player BODY + FRONT Retirement

## Baseline and Outcome

- Accepted forward baseline: Build 0273; counter 273.
- Produced candidate: Build 0274; counter 274.
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0274.bin`
- SHA-256: `4ead3b77da5bba008e5a0f18459135d856121f673c6fc772ead7b104876231e1`
- Size: 1,590,924 bytes (`0x18468C`).
- Canonical gate: PASS.
- Classification: EXTENDING KF-074 / OPEN-024. Rediscovery Hazard HIGH.
- Contradiction of a CONFIRMED or STRONG prior: none.

## Semantic Cut

The retained arcade program still decides player action/state, animation frame,
mapping table, piece list, facing, position, visibility, and per-piece attributes.
The cut is immediately before PC090OJ tuple realization:

```text
arcade main-loop player semantic decisions
  -> final PLAYER_FRONT / PLAYER_BODY native queue entries
  -> existing arcade VBlank finalizer
  -> staged SAT and VBlank VDP commit
```

The removed chip tail is the player-only `a5+0x11B2` / `a5+0x0170`
PC090OJ tuple publication, its `0x41F5E` copy, and the Genesis tuple consumer.
No VDP write occurs in the main loop. No player tuple-shaped replacement buffer,
second finalizer, VBlank rerun of `0x540CC`, or full state-machine transcription
was added.

## Main-Loop and VBlank Lifecycle

- The replacement at `arcade_pc 0x05105A` preserves the original
  `move.w #0x00FF,a5@0x12FC`, then calls `native_player_frame_begin`.
- `arcade_pc 0x051060` then calls the retained FRONT producer at
  `arcade_pc 0x059F92`.
- `arcade_pc 0x05151C` later calls the retained BODY producer at
  `arcade_pc 0x0540CC` in the same main-loop frame.
- `native_player_frame_begin` clears only `native_player_front_count` and
  `native_player_body_count` once before both producers.
- `native_sprite_frame_begin` continues to clear VBlank-owned HUD/effect/enemy
  lanes and `pc090oj_sat_frame_ready`, but preserves the completed player lanes.
- The established `pc090oj_native_emit_pass` remains the sole gameplay
  finalizer and concatenates HUD, FRONT_EFFECT, PLAYER_FRONT, MIDDLE,
  PLAYER_BODY, and BACK_ENEMY before VBlank SAT commit.

Final address-map results:

| Role | arcade_pc | runtime_genesis_pc | Mapping |
|---|---:|---:|---|
| player reset insertion | `0x05105A` | `0x05125A` | `patched_site` |
| FRONT call | `0x051060` | `0x051266` | `arcade_copy` |
| BODY call | `0x05151C` | `0x051722` | `arcade_copy` |
| BODY entry | `0x0540CC` | `0x0542CC` | `arcade_copy` |
| FRONT entry | `0x059F92` | `0x05A13A` | `arcade_copy` |

## BODY Native Output

The original BODY state machine and ROM mapping/piece tables remain arcade
code. At each terminal tuple store, the retained register values are adapted to
`native_sprite_emit`: `d1=attr`, `d6=Y`, `d3=code`, `d4=X`, with `d2` preserved
as the arcade loop counter. Each segment explicitly selects
`NATIVE_LANE_PLAYER_BODY`.

The old tuple-zero consumer also copied X/Y into persistent player fields
`a5+0x129A/0x129C`. The native tuple-zero output now publishes those semantic
coordinates directly. An inactive body, an all-blank body, or a blank first
piece clears the anchor, preventing stale state without retaining Block A.
The old anchor-copy prologue at `arcade_pc 0x0547C0` is retired while its
unrelated continuation remains live.

## FRONT Native Output

The retained producer at `arcade_pc 0x059F92` still selects weapon/front codes
from `a5+0x1388` and active fields at `a5+0x140C/0x140E/0x1410`. Its four final
PC090OJ tuple realizations now set registers and append directly to
`NATIVE_LANE_PLAYER_FRONT`. Inactive values branch around emission, so blank
pieces create no queue entry.

## Writer and Consumer Coverage Matrix

| Arcade producer/consumer | Proven disposition in Build 0274 |
|---|---|
| `0x054492` core BODY expander | final stores converted to PLAYER_BODY |
| `0x054576` all-blank BODY path | clears anchor, emits nothing, no tuple clear loop |
| `0x0545BA` inline BODY expander | final stores converted; tuple 0 publishes/clears anchor |
| `0x0546A8` secondary BODY expander | final stores converted to PLAYER_BODY |
| `0x05475A` three-piece auxiliary player segment | final stores converted to PLAYER_BODY |
| `0x059F92..0x05A080` FRONT family | all four active outputs converted; all blank outputs no-emit |
| `0x051E00` auxiliary-record anchor input | reads persistent `a5+0x129A/0x129C`, not Block A |
| `0x0547C0` tuple-zero anchor consumer | complete player-tuple prologue retired |
| gameplay `0x041F5E` translation | frame reset only; no player tuple consumer/copy |
| `native_stage_player_blocks_41f5e` | removed |
| `pc090oj_workram_block_sprites*` player family | removed |
| final player consumer | native queue finalizer only |

Binary reference scans found no live literals for `0x10D1D2`, `0x10D1F2`,
`0xFF11B2`, `0xFF0170`, or `0x10D212`. The two remaining `0x10D1B2`
literals are at the dead fallback bodies described below.

## Explicit 0x5288C Disposition

`FUN_0005288c` is a fallback tuple-zero producer (word0 1/5, code 0/0x6E1,
player position, gates including `a5+0x1296` and `a5+0x1308` bit 3). Static
call enumeration gives one parent path: `0x52792 -> 0x5288C` inside
`FUN_00052732`. The current main flow at `0x5108C` branches directly to
`0x51096`, bypassing the dead `0x51090 -> 0x52732` call. No other caller exists
in the current Ghidra inventory. Therefore `0x5288C` is dead/superseded and was
not converted. The related `0x52A6C` Block-A fallback is under the same dead
`0x52732` path. Their copied bytes remain as unreachable provenance; they are
not a live player writer.

Final mappings are `arcade_pc 0x05288C -> runtime_genesis_pc 0x052A8C` and
`arcade_pc 0x052A6C -> runtime_genesis_pc 0x052C6C`, both `arcade_copy`.

## Shift/Reflow

The spec contains 58 `shift_replacements`. Actual per-site deltas are grouped
below; zero-delta sites are listed to make the replacement coverage explicit.

| Group | arcade_pc sites | Deltas |
|---|---|---|
| lifecycle/anchor input | `0x5105A`, `0x51E00` | `+6`, `-6` |
| inactive BODY clear | `0x542E8` | `-48` |
| BODY core | `0x54492`, `0x544D0`, `0x544F2`, `0x54504`, `0x54508`, `0x5452C` | `0,0,0,0,0,+6` |
| BODY all-blank | `0x54576` | `-26` |
| BODY inline | `0x545BA`, `0x545CC`, `0x545EE`, `0x54600`, `0x54628`, `0x5464A` | `0,+6,0,0,0,+6` |
| BODY secondary | `0x546A8`, `0x546E6`, `0x54708`, `0x5471A`, `0x5471E`, `0x54742` | `0,0,0,0,0,+6` |
| BODY auxiliary | `0x5475A`, `0x5476C`, `0x5476E`, `0x54774`, `0x54784`, `0x54788`, `0x54790` | `0,+2,-6,-2,+2,+4,-16` |
| retired anchor copy | `0x547C0` | `-22` |
| FRONT weapon | `0x59F9A`, `0x59FA0`, `0x59FA4`, `0x59FB0`, `0x59FBC`, `0x59FC8`, `0x59FD2`, `0x59FD4`, `0x59FD8`, `0x59FDE` | `0,0,0,0,0,0,+2,0,+6,-2` |
| FRONT overlays 1-3 | `0x59FFC..0x5A080` (18 sites) | each group `0,0,0,0,+6,-2` |

Net copied-program shift delta: `-70` bytes (`-0x46`). The native blank-anchor
helper adds `0x10` Genesis helper bytes, making canonical coverage `0x18468C`.
The shift patcher repaired 7,209 branches and 609 absolute-long references.
Postpatch disassembly confirmed all locally widened branches land on instruction
boundaries, including BODY blank continuations and FRONT type selection.

Representative output mappings:

| arcade_pc | runtime_genesis_pc | Purpose |
|---:|---:|---|
| `0x0542E8` | `0x0544E8` | inactive BODY clear |
| `0x054492` | `0x054662` | BODY lane select |
| `0x054576` | `0x05474C` | all-blank clear |
| `0x0545BA` | `0x054776` | inline BODY lane select |
| `0x05464A` | `0x05480C` | tuple-zero native output |
| `0x054742` | `0x05490A` | secondary native output |
| `0x05475A` | `0x054928` | auxiliary BODY lane select |
| `0x05476C` | `0x05493A` | auxiliary blank decision |
| `0x054790` | `0x05495E` | auxiliary blank continuation |
| `0x0547C0` | `0x05497E` | retired anchor-copy entry |
| `0x059F9A` | `0x05A142` | FRONT lane select |
| `0x059FD2` | `0x05A17A` | FRONT type branch |
| `0x05A080` | `0x05A23C` | final FRONT blank path |

## Legacy Retirement Boundary

Removed:

- player-only `pc090oj_workram_block_sprites*` and family apply logic;
- `native_stage_player_blocks_41f5e`;
- gameplay `0x41F5E` player tuple staging;
- live player writes/reads for `a5+0x11B2`, `a5+0x0170`, and related BODY
  tuple ranges;
- the old tuple-zero anchor consumer.

Intentionally remaining:

- unreachable `0x5288C`/`0x52A6C` copied arcade fallback bodies as provenance;
- frontend/non-gameplay `pc090oj_object_ram` compatibility and legacy scanner;
- native PC090OJ-named tile residency, DMA, queue, and SAT output support;
- the surrounding arcade work-RAM layout and unrelated `0x41F5E` flow.

## Validation

### Original Arcade

Existing repository-owned debugger evidence was reused from
`states/traces/player_builder_provenance_20260809_000004/`. It is original
arcade MAME `rastan` evidence, not Genesis or PAL `megadriv`. The 29,591-byte
`debug.log` records 295 BODY events and 318 VBlank-copy events; BODY returns via
`0x51522` and was observed once per VBlank-relative frame. A writepoint on the
FRONT source fired 714 times and showed inactive blank behavior in the captured
attract state. Static arcade decode supplies the active weapon code selection;
active throw visuals remain a user-verification item.

### Genesis NTSC

The Makefile-owned Genesis NTSC trace is:

`states/traces/rastan_direct_video_test_build_0274_mame_30s_20260809_154336/`

It sampled 1,798 external frames, completed normally, reported 47,265 live VDP
port writes through the final frame, and reported no unique unmapped memory
addresses. The 30-second automated window covered frontend smoke behavior, not
interactive gameplay BODY/FRONT animation acceptance.

## Tool Reuse

- Existing project tools reused: Ghidra exports and
  `docs/design/Andy_workram_block_sprites_family_provenance.md`; established
  MAME debugger evidence under `states/traces/player_builder_provenance_20260809_000004/`;
  `shift_replacements`, `shift_table_patcher.py`,
  `postpatch_startup_rom.py`, `verify_canonical_rom.py`, generated
  `address_map.json`, Makefile canonical gate, and mandatory Genesis NTSC trace.
- New tooling created: none.
- Why new tooling was necessary: not applicable. The existing shift pipeline was
  extended in place to handle complete variable-length guard spans, physical
  shifted copy bounds, and zero-byte retirement boundaries correctly; no parallel
  patcher, harness, or temporary validation architecture was introduced.

## User Must Verify

Test idle; walking left/right; facing both directions; jump/fall; sword attacks;
weapon/throw FRONT behavior; taking damage; player death; any state associated
with the `0x5288C` fallback semantic object; BODY/FRONT layering against enemies
and effects; HUD; ROUND/READY to gameplay; no missing/flickering player pieces;
no duplicate player; and no new palette errors or major speed regression.

## Impact and Stop Status

- OPEN-024: advanced, not closed.
- New issues opened: none.
- Issues closed: none.
- KNOWN_FINDINGS impact: extends KF-074; no separate index entry added.
- STOP triggered: no.
- Architecture compliance: confirmed.

