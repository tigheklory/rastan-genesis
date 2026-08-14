# AGENTS.md

This file is the working guide for coding agents in this repository.

## Mission

Port arcade-accurate `Rastan` behavior to Sega Genesis while preserving original
assets and as much original game logic as possible.

Current development preference:

- avoid one-off crash-site hacks
- keep rules declarative in `specs/`
- favor build-time translation/remap over runtime patch tricks

## Repo map (current)

- `apps/rastan-direct/`: **current** project — assembly opcode-replacement port.
  - `apps/rastan-direct/src/*.s`: current production source.
  - `apps/rastan-direct/Makefile`: owns the build, canonical gate, sequential
    numbering/counter, and the mandatory MAME trace.
- `tools/translation/`: patchers and translation tooling (`postpatch_startup_rom.py`,
  `verify_canonical_rom.py`, LUT/preload generators).
- `specs/rastan_direct_remap.json`: source-of-truth remap/opcode_replace rules.
- `build/rastan-direct/address_map.json`: generated arcade↔Genesis address correlation.
- `build/`: disposable generated files and manifests; `dist/`: released numbered ROMs.
- `docs/design/`: design/analysis reports and the canonical policies.
- `docs/reverse-engineering/`, `docs/reference/`, `analysis/ghidra/`: RE notes + arcade
  disassembly exports; `attic/`, `apps/rastan/`: **retired SGDK era** (history only).

## Build and run (current)

Load the local toolchain first, then run the normal Makefile (default goal builds the ROM,
runs the canonical gate, auto-numbers via the counter + consumed-ledger, and runs the ~30s
MAME trace):

```bash
source tools/setup_env.sh
make -C apps/rastan-direct        # or `make` when already inside apps/rastan-direct/
```

(The default goal builds the ROM, runs the canonical gate, auto-numbers the artifact, and
runs the MAME trace. Build variants and feature flags — e.g. `release`,
`RASTAN_GAMEPLAY_HUD_SPRITES=0` — are **task-specific** and belong only in the prompt that
needs them, not in the universal command.)

- rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- numbered artifact (Makefile-owned name/number — never rename/reuse):
  `dist/rastan-direct/rastan_direct_video_test_build_NNNN.bin`
- Report the artifact exactly as generated (path, SHA-256, size, counter).

## Current architecture status

- Current accepted forward baseline as of this documentation update: **Build 0273**.
  This is an as-of marker, not a permanent baseline declaration. Before beginning any task,
  determine the latest accepted Genesis baseline from current project evidence and task context.
- Current immediate work as of this update is PC090OJ player-sprite semantic provenance and
  native replacement, including `a5+0x11B2` BODY and `a5+0x0170` probable FRONT/weapon.
  Agents must still resolve the current task and baseline from current evidence rather than
  treating this snapshot as permanent scope.
- Graphics work is governed by
  `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` (+ `RULES.md` §11):
  cut at the arcade **semantic** boundary and produce final Genesis VDP/SAT output directly.

## Critical engineering constraints

1. Prefer holistic remap changes over incremental trampoline stepping.
2. Keep manifests as outputs, specs as inputs.
3. Preserve original `maincpu` behavior as much as possible; remap hardware
   contracts rather than rewriting gameplay logic.
4. Minimize shadow/backing RAM usage to only what the translated hardware
   contract needs.
5. Treat normal `START RASTAN` handoff as one-way target architecture.

## Long-term rendering architecture

> **CANONICAL POLICY (read first):**
> `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` and `RULES.md` §11 govern all
> PC080SN/PC090OJ work. The final architecture is `arcade semantic decision → native
> Genesis VDP/SAT realization` — cut **above** chip-specific execution. No software
> PC080SN/PC090OJ device, virtual chip RAM, C-window/name-RAM shadow, object-RAM mirror,
> generic chip-address translation, or full-map/tall-buffer projection is the final design.
> Any "shadow"/"projection" mentioned below is **transitional compatibility only** (isolated,
> labeled, scheduled for removal) — never the accepted target. Before proposing/implementing
> PC080SN/PC090OJ work, agents must state the semantic cut and the chip tail being removed.
> (Note: some file paths in older subsections below, e.g. `apps/rastan/src/*`, are the
> RETIRED SGDK/C era; the current project is `apps/rastan-direct/` — historical reference
> only.)

