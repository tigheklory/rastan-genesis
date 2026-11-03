# Multi-Pass Operand Relocation Design

Produced by Andy (design agent). No implementation performed.

---

## 1. Purpose

The current patcher applies structural layout changes (insertions, deletions, replacements)
and absolute-address relocation in a single combined pass. This works correctly for original
ROM code in the `whole_maincpu_copy` region: those callsites receive
`target = arcade_target + 0x200 + accumulated_shift_before_target`. However, it breaks for
`shift_replacement` entries whose `replacement_bytes` contain raw embedded arcade addresses:
those entries receive only `target = arcade_target + 0x200` (base relocation only), because
the patcher processes replacement bytes without the benefit of a completed, final shift table.

This document defines the preferred long-term architecture: a two-pass system that separates
structural layout changes from operand relocation, preserving original arcade addresses as
the durable source of truth.

---

## 2. Current Pipeline Limitations

### 2.1 Why raw `replacement_bytes` with embedded addresses are brittle

When a `shift_replacement` entry contains raw opcode bytes with an embedded arcade address
(e.g., `4eb900059f5e`), the embedded address is a hard-coded numeric value. Its correct
Genesis translation is `arcade_target + 0x200 + shift_before(arcade_target)`, where
`shift_before(arcade_target)` is the sum of all net size deltas from shift_replacement
entries whose `arcade_pc` is less than the target address. This accumulated shift value
changes whenever any shift_replacement entry before the target is added, removed, or
resized. A raw embedded hex value cannot automatically track these changes. Every time
the shift table is modified — for example, when new graphics hooks are added or existing
ones are resized — any entry with a raw embedded address silently becomes stale and will
produce the wrong Genesis address at the callsite. Build 273 is a concrete example: Patch A
at arcade 0x03A8E0 embeds target `0x059F5E`, the patcher adds only +0x200, and the
resulting JSR lands at 0x05A15E (sprite table data) instead of 0x05A174 (the producer
function entry). The shift before target 0x059F5E is 22 bytes; that value is not reflected
in the raw bytes.

### 2.2 Why Strategy B (one-entry pre-compensation) is not durable

Strategy B (from `docs/design/absolute_call_target_fix_plan.md`) proposes changing the
embedded value from `0x059F5E` to `0x059F74` (= arcade_target + shift_before_target) so
that when the patcher adds +0x200, the result is the correct `0x05A174`. This compensates
for the current shift table state but it is a snapshot fix. If any shift_replacement entry
before arcade address `0x059F5E` is later added, removed, or resized, the accumulated
shift before the target changes and `0x059F74` becomes wrong again. Every such change
would require a manual re-scan and re-derivation of the embedded value. As more graphics
patches are added (Phase 2 and beyond), the shift table will grow and this maintenance
burden compounds. The embedded value `0x059F74` has no self-describing provenance in the
spec: a future reader cannot recover the original arcade address `0x059F5E` from it without
reverse-engineering the delta. Strategy B is appropriate as an immediate fix for Build 273
but must be superseded by a durable architecture.

### 2.3 What `rom_absolute_call_relocation` handles correctly

The `rom_absolute_call_relocation` block in `startup_title_remap.json` scans the
`whole_maincpu_copy` region for all opcode/operand patterns listed in
`opcodes_with_abs_long_operand` and rewrites each embedded absolute long address using
`target = arcade_address + 0x200 + accumulated_shift_before_target`. Test cases TC2
and TC3 in `docs/design/rom_absolute_call_relocation_vs_shift_proof.md` confirm this:
the callsite at arcade 0x51266 calls arcade target 0x059F5E and the patcher writes
`0x05A174` (= `0x059F5E + 0x200 + 22`). Original copied ROM code is handled correctly
because the patcher has the completed shift table when it does this scan and applies the
formula correctly for every opcode class listed.

### 2.4 What `rom_absolute_call_relocation` does NOT handle

`rom_absolute_call_relocation` does not cover `shift_replacement` entries where
`replacement_bytes` contain synthetic patcher-authored bytes with raw embedded arcade
addresses. These entries are not part of the scanned `whole_maincpu_copy` region — they
are explicit override patches that the patcher writes directly. When the patcher writes
such an entry, it applies +0x200 (base relocation) to any embedded address it detects but
does not apply `accumulated_shift_before_target`. The result is that any embedded arcade
address in a `shift_replacement` entry will be under-relocated by exactly the value of
`shift_before(target)` at the time of the build. This class of error cannot be fixed by
tuning `rom_absolute_call_relocation` alone; it requires a separate post-layout operand
resolution pass.

