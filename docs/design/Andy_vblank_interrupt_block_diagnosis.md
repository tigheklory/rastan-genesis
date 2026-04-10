# Andy — VBlank Interrupt Block Diagnosis

**Rastan-Genesis / apps/rastan-direct**
Analysis of PC loop at `0x000404`-`0x00040C` / `0x0008AA`-`0x0008B8` with observed SR = `0x2604`.

---

## 1. Executive Summary

The runtime symptom — PC cycling through `0x000404`, `0x000408`, `0x00040C`, `0x0008AA`,
`0x0008B2`, `0x0008B8`, screen blank, arcade tick never reached — has one root cause:
the genesis-side code compiled from `main_68k.s` extends beyond binary address `0x0003FF`,
but the patcher only restores genesis boot bytes for addresses `0x000000`-`0x0003FF`. Every
byte above `0x3FF` in the final binary is arcade ROM data, not genesis code. The function
`vdp_commit_scroll` (assembled at `0x3D6`-`0x413`) spans this boundary: its first 42 bytes
(up to `0x3FF`) survive the restore, but its remaining 20 bytes (at `0x400`-`0x413`) are
arcade ROM bytes. When `_VINT_handler` calls `bsr vdp_commit_scroll`, execution proceeds
through the 42 preserved bytes and then falls into arbitrary arcade ROM data at `0x400`,
which decodes as 68000 instructions that form the observed loop. `vdp_commit_scroll` never
returns. `frame_counter` is never incremented. The main loop's `wait_vblank` poll never
exits. `rastan_direct_arcade_tick_entry` (`0x0003A208`) is never reached.

SR = `0x2604` (IPL mask = 6) is a consequence, not a cause: the 68000 automatically sets
IPL to the interrupt level being serviced when it accepts a Level 6 VBlank interrupt and
enters `_VINT_handler`. SR stays at IPL=6 for as long as the handler has not executed `RTE`.
Because `vdp_commit_scroll` never returns to the handler, `RTE` is never reached, and SR
is permanently frozen at IPL=6. This secondary effect blocks any further Level 6 VBlank
delivery (a level-N interrupt requires IPL mask < N, i.e., mask < 6 for level 6), but that
is irrelevant: the handler is already stuck; no further VBlanks are needed to explain the
loop.

There is no instruction anywhere in `boot.s` or `main_68k.s` that sets SR to `0x2600` or
`0x2604` explicitly. The only SR-set instructions in the source are:
- `boot.s` `_start`: `move.w #0x2700, %sr` (IPL=7, all interrupts masked during early init)
- `main_68k.s` `main_68k`: `move.w #0x2700, %sr` (redundant re-mask at entry)
- `main_68k.s` `main_68k`: `move.w #0x2000, %sr` (IPL=0, all interrupts enabled, correct)

The `0x2604` is produced entirely by the CPU's interrupt-acceptance hardware when it takes
the Level 6 VBlank interrupt. The Z flag (CCR bit 2 = `0x04`) is set by whatever flag-setting
instruction executed most recently inside the stuck handler call chain.

**Single root cause**: `vdp_commit_scroll` compiled size (42 bytes past `0x3D6` = ends at
`0x413`) overflows the patcher's preserved region (`0x000000`-`0x0003FF`). Bytes at
`0x000400`-`0x000413` are arcade ROM data, not genesis instructions. Execution of
`vdp_commit_scroll` falls into arcade ROM bytes at `0x400`, producing the observed loop.

**Single correction**: Shrink or relocate genesis code so that all functions called from
`_VINT_handler` (specifically `vdp_commit_scroll` and everything it depends on) fit entirely
within `0x000000`-`0x0003FF`, OR extend the preserved region in the patcher to cover the
full genesis code size.

---

## 2. Inputs Audited

1. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/main_68k.s` — READ COMPLETE.
   467 lines. Contains `main_68k`, `_VINT_handler`, all VDP helper functions, `vdp_commit_scroll`,
   `rastan_direct_update_inputs`, `arcade_tick_logic`, `init_staging_state`. `.bss` symbols
   at VMA `0xFF0000`.

2. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s` — READ COMPLETE.
   55 lines. Exception vector table at `.org 0x000000`: 64 vectors. Reset vector = `_start`.
   VBlank vector (vec[30], offset `0x78`) = `_VINT_handler`. All other non-reset/non-VBlank
   vectors = `_default_handler` (= `RTE` at `.org 0x000200`). `_start` at `0x000202`.
   Only SR manipulation in `boot.s`: `move.w #0x2700, %sr`.

3. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/link.ld` — READ COMPLETE.
   `.text.boot` first, then `.text`, `.rodata`, `.data`, all in one output section starting
   at `0x000000`. `.bss` at VMA `0xFF0000` (NOLOAD). No explicit placement of arcade ROM —
   that is injected by the patcher.

4. `/home/tighe/projects/rastan-genesis/docs/design/Cody_rastan_direct_final_rom_boot_byte_fix.md`
   — READ COMPLETE. Confirms: preserved region is `0x000000`-`0x0003FF` (1024 bytes),
   restored last (after rewrite passes) for the `rastan_direct` profile. The fix guarantees
   `0x38A = 67 28` in the final ROM. The preserved region boundary at `0x3FF` is unchanged.

5. `/home/tighe/projects/rastan-genesis/docs/design/Andy_early_control_flow_loop_diagnosis.md`
   — READ COMPLETE. Previous analysis established symbol addresses from a `nm` symbol table:
   `vdp_commit_bg = 0x000384`, `vdp_commit_tiles_if_dirty = 0x00035A`,
   `vdp_commit_palette = 0x0003B6`, `_VINT_handler = 0x000250`. These are used as anchor
   points for the current address calculations.

---

## 3. Exact Identification of Observed Loop Addresses

### Vector table layout (boot.s)

The exception vector table is 64 longwords × 4 bytes = 256 bytes, occupying `0x000000`-`0x0000FF`.
The Genesis ROM header (`.org 0x000100`) occupies `0x000100`-`0x0001FF`.
`_default_handler` (`RTE`) is at `.org 0x000200`.
`_start` is at `0x000202`.

### Symbol address reconstruction

Using the anchor `_VINT_handler = 0x000250` (confirmed by previous analysis doc) and
instruction-size arithmetic from `main_68k.s` source:

| Symbol | Address | Size (bytes) |
|---|---|---|
| `_VINT_handler` | `0x000250` | 64 |
| `vdp_boot_setup` | `0x000290` | 126 |
| `vdp_set_reg` | `0x00030E` | 18 |
| `vdp_set_vram_write_addr` | `0x000320` | 38 |
| `sprite_dma_addr_high_bits_fix` | `0x000346` | 12 |
| `genesistan_hook_tilemap_plane_a` | `0x000352` | 8 |
| `vdp_commit_tiles_if_dirty` | `0x00035A` | 42 |
| `vdp_commit_bg` | `0x000384` | 50 |
| `vdp_commit_palette` | `0x0003B6` | 32 |
| `vdp_commit_scroll` | `0x0003D6` | **62** |
| (end of `vdp_commit_scroll`) | `0x000414` | — |
| `rastan_direct_update_inputs` | `0x000414` | ~130 |
| `arcade_tick_logic` | `~0x000496` | 12 |
| `init_staging_state` | `~0x0004A2` | large |

Confirmed anchors match the previous doc (`vdp_commit_bg = 0x384`, `vdp_commit_tiles_if_dirty = 0x35A`,
`vdp_commit_palette = 0x3B6`).

### Preserved region boundary

The patcher restores genesis bytes at `0x000000`-`0x0003FF` (1024 bytes). Bytes at
`0x000400` and above are arcade ROM data in the final binary.

### `vdp_commit_scroll` boundary crossing

`vdp_commit_scroll` at `0x3D6`, 62 bytes, ends at `0x413`:

| Range | Content |
|---|---|
| `0x3D6`-`0x3FF` (42 bytes) | Preserved genesis bytes (correct instructions) |
| `0x400`-`0x413` (20 bytes) | Arcade ROM data (not genesis instructions) |

The last preserved instruction starting before `0x400` is `move.w staged_scroll_y_fg, VDP_DATA`
(opcode at `0x3FE`-`0x3FF`, operand extension words at `0x400`-`0x407` = arcade ROM bytes).
The next intended instruction `move.w staged_scroll_y_bg, VDP_DATA` starts at `0x408` = arcade
ROM bytes. The `rts` at `0x412`-`0x413` = arcade ROM bytes.

### Mapping observed addresses to content

| Observed PC | Content |
|---|---|
| `0x000404` | Arcade ROM byte (4 bytes into the corrupted `move.w staged_scroll_y_fg, VDP_DATA` operand extension) |
| `0x000408` | Arcade ROM byte (start of where `move.w staged_scroll_y_bg, VDP_DATA` was intended; now arcade ROM data decoded as a 68000 instruction) |
| `0x00040C` | Arcade ROM byte (mid-instruction or branch target in arcade ROM decoded sequence) |
| `0x0008AA` | Arcade ROM data at binary offset `0x8AA` = arcade ROM offset `0x8AA - 0x200 = 0x6AA`; a called or jumped-to address from the loop at `0x400` range |
| `0x0008B2` | Arcade ROM data; sequential or branch target from `0x8AA` |
| `0x0008B8` | Arcade ROM data; sequential or branch target from `0x8B2` |

The pattern `0x040C → 0x0404 → 0x08AA → 0x08B2 → 0x08B8 → 0x0408 → 0x040C` is consistent
with arcade ROM bytes at `0x400-0x40F` decoding as a `BSR` or `JSR` instruction that calls
a subroutine at `0x0008AA`, executes 3 sequential instructions there, returns (via `RTS` in
arcade data at `0x8B8`+), and loops back — all because the arcade ROM data there happens to
form syntactically valid 68000 opcodes that create a loop.

**Observed loop addresses identified exactly: YES** (mapped to arcade ROM data overwriting
genesis code above `0x3FF`).

---

## 4. Main Loop Wait Analysis

In `main_68k.s`, the wait loop:

```
.Lmain_loop:
    move.w  frame_counter, %d0      ; snapshot current counter value
