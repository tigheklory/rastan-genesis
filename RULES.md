# RULES.md

## Non-Negotiable Rules

This project follows strict architectural constraints. These rules must never be violated.

---

## 1. Arcade Code Owns Execution

- The arcade code is the program.
- There is no separate Genesis-owned game loop.
- There is no `main_68k` runtime ownership.
- The arcade code must run continuously and retain full control of execution.

---

## 2. No Separate Genesis Runtime

- Genesis code must never:
  - own frame progression
  - own a main loop
  - schedule gameplay
- Genesis code exists only to service hardware.

---

## 3. VBlank Ownership

- The arcade VBlank is the only frame authority.
- There is no separate Genesis VBlank identity.
- Genesis VBlank is only a hardware servicing hook for:
  - VDP commits
  - DMA operations

---

## 4. Helper Functions Only

Genesis-side code must follow this pattern:

- Called by arcade code (JSR/JMP)
- Performs one finite hardware translation or operation
- Returns immediately via `RTS` to arcade-owned execution

**Bounded loops are allowed; unbounded control flow is not.**

- Allowed: a bounded loop that completes **one finite semantic hardware operation**
  and returns — e.g. iterating over a bounded row, column, plane seed, SAT set,
  palette set, or DMA job, where the bound comes from the retained arcade semantic
  operation (how many cells/entries the arcade decision requires).
- Forbidden: unbounded loops, frame waits, polling/spin waits, schedulers, gameplay
  loops, and any control-flow ownership.
- The helper must always return control to arcade-owned execution; it never waits for
  a frame, an event, or a condition, and never keeps running the program.

(The diagnostic-bookmark self-loop of §10 is a separate, explicitly-scoped exception —
it halts for observation and is not a working helper loop.)

Also forbidden in helpers:
- blocking
- scheduling
- control-flow ownership

---

## 5. No Test Code

- No scaffolding
- No temporary systems
- No alternate execution paths
- No debug-only logic that affects architecture

All code must be production-intent.

If there is a bug:
- Fix the real system
- Do not introduce temporary code paths

---

## 6. No Re-Entry Into Boot/Init

- Boot/init code runs once at cold start only
- Arcade code must never jump back into initialization
- Any such behavior is a bug

---

## 7. No Hidden State Machines

- Genesis-side code must not introduce its own lifecycle
- No “restart paths”
- No “safe re-entry”
- No secondary control logic

---

## 8. Arcade Intent → Genesis Execution

- Arcade code expresses intent
- Genesis executes that intent
- No reinterpretation of control flow

---

## 9. If It Doesn’t Belong in Final Build, It Doesn’t Belong Here

Every line of code must answer:

> Would this exist in the final production ROM?

If not, it is forbidden.

---

## 10. Diagnostic Bookmarks

A controlled exception to Rule 5 for evidence collection.

A diagnostic bookmark answers binary reachability questions ("did execution reach this address?") that traces and disassembly cannot answer alone. It does so without altering behavior.

Established by Tighe + Chad agreement; see `AGENTS_LOG.md` entry `[Andy — Add Diagnostic Bookmark Rule]`.

### Anatomy

A bookmark has two parts.

**Helper.** A small, immutable routine in a safe high-ROM region.
- Default body: deterministic self-loop (`bra .` or `jmp .`).
- Produces no side effects: no memory writes, no register clobbers visible to callers, no hardware writes, no return.
- Bytes are immutable across builds; SHA256-verifiable.
- May persist as project infrastructure indefinitely.

**Activator.** An `opcode_replace` entry (or equivalent JMP injection) redirecting execution from a target address to the helper.
- Temporary.
- Must be reverted in the immediately-following ROM-producing build.
- Persistence of an active activator across two consecutive ROM-producing builds is forbidden.
- Non-ROM-producing tasks (evidence reports, classification docs) do not shift the revert obligation; the clock is measured in ROM-producing builds.

### Constraints

