# Text Record Rejection Point

## Section 1 - Full Internal Path Trace
Trace source: `/tmp/text_record_branch_trace.txt` on `/tmp/r235_target_2027c0.bin`.

Decision path for the single `0x20034C` invocation (`frame=666`) is:

1. `PC=0x20036A` `bne.s 0x200372`
- Relevant state: `A2=0x0003BCBE` (from `0x200362`), non-zero.
- Branch: **TAKEN**.
- Why: descriptor pointer is non-null.

2. `PC=0x200380` `bne.s 0x200398`
- Relevant state: `D0(word)=0x0000` after `move.w 0xE0FF6B3C,D0` (`seq=0018`).
- Branch: **NOT taken** (falls to `0x200382`).
- Why: zero flag set from `D0(word)==0`.

3. `PC=0x200394` `beq.w 0x2005F6`
- Relevant state: `D0(word)=0x0001` (`seq=0021`).
- Branch: **NOT taken** (falls to `0x200398`).
- Why: zero flag clear (`D0(word)!=0`).

4. `PC=0x20039A` `beq.w 0x2004B2`
- Relevant state: first text byte already loaded as `D1=0x0000000D` (`seq=0024`).
- Branch: **NOT taken**.
- Why: first code byte is non-zero.

5. `PC=0x2003A6` `bmi.w 0x2004E6`
- Relevant state: `D4=0x0002` (`seq=0026`, sign bit clear).
- Branch: **NOT taken**.
- Why: positive/non-negative mode path.

6. Loop body decision A (executed 156 times): `PC=0x2003E0` `bls.s 0x200406`
- First-iteration state: `D7=0x0A4A8F0C` (`seq=0030`).
- Branch count evidence: `HIT 2003E0 = 156`, `HIT 200406 = 0`.
- Branch: **NOT taken (all 156)**.
- Why: `D7` is not `<= 0x00007FFF`.

7. Loop body decision B (executed 156 times): `PC=0x2003EC` `bhi.w 0x2004AA`
- First-iteration state: `D6=0x0B0B0F0C`, `D0=0xE0FFC84C` (`seq=0032`).
- Branch count evidence: `HIT 2003EC = 156`, `HIT 2003F0 = 0`, `HIT 2004AA = 156`.
- Branch: **TAKEN (all 156)**.
- Why: unsigned compare result indicates `D0 > D6` every iteration, so each character path is rejected before `0x20040E..0x2004A2`.

8. Loop continuation: `PC=0x2004AE` `bne.w 0x2003D2`
- Branch count evidence: `HIT 2004AE = 156`, `HIT 2003D2 = 156`.
- Branch: **TAKEN 155 times, NOT taken once**.
- Why: non-zero text bytes continue loop; final byte at `A2=0x3BD60` is `0x00` (`seq=1268..1276`), ending loop.

9. Post-loop exit: `PC=0x2004B8` `bne.w 0x20036C`
- Relevant state: `D0(word)=0x0000` at this check (`seq=1278`).
- Branch: **NOT taken**.
- Why: `0xE0FF6B3C` word is zero.

10. Final return gate: `PC=0x2004CA` `bne.w 0x20036C`
- Relevant state: after decrement, `D0(word)=0x0001` (`seq=1280`).
- Branch: **TAKEN** to `0x20036C`, then `0x200370` return.
- Why: non-zero countdown forces immediate return path.

Return observed:
- `CALL_END ... pc=0x200370 ... d6=0x0B0B117C a2=0x0003BD61`.

## Section 2 - Descriptor Analysis
Locked invocation inputs:
- selector `D0=0x0002`
- table base `0x0003BD92`
- resolved descriptor pointer `0x0003BCBE`

Table proof (`od` at `0x3BD92`):
- entry0: `0x0003BC98`
- entry1: `0x0003BCA6`
- entry2: `0x0003BCBE`  <- selected by `D0=2`

Descriptor bytes at `0x3BCBE` (first record and continuation):
- `0x3BCBE: 0B 0B 0F 0C 12 10 ...`

Decoded record fields used by `0x20034C`:
- `+0x00..+0x03` long -> `D6 = 0x0B0B0F0C` (destination base used in per-character position checks)
- `+0x04..+0x05` word -> `D3 = 0x1210` (attribute/mode bits)
- `+0x06..` byte stream -> character codes (`0x0D, 0x18, 0x0B, ...`), terminated by `0x00` at `0x3BD60`

Checks applied by `0x20034C` to this record:
- null descriptor check (`0x200366/0x20036A`)
- mode/guard checks (`0x200380`, `0x200394`, `0x20039A`, `0x2003A6`)
- per-character range/alignment checks before write path (`0x2003E0`, `0x2003EC`, `0x2003F8`, `0x20040A`)

Field/value that causes non-productive behavior:
- `D6` from descriptor longword (`0x0B0B0F0C`) is outside expected drawable destination range for this path, causing immediate rejection at `0x2003EC` on every character.

## Section 3 - Exact Rejection Point
=== TEXT_RECORD_REJECTION_POINT ===
- producer_entry: `0x20034C`
- descriptor_ptr: `0x0003BCBE`
- rejecting_pc: `0x2003EC`
- rejecting_condition: `bhi.w 0x2004AA` after `cmp.l %d6,%d0` (with `D0 = 0xE0FFC84C` baseline)
- descriptor_value_involved: descriptor `+0x00..+0x03` -> `D6 = 0x0B0B0F0C`
- expected_value_for_productive_path: `D6 >= 0xE0FFC84C` (and subsequent upper/alignment checks must also pass)
- actual_value_seen: `0x0B0B0F0C` (first loop), then `+4` stride values, all still far below `0xE0FFC84C`

## Section 4 - Root Cause Classification
Selected classification: **wrong descriptor contents**.

Proof:
- Selector and table resolution are consistent (`D0=2` resolves to table entry `0x3BCBE` from `0x3BD92`).
- Branch opcode behavior is internally consistent (`0x2003EC` taken 156/156; `0x2003F0` never reached).
- Rejection is driven by descriptor-derived `D6` value (`0x0B0B0F0C` series), not by wrapper entry, selector mismatch, or an inverted branch condition.

## Section 5 - Conclusion
0x20034C rejects the text record at `0x2003EC` because descriptor `D6` (`0x0B0B0F0C`-series) fails the destination-range compare against `0xE0FFC84C`, so execution returns before reaching `0x2004A2`.
