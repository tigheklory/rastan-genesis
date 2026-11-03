# RG-012 Writer-Triggered Native Audit and PC090OJ/PC080SN Producer Decompilation

Date: 2026-10-21  
Agent: Cody  
Scope: static analysis and reconstructed C only; no production implementation

## Baseline and scope controls

The accepted baseline remains Build 0472. The existing normal artifact is 2,739,896 bytes and
still hashes to `5b855e163a572c3a511a76470199c9cb13324f6ea0739bbd0f6834b80092dc7a`.
`accepted/build-0472` peels to the exact ROM-producing source
`4d5aadb0e92387617594404f9e757597c87517a3`; the build counter remains 472.

No ROM was built, no build number was consumed, no MAME process or gameplay route was run, and no
trace, input movie, save state, instrumentation, production assembly, remap specification, writer
hook, dirty flag, or HUD code was created or changed. This report uses the current source, canonical
Ghidra exports, `build/maincpu.disasm.txt`, the generated native tables, the current
`build/rastan-direct/address_map.json`, and the existing C decompilation.
Build 0473 was not produced or consumed.

## Policy boundary

This is an analysis-only task, so it removes no chip tail. The semantic cuts evaluated are:

- PC090OJ: retained actor creation, family/state/animation selection, position, palette policy,
  flip, visibility and priority/order -> final native SAT entries. The chip tail is the old
  descriptor-program expansion, object-RAM formatting/mirroring, record scan and record decoder.
- PC080SN: retained progression, scene/layout selection, scroll/ring ownership, descriptor source
  selection and logical cell choice -> final Plane A/B name words and bounded publication jobs.
  The chip tail is C-window address formatting, name-RAM walking, raw hardware-register writes and
  generic chip-address projection.

Current transitional compatibility remains where retained producers have not yet been lifted:
the PC080SN C-range dispatcher and generic fill/text/block-copy routes, descriptor and item-page
source-pointer relocation, and the general PC090OJ Level-A/Level-B paths. Their consumers and the
safe removal boundaries are inventoried below. Native SAT queues, reverse residency, Plane A/B
staging buffers and row/column dirty masks are final Genesis mechanisms, not chip shadows.

## Evidence and tool reuse

No new analysis infrastructure was made. Static provenance reused:

- canonical Ghidra `function_inventory.tsv`, `hw_refs.tsv`, call graph and decompiler export;
- original raw 68000 disassembly;
- current generated arcade-to-Genesis address map (not a presumed `+0x200` delta);
- existing `analysis/decompilation/c` semantic and raw reconstructions;
- generated generic sprite base/usage/frame tables and sprite residency tables;
- current native sources listed in the prompt, including all nine mandatory files.

The current address map is important: old reports and a few source comments retain historical
runtime PCs such as `0x055B04`/`0x055E5E`. At Build 0472 the authoritative mappings are instead
`0x055904 -> 0x055980` and `0x055C5E -> 0x055CDA` after accumulated shifts.

### Mandatory native-source audit coverage

| File | Finding |
|---|---|
| `apps/rastan-direct/src/pc090oj_hooks.s` | Contains the main generic-family rediscovery candidate, general per-piece dynamic finalization, direct control writers, SAT-ready handoff and accepted score dirty path. |
| `apps/rastan-direct/src/pc090oj_assets.s` | Only binds generated tables/assets; it performs no consumer polling. The base/usage/frame and residency data make static exact-frame specialization possible. |
| `apps/rastan-direct/src/vdp_comm.s` | Tile and Plane row publication is dirty-mask driven. Staging buffers are final native state, not compatibility shadows. |
| `apps/rastan-direct/src/dma.s` | VBlank orchestrates bounded tile/palette/Plane/SAT commits; it does not rediscover actor or scene identity. |
| `apps/rastan-direct/src/tilemap_hooks.s` | Contains event-bound descriptor/tileset compatibility checks, native row/column producers, and remaining C-window/address translation residue. |
| `apps/rastan-direct/src/scene_load.s` | Uses requested scene/package IDs to choose generated manifests at scene events; no ordinary-frame polling. |
| `apps/rastan-direct/src/palette_hooks.s` | Authoritative publisher hooks perform mutation-side staged-word comparison and notify `palette_pending` only on real changes. |
| `apps/rastan-direct/src/fg_tile_cache.s` | Package/record/epoch checks are explicit install/advance/reseed guards; uploads and remaps happen only at those events. |
| `apps/rastan-direct/src/hud_native.s` | Frontend has bounded ten-byte consumer polling; gameplay score is writer-triggered. HUD remains unchanged and outside implementation scope. |

