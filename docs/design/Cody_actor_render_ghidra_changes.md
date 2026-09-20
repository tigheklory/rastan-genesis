# Cody Actor Renderer Ghidra Change List

The live project `tools/ghidra/rastan_project/rastan_arcade_ref.gpr` was used as the canonical starting point but was not modified. Apply the following changes in Ghidra; this file is the truthful handoff, not a claim that the project database already contains them.

## Proposed symbols and types

### `0x03D054`

- old symbol: `actor_family0_render_3d054`
- new proposed symbol: `actor_record_to_pc090oj_sat_dispatch_3d054`
- type/signature: `void func(ActorRecord *A4, SATEntry *A1, uint8 anim_D0, uint8 mirror_D6, uint8 facing_D7, uint16 budget_D2)`
- semantic meaning: dispatch actor `+0x38` to one of five compositor pointer tables, resolve `anim*2`, then enter `0x3C902`
- callers/xrefs: `0x41DD2`, `0x41E0C`, `0x41E60`, `0x41E9E`, `0x45E28`, `0x45E64`, `0x45E9E`
- evidence: machine code `0x3D05A..0x3D098`; exact MAME program pointers in verified JSON
- confidence: high

### `0x03C902`

- old symbol: none/incomplete compositor label
- new proposed symbol: `pc090oj_compositor_program_dispatch_3c902`
- type/signature: `void func(const uint8 *A0, SATEntry *A1, ActorRecord *A4, uint16 budget_D2, uint8 mirror_D6, uint8 facing_D7)`
- semantic meaning: dispatch special coordinate modes or expand four-byte general piece records to PC090OJ SAT
- callers/xrefs: tail-called by the five table wrappers
- evidence: `0x3C902..0x3CA34`; eight exact SAT matches
- confidence: high

### `0x03C9E8`

- old symbol: none
- new proposed symbol: `apply_actor_palette_attr_if_enabled_3c9e8`
- type/signature: helper using `ActorRecord+0x27`
- semantic meaning: if bit 6 of `+0x27` is set, replace word0 low byte with `+0x27`
- callers/xrefs: general compositor branches `0x3C97E`, `0x3C9BE`
- evidence: instruction sequence and exact emitted word0 values
- confidence: high

### `0x03CA00`

- old symbol: none
- new proposed symbol: `read_compositor_control_3ca00`
- type/signature: `uint8 func(const uint8 **A0, bool *terminated_D5, uint8 *mode_D3)`
- semantic meaning: read control byte, extract high-nibble mode, set terminator state on `0xFF`
- callers/xrefs: both general piece loops
- evidence: machine code
- confidence: high

### `0x03CA12`

- old symbol: none
- new proposed symbol: `emit_compositor_tile_word_3ca12`
- type/signature: helper using base `ActorRecord+0x1E` and local negate flag
- semantic meaning: add or subtract unsigned program tile delta from base and write SAT word2
- callers/xrefs: both general piece loops
- evidence: machine code; exact tile sequences
- confidence: high

### `0x04A086`

- old symbol: `FUN_0004a086`
- new proposed symbol: `decode_spawn_record_into_actor_slot_4a086`
- type/signature: `void func(const SpawnRecord *A0, ActorRecord *A4)`
- semantic meaning: copy class/family, split spawn byte2 into compositor `+0x38` and parallel variant `(0x752,A4)`, copy byte3 to `+0x36`
- callers/xrefs: field schedule/spawn path
- evidence: `0x4A086..0x4A0A0`
- confidence: high

### `0x04543E`

- old symbol: `actor_record_loader_4543e`
- new proposed symbol: `load_actor_record_type_entry_4543e`
- type/signature: `void func(ActorRecord *A4)`
- semantic meaning: index eight-byte table `0x45592` by `(actor+0x06)-8`
- callers/xrefs: paired/special/boss record creation paths
- evidence: `0x4543E..0x4548E`; table decode; boss captures
- confidence: high

### `0x04544E`

- old symbol: `FUN_0004544e`
- new proposed symbol: `load_actor_family_variant_entry_4544e`
- type/signature: `void func(ActorRecord *A4)`
- semantic meaning: select ordinary/boss base record by family, compositor, and parallel variant; initialize base `+0x1E` and current frame `+0x01`
- callers/xrefs: ordinary actor activation path
- evidence: `0x4544E..0x454B8`, tables `0x454BA/0x454D2/0x454EA/0x45502/0x45562`
- confidence: high

### `0x045684`

- old symbol: `FUN_00045684`
- new proposed symbol: `assign_actor_palette_attribute_45684`
- type/signature: `void func(ActorRecord *A4, GlobalState *A5)`
- semantic meaning: assign `+0x27` from ordinary family table `0x45722/0x4576A` or boss table `0x456EC`; set bit 6
- callers/xrefs: actor initialization
- evidence: machine code and palette/SAT captures
- confidence: high

### `0x03BA20` / `0x03BA56` / `0x03BA64`

