# Build 0340 — OPT-003 Prebaked Sprite Palette-Line Routing (STOPPED / implementation-ready, gate-blocked)

**Agent:** Andy · **Date:** 2026-09-02 · **Status:** STOPPED — implemented + proven output-identical, blocked by
seven-epoch gate; **not** in any numbered production ROM. Awaiting Tighe's decision.
**Prompt:** "ANDY — BUILD 0340 OPT-003 PREBAKE SPRITE PALETTE-LINE ROUTING" (ChatGPT-authored).
**Brief:** [Andy_opt003_prebake_sprite_palette_line_brief.md](Andy_opt003_prebake_sprite_palette_line_brief.md).

---

## 1. Phase 0 / classification / priors
- **Classification: EXTENDING.** Replaces an existing runtime computation (`palette_route_lookup` linear
  scan inside `.Lnative_palsel`) with a generated direct-lookup equivalent; **no semantic change**.
- **Priors:** KF-046 (arcade-bank→Genesis-CRAM-line route table `palette_route_table`/`palette_route_lookup`,
  keyed `(scene,owner,bank)→(line,flags)`) is the model this bakes. KF-066 (Build 0210 bank 0x36→line 0
  route) is one of the rows. No contradiction found; current source matches the brief's description.
- **Rediscovery hazards avoided:** did not re-derive the route model or the palette registry authority.
- **Issue impact:** no OPEN/CLOSED issue status changed.

## 2. Original hot path
- `.Lnative_pal_fixup` (pc090oj_hooks.s) loops over up to 80 emitted SAT entries (`pc090oj_emitted_count`),
  calling `.Lnative_palsel` per piece (unless a forced line is set).
- `.Lnative_palsel` (Build 0210 semantics), `RASTAN_GAMEPLAY_HUD_SPRITES != 1` path:
  1. `effective_bank = (d1 & 0x0F) | d7`, where `d7 = (pc090oj_sprite_ctrl_shadow & 0x00E0) >> 1`.
  2. `if effective_bank == 0x30: line = 2` (death-burst/effects special case, scene-independent, pre-lookup).
  3. else `palette_route_lookup(scene_id, PROUTE_OWNER_PC090OJ, effective_bank)` = **linear scan** of
     `palette_route_table` (rows of 5 words, ~10 rows), first match wins.
  4. miss → `line = (effective_bank >> 4) & 3`.
- `palette_route_lookup` (palette_hooks.s): linear scan, returns line or −1.
- Cost: a per-piece linear scan (~up to 10 rows × 3 compares) for ~28 pieces/frame avg (up to 72), 60×/s.

## 3. Proven runtime domain
- **Scene domain: scene_id ∈ {0,1,2}.** `scene_load.s` writes `genesistan_current_scene_id` from the PC080SN
  tileset id after collapsing ids ≥ 3 to gameplay scene 1 (`cmpi #3 / blo / moveq #1`). Only 0,1,2 reach it.
  Only scene 1 has PC090OJ route rows; scenes 0/2 are pure special-case + fallback.
- **Effective-bank domain: eb ∈ [0, 0x7F].** nibble (0..0x0F) OR-ed with colbank `(x&0xE0)>>1` ∈
  {0x00,0x10,…,0x70}; no bit overlap → 0..0x7F.
- **Special case / fallback (baked verbatim):** `eb==0x30 → 2`; route hit → table line; miss → `(eb>>4)&3`.

## 4. Generated LUT architecture
- **Generator:** `tools/translation/gen_pc090oj_palsel_lut.py` (project-owned, reusable; Makefile-wired,
  runs `--verify` every build).
- **Generated artifact:** `apps/rastan-direct/out/pc090oj_palsel_lut.inc` — `pc090oj_palsel_lut`, a byte LUT.
- **Dimensions:** NUM_SCENES = 4 (power-of-two; scene index masked 0x03), BANK_WIDTH = 128 (masked 0x7F),
  1 byte/entry, value = line 0..3. Total **4 × 128 = 512 bytes**.
- **Index formula:** `index = (scene_id & 0x03) << 7 | (effective_bank & 0x7F)`. Scene proven 0..2, so the
  mask is always in-bounds without a runtime branch; the unreachable scene-3 row is filled with the same
  special/fallback content.
- **Source-of-truth relationship:** the generator PARSES `palette_route_table` (PC090OJ rows) from
  `palette_hooks.s` and encodes the two hardcoded rules (0x30→2, `(eb>>4)&3`). Editing the route table
  regenerates the LUT; there is exactly **one authored source** and **one derived table**.
- **DERIVED DATA, NOT A REGISTRY:** the LUT is a performance artifact. `specs/palette_decisions.json`
  remains the sole palette-decision registry and is neither read nor written. The known
  `palette_decisions.json` vs `palette_route_table` divergence (e.g. bank 0x33, 0x36) is intentionally
  **NOT** reconciled — the LUT reproduces the current live ASM route behavior only.

