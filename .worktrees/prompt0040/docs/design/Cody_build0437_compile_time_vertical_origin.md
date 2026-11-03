# Cody Build 0437: Compile-Time Vertical-Origin Correction

## Task and baseline

- Agent/task: Cody — remove Build-0436 runtime origin state and use Makefile immediates.
- Baseline: Build 0436 (preserved; runtime-state implementation rejected).
- Produced build: 0437.
- Counter: 436 -> 437.
- Production files changed: `apps/rastan-direct/src/pc090oj_hooks.s`,
  `apps/rastan-direct/src/vdp_comm.s`.
- Makefile values remain `RASTAN_FRONTEND_Y_ORIGIN ?= 8` and
  `RASTAN_GAMEPLAY_Y_ORIGIN ?= 8`.

## Semantic boundary and architecture

The semantic cut is unchanged: arcade-owned scene selection, object positions, animation,
visibility, ordering, and scroll decisions remain above the cut; the established native tails
produce final Genesis SAT coordinates and Plane A/B VSRAM values below it. This correction changes
only the final presentation-coordinate arithmetic.

No additional PC090OJ/PC080SN chip tail was retired in this correction. The already-retired chip
tails remain retired, no chip-shaped state was restored, and no new shadow, mirror, projector,
dispatcher, or compatibility path was introduced. Existing unrelated compatibility code remains
outside this task.

## Correction

Build 0436 wrote a Makefile-selected origin into the WRAM word `native_active_y_origin` once per
sprite pass, then loaded that word for every non-fixed sprite. Build 0437 removes the stores, load,
BSS word, and symbol completely.

For default 8/8 builds, conditional assembly emits one shared `subi.w #8,d2` in the SAT finalizer.
The frontend/gameplay renderer stays shared. If the two configured values differ, the assembler
emits two tiny scene-domain paths containing the respective immediate operations and reconverges
at `.Lnq_y_origin_ready` before the shared bounding, residency, and SAT work.

Plane A and Plane B no longer select an origin into `d1`. Each plane applies its configured
immediate directly to the negated scroll value, then reconverges into the existing gameplay-only
9-bit mask and VSRAM publication.

The fixed-screen top-HUD branch remains before the configurable origin path and retains
`PC090OJ_FIXED_HUD_Y_OFFSET = -8`. Viewport 0..223 and all world/collision state are unchanged.

## Static proof

- `native_active_y_origin` has no production-source reference and is absent from the linked symbol
  table.
- No replacement origin RAM word exists; the BSS allocation was deleted.
- Default sprite object code contains `subi.w #8,d2` with no scene-origin RAM access.
- Default Plane A and Plane B object code each contains `addi.w #8,d0`.
- Only `pc090oj_hooks.s` and `vdp_comm.s` reference either origin constant; collision, actor/world,
  camera-state, hitbox/hurtbox, sword/contact, and rope logic reference neither.
- Top-HUD tuples still take the bit-14 fixed-screen path and never use either configurable origin.
- All six generated Build-0437 variant receipts record frontend 8 / gameplay 8.

### Alternate 8/0 compile proof

The two affected objects were assembled, without linking or numbering a ROM, using frontend 8 and
gameplay 0. Disassembly proved:

- sprite frontend path: `subi.w #8,d2`;
- sprite gameplay path: `subi.w #0,d2`;
- Plane A frontend/gameplay paths: `addi.w #8,d0` / `addi.w #0,d0`;
- Plane B frontend/gameplay paths: `addi.w #8,d0` / `addi.w #0,d0`.

The objects were restored to the default 8/8 configuration before the numbered build. Alternate
compile proof: PASS.

## Build and gates

Canonical opcode-replacement count: 231 sites; expected Genesis-byte coverage: `0x292EB8`.
Canonical gate PASS. Gameplay-entry gate PASS. The known Phase-1 seven-epoch gate remains FAIL;
the numbered artifact was preserved per project policy. The complete canonical, `_d`, `_s`, `_do`,
`_c`, and `_full_hud` family and all configuration receipts passed the variant-set check.

The standard fixed 30-second **GENESIS NTSC MAME** trace completed at 1,798 frames with 46,949 live
VDP-port writes and no reported address, bus, illegal-instruction, or crash-handler event in the
gameplay-entry gate evidence. Trace:
`states/traces/rastan_direct_video_test_build_0437_mame_30s_20261016_222647/`.

## Deterministic rope benchmark

The existing unchanged **GENESIS NTSC MAME** route was run three times per ROM.

| ROM | Trials | Median | vs 0435 | vs 0436 |
|---|---|---:|---:|---:|
| canonical | 806, 806, 806 | 13,450.653 ms | +3 frames / +50.065 ms | -1 frame / -16.688 ms |
| `_full_hud` | 859, 859, 859 | 14,335.125 ms | +5 frames / +83.441 ms | -2 frames / -33.376 ms |

Both results are deterministic. Removing runtime origin state reduced the Build-0436 result, but did
not restore either ROM to Build-0435 timing. Therefore the Build-0436 benchmark regression is only
partially reduced and is **not resolved** by this correction. No further performance investigation
was performed in this task.

## Artifacts

All artifacts are 2,698,936 bytes.

| Artifact | SHA-256 |
|---|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0437.bin` | `cadfef11f2e87621d087874335f03278041665acbeec79cadb10a57dfdd1d2e1` |
| `dist/rastan-direct/rastan_direct_video_test_build_0437_d.bin` | `1828b4fbe01f8347ae1ed02af6927fc754030292a4e7d4cec24ef8db3c7502fe` |
| `dist/rastan-direct/rastan_direct_video_test_build_0437_s.bin` | `7baa895c6b755241adf6325585e7ba2a39cfdf33a3707829f64028f27fcd28d4` |
| `dist/rastan-direct/rastan_direct_video_test_build_0437_do.bin` | `df54b39dcd7e959b10abf9ae4cbcb6e09739dd8a0a5517edb74f641465b027af` |
| `dist/rastan-direct/rastan_direct_video_test_build_0437_c.bin` | `9d5b4e62c9c1256c93f2c58079685423ce0e1bf3fe3ec7eada3c2bf865981189` |
| `dist/rastan-direct/rastan_direct_video_test_build_0437_full_hud.bin` | `c8bd7ca39a719ad2645a4264f45932fcf59a78403fc5389f047b9869ee277a36` |

## Tool reuse

- Existing project tools reused: the Makefile-owned build/gates/fixed trace and
  `tools/mame/run_rope_attach_performance_benchmark.sh` with its unchanged Lua route and summarizer.
- New tooling created: none.
- Why new tooling was necessary: not applicable.

## Native-replacement policy checklist

- Semantic cut remains above chip-specific execution: YES.
- Complete previously retired PC090OJ/PC080SN tails remain bypassed: YES.
- Chip-shaped state consumed or restored: NO.
- New mirror/shadow/projector/device dispatcher: NO.
- Transitional compatibility added: NO.
- Arcade gameplay/frame/VBlank ownership preserved: YES.
- Final Genesis SAT/VSRAM output produced directly: YES.

## USER MUST VERIFY

On real Genesis hardware, test the default Build 0437 canonical and `_full_hud` ROMs through title,
attract, ROUND/READY, normal Round-1 horizontal and vertical movement, rope attachment, and combat.
Confirm that sprites remain aligned with both planes, the top HUD does not move, collision/grounding
and rope contact are unchanged, and the full-HUD variant retains its complete HUD placement.

STOP status: implementation, build, static proof, standard trace, and requested rope benchmarks
complete; real-hardware presentation/gameplay acceptance remains with Tighe.
