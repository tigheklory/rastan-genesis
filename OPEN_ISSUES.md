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
- **Summary:** Palette is visible in Exodus and tile preload base is now corrected (CLOSED-007). However, the visible composed output remains incorrect — Build 59 Image Window shows green fill blocks, black regions, and striped artifacts despite correct preload placement, populated CRAM, active VRAM, and sane VDP plane bases. Root cause is no longer "wrong slot base" but rather wrong nametable composition / plane priority / window plane / palette mapping.
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
- **Evidence (Build 59 post-CLOSED-007 transformation):**
  - SGDK-era 20-slot reservation removed in Build 59 (`dist/rastan-direct/rastan_direct_video_test_build_0059.bin`, SHA256 `1135e1aaa2e2c39d64a8390c024dd8e67a998b53f829f2cd7e4eabea2d02ec23`); see CLOSED-007.
  - Build 59 video debug capture (`docs/design/Cody_build59_video_30fps_debug_windows.md`):
    - Pattern Viewer: nontrivial tile glyph content visible (text fragments "RASTA...", dense tile content)
    - VRAM Memory Editor: structured non-zero tile data at low addresses (e.g., `0x0026`, `0x00B0`, `0x0108`, `0x02AA`, `0x0302`)
    - Image Window: ACTIVE but INCORRECT — large green fill blocks, black regions, striped artifacts
    - CRAM: populated with mixed non-default values (Row 00: `0000 0EEE 000E 0468 08AC 046A...`)
    - 68000 PC samples in active runtime: `0x000719E0`, `0x0003B100` (Exodus only — MAME Build 59 progression unverified)
    - Plane Viewer: A=`0xE000`, B=`0xC000`, Window=`0xF000`, Sprites=`0xF800` (consistent with Build 58 verified bases)
  - Tighe visual confirmation: VRAM 0x0000..0x001F is blank in Build 59 Exodus state (slot 0 sentinel preserved as expected per CLOSED-007 closure conditions)
  - This is the FIRST truly debuggable visual state for the project — visible palette, populated CRAM, active VRAM, non-empty Pattern Viewer, corrected preload alignment, and an active (though incorrect) composed output window all coexist for the first time.
- **Suspected area:** Nametable composition for Plane A/B at populated active state — what tile indices are being written to nametable cells, with what palette line/priority/flip bits. Possible secondary suspects: window plane composition (`0xF000`), plane priority configuration in VDP registers, palette-line-to-CRAM mapping for sprite vs background tiles. Tile preload base is no longer suspect (resolved in CLOSED-007).
- **Next required task:** Build 59 runtime state comparison — verify whether MAME on Build 59 also reaches the active VDP/CRAM state Exodus shows, OR whether MAME remains stuck (which would mean Exodus is the only viable evidence source for OPEN-001 going forward). If MAME progresses, capture Plane A/B nametable bytes from MAME at populated state and decode tile indices, palette lines, priority bits. If MAME stuck, plan Exodus-side nametable extraction (manual Memory Editor capture or save-state export) for the same five ranges (VRAM 0x0000..0x1FFF, VRAM 0xC000..0xCFFF, VRAM 0xE000..0xEFFF, VRAM 0xF000..0xFFFF, VDP regs 0x00..0x17).
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
