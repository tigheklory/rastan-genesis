# Phase 1 Revert + Producer/Renderer Order Fix — Patch Plan

## 1. Purpose

This document provides a precise, minimal, relocation-safe patch plan for:

1. Reverting all Phase 1 items identified in `opcode_change_audit_keep_rework_revert.md`
2. Correcting the producer → renderer ordering bug in the title screen init cluster

This plan is EXCLUSIVELY:
- Revert scaffolding and hacks
- Fix ordering

It does NOT redesign the tilemap system, sprite pipeline, VBlank DMA, or WRAM buffer
structure. Those are Phase 2+.

---

## 2. Phase 1 Revert Plan

### Background: Spec Architecture

The build uses two patch lists:
- **`shift_replacements`**: size-changing replacements that trigger full shift-table reflow.
  Use arcade PC addresses. The patcher finds the instruction in the relocated copy and
  applies the replacement, then reflows all branches/jumps/absolute-longs.
- **`opcode_replace`**: same-size or in-place replacements. Use arcade PC addresses.
  Applied after the shift pass. Must match original bytes exactly.

Both use `arcade_pc` as the key (original ROM address, NOT genesis/relocated address).
The whole-maincpu-copy shifts all arcade bytes by +0x200 (genesis address = arcade + 0x200 +
accumulated_shift_from_all_prior_insertions).

---

### Change ID: D-5 — Descriptor Attr Force

**Location**: `specs/startup_title_remap.json`, `opcode_replace` array, 5 entries:
- `arcade_pc: 0x05A11A`
- `arcade_pc: 0x05A13E`
- `arcade_pc: 0x05A188`
- `arcade_pc: 0x05A1AC`
- `arcade_pc: 0x05A1D0`

**Current modified bytes (all 5 entries)**:
```
original_bytes: "30FC0000"   (movew #0, a0@+)
replacement_bytes: "30FC0080" (movew #0x80, a0@+)
```

**Original intent**:
The arcade producer at 0x05A174 writes descriptor attribute fields. The correct arcade
value is 0x0000 (zero-initialized or unset for this pass). The 0x0080 was injected to make
the renderer's "non-empty" check pass using fake data.

**Revert action**:
For all five entries, change `replacement_bytes` to match `original_bytes`:
```json
"replacement_bytes": "30FC0000"
```
Effectively making each entry a no-op replacement (original bytes restored).

**Notes**:
- These are all same-size replacements (4 bytes). No shift impact.
- After revert: attribute fields in block-A descriptors are zero (real arcade value).
  The renderer may not produce visible output (expected — descriptor content is not yet built).
- Do NOT remove the entries; keep them as identity replacements so original_bytes validation
  continues to fire as a guard.

---

### Change ID: D-7 — RTS Trampoline Extension

**Location**: `specs/startup_title_remap.json`, `opcode_replace` array:
```json
"arcade_pc": "0x059F90",
"original_bytes": "4E75",
"replacement_bytes": "61000124610000044E75"
```

**Current modified behavior**:
The 2-byte `rts` at 0x059F90 is replaced with 10 bytes:
`bsr +0x0124` (→ calls block-A builder near 0x05A0B8),
`bsr +0x0004` (→ calls block-B path at ~0x059F9A),
`rts`.

This extends the fill-loop function's return boundary to add two implicit calls before
returning, without modifying any callsite. This is a trampoline-style hook — explicitly
forbidden by the architecture.

**Additional hazard**: The 10-byte replacement overwrites 8 bytes beyond the original 2-byte
rts, clobbering the following `cmpiw #255, a5@(5000)` (6 bytes at 0x059F92) and the
`beqs 0x059FDE` (2 bytes at 0x059F98). Any code path that enters at 0x059F92 (there is a
`jsr 0x059F92` at 0x051060) executes corrupted bytes in the current build.

**Original bytes to restore**:
`4E75` (plain rts, 2 bytes at 0x059F90)

**Revert action**:
Change `replacement_bytes` to `"4E75"`.

The patcher will write `4E75` at the position corresponding to arcade 0x059F90 and leave
the following bytes (0x059F92 onward) as their original ROM content (restored by the
identity replacement). The `cmpiw` at 0x059F92 and `beqs` at 0x059F98 are restored.

**Notes**:
- Same-size replacement (2 bytes). No shift impact.
- After revert: the fill-loop function returns cleanly. The block-A and block-B content
  builders are no longer called from this path. Block-A descriptor slots remain at whatever
  value the clear/fill puts there (zero initially). This is the correct baseline state.
