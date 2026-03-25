# AGENTS.md

This file is the working guide for coding agents in this repository.

## Mission

Port arcade-accurate `Rastan` behavior to Sega Genesis while preserving original
assets and as much original game logic as possible.

Current development preference:

- avoid one-off crash-site hacks
- keep rules declarative in `specs/`
- favor build-time translation/remap over runtime patch tricks

## Repo map

- `apps/rastan/`: active SGDK launcher/baseline app
- `tools/translation/`: patchers and translation tooling
- `specs/`: source-of-truth rules for layout/remap/fixups
- `build/`: disposable generated files and manifests
- `dist/`: released ROM builds
- `docs/project/`: execution plans and decision log
- `docs/reverse-engineering/`: disassembly notes and behavior references
- `docs/reference/`: external hardware docs and captures
- `attic/`: historical experiments (not baseline)

## Build and run

Always load local toolchain first:

```bash
source tools/setup_env.sh
```

Primary build commands:

```bash
make -C apps/rastan release
make -C apps/rastan release-nohook
make -C apps/rastan debug
```

Output ROMs:

- working ROM: `apps/rastan/out/rom.bin`
- named builds: `dist/Rastan_<n>_<timestamp>.bin`

## Current startup/title bring-up status

- Stable launcher baseline exists in recent `56`-style hooked flow.
- Normal mode live front-end attempts (`57`/`59`) still fail with control-flow
  issues (e.g. falling into `0x03816B` data path).
- Test mode is currently stable but still routed to preview/debug path, not the
  full board-style diagnostics screen.

## Critical engineering constraints

1. Prefer holistic remap changes over incremental trampoline stepping.
2. Keep manifests as outputs, specs as inputs.
3. Preserve original `maincpu` behavior as much as possible; remap hardware
   contracts rather than rewriting gameplay logic.
4. Minimize shadow/backing RAM usage to only what the translated hardware
   contract needs.
5. Treat normal `START RASTAN` handoff as one-way target architecture.

## Long-term rendering architecture

The confirmed rendering strategy for this port is
**direct opcode replacement with shift-table reflow**.

### What this means

The Python patching pipeline reads the original arcade
ROM files directly. For each arcade hardware register
write that needs to become a Genesis VDP operation, the
patcher replaces the original 68000 instruction bytes
with a Genesis-native instruction sequence inline.

When a replacement sequence is longer than the original
instruction, the patcher inserts the extra bytes at that
location. All subsequent code shifts forward. The patcher
maintains a shift table — a sorted list of insertion
points and sizes — and applies accumulated offsets to
every absolute and relative reference in the binary.

No trampolines. No NOP padding. No runtime interception.
The final ROM contains only Genesis-native code.

### Shift table reference types

Every reference type in the 68000 binary must be fixed:
- Absolute: JSR, JMP, LEA, MOVEA.L, PEA operands
- Relative: BRA, BSR, Bcc displacements (recalculated)
- Tables: jump table word displacements (recalculated)

### Hardware regions and their replacement targets

| Arcade address      | Hardware          | Genesis target         |
|---------------------|-------------------|------------------------|
| 0xC00000-0xC0FFFF   | PC080SN tilemap   | VDP nametable writes   |
| 0xC20000-0xC20003   | PC080SN Y scroll  | VDP scroll registers   |
| 0xC40000-0xC40003   | PC080SN X scroll  | VDP scroll registers   |
| 0xD00000-0xD03FFF   | PC090OJ sprites   | VDP sprite table       |
| 0x800000 region     | CLCS palette RAM  | PAL_setColor calls     |

### What stays as runtime shadows

These regions are NOT replaced by opcode rewriting.
They remain as runtime shadow variables:
- 0x100000 arcade work RAM (genesistan_arcade_workram_words)
- 0x390000 input registers
- 0x3E0000 sound command registers (PC060HA mailbox)

### Spec entry format for replacements

