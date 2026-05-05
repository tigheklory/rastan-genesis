# Cody Build 53 RTS Identification and Caller Chain Trace (Read-Only)

## Scope
- Task type: read-only evidence extraction.
- Inputs: compiled ROM artifacts, disassembly, symbol map, address map, remap spec, and prior extraction docs.
- No source/spec/tool/ROM artifact files were modified.

## §1.1 RTS instructions in `genesistan_hook_tilemap_bg_fill` and adjacent helper region

Boundary used for `genesistan_hook_tilemap_bg_fill`:
- Start: `0x00070570` (`apps/rastan-direct/out/symbol.txt:163`)
- End (exclusive): `0x00070646` (`apps/rastan-direct/out/symbol.txt:164`)

RTS inside `genesistan_hook_tilemap_bg_fill` range:
- `0x00070644`: `rts` (`build/genesis_postpatch.disasm.txt:123143`)
  - Observation: immediately after `moveml %sp@+,%d0-%fp` at `0x00070640`.

Adjacent helper before `genesistan_hook_tilemap_bg_fill` (`genesistan_hook_tilemap_fg`):
- Symbol range: `0x000703CE..0x00070570` (`apps/rastan-direct/out/symbol.txt:162-163`)
- RTS in this adjacent symbol:
  - `0x0007055E`: `rts` (`build/genesis_postpatch.disasm.txt:123072`)
  - `0x0007056E`: `rts` (`build/genesis_postpatch.disasm.txt:123076`)

Adjacent helper after `genesistan_hook_tilemap_bg_fill`:
- Symbol: `genesistan_hook_text_writer_3c4d2`
- Start: `0x00070646` (`apps/rastan-direct/out/symbol.txt:164`)

`genesistan_hook_3ad44_dispatch` RTS:
- Symbol range: `0x00071434..0x000714D6` (`apps/rastan-direct/out/symbol.txt:183-184`)
- RTS:
  - `0x000714D4`: `rts` (`build/genesis_postpatch.disasm.txt:124295`)

## §1.2 Function boundaries for involved helpers

Symbol table source window:
- `apps/rastan-direct/out/symbol.txt:158-198`

Required helpers:
- `genesistan_hook_tilemap_bg_fill`: `0x00070570..0x00070646` = `0xD6` bytes
- `genesistan_hook_3ad44_dispatch`: `0x00071434..0x000714D6` = `0xA2` bytes
- `vdp_commit_sprites`: `0x00071834..0x000719F6` = `0x1C2` bytes
- `genesistan_pc090oj_dma_self_test`: `0x000719F6..0x00071AFC` = `0x106` bytes

Other helper symbols in the requested wrapper span (`0x00070000..0x0017C96C`):
- `vdp_boot_setup` `0x00070000..0x0007007E`
- `_vblank_service` `0x000700C2..0x00070106`
- `genesistan_hook_tilemap_plane_a` `0x0007022C..0x000703CE`
- `genesistan_hook_tilemap_fg` `0x000703CE..0x00070570`
- `genesistan_hook_text_writer_3c4d2` `0x00070646..0x00070832`
- `genesistan_hook_text_writer_3c950` `0x00070832..0x000709F2`
- `genesistan_hook_number_renderer_3c2e2` `0x000709F2..0x00070B8A`
- `genesistan_hook_text_writer_3c550` `0x00070B8A..0x00070BDA`
- `genesistan_hook_text_writer_3c586` `0x00070BDA..0x00070CC8`
- `genesistan_hook_text_writer_3c636` `0x00070CC8..0x00070DA0`
- `genesistan_hook_text_writer_3c6dc` `0x00070DA0..0x00070E24`
- `genesistan_hook_text_writer_3c75c` `0x00070E24..0x00070EDC`
- `genesistan_hook_text_writer_3c7a4` `0x00070EDC..0x00070F4A`
- `genesistan_hook_text_writer_3c830` `0x00070F4A..0x0007106C`
- `genesistan_hook_cwindow_clear` `0x0007106C..0x000710CA`
- `genesistan_pc090oj_hook_target_3b902` `0x00071340..0x00071382`
- `genesistan_pc090oj_hook_target_3b926` `0x00071382..0x0007139A`
- `genesistan_pc090oj_hook_target_3b930` `0x0007139A..0x000713D8`
- `genesistan_pc090oj_hook_target_41dae` `0x000713D8..0x000713E6`
- `genesistan_pc090oj_hook_target_41f5e` `0x000713E6..0x000713F4`
- `genesistan_pc090oj_hook_target_45dfa` `0x000713F4..0x00071402`
- `genesistan_pc090oj_hook_target_59f5e` `0x00071402..0x00071434`
- `genesistan_pc090oj_hook_init_priority_3ad84` `0x000714D6..0x0007150C`
- `genesistan_pc090oj_hook_score_digit_3b802` `0x0007150C..0x000715F8`
- `genesistan_pc090oj_hook_slot_init_54052` `0x000715F8..0x00071688`
- `genesistan_pc090oj_hook_sprite_update_54810` `0x00071688..0x000716E6`
- `genesistan_pc090oj_hook_sprite_decay_5607c` `0x000716E6..0x0007175A`
- `genesistan_pc090oj_hook_copy_56114` `0x0007175A..0x0007179A`
- `genesistan_pc090oj_hook_zero_fill_56440` `0x0007179A..0x000717B4`
- `genesistan_pc090oj_hook_status_sprite_5a098` `0x000717B4..0x000717F0`
- `genesistan_pc090oj_hook_audit_guard` `0x000717F0..0x00071834`
- `load_scene_tiles` `0x00071AFC..0x00071B9C`

