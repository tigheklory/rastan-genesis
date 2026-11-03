# Cody - Build 0169 BG-Pass Collision Producer Candidate

**Date:** 2026-07-14
**Type:** Analysis-first implementation + verification
**Baseline:** Build 0168 candidate, `dist/rastan-direct/rastan_direct_video_test_build_0168.bin`, SHA `be2d575256ff72d942055c3477a31b0be4af1c863b9cf114f1c5f3bbd184d993`, counter `168`
**Produced build:** Build 0169, `dist/rastan-direct/rastan_direct_video_test_build_0169.bin`, SHA `b8c87809fe84650b8c31b7b835469609034fca29cf43a4f2aeb669925acc1634`, size `1,581,480`
**Scope:** Correct the Build 0168 collision-map overcorrection by moving Stage 1 collision production from the FG_SRC visual helper to a BG-pass collision side-channel matching arcade producer `0x0559B2`. No player-state patch, no safe-ground hardcode, no death-handler change, no D00298/Exodus/sprite/scroll/collision broad rewrite.

## Phase 0

Classification: **EXTENDING** OPEN-017 and the Build 0159/0168 collision-map producer chain. Relevant priors: KF-039 mapped WRAM base, KF-040/KF-041 copied pipeline step replaced by partial Genesis helper, KF-042 pass-selector relocation, Build 0168 collision-reader rebase, and Build 0169 ground-contact analysis. No contradiction of confirmed or strong findings detected.

Architecture compliance: **CONFIRMED**. Arcade code remains the program. The new Genesis code is a helper called from the existing opcode-replaced arcade BG producer entry, preserves registers, writes only mapped WRAM collision staging, and returns to arcade flow. It does not raw-write VDP/PC080SN hardware and does not force player/camera/collision state.

## Arcade Producer Proof

Original arcade disassembly proves Stage 1 collision-map production belongs to the BG producer path:

- Dispatch `arcade_pc 0x055948`: `a5@(0x10A8)==0` selects BG branch `0x055968`; nonzero selects FG branch `0x055990`.
- BG entry `arcade_pc 0x055968`: loads `a0 = a5@(0x10A0)`, `a1 = 0x0010D080`, `a3 = 0x0010D040`, then calls `0x0559B2` for 16 descriptors.
- BG producer `arcade_pc 0x0559B2`: per row, reads collision word from the rebuilt descriptor/table data and stores it to `0x0010DE00 + ((a0 - 0x00C08000) >> 1)`.

Collision word semantics from `0x0559B2`:

```asm
559b6: lea    0x20(a2),a6
559ba: move.w (a6),d0
559bc: cmpi.w #0x00ff,d0
559c0: beq    0x559d4
559c2: d7 = a5@(0x10CA) * 2 + row * 8
559ce: lea    0x14(a2,d7.w),a6
559d4: lea    0x22(a2),a6      ; alternate collision word
559d8: move.w (a6),d0
559da: d7 = a0 - 0x00C08000
559e2: d7 >>= 1
559e4: d7 += 0x0010DE00
559ec: move.w d0,(a6)
```

So the correct Stage 1 model is not FG_SRC collision emission. It is a BG-pass descriptor walk over the rebuilt list at mapped Genesis WRAM `0x00FF1000` and block/table data addressed through the Genesis ROM copy base.

## Build 0168 Failure Mechanism

Build 0168 successfully rebased the collision reader endpoint to mapped Genesis WRAM `0x00FF1E00` and removed the earlier raw-ROM type-8 failure. However, it populated that buffer from `genesistan_stage_fg_src_column`, a visual FG_SRC replay helper. Runtime evidence showed this overcorrected the opening collision boundary:

| Runtime | First gameplay row/col | Word | Result |
|---|---:|---:|---|
| Arcade | `6/6` | `0x0000` | falls from `Y=0x0030` to `Y=0x0070` |
| Build 0168 | `6/6` | `0x0003` | grounded immediately at `Y=0x0030` |
| Diagnostic Build 0167 | `6/6` | `0x0000` | empty map, falls through; not a fix |

This proved Build 0168's reader rebase concept was needed, but the producer side-effect was attached to the wrong owner/content model.

## Implementation

Changed `apps/rastan-direct/src/tilemap_hooks.s` only for producer behavior:

- `genesistan_stage_fg_src_column` now stages only visible FG cells through `genesistan_hook_tilemap_fg_fill`; its collision-map side-effect was removed.
- Added `genesistan_stage_bg_collision_column`, called from `genesistan_hook_tilemap_plane_a` only when `genesistan_current_scene_id == SCENE_GAMEPLAY_ID`.
- The new helper validates the original collision destination as `0x00C08000..0x00C0BFFF`, walks `A5+0x1000` rebuilt descriptor pointers, reads the BG block pointer from descriptor word 1, applies the arcade collision word rule (`block+20+row*8+strip*2` or `block+34` when `block+32 == 0x00FF`), and writes mapped collision WRAM `0x00FF1E00 + ((dest - 0x00C08000) >> 1)`.
- The helper does not stage tiles and does not advance `a5@(0x10A0)`; the existing translated producer remains responsible for cursor progression.

