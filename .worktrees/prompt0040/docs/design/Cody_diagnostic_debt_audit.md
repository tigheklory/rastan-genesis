# Cody Diagnostic Debt Audit

## 1. Executive Summary
This audit inventories temporary, proof-only, suppression-based, instrumentation-based, and potentially contaminating changes using current source state and documented history (`AGENTS_LOG.md` + build design documents).

Active temporary/diagnostic items still present: 17.
Historical temporary/diagnostic items documented but not active in current runtime path: 4.
High-risk active contaminants: 11.

## 2. Active Temporary / Diagnostic Changes Still Present

| Item | Category | Exact file | Exact function / symbol / location | Exact current behavior | Why it was added | Meant to be temporary | Still present now | Changes runtime behavior | Changes visible output | Can contaminate debugging conclusions |
|---|---|---|---|---|---|---|---|---|---|---|
| A01 | `TEMPORARY_SENTINEL_TEST` | `apps/rastan/src/boot/sega.s` | `_VINT_arcade_mode` lines with `move.w #0xFFFF, pc080sn_fg_buffer`, `fg_debug_before`, `fg_debug_after` captures | Writes FG buffer cell 0 to `0xFFFF` every frame before tick and records before/after values | Build 325/326 sentinel proof of FG-buffer survival through tick | YES | YES | YES | YES | YES |
| A02 | `INSTRUMENTATION` | `apps/rastan/src/startup_trampoline.s` | `genesistan_bulk_tilemap_commit`, instruction `move.l %a0, bulk_debug_pre_read_a0` before `move.w (%a0)+,%d4` | Stores live A0 pointer before bulk dereference on each row-loop iteration | Build 328 proof for `C7121A` bad-read source | YES | YES | YES | YES (via overlay line `P:`) | YES |
| A03 | `DEBUG_OVERLAY` | `apps/rastan/src/main.c` + `apps/rastan/src/boot/sega.s` | `genesistan_debug_fg_proof()` and `_VINT_arcade_mode` call site | Renders `B:`, `A:`, `P:`, `M:`, `I:`, `K:` telemetry into FG buffer each frame | Build 326/328/330 runtime proof telemetry | YES | YES | YES | YES | YES |
| A04 | `INSTRUMENTATION` | `apps/rastan/src/boot/sega.s` + `apps/rastan/src/startup_trampoline.s` + `apps/rastan/src/main.c` | `_VINT_arcade_mode` frame-history roll/reset + counters `vdp_commit_*` | Tracks per-frame commit counts and last-3-frame history continuously | Build 336 commit-frequency census | YES | YES | YES | NO | YES |
| A05 | `TEMPORARY_SUPPRESSION` | `apps/rastan/src/main.c` | `genesistan_bulk_preload_check()` immediate `return` | Tick-phase scene preload path is disabled; no preload call on range miss | Build 335 proof to remove non-VBlank DMA writer | YES | YES | YES | YES (tile visibility/content timing) | YES |
| A06 | `TEMPORARY_PALETTE_TEST` | `apps/rastan/src/main.c` | `apply_post_reset_test_palette()` and call in `request_start_rastan()` after `force_clean_vram_init()` | Writes fixed 64-entry test palette to CRAM immediately after reset/handoff | Build 331 proof for early-black period causality | YES | YES | YES | YES | YES |
| A07 | `TEMPORARY_SPRITE_TEST` | `apps/rastan/src/main.c` | `genesistan_render_sprites_vdp()`, commented-out `VDP_updateSprites(sprite_count, DMA)` and `VDP_waitDMACompletion()` | Sprite enumeration/shadow build runs, but SAT DMA publish from C path is suppressed | Build 339 proof isolation of SAT DMA side effect | YES | YES | YES | YES | YES |
| A08 | `TEMPORARY_EARLY_RETURN` | `apps/rastan/src/startup_trampoline.s` | `genesistan_render_sprites_vdp_asm` first instruction `rts` | Entire assembly sprite renderer exits immediately; body unreachable | Build 329 Plane-A-only proof suppression | YES | YES | YES | YES | YES |
| A09 | `TEMPORARY_PALETTE_TEST` | `apps/rastan/src/startup_trampoline.s` | `genesistan_palette_commit_asm` header comment and implementation | Uses temporary mirrored-block palette conversion strategy and writes mirrored CRAM lines | Build 320 visibility proof palette path | YES | YES | YES | YES | YES |
| A10 | `OTHER_TEMPORARY_OR_CONTAMINATING_CHANGE` | `apps/rastan/src/main.c` | `text_writer_ptr_to_xy()` block with commented-out row visibility check (`TEMP DEBUG`) | Row-bias visibility filter remains disabled | Added as temporary debug for empty-plane diagnosis | YES | YES | YES | YES | YES |
| A11 | `OTHER_TEMPORARY_OR_CONTAMINATING_CHANGE` | `apps/rastan/src/main.c` | `sanitize_arcade_workram()` | Scans work RAM and zeros values in `0xC00000-0xC0FFFF` range after each tick | Stability bridge until full opcode replacement coverage | YES | YES | YES | YES | YES |
| A12 | `PATCH_OR_REMAP_FOR_DIAGNOSIS` | `specs/startup_title_remap.json` | `opcode_replace` entries at `0x000514`, `0x000518`, `0x00052A` | NOP/RTS startup boot probe/text-fill writes | Crash-prevention and early bring-up bypassing | YES | YES | YES | YES | YES |
| A13 | `PATCH_OR_REMAP_FOR_DIAGNOSIS` | `specs/startup_title_remap.json` | `opcode_replace` C-window pointer/store/read bypass cluster (examples: `0x0556F2`, `0x05577E`, `0x0558C6`, `0x0558E0`, `0x055904`, plus contiguous NOP store block `0x0503F6..0x050428`) | Replaces many C-window pointer and memory-write/read instructions with NOP/RTS/bypass forms | Prevent unmapped-window crashes and pointer-propagation faults during bring-up | YES | YES | YES | YES | YES |
| A14 | `PATCH_OR_REMAP_FOR_DIAGNOSIS` | `specs/startup_title_remap.json` | Text-writer silencing entries (`0x03BB66`, `0x03BB68`, `0x03BB74`, `0x03BB76`) and additional C-window writer NOP entries (`0x052858`, `0x052974`, `0x0575CE`, `0x0576A8`, `0x0576B0`, `0x0576C4`, `0x0576CE`, `0x0576D4`, `0x057754`) | Silences legacy direct C-window text/status writes while using hook paths | Prevent direct unmapped C-window writes on Genesis | YES | YES | YES | YES | YES |
| A15 | `PATCH_OR_REMAP_FOR_DIAGNOSIS` | `specs/startup_title_remap.json` | Transition/helper bypass entries (`0x03A294`, `0x03A2B2`, `0x03A6B2`, `0x03A860`, `0x03AC54`) | RTS/NOP/BRA bypasses in transition clusters and unstable helper call sites | Avoid address errors and unsafe helper paths | YES | YES | YES | YES | YES |
| A16 | `OTHER_TEMPORARY_OR_CONTAMINATING_CHANGE` | `specs/startup_title_remap.json` | Policy note: `Test mode remains on the preview/debug path` | Test-mode path remains redirected to preview/debug flow instead of board-style final flow | Bring-up staging decision | YES | YES | YES | YES | YES |
| A17 | `OTHER_TEMPORARY_OR_CONTAMINATING_CHANGE` | `apps/rastan/src/startup_bridge.c` | `genesistan_palette_rom_table` comment: “Retained as fallback/debug data” | Fallback/debug palette table remains present alongside CLCS capture path | Transitional palette architecture during migration | YES | YES | YES | YES | YES |