## §1.3 Call sites targeting dispatch (`0x71434`) or tilemap_bg_fill (`0x70570`)

Runtime disassembly callsites:
- To `0x00071434` (`genesistan_hook_3ad44_dispatch`):
  - Caller `0x0003AF44`: `jsr 0x71434` (`build/genesis_postpatch.disasm.txt:73741`)
- To `0x00070570` (`genesistan_hook_tilemap_bg_fill`):
  - Caller `0x00071498`: `bsrw 0x70570` (`build/genesis_postpatch.disasm.txt:124280`)

Instruction classes (verbatim):
- `0x0003AF44`: `jsr` (return-pushing)
- `0x00071498`: `bsrw` (return-pushing)

Remap entries containing symbol placeholders:
- Dispatch symbol placeholder found:
  - `arcade_pc: 0x03AD44`
  - `replacement_bytes: 4EB9{symbol:genesistan_hook_3ad44_dispatch}4E75`
  - (`specs/rastan_direct_remap.json:307-310`)
- Tilemap symbol placeholder in `replacement_bytes`:
  - none found (`{symbol:genesistan_hook_tilemap_bg_fill}` not present in `replacement_bytes` fields).

## §1.4 Tilemap caller chain trace (4 callers) and stack-return-address sequence

Arcade callers (from `build/maincpu.disasm.txt`):

1) Caller `arcade_pc 0x03AE70`
- Context (`build/maincpu.disasm.txt:73975-73979`):
  - `3ae64: lea 0xc00100,%a0`
  - `3ae6a: movew #1900,%d1`
  - `3ae6e: moveq #32,%d0`
  - `3ae70: bsrw 0x3ad44`
- A0 at call: `0x00C00100`

2) Caller `arcade_pc 0x03AE80`
- Context (`build/maincpu.disasm.txt:73979-73983`):
  - `3ae74: lea 0xc08100,%a0`
  - `3ae7a: movew #1900,%d1`
  - `3ae7e: moveq #32,%d0`
  - `3ae80: bsrw 0x3ad44`
- A0 at call: `0x00C08100`

3) Caller `arcade_pc 0x03AF38`
- Context (`build/maincpu.disasm.txt:74023-74027`):
  - `3af2c: lea 0xc00000,%a0`
  - `3af32: movew #4096,%d1`
  - `3af36: moveq #32,%d0`
  - `3af38: bsrw 0x3ad44`
- A0 at call: `0x00C00000`

4) Caller `arcade_pc 0x03AF48`
- Context (`build/maincpu.disasm.txt:74027-74031`):
  - `3af3c: lea 0xc08000,%a0`
  - `3af42: movew #4096,%d1`
  - `3af46: moveq #32,%d0`
  - `3af48: bsrw 0x3ad44`
- A0 at call: `0x00C08000`

Runtime path for these 4 tilemap callers:
- Runtime caller sites:
  - `0x0003B070: bsrw 0x3AF44` (`build/genesis_postpatch.disasm.txt:73845`)
  - `0x0003B080: bsrw 0x3AF44` (`build/genesis_postpatch.disasm.txt:73849`)
  - `0x0003B138: bsrw 0x3AF44` (`build/genesis_postpatch.disasm.txt:73919`)
  - `0x0003B148: bsrw 0x3AF44` (`build/genesis_postpatch.disasm.txt:73923`)
- Opcode-replaced site body:
  - `0x0003AF44: jsr 0x71434` (`build/genesis_postpatch.disasm.txt:73741`)
  - `0x0003AF4A: rts` (`build/genesis_postpatch.disasm.txt:73742`)
- Dispatch tilemap branch call:
  - `0x00071498: bsrw 0x70570` (`build/genesis_postpatch.disasm.txt:124280`)
  - `0x0007149C: bras 0x714d0` (`build/genesis_postpatch.disasm.txt:124281`)

Return addresses (from next-instruction addresses shown in disassembly):
- From tilemap caller BSR to `0x3AF44`:
  - `0x0003B070` call returns to `0x0003B074`
  - `0x0003B080` call returns to `0x0003B084`
  - `0x0003B138` call returns to `0x0003B13C`
  - `0x0003B148` call returns to `0x0003B14C`
