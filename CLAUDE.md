# CLAUDE.md — Project Guidance for Rastan Genesis

This file records permanent project intent for anyone (including AI agents) working on the
Rastan Genesis port. Read it alongside `RULES.md` and `ARCHITECTURE.md` before starting work.

Rastan Genesis is a **hardware-level translation** of the original Taito Rastan arcade program
to the Sega Genesis. The arcade program stays authoritative; only its arcade-chip-specific
*execution* is replaced with native Genesis hardware realization.

---

## Holistic Native-Replacement Mandate

The Rastan Genesis project is a hardware-level translation of the original arcade program, not an
accumulation of compatibility patches.

The original arcade program remains authoritative for gameplay, state, timing, traversal and
semantic decisions. PC090OJ and PC080SN device-specific execution must ultimately be removed and
replaced by native Sega Genesis VDP/SAT realization.

Use Rainbow Islands' native Mega Drive implementation philosophy and Sonic 1's BuildSprites-style
semantic-object → mapping/piece-expansion → sequential SAT production as **structural references
where applicable**. They are examples of clean native Genesis realization — not sources of any
Rastan-specific game logic.

Work by **complete semantic ownership boundaries**, not merely by individual patched functions,
record writers, screens or symptoms.

If a low-level routine lacks required semantic information, **trace upstream** until the complete
semantic owner is found. Split ownership *expands the task boundary*; it is not by itself a reason
to STOP.

Prefer **one coherent producer-family / subsystem replacement that removes legacy code** over
multiple screen-specific gates or small compatibility patches.

Do not create a growing hybrid architecture in which native and legacy renderers are selected by
increasingly specific scene/state conditions.

Every implementation task should seek to make the legacy subsystem **materially smaller**.

The target shape is always:

    original arcade semantic decision
        -> mapping / glyph / piece selection
        -> compact native Genesis sprite/plane production
        -> staged SAT / Plane data
        -> existing arcade-owned VBlank commit

and never:

    arcade semantic state -> emulated PC090OJ/PC080SN record -> compatibility RAM
        -> scan / decode / project -> Genesis output

---

## Canonical Palette-Decision Registry

`specs/palette_decisions.json` is the project's **only** palette-decision registry. Before any
palette analysis or implementation, consult it, preserve the recorded scene/stage context, name
the affected Palette Decision IDs, and inspect the consumers listed by those decisions. Any
change to a palette decision must update that JSON in the same task. Never create or maintain a
duplicate palette mapping registry in Markdown, another spec, source comments, or generated
files; reports may cite IDs and evidence without duplicating registry authority.

Registry statuses are exactly `proven`, `decided`, `provisional`, and `unknown`. Do not use
`confirmed` or introduce another palette-status vocabulary.

---

## Shift-Table Reflow Is the Canonical Replacement Mechanism

**This project does not have a general equal-length patch constraint.** Choose the highest safe
arcade semantic cut first, then use the established translation pipeline to accommodate the
replacement size. Do not move the cut to a worse boundary merely because the native sequence is
longer than the original instruction or byte window.

The current spec has two distinct replacement paths:

- `opcode_replace` entries are deliberately byte-neutral; `postpatch_startup_rom.py` rejects an
  entry whose original and replacement lengths differ.
- `shift_replacements` entries are the canonical variable-length path. They validate the original
  bytes, splice the replacement into the copied arcade program, shift all later copied bytes, and
  build the accumulated shift table used to repair supported references and generate the final
  address correlation.

Therefore, "no room", "will not fit", "must be byte-neutral", or "a BSR/JSR is too large" is not
a valid architectural blocker by itself. It is also not sufficient justification for NOP padding,
an equal-length hack, replacing a larger arcade routine, moving the semantic cut, creating a
trampoline architecture, or duplicating arcade logic. A real blocker must identify the exact site
and reference/relocation class that the **current** tooling cannot safely reflow.

