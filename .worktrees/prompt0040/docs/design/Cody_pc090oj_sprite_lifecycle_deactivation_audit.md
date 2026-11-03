# Cody - PC090OJ Sprite Activation/Deactivation Producer Audit

**Date:** 2026-07-03  
**Type:** Evidence audit only  
**Build baseline:** Build 0135, `dist/rastan-direct/rastan_direct_video_test_build_0135.bin`  
**Build 0135 SHA256:** `8e00be424f9afefe79d199640096bf99de7b53c4ba49e83ad32b2b491990844e`  
**Evidence directory:** `states/traces/pc090oj_sprite_lifecycle_deactivation_audit_20260703_113605/`

## Phase 0

**Relevant priors:**

- `RULES.md`, `ARCHITECTURE.md`, `AGENTS.md`, latest `AGENTS_LOG.md` tail.
- `KNOWN_FINDINGS.md`: KF-026 (PC090OJ runtime write surface not fully statically enumerable), KF-032 (raw PC080SN/PC090OJ writes must route through staging/mirror paths), KF-010/KF-011 context.
- `OPEN_ISSUES.md`: OPEN-001 (graphics output), OPEN-024 (PC090OJ sprite subsystem incomplete/garbage), OPEN-018 raw write context.
- `docs/design/Cody_build0135_remaining_display_off_budget_and_pc090oj_scan_depth_analysis.md`.
- `docs/design/Cody_build0135_display_on_timing_reorder.md`.
- `docs/design/Cody_build0133_hv_vcounter_display_on_diagnostic.md`.
- `docs/design/Cody_pc090oj_persistent_sprite_tile_dma_cache_build0132.md`.
- `docs/design/Andy_build0132_residency_cache_static_review.md`.
- `docs/design/Cody_pc080sn_vram_ownership_relocation_implementation.md`.
- Prior PC090OJ producer/object-RAM-faithful reports found under `docs/design/` and prior trace scripts under `states/traces/`.

**High-rediscovery hazards:** KF-026, KF-032, OPEN-024, Build 0132 residency cache correctness, Build 0135 scan-depth finding. None contradicted.

**Task classification:** EXTENDING, evidence audit for OPEN-001 / OPEN-024.

**Contradiction detected:** NO.

**Build 0135 baseline:** Build 0135 is the current production baseline for this audit. It includes the display-on reorder and the PC090OJ residency cache, but still has the remaining horizontal band/slit.

**PC090OJ scan-depth result:** Build 0135 complete scan samples decode all 256 PC090OJ entries every completed frame, while emitting only 19..32 Genesis SAT sprites with dropped=0. Highest meaningful sampled source index is 45, but nonzero object records reach index 239; a hard cap is not proven safe.

**Genesis 80-SAT output cap:** The Genesis output cap remains 80 SAT entries. The PC090OJ input semantics remain the full 256 object records.

**Candidate-bitset hypothesis:** A derived 256-bit helper bitset may avoid blindly scanning all 256 records, provided it is maintained from all PC090OJ mirror write surfaces and never allows false negatives. False positives are acceptable.

**address_map.json loaded:** YES. `build/rastan-direct/address_map.json` was used for opcode-replacement site mapping in `static_inventory.json` / `static_inventory.md`.

**arithmetic offset used as proof:** NO. For opcode replacement sites, mappings are derived from `address_map.json` segments. Genesis helper symbols are labeled `genesis_only` and are not assigned arcade PCs.

**STOP conditions acknowledged:** YES. No implementation, no source/spec/tool/Makefile/ROM/build changes, no bookmark, no diagnostic ROM, no scan-depth cap, no PC080SN or scene changes.

## Evidence Artifacts