## Phase 1: known event-driven systems

| System | Static verification | Classification |
|---|---|---|
| `palette_pending` | Mutation-side palette hooks and scene activation set it; VBlank `vdp_commit_palette` tests once, performs one 64-word CRAM DMA when set, then clears it. | Writer-triggered dirty notification; keep. Some comments still say “unconditional,” but current instructions are dirty-gated. |
| `tiles_dirty` | Tile producers set the byte; `vdp_commit_tiles_if_dirty` tests once, writes 48 words only when set, then clears it. | Writer-triggered dirty notification; keep. |
| `bg_row_dirty` / `fg_row_dirty` | Logical row producers set bits; VBlank walks only the captured dirty mask and clears published bits. | Writer-triggered bounded publication; keep. |
| `bg_col_dirty` / `fg_col_dirty` | Logical column producers set one of two 32-bit masks; VBlank gathers and publishes only dirty columns, then clears both masks. | Writer-triggered bounded publication; keep. |
| `pc090oj_sat_frame_ready` | Native finalization sets it once a complete back bank exists; prepare skips a second build, commit swaps banks, DMAs the ready SAT, then clears it. | Producer/consumer handoff; keep. |
| `gameplay_hud_score_dirty` | Proven score writers notify; unchanged gameplay tests one byte and performs no BCD reads or digit rebuild. | Accepted writer-triggered design; HUD is unchanged by RG-012. |

## Phase 1: change-detection and rediscovery candidates

### Candidate matrix

| Candidate / consumer | Frequency | Authoritative state and repeated work | Unchanged versus changed work | Classification | Expected relevance |
|---|---|---|---|---|---|
| `.Lnative_generic_frame_try` in `pc090oj_hooks.s` | Per retained actor frame entering Level B | Actor base `+0x1E` indexes a 4096-byte LUT, then a 10-byte usage descriptor revalidates discriminator, compositor `+0x38`, attribute policy `+0x27`, controller/bank lane, selector `+0x01` range and orientation before indexing a generated frame. | A rejected/unchanged identity still pays the classification checks; an accepted frame continues into final piece emission. | **Stable-identity rediscovery**, mixed with required dynamic selector/orientation evaluation. | High for cave bats and any route dominated by exact generated families; potentially visible in rope/general gameplay only in proportion to actors using this path. No cycle claim. |
| `.Lnq_emit_entry` general Level-A finalizer | Per piece | Source/variant identity tags, blank-code bitset, wrapped geometry, oriented opaque bbox, variant group/bank, palette line and reverse residency. | Ordinary pieces repeat the dynamic validity/clipping/resource work; tagged exact frames bypass source/blank/variant work, and fixed HUD cells bypass bbox. | Mostly **legitimate dynamic evaluation**; remaining untagged identity translation is transitional. | General gameplay and bats; rope relevance depends on piece count. |
| `genesistan_hud_prepare_frontend` | Per frontend VBlank | Ten scalar bytes: three 3-byte BCD groups plus credit. | Ten comparisons; only a changed group/credit rebuilds and publishes records. | **Consumer polling**, bounded and frontend-only. Writer closure is not established here; HUD explicitly out of scope. | None for gameplay rope or cave bats; frontend only. |
| `genesistan_hook_pc080sn_descriptor_rebuild` | Per descriptor rebuild/reseed event | Compares retained progression `A5+0x013E` with `fg_boundary_active_record`; on mismatch installs the generated boundary package, then rebuilds 17 descriptor entries (`D0=16` with `DBRA`) through arcade-to-Genesis pointer relocation. | Same-record rebuild skips package installation but still performs the required descriptor rebuild; changed record installs first. | Record comparison is **event-bound guard**; pointer reconstruction is **translation residue**. | Low in steady rope/bat frames; scene/reseed only. |
| `genesistan_hook_itempage_strip_blit` | Per 64-cell Plane-B strip during fill/stream | Relocated source pointer selects gameplay/outdoor/cave tileset, compares desired ID with `genesistan_current_pc080sn_tileset_id`, and calls `load_scene_tiles` only on mismatch. | Cache hit continues directly to native strip staging; miss loads a generated residency package and may arm presentation. | **Consumer-side cache test**, but bounded to a semantic strip event; also translation residue. | Scene entry and vertical/background streaming; can affect rope route structurally, not ordinary bat SAT cost. |
| `pc090oj_ctrl_shadow` and `pc090oj_sprite_ctrl_shadow` setters | Only at authoritative arcade control writes | Compares the incoming control word with current native control state and stores only on change. | One mutation-site comparison; no later scan is triggered by the setter itself. Finalizer reads the current value because flip/bank is presentation-dynamic. | **Direct update already**, not polling. | Global sprite presentation; comparison itself is negligible structurally and not a target. |
| `load_scene_tiles` scene/package selection | Per requested scene/package load | Scene/tileset ID chooses a static generated manifest; current IDs and presentation state prevent inappropriate reload/display enable. | No ordinary-frame work; requested loads perform bounded manifest upload and event setup. | **Generated/static native metadata** plus legitimate resource-cache state. | Scene transitions only. |
| `fg_boundary_install` package/record/epoch checks | Per explicit install/advance/reseed event | Active package, record and transition ownership avoid duplicate uploads and preserve overlap handoff. | Same package follows its no-op/limited path; changed epoch uploads required identities and remaps names. | Legitimate **native resource evaluation**, already event-bound. | Scene/segment boundaries; not ordinary actor frames. |
| Palette hook staged-word comparisons | At authoritative palette publisher calls | Converted CRAM word is compared with staged word; `palette_pending` is set only if any destination changes. | Unchanged publisher does conversion/comparison but causes no CRAM DMA; changed publisher writes and notifies. | Mutation-side **change detection**, not consumer polling. | Animated palette publishers and transitions; possible route relevance, but correct semantic location. |

