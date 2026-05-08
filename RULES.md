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
- Performs a hardware translation or operation
- Returns immediately via `RTS`

Forbidden:
- loops
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

## Summary

Arcade code is the program.

Genesis is the hardware execution layer.

Nothing may violate this separation.