- `states/traces/pc090oj_sprite_lifecycle_deactivation_audit_20260703_113605/static_inventory.md`
- `states/traces/pc090oj_sprite_lifecycle_deactivation_audit_20260703_113605/static_inventory.json`
- `states/traces/pc090oj_sprite_lifecycle_deactivation_audit_20260703_113605/arcade/capture_arcade_pc090oj_lifecycle_frame_done.lua`
- `states/traces/pc090oj_sprite_lifecycle_deactivation_audit_20260703_113605/arcade/arcade_pc090oj_lifecycle_writes.log`
- `states/traces/pc090oj_sprite_lifecycle_deactivation_audit_20260703_113605/arcade/frame_*_pc090oj_d00000_0800.bin`
- `states/traces/pc090oj_sprite_lifecycle_deactivation_audit_20260703_113605/arcade/frame_*_pc090oj_entries.csv`
- `states/traces/pc090oj_sprite_lifecycle_deactivation_audit_20260703_113605/arcade_lifecycle_reduction.md`
- `states/traces/pc090oj_sprite_lifecycle_deactivation_audit_20260703_113605/arcade_lifecycle_reduction.json`

Runtime trace limitation: the original-arcade CPU program-space write tap did not fire for PC090OJ device writes in this MAME run, even though frame dumps prove object RAM changed from boot to title state. Therefore the arcade runtime artifacts support record-state/class transitions, but not writer-PC attribution. Writer-PC attribution below comes from static disassembly and `address_map.json` / remap entries.

## Q1 - Current Genesis PC090OJ Write Paths

### Summary

Current Genesis PC090OJ mirror updates are centralized enough that a future candidate bitset has plausible hook points. The important distinction is between full-record helpers, partial raw-mirror helpers, and block fills.

| Path | Source | Runtime Genesis PC | Arcade PC | Width | Fields | Record index available? | Candidate suitability |
|---|---|---:|---:|---|---|---|---|
| `.Lpc090oj_emit_slot` | `pc090oj_hooks.s:94-125` | internal helper | Genesis-only helper | 4 words / record | word0/status, Y, tile/code, X | YES, explicit `%d0` slot | Excellent set point. Clear only after full-record inactive evaluation. |
| `.Lpc090oj_clear_slot` | `pc090oj_hooks.s:227-237` | internal helper | Genesis-only helper | record | word0=0, Y=`0x0180`, code=0, X=0 | YES, explicit `%d0` slot | Excellent clear/deactivation point. |
| `.Lpc090oj_mirror_write_word_a1_d0` | `pc090oj_hooks.s:239-258` | internal helper | Genesis-only helper | word | one of word0/Y/code/X via `A1` offset | YES, `(A1 - HW_ADDRESS 0x00D00000) >> 3` | Excellent set/dirty point. Clear only by evaluating the complete current record. |
| `.Lpc090oj_mirror_write_byte_a1_d0` | `pc090oj_hooks.s:260-279` | internal helper | Genesis-only helper | byte | partial byte of Y/code/status depending `A1` | YES, `(A1 - HW_ADDRESS 0x00D00000) >> 3` | Set/dirty only. Do not clear from byte alone. |
| `genesistan_hook_3ad44_dispatch`, PC090OJ branch | `pc090oj_hooks.s:465-510` | `0x071B66` | patched site `arcade_pc 0x03AD44` maps to `runtime_genesis_pc 0x03AF44` | block long-fill | range of record words from `A0`, `D1`, `D0` | YES, start/range derivable from `A0` | Range set/dirty; range clear only after evaluating touched records. |
| `.Lvcs_mirror_scan` | `pc090oj_hooks.s:959-1079` | inside `vdp_commit_sprites` at `0x071FB4` | Genesis-only consumer | read-only scan | all 256 records | YES, `%d6` source index | This is the consumer that a candidate bitset would narrow. |

### Function-Level Producer Helpers

These helpers ultimately feed `.Lpc090oj_emit_slot`, `.Lpc090oj_clear_slot`, or raw mirror write helpers:

| Helper | Runtime Genesis PC | Patched arcade_pc / mapping | Producer behavior |
|---|---:|---:|---|
| `genesistan_pc090oj_hook_target_3b902` | `0x071A4E` | `arcade_pc 0x03B902` -> `runtime_genesis_pc 0x03BB02` | If `%d1==0`, clears slots 0..4; otherwise writes slots 0..4 with code=1 and Y from `%d1`. |
| `genesistan_pc090oj_hook_target_3b926` | `0x071A90` | `arcade_pc 0x03B926` -> `runtime_genesis_pc 0x03BB26` | Clears slots 5..13. |
| `genesistan_pc090oj_hook_target_3b930` | `0x071AA8` | `arcade_pc 0x03B930` -> `runtime_genesis_pc 0x03BB30` | Raw word-preserving writer: word0=0, Y byte, code byte, transformed X word. Record index comes from `A1`. |
| `genesistan_pc090oj_hook_target_41dae` | `0x071AE8` | `arcade_pc 0x041DAE` -> `runtime_genesis_pc 0x041FAE` | Emits slots 0..21 from work-RAM blocks. Original fallback writes Y=`0x0180` for inactive blocks. |
| `genesistan_pc090oj_hook_target_41f5e` | `0x071AF6` | `arcade_pc 0x041F5E` -> `runtime_genesis_pc 0x04215E` | Emits slots 0..21 from work-RAM blocks. Original fallback writes Y=`0x0180`. |
| `genesistan_pc090oj_hook_target_45dfa` | `0x071B04` | `arcade_pc 0x045DFA` -> `runtime_genesis_pc 0x045FFA` | Emits alternate 22-slot frame from work-RAM blocks. |
| `genesistan_pc090oj_hook_target_59f5e` | `0x071B12` | `arcade_pc 0x059F5E` -> `runtime_genesis_pc 0x05A15E` | Clears slots 0..7 and preserves related work-RAM tuple clears. |
| `genesistan_pc090oj_hook_init_priority_3ad84` | `0x071C52` | `arcade_pc 0x03AD84` -> `runtime_genesis_pc 0x03AF84` | Initializes slots 76..79 with code=0 priority ladder records. |
| `genesistan_pc090oj_hook_score_digit_3b802` | `0x071C88` | `arcade_pc 0x03B802` -> `runtime_genesis_pc 0x03BA02` | Partial byte/word score digit writes to PC090OJ mirror; activation is partial over multiple writes. |
| `genesistan_pc090oj_hook_slot_init_54052` | `0x071D74` | `arcade_pc 0x054052` -> `runtime_genesis_pc 0x054252` | Initializes slots 72..75 with code=0 records while preserving C-chip text RAM clears. |
| `genesistan_pc090oj_hook_sprite_update_54810` | `0x071E04` | `arcade_pc 0x054810` -> `runtime_genesis_pc 0x054A10` | Emits four sprites per call into slots 44..55. |
| `genesistan_pc090oj_hook_sprite_decay_5607c` | `0x071E66` | `arcade_pc 0x05607C` -> `runtime_genesis_pc 0x05627C` | Decrements Y for slots 56..63; when Y reaches `0x0010`, clears code to zero. |
| `genesistan_pc090oj_hook_copy_56114` | `0x071EDA` | `arcade_pc 0x056114` -> `runtime_genesis_pc 0x056314` | Copies descriptor list into slots 64..67 until sentinel `0xFFFF`. |
| `genesistan_pc090oj_hook_zero_fill_56440` | `0x071F1A` | `arcade_pc 0x056440` -> `runtime_genesis_pc 0x056640` | Clears slots 68..71. |
| `genesistan_pc090oj_hook_status_sprite_5a098` | `0x071F34` | `arcade_pc 0x05A098` -> `runtime_genesis_pc 0x05A298` | Emits status/UI sprites into slots 30..43. |

Classification: the current Genesis write surface can identify record indices at all known helper/mirror write points. That is enough for a future candidate bitset design, provided every path above is covered and no raw PC090OJ writes remain outside these helpers.

## Q2 - Arcade PC090OJ Object-RAM Deactivation Methods

### Observed / Proven Patterns