### Current Verified Flow

The Makefile-owned production flow is:

    tools/build_rastan_regions.py -> build/regions/maincpu.bin + ROM inventory
        -> ELF link + nm -> apps/rastan-direct/out/symbol.txt
        -> prepatch ROM + prepatch boot guard
        -> specs/rastan_direct_remap.json
        -> tools/translation/postpatch_startup_rom.py
             -> tools/translation/shift_table_patcher.py for shift_replacements
             -> byte-neutral opcode_replace and declared relocation/table passes
        -> generated manifest + relocation report + address_map.json
        -> postpatch boot guard + postpatch disassembly
        -> tools/translation/verify_canonical_rom.py
        -> numbered ROM only after GATE_PASS

`shift_table_patcher.py` currently repairs 68000 8-bit and 16-bit `BRA`/`BSR`/`Bcc`
displacements, supported absolute-long operands for `JSR`, `JMP`, `PEA`, `LEA`, and `MOVEA.L`,
and explicitly declared 16-bit jump/displacement tables. A short branch that no longer fits must
be promoted deliberately. Automatic jump-table discovery is not implemented, so relevant tables
must be declared. `postpatch_startup_rom.py` separately applies accumulated shifts while handling
declared `absolute_long_pointer_tables`, deferred shifted operands, ordinary replacements, and the
whole-maincpu relocation passes. Do not claim support for an unlisted reference class without
checking the current code.

Original-byte mismatches, invalid target ranges, and branch-displacement overflow fail during
translation. `verify_rastan_direct_boot_guard.py` checks the required boot/vector contract before
and after patching. `verify_canonical_rom.py` validates the resulting manifest/address-map
coverage, canonical replacement counts, source inclusion and release invariants; it is not a
substitute for declaring every relocation class correctly.

### Canonical Pipeline Inventory

| File | Kind | Input / generated | Exact role |
|---|---|---|---|
| `specs/rastan_direct_remap.json` | JSON | Authoritative input | Declares whole-maincpu policy, `opcode_replace`, optional `shift_replacements`, relocation policy, pointer/jump tables, and expectations. |
| `tools/build_rastan_regions.py` | Python | Build input stage | Reconstructs authoritative arcade regions and writes `build/regions/maincpu.bin`, `build/rom_inventory.json`, and `build/regions/variant.json`. |
| `build/rom_inventory.json` | JSON | Generated fingerprint state | Records the source ROM fingerprints that `build_rastan_regions.py` validates before accepting/reconstructing regions. |
| `build/regions/variant.json` | JSON | Generated variant input | Records the selected arcade variant and reconstructed region metadata. |
| `tools/disasm_maincpu.sh` | Shell | Reference-input producer | Regenerates `build/maincpu.disasm.txt`, the arcade instruction-size/displacement reference consumed by the shift patcher. It is not a normal Makefile release stage. |
| `tools/translation/postpatch_startup_rom.py` | Python | Production transformer | Orchestrates copy/rebase, symbol resolution, shift replacements, byte-neutral replacements, declared relocation/table passes, checksums, and generated mapping/manifest output. |
| `tools/translation/shift_table_patcher.py` | Python | Production transformer | Validates and inserts variable-length replacements, computes accumulated shifts, and repairs the supported branch, absolute-long, and declared jump-table references. |
| `apps/rastan-direct/out/symbol.txt` | Text | Generated input | Produced by `nm`; resolves native helper symbols used by replacement bytes. |
| `build/maincpu.disasm.txt` | Text | Generated reference input | Supplies original 68000 instruction boundaries and operands to the shift patcher. |
| `build/rastan-direct/rastan_direct_patch_manifest.json` | JSON | Generated output | Records patch inputs, replacement/relocation summaries, expected counts, coverage, and build context. |
| `build/rastan-direct/startup_common_relocations.json` | JSON | Generated output | Records generated relocation objects/blocks for the selected arcade variant. |
| `build/rastan-direct/address_map.json` | JSON | Generated authority | Records the resulting `arcade_pc` to `runtime_genesis_pc` segments and accumulated `shift_deltas`. |
| `dist/operand_relocation_report.txt` | Text | Generated output | Reports operand-relocation decisions made by the postpatcher. |
| `tools/translation/verify_rastan_direct_boot_guard.py` | Python | Verifier | Checks the boot, vector, reset, VINT, and entry-point contract before and after postpatching. |
| `tools/translation/verify_canonical_rom.py` | Python | Canonical gate | Validates the postpatched ROM, manifest/address-map coverage, replacement expectations, dependencies, numbering, and release invariants before artifact publication. |
| `build/genesis_postpatch.disasm.txt` | Text | Generated evidence | Makefile-generated disassembly of the final postpatched ROM for static verification. |
| `build/rastan-direct/active_bookmark_baseline.json` | JSON | Conditional generated state | Canonical-gate state used only by the diagnostic bookmark/revert workflow; not a replacement-spec input. |
| `build/rastan-direct/build_counter.txt` | Text | Generated release state | Makefile-owned last numbered build value, validated before publication. |
| `build/rastan-direct/consumed_build_numbers.txt` | Text | Release input/state | Prevents reuse of previously consumed numbered artifacts. |
| `apps/rastan-direct/Makefile` | Build owner | Authoritative workflow | Orders all production stages, runs the guards/gate, owns numbering, and publishes the ROM only after verification. |

