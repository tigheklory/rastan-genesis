# Cody - Build 0165 Targeted Player-Source Writer Rebase

**Date:** 2026-07-13  
**Type:** Implementation + verification  
**Build context:** Build 0164 accepted local baseline for this task; produce Build 0165.  
**Scope:** Targeted per-site WRAM-immediate rebases only for active-gameplay player-source population writers feeding `A5+0x11B2` / `Genesis-WRAM 0x00FF11B2`. Preserve Build 0164 `0x041F5E` destination split. Keep systemic WRAM-immediate rebase gated off. No D00298, scroll, VDP DMA, LUT, scene-loader, collision/death, or broad PC090OJ work.

## Baseline

- Branch: `rastan-direct-proposal`
- Build before task: `0164`
- Build 0164 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0164.bin`
- Build 0164 SHA256: `76e93b2f66563632216c03377a679e47a7655e17e78731b230e81a6f00435c6a`
- Build 0164 size: `1,581,268` bytes
- Relevant prior docs:
  - `docs/design/Andy_player_source_block_population_fix_attempt.md`
  - `docs/design/Andy_build0164_systemic_wram_immediate_rebase.md`

## Phase 0

Classification: **EXTENDING**. This extends the KF-044 / OPEN-017 player-source-block thread after Build 0164 proved the `0x041F5E` destination split safe but inert while `Genesis-WRAM 0x00FF11B2` stayed empty.

Relevant priors:

- KF-044: raw arcade-WRAM immediate literals can leave Genesis WRAM producers writing to ROM aliases; blanket/systemic rebasing regressed pre-spawn progression and must remain gated off.
- OPEN-017: gameplay/player sprite bring-up remains active.
- OPEN-001 / OPEN-024: rendering context only.

Rediscovery hazards touched: KF-044. No contradiction of a CONFIRMED/STRONG finding detected.

Architecture compliance: **CONFIRMED**. The change is byte-neutral opcode replacement of immediate operands in copied arcade code. The arcade code remains the program; Genesis-side code remains helper/opcode-replacement only; rendering still flows through staging -> VBlank commit -> VDP. No NOP/RTS bypass, no hardcoded SAT/player sprites, no broad PC090OJ rewrite.

## Implementation

Added five targeted `opcode_replace` entries in `specs/rastan_direct_remap.json` for active-gameplay player-source writer base loads:

| arcade_pc | runtime_genesis_pc | original immediate | replacement immediate | purpose |
|---:|---:|---:|---:|---|
| `0x054492` | `0x054692` | `0x0010D1D2` | `0x00FF11D2` | source sub-block at `A5+0x11D2` |
| `0x05457A` | `0x05477A` | `0x0010D1B2` | `0x00FF11B2` | fallback/clear population base |
| `0x0545BA` | `0x0547BA` | `0x0010D1B2` | `0x00FF11B2` | active player-source population base |
| `0x0546A8` | `0x0548A8` | `0x0010D1F2` | `0x00FF11F2` | source sub-block at `A5+0x11F2` |
| `0x05475A` | `0x05495A` | `0x0010D212` | `0x00FF1212` | source sub-block at `A5+0x1212` |

These replacements preserve the original `MOVEA.L #imm,A1` opcode shape and instruction length (`6 -> 6` bytes). They are not a systemic pass.

Intentionally unchanged:

- `spec.wram_immediate_relocation.enabled = false`
- pre-spawn ROM-alias dependency sites:
  - `arcade_pc 0x051E00` / `runtime_genesis_pc 0x052000`
  - `arcade_pc 0x05288C` / `runtime_genesis_pc 0x052A8C`
  - `arcade_pc 0x052A6C` / `runtime_genesis_pc 0x052C6C`
- Build 0164 `pc090oj_workram_block_sprites_41f5e` destination split, which maps block A to records `120..137` and block B to records `92..95`.

## Invariant Delta

- `opcode_replace` count: `137 -> 142`
- `total_genesis_bytes_covered`: unchanged at `0x1820D4`
- Mechanical reason: the five new replacements are byte-neutral immediate-operand substitutions.

