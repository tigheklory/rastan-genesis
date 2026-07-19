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

## KF-038 — Long PC080SN BG/FG C-window rows alias in current 32-row Genesis staging models

- **Status:** OPEN (architectural follow-up)
- **Confidence:** CONFIRMED (Build 0115 item-description aliasing evidence; Build 0169 Stage 1 gameplay BG terrain aliasing evidence; Build 0170 gameplay tall-BG candidate validation; Build 0171 rolling BG projection validation; Build 0172 gameplay FG 64-row parity validation) / STRONG (architectural interpretation)
- **Applicability:** GENERAL_FOR_PROVEN_LONG_PC080SN_PATHS (item-description page and Stage 1 gameplay BG/FG evidence) / PARTIALLY_IMPLEMENTED_FOR_STAGE1_GAMEPLAY_OPENING (Builds 0170/0171 BG, Build 0172 FG candidate) / ARCHITECTURAL_FOLLOWUP (representation design still required before global change)
- **Rediscovery Hazard:** HIGH (symptom can look like text-writer, LUT, or VDP commit failure)
- **Addresses:** shared text-writer dispatcher `runtime_genesis_pc 0x000714C8`; item-description writer call `runtime_genesis_pc 0x0005623C`; Stage 1 item-strip producer `genesistan_hook_itempage_strip_blit` / `runtime_genesis_pc 0x00071878`; BG fill helper `genesistan_hook_tilemap_bg_fill` / store `runtime_genesis_pc 0x00070840`; gameplay FG source-column helper `genesistan_stage_fg_src_column`; FG tall fill helper `genesistan_hook_tilemap_fg_fill_tall`; FG projection helper `vdp_project_fg_tall_if_dirty`; `FIRE SWORD` source destination `HW_ADDRESS 0x00C01428`; aliasing later row destination `HW_ADDRESS 0x00C03428`; aliased staging cell `WRAM 0x00FF4A2E`; adjacent surviving `I` cell `WRAM 0x00FF4A30`; Stage 1 source pointer `genesis_rom_offset/runtime_source 0x0000D31C`; Stage 1 BG dest cursor `HW_ADDRESS 0x00C00000`; Stage 1 FG C-window base `HW_ADDRESS 0x00C08000`; Stage 1 sample cells including `WRAM 0x00FF441E` (`row 7 col 0`) and `WRAM 0x00FF4C1E` (`row 23 col 0`); Build 0172 `staged_fg_buffer = WRAM 0x00FF70A6`, `staged_fg_tall_buffer = WRAM 0x00FF80A6`; staged scroll words `WRAM 0x00FF4012/0x00FF4014/0x00FF4016/0x00FF4018`
- **Source Documents:** docs/design/Cody_build0115_itemdesc_crash_scroll_evidence.md; states/traces/build_0115_itemdesc_crash_scroll_evidence_20260629_090111/native_events.log; states/traces/build_0115_itemdesc_crash_longcheck_20260629_090635/staged_bg_at_crash.bin; docs/design/Cody_build0170_stage1_bg_source_window_trace.md; states/traces/build0170_stage1_bg_source_window_trace_20260714_182717/genesis_transition_snapshots.csv; docs/design/Cody_build0170_tall_bg_representation_candidate.md; states/traces/build0170_tall_bg_validation_20260714_193346/build0170_tall_bg_snapshots.csv; docs/design/Cody_build0171_tall_bg_projection_rowbase_candidate.md; states/traces/build0171_tall_bg_projection_rowbase_20260714_200031/build0171_rowbase_samples.csv; docs/design/Cody_build0172_fg_64row_parity_candidate.md; states/traces/build0172_fg64_validation_20260715_181940/build0172_fg64_samples.csv; states/traces/build0172_fg64_validation_20260715_181940/build0172_fg64_summary.log
- **Related Issues:** OPEN-001, OPEN-022, OPEN-023, OPEN-024, KF-010, KF-032, KF-036
- **Last verified:** 2026-07-15 (Build 0172 gameplay FG 64-row parity candidate validation)

**Finding.** Build 0115's shared text-writer dispatcher successfully routes item-description text into Genesis BG staging: the six-caller producer-equivalence validation reported mismatch count `0`, and runtime evidence shows the item page reaches BG staging. However, the item-description page uses a longer PC080SN BG C-window address span than the current 32-row Genesis BG staging model preserves without aliasing. Later PC080SN BG rows can map to the same Genesis staging cells as earlier rows and overwrite them. This is a staging-geometry alias, not a dispatcher emission failure, LUT failure, or VDP commit failure.

**Concrete evidence.** The `F` in `FIRE SWORD` is emitted and staged correctly: the dispatcher records `DISPATCH_BG_ROUTE ... dest=00C01428 composed=00000046 code=0046 attr=0000`, followed by `BG_STAGING_STORE ... src_dest=00C01428 off=00000A14 eff=00FF4A2E cell=001C`. A later PC080SN BG row aliases into the same Genesis staging cell and clears it: `BG_STAGING_STORE ... src_dest=00C03428 off=00000A14 eff=00FF4A2E cell=0000`. Final/crash-time staging records `WRAM 0x00FF4A2E = 0x0000` while the adjacent `I` cell remains `WRAM 0x00FF4A30 = 0x001F`, producing `IRE SWORD`. The aliasing mechanism matches `genesistan_hook_tilemap_bg_fill`: after `(dest - ARCADE_PC080SN_CWINDOW_BASE_BG) >> 2`, the helper computes column with `andi.w #0x003F` and row with `lsr.w #6` then `andi.w #0x001F`, collapsing higher PC080SN rows into a 32-row staging space.

**Build 0169 gameplay extension.** Stage 1 gameplay proves the same mechanism outside the item-description page. In `docs/design/Cody_build0170_stage1_bg_source_window_trace.md`, the item-strip producer starts from expected gameplay source `0x0000D31C`, BG destination cursor `0x00C00000`, and attr `0x0002`; it then writes a 64-row PC080SN column through `genesistan_hook_tilemap_bg_fill`. The correct visible cell `YELLOW_2_16` (`row 7 col 0`) briefly stages source raw tile `0x050C` via LUT slot `0x00D3` as word `0x40D3`, then source row `39` (`row+32`) raw tile `0x06BB` maps to LUT slot `0x0281` and overwrites the same Genesis staging cell as `0x4281`. Likewise `BLACK_2_0` (`row 23 col 0`) should stage raw `0x0602` / slot `0x01C8`, but row `55` (`row+32`) raw `0x0694` / slot `0x025A` overwrites it as final word `0x425A`. This proves Stage 1 terrain is using a long/tall PC080SN BG column that the current 32-row staging model cannot preserve.

**Build 0170 implementation evidence.** Build 0170 implements a gameplay-only tall-BG representation for the proven Stage 1 item-strip source family: sources in `[0xD31C,0xFB1C)` write through `genesistan_hook_tilemap_bg_fill_tall` into `staged_bg_tall_buffer` (64x64 words), while non-gameplay paths keep the 32-row `genesistan_hook_tilemap_bg_fill` path. VBlank `vdp_project_bg_tall_if_dirty` is gated by `genesistan_current_scene_id==1`; it uses the existing Build 0166 `-raw + 8` vertical-scroll convention only to choose the 0..31 vs 32..63 half, then copies that half into the existing `staged_bg_buffer` and marks BG rows dirty for the normal Plane-B commit. Validation in `states/traces/build0170_tall_bg_validation_20260714_193346/build0170_tall_bg_snapshots.csv` shows the Stage 1 post-landing frame `820` retains `YELLOW_2_16=0x40D3`, `BLACK_2_0=0x41C8`, and `MOUNTAIN_8_9=0x4073` in projected staging, while former alias rows remain preserved only in tall backing (`row39=0x4281`, `row55=0x425A`, `row32=0x422C`). This validates the representation for the sampled Stage 1 opening window but does not close broader long-BG handling for every screen or later scroll window.

**Build 0171 projection evidence.** Build 0171 corrects the Build 0170 projection from a 0/32 half-buffer select to a rolling 64-row visible-window projection. `vdp_project_bg_tall_if_dirty` now derives `projection_row_base = (((-staged_scroll_y_bg + 8) & 0x01FF) >> 3) & 0x3F`, copies each visible row from `(projection_row_base + visible_row) & 0x3F`, and gameplay BG VSRAM commit applies only the pixel residual `& 0x0007` so the VDP does not reapply the tile-row portion of scroll. Validation in `states/traces/build0171_tall_bg_projection_rowbase_20260714_200031/` compares the projected 32-row staging against the corresponding tall-buffer rows: Build 0170 matched `24/204` sampled rolling-row cells, while Build 0171 matched `192/204`; the remaining Build 0171 mismatches are confined to frame `751`, where post-frame sampling sees next-frame scroll before the next projection. Screenshots show sky/clouds preserved and mountain bands materially more coherent, while black horizontal gap / missing ground remains a separate unresolved visual boundary.

**Build 0172 FG parity evidence.** Build 0172 proves the Stage 1 gameplay FG source path had the same class of row-depth preservation gap. Before Build 0172, `genesistan_stage_fg_src_column` folded the gameplay source family through `FG_PRODUCER_SEG_COUNT=8` and the legacy 32-row `genesistan_hook_tilemap_fg_fill`, preserving only rows `0..31` even though the source family provides 16 four-row segments (64 rows). Build 0172 adds scene-1-only `genesistan_hook_tilemap_fg_fill_tall`, `staged_fg_tall_buffer` (64x64 words), `fg_tall_dirty`, and `vdp_project_fg_tall_if_dirty`; gameplay FG vertical scroll now commits only the residual pixel offset `& 0x0007`, matching the Build 0171 BG projection ownership split. Runtime validation in `states/traces/build0172_fg64_validation_20260715_181940/` shows the path is live: by gameplay frame `571`, `fg_tall_nz=4032` and `fg_nz=2016`; steady frames `820/900/1081/1400` preserve `fg_tall_nz=4032`, and sampled projected FG cells equal their corresponding tall-buffer source rows. Visual output changed substantially but is not arcade-correct yet: repeated green/foreground-looking tiles appear where Build 0171 showed missing lower foreground, while black/blank bands and other gameplay issues remain separate unresolved boundaries.


