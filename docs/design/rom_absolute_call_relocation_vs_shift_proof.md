# rom_absolute_call_relocation vs Accumulated Shift — Proof

## 1. Purpose

Verify the hypothesis that `rom_absolute_call_relocation` applies only base relocation
(`arcade_target + 0x200`) to absolute call addresses embedded in `shift_replacement`
entries, rather than applying `arcade_target + 0x200 + accumulated_shift_at_callsite`.

Three test cases are drawn from Build 273 ROM (`dist/Rastan_273.bin`).
Produced by Andy (verification agent).

---

## 2. Hypothesis

**As stated in task:**

> `rom_absolute_call_relocation` applies: `target = arcade_address + 0x200`
> BUT SHOULD apply: `target = arcade_address + 0x200 + accumulated_shift_at_callsite`

This verification tests whether the actual ROM bytes match `base_only`, `base+shift_at_callsite`,
or a third formula (`base + accumulated_shift_before_target`), which is also examined where evidence
from original unpatched code allows comparison.

---

## 3. Shift Table Reference

All `shift_replacements` entries from `specs/startup_title_remap.json`, sorted by `arcade_pc`.
Sizes: symbols resolve to 6 bytes (opcode 2 + abs_long addr 4).

| arcade_pc  | orig bytes | repl bytes | delta | cumulative |
|------------|-----------|-----------|-------|------------|
| 0x00016A   | 6         | 6         | 0     | 0          |
| 0x000170   | 6         | 6         | 0     | 0          |
| 0x03A20E   | 4         | 6         | +2    | 2          |
| 0x03A264   | 4         | 6         | +2    | 4          |
| 0x03A640   | 4         | 6         | +2    | 6          |
| 0x03A6C4   | 4         | 6         | +2    | 8          |
| 0x03A818   | 6         | 6         | 0     | 8          |
| 0x03A820   | 4         | 6         | +2    | 10         |
| 0x03A854   | 4         | 6         | +2    | 12         |
| 0x03A8E0   | 4         | 6         | +2    | 14         |
| 0x03A9C6   | 4         | 6         | +2    | 16         |
| 0x03A9D4   | 4         | 6         | +2    | 18         |
| 0x03B8E8   | 4         | 6         | +2    | 20         |
| 0x03B8F0   | 4         | 6         | +2    | 22         |
| 0x03C3FE   | 4         | 6         | +2    | 24         |
| 0x041DAE   | 4         | 6         | +2    | 26         |
| 0x041F5E   | 4         | 6         | +2    | 28         |
| 0x045DFA   | 4         | 6         | +2    | 30         |
| 0x055AB4   | 8         | 6         | -2    | 28         |
| 0x055ABC   | 8         | 6         | -2    | 26         |
| 0x055AC4   | 8         | 6         | -2    | 24         |
| 0x055ACC   | 8         | 6         | -2    | 22         |
| 0x059F90   | 2         | 2         | 0     | 22         |

**Accumulated shift before target 0x059F5E** (the producer function, last shift entry before it is
0x055ACC at cumulative 22, then 0x059F90 at cumulative 22):

Entries before 0x059F5E: all entries up to (and including) 0x055ACC.
Entry 0x059F90 is AFTER 0x059F5E, so it is excluded.
Total accumulated shift before 0x059F5E = **22 bytes**.

---

## 4. Test Case 1 — Producer Patch A (Required)

### A. Source

- Spec entry type: `shift_replacement` at `arcade_pc=0x03A8E0`
- Entry introduced by Phase 1 ordering fix (Patch A)
- `replacement_bytes`: `4eb900059f5e` (JSR to arcade address 0x059F5E)
- This is NOT original arcade code — it is a patcher-written replacement.

### B. Accumulated shift before callsite 0x03A8E0

| arcade_pc  | orig | repl | delta | cumulative |
|------------|------|------|-------|------------|
| 0x03A20E   | 4    | 6    | +2    | 2          |
| 0x03A264   | 4    | 6    | +2    | 4          |
| 0x03A640   | 4    | 6    | +2    | 6          |
| 0x03A6C4   | 4    | 6    | +2    | 8          |
| 0x03A820   | 4    | 6    | +2    | 10         |
| 0x03A854   | 4    | 6    | +2    | 12         |

**Accumulated shift before callsite 0x03A8E0: 12 bytes**

### C. Addresses

- Arcade target: `0x059F5E`
- Genesis callsite: `0x03A8E0 + 0x200 + 12 = 0x03AAEC`
- base only: `0x059F5E + 0x200 = 0x05A15E`
- base + shift_at_callsite (12): `0x059F5E + 0x200 + 12 = 0x05A16A`
- base + shift_before_target (22): `0x059F5E + 0x200 + 22 = 0x05A174`

### D. ROM bytes at Genesis 0x03AAEC

```
python3 -c "
import struct
with open('dist/Rastan_273.bin', 'rb') as f:
    f.seek(0x03AAEC)
    data = f.read(6)
print(data.hex())
print(hex(struct.unpack('>I', data[2:])[0]))
"
```

