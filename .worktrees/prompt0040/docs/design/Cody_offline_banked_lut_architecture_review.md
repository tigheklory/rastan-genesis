# Cody Offline Banked-LUT Architecture Review

## Scope and baseline

This is an independent architecture review of context-selected, Python-generated
lookup/data banks for the native Genesis realization of Rastan graphics. It makes
no production, specification, ROM, build, or counter change.

- Baseline: Build 0354, counter 354.
- Build 0355 is not consumed.
- Arcade semantic decisions remain authoritative.
- Runtime remains native Motorola 68000 assembly.
- Python may perform expensive semantic analysis, deduplication, capacity planning,
  bank formation, and verification offline.
- The final rendering path remains arcade semantic state to native Genesis VDP/SAT
  output. This proposal is not a software PC080SN/PC090OJ device or an address
  translation layer.

Evidence inspected includes the current native sprite and palette paths, current
Plane A boundary packages and fixed Plane B package, canonical palette decisions,
Round 1 Phase 1 graphics inventories, later-round sprite-family presence data,
the OPT-003 palette-LUT experiment and correction, and the independent Build 0354
physical beam-position audit.

## Executive conclusion

**DESIGN RECOMMENDATION:** Adopt generated, context-selected banks as the dominant
organization for mappings that are demonstrably invariant over a useful lifetime.
Do not adopt one monolithic Round/Phase bank that switches sprites, palettes,
Plane A, and Plane B together. The correct design is a small context descriptor
whose independently interned fields select subsystem banks. Each subsystem gets
the largest lifetime proven valid by arcade semantics and capacity constraints.

**PROVEN FACT:** Current data already exhibits different natural lifetimes:

- Round 1 Phase 1 Plane B is one fixed 854-pattern set.
- Round 1 Phase 1 Plane A cannot fit as one lossless or currently approved
  phase-wide set in its 676-pattern capacity and therefore uses coexistence banks.
- Sprite palette routing has a small direct-lookup domain, but its canonical
  decisions are not yet reconciled with the live route table.
- Sprite pattern residency still depends on a bounded dynamic 49-cell cache and
  a maximum 12-entry pattern-DMA worklist.

**STRONG INFERENCE:** A descriptor of independently reusable bank identities will
reduce repeated runtime semantic work while avoiding needless duplication. A
descriptor should not imply that every field changes at every Round, Phase, map,
or epoch boundary.

**UNKNOWN / NEEDS PROOF:** The complete legal sprite-pattern and palette domain is
not yet closed. The current Round 1 Phase 1 semantic inventory has 27 discovered
graphics-bearing families but only five resolved and 22 explicitly unresolved.
That incompleteness forbids a definitive phase-wide sprite bank plan or a
canonical colored mapping for every family.

## 1. Suitability of generated banks

**PROVEN FACT:** Build 0354 physical beam measurements show that runtime sprite
publication is the major current cost, and the palette-fixup/routing pass is its
dominant measured sub-cost. Representative measurements are:

| Case | Total lines | Plane A lines | Plane B lines | Sprite lines | Emitted SAT | Pattern DMA |
|---|---:|---:|---:|---:|---:|---:|
| Stationary, frame 546 | 54.451 | 1.439 | 0.092 | 50.303 | 28 | 0 |
| Horizontal, frame 778 | 93.109 | 1.422 | 0.094 | 88.959 | 46 | 0 |
| Vertical/jump, frame 1227 | 46.932 | 13.162 | 0.092 | 31.059 | 19 | 0 |
| Sprite-heavy, frame 881 | 118.289 | 1.422 | 0.092 | 114.139 | 51 | 10 entries / 1,280 bytes |
| Worst complete, frame 775 | 134.033 | 1.420 | 37.852 | 92.125 | 46 | 2 entries / 256 bytes |

