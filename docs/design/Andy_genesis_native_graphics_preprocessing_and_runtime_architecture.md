# Genesis-Native Graphics Preprocessing & Runtime Architecture (FINAL)

**Author:** Andy · **Revised:** 2026-10-06 · **Baseline:** Build 0400 (`9094d21`), behaviorally accepted.
**Status:** DESIGN / ARCHITECTURE ONLY. No production source changed, no ROM, no Build 0402, Build 0401
not reapplied. This is the finalized implementation blueprint for Cody.

Build 0401 (WORK/READY/DISPLAYED ownership) is SHELVED, not rejected — preserved in full under
`docs/design/build0401_shelved/` (design, exact patch, hashes, notes, results, promotion/adoption
model). 0401 proved ownership isolation works behaviorally; its temporary full-plane snapshot cost
makes it unsuitable as the *immediate* development baseline, so it is reintroduced late (§20).

**Authoritative premise (KF-089 / the Build-0400 audit):** there is **no remaining PC090OJ/PC080SN
hardware-bus emulation.** This is **not** a "remove emulation" project. The real problems are: (1)
runtime interpretation of arcade graphics structures; (2) translation overhead; (3)
arcade-memory-layout/token coupling; (4) runtime interpretation of precomputable information; (5)
graphics-specific re-entry into arcade routines (textwriter `0x565CE`); (6) inefficient sprite
residency lookup/derivation.

Governing principle throughout:

> **Python preprocesses invariant knowledge; the Genesis 68000 handles dynamic game state.**

**Decisive correction incorporated this revision:** the `(code, effective_bank) → finalized Genesis
pattern` mechanism is *already implemented and proven* in
`tools/graphics_editor/gen_reindexed_pc090oj.py` (artifacts `pc090oj_editor.bin`,
`pc090oj_sprite_variants.inc`, `pc090oj_variant_index.json`, `pc090oj_editor_manifest.json`). Arcade
code alone is **not** a unique finalized Genesis graphics identity. This design reuses that resolver
and never invents a competing `(code,bank)` representation.

---

## 1. Build-0400 architectural truth

### 1.1 Frame structure (unchanged)
```
IRQ6 _vblank_service -> input -> sprite guard -> dma_publish_frame (publishes N-1)
  -> tail-JMP arcade worker 0x3A208 (IPL7): SEMANTIC OWNER runs, hits native graphics hooks
  -> restore IPL -> RTE -> mainline spin
```

### 1.2 What stays arcade-owned (do NOT rewrite for purity)
The arcade worker owns, and keeps owning: actor lifecycle, spawn/despawn, AI, state machines,
animation **state selection**, position, velocity/movement, collision/gameplay, health/status,
camera/scroll, progression, and **dynamic palette intent**. The problem this design targets exists
*after* those semantic decisions.

### 1.3 Current graphics pipeline (the problem)
```
arcade semantic state
  -> arcade-oriented graphics representation
  -> RUNTIME INTERPRETATION  (family tables, animation descriptors, piece streams,
                              arcade code values, palette-bank semantics, address-token vocabulary,
                              (code,bank) variant resolve, per-sprite residency derivation)
  -> Genesis-native staged graphics -> dma_publish_frame -> VDP
```
The sprite interpreter `.Lnative_emit_actor_common` (`pc090oj_hooks.s:598-768`) is the hot path:
`worker ≈ 55,600 + 2,609 × emitted_sprites`.

### 1.4 Migration target
```
arcade semantic state
  -> small explicit native semantic key  (family/usage, anim, orientation, X/Y, attr, lane)
  -> precomputed Genesis-native frame + pattern metadata
  -> bounded hybrid residency (finalized-pattern keyed)
  -> SAT / plane staging -> dma_publish_frame -> VDP
```
The arcade worker remains; the repetitive graphics interpretation disappears, frame by frame, as
coverage grows. Unknown frames stay on the Build-0400 fallback.

---

## 2. Arcade-memory-layout / token coupling

Values like `0xD00460 + actor_index*0x50`, `0xC00000/0xC08000 + offset`, `0x200000 + pal_offset`
are **not dereferenced hardware** — they are semantic values expressed in the arcade machine's
*address vocabulary*. `0xC08000 + off` means "FG plane destination + off"; `0xD00460 + idx*0x50`
merely encodes "actor/register slot idx"; `0x200000 + off` encodes a palette destination. Native
code currently *recognizes and re-decodes* these each frame (`cmpi/subi/divu/cmpa`).

