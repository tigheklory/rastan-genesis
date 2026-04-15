# 🔒 AGENT PROMPT TEMPLATE (STRICT, NO WEASEL ROOM)

**Agent:** Andy / Cody  
**Type:** Analysis / Verification / Implementation / Hybrid  
**Build Context:** (e.g., Build 0027, rastan-direct)  

---

# 🎯 OBJECTIVE

State the exact goal in one sentence.

---

# 🧠 PROJECT MODEL (MANDATORY CONTEXT)

This project follows the **Rainbow Islands arcade → Sega Genesis transition model**.

This is the **authoritative reference model and proven path to success**.

Key principles:

- Arcade hardware produces **intent**, not pixels  
- Genesis must **translate intent → VDP operations**  
- No framebuffer emulation  
- No hardware mirroring  
- No shadowing  
- All rendering must flow through staging buffers → VBlank commit  

All solutions MUST align with this model.

---

# 🚨 PRIME DIRECTIVE (NON-NEGOTIABLE)

NO SCAFFOLDING. EVER.

- No temporary systems  
- No reconstruction of data later  
- No approximations  
- No fallback logic  
- No “we’ll fix it later”  

If data is required later, it MUST be recorded at the moment it is created.

If a system cannot be implemented correctly at the source of truth:
→ STOP

A stub that does nothing is acceptable.  
A system that approximates or reconstructs later is NOT.

---

# ⚠️ GLOBAL RULES (APPLY ALWAYS)

1. NO GUESSING  
2. SINGLE TARGET ONLY  
3. ADDRESS SPACE MUST BE EXPLICIT  
4. NO UNAUTHORIZED CHANGES  
5. STOP CONDITIONS (MANDATORY)  
6. NO MEMORY SHADOWING  
7. ALL OUTPUT THROUGH STAGING BUFFERS  
8. NO SCAFFOLDING (see PRIME DIRECTIVE)  
9. NO MISREPRESENTATION  
10. NO HEURISTIC MAPPING  
11. NO IMPLEMENTATION (for design tasks)  
12. TOTAL COVERAGE REQUIRED  
13. NON-ROM ADDRESSES MUST BE EXPLICITLY CLASSIFIED  

---

# 📚 REQUIRED READING (MANDATORY)

Before ANY work:

1. AGENTS_LOG.md (latest entries FIRST)
2. Latest docs in docs/design/
3. All Rainbow Islands reference docs in docs/design/
4. Any files explicitly listed in the prompt

FAILURE TO READ = INVALID RESULT

---

# 📄 REQUIRED DESIGN DOCUMENT

docs/design/<Agent>_<task>.md

Must ALWAYS be produced (even on STOP)

---

# 🧾 AGENTS_LOG.md REQUIREMENT (APPEND ONLY)

## [Agent - Type, Short Title]

* files changed:
* build produced: YES/NO
* ROM path:
* root cause confirmed: YES/NO
* fix implemented: YES/NO
* no unrelated changes: YES/NO

---

## AGENTS_LOG DETAIL REQUIREMENT (IMPORTANT)

The above is MINIMUM.

You MUST include additional technical detail:
- exact addresses
- trace logs
- disassembly references
- emulator behavior
- verification steps

This is a floor, NOT a ceiling.

---

# 📤 REQUIRED FINAL RESPONSE FORMAT

## [Agent - Type, Short Title]

* Files created/modified:
* Build produced: YES/NO
* ROM path:

* Root cause confirmed: YES/NO
* Fix implemented: YES/NO
* No unrelated changes: YES/NO

* Verification result:
  * item: USER MUST VERIFY

---

# 🚫 FAILURE CONDITIONS

- guessing  
- skipping verification  
- incorrect mapping  
- scaffolding  
- misrepresentation  
- missing documentation  

---

# 🧠 FINAL INSTRUCTION

Complete Phase 1 first. Only proceed if proven.

Do not deviate.
