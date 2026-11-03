# Cody - Build 0163 Visual Result + Exodus Loop + Scroll Direction Boundary

**Date:** 2026-07-13  
**Type:** Analysis / documentation only  
**Mode:** No build, no source/spec/tool/ROM behavior changes  
**Build under discussion:** Build 0163 visual-test candidate  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0163.bin`  
**SHA256:** `6f6efa750a004e5f74d365eb0d43119e7e88456ae44abc477237af93725171c5`

## Scope

This note documents Tighe's Build 0163 visual result, classifies the forced gameplay sprite tile-refresh experiment, records the Exodus-specific `runtime_genesis_pc 0x0003A346` loop observation, and records the new arcade-vs-Genesis gameplay scroll-direction observation.

No fix is attempted here. The task intentionally does **not** touch collision, palettes, PC080SN/FG_SRC, VINT/vector/SR/VDP register ownership, hardcoded sprites, hardcoded SAT entries, hardcoded tile indices, second renderers, returning-title tile wipe, Exodus control-flow, or gameplay scroll direction.

## Phase 0

Relevant priors read:

- `RULES.md`
- `ARCHITECTURE.md`
- `docs/design/Andy_build0163_force_gameplay_sprite_tile_refresh.md`
- `docs/design/Cody_pc090oj_gameplay_tile_dma_vram_residency.md`
- `docs/design/Cody_pc090oj_gameplay_representation_activation.md`
- `docs/design/Cody_build0162_vint_timing_trace_classification.md`
- `AGENTS_LOG.md`
- `OPEN_ISSUES.md`
- `KNOWN_FINDINGS.md`

Task classification: **EXTENDING**. This extends OPEN-017 / OPEN-024 / OPEN-001 gameplay-rendering evidence after the Build 0163 controlled forced-refresh experiment.

Architecture compliance: **CONFIRMED**. This is documentation-only. The arcade code remains the program; Genesis-side code remains helper/service-only; no behavior was changed.

Contradiction of CONFIRMED/STRONG prior: **NONE**.

## Build 0163 Status

| Field | Value |
|---|---|
| ROM path | `dist/rastan-direct/rastan_direct_video_test_build_0163.bin` |
| SHA256 | `6f6efa750a004e5f74d365eb0d43119e7e88456ae44abc477237af93725171c5` |
| File size | `1,581,240` bytes |
| Build counter | `163` |
| `opcode_replace` | `137` |
| coverage | `0x1820B8` |
| Accepted build status | Build 0160 remains accepted unless Tighe explicitly accepts a later build |
| Build 0163 status | Preserved visual-test candidate; not accepted as a fix based on current visual result |

Current source state: **temporary experiment source present**.

Evidence: `apps/rastan-direct/src/pc090oj_hooks.s` still contains the Build 0163 gameplay-gated forced requeue in `.Lpc090oj_worklist_set`:

```asm
cmpi.b  #PC090OJ_SCENE_GAMEPLAY_ID, genesistan_current_scene_id
beq.s   .Lwls_differ
```

This task did not revert or modify that source.

## Forced-Refresh Experiment Interpretation

Settled mechanism from Andy's Build 0163 note:

- Build 0162: `tile_dma_count = 0` across gameplay; the residency cache blocks all gameplay sprite tile refresh.
- Build 0163: represented gameplay slots are forced to requeue tile DMA in gameplay; peak `tile_dma_count = 6`; `12/21` sampled gameplay frames re-DMA represented gameplay slots.
- Build 0163 uses the existing worklist/source/destination/DMA-commit path. SAT placement, decode, palette, collision, VINT, PC080SN, and player/camera logic were not intentionally changed.

Tighe's visual result:

- No major gameplay improvement versus Build 0162.
- `ROUND 1` / `READY` text is not meaningfully better.
- Gameplay still shows mountain background plus sprite/dot artifacts.
- Player/Rastan is still absent or quickly removed/dies.

Classification: **forced refresh alone is unlikely to be the primary sprite blocker**.

Interpretation:

- The Build 0163 forced-refresh mechanism is mechanically successful but visually weak/negative.
- Do not continue forcing more refresh as the main line.
- Do not treat the residency-cache refresh as an accepted permanent fix.
- The next sprite boundary should shift toward sprite identity/lifecycle/source/layout, not candidate activation, VINT cadence, or broader forced tile refresh.

## Visual Result Table

These are user visual observations, not automated proof.

| Area | Build 0163 observation | Interpretation |
|---|---|---|
| Initial title | Mostly intact | Frontend still basically works |
| Throne/story screen | Mostly intact | Frontend sprite/palette path still alive |
| `ROUND 1` / `READY` | Not meaningfully improved | Forced refresh did not fix text/dot artifacts |
| Gameplay mountain | Still appears | BG/palette path still alive |
| Player/Rastan | Absent / quickly removed | Not explained by tile-refresh experiment alone |
| Flickering dots | Still present | Next boundary remains sprite identity/source/layout or player lifecycle |
| Returning title cycle | Some TAITO/title-logo tiles corrupt | Scene-transition/LUT/tile-lifecycle issue, deferred |
| Gameplay scrolling | BG/FG scroll direction appears inverted vs arcade | Needs dedicated arcade-vs-Genesis scroll trace |

## Exodus-Specific `0x0003A346` Loop Note

Tighe observed Exodus behavior separately from BlastEm:

- Exodus is stuck in the previously identified `runtime_genesis_pc 0x0003A346` loop.
- Exodus appears not to reach the same final gameplay scene/palette state seen in BlastEm.
- Exodus screenshots show early/partial palette and scene-state behavior.

Interpretation:

- Exodus is not currently a fair visual verifier for Build 0163 gameplay sprite improvement.
- The Exodus issue should be treated as a strict-emulator / scene-transition / control-flow boundary, not as proof that Build 0163's forced tile-refresh mechanism failed.

Deferred issue note:

> Exodus `0x0003A346` loop / scene-transition completion boundary: In Exodus, the ROM appears to remain trapped in the previously identified `runtime_genesis_pc 0x0003A346` loop and does not reach the same final gameplay/palette state as BlastEm. This blocks using Exodus as a visual verifier for gameplay sprite/palette changes. Needs a dedicated strict-emulator control-flow trace later.

No Exodus fix was attempted.

## Gameplay Scroll-Direction Observation

Tighe's new observation:

- In the original arcade version, as Rastan/player falls, the background and foreground layers scroll with the tiles moving upward on the screen.
- In the Genesis build, across tested emulators and Genesis behavior observed by Tighe, the background and foreground scrolling appears inverted: tiles move downward on the screen.

This is important because scroll direction may explain why the gameplay background looks alive but wrong, and it may share causality with player lifecycle/death.

Possible causes, not decided here:

1. Genesis scroll sign/convention mismatch.
2. PC080SN-to-Genesis scroll conversion sign error.
3. Camera/player-position scroll calculation using a bad or missing player state.
4. Player death/removal causing camera/scroll state to diverge.
5. Wrong scroll source field being routed.
6. Timing/state mismatch during the `ROUND 1` fall.
7. Plane A/Plane B scroll values committed correctly but interpreted with inverted sign.
8. Arcade and Genesis being compared at slightly different logical moments.

Deferred note:

> Arcade-vs-Genesis gameplay scroll direction / player-fall camera trace: Compare arcade and Genesis during the same `ROUND 1` fall window, including player x/y, camera x/y, PC080SN scroll source fields, Genesis staged scroll values, VDP hscroll/vscroll/VSRAM values, and visible tile motion direction.

No scroll fix was attempted.

## Returning-Title Tile Wipe Note

Tighe observed that when the attract cycle returns to the title, some TAITO/title-logo tiles corrupt.

Current interpretation, deferred:

- These may be tiles added later in the LUT that live in a region wiped between scene transitions.
- The title scene may need a reload/revalidate lifecycle when returning from later scenes.
- This is separate from the gameplay sprite blocker.

No returning-title tile lifecycle fix was attempted.

## Player Death Note

Tighe observed that Player/Rastan appears to die quickly again.

Current interpretation, deferred:

- The known collision path remains unresolved.
- Collision WRAM `0xFF1E00` empty / raw reader issues remain deferred from earlier evidence.
- Sprite visibility and scroll-direction analysis must account for the possibility that the player is killed or removed before the sampled stable gameplay frames.

No collision/player-death fix was attempted.

## Recommended Next Boundaries

There are two serious next boundaries. If the immediate goal is Player/Rastan visibility, do Boundary A first. If the immediate goal is gameplay background correctness and camera causality, do Boundary B first.

### Boundary A - PC090OJ Arcade-vs-Genesis Player Sprite Identity / Lifecycle Trace

Purpose: determine whether Genesis ever has the same player/Rastan PC090OJ record that arcade has during the early `ROUND 1` fall window, before quick death/removal contaminates the trace.

Questions:

1. In original arcade at the same `ROUND 1` / `READY` / first gameplay timing, which PC090OJ records represent Rastan/player?
2. What codes, x/y, size, and visibility fields does arcade use for the player?
3. Does Genesis `pc090oj_object_ram` ever contain the same player record before quick death?
4. If yes, is it accepted, rejected, represented, overwritten, or removed?
5. If rejected, what exact filter rejects it?
6. If represented, which SAT slot and tile code does it use?
7. If never present, is the player already killed or skipped before sprite generation?
8. Are the represented Genesis records mostly `READY`/text/HUD or non-player objects?
9. Are codes `0x0512`/`0x0513` player/enemy graphics, text fragments, or something else?
10. Are rejected `0x002A` records meaningful arcade sprites or correctly offscreen filler?
11. Does the collision/death path remove the player before the sprite window being analyzed?

### Boundary B - PC080SN Arcade-vs-Genesis Gameplay Scroll Direction Trace

Purpose: determine why BG/FG tile motion during the `ROUND 1` fall appears inverted in Genesis compared with arcade.

Questions:

1. What are arcade player y, camera y, BG scroll, and FG scroll during the same fall frames?
2. What are Genesis player y, camera y, staged BG/FG scroll, and committed VDP scroll values?
3. Are Genesis scroll values sign-inverted relative to arcade?
4. Is the wrong source field used?
5. Is the camera following a missing/dead player state?
6. Is the visible inversion just a Genesis VDP convention that should be converted?
7. Do BG and FG invert together, or does one layer diverge first?

## Recommended Next Prompt Title

Recommended next prompt title if the goal is sprite/player visibility:

> PC090OJ Arcade-vs-Genesis Player Sprite Identity / Lifecycle Trace

Recommended next prompt title if the goal is background/camera correctness:

> PC080SN Arcade-vs-Genesis Gameplay Scroll Direction Trace

## Open / Closed Issues Impact

Open issues touched:

- OPEN-001: incomplete/incorrect graphics output context.
- OPEN-017: gameplay bring-up / Build 0163 visual-test candidate context.
- OPEN-024: PC090OJ sprite subsystem incomplete / garbage context.

New issues opened: NONE. The Exodus loop and scroll-direction observations are recorded here as deferred notes, not ledger edits, because this task is documentation-only and the prompt allowed keeping them in the design doc if no suitable small issue update was required.

Issues closed: NONE.

Issues intentionally deferred:

- Exodus `0x0003A346` loop / strict-emulator transition trace.
- Arcade-vs-Genesis gameplay scroll direction / player-fall camera trace.
- Returning-title tile wipe / tile lifecycle reload.
- Player death/collision path.
- VINT/vector/SR/VDP register ownership.
- PC080SN/FG_SRC implementation.
- Palette work.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. The Build 0163 visual result is important guidance, but it does not yet establish a durable new mechanism. The scroll-direction observation and Exodus-loop observation should wait for dedicated runtime traces before promotion.

## STOP

STOP triggered: **NO**. The requested documentation was completed without source/build changes.
