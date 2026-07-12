# OPEN_ISSUES.md

This file tracks unresolved project issues. Issues are added when identified by Tighe, Claude/Andy, Chad, Cody, or trace evidence. When an issue is resolved and verified, move it to CLOSED_ISSUES.md with the closing build and evidence.

Rules:
- Do not delete issues.
- Do not silently rename issues.
- Do not close an issue without a verification note and closure condition citation.
- Every Cody/Andy prompt must include an "Open/Closed Issues Impact" section.
- If a new issue is discovered during work, add it here before final response.
- If an issue is resolved, move it to CLOSED_ISSUES.md with full closure metadata.

---

## OPEN-001 — Build 0094 title/attract graphics incomplete

  - [2026-07-09 Build 0151] BEST 5 ranking SCORE/ROUND values restored: genesistan_hook_number_renderer_3c2e2 mapped its descriptor's absolute arcade source pointer with `& 0x0000FFFF` (kept the 0xC000 A5-base bits -> read 0x00FFCxxx zeros); fixed to `- ARCADE_WORKRAM_A5_BASE(0x0010C000)` (KF-039). Also fixed the leading-zero suppression (gated on a clobbered %d7 -> re-read count from live %a0). BEST 5 now shows 273100/257200/197800/125400/112000, rounds 3/3/3/2/2, names COB.. -- arcade-exact. ROM build_0151 SHA eab3a3fb.... Build 0150 (source-base only) intermediate. Evidence: docs/design/Andy_build_0151_highscore_score_round.md.
  - [2026-07-09 Build 0149] Title/credited-title HIGH SCORE header correct: (1) title score value 273100 restored by fixing the 0x3B802 work-RAM source remap (region base 0x00100000 -> arcade A5 base 0x0010C000); init was already correct. (2) Complete HIGH SCORE label retained through coin insertion by fixing genesistan_pc090oj_hook_target_59f5e to clear the arcade's record range 9..16 (0x00D00048) instead of 0..7 (which wiped label records 4..7 -> only 'RE'). ROM build_0149 SHA 84317ce9.... Build 0148 superseded/unaccepted. Evidence: docs/design/Andy_build_0149_title_highscore_coin_label.md.
  - [2026-07-09 Build 0147] Missing `UP` in `2UP` FIXED and extra leading-zero score rows removed by one general rule: `.Lpc090oj_decode_record` now applies an arcade->Genesis viewport origin (`PC090OJ_TO_GENESIS_Y_OFFSET=-8`, matching the background's +8 origin bias) plus an opaque-geometry clip (per-code `pc090oj_opaque_bbox`), so a record gets SAT representation only when >=1 opaque pixel survives the viewport. Fully-clipped leading-zero digits stay in the mirror but consume no SAT/scanline budget; `2UP` restored. ROM build_0147 SHA bb2af8f9.... No special-casing. Evidence: docs/design/Andy_build_0147_pc090oj_viewport_clip.md.
  - [2026-07-08 Andy analysis] Missing `UP` in `2UP` root-caused: arcade 8-px top-margin clip (`set_visarea` Y=8..247, pc090oj.cpp) is not reproduced by the Genesis PC090OJ decode, so leading-zero digit records (code 0x2A, top-inked, raw Y=0) that the arcade hides are given full SAT slots at screen Y0, overflowing scanline 0 (20/line H40 limit) and dropping the last chain sprite (record 45 = `UP`). Same root cause explains the extra visible score zeros (`000000` vs arcade `00`). Fix boundary: add a visible-area top-clip / vertical-ink representation gate to `.Lpc090oj_decode_record` (general rule, mirror preserved). Evidence: docs/design/Andy_missing_up_2up_header.md.
- **Status:** OPEN
- **Priority:** HIGH
- **Discovered by:** Tighe / project visual evidence
- **Observed in build/artifact:** Build 0094, `dist/rastan-direct/rastan_direct_video_test_build_0094.bin`, SHA256 `558c88b39b359af7ee1f2cee1fa2318dde34b20ebfab7d25e25c0a18e0a819e2`
- **Current summary:** Build 0094 supersedes the stale Build-59 blank-output framing. The title/attract path now reaches visible output, and the FG cell-composition zero-cell mechanism is fixed at runtime. The remaining OPEN-001 problem is incomplete/incorrect graphics output, not blank output and not the gameplay-start exception.
- **Proven Build 0094 evidence:**
  - Build 0094 is not byte-identical to Build 0092/0093 and contains the Option B compose-site instructions at runtime `0x707DA` / `0x707DC` / `0x707E0`.
  - Invariant passed: `total_genesis_bytes_covered=0x17CB58`, `opcode_replace=95`.
  - Address-map/helper-shift guard passed: range helper shifted to `0x707E6`, glyph per-cell helper to `0x70BCA`, shared store entry `0x707BC` unchanged.
  - Runtime title-entry trace: producer `0x3ACAE` hit once at frame 212; first render `0x3ACB6` hit once; FG range gate `0x707E6` hit 258 times; FG store `0x70794` hit 258 times, all with `%a6=0x00FF501A` and in-buffer offsets; 213 nonzero composed `%d1` stores, 45 zero stores; crash-halt events 0.
  - Before/after: Build 0092 had 258 stores all `%d1=0x0000`; Build 0094 has 258 stores with 213 nonzero composed cells. Store-time `%d1` is a composed Genesis cell word, not raw ASCII. The 45 zero stores are recorded only as a count and are not classified as a defect.
  - Evidence docs: `docs/design/Cody_tilemap_hooks_rebuild_dependency_fix.md`, `states/traces/build_0094_title_producer_entry_window_trace_20260622_183218/title_producer_runtime_analysis.md`.
- **User-visual observations from Tighe (not yet promoted to proven runtime facts):**
  - Text renders.
  - Large TAITO logo partly renders but is incomplete / missing tiles.
  - Sword/logo artwork is not displaying.
  - Text is not cleared between attract states.
  - Scrolling/item page shows rows of dots.
  - Credits work; attract mode proceeds; coin/start works.
  - Starting gameplay later reaches the exception handler.
  - The ROM does not currently run on real Genesis hardware (tracked separately as OPEN-017).

  - [2026-07-09 Build 0153] Gameplay scene-asset embedded-pointer relocation gap CLOSED for the complete proven family (KF-028/OPEN-016 class): 3 per-stage/substage pointer tables (arcade 0x059EC8 palette, 0x059C9A BG/tile, 0x059F1E layout; Genesis 0x05A0C8/0x059E9A/0x05A11E) declared in absolute_long_pointer_tables and relocated +0x200. Stage 1 outside palette now resolves (hook A0 0x5DB4E->0x5DD4E, staged nonzero 1->16, real colours, committed CRAM); black+one-pink gone. BG/tile+layout sources corrected too. Frontend + 0xC08C62 routing intact. Next boundary: gameplay BG tile-pattern VRAM load + tilemap population (scene_id stays 0, load_scene_tiles(1) doesnt fire) -- non-pointer, separate. ROM build_0153 SHA ee232cbd.... Evidence: docs/design/Andy_build_0153_gameplay_asset_pointer_relocation.md.
  - [2026-07-09 gameplay-init divergence, Outcome D] Blank Stage 1 outside root-caused: the gameplay scene-asset loader R_c (arcade 0x59DE8 / Genesis 0x59FE8) DOES execute (flag a5@0x13B0=0), but builds its palette/BG/tile source pointers from an embedded data table at Genesis 0x5A0C8 (arcade 0x59EC8) holding UNRELOCATED arcade pointers (0x5DB4E...); the postpatch relocates only instruction-operand absolutes, not embedded data-table pointers (KF-028/OPEN-016 class). So the palette hook reads 0x5DB4E (zeros) instead of 0x5DD4E (+0x200, real palette). Bounded fix = relocate the gameplay asset pointer tables +0x200 via the existing embedded-pointer relocation. No build (partial-visual risk). Evidence: docs/design/Andy_gameplay_init_control_flow_divergence.md.
  - [2026-07-09 Build 0153 analysis, Outcome G] Gameplay entry: Build 0152 clears the 0xC08C62 raw-write fault; the next boundary is proven to be non-execution of the gameplay PC080SN/palette scene-setup path. At state 2/3/0 (= arcade Stage 1 outside gameplay) load_scene_tiles is never called with scene ID 1 (scene_id stays 0, a0 stays title range), and neither the BG scroll-fill hook nor the palette producer hook runs during gameplay (0 scene-detection reads / 0 staged-palette writes vs 2/128 in the frontend), so tiles+palette never load and CRAM/BG stay blank. Not a bounded loader fix. Next: capture the arcade caller chain of the gameplay palette producer (0x059B0E/0x059AD4) and BG-descriptor fill, compare to Genesis to find the exact stop point. Evidence: docs/design/Andy_stage1_outside_scene_assets_analysis.md.- **Current unresolved graphics symptoms:** sword/logo artwork absent; TAITO logo incomplete/missing tiles; stale text between attract states; dot rows on scrolling/item page; no complete title/game graphics acceptance yet.
- **Next required task:** a graphics-only diagnostic for Build 0094 title/attract completion. Classify each missing/incomplete element through producer -> staging -> clear/dirty -> VBlank commit -> tile-pattern availability -> palette -> plane/priority/scroll. The gameplay-start exception is deferred and is not the next OPEN-001 task.
- **Gameplay-start crash discipline:** gameplay start reaches the exception handler, but on-screen crash fields are suspect under OPEN-015 and must be verified from the WRAM crash record before being treated as real. Do not record a specific fault PC, fault address, or vector from the on-screen fields.
- **Historical note:** Prior Build-58/59 blank-output, C-helper, and bootstrap-blocked wording is superseded for current Build 0094 planning. Those historical artifacts remain in their cited design docs and AGENTS_LOG entries; the active OPEN-001 state is the Build 0094 incomplete-graphics state above.
- **Closure condition:** title/attract graphics are visibly complete from game-executed render paths (not launcher/config/debug/exception text), with evidence that producer/staging/commit/tile/palette/plane-priority paths produce correct VDP-backed output.

---

## OPEN-002 — Build numbering and artifact naming ambiguity

- **Status:** OPEN
- **Priority:** HIGH
- **Discovered by:** Tighe
- **Observed in build/artifact:** Build 55b implementation
- **Summary:** Cody produced numbered output `rastan_direct_video_test_build_0057.bin` and copied it to `rastan_direct_video_test_build_0055b.bin`. Letter-suffix conventions create confusion across evidence, traces, and visual reports.
- **Evidence:** Cody Build 55b report states numbered output was `0057.bin`; same report states requested artifact created by copy as `0055b.bin`.
- **Decision:** Going forward, ROM artifacts use strictly sequential build numbers only. Planning labels (e.g., "55b" in prose) may appear in docs, but ROM filenames and trace folders must use the actual sequential build number. No copied alias ROMs unless explicitly marked as alias with SHA256 equality verification.
- **Build and task naming policy (mandatory) — UPDATED:**
  - ROM filenames must be strictly sequential. No letter suffixes (`0055b`, `0055c`, etc.).
  - Task labels, design doc filenames, dump directories, and trace folders must NOT use letter suffixes either. No `Cody_buildXXb_*.md`, no `states/dumps/buildXXb_*/`, no `states/traces/buildXXb_*/`, and no `[Agent — Build XXb ...]` task headers.
  - Build numbers are reserved for ROM-producing tasks. Evidence-only tasks (no ROM produced) should use descriptive names without build numbers — e.g., `Cody_offset_graphics_evidence.md` not `Cody_build58_offset_graphics_evidence.md`.
  - When a ROM is produced, it gets the next sequential build number based on the prior ROM-producing build (NOT the prior evidence task).
  - Planning labels in prose are still allowed (e.g., "the visible-state acquisition task") but must NOT use letter suffixes ("the 58c task" is wrong; "the visible-state acquisition" is correct).
  - Historical artifacts (`Cody_build58b_*`, `Cody_build58c_*`, `states/dumps/build58b_*`, `states/dumps/build58c_*`, ROM aliases like `rastan_direct_video_test_build_0055b.bin`) remain as-is. No renames. They serve as the historical evidence trail of why the policy was tightened.
  - If an alias is unavoidable for a ROM, the report must state: canonical artifact path, alias path, SHA256 of both, byte-identical YES/NO.
- **Suspected area:** build pipeline, artifact-naming policy, Cody implementation reports.
- **Next required task:**
  - Cody must compute SHA256 of `0057.bin` and `0055b.bin` and report whether byte-identical (DONE — see Build 58 evidence above).
  - For OPEN-002 closure: 3 consecutive ROM-producing builds must use strictly sequential numbering with no letter suffixes anywhere (filename, task header, design doc, dump directory, trace folder).
  - Going forward, evidence-only tasks use descriptive names without build numbers; ROM-producing tasks use sequential build numbers.
- **Evidence (Build 58 evidence task):**
  - `dist/rastan-direct/rastan_direct_video_test_build_0057.bin` SHA256: `703fe9d6c96b6264bb5911be5581acf31845e282e6bb827fab7e2c502c00ee16`
  - `dist/rastan-direct/rastan_direct_video_test_build_0055b.bin` SHA256: `703fe9d6c96b6264bb5911be5581acf31845e282e6bb827fab7e2c502c00ee16`
  - Byte-identical: YES
  - Canonical ROM going forward for this evidence chain: `0057.bin`
- **Evidence (Build 58c violation pattern):**
  - Cody "Build 58b" nametable dump task produced design doc `docs/design/Cody_build58b_nametable_dump_evidence.md` and dump directory `states/dumps/build58b_20260505_175403/` (and `states/dumps/build58b_20260505_175922/`).
  - Cody "Build 58c" visible-state acquisition task produced design doc `docs/design/Cody_build58c_visible_state_acquisition.md` and dump directory `states/dumps/build58c_20260506_132350/`.
  - These are letter-suffix violations of the original OPEN-002 policy spirit — they were tolerated only because the original wording covered ROM filenames specifically. The policy now extends to all task/doc/dump/trace artifacts.
  - These artifacts are NOT renamed; they serve as historical evidence.
- **Evidence (SGDK Slot Reservation Removal Implementation):**
  - ROM-producing implementation completed with sequential naming and no letter suffix in artifact name:
    - `dist/rastan-direct/rastan_direct_video_test_build_0059.bin`
  - Implementation design doc uses descriptive naming with no build number:
    - `docs/design/Cody_slot_reservation_removal_implementation.md`
  - AGENTS_LOG entry header uses descriptive naming:
    - `[Cody — SGDK Slot Reservation Removal Implementation]`
  - Note: intermediate numbered build `0058` was produced during first pass but remained byte-identical to `0057` due stale `.incbin` object dependency; clean rebuild produced `0059` with the actual LUT/preload shift. Both artifacts keep compliant sequential/no-suffix naming.
  - OPEN-002 clean-build progress marker: this implementation records **build 1 of 3** consecutive clean ROM-producing builds toward OPEN-002 closure.
- **Closure condition:** BUILD_NAMING.md or AGENTS_LOG entry codifies the policy; future build artifacts use only sequential numbering for ≥3 consecutive builds without aliases.

---

## OPEN-003 — MAME trace disagrees with Exodus visual palette result

- **Status:** OPEN
- **Priority:** HIGH
- **Discovered by:** Tighe / Cody trace conflict
- **Observed in build/artifact:** Build 55b
- **Summary:** Cody MAME trace reports `genesistan_palette_hook_3ba64` hit once, staged 64 zero values, never set `palette_dirty`, never reached `vdp_commit_palette`, and `_vblank_service` had 0 hits. Tighe reports Exodus shows palette loaded.
- **Evidence:**
  - Cody Build 55b MAME trace: helper hit count 1, staged writes 64 (all `post=0`), `palette_dirty=1` writes 0, `vdp_commit_palette` hit count 0, `_vblank_service` hit count 0.
  - Tighe visual observation: palette loaded in Exodus.
  - Prior Build 55a trace had `_vblank_service` 255 hits — Build 55b shows 0, suggesting either ROM identity confusion or a Build 55b regression.
- **Suspected causes:** MAME trace setup incomplete; trace watched wrong ROM artifact due to `0057` vs `0055b` aliasing; trace sampled only one helper hit; Exodus and MAME differ in execution path; palette visible in Exodus may come from crash handler, direct VDP write, or another CRAM source.
- **Suspected area:** ROM identity (per OPEN-002), MAME trace harness setup, `_vblank_service` reachability, alternative CRAM writers (crash_init_cram, direct VDP writes).
- **Next required task:** Cody video/debug extraction (in progress) may help reconcile; reconcile ROM identity by SHA256; trace exact ROM used in Exodus if possible; compare MAME and Exodus CRAM state over time; verify whether CRAM is changed by `vdp_commit_palette`, crash handler, direct VDP write, or another path.
- **Closure condition:** one report explains why MAME trace and Exodus visual result differ; trace identifies actual CRAM writer for the visible palette.
- **Evidence (Build 59 runtime state comparison):**
  - Validation artifact: `states/dumps/build59_runtime_state_20260507_142931/validation.txt`.
  - MAME on Build 59 (`0059.bin`) sampled at `sec_5/10/20/30/60/120`.
  - Outcome:
    - VRAM populated-state sentinels remained zero at every sampled timestamp.
    - Nametable first cells and sampled non-zero counts remained zero at every sampled timestamp.
    - `PC` left `0x03A19x` at `sec_30` and `sec_60`, but this did not correlate with populated VRAM evidence.
  - Conclusion: post-CLOSED-007, emulator divergence remains unresolved for active-state evidence capture; MAME did not provide a populated state matching Exodus for OPEN-001 composition decode in this run.
  - Full report: `docs/design/Cody_build59_runtime_state_comparison.md`.
- **Next required task:** perform Exodus-side synchronized byte capture for the same five ranges used by MAME validation, then compare against MAME captures to isolate divergence at VRAM/nametable/register level.
- **Evidence (Build 59 MAME script anomaly — sub-finding):**
  - Cody Build 59 runtime state comparison (`docs/design/Cody_build59_runtime_state_comparison.md`) MAME validation.txt across 6 timestamps reported all-zero VRAM sentinels (`0x029A`, `0x02AA`, `0x02C0`, `0x0020`), all-zero Plane A/B first cells, all-zero non-zero word counts in `0x0000..0x1FFF`, `0xC000..0xCFFF`, `0xE000..0xEFFF`.
  - Same ROM in Exodus (per `Cody_build59_video_30fps_debug_windows.md` accurate findings + Tighe direct verification) shows populated VRAM (Pattern Viewer with real tile data, VRAM Memory Editor with structured non-zero data), populated CRAM with mixed values.
  - Possible explanations:
    - MAME script reads wrong address space (e.g., reading raw RAM instead of VDP VRAM through the proper VDP debug interface)
    - MAME instrumentation captures VRAM at a moment before tile data is written
    - Genuine MAME-vs-Exodus runtime divergence: MAME execution path differs from Exodus, never writes the VDP state Exodus reaches
    - Timing/race: sampling happens between writes
    - Stale readback: MAME VDP debug interface returns cached state
  - Insufficient evidence to discriminate. Tracked as OPEN-003 sub-finding rather than new issue. Resolution may come from: comparing Cody MAME script against MAME debug API documentation, capturing MAME state via a different instrumentation path, or correlating Cody MAME PC samples (`0x071A48`, `0x070610` at `sec_30/60`) with arcade code that writes VDP — if those PC samples ARE in VDP-write code paths but VRAM remains empty, instrumentation is suspect; if NOT in VDP-write paths, MAME execution genuinely doesn't reach the writes.

---

## OPEN-004 — Bootstrap re-entry / soft-reset loop

- **Status:** OPEN
- **Priority:** HIGH
- **Discovered by:** Cody / Andy
- **Observed in build/artifact:** Builds 55a / 55b
- **Summary:** Execution repeatedly re-enters bootstrap/startup path around `0x0202 → 0x022C → 0x024A`, approximately 15 times in 64 seconds. Not normal arcade progression.
- **Evidence:** Cody origin archaeology shows repeated chain `0x022C → 0x024A → 0x03B110 → 0x03BBF8 → 0x03BC64`; Andy classified bootstrap re-entry as pre-existing invariant 8 violation and contributing issue (`docs/design/Andy_build55_active_palette_writer_classification.md` §1.5 / §1.7).
- **Suspected causes:** exception vector, watchdog-like reset behavior, HV Counter / control port issue, bad return vector or stack corruption, intentional but currently misunderstood startup loop.
- **Suspected area:** exception vector table at `0x0008..0x003C`, bootstrap entry `0x0202`, return-from-init paths, possible interaction with OPEN-005.
- **Next required task:** future evidence task (next sequential build number after 57): breakpoint on `0x0202`; capture last N PCs before each re-entry; inspect exception vectors and SR; determine exact trigger source.
- **Closure condition:** trigger source identified and fixed, OR proven intentional/benign with cited evidence.

---

## OPEN-005 — BlastEm HV Counter / control port 8 fatal

- **Status:** OPEN
- **Priority:** HIGH
- **Discovered by:** BlastEm runtime
- **Observed in build/artifact:** Builds 54 / 55 / 55b
- **Summary:** BlastEm reports illegal write to HV Counter / control port 8. Parked during palette work. May relate to bootstrap re-entry or emulator divergence.
- **Evidence:** BlastEm crash screenshot from Build 54 visual test; Andy notes HV Counter relation is plausible but not evidence-supported (`docs/design/Andy_build55_active_palette_writer_classification.md` §1.5); MAME may tolerate behavior that BlastEm hard-fails.
- **Suspected causes:** arcade init code writing to a Genesis-mapped address that conflicts with HV Counter port behavior.
- **Suspected area:** VDP HV Counter address `0xC00008`, arcade init paths, emulator-specific strictness.
- **Next required task:** evidence-only trace targeting writes to VDP / HV / control port addresses; capture PC, instruction, registers, call chain; correlate with bootstrap re-entry trigger (OPEN-004).
- **Closure condition:** illegal writer identified; fix implemented OR proven harmless under target hardware rules.

---

## OPEN-006 — Sprite / high-bank palette mapping deferred

- **Status:** OPEN
- **Priority:** MEDIUM
- **Discovered by:** Andy / Cody
- **Observed in build/artifact:** Build 55 design
- **Summary:** Palette banks ≥ 4 are skipped per `bank < 4` rule. Sprite palette bank mapping deferred because sprite `%d1`/`%d7` provenance and arcade sprite bank → Genesis CRAM line mapping unproven.
- **Evidence:** Cody Build 56 follow-up artifact `docs/design/Cody_build56_sprite_palette_bank_mapping_todo.md`; high banks identified: `0x04, 0x05, 0x06, 0x33, 0x41, 0x43`, banks `48..79` from `0x045DE4` path.
- **Suspected area:** PC090OJ sprite attributes, sprite caller register provenance, `apps/rastan-direct/src/pc090oj_hooks.s` lines 128-136.
- **Next required task:** trace sprite palette bank provenance from PC090OJ sprite attributes; derive arcade sprite palette bank → Genesis CRAM line mapping.
- **Build 0145 bank-51 line-3 delivery (2026-07-08, Outcome A, retained):** completes the frontend sprite palette. Modified only `genesistan_palette_hook_59ad4` (arcade `0x059AD4`) to accept the arcade's bank-51 update (`d0=0x33`) and stage it into Genesis line 3 via the existing conversion/staging body (source arcade bank 51 `0x00200660`, destination `staged_palette_words` line 3). ROM `dist/rastan-direct/rastan_direct_video_test_build_0145.bin` SHA `b5c903a942b669e869b5b2d4ed4448f96d402707e3dcda946afabe2eb4dd23f7`. Item screen (2/2/6): staged line 3 now nonzero and equals converted arcade bank 51 word-for-word (16/16); records 64-67 select line 3; the four item sprites render VISIBLE with correct bank-51 colours (green/red weapon, red sword) — were black in Build 0144. Bank 48 / line 2 / header (1UP yellow, HI SCORE orange) / planes unchanged. Frontend sprite palette now COMPLETE: bank 48 -> line 2 + bank 51 -> line 3, both resident. Remaining OPEN-006 scope: general high-bank mapping for gameplay/other arcade sprite banks. Evidence: `docs/design/Andy_build_0145_bank51_line3_delivery.md`.
- **Build 0144 frontend sprite-palette split (2026-07-08, Outcome B, retained):** implemented the proven assignment — SAT selector (`.Lpc090oj_place_record_in_slot`) maps effective bank 0x30(48)->Genesis line 2, 0x33(51)->line 3, else `(bank>>4)&3`; palette determiner `genesistan_palette_hook_3ba64` routes arcade bank 48->line 2, bank 51->line 3 (banks 0/1 kept on lines 0/1, others skipped). ROM `dist/rastan-direct/rastan_direct_video_test_build_0144.bin` SHA `ba1ed586daa587cf0f6d2ffe851c0771b9d4ad42fb94677af42cdeed3d9d91ae`. Runtime (5 frontend screens): selectors correct (bank 48->line 2, bank 51->line 3, both present on item screen; SAT geometry/identity byte-identical to Build 0142, only palette bits changed). **Bank 48 header colours now render arcade-correct on all 5 screens (1UP yellow, HI SCORE orange; was purple in 0142) — primary goal fixed.** **Bank 51 line 3 stays all-zero** (four item sprites render black) because arcade bank 51 (palette RAM 0x200660) is NOT carried by 0x03BA64 (covers banks 0..48, 0x200000..0x20061F); it reaches staging via `genesistan_palette_hook_59ad4` (0x059AD4, d0=0x33), which this task did not modify. Retained (selector split + bank-48 delivery are a genuine architecture-compliant improvement). Remaining OPEN-006 work: route arcade bank 51 into staged line 3 via 0x059AD4. Evidence: `docs/design/Andy_build_0144_frontend_sprite_palette_split.md`.
- **Frontend CRAM line-ownership verification (2026-07-08, Outcome A):** across all five frontend screens (title 0/1/0, throne/story 0/1/2, high-score 2/0/0, item-desc 2/2/6, coined-up 1/1/0; all sprite_ctrl_shadow=0x60, colbank 48): Genesis CRAM **line 2 is unowned** — zero Plane A / Plane B / Window / SAT selectors and all-zero CRAM (staged + VDP pen_color); **line 3 is sprite-exclusive** — no plane/Window consumer, and under the current `(bank>>4)&3` renderer all frontend sprites (banks 48 and 51) hash to line 3 (item screen: bank 48 records 28-45 + bank 51 records 64-67 co-resident). CRAM lines 2/3 are written only by the boot BSS zero-clear (`0x0002A4`) and the `0x03BA64` palette path (`0x0718DA` → staged_palette_words → palette_dirty → vdp_commit_palette); CRAM line N currently mirrors arcade bank N via the single `0x03BA64` boot load (colbank 0). CRAM line 3 is **static** (byte-identical across all five screens) with no restoration producer. Consequence for the deferred fix: line 2 is a free line; line 3 can hold bank 51 only if the header bank (48) is first routed off line 3 (renderer decision). Evidence: `docs/design/Andy_frontend_cram_and_palette_line_ownership.md`, `states/traces/frontend_cram_palette_line_ownership/`.
- **Build 0143 implementation attempt (2026-07-07, Outcome C):** the authorized coordinated fix (renderer line=`((word0&0x0f)|colbank)&3`; producer `0x03BA64` window `line=bank-((sprite_ctrl_shadow&0xE0)>>1`) was implemented, built (rejected ROM SHA `4518bd0bfd19ce4e014a9d13b17eedafae03aac8afe6d354e4baef2227136bec`), validated as FAILING, and reverted. The renderer change works (header bank 48 -> Genesis line 0, item bank 51 -> line 3), but the producer cannot deliver the CRAM: native trace shows `0x03BA64` loads arcade bank 48 (`a0=0x200600`) while `pc090oj_sprite_ctrl_shadow=0x0000` (colbank 0, window rejects it) and is never re-invoked after the colbank->0x60 transition; the live per-colbank load fires through a DIFFERENT producer `genesistan_palette_hook_59ad4` (`0x0717AE`) with `d0`=effective bank (e.g. 0x33=51), gated `<4`. Genesis CRAM lines 0-3 stay arcade banks 0-3. A single current-shadow-keyed producer window cannot align; a real fix must reconcile producer invocation timing with the sprite_ctrl colbank write and likely span `0x059AD4`/`0x045DAE` (outside a bounded single-producer change). Evidence: `docs/design/Andy_pc090oj_dynamic_sprite_palette_window_build_0143.md`.
- **Build 0143 audit (2026-07-07):** frontend-header manifestation PROVEN (ARCADE vs GENESIS MAME, `docs/implementation/Andy_frontend_header_palette_build0143.md`). Arcade frontend runs global `sprite_ctrl=0x60` → `sprite_colbank=48` (`pc090oj.cpp:187` `color=(word0&0x0f)|sprite_colbank`). Header text (records 28–45, word0=0) → arcade bank 48 (orange/yellow/white); large item-icon sprites (records 64–67, word0=3) → arcade bank 51. The Build 0142 renderer's `(color>>4)&3` aliases both bank 48 and 51 (indeed banks 48–63) onto Genesis line 3, and `genesistan_palette_hook_3ba64` (arcade 0x03BA64) loads only arcade banks 0–3 into lines 0–3 by bank index — so line 3 holds bank 3 (purple). The two mappings are inconsistent and the 128 arcade banks cannot be separated across 4 Genesis lines without a colbank-aware bank→line assignment (renderer formula + producer). Outcome C: bounded header fix not possible without this broad mapping.
- **Closure condition:** sprite palette mapping implemented and visually verified, OR explicitly ruled out for current milestone with documented decision.

---

## OPEN-007 — Build 55a palette helpers patched but inactive until arcade progresses

- **Status:** OPEN
- **Priority:** LOW
- **Discovered by:** Cody MAME runtime trace
- **Observed in build/artifact:** Build 55a / 55b
- **Summary:** Three palette helpers at `0x59AD4`, `0x03AB00`, `0x045DB8` patched correctly but not reached during current startup-loop runtime. May activate after bootstrap re-entry (OPEN-004) is fixed.
- **Evidence:** Cody MAME trace — all three helpers hit count 0 over 64 seconds (`docs/design/Cody_build55_mame_palette_runtime_trace.md` §2.1); Andy classification recommends keeping them (`docs/design/Andy_build55_active_palette_writer_classification.md` §1.6).
- **Suspected area:** dependent on OPEN-004 resolution.
- **Next required task:** after bootstrap re-entry fix, rerun helper reachability trace.
- **Closure condition:** helpers either reached and verified, OR proven dead/unneeded and removed by design decision.

---

## OPEN-008 — Need standard issue-tracking process in every prompt

- **Status:** OPEN
- **Priority:** HIGH
- **Discovered by:** Tighe
- **Observed in build/artifact:** Current workflow (issues being rediscovered across prompts)
- **Summary:** OPEN_ISSUES.md and CLOSED_ISSUES.md must become mandatory project artifacts that every Cody/Andy prompt reads and updates.
- **Evidence:** Multiple investigation cycles revisiting same issues (white CRAM, bootstrap re-entry, HV Counter) without persistent tracking.
- **Suspected area:** prompt-template convention, agent workflow.
- **Next required task:** prompt template addition (this file's "Prompt Template Requirement" section addresses this); enforce by inclusion in next 3 consecutive Cody/Andy prompts.
- **Closure condition:** prompt template updated and used in next 3 consecutive Cody/Andy prompts with proper Open/Closed Issues Impact section.

---

## OPEN-014 — MAME tracer does not reliably sample a parked diagnostic-bookmark helper

- **Status:** OPEN
- **Priority:** MEDIUM
- **Discovered by:** BM-003 Insert (Cody), surfaced during Outcome-A classification
- **Observed in build/artifact:** Build 0076 BM-003 diagnostic cycle
- **Summary:** The diagnostic helper `genesistan_diag_bookmark` at `0x00071C78` is a 2-byte `BRA -2` self-loop (`60 FE`). In BM-003, helper park was confirmed by Tighe's direct Exodus observation and corroborated by MAME exit summary (`Final PC 0x071C7A`), but the BM-003 MAME sampled trace log did not directly sample the parked helper loop. Because helper park is the Outcome-A signal for bookmark cycles, this is a known instrumentation gap in the current MAME trace path.
- **Evidence:** `dist/rastan-direct/bookmarks/build_0076_pc_0x0003A19C/`; `docs/design/Cody_BM003_insert.md`.
- **Impact:** Bookmark cycles can be confirmed via Exodus/BlastEm and MAME exit summaries, but the primary sampled MAME trace path does not always self-evidence helper-park Outcome A.
- **Next required task:** Andy design question for reliable helper-park capture (e.g., tracer sampling mode for helper PC range, alternate trace tool path, or helper observability construct). Not fixed in BM-003 Revert.
- **Closure condition:** Trace mechanism update demonstrably captures helper park directly and reliably in a bookmark Outcome-A run.
- **Cross-references:** OPEN-012, OPEN-013, Rule 10, diagnostic bookmark helper design.

---

## OPEN-015 — crash_handler.s numeric renderer prints cursor offsets instead of saved crash values

- **Status:** OPEN
- **Priority:** HIGH
- **Discovered by:** Andy / Tighe
- **Observed in build/artifact:** KF-028 patched ROM crash triage, `docs/design/Andy_kf028_patched_rom_address_error_triage.md`
- **Summary:** The crash handler stores real diagnostic values in WRAM, but the on-screen hex fields are wrong. `crash_put_hexN_at` calls `crash_set_cursor` after the caller loads the value into `%d2`; `crash_set_cursor` clobbers `%d2` with `row*128 + col*2`. As a result, `VECTOR`, `FAULT PC`, `FAULT ADDR`, `SR`, registers, and the DEST/DIRTY/FRAME block display cursor offsets, not saved diagnostic values. A second reliability defect exists in `_crash_common`: it decodes the group-0 frame into `d1-d5`, sets `a0=sp`, and sets `a1=.Lhandler_pc_marker` before saving registers, so saved `D0-D5/A0/A1` are frame/handler values rather than true at-fault registers.
- **Reliable fields:** The exception name is reliable because it is string-rendered. The stack dump is reliable because each stack word is loaded into `%d2` after cursor setup.
- **Scope of impact:** This is a pre-existing baseline diagnostic defect in `crash_handler.s`, not caused by the KF-028 input-shim wiring fix. Any crash rendered through this handler can show bogus numeric fields and mislead triage.
- **Workaround (verified working):** Read the real crash record directly from WRAM in the emulator memory viewer:
  - `0xFF6804` = `CRASH_STACKED_SR` word
  - `0xFF6806` = `CRASH_STACKED_PC` long
  - `0xFF6854` = `CRASH_FAULT_ADDRESS` long
  - `0xFF6816..0xFF684E` = saved D0-A6 register block
- **Saved-register caveat:** In the current crash record, saved `D0-D5/A0/A1` are not true at-fault register values:
  - `D0` = exception type
  - `D1` = stacked SR
  - `D2` = stacked PC
  - `D3` = IR
  - `D4` = fault address
  - `D5` = SSW
  - `A0` = handler SP
  - `A1` = handler marker
  - Only `D6/D7/A2-A6` are genuine at-fault register values in this crash record.
- **Evidence:** Andy's corrected triage proves every on-screen numeric field equals that field's cursor offset, not the intended value. The WRAM workaround was used successfully on 2026-06-17 to recover the real fault PC `0x0003BD68` and fault address `0x50205741` from the KF-028 patched ROM crash, after the on-screen render showed cursor-offset artifacts.
- **Evidence (second reliability defect):** `docs/design/Andy_kf028_real_fault_triage.md` shows `_crash_common` overwrites `d1-d5/a0/a1` with frame/handler values before saving the register block. This loses true at-fault `D1-D5/A0/A1` values; the real faulting `a1` is not preserved, while the fault address from the exception frame remains reliable.
- **Build 0094 gameplay-start note:** Tighe reports Build 0094 can reach Start/gameplay and then crash to the exception handler. This issue remains the crash-data discipline gate: on-screen crash fields are unreliable unless verified from the WRAM crash record. Gameplay-start crash triage is deferred relative to graphics completion.
- **Suspected area:** `crash_handler.s` numeric rendering wrappers (`crash_put_hex8_at`, `crash_put_hex16_at`, `crash_put_hex32_at`), `crash_set_cursor` register preservation, and `_crash_common` register-save ordering.
- **Fix direction:** Either preserve `%d2` across `crash_set_cursor`, or restructure the `crash_put_hexN_at` wrappers so the cursor is set first and the value is loaded into `%d2` afterward. Also preserve true at-fault `D0-D5/A0/A1` before `_crash_common` repurposes those registers for exception-frame decode and handler bookkeeping.
- **Next required task:** Fix both crash-handler reliability defects, rebuild, and reproduce a crash or unit-style crash-render validation to confirm on-screen numeric fields match the WRAM crash record and saved register fields preserve true at-fault values where architecturally available.
- **Closure condition:** A crash-render validation shows `FAULT PC`, `FAULT ADDR`, `SR`, registers, and DEST/DIRTY/FRAME fields display the saved WRAM crash-record values rather than cursor offsets, and the saved register block no longer replaces `D0-D5/A0/A1` with frame/handler scratch values.

---

## OPEN-016 — embedded absolute data-pointer tables are not relocated by +0x200

- **Status:** OPEN
- **Priority:** HIGH
- **Discovered by:** Andy
- **Observed in build/artifact:** KF-028 patched ROM crash, `docs/design/Andy_kf028_title_text_descriptor_provenance.md`
- **Summary:** The title glyph-renderer descriptor table at Genesis `0x3BD7C` is a confirmed embedded absolute data-pointer table whose entries were not relocated by the `+0x200` identity offset when the arcade ROM blob moved into the Genesis image. The table entries are absolute ROM pointers into the relocated arcade blob, but they remain arcade addresses.
- **Confirmed instance:** The glyph/string renderer at `0x3BD48` indexes the descriptor-pointer table at `0x3BD7C`. For index 65, `table[65]` is read from `0x3BE80`.
- **Concrete example:**
  - arcade descriptor index 65 = `0x3C246`
  - relocated Genesis descriptor = `0x3C446`
  - current Genesis `table[65]` incorrectly remains `0x3C246`
  - Genesis `0x3C446` contains the valid descriptor header `0x00C0914C | 0x0000 | "OTHERW..."`
- **Crash mechanism:** Because `table[65]` stayed stale at `0x0003C246`, the renderer read text bytes at Genesis `0x3C246` as `descriptor[0]`. Those bytes are `0x50205741` (`"P WA"`, odd-aligned), so the write at `0x3BD66` (`movew %d2,%a1@+`) address-errored when using text data as a destination pointer.
- **Scope of impact:** This is a missing/incomplete Genesis translation of embedded absolute data-pointer tables. `postpatch_lenient.py` relocates absolute targets in instruction operands, but this confirmed table is data, not an instruction operand. Other embedded absolute data-pointer tables in the relocated arcade blob may also be stale and latent crash sources.
- **Immediate fix direction:** Relocate the `0x3BD7C` descriptor-pointer table entries by `+0x200`, after confirming the exact table length.
- **Immediate instance status (2026-06-18, Cody):** FIXED for the confirmed title glyph/string descriptor-pointer table instance only. Cody confirmed the actual table is 71 longwords (`0x03BD7C..0x03BE97` runtime Genesis), added a narrow `absolute_long_pointer_tables` entry in `specs/rastan_direct_remap.json`, and verified `table[65]` at `0x03BE80` now changes from `0x0003C246` to `0x0003C446`. See `docs/design/Cody_OPEN016_descriptor_pointer_table_relocation.md`.
- **Build 0094 status (2026-06-22, Cody):** OPEN-016 remains OPEN. The immediate descriptor-pointer table instance is relocated; the glyph renderer is routed into the FG staging path; the Build 0091 missing-helper-base-register address error is fixed; and Build 0094 validates the Option B zero-cell composition fix at runtime (`0x70794` stores: 258 total, 213 nonzero composed `%d1`, 45 zero). Do not close OPEN-016 on nonzero cells alone: the broader embedded absolute data-pointer-table survey remains, and title/attract visual acceptance is incomplete.
- **Broader follow-up:** Survey the relocated arcade blob for other embedded absolute data-pointer tables with the same unrelocated-pointer gap. This survey is needed after the immediate crash fix or alongside it, but was not performed when this issue was opened.
- **Related findings/issues:** KF-028, KF-013, OPEN-001, OPEN-004, OPEN-015.
- **Closure condition:** The `0x3BD7C` table is relocated correctly in the Genesis image, the KF-028 patched-ROM title-text crash no longer dereferences text bytes as a destination pointer, and a bounded survey either relocates or explicitly clears other embedded absolute data-pointer tables in the relocated arcade blob.

---

## OPEN-017 — Build 0094 ROM does not currently run on real Genesis hardware

- **Status:** OPEN
- **Priority:** HIGH
- **Discovered by:** Tighe
- **Observed in build/artifact:** Build 0094, `dist/rastan-direct/rastan_direct_video_test_build_0094.bin`, SHA256 `558c88b39b359af7ee1f2cee1fa2318dde34b20ebfab7d25e25c0a18e0a819e2`
- **Summary:** User-visual / hardware observation: the Build 0094 ROM does not currently run on real Genesis hardware. This is tracked separately from Build 0094 title/attract graphics completion unless later evidence ties the failure mechanism to the same graphics pipeline issue.
- **Evidence:** Tighe report during Build 0094 documentation sync. No hardware fault PC/vector/address is recorded here.
- **Suspected area:** unknown. Potentially hardware compatibility, ROM/header/mapper behavior, timing, VDP/interrupt behavior, or another real-hardware-only constraint; no mechanism has been proven.
- **Next required task:** after the current graphics-completion task, perform a bounded real-hardware compatibility capture that records the exact device/flashcart path, visible behavior, and any available bus/exception evidence without conflating it with emulator graphics symptoms.
- **Closure condition:** Build 0094-or-later ROM runs on real Genesis hardware, or the real-hardware incompatibility mechanism is identified and fixed or explicitly tracked under a narrower successor issue.
- **[2026-07-10 Build 0154 analysis, Outcome G, no build]** Gameplay Stage 1 BG boundary re-characterised with runtime proof (see KF-040, docs/design/Andy_gameplay_pc080sn_output_analysis.md). The task's hypothesis of "untranslated raw gameplay PC080SN bulk-writers" is DISPROVEN: on Genesis Build 0153 the arcade raw column writers (BG `0x055C7A` via `0x055C68`, FG `0x0559B2`) are statically `arcade_copy` but **never execute** (0 raw-writer VDP writes; producer `0x055E68` never stores dest-cursor `0xFF10F8`). The gameplay BG cells already reach `staged_bg_buffer` (2048/2048) and are committed via the already-hooked item-page strip-blit `0x716CA` with a relocated source `0xD31C`. BUT the staged plane is a uniform `0x4000` (tile 0 + priority): `genesistan_current_scene_id` stays `0` (title), `load_scene_tiles(1)` never fires, gameplay tile patterns are not resident, and the tile LUT collapses gameplay code words to tile 0. Real boundary = **scene selection + tile-pattern residency + real-content staging** for the item-page/column gameplay path; the descriptor-hook scene detector (`plane_a`/`fg`, keyed on `a5@0x10A0/0x10A4`) is not exercised by this path and never sees a gameplay-range (`0x56A22..0x570C2`) pointer. No build (authoritative gameplay scene pointer unproven; forcing scene ID 1 / manual `load_scene_tiles(1)` forbidden). Smallest next design task defined in the analysis doc. Not closed; no duplicate.
- **[2026-07-10 Build 0154 scene-selection analysis, Outcome G, no build]** Root-caused past scene selection (see KF-041, docs/design/Andy_gameplay_scene_selection_analysis.md). Making the producer "select scene 1 naturally" CANNOT render Stage 1: the gameplay manifests, the global tile LUT, and `genesistan_scene_a0_ranges` were generated from a block-descriptor source model (`precompute_pc080sn_tile_lut.py` `GAMEPLAY_TABLE_START=0x5635E`, range `0x56A22..0x570C2`, codes `0x00AD`-family) that the **runtime never runs**, while the live producer (`0x055C5E → 0x716CA`) reads source `0xD11C`→`0xD31C` via descriptor `0x03951C`, emitting `0x04A6`-family codes. Controlled offline reproduction over the real ROM + shipped LUT: `distinct_codes=834`, `covered=1/834`, `lut_nonzero=0%`. `bg_fill` selects the tile index from the LUT (not VRAM residency), so `load_scene_tiles(1)` cannot help. Fix requires re-modeling the tile-analysis pipeline around the runtime producer source family (prove `0x03951C` walker + `0xD11C` layout, regenerate manifest+LUT to cover `0x04A6…`, wire a producer-source scene selector) — a larger redesign, so no build. Not closed; no duplicate.
- **[2026-07-10 Build 0154, Outcome F, IMPLEMENTED]** The above re-model is done (KF-041 RESOLVED for Stage 1; see docs/design/Andy_build_0154_runtime_gameplay_tile_model.md). Decoded the `0x3951C` 6-byte `{attr,src}` descriptor (56 entries → 5 blocks `0xD11C..0xF91C`, 16×64 each, 854 codes `0x04A6..0x07FB`, all patterns valid). `precompute_pc080sn_tile_lut.py` gained `collect_runtime_gameplay_sources` (structural walk) replacing the misclassified `0x5635E` gameplay model; global ROM-resident LUT now maps 854/854 runtime codes (was 1/854), gameplay manifest regenerated, peak scene 1067/1164, deterministic. `genesistan_hook_itempage_strip_blit` gained a producer-source scene-selection preamble (source ∈ `[0xD31C,0xFB1C)` & `scene_id!=1` → `load_scene_tiles(1)`; no state test, no forced ID). Build 0154 SHA `69bd306e…` size 1,580,776: Genesis MAME 2/3/0 shows `scene_id=1`, staged BG nonuniform (277 distinct), **Stage 1 outside renders (ROUND 1/READY)**; title/story/BEST 5/item page intact; GATE_PASS/boot-guard/trace clean; address-map gaps=[]/overlaps=[]. Remaining boundary: BG pixel-accuracy (column ordering/FG/scroll) + gameplay sprites/scroll/controls/collision/audio. Not closed; no duplicate.
- **[2026-07-10 Build 0155 plane-composition analysis, Outcome E, no build]** Root-caused the Build 0154 malformed Stage 1 display (see docs/design/Andy_stage1_plane_composition_analysis.md). The BG plane is PROVEN CORRECT: full 56-entry descriptor sequence decoded (blocks A/B/E/E initial), Genesis staged_bg 2048/2048 = arcade rows 0-31 (cell-verified), matching the arcade Y-scroll=0 visible window. The dominant defect is the **unpopulated PC080SN FG plane (Genesis Plane A)**: arcade fully populates it (mostly transparent 0x020 + sparse 0x41C/0x434 features, 17 codes, 5 UNMAPPED in the LUT) via a distinct 4-row-strip producer (arcade 0x0559B2, source 0x20FC, shared descriptor walker 0x3951C, a5@0x10CA column index, 0xFF sentinel + 0x10DE00 shadow); Genesis staged_fg = 76/2048. Also the BG X-scroll animates on arcade (scrollA 0x1FF-=3/frame) but is static on Genesis. No build: the 0x0559B2 FG source-column semantics are not yet decoded (stop condition), and a faithful fix needs FG-source decode + FG tiles in LUT/manifest + an FG producer hook to staged_fg_fill + scroll routing. Bounded next task defined. Not closed; no duplicate.
- **[2026-07-10 Build 0155 FG-producer analysis, no build]** The Stage 1 FG source model is now FULLY PROVEN and validated (see docs/design/Andy_stage1_fg_producer_analysis.md): the arcade FG producer 0x055968/writer 0x0559B2 builds a deterministic ROM chain — SRC[seg]=0x1691C+seg*0x22C0+stage*0x40 (stage 0), rebuild sets block PTR[seg]=0x200+ROM_word(SRC[seg]+2), code=ROM_word(PTR[seg]+colidx*2+row*8) with planerow=seg*4+row, dcol=group*4+colidx; an offline reconstruction reproduces the arcade FG plane 2048/2048 cells (100%). FG code set = 49 (48 valid patterns; 0x020 transparent -> tile 0 safe). The generator extraction (collect_runtime_gameplay_fg_tiles) is written+validated (LUT 48/49, manifest 914->962, peak 1067/1164, deterministic). BLOCKER: the intended hook boundary genesistan_hook_tilemap_plane_a (0x070248, reimplementation of arcade FG producer 0x055968) does NOT execute at Stage 1 on Genesis — the FG dest slot 0xFF10A0 / PTR table 0xFF1040 / colidx 0xFF10CA are written by PC 0x050650 and the descriptor-producer dispatch (0x055B48->0x055B68->0x070248) is dynamically bypassed (KF-040 class); an FG preamble there never fired (staged_fg stayed 76/2048). The implemented attempt (generator FG extraction + 0x070248 preamble + canonical bump) built cleanly but staged no FG and was REVERTED rather than shipped as a false FG fix. Next: locate the live FG producer/call site (trace 0x050650; find the FG analogue of the BG strip producer 0x055C68), place the proven 16x4 replay there, re-apply the ready generator extraction. Not closed; no duplicate.
- **[2026-07-10 Build 0155 IMPLEMENTED, Outcome F]** Stage 1 FG plane RESTORED (see docs/design/Andy_build_0155_stage1_fg_live_boundary.md). Live boundary found = genesistan_hook_tilemap_fg (0x0703EA), NOT 0x070248 (dynamically bypassed): the Stage 1 setup loop 0x50634 calls dispatcher 0x055B48 which (a5@0x10A8=0x80) routes to 0x0703EA per FG column; its native a5@0x10A4 is out of range (bails) while the real FG dest is a5@0x10A0=0xC08000+dcol*4. A preamble (gated scene_id==1) computes each cell from ROM (dcol=(a5@0x10A0&0x3FFC)>>2; SRC=0x16B1C+seg*0x22C0+group*4; block=ROM_word(SRC+2)+0x200; code=ROM_word(block+colidx*2+row*8)) into genesistan_hook_tilemap_fg_fill, staging the visible top 32 rows (seg 0..7). The 49-code FG family added to the global LUT + gameplay manifest (collect_runtime_gameplay_fg_tiles). Build 0155 SHA f226278f... size 1,581,124: staged_fg 76->2020/2048, visible rows 0-27 match arcade FG cells 98%, transparent 0x020 correct, Plane B unchanged, frontend intact, deterministic, GATE_PASS. Remaining: BG sky palette/content (rocky vs arcade clouds), horizontal seam, BG X-scroll, gameplay sprites. Not closed; no duplicate.
- **[2026-07-10 Build 0157, IMPLEMENTED]** PC090OJ dirty->candidate->SAT handoff fixed (see docs/design/Andy_build_0157_pc090oj_dirty_candidate_scan.md + Cody_build0157_pc090oj_candidate_dirty_handoff.md). Runtime proof (Build 0156 gameplay 2/3/0): pc090oj_object_ram=212 coded records, pc090oj_mirror_dirty=1, but candidate_bitset=0/32 (family_apply_record 0x071BB8 clears its candidate after direct-sync; vdp_prepare_sprites consumes only candidate_bitset, never mirror_dirty) -> represented=6 (stale) / sat_dirty=0. Fix: vdp_prepare_sprites folds mirror_dirty into the existing bootstrap resweep (bootstrap_pending OR mirror_dirty -> clear both + .Lpc090oj_set_all_candidates -> existing .Lpc090oj_process_candidates -> represent -> SAT; +0xC bytes, no 2nd renderer/SAT/manual). AFTER (active window F=533-534): candidate_bitset 31/32, represented 6->11, staged_sprite_sat = 11 real entries. Sprites not yet visibly appear because Rastan dies almost instantly (active window precedes plane-paint window; deferred control-flow/collision). Frontend sprites (title represented=15) + Builds 0152/0154/0155/0156 intact; GATE_PASS; deterministic. Build 0157 SHA 725c36a2... size 1,581,168. Not closed; no duplicate.
- **[2026-07-11 Build 0158, IMPLEMENTED]** Stage 1 command-source rebase (classification A; see docs/design/Andy_build_0158_command_source_rebase.md). Runtime 0x05122E `move.w 0x0010C016,%d0` read a raw arcade-WRAM literal that is ROM on Genesis (0x5553), so 0x051234 wrote 0x5553 to a5+0x137A instead of arcade's 0x00FF; the correct value was already present at mapped WRAM 0x00FF0016 (=0x00FF, written by 0x03A99A). Byte-neutral opcode_replace at 0x05102E: 30390010C016 -> 303900FF0016 (KF-036/KF-039 single-site rebase 0x10C000->0xFF0000; no NOP/destination-patch/forced-value/fallback). After: a5@0x137A=0x00FF (bad 0x5553 gone), tracks arcade. Internal state fix -- player sprite still not visible (Rastan dies ~instantly, deferred control-flow). Builds 0152/0154/0155/0156/0157 + frontend intact; GATE_PASS; deterministic; opcode_replace 135->136. Build 0158 SHA 2bf5a06f... size 1,581,168. Not closed; no duplicate.
- **[2026-07-11 Build 0159 analysis, no build]** Post-command drop/landing arcade-vs-Genesis(0158) comparison (see docs/design/Andy_build0159_post_command_drop_landing_analysis.md). Command fix INTACT (a5+0x137A=0x00FF through the window). DROP/LANDING FAITHFUL: both land at Y=0x0070, X=0x0020, ALIVE; the player does NOT die (the "dies almost instantly" is not a player-state defect in 0158). First remaining divergences (writer PCs unproven): vcorr a5+0x10DA 0x0004 vs 0x0003 (Genesis linear drop vs arcade gravity; lands rel 45 vs 33); terminal mode a5+0x10E8 0x0008 vs 0x0000; BG vertical scroll 0x00FF409A animates 0x01EC->0x0147 on Genesis vs arcade scrY=0 -> the "scrolls into black" on the 32-row plane. "No sprite" = Build 0157 deferred sprite-display timing. Classification B (fields found, writers unproven) / D aspect (visible failure = camera-scroll + sprites, not drop/landing/death). Not closed; no duplicate.
- **[2026-07-11 Build 0159 life-loss analysis, no build]** "Burns lives / reaches continue" root-caused (see docs/design/Andy_build0159_life_loss_owner.md). The 2/3/0->2/4/0->setup->2/3/0 cycle is ARCADE-FAITHFUL (arcade runs the identical cycle; named life words a5+0x1394/0x13AA never decrement on either). Genesis-specific divergence = DURATION: 2/3/0 lasts ~313 frames vs arcade ~588. Cause: player mode a5+0x10E8=0x0008 written early at 0x05400C (arcade 0x053E0C), an arcade_copy handler reached by the floor/collision dispatch 0x053FA6 (`*(a0)&0x7F==8`); once mode=0x0008, 0x051B98 writes 0xFF0002<-4 (gameplay end). Genesis reads the type-8 FLOOR/COLLISION MAP value ~275 frames earlier; SOURCE (why floor-map yields 8 early) is floor/collision map + camera scroll (unproven, out of scope; staged_scroll_y_bg=0x014B at the mode=8 write). Classification C (writer+immediate condition proven; source unproven) / D aspect (cycle faithful, not a life-counter defect). Do NOT patch arcade_copy 0x05400C. Not closed; no duplicate.
- **[2026-07-11 Build 0159 floor/collision-map origin analysis, no build]** ROOT CAUSE FOUND (see docs/design/Andy_build0159_floor_collision_map_origin.md). The floor/collision dispatch 0x53FA6 (`*(a0)&0x7F==8 -> mode=0x0008`) gets a0 from lookup 0x53C2E, which ends `moveal #0x0010DE00,a0; addal index`. 0x0010DE00 is a RAW ARCADE-WRAM literal (0x10C000+0x1E00) NOT rebased to Genesis 0x00FF1E00 (KF-039 class, same as Build 0158). Runtime proven (F=698): A0=0x0010F20A = a ROM address, *(A0)=0x1888 (&0x7F=8) -> fires; player X=0x0020 Y=0x0070 correct, cmd=0x00FF intact. ROM@0x10DE00 = garbage (3 type-8 words); WRAM@0x00FF1E00 = EMPTY (producers write the map to ROM 0x10DExx = dropped). ~9 un-rebased sites (reader 0x53C64; producers 0x55BE4/0x55C5A/0x55C7A/0x52A82/0x5A4CE/0x5A536; compares 0x414E8/0x45F52). camY(a5@0x10B0)=0x014B (= extra BG vertical scroll) shifts index but is secondary. Classification A (cause proven+bounded); fix = coordinated multi-site collision-buffer rebase 0x0010DE00->0x00FF1E00 (NOT a reader-only patch - that reads empty WRAM), deferred to a dedicated build. Do NOT patch faithful handler 0x5400C. Not closed; no duplicate.
- **[2026-07-11 Build 0159 collision-buffer rebase feasibility, STOP no build]** The coordinated rebase was scoped and its site set fully verified (9 sites, one 0x2000-byte buffer [0x10DE00,0x10FE00); readers 0x53C64/0x5A4CE, producers 0x55BE4/0x55C5A/0x55C7A, converters 0x52A82/0x5A536, compares 0x414E8/0x45F52; all byte-neutral; target WRAM 0xFF1E00..0xFF3E00 free). But the PRE-BUILD RUNTIME GATE FAILED: write-tap on 0x10DE00..0x10FDFF over a full run = ZERO writes, and producer stores 0x55BEC/0x55C62/0x55C82 NEVER execute -> the collision-map PRODUCER PIPELINE IS DEAD on Genesis (KF-040 class). Corrects prior 'producers write-to-ROM-dropped': producers never run; reader consumes static ROM graphics data. A literal rebase would read an EMPTY 0x00FF1E00 (type-0 = no collision) -> removes collision entirely -> UNSAFE. Classification C (unsafe) + D (prior mechanism corrected). STOP, no build; no opcode_replace added (count stays 136). Real fix = make the producer pipeline run/populate on Genesis, deferred. Not closed; no duplicate. (docs/design/Andy_build0159_collision_buffer_rebase.md)
- **[2026-07-11 Build 0159 collision producer pipeline owner, no build]** OWNER PROVEN (docs/design/Andy_build0159_collision_producer_pipeline_owner.md). The arcade PC080SN tilemap-population routine IS the collision-map producer (double duty: VDP tiles + collision cells at 0x10DE00). Build 0154 (genesistan_hook_tilemap_plane_a @arcade 0x55968) and Build 0155 (genesistan_hook_tilemap_fg @arcade 0x55990) opcode_replaced those routines with `jsr <staging hook> + NOPs` that emit only tiles, dropping the collision-cell writes; producer subroutines 0x559B2/0x55A14 orphaned (Genesis 0x55BB2/0x55C14 no callers). Arcade proof: 8192 buffer writes F6..306 from 0x03AF02 (startup zeroing loop) + 0x0559F0 (BG tilemap producer store 0x559EC via dispatch 0x55948, a5@0x10A8==0). Genesis: dispatch 0x55B48 runs but a5@0x10A8=0x80 -> FG hook branch; neither hook emits collision cells; startup zeroing loop (rebased) zeros 0x00FF1E00 (all-zero). KF-040/KF-041 instance. Classification D: producer intentionally dead; fix = extend the Genesis tilemap staging hook(s) to also emit collision cells into 0x00FF1E00, THEN the coordinated 9-site buffer rebase (reader-rebase alone unsafe). Tilemap-staging/collision build, deferred. Not closed; no duplicate.
- **[2026-07-11 Build 0159 tilemap staging collision producer, STOP C, no build]** Attempted the converged fix (extend the tilemap hook to emit collision cells). Descriptor source is POPULATED on Genesis (0xFF1040 ptrs, 0xFF1080=0x0003; descriptor[0]@0x1200: +20..+30=0x0020, +32=0x00FF, +34=0x0000; real collision codes 0x20/0x00, never type-8). But a safe build is BLOCKED: (a) producer-variant/state divergence -- arcade builds Stage-1 collision via the BG producer (a5@0x10A8==0, BG store 0x0559F0 x4096) while Genesis runs the FG hook (a5@0x10A8=0x80 x80); emitting from FG with FG semantics (solid-above marker + order-flip) would build a different map than the arcade BG map; (b) the FG hook uses the FG_SRC seg/row model, not the arcade 16-descriptor strip/col collision walk (a2+20+strip*2+col*8 or a2+34), so bridging is unvalidated. Building now would guess collision values -> risk a wrong map. Classification C, STOP no build (opcode_replace stays 136). Next: resolve the a5@0x10A8 arcade-0/Genesis-0x80 producer-selection divergence, validate the descriptor-walk offline, then port the collision half + coordinated 9-site rebase. Not closed; no duplicate. (docs/design/Andy_build0159_tilemap_staging_collision_producer.md)
- **[2026-07-11 Build 0159 collision producer selection, ROOT CAUSE, no build]** RESOLVED the a5@0x10A8 divergence (docs/design/Andy_build0159_collision_producer_selection.md). a5@0x10A8 (Genesis 0xFF10A8) is the PC080SN tilemap PASS SELECTOR (dispatch 0x55948: ==0 BG producer, !=0 FG). Value = *(a5@0x10C6), set at arcade 0x503CE: d0 = #0x00050F6B (seq-table base) + index. BUG = postpatch relocation INCONSISTENCY: sibling `moveal #0x00050EE0,a1` at 0x503BC was relocated (->0x000510E0) but `movel #0x00050F6B,d0` at 0x503CE was NOT (data-reg literal, same class as Build 0158). ROM proof: Genesis[0x050F6B]=0x80 vs [0x05116B]=0x00; arcade[0x050F6B]=0x00. So Genesis a5@0x10A8=0x80 (FG) vs arcade 0x00 (BG) -- a BUG, not arcade-equivalent. Correct producer = BG. STRONGLY implicated in the visible FG-tile issue (wrong pass; Build 0155 accommodated the bug). Classification C + D reframe: the boundary is a pointer-relocation/pass-selection bug upstream of collision emission. NEXT: dedicated byte-neutral relocation build at 0x503CE (203C00050F6B->203C0005116B), rendering-regressed (Build 0154/0155), re-observe a5@0x10A8=0x00 + visible FG, THEN collision emit + 9-site rebase. STOP no build; opcode_replace stays 136. Not closed; no duplicate.
- **[2026-07-11 Build 0159 PASS-SELECTOR RELOCATION, BUILT]** Implemented the byte-neutral relocation (docs/design/Andy_build0159_pass_selector_relocation.md). opcode_replace at 0x0503CE 203C00050F6B->203C0005116B (pass-seq table base literal +0x200; sibling 0x503BC already relocated). Build 0159 SHA 14138b82..., counter 159, opcode_replace 137, byte-neutral, GATE_PASS. RESULT (deterministic): desc-rebuild reads 0x00 from the relocated table -> a5@0x10A8=0x0000; dispatch 100% BG (x83), no 0x80 -> arcade-equivalent (arcade always 0x0000). BG staging intact (2048); FRONTEND intact (title represented=15, staged_bg/fg=560/66 identical to 0158); command 0x00FF intact; routes 0156/0152/0157 intact. EXPECTED PASS-SELECTION IMPACT: gameplay FG staging dropped 2020->12 (Build 0155 FG hook was FG-branch/bug-triggered, now bypassed) -> FOLLOW-UP: re-anchor Build 0155 FG_SRC staging to the BG pass. Collision NOT fixed here (WRAM 0xFF1E00 empty, reader raw 0x10DE00, early mode=0x0008 F=679) -> collision emit + 9-site rebase still pending. KF-042 added. Not closed; no duplicate.
- **[2026-07-11 Build 0160 FG_SRC reattachment point analysis, no build]** Located where Build 0155's gameplay FG_SRC staging should reattach after Build 0159 fixed the selector (docs/design/Andy_build0160_fg_src_reattachment_point.md). Old attach = genesistan_hook_tilemap_fg (FG branch, fired only via the a5@0x10A8=0x80 bug); Build 0159 -> BG branch (genesistan_hook_tilemap_plane_a) 100%, FG hook not called (gameplay staged_fg=12 vs BG 2048). The FG_SRC block's ONLY external input is a5@0x10A0 (masked -> dcol), which the BG hook already reads; block is self-contained (constants/ROM/fg_fill, register-preserving), reads not writes a5@0x10A0, does not touch a5@0x10A8. Proposed: fold FG_SRC into genesistan_hook_tilemap_plane_a gated by SCENE_GAMEPLAY_ID (additive, preserves selector + BG staging). Classification C: input proven, but the BG hook's a5@0x10A0 progression differs from the old FG-branch context so column-mapping correctness is unproven (pre-0159 FG was not visibly correct either) -> defer to implementation build with runtime+visual column-mapping validation. Not closed; no duplicate.
- **[2026-07-11 Build 0160 FG_SRC fold into corrected BG pass, BUILT]** Implemented (docs/design/Andy_build0160_fg_src_fold_into_bg_pass.md). Extracted the FG_SRC gameplay body into movem-wrapped genesistan_stage_fg_src_column; added gated `bsr` at genesistan_hook_tilemap_plane_a entry (SCENE_GAMEPLAY_ID, reuse a5@0x10A0); deduped genesistan_hook_tilemap_fg. tilemap_hooks.s only; opcode_replace stays 137; coverage 0x182070->0x182090. Build 0160 SHA e9243ff028cdcd8f3776a51ffa54ea8438f1489bca61fd607bff0c268983e697, size 1,581,200, counter 160, GATE_PASS. RESULT (deterministic): selector a5@0x10A8=0x0000 x83 (0159 preserved, 0x505CE=movel #0x0005116B); gameplay staged_fg 12->2016 (~0155's 2020); staged_bg 2048 intact; 63/64-column coverage, varying cells (non-degenerate, no stale/one-column overwrite); frontend identical (represented=15, staged_bg/fg 560/66); command 0x00FF. Collision unchanged (WRAM 0xFF1E00 empty, reader raw 0x10DE00; mode=0x0008 did not fire in 820f window, timing-shifted; deferred). Remaining OPEN-017: visible-FG pixel check, collision producer/emit + 9-site rebase, player/Rastan sprite absence. Classification A. Not closed; no duplicate.
- **[2026-07-11 Build 0161 gameplay FG/sprite palette CRAM ownership, STOP B, no build]** Audited the gameplay palette/CRAM path (docs/design/Andy_build0161_gameplay_palette_cram_ownership.md). Commit (vdp_commit_palette) RUNS (palette_dirty set 124x -> DMA staged_palette_words 0xFF609E -> CRAM); CRAM==staged. At gameplay F=560: line0/1=BLACK, line2=populated (bank48), line3=nz1 (08AE only, bank51). BG cells -> line2 (populated) -> BG appears; FG cells -> line3 (FG_PLANE_ATTR_HI=0x00030000) = BLACK -> FG invisible; sprites/Rastan also line3 -> black. Arcade banks 0/1/48/51 ALL populated (bank51=15 colors) but only Genesis line2 survived. LINE 3 NEVER POPULATED (nz 0->1 at F195, constant) -> missing/non-running bank51->line3 producer in gameplay (hook_59ad4 writes only line3[0] from src 0x059B38; hook_3ba64 bank51 branch didn't fire). Confirmed adjacent bug: hook_59ad4 `move.w d1,(a1)+` compacts vs arcade positional `(a1)`+unconditional `addq #2,a1` -- real defect but not proven the cause (line never filled, not scrambled). Classification B (line black + usage proven; producer owner unproven), STOP no build. Next: prove the arcade bank-51 gameplay producer + Genesis hook, then fix; no forced colors. Not closed; no duplicate.
- **[2026-07-11 Build 0161 bank-51 palette producer owner finish attempt, STOP C, no build]** OWNER FOUND (docs/design/Andy_build0161_gameplay_palette_cram_ownership.md sec 20). Arcade full bank-51 load = generic memcpy 0x3A2D0 (movew (a0)+,(a1)+) copying WRAM 0x10D662 -> palette RAM 0x200660 (15 colors). On Genesis 0x3A2D0 is unhooked -> writes unmapped 0x200660 -> dropped. The hooked 0x3A2D0 caller hook_45dae (arcade 0x045DB8, 64-word chunk) gates on a1==0x200000 (bank-0 chunk only) -> rejects the sprite-bank chunk (a1=0x200600, banks 48-51) and writes staged sequentially from line-0 base (no bank->line offset). Fix = add/extend a hook to convert the sprite-bank chunk into staged lines 2,3 at correct offsets (48->line2, 51->line3), committed by vdp_commit_palette; validate line3 15 colors; no forced colors; no frontend regression. Classification C (owner found; fix not trivially bounded this VERY-LOW-budget session), STOP no build; counter 160, opcode_replace 137. Not closed; no duplicate.
- **[2026-07-12 Build 0161 sprite-bank palette chunk routing, STOP B, build REVERTED]** Implemented+built the routing fix (extend hook_45dae for a1==0x200600 -> bank 51 -> staged line 3; opcode_replace at 0x045DEE) but REVERTED it as a NO-OP (docs/design/Andy_build0161_sprite_bank_palette_chunk_routing.md). The routing is correct (0x045FEE now would jsr the hook), but line 3 stayed black (08AE 0000...) because the hook's sprite branch read a ZERO SOURCE: Genesis 0xFF1600 (=arcade 0x10D600 sprite-palette source) is ALL ZERO at gameplay, while the arcade 0x10D600 is populated (bank51 0842 739C 429E...). So the DEEPER blocker is that the arcade sprite-palette source producer (fills 0x10D600) does not reach Genesis 0xFF1600 (KF-039 raw-WRAM-literal / unhooked-producer class). Build reverted (counter reset 160, opcode_replace back to 137, coverage 0x182090); accepted stays Build 0160. Classification B. NEXT: rebase/hook the 0x10D600 source producer to Genesis 0xFF1600 FIRST, then re-apply the routing. Not closed; no duplicate.
- **[2026-07-12 Build 0161 sprite-palette source population, PASSING CANDIDATE]** BUILD-VERIFIED (docs/design/Andy_build0161_sprite_palette_source_population.md). Root (KF-043): arcade 0x3BA64 writes bank 48 to palette RAM 0x200600 (->Genesis line 2) but bank 51 ONLY to the sprite-palette source buffer 0x10D660 (a5-rel=Genesis 0xFF1660), then memcpy->0x200600 (unmapped, dropped); hook_3ba64 only stages the 0x200000 palette-RAM writes and skipped the bank-51 source-buffer write -> line 3 black. FIX (palette_hooks.s only, no opcode_replace): stage a0 in [0xFF1660,0xFF1680) directly to staged line 3 in hook_3ba64. RESULT (deterministic): line 3 nz 1->15 (faithful bank-51 colors), line 2/lines0-1/selector/FG(2016)/BG(2048)/command/frontend all intact, GATE_PASS. Build 0161 SHA 79c2c016..., counter 161, opcode_replace 137, coverage 0x1820A4. PASSING CANDIDATE preserved; accepted stays Build 0160 pending Tighe visual acceptance. Remaining: visible-pixel confirmation, collision producer, sprite geometry. Not closed; no duplicate.
- **[2026-07-12 Build 0162 gameplay palette lines 0/1 population, PASSING CANDIDATE]** BUILD-VERIFIED (docs/design/Andy_gameplay_palette_lines_0_1_population.md). Root: arcade banks 0/1 are written directly to palette RAM 0x200000 (0x3BA64) and staged by hook_3ba64 -> Genesis lines 0/1 at F=14, but hook_45dae (F=210) ZEROED them by copying the empty sprite-palette source buffer 0xFF1600 (KF-043) -> black clobber; banks 0/1 (written once) never re-populated. FIX (palette_hooks.s only, no opcode_replace): hook_45dae skips ZERO converted values (positional advance) so the empty source can't clobber. RESULT (deterministic): line 0 nz 0->15 (faithful bank0: 7BDE->0EEE), line 1 nz 0->14; lines 2/3 preserved (nz=15); selector/FG/BG/command/frontend intact; GATE_PASS. All four gameplay CRAM lines now populated. Build 0162 SHA 7bcb3179..., counter 162, opcode_replace 137, coverage 0x1820AC. PASSING CANDIDATE preserved (0161 + 0162); accepted stays 0160 pending Tighe visual acceptance. Not closed; no duplicate.
- **[2026-07-12 Gameplay sprite path ownership analysis, STOP C, no build]** Compared title (works) vs gameplay (flickering dots) PC090OJ/SAT (docs/design/Andy_gameplay_sprite_path_ownership.md). USER RAW-BYPASS HYPOTHESIS REFUTED: no arcade PC090OJ 0xD00000 writes during gameplay; object_ram written only by Genesis hooks (484 writes/frame) and HAS 24 drawable gameplay records (codes 0x2A/0x3E8-0x3EF etc.). But represented=6 (F560)/10 (F533) of 24, and the staged-SAT link chain is CORRUPT (06 06 03 04 05 06 07 08 0D 0A 0B 0C 0D 0E 00 00; duplicate/skipping links, changing frame-to-frame) -> flickering garbage. First break = PC090OJ represent->SAT-link engine (incremental linked-list sync_record_from_mirror/set_link/head-insert), not a raw bypass. Palette line 2 populated (not a palette cause). Classification C (deep engine defect, not trivially bounded), STOP no build. Next: dedicated analysis of the SAT-link/represent management. Not closed; no duplicate.
- **[2026-07-10 Build 0158 analysis, no build]** Cody performed the player death/fall boundary check and STOPPED without implementation (see docs/design/Cody_player_death_fall_analysis.md). Tiny SAT sanity result: **A** — Build 0157 has plausible early gameplay staged SAT entries (frames 533-534, represented 10->11, sat_dirty=1, sane Y/X/link/attr/tile words), so SAT format is not the immediate stop gate. However, the required arcade-vs-Genesis player-state timeline is absent: no current artifact identifies the player object structure in both arcade and Genesis, and no current artifact identifies the collision/floor routine PC or lookup inputs/outputs. Therefore the first death/fall divergence cannot be classified and the state-causality rule cannot be answered. No Build 0158 produced; next bounded evidence task is a short arcade-vs-Genesis Stage 1 trace that captures player object, camera/scroll, and collision/floor inputs/outputs through first life-loss. Not closed; no duplicate.

---

## OPEN-018 — Route raw copied PC080SN writes through Genesis staging

- **Status:** OPEN (immediate-absolute portion implemented/validated in Build 0107; high-score producer-loop instance implemented/validated in Builds 0111/0112; register-absolute 0xC08C62 in Build 0152 and sibling 0xC08C66 in Build 0156; other raw-write shapes remain)
- **Priority:** HIGH (strict-emulator / real-hardware crash class)
- **[2026-07-10 Build 0156]** Register-absolute sibling routed: the raw FG single-digit writer at runtime 0x03D24C (arcade 0x03D04C) `move.w %d1, 0x00C08C66` (d1 = digit tile 0x30..0x39) — sibling of Build 0152's 0x03A72A/0xC08C62 — is now routed via byte-neutral opcode_replace 33C100C08C66 -> jsr genesistan_hook_inline_fg_write_3d04c -> genesistan_hook_tilemap_fg_fill -> staged_fg -> existing FG VBlank commit. User report proved it blocks (BlastEm strict-freeze at write address C08C66 during Build 0155 gameplay). Validation: 0x3D24C now jsr 0x708C8; runtime 0 raw C08C66 writes; deterministic; Build 0155 FG + Build 0152 C08C62 intact; GATE_PASS; opcode_replace 134->135, coverage 0x182044->0x182064. Build 0156 SHA 03c6e8aa... size 1,581,156. See docs/design/Andy_build_0156_c08c66_fg_digit_route.md. Remaining raw-write shapes (producer-loop 0x3B3CC/0x3B7F6/0x3B7F8) still open.
- **Build 0107 status (2026-06-27):** The immediate-absolute Class A portion is implemented and validated. Build 0107 (`dist/rastan-direct/rastan_direct_video_test_build_0107.bin`, SHA256 `4b4a588b1da2ccec6b31cac781bd53627993eaa6170ec013da56f349c99ef1e3`) routes four immediate-absolute raw FG writes (`0x3ACEA`, `0x3A550`, `0x3A8FE`, `0x3A908`) via byte-neutral 8-byte `jsr abs.l + nop` trampolines → `genesistan_hook_tilemap_fg_fill` (live LUT → FG staging → dirty → VBlank commit). Invariants: `opcode_replace 98→102`, `total_genesis_bytes_covered 0x17CD68→0x17CDD4` (helper growth `0x6C`), attr gate passed for all four. The **story-page comma crash is fixed on BlastEm and real Genesis and the comma renders** (`0x3ACEA`); `0x3A908` staging + `%d0` preservation runtime-proven; `0x3A550`/`0x3A8FE` are structurally covered by the same mechanism but were not runtime-reached in the sampled validation windows (no overclaim of visual proof for those two). **Do not mark OPEN-018 globally closed** — the register-absolute (`0x3A92A`, `0x3D24C`) and producer-loop (`0x3B3CC`, `0x3B7F6`, `0x3B7F8`) raw-write shapes remain (did NOT block the validated story-page path; relevant to full raw-write closure / other screens). See `docs/design/Andy_build_0107_validation_and_class_b_remaining_status.md`. The TAITO/paren visual gaps are NOT under OPEN-018 — they are Class B (KF-033 / OPEN-019 / OPEN-020).
- **Build 0111/0112 status (2026-06-28):** The high-score FG producer-loop instance at `runtime_genesis_pc 0x0003C5FE` is routed through `genesistan_hook_highscore_fg_producer` and Genesis FG staging. Build 0111 proved the old raw body PCs `0x03C62A/0x03C646/0x03C64A` no longer fired and 15 logical high-score cells staged, but used the wrong source base. Build 0112 corrected the source base to mapped Genesis WRAM `0x00FF0000`, proved NAME bytes `COB/THS/YAG/TKG/YTN` were read from `0x00FF0157..0x00FF0165`, and proved the old bad literal source range `0x0010C1BF..0x0010C1CD` was no longer read. This closes the known high-score `0x03C5FE` raw-write/source-base sub-arc, but **does not close OPEN-018 globally**; other raw PC080SN/PC090OJ write shapes may remain.
- **Build 0152 status (2026-07-09):** The proven gameplay-entry register-absolute FG write at `runtime_genesis_pc 0x0003A92A` (`arcade_pc 0x0003A72A`, `move.w d0,0x00C08C62`) is routed through `genesistan_hook_inline_fg_write_3a92a -> genesistan_hook_tilemap_fg_fill`. Original arcade runtime evidence showed this site writing dynamic ASCII `0x0031` from `A5+0x0117 | 0x0030` into the PC080SN FG cell during state `2/2/6`; Build 0152 static/runtime validation shows the site is now a patched-site `jsr`, the wrapper receives live `D0=0x31`, and the armed FG-fill store composes/stages the cell at offset `0x0630` with base `0x00FF509E`. The adjacent register-absolute writer `runtime_genesis_pc 0x0003D24C` (`arcade_pc 0x0003D04C`, `move.w d1,0x00C08C66`) remains `arcade_copy` and is **not patched** in Build 0152 because same-route arcade proof was not established. Build 0152 ROM SHA256 `3d805331815588576a3fdeef732a7b094f3c15997b66c76830827adfc2f35214`.
- **Discovered by:** Cody (Build 0106 c09172 writer watchpoint) / canonicalized by Andy
- **Observed in build/artifact:** Build 0106, `dist/rastan-direct/rastan_direct_video_test_build_0106.bin`, SHA256 `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`
- **Summary:** `runtime_genesis_pc 0x0003ACEA` (= `arcade_pc 0x0003AAEA`, `arcade_copy`) executes `move.w #0x2749, 0x00C09172` — a raw copied PC080SN FG write (story comma/special glyph, FG row17/col28) that bypasses Genesis staging. Class A (KF-032). Tile `0x2749` is already mapped (slot `0x0039`); the defect is the raw write path into VDP-mirror space.
- **Evidence:** docs/design/Cody_build_0106_c09172_writer_watchpoint.md; docs/design/Cody_build_0106_correction_taito_arcade_intent_paren_lut.md; address_map.json segment `0x03AB20..0x03AD00`.
- **Suspected area:** translated-arcade-write routing; same class as the Build 0106 scroll-RAM raw fill (0x3AF3C).
- **Next required task:** continue the remaining raw-write inventory/routing work for non-closed raw PC080SN/PC090OJ shapes; do NOT NOP/suppress. Treat the story-comma immediate write and high-score `0x03C5FE` producer as closed sub-cases, not as global closure.
- **Closure condition:** all confirmed raw copied PC080SN/PC090OJ write classes are routed through the appropriate Genesis staging path and no strict-target HV/VDP-mirror fatal remains for those classes.

---

## OPEN-019 — Repair low-code FG glyph/symbol LUT coverage

- **Status:** OPEN
- **Priority:** MEDIUM-HIGH
- **Discovered by:** Cody (Build 0106 paren/TAITO evidence) / canonicalized by Andy
- **Observed in build/artifact:** Build 0106, SHA256 `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`
- **Summary:** Routed FG glyph cells stage blank because the tile LUT maps low arcade glyph/symbol codes to slot `0x0000` (KF-033). Confirmed-failing codes: `0x0022, 0x0027, 0x0028, 0x0029, 0x002C, 0x003F` (symptoms: missing `INSERT COIN(S)` parens; four missing small red TAITO cells).
- **Design constraints:**
  - `0x0028/0x0029` are byte-identical to preloaded aliases `0x2747/0x2748` (slots `0x0037/0x0038`) → likely LUT-entry-only fix (pattern already in VRAM).
  - `0x0022/0x0027/0x002C/0x003F` are NOT byte-identical to their mapped tiles and have their own nonblank ROM patterns → may need preload/slot coverage **plus** LUT entries; do not assume LUT-only.
  - Root is the generator `tools/translation/precompute_pc080sn_tile_lut.py` (`TEXT_SPECIAL_GLYPH_MAP` registers only mapped tiles). Fix should avoid one-off whack-a-mole; see OPEN-020.
- **Evidence:** docs/design/Cody_build_0106_correction_taito_arcade_intent_paren_lut.md; docs/design/Cody_build_0106_taito_magenta_cell_arcade_intent.md; docs/design/Andy_build_0106_fixed_tile_findings_canonicalization.md; LUT/preload binaries inspected.
- **Next required task:** decide the fix shape (LUT-only for parens vs preload+LUT for TAITO codes) per OPEN-020 audit; repair generator/LUT so routed low-code glyphs stage their correct pattern.
- **Closure condition:** the confirmed-failing low-code FG glyphs render correctly, with the generator updated so the gap does not recur.

---

## OPEN-020 — Comprehensive low-code FG glyph/symbol coverage audit

- **Status:** OPEN
- **Priority:** MEDIUM
- **Discovered by:** Andy (Build 0106 canonicalization, Task 1)
- **Observed in build/artifact:** Build 0106, SHA256 `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`
- **Summary:** Six low-code FG gaps were found by visible symptom; the root mechanism (KF-033/KF-035) implicates the full set of 8 `TEXT_SPECIAL_GLYPH_MAP` keys (`0x0021,0x0022,0x0027,0x0028,0x0029,0x002C,0x002D,0x003F`), of which `0x0021 ('!')` and `0x002D ('-')` are latent (LUT=0, not yet observed failing). Audit the low-code FG glyph/symbol range against arcade title/story tilemap intent and existing LUT/preload coverage before finalizing OPEN-019, to avoid whack-a-mole.
- **Method (per KF-034/KF-035):** derive "what should render" from arcade tilemap/runtime staged cell codes (not Genesis LUT/staging results); cross-check VRAM/pattern table, rendered output, writer evidence; use two-context coordinate reconciliation with anchors.
- **Evidence:** docs/design/Andy_build_0106_fixed_tile_findings_canonicalization.md (§3a, §4).
- **Closure condition:** a complete inventory of low-code FG glyph/symbol coverage gaps (LUT-only vs preload+LUT) is produced and fed into the OPEN-019 fix.

---


## OPEN-021 — High-score SCORE/ROUND columns still need arcade-anchored source provenance

- **Status:** OPEN
- **Priority:** MEDIUM
- **Discovered by:** Cody (Build 0112 high-score NAME source-base fix follow-up)
- **Observed in build/artifact:** Build 0112, `dist/rastan-direct/rastan_direct_video_test_build_0112.bin`, SHA256 `024241b2378dba68102637c368bc92d5edc41b2b30776363a96144146dfe215d`
- **Summary:** Build 0112 proves the high-score NAME column is seeded and correctly read from mapped Genesis WRAM (`0x00FF0157..0x00FF0165 = COB/THS/YAG/TKG/YTN`). That disproves the earlier whole-table-unseeded assumption. The SCORE/ROUND columns remain zero/blank and need their own arcade-anchored source/destination audit rather than piggybacking on the NAME fix.
- **Evidence:** docs/design/Cody_highscore_name_column_source_audit_build_0111.md; docs/design/Cody_build_0112_highscore_name_source_base_fix.md
- **Next required task:** identify the original arcade runtime SCORE/ROUND source addresses, map them to Genesis WRAM through the authoritative mapping, and compare Build 0112 reads/staging against original arcade runtime state.
- **Closure condition:** SCORE/ROUND source provenance is established and either proven correct or fixed with runtime evidence.

---

## OPEN-022 — C00828 strict-target freeze on BG raw write around high-score exit

- **Status:** OPEN
- **Priority:** HIGH (strict-emulator / real-hardware crash class)
- **Discovered by:** Tighe/Cody during post-Build 0112 high-score progression testing
- **Observed in build/artifact:** Build 0112 follow-up context; exact producing build/evidence path to be recorded by the next diagnostic
- **Summary:** After the high-score path progresses further, a strict-target freeze occurs on a raw write to `HW_ADDRESS 0x00C00828` (BG PC080SN page/window region). This is the BG-side sibling of the KF-032 raw copied PC080SN write class and appears after the high-score producer route/source-base fixes, not before them.
- **Evidence:** AGENTS_LOG Build 0112 follow-up context; formal writer-PC evidence still needed.
- **Next required task:** capture the writing `runtime_genesis_pc`, map it via `build/rastan-direct/address_map.json`, classify the write shape, and route the arcade intent through BG staging if confirmed.
- **Closure condition:** the `0x00C00828` raw write is either routed correctly or disproven as the strict-target freeze source with debugger-side evidence.

---

## OPEN-023 — Window layer path remains unimplemented / garbage

- **Status:** OPEN
- **Priority:** MEDIUM
- **Discovered by:** Long-running title/attract visual bring-up evidence
- **Observed in build/artifact:** Current rastan-direct builds through Build 0112
- **Summary:** The Genesis window-layer path is not yet implemented as a faithful translation target. Any window-layer visible output or garbage should not be treated as proof that the Plane A/Plane B title/high-score paths are correct.
- **Evidence:** Current architecture notes and Build 0094+ visual/debug captures; no dedicated closure evidence yet.
- **Next required task:** perform an arcade-intent and Genesis mapping audit for any screen that actually requires the Genesis Window layer, separate from FG/Plane-A text work.
- **Closure condition:** required window-layer arcade intent is identified and translated, or the layer is proven unused for the active screen set.

---

## OPEN-024 — PC090OJ sprite subsystem remains incomplete / garbage

- **Status:** OPEN
- **Priority:** MEDIUM-HIGH
- **Discovered by:** Long-running rendering bring-up evidence
- **Observed in build/artifact:** Current rastan-direct builds through Build 0112
- **Summary:** PC090OJ sprite output remains incomplete; sprite garbage/missing sprites should not be conflated with PC080SN BG/FG tilemap fixes. This is broader than the older high-bank palette mapping thread.
- **Evidence:** KF-026 and current Build 0094+ visual/debug captures; no final sprite-path validation yet.
- **Next required task:** audit PC090OJ runtime writes, sprite table staging, tile-cache/palette use, and VDP SAT commit against original arcade runtime state.
- **Build 0146 HIGH-SCORE "GH" FIX (2026-07-08, Outcome B, retained):** corrected `genesistan_pc090oj_hook_target_3b902` to faithfully translate arcade `0x03B902` — clear path (d1==0) copies the 5-record table at `0x3B984` (Genesis `0x3BB84`) into records 17-21 via the existing `genesistan_pc090oj_hook_target_3b930`; fill path (d1!=0) writes byte `d1` to the Y-high byte (offset 2) of records 17-21 via `mirror_write_byte` (matching arcade `move.b %d1,2(%a1)` x5). The helper no longer writes records 0-4. ROM `dist/rastan-direct/rastan_direct_video_test_build_0146.bin` SHA `3edcf345d1c6e547b993f72b29ab9d80f7fa58823ad992de962391a5ce8a416b`. Runtime-verified: zero code-1 writes to record 4; final record 4 = `0000 0000 003B 0088` (GH) on slot 0; new fill (pc 0x71A30) writes only Y-high bytes of records 17-21; `HIGH SCORE` renders complete on the title; item screen (bank-51 sprites + palette, represented 22) unchanged. **Remaining:** the separate state-dependent missing `UP` in `2UP` (not investigated). Evidence: `docs/design/Andy_build_0146_pc090oj_3b902_fix.md`.
- **Missing HIGH-SCORE "GH" root cause (2026-07-08, analysis):** the title/header `HIGH SCORE` renders as `HI SCORE` because `genesistan_pc090oj_hook_target_3b902` (arcade `0x03B902`, genesis_rom_offset `0x03BB02`, patched_site) fills PC090OJ mirror records **0-4** with `(word0=0,Y=0,code=1,X=0)`, whereas the arcade `0x03B902` targets records **17-21** (`HW_ADDRESS 0x00D00088`, byte-2 only). The helper's wrong record base (0 vs 17) overwrites record 4 — the "GH" glyph the `0x03B930` producer had correctly written (arcade record 4 = `code 0x3B, X 0x88`, never code 1). Records 5-8 (HI/ S/CO/RE) are outside 0-4 and survive. Proven by emit-helper caller capture (ra `0x00071B14`) + arcade/Genesis record-4 watchpoints + arcade original bytes. **Next action:** correct the `genesistan_pc090oj_hook_target_3b902` fill/clear loop record range (target 17-21 / `0xD00088`, not 0-4). Evidence: `docs/design/Andy_missing_gh_high_score_header.md`.
- **Build 0142 status (2026-07-07):** ADVANCED, not closed. The PC090OJ renderer was re-architected to a retained record-identity translation (record_to_slot LUT, represented/waiting/used-slot bitmaps, sparse stable SAT slots with slot-0 head invariant, local link splice, bounded coalesced tile-DMA worklist, candidate-driven compatibility, one converted semantic family) — design `docs/design/Andy_pc090oj_semantic_helper_families_build0142.md` §§9-C/9-D/9-E, implementation/evidence `docs/implementation/Andy_pc090oj_retained_identity_build_0142.md`, ROM `dist/rastan-direct/rastan_direct_video_test_build_0142.bin` SHA256 `f4c4234910fd56c739f874ad2a176ec447949f4e492b6526d37064f7dd23f245`. Native evidence proves the renderer emits **exactly the mirror's drawable set** (independently-decoded drawable == represented, 22/22 at state 2/2/6) with correct transformed Y/X + slot-keyed tile index (0 mismatch), an ascending-priority link chain visiting each represented record once, all structural invariants passing, and stable DISPLAY_OFF cut to 994 cyc. Remaining OPEN-024 work: visual confirmation (Tighe BlastEm/Exodus) and the pre-existing palette (OPEN-006) / position defects, which this architecture change does not touch. Gameplay sprite-decay `0x5607C` recommended as the next semantic-family conversion (Build 0143).
- **Closure condition:** sprites render from the translated PC090OJ path with correct tile/palette/position behavior, or a narrower set of remaining sprite defects is split into dedicated issues.

---

## OPEN-025 — JSON-based arcade RAM seeding architecture for default tables

- **Status:** OPEN (future architecture note)
- **Priority:** LOW-MEDIUM
- **Discovered by:** Build 0111/0112 high-score source-base work
- **Observed in build/artifact:** Current rastan-direct builds through Build 0112
- **Summary:** The high-score NAME audit showed that arcade work-RAM default/seed data can be semantically important and must be compared against original arcade runtime state. If future screens require default arcade RAM tables that are not created by translated runtime order, the project should prefer a declarative JSON/source-of-truth seeding mechanism over ad hoc helper literals.
- **Evidence:** docs/design/Cody_highscore_name_column_source_audit_build_0111.md; docs/design/Cody_build_0112_highscore_name_source_base_fix.md
- **Next required task:** only if a real missing-seed defect is proven, design a declarative seed mechanism that records original arcade source, target mapped WRAM address, timing, and validation evidence.
- **Closure condition:** either no such RAM seed architecture is needed after audits, or a declarative mechanism exists and covers proven seed requirements.

---

## Prompt Template Requirement (mandatory for all Cody/Andy prompts)

Before work:
1. Read `OPEN_ISSUES.md`.
2. Read `CLOSED_ISSUES.md`.
3. Identify which open issues this task touches.
4. Do not reopen closed issues unless new evidence directly contradicts the closure note.

During work:
- If a new unresolved issue is discovered, add it to `OPEN_ISSUES.md` BEFORE final response.
- If an issue is resolved, move it from `OPEN_ISSUES.md` to `CLOSED_ISSUES.md` with full closure metadata (closing build, evidence, closure note).
- Do not delete issue history.
- Do not close an issue without evidence and closure condition citation.

Final response must include "Open/Closed Issues Impact" section with:
- Open issues touched: [IDs or NONE]
- New issues opened: [IDs or NONE]
- Issues closed: [IDs or NONE]
- Issues intentionally deferred: [IDs or NONE]
