# R1-S2 jump-assisted versus normal rope trace preparation

Date: 2026-11-02  
Agent: Cody  
Assignment: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0057`  
Baseline: Build 0528; diagnostic family: Build 0529

## Delivered result

One playable invincible R1-S2 ROM and a two-mode external trace are ready. Both modes launch the
same SHA-identified ROM from a fresh Genesis NTSC MAME process and never automate controller input.
No renderer change was made.

Diagnostic ROM:
`dist/rastan-direct/rastan_direct_video_test_build_0529_invincible_S1-2.bin`, 3,792,568 bytes,
SHA-256 `f47d3ed5c91e5e7a424de8f71e7f5622fbd8a71fbbf4a98e693992bbd8421e4a`.

Run these exact commands from the repository root:

```bash
tools/diagnostics/run_r1s2_rope_trace.sh jump
tools/diagnostics/run_r1s2_rope_trace.sh normal
```

For JUMP, use jump-assisted climbing on the chains wherever practical. For NORMAL, hold Up and
avoid jump assistance. Complete the subround, then close MAME normally. Press `M` whenever visible
corruption appears; each press edge records the current semantic location. `F12` remains MAME's
screenshot key.

The launchers refuse to overwrite an existing mode directory. Outputs are:

- `states/traces/r1s2_rope_build_0529/jump/{frames.tsv,events.tsv,markers.tsv,metadata.txt}`
- `states/traces/r1s2_rope_build_0529/normal/{frames.tsv,events.tsv,markers.tsv,metadata.txt}`

After both complete runs:

```bash
tools/diagnostics/compare_r1s2_rope_traces.py
```

This writes `states/traces/r1s2_rope_build_0529/comparison.md`.

## Trace contract

The launcher resolves native addresses from the current `apps/rastan-direct/out/symbol.txt`; it
does not embed stale Build-specific symbol addresses. The exact Build 0529 resolutions are:

| State/event | Address or PC | Classification |
|---|---:|---|
| input latch | `A5+$0016` | runtime value |
| invincibility gate | `A5+$0040` | runtime value; bit `$0040` expected |
| record | `A5+$013E` | runtime value |
| selector / completed selector | `A5+$10A8` / `A5+$132C` | runtime values |
| FG X/Y | `A5+$10AE/$10B0` | runtime values |
| player X/Y | `A5+$10BE/$10C0` | runtime values |
| vertical/horizontal accumulators | `A5+$1262/$1264/$1266/$1268` | runtime values |
| movement step / camera delta / flags | `A5+$10DE/$10DA/$10D0` | runtime values |
| strip/group | `A5+$10CA/$10CC` | runtime values |
| player action / facing | `A5+$10E8/$1114` | state 4 rope-attached; facing 2 visually left |
| staged FG scroll X/Y | `$FF40A0/$FF40A4` | runtime values |
| source reference | `$FF6286` | runtime pointer |
| row/column dirty | `$FF4006/$FF61F4` | runtime masks |
| narrow descriptor count | `$FF4092` | runtime count |
| staged Plane A | `$FF50A6..$FF60A5` | aggregated write tap |
| VBlank counters | `$FF61EC..$FF61F2` | runtime values/write sequence |
| selector-0/selector-1/2 entry | `$0704C0/$0706FA` | exact debugger execution event |
| no-publication up/down entry | `$070AAC/$070B04` | exact debugger execution event |
| Plane A row/scroll commit | `$07014E/$070192` | exact ordered execution events |

Each `frames.tsv` row contains the raw state, actual FG-Y delta, exact path-event order, dirty state,
VBlank counters/workload deltas, and aggregated staged-row writes. Staged writes retain physical row,
column span, write count, order-sensitive hash, and every observed writer PC. This exposes a later
same-row overwrite without logging every word as a separate disk event. `events.tsv` records only
path entries and per-row staging summaries.

The following are explicitly derived, not fabricated runtime fields:

- scroll direction from consecutive `A5+$10B0` values;
- entering logical and physical rows from consecutive native-visible tops;
- predecessor/current selection label from the Build 0528 `(selector, completed, record)` branch
  contract.

The metadata labels these fields as inferred. The exact ordinary/no-publication route and row/scroll
commit order come from execution events, not that inference. Host tracing does not write ROM, WRAM,
input, VDP state, or emulator input fields.

## Comparison method

The comparator excludes title/READY repetition and aligns R1-S2 samples by this semantic key:

`FG Y / logical entering row / record / selector / completed selector / strip / group`.

Repeated occurrences of the same key are paired in chronological occurrence order rather than
reusing one frame. It then compares selected predecessor/current mode, physical row, staged-row
hash/writers, dirty writes, VBlank sequence/workload, and ordered publication events. Raw frame
numbers are provenance only.

The report highlights the earliest differing matched semantic state. That difference is evidence
for review, not automatic proof of arcade incorrectness. An unmatched state likewise is not called
a fault without checking progression and the user's `M` markers.

## Invincibility and derivative proof

The implementation reuses the already verified `_invincible` family member. Original arcade
startup computes `A5+$0040=$0040` from the patched `$FFBF` source configuration. Static release
verification proved the paired startup bit, all 66 damage dispatches, and zero unrelated parent ROM
differences. The R1-S2 derivative differs from the parent only at ROM `$0508A3` (`$25->$27` music)
and `$05FF9F` (`$FF->$DF` stage selector).

This preserves ordinary movement, rope/wall collision, camera and scroll logic. It suppresses the
damage reaction, including hit-stun and knockback, when an ordinary damaging contact would have
occurred. Falling into water remains lethal, exactly as warned by the stock arcade cheat.

## Verification completed before handoff

- Build 0529 release and complete family: PASS.
- Exact derivative byte-scope verifier: PASS.
- Established functional direct-start probe: PASS; live R1-S2 stage `$0010`, record `$0011`, both
  planes populated, map misses 0.
- JUMP and NORMAL launcher modes: both started the exact diagnostic ROM and created valid trace
  files in isolated `/tmp` smoke directories.
- Comparator: ran successfully on those smoke outputs.

The functional probe used the repository's established coin/start automation only to prove stage
initialization. The delivered gameplay launcher performs no automation.

## What cannot yet be concluded

No complete human JUMP or NORMAL trace exists at handoff, so there is no supported earliest runtime
divergence and no specific Plane A repair recommendation yet. The smoke captures remained in startup
and are not diagnosis evidence. Build 0528's residual corruption is not fixed.

After Tighe completes both playthroughs, inspect the generated comparison around each `M` marker. A
specific correction should be proposed only if runtime evidence identifies an incorrect selection,
same-row overwrite, missed/reordered publication, or VBlank-supported failure.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0057`

