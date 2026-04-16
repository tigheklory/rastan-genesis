# Andy — Default Path `arcade_pc: 0x03C950` Sub-Caller Audit & Hook Spec

**Status:** SPEC COMPLETE. Ready for Cody. All sub-subs INTERNAL-only; safe single-`opcode_replace` patch span proven.
**Build Context:** Build 0034, `rastan-direct`.

---

## 1. Default Path Body

### 1.1 Entry-point confirmation

- Entry: **`arcade_pc: 0x03C950`** (`build/maincpu.disasm.txt:76289` — `clrw %d0`).
- Genesis offset (from `build/rastan-direct/address_map.json` `arcade_copy` segment `[0x03B0A4, 0x03EF28) → [0x03B2A4, 0x03F128)` with `identity_offset = 512`): **`genesis_rom_offset: 0x03CB50`**.
- ROM bytes at `genesis_rom_offset: 0x03CB50` are **unpatched original arcade bytes** (no `opcode_replace` in `specs/rastan_direct_remap.json` covers any address in `[0x03C950, 0x03CA38)`; the only patched site in the `0x03Cxxx` range is `0x03C4D2`).

### 1.2 Full disassembly (entry-point through end of last sub-sub)

```
arcade_pc      bytes              mnemonic
; ── default-path entry ──
0x03C950       4240               clrw   %d0
0x03C952       4245               clrw   %d5
0x03C954       0806 0000          btst   #0, %d6
0x03C958       6600 00CC          bnew   0x03CA26                   ; branch to alt-dispatch sub-sub
0x03C95C       4A07               tstb   %d7
0x03C95E       6746               beqs   0x03C9A6                   ; D7==0 → alt main-loop
; ── primary main loop (D7 != 0) ──
0x03C960       6100 009E          bsrw   0x03CA00                   ; sub-sub: read (A0)+ → D0/D3, sentinel-detect (sets D5=1 if 0xFF)
0x03C964       4A45               tstw   %d5
0x03C966       6600 008E          bnew   0x03C9F6                   ; → fast-fill escape if sentinel hit
0x03C96A       4247               clrw   %d7
0x03C96C       0C03 0040          cmpib  #0x40, %d3
0x03C970       6602               bnes   0x03C974
0x03C972       5247               addqw  #1, %d7                    ; D7 = 1 if D3 == 0x40
0x03C974       0C03 0080          cmpib  #-128, %d3                 ; cmpib #0x80, %d3
0x03C978       6604               bnes   0x03C97E
0x03C97A       0040 4000          oriw   #0x4000, %d0               ; D0 |= 0x4000 if D3 == 0x80
0x03C97E       6100 0068          bsrw   0x03C9E8                   ; sub-sub: A4@(39) bit 6 → may load D0 from A4@(39).b
0x03C982       32C0               movew  %d0, %a1@+                 ; ★ WRITE A — A1@+ → cell-N attribute slot
0x03C984       1218               moveb  %a0@+, %d1                 ; read script byte
0x03C986       4881               extw   %d1
0x03C988       D26C 001A          addw   %a4@(26), %d1              ; D1 = script_byte + A4@(26) (tile base)
0x03C98C       6100 FF68          bsrw   0x03C8F6                   ; helper: cmpib #0x70,D3; addw A4@(24),D1 if match (NOTE: lives BEFORE entry; see §1.5)
0x03C990       32C1               movew  %d1, %a1@+                 ; ★ WRITE B — A1@+ → cell-N tile slot
0x03C992       6100 007E          bsrw   0x03CA12                   ; sub-sub: read (A0)+ → D0; conditional negw on D7; addw A4@(30); ★ WRITE C inside (movew %d0,%a1@+)
0x03C996       1E18               moveb  %a0@+, %d7                 ; read script byte
0x03C998       4887               extw   %d7
0x03C99A       DE6C 0016          addw   %a4@(22), %d7              ; D7 = script_byte + A4@(22) (attribute base)
0x03C99E       32C7               movew  %d7, %a1@+                 ; ★ WRITE D — A1@+ → cell-(N+1) tile slot
0x03C9A0       5382               subql  #1, %d2                    ; loop control
0x03C9A2       66BC               bnes   0x03C960
0x03C9A4       4E75               rts
; ── alt main loop (D7 == 0) ──
0x03C9A6       6100 0058          bsrw   0x03CA00                   ; sentinel sub-sub
0x03C9AA       4A45               tstw   %d5
0x03C9AC       6600 0048          bnew   0x03C9F6                   ; → fast-fill escape
0x03C9B0       4247               clrw   %d7
0x03C9B2       0C03 0040          cmpib  #0x40, %d3
0x03C9B6       6602               bnes   0x03C9BA
0x03C9B8       5247               addqw  #1, %d7
0x03C9BA       0040 4000          oriw   #0x4000, %d0               ; UNCONDITIONAL in alt path (no D3==0x80 test)
0x03C9BE       6100 0028          bsrw   0x03C9E8                   ; sub-sub
0x03C9C2       32C0               movew  %d0, %a1@+                 ; ★ WRITE E
0x03C9C4       1218               moveb  %a0@+, %d1
0x03C9C6       4881               extw   %d1
0x03C9C8       D26C 001A          addw   %a4@(26), %d1
0x03C9CC       32C1               movew  %d1, %a1@+                 ; ★ WRITE F
0x03C9CE       6100 0042          bsrw   0x03CA12                   ; sub-sub (★ WRITE G inside)
0x03C9D2       1E18               moveb  %a0@+, %d7
0x03C9D4       4887               extw   %d7
0x03C9D6       4447               negw   %d7                        ; ! ALT-PATH NEGATION
0x03C9D8       9E78 0010          subw   0x10, %d7                  ; subw absolute-short addr, NOT immediate (see §1.6)
0x03C9DC       DE6C 0016          addw   %a4@(22), %d7
0x03C9E0       32C7               movew  %d7, %a1@+                 ; ★ WRITE H
0x03C9E2       5382               subql  #1, %d2
0x03C9E4       66C0               bnes   0x03C9A6
0x03C9E6       4E75               rts
; ── sub-sub 0x03C9E8 ──
0x03C9E8       082C 0006 0027     btst   #6, %a4@(39)
0x03C9EE       6704               beqs   0x03C9F4
0x03C9F0       102C 0027          moveb  %a4@(39), %d0              ; D0 = A4@(39).b if bit 6 set
0x03C9F4       4E75               rts
; ── sub-sub 0x03C9F6 (fast-fill escape; reached via bnew from main loops) ──
0x03C9F6       337C 0180 0002     movew  #0x0180, %a1@(2)           ; ★ WRITE I — blank tile at A1+2 (cell-N tile)
0x03C9FC       5089               addql  #8, %a1                    ; advance A1 by 8 (skip cell N and cell N+1)
0x03C9FE       60A0               bras   0x03C9A0                   ; jump to loop tail (D2 dec + bne)
; ── sub-sub 0x03CA00 ──
0x03CA00       1018               moveb  %a0@+, %d0
0x03CA02       1600               moveb  %d0, %d3
0x03CA04       0203 00F0          andib  #-16, %d3                  ; D3 = top nibble of script byte
0x03CA08       0C00 00FF          cmpib  #-1, %d0
0x03CA0C       6602               bnes   0x03CA10
0x03CA0E       7A01               moveq  #1, %d5                    ; D5 = 1 sentinel marker
0x03CA10       4E75               rts
; ── sub-sub 0x03CA12 (writes inside) ──
0x03CA12       4240               clrw   %d0
0x03CA14       1018               moveb  %a0@+, %d0
0x03CA16       4A47               tstw   %d7
0x03CA18       6702               beqs   0x03CA1C
0x03CA1A       4440               negw   %d0                        ; D0 = -D0 if D7 != 0
0x03CA1C       D06C 001E          addw   %a4@(30), %d0              ; D0 += A4@(30) (per-glyph X-offset?)
0x03CA20       32C0               movew  %d0, %a1@+                 ; ★ WRITE C/G inside CA12
0x03CA22       4240               clrw   %d0
0x03CA24       4E75               rts
; ── sub-sub 0x03CA26 (alt-dispatch entry; reached when D6 bit 0 is set) ──
0x03CA26       4A2C 0003          tstb   %a4@(3)
0x03CA2A       6600 FF34          bnew   0x03C960                   ; back into primary main loop
0x03CA2E       4A07               tstb   %d7
0x03CA30       6700 FF2E          beqw   0x03C960                   ; back into primary main loop
0x03CA34       6000 FF70          braw   0x03C9A6                   ; back into alt main loop
; ── data follows at 0x03CA38 ──
0x03CA38       FCFF...                                              ; data table (NOT executed)
```

