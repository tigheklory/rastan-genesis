# Cody - R1/P1 Palette Authority and Oracle

Date: 2026-09-11

## Baseline

- Baseline: Build 0354 / counter 354.
- Task classification: EXTENDING / PROOF-FIRST / INFRASTRUCTURE.
- Production changes: NONE.
- Build 0355 consumed: NO.
- Best visual baseline Build 0353: unchanged.
- Diagnostic/performance baseline Build 0354: unchanged.

This report reconciles the current Round 1 Phase 1 (R1/P1) palette authorities,
defines a fail-closed legal sprite-palette domain, supplies an SAT word-2 parity
oracle for the resolved subset, and separates the historical OPT-003 question
from a newly proven linked-WRAM ownership defect. It does not promote a palette
mapping, modify runtime code, or authorize Build 0355.

## Phase 0

The mandatory governance, architecture, issue ledgers, current palette registry,
Build 0353/0354 evidence, OPT-003 history, native sprite source, graphics-editor
tools, symbols, and generated address data were inspected.

Relevant prior findings include KF-043, KF-046, KF-064, KF-066, KF-068, and
KF-069. OPEN-006 remains the principal palette issue; OPEN-026 and OPEN-027 are
related visual/composite context but are not palette authorities. No closed issue
was reopened. No CONFIRMED or STRONG finding was contradicted. The palette
registry contains several references to `KF-1214`, but no `KF-1214` heading exists
in the current `KNOWN_FINDINGS.md`; those references therefore do not independently
establish authority.

## Evidence Inspected

Primary inputs:

