# Cody — Hook Closure Implementation (Phase A)

Agent: Cody  
Type: Implementation  
Build Context: current `rastan-direct`

## Scope

Phase A only. Added the 17 `opcode_replace` entries from:
- `docs/design/Andy_p1_p2_hook_closure_design.md` (Phase 6, Items 1-17)

No source files were modified.

## Files touched

- `specs/rastan_direct_remap.json` (17 additive entries only)

## Phase A.1 — Remap entry insertion result

Inserted in ascending `arcade_pc` order:

- `0x03A00C`
- `0x03A012`
- `0x03AE86`
- `0x03AE8E`
- `0x03AE96`
- `0x03AEA2`
- `0x03AEAA`
- `0x03AEBC`
- `0x03AEC6`
- `0x03AECE`
- `0x03AEE0`
- `0x03AEEA`
- `0x03AEF0`
- `0x03AF0A`
- `0x03AF14`
- `0x03AF4C`
- `0x03AF72`

Field checks against Phase 6 worklist:
- `original_bytes` match: PASS (all 17)
- `replacement_bytes` match: PASS (all 17)
- `note` copied verbatim: PASS (all 17)

Inherited-site exclusion checks:
- `0x03AEF6`: ABSENT
- `0x03AEFE`: ABSENT
- `0x03AF00`: ABSENT
- `0x03AF02`: ABSENT

## Phase A.2 — Build result

Command executed:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Result: **FAIL** (STOP)

Failure detail:
- Postpatch tool raised:
  - `RuntimeError: Expected 56 opcode replacements but applied 73.`

Cause of mismatch is explicit in current tooling/metadata:
- `specs/rastan_direct_remap.json` now has `opcode_replace_count: 56` (stale after adding 17 entries)
- `tools/translation/postpatch_startup_rom.py` also enforces count `56` in verification path

## Phase A.3 — Verification status

Not executed due Phase A.2 STOP (build failure).

Per prompt STOP conditions:
- Build failed, so verification could not proceed.

## STOP status

STOP triggered: YES

Reason:
- Build failure due opcode replacement count guard mismatch (`expected 56`, `applied 73`).

No workaround was applied in this phase.
