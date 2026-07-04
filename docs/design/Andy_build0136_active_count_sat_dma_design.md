# Andy — Build 0136 Active-Count SAT DMA Design (Design Only)

**Author:** Andy
**Date:** 2026-07-03
**Baseline:** Build 0136, `dist/rastan-direct/rastan_direct_video_test_build_0136.bin`, SHA256 `23dde0a0516378267f125cde34e0cd6328a21c559bc556d2b82f034d02916bd4`.
**Priors:** Cody Build 0136 candidate bitset; Andy candidate-bitset + DISPLAY_OFF-split design; Cody Build 0135 budget/scan-depth; Cody Build 0132 residency cache.
**Scope:** DESIGN ONLY. No implementation/edit/build/diagnostic-ROM. All addresses Genesis-native; no arcade↔genesis arithmetic. Labels **[OBS]** verified from Build 0136 source; **[INT]** interpretation.

> **BOTTOM LINE:** Uploading only `active_count × 4` SAT words is **provably safe** because (a) emitted sprites pack **contiguously** into SAT slots `0..active_count−1` (`emit d0 = emitted_count`), and (b) `.Lvcs_link_chain_build` terminates the **last active slot** with link=0 — so slots `active_count..79` are **unreachable by the VDP link chain** regardless of stale VRAM content. No extra terminator entry is needed (the last active entry *is* the terminator). The only hazards are a **zero-length DMA** (VDP treats length 0 as 0x10000 words) and the **contiguity precondition**; both are handled by `dma_words = max(active_count, 1) × 4`. **Recommend Option A**, one narrow change to `.Lvcs_sat_dma` length only. Honest caveat: the SAT DMA is a small slice of the display-off window (~0.5–1 scanline), so this reduces the band **modestly** and directly — the larger lever remains the deferred DISPLAY_OFF split.

---

## == PHASE 0 ==

- **Build 0136 baseline:** verified SHA `23dde0a0…916bd4`.
- **Candidate mask status:** implemented; reduces decoded records 256→~42 in stable title/story; same 23 emitted, 0 drops. **Preserved exactly by this design.**
- **Current SAT DMA:** `.Lvcs_sat_dma` uploads a fixed 320 words (80 entries × 4) unconditionally every frame — unchanged by Build 0136.
- **Owner direction:** make SAT DMA length depend on the final emitted/active SAT count (NOT candidate_count); everything else (mask, split, tile DMA, DISPLAY_ON order, PC080SN) unchanged.
- **Contradiction detected:** NO.

(Relevant priors: Build 0132 residency cache tile DMA 0 steady; my prior partition showing SAT DMA is a real 68k→VRAM DMA and is the only *unconditional* VDP work in the sprite commit. High-rediscovery hazard: VDP DMA length 0 = 0x10000-word transfer — must never be issued. address_map.json loaded: YES. arithmetic offset used as proof: NO.)

---

## == Q1 SAT LAYOUT / COUNT ==

- **entry size:** 8 bytes = **4 words** (word0=Y, word1=size|link, word2=attr[priority/palette/flip/tile], word3=X). [OBS]
- **maximum entries:** **80** (`staged_sprite_sat = .space (80*8)`; emit caps `emitted_count` at 80, pc090oj_hooks.s:1038-1042).
- **staging layout:** `staged_sprite_sat` (640 bytes, slot 0 first); dest VRAM `0xF800`.
- **active-count meaning (Q1.4):** `staged_sprite_active_count` = number of valid descriptors linked into the chain, set by `.Lvcs_link_chain_build` (`clr` then `addq #1` per valid slot, 1082/1113). Equals `emitted_count` (every scan-emitted drawable slot is valid).
- **packed order (Q1.5/1.6):** valid entries are **packed contiguously from slot 0** — the scan emits with `d0 = pc090oj_emitted_count`, incremented only on emit (1038/1054), so slots `0,1,2,…,active_count−1` are all valid; `active_count..79` are cleared-invalid. **SAT slot assignment == emitted order.** [OBS]
- **last-link guarantee (Q1.7):** the **last active slot's link = 0** — `.Lvcs_link_done` writes `0x0500` (link bits 0) to the last valid slot's SAT word1 (1119-1126). Intermediate slots link to the next valid slot (1105-1109).
- **tail reachability (Q1.8):** slots `active_count..79` are **unreachable** — the VDP follows the link chain from slot 0 and stops at the link=0 terminator (last active slot), never traversing the tail.
- **active-count finalized before `.Lvcs_sat_dma` (Q1.9):** YES — order is `mirror_scan → link_chain_build (sets active_count) → tile_dma → sat_dma`. active_count is final when sat_dma runs.

