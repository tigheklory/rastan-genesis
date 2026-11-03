# Cody — OPEN-016 Part 2 Glyph Renderer Hook

**Date:** 2026-06-19
**Type:** Implementation + static verification
**Scope:** Hook runtime Genesis `0x0003BD48` / arcade source `0x0003BB48` title glyph/string renderer into the existing FG staging path. No runtime probing. No bookmark cycle. No crash-handler work. No Start-C-A crash investigation. OPEN-016 remains open.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-028 (input-shim/title-text U3 arc), KF-013 (text dispatch inside VBlank), KF-010 (FG maps to Plane A), OPEN-016 (Part 2 active), OPEN-015 (deferred crash-handler defects), OPEN-001 (rendering context). No contradiction detected.

## Phase 1.3 — Destination Enumeration

OPEN-016 Part 1 ROM SHA verified: `c9fab1b47ccd3dd7dff76dbd4fe8776521287697a9e6824917a1b7a10131b390`.

- Direct runtime Genesis callers of `0x0003BD48`: 48 (`bsrw 0x3bd48` sites)
- Unique possible `d0` values: 48 (branch-fed call sites included)
- Unique descriptor destinations: 40
- Destinations in PC080SN FG C-window `0x00C08000..0x00C0FFFF`: 40
- Destinations outside FG C-window: 0
- Acceptance: **PASS**

Branch-fed call sites with multiple possible IDs were preserved in the proof: `0x3A910` (`56/4/5`), `0x3AAFC` (`10/11`), and `0x3AC68` (`30/12`). Negative/large IDs were resolved with the original `idx = d0 & 0x7F` rule: `-126 -> idx 2`, `132 -> idx 4`, `186 -> idx 58`.

Representative resolved destinations:

| d0 | idx | table entry | descriptor | dest | text |
|---:|---:|---|---|---|---|
| `65` | `65` | `0x03BE80` | `0x03C446` | `0x00C0914C` | `OTHERWISE I COULD NOT` |
| `63` | `63` | `0x03BE78` | `0x03C416` | `0x00C08D4C` | `I USED TO BE A THIEF` |
| `70` | `70` | `0x03BE94` | `0x03C4C4` | `0x00C09B4C` | `DAYS FULL OF ADVENTURE.` |
| `-126` | `2` | `0x03BD84` | `0x03BEBE` | `0x00C09E84` | `CREDIT   ` |
| `186` | `58` | `0x03BE64` | `0x03C39C` | `0x00C08A48` | `PLAYER 1` |

All caller-reached descriptors use zero-terminated printable byte strings; no caller-reached descriptor contains an unresolved escape/control byte.

## Phase 1.4 — Renderer Semantics

Original runtime Genesis routine `0x0003BD48..0x0003BD7A`:

```asm
3bd48: movew %d0,%d1
3bd4a: andiw #0x007f,%d0
3bd4e: lslw #2,%d0
3bd50: lea table,%a0
3bd54: addaw %d0,%a0
3bd56: moveal %a0@,%a0
3bd58: moveal %a0@+,%a1      ; descriptor[0] dest
3bd5a: movew %a0@+,%d2       ; descriptor[4] attr
3bd5c: tstb %d1
3bd5e: bmis space-mode
normal: read byte until 0; write attr word then glyph word to (a1)+
space-mode: read byte until 0; write attr word then 0x0020 space word to (a1)+
3bd7a: rts
```

Descriptor layout: `[long PC080SN dest][word attr][zero-terminated bytes]`.

Normal mode: one descriptor byte produces two PC080SN words: attr first, glyph second. Negative low-byte mode (`tst.b d1` negative) preserves descriptor length but writes spaces (`0x0020`) instead of glyph bytes. Termination is byte `0x00`, consumed before `RTS`.

Input contract: `d0` is the renderer ID and signed-byte mode source. No stack arguments. No other input register is required.

Output contract: original clobbers `d0/d1/d2/a0/a1` and condition codes; final `d0=0`, `a0` points after the terminator, and `a1` advances four bytes per emitted character. Callers do not read renderer outputs before setting their own next values or returning. The hook preserves the same loop termination and advances `a1` by the same amount while using staging for the hardware write.

Acceptance: **PASS**.

## Implementation

Added `genesistan_hook_glyph_renderer_3bd48` in `apps/rastan-direct/src/tilemap_hooks.s` and added the symbol to `specs/rastan_direct_remap.json`.

Added one `opcode_replace` entry at arcade source `0x03BB48` (runtime Genesis `0x03BD48`):

- Original span: 52 bytes (`0x03BD48..0x03BD7B` runtime)
- Replacement: `JSR genesistan_hook_glyph_renderer_3bd48; RTS; NOP padding`
- Descriptor table at runtime `0x03BD7C` preserved unchanged

The hook replays the original index/header/string loop. For each emitted glyph/space, it stages a composed Genesis Plane-A cell by reusing the existing `.Ltw_store_from_components_at_a2` helper with `a2 = a1 + 2`, then advances original `a1` by 4 bytes to preserve the renderer's destination-pointer progression.

Staging path statically verified in generated disassembly:

- `0x70BC8`: store helper saves caller-visible scratch registers
- `0x70BCC`: `a2 = a1`
- `0x70BCE`: `a2 += 2`
- `0x70BD4`: calls existing cell translator/store at `0x707BC`
- `0x70800`: subtracts `0x00C08000`
- `0x70794`: writes `staged_fg_buffer`
- `0x7079E`: `bset` row bit in `fg_row_dirty`
- `0x70BDC`: original `a1 += 4`

## Build Verification

- Patched ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Patched SHA256: `942dcb1aefebec7cbd808d016ff41f4bc22ec9ffd92c98be8a423297a56590cc`
- Boot guard: PASS
- Canonical gate: PASS (`GATE_PASS`)
- Repeat no-runtime rebuild: PASS, byte-identical SHA
- `opcode_replace` patched-site count: `94 -> 95`
- `total_genesis_bytes_covered`: `0x17CAF0 -> 0x17CB44`
- Mechanical delta: +1 hook, +`0x54` bytes (assembled symbol span `0x70B8E..0x70BE2`)

Static verification:

- Runtime `0x03BD48` wrapper calls `0x00070B8E` and leaves descriptor table at `0x03BD7C` intact.
- All 48 direct callers still call runtime `0x03BD48`.
- OPEN-016 Part 1 relocation preserved: `table[65] @ 0x03BE80 = 0x0003C446`; descriptor starts `00 C0 91 4C 00 00 "OTHERW..."`.
- Existing `genesistan_hook_text_writer_*` symbols remain present; no existing hook entries were removed.

## Status

OPEN-016 remains OPEN. Part 2 fixes the confirmed `0x3BD48` renderer write-destination gap, but the broader embedded data-pointer table survey and broader unhooked-writer survey remain out of scope.

Runtime probing: NO. Bookmark cycle: NO. Crash-handler work: NO. Start-C-A crash investigation: NO. KNOWN_FINDINGS update: NO.
