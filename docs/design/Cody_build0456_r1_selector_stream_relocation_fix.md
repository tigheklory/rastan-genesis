# Build 0456 — R1 Selector-Stream Relocation Fix

**Date:** 2026-10-19

**Status:** CANDIDATE — Tighe real-hardware acceptance pending

**Issue:** OPEN-037
**Accepted baseline:** Build 0455

## Result

Build 0456 removes the stale generated Genesis address from the retained R1 map-selector initializer.
At arcade `0x0503CE`, `MOVE.L #imm,D0` now resolves semantic arcade target `0x050F6B` through the
existing final shift/address relocation pass. The generated operand is `0x051155`, exactly the current
`address_map.json` result. No build-specific runtime address or compensating delta remains in policy.

The established deterministic `_invincible` rope benchmark is `798 / 798 / 798` frames, median
`13,317.147 ms`, deterministic YES, exactly matching accepted Build 0455. This is mechanically and
performance validated but remains unaccepted until Tighe completes the required real-Genesis R1 test.

## Proven defect and repair

The retained arcade initializer performs:

```text
A1 = 0x050EE0 + word(A5+0x013E)
D1 = byte(A1)
D0 = 0x050F6B + D1
A5+0x10C6 = D0
```

The first base followed relocation. The second was permanently encoded as historical runtime
`0x051171` in `opcode_replace`. It was correct only for Build 0442. The verified mappings are:

| Build | map(arcade `0x050F6B`) | embedded operand | error |
|---|---:|---:|---:|
| 0442 | `0x051171` | `0x051171` | 0 |
| 0443/0444 | `0x051173` | `0x051171` | -2 |
| 0445/0446 | `0x051153` | `0x051171` | +30 |
| 0455 | `0x051155` | `0x051171` | +28 |
| 0456 | `0x051155` | `0x051155` | 0 |

The production spec now owns the reference as:

```json
{
  "arcade_pc": "0x0503CE",
  "original_bytes": "203C00050F6B",
  "relocate_after_shift": true,
  "replacement_template": "203C",
  "operand_kind": "abs_l_32bit",
  "operand_width": 4,
  "operand_arcade_target": "0x050F6B"
}
```

This remains a six-byte `MOVE.L #imm,D0`; it adds no shift and preserves the following original
`ADD.L D1,D0`. Pass B computes the final operand from the semantic arcade target plus the current
relocation and accumulated shift table.

## Causal chain and static selector result

The stale base seeded `A5+0x10C6` 28 bytes late in Build 0455. `FUN_000558E0` advanced that wrong
stream and published its values to `A5+0x10A8`. `FUN_00052732` treats values 4/5/6 as progression
events and sets `A5+0x10E8=7`, starting scripted auto-walk before the final map records and door.

Build 0455's wrong stream yields event 4 at progression `0x0E` and event 6 at `0x14`. The corrected
Build 0456 source bytes are byte-identical to original arcade selector data and restore the R1 sequence
whose first intended event 4 is at progression `0x10`; there is no stale premature 4/5/6 event.

The separate hardware-observed 0445 (~Segment 11) versus 0446 (~Segment 13) endpoint difference
remains an **unresolved secondary historical discrepancy**. It is not required to prove or evaluate
this current persistent-defect repair.

## Durable verifier

`tools/translation/verify_r1_selector_stream_relocation.py` is called immediately after postpatching
the canonical ROM and every configured variant. It proves:

- spec ownership is one `relocate_after_shift` entry, not `opcode_replace`;
- mapped arcade `0x0503CE` is still `MOVE.L #imm,D0`;
- its decoded operand equals `address_map(0x050F6B)` without a hard-coded Genesis value;
- all 157 selector-stream bytes are contiguous and equal original `maincpu` bytes.

Canonical and all six variants resolve operand and target to `0x051155`. Running the verifier on the
preserved Build 0455 ROM fails as intended:

```text
stale selector-stream operand: 0x051171 != map(0x050F6B)=0x051155
```

## Bounded sibling audit

The bounded scan covered `opcode_replace` entries that contain a ROM-range arcade address and a
different generated runtime address at the same operand offset. Besides the repaired `0x0503CE`, it
found 23 Build-0200 jump/fall arc-table references at arcade callsites `0x0505DC`, `0x0514B8`, and
`0x0520DC..0x0523C4`. Their semantic targets are `0x05B516`, `0x05B548`, `0x05B570`, `0x05B5A2`,
`0x05B5EC`, and `0x05B62E`.

Those 23 are structurally historical literals in the JSON, but their instruction forms belong to the
postpatcher's recognized absolute-long opcode set. The final Build 0456 operands at all 23 sites equal
their current address-map targets (for example, `0x05B5EC -> 0x05B60C`). They are not current runtime
defects, and changing their separate policy entries was outside this focused behavioral build. No
additional production change was made.

## Architecture boundary

This is copied-ROM data-reference relocation, not a PC080SN or PC090OJ native-replacement build. The
semantic cut is unchanged: retained arcade initializer/progression logic remains above the existing
native presentation boundaries. No chip-specific tail is newly removed, no transitional compatibility
layer is introduced, and no shadow RAM is added.

## Validation

| Check | Result |
|---|---|
| Root selector relocation verifier, seven ROMs | PASS |
| Assembly/link and shift reflow (76 sites) | PASS |
| Canonical gate | PASS |
| Gameplay-entry gate | PASS |
| Seven-epoch gate | PASS |
| Accepted item-screen verifier | PASS |
| Native title verifier | PASS |
| Shared HUD verifier | PASS |
| BEST-5 verifier | PASS |
| Fixed 30-second Genesis NTSC MAME validation | PASS |
| Complete seven-ROM family | PASS |
| `_invincible` verifier | PASS |
| Deterministic rope | PASS — `798/798/798`, `13,317.147 ms`, YES |

No late-game route, exploratory gameplay trace, save state, Lua probe, or manual gameplay navigation
was created or run. The only gameplay benchmark was the existing deterministic rope workflow.

## Artifacts

- Canonical ROM: `dist/rastan-direct/rastan_direct_video_test_build_0456.bin`
- Canonical SHA-256: `961fe13ab04a8571d704bbf39705571ec0910e6fa2300eadc0f41f3fb7ed9829`
- `_invincible` SHA-256: `c6e459c6df5efba0da47d0eddd5df301cce82e469ac4bfc17acefcc57f04fb97`
- Size: 2,739,896 bytes each
- Counter: 456
- Source state: uncommitted candidate working tree based on `e13f32d40584f7de2a42d0f56cdecfd417b7e644`
- Fixed30 evidence: `states/traces/rastan_direct_video_test_build_0456_mame_30s_20261019_172527/`
- Rope evidence: `states/traces/build0456_rope_attach_benchmark_invincible/`

## Scope and acceptance

Build-0455 item presentation, title, HUD, collision, player gameplay behavior, enemies, and the known
D3 glyph contract mismatch were not intentionally changed. Phase D and Phase E were not started.
OPEN-037 remains open until Tighe verifies the full R1 Subround-1 extent and true end door, correctly
timed auto-walk, successful Subround-2 load, and no regression to earlier streaming/collision/gameplay.