### 1.3 Write instructions targeting `HW_ADDRESS/PC080SN/FG_TILEMAP`

All writes target the destination held in A1, which the dispatcher
upstream supplies as a pointer in PC080SN FG tilemap range when text
content is being rendered. Exhaustive list:

| Tag | `arcade_pc` | Instruction | Path |
|-----|-------------|-------------|------|
| WRITE A | `0x03C982` | `movew %d0, %a1@+` | primary main loop, cell-N attr slot |
| WRITE B | `0x03C990` | `movew %d1, %a1@+` | primary main loop, cell-N tile slot |
| WRITE C | `0x03CA20` (inside sub `0x03CA12`) | `movew %d0, %a1@+` | primary main loop via `bsr 0x03CA12`, cell-(N+1) attr slot |
| WRITE D | `0x03C99E` | `movew %d7, %a1@+` | primary main loop, cell-(N+1) tile slot |
| WRITE E | `0x03C9C2` | `movew %d0, %a1@+` | alt main loop, cell-N attr slot |
| WRITE F | `0x03C9CC` | `movew %d1, %a1@+` | alt main loop, cell-N tile slot |
| WRITE G | `0x03CA20` (same instruction as WRITE C, second invocation in alt path) | `movew %d0, %a1@+` | alt main loop via `bsr 0x03CA12`, cell-(N+1) attr slot |
| WRITE H | `0x03C9E0` | `movew %d7, %a1@+` | alt main loop, cell-(N+1) tile slot |
| WRITE I | `0x03C9F6` | `movew #0x0180, %a1@(2)` | fast-fill escape (sentinel `0xFF` hit), single blank-tile cell at A1+2 |

