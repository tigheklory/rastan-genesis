# Cody — Build 0255 Attract Demo Scripted Input Fix

## Result

Build 0255 implements the two indivisible address-provenance corrections proven by the prior audit. The retained arcade demo player now selects a valid relocated script, advances its cursor, and emits the same early active-low input sequence as the arcade reference. No input-owner, gameplay, rendering, or hardware-service source was redesigned.

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0255.bin`
- SHA-256: `edfd03534b1766309de105a1dad00671d0ac73eb3ca0fa5dfe7cc3859b378673`
- Size: `1,592,224` bytes
- Counter: `255`
- Canonical gate: `GATE_PASS`
- Build 0254 remains preserved and byte-verified.
- STOP triggered: **NO**

## Baseline and user-observed issue

The accepted baseline was Build 0254 at `dist/rastan-direct/rastan_direct_video_test_build_0254.bin`, SHA-256 `53bf25f4f2a090864aaab3fad98ce1646b15226d218f5e907468e52212c0b7e4`, size `1,592,224`, counter `254`. The rolling ROM initially matched it. User verification accepted the D00298/D002B0 writer repair and retained frontend and gameplay visuals, but attract gameplay showed no scripted Rastan movement.

Before modification, the worktree already contained the accepted Build 0254 source/spec/generated changes and the documentation synchronization changes. They were preserved. This task changed only the authorized remap/gate inputs, normal-build outputs, this report, and `AGENTS_LOG.md`.

## Required evidence read

The implementation followed `AGENTS.md`, `RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`, the latest relevant `AGENTS_LOG.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, and the canonical PC080SN/PC090OJ replacement policy.

Task-specific reports read:

- `docs/design/Andy_build0249_shared_native_sprite_emitter_contract.md`
- `docs/design/Cody_build0254_d00298_raw_pc090oj_writer_fix.md`
- `docs/design/Cody_known_findings_sync_0249_0254.md`
- `docs/design/Cody_attract_demo_scripted_input_provenance_audit.md`

Supporting implementation evidence included the current remap spec, address map, symbols, generated disassembly, `tilemap_hooks.s`, and the existing `opcode_replace` and `absolute_long_pointer_tables` consumers in the postpatch/gate tools.

## Prior audit and state causality

The audit proved that retained arcade `FUN_00052b4a` at `0x052B4A` owns demo playback, is called from `FUN_0005100a`, and is activated by `FUN_0005126e`. It should receive active demo status, stage `1`, a valid script pointer, and a pair cursor; it should then write `A5+0x137A` before player/action logic.

Earlier arcade initialization and `FUN_0005126e` correctly create that state. It previously failed because:

1. selector derivation read raw arcade address `0x0010C118` rather than mapped `A5+0x118`; and
2. the copied table at arcade `0x052C1C` retained stale embedded arcade ROM targets.

The repair changes those sources only. It does not seed state, reorder initialization, skip or duplicate a write, or change the demo player's arithmetic/control flow.

## Exact spec changes

Only `specs/rastan_direct_remap.json` gained the two required declarations.

### Selector read

- Arcade PC: `0x052B66`
- Original instruction: `move.b 0x0010C118,d0`
- Original bytes: `10390010C118`
- Patched instruction: `move.b 0x00FF0118,d0`
- Replacement bytes: `103900FF0118`

This is a same-instruction, byte-neutral source-operand rebase through the established `opcode_replace` mechanism. It is not an equal-length control-flow workaround: no behavior is suppressed or redirected, and the original instruction semantics are retained against the correct mapped state.

### Embedded pointer table

The existing schema was sufficient and required no new tool behavior:

```json
{
  "table_address": "0x052C1C",
  "entry_count": 9,
  "entry_size_bytes": 4
}
```

The established consumer relocates only entries inside the declared copied-ROM source window, using the same relocation/shift model that produces `address_map.json`. The manifest reports `entry_count: 9`, `fixes: 9`, and runtime table address `0x052E1C`.

The spec expectation and paired canonical gate constants changed from 220 to 221 opcode-replacement sites. This paired tooling edit was required by the normal canonical gate. Coverage remains byte-neutral at `0x184BA0`.

## Original table and address-map proof

Every mapping below was queried from generated `build/rastan-direct/address_map.json`, not assumed from arithmetic.

