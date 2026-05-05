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
- **Summary:** Palette is now visible in Exodus, but graphics rendering shows tile data referenced from wrong base — graphics not starting in first expected slot.
- **Evidence:** Tighe visual observation from Exodus session post-Build-55b.
- **Suspected area:** tile load base, Plane A/B tile index base, PC080SN attribute translation, VRAM staging offset, tilemap commit path.
- **Next required task:** Cody video/debug extraction (in progress) should identify VRAM tile data start address, plane tile index values, whether tile indices are offset by a constant, and where the offset originates.
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
- **Build naming policy (mandatory):**
  - ROM filenames must be strictly sequential.
  - Do NOT create `0055b`, `0055c`, etc. ROM aliases going forward.
  - Planning labels may exist in docs, but ROM artifacts must use the next sequential build number.
  - If an alias is unavoidable, the report must state: canonical artifact path, alias path, SHA256 of both, byte-identical YES/NO.
- **Suspected area:** build pipeline, artifact-naming policy, Cody implementation reports.
- **Next required task:** Cody must compute SHA256 of `0057.bin` and `0055b.bin` and report whether byte-identical. Establish next sequential build number for next implementation.
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