**Scroll evidence.** The item-page staged scroll values stayed zero in the captured window (`staged_scroll_x_bg=0`, `staged_scroll_x_fg=0`, `staged_scroll_y_fg=0`; the relevant staged scroll words remained zero), and no raw PC080SN X/Y scroll writes were observed (`RAW_PC080SN_YSCROLL_WRITE=0`, `RAW_PC080SN_XSCROLL_WRITE=0`). The Genesis VBlank scroll commit path is active, but item-page scroll values were zero in this trace. The visible row corruption is therefore staging-geometry aliasing first, not a nonzero scroll-offset explanation.

**Use as prior.** Do not rediscover `FIRE SWORD -> IRE SWORD` as a `genesistan_hook_textwriter_dispatch`, `0x565CE` substitution, `attr_lut`, VDP commit, or Build 0115 opcode-rebasing defect. Do not rediscover the Build 0169 Stage 1 yellow/mountain/wrong-ground terrain as missing PC080SN pattern residency, a source-table relocation miss, an unrelated source-family selection error, an FG/BG swap, palette issue, input issue, or collision-reader issue. The Build 0115 dispatcher remains validated and item text reaches BG staging; the Build 0169 Stage 1 item-strip source family is also expected (`0xD31C`/`0xDB1C`/`0xF31C`) and emits correct lower rows before alias overwrite. Build 0171 is the current Stage 1 gameplay-opening BG projection candidate and Build 0172 is the current gameplay FG row-depth parity candidate: inspect their scene-1 tall backing/projection paths before proposing another terrain source fix. Do not globally change `bg_fill` or `fg_fill` row mapping without a design pass: making staging taller globally could break currently working 32-row-wrapping screens such as title/story/high-score. Broader follow-up still needs to prove later scroll windows, non-gameplay tall layouts, and any remaining rendered black/blank bands as distinct from row-depth preservation.

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

## KF-045 — Stage-1 gameplay FG terrain uses arcade color bank 3, but the Genesis carrier line can be clobbered before gameplay

- **Status:** ACTIVE
- **Confidence:** STRONG (original arcade runtime PC080SN attr/palette samples; Build 0173/0174 Genesis runtime palette/cell probes; build-verified failed candidate)
- **Applicability:** Gameplay PC080SN FG_SRC palette/attribute mapping and Stage-1 terrain palette lifetime (rastan-direct)
- **Rediscovery Hazard:** HIGH
- **Addresses:** `genesistan_stage_fg_src_column`, `FG_PLANE_ATTR_HI`, `genesistan_hook_tilemap_fg_fill_tall`, `staged_fg_tall_buffer`, `staged_fg_buffer`, `staged_palette_words`, `genesistan_palette_hook_3ba64`, `genesistan_palette_hook_59ad4`, arcade bank-3 source `runtime_genesis_rom_offset 0x0004ED56` / JSON-mapped arcade source `0x0004EB56`
- **Source Documents:** docs/design/Cody_build0173_fg_palette_attribute_candidate.md; docs/design/Cody_build0174_fg_arcade_palette_source_candidate.md
- **Related Issues:** OPEN-017; related context KF-010, KF-032, KF-038, KF-043
- **Last verified:** 2026-07-15 (Build 0174 palette-source trace)

**Finding.** Build 0172 proved the Stage-1 gameplay FG_SRC path could preserve/project foreground terrain tile identities vertically, but rendered them through the wrong visible colors. Build 0173 moved the gameplay FG carrier from Genesis line 3 to line 2, but Build 0174 arcade-runtime evidence corrected the palette-source interpretation: original arcade Stage-1 visible FG PC080SN cells use attr/color bank `0x0003`, and converted arcade bank 3 is `0000 0868 0846 0646 0624 0424 0402 0202 0202 028C 044C 0226 0004 0002 0222 0424`. Build 0173 line 2 exactly matches arcade bank 2, not the arcade FG terrain bank. Build 0174 mechanically moved gameplay FG cells to Genesis line 1 and routed bank 3 there, but runtime provenance shows the correct bank-3 values are only briefly written by `genesistan_palette_hook_3ba64` (around `runtime_genesis_pc 0x00071E0A`) and then overwritten before gameplay by later `genesistan_palette_hook_59ad4` frontend/coined-up line-1 writes (around `runtime_genesis_pc 0x00071CEE`). Thus Build 0174 is a failed palette-source delivery candidate: the arcade bank is identified and can be converted, but its Genesis carrier line does not survive to gameplay.

**Use as prior.** Do not rediscover the Stage-1 FG palette problem as a tile-code, tile-LUT, row-depth, or projection failure when the FG tile identities are otherwise correct. Do not return to line 2 or line 3 merely because they are populated: line 2 is arcade bank 2, and line 3 remains related to the green/sprite/bank-51 family from KF-043. Do not globally suppress `0x59AD4` line-1 palette writes, because frontend/title/story content uses line 1. The next bounded fix should preserve frontend line-1 behavior and restore/load arcade bank 3 from the JSON-mapped source (`runtime_genesis_rom_offset 0x0004ED56` / arcade `0x0004EB56`) at a proven gameplay FG palette boundary, setting `palette_dirty` through the existing palette staging path.

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

---

## KF-046 — Arcade palette-bank → Genesis CRAM-line route table + scene-gated carrier re-assert (Stage 1 FG bank 3 on line 1)

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (Build 0174 + Build 0175 runtime CRAM traces; build-verified Build 0175)
- **Applicability:** DURABLE palette-routing mechanism (rastan-direct)
- **Rediscovery Hazard:** HIGH
- **Addresses:** route table `palette_route_table` + `palette_route_lookup` (palette_hooks.s); carrier cache `fg_bank3_line_cache`/`fg_bank3_cache_valid`/`fg_bank3_route_seen` and `vdp_reassert_fg_bank3_line` (vdp_comm.s); staged_palette_words line 1 = arcade PC080SN FG bank 3 during scene 1.
- **Source Documents:** docs/design/Cody_build0175_palette_route_lut_candidate.md
- **Related Findings:** KF-043 (bank-51/line-3 sprite ownership), KF-045 (Stage 1 FG palette carrier), KF-010 (BG/FG staging + full-plane commit)
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-15 (Build 0175)

**Finding.** Genesis CRAM-line ownership is scene-dependent, so a fixed `FG_PLANE_ATTR_HI = line N` guess cannot be correct across frontend and gameplay. Model it as a route table keyed on `(scene_id, owner, arcade_bank) -> (genesis_line, flags)`. For Stage 1: line 0 = arcade bank 0 (HUD), line 1 = arcade FG bank 3 during gameplay / frontend plane palette during title-story, line 2 = arcade BG bank, line 3 = arcade bank 51 (sprites). Line 1 is genuinely FREE to carry FG bank 3 during gameplay because nothing writes it during scene 1 — but a pre-gameplay frontend write leaves it holding a stale palette (this was the Build 0174 "raw steak" FG). Fix (classification A): the palette hooks snapshot the converted bank 3 into a carrier cache when they produce it, and a scene-1-gated VBlank re-assert restores the route-selected line from that cache if it drifts, marking palette_dirty. This does NOT globally suppress any palette hook and does NOT touch frontend line 1 (scene 0). Verified: gameplay line 1 == arcade bank 3 byte-exact; FG cells 996/996 on line 1; BG 2048/2048 on line 2; title/story line 1 preserved.

**Use as prior.** When a gameplay palette line shows the wrong colors but the tiles/cells correctly point at that line, check whether the line is (a) written by the arcade only pre-gameplay and (b) left holding a different scene's owner. If so, the fix is a scene-gated carrier re-assert from a cache captured at production time — never a global hook suppression or a fixed-line re-guess. Extend `palette_route_table` for new (scene, owner, bank) → line routes rather than hardcoding line bits.

---

## KF-047 — PC090OJ final SAT cap is too late; dirty mirror frames must derive bounded changed-record candidates

- **Status:** ACTIVE
- **Confidence:** STRONG (Build 0175/0176/0177 timing traces, Build 0177 candidate-flow proof, Build 0178 resident-cache restoration timing, and Build 0180 SAT-dirty byte-change gating)
- **Applicability:** PC090OJ sprite preparation / retained mirror / Genesis SAT worklist budgeting (rastan-direct)
- **Rediscovery Hazard:** HIGH
- **Addresses:** `vdp_prepare_sprites`, `pc090oj_object_ram`, `pc090oj_mirror_shadow`, `pc090oj_mirror_dirty`, `pc090oj_candidate_bitset`, `pc090oj_candidate_count`, `.Lpc090oj_set_all_candidates`, `.Lpc090oj_process_candidates`, `.Lpc090oj_mark_changed_candidates_since_shadow`, `.Lpc090oj_activate_record`, `.Lpc090oj_place_record_in_slot`, `pc090oj_sat_dirty`, `pc090oj_tile_dma_count`, `staged_sprite_active_count`
- **Source Documents:** docs/design/Cody_build0176_0177_pc090oj_presat_output_budget.md; docs/design/Cody_build0178_sprite_helper_residual_efficiency.md; docs/design/Cody_build0180_pc090oj_sat_dirty_enemy_offscreen.md
- **Related Findings:** KF-010, KF-032, KF-038, KF-043, KF-046
- **Related Issues:** OPEN-017, OPEN-024, OPEN-001 context
- **Last verified:** 2026-07-16 (Build 0180)

