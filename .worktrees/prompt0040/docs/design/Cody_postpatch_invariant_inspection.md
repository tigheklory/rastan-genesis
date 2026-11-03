# [Cody — Postpatch Invariant Structure Inspection + Conditional Update]

## Scope
Phase 1 read-only inspection completed for:
- `tools/translation/postpatch_startup_rom.py`
- `specs/rastan_direct_remap.json` (current working tree)
- `HEAD:specs/rastan_direct_remap.json` (pre-edit baseline)

No runtime/source/spec logic was changed during evidence gathering.

## §1.A — Build 0029 invariant section (quoted with file:line)
Source: `tools/translation/postpatch_startup_rom.py:1736-1751`

```python
        if len(opcode_replace_logs) != len(opcode_replace_sites):
            raise RuntimeError(
                "Address-map invariant failure: opcode_replace rewrite_log count "
                "does not match patched_site opcode_replace segment count."
            )
        if (
            int(segment_coverage["total_genesis_bytes_covered"]) != 0xFBF20
            or len(opcode_replace_sites) != 73
        ):
            raise RuntimeError(
                "Build 0029 invariant failure: expected "
                "total_genesis_bytes_covered=0xFBF20 and "
                "opcode_replace patched_site count=73; got "
                f"total_genesis_bytes_covered=0x{int(segment_coverage['total_genesis_bytes_covered']):X} "
                f"opcode_replace patched_site count={len(opcode_replace_sites)}."
            )
```

## §1.B — Expected count (`73`) definition
- Definition type: **literal constant**
- Evidence:
  - Numeric invariant check uses literal `73` at `tools/translation/postpatch_startup_rom.py:1743`
  - Error message hardcodes `count=73` at `tools/translation/postpatch_startup_rom.py:1748-1750`
- Not table-driven, not manifest-driven, not spec-derived in this check block.

## §1.C — Expected bytes (`0xFBF20`) definition
- Definition type: **literal constant**
- Evidence:
  - Numeric invariant check uses literal `0xFBF20` at `tools/translation/postpatch_startup_rom.py:1742`
  - Error message hardcodes `0xFBF20` at `tools/translation/postpatch_startup_rom.py:1747-1749`
- Not table-driven, not manifest-driven, not spec-derived in this check block.

## §1.D — Invariant structure classification
Classification: **(a) Simple constant pair**

Rationale:
- The Build 0029 gate compares two literal constants in one condition:
  - `total_genesis_bytes_covered == 0xFBF20`
  - `patched_site opcode_replace count == 73`
- Both constants are adjacent and local to the check.

Note:
- There is also a separate dynamic expectation check driven by spec (`expectations.opcode_replace_count`) at `tools/translation/postpatch_startup_rom.py:1616-1627`.  
  That check is independent and does not replace the Build 0029 hardcoded pair.

## §1.E — `arcade_pc 0x03AD44` prior-entry inspection
Command basis:
- Prior baseline: `git show HEAD:specs/rastan_direct_remap.json`
- Current working tree: `specs/rastan_direct_remap.json`

### Prior entry content (HEAD baseline)
```json
{
  "arcade_pc": "0x03AD44",
  "original_bytes": "20C0534166FA4E75",
  "replacement_bytes": "4eb9{symbol:genesistan_hook_tilemap_bg_fill}4e75",
  "note": "Title/attract BG write path longword fill -> rastan-direct BG fill hook symbol."
}
```

### Current entry content (working tree)
```json
{
  "arcade_pc": "0x03AD44",
  "original_bytes": "20C0534166FA4E75",
  "replacement_bytes": "4EB9{symbol:genesistan_pc090oj_hook_init_clear_3ad44}4E75",
  "note": "PC090OJ Strategy A function-body replacement at INDEPENDENT writer fn 0x3AD44 (helper genesistan_pc090oj_hook_init_clear_3ad44). Intercepts 7 ledger init/reset callers (0x03AD5C, 0x03AD6E, 0x03AD82, 0x03AE70, 0x03AE80, 0x03AF38, 0x03AF48). Helper zeroes the SAT slot range 76..79 corresponding to the bulk-clear targets. See Andy_pc090oj_implementation_spec.md §8.6."
}
```

### Replacement validity determination
Result: **QUESTIONABLE**

Reason:
- Prior entry purpose was a tilemap BG fill hook (`genesistan_hook_tilemap_bg_fill`), not a PC090OJ helper.
- Current entry repurposes the same `arcade_pc` site for PC090OJ behavior.
- Under this task’s decision rule, a same-address replacement is only auto-valid if prior and new entries cover the same concern. That condition is not met.

## §1.F — Phase 1 conclusion
Conclusion: **STOP — 0x03AD44 replacement is QUESTIONABLE**

Summary:
- Invariant structure condition is met for Phase 2 model (**simple constant pair**).
- Replacement-validity condition is **not met** (prior entry served a different concern).
- Therefore, per task gating rules, **Phase 2 must not execute** in this run.

## Outcome
- Phase 1 read-only evidence gathered: **complete**
- Phase 2 invariant update: **not executed**
