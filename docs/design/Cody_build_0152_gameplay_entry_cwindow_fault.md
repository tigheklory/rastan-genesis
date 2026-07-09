# Cody - Build 0152 Gameplay-Entry C-window Fault

**Date:** 2026-07-09
**Type:** Implementation + evidence
**Build produced:** Build 0152
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0152.bin`
**SHA256:** `3d805331815588576a3fdeef732a7b094f3c15997b66c76830827adfc2f35214`
**Scope:** Route only the proven gameplay-entry raw PC080SN FG write at `arcade_pc 0x03A72A` / `runtime_genesis_pc 0x03A92A`. No bookmark. No BlastEm claim. No item-scroll, sprite, palette, title/story/BEST5, or `0x03D04C` fix.

## Phase 0 Baseline

- Branch: `rastan-direct-proposal`
- Starting HEAD: `eac4699 Build 151 High Score Table`
- Starting worktree: clean
- Accepted prior ROM: `dist/rastan-direct/rastan_direct_video_test_build_0151.bin`
- Build 0151 SHA256: `eab3a3fbfa27327ff5a34ba729467e43f59b3c2940f8bc84c27310a7f1e9429b`
- Build counter before release: `151`

Relevant constraints loaded from `RULES.md`, `ARCHITECTURE.md`, `OPEN_ISSUES.md`, `KNOWN_FINDINGS.md`, `AGENTS_LOG.md`, and the OPEN-018 / Build 0107 / Build 0151 design notes. This task extends OPEN-018 and does not alter architecture.

## Address Mapping

All arcade-to-Genesis mappings were checked through `build/rastan-direct/address_map.json`.

| Address | Mapping result |
|---|---|
| `arcade_pc 0x03A72A` | exact `patched_site` after Build 0152, `runtime_genesis_pc 0x03A92A` |
| `arcade_pc 0x03D04C` | exact `arcade_copy`, `runtime_genesis_pc 0x03D24C` |
| `arcade_pc 0x03A36A` | exact `arcade_copy`, `runtime_genesis_pc 0x03A56A` |
| `arcade_pc 0x03A4EC` | exact `arcade_copy`, `runtime_genesis_pc 0x03A6EC` |

No `+0x200` arithmetic was used as proof.

## Arcade Intent Evidence

Evidence directory: `states/traces/build_0152_gameplay_entry_cwindow_fault/`

Original arcade MAME runtime capture used `rastan` / World Rev 1. The compact extracted event log is `arcade_intent_breakpoint_events.log`; the Lua route/tap log is `arcade_intent_lua.log`.

Proven event:

```text
EV_A72A ... pc=03A72C ... d0=00000031 ... src117=01 state=0002/0002/0006 near=0000,0020,0000,0020
STATE frame=188 state=0002/0002/0007 near=0000,0031,0000,0020
```

Interpretation:

- Observable fact: original arcade reaches `arcade_pc 0x03A72A` during state `2/2/6`.
- Observable fact: the live value is `D0=0x00000031`.
- Observable fact: source byte `A5+0x0117` is `0x01`; local code forms `D0 = byte(A5+0x0117) | 0x0030`.
- Observable fact: PC080SN FG nearby words change from `0000,0020,0000,0020` to `0000,0031,0000,0020` by the next observed state.
- Interpretation: `0x03A72A` is a dynamic one-cell FG tile/code write, not a bulk clear or unrelated hardware side effect.

The adjacent writer `arcade_pc 0x03D04C` / `runtime_genesis_pc 0x03D24C` was investigated as a sibling candidate, but same-route proof was not established in this task. It remains unpatched and tracked under OPEN-018 as a surviving register-absolute raw-write candidate.

## Implementation

Added `genesistan_hook_inline_fg_write_3a92a` in `apps/rastan-direct/src/tilemap_hooks.s` and declared it in `specs/rastan_direct_remap.json`.

The wrapper:

```asm
genesistan_hook_inline_fg_write_3a92a:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    lea     0x00C08C60, %a0
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_fg_fill
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    tst.w   %d0
    rts
```

Reasoning:

- The original instruction writes the low word of live `D0` to `HW_ADDRESS 0x00C08C62`, the tile/code half of the cell whose base is `0x00C08C60`.
- `genesistan_hook_tilemap_fg_fill` already implements the OPEN-018 live-LUT FG staging path.
- The wrapper preserves all registers and uses `tst.w %d0` after restore to reproduce the original `MOVE.W d0,(abs).L` condition-code effect for N/Z/V/C.
- At this site, the next instruction is `moveq #-126,%d0`, so CCR is overwritten immediately, but the wrapper still preserves the original instruction's local condition semantics.

