# Andy — PC090OJ Persistent Sprite Tile-DMA Cache Design (Design Only)

**Author:** Andy
**Date:** 2026-07-02
**Baseline:** Build 0130 (byte-identical to Build 0128), SHA256 `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f`.
**Primary prior:** `docs/design/Andy_build0130_graphics_timing_budget_analysis.md`.
**Scope:** DESIGN ONLY. No implementation/edit/build/diagnostic-ROM. Genesis-only runtime code labeled `runtime_genesis_pc`/Genesis-WRAM; no arithmetic-offset proof. Labels **[OBS]** verified from source this task, **[INT]** interpretation.

> **BOTTOM LINE:** The narrowest safe fix is an **80-word, per-SAT-slot resident-code cache** (`sprite_tile_resident_code`) that **survives** the per-frame descriptor clear. `.Lpc090oj_emit_slot` sets the tile-DMA-needed bit by comparing the emitted 12-bit code against `sprite_tile_resident_code[slot]` (instead of the always-zeroed descriptor offset 8); `.Lvcs_tile_dma` updates the cache **after** a successful DMA. The mirror stays canonical, SAT position/link/palette/priority and full SAT DMA stay per-frame, and **only redundant sprite tile-pattern DMA stops happening**. Per-slot VRAM is exclusively owned (tiles 1024–1343), so residency is valid until an external writer touches that region — the single open safety question is whether `load_scene_tiles` can write tiles ≥1024 (Q4), resolved by a mandated Cody LUT check with a cheap invalidation fallback.

---

## == PHASE 0 ==

- **Relevant priors:** Andy Build 0130 timing/budget (churn CONFIRMED; late-display SUPPORTED); Andy PC090OJ object-RAM-faithful architecture (mirror canonical); KF-021 (staged/true/linked SAT divergence — context); OPEN-001, OPEN-024.
- **High-rediscovery hazards:** KF-021 HIGH (staged SAT ≠ truth); the SAT slot is assigned by **emission order** (`pc090oj_emitted_count`), not PC090OJ entry index — a cache keyed by slot must be reasoned for correctness under emission-order shifts (done below).
- **Task classification:** Narrow performance-correctness DESIGN extending OPEN-024 (churn) / OPEN-001 (title timing).
- **Contradiction detected:** NO.
- **Open/Closed pre-check:** OPEN-024 primary (churn), OPEN-001 context; not closing either.
- **Build 0130 baseline:** verified `79ec8a30…f5bc6f`, byte-identical to Build 0128.
- **Confirmed churn summary:** `.Lvcs_mirror_scan` (pc090oj_hooks.s:947) calls `.Lvcs_clear_generated_sprite_state`, which zeroes the whole descriptor table incl. offset-8 old-tile (936-940); `.Lpc090oj_emit_slot` reads offset 8 as old tile (126) → always 0 → changed-bit 0x0004 always set for nonzero codes (147-150); `.Lvcs_tile_dma` gates on that bit (1131) → 23×64 = **1472 tile-DMA words/frame** at title + fixed **320-word SAT DMA/frame** (1200-1204).
- **address_map.json loaded:** YES (all sites Genesis-native; no arcade↔genesis arithmetic used).
- **arithmetic offset used as proof:** NO.

---

## == CACHE DESIGN VERDICT ==

**Recommended cache shape:** **per-SAT-slot resident-code cache** — one 16-bit word per SAT slot (80 words) holding the 12-bit PC090OJ tile code currently resident in that slot's owned VRAM, with the value **0x0000 reserved as the "cold / no residency" sentinel** (code 0 is never emitted — the scan skips it at pc090oj_hooks.s:977-978 — so 0 can never be a legitimate resident code, making it a free, unambiguous sentinel; no separate valid bit needed).

Evaluated against the task's four options:
- **per-SAT-slot resident code** — chosen. Minimal; matches the existing slot-derived VRAM tile index; no allocator.
- **per-SAT-slot resident code + valid bit** — unnecessary; the 0x0000 sentinel folds the valid bit into the code word.
- **per-SAT-slot resident code + source/blank/status** — over-scoped; blank/offscreen entries are never emitted, so they never reach a slot; status adds no safety.
- **code→VRAM residency shared across slots** — REJECTED for the first fix: the SAT tile index is `(SPRITE_TILE_BASE + slot*4)` (pc090oj_hooks.s:1171-1174), i.e. VRAM is **slot-owned, not code-owned**. A shared cache would require a VRAM allocator (assign/refcount/evict per unique code) — a broad rewrite, explicitly out of scope.

