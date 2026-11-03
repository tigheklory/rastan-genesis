# Build 0409 Displayed Enemy Sprite-Loss Fix

**Golden visual reference:** Build 0406  
**Rejected builds:** 0407, 0408  
**Corrected candidate:** Build 0409  
**Human acceptance:** required

## First displayed-pipeline divergence

The actual Genesis VDP SAT was read through the 68000 VDP data/control ports
after stopping the machine. MAME's `:gen_vdp` Lua `videoram` space is only the
inherited 16 KiB compatibility space (`mask=0x3FFF`), so it cannot directly
address the Mega Drive VDP's 64 KiB SAT location at VRAM `0xF800`. The terminal
reader was validated on a visible frame by matching decoded linked SAT entries
to Rastan and enemy screen coordinates.

At the first unambiguous Build-0408 failure, gameplay frame 1243 / captured
frame 817, actor `0xFF0488` is active at X/Y `216/121`, base `0x004B`, selector
`0x18`, state `0x00`, subframe `0x00`, orientation `1`. The generated table
reader visits all eight expected body records:

`0069, 0067, 004E, 004C, 0068, 0063, 004D, 004B`.

The body uses the `back_enemy` semantic lane. Thirteen records from earlier
actors already occupy that queue. Only `0069` and `0067` append, taking the
count from 13 to 15; the other six records fail the fast append's end-pointer
comparison. Consequently only two of eight body records reach the finalizer
and published SAT. The independently produced impact/effect uses the
`front_effect` lane, so it can remain visible while the body disappears.

This is the first divergence. It precedes the shared finalizer, SAT staging,
SAT publication, residency, pattern DMA, and VDP sprite evaluation.

## Root cause

Build 0407 introduced `native_sprite_fast_context`, which selects a queue once
per generated frame. It constructed `A2`, the exclusive queue end, using
numeric-displacement `LEA` expressions such as:

```asm
lea (NATIVE_BACK_ENEMY_BOUND * NATIVE_QUEUE_ENTRY_BYTES)(%a3), %a2
```

The toolchain encoded an indexed/full-extension effective address. The target
68000 does not implement the later-CPU full extension and interprets its first
extension word as a brief indexed address. At the failing frame the measured
registers were:

```text
A3 = 0x00FFBBB8  native_queue_back_enemy
D0 = 0x0005      selected lane
A2 = 0x00FFBC2D  observed exclusive end
A2 - A3 = 0x75   15 queue records, not 99
```

Thus this was a shared fast-context bounds defect, not a Lizardman frame-table
defect. Build 0408's A3/A6 preservation correction remains valid and retained.

## Correction

All six fast contexts now load exact linker labels placed immediately after
their queue allocations:

```asm
lea native_queue_back_enemy, %a3
lea native_back_enemy_count, %a6
lea native_queue_back_enemy_end, %a2
```

The resulting allocation spans are mechanically verified as 9, 36, 30, 24,
20, and 99 records for HUD, front effect, player front, middle, player body,
and back enemy respectively. The build verifier now requires both each end
label reference and exact adjacency of every end label to its `.space`
allocation. No actor-specific path, fallback, runtime arcade parser, or SAT
workaround was introduced.

The variable-count emitter, fast enqueue, once-per-frame context, A3/A6 save,
Python-precomputed tables, shared residency/worklist/finalizer, and 49/49
native-complete architecture are retained.

## Published-SAT and framebuffer proof

Evidence:

- failing 0408:
  `states/traces/build0409_actual_vdp_0408_fail_frame1243_state/`
- generated-record reads:
  `states/traces/build0409_actual_vdp_0408_fail_frame1243_table/`
- enqueue transition:
  `states/traces/build0409_actual_vdp_0408_fail_frame1243_enqueue/`
- complete 0406 reference:
  `states/traces/build0409_actual_vdp_0406_gold_frame0659/`
- corrected 0409 semantic frame:
  `states/traces/build0409_actual_vdp_fixed_semantic_frame0649/`
- corrected deterministic framebuffer route:
  `states/traces/build0409_displayed_enemy_fixed/`

In the corrected semantic frame, the back-enemy count is 17, beyond the old
hidden cutoff of 15. Both visible Lizardmen have all eight records in the
queue, and all sixteen body pieces appear in the published VDP SAT at indices
13--28. The actual framebuffer shows the Lizardman body together with the
impact effect.

The relevant hardware load is below the Genesis limits. The complete 0406
frame peaks at 14 sprites / 28 cells on one scanline; the failing 0408 frame
peaks at only 7 / 14 because the entries are already absent; corrected 0409
peaks at 10 / 20. Therefore neither per-line overflow nor SAT ordering caused
the loss. Because the missing entries never reached SAT, premature residency,
unpublished DMA, slot reuse, and worklist saturation are also non-causal.

The deterministic framebuffer route did not place a Four-Armed actor onscreen:
its `0x02E8` records remained parked at X/Y `0/384`. Tighe's real-gameplay
observation establishes the visual symptom, and the same defect applies
mechanically because Four-Armed uses the same generated fast append and
`back_enemy` context. Final Four-Armed visual acceptance therefore remains a
user test rather than being mislabeled as an automated visual pass.

## Performance

Same GENESIS NTSC MAME record-2 autorun and 1,200 rendered gameplay frames:

| Metric | 0406 | 0408 | 0409 |
|---|---:|---:|---:|
| workers/rendered frame | 0.6567 | 0.8308 | 0.8358 |
| worker average/update | 186,855.31 | 146,609.22 | 145,921.68 |
| IRQ average/update | 193,172.71 | 152,246.56 | 151,489.25 |
| graphics average/update | 122,333.29 | 80,392.38 | 76,211.10 |
| IRQ over 128,009 cycles | 99.5% | 82.7% | 72.2% |
| rendered frames without worker | 412 | 203 | 197 |

Relative to 0406, Build 0409 provides 27.27% more workers per rendered frame,
21.91% fewer worker cycles, 21.58% fewer IRQ cycles, 37.70% fewer measured
graphics cycles, and 52.18% fewer frames without a worker. Relative to 0408,
the corresponding changes are +0.60%, -0.47%, -0.50%, -5.20%, and -2.96%.
The large native performance gain is retained. VDP ownership passes.

## Gates and artifacts

The canonical gate and gameplay-entry gate pass. Gameplay-entry exceptions
are address/bus/illegal/crash-handler `0/0/0/0`. The pre-existing seven-epoch
warning remains unchanged.

All five ROMs are 1,998,520 bytes.

| Variant | SHA-256 |
|---|---|
| canonical | `6e1fc8c5949722f95b68c5c94c09df04d7bf5218853614de55a1475d830b7b6c` |
| `_c` | `d8ba2321b91c0bfd1057b91282e4d5509e438edee6c10eadc18860f319c045fc` |
| `_d` | `13219b23562b62dbeaf2c280b92920bb3b6c48eb4ef0c6cfd6cec7ff06d07601` |
| `_do` | `d18c7731dbf3a3ee9c48cb340944560fd6087e77bb00ee21c986dcda93cb41a4` |
| `_s` | `c0f17bc72b60bba4375d1ae71042c6754b40e7a4f2e5e9bb65dcb11d491442d2` |

Tighe visual/gameplay/performance acceptance is required.