**Target:** explicit native semantics — `{plane=A, tile_offset=N}`, `actor_index=N`,
`palette_identity=N` — converted **once at the graphics producer boundary** (the first native hook
that sees the token), not repeatedly downstream.

**Hard constraint:** do **not** globally rewrite A5-WRAM for cleanliness. The game logic's WRAM may
stay arcade-oriented wherever changing it risks behavior. Convert at the read-side boundary only.

---

## 3. Palette Composer authority model (two distinct roles)

The new frame compiler **integrates with**, and never duplicates, the Palette Composer.

**3A — Human authoring workspace:** the Palette Composer edits
`analysis/graphics_optimizer/editor_policy/Test.json` (authored target lines, per-usage `index_map`s,
shared-line color choices, context mappings, Layer-A where supported). It is the authoring
workspace, **not** the canonical production registry.

**3B — Canonical decision authority:** `specs/palette_decisions.json` is the canonical palette
registry (arcade palette semantics, effective bank, Genesis realization, context/stage scope,
status ∈ {proven, decided, provisional, unknown}, evidence, consumers, compromises). Generated frame
data must **never** silently override it. The frame compiler consumes palette *results*; it does not
make or restate palette decisions (per `feedback_no_palette_registry_duplication_in_reports`).

---

## 4. The `(code, effective_bank)` finalized-pattern architecture (ALREADY PROVEN — REUSE)

`gen_reindexed_pc090oj.py` already implements the complete variant mechanism:

- It bakes **one base cell per code** at `code*128` (base bank by `BASE_PRIORITY`) and **appends a
  distinct 128-byte variant cell for every divergent `(code, effective_bank)`**, grouped by code,
  into `pc090oj_editor.bin` (`region_cell_base = 4096`).
- It emits an **O(1) runtime resolver** in `pc090oj_sprite_variants.inc`:
  `pc090oj_variant_group_base[code]` (u16, `0xFFFF` = not divergent) and
  `pc090oj_variant_bank_slot[effective_bank]` (byte, `0xFF` = base). Runtime selects
  **`vi = group_base[code] + bank_slot[bank]`**.
- Divergent `(code,bank)` entries are **never collapsed, never dominant-overwritten**.
- `effective_bank` is a **static property of the semantic usage** (`USAGE_BANK`: rastan 0x33,
  lizardman 0x36, valkyrie 0x32, chimera 0x34, flying_demon 0x35, bats 0x3E, four_armed 0x3A,
  cave_block 0x3C, burst 0x30, weapons 0x33). A single *code* can appear under different banks across
  usages → that is exactly what the variant table represents.
- Index/hashes already recorded: `pc090oj_variant_index.json` carries `profile_sha256`,
  `bank_ordinal`, `group_base`.

**This is the canonical `(code,bank) → finalized native pattern` resolver. Reuse it as-is. Do not
build another.**

---

## 5. Four distinct identities (must not be conflated)

| # | Identity | Definition | Who owns it |
|---|---|---|---|
| **A** | **Arcade graphics code** | `arcade_code = base_tile(a4@0x1e) + dCode` (piece code) | arcade piece stream (now pre-expanded offline) |
| **B** | **Effective arcade palette bank** | the semantic bank the piece displays under; affects finalized pattern bytes | `USAGE_BANK` (static per usage) |
| **C** | **Finalized Genesis pattern identity** | `(A,B) → variant cell index vi` into `pc090oj_editor.bin` | `gen_reindexed_pc090oj.py` resolver (§4) |
| **D** | **Genesis CRAM line** | physical 16-color line the SAT entry selects | Palette Composer authored `line` + arcade attr; separate from C |

Residency (§15) keys on **C** (finalized pattern), never **A** alone. CRAM-line routing (**D**) is a
separate SAT-attribute concern, not a pattern-identity concern.

---

## 6. Shared, extensible, context-scoped semantic graphics corpus

Both the Palette Composer and the frame compiler answer the same question — *what pieces make up this
object/frame?* — and must share **one** representation, never two independent answers.

**It already exists** as the corpus TSVs that `gen_reindexed_pc090oj.py` consumes:
`analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv`,
`analysis/actor_decompilation/h24_player_weapon_cells.tsv`, the H24 player-body cell set, cave_block,
and the burst/impact effect (derived from the compositor VM — the same decompilation source the
Palette Composer uses).

