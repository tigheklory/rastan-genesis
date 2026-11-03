# Cody - OPEN-018 Class A Raw FG Immediate Routing STOP

**Date:** 2026-06-26
**Type:** Implementation attempt + STOP analysis
**Scope requested:** Route four Class A raw PC080SN FG immediate writes through `genesistan_hook_tilemap_fg_fill` using byte-neutral opcode replacements. No source/spec/tool/ROM changes retained after STOP. No bookmark cycle. No fix shipped.

## Phase 0

Read required project rules and current findings/log context before implementation. Classification: **EXTENDING** OPEN-018 / OPEN-001. OPEN-015 not touched.

Address mapping was performed through `build/rastan-direct/address_map.json` segment containment, not arithmetic as authority:

| runtime_genesis_pc | JSON segment kind | arcade_pc |
|---|---|---|
| `0x0003ACEA` | `arcade_copy` | `0x0003AAEA` |
| `0x0003A550` | `arcade_copy` | `0x0003A350` |
| `0x0003A8FE` | `arcade_copy` | `0x0003A6FE` |
| `0x0003A908` | `arcade_copy` | `0x0003A708` |

## Attr Gate Evidence

Before source edits, I ran an original arcade MAME read-only debugger trace and confirmed the paired PC080SN FG attr words were zero in the live title/story page state:

Trace artifact:
`states/traces/open018_attr_gate_original_arcade_20260626_163825/native_debug_trace.log`

Captured event:

```text
EVENT ATTR_GATE_ALL_AT_3AAEA ... attr_C09170=0000 code_C09172=0020 attr_C08A50=0000 code_C08A52=0020 attr_C08E78=0000 code_C08E7A=0020 attr_C08E64=0000 code_C08E66=0020
```

Result: attr gate **PASS** for all four sites (`0xC09170`, `0xC08A50`, `0xC08E78`, `0xC08E64`).

## Implementation Attempt

I attempted the requested implementation shape:

- Four dedicated `genesistan_hook_inline_fg_write_*` trampolines.
- Full `movem.l %d0-%d7/%a0-%a6` preservation.
- Each trampoline loaded `A0` with the aligned PC080SN FG attr-word address, `D0` with `attr<<16|code`, `D1=1`, then called `genesistan_hook_tilemap_fg_fill`.
- Four `opcode_replace` entries were added at arcade PCs `0x03A350`, `0x03A6FE`, `0x03A708`, `0x03AAEA`.

No ROM artifact was produced.

## STOP Reason

The prompt requires each replacement to be a **6-byte byte-neutral `jsr abs.l`**. The target instructions are not 6 bytes; they are 8-byte 68000 instructions:

```text
33 FC iiii aaaaaaaa
move.w #imm16, abs.l
```

Examples:

| runtime_genesis_pc | Original bytes | Length |
|---|---|---:|
| `0x0003ACEA` | `33 FC 27 49 00 C0 91 72` | 8 |
| `0x0003A550` | `33 FC 00 32 00 C0 8A 52` | 8 |
| `0x0003A8FE` | `33 FC 27 44 00 C0 8E 7A` | 8 |
| `0x0003A908` | `33 FC 27 44 00 C0 8E 66` | 8 |

A `jsr abs.l` is 6 bytes (`4E B9` + 32-bit address), so it is not byte-neutral for these sites. The postpatch tool correctly rejected the replacement:

```text
RuntimeError: opcode_replace at 0x03A350: original_bytes and replacement_bytes must be the same length.
```

Using `jsr abs.l` plus a trailing `nop` would be 8 bytes, but the prompt explicitly required a 6-byte replacement and the project rules forbid unapproved NOP/equal-length workaround behavior. Therefore implementation under the given constraints is impossible.

## Cleanup

All source/spec/tool edits from the failed attempt were removed:

- `apps/rastan-direct/src/tilemap_hooks.s` restored to pre-attempt content.
- `specs/rastan_direct_remap.json` restored to opcode_replace count `98` and no four new routing entries.
- `tools/translation/postpatch_startup_rom.py` restored to `98 / 0x17CD68`.
- `tools/translation/verify_canonical_rom.py` restored to `98 / 0x17CD68`.

Generated build byproducts under `apps/rastan-direct/out/` and valid trace artifacts remain from the attempt. No release ROM was produced.

## Recommended Next Directive

A corrected implementation directive needs to choose one approved byte-neutral strategy for 8-byte sites, for example:

- approve `jsr abs.l + nop` as padding for these four 8-byte `move.w #imm,abs.l` replacements; or
- authorize a shift-table replacement that shrinks/grows code correctly; or
- authorize another production-safe 8-byte control-transfer pattern.

Do not proceed until the replacement shape is clarified, because the current prompt's 6-byte byte-neutral requirement contradicts the actual instruction encoding.

## Impact

- OPEN-018 remains open.
- KNOWN_FINDINGS unchanged.
- No source/spec/tool/ROM fix retained.
- STOP triggered: **YES**.
