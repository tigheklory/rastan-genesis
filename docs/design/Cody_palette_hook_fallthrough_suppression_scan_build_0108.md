# Cody - Palette-Hook Fall-Through Suppression Scan, Build 0108

**Date:** 2026-06-27
**Type:** Evidence / static analysis only
**Build:** 0108, `dist/rastan-direct/rastan_direct_video_test_build_0108.bin`
**Build SHA256:** `bd0c7faa187f6d9aded904638e8d7cb8c9e3df6304c5178a36ec02e6c8bbad09`
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build changes. No bookmark cycle. No diagnostic ROM. No fix design or implementation.

## Phase 0

Read in full: `RULES.md` and `ARCHITECTURE.md`.

Baseline context: `docs/design/Cody_highscore_timer_expiry_evidence_v3_build_0108.md` proved Build 0108 reaches the correct story-expiry/high-score selector state `(s0,s2,s4)=(0,1,2)`, timer `FF002C=0`, and enters `runtime_genesis_pc 0x03AD00`, but the patched site returns before the high-score tail at `0x03AD08+`.

Address discipline: every arcade-to-Genesis code correlation below is from `build/rastan-direct/address_map.json`. No `+0x200` arithmetic is used as proof. Address labels use `arcade_pc`, `runtime_genesis_pc`, `genesis_rom_offset`, `HW_ADDRESS`, and `Genesis-WRAM` explicitly where applicable.

## Q1 - Arcade Intent at `arcade_pc 0x03AB00`

### Original Instruction

Arcade disassembly:

```asm
arcade_pc 0x03AB00: 33fc 03ff 0020 0022  movew #0x03FF,0x00200022
arcade_pc 0x03AB08: 6100 0350            bsrw 0x03AE5A
arcade_pc 0x03AB0C: 6100 0BB0            bsrw 0x03B6BE
arcade_pc 0x03AB10: 703C                 moveq #60,%d0
arcade_pc 0x03AB12: 6100 1034            bsrw 0x03BB48
```

The instruction at `arcade_pc 0x03AB00` is 8 bytes long and falls through to `arcade_pc 0x03AB08`.

### Hardware Meaning of `HW_ADDRESS 0x00200022`

Authoritative MAME reference: `docs/reference/mame/rastan/src/mame/taito/rastan.cpp`.

Relevant MAME lines:

```cpp
map(0x200000, 0x200fff).ram().w("palette", FUNC(palette_device::write16)).share("palette");
PALETTE(config, "palette").set_format(palette_device::xBGR_555, 2048);
```

So `HW_ADDRESS 0x00200022` is inside arcade CLCS palette RAM, handled by MAME's `palette_device::write16`, with format `xBGR_555` and 2048 entries.

Offset calculation inside the same hardware address space:

- `0x00200022 - 0x00200000 = 0x22` bytes.
- 16-bit palette words imply entry index `0x22 / 2 = 0x11` decimal 17.
- With 16 colors per bank, this is palette bank `1`, entry `1`.

### Plain-Language Intent

The arcade instruction writes color word `0x03FF` directly into CLCS palette RAM at palette bank 1, entry 1. In arcade color terms, the value is already an `xBGR_555` palette word. The visible intent is to update one palette color at the story-expiry/high-score transition.

The full arcade intent at this site is two-part:

1. Apply the palette/color update at `HW_ADDRESS 0x00200022`.
2. Continue execution into the high-score page setup tail at `arcade_pc 0x03AB08+`.

### Genesis Hook Assessment

Build 0108 maps `arcade_pc 0x03AB00..0x03AB08` to `runtime_genesis_pc 0x03AD00..0x03AD08` as a `patched_site`:

```text
original_bytes:    33fc03ff00200022
replacement_bytes: 4eb9000714f44e75
```

Runtime replacement:

```asm
runtime_genesis_pc 0x03AD00: jsr 0x0714F4 ; genesistan_palette_hook_03ab00
runtime_genesis_pc 0x03AD06: rts
```

Hook source: `apps/rastan-direct/src/palette_hooks.s`.

```asm
genesistan_palette_hook_03ab00:
    movem.l %d0-%d3/%a0, -(%sp)
    move.w  #0x03FF, %d0
    bsr     .Lxbgr555_to_cram
    lea     staged_palette_words, %a0
    move.w  %d1, 34(%a0)
    move.b  #1, palette_dirty
    movem.l (%sp)+, %d0-%d3/%a0
    rts
```

Assessment: `genesistan_palette_hook_03ab00` **approximates/reproduces intent (1) in the port-correct way**. It takes the same `0x03FF` arcade `xBGR_555` value, converts it to Genesis CRAM format, writes the corresponding staged palette word at byte offset `34` (`entry 17`, bank 1 entry 1), and sets `palette_dirty`.

The hook does **not** reproduce intent (2), because the patched-site `RTS` returns before `runtime_genesis_pc 0x03AD08+`.

Conclusion for later work: the evidence supports that a later fix needs to restore the arcade fall-through/control-flow intent. The palette hook's color effect is not shown defective by this task, aside from the inherent Genesis color-depth conversion.

