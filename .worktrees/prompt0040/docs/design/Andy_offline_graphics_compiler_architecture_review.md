# Andy — Offline PC080SN→Genesis Graphics Compiler: Architecture Review

**Type:** review/feedback only. No production change, no ROM, Build 0302 not consumed. Baseline Build 0301.

## Verdict up front
The direction is **right**, and it is what Build 0301's evidence already points to: the runtime hash/cache/
liveness/eviction is re-deriving *at 60 Hz* what is almost entirely knowable at compile time, which is why it
is slow. But the honest architecture is **HYBRID, offline-weighted**: move all *planning* offline; keep a
**thin runtime that observes the arcade's real progression, selects a precomputed graphics state, and executes
a precomputed transition**. Do not go fully static-per-scene (that was the failed per-segment residency), and
do not keep a general runtime cache "just in case."

Crucially, **you are not starting a new tool** — `tools/translation/precompute_pc080sn_tile_lut.py` is already
half this compiler (`discover_descriptor_tables`, `collect_strip_tiles`, `collect_runtime_gameplay_fg_tiles`
[the strip-source walk], `extract_tiles_from_source`, `collect_block_scene_tiles_and_source_map`,
`assign_scene_aware_slots`, `write_scene_manifest`). The compiler is an **evolution** of that generator, not a
parallel parser.

---

## 1. Right architecture? — HYBRID (offline planner + thin runtime selector)
Offline is right because Rastan's forward-linear progression + statically-enumerable map/tile/palette data
make the residency plan a *compile-time* problem (interval allocation), not a runtime search. Build 0301
proved the runtime approach works but costs O(cells)/frame in three places. **What must stay runtime is only
what is genuinely dynamic:** *which* precomputed state is active (the arcade decides at runtime via
death/branch/event), and the *execution* of the precomputed DMA/LUT/CRAM patch on transition. So: offline
does 100% of the planning; runtime does selection + a table-driven transition + the existing cheap per-cell
lookup + VBlank commit. That is a hybrid, but the 68000 does *no planning*.

## 2. The compiler's natural unit — a **residency epoch keyed on map-stream progression, NOT segment**
The cave capture is decisive: `segment` is not the unit (segment 1 = outdoor+cave; tm0=0/selector=0
throughout). **Correction (addendum §2):** my earlier claim that `a5@0x10C6` "sat at 5" was a **watch-width
error on my part**, not a property of the field. `a5@0x10C6` is the 32-bit map-stream **byte pointer**
(value ≈ `0x00050F6C`); my Build-0301 trace watched it as a 16-bit word at 0xFF10C6, so it read the constant
**high word `0x0005`** while the real progression — `0x050F6C → 0x050F6D → 0x050F6E` per the arcade capture
(`Cody_arcade_stage1_cave_route_capture.md`) — lives in the **low word at 0xFF10C8**, which I never watched.
So the page pointer **does** progress; it advances **+1 per ring cycle** (0x0558E4) in lockstep with the
segment (0x0558FE). It is therefore a valid but **ring-cycle-granular** signal (~one 64-column ring ≈ a
couple of screens). Finer, intra-ring tile lifetime is still driven by the **ring/scroll progression**
(`strip a5@0x10CA` changed 191×, `group a5@0x10CC` 52× in the capture). So the true residency driver is
**how far the map-stream has been traversed** — the source-column position the strip-source tables
(`0x1691C + strip*0x22C0 + segment*0x40 + group*4`) are feeding.