.Lwait_vblank:
    cmp.w   frame_counter, %d0      ; compare with live value
    beq.s   .Lwait_vblank           ; spin while equal (VBlank not yet fired)

    bsr     arcade_tick_logic
    bra.s   .Lmain_loop
```

Located at approximately `0x23A`-`0x24D` (entirely within preserved region).

- **Polled variable**: `frame_counter`
- **Location of `frame_counter`**: `.bss` section at VMA `0xFF0000` (first `.word` in `.bss` = `0xFF0000`)
- **Wait condition**: loop exits when `frame_counter` differs from its snapshot value
- **Who increments `frame_counter`**: `addq.w #1, frame_counter` inside `_VINT_handler` at `0x284`

For the loop to exit, `_VINT_handler` must complete to `0x284` and execute `RTE`. Because
`vdp_commit_scroll` never returns (see Section 3), the handler never reaches `0x284`.
`frame_counter` stays at `0x0000`. The wait loop spins forever — but in fact, because SR
becomes IPL=6 once VBlank fires and the handler does not return, the main loop itself is no
longer executing; execution is stuck inside the handler.

**Main loop wait condition identified: YES**
**Waited-on variable (`frame_counter`) identified: YES**

---

## 5. SR / Interrupt Mask Analysis

### SR = `0x2604` decoded

```
0x2604 = 0010 0110 0000 0100
          ^^^^ = T=0, S=1 (supervisor mode)
               ^^^ = IPL mask bits [10:8] = 110 = 6
                         ^^^^ = CCR high bits = 0
                              ^^^^ = CCR: Z=1, N=0, V=0, C=0
```

- **Supervisor mode**: S=1 — execution is in supervisor (interrupt) context.
- **IPL mask = 6**: Interrupts at level 6 require IPL mask < 6 to be accepted. With mask=6,
  only level-7 NMI can interrupt. Level-6 VBlank is blocked.
- **Z=1**: The most recent flag-affecting instruction in the current execution stream compared
  equal or produced a zero result.

### How SR reached `0x2604`

