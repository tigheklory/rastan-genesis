# Andy — P1 / P2 Prerequisite Verification

**Agent:** Andy
**Type:** Forensic Verification (analysis only, no implementation)
**Build context:** current `rastan-direct`
**Architecture compliance:** CONFIRMED against [RULES.md](RULES.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

**Outcome: P1 = FAIL. P2 = FAIL. Cody implementation blocked.**

Both prerequisites from
[Andy_rastan_direct_runtime_decomposition.md](docs/design/Andy_rastan_direct_runtime_decomposition.md)
Phase 7 are unsatisfied. Specific blocking instructions enumerated
below. No fix proposed (forensic scope).

---

## Address-space legend

- `arcade_pc <value>` — PC in arcade ROM address space. Bytes live at
  file offset `arcade_pc` in [build/regions/maincpu.bin](build/regions/maincpu.bin).
- `genesis_rom_offset <value>` — byte offset in the built Genesis ROM.
  Per [address_map.json](build/rastan-direct/address_map.json)
  `relocation_delta = 0x000200` and the arcade-copy segment covers
  arcade `0x000E0A..0x03A0A8` at `identity_offset 512`, so within
  that window `genesis_rom_offset = arcade_pc + 0x200`.
- `runtime_genesis_pc <value>` — PC value the 68000 executes at
  runtime; equal to `genesis_rom_offset` for code reached via the
  reset vector or JMP that stays in ROM.
- `HW_ADDRESS <region/chip> <addr>` — 68000-space address that in
  the **arcade** system decoded to a named chip. On Genesis the same
  address typically lands in undefined/unmapped space.

---

## Address mapping confirmation

From [build/rastan-direct/address_map.json](build/rastan-direct/address_map.json)
lines 28-37: arcade copy segment `arcade_start 0x000E0A .. arcade_end_exclusive 0x03A0A8`
at identity_offset 512 covers the arcade range that contains `0x03A000` and `0x03A008`.
First opcode-replace site is at `arcade_pc 0x03A0A8` (line 115 of
[specs/rastan_direct_remap.json](specs/rastan_direct_remap.json)), so
**arcade bytes at `0x3A000..0x3A0A7` run with their original encoding**.

| symbol                    | arcade_pc     | genesis_rom_offset | runtime_genesis_pc |
| ------------------------- | ------------- | ------------------ | ------------------ |
| arcade cold-init entry    | `0x0003A000`  | `0x00003A200`      | `0x00003A200`      |
| arcade L5 VBlank handler  | `0x0003A008`  | `0x00003A208`      | `0x00003A208`      |
| `startup_common` body     | `0x0003AE86`  | `0x00003B086`      | `0x00003B086`      |
  *(target of BRA.W at `0x3A000`; `0x3A000 + 2 + 0x0E84 = 0x3AE86`)*

Both target addresses successfully mapped. No STOP on mapping.

---

## P1 — arcade_pc 0x0003A000 (startup_common)

### Step 1-2. Scope and disassembly

`arcade_pc 0x0003A000` itself is a single `BRA.W` (6 bytes) that
leaves the region on instruction #1. The useful verification scope is
its target, `arcade_pc 0x0003AE86` — the actual `startup_common`
body. I disassembled `arcade_pc 0x0003AE86` through `arcade_pc
0x0003B030` (~80 instructions) from
[build/maincpu.disasm.txt:73984-74091](build/maincpu.disasm.txt).

Raw entry point (bytes at file offset `0x3A000` from
[build/regions/maincpu.bin](build/regions/maincpu.bin)):

| arcade_pc     | bytes              | mnemonic             | leaves region?            |
| ------------- | ------------------ | -------------------- | ------------------------- |
| `0x0003A000`  | `60 00 0E 84`      | `BRA.W 0x0003AE86`   | YES — unconditional       |

Continuation at `arcade_pc 0x0003AE86` ...

### Step 3. Hardware writes (and selected reads) in startup_common body

Every instruction in `0x3AE86..0x3B030` that writes, or reads-for-setup, an address outside arcade work-RAM. Classification column
checks [specs/rastan_direct_remap.json](specs/rastan_direct_remap.json)
for a matching `arcade_pc` opcode-replace.

| arcade_pc     | instruction                                  | HW target         | arcade chip (reference)          | hooked in remap.json? | blocking P1 |
| ------------- | -------------------------------------------- | ----------------- | -------------------------------- | --------------------- | ----------- |
| `0x0003AE86`  | `MOVE.W #0, 0x00C50000`                      | `HW 0x00C50000`   | PC080SN screen-flip              | **NO**                | **YES**     |
| `0x0003AE8E`  | `MOVE.W #0, 0x00D01BFE`                      | `HW 0x00D01BFE`   | PC090OJ sprite DMA               | **NO**                | **YES**     |
| `0x0003AE96`  | `CLR.W 0x00350008`                           | `HW 0x00350008`   | TC0140SYT / sound coin counter   | **NO**                | **YES**     |
| `0x0003AE9C`  | `CLR.W 0x00380000`                           | `HW 0x00380000`   | TC0040IOC watchdog/control       | YES — spec line 295 (`4E71 4E71 4E71` suppress) | no |
| `0x0003AEA2`  | `MOVE.B #4, 0x003E0001`                      | `HW 0x003E0001`   | TC0140SYT sound-CPU reset        | **NO**                | **YES**     |
| `0x0003AEAA`  | `MOVE.B #1, 0x003E0003`                      | `HW 0x003E0003`   | TC0140SYT sound-CPU bank         | **NO**                | **YES**     |
| `0x0003AEB6`  | `MOVE.W 0x00200000, D1` *(read)*             | `HW 0x00200000`   | RAM probe (Rastan-specific)      | **NO**                | **YES**     |
| `0x0003AEBC`  | `MOVE.W D1, 0x00200000`                      | `HW 0x00200000`   | RAM probe write-back             | **NO**                | **YES**     |
| `0x0003AEC6`  | `MOVE.B #4, 0x003E0001`                      | `HW 0x003E0001`   | TC0140SYT sound-CPU reset        | **NO**                | **YES**     |
| `0x0003AECE`  | `MOVE.B #0, 0x003E0003`                      | `HW 0x003E0003`   | TC0140SYT sound-CPU bank         | **NO**                | **YES**     |
| `0x0003AEDA`  | `MOVE.W 0x00200000, D1` *(read)*             | `HW 0x00200000`   | RAM probe                        | **NO**                | **YES**     |
| `0x0003AEE0`  | `MOVE.W D1, 0x00200000`                      | `HW 0x00200000`   | RAM probe write-back             | **NO**                | **YES**     |
| `0x0003AEEA`  | `LEA 0x0010C000, A0`                         | *(pointer load — 0x10C000 is arcade work-RAM)* | arcade work-RAM | — | see 0x3AF04 note below |
| `0x0003AEF0`  | `LEA 0x0010C002, A1`                         | *(pointer load)*  | arcade work-RAM                   | —                     | no          |
| `0x0003AEF6`  | `MOVE.W #0, (A0)`                            | `HW 0x0010C000`   | arcade work-RAM zero             | **NO** *(pointer)*    | **YES** (Note 1) |
| `0x0003AEFE..0x3AF02` | work-RAM propagate loop          | `HW 0x0010C002..0x0010E000` | arcade work-RAM          | **NO** *(pointer)*    | **YES** (Note 1) |
| `0x0003AF04`  | `LEA 0x0010C000, A5`                         | *(pointer load — arcade work-RAM base)* | — | YES — spec line 301 (redirects to `0x00FF0000`) | no |
| `0x0003AF0A`  | `MOVE.W D0, 0x003C0000`                      | `HW 0x003C0000`   | TC0040IOC video-control          | **NO**                | **YES**     |
| `0x0003AF14`  | `MOVE.W D0, 0x003C0000`                      | `HW 0x003C0000`   | same                             | **NO**                | **YES**     |
| `0x0003AF1E`  | `MOVE.W D0, 0x00380000`                      | `HW 0x00380000`   | watchdog                          | YES — spec line 307 (NOP suppress) | no |
| `0x0003AF2C`  | `LEA 0x00C00000, A0`                         | *(PC080SN BG base ptr)* | pointer to PC080SN        | pointer target (see Note 2) | no (consumed by 0x3AD44 hook) |
| `0x0003AF3C`  | `LEA 0x00C08000, A0`                         | *(PC080SN FG base ptr)* | pointer to PC080SN        | pointer target (see Note 2) | no |
| `0x0003AF4C`  | `MOVE.W D0, 0x003C0000`                      | `HW 0x003C0000`   | TC0040IOC video-control          | **NO**                | **YES**     |
| `0x0003AF52`  | `LEA 0x00C04000, A0`                         | *(PC080SN attr BG)*     | pointer to PC080SN        | pointer target (see Note 2) | no |
| `0x0003AF62`  | `LEA 0x00C0C000, A0`                         | *(PC080SN attr FG)*     | pointer to PC080SN        | pointer target (see Note 2) | no |
| `0x0003AF72`  | `MOVE.W D0, 0x003C0000`                      | `HW 0x003C0000`   | TC0040IOC video-control          | **NO**                | **YES**     |
| `0x0003AF7A`  | `MOVE.B 0x00390009, D0` *(read)*             | `HW 0x00390009`   | DIP1 read                        | YES — spec line 313 (replaced with `#0xFE`) | no |
| `0x0003AF86`  | `MOVE.B 0x0039000B, D0` *(read)*             | `HW 0x0039000B`   | DIP2 read                        | YES — spec line 319 (replaced with `#0xFF`) | no |
| `0x0003AFEE`  | `MOVE.W 0x0005FF9E, D0` *(read)*             | arcade ROM tail  | OK — ROM read in-range            | —                     | no          |
| `0x0003AFFE`  | `MOVE.W 0x0005FF9E, D0` *(read)*             | arcade ROM tail  | same                             | —                     | no          |

**Note 1 — arcade work-RAM writes at `0x10C000..0x10E000`.** The
0x10C000 write at `0x0003AEF6` and the propagate loop at
`0x0003AEFE..0x0003AF02` write through `A0`/`A1` to arcade work-RAM
(`0x10C000..` in arcade hardware, unmapped in Genesis). `A0` and `A1`
are loaded from absolute literals at `0x0003AEEA` and `0x0003AEF0`.
**These literal loads are NOT opcode-replaced.** The existing remap
only redirects the `A5` work-RAM base at `0x0003AF04` (spec line 301)
to `0x00FF0000`; it does not redirect the earlier `A0/A1` loads at
`0x0003AEEA / 0x0003AEF0`. Result: arcade's work-RAM-zero loop writes
through `A0/A1` still point at `HW 0x0010C000` — which on Genesis
is unmapped cart-ROM space. Writes silently ignored at best; bus
error at worst. Either way, the arcade-intended zero-fill of
`0x0010C000..0x0010E000` does not happen — arcade workram at
`0x00FF0000+` is not zeroed by this path.

**Note 2 — PC080SN tilemap base-pointer loads at `0x0003AF2C / 0x0003AF3C / 0x0003AF52 / 0x0003AF62`.**
Each `LEA 0xC0xxxx, A0` is followed by a `BSR.W 0x0003AD44` or
`BSR.W 0x0003AD3C` fill-loop call. The `0x0003AD44` fill helper is
itself hooked via opcode_replace (spec line 259) to a
`genesistan_hook_tilemap_bg_fill` RTS-returning helper, which writes
to `staged_bg_buffer` via the pointer in `A0`. The helper contains
address-range guards that reject pointers outside
`ARCADE_PC080SN_CWINDOW_BASE_BG..+0x4000`, so only writes with
`A0 ∈ [0xC00000, 0xC04000)` take effect; the `LEA 0xC04000, A0` and
`LEA 0xC0C000, A0` base-pointer loads at `0x0003AF52` and
`0x0003AF62` fall outside that range and are silently ignored by the
hook. **Not blocking — behaviour is absorbed by the existing hook's
range check.**

### Step 4. Control-flow escapes in the first ~80 instructions

| arcade_pc     | instruction                  | target        | classification                                              | blocking P1 |
| ------------- | ---------------------------- | ------------- | ----------------------------------------------------------- | ----------- |
| `0x0003A000`  | `BRA.W 0x0003AE86`           | `arcade_pc 0x3AE86` | arcade code                                            | no          |
| `0x0003AEC4`  | `BNE.S 0x0003AEB6`           | `arcade_pc 0x3AEB6` | arcade code (local loop)                                | no          |
| `0x0003AEE8`  | `BNE.S 0x0003AEDA`           | `arcade_pc 0x3AEDA` | arcade code (local loop)                                | no          |
| `0x0003AF02`  | `BNE.S 0x0003AEFE`           | `arcade_pc 0x3AEFE` | arcade code (local loop)                                | no          |
| `0x0003AF10`  | `BSR.W 0x0003B9F8`           | `arcade_pc 0x3B9F8` | arcade code                                             | no          |
| `0x0003AF28`  | `BSR.W 0x0003AD72`           | `arcade_pc 0x3AD72` | arcade code                                             | no          |
| `0x0003AF38`  | `BSR.W 0x0003AD44`           | `arcade_pc 0x3AD44` | arcade code → hooked Genesis RTS-returning helper (spec line 259) | no |
| `0x0003AF48`  | `BSR.W 0x0003AD44`           | same          | same                                                        | no          |
| `0x0003AF5E`  | `BSR.W 0x0003AD3C`           | `arcade_pc 0x3AD3C` | arcade code                                             | no          |
| `0x0003AF6E`  | `BSR.W 0x0003AD3C`           | same          | same                                                        | no          |

All escapes target arcade code (or arcade code that is itself
redirected to a Genesis `RTS`-returning hook via opcode_replace). No
escape targets Genesis runtime or boot code. **Control-flow escapes
are not blocking.**

### Step 5. P1 pass condition

P1 pass requires every hardware write to be explicitly hooked or
provably target WRAM/ROM only. That is **not** met.

**Unhooked writes in startup_common (first ~80 instructions):** 13,
listed in the "blocking P1: YES" rows above. All target arcade
hardware addresses that on Genesis land in unmapped space (outside
cart-ROM `0x000000..0x0FC1C3`, outside Genesis WRAM
`0x00FF0000..0x00FFFFFF`, outside VDP port band
`0x00C00000..0x00C0001F`, outside I/O band `0x00A10000..0x00A1001F`,
outside Z80 band `0x00A00000..0x00A0FFFF`).

The remap already handles the `0x380000` watchdog and the `0x390009/0x39000B`
DIP reads, and redirects the `A5` work-RAM base. It has NOT been
extended to cover the `0xC50000`, `0xD01BFE`, `0x350008`,
`0x3E0001/3`, `0x200000`, or `0x3C0000` writes, nor the `A0/A1`
work-RAM base loads at `0x0003AEEA / 0x0003AEF0`.

```
P1 result: FAIL
Blocking issues:
  - arcade_pc 0x0003AE86  MOVE.W #0, HW 0x00C50000  — PC080SN screen-flip, unhooked
  - arcade_pc 0x0003AE8E  MOVE.W #0, HW 0x00D01BFE  — PC090OJ sprite DMA, unhooked
  - arcade_pc 0x0003AE96  CLR.W HW 0x00350008       — TC0140SYT/coin, unhooked
  - arcade_pc 0x0003AEA2  MOVE.B #4, HW 0x003E0001  — sound-CPU reset, unhooked
  - arcade_pc 0x0003AEAA  MOVE.B #1, HW 0x003E0003  — sound-CPU bank, unhooked
  - arcade_pc 0x0003AEBC  MOVE.W D1, HW 0x00200000  — RAM probe, unhooked
  - arcade_pc 0x0003AEC6  MOVE.B #4, HW 0x003E0001  — unhooked
  - arcade_pc 0x0003AECE  MOVE.B #0, HW 0x003E0003  — unhooked
  - arcade_pc 0x0003AEE0  MOVE.W D1, HW 0x00200000  — unhooked
  - arcade_pc 0x0003AEF6  MOVE.W #0, (A0)           — A0 = HW 0x0010C000 (unmapped); A0 literal load at 0x3AEEA not redirected
  - arcade_pc 0x0003AF0A  MOVE.W D0, HW 0x003C0000  — TC0040IOC video-control, unhooked
  - arcade_pc 0x0003AF14  MOVE.W D0, HW 0x003C0000  — unhooked
  - arcade_pc 0x0003AF4C  MOVE.W D0, HW 0x003C0000  — unhooked
  - arcade_pc 0x0003AF72  MOVE.W D0, HW 0x003C0000  — unhooked
```

---

## P2 — arcade_pc 0x0003A008 (arcade L5 VBlank handler)

### Step 1-2. Scope and disassembly

[build/maincpu.disasm.txt:72947-72980](build/maincpu.disasm.txt)
disassembly, corroborated against [build/regions/maincpu.bin](build/regions/maincpu.bin)
at file offset `0x3A008..0x3A07F`:

| arcade_pc     | bytes                  | mnemonic                                   |
| ------------- | ---------------------- | ------------------------------------------ |
| `0x0003A008`  | `00 7C 0F 00`          | `ORI.W #0x0F00, SR`                        |
| `0x0003A00C`  | `42 79 00 35 00 08`    | `CLR.W 0x00350008`                         |
| `0x0003A012`  | `33 C0 00 3C 00 00`    | `MOVE.W D0, 0x003C0000`                    |
| `0x0003A018`  | `30 2D 00 02`          | `MOVE.W A5@(2), D0`                        |
| `0x0003A01C`  | `0C 40 00 02`          | `CMPI.W #2, D0`                            |
| `0x0003A020`  | `65 1C`                | `BCS.S 0x0003A03E`                         |
| `0x0003A022`  | `0C 40 00 04`          | `CMPI.W #4, D0`                            |
| `0x0003A026`  | `64 16`                | `BCC.S 0x0003A03E`                         |
| `0x0003A028`  | `61 00 00 FC`          | `BSR.W 0x0003A126`                         |
| `0x0003A02C`  | `4A 6D 00 00`          | `TST.W A5@(0)`                             |
| `0x0003A030`  | `67 0C`                | `BEQ.S 0x0003A03E`                         |
| `0x0003A032`  | `0C 6D 00 01 13 94`    | `CMPI.W #1, A5@(5012)`                     |
| `0x0003A038`  | `67 04`                | `BEQ.S 0x0003A03E`                         |
| `0x0003A03A`  | `61 00 7E F4`          | `BSR.W 0x00041F30`                         |
| `0x0003A03E`  | `61 00 0B 3C`          | `BSR.W 0x0003AB7C`                         |
| `0x0003A042`  | `61 00 0B 9E`          | `BSR.W 0x0003ABE2`                         |
| `0x0003A046`  | `61 00 00 60`          | `BSR.W 0x0003A0A8` *(target itself hooked at spec line 115)* |
| `0x0003A04A`  | `61 00 4E AE`          | `BSR.W 0x0003EEFA`                         |
| `0x0003A04E`  | `61 00 4F 0C`          | `BSR.W 0x0003EF5C`                         |
| `0x0003A052`  | `48 7A 00 20`          | `PEA pc@(0x0003A074)` — push RA            |
| `0x0003A056..0x0003A06A` | *(computed-JMP dispatch on A5@(0))* | LEA/ADD/MOVE/LEA/ADD/JMP (A0) |
| `0x0003A06C`  | `0992`                 | table entry 0 → target `0x0003A06C + 0x0992 = 0x0003A9FE` |
| `0x0003A06E`  | `0840`                 | table entry 1 → target `0x0003A06C + 0x0840 = 0x0003A8AC` |
| `0x0003A070`  | `00EE`                 | table entry 2 → target `0x0003A06C + 0x00EE = 0x0003A15A` |
| `0x0003A072`  | `0B02`                 | table entry 3 → target `0x0003A06C + 0x0B02 = 0x0003AB6E` |
| `0x0003A074`  | `4E B9 00 05 5C A2`    | `JSR 0x00055CA2`                           |
| `0x0003A07A`  | `02 7C F0 FF`          | `ANDI.W #0xF0FF, SR`                       |
| `0x0003A07E`  | `4E 73`                | `RTE`                                      |

### Step 3. Hardware writes

| arcade_pc     | instruction                    | HW target         | arcade chip                 | hooked? | blocking P2 |
| ------------- | ------------------------------ | ----------------- | --------------------------- | ------- | ----------- |
| `0x0003A00C`  | `CLR.W 0x00350008`             | `HW 0x00350008`   | TC0140SYT / coin counter    | **NO**  | **YES**     |
| `0x0003A012`  | `MOVE.W D0, 0x003C0000`        | `HW 0x003C0000`   | TC0040IOC video-control     | **NO**  | **YES**     |

No VDP port writes in the L5 handler body.

### Step 4. Control-flow escapes

| arcade_pc     | instruction                  | target                | classification    | blocking P2 |
| ------------- | ---------------------------- | --------------------- | ----------------- | ----------- |
| `0x0003A020`  | `BCS.S 0x0003A03E`           | `arcade_pc 0x3A03E`   | arcade code       | no          |
| `0x0003A026`  | `BCC.S 0x0003A03E`           | `arcade_pc 0x3A03E`   | arcade code       | no          |
| `0x0003A028`  | `BSR.W 0x0003A126`           | `arcade_pc 0x3A126`   | arcade code       | no          |
| `0x0003A030`  | `BEQ.S 0x0003A03E`           | `arcade_pc 0x3A03E`   | arcade code       | no          |
| `0x0003A038`  | `BEQ.S 0x0003A03E`           | `arcade_pc 0x3A03E`   | arcade code       | no          |
| `0x0003A03A`  | `BSR.W 0x00041F30`           | `arcade_pc 0x41F30`   | arcade code       | no          |
| `0x0003A03E`  | `BSR.W 0x0003AB7C`           | `arcade_pc 0x3AB7C`   | arcade code       | no          |
| `0x0003A042`  | `BSR.W 0x0003ABE2`           | `arcade_pc 0x3ABE2`   | arcade code       | no          |
| `0x0003A046`  | `BSR.W 0x0003A0A8`           | `arcade_pc 0x3A0A8` — itself hooked to Genesis shadow-input helper (spec line 115) | arcade → RTS-returning hook | no |
| `0x0003A04A`  | `BSR.W 0x0003EEFA`           | `arcade_pc 0x3EEFA`   | arcade code       | no          |
| `0x0003A04E`  | `BSR.W 0x0003EF5C`           | `arcade_pc 0x3EF5C`   | arcade code       | no          |
| `0x0003A06A`  | `JMP (A0)` computed          | one of `arcade_pc 0x3A9FE / 0x3A8AC / 0x3A15A / 0x3AB6E` | all four arcade_pc destinations, all arcade code | no |
| `0x0003A074`  | `JSR 0x00055CA2`             | `arcade_pc 0x55CA2`   | arcade code       | no          |

All control-flow escapes target arcade code (or arcade code that is
itself hooked via opcode_replace to a Genesis RTS-returning helper).
**No escape targets Genesis runtime or boot code.**

Note on the computed-JMP mode=3 entry: it dispatches to `arcade_pc
0x0003AB6E`, which is the Path-A thunk (`BRA.W 0x00039F80`) identified
in [Andy_reset_path_root_cause.md](docs/design/Andy_reset_path_root_cause.md).
Under the decomposition's opcode_replace of the warm-restart at
`arcade_pc 0x00039F9E` → `JMP arcade_pc 0x0003A000`, that dispatch
path remains arcade-owned (warm restart re-enters arcade
startup_common, not Genesis bootstrap). **Not blocking P2** in
itself, but reintroduces the P1 failures at runtime each time the
L5 dispatch picks mode=3 and the inner countdown at `A5@(0x2C)`
expires.

### Step 5. RTE confirmation

- **RTE present:** YES at `arcade_pc 0x0003A07E` (bytes `4E 73`).
- **Stacked return address class:** under the decomposition, the
  L5 auto-vector fires while arcade code is executing (any arcade PC
  in the `0x00000200..0x000FC1C3` Genesis-ROM-mapped range). 68000
  IRQ entry pushes SR and the interrupted PC. The pushed PC is the
  arcade instruction being retired when the IRQ arrived — i.e., an
  `arcade_pc`-derived `runtime_genesis_pc`. The RTE at `0x3A07E`
  pops exactly that SR+PC and returns control to arcade code.
  Class: **`arcade_pc`-derived `runtime_genesis_pc`**.
- **RTE safe:** YES — RTE returns to arcade code.

### Step 6. VDP conflict with `_vblank_service`

`_vblank_service` commits staged tiles / BG / FG / palette / scroll
to VDP, then tail-JMPs to `arcade_pc 0x0003A008`. The L5 handler from
`0x3A008..0x3A07E` performs **no VDP port writes** (no write to the
`0xC00000..0xC0001F` band). Consequently there is no VDP-state
conflict with `_vblank_service`.

```
VDP writes in L5 handler: NO
Conflict with _vblank_service commit state: NO
```

### Step 7. P2 pass condition

P2 pass requires every hardware write to be explicitly hooked or
provably target WRAM/ROM only. That is **not** met.

```
P2 result: FAIL
Blocking issues:
  - arcade_pc 0x0003A00C  CLR.W HW 0x00350008       — TC0140SYT/coin, unhooked
  - arcade_pc 0x0003A012  MOVE.W D0, HW 0x003C0000  — TC0040IOC video-control, unhooked
```

**Empirical note (not a proof):** the current `rastan-direct` build
routes the L5 handler through `arcade_tick_logic` in the
Genesis-owned loop and executes these two instructions on every
frame. Build 0046 MAME traces report execution continuing past these
without immediate exception (the crash at frame 386+ is from a
different code path — see [Andy_reset_path_root_cause.md](docs/design/Andy_reset_path_root_cause.md)).
This does not constitute a proof that the writes are safe — per
Global Rule 7 ("NO SPECULATION") the observed absence of crash is
not equivalent to proved safety. Addresses remain unhooked; P2
remains FAIL.

---

## Phase 3 — Combined verdict

```
P1 (startup_common 0x0003A000 → 0x0003AE86): FAIL
P2 (L5 handler 0x0003A008):                  FAIL

Ready for Cody decomposition implementation: NO
```

### Blocking issues before implementation

**P1 blockers (13 unhooked hardware writes in startup_common):**

| arcade_pc     | instruction                                  | HW target         |
| ------------- | -------------------------------------------- | ----------------- |
| `0x0003AE86`  | `MOVE.W #0, 0x00C50000`                      | PC080SN flip      |
| `0x0003AE8E`  | `MOVE.W #0, 0x00D01BFE`                      | PC090OJ sprite DMA |
| `0x0003AE96`  | `CLR.W 0x00350008`                           | sound/coin         |
| `0x0003AEA2`  | `MOVE.B #4, 0x003E0001`                      | sound-CPU reset    |
| `0x0003AEAA`  | `MOVE.B #1, 0x003E0003`                      | sound-CPU bank     |
| `0x0003AEBC`  | `MOVE.W D1, 0x00200000`                      | RAM probe          |
| `0x0003AEC6`  | `MOVE.B #4, 0x003E0001`                      | sound-CPU reset    |
| `0x0003AECE`  | `MOVE.B #0, 0x003E0003`                      | sound-CPU bank     |
| `0x0003AEE0`  | `MOVE.W D1, 0x00200000`                      | RAM probe          |
| `0x0003AEEA / 0x0003AEF6 / 0x3AEFE..` | A0=0x0010C000 + work-RAM fill | A0 literal load unmapped-range | 
| `0x0003AF0A`  | `MOVE.W D0, 0x003C0000`                      | video-control      |
| `0x0003AF14`  | `MOVE.W D0, 0x003C0000`                      | video-control      |
| `0x0003AF4C`  | `MOVE.W D0, 0x003C0000`                      | video-control      |
| `0x0003AF72`  | `MOVE.W D0, 0x003C0000`                      | video-control      |

**P2 blockers (2 unhooked hardware writes in L5 handler):**

| arcade_pc     | instruction                                  | HW target         |
| ------------- | -------------------------------------------- | ----------------- |
| `0x0003A00C`  | `CLR.W 0x00350008`                           | sound/coin         |
| `0x0003A012`  | `MOVE.W D0, 0x003C0000`                      | video-control      |

Until these are hooked (or proven to land in WRAM/ROM only on
Genesis), the decomposition cannot hand control to `arcade_pc
0x0003A000` on cold boot or to `arcade_pc 0x0003A008` on the L5
vector path without exposing Genesis hardware to arcade-era
hardware-register accesses whose runtime effect on Genesis is not
proven safe.

### Resolvable prerequisite work (scope note, not a fix)

The blocking issues above are bounded. The patterns in the remap
spec already show how similar writes are handled (`33C000380000` →
`4E714E714E71` suppress for the watchdog; shadow-byte redirects for
input reads). The same mechanism can extend to the additional sites
when that work is undertaken. That is implementation scope — out of
scope for this verification.

---

## Summary

- P1 arcade_pc 0x0003A000 mapped: YES — `genesis_rom_offset 0x00003A200`
- P1 hardware writes found: 14 (13 writes + 1 pointer-backed work-RAM zero loop)
- P1 unhooked writes: 13 (all in table above)
- P1 control-flow escapes classified: YES — all arcade code or arcade-code-via-hook
- P1 result: **FAIL**

- P2 arcade_pc 0x0003A008 mapped: YES — `genesis_rom_offset 0x00003A208`
- P2 hardware writes found: 2
- P2 unhooked writes: 2 (both in table above)
- P2 RTE confirmed: YES at `arcade_pc 0x0003A07E`
- P2 RTE return class: **`arcade_pc`-derived `runtime_genesis_pc`**
- P2 VDP conflict: NO
- P2 result: **FAIL**

- Ready for Cody implementation: **NO**
- STOP triggered: NO — verification completed with definitive FAIL verdict (not an INDETERMINATE/STOP state)

No fix proposed. No design change proposed. No architecture change proposed.