The worst complete publisher was 65,408 dots, 134.033 physical lines, not a full
262-line frame. Pattern DMA is bounded to 12 entries / 1,536 bytes and is commonly
zero. The fixed 640-byte SAT DMA is about one line. Palette-fixup time correlates
with emitted entries at `r = 0.990215`; the sampled descriptive slope is about
989.56 dots, or 2.028 lines, per emitted SAT entry. These are measurements, not a
promise that replacing one lookup recovers the entire slope.

**PROVEN FACT:** The retired approximately 258-line estimate came from applying
`% 262` to an 8-bit NTSC V-counter sample. The counter byte is neither a physical
line number nor a monotonic elapsed-time value. MAME `beam_y`/`beam_x`, expanded
across physical wraps using 262 lines times 488 dots, is the authoritative timing
method.

**PROVEN FACT:** The first capture observed 1,123 publisher invocations over 1,800
external frames; 759 entries, 67.59%, began during active display. The second
stationary capture contains 237 gameplay publications. Therefore reducing hot-path
CPU work matters even though the worst complete publication does not consume a
whole physical frame.

**DESIGN RECOMMENDATION:** Use direct generated lookups where a complete semantic
key and stable output are proven. Pointer selection should happen at semantic
boundaries, not during every emitted cell or sprite. Keep genuinely dynamic SAT,
scroll, CRAM, and animation state dynamic.

The model is appropriate because:

- ROM is a favorable place for immutable mapping data.
- Current hot paths pay repeated decision/search costs that Python can resolve.
- A current pointer plus direct index is cheap on 68000.
- Immutable generated banks are easier to checksum and compare with an arcade
  oracle than general runtime policy.
- Independent bank reuse controls ROM growth.

The model is not universally appropriate because:

- capacity and coexistence force Plane A and likely sprite-pattern epochs;
- CRAM contents can change dynamically;
- X/Y, flips, links, size, and animation selection remain runtime facts;
- unresolved semantic domains must not be assigned arbitrary defaults;
- table relocation itself has already exposed a deterministic correctness risk.

## 2. Top-level organization

**DESIGN RECOMMENDATION:** Use a hierarchy such as:

```text
round/scene descriptor
    -> sprite graphics bank id/pointer
    -> sprite palette-map bank id/pointer
    -> CRAM state/program id/pointer
    -> Plane B bank id/pointer
    -> Plane A epoch schedule id/pointer

Plane A epoch descriptor, selected only at a proven boundary
    -> Plane A mapping pointer
    -> Plane A upload/package pointer
```

The top level should activate independently interned fields. It should not force a
Plane B reload when only Plane A changes, or a sprite-pattern reload when only CRAM
state changes.

**DESIGN RECOMMENDATION:** Multiple descriptors should point to identical ROM
banks. Python should hash canonical payloads and deduplicate them. It should also
compute the largest valid lifetime for each mapping from legal semantic reachability,
coexistence, transition overlap, hardware capacity, and fidelity constraints.

**UNKNOWN / NEEDS PROOF:** Round and Phase identifiers alone are not sufficient
proof of bank lifetime. They are useful semantic inputs, but the generated lifetime
may be whole game, several phases, one phase, or a smaller coexistence epoch.

## 3. Independent subsystem lifetimes

**DESIGN RECOMMENDATION:** The compiler should maximize each bank's lifetime
independently and allow exact payload reuse. This is a better responsibility split
than carrying generalized policy in 68000 code.

The compiler must be fail-closed. Its input domain is all legally reachable arcade
semantics, not only one trace. Runtime traces validate and enrich the static domain;
they do not replace it. Unresolved legal cases remain explicitly unresolved and are
included conservatively in capacity calculations.

## 4. Sprite graphics versus attributes

**PROVEN FACT:** Sprite graphics recur across rounds. The arcade family descriptor
table at arcade data `0x045502` contains 12 family bases. The static palette-nibble
table at arcade data `0x045722` contains six 12-entry rows. Graphics family and
palette selection are therefore structurally separate in original data.