```
authoritative arcade/Ghidra/census evidence
        -> context-scoped semantic graphics corpus (the TSVs; extensible)
        -> actor/object -> pose/frame -> ordered pieces -> (code, effective_bank, geometry/flip)
                 /                                    \
        Palette Composer                        native frame compiler
        (colors / index maps / line)            (geometry / finalized pattern IDs)
                 \                                    /
                      finalized native graphics
```

**The corpus may contain PARTIAL entries — that is required.** It is authoritative only for entries
backed by explicit evidence. UNKNOWN stays UNKNOWN; never fabricate an entry for table completeness
(`feedback_build_on_existing_work`, `project_living_bestiary`).

---

## 7. Three independent completeness dimensions

For each actor/family/context, track **separately** (never collapse into one "done"):

- **Palette completeness:** effective bank known? Palette Composer mapping authored? canonical
  decision present (status ∈ proven/decided/provisional)?
- **Frame completeness:** every legal pose/frame assembly known? ordered piece list? code values?
  flip/orientation behavior?
- **Selector completeness:** exactly which actor state / animation-program value / specialized
  dispatch condition / dynamic override selects which frame?

A valid state is `palette=COMPLETE, frames=PARTIAL, selector=PARTIAL` — usable for palette authoring,
**not** yet ready for native-renderer replacement. "Palette Composer knows this object" ≠ "we know
every animation this object can display."

---

## 8. Native frame format (fields fixed; binary layout frozen in Task 1 after KU-1/KU-5)

Per `(family/usage, anim_index, orientation)` the generator pre-expands the arcade piece stream
(both orientations baked; mirror neg/+0x10 and type-0x70 extra-Y folded offline):

```
frame:  u8 piece_count            ; 0 allowed; a distinct UNRESOLVED sentinel (§10) is separate
piece:  s16 dX                    ; orientation baked
        s16 dY                    ; type-0x70 extra-Y folded
        <pattern-ref>             ; see resolve mode below
        u8  size                  ; Genesis sprite size nibble (from per-code geometry / pc090oj_opaque_bbox)
        u8  flags                 ; baked pieceFlipX, attr-set(0x80), was-0x70, resolve-mode bit
```

`<pattern-ref>` has **two resolve modes** (the format carries a mode bit; §14 decides per piece):
- **Finalized (Level B):** a direct `vi` (variant cell index) into `pc090oj_editor.bin`. Used when
  `(code,bank)` is fully static for the piece (base_tile static per frame — KU-1 — and usage/bank
  known). Runtime does **zero** `(code,bank)` work.
- **Resolvable (Level A):** `(dCode, bank_tag)`; runtime computes
  `vi = group_base[base_tile+dCode] + bank_slot[bank]` via the existing §4 resolver. Used only when
  base_tile is runtime-dynamic or a frame is genuinely shared across usages/banks.

Per §13's instruction, **do not prematurely freeze field widths / the mode encoding** until KU-1
(base_tile granularity) and KU-5 (lane) are proven in Task 1. The *fields* above are stable; their
exact bytes are Task-1 deliverables.

Generated artifacts: `build/pc090oj_frame_table.bin`, `build/pc090oj_frame_index.bin`
(`(family*ANIM_MAX + anim)*2 + orientation → {offset, count}` with an UNRESOLVED sentinel),
`build/pc090oj_frame_residency.bin` (§15), `build/pc090oj_frame_table.report.txt` (coverage §25).

---

## 9. Progressive mixed-mode migration + UNRESOLVED fallback

```
actor state -> frame-index lookup
   resolved  -> precomputed frame -> finalized pattern (§4) -> residency (§15) -> SAT
   UNRESOLVED -> existing Build-0400 .Lnative_emit_actor_common  (intentional, transitional, measured)
```
The frame index carries an explicit **`UNRESOLVED`** sentinel. The runtime `native_emit_frame`
tests it first and dispatches to the legacy interpreter for that `(family,anim,orientation)`.
**Never invent a native frame for an unresolved state.** Each decompilation advance moves coverage
from runtime interpretation to offline data without any format/renderer change.

---

## 10. Hybrid residency architecture (NOT pure per-owner Sonic model)

**Proven infeasible:** a permanent per-owner VRAM union. R1/P1 displays **61–63 distinct sprite
cells simultaneously within single frames** (demon-swarm peak; evidence:
`docs/design/Andy_r1p1_sprite_semantic_completion_and_58cell_packing.md`), and per-owner unions are
far larger. The physical floor is the peak single-frame simultaneous distinct-tile count.

**Hybrid model (design to this):**
- **Fixed/permanent:** small persistent player core, HUD glyphs, tiny always-used assets.
- **Scene/family resident:** where lifetime/semantic evidence proves it safe (e.g. a continuously
  respawning family active for the whole context — lizard-men).
