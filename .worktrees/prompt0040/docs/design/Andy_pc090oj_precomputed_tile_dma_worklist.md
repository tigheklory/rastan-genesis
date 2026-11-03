# Andy — PC090OJ Precomputed Tile-DMA Worklist and Minimal DISPLAY_OFF Commit (Design / Static Only)

**Author:** Andy
**Date:** 2026-07-06
**Baseline:** Build 0140, `dist/rastan-direct/rastan_direct_video_test_build_0140.bin`, SHA256 `f6e63eb3e3a6d5e82caf9e151ef2eb1c23418633ee7118adad51f1c2081a135c`.
**Primary evidence:** `docs/validation/Cody_pc080sn_pc090oj_two_environment_profile_build_0140.md` + `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/`.
**Scope:** Static design only. **No** implementation/source/spec/tool/Makefile/ROM/build/bookmark/runtime change. Mappings from `address_map.json`, no arithmetic. Labels **[OBS]** source-verified; **[EVID]** profiling; **[INT]** interpretation.

---

## 1. Executive decision

**Outcome A — implementation-ready.** The DISPLAY_OFF interval is ~93% wasted in stable frontend frames: **11,088 cycles (68%)** re-scanning a **fixed 80-slot** tile-DMA/residency loop that issues **zero** transfers, plus **~4,000 cycles** clearing 80 descriptor touched-flags that the next frame wipes anyway. The residency **decision** is already made before DISPLAY_OFF (the code-vs-resident compare in the emit path). The fix: during `vdp_prepare_sprites` (before DISPLAY_OFF), when a drawable's code ≠ its resident code, **append a compact `{slot, code}` entry to a pending tile-DMA worklist**; inside DISPLAY_OFF, iterate **only that worklist** (count-bounded, usually 0) + the existing SAT DMA. Remove the 80-slot scan and the redundant descriptor clear. This turns the sprite DISPLAY_OFF cost from ~15,674 cycles to **~600 cycles** in stable frames, shrinking the black-strip height from ~33 scanlines toward ~2–3, with **no** frame-model change, no FRONT/BACK, no content diffing, no extra latency, and the arcade mirror untouched.

---

## 2. Current loop inventory [OBS `pc090oj_hooks.s`; EVID PC ranges]

| Routine (PC) | Loop bound | Scans | Per-iteration work | Phase | Needed if 0 producer writes? | Needed if 0 tile-DMA? |
|---|---|---|---|---|---|---|
| `rastan_direct_update_inputs` | — | inputs | read pad | **pre-OFF** | yes | yes |
| `vdp_prepare_sprites` → `.Lvcs_mirror_scan` (`0x072168`) | 256 | **256 arcade records** (candidate-gated) | check candidate bit; decode ~42; `emit_slot` per drawable | **pre-OFF** | scan yes (cheap for non-candidates); decode only if candidate | yes (decides changes) |
| ↳ `.Lvcs_clear_generated_sprite_state` (in scan) | 80+80 | **80 SAT + 80 descriptors** | `clr.w` wipe (800 words) + counters | **pre-OFF** | yes (per-frame reset) | yes |
| ↳ `.Lpc090oj_emit_slot` (residency compare, 145-164) | per drawable | resident[slot] | `(code&0xFFF)` vs `resident[slot]`; set changed bit | **pre-OFF** | for each drawable | **this is where the change decision is made** |
| `vdp_prepare_sprites` → `.Lvcs_link_chain_build` (`0x072312`) | 80 | **80 SAT slots** | link valid slots in order | **pre-OFF** | yes (per-frame) | yes |
| `vdp_commit_sprites_vram` → **`.Lvcs_tile_dma` (`0x072380`)** | **80** | **80 SAT slots** | `mulu.w #12` (~40cy) + descriptor fetch + `btst #0`/`btst #2`; DMA only if changed | **INSIDE OFF** | **NO** (re-discovers the pre-made decision) | **NO** (0 changed ⇒ 0 DMA, but still scans 80) |
| `vdp_commit_sprites_vram` → `.Lvcs_sat_dma` (`0x072442`) | — | active_count | one DMA, `active_count×4` words | **INSIDE OFF** | yes | yes |
| `vdp_commit_sprites_vram` → **`.Lvcs_clear_dirty` (`0x0724D2`)** | **80** | **80 descriptors** | `move.w`/`andi #0x7FFF`/`move.w` touched-flag clear + `clr.l dirty` | **INSIDE OFF** | **NO** (redundant with next `clear_generated`) | **NO** |