| Index | Original arcade value | Emitted Genesis value | Address-map kind |
|---:|---:|---:|---|
| 0 | `0x0005354E` | `0x0005374E` | `arcade_copy` |
| 1 | `0x00052C40` | `0x00052E40` | `arcade_copy` |
| 2 | `0x00052C44` | `0x00052E44` | `arcade_copy` |
| 3 | `0x0005354E` | `0x0005374E` | `arcade_copy` |
| 4 | `0x00052F4A` | `0x0005314A` | `arcade_copy` |
| 5 | `0x0005324C` | `0x0005344C` | `arcade_copy` |
| 6 | `0x00052C48` | `0x00052E48` | `arcade_copy` |
| 7 | `0x00052C48` | `0x00052E48` | `arcade_copy` |
| 8 | `0x00052C48` | `0x00052E48` | `arcade_copy` |

The table itself maps `0x052C1C -> 0x052E1C` as `arcade_copy`. The selector site maps `0x052B66 -> 0x052D66` as `patched_site`, origin `opcode_replace`.

## Emitted static validation

Build 0255 emitted these exact selector bytes:

```text
00052d66: 10 39 00 ff 01 18
52d66: 1039 00ff 0118  moveb 0xff0118,%d0
```

The runtime table is:

```text
00052e1c: 0005374e 00052e40 00052e44 0005374e
00052e2c: 0005314a 0005344c 00052e48 00052e48
00052e3c: 00052e48
```

No original arcade pointer remains in the emitted nine-entry table. Script bytes remain present at `0x052E40`, `0x052E44`, `0x052E48`, `0x05314A`, `0x05344C`, and `0x05374E`. For example, the first mapped data begins `FF F7 00 00 FF FB 00 00 46 FF 51 F7 ...`, and the selected stage-1 stream at `0x05374E` begins `6B FF 32 F7 01 E7 06 E5 ...`.

The Build 0254 raw PC090OJ destination repair is intact:

```text
0x05A71E: 207C00FFB232
0x05A754: 207C00FFB24A
```

Generated invariants:

- opcode-replacement sites: `221` (exactly +1)
- total Genesis bytes covered: `0x184BA0` (unchanged)
- gaps: `[]`
- overlaps: `[]`

## Matched arcade/Genesis demo trace

Temporary read-only trace output is under `/tmp/build0255_demo_match/`:

- arcade: `/tmp/build0255_demo_match/arcade/timeline.csv`
- Genesis: `/tmp/build0255_demo_match/genesis/timeline.csv`

Commands:

```bash
TRACE_DIR=/tmp/build0255_demo_match/arcade STATE_BASE=0x10c000 MAX_FRAMES=4200 \
  timeout 180s mame rastan -rompath roms -video none -sound none -nothrottle \
  -skip_gameinfo -autoboot_script /tmp/build0255_demo_match.lua

TRACE_DIR=/tmp/build0255_demo_match/genesis STATE_BASE=0xff0000 \
  SCENE_ADDR=0xffb8b0 MAX_FRAMES=4200 timeout 180s mame genesis \
  -cart dist/rastan-direct/rastan_direct_video_test_build_0255.bin \
  -video none -sound none -nothrottle -skip_gameinfo \
  -autoboot_script /tmp/build0255_demo_match.lua
```

Equivalent watched state was stage `+0x118`, remaining duration `+0x1372`, current byte `+0x1373`, cursor `+0x1374`, demo status `+0x1376`, and consumed input `+0x137A`; Genesis scene `0xFFB8B0` was also sampled.

### Matched behavior

- Arcade: demo active by frame 2587; first valid pair at frame 2589; cursor advances from `0` to `1` with current `FF`, then to `2` with `F7`.
- Genesis: demo active by frame 2689; at the former frame-2692 failure boundary it remains `0001`, cursor is `1`, current is `FF`, and remaining duration is `6A` rather than immediately finishing.
- The stage byte is `01` and selector override is `0`, so retained arithmetic selects valid table index `3`, whose emitted pointer is `0x0005374E`.
- Genesis cursor advances through the same early sequence as arcade: `FF, F7, E7, E5, F5, FD, F5, F7, F5, E5, ED, FD...`.
- Genesis `0x00FF137A` receives matching active-low values including `FFF7`, `FFE7`, `FFE5`, `FFF5`, `FFFD`, and `FFED`.
- Build 0255 remains in active demo playback until external frame 3892, roughly 1,200 frames past the old immediate failure, reaching cursor `0x42`. A later attract-state transition resets/finishes that run at frame 3893; it does not contradict the repaired initial selection/cursor causality. Full long-run arcade timing equivalence remains outside this bounded repair and is not claimed.