- **Shared bounded pool:** for large combinatorial enemy families whose simultaneous requirements
  forbid permanent allocation. Must use an **O(1) reverse lookup**, deterministic bounded
  replacement, bounded DMA, **no linear 49-slot search**, fed by generated residency hints.

Residency keys the **finalized pattern identity (§5C / `vi`)**, because the same code under bank A vs
bank B is a different Genesis cell. The allocator receives native graphics identities; it does not
understand Palette Composer policy. Precomputing frame mappings does **not** mean every graphic
resides permanently — it removes the interpretation cost, not the bounded placement work Rastan's
density genuinely requires (steady-state DMA is small; MAX ~49 patterns only at context transitions).

The existing allocator state (`sprite_tile_resident_code`, reverse directory, `pc090oj_tile_dma_worklist`)
stays; this design replaces the *per-frame derivation of what to resident* with a static manifest
lookup and upgrades the lookup to O(1) reverse-index (§15).

---

## 11. R1/P1 is the FIRST context, not a global policy

The governed production bridge currently supports **`context:gameplay.r01.p01` only**. Do **not**
auto-inherit R1/P1 Layer-A mappings, sprite palette policy, CRAM-line decisions, index maps,
coexistence assumptions, or residency packages into any other sub-round/round. The formats must
support, with **no format change**:
`gameplay.r01.p01 / r01.p02 / r01.p03 / r02.p01 / … / boss.* / frontend.*`. Every corpus/frame/
residency artifact is context-keyed.

---

## 12. PC080SN / token decoupling

The native plane system is already Genesis-native. Do not rewrite correct scroll/tilemap production
to drop historical names. Eliminate only the arcade-address vocabulary at the producer boundary:
extend `precompute_pc080sn_tile_lut.py` to emit a `cwindow_dest(0xC00000/0xC08000+off) → {plane,
genesis_dest}` LUT so the recognition hooks (`genesistan_hook_3ad44_dispatch`, strip/fill,
textwriter) replace their `cmpi/subi` chains with one indexed lookup, then retire `3ad44` per its own
"Final-Retirement Handoff". Geometry/destination and palette policy stay **separate** concerns, both
context-aware. Do not fold R1/P1 Layer-A palette policy into tile-destination mapping. Token report:

| Token | Creator | Decoded at | Freq | Native replacement | Producer-change safe? | Python? |
|---|---|---|---|---|---|---|
| `0xC00000/0xC08000+off` | arcade PC080SN writer | `hook_3ad44`, textwriter, strip/fill (~20 sites) | per cell/strip/frame | `cwindow_dest→{plane,dest}` LUT | convert at first hook (safe) | yes (extend `precompute_pc080sn_tile_lut.py`) |
| `0xD00460+idx*0x50` | arcade reg at `A5+0x1282` | `contact_coords_51ab6:829` (subi/divu) | per contact/frame | expose `actor_index` at read boundary | read-side only (safe) | no (asm) |
| `0x200000+off` | arcade palette copy | `palette_hook_45dae:304` (cmpa) + siblings | per copy/scene | arcade-pal-dest → CRAM line map | read-side (safe) | yes (small map) |

---

## 13. Native textwriter plan (own bounded task)

Replace the per-character `jsr 0x000565CE` re-entry. Observed contract (`textwriter_dispatch:3957-3988`):
`0x565CE` returns a single glyph **tile code** in `d0`, packed with attribute and written to the
decoded C-window destination. **If Ghidra confirms it is a pure static char→code map (KU-2)**,
generate `build/textwriter_glyph_lut.bin` (`char → native tile code [+size/attr]`) offline and route
the destination via the §12 cwindow LUT:
```
character -> generated glyph→native-tile LUT -> native Plane A/B destination
```
No arcade re-entry. Must reproduce exactly what `0x565CE` returned; do not change text layout.

---

## 14. Effective-bank dynamic granularity (how much pre-resolves offline)

`USAGE_BANK` proves **effective bank is static per semantic usage** — not per actor instance, not per
piece, in the proven R1/P1 corpus. Therefore, per piece:
- **Level B (best, emit finalized `vi` offline):** base_tile static per `(family,anim)` (KU-1) AND
  the frame's owning usage (→bank) known. Covers the whole proven R1/P1 corpus with static codes.
  Runtime does **no** `(code,bank)` resolve.
- **Level A (resolve once per frame):** base_tile dynamic (code unknown offline) but usage/bank known
  → runtime resolves with `bank` constant-folded to the usage bank.