---

## 3. Preferred Multi-Pass Architecture

### Overview

Separate the build process into two conceptually distinct passes:

- **Pass A** (structural): all insertions, deletions, and replacements are applied; the
  final ROM layout is computed; the cumulative shift at every arcade address position is
  known and stable.
- **Pass B** (deferred operand rewrite): for entries flagged with `relocate_after_shift`,
  the correct final Genesis operand value is computed using the formula
  `final_operand = operand_arcade_target + 0x200 + shift_before(operand_arcade_target)`,
  and the operand bytes at the callsite are overwritten in the output ROM.

The two passes do not compete. Pass A never embeds a raw arcade address in an entry that
will be later fixed by Pass B: entries needing deferred relocation carry only metadata in
the spec (template opcode + source-of-truth arcade address), not raw numeric operand bytes.
Pass B reads the final shift table produced by Pass A and derives the correct operand value
fresh on every build. No hardcoded Genesis addresses appear in the spec.

### Pass A — Structural Patching

Input: spec entries of all kinds (shift_replacements, opcode_replace, etc.)

Actions:
1. For each shift_replacement entry, write `replacement_bytes` at the callsite, expanding
   or contracting the ROM as needed.
2. For each opcode_replace entry, overwrite the exact byte range at the callsite with
   `replacement_bytes` (no size change).
3. Apply `rom_absolute_call_relocation` over the `whole_maincpu_copy` region using the
   now-complete shift table.
4. Record final cumulative shift at every arcade address position for use by Pass B.

Output: a ROM with correct layout for all non-deferred entries; a finalized shift table.

### Pass B — Deferred Operand Relocation

Input: the Pass A output ROM; the finalized shift table; all spec entries with
`"relocate_after_shift": true`.

Actions: for each such entry:
1. Compute `shift_before_target = cumulative_shift_up_to(operand_arcade_target)` from the
   finalized shift table.
2. Compute `final_operand = operand_arcade_target + 0x200 + shift_before_target`.
3. Locate the callsite in the output ROM:
   `genesis_callsite = arcade_pc + 0x200 + shift_before(arcade_pc)`
4. Write the `replacement_template` opcode bytes followed by the `final_operand` (encoded
   per `operand_kind`, big-endian) at `genesis_callsite`.
5. Emit a relocation report entry for this operand (see Section 8).

Output: a ROM where all deferred operand entries contain the correct final Genesis addresses.

### Why this separation is the core insight

Pass A finalizes the shape of the ROM. Pass B reads that final shape to compute operand
values. Because Pass B always recomputes from the current shift table, adding or removing
any shift_replacement entry before `operand_arcade_target` automatically produces the
correct new `final_operand` on the next build. No spec value goes stale. The original
arcade address stored in `operand_arcade_target` is the only value that must be manually
maintained, and it is stable as long as the original arcade ROM function does not move.

---

## 4. Spec Format Proposal

### Required fields for a deferred-operand entry

| Field | Type | Description |
|---|---|---|
| `arcade_pc` | hex string | Callsite location in arcade address space. Source of truth for where to apply the patch. |
| `original_bytes` | hex string | Original bytes at the callsite in the arcade ROM. Used for patch verification. |
| `replacement_template` | hex string | Opcode bytes only, without the operand (e.g., `4EB9` for JSR abs.l). |
| `operand_kind` | string | Operand encoding type (e.g., `abs_l_32bit`). Tells Pass B how to encode and write the final operand. |
| `operand_arcade_target` | hex string | Original arcade address of the target. This is the source of truth; never a derived or pre-shifted value. |
| `operand_width` | integer | Width in bytes of the operand field (e.g., 4 for abs.l). |
| `relocate_after_shift` | boolean | When true, this entry is deferred to Pass B. Pass A writes the template only (or skips this callsite); Pass B fills in the operand. |
| `opcode_class` | string | Optional. Human-readable coverage label (e.g., `jsr_abs_l`). Used for audit and reporting. |
| `note` | string | Optional. Human-readable annotation. |

### Concrete example: Patch A

Patch A is the Phase 1 ordering fix: at arcade callsite 0x03A8E0 (a 4-byte BSR that was
replaced with a 6-byte JSR to the sprite producer function at arcade 0x059F5E).