**Proof the active count can safely set DMA length:** valid entries are contiguous `0..active_count−1`; the terminator (link=0) sits at slot `active_count−1`, *within* the first `active_count` entries; the tail is unreachable. Therefore uploading exactly `active_count` entries transfers the whole reachable chain including its terminator. **Safe.** (Precondition: contiguity — guaranteed by emit-order packing; make it a Cody STOP check.)

---

## == Q2 CURRENT DMA ==

`.Lvcs_sat_dma` [OBS pc090oj_hooks.s:1219-1258]:
- **method:** real 68k→VRAM DMA.
- **fixed length:** `move.w #0x9340,(%a3)` (reg 0x13 low = 0x40) + `move.w #0x9401,(%a3)` (reg 0x14 high = 0x01) → length `0x140` = **320 words**, hardcoded.
- **source:** `staged_sprite_sat` (via regs 0x95/0x96/0x97 = address/2), slot 0.
- **destination:** VRAM `0x0000F800` (command `ori.l #0x40000080` = VRAM-write + DMA-enable).
- **DMA register writes:** 0x13/0x14 (length), 0x15/0x16/0x17 (source), then the dest command long.
- **trigger:** single `move.l %d1,(%a3)` (1257).
- **conditional:** always executes (no gate).
- **active-count usage:** NONE today — length is the literal 320 regardless of emitted/active count.

**Confirmed:** Build 0136 still uploads all 80 SAT entries every frame irrespective of the ~23 emitted.

---

## == Q3 VARIABLE LENGTH ==

- **selected count:** `staged_sprite_active_count` (NOT candidate_count).
- **formula:** `dma_words = max(active_count, 1) × 4`.
- **minimum:** 4 words (1 blank entry — zero-active guard, Q5).
- **maximum:** `80 × 4 = 320` (active_count ≤ 80 by emit cap; defensive clamp to 80).
- **at what point final (Q3.2):** after `.Lvcs_link_chain_build`, before `.Lvcs_sat_dma` (Q1.9).
- **68000 length calc (Q3.3):**
  ```
      move.w  staged_sprite_active_count, %d0
      bne.s   .Lsat_have_count
      moveq   #1, %d0                 ; zero-active → 1 blank entry
  .Lsat_have_count:
      cmpi.w  #80, %d0                ; defensive clamp
      bls.s   .Lsat_count_ok
      move.w  #80, %d0
  .Lsat_count_ok:
      lsl.w   #2, %d0                 ; ×4 → dma_words (≤320)
  ```
- **DMA-length register handling (Q3.4):** replace the two fixed writes with:
  ```
      move.w  %d0, %d1
      andi.w  #0x00FF, %d1
      ori.w   #0x9300, %d1            ; reg 0x13 = length low byte
      move.w  %d1, (%a3)
      move.w  %d0, %d1
      lsr.w   #8, %d1
      andi.w  #0x00FF, %d1
      ori.w   #0x9400, %d1            ; reg 0x14 = length high byte
      move.w  %d1, (%a3)
  ```
  (e.g. 92 → low 0x5C/high 0x00; 128 → low 0x80/high 0x00; 320 → low 0x40/high 0x01.)
- **320-word max enforced (Q3.5):** active_count ≤ 80 (emit cap) → ×4 ≤ 320; the defensive `cmpi #80` clamp guarantees it even if the invariant were violated.
- **source/destination unchanged (Q3.6):** YES — source `staged_sprite_sat`, dest `0xF800`, regs 0x15/0x16/0x17 and the dest command long unchanged; only the 0x13/0x14 length writes become variable.
- **DMA starts at slot 0 (Q3.7):** YES — source is `staged_sprite_sat` (slot 0), dest `0xF800` (SAT slot 0); uploads slots `0..active_count−1`.

