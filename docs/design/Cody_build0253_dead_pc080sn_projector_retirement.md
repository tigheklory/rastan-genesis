# Cody Build 0253 Dead PC080SN Projector Body Retirement

## Baseline
- Accepted baseline: Build 0252
- Accepted ROM: `dist/rastan-direct/rastan_direct_video_test_build_0252.bin`
- Accepted SHA-256: `5f1457bcebd1f77e496de0cce54de6de5e41ad9846073d50d55e6e6debece948`
- Accepted counter: `252`
- User visual verification: PASS for Rastan, lizard men, bats, and axe item. Remaining visual issues are preexisting.
- Build 0252 was preserved. No revert was performed.

## Phase 0 Statement
Read for this task: `RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`, `AGENTS_LOG.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, and `CLOSED_ISSUES.md`.

Relevant priors:
- The native replacement policy remains authoritative: arcade semantic decisions stay upstream; PC080SN/PC090OJ chip-specific tails are retirement targets only when their replacement boundary is proven.
- Build 0252 is the accepted visual baseline and already hoisted the gameplay skip around `vdp_project_bg_tall_if_dirty` and `vdp_project_fg_tall_if_dirty`.
- Build 0245/0248 native Plane A/B producers and strip commits are the active gameplay PC080SN path.
- Build 0251/0252 native PC090OJ gameplay path is preserved and intentionally untouched.

Rediscovery hazards touched:
- Legacy PC080SN projector retirement is adjacent to the native Plane A/B migration work and must not re-enable projection over native output.
- PC090OJ object/mirror state and sprite lifecycle are out of scope for this task.

Task classification: EXTENDING, focused dead-code removal after accepted Build 0252 visual proof.

Contradiction of CONFIRMED or STRONG findings: NONE.

## Files and Evidence Inspected
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/boot/boot.s`
- `apps/rastan-direct/out/symbol.txt`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- `states/traces/rastan_direct_video_test_build_0253_mame_30s_20260803_210400/genesis_exec_summary.txt`

Search command used for xrefs:

```text
rg -n "vdp_project_bg_tall_if_dirty|vdp_project_fg_tall_if_dirty|staged_bg_tall_buffer|staged_fg_tall_buffer|bg_tall_dirty|fg_tall_dirty|bg_tall_project_base|fg_tall_project_base" apps/rastan-direct/src apps/rastan-direct/out/symbol.txt tools/translation specs build/rastan-direct
```

## Current Control Flow Before Removal
In Build 0252 source, `_vblank_service` checks `genesistan_current_scene_id` before invoking the projector stubs:

```asm
bsr     vdp_commit_tiles_if_dirty
cmpi.b  #1, genesistan_current_scene_id
beq.s   .Lvs_skip_gameplay_tall_projectors
bsr     vdp_project_bg_tall_if_dirty
bsr     vdp_commit_bg_strips_if_dirty
bsr     vdp_project_fg_tall_if_dirty
bra.s   .Lvs_after_tall_projectors
.Lvs_skip_gameplay_tall_projectors:
bsr     vdp_commit_bg_strips_if_dirty
.Lvs_after_tall_projectors:
bsr     vdp_commit_fg_narrow_strips
```

Gameplay scene (`genesistan_current_scene_id == 1`):
- `vdp_project_bg_tall_if_dirty` is not called.
- `vdp_project_fg_tall_if_dirty` is not called.
- `vdp_commit_bg_strips_if_dirty` still runs.
- `vdp_commit_fg_narrow_strips` still runs.

Non-gameplay scenes (`genesistan_current_scene_id != 1`):
- `_vblank_service` still calls the projector function labels.
- Before Build 0253, each projector function immediately returned before its old body:

```asm
vdp_project_bg_tall_if_dirty:
    cmpi.b  #1, genesistan_current_scene_id
    beq.s   .Lbg_tall_project_done
    rts

    ; old projector body here, after an unconditional return
```

```asm
vdp_project_fg_tall_if_dirty:
    cmpi.b  #1, genesistan_current_scene_id
    beq.s   .Lfg_tall_project_done
    rts

    ; old projector body here, after an unconditional return
```

Therefore the old bodies could not be entered through gameplay or non-gameplay VBlank control flow.

## Reachability Proof
### Gameplay Reachability
BG projector body reachable in gameplay: NO.

Reason: `_vblank_service` branches around both projector calls when `genesistan_current_scene_id == 1`. The gameplay path goes directly to `vdp_commit_bg_strips_if_dirty`, then `vdp_commit_fg_narrow_strips`.

FG projector body reachable in gameplay: NO.

Reason: same call-site branch around both projector calls when `genesistan_current_scene_id == 1`.

### Non-Gameplay Reachability
BG projector body reachable in non-gameplay: NO.

Reason: the only source caller is `_vblank_service`. In non-gameplay, the function is called, but the local function logic falls through to an immediate `rts` before the old body. The branch target `.Lbg_tall_project_done` is also an `rts` after the body, but it is only taken for scene 1; scene 1 no longer reaches the call site.

