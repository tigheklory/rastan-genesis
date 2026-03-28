# Absolute Call Target Fix Plan

## 1. Purpose

Document the design plan for correcting raw-address JSR targets embedded in
`shift_replacements` entries in `specs/startup_title_remap.json`.

The proven issue: when `replacement_bytes` contains a raw 4EB9 + 4-byte arcade address,
`rom_absolute_call_relocation` applies only `arcade_address + 0x200` (base relocation),
not the full `arcade_address + 0x200 + accumulated_shift_before_target`. This causes the
JSR to land at the wrong address in the Genesis ROM.

Produced by Andy (design agent). No implementation performed.

---

## 2. Confirmed Behavior Summary

From `docs/design/rom_absolute_call_relocation_vs_shift_proof.md` (locked context, do not re-prove):

### For `shift_replacement` entries with raw arcade addresses in `replacement_bytes`:

```
actual_target = arcade_address + 0x200          (base relocation only)
correct_target = arcade_address + 0x200 + accumulated_shift_before_target
```

### For original ROM code (whole_maincpu_copy region):

```
actual_target = arcade_address + 0x200 + accumulated_shift_before_target
```

This asymmetry is the root cause of the bug: replacement bytes with embedded raw arcade
addresses receive only base relocation, not the full accumulated-shift relocation that
original ROM code receives automatically.

### Patch A confirmed broken (Build 273):

| Field              | Value                          |
|--------------------|-------------------------------|
| Arcade callsite    | 0x03A8E0                      |
| Genesis callsite   | 0x03AAEC                      |
| Embedded arcade target | 0x059F5E                  |
| ROM actual JSR target  | 0x05A15E (base only)      |
| Correct JSR target     | 0x05A174 (base + shift 22)|
| Content at 0x05A15E    | sprite table data (00 40 00 80...) — NOT executable |
| Content at 0x05A174    | MOVEW #8,D1 / MOVEAL — producer function entry      |

---

## 3. Affected Entries (Full List)

Scan of all `shift_replacements` entries for pattern: `4EB9` followed by 8 raw hex
address bytes, with no `{symbol:...}` substitution.

```python
# Scan script: Task 1
import json, re
with open('specs/startup_title_remap.json') as f:
    spec = json.load(f)
shift_reps = spec.get('shift_replacements', [])
jsr_pattern = re.compile(r'4[Ee][Bb]9([0-9a-fA-F]{8})', re.IGNORECASE)
affected = []
for entry in shift_reps:
    rb = entry.get('replacement_bytes', '')
    if '{symbol:' in rb:
        continue
    m = jsr_pattern.search(rb)
    if m:
        affected.append(entry)
# Total affected: 1
```

### Result: 1 affected entry

| arcade_pc  | replacement_bytes | embedded arcade target |
|------------|-------------------|------------------------|
| 0x03A8E0   | 4eb900059f5e      | 0x059F5E               |

No other `shift_replacements` entries contain raw JSR absolute patterns. All other entries
either use `{symbol:...}` substitution or are non-JSR opcodes (4EF9 is included but those
entries also use `{symbol:...}`).

---

## 4. Per-Entry Analysis

### Entry: arcade_pc = 0x03A8E0 (Patch A)

**Context:** Phase 1 ordering fix. This slot was changed from
`{symbol:genesistan_render_sprites_vdp_bridge}` (renderer) to `4eb900059f5e` (producer JSR)
so that the producer executes before the renderer in the title-init path.

#### Address Computation

| Step                             | Value       |
|----------------------------------|-------------|
| arcade_target (embedded)         | 0x059F5E    |
| base = arcade_target + 0x200     | 0x05A15E    |
| accumulated_shift_before_target  | 22 bytes    |
| correct = base + 22              | **0x05A174**|
| actual ROM (Build 273)           | 0x05A15E    |
| delta (error)                    | -22 (0x16)  |

#### Shift Contributions Before Target 0x059F5E

All entries from `shift_replacements` sorted by `arcade_pc`, contributing to cumulative
shift before 0x059F5E:

| arcade_pc  | orig bytes | repl bytes | delta | cumulative |
|------------|------------|------------|-------|------------|
| 0x03A20E   | 4          | 6          | +2    | 2          |
| 0x03A264   | 4          | 6          | +2    | 4          |
| 0x03A640   | 4          | 6          | +2    | 6          |
| 0x03A6C4   | 4          | 6          | +2    | 8          |
| 0x03A820   | 4          | 6          | +2    | 10         |
| 0x03A854   | 4          | 6          | +2    | 12         |
| 0x03A8E0   | 4          | 6          | +2    | 14         |
| 0x03A9C6   | 4          | 6          | +2    | 16         |
| 0x03A9D4   | 4          | 6          | +2    | 18         |
| 0x03B8E8   | 4          | 6          | +2    | 20         |
| 0x03B8F0   | 4          | 6          | +2    | 22         |
| 0x03C3FE   | 4          | 6          | +2    | 24         |
| 0x041DAE   | 4          | 6          | +2    | 26         |
| 0x041F5E   | 4          | 6          | +2    | 28         |
| 0x045DFA   | 4          | 6          | +2    | 30         |
| 0x055AB4   | 8          | 6          | -2    | 28         |
| 0x055ABC   | 8          | 6          | -2    | 26         |
| 0x055AC4   | 8          | 6          | -2    | 24         |
| 0x055ACC   | 8          | 6          | -2    | 22         |

**Final accumulated shift before 0x059F5E: 22 bytes**

Note: Entry 0x059F90 (at cumulative 22, delta=0) is AFTER 0x059F5E and is excluded.

#### Expected vs Actual

| Formula                                  | Address   | Matches ROM |
|------------------------------------------|-----------|-------------|
| arcade_target + 0x200 (base only)        | 0x05A15E  | YES (wrong) |
| arcade_target + 0x200 + shift_callsite(12) | 0x05A16A | NO        |
| arcade_target + 0x200 + shift_target(22) | 0x05A174  | NO (correct)|

The ROM currently lands at 0x05A15E (data), not 0x05A174 (function entry).

#### Cross-Verification via Patch B

Patch B (`opcode_replace` at arcade_pc `0x03A8E4`) has:
```json
"original_bytes": "4eb90005a174"
```
This is the byte sequence the patcher expects to find in the ROM at that arcade address —
the patcher's own relocation of arcade target `0x059F5E` produced `0x05A174` for original
ROM code. This independently confirms that `0x05A174` is the correct relocated address for
the producer function.

---

## 5. Selected Correction Strategy

**Strategy B: Pre-adjust `replacement_bytes` to embed the correct pre-relocated genesis address.**

### Justification

Strategy A (symbol-based) was evaluated and rejected:

- The producer function at arcade `0x059F5E` / genesis `0x05A174` is pure arcade ROM code
  residing in the `whole_maincpu_copy` region. It has no `genesistan_` symbol in the
  linker output (`apps/rastan/out/symbol.txt`).
- Creating a named symbol for this function would require adding a C declaration or wrapper
  in `startup_bridge.c`, which is prohibited by the design-only constraint of this task.
- There is no existing `{symbol:...}` name that resolves to `0x05A174`.

Strategy B is viable and consistent with the existing system:

- The correct genesis address for the producer is `0x05A174`. This is a stable value:
  the shift table shows exactly 22 bytes of accumulated shift before `0x059F5E`, and this
  value is confirmed by two independent callsites (TC2 at `0x051484`, TC3 at `0x051BBE`)
  and by Patch B's own `original_bytes`.
- The fix changes only the 4 address bytes embedded in `replacement_bytes` from
  `00059f5e` to `0005a174`. The entry size (6 bytes) does not change.
- Because the size does not change, the shift delta of Patch A (+2) is unaffected. The
  accumulated shift calculation for all subsequent entries remains unchanged.
- `rom_absolute_call_relocation` is bypassed for this specific address because Strategy B
  embeds the final genesis address directly — no relocation needed for those 4 bytes.

**Note for implementer (Cody):** When `rom_absolute_call_relocation` processes this entry
after the fix, it will encounter `0x0005a174` in the replacement bytes and attempt to
relocate it again. If it does, the result will be wrong. Verify after build that the ROM
at `0x03AAEC` reads `4eb9 0005a174` and not `4eb9 0005a374` or similar. If
`rom_absolute_call_relocation` is re-applying +0x200 to the already-relocated value, a
note to the patcher to skip this entry's address bytes may be needed. However, the proof
in TC1 shows that for shift_replacement entries, `rom_absolute_call_relocation` applies
ONLY +0x200 (base) to embedded raw addresses. So if we embed `0x0005a174`, the patcher
will compute `0x0005a174 + 0x200 = 0x0005a374`, which is WRONG.

**Revised analysis — correct approach:**

Because `rom_absolute_call_relocation` WILL apply +0x200 to whatever raw address is
embedded in `replacement_bytes` of a shift_replacement entry, we cannot simply embed
`0x05A174` directly. The patcher will add another 0x200 to it.

To produce the correct output `0x05A174`, we must embed the pre-compensation value:

```
embedded_value = correct_genesis_addr - 0x200
embedded_value = 0x05A174 - 0x200 = 0x059F74
```

Wait — but that is NOT what TC1 shows. TC1 shows:
- embedded: `0x059F5E`
- ROM output: `0x05A15E` = `0x059F5E + 0x200`

This confirms: patcher adds exactly +0x200 to whatever is embedded. It does NOT add
accumulated shift. So to get ROM output `0x05A174`:

```
embedded_value = 0x05A174 - 0x200 = 0x059F74
replacement_bytes = 4eb900059f74
```

**This is the correct replacement_bytes for Patch A.**

Verification:
- embedded: `0x059F74`
- patcher applies +0x200: `0x059F74 + 0x200 = 0x05A174`
- ROM output: `4eb9 0005a174` — JSR to producer function entry. CORRECT.

Cross-check: `0x059F74 = 0x059F5E + 0x16 = 0x059F5E + 22 = arcade_target + shift_before_target`

So the correct formula for the embedded value is:
```
embedded_value = arcade_target + accumulated_shift_before_target
              = 0x059F5E + 22
              = 0x059F74
```

This makes intuitive sense: embed the arcade address pre-adjusted by the shift that the
patcher would have applied if this were original ROM code, so that when the patcher adds
its base +0x200, the result is the correct genesis address.

---

## 6. Spec Patch Plan

### Entry: arcade_pc 0x03A8E0

**BEFORE:**
```json
{
  "arcade_pc": "0x03A8E0",
  "original_bytes": "61001020",
  "replacement_bytes": "4eb900059f5e",
  "note": "..."
}
```

**AFTER:**
```json
{
  "arcade_pc": "0x03A8E0",
  "original_bytes": "61001020",
  "replacement_bytes": "4eb900059f74",
  "note": "ORDER FIX PATCH A: producer (0x059F5E) runs at this slot (before renderer at 0x03A8E4). Embedded value 0x059F74 = arcade_target(0x059F5E) + shift_before_target(22). rom_absolute_call_relocation adds +0x200 to yield genesis 0x05A174 (producer function entry). Size: 4->6 bytes (+2 shift, unchanged)."
}
```

**Key values:**

| Field                        | Value        |
|------------------------------|--------------|
| arcade_target (function)     | 0x059F5E     |
| accumulated_shift_before     | 22 (0x16)    |
| pre-adjusted embedded value  | 0x059F74     |
| patcher adds +0x200          | 0x05A174     |
| ROM output (expected)        | 4eb90005a174 |
| ROM output (current, broken) | 4eb90005a15e |
| Entry size: orig / repl      | 4 / 6 bytes (no change) |
| Shift delta                  | +2 (no change) |

**No change to entry size, no cascading shift effects.**

---

## 7. Validation Plan

### 7.1 Static Check (post-build)

After rebuilding with the corrected `replacement_bytes`:

1. Locate the callsite in the ROM. Genesis address of arcade 0x03A8E0:
   ```
   genesis_addr = 0x03A8E0 + 0x200 + 12 (shift_before_callsite) = 0x03AAEC
   ```
2. Read 6 bytes at ROM offset `0x03AAEC`:
   ```python
   import struct
   with open('dist/Rastan_NNN.bin', 'rb') as f:
       f.seek(0x03AAEC)
       data = f.read(6)
   print(data.hex())
   # Expected: 4eb90005a174
   # Wrong (current): 4eb90005a15e
   ```
3. Confirm decoded target = `0x05A174`.
4. Read 6 bytes at ROM offset `0x05A174` and confirm they decode to the producer prologue:
   ```
   Expected: 323c0008 207ce0ff11fe ...
   (MOVEW #8,D1 / MOVEAL #0xE0FF11FE,A0)
   ```
5. Confirm Patch B at `0x03AAF2` is still `4eb900202b80` (renderer bridge, unchanged).

### 7.2 Runtime Check

Using the Genesis MAME harness (`tools/mame/run_genesis_trace_wsl.sh`) with a Lua probe:

1. Install taps at:
   - `0x05A174` — producer function entry (the fix target; should now fire)
   - `0x05A15E` — old wrong target (should NOT fire after fix)
   - `0x202B80` — genesistan_render_sprites_vdp_bridge (renderer)
   - `0x03AAEC` — callsite A (producer slot)
   - `0x03AAF2` — callsite B (renderer slot)

2. Navigate to a frame where callsite A is hit.

3. Ordering assertion: within any single execution pass through the 0x03AAEC/0x03AAF2 pair:
   - `0x03AAEC` fires before `0x03AAF2` (callsite ordering — already correct in Build 273)
   - `0x05A174` fires after `0x03AAEC` and before `0x03AAF2` (producer executes correctly)
   - `0x05A15E` does NOT fire (old wrong target no longer reached)

4. Pass/fail criterion:
   ```
   PASS: tap 0x05A174 fires, tap 0x05A15E does NOT fire
   FAIL: tap 0x05A15E fires, tap 0x05A174 does NOT fire
   ```

### 7.3 Descriptor Check

After the fix, the producer at `0x05A174` runs correctly. Its expected behavior
(from AGENTS_LOG and phase1_execution_results.md):

- Clears block-A (8 longs at `0xE0FF11FE`) to zero
- Writes 4 initial B-block entries (`0x0080, 0, 0, 0` each) at `0xE0FF01BC`

Descriptor probe (at renderer bridge `0x202B80` entry, second pass):

```
block-B (0xFF01BC..0xFF01C2): 0080 0000 0000 0000
```

This is the same block-B state already observed in Build 273 at seq=046. However, the
key distinction after the fix:

- In Build 273 (broken): block-B has 0x0080 because execution drifted from data at
  `0x05A15E` to land at `0x05A174` via accidental context (A5 changes between seq=043
  and seq=044 in the proof trace show this was a coincidental hit, not the intended call).
- After fix: `0x05A174` is called directly and intentionally. The A5 context at
  `0x05A174` should match the context of the callsite (`A5=E0FF004C`) rather than
  showing a context switch (as observed in Build 273 where A5 changed to `E0FF004B`).

Verification: confirm A5 at the `0x05A174` tap matches A5 at the `0x03AAEC` callsite tap
(same frame, same A5 value — no context drift).

---

## 8. Summary

| Field                  | Value                              |
|------------------------|------------------------------------|
| Affected entries       | 1 (arcade_pc 0x03A8E0)             |
| Root cause             | rom_absolute_call_relocation applies +0x200 only to raw addresses in shift_replacement replacement_bytes |
| Correct formula        | embedded = arcade_target + shift_before_target; patcher adds +0x200 to yield genesis addr |
| Current embedded value | 0x059F5E (wrong)                   |
| Correct embedded value | 0x059F74 (= 0x059F5E + 22)         |
| ROM output (current)   | JSR 0x05A15E (sprite data — wrong) |
| ROM output (after fix) | JSR 0x05A174 (producer entry — correct) |
| Entry size change      | None (6 bytes both ways)           |
| Shift table impact     | None                               |
| Strategy               | B — pre-adjust embedded address    |
| Files to modify        | specs/startup_title_remap.json only (one field, one entry) |