**Loops that must not exist inside DISPLAY_OFF:** `.Lvcs_tile_dma`'s 80-slot scan and `.Lvcs_clear_dirty`'s 80-descriptor clear — both are fixed-80, both are pure CPU with zero required work in stable frames.

---

## 3. The 11,100-cycle residency cost [EVID + OBS]

`.Lvcs_tile_dma` (PC `0x072380`, "sprite-pattern residency checks", **11,088 / 11,088 / 11,286 cyc = ~68%**) is a **fixed 80-iteration loop** [OBS `pc090oj_hooks.s:1130-1217`]. Per slot it executes `move.w %d7,%d0; mulu.w #12,%d0; lea …; adda.l …; move.w (%a0),%d1; btst #0; btst #2; …`. The `mulu.w #12` alone is ~38–70 cycles on the 68000; with the descriptor fetch and two `btst` gates, ~130–140 cycles/slot × 80 ≈ **~11,100 cycles**, matching the measurement. **The residency *decision* (`code ≠ resident[slot]`) was already computed before DISPLAY_OFF** inside `.Lpc090oj_emit_slot` (lines 145-164) and recorded as the descriptor changed bit. So this loop is a **rediscovery scan**: with 0 producer writes → 0 changed → 0 DMA, it still walks all 80 slots inside DISPLAY_OFF only to conclude "nothing to transfer." That is the 68% waste.

## 4. The 4,128-cycle other-sprite cost [EVID + OBS]

"Other sprite commit work" (PC `0x0724D2 → 0x0700E6`, **4,128 cyc = ~25%**) is `.Lvcs_clear_dirty` [OBS `pc090oj_hooks.s:1260-1270`] + the commit wrapper glue. Components and classification:

| Component | Cost | Classification |
|---|---|---|
| `.Lvcs_clear_dirty` 80-descriptor touched-flag clear (`move.w`/`andi #0x7FFF`/`move.w`/`adda #12`/`dbra`) | ~4,000 | **may be ELIMINATED** — redundant: next frame's `.Lvcs_clear_generated_sprite_state` zeroes the entire descriptor table; nothing reads the touched flag between DISPLAY_ON and that wipe |
| `clr.l staged_sprite_dirty` | ~12 | **may be eliminated** — also re-cleared by `clear_generated`; SAT DMA is active-count-based (Build 0137), not dirty-block-based, so `staged_sprite_dirty` is vestigial for the DMA gate |
| `movem` restore + `rts` + `bsr`/return glue for `vdp_commit_sprites_vram` | ~116 | **must remain** (unavoidable call overhead) |

So **~4,000 of the 4,128 is eliminable inside DISPLAY_OFF** (bounded by nothing — it is dead cleanup); only ~116 cycles of wrapper glue is retained.

## 5. The 18,112-cycle pre-DISPLAY_OFF gap [EVID + OBS]

Table D's five listed pre-OFF components (candidate traversal 31,626 + decode 12,562 + emit 2,162 + SAT-packing 0 + link 12,814 = 59,164) exclude the fixed remainder to the 77,276 total = **18,112 cycles**. Source-level owner: **`.Lvcs_clear_generated_sprite_state`** (80-SAT + 80-descriptor `clr.w` wipe = 800 words ≈ ~6,400 cyc + counter clears) + **`rastan_direct_update_inputs`** + **`vdp_prepare_sprites` movem/wrapper/bsr glue** + the DISPLAY_OFF register-write setup. Classification: **fixed table-clearing + input + wrapper overhead, semantically necessary per-frame, and it runs BEFORE DISPLAY_OFF — it does NOT contribute to the black-strip height.** It is owned by the same PC090OJ prep architecture, so it *can* be reduced (bound the `clear_generated` wipe to `active_count`/prev-emitted instead of a fixed 80), but that is an **adjacent optional reduction, out of this task's minimal DISPLAY_OFF scope** (§12). Do not expand the implementation to it unless a later task targets pre-OFF VBlank time.

**Table C label correction [EVID].** Frames 100/250/960 had **0 producer writes**, so "Activations 23/23/32" cannot be activation events and "SAT shifts 22/22/31" cannot be slot-shift events. They equal the **Drawables-emitted / Active-sprites** counts (23/23/32) and **active_count − 1** (22/22/31 = link-chain edge count / terminator relationships). Correct meaning: **active/drawable count** and **number of intra-chain links**, not lifecycle events. Do not propagate the "Activations/SAT shifts" labels.

