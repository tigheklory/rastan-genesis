# Andy — PC090OJ Candidate Bitset + DISPLAY_OFF Split Design (Design Only)

**Author:** Andy
**Date:** 2026-07-03
**Baseline:** Build 0135, `dist/rastan-direct/rastan_direct_video_test_build_0135.bin`, SHA256 `8e00be424f9afefe79d199640096bf99de7b53c4ba49e83ad32b2b491990844e`.
**Priors:** Cody sprite-lifecycle/deactivation audit; Cody Build 0135 DISPLAY_OFF budget + scan-depth analysis; Cody Build 0135 DISPLAY_ON reorder; Cody Build 0133 HV diagnostic; Cody Build 0132 residency cache; Andy Build 0132 static review; Andy Build 0134 timing fix.
**Scope:** DESIGN ONLY. No implementation/edit/build/diagnostic-ROM. All addresses Genesis-native (`runtime_genesis_pc`); no arcade↔genesis arithmetic. Labels **[OBS]** verified from Build 0135 source; **[INT]** interpretation.

> **BOTTOM LINE:** The dominant remaining DISPLAY_OFF cost is the **WRAM-only** sprite prep (`.Lvcs_mirror_scan` 256-entry decode + `.Lvcs_link_chain_build`) that currently runs *inside* the display-off window — it touches **zero VDP**. The narrowest, mechanically-provable, correctness-neutral fix is the **DISPLAY_OFF split (Sequence 1, Build 0136)**: run sprite prep *before* DISPLAY_OFF (display stays enabled, showing the prior frame during any overrun), leaving only the two VRAM DMAs (`.Lvcs_tile_dma` gated-to-0 by the residency cache + `.Lvcs_sat_dma` 320 words) inside display-off. This shrinks the black band to the DMA window without changing sprite semantics, ordering, counts, or the mirror. The **candidate bitset (Build 0137)** is a good follow-up that reduces scan CPU, but it is correctness-sensitive (false-negative risk) and its benefit is secondary once the scan is out of the display-off window — do it second, validated against a full-scan baseline off the critical path. **Recommend Sequence 1.**

---

## == PHASE 0 ==

- **Relevant priors:** Build 0132 residency cache (sprite tile DMA suppressed to 0 steady); Build 0135 DISPLAY_ON reorder (after sprite commit, +~1 line); Cody budget analysis (sprite_commit_total dominant, non-sprite stages 1–2 lines); Cody lifecycle audit (write paths centralized, set-broad/clear-cautious, candidate-only first, no dirty bitset); Andy Build 0130 (late-DISPLAY_ON band).
- **High-rediscovery hazards:** (1) **false negatives are fatal** — a drawable record skipped by the candidate set = a missing sprite; (2) SAT slot = emission order, so candidate iteration MUST stay ascending record order to preserve priority/source_id; (3) Genesis 80-SAT output cap ≠ PC090OJ 256-record input — never scan only 0..79; (4) raw zero/nonzero ≠ visibility (use the full decode predicates); (5) KF-021 (staged SAT ≠ truth) unaffected.
- **Task classification:** Narrow sprite-cost + DISPLAY_OFF-window DESIGN for OPEN-001, building on OPEN-024 cache.
- **Contradiction detected:** NO.
- **Build 0135 baseline:** verified `8e00be42…990844e`.
- **Cody scan-depth result:** `vdp_commit_sprites` scans all 256 PC090OJ records every frame; emits only 19..32 SAT sprites; dropped=0; tile DMA suppressed; remaining steady cost = CPU scan/link/build + fixed SAT DMA.
- **Cody lifecycle result:** all known PC090OJ write paths derive a record index; deactivation via code-zero / Y-sentinel-offscreen / whole/block clears / overwrite-reuse; activation can be partial → tile/code-only set is unsafe; set broadly, clear cautiously; candidate-only first; defer dirty bitset.
- **Genesis 80-SAT output cap:** preserved (emit cap at pc090oj_hooks.s:1038-1042 unchanged).
- **candidate-bitset framing:** 256-bit derived helper state; mirror stays canonical; false positives allowed, false negatives forbidden.
- **DISPLAY_OFF split framing:** relocate WRAM-only prep out of the display-off window; VRAM DMAs stay inside.
- **address_map.json loaded:** YES. **arithmetic offset used as proof:** NO.

