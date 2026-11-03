# Cody — Native Graphics Task 1: Rastan Player-Compositor Pilot

## Result

Build 0403 implements a mixed native/retained pilot at the dedicated Rastan
primary-body compositor, original arcade PC `0x054492`. It does not use or
modify `native_stage_dispatch_41dae`.

The generated native table covers all 75 primary-body selectors with weapon
selector 0 (none), 1 (sword), 2 (axe), or 3 (hammer), in both compositor
orientations: 600 native keys. The 150 fire-sword keys remain explicit
`UNRESOLVED` entries and execute the accepted Build-0400 compositor because
fire-sword codes `0x046E`, `0x046F`, `0x047B`, and `0x047C` are dynamically
substituted from `A5+0x1308`.

## PLAYER-KU results

### PLAYER-KU-1 — selector contract

`0x054326` remains the semantic owner of `A5+0x1244` (primary body and weapon
frame) and `A5+0x1246` (secondary/legs frame). It derives them from the retained
player mode, animation, death, and attack state. The Task-1 native key uses the
already-selected `A5+0x1244`, `A5+0x12FA` weapon selector, and the orientation
predicate `A5+0x1114 == 2` versus `!= 2`. The original mode-9/orientation-3
decrement is applied before the key lookup. `A5+0x1246` and `0x0546A8` remain
retained.

### PLAYER-KU-2 — body frame source

The primary table is rooted at `0x05BD40`. Each selector is a signed relative
offset to up to four six-byte descriptors: `u16 code, s8 x, s8 y, u16 attr`.
A zero code is sticky blank because the original loop does not advance the
descriptor pointer after zero. Piece order, signed geometry, `Y+1`, descriptor
attribute, horizontal-flip attribute, and mirrored `X=-x-16` are baked.

### PLAYER-KU-3 — weapon composition

Weapon overlays are independent tables selected by `A5+0x12FA`: sword
`0x05CD8A`, fire sword `0x05D068`, axe `0x05D346`, and hammer `0x05D666`.
Native frames concatenate primary body pieces and then the selected static
weapon pieces, exactly preserving compositor order. The first weapon piece
publishes the masked `A5+0x129A/0x129C` anchor. No weapon or a blank weapon
frame clears that anchor. Fire sword is retained because of its dynamic code
substitution.

### PLAYER-KU-4 — pattern identity

Every body/sword/axe/hammer code in the pilot is non-divergent in
`pc090oj_variant_index.json`. Therefore its finalized editor pattern identity
is invariant and equals the source code. The generator fails if any covered
code enters a divergent group. Dynamic SAT attributes remain separate from
pattern identity. Fire sword is not guessed or baked.

### PLAYER-KU-5 — lane order

The native primary frame emits to `NATIVE_LANE_PLAYER_BODY`. The separate
FRONT producers continue to select `NATIVE_LANE_PLAYER_FRONT`, and the retained
secondary compositor subsequently appends to BODY. Existing lane concatenation
still determines SAT priority; FRONT and BODY were not collapsed.

## Frozen key and binary formats

Key:

`((effective_body_selector * 5 + weapon_selector) * 2 + orientation)`

- `effective_body_selector`: 0..74 after the proven mode-9 decrement
- `weapon_selector`: 0..4
- orientation 0: `A5+0x1114 == 2`; orientation 1: `A5+0x1114 != 2`

Index entries are six-byte big-endian records: `u32 table_offset, u8
piece_count, u8 status`. `UNRESOLVED` is `FFFFFFFF FF 00`; native status is 1.

Frame pieces are ten-byte big-endian records: `s16 dx, s16 dy, u16
finalized_vi, u16 attr, u8 size, u8 flags`. Size 5 is the fixed 16x16 Genesis
sprite shape. Flag bit 0 identifies the weapon anchor piece.

The residency file starts with `P9RS`, version 1, and 750 records. Each record
provides the offset/count/min/max for a sorted finalized-vi set. This is future
Phase-B input; Task 1 continues to use the current accepted O(1) residency
reverse index through `native_sprite_emit`.

## Control flow and fallback

The shift replacement at `0x054492` calls `native_player_frame_try`. A native
hit emits the complete primary-body/static-weapon frame and returns from
`0x054492`. An explicit `UNRESOLVED` result calls the existing
`native_player_body_begin` and falls through to the unchanged Build-0400
per-piece compositor and `native_player_piece` hooks. This preserves the
dedicated player fallback and upstream gameplay ownership.

## Generated outputs and verification

- `build/pc090oj_frame_table.bin`: 18,220 bytes, 398 deduplicated payloads
- `build/pc090oj_frame_index.bin`: 4,500 bytes, 600 native / 150 UNRESOLVED
- `build/pc090oj_frame_residency.bin`: 12,708 bytes
- `build/pc090oj_frame_table.report.txt`
- `build/pc090oj_frame_table.coverage.json`

Layer 1, unchanged `verify_reindexed_pc090oj.py`: PASS; 916 requirements,
zero mismatches, zero incomplete mappings, and all 344 Rastan base codes
retained correctly.

Layer 2, independent `verify_pc090oj_frame_table.py`: PASS; independently
redecoded all 600 native entries, both orientations, piece order, geometry,
attributes, size, finalized identity, anchor flag, and residency sets; verified
all 150 fire-sword entries as explicit `UNRESOLVED`.

The normal Build-0403 gameplay-entry gate reached controllable gameplay with
address errors 0, bus errors 0, illegal instructions 0, and crash-handler
entries 0. The normal 30-second MAME trace reported no unmapped address. The
canonical ROM gate passed. The pre-existing seven-epoch target gate produced
its usual warning after its target-epoch proof passed; no tilemap/epoch code was
changed.

No separate cycle trace was added. Structural performance improvement is
bounded and direct: each covered frame replaces two retained four-iteration
descriptor loops, table traversal, per-piece orientation arithmetic, and
per-piece hook dispatch with one index lookup and one compact native loop.
Whole-game performance remains a later phase.

## Files changed

- `tools/translation/precompute_pc090oj_frame_table.py`
- `tools/translation/verify_pc090oj_frame_table.py`
- `apps/rastan-direct/Makefile`
- `apps/rastan-direct/src/pc090oj_assets.s`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `specs/rastan_direct_remap.json`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- this report and `AGENTS_LOG.md`

Build 0402 was preserved as a consumed canonical-gate failure after only one of
the paired ROM-size invariants had been updated. Build 0403 synchronized both
invariants and is the candidate family. Canonical SHA-256:
`cd2e8f273c92ff3e0e7a9218fae8a8b007f6a91707cc774ed067b5e048a1cf76`.
Tighe visual/gameplay acceptance is required before Phase B.