The **delivery mechanism** is **direct opcode replacement with shift-table reflow** (no
trampolines, no runtime interception; the final ROM is Genesis-native code). This mechanism
remains current and valid.

The **rendering strategy** is **NOT** replacing each individual arcade hardware-register
write one-for-one. It is: cut at the **highest safe arcade semantic producer boundary** and
have the native helper produce **final Genesis Plane A/B name words or SAT entries directly**
from the retained arcade semantic state — per
`docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` (+ `RULES.md` §11). Per-write and
per-cell mapping tables below are **reference for where hardware surfaces live**, not a
mandate to replace at the individual-write level.

### What this means

The Python patching pipeline reads the original arcade ROM files directly and, at the chosen
**semantic producer boundary**, replaces the original 68000 instruction bytes with a
Genesis-native sequence inline (the complete PC080SN/PC090OJ chip tail below the boundary is
retired, not translated write-by-write).

When a replacement sequence is longer than the original
instruction, the patcher inserts the extra bytes at that
location. All subsequent code shifts forward. The patcher
maintains a shift table — a sorted list of insertion
points and sizes — and applies accumulated offsets to the
supported reference classes documented below.

No trampolines. No NOP padding. No runtime interception.
The final ROM contains only Genesis-native code.

### Shift table reference types

The current reflow engine fixes:
- Absolute-long operands: JSR, JMP, LEA, MOVEA.L, and PEA forms recognized by
  `shift_table_patcher.py`.
- Relative control flow: 8-bit and 16-bit BRA, BSR, and Bcc displacements. If a short branch no
  longer fits, it must be promoted deliberately; the patcher does not silently widen it.
- Tables: explicitly declared 16-bit jump/displacement tables. Automatic jump-table discovery is
  not implemented.

`postpatch_startup_rom.py` separately applies accumulated shift deltas to declared
`absolute_long_pointer_tables`, deferred shifted operands, and later replacement/relocation
passes. A reference class not listed here must be checked against the current implementation and
declared or supported explicitly; do not assume either support or impossibility.

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

Entries live in top-level arrays in `specs/rastan_direct_remap.json` (the old
`specs/startup_title_remap.json` name is retired SGDK-era):

```json
{
  "arcade_pc": "0x03XXXX",
  "original_bytes": "<hex, validated before patching>",
  "replacement_bytes": "<Genesis instruction sequence>",
  "note": "human-readable provenance"
}
```

Use `opcode_replace` for intentionally equal-length replacements. Use `shift_replacements` when
the replacement changes size and requires downstream reflow. Original-byte mismatch aborts the
build. The absence of live `shift_replacements` at a particular baseline is inventory state, not
removal of the variable-length architecture.

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

## Files to check before touching the remap (current)

- `specs/rastan_direct_remap.json` — current opcode_replace / remap spec
- `build/rastan-direct/address_map.json` — generated arcade↔Genesis address map
- `tools/translation/postpatch_startup_rom.py`, `tools/translation/verify_canonical_rom.py`
- `apps/rastan-direct/src/*.s` — current production source
- `apps/rastan-direct/Makefile` — build/gate/counter owner
- `RULES.md`, `ARCHITECTURE.md`,
  `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`

## Canonical Opcode-Replacement / Shift-Reflow Workflow

**There is no general equal-length replacement constraint.** The semantic cut determines the
scope; local byte availability does not. A larger replacement uses `shift_replacements` rather
than forcing a byte-neutral rewrite, wider semantic cut, trampoline, NOP padding, or duplicate
game logic.

Follow this current production sequence:

1. Prove the highest safe arcade semantic cut and the complete chip-specific tail being retired.
2. Verify original instructions against `build/regions/maincpu.bin`, the canonical Ghidra
   project, and `build/maincpu.disasm.txt` as applicable.
3. Update the authoritative `specs/rastan_direct_remap.json`: use `opcode_replace` only for an
   intentionally equal-length change, or `shift_replacements` for a size-changing replacement.
4. Add or update the native helper in `apps/rastan-direct/src/*.s`; replacement bytes may resolve
   helper addresses through the Makefile-generated `apps/rastan-direct/out/symbol.txt`.
5. Run the Makefile-owned pipeline. `tools/build_rastan_regions.py` reconstructs the arcade
   regions; `postpatch_startup_rom.py` orchestrates copy/rebase and all replacement/relocation
   passes; it invokes `shift_table_patcher.py` for inserted-byte reflow.
6. Let the tools regenerate `build/rastan-direct/rastan_direct_patch_manifest.json`,
   `build/rastan-direct/startup_common_relocations.json`,
   `build/rastan-direct/address_map.json`, `dist/operand_relocation_report.txt`, and
   `build/genesis_postpatch.disasm.txt`. Never hand-edit these outputs.
7. Treat `build/rastan-direct/address_map.json` as the authority for every postpatch
   `arcade_pc`/`runtime_genesis_pc` relationship. A base `+0x200` copy delta is not proof after
   inserted-byte shifts.
8. Require both `verify_rastan_direct_boot_guard.py` checks and
   `verify_canonical_rom.py`/`GATE_PASS` before the Makefile publishes a numbered ROM.

### Pipeline Files and Responsibilities

| File | Input / generated | Responsibility |
|---|---|---|
| `apps/rastan-direct/Makefile` | Workflow owner | Links helpers, emits symbols/prepatch ROM, invokes region build/postpatch/guards/gate, then owns numbering and publication. |
| `specs/rastan_direct_remap.json` | Authoritative input | Whole-maincpu policy, replacements, relocation policy, declared tables, and canonical expectations. |
| `tools/build_rastan_regions.py` | Input preparation | Generates `build/regions/maincpu.bin`, `build/rom_inventory.json`, and `build/regions/variant.json` from authoritative arcade ROM inputs. |
| `build/rom_inventory.json` | Generated fingerprint state | Source ROM fingerprints validated by `build_rastan_regions.py` before region reconstruction. |
| `build/regions/variant.json` | Generated variant input | Selected arcade variant and reconstructed-region metadata. |
| `tools/disasm_maincpu.sh` | Reference producer | Regenerates `build/maincpu.disasm.txt` for original instruction boundaries; it is run when that reference needs refresh, not by the normal release target. |
| `tools/translation/postpatch_startup_rom.py` | Transformer | Resolves symbols, copies/rebases maincpu code, applies shift and byte-neutral replacements plus declared relocation/table passes, and emits maps/manifests/checksum. |
| `tools/translation/shift_table_patcher.py` | Reflow engine | Inserts variable-length replacements, computes accumulated shifts, and repairs supported branch, absolute-long, and declared jump-table references. |
| `tools/translation/verify_rastan_direct_boot_guard.py` | Guard | Verifies boot/vector/reset/VINT/entry contracts before and after postpatching. |
| `tools/translation/verify_canonical_rom.py` | Canonical gate | Verifies the final ROM, manifest/address-map coverage, replacement expectations, dependencies, numbering, and release invariants. |
| `apps/rastan-direct/out/symbol.txt` | Generated input | Resolves native helper symbols referenced by replacement bytes. |
| `build/maincpu.disasm.txt` | Generated reference input | Supplies original instruction boundaries and operands to the reflow engine. |
| `build/rastan-direct/rastan_direct_patch_manifest.json` | Generated output | Patch-input, replacement, relocation, count, coverage, and build-context record. |
| `build/rastan-direct/startup_common_relocations.json` | Generated output | Generated relocation object/block record for the selected variant. |
| `build/rastan-direct/address_map.json` | Generated authority | Final mapping segments and `shift_deltas`; sole authority for current arcade/runtime PC correlation. |
| `dist/operand_relocation_report.txt` | Generated output | Operand-relocation decisions from the postpatcher. |
| `build/genesis_postpatch.disasm.txt` | Generated evidence | Disassembly of the final postpatched Genesis ROM. |
| `build/rastan-direct/active_bookmark_baseline.json` | Conditional generated state | Canonical-gate state for the diagnostic bookmark/revert workflow only. |
| `build/rastan-direct/build_counter.txt` | Generated release state | Makefile-owned last numbered build value, validated before publication. |
| `build/rastan-direct/consumed_build_numbers.txt` | Release input/state | Prevents reuse of consumed numbered artifacts. |