**Why this is the narrowest safe fix:** it changes exactly one decision — *the source of the "tile changed" comparison* — from the wiped descriptor offset 8 to a persistent 80-word array, plus a post-DMA cache write. No producer, no mirror, no SAT-layout, no allocator, no scene_load change (pending Q4). Correctness holds even when emission order shifts: each slot's VRAM is exclusively owned and always re-DMA'd on any code mismatch, then the cache is updated — VRAM and cache never diverge, and slot X's SAT always points at slot X's VRAM.

**What remains canonical:** the PC090OJ object RAM mirror (`pc090oj_object_ram`). The cache is a pure render-side residency optimization derived from mirror-scan output; it is never a sprite-truth source.

**What remains per-frame:** the full mirror scan, descriptor/SAT clear + rebuild, SAT Y/X position, link chain, palette/priority, and the full 320-word SAT DMA — all unchanged.

**What no longer happens every frame:** re-DMA of sprite tile patterns whose slot already holds the same code. On a stable title (23 sprites, stable emission order) sprite tile DMA drops to ~0 words/frame after the first frame.

---

## == CACHE STORAGE / LIFETIME ==

- **WRAM symbols:** `sprite_tile_resident_code` — new `.bss` array in `pc090oj_hooks.s` alongside `staged_sprite_*`. (Optional counter `sprite_tile_dma_words` for evidence, not required for function.)
- **Size:** `80 * 2 = 160 bytes` (one word per SAT slot, matching the 80-slot descriptor/SAT tables).
- **Initialization:** all 80 words = sentinel **0x0000** before the first VBlank commit. Sentinel 0x0000 is chosen so that **existing boot-time WRAM/.bss zeroing is sufficient** — if Cody confirms the boot path zero-fills the BSS/WRAM region containing this symbol, **no boot.s edit is needed**. If BSS is not guaranteed zeroed, add a tiny explicit clear loop (80 words → 0) called once from the existing boot/init sequence.
- **Invalidation:** only when the slot-owned sprite VRAM (tiles 1024–1343 / bytes 0x8000–0xA800) is written by something other than `.Lvcs_tile_dma`. Normal steady/transition rendering never does this (each slot owns 4 disjoint tiles). Triggers: (a) boot/VDP init (covered by Initialization), (b) `load_scene_tiles` **iff** it can target ≥ tile 1024 (Q4 — pending Cody LUT check), (c) any future path that re-runs `vdp_boot_setup` or bulk-uploads sprite VRAM.
- **Scene-load interaction:** **PREFERRED** — Cody proves the PC080SN tile-VRAM LUT max index < 1024, then `load_scene_tiles` cannot touch sprite VRAM and **no scene_load.s change is needed** (honors "do not optimize scene_load.s"). **FALLBACK** — if the LUT can reach ≥1024, a minimal cache-invalidation (80-word clear to 0x0000) must run after each `load_scene_tiles`; this is a correctness hook, not an optimization, but because it expands scope into the scene-load path it is a **STOP-to-confirm** with the user.
- **VDP reset interaction:** the crash handler halts (does not resume rendering), so no cache concern there. Any deliberate VDP re-init that re-uploads VRAM must clear the cache; none exists in the steady path, so for this fix the boot init suffices. Flag as a documented invariant.

---

## == CODE PATH DESIGN == (labels, not patch code)

