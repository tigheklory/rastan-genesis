# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0114 — Round-1 Plane-A residency architecture recovery

**Author:** Andy · **Date:** 2026-11-09 · **Type:** analysis / documentation archaeology. **No production
source, generator, profile, Makefile, binary, ROM, or build-number change.** Baseline Build 0560 untouched;
counter unchanged. This recovers the proven Round-1 native Plane-A residency architecture from the repository
and determines how Round 2 should extend it.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0114`

---

## Executive conclusion

**YES — Round 1 already solved this, and Round 2 should reuse the same architecture unchanged in shape.**

The native Plane-A system is a complete **offline-precompute residency engine**: the arcade progression record
is mapped to a graphics *epoch*; each epoch carries a compiler-reconstructed, complete, exact-32-byte pattern
vocabulary and a code→slot LUT; records inside one epoch change with **zero** DMA/remap/eviction; and the two
genuinely hard screen-to-screen handoffs (rope→waterfall, waterfall→next) are served by bounded **transition
overlap packages** that keep the outgoing visible patterns in their existing slots while adding the incoming
ones. This *is* Tighe's "ROM holds all epoch data; WRAM holds current + incoming working state" model — it is
already implemented, just under different names (stable package / transition package / active LUT).

The PROMT-ID-0113 "scratch collision" is **not** a new architectural problem and **not** a reason to build two
20 KB LUTs or redesign anything. It is a single **R1-only numeric-range assumption** exposed by R2: R1's real
arcade Plane-A tile codes all sit **below 0x1600**, so the compiler parks its transition scratch in the
`[0x1600, 0x2800)` hole of the active LUT; R2's real arcade FG tile codes `0x24BB..0x24C2` (9403..9410) sit
**inside** that hole, so the long-standing Build-0308 guard "transition scratch overlaps a legal code" correctly
refuses. The smallest correct R2 extension is to give the scratch a hole that is empty for the active round
(or move it out of the dense-code LUT entirely) — a placement fix, not an architecture.

---

## Historical timeline (build/commit chronology)

| Build | What it established (Plane-A residency line) |
|---|---|
| 0293–0295 | PC080SN semantic-mismatch analysis; tilemap translation is intent→VDP-owner, not callsite patches (`pc080sn_tilemap_architecture.md`, `pc080sn_semantic_mismatch_analysis_build29*.md`). |
| 0297 | Native PC090OJ sprite path; object-RAM compatibility renderer removed (preserved note in 0308). |
| 0301–0303 | Streaming PC080SN tile residency; **exact 32-byte pattern identity** becomes the allocation unit (not arcade-code equality). |
| 0307 | Full-VRAM 2-D epoch review; selective Plane-B Y-envelope widening for the rope (records 2–3 take a 64-row single-variant envelope). |
| **0308** | **Zero-drop per-record Plane-A residency + fixed 854-pattern Level-1 Plane-B.** Compiler emits one package per record; A band = slots 855–1338 (cap 484); sprites 1339–1534. Scratch uses the "statically empty LUT word range 5632–7969". Still display-off per A transition (no-black not done). |
| 0309 | 0308 gameplay-entry crash fix (68000-safe pointer construction; package alignment/range guards). |
| **0310** | **Seven complete-residency epochs** replace 16 per-record packages. `record_to_epoch = 0,0,0,1,2,2,2,2,2,2,3,4,5,5,5,6`. `fg_boundary_install` returns early if the epoch is already active → within-epoch DMA/evict/churn = 0. Exhaustive DP proves 7 is the minimum at cap 484. |
| **0311** | **Transition overlap packages 7 & 8** for rope→waterfall (rec 2→3) and waterfall→next (rec 3→4); reclaim at logical column 45 via `fg_boundary_transition_step`. Introduces the **writable `fg_boundary_active_lut`** (0x2800 words, WRAM) and the **transition scratch** inside it; adds the 50-word `fg_boundary_conflict_lut` for a WRAM address collision. (git: active LUT + scratch + `BOUNDARY_LUT_WORDS` all first appear in commit `c8adf2a4` "Build 311".) |
| 0312 | Round-1 Phase-1 Plane-A completion checkpoint (publication defect fix). |
| 0315–0316 | **Palette Composer Layer-A integration.** Authored (editor-policy) reindexed patterns become the physical input; dedup/packages/uploads computed from the FINAL reindexed 32-byte bytes; Plane-B byte-identical; authored palette on the Layer-A line. |
| 0341 | OPT-003 completion + epoch-gate robustness. |
| **0342** | **Clean 676-slot contiguous Plane-A repack.** A band decoupled to contiguous slots **663–1338 (676)**; Plane-B 854 repacked into `[1–662] ∪ [1664–1791] ∪ [1920–1983]`; epochs recomputed to **5 stable** `((0-2),(3),(4-10),(11-12),(13-15))`; both streamed transitions preserved; `record_to_package = [0,0,0,5,6,2,2,2,2,2,2,3,3,4,4,4]`. This is the shape in Build 0560. |
| 0349–0352 | Sonic-style / live-scroll Plane-A streaming experiments (edge streaming, shared-live resolver) — explorations, not the accepted residency model. |
| 0362–0400 | Rope segment-5 visibility, missing rope blocks, segment 10/11/12 transitions — per-screen residency corrections on top of the epoch model. |
| 0417–0439 | Full-span logical background correctness; VDP DMA 128 KiB-boundary safety; Plane-A column/selector segment hoist (perf). |
| 0525–0538 | R1-S2 respawn/boundary fixes; natural Round-1 transitions. |
| 0560 | Current accepted baseline (profile `Test_2_0`, PROMT-ID-0112). |

---

## Original architectural goals

From `pc080sn_tilemap_architecture.md`, `final_block_write_and_scene_scoped_tile_loading_architecture.md`,
and the 0308/0310 docs, the goals were explicit and still hold:

- **Offline precompute, O(1) runtime.** Build-time Python assigns every pattern a VRAM slot; runtime does a
  single LUT lookup. **No runtime allocator, search, LRU, hash, eviction, miss-DMA, per-frame residency scan,
  or software PC080SN device.** (0310: "adds no runtime allocator, search, LRU…".)
- **Exact 32-byte pattern identity** is the allocation unit; arcade-code equality is *not* pattern equality.
- **Mirror the arcade semantic decision, replace only the chip-specific tail.** The retained cut is the arcade
  progression record (`A5+0x13E`) and selector-0 source/scroll; the replaced tail is PC080SN destination/write.
- **Complete residency per epoch** → zero in-epoch work; **bounded transition packages** only where a real
  screen handoff keeps outgoing patterns on-screen while incoming ones arrive.
- **No black frames / no drops** as the correctness bar (zero Plane-A drops for every record/epoch).

---

## ROM-resident data

Every *epoch-specific* lookup/pattern datum is immutable and ROM-resident (generated by
`tools/translation/compile_pc080sn_genesis.py` into `build/pc080sn_boundary/boundary_packages.bin` +
`boundary_constants.inc`):

| Structure | Represents | Immutable? | Selected | Size / scope |
|---|---|---|---|---|
| `record_to_epoch` (`record_table`) | arcade record → stable epoch id | yes (ROM) | per record change | 16 (R1) entries; per-round |
| `record_to_package` | arcade record → *package* (stable epoch or transition pkg 7/8) | yes (ROM) | per record change | 16 entries; per-round |
| stable epoch packages 0..N | one epoch's complete code→slot map + pattern uploads + identity list | yes (ROM) | on epoch entry | 5 pkgs at 0342; per-epoch |
| transition/overlap packages (7,8) | bounded 2-D overlap: outgoing-visible retained slots + incoming-only safe slots | yes (ROM) | on entering a streamed-transition record | 2 pkgs; per-transition |
| reindexed pattern ROM (`genesistan_pc080sn_tile_rom` / editor region) | final 32-byte Genesis pixels (authored reindex applied) | yes (ROM) | DMA source at install | per-pattern |
| `pc080sn_tile_vram_lut` / attr LUT | global code→slot + attr bits (strip/block/text) | yes (ROM) | always | 16384 / 32 entries; global |
| `FG_BOUNDARY_*` equs (`SLOT_FIRST=663`, `SLOT_COUNT=676`, `LUT_WORDS=0x2800`, `SCRATCH_WORD=0x1600`) | geometry constants | yes (ROM) | build-time | scalars |

**"Immutable" means:** within an epoch, a logical arcade code maps to **exactly one** physical 32-byte pattern
identity; the compiler raises `logical code 0x%X changes physical identity inside epoch` if any record in the
epoch disagrees (`compile_pc080sn_genesis.py:663-666`). The epoch's pattern vocabulary and code→slot map never
change while that epoch is active — that is the whole basis of the zero-in-epoch-work guarantee.

## WRAM-resident data

Exactly one mutable runtime structure, plus its transient scratch:

| Structure | Represents | Rebuilt? | Copied | Cleared | Size / scope |
|---|---|---|---|---|---|
| `fg_boundary_active_lut` (`.bss`, `fg_tile_cache.s:756`) | the **current** epoch's live code→slot LUT (dense, indexed by raw arcade tile code) | yes, on epoch/transition install | from the selected ROM package | on install (cleared then repopulated) | `0x2800` words = **20 KB**; one global buffer, holds the active epoch |
| identity scratch (`fg_boundary_active_lut + FG_BOUNDARY_IDENTITY_SCRATCH`, base `SCRATCH_WORD*2`) | during a transition install: incoming-vs-outgoing identity bookkeeping | transient per install | — | per install | `len(pattern_id)` words, inside the active-LUT hole |
| slot-translation scratch (`+ FG_BOUNDARY_SLOT_TRANSLATION_SCRATCH`) | during install: old-slot→new-slot translation for retained identities | transient per install | — | per install | `a_slot_count` (676) words, inside the hole |
| `fg_boundary_conflict_lut` (WRAM `0xFFB1CC`, 50 words) | 0311 bounded relocation for codes `0x031A..0x034B` that collided with a WRAM crash-record area | fixed | — | — | 50 words; global |

The active LUT is the **only** per-epoch mutable table. The two scratch regions are *transient install-time
working buffers* that were deliberately parked in an unused tail of the same 20 KB buffer (see "Why" below).

---

## Plane-A epoch model

- Records are partitioned into **contiguous epochs**; each epoch's complete pattern union must fit the Plane-A
  slot capacity (484 at 0308/0310/0311; **676 at 0342/0560**).
- `record_to_epoch` selects the epoch; `fg_boundary_install` installs it. **If the requested record's epoch is
  already active, the installer updates only the active record/variant and returns before any descriptor walk,
  interrupt mask, display-off, LUT rebuild, remap, or pattern DMA** (0310 "Runtime contract"). Hence several
  records share one epoch with **no graphics reload** — the answer to "why several records share an epoch."
- The epoch count is a *deliberate* choice, not a minimum: 0342 keeps 5 (not the global DP minimum 4) precisely
  so that records `0-2 | 3` stay split and **both proven streamed transitions survive**
  (`compile_pc080sn_genesis.py:638-641`).

## Stable packages

A stable package is an epoch's complete, self-sufficient residency: the full code→slot map, the pattern upload
list (ROM offset → slot), and the identity list. Installing it makes the epoch's entire vocabulary resident.
Within the epoch nothing further is uploaded.

## Transition / overlap packages

Only where a real on-screen handoff occurs (rope→waterfall, waterfall→next) does the compiler emit a bounded
**overlap package** (packages 7, 8). Each:

- preserves **all** outgoing *visible* identities in their **existing slots** (zero slot movement — proven
  byte-for-byte in `Cody_build0311_*`: rope 12 identities, waterfall 224 identities, slot movement 0);
- adds only the **incoming-only** required identities into safe free slots;
- is sized to the **exact 2-D legal overlap window** (40-col display window × all 64 legal rows), not the whole
  epoch union — rope peak 394, waterfall peak 479, both ≤ cap;
- is retired at a **precomputed safe handoff column (logical column 45)** by `fg_boundary_transition_step`,
  which swaps the overlap package for the incoming stable package.

## Current / incoming residency lifetime

This is exactly Tighe's model, already realized:

- **Current epoch** = whatever the active LUT currently holds (ROM stable package installed).
- **Incoming epoch** during a streamed transition = the overlap package (packages 7/8), which holds *outgoing
  retained + incoming-only* simultaneously, bounded to what is legally on-screen.
- **Handoff** = at column 45 the incoming stable package becomes authoritative; outgoing-only slots are
  reclaimed only then.
- **Outgoing state afterward** = discarded/overwritten by the next epoch's install.

So "current + incoming coexist, outgoing is discarded after handoff" is **already** the implemented lifetime.
It is expressed as *stable package + overlap package + record_to_package + column-45 handoff*, not as a literal
double-buffer of two full LUTs.

---

## LUT architecture

There is **one** runtime LUT (`fg_boundary_active_lut`, 20 KB WRAM), **densely indexed by raw arcade tile
code**, holding the active epoch's code→slot mapping. All the real per-epoch data lives in ROM packages; the
active LUT is just the installed working copy of the current package. The dense-by-raw-code indexing is the
only reason the LUT is 20 KB (`0x2800` words covers codes up to 0x27FF): it trades RAM for an O(1)
`slot = active_lut[code]` with no hashing. The strip/block/text paths use the separate global ROM
`pc080sn_tile_vram_lut`; the boundary active LUT is the Plane-A residency overlay on top of that.

## Why `fg_boundary_active_lut` exists

1. **Introduced:** Build 0311 (git `c8adf2a4`). The *concept* (a per-epoch code→slot table) existed at 0308 as
   the "statically empty LUT word range"; 0311 named it, sized it `BOUNDARY_LUT_WORDS=0x2800`, and placed it in
   WRAM `0xFF61CC`.
2. **Problem it solved:** a transition needs to rewrite Plane-A name words through a code→slot map that differs
   from the one that produced the currently displayed cells. A ROM table cannot be edited in place during the
   overlap; the active LUT is the **mutable installed copy** of the current package so the resolver/installer
   can rewrite and retire slots atomically at the handoff.
3. **Final or convenience?** The 0311 doc is explicit: the package/LUT installer "remains an explicitly
   isolated **transitional compatibility structure**… not a virtual PC080SN memory device… This task did not
   broaden or promote that structure into the final architecture." So the *active LUT as installed overlay* is
   the working mechanism, but it is self-described as transitional, and CLAUDE.md's target shape wants the
   legacy tail to keep shrinking.
4. **Was ROM-resident per-epoch LUT the intent instead?** The *epoch data* is ROM-resident (packages). The
   **active working copy** is deliberately WRAM because it is rewritten during install/handoff. Both coexist by
   design: ROM = immutable epoch data, WRAM = current working copy.
5–6. **Did later work replace it?** No. 0342 repacked slots but kept the same active-LUT mechanism.
7. **Is 20 KB required?** Only by the **dense raw-code indexing**, not by residency semantics. A sparse or
   per-round-based index would be far smaller; the 20 KB buys branchless O(1) lookup.
8. **Scratch-in-LUT intended as temporary?** **Yes, explicitly.** 0308: "The temporary identity and
   slot-translation tables use the statically empty LUT word range 5632 through 7969; legal-code overlap is
   zero." It was a deliberate optimization to reuse the LUT's unused tail instead of allocating a separate
   buffer.
9. **Did docs flag the scratch as separable?** The installer/LUT is repeatedly flagged as a *transitional*
   structure (0311). I did **not** find a doc that explicitly says "move the scratch to its own buffer," but the
   transitional framing plus CLAUDE.md's shrink mandate make separation consistent with recorded intent.

## Transition scratch history

- Born inside the active LUT at 0308 as the "statically empty LUT word range" (words 5632–7969), chosen because
  **R1's real arcade Plane-A codes are all below that range**, so the hole was provably free of legal codes.
- Formalized at 0311 as `FG_BOUNDARY_IDENTITY_SCRATCH` + `FG_BOUNDARY_SLOT_TRANSLATION_SCRATCH`, based at
  `FG_BOUNDARY_SCRATCH_WORD` (`0x1600`), sized `len(pattern_id) + a_slot_count` words
  (`compile_pc080sn_genesis.py:1003-1004`).
- Guarded from the start: the compiler fails if the scratch overlaps a legal code
  (`:1005-1010`; `occupied_codes` = Plane-B codes + each record's real `seg_fg_tiles`). This is the exact guard
  PROMT-ID-0113 tripped on R2.

## 676-slot VRAM repack

Build 0342 decoupled the Plane-A band from Plane-B's end and pinned it to a **contiguous 663–1338 (676
slots)**, repacking Plane-B's 854 patterns into three legal gaps. This raised the per-epoch capacity 484→676,
collapsed 7 epochs → 5 (both streamed transitions retained), and shrank the generated package binary. 0560 runs
this layout. (`Andy_clean_vram_repack_676_contiguous_layerA.md`.)

## Rope / waterfall transition implementation

Step-by-step, from `Cody_build0311_*` (proven, gated):

1. Active stable epoch before: epoch A (records 0–2) resident.
2. Incoming patterns determined **offline** by reconstructing the record's original 64×64 selector-0 map over
   the 40-col legal window × 64 legal rows (no fixed viewport assumption).
3. Overlap package generated offline = outgoing-visible ∪ incoming-required, with outgoing kept in-slot.
4. Retained slots: all outgoing-visible identities keep their existing slots (movement = 0).
5. Incoming-only identities uploaded into safe free slots.
6. Old patterns remain resident through the overlap (that was the 0311 fix — 0310 wrongly overwrote outgoing-
   only cells still referenced by the name table at `.Linstall_remap_plane_store: move.w %d0,(%a0)`).
7. Names translated through the active LUT / slot-translation scratch.
8. At the handoff column (45) `fg_boundary_transition_step` swaps overlap package → incoming stable package.
9. Incoming stable package becomes authoritative there.
10. During overlap, the active LUT holds the overlap package's combined map.
11. After handoff, outgoing-only slots are reclaimed; next epoch install overwrites.

**Round 1 already has an effective current+incoming residency mechanism** — this is it.

## Waterfall pattern consolidation

The R1-S1 tile-pressure relief Tighe remembers is the **exact-32-byte-pattern dedup that is intrinsic to the
compiler**, not a waterfall-specific hack: identity is the final 32-byte pattern, so any two usages (including
visually similar waterfall tiles) that resolve to identical bytes **share one slot automatically**. After the
0316 authored reindex, dedup is computed on the FINAL reindexed bytes, so editor reindexing legitimately
changes (shrinks) the per-epoch unions (`compile_pc080sn_genesis.py:673-679` downgrades the hardcoded
`expected_epoch_counts` to an informational note in candidate mode). The consolidation is therefore **offline,
generic, and automatic** — it changes *physical pattern identity sharing*, not logical tile codes, and every
epoch benefits without special-casing. (This is also why PROMT-0113 found R2-S1 has only ~37 near-dups and 1
exact dup: dedup already captured the exact matches; the remaining win for R2 is *per-segment epochs*, exactly
like R1.)

## Record / segment / epoch semantics

- **arcade segment** = the selector-0 source table index (`FG_SRC_BASE + i*FG_SRC_STRIDE`); supplies the raw
  64×64 cell map.
- **record** = arcade progression record (`A5+0x13E`); the retained semantic authority for *which* screen.
- **epoch** = compiler grouping of contiguous records sharing one complete resident vocabulary.
- **visual scene / subround** = palette/asset context (R1-S1 outdoor, S2 castle, S3 boss); drives the authored
  palette + scene-select asset, **separate** from residency epochs.
- **palette asset** = the authored Line-0/1/3 blob installed per scene (`vdp_install_test_lines`).
- **transition package** = the bounded overlap between two epochs at a streamed handoff.

The **arcade progression record is the single semantic authority**; epochs/packages are a downstream offline
grouping of it. Several records share an epoch because their complete pattern unions coincide within capacity,
so no reload is needed.

---

## Build 0560 current state versus historical design

| R1 historical mechanism | Original intent | Current 0560 implementation | Still correct? | Evidence |
|---|---|---|---|---|
| Epoch grouping | contiguous records → complete-residency epoch | 5 stable epochs at cap 676 (`BOUNDARY_ROUND1_EPOCH_RECORDS`) | **Yes** | `compile_pc080sn_genesis.py:220,637`; 0342 doc |
| Stable package | full code→slot + uploads per epoch, ROM | `boundary_packages.bin` stable pkgs | **Yes** | 0310/0342 |
| Transition package | bounded overlap, outgoing in-slot + incoming | `TRANSITION_DEFS` → pkgs; `record_to_package` | **Yes** | `:247`, 0311 |
| ROM package storage | immutable epoch data in ROM | `boundary_packages.bin` + constants | **Yes** | 0310/0311 |
| Active lookup | one WRAM working copy of current package | `fg_boundary_active_lut` 0x2800w `.bss` | **Yes** (transitional) | `fg_tile_cache.s:756` |
| Transition scratch | transient install buffer in unused LUT tail | `scratch_word=0x1600`, sized `len+676`, guarded | **Yes for R1; R1-only range assumption** | `:1001-1010` |
| Pattern identity | exact 32-byte bytes, post-reindex | dedup on reindexed region | **Yes** | 0316 |
| Slot translation | retained identities keep slots | slot-translation scratch + in-slot retention | **Yes** | 0311 |
| Current/incoming handoff | overlap pkg → stable pkg at column 45 | `fg_boundary_transition_step` | **Yes** | 0311 |
| Plane-B ownership | fixed 854, byte-identical, Line 2 | repacked `[1-662]∪[1664-1791]∪[1920-1983]`, Line 2 reserved | **Yes** | 0342; 0316 §14 |
| Plane-A slot range | contiguous 663–1338 (676) | `a_slot_first=663`, `a_slot_count=676` | **Yes** | `:565-569` |
| No-runtime-LRU rule | no allocator/search/LRU/eviction | none present | **Yes** | 0308/0310 |

**No drift.** Every proven R1 mechanism is intact in 0560. The only thing R1 never had to handle is a round
whose real arcade codes extend into the `[0x1600,0x2800)` scratch hole — because only R1 existed natively.

---

## PROMT-ID-0113 scratch-collision reinterpretation

1. **Is it exposing an R1-only assumption?** **Yes.** The scratch sits at word `0x1600` because R1's real
   arcade Plane-A codes are all `< 0x1600`, making `[0x1600, 0x2800)` a provably empty hole (0308's "statically
   empty LUT word range"). R2's real arcade FG tile codes `0x24BB..0x24C2` land *inside* that hole, so the
   Build-0308 guard `transition scratch overlaps legal LUT codes` fires. Same guard, doing its job.
2. **Was the solution already documented?** The *mechanism* (choose a scratch hole provably empty of the active
   round's legal codes) is documented at 0308. The specific case of a second round whose codes invade R1's hole
   was never needed, so no ready-made relocation exists — but the principle does.
3. **Should R2 use the same package/transition architecture without enlarging the global LUT?** **Yes.** R2
   gets its own `record_to_epoch`, `record_to_package`, stable packages, and (if needed) streamed-transition
   packages — identical shape to R1. No global R1+R2 mega-LUT is required.
4. **Does the current active-LUT/scratch arrangement depart from the intended architecture?** Only in the sense
   the 0311 doc already admits: the active LUT + in-LUT scratch is a *transitional* convenience. It is correct
   for R1; it just embeds an R1-specific empty-range assumption.
5. **Is any redesign necessary?** **No residency redesign.** A **scratch-placement fix** is necessary: either
   (a) base the scratch at a hole empty for the active round (a per-round `SCRATCH_WORD`, e.g. above the active
   round's max legal code), or (b) move the two scratch regions into their own small transient WRAM buffer
   (`len(pattern_id)+676` words) outside the dense-code LUT. Option (b) also advances CLAUDE.md's shrink
   mandate and removes the assumption permanently.
6. **Smallest extension of the proven R1 mechanism for R2:** add R2's three authored scenes + epoch records +
   transition defs to the generator; relocate the transition scratch out of the shared-with-legal-codes hole;
   wire the runtime per-round scene-select/palette/gates R2-additively. Nothing else.

---

## Re-evaluate the "two LUTs" question

R2 does **not** need two 20 KB buffers. What must coexist during a transition is already minimal and already
coexists: **the current stable package's active map + the incoming overlap package's additions**, bounded to
the legal on-screen window (peaks ≤ cap). The lifetime Tighe cares about (only current + incoming) is satisfied
by one active LUT holding the overlap package during the handoff, then the incoming stable package. The only
genuinely new RAM need for R2 is the transient scratch *if it is moved out of the LUT* — `len(pattern_id)+676`
words, transient, not a second full LUT. **Do not add a symmetric second 20 KB buffer.**

---

## R2 minimal extension (recommended, NOT implemented here)

1. **Generator** (`compile_pc080sn_genesis.py`):
   - Add the three R2 scenes to `AuthoredLayerA.SCENES` (`PAL-R2-S1-PLANEA-OUTDOOR` rec 23–38,
     `PAL-R2-S2-PLANEA-CASTLE` 39–44, `PAL-R2-S3-PLANEA-BOSS` 45), consuming Test 2.0's existing
     `plane_usage_palette_mappings`.
   - Add `BOUNDARY_ROUND2_EPOCH_RECORDS` as a finer split proven ≤676 (PROMT-0113: `23-32/33-38/39-45` →
     586/606/425).
   - **Relocate the transition scratch** so it is empty of the *active round's* legal codes — preferred: move
     the identity + slot-translation scratch to their own transient WRAM buffer (new `.bss`, `len+676` words),
     dropping the `0x1600`-in-LUT placement; update `FG_BOUNDARY_SCRATCH_WORD` usage in `fg_tile_cache.s`
     accordingly. This removes the R1-only assumption for good and is R1-safe (R1 patterns unchanged; only the
     scratch base moves).
2. **Palette install** (`vdp_comm.s`, `palette_hooks.s`): `.incbin` the three R2 Line-0/1/3 blobs (Line 0 ==
   player palette already); extend `diagnostic_palette_asset_ptrs` 3→6 and the scene-select for stages 23–45.
3. **Native FG residency** (`scene_load.s`, `tilemap_hooks.s`): generate R2 epoch residencies; extend the R1
   round gate (`cmpi.w #23`) R2-additively so stages 23–45 install R2 packages while R1 stays byte-identical.