**Finding.** Full PC090OJ mirror/state tracking is required, but full expensive Genesis sprite-output preparation is not. Build 0175/0176 timing proved the dominant service cost was before DISPLAY_OFF in `vdp_prepare_sprites` (~35 ms / >2 frames), not the BG/FG commit section. Andy's Build 0176 mirror-shadow memoization did not materially improve timing because a dirty mirror still expanded into `.Lpc090oj_set_all_candidates`, forcing a full 256-record candidate pass before the final 80-SAT-entry cap could help. Build 0177 changed the boundary: `pc090oj_object_ram` still tracks all 256 records, but dirty frames compare the mirror against `pc090oj_mirror_shadow` and mark only changed 8-byte records as candidates; live producer candidates are preserved; bootstrap/global-control paths still use a full sweep. Runtime proof: Build 0177 gameplay candidate-flow averaged `14.00` live entry candidates plus `6.04` changed mirror tuples, `20.04` candidates after marking, and `0` after processing; gameplay `.Lpc090oj_set_all_candidates` hits were `0`. Timing improved from Build 0176 `DISPLAY_OFF=524/1500=0.349/frame`, prep ~`35.7 ms`, to Build 0177 `DISPLAY_OFF=703/1500=0.469/frame`, prep ~`12.0 ms`. Build 0178 then removed the expired Build 0163 gameplay-only forced tile-DMA requeue inside `.Lpc090oj_worklist_set`, allowing the existing resident-code equality check to cancel unchanged sprite tile work. This reduced gameplay tile-DMA work from `18/24` entries to about `6` per serviced frame and reduced dense/later DISPLAY_OFF time from `2.217 ms` to `1.175 ms`, with no BG/FG dirty-row evidence in the sampled timing windows. Build 0180 then proved the next residual budget boundary: animation-only PC090OJ code changes can require tile-DMA without changing Genesis SAT bytes because SAT word2 uses the slot-resident tile index rather than the arcade sprite code. `.Lpc090oj_place_record_in_slot` had been marking `pc090oj_sat_dirty` for every represented-record resync; gating SAT dirty on actual staged-SAT word changes reduced SAT dirty at DISPLAY_OFF from `503/503` to `1/523`, while leaving legitimate tile-DMA animation work intact.

**Use as prior.** Do not rediscover PC090OJ slowdown as merely a final SAT-emission cap problem. The Genesis 80-sprite limit must constrain output work before expensive decode/representation/tile-DMA/SAT construction, while retaining the full arcade mirror for correctness. It is valid to scan/compare all 256 lightweight mirror tuples to derive changed candidates, but dirty-frame processing must not mark all 256 records unless bootstrap or a proven global-control change requires full reevaluation. Also check for stale diagnostic forcing that bypasses resident caches: unchanged `sprite_tile_resident_code[slot]` must be allowed to cancel tile-DMA worklist entries. Animation-only sprite-code changes may still need tile-DMA but should not force SAT DMA unless the staged SAT words actually change. If sprites are still missing, first distinguish mirror existence from output eligibility/rejection; do not hardcode enemies, drop mirror records, force visibility, or broad-disable SAT/tile DMA as a performance fix.

---

## KF-048 — PC090OJ helper mirror sizing is build-time configurable (PC090OJ_MIRROR_RECORDS); default 256, safe to cap

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (build-verified 256/128/80, deterministic; MAME rate/represented/oob evidence)
- **Applicability:** DURABLE build/tuning mechanism (rastan-direct)
- **Rediscovery Hazard:** MEDIUM
- **Addresses:** `apps/rastan-direct/Makefile` var `PC090OJ_MIRROR_RECORDS` (default 256) -> generated `out/pc090oj_config.inc` (`PC090OJ_MIRROR_RECORDS`/`PC090OJ_MIRROR_BYTES`/`PC090OJ_BITSET_BYTES`) included by `pc090oj_hooks.s`. `PC090OJ_HW_ACTIVE_END = PC090OJ_HW_BASE + PC090OJ_MIRROR_BYTES`. Bounds checks in `.Lpc090oj_emit_slot` / `.Lpc090oj_family_apply_record` (drop record>=N to `pc090oj_producer_oob_count`).
- **Source Documents:** docs/design/Andy_build0181_pc090oj_configurable_mirror_records.md
- **Related Findings:** KF-044 (player-source records), KF-046 (palette route), Build 0177 per-record change scan
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-16 (Builds 0181/0182/0183)

**Finding.** The PC090OJ helper mirror (object RAM, shadow, candidate/represented/waiting bitsets, record_to_slot) and every record loop bound / not-found sentinel are sized from a single build-time value. Default 256 is functionally identical to Build 0180 (the bounds checks never fire; oob=0). Overriding via `make release PC090OJ_MIRROR_RECORDS=128` (or 80) rebuilds deterministically with a smaller mirror; records beyond N are safely dropped (no memory overflow). Measured: capping to 128/80 raises the VBlank-service rate ~19% (0.477 -> ~0.57) with sprite representation roughly preserved (22..28), because the active/visible sprite set fits within ~80 records and the arcade addresses many records the Genesis never displays.

**Use as prior.** To tune how many PC090OJ records are mirrored/scanned/processed, change the one Make variable — do NOT hand-edit assembly constants (they all derive from the config). Keep the default at 256. When adding a record-indexed mirror access, make it derive its size from `PC090OJ_MIRROR_*` and bounds-check record indices against `PC090OJ_MIRROR_RECORDS`. Capping the mirror is a slowdown lever but does not fix black bars or the frozen actor-progression (no enemies / uncontrollable) roots.

---

## KF-049 — PC090OJ mirror cap below 122 corrupts Rastan: canonical player anchor lives at records 120..121

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (deterministic diagnostic sweep 80..128 + head-SAT runtime evidence)
- **Applicability:** DURABLE safe-lower-bound for the configurable PC090OJ mirror (KF-048)
- **Rediscovery Hazard:** MEDIUM
- **Addresses:** player anchor mirror records 120 (009E) / 121 (009F) = arcade-canonical player (0x041F5E A5+0x11B2 -> records 120..137, Build 0164). Low duplicate at records 0/1. Head SAT slot 0 @ staged_sprite_sat 0x00FFA1B0.
- **Source Documents:** docs/design/Andy_build0183_80_record_visual_rejection.md
- **Related Findings:** KF-048 (configurable mirror), KF-044 (player-source records / 0x041F5E mapping)
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-16 (Builds 0181..0190)

**Finding.** `PC090OJ_MIRROR_RECORDS` (KF-048) has a hard visual floor at **122**. Sweep of the head SAT sprite X (fixed 0x00FFA1B0): >=122 correct (screen X≈16, left); 116..120 head sprite empty; <=112 flipped to screen X≈288 (right) — `0x1A0 = (320 - x - 16) + 0x80`, the PC090OJ flip-screen transform. The low player records 0..14 are byte-identical across caps, so the corruption is not in their data: the represent/player composition is load-bearing on the **canonical player anchor records 120..121**. Dropping them (any cap <122) leaves the surviving low-duplicate records unable to compose Rastan, and the global flip-screen ends up applied. 128 and 256 render correctly, so this is a game/represent-architecture dependency, NOT a bug in the configurable-mirror mechanism (no code fix warranted).

**Use as prior.** When tuning the PC090OJ mirror cap, do not go below **122**; use **128** for margin. The arcade's real Stage-1 player sprite is the record-120..137 cluster (0x041F5E/Build 0164), not the low records 0..11 — any cap that drops 120..121 breaks Rastan's position/orientation. Keep project default 256.

---

## KF-050 — Player Rastan renders arcade-equivalently at 256/128; Genesis double-draws Rastan (canonical 120..137 + spurious low duplicates 0..17)

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (arcade-vs-Genesis PC090OJ record/SAT trace + rendered screenshots, Builds 0181/0182/0183)
- **Applicability:** DURABLE player-sprite composition fact (rastan-direct)
- **Rediscovery Hazard:** MEDIUM
- **Addresses:** arcade canonical Rastan records 120,121,124,125,126 (codes 009E/009F/008E/008F/0090); Genesis spurious low duplicates 0,1,4,5,6,8..11 via pc090oj_workram_block_sprites default path (hook_target_45dfa) copying A5+0x11B2 -> records 0..17. Player SAT: palette line 3, hflip=1, screenX 16..32.
- **Source Documents:** docs/design/Andy_player_sprite_composition_256_128_vs_arcade.md; screenshots states/traces/build0181_sprite/snap_*/
- **Related Findings:** KF-049 (mirror floor 122 / anchor 120..121), KF-044 (0x041F5E player-source mapping / Build 0164)
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-16 (Builds 0181/0182)

**Finding.** At the default 256 and diagnostic-safe 128 caps, Rastan's player sprite is arcade-equivalent: LEFT position (screenX≈16, arcade X=0x10..0x20), sprite palette line 3, hflip=1 (facing right), coherent barbarian composition — confirmed both by PC090OJ record/SAT trace and by rendered screenshots (256 and 128 identical to each other; both match the arcade barbarian). The red/orange broken cluster on the right is exclusively the Build 0183/80 cap artifact (records 120..121 dropped). HOWEVER, Genesis draws Rastan roughly twice: from the arcade-canonical records 120..137 AND from spurious low-duplicate records 0..17 written by the pc090oj_workram_block_sprites default path (hook_target_45dfa) — while arcade 0x045DFA is a different routine that does not copy A5+0x11B2. The duplicate overlaps the canonical Rastan (same position, adjacent tiles) so there is no visible corruption, but it consumes ~2x the 80-slot SAT budget.

**Use as prior.** The safe builds already render Rastan correctly; do not treat "Rastan is a red blob" as a 256/128 defect — that is the 80 artifact. The arcade player is the record-120..137 cluster only; the Genesis low-record player copy (0..17) is spurious (Build 0164 45dfa mismatch) and a candidate for a bounded cleanup to reclaim SAT slots (possibly relevant to missing-enemy SAT pressure). Not a mirror-mechanism bug.

---

## KF-051 — Spurious low-record Rastan duplicate owned by hook_target_41dae/45dfa (default block-copy helper); Build 0192 gameplay-gated suppression halves player SAT

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (arcade-vs-Genesis producer trace + before/after SAT/rate measurement + screenshots; build-verified Build 0192)
- **Applicability:** DURABLE PC090OJ producer-routing rule (rastan-direct)
- **Rediscovery Hazard:** MEDIUM
- **Addresses:** genesistan_pc090oj_hook_target_41dae / _45dfa -> default pc090oj_workram_block_sprites (A5+0x11B2 -> records 0..17, A5+0x0170 -> 18..21). Canonical player from hook_target_41f5e -> pc090oj_workram_block_sprites_41f5e (records 120..137 / 92..95). genesistan_current_scene_id gameplay gate = 1.
- **Source Documents:** docs/design/Andy_spurious_low_record_player_duplicate_sat_budget.md
- **Related Findings:** KF-050 (double-draw), KF-049 (mirror floor 122), KF-044 (0x041F5E / Build 0164 lineage)
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-16 (Build 0192)

