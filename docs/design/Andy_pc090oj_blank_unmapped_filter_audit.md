# Andy — Independent Audit: PC090OJ Blank-Code Filter & Unmapped-Code Guard (Analysis Only)

**Author:** Andy
**Date:** 2026-07-01
**Baseline:** rastan-direct Build 0123. rastan-direct.
**Scope:** ANALYSIS / AUDIT only. No source/spec/tool/Makefile/ROM/build/bookmark/diagnostic changes; no build. MAME used only as hardware reference (in-repo). Code correlation via `address_map.json` (no arithmetic). Labels: **[OBS]** independently verified this task; **[CODY]** Cody's claim; **[MAME]** in-repo reference; **[INT]** interpretation. Verdict at the end: single GO / NO-GO.

> **BOTTOM LINE:** Cody's blank-code filter and unmapped-code guard are **correct, necessary, and safe** — I independently re-derived the load-bearing facts (22 blank codes, 4096-cell ROM, 0x1FFF/0xFFF masks, SAT clear-before-scan) and they hold. **GO, with constraints.** The one thing the filter does **not** do is fix the observed black overdraw (Cody's own evidence attributes that to stale/true-VDP-SAT divergence, KF-021, not blank codes) — so a **true VDP SAT (0xF800) capture is mandatory** in the same build's validation, and the prompt must not conflate the filter with a black-overdraw fix.

---

## == PHASE 0 ==

**Relevant priors:**
- **KF-021 — applies (HIGH):** staged SAT, true VDP SAT, and the linked SAT chain can diverge and create false visual attribution. Central to the stale-SAT / black-overdraw question.
- **KF-032 — applies:** raw copied PC090OJ writes must route to the staging/mirror, not Genesis VDP aliases (the mirror architecture is the correct answer).
- **KF-036 — applies (context):** the sprite hooks read arcade work-RAM; mapped-base discipline governs the legacy bridge.
- **KF-010 / KF-011 / KF-026 — context** (plane mapping; arcade owns VBlank lifecycle; PC090OJ write surface not fully statically enumerable).
- **Andy PC090OJ architecture audit** (`docs/design/Andy_pc090oj_object_ram_to_genesis_sat_architecture.md`) — this Build 0123 phase-1 implements the object-RAM-mirror direction that audit recommended.

**High-rediscovery hazards:** **KF-021 — HIGH**, because the black overdraw is currently attributed by Cody to WRAM-vs-true-VDP-SAT divergence, and only WRAM SAT was captured; misreading WRAM-SAT correctness as final-composite correctness is exactly the KF-021 trap.

**Task classification:** ANALYSIS / DESIGN AUDIT / EXTENDING OPEN-024.

**Contradiction detected: NO.** Cody's phase-1 implementation, the black-overdraw evidence, and the filter design are internally consistent, and consistent with the architecture and the MAME reference. (The black-overdraw evidence explicitly does **not** re-blame transparency and does **not** claim the filter fixes it — no contradiction.) No contradiction affects implementation safety → no forced NO-GO on that basis.

**Open/Closed Issues pre-check:** OPEN-024 primary (sprite subsystem); OPEN-001 context (title/attract completeness); OPEN-006 context (sprite palette/colbank — now direct-captured); OPEN-023 Window contrast only (refuted, sprite is the live layer); OPEN-015 not touched (no crash-numeric reliance).

---

## == ARCHITECTURAL RULE AUDIT (Part A) ==

**Rule under audit:** mirror preserves arcade truth (blank/stale/offscreen/unmapped entries stay in the mirror); filtering only at Genesis SAT emission/compaction; SAT holds only entries selected for actual Genesis rendering.