## Q2 - High-Score Tail Intactness

Address-map anchors from `build/rastan-direct/address_map.json`:

| Meaning | arcade_pc | runtime_genesis_pc / genesis_rom_offset | Map kind |
|---|---:|---:|---|
| patched palette site | `0x03AB00` | `0x03AD00` | `patched_site` |
| clear tail | `0x03AB08` | `0x03AD08` | `arcade_copy` |
| high-score init | `0x03AB0C` | `0x03AD0C` | `arcade_copy` |
| high-score render | `0x03AB12` | `0x03AD12` | `arcade_copy` |
| high-score timer reload | `0x03AB22` | `0x03AD22` | `arcade_copy` |
| master advance | `0x03AB48` | `0x03AD48` | `arcade_copy` |
| clear helper entry | `0x03AE64` | `0x03B064` | `arcade_copy` |
| clear helper BG call | `0x03AE70` | `0x03B070` | `arcade_copy` |
| clear helper FG call | `0x03AE80` | `0x03B080` | `arcade_copy` |

Build 0108 ROM bytes at `genesis_rom_offset 0x03AD00`:

```text
4eb9000714f44e75 6100035061000bb0 ...
```

This shows the patched `jsr; rts`, immediately followed by the intact original tail bytes beginning at `genesis_rom_offset 0x03AD08`.

Tail disassembly in Build 0108:

```asm
runtime_genesis_pc 0x03AD08: 6100 0350       bsrw 0x03B05A        ; clear tail call
runtime_genesis_pc 0x03AD0C: 6100 0BB0       bsrw 0x03B8BE        ; high-score init
runtime_genesis_pc 0x03AD10: 703C            moveq #60,%d0
runtime_genesis_pc 0x03AD12: 6100 1034       bsrw 0x03BD48        ; high-score render line/id 60
runtime_genesis_pc 0x03AD16: 703D            moveq #61,%d0
runtime_genesis_pc 0x03AD18: 6100 102E       bsrw 0x03BD48
runtime_genesis_pc 0x03AD1C: 703E            moveq #62,%d0
runtime_genesis_pc 0x03AD1E: 6100 1028       bsrw 0x03BD48
runtime_genesis_pc 0x03AD22: 3b7c 00a0 002c  movew #160,%a5@(44)
runtime_genesis_pc 0x03AD28: 41ed 0100       lea %a5@(256),%a0
runtime_genesis_pc 0x03AD2C: 30bc 0000       movew #0,%a0@
runtime_genesis_pc 0x03AD30: 43ed 0102       lea %a5@(258),%a1
runtime_genesis_pc 0x03AD34: 701f            moveq #31,%d0
runtime_genesis_pc 0x03AD36: 6100 f798       bsrw 0x03A4D0
runtime_genesis_pc 0x03AD3A: 41ed 0100       lea %a5@(256),%a0
runtime_genesis_pc 0x03AD3E: 6100 fea6       bsrw 0x03ABE6
runtime_genesis_pc 0x03AD42: 3b7c 0001 0100  movew #1,%a5@(256)
runtime_genesis_pc 0x03AD48: 3b7c 0002 0000  movew #2,%a5@(0)
runtime_genesis_pc 0x03AD4E: 426d 0002       clrw %a5@(2)
runtime_genesis_pc 0x03AD52: 426d 0004       clrw %a5@(4)
runtime_genesis_pc 0x03AD56: 4e75            rts
```

Clear helper path in Build 0108:

```asm
runtime_genesis_pc 0x03B05A: 6100 0008       bsrw 0x03B064
runtime_genesis_pc 0x03B05E: 6100 0238       bsrw 0x03B298
runtime_genesis_pc 0x03B062: 4e75            rts
runtime_genesis_pc 0x03B064: 41f9 00c0 0100  lea 0x00C00100,%a0
runtime_genesis_pc 0x03B06A: 323c 076c       movew #1900,%d1
runtime_genesis_pc 0x03B06E: 7020            moveq #32,%d0
runtime_genesis_pc 0x03B070: 6100 fed2       bsrw 0x03AF44
runtime_genesis_pc 0x03B074: 41f9 00c0 8100  lea 0x00C08100,%a0
runtime_genesis_pc 0x03B07A: 323c 076c       movew #1900,%d1
runtime_genesis_pc 0x03B07E: 7020            moveq #32,%d0
runtime_genesis_pc 0x03B080: 6100 fec2       bsrw 0x03AF44
runtime_genesis_pc 0x03B084: 4e75            rts
```

Result: **TAIL INTACT: YES.**

The high-score page setup tail and clear helper are present in Build 0108 and mapped as arcade copies. They are skipped only because `runtime_genesis_pc 0x03AD06` returns before `runtime_genesis_pc 0x03AD08` executes.

## Q3 - Bounded Sibling Palette-Hook Fall-Through Suppression Scan

