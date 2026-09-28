# Cody — Build 0366 cave-block collision and palette

## Result and acceptance boundary

Build 0366 restores the original player/special-solid record consumer to relocated Genesis work
RAM and assigns the destructible Stage-1 cave block to the already-resident Layer-A muddy-ground
palette with an offline Palette Composer reindex of only its four cells. The canonical gate,
GENESIS NTSC gameplay-entry gate, PC090OJ palette-selection equivalence proof, decompilation guard,
and C syntax check pass. The automated runs do not reach and interact with the cave block or the
Segment-5 rope, so collision behavior, destruction lifetime, final color appearance, and rope
non-regression remain **USER MUST VERIFY in BlastEm**.

Baseline: user-accepted Build 0365. Produced build: 0366. Counter transition: 365 -> 366.

Canonical ROM:

- Path: `dist/rastan-direct/rastan_direct_video_test_build_0366.bin`
- SHA-256: `d975695da68e9fa2092b90052a94f1fb440c928015530b7e7ba2613500f662e2`
- Size: 1,719,992 bytes

Same-number variants, all 1,719,992 bytes:

| Artifact | SHA-256 |
|---|---|
| `_d` | `f6165fc4f71e59f3d309913f9816ba399294feda5a81e86717bda5f8b77c8128` |
| `_s` | `ace8e1f356fe5d4c6f31ecba4752c20970ece0a0ab4f47f3ac3702d207c3fd52` |
| `_do` | `c8c1330788ebdd2548ae1b5350631753a273ecb765e3fbb71733ec933efd97b7` |
| `_c` | `3f3c68f167b8119c6d90697b4fc2a763789495f9ee04fe74b1e52f62b136edb4` |

## A. Arcade identity and handler

The object is the A5+0x02C8 actor slot (`actor_2c8`) created through the retained parameterized
actor constructor at arcade `0x45248`. The Stage-1 route seeds target character `H`, base graphics
`0x0179`, mode `+0x03=1`, and live state `+0x05=0x1E`. Its captured native composite is four
PC090OJ cells `0x0179..0x017C`. The already-working sword/destruction path changes the actor to its
destruction state (captured as `0x0F`) and eventually retires it; Build 0366 does not change that
path, actor record, animation, or renderer.

## B. Original solid-collision semantic

The ORIGINAL ARCADE frame order is player update `0x5100A`, actor update, then collision manager
`0x449B4`. This is not a PC090OJ-object-RAM collision and it does not inject a fake map cell.

For mode actors, internal path `0x44548` indexes the target-character table at `0x44582`. Character
`H` (`0x48 - 0x43 = 5`) selects rectangle index `0x52` (82). Index 82 in the signed-byte table at
`0x44CE0` is:

| Edge | Actor-relative coordinate |
|---|---:|
| left | -20 |
| right | +20 |
| top | -16 |
| bottom | +16 |

After the original overlap test, `0x444F8` accepts actor states `0x15`, `0x17`, `0x1B`, `0x1C`, and
`0x1E`. It writes one 12-byte record at A5+0x0242:

| Offset | Meaning |
|---|---|
| +0 | active = 1 |
| +2 | live actor state |
| +4 | live actor X |
| +6 | live actor Y |
| +8 | signed left/right bytes |
| +10 | signed top/bottom bytes |

The player path at `0x54BF8..0x54DA8` consumes that record and preserves the original
state-dependent top/side response, prior-extents deltas, side selection, and response fields at
A5+0x1312..0x1320. Therefore the original actor position—not a fixed screen coordinate—owns the
solid geometry.

## C. First Genesis divergence

The collision producer remained live and wrote its correct record through A5-relative addressing
to Genesis WRAM `0x00FF0242`. The retained consumer at arcade PC `0x054BF8`, however, still began:

```asm
lea 0x0010C242,a0
```

`0x0010C242` is cartridge ROM in the Genesis address model, so the player read ROM instead of the
record the collision manager had just emitted. This explains the split user result: the later,
independent sword/damage passes still hit and destroy the block, while Rastan's body never sees the
special-solid record.

The current generated address map proves:

- arcade PC `0x054BF8..0x054BFE`
- runtime Genesis PC `0x054C92..0x054C98`
- kind `patched_site`, origin `opcode_replace`
- original `41F90010C242`
- replacement `41F900FF0242`

The final postpatch disassembly at runtime `0x054C92` is `lea 0xff0242,%a0`.

## D. Minimal collision fix and solidity lifetime

Build 0366 rebases only that absolute LEA operand to Genesis WRAM:

```asm
lea 0x00FF0242,a0
```

All original producer, overlap, top/side response, player state, velocity/position response,
sword damage, destruction state, and retirement control flow remain in charge. No new helper,
block-specific collision routine, hard-coded world coordinate, SAT-derived collision, global fake
collision layer, PC090OJ shadow, NOP, or RTS bypass was added.

The collision manager clears A5+0x0242 before its scan and rewrites it only while a qualifying live
actor overlaps the player. The cave block's normal live state `0x1E` qualifies; captured destruction
state `0x0F` does not. Thus the original transition removes solidity immediately when the actor
leaves the qualifying live state, and retirement cannot leave a ghost record. Final timing remains
subject to the user's interactive BlastEm test.

## E. Palette ownership and index compatibility

Affected registry decision: `PAL-PC090OJ-STAGE1-CAVE-BLOCK-001` (`decided`; visual acceptance
pending).

The frozen Palette Composer profile and live source agree that gameplay CRAM Line 3 is the shared
Layer-A master palette. In the Stage-1 context, the muddy Layer-A ground mappings use Line-3 entries
1..5:

`0x028C, 0x044C, 0x0026, 0x0004, 0x0002`.