---

## 6. Worklist representation

**Entry (minimum): `{ slot: u16, code: u16 } = 4 bytes.`** Everything a transfer needs is derivable from these two at commit time — the same derivations `.Lvcs_tile_dma` already does, now only for actual transfers instead of 80 slots:
- **source** = `rastan_pc090oj + (code & 0x0FFF)*128`, DMA source `= /2`;
- **VRAM destination** = `(SPRITE_TILE_BASE + slot*4)*32` (sprite tile region, tiles 1024–1343);
- **transfer length** = fixed **64 words** (one 4-tile sprite pattern);
- **residency owner** = `sprite_tile_resident_code[slot]`;
- **new resident code** = `code`, committed **after** the DMA (§7).

- **Maximum entry count:** **80** (one SAT slot can appear at most once per frame; ≤ 80 emitted). Overflow is **structurally impossible** (≤ 80 slots, ≤ 1 append each).
- **WRAM cost:** `80 × 4 = 320 B` table + `2 B` count = **322 B** (`pc090oj_tile_dma_worklist`, `pc090oj_tile_dma_count`), appended above the ~0xFF7106 BSS high-water; ~34 KB free — trivial.
- **Producer/preparation cost:** one append (write `{slot,code}`; `count++`) **only on a residency mismatch**, inside the pre-OFF emit path where the compare already occurs — near-zero added pre-OFF cost (0 appends in stable frames).
- **Append order:** emission order (ascending SAT slot), which is also the natural DMA order; irrelevant to correctness (disjoint VRAM destinations).
- **Publication point:** the worklist is fully built when `vdp_prepare_sprites` returns, **before** DISPLAY_OFF; `count` is written last per append (§8).
- **Overflow behavior:** cannot occur (cap = 80 = max slots). A defensive `count < 80` guard on append routes any impossible excess to the permanent fallback (§7) — never in a normal frame.
- **Zero-entry behavior:** commit sees `count == 0`, skips the loop entirely (a single compare), proceeds to SAT DMA. **This is the common stable-frame path.**
- **Ordering / duplicates:** each slot appends at most once (the emit visits each slot once), so **no duplicates can occur**; no dedup needed.
- **Packed SAT-slot shift:** residency is slot-keyed; if a slot now holds a different arcade record, its emitted code ≠ resident → mismatch → appended → DMA'd → resident updated. Self-correcting (unchanged from current semantics).
- **Tile-code change:** the compare catches it → append.
- **Slot deactivation:** a slot beyond `active_count` is not emitted → not appended; its stale resident/VRAM is unreachable via the link chain → harmless.
- **Scene transition:** sprite tile VRAM (tiles 1024–1343) is **exclusively sprite-owned** (PC080SN was relocated to 0..1023 + 1344..1503 per the VRAM-ownership design), so scene loads never overwrite it → **no residency invalidation is required**. (Invariant to preserve; if that ownership ever changes, invalidate residency + worklist on scene load.)

---

## 7. Residency-state rules

- **Compare before DISPLAY_OFF:** in the emit path (`.Lvcs_mirror_emit` / `.Lpc090oj_emit_slot`, `scan_active == 1` only), compute `code = emitted tile code & 0x0FFF`; if `code != sprite_tile_resident_code[slot]` → **append `{slot, code}`** to the worklist (`count++`). Legacy producer emits (`scan_active == 0`) must **not** append.
- **Append DMA work only where required:** exactly on mismatch; matching slots append nothing (the common case).
- **Update `sprite_tile_resident_code[slot] = code` only AFTER the DMA is guaranteed executed** — i.e., in the DISPLAY_OFF commit, immediately after the DMA trigger (the 68000 stalls on the bus through the VRAM DMA, so the next instruction runs post-completion). **Never mark resident at append/queue time.**
- **Worklist overflow:** impossible under the ≤80 invariant; the defensive fallback (`count` would exceed 80) is a **permanent bounded full-slot DMA of all emitted slots** — used only in that impossible case, **never re-introducing the fixed 80-scan in normal frames.**
- **Interrupted/aborted presentation:** the worklist is built and consumed within one VBlank handler; if the handler cannot run, no partial state is committed (resident is updated only per-DMA). No cross-frame partial worklist survives (count reset each frame, §8).
- **Packed slot belongs to a different record / active_count shrink or grow:** handled by the slot-keyed compare (mismatch → re-DMA; shrunk slots unreachable; grown slots emitted+compared). No extra logic.
- **The resident state represents data actually transferred to VRAM** — the update is strictly post-DMA, never post-append.

