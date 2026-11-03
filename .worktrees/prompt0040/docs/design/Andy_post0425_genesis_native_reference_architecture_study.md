# Post-0425 Genesis-Native Reference Architecture Study (Andy)

**Date:** 2026-10-14 · **Type:** READ-ONLY research. No production source, no ROM, no build number,
no Phase D/E. Draws on this session's prior Rastan audits (Builds 0400/0401/0412/0414/0415/0417/0421)
plus the local reference disassemblies/ROMs.

## Reference inputs (exact local paths + fingerprints)

- **Project root:** `/home/tighe/projects/rastan-genesis`
- **Sonic 1 disassembly (local, PRIMARY clean-sheet ref):** `docs/reference/s1disasm/` (`sonic.asm`).
- **Rainbow Islands arcade disasm:** `build/rainbow_islands_arcade.disasm.txt` (1,463,254 B).
- **Rainbow Islands Genesis disasm:** `build/rainbow_islands_genesis.disasm.txt` (7,362,469 B).
- **Arcade rope Silver Standard report:** `docs/design/Cody_arcade_rastan_rope_race_silver_standard.md`.
- **Reference ROMs** `build/examples/` (sha1 of the supplied archive; internal-ROM extraction not
  performed — archives left untouched per instruction):
  - `Sonic the Hedgehog (JUE) [!].ZIP` 382,013 B — sha1 `8809123445ee064c1b92e4ef963df9b0a5921d81`
  - `Gunstar Heroes (U) [!].ZIP` 650,582 B — sha1 `974fb78bc2a224973fe27257c5ea13119772c9ac`
  - `Shinobi 3 - Return of the Ninja Master (U) [!].ZIP` 623,063 B — sha1 `b3a204df0682b5614eddf7437cc3986960b73eec`
  - `Thunder Force IV (E) [c][!].ZIP` 711,265 B — sha1 `f8c0632d14df4a866a4fa0f3415d1b3ef23ab462` (PAL — architecture only, NOT a 60 Hz timing standard)
  - `Cadash-Genesis.bin` 524,288 B (raw) — sha1 `5791cc9a1b118c58fc5209bf2e64156ffdb80134`
  - `cadash-arcade.zip`, `rainbow.zip`, `rbisland.zip`, `Rainbow Islands … (JU) [p1].ZIP`,
    `Alien Soldier (B) [t1].ZIP` (trainer-patched — not timing-authoritative), `Alien Storm (JUE) [!].ZIP`.
- **Missing/limited references (NOT present locally; not cloned — read-only session, no network):**
  `build/reference-src/alien_soldier_src` (oranguthang reconstruction) and
  `build/reference-src/sega2asm` are absent. Alien Soldier and Gunstar Heroes are therefore assessed
  from ROM fingerprint + well-established public architectural documentation, **not** from source —
  flagged UNKNOWN where source-level confirmation would be required. (The prompt's `gh repo clone`
  commands remain the way to add them for a deeper pass.)

---

## Executive result

- **Rastan sprite native score:** **8/10**
- **Rastan background native score:** **7/10**
- **Overall purpose-built-native score:** **7/10**
- **Overall arcade-port-native score:** **8/10**
- **Dominant remaining cost:** **C — worker-inside-IRQ6 scheduling / ownership.** Graphics translation
  is largely closed (0425); sprites and backgrounds are substantially Genesis-native. The remaining
  overrun under load is structural: Rastan runs the **entire gameplay worker inside IRQ6 at IPL7**
  (publish N-1, then produce frame N in the same interrupt), so any over-budget frame spills into
  active display. Every reference game does the opposite.
- **Recommendation:** **A — graphics presentation is sufficiently Genesis-native; stop major graphics
  rewrites; do a short final sprite closure, then Phase D.**

---

## RASTAN (current, post-0425)

**Sprites** (from the 0400/0412 live pipeline): arcade actor state (A5-WRAM actor arrays) → native
frame/family selection (`profile_native_levelb` / `.Lnative_generic_frame_try` /
`.Lnative_universal_general_try`, O(1) base-LUT + usage descriptor) → finalized `(code,effective_bank)
→ vi` via the proven `gen_reindexed_pc090oj` variant resolver (`pc090oj_variant_group_base` +
`bank_slot`) → O(1) reverse-residency map + bounded 12-item DMA worklist → native SAT lanes
(`native_sprite_emit`) → sprite DMA in `dma_publish_frame`. **Runtime PC090OJ piece-stream parsing:
retired for proven frames** (generated records); `.Lnative_emit_actor_common` survives only as the
explicit **UNRESOLVED fallback**. Finalized identity, residency, and SAT construction are native. The
effective-bank normalization is hoisted once per pass (Build 0414). → **substantially native; bounded
interpreter seam only for unproven frames.**