4. **Verify** per the proven R1 gates (epoch gate, transition-retention, canonical) plus MAME visual.

---

## Eight unmapped R2 usages

**Real authoring problem: UNPROVEN — and most likely NOT a blocker.** Evidence:

- The generator already has a defined, non-dropping path for unmapped usages: when a usage has no Test 2.0
  mapping, `AuthoredLayerA.__init__` records it in `raw_required[record]` and `resolve()` returns
  `(code, raw arcade pattern bytes, line 3, None)` (`compile_pc080sn_genesis.py:96-100,140-141,149-151`). So an
  unmapped usage renders with its **raw arcade pattern on palette Line 3** — the default — exactly as R1's own
  unmapped usages do. §27 "no dropped usages" is satisfied by this fallback.
- R1 itself has unmapped usages handled this way (the `self.unmapped` counter is nonzero for R1), so R2's 8 are
  the *same class*, not a new gap.
- Codes `0x0020` and `0x00AD` are low/common codes (candidates for blank/shared/structural tiles). To *prove*
  they need authoring, one would check whether their raw patterns are non-blank and visibly render in R2-S1 —
  but even then, raw-on-Line-3 is a valid, non-dropping realization, identical to R1.

Conclusion: these 8 are a palette-authoring-layer refinement, not a residency blocker, and **do not require
bothering Tighe** before implementation. If, after R2 renders, those specific tiles look wrong, they can be
authored in the Composer then.