---

## == Q1 vdp_commit_sprites PARTITION ==

`vdp_commit_sprites` = `.Lvcs_mirror_scan → .Lvcs_link_chain_build → .Lvcs_tile_dma → .Lvcs_sat_dma → .Lvcs_clear_dirty` [OBS pc090oj_hooks.s].

- **WRAM-only steps:**
  - **generated descriptor/SAT clear** (`.Lvcs_clear_generated_sprite_state`, inside scan) — zeroes staged_sprite_sat/descriptors/dirty/active_count. WRAM.
  - **full 256-entry mirror scan + descriptor generation** (`.Lvcs_mirror_scan` → `.Lpc090oj_emit_slot`, `pc090oj_scan_active==1` so **no** mirror bridge) — reads `pc090oj_object_ram`, writes staged descriptors/SAT. WRAM only (verified: no VDP_CTRL/VDP_DATA in the loop).
  - **link-chain build** (`.Lvcs_link_chain_build`, 1081-1128) — reads descriptors, writes staged_sprite_sat link words + active_count. WRAM only.
  - **dirty cleanup** (`.Lvcs_clear_dirty`, 1260+) — clears staged_sprite_dirty + touched flags. WRAM only.
- **VDP-touching steps:**
  - **sprite tile DMA** (`.Lvcs_tile_dma`) — 68k→VRAM DMA of sprite patterns (dest 0x8000+), **gated by valid+changed**; residency cache makes this ~0 steady. Also writes `sprite_tile_resident_code` (WRAM) after each DMA.
  - **SAT commit** (`.Lvcs_sat_dma`, 1219-1258) — 68k→VRAM DMA, source staged_sprite_sat, dest VRAM 0xF800, **320 words, unconditional every frame**.
- **display-off-required steps (Q1.3):** the two VRAM DMAs only — tile DMA (sprite patterns 0x8000) and SAT DMA (0xF800). Writing these VRAM structures while they are being scanned corrupts the visible frame, so they need display-off (or at least VBlank with display off to avoid mid-scan artifacts). The WRAM steps require neither.
- **VBlank-only steps (Q1.4):** the VRAM DMAs need VBlank/display-off; the WRAM steps (scan/link/clear) need neither VBlank nor display-off (pure WRAM CPU).
- **could run before DISPLAY_OFF (Q1.5):** all WRAM-only steps — scan, link, (clear-generated is part of scan). They read `pc090oj_object_ram` which no `_vblank_service` stage mutates (see Q4.4).
- **could run after DISPLAY_ON (Q1.6):** `.Lvcs_clear_dirty` (WRAM cleanup) could, but it is cheap and kept with the commit.
- **SAT commit method (Q1.7):** **real VDP DMA**, statically provable — DMA length regs `0x9340/0x9401` (=0x140=320 words), source-address regs `0x95/0x96/0x97`, dest command `ori.l #0x40000080` (VRAM-write + DMA-enable bit) with a single `move.l %d1,(%a3)` trigger [OBS 1219-1258]. NOT a CPU loop. 68k is bus-stalled for the transfer, so the following instruction runs after completion.
- **unknowns (Q1.8):** NONE for the SAT method (statically proven DMA) or the WRAM/VDP split. The *relative cost* attribution (scan CPU vs SAT DMA) is a runtime question, already answered by Cody's budget analysis (sprite_commit_total dominant, CPU + fixed SAT). No further partition audit required.

---

## == Q2 CANDIDATE BITSET DESIGN == (Build 0137, deferred)

