# Cody — `_bootstrap` Symbol Resolution Fix

Agent: Cody  
Type: Implementation (tool fix — one line only)  
Build Context: current `rastan-direct`

## Objective

Apply the one-line symbol-dictionary substitution at
`tools/translation/postpatch_startup_rom.py:1689` so
`direct_execution.entry_symbol` resolves from `all_symbol_addresses`.

## Phase 1 — One-line fix

Verified pre-change line 1689:

```python
direct_entry_symbol_addr = resolve_symbol_address(symbol_addresses, direct_entry_symbol)
```

Applied one-line change:

```python
direct_entry_symbol_addr = resolve_symbol_address(all_symbol_addresses, direct_entry_symbol)
```

Change scope:
- Only variable token changed: `symbol_addresses` -> `all_symbol_addresses`
- No abstraction or conditional logic added
- No other line edits made in this pass

## Phase 2 — Build result

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Result: **FAIL (STOP)**

Observed behavior:
- `resolve_symbol_address` error for `_bootstrap`: **NOT PRESENT** (fixed)
- New failure appears later in postpatch invariant check:

```text
RuntimeError: Build 0029 invariant failure: expected total_genesis_bytes_covered=0xFC1C4 and opcode_replace patched_site count=73; got total_genesis_bytes_covered=0xFBF20 opcode_replace patched_site count=73.
```

Failure site:
- `tools/translation/postpatch_startup_rom.py:1745`

Implication:
- One-line symbol-visibility fix worked for the original blocker.
- Build still fails due separate invariant mismatch.

## Phase 3 — Manifest verification status

Because build failed before successful postpatch completion, current manifest values
remain stale from the prior successful run:

- `entry_arcade_pc`: `0x03A008`
- `entry_symbol`: `rastan_direct_arcade_tick_entry`
- `entry_symbol_address`: `0x0003A208`

So expected updated manifest tuple could not be verified in this pass.

## Phase 4 — Integrity snapshot at STOP

Static checks (source/symbol/spec):
- vector 29 -> `_vblank_service`: YES
- `_bootstrap` ends with `jmp (0x00003A200).l`: YES
- `_vblank_service` ends with `jmp (0x00003A208).l`: YES
- `_vblank_service` contains `RTE`: NO
- `main_68k` absent: YES
- no Genesis-owned loop symbols (`main_68k`, `arcade_tick_logic`, `rastan_direct_arcade_tick_entry`, `frame_counter`, `tick_counter`): YES
- Phase A 17 entries in spec: YES
- Phase A 17 entries in built ROM: NO (no postpatch-complete ROM emitted)

## STOP condition

STOP triggered: **YES**

Reason:
- Build fails on invariant mismatch at postpatch line 1745 after the one-line fix.
- Prompt requires STOP on any build failure.