The first release invocation was stopped by the canonical gate because I initially expected coverage `0x1820F2`. The gate reported the correct mechanical value:

```text
expected total_genesis_bytes_covered=0x1820F2 and opcode_replace patched_site count=142; got total_genesis_bytes_covered=0x1820D4 opcode_replace patched_site count=142
```

After correcting both canonical invariant files to `0x1820D4`, the release target was rerun and passed.

## Build 0165

- Command: `source tools/setup_env.sh && make -C apps/rastan-direct release`
- Result: **PASS**
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0165.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `dd2e4d63ece2b7862b58da33b9c662114a27659844f5ef4154b2cf3a55986c4c`
- Size: `1,581,268` bytes
- Counter after build: `165`
- Numbered vs rolling ROM: byte-identical (`cmp=0`)
- Release trace directory: `states/traces/rastan_direct_video_test_build_0165_mame_30s_20260713_193903/`

## Static Verification

Patched runtime bytes in Build 0165:

```text
runtime_genesis_pc 0x054692: 227C00FF11D2207C
runtime_genesis_pc 0x05477A: 227C00FF11B232FC
runtime_genesis_pc 0x0547BA: 227C00FF11B2343C
runtime_genesis_pc 0x0548A8: 227C00FF11F2207C
runtime_genesis_pc 0x05495A: 227C00FF1212343C
```

Forbidden pre-spawn sites remain raw/canonical:

```text
runtime_genesis_pc 0x052000: 227C0010D1B25489
runtime_genesis_pc 0x052A8C: 207C0010D1B20C6D
runtime_genesis_pc 0x052C6C: 207C0010D1B25488
```

Build 0164 destination split remains present in `pc090oj_hooks.s`: `pc090oj_workram_block_sprites_41f5e` uses base records `120` and `92`; the default `pc090oj_workram_block_sprites` path remains `0` and `18`.

## Runtime Validation

Trace directory:

- `states/traces/build0165_targeted_player_source_writer_rebase_20260713_194138/`

Artifacts:

- `build0165_player_source_validate.lua`
- `build0165_player_source_validate.txt`
- `build0165_player_source_writes.csv`
- `build0165_representation_snapshot.lua`
- `build0165_representation_snapshot.txt`
- `mame_stdout.log`
- `mame_stderr.log`
- `mame_exit_code.txt`

MAME exited status `0`.

### Build 0164 Control

Existing Build 0164 control evidence (`states/traces/player_src/gen0164.txt`) reached gameplay but showed:

- `src 0xFF11B2`: all zero at gameplay frames `560` and `620`
- `records 120..137`: code words all zero at gameplay frames `560` and `620`
- source writers after frame `280`: `NONE`
- `represented=6`, `producer_writes` growing

### Build 0165 Result

Build 0165 reaches gameplay state `2/3/0` and activates the source writers.

At frame `560`:

```text
state=0002/0003/0000 represented=24 staged_active=24 scan_active=1 mirror_dirty=0
src_nonzero_words=51 obj120_137_nonempty=15 obj92_95_nonempty=4
```

Representative source records at `Genesis-WRAM 0x00FF11B2`:

```text
src00:4003 0025 009E 0010
src01:4003 0035 009F 0010
src04:4003 002D 008E 0018
src05:4003 003D 008F 0020
src06:4003 003D 0090 0010
src08:4003 004D 010B 0020
src09:4003 004D 010C 0010
src10:4003 005D 010D 0020
src11:4003 005D 010E 0010
```

Representative mirror records `120..137` after the Build 0164 split copies them:

```text
rec120:4003 0021 009E 0010
rec121:4003 0031 009F 0010
rec124:4003 0029 008E 0018
rec125:4003 0039 008F 0020
rec126:4003 0039 0090 0010
rec128:4003 0049 010B 0020
rec129:4003 0049 010C 0010
rec130:4003 0059 010D 0020
rec131:4003 0059 010E 0010
```

Source writer PCs observed during gameplay include the active-gameplay writer family:

```text
0546D6/0546DA/0546DE/0546E2
0546F6/054708/05470E/054730
0547D2/0547D6/0547DA/0547DE
0547F2/054804/05482C/05484E
05490C/05491E/054924/054946
054974/05497A/054988/05498E
```

The trace also saw earlier non-gameplay clears/writes at `0x03A4D4` and `0x03B102`; these do not invalidate the active-gameplay result.

Palette lines remained populated in gameplay snapshots:

```text
palette nz L0=15 L1=14 L2=15 L3=15
```

### Representation / SAT Snapshot

The follow-up representation snapshot confirms the core player-cluster records reach representation and staged SAT during gameplay.

At frame `560`:

```text
rec120 slot=01 represented=1 obj=4003 0021 009E 0010 sat=0099 0502 EC04 0090
rec121 slot=02 represented=1 obj=4003 0031 009F 0010 sat=00A9 0503 EC08 0090
rec124 slot=03 represented=1 obj=4003 0029 008E 0018 sat=00A1 0504 EC0C 0098
rec125 slot=04 represented=1 obj=4003 0039 008F 0020 sat=00B1 0505 EC10 00A0
rec126 slot=05 represented=1 obj=4003 0039 0090 0010 sat=00B1 0509 EC14 0090
rec128 slot=09 represented=1 obj=4003 0049 010B 0020 sat=00C1 050A EC24 00A0
rec129 slot=0A represented=1 obj=4003 0049 010C 0010 sat=00C1 050B EC28 0090
rec130 slot=0B represented=1 obj=4003 0059 010D 0020 sat=00D1 050C EC2C 00A0
rec131 slot=0C represented=1 obj=4003 0059 010E 0010 sat=00D1 0500 EC30 0090
```

Records `132..134` remain not represented:

```text
rec132 slot=FF represented=0 obj=0010 5551 09DB 5522
rec133 slot=FF represented=0 obj=0010 2533 09DB 1542
rec134 slot=FF represented=0 obj=0010 2334 09DB 4445
```

## Remaining Caveat

The targeted rebase successfully makes the source block live and makes records `120..137` populate, but it does **not** prove final visual correctness.

Records `132..134` carry suspicious words such as:

```text
rec132:0010 5551 09DB 5522
rec133:0010 2533 09DB 1542
rec134:0010 2334 09DB 4445
```

These are downstream/source-content evidence to preserve, not a reason to broaden this patch. The prompt's boundary was only to populate the active gameplay player-source block and keep the Build 0164 destination split intact.

## Assessment

Proven:

- Build 0165 preserves gameplay progression to state `2/3/0`.
- The five targeted active-gameplay WRAM immediates are rebased in the ROM.
- The systemic WRAM-immediate pass remains gated off.
- The forbidden pre-spawn sites remain raw/canonical.
- `Genesis-WRAM 0x00FF11B2` is no longer empty during gameplay.
- Build 0164's destination split is now live: records `120..137` and `92..95` are populated from the mapped source blocks.
- Represented/staged sprite counts rise to `24` at gameplay frame `560`, versus the Build 0164 control's `6`.
- Player-cluster records `120/121/124/125/126/128/129/130/131` reach representation and staged SAT during gameplay.

Not proven:

- Player visual correctness on screen.
- Correctness of every source record, especially records `132..134`, which remain not represented.
- Any fix for D00298, collision/death, scroll, VDP DMA, LUTs, scene loader, or broader sprite identity.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-001, OPEN-024 (context).
- New issues opened: NONE.
- Issues closed: NONE.
- Intentionally deferred: D00298, collision/death, scroll direction, VDP DMA, LUTs, scene loader, pre-spawn ROM-alias dependency, broad PC090OJ rewrite, hardcoded sprites/SAT.

## KNOWN_FINDINGS Impact

Option C — proposed update to KF-044 is appropriate after review: Build 0165 demonstrates that a targeted per-site active-gameplay rebase can populate `0x00FF11B2` and activate the Build 0164 `0x041F5E` destination split while leaving the systemic pass gated off and the pre-spawn dependency untouched. I did not edit `KNOWN_FINDINGS.md` in this task.

## STOP

STOP triggered: **NO**.
