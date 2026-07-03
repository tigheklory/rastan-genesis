# Andy — PC080SN / PC090OJ VRAM Ownership Design (Static Validation / Design Only)

**Author:** Andy
**Date:** 2026-07-02
**Baseline:** Build 0130 (byte-identical to Build 0128), SHA256 `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f`.
**Primary prior:** `docs/design/Cody_pc090oj_persistent_sprite_tile_dma_cache_implementation.md` (Gate-1 STOP); `docs/design/Andy_pc090oj_persistent_sprite_tile_dma_cache_design.md`; `docs/design/Andy_build0130_graphics_timing_budget_analysis.md`.
**Scope:** DESIGN / static validation only. No implementation/edit/build/ROM. Static inspection of the LUT generator + manifests was performed offline as design validation (Cody STOPPED and returned this gate). Labels **[OBS]** verified this task; **[INT]** interpretation.

> **BOTTOM LINE:** The overlap is real and **concurrent** (not transient): the PC080SN End-Round scene loads tile patterns into Genesis VRAM slots **1280..1342**, which are exactly the VRAM tiles owned by **PC090OJ sprite slots 64..79** (`1024 + 64*4 = 1280`). Invalidation-only (Option D) cannot fix a concurrent-ownership clash and is not provably safe. The narrowest safe fix is **Option A**: change one generator constant, **`TILE_CACHE_BASE_B: 1280 → 1344`** (keep `SIZE_B = 160`), so PC080SN cache B occupies **1344..1503** — fully above the sprite range (ends 1343) and below Plane B (1536). No PC090OJ base change, no plane/SAT/HScroll relocation, no `scene_load.s` change. Proven to fit with 129 slots of slack. **Recommend Option A.**

---

## == PHASE 0 ==

