# Handler Translation Coverage

Build context: `rastan-direct` Build 0034.

This ledger tracks the text-writer dispatcher family coverage and is the durable mapping artifact for per-handler hook translation.

## Coverage Entries

### 1) `arcade_pc: 0x03C4D2`
- `genesis_rom_offset`: `0x03C6D2`
- hook symbol: `genesistan_hook_text_writer_3c4d2`
- patch span: `0x03C4D2..0x03C515` (`0x44` bytes)
- caller site(s): `0x03C924`, `0x03C92C`
- write shape: stride-8 glyph pair writer (`A1@(2)` / `A1@(6)` equivalent), staged FG translation
- sentinel behavior: `D3==0x50 && final-iteration` early-skip behavior
- game-state reads: none
- A1 post-advance contract: `A1 = entry + 0x50`
- unique behavior notes: existing baseline hook from Build 0033
- build introduced: `0033`
- build last verified: `0034`
- implementation status: `VERIFIED`

### 2) `arcade_pc: 0x03C550`
- `genesis_rom_offset`: `0x03C750`
- hook symbol: `genesistan_hook_text_writer_3c550`
- patch span: `0x03C550..0x03C586` (`0x36` bytes)
- caller site(s): `0x03C93C`
- write shape: 5-iteration stride-8 pair writer, attribute-first source semantics, staged FG emission
- sentinel behavior: none
- game-state reads: none
- A1 post-advance contract: loop `+8` per iter, then `+0x30` post-loop
- unique behavior notes: one glyph byte reused across all iterations
- build introduced: `0034`
- build last verified: `0034`
- implementation status: `IMPLEMENTED`

### 3) `arcade_pc: 0x03C586`
- `genesis_rom_offset`: `0x03C786`
- hook symbol: `genesistan_hook_text_writer_3c586`
- patch span: `0x03C586..0x03C606` (`0x80` bytes)
- caller site(s): `0x03C94C`
- write shape: dual-path stride-8 writer (inner-loop + helper inserts), staged FG emission
- sentinel behavior: `0xFF` byte sentinel in inner loop
- game-state reads: `A4@(1).b` path selector
- A1 post-advance contract: path-dependent (`+0x18` or `+0x10` post blocks, with loop/helper advances)
- unique behavior notes: two-phase left/right bias (`D2=0` then `D2=-16`)
- build introduced: `0034`
- build last verified: `0034`
- implementation status: `IMPLEMENTED`

### 4) `arcade_pc: 0x03C636`
- `genesis_rom_offset`: `0x03C836`
- hook symbol: `genesistan_hook_text_writer_3c636`
- patch span: `0x03C636..0x03C6AC` (`0x76` bytes)
- caller site(s): `0x03C944`
- write shape: conditional prelude + dual inner-loop stride-8 writer, staged FG emission
- sentinel behavior: `0xFF` byte sentinel in inner loop
- game-state reads: `A5@(280).b`, `A5@(318).w`
- A1 post-advance contract: path-dependent post add (`+0x20` or `+0x30`), plus loop/helper advances
- unique behavior notes: same game-state gate controls prelude inclusion and epilogue A1 add
- build introduced: `0034`
- build last verified: `0034`
- implementation status: `IMPLEMENTED`

### 5) `arcade_pc: 0x03C6DC`
- `genesis_rom_offset`: `0x03C8DC`
- hook symbol: `genesistan_hook_text_writer_3c6dc`
- patch span: `0x03C6DC..0x03C70A` (`0x2E` bytes)
- caller site(s): `0x03C91C`
- write shape: two-pass stride-8 writer (`D1` offset sweep then fixed), staged FG emission
- sentinel behavior: zero-byte terminator in inner loop
- game-state reads: none
- A1 post-advance contract: inner loops advance by `+8`/iter, then extra `+8` epilogue
- unique behavior notes: first pass `D1` increments by 16; second pass fixed `D1`
- build introduced: `0034`
- build last verified: `0034`
- implementation status: `IMPLEMENTED`

### 6) `arcade_pc: 0x03C75C`
- `genesis_rom_offset`: `0x03C95C`
- hook symbol: `genesistan_hook_text_writer_3c75c`
- patch span: `0x03C75C..0x03C7A4` (`0x48` bytes)
- caller site(s): `0x03C934`
- write shape: prelude helper pair + four stride-8 inner blocks with varied `(D2,D3)`, staged FG emission
- sentinel behavior: `0xFF` byte sentinel in shared inner flavor
- game-state reads: none
- A1 post-advance contract: prelude/inner advances plus `+0x10` epilogue
- unique behavior notes: four distinct `(bias,count)` inner calls in one handler
- build introduced: `0034`
- build last verified: `0034`
- implementation status: `IMPLEMENTED`

