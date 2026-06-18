# 🔒 AGENT PROMPT TEMPLATE (STRICT, NO WEASEL ROOM)

**Agent:** Andy / Cody  
**Type:** Analysis / Verification / Implementation / Hybrid  
**Build Context:** (e.g., Build 0046, rastan-direct)  

---

# ⚠️ MANDATORY ARCHITECTURE COMPLIANCE

Before reading anything else, internalize these two rules. They are non-negotiable and override any prior design, any prior prompt, and any prior implementation decision.

**Read `RULES.md` and `ARCHITECTURE.md` in full before proceeding.**

The short version:

> The arcade code is the program. It runs on Genesis hardware.  
> Genesis-side code exists only as opcode replacements or helper routines that are called by arcade code and return with RTS.  
> There is no Genesis-owned game loop. There is no Genesis-owned VBlank identity. There is no re-entry into boot/init during gameplay.  
> If any current code violates this, that code is a bug — not a lifecycle to support.

**Violation of RULES.md or ARCHITECTURE.md is a STOP condition.**

If any proposed change would:
- Give Genesis code control-flow ownership
- Re-enter boot/init during gameplay
- Introduce a Genesis-side lifecycle or state machine
- Add test code, scaffolding, or temporary logic
- Prevent arcade code from owning execution 100%

→ **STOP. Do not implement. Report the violation.**

---

# 🔍 PHASE 0 — REQUIRED PRIORS CHECK

Priors before posteriors. Before reading any task-specific evidence (current traces, current ROM state, current spec content, current investigation reports, current source files), the agent reads the project's curated memory and issue ledger. This phase establishes what is already known so the agent does not silently rediscover, contradict, or duplicate it.

## §0.1 — Read the baseline (in order)

1. `KNOWN_FINDINGS.md` (full file, including the rulebook preamble and the deferred-candidates appendix)
2. `OPEN_ISSUES.md`
3. `CLOSED_ISSUES.md`

Reading order is load-bearing. Do NOT read task-specific evidence until Phase 0 is complete.

## §0.2 — Produce the Phase 0 baseline statement

State the following block, populated with task-specific values, before any further work:

```
Relevant priors from KNOWN_FINDINGS:
  - KF-NNN (Title) — Confidence: [CONFIRMED/STRONG/WORKING_HYPOTHESIS];
    applies because [specific reason this task touches this finding's subject]
  - [additional KF entries...]
  (or: No KNOWN_FINDINGS entries apply to this task.)

Rediscovery Hazard HIGH findings touched (if any):
  - KF-NNN (Title) — HIGH; canonical reading: [one-sentence summary];
    this task [respects/extends/tests] that reading because [reason]
  (or: No HIGH-hazard findings touched.)

Deferred-appendix entries relevant to this task (if any):
  - DEF-NNN — relevant because [reason]; not treated as canonical prior
  (or: No deferred entries relevant.)

Task classification (exactly one):
  - EXTENDING — this task refines, corroborates, or tests the working
    hypotheses of an existing KF entry (cite KF-NNN)
  - NEW — this task investigates system behavior not currently indexed in KNOWN_FINDINGS
  - INFRASTRUCTURE — this task does not investigate system behavior;
    it modifies project tooling, process, spec, gate, build pipeline,
    naming, documentation, or workflow

Open/Closed issues touched:
  - OPEN-NNN — [touched / unblocked / blocked by / context only]
  - CLOSED-NNN — [referenced for context / supersedes prior reading]
  (or: No issues touched.)

Contradiction of CONFIRMED or STRONG finding detected during Phase 0 read:
  NONE
  (or: STOP — see §0.4)
```

## §0.3 — Task classification semantics

**EXTENDING.** The task refines, corroborates, or tests a KNOWN_FINDINGS entry. Cite the specific KF-NNN. The task may produce a propose-update output that adds evidence, refines confidence, or extends scope of that entry.

**NEW.** The task investigates system behavior that is not yet indexed in KNOWN_FINDINGS. The task may produce a propose-update output that adds a new KF-NNN entry (subject to the curation discipline established in the KNOWN_FINDINGS rulebook).

