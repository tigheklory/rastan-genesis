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
- hook symbol: `N/A`
- patch span: `N/A`
- caller site(s): dispatcher fall-through
- write shape: different from stride-8 sibling set (out of current scope)
- sentinel behavior: `N/A`
- game-state reads: includes dispatcher/default-path specific state reads
- A1 post-advance contract: `PENDING`
- unique behavior notes: explicitly excluded from Build 0034 scope
- build introduced: `N/A`
- build last verified: `0034`
- implementation status: `OUT OF SCOPE / PENDING`