Generated maps, manifests, reports, inventories, disassemblies, and counters are outputs. Never
hand-edit them to make a patch appear valid. Historical `startup_title_remap.json` and currently
uninvoked translation scripts are not substitutes for the Makefile-owned production path above.

### Address and Usage Discipline

`build/rastan-direct/address_map.json` is authoritative for every
`arcade_pc` <-> `runtime_genesis_pc` claim. The base whole-maincpu copy currently starts at a
`+0x200` relocation, but insertions can move later code by additional accumulated deltas. Never use
blind `+0x200` arithmetic as proof when the current map can answer the question.

**Do not rediscover this.** Variable-length replacement and shift-table reflow are established
infrastructure. Before reasoning from local byte availability, read this section and inspect the
current spec, postpatcher, shift patcher, address map, and canonical gate. Paid usage must not be
spent redesigning a semantic replacement around an assumed equal-length limit.

---

## Authoritative Analysis Sources, Ghidra-First Workflow, and Target Platform

The **original Rastan arcade ROM/program is the authoritative source of intent**. When determining what a
routine means, what state owns a value, what an object represents, or where a native-replacement boundary
belongs, start from the original arcade program — not from the current Genesis translation, a compatibility
mirror, or one observed runtime trace. If the Genesis build disagrees with the arcade program, the arcade
behavior is the behavior to preserve unless Tighe explicitly decides otherwise.

A complete Ghidra reverse-engineering environment for the arcade program already exists in WSL and MUST be
reused before doing broad runtime tracing:

- Ghidra project: `tools/ghidra/rastan_project/rastan_arcade_ref.gpr`
- Existing exports/decompilation material: `analysis/ghidra/rastan_arcade/exports/`
- Original arcade ROM/disassembly and Ghidra call graph/xrefs/decompilation are the primary tools for static
  provenance, semantic ownership, caller enumeration, and identifying where arcade-chip-specific execution
  begins.

**Do not use MAME tracing as a substitute for static reverse engineering that Ghidra can answer more
completely and cheaply.** A runtime trace proves what happened in the traced execution; by itself it does not
prove every caller, every state, every branch, or the complete meaning of a routine. Prefer this order:

    original arcade ROM + Ghidra decompilation/xrefs/call graph
        -> establish semantic intent and complete static ownership
        -> use original-arcade MAME only for unresolved dynamic facts, timing, state, and visual ground truth
        -> implement the native Genesis realization
        -> use Genesis MAME / BlastEm / hardware to validate the candidate

