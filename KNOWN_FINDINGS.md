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

## KF-015 — Scroll model: full-plane with +8 vertical bias, no per-line

- **Status:** ACTIVE
- **Confidence:** STRONG
- **Applicability:** GLOBAL
- **Rediscovery Hazard:** NORMAL
- **Addresses:** WRAM/A5 offsets `0x10EC`, `0x10EE`, `0x10AE`, `0x10B0`
- **Source Documents:** docs/design/pc080sn_tilemap_architecture.md (Scroll System)
- **Related Issues:** (none)
- **Last verified:** 2026-05-22 (Build 0077)

**Finding.** Documented scroll commit uses full-plane BG/FG scroll values with +8 vertical bias and does not use per-scanline scroll mode.

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

### KF-028 — Genesis input mirror `0xff60fc..0xff6100` is unpopulated in Build 0077

Status: ACTIVE
Confidence: CONFIRMED (static facts: sole writer, unreferenced shim entry, boot-clear gap) / STRONG (causal link to state-3 routing observed in BM-007)
Applicability: BUILD_SPECIFIC (Build 0077)
Rediscovery Hazard: HIGH (treat as canonical prior unless contradicted by explicit evidence)
Addresses: input mirror byte `0xff60ff` (and neighbors `0xff60fc..0xff6100`); sole writer `0x711ac`; shim entry `0x710ca` (unreferenced); boot-clear gap `0xff60fa..0xff6103`; arcade-source counterpart input port `0x390007` (TC0040IOC, read-only hardware); arcade-translated readers `0x3a690`, `0x3a9b8`, `0x3ab1a`, `0x3ad96`, `0x3ae04`, `0x3ae94`, `0x3aefe`
Source Documents: docs/design/Andy_0xff60ff_input_shim_audit.md (Phase 1-4 static audit; Outcome A); BM-007 evidence at dist/rastan-direct/bookmarks/build_0077_pc_0x0003ADD6/ (runtime corroboration)
Related Issues: OPEN-001, OPEN-004
Last verified: 2026-06-13 (Build 0077)

**Finding.** The arcade TC0040IOC input port `0x390007` (read-only hardware, KF-022 active-low: idle/unpressed = 1) is mirrored on Genesis at WRAM `0xff60ff` (and adjacent bytes `0xff60fc..0xff6100`), read by the arcade-translated code at seven sites (`0x3a690/0x3a9b8/0x3ab1a/0x3ad96/0x3ae04/0x3ae94/0x3aefe`). The sole writer of `0xff60ff` in Build 0077 is `0x711ac` (`moveb %d5,0xff60ff`), inside the controller-poll shim at `0x710ca`. The shim entry `0x710ca` is unreferenced in Build 0077: no `jsr`/`bsr`/`jmp` immediate, no pointer-table reference to `0007 10ca`, and not reached by fall-through (preceded by `rts`). Additionally, `0xff60ff` lies in the Genesis BSS domain (above `0xff4000` per KF-008) and is outside both the arcade WRAM zero-fill (`0xff0000..0xff3fff`) and the boot BSS clear ranges (clears stop at `0xff60f8`, resume at `0xff6104`); `0xff60fa..0xff6103` is a clear-gap that includes the entire input-mirror byte range `0xff60fc..0xff6100`. The mirror is therefore neither initialized nor updated in Build 0077. If the shim ran, it would write `0xff60ff` bit 2 = 1 (the shim builds `%d5` as `moveq #-1`, only conditionally clears bits 3/4/5, leaves bit 2 untouched).

**Use as prior.** When arcade-translated code reads `0xff60xx` input-mirror bytes in Build 0077, do not assume they reflect controller state — the mirror is unpopulated. Specifically: the gate at `0x0003AD96` (`btst #2,0xff60ff`) reads bit 2 = 0 (active-low asserted), causing fall-through to the state-3 writer at `0x0003ADD6` and routing master dispatch to the watchdog instead of the title dispatcher. **Do NOT attempt to "fix" this by initializing only `0xff60ff`.** That would unblock one gate but leave the entire input mirror stale and non-functional across the other six reader sites. The real fix is wiring the input-poll shim `0x710ca` into the per-frame input-servicing path before the arcade VBlank handler consumes the mirror. Cross-reference KF-003 (dispatch chain), KF-022 (TC0040IOC active-low semantics), KF-008 (WRAM ownership split).

**Working hypotheses.** (1) The shim's intended call site was dropped during port development (regression), in which case there is a missing `jsr 0x710ca` somewhere in the per-frame input-servicing path. (2) The shim was never wired (incomplete port), in which case the call site needs to be designed. Distinguishing (1) from (2) is the next bounded investigation. Per Andy_0xff60ff_input_shim_audit.md §5; explicitly flagged as hypothesis pending the call-site investigation.

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
