# Andy — Writer-PC Audit: genesis_rom_offset 0x03C516 → arcade_pc 0x03C316

**Status:** ANALYSIS COMPLETE. **Critical finding: the trace writer PCs do NOT
correspond to arcade_pc 0x03C516.** They correspond to **arcade_pc 0x03C316**
(number-renderer function at arcade_pc 0x03C2E2). Fix target changes from the
text-script inner subroutine to an entirely separate number-display function.
**Ready for Cody.**

---

## 1. Trace Evidence Confirmation — WITH CORRECTION

### 1.1 Raw trace data (confirmed)

From `build/mame/home/genesistrace/genesis_exec_trace.log`:

- Writer PCs (all `runtime_genesis_pc`): **0x03C52A, 0x03C52C, 0x03C516, 0x03C518**
- A1 = `0x00C09EA0..0x00C09EA6` → `HW_ADDRESS/PC080SN/FG_TILEMAP`
- A4 = `0x00000000`
- A0 = `0x0003C59A`
- D3 = `0x00FF`

### 1.2 Address-space resolution via address_map.json (CRITICAL)

The trace reports `runtime_genesis_pc` values. These must be resolved to
`arcade_pc` via `address_map.json` — NOT assumed to be arcade-space values.

`address_map.json` `arcade_copy` segment:
`[arcade: 0x03B0A4, 0x03EF28) → [genesis: 0x03B2A4, 0x03F128), identity_offset = 512]`

| `runtime_genesis_pc` | `arcade_pc` (from segment) | What's at this `arcade_pc` |
|----------------------|----------------------------|----------------------------|
| `0x03C516` | **`0x03C316`** | `subql #1, %a2` (inside number-renderer digit loop) |
| `0x03C518` | **`0x03C318`** | `bras 0x3C32A` (skip to loop tail) |
| `0x03C52A` | **`0x03C32A`** | `subqw #1, %d0` (loop decrement) |
| `0x03C52C` | **`0x03C32C`** | `bnes 0x3C302` (loop branch) |

**None of these correspond to arcade_pc 0x03C516 (the text-script inner
subroutine).** The inner sub at arcade_pc 0x03C516 is relocated to
genesis_rom_offset 0x03C716, which does NOT appear in the trace.

The prompt's framing assumption — "These PCs fall within the inner
subroutine at arcade_pc: 0x03C516" — was a **cross-space confusion**.
`genesis_rom_offset 0x03C516` ≠ `arcade_pc 0x03C516`. The address_map
segment lookup proves they map to arcade_pc 0x03C316.

### 1.3 `helper_5b512_rts count=0` reconciliation

Prior builds reported `helper_5b512_rts count=0`, which correctly indicated
the text-script inner sub at arcade_pc 0x03C516 (which calls
`jsr 0x5B512`) is NOT executing. This was never contradicted — the live
writer was always a different function. The apparent contradiction arose
from misidentifying `genesis_rom_offset 0x03C516` as `arcade_pc 0x03C516`.

### 1.4 A0 and A4 at trace time