- **WRAM layout:** `pc090oj_candidate_bitset : .space 32` (256 bits, bit *r* = record *r* is a candidate), in `.bss` adjacent to `pc090oj_object_ram`. Derived helper state only; the mirror stays canonical.
- **boot init:** clear all 32 bytes to 0 in `_bootstrap_clear_staging` (all records non-candidate at boot; every subsequent mirror write sets its bit).
- **set hooks (set broadly — no false negatives):** set the record's bit on **every** mirror write, in the centralized write helpers:
  - `.Lpc090oj_mirror_write_word_a1_d0` / `.Lpc090oj_mirror_write_byte_a1_d0` (0x3B930/0x3B802 paths) — record = `((a1 & 0xFFFFFF) − 0xD00000) >> 3`.
  - `.Lhook_3ad44_pc090oj_long_fill_loop` (3AD44 long-fill) — record = `d2 >> 3` per advancing offset.
  - `.Lpc090oj_emit_slot` mirror-bridge (`pc090oj_scan_active==0`, all legacy per-site hooks) — record = `d0` (slot).
  These three points cover all known write paths (Cody audit) → every written record becomes a candidate → no false negatives.
- **clear hooks (clear cautiously):** clear a candidate bit **only during the scan, and only when the fully-decoded record is code-zero** (`word2 & 0x1FFF == 0`, the `.Lvcs_mirror_code_zero_skip` predicate — the canonical "empty record"). **Do NOT clear on blank / unmapped / offscreen** — those have nonzero codes and can become drawable next frame without a rewrite (e.g., an offscreen sprite that scrolls on-screen), so clearing them would be a false negative. **Do NOT clear from a partial byte/word write.** Rationale: a code-zero record is never drawable; if a producer later rewrites it nonzero, the set-hook re-sets the bit. This yields sustained benefit (producer code-zero clears drop their bits at next scan) with zero false-negative risk.
- **range/global clear behavior:** whole/block clears (3AD44 fill, 56440 zero-fill, 3B926 clear) write code-zero through the normal write path → set-hook sets the bit → the scan then decodes code-zero → clears it. No special range-clear logic in the first design (proven range clears are a deferred optimization).
- **record-index derivation:** `record = mirror_byte_offset >> 3` for address-based writes; `record = d0` for the emit_slot bridge. Bit address = `candidate_bitset + (record >> 3)`, bit = `record & 7`.
- **false-positive policy:** allowed — a candidate that decodes to non-drawable (blank/unmapped/offscreen) is simply skipped by the scan, exactly as today; it stays a candidate (kept for next frame). Cost = decoding an extra record.
- **false-negative prevention:** every mirror write sets the bit (set-broad); clears happen only on code-zero (provably non-drawable). A full-scan-baseline diagnostic (Q3.5) must prove the candidate-emitted SAT set is byte-identical to the full-256 scan before Build 0137 ships.

---

## == Q3 MIRROR SCAN ITERATION == (Build 0137)