### Resulting architecture choices

- **Keep per-frame:** selector/orientation, position, clipping/bbox, effective palette when policy is
  dynamic, SAT capacity/order, and dynamic sprite residency. These are current presentation facts.
- **Keep event-bound:** progression/package mismatch guards, tileset cache tests and scene resource
  selection. They are not broad steady-frame scans.
- **Generated/static native metadata:** exact frame piece lists and invariant frame attributes are
  already generated. Extend only for families whose identity transition writers are proven closed.
- **Do not add a dirty flag yet:** generic actor family identity. The writer set for all validated
  fields is not complete enough, and several fields are demonstrably mutable.

## Upstream writer proof

### PC090OJ global controls: bounded and already intercepted

The canonical Ghidra hardware-reference export and a whole-disassembly search give a closed set of
three PC090OJ global-flip control writes and nine true sprite-control writes. The current spec
already replaces them at the hardware mutation sites. The address map gives:

| Original PC -> mapped PC | Containing function | Meaning / timing |
|---|---|---|
| `0x03AE06 -> 0x03B01E` | `FUN_0003add8` | set PC090OJ global control to 1; runtime frontend transition |
| `0x03AE1E -> 0x03B036` | `FUN_0003add8` | clear global control; runtime frontend transition |
| `0x03AE8E -> 0x03B0A6` | `startup_common_body` | startup clear |
| `0x03A1D8 -> 0x03A3D8` | `frontend_state0_init_3a1c4` | initialize sprite control from retained `A5+0x14` |
| `0x03AE34 -> 0x03B04C` | `FUN_0003ae28` | runtime control-bit update |
| `0x03AE9C -> 0x03B0B4` | `startup_common_body` | startup clear |
| `0x03AF1E -> 0x03B136` | `startup_common_body` | startup value `0x60` |
| `0x03EF28 -> 0x03F124`, `0x03EF48 -> 0x03F144` | `FUN_0003eefa` | runtime bit-3 set/clear |
| `0x03EF8A -> 0x03F186`, `0x03EFAA -> 0x03F1A6` | `FUN_0003ef5c` | runtime bit-2 set/clear |
| `0x045306 -> 0x045502` | Ghidra-unlisted section/round transition body | runtime bank/control selection from retained state |

