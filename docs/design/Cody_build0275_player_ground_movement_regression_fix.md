# Build 0275 Player Ground/Movement Regression Fix

## Baseline and Scope

- Accepted forward baseline: Build 0273, SHA-256 `a9c8a609774e48c38c3e5c740a3e04f7b74675a896dc0a36d2529846ea5363b8`.
- Rejected candidate investigated: Build 0274, SHA-256 `4ead3b77da5bba008e5a0f18459135d856121f673c6fc772ead7b104876231e1`.
- Classification: EXTENDING OPEN-024 and KF-074.
- Semantic cut retained: arcade FRONT/BODY state and mapping decisions produce final native Genesis `PLAYER_FRONT` / `PLAYER_BODY` entries.
- Complete chip tail still retired: player PC090OJ tuple stores, tuple decoding, scanning, and player SAT projection are not restored.

## Root Cause

Build 0274's inline native realization used `D1`, `D3`, `D4`, and `D6` as temporary word0/code/X/Y registers. `native_sprite_emit` preserves registers only after those temporary values are installed, so it restored the native values rather than the values live at entry to the original arcade producer.

Original-arcade Ghidra/disassembly proves FRONT (`0x059F92..0x05A096`) modifies only `A0`, while BODY root (`0x0540CC..0x054324`) uses `D0/D1/D2` and `A0..A4` but does not modify `D3/D4/D6`. The native replacement therefore violated the retained arcade caller contract. FRONT executes before movement/state processing and BODY executes later in the same main-loop frame, so the leaked rendering temporaries can alter retained arcade state processing.

The bounded correction saves only newly clobbered registers:

- FRONT: preserve `D1/D3/D4/D6` at its sole entry/exit.
- BODY: preserve `D3/D4/D6` at entry, common exit, and replaced inactive-mode exit.

`MOVEM.L` does not alter CCR, so producer exit flags survive the restores.

| Field/routine | Arcade semantic purpose | 0273 behavior | 0274 behavior | Fix |
|---|---|---|---|---|
| `a5+0x129A` | X anchor for an auxiliary four-piece PC090OJ object | Tuple-zero producer/copy supplies anchor | Native BODY publishes anchor directly | Keep direct semantic anchor |
| `a5+0x129C` | Y anchor for an auxiliary four-piece PC090OJ object | Tuple-zero producer/copy supplies anchor | Native BODY publishes anchor directly | Keep direct semantic anchor |
| `0x0547C0` | Consumes tuple-zero X/Y for auxiliary positioning, then continues unrelated state logic | Copies tuple zero when enabled | Copy prologue retired because native BODY owns anchor | Keep Build 0274 retirement |
| `0x051E00` | Seeds another auxiliary object X/Y from tuple zero | Reads tuple-zero X/Y | Reads retained direct anchor | Keep Build 0274 rewrite |
| FRONT `0x059F92` | Retained FRONT semantic producer | Leaves D registers unchanged | Leaks native `D1/D3/D4/D6` | Preserve introduced-only clobbers |
| BODY `0x0540CC` | Retained BODY semantic producer | Leaves `D3/D4/D6` unchanged | Leaks native `D3/D4/D6` | Preserve introduced-only clobbers |

## Original Arcade Anchor Proof

Ghidra exports under `analysis/ghidra/rastan_arcade/exports/` show all direct references:

- Writers: `0x052A74/0x052A7A` and `0x0547D0/0x0547D6`.
- Readers: `0x052AC6/0x052ADE` and `0x054834/0x05484C`.

Both consumer families add signed per-piece offsets and emit a four-piece auxiliary PC090OJ object. No reader feeds ground contact, slope, collision, camera, movement-state selection, or player physics. A blank tuple is `{word0=3,Y=0,code=0,X=0}`, so the original copy clears both anchors; Build 0274's direct blank clear preserves that value semantics.

## Timing

Original arcade order:

1. `0x05105A` performs the per-frame semantic write.
2. `0x051060` calls FRONT; the original register contract returns intact.
3. Retained movement/state update begins around `0x05132A`.
4. `0x05151C` calls BODY; the original `D3/D4/D6` contract returns intact.
5. `0x05154A` calls auxiliary consumer `0x0547C0`.

Build 0274 incorrect order/state:

1. Native lane reset and FRONT semantic decisions execute.
2. FRONT native realization leaves `D1/D3/D4/D6` temporary values live.
3. Retained movement executes with state the original FRONT never produced.
4. BODY later leaks `D3/D4/D6` into subsequent retained execution.

Corrected order:

1. Native lane reset stays at the same semantic boundary.
2. FRONT saves introduced-only scratch registers, realizes native entries, and restores caller state before movement.
3. Retained movement/state logic executes with the arcade register contract.
4. BODY restores introduced-only scratch registers at every BODY-root exit.
5. Native queues remain available to the existing VBlank finalizer.

## State Comparison

The focused comparison reused `states/traces/build0200_jump_fall_pending_move/jump_compare.lua`; no new disposable harness was created. Results are under `states/traces/build0274_player_ground_movement_compare_20260810/`.

| State/field | ORIGINAL ARCADE | Build 0273 | Build 0274 | Corrected build |
|---|---|---|---|---|
| Initial mode-3 Y | `0x0030` | `0x0030` | `0x0030` | Pending validation |
| Motion index | Decrements each frame | Decrements each frame | Reaches `0xFFFE`, then stalls | Pending validation |
| `a5+0x1266` | No 0274-only early `+2` | Accepted landing trajectory | `0x0002` one frame after mode-3 entry | Pending validation |
| Landing | Mode 3 exits near Y `0x0070` | Stable mode 0/Y `0x0070` | Re-enters mode 3 and reaches Y `0x0100` | Pending validation |
| `a5+0x129A/0x129C` | Auxiliary anchor | Tuple-backed anchor | Direct native anchor | Direct native anchor retained |

The first sampled divergence is one frame after mode-3 entry: Build 0274 has `a5+0x1264=1`, `a5+0x1266=2`, then stalls the motion index at `0xFFFE`; Build 0273 and original arcade continue their landing trajectories.

## Register / CCR Proof

| Replacement site | Required live regs/flags | Preservation proof |
|---|---|---|
| `0x05105A` reset insertion | Original store result and caller registers | Helper preserves registers; following FRONT call does not consume store flags |
| FRONT `0x059F92/0x05A096` | Original leaves D registers intact; exit CCR survives | `MOVEM.L D1/D3/D4/D6,-(SP)` and inverse restore; MOVEM does not alter CCR |
| BODY `0x0540CC/0x054324` | Original modifies `D0/D1/D2` but not `D3/D4/D6` | Only introduced clobbers are stacked/restored |
| BODY inactive `0x0542E8` | Same BODY-root contract | Direct native clear restores `D3/D4/D6` before RTS |
| BODY/FRONT piece calls | Loop `D2`, producer registers, subsequent branch flags | Existing helper preserves `D2`; producer guards restore caller-only values |
| Anchor `0x0547C0` | Continuation flags | Continuation begins with `CMPI`, establishing consumed flags |
| Anchor source `0x051E00` | Original final `CLR.W` flags | Replacement ends with the same `CLR.W` |

## Architecture and Validation

Native BODY/FRONT remains the only gameplay player sprite path. This correction changes retained CPU register lifetime only. It does not recreate `a5+0x11B2` / `a5+0x0170` player tuples, a tuple decoder, scanner, or second SAT path. VBlank remains the sole finalizer and VDP authority.

Build, gate, Genesis NTSC smoke, and corrected state-comparison results are appended after candidate production.

## USER MUST VERIFY

- Stand still.
- Walk left and right.
- Jump and land.
- Walk and stand on normal ground.
- Try an actual slope.
- Attack while standing and walking.
- Face both directions.
- Take damage if reachable.
- Verify Rastan does not float or drift.
- Verify BODY/FRONT graphics remain correct.