Use runtime watchpoints/traces when they answer a genuinely dynamic question that static analysis cannot
settle efficiently. Do not start with repeated MAME traces when the decompilation, xrefs, or disassembly can
identify the producer/caller structure directly. If a trace appears to contradict the original arcade code,
investigate the discrepancy rather than treating the single trace as authoritative intent.

Static provenance is not blocked merely because a literal address xref is absent. Stores and ownership may
be computed, register-passed, table-driven, or reached through an indirect call. Continue with decompiler
output, xrefs, call graph, data references, computed-pointer analysis, and register flow before declaring a
writer or semantic owner unresolved. One missed watchpoint or inconvenient debugger technique is likewise
not proof that the provenance is unavailable.

Always state the platform being tested. **Arcade MAME** means the original Rastan arcade ROM and is used for
authoritative runtime behavior. **Genesis MAME** is candidate validation only and is not the source of Rastan
semantic intent.

The project targets the **USA/NTSC Sega Genesis**, not the European PAL Mega Drive. Genesis-driver MAME testing
must therefore use the project's USA/NTSC Genesis machine/configuration (normally `genesis`), not the PAL
`megadriv` machine, unless Tighe explicitly requests a PAL-specific test. A PAL Mega Drive run must never be
used as acceptance evidence for timing, performance, frame behavior, or gameplay of the USA target.

Do not create a duplicate Ghidra project or reinstall/re-import the arcade program unless the existing project
is proven unusable. Reuse the established WSL/Ghidra analysis so paid tool/model usage is spent on new evidence,
not rediscovery.

---

## Established Project Tooling Is Mandatory

Before creating any Lua trace, MAME launcher, debugger script, save-state harness, input driver, Ghidra
import/export script, instrumentation wrapper, or ad-hoc trace workflow, inspect the existing repository
tools and reuse or extend them. The current canonical inventory is:

- `tools/mame/README.md`: entry point for the established MAME layout, output paths, and launch workflows.
- `tools/mame/run_genesis_trace_wsl.sh`: Genesis-target execution tracing through the USA/NTSC `genesis`
  machine by default, using `tools/mame/scripts/genesistrace.lua`.
- `tools/mame/run_rastan_trace_wsl.sh`: full ORIGINAL ARCADE Rastan execution tracing with
  `tools/mame/scripts/rastantrace.lua`.
- `tools/mame/run_rastan_trace_lite_wsl.sh`: lower-overhead ORIGINAL ARCADE tracing for longer
  title/attract runs with `tools/mame/scripts/rastantrace_lite.lua`.
- `tools/mame/run_rastan_jumptrace_wsl.sh`: established ORIGINAL ARCADE jump/control trace using
  `tools/mame/scripts/rastanjumptrace.lua`.
- `tools/mame/run_rastan_wsl.sh`: interactive ORIGINAL ARCADE monitoring/input workflow using
  `tools/mame/scripts/rastanmon.lua`; `run_rastan_wsl_j.sh` currently invokes the same monitor workflow and
  must not be treated as proof of a separate joystick capability.
- `tools/mame/scripts/run_rastan_fu1_playtrace.sh`: durable interactive ORIGINAL ARCADE playtrace/debugger
  workflow with preserved logs/video and the established manual coin/start method.
- `tools/ghidra/rastan_project/rastan_arcade_ref.gpr`: canonical arcade Ghidra project. Reuse its exports in
  `analysis/ghidra/rastan_arcade/exports/`, including the decompiler export, xrefs, call graph, full listing,
  function inventory, hardware references, indirect/jump-table inventory, and subsystem map.
- `tools/ghidra/`: project-owned Ghidra analysis scripts and prior outputs. Check these before writing a new
  import, xref, or export script.