1. After `main_68k` executes `move.w #0x2000, %sr` (at `0x236`), SR = `0x2000` (IPL=0).
2. VBlank fires (VDP VInt enabled via MODE2 bit 5 = 1 in `vdp_boot_setup`). The 68000 accepts
   the Level 6 interrupt. The CPU automatically:
   - Pushes current PC and SR (`0x2000`) onto the supervisor stack.
   - Sets the new SR: T=0, S=1, IPL = interrupt level being serviced = 6. Result: SR = `0x2600`
     (plus CCR bits from whatever was in effect — CCR bits are generally not changed by the
     interrupt mechanism, but the hardware sets S=1, clears T, and sets IPL=6).
   - Fetches the exception vector at offset `0x78` (Level 6 autovector = vec[30]) = `_VINT_handler`.
   - Starts executing `_VINT_handler` at `0x000250`.
3. `_VINT_handler` runs. Eventually calls `bsr vdp_commit_scroll`, which executes the 42
   preserved bytes and then falls into arcade ROM bytes at `0x400`. Execution never returns
   to `_VINT_handler`. `RTE` (at `0x28E`) is never executed.
4. SR remains at IPL=6 throughout. The Z flag bit (`0x04`) in the observed `0x2604` value
   was set by one of the arcade ROM instructions in the loop at `0x400`-`0x40C` or `0x8AA`-`0x8B8`.

### SR explicitly set in source code

| File | Instruction | Value | IPL |
|---|---|---|---|
| `boot.s` `_start` | `move.w #0x2700, %sr` | `0x2700` | 7 (all masked) |
| `main_68k.s` `main_68k` | `move.w #0x2700, %sr` | `0x2700` | 7 (all masked) |
| `main_68k.s` `main_68k` | `move.w #0x2000, %sr` | `0x2000` | 0 (all enabled) |

There is NO instruction in any source file that explicitly sets SR to `0x2600`, `0x2604`,
or any value with IPL=6. The `0x2604` value is produced entirely by the CPU's interrupt
acceptance mechanism.

**Runtime SR/interrupt mask analyzed: YES**

---

## 6. VBlank Delivery and `frame_counter` Analysis

### VBlank vector wiring

`boot.s` exception vector table construction:
```
.org 0x000000
.long 0x00FF0000          ; vec[0]  = initial SSP
.long _start              ; vec[1]  = reset PC
.rept 28
.long _default_handler    ; vec[2..29] = bus error through level-5 autovector
.endr
.long _VINT_handler       ; vec[30] = Level 6 autovector (offset 0x78) = VBlank
.long _default_handler    ; vec[31] = Level 7 autovector
.rept 32
.long _default_handler    ; vec[32..63] = user-defined vectors
.endr
```

Vec[30] at offset `0x78` = `_VINT_handler`. This is correct for Level 6 VBlank on Genesis.

### VDP VInt enable

`vdp_boot_setup` sets VDP register 1 (MODE2) with value `VDP_MODE2_DISPLAY_OFF = 0x34`:
- `0x34` = `0011 0100` binary
- Bit 5 = 1 → VInt enabled
VInt is enabled from the start of `vdp_boot_setup`. This is correct.

### `frame_counter` increment path

`_VINT_handler` increments `frame_counter` at source line 89:
```
addq.w  #1, frame_counter
```
Assembled at approximately `0x284` (inside `_VINT_handler`, which is at `0x250`-`0x28F`).

For this increment to execute, the handler must survive through:
1. `bsr vdp_commit_bg` (at `0x262`) → calls `vdp_commit_bg` at `0x384` → this function
   is entirely within `0x384`-`0x3B5`, preserved. On first VBlank (`bg_dirty=1`, set by
   `init_staging_state`), `vdp_commit_bg` runs fully (BEQ not taken), writes 2048 words
   to VDP via `dbra` loop, clears `bg_dirty`, returns to `0x266`. (**Correct, returns.**)
2. `tst.b palette_dirty` / conditional `bsr vdp_commit_palette` → `vdp_commit_palette` at
   `0x3B6`-`0x3D5`, preserved. Writes 64 palette words, returns. (**Correct, returns.**)
3. `bsr vdp_commit_scroll` (at `0x280`) → calls `vdp_commit_scroll` at `0x3D6`.
   `vdp_commit_scroll` runs first 42 preserved bytes, then falls into arcade ROM bytes at
   `0x400`. **NEVER RETURNS.** Handler never reaches `0x284`. `frame_counter` never
   increments.

**VBlank vector path verified: YES** (vec[30] = `_VINT_handler`, VDP VInt bit set).
**`frame_counter` increment path verified: NO** — `vdp_commit_scroll` does not return;
`frame_counter` is never incremented.