These replacements are existing hardware-call/store substitutions and do not require new insertion.
Their helpers receive the intended value in `D0` or a fixed constant and return without exporting a
new value. Any future modification must preserve each site's CCR/register contract; startup clear
and ordinary `MOVE.W` sites do not all have identical flag behavior. The writer set is complete for
these two hardware addresses. The right decision is **DIRECT UPDATE (already implemented)**, not a
consumer dirty scan.

### Generic actor identity: writers are not creation-only

The generated usage table currently recognizes five exact usages:

- cave block: discriminator `+0x05 == 0x1E`, base `0x0179`, selector `0x70`, comp 0, bank `0x3C`,
  embedded attribute;
- burst: `+0x05 == 0x0F`, base `0x0275`, selectors `0x9E..0xA0`, comp 0, bank `0x30`, embedded;
- lizard: family `+0x3E == 0`, base `0x004B`, selectors `0x17..0x1F`, comp 0, bank `0x36`, override;
- large bat: rec-type `+0x06 == 0x0A`, base `0x03F6`, selectors `0xB6..0xB8`, comp 0, bank `0x3E`, embedded;
- small bat: rec-type `+0x06 == 0x0B`, base `0x0268`, selectors `0xB9..0xBB`, comp 0, bank `0x3E`, embedded.

The fields do not form one immutable identity:

- `0x4543E`/`0x4544E` initialize base, selector, config and compositor-related template state;
- `0x4A086` creates scheduled actors and writes family plus the parallel variant;
- marker-chain handlers rewrite base, selector, state and compositor during runtime;
- `0x40CCC` converts an actor in place during death/drop presentation, including family, base,
  compositor and palette-policy state;
- `0x42ABC` rewrites death presentation base, selector and compositor;
- `0x4092E` clears/rearms records;
- `0x45684` establishes the palette override, while retirement/death paths can clear bit 6;
- animation handlers deliberately change selector `+0x01` every active frame.

The raw disassembly contains many additional base and compositor writes across family-specific
handlers. Therefore a global “set native family handle at creation” design is **NOT SAFE**. A narrow
per-family handle remains **PLAUSIBLE — MORE DECOMP NEEDED** only if its creator, every identity-
changing transition and retirement/reuse path are closed. Selector/orientation must remain dynamic.
The safest future insertion point is a higher-level semantic creator/transition call, not hooks on
individual byte stores.

Reflow risk is high for arbitrary retained-region hooks: many source stores are 4-6 bytes and sit in
branch-heavy state handlers. A `JSR` insertion could shift relative branches and computed tables;
CCR, all live registers, stack balance and record-reuse semantics must be preserved. Builds 0470/
0471 demonstrate that undeclared crossing tables are unacceptable. No hook is recommended now.

### Progression / descriptor record writers

A whole-disassembly store search closes the direct `A5+0x013E` writer set:

| Original PC -> mapped PC | Function / purpose | Timing and contract |
|---|---|---|
| `0x05025A -> 0x050456` | `world_select` (`0x50248`) | initialization/section selection: table `0x5073A[section]` becomes progression |
| `0x0558FE -> 0x055978` | segment/ring-cycle advance | runtime increment after a completed 64-publication cycle; already replaced by size-changing `fg_boundary_advance_segment`, preserving the increment and installing the package |
| `0x055F26 -> 0x055FA2` | transition state-8 restore | runtime restore from checkpoint `A5+0x13B8` during scene/continue transition |

The descriptor rebuild entry `0x055904 -> 0x055980` then consumes progression at a natural event
boundary. It already catches initialization and checkpoint restoration through its active-record
mismatch, while the segment writer has a direct native replacement. Thus a new dirty flag would
only move a small event-bound comparison into three sensitive retained sites. Classification:
**ALREADY EVENT-BOUND / LOW PRIORITY**.

The `0x0558FE` replacement is a declared 4-to-6-byte shift replacement; any change must retain its
following original `RTS`, registers/CCR and all reflowed branches/tables. The other two are ordinary
retained stores and would require explicit semantic reflow if enlarged. Prefer the existing
descriptor-rebuild hardware-tail replacement over inserting calls at them.

### Item-page / Plane-B tileset ownership