Sub-sub `0x03C9E8` performs **no writes** (only reads `A4@(39)` and
loads D0 if a flag bit is set). Sub-sub `0x03CA00` performs **no
writes** (only reads from A0 stream and sets D5 sentinel marker).
Sub-sub `0x03CA26` performs **no writes** (only branches into the main
loops based on `A4@(3).b` and D7).

### 1.4 Write-shape classification

- **Primary write shape: stride-2 `A1@+` post-increment, 4 words per iteration** (WRITES A/B/C/D in primary path; WRITES E/F/G/H in alt path). Net A1 advance per iteration: 8 bytes = 2 arcade tilemap cells (4 bytes each, `[attr_word, tile_word]` Taito convention).
- **Per-iteration cell coverage:** 2 cells. Cell N: WRITE A (attribute) + WRITE B (tile). Cell N+1: WRITE C (attribute, via sub `0x03CA12`) + WRITE D (tile). Same per-iteration A1 advance as the stride-8 family (`+8` bytes), but **different write granularity** — default path writes the **full 4-byte cell record** (tile+attr) for both cells, whereas stride-8 family writes only the tile word for each cell.
- **Fast-fill escape (WRITE I):** `movew #0x0180, %a1@(2)`. Same shape as the stride-8 family's blank-tile sentinel write. Followed by `addq.l #8, A1` and a branch back to the loop tail — so a single sentinel iteration fills only the **tile slot of cell N**, leaves cell-N attr untouched, and does not write cell N+1 at all.

### 1.5 Note on out-of-range helper at `arcade_pc: 0x03C8F6`