Spec opcode replacement:

- `arcade_pc`: `0x03A72A`
- `original_bytes`: `33C000C08C62`
- `replacement_bytes`: `4EB9{symbol:genesistan_hook_inline_fg_write_3a92a}`
- Replacement length: 6 bytes, exactly matching the original six-byte `move.w d0,(abs).L`.
- No NOP, RTS bypass, shadow RAM, force-state, or VBlank/commit-path change.

## Build Verification

Release command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result:

- Boot guard before postpatch: PASS
- Boot guard after postpatch: PASS
- Canonical gate: `GATE_PASS`
- Numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0152.bin`
- Rolling artifact: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Numbered and rolling ROMs are byte-identical (`cmp=0`)
- SHA256: `3d805331815588576a3fdeef732a7b094f3c15997b66c76830827adfc2f35214`
- `opcode_replace` count: `133 -> 134`
- `total_genesis_bytes_covered`: `0x181D50 -> 0x181D68`

The invariant constants were updated in both canonical verification scripts to the observed mechanical values.

Generated disassembly confirms the raw site is no longer raw:

```asm
3a920: 4240            clrw %d0
3a922: 102d 0117       moveb %a5@(279),%d0
3a926: 0040 0030       oriw #48,%d0
3a92a: 4eb9 0007 07fa  jsr 0x707fa
3a930: 7082            moveq #-126,%d0
```

Generated disassembly confirms the wrapper:

```asm
707fa: 48e7 fffe       moveml %d0-%fp,%sp@-
707fe: 41f9 00c0 8c60  lea 0xc08c60,%a0
70804: 7201            moveq #1,%d1
70806: 6100 fecc       bsrw 0x706d4
7080a: 4cdf 7fff       moveml %sp@+,%d0-%fp
7080e: 4a40            tstw %d0
70810: 4e75            rts
```

Address map verification after build:

- `arcade_pc 0x03A72A` is now a `patched_site` mapping to `runtime_genesis_pc 0x03A92A`.
- `arcade_pc 0x03D04C` remains `arcade_copy` mapping to `runtime_genesis_pc 0x03D24C`.

## Runtime Validation

Focused Build 0152 MAME validation used `build0152_wrapper_store_dump.cmd` and `build0152_validate.lua` under the evidence directory.

The debugger breakpoint at wrapper entry armed a temporary breakpoint at the exact FG store inside `genesistan_hook_tilemap_fg_fill` and quit immediately after dumping register state. This avoids scratch-counter contamination from later gameplay writes.

Dump evidence (`build0152_wrapper_store_dump.bin`, MAME text dump format):

```text
FFFEE0:  0007 078A 0000 0009 0000 0630 00FF 509E
FFFEF0:  0007 07FC 0000 0031 0003 C37A 0000 0000
```

Decoded:

- Wrapper entry breakpoint: `PC=0x000707FC`, live `D0=0x00000031`.
- Armed store breakpoint: post-instruction `PC=0x0007078A`, composed cell `D3=0x0009`, staging offset `D0=0x0630`, staging base `A6=0x00FF509E`.
- Interpretation: the original arcade dynamic code word is now converted through the live LUT and staged into `staged_fg_buffer`, not raw-written to the PC080SN/VDP mirror address.

The autonomous MAME state route reached gameplay-entry state progression through `2/2/6`, `2/2/7`, `2/2/4`, `2/2/5`, and `2/3/0` without a MAME exception during the validation run. This does not prove BlastEm strict-target behavior; Tighe runtime confirmation is still required.

## Non-Claims / Deferred

- `runtime_genesis_pc 0x03D24C` / `arcade_pc 0x03D04C` is not fixed in Build 0152.
- No claim is made that BlastEm/Nomad strict-target behavior is fixed until Tighe tests Build 0152.
- No source/spec changes were made for item-scroll, sprites, palette, PC090OJ clipping, stale `0x2731`, title/story/BEST5/high-score visuals, or VBlank/commit timing.
- No new KNOWN_FINDINGS entry was added; this is an OPEN-018 sub-case using the existing raw-PC080SN routing model.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-018 updated: Build 0152 closes the proven `0x03A92A` register-absolute raw FG sub-case; `0x03D24C` remains open.
- OPEN-001 / OPEN-005 context only.
- KNOWN_FINDINGS: Option A, no update.

## STOP

STOP triggered: NO.
