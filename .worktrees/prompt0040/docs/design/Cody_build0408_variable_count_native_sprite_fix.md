# Build 0408 Variable-Count Native Sprite Fix

**Golden reference:** Build 0406  
**Rejected regression:** Build 0407  
**Corrected candidate:** Build 0408  
**Human acceptance:** required

## Result

Tighe confirmed that Build 0406 renders the affected enemies correctly and
Build 0407 is faster but loses whole composite pieces on Lizardman and the
Four-Armed enemy. The first Build-0406/0407 divergence is not generated data,
source iteration, queue compaction, residency, or SAT construction. It is the
retained caller's address-register contract at the return from both generic
generated-frame wrappers.

Build 0407 moved lane selection to `native_sprite_fast_context`, which uses
`A3` as queue base and `A6` as count pointer. The player wrappers already saved
those registers. `.Lnative_generic_frame_try` and
`.Lnative_universal_general_try` still saved only `A0-A2`, because the former
Build-0406 `native_sprite_emit` preserved its own scratch registers on every
piece. Thus successful enemy frames returned with caller-owned `A3/A6`
replaced by native queue addresses.

Exact Lizardman A/B evidence at actor `0xFF04C8`:

| Build | boundary | A3 | A6 |
|---|---|---:|---:|
| 0406 | Level-B entry | `0xFF12A8` | `0xFF0298` |
| 0406 | Level-B success return | `0xFF12A8` | `0xFF0298` |
| 0407 | Level-B entry | `0xFF12A8` | `0xFF0298` |
| 0407 | Level-B success return | `0xFFBBB8` | `0xFFB7FE` |

The latter values are exactly `native_queue_back_enemy` and
`native_back_enemy_count`. The universal wrapper shows the same clobber at the
Four-Armed actor slot (`0xFF04C8`, frame 2096/2097). Build 0408 observed 4,017
matched generic entry/return pairs with zero `A3/A6` mismatches.

## Generated data and A-H reconciliation

Independent arcade-program re-expansion remains byte-exact for both
orientations:

- Lizardman: base `0x004B`, selector `0x17`, compositor `0`, 8 potential
  records. Representative identities are `66,64,4E,4C,65,63,4D,4B`.
- Four-Armed: base `0x02E8`, selector `0x61`, compositor `0`, 9 potential
  records. Representative identities are
  `2F6,2F4,2F5,2EC,2E9,2EB,2E8,2ED,2EA`.

Representative Build-0408 reconciliation:

| Actor/state | A potential | B considered | C prequeue reject | D accepted | E count increment | F records | G finalizer consumed | H SAT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Lizardman `004B/17/ori0`, fully visible | 8 | 8 | 0 | 8 | 8 | 8 | 8 | 8 |
| Four-Armed `02E8/61/ori0`, right-clipped | 9 | 9 | 0 | 9 | 9 | 9 | 9 | 6 |
| Four-Armed `02E8/61/ori0`, fully visible | 9 | 9 | 0 | 9 | 9 | 9 | 9 | 9 |

The three right-clipped Four-Armed records at X `0x146` are legitimate common
finalizer geometry rejections. Later sibling records are still considered and
emitted. Across 11 sampled positions its source count remains 9 while SAT
output changes from 6 to 9 solely with visibility.

The first Lizardman frame in the deterministic route already has all eight
queue records and all eight SAT records in both 0406 and 0407. A transient
12-install worklist saturation at a later frame is also identical in both
builds, so it is not the regression. The first exclusive 0407 divergence is
the wrapper-return register state above; corruption begins after the complete
current actor has been finalized and affects subsequent retained traversal and
producer work.

## Correction and gates

Both generic wrappers now save and restore `A3/A6` once at the frame boundary,
on success and unresolved exits. The single variable-count emitter,
once-per-frame lane context, and fast enqueue are retained unchanged. No
count-specific actor handler was added.

The build-integrated direct-dispatch verifier now requires this register
contract and mechanically reconciles six variable-count cases: no rejection,
first/middle/last rejection, multiple consecutive/partial-visibility
rejection, and near-capacity output. Generated-table verification passes for
1,200 player frames, 416 secondary frames, 38 direct generic records, 1,898
universal general records, and 24 specialized records.

The Build-0408 rack-advance closeout completed all 18 established subrounds
with player fallback `0`, generic fallback `0`, player adapter `0`, crash flag
`0`. Gameplay-entry exceptions are address/bus/illegal/crash-handler
`0/0/0/0`. This mechanically covers the campaign's Lizardman, Four-Armed,
Large Bat, Small Bat, Flying Demon, Chimera, Valkyrie, specialized actor,
Rastan BODY/FRONT/secondary, and fire-sword generated routes. Tighe must still
perform visual/gameplay acceptance.

## Performance

Same GENESIS NTSC MAME record-2 autorun, 1,200 rendered gameplay frames:

| Metric | 0406 | 0407 | 0408 |
|---|---:|---:|---:|
| workers/rendered frame | 0.6567 | 0.8342 | 0.8308 |
| worker average/update | 186,855.31 | 145,865.23 | 146,609.22 |
| IRQ average/update | 193,172.71 | 151,515.14 | 152,246.56 |
| graphics average/update | 122,333.29 | 85,793.42 | 80,392.38 |
| IRQ over 128,009 cycles | 99.5% | 79.1% | 82.7% |
| rendered frames without worker | 412 | 199 | 203 |

Relative to 0406, 0408 retains +26.52% workers/rendered frame, -21.54% worker
cycles, -21.19% IRQ cycles, -34.28% measured graphics cycles, and 50.73% fewer
frames without a worker. Relative to 0407, the frame-boundary register save is
only +0.51% worker and +0.48% IRQ average; the major Build-0407 performance
gain is substantially retained. VDP ownership passes.

## Artifacts and evidence

All Build-0408 ROMs are 1,998,520 bytes.

| Variant | SHA-256 |
|---|---|
| canonical | `f6f563b100e8101283b40748c6e1261694c71888ab52406355b1277352f305a5` |
| `_c` | `9b84da979c46f376a7e4e559116d1cdf9257ac7bf402ae49f723b45456689403` |
| `_d` | `451cc228df0e3e4dc3efae8ac6c8ed9c304235a36c02738039439ab811572ba9` |
| `_do` | `1adb5090137c81e05fba4cc1a1fc855a403261e8c4842719e31950a8d3642a13` |
| `_s` | `3f0d59dc38e99b673addf11b8567e9ab2d4b2329943dce47cc8210baf82764ff` |

Evidence is under `states/traces/build0408_variable_count_*`, with the normal
gate at `states/traces/build0408_gameplay_entry_gate_20261009_130747/`.

