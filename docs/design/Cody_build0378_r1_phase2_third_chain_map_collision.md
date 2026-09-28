# Cody — Build 0378 R1 Phase-2 third-chain map/collision investigation

**Status:** Build 0378 was produced and is permanently consumed. It corrected the general native
collision publisher so gameplay collision cells use the same live/ring-unwrapped descriptor
mapping as Plane-A staging. The eight previously differing collision cells now match, but Tighe's
BlastEm test and the post-build route both show that forward traversal still fails. The single
reproduced ceiling cell remains valid arcade terrain and must not be altered.

## A. Baseline and accepted behavior

The production baseline is Build 0377 (counter 377). Tighe accepted its Round-1 boss-room MODE
crash correction and preservation of the Build-0376 second-rope `C0ABE0` correction. Later-round
MODE cycling remains **FAIL / DEFERRED** and was not investigated here.

The existing focused scripts under `states/traces/build0378_third_chain_diagnostic/` were reused.
The production change is confined to `apps/rastan-direct/src/tilemap_hooks.s`; generated coverage
expectations were advanced with the helper growth by the normal pipeline.

## B. Exact reproduced state

The established natural-control route reaches this stable state:

| Field | Value |
|---|---:|
| stage `A5+0x0118` | `0x01` |
| progression `A5+0x013E` | `0x0011` |
| selector `A5+0x10A8` | `0x0000` |
| strip `A5+0x10CA` | `0x0001` |
| group `A5+0x10CC` | `0x0001` |
| player X/Y | `0x0121 / 0x003E` |
| player state | `0x0004` (retained climbing state) |
| horizontal/vertical movement request | `0x0000 / 0x0001` during the rejected upward step |
| foreground scroll X/Y | `0x015F / 0x0026` |
| native scene id | `0x01` |
| boundary record / variant / package | `0x0011 / 0x0000 / 0x0005` |

The player remains at this position when the test continues to request upward movement into the
ceiling. This is a reproducible movement rejection, but the source comparison below proves that
the rejection itself is arcade-correct.

## C. Exact player probe and movement decision

The retained probe forms:

```text
D1 = player X                         = 0x0121
D2 = player Y - A5+0x1130 - D6       = 0x003E - 0x0018 - 1 = 0x0025
```

`collision_map_lookup_53a2e` maps that point, with scroll `0x015F/0x0026`, to ring row 63,
column 58, address `0x00FF3DF4`. The word is `0x0001` (low-seven-bit property 1).

At original `0x053A90` / Build-0377 runtime `0x053BAC`, the head-probe family classifies property
1 as solid. Original `0x05387E` / runtime `0x05399A` then tests the climbable result bit; bit 5 is
clear, so original `0x053884` / runtime `0x0539A0` reduces the requested one-pixel upward movement
to zero and retries. This establishes `PLAYER_HEAD_COLLISION` as the first rejecting decision,
without establishing that the decision is erroneous.

Representative live probes at this position are:

| Probe | Coordinate | Ring cell/address | Live word/property |
|---|---|---|---:|
| head center | `0x0121,0x0025` | row 63, col 58 / `0xFF3DF4` | `0x0001 / 1` |
| feet center | `0x0121,0x0057` | row 6, col 58 / `0xFF2174` | `0x0002 / 2` |
| feet left | `0x011B,0x0057` | row 6, col 57 / `0xFF2172` | `0x0000 / 0` |
| feet right | `0x0127,0x0057` | row 6, col 59 / `0xFF2176` | `0x0000 / 0` |

The solid center head result short-circuits the optional head-side probes for this upward step.

## D. Special-solid and chain ownership

`A5+0x0242` remains `0x0000` throughout the reproduced stop. No special-solid rectangle is
active, so `SPECIAL_SOLID` is excluded.

The climb/contact contract here is the retained collision grid: property 2 supplies the
climbable/contact bit and saved collision pointer. The player reaches state 4 normally and keeps
requesting movement. No PC090OJ rope actor or special rope collision owns the rejecting cell.
The state machine is therefore not the cause of the upward rejection.

## E. Offending-cell provenance and original arcade source