| Pattern | Writer arcade_pc evidence | Mapped Genesis site | Record/range | Before/after example | Classification |
|---|---:|---:|---|---|---|
| Code/tile zero or code-zero inactive record | `0x03AD44` bulk fills; `0x03B902` clear path via `0x03B930`; `0x03B926`; `0x05607C` when Y reaches `0x0010`; `0x056440`; `0x059F5E` | See Q1 mapped sites | many | Runtime title frame 60: entry 0 = `0000 0100 0000 0100`, class `code_zero`; entries 46.. also code-zero. | code/tile zero, inactive but record is nonzero |
| Y sentinel `0x0180` | static disassembly at `arcade_pc 0x041EB6`, `0x041ECA`, `0x041EDE`, `0x041EFC`, `0x041F8C`; helper clear uses Y=`0x0180` | `0x041DAE`, `0x041F5E`, `.Lpc090oj_clear_slot` users | multiple | Static fallback writes `movew #384,%a1@(2)` then advances by 8. | offscreen/sentinel Y deactivation |
| Whole/block clear | `arcade_pc 0x059F5E` uses `move.l #0` twice per record over eight records at `HW_ADDRESS 0x00D00048`; `arcade_pc 0x03AD44` long fill can clear/fill PC090OJ ranges. | `0x05A15E`, `0x03AF44` patched sites | ranges | Static: `0x59F68 clrl %d0`; `0x59F6A/0x59F6C movel %d0,%a0@+` repeated. | scene/global or block clear |
| Offscreen Y with nonzero code | Static `0x03B930` data-driven writes and runtime frame dumps | mapped through `0x03BB30` / raw helper | entries 9..21, 26..27 in title sample | Runtime frame 60: entry 9 = `0000 00F8 0037 0008`, class `offscreen_y`; entry 17 = `0000 01EC 002A 0000`, class `offscreen_y`. | offscreen Y deactivation/filtering |
| Overwrite/reuse | work-RAM block producers `0x041DAE`, `0x041F5E`, `0x045DFA`, ROM-table producer `0x054810`, copy producer `0x056114`, status producer `0x05A098` | Q1 mapped helper sites | fixed slot ranges | Producers rewrite full records each time they run. | overwrite/reuse |

### Runtime State Evidence

Original arcade no-input MAME frame dumps:

- Frame 1 boot: all 256 records are all-zero.
- Frame 60 title: all 256 records are nonzero, but only 42 have nonzero code and only 27 classify drawable. Counts: 27 `candidate_drawable`, 214 `code_zero`, 15 `offscreen_y`.
- Frames 60..420 remained stable in this no-input capture.

Important implication: the arcade does not require inactive records to be physically all-zero. A record can be nonzero and inactive because code is zero, Y is offscreen/sentinel, or another decode rule rejects it. Candidate clear logic must not use raw nonzero/zero as the activation truth.

### Capture Limitations

The MAME Lua write tap did not capture per-write writer PCs in this run. Coin/start, ROUND/start, gameplay/demo-like, and endround were not reached in this no-input arcade trace. Existing Build 0135 Genesis evidence covers coin/start sample windows, but not original arcade writer PCs for those states in this task.

## Q3 - Arcade Activation Methods

### Observed / Proven Patterns

| Pattern | Writer arcade_pc evidence | Mapped Genesis site | Record/range | Activation shape | Notes |
|---|---:|---:|---|---|---|
| Data-driven record construction with code byte/word | `arcade_pc 0x03B930` | `runtime_genesis_pc 0x03BB30`, helper `0x071AA8` | variable `A1` records | word0, Y, code, X are written sequentially; code is third word | Candidate must be set before or during partial construction, not only after final decode. |
| Work-RAM block full-record copy | `arcade_pc 0x041DAE`, `0x041F5E`, `0x045DFA` | helper `0x071AE8`, `0x071AF6`, `0x071B04` | slots 0..21 | full records emitted from work-RAM blocks | If source block starts inactive, fallback writes Y=`0x0180`. |
| Score/status partial writes | `arcade_pc 0x03B802`, `0x05A098` | helper `0x071C88`, `0x071F34` | score/status ranges | byte and word writes build/update records | Partial byte writes make tile-code-only candidate setting too narrow. |
| Copy/list producer | `arcade_pc 0x056114` | helper `0x071EDA` | slots 64..67 | copies records until `word0 == 0xFFFF` sentinel | Sentinel terminates producer, not necessarily all slots rewritten. |
| ROM-table sprite update | `arcade_pc 0x054810` | helper `0x071E04` | slots 44..55 | four records per call | X/Y depend on state offsets; existing active record can move onscreen/offscreen without a code change. |

Runtime activation example from original arcade frame dumps:

- Frame 1 -> frame 60 changed all 256 records.
- Entries 4..8 changed from all-zero to drawable title records, e.g. entry 4: `0000 0000 0000 0000` -> `0000 0000 003B 0088`.
- Entries 0..3 changed from all-zero to nonzero code-zero records, e.g. entry 0: `0000 0000 0000 0000` -> `0000 0100 0000 0100`.
- Entries 9..16 changed from all-zero to nonzero offscreen-Y records, e.g. entry 9: `0000 0000 0000 0000` -> `0000 00F8 0037 0008`.