The relevant boundaries are already exact replacements:

- descriptor rebuild `0x055904 -> 0x055980`;
- item-page strip-populate relocation `0x055C2E -> 0x055CAA`;
- item-page/native Plane-B strip boundary `0x055C5E -> 0x055CDA`;
- retained wrapper/bookkeeping `0x055C4A -> 0x055CC6`;
- retired raw per-cell tail begins at `0x055C7A -> 0x055CF6`.

The existing `0x055C5E` replacement occupies the original ten-byte entry as `JMP` plus padding and
reloads its clobbered inputs before use. A future higher semantic cut can replace source-pointer
range classification with a page/scene package selected by the retained page producer, but only
after the `0x055C4A` bookkeeping, source ownership and non-gameplay item-page consumers are fully
covered. Until then it is **REQUIRED TRANSITIONAL COMPATIBILITY** and a **SAFE FUTURE CUT
CANDIDATE**, not a per-frame dirty target.

## Phase 2: bounded producer decompilation

Four bounded functions were lifted without reopening the completed RG-007 airborne chain.

| Original PC -> mapped PC | New status | Semantic result | Optimization connection |
|---|---|---|---|
| `0x04382E -> 0x043A2A` | STUB_ONLY -> COMPLETE | State-0x13 animation-countdown reload: round 2 writes 4; every other round writes 0 to actor `+0x09`. | Confirms dynamic animation timing, not stable family identity; keep with retained actor state. |
| `0x0453D6 -> 0x0455D2` | STUB_ONLY -> COMPLETE | Record type 12 is exempt. Difficulty 0 decrements each `+0x28/+0x29` byte independently if >=2; difficulty 1 is unchanged; difficulty 2 increments only low byte; difficulty 3+ increments both. | Bounded template mutation at load time, but it controls gameplay tuning rather than native family identity. No presentation hook. |
| `0x0468D0 -> 0x046ACC` | STUB_ONLY -> COMPLETE | Initializes component facing to 1 iff wrapped actor X is below `A5+0x10BE`, else 0. | Facing is camera-relative/dynamic state and cannot be baked into a family handle. |
| `0x0504FA -> 0x0506FC` | PARTIAL -> COMPLETE | Selects a 12-byte record at `0x50850 + A5+0x013E*12` and initializes paired scroll fields `0x10AE/0x10EC`, `0x10B0/0x10EE`, plus `0x10B8`, `0x10BA`, `0x10BE`, `0x10C0`. | This is a bounded scene-entry semantic producer. A future scene package can consume this record directly instead of reconstructing chip descriptors, but the current event-bound rebuild is not a hot polling loop. |

Detailed contracts:

- `0x4382E`: input `A4` actor and `A5+0x0118` round; output is actor byte `+0x09` only.
  Callers are `0x437D4` and `0x43826` inside the state-0x13/0x14 handler `h5_4375c`.
  It calls nothing and changes no actor identity or state. Static completeness is high: the whole
  six-instruction leaf through its `RTS` is reconstructed.
- `0x453D6`: input `A4` actor/template result and difficulty byte `A5+0x002F`; outputs are the
  high and low bytes of actor word `+0x28` unless record type `+0x06` is 12. Its sole canonical
  caller is the shared apply tail at `0x4548E`, reached from record-type and family template loaders.
  It calls nothing and changes no lifecycle state. Static completeness is high: all four difficulty
  branches and both guarded decrements through `0x45416 RTS` are represented.
- `0x468D0`: input `A4+0x16` actor X and `A5+0x10BE` camera/player screen-X reference; output is
  actor facing byte `+0x02`. Callers are `0x4686E` in `actor_boss_component_4684e` and `0x468F4`
  in the adjacent component path. It calls nothing and makes no lifecycle transition. Static
  completeness is high: the wrapped compare and both facing results through `RTS` are exact.
- `0x504FA`: input is progression word `A5+0x013E`; outputs are the eight retained scroll/camera
  words listed above (two table words are each copied to a pair). It is called at `0x5020A` by the
  scene/round initializer beginning `0x501E2`, after world selection (`0x50248`), descriptor/layout
  setup (`0x502CC`) and initial scene fill (`0x503DC`), and before remaining scroll-state setup
  (`0x5053A`). It calls nothing and performs no PC080SN write. Static completeness is high: all six
  table words and the terminal `RTS` are reconstructed.