- `A0 = 0x0003C59A` (genesis_rom_offset): via address_map → **`arcade_pc 0x03C39A`**. This is inside the ROM data table at arcade_pc 0x03C37C (the number-renderer's digit-display-entry table). The function loaded A0 from `lea PC@(0x3C37C), A0; adda.w D0, A0`, and at trace time A0 = `table_base + D0*10_entry_index` = `0x3C37C + 0x1E` → `0x3C39A`. Consistent with the number-renderer reading its 3rd display entry (D0_input=3 → muluw #10 → offset 30 = 0x1E).
- `A4 = 0x00000000`: the number-renderer function does NOT use or set A4. A4 is zero because the caller context (gameplay state update or score display) does not establish A4 for this function. This is expected — A4 is the text-script state pointer, which is irrelevant to the number-renderer.

---

## 2. Inner Subroutine (arcade_pc 0x03C516) — Status

For completeness: arcade_pc 0x03C516 was the private inner subroutine
of the text-script handler at arcade_pc 0x03C4D2 (hooked since Build 33).
Its genesis_rom_offset is `0x03C716` (from address_map.json). It is
**outside the 0x03C4D2 patch span** (`patched_site [arcade: 0x03C4D2,
0x03C516)` — the inner sub starts at the first byte AFTER the patch).

However, **the inner sub is confirmed dead**:
- Its only callers (`arcade_pc: 0x03C502, 0x03C50E`) were inside the
  0x03C4D2 patch span and are now NOPs.
- `helper_5b512_rts count=0` confirms it never executes (it calls
  `jsr 0x5B512` every iteration).
- **It is NOT the live crash source.** The live crash source is the
  number-renderer at arcade_pc 0x03C2E2.

---

## 3. Number-Renderer Function — Direct Caller Audit

### 3.1 Function body: arcade_pc 0x03C2E2

Source: `build/maincpu.disasm.txt:75750–75801`.

```
; ── entry ──
0x03C2E2   3E3C 0000        movew  #0, %d7                    ; D7 = 0 (attribute word for digits)
0x03C2E6   C0FC 000A        muluw  #10, %d0                   ; D0 = entry_index × 10 (table offset)
0x03C2EA   41FA 0090        lea    %pc@(0x3C37C), %a0         ; A0 = table base
0x03C2EE   D0C0             adda.w %d0, %a0                   ; A0 = &table[entry_index]
0x03C2F0   3010             movew  %a0@, %d0                  ; D0 = digit_count
0x03C2F2   2268 0002        movea.l %a0@(2), %a1              ; A1 = FG tilemap dest (arcade hw addr)
0x03C2F6   2468 0006        movea.l %a0@(6), %a2              ; A2 = source data pointer (BCD/hex byte source)
0x03C2FA   0C40 FFFF        cmpi.w #-1, %d0                   ; sentinel check
0x03C2FE   6700 0052        beqw   0x03C352                   ; → "ALL" handler if count == 0xFFFF
; ── digit loop ──
0x03C302   0800 0000        btst   #0, %d0                    ; test digit parity
0x03C306   6712             beqs   0x03C31A                    ; even → high nibble
0x03C308   1212             moveb  %a2@, %d1                  ; low-nibble path: read byte at A2
0x03C30A   0241 000F        andi.w #15, %d1                   ; mask low nibble
0x03C30E   0041 0030        ori.w  #0x30, %d1                 ; + 0x30 → ASCII '0'..'9' or ':'..'?'
0x03C312   32C7             movew  %d7, %a1@+                 ; ★ WRITE: attr word
0x03C314   32C1             movew  %d1, %a1@+                 ; ★ WRITE: tile code
0x03C316   538A             subql  #1, %a2                    ; A2-- (for alternating nibble)
0x03C318   6010             bras   0x03C32A
0x03C31A   1212             moveb  %a2@, %d1                  ; high-nibble path
0x03C31C   E809             lsr.b  #4, %d1                    ; shift high nibble down
0x03C31E   0241 000F        andi.w #15, %d1
0x03C322   0041 0030        ori.w  #0x30, %d1
0x03C326   32C7             movew  %d7, %a1@+                 ; ★ WRITE: attr word
0x03C328   32C1             movew  %d1, %a1@+                 ; ★ WRITE: tile code
0x03C32A   5340             subqw  #1, %d0                    ; decrement digit counter
0x03C32C   66D4             bnes   0x03C302
; ── leading-zero suppression ──
0x03C32E   0C50 0006        cmpi.w #6, %a0@                   ; if original count == 6 → suppress
0x03C332   661C             bnes   0x03C350
0x03C334   3010             movew  %a0@, %d0
0x03C336   2268 0002        movea.l %a0@(2), %a1
0x03C33A   3229 0002        movew  %a1@(2), %d1               ; read tile at A1+2
0x03C33E   0C41 0030        cmpi.w #0x30, %d1                 ; is it '0'?
0x03C342   660C             bnes   0x03C350                    ; if not → done
0x03C344   337C 0020 0002   movew  #0x20, %a1@(2)             ; ★ WRITE: replace '0' with space (0x20)
0x03C34A   5889             addql  #4, %a1
0x03C34C   5340             subqw  #1, %d0
0x03C34E   66EA             bnes   0x03C33A
0x03C350   4E75             rts
; ── "ALL" handler (count == 0xFFFF) ──
0x03C352   1212             moveb  %a2@, %d1
0x03C354   0241 000F        andi.w #15, %d1
0x03C358   0C01 0007        cmpi.b #7, %d1
0x03C35C   661A             bnes   0x03C378
0x03C35E   93FC 0000 0008   suba.l #8, %a1                    ; back up 2 cells (8 bytes)
0x03C364   32C7             movew  %d7, %a1@+                 ; ★ WRITE: attr
0x03C366   32FC 0041        movew  #0x41, %a1@+               ; ★ WRITE: 'A'
0x03C36A   32C7             movew  %d7, %a1@+                 ; ★ WRITE: attr
0x03C36C   32FC 004C        movew  #0x4C, %a1@+               ; ★ WRITE: 'L'
0x03C370   32C7             movew  %d7, %a1@+                 ; ★ WRITE: attr
0x03C372   32BC 004C        movew  #0x4C, %a1@                ; ★ WRITE: 'L' (no post-inc)
0x03C376   4E75             rts
; ── special single-digit re-enter ──
0x03C378   7001             moveq  #1, %d0
0x03C37A   6086             bras   0x03C302                    ; re-enter loop with D0=1
; ── table at 0x03C37C ──
```

### 3.2 All write instructions

| `arcade_pc` | Instruction | Role |
|-------------|-------------|------|
| `0x03C312` | `movew %d7, %a1@+` | digit-loop: attribute word |
| `0x03C314` | `movew %d1, %a1@+` | digit-loop: tile code (low-nibble path) |
| `0x03C326` | `movew %d7, %a1@+` | digit-loop: attribute word |
| `0x03C328` | `movew %d1, %a1@+` | digit-loop: tile code (high-nibble path) |
| `0x03C344` | `movew #0x20, %a1@(2)` | leading-zero suppression: replace '0' with space |
| `0x03C364` | `movew %d7, %a1@+` | "ALL" handler: attr for 'A' |
| `0x03C366` | `movew #0x41, %a1@+` | "ALL" handler: tile 'A' |
| `0x03C36A` | `movew %d7, %a1@+` | "ALL" handler: attr for 'L' |
| `0x03C36C` | `movew #0x4C, %a1@+` | "ALL" handler: tile 'L' (first) |
| `0x03C370` | `movew %d7, %a1@+` | "ALL" handler: attr for 'L' |
| `0x03C372` | `movew #0x4C, %a1@` | "ALL" handler: tile 'L' (second, no post-inc) |

All writes target A1, which is loaded from `arcade_pc: 0x03C2F2`
(`movea.l %a0@(2), %a1`) — a longword from the ROM display-entry table.
This longword is a `HW_ADDRESS/PC080SN/FG_TILEMAP` value (e.g.
`0x00C09EA0` from the trace).

### 3.3 Direct callers (all `bsrw 0x3C2E2` in `build/maincpu.disasm.txt`)

| # | Caller `arcade_pc` | Caller `genesis_rom_offset` | Segment kind | Status |
|---|--------------------|-----------------------------|-------------|--------|
| 1 | `0x03A546` | `0x03A746` | `arcade_copy` | **LIVE** |
| 2 | `0x03A96E` | `0x03AB6E` | `arcade_copy` | **LIVE** |
| 3 | `0x03AC60` | `0x03AE60` | `patched_site [0x03AC54, 0x03AC66)` | **DEAD** (overwritten with `bras+NOPs` by existing patch — the `bsrw` at offset 0x0C in the patch span is now `4E71 NOP`) |
| 4 | `0x03B0AC` | `0x03B2AC` | `arcade_copy` | **LIVE** |
| 5 | `0x03B426` | `0x03B626` | `arcade_copy` | **LIVE** |
| 6 | `0x03B42C` | `0x03B62C` | `arcade_copy` | **LIVE** |
| 7 | `0x03B714` | `0x03B914` | `arcade_copy` | **LIVE** |

**6 live callers, 1 dead.** All callers pass D0 as the display-entry
index. D0 selects which table entry's destination address and source
data pointer to use. The function is a **stateless number renderer**.

### 3.4 Runtime evidence explanation

- **A4 = 0**: the number-renderer function does not read or write A4.
  A4 = 0 because the calling context (gameplay/attract state update at
  arcade_pc ~0x03A5xx–0x03B7xx) has no reason to establish a text-script
  A4 state pointer. Zero is a benign side-effect.
- **A0 = genesis_rom_offset 0x03C59A = arcade_pc 0x03C39A**: this is
  `table_base + 30 = 0x03C37C + 0x1E`, corresponding to the 3rd
  display-entry (D0_input = 3). The function computed `D0 = 3 × 10 = 30`
  at `arcade_pc: 0x03C2E6` (`muluw #10, D0`), then `lea + adda.w` places
  A0 at the entry for index 3.
- **D3 = 0x00FF**: D3 is not used or set by this function. It retains
  whatever value the caller had. `0x00FF` is consistent with the
  attract-mode state machine's prior sentinel processing (0xFF terminal
  from the text-script path that fired earlier in the frame).

