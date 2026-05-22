# Cody — BM-003 Insert (Positive-Control Validation of bookmarks_v2)

Date: 2026-05-19

## Phase 1 — Target Re-Derivation (not inherited)

### 1.1 BM-002 trace evidence for runtime PC reachability
Source: `dist/rastan-direct/bookmarks/build_0069_pc_0x03A19C/mame_run_log.txt`
Observed `pc=03a19c` hits at lines:
- line 24 (`frame 000180`)
- line 42 (`frame 000330`)
- line 50 (`frame 000420`)
- line 77 (`frame 000720`)
- line 119 (`frame 001110`)
- line 126 (`frame 001200`)
- line 153 (`frame 001500`)

Result: `runtime_genesis_pc 0x0003A19C` is provably executed in BM-002 trace.

### 1.2 Canonical bytes at target offset (Build 0070)
Read from `dist/rastan-direct/rastan_direct_video_test_build_0070.bin` at file offset `0x0003A19C`:
- 16 bytes: `66 f4 2e 78 00 00 20 78 00 04 4e d0 65 02 60 e0`
- first 8 bytes (used for bookmark): `66f42e7800002078`

### 1.3 First-instruction screening (§6.1 workflow)
Disassembly at `0x0003A19C` (Build 0070):
- `66f4  bnes 0x3a192`

First instruction is branch (`BNE.S`) and passes the OPEN-012 first-instruction PC-relative screening for disallowed LEA/JMP PC-relative forms.

### 1.4 span_length choice
Selected `span_length = 8`:
- Activator core is 6 bytes (`4EF9 + helper_addr`)
- One NOP word pad (`4E71`) yields 8-byte overwrite
- Satisfies schema constraints (`>=6`, `(span_length-6)` even)

## Phase 2 — Spec Mutation (`bookmarks_v2` only)
Updated `specs/rastan_direct_remap.json`:
- Added one `bookmarks_v2` entry with:
  - `cycle_id: BM-003`
  - `runtime_genesis_pc: 0x0003A19C`
  - `span_length: 8`
  - `pre_insert_canonical_bytes: 66f42e7800002078`
  - `helper_symbol: genesistan_diag_bookmark`
  - `activator_pattern: JMP_LONG_ABS`
  - `nop_padding_byte: 0x4E71`
  - `pre_insert_canonical_rom_sha256: 72f9f33d...`

Checks:
- No legacy `diagnostic_bookmarks` used
- No `arcade_pc` field in bookmark entry
- `opcode_replace` unchanged at 94 entries

## Phase 3 — Build/Gate/Manifest/State Validation
Command:
- `source tools/setup_env.sh && make -C apps/rastan-direct release`

Build result:
- `GATE_PASS`
- Numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0076.bin`
- build counter advanced `75 -> 76`

Gate/postpatch checks:
- context: `diagnostic`
- `postpatch_expected_opcode_replace_sites: 94`
- `postpatch_expected_total_genesis_bytes_covered: 0x17CAEC`
- `bookmarks_v2_applied[0].runtime_genesis_pc: 0x0003A19C`
- `bookmarks_v2_applied[0].activator_bytes: 4ef900071c784e71`
- state file written at `build/rastan-direct/active_bookmark_baseline.json` with:
  - `cycle_id: BM-003`
  - `pre_insert_canonical_rom_sha256: 72f9f33d...`
  - `pre_insert_build_counter: 75`

ROM integrity checks:
- Build 0076 SHA256: `be6fbef330311a9bfbb9da49a869f925b24a154619709de1515527f8aed102a2`
- Helper bytes at `0x00071C78`: `60fe`
- Helper canonical SHA (`60fe`): `20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb`
- Activator bytes at `0x0003A19C`: `4ef900071c784e71`

## Phase 4 — MAME Trace + Outcome
Trace artifact produced by same make invocation:
- `states/traces/rastan_direct_video_test_build_0076_mame_30s_20260519_142841/genesis_exec_trace.log`
- copied to: `dist/rastan-direct/bookmarks/build_0076_pc_0x0003A19C/mame_run_log.txt`

Currency proof:
- ROM timestamp: `14:28:41 -0400`
- trace timestamp: `14:28:48 -0400`
- same build tag (`0076`) in artifact path

Outcome classification:
- **Outcome A — helper parks**
- Primary evidence: same-run MAME Exit Summary appended by genesistrace reports final PC `0x071C7A` at `2026-05-19 14:28:48`, consistent with helper-loop park after jump to `0x071C78`.
- Sampling caveat: `pc=` lines in sampled trace did not include explicit `071c78/071c7a`, so direct first-arrival frame and sampled hit count are not available from `mame_run_log.txt`.

## Phase 5 — Artifacts
Created:
- `dist/rastan-direct/bookmarks/build_0076_pc_0x0003A19C/insert_meta.txt`
- `dist/rastan-direct/bookmarks/build_0076_pc_0x0003A19C/mame_run_log.txt`
- `dist/rastan-direct/bookmarks/build_0076_pc_0x0003A19C/NOTES.md`

Task boundary:
- BM-003 Insert only.
- No revert performed here.
