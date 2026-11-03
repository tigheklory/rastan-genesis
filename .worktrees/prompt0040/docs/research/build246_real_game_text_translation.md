# Build 246 - Real Game Text Translation (Title/Attract Path)

## Objective
Implement the first real game text translation slice on the title/attract producer path (not launcher/exception text), using opcode/spec patching only.

Tested artifact:
- `dist/Rastan_246.bin`
- sha256: `771b747b7cc45b9de8489c9c251ff5d22c66fd57fac5d07e83761321d53831d0`

## A) Real Game Title Text Records (from producer table)
Producer table consumed by `0x20034C` (runtime table base `0x03BD92`, 22 entries):
- Entry 2: `CREDIT   `
- Entry 12: `@ TAITO AMERICA CORP. 1987`
- Entry 20: `R A S T A N`

Requested strings mapping status in this table:
- `TAITO`: present (entry 12 contains TAITO in copyright line).
- `copyright`: present (entry 12).
- `CREDIT 0`: partial (`CREDIT   ` in this table; numeric suffix not present in same record).
- `1UP`, `HIGH SCORE`, `2UP`: not present as plain ASCII records in this table (likely produced by other title path assets/producers).

First real game text record reached in execution order for this run:
- selector `D0=2` -> entry 2 -> `CREDIT   `

Live proof:
- `/tmp/build243_real_text_probe.txt`: `CALL01 ... d0=2 ... text=CREDIT   `

## B) Descriptor Semantics (first reached record)
First reached descriptor (`CREDIT   `):
- Source descriptor (arcade maincpu):
  - ptr `0x03BCBE`
  - `D6` field: `0x00C09E84`
- Translated runtime descriptor (Build 246):
  - ptr `0x03BED4`
  - `D6` field: `0xE1000126`

Field meaning used by `0x20034C`:
- `+0x00..+0x03` (`D6`): destination cursor/command base for write path
- `+0x04..+0x05` (`D3`): mode/attr word
- `+0x06..` bytes: text payload until `0x00`

Why prior path failed:
- stale/untranslated destination semantics produced reject/non-productive path at producer checks.

## C) Reusable Translation Rule
Applied rule (table-wide, not single-record constant hack):
- pointer-table relocation with shift-aware target fixups for all 22 entries
- descriptor destination window mapping from arcade C-window semantics to Genesis runtime-visible destination window

Rule form:
- `arcade descriptor D6 in 0x00C00000..0x00CFFFFF`
- `-> translated D6 in active Genesis runtime window (E0FF.../E100...)`

This was applied as table/range translation, not a one-record hardcoded destination replacement.

## Implementation Changes
1) Title dispatch target path (spec opcode):
- `0x03BB48` replacement remains `jsr 0x2027C0; rts` (`rom pc 0x03BD5E`).

2) Runtime ROM opcode replacement support (spec-driven):
- added `rom_opcode_replace` handling in `tools/translation/postpatch_startup_rom.py`.
- Build 246 spec patch at fixed ROM site:
  - `rom_pc 0x2027C0`
  - before: `32DA720070001018`
  - after:  `4EB90020034C4E75`

This keeps the locked dispatch target (`0x2027C0`) while resolving it to the text producer path in this build layout.

## Required Proof
### 1) Execution proof
From `/tmp/build243_real_text_probe.txt` on `dist/Rastan_246.bin`:
- `HIT 03BD5E 1`
- `HIT 2027C0 1`
- `HIT 20034C 1`
- productive site hit: `HIT 2004A2 9`

### 2) Descriptor proof
For first reached record (`selector=2`):
- original descriptor ptr/value: `0x03BCBE`, `D6=0x00C09E84`
- translated descriptor ptr/value: `0x03BED4`, `D6=0xE1000126`
- first call proof: `CALL01 ... d0=2 ... ptr=0003BED4 ... text=CREDIT   `

### 3) Producer payload proof
From `/tmp/build246_2004a2_values.txt`:
- `0x2004A2` writes non-space tile words: `0014 0015 0016 0017 0018 0019 001A 001A 001A`
- count: `9`

### 4) Buffer / game-path proof
- Real game producer path is active (`0x03BD5E -> 0x2027C0 -> 0x20034C -> 0x2004A2`).
- text-shadow non-space remains `0/256` for this run (`/tmp/build243_real_text_probe.txt`) because this producer writes directly via VDP port path (`0xC00004/0xC00000`) rather than populating the shadow window.

### 5) VRAM / visibility proof
- VDP port write activity is present:
  - `vdp_data_writes=23612`
  - `vdp_ctrl_writes=13707`
- CRAM hard evidence (started game path):
  - `/tmp/build246_palette_probe.txt`
  - frame 650: `cram_nonzero=0/64`
  - frame 800: `cram_nonzero=0/64`

Visual captures:
- pre-exception started game frame: `docs/research/artifacts/build246_preexception_black.png`
- later exception frame: `docs/research/artifacts/build246_exception_frame.png`
- launcher reference (invalid proof): `docs/research/artifacts/build246_launcher_invalid_reference.png`

## Why This Is Not Launcher/Exception Proof
- Launcher/config text appears only in no-start launcher capture and is explicitly invalid for success.
- Started-path run with producer activity still shows black pre-exception frame, then exception text.
- Therefore this pass does **not** claim launcher/exception text as success.

## Result Classification
Status: **PARTIAL IMPLEMENTATION - NOT COMPLETE**

What is now fixed:
- first real producer call chain executes through locked dispatch target and reaches productive writer site (`0x2004A2`).
- descriptor semantics translation is applied for the first reached record (`CREDIT`).

What is still blocking visible real title/attract text:
- started-path CRAM remains all-zero (`0/64` nonzero), so pre-exception output remains black even with producer writes.
- real game title/attract text is still not visible before exception handling.

## Remaining Issues (next pass)
- restore/translate palette ownership for started title/attract render path so CRAM is non-zero before text writes.
- validate first visible title/attract frame against arcade reference text set (`1UP`, `HIGH SCORE`, `2UP`, `TAITO`, copyright, `CREDIT 0`).
- then re-run visual proof to confirm non-launcher, pre-exception game text visibility.