- From `jsr 0x71434` at `0x0003AF44`: returns to `0x0003AF4A`
- From `bsrw 0x70570` at `0x00071498`: returns to `0x0007149C`

Expected stacked return-address sequence for this tilemap-dispatch call path (at execution inside `0x00070570` body):
- Top: `0x0007149C`
- Next: `0x0003AF4A`
- Next: one of `0x0003B074 / 0x0003B084 / 0x0003B13C / 0x0003B14C` (caller-dependent)

## §1.5 Expected vs observed return address

Expected top-of-stack return address for the tilemap-dispatch call path above:
- `0x0007149C` (from `bsrw 0x70570` at `0x00071498`, next instruction at `0x0007149C`)

Observed wild PC after RTS (from frame extraction evidence):
- `0x008F831C` (`docs/design/Cody_exodus_frame_extraction_build_53_2.md:140-144`)

Match:
- `NO`

## §1.6 Caller invocation class check (JSR/BSR/JMP)

Call sites checked (from §1.3 and §1.4):
- `0x0003B070 -> 0x0003AF44`: `bsrw` (return-pushing)
- `0x0003B080 -> 0x0003AF44`: `bsrw` (return-pushing)
- `0x0003B138 -> 0x0003AF44`: `bsrw` (return-pushing)
- `0x0003B148 -> 0x0003AF44`: `bsrw` (return-pushing)
- `0x0003AF44 -> 0x00071434`: `jsr` (return-pushing)
- `0x00071498 -> 0x00070570`: `bsrw` (return-pushing)

Counts:
- JSR/BSR-family (return-pushing): 6
- JMP-family (no return push): 0
- Mismatched call-class at listed sites: none observed

## §1.7 Replacement boundary verification at `arcade_pc 0x03AD44`

Original arcade bytes/instructions:
- Remap/original bytes:
  - `original_bytes: 20C0534166FA4E75` (`specs/rastan_direct_remap.json:308`)
- Arcade disassembly context:
  - `3ad44: movel %d0,%a0@+`
  - `3ad46: subqw #1,%d1`
  - `3ad48: bnes 0x3ad44`
  - `3ad4a: rts`
  - (`build/maincpu.disasm.txt:73893-73896`)

Replacement bytes:
- `replacement_bytes: 4EB9{symbol:genesistan_hook_3ad44_dispatch}4E75`
  (`specs/rastan_direct_remap.json:309`)

Length check:
- Original footprint: 8 bytes (`0x03AD44..0x03AD4C`) (`build/rastan-direct/address_map.json`, segment index 49)
- Replacement footprint: 8 bytes (`genesis_start 0x03AF44`, `genesis_end_exclusive 0x03AF4C`) (`build/rastan-direct/address_map.json`, segment index 49)

Bytes after replacement:
- Next segment begins at `genesis_start 0x03AF4C` / `arcade_start 0x03AD4C`, `kind: arcade_copy` (`build/rastan-direct/address_map.json`, segment index 50)
- Runtime disassembly at `0x03AF4C` shows normal copied code start (`movew #8,%d1`) (`build/genesis_postpatch.disasm.txt:73743`)

Fall-through check:
- Replaced sequence at runtime:
  - `0x03AF44: jsr 0x71434`
  - `0x03AF4A: rts`
  - (`build/genesis_postpatch.disasm.txt:73741-73742`)
- Fall-through past replaced site body: `NO` (site ends with `rts`).

## §1.8 Symbol coverage for `runtime_genesis_pc 0x000711CE`

Symbol ownership from `apps/rastan-direct/out/symbol.txt`:
- `rastan_direct_update_inputs` starts at `0x000710CA` (`symbol.txt:175`)
- Next symbol `genesistan_pc090oj_hook_target_3b902` starts at `0x00071340` (`symbol.txt:176`)

Coverage result:
- `0x000711CE` is inside `rastan_direct_update_inputs` range `0x000710CA..0x00071340`.
- Offset from symbol start: `0x104`
- Symbol body size: `0x276` bytes

Classification for §1.8 options:
- `PC inside helper body` (inside named symbol body; not in a symbol gap).

## Integrity checklist
- §1.1 RTS instructions enumerated with citations: YES
- §1.2 function boundaries determined for required helpers: YES
- §1.3 call sites enumerated for dispatch/tilemap targets: YES
- §1.4 tilemap caller chain trace documented with cited disassembly: YES
- §1.5 expected vs observed return address compared: YES
- §1.6 JSR/BSR/JMP class verified for listed call sites: YES
- §1.7 replacement boundary at `0x03AD44` verified: YES
- §1.8 symbol coverage for `0x711CE` determined: YES
- Analysis/diagnosis/hypotheses/recommendations: NONE