**PROVEN FACT:** The family with graphics base `0x004B` is observed in Round 1
Phase 1 and later Round 2, 4, 5, and 6 contexts. Other graphics bases also recur
across the later-round presence inventory.

**PROVEN FACT:** The palette table is identical for most entries across its six
rows, but family index 7 changes from nibble `0x0F` to `0x02` in the fifth row.
This proves that the original data model permits a stable graphics family and a
context-dependent palette selection.

**UNKNOWN / NEEDS PROOF:** The current presence evidence labels graphics base
`0x043A` / family 7 as static-only/unobserved. Therefore the table difference proves
separate semantics and a legal context distinction, but does not prove that a
human-visible recurring family-7 instance uses both colors in observed gameplay.

**DESIGN RECOMMENDATION:** Intern sprite graphics maps separately from palette or
static-attribute maps. Two contexts should be able to share one graphics bank and
select different attribute/palette banks without duplicating graphics mappings.

## 5. Sprite LUT key and value

### Key

**PROVEN FACT:** Current native emission masks an arcade sprite code to 13 bits.
The offline sprite editor/reindex path is keyed by `(code, bank)` because identical
source codes can require bank-specific transformed art. Current runtime palette
selection additionally derives an effective bank from the record's low nibble and
the display-latched upper control bits.

**DESIGN RECOMMENDATION:** Do not allocate a naive dense
`8192 codes * 128 effective banks` Cartesian LUT. It would consume 2 MiB per context
even with a 16-bit value. Instead generate a compact legal semantic-piece ID or a
sparse/per-bank code map for every proven legal `(arcade_code, effective_bank)`
pair. Missing legal-but-unresolved pairs must map to an explicit invalid/unresolved
sentinel, not an arbitrary tile or palette.

The hot-path key should be either:

1. a compact semantic piece ID generated offline, preferred when producer analysis
   can assign it directly; or
2. `(arcade_code, effective_bank)` through a compact generated two-level map.

`sprite code` alone is insufficient for transformed art or palette semantics.

### Value

**DESIGN RECOMMENDATION:** Keep graphics and palette outputs independently
internable:

```text
sprite_graphics_entry: uint16
    Genesis resident pattern/cell identity, or 0xFFFF invalid

sprite_static_attr_entry: uint8 or uint16
    palette line and only other bits proven invariant for that semantic piece
```

A parallel graphics word plus compact attribute byte is preferable to a long entry
when the banks have different lifetimes. A precomposed SAT word-2 template is valid
only after every folded bit is proven static.

**PROVEN FACT:** These remain runtime values in the current contract:

- X and Y;
- horizontal and vertical flip from source state;
- SAT link;
- size/composition;
- animation-piece selection.

Priority is currently emitted as a constant in the inspected path, but should be
folded only after the semantic domain proves it invariant. Pattern residency may
also remain dynamic until the offline epoch feasibility work is complete.

## 6. Eliminating `.Lnative_pal_fixup`

**PROVEN FACT:** Native emission currently writes each SAT entry, records a source
palette nibble in `pc090oj_sat_nibble`, records an optional force-line byte in
`pc090oj_sat_force_line`, and later iterates every emitted SAT entry in
`.Lnative_pal_fixup`. That post-pass combines the display-latched control state and
nibble, applies the special effective-bank `0x30` rule, scans
`palette_route_table` through `palette_route_lookup`, applies fallback behavior,
and patches SAT word 2 palette bits.

**ANSWER: YES WITH CONDITIONS.** The result can be determined at emit time from a
generated direct palette-map bank plus any proven semantic override. The separate
post-pass can be removed from normal gameplay only after all of these conditions
are met:

1. The canonical palette registry and current runtime route table are reconciled.
2. The full legal key domain is statically enumerated and unresolved cases fail
   closed.
3. The `0x30` special rule and any legitimate fallback are represented by proven
   semantics rather than silently lost.
