# Cody - Build 0116 0x0010D000 PC080SN Descriptor Table WRAM Rebase

**Date:** 2026-06-29
**Type:** Implementation + build + validation
**Build produced:** Build 0116
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0116.bin`
**SHA256:** `94f157ecc296cb9e9c2521ec6c3d462671c59dde75d2fe42274508795a4eb30f`
**Scope:** Implement Andy's selected byte-neutral KF-036-class raw arcade work-RAM literal rebase for the proven `0x0010D000..0x0010D0FC` PC080SN descriptor/work page. No KF-038 fix. No helper. No seeded data. No broad RAM mirror. No render-loop raw PC080SN routing.

Address labels:
- `runtime_genesis_pc`: Genesis runtime/file-offset PC
- `arcade_pc`: source arcade code PC, mapped via `build/rastan-direct/address_map.json`
- `Genesis-WRAM`: `0x00FFxxxx`
- `arcade-RAM`: original arcade work RAM addresses
- `HW_ADDRESS`: PC080SN/VDP-like hardware address values such as `0x00C08000`

## Phase 0

Relevant rules read: `RULES.md`, `ARCHITECTURE.md`, and latest `AGENTS_LOG.md` entries. Classification: **EXTENDING** KF-036-class item-page blocker. OPEN-001/OPEN-022/OPEN-023/OPEN-024 context; OPEN-015 context. KF-038 explicitly out of scope.

No contradiction detected before implementation. The selected design was `docs/design/Andy_0010D000_pc080sn_descriptor_table_wram_mapping_design.md`.

## Implementation

Patch shape selected by Andy: direct byte-neutral immediate/absolute operand rebasing.

Mapping applied:

```text
arcade-RAM 0x0010D0xx raw literal operand -> Genesis-WRAM 0x00FF10xx operand
```

This is offset-preserving from KF-036's `0x0010C000 -> 0x00FF0000` mapping. It is not `0x00FFD000`.

Implementation files changed:

- `specs/rastan_direct_remap.json`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

No source `.s` file was modified.

## Site Verification

All 25 requested runtime sites were verified against current `build/genesis_postpatch.disasm.txt` before implementation, then verified again after Build 0116. Each maps through `address_map.json` to the listed `arcade_pc`; no arithmetic offset was used as proof.

| runtime_genesis_pc | arcade_pc | Build 0116 postpatch result |
|---|---|---|
| `0x000505EC` | `0x000503EC` | `movel #0x00C08000,0x00FF10A0` |
| `0x000505F6` | `0x000503F6` | `movel #0x00C00000,0x00FF10F8` |
| `0x00050600` | `0x00050400` | `movel #0x00C08000,0x00FF10A4` |
| `0x0005060C` | `0x0005040C` | `movel #0x00C00000,0x00FF10F8` |
| `0x00050616` | `0x00050416` | `movel #0x00C08000,0x00FF10A0` |
| `0x00050626` | `0x00050426` | `movel %d0,0x00FF10A4` |
| `0x0005062C` | `0x0005042C` | `movew #64,0x00FF10AA` |
| `0x00050644` | `0x00050444` | `subil #16380,0x00FF10A0` |
| `0x0005064E` | `0x0005044E` | `subil #16380,0x00FF10F8` |
| `0x00050668` | `0x00050468` | `subil #16380,0x00FF10F8` |
| `0x00050672` | `0x00050472` | `subqw #1,0x00FF10AA` |
| `0x00050678` | `0x00050478` | `cmpiw #0,0x00FF10AA` |
| `0x000514D2` | `0x000512D2` | `movew 0x00FF10DA,%d6` |
| `0x000514E8` | `0x000512E8` | `movew 0x00FF10DA,%d6` |
| `0x000514FE` | `0x000512FE` | `movew 0x00FF10D8,%d6` |
| `0x0005151C` | `0x0005131C` | `movew 0x00FF10D8,%d6` |
| `0x000528E4` | `0x000526E4` | `clrw 0x00FF10EA` |
| `0x00055AC8` | `0x000558C8` | `moveal #0x00FF1000,%a0` |
| `0x00055AF8` | `0x000558F8` | `movew %d0,0x00FF10A8` |
| `0x00055B04` | `0x00055904` | `moveal #0x00FF1000,%a0` |
| `0x00055B0A` | `0x0005590A` | `moveal #0x00FF1040,%a1` |
| `0x00055B10` | `0x00055910` | `moveal #0x00FF1080,%a2` |
| `0x00055B40` | `0x00055940` | `movew %d0,0x00FF10A8` |
| `0x00055E14` | `0x00055C14` | `moveal #0x00FF10FC,%a0` |
| `0x00055E2E` | `0x00055C2E` | `moveal #0x00FF10FC,%a0` |