**Finding.** hook_target_41dae and hook_target_45dfa replace arcade routines 0x041DAE/0x045DFA, which copy A5+0x508/0x5C8 -> records 57/96/140/46 (via 0x3D054) — NOT A5+0x11B2. But the Genesis hooks call the default pc090oj_workram_block_sprites, which copies the player block A5+0x11B2 -> records 0..17 (and A5+0x0170 -> 18..21) — an exact duplicate of what hook_target_41f5e already stages to canonical records 120..137/92..95 (Build 0164 address-split artifact). In Stage 1 gameplay arcade records 0..17 are empty, so the low copy is a proven Genesis-only spurious duplicate that draws Rastan ~3x and consumes ~2/3 of the 80-slot SAT budget on redundant player sprites. Build 0192 gates the default copy off in gameplay (scene 1) at both hooks: player SAT slots 18->6 (arcade-faithful), SAT chain 28->15, VINT rate 0.484->0.588 (+21%), records 0..17 writes ->0, with NO player/frontend regression (Rastan still coherent on the left; title/READY intact). Canonical player is independently maintained by hook_target_41f5e at the same frame rate, so suppression cannot make it stale.

**Use as prior.** When a Genesis PC090OJ producer duplicates a sprite, check whether a hook (41dae/45dfa) is using the default block-copy helper instead of the arcade routine's real work. The arcade player is the record-120..137 cluster only; the low-record copy (0..17) is spurious. Suppress spurious producer routes scene-gated (only where proven), never globally, and never by faking SAT / forcing position. A faithful re-implementation of arcade 0x041DAE/0x045DFA (records 57/96/140/46) remains a separate future task.

---

## KF-052 — Build 0192 VINT bottleneck has shifted from PC090OJ prep to the arcade VINT + main loop (58.5%); display-off window now tiny (0.40 ms)

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (fine-grained per-section VINT timing, Build 0192, 653 services)
- **Applicability:** DURABLE timing/budget fact (rastan-direct)
- **Rediscovery Hazard:** MEDIUM
- **Addresses:** _vblank_service sections; arcade VINT chain 0x3A208; vdp_prepare_sprites; display-off/on VDP reg-1 writes (0x8134/0x8174).
- **Source Documents:** docs/design/Andy_build0192_remaining_vint_budget_and_duplicate_census.md; chart docs/design/build0192_vint_budget_breakdown.png
- **Related Findings:** KF-051 (spurious dup suppression), KF-050 (double-draw)
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-16 (Build 0192)

**Finding.** Build 0192 VINT service = 26.55 ms = 1.59 frames (overruns the 16.667 ms 60 Hz budget by ~9.9 ms; effective rate 0.588, ~35 Hz). Per-section: arcade VINT + main loop 15.52 ms (58.5%), vdp_prepare_sprites 10.30 ms (38.8%), everything else < 0.3 ms each. The display-off window (off->on) is only 0.40 ms — the VRAM commits are now cheap (Build 0178 tile-DMA cache + Build 0180 SAT gating + Build 0192 half-sprite set). Rolling black bars are now a small (~6-scanline) mid-screen band because display-off is issued ~10.4 ms into the service (after prepare_sprites), landing ~line 124, and rolls because the 1.59-frame service period is non-integer. The dominant cost has SHIFTED from PC090OJ prep (which dominated earlier builds) to the arcade VINT + main loop — i.e., the injected tilemap/palette/PC090OJ hooks and game logic running during the arcade VINT tail.

**Use as prior.** Further slowdown/black-bar reduction must target the arcade-VINT/main-loop cost (58.5%) and/or move display-off into VBlank (the commit window is only 0.4 ms, so display-off may be unnecessary) — NOT PC090OJ prep alone, and NOT more duplicate suppression (the sprite set is already near arcade-faithful after Build 0192). These are VBlank-ordering / hook-cost tasks, not duplicate cleanups.

---

## KF-053 — family_apply_record double-sync eliminated (Build 0193): defer to the VBlank candidate path + unchanged-tuple fast path; 41f5e hook 6.54->1.76 ms, VINT rate 0.588->0.769

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (measured sub-bucket + full-budget before/after; screenshots; build-verified Build 0193)
- **Applicability:** DURABLE PC090OJ producer-path rule (rastan-direct)
- **Rediscovery Hazard:** HIGH
- **Addresses:** .Lpc090oj_family_apply_record (pc090oj_hooks.s); hook_target_41f5e runtime jsr @0x4215E; VBlank mark/process path (.Lpc090oj_mark_changed_candidates_since_shadow / .Lpc090oj_process_candidates).
- **Source Documents:** docs/design/Andy_fable_build0192_cycle_optimization_pass.md
- **Related Findings:** KF-052 (bucket attribution), KF-051 (0192 suppression), Build 0177 shadow-compare
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-16 (Build 0193)

**Finding.** The 0x041F5E player block copy synced all 22 records inline every service (decode+SAT under 15-reg movem+SR mask = 6.54 ms in the arcade main-loop bucket) even for value-identical tuples, then set mirror_dirty so the VBlank shadow scan re-marked and process_candidates synced the same records a SECOND time. Build 0193 makes family_apply_record behave like every other producer: skip value-identical tuples (Build 0177 invariant: identical bytes => identical decoded output), else write mirror + set candidate; the proven VBlank path syncs exactly once before the same service's commit — VRAM output per service unchanged. Measured: 41f5e hook 6.541->1.762 ms; total service 26.554->21.669 ms (1.59->1.30 frames); rate 0.588->0.769 (~46 Hz); Rastan/title/READY/BG/FG/palette all correct.

**Use as prior.** PC090OJ producers must NOT sync inline + clear their candidate (that forces the VBlank path to redo the work); the correct producer contract is: bounds-check, skip identical tuples, write mirror, candidate_set, mirror_dirty. Remaining measured costs: prepare scan 4.16 ms + shadow copy 2.0 ms (candidates make the scan near-redundant — future candidate with debug guard), and the VBlank commit-first reorder (~0.3 ms commit window) is the highest-value remaining black-bar fix.

---

## KF-054 — VBlank commit-first reorder is unsafe without full double-buffering: SAT is produced in-service, all planes/palette/scroll by the arcade VINT

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (source data-lifetime trace + empirical static-motion measurement, Build 0193)
- **Applicability:** DURABLE presentation-ordering constraint (rastan-direct)
- **Rediscovery Hazard:** HIGH
- **Addresses:** _vblank_service (vdp_comm.s); staged_sprite_sat vs staged_bg/fg_buffer/staged_palette_words/staged_scroll_*; arcade VINT tail jmp 0x3A208.
- **Source Documents:** docs/design/Andy_build0193_vblank_commit_first_reorder.md
- **Related Findings:** KF-052/KF-053 (VINT budget), KF-015 (full-plane scroll model)
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-16 (Build 0193)

**Finding.** In the current architecture the sprite SAT is produced INSIDE _vblank_service by vdp_prepare_sprites (which reads the PC090OJ mirror), while BG/FG plane, palette, and scroll staging are all produced by the ARCADE VINT that runs after the tail jmp 0x3A208 (between services). Coherence holds only because the current order runs prepare immediately before the commit: prepare reads the mirror left by arcadeVINT_{N-1} and the planes/scroll staging is also arcadeVINT_{N-1}, so all classes reflect one arcade game frame. A commit-first reorder (commit at VBlank entry, prepare afterward) commits SAT from prepare_{N-1} (= arcadeVINT_{N-2}) against planes/scroll from arcadeVINT_{N-1} -> sprites lag the background by one frame -> tearing/positional mismatch under motion. The coherent {SAT+tiles+BG+FG+palette+scroll} snapshot exists only momentarily and is overwritten by the next arcade VINT, so a coherent commit-first requires double-buffering the whole ~4.2K-word snapshot (copy = ~0.4 frame, or a broad hook-destination-swap change). NOT bounded. The black band's root is the service overrunning one frame (prepare ~10 ms pushes DISPLAY_OFF to ~line 124 mid-screen); the coherence-preserving fix is to reduce prepare below ~2 ms (KF-053 scan/copy elimination) so prepare+commit fits inside VBlank.

**Use as prior.** Do NOT reorder _vblank_service to commit before prepare — it de-syncs sprites from planes/scroll. A naive reorder will appear safe ONLY because the game is currently frozen (measured: scroll and SAT head-X change 0x/900 gameplay samples); it tears once progression is fixed. To move the commit into real VBlank, either make prepare cheap enough that prepare+commit fits in VBlank (coherent, preferred) or design a full double-buffered presentation snapshot (separate larger task). No structured-metadata owner exists for _vblank_service ordering.

---

## KF-055 — Exodus READY lock at 0x3A342/0x3A346 is a TC0140SYT sound busy-wait on unredirected read 0x3E0003 (emulator-dependent open bus)

- **Status:** ACTIVE
- **Confidence:** CONFIRMED in MAME (loop exits, 0x3E0003=0x00); Exodus lock is Tighe's external observation (consistent with the mechanism)
- **Applicability:** DURABLE strict-emulator / sound-handshake boundary (rastan-direct)
- **Rediscovery Hazard:** HIGH
- **Addresses:** runtime loop 0x0003A33E..0x0003A346 (arcade 0x3A13E..0x3A146, sound-command dispatcher); TC0140SYT status read 0x0003F2A4 / arcade 0x3F0A4 (`moveb 0x3E0003,%d0`); send 0x3F284/arcade 0x3F084; 0x3E0000-0x3E0003 = arcade TC0140SYT (absent on Genesis).
- **Source Documents:** docs/design/Andy_exodus_ready_loop_entry_trace.md
- **Related Findings:** KF (sound suppression opcode_replace entries in spec)
- **Related Issues:** OPEN-017, OPEN-003 (emulator divergence)
- **Last verified:** 2026-07-16 (Build 0193, MAME)