**`.Lvcs_clear_generated_sprite_state`:** **UNCHANGED in behavior** — it still clears `staged_sprite_sat`, `staged_sprite_descriptor_table`, `staged_sprite_dirty`, `staged_sprite_active_count` every scan for per-frame validity/link rebuild. Add only a documentation invariant: **it must NOT touch `sprite_tile_resident_code`** (the cache's persistence is the entire point).

**`.Lpc090oj_emit_slot`:** replace the changed-bit source. Currently: `move.w 8(%a0),%d6` (old tile, always 0 post-clear) then `cmp.w %d3,%d6` (126,148-150). New: compute the resident-cache address for the current slot `d0` (`sprite_tile_resident_code + d0*2`), read the resident code, compare against the emitted code masked to 12 bits `(d3 & 0x0FFF)`; set flag bit `0x0004` only if they differ. **The cache is READ here, never WRITTEN here** (writing before the DMA would falsely mark VRAM resident). The descriptor offset-8 write (132) may remain (harmless) or be dropped; offset 8 is no longer the comparison source. This logic is only consequential for scan-emitted descriptors — legacy-producer emit_slot calls set descriptors that the next scan's clear wipes before `.Lvcs_tile_dma`, so producer semantics are untouched.

**`.Lvcs_tile_dma`:** keep the valid-bit (btst #0) and changed-bit (btst #2, line 1131) gates and the existing masked tile read `move.w 8(%a0),%d2; andi.w #0x0FFF,%d2` (1134-1135). After the DMA registers are programmed and the changed bit is cleared (`andi.w #0xFFFB,(%a0)`, 1191), **write the DMA'd code into the cache: `sprite_tile_resident_code[slot] = (d2 & 0x0FFF)`**. On a cache hit (changed bit not set) the slot is skipped exactly as today and the resident entry is correctly left intact.

**Boot/init:** ensure `sprite_tile_resident_code` = all 0x0000 before the first commit (via existing BSS zeroing if confirmed, else an explicit 80-word clear called from boot init).

**Invalid/blank/offscreen behavior:** code-zero/blank/unmapped/offscreen entries are **skipped by the scan** (pc090oj_hooks.s:977-1021) and never consume a slot → they never read or write the cache. The `.Lpc090oj_emit_invalid` path sets descriptor word0 = `0x8000` with **no** changed bit and **no** valid bit → `.Lvcs_tile_dma`'s valid gate rejects it → no DMA, no cache write. Resident entries are therefore **left intact** across frames where a slot is idle (see Q6 rationale below).

**Same-code/multi-slot behavior:** each slot compares only against its **own** resident entry, so if the same code occupies slots 3 and 7 both DMA into their own VRAM (duplicate upload across distinct slots) — accepted for the first fix (no shared residency; see Q7).

### Q6 decision — leave resident code intact on invalid/blank/offscreen (do NOT invalidate)
**Safer.** Per-slot VRAM (4 tiles) is exclusively owned; while a slot is idle nothing overwrites its VRAM, so its residency stays valid. If the sprite later returns to that slot with the same code → cache hit → correctly skip DMA. Invalidating on idle would force needless re-DMA on return with zero safety benefit. The only thing that can make residency stale is an external writer to tiles 1024–1343 (boot/scene-load), handled by Initialization/Invalidation — not by per-sprite state.

### Q7 decision — duplicate cross-slot uploads acceptable
**Confirmed acceptable** as the narrow first fix. The cache eliminates the frame-over-frame redundancy (the confirmed churn); intra-frame duplication across different slots holding the same code remains, and removing it would require the rejected shared code→VRAM allocator.

---

## == SAFETY AGAINST SCAFFOLDING ==

- **PC090OJ mirror preserved:** YES — `pc090oj_object_ram` remains the sole canonical sprite state; the cache is derived from scan output only.
- **Producer semantics preserved:** YES — no producer/hook changed; legacy emit_slot mirror-bridge behavior unchanged; the changed-bit source change only affects scan-emitted descriptors consumed by tile DMA.
- **SAT/staging not canonical:** YES — SAT/descriptors are still rebuilt every frame from the mirror; the cache never feeds sprite truth.
- **No fake sprites:** YES — nothing synthesized; the cache stores only real codes actually DMA'd.
- **No 30 FPS fallback:** YES — full 60 Hz path; the change reduces work, not rate.
- **No broad rewrite:** YES — one comparison source + one post-DMA write + one BSS array; `.Lpc090oj_emit_slot` is **not** split.

---

## == EXPECTED IMPACT ==

- **Before:** 1472 sprite tile-DMA words/frame at title (23 emitted × 64), unconditional, every frame; + 320-word SAT DMA.
- **After:** frame 1 (cold cache) up to 1472 words (all miss); **steady title (stable 23 sprites, stable emission order): ~0 sprite tile-DMA words/frame** after warm-up; SAT DMA unchanged at 320 words.
- **Expected tile DMA reduction:** ~1472 → ~0 words/frame in steady title state (≈100% of the confirmed churn); sprite VDP DMA drops ~1792 → ~320 words/frame. Transient re-DMA only on frames where a slot's emitted code actually changes (packing shift, animation, sprite entering/leaving).
- **Expected display-on timing impact:** shrinking the display-off commit window by ~1472 DMA words should pull checkpoint 0x0B (DISPLAY_ON) earlier → more frames restoring display **inside** VBlank → SUPPORTS mitigating the Q1 rolling-slit. **Not claimed to fully fix** late-display (BG/FG strip bursts and other contributors remain; magnitude unproven without the HV/VCounter diagnostic).
- **Risks:** (1) emission-order packing shifts cause transient (correct) re-DMA — benign; (2) scene-load overwrite of sprite VRAM if disjointness is false and invalidation omitted → addressed by Q4 mandate/STOP; (3) reliance on BSS-zeroing for cold state → addressed by explicit-init fallback; (4) a future VRAM-reupload path added without cache clear → documented invariant.

---

## == CODY IMPLEMENTATION PLAN ==

**Files allowed:** `apps/rastan-direct/src/pc090oj_hooks.s` (cache array + emit_slot compare + tile_dma post-DMA write); optionally `apps/rastan-direct/src/boot/boot.s` (one init call) **only if** BSS is not zero-guaranteed. **No** scene_load.s edit unless the Q4 fallback triggers (then STOP-to-confirm first).

**Exact implementation steps:**
1. Add `.bss` array `sprite_tile_resident_code : .space (80*2)` in pc090oj_hooks.s; add `.global`.
2. Confirm boot zeroes this WRAM/.bss region; if not, add an 80-word clear-to-0 init called once from boot init.
3. In `.Lpc090oj_emit_slot`: change the changed-bit determination to compare `(d3 & 0x0FFF)` against `sprite_tile_resident_code[d0]`; set `0x0004` on mismatch. **Do not write the cache here.**
4. In `.Lvcs_tile_dma`: after the DMA + existing changed-bit clear, write `sprite_tile_resident_code[slot] = (offset8 & 0x0FFF)`.
5. Leave `.Lvcs_clear_generated_sprite_state` untouched; add a comment that it must not clear the cache.
6. **Q4 gate first:** determine the max Genesis VRAM tile index in `genesistan_pc080sn_tile_vram_lut` / the scene preload manifests. If `< 1024` → done (no scene_load change). If `>= 1024` → STOP and confirm adding a post-`load_scene_tiles` cache invalidation.

**Runtime evidence required:** build number/SHA/size; source files changed; canonical gate + invariant (`opcode_replace` count, `total_genesis_bytes_covered` — expect helper growth only); title `pc090oj_emitted_count` (expect 23); sprite tile-DMA words/frame **before (1472)** and **after** (expect ~0 steady, warm-up spike frame 1); optional later HV/VCounter diagnostic for display-on inside/outside VBlank; title screenshots.

**Regression evidence required:** title score sprites still present (22/27 maintained, codes 0x2A–0x49); SAT link-chain validity; sprites animate/move correctly (position/palette/priority still per-frame); no source/staging canonical bypass (mirror still sole truth); scene transitions (coin/start, ROUND) render correctly (proves no stale sprite VRAM after any scene load).

**STOP conditions:**
- The cache cannot be initialized to a safe cold state (neither BSS-zero confirmed nor a safe explicit init exists).
- The sprite VRAM region (tiles 1024–1343) can be overwritten by scene loads **without** a detectable invalidation point (Q4 fallback) — STOP and confirm the scene_load invalidation before proceeding.
- The implementation would require making SAT/staging canonical.
- The implementation would require removing the PC090OJ object RAM mirror.
- The implementation would require a broad `.Lpc090oj_emit_slot` rewrite / producer-semantic change.
- The implementation would require a 30 FPS fallback.

---

## == OPEN / KNOWN FINDINGS IMPACT ==

- **Open issues touched:** OPEN-024 (sprite tile-DMA churn fix design; not closed), OPEN-001 (title display-off timing context; not closed).
- **Issues not closed:** OPEN-024, OPEN-001 (design only; awaits implementation + evidence).
- **Findings to update later:** on successful implementation, add a KNOWN_FINDINGS entry — "sprite tile DMA is residency-cached per SAT slot; descriptor offset 8 is no longer the change source; cache invalidation required if any path writes sprite VRAM tiles 1024–1343." Update the Q4 disjointness result.
- **Deferred work:** `.Lpc090oj_emit_slot` producer/render split (Q4-D of the timing analysis, OPEN-024); HV/VCounter diagnostic to quantify display-on lateness; shared code→VRAM residency (only if duplicate cross-slot uploads later prove costly); `scene_load.s` optimization (out of scope).

AGENTS_LOG updated: YES
STOP status: NO — design complete; single pending safety gate (Q4 scene-load VRAM disjointness) is delegated to Cody as a verify-first step with a defined fallback + STOP.
