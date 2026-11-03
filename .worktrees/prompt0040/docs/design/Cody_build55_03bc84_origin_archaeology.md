# Cody Build 55 0x03BC84 Origin Archaeology

## Scope
- Type: read-only archaeology + trace post-value analysis
- Build context: `rastan-direct` Build 0055
- Runtime authority: `build/genesis_postpatch.disasm.txt`

## §1.1 Address-map classification + arcade ROM presence
- Runtime `0x03BC84` is inside address-map segment:
  - `genesis_start=0x03BB50`, `genesis_end_exclusive=0x03C4E2`, `kind=arcade_copy`, `arcade_start=0x03B950`, `identity_offset=512` (`build/rastan-direct/address_map.json:1229-1236`).
- Therefore `runtime_genesis_pc 0x03BC84 -> arcade_pc 0x03BA84` by identity offset `+0x200`.

Arcade ROM cross-check:
- `arcade_pc 0x03BA84` exists (`build/maincpu.disasm.txt:74896`).
- Runtime body at `0x03BC64..0x03BC86` matches arcade body at `0x03BA64..0x03BA86` with +`0x200` relocation:
  - Runtime: `build/genesis_postpatch.disasm.txt:74813-74827`
  - Arcade: `build/maincpu.disasm.txt:74883-74897`
- Classification: postpatch-transformed relocation (same instructions, shifted addresses).

## §1.2 Symbol map presence
- Symbol at `0x03BC84`: none (`apps/rastan-direct/out/symbol.txt`, no matching entry).
- Symbol in prior `0x100` window `0x03BB84..0x03BC83`: none (no matching entries in symbol map).
- Nearest preceding symbol <= `0x03BC84`: `0000fc00 a VRAM_HSCROLL_BASE` (`apps/rastan-direct/out/symbol.txt:150`).

Keyword matches in symbol map (`palette|checkerboard|vblank|sgdk|convert|clear|init|cram|loader`):
- `0000024a _bootstrap_clear_staging` (`apps/rastan-direct/out/symbol.txt:28`)
- `00000520 crash_vdp_reinit` (`apps/rastan-direct/out/symbol.txt:58`)
- `0000058a crash_init_cram` (`apps/rastan-direct/out/symbol.txt:59`)
- `000009aa crash_clear_plane_a` (`apps/rastan-direct/out/symbol.txt:62`)
- `000700c2 _vblank_service` (`apps/rastan-direct/out/symbol.txt:155`)
- `000701cc vdp_commit_palette` (`apps/rastan-direct/out/symbol.txt:159`)
- `0007106c genesistan_hook_cwindow_clear` (`apps/rastan-direct/out/symbol.txt:174`)
- `000711e2 genesistan_palette_hook_59ad4` (`apps/rastan-direct/out/symbol.txt:176`)
- `00071248 genesistan_palette_hook_03ab00` (`apps/rastan-direct/out/symbol.txt:177`)
- `0007126c genesistan_palette_hook_45dae` (`apps/rastan-direct/out/symbol.txt:178`)
- `000715c6 genesistan_pc090oj_hook_init_priority_3ad84` (`apps/rastan-direct/out/symbol.txt:187`)
- `000716e8 genesistan_pc090oj_hook_slot_init_54052` (`apps/rastan-direct/out/symbol.txt:189`)
- `00071cae z80_init_and_start` (`apps/rastan-direct/out/symbol.txt:201`)
- `00ff4000 palette_dirty` (`apps/rastan-direct/out/symbol.txt:244`)
- `00ff601a staged_palette_words` (`apps/rastan-direct/out/symbol.txt:256`)
- `00ff686a CRASH_PALETTE_DIRTY` (`apps/rastan-direct/out/symbol.txt:313`)

No `checkerboard`, `sgdk`, `convert`, or `loader` symbol names were found in this symbol file.

## §1.3 Source file search
Address literal search (`apps/rastan-direct/src` + `apps/rastan/src`):
- No matches for `0x03BC84`, `0x3BC84`, `0x03BA84`, `0x3BA84`, `0x03BC64`, `0x03BBF8`, `0x03B110` (`rg` returned no results).

Pattern search:
- No source match for `movew %d0,%a0@+` across these trees (`rg` returned no results).
- `0x200000` appears only in Build-55 helper source comments/checks:
  - `apps/rastan-direct/src/palette_hooks.s:105`
  - `apps/rastan-direct/src/palette_hooks.s:110`
- No `0x200000` hits in `apps/rastan/src` SGDK tree (`rg` returned no results).

Origin classification from source search + disassembly cross-check:
- `0x03BC84` source origin in repo files: NOT FOUND.
- Code origin type: **COPIED-FROM-ARCADE** (runtime body matches arcade body with +`0x200` relocation; §1.1 citations).

## §1.4 Git history archaeology
- §1.3 did not identify a repository source file defining `0x03BC84`; origin is copied arcade code.
- Per task rule for copied-from-arcade origin: git archaeology of source introduction is **N/A** (arcade ROM is external).

## §1.5 Producer / clearer / mixed classification
Parsed all `WP_PALETTE_RAM` events in:
- `states/traces/build55_active_palette_discovery_20260504_143202/debug.log`