**Finding.** The arcade sound-command dispatcher (arcade 0x3A126) sends queued commands (A5+0x292..0x297) to the TC0140SYT and busy-waits at 0x3A33E-0x3A346 (`bsr 0x3F29C; btst #0,d0; bne`) for the sound CPU ready bit (0x3E0003 bit 0). The spec suppresses the TC0140SYT WRITE side (reset/bank) but leaves the status-READ busy-wait (arcade 0x3F0A4, 0x3E0003) unredirected. Genesis has no TC0140SYT; 0x3E0003 is out-of-physical-ROM cartridge space (ROM 1.58 MB; addr ~3.87 MB) whose value is emulator open bus. MAME/BlastEm read 0x00 (bit 0 = 0) -> loop exits -> gameplay; Exodus reads bit 0 = 1 -> loop spins forever -> READY lock. The earlier-observed 0x702F0/0x702F6 and 0x702BA/0x702C0 loops are normal bounded VBlank dbf commit loops (palette + FG strips), not the lock.

**Use as prior.** Any arcade sound/coprocessor handshake that busy-waits on an absent Genesis chip register is emulator-open-bus-dependent and will lock strict emulators (Exodus) while lenient ones (MAME/BlastEm return 0) pass. The fix class is to redirect the READ (not just suppress the write) to return the ready value, or route the handshake through the Genesis Z80 sound path — never NOP the loop. Check the read value at the poll address before assuming a timing/interrupt cause.

---

## KF-056 — Build 0194 redirects the TC0140SYT status read (0x3E0003) so the sound busy-wait exits on all emulators (Exodus READY lock fixed)

- **Status:** ACTIVE
- **Confidence:** CONFIRMED in MAME (loop deterministically exits; gameplay/visuals intact); Exodus fix by construction (open-bus dependency removed)
- **Applicability:** DURABLE strict-emulator sound-handshake fix (rastan-direct)
- **Rediscovery Hazard:** MEDIUM
- **Addresses:** opcode_replace arcade 0x03F0A4 / runtime 0x0003F2A4: `moveb 0x3E0003,%d0` -> `andi.l #0xFFFFFFFE,%d0`. Loop 0x3A33E-0x3A346; subroutine 0x3F29C.
- **Source Documents:** docs/design/Andy_build0194_tc0140syt_status_read_redirect.md
- **Related Findings:** KF-055 (root cause)
- **Related Issues:** OPEN-017, OPEN-003
- **Last verified:** 2026-07-16 (Build 0194, MAME)

**Finding.** Per KF-055 the Exodus READY lock is the TC0140SYT sound busy-wait reading emulator-open-bus at 0x3E0003. Build 0194 replaces the single-caller status read at arcade 0x3F0A4 with `andi.l #0xFFFFFFFE,%d0`, forcing bit 0 (busy) clear so the arcade loop `btst #0,d0; bne` falls through naturally. Byte-exact 6->6, no NOP, no branch/loop/state change; the sole caller uses only bit 0 and overwrites d0 after. MAME: D0 bit 0 clear 3/3, loop exits, gameplay reached, rate 0.771 (no regression vs 0193), Rastan/title/READY/BG/FG/palette all correct. Removes the open-bus dependency, so Exodus (and any emulator) exits the loop deterministically.

**Use as prior.** When suppressing an absent-hardware coprocessor handshake, redirect the busy-status READ (not just the writes) to the ready value; a single andi.l/moveq at the read is enough when the poll only tests one bit and the caller discards the rest. Never NOP the wait loop or force its branch. opcode_replace count is now 152.

---

## KF-057 — Player control input chain: ten raw-literal latch reads (0x10C016) rebased in Build 0196; control still blocked by un-dispatched player routine (0x51090 jsr skipped)

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (live latch/shadow traces + ROM byte verification + zero-hit execution taps, Builds 0195/0196)
- **Applicability:** DURABLE input-architecture + frozen-progression boundary (rastan-direct)
- **Rediscovery Hazard:** HIGH
- **Addresses:** input latch A5+0x16 = 0xFF0016 (writer arcade 0x3A796, gate A5+0x34); shadows 0xFFA1A8..AB; ten rebased readers 0x5277A/0x527D4/0x527E4/0x527F4/0x52804/0x528CA/0x528DA/0x528EA/0x528FA/0x52BC8 (+ 0x5102E from Build 0158); player-control routine arcade 0x52732; sole caller 0x51090 jsr (skipped by 0x5108C braw 0x51096); gatekeeper 0x5132A / A5+0x10E8 state machine.
- **Source Documents:** docs/design/Andy_fable_build0196_player_control_and_mirror192.md
- **Related Findings:** KF-042 (0x10C016 raw literal, Build 0158), KF-044 (player source block / frozen spawn), KF-049 (mirror floor)
- **Last verified:** 2026-07-17 (Builds 0196/0197)

**Finding.** The Genesis input plumbing is fully correct through the latch: pad -> `rastan_direct_update_inputs` -> active-low shadows (P1 byte bit0..5 = U/D/L/R/B=attack/C=jump, exact arcade P1 layout) -> redirected port reads (0x3A4A2/0x3A778 -> shadow) -> arcade latch write A5+0x16 (0xFF0016), verified live (Right=0xF7, Left=0xFB, C=0xDF; gate A5+0x34=1). The player-control DISPATCH however read the latch via raw absolute `movew 0x10C016,%d0` at ELEVEN sites; Build 0158 rebased one (0x5102E) and Build 0196 rebased the remaining TEN (byte-neutral -> 0x00FF0016; opcode_replace count 162). ROM 0x10C016 reads 0xEFFF (low byte 0xFF = active-low nothing-pressed), so pre-0196 the control code saw "no input" forever. AFTER the rebase control is STILL blocked: the ten readers never execute because the sole caller of the player-control routine (arcade 0x51090 `jsr 0x52732`) sits after an unconditional `braw 0x51096` at 0x5108C; only the gatekeeper `jsr 0x5132A` (A5+0x10E8-driven player-state machine) can route into it, and it never does — while the master gameplay routine demonstrably runs (0x5102E command read fires continuously). This un-dispatched player routine is the frozen-progression root shared with missing enemies/scroll.

**Use as prior.** Input-layer work is DONE: shadows, port redirects, latch, bit mapping, and all eleven latch readers are correct — do not re-audit them for control bugs. The next control boundary is exclusively WHY the 0x5132A/A5+0x10E8 state machine never activates the 0x51090 player-control call (spawn-state completion; see KF-044). Beware m68k prefetch: execution taps at a routine head adjacent to another routine's end fire on prefetch without execution — verify with taps deeper inside the routine.

---

## KF-058 — Build 0198 makes Rastan controllable: 29-site raw-literal family 0x10D37A (per-frame input copy A5+0x137A) rebased; mode=action-state semantics decoded

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (live control test: walking/jump/fall + camera scroll; arcade-matched mode transitions; build-verified 0198/0199)
- **Applicability:** DURABLE input/action-state architecture (rastan-direct); THE frozen-progression root fix
- **Rediscovery Hazard:** HIGH
- **Addresses:** per-frame input copy A5+0x137A (writer 0x51034 a5-relative from latch read 0x5102E); 29 rebased readers 0x514A4..0x52A1A (`30390010D37A`->`303900FF137A`); action state A5+0x10E8 (0=idle,1=walk,2=jump,3=fall,8=death); HP A5+0x13A (init 0x3000; 0x517E6 death check); substate A5+0x1364 (walk anim).
- **Source Documents:** docs/design/Andy_fable_build0198_player_action_state_input_copy_rebase.md
- **Related Findings:** KF-057 (latch layer), KF-042 (0x10C016), KF-044 (raw-literal class)
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-17 (Builds 0198/0199)

**Finding.** The player action state machine (0x514A4..0x52A1A: gatekeeper heads 0x515B6/0x51600 + every walk/jump/attack handler) reads the per-frame input copy A5+0x137A exclusively through raw literal `movew 0x10D37A,%d0` — 29 sites, all previously reading Genesis ROM constant 0xEEEE (phantom frozen input). The copy itself was always correct (master routine 0x51034 writes it a5-relative from the Build-0158-rebased latch read every frame). Rebasing the 29 sites (byte-neutral) completes the 40-site input-read family (11 latch + 29 copy) and RESTORES CONTROL: Right -> mode=1 walking with camera scrollX advancing; C -> mode=2 jump; descent -> mode=3 with scrollY following; substate walk-cycle animates; arcade-matched semantics. This unfroze the entire progression (scroll was static for hundreds of builds). Mode is the ACTION state, not a spawn gate; A5+0x13A is HP (death -> mode=8 at 0x517E6); the 0x51090 `jsr 0x52732` is dead code in this flow on both machines.

**Use as prior.** The input chain is now FULLY complete (pad->shadow->latch->copy->40 readers); do not re-audit it. Player-adjacent raw-literal families follow the pattern: find `3039/1039/xx39 0010 xxxx` absolute reads of a5-mirrored fields and rebase byte-neutrally (+0xEE4000); the action state machine's a5-relative accesses always worked. With progression live, next tasks (enemies, sky-reset, FG streaming, black bars) must be re-evaluated against a SCROLLING game — prior static-frame findings may shift.


---

## KF-059 — Build 0200 fixes jump/fall stuck-at-top via copied-ROM arc-table pointer relocation

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (arcade-vs-Genesis jump trace + ROM byte verification + Build 0200/0201 validation)
- **Applicability:** DURABLE copied-ROM data-pointer relocation rule for player action physics (rastan-direct)
- **Rediscovery Hazard:** HIGH
- **Addresses:** player action state `A5+0x10E8` mode 2/3; arc pointer `A5+0x1332`; arc index `A5+0x1336`; pending flag `A5+0x1272`; vertical accumulator `A5+0x1262`; patched arcade PCs `0x0505DC`, `0x0514B8`, `0x0520DC`, `0x0520E6`, `0x05211A`, `0x052124`, `0x052150`, `0x05215A`, `0x05218E`, `0x052198`, `0x0521CA`, `0x0521D4`, `0x052212`, `0x05221C`, `0x052250`, `0x05225A`, `0x052298`, `0x0522A2`, `0x0522D6`, `0x0522E0`, `0x052310`, `0x05233E`, `0x0523C4`.
- **Source Documents:** docs/design/Cody_build0200_jump_fall_pending_move_flag.md; traces under states/traces/build0200_jump_fall_pending_move/
- **Related Findings:** KF-057, KF-058, KF-039/KF-044 raw-literal class
- **Related Issues:** OPEN-017
- **Last verified:** 2026-07-17 (Builds 0200/0201)

