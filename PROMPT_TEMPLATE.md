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
3. `AGENTS_LOG.md` — latest entries first
4. `docs/design/Andy_init_staging_state_split_design.md` — if relevant
5. Any files explicitly listed in this prompt

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

---

# 🧠 FINAL INSTRUCTION

Complete Phase 1 first. Only proceed if proven correct against `RULES.md` and `ARCHITECTURE.md`.

Do not deviate. Do not patch around architectural violations — report them.

The arcade code is the program. Keep it that way.