Raw reconstructions were added as `raw/0004382e.c`, `raw/000453d6.c`,
`raw/000468d0.c` and `raw/000504fa.c`; semantic forms were added to the existing actor-helper,
actor-behavior and world-scroll sources. The coverage census changes from 135 COMPLETE / 11
PARTIAL / 3 STUB_ONLY to **139 COMPLETE / 10 PARTIAL / 0 STUB_ONLY**.

Relevant remaining gaps are deliberately bounded:

- `0x51880` scroll step dispenser remains PARTIAL because its enclosing movement/caller closure is
  larger than the isolated cap-to-four expression;
- `0x539C2` vertical clamp controller remains PARTIAL because its branch/callee closure is not fully
  reconstructed;
- family-specific runtime identity transitions outside the already-complete actor functions remain
  incomplete, preventing a safe native family-handle writer set;
- PC080SN page/scene transition controller around `0x55E..0x560` needs a focused lift before the
  item-page source classification can move upward.

## Actor-family classification

| Field | Classification | Reason |
|---|---|---|
| Base `+0x1E` | Dynamic identity/state | Initialized from templates, then rewritten by marker chains and death/drop transforms. |
| Discriminator (`+0x05`, `+0x06` or `+0x3E`) | Mixed identity/state | State is dynamic; record type and family are more stable but can change on activation/reuse or in-place transformation. |
| Compositor `+0x38` | Dynamic presentation state | Template/death/handler paths rewrite it. |
| Palette override `+0x27` bit 6 | Dynamic policy | Creation resolver can set it; retire/death paths clear it; embedded and override policies both exist. |
| Sprite-control bank lane | Global dynamic presentation state | Writer set is bounded and already directly captured, but runtime transitions change it. |
| Selector `+0x01` | Dynamic frame state | Animation and behavior handlers deliberately update it. |
| Orientation/facing | Dynamic frame state | Camera-relative function `0x468D0` and other movement logic update it. |

Overall classification: a universal creation-time native family handle is **NOT SAFE**. Exact
large/small-bat handles are **PLAUSIBLE — MORE DECOMP NEEDED**, because their record-type and base
look narrow but their complete creation, death, reuse and transform writer closure has not been
proven. The current generated validator remains correct.

## Palette semantics

- Actor `+0x27` bit 6 selects whether the actor override replaces the compositor's embedded low
  byte; `0x3C9E8` is the proven render-time selector.
- `0x45684` resolves scheduled actor palette policy at creation, but in-place death/rearm paths can
  clear the override without rerunning that resolver.
- Sprite-control high bank bits are runtime-global and have the closed mutation set listed above.
- Scene palette manifests are generated/static at `load_scene_tiles`; animated publishers compare
  actual changed entries and set `palette_pending` only when staged CRAM changes.
- Generated Level-B frame attributes are safe only after the usage descriptor proves the expected
  embedded/override policy and bank lane. The current path already performs that proof before using
  invariant frame metadata.

Recommendation: keep generated native palette metadata for exact proven frames; do not generalize
it to a family solely from base or record type. No new palette dirty architecture is needed.

## Plane A / B semantic producers

- `0x50248`/`0x502CC` decide progression, scene index and scene descriptor/layout ownership.
- `0x504FA` initializes retained scroll/camera semantic state from the progression record.
- `0x563A6` decompresses background metatile/page data; `0x55C4A` owns strip cursor/bookkeeping and
  `0x55C5E` is the current native Plane-B publication boundary.
- `0x55904` rebuilds descriptor sources; `0x559B2`/`0x55A14` produce collision-grid semantics from
  the same layout family. Collision remains retained gameplay state, not a rendering tail.
- Plane A/B native producers decide final name words and set row/column dirty masks; VBlank is only
  the bounded publisher.

The best future upward cut is at the retained scene/page producer after it has chosen progression,
layout source and page/strip ownership: select a generated native package/final name source there,
while retaining collision and scroll semantics. Do not cut below at raw C-window destinations.

## Legacy translation inventory