**Finding.** Build 0198 restored player control, but jump mode used embedded arcade ROM data-pointer literals such as `0x0005B548` for the jump/fall arc tables. In the Genesis copied-ROM layout, `address_map.json` places arcade data `0x0005B548` at runtime Genesis `0x0005B748`; leaving the raw literal unrelocated made the arc walker read runtime `0x0005B548` (mapped to arcade `0x0005B348`) whose bytes begin `00AD 00AD...` instead of the real arc table `FFFF 0004 0004 0003...`. The first jump step therefore loaded `A5+0x1262=0x00AD` instead of `0x0004`, causing `A5+0x1272=1`; the faithful branch at runtime `0x51564` then skipped the arc walker while the oversized pending movement drained, freezing `A5+0x1336` around 1 and producing the stuck/high jump. Build 0200 rebased the active arc-pointer literals and compare immediate byte-neutrally to the copied-ROM locations (`0x5B516->0x5B716`, `0x5B548->0x5B748`, `0x5B570->0x5B770`, `0x5B5A2->0x5B7A2`, `0x5B5EC->0x5B7EC`, `0x5B62E->0x5B82E`). Post-fix, Build 0200/0201 read pointer `0x0005B748`, first accumulator `0x0004`, `A5+0x1272` no longer sticks high, arc index reaches 18, and mode 3 transition is restored in the trace.

**Use as prior.** Do not re-chase this symptom as held-C retriggering, input-edge handling, collision, or a bad `A5+0x1272` clear. The pending flag was behaving according to the arcade branch; Genesis fed it the wrong movement magnitude because copied-ROM **data pointer literals** were not relocated. For future movement/physics defects, audit embedded ROM data-pointer immediates in active action-state routes against `address_map.json`, not by `+0x200` assumption alone. Residual exact jump cadence/visual feel, if any, is a separate timing/control-flow observation, not proof that this pointer fix failed.

---

## KF-060 — Enemy PC090OJ records (46/57/96/140) never staged: arcade writers 0x41DAE/0x45DFA NOPped, replacement hook misroutes + Build 0192 gameplay-skip

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (writer provenance + Genesis mirror evidence: populated actor block 0x2C8 → blank record 140; player record 120 real)
- **Applicability:** DURABLE PC090OJ enemy/actor sprite staging (rastan-direct); root of "no enemies appear"
- **Rediscovery Hazard:** HIGH
- **Addresses:** arcade enemy writers 0x41DAE (blocks A5+0x508/0x5C8/0x2C8/0x748 → records 57/96/140/46) and 0x45DFA (A5+0x5C8/0x748/0x8C8), both via actor→sprite expansion 0x3D054 (writes records through a1@+, sub-engine 0x3C902 at 0x3C982/0x3C990 — redirectable). Genesis NOPs them (0x42060..0x4208E etc.) and installs hook_target_41dae/41f5e/45dfa. Mirror pc090oj_object_ram=0xFFA9D8.
- **Source Documents:** docs/design/Andy_opus_build0202_enemy_record46_writer_provenance.md; docs/design/Cody_build0202_enemy_spawn_and_visual_issue_ledger.md
- **Related Findings:** KF-051 (Build 0192 duplicate suppression — the same gate that skips these hooks), KF-047/048/049/050
- **Related Issues:** OPEN-017, OPEN-024
- **Last verified:** 2026-07-17 (Build 0200)

**Finding.** The arcade enemy/actor sprite writers 0x41DAE and 0x45DFA expand actor-staging blocks into PC090OJ records 57/96/140/46 via engine 0x3D054. The Genesis port NOPped these routines and replaced them with hook_target_41dae/45dfa → pc090oj_workram_block_sprites, which (a) in Stage-1 gameplay SKIPS entirely (Build 0192 scene gate, cmpi.b #PC090OJ_SCENE_GAMEPLAY_ID), and (b) outside gameplay copies the WRONG source (player block A5+0x11B2) to the WRONG records (0..17/18..21). Only the player path (hook_target_41f5e → pc090oj_workram_block_sprites_41f5e, records 120..137/92..95) is faithfully reimplemented. Genesis mirror records 46/57/96/140 stay at blank placeholder [0000 0100 0000 0100]; record 120 (player) is real. Block A5+0x2C8 (→140) is populated (6 active) yet record 140 is blank — isolating the staging drop independent of actor population. Classification E. The port's own source (pc090oj_hooks.s:317-320, 494-503) documents this as a deferred gap.

**Use as prior.** A faithful fix is architecturally viable — the expansion engine 0x3D054 writes via a1@+, so a Genesis hook can point a1 at pc090oj_object_ram+rec*8 and call the relocated arcade expansion (0x3D254) — but it is a multi-routine reimplementation (4 actor blocks + per-block active/count/blank-fill logic + verify 0x3D054 sub-engines 0x4770E/0x3F0BC/0x3FFDC/0x3FFF0/0x3C902 and their ROM sprite-layout tables relocate correctly + candidate marking + avoid re-introducing the Build 0192 duplicate Rastan). NOT a byte-neutral rebase. Before implementing, resolve the remaining unknown: whether arcade actor block A5+0x748 (record 46's source) is populated at the matched point while Genesis 0xFF0748 is empty (pure staging gap = E) OR the enemy-logic that fills it also diverges (upstream spawn = B/C). Do not hardcode records, force SAT, or raise the mirror cap to "see" enemies.

---

## KF-061 — Enemy staging framework is safe, but arcade expansion engine 0x3D254 cannot be called from the hook, and the actor blocks are unpopulated upstream (refines KF-060)

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (Build 0202 attempt + engine-disable bisect: engine-enabled locks the player in mode 3; engine-disabled restores Build 0200 control exactly)
- **Applicability:** DURABLE — bounds the enemy-staging fix
- **Rediscovery Hazard:** HIGH (prevents re-attempting the same unsafe engine call)
- **Addresses:** arcade actor→sprite engine 0x3D054 (genesis 0x3D254) → 0x3CB02 family; actor blocks A5+0x508/0x5C8/0x2C8/0x748/0x8C8; mirror pc090oj_object_ram; hooks hook_target_41dae/45dfa.
- **Source Documents:** docs/design/Andy_opus_build0202_enemy_actor_staging_implementation.md
- **Related Findings:** KF-060 (writer provenance), KF-051 (Build 0192 duplicate suppression)
- **Related Issues:** OPEN-017, OPEN-024
- **Last verified:** 2026-07-17 (Build 0200 baseline)

**Finding.** A faithful Genesis reimplementation of the arcade enemy writers 0x41DAE/0x45DFA was built (scratch buffer + block iteration + family_apply_record flush + candidate marking; GATE_PASS, source-only). Bisect proved: the staging FRAMEWORK is safe (blank-only variant restores Build 0200 control exactly, player records intact), but CALLING the relocated arcade expansion engine 0x3D254 from the hook CORRUPTS player/collision state — the player locks in mode 3 (fall) from gameplay start and never gains control. Cause: at the matched window the Genesis enemy actor blocks are unpopulated (records 46/57/96/140 blank-fill only, no valid code), so the engine indexes its ROM sprite-layout tables with invalid actor fields and touches shared state. Blank-only staging yields zero enemies (no improvement). A full clone of 0x3CB02's multi-case sprite engine is out of bounded scope.

**Use as prior.** Do NOT call 0x3D254 from a Genesis hook against unpopulated/garbage actor blocks — it regresses control (proven). The enemy fix is blocked UPSTREAM: the arcade routine that populates A5+0x748 (and siblings) with valid enemy actor structs must be found and its Genesis divergence (spawn/progression/NOPped enemy-logic/raw-WRAM-literal) resolved FIRST. The staging framework from Build 0202 is reusable once valid actors exist. Decisive next evidence: arcade write-watch on A5+0x748 (0x10C748) vs Genesis 0xFF0748 at the matched frame (needs arcade romset). Do not ship blank-only staging (churn, no enemies), do not raise the mirror cap, do not force records.

---

## KF-062 — Genesis DOES populate enemy actor blocks (camera/scroll spawn works); enemy-visibility blocker is the NOPped staging + unsafe engine, plus sub-phase progression (revises KF-060/061 upstream framing)

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (live arcade-vs-Genesis WRAM sampling, both emulators)
- **Applicability:** DURABLE — redirects the enemy investigation
- **Rediscovery Hazard:** HIGH (prevents re-chasing a nonexistent "unrelocated spawn pointer")
- **Addresses:** camera A5+0x10B8 (spawn gate cmpiw #160 at 0x4580C/0x45EFC/0x4B170/0x4B9C4/0x4C3BE); scroll velocity A5+0x10D8; stage A5+0x118; sub-phase A5+0x13E; stage-init table arcade 0x50850 / genesis 0x50A50 (relocated, verified); actor blocks A5+0x2C8/0x748.
- **Source Documents:** docs/design/Andy_opus_build0203_enemy_actor_population_and_expansion_fix.md
- **Related Findings:** KF-060 (staging NOPped/misrouted), KF-061 (engine-call unsafe), KF-059 (jump/fall)
- **Related Issues:** OPEN-017, OPEN-024
- **Last verified:** 2026-07-17 (Build 0200, arcade romset via -rompath roms)

**Finding.** The arcade Rastan romset runs under MAME (`-rompath roms`; the `roms/allregions` set is bad and shadows it). Live comparison shows Genesis actor population is NOT globally broken: with the camera scrolling (A5+0x10B8 advancing past the spawn gate of 160, driven by scroll velocity A5+0x10D8), block A5+0x2C8 holds 6 entries and block A5+0x748 (rec 46) spawns (~F1800). The stage-init table pointer is correctly relocated (0x50850->0x50A50, data byte-identical), the spawn dispatcher/preprocessor (0x450D8/0x4580C) are intact, and spawn-control fields (stage 0x118, sub-phase 0x13E, wave 0x21C, trigger 0x2DE) match arcade. There is NO unrelocated pointer / raw literal / NOPped routine on the population path. Enemies still don't reach the screen because (1) the staging routines 0x41DAE/0x45DFA are NOPped and the expansion engine 0x3D254 is never called and is unsafe to call from a hook (KF-060/061), and (2) sub-phase progression diverges (Genesis A5+0x13E cycles 1->0 with resets vs arcade 1->2), the known level-reset symptom, limiting later waves.

**Use as prior.** Do NOT search for an "unrelocated enemy spawn pointer" or a raw-literal in the population path — there isn't one; population works. The enemy-visibility blocker is the staging/expansion layer (KF-061: make 0x3D254 safe to call on a validated actor, then drive the Build 0202 framework) and the sub-phase/level-reset progression bug. Both are separate bounded investigations, not single-instruction rebases. Arcade is now runnable for direct comparison (`-rompath roms`).

---

## KF-063 — Expansion engine 0x3D254 is safe on validated actors; Build 0204 fixes record-46 empty output by restoring shared 0x3C950 PC090OJ writes

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (Build 0203 diagnostic proved valid-code-guarded record-46 staging preserves player control; Build 0204 proved nonzero record-46 output reaches PC090OJ representation)
- **Applicability:** DURABLE — unblocks the enemy-staging approach; supersedes KF-061's "engine unsafe" as unconditional
- **Rediscovery Hazard:** HIGH
- **Addresses:** engine `runtime_genesis_pc 0x0003D254` (`arcade_pc 0x0003D054`, JSON-mapped); shared patched site `runtime_genesis_pc 0x0003CB50` (`arcade_pc 0x0003C950`, JSON-mapped); block A5+0x748 record-46 path; `genesistan_hook_text_writer_3c950`; `genesistan_pc090oj_hook_target_41dae`.
- **Source Documents:** docs/design/Andy_opus_build0203_single_actor_expansion_engine_safety.md; docs/design/Cody_build0204_pc090oj_record46_expansion_output_fix.md; docs/design/Cody_build0205_pc090oj_enemy_visual_correctness.md
- **Related Findings:** KF-061 (engine unsafe in broad hook — now scoped to invalid actors), KF-060, KF-062
- **Related Issues:** OPEN-017, OPEN-024
- **Last verified:** 2026-07-17 (Build 0205 visual-correctness evidence pass against Build 0204)

**Finding.** Calling the relocated arcade actor->sprite engine `0x3D254` from a Genesis hook is SAFE when restricted to VALIDATED actors (active flag AND non-zero code `a4@(1)` AND arcade `a4@(0x36)==0` gate). Build 0203 staged ONLY block A5+0x748 (record 46) with that guard: the player stayed fully controllable (mode 0->1->2, walk/scroll/jump), no mode-3 lock, player records intact. This proves KF-061's corruption was classification B (the Build 0202 broad hook called the engine on block-0x2C8 code-0 invalid actors -> wild jump-table dispatch), not an inherent engine hazard. The Build 0203 code-zero output was then root-caused to a shared opcode-replacement collision: the engine's default shape path reaches `runtime_genesis_pc 0x03CB50` (`arcade_pc 0x03C950`), but that site had been replaced by `genesistan_hook_text_writer_3c950`, which only routed PC080SN C-window text staging and did not preserve the original non-C-window `(%a1)+` PC090OJ record writes. Build 0204 made the helper destination-aware: C-window `%a1` continues through FG staging, while non-C-window `%a1` restores the original sprite-record emitter semantics. Focused Build 0204 validation shows record 46 first becomes nonzero/visible at frame 785 (`[0000 0069 0275 0070]`), becomes represented at frame 786, and remains represented in SAT slot 16 with final sampled tuple `[0000 0069 0277 009B]`.

Build 0205 visual-correctness evidence (against the preserved Build 0204 ROM) adds an important acceptance boundary: reaching SAT is NOT sufficient to accept the enemy fix visually. Runtime MAME samples prove record 46/slot 16 owns the new output (`SAT=00E1 0502 C440 00F0/00EB`, tile `0x0440`, palette line `2`, resident code `0x0275 -> 0x0277`), and original arcade samples show the same PC090OJ code family for visible green enemy actors. However Genesis composite snapshots at the corresponding sampled frames did not show an arcade-equivalent enemy, and MAME Lua `:gen_vdp` `videoram` reads returned zero for the expected sprite tile address (`0x8800`) while also returning zero in prior probes; VDP-port Lua taps likewise did not fire. Therefore the downstream true-VRAM/tile-DMA residency boundary remains unresolved and requires debugger-side VDP command/VRAM evidence before any visual-correctness patch.

**Use as prior.** The engine CAN be driven safely from a hook with a non-zero-code guard — do not re-fear it wholesale. If a future PC090OJ engine path reaches `arcade_pc 0x03C950`, preserve both roles of that shared routine: PC080SN C-window text must route to Genesis tile staging, while non-C-window destinations must preserve the original PC090OJ tuple writes into the caller's `%a1`. Do NOT stage code-0 actors, force SAT entries, hardcode enemies, or route raw D-window writes. Build 0204 fixes only the first validated record-46 output boundary; it does not prove visual correctness. Before patching palette or sprite decode for record 46, prove whether true VRAM at `0x8800..0x887F` matches `rastan_pc090oj + 0x0277*128` after `.Lvcs_tile_dma`. Sibling actor blocks/records 57/96/140, sub-phase/level-reset progression, stale record 132, and bat respawn remain separate OPEN-017 work.

---

## KF-064 — Corrected lizard-man ownership: first Stage-1 lizard men = block A5+0x2C8 → composite records ~140..229 (codes 0x004B-0x0069); record 46 (code 0x0277) is a DISTINCT non-lizard sprite

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (live arcade-vs-Genesis PC090OJ dumps + snapshots; block-0x2C8-activity ↔ composite-record-count correlation)
- **Applicability:** DURABLE — corrects the record-46→lizard attribution that Build 0204/0205 assumed
- **Rediscovery Hazard:** HIGH (prevents re-tracing record 46's VRAM as the lizard)
- **Addresses:** lizard actors block A5+0x2C8 (codes 0x17/0x18/0x1C-0x1F/0x70) → engine-expanded composite PC090OJ records ~140..229 (output codes 0x004B-0x0069, word0=0x4046); record 46 = block A5+0x748 (code 0x0277), single non-lizard sprite.
- **Source Documents:** docs/design/Cody_first_lizard_record_ownership_true_vram_trace.md
- **Related Findings:** KF-063 (record 46 reaches SAT — still valid, but record 46 is NOT the lizard), KF-060/061/062
- **Related Issues:** OPEN-017, OPEN-024
- **Last verified:** 2026-07-18 (Build 0204, arcade via -rompath roms)

**Finding.** The first normally-encountered Stage-1 lizard men are the composite PC090OJ record groups ~140..229 (4 groups of 8, sprite codes 0x004B-0x0069, word0=0x4046), produced by the engine expanding actor block A5+0x2C8 (arcade actors codes 0x17/0x18/0x1C-0x1F/0x70; composite record count 16->52 tracks block-0x2C8 activity; on-screen positions match the visible green lizards). Record 46 (block A5+0x748, code 0x0277) is a DISTINCT single 8x8 sprite that flickers on/off near Rastan and is off-screen when the lizards are visible -- NOT a lizard body. On Genesis Build 0204: block A5+0x2C8 holds VALID lizard actors (e4-e8, codes 0x17/0x18 matching arcade; plus one code-0 invalid entry e0), but composite records 140..229 are BLANK because the current staging helper (pc090oj_hooks.s:533) processes ONLY block A5+0x748 (record 46). So Build 0204 fixed a secondary non-lizard sprite; the visible lizard men remain unstaged. The lizard chain breaks at the object-source/staging layer for block A5+0x2C8 (proven via WRAM/mirror sampling; no VDP-VRAM Lua reads relied upon). Decision-matrix Outcome A.

**Use as prior.** Do NOT patch or true-VRAM-trace record 46 for the lizard man. The lizard target is block A5+0x2C8 -> composite records ~140..229. Next bounded task: extend the proven KF-063 non-zero-code-guarded narrow staging to block A5+0x2C8 (skips code-0 e0, processes valid e4-e8; reproduce arcade 0x41DAE block-3 iteration: 9 entries, d2=10/19, a4@(5)/a4@(3) gates), then true-VRAM-trace the actual lizard records. Does NOT weaken KF-063 (engine-safe / 0x3C950-fix / record-46-reaches-SAT claims remain valid).

---

## KF-065 — Block A5+0x2C8 lizard writer semantics + Build 0205 whole-block-scratch staging route

- **Status:** ACTIVE (implemented candidate; visual/runtime acceptance pending)
- **Confidence:** CONFIRMED (arcade static reconstruction of 0x41E22 + live d2-stride measurement; engine d2-budget proven)
- **Applicability:** DURABLE — the implementation contract for staging the first visible lizard men
- **Rediscovery Hazard:** MEDIUM
- **Addresses:** arcade writer arcade_pc 0x00041E22 (block 3 of 0x41DAE); block A5+0x2C8; engine 0x3D054/runtime 0x3D254; shared 0x3C950/runtime 0x3CB50; composite records 140..238.
- **Source Documents:** docs/design/Andy_lizard_composite_pc090oj_staging_design.md; docs/design/Cody_lizard_composite_pc090oj_staging_implementation.md; docs/design/Cody_lizard_b5_activation_writer_provenance.md; docs/design/Cody_lizard_actor_activation_progression_fix.md
- **Related Findings:** KF-064 (ownership), KF-063 (engine safety + 0x3C950 fix), KF-060/061/062
- **Related Issues:** OPEN-017, OPEN-024
- **Last verified:** 2026-07-18 (Build 0206 lizard activation progression fix)

**Finding.** Arcade block A5+0x2C8 (writer arcade_pc 0x00041E22) iterates 9 64-byte entries, destination PC090OJ record 140, calling engine 0x3D054 with d2=10 (19 for entry index 8). The engine writes EXACTLY d2 records per active actor (loop subql #1,%d2 at 0x3C9A0/0x3C9E2), so %a1 advances by exactly d2 per entry -> deterministic record placement, total span records 140..238 (99 records). Validity gates: a4@(0)!=0 AND a4@(5)!=0 AND a4@(3)==0 (a4@(3)!=0 -> arcade 0x3EFBE special, not engine); code a4@(1)==0 is invalid (Build 0202 corruptor). Measured layout: entry0 (0x3EFBE special) -> records 140-143 code 0x017C (NON-lizard); entries1-3 inactive -> blank 150-179; entries4-8 (valid, codes 0x17/0x18) -> the visible lizard bodies records 180-229 (output codes 0x006D/0x0069). Shared 0x3C950 writer is Build-0204 destination-aware (non-C-window a1 -> sprite-direct), so composite writes to a WRAM scratch are preserved. Build 0205 implements the selected staging route: whole-block scratch (`pc090oj_block2c8_scratch`, 100 records/800 bytes) seeded from mirror records 140..238, valid actors call runtime 0x3D254, inactive actors write only word1/Y=0x0180, special `a4@(3)!=0` and active code-zero actors preserve the seeded window, then records 140..238 flush through `.Lpc090oj_family_apply_record` (change-detecting, candidate/dirty, Build 0193 fast path). Capacity estimate remains ~50 lizard records + 17 existing = ~67 < 80 SAT (fits); per-scanline clustering and visual correctness are still pending validation.

Build 0205 runtime writer-provenance evidence refines the current acceptance boundary: the exact arcade b5 activation writer for block `A5+0x02C8` entries 4..8 is `arcade_pc 0x00041320` (`move.b %d1,5(%a4)`), reached via `0x3A7B4 -> 0x41F0E -> 0x40B66 -> 0x40B80 -> ... -> 0x41320`; `address_map.json` maps this to `runtime_genesis_pc 0x00041520` through the equivalent path `0x3A9B4 -> 0x4210E -> 0x40D66 -> 0x40D80 -> ... -> 0x41520`. Original arcade debugger watchpoints prove nonzero b5 activations for entries 8,7,6,5,4 at arcade WRAM `0x10C4CD/0x10C48D/0x10C44D/0x10C40D/0x10C3CD`. Genesis Build 0205 proves the mapped writer/path is alive for positive-control entry 8 (`0xFF04CD = 0x02`) but never reaches that writer for entries 4..7 in the captured window. The one-lizard limit is therefore upstream actor activation/progression reachability for entries 4..7, not the Build 0205 whole-block staging helper and not a later overwrite of correctly activated entries.

Build 0206 traced and fixed that upstream reachability divergence at the collision-scan boundary. The scan's Genesis-WRAM collision base was already rebased at `runtime_genesis_pc 0x00053C64` to `0x00FF1E00`, and the backward lower-bound compare at `runtime_genesis_pc 0x000414E8` was already `0x00FF1E00`; however, the forward upper-bound compare at `arcade_pc 0x000412CC` / `runtime_genesis_pc 0x000414CC` still used raw arcade `0x0010FE00`. Build 0205 entries 4..7 exhausted `SCAN_FAIL_FWD` with `%a0` around `0x00FA7Cxx`, while entry 8 remained the positive-control hit. Build 0206 replaces `B1FC0010FE00` with `B1FC00FF3E00`, completing the mapped collision-buffer range `0x00FF1E00..0x00FF3E00`. Runtime validation proves entries 8,7,6,5,4 all hit `runtime_genesis_pc 0x00041520`; acceptance metrics reached max `valid_actors=4`, `actor_windows_nonzero=5`, `represented=36`, `active_count=53`, and `waiting=0`. A focused record-46 probe kept record 46 nonzero/represented (`0x0275 -> 0x0277`, SAT slot 40), so the lizard activation fix did not regress that secondary sprite path in the sampled run.

**Use as prior.** Build 0206 is the current candidate implementation for block 0x2C8 lizard activation + staging. Do NOT reuse the 8-byte record-46 scratch; do NOT engine-call code-zero/special actors; do NOT write the mirror directly; do NOT blanket-mark candidates; do NOT change the mirror cap; do NOT seed `a4@(5)`/b5 or force actors/records/SAT. The safe activation fix is the paired mapped collision-buffer bounds: base/lower `0x00FF1E00`, upper `0x00FF3E00`. Do NOT claim final visual/combat acceptance from the trace alone: lizard palette bank 0x36, feet/ground alignment, damage/contact behavior, black bar/VBlank pressure, record 132, bats, and other gameplay visual issues remain separate evidence tasks.

---

## KF-066 — Gameplay HUD-sprite suppression option + shared line-0 carrier for PC090OJ bank 0x36 (lizard palette); route-lookup d3-clobber hazard

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (Build 0210 runtime validation: HUD retired at gameplay entry, CRAM line 0 = converted bank 0x36, lizards green/full-bodied on SAT line 0, Rastan line 3 intact)
- **Applicability:** DURABLE architecture (build option + palette carrier); hazard note prevents re-introducing the 0209 defect
- **Rediscovery Hazard:** HIGH
- **Addresses:** RASTAN_GAMEPLAY_HUD_SPRITES (Makefile -> pc090oj_config.inc); HUD records 0..45; .Lpc090oj_sync_record_from_mirror gate; vdp_prepare_sprites scene-transition sweep; palette_route_table row (1, PC090OJ, 0x36 -> line 0, CARRIER); sprite-palette SOURCE buffer bank 0x36 = 0x00FF16C0..DF (bank-51/Build-0161 pattern); pc090oj_bank36_line0_cache/_valid; vdp_reassert_bank36_line0; arcade bank 0x36 = 0000 4318 00C0 0246 01C0 030E 2948 318A 6356 6B9A 10D2 2996 210A 380E 01CE 39CE (written once at stage load).
- **Source Documents:** docs/design/Andy_opus_gameplay_hud_suppression_lizard_palette_build0208.md
- **Related Findings:** KF-043/KF-046 (palette routes), KF-064/KF-065 (lizard ownership/staging), KF-063
- **Related Issues:** OPEN-017, OPEN-024
- **Last verified:** 2026-07-19 (Build 0210)

**Finding.** (1) Gameplay HUD sprites are PC090OJ records 0..45; suppressing their REPRESENTATION only (draw=0 in sync during scene 1, plus a scene-transition full candidate sweep to retire pre-gameplay representations) frees 6-10 SAT slots and CRAM line 0 without touching arcade HUD/score/life state; frontend scenes keep full HUD presentation. (2) Lizard effective sprite bank 0x36 (word0 nibble 6 | colbank 0x30 from sprite_ctrl 0x0060) is carried to Genesis CRAM line 0 via the shared architecture: route-table row + palette_route_lookup consulted in the palsel general path + hook-side cache (the bank flows through the sprite-palette SOURCE buffer at a5+0x1600+(bank-0x30)*0x20 = 0xFF16C0, NOT the palette-RAM path) + scene-1 carrier re-assert (compare-then-restore, Build-0175 pattern). Rastan (0x33->line 3), BG (48->2), FG (3->1) unchanged. Result: full green arcade-matching lizard men.

**Use as prior.** HAZARD: palette_route_lookup returns flags in d3 and clobbers d0/d3/a0 — in .Lpc090oj_place_record_in_slot the decoded sprite code lives in d3 and feeds the tile-DMA queue; failing to preserve d3 makes every routed sprite load tile code 0x0001 (invisible bodies, thin bars — Build 0209 rejected for exactly this). Sprite palette banks arrive via the WRAM source buffer (0xFF1600 window), not palette RAM — catch them there (bank-51 precedent). The consumed-number release guard refuses counter reuse: iterating on a numbered build consumes a number per iteration (0208/0209 rejected+preserved, 0210 candidate).

---

## KF-067 — Lizard 8px-low root: Genesis collision map ground band one 8px row lower than arcade (row 39 vs 38); block-0x2C8 render compensated -8; expansion engine clobbers d0-d7 (latch on stack)

- **Status:** ACTIVE
- **Confidence:** CONFIRMED (full 8KB map diff at matched frames; rendered-pixel proof: arcade foot 129, 0210 foot 137, 0213 foot 129)
- **Applicability:** DURABLE — explains any map-grounded actor sitting 8 low; hazard note prevents re-introducing the 0211/0212 corruption
- **Rediscovery Hazard:** HIGH
- **Addresses:** collision map arcade WRAM 0x0010DE00..0x0010FE00 / Genesis WRAM 0x00FF1E00..0x00FF3E00 (64 rows x 0x80 bytes; ground words 0x3400/0x3A00 at arcade row 38 vs Genesis row 39); producer genesistan_stage_bg_collision_column (tilemap_hooks.s); actor anchor a4@(0x1A) (arcade 0x79 vs Genesis 0x81 with identical world-Y/camera inputs); compensation in pc090oj_stage_block2c8 (uniform -8 on engine-emitted Y, stack-latched count).
- **Source Documents:** docs/design/Andy_fable_lizard_vertical_alignment_mirror192.md
- **Related Findings:** KF-064/065 (lizard staging), KF-066 (palette), KF-063
- **Related Issues:** OPEN-017, OPEN-024
- **Last verified:** 2026-07-19 (Builds 0213/0214)

**Finding.** (1) The Genesis-produced collision map carries the Stage-1 ground band one 8px row LOWER than arcade (map row 39 vs 38; 8KB diff at matched frames; also a leftmost-column X-edge word missing). Enemies ground on this map -> actor anchors read +8 (0x81 vs 0x79) with identical inputs; the engine/staging/decode faithfully render them 8 into the visible (correctly drawn) ground. The player's contact was separately tuned to the visible ground, so only map-grounded actors show the offset. Build 0213 compensates at the block-0x2C8 composite-producer boundary: uniform -8 on the Y field of exactly the d2 engine-emitted records (high bits preserved; blank/preserved windows untouched; actor state untouched). Rendered proof: feet 137->129 = arcade-identical. The durable future fix is the map row base itself + re-tuning the player path (moves Rastan -> out of scope here). (2) HAZARD: the expansion engine 0x3D254 clobbers d0-d7 (counts d2 to 0, uses d3 for byte fetches) -- post-call loops MUST latch counts on the stack; d2- and d3-latches caused the rejected Builds 0211/0212 (wild dbra walked WRAM backward applying -8 to every (addr%8)==2 word = global state corruption). (3) Mirror 192 is structurally incompatible with the lizard span: records 192..238 (47/99) OOB-dropped every frame (lizrep 2 vs 24) -- 192 is non-viable for lizard-era builds without span rebasing.

**Use as prior.** Any other actor family grounding 8 low shares the KF-067 map root -- compensate at its producer boundary or fix the map+player jointly. Never trust engine-preserved registers; stack-latch. Do not ship 192 expecting full lizards.