- **candidate iteration:** replace the `d6 = 0..255` unconditional loop with iteration over set candidate bits in **ascending record order** (walk the 32 bytes; for each, test bits in record order; skip clear bits). For each set bit: `a0 = pc090oj_object_ram + record*8`; decode the original 8-byte record; apply the **existing** code-zero / blank / unmapped / offscreen / drawable predicates unchanged; emit via the existing `.Lpc090oj_emit_slot` path; optionally clear the bit on code-zero.
- **priority/order (Q3.1):** PRESERVED — ascending record order is identical to the current 0..255 order; candidates are a superset of drawables, so the emitted sequence (and thus SAT slot assignment) is identical to the full scan.
- **source_id (Q3.2):** PRESERVED — `source_id = record index` (the set bit's index), same value the full scan would use.
- **counters (Q3.3):** emitted/dropped/drawable/blank/unmapped/offscreen/code-zero counters increment on the same predicates → identical values (drawable set unchanged). Add `pc090oj_candidate_count` (candidates iterated) for evidence.
- **decoded_count interpretation (Q3.4):** it becomes **"records the scan actually decoded this frame" = number of candidate bits iterated (≤256)**, no longer a fixed 256. Runtime evidence must read it as candidate-iteration count; the drop from 256 to ~(19..32 + false positives) is the measured win.
- **dropped semantics:** unchanged — 80-cap and dropped counting are on the emit side; since drawables are identical, dropped is identical (0 in sampled frames).
- **proof mode (Q3.5):** **YES, required.** A **separate temporary** full-scan-baseline diagnostic build must run BOTH the candidate scan and a full-256 scan and assert the two emitted SAT sets (slots, codes, Y/X, source_id, order, emitted/dropped) are byte-identical across no-input/story/coin/ROUND. This proves no false negatives. It is temporary + reverted byte-identical (Build 0133 discipline); production Build 0137 has no baseline.
- **false-positive measurement (Q3.6):** `false_positives = pc090oj_candidate_count − pc090oj_drawable_count` (candidates that decoded non-drawable). Report per anchor; a low candidate_count with identical emitted set = success.

---

## == Q4 DISPLAY_OFF SPLIT == (Build 0136 — recommended first)

- **safe before DISPLAY_OFF:** `vdp_prepare_sprites` = `.Lvcs_mirror_scan` + `.Lvcs_link_chain_build` (WRAM-only). Runs right after `rastan_direct_update_inputs`, before the DISPLAY_OFF write.
- **remains inside DISPLAY_OFF:** `vdp_commit_sprites_vram` = `.Lvcs_tile_dma` + `.Lvcs_sat_dma` + `.Lvcs_clear_dirty`, after the tile/BG/FG VRAM commits, before DISPLAY_ON (preserving Build 0135's DISPLAY_ON-after-sprite-commit order).
- **double-buffer needed (Q4.2):** NO. The existing `staged_sprite_sat` + `staged_sprite_descriptor_table` are already the buffer between prep (producer) and DMA (consumer); nothing mutates them between the split points.
- **new staging buffers (Q4.3):** NO.
- **object-RAM mutation risk (Q4.4):** NONE within `_vblank_service`. Between `vdp_prepare_sprites` and the sprite VRAM commit, the only stages are `vdp_commit_tiles_if_dirty` / `_bg_strips_` / `_fg_strips_`, which read `staged_tile_words`/`staged_bg_buffer`/`staged_fg_buffer` and write VRAM — none touches `pc090oj_object_ram` or `staged_sprite_*`. Arcade producers run in the **main loop**, not inside `_vblank_service`, so the mirror is stable from prep to DMA. [OBS vdp_comm.s:158-184, commit routines]
- **tile/BG/FG depend on sprite prep later? (Q4.5):** NO — independent staging.
- **sprite prep need to remain inside VBlank? (Q4.6):** NO — it is pure WRAM CPU (no VDP access); running it at VBlank entry (before DISPLAY_OFF) is fine and preserves the "snapshot mirror at frame boundary" semantics. Display is ON during prep (from the prior frame's DISPLAY_ON); if prep overruns into active display, the prior frame's VRAM is shown (not black), so the black band shrinks to the DMA window.
- **Grade-1 feasibility (Q4.7):** YES. Implementation = split `vdp_commit_sprites` into two `.global` wrappers (`vdp_prepare_sprites` = scan+link; `vdp_commit_sprites_vram` = tile+sat+clear) in pc090oj_hooks.s, and call them at the two points in `_vblank_service`. No logic change to any sub-routine. Order preserved (scan→link before tile→sat; link must precede sat_dma since it writes the SAT link words the DMA uploads).
- **fallback / partition audit (Q4.8):** none needed — the partition is statically proven (Q1). Fallback if a regression appears: revert to the single `vdp_commit_sprites` call.

---

## == Q5 NEXT PRODUCTION SEQUENCE ==

- **selected sequence:** **Sequence 1** — Build 0136 = DISPLAY_OFF split only; Build 0137 = candidate bitset.
- **why:** the split is the narrowest change that *directly* attacks OPEN-001's band — it removes the dominant WRAM scan/link from the display-off window (display stays ON during the scan, shrinking the black band to the DMA-only window), is mechanically proven safe (no mirror mutation between prep and DMA), and changes **no** sprite semantics/order/counts (zero false-negative risk). The candidate bitset is correctness-sensitive (false-negative risk, lifecycle set/clear rules) and its main benefit (scan CPU) is secondary once the scan is off the display-off critical path; sequencing it second lets Cody validate it against a full-scan baseline **without** it sitting on the band's critical path. Sequence 3 (both together) couples a safe change with a risky one and muddies regression attribution. Sequence 4 (more audit) is unnecessary — Q1 statically proves the partition and the SAT-DMA method.
- **confidence:** HIGH that the split is safe and correctness-neutral; HIGH that it materially shrinks the band (Cody: non-sprite stages 1–2 lines, tile DMA 0 steady, so residual display-off ≈ SAT DMA ≈ 1–2 lines); MEDIUM that it fully removes the band (if the 320-word SAT DMA + any dirty BG/FG strips still overrun in worst frames, a follow-up SAT/strip step or the candidate bitset closes the gap).

---

## == Q6 RISKS / TESTS / FALLBACKS == (Sequence 1, Build 0136 split)

- **missed candidate set / unsafe candidate clear / candidate false positive:** N/A for Build 0136 (no bitset yet) — these are Build 0137 risks; for 0137, detection = full-scan-baseline diff (emitted sets must be byte-identical), fallback = revert to full 256 scan.
- **stale descriptors:** test — emitted/drawable/dropped counts and a descriptor dump identical to Build 0135 across anchors; fallback = revert split.
- **sprite ordering mismatch / source_id mismatch:** test — the scan is byte-for-byte the same code, only relocated; verify source_id and SAT link chain identical to 0135; fallback = revert.
- **dropped sprite count changes:** test — dropped stays 0 (sampled); fallback = revert.
- **title score regression:** test — title score sprites present (codes 0x2A–0x49, ~22/27) screenshot; fallback = revert.
- **story / coin-start / ROUND-start regression:** test — contact-sheet compare vs Build 0135 for each anchor (no-input, story/black-cover, coin-accept, ROUND); fallback = revert.
- **cache regression:** test — `sprite_tile_resident_code` writes still 0 steady after warm-up; fallback = revert.
- **SAT/link regression:** test — link chain valid, active_count identical; fallback = revert.
- **DISPLAY_OFF band remains:** test — Exodus/HV: display-off window ≈ DMA window; band reduced vs 0135; if unchanged, the band is SAT-DMA/strip-bound → next step = SAT/strip work (deferred), not masking.
- **SAT commit still too expensive:** test — measure residual display-off window; if SAT DMA dominates, deferred SAT-DMA-reduction design (out of scope here).
- **gameplay/endround not covered:** test — include an endround/gameplay anchor in the contact sheet to confirm the split holds across scenes (mirror-stable-in-VBlank argument is scene-independent).

---

## == Q7 CODY PROMPT ==

**copy-ready prompt:**

---
**Cody — Build 0136 PC090OJ DISPLAY_OFF Split (production, narrow)**

**Type:** One narrow production build. No temporary diagnostic in the production ROM. No candidate bitset in this build.
**Baseline:** Build 0135, SHA256 `8e00be424f9afefe79d199640096bf99de7b53c4ba49e83ad32b2b491990844e`.
**Design:** `docs/design/Andy_pc090oj_candidate_bitset_and_displayoff_split_design.md` (Q4).

**Files allowed:** `apps/rastan-direct/src/pc090oj_hooks.s` and `apps/rastan-direct/src/vdp_comm.s` only. No `scene_load.s`, `tilemap_hooks.s`, PC080SN artifact, residency-cache, mirror-decode, SAT-layout, or DISPLAY_ON-order change.

**Exact routine boundaries:** in `pc090oj_hooks.s`, split `vdp_commit_sprites` into two `.global` entry points **without changing any sub-routine logic**:
- `vdp_prepare_sprites:` → `bsr .Lvcs_mirror_scan` ; `bsr .Lvcs_link_chain_build` ; rts (movem-preserve as today).
- `vdp_commit_sprites_vram:` → `bsr .Lvcs_tile_dma` ; `bsr .Lvcs_sat_dma` ; `bsr .Lvcs_clear_dirty` ; rts.
- Keep the sub-routines and `.Lpc090oj_emit_slot` byte-for-byte unchanged.

In `vdp_comm.s`, `_vblank_service` becomes:
```
    bsr rastan_direct_update_inputs
    bsr vdp_prepare_sprites          ; WRAM sprite prep, display still ON
    <DISPLAY_OFF>
    bsr vdp_commit_tiles_if_dirty
    bsr vdp_commit_bg_strips_if_dirty
    bsr vdp_commit_fg_strips_if_dirty
    bsr vdp_commit_sprites_vram      ; VRAM tile+SAT DMA under display-off
    <DISPLAY_ON>                     ; keep Build 0135 position (after sprite VRAM commit)
    <palette (if dirty)>
    bsr vdp_commit_scroll
    <handoff>
```
Do not otherwise reorder; do not duplicate DISPLAY_ON/OFF.

**Build/gate:** `opcode_replace` patched-site count `133` unchanged; `total_genesis_bytes_covered` may grow by the two small wrappers (expected, update the two canonical tools only if the invariant gate stops on the new value); confirm boot guard + canonical gate PASS; rolling==numbered (`cmp -s`).

**Runtime comparison (vs Build 0135):** `emitted_count`, `drawable_count`, `dropped_count`, `code_zero/blank/unmapped/offscreen` counters, SAT link chain, and `source_id` values **identical**. Residency-cache writes still 0 steady after warm-up.

**Anchor checks (contact sheet, no-input + story/black-cover + coin-accept + ROUND-start + one endround/gameplay):** title score sprites present (codes 0x2A–0x49); composite band reduced vs Build 0135; no PC080SN plane regression; no sprite ordering/priority change.

**Full-scan baseline comparison:** N/A for Build 0136 (scan code unchanged; only relocated). Reserve the full-scan baseline diff for the later candidate-bitset build (Build 0137).

**STOP conditions:** any emitted/drawable/dropped/source_id/link mismatch vs 0135; band unchanged (re-diagnose SAT-DMA/strip cost, do not mask); any producer/commit found mutating `pc090oj_object_ram` or `staged_sprite_*` between prep and DMA; invariant gate fails unexpectedly; regression in any anchor.

**OPEN-001 / OPEN-024 impact:** OPEN-001 — direct band-reduction attempt (not closed until visual proof); OPEN-024 — sprite pipeline unchanged in semantics (mirror canonical, cache intact); neither closed.

---

## Open / Closed Issues Impact

- **Open issues touched:** OPEN-001 (DISPLAY_OFF band — split reduces the window; not closed), OPEN-024 (sprite pipeline — partition documented, cache/mirror intact; not closed).
- **Closed issues touched:** NONE.
- **New issues opened:** NONE (recommend a post-0136 KNOWN_FINDINGS entry: the sprite display-off window need only cover the two VRAM DMAs; WRAM scan/link/build belong before DISPLAY_OFF).
- **Issues closed:** NONE.
- **Issues intentionally deferred:** candidate bitset (Build 0137, Q2/Q3) + its full-scan baseline; SAT-DMA cost reduction if the residual band persists; dirty bitset; range/global candidate-clear optimization; `.Lpc090oj_emit_slot` producer/render split.

AGENTS_LOG updated: YES
STOP status: NO — partition statically proven; DISPLAY_OFF split is safe and narrow (Sequence 1, Build 0136); candidate bitset fully designed for Build 0137; delegated to Cody as two sequenced builds.