Activation is partial over multiple writes for the raw mirror paths. Tile/code nonzero is a key drawable condition, but candidate tracking should set bits on any record write because X/Y/status can be written before code, and existing nonzero-code records can become drawable via X/Y changes.

## Q4 - Can A Candidate Bitset Be Maintained Safely?

A conservative 256-bit candidate bitset is feasible as helper-derived state, but only with broad set rules and cautious clear rules.

| Rule | Classification | Rationale |
|---|---|---|
| Rule A: set candidate bit on any write to a PC090OJ record | Too broad but safe | Covers full-record, word, byte, and block writes. No false negatives from partial activation. Initial/bulk fills may set many bits, but correctness is preserved. |
| Rule B: set candidate bit on any write to tile/code field | Too narrow / risks false negative | A record may already have nonzero code and later move onscreen via X/Y writes, or be partially written before code. This can miss candidates. |
| Rule C: set candidate bit on any write to X/Y/tile/status fields | Safe if all helper paths are covered | Equivalent to Rule A for the 8-byte PC090OJ record. Must include byte writes and block fills. |
| Rule D: clear candidate bit only on whole-record clear | Safe but too broad | Avoids false negatives, but leaves candidates for code-zero, Y-sentinel, or offscreen deactivations. Less performance gain. |
| Rule E: clear candidate bit when tile/code becomes 0 and current record evaluates inactive | Safe only if generalized to full-record inactive evaluation | Code-zero clear is safe after reading the complete record, but deactivation can also be Y=`0x0180` or offscreen. Future design should clear after complete decode says inactive, not from the field write alone. |
| Rule F: clear only during scene/global PC090OJ clear, never from per-field writes | Safe but too broad | Correctness-safe, but may retain too many false positives after ordinary per-record deactivation. |

Recommended safety rule for future design: set on any touched record; clear only when a complete current record is evaluated inactive by the same source-record decode predicates used by `.Lvcs_mirror_scan` (code zero, blank code, unmapped, offscreen/sentinel), or on a proven whole-range/global clear. Never clear from a partial byte/word write without reading the complete record.

False-positive risk: acceptable. Example: keeping offscreen/code-zero records as candidates costs extra evaluation but does not drop sprites.

False-negative risk: unacceptable. Rule B has this risk; any design that misses byte writes, block fills, or X/Y-only activation also has this risk.

## Q5 - Dirty Bitset Need

1. **Is candidate-only enough to reduce the 256 scan?** Yes, if candidates are allowed to clear after full-record inactive evaluation. If set-only candidate bits are never cleared, title initialization can set all 256 records and lose most of the benefit.
2. **Would a dirty bitset be needed to avoid evaluating unchanged candidates?** It would be useful for a second-stage optimization, but not required for a safe first design. Candidate-only still reduces source iteration once inactive records are cleared.
3. **Can dirty bits be maintained from the same write hooks?** Yes in principle: the same index derivation used for candidate bits can set per-record dirty bits on record/word/byte/block writes.
4. **Would dirty bits risk stale descriptors if missed?** Yes. A missed dirty bit could leave a stale descriptor/SAT record even though the mirror changed. This is a higher correctness risk than candidate-only.
5. **Should first implementation use only candidate bits, or candidate + dirty?** Candidate bits only. Dirty bits should wait until candidate lifecycle is proven in runtime evidence.

The current `staged_sprite_dirty` is per generated SAT block, not per PC090OJ source record. It does not replace a source-record dirty bitset.

## Q6 - Safe First Design Target

**Selected option:** Option A - Conservative candidate bitset only.

**Why:**

- It preserves full 256-record PC090OJ input semantics.
- It keeps the Genesis output cap at 80 SAT entries.
- It can be maintained at all known Genesis mirror write points because record indices are available.
- It accepts false positives, avoiding sprite drops.
- It defers dirty-bit complexity until candidate lifecycle correctness is proven.
- It avoids the unsafe hard cap / early-exit branch rejected by Build 0135 scan-depth evidence.