### 7) `arcade_pc: 0x03C7A4`
- `genesis_rom_offset`: `0x03C9A4`
- hook symbol: `genesistan_hook_text_writer_3c7a4`
- patch span: `0x03C7A4..0x03C7D2` (`0x2E` bytes)
- caller site(s): `0x03C914`
- write shape: mixed synthesized-tile inner flavor + script-byte inner flavor, staged FG emission
- sentinel behavior: `0xFF` sentinel in script-byte inner flavor
- game-state reads: none
- A1 post-advance contract: no explicit post add after final inner block
- unique behavior notes: synthesized tile source (`-32/-48` bias) for first two blocks
- build introduced: `0034`
- build last verified: `0034`
- implementation status: `IMPLEMENTED`

### 8) `arcade_pc: 0x03C830`
- `genesis_rom_offset`: `0x03CA30`
- hook symbol: `genesistan_hook_text_writer_3c830`
- patch span: `0x03C830..0x03C85E` (`0x2E` bytes)
- caller site(s): `0x03C90C`
- write shape: dual-path stride-8 writer with complex first-iteration behavior, staged FG emission
- sentinel behavior: zero-byte terminator in inner flavor
- game-state reads: `A4@(56).b`, `A5@(280).b`, `A5@(318).w`
- A1 post-advance contract: path-dependent (primary: loop-driven; alt: helper+loops then `+0x10`)
- unique behavior notes: preserves special `A1@(4)`-derived first-iteration attribute behavior via explicit left-cell special-attribute path
- build introduced: `0034`
- build last verified: `0034`
- implementation status: `IMPLEMENTED`

### 9) `arcade_pc: 0x03C950` (default path)
- `genesis_rom_offset`: `0x03CB50`
- hook symbol: `genesistan_hook_text_writer_3c950`
- patch span: `arcade_pc: 0x03C950..0x03CA37` (`0xE8` bytes)
- caller site(s): dispatcher fall-through
- write shape: `A1@+` stride-2 default path; per non-sentinel iter writes ordered as `attr(N) -> tile(N) -> attr(N+1) -> tile(N+1)` with staged FG translation
- sentinel behavior: fast-fill writes blank tile `0x0180` at cell-N tile slot only, then advances `A1` by `+8`
- game-state reads: `A4@(3)/(22)/(24)/(26)/(30)/(39)`, `D3` top nibble, `D6` bit 0, `D7` selector/sign, absolute word read at address `0x000010`
- A1 post-advance contract: exactly `+8` bytes per iteration in all paths
- unique behavior notes: inlines `arcade_pc: 0x03C8F6` behavior (`D3==0x70 => D1 += A4@(24)`); preserves alt-path absolute word read from `0x000010`; write family differs from stride-8 hooks
- build introduced: `0035`
- build last verified: `0035`
- implementation status: `IMPLEMENTED`

### 10) `arcade_pc: 0x03C2E2` (number renderer)
- `genesis_rom_offset`: `0x03C4E2`
- hook symbol: `genesistan_hook_number_renderer_3c2e2`
- patch span: `arcade_pc: 0x03C2E2..0x03C37B` (`0x9A` bytes)
- caller site(s): `0x03A546`, `0x03A96E`, `0x03B0AC`, `0x03B426`, `0x03B42C`, `0x03B714` (live); `0x03AC60` (dead via prior patched-site overwrite)
- write shape: stride-4 digit loop (`A1@+` attr then tile per digit), indexed leading-zero suppression (`A1@(2)`), and `"ALL"` sequence writes (`A1@+`/final `A1@`) translated to staged FG writes
- sentinel behavior: `count==0xFFFF` enters `"ALL"` path; `count==6` enables leading-zero suppression (`0x30 -> 0x20`)
- game-state reads: table-driven values at `genesis_rom_offset: 0x03C57C`; `A5` (Genesis WRAM base for A2 relocation)
- A1 post-advance contract: `+4` bytes per digit in digit loop; `+4` per scanned digit in suppression loop; `"ALL"` literal path net `+2` bytes from entry position
- unique behavior notes: absolute table access at `0x0003C57C`; `A2 = A5 + (table_a2_value & 0xFFFF)` relocation; all tile codes (`0x30+nibble`, `0x20`, `0x41`, `0x4C`) translated through `genesistan_pc080sn_tile_vram_lut`; all 13 decoded table destinations are FG-range
- build introduced: `0036`
- build last verified: `0036`
- implementation status: `VERIFIED`