The default path's primary main loop calls `bsrw 0x03C8F6` at
`arcade_pc: 0x03C98C`. This helper lives **outside** the 0x03C950
default-path range (it sits between handler 0x03C830 and dispatcher
0x03C902). It contains no `A1` writes — just `cmpib #0x70, D3; bnes ;
addw A4@(24), D1` (a tile-base-offset adjustment when D3 == 0x70).
Single caller via grep: only `arcade_pc: 0x03C98C`. After the default
path is patched, 0x03C8F6 becomes dead code (its only reachable caller
is overwritten). **It is NOT included in the patch span** because it
lives outside the contiguous 0x03C950+ range. Cody's hook must
replicate the `D3 == 0x70 → D1 += A4@(24)` adjustment internally.

### 1.6 Note on `subw 0x10, D7` at `arcade_pc: 0x03C9D8`

`9E78 0010` decodes to `subw <abs.w 0x0010>, D7` — i.e. subtract from
D7 the word at absolute short address `0x000010`. Address `0x000010`
is inside the Genesis `preserved_vectors` segment (Genesis vector
table location for trap 0). On the original arcade hardware this
addressed something in low-RAM/vector space too. On Genesis it reads
the preserved vectors. Cody MUST replicate this read exactly — the
hook executes `subw 0x10, D7` against whatever the Genesis vector area
contains. (This is an arcade-code-quirk preserved by the relocation.)

### 1.7 Opcode routing

Per `docs/design/Andy_dispatcher_map_analysis.md` §2: top-nibble values
**not** matching any of `0x10, 0x20, 0x30, 0x50, 0x60, 0x90, 0xA0, 0xB0, 0xC0`
fall through the dispatcher to `arcade_pc: 0x03C950`. By exhaustion
this is the set: **`0x00, 0x40, 0x70, 0x80, 0xD0, 0xE0, 0xF0`**.

Confirmation in default-path body: `D3` (the top-nibble byte set by
sub-sub `0x03CA00`) is compared to `0x40`, `0x80`, and (in helper
`0x03C8F6`) `0x70` — three of the seven opcodes are explicitly handled
with conditional behavior here. The other four (`0x00, 0xD0, 0xE0, 0xF0`)
fall through with default attribute composition (no `0x4000` OR-mask,
no D7 increment, no D1 base-offset adjustment).

No double-routing: each top nibble is checked at most once in the
dispatcher's `cmpib` ladder, and after the last `beqw 0x03C586` at
`arcade_pc: 0x03C94C` execution falls through unconditionally to
`arcade_pc: 0x03C950`.

---

## 2. Sub-Caller Audit Results

Method: `grep` of `build/maincpu.disasm.txt` for each sub-sub address.

| Sub-sub `arcade_pc` | All callers found | Internal? | Genesis offset |
|---------------------|--------------------|----------|----------------|
| `0x03C9E8` | `0x03C97E (bsrw)`, `0x03C9BE (bsrw)` — both inside default-path body | **INTERNAL only** | `0x03CBE8` |
| `0x03C9F6` | `0x03C966 (bnew)`, `0x03C9AC (bnew)` — both inside default-path body | **INTERNAL only** | `0x03CBF6` |
| `0x03CA00` | `0x03C960 (bsrw)`, `0x03C9A6 (bsrw)` — both inside default-path body | **INTERNAL only** | `0x03CC00` |
| `0x03CA12` | `0x03C992 (bsrw)`, `0x03C9CE (bsrw)` — both inside default-path body | **INTERNAL only** | `0x03CC12` |
| `0x03CA26` | `0x03C958 (bnew)` — inside default-path entry | **INTERNAL only** | `0x03CC26` |

**No external callers for any of the 5 sub-subs.** All 5 are safely
includable in the patch span.

Out-of-scope helper noted in §1.5 (`0x03C8F6`): also INTERNAL-only
(single caller `0x03C98C` inside default path), but lives outside the
contiguous 0x03C950+ range, so excluded from the patch span and
becomes dead code after patch.

---

## 3. Safe Patch Span

### 3.1 Boundaries

- **Start:** `arcade_pc: 0x03C950` (entry confirmed in §1.1).
- **End (last byte of last sub-sub):** the final RTS / branch of the
  last sub-sub `0x03CA26` is the `braw 0x3C9A6` at `arcade_pc: 0x03CA34`,
  which is a 4-byte instruction (`6000 FF70`) ending at
  `arcade_pc: 0x03CA37`. The next address `0x03CA38` is data
  (`fcff fffa ...` per `build/maincpu.disasm.txt:76372+`).
