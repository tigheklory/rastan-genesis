# Cody — KF-028 Refinement for Build 0091 Helper Crash Diagnosis

**Date:** 2026-06-19
**Type:** Documentation/canonicalization only
**Build context:** Build 0091 / OPEN-016 Part 2 ROM, SHA `942dcb1aefebec7cbd808d016ff41f4bc22ec9ffd92c98be8a423297a56590cc`
**Scope:** Refine `KNOWN_FINDINGS.md` KF-028 from Andy's static triage. No source/spec/tool/Makefile/ROM modifications. No build. No bookmark cycle. No runtime probing. No implementation.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-028 (input-shim/title-text U3 arc), KF-013 (text dispatch inside VBlank), KF-010 (FG maps to Plane A), KF-004 (runtime PC = ROM file offset), and KF-006 (identity offset `0x200`). HIGH-hazard prior touched: KF-028. No deferred appendix entries were directly relevant.

Open issues touched as context only: OPEN-016, OPEN-015, OPEN-001. No issue closure or issue edit was performed.

Contradiction detected: **NO**. STOP not triggered.

## Source Verification

Primary source: `docs/design/Andy_build_0091_helper_crash_triage.md`.

The triage records a Build 0091 ADDRESS ERROR write from the WRAM crash record:

- Faulting instruction: `runtime_genesis_pc 0x00070794`, `move.w %d1,(0,%a6,%d2.w)`
- IR: `0x3D81`, matching the patched disassembly at `0x00070794`
- Extension word: `0x2000`
- Stacked PC: `0x00070796`, the extension word per m68k group-0 imprecise-PC convention
- Stacked SR: `0x2700`
- SSW: `0x000D` (write, supervisor data)
- Fault address: `0x00000F41` (odd)

The helper write computes `%a6 + %d2.w`; `%a6` must be `staged_fg_buffer` at WRAM `0x00FF501A`. The low odd fault address proves `%a6` was not preloaded with that staging base.

## Classification

Andy classifies the crash as **A — Hook behavior bug**.

`genesistan_hook_glyph_renderer_3bd48.Lgr_store_cell` calls the shared FG-staging helper `.Ltw_store_from_components_at_a2` at `runtime_genesis_pc 0x000707BC` without loading the helper's required base registers:

- `%a3 = genesistan_pc080sn_tile_vram_lut`
- `%a5 = genesistan_pc080sn_attr_lut`
- `%a6 = staged_fg_buffer`

Existing text-writer hooks such as `genesistan_hook_text_writer_3c550` (`tilemap_hooks.s:1090`) and `genesistan_hook_text_writer_3c586` (`tilemap_hooks.s:1122`) perform those three `lea` instructions before calling the shared helper. The shared helper is therefore not the fault locus; the glyph hook omitted the precondition setup.

Not C: the helper is structurally compatible. Not B: the fault is caused by a bad base register, not bad staged data. Not D: the mechanism is statically resolved.

## KF-028 Edit Applied

`KNOWN_FINDINGS.md` KF-028 was refined per Option C:

- Metadata updated to include Build 0091 / OPEN-016 Part 2 context.
- Source Documents now include `docs/design/Andy_build_0091_helper_crash_triage.md`.
- Last verified updated to `2026-06-19 (Build 0091 / OPEN-016 Part 2 ROM)`.
- Finding paragraph records the observable Build 0091 crash values and faulting instruction.
- Use-as-prior records the mechanism, classification A, and fix locus: add the missing register setup in the glyph hook, not in the shared store helper.

## Non-Actions

No implementation was performed. No source, spec, tool, Makefile, ROM, build artifact, bookmark artifact, or runtime evidence was modified. No `KNOWN_FINDINGS.md` rulebook changes were made. No issue was opened, edited, or closed.

## Open / Closed Issues Impact

- Open issues touched: OPEN-016 (context), OPEN-015 (context), OPEN-001 (context)
- Closed issues touched: NONE
- New issues opened: NONE
- Issues closed: NONE
- Issues intentionally deferred: Start-C-A crash, broader unhooked-writer survey, broader embedded data-pointer-table survey, OPEN-015 fix

## KNOWN_FINDINGS Impact

Option C — KF-028 refined with the Build 0091 crash diagnosis. Rationale: the mechanism is statically proven from Andy's triage and should be canonical before the implementation fix proceeds.

## STOP

STOP triggered: NO.