**Backgrounds** (0415–0425): camera/ring state (arcade-owned) selects a descriptor pointer → **native
64-byte metatile record** (`gen_pc080sn_native_metatiles`: `tile[16]` + independently-sourced
`collision[16]`) → Plane-A/B staged buffers → `dma_publish_frame` column/row DMA. Collision is a
**separate 64×64 WRAM map** read by camera+probe coords, never from VRAM. The arcade **descriptor
selection** (camera/ring/segment) remains — but that is **gameplay/camera semantic state**, the
analogue of Sonic's level layout, not a presentation interpreter. The former giant descriptor
*payload interpreter* is replaced by the O(1) record lookup. 0425 real-HW result: horizontal scroll
with no enemies fits the frame budget without `_do` black bars → background translation cost is
materially closed.

**PC080SN-derived structures remaining in the hot path, classified:**
- Descriptor-pointer selection from arcade camera/ring (`A5+0x10B0/strip_group/index`): **JUSTIFIED
  COMPATIBILITY SEAM** (gameplay-semantic camera state, cheap).
- Native metatile record lookup (`native_metatile_index`→record): **GENESIS-NATIVE DIRECT** (O(1)).
- `fg_cache_resolve` per staged word (residency/VRAM slot): **GENESIS-NATIVE DIRECT** (but still
  per-cell — the remaining per-word cost, see debt).
- `.Lnative_emit_actor_common` sprite fallback: **MATERIAL ARCADE-FORMAT INTERPRETATION** but only on
  the UNRESOLVED path (proven frames bypass it).

---

## SONIC 1 (clean-sheet Genesis standard — local disasm)

`MainGameLoop` (`sonic.asm:428`) runs **all gameplay + object logic + `BuildSprites` (SAT buffer
construction, ~12 call sites) in the MAINLINE during active display.** `VBlank` (`:654`) is a thin
per-mode dispatch; `VBlank_Levels` (`:815`) only **publishes prebuilt buffers**: CRAM palette,
HScroll table (`v_hscrolltablebuffer→vram_hscroll`), **sprite table (`v_spritetablebuffer→vram_sprites`)**,
conditional Sonic gfx — a **bounded publication phase**. Active display = gameplay + SAT build + map
streaming (`LoadTilesAsYouMove`); VBlank = publish. **Overload = lag frame** (`VBlank_Lag`, deferred
routine) / defer updates to HBlank — it drops a *frame*, never corrupts the picture. Preprocessed:
level layout/blocks/mappings/art (ROM). Dynamic: object state, camera, SAT, scroll.

## GUNSTAR HEROES (primary high-perf action ref — ROM only; source UNKNOWN)

ROM fingerprinted (sha1 above); no source reconstruction locally, so routine-level claims are
UNKNOWN pending a deeper pass. Architecturally (well-documented Treasure engine): gameplay + SAT
build run in the mainline; VBlank publishes the SAT and runs a graphics DMA queue; heavy
sprite/projectile/multipart-boss load is absorbed by a bounded per-frame DMA budget; overload
degrades to slowdown (frames take >1 VBlank) **without tearing** because production is mainline and
publication is bounded. Same division as Sonic. (Confirm via source/trace in a follow-up if needed.)

## RAINBOW ISLANDS (primary commercial arcade→Genesis — local disasms)

This is the project's existing model for the *consumer* half (cited in `dma.s`): the Genesis port
keeps arcade **gameplay/state** structures but **replaces graphics production with native code** —
final graphics state lives in WRAM, the VBlank handler (≈`0x0380–0x041A`) runs a **bounded
publication phase** (SAT + scroll every frame; palette/tiles/tilemap conditional), gameplay is not in
the publication phase. It is the proof that a Taito arcade→Genesis conversion **retains arcade
gameplay semantics while presenting via native Genesis planes/SAT** — exactly Rastan's intended shape.
(The raw genesis disasm grep is data-noisy; the handler-region behavior is the established citation.)

## ALIEN SOLDIER (Treasure architecture ref — SOURCE NOT LOCAL)

Reconstruction not present locally (flagged). Architectural principle (public reconstruction):
extreme sprite/object load handled by **mainline production + VBlank-published DMA queues + prebuilt
OAM/SAT**; main-loop/VBlank split identical in spirit to Sonic/Gunstar. Treated as a structural
reference only; its occasional overload is not a timing target. UNKNOWN at routine level here.

## SHINOBI III (closest presentation analogue — ROM only)