---

## 8. DISPLAY_OFF sequence (replacement `vdp_commit_sprites_vram`)

Pre-OFF (`vdp_prepare_sprites`): reset `pc090oj_tile_dma_count = 0` at scan start; scan/emit appends worklist entries on mismatch; build SAT + link chain (unchanged). Then DISPLAY_OFF. Then:

```
; display already off
1. move.w pc090oj_tile_dma_count, d7 ; beq -> step 4   (zero-entry fast path)
2. for i in 0 .. count-1:
     slot = worklist[i].slot ; code = worklist[i].code
     source = rastan_pc090oj + code*128 ; DMA src = source/2
     dest   = (SPRITE_TILE_BASE + slot*4)*32
     program VDP DMA regs (len=64 words, src, dest+DMA-bit); trigger   ; 68k stalls to completion
     sprite_tile_resident_code[slot] = code                            ; post-DMA (safe)
3. (end loop)
4. SAT DMA: active_count*4 words -> 0xF800    ; unchanged (.Lvcs_sat_dma)
5. minimal cleanup: none required (descriptor/SAT/dirty are wiped by next frame's clear_generated)
6. rts -> DISPLAY_ON
```

- **Bounded by `pending_tile_dma_count + 1 SAT DMA`, NOT by 80.**
- **Residency-update timing:** immediately after each DMA trigger (= after completion, via bus-stall) — no separate pending-to-resident list needed; no CPU wait-poll required (VRAM DMA holds the bus).
- `.Lvcs_clear_dirty` is **removed** (step 5 = nothing); the descriptor/dirty state is reset by the next frame's `clear_generated_sprite_state` (already runs pre-OFF).

---

## 9. Old-path removal table