- **Observation only.** Activator and helper must not alter game data, dirty flags, staging buffers, hardware register state, return values, rendering output, or downstream control flow that other code depends on. Halting execution at the bookmark IS the observation; that is not a hidden side effect.
- **No supervisor-mode assumption.** `STOP #$2700` is privileged on the 68000 and traps in user mode. Default helper body is a self-loop, not `STOP`. `STOP` is permitted only when supervisor mode is independently proven at the activator's reach point, OR when privilege-violation behavior itself is the observation.
- **ROM, not WRAM.** Helpers in WRAM are vulnerable to the corruption a bookmark is most often used to investigate (bootstrap re-entry, stack overflow, exception-handler bugs).
- **Scoped task.** A bookmark insertion task inserts only the activator. A revert task reverts only the activator. No other source, spec, tool, or build change occurs in either. At most one bookmark cycle is in flight at any time; a single ROM build does not combine an insert with another bookmark's revert.
- **Logged on both ends.** Insert and revert each get an `AGENTS_LOG.md` entry stating: target address, byte sequence before, byte sequence after, helper symbol, helper SHA256, and either the evidence question being answered (insert) or the evidence outcome and next step (revert).
- **Byte-verified against canonical ROM.** "Canonical ROM" means the current canonical post-patch artifact (e.g., `0057.bin` and its sequential successors per OPEN-002). Insert byte sequence is verified against the canonical ROM's bytes at the target address; revert byte sequence is verified to restore exactly those canonical bytes (which may themselves include a production `opcode_replace` patch — the activator does not "see through" to raw arcade bytes); helper SHA256 is verified at build time and on revert. Any mismatch is a STOP condition.

### Distinction from scaffolding

Scaffolding fakes data to make code appear to work. Bookmarks halt execution to confirm what state existed. The first masks bugs by producing misleading partial-success; the second narrows root-cause search by producing binary evidence.

Bookmarks comply with Rule 9. The helper IS final-build infrastructure: immutable, harmless if never reached, present in the shipping ROM. The activator is provably absent by the next ROM-producing build's revert log.

### Out of scope for this rule

The specific helper bytes, symbol name, and build-pipeline integration are defined in `docs/design/Andy_diagnostic_bookmark_helper_design.md`. Bookmark cycles may begin once Tighe approves that design and Cody ships the first build introducing the helper. The helper's resolved address is recorded in `out/symbol.txt` after the first build.

---

## 11. Native PC080SN / PC090OJ Replacement (no chip emulation)

The final architecture must **not** emulate, mirror, shadow, or translate PC080SN or
PC090OJ hardware behavior after the arcade program has specialized its output for those
chips. Preserve the arcade **semantic** decision and cut *before* chip-specific execution;
replace the complete chip tail with **direct Genesis VDP/SAT production**. No software
PC080SN/PC090OJ device, virtual chip RAM, C-window/name-RAM shadow, object-RAM mirror,
generic chip-address translation, or full-map projection as the final design. Any temporary
compatibility path must be explicitly labeled, isolated, non-overwriting, and scheduled for
removal.

**Authoritative details, examples, boundary proof, and review checklist:**
`docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` (mandatory reading before any
PC080SN/PC090OJ work; agents must state the semantic cut and the chip tail being removed).

---

## Numbered ROM Artifact Preservation Rule

Numbered ROM artifacts are evidence and must not be deleted, overwritten, or silently replaced.

If a numbered build, diagnostic build, or candidate ROM is produced, preserve the ROM file, SHA256, size, build counter, config, source patch/diff, and status.

Rejected or broken numbered builds must be preserved and clearly labeled: **REJECTED / NOT ACCEPTED / DIAGNOSTIC ONLY.**

- Do not delete a rejected numbered ROM just because the source was reverted.
- Do not reuse a numbered build slot after a numbered ROM was produced, even if that ROM was later rejected or accidentally deleted.
- If an artifact was accidentally deleted, do not spend time rebuilding it unless Tighe explicitly asks. Instead, document: that it existed; its SHA/size if known; why it was rejected; that the artifact is missing/deleted; that the number is consumed and must not be reused.
- Rolling ROM and accepted build status are separate from artifact preservation. A rejected diagnostic may exist on disk while the rolling ROM remains the prior accepted candidate.
- **Agents must ask before deleting any numbered ROM artifact.**
- Producing or rejecting a numbered artifact requires preservation and advancement to the next number. It is not, by itself, a STOP condition. When a ROM-producing task authorizes implementation and the next correction remains within the same proven technical boundary, agents continue with sequential numbered builds without requesting another directive.

