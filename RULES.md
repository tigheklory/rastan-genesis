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

## Summary

Arcade code is the program.

Genesis is the hardware execution layer.

Nothing may violate this separation.