**INFRASTRUCTURE.** The task does not investigate system behavior. It modifies project tooling, process, spec, build pipeline, naming conventions, documentation structure, or workflow. INFRASTRUCTURE tasks do NOT produce KNOWN_FINDINGS updates. The expected propose-update output for an INFRASTRUCTURE task is "No new finding to index" with the rationale "this task is INFRASTRUCTURE per Phase 0 classification."

INFRASTRUCTURE is a first-class classification. Most project tasks are infrastructure work (gate hygiene, ID splits, schema changes, pipeline modifications). Forcing them into EXTENDING or NEW would invite either inaccuracy or invented system-behavior claims. The classification is honest about what kind of work is happening.

## §0.4 — Contradiction handling

If the Phase 0 read or subsequent task evidence surfaces a contradiction of a CONFIRMED or STRONG KNOWN_FINDINGS entry, the agent STOPs and reports. Contradiction is NOT silently rewritten.

The contradiction must be classified before any finding revision is considered. Six classes:

1. **Observational** — task evidence measures something that conflicts with the KF entry's stated measurement (most serious; possibly the KF entry is wrong)
2. **Interpretive** — task's reading of evidence conflicts with the KF entry's reading (often resolvable; possibly the KF entry needs nuance)
3. **Emulator-specific** — contradiction appears in one emulator but not another (OPEN-003-style; likely needs deferred-appendix treatment until reconciled)
4. **Build-specific** — contradiction appears in a specific build context that may not generalize (possibly the KF entry needs BUILD_SPECIFIC scoping)
5. **Instrumentation-specific** — contradiction is an artifact of how evidence was gathered, not actual behavior (the KF entry may be correct and the contradiction is in the instrumentation)
6. **Architectural** — contradiction reflects a genuine change in project state since the KF entry was written (possibly the KF entry needs supersession to a SUPERSEDED status with a successor entry)

The contradiction-classification statement is mandatory before any revision proposal:

```
Contradiction of KF-NNN (Title) detected:
  Class: [observational | interpretive | emulator-specific | build-specific | instrumentation-specific | architectural]
  Task evidence: [cite the specific evidence]
  Existing KF claim: [quote the specific KF claim that's contradicted]
  Reconciliation hypothesis: [agent's best read; explicitly labeled as recommendation, not decision]
  Routing: STOP — await Tighe/Chad Sr. review before any KF entry revision is considered
```

The contradiction-classification record is itself valuable institutional memory. Even if the contradiction is later resolved as "no real contradiction" (e.g., agent misread the KF entry), the classification record helps future agents recognize similar near-contradictions.

## §0.5 — Phase 0 STOP conditions

Phase 0 STOPs immediately if:

- `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, or `CLOSED_ISSUES.md` cannot be read
- The Phase 0 read itself surfaces a contradiction of a CONFIRMED or STRONG finding (see §0.4)
- Task classification cannot be honestly made (the task doesn't cleanly fit EXTENDING, NEW, or INFRASTRUCTURE — report this rather than forcing a fit)

A Phase 0 STOP halts the entire task. Do not proceed to OBJECTIVE or any subsequent phase. Report the STOP and await Tighe/Chad Sr. direction.

## §0.6 — What Phase 0 is NOT

Phase 0 is not a request for permission. The agent does not wait for human acknowledgment between Phase 0 and the OBJECTIVE phase unless a STOP fired. The baseline statement is for the audit trail; once produced, the agent proceeds to OBJECTIVE under the priors that statement establishes.

Phase 0 is not "skim KNOWN_FINDINGS for relevant entries." It is reading the full file. The rulebook preamble of `KNOWN_FINDINGS.md` sets editorial discipline that the agent must follow for any propose-update output later in the task; that preamble is read fresh each task.

Phase 0 is not optional for INFRASTRUCTURE tasks. Even tasks that produce no new finding still read the baseline and produce the statement; INFRASTRUCTURE tasks will typically show "No KNOWN_FINDINGS entries apply" and end the task with "No new finding to index — INFRASTRUCTURE classification."

---

# 🎯 OBJECTIVE

State the exact goal in one sentence.

---

# 🧠 PROJECT MODEL (MANDATORY CONTEXT)

This project transforms arcade Rastan to run on Sega Genesis hardware.

**The arcade code is the program. It is morphed to run on Genesis. It is not wrapped.**

- Arcade code owns execution, timing, and frame progression 100%
- The arcade VBlank is the only frame authority — it is morphed to be Genesis-compatible, not replaced
- Genesis-side code is helper routines only: called by arcade code, perform one hardware task, return with RTS
- All rendering flows through WRAM staging buffers → VBlank commit → VDP
- No framebuffer emulation, no hardware mirroring, no shadowing
- No separate Genesis runtime, no Genesis-owned loop, no Genesis-owned VBlank

**Reference:** `ARCHITECTURE.md`, `RULES.md`

---

# 🚨 PRIME DIRECTIVE (NON-NEGOTIABLE)

NO SCAFFOLDING. EVER.

Every line of code must belong in the final production ROM.

Ask: *Would this exist in the shipping ROM?*  
If not — it does not belong here. Do not write it.

There are no exceptions. There is no "we'll remove it later." If a bug exists, fix the real system.

## CONTROL FLOW INVARIANT

At all times, the arcade code must remain in continuous control of execution.

Any control transfer that does not return directly to arcade flow via RTS is a violation.

## PHASE 0 DISCIPLINE (DO NOT)

- Do NOT skip Phase 0 or proceed to OBJECTIVE before producing the Phase 0 baseline statement.
- Do NOT read task-specific evidence before completing Phase 0.
- Do NOT force a task classification that doesn't honestly fit. If the task is neither EXTENDING, NEW, nor INFRASTRUCTURE, STOP and report.
- Do NOT silently revise a KNOWN_FINDINGS entry that current evidence appears to contradict. Contradictions are STOPped and classified per §0.4.
- Do NOT smuggle interpretation, causality, or intent into task report Finding statements. Reports describe observable system behavior; interpretation goes in explicitly labeled sections (Working hypotheses, Use as prior, etc.). The observation-vs-interpretation discipline applies to task reports themselves, not just to KNOWN_FINDINGS entries.
- Do NOT propose KNOWN_FINDINGS updates for INFRASTRUCTURE tasks. INFRASTRUCTURE work does not produce system-behavior findings; the expected propose-update output is "No new finding to index — INFRASTRUCTURE classification."

---

# 🐛 OPEN/CLOSED ISSUES IMPACT — REQUIRED

This project maintains two issue ledgers that all agents must consult and update:

- `OPEN_ISSUES.md` — unresolved issues
- `CLOSED_ISSUES.md` — resolved issues with closure metadata

**Before work:**
1. Read `OPEN_ISSUES.md`.
2. Read `CLOSED_ISSUES.md`.
3. Identify which open issues this task touches.
4. Do not reopen closed issues unless new evidence directly contradicts the closure note.

**During work:**
- If a new unresolved issue is discovered, add it to `OPEN_ISSUES.md` BEFORE final response.
- If an issue is resolved, move it from `OPEN_ISSUES.md` to `CLOSED_ISSUES.md` with full closure metadata (closing build, evidence, closure note).
- Do not delete issue history.
- Do not close an issue without evidence and closure condition citation.

**Final response must include "Open/Closed Issues Impact" section.** See REQUIRED FINAL RESPONSE FORMAT.

---

# ⚠️ GLOBAL RULES (APPLY ALWAYS)

1. NO GUESSING  
2. SINGLE TARGET ONLY  
3. ADDRESS SPACE MUST BE EXPLICIT — every address labeled with its space: `arcade_pc`, `genesis_rom_offset`, `runtime_genesis_pc`, or `HW_ADDRESS/chip/region`  
4. NO UNAUTHORIZED CHANGES  
5. STOP CONDITIONS (MANDATORY) — stop and report rather than work around  
6. NO MEMORY SHADOWING  
7. ALL OUTPUT THROUGH STAGING BUFFERS  
8. NO SCAFFOLDING (see PRIME DIRECTIVE)  
9. NO MISREPRESENTATION  
10. NO HEURISTIC MAPPING  
11. NO IMPLEMENTATION (for design tasks)  
12. TOTAL COVERAGE REQUIRED  
13. NON-ROM ADDRESSES MUST BE EXPLICITLY CLASSIFIED  
14. NO TEST CODE — no scaffolding, no debug paths, no temporary systems, no alternate execution paths. Production-intent only.  
15. ARCADE OWNS EXECUTION — any proposed change that gives Genesis code control-flow ownership is a bug, not a solution  

---

# 📚 REQUIRED READING (MANDATORY)

Before ANY work:

1. `RULES.md` — read completely
2. `ARCHITECTURE.md` — read completely
3. `KNOWN_FINDINGS.md` — curated long-term priors; full file, including rulebook preamble and deferred-candidates appendix
4. `OPEN_ISSUES.md` — read all open issues; identify which this task touches
5. `CLOSED_ISSUES.md` — read closed issues to avoid re-investigating resolved questions
6. `AGENTS_LOG.md` — latest entries first
7. Task-specific source files / design docs / evidence

Reading order is load-bearing: project rules → curated priors → issue ledger → recent activity → task-specific evidence.

**FAILURE TO READ = INVALID RESULT**

---

# 📄 REQUIRED DESIGN DOCUMENT

`docs/design/<Agent>_<task>.md`

Must ALWAYS be produced — even on STOP.

---

# 🛑 STOP CONDITIONS

Stop immediately and report if:

- Any proposed change violates `RULES.md` or `ARCHITECTURE.md`
- Genesis code would own control flow
- Boot/init would be re-entered during gameplay
- A Genesis-side lifecycle or state machine would be introduced
- Test code or scaffolding would be added
- The change cannot be proven correct from existing evidence
- Phase 0 cannot be completed (see §0.5)
- During Phase 0 or any subsequent phase, current evidence directly contradicts a CONFIRMED or STRONG KNOWN_FINDINGS entry. (Refinement of a finding — the finding is right but the current task extends or narrows it — is NOT a STOP; it is handled in the propose-update output. Direct contradiction — the finding's substantive claim is wrong — IS a STOP. Contradictions are classified per §0.4 before any revision is considered.)
- The task's findings would require demoting an existing CONFIRMED or STRONG finding to SUPERSEDED status. (Working hypotheses can be demoted by the propose-update process; CONFIRMED/STRONG demotions require Tighe/Chad Sr. review via the contradiction-classification path.)

Do not work around a STOP condition. Report it.

---

# 🧾 AGENTS_LOG.md REQUIREMENT (APPEND ONLY)

## [Agent — Type, Short Title]

* files changed:
* build produced: YES/NO
* ROM path:
* root cause confirmed: YES/NO
* fix implemented: YES/NO
* no unrelated changes: YES/NO

**This is a floor, not a ceiling.** Include:
- exact addresses
- trace references
- disassembly references
- emulator behavior
- verification steps

---

# 📤 REQUIRED FINAL RESPONSE FORMAT
[Agent — Type, Short Title]
Files created/modified:
Build produced: YES/NO
ROM path:
Root cause confirmed: YES/NO
Fix implemented: YES/NO
No unrelated changes: YES/NO
Architecture compliance: CONFIRMED / VIOLATION FOUND — [describe]
Verification result:
USER MUST VERIFY: [item]
Open/Closed Issues Impact:
- Open issues touched: [IDs or NONE]
- New issues opened: [IDs or NONE]
- Issues closed: [IDs or NONE]
- Issues intentionally deferred: [IDs or NONE]

KNOWN_FINDINGS impact:

Pick exactly one of A / B / C / D:

```
Option A — No new finding to index.
  Rationale: [one sentence explaining why no system-behavior finding emerged.
  Expected default for INFRASTRUCTURE tasks. Also expected for EXTENDING
  tasks that confirm but do not refine the existing finding.]

