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
- **Current unresolved graphics symptoms:** sword/logo artwork absent; TAITO logo incomplete/missing tiles; stale text between attract states; dot rows on scrolling/item page; no complete title/game graphics acceptance yet.
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

---

## OPEN-018 — Route raw copied PC080SN story-comma write through staging

- **Status:** OPEN (immediate-absolute portion IMPLEMENTED & VALIDATED in Build 0107; register-absolute + producer-loop raw-write shapes remain)
- **Priority:** HIGH (strict-emulator / real-hardware crash class)
- **Build 0107 status (2026-06-27):** The immediate-absolute Class A portion is implemented and validated. Build 0107 (`dist/rastan-direct/rastan_direct_video_test_build_0107.bin`, SHA256 `4b4a588b1da2ccec6b31cac781bd53627993eaa6170ec013da56f349c99ef1e3`) routes four immediate-absolute raw FG writes (`0x3ACEA`, `0x3A550`, `0x3A8FE`, `0x3A908`) via byte-neutral 8-byte `jsr abs.l + nop` trampolines → `genesistan_hook_tilemap_fg_fill` (live LUT → FG staging → dirty → VBlank commit). Invariants: `opcode_replace 98→102`, `total_genesis_bytes_covered 0x17CD68→0x17CDD4` (helper growth `0x6C`), attr gate passed for all four. The **story-page comma crash is fixed on BlastEm and real Genesis and the comma renders** (`0x3ACEA`); `0x3A908` staging + `%d0` preservation runtime-proven; `0x3A550`/`0x3A8FE` are structurally covered by the same mechanism but were not runtime-reached in the sampled validation windows (no overclaim of visual proof for those two). **Do not mark OPEN-018 globally closed** — the register-absolute (`0x3A92A`, `0x3D24C`) and producer-loop (`0x3B3CC`, `0x3B7F6`, `0x3B7F8`) raw-write shapes remain (did NOT block the validated story-page path; relevant to full raw-write closure / other screens). See `docs/design/Andy_build_0107_validation_and_class_b_remaining_status.md`. The TAITO/paren visual gaps are NOT under OPEN-018 — they are Class B (KF-033 / OPEN-019 / OPEN-020).
- **Discovered by:** Cody (Build 0106 c09172 writer watchpoint) / canonicalized by Andy
- **Observed in build/artifact:** Build 0106, `dist/rastan-direct/rastan_direct_video_test_build_0106.bin`, SHA256 `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`
- **Summary:** `runtime_genesis_pc 0x0003ACEA` (= `arcade_pc 0x0003AAEA`, `arcade_copy`) executes `move.w #0x2749, 0x00C09172` — a raw copied PC080SN FG write (story comma/special glyph, FG row17/col28) that bypasses Genesis staging. Class A (KF-032). Tile `0x2749` is already mapped (slot `0x0039`); the defect is the raw write path into VDP-mirror space.
- **Evidence:** docs/design/Cody_build_0106_c09172_writer_watchpoint.md; docs/design/Cody_build_0106_correction_taito_arcade_intent_paren_lut.md; address_map.json segment `0x03AB20..0x03AD00`.
- **Suspected area:** translated-arcade-write routing; same class as the Build 0106 scroll-RAM raw fill (0x3AF3C).
- **Next required task:** design a routing fix that delivers the arcade intent (stage tile 0x2749 at FG row17/col28) through the FG staging path; do NOT NOP/suppress. Scan for sibling raw PC080SN/PC090OJ writes (e.g. inline producer `0x0003B392`).
- **Closure condition:** the story-comma cell is staged (not raw-written) and renders on strict targets without an HV/port fatal.

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
