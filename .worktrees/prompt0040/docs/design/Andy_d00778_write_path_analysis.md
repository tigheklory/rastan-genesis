# Andy — D00778 Write Path Analysis

**Agent:** Andy
**Type:** Static Analysis / Classification Research (no implementation)
**Build context:** `rastan-direct` Build 0052
**Architecture compliance:** CONFIRMED (no source / spec / tool modifications).

**Outcome:** The write at `arcade_pc 0x03ADAA` is **arcade PC090OJ sprite-table initialization**. `A0 = HW_ADDRESS 0x00D00778` is a byte offset 0x778 into the arcade PC090OJ sprite-RAM region (`0x00D00000..0x00D03FFF`). The write is part of a **structured sprite-descriptor initialization loop** (14+3 entries × 8 bytes each) emitted from the function at `arcade_pc 0x03AD72`, which is called from `arcade_pc 0x03AF28` inside arcade startup_common, directly before the BG tilemap fill at `arcade_pc 0x03AF38`. The write is **currently UNHANDLED** by the opcode_replace layer: no spec entry covers `arcade_pc 0x03ADAA` and no entry generally covers writes to the `0x00D00000..0x00D03FFF` region (other than `arcade_pc 0x03AE06` / `0x03AE1E` which specifically suppress the DMA-trigger register at `0x00D01BFE`, not ordinary sprite-RAM writes). The related longword-fill primitive at `arcade_pc 0x03AD44` is hooked to `genesistan_hook_tilemap_bg_fill`, but that helper's range check restricts it to `0x00C00000..0x00C04000` and silently drops sprite-RAM targets. **No fix is proposed — classification only per Rule 16.**

---

## Address-space legend

- `arcade_pc` — PC in arcade ROM address space.
- `HW_ADDRESS 0x00D00000..0x00D03FFF` — arcade **PC090OJ sprite RAM** region on the Taito F2 / Rastan board. On Genesis this address falls outside cart-ROM (ROM ends at `0x0FC1C3`), outside VDP port band (`0x00C00000..0x00C0001F`), outside I/O band (`0x00A10000..0x00A1001F`), outside Z80 band (`0x00A00000..0x00A0FFFF`), and outside WRAM (`0x00FF0000..0x00FFFFFF`) — it is **unmapped on Genesis**. BlastEm halts on writes to this region; Exodus tolerates them (confirmed in [Cody_d00778_vs_delay_loop_ordering_trace.md](docs/design/Cody_d00778_vs_delay_loop_ordering_trace.md) Phase 1 context).
- `runtime_genesis_pc = arcade_pc + 0x200` for arcade ROM code (whole-maincpu-relocation).

---

## Phase 1 — Disassembly of primary write region (`arcade_pc 0x03AD8E..0x03ADAE`)

From [build/maincpu.disasm.txt](build/maincpu.disasm.txt) lines 73910-73924, cross-verified against [build/regions/maincpu.bin](build/regions/maincpu.bin).

### Region disassembly