**Confidence:** Medium-high for design work. The static write surface is well centralized, but runtime write taps did not capture writer PCs in this task, and gameplay/endround original-arcade lifecycle coverage remains incomplete.

**Rejected options:**

- Option B, candidate + dirty: promising later, too risky as first change because missed dirty updates can stale descriptors.
- Option C, move full 256 scan before DISPLAY_OFF: still viable as a lower-risk timing design, but this audit specifically supports the candidate-bit branch as safe enough for design.
- Option D, hard scan cap/early exit: rejected; Build 0135 evidence proves nonzero records reach high indices and gameplay is not fully bounded.
- Option E, more evidence first: not selected. More evidence would improve confidence, but enough static lifecycle structure exists to start a design-only prompt with explicit safeguards and runtime proof gates.

## Q7 - Next Prompt

```text
[Andy - Design Only: Conservative PC090OJ Candidate Bitset]

Type: Design only. No implementation. No source/spec/tool/build/ROM changes.

Context:
Cody's PC090OJ sprite lifecycle/deactivation audit selected Option A: conservative candidate bitset only. Build 0135 still scans all 256 PC090OJ object records inside vdp_commit_sprites. Genesis output remains capped at 80 SAT sprites. Full 256-entry PC090OJ input semantics must be preserved.

Evidence to use:
- docs/design/Cody_pc090oj_sprite_lifecycle_deactivation_audit.md
- states/traces/pc090oj_sprite_lifecycle_deactivation_audit_20260703_113605/static_inventory.md
- states/traces/pc090oj_sprite_lifecycle_deactivation_audit_20260703_113605/arcade_lifecycle_reduction.md
- docs/design/Cody_build0135_remaining_display_off_budget_and_pc090oj_scan_depth_analysis.md
- apps/rastan-direct/src/pc090oj_hooks.s
- build/rastan-direct/address_map.json

Goal:
Design a production-safe 256-bit PC090OJ candidate bitset. One bit per PC090OJ object record. The mirror remains canonical. Candidate state is derived helper state only. False positives are allowed; false negatives are forbidden.

Required design decisions:
1. Exact WRAM storage layout for candidate bits, with no overlap.
2. All candidate set hook points:
   - .Lpc090oj_emit_slot
   - .Lpc090oj_clear_slot
   - .Lpc090oj_mirror_write_word_a1_d0
   - .Lpc090oj_mirror_write_byte_a1_d0
   - genesistan_hook_3ad44_dispatch PC090OJ block-fill branch
   - any boot/scene clear paths that initialize pc090oj_object_ram
3. Candidate clear rule:
   - clear only after complete current record is evaluated inactive by the same decode predicates as .Lvcs_mirror_scan, or on proven whole-record/global clear.
   - never clear from a partial byte/word write alone.
4. Modified mirror-scan iteration design:
   - iterate candidate bits, not all 256 entries.
   - preserve source_id as original PC090OJ record index.
   - preserve 80 SAT output cap and dropped-count semantics.
   - preserve blank/unmapped/offscreen/code-zero counters or define replacements.
5. Boot initialization and scene/global clear behavior.
6. Runtime proof gates to show no false negatives versus a full 256 scan in no-input, coin/start, story, ROUND/start, gameplay/demo if reachable.

Forbidden:
- no hard scan cap
- no early exit by index
- no dirty bitset in first design
- no PC080SN changes
- no SAT output cap change
- no source implementation in this task

Deliverable:
docs/design/Andy_pc090oj_candidate_bitset_design.md with a state-causality answer: what candidate state should exist, which writes create it, and why no sprite can be missed.
```

## Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-024. OPEN-018 context only.
- Closed issues touched: NONE.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: implementation, dirty bitset, hard scan cap, broader gameplay/endround runtime coverage, PC080SN work, visual sprite correctness beyond candidate lifecycle.

## KNOWN_FINDINGS Impact

Option A - no `KNOWN_FINDINGS.md` update. This audit selects a safe design branch but does not prove a new durable behavior mechanism beyond existing KF-026/KF-032/OPEN-024 context.

## STOP Status

STOP triggered: NO for the audit. Runtime writer-PC capture was limited because the MAME CPU program-space write tap did not fire for PC090OJ device writes; this limitation is recorded and does not block the conservative design recommendation.