- **Span:** `arcade_pc: 0x03C950..0x03CA37` inclusive = **`0xE8` bytes
  (232)**.

### 3.2 Genesis-side range

From `address_map.json` `arcade_copy` segment record with
`identity_offset = 512`: span maps to
`genesis_rom_offset: 0x03CB50..0x03CC37` inclusive = `0xE8` bytes.

### 3.3 Binary verification

- ROM bytes at `genesis_rom_offset: 0x03CB50..0x03CC37` are the
  verbatim arcade code bytes shown in §1.2 (no `opcode_replace` entry
  in `specs/rastan_direct_remap.json` covers any address in this
  range; the only patched site in the `0x03Cxxx` arcade range is
  `0x03C4D2`, which ends well before `0x03C950`).
- No overlap with any existing `patched_site` segment.
- Span lies entirely inside the single `arcade_copy` segment
  `[0x03B0A4, 0x03EF28) → [0x03B2A4, 0x03F128)`.

### 3.4 Safety statement

**Safe to replace with a single `opcode_replace` entry at
`arcade_pc: 0x03C950`. Span = 0xE8 bytes. No external callers exist
for any code inside the span.** Out-of-range helper `0x03C8F6`
becomes unreachable after the patch (dead code, no harm).

---

## 4. Hook Contract — `genesistan_hook_text_writer_3c950`

Zero design decisions remain after this section.

### 4.1 Hook name

`genesistan_hook_text_writer_3c950`.

### 4.2 Input register contract

| Reg | Role at hook entry | Source |
|-----|--------------------|--------|
| **A0** | Script pointer. Default path reads via `(A0)+` from sub-sub `0x03CA00`, plus per-iteration in the body. | Dispatcher upstream. |
| **A1** | Destination pointer. Expected in `HW_ADDRESS/PC080SN/FG_TILEMAP` (`[0xC08000, 0xC0C000)`); writes via `A1@+` (stride 2) and one `A1@(2)` (fast-fill). | Dispatcher upstream. |
| **A4** | Script-state block. Fields read: `A4@(3).b` (in `0x03CA26` alt-dispatch), `A4@(22).w` (attribute base), `A4@(24).w` (D3==0x70 tile-base offset, via `0x03C8F6` semantics inlined into the hook), `A4@(26).w` (tile base), `A4@(30).w` (per-glyph offset, in `0x03CA12`), `A4@(39).b` (in `0x03C9E8` — bit 6 gates D0 load). | Script state. |
| **D0** | Cleared at entry; subsequently composed (with possible `0x4000` OR for `D3==0x80`, plus `A4@(39).b` from `0x03C9E8`) and used for WRITE A/E. | Internal to hook. |
| **D2** | Loop count. Decremented by `subq.l #1, D2; bne` at end of each main-loop iteration. Caller-supplied. | Caller. |
| **D3** | Script opcode top-nibble (set by `0x03CA00` sub-sub from `(A0)+` read). Used for `cmpib #0x40 / #0x70 / #0x80` decisions. | `0x03CA00` reads it from `(A0)+`; first byte of script payload. |
| **D5** | Cleared at entry; set to `1` by `0x03CA00` when sentinel `0xFF` byte read; gates fast-fill escape. | Internal. |
| **D6** | Bit 0 selects entry path (`0` → main loop, `1` → alt-dispatch via `0x03CA26`). Caller-supplied. | Caller. |
| **D7** | Selects which main loop is used (`0` → alt loop, non-zero → primary loop). Inside loops also used as path/sign flag (`0x03CA12` negation gate). Caller-supplied at entry; clobbered/recomputed inside. | Caller. |

### 4.3 Write contract — full enumeration of forms