- The `jsr 0x059F92` at 0x051060 is also restored to correct behavior.

---

### Change ID: T-9 — Full Function NOP at 0x0560DA

**Location**: `specs/startup_title_remap.json`, `opcode_replace` array:
```json
"arcade_pc": "0x0560DA",
"original_bytes": "206D10A0B1FCE0FF71A266046100FF6E206D10A0343C0032203C0000002020C0534266FAD1FC0000010020080280E0FFA1A220402B4810A0",
"replacement_bytes": "4E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E71"
```

**Current modified behavior**:
The entire body of the function (52 bytes, 26 NOPs) is silenced. The function originally:
1. Loads A5@(0x10A0) (a C-Window derived base pointer)
2. Compares it against 0xE0FF71A2 (a WRAM address)
3. If in range: calls a fill/copy helper (0x3AF6E vicinity)
4. Writes the result back to A5@(0x10A0)

This function was NOPed without documented analysis of its non-graphics side effects.

**Revert action**:
Change `replacement_bytes` to match `original_bytes`:
```json
"replacement_bytes": "206D10A0B1FCE0FF71A266046100FF6E206D10A0343C0032203C0000002020C0534266FAD1FC0000010020080280E0FFA1A220402B4810A0"
```

**Notes**:
- Same-size replacement (52 bytes). No shift impact.
- After revert: function 0x0560DA executes again. It reads A5@(0x10A0) and compares against
  0xE0FF71A2. If the C-Window base stores have been NOPed (T-7), A5@(0x10A0) may be zero or
  stale. The comparison `cmpa.l #0xE0FF71A2, A0` will likely fail (not in range), and the
  conditional branch will skip the fill call. The WRAM store at the end will write the
  (stale) pointer back to A5@(0x10A0). Net effect: likely harmless but the function runs.
- Monitor for crashes. If any crash occurs at this address, analyze the full body before
  re-NOPing individual ops.
- Do NOT remove the entry. Keep it as an identity replacement for validation guard.

---

### Change IDs: C-3 and C-4 — Tilemap Col/Row Counter Hooks

**Location**: `specs/startup_title_remap.json`, `shift_replacements` array:

Entry C-3 (Tilemap Plane A):
```json
"arcade_pc": "0x055968",
"original_bytes": "206D10A0323C0010227C0010D080267C0010D0402453610000322B4810A0588B5489534166EE",
"replacement_bytes": "4eb9{symbol:genesistan_hook_tilemap_plane_a}4e754e714e714e714e714e714e714e714e714e714e714e714e714e714e714e71"
```

Entry C-4 (Tilemap Plane B):
```json
"arcade_pc": "0x055990",
"original_bytes": "206D10A47210227C0010D080267C0010D04024536100006E588B5489534166F2",
"replacement_bytes": "4eb9{symbol:genesistan_hook_tilemap_plane_b}4e754e714e714e714e714e714e714e714e714e714e714e714e714e714e71"
```

**Current modified behavior**:
Both functions are replaced with `jsr genesistan_hook_tilemap_plane_X; rts; NOPs`. The C
hooks use stateful col/row counters that advance per call, which do not correctly track
the arcade destination address.

**Original bytes decoded**:
- 0x055968: loads A5@(0x10A0) (C-Window base pointer), sets up A1 with stride, does
  tile-index write loop through the C-Window pointer (arcade hardware write).
- 0x055990: same pattern for A5@(0x10A4) (second C-Window base pointer).

**Revert action — IMPORTANT SIZING NOTE**:

C-3 original_bytes = 38 bytes. Current replacement resolves to:
`4EB9` (2) + symbol (4) + `4E75` (2) + 14×`4E71` (28) = 36 bytes. Size delta = -2.

C-4 original_bytes = 32 bytes. Current replacement resolves to:
`4EB9` (2) + symbol (4) + `4E75` (2) + 11×`4E71` (22) = 30 bytes. Size delta = -2.

Both are SHRINKING replacements. Reverting restores the original larger sizes (+2 and +2).
This shifts all subsequent code by +4 bytes total after 0x055990.

**Revert strategy**: Since the original functions write to C-Window hardware addresses which
are invalid on Genesis, and the C-Window base stores are already NOPed by T-7, restoring
the original function body would cause the tile write loop to run with a stale/zero pointer —
writing to address ~0x00100000 which may be unmapped but is not necessarily crash-inducing
in tested behavior.