- old symbol: `FUN_0003ba20` / `FUN_0003ba56` / `FUN_0003ba64`
- new proposed symbol: `load_round_palette_banks_3ba20` / `load_palette_pool_block_3ba56` / `convert_0rgb_to_xbgr555_3ba64`
- type/signature: scene-table loader, one-pool-block loader, and `void convert(const uint16 *A3, uint16 *A0, uint32 count_D3)`
- semantic meaning: select `0x4FD02` pool blocks through the round row at `0x3BA88`, double each 0RGB nibble, and rearrange to arcade xBGR-555; PC090OJ displays sprite bank `0x30 | (SAT word0 & 0x0F)`
- callers/xrefs: `0x45D96` and palette initialization/copy paths
- evidence: machine code `0x3BA20..0x3BA86`; eight same-frame live palette-RAM banks exactly equal transformed ROM blocks
- confidence: high

### `0x041DAE`

- old symbol: `FUN_00041dae`
- new proposed symbol: `render_normal_actor_blocks_to_pc090oj_41dae`
- type/signature: `void func(GlobalState *A5)`
- semantic meaning: iterate actor blocks directly and allocate fixed SAT budgets
- callers/xrefs: frame renderer `0x41F58`
- evidence: `A4` block LEAs and `0x3D054` calls
- confidence: high

### `0x045DFA`

- old symbol: `FUN_00045dfa`
- new proposed symbol: `render_boss_mode_actor_blocks_to_pc090oj_45dfa`
- type/signature: `void func(GlobalState *A5)`
- semantic meaning: alternate block/SAT allocation when `A5+0x2A2 == 2`; consumes actor slots directly
- callers/xrefs: frame renderer `0x41F54`
- evidence: disassembly and both boss MAME samples
- confidence: high

### `0x0423B2`

- old symbol: none/subfunction inside actor state machine
- new proposed symbol: `create_round5_boss_type17_children_423b2`
- type/signature: `void func(GlobalState *A5, ActorRecord *owner_A4)`
- semantic meaning: create five `A5+0x5C8` records with compositor 1 and record type 17, then load table `0x45592` -> base `0x0988`
- callers/xrefs: type-16 state transition at `0x42376`; later recreation at `0x46C98`
- evidence: `0x423B2..0x423F2`, type table, Round-5 capture
- confidence: high

### `0x0457D0`

- old symbol: none
- new proposed symbol: `create_round1_boss_type15_components_457d0`
- type/signature: `void func(ActorRecord *A4, GlobalState *A5)`
- semantic meaning: initialize compositor 1 / record type 15 and load base `0x061D`
- callers/xrefs: `0x457B2` loop and actor state path `0x42214`
- evidence: machine code and type table
- confidence: high

### `0x046BE0`

- old symbol: none/incomplete function boundary
- new proposed symbol: `boss_type14_type16_update_dispatch_46be0`
- type/signature: `void func(ActorRecord *A4, GlobalState *A5)`
- semantic meaning: shared update state machine for record types 14/16; round 1 calls `0x4CE6C`, round 5 calls `0x4E13C`; type-specific animation/child behavior follows at `0x46C98..0x46F1E`
- callers/xrefs: actor state dispatch from `0x4221A`
- evidence: round comparisons, type comparisons, `+0x01` writers, child creator call
- confidence: medium-high

## Proposed table labels

| Address | Proposed label | Type | Confidence |
|---:|---|---|---|
| `0x3D09E` | `compositor0_program_offsets` | `int16[256]`-like offset table | high |
| `0x4771C` | `compositor1_program_offsets` | offset table | high |
| `0x3F0CE` | `compositor2_program_offsets` | offset table | high |
| `0x40004` | `compositor3_program_offsets` | offset table | high |
| `0x4002C` | `compositor4_program_offsets` | offset table | high |
| `0x45502` | `ordinary_actor_base_records_variant0` | eight-byte base records | high |
| `0x45562` | `ordinary_actor_base_records_variant_nonzero` | eight-byte base records | high |
| `0x45592` | `special_actor_record_type_entries` | eight-byte records indexed by type-8 | high |
| `0x456EC` | `boss_palette_attribute_table` | byte table indexed by variant/round/compositor adjustment | high |
| `0x45722` | `ordinary_palette_attr_table_primary` | 12 bytes per round | high |
| `0x4576A` | `ordinary_palette_attr_table_alternate` | 12 bytes per round | high |

## Proposed structures

### `ActorRecord` (size `0x40`)

Type only the fields listed in the verification report. Leave unproven gaps as byte arrays. Do not include the parallel `A4+0x752` byte in this structure.

### `SpawnRecord`

At minimum type the first four bytes separately: class, family, packed variant/compositor, and state byte. Do not name byte 3 “animation.”

### `BaseVariantRecord` / `RecordTypeEntry` (size 8)

Use separate typedef names even if their layouts currently match. Proven fields include base graphics word at `+0`, a byte copied to actor `+0x3A` at `+2`, initial current-frame byte at `+3`, and words copied to actor `+0x28/+0x2C` at `+4/+6`.

### `SATEntry` (size 8)

`word0 attributes`, `word1 Y`, `word2 code`, `word3 X`.

### Parallel variant storage

Model `(0x752,A4)` as a parallel per-slot byte relation, not an `ActorRecord` field. A comment/data overlay is safer than a false oversized struct.
