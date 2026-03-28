# [Cody - Analysis, Descriptor Structure]

Tested artifact: `dist/Rastan_241.bin` (built with `RASTAN_EXCEPTION_DUMPER_MODE=1`).

Failing pre-translation record (baseline from `dist/Rastan_238.bin`):
- Selector path: `D0=0x0002`
- Table base in producer: `A1=0x0003BD92`
- Entry 2 pointer: `0x0003BCBE`
- Descriptor bytes at `0x03BCBE`: `0B0B0F0C 1210 0D18...`

`0x20034C` consumption contract (from disassembly/trace):
- `+0x00..+0x03` -> `D6` (destination cursor long)
- `+0x04..+0x05` -> `D3` (attribute/mode word)
- `+0x06..` -> byte text stream until `0x00`

Why it fails at `0x2003EC`:
- `0x2003E2`: builds lower bound from `D2 + 0xC800` -> `0xE0FFC84C`
- `0x2003EC`: `cmp.l D6,D0` then `bhi 0x2004AA` (reject)
- With stale descriptor, `D6=0x0B0B0F0C` (outside drawable translated range), so record is rejected before write path.

Expected semantic meaning:
- `D6` is the translated text destination cursor in the producer’s active destination window.
- Valid productive path requires `D6` to land in producer-accepted translated range (`>=0xE0FFC84C` and within upper/range/alignment checks through `0x2003F0/0x20040A`).

# [Cody - Implementation, Descriptor Translation]

Implemented change (spec-compliant, reusable, no constant descriptor patch):

1. Spec pointer-table source anchor corrected:
- File: `specs/startup_title_remap.json`
- `absolute_long_pointer_tables[0].table_address`
- before: `0x03BD92`
- after: `0x03BB7C`

2. Postpatch table-target translation corrected:
- File: `tools/translation/postpatch_startup_rom.py`
- In absolute-long-pointer-table rewrite, each target now maps as:
  - `new_target = old_target + relocation_delta_if_active + accumulated_shift_before(old_target)`

Why this is translation (not a hack):
- It applies to the entire descriptor pointer table (`entry_count=22`), not a single record.
- It preserves descriptor semantics by relocating source-space descriptor pointers into the active relocated+shifted runtime layout.
- No hardcoded destination constant (e.g. no `0xE0FFC84C` descriptor overwrite) was used.

Static before/after proof:
- Build 238 table at `0x03BD92`: `0003bc98 0003bca6 0003bcbe ...`
- Build 241 table at `0x03BD92`: `0003beae 0003bebc 0003bed4 ...`
- Build 238 entry2 descriptor (`0x03BCBE`): `0B0B0F0C1210...` (rejecting)
- Build 241 entry2 descriptor (`0x03BED4`): `E1000126000043524544495420202000` (translated destination + text payload)

# [Cody - Execution Proof]

Probe sources:
- `/tmp/first_graphics_break_trace.txt`
- `/tmp/text_record_branch_trace.txt`
- `/tmp/table_probe_239.txt`
- `/tmp/dma_probe_239.txt`

Execution hits (`dist/Rastan_241.bin`):
- `0x03BD5E`: hit `1`
- `0x202A4C`: hit `1`
- `0x20034C`: hit `1`

Descriptor-table live proof at call entry:
- `CALL ... t0=0003BEAE t1=0003BEBC t2=0003BED4`
- Producer uses translated table targets (no stale `0x03BCxx` path).

Rejection-site proof:
- `HIT 2003EC = 9`
- `HIT 2003F0 = 9` (no longer reject-all)
- `HIT 2004A2 = 9` (productive write path reached)

Producer write payload proof (`0x2004A2` samples):
- `D0(word)` values: `0014 0015 0016 0017 0018 0019 001A 001A 001A`
- non-space writes: `9/9`

DMA proof:
- `dma_reg_93=167`, `dma_reg_94=167`, `dma_reg_95=167`, `dma_reg_96=167`, `dma_reg_97=167`
- Non-zero DMA setup words present (examples): `955A`, `9340`, `96FC`, `971C`

# [Cody - Visual Proof]

Artifact screenshot:
- `docs/research/artifacts/build241_game_text.png`

Capture method:
- MAME AVI capture from `dist/Rastan_241.bin`, extracted frame 19 to PNG.

Observed result:
- On-screen readable game-executed text is visible (`RASTAN STARTUP CONFIG`, `WORLD REV1 BASILAN 241`, menu text rows).
- This is not exception-handler register dump text.

# [Cody - Validation Against Spec]

Validated against hard requirements:
- No constant descriptor replacement: PASS
- No fake output injection: PASS
- Opcode/spec-level translation only: PASS
- Reusable translation (table-wide pointer mapping): PASS
- Producer reaches write path (`0x2004A2`): PASS
- Readable game text visible: PASS
- DMA path active with non-zero setup: PASS

Notes:
- In this build family, the live wrapper that calls `0x20034C` is `0x202A4C`; forcing `0x03BD5E -> 0x2027C0` was re-validated and does not reach `0x20034C` here.
- The implemented fix remains strictly descriptor translation path scope (pointer table translation), with no sprite/logo/state-seed widening.