4. HUD/other force behavior is represented as a semantic class/tag in the lookup
   key or as a minimal explicit override.
5. The control state is latched at the same semantic time before emission.
6. Exhaustive tests prove SAT word-2 parity for all legal inputs, including dynamic
   flip/priority composition.
7. The deterministic OPT-003 layout/reflow regression is resolved before adding a
   production table.

**STRONG INFERENCE:** Removing the linear route scan and second emitted-entry pass
addresses the dominant measured sprite sub-cost. The exact recovered time is
unknown because the Build 0354 timing bracket includes surrounding per-entry work,
and the direct lookup itself is not free.

## 7. Palette terminology and architecture

Use three distinct terms:

1. **Palette mapping:** semantic identity/effective bank/context to Genesis CRAM
   line. This is a small generated attribute mapping.
2. **CRAM color state:** Genesis line to 16 color words, including legitimate
   runtime animation, fades, effects, and carrier ownership.
3. **Pixel reindex profile:** offline `(code, bank)` pixel transformation needed to
   realize arcade art under Genesis line constraints.

**DESIGN RECOMMENDATION:** Palette-line mapping should normally be folded into a
sprite or tile's static generated attributes, or fetched from a direct compact
palette-map bank at emission. CRAM state/program data belongs in the context
descriptor but remains independently switchable and may be dynamic.

Do not call all three a `palette LUT`; that obscures ownership and lifetime.

## 8. Palette-mapping stability and authority

**PROVEN FACT:** Current palette selection uses at least:

- source palette nibble;
- display-latched `pc090oj_sprite_ctrl_shadow` upper bits;
- scene/context;
- a semantic force tag currently stored per emitted entry.

The effective bank is therefore dynamic unless the producer/context proves the
control state invariant. The safe direct map is at least 128 entries per active
context when indexed by effective bank, with a semantic force class folded into
the context/key or retained as a small override.

**PROVEN FACT:** The generated OPT-003 payload demonstrates that the current live
logic can be represented by four 128-byte maps, 512 payload bytes total, with zero
mismatches over all 512 tested scene/effective-bank combinations. That proves
behavioral representability of the live implementation, not semantic correctness.

**PROVEN FACT:** The canonical registry and current route table disagree. The
registry records established Stage 1 mappings for Rastan/sword effective bank
`0x33` to line 3 and Lizardman effective bank `0x36` to line 0. The inspected live
route table maps `0x33` to line 0 and `0x36` to line 1, and also assigns routes to
families whose registry status remains provisional. Per project policy, this
discrepancy must be resolved before further palette implementation.

**UNKNOWN / NEEDS PROOF:** The project does not yet have one canonical output line
for every legal Round 1 Phase 1 sprite identity. Large bats, small bats, Axe, the
four-armed enemy, and other discovered classes include provisional or unknown
palette decisions. The semantic inventory also retains 22 unresolved
graphics-bearing families. One output per semantic identity for the entire phase
is therefore not proven.

## 9. Forced-line behavior

**PROVEN FACT:** `pc090oj_sat_force_line` is indexed by emitted SAT entry, but the
inspected producer sets it from a semantic HUD tag; it is not derived from physical
screen position or immutable SAT slot identity. The slot-indexed array is a
transitional way to carry metadata into the later fixup pass.

**DESIGN RECOMMENDATION:** Fold a proven semantic class such as HUD into the
generated attribute key/value. Retain a minimal runtime override only for a class
whose line genuinely changes after semantic emission. Do not encode physical SAT
slot as palette semantics.

## 10. Sprite pattern residency

**PROVEN FACT:** The current system has 49 resident 16x16 cells, corresponding to
196 Genesis 8x8 patterns and 6,272 bytes of sprite-pattern VRAM. It performs a
fully associative runtime resident lookup/allocation and builds a pattern-DMA
worklist bounded to 12 cells per publication.