New entry type in specs/startup_title_remap.json:

  {
    "type": "opcode_replace",
    "address": "0x03XXXX",
    "original_bytes": "<hex — validated before patching>",
    "replacement_bytes": "<Genesis instruction sequence>",
    "comment": "human-readable description"
  }

The patcher validates original_bytes match before
applying any replacement. Mismatches abort the build.

### Prerequisites before any opcode replacement

1. ROM fingerprints captured in build/rom_inventory.json
2. PC080SN tilemap word bit format confirmed
3. validate_specs.py passes cleanly
4. Stack gap >= 0x4000 confirmed in linker map

### Shadow arrays deleted as regions are replaced

Once opcode replacement is verified for a region,
its shadow array is deleted from BSS. Deletion order:
1. C-Window SRAM pages — after tilemap rewrites verified
2. genesistan_shadow_d00000_words — after sprite rewrites
3. Scroll/palette shadows — after those rewrites

## Files to check before touching startup remap

- `docs/project/startup_title_remap_plan.md`
- `docs/project/decision_log.md`
- `specs/startup_title_remap.json`
- `tools/translation/postpatch_startup_rom.py`
- `apps/rastan/src/startup_trampoline.s`
- `apps/rastan/src/startup_bridge.c`
- `apps/rastan/src/main.c`

## MAME and reverse-engineering references

- Rastan MAME driver: `src/mame/taito/rastan.cpp` (external reference)
- Local disassembly: `build/maincpu.disasm.txt`
- 68000 reference manual:
  - `docs/reference/hardware/motorola_68000_reference_manual.pdf`

## Agent guardrails

- Do not treat `attic/` behavior as authoritative.
- Do not silently change build architecture (copy mode, ROM base, entry flow)
  without updating `docs/project/startup_title_remap_plan.md` and
  `docs/project/decision_log.md`.
- If a change affects remap logic, update `specs/` first (or in the same change)
  and then update the patcher.
- Avoid destructive git commands (`reset --hard`, checkout rollback) unless
  explicitly requested.

## Preferred workflow for substantial remap changes

1. Update plan/decision docs.
2. Update spec rules in `specs/`.
3. Update patcher/tooling to consume spec.
4. Build with `make -C apps/rastan debug`.
5. Validate generated manifests under `build/rastan/`.
6. Then produce a release build for emulator testing.


## Team Structure

### Claude (Technical Lead)
Platform: claude.ai chat (this session)
Role: Architecture, disassembly analysis, hardware research,
prompt design, build review, steering.
Does not have direct file access. Receives uploads and
reports from Tighe. Issues directives via Tighe.

### Andy (Claude VS Code Extension)
Platform: VS Code Claude extension
Role: Primary implementer. Has direct file system access
to the workspace. Receives implementation prompts from
Claude via Tighe. Reads AGENTS_LOG.md and AGENTS.md
before every task. Re-reads AGENTS_LOG.md from disk
immediately before any append.

### Cody (Codex / VS Code Copilot)
Platform: VS Code Copilot chat
Role: Secondary implementer. Used when Andy is unavailable
or for parallel tasks. Same discipline as Andy — reads
logs before starting, re-reads before appending.

### Chad (ChatGPT)
Platform: ChatGPT
Role: High-level management and bridge to Tighe. Reviews
directives from Claude before they go to implementers.
Escalates conflicts or ambiguities to Tighe rather than
resolving them independently.

### Alan (Gemini VS Code Extension)
Platform: Gemini VS Code extension
Role: Specialist consultant. Called in for fresh analysis
when the team is stuck. Does not implement. Appends
analysis to AGENTS_LOG.md only. Confirmed the KEEP()
linker solution in Build 96.

### Gemini (Google Gemini)
Platform: Gemini
Role: Specialist consultant. Available for second opinions,
cross-referencing hardware documentation, or analysis
tasks where a different model perspective is useful.

### Tighe (Human Supervisor)
Role: Project owner and final authority. Coordinates
between all agents. Commits and pushes to GitHub.
Tests builds on BlastEm and MAME. Makes final decisions
on architecture and scope.