| Write form | Composition | Cell slot in 4-byte arcade cell record |
|------------|-------------|----------------------------------------|
| WRITE A (primary, cell-N attr) | `D0` = (`0` or `(A4@(39).b)` per `0x03C9E8`) `|` (`0x4000` if `D3 == 0x80`) | attribute word of cell N |
| WRITE B (primary, cell-N tile) | `D1` = `script_byte + A4@(26)` `+ A4@(24)` (if `D3 == 0x70`) | tile word of cell N |
| WRITE C (primary, cell-(N+1) attr; inside sub `0x03CA12`) | `D0` = `script_byte`; if D7 != 0, negate; then `+= A4@(30)` | attribute word of cell N+1 |
| WRITE D (primary, cell-(N+1) tile) | `D7` = `script_byte + A4@(22)` | tile word of cell N+1 |
| WRITE E (alt, cell-N attr) | `D0` = `0` `\| 0x4000` `\|` (`(A4@(39).b)` if bit 6 set in `A4@(39)`) — note: alt path always ORs `0x4000` (no `D3==0x80` check) | attribute word of cell N |
| WRITE F (alt, cell-N tile) | `D1` = `script_byte + A4@(26)` (no `D3==0x70` adjustment in alt path) | tile word of cell N |
| WRITE G (alt, cell-(N+1) attr; inside `0x03CA12`) | same as WRITE C | attribute word of cell N+1 |
| WRITE H (alt, cell-(N+1) tile) | `D7` = `-script_byte − [word at absolute address 0x000010] + A4@(22)` | tile word of cell N+1 |
| WRITE I (fast-fill escape) | `0x0180` literal (blank tile) at `A1@(2)` | tile word of cell N (only); cell-N attr untouched; cell N+1 not written; A1 += 8 |

### 4.4 Output contract

For every cell N produced by WRITES A/B (or E/F) and every cell (N+1)
produced by WRITES C/D (or G/H), the hook MUST:

1. Compute `arcade_tile = D1` (or D7 for cell N+1) — the tile word, masked to `0x3FFF` for LUT lookup.
2. Compute `arcade_attr` — the attribute word **as a single 16-bit value composed from D0** (cell N) or **the value `D0` from sub `0x03CA12`** (cell N+1).
3. Translate: `gen_tile = genesistan_pc080sn_tile_vram_lut[arcade_tile]`; `gen_attr = genesistan_pc080sn_attr_lut[<attribute-bits-extracted-per-existing-hook-pattern>]`.
4. Compose: `nametable_word = gen_tile | gen_attr`.
5. Compute `(row, col)` for the cell using the same row/col formula as `docs/design/Andy_text_writer_3c4d2_hook_spec.md` §5.1: `cell_index = (current_A1 - 0xC08000) / 4; col = cell_index & 0x3F; row = (cell_index >> 6) & 0x3F`.
6. Write `nametable_word` to `staged_fg_buffer[row * 64 + col]`.
7. `bset row, fg_row_dirty`.

For WRITE I (fast-fill blank): emit one blank-tile cell at the cell
whose tile slot is `A1+2`, then advance `A1` by 8 (skipping cell N+1
entirely). Cell-N attribute is **not** updated by this escape (the
existing attribute word in `staged_fg_buffer[row*64 + col]` is
preserved by writing only the tile component or, simpler, by writing
`gen_tile_blank | gen_attr_default` consistent with the existing
`genesistan_hook_cwindow_clear` behavior).

**A1 final value on hook exit:** `A1 = entry_A1 + (D2_entry × 8)`
(if no fast-fill iterations) or `entry_A1 + (D2_entry × 8) + 8 ×
fast_fill_count` (which is the same — every iteration including
fast-fill advances A1 by 8). **Cody MUST set A1 to this exact value
before RTS** so dispatcher caller state is preserved.

**A0 final value on hook exit:** advanced by the script-byte reads
performed across all iterations. Each non-sentinel iteration of
primary path consumes 3 bytes (one in `0x03CA00`, one at `0x03C984`,
one in `0x03CA12`, one at `0x03C996`) — actually 4 bytes per primary
iteration. Each non-sentinel iteration of alt path consumes 4 bytes
similarly. Each sentinel-triggering iteration consumes 1 byte (the
0xFF) before the escape. **Cody MUST mirror these A0 advances exactly
to preserve downstream dispatcher state.**

### 4.5 Caller analysis