**PROVEN FACT:** The currently resolved sprite subset already contains 95 exact
16x16 cells, or 380 Genesis 8x8 patterns, while 22 discovered graphics-bearing
families remain unresolved. Thus one phase-wide union cannot fit the 196-pattern
region even before unresolved families are added.

**UNKNOWN / NEEDS PROOF:** A 380-pattern union does not prove those cells coexist
in one frame. It does prove that one permanently resident union for the known
phase-wide subset is impossible at current capacity. The minimum legal residency
epoch count remains unknown until animation/composer pieces and coexistence for all
resolved and unresolved classes are closed.

**DESIGN RECOMMENDATION:** Keep the bounded dynamic residency mechanism for now;
pattern DMA is not the principal measured hotspot. Eventually let Python derive
minimal sprite residency epochs from legal spawn/state/animation coexistence, with
transition overlap and a fail-closed unresolved reserve. Do not replace working
bounded residency with speculative phase banks before that proof.

## 11. Layer B

**PROVEN FACT:** Round 1 Phase 1 Plane B has 854 exact patterns and fits its fixed
VRAM allocation. The current boundary package reports one Plane B epoch, no
variants, descriptors 0 through 55, zero ordinary drops, no per-publication Plane B
pattern DMA, and no ordinary runtime name remap. The fixed set is loaded once at
gameplay entry; its map/upload payload is 6,832 bytes.

**DESIGN RECOMMENDATION:** Treat current R1/P1 Plane B as a phase-static generated
bank and point the context descriptor to it. This subsystem is already close to the
proposed architecture.

**UNKNOWN / NEEDS PROOF:** Cross-round reuse should be discovered by hashing exact
pattern and mapping payloads after later phases are compiled. Current evidence does
not justify declaring one whole-game Plane B set or one unique set per phase.

## 12. Layer A capacity

**PROVEN FACT:** Current Round 1 Phase 1 figures are:

| Measure | Patterns | Difference from 676 capacity |
|---|---:|---:|
| Genesis Plane A capacity | 676 | 0 |
| Unique arcade codes in union | 1,316 | +640 |
| Exact physical patterns after exact duplicate collapse | 1,315 | +639 |
| Lossless H/V/HV-normalized equivalence classes | 1,246 | +570 |
| Current approved visual-consolidation identity universe | 1,300 | +624 |
| Largest current stable coexistence epoch | 639 | -37 |

The current approved consolidation removes 15 identities from the 1,315 exact
physical union. The 69 independently identified flip-equivalence savings and the
15 approved visual-consolidation savings have not yet been emitted as one combined
production universe. Even the optimistic independent subtraction,
`1,315 - 69 - 15 = 1,231`, remains 555 patterns over capacity.

**ANSWER: NO** for one R1/P1 phase-wide Plane A set under current capacity and
approved fidelity. Exact deduplication, lossless flip normalization, and existing
approved consolidation are nowhere close to the additional 555-pattern reduction
needed.

Reduction classifications:

- **Lossless:** exact byte duplicates; H/V/HV-equivalent patterns when the generated
  name-word flip bits preserve orientation; cross-segment identical payload reuse.
- **Already visually accepted:** the 47 source identities consolidated to 35
  targets in the current policy, covering 283 cells, including the documented
  waterfall/noise treatment. This is not mathematically lossless.
- **Potentially lossy / requires Tighe approval:** any broader near-match,
  animation-frame removal, texture collapse, or art substitution not already in
  the canonical policy and visually accepted.

**DESIGN RECOMMENDATION:** Do not spend quality to force one bank. Continue using
compiler-generated coexistence banks unless a future lossless method changes the
capacity arithmetic materially.

## 13. Layer A fallback and minimum banks

**PROVEN FACT:** The current compiler emits five stable banks and two transition
packages for records 0 through 15. Stable exact/approved counts are 282, 333, 639,
583, and 639. Transition counts are 394 and 478. The package binary, including
fixed Plane B data, is 47,268 bytes.