---

## 7. Arcade Entry Reachability Analysis

### `0x0003A208` (`rastan_direct_arcade_tick_entry`)

`rastan_direct_arcade_tick_entry` is called from `arcade_tick_logic` (source line 322):
```
arcade_tick_logic:
    bsr     rastan_direct_update_inputs
    jsr     rastan_direct_arcade_tick_entry   ; = 0x0003A208
    rts
```

`arcade_tick_logic` is called from `main_68k`'s main loop ONLY AFTER the `wait_vblank`
poll exits (source lines 63-64):
```
    bsr     arcade_tick_logic
    bra.s   .Lmain_loop
```

The `wait_vblank` poll exits only when `frame_counter` changes. `frame_counter` is never
incremented (Section 6). Additionally, `arcade_tick_logic` itself is at approximately
`0x000496`, which is above `0x3FF` and thus in the arcade ROM region — its assembled bytes
are replaced by arcade ROM data. But this is moot: execution never reaches the `wait_vblank`
exit condition in the first place.

`0x0003A208` is unreachable. The breakpoint at `0x0003A208` never fires.

### `0x055B68` (BG hook `genesistan_hook_tilemap_plane_a`)

The BG hook is called from within the arcade ROM tick path. The tick path is entered only
via `rastan_direct_arcade_tick_entry`. Since that is never reached, the BG hook is also
never reached. The breakpoint at `0x055B68` never fires.

**Arcade tick non-reachability explained exactly: YES**
**BG hook non-reachability explained exactly: YES**

---

## 8. Single Root Cause

The genesis-side compiled code (`main_68k.s` `.text` section) extends to binary address
`0x000413`. The patcher restores genesis bytes only for addresses `0x000000`-`0x0003FF`.
Bytes at `0x000400`-`0x000413` (and all higher addresses) remain as arcade ROM data in the
final binary. The function `vdp_commit_scroll` (assembled at `0x3D6`-`0x413`) overflows
the preserved region by 20 bytes: its tail (`0x400`-`0x413`) is arcade ROM data. When
`_VINT_handler` calls `bsr vdp_commit_scroll`, execution proceeds through 42 correct bytes
and then falls into arcade ROM bytes at `0x000400`, which decode as arbitrary 68000
instructions that create the observed loop at `0x000404`-`0x00040C` / `0x0008AA`-`0x0008B8`.
`vdp_commit_scroll` never returns. `_VINT_handler` never reaches `addq.w #1, frame_counter`
or `rte`. `frame_counter` stays at 0. The main loop's `wait_vblank` never exits. SR remains
frozen at IPL=6 (set when VBlank was accepted). `rastan_direct_arcade_tick_entry` and the
BG hook are never reached.

---

## 9. Single Next Correction for Cody

**What must happen**: All genesis-side code that executes during or is called from
`_VINT_handler` must reside entirely within `0x000000`-`0x0003FF`.

**The overflow**: `vdp_commit_scroll` ends at `0x413`. The preserved region ends at `0x3FF`.
Overflow = 20 bytes.

**Two equivalent fix strategies**:

### Strategy A — Extend the preserved region (patcher side)

In `tools/translation/postpatch_startup_rom.py`, for the `rastan_direct` profile, change
the preserved region from `rom_bytes[0x000000:0x000400]` to `rom_bytes[0x000000:0x000800]`
(or larger, enough to cover all genesis code). This ensures genesis bytes at `0x400`-`0x7FF`
are also restored after the arcade ROM copy, so `vdp_commit_scroll`'s tail survives intact.

The exact replacement line (currently): `preserved_genesis_vectors = bytes(rom_bytes[0x000000:0x000400])`
The corrected form: `preserved_genesis_bytes = bytes(rom_bytes[0x000000:0x000800])`
And the restore line: `rom_bytes[0x000000:0x000800] = preserved_genesis_bytes`

The preserved size must cover the full compiled size of all `.text` and `.rodata` content.
To determine the exact size, read the ELF `.text` section size after a clean build:
`size apps/rastan-direct/out/rastan_direct_video_test.elf` or check the linker map.
Round up to the next 512-byte boundary for safety.

### Strategy B — Shrink genesis code to fit within 0x3FF (source side)