- **Relevant priors:** Andy PC090OJ residency-cache design (per-SAT-slot cache, 1024..1343 assumed sprite-owned); Cody Gate-1 STOP (overlap found); Andy Build 0130 churn analysis (1472 tile-DMA words/frame). KF-021 context.
- **High-rediscovery hazards:** the SAT slot→VRAM mapping `(SPRITE_TILE_BASE + slot*4)` means sprite slots 64..79 map to VRAM 1280..1343 — the exact endround cache-B band; the clash is per-slot-VRAM ownership, easy to misread as a scene-load staleness problem.
- **Task classification:** VRAM-ownership DESIGN + static capacity proof, enabling the OPEN-024 residency cache.
- **Contradiction detected:** NO (confirms and refines Cody's Gate-1 STOP with the full per-manifest picture).
- **Open/Closed pre-check:** OPEN-024 (cache enablement) + OPEN-001 (title timing) context; not closing either.
- **Build 0130 baseline:** verified `79ec8a30…f5bc6f`, byte-identical to 0128.
- **Gate 1 STOP summary:** Cody correctly STOPPED before the residency-cache implementation — `pc080sn_scene_preload_endround.bin` writes 63 slots in 1280..1342, the LUT maps PC080SN tiles 0x29DD..0x2A1B there, and `precompute_pc080sn_tile_lut.py` sets `TILE_CACHE_BASE_B=1280 / SIZE_B=160` → PC080SN owns part of the proposed 1024..1343 sprite range. No build, baseline unchanged.
- **address_map.json loaded:** YES (task is Genesis-VRAM-internal; no arcade↔genesis correlation needed).
- **arithmetic offset used as proof:** NO.

---

## == CURRENT VRAM OWNERSHIP ==

**PC090OJ sprite range (desired exclusive):** tiles **1024..1343** (320 tiles = 80 SAT slots × 4), bytes 0x8000..0xA7FF. Slot X → tiles `1024+X*4 .. 1024+X*4+3`. So slots 0..63 → 1024..1279; **slots 64..79 → 1280..1343**. [OBS pc090oj_hooks.s:73,1171-1174]

**PC080SN allocator [OBS `precompute_pc080sn_tile_lut.py`]:** `build_slot_sequence()` = `[0..1003]` (BASE_A=0, SIZE_A=1004) ∪ `[1280..1439]` (BASE_B=1280, SIZE_B=160). Tiles are assigned scene-aware in that order; cache B is only reached when cache A (1004 slots) is exhausted.

**PC080SN current manifest ranges [OBS parsed binaries]:**

| Manifest | pairs | dst min | dst max | dst ranges | overlaps 1024..1343 |
|---|---:|---:|---:|---|---|
| title | 845 | 0 | 844 | 0..844 | none |
| gameplay | 829 | 0 | 828 | 0..828 | none |
| **endround** | **1067** | 0 | **1342** | **0..1003 ∪ 1280..1342** | **1280..1342** |
| vram_preload (legacy = title) | 845 | 0 | 844 | 0..844 | none |

**overlap:** endround only, VRAM tiles **1280..1342** (63 slots).
**cause:** cache A fills completely for endround (1004 unique tiles → 0..1003), and its remaining 63 tiles spill into cache B at 1280.., which the residency-cache design wanted to reserve for sprites.
**risk:** **concurrent** ownership. During End-Round, PC080SN name-tables reference patterns resident at 1280..1342 *while displayed*; if PC090OJ later emits ≥65 sprites (slots 64..79), its tile DMA overwrites those same VRAM tiles → mutual corruption. This is not a stale-cache problem — both owners need the bytes at the same time.

---

## == OPTION ANALYSIS ==

**Option A — move PC080SN cache B (`BASE_B 1280→1344`, `SIZE_B=160` → B=[1344..1503]):** **RECOMMENDED.** B now starts at 1344 = sprite-top(1343)+1 → zero overlap with 1024..1343; B max 1503 < Plane B 1536. Endround's 63 cache-B tiles relocate to 1344..1406 (max 1406). One constant changed; A unchanged (already ends at 1003 < 1024); title/gameplay untouched (never reach B). Pure VRAM placement change — the LUT (name-table refs) and manifests (pattern uploads) regenerate from the same `assigned_slots`, so rendered output is identical. **Safe + narrowest.**

**Option B — move PC090OJ `SPRITE_TILE_BASE`:** **REJECT.** No contiguous 320-tile gap exists below 1536 that avoids PC080SN: PC080SN occupies [0..1003] and [1280..1439], leaving only 1004..1279 (276) and 1440..1535 (96) — neither ≥320. Relocating sprites would still require moving PC080SN, so this is strictly worse than A.

**Option C — allocator reserves a PC090OJ range:** this is the **general form of Option A**. Reserving 1024..1343 for sprites and confining PC080SN cache B to [1344..1503] is exactly what the `BASE_B` move accomplishes. No separate mechanism needed; A is the minimal instance.

**Option D — invalidation-only after scene loads:** **REJECT (not provably safe).** Per the task's warning, invalidation only cures *transient* external writes. Here the conflict is **simultaneous**: sprite slots 64..79 own VRAM 1280..1343, and endround needs patterns resident there concurrently. Empirically emitted counts are ≤32 (title 23, ROUND 32 — slots 0..31 only, VRAM 1024..1151), so slots 64..79 were not observed in the traces — **but this is not a hard bound** (the mirror scan emits up to 80, pc090oj_hooks.s:1026). I cannot prove slots 64..79 are never used during endround, so invalidation-only fails the required proof and cannot resolve concurrent overwrite regardless.

**Option E — shared code→VRAM allocator / reduced sprite reservation:** **REJECT for now (fallback only).** Reducing the sprite reservation to 64 slots (VRAM 1024..1279, avoiding 1280..1342) would dodge the clash but caps simultaneous sprites at 64 — a functional regression — and a shared allocator is a broad rewrite. Option A keeps the full 80 slots and is far narrower.

---

## == CAPACITY / SAFETY PROOF ==

- **available pattern slots (below Plane B 1536):** 1536 (tiles 0..1535).
- **PC080SN demand:** largest scene = End-Round = **1067** unique tiles.
- **PC090OJ demand:** **320** tiles (1024..1343).
- **candidate ranges (Option A):** PC090OJ = 1024..1343; PC080SN A = [0..1003] (unchanged), B = **[1344..1503]** (BASE_B=1344, SIZE_B=160). Allocator budget = 1004 + 160 = **1164** ≥ 1067 needed.
- **max destination after move:** endround 0..1003 ∪ 1344..1406 → **max 1406**; title 844; gameplay 828. (Verified: endround cache-B tiles = 1067−1004 = 63 → 1344..1406.)
- **plane/name/SAT/HScroll collision:** none — 1406 < Plane B (1536) < Plane A (1792) < SAT (1984) < HScroll (2016). Sprite 1024..1343 and PC080SN B 1344..1503 are adjacent, disjoint.
- **slack:** B window unused 1407..1503 (97) + free 1504..1535 (32) + A/sprite gap 1004..1023 (20) = **149 slots** below Plane B unused after both owners placed.
- **safe:** **YES.**

**Capacity Q&A:**
1. **PC080SN + PC090OJ fit below 1536 disjoint?** YES (1067 + 320 = 1387 ≤ 1536; layout-constrained budget 1216 ≥ 1067).
2. **PC090OJ stays 1024..1343, PC080SN uses 0..1023 + 1344..1535?** YES — 1024 + 192 = 1216 ≥ 1067.
3. **Is 0..1023 + 1344..1503 enough?** YES — 1024 + 160 = 1184 ≥ 1067 (endround needs 1067; cache B only carries 63).
4. **`BASE_B=1344 / SIZE_B=160` sufficient and safe?** YES — endround uses 1344..1406 (63 of 160), max 1503 < 1536.
5. **Any manifest need 1504..1535?** NO — post-move max is 1406.
6. **1504..1535 safe slack?** YES — free, below Plane B, unreferenced.
7. **Anything else using 1344..1503?** NO — only PC080SN cache B after the move; sprites end at 1343; planes/SAT/HScroll ≥1536.

---

## == RECOMMENDED DESIGN ==

- **Chosen option:** **Option A** (= minimal Option C).
- **Exact constants:** in `tools/translation/precompute_pc080sn_tile_lut.py`: `TILE_CACHE_BASE_B = 1344` (was 1280); `TILE_CACHE_SIZE_B = 160` (unchanged); `TILE_CACHE_BASE_A = 0`, `TILE_CACHE_SIZE_A = 1004` (unchanged). Resulting slot sequence `[0..1003] ∪ [1344..1503]`.
- **Files affected later (Phase 1):** `tools/translation/precompute_pc080sn_tile_lut.py` (one constant).
- **Generated artifacts affected later:** `build/pc080sn_tile_vram_lut.bin`, `build/pc080sn_tile_vram_lut_words.inc`, `build/pc080sn_scene_preload_endround.bin` (slot values only; pair count stays 1067), `build/pc080sn_scene_preload_title.bin` + `_gameplay.bin` (regenerate; expected byte-identical — no cache-B tiles), `build/pc080sn_vram_preload.bin` + `_words.inc` (legacy = title; expected byte-identical), `build/pc080sn_source_scene_map.bin`, `build/pc080sn_unique_tile_count.txt`.
- **Why safe:** sprite range 1024..1343 becomes exclusively sprite-owned; PC080SN B is disjoint (1344..1503) and below Plane B; capacity proven with 149-slot slack; name-table refs and pattern uploads regenerate consistently → identical rendered output.
- **Why narrow:** exactly one generator constant changes; PC090OJ base, cache A, plane/SAT/HScroll bases, `scene_load.s`, `tilemap_hooks.s`, and all runtime code are untouched.
- **What remains unchanged:** PC090OJ object RAM mirror (canonical); SPRITE_TILE_BASE=1024; Plane B/A/SAT/HScroll bases; PC080SN cache A; render-side-only cache role; no fake sprites/framebuffer/SGDK/C/30 FPS/runtime Python.

---

## == CODY FOLLOW-UP PLAN ==

**Phase 1 — PC080SN VRAM ownership relocation only:**
1. Set `TILE_CACHE_BASE_B = 1344` in `precompute_pc080sn_tile_lut.py` (keep SIZE_B=160).
2. Regenerate: `pc080sn_tile_vram_lut.bin`(+.inc), `pc080sn_scene_preload_{title,gameplay,endround}.bin`, `pc080sn_vram_preload.bin`(+.inc), `pc080sn_source_scene_map.bin`, `pc080sn_unique_tile_count.txt`.
3. Confirm the generator's own budget/range checks still PASS.
4. Build the ROM (no source/opcode change → `opcode_replace` count and `total_genesis_bytes_covered` unchanged; only PC080SN data bytes change).

**Phase 1 evidence:** regenerated manifests with **no PC080SN destination in 1024..1343** and **all destinations < 1536** (endround max = 1406); title/gameplay/vram_preload byte-identical (or explained); canonical gate/invariant status (opcode count + bytes-covered unchanged); build number/SHA/size; title + End-Round + coin/start screenshots showing **no PC080SN plane regression**.

**Phase 2 — PC090OJ per-SAT-slot residency cache (Andy prior design), only after Phase 1 proves clean ownership:** implement per `Andy_pc090oj_persistent_sprite_tile_dma_cache_design.md`. Because 1024..1343 is now exclusively sprite-owned and PC080SN can no longer write it, **no scene-load cache invalidation is required** and `scene_load.s` stays untouched (the prior design's Q4 gate is satisfied structurally).

**Phase 2 evidence:** build/SHA/size; files changed (`pc090oj_hooks.s` + boot init if BSS not zero-guaranteed); gate/invariant; title `emitted=23`; sprite tile-DMA words before (1472) / after (~0 steady); title score sprites retained (22/27, codes 0x2A–0x49); SAT chain valid; End-Round renders correctly (proves no sprite/PC080SN VRAM collision); no SAT/staging canonical bypass.

**STOP conditions:**
- Regenerated PC080SN cache B still overlaps 1024..1343.
- Any regenerated destination ≥ 1536.
- Collision with Plane A/B / SAT / HScroll VRAM.
- PC080SN cannot fit below 1536 with PC090OJ reserved.
- Invalidation-only becomes the only workable option (needs further runtime proof — do not proceed).
- Solution would require relocating Plane A/B/SAT/HScroll tables.
- Solution would require changing PC090OJ object RAM semantics.
- Solution would require a broad renderer rewrite.
- Solution would require a 30 FPS fallback.

---

## Open / Closed Issues Impact

- **Open issues touched:** OPEN-024 (unblocks the sprite tile-DMA residency cache via clean VRAM ownership; not closed), OPEN-001 (title/timing context; not closed).
- **Closed issues touched:** NONE.
- **New issues opened:** NONE (recommend a KNOWN_FINDINGS entry post-implementation documenting the Genesis VRAM ownership map: patterns 0..1023 + 1344..1503 = PC080SN, 1024..1343 = PC090OJ sprites, 1536+ = planes/SAT/HScroll).
- **Issues closed:** NONE.
- **Issues intentionally deferred:** the residency-cache implementation itself (Phase 2); `.Lpc090oj_emit_slot` producer/render split; HV/VCounter display-on diagnostic; any future PC080SN growth beyond 1216 slots (would revisit this map).

AGENTS_LOG updated: YES
STOP status: NO — safe ownership map found and proven (Option A); delegated to Cody as a two-phase plan (PC080SN relocation → then residency cache), no implementation performed.