**PROVEN FACT:** Capacity-only contiguous segmentation has a minimum of four stable
groups, with candidate segmentations:

```text
[0..3], [4..10], [11..12], [13..15]
[0..4], [5..10], [11..12], [13..15]
```

**UNKNOWN / NEEDS PROOF:** Four stable groups are not yet a proven production
minimum because transition overlap, visible continuity, exact record activation,
and package survival must also pass. Capacity arithmetic alone cannot eliminate
the current transition packages.

**DESIGN RECOMMENDATION:** Let Python minimize banks under capacity plus transition
and visibility constraints. The current defensible configuration is five stable
banks plus two transition packages. Four stable banks are a valid optimization
candidate, not an accepted architecture fact.

## 14. Natural bank lifetimes

| Subsystem | Likely natural lifetime | Evidence/status |
|---|---|---|
| Sprite patterns | Coexistence epoch, potentially reused across rounds | Phase-wide known union exceeds 196 patterns; graphics families recur. Exact epochs need full semantic closure. |
| Sprite static attributes | Semantic context or palette-policy lifetime | Graphics and palette are separate in arcade data; same graphics bank may use another attribute bank. |
| Palette mapping | Effective-bank plus semantic-class mapping lifetime | Small and direct, but registry/live disagreement and unresolved families block canonical closure. |
| CRAM state | Scene/effect transition, possibly frame-driven | Color values can fade, animate, or use carrier ownership; do not freeze into static sprite mappings. |
| Layer A | Generated coexistence epoch | Phase union exceeds capacity; current largest epoch is 639/676. |
| Layer B | Phase-static for R1/P1 | One fixed 854-pattern set loaded at gameplay entry. Later reuse should be hash-discovered. |

Round and Phase remain useful keys into generated descriptors, but compiler-derived
semantic epochs should determine actual switching.

## 15. Runtime pointer state and activation

**DESIGN RECOMMENDATION:** Runtime state should hold direct active pointers, plus
small IDs only where useful for validation:

```text
current_sprite_graphics_map      dc.l
current_sprite_palette_map       dc.l
current_sprite_residency_desc    dc.l
current_cram_state_desc          dc.l
current_plane_a_map              dc.l
current_plane_a_package          dc.l
current_plane_b_map              dc.l

current_context_id               dc.w
current_plane_a_epoch_id         dc.w
```

Activate scene/phase fields at the original semantic scene or phase transition.
Activate Plane A and future sprite residency epochs only at their proven producer
boundaries. Unchanged interned bank IDs should not trigger reloads.

**DESIGN RECOMMENDATION:** Hot paths must dereference a current pointer and index
directly. They should not walk Round to Phase to descriptor to bank for each cell or
sprite. IDs are useful for assertions and trace readability; pointers/base offsets
are preferable for normal 68000 lookup.

## 16. ROM and WRAM cost

Measured/current payload references:

- Palette mapping equivalent to current live logic: 128 bytes per context;
  four contexts are 512 payload bytes.
- Plane A active LUT: 10,240 words, 20,480 bytes of WRAM.
- Current seven-package Plane A plus fixed Plane B binary: 47,268 bytes.
- Fixed Plane B mapping/upload payload: 6,832 bytes.
- Sprite resident VRAM: 6,272 bytes, 49 cells / 196 patterns.
- Full PC080SN and PC090OJ source pattern regions already exist as 524,288-byte
  source assets; generated maps should reference them rather than duplicate source
  art.
- Context descriptors at roughly 24 to 32 bytes each are negligible.
- CRAM state snapshots are 128 bytes each before any transition program metadata.

Sprite mapping alternatives:

- Dense code-only word map: `8192 * 2 = 16 KiB` per graphics context.
- Naive code/effective-bank word map: `8192 * 128 * 2 = 2 MiB` per context,
  rejected as wasteful.