- Single caller of `arcade_pc: 0x03C950`: dispatcher fall-through from `arcade_pc: 0x03C94C` (`beqw 0x3c586`) ending its case-ladder and falling into `0x03C950`. There is **no** direct `bsr/jsr 0x03C950` anywhere in the arcade ROM (verified by grep — no matches for `0x3c950` outside the dispatcher continuation).
- Genesis offset of the fall-through point: `arcade_pc: 0x03C94C` → `genesis_rom_offset: 0x03CB4C` (immediately above the patched 0x03C950 entry). The fall-through is implicit (no instruction targets 0x03C950 — execution simply continues past the last `beqw`), so no separate patch site is needed.
- **Conclusion:** a single `opcode_replace` at `arcade_pc: 0x03C950` is sufficient. The dispatcher continues to fall through to the patched bytes (now `JSR hook; RTS; NOPs`), the hook runs, and execution returns to the dispatcher's caller via the RTS in the patched body.

### 4.6 Differences from stride-8 family

| Property | Stride-8 family | Default path 0x03C950 |
|----------|-----------------|------------------------|
| Write addressing mode | Indexed `A1@(2)` and `A1@(6)` | Post-increment `A1@+` (×4 per iter) plus one `A1@(2)` (fast-fill) |
| Per-iteration writes | 2 (tile-only at cells N and N+1) | 4 (tile + attr at cells N and N+1) |
| Per-iteration A1 advance | `addq.l #8, A1` (instruction) | implicit through 4× `A1@+` post-inc = +8 |
| Cell-record coverage | tile slot only of each cell | full cell record (tile + attr) for both cells |
| Loop count source | hardcoded per handler (`moveq #5/#6/#9/etc.`) | passed in via D2 (caller-supplied) |
| Path selection | per-handler (sometimes `A4@(56).b` or `A4@(1).b`) | `D6` bit 0 + `D7` zero-test + `D3` opcode tests + `0x03CA00` sentinel |
| Attribute composition | `A4@(22) + per-half D2` (constant alternating offsets) | Compose from D0 (with conditional `0x4000` OR and `A4@(39).b` byte) and from D7 (script byte ± `[0x000010]` + `A4@(22)`) |
| Tile composition | script byte + `A4@(26)` + handler-specific extras | script byte + `A4@(26)` + (`A4@(24)` if `D3==0x70`) + (`A4@(30)` for alt-attr cell from `0x03CA12`) |
| Sentinel | per-handler (`0xFF`, zero-byte, or `D3==0x50 && D4==1`) | `0xFF` only (sub-sub `0x03CA00`) |
| Reads from absolute address `0x000010` | NO | YES (alt path WRITE H — `subw 0x10, D7`) |
| Conditional secondary dispatch | NO | YES (sub-sub `0x03CA26` re-routes when `D6` bit 0 set) |