```json
{
  "arcade_pc": "0x03A8E0",
  "original_bytes": "61001020",
  "replacement_template": "4EB9",
  "operand_kind": "abs_l_32bit",
  "operand_arcade_target": "0x059F5E",
  "operand_width": 4,
  "relocate_after_shift": true,
  "opcode_class": "jsr_abs_l",
  "note": "ORDER FIX PATCH A: producer (0x059F5E clear+B-block-init) runs first at this slot. Size: 4->6 bytes (+2 shift). Pass B computes final_operand = 0x059F5E + 0x200 + shift_before(0x059F5E) = 0x05A174 and writes 4EB9 0005A174 at genesis callsite 0x03AAEC."
}
```

Pass B resolution for this entry (current shift table, 22 bytes before 0x059F5E):
```
shift_before(0x059F5E) = 22
final_operand = 0x059F5E + 0x200 + 22 = 0x05A174
genesis_callsite = 0x03A8E0 + 0x200 + 12 = 0x03AAEC
ROM output at 0x03AAEC: 4E B9 00 05 A1 74
```

If a new shift_replacement entry adding +2 bytes is later inserted before 0x059F5E:
```
shift_before(0x059F5E) = 24  (automatically updated)
final_operand = 0x059F5E + 0x200 + 24 = 0x05A176
ROM output: 4E B9 00 05 A1 76
```

No spec edit required. The entry's `operand_arcade_target` remains `"0x059F5E"` and is
always correct.

---

## 5. Opcode Class Coverage

The existing `rom_absolute_call_relocation` already handles all of these opcode classes for
**original ROM code** in the `whole_maincpu_copy` region. The question for the new Pass B
is whether it needs to handle them for **patcher-authored replacement entries** with
embedded absolute long operands that should be deferred.

| Opcode/Class | Encoding | Operand Type | Should New Pass Handle? | Why |
|---|---|---|---|---|
| JSR abs.l | 4EB9 + 32-bit | abs_l_32bit | Yes | Most common patcher hook injection; Patch A is exactly this case. Original ROM: already handled by rom_absolute_call_relocation. |
| JMP abs.l | 4EF9 + 32-bit | abs_l_32bit | Yes | Used for entry-point redirections (e.g., 0x03C3FE, 0x041DAE, 0x041F5E, 0x045DFA in current spec). If any of these ever point to an arcade ROM target rather than a genesistan_ symbol, Pass B must handle it. Original ROM: handled by rom_absolute_call_relocation. |
| LEA abs.l, An | 41F9/43F9/45F9/47F9/49F9/4BF9/4DF9/4FF9 + 32-bit | abs_l_32bit | Yes | Used to load absolute ROM or RAM addresses into address registers. If a replacement entry embeds an arcade address in LEA form, Pass B must relocate it. Original ROM: handled by rom_absolute_call_relocation (all LEA An encodings are listed in opcodes_with_abs_long_operand). |
| MOVEA.l #imm, An | 207C/227C/247C/267C/287C/2A7C/2C7C/2E7C + 32-bit | abs_l_32bit | Yes | Used to load absolute addresses into address registers (MOVEA.l form). Same rationale as LEA. All listed in opcodes_with_abs_long_operand. Original ROM: handled. |
| PEA abs.l | 4879 + 32-bit | abs_l_32bit | Yes | Used to push absolute long addresses onto the stack (parameter passing). Listed in opcodes_with_abs_long_operand. Original ROM: handled. Any patcher-authored PEA with a raw arcade address needs Pass B. |
| MOVE.l abs.l, ... forms | Various (depends on src/dst effective address mode) | abs_l_32bit | Yes, where applicable | MOVE.l with absolute long source or destination. The exact opcode word depends on the addressing mode combination. For any replacement_bytes that embed an arcade absolute long address in a MOVE.l instruction, Pass B applies. Original ROM: handled by rom_absolute_call_relocation scan where opcode pattern matches. |
| BSR / BRA | 6100 (word), 6000 (word) + 16-bit displacement | rel_16bit | No | PC-relative; displacement is recalculated from the shifted callsite position. This is a different relocation class (relative, not absolute). Not handled by Pass B (requires a separate relative-displacement pass if ever needed in patcher-authored replacement bytes). |
| DBRA / Bcc | Various + 16-bit displacement | rel_16bit | No | Same as BSR/BRA: PC-relative displacement, not an embedded absolute address. Not a Pass B concern. |