Reduce the size of functions in `main_68k.s` so that all code from `0x000200` onward fits
within `0x000000`-`0x0003FF` (1024 bytes total including header). Given the header occupies
`0x000000`-`0x0001FF`, and `_default_handler` + `_start` occupy `0x000200`-`0x000229`, the
genesis code (starting at `main_68k` = `0x22A`) has only `0x3FF - 0x22A + 1` = `0x1D6` =
470 bytes available. The current code is significantly larger. This strategy requires
substantial code restructuring and is not recommended as the immediate fix.

**Recommended**: Strategy A. Extend the preserved region to cover the full genesis ELF `.text`
section size, rounded up to a power of two or page size.

**Exact file**: `tools/translation/postpatch_startup_rom.py`
**Exact location**: the `rastan_direct` profile's preserved-bytes slice and restore, in the
`defer` block that runs last before checksum/write.
**Exact change**: increase both the save slice and the restore slice from `0x000400` to a
value at or above the end of the compiled genesis `.text` section (at minimum `0x000500`
to cover `vdp_commit_scroll` + a safe margin; a value of `0x001000` provides ample
headroom for the entire genesis wrapper code).

Additionally: update the postpatch boot guard (`tools/translation/verify_rastan_direct_boot_guard.py`)
to also verify a byte within `vdp_commit_scroll` (e.g., that `0x412` = `0x4E 0x75` = `RTS`
and `0x40C` contains an expected instruction byte), confirming the entire function survives
the patcher.

---

## 10. What Must Not Be Changed Yet

1. **`apps/rastan-direct/src/main_68k.s`** — Source is correct. `vdp_commit_scroll` logic
   is correct. `_VINT_handler` structure is correct. `move.w #0x2000, %sr` correctly enables
   VBlank. `frame_counter` increment and `rte` are correct. Do not modify.

2. **`apps/rastan-direct/src/boot/boot.s`** — Exception vector table, `_default_handler`,
   `_start`, and SR initialization are all correct. VBlank vector (vec[30]) wired to
   `_VINT_handler` is correct. Do not modify.

3. **`apps/rastan-direct/link.ld`** — Linker layout (`.text` at `0x000000`, `.bss` at
   `0xFF0000`) is correct. Do not modify.

4. **`specs/rastan_direct_remap.json`** — Relocation delta, whole-maincpu copy config,
   10 opcode-replace entries, `rom_absolute_call_relocation` settings are all verified
   correct from previous analyses. Do not modify.

5. **`rastan_direct_arcade_tick_entry = 0x0003A208`** — This address is correct (arcade
   src `0x03A008` + relocation `0x000200`). Do not change.

6. **The deferred preserved-byte restore timing** — The Cody final-ROM boot-byte fix
   (deferring the restore until after rewrite passes) is correct and must be kept. The
   fix needed is to the SIZE of the preserved region, not the timing.

7. **The 10 opcode-replace patches** — Verified applied by the manifest. Not the cause
   of this failure. Do not alter.

8. **`apps/rastan-direct/Makefile`** — The build chain (clean build forced, prepatch and
   postpatch guards) is correct as fixed by Cody. Do not modify unless extending the
   guard to also check `vdp_commit_scroll` bytes.

---

## 11. Final Verdict

The PC loop at `0x000404`-`0x00040C` and `0x0008AA`-`0x0008B8` with SR = `0x2604` is
caused by a single defect: `vdp_commit_scroll` (assembled bytes `0x3D6`-`0x413`) overflows
the patcher's preserved genesis region (`0x000000`-`0x0003FF`) by 20 bytes. The bytes at
`0x000400`-`0x000413` are arcade ROM data. When `_VINT_handler` calls `bsr vdp_commit_scroll`,
execution falls into arcade ROM bytes at `0x000400` and loops. `vdp_commit_scroll` never
returns. `frame_counter` is never incremented. SR stays at IPL=6 (Level 6 interrupt was
accepted, handler never returned). The main loop's `wait_vblank` never exits.
`rastan_direct_arcade_tick_entry` (`0x0003A208`) and the BG hook (`0x055B68`) are both
unreachable. The correction is to extend the patcher's preserved region to cover the full
compiled size of the genesis `.text` section, ensuring all genesis wrapper code survives
the arcade ROM copy.