FG projector body reachable in non-gameplay: NO.

Reason: identical structure to the BG projector. The only source caller is `_vblank_service`; non-gameplay calls hit the immediate `rts` before the old body.

### Direct Label Entry
Private labels inside the old bodies were not global, had no source xrefs after the entry stubs, and were removed with the old bodies. Exported function symbols were retained.

## Xref Classification
| Symbol | Xref Summary | Classification | Action |
| --- | --- | --- | --- |
| `vdp_project_bg_tall_if_dirty` | Global symbol; source caller at `vdp_comm.s` VBlank non-gameplay path | exported no-op stub still required | retained stub |
| `vdp_project_fg_tall_if_dirty` | Global symbol; source caller at `vdp_comm.s` VBlank non-gameplay path | exported no-op stub still required | retained stub |
| old BG projector body labels | Only internal to unreachable body | unreachable code body/private labels | removed |
| old FG projector body labels | Only internal to unreachable body | unreachable code body/private labels | removed |
| `staged_bg_tall_buffer` | Written by `genesistan_hook_tilemap_bg_fill_tall`; cleared by boot | data still referenced | retained |
| `staged_fg_tall_buffer` | Written by `genesistan_hook_tilemap_fg_fill_tall`; cleared by boot and C-window clear path | data still referenced | retained |
| `bg_tall_dirty` | Written by tall BG fill; cleared by boot | data still referenced | retained |
| `fg_tall_dirty` | Written by tall FG fill and C-window clear; cleared by boot | data still referenced | retained |
| `bg_tall_project_base` | Cleared by boot; exported global | unsafe to remove in this code-body-only task | retained |
| `fg_tall_project_base` | Cleared by boot; exported global | unsafe to remove in this code-body-only task | retained |

## Implementation
Changed `apps/rastan-direct/src/vdp_comm.s` only for production source:
- Replaced the unreachable `vdp_project_bg_tall_if_dirty` old body with an exported `rts` stub and explanatory comment.
- Replaced the unreachable `vdp_project_fg_tall_if_dirty` old body with an exported `rts` stub and explanatory comment.
- Removed only private old-body labels and copy/project loops.

Intentionally retained:
- `vdp_commit_bg_strips_if_dirty`
- `vdp_commit_fg_narrow_strips`
- native Plane A/B producers
- `vdp_commit_scroll`
- `vdp_commit_sprites_vram`
- palette reassert paths
- all tall buffers, dirty flags, project-base globals, and boot clears
- native sprite queues and PLAYER_BODY lifecycle
- PC090OJ native finalizer
- collision, rope/reset, input, audio, and frontend behavior

## Canonical Coverage Update
The first build stopped at the canonical invariant with:

```text
expected total_genesis_bytes_covered=0x184C9C and opcode_replace patched_site count=218;
got total_genesis_bytes_covered=0x184BA0 opcode_replace patched_site count=218
```

The byte delta is `-0xFC`, matching the removal of unreachable Genesis-only projector code while preserving opcode replacement site count.

Updated paired constants:
- `tools/translation/postpatch_startup_rom.py`: `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x184BA0`
- `tools/translation/verify_canonical_rom.py`: `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x184BA0`

Opcode replacement count remained `218`.

## Build 0253 Validation
Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release PC090OJ_MIRROR_RECORDS=256 RASTAN_GAMEPLAY_HUD_SPRITES=2
```

Result:
- Build produced: YES, exactly Build 0253
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0253.bin`
- SHA-256: `3015974ec444e3be2d49f182a191dfb5a536dfb89b07d3e9ec84c9767f1e6155`
- Size: `1592224`
- Counter: `253`
- `GATE_PASS`: YES
- Rolling artifact SHA matches numbered ROM.
- `RASTAN_GAMEPLAY_HUD_SPRITES = 2` present in `apps/rastan-direct/out/symbol.txt`.
- `vdp_reassert_bank36_line0` remains present.
- Postpatch address-map coverage: `total_genesis_bytes_covered = 1592224` (`0x184BA0`), gaps `[]`, overlaps `[]`.
- Opcode replace sites: `218`.

## MAME Smoke Trace
Trace directory:

```text
states/traces/rastan_direct_video_test_build_0253_mame_30s_20260803_210400/
```

Summary:
- Frames: `1798`
- `vdp_ports_live count=47197`
- `fg_cwindow_live count=0`
- No unmapped/fatal/error summary entries were reported.

## Open/Closed Issues Impact
Open issues touched:
- OPEN-017 / OPEN-024-adjacent native rendering/performance cleanup context.

New issues opened: none.

Issues closed: none.

Issues intentionally deferred:
- non-gameplay PC080SN data/global retirement
- remaining visual issues from Build 0252 user baseline
- PC090OJ compatibility retirement
- rope/reset/collision/input/audio/frontend behavior

## KNOWN_FINDINGS Impact
Option A: No new finding to index. This is a bounded cleanup following already-established native PC080SN Plane A/B migration and Build 0252 visual acceptance.

## STOP Status
STOP triggered: NO.