- `specs/palette_decisions.json`
- `apps/rastan-direct/src/palette_hooks.s`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/fg_tile_cache.s`
- `apps/rastan-direct/src/crash_handler.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/rastan-direct/address_map.json`
- `analysis/graphics_optimizer/editor_policy/Test.json`
- `analysis/graphics_optimizer/round1_phase1_whole_game_lexicon/sprite_class_coverage.json`
- `analysis/graphics_optimizer/round1_phase1_whole_game_lexicon/sprite_families.json`
- `tools/graphics_editor/gen_reindexed_pc090oj.py`
- `tools/graphics_editor/export_palette_policy.py`
- Build 0279 corrected human capture and the reports cited by the registry
- Build 0353/0354 and OPT-003 reports cited in the generated evidence

Generated proof artifacts:

- `analysis/graphics_optimizer/r1p1_palette_authority_oracle/palette_authority_reconciliation.json`
- `analysis/graphics_optimizer/r1p1_palette_authority_oracle/legal_sprite_palette_domain.json`
- `analysis/graphics_optimizer/r1p1_palette_authority_oracle/minimum_lookup_key.json`
- `analysis/graphics_optimizer/r1p1_palette_authority_oracle/pixel_reindex_profile_audit.json`
- `analysis/graphics_optimizer/r1p1_palette_authority_oracle/sat_word2_parity.json`
- `analysis/graphics_optimizer/r1p1_palette_authority_oracle/opt003_relocation_root_cause.json`
- `analysis/graphics_optimizer/r1p1_palette_authority_oracle/relocation_invariant_results.json`

## 1. Palette Authority Reconciliation

### Authority rule

`specs/palette_decisions.json` is the sole decision registry, but a registry entry
is not proof that current runtime source implements it. Conversely, the Build 0325
frozen-Test route table records a diagnostic/editor realization and does not become
canonical simply because natural gameplay currently executes it. Accepted arcade
semantics and Tighe-accepted decisions control; discrepancies remain visible.

The live path is static-source proven: emitted entries save a source nibble in
`pc090oj_sat_nibble`; VBlank commit calls `.Lnative_pal_fixup`; the fixup combines
the nibble with `pc090oj_sprite_ctrl_shadow`, calls `.Lnative_palsel`, and that
routine linearly scans `palette_route_table`. No new runtime capture was made.

### Reconciliation matrix

| Semantic class | Arcade identity | Nibble | Control | Effective bank | Registry result | Live route | Runtime-used result | Arcade/oracle evidence | Status | Confidence |
|---|---|---:|---:|---:|---|---:|---|---|---|---|
| Rastan player/sword | BODY plus melee-sword/nibble-3 pieces | `0x3` | `0x0060` | `0x33` | line 3, `proven` | line 0 | Static natural path selects line 0 | Original composer plus corrected Build 0279 capture support registry | CONTRADICTED | HIGH |
| Stage-1 Lizardman | family 0 classes 17/18 and related pieces | `0x6` | `0x0060` | `0x36` | line 0, `decided` | line 1 | Static natural path selects line 1 | Arcade bank proven; accepted Genesis compromise and corrected Build 0279 support registry | CONTRADICTED | HIGH |
| Large bat | actor `0x5C8`, base `0x03F6` | `0xE` | `0x0060` | `0x3E` | no accepted line, `provisional` | line 0 | Static natural path selects line 0 | Identity/bank provisional; color decision unresolved | TEST-ONLY | PROVISIONAL |
| Small bat | actor `0x748`, base `0x0268` | `0xE` | `0x0060` | `0x3E` | no accepted line, `provisional` | line 0 | Static natural path selects line 0 | Identity/bank provisional; color decision unresolved | TEST-ONLY | PROVISIONAL |
| Axe item | exact family/bank unresolved | unresolved | unresolved | unresolved | no line, `unknown` | none | no resolved route | Existing evidence proves presence, not palette identity | UNRESOLVED | UNKNOWN |
| Four-armed enemy | ordinary family, base `0x02E8` | `0xA` | `0x0060` | `0x3A` | no accepted line, `provisional` | line 1 | Static natural path selects line 1 | Effective bank supported; semantic name awaits final acceptance | TEST-ONLY | PROVISIONAL |
| Chimera | base `0x00D0` | `0x4` | `0x0060` | `0x34` | no accepted line, `provisional` | line 0 | Static natural path selects line 0 | Effective bank supported; line is frozen-Test only | TEST-ONLY | PROVISIONAL |
| Valkyrie | base `0x0241` | `0x2` | `0x0060` | `0x32` | no accepted line, `provisional` | line 0 | Static natural path selects line 0 | Effective bank supported; identity marked USER VERIFY | TEST-ONLY | PROVISIONAL |
| Flying Demon | special actor `0x508`, base `0x0129` | `0x5` | `0x0060` | `0x35` | no accepted line, `provisional` | line 1 | Static natural path selects line 1 | Effective emitted bank supported; line is frozen-Test only | TEST-ONLY | PROVISIONAL |

Machine-readable classification counts are: accepted/canonical 0,
contradicted 2, test-only 6, unresolved 1, provisional 0, and not-reachable 0.
The zero accepted count means no inspected registry row currently agrees with a
live R1/P1 route; it does not revoke the two accepted registry decisions.

### Provenance timeline and acceptance

- Rastan/sword: the registry decision is grounded in the corrected Build 0279
  human capture and original composer work. It is marked `proven`. Build 0334
  removed the prior hardcoded bank-`0x33` line-3 override so that the frozen-Test
  route table, authored for reindexed Test art, became the live source authority
  and selected line 0. That later source change was a Test-profile realization;
  this audit found no evidence that it superseded the accepted registry decision.
- Stage-1 Lizardman: the registry records the Build 0208/KF-066 line-0 carrier
  compromise and corrected Build 0279 evidence as an intentional `decided`
  Genesis mapping. Build 0325's frozen-Test ownership assigned bank `0x36` to
  line 1; Build 0336 then removed the older line-0 carrier/reassert path. The
  source timeline explains the live result but does not establish a new accepted
  decision.
- Large bat and small bat: their registry entries are `provisional`; the effective
  bank is candidate evidence and no Genesis line is accepted. Build 0325/Test
  assigns bank `0x3E` to line 0. The user already identified a prior blue/cyan bat
  rendering as non-authoritative, so that line/profile cannot be promoted from
  appearance or convenience.
- Four-armed enemy, Chimera, Valkyrie, and Flying Demon: registry entries are
  `provisional`. Their effective banks are supported by the current semantic
  corpus, but the live lines originate in the frozen-Test table. Semantic names
  that are marked USER VERIFY remain provisional; no inspected evidence records
  Tighe acceptance of these line assignments as canonical.
- Axe: the registry is `unknown`; no effective bank, profile, or line has been
  proven. It has no corresponding live route to reconcile.

No row is classified from inference alone, and runtime trace absence is not used
to downgrade legal reachability.

### Proven facts

- The canonical Rastan/sword decision is effective bank `0x33` to line 3.
- The canonical Stage-1 Lizardman decision is an intentional Genesis decision:
  effective bank `0x36` to line 0.
- Current source routes those banks to lines 0 and 1 respectively.
- The other six concrete enemy routes are explicitly described in source as the
  frozen-Test line ownership and lack accepted registry lines.
- Axe has no proven effective bank or line.
- The arcade R1 palette source is selected through the round-specific index table
  at arcade ROM/data `0x03BA88` into the source pool at `0x04FD02`; direct bank
  indexing is not the model.

### Interpretation

Current natural gameplay can execute a route that differs from accepted registry
semantics. That establishes a discrepancy, not which visible result Tighe prefers.
No registry or route change is authorized here.

### Requires Tighe decision

- Whether the accepted Rastan/sword and Lizardman registry decisions remain the
  intended Build 0355 targets despite the frozen-Test source configuration.
- Which, if any, frozen-Test candidate profiles/lines for bats, four-armed enemy,
  Chimera, Valkyrie, and Flying Demon should be promoted after visual/arcade proof.
- Axe remains evidence-blocked rather than a visual-choice-only case.

## 2. Full Legal R1/P1 Sprite-Palette Domain

The legal domain is derived from static object/spawn/composer coverage, not trace
frequency. Runtime observations annotate the rows but do not remove unobserved
legal cases.

| ID | Semantic class | Resolution | Palette authority |
|---:|---|---|---|
| 0 | `rastan_player_body` | resolved | Rastan/sword decision, bank `0x33`, line 3 |
| 1 | `stage1_lizardman` | resolved | Lizardman decision, bank `0x36`, line 0 |
| 2 | `collision_marker40_route` | unresolved, static-only | UNRESOLVED |
| 3 | `collision_marker41_route` | unresolved, static-only | UNRESOLVED |
| 4 | `family0_class70_actor` | unresolved semantic identity | bank `0x30`; line unresolved |
| 5 | `family2_round1_actor_cluster` | unresolved semantic identity | bank `0x36`; line unresolved |
| 6 | `collision_marker49_special_route` | unresolved, static-only | UNRESOLVED |
| 7 | `collision_marker4f_behavior20_route` | unresolved, static-only | UNRESOLVED |
| 8 | `record08_family2_class30` | unresolved, static-only | UNRESOLVED |
| 9 | `record09_family1_class57` | unresolved, static-only | UNRESOLVED |
| 10 | `record0a_family1_classb6` | unresolved, static-only | UNRESOLVED |
| 11 | `record0b_family1_classb9` | unresolved, static-only | UNRESOLVED |
| 12 | `record0c_family1_classbc` | unresolved, static-only | UNRESOLVED |
| 13 | `hurry_up_bat` | unresolved | bank/line unresolved |
| 14 | `normal_small_bat` | unresolved | bank/line unresolved |
| 15 | `large_bat` | unresolved | candidate bank `0x3E`; line unresolved |
| 16 | `four_armed_enemy` | unresolved | candidate bank `0x3A`; line unresolved |
| 17 | `axe_item` | unresolved | bank/line unresolved |
| 18 | `player_auxiliary` | resolved | Rastan/sword decision, bank `0x33`, line 3 |
| 19 | `other_item_drop` | unresolved | UNRESOLVED |
| 20 | `projectile_weapon` | unresolved | UNRESOLVED |
| 21 | `transient_effect` | unresolved | UNRESOLVED |
| 22 | `gameplay_hud` | unresolved in canonical registry | semantic force exists; canonical decision absent |
| 23 | `hostile_base004b_compositor0` | resolved | Lizardman decision, bank `0x36`, line 0 |
| 24 | `hostile_base0179_compositor0` | unresolved | bank `0x30`; line unresolved |
| 25 | `hostile_base0a5a_compositor2` | unresolved | bank `0x36`; line unresolved |
| 26 | `hostile_base0a73_compositor2` | unresolved | bank `0x36`; line unresolved |

Counts:

- Total legal semantic cases: 27.
- Resolved canonical cases: 4.
- Unresolved cases: 23.
- Statically legal but not observed in the inspected traces: 9 (IDs 2, 3, 6,
  7, 8, 9, 10, 11, and 12).

Every unresolved field uses the literal `UNRESOLVED` sentinel in generated data.
An unresolved row cannot contribute a guessed colored sprite, accepted SAT oracle
answer, palette-line feasibility claim, or Build 0355 implementation entry.

## 3. Minimum Lookup Key

### Result

Arcade code alone is insufficient. Proven code collisions include:

- codes `0x004F..0x0054` and `0x0063..0x0066`: `stage1_lizardman` versus
  `hostile_base004b_compositor0`;
- code `0x0179`: `family0_class70_actor` versus
  `hostile_base0179_compositor0`;
- code `0x0276`: `player_auxiliary` versus `hurry_up_bat`.

`(code, source bank)`, `(code, effective bank)`, semantic piece plus bank, and
semantic piece plus control-state cannot be proven complete while 23 legal cases
retain unresolved identities/banks/profiles. Control state contributes to effective
bank derivation but does not identify the producer.

### Recommended generated representation

Use the active graphics context/epoch to select a compact bank, then use a generated
semantic piece ID as the row index. Each static row carries:

- pixel-reindex profile ID;
- Genesis palette bits;
- priority only if semantically static;
- Palette Decision ID.

The emitter supplies genuinely dynamic pattern slot, H flip, V flip, and priority
when priority is not static. Semantic producer/class/control-state analysis belongs
in the offline compiler that creates the ID and bank; it must not be repeated by
the 68000 hot path.

This is the smallest representation supported for the four resolved rows. Domain
completeness remains INCOMPLETE, so it is not yet a complete Build 0355 lookup key.

## 4. Pixel Reindex Profiles

The frozen Test editor profile has 10 usage mappings and 9 distinct candidate
`(line,index_map)` signatures. They are candidate authoring evidence, not canonical
profiles. Two Rastan captures share an empty/delta-E profile, while another Rastan
usage has a different explicit profile. This proves the tooling has represented
multiple candidate profiles for one source family; it does not prove that canonical
R1/P1 requires both.

Canonical distinct R1/P1 profile count: UNRESOLVED.

Required relationship classification:

| Semantic scope | Same source/reindex/line | Same source/reindex/different line | Same source/different reindex/same line | Same source/different reindex/different line |
|---|---|---|---|---|
| Rastan BODY and player auxiliary | canonical profile unresolved | not proven | frozen-Test candidates show multiple Rastan profiles on Test line 0 only; not canonical | not proven |
| Lizardman and base-`0x004B` hostile compositor | canonical profile unresolved | not proven | not proven | not proven |
| Remaining 23 legal cases | UNRESOLVED | UNRESOLVED | UNRESOLVED | UNRESOLVED |

Thus no canonical R1/P1 row can yet be promoted into one of the four reindex
relationships. The table deliberately preserves unknown rather than treating the
current Test asset as canonical.

The current toolchain already supports:

- a usage-level palette line;
- a usage-level pixel index map;
- a context-policy container.

It only PARTLY supports the required future model. The production reindex generator
collapses output to one global mapping per arcade code and aborts on a conflicting
map. The promotion bridge supports only `context:gameplay.r01.p01`. Required future
explicit data are stable profile IDs, context/epoch-selected semantic-piece rows,
semantic-piece-to-profile/line relationships, context-specific transformed asset
variants, and Palette Decision IDs.

No whole-game invariant is inferred from R1/P1. The recommended bank format retains
the ability for the same source graphics to use a different reindex profile and/or
line in another context.

## 5. Forced-Line Semantics

The only inspected writer of `pc090oj_sat_force_line` initializes each emitted slot
to `0xFF` and changes it to line 3 when semantic tag bit 15 in the queued metadata
is set. `.Lnative_pal_fixup` is the only reader. The array index follows the emitted
SAT slot, but the deciding input is the semantic HUD tag, not physical placement.

Results:

- HUD forced-line behavior is semantic: YES.
- It can become a generated static palette attribute once the HUD row has a
  canonical palette decision.
- Other R1/P1 semantic force classes: none proven.
- True SAT-slot-dependent palette behavior: none proven.

The current SAT-indexed array is transitional transport and is not evidence that
the final architecture needs SAT-slot metadata.

## 6. SAT Word-2 Parity Oracle

`tools/graphics_optimizer/build_r1p1_palette_oracle.py` deterministically builds
the legal domain and compares the reference semantic answer with the proposed
static-record composition.

Composition under test:

`priority | palette_line | V-flip | H-flip | pattern_index`

The reference path independently models the Build 0354 operation: compose an
emitted word without palette bits, clear bits 14:13, and patch in the accepted
semantic line. The proposed path instead ORs dynamic pattern/H/V bits into a
pre-resolved static priority/palette attribute. The oracle holds accepted palette
bits and fixed priority static while enumerating dynamic pattern samples `0x000`,
`0x001`, `0x3FF`, and `0x7FF`, both H-flip states, and both V-flip states. It covers
all legal codes belonging to each resolved row.

Results:

- Resolved legal semantic cases tested: 4.
- Resolved combinations tested: 1,184.
- Mismatches: 0.
- First mismatch: none.
- Unresolved legal cases: 23, explicitly listed and not silently skipped.
- Resolved subset: PASS.
- Overall parity: INCOMPLETE.

The oracle intentionally compares against reconciled canonical semantic rows, not
against Build 0354's route table. It reuses the sound direct-map equivalence idea
from OPT-003 without adopting OPT-003's runtime implementation or provisional
palette answers.

## 7. OPT-003 Layout Regression

### What is disproven

The previous BSS-shift theory is CONFIRMED FALSE under the matched configuration:
138 BSS symbols were compared and none moved. OPT-003 added 512 generated bytes;
`pc090oj_native_emit_pass` and `fg_boundary_packages` shifted by 14 and 16 bytes,
respectively, while the package pointer was correctly relocated and all 49,732
package bytes remained identical.

No stale native ROM address-as-data operand or shift-table relocation omission has
been proven. Therefore this report does not invent such a site.

### Historical diagnostic defect

The old synthetic gate used invalid/synthetic state and arbitrary PC manipulation.
Its historical dense-LUT expression for code `0x034C` was:

`Genesis-WRAM 0x00FF6188 + 0x034C * 2 = 0x00FF6820`.

`Genesis-WRAM 0x00FF6820` is also fixed owner `CRASH_D3`. The claimed
`0x0420 -> 0x0000` event therefore sampled a multiply-owned address. No exact
writer was captured. A later matched, context-preserving safe call kept `0x0420`
stable for eight executing frames and passed package-5 and fixed-Plane-B maps.
The old gate cannot establish a natural-gameplay OPT-003 relocation failure.

### Current structural defect

The current linked symbol is:

- `fg_boundary_active_lut`: Genesis-WRAM `0x00FF619C`, 10,240 words.
- fixed crash record: Genesis-WRAM `0x00FF6800..0x00FF6863` inclusive.

The physical overlap corresponds to LUT codes `0x0332..0x0363`. Current source
diverts only codes `0x031A..0x034B`, leaving `0x034C..0x0363` overlapping and
needlessly diverting `0x031A..0x0331`. The manual interval became stale as linked
layout changed.

This proves failure to enforce disjoint ownership between linker-placed indexed
native data and fixed absolute WRAM owners. It does not prove the exact historical
OPT-003 runtime clobbering writer. That root cause remains UNRESOLVED.

### Correct structural boundary

- Place the complete legal indexed range outside fixed owners, or derive every
  exclusion from current linked/fixed ranges rather than copied constants.
- Run the ownership invariant before publication.
- Do not use ROM padding or a convenient generated-rodata address as a fix.

## 8. Relocation and Address-as-Data Invariant

`tools/translation/verify_native_wram_ownership.py` parses the linked symbol table,
computes the complete physical range of `fg_boundary_active_lut`, intersects it
with the fixed crash-record owner, translates overlap addresses back to LUT codes,
and compares that set with the configured diversion interval. It writes a
machine-readable result and exits nonzero when ownership is inconsistent.

It catches:

- physical overlap between the declared dense LUT and fixed crash-record range;
- missing diversion codes;
- stale diversion codes;
- layout drift that changes those sets.

It does not catch:

- arbitrary computed pointers;
- undocumented fixed owners;
- stale ROM code-pointer tables or arbitrary address-as-data sites;
- runtime ordering or a causative writer.

Result on current Build 0354 source: FAIL. Missing diversions are
`0x034C..0x0363`; stale diversions are `0x031A..0x0331`.

This is a focused pre-publication proof guard, not a claim that every relocation
class is now covered.

## 9. Palette Tool as Future Authority Interface

The editor model is useful but not yet sufficient as sole compiler input:

- Supported now: usage-scoped line, usage-scoped index map, R1/P1 context container.
- Implicit now: stable profile identity, semantic piece identity, decision linkage,
  and whether a mapping is canonical versus frozen-Test candidate data.
- Must become explicit: profile IDs, context/epoch bank selection, semantic rows,
  transformed-asset variants, status/sentinel, and Palette Decision ID.

`colors.json` and frozen Test outputs are not promoted to palette authority by this
audit. Unknown-bank artwork remains uncolored/fail-closed for canonical decisions
and feasibility.

## 10. Eventual Build 0355 Contract

Safe to implement next: NO.

Remaining blockers:

1. Resolve the two canonical/live contradictions, with Tighe's decision where the
   accepted visual target must be reaffirmed.
2. Resolve or explicitly defer all legal cases required by Build 0355 scope; 23 of
   27 currently fail closed.
3. Assign accepted pixel-reindex profile IDs to every in-scope resolved row.
4. Establish a complete compact semantic-piece ID at each native producer.
5. Correct the linked-WRAM ownership defect and require the guard to pass.
6. Keep the exact historical OPT-003 writer classified UNRESOLVED unless new
   evidence proves it; do not claim a relocation fix from the present evidence.

When those gates are closed, the bounded production contract is:

1. Offline compiler emits context/epoch-selected static sprite records keyed by
   compact semantic piece ID.
2. Native emitters combine static palette bits/profile-selected art with dynamic
   pattern slot, H/V flip, and any genuinely dynamic priority.
3. SAT word 2 is written final during emission.
4. The exhaustive oracle covers every legal row with zero unresolved cases and
   zero mismatches.
5. Only then retire normal-gameplay `.Lnative_pal_fixup`,
   `palette_route_lookup`, `pc090oj_sat_nibble`, and
   `pc090oj_sat_force_line` where xrefs prove them unnecessary.

Sprite pattern residency, Plane A, Plane B, scrolling, CRAM color animation, and
D00462 remain separate and outside that build contract.

## 11. Proven, Inferred, and Unsupported

### Proven

- Registry/live route disagreement for banks `0x33` and `0x36`.
- Six additional live enemy routes are frozen-Test values without accepted lines.
- The static legal domain has 27 cases; four have complete canonical answers.
- Code alone has semantic collisions.
- HUD force metadata carries a semantic tag through SAT-indexed storage.
- The resolved SAT word-2 subset passes 1,184 combinations with zero mismatches.
- Matched BSS did not shift in OPT-003.
- Current linked WRAM ownership overlaps and the manual diversion interval is stale.

### Inference / recommended design

- Context-selected banks of compact semantic-piece records are the smallest known
  architecture that preserves offline semantics and O(1) runtime lookup.
- SAT-slot force and post-emission palette fixup should be eliminable after complete
  semantic closure and xref proof.

### Unsupported / unresolved

- A complete canonical line/profile for 23 legal cases.
- A canonical requirement for multiple Rastan reindex profiles in R1/P1.
- A true SAT-slot-dependent palette rule.
- A stale ROM address-as-data operand causing OPT-003.
- The exact writer responsible for the historical claimed `0x0420 -> 0x0000` event.

## 12. Architecture and Ledger Impact

- Offline-generated palette/static-attribute banks remain the correct target: YES,
  WITH CONDITIONS (complete authority/domain/profile closure and passing guards).
- `.Lnative_pal_fixup` eliminable: YES, WITH CONDITIONS.
- Runtime palette search required in final architecture: NO proven R1/P1 case.
- Palette mapping remains separate from CRAM color animation: YES.
- Context-dependent sprite reindex/palette assignment remains supported: YES.
- Semantic cut retained: original arcade semantic sprite identity/context.
- Chip-specific tail replaced eventually: transitional nibble/force storage,
  route search, and SAT palette-bit patching only after parity proof.
- Transitional compatibility still present: the Build 0354 post-emission fixup path.
- OPEN-006: touched and refined; not closed.
- OPEN-026/OPEN-027: context only; unchanged.
- New issues: none.
- Closed issues: none.
- KNOWN_FINDINGS: no new entry indexed; the missing `KF-1214` references are noted
  as an evidence-quality problem rather than silently repaired.

## Verification

- `tools/graphics_optimizer/build_r1p1_palette_oracle.py`: PASS as a generator;
  reports overall parity INCOMPLETE by design.
- `tools/translation/verify_native_wram_ownership.py`: expected FAIL on current
  Build 0354 source due to the proven ownership mismatch.
- Generated JSON files: parse successfully.
- Python syntax checks: pass.
- Production source/spec: unchanged.
- ROM/build/counter: unchanged; counter 354; Build 0355 unconsumed.
- All numbered builds: preserved.