Graphics precomputation scripts that feed tile/palette assets are build inputs, but they do not
perform opcode reflow. Historical specs and translation scripts not invoked by the current
Makefile are not production pipeline authority.

**Do not rediscover this.** Variable-length opcode replacement and shift-table reflow are
established infrastructure. Before saying "no room", "will not fit", "must be byte-neutral", or
"a BSR/JSR is too large", inspect the current spec and tools. A true blocker must prove the exact
unsupported site/reference class from the current implementation. Paid usage must not be spent
redesigning around an assumed equal-length limit.

## MAME and reverse-engineering references

- Rastan MAME driver: `src/mame/taito/rastan.cpp` (external reference)
- Local disassembly: `build/maincpu.disasm.txt`
- 68000 reference manual:
  - `docs/reference/hardware/motorola_68000_reference_manual.pdf`

## Mandatory Analysis and Tool-Reuse Workflow

Andy, Cody, and every other agent are bound by the same evidence workflow:

1. Read `RULES.md` fully and inspect the latest relevant project evidence.
2. For original arcade meaning or provenance, begin with the canonical Ghidra project
   `tools/ghidra/rastan_project/rastan_arcade_ref.gpr` and the exports under
   `analysis/ghidra/rastan_arcade/exports/`.
3. Inspect `tools/mame/`, `tools/ghidra/`, and `tools/translation/` before creating any new
   trace, debugger, input, save-state, import/export, instrumentation, or patching workflow.
4. Use ORIGINAL ARCADE MAME to establish dynamic arcade ground truth and GENESIS NTSC MAME
   to validate the translation. Do not substitute PAL `megadriv` for the USA/NTSC target.
5. Reuse established coin/start/player controls, MAME field names, save-state methods, and
   launch wrappers from repository tools and prior durable evidence.
6. Spend paid usage on new semantic evidence and implementation, not infrastructure
   rediscovery or chains of disposable probes.

Static arcade provenance must follow computed pointers, register-passed stores, indirect calls,
data references, and call graph flow. Missing literal xrefs or a failed watchpoint do not make
provenance blocked while those established resources remain unchecked.

### Flexible Shared Capability and Preferred Strengths

Roles describe strengths and normal preferences, not exclusive authority. Tighe may assign
architecture, planning, reverse engineering, Ghidra/static provenance, semantic analysis,
implementation, assembly/source patching, remap/spec changes, builds, MAME tracing, runtime
validation, design/report writing, code review, or regression investigation to either Andy or
Cody. The assigned agent must perform the complete requested task when capable and must not
refuse, defer, or split it merely because the other agent is described as stronger in part of
the work.

Tighe chooses the assigned agent according to available usage, current context, relevant
expertise, continuity, and project efficiency.

**Andy is particularly strong in:** architecture and holistic subsystem design;
semantic/contract reasoning; native-system design; cross-subsystem review; implementation
planning; and validating whether a proposed cut represents arcade intent. When assigned, Andy
may also perform Ghidra/static analysis, source implementation, assembly patching, builds, MAME
tracing, runtime verification, and documentation.

**Cody is particularly strong in:** Ghidra/static provenance; call/data-flow proof; source
patching; assembly implementation; build/gate work; address-map proof; MAME tracing; and concrete
runtime verification. When assigned, Cody may also perform architecture, planning,
semantic/contract analysis, subsystem design, review, and documentation.