### Consumed / deleted numbers

- **Build 0202** was produced during the failed enemy actor staging attempt (engine-enabled staging locked the player in mode 3 from gameplay start; partial SHA `ede84ca7...`), then deleted. Do not recreate it unless Tighe explicitly asks. Treat 0202 as **consumed by a deleted rejected diagnostic**. The next produced numbered ROM must not silently reuse 0202 (next candidates: Build 0203 main / Build 0204 comparison).

---

## Holistic Replacement and Usage-Efficiency Rules

These rules govern how PC090OJ/PC080SN native-replacement work is scoped and carried out. They
strengthen (never weaken) the rules above; where the native-replacement policy of §11 applies,
these define *how* to pursue it.

1. **TRACE TO THE SEMANTIC OWNER.** A patched function is not automatically the correct
   replacement boundary. If required state (position, attribute, value, visibility, palette,
   layout) is owned elsewhere, follow callers, xrefs, writes and runtime provenance until the
   complete semantic owner is identified.

2. **SPLIT OWNERSHIP IS NOT A STOP CONDITION.** If several arcade routines collectively produce
   one visual/game-semantic object, treat them as **one** replacement subsystem. Split ownership
   expands the conversion boundary; it does not justify a STOP or a partial change.

3. **RETIRE SUBSYSTEMS, NOT SCREENS.** Do not solve shared rendering code separately for title,
   ROUND, story, high-score, gameplay, etc. when a shared semantic producer can be converted once.

4. **NO PATCH ACCUMULATION.** Do not add scene/state gates merely to bypass legacy behavior for
   one more case when the proper solution is to replace the underlying producer family.

5. **EVERY NATIVE-CONVERSION BUILD MUST SHRINK LEGACY.** A native-replacement build must materially
   remove or permanently bypass obsolete PC090OJ/PC080SN code or dependencies. Adding a new native
   path while leaving the same legacy path intact is not completion.

6. **FOLLOW THE NATIVE GENESIS MODEL.** Prefer `semantic state -> native mapping/piece expansion
   -> Genesis staging -> VBlank commit`, using Rainbow Islands / Sonic 1 BuildSprites structural
   lessons. Never recreate the arcade graphics chip in software under another name.

7. **ANALYSIS SERVES IMPLEMENTATION.** Analysis should resolve the provenance needed to implement.
   Do not turn implementation tasks into analysis-only checkpoints unless there is a genuine
   hardware/semantic impossibility.

8. **DO NOT ASK TIGHE TO RESCOPE A CLEAR GOAL INTO TINY TASKS.** When the requested subsystem is
   clear, determine the necessary internal scope yourself and complete it.

9. **MINIMIZE PAID USAGE.** Model/tool usage and repeated iterations cost Tighe real money. Avoid
   redundant traces, rediscovery, unnecessary builds, verbose restatement, repeated STOP reports
   and low-value intermediate work.

10. **STOP MEANS TRUE BLOCKER.** STOP only when exhaustive evidence demonstrates that the requested
    semantic behavior cannot be determined or implemented without violating a project invariant.
    Difficulty, split ownership, a large call graph, cross-screen reuse, or needing additional
    tracing are not STOP reasons.

11. **DO NOT MISREPRESENT PARTIAL WORK.** A scene-specific bypass, dead-write suppression or
    partial producer conversion must not be described as retirement of the whole subsystem.

12. **KEEP THE CODEBASE MOVING TOWARD DELETION.** The expected trajectory is fewer PC090OJ/PC080SN-
    specific producers, records, scans, mirrors, translators and compatibility branches after each
    relevant task.

---

## Summary

Arcade code is the program.

Genesis is the hardware execution layer.

Nothing may violate this separation.