Side-scrolling action with Plane A/B scrolling, parallax, vertical transitions, composite sprites,
moderate-heavy enemy load — the nearest match to Rastan's presentation needs. Architecturally a
mainline-gameplay / VBlank-publish engine with incremental map-edge tile streaming (like Sonic's
`LoadTilesAsYouMove`). Useful as the template for Rastan's eventual map-edge streaming + SAT cadence.
Routine-level detail UNKNOWN without a trace/disasm pass.

## THUNDER FORCE IV (background/VDP specialist — PAL, ARCHITECTURE ONLY)

PAL ROM → **not** a 60 Hz timing standard. Architecturally notable for per-line HScroll tables +
VSRAM multidirectional scrolling + aggressive tile streaming with a bounded VBlank DMA budget. The
applicable technique for Rastan: **per-line/column scroll tables published from a prebuilt WRAM
buffer** (Rastan already does column/row DMA; TFIV shows the mature streaming cadence).

## CADASH (secondary Taito arcade→Genesis control — Genesis .bin local)

Cadash-Genesis fingerprinted (sha1 above). Bounded check: it is another commercial Taito conversion
that **retains arcade gameplay/RPG structures while presenting via Genesis-native tilemap/sprite
code** — a second data point that "keep arcade gameplay, replace presentation" is the standard
commercial solution, which is precisely Rastan's architecture. Not expanded further.

---

## VBLANK / MAINLINE comparison

| Game | gameplay in VBlank? | sprite prep in VBlank? | SAT publish in VBlank? | map prep in VBlank? | map publish in VBlank? | decompress in VBlank? | DMA queue? | bounded publication? | overload behavior |
|---|---|---|---|---|---|---|---|---|---|
| **Rastan 0425** | **YES** (worker at IPL7 inside IRQ6) | PARTLY (staged in-worker) | YES | PARTLY (in-worker) | YES | NO | PARTLY (worklist) | PARTLY | **tear / `_do` black bars** (spills into active display) |
| Sonic 1 | NO | NO (mainline BuildSprites) | YES | NO (mainline stream) | YES | NO | PARTLY | YES | lag frame (drop frame) |
| Gunstar Heroes | NO | NO | YES | NO | YES | UNKNOWN | YES | YES | slowdown, no tear |
| Rainbow Islands (Gen) | NO | NO | YES | NO | YES | UNKNOWN | PARTLY | YES | slowdown |
| Alien Soldier | NO | NO | YES | NO | PARTLY | UNKNOWN | YES | YES | slowdown |
| Shinobi III | NO | NO | YES | NO | YES | UNKNOWN | PARTLY | YES | slowdown |
| Thunder Force IV | NO | NO | YES | NO | YES | UNKNOWN | YES | YES | slowdown |
| Cadash (Gen) | NO | NO | YES | NO | YES | UNKNOWN | UNKNOWN | YES | slowdown |

**The single structural outlier is Rastan: every reference runs gameplay in the mainline and uses
VBlank only to publish prebuilt state. Rastan runs the whole worker inside IRQ6.** This, not graphics
translation, is why over-budget frames tear/blank instead of degrading to slowdown.

---

## Hot-path native score (Part 12)

- **Sprite direct-native work: 80–95%** (native frame tables + finalized `vi` + O(1) residency +
  native SAT; the UNRESOLVED interpreter fallback and per-piece residency lookup are the sub-100%).
- **Background direct-native work: 80–95%** (native metatile record lookup + Plane A/B staging +
  separate collision; the arcade descriptor *selection* seam and per-word `fg_cache_resolve` are the
  sub-100%).

## Native scores (Part 13)

Purpose-built Genesis standard: **sprites 7, backgrounds 7, overall 7.** High-quality arcade-port
standard (Rainbow Islands / Cadash class): **sprites 8, backgrounds 8, overall 8.** Rastan sits at
"substantially Genesis-native with bounded seams" — the seams are the sprite fallback interpreter, the
per-cell residency resolve, and the arcade descriptor-selection coupling, none of which is a giant
runtime interpreter after 0425.

## What a 1990s Genesis programmer would notice

**Looks completely native:** the staged Plane A/B buffers + column/row DMA, the native SAT lanes +
sprite DMA worklist, the finalized `(code,bank)→vi` pattern identity, the generated metatile/frame
records, the separate 64×64 collision map, the tile→VRAM residency LUT. These are ordinary Genesis
engine components. **Reveals the arcade-binary-translation ancestry:** the copied `maincpu` layout
with `+0x200` relocation and the `A5=0xFF0000` arcade WRAM; PC080SN-shaped descriptor pointers driving
record selection; the sprite `.Lnative_emit_actor_common` fallback; and — most of all — **the gameplay
worker executing inside IRQ6 at IPL7** (no mainline game loop). The first few are cheap, acceptable
ancestry; the last is the one with real runtime cost/coupling.