## Build / Invariants

Release command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

- Build number: `0116`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0116.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `94f157ecc296cb9e9c2521ec6c3d462671c59dde75d2fe42274508795a4eb30f`
- Numbered and rolling ROMs: byte-identical
- Canonical gate: `GATE_PASS`
- `opcode_replace`: `104 -> 129` (`+25`)
- `total_genesis_bytes_covered`: unchanged at `0x17CF08`
- `postpatch_expected_opcode_replace_sites`: `129`
- `postpatch_expected_total_genesis_bytes_covered`: `0x17CF08`

## Byte Diff Validation

Compared Build 0115 ROM to Build 0116 ROM.

Result: byte diff is restricted to:

- 25 operand high/mid byte pairs: `10D0 -> FF10`
- ROM header checksum at `genesis_rom_offset 0x00018E..0x00018F`: `0x9F4F -> 0xF6A6`

No instruction span changed size. No helper bytes were added. No `HW_ADDRESS` immediate values `0x00C08000` or `0x00C00000` were changed; only the destination/source work-RAM operands were rebased.

Representative postpatch bytes:

```text
0x0505EC: 23FC00C0800000FF10A0  ; #0x00C08000 preserved, slot rebased
0x0505F6: 23FC00C0000000FF10F8  ; #0x00C00000 preserved, slot rebased
0x055B04: 207C00FF1000          ; read base rebased
0x055B0A: 227C00FF1040          ; rebuilt table base rebased
0x055B10: 247C00FF1080          ; copied-word table base rebased
```

## Runtime Validation Artifacts

Build 0116 release smoke trace:

- `states/traces/rastan_direct_video_test_build_0116_mame_30s_20260629_152845/`
- Completed `1798` frames.
- No crash reported in the standard trace.

Targeted validation attempts:

- `states/traces/build_0116_10d000_wram_rebase_validation_20260629_153040/`
- `states/traces/build_0116_10d000_wram_rebase_validation_20260629_153132/`
- `states/traces/build_0116_10d000_wram_rebase_validation_20260629_153609_unconditional/`
- `states/traces/build_0116_10d000_wram_rebase_validation_20260629_154038_itempath/`
- `states/traces/build_0116_10d000_wram_rebase_validation_20260629_154352_console/`

The final targeted run hit `runtime_genesis_pc 0x00055B38` and dumped `Genesis-WRAM 0x00FF1000..0x00FF10BF`:

- `states/traces/build_0116_10d000_wram_rebase_validation_20260629_154352_console/wram_ff1000_table_after_rebuild.bin`

MAME's debugger UI did not capture `printf` event lines in stdout/stderr, but the dump exists only because the `0x55B38` breakpoint fired. Therefore the routine reached `0x55B38`, proving the original `runtime_genesis_pc 0x00055B1A` ADDRESS ERROR did not occur in that run.

## Pointer / Table Gate Result

The mapped source table after the first observed Build 0116 rebuild contains the same **source pointer values** observed in original arcade:

```text
FF1000: 0001691C 00018BDC 0001AE9C 0001D15C
FF1010: 0001F41C 000216DC 0002399C 00025C5C
FF1020: 00027F1C 0002A1DC 0002C49C 0002E75C
FF1030: 00030A1C 00032CDC 00034F9C 0003725C
```

This proves the raw-literal source table now reads from mapped `Genesis-WRAM 0x00FF1000`, not wrapper/ROM bytes such as `0x0000000F`.