## 5. Offline equivalence results (`--verify`, Part D)
- **Combinations tested: 512** (4 scenes × 128 banks).
- **Route-hit cases: 7** · **Fallback cases: 501** · **Special-case (0x30) cases: 4** (one per scene).
- **Mismatches: 0.**
- Hand-anchored spot checks (tie the oracle to human-verified route-table semantics), all PASS:
  - scene 1 bank 0x30 → **2** (special)
  - scene 1 bank 0x33 → **0** (route)
  - scene 1 bank 0x36 → **1** (route)
  - scene 1 bank 0x31 → **3** (miss, `(0x31>>4)&3`)
  - scene 0 bank 0x33 → **3** (frontend miss)
  - scene 0 bank 0x30 → **2** (special)
- The 47 pattern-reuse / palette-decision divergences were explicitly NOT the oracle; expected output =
  current runtime behavior.

## 6. Runtime OPT-003 replacement
- **Effective-bank computation preserved EXACTLY** (`(d1&0x0F)|d7`), unchanged from Build 0210.
- **Direct indexed load:** compute index, `lea pc090oj_palsel_lut,%a0`, `move.b 0(%a0,%d0.w),%d2`, line→d0.
- **Per-piece linear scan removed:** `.Lnative_palsel` no longer calls `palette_route_lookup` and no longer
  scans `palette_route_table` in the `!= 1` path. The `RASTAN_GAMEPLAY_HUD_SPRITES == 1` path keeps the
  inline special-case + `(eb>>4)&3` fallback unchanged (LUT not built for that mode).
- **Register contract preserved:** preserves d1–d3 and d7, output line in d0, clobbers d0/a0 (as before).
- **Remaining callers of `palette_route_lookup`:** **0.** It was the only caller; `tilemap_hooks.s:50` is an
  `.extern` declaration, never a `bsr`/`jsr`. `palette_route_lookup` + `palette_route_table` are RETAINED
  unstubbed — the table is the generator's source-of-truth and the routine is the human-readable reference
  algorithm. Reported dead-for-cleanup, **not** auto-deleted or NOP/RTS-stubbed.
- **Why no `shift_replacements` reflow was required:** the change lives entirely in **linked native helper
  code** (pc090oj_hooks.o), whose symbols are resolved via `nm`→symbol.txt and referenced by the arcade
  patch by name. Changing native code size only shifts native symbol addresses, which the link + operand
  relocation absorb; it does not alter the arcade maincpu byte stream, so the variable-length reflow path
  is not involved. Canonical GATE_PASS confirmed relocation/coverage consistency.

## 7. Seven-epoch gate result
- **Failing epoch: epoch 1, record 3.** Epoch 0 PASS; epochs 2–6 not reached (gate stops at first fail).
- **Assertion:** `full_plane_a_lut=FAIL`, `plane_a_lut_mismatch=index=308 code=034C expected=04E0 actual=0000`
  — one Plane-A nametable cell (index 308) read `0000` (not-yet-written) at the sampled frame.
- **All other gate metrics identical** between the OPT-003 build and the clean revert (below):
  `external_frames=336`, `target_epoch=1`, `required_patterns=394`, `map_count=395`, `upload_count=394`,
  `epoch_transitions=2`, `pattern_dma_transitions=2`, `installer_injections=1`, `exceptions=0`,
  `sp_valid=YES`, `full_fixed_plane_b_lut=PASS`. Only the single Plane-A cell differs.
- **Evidence:** `states/traces/build0340_phase1_epoch_gate_20260902_170048/epoch_1_record_3/`
  (epoch_gate_summary.txt, epoch_gate_events.tsv, mame_stdout/stderr). MAME ran at ~1013% for 336 frames;
  target epoch became active at frame 328 (`patterns=394 maps=395 uploads=394`), sampled ~336.

## 8. Differential / revert experiment
- **Reverted:** only the two OPT-003 source edits in `pc090oj_hooks.s` (the `.include` and the
  `.Lnative_palsel` body), restoring the pre-OPT-003 scan. All other working-tree state (the uncommitted
  0337–0339 diagnostic work, vdp_comm.s, etc.) left intact. Makefile LUT rule left in place but inert
  (nothing includes the LUT).
- **Result:** the reverted tree **PASSED all seven epochs** and published.
- **Proven:** OPT-003 is what flips epoch 1 from PASS to FAIL; the failure is deterministic (both OPT-003
  runs failed with the identical signature; the revert passed on first run). The palette OUTPUT is
  independently proven identical (§5), and Plane-A is a domain OPT-003 does not write.
- **Interpretation (not proof):** the most consistent reading is a single-cell Plane-A nametable-fill timing
  race at the exact frame-336 sample, tipped by OPT-003's native code-layout shift (the palsel routine
  changed size + 512 B of LUT rodata was added, relocating downstream native symbols). Because every other
  metric is byte-identical and the game runs correctly to the waterfall and beyond (Tighe confirmed
  0338/0339/0340 play fine), this reads as gate-sampling fragility rather than a real Plane-A defect. That
  interpretation is not yet independently proven at the cell-write-timing level.

## 9. Build-number incident (disclosure)
- The differential test in §8 was run with `make all`, which **publishes and numbers on GATE_PASS**. The
  **reverted (non-OPT-003) ROM therefore consumed Build 0340** — effectively a rebuilt 0339.