**Preferred revert**: Replace with NOPs of original size (not jsr hooks, not original bytes).
This is the safest intermediate state: the functions are silent (same as before), but the
wrong col/row counter approach is removed. The size is restored to original to unblock
correct shift calculations.

For C-3: Replace the shift_replacement entry at 0x055968 with NOP-fill of 38 bytes:
```json
"replacement_bytes": "4E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E71"
```
(38 bytes = 19 NOPs)

For C-4: Replace the shift_replacement entry at 0x055990 with NOP-fill of 32 bytes:
```json
"replacement_bytes": "4E714E714E714E714E714E714E714E714E714E714E714E714E714E714E71"
```
(32 bytes = 16 NOPs)

**Notes**:
- These entries remain in `shift_replacements` because they still change the code content
  (NOP fill is not identity). But the SIZE now matches original (no shrink), so the
  accumulated shift from 0x055990 onward returns to what it would be without these entries.
- All shift_replacement entries AFTER 0x055990 must be verified for correct shift offset
  after this change. The shift_table_patcher handles this automatically on rebuild.
- The C functions `genesistan_hook_tilemap_plane_a` and `genesistan_hook_tilemap_plane_b`
  in `main.c` are left in place (not deleted); they simply stop being called from the arcade
  code path. Remove the col/row counter resets from the SCREEN_FRONTEND_LIVE loop in main.c
  (lines that set `genesistan_hook_col_a = 0; genesistan_hook_row_a = 8;` etc.), since they
  are now dead code.

---

## 3. Producer → Renderer Ordering Fix

### Root Cause Identification

**Title init cluster**: Arcade address range 0x03A8D2–0x03A8FF (title substate=0 init path).

**Execution context**: `genesistan_run_original_frontend_tick()` (in main.c) runs the arcade
title state machine. When title substate (A5@(4)) = 0, the state=0 init path fires.

**Key addresses (ORIGINAL ROM = arcade addresses)**:

| Arcade addr | Instruction | Semantic role |
|-------------|-------------|---------------|
| 0x03A8D6 | `bsrw 0x03AD4C` | Clear descriptor windows (T-1 patch) |
| 0x03A8DA | `bsrw 0x03AE5A` | Clear text shadow (T-2 patch) |
| 0x03A8DE | `moveq #1, D1` | Setup arg for renderer call |
| **0x03A8E0** | `bsrw 0x3B902` | **ARCADE RENDERER** — S-1 patch replaces with genesis renderer |
| **0x03A8E4** | `jsr 0x059F5E` | **PRODUCER** — descriptor clear + B-block setup |
| 0x03A8EA | `moveq #9, D0` | Text dispatch selector |
| 0x03A8EC | `bsrw 0x3BB48` | Text dispatch (T-4 path) |

**Current ordering (WRONG)**:
1. Clear windows
2. Clear text shadow
3. **RENDERER** (0x03A8E0 → S-1 → `jsr genesistan_render_sprites_vdp_bridge`)
4. **PRODUCER** (0x03A8E4 → `jsr 0x059F5E`)
5. Text dispatch...

**Genesis addresses (for reference only)**:

With 7 prior shift_replacements before 0x03A8E0 adding +2 each (some +0 for same-size):
Exact accumulated shift before 0x03A8E0 = +12 bytes (6 of the prior S-1 entries add +2,
one entry at 0x03A818 is same size = 0).

Genesis address of 0x03A8E0 = 0x03A8E0 + 12 + 0x200 = 0x03AAEC.
Genesis address of 0x03A8E4 = 0x03A8E4 + 14 + 0x200 = 0x03AAF2.

These match the "PC 0x03AAEC" and "PC 0x03AAF2" seen in the execution trace.

**Required ordering (CORRECT)**:
1. Clear windows
2. Clear text shadow
3. **PRODUCER** (0x03A8E0 position → `jsr 0x059F5E`) — runs first
4. **RENDERER** (0x03A8E4 position → `jsr genesistan_render_sprites_vdp_bridge`) — runs after

### Patch Strategy: Swap at the Callsite

**Approach**: Modify two spec entries. No new code. No trampolines.

#### Step A — Move producer call into the renderer's slot (0x03A8E0)

Modify the shift_replacement entry at `arcade_pc: 0x03A8E0`:

**Current**:
```json
{
  "arcade_pc": "0x03A8E0",
  "original_bytes": "61001020",
  "replacement_bytes": "4eb9{symbol:genesistan_render_sprites_vdp_bridge}",
  "note": "..."
}
```

**New**:
```json
{
  "arcade_pc": "0x03A8E0",
  "original_bytes": "61001020",
  "replacement_bytes": "4eb900059f5e",
  "note": "ORDERING FIX: producer (0x059F5E clear+init) now runs first. Previously was renderer call."
}
```

Replacement bytes `4eb900059f5e` = `jsr 0x00059F5E` (6 bytes).
Size: original 4 bytes → replacement 6 bytes = +2 bytes shift. Same net shift as before.
The absolute address 0x00059F5E in the replacement will be updated by
`rom_absolute_call_relocation` to the correct relocated genesis address of the producer.

**Why this is safe**: The accumulated shift from this replacement (+2) is unchanged from
before (it was already +2 from the previous renderer jsr). All subsequent addresses
that were correct remain correct.

#### Step B — Move renderer call into the producer's slot (0x03A8E4)

Add a new entry to `opcode_replace` (NOT shift_replacements — same size):

```json
{
  "arcade_pc": "0x03A8E4",
  "original_bytes": "4eb900059f5e",
  "replacement_bytes": "4eb9{symbol:genesistan_render_sprites_vdp_bridge}",
  "note": "ORDERING FIX: renderer now runs after producer. Originally was jsr 0x059F5E here."
}
```

Replacement bytes = `jsr genesistan_render_sprites_vdp_bridge` (6 bytes).
Size: original 6 bytes → replacement 6 bytes = 0 shift delta.

**Why this is safe**: Same-size replacement, no shift impact. The `{symbol:...}` form resolves
at link time to the correct genesis address of the C bridge function.

### Why This Guarantees Producer Runs First

In the patched build, the state=0 init sequence becomes:

```
0x03A8D6: bsrw 0x03AD4C    → clear descriptor windows (T-1)
0x03A8DA: bsrw 0x03AE5A    → clear text shadow (T-2)
0x03A8DE: moveq #1, D1
0x03A8E0: jsr 0x059F5E     → PRODUCER runs first
0x03A8E4: jsr genesistan_render_sprites_vdp_bridge → RENDERER runs after
```

The producer (0x059F5E) executes its clear and B-block init sequence, then returns.
Only then does the renderer run and read from the descriptor windows.

After D-7 is also reverted (0x059F90 → plain `4E75`), the producer at 0x059F5E:
1. Clears block-A slots at 0xE0FF11FE (8 longs via D-1 retarget)
2. Writes initial B-block entries at 0xE0FF01BC (4 entries via D-2/D-3 retargets)
3. Returns

The renderer then reads block-A (will see zeros — block-A content building is Phase 2)
and block-B (will see initial entries). This is the clean baseline state from which
Phase 2 will add explicit block-A builder calls.

---

## 4. Validation Plan

### Pre-validation (build health)

After applying all Phase 1 changes, run a full build and confirm:

1. **Build succeeds**: No patcher errors about original_bytes mismatch. All reverts must
   match the spec's recorded `original_bytes` exactly.
2. **No regression in T-8/T-7/T-13 patches**: These are untouched. Confirm patcher does
   not error on them.
3. **C-3/C-4 size correction**: Confirm that after restoring original size at 0x055968 and
   0x055990, the shift_table_patcher reports clean relocation for all subsequent entries.

### Execution validation

Run Build 272+ (first build with Phase 1 applied) in MAME with the same probe set used
in Build 271:

| Probe | Expected result |
|-------|-----------------|
| `HIT 03A8E0` (arcade addr for producer slot) | Should fire once (state=0 init) |
| `HIT 059F5E` | Should fire before renderer hits |
| `HIT genesistan_render_sprites_vdp_bridge` | Should fire AFTER 059F5E fires |
| Descriptor window A@0xE0FF11FE at renderer entry | Should be ZERO (producer clears it, no content builder yet) |
| No attr contamination | 0x05A188 etc should write 0x0000, not 0x0080 |
| 0x0560DA restored | Game should not crash when this function executes |
| Tilemap hooks removed | genesistan_hook_tilemap_plane_a/b should not be called |

### Ordering proof

Instrument the execution trace with a sequence probe:
- Observe: `HIT 059F5E` before `HIT genesistan_render_sprites_vdp_bridge` within the same
  state=0 init pass