| arcade_pc | bytes                   | instruction                         | role |
| --------- | ----------------------- | ----------------------------------- | ---- |
| `0x3AD84` | `72 0E`                 | `moveq #14, %d1`                    | outer loop count = 14 iterations |
| `0x3AD86` | `41 F9 00 D0 07 78`     | `lea 0x00D00778, %a0`               | **A0 = HW_ADDRESS 0x00D00778** — arcade PC090OJ sprite RAM offset 0x778 |
| `0x3AD8C` | `20 3C 00 00 00 08`     | `movel #8, %d0`                     | D0 = 0x00000008 — initial "incrementing field" value |
| `0x3AD92` | `2E 3C 00 00 01 60`     | `movel #352, %d7`                   | D7 = 0x00000160 (= 352 decimal) — constant "fixed field" value |
| `0x3AD98` | `4E B9 00 05 B5 12`     | `jsr 0x05B512`                      | call helper at `arcade_pc 0x05B512` (see Phase 3 — effectively a no-op) |
| `0x3AD9E` | `61 00 00 0A`           | `bsrw 0x03ADAA`                     | call the loop body at `0x03ADAA` as a subroutine; push return address `0x03ADA2`. This runs the first 14 iterations. |
| `0x3ADA2` | `72 03`                 | `moveq #3, %d1`                     | (reached after the BSR above returns) reset D1 = 3 for a second pass |
| `0x3ADA4` | `20 3C 00 00 00 C8`     | `movel #200, %d0`                   | D0 = 0x000000C8 (= 200 decimal) — reset incrementing field |
| `0x3ADAA` | `20 80`                 | `movel %d0, %a0@`                   | **THE WRITE.** `*A0 = D0` — on iter 1, writes `0x00000008` to `HW_ADDRESS 0x00D00778` |
| `0x3ADAC` | `21 47 00 04`           | `movel %d7, %a0@(4)`                | `*(A0+4) = D7` — writes `0x00000160` to `HW_ADDRESS 0x00D0077C` |
| `0x3ADB0` | `50 88`                 | `addql #8, %a0`                     | A0 += 8 (advance to next 8-byte entry) |
| `0x3ADB2` | `06 40 00 10`           | `addiw #16, %d0`                    | D0 += 16 (word-sized add) — "field 1" increments by 16 per entry |
| `0x3ADB6` | `53 41`                 | `subqw #1, %d1`                     | D1-- |
| `0x3ADB8` | `66 F0`                 | `bnes 0x03ADAA`                     | loop back while D1 != 0 |
| `0x3ADBA` | `4E 75`                 | `rts`                               | **function exit** — pops return address and resumes at caller |

### Function boundary

Walking backward past `0x03AD72` confirms a preceding RTS at `0x3AD70`:

```
arcade_pc 0x3AD70:  4e75                   rts                              ← end of PRECEDING function (at 0x03AD4C)
arcade_pc 0x3AD72:  32 3c 01 e0            movew #480, %d1                  ← ENTRY of function containing 0x3AD84 / 0x3ADAA
arcade_pc 0x3AD76:  41 f9 00 d0 00 00      lea 0x00D00000, %a0              ← A0 = PC090OJ sprite RAM base
arcade_pc 0x3AD7C:  20 3c 00 00 01 00      movel #256, %d0                  ← D0 = 0x00000100 = sprite-init pattern
arcade_pc 0x3AD82:  61 c0                  bsrs 0x03AD44                    ← longword-fill: 480 longs × 4B = 1920 B (0x780) at 0x00D00000..0x00D00780 filled with 0x00000100
arcade_pc 0x3AD84..0x3ADBA:                                                 ← sprite-table structured init (analysed above)
arcade_pc 0x3ADBA:  4e 75                  rts                              ← FUNCTION EXIT for this segment
```

- **Function entry:** `arcade_pc 0x03AD72`
- **Function exit:** `arcade_pc 0x03ADBA` (the final RTS after the second structured-init loop)
- **Inner BSR-as-loop entry:** `arcade_pc 0x03ADAA` (called as a subroutine from `0x3AD9E` with D1=14 and again reached by fall-through at `0x3ADA2→0x3ADAA` with D1=3)

### Static reconciliation of trace's 5-PC chain

Cody's 5 trace PCs (per [Cody_d00778_vs_delay_loop_ordering_trace.md](docs/design/Cody_d00778_vs_delay_loop_ordering_trace.md) Phase 3) are observed at the +2 prefetch offset used by MAME. Applied to the arcade_pc column:

| rel seq | reported arcade_pc | actual-instruction arcade_pc (−2) | matches disassembly? | actual mnemonic |
| ------- | ------------------ | --------------------------------- | -------------------- | --------------- |
| −5 | `0x03AD8E` | `0x03AD8C` | YES | `movel #8, %d0` (4/6-byte immediate — the initial D0=8 load) |
| −4 | `0x03AD94` | `0x03AD92` | YES | `movel #352, %d7` (D7=352) |
| −3 | `0x03AD9A` | `0x03AD98` | YES | `jsr 0x05B512` (helper call) |
| −2 | `0x05B514` | `0x05B512` | YES | helper entry — two RTS bytes (see Phase 3) |
| −1 | `0x03ADA0` | `0x03AD9E` | YES | `bsrw 0x03ADAA` (call the loop subroutine) |

All 5 trace PCs reconcile cleanly with the disassembly at the uniform `−2` prefetch offset. The CPU then enters the loop at `0x03ADAA` and the watchpoint fires on the first `movel %d0, %a0@` store.

---

## Phase 2 — Caller context

### Stack frames at the watchpoint hit

From [Cody_d00778_vs_delay_loop_ordering_trace.md](docs/design/Cody_d00778_vs_delay_loop_ordering_trace.md) Phase 3:

- `[SP+0x00] = 0x0003AFA2` → `arcade_pc 0x03ADA2`
- `[SP+0x04] = 0x0003B12C` → `arcade_pc 0x03AF2C`

`[SP]` is the return address from the `bsrw 0x03ADAA` at `0x3AD9E` (pushes `PC+4 = 0x3ADA2`). This confirms we are currently one subroutine-level deep inside the function at `0x03AD72`.

`[SP+4]` is one frame up — the return address that the outer caller pushed onto the stack when it invoked the function at `0x03AD72`. Converting: `0x0003B12C → arcade_pc 0x03AF2C`.

### Disassembly around `arcade_pc 0x03AF20..0x03AF3C`

From [build/maincpu.disasm.txt:74020-74026](build/maincpu.disasm.txt):

```
3af1e: 33 c0 00 38 00 00      movew %d0, 0x00380000           (TC0040IOC watchdog write; suppressed by Phase A entry at 0x03AF1E)
3af24: 3b 40 00 14            movew %d0, %a5@(20)             (WRAM write)
3af28: 61 00 fe 48            bsrw 0x03AD72                    ← CALLS THE FUNCTION CONTAINING D00778
3af2c: 41 f9 00 c0 00 00      lea 0x00C00000, %a0             (BG tilemap base — [SP+4] return address points here)
3af32: 32 3c 10 00            movew #4096, %d1
3af36: 70 20                  moveq #32, %d0
3af38: 61 00 fe 0a            bsrw 0x03AD44                    (longword fill — hooked to genesistan_hook_tilemap_bg_fill)
```