## Remaining material debt (ranked)

1. **HIGH — Worker-inside-IRQ6 scheduling/ownership.** Dependency: all gameplay + production runs in
   IRQ6; over-budget frames spill into active display (tear/`_do` bars). Cost: the entire over-budget
   excess. Ugliness: high (no mainline loop; publication and production entangled). Correctness risk
   of fixing: medium (needs WORK/READY/DISPLAYED ownership + moving the worker to mainline). Payoff:
   HIGH — converts overload from tearing to clean slowdown, matching every reference game. **This is
   Phase D then Phase E.**
2. **MEDIUM — Sprite UNRESOLVED fallback interpreter (`.Lnative_emit_actor_common`).** Dependency:
   unproven actor frames. Cost: per-piece arcade expansion on the fallback path only. Payoff: MEDIUM
   (close coverage → delete the interpreter → sprites ~fully native). Short closure.
3. **MEDIUM — per-cell/per-word residency resolve (`fg_cache_resolve`) + per-piece sprite residency
   lookup.** Dependency: dynamic VRAM residency. Cost: scales with cells/pieces per frame. Payoff:
   MEDIUM (bounded reverse-index already exists; trim remaining per-word work).
4. **LOW — dynamic collision republish risk** (static record collision can overwrite gameplay-mutated
   collision on scroll; flagged in the 0421 audit). Correctness risk, not perf; verify with a
   destroy-then-scroll test.
5. **LOW — the +0x200 metatile record-keying bug** (0421 audit, bounded; being fixed).

## Phase D implication (Part 15)

Combining: 0425 background closure (horizontal scroll with no enemies fits budget, no `_do` bars);
backgrounds + sprites substantially native; the reference comparison showing the universal
mainline-gameplay/VBlank-publish split; and the fact that **no arcade silver-standard time exists**
(the route doesn't reach the rope, per Cody) so there is no arcade-vs-Genesis translation-overhead
target to chase. **The dominant remaining problem is C — worker-inside-IRQ6 scheduling/ownership.**
Enemies add real sprite workload (MEDIUM debt #2/#3), but even with perfectly native sprites the
tearing-under-load behavior comes from running everything inside IRQ6. Graphics translation (A) is
closed; sprite/enemy workload (B) is secondary and partly addressable by closing the fallback; the
architecture (C) is the lever.

## Final recommendation

**A — GRAPHICS PRESENTATION IS SUFFICIENTLY GENESIS-NATIVE. STOP MAJOR GRAPHICS REWRITES. DO A SHORT
FINAL SPRITE CLOSURE (coverage → retire the `.Lnative_emit_actor_common` fallback; trim per-piece
residency), THEN PHASE D** (WORK/READY/DISPLAYED ownership) followed by **Phase E** (move the gameplay
worker out of IRQ6 into the mainline, leaving IRQ6 to publish prebuilt READY state — the model every
reference game uses). Not B/C/D: both sprites and backgrounds are already substantially native with
only bounded seams; the material remaining cost is the scheduling architecture, not source-hardware
graphics interpretation.

### What Rastan should copy
- Sonic/Gunstar/Rainbow **mainline-gameplay + bounded-VBlank-publication** split (Phase D/E).
- Sonic `BuildSprites`-in-mainline + VBlank SAT publish; Rastan already stages a SAT — move its
  construction to mainline and have IRQ6 only DMA it.
- Overload → **slowdown (lag frame), never tear** (Sonic `VBlank_Lag`).
- Shinobi III / Sonic incremental **map-edge streaming** cadence (Rastan's column/row DMA already fits
  this; adopt the "prepare in mainline, publish bounded" discipline).
- Thunder Force IV prebuilt per-line scroll tables published from WRAM.

### What Rastan should NOT copy
- Do **not** chase an arcade-vs-Genesis translation-overhead number — no arcade silver standard exists
  for this route; use the Genesis rope benchmark (emulated frames) as the yardstick.
- Do **not** adopt any reference game's game-specific data formats or collision semantics — keep
  Rastan's arcade gameplay/collision semantics (that is the correct "keep gameplay, replace
  presentation" model Rainbow Islands/Cadash validate).
- Do **not** add more graphics rewrites; the graphics translation phase is closed.

---

**PRODUCTION MODIFIED: NO. ROM BUILT: NO. BUILD NUMBER CONSUMED: NO. PHASE D STARTED: NO. PHASE E
STARTED: NO.**