These differences mean Cody's `genesistan_hook_text_writer_3c950`
implementation **cannot share the body of any stride-8 hook**. The
shared LUT-translate-and-store helper from
`docs/design/Andy_stride8_sibling_hook_spec.md` §H8 conclusion can be
re-used (it is a generic "write a Genesis nametable word at (row,col)
and dirty the row" primitive).

### 4.7 `opcode_replace` entry template

```jsonc
{
  "arcade_pc": "0x03C950",
  "original_bytes": "<232 bytes from build/regions/maincpu.bin[0x03C950 : 0x03CA38]>",
  "replacement_bytes": "4EB9{symbol:genesistan_hook_text_writer_3c950}4E75<224 bytes of 4E71 NOP padding>",
  "note": "Route text-script dispatcher fall-through (top nibbles 0x00/0x40/0x70/0x80/0xD0/0xE0/0xF0) to Genesis FG staging hook; intercepts both A1@+ stride-2 writes and the 0x0180 fast-fill escape that previously hit PC080SN FG C-window."
}
```

Replacement length: 6 (JSR) + 2 (RTS) + 224 (112 NOPs) = 232 bytes (`0xE8`).
Equal to original_bytes length — required by `postpatch_startup_rom.py:973–977`.

`opcode_replace_count` in `specs/rastan_direct_remap.json` advances
**54 → 55**. The patcher invariant in
`tools/translation/postpatch_startup_rom.py` (which Cody previously
bumped 47 → 54 — see AGENTS_LOG entry "Cody - Implementation, stale
opcode_replace_count invariant fix") needs the corresponding bump
to 55, with `total_genesis_bytes_covered` updated to the new ROM size
(no expected change since this `opcode_replace` is equal-length).

`required_symbols` adds: `genesistan_hook_text_writer_3c950`.

---

## 5. Differences from Stride-8 Family

(Summary table reproduced in §4.6 for reference.) The single most
important implementation-affecting difference is the **stride-2 `A1@+`
write addressing mode with full cell-record coverage**: the default
path writes the *attribute* word as well as the tile word for both
cells N and N+1 of each iteration. Cody's hook MUST emit composed
Genesis nametable words for every cell touched (not skip the attribute
position as the stride-8 hooks do).

The fast-fill escape (WRITE I) is structurally similar to the stride-8
family's blank-tile sentinel, but the surrounding cell-record
semantics differ — only cell N's tile is updated, not its attribute,
and cell N+1 is skipped entirely (A1 advances by 8 with no second-cell
write).

The `subw 0x10, D7` alt-path read at `arcade_pc: 0x03C9D8` reads the
word at Genesis ROM `0x000010` (which is inside `preserved_vectors`
per `docs/design/Andy_address_map_artifact_design.md` §6). This is an
arcade-code idiosyncrasy that Cody must preserve verbatim — the hook
performs the same `subw 0x10, D7` read and uses the resulting D7 in
the WRITE H attribute composition. (The Genesis preserved-vector
content at 0x000010 is the high word of the reset vector, which is
`0x0000` for reset PC `0x00000202`. So this read effectively subtracts
zero on Genesis — but the hook MUST emit the read so behavior is
faithful and any future change to the preserved vectors is captured.)

---

## 6. Implementation Readiness

**READY FOR CODY.** All evidence proven from disassembly + address_map.
Patch span safe for single `opcode_replace`. Hook contract complete
with no design decisions remaining.

Cody work items:
1. Add hook function `genesistan_hook_text_writer_3c950` to
   `apps/rastan-direct/src/main_68k.s`. Reuse the existing
   `_store_cell` helper (or factor a private helper if not yet
   present) for the Genesis write step.
2. Add `genesistan_hook_text_writer_3c950` to `.global` in
   `main_68k.s` and to `required_symbols` in
   `specs/rastan_direct_remap.json`.
3. Add the `opcode_replace` entry from §4.7 to
   `specs/rastan_direct_remap.json`. Cody fills in `original_bytes`
   from the binary at `arcade_pc: 0x03C950 .. 0x03CA38`.
4. Bump `expectations.opcode_replace_count` from `54` to `55`.
5. Bump the patcher invariant in
   `tools/translation/postpatch_startup_rom.py` from `54` to `55`
   (`total_genesis_bytes_covered` should be unchanged since the
   replacement is equal-length to the original; if not, update it to
   the new value reported by the patcher's actual measurement).
6. Build → 30 s MAME trace → Exodus capture as Build 0035. Verify
   `fg_cwindow_live count` drops to zero (or only contains writes
   from a heretofore-unidentified writer outside the dispatcher) and
   that BlastEm no longer hard-crashes at `0xC09EA0` on boot.

---

## Open Questions

1. The exact attribute-bits-extraction pattern in step 3 of §4.4
   should match the existing `_translate_attr` helper at
   `apps/rastan-direct/src/main_68k.s:739–766` (which the existing
   hooks reuse). Cody should pass D0 through that helper for
   cell-N attributes and the D0-from-`0x03CA12` value through it for
   cell-(N+1) attributes — the helper accepts a generic 16-bit input
   and produces the Genesis attr word.
2. The trace-summary `fg_cwindow_live` field discrepancy across
   Builds 32/33/34 (open question 4 from Build 33 diagnostic) remains
   unresolved. Whether per-hook live-write watches in
   `tools/mame/genesistrace.lua` are added before or after Build 0035
   is a tooling decision; this spec does not require it for
   correctness validation since the BlastEm crash is the primary
   Build 0035 success signal.