- **Per-piece runtime resolve (required fallback only):** a frame genuinely shared across usages with
  different runtime banks → use the existing O(1) `(code,bank)` resolver unchanged.

Do not keep runtime `(code,bank)` work merely because Build 0400 did. Prefer Level B wherever KU-1
permits.

---

## 15. Residency keyed on finalized native patterns

```
semantic piece -> (code, effective_bank) -> finalized native cell vi (§4) -> VRAM residency
```
The generator emits per frame, in `pc090oj_frame_residency.bin`, the set of **`vi`s** the frame
needs (plus min/max and a bitset) so the runtime answers "already resident?" with an **O(1)
reverse-index** test against the current resident set — replacing any linear 49-slot scan. A resident
frame costs one lookup; a transient frame enqueues its missing `vi`s into the existing bounded
`pc090oj_tile_dma_worklist` (12×4). The allocator receives `vi`s, never raw codes, and never parses
palette policy.

---

## 16. Build dependency graph (with hashes)

```
raw arcade evidence (Ghidra / census / compositor VM)
  -> semantic corpus TSVs (context-scoped)                      [sha: corpus_sha]
  -> Palette Composer authoring (Test.json)                     [sha: profile_sha256]  (already in variant_index.json)
  -> governed/frozen profile snapshot
  -> canonical palette decisions (specs/palette_decisions.json) [sha: decisions_sha]
  -> gen_reindexed_pc090oj.py
        -> pc090oj_editor.bin + pc090oj_sprite_variants.inc + pc090oj_variant_index.json + manifest
  -> precompute_pc090oj_frame_table.py  (NEW; model: precompute_pc080sn_tile_lut.py)
        -> pc090oj_frame_table.bin + _index.bin + _residency.bin + report (coverage §25)
  -> ROM
```
Geometry that is palette-independent may be cached separately, but any field holding a **finalized
`vi`** must rebuild when its palette-compiled inputs change. Each generated report records all of:
`corpus_sha`, `profile_sha256`, `decisions_sha`, reindexed-manifest sha, and the frame-table input
hash, so stale combinations are mechanically detectable. Makefile wiring mirrors
`apps/rastan-direct/Makefile:239-265`.

---

## 17. Verification chain (layered; keep the existing palette verifier)

- **Layer 1 (palette compiler, existing):** `verify_reindexed_pc090oj.py` proves
  `(code,bank)+authored policy → correct finalized pattern bytes`.
- **Layer 2 (frame compiler, NEW):** `verify_pc090oj_frame_table.py` proves
  `actor/frame → correct ordered native pattern IDs (vi) + geometry` by an independent re-expansion,
  byte-compared to a runtime-captured reference for the pilot.
- **Layer 3 (runtime):** `vi → correct VRAM slot, SAT attribute, CRAM line, displayed sprite`
  (GENESIS NTSC MAME). Static **and** runtime proof; not screenshot similarity alone.

---

## 18. Performance model

Build 0400 per sprite (`2,609 cyc` slope): family-table lookup + descriptor resolve + self-rel
decode + piece-stream parse + control-nibble classify + orientation transform + repeated
sign-extend/add + `(code,bank)`/residency derivation + SAT.

- **Proposed Level A:** precomputed geometry, runtime `(code,bank)` resolve. Removes table/descriptor/
  stream/nibble/orientation/sign-extend work; keeps one O(1) resolve + adds + SAT.
- **Proposed Level B:** precomputed geometry **and** finalized `vi`. Removes the resolve too.

Target per-piece hot path:
```
load generated piece -> add X -> add Y -> O(1) residency check -> merge truly-dynamic attr -> SAT write
```
Fixed per-actor table/descriptor overhead vanishes (folded into one index load). The `2,609×emitted`
slope should drop materially; exact factor is the Task-1 measurement, not a pre-implementation
guarantee.

---

## 19. ROM / WRAM / VRAM tradeoffs

- **ROM ↑ (accepted):** frame tables, indices, context manifests, variant metadata (variant cells
  already exist). Tens of KB order; dedup via content hash in Python (`apply_pattern_reuse.py` model).
- **WRAM:** net neutral→reduced (no stream-parse scratch); **no** large new buffers (unlike 0401's
  snapshots); arcade WRAM untouched.
- **VRAM:** bounded by the §10 hybrid model; the manifest makes the resident working set explicit and
  auditable (`audit_vram_tile_usage.py`). Do not assume all actor art fits permanently.