Bounded candidate selection: palette/control-write opcode replacements in `specs/rastan_direct_remap.json` whose replacement invokes `genesistan_palette_hook_*`, cross-checked against `build/rastan-direct/address_map.json` and Build 0108 disassembly/bytes.

Candidates examined: `4`.

### Candidate 1 - `arcade_pc 0x03AB00` / `runtime_genesis_pc 0x03AD00`

- Original instruction/span: `33FC03FF00200022`, 8 bytes.
- Original mnemonic: `movew #0x03FF,0x00200022`.
- Original control flow: falls through to meaningful high-score setup at `arcade_pc 0x03AB08+`.
- Replacement shape in Build 0108: `jsr genesistan_palette_hook_03ab00; rts` (`4EB9000714F44E75`).
- Does RTS skip meaningful arcade code? **YES.** It skips `runtime_genesis_pc 0x03AD08+` clear/init/render/timer-reload/master-advance.
- Classification: **FALL-THROUGH-SUPPRESSING HOOK**.

### Candidate 2 - `arcade_pc 0x059AD4` / `runtime_genesis_pc 0x059CD4`

- Original span: `C2FC0020...4E75`, 70 bytes.
- Original role: complete palette conversion/writer routine. It multiplies row/bank inputs, targets `HW_ADDRESS 0x00200000 + bank*0x20`, writes up to 16 converted palette words, and exits with `RTS` at `arcade_pc 0x059B18`.
- Replacement shape in Build 0108: `jsr genesistan_palette_hook_59ad4; rts; nop padding`.
- Does RTS skip meaningful arcade fall-through code? **NO.** The original span itself ended in `RTS`; bytes after the routine are data/table words, not fall-through code.
- Classification: **SAFE TERMINAL HOOK**.

### Candidate 3 - `arcade_pc 0x045DB8` / `runtime_genesis_pc 0x045FB8`

- Original instruction/span: `4EB90003A4D0`, 6 bytes.
- Original mnemonic: `jsr 0x03A2D0`.
- Original control flow: the original `JSR` returned to meaningful caller code at `arcade_pc 0x045DBE` (`addqw #1,%a5@(568)`), then `RTS` at `0x045DC2`.
- Replacement shape in Build 0108: single-instruction target swap `jsr genesistan_palette_hook_45dae` (`4EB900071518`), no inserted `RTS` at the patched site.
- Runtime mapped fall-through remains present:

```asm
runtime_genesis_pc 0x045FB8: 4eb9 0007 1518  jsr 0x071518
runtime_genesis_pc 0x045FBE: 526d 0238       addqw #1,%a5@(568)
runtime_genesis_pc 0x045FC2: 4e75            rts
```

- Does replacement skip meaningful arcade fall-through code? **NO.** The meaningful fall-through at `runtime_genesis_pc 0x045FBE` is preserved.
- Classification: **SAFE TERMINAL HOOK** for the bounded suppression concern. More precisely: safe non-terminal JSR-target swap.

### Candidate 4 - `arcade_pc 0x03BA64` / `runtime_genesis_pc 0x03BC64`

- Original span: `301B3400...538366DE4E75`, 34 bytes.
- Original role: active palette writer loop. It reads from `%a3`, converts a 0RGB-style value into xBGR-ish palette word form, writes through `%a0@+`, decrements `%d3`, loops with `bnes 0x03BA64`, and exits with `RTS` at `arcade_pc 0x03BA86`.
- Replacement shape in Build 0108: `jsr genesistan_palette_hook_3ba64; rts; nop padding`.
- Does RTS skip meaningful arcade fall-through code? **NO.** The original span itself ended in `RTS`; bytes after the routine are table/data-looking words and not required fall-through code.
- Classification: **SAFE TERMINAL HOOK**.

## Sibling Scan Result

Sibling `FALL-THROUGH-SUPPRESSING HOOK` count: `1`.

List:

- `arcade_pc 0x03AB00` / `runtime_genesis_pc 0x03AD00` only.

Within the bounded palette/control hook set, `0x03AB00` is a one-off confirmed suppression. The broader bug pattern is real (`hook + rts` replacing a fall-through instruction), but no other palette-hook candidate in this bounded scan shares the damaging control-flow shape.

## Recommendation for Next Step

Recommendation: **Andy one-site design (`arcade_pc 0x03AB00` / `runtime_genesis_pc 0x03AD00`)**.

Reason: the skipped high-score tail is intact, the palette hook effect appears port-correct for the direct color write, and the bounded sibling scan found no other fall-through-suppressing palette hook.

This is a recommendation only, not a fix design or implementation.

## OPEN / KNOWN_FINDINGS Impact

- Open issues touched: OPEN-001 context, OPEN-018/Class B context, OPEN-015 not touched.
- Issues opened: NONE.
- Issues closed: NONE.
- `KNOWN_FINDINGS.md` impact: no update in this evidence-only task. A later canonicalization may be useful if the team wants to record the `0x03AB00` fall-through suppression mechanism.

## STOP

STOP triggered: **NO**.

No source, spec, tool, Makefile, ROM, build artifact, bookmark artifact, or diagnostic ROM was modified.