| Component | Classification | Successor / rationale |
|---|---|---|
| `.Lvcs_tile_dma` fixed 80-slot scan (`0x072380`) | **REPLACE** | worklist iteration bounded by `pc090oj_tile_dma_count`; the residency compare stays in the pre-OFF emit path |
| `.Lvcs_clear_dirty` 80-descriptor touched-flag clear (`0x0724D2`) | **REMOVE** | redundant with next-frame `clear_generated_sprite_state`; nothing reads the touched flag before that wipe |
| `clr.l staged_sprite_dirty` in clear_dirty | **REMOVE** | vestigial (SAT DMA is active-count-based since Build 0137); re-cleared by `clear_generated` |
| descriptor "changed" bit (0x0004) as the DMA gate (`emit_slot` 147-164) | **REPLACE** | the worklist entry is the gate; the compare stays but publishes a worklist append instead of gating an 80-scan (the descriptor bit may be dropped) |
| `.Lvcs_mirror_scan`, `.Lvcs_link_chain_build`, `.Lvcs_sat_dma`, mirror, candidate bitset, `sprite_tile_resident_code` | **RETAIN** | unchanged (residency array is now written only by the worklist commit) |
| `.Lvcs_clear_generated_sprite_state` 80-wipe (pre-OFF, part of §5's 18,112) | **RETAIN** (optional later reduction) | out of this task's minimal DISPLAY_OFF scope |

No obsolete scan remains as a fallback; the overflow fallback (§7) is a bounded full-slot DMA, never the fixed 80-*scan*, and never in normal frames.

---

## 10. Interrupt / ownership proof

The worklist is built by `vdp_prepare_sprites` and consumed by `vdp_commit_sprites_vram` — **both inside the same `_vblank_service` invocation, sequentially, on the single 68000**. Therefore:
- **Producers cannot modify the mirror during preparation** — main-loop PC090OJ producers are preempted while the VBlank handler runs; no producer executes between prepare and commit.
- **The worklist is complete before DISPLAY_OFF consumes it** — prepare runs to completion (all appends done) → DISPLAY_OFF → commit reads the finished `count`.
- **`count` cannot expose a partial entry** — each append writes the `{slot,code}` payload then increments `count` (count-last); but even without that, no consumer runs during prepare (sequential), so partial exposure is impossible. **No interrupt masking is needed** (single handler, no preemption within it).
- **Cleanup cannot erase next-frame producer state** — the commit writes only `sprite_tile_resident_code` (slot-keyed VRAM residency); producers write the mirror + candidate bitset, which the commit never touches. `count` is reset at the *next* frame's scan start, after this frame's consumption.
- **No extra frame of latency** — prepare→commit occur in the same VBlank as today; the mirror→SAT→VRAM path is unchanged in timing; only the *inside-OFF discovery scan* is removed.

---

## 11. WRAM cost

| Symbol | Size | Purpose |
|---|---:|---|
| `pc090oj_tile_dma_worklist` | 320 B (80 × 4) | `{slot:u16, code:u16}` entries |
| `pc090oj_tile_dma_count` | 2 B | pending entry count (reset each frame at scan start) |

Total **+322 B** in `pc090oj_hooks.s` `.bss`, above ~0xFF7106 (~34 KB free). No boot init strictly required (count is reset per frame in prepare), but a boot clear-to-0 is harmless and recommended for determinism.

---

## 12. Total-cost estimate [INT, instruction/loop-bound level — not a runtime measurement]

Current inside-DISPLAY_OFF sprite cost: **15,674** (100/250), **15,872** (960) = tile scan (~11,088/11,286) + clear_dirty+glue (~4,128) + SAT DMA (458).

| Scenario | Estimated inside-OFF sprite cost | vs current |
|---|---:|---|
| **0 tile-DMA entries (stable frames)** | `count==0` check (~10) + SAT DMA (458) + wrapper glue (~116) ≈ **~590** | −~15,080 (~96%) |
| 1 tile-DMA entry | ~590 + 1×(derive+DMA setup+64-word transfer ~430) ≈ **~1,020** | −~14,650 |
| several (e.g. 8) | ~590 + 8×~430 ≈ **~4,030** | −~11,600 |
| worst case (all 80 need DMA, e.g. scene change) | ~458 + 80×~430 ≈ **~34,900** | comparable/better than old (old = 80-scan + 80-DMA); rare transition frame |

- **Work moved before DISPLAY_OFF:** the residency *decision* was already pre-OFF; only a cheap append is added there (~0 in stable frames).
- **Work eliminated:** the 80-slot rediscovery scan (~11,100) and the redundant 80-descriptor clear (~4,000).
- **Work retained inside DISPLAY_OFF:** SAT DMA (458) + the actual required tile DMAs (0 in stable frames) + ~116 glue.
- **DISPLAY_OFF total (stable):** 16,350 → ~590 (sprite) + ~676 (non-sprite: tile/BG/FG/control) ≈ **~1,266 cycles** (from ~33 scanlines of display-off to ~2.6).
- **Total frame VBlank work** is ~unchanged (the pre-OFF 77,276 is untouched by this task); only the DISPLAY_OFF slice shrinks. No exact runtime saving is claimed without measurement.

---

## 13. Expected visible effect

The DISPLAY_OFF interval (the disabled-display window that becomes the black horizontal strip when the commit overruns VBlank into active scanout) shrinks from **~16,350 cycles (~33 scanlines)** toward **~1,270 cycles (~2.6 scanlines)** in stable frontend frames, by removing ~11,088–11,286 (tile scan) + ~4,000 (clear_dirty). **The strip is not promised to disappear** — the large pre-DISPLAY_OFF work (77,276 cyc, out of scope) still delays *when* DISPLAY_OFF starts, so a thin residual band may remain. Measurable success: **substantially shorter DISPLAY_OFF interval; visibly reduced black-strip height; unchanged sprite output; unchanged frontend progression; no missing sprite patterns; no SAT corruption.**

---

## 14. Implementation boundary

Smallest permanent change: (1) add `pc090oj_tile_dma_worklist` + `pc090oj_tile_dma_count`; (2) in the pre-OFF emit path (scan_active==1), append `{slot,code}` on residency mismatch; reset `count` at scan start; (3) replace `.Lvcs_tile_dma`'s 80-slot scan with a count-bounded worklist iteration (derive source/dest, DMA, then update `sprite_tile_resident_code[slot]`); (4) remove `.Lvcs_clear_dirty`. Files: **`pc090oj_hooks.s`** (all of the above) + **`boot/boot.s`** (optional count clear). `vdp_comm.s` unchanged (the commit-vram wrapper's call list drops `.Lvcs_clear_dirty`; that edit is in `pc090oj_hooks.s` if the wrapper lives there, else a one-line removal). **Excluded:** PC080SN changes, committed-shadow work, original-arcade readback work, PC090OJ field-level producer redesign, stable-slot allocator, palette/scroll, and the §5 pre-OFF `clear_generated` reduction. One numbered build for user visual testing.