However, the table output comparison **does not match original arcade**:

Original arcade output from `docs/design/Cody_build0115_itempage_exit_5591A_a4_provenance_evidence.md`:

```text
arcade-RAM 0x0010D040 rebuilt: 000020FC ... 00002048
arcade-RAM 0x0010D080 words:   0003 ... 0003
```

Build 0116 mapped output:

```text
FF1040: 00002225 00002248 00002248 ...
FF1080: 2024 0013 0013 0013 ...
```

Why: the source pointer table values are still **arcade ROM addresses** such as `0x0001691C`. In the Genesis ROM, copied arcade content is shifted by the JSON-mapped arcade-copy segment; the original arcade bytes for `arcade_pc 0x0001691C` live at `genesis_rom_offset 0x00016B1C`, not `0x0001691C`.

Observed bytes:

```text
Build 0116 genesis_rom_offset 0x0001691C: 20 24 20 25 20 26 05 1C
Build 0116 genesis_rom_offset 0x00016B1C: 00 03 20 FC 00 03 10 00
Original arcade maincpu       0x0001691C: 00 03 20 FC 00 03 10 00
```

So Build 0116 fixes the raw work-RAM table address (`0x0010D000 -> 0x00FF1000`) but exposes the next issue: the **contents** of that table still contain unrelocated arcade ROM source pointers.

## Validation Outcome

Passed:

- Build canonical gate.
- Build 0116 artifact produced.
- `opcode_replace +25`.
- `total_genesis_bytes_covered` unchanged.
- Byte diff restricted to intended operands plus checksum.
- No `0x00C08000` / `0x00C00000` hardware immediate changed.
- `runtime_genesis_pc 0x00055B04..0x00055B46` reached completion at `0x55B38`.
- Original `runtime_genesis_pc 0x00055B1A` odd-address crash is gone in the targeted run.
- `Genesis-WRAM 0x00FF1000` table is populated and no longer reads wrapper/ROM bytes.

Failed / STOP-limited:

- Table outputs at `Genesis-WRAM 0x00FF1040` and `0x00FF1080` do **not** match original arcade rebuild behavior.
- The source pointer values are valid-looking arcade addresses but are not relocated to their Genesis ROM offsets before dereference.
- This means the validation gate uncovered a new data-pointer relocation issue in the table contents. No further fix was attempted because the prompt authorized only the selected `0x0010D0xx -> 0x00FF10xx` work-RAM literal rebase.

## Classification

Implementation result: **partial progress with STOP-limited validation failure**.

The KF-036-class raw work-RAM literal rebase is implemented correctly and clears the immediate wrapper/ROM `%a4=0x0000000F` fault. The next blocker is not KF-038 row aliasing and not the literal WRAM address rebase itself; it is that the table contents still hold original arcade ROM source pointers (`0x0001691C..`) instead of mapped Genesis ROM offsets (`0x00016B1C..`) or an equivalent translated access model.

No fix for that new table-content relocation issue was implemented here.

## Non-Actions

- No source `.s` changes.
- No helper added.
- No seeded/fake table data.
- No broad RAM mirror.
- No KF-038 staging-size/scroll fix.
- No raw PC080SN render-loop routing.
- No sprite/HUD/window work.
- No issue opened or closed.
- No `KNOWN_FINDINGS.md` update in this task.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001: context; item-page progress advanced but output table mismatch remains.
- OPEN-022/OPEN-023/OPEN-024: context; no closure.
- OPEN-015: context; debugger-side/runtime evidence used.
- KF-036: reinforced and implemented for the `0x0010D0xx` raw literal page.
- KF-038: not touched and not contradicted.

## STOP

STOP status: **YES (validation-limited)**.

Reason: the authorized implementation was applied and the original `0x55B1A` ADDRESS ERROR is gone, but the required original-arcade table output comparison fails because the mapped WRAM table contains unrelocated arcade ROM source pointers. Further work needs a new evidence/design pass for that table-content pointer relocation, not another ad hoc patch in this task.
