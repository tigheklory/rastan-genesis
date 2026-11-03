# Cody - Build 0168 Collision Map / Drowning Fix Candidate

**Date:** 2026-07-14
**Type:** Analysis-first implementation + verification
**Baseline:** Build 0166, `dist/rastan-direct/rastan_direct_video_test_build_0166.bin`, SHA `a74365146eef4fdf0e9b429d7e66d63186023e3541f36fc1fa9b2703eed62ff5`, counter `166`
**Corrected candidate:** Build 0168, `dist/rastan-direct/rastan_direct_video_test_build_0168.bin`, SHA `be2d575256ff72d942055c3477a31b0be4af1c863b9cf114f1c5f3bbd184d993`, counter `168`
**Scope:** Collision-map producer/read boundary for the early drowning/death transition. No death-handler bypass, no forced safe ground, no player-state patch, no D00298/Exodus/continue/game-over/VBlank/sprite-source work.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-010, KF-036, KF-039, KF-040, KF-041, KF-042, KF-044; OPEN-017 active; OPEN-001/OPEN-024 context. Prior design/evidence read: `docs/design/Andy_build0159_collision_producer_pipeline_owner.md`, `docs/design/Andy_build0159_tilemap_staging_collision_producer.md`, `docs/design/Andy_build0159_collision_producer_selection.md`, and `docs/design/Cody_build0167_death_drowning_transition_fix.md`.

Rediscovery-hazard findings touched: collision-map raw-WRAM / PC080SN side-effect chain. No contradiction of CONFIRMED/STRONG findings was found.

Architecture compliance: **CONFIRMED**. The fix restores an omitted arcade hardware side effect inside the existing Genesis helper/opcode-replacement path, then points copied arcade collision readers/converters at the mapped Genesis WRAM buffer. No second renderer, no Genesis-owned gameplay flow, no collision/death bypass.

## State Causality

1. At the collision reader, arcade-equivalent state should be a populated collision-map buffer at the mapped Genesis-WRAM equivalent of arcade work RAM `0x0010DE00`, namely `0x00FF1E00`.
2. The earlier PC080SN tilemap producer is responsible for creating that state as a side effect while it populates tilemap cells.
3. In Build 0166 the graphics staging path existed, but the PC080SN collision-map side effect was omitted and the collision reader still loaded raw `0x0010DE00`, so the reader consumed ROM garbage rather than a populated mapped collision map.

## Classification

**C - Producer omitted by PC080SN hook**, with a required coordinated reader/converter rebase.

The first proven divergence is that Build 0166 has no live writes to raw `0x0010DE00`, keeps mapped `0x00FF1E00` empty except startup clearing, and reads raw ROM bytes at runtime `0x053C64`. The mode-8 transition is then triggered by the faithful copied handler at runtime `0x05400C` after the raw collision value classifies as type `8`.

## Implementation

### Collision Side Effect

`apps/rastan-direct/src/tilemap_hooks.s` now defines `ARCADE_COLLISION_MAP_BASE = 0x00FF1E00` and extends `genesistan_stage_fg_src_column` to mirror the original PC080SN collision-map side effect while it stages the live gameplay FG source column.

For each staged cell, the hook:

- preserves the descriptor base in `%a3`;
- reads the descriptor collision word from `20(%a3,row*8+colidx*2)`;
- uses `34(%a3)` when the original descriptor sentinel at `32(%a3)` is `0x00FF`;
- computes the collision-map offset from the virtual FG C-window destination: `(a0 - 0x00C08000) >> 1`, masked to the `0x2000`-byte buffer;
- writes the collision word to `0x00FF1E00 + offset`.

### Collision Buffer Rebase

`specs/rastan_direct_remap.json` adds nine byte-neutral opcode replacements from raw arcade work RAM `0x0010DE00` to mapped Genesis WRAM `0x00FF1E00`:

- arcade `0x053A64`: reader `MOVEA.L #0x0010DE00,A0` -> `#0x00FF1E00`
- arcade `0x05A2CE`, `0x052882`: converter `ADDI.L #0x0010DE00,D0` -> `#0x00FF1E00`
- arcade `0x0559E4`, `0x055A5A`, `0x055A7A`: copied fallback producer address math -> `0x00FF1E00`
- arcade `0x05A336`: converter `SUBI.L #0x0010DE00,D0` -> `#0x00FF1E00`
- arcade `0x0412E8`, `0x045D52`: pointer compares -> `0x00FF1E00`

Canonical invariants are updated to `opcode_replace` count `151` and `total_genesis_bytes_covered = 0x182114`.

## Build Notes

A first numbered artifact, Build 0167, was mechanically produced but then superseded by validation: its mapped collision buffer stayed all zero, proving the first insertion point was inert. Build 0167 must not be treated as the accepted fix.

The corrected candidate is Build 0168:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0168.bin`
- SHA256: `be2d575256ff72d942055c3477a31b0be4af1c863b9cf114f1c5f3bbd184d993`
- Size: `1,581,332` bytes
- Counter: `168`
- Rolling ROM SHA matches Build 0168.
- Canonical gate: `GATE_PASS`
- Boot guard: PASS

Static generated-disassembly verification:

- runtime `0x053C64` now loads `#0x00FF1E00` into `%a0`.
- runtime `0x05400C` remains the faithful mode-8 writer and was not patched.
- generated hook code writes collision words to `0x00FF1E00 + offset` after the live FG source staging store.

## Runtime Validation

Trace directory: `states/traces/build0167_collision_map_fix_20260714_010228/`

Build 0166 control:

- Frames sampled: `901`
- Gameplay state at snapshots: `2/3/0`
- Raw `0x0010DE00`: `nonzero=4011`, `type8=72`, no raw writes
- Mapped `0x00FF1E00`: `nonzero=0`, `type8=0`
- Mode-8 event: frame `757`, reported PC `0x054012` after the write, exact writer instruction runtime `0x05400C`
- Boundary sample: `A0=0x0010F28A`, value `0x8888`, `value & 0x7F = 8`, player `X=0x0020`, `Y=0x0070`, `camY=0x0143`

Build 0168 corrected candidate:

- Frames sampled: `901`
- Gameplay state at snapshots: `2/3/0`
- Raw `0x0010DE00`: still ROM data, `nonzero=4011`, `type8=69`, no raw writes
- Mapped `0x00FF1E00`: populated, `nonzero=2016`, `type8=0`
- Mapped writes: `6112`, first write frame `12`
- Mode-8 events in the same scripted window: `0`

This proves the corrected candidate restores a populated mapped collision buffer and removes the early scripted mode-8 transition observed in Build 0166. It does not prove final real-hardware visual success; Tighe must verify the real Genesis/BlastEm lock and visible drowning behavior.

## Open / Closed Issues Impact

Open issues touched: OPEN-017; OPEN-001 and OPEN-024 context. New issues opened: NONE. Issues closed: NONE.

Deferred issues preserved: BG mostly mountains vs arcade mostly sky, missing ground tiles during fall, foreground palette, READY/header flicker, VBlank/rolling black bar, slowdown, input/down+attack, continue/game-over tiles, D00298 attract-demo issue, Exodus pre-gameplay loop, and suspicious PC090OJ records `132..134`.

Accepted build status: unchanged pending Tighe verification. Build 0168 is a corrected candidate, not an accepted baseline.

## KNOWN_FINDINGS Impact

Option A - no new finding indexed. The mechanism is an implementation of the already-recorded collision/PC080SN side-effect chain under OPEN-017/KF-040/KF-041/KF-042-style context.

## STOP

STOP triggered: **NO** for the corrected Build 0168 candidate.

Build 0167 note: Build 0167 is superseded by validation and should not be used as the fix artifact.
