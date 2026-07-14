# KNOWN_FINDINGS.md

This file is the project's curated long-term memory of durable system-behavior findings about arcade Rastan, the Genesis port, and the hardware behavior relevant to the port. Every agent reads this file at the start of every task. **Curated memory, not exhaustive memory** — bloat is a failure mode.

This file is NOT a task log. It is NOT a build log. It does NOT replace `AGENTS_LOG.md`, `OPEN_ISSUES.md`, or `CLOSED_ISSUES.md`.

## What belongs

- Durable system-behavior facts about arcade Rastan, the Genesis port, or relevant Genesis/68000 hardware.
- Verified addresses, byte sequences, hardware-register behaviors, code-routine purposes that future work must remember to avoid re-deriving.

## What does NOT belong

- Task summaries, "agent X did Y" content, build logs, implementation history.
- Issue bookkeeping (those live in OPEN_ISSUES.md / CLOSED_ISSUES.md).
- Speculative theories unsupported by evidence (those live in design docs).

## Three orthogonal axes

Every entry carries three independent labels.

**Status** (lifecycle). `ACTIVE` — current reading. `SUPERSEDED` — once active, narrowed/refined/replaced by a later finding; kept so older docs don't revive stale interpretations. `RETIRED` — no longer applies to current project state.

**Confidence** (evidence strength). `CONFIRMED` — verified by byte inspection, hash, trace, hardware docs, or multiple independent investigations agreeing. `STRONG` — well supported, no contradicting evidence, partly interpretive. `WORKING_HYPOTHESIS` — current best explanation; may be tested, promoted, demoted, or superseded. Multiple ratings are allowed when parts of one entry differ.

**Applicability** (scope). `GLOBAL` — all project builds/contexts. `BUILD_SPECIFIC`, `ERA_SPECIFIC`, `CONTAMINATED_CONTEXT` — cite specifics where used; contaminated-context findings may not generalize.

## Rediscovery Hazard (binary)

`HIGH` — historically rediscovered or reframed by agents lacking prior knowledge; HIGH entries include a "treat as canonical prior unless contradicted by explicit evidence" instruction in Use as prior. `NORMAL` — ordinary; no special handling.

## Observation vs. interpretation

Findings describe **observable system behavior** — what code does, addresses involved, bytes verified, runtime states measured. Interpretation, causality, and intent belong **only** in labeled "Working hypotheses" or "Use as prior" subsections.

- **BAD:** "The game intentionally resets because bootstrap progression is broken."
- **GOOD:** "Watchdog expires before any observed kick site executes, producing repeated bootstrap re-entry."

The bad version smuggles intent, causality, and characterization into a single sentence presented as fact. The good version is mechanical.

## Entry format

Metadata block mandatory; prose subsections render only when populated.

- **Status / Confidence / Applicability / Rediscovery Hazard** — per the schema above.
- **Addresses** — comma-separated, address-space labeled where applicable.
- **Source Documents** — file paths with section/line where applicable.
- **Related Issues** — comma-separated `OPEN-NNN` / `CLOSED-NNN`, or "(none)".
- **Last verified** — `YYYY-MM-DD` (build context).

Prose subsections:

- **Finding.** Observable system behavior. No interpretation, causality, or intent.
- **Use as prior.** How future agents should treat the finding (HIGH-hazard canonical-prior note lives here).
- **Working hypotheses.** Labeled interpretations not yet CONFIRMED/STRONG; each cites source and confidence.
- **Supersession notes.** Required when older readings have been narrowed/refined/replaced by this entry.

## Maintenance

Agents read this file at the start of every task. Propose updates only for durable system-behavior findings. If current evidence appears to contradict a `CONFIRMED` or `STRONG` finding, STOP and report — do not silently rewrite.

---