---

## What should NOT be redesigned

- The offline-precompute residency engine (epochs, packages, record_to_epoch/package).
- The exact-32-byte pattern identity + automatic dedup (the "consolidation").
- The transition/overlap package + column-45 handoff mechanism.
- The single active-LUT-as-installed-working-copy model.
- Plane-B byte-identity, Line-2 reservation, 676-slot Plane-A band.
- The no-runtime-allocator/LRU rule.

Do **not** build: a second 20 KB LUT, a runtime allocator/LRU, a shadow tilemap, runtime pixel conversion, a
new R2 renderer/streaming engine, or an R1+R2 mega-LUT.

---

## Exact recommended next implementation task

**One task, R2-additive, R1 byte-identical:** extend `compile_pc080sn_genesis.py` with the three R2 authored
scenes and the proven finer R2 epoch split, **and relocate the transition identity/slot-translation scratch
out of the shared `0x1600` LUT hole into its own transient WRAM buffer** (removing the R1-only empty-range
assumption), then wire the R2 palette-install/scene-select/round gates additively. Validate with the existing
R1 epoch + transition-retention + canonical gates (must stay PASS and R1 byte-identical) and MAME visual on
R2-S1/S2/S3 direct ROMs. Start with the smallest R2 scene (S3 boss, 200 uses) to validate the full native path
before R2-S1's tight outdoor split. The 8 unmapped R2-S1 usages ride the existing raw-on-Line-3 fallback; no
pre-authoring required.

---

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0114`
