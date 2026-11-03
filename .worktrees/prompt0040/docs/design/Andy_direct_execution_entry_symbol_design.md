# Andy — `direct_execution.entry_symbol` Replacement Design

**Agent:** Andy
**Type:** Forensic Analysis + Design (no implementation)
**Build context:** current `rastan-direct`, Phase B decomposition complete
**Architecture compliance:** CONFIRMED against [RULES.md](RULES.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

**Outcome:** selected replacement is `_bootstrap`. Only a single one-line JSON edit is required. No `postpatch_startup_rom.py` change required beyond the filter Cody already applied in
[Cody_stale_symbol_fix.md](docs/design/Cody_stale_symbol_fix.md).

---

## Phase 1 — Downstream uses of `direct_entry_symbol_addr`

Traced every reference to `direct_entry_symbol_addr` in
[tools/translation/postpatch_startup_rom.py](tools/translation/postpatch_startup_rom.py)
using `grep -n`. Results:

| Line    | Code                                                                                                 | Purpose                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 1685    | `direct_cfg = spec.get("direct_execution", {})`                                                     | Load the `direct_execution` sub-object from `specs/rastan_direct_remap.json`. |
| 1686    | `direct_entry_symbol = str(direct_cfg.get("entry_symbol", "")) if is_rastan_direct_profile else ""` | Read the `entry_symbol` string name (a Genesis symbol name).                |
| 1687    | `direct_entry_symbol_addr = None`                                                                   | Initialize resolved-address slot.                                           |
| 1688    | `if is_rastan_direct_profile and direct_entry_symbol:`                                              | Guard.                                                                      |
| 1689    | `direct_entry_symbol_addr = resolve_symbol_address(symbol_addresses, direct_entry_symbol)`          | **Resolve symbol name → address via the build symbol table. Fails with `RuntimeError: Replacement references missing symbol` if the name is absent.** This is where the build currently breaks. |
| 1892    | `manifest["direct_execution"] = {`                                                                  | Begin manifest block.                                                       |
| 1893    | `"entry_arcade_pc": direct_cfg.get("entry_arcade_pc"),`                                             | Pass-through of the spec's arcade-side address literal.                     |
| 1894    | `"entry_symbol": direct_entry_symbol,`                                                              | Pass-through of the symbol-name string.                                     |
| 1895-98 | `"entry_symbol_address": (f"0x{direct_entry_symbol_addr:08X}" if ... is not None else None),`       | Writes the resolved address as 8-digit uppercase hex into the manifest.     |

**Total references to `direct_entry_symbol_addr` in the entire file:** exactly 4 (lines 1687, 1688-implicit-check, 1689, 1896). Confirmed via `grep -n "direct_entry_symbol"` — no other hits.

**What the tool does with the value:**

- **Zero** ROM bytes are written using it.
- **Zero** patches reference it.
- **Zero** validation assertions use it.
- **Zero** downstream tools in this repo consume it (searched for `entry_symbol_address` across the tree; the only hit outside `postpatch_startup_rom.py` is historical evidence in [Chad_history_breifing.md](Chad_history_breifing.md) and [docs/design/Cody_rastan_direct_patcher_reuse_and_extension.md](docs/design/Cody_rastan_direct_patcher_reuse_and_extension.md) showing the previous value was `0x0003A208`).

**Conclusion for Phase 1.** `direct_entry_symbol_addr` is **pure manifest metadata**. It is resolved once, written to the build manifest's `direct_execution.entry_symbol_address` field for documentation / inspection, and never used to affect ROM bytes, patch logic, address maps, or invariants. The build fails because `resolve_symbol_address` cannot find the stale name — not because the value is semantically needed downstream.

---

## Phase 2 — Replacement symbol evaluation

Three candidates per the prompt, evaluated against the current
symbol table
[apps/rastan-direct/out/symbol.txt](apps/rastan-direct/out/symbol.txt):

| Symbol                             | Exists in symbol table? | Address     | Appropriate for "Genesis-side direct-execution entry"? | Reasoning |
| ---------------------------------- | ----------------------- | ----------- | ------------------------------------------------------ | --------- |
| `_bootstrap`                       | YES (line 26 of symbol.txt) | `0x00000226` | **YES — selected** | The Genesis symbol that owns cold-boot and **permanently hands execution to arcade code** via `jmp (0x00003A200).l`. This is literally the symbol whose execution causes "direct arcade execution" to begin. Semantically matches the field name: it is the entry into direct execution. Phase B decomposition added it specifically for this role. |
| `_start`                           | YES (line 25)               | `0x00000202` | partial fit                                            | The 68000 reset vector target. Runs earlier than `_bootstrap` (does SR/SP/TMSS then `jsr _bootstrap`). Generic reset logic, not specific to the direct-execution architecture. Works, but `_bootstrap` is more precise. |
| `genesis_rom_offset 0x3A200` (= arcade_pc 0x3A000) directly | N/A — not a Genesis symbol | `0x0003A200` | no | The `entry_symbol` field is a symbol-name string, resolved via `resolve_symbol_address` against the symbol table. An arcade_pc is already surfaced in the adjacent `entry_arcade_pc` field; duplicating it as a non-existent symbol name would require tool changes (string-vs-literal detection in `resolve_symbol_address`) beyond the scope of this fix. |

**Selected replacement:** `_bootstrap`

**Justification (one sentence):** `_bootstrap` is the single Genesis
symbol whose execution is the direct-execution entry point — its
body performs the one-time cold-boot setup and then permanently
JMPs to arcade code at `arcade_pc 0x0003A000` — which is exactly
what `direct_execution.entry_symbol` should document under the Phase B
architecture.

---

## Phase 3 — Fix specification

### Required change (single one-line JSON edit)

```
File:          specs/rastan_direct_remap.json
Field:         direct_execution.entry_symbol
Current value: "rastan_direct_arcade_tick_entry"
New value:     "_bootstrap"
Justification: Under the Phase B decomposition, _bootstrap is the
               Genesis symbol that performs cold-boot setup and JMPs
               permanently into arcade code at arcade_pc 0x0003A000.
               It exists in the current symbol table at 0x00000226.
               rastan_direct_arcade_tick_entry refers to the deleted
               Genesis-owned loop entry and no longer exists in the
               symbol table; the rename preserves manifest metadata
               semantics under the new architecture.
```

### Additional `postpatch_startup_rom.py` changes

**NONE** beyond the `required_symbols` filter Cody has already
applied at line 911 (per [Cody_stale_symbol_fix.md](docs/design/Cody_stale_symbol_fix.md) Phase 2). Once `entry_symbol = "_bootstrap"`, the
`resolve_symbol_address` call at line 1689 succeeds (the symbol
exists at `0x00000226`), and line 1896 writes
`"entry_symbol_address": "0x00000226"` into the manifest.

The `required_symbols` filter Cody added is now a double-safety: the
name `rastan_direct_arcade_tick_entry` is gone from both the spec and
the required-symbols list, so even if one slips back the other
catches it. No change required — leave the filter in place.

### Consistency recommendation (out of strict scope but noted)

The sibling field `direct_execution.entry_arcade_pc` currently
contains `"0x03A008"`. Under the old Genesis-owned-loop architecture
that value paired with `rastan_direct_arcade_tick_entry` — both
referred to the arcade L5 handler at `arcade_pc 0x3A008` which the
Genesis loop JMPed into every frame. Under the Phase B architecture:

- Cold-boot handoff target: `arcade_pc 0x0003A000` (Genesis ROM `0x00003A200`)
- VBlank-chain target:       `arcade_pc 0x0003A008` (Genesis ROM `0x00003A208`)

If `entry_symbol` is renamed to `_bootstrap` (which owns the
cold-boot handoff to `arcade_pc 0x0003A000`), semantic consistency
argues `entry_arcade_pc` should also change from `"0x03A008"` to
`"0x03A000"`. This is a manifest-metadata correctness issue only —
the value is not consumed anywhere that would affect the build. It is
**out of the strict scope of this prompt** (which asks about
`entry_symbol`), but Cody should be informed so the manifest is
internally coherent. Recommend making both changes in the same spec
edit:

```
direct_execution:
  entry_arcade_pc: "0x03A008" → "0x03A000"
  entry_symbol:    "rastan_direct_arcade_tick_entry" → "_bootstrap"
```

If the project prefers strict scoping, making only the
`entry_symbol` change unblocks the build; the `entry_arcade_pc`
inconsistency is cosmetic and can be deferred.

---

## STOP conditions — not triggered

- Downstream uses of `direct_entry_symbol_addr` fully traced: 4 references, all in the same Python source file, all proven to be metadata-only.
- Correct replacement symbol identified with HIGH confidence: `_bootstrap` exists at `0x00000226` in the current symbol table and is the definitional Genesis-side direct-execution entry under Phase B.
- Replacement does not require a new symbol — `_bootstrap` already exists.

---

## Summary

- Downstream uses of `direct_entry_symbol_addr` traced: **YES** — manifest metadata only (line 1896), no ROM patch, no validation, no address-map, no downstream tool consumer in this repo.
- Correct replacement symbol identified: **YES — `_bootstrap`**
- Fix specified for Cody: **YES — one-line JSON edit, no tool change**
- STOP triggered: **NO**
- Ready for Cody implementation: **YES**