- These should appear in order: producer → renderer (not renderer → producer as before)

### Regression guard

- `CREDI` text still visible (T-4/T-5/C-1 text path unaffected)
- No exception frame from restored 0x0560DA function
- No crash from C-3/C-4 NOP fill (original C-Window writes were already NOPed by T-7;
  NOP fill is equivalent or safer)

---

## 5. Risks

### Risk 1: 0x0560DA restoration causes crash

If the function at 0x0560DA has non-obvious side effects (e.g., writes to a memory address
that causes an exception on Genesis), it will crash on first execution.

**Mitigation**: Run with the MAME debugger and set a breakpoint at 0x0560DA + 0x200 +
accumulated_shift. Step through the first execution. Confirm the cmpa comparison fails
(stale pointer < 0xE0FF71A2) so the fill call is skipped. If it does not fail, analyze why
and NOP only the specific graphics-output portion.

### Risk 2: C-3/C-4 size restoration breaks later shift entries

Removing the -2 shrink at 0x055968 and 0x055990 restores +4 total bytes to the image
after 0x055990. All shift_replacement entries after 0x055990 must be verified.

**Mitigation**: The shift_table_patcher automatically recalculates all shifts on each build.
After the change, inspect the patcher's relocation log for any entries in the 0x055990+
range that emit warnings or mismatch original_bytes.

### Risk 3: `4eb900059f5e` absolute address not updated

If the `rom_absolute_call_relocation` pass does not catch the `jsr 0x059F5E` in the
replacement_bytes at 0x03A8E0, the instruction will call the wrong address.

**Mitigation**: Confirm `rom_absolute_call_relocation` scans the full maincpu copy window
and includes 0x4EB9 in its opcode list (it does, per the spec). Alternatively, express the
replacement as `4eb9{symbol:genesistan_producer_059f5e}` once a named symbol for 0x059F5E
is added to `required_symbols`. This is the preferred long-term form.

### Risk 4: D-7 revert uncovers 0x051060 → 0x059F92 call issue

The `jsr 0x059F92` at 0x051060 calls into what was the cmpiw at 0x059F92 in the original
ROM but was corrupted by D-7's overwrite. After D-7 revert, 0x059F92 is restored to
`cmpiw #255, a5@(5000)`. This re-enables the original conditional path from 0x051060
into the block-B descriptor chain. Verify this path behaves correctly (it was working
before D-7 was applied).

**Mitigation**: Set a breakpoint at the relocated 0x051060 and confirm the path through
0x059F92 completes without exception.

### Risk 5: Ordering fix with D-7 also reverted

With D-7 reverted, the block-A content builder is no longer called from the producer path.
After the ordering fix, the renderer runs after the producer but still reads zero from
block-A. No visible logo sprites. This is EXPECTED for Phase 1.

**Important**: Do not re-introduce any builder call hack as a workaround. Block-A builder
calls will be added explicitly in Phase 2 via a clean callsite, not a trampoline.

---

## 6. Spec Change Summary

All changes are in `specs/startup_title_remap.json`.

| Change | Array | arcade_pc | Action |
|--------|-------|-----------|--------|
| D-5 revert (x5) | `opcode_replace` | 0x05A11A, 0x05A13E, 0x05A188, 0x05A1AC, 0x05A1D0 | replacement_bytes: 30FC0000 |
| D-7 revert | `opcode_replace` | 0x059F90 | replacement_bytes: 4E75 |
| T-9 revert | `opcode_replace` | 0x0560DA | replacement_bytes: (same as original_bytes) |
| C-3 revert | `shift_replacements` | 0x055968 | replacement_bytes: 19×4E71 (38 bytes) |
| C-4 revert | `shift_replacements` | 0x055990 | replacement_bytes: 16×4E71 (32 bytes) |
| Order fix A | `shift_replacements` | 0x03A8E0 | replacement_bytes: 4eb900059f5e (producer jsr) |
| Order fix B | `opcode_replace` | 0x03A8E4 | NEW entry: jsr genesistan_render_sprites_vdp_bridge |

**C code change** (`apps/rastan/src/main.c`):
Remove col/row counter resets from the `SCREEN_FRONTEND_LIVE` loop body:
```c
// REMOVE these 4 lines:
genesistan_hook_col_a = 0;
genesistan_hook_row_a = 8;
genesistan_hook_col_b = 0;
genesistan_hook_row_b = 8;
```
These are dead code after the C-3/C-4 hooks are reverted.