## 3. Temporary / Diagnostic Changes Found in History But Not Active Now

| Item | Exact change | Source of evidence | Still present now | May have affected later reasoning |
|---|---|---|---|---|
| H01 | Top-of-hook early return in `genesistan_hook_frontend_sprite_sat_refresh` disabled entire hook path (`return;` at entry) | `docs/design/build338_disable_sprite_sat_dma_hook.md`, `AGENTS_LOG.md` Build 338 block | NO | YES |
| H02 | Unconditional zero-scroll proof commit (forced all H/V scroll to zero every frame) | `docs/design/build322_unconditional_zero_scroll_proof_fix.md`, `AGENTS_LOG.md` Build 322 and Build 333 restoration entry | NO | YES |
| H03 | Script-driven proof patching path to disable VDP systems except PC080SN (`tools/debug/patch_disable_vdp_except_pc080sn.py`) | `AGENTS_LOG.md` entries around Build 317 isolation tooling | YES (tool exists) / NO (not active in current ROM runtime path) | YES |
| H04 | Hook-disabled SAT test ROM path (`genesistan_render_sprites_vdp` unreachable) superseded by Build 339 hook-restored path | `AGENTS_LOG.md` Build 338 then Build 339 entries | NO | YES |

## 4. High-Risk Contaminants