| Remaining runtime mechanism | Classification | Removal boundary / reason |
|---|---|---|
| Level-B generic base/usage validation | NEEDS MORE DECOMP | Replace only for a family after all identity-changing writers and reuse paths are closed; selector/orientation remain dynamic. |
| Untagged Level-A source/blank/variant interpretation | REQUIRED TRANSITIONAL COMPATIBILITY | Generated exact frames already bypass portions; general actor/piece coverage is incomplete. |
| SAT lane ordering, bbox/clipping, reverse residency and DMA worklist | DO NOT TOUCH | Final Genesis realization and resource management, not PC090OJ emulation. |
| PC090OJ global/sprite-control native words | ALREADY EVENT-BOUND / LOW PRIORITY | Bounded hardware writers directly update them; finalizer legitimately reads current control. |
| PC080SN C-range dispatcher in `genesistan_hook_3ad44_dispatch` | SAFE FUTURE CUT CANDIDATE | Its D-range/PC090OJ role is retired; remove only after every remaining C-range producer has a semantic native owner. |
| Descriptor rebuild pointer relocation | SAFE FUTURE CUT CANDIDATE; ALREADY EVENT-BOUND | Move to generated scene packages after all progression/reseed consumers are covered. |
| Item-page strip descriptor/source relocation | REQUIRED TRANSITIONAL COMPATIBILITY / SAFE FUTURE CUT CANDIDATE | Current non-gameplay and shared page producers still supply arcade-format pointers. |
| Generic BG/FG fill, block-copy and textwriter routes | REQUIRED TRANSITIONAL COMPATIBILITY | Frontend/text/unconverted producers still use them; remove producer-family by producer-family. |
| `staged_bg_buffer`, `staged_fg_buffer`, row/column dirty masks | DO NOT TOUCH | Final native Plane B/A representation and VBlank publication source. |
| `fg_boundary_*` package/epoch state and `load_scene_tiles` manifests | ALREADY EVENT-BOUND / LOW PRIORITY | Native residency ownership, not chip emulation. |
| Historical tall projection/object-RAM scan/decoder | Already retired | No live final-authority role; do not recreate. |

## Reflow and contract conclusions

1. Prefer existing retired-device write/call sites. Global control and palette publishers already
   have bounded exact replacement points.
2. Do not insert calls after arbitrary actor field writes. The writer set is broad, branch/table
   dense and not closed; a correct design needs a higher semantic creator/transition boundary.
3. The existing item-page and descriptor sites are equal-footprint hardware-tail replacements.
   Changing helper semantics need not insert bytes into retained code, but must preserve their
   documented register, CCR, stack, source cursor and return/fallthrough contracts.
4. Any size-changing retained-region change must use declared shift replacement and audit every
   crossed relative branch, absolute operand and explicit displacement/jump table. The RG-008/RG-009
   failures are direct evidence that nearby undisclosed tables cannot be assumed safe.
5. Writer-trigger hooks must preserve the caller-visible SR when they replace an operation whose
   flags remain live, just as the accepted score notification does. No candidate here is approved
   for implementation by this report.

## Conclusion

The current native architecture is already strongly event-driven at VBlank publication, palette,
tile, scene-package and score boundaries. The only convincing steady actor-side rediscovery target
is the generic generated-family classifier. It cannot safely become a universal creation-time
handle yet because its purported identity fields are not immutable and the transition writer set is
not closed. PC080SN comparisons are mostly event-bound compatibility guards; the meaningful future
gain is a higher scene/page semantic cut that removes arcade descriptor and pointer representation,
not more dirty flags. Build 0472 and all production behavior remain unchanged.

Prioritized future evidence work, not authorized for implementation by RG-012:

1. Close the large/small-bat creator, death/impact, reuse and identity-transition writer set, reusing
   the completed RG-007 airborne functions rather than reopening them.
2. Lift the bounded `0x55E..0x560` page/transition controller far enough to prove page ownership and
   all non-gameplay consumers above the item-page pointer-relocation tail.
3. Only if item 1 closes cleanly, design an exact generated bat-family handle set at proven semantic
   creator/transition boundaries, leaving selector, orientation, position, clipping and residency
   dynamic.
4. Leave frontend HUD polling and current event/dirty publication systems unchanged unless a later
   explicitly scoped task proves their writer closure and measures a relevant cost.