- **CPU ↓ (the goal):** eliminate repeated interpretation + linear residency search.

---

## 20. Relationship to Build 0401

Independent of the sprite/preprocessing work. Reintroduce **after** producers are cheap, so the
ownership overhead fits. The 0401 patch is already isolated/preserved for clean reapplication.

---

## 21. Migration sequence (challenge-reviewed; recommended)

1. Native frame-compiler infrastructure + finalized `(code,bank)` integration.
2. Palette-Composer / native-pattern integration (shared corpus, hashes).
3. **Pilot native renderer** — ONE mature path, final format (§27 Task 1).
4. Hybrid O(1) residency integration.
5. Expand **proven** R1/P1 coverage (§28 Task 2).
6. Performance verification (the slope gate).
7. Reintroduce WORK/READY/DISPLAYED ownership (0401).
8. Eliminate/simplify the temporary full-plane snapshot.
9. Move worker scheduling outside IRQ6 — **last**, never bundled with frame conversion.
Parallel low-risk tracks: textwriter (§13), PC080SN token decoupling (§12), dead-vestige sweep (gated).

---

## 22. Cody Task 1 — final-architecture pilot (ONE numbered ROM)

- **Baseline:** Build 0400. **Pilot:** Rastan/player (most mature evidence); state exact coverage, do
  not claim the whole actor is complete if it is not.
- **Establish (FINAL model, not a prototype):** shared-corpus input; Palette Composer integration;
  final frame-table format (freeze layout here after KU-1/KU-5); finalized `(code,bank)`→`vi`
  integration via the existing resolver; fast `native_emit_frame`; hybrid residency interface;
  `UNRESOLVED` fallback; generated coverage report; independent Layer-2 verifier.
- **Python/build:** new `tools/translation/precompute_pc090oj_frame_table.py` +
  `verify_pc090oj_frame_table.py`; Makefile targets + incbin into `pc090oj_assets.s`.
- **Assembly:** new `native_emit_frame` in `pc090oj_hooks.s`; one-path dispatch gate in the player
  band of `native_stage_dispatch_41dae` only.
- **Do NOT touch:** scheduling, 0401 ownership, unrelated tilemap, unrelated palette policy,
  unresolved families. Palette policy must stay equivalent to Build 0400.
- **Acceptance:** Layer-1 verifier PASS; Layer-2 verifier PASS; exact known pilot geometry PASS;
  correct finalized variants; correct SAT palette bits; correct CRAM content/line; visual PASS;
  address/bus errors 0; measured renderer cost materially reduced; fallback correct for unresolved
  frames. **Rollback:** revert the single dispatch gate → pure Build 0400.

---

## 23. Cody Task 2 — expand proven R1/P1 coverage (ONE numbered ROM)

**Not** "convert every actor." Convert all **currently proven** R1/P1 frames/families meeting the
readiness contract (palette + frame-subset + selector completeness; `(code,bank)` correctness;
finalized-pattern correctness; residency correctness; visual/runtime equivalence). Unresolved frames
stay fallback. Produce an exact coverage matrix (§25) showing native vs fallback vs unknown. Do not
hide fallback use. Wire `pc090oj_frame_residency.bin` to the O(1) allocator; do not change allocator
data structures. HEAVY-run runtime proof; VDP ownership gate PASS; new slope measured.

---

## 24. Later migration tasks + global retirement criteria

Later tasks: textwriter (§13), PC080SN token decoupling (§12), 0401 reintroduction (§20), snapshot
simplification, scheduling move (last), dead-vestige sweep (gated on arcade call sites cut; Build
0267 precedent).

**Context-specific retirement:** when a *context* reaches proven 100% coverage, its legacy
interpretation path may be removed **for that context**. **Global deletion** of
`.Lnative_emit_actor_common` only when *every reachable consumer in the whole game* is proven
replaced (all contexts converted → zero live consumers → delete). **Never** delete because current
R1/P1 playtesting doesn't reach an unknown path ("not observed" ≠ dead).

---

## 25. Coverage matrix (generated, machine-readable)