| Item ref | Risk reason | Severity |
|---|---|---|
| A05 | Disables tick-phase preload ownership path and removes runtime tile availability behavior | HIGH |
| A06 | Injects forced CRAM palette not sourced from normal runtime palette ownership | HIGH |
| A07 | Suppresses SAT DMA publish while leaving sprite prep active, altering final presentation contract | HIGH |
| A08 | Unconditional early return removes entire assembly sprite renderer path | HIGH |
| A09 | Palette commit function is explicitly marked temporary proof strategy | HIGH |
| A10 | Disabled row-visibility filter changes text placement domain | MEDIUM |
| A11 | Pointer sanitizer mutates work RAM data post-tick, changing code-path causality | HIGH |
| A12 | Boot probe/text-fill NOP/RTS bypasses alter startup behavior | HIGH |
| A13 | C-window pointer/store/read bypass cluster alters foundational memory contract | HIGH |
| A14 | Text-writer C-window silencing entries alter original writer semantics | HIGH |
| A15 | Transition/helper bypasses remove original control-flow work | HIGH |

## 5. Master Cleanup Candidates

| Item ref | Short name | Category | Current status | Cleanup priority |
|---|---|---|---|---|
| A01 | FG sentinel before/after capture | `TEMPORARY_SENTINEL_TEST` | ACTIVE | IMMEDIATE |
| A02 | Bulk A0 pre-read capture | `INSTRUMENTATION` | ACTIVE | IMMEDIATE |
| A03 | Plane-A debug telemetry overlay | `DEBUG_OVERLAY` | ACTIVE | SOON |
| A04 | VDP commit frame counters/history | `INSTRUMENTATION` | ACTIVE | SOON |
| A05 | Tick preload path suppression | `TEMPORARY_SUPPRESSION` | ACTIVE | IMMEDIATE |
| A06 | Post-reset forced test palette | `TEMPORARY_PALETTE_TEST` | ACTIVE | IMMEDIATE |
| A07 | C sprite SAT DMA commit disabled | `TEMPORARY_SPRITE_TEST` | ACTIVE | IMMEDIATE |
| A08 | ASM sprite renderer early RTS | `TEMPORARY_EARLY_RETURN` | ACTIVE | IMMEDIATE |
| A09 | Temporary palette commit algorithm | `TEMPORARY_PALETTE_TEST` | ACTIVE | VERIFY_FIRST |
| A10 | Text row filter disabled | `OTHER_TEMPORARY_OR_CONTAMINATING_CHANGE` | ACTIVE | SOON |
| A11 | Work RAM C-window pointer sanitizer | `OTHER_TEMPORARY_OR_CONTAMINATING_CHANGE` | ACTIVE | VERIFY_FIRST |
| A12 | Boot probe/text-fill bypasses | `PATCH_OR_REMAP_FOR_DIAGNOSIS` | ACTIVE | IMMEDIATE |
| A13 | C-window pointer/store/read bypass cluster | `PATCH_OR_REMAP_FOR_DIAGNOSIS` | ACTIVE | IMMEDIATE |
| A14 | Text-writer silencing bypass cluster | `PATCH_OR_REMAP_FOR_DIAGNOSIS` | ACTIVE | IMMEDIATE |
| A15 | Transition/helper bypass cluster | `PATCH_OR_REMAP_FOR_DIAGNOSIS` | ACTIVE | IMMEDIATE |
| A16 | Test-mode preview/debug routing | `OTHER_TEMPORARY_OR_CONTAMINATING_CHANGE` | ACTIVE | VERIFY_FIRST |
| A17 | Palette fallback/debug table retention | `OTHER_TEMPORARY_OR_CONTAMINATING_CHANGE` | ACTIVE | LATER |
| H01 | Hook top-return suppression (Build 338) | `TEMPORARY_EARLY_RETURN` | REVERTED | VERIFY_FIRST |
| H02 | Zero-scroll forced commit (Build 322) | `TEMPORARY_SCROLL_TEST` | REVERTED | VERIFY_FIRST |
| H03 | Offline disable-vdp proof script | `TEMPORARY_BUILD_PROOF` | UNCLEAR | LATER |
| H04 | Hook-disabled SAT DMA test path | `TEMPORARY_SPRITE_TEST` | REVERTED | VERIFY_FIRST |

## 6. Single Most Important Next Non-Code Step
`BUILD_MASTER_DIAGNOSTIC_DEBT_DOCUMENT`

## 7. Final Verdict
The project currently contains an active stack of temporary/proof/suppression and instrumentation changes across source and remap spec layers. The largest active contaminant set is the spec-level bypass cluster (`NOP`/`RTS`/`Bypass` entries), followed by runtime proof hooks in VBlank and sprite/palette suppression tests. A consolidated master diagnostic-debt document is required before further root-cause conclusions are treated as stable.