The cave block emits palette nibble C, effective PC090OJ bank `0x3C`. The ROUND-1 indirect palette
load is `0x3BA88[12]=35`, selecting pool row `0x50162`. Cells `0x0179..0x017C` use raw nonzero pixel
indices `{1,7,8,9,12,13,14}`; those meanings are not compatible with the already-authored Layer-A
ground entries.

Only `usage:cave_block:bank0x3C` was added to the Palette Editing Tool profile. Palette Composer
CIEDE2000 matching was constrained to the established five ground entries (rather than creating a
new line or using the unrelated blue/teal entries). The authored offline map is:

| Cave source index | Shared Line-3 ground index |
|---:|---:|
| 1 | 5 |
| 7 | 2 |
| 8 | 1 |
| 9 | 3 |
| 12 | 3 |
| 13 | 3 |
| 14 | 1 |

`gen_reindexed_pc090oj.py` applies this map only to cells `0x0179..0x017C`. The native route selects
Line 3 for bank `0x3C`; it does not rewrite CRAM. Line 3 stays resident under Layer-A ownership, so
Layer A is undisturbed and no unrelated sprite palette is overwritten. The generated manifest
records four cave-cell entries, and the exhaustive palette-selection verifier reports 512 mapping
cases plus 16,777,216 SAT word-2 cases with zero mismatches.

## F. Architecture boundary

Collision semantic cut: retained live actor and original collision manager -> A5+0x0242 special
solid record in native Genesis WRAM -> retained player collision response. The stale arcade absolute
address was the only missing address contract.

Graphics semantic cut remains the established actor/mapping decision -> native Genesis queue/SAT.
The obsolete PC090OJ record-writing/readback tail remains retired. Build 0366 removes no additional
shared PC090OJ producer; it adds only an offline cave-cell reindex and direct palette-line decision.
No rope visual/contact/animation source was changed.

## G. Files changed

Production inputs and tooling:

- `specs/rastan_direct_remap.json`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- `apps/rastan-direct/src/palette_hooks.s`
- `tools/graphics_editor/gen_reindexed_pc090oj.py`
- `analysis/graphics_optimizer/editor_policy/Test.json`
- `build/rastan-direct/build0314/Test.snapshot.json`
- `specs/palette_decisions.json`

Decompilation/evidence:

- `analysis/decompilation/c/raw/00044548.c`
- `analysis/decompilation/c/raw/00054bf8.c`
- `analysis/decompilation/c/rastan_player_solid_object.c`
- `analysis/decompilation/c/function_coverage.csv`
- `analysis/decompilation/c/historical_claim_audit.csv`
- `analysis/decompilation/c/README.md`
- this report and `AGENTS_LOG.md`

Generated outputs include the canonical address map/manifest/disassembly, reindexed PC090OJ asset
and manifest, palette-equivalence report, numbered ROMs, and trace evidence.

## H. Validation

Static/build validation:

- `check_actor_decompilation_coverage.py`: PASS (90 rows; guard PASS).
- all semantic/raw decompilation C with `gcc -std=c11 -fsyntax-only`: PASS.
- JSON syntax for remap, palette registry, and both Palette Composer profiles: PASS.
- PC090OJ offline generator: four cave cells reindexed; profile SHA-256
  `09399d34478e9836e862de814cd820feff4a24e9fe37a8808d4b0e797b7193e0`.
- palette LUT verifier: 512 mapping cases, 16,777,216 SAT word-2 cases, zero mismatches.
- canonical patch manifest: 228 opcode-replace sites.
- address-map coverage: 1,719,992 bytes, no gaps or overlaps.
- canonical gate: PASS.
- same-number canonical/`_d`/`_s`/`_do`/`_c` artifact-set check: PASS.
- known Phase-1 seven-epoch gate: FAIL; artifact preserved, unchanged acceptance limitation.

Runtime validation:

- GENESIS NTSC MAME gameplay-entry gate: PASS, 240 post-entry frames, zero address errors, bus
  errors, illegal instructions, or crash-handler entries. Evidence:
  `states/traces/build0366_gameplay_entry_gate_20260922_155350/`.
- GENESIS NTSC MAME standard trace: 1,798 frames completed. It does not reach the cave block or
  Segment-5 rope. Evidence:
  `states/traces/rastan_direct_video_test_build_0366_mame_30s_20260922_155353/`.
- ORIGINAL ARCADE semantic proof used the canonical ROM/disassembly and existing captured actor/
  compositor evidence; no new runtime harness was necessary.

Existing project tools reused: canonical Ghidra exports and maincpu disassembly, current address
map/manifest pipeline, Palette Editing Tool/Palette Composer profile and generator, Makefile gates,
and established GENESIS NTSC MAME gameplay-entry/30-second trace harnesses.

New tooling created: none.

Why new tooling was necessary: not applicable.

## I. USER MUST VERIFY — BlastEm

1. Segment-5 rope still renders correctly in both directions, can be grabbed, carries Rastan, and
   permits jump/release.
2. Before destruction, land on and stand on the cave block without sinking or falling through;
   approach its sides/bottom and compare response with the arcade; scroll while touching it and
   confirm the surface stays aligned with the visible block.
3. Destroy it with the sword using the accepted hit count/timing and confirm its destruction
   animation remains normal.
4. After the destruction transition, pass through the former block position and confirm there is
   no ghost platform.
5. Confirm the block uses the same muddy/brown colors as adjacent Layer-A ground and that no other
   plane or sprite palette is corrupted.
6. Confirm no `D00462` freeze and no new exception.

STOP status: Build 0366 is complete and testable; behavioral/visual acceptance is pending Tighe's
BlastEm validation.