Both agents remain identically bound by all of `RULES.md`, arcade-authoritative intent,
Ghidra-first static provenance, established-tool-first workflow, existing MAME/input harness
reuse, USA/NTSC Genesis validation, explicit ORIGINAL ARCADE versus GENESIS NTSC evidence,
no disposable trace sprawl, semantic-boundary native replacement, consumer-coverage proof,
numbered-ROM preservation, standalone report requirements, and paid-usage efficiency.

### Agent Handoff Reuse

When an agent has already established tooling, provenance, addresses, address-map correlations,
input field names, save-state steps, or a working trace method, the next agent must reuse and
cite that work. Rediscovering the same infrastructure is prohibited unless current evidence
proves it stale or incorrect; in that case, document the contradiction before replacing it.

When Tighe transfers a task from Andy to Cody or Cody to Andy because of usage availability,
the receiving agent must continue from the existing evidence. Before continuing, inspect the
current source, standalone report or handoff, existing Ghidra findings, established addresses
and mappings, existing trace results, existing MAME/input methodology, and current task
conclusions. Do not restart the investigation merely because another agent produced that
evidence, and do not require a new analysis phase when the established evidence already proves
the facts needed for the remaining work. If prior evidence appears wrong, stale, or
contradictory, identify the concrete contradiction before spending usage recreating it.

### No Mandatory Cross-Agent Pipeline

Unless Tighe explicitly requests divided work, do not impose an Andy-analysis-to-Cody-build or
Cody-trace-to-Andy-design pipeline. The assigned agent should reuse existing evidence, perform
whatever remaining analysis is necessary, and complete the assigned task. Analysis-only scope
must be honored when Tighe requests it; otherwise, an implementation task must not become a
handoff merely because it includes architecture, provenance, tracing, documentation, or review.

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

1. Confirm the semantic cut + chip tail per `PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`
   (for graphics work) and update the relevant design doc.
2. Update spec rules in `specs/rastan_direct_remap.json`; select byte-neutral `opcode_replace`
   or size-changing `shift_replacements` according to the replacement, never according to an
   assumed byte-fit architecture.
3. Update patcher/tooling (`tools/translation/`) and/or `apps/rastan-direct/src/*.s`.
4. Build with `source tools/setup_env.sh && make -C apps/rastan-direct` (add task-specific variants/flags only when the prompt requires them).
5. Validate generated manifests/address map under `build/rastan-direct/` and the canonical gate.
6. Compare against ORIGINAL ARCADE ground truth and the CURRENT ACCEPTED GENESIS BASELINE
   established by current project evidence, using the auto-generated trace where applicable.


## Retired / historical (SGDK/C era) — history only, NOT current guidance

The following are **retired** and must not be treated as current operational guidance. They
are kept only as provenance for reading old reports. The current project is the
`apps/rastan-direct/` assembly era (see "Repo map (current)" and "Build and run (current)").

- `apps/rastan/` (SGDK launcher app), `apps/rastan/src/main.c`,
  `apps/rastan/src/startup_bridge.c`, `apps/rastan/src/startup_trampoline.s` — SGDK/C era.
- Old build commands `make -C apps/rastan release[-nohook]/debug`; output `apps/rastan/out/rom.bin`.
- Old artifact naming `dist/Rastan_<n>_<timestamp>.bin` / `Rastan_NNN.bin` — retired;
  the Makefile now owns numbering as `rastan_direct_video_test_build_NNNN.bin`.
- Old spec name `specs/startup_title_remap.json` → current `specs/rastan_direct_remap.json`.
- Old `docs/project/startup_title_remap_plan.md` / `decision_log.md` — historical.
- Old "56/57/59-style" front-end bring-up notes — superseded; resolve the current accepted
  baseline from current project evidence rather than from these historical notes.
