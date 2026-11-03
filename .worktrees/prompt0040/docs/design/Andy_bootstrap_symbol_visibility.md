# Andy — `_bootstrap` Symbol Visibility Analysis

**Agent:** Andy
**Type:** Forensic Analysis + Design (no implementation)
**Build context:** current `rastan-direct`, Phase B decomposition complete
**Architecture compliance:** CONFIRMED against [RULES.md](RULES.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

**Outcome:** root cause is **name-filter reassignment** of `symbol_addresses` at [postpatch_startup_rom.py:964](tools/translation/postpatch_startup_rom.py), **not** local-vs-global symbol type. Recommended fix is Option 2: one-line change in the tool to resolve `direct_execution.entry_symbol` against the unfiltered symbol dict `all_symbol_addresses` (already built at line 930).

**Option 1 (`.global _bootstrap` in `boot.s`) does NOT fix the root cause** — it is evaluated and rejected with evidence below.

---

## Phase 1 — How `symbol_addresses` is built

Traced in [tools/translation/postpatch_startup_rom.py](tools/translation/postpatch_startup_rom.py).

### Regex that parses the symbol file

```
Line 15:  SYMBOL_PATTERN = re.compile(r"^([0-9A-Fa-f]+)\s+\S+\s+(\S+)")
```

The type column is matched by `\S+` — a single non-whitespace token. The pattern does **not** restrict to `T` (global) vs `t` (local); any non-whitespace type value matches (including `t`, `T`, `A`, `a`, `W`, `B`, `D`, `R`, etc.). Group 1 is the address, group 2 is the symbol name.

Applied to `00000226 t _bootstrap` from [apps/rastan-direct/out/symbol.txt](apps/rastan-direct/out/symbol.txt), this matches cleanly with `name = "_bootstrap"`, `address = 0x00000226`.

### `parse_symbol_table` function

```
Line 61-85:  def parse_symbol_table(path, required_names=None) -> dict[str, int]:
```

Two return modes:

- **`required_names=None`** → returns **every** `(name, address)` pair matched by `SYMBOL_PATTERN`, unfiltered. `t` and `T` symbols both included.
- **`required_names=<tuple>`** → returns **only** entries whose name (or `_<name>` fallback) appears in the tuple. Any symbol not in the whitelist is dropped.

### Construction of `symbol_addresses` for the rastan-direct profile

| Line | Code                                                                         | Effect on `symbol_addresses` visible at line 1689                                    |
| ---- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| 906  | `required_symbols = tuple(spec.get("required_symbols", []))`                 | Reads the whitelist from spec. This does not contain `_bootstrap`.                   |
| 907-912 | `if is_rastan_direct_profile: required_symbols = tuple(name for name in required_symbols if name != "rastan_direct_arcade_tick_entry")` | Cody's existing filter; removes stale name. Does not add `_bootstrap`. |
| 930  | `all_symbol_addresses = parse_symbol_table(symbols_path, required_names=None)` | Builds a **full** dict of every symbol, including `_bootstrap` at `0x00000226`.    |
| 931  | `symbol_addresses = all_symbol_addresses`                                    | Initially, `symbol_addresses` is an alias for the full dict — `_bootstrap` present. |
| 964  | `symbol_addresses = parse_symbol_table(symbols_path, required_symbols)`      | **REASSIGNMENT** — `symbol_addresses` now refers to a newly parsed dict **filtered** by `required_symbols`. Every name not in the whitelist is dropped, including `_bootstrap`. `all_symbol_addresses` is unchanged. |
| 1689 | `direct_entry_symbol_addr = resolve_symbol_address(symbol_addresses, direct_entry_symbol)` | Lookup happens on the **filtered** dict from line 964. `_bootstrap` is not present → `RuntimeError`. |

### Symbol types included vs excluded

**Included (by `SYMBOL_PATTERN` regex):** every symbol type (the regex matches any `\S+`). Concretely, `out/symbol.txt` contains types `a`, `A`, `t`, `T`, `W`, `B`, `D`, `R` — all matched.

**Excluded (by `parse_symbol_table(..., required_names=<tuple>)` name filter at line 964):** every symbol whose name (or `_<name>`) is not listed in `spec.required_symbols`. This is a **name-based filter**, not a type-based filter.

**Are local (`t`) symbols included?** In `all_symbol_addresses`: **YES** (line 930, no filter). In `symbol_addresses` at line 1689: **NO unless the name happens to also be in `required_symbols`**. Type is not a factor in either case — name is.

---

## Phase 2 — Root cause

**Root cause:** At [postpatch_startup_rom.py:964](tools/translation/postpatch_startup_rom.py), `symbol_addresses` is reassigned to a dict built with the `required_symbols` whitelist; `_bootstrap` is not in that whitelist, so by the time `resolve_symbol_address` runs at line 1689, the name is absent regardless of its ELF/nm symbol type.

**Confirmed from:** [postpatch_startup_rom.py:964](tools/translation/postpatch_startup_rom.py) (the filtering reassignment) combined with [postpatch_startup_rom.py:61-85](tools/translation/postpatch_startup_rom.py) (the `parse_symbol_table` whitelist semantics). Also corroborated by [specs/rastan_direct_remap.json](specs/rastan_direct_remap.json) lines 80-104 — the `required_symbols` array contains hook names and staged_scroll symbols but no boot/bootstrap symbols.

Symbol type (`t` vs `T`) is **not** the cause. The regex at [postpatch_startup_rom.py:15](tools/translation/postpatch_startup_rom.py) accepts both.

---

## Phase 3 — Fix option evaluation

### Option 1 — Declare `_bootstrap` as `.global` in `boot.s`

- **What it changes:** adds `.global _bootstrap` to the assembly source. The symbol's nm type flips from `t` (local text) to `T` (global text) in the linker output.
- **Effect on `SYMBOL_PATTERN` matching:** none — the regex accepts both `t` and `T` equally (`\S+`).
- **Effect on the `required_symbols` whitelist at line 964:** none — the whitelist filters by **name**, not by type. Making `_bootstrap` global does not add `"_bootstrap"` to `required_symbols`, so the filter at line 964 still drops it.
- **Does it fix the root cause?** **NO.** After the change, `out/symbol.txt` would contain `00000226 T _bootstrap`, which is still not in `required_symbols`, so `symbol_addresses["_bootstrap"]` at line 1689 remains absent.
- **Architecturally correct under RULES.md?** Moot. Making `_bootstrap` global is harmless but purposeless for this bug — `_bootstrap` does not need external linkage (nothing outside `boot.s` calls it; it is invoked by `jsr _bootstrap` from `_start` in the same translation unit).
- **Scope:** one line in assembly source.
- **Risk:** NONE functionally; a slightly misleading "fix" that does not address the real issue.
- **Recommended:** **NO.**

```
Option 1:
  Fixes root cause: NO
  Architecturally correct: N/A (would not fix bug)
  Scope: minimal but ineffective
  Risk: NONE
  Recommended: NO
```

### Option 2 — Change `postpatch_startup_rom.py` to resolve `direct_entry_symbol` against the unfiltered dict

- **What it changes:** at line 1689, change `symbol_addresses` to `all_symbol_addresses`. The unfiltered dict (already built at line 930, contains every symbol including `_bootstrap`) is used for this one resolution.
- **Effect on the resolution:** `resolve_symbol_address(all_symbol_addresses, "_bootstrap")` returns `0x00000226` cleanly; line 1896 writes `"entry_symbol_address": "0x00000226"` into the manifest. Build succeeds.
- **Effect on any other symbol resolution in the tool:** none. `all_symbol_addresses` is already used at lines 968 and 970 for `genesistan_crash_handler_end`; this change uses it for one additional lookup. No other `resolve_symbol_address` call is modified. No patch-byte computation changes. No validation changes.
- **Is this broader than needed?** No — it is the minimum scope. Only the direct-execution metadata resolution is changed.
- **Architecturally correct under RULES.md?** YES. `direct_execution.entry_symbol` resolves to a **manifest metadata** value (confirmed in [Andy_direct_execution_entry_symbol_design.md](docs/design/Andy_direct_execution_entry_symbol_design.md) — the resolved address is written only to `manifest["direct_execution"]["entry_symbol_address"]` at line 1896; no ROM patch, no validation, no downstream consumer). Since this is documentation metadata, not a replacement-byte target, it does not need to participate in the `required_symbols` validation pass that protects `{symbol:NAME}` expansion in `replacement_bytes`. Using the unfiltered dict for one metadata field is semantically appropriate and does not weaken any safety invariant.
- **Scope:** one line.
- **Risk:** NONE. The only observable change is that the manifest's `direct_execution.entry_symbol_address` field now correctly reports `0x00000226` for `_bootstrap`. No bytes patched differently.
- **Recommended:** **YES.**

```
Option 2:
  Fixes root cause: YES
  Architecturally correct: YES
  Scope: minimal (one line)
  Risk: NONE
  Recommended: YES
```

---

## Phase 4 — Fix specification

**Selected option:** Option 2.

**Justification (one sentence):** The root cause is a name-filter reassignment of `symbol_addresses` to a whitelist that omits `_bootstrap`; `_bootstrap` is already correctly parsed into the unfiltered `all_symbol_addresses` dict at line 930, so the minimum correct fix is to resolve the metadata-only `direct_execution.entry_symbol` against that existing unfiltered dict.

### Exact change for Cody

```
File:   tools/translation/postpatch_startup_rom.py
Line:   1689
Before: direct_entry_symbol_addr = resolve_symbol_address(symbol_addresses, direct_entry_symbol)
After:  direct_entry_symbol_addr = resolve_symbol_address(all_symbol_addresses, direct_entry_symbol)
```

**Diff:** replace the variable name `symbol_addresses` with `all_symbol_addresses` on line 1689. Every other character on the line — function call, argument order, assignment target — is unchanged.

**Why this is minimal:**

- Only one line edited.
- Only one call site affected — the direct-execution metadata resolver.
- No change to `parse_symbol_table`.
- No change to `SYMBOL_PATTERN`.
- No change to the `required_symbols` whitelist in the spec.
- No change to `boot.s` (no `.global` declaration added).
- No change to any `resolve_symbol_address` call that drives a replacement-byte patch (those continue to use the filtered `symbol_addresses`, preserving the `required_symbols` validation contract for actual patch operations).

**Verification note for Cody:** after applying the change, the build should succeed and `apps/rastan-direct/build/rastan_direct_patch_manifest.json` (or equivalent manifest path) should contain:

```json
"direct_execution": {
  "entry_arcade_pc": "0x03A000",
  "entry_symbol": "_bootstrap",
  "entry_symbol_address": "0x00000226"
}
```

Consistent with the address of `_bootstrap` in [apps/rastan-direct/out/symbol.txt](apps/rastan-direct/out/symbol.txt) (line `00000226 t _bootstrap`).

---

## STOP conditions — not triggered

- `symbol_addresses` construction fully traced (Phase 1 table above).
- Root cause confirmed with file:line evidence (Phase 2).
- Both fix options evaluated; Option 2 clearly resolves the root cause (Phase 3).
- Option 1 evaluated and rejected with evidence (not a false choice — evaluated fully, correctly excluded).

---

## Summary

- symbol_addresses construction traced: **YES**
- root cause confirmed: **YES** — `symbol_addresses` is reassigned at line 964 to a name-filtered dict built from `required_symbols`; `_bootstrap` is not in that whitelist; filter is by name, not by symbol type.
- option 1 evaluated: **YES** — rejected; symbol type is not the bottleneck, so making `_bootstrap` global does not affect the name-based filter.
- option 2 evaluated: **YES** — accepted; the one-line change at line 1689 to use `all_symbol_addresses` (already built) resolves the metadata-only lookup against the full symbol set without weakening any patch-validation invariant.
- recommended fix: **Option 2**; change `symbol_addresses` → `all_symbol_addresses` on line 1689 of `tools/translation/postpatch_startup_rom.py`.
- STOP triggered: **NO**.