The exact retained source tuple for ring row 63, column 58 is:

| Term | Value |
|---|---:|
| column/row-group descriptor index | 15 |
| progression | `0x0011` |
| current strip / group | `1 / 1` |
| target cell within 4x4 record | row 3, column 2 |
| live row-group source pointer | `0x0376A0` |
| ring-unwrapped descriptor delta | `-3` entries |
| original arcade descriptor address | `0x037694` |
| Genesis ROM descriptor address | `0x037894` (`+0x200` ROM rebase) |
| descriptor word1 / collision-record pointer | `0x3A08` |
| control word at original `0x3A28` | `0x00FF` (uniform-record sentinel) |
| selected record offset | `0x22` (uniform alternate) |
| original arcade collision source | `0x003A2A` |
| Genesis ROM collision source | `0x003C2A` |
| source word | `0x0001` |
| Genesis destination | `0x00FF3DF4` |
| Genesis live word | `0x0001` |

Because this record takes the sentinel/uniform path, the previously stated H13 ordinary-cell
base ambiguity is immaterial to this target: both the original instruction path and Genesis
select record offset `0x22`. The original arcade source word is conclusively `0x0001`.

The source pointer is also coherent with scene ownership. `0x0376A0` is the live front pointer;
physical column 58 is behind the wrapped front, so delta `-3` resolves the resident prior block at
`0x037694` (scene page `0x10`, entry 14). Active record `0x11`, package 5, and this resident prior
block are mutually consistent. There is no previous/next-record, stale-package, early-switch, or
wrong-scene evidence at the target.

## F. Arcade versus Genesis and local displacement search

| Probe | Original arcade source property | Genesis live property | Same? |
|---|---:|---:|---|
| head center | `0x0001 / 1` | `0x0001 / 1` | YES |
| feet center | `0x0002 / 2` | `0x0002 / 2` | YES |
| feet left | `0x0000 / 0` | `0x0000 / 0` | YES |
| feet right | `0x0000 / 0` | `0x0000 / 0` | YES |

The requested `row -4..+4`, `column -4..+4` source search found no displacement explaining the
target: the exact source and live target already match. Rows 60..63 across columns 54..62 are the
same solid uniform record where applicable. Row 59/column 58 is empty, and wrapped row 0/column
58 is property 2, but neither is the selected target. The observed source displacement is
**rows 0, columns 0**; the nearest different/climbable neighbor is wrapped row `+1`, not a value
mis-selected into the target.

The visible ceiling and collision cell are consistent, not split: descriptor `0x037694` points
to record `0x3A08`, whose visible-cell portion supplies the masonry while its uniform collision
portion supplies property 1. Thus the reproduced screenshot classification is “visible solid and
collision solid.” There is no visual/collision source mismatch at this cell.

## G. First divergence result

There is no arcade-versus-Genesis divergence in the traced head cell:

```text
arcade descriptor 0x037694 -> record 0x3A08 -> source 0x003A2A -> 0x0001
Genesis descriptor 0x037894 -> record 0x3A08 -> source 0x003C2A -> 0x0001
                                                   live 0x00FF3DF4 -> 0x0001
```

The selector-0 collision store trace also confirms that this target is not spuriously rewritten
from another record during the route. Its retained value and current semantic source agree.
Consequently `WRONG_COLLISION_RECORD_POINTER`, `WRONG_CELL_OFFSET`, `ROW_INDEX_ERROR`,
`COLUMN_INDEX_ERROR`, `STALE_SEGMENT_COLLISION`, `EARLY_SEGMENT_SWITCH`,
`WRONG_NATIVE_COLLISION_BASE`, and `PLAYER_PROBE_WRONG` are all unsupported for this reproduction.

## H. Lateral detach test — not route completion

The original route kept trying the climb direction/right-side jump and repeatedly reattached.
A bounded control-only rerun changed no memory and no ROM. At the stable position it released Up
and applied left+jump:

| Frame | X/Y | State | Result |
|---:|---:|---:|---|
| 4223 | `0x0121/0x003E` | 4 | attached beneath ceiling |
| 4225 | `0x0121/0x003E` | 2 | lateral release begins |
| 4255 | `0x0100/0x003E` | 3 | clear of chain, moving left |
| 4323 | `0x00E3/0x0070` | 1 | ordinary grounded movement |

The run continued through frame 5200 with progression `0x0011` and no crash, but Y increased from
`0x003E` to `0x0070`: Rastan fell into the lower/previous section. Tighe reproduced the same result
in BlastEm. This proves only **CHAIN DETACH: PASS**. It does not prove a usable upper exit or
forward traversal; **FORWARD NATURAL TRAVERSAL: FAIL — USER BLASTEM**. The earlier acceptance was
false and is retracted.

The correct ceiling-cell proof remains valid and excludes only that one candidate. Investigation
continues with the arcade upper landing and the complete bounded exit corridor. `0xFF3DF4` must
not be altered.

## I. Build 0378 correction and result

The selector-0 and selector-1/2 collision publishers now call
`resolve_plane_a_collision_cell`, which derives the collision word from the same logical row,
logical column, live descriptor pointer, and ring-unwrapped source selection as
`resolve_plane_a_cell`. This is a general source-ownership correction; it has no rope, stage,
progression, or coordinate special case. The post-build 72-cell corridor has zero collision
mismatches and restores the eight cells that differed in Build 0377.

- Build 0378 produced: **YES**
- Runtime counter: **377 -> 378**
- Canonical ROM: `dist/rastan-direct/rastan_direct_video_test_build_0378.bin`
- Canonical SHA-256: `2ae724691737fda44f98368ba58d76975016be8a7a73447b979683d064b83e63`
- ROM size: 1,724,088 bytes
- Opcode replacements: 230
- Canonical coverage: `0x1A4EB8`
- Variants: canonical, `_d`, `_s`, `_do`, `_c` all present and 1,724,088 bytes
- Production semantic subsystem: native Plane-A gameplay collision publication
- Native semantic cut: retained logical map cell and descriptor choice to final Genesis WRAM
  collision word; no PC080SN shadow or raw chip write added
- Legacy removed: no additional chip tail; the change aligns an existing native publisher
- Legacy intentionally remaining: retained arcade map/collision consumers and movement logic
- Static proof: source resolver equivalence and current address-map/disassembly inspection
- Runtime proof: GENESIS NTSC MAME post-build corridor, zero collision mismatches
- Existing project tools reused: the established Build-0378 focused route/corridor scripts,
  canonical Ghidra exports, disassemblies, and generated address map
- New tooling created: `arcade_exit_trace.lua`, narrowly extending the existing route cadence to
  capture the first original-arcade third-chain attachment; no broad framework was added
- Why necessary: the earlier Genesis-only corridor did not identify the arcade attachment epoch
- Build-0376 second-rope behavior: production code retained; user regression test still required
- Build-0377 boss-room behavior: production code retained; user regression test still required
- Chain attach: **PASS**
- Chain detach: **PASS**
- Forward natural traversal: **FAIL — USER BLASTEM**
- MODE Round-2 cycling: **NOT INVESTIGATED — DEFERRED**
- Unresolved limitation: the first post-attachment gameplay decision that sends arcade Rastan to
  the upper route but Genesis Rastan back to the lower section is not yet captured.
- STOP status: **STOPPED at that exact unresolved post-attachment decision; no further candidate
  was patched.**

### USER MUST VERIFY

- Build 0378 remains a failed traversal candidate: do not accept it as fixing the third-chain
  route.
- Its collision correction should remain under test for ordinary R1 Phase-2 terrain, the three
  chain attach/detach points, and absence of new collision holes.
- Build-0376 second-rope crash and Build-0377 boss-room MODE crash must remain absent.

The subsequent vertical-scroll comparison is documented separately in
`docs/design/Cody_third_chain_vertical_scroll_divergence_resolution.md`. It proves that the cited
arcade `0x010D` and Genesis `0x0026` frames were different ring epochs; the exact same `0/0` epoch
matches at `0x010D`, so no scroll patch or Build 0379 was justified.