- **Counter/ledger state:** `build_counter.txt = 340`; `consumed_build_numbers.txt` records
  `0340 PRODUCED 2026-09-02 auto-recorded-by-release`; `dist/rastan-direct/rastan_direct_video_test_build_0340{,_d,_s}.bin` exist.
- **The 0340 release ROM does NOT contain OPT-003.** It is a functional equivalent of 0339.
- **Do not rewrite history or reuse 0340.** This was my procedural error (should have used a throwaway build
  path for a differential test); flagged openly, not hidden. Any eventual OPT-003 candidate must be **0341
  or later**.

## 10. Current repository state
- **OPT-003 implementation is RESTORED in the working tree** (the two `pc090oj_hooks.s` edits re-applied).
- **No further numbered build produced** after the accidental 0340.
- **Files added by OPT-003:**
  - `tools/translation/gen_pc090oj_palsel_lut.py` (generator + verifier)
  - `apps/rastan-direct/out/pc090oj_palsel_lut.inc` (generated artifact)
  - `docs/design/Andy_opt003_prebake_sprite_palette_line_brief.md` (pre-work brief)
  - `docs/design/Andy_build0340_opt003_prebaked_sprite_palette_line.md` (this document)
- **Files modified by OPT-003:**
  - `apps/rastan-direct/src/pc090oj_hooks.s` (`.include` of the LUT + rewritten `.Lnative_palsel`)
  - `apps/rastan-direct/Makefile` (LUT vars, generation rule with `--verify`, LUT as a `pc090oj_hooks.o` prereq)
  - `apps/rastan-direct/out/pc090oj_hooks.o` (rebuilt object; build output)
- `OPTIMIZATIONS.md` OPT-003 status updated to STOPPED/gate-blocked (no production savings recorded).

## 11. STOP status
- **Why stopped:** OPT-003 is output-correct and builds, but deterministically fails the seven-epoch gate on
  a single Plane-A cell, and the differential test consumed a build number. Publishing requires GATE_PASS;
  I will not fake it, and I will not iterate builds or touch the gate/counter without Tighe's decision.
- **Decision still required (Tighe):**
  1. Gate: accept as sampling fragility and widen the epoch-gate settle window (add a settle frame) so
     OPT-003 can build as 0341? / re-baseline? / investigate the cell-write timing first?
  2. Build number: leave 0340 consumed (OPT-003 → 0341) or roll the counter back (0340 was a duplicate)?
- **OPT-003 is NOT IMPLEMENTED in a numbered production ROM.** No such claim is made anywhere.

## 12. Performance status
- **Intent:** remove the per-piece linear `palette_route_lookup` scan (≤80 pieces/frame) → one indexed byte
  load; also removes the route-scan from the busiest per-frame loop and shrinks the vblank frame.
- **Estimated saving (labeled estimate, NOT measured):** per piece the old path cost an indexed function
  call + up to ~10 route-row comparisons (3 word-compares each) + branch overhead; the new path is a small
  fixed index computation + one `move.b`. Rough order: tens of cycles saved per emitted piece; at ~28
  pieces/frame that is on the order of ~10³ cycles/frame, scaling with sprite load (more at 72 pieces).
- **No measured saving claimed.** The `_d` bar before/after (0339_d vs an OPT-003 `_d`) has not been
  captured because no OPT-003 numbered build exists yet.

## 13. Scaffolding inventory / removal status
- **No production scaffolding added.** No runtime old-vs-new comparison, no dual routing, no fallback-to-scan
  "just in case", no shadow state. The direct LUT is the sole production path; equivalence is proven offline.
- **Temporary investigation scaffolding, already removed:** the §8 differential revert was a temporary source
  edit; OPT-003 has been restored. The Makefile LUT rule was left in place during the revert but is inert
  without the include; with OPT-003 restored it is live and correct.
- **Retained (not scaffolding):** `palette_route_lookup` + `palette_route_table` are kept as the generator's
  authored source-of-truth and reference algorithm (0 live callers, reported for later cleanup).
- **Scratch:** build logs under the session scratchpad; no `/tmp` production scripts.

## 14. USER MUST VERIFY / deferred
- **USER MUST VERIFY (once an OPT-003 numbered build exists):** sprite palettes unchanged on title/frontend,
  attract throne, ROUND/READY, R1/P1 gameplay, water + dirt; Rastan and Lizardman colors unchanged; then
  compare 0339_d vs the OPT-003 `_d` green servicing band for the expected shrink.
- **Deferred (explicitly out of scope here):** the Plane-A cell-308 timing root cause; the
  `palette_decisions.json` vs ASM divergence; the deeper `(code,bank)` `code→line` bake (needs colbank
  invariance proof); OPT-004 CRAM/VBlank; the VRAM-reclaim / widen-Layer-A-window idea (separate analysis).

## 15. Next-build expectation
- **0340 is consumed** (non-OPT-003 ROM). Any eventual OPT-003 candidate must therefore be numbered **0341
  or later**. No numbered OPT-003 artifact exists yet.