---

## 4. Fix Boundary Determination

The prompt's three options (A: extend 0x03C4D2 span, B: hook at
0x03C516, C: hook external callers of 0x03C516) were all framed around
arcade_pc 0x03C516 — which is NOT the crash source. After the §1
correction, only one fix makes sense.

### Option A — Extend the 0x03C4D2 patch span

**REJECTED.** The number-renderer at arcade_pc 0x03C2E2 is not contiguous
with or related to the text-script handler at arcade_pc 0x03C4D2. They
are independent functions with no shared code path (0x03C2E2 is called
via 7 `bsrw` sites from the attract-mode state machine; 0x03C4D2 is
called via the text-script dispatcher). Extending 0x03C4D2's patch span
cannot reach 0x03C2E2.

### Option B — Hook at arcade_pc 0x03C516

**REJECTED.** arcade_pc 0x03C516 is the dead text-script inner
subroutine (confirmed dead by `helper_5b512_rts count=0` and by the
address_map correction in §1.2). It is not executing. Hooking dead code
does not fix the live crash.

### Option C — Hook the live writer function directly

**SELECTED — but reframed.** The correct target is **not** "external
callers of 0x03C516" but rather the function at **arcade_pc 0x03C2E2**
(the number-renderer). A single hook at this entry point intercepts
all 6 live callers, because they all `bsrw 0x03C2E2`.

