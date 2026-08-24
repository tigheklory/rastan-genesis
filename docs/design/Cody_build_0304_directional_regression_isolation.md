# Cody - Build 0304 Directional Regression Isolation

Date: 2026-08-22  
Classification: EXTENDING / A-B regression isolation  
Gameplay baseline: Build 0302  
Regressed candidate: Build 0303  
Produced isolation candidate: Build 0304

## Outcome

Build 0304 is the requested A/B isolation ROM. It retains Build 0303's exact-pattern package
compiler, stable slot allocation, boundary-only staged Plane-A/Plane-B remap, full dual-plane
name-table recommit, and event/reseed timing correction. The only gameplay-functional Build-0303
delta reverted is the replacement at `arcade_pc 0x05109C`: Build 0304 again executes the copied
Build-0302 arcade directional family.

This build does not claim that early Stage-1 collision is fixed. The mandatory MAME smoke trace did
not enter gameplay, so Tighe's early-Stage-1 test is the authoritative A/B result.

## Scope Discipline

- Active scope: Build-0303's early Stage-1 gameplay/collision regression only.
- User observations are evidence, not automatic implementation scope.
- Deferred later-game crashes and other observations were not investigated.
- No collision code, collision classification, terrain table, or collision-ring representation was
  changed.
- No broad graphics redesign or per-frame residency mechanism was introduced.

The temporary return to the copied directional family is an explicitly authorized isolation step,
not the final native PC080SN architecture. The retained semantic decision remains arcade-owned;
Build 0304 temporarily restores the prior chip-specific tail solely to identify whether Build
0303's native replacement caused the regression.

## Exact A/B Control-Flow Proof

All address spaces are labeled explicitly. The original instruction at `arcade_pc 0x05109C` is:

```text
4EB900055AD6    jsr arcade_pc 0x055AD6
```

Preserved numbered-ROM disassembly proves:

| Build | Call-site space | Instruction/target | Classification |
|---|---|---|---|
| 0302 | `runtime_genesis_pc 0x0512A2` | `jsr runtime_genesis_pc 0x055BB2` | copied Build-0302 directional semantics |
| 0303 | `runtime_genesis_pc 0x0512A8` | `jsr runtime_genesis_pc 0x070A8A` | `genesistan_pc080sn_directional_dispatch_native` |
| 0304 | `runtime_genesis_pc 0x0512A8` | `jsr runtime_genesis_pc 0x055BB8` | copied Build-0302 directional semantics restored |

The six-byte location change between Build 0302 and Builds 0303/0304 is caused by the retained
Build-0303 post-reseed insertion at `arcade_pc 0x050482`; it is not a guessed fixed offset.
Build-0304 `address_map.json` maps:

- `arcade_pc 0x05109C` inside copied segment `runtime_genesis_pc 0x05126C..0x0512F6`, with the
  instruction at `runtime_genesis_pc 0x0512A8`;
- `arcade_pc 0x055AD6` to copied target `runtime_genesis_pc 0x055BB8`.

The sole spec change was removal of the equal-size Build-0303 shift replacement at
`arcade_pc 0x05109C`. The native helper remains compiled for evidence preservation, but no gameplay
caller at this site reaches it.

## Binary Delta Proof

Build 0303 and Build 0304 have equal size. `cmp -l` reports only six changed bytes:

- ROM offsets `0x00018E..0x00018F`: Genesis header checksum;
- ROM offsets `0x0512AB..0x0512AD`: the JSR target changes from `runtime_genesis_pc 0x070A8A` to
  `runtime_genesis_pc 0x055BB8`;
- ROM offset `0x2E18DB`: diagnostic build-number digit 3 -> 4.

Therefore the only gameplay-functional ROM delta is the requested directional call target.

## Retained Build-0303 Architecture

The following were independently checked after Build-0304 generation:

- exact decoded 32-byte canonical pattern identities: active;
- graph-aware stable allocator: active;
- legal transition graph: 1,354 edges;
- deterministic transition tests: PASS;
- representative record 0/variant 0 -> record 1/variant 0 stable result: retained from Build 0303;
- staged Plane-A boundary remap: active (`fg_boundary_name_remap_a` at Genesis-WRAM
  `0x00FFB1E0`);
- staged Plane-B boundary remap: active (`fg_boundary_name_remap_b` at Genesis-WRAM
  `0x00FFB1E4`);
- pattern-index mask: `0x07FF`;
- attribute-preservation mask: `0xF800`;
- full Plane-A and Plane-B boundary recommit: active;
- post-reseed install helper: `fg_boundary_install_post_reseed` at `runtime_genesis_pc 0x072632`;
- per-frame mark-live, plane scan, hash residency, allocation, LRU, eviction, package selection, and
  miss-triggered loading: absent.

The compiler regenerated 23 records and 170 packages with the same 1,402,544-byte package payload,
960/960 maximum slot use, 22 intentionally dropping Plane-B packages, and stable transition tests
passing.

## Collision Non-Changes

This task did not modify:

- `collision_map_lookup_53a2e` or any collision consumer;
- Genesis-WRAM collision-ring representation corresponding to arcade WRAM `0x0010DE00`;
- collision classifications;
- terrain tables;
- player/world collision state;
- any collision source or generated collision data.

The A/B question remains strictly whether restoring the Build-0302 directional family restores
early Stage-1 movement/collision.

## Build and Validation

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0304.bin`
- SHA-256: `adeea49a86611ec6b58cfdc1bfe85b76ed3bf75e1761417b9cb8bf6e3284bce7`
- size: 3,022,520 bytes
- counter: 303 -> 304
- rolling/numbered equality: PASS, identical SHA-256 and size
- canonical gate: PASS
- patcher: 69 shift replacements, expected one-entry reduction from removal of the Build-0303
  equal-size redirect
- mandatory MAME trace:
  `states/traces/rastan_direct_video_test_build_0304_mame_30s_20260822_090504/`
- MAME frames: 1,798
- MAME average speed: 463.49%
- unique unmapped memory addresses: none
- final MAME PC: `runtime_genesis_pc 0x073940`
- additional builds: none

The smoke trace remained outside gameplay. It proves boot/frontend stability and absence of a new
unmapped-address failure, not the requested early Stage-1 collision result.

## Required User Test

Test early Stage 1 first:

1. start Stage 1;
2. walk right through the beginning where Build 0303 encountered the false wall;
3. report whether Rastan can move normally and whether collision corresponds to visible terrain;
4. secondarily note whether Build 0303's stable-slot/name-table coherence improvement remains.

Do not extend this test to deferred later-game observations for the Build-0304 decision.

Interpretation:

- if early collision is restored, the Build-0303 native directional replacement is isolated as the
  regression cause;
- if early collision is not restored, that replacement is rejected as the sole cause and the
  remaining Build-0302-to-0303 deltas must be isolated separately.

## Files Changed for Build 0304

- `specs/rastan_direct_remap.json`: removed only the Build-0303 `arcade_pc 0x05109C` gameplay
  directional redirect;
- generated objects, map, manifests, disassembly, ROM, trace, and counter from the normal build;
- `docs/design/Cody_build_0304_directional_regression_isolation.md`;
- `AGENTS_LOG.md`.

Preexisting unrelated dirty-tree changes and every numbered ROM were preserved.

## Ledger Impact

- KNOWN_FINDINGS: unchanged pending the authoritative user A/B result.
- OPEN_ISSUES: no new issue and none closed.
- CLOSED_ISSUES: unchanged.