Recommended unit: keep the name **epoch**, defined as *a maximal contiguous interval of the arcade map-stream
traversal over which one Genesis VRAM+CRAM+LUT state is valid.* The compiler derives epoch boundaries from
**tile lifetime along the linear scroll** (new tiles that don't fit the retained set force a boundary). The
**runtime discriminator** is the arcade traversal position. **Best proven candidates (do not finalize yet —
insufficient evidence to pick one):** the **32-bit map-stream pointer `a5@0x10C6`** (full width, low word
`0x050F6C…`) and/or the **segment `a5@0x13E`** give the *coarse, ring-cycle* key; the **strip/group
`a5@0x10CA`/`a5@0x10CC`** (or the strip-source bases `a5@0x1000`) give the *intra-ring* fine position. Whether
epochs can be ring-cycle-coarse (page/segment alone) or must be finer (strip/group) depends on whether one
ring's tile+palette set fits VRAM/CRAM — that is exactly what milestone 1 must measure. Pinning the cheapest
sufficient signal is the #1 open item (risk §16).

## 3. Whole-game offline enumeration — PARTIAL
Statically enumerable from the arcade ROM/regions (all already decoded or decodable by the existing tools):
map source tables (`0x1691C..0x3725C`), metatile→tile format, tile graphics (`pc080sn.bin`), tm0/BG
descriptors (`0x3951C`), the stage→segment→page→strip/group chain (`docs/arcade_reference/pc080sn/
map_stream_format.md`), palette/bank tables. **Needs runtime evidence / not fully static:** the
event-byte→next-direction routing (the map-stream doc explicitly calls this "strongly-supported, not fully
proven"), death→checkpoint restore targets (`a5@0x13B8`), and any branch the arcade takes on player/enemy
state. **Genuinely dynamic:** which branch/epoch is live *right now* (the runtime must observe it). Do not
assume the forward graph is complete until the event-completion edges are confirmed.

## 4. Global offline VRAM allocation — YES for forward runs, PARTIAL overall
Along a linear progression this is textbook interval allocation: compute each tile's live interval
(first→last visible along the traversal), color intervals into VRAM slots with reuse after death of an
interval, minimizing transition DMA. Very tractable offline. **Complications = the reset edges:** death→
checkpoint and attract/Game-Over jump *backward/elsewhere*, breaking linearity. Handle them as **discrete
restore points**: the compiler emits a **complete graphics-state package** for each checkpoint/reset target
(the exact VRAM+CRAM+LUT valid there), applied on that edge. Between resets the run is linear and clean. The
allocation must be **Plane-A+Plane-B+sprite-aware**: only slots **0..1023 are sprite-safe** (sprites
`SPRITE_TILE_BASE=1024`), so planes share ≤~1004 slots minus HUD/text — the epoch's combined A+B tile set
must fit that, or the compiler must split the epoch finer.

## 5. Plane A and B compiled together — YES (mandatory)
Build 0301 proved FG-only can't fit (static BG 854 + text left ~90 free < 200 FG working set). A and B
compete for the *same* pattern VRAM (0..1535, sprites 1024+, nametables 1536+), so they **must be
co-allocated per epoch**. This is not optional.

## 6. Palette — integrated, shared across ALL owners (tiles AND sprites), co-optimized
This is Build 0301's remaining visible failure (right patterns, wrong CRAM line). Genesis CRAM is **4 lines ×
16 colors = 64 entries total, shared by Plane A, Plane B, PC090OJ sprites, and HUD/text** — this is the hard
constraint, and my first draft understated it by discussing only tile palettes.

### 6.1 PC090OJ sprite palettes (addendum §1) — the existing native path
1. **Arcade field identifying a sprite palette:** the PC090OJ object attribute low byte **`a4@39` (offset
   0x27)** carries the color bits (`pc090oj_hooks.s:580-678`); the resulting **effective color bank** (e.g.
   0, 3, 48, 51, 0x36) names the palette family.
2. **Existing native bank→line mapping:** **`palette_route_table` + `palette_route_lookup`**
   (`palette_hooks.s`) — a single-source `(scene_id, owner, arcade_bank) → genesis_line(0..3) + carrier flag`
   router, with per-VBlank carrier re-assert (`vdp_reassert_fg_bank3_line`, `vdp_reassert_bank36_line0`).
   **This is already exactly the "epoch bank→line table + tiny runtime selector" mechanism the addendum asks
   about** — the compiler should *generate* this table per epoch instead of it being hand-authored.
3. **Families coexisting in ordinary gameplay** (current Stage-1 rows): line0=HUD bank 0 (or PC090OJ bank
   0x36 lizard-men when HUD-line free), line1=PC080SN FG bank 3, line2=PC080SN BG bank 48, line3=PC090OJ
   bank 51 (player/main sprites). So **all 4 lines are already occupied**, with sprites getting ~1–2 lines.
4. **Player palette effectively persistent:** YES — the player/main sprite family (bank 51 → line 3) is
   always present and always routed; treat it as a pinned line across gameplay epochs.
5. **How many enemy/item/effect families can coexist:** on Genesis, **very few** — with FG(1)+BG(1)+
   HUD/sprite(1)+sprite(1) already = 4, sprites realistically get **~1–2 lines**, i.e. the arcade's 16 object
   banks must collapse onto ~2 Genesis sprite lines per epoch. This forces deliberate compromises (the
   registry's `decided` status), and some epochs will not fit all simultaneously-visible sprite families —
   the compiler must detect and flag that, not silently alias.

### 6.2 Corrected shared-CRAM feasibility test
Not "tiles ≤ 4 lines." The per-epoch test is:

    lines(Plane-A demand) + lines(Plane-B demand) + lines(PC090OJ sprite demand) + lines(HUD/text)  <=  4

With the player line effectively pinned and HUD needing ~1, **an epoch typically has ≤2 lines to split
between BOTH planes plus any second sprite family.** This is the true bottleneck (far tighter than the tile-
VRAM budget). The compiler must **co-optimize tile-slot, plane palette-line, and sprite palette-line
assignment together**, respecting `specs/palette_decisions.json` (compile `proven`/`decided`; leave
`provisional`/`unknown` as explicit gaps — never invent), and **report any epoch where arcade demand exceeds
4 lines** so the compromise is an explicit, registry-tracked decision.

### 6.3 Compiled vs runtime split
- **Compiled per epoch:** the `(owner,bank)→line` route table, per-line CRAM contents, name-word palette
  bits for tiles, and CRAM transition patches — for Plane A, Plane B, sprites, and HUD.
- **Runtime-dynamic:** which specific enemies/items/effects are actually on screen (arcade decides), palette
  fades/flashes, and the existing per-VBlank carrier re-assert. The runtime keeps the existing
  `palette_route_lookup` selector; the compiler just feeds it generated per-epoch tables.
10. **`palette_decisions.json` interaction:** the sprite bank→line choices (bank 51→line3, 0x36→line0, FG
    bank3→line1, BG bank48→line2) **are palette decisions** and must live as registry rows with their status;
    the compiler consumes the registry and emits the route table only for `proven`/`decided` rows.

## 7. LUT format — **base LUT in ROM + per-epoch patch overlay in RAM**
Target = the original *single indexed read* per cell (`slot = LUT[code]`), no hash/liveness. Keep one active
`code→slot` map the producers index directly. A full 32 KB LUT *per epoch* in ROM is wasteful; a full 32 KB
LUT in RAM is half the 68000 RAM. Recommend **base LUT (ROM) + a small generated patch list per epoch** that
the runtime applies into a compact active map on transition. Because used codes are sparse (~1610 for Stage 1),
a **compact used-codes table** (or a 2-level code→bank→slot) beats the flat 32 KB and eases the RAM pressure.
Tradeoff: ROM holds base + N small patches (cheap); RAM holds the compact active map (small); per-frame lookup
is O(1); transition applies a bounded patch. This is the direct replacement for `fg_tile_cache.s`'s per-cell
work.

## 8. Pattern packing — YES, repack for DMA
The Genesis pattern ROM need **not** preserve arcade tile-ROM order. Repack per epoch so an epoch's
newly-needed tiles are **contiguous**, turning a transition into **one (or few) large DMA runs** instead of
many small ones — the biggest transition-cost win. Transition-specific packed blocks are worth it. (One
constraint: a tile shared by adjacent epochs should keep its slot to avoid re-DMA — the allocator already
wants that.)

## 9. Checkpoint/death restore — generated complete restore packages
Yes: each checkpoint gets a compiler-generated **full graphics-state package** (VRAM slot patterns + CRAM +
active-LUT state) applied on death-restore. Simpler and safer than trying to "rewind" the streaming state.
Few checkpoints → affordable.

## 10. Game Over / attract / frontend — explicit compiler-generated reset states
Yes — model title/attract/game-over as their own epochs/packages with full reset. **Downgrade (addendum §3):**
my earlier statement that Build 0301's black tiles are "precisely a missing full reset" is a **HYPOTHESIS,
not proven** — I inferred it from the code (staged buffers not cleared on `fg_cache_reset` + producers
publishing only changed cells) and the screenshots, but I did **not** mechanically prove that the black cells
are stale name words pointing at repurposed slots (that would need a trace correlating specific staged cells,
their name words, and slot reassignment). It remains the **likely** cause and complete reset packages would
address it, but it must not enter the compiler spec as a proven root cause. Generated full-reset packages
remain a good architectural feature on their own merits (deterministic screen transitions).

## 11. Dynamic fallback pool — **not by default; UNKNOWN pending event-graph proof**
If the progression graph is fully enumerated, no runtime cache is needed. The only thing that could force a
fallback is an un-enumerated/branching progression edge (event→next routing, or an unproven branch). If one
is proven unavoidable, keep a **tiny bounded emergency pool** (a handful of slots) sized from evidence — never
a general hash/LRU. Do not retain Build-0301's machinery out of caution.

## 12. Existing systems likely replaced (do not delete now)
`fg_tile_cache.s` (runtime hash/alloc/evict/liveness/mark_live) → replaced by static LUT + precomputed
transitions. The per-segment residency scenes (ids 4–8) + `genesistan_select_stage1_cave_residency` → gone.
The scene-load *gameplay* tile manifests → replaced by epoch packages (keep title/endround static loads until
they too become reset epochs). Inside `precompute_pc080sn_tile_lut.py`, the scene-tile-set model is
**superseded** by the epoch/lifetime model — but the file is **reused/evolved**, not deleted.

## 13. Existing tooling to reuse (don't rebuild)
- `precompute_pc080sn_tile_lut.py` — the arcade map/strip/metatile decoders + slot-assignment core.
- `precompute_pc080sn_attr_lut.py` + `palette_decisions.json` — palette/attr basis.
- `tools/build_rastan_regions.py` → `build/regions/{maincpu,pc080sn}.bin` — authoritative graphics inputs.
- `build/rastan-direct/address_map.json` — arcade_pc↔runtime mapping.
- `analysis/ghidra/rastan_arcade/exports/` + `map_stream_format.md` — the proven progression model.
- The `genesistrace.lua` detector — becomes the *validation* harness for compiled epochs.

## 14. Recommended generated assets (build/pc080sn_genesis_compiled/)
- `patterns.bin` — repacked Genesis pattern banks (DMA-ordered).
- `epochs.json` + `epochs.inc` — epoch table: id, arcade discriminator range, predecessor/successor,
  Plane-A tile set+slots, Plane-B tile set+slots, palette lines, checkpoint links.
- `lut_base.bin` + per-epoch `lut_patch_*.bin` (or one `lut_patches.inc`).
- `dma_transitions.inc` — per-transition (source-offset,VRAM-dest,length) runs.
- `cram_epochs.bin` + `cram_transitions.inc` — palette-line contents + patches (all owners).
- **`palette_route_epochs.inc`** — the generated per-epoch `(owner, arcade_bank) → genesis_line + flags`
  route table for **PC080SN FG/BG, PC090OJ sprites, and HUD** (replaces the hand-authored
  `palette_route_table`), + the name-word palette-bit maps + per-epoch pinned-line conventions (player line).
- `checkpoint_packages.inc`, `reset_packages.inc` (frontend/attract/game-over).
- `epoch_docs/*.md` — generated, one source of truth (byproduct of the same model).

## 15. Runtime split (be explicit)
**Every frame (cheap, unchanged shape):** per-cell `slot = active_LUT[code]` + native name-word production +
existing VBlank commit. No hash, no liveness, no eviction. **On epoch transition only (rare):** read the
arcade discriminator; if it crossed a compiled boundary → run that transition's precomputed DMA list, apply
its LUT patch and CRAM patch (bounded, ideally in one display-off/VBlank window). **On death/reset edges:**
apply the checkpoint/reset package.

## 16. Top risks (concrete)
1. **Epoch discriminator (highest):** finding a cheap, reliable arcade signal that changes at epoch
   granularity — segment and page are too coarse; the real driver is scroll/ring position. If no clean cheap
   signal exists, epoch selection becomes fragile. Milestone 1 must pin this.
2. **Event→progression routing unproven** (map_stream §6): the forward graph may have gaps → mis-selected or
   unreachable epochs.
3. **Shared 4-line CRAM contention (elevated — likely the tightest constraint, tighter than tile VRAM):**
   Plane-A + Plane-B + sprites + HUD must fit 4 CRAM lines/epoch, with the player line effectively pinned and
   HUD ~1 → often ≤2 lines for both planes plus a second sprite family. Some epochs' arcade demand will
   exceed 4 → forced, registry-tracked compromise. Plus **palette unknowns** in the registry block compiling
   some epochs' CRAM.
4. **Per-epoch A+B+sprite VRAM fit:** if any epoch's combined set exceeds sprite-safe slots, the compiler must
   split finer → more transitions → DMA/timing pressure.
5. **Transition DMA budget/timing:** a large mid-scroll transition must fit a VBlank or accept a brief
   display-off flash (Build 0301's entry glitch generalized).
6. **Reset completeness:** any incomplete reset package reintroduces Build 0301's stale-cell black tiles.

## 17. First milestone — one real linear stretch, output only (no runtime wiring)
Compile **Stage-1 outdoor→cave (the captured segments 1→2→3 route)** offline into concrete Genesis assets:
(a) derive its epochs from tile-lifetime along the traversal; (b) co-allocate Plane-A+Plane-B tiles into
sprite-safe slots per epoch; (c) repack the patterns; (d) emit the base LUT + per-epoch patches + transition
DMA lists; (e) assign CRAM lines + name-word palette bits per epoch (respecting `palette_decisions.json`);
(f) generate the epoch docs. **Validate the *output* against the arcade reference** — does epoch N's tile+
palette set reproduce the arcade cave frame? — using the existing decoders and the `genesistrace`/Exodus
comparison, **without touching the runtime yet**. That proves *arcade data → compiler → Genesis-native assets
+ correct palette* for one real stretch. Runtime integration (selector + transition executor replacing
`fg_tile_cache.s`) is milestone 2, only after the assets validate.

---
**Overall verdict:** HYBRID (offline planner + thin runtime selector) ·
**Recommended compiler unit:** residency **epoch** = interval of arcade map-stream traversal with one
VRAM/CRAM/LUT state; runtime key = (segment + intra-segment scroll/ring position), NOT segment/page alone ·
**Whole-game offline enumeration:** PARTIAL (map/tiles/palette static; event-routing + checkpoints need
runtime confirmation) · **Plane A+B compiled together:** YES · **Palette integrated:** YES ·
**Recommended LUT format:** base LUT (ROM) + per-epoch patch overlay into a compact active map (O(1) lookup) ·
**Global offline VRAM allocation:** PARTIAL/YES (linear runs yes; reset edges via packages) ·
**Pattern ROM repacking:** YES · **Checkpoint restore:** generated complete restore package per checkpoint ·
**Frontend/attract reset:** explicit compiler-generated reset epochs/packages ·
**Dynamic fallback required:** UNKNOWN (default NO; only a tiny bounded pool if an un-enumerated edge is
proven) · **Major systems likely replaced:** fg_tile_cache.s runtime cache/liveness, per-segment residency +
selector, gameplay scene manifests · **Recommended generated assets:** patterns.bin, epochs table,
lut_base+patches, dma_transitions, cram_epochs+transitions, checkpoint/reset packages, epoch docs ·
**Genesis per-frame CPU:** only `slot=active_LUT[code]` + name-word production + VBlank commit ·
**Genesis transition-time:** read discriminator, execute precomputed DMA/LUT/CRAM patch (+ checkpoint/reset
packages on those edges) · **Top risks:** epoch discriminator signal; unproven event routing; palette
unknowns; per-epoch A+B+sprite fit; transition DMA timing; reset completeness ·
**First milestone:** offline-compile the Stage-1 1→2→3 route to Genesis assets+palette and validate the
OUTPUT against the arcade reference, no runtime wiring · **Production source changed:** NO · **ROM:** NO ·
**Build 0302 consumed:** NO.