Per object/family/**context**, track: semantic identity known? palette bank known? Palette Composer
authored? canonical decision present? complete code corpus? pose/composite data? complete legal frame
domain? runtime selector known? native frame generated? native runtime path enabled? fallback
required? Statuses: `NATIVE_COMPLETE`, `NATIVE_PARTIAL`, `PALETTE_COMPLETE_FRAME_PARTIAL`,
`GRAPHICS_KNOWN_SELECTOR_UNKNOWN`, `UNRESOLVED_FALLBACK`. **UNKNOWN is not failure — it means "do not
convert yet."** Emitted as `build/pc090oj_frame_table.report.txt` + a JSON matrix.

---

## 26. Do not confuse legacy names with legacy architecture

Many `pc090oj_*`/`pc080sn_*` symbols are now native Genesis infrastructure. Classify any touched
symbol as: arcade-coupled (scheduled for replacement) / native-with-historical-name / build-time
tooling / dead vestige. **Do not rename aggressively during implementation** — renaming is a later
cleanup; behavior and architecture come first.

---

## 27. Known unknowns (resolve before freezing the Task-1 format)

- **KU-1 (blocks §8/§14/§15):** is `base_tile` (`a4@0x1e`) a pure function of `(family,anim)`? If yes
  → Level B (emit `vi` directly, exact resident bitsets). If dynamic → Level A (runtime resolve).
  Resolve via Ghidra writers to actor `+0x1e` (+ whether anim-select sets it) + one watchpoint.
- **KU-2 (blocks §13):** exact `0x565CE` contract — pure static char→code, or dynamic state? Ghidra.
- **KU-3:** specialized-dispatch sprite types (0x10..0xC0) reachable in later stages/bosses? If so the
  generator must expand `a4@0x0B`-indexed specialized frames (format already supports it).
- **KU-4:** the actor→usage→bank runtime mapping. `USAGE_BANK` is static per usage, but `a4@0x38`
  family is a *bucket, not identity* (`project_actor_identity_and_census`: 36 distinct bases via
  `0x45502/0x45562/0x454ba`, +0x3E bucket, +0x752 variant; per-round palette `0x3BA88→0x4FD02`).
  Confirm how the runtime resolves an actor instance to its usage/bank (sprite-ctrl colour-bank
  shadow + per-round palette) before Task 2 claims multi-family coverage.
- **KU-5:** `native_sprite_lane` ordering (append order = priority) must be preserved exactly; confirm
  lane assignment is purely per-band from the three callers, carried as a runtime input.

---

## REQUIRED ANSWERS BEFORE CODY IMPLEMENTS

1. **Shared corpus?** The existing context-scoped semantic corpus TSVs
   (`analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv`, `h24_player_weapon_cells.tsv`, the
   H24 player-body set, cave_block, compositor-VM burst) — the same inputs `gen_reindexed_pc090oj.py`
   already consumes. Both the Palette Composer and the new frame compiler read these; no second corpus.
2. **Incomplete/unknown representation?** Corpus entries are per-(object,context) and may be partial;
   absent poses/frames/selectors are simply not present, and the frame index emits `UNRESOLVED` for
   them. The coverage matrix (§25) records exactly which dimensions are known. No fabricated entries.
3. **Ready for native conversion today?** Rastan/player (H24 body + 4 weapons) has mature palette +
   pose evidence → the Task-1 pilot. Non-divergent-code enemies with authored index_maps are
   candidates for Task 2 **per frame/selector readiness**, not wholesale.
4. **Palette-known but frame/selector-incomplete?** The enemy families whose `USAGE_BANK`/index_maps
   are authored (lizardman, valkyrie, chimera, flying_demon, four_armed, bats) but whose *complete
   legal frame domain and runtime selectors* are not yet enumerated → `PALETTE_COMPLETE_FRAME_PARTIAL`
   / `GRAPHICS_KNOWN_SELECTOR_UNKNOWN`. Confirm per family against the corpus before converting.
5. **Bank granularity?** **Static per semantic usage** (`USAGE_BANK`) — not per actor instance, not
   per piece (proven R1/P1). A *code* shared across usages needs that usage's bank; within one frame
   of one usage, bank is a compile-time constant. (Runtime actor→usage mapping = KU-4.)
6. **Where can Python emit finalized `vi` directly?** Any piece whose `(code,bank)` is fully static —
   i.e. base_tile static per `(family,anim)` (KU-1) and usage/bank known. Expected to cover the
   proven R1/P1 static-code corpus (Level B).
7. **Where must runtime `(code,bank)` resolution remain?** Only where base_tile is runtime-dynamic
   (Level A, bank constant-folded) or a frame is genuinely shared across usages with different runtime
   banks (full O(1) resolve). Not elsewhere.
8. **Canonical `(code,bank)→pattern` resolver?** `apps/rastan-direct/out/pc090oj_sprite_variants.inc`
   (`vi = pc090oj_variant_group_base[code] + pc090oj_variant_bank_slot[bank]`) over
   `build/regions/pc090oj_editor.bin`, generated by `gen_reindexed_pc090oj.py`, indexed by
   `build/regions/pc090oj_variant_index.json`. Reuse unchanged.
9. **Residency keys finalized patterns how?** The frame-residency artifact lists each frame's set of
   `vi`s (§15); the allocator keys/looks up by `vi`, never by raw arcade code. Same code under
   different banks = different `vi` = different residency entry.
10. **Shared pool without linear search?** An O(1) reverse index `vi → resident slot` (and
    slot→vi) with deterministic bounded replacement and bounded DMA, replacing the linear 49-slot
    scan; generated residency hints prioritize which `vi`s to keep resident per context.
11. **Permanent vs shared/transient?** Permanent: player core, HUD glyphs, tiny always-used assets.
    Scene/family-resident: lifetime-proven families (e.g. lizard-men). Shared bounded pool: large
    combinatorial enemy families (demon-swarm peak 61–63 cells) that cannot be permanently unioned.
12. **Palette edit → rebuild propagation?** The Makefile dependency chain (§16): editing `Test.json`
    changes `profile_sha256` → `gen_reindexed_pc090oj.py` rebuilds `pc090oj_editor.bin`/variant index
    → `precompute_pc090oj_frame_table.py` (which depends on the variant index for finalized `vi`s and
    the corpus) rebuilds frame/residency data → ROM relinks. No manual sync.
13. **Hashes/manifests against stale combos?** `profile_sha256` (already in `pc090oj_variant_index.json`),
    `corpus_sha`, `decisions_sha` (`specs/palette_decisions.json`), reindexed-manifest sha, and the
    frame-table input hash — all recorded in each generated report; a mismatch fails the build.
14. **Add an actor six months out without architecture change?** Add corpus evidence (identity →
    context → bank(s) → pieces → selectors), author/promote palette policy, let
    `gen_reindexed_pc090oj.py` compile any new `(code,bank)` variants, let
    `precompute_pc090oj_frame_table.py` emit its frames, flip its matrix entry to enabled. No new
    renderer/format/palette/residency system.
15. **Later contexts (R1/P2, later rounds) without R1/P1 inheritance?** Everything is context-keyed
    (§11); each context carries its own corpus slice, Layer-A package, palette policy, CRAM-line
    decisions, and residency hints. R1/P1 is the first instance of the generalized model, inherited by
    nothing automatically.
16. **UNRESOLVED sentinel/fallback contract?** `pc090oj_frame_index.bin` stores a reserved sentinel
    (e.g. `count=0xFF` / offset `0xFFFFFF`) for any `(family,anim,orientation)` without proven native
    data; `native_emit_frame` tests it first and tail-calls the existing `.Lnative_emit_actor_common`
    for that actor, unchanged. Byte-identical to Build 0400 on the fallback path.
17. **When may a context stop using the legacy path?** When its coverage matrix shows every reachable
    `(family,anim,orientation)` in that context is `NATIVE_COMPLETE` with Layer-1/2/3 proof — then the
    context's dispatch may bypass the interpreter.
18. **When may the legacy path be deleted globally?** Only when *all* contexts reach that state and the
    interpreter has zero live consumers game-wide (per "replace every live consumer first"; never on
    "not observed in current playtesting").
19. **Cody's first exact steps?** (a) Resolve KU-1 (base_tile granularity) and KU-5 (lane) for the
    player; (b) write `precompute_pc090oj_frame_table.py` consuming the corpus + variant index, emit
    player frames (both orientations) with finalized `vi` where KU-1 permits, UNRESOLVED elsewhere;
    (c) write `verify_pc090oj_frame_table.py`; (d) implement `native_emit_frame` + the player-band
    dispatch gate + UNRESOLVED fallback; (e) Makefile + incbin; (f) run Layer-1/2/3 proofs; (g) emit
    one numbered ROM + coverage report.
20. **What NOT to touch in Task 1?** Scheduling/IRQ6; Build 0401 ownership material; unrelated
    tilemap/PC080SN code; palette policy (must stay equivalent to Build 0400); all non-player /
    unresolved families (they stay on the fallback); the `(code,bank)` resolver internals; A5-WRAM.

---

*No production source changed. No ROM produced. Build 0401 material untouched. The objective is the
final extensible architecture now, compiling more of the game into it as reverse engineering
advances — unknown graphics stay on the proven Build-0400 fallback. No guessing, no fake completeness,
no duplicated palette policy, no new PC090OJ/PC080SN abstraction.*