- **mirror rule correct:** **YES.** [INT] It matches the object-RAM-mirror architecture: `pc090oj_object_ram` is the arcade truth (256 entries); decoding/filtering is a Genesis hardware-service step. Consistent with ARCHITECTURE.md (arcade code is the program; Genesis helpers translate, don't own game state) and with Cody's design doc §"Mirror every arcade PC090OJ active object-RAM entry, including blank/filtered."
- **filter-at-emission correct:** **YES.** Skipping blank/unmapped/offscreen/overflow during compaction into the 80-entry SAT is a translation step, not gameplay logic. The mirror still holds every entry.
- **risk of mirror mutation:** **LOW, already guarded.** [OBS] Build 0123 sets `pc090oj_scan_active=1` during the scan (phase1 doc) so decoded/flipped output is **not** written back into `pc090oj_object_ram`. The blank/unmapped filter must read the mirror and only affect **whether a slot is emitted** — it must never clear/zero/rewrite a mirror entry. Residual risk exists only if a future edit adds a "clean up blank entries in the mirror" shortcut.
- **required Cody wording (to prevent mirror mutation):** the implementation prompt MUST state: *"The blank-code and unmapped-code filters operate ONLY at SAT emission in the mirror scan. They read `pc090oj_object_ram` and decide emit/skip. They MUST NOT write, clear, zero, normalize, or reorder any `pc090oj_object_ram` entry. The mirror remains a byte-faithful copy of arcade object RAM; `pc090oj_scan_active` stays set during the scan."*

---

## == BLANK-CODE INVENTORY AUDIT (Part B) ==

**Independently recomputed from `build/pc090oj_genesis.bin` (not trusting Cody's list):** [OBS]
- **asset size verified:** 524,288 bytes ÷ 128 = **4096 cells** — matches source `pc090oj.bin` (524,288) and **MAME `ROM_REGION(0x080000,"pc090oj")` = 4096 cells** (`rastan.cpp:517`). Converted range = codes 0x000..0xFFF. ✔
- **cell size verified:** 16×16×4bpp = 256 px × 4 bits = 1024 bits = **128 bytes/cell**. ✔
- **blank test correct:** "all 256 pixels index 0" ⇔ all 128 bytes zero (4bpp packed) → my scan finds **22 all-zero cells**, exactly matching Cody's 22; code 0 blank ✔; emitted codes 0x0001/0x0110/0x0080 **nonblank** ✔. Testing **pixel indices (pen 0)**, not palette black, is **correct** — a sprite whose pens all map to black is still a real sprite; only pen-0-everywhere is genuinely transparent. ✔
- **blank list confidence:** **HIGH** — independently reproduced (22 codes incl. 0x0, 0x2, 0x4, 0x45, 0xa8–0xab, 0xf3, 0x100, 0x178, 0x1d8, 0x4ff, 0x5b0, 0x5d6–0x5d9, 0x5db, 0x9fd, 0xaa3, 0xac2). Internally consistent.
- **table recommendation:** **GENERATE at build time; do NOT hardcode the 22-code list.** [INT] A hardcoded list silently drifts if the PC090OJ asset changes (new preconvert → different blank cells) — the exact KF-033/KF-036 lesson (generated LUTs, not literals). Recommended form: a **4096-bit blank bitset (512 bytes)**, one bit per code, generated from the **converted** `pc090oj_genesis.bin` in the same tool pass as the tile conversion, `incbin`'d, checked at runtime as `bit[code]`. (A 4096-byte table is acceptable but 8× larger for no benefit.) Safest low-risk choice: **build-time 512-byte bitset from the converted asset.**

---

## == SOURCE VS CONVERTED CONSISTENCY AUDIT (Part C) ==

- **conversion consistency:** **Sufficient for blank filtering.** [OBS] Cody reports 0 blank-flag mismatches and 0 recomposed-16×16 mismatches between source and converted; and critically, **blank (all-zero) is order-INVARIANT** — reordering zero bytes yields zero bytes, so an all-zero cell is all-zero in TL/BL/TR/BR order or any order. So the blank table is identical whether generated from source or converted. (I generated from converted; same 22.)
- **quadrant order risk (for blank detection): NIL.** The TL/BL/TR/BR reorder (`preconvert_pc090oj_tiles.py`, "matches `frontend_decode_pc090oj_cell()` exactly") only rearranges pixels *within* a cell; it cannot change which cells are all-zero, and the **code→cell index (cell N = code N) is preserved** across source/converted. So blank[code] is well-defined regardless of order.
- **runtime/table index risk:** **LOW.** The runtime tile DMA indexes by decoded code (masked, §D); the blank table indexes by decoded code (0..0xFFF). Both index the same 4096-cell converted asset by code. **Prevent any residual risk by generating the blank table from the same converted asset the runtime DMAs** (not the source), so table-index ≡ DMA-index by construction.
- **quadrant-order bug: NOT revealed** for blank detection (order-invariant). The *graphics* quadrant order is a separate concern already validated (source-vs-converted 16×16 pixels match exactly — black-overdraw evidence #5).
- **required proof:** Cody should state that the blank bitset is generated from `build/pc090oj_genesis.bin` (the DMA source) and indexed by the same code used for tile DMA, so table and runtime share one code indexing. (Given order-invariance, this is belt-and-suspenders, but it closes the audit.)

---

## == UNMAPPED HIGH-CODE GUARD AUDIT (Part D) ==

- **PC090OJ mask:** `code = word2 & 0x1fff` — **CORRECT** [MAME `pc090oj.cpp:191`]; the scan uses `andi.w #0x1FFF,%d3` [OBS].
- **converted range:** **really only 0x000..0xFFF** [OBS] — the asset AND the MAME ROM region are both 4096 cells (0x80000). Codes 0x1000..0x1FFF have **no ROM data**.
- **wrap risk:** the current tile DMA masks `#0x0FFF` (`pc090oj_hooks.s:1064`), so a decoded high code (0x1000..0x1FFF) would **wrap** to 0x000..0xFFF and render a **wrong (aliased) low graphic**. Real Rastan sprites cannot use high codes (4096-cell ROM); a high code in an entry is therefore **garbage/stale, not a real sprite**. **Wrapping renders a wrong graphic; skipping drops garbage — skipping is safer.**
- **skip high codes:** **YES — skip codes ≥ 0x1000 at emission** (do not wrap/alias). Because real sprites never use them, skipping drops nothing real and avoids rendering a wrong aliased graphic (a potential contributor to visual noise).
- **counter required:** **YES — mandatory.** Add a `pc090oj_unmapped_count` (or a distinct bucket in `dropped_count`). A nonzero high-code count is a **red flag** that either the assumption is wrong or stale/garbage entries are present — it must be observable, not silently wrapped or silently skipped.
- **high codes remain in mirror unchanged:** **YES** — the mirror is arcade truth; the guard skips only at emission.
- **arcade reason high codes alias low:** **Not established.** [INT] The ROM is 4096 cells, so *if* MAME's gfxdecode wrapped (modulo 4096) a high code would alias; but modern MAME does not reliably auto-modulo, and **Rastan emits no high codes** (Build 0123: 0 high-code entries in the frame). So aliasing is theoretical and unobserved.
- **aliasing proof required (before allowing wrap/alias):** (1) evidence the game emits codes ≥ 0x1000 on **real** (drawable, intended) sprites — not garbage; AND (2) confirmation that the arcade renders those as the aliased low graphic (verify MAME's out-of-range gfx behavior for this device/region). **Absent both, SKIP + COUNT (do not alias).** Since Build 0123 shows zero high codes, the counter is expected to stay 0.

---

## == STALE SAT SAFETY AUDIT (Part E) ==

- **WRAM clearing sufficient (if full DMA confirmed):** **YES, and the clear is VERIFIED in source.** [OBS] `.Lvcs_mirror_scan` first calls `.Lvcs_clear_generated_sprite_state`, which zeroes **all 80** `staged_sprite_sat` entries (`clr.w` over `80*8/2`) and **all 80** `staged_sprite_descriptor_table` records, plus `staged_sprite_dirty` and `staged_sprite_active_count`, *before* scanning the mirror. So stale generated entries cannot survive into the emit.
- **full SAT DMA verified:** **NOT independently verified this task** — `vdp_commit_sprites` calls `.Lvcs_sat_dma`; Cody claims a full 80-entry SAT DMA. **Cody must confirm** `.Lvcs_sat_dma` DMAs all 80 SAT entries (not just the emitted count) every commit; combined with the verified clear, that makes decreasing-count safe.
- **zero-emitted case:** **SAFE, by construction.** [OBS+INT] With the SAT pre-cleared to all-zero and 0 emitted, slot 0 = Y=0 (Genesis SAT Y=0 is 128 px above the visible top → **offscreen**), tile 0, size 0, link 0. The hardware sprite chain starts at slot 0 → draws nothing (offscreen) → link 0 terminates. `.Lvcs_link_chain_build`'s zero path (`d6=-1` → no terminator written) is safe precisely because the cleared SAT already has slot 0 offscreen/link-0.
- **decreasing-count case (4→0 or N→M):** **SAFE** given clear-before-scan + full-80 DMA (stale slots re-zeroed and DMA'd offscreen). Contingent on the full-80 DMA confirmation above.
- **unused slots hidden/unreachable:** **BOTH, effectively.** Emitted slots form the link chain [0..N−1] terminated at N−1 (`0x0500`); slots N..79 are **unlinked (unreachable)** AND **cleared to Y=0 (offscreen/hidden)**. On Genesis, unreachable-by-link is sufficient to not render; the additional clear (offscreen) is defense-in-depth. **Good** — do not weaken to unreachable-only.
- **true VDP SAT requirement:** **MANDATORY, not optional.** [INT] Cody's black-overdraw evidence names **stale/true-VDP-SAT divergence (KF-021 HIGH)** as the leading remaining hypothesis and captured only **WRAM** SAT, not true VDP SAT (`0xF800..0xFA7F`). WRAM-source correctness does **not** prove the post-DMA VDP SAT is correct. Capturing true VDP SAT is the decisive evidence for both the black overdraw and the DMA correctness — it must be in this build's validation.

---

## == IMPLEMENTATION READINESS (Part F) ==

**verdict: GO (with constraints).** The blank-code filter and unmapped-code guard are independently verified correct, are necessary for general SAT-compaction correctness (today only code 0 is skipped; 21 blank + all high codes are unhandled), and are safe (emission-only; mirror preserved; SAT clear-before-scan verified; zero/decreasing-count safe). Build 0123's captured frame has 0 nonzero-blank and 0 high-code entries, so the change is **purely preventive** for that frame — it will not regress the 4 emitted sprites.

**constraints (must be in Cody's implementation prompt):**
1. **Generated blank bitset, not hardcoded.** Build-time 512-byte (4096-bit) blank bitset generated from `build/pc090oj_genesis.bin`; `incbin`'d; runtime `bit[code]` test. No hardcoded 22-code list.
2. **Emission-only; never mutate the mirror.** Filters decide emit/skip in the mirror scan; they must not write/clear/reorder any `pc090oj_object_ram` entry. `pc090oj_scan_active` stays set.
3. **Unmapped guard = skip + count, never wrap.** After `andi #0x1FFF`, `if code >= 0x1000 → skip` and increment `pc090oj_unmapped_count`. Do not rely on the `0x0FFF` DMA wrap for high codes.
4. **Scan order:** decode `code & 0x1FFF`; `code==0 → skip` (existing); `code>=0x1000 → skip+count` (new, before the bitset lookup so the 4096-entry bitset is never indexed out of range); `blank_bitset[code] → skip+count` (new); else signed-coord/global-flip/offscreen tests → emit if drawable. Count decoded/drawable/emitted/dropped(blank)/unmapped separately.
5. **Preserve verified stale-SAT safety:** keep clear-before-scan; **confirm** `.Lvcs_sat_dma` DMAs all 80 entries every commit; prove the zero-emitted and decreasing-count cases directly.
6. **MANDATORY true VDP SAT capture** (`0xF800..0xFA7F`) post-DMA at a title/attract frame, as this build's validation — to resolve the black-overdraw stale-/true-SAT hypothesis (KF-021). Do NOT ship the filter as "the black-overdraw fix."
7. Byte/invariant discipline: report `opcode_replace` / `total_genesis_bytes_covered` deltas (bitset incbin + a few scan instructions + the DMA-size confirm); no other behavior change.

**evidence required from Cody (in the build's validation):**
- Regenerated blank bitset matches the independently-computed 22 blank codes (and updates automatically if the asset changes).
- A frame trace showing `unmapped_count`/`blank_drop_count` (expected 0 at title, per Build 0123) and that the 4 emitted sprites are unchanged.
- **True VDP SAT dump** at the title frame proving the committed SAT contains only the emitted (or offscreen/terminated) entries — the black-overdraw decider.
- Zero-emitted and decreasing-count frames (or a synthetic proof) showing no stale/black coverage.

**risks NOT solved by this implementation (state explicitly, do not overclaim):**
- **The black overdraw itself** — leading hypothesis is stale/true-VDP-SAT divergence (KF-021), NOT blank codes; the filter does not address it. The true-VDP-SAT capture (constraint 6) is where that gets resolved.
- **Producer coverage** — the mirror is fed by the `0x3AD44` dispatch + legacy per-site hooks; any unhooked PC090OJ write path still leaves the mirror incomplete (per the architecture audit). Not this task's scope.
- **256→80 overflow** — not exercised at title (few visible sprites); the drawable counter should flag if a future frame exceeds 80.

---

## Open / Closed Issues Impact

- **Open issues touched:** **OPEN-024** (PC090OJ sprite subsystem — this audit validates the blank/unmapped filter + confirms the phase-1 mirror/scan/clear/ctrl-capture/flip improvements; not closed — the black overdraw and true-VDP-SAT question remain), **OPEN-001** (context — sprite correctness feeds title completeness), **OPEN-006** (context — colbank now direct-captured `(sprite_ctrl&0xE0)>>1`), **OPEN-023** (contrast only). OPEN-015 not touched.
- **Closed issues touched:** NONE.
- **New issues opened:** NONE (recommend a tracked note that the black overdraw remains open pending true-VDP-SAT capture, distinct from the filter).
- **Issues closed:** NONE.
- **Issues intentionally deferred:** the black-overdraw root (true-VDP-SAT capture); producer-coverage completeness; 256→80 overflow policy; implementation itself.

## files changed
NONE (audit only).

## AGENTS_LOG updated
YES (analysis-doc log entry per standing process).

## STOP status
NO — audit complete; independent verification done; verdict issued.

---

# Required Final Recommendation

**GO:** Proceed to Cody implementation with the constraints in Part F (build-time generated blank bitset; emission-only, no mirror mutation; unmapped high-code skip+count, never wrap; preserve verified stale-SAT clear + full-80 DMA; MANDATORY true VDP SAT capture; do not present the filter as the black-overdraw fix).