- **Instruction at `0x03AF28`:** `bsrw 0x03AD72` — Branch-to-Subroutine Word. Pushes return address `0x3AF2C` and jumps to `0x03AD72`.
- **Role:** invokes the PC090OJ sprite-table init function from inside startup_common.
- **Instruction at `0x03AF2C`:** `lea 0x00C00000, %a0` — the next BG tilemap fill preparation (not itself the caller; it's merely the return target).

### Enclosing function of `arcade_pc 0x03AF28`

From prior forensic work ([Andy_p1_p2_prerequisite_verification.md](docs/design/Andy_p1_p2_prerequisite_verification.md) Phase 1, [Andy_interrupt_enable_timing.md](docs/design/Andy_interrupt_enable_timing.md) Phase 4): the function reached from the cold-boot chain `ROM[0x0004] → 0x3A000 → BRA.W 0x3AE86` is **arcade startup_common body**. The instruction at `0x03AF28` is well inside that body (between `0x03AE86` startup_common entry and `0x03B07A` the interrupt-enable site).

```
Enclosing function of 0x03AF28:             arcade startup_common body at arcade_pc 0x03AE86
Static caller chain:
  CPU reset / ROM[0x0004]
    → arcade_pc 0x03A000: BRA.W 0x03AE86
    → arcade_pc 0x03AE86 (startup_common body entry)
    → ... init sequence ...
    → arcade_pc 0x03AF28: bsrw 0x03AD72           ← BSR into sprite-init function
    → arcade_pc 0x03AD72 (function entry)
    → arcade_pc 0x03AD84..0x03ADBA (structured sprite-table init)
    → arcade_pc 0x03ADAA: movel %d0, %a0@         ← THE WRITE (first iteration of outer 14-loop)
Arcade phase:                                cold boot, startup_common body
                                             (pre-interrupt-enable per Build 0052 post-fix ordering;
                                              IMASK=7 when this executes after the boot.s:160 deletion).
```

---

## Phase 3 — Helper function analysis at `arcade_pc 0x05B512`

Trace's seq −2 was `0x05B514` (reported, i.e. `0x05B512` at −2 offset). Disassembly shows this region is a **data table, not code** — the disassembler parses the data bytes as pseudo-instructions.

Raw bytes at [build/maincpu.disasm.txt:114972](build/maincpu.disasm.txt) (line shown with objdump's attempt at instruction parsing):

```
5b510: 00 ad 4e 75 4e 75 ff ff
5b518: 00 04 00 04 00 04 00 04
5b520: 00 04 00 04 00 04 00 04
5b528: 00 03 00 03 00 03 00 03
5b530: 00 03 00 03 00 03 00 03
...
```

Byte-level interpretation at `arcade_pc 0x05B512`:

```
arcade_pc 0x05B512:  4E 75                  → RTS  (opcode 4E75 is unconditionally return-from-subroutine)
arcade_pc 0x05B514:  4E 75                  → RTS
arcade_pc 0x05B516:  FF FF                  → data / padding
arcade_pc 0x05B518..:                         → 16-bit data words (`0x0004`, `0x0003`, `0x0002`, `0x0001` repeating) — a numeric table, not code
```

The bytes `4E 75` at `0x05B512` are **opcode-equivalent to RTS**. Whether placed deliberately as a stub (common arcade-ROM pattern for "optional-callback slot defaults to no-op") or incidentally as data bytes that happen to match RTS, the run-time effect of `jsr 0x05B512` is:

1. JSR pushes return address `0x3AD9E` (= PC+4 from `arcade_pc 0x03AD98`) onto the stack.
2. Jump to `arcade_pc 0x05B512`.
3. Execute `RTS`.
4. RTS pops the pushed return address → resume at `arcade_pc 0x03AD9E` (the `bsrw 0x03ADAA` instruction).

**Net effect: the helper is an immediate-return no-op.** It does not compute or alter D0, D7, A0, or any operand used by the subsequent D00778 write. It contributes no logic to the write path.

### Function boundaries

The helper at `0x05B512` has effectively zero body (one RTS instruction at entry). No epilogue to trace. Analysing the surrounding data region for completeness:

- `0x05B4F0..0x05B511`: byte pattern `00 AD` repeating — looks like a table of byte values (each `00 AD` = 173 decimal) or the tail of a prior table.
- `0x05B512..0x05B515`: `4E 75 4E 75` — two RTS bytes, interpretable as the stub.
- `0x05B516..0x05B517`: `FF FF` — table terminator or gap.
- `0x05B518..`: `0004` / `0003` / `0002` / `0001` sequences — a numeric table with decreasing values (likely a lookup / LFO / animation curve).

No structural code around `0x05B512` beyond the two RTS bytes. The helper is classified as a **stub / optional-callback slot**.

### Relationship to the D00778 write value

The helper does not compute the D0 value written at `0x03ADAA` (D0 is unaffected — the RTS preserves registers by convention, and inspection of the two RTS bytes confirms no register write). The constants D0=8 and D7=352 are set by the caller at `0x03AD8C` / `0x03AD92` BEFORE the JSR, and they flow through the JSR unchanged to the loop body at `0x03ADAA`.

```
Helper entry:                    arcade_pc 0x05B512
Helper exit:                      arcade_pc 0x05B512 (same instruction; RTS returns immediately)
Helper body size:                 2 bytes (`4E 75` = RTS)
Helper classification:             stub / optional-callback slot with no behaviour
Effect on D00778 write:            none — operand registers pass through unchanged
Reach mechanism:                   JSR `0x05B512` at arcade_pc 0x03AD98; JSR pushes return, jumps, RTS pops, resumes
```

---

## Phase 4 — Related fill primitive at `arcade_pc 0x03AD40..0x03AD60`

### Disassembly

From [build/maincpu.disasm.txt:73891-73905](build/maincpu.disasm.txt):

```
arcade_pc 0x03AD3C (word-fill primitive entry — preceding function):
  ...
  0x3AD40: 66 fa                  bnes 0x03AD3C                       ← loop back
  0x3AD42: 4e 75                  rts                                 ← END of WORD-fill primitive

arcade_pc 0x03AD44 (LONGWORD-fill primitive entry):
  0x3AD44: 20 c0                  movel %d0, %a0@+                    ← store D0, A0 += 4
  0x3AD46: 53 41                  subqw #1, %d1                        ← D1--
  0x3AD48: 66 fa                  bnes 0x03AD44                       ← loop while D1 != 0
  0x3AD4A: 4e 75                  rts                                 ← END of LONGWORD-fill primitive
```

**Shape:** pure longword memset. Caller sets A0 (dest), D1 (count), D0 (value), BSR/JSRs to `0x03AD44`, which writes D0 to (A0)+ for D1 iterations, then RTS.

### Callers of `arcade_pc 0x03AD44` adjacent to this path

From [build/maincpu.disasm.txt:73897-73914](build/maincpu.disasm.txt):

```
arcade_pc 0x03AD4C (FIRST FUNCTION — separate from the D00778 function; this one is at 0x03AD4C..0x03AD70):
  0x3AD4C: movew #8,    %d1                           ← D1 = 8
  0x3AD50: lea 0x00D00000, %a0                        ← A0 = PC090OJ base
  0x3AD56: movel #256, %d0                             ← D0 = 0x00000100
  0x3AD5C: bsrs 0x03AD44                              ← fill 8 longwords at 0x00D00000..0x00D0001F with 0x00000100
  0x3AD5E: movew #386, %d1                             ← D1 = 386
  0x3AD62: lea 0x00D00170, %a0                        ← A0 = 0x00D00170
  0x3AD68: movel #256, %d0                             ← D0 = 0x00000100
  0x3AD6E: bsrs 0x03AD44                              ← fill 386 longwords at 0x00D00170..0x00D00778 with 0x00000100
                                                      ← NOTE: 0x00D00170 + 386*4 = 0x00D00170 + 0x608 = 0x00D00778 ⟵ exactly where the next function writes
  0x3AD70: rts                                         ← function exit (0x03AD4C..0x03AD70)

arcade_pc 0x03AD72 (SECOND FUNCTION — the one containing the D00778 write):
  0x3AD72: movew #480, %d1                            ← D1 = 480
  0x3AD76: lea 0x00D00000, %a0                        ← A0 = PC090OJ base
  0x3AD7C: movel #256, %d0                             ← D0 = 0x00000100
  0x3AD82: bsrs 0x03AD44                              ← fill 480 longwords at 0x00D00000..0x00D00780 with 0x00000100
                                                      ← NOTE: 480*4 = 1920 = 0x780 → ends at 0x00D00780 (just past 0x00D00778)
  0x3AD84..0x03ADBA:                                   ← structured sprite-table init overwrites portions of the pre-filled region
```

Both functions at `0x03AD4C` and `0x03AD72` pre-fill spans of PC090OJ sprite RAM with the constant `0x00000100` via `0x03AD44`, then the second function overwrites specific sprite entries starting at `0x00D00778` with structured data.

**The D00778 write at `arcade_pc 0x03ADAA` is NOT inside the fill primitive at `0x03AD44`.** It is a separate, more complex write loop inside the caller function at `0x03AD72`. The only relationship is:

- Fill primitive `0x03AD44` pre-populates `0x00D00000..0x00D00780` with `0x00000100` at `0x03AD82`.
- Structured init at `0x03ADAA` then overwrites `0x00D00778..` with (incrementing, constant) 8-byte pairs.

```
Fill primitive `0x03AD44`:           pure longword memset (movel D0, (A0)+; subqw D1; bnes; rts).
Is the D00778 write inside this?:    NO. The write at 0x03ADAA is in a separate loop in the caller
                                     function at 0x03AD72, not inside 0x03AD44.
Intended fill target at preceding   0x00D00000..0x00D00780 with longword value 0x00000100
call (0x03AD82):                    (480 × 4 bytes = 0x780 bytes).
```

---

## Phase 5 — Spec cross-reference

Searched [specs/rastan_direct_remap.json](specs/rastan_direct_remap.json) for entries in or near the regions analysed (with commentary on each):

| arcade_pc  | spec role                                                  | relevant to D00778 path? | note |
| ---------- | ---------------------------------------------------------- | ------------------------ | ---- |
| `0x03AD44` | opcode_replace: BSR-target redirected to `genesistan_hook_tilemap_bg_fill` | **INDIRECTLY** — same fill primitive is invoked from both the PC090OJ init function (calls at `0x03AD5C`, `0x03AD6E`, `0x03AD82`) and the PC080SN BG tilemap fill in startup_common (call at `0x03AF38`). The hook's body (analysed in [Andy_p1_p2_prerequisite_verification.md](docs/design/Andy_p1_p2_prerequisite_verification.md) §Note 2 of Phase 1) has an explicit range check that rejects A0 outside `[0xC00000, 0xC04000)`. For PC090OJ targets (`A0 = 0xD00000+`), the hook silently drops the writes. **Effect:** the pre-fills of `0x00D00000..0x00D00780` at `0x03AD5C/0x03AD6E/0x03AD82` are currently no-ops on Genesis; the sprite RAM never gets the `0x00000100` pattern the arcade expects. |
| `0x03ADFE` | opcode_replace: suppress `movew #0, 0x00C50000` (PC080SN screen-flip) | NO | Unrelated — targets PC080SN chip, not PC090OJ. |
| `0x03AE06` | opcode_replace: suppress `movew #0, 0x00D01BFE` (PC090OJ sprite-DMA trigger) | NO (different register) | Targets the DMA-start register at `0x00D01BFE`, not sprite RAM at `0x00D00778`. Conceptually sibling, but a different specific register role. |
| `0x03AE16` | opcode_replace: suppress `movew #0, 0x00C50000` | NO | Unrelated. |
| `0x03AE1E` | opcode_replace: suppress `movew #0, 0x00D01BFE` | NO (different register) | Same register as `0x03AE06`. |
| `0x03AE86` | opcode_replace: suppress `movew #0, 0x00C50000` (PC080SN flip, startup) | NO | Unrelated. |
| `0x03AE8E` | opcode_replace: suppress `movew #0, 0x00D01BFE` (PC090OJ DMA trigger, startup) | NO (different register) | Same category. |
| `0x03AD8A` / `0x03AD86` / `0x03ADAA` / etc. | **NO ENTRIES** | — | **No opcode_replace entry covers the LEA at `0x03AD86` (which loads `A0 = 0x00D00778`), the write at `0x03ADAA`, or any structured sprite-table init instruction in the `0x03AD8x..0x03ADBA` range.** |
| Any region-level rule for `0x00D00000..0x00D03FFF` sprite RAM | **NONE** | — | The spec has no generic rule that translates arbitrary writes to arcade PC090OJ sprite RAM. Only the specific DMA-trigger register writes are suppressed (at `0x03AE06` and `0x03AE1E`). |

### Outcome: is the D00778 path partially / fully translated?

- Writes via `0x03AD44` fill primitive to PC090OJ sprite RAM: **DROPPED** by the hook's range check. Arcade-intended pattern `0x00000100` never reaches a Genesis-side destination.
- Direct write at `0x03ADAA` (`movel %d0, %a0@` with `A0 = 0x00D00778`): **UNHANDLED** — no opcode_replace covers it. Goes to unmapped Genesis memory.
- Direct write at `0x03ADAC` (`movel %d7, %a0@(4)` — the fixed-field `0x00000160` to offset +4 of each sprite entry): **UNHANDLED**.
- Subsequent iterations (D1 = 14 then 3): all **UNHANDLED**.

```
Existing Genesis translation status for the D00778 path:  UNHANDLED
  - Predecessor fill-primitive calls are hooked but range-gated out (silently dropped).
  - The direct structured-init writes at 0x03ADAA..0x03ADAC are not covered by
    any opcode_replace entry.
  - The sprite-RAM destination region 0x00D00000..0x00D03FFF has no generic
    translation rule.
```

---

## Phase 6 — Classification

Based on Phases 1-5 evidence:

```
Subsystem:                            sprite (arcade PC090OJ sprite-table initialization)
Arcade hardware target:               PC090OJ (Taito F2 sprite chip)
  Address 0x00D00778 interpretation:  byte offset 0x778 into arcade PC090OJ sprite-RAM region
                                      (region 0x00D00000..0x00D03FFF = 16 KB). Arcade PC090OJ
                                      typically uses 16-byte sprite entries (4 words: Y, code,
                                      X, attribute). 0x778 / 16 = 0x77 = sprite index 119 under
                                      that layout. Alternatively, if the pair-write pattern
                                      (8-byte pairs written at 0x03ADAA..0x03ADAC) uses a
                                      smaller stride, it may be writing half-sprite records.
                                      Precise stride is out of scope for this classification —
                                      the key fact is the region is sprite RAM.
Operation type:                       structured sprite-descriptor initialization loop
  - outer setup: D1=14, D0=8, D7=352 (0x160), A0=0x00D00778
  - BSR to inner loop; inner loop iterates 14 times writing (D0, D7) as two
    longwords per entry, D0 += 16 per iteration, A0 += 8 per iteration
  - outer reset: D1=3, D0=200, continue with same inner loop for 3 more iterations
  - total: 14 + 3 = 17 entries × 8 bytes = 136 bytes written into sprite RAM
    starting at 0x00D00778
  - constant "field 2" = D7 = 0x00000160 across all 17 entries; "field 1" =
    D0 starts at 0x8 (first 14 entries) and restarts at 0x200 (next 3 entries),
    incrementing by 16 each iteration.
Relationship to rendering:
  Required for correct state:         YES (arcade's own sprite subsystem depends on the arcade-
                                      initialised sprite table contents for subsequent sprite
                                      renders to be coherent).
  Required for visible output:        INDIRECTLY YES — arcade expects sprite RAM to contain these
                                      initialised descriptors before gameplay begins. If the
                                      descriptors never arrive on Genesis, arcade's subsequent
                                      sprite update paths may behave unpredictably against empty
                                      or default sprite state.
Existing Genesis translation status:  UNHANDLED
  - No spec entry covers arcade_pc 0x03ADAA or the surrounding structured-init instructions.
  - Related pre-fills via arcade_pc 0x03AD44 reach PC090OJ but are silently dropped by the
    existing genesistan_hook_tilemap_bg_fill range check.
  - DMA-trigger writes at arcade_pc 0x00D01BFE are suppressed via opcode_replace at
    0x03AE06 / 0x03AE1E — a different register role from the sprite-RAM writes here.
  - Genesis sprite rendering uses a completely different mechanism (VDP Sprite Attribute
    Table + DMA from WRAM SAT staging), so the arcade PC090OJ sprite-table bytes do not
    translate 1:1 to a Genesis memory region. Any future translation will require a
    genesistan_hook_pc090oj_* helper that rewrites arcade sprite descriptors into
    Genesis SAT entries — outside the scope of this classification task per Rule 16.
```

---

## Phase 7 — Secondary context (limited scope, one paragraph)

Current Build 0052 VRAM initialisation is handled by Genesis-side bootstrap (`_bootstrap_clear_staging` clears `staged_bg_buffer`, `staged_fg_buffer`, Plane A nametable VRAM) and by `load_scene_tiles` (uploads title scene tile patterns to VRAM). Current Build 0052 palette loading is **not yet active in the runtime trace window** — palettes are staged into `staged_palette_words` at 0x00 during boot and never committed in the 5-second window because `palette_dirty` is never set by any arcade hook running in that window. **VRAM/palette relevance to the D00778 write path: INDIRECT.** The D00778 path is **sprite-subsystem specific** (PC090OJ sprite RAM) and does not interact with VRAM tile data or CRAM palette entries directly. Any Genesis-side translation of the D00778 path will eventually need to populate Genesis SAT (stored in VRAM, separate from tile data) based on the arcade sprite descriptors, but that translation is a standalone sprite-hook design problem — not a VRAM/palette problem. No cross-dependency exists that would require a coupled VRAM/palette fix to precede sprite translation.

---

## Phase 8 — Integrity

- All specified regions disassembled and analysed: **YES** — Phase 1 (primary write region `0x03AD8E..0x03ADAE` and function body `0x03AD72..0x03ADBA`), Phase 2 (caller context `0x03AF20..0x03AF3C`), Phase 3 (helper region `0x05B500..0x05B540`), Phase 4 (fill primitive `0x03AD40..0x03AD60`).
- 5-PC trace reconciled with disassembly: **YES** — uniform `−2` prefetch offset, 5/5 PCs matched against static disassembly.
- Spec cross-reference complete: **YES** — all relevant entries enumerated with relevance classification.
- Classification supported by cited evidence: **YES** — each classification dimension cites specific disassembly line(s), spec entries, or known arcade hardware map.
- No source / spec / tool modifications: **YES**.
- STOP triggered: **NO**.

---

## Summary

```
Primary write site analyzed:             YES
Caller context identified:               YES (bsrw 0x03AD72 at arcade_pc 0x03AF28 inside startup_common)
Helper function analyzed:                YES (arcade_pc 0x05B512 is a stub/no-op; two RTS bytes)
Fill primitive analyzed:                 YES (arcade_pc 0x03AD44 is a longword memset; D00778 write is
                                         NOT inside it — it's in a separate structured-init loop)
Spec entries found:                      8 related (0x03AD44, 0x03ADFE, 0x03AE06, 0x03AE16, 0x03AE1E,
                                         0x03AE86, 0x03AE8E), zero cover the specific D00778 write path
Subsystem classification:                sprite (arcade PC090OJ sprite-table initialisation)
Arcade hardware target:                  PC090OJ (Taito F2 sprite chip;
                                         sprite-RAM region 0x00D00000..0x00D03FFF)
Operation type:                          structured sprite-descriptor initialisation loop
                                         (14 + 3 = 17 × 8-byte entries at 0x00D00778..0x00D00800)
Address 0x00D00778 interpretation:        byte offset 0x778 into arcade PC090OJ sprite RAM;
                                         sprite-table slot in the middle of the sprite-descriptor area
Existing Genesis translation status:      UNHANDLED (no opcode_replace covers 0x03ADAA;
                                         related pre-fills via 0x03AD44 are silently dropped by
                                         the existing tilemap-fill hook's range check)
VRAM/palette relevance:                  INDIRECT (sprite subsystem is orthogonal to VRAM/palette
                                         in terms of fix scope; Genesis SAT translation is a separate
                                         sprite-hook design problem, not a VRAM/palette coupling)
STOP triggered:                          NO
```