- "C-Window / name-RAM shadow", "genesistan_shadow_d00000_words", and tall-buffer projection
  framed as an intermediate step: these are **transitional compatibility only** and are being
  retired per `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` — never the final
  architecture. (Work-RAM/input/sound-mailbox shadows are not chip emulation and remain.)

## Team Structure (current)

### Tighe (Human Supervisor)
Project **owner and final authority**. Sets scope and architecture decisions, commits and
pushes, and tests builds on hardware/emulator. No AI agent has authority above Tighe,
`RULES.md`, or `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`.

### Andy
Particularly strong in architecture, holistic subsystem design, semantic/contract reasoning,
native-system design, cross-subsystem review, implementation planning, and arcade-intent cut
validation. These are preferred strengths, not exclusive permissions. When assigned by Tighe,
Andy may also perform static analysis, implementation, assembly/source patching, builds, MAME
tracing, runtime validation, documentation, and the complete task workflow.

### Cody
Particularly strong in Ghidra/static provenance, call/data-flow proof, source and assembly
implementation, build/gate work, address-map proof, MAME tracing, and concrete runtime
verification. These are preferred strengths, not exclusive permissions. When assigned by
Tighe, Cody may also perform architecture, planning, semantic/contract analysis, subsystem
design, review, documentation, and the complete task workflow.

## Authority Structure (current)

- **Final authority:** Tighe (then `RULES.md` and the canonical policy — no AI agent overrides them).
- Tighe assigns work to Andy or Cody according to need, available usage, context, continuity,
  expertise, and project efficiency.
- Andy and Cody have overlapping capabilities with different preferred strengths. Neither agent
  has exclusive ownership of planning, analysis, architecture, implementation, builds, tracing,
  review, documentation, or validation.
- Any conflict or ambiguity escalates to **Tighe**; agents do not resolve authority conflicts independently.

## Retired team/authority structure (historical — NOT current)

Superseded by the current structure above; kept only as provenance for old reports:

- "Claude (Technical Lead)" owning technical decisions and issuing directives — retired.
- "Andy = primary implementer" / "Cody = secondary implementer" — retired; current roles are
  overlapping and assignment-driven, with different preferred strengths but no exclusive work class.
- "Chad (ChatGPT) — high-level management authority / reviews directives" — retired (no AI
  management authority; final authority is Tighe).
- "Alan / Gemini specialist consultants" — retired as a standing structure.

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

### Canonical palette-decision registry

`specs/palette_decisions.json` is the **only** palette-decision registry. Every palette task
must consult it before analysis or implementation and must preserve each decision's scene and
stage context. Reports and changes must identify every affected Palette Decision ID, inspect all
listed runtime/build consumers before changing a decision, and update the JSON in the same task
as any palette-decision change. Do not maintain a duplicate palette mapping registry in Markdown,
source comments, another spec, or generated output; other documents may cite decision IDs and
evidence but must not become a competing mapping authority.

Registry statuses are exactly `proven`, `decided`, `provisional`, and `unknown`. Do not use
`confirmed` or introduce another palette-status vocabulary.

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

## Project Rule Update — Title/Attract Visual Proof Gate

For graphics bring-up tasks, title/attract success proof is valid ONLY when:
- real game title/attract text is visible before exception handling
- output is from game-executed render path, not launcher/config UI
- output is not exception handler text
- output is not SGDK/debug helper text

Invalid proof examples (must be rejected):
- launcher/startup/config menu text
- exception dump/register text
- SGDK/debug overlay/helper text

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
  * `RULES.md` in full
  * latest relevant section of `AGENTS_LOG.md`

* Treat `AGENTS_LOG.md` as the **source of current truth**

* NEVER:

  * rely on summaries
  * assume previous fixes were correct
  * reuse old approaches without verification

* ALWAYS:

  * cite the build / log section being continued
  * verify assumptions against current state
  * inspect established repository tools before creating a new harness
  * distinguish ORIGINAL ARCADE ground truth from GENESIS NTSC validation
  * reuse prior agent tooling, provenance, mappings, controls, and trace methods
  * treat paid usage efficiency as a project requirement