---

## 15. Acceptance criteria

- Same sprite output as Build 0140 (identical SAT contents, link chain, active_count, `92/92/128` SAT-DMA words in the three reference frames).
- Stable frames issue **0** tile DMAs and iterate a **0-length** worklist (no 80-slot scan executes inside DISPLAY_OFF).
- On a producer-write/scene frame, exactly the mismatching slots DMA (worklist count = number of code changes), and `sprite_tile_resident_code` matches VRAM after commit.
- `sprite_tile_resident_code[slot]` updated **only after** its DMA (never at append).
- No missing/garbled sprite patterns; no SAT linkage corruption; no sprite disappearance.
- DISPLAY_OFF interval for the three reference frontend frames is **substantially shorter** (target ≪ 16,350 cyc); black-strip height visibly reduced in the user's BlastEm test.
- Frontend progression unchanged.
- Mapping (§16); no frame-model / VBlank-order / DISPLAY_ON-OFF-placement change.

## 16. Mapping and build acceptance

- `address_map.json` **gaps = 0**, **overlaps = 0**;
- expected changed sites documented (Genesis-only `pc090oj_hooks.s` growth; no patched-site or wrapper change);
- **unexpected mapping change = STOP**;
- wrapper bytes unchanged where no wrapper change is authorized;
- **no fixed `opcode_replace` count requirement** (record the Build 0140 count as baseline only);
- Build 0140 remains the comparison baseline.

## 17. Revert criteria

Revert on: any sprite-output mismatch vs Build 0140 (SAT, link chain, active_count, SAT-DMA words); a tile pattern not transferred when its code changed (missing/garbled sprite); residency marked before its DMA; a residency slot left stale after a real change; worklist overflow behavior differing from the defined fallback; SAT link corruption / sprite disappearance / ordering regression; VDP autoincrement or address-state corruption; the 80-slot scan reappearing in normal frames; any newly published worklist entry lost or a partial entry consumed; frontend-progression regression; unexpected `address_map.json` gap/overlap/patched-site change; a new exception; or a need for scaffolding.

---

## 18. Outcome

**Outcome A — implementation-ready PC090OJ worklist design complete.** The three DISPLAY_OFF costs are attributed to exact routines, the mislabeled Table C values are corrected, the worklist representation/residency rules/DISPLAY_OFF sequence/removal table/interrupt proof/WRAM/cost estimate are defined, and the change stays within the constraints (mirror preserved, no diffing, no latency, no frame-model change, no permanent parallel scan). No static dependency blocks implementation (not Outcome B); no residency/frame-semantics conflict (not Outcome C) — the worklist reproduces the current slot-keyed residency semantics exactly, only moving discovery out of DISPLAY_OFF.

## Exact next Cody task outline

**"Cody — Build 0141 PC090OJ precomputed tile-DMA worklist + minimal DISPLAY_OFF commit"**
- Files: `apps/rastan-direct/src/pc090oj_hooks.s` (+ optional `boot/boot.s` count clear). No PC080SN/spec/tool/Makefile change; no committed-shadow, no original-arcade readback, no producer/field redesign.
- Add `pc090oj_tile_dma_worklist` (320 B) + `pc090oj_tile_dma_count` (2 B); reset count at scan start; append `{slot,code}` on residency mismatch in the scan emit path (scan_active==1 only).
- Replace `.Lvcs_tile_dma` 80-slot scan with a count-bounded worklist commit (derive source/dest, DMA 64 words, then update `sprite_tile_resident_code[slot]`); remove `.Lvcs_clear_dirty`.
- Build one numbered ROM (Build 0141); confirm `address_map.json` gaps/overlaps = 0, no patched-site/wrapper change, only Genesis-only growth (`opcode_replace` recorded, not fixed).
- Evidence (MAME Genesis + native debugger; user BlastEm for visual): SAT/link/active_count/SAT-DMA parity vs Build 0140 in the three reference frames; 0-length worklist + no 80-slot scan inside DISPLAY_OFF in stable frames; measured DISPLAY_OFF cycle reduction; a producer-write/scene frame DMAs exactly the changed slots with correct post-DMA residency; user confirms reduced black-strip height, unchanged sprites, unchanged frontend progression.

**Confirmation:** no source, spec, tool, Makefile, ROM, build, bookmark, runtime, VBlank-order, DISPLAY_OFF/ON, or frame-pipeline changes were made — one design document and one AGENTS_LOG entry only.