**Summary:** Pass B should support `abs_l_32bit` operands for all opcode classes that embed
a 32-bit absolute long address, matching (and extending to patcher-authored entries) the
coverage already provided by `rom_absolute_call_relocation` for original ROM code. The
minimum viable implementation covers JSR abs.l and JMP abs.l; full coverage adds LEA abs.l,
MOVEA.l immediate, and PEA abs.l. PC-relative forms (BSR, BRA, Bcc, DBRA) are out of scope
for Pass B.

---

## 6. Operand Resolution Rules

### Formula

```
final_operand = operand_arcade_target + 0x200 + shift_before(operand_arcade_target)
```

Where:
- `operand_arcade_target` is the original arcade address stored in the spec entry. It is
  never a derived or pre-shifted value.
- `0x200` is the Genesis ROM base relocation (the `whole_maincpu_copy` copies arcade
  address 0x000000 to Genesis ROM address 0x000200, so all arcade addresses receive
  this constant offset).
- `shift_before(operand_arcade_target)` is the sum of all net size deltas
  `(repl_len - orig_len)` for shift_replacement entries with `arcade_pc < operand_arcade_target`,
  computed from the finalized Pass A shift table.

### When `shift_before(target)` is computed

Pass A produces the final shift table as a side effect of applying all structural changes.
Pass B reads this table after Pass A completes. This ordering guarantee is the key
architectural property: `shift_before(target)` is derived from the layout that is actually
present in the output ROM, not from a pre-build estimate.

### How this avoids stale hardcoded Genesis addresses

The spec stores `operand_arcade_target` as the original arcade address (`0x059F5E` for
Patch A). This value is stable: it refers to a function in the arcade ROM that does not
move. The Genesis address `0x05A174` is never stored in the spec; it is derived fresh
on every build. If the shift table changes (any entry added, removed, or resized before
`0x059F5E`), `shift_before(0x059F5E)` updates automatically, and the next build produces
the correct `final_operand` without any spec edit.

### Example: adding a new shift_replacement before 0x059F5E

Suppose a new graphics hook at arcade 0x04A000 is added as a shift_replacement entry
with `original_bytes` length 4 and `replacement_bytes` length 6 (+2 bytes). The new
shift table gives `shift_before(0x059F5E) = 24`. Pass B computes:
```
final_operand = 0x059F5E + 0x200 + 24 = 0x05A176
```
The ROM is correct for the new layout. No human intervention is needed. The only change
in the spec is the new hook entry; Patch A's entry is untouched and remains valid because
`operand_arcade_target = "0x059F5E"` is still correct.

---

## 7. Migration Plan

### Step 1: Identify entries requiring conversion

Scan all `shift_replacement` entries in `startup_title_remap.json` for `replacement_bytes`
that match the pattern: a known opcode prefix (4EB9, 4EF9, 41F9–4FF9, 207C–2E7C, 4879)
followed by 8 raw hex digits without a `{symbol:...}` substitution. Any such entry
contains a raw embedded arcade address that will not be correctly relocated under the
current system as the shift table evolves.

As of Build 273, exactly one entry matches: `arcade_pc = 0x03A8E0` (Patch A) with
`replacement_bytes = 4eb900059f5e`.

### Step 2: Symbol-based entries are not affected

Entries whose `replacement_bytes` use `{symbol:...}` substitution (e.g.,
`4eb9{symbol:genesistan_render_sprites_vdp_bridge}`) resolve to linker-assigned absolute
Genesis addresses at build time. They do not embed arcade addresses and are not subject
to the shift accumulation problem. These entries remain valid and do not need conversion.
Examples: all other `shift_replacement` entries in the current spec.

### Step 3: Convert raw-address entries to the `relocate_after_shift` form

For each identified entry, replace the raw `replacement_bytes` field with the structured
deferred-relocation fields: `replacement_template`, `operand_arcade_target`,
`operand_kind`, `operand_width`, and `relocate_after_shift: true`. The `arcade_pc` and
`original_bytes` fields are unchanged.

The `original_bytes` field should continue to carry the original arcade ROM bytes for
patch verification. The entry size (orig_len, repl_len) is preserved: the total byte
length of `replacement_template + operand_width` must equal the intended replacement
length (6 bytes for a JSR abs.l = 2-byte opcode + 4-byte operand).

### Step 4: Original ROM code entries are unchanged

Entries in the `rom_absolute_call_relocation` scan region (the `whole_maincpu_copy`
region) are already handled correctly by the existing absolute-call relocation pass.
They are not shift_replacement entries with raw bytes; they are original arcade code
that the patcher rewrites in-place. No migration is needed for this category.

