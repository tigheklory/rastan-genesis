# Cody — Stale Symbol Fix

Agent: Cody
Type: Implementation (bookkeeping)
Build Context: current `rastan-direct`

## Objective

Remove stale validation dependency on `rastan_direct_arcade_tick_entry` in
`tools/translation/postpatch_startup_rom.py`, then rebuild.

## Phase 1 — References found in `postpatch_startup_rom.py`

### Literal symbol-name references

1. Line 911:

```python
name for name in required_symbols if name != "rastan_direct_arcade_tick_entry"
```

Role: **validation check filtering** (drops stale name from `required_symbols` prior to `parse_symbol_table(..., required_symbols)`).

### Symbol-use path tied to the same stale symbol (non-literal in code)

`specs/rastan_direct_remap.json` defines:

- `direct_execution.entry_symbol = "rastan_direct_arcade_tick_entry"`

Tool lines:

- Line 1686:

```python
direct_entry_symbol = str(direct_cfg.get("entry_symbol", "")) if is_rastan_direct_profile else ""
```

- Line 1689:

```python
direct_entry_symbol_addr = resolve_symbol_address(symbol_addresses, direct_entry_symbol)
```

Role: **address computation** (resolves symbol address for direct execution metadata).

## Phase 2 — Change applied

Applied one stale-validation fix in tool:

- filtered `required_symbols` for rastan-direct profile to exclude
  `rastan_direct_arcade_tick_entry` before symbol-table required-name validation.

No other logic removed.

## Phase 3 — Build

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Result: **FAIL (STOP)**

New failure after stale validation filter:

```text
RuntimeError: Replacement references missing symbol: rastan_direct_arcade_tick_entry
```

Location:

- `postpatch_startup_rom.py` line 1689 (`resolve_symbol_address(symbol_addresses, direct_entry_symbol)`)

Interpretation:

- stale **validation** check was removed
- stale **address computation** reference path remains (via `direct_execution.entry_symbol`)

## STOP condition

STOP triggered: **YES**

Reason:

- A reference path for `rastan_direct_arcade_tick_entry` is used for **address computation**.
- Per prompt rules, this requires STOP/report rather than further removal in this pass.

## Decomposition verification snapshot at STOP

- vector 29 -> `_vblank_service`: YES
- `main_68k` absent from symbol table: YES
- `_bootstrap` present and ends with `jmp (0x3A200).l`: YES
- `_vblank_service` present and ends with `jmp (0x3A208).l`: YES
- `_vblank_service` issues `RTE`: NO
- all 17 Phase A hook entries present in remap spec: YES
- no Genesis-owned loop symbols present (`main_68k`, `arcade_tick_logic`, `_VINT_handler`, `frame_counter`, `tick_counter`): YES
- `crash_handler.s` `frame_counter` reference absent: YES
- `rastan_direct_arcade_tick_entry` absent from symbol table: YES