- Recommended compact legal-pair or semantic-piece map: size depends on completed
  legal-domain enumeration and should be interned/deduplicated. Exact size is
  currently unknown.

Plane A should retain compressed package/base-plus-delta installation rather than
copying a complete 20,480-byte flat LUT into ROM for every bank. Seven flat copies
would already be 143,360 bytes before mapping/upload metadata, compared with the
current 47,268-byte combined package.

**DESIGN RECOMMENDATION:** Trading modest, compact, deduplicated ROM tables for
O(1) runtime lookup is favorable. Trading ROM for naive Cartesian products or
duplicated full LUTs is not.

## 17. Bank-switching analogy

**ANSWER: PARTLY.** The analogy is useful because a semantic transition changes the
base pointer that backs a stable lookup, and subsequent accesses use the same index
against another immutable payload. It is not hardware address-window banking:

- no cartridge mapper changes address visibility;
- multiple subsystem banks remain independently addressable in ROM;
- activation may include VRAM/CRAM uploads rather than only pointer exchange;
- lifetimes are compiler-derived semantic/coexistence epochs, not fixed physical
  ROM pages.

A more precise term is **generated context descriptors with independently interned
mapping and residency banks**. `Semantic bank switching` remains a fair shorthand
if this distinction is documented.

## 18. Current Build 0354 versus proposed architecture

| Concern | Current Build 0354 | Recommended architecture |
|---|---|---|
| Runtime semantic decisions | Linear sprite palette route scan and dynamic sprite residency; direct active Plane A LUT | Direct compact palette/attribute lookup; retain only proven dynamic residency and SAT state |
| Per-frame/VBlank CPU | Palette fixup scales strongly with emitted SAT entries | Resolve mapping at emit time through current bank pointer |
| VRAM transitions | Plane A generated packages; fixed Plane B; dynamic sprite worklist | Keep independent transitions; eventually generated sprite coexistence epochs if proven beneficial |
| ROM | Compact boundary package; source art; unused generated palette-LUT artifact in build output | Interned compact maps/descriptors; no Cartesian LUTs or duplicated source art |
| WRAM | 20 KiB active Plane A LUT plus sprite residency metadata and post-pass arrays | Active pointers/IDs; keep active Plane A representation as needed; retire post-pass metadata after parity proof |
| Complexity | Split between generated plane packages and generalized sprite policy | More offline compiler complexity, simpler bounded 68000 hot paths |
| Correctness risk | Existing behavior known but palette authority disagrees; dynamic scans are costly | Generated oracle can be exhaustive, but table relocation and incomplete domains are hard gates |
| Debuggability | Runtime behavior requires tracing loops and state | Bank IDs, hashes, generated manifests, and fail-closed sentinels improve attribution |
| Future scaling | New contexts risk more route logic and runtime policy | Reuse identical interned banks and add only semantically distinct payloads |

### Status classification

**Already aligned:**

- fixed Round 1 Phase 1 Plane B vocabulary;
- generated Plane A stable/transition packages;
- O(1) active Plane A mapping lookup;
- bounded sprite pattern-DMA worklist;
- offline PC090OJ editor/reindex source;
- native sprite lane and SAT production.

**Partially aligned:**

- context/package activation;
- sprite pattern residency, which is bounded but still general and dynamic;
- generated OPT-003 palette map tooling, which proves representability but is not
  active or semantically reconciled.

**Still transitional:**

- `.Lnative_pal_fixup` and repeated `palette_route_lookup` scans;
- `pc090oj_sat_nibble` and `pc090oj_sat_force_line` post-pass metadata;
- active Plane A LUT reconstruction during package activation;
- the old hand-authored 256-byte `pc090oj_slot_lut`, which is not a complete
  semantic graphics bank.

**Fundamentally incompatible with the recommendation:**

- treating the current live palette route table as semantic authority while it
  disagrees with the sole canonical palette registry;