The sampled external frames can straddle VBlank and arcade update cadence, but the retained static call order is decisive for ownership: normal latch copy writes `A5+0x137A` first, `FUN_00052b4a` writes scripted input afterward, and player/action logic follows. No normal-input write occurs after the demo writer within that update chain. MAME PC-attribution taps were not used because their limitations were established in the preceding audit; no PC attribution is overclaimed.

## Build and smoke validation

Exactly one normal release invocation was run:

```bash
source tools/setup_env.sh
make -C apps/rastan-direct release PC090OJ_MIRROR_RECORDS=256 RASTAN_GAMEPLAY_HUD_SPRITES=2
```

Results:

- counter advanced exactly `254 -> 255`;
- numbered artifact is `dist/rastan-direct/rastan_direct_video_test_build_0255.bin`;
- rolling and numbered ROMs match by SHA-256 and size;
- `GATE_PASS`;
- standard 30-second MAME smoke trace: `states/traces/rastan_direct_video_test_build_0255_mame_30s_20260804_112915/`;
- smoke frames: `1798`;
- `vdp_ports_live count=47197` through frame 1797;
- unique unmapped memory addresses: none observed;
- no canonical gap or overlap.

Build 0254 remains at its original path, size, and SHA-256.

## Architecture compliance

The arcade demo routine remains the sole demo scheduler and input-playback owner. No Genesis-owned loop, state machine, seed, fallback, helper, or controller-policy change was introduced.

The graphics semantic cut remains `arcade actor/object semantic state -> native Genesis SAT`; the PC090OJ gameplay scan/decode/chip tail remains retired. Native Plane A/B production and the PC080SN chip tail remain unchanged. Transitional frontend compatibility storage and its existing producers/consumers remain isolated and are neither expanded nor made authoritative by this input-only fix. No rendering-policy checklist boundary changes.

Andy architecture review after implementation is **not recommended**: emitted evidence confirms the existing bounded translation mechanisms were sufficient. Further unrelated input ownership or long-run gameplay divergence work would require its own provenance task.

## Files changed

- `specs/rastan_direct_remap.json`
- `tools/translation/postpatch_startup_rom.py` (paired canonical count only)
- `tools/translation/verify_canonical_rom.py` (paired canonical count only)
- generated `build/rastan-direct/address_map.json`
- generated `build/rastan-direct/rastan_direct_patch_manifest.json`
- generated `build/rastan-direct/build_counter.txt`
- generated `build/genesis_postpatch.disasm.txt`
- generated `build/rom_inventory.json`
- numbered and rolling Build 0255 ROM artifacts
- standard Build 0255 smoke trace
- `docs/design/Cody_build0255_attract_demo_scripted_input_fix.md`
- `AGENTS_LOG.md`

No assembly, Makefile, input helper, PC080SN/PC090OJ source, palette/CRAM, audio, collision, rope, or gameplay-lifecycle file changed.

## User verification required

- BlastEm attract demo must visibly follow scripted movement.
- The accepted D00298/D002B0 fatal must remain absent.
- Normal gameplay controls and Rastan/lizard/bat/axe rendering must remain intact.
- Frontend/title/story/high-score screens must remain intact.

Do not treat visual acceptance as complete until Tighe verifies these items.

## Open/Closed Issues and KNOWN_FINDINGS impact

- OPEN-016: touched by the now-implemented demo pointer-table subcase; not globally closed.
- OPEN-017: touched by the raw WRAM selector rebase and scripted-input behavior; not globally closed.
- OPEN-024: context only; accepted D00298/D002B0 remaps preserved.
- New issues opened: **NONE**.
- Issues closed: **NONE**.
- Deferred: user visual acceptance, full long-run attract equivalence, frontend-native PC090OJ/PC080SN conversion, and compatibility retirement.
- KNOWN_FINDINGS: no pre-acceptance edit. The build applies KF-028, KF-057, and KF-058; a durable Build 0255 finding may be indexed only after user acceptance under project convention.

## Stop status

STOP triggered: **NO**. Both indivisible fixes are present, the single authorized numbered build passed its gate, static validation is exact, and the matched trace confirms the intended causal repair.