---

## == Q4 SHRINK SAFETY == (32 active → 23 active)

- **last-link:** the 23rd active entry (slot 22) has **link=0** — `.Lvcs_link_done` sets the last valid slot's link to `0x0500` (link bits 0), and slot 22 is within the uploaded `0..22` range, so the fresh terminator is uploaded. [OBS]
- **stale tail:** VRAM SAT slots 23..31 retain frame N's data, but the chain terminates at slot 22 (link=0) → the VDP **never traverses** to slot 23+. Unreachable.
- **terminator need (Q4.4):** **no extra terminator entry needed** — the last active entry *is* the terminator (link=0), and it is uploaded. Option B's `+1` entry is unnecessary.
- **no stale sprite visible:** the tail is unreachable; nothing from frame N slots 23..31 renders.
- **sufficiency (Q4.5):** uploading exactly `active_count` entries is sufficient when the chain shrinks, because the terminator moves *down* to slot `active_count−1` (rewritten every frame by `.Lvcs_link_chain_build`) and is within the uploaded range.

**classification: SAFE.** `.Lvcs_link_chain_build` guarantees the last active slot's link=0 every frame (1119-1126); the tail is unreachable. (If Cody finds any frame where the last active slot's link ≠ 0 → STOP; that would be a link-builder bug, not addressed here.)

---

## == Q5 ZERO ACTIVE ==