## KF-001 — Watchdog/reset routine

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (mechanism, addresses) / WORKING_HYPOTHESIS (OPEN-001+OPEN-004 collapse claim)
- **Applicability:** GLOBAL (rastan-direct, all builds post-determinism-gate)
- **Rediscovery Hazard:** HIGH (repeatedly rediscovered and reframed across project history; treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** routine 0x0003A180..0x0003A1AC; visible delay loop 0x0003A192 ↔ 0x0003A19C; counter A5+0x2C = WRAM 0x00FF002C; reset path vector sources 0x00000000 (SP) and 0x00000004 (PC); reset target _bootstrap 0x00000202; 11 kick sites (0x0003A5D4, 0x0003A63E, 0x0003AC88, 0x0003ACF2, 0x0003AD22, 0x0003AD5E, 0x0003ADD0; plus 4 tentative deeper sites at 0x0009A3B0/D0, 0x0009A4B0/D0)
- **Source Documents:** docs/design/Andy_polling_loop_investigation.md; docs/design/Andy_BM002_runtime_failure_investigation.md; BM-003 evidence at dist/rastan-direct/bookmarks/build_0076_pc_0x0003A19C/; docs/design/WRAM_memory_map.md (corroborates counter location 0xFF002C); AGENTS_LOG.md (corroborates mechanism via multiple historical entries)
- **Related Issues:** OPEN-001, OPEN-004
- **Last verified:** 2026-05-29 (Build 0077)

**Finding.** A software watchdog routine in the arcade-translated code. The routine tests a counter at 0x00FF002C; if positive, decrements and returns; if zero, runs a ~3.6s delay loop, reloads SP and PC from the reset vectors at 0x00000000 and 0x00000004, and jumps to _bootstrap at 0x00000202. The total cycle (delay + bootstrap restart) is ~4.3s, matching OPEN-004's observed 15-re-entries-in-64s. 11 code sites elsewhere in the ROM write positive values to 0x00FF002C ("kick sites"); 1 site explicitly clears it.

**Use as prior.** Do not frame 0x0003A192 ↔ 0x0003A19C as a mysterious loop or polling wait. The mechanism is established. Investigations involving the boot path or early game-loop run against this ~3.6s deadline. The watchdog mechanism is not itself the defect; the defect is upstream — arcade game-loop progression is failing to reach the kick sites before the counter expires. Investigations should target that upstream progression failure, not re-investigate the watchdog mechanism. The loop body at 0x0003A192 is a D1 countdown via SUBI.L + BNE.S; the MOVE.L $0.W,D0 read returns a constant ROM value and is not a polling read.

**Working hypotheses.** (1) OPEN-001 and OPEN-004 share this as common proximate cause. The math fits and symptoms align, but graphics-pipeline progress per CURRENT_STATE.md and GRAPHICS_STATUS.md complicates the simple reading; the alternative (shared upstream cause but functionally distinct manifestations) has not been ruled out. Per Andy_polling_loop_investigation §5.2. (2) Every bootstrap cycle hits the watchdog routine before any kick site is reached, so the counter (zero from BSS clear) immediately expires. Per Andy_polling_loop_investigation §5.3; explicitly flagged by Andy as hypothesis, not proven by static analysis alone.

**Supersession notes.** Earlier "delay loop" and "soft-reset preamble" characterizations (BM-002 era) describe parts of this mechanism and remain valid as far as they go. The earlier "staged_bg_buffer[0] = 0x0001 is the root cause" reading is superseded — that overlap is one specific path to a zero counter, not the broader cause.

## KF-002 — Bootstrap re-entry cadence (observed)

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** BUILD_SPECIFIC (observed in Build 55a/55b issue-window evidence)
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** runtime Genesis PC chain `0x00000202 -> 0x0000022C -> 0x0000024A`
- **Source Documents:** OPEN_ISSUES.md (OPEN-004 body)
- **Related Issues:** OPEN-004, OPEN-001
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** Runtime re-entry into the bootstrap/startup chain (`0x0202 -> 0x022C -> 0x024A`) was observed repeatedly at roughly 15 cycles per 64 seconds in the cited evidence window.

**Use as prior.** Treat bootstrap re-entry cadence as measured behavior in the cited window, not as a resolved cause statement.

## KF-003 — Watchdog kick-site inventory and progression-failure framing

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** GLOBAL (writer inventory) / BUILD_SPECIFIC (observed reachability omission in analyzed Build 0077 window)
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** kick sites `0x0003A5D4`, `0x0003A63E`, `0x0003AC88`, `0x0003ACF2`, `0x0003AD22`, `0x0003AD5E`, `0x0003ADD0`, `0x0009A3B0`, `0x0009A3D0`, `0x0009A4B0`, `0x0009A4D0`; force-expire clear `0x0003AE76`; watchdog counter `0x00FF002C`
- **Source Documents:** docs/design/Andy_polling_loop_investigation.md (§3.1, §4.1-§4.2); docs/design/Andy_first_kick_path_cross_reference.md (Phase 1-3 static cross-reference; Outcome B); docs/design/Andy_predecessor_chain_0x0003AC88.md (backward-trace; Outcome B; 9-node chain + %a5@(44) dual-use)
- **Related Issues:** OPEN-004, OPEN-001
- **Last verified:** 2026-06-11 (Build 0077)

**Finding.** The `%a5@(44)` (`0x00FF002C`) writer inventory includes 11 positive-value kick sites, 5 decrement sites, and one explicit force-expire clear site (`CLRW` at `0x0003AE76`). In the analyzed Build 0077 observation window, sampled execution included interrupt/helper excursions but did not include the known kick-site region. Static cross-reference of Build 0077 (Andy, `docs/design/Andy_first_kick_path_cross_reference.md`) identifies the path from reset to any kick site as `reset → init → main loop → Level-5 VBlank → state-machine dispatcher → handler containing the kick`. The arcade main loop at `0x3B07E` and its Genesis-translated equivalent at `0x3B27E` are byte-perfect translated-flow equivalents through the watchdog test wrapper at arcade `0x39FA8` / Genesis `0x3A1A8`. The WRAM rebase from arcade `0x10C000` to Genesis `0xFF0000` is a translation patch that preserves the `%a5@(44)` watchdog-counter invariant. No causally-meaningful static divergence is identifiable on the path from reset to a kick site; reachability is determined at runtime by VBlank dispatch and state-machine progression.

**Use as prior.** Use this as a two-part prior: writer inventory is a stable mechanism fact; sampled non-reachability is window-scoped evidence. When investigating non-reachability of kicks, do NOT search for a static divergence in the reset-to-main-loop layers — they are translation-equivalent. Focus instead on Level-5 VBlank vector setup, VBlank dispatcher entry, and state-machine initial conditions. The concrete predecessor chain to the first kick `0x0003AC88` (Andy, `docs/design/Andy_predecessor_chain_0x0003AC88.md`) is: Genesis Level-6 VBlank vector → `0x700c2` (servicing helpers) → `jmp 0x3a208` (arcade VBlank handler) → master dispatch on `%a5@(0)` at `0x3a256` (state 0 → `0x3abfe`) → title dispatcher gated on `%a5@(44)==0`, sub-dispatch on `%a5@(2)` (0) and `%a5@(4)` (1) → handler `0x3ac54` → kick `0x3ac88`. The chain is translated-flow equivalent arcade↔Genesis; the only byte difference is reachability-neutral NOP elision of arcade hardware writes (`0x350008`, `0x3c0000`) at the VBlank entry. The counter `%a5@(44)` is dual-use: the title dispatcher at `0x3abfe` decrements it each frame and dispatches only at zero, the same cell the KF-001 watchdog tests for expiry.

## KF-004 — runtime_genesis_pc equals cartridge ROM file offset

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** runtime Genesis PC `N` maps to ROM file offset `N` (example: `0x03A19C`)
- **Source Documents:** docs/design/Andy_BM002_runtime_failure_investigation.md (§1.2)
- **Related Issues:** CLOSED-010, CLOSED-011
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** CPU fetch at runtime Genesis PC `N` reads cartridge ROM bytes at file offset `N` in this port context.

**Use as prior.** Any bookmark or trace interpretation that breaks this identity is suspect until proven otherwise.

## KF-005 — Retired BM-001/BM-002 cycles exhibit target-space mismatch (evidence not trustworthy at face value)

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (BM-002 mismatch) / STRONG (BM-001 same fault class)
- **Applicability:** CONTAMINATED_CONTEXT (retired BM-001/BM-002 evidence)
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** BM-002 arcade_pc `0x03A19C` translated write offset `0x03A39C` vs trace/runtime `0x03A19C`; BM-001 arcade_pc `0x055948` translated write offset `0x055B48` vs trace/runtime `0x055948`
- **Source Documents:** docs/design/Andy_BM002_runtime_failure_investigation.md (§5.1, §6.1)
- **Related Issues:** CLOSED-010
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** Retired BM-001/BM-002 cycle evidence contains target-space mismatch between where activators were written and where runtime PCs were executed.

**Use as prior.** Do not treat BM-001/BM-002 Outcome-B-style non-hits as reachability evidence without first correcting for the target-space mismatch.

## KF-006 — identity_offset is 0x200 across current arcade_copy segments

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** ERA_SPECIFIC (current `address_map.json` configuration)
- **Rediscovery Hazard:** NORMAL
- **Addresses:** translation constant `identity_offset = 0x200`
- **Source Documents:** docs/design/Andy_OPEN012_bookmark_coordinate_model_design.md (§1.1)
- **Related Issues:** CLOSED-010
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** In the current mapping configuration, all `arcade_copy` segments use `identity_offset = 0x200` and no alternate identity offset is present.

## KF-007 — bookmarks_v2 writes activators using trace PC verbatim

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** bookmark target `runtime_genesis_pc`; write location ROM file offset `runtime_genesis_pc`
- **Source Documents:** docs/design/Andy_OPEN012_bookmark_coordinate_model_design.md (§2.4, §3.1)
- **Related Issues:** CLOSED-010, CLOSED-011
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** Under `bookmarks_v2`, trace PC is used verbatim as `runtime_genesis_pc`, and activator bytes are written at that same ROM file offset without bookmark-side arithmetic.

## KF-008 — WRAM ownership split (arcade workram vs Genesis BSS)

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** ERA_SPECIFIC (WRAM map documented in source)
- **Rediscovery Hazard:** NORMAL
- **Addresses:** arcade workram `0xFF0000..0xFF3FFF`; Genesis BSS ownership starting `0xFF4000..`
- **Source Documents:** docs/design/WRAM_memory_map.md (Address Space Overview)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** The documented WRAM ownership split assigns `0xFF0000..0xFF3FFF` to arcade workram domain and `0xFF4000..` to Genesis BSS domain.

## KF-009 — Diagnostic bookmark helper location and bytes

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** helper runtime Genesis PC `0x00071C78`; bytes `60 FE`
- **Source Documents:** docs/design/Cody_BM003_insert.md; docs/design/Cody_BM003_revert.md
- **Related Issues:** OPEN-014
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** The diagnostic helper `genesistan_diag_bookmark` is located at `0x00071C78` and uses `60 FE` (`BRA -2`) as its parked-loop body.

## KF-010 — Plane mapping: BG → Plane B, FG → Plane A

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** ERA_SPECIFIC (documented direct-model mapping)
- **Rediscovery Hazard:** NORMAL
- **Addresses:** VRAM Plane B base `0xC000`; Plane A base `0xE000`
- **Source Documents:** AGENTS.md (VDP Layer Mapping)
- **Related Issues:** OPEN-001
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** The documented layer mapping places arcade BG on Genesis Plane B and arcade FG on Genesis Plane A.

## KF-011 — Frame ownership: arcade Level-5 VBlank owns progression

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** N/A
- **Source Documents:** ARCHITECTURE.md (Frame Ownership / VBlank Behavior)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** Frame progression is owned by arcade Level-5 VBlank; Genesis-side VBlank is servicing-only (staged commit / DMA) and must not own gameplay progression.

## KF-012 — Interrupt enable site and ENABLE-then-CLEAR ordering

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (first IMASK lowering site) / STRONG (observed ENABLE-then-CLEAR ordering)
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** Genesis boot enable `boot.s:160` (`move.w #0x2000,%sr`); arcade enable site `arcade_pc 0x03B07A`; startup clear site `0x03AEFC`
- **Source Documents:** docs/design/Andy_interrupt_enable_timing.md (Phase 3, summary)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** On the analyzed cold-boot path, first IMASK lowering occurs in Genesis bootstrap before arcade startup enable-site processing, yielding observed ENABLE-then-CLEAR ordering.

## KF-013 — Text producer dispatch fires inside VBlank handler

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** text dispatch entry `0x0003BB48`; VBlank handler region around `0x0003A008`
- **Source Documents:** docs/design/rastan_vblank_and_vdp_buffer_architecture.md (Key Finding)
- **Related Issues:** OPEN-001
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** The primary text dispatch path (`0x3BB48`) is called from inside the VBlank interrupt handler for title/text selectors.

## KF-014 — PC080SN tile LUT O(1) lookup contract

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** LUT tile-code domain `0x0000..0x3FFF`
- **Source Documents:** docs/design/pc080sn_tilemap_architecture.md (§2a)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** The PC080SN tile-LUT path pre-assigns VRAM slots for strip-table-reachable tile codes and uses direct LUT lookup at runtime (no per-hit lookup DMA work).

## KF-015 — Scroll model: full-plane with raw-Y negation plus +8 vertical bias, no per-line

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** WRAM/A5 offsets `0x10EC`, `0x10EE`, `0x10AE`, `0x10B0`
- **Source Documents:** docs/design/pc080sn_tilemap_architecture.md (Scroll System); docs/design/build317_scroll_wram_staging_and_single_commit.md; docs/design/Cody_build0165_visual_issue_ledger_and_scroll_trace.md
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-13 (Build 0166 vertical-scroll sign fix)

**Finding.** Documented scroll commit uses full-plane BG/FG scroll values and does not use per-scanline scroll mode. For vertical scroll, raw PC080SN BG/FG Y source words (`a5+0x10EE` / `a5+0x10B0`) must be converted to Genesis VSRAM convention as `-raw + VDP_DISPLAY_ORIGIN_Y_BIAS` (bias currently `+8`), not committed raw with bias only. Build 0165 proved the raw source/staged Y values matched arcade directionally while Genesis VSRAM publication used the wrong sign; Build 0166 restored the negation in `vdp_commit_scroll`.

## KF-016 — Title-state VBlank sprite-RAM clear pattern

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** clear-loop site around runtime Genesis PC `0x0003AD4C`; arcade sprite RAM region `0x00D00000`
- **Source Documents:** docs/design/rastan_vblank_and_vdp_buffer_architecture.md (Sprite RAM Clear)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** The title-state VBlank sequence includes sprite RAM clear writes using `0x00000100` off-screen Y marker semantics across clear loops.

## KF-017 — opcode_replace strict invariants under bookmarks_v2

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** invariant counts `94` sites, coverage `0x17CAEC`
- **Source Documents:** docs/design/Cody_OPEN012_OPEN013_implementation.md (A3, A5)
- **Related Issues:** CLOSED-011
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** Under `bookmarks_v2`, opcode_replace invariants remain strict canonical values (`94` sites, `0x17CAEC` coverage) in all build modes, including diagnostic runs.

## KF-018 — Bookmark schema validation: legacy forms fail-closed, failure IDs disambiguated

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** failure IDs `GATE_FAIL_LEGACY_BOOKMARK_SCHEMA`, `GATE_FAIL_2_5_BOOKMARK_SCHEMA_VALIDATION`
- **Source Documents:** docs/design/Cody_OPEN012_OPEN013_implementation.md (A2, A5, failure-ID table)
- **Related Issues:** CLOSED-011
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** Legacy bookmark schema forms (`diagnostic_bookmarks`, `opcode_replace.bookmark_cycle`) are rejected fail-closed, and schema-validation failures are emitted under disambiguated failure IDs with distinct meanings.

## KF-019 — MAME tracer parked-helper sampling gap

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GLOBAL (instrumentation-path limitation) / BUILD_SPECIFIC (BM-003 sampled-trace instance)
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** helper `0x00071C78`; MAME exit summary final PC `0x071C7A`
- **Source Documents:** OPEN_ISSUES.md (OPEN-014); AGENTS_LOG.md (BM-003 Insert/Revert entries)
- **Related Issues:** OPEN-014
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** In BM-003, helper park was confirmed by Exodus observation and MAME exit summary, while sampled MAME trace lines did not directly capture parked-helper PCs.

**Use as prior.** Treat sampled MAME-trace helper non-appearance as an instrumentation caveat unless paired with explicit currency and corroborating evidence.

## KF-020 — FG sentinel and overlay contamination invalidates Plane-A and text-pipeline evidence

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** CONTAMINATED_CONTEXT
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** N/A
- **Source Documents:** Master Diagnostic Debt.md (§2.1)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** When FG sentinel and overlay diagnostics are active, Plane A/text-pipeline conclusions from those runs are non-trustworthy.

**Use as prior.** Evidence gathered under this contamination class requires explicit decontamination or independent corroboration before promotion to canonical behavior claims.

## KF-021 — Combined sprite-renderer-early-return and SAT-DMA suppression masks sprite output

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** CONTAMINATED_CONTEXT
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** N/A
- **Source Documents:** docs/design/Andy_diagnostic_debt_audit.md (High-Risk Contaminants)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** If sprite-renderer early-return and SAT DMA suppression are both active, visible sprite output can be fully masked regardless of upstream sprite-generation behavior.

**Use as prior.** Sprite-layer conclusions from such runs are non-diagnostic until the contamination pair is removed.

## KF-022 — TC0040IOC input registers are active-low

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** `0x390001`, `0x390003`, `0x390005`, `0x390007`, `0x390009`, `0x39000B`
- **Source Documents:** docs/design/TC0040IOC_specifications.md (register map/convention)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** TC0040IOC input reads are active-low byte semantics: open/unpressed reads `1`, asserted/pressed reads `0`.

## KF-023 — TC0040IOC 0x380000 control-write semantics (coin lockout, flip-screen)

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** control write target `0x380000`
- **Source Documents:** docs/design/TC0040IOC_specifications.md (§3.5)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** Writes to TC0040IOC control target `0x380000` carry control semantics that include coin-lockout and flip-screen state handling in the documented map.

## KF-024 — Rastan DIP defaults: DIP1=0x01, DIP2=0x00 for non-flipped upright

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** DIP ports `0x390009`, `0x39000B`
- **Source Documents:** docs/design/Andy_rastan_dip_defaults_and_flip_behavior.md (§5.3, §9)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** For documented non-flipped upright defaults, active-high interpreted values are DIP1 `0x01` and DIP2 `0x00` after inversion.

## KF-025 — 0xDFFFFE is unmapped open-bus (not watchdog/control)

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** `0xDFFFFE`; watchdog/control comparison target `0x3C0000`
- **Source Documents:** docs/design/Andy_dffffe_hardware_identification.md (§5)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** `0xDFFFFE` is classified as unmapped open-bus in the analyzed hardware mapping context and is distinct from watchdog/control register paths.

## KF-026 — PC090OJ runtime write surface not fully statically enumerable

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** representative pointer-indexed write path around runtime Genesis PCs `0x41BF8..0x41C1C`
- **Source Documents:** docs/design/Andy_pc090oj_full_subsystem_design.md (§1.3, §3, §9)
- **Related Issues:** OPEN-006
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** Static analysis alone does not fully enumerate PC090OJ write surfaces because pointer-indexed runtime addressing contributes write destinations that require trace evidence.

## KF-027 — Rastan sound queue silently drops commands on full

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** WRAM queue range `a5+0x292..0x297`
- **Source Documents:** docs/design/Andy_rastan_sound_command_execution_verified.md (queue behavior, edge case)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** The documented 6-slot sound queue silently drops new command bytes when all slots are occupied (no overflow flag).

### KF-028 — Genesis input mirror wiring exposes unrelocated title-text descriptor table

Status: ACTIVE
Confidence: CONFIRMED (input-mirror static facts; descriptor relocation/data facts; faulting instructions + crash records; Build 0091 helper precondition facts) / STRONG (U3 tool-gap classification; hook-behavior classification)
Applicability: BUILD_SPECIFIC (Build 0077 baseline, KF-028 input-shim wiring patched ROM, and OPEN-016 Part 2 Build 0091)
Rediscovery Hazard: HIGH (treat as canonical prior unless contradicted by explicit evidence)
Addresses: input mirror `0xff60fc..0xff6100` including `0xff60ff`; shim writer `0x711ac`; shim entry `0x710ca` / patched symbol `0x710ce`; intended caller `_vblank_service` runtime `0x700c2`; state gate `0x3ad96`; state-3 writer `0x3add6`; title handler `0x3acc6..0x3accc`; glyph/string renderer `0x3bd48`; faulting write `0x3bd66`; descriptor-pointer table `0x3bd7c`; `table[65]` at `0x3be80`; stale pointer `0x0003c246`; relocated descriptor `0x3c446`; fault address/text bytes `0x50205741` (`"P WA"`); Build 0091 helper fault write `runtime_genesis_pc 0x00070794`; stacked PC `0x00070796`; shared FG-staging helper `runtime_genesis_pc 0x000707bc`; `staged_fg_buffer` WRAM `0x00ff501a`; Build 0091 fault address `0x00000f41`
Source Documents: docs/design/Andy_0xff60ff_input_shim_audit.md (input mirror static audit; Outcome A); docs/design/Andy_0x710ca_call_site_investigation.md (intended shim caller); docs/design/Andy_kf028_real_fault_triage.md (real crash record; faulting instruction); docs/design/Andy_kf028_glyph_renderer_caller_trace.md (caller/d0/table chain); docs/design/Andy_kf028_title_text_descriptor_provenance.md (U3 provenance/root); docs/design/Andy_build_0091_helper_crash_triage.md (Build 0091 helper crash; hook behavior bug); BM-007 evidence at dist/rastan-direct/bookmarks/build_0077_pc_0x0003ADD6/ (runtime corroboration)
Related Issues: OPEN-001, OPEN-004, OPEN-015, OPEN-016
Last verified: 2026-06-19 (Build 0091 / OPEN-016 Part 2 ROM)

**Finding.** In Build 0077, the arcade TC0040IOC input mirror at Genesis WRAM `0xff60fc..0xff6100` is neither initialized nor updated: its sole writer is `0x711ac` inside the controller-poll shim at `0x710ca`, the shim was unreferenced, and the mirror lies in the boot-clear gap `0xff60fa..0xff6103`. Wiring the shim into `_vblank_service` changes execution from watchdog/state-3 routing into main-loop / Level-6 VBlank / title sub-state execution. In that newly reached title path, `0x3acc6` loads `d0=65`, `0x3acc8` calls glyph/string renderer `0x3bd48`, and stack breadcrumb `0x3accc` is the return address from that call. The renderer computes `idx=d0&0x7f=65`, reads `table[65]` from `0x3be80` in table `0x3bd7c`, gets stale Genesis value `0x0003c246`, loads descriptor pointer `0x3c246`, and reads `descriptor[0]=0x50205741` (`"P WA"`, odd text bytes). The faulting instruction is `0x3bd66: movew %d2,%a1@+`; crash-frame IR `0x32c2` matches that instruction and SSW confirms a write. The address error is therefore text data being used as the renderer destination pointer. OPEN-016 Part 2 Build 0091 adds `genesistan_hook_glyph_renderer_3bd48` to route the title glyph renderer's PC080SN FG writes into `staged_fg_buffer`, and the Build 0091 ROM faults with an ADDRESS ERROR write at `runtime_genesis_pc 0x00070794`. The instruction is `move.w %d1,(0,%a6,%d2.w)`; crash-frame IR `0x3d81` matches the instruction and extension word `0x2000`, stacked PC `0x00070796` points at the extension word per the m68k group-0 imprecise-PC convention, stacked SR is `0x2700`, SSW is `0x000d` (write, supervisor data), and the fault address is odd low address `0x00000f41`.

**Build 0153 extension (embedded-pointer class generalised).** The same OPEN-016/KF-028 embedded absolute data-pointer relocation class also covers the GAMEPLAY scene-asset pointer tables. `specs/rastan_direct_remap.json` `absolute_long_pointer_tables` now declares three per-stage/substage tables consumed by the gameplay scene loader R_c (arcade 0x059DE8) and its sub-loaders: arcade 0x059EC8 (palette, 6 entries) -> genesistan_palette_hook_59ad4; arcade 0x059C9A (PC080SN BG/tile patterns, 6 entries); arcade 0x059F1E (substage layout, 4 entries). Rule for identifying such a table: a run of embedded 24-bit ROM-address longwords indexed by a `movea.l #table,aN; movea.l (aN,dM),aN` loader, bounded by the first non-ROM-pointer longword (code or a pointed-to data block); relocate each in-window entry by the copy delta (+0x200). Distinguish from word/byte count tables (e.g. 0x05A0BC) and from code bytes that resemble pointers (0x30FC/0x4E75). Instruction-operand relocation remains a separate class and is unchanged.

**Use as prior.** Treat the original input-mirror bug and the later title-text crash as sequential findings in the same KF-028 arc: wiring the shim is required and correct, but it exposes a downstream title-text translation gap. Do not classify the `0x3bd66` crash as a `+4` layout-shift artifact: the renderer/table/descriptors are below the `0x700c6` insertion point, and Outcome A is not supported. Do not classify it as U1: `d0=65` is a hardcoded arcade immediate. Do not classify it as U2 for this crash: arcade descriptor data is valid and descriptors were correctly relocated. The root is U3: the arcade ROM blob moved by `+0x200`, descriptors such as arcade `0x3c246` became Genesis `0x3c446` with valid header `0x00c0914c | 0x0000 | "OTHERW..."`, but the embedded absolute descriptor-pointer table at Genesis `0x3bd7c` was not relocated. Its entries remain byte-identical to the arcade table, so `table[65]` stayed `0x0003c246` instead of `0x0003c446`. `postpatch_lenient.py` relocates absolute targets in instruction operands, not absolute longword pointers embedded in data tables. Treat the Build 0091 `0x00070794` crash as classification A, a hook behavior bug in `genesistan_hook_glyph_renderer_3bd48`, not as a shared-helper/staging-data fault: `.Lgr_store_cell` calls the shared FG-staging store helper `.Ltw_store_from_components_at_a2` at `runtime_genesis_pc 0x000707bc` without preloading `%a3=genesistan_pc080sn_tile_vram_lut`, `%a5=genesistan_pc080sn_attr_lut`, or `%a6=staged_fg_buffer` (WRAM `0x00ff501a`). Existing `genesistan_hook_text_writer_*` hooks, including `_3c550` at `tilemap_hooks.s:1090` and `_3c586` at `tilemap_hooks.s:1122`, satisfy that precondition before calling the helper; the glyph hook omits it, so `%a6` holds stale arcade-renderer context and the helper writes through the low odd address `0x00000f41`. The fix locus for this crash is the glyph hook register setup, not the shared store helper. Cross-reference KF-013 (VBlank/title text dispatch), KF-010 (FG maps to Plane A), OPEN-015 (crash-handler defects that required WRAM crash-record decoding), and OPEN-016 (embedded data-pointer relocation gap and Part 2 hook).

**Supersession notes.** Earlier KF-028 wording treated the intended shim caller as an open dropped-vs-never-wired question. Andy's call-site investigation classifies it as a never-wired Genesis-side gap: `rastan_direct_update_inputs` should be called from `_vblank_service` before the `jmp 0x3a208` handoff. The post-wiring address-error crash does not invalidate the shim fix; it exposes the unrelocated title-text descriptor-pointer table.

---


## KF-029 — Build 0094 FG cell-composition fix produces nonzero staged cells

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** BUILD_SPECIFIC (Build 0094, `rastan-direct`)
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** title producer `runtime_genesis_pc 0x0003ACAE`; first render call `runtime_genesis_pc 0x0003ACB6`; FG store `runtime_genesis_pc 0x00070794`; compose-site instructions `runtime_genesis_pc 0x000707DA`, `0x000707DC`, `0x000707E0`; FG range gate `runtime_genesis_pc 0x000707E6`; staged FG buffer `WRAM 0x00FF501A`
- **Source Documents:** docs/design/Cody_tilemap_hooks_rebuild_dependency_fix.md; states/traces/build_0094_title_producer_entry_window_trace_20260622_183218/title_producer_runtime_analysis.md; docs/design/Cody_fg_cell_composition_fix_build.md
- **Related Issues:** OPEN-016, OPEN-001
- **Last verified:** 2026-06-22 (Build 0094)

**Finding.** In Build 0094 (`dist/rastan-direct/rastan_direct_video_test_build_0094.bin`, SHA256 `558c88b39b359af7ee1f2cee1fa2318dde34b20ebfab7d25e25c0a18e0a819e2`), preserving `%d7` across `.Ltw_translate_attr` in `.Ltw_compose_d1_from_d0_d2` fixes the previously observed zero-cell mechanism. The produced ROM contains the Option B instructions at `0x707DA` (`move.w %d7,-(%sp)`), `0x707DC` (`bsr 0x70752`), and `0x707E0` (`move.w (%sp)+,%d1`). Runtime title-entry trace records producer `0x3ACAE` hit once, first render `0x3ACB6` hit once, FG range gate `0x707E6` hit 258 times, and FG store `0x70794` hit 258 times with `%a6=0x00FF501A` and in-buffer offsets. Build 0094 produced 213 nonzero composed `%d1` stores and 45 zero stores; Build 0092 had 258 stores all `%d1=0x0000`.

**Use as prior.** Store-time `%d1` at `0x70794` is a composed Genesis cell word, not raw ASCII. Do not expect literal text bytes at the store point. The 45 zero stores are a raw observed count only and are not classified as a defect without further evidence.

## KF-030 — `total_genesis_bytes_covered` is finalized address-map coverage, not per-helper semantic growth

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GLOBAL (current `rastan-direct` postpatch invariant model)
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** invariant `total_genesis_bytes_covered`; `genesis_only` wrapper segment `0x070000..len(rom_bytes)`
- **Source Documents:** docs/design/Cody_fg_cell_composition_fix_build.md; docs/design/Cody_tilemap_hooks_rebuild_dependency_fix.md; tools/translation/postpatch_startup_rom.py:643-683; tools/translation/postpatch_startup_rom.py:1958-1974; tools/translation/postpatch_startup_rom.py:1979-2006
- **Related Issues:** CLOSED-008, OPEN-016
- **Last verified:** 2026-06-22 (Build 0094)

**Finding.** `total_genesis_bytes_covered` is the sum of finalized address-map segment coverage and must equal final ROM length. In `rastan-direct`, the native helper area is represented as one `genesis_only` wrapper segment, not as per-helper symbol spans. Helper-local instruction growth does not move `total_genesis_bytes_covered` unless final ROM length changes.

**Use as prior.** Do not treat helper-local semantic growth as requiring a `total_genesis_bytes_covered` change. Verify the produced ROM's bytes/disassembly and branch references directly when helper-local code shifts inside the wrapper segment.

## KF-031 — Build 0093 stale assembler object recurrence and Build 0094 assembler rebuild hardening

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** BUILD_SPECIFIC (invalid Build 0093 / fixed Build 0094) / ERA_SPECIFIC (Makefile timestamp-based assembler rules before Build 0094 hardening)
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** stale object `apps/rastan-direct/out/tilemap_hooks.o`; edited source `apps/rastan-direct/src/tilemap_hooks.s`; Build 0093 SHA `4cc782854a40ccf3333ec8ecbe40f71a7617201576c124b60b49e5008fdd20e2`; Build 0094 SHA `558c88b39b359af7ee1f2cee1fa2318dde34b20ebfab7d25e25c0a18e0a819e2`
- **Source Documents:** docs/design/Cody_fg_cell_composition_fix_build.md; docs/design/Cody_tilemap_hooks_rebuild_dependency_fix.md; CLOSED_ISSUES.md (CLOSED-008 post-closure addendum)
- **Related Issues:** CLOSED-008, OPEN-016
- **Last verified:** 2026-06-22 (Build 0094)

**Finding.** Invalid Build 0093 linked a stale `tilemap_hooks.o` that was newer than the edited `tilemap_hooks.s`, producing a ROM byte-identical to Build 0092 despite the source edit. Build 0094 fixed this sibling build-integrity recurrence by forcing assembler object rebuilds and verified that the produced ROM contains the Option B compose-site instructions.

**Use as prior.** Classify this as a sibling recurrence of CLOSED-008's stale-input/determinism class, not the same original missing-`.incbin` prerequisite root. For assembler-source changes in this era, verify the produced ROM/disassembly rather than trusting source diffs alone.

## KF-032 — Raw copied arcade PC080SN writes must route through Genesis staging, not VDP mirror

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GENERAL (any verbatim-copied arcade write to PC080SN/PC090OJ hardware space)
- **Rediscovery Hazard:** HIGH (MAME-tolerant; BlastEm/Nomad/real-HW fatal — symptom hides on the common dev emulator)
- **Addresses:** Class-A confirmed instances — (1) PC080SN per-line scroll-RAM raw fill: raw primitive `runtime_genesis_pc 0x0003AF3C` called from `0x0003B15E`/`0x0003B16E` with A0=`HW_ADDRESS 0x00C04000`/`0x00C0C000` (Build 0106 HV-crash root cause); (2) story comma/special glyph: `runtime_genesis_pc 0x0003ACEA` = `arcade_pc 0x0003AAEA` (`arcade_copy` seg `0x03AB20..0x03AD00`), `move.w #0x2749,0x00C09172`, FG row17/col28, tile `0x2749 → slot 0x0039`.
- **Source Documents:** docs/design/Andy_build_0105_hv_counter_root_cause_fix_design.md; docs/design/Cody_build_0106_correction_taito_arcade_intent_paren_lut.md; docs/design/Cody_build_0106_c09172_writer_watchpoint.md; docs/design/Andy_build_0106_fixed_tile_findings_canonicalization.md
- **Related Issues:** OPEN-005, OPEN-018, OPEN-017
- **Last verified:** 2026-06-26 (Build 0106)

**Finding.** Verbatim-copied arcade `move.w`/`move.l` writes (and raw fill loops) targeting `HW_ADDRESS 0x00C00000..0x00C0FFFF` (PC080SN) or `0x00D00000..0x00D007FF` (PC090OJ) execute on Genesis as raw 68000 writes into VDP-mirror space. Because `(address & 0x1F)` can select the read-only HV-counter port (offset 0x08), strict targets fatal ("Illegal write to HV Counter port 8"); even when they don't crash, the cell never reaches Genesis staging and renders blank. These writes must route through the PC080SN/PC090OJ dispatch/staging path or a named site-specific staging helper, preserving arcade intent.

**Use as prior.** Do NOT fix by NOP/suppression, VDP-port sanitizer, suppressing 0xC00008, MAME-tolerance mimicry, or dropping the write unless arcade intent is proven irrelevant — route the intent to staging. Scan for sibling raw writes/fills; fixing one site commonly exposes the next (e.g. the C0C000 scroll clear and the inline title producer `0x0003B392`). This is the same class as the Build 0106 scroll-RAM HV crash and the story-comma write.

**Build 0107 validation (2026-06-27).** The routing model is VALIDATED on strict targets: routing four immediate-absolute raw FG writes through trampoline → `genesistan_hook_tilemap_fg_fill` (live LUT → FG staging → dirty → VBlank commit) fixed the story-page comma crash on BlastEm and real Genesis and made the comma render. Approved patch shape for an 8-byte `move.w #imm,(abs).L` site = byte-neutral 8-byte `jsr abs.l + nop`. Build 0107 SHA256 `4b4a588b1da2ccec6b31cac781bd53627993eaa6170ec013da56f349c99ef1e3`. Remaining raw-write shapes (register-absolute `0x3A92A`/`0x3D24C`; producer-loop `0x3B3CC`/`0x3B7F6`/`0x3B7F8`) are unrouted and tracked under OPEN-018.

## KF-033 — Low-code FG glyph/symbol LUT coverage gaps (routed but staged blank)

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** BUILD_SPECIFIC (Build 0106 / current LUT) but ROOT is TOOL-LEVEL (`precompute_pc080sn_tile_lut.py` mapping assumption — persists until the tool/LUT is fixed)
- **Rediscovery Hazard:** HIGH
- **Addresses:** affected arcade tile codes `0x0021,0x0022,0x0027,0x0028,0x0029,0x002C,0x002D,0x003F` (the 8 `TEXT_SPECIAL_GLYPH_MAP` keys); confirmed-failing subset `0x0022,0x0027,0x0028,0x0029,0x002C,0x003F`; LUT `build/pc080sn_tile_vram_lut.bin`; generator `tools/translation/precompute_pc080sn_tile_lut.py` (`extract_text_writer_tiles` + `TEXT_SPECIAL_GLYPH_MAP`); FG store `runtime_genesis_pc 0x00070952`; glyph renderer `0x0003BD48..0x0003BD7C` (patched_site, `arcade_pc 0x0003BB48`).
- **Source Documents:** docs/design/Cody_build_0106_correction_taito_arcade_intent_paren_lut.md; docs/design/Cody_build_0106_taito_magenta_cell_arcade_intent.md; docs/design/Andy_build_0106_fixed_tile_findings_canonicalization.md
- **Related Issues:** OPEN-001, OPEN-019, OPEN-020
- **Last verified:** 2026-06-26 (Build 0106; LUT/preload binaries inspected)

**Finding.** The Build 0106 glyph renderer can route a cell correctly and still stage blank when the direct tile LUT maps a low arcade glyph/symbol code to slot `0x0000`. Root cause: `precompute_pc080sn_tile_lut.py` applies `TEXT_SPECIAL_GLYPH_MAP` (0x21→0x2744 … 0x3F→0x274B) and registers only the **mapped** punctuation tiles (0x2744–0x274B), assuming the runtime applies the same 0x563CE mapping. Verified: the title preload contains low codes `0x20,0x23–0x26,0x2B,0x2E,0x2F,0x30–0x3E` but is missing **exactly** the 8 map keys; `LUT[0x0022/0x0027/0x0028/0x0029/0x002C/0x003F]=0x0000` while `LUT[0x2745..0x274B]=0x0035..0x003B`. Symptoms: missing `INSERT COIN(S)` parens; four missing small red TAITO cells. No strict crash (writes are routed); the staged value is blank.

**Use as prior.** Two sub-cases differ by byte-identity: **(a)** parens `0x0028/0x0029` are byte-identical to preloaded aliases `0x2747/0x2748` (slots 0x37/0x38) → fixable by adding the LUT entry alone (pattern already in VRAM). **(b)** TAITO low codes `0x0022/0x0027/0x002C/0x003F` are NOT byte-identical to their mapped tiles and have their own nonblank ROM patterns → may need preload/slot coverage **plus** LUT entries; do not assume LUT-only. `0x0021 ('!')` and `0x002D ('-')` are latent gaps (LUT=0, not yet observed failing).

## KF-034 — Rendered-cell audits require two-context coordinate reconciliation

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GENERAL (any audit comparing a Genesis rendered cell to arcade tilemap intent)
- **Rediscovery Hazard:** MEDIUM-HIGH
- **Addresses:** wrong-cell precedent BG `0x22CB..0x22CE`; correct magenta cells FG `(23,17)/(23,22)/(23,24)/(24,20)`; evidence `states/screenshots/build_106_missing_TAITO_logo_tiles_highlighted_in_magenta_hex_code_#ff00ff.png`
- **Source Documents:** docs/design/Cody_build_0106_taito_magenta_cell_arcade_intent.md; docs/design/Andy_build_0106_fixed_tile_findings_canonicalization.md
- **Related Issues:** OPEN-001
- **Last verified:** 2026-06-26 (Build 0106)

**Finding.** Genesis rendered-screen cells and arcade PC080SN tilemap cells require two independent transforms before comparison: (1) Build rendered screen → staged row/col via the Genesis display scroll/origin/title positioning; (2) arcade rendered title position → arcade PC080SN row/col via arcade PC080SN scroll/visible-area/title positioning. Both must be validated with adjacent visible anchor tiles. A naive pixel→row/col conversion on the wrong layer mis-located the missing TAITO cells onto the BG `0x22CB..0x22CE` block; the two-context method correctly resolved them to FG low-code glyphs.

**Use as prior.** Do not audit guessed cells from single-context pixel math. Always anchor against adjacent known-good cells in both contexts and confirm the layer (BG vs FG) before attributing a coverage/staging defect.

## KF-035 — Tile usage/preload audits must derive intent from arcade tilemap, not Genesis LUT/staging

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GENERAL (process guardrail for all tile usage/preload/coverage audits)
- **Rediscovery Hazard:** HIGH
- **Addresses:** original audit `docs/design/Cody_build_0095_arcade_title_tile_usage_audit.md`; generator `tools/translation/precompute_pc080sn_tile_lut.py`; blind-spot codes `0x0021,0x0022,0x0027,0x0028,0x0029,0x002C,0x002D,0x003F`
- **Source Documents:** docs/design/Andy_build_0106_fixed_tile_findings_canonicalization.md (§4 Task-1 verification)
- **Related Issues:** OPEN-001, OPEN-019, OPEN-020
- **Last verified:** 2026-06-26 (Build 0106; blind spot CONFIRMED)

**Finding.** The Build 0095 title tile-usage/preload audit was CONFIRMED blind to the low-code FG glyph cells via a dual mechanism: (i) it scoped the "red TAITO logo" to the BG block `0x5B0B2` geometry (codes `0x22CB..0x22CE`) and never audited the FG glyph-renderer path; (ii) it relied on the preload/LUT generator's coverage assertions, which embed `TEXT_SPECIAL_GLYPH_MAP` and silently drop the 8 raw low glyph codes (LUT=0). Standing rules: staging nonzero does not prove visual correctness; staging zero does not prove a tile is not preloaded; Genesis LUT results cannot be the only source of truth for arcade tile usage; cross-check arcade tilemap intent, VRAM/pattern table, rendered output, and writer evidence.

**Use as prior.** Tile usage/preload analysis must derive "what should render" from original arcade tilemap/runtime intent (and the actual runtime-staged cell codes), not solely from Genesis-side LUT results or staging values. A tool that remaps codes (e.g. punctuation mapping) can hide whole code classes from a coverage check.


## KF-036 — Arcade work-RAM helper reads must use the mapped Genesis WRAM base

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GENERAL (rastan-direct helpers/opcode replacements that read or write arcade work-RAM data)
- **Rediscovery Hazard:** HIGH (easy to confuse shifted code addresses with data/RAM address mapping)
- **Addresses:** arcade work-RAM `0x0010C000..0x00110000`; mapped Genesis WRAM base `0x00FF0000`; high-score NAME source arcade `0x0010C157..0x0010C165`; mapped source `0x00FF0157..0x00FF0165`; bad Build 0111 helper source `0x0010C1BF..0x0010C1CD`; generated work-RAM remap sites `arcade_pc 0x03AEEA/0x03AF04`; high-score hook `runtime_genesis_pc 0x000707A0`, source-base add at `0x000707CA`.
- **Source Documents:** docs/design/Cody_highscore_name_column_source_audit_build_0111.md; docs/design/Cody_build_0112_highscore_name_source_base_fix.md
- **Related Issues:** OPEN-001, OPEN-018, CLOSED-017
- **Last verified:** 2026-06-28 (Build 0112)

**Finding.** In `rastan-direct`, arcade work-RAM data is not read through literal `0x0010xxxx` addresses. The translated runtime maps the arcade work-RAM base `0x0010C000` to Genesis WRAM `0x00FF0000`; helpers that consume arcade work-RAM records must therefore use the mapped Genesis base plus the original arcade offset. Build 0111 violated this in `genesistan_hook_highscore_fg_producer` by reading from literal `0x0010C068 + src_off`, which matched prior Genesis build output but not original arcade intent. The correct Build 0112 source base is `0x00FF0000`; the NAME source bytes at `0x00FF0157..0x00FF0165` are `COB/THS/YAG/TKG/YTN`, matching the original arcade runtime source at `0x0010C157..0x0010C165`.

**Use as prior.** JSON/address-map correlation is authority for code address movement; it is not a license to compensate stable data/RAM sources for helper/code growth. A previous Genesis build matching another previous Genesis build is not proof of arcade fidelity. Anchor data-source helpers to original arcade runtime data and the mapped Genesis equivalent. The established sprite-helper idiom is the safe pattern for arcade work-RAM pointers: subtract the arcade work-RAM base (for example `0x00100000`) and add the offset to the live Genesis WRAM/A5 base, rather than preserving a literal arcade-space pointer.

## KF-037 — Opcode-replacement hooks must preserve fall-through control flow

- **Status:** ACTIVE
- **Confidence:** CONFIRMED
- **Applicability:** GENERAL (opcode replacements for instructions inside fall-through routines)
- **Rediscovery Hazard:** HIGH (hook effect can look correct while the suppressed tail silently blocks state progression)
- **Addresses:** high-score entry palette site `arcade_pc 0x0003AB00` / `runtime_genesis_pc 0x0003AD00`; hook `genesistan_palette_hook_03ab00`; suppressing `rts` at `runtime_genesis_pc 0x0003AD06`; required fall-through tail starts at `runtime_genesis_pc 0x0003AD08`; safe terminal siblings `0x059AD4`, `0x045DB8`, `0x03BA64`.
- **Source Documents:** docs/design/Cody_highscore_timer_expiry_evidence_v3_build_0108.md; docs/design/Andy_03ab00_palette_hook_fallthrough_restore_design.md; docs/design/Cody_palette_hook_fallthrough_suppression_scan_build_0108.md
- **Related Issues:** CLOSED-015, OPEN-001
- **Last verified:** 2026-06-27 (Build 0109)

**Finding.** A replacement hook must preserve both the replaced instruction's side effect and the original routine's control-flow contract. Build 0108 reached the high-score entry palette site (`runtime_genesis_pc 0x0003AD00`) and executed the palette hook, but the replacement tail `jsr genesistan_palette_hook_03ab00; rts` returned early and suppressed the arcade fall-through into `0x0003AD08`, preventing the high-score setup tail from running. Build 0109 restored the fall-through by changing only `0x0003AD06: rts -> nop`, preserving the palette hook while allowing the high-score tail to execute.

**Use as prior.** Before adding `rts` after an opcode-replacement hook, prove the original site was terminal. If the original instruction fell through into live logic, the replacement must fall through too. Sibling-scan before generalizing: the related palette-hook siblings inspected for this case were terminal/safe and did not need the same change.

## KF-038 — Long PC080SN BG C-window rows alias in the current 32-row Genesis BG staging model

- **Status:** OPEN (architectural follow-up)
- **Confidence:** CONFIRMED (Build 0115 item-description aliasing evidence) / STRONG (architectural interpretation)
- **Applicability:** BUILD_SPECIFIC (Build 0115 item-description page evidence) / POTENTIALLY_GENERAL (PC080SN virtual/tall tilemap behavior pending gameplay/demo evidence)
- **Rediscovery Hazard:** HIGH (symptom can look like text-writer, LUT, or VDP commit failure)
- **Addresses:** shared text-writer dispatcher `runtime_genesis_pc 0x000714C8`; item-description writer call `runtime_genesis_pc 0x0005623C`; BG fill helper `genesistan_hook_tilemap_bg_fill`; `FIRE SWORD` source destination `HW_ADDRESS 0x00C01428`; aliasing later row destination `HW_ADDRESS 0x00C03428`; aliased staging cell `WRAM 0x00FF4A2E`; adjacent surviving `I` cell `WRAM 0x00FF4A30`; staged scroll words `WRAM 0x00FF4012/0x00FF4014/0x00FF4016/0x00FF4018`
- **Source Documents:** docs/design/Cody_build0115_itemdesc_crash_scroll_evidence.md; states/traces/build_0115_itemdesc_crash_scroll_evidence_20260629_090111/native_events.log; states/traces/build_0115_itemdesc_crash_longcheck_20260629_090635/staged_bg_at_crash.bin
- **Related Issues:** OPEN-001, OPEN-022, OPEN-023, OPEN-024, KF-010, KF-032, KF-036
- **Last verified:** 2026-06-29 (Build 0115)

**Finding.** Build 0115's shared text-writer dispatcher successfully routes item-description text into Genesis BG staging: the six-caller producer-equivalence validation reported mismatch count `0`, and runtime evidence shows the item page reaches BG staging. However, the item-description page uses a longer PC080SN BG C-window address span than the current 32-row Genesis BG staging model preserves without aliasing. Later PC080SN BG rows can map to the same Genesis staging cells as earlier rows and overwrite them. This is a staging-geometry alias, not a dispatcher emission failure, LUT failure, or VDP commit failure.

**Concrete evidence.** The `F` in `FIRE SWORD` is emitted and staged correctly: the dispatcher records `DISPATCH_BG_ROUTE ... dest=00C01428 composed=00000046 code=0046 attr=0000`, followed by `BG_STAGING_STORE ... src_dest=00C01428 off=00000A14 eff=00FF4A2E cell=001C`. A later PC080SN BG row aliases into the same Genesis staging cell and clears it: `BG_STAGING_STORE ... src_dest=00C03428 off=00000A14 eff=00FF4A2E cell=0000`. Final/crash-time staging records `WRAM 0x00FF4A2E = 0x0000` while the adjacent `I` cell remains `WRAM 0x00FF4A30 = 0x001F`, producing `IRE SWORD`. The aliasing mechanism matches `genesistan_hook_tilemap_bg_fill`: after `(dest - ARCADE_PC080SN_CWINDOW_BASE_BG) >> 2`, the helper computes column with `andi.w #0x003F` and row with `lsr.w #6` then `andi.w #0x001F`, collapsing higher PC080SN rows into a 32-row staging space.

**Scroll evidence.** The item-page staged scroll values stayed zero in the captured window (`staged_scroll_x_bg=0`, `staged_scroll_x_fg=0`, `staged_scroll_y_fg=0`; the relevant staged scroll words remained zero), and no raw PC080SN X/Y scroll writes were observed (`RAW_PC080SN_YSCROLL_WRITE=0`, `RAW_PC080SN_XSCROLL_WRITE=0`). The Genesis VBlank scroll commit path is active, but item-page scroll values were zero in this trace. The visible row corruption is therefore staging-geometry aliasing first, not a nonzero scroll-offset explanation.

**Use as prior.** Do not rediscover `FIRE SWORD -> IRE SWORD` as a `genesistan_hook_textwriter_dispatch`, `0x565CE` substitution, `attr_lut`, VDP commit, or Build 0115 opcode-rebasing defect. The Build 0115 dispatcher remains validated and item text reaches BG staging. Do not globally change `bg_fill` row mapping without a design pass: making BG staging taller globally could break currently working 32-row-wrapping screens such as title/story/high-score. The item-description page appears to use PC080SN BG C-window addresses as a taller/longer text layout than current Genesis 32-row staging preserves; this may be item-description-specific, general PC080SN virtual tilemap behavior also used by gameplay level scrolling, or a missing scroll/window model where high rows should remain distinct until revealed by scroll. Gameplay/demo PC080SN evidence is required before selecting a representation.

## KF-039 — Arcade work-RAM absolute pointers map to Genesis WRAM via the A5 base 0x0010C000

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (arcade + Genesis runtime dumps; arcade disassembly; visual)
- **Applicability:** DURABLE mapping rule (rastan-direct); producer facts BUILD_SPECIFIC (Build 0149)
- **Rediscovery Hazard:** HIGH (treat as canonical prior unless contradicted by explicit evidence)
- **Addresses:** arcade A5 = `0x0010C000`; Genesis a5 = `0x00FF0000`; title high-score source arcade `0x0010C142` -> Genesis `0x00FF0142`; ranking table arcade `0x0010C140..0x0010C165` -> Genesis `0x00FF0140..0x00FF0165`; names at `0x00FF0157`; 0x3B802 hook `genesistan_pc090oj_hook_score_digit_3b802` (`0x00071D34`); clearer `genesistan_pc090oj_hook_target_59f5e` (`0x00071B84`); arcade `0x59F5E` clear base `0x00D00048` (record 9)
- **Source Documents:** docs/design/Andy_build_0149_title_highscore_coin_label.md; docs/design/Andy_build_0148_default_title_highscore.md
- **Related Issues:** OPEN-001, OPEN-024
- **Last verified:** 2026-07-09 (Build 0149)

**Finding.** Absolute arcade work-RAM pointers (`0x0010Cxxx`) held in translated data/record tables map to Genesis WRAM as `genesis = a5 + (pointer - 0x0010C000)` with runtime arcade A5 `0x0010C000` and Genesis a5 `0x00FF0000` (i.e. arcade `0x0010C000` -> Genesis `0x00FF0000`). Confirmed by the ranking table landing byte-identical at `0x00FF0140..0x00FF0165` (scores `31 27 00 …`, names COB/THS/YAG/TKG/YTN at `0x00FF0157`). The title high-score initialization is present and correct; the earlier "HIGH SCORE 00" defect was a producer read using region base `0x00100000` instead of the A5 base `0x0010C000` (off by `0xC000`, reading empty `0x00FFC142`). PC090OJ record clear/producer ranges expressed as arcade HW addresses map by record index: arcade `0x59F5E` clears 8 records from `0x00D00048` = record 9 (records 9..16), **not** records 0..7.

Reinforced Build 0151: `genesistan_hook_number_renderer_3c2e2` (arcade 0x3C2E2, BEST 5 SCORE/ROUND) had the same defect in a different guise -- it masked the descriptor's absolute source pointer with `& 0x0000FFFF` instead of subtracting `ARCADE_WORKRAM_A5_BASE`, reading 0x00FFCxxx zeros.

**Use as prior.** When translating an arcade routine that dereferences a `0x0010Cxxx` work-RAM pointer, subtract the A5 base `0x0010C000` (not the region base `0x00100000`) before adding Genesis a5. When translating a PC090OJ producer/clearer that addresses records by HW address, derive the record index as `(HW - 0x00D00000) / 8` rather than assuming a 0-based range. Do not seed default score/high-score values: the arcade high-score init already populates the Genesis table correctly.

---

## KF-040 — Gameplay Stage 1 BG is painted at scene entry via the item-page strip-blit hook; the raw column writers are dynamically dead; the boundary is scene selection / pattern residency

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (arcade + Genesis Build 0153 runtime taps; disassembly; screenshot)
- **Applicability:** DURABLE ownership/boundary rule (rastan-direct gameplay BG); producer facts BUILD_SPECIFIC (Build 0153)
- **Rediscovery Hazard:** HIGH (contradicts the intuitive "raw C-window writer" reading of the static address_map)
- **Addresses:** arcade raw BG writer loop `0x055C7A` (stores `0x055C80`/`0x055C94`) via producer `0x055C68`; arcade raw FG writer loop `0x0559B2` (stores `0x0559B8`/`0x055A06`); item-page BG strip-blit `genesistan_hook_itempage_strip_blit` runtime `0x716CA` installed at arcade `0x055C5E`/Genesis `0x055E5E`; descriptor walker arcade `0x03951C`; tile sources `0x00D11C`/`0x00D91C`/`0x00F11C` (arcade) -> `0x00D31C…` (+0x200); `staged_bg_buffer` `0x00FF409E`; `genesistan_current_scene_id` `0x00FF7474`; scene detector in `genesistan_hook_tilemap_plane_a`/`_fg` (`0x00070248`/`0x000703EA`, keyed on `a5@0x10A0`/`a5@0x10A4`)
- **Source Documents:** docs/design/Andy_gameplay_pc080sn_output_analysis.md; states/traces/build_0154_gameplay_pc080sn_output/
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-10 (Build 0153)

**Finding.** On the arcade, the Stage 1 outside BG/FG plane is painted **once at state `2/2/4`** (not during steady gameplay `2/3/0`, where there are zero PC080SN C-window writes) by raw column writers `0x055C7A` (BG) / `0x0559B2` (FG), each store firing 4096× = 64 cols × 64 rows, walking descriptor `0x03951C` with tile sources `0xD11C`-family (step `0x800`). On Genesis Build 0153 these raw writer instruction sites are statically `arcade_copy` but **dynamically dead**: no `0x055Bxx–0x055Fxx` PC ever writes the VDP, and producer `0x055E68` never stores its dest-cursor `0xFF10F8`. Instead the **already-hooked item-page BG strip-blit** (`0x716CA`, at `0x055E5E`) runs with a **relocated** source `0xD31C` (=`0xD11C`+0x200) and stages BG cells through `genesistan_hook_tilemap_bg_fill`: `staged_bg_buffer` is fully populated (2048/2048) and committed (`bg_row_dirty=0`). However the staged plane is a **uniform `0x4000`** (tile index 0 + priority), because `genesistan_current_scene_id` stays `0` (title), `load_scene_tiles(1)` never runs, the gameplay tile patterns are not resident, and the tile→VRAM LUT collapses the gameplay code words to tile 0. The Genesis scene detector lives only in the descriptor-hook path (`plane_a`/`fg`, keyed on `a5@0x10A0/0x10A4`), which is not exercised by the item-page/column gameplay path, and the descriptor slots never hold a gameplay-range (`0x56A22..0x570C2`) pointer during entry.

**Use as prior.** Do **not** treat the gameplay BG blank as an "untranslated raw PC080SN writer" problem: the raw writers do not execute on Genesis and the BG cells already stage+commit. The Stage 1 BG boundary is **scene selection + tile-pattern residency + real-content staging** — i.e. why the item-page branch stages a uniform tile-0 plane, why the arcade column producer `0x055C68` is bypassed on Genesis, and how to trigger `load_scene_tiles(1)` naturally from a proven authoritative gameplay scene pointer (which is not yet identified). When auditing a "raw C-window writer" flagged only by static `arcade_copy` mapping, confirm at runtime that the site actually executes on Genesis before treating it as a live gap.

---

## KF-041 — Gameplay tile preload/LUT model the wrong source; the runtime Stage 1 BG producer reads 0xD11C/0x03951C (codes 0x04A6+), of which the LUT maps ~0

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (offline reproduction over Build 0153 ROM + shipped LUT; generator source read; runtime taps)
- **Applicability:** DURABLE pipeline/source-model rule (rastan-direct gameplay tile preload + LUT); code specifics BUILD_SPECIFIC (Build 0153)
- **Rediscovery Hazard:** HIGH (the intuitive "select the gameplay scene / run load_scene_tiles(1)" fix does nothing here)
- **Addresses:** runtime producer `genesistan_hook_itempage_strip_blit` `0x716CA` at arcade `0x055C5E`; source slot `0xFF1100` = `0xD31C` (arcade `0xD11C`+0x200); descriptor walker arcade `0x03951C` (6-byte entries); runtime Stage 1 codes `0x04A6`-family; generator `tools/translation/precompute_pc080sn_tile_lut.py` `GAMEPLAY_TABLE_START=0x5635E`; `genesistan_scene_a0_ranges` gameplay `0x00056A22..0x000570C2` (block-model, ROM@`0x56C22`=`00AD`-family); global `genesistan_pc080sn_tile_vram_lut`; `load_scene_tiles` (`scene_load.s`)
- **Source Documents:** docs/design/Andy_gameplay_scene_selection_analysis.md; states/traces/build_0154_gameplay_scene_selection/repro_lut_mismatch.py
- **Related Issues:** OPEN-017
- **Related Findings:** KF-040
- **Last verified:** 2026-07-10 (Build 0153)
- **Resolution (Build 0154):** RESOLVED for Stage 1 outside. `tools/translation/precompute_pc080sn_tile_lut.py` now models the runtime producer (`collect_runtime_gameplay_sources` walks descriptor `0x3951C` → 5 blocks `0xD11C..0xF91C`, replacing the misclassified `0x5635E` model); the global LUT now maps all 854 runtime codes `0x04A6..0x07FB` (was 1/854), and `genesistan_hook_itempage_strip_blit` gained a producer-source scene-selection preamble that calls `load_scene_tiles(1)` when the strip source is in `[0xD31C,0xFB1C)`. Build 0154 renders Stage 1 (`scene_id=1`, staged BG 277 distinct values). The durable rule below still holds as prior for any future producer-vs-generator source-model audit.

**Finding.** The Genesis gameplay tile-preload manifests, the global `pc080sn_tile_vram_lut`, and
`genesistan_scene_a0_ranges` are all generated from a **block-write descriptor source model** (generator
`GAMEPLAY_TABLE_START=0x5635E`, gameplay source range `0x56A22..0x570C2`, tile codes in the `0x00AD` family). The
**runtime Stage 1 BG producer does not use that model**: it is the general BG column/strip producer at arcade
`0x055C5E` (Genesis hook `0x716CA`), which reads source slot `0xFF1100` = `0xD31C` (arcade `0xD11C`+0x200,
correctly relocated by Build 0153) via descriptor walker `0x03951C`, emitting codes in the `0x04A6` family. A
controlled offline reproduction over the real Build 0153 ROM + shipped LUT (`cell = word@(base+row*32+col*2)`,
bases `0xD31C/0xDB1C/0xF31C`, 16 cols × 64 rows) yields `distinct_codes=834`, `covered=1/834`, `lut_nonzero=18
(0%)`. Because `genesistan_hook_tilemap_bg_fill` selects the Genesis tile index as `tile_vram_lut[code & 0x3FFF]`
— from the **LUT, not from VRAM residency** — these codes stage as tile 0 (`0x4000` + priority), giving the
uniform blank plane (see KF-040) **regardless of `load_scene_tiles`**.

**Use as prior.** Do **not** attempt to fix the gameplay BG by only "selecting scene 1" / running
`load_scene_tiles(1)`: pattern residency does not change the LUT, and the LUT maps ~0/834 of the runtime codes.
The gameplay tile-analysis pipeline (`precompute_pc080sn_tile_lut.py`) must first be **re-modeled around the
runtime producer's source family** (`0xD11C` + descriptor `0x03951C`, codes `0x04A6…`) so the regenerated
manifest + global LUT cover those codes; then a producer-source scene selector can drive `load_scene_tiles(1)`
naturally. When a scene manifest/LUT appears not to cover a producer's tiles, verify the generator's **source
model matches the producer's runtime source pointer**, not a statically-plausible descriptor range.

---


## Deferred Candidates Appendix

**This appendix is NOT canonical priors. Entries here are pre-canonical observations that did not meet promotion criteria at the time of the most recent curation pass. They may be promoted, refined, or rejected in future curation passes.**

**Do NOT treat appendix entries as priors for current investigations. They are tracked epistemic uncertainty, not established system behavior.**

Each deferred entry uses a lighter format than canonical KF entries: short statement, source citation, deferral reason. No confidence ratings, no applicability scopes, no rediscovery hazard flags — those classifications would imply canonization, which deferred entries explicitly lack.

### DEF-001 — Address-map non-ROM hardware-address reverse-lookup classification

Source: docs/design/Andy_address_map_artifact_design.md (§7.3, §8 example 5)

Candidate ID (from Task 1): MEMORY-04

Statement: Reverse-lookup classification in the cited design treats hardware-space runtime addresses (example `0xC09EA0`) as non-ROM/unmapped-to-arcade rather than translated arcade code addresses.

Deferral reason: Single-source design-doc classification semantics may evolve with `address_map.json` revisions; defer until corroborated by independent operational evidence or contradiction testing.


## KF-042 — Data-register pointer-literal not relocated by postpatch shift; Stage-1 tilemap pass selector a5@0x10A8 became 0x80 (FG) instead of 0x00 (BG)

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (arcade + Genesis runtime taps; ROM byte proof; build-verified fix Build 0159)
- **Applicability:** DURABLE relocation rule (rastan-direct); reinforces KF-039
- **Rediscovery Hazard:** HIGH
- **Addresses:** arcade `0x503CE` `movel #0x00050F6B,d0` (pass-seq table base) NOT relocated; sibling `0x503BC` `moveal #0x00050EE0,a1` WAS (-> 0x000510E0). Genesis ROM[0x050F6B]=0x80 vs relocated ROM[0x05116B]=0x00 (arcade ROM[0x050F6B]=0x00). Selector `a5@0x10A8` = arcade 0x10D0A8 / Genesis 0xFF10A8 (also PC080SN_DESC_REBUILD_OUT). Fix: opcode_replace 0x503CE 203C00050F6B -> 203C0005116B (Build 0159).
- **Source Documents:** docs/design/Andy_build0159_collision_producer_selection.md; docs/design/Andy_build0159_pass_selector_relocation.md
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-11 (Build 0159)

**Finding.** The postpatch shift-relocation only adjusts abs.l control-transfer/LEA operands (opcodes 0x4EB9/0x4EF9/LEA abs.l via `maybe_shift_abs_long_expected_bytes`). An absolute code/data pointer loaded into a DATA register via `movel #imm,Dn` (opcode 0x203C) is NOT recognized and is left un-shifted, even when its address-register sibling (`moveal #imm,An`) IS relocated. At arcade 0x503CE the PC080SN pass-sequence table base `#0x00050F6B` was left raw, so on Genesis `a5@0x10C6` landed 0x200 too low and the desc-rebuild set the Stage-1 tilemap PASS SELECTOR `a5@0x10A8` to 0x0080 (FG branch) instead of 0x0000 (BG). The arcade always selects BG (a5@0x10A8==0). This mis-selection is the upstream cause of the dead BG collision producer and drove Build 0155's FG staging to be triggered by the bug. Build 0159 relocates the literal (byte-neutral); dispatch is now 100% BG, matching arcade.

**Use as prior.** When an arcade routine loads a `[0,0x60000)` code/data pointer via `movel #imm,Dn` (or any data-register immediate), the postpatch will NOT relocate it; check for un-relocated `#imm` siblings of relocated `moveal #imm,An` loads and rebase them +0x200 (Genesis) via byte-neutral opcode_replace. Consequence to watch: fixing such a selector can bypass hooks (e.g. Build 0155 FG staging) that were built to accommodate the bug — re-anchor them to the corrected path.

---


## KF-043 — Arcade sprite palette bank 51 is produced only into the source buffer (0x10D600), not palette RAM; hook_3ba64 skipped it, blacking Genesis CRAM line 3

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (arcade + Genesis runtime taps; build-verified fix Build 0161)
- **Applicability:** DURABLE palette-ownership rule (rastan-direct)
- **Rediscovery Hazard:** HIGH
- **Addresses:** arcade sprite-palette source buffer 0x0010D600..0x0010D67F (Genesis a5@0x1600 = 0x00FF1600); bank 48 @0x10D600->0xFF1600, bank 51 @0x10D660->0xFF1660. Arcade producer 0x3BA64 (Genesis hook `genesistan_palette_hook_3ba64` @0x71996). Genesis CRAM: bank48->line2, bank51->line3.
- **Source Documents:** docs/design/Andy_build0161_sprite_palette_source_population.md; docs/design/Andy_build0161_sprite_bank_palette_chunk_routing.md; docs/design/Andy_build0161_gameplay_palette_cram_ownership.md
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-12 (Build 0161)

**Finding.** Arcade routine 0x3BA64 (a palette converter/writer) is called with different a0 destinations: bank 48 is written to arcade palette RAM 0x200600 (a direct write), but **bank 51 is written ONLY to the sprite-palette SOURCE buffer 0x10D660** (a5-relative, Genesis 0xFF1660), then a generic memcpy (0x3A2D0) copies 0x10D600->0x200600 (arcade palette RAM). On Genesis, `hook_3ba64` (replacing 0x3BA64) only stages writes whose a0 is in the palette-RAM range 0x200000..0x200FFF; for the bank-51 source-buffer write (a0=0xFF1660) it skips, and the memcpy destination 0x200600 is unmapped. So arcade bank 48 reached Genesis CRAM line 2 (BG visible) but bank 51 never reached line 3 -> gameplay FG (FG_PLANE_ATTR_HI->line3) and sprites/Rastan were black. Build 0161 fix: in hook_3ba64, stage the bank-51 source-buffer writes (a0 in 0xFF1660..0xFF167F) directly to staged line 3 via the existing xBGR->CRAM path; line 3 populates with 15 converted colors, frontend/line-2/lines-0-1 unaffected.

**Use as prior.** A Genesis CRAM line can be black even though its arcade bank is populated, if the arcade writes that bank to a WRAM source buffer (later memcpy'd to palette RAM) rather than directly to palette RAM -- and the palette hook only stages direct palette-RAM writes. Check whether a palette bank is produced via a source-buffer + memcpy path; if so, stage the source-buffer write directly (a5-relative dest is rebased WRAM, valid on Genesis). No hardcoded colors.

**Build 0162 follow-up.** The same empty source buffer also caused a destructive clobber: `hook_45dae`'s bank-0 chunk (a1=0x200000) copies the source buffer 0x00FF1600 -> staged lines 0-3, and on Genesis (empty source) it ZEROED lines 0/1 that `hook_3ba64` had correctly staged from the arcade direct palette-RAM writes of banks 0/1. Fix (Build 0162): `hook_45dae` skips writing ZERO converted values (advancing the staged slot positionally), so the empty source no longer clobbers the real palette. All four gameplay CRAM lines then populate.

---

## KF-044 — Raw arcade-WRAM immediate destination literals (movea.l/move.l #imm) are not rebased; Genesis producers using them write ROM (dropped), so their WRAM blocks stay empty

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (arcade + Genesis Build 0163 runtime write-taps; static disasm of writer sites)
- **Applicability:** DURABLE relocation rule (rastan-direct) — WRAM producer path
- **Rediscovery Hazard:** HIGH
- **Addresses:** player PC090OJ source block arcade `0x0010D1B2..0x0010D241` (A5+0x11B2) = Genesis `0x00FF11B2..0x00FF1241`. Base-literal loader sites (`movea.l #0x0010D1B2,An`, opcodes 0x207C/0x227C): `0x51E00, 0x5288C, 0x52A6C, 0x54074, 0x5430C, 0x5457A, 0x545BA, 0x547C8`. Executing writer PCs (arcade→Genesis +0x200): `0x5471E→0x5491E, 0x544DE→0x546DE, 0x545D6→0x547D6, 0x54530→0x54730, 0x54724→0x54924`. Record-offset literals: `0x10D1D2/1F2/212/2A8/2C8/338/420`. Broader residue: **61** raw-WRAM immediates in [0x10C000,0x110000), incl. palette `0x10D600`×6, collision `0x10DE00`.
- **Source Documents:** docs/design/Andy_player_source_block_population_fix_attempt.md
- **Related Issues:** OPEN-017
- **Related Findings:** KF-039 (arcade WRAM base 0x10C000→0xFF0000), KF-042 (pass-selector `movel #imm,Dn` not rebased), KF-043 (palette source buffer)
- **Last verified:** 2026-07-13 (Build 0163 baseline)

**Finding.** The postpatch relocation only shifts code-region absolute operands (0x4EB9/0x4EF9/LEA abs.l in [0,0x60000)). It does NOT rebase WRAM immediate operands (arcade [0x10C000,0x110000) → Genesis 0xFF0000..). The player source-block writers compute the destination base with raw immediates `movea.l #0x0010D1B2,An` (0x207C/0x227C), and read control fields via A5-relative (correct). On Genesis these writers execute (verified: writer PCs = arcade+0x200) but store to raw `0x10D1B2` = ROM (unmapped for writes) → dropped. Genesis `0x00FF11B2` stays all-zero, so the downstream `0x041F5E`/`pc090oj_workram_block_sprites` copy has nothing to move and the player/Rastan cluster never reaches sprite records. Same class as the pass-selector immediate (KF-042) but for `movea.l`, and the same root as the palette/collision raw-literal producers.

**Use as prior.** When a Genesis WRAM block is unexpectedly empty, check whether its arcade producer loads the destination as a raw WRAM immediate (`movea.l/move.l #imm` in [0x10C000,0x110000)). If so the write silently hits ROM on Genesis. The bounded per-site remedy is an `opcode_replace` on that immediate (`0x0010xxxx→0x00FFxxxx`, byte-neutral) as Build 0158 did for one literal (`0x10C016→0xFF0016`) and KF-036 did for the item-page descriptor block (`0x558C8..0x55C68`). Do NOT fix a downstream destination-record remap while the source block is still empty.

**Build 0164 update — a BLANKET systemic rebase is UNSAFE; the player source block is un-fixable by literal rebase.** A postpatch pass (`rewrite_wram_immediate_literals_in_scan_windows`, spec `wram_immediate_relocation`) was implemented to rebase all MOVE.L/MOVEA.L #imm operands in a WRAM value window by +0x00EE4000 (mechanically correct: 55 sites/28 literals, 0 anomalies, verified in-ROM). But **enabling it regresses gameplay progression**: rebasing even *only* the player source block `0x10D1B2` freezes the game before player spawn (writerExec 561→0; producer frozen at F480 vs progressing to F536 in Build 0163). Cause: the `0x10D1B2` block is read/initialised pre-spawn by non-player-cluster routines — reader `0x51E00` (`movea.l #0x0010D1B2,a1; move.w a1@,…`), writer/init `0x5288C`/`0x52A6C` (`move.w #5,a0@+`) — which on Genesis alias ROM (constant reads / dropped writes); the mis-ported transition logic only advances in that ROM-aliased state, so zero-initialised WRAM hangs it. There are also NO a5-relative gameplay writers to `0xFF11B2` (only startup-zeroing 0x03B102/0x03A4D4). **Conclusion: the player source cannot be populated by literal rebasing; safe WRAM rebases must stay per-site opcode_replace on vetted addresses.** The pass is kept in the tree but GATED OFF (`enabled:false`). Populating the player source requires first resolving the pre-spawn ROM-alias dependency on `0x10D1B2` (trace 0x51E00/0x5288C/0x52A6C + a5-base in the F480–F536 window). The paired 0x041F5E destination-record split (A5+0x11B2→records 120..137, A5+0x0170→92..95) shipped in Build 0164 and is correct but inert until the source populates.

---

---

### DEF-002 — Populated VDP internals can coexist with blank composed output

Source: OPEN_ISSUES.md (OPEN-001 summary)

Candidate ID (from Task 1): VDP-01

Statement: In the cited OPEN-001 evidence window, CRAM/pattern internals were reported populated while composed game output remained effectively blank.

Deferral reason: OPEN-003 emulator disagreement remains unresolved; defer canonization until evidence convergence or independent corroboration resolves the conflict.

---

### DEF-003 — All-zero Plane A/B nametable capture in OPEN-001 evidence

Source: OPEN_ISSUES.md (OPEN-001 Build 58b evidence)

Candidate ID (from Task 1): VDP-02

Statement: The cited Build 58b nametable captures reported Plane A (`0xE000..0xEFFF`) and Plane B (`0xC000..0xCFFF`) as all `0x0000` in that evidence run.

Deferral reason: This is build-era observation data; defer until re-verified against current canonical Build 0077 runtime-state captures.

---

### DEF-004 — Palette conversion precomputed offline; runtime direct CRAM DMA

Source: AGENTS.md (Palette Architecture section)

Candidate ID (from Task 1): VDP-03

Statement: The architecture note states palette conversion is precomputed offline into ROM and runtime palette load is direct CRAM DMA copy.

Deferral reason: Current support is primarily architecture-intent documentation rather than direct runtime corroboration artifact in this curation pass; defer until independently corroborated in runtime evidence.

---

### DEF-005 — MAME vs Exodus runtime-state disagreement (OPEN-003)

Source: OPEN_ISSUES.md (OPEN-003)

Candidate ID (from Task 1): DIAG-05

Statement: OPEN-003 records unresolved disagreement between MAME-captured runtime evidence and Exodus-observed runtime behavior for overlapping investigation scopes.

Deferral reason: Disagreement is still open and unconverged; defer canonical promotion until OPEN-003 is resolved or an independent reconciliation artifact lands.
