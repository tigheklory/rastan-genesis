# Cody - Lizard Actor Activation Progression Fix and Build 0206

**Date:** 2026-07-18
**Type:** Analysis-first bounded implementation + release build + runtime validation
**Build produced:** Build 0206/256
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0206.bin`
**SHA256:** `98dc3a1b58ab66403ceb90d3d397f621d0aa90bf616c48671c43080dc720a4ae`
**Scope:** Extend KF-064/KF-065 by restoring the upstream actor activation/progression path that lets block `A5+0x02C8` lizard entries 4..7 reach the original mapped b5 writer. No actor seeding, no forced records/SAT, no direct sprite injection, no visual/palette/combat/black-bar work.

Address labels: `arcade_pc` / `runtime_genesis_pc` are code addresses mapped through `build/rastan-direct/address_map.json`; `Genesis-WRAM` is Genesis work RAM; `arcade_WRAM` is original arcade work RAM.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-064 (first visible Stage-1 lizard men are block `A5+0x02C8` -> composite records ~140..229, not record 46), KF-065 (Build 0205 whole-block scratch staging route and Build 0205 b5 writer-provenance boundary), KF-063 (validated actor engine safety and shared `0x3C950` destination-aware writer), KF-060..KF-062 (PC090OJ actor/staging context), and issue context OPEN-017 / OPEN-024.

Rediscovery-hazard HIGH findings touched: KF-064 and related PC090OJ ownership findings. No contradiction of CONFIRMED/STRONG findings detected.

Architecture compliance: **CONFIRMED**. The fix preserves arcade code as the program: it rebases a stale copied arcade compare literal so the original actor scan can operate on the translated Genesis collision-buffer address range. It does not seed `b5`, force lizard actors, force PC090OJ records/SAT entries, add a second renderer, or bypass the staging -> representation -> VBlank/SAT pipeline.

## Baseline

- Counter before release: `205`.
- Build 0205 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0205.bin`.
- Build 0205 SHA256: `4238d2ffcd226c45f1251ccbe4e7e64fa9b642acb18c4957ab85e1fd888b4aee`.
- Build 0205 `opcode_replace`: `214`.
- Build 0205 `total_genesis_bytes_covered`: `0x182950`.

Prior evidence proved the exact activation writer but not the upstream cause:

- Arcade reaches `arcade_pc 0x00041320` (`move.b %d1,5(%a4)`) for entries `8,7,6,5,4`.
- `address_map.json` maps that writer to `runtime_genesis_pc 0x00041520`.
- Genesis Build 0205 reaches the mapped writer for positive-control entry 8 only.
- Genesis Build 0205 never reaches the mapped writer for entries 4..7 in the captured window.

## Evidence Artifacts

Trace directory: `states/traces/lizard_actor_activation_progression_fix_20260718_224821/`

Key evidence files:

- `scan_event_reduction.md` - original arcade versus Genesis Build 0205 reduced scan/writer comparison.
- `genesis_build0206_scan_event_reduction.md` - Build 0206 reduced scan/writer comparison.
- `genesis_build0206_acceptance_reduced.md` / `.json` - post-fix actor/window/mirror/represented metrics.
- `genesis_build0206_record46_probe.csv` - record-46 continuity probe.
- `arcade_scan_debug_trace.log`, `genesis_scan_debug_trace.log`, `genesis_build0206_scan_debug_trace.log` - retained debugger traces.

## State Causality

At the scan wrap/comparison PCs, `%a0` should be a pointer inside the translated Genesis collision buffer range:

```text
Genesis-WRAM collision base: 0x00FF1E00
Genesis-WRAM collision end:  0x00FF3E00
```

The earlier state creator is already translated correctly:

```asm
runtime_genesis_pc 0x00053C64: movea.l #0x00FF1E00,%a0
```

The backward lower-bound guard was also already translated correctly:

```asm
runtime_genesis_pc 0x000414E8: cmpa.l #0x00FF1E00,%a0
```

The missing state was the matching forward upper bound. Build 0205 still compared `%a0` against raw arcade work RAM end `0x0010FE00`:

```asm
runtime_genesis_pc 0x000414CC: cmpa.l #0x0010FE00,%a0
```

Because the scan pointer is now in Genesis-WRAM near `0x00FF1E00..0x00FF3DFF`, this stale upper bound caused the forward scan wrap path to subtract `0x2000` when it should not. The scan then moved into `0x00FA7Cxx`-style addresses, missed the collision word `0x3A00`, exhausted the scan, and never reached `runtime_genesis_pc 0x00041520` for entries 4..7.

## Pre-Fix Divergence