Output:
```
4eb90005a15e
0x5a15e
```

### E. Comparison

- arcade_target: `0x059F5E`
- base (`arcade_target + 0x200`): `0x05A15E`
- accumulated_shift_at_callsite: `12`
- expected per hypothesis (`base + shift_at_callsite`): `0x05A16A`
- actual (ROM bytes): `0x05A15E`
- **actual == base?  YES**
- **actual == expected (hypothesis)?  NO**

### F. ROM content check

Genesis `0x05A15E` bytes: `00 40 00 80 01 20 01 60 99 99 00 25 00 50 01 00`

This is sprite table data, not executable code. The JSR lands in data.

---

## 5. Test Case 2 — Original ROM Callsite at Arcade 0x51266

### A. Source

- Original arcade ROM code (whole_maincpu_copy region), NOT a patched replacement
- Arcade callsite confirmed at `0x51266` by inverting Genesis mapping
- Arcade target: `0x059F5E` (producer function, confirmed: same function as TC1)
  - Evidence: `opcode_replace` entry at `arcade_pc=0x03A8E4` has
    `original_bytes=4eb90005a174`, which equals `0x059F5E + 0x200 + 22`.
    This proves the patcher's relocation of `0x059F5E` reached `0x05A174` for original
    arcade code, confirming `0x059F5E` was the arcade-original call target at `0x03A8E4`.
    The callsite at `0x51266` calls the same producer function.

### B. Accumulated shift before callsite 0x51266

| arcade_pc  | orig | repl | delta | cumulative |
|------------|------|------|-------|------------|
| 0x03A20E   | 4    | 6    | +2    | 2          |
| 0x03A264   | 4    | 6    | +2    | 4          |
| 0x03A640   | 4    | 6    | +2    | 6          |
| 0x03A6C4   | 4    | 6    | +2    | 8          |
| 0x03A820   | 4    | 6    | +2    | 10         |
| 0x03A854   | 4    | 6    | +2    | 12         |
| 0x03A8E0   | 4    | 6    | +2    | 14         |
| 0x03A9C6   | 4    | 6    | +2    | 16         |
| 0x03A9D4   | 4    | 6    | +2    | 18         |
| 0x03B8E8   | 4    | 6    | +2    | 20         |
| 0x03B8F0   | 4    | 6    | +2    | 22         |
| 0x03C3FE   | 4    | 6    | +2    | 24         |
| 0x041DAE   | 4    | 6    | +2    | 26         |
| 0x041F5E   | 4    | 6    | +2    | 28         |
| 0x045DFA   | 4    | 6    | +2    | 30         |

**Accumulated shift before callsite 0x51266: 30 bytes**

### C. Addresses

- Arcade target: `0x059F5E`
- Genesis callsite: `0x51266 + 0x200 + 30 = 0x051484`
- base only: `0x059F5E + 0x200 = 0x05A15E`
- base + shift_at_callsite (30): `0x059F5E + 0x200 + 30 = 0x05A17C`
- base + shift_before_target (22): `0x059F5E + 0x200 + 22 = 0x05A174`

### D. ROM bytes at Genesis 0x051484

```
python3 -c "
import struct
with open('dist/Rastan_273.bin', 'rb') as f:
    f.seek(0x051484)
    data = f.read(6)
print(data.hex())
print(hex(struct.unpack('>I', data[2:])[0]))
"
```

Output:
```
4eb90005a174
0x5a174
```

### E. Comparison

- arcade_target: `0x059F5E`
- base (`arcade_target + 0x200`): `0x05A15E`
- accumulated_shift_at_callsite: `30`
- expected per hypothesis (`base + shift_at_callsite`): `0x05A17C`
- actual (ROM bytes): `0x05A174`
- **actual == base?  NO**
- **actual == expected (hypothesis)?  NO**

### F. ROM content check

Genesis `0x05A174` bytes: `32 3C 00 08 20 7C E0 FF 11 FE 42 80 20 C0 20 C0`

Decoded:
- `32 3C 00 08` = `MOVEW #8, D1`
- `20 7C E0 FF 11 FE` = `MOVEAL #0xE0FF11FE, A0`
- `42 80` = `CLRL D0`
- `20 C0` = `MOVE.L D0, (A0)+`

This is the producer function prologue (clear block-A loop). The relocation is CORRECT
for this callsite — the function is reachable.

---

## 6. Test Case 3 — Original ROM Callsite at Arcade 0x519A0

### A. Source

- Original arcade ROM code (whole_maincpu_copy region)
- Arcade callsite at `0x519A0` (Genesis `0x051BBE`)
- Arcade target: `0x059F5E` (same producer function)

### B. Accumulated shift before callsite 0x519A0

Same entries as TC2 (all entries ≥ 0x045DFA are after 0x45DFA, next is 0x055AB4 which is > 0x519A0):

