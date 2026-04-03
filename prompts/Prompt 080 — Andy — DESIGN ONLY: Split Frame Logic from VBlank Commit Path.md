# Prompt 080 — Andy — DESIGN ONLY: Split Frame Logic from VBlank Commit Path

## [Andy - Design, Split Frame Logic from VBlank Commit Path]

### ROLE

You are acting as:

## ROLE = DESIGN ONLY

You are NOT implementing in this prompt.
You are NOT analyzing loosely in this prompt.
You are producing a precise, staged design for a future implementation.

No code changes.
No “partial implementation.”
No speculative wandering.

---

## OBJECTIVE

Design a controlled migration from the current Build 316/317-style model:

- game logic inside VBlank
- VDP work mixed with logic

to a split model:

### Non-VBlank frame-prep subroutine
- input polling
- arcade/game logic
- WRAM staging
- dirty flags
- state preparation

### VBlank commit-only subroutine
- display-disable / enable
- final scroll commit
- final tilemap commit
- final sprite/SAT commit
- final palette commit
- final VDP register writes as needed

This design is for later implementation.
Do NOT implement it now.

---

## SOURCE OF TRUTH

You MUST use:

- `docs/design/build316_vs_rainbow_islands_genesis_vblank_noninterrupt_vdp_report.md`
- current Build 316/317 source tree
- the current actual VBlank path
- the current actual non-interrupt initialization path
- the Rainbow Islands Genesis execution model from the report

The design must be grounded in the current codebase, not a fantasy rewrite.

---

## HARD SCOPE LOCK

You MUST NOT:

- implement anything
- rewrite the whole engine conceptually
- propose impossible “just move everything” hand-waving
- ignore existing hooks and current Build 316/317 architecture

You MUST design a migration that is:

- phased
- specific
- implementable
- low-ambiguity

---

## REQUIRED DESIGN GOAL

The design must answer:

### What exactly moves OUT of VBlank?
### What exactly stays IN VBlank?
### In what order?
### Which current hooks must stop touching VDP directly?
### Which current hooks can remain but must become staging-only?
### What new frame-prep entrypoint is required?
### How frame synchronization should work?
### What risks must be managed during migration?

---

## REQUIRED TASKS

### TASK 1 — DEFINE THE TARGET END-STATE EXECUTION MODEL

You MUST clearly define the intended final execution model in ordered steps:

#### Non-VBlank frame-prep phase
What runs there, in what order, and why.

#### VBlank commit phase
What runs there, in what order, and why.

This must be explicit and numbered.

---

### TASK 2 — INVENTORY CURRENT BUILD 316/317 VBLANK WORK BY MIGRATION CATEGORY

Classify every major current VBlank subsystem into one of these:

1. must remain in VBlank
2. should move out of VBlank
3. currently mixed and must be split
4. already correctly staged

At minimum include:
- input polling
- arcade tick / game logic
- scroll
- tilemap
- text/title writers
- palette
- sprite/SAT
- scene preload checks
- display enable/disable

---

### TASK 3 — DEFINE THE NEW NON-VBLANK FRAME-PREP SUBROUTINE

You MUST define one concrete future subroutine or phase that will run outside VBlank.

It must specify:
- entry point
- when it runs
- what it reads
- what it writes
- what it stages
- what it must NOT touch

This is the heart of the split.

---

### TASK 4 — DEFINE THE NEW VBLANK COMMIT-ONLY SUBROUTINE

You MUST define one concrete future VBlank commit path that contains only the work that truly belongs there.

You MUST specify:
- exact ordered commit sequence
- display disable/enable placement
- scroll commit placement
- tilemap commit placement
- sprite/SAT commit placement
- palette commit placement
- any register writes

---

### TASK 5 — DEFINE HOOK CONVERSION REQUIREMENTS

For each major current hook type, specify whether it must become:

- non-VBlank staging-only
- VBlank commit-only
- removed/replaced
- left unchanged

At minimum cover:
- scroll hooks
- tilemap hooks
- text writer hooks
- sprite hooks
- scene preload hook/check

---

### TASK 6 — DEFINE THE FRAME SYNCHRONIZATION MODEL

This is critical.

You MUST explain how the future split frame model synchronizes:

- non-VBlank frame-prep
- VBlank commit
- frame completion / next frame start

You MUST address:
- how to avoid racing staged data vs commit
- whether double-buffering is needed
- whether simple “prepare then commit then clear flags” is sufficient
- what the minimal safe model is for this codebase

---

### TASK 7 — DEFINE A PHASED IMPLEMENTATION PLAN

You MUST break the migration into phases.

For each phase:
- exact subsystem
- expected code areas touched
- why this phase order is safest
- what can be validated after that phase

This must be practical, not theoretical.

---

### TASK 8 — IDENTIFY THE SINGLE HIGHEST-RISK PART OF THE SPLIT

Choose one biggest migration risk, such as:
- arcade tick assumptions about interrupt context
- hooks that still directly touch VDP
- sprite timing
- frame synchronization hazards
- another exact risk if proven

Explain it clearly.

---

### TASK 9 — IDENTIFY THE SINGLE BEST FIRST IMPLEMENTATION PHASE

Choose the best first implementation phase after scroll work is finished.

Do NOT implement it.
Just choose and justify it.

---

## REQUIRED DOCUMENT

Create:

`docs/design/frame_logic_vs_vblank_commit_split_design.md`

---

## REQUIRED DOCUMENT STRUCTURE

1. Executive Summary
2. Current Build 316/317 Execution Model
3. Target End-State Execution Model
4. What Moves Out of VBlank
5. What Stays In VBlank
6. New Non-VBlank Frame-Prep Subroutine
7. New VBlank Commit-Only Subroutine
8. Hook Conversion Requirements
9. Frame Synchronization Model
10. Phased Implementation Plan
11. Highest-Risk Part of the Split
12. Best First Implementation Phase
13. Final Verdict

---

## PRESENTATION REQUIREMENTS

The design must be:

- strict
- ordered
- specific
- implementation-ready
- not vague

Use numbered sequences.
Use subsystem tables where helpful.
Do NOT bury the design in prose.

---

## AGENTS_LOG REQUIREMENT

Append exactly:

## [Andy - Design, Split Frame Logic from VBlank Commit Path]

Include:
- document created
- target split model defined: YES/NO
- migration categories completed: YES/NO
- frame synchronization model defined: YES/NO
- highest-risk part identified
- best first implementation phase identified
- no implementation performed

Append at the END of `AGENTS_LOG.md` ONLY.

Do NOT insert at top.
Do NOT insert in middle.

---

## OUTPUT FORMAT (STRICT)

Reply ONLY with:

1. files changed
2. whether the target split model was fully defined
3. highest-risk part identified
4. best first implementation phase identified

NO additional text.

---

## SUCCESS CRITERIA

You succeed ONLY if:

- the split model is fully defined
- VBlank vs non-VBlank responsibilities are clearly separated
- hook conversion requirements are clearly specified
- frame synchronization is addressed concretely
- a phased plan is provided
- one highest-risk part is identified
- one best first implementation phase is identified
- the document is created
- AGENTS_LOG is appended correctly
- no implementation is performed

---

## FAILURE CONDITIONS

FAIL if:

- the design is vague
- it ignores current code structure
- it hand-waves synchronization
- it does not define hook conversion requirements
- it drifts into implementation
- it places AGENTS_LOG incorrectly

---

## FINAL RULE

Design a real migration from “logic + commits inside VBlank” to “frame-prep outside VBlank, commit-only inside VBlank,” grounded in the current codebase and the Rainbow Islands model.

## START NOW