Original arcade scan/writer behavior from `scan_event_reduction.md`:

| Entry | Arcade result | Representative hit / writer |
|---:|---|---|
| 8 | hit + writer | `SCAN_HIT pc=0412FE a0=0010F154 word=3A00`; `WRITER pc=041322 d1=00000002` |
| 7 | hit + writer | `SCAN_HIT pc=0412FE a0=0010F154 word=3A00`; `WRITER pc=041322 d1=00000002` |
| 6 | hit + writer | `SCAN_HIT pc=0412FE a0=0010F154 word=3A00`; `WRITER pc=041322 d1=00000002` |
| 5 | hit + writer | `SCAN_HIT pc=0412FE a0=0010F154 word=3A00`; `WRITER pc=041322 d1=00000002` |
| 4 | eventual hit + writer | `SCAN_HIT pc=0412FE a0=0010F110 word=3A00`; `WRITER pc=041322 d1=00000001` |

Genesis Build 0205 behavior from the same reduction:

| Entry | Build 0205 result | Representative failure / hit |
|---:|---|---|
| 8 | positive control hit + writer | `SCAN_HIT pc=0414FE a0=00FC31D4 word=3A00`; `WRITER pc=041522 d1=00000002` |
| 7 | scan fail only | `SCAN_FAIL_FWD pc=0414E0 a0=00FA7C54 scan_count=0000` |
| 6 | scan fail only | `SCAN_FAIL_FWD pc=0414E0 a0=00FA7C54 scan_count=0000` |
| 5 | scan fail only | `SCAN_FAIL_FWD pc=0414E0 a0=00FA7C72 scan_count=0000` |
| 4 | scan fail only | `SCAN_FAIL_FWD pc=0414E0 a0=00FA7C3E scan_count=0000` |

**First exact upstream divergence:** the translated forward collision scan for entries 4..7 wraps against a stale raw upper bound, exits with `SCAN_FAIL_FWD`, and therefore never reaches the mapped b5 writer at `runtime_genesis_pc 0x00041520`.

## Fix Applied

A single byte-neutral opcode replacement was added to `specs/rastan_direct_remap.json`:

```json
{
  "type": "opcode_replace",
  "arcade_pc": "0x0412CC",
  "original_bytes": "B1FC0010FE00",
  "replacement_bytes": "B1FC00FF3E00"
}
```

This changes only the forward upper-bound compare:

```asm
runtime_genesis_pc 0x000414CC: cmpa.l #0x00FF3E00,%a0
```

The paired canonical invariants were updated in:

- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

Final invariant values:

- `CANONICAL_OPCODE_REPLACE_COUNT = 215`
- `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x182950`

The coverage is unchanged because this replacement is byte-neutral and subdivides already-covered copied code; the patched-site count increments by one.

## Build Attempt Notes

The release target was invoked until a valid artifact was produced after correcting mechanical invariant/spec expectations:

1. First attempt stopped before numbered artifact production because `specs/rastan_direct_remap.json` still expected `214` opcode replacements while the patcher applied `215`.
2. Second attempt stopped before numbered artifact production because the coverage invariant had been mechanically over-adjusted to `0x182956`; observed canonical coverage remained `0x182950`.
3. Third attempt passed after restoring coverage to `0x182950` and keeping opcode replacement count `215`.

## Build 0206 Artifact

- Counter: `205 -> 206`.
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0206.bin`.
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`.
- SHA256: `98dc3a1b58ab66403ceb90d3d397f621d0aa90bf616c48671c43080dc720a4ae` for both.
- Size: `1583440` bytes for both.
- Numbered vs rolling `cmp`: byte-identical.
- Release result: `GATE_PASS`.
- Release trace: `states/traces/rastan_direct_video_test_build_0206_mame_30s_20260718_225505/`.

## Static Verification

`build/rastan-direct/address_map.json` maps the fixed site exactly:

- `arcade_pc 0x000412CC` -> `runtime_genesis_pc 0x000414CC`.

Produced disassembly confirms the upper/lower/base triplet:

```asm
runtime_genesis_pc 0x000414CC: cmpa.l #0x00FF3E00,%a0
runtime_genesis_pc 0x000414E8: cmpa.l #0x00FF1E00,%a0
runtime_genesis_pc 0x00053C64: movea.l #0x00FF1E00,%a0
```

ROM bytes confirm:

- `0x414CC = B1 FC 00 FF 3E 00`
- `0x414E8 = B1 FC 00 FF 1E 00`
- `0x53C64 = 20 7C 00 FF 1E 00`

Patch manifest confirms:

- `postpatch_expected_opcode_replace_sites = 215`
- `postpatch_expected_total_genesis_bytes_covered = 0x182950`

## Post-Fix Runtime Validation

Build 0206 scan reduction proves entries 8..4 now reach the scan hit and mapped writer:

| Entry | Build 0206 counts | Representative hit / writer |
|---:|---|---|
| 8 | `SCAN_HIT=1`, `WRITER=1` | `SCAN_HIT pc=0414FE a0=00FF31D4 word=3A00`; `WRITER pc=041522 d1=00000002` |
| 7 | `SCAN_HIT=1`, `WRITER=1` | `SCAN_HIT pc=0414FE a0=00FF31D4 word=3A00`; `WRITER pc=041522 d1=00000002` |
| 6 | `SCAN_HIT=1`, `WRITER=1` | `SCAN_HIT pc=0414FE a0=00FF31D4 word=3A00`; `WRITER pc=041522 d1=00000002` |
| 5 | `SCAN_FAIL_FWD=1`, then `SCAN_HIT=1`, `WRITER=1` | `SCAN_HIT pc=0414FE a0=00FF31F4 word=3A00`; `WRITER pc=041522 d1=00000002` |
| 4 | `SCAN_HIT=1`, `WRITER=1` | `SCAN_HIT pc=0414FE a0=00FF31BE word=3A00`; `WRITER pc=041522 d1=00000001` |

The one remaining entry-5 `SCAN_FAIL_FWD` is followed by a successful later hit/writer and does not reproduce the Build 0205 permanent failure.

Build 0206 acceptance sampler:

- `valid_actors`: max `4`, first frame `549`, last `1443`.
- `actor_windows_nonzero`: max `5`, first frame `550`, last `1800`.
- `mirror_nonzero`: max `47`.
- `mirror_drawable`: max `47`.
- `mirror_visible`: max `36`.
- `represented`: max `36`, first frame `557`, last `1446`.
- `waiting`: max `0`.
- `represented_count`: max `53`.
- `active_count`: max `53`.
- `scan_active`: max `1`.

Max-valid sampled frame (`1031`) contained four valid lizard entries: entries `5`, `6`, `7`, and `8`. The automated drive did not capture five simultaneously valid actors, but the scan trace proves entries `4..8` all reach the activation writer and the actor-window sampler separately reaches five nonzero windows.

Record-46 continuity probe:

- Rows sampled: `692` data rows.
- Nonzero record-46 rows: `516`.
- Represented record-46 rows: `515`.
- First nonzero frame: `885`, code `0x0275`.
- First represented frame: `886`, SAT slot `40`, SAT tuple `y=0x00E1 attr=0xC4A0 x=0x0111`.
- Last nonzero frame: `1400`, code `0x0277`, represented in slot `40`.

This probe did not show a record-46 continuity regression from the lizard activation fix.

## Classification

**Root cause confirmed:** YES.

The Build 0205 one-lizard activation ceiling for entries 4..7 was caused by a missed mapped-work-RAM rebase in the collision scan's forward upper-bound compare at `arcade_pc 0x000412CC` / `runtime_genesis_pc 0x000414CC`. The state that should exist at the scan is an `%a0` pointer bounded by `0x00FF1E00..0x00FF3E00`; the base and lower bound already matched that translated range, but the upper bound still used raw arcade `0x0010FE00`.

**Smallest safe fix boundary:** the byte-neutral immediate rebase `0x0010FE00 -> 0x00FF3E00` at the existing copied arcade compare. No downstream staging, SAT, actor-state, or PC090OJ representation behavior was forced.

## USER MUST VERIFY

Runtime traces prove writer reachability and representation metrics, not final human visual acceptance. Tighe should verify on real interactive frontend/gameplay:

- Multiple lizard men visibly appear in Build 0206.
- Player control remains intact.
- Record-46 secondary sprite behavior remains acceptable.
- Lizard palette / bank-0x36 carrier remains as expected or still needs a separate fix.
- Feet/ground alignment and damage/contact behavior are still separate boundaries.
- Existing deferred issues remain: black bar/VBlank budget, stale record 132 sphere, bat palette, FG/sky/HUD, D00298, continue/game-over.

## OPEN / KNOWN_FINDINGS Impact

Open issues touched: OPEN-017 and OPEN-024. OPEN-017 is updated with the Build 0206 fix and validation. No new issue opened. No issue closed.

KNOWN_FINDINGS impact: **Option C** - KF-065 refined with the Build 0206 actor activation progression fix. KF-064 remains intact.

## STOP

STOP triggered: **NO**. Build 0206 was produced and validated within the bounded fix scope.
