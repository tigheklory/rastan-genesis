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

## OPEN-001 — Offset graphics / tile slot base mismatch

- **Status:** OPEN
- **Priority:** HIGH
- **Discovered by:** Tighe
- **Observed in build/artifact:** Build 55b / sequential ROM (per OPEN-002 ROM identity ambiguity)
- **Summary:** Palette is populated in CRAM and tile preload base is corrected (CLOSED-007). VDP internals show populated state in Exodus debug panes — Pattern Viewer contains real Rastan tile data starting at slot 0, VRAM Memory Editor shows structured data, CRAM contains mixed non-default values. However, the actual composed video output (game screen) remains essentially blank in both MAME and Exodus on Build 59 (Tighe direct visual verification: black with minor purple artifact). Root cause: the rendering pipeline failure is downstream of VRAM/CRAM/preload — most likely in nametable composition (writes to Plane A/B at `0xC000`/`0xE000` not happening or producing wrong indices/attributes), plane enable bits in VDP registers, display enable sequencing, or runtime control flow that should reach nametable-writer code paths but does not.
- **Evidence:** Tighe visual observation from Exodus session post-Build-55b.
- **Evidence (Build 58 evidence pass):**
  - Canonical ROM identity reconciled to `0057.bin` with SHA256 match against `0055b.bin` alias (see OPEN-002 update below).
  - VDP plane bases verified consistent from source+trace+viewer: A=`0xE000`, B=`0xC000`, Window=`0xF000`, SAT=`0xF800`.
  - Scene tile preload/load base verified at slot `0x14` (VRAM `0x280`) via manifests + runtime control-port trace.
  - PC080SN tile LUT path verified active and aligned with checked preload slots.
  - Plane A/B nametable word ranges (`0xE000..0xEFFF`, `0xC000..0xCFFF`) are **NOT VISIBLE** in current screenshot set; this blocks direct constant-offset proof/refutation for nametable indices.
  - Full report: `docs/design/Cody_build58_offset_graphics_evidence.md`.
- **Evidence (Build 58b nametable dump continuation):**
  - Read-only dump captured with canonical ROM state (`states/dumps/build58b_20260505_175403/`), including all required ranges:
    - `VRAM 0x0000..0x1FFF`
    - `VRAM 0x0C000..0x0CFFF` (Plane B nametable)
    - `VRAM 0x0E000..0x0EFFF` (Plane A nametable)
    - `VRAM 0x0F000..0x0FFFF`
    - `VDP regs 0x00..0x17`
  - Capture metadata: frame `900`, `PC=0x03A198`, `SR=0x2700`, `IPM=7`.
  - Plane B (`0xC000..0xCFFF`) decode: all 2048 cells `0x0000` (`index=0`, flips/palette/priority clear).
  - Plane A (`0xE000..0xEFFF`) decode: all 2048 cells `0x0000` (`index=0`, flips/palette/priority clear).
  - Statistics:
    - Plane A: min=`0`, max=`0`, cells `<0x14`=`2048`, cells `>=0x14`=`0`
    - Plane B: min=`0`, max=`0`, cells `<0x14`=`2048`, cells `>=0x14`=`0`
  - Late confirmation run (`states/dumps/build58b_20260505_175922/`, frame `5000`, `PC=0x03A194`) also produced all-zero target VRAM ranges.
  - Hypothesis B classification from this continuation: **INSUFFICIENT** (dump state non-diagnostic; no live nametable index stream present).
  - Full report: `docs/design/Cody_build58b_nametable_dump_evidence.md`.
- **Evidence (Build 58c visible-state acquisition):**
  - State-validation gate run in MAME across required timestamps (`sec_5`, `sec_10`, `sec_20`, `sec_30`, `sec_60`, `sec_120`) using canonical `0057.bin`.
  - Validation artifact: `states/dumps/build58c_20260506_132350/validation.txt`.
  - At every sampled timestamp:
    - `VRAM 0x029A = 0x0000`
    - `VRAM 0x02AA = 0x0000`
    - `VRAM 0x02C0 = 0x0000`
    - `VRAM 0xC000 = 0x0000`
    - `VRAM 0xE000 = 0x0000`
    - non-zero counts for `0x0280..0x037F`, `0xC000..0xCFFF`, `0xE000..0xEFFF` all `0`
    - gate result `FAIL`
  - Build 58c conclusion: MAME did not reproduce a validated visible-state capture for OPEN-001 byte-level nametable evidence in this run window; 5-range dump/decode was intentionally skipped by gate rule.
  - Full report: `docs/design/Cody_build58c_visible_state_acquisition.md`.