Option B — Proposed new entry:
  [Full entry in KF-NNN format per KNOWN_FINDINGS.md rulebook preamble.
  Next available KF-NNN number. All metadata fields populated.
  Confidence rating proposed with reasoning. Tighe/Chad Sr. approve
  before the entry is merged into KNOWN_FINDINGS.md.]

Option C — Proposed update to KF-NNN:
  Current entry: [cite section being changed]
  Proposed change: [specific edit, with reasoning]
  Type: [refinement / supersession / confidence change /
         applicability change / status change]
  Citations: [cited evidence from this task supporting the change]
  Tighe/Chad Sr. approve before the change is merged.

Option D — Contradiction-classification report (only when §0.4 fired):
  See §0.4 contradiction-classification statement.
  Routing: STOP — Tighe/Chad Sr. review required.
```

Note: Option A is the expected default for INFRASTRUCTURE tasks and most EXTENDING tasks. Tasks that genuinely discover or refine durable system behavior pick B or C. Tasks that detect contradiction pick D and STOP. Picking B or C for an INFRASTRUCTURE task is a failure condition — those changes belong in design docs and AGENTS_LOG, not KNOWN_FINDINGS.

## Observation vs. interpretation in task reports

Task reports describe observable system behavior — what code did, what addresses were involved, what bytes were verified, what runtime states were measured. Interpretation, causality, and intent attribution belong only in explicitly labeled sections (Working hypotheses, Use as prior, Reconciliation hypothesis, etc.).

- **BAD:** "The system intentionally resets because bootstrap progression is broken."
- **GOOD:** "Watchdog expires before any observed kick site executes, producing repeated bootstrap re-entry."

The bad version mixes inferred intent ("intentionally"), inferred causality ("because"), and characterization ("broken") into a single sentence presented as fact. The good version is mechanical.

This discipline applies to all report Finding statements, not just to KNOWN_FINDINGS entries. Reports that smuggle interpretation into Finding statements contaminate any KNOWN_FINDINGS entries derived from them.

---

# 🚫 FAILURE CONDITIONS

- Guessing  
- Skipping verification  
- Incorrect address mapping  
- Scaffolding or test code  
- Misrepresentation  
- Missing documentation  
- Any violation of RULES.md or ARCHITECTURE.md  
- Genesis code owning control flow  
- Re-entry into boot/init during gameplay  
- Skipping Phase 0 or reading task-specific evidence before completing it
- Proceeding past a Phase 0 STOP
- Proceeding past a CONFIRMED/STRONG contradiction without STOPping
- Silently revising a KNOWN_FINDINGS entry that current evidence appears to contradict
- Failing to classify a detected contradiction per §0.4 before proposing any revision
- Proposing a KNOWN_FINDINGS entry for INFRASTRUCTURE work (gate changes, schema changes, naming hygiene, build pipeline, tooling)
- Proposing a KNOWN_FINDINGS entry that contains interpretation, causality, or intent attribution in the Finding statement (interpretation belongs only in Working hypotheses or Use as prior sections)
- Forcing a task classification that doesn't honestly fit (e.g., claiming a target-selection task is EXTENDING when it's actually NEW, or claiming an INFRASTRUCTURE task is EXTENDING to pad the propose-update output)
- Self-promoting confidence ratings (e.g., proposing a new entry as CONFIRMED when the evidence supports only STRONG or WORKING_HYPOTHESIS). Confidence ratings are conservative; Tighe/Chad Sr. may downgrade a proposed rating during review.
- Silently updating KNOWN_FINDINGS rather than producing a propose-update output for human review
- Smuggling interpretation, causality, or intent into task report Finding statements (not just KNOWN_FINDINGS entries — the observation-vs-interpretation discipline applies to reports themselves)

---

# 🧠 FINAL INSTRUCTION

Complete Phase 1 first. Only proceed if proven correct against `RULES.md` and `ARCHITECTURE.md`.

Do not deviate. Do not patch around architectural violations — report them.

The arcade code is the program. Keep it that way.