## Authority Structure

Technical decisions: Claude
Implementation: Andy (primary), Cody (secondary)
Management review: Chad
Specialist analysis: Alan, Gemini
Final authority: Tighe

If any agent's guidance conflicts with Claude's directives,
escalate to Tighe. Do not resolve independently.

## FUTURE OPTIMISATIONS (post full VDP implementation)
- C-Window shadow arrays (genesistan_shadow_c00000_words,
  c04000, c08000, c0c000) can be removed entirely once all
  C-Window writes are replaced by VDP opcode replacements.
  ROM will no longer need SRAM at 0x200000 and will operate
  within standard 64KB Genesis WRAM only.
- Horizontal flip and vertical mirror routines in the arcade
  code can be removed or NOPped — the Genesis VDP handles
  flip and mirror natively per-tile in the nametable entry
  bits, so the arcade software flip logic is redundant.
- Remove SRAM header declaration from ROM header once
  C-Window shadows are eliminated.`
## Palette Architecture (decided Build 112 session)

The arcade palette RAM (2048 entries, 4096 bytes)
is pre-converted to Genesis VDP format during the
patching process and stored in ROM as a static
symbol genesistan_palette_rom_table. No runtime
colour conversion is performed.

Conversion formula (per entry):
  arcade format: xBGR-555
    bits 14:10 = Blue (5-bit)
    bits 9:5   = Green (5-bit)
    bits 4:0   = Red (5-bit)
  Genesis format: 0000 BBB0 GGG0 RRR0
    bits 11:9  = Blue (3-bit, top 3 of arcade)
    bits 7:5   = Green (3-bit, top 3 of arcade)
    bits 3:1   = Red (3-bit, top 3 of arcade)
  R_gen = (R_arc >> 2) << 1
  G_gen = (G_arc >> 2) << 5
  B_gen = (B_arc >> 2) << 9

Tile attribute palette field (9-bit):
  bits 8:7 → Genesis palette line (0-3)
  bits 6:4 → sub-bank select within line
  bits 3:0 → colour index within 16-colour bank

At runtime load_arcade_palette() is a direct
DMA copy from ROM table to CRAM. No math.

genesistan_palette_buffer[64] in WRAM is
temporary staging only during Build 111/112
transition. Removed in Build 113 once ROM table
is in place.

## Tile Cache Architecture (decided Build 112 session)

The PC080SN has 16384 tiles × 32 bytes = 512KB.
Genesis VRAM holds ~1164 tiles in the cache
region (slots 20–1023 plus 1280–1439).

Cache design (per-slot, ~4.6KB WRAM total):
  uint16_t cache_slot_to_arcade[1164]  — 2.3KB
    which arcade tile occupies each slot
  uint16_t cache_slot_lru[1164]        — 2.3KB
    LRU counter per slot
  uint16_t cache_lru_clock             — 2 bytes
    global incrementing counter

Cache lookup: linear scan of 1164 slots.
Working set per scene: 200-400 tiles.
Cache misses trigger VDP_loadTileData() DMA
from rastan_pc080sn ROM (32 bytes per tile).

Full 16384-entry forward map is NOT feasible
in WRAM (would require 32KB+). Per-slot reverse
map only.

No ROM banking in PC080SN or PC090OJ. All 16384
tiles always accessible. Different sub-stages
(outdoor, fortress, boss) use different tile
index ranges within the same ROM.

## VDP Layer Mapping (confirmed Build 112 session)

  Arcade BG layer 0 (C-Window page 0,
    A5@(4256) starts 0xC00400)
    → Genesis Plane B (VRAM 0xC000)
    → nametable position: offset into page 0
      divided by 2 = cell index

  Arcade FG layer 1 (C-Window page 2,
    A5@(4260) starts 0xC08400)
    → Genesis Plane A (VRAM 0xE000)
    → FG layer IS the text/HUD layer
    → no separate text layer exists

  PC090OJ sprites → Genesis VDP SAT
    each entry always 16×16 pixels (one cell)
    large chars (GAME OVER) = multiple entries
    no size field in sprite word

  Both planes start at row 8 col 0 (offset 0x400
  into their respective C-Window pages).

## Project Rule Update — Mandatory Replacement Discipline
- Shift-table / proper redirected replacement is now mandatory by default.
- NOP/RTS/equal-length workaround/same-size redirect are forbidden without prior approval.
- Any unapproved bypass-style patch is considered broken.
- “Equal-length constraint” is not an acceptable final justification when broader hook/stub/shift-table mechanisms exist.

## Project Rule Update — Definition of Success

Success is defined as FOLLOWING INSTRUCTIONS EXACTLY.

Success is NOT defined as:
- “no crash”
- “more stable”
- “runs longer”
- “fewer exceptions”

If a directive is given (e.g. fix a crash, replace a system, remove a dependency):

- The directive itself defines success
- Partial compliance is NOT success
- Workarounds that change behavior outside the directive are NOT success

Crash handling rule:
- If a crash is reported and the directive is to fix it:
  - The crash must be resolved WITHOUT altering unrelated systems
  - No bypass (NOP/RTS) is allowed unless explicitly approved
  - No functionality may be removed unless explicitly approved

Forbidden behaviors:
- “stabilizing” by removing logic
- masking crashes instead of fixing root cause
- modifying unrelated systems to avoid failure
- redefining scope of the task

If a proper fix is not possible:
- STOP
- report the limitation
- request guidance

Do NOT improvise outside the directive.

## Project Rule Update — Patch Discipline

- Shift-table / proper redirected replacement is mandatory
- NOP/RTS/equal-length workaround is forbidden without approval
- Any unapproved bypass is considered broken

Combined with success definition:
- A crash “fixed” via bypass is NOT considered fixed

## 🚨 Definition of Done (MANDATORY)

A task is ONLY considered complete if ALL of the following are true:

* No use of:

  * NOP (unless explicitly approved)
  * RTS as a bypass
  * equal-length replacement hacks
  * shadow RAM (full or partial)
  * “stability” or “fallback” logic

* The fix:

  * preserves correct execution behavior
  * preserves correct state flow
  * matches arcade logic expectations

* “No crash” is NOT success

* Visual output must be real (VDP-backed), not suppressed or bypassed

* All fixes must align with shift-table patching architecture

If any shortcut is used → the fix is INVALID

## 🧠 State Causality Rule (MANDATORY BEFORE ANY FIX)

Before applying ANY patch, you MUST answer:

1. What state should exist at this PC?
2. Which earlier code is responsible for creating that state?
3. Why did that state not get created?

If these are not proven:
→ DO NOT PATCH

Fix the cause, not the symptom.

## ⏱ Execution Order Integrity Rule

Initialization is NOT a function — it is a timeline.

* State is created across multiple phases
* Order of execution is critical
* Moving or skipping writes breaks downstream logic

DO NOT:

* reorder initialization blindly
* “set values earlier” without proving correctness
* manually seed values unless absolutely unavoidable

ALWAYS:

* restore correct execution order
* preserve original state sequencing

## 🔍 Validation Requirements (REQUIRED)

Every change MUST include validation evidence:

* What state changed?
* Where is it written?
* When is it written (relative order)?
* What downstream logic depends on it?

AND:

* Confirm no unintended side effects
* Confirm no state is being skipped or duplicated

## 🤖 Agent Operating Rules

All agents MUST:

* Read:

  * `AGENTS.md`
  * latest relevant section of `AGENTS_LOG.md`

* Treat `AGENTS_LOG.md` as the **source of current truth**

* NEVER:

  * rely on summaries
  * assume previous fixes were correct
  * reuse old approaches without verification

* ALWAYS:

  * cite the build / log section being continued
  * verify assumptions against current state