- **Evidence (Build 59 post-CLOSED-007 — corrected interpretation):**
  - SGDK-era 20-slot reservation removed in Build 59 (`dist/rastan-direct/rastan_direct_video_test_build_0059.bin`, SHA256 `1135e1aaa2e2c39d64a8390c024dd8e67a998b53f829f2cd7e4eabea2d02ec23`); see CLOSED-007.
  - Build 59 video debug capture (`docs/design/Cody_build59_video_30fps_debug_windows.md`) confirmed VDP internal state populated:
    - Pattern Viewer: nontrivial tile glyph content visible (text fragments "RASTA...", dense tile content) — Tighe directly verified
    - VRAM Memory Editor: structured non-zero data at low addresses (e.g., `0x0026`, `0x00B0`, `0x0108`, `0x02AA`, `0x0302`)
    - CRAM: populated with mixed non-default values (Row 00: `0000 0EEE 000E 0468 08AC 046A...`)
    - 68000 PC samples in active runtime: `0x000719E0`, `0x0003B100`
    - Plane Viewer base addresses: A=`0xE000`, B=`0xC000`, Window=`0xF000`, Sprites=`0xF800` (consistent with Build 58 verified bases)
  - **Correction:** the Cody report's description of Image Window content as "green rectangular fill regions plus black regions and striped artifact bands" was an interpretation error. Those green rectangular regions were Plane Viewer boundary overlays (Screen Boundaries / Sprite Boundaries checkboxes enabled in the Plane Viewer panes), NOT actual rendered game video output.
  - **Tighe direct visual verification (May 7, 2026):** the actual game video output (Image Window in Exodus, game window in MAME) on Build 59 is essentially blank — black screen with a small purple artifact near the top — same fundamental visual state in both emulators, same as canonical Build 57.
  - Tighe direct verification of slot 0 in Exodus: VRAM `0x0000` area is blank (CLOSED-007 sentinel preservation confirmed).
  - **Architectural significance:** CLOSED-007 was a real cosmetic / data-organization fix (tile data now at correct slot, Pattern Viewer reflects it), but it did NOT change actual game rendering behavior. The rendering pipeline downstream of VRAM/CRAM is what's broken. Tile patterns are loaded into VDP memory; CRAM is populated; but the composition step that should produce visible rendered output does not happen (or does not happen correctly).
  - **MAME script anomaly:** Cody's MAME validation.txt (`Cody_build59_runtime_state_comparison.md`) reported all-zero VRAM sentinels and all-zero nametable first cells across all 6 timestamps in MAME. This contradicts the populated state Exodus debug panes show on the same ROM. Possible causes: MAME instrumentation issue, wrong address space interpretation in the script, genuine MAME-vs-Exodus runtime divergence, timing/race between sampling and VRAM writes, or stale readback. Insufficient evidence to classify; tracked as OPEN-003 sub-finding.
- **Evidence (Build 59 runtime state comparison):**
  - Validation artifact: `states/dumps/build59_runtime_state_20260507_142931/validation.txt`.
  - Timestamp coverage: `sec_5`, `sec_10`, `sec_20`, `sec_30`, `sec_60`, `sec_120`.
  - Build 59 MAME sampled values:
    - `VRAM 0x029A/0x02AA/0x02C0` all `0x0000` at all timestamps.
    - `VRAM 0x0020` sentinel `0x0000` at all timestamps.
    - `VRAM 0xC000` (Plane B first cell) `0x0000` at all timestamps.
    - `VRAM 0xE000` (Plane A first cell) `0x0000` at all timestamps.
    - Non-zero word counts: `0x0000..0x1FFF=0`, `0xC000..0xCFFF=0`, `0xE000..0xEFFF=0` at all timestamps.
  - PC progression:
    - `sec_5/10/20/120`: `PC` in `0x03A19x`.
    - `sec_30`: `PC=0x071A48`, `SR=0x2600`, `IPM=6`.
    - `sec_60`: `PC=0x070610`, `SR=0x2700`, `IPM=7`.
  - Interpretation for OPEN-001 objective: despite transient non-`0x03A19x` PC states, no populated VRAM state matching Exodus was captured; full 5-range decode was intentionally skipped to avoid non-diagnostic all-zero decode.
  - Full report: `docs/design/Cody_build59_runtime_state_comparison.md`.
- **Suspected area:** **Strongly likely blocked by OPEN-004 bootstrap re-entry.** Per `docs/design/Andy_nametable_composition_path_classification.md`, Plane A/B nametable population requires arcade execution to reach the PC080SN strip producer call sites at arcade_pc `0x055968` (BG; `genesistan_hook_tilemap_plane_a`) and `0x055990` (FG; `genesistan_hook_tilemap_fg`). Parent dispatcher at arcade_pc `0x055948` is called from `0x050434`, `0x0556FC`, `0x055788`, `0x055822` — all four in the post-bootstrap arcade game-loop range. Bootstrap re-entry per OPEN-004 keeps execution looping at `0x0202..0x03BC64` and never advances to the `0x055xxx` range. Build 59 MAME PC samples confirm: sec_30 hits `0x071A48` (inside `vdp_commit_sprites` — `_vblank_service` IS firing), sec_60 hits `0x070610` (inside `genesistan_hook_tilemap_bg_fill` via 0x03AD44 polymorphic dispatch transit), but no sample reaches the `0x055xxx` strip producer range. Tile preload base is NOT suspect (CLOSED-007). Tile pattern memory is NOT suspect (Pattern Viewer). CRAM is NOT suspect (Exodus). Plane enable bits / display enable sequencing are NOT primary suspects (VBlank service runs and disables/re-enables display correctly per `vdp_comm.s:159-178`).
- **Next required task:** **OPEN-004 bootstrap re-entry trigger investigation must complete first** (per `docs/design/Andy_nametable_composition_path_classification.md` §3.2). The previous Next Required Task (Tighe Exodus Memory Editor capture of nametable ranges) is **SUPERSEDED** — the empty-nametable result is now classified as a DEPENDENT symptom rather than an independent root cause. Once OPEN-004 resolves and arcade progresses into the post-bootstrap game loop, OPEN-001 will likely self-resolve OR transform again into a downstream symptom that can be classified at that point. Cody next task: `Cody — Bootstrap Re-entry Trigger Investigation` (descriptive name, evidence-only, no ROM produced); OPEN-004's existing Next Required Task is the appropriate scope.
- **Closure condition:** emulator screenshot/video shows tile graphics referenced from correct base; trace/doc proves tile data load base and tilemap indices agree.

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