Canonical invariant update:

- `opcode_replace` count unchanged: `151`.
- `total_genesis_bytes_covered`: `0x182114 -> 0x1821A8`.
- Mechanical delta: `+0x94` net for removing the FG collision block and adding the BG collision side-channel.

## Build Verification

Command run:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

First invocation assembled successfully but stopped at the canonical coverage gate:

```text
expected total_genesis_bytes_covered=0x182114 and opcode_replace patched_site count=151;
got total_genesis_bytes_covered=0x1821A8 opcode_replace patched_site count=151
```

After updating only the canonical coverage constants to `0x1821A8`, the release passed:

- Boot guard: PASS.
- Canonical gate: `GATE_PASS`.
- Counter advanced: `168 -> 169`.
- Numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0169.bin`.
- Rolling artifact: `apps/rastan-direct/dist/rastan_direct_video_test.bin`.
- SHA256: `b8c87809fe84650b8c31b7b835469609034fca29cf43a4f2aeb669925acc1634` for both numbered and rolling ROMs.
- Size: `1,581,480` bytes.
- `cmp`: numbered and rolling ROMs byte-identical.
- Release trace: `states/traces/rastan_direct_video_test_build_0169_mame_30s_20260714_162157/`.

## Static Verification

Generated disassembly confirms:

- `runtime_genesis_pc 0x00070260`: gameplay path calls `genesistan_stage_fg_src_column`.
- `runtime_genesis_pc 0x00070264`: gameplay path calls `genesistan_stage_bg_collision_column`.
- `runtime_genesis_pc 0x00070400..0x00070498`: FG_SRC helper now stages visible cells and returns; no `0x00FF1E00` collision write remains in that helper.
- `runtime_genesis_pc 0x0007049A..0x00070560`: BG collision helper validates `0x00C08000..0x00C0BFFF`, reads descriptor/block data, and writes collision words to `0x00FF1E00` via `%fp@(0,%d0.w)`.
- `runtime_genesis_pc 0x000703F0`: existing render-side invalid-destination path still advances `a5@(0x10A0)` by `0x4000`; the collision helper does not duplicate that state advance.

## Runtime Verification

Trace directory:

`states/traces/build0169_bg_collision_candidate_20260714_162157/`

Command used the existing ground-contact trace harness against Build 0169. MAME exit code: `0`.

Comparison against prior arcade/Build0167/Build0168 evidence:

| Runtime | First gameplay | First Y>=0x70 | First grounded/contact flag | Final sampled state |
|---|---|---|---|---|
| Arcade | frame `307`, row/col `6/6`, word `0x0000`, `Y=0x0030` | frame `338`, `Y=0x0070`, word `0x0000` | frame `400`, `Y=0x0070`, camera Y `0x0149`, row/col `36/6`, word `0x0000`, down2 `0x3400` | `Y=0x0070`, camera Y `0x0149` |
| Build 0168 | frame `536`, row/col `6/6`, word `0x0003`, `Y=0x0030` | none | frame `539`, still `Y=0x0030`, camera Y `0x0000` | stuck at `Y=0x0030`, later word `0x1000` |
| Build 0169 | frame `541`, row/col `6/6`, word `0x0000`, `Y=0x0030` | frame `598`, `Y=0x0070`, word `0x0000` | frame `766`, `Y=0x0070`, camera Y `0x0149`, row/col `36/6`, word `0x0020` | `Y=0x0070`, camera Y `0x0149` |

Assessment:

- Build 0169 fixes the Build 0168 immediate early-solid cell at row/col `6/6` (`0x0003 -> 0x0000`).
- Build 0169 restores the opening fall to `Y=0x0070` and the same camera-Y landing band (`0x0149`) in this scripted window.
- Build 0169 collision map population is close to arcade in aggregate (`nonzero=1752`, no type-8) but not byte-identical to the prior arcade sample (`nonzero=1756`; at the sampled landing cell row/col `36/6`, Build 0169 has `0x0020` while arcade trace had `0x0000`). This is a remaining collision-content caveat, not a reason to revert the producer-owner correction.
- No mode-8 event occurred through frame `1120` in the Build 0169 trace.

## OPEN / KNOWN_FINDINGS Impact

OPEN-017 remains open. Build 0169 is a candidate that corrects the Build 0168 collision producer ownership error in the scripted opening window, but broader gameplay, real hardware, visual composition, input/control, VBlank/slowdown, READY/header sprites, continue/game-over, D00298, and suspicious PC090OJ records remain deferred.

KNOWN_FINDINGS impact: Option A. No new durable finding indexed; this implements the already-documented BG-pass collision producer ownership finding from the Build 0159/0169 evidence chain.

## STOP

STOP triggered: **NO**. Bounded source change, build, static verification, and runtime verification completed. User/Tighe should still visually and hardware-test Build 0169 before treating it as accepted.