- `tools/translation/`: current remap, shift-table, precomputation, and canonical-verification pipeline. Check
  it before creating alternate patching, mapping, or ROM-inspection tooling.

New tooling is allowed only after the exact missing capability is named, existing tools are shown unable to
provide it, and extending a durable existing tool is considered first. Any genuinely new tool must be
project-owned and reusable, not a chain of disposable `/tmp` scripts, and its necessity must be documented.

### Known Inputs, Controls, and Runtime Workflows

Do not rediscover coin, start, player controls, MAME field names, save-state handling, or established runtime
entry sequences. Search `tools/mame/`, its scripts and README, relevant `states/traces/` captures, and current
design/reference documents first. The durable FU1 playtrace already records manual arcade coin/start as
default keys `5` and `1`; existing Lua captures already use field names such as `Coin 1`, `1 Player Start`,
`P1 Right`, and `P1 Button 1/2`. Reuse the proven method applicable to the requested platform rather than
inventing another input driver.

### Platform Labels and Evidence Roles

- **ORIGINAL ARCADE MAME**: original `rastan` arcade program; authoritative dynamic ground truth.
- **GENESIS NTSC MAME**: USA/NTSC `genesis` target; validates the translated implementation.
- **PAL MEGADRIVE MAME**: `megadriv`; permitted only when Tighe specifically requests PAL testing.

Every MAME claim must use one of these explicit platform labels. PAL Mega Drive output cannot substitute for
USA/NTSC Genesis acceptance evidence.

---

## Efficiency Is a Project Requirement

Efficiency matters. Repeated STOPs, avoidable analysis loops, unnecessary intermediate builds and
tiny partial changes consume paid model/tool usage and **real money** for Tighe. Do not force
another iteration when the requested architectural direction is already clear.

Use analysis to **enable** implementation, not to avoid it. The desired working loop is:

    understand the complete semantic subsystem
        -> trace whatever ownership is necessary
        -> implement the clean native replacement
        -> remove the obsolete legacy tail
        -> validate it
        -> move on

Being "safe" by repeatedly declining the actual work, making tiny partial changes, or forcing
another prompt is **not** efficient and is **not** helpful.

Paid model and tool usage is a project resource. Re-deriving established infrastructure, controls, launch
syntax, static-analysis resources, or working trace methods is a governance failure. Spend usage on new
semantic evidence and implementation, not tooling rediscovery.

---

## Never Delete a Producer Before Replacing Every Live Semantic Consumer

A legacy PC090OJ/PC080SN producer may be retired **only after every live semantic behavior it
supplies has a proven native owner**.

Seeing that one or two screens already have native equivalents does **not** prove that all callers
are superseded. Existing native ownership in one state does not establish ownership in another.

A global `rts`, NOP, dead-write suppression, skipped call, or discarded output is **not** native
replacement — it is deletion of behavior.

Before retiring a shared producer:

- Enumerate **all** live callers and identify the semantic output each caller relies on.
- If callers use different layout/state owners, trace those owners and unify them at the correct
  semantic boundary.
- Do **not** infer an output is unnecessary merely because the currently reachable test harness
  does not display it. "Not observed in the current test window" is not evidence of deadness.
- If a caller cannot be naturally reached, build an **external** validation method (MAME input
  script, state-driving Lua, save state, deterministic setup, watchpoint/provenance trace) rather
  than deleting its output untested. Never add production ROM scaffolding for this.

The required order is always:

    prove semantic ownership -> implement native replacement -> validate consumers -> remove legacy

Never:

    remove producer -> see what breaks -> patch individual screens afterward

Build 0267 violated this: `0x3B802`/`0x5A098` were stubbed to `rts` after proving only the title and
gameplay consumers, and the title-only harness missed that ROUND/READY, the throne/PUSH-BUTTON
screen and the ranking screen still consumed `0x3B802`'s high-score output. That regression cost
paid usage and real money to detect and undo. It must not recur.
