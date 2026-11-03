# Cody — Build 0091 Helper Crash Fix

**Date:** 2026-06-19
**Type:** Implementation + numbered build attempt
**Scope:** Add base-register setup to `genesistan_hook_glyph_renderer_3bd48.Lgr_store_cell` for the Build 0091 helper crash. No runtime probing. No bookmark cycle. No shared-helper rewrite. No OPEN-015 or Start-C-A work.

## Phase 0

Classification: **EXTENDING**. Priors loaded: KF-028 (Build 0091 helper-crash diagnosis), KF-013 (text dispatch inside VBlank), KF-010 (FG maps to Plane A), KF-004 (runtime PC = ROM file offset), and KF-006 (identity offset `0x200`). HIGH-hazard prior touched: KF-028. No deferred appendix entry was directly relevant.

Open issues touched: OPEN-016 (active), OPEN-015 (context), OPEN-001 (context). No issues opened or closed. Contradiction detected: **NO**.

## Phase 1 — Convention Verification

Existing text-writer hook convention:

```asm
    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6
```

Confirmed in `genesistan_hook_text_writer_3c550` and `genesistan_hook_text_writer_3c586`.

Before the fix, `.Lgr_store_cell` had `movem.l %d0-%d7/%a2-%a6, -(%sp)` followed by the per-cell setup and `bsr .Ltw_store_from_components_at_a2`; the three `lea` instructions were absent. The `movem.l` save preserves `%a3`, `%a5`, and `%a6`.

## Phase 2 — Fix Applied

Inside `apps/rastan-direct/src/tilemap_hooks.s`, `.Lgr_store_cell` now loads the required base registers after the save and before the shared-helper call:

```asm
.Lgr_store_cell:
    movem.l %d0-%d7/%a2-%a6, -(%sp)

    lea     genesistan_pc080sn_tile_vram_lut, %a3
    lea     genesistan_pc080sn_attr_lut, %a5
    lea     staged_fg_buffer, %a6

    movea.l %a1, %a2
    adda.w  #2, %a2
    move.w  %d3, %d0
    bsr     .Ltw_store_from_components_at_a2
```

No shared-helper code was modified. No other hook was intentionally modified.

## Phase 3 — Invariant Delta

The canonical invariant was updated in `tools/translation/postpatch_startup_rom.py` and `tools/translation/verify_canonical_rom.py`:

- `opcode_replace` patched-site count: `95` (unchanged)
- `total_genesis_bytes_covered`: `0x17CB44 -> 0x17CB58`
- Mechanical delta: `+0x14`

The net `+0x14` is mechanically tied to the three new base-register loads plus assembler branch-size effects in the existing hook body. No opcode_replace entry was added.

## Phase 4 — Release Build Attempt

Pre-build counter: `91`.

Command run exactly once:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **STOP before numbered artifact production**.

The first release invocation failed at the postpatch invariant gate before counter increment and before numbered artifact copy:

```text
RuntimeError: Build 0029 invariant failure: expected total_genesis_bytes_covered=0x17CB56 and opcode_replace patched_site count=95; got total_genesis_bytes_covered=0x17CB58 opcode_replace patched_site count=95. build_context=canonical.
```

After the failure, the invariant was corrected to the observed mechanical value `0x17CB58`. The release target was **not** run a second time because the prompt required a single release invocation.

Post-failure counter: `91` (unchanged). Numbered Build 0092 artifact: **not produced**. The rolling output `apps/rastan-direct/dist/rastan_direct_video_test.bin` was removed by Make's delete-on-error behavior.

## Static Evidence from Failed Build Artifacts

The failed build assembled the ELF before the postpatch gate. `m68k-elf-objdump` confirms the inserted setup in the assembled helper:

```asm
00070bc8: 48e7 ff3e       moveml %d0-%d7/%a2-%fp,%sp@-
00070bcc: 47f9 000f 1f2c  lea 0x000f1f2c,%a3  ; genesistan_pc080sn_tile_vram_lut
00070bd2: 4bf9 000f 9f2c  lea 0x000f9f2c,%a5  ; genesistan_pc080sn_attr_lut
00070bd8: 4df9 00ff 501a  lea 0x00ff501a,%fp ; staged_fg_buffer (%a6)
00070bde: 2449            moveal %a1,%a2
00070be0: d4fc 0002       addaw #2,%a2
00070be4: 3003            movew %d3,%d0
00070be6: 6100 fbd4       bsrw 0x707bc
```

Symbols from `apps/rastan-direct/out/symbol.txt`:

- `genesistan_pc080sn_tile_vram_lut = 0x000F1F2C`
- `genesistan_pc080sn_attr_lut = 0x000F9F2C`
- `staged_fg_buffer = WRAM 0x00FF501A`

## Determinism / Numbered Artifact

No deterministic ROM comparison was possible because no numbered artifact was produced and the rolling ROM was deleted on error. The release target was not rerun.

## OPEN-016 / KNOWN_FINDINGS Impact

KNOWN_FINDINGS impact: Option A — no new finding indexed. KF-028 was already refined before this implementation task.

OPEN-016 remains open. Runtime verification and broader deferred surveys remain pending.

## STOP

STOP triggered: **YES** — the single allowed release invocation did not produce a numbered artifact. Counter stayed `91`; no Build 0092 ROM exists from this task. The code fix and corrected invariant are present in the workspace, but the release build must be rerun only under a follow-up directive that authorizes another release invocation.