Counts:
- Total writes: `11760`
- `post = 0`: `1305` (`11.0969%`)
- `post != 0`: `10455` (`88.9031%`)
- Writer PC distribution: all writes from `pc=0x03BC84` (sample lines include `158`, `160`, `164`, `25132`).

Representative non-zero samples (10):
- `debug.log:158` `addr=0x200000 pre=0x0000 post=0x00FF pc=0x03BC84`
- `debug.log:164` `addr=0x200006 pre=0x29D0 post=0x0202 pc=0x03BC84`
- `debug.log:168` `addr=0x20000A pre=0x29D4 post=0x032E pc=0x03BC84`
- `debug.log:172` `addr=0x20000E pre=0x7BDE post=0x0334 pc=0x03BC84`
- `debug.log:176` `addr=0x200012 pre=0x7BDE post=0x033A pc=0x03BC84`
- `debug.log:180` `addr=0x200016 pre=0x7BDE post=0x0340 pc=0x03BC84`
- `debug.log:184` `addr=0x20001A pre=0x7BDE post=0x0346 pc=0x03BC84`
- `debug.log:188` `addr=0x20001E pre=0x7BDE post=0x034C pc=0x03BC84`
- `debug.log:192` `addr=0x200022 pre=0x001E post=0x0352 pc=0x03BC84`
- `debug.log:196` `addr=0x200026 pre=0x001E post=0x0358 pc=0x03BC84`

Classification:
- **MIXED** (fails ≥95% thresholds for CLEARER and PRODUCER).

Interleave/group check:
- Zero/non-zero are interleaved in early sequence (e.g., `debug.log:158..196` alternates frequently).
- Run analysis over full event stream: many short zero runs (max 8) and longer non-zero runs (max 320), indicating both behaviors occur materially.

## §1.6 Caller chain analysis (postpatch authority)
Static chain from postpatch disassembly:
- `0x03BC84` loop back-edge to `0x03BC64` (`build/genesis_postpatch.disasm.txt:74826`).
- `0x03BC64` loop body begins at `movew %a3@+,%d0` (`build/genesis_postpatch.disasm.txt:74813`).
- `0x03BBF8` calls `0x03BC64` twice (`build/genesis_postpatch.disasm.txt:74788`, `74791`) and returns (`74792`).
- Callers of `0x03BBF8`: `0x03B110`, `0x03B380`, `0x03B446` (`build/genesis_postpatch.disasm.txt:73906`, `74092`, `74153`).

Runtime reach evidence:
- Chain probe captures repeated sequence:
  - `BP_BOOT_022C` (`...chain_probe.../debug.log:44`)
  - `BP_BOOT_024A` (`...chain_probe.../debug.log:46`)
  - `BP_FN_3B110` (`...chain_probe.../debug.log:48`)
  - `BP_FN_3BBF8` (`...chain_probe.../debug.log:50`)
  - `BP_FN_3BC64` (`...chain_probe.../debug.log:52`)
- The same ordering repeats later (e.g., `...chain_probe.../debug.log:3190..3196`).

_vblank comparison:
- `_vblank_service` symbol is `0x000700C2` (`apps/rastan-direct/out/symbol.txt:155`).
- No static call edge in this chain section to `0x000700C2`; chain addresses are in the `0x03Bxxx..0x03BCxx` block.
- Separate trace confirms `_vblank_service` runs (`docs/design/Cody_build55_mame_palette_runtime_trace.md:22`), but this `0x03BC84` chain evidence is tied to the repeated bootstrap/startup path events above.

Chain-reach classification for this task:
- **Reached from `_bootstrap` re-entry path** (not from `_vblank_service`) based on repeated `0x022C/0x024A` then `0x03B110/0x03BBF8/0x03BC64` ordering in the same trace.

## §1.7 Origin classification
- Classification: **A. Arcade-original**.

Cited reasoning:
1. Address map class is `arcade_copy` for the containing segment, with identity offset `+0x200` (`build/rastan-direct/address_map.json:1229-1236`).
2. Runtime `0x03BC84` maps to `arcade_pc 0x03BA84` and the 32-instruction body matches relocated arcade code (`build/genesis_postpatch.disasm.txt:74813-74827`; `build/maincpu.disasm.txt:74883-74897`).
3. No repository source definition was found in `apps/rastan-direct/src` or `apps/rastan/src`; SGDK tree has no `0x200000` palette-RAM producer path for this address.
4. Runtime chain evidence shows this copied code is actively reached via the startup re-entry sequence (`...chain_probe.../debug.log:44-52`, `3190-3196`).

## §2 Integrity
- §1.1 address_map classification: PROVEN
- §1.1 arcade ROM cross-check: PROVEN
- §1.2 symbol map presence: PROVEN
- §1.3 source file origin identified: NOT FOUND (classified copied-from-arcade)
- §1.4 git history archaeology: N/A (copied-from-arcade)
- §1.5 producer/clearer/mixed: MIXED (counts reported)
- §1.6 caller chain to `_vblank_service` or arcade dispatch: PROVEN to `_bootstrap` re-entry path
- §1.7 origin classification: A
- All findings cited: YES
- No hypotheses beyond evidence: YES
- No fixes recommended: YES
- No external sources: YES
- No broad decompilation as authority: YES
- Postpatch primary for runtime: YES
- Address map authoritative: YES
- Decisive classification only: YES
- No source/spec/tool modifications: YES
- STOP conditions encountered: NONE
