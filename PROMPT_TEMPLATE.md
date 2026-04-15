# 🔒 AGENT PROMPT TEMPLATE (STRICT, NO WEASEL ROOM)

**Agent:** Andy / Cody  
**Type:** Analysis / Verification / Implementation / Hybrid  
**Build Context:** (e.g., Build 0027, rastan-direct)  

---

# 🎯 OBJECTIVE

State the exact goal in one sentence.

---

# 🧠 PROJECT MODEL (MANDATORY CONTEXT)

This project follows the Rainbow Islands arcade → Sega Genesis translation model.

- Arcade produces intent
- Genesis translates intent → VDP operations
- No framebuffer emulation
- No shadowing
- All rendering via staging + VBlank commit

---

# ⚠️ GLOBAL RULES (APPLY ALWAYS)

1. NO GUESSING  
2. SINGLE TARGET ONLY  
3. ADDRESS SPACE MUST BE EXPLICIT  
4. NO UNAUTHORIZED CHANGES  
5. STOP CONDITIONS (MANDATORY)  
6. NO MEMORY SHADOWING  
7. ALL OUTPUT THROUGH STAGING BUFFERS  
8. NO SCAFFOLDING  
9. NO MISREPRESENTATION  

---

# 🔍 PHASE 1 — ANALYSIS / VERIFICATION

Must complete before implementation.

---

# ⚙️ PHASE 2 — IMPLEMENTATION

Scope strictly limited.

---

# 📄 REQUIRED DESIGN DOCUMENT

docs/design/<Agent>_<task>.md

Must include full or partial results (even on STOP).

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

The format above defines the MINIMUM required fields.

You MUST include additional technical detail whenever available, including:

- exact addresses (arcade_pc / runtime_genesis_pc / genesis_rom_offset)
- opcode_replace entries and counts
- patch offsets and byte verification
- trace file paths and log references
- disassembly references
- emulator behavior (BlastEm, Exodus, MAME)
- crash signatures or failure states
- verification steps and observed outcomes

DO NOT reduce detail to match the template.

The template is a floor, NOT a ceiling.

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
- missing docs/logs

---

# 🧠 FINAL INSTRUCTION

Complete Phase 1 first. Only proceed if proven.