### Step 5: Build 273 transition (immediate fix)

The immediate fix for Build 273 is Strategy B as documented in
`docs/design/absolute_call_target_fix_plan.md`: change `replacement_bytes` from
`4eb900059f5e` to `4eb900059f74` so that the patcher's +0x200 yields 0x05A174. This
corrects the current build. The full migration to the `relocate_after_shift` form is
the long-term replacement and should be implemented before the shift table grows
significantly.

---

## 8. Validation Plan

### 8.1 Static validation after rebuild

For Patch A, the ROM at the callsite Genesis address must read `4EB9 0005A174`:

| Field | Value |
|---|---|
| `operand_arcade_target` | 0x059F5E |
| `shift_before(0x059F5E)` | 22 (current shift table) |
| `final_operand` | 0x059F5E + 0x200 + 22 = 0x05A174 |
| `genesis_callsite` | 0x03A8E0 + 0x200 + 12 = 0x03AAEC |
| ROM bytes expected at 0x03AAEC | `4E B9 00 05 A1 74` |
| ROM bytes (Build 273, broken) | `4E B9 00 05 A1 5E` |

Static check script:
```python
import struct
with open('dist/Rastan_NNN.bin', 'rb') as f:
    f.seek(0x03AAEC)
    data = f.read(6)
assert data.hex() == '4eb90005a174', f"FAIL: got {data.hex()}"
```

### 8.2 Relocation report format

The patcher should emit a relocation report for each deferred operand entry processed by
Pass B. Minimum required fields per entry:

```
arcade_pc:               0x03A8E0
arcade_target:           0x059F5E
shift_before_target:     22
final_operand:           0x05A174
genesis_callsite:        0x03AAEC
template:                4EB9
operand_kind:            abs_l_32bit
rom_bytes_written:       4EB9 0005A174
status:                  OK
```

### 8.3 Shift table evolution test (static)

Adding a new shift_replacement entry before 0x059F5E (e.g., at arcade 0x04A000, +2 bytes)
and rebuilding should automatically update the resolved operand to 0x05A176 without any
change to the Patch A entry. This can be verified statically by inspecting the output ROM
bytes at 0x03AAEC without running MAME.

Expected output after adding such an entry:
```
shift_before(0x059F5E) = 24
final_operand = 0x059F5E + 0x200 + 24 = 0x05A176
ROM at 0x03AAEC: 4E B9 00 05 A1 76
```

This confirms that the architecture is self-correcting under shift table changes.

### 8.4 Runtime validation

Using the Genesis MAME harness (`tools/mame/run_genesis_trace_wsl.sh`) with a Lua probe:

- Install tap at `0x05A174` (producer function entry, the correct target).
- Install tap at `0x05A15E` (sprite table data, the wrong target from Build 273).
- Install tap at `0x03AAEC` (callsite A).

Pass criterion:
```
PASS: tap 0x05A174 fires after callsite_a; tap 0x05A15E does NOT fire.
FAIL: tap 0x05A15E fires; tap 0x05A174 does not fire from the callsite_a path.
```

Additionally, at the `0x05A174` tap, the A5 register must match the A5 value at the
`0x03AAEC` callsite tap (same frame, same A5 — no context drift, unlike the Build 273
observation where A5 changed between seq=043 and seq=044 indicating execution through data).

---

## 9. Final Recommendation

Implement Pass A and Pass B as described. The transition requires:

1. (Immediate) Apply Strategy B fix from `docs/design/absolute_call_target_fix_plan.md`
   to correct Build 273 (change `4eb900059f5e` to `4eb900059f74` in Patch A entry).

2. (Long-term) Add `relocate_after_shift` support to the patcher:
   - Pass A: recognize entries with `relocate_after_shift: true` and record their
     `arcade_pc` and `operand_arcade_target` without embedding a raw address.
   - Pass B: after Pass A, compute `shift_before(operand_arcade_target)` from the
     finalized shift table, derive `final_operand`, and write the opcode+operand bytes
     at the computed genesis callsite.
   - Emit a per-entry relocation report.

3. Convert Patch A (and any future raw-address entries) to the `relocate_after_shift`
   format once Pass B is implemented.

4. Retain `rom_absolute_call_relocation` unchanged for original ROM code: it handles the
   `whole_maincpu_copy` region correctly and is complementary to, not replaced by, Pass B.

The preferred design separates structural shifting from operand relocation and preserves
original arcade targets as the source of truth.