- forcing all subsystem banks to switch as one Round/Phase monolith;
- a one-bank R1/P1 Plane A design under current capacity/fidelity;
- a naive full code-by-bank sprite LUT;
- assigning colored output to unknown palette identities.

## Architectural risks

1. **PROVEN FACT:** Canonical palette decisions and live routes disagree for
   established R1/P1 mappings.
2. **PROVEN FACT:** The legal sprite corpus remains materially unresolved.
3. **PROVEN FACT:** Enabling the 512-byte OPT-003 generated table caused a
   deterministic code/rodata-layout regression. A later correction disproved the
   earlier BSS-shift explanation: all 138 matched BSS symbols were unchanged. The
   exact stale native address-as-data or undeclared relocation remains open.
4. **STRONG INFERENCE:** Independently switched banks require explicit coherence
   rules so a new palette map, CRAM state, graphics map, and residency package do
   not describe different contexts during a transition.
5. **UNKNOWN / NEEDS PROOF:** Plane A's capacity-only four-bank solution may not
   preserve visible transition overlap.
6. **UNKNOWN / NEEDS PROOF:** Dynamic CRAM effects and carrier ownership are not
   fully reducible to immutable context snapshots.
7. **DESIGN RECOMMENDATION:** Generated domains must include statically legal but
   unobserved cases. Trace absence is not proof of illegality.
8. **DESIGN RECOMMENDATION:** Any new rodata bank must pass address-as-data and
   reflow/relocation audits, not only functional table-equivalence tests.

## Recommended next step

**Should Build 0355 implement anything immediately? NO.**

First complete one no-ROM proof package:

1. Reconcile `specs/palette_decisions.json` with the current route table for every
   currently reachable R1/P1 effective bank. Explicitly distinguish intentional
   test configuration from accepted semantic mapping.
2. Generate a fail-closed sprite palette oracle over the full statically legal
   R1/P1 domain. Each row should contain semantic class, arcade code, source nibble,
   control state, effective bank, force tag, expected Genesis line, decision ID,
   and resolution status. Preserve unresolved cases without assigning colors.
3. Diagnose the deterministic OPT-003 code/rodata-shift regression and add a
   relocation/address-as-data invariant that fails before publication.
4. Only after those gates pass, implement one bounded change: direct 128-byte
   active palette-map lookup at native sprite emission with exhaustive SAT word-2
   parity, then remove the later normal-gameplay palette fixup metadata/pass.

The sprite-residency epoch compiler and further Plane A package minimization should
remain separate later tasks. Pattern DMA is bounded and commonly zero, while the
palette route is the measured immediate hotspot.

## Final determinations

- **Should Rastan use context-selected generated LUT banks? PARTLY / YES by
  subsystem.** They should dominate immutable mappings, but not replace genuinely
  dynamic state or force synchronized lifetimes.
- **Confidence:** High for the top-level independent-bank recommendation, Plane A
  and Plane B conclusions, and immediate palette-hotspot boundary. Medium for the
  eventual sprite-residency form because the legal sprite corpus is incomplete.
- **Context descriptor:** Yes, with independently interned fields and optional
  generated epoch schedules.
- **Automatic lifetime discovery and payload deduplication:** Yes, subject to
  arcade semantic and transition proofs.
- **`.Lnative_pal_fixup`:** Eliminable with the enumerated conditions, not safe to
  remove today.
- **One phase-wide R1/P1 Plane A bank:** No under current capacity and approved
  fidelity.
- **One phase-wide R1/P1 sprite pattern bank:** No for the known union at current
  capacity; exact epoch plan remains unknown.
- **R1/P1 Plane B:** Already phase-static at 854 patterns.
- **D00462:** Unchanged.
- **Build 0353 visual baseline:** Unchanged.
- **Build 0354 diagnostic evidence:** Unchanged.
- **All numbered builds:** Preserved.