- **blank slot (Q5.1):** YES — `.Lvcs_clear_generated_sprite_state` zeroes all 80 SAT entries before every scan (929-940), so slot 0 = {Y=0, word1=0 (size 0, link 0), attr=0, X=0}. In a zero-active frame nothing overwrites it → slot 0 stays blank.
- **Y value (Q5.2):** raw SAT **Y=0** = 128px above the top visible line → fully offscreen/invisible (the emit path's +0x80 bias is not applied to a cleared slot).
- **link (Q5.3):** **0** guaranteed (cleared word1=0 → link 0 → immediate terminator).
- **DMA length (Q5.4):** upload **exactly one** entry → `dma_words = 4` (via `max(active_count,1)×4`). One blank invisible self-terminating entry.
- **zero-length hazard (Q5.5):** YES — a VDP DMA length of 0 transfers **0x10000 words** (catastrophic). The `max(,1)` clamp prevents ever writing a 0 length.
- **prior slot-0 sprite disappears (Q5.6):** uploading the fresh cleared slot 0 (Y=0, link=0) overwrites the previous frame's slot-0 sprite → it vanishes; and the chain terminates at the invisible slot 0, so prior slots 1..K (not re-uploaded) are unreachable → whole prior sprite set disappears.

**classification: SAFE** with the min-1-entry rule. (Transfer one blank entry; do not use a separate mechanism.)

---

## == Q6 EXPECTED BENEFIT ==

| active | old words | new words | reduction |
|---:|---:|---:|---:|
| 19 | 320 | 76 | 76.3% |
| 23 | 320 | 92 | 71.3% |
| 30 | 320 | 120 | 62.5% |
| 32 | 320 | 128 | 60.0% |
| 80 | 320 | 320 | 0% |

- **band implication:** the SAT DMA runs inside the display-off window, so this reduction is *directly* on the band's critical path. But in absolute terms 320 words ≈ ~640 DMA cycles ≈ ~1.3 scanlines; cutting to 92 words ≈ ~184 cycles ≈ ~0.4 scanlines → **~0.5–1 scanline saved**. This is a real, direct reduction but **modest** — the SAT DMA is a small fraction of the display-off window, which is still dominated by the (candidate-reduced) scan/link CPU that Build 0136 left inside display-off. **Honest expectation:** likely a small visible improvement; the larger band reduction still needs the deferred **DISPLAY_OFF split** (moving WRAM scan/link out of display-off). This change stacks cleanly with that later split.

---

## == Q7 RISKS / TESTS ==

- **stale tail sprites after count decreases:** detect — 32→23 shrink test, inspect VRAM SAT + on-screen; evidence — no ghost sprites at former slots; fallback — Option B (upload active_count+1 blank).
- **incorrect final link:** detect — assert last active slot (slot active_count−1) SAT word1 link bits == 0 each frame; evidence — link dump; fallback — STOP (link-builder fix, out of scope).
- **zero-active frame:** detect — force/observe a 0-emit frame; evidence — DMA length = 4 (never 0), screen clears; fallback — hardcode min 1.
- **active_count sampled too early:** detect — confirm sat_dma reads active_count after link_chain_build; evidence — order unchanged; fallback — recompute in sat_dma.
- **active_count > 80:** detect — defensive clamp; evidence — length ≤ 320; fallback — clamp (already in design).
- **DMA length register error:** detect — compare low/high bytes for 23/32/80 active; evidence — 0x5C/00, 0x80/00, 0x40/01; fallback — revert to fixed 320.
- **source/destination change:** detect — diff regs 0x15/16/17 + dest command vs Build 0136; evidence — identical; fallback — revert.
- **SAT order change:** detect — source_id + emitted order identical to 0136; evidence — counters/dump; fallback — revert.
- **title score / story sprite regression:** detect — title (codes 0x2A–0x49) + story anchors screenshot vs 0136; evidence — same sprites; fallback — revert.
- **coin/start clear transition; ROUND/start transition:** detect — anchor screenshots across the count-shrink transitions (32→23, active→0→active); evidence — no ghosts, clean clears; fallback — Option B.
- **residency-cache regression:** detect — `sprite_tile_resident_code` writes still 0 steady; evidence — cache tap; fallback — revert (tile DMA untouched anyway).
- **PC080SN regression:** detect — plane viewers; evidence — unchanged; fallback — revert (PC080SN untouched).

---

## == Q8 RECOMMENDATION ==

- **selected option:** **Option A** — DMA exactly `active_count` entries, minimum one blank entry.
- **why not B/C/D:** B's extra terminator entry is unnecessary (the last active entry already terminates with link=0, Q4) and would upload a stale/blank slot beyond the chain; C (keep full 320) forgoes a proven-safe 60–76% reduction; D (need evidence) is unnecessary — safety is statically proven (Q1/Q4/Q5). Keep Option B in reserve as the fallback if any last-active-link≠0 case is ever observed.
- **exact routine shape (`.Lvcs_sat_dma`, length section only):**
  ```
  .Lvcs_sat_dma:
      movea.l #VDP_CTRL, %a3
      ; --- variable length: dma_words = max(active_count,1)*4, clamp 80 ---
      move.w  staged_sprite_active_count, %d0
      bne.s   .Lsat_have_count
      moveq   #1, %d0
  .Lsat_have_count:
      cmpi.w  #80, %d0
      bls.s   .Lsat_count_ok
      move.w  #80, %d0
  .Lsat_count_ok:
      lsl.w   #2, %d0                 ; words
      move.w  %d0, %d1
      andi.w  #0x00FF, %d1
      ori.w   #0x9300, %d1
      move.w  %d1, (%a3)              ; length low
      move.w  %d0, %d1
      lsr.w   #8, %d1
      andi.w  #0x00FF, %d1
      ori.w   #0x9400, %d1
      move.w  %d1, (%a3)              ; length high
      ; --- source / dest / trigger: UNCHANGED from Build 0136 ---
      move.l  #staged_sprite_sat, %d0
      lsr.l   #1, %d0
      ... (regs 0x95/0x96/0x97 as today) ...
      move.l  #0x0000F800, %d0
      ... (dest command ori.l #0x40000080 as today) ...
      move.l  %d1, (%a3)             ; trigger
      rts
  ```
- **why safe:** contiguous packing (Q1.5), last-active terminator link=0 (Q1.7/Q4), unreachable tail (Q1.8), zero-active min-1 guard (Q5); source/dest/trigger and all other stages byte-unchanged.

---

## == Q9 CODY PROMPT ==

**copy-ready prompt:**

---
**Cody — Build 0137 Active-Count SAT DMA (production, narrow)**

**Type:** One narrow production build. No temporary diagnostic in the production ROM.
**Baseline:** Build 0136, SHA256 `23dde0a0516378267f125cde34e0cd6328a21c559bc556d2b82f034d02916bd4`.
**Design:** `docs/design/Andy_build0136_active_count_sat_dma_design.md` (Q8).

**Files allowed:** `apps/rastan-direct/src/pc090oj_hooks.s` only, and only the **length section** of `.Lvcs_sat_dma`.

**Change:** replace the two fixed DMA-length register writes (`move.w #0x9340,(%a3)` / `move.w #0x9401,(%a3)`) with the variable-length sequence from the design: `dma_words = max(staged_sprite_active_count, 1) × 4`, defensively clamped to 80 entries (≤320 words), written to regs 0x13 (low) and 0x14 (high). **Do not** change the DMA source (regs 0x15/0x16/0x17 = `staged_sprite_sat`), destination (`0xF800`), dest command, or the trigger `move.l`. **Do not** touch the candidate mask, mirror scan, link-chain builder, tile DMA, residency cache, DISPLAY_ON/OFF ordering, the DISPLAY_OFF split (deferred), or PC080SN.

**Precondition to verify (STOP if false):** valid SAT slots are contiguous `0..active_count−1` (i.e., `active_count == emitted_count` and equals highest-valid-slot+1), and the last active slot's SAT word1 link bits == 0 every frame.

**Build/gate:** `opcode_replace` count `133` unchanged; `total_genesis_bytes_covered` may grow by the added length math (update the two canonical tools only if the gate stops on the new value); boot guard + canonical gate PASS; rolling==numbered.

**Runtime comparison (vs Build 0136):** emitted/drawable/dropped/active counts, source_id order, SAT link chain, candidate counts, and residency-cache steady writes (0) **identical**. Verify DMA length low/high bytes for representative frames (e.g. 23→0x5C/0x00, 32→0x80/0x00, 80→0x40/0x01).

**Transition tests (mandatory):**
- **32→23 shrink:** no ghost/stale sprites at former slots 23..31; on-screen sprite set matches the 23 active.
- **active→0→active** (if reachable): zero-active frame issues length 4 (never 0), screen clears of sprites, then repopulates correctly.
- title (score codes 0x2A–0x49), story/black-cover, coin/start clear, ROUND/start — screenshot compare vs Build 0136 (no regressions, clean clears).

**Evidence:** **BlastEm** visual contact sheet (not only MAME) across the above anchors + transitions; DMA-length verification; count/link/source_id parity dump; residency-cache proof.

**STOP conditions:** any stale/ghost sprite after a count decrease; any SAT length/order/source_id/link mismatch; last-active-link ≠ 0 in any frame; zero-length DMA ever computed; candidate mask or any other stage perturbed; invariant gate fails unexpectedly.

**OPEN-001 / OPEN-024 impact:** OPEN-001 — reduces the SAT-DMA portion of the display-off band (modest, direct; not closed); OPEN-024 — sprite semantics/mirror/cache unchanged; neither closed.

---

## Open / Closed Issues Impact

- **Open issues touched:** OPEN-001 (SAT-DMA share of the display-off band — reduced; not closed), OPEN-024 (sprite pipeline — SAT length only, semantics intact; not closed).
- **Closed issues touched:** NONE.
- **New issues opened:** NONE (recommend a post-0137 KNOWN_FINDINGS entry: SAT DMA length may follow `active_count×4` because emitted sprites pack contiguously and the last active slot terminates the chain with link=0).
- **Issues closed:** NONE.
- **Issues intentionally deferred:** DISPLAY_OFF split (the larger band lever); candidate-mask clear-on-code-zero tuning; SAT double-buffering; any sub-entry (partial-SAT) optimization.

AGENTS_LOG updated: YES
STOP status: NO — active-count SAT DMA is statically proven safe (contiguous packing + last-active link=0 terminator + min-1 zero guard); Option A recommended as one narrow Build 0137 change; delegated to Cody.