**Hook: `genesistan_hook_number_renderer_3c2e2`**

- Patch span: `arcade_pc: 0x03C2E2..0x03C37B` inclusive = **0x9A bytes (154)**.
  The ROM table at `arcade_pc: 0x03C37C` is left intact — the hook reads it
  to obtain display-entry parameters (digit count, source BCD pointer).
- The hook must convert the **destination FG tilemap address** from the
  table entry into `(row, col)` in `staged_fg_buffer` using the standard
  formula, then write translated digit tiles via the tile LUT and set
  `fg_row_dirty` bits.
- `genesis_rom_offset` of patch start: `0x03C4E2` (from address_map.json).
- All write forms (digit-loop, leading-zero suppression, "ALL" handler)
  must be replicated in the hook targeting `staged_fg_buffer`.

### Why Option C is the correct and minimal fix

1. **Single function = single hook.** All live callers reach the writer
   through one function entry point. Hooking 0x03C2E2 intercepts 100%
   of the live FG-write traffic from this function.
2. **No scope expansion required.** The function is self-contained (no
   external sub-subs beyond itself and the data table it reads).
3. **Structurally sound per Rainbow Islands strategy.** This is another
   intent class (number/score display) distinct from the text-script
   handler family. Per `docs/design/Andy_final_pc080sn_hook_strategy.md`:
   "One hook, multiple call sites, zero game-state awareness" — exactly
   what the number-renderer hook provides.

---

## 5. Implementation Readiness

**READY FOR CODY** — pending a full hook spec for
`genesistan_hook_number_renderer_3c2e2` (which should be written as a
follow-up Andy spec doc with the standard H1–H7 template). The key
parameters are already known from this audit:

| Attribute | Value |
|-----------|-------|
| Hook name | `genesistan_hook_number_renderer_3c2e2` |
| Entry `arcade_pc` | `0x03C2E2` |
| Entry `genesis_rom_offset` | `0x03C4E2` |
| Patch span (code body) | `0x03C2E2..0x03C37B` = 154 bytes |
| ROM table (NOT patched) | `arcade_pc: 0x03C37C+` (10-byte entries, index via D0 input) |
| Input register | D0 = display-entry index (0-based); all others don't-care |
| A1 source | loaded from table entry longword at offset +2 (FG tilemap hw addr) |
| A2 source | loaded from table entry longword at offset +6 (BCD data pointer) |
| Write shape | stride-4 `A1@+` (2 words: attr + tile per digit); leading-zero via `A1@(2)` indexed; "ALL" via `A1@+` sequence |
| Digit tile mapping | `0x30 + nibble` for decimal digits (arcade tile code → LUT translation to Genesis) |
| `opcode_replace_count` | 55 → **56** |
| Callers | 6 live `bsrw 0x03C2E2` sites; 1 dead (patched_site overlap) |

---

## Open Questions

1. **Full hook spec document** for `genesistan_hook_number_renderer_3c2e2`
   should be produced as a follow-up Andy prompt (standard H1–H7 format
   per the stride-8 spec template). This audit provides the necessary
   foundation but does not contain the full write-contract specification
   or the `opcode_replace` JSON template.
2. **Whether the ROM table at 0x03C37C contains any FG tilemap addresses
   in the 0xC09Exx range** should be confirmed by hex-dumping the table
   entries. The trace shows writes at `0xC09EA0..0xC09EA6` — the table
   entry at index 3 (A0 = 0x03C39A) must contain `0x00C09EA0` (or a
   value that produces that A1 address).
3. **Whether additional non-dispatcher, non-number-renderer writers
   exist** in the arcade ROM that also target FG tilemap. After Build 36
   (with this hook installed), a new trace should be checked for any
   remaining `fg_cwindow_live` writes. The PC080SN writer audit in
   `docs/design/Cody_pc080sn_writer_audit.md` should be the authoritative
   inventory for identifying further writers.