| arcade_pc  | orig | repl | delta | cumulative |
|------------|------|------|-------|------------|
| 0x03A20E   | 4    | 6    | +2    | 2          |
| 0x03A264   | 4    | 6    | +2    | 4          |
| 0x03A640   | 4    | 6    | +2    | 6          |
| 0x03A6C4   | 4    | 6    | +2    | 8          |
| 0x03A820   | 4    | 6    | +2    | 10         |
| 0x03A854   | 4    | 6    | +2    | 12         |
| 0x03A8E0   | 4    | 6    | +2    | 14         |
| 0x03A9C6   | 4    | 6    | +2    | 16         |
| 0x03A9D4   | 4    | 6    | +2    | 18         |
| 0x03B8E8   | 4    | 6    | +2    | 20         |
| 0x03B8F0   | 4    | 6    | +2    | 22         |
| 0x03C3FE   | 4    | 6    | +2    | 24         |
| 0x041DAE   | 4    | 6    | +2    | 26         |
| 0x041F5E   | 4    | 6    | +2    | 28         |
| 0x045DFA   | 4    | 6    | +2    | 30         |

**Accumulated shift before callsite 0x519A0: 30 bytes**

### C. Addresses

- Arcade target: `0x059F5E`
- Genesis callsite: `0x519A0 + 0x200 + 30 = 0x051BBE`
- base only: `0x059F5E + 0x200 = 0x05A15E`
- base + shift_at_callsite (30): `0x059F5E + 0x200 + 30 = 0x05A17C`
- base + shift_before_target (22): `0x059F5E + 0x200 + 22 = 0x05A174`

### D. ROM bytes at Genesis 0x051BBE

```
python3 -c "
import struct
with open('dist/Rastan_273.bin', 'rb') as f:
    f.seek(0x051BBE)
    data = f.read(6)
print(data.hex())
print(hex(struct.unpack('>I', data[2:])[0]))
"
```

Output:
```
4eb90005a174
0x5a174
```

### E. Comparison

- arcade_target: `0x059F5E`
- base (`arcade_target + 0x200`): `0x05A15E`
- accumulated_shift_at_callsite: `30`
- expected per hypothesis (`base + shift_at_callsite`): `0x05A17C`
- actual (ROM bytes): `0x05A174`
- **actual == base?  NO**
- **actual == expected (hypothesis)?  NO**

### F. ROM content check

Same as TC2: `0x05A174` is the producer function entry (MOVEW #8, D1 / MOVEAL prologue).

---

## 7. Summary Table

| Case | Callsite (arcade) | Target (arcade) | Shift at callsite | Base (target+0x200) | Expected (base+shift_callsite) | Actual (ROM) | Matches Base | Matches Expected |
|------|-------------------|-----------------|-------------------|---------------------|-------------------------------|-------------|--------------|-----------------|
| TC1  | 0x03A8E0 (Patch A shift_replacement) | 0x059F5E | 12 | 0x05A15E | 0x05A16A | **0x05A15E** | **YES** | NO |
| TC2  | 0x51266 (original ROM code) | 0x059F5E | 30 | 0x05A15E | 0x05A17C | **0x05A174** | NO | NO |
| TC3  | 0x519A0 (original ROM code) | 0x059F5E | 30 | 0x05A15E | 0x05A17C | **0x05A174** | NO | NO |

Additional data point:
- Shift before TARGET `0x059F5E` = **22** (from shift table, all entries before 0x059F5E)
- `0x059F5E + 0x200 + 22 = 0x05A174` — matches TC2 and TC3 actual values exactly.

---

## 8. Final Determination

**For shift_replacement entries containing raw arcade addresses in `replacement_bytes` (TC1):**

`rom_absolute_call_relocation` applies `arcade_address + 0x200` only. The accumulated
shift before the callsite (12 bytes in TC1) is NOT applied.

Result at `Genesis 0x03AAEC`: JSR `0x05A15E` — this lands in sprite table data, not the
producer function. The actual function entry is at `0x05A174`.

**For original ROM code copied via `whole_maincpu_copy` (TC2, TC3):**

`rom_absolute_call_relocation` applies `arcade_address + 0x200 + accumulated_shift_before_TARGET`
(not shift at callsite). In TC2 and TC3, the callsite shift is 30 but the target shift is 22.
The actual ROM values match `base + shift_before_target (22)`, not `base + shift_at_callsite (30)`.

**Final determination (restricted to the spec-defined test — shift_replacement Patch A):**

"A rom_absolute_call_relocation applies only base relocation and ignores accumulated shift."

This statement is true specifically for the `shift_replacement` case: the patcher does not apply
any shift delta when relocating arcade addresses embedded in `replacement_bytes`. For original
copied ROM code, a different (target-based) shift formula is applied correctly.

---

## 9. ROM and Spec Files Used

- ROM: `dist/Rastan_273.bin` (3,932,160 bytes, Build 273)
- Spec: `specs/startup_title_remap.json`
- Prior analysis: `docs/design/phase1_runtime_ordering_proof.md`
