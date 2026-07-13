# Cody - PC090OJ Gameplay Representation Activation Trace

**Date:** 2026-07-12
**Type:** Runtime evidence / analysis only
**Build under test:** Build 0162, `dist/rastan-direct/rastan_direct_video_test_build_0162.bin`
**Scope:** PC090OJ mirror/candidate/representation/SAT activation only. No source/spec/tool/Makefile/ROM/invariant changes. No build. No VINT/vector/SR/VDP register ownership changes. No collision, palette, PC080SN/FG_SRC, player-state, camera/scroll, D00298, Exodus/audio, or hardcoded sprite/SAT work.

## Baseline

The Build 0162 VINT timing classification is settled input: steady gameplay frames `637..1498` have no missing `_vblank_service` frames, no entry-without-RTE frames, no VDP register-1 VINT clobber, and a longest steady service chain of `9666` cycles. Therefore this task does not target VINT ownership or frequency.

Relevant prior sprite-path context:

- Andy's earlier gameplay SAT-link/ownership notes reported populated gameplay `pc090oj_object_ram`, stale/reachable title-like SAT entries, and a candidate/representation boundary as the next suspect.
- Current source is newer than the older 0x071Axx/0x071Bxx address notes: Build 0162 `vdp_prepare_sprites` already consumes `pc090oj_mirror_dirty` by marking all candidates when dirty/bootstrap is pending.
- The purpose of this task is to prove whether current Build 0162 still fails at candidate activation, decode/filter, representation, free-slot/count, or whether the real failure is later.

## Phase 0

Relevant priors from `KNOWN_FINDINGS.md`: KF-010 (staging/VDP commit model), KF-032 (PC080SN-style writes route through staging), KF-036/KF-039 (mapped work-RAM lessons), and current PC090OJ/OPEN-024 history as issue context. Relevant issue context: OPEN-024 (PC090OJ sprites incomplete/garbage), OPEN-017 (gameplay bring-up), and OPEN-001 (graphics output incomplete).

Rediscovery Hazard HIGH touched: VBlank ownership and PC090OJ staging/representation. No contradiction with a CONFIRMED/STRONG finding was detected. The task classification is **EXTENDING**. No closed issue was reopened. Architecture compliance is confirmed: arcade code remains the program; Genesis-side code is helper/service only; rendering still flows through staging -> VBlank commit -> VDP.

## Files And Evidence Inspected

Source/static:

- `RULES.md`
- `ARCHITECTURE.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- `AGENTS_LOG.md`
- `docs/design/Cody_build0162_vint_timing_trace_classification.md`
- `docs/design/Andy_gameplay_sat_link_management.md`
- `docs/design/Andy_gameplay_sprite_path_ownership.md`
- `docs/design/Andy_gameplay_palette_lines_0_1_population.md`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/rastan-direct/address_map.json`

Runtime evidence:

- Trace directory: `states/traces/pc090oj_gameplay_representation_activation_20260712_204408/`
- Native debugger trace: `build0162_pc090oj_representation_debug.log` (`35,809` lines, `17,881` EVENT lines)
- Snapshot files: `frame_0100_*`, `frame_0637_*`, `frame_0891_*`, `frame_1498_*`
- Reduced analysis: `pc090oj_representation_analysis.md`
- Per-record proof table: `gameplay_drawable_records_frame_0637.csv`

## Current Source Anchors

Symbols from `apps/rastan-direct/out/symbol.txt`:

| Symbol | Address |
|---|---:|
| `vdp_prepare_sprites` | `runtime_genesis_pc 0x0007219C` |
| `staged_sprite_sat` | `Genesis-WRAM 0x00FF6188` |
| `staged_sprite_active_count` | `Genesis-WRAM 0x00FF67CC` |
| `pc090oj_object_ram` | `Genesis-WRAM 0x00FF69B0` |
| `pc090oj_candidate_bitset` | `Genesis-WRAM 0x00FF71B0` |
| `pc090oj_mirror_dirty` | `Genesis-WRAM 0x00FF71D4` |
| `pc090oj_scan_active` | `Genesis-WRAM 0x00FF71EA` |
| `record_to_slot` | `Genesis-WRAM 0x00FF71F0` |
| `represented_records` | `Genesis-WRAM 0x00FF72F0` |
| `pc090oj_represented_count` | `Genesis-WRAM 0x00FF7390` |
| `pc090oj_bootstrap_pending` | `Genesis-WRAM 0x00FF7394` |

Current source behavior:

- `_vblank_service` calls `vdp_prepare_sprites` before display-off and VDP commits (`vdp_comm.s:164..191`).
- `vdp_prepare_sprites` initializes only if `pc090oj_scan_active == 0`; if `pc090oj_bootstrap_pending | pc090oj_mirror_dirty` is nonzero, it clears both and calls `.Lpc090oj_set_all_candidates`; then it calls `.Lpc090oj_process_candidates` and copies `pc090oj_represented_count` to `staged_sprite_active_count` (`pc090oj_hooks.s:958..987`).
- `.Lpc090oj_process_candidates` consumes `pc090oj_candidate_bitset`, calls `.Lpc090oj_sync_record_from_mirror` for set bits, then clears each consumed bit (`pc090oj_hooks.s:1079..1118`).
- `.Lpc090oj_sync_record_from_mirror` decodes a record and either activates, updates, deactivates, or rejects it (`pc090oj_hooks.s:1558..1598`).
- `.Lpc090oj_place_record_in_slot` writes the staged SAT slot, descriptor, record-to-slot mapping, represented bit, used-slot bit, queues/cancels tile DMA work, and sets `pc090oj_sat_dirty` (`pc090oj_hooks.s:1442..1544`).

## Runtime Method

A read-only MAME debugger trace was run against Build 0162 with breakpoints around prepare/process/sync/activate/place paths, then a Lua snapshot pass captured title and gameplay frame state.

Representative snapshot frames:

- Title known-good: frame `100`
- Stable gameplay/flickering-dot window: frames `637`, `891`, `1498`

Trace exit status: `0`. No build was produced.

## Snapshot Summary

| Frame | State | Dirty | Represented count | Staged active | Coded records | Drawable by current decode | Represented bits | Reachable records |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| `100` | `0000/0001/0000` | `0000` | `000F` | `000F` | `42` | `15` | `15` | `4,5,6,7,8,22,23,24,25,34,35,36,43,44,45` |
| `637` | `0002/0002/0006` | `0000` | `000E` | `000E` | `28` | `14` | `14` | `22,23,24,25,34,35,36,43,44,45,64,65,66,67` |
| `891` | `0002/0002/0006` | `0000` | `000E` | `000E` | `28` | `14` | `14` | `22,23,24,25,34,35,36,43,44,45,64,65,66,67` |
| `1498` | `0002/0002/0006` | `0000` | `000E` | `000E` | `28` | `14` | `14` | `22,23,24,25,34,35,36,43,44,45,64,65,66,67` |

Important correction to prior premise: this Build 0162 trace does **not** reproduce 24 drawable gameplay records under the current decoder/filter. It reproduces `28` coded records, of which `14` are accepted/drawable and `14` are rejected as `offscreen_y`.

## Event Counts

From `pc090oj_representation_analysis.md`:

| Event | Count |
|---|---:|
| `PREP_ENTRY` | `1404` |
| `PREP_BEFORE_PROCESS` | `1404` |
| `PREP_EXIT` | `1404` |
| `PROC_ENTRY` | `1404` |
| `PROC_CAND` | `2048` |
| `PROC_EXIT` | `1404` |
| `SYNC_ENTRY` | `2136` |
| `SYNC_DECODE` | `2136` |
| `SYNC_ACCEPT_NEW` | `20` |
| `SYNC_WAS_REP` | `91` |
| `SYNC_UPDATE_REP` | `85` |
| `SYNC_REJECT_NOTDRAW` | `2025` |
| `SYNC_DEACTIVATE` | `6` |
| `ACT_ENTRY` | `20` |
| `ACT_FIRST` | `1` |
| `ACT_NEW_HEAD` | `1` |
| `ACT_ORDINARY` | `18` |
| `PLACE_DONE` | `112` |
| `SET_ALL_ENTRY` | `13` |
| `SET_ALL_EXIT` | `13` |

No `ACT_TO_WAITING` event was observed, so the free-slot/count/waiting path is not implicated by this trace.

## Per-Record Proof At Gameplay Frame 637

Every record accepted by the current decoder is represented and reachable. Candidate bits are zero at stable frame 637 because processing completed earlier; each accepted record was synchronized eight times and accepted once.

| rec | code | raw x/y | decoded x/y | candidate@637 | sync calls | accepted | was represented | represented@637 | SAT slot | verdict |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| `22` | `002B` | `00A8/0010` | `168/16` | `0` | `8` | `1` | `7` | `1` | `00` | accepted + reachable |
| `23` | `002D` | `00A0/0010` | `160/16` | `0` | `8` | `1` | `7` | `1` | `06` | accepted + reachable |
| `24` | `0031` | `0098/0010` | `152/16` | `0` | `8` | `1` | `7` | `1` | `07` | accepted + reachable |
| `25` | `002C` | `0090/0010` | `144/16` | `0` | `8` | `1` | `7` | `1` | `08` | accepted + reachable |
| `34` | `0039` | `0040/0010` | `64/16` | `0` | `8` | `1` | `7` | `1` | `09` | accepted + reachable |
| `35` | `0048` | `0028/0000` | `40/0` | `0` | `8` | `1` | `7` | `1` | `0A` | accepted + reachable |
| `36` | `0046` | `0038/0000` | `56/0` | `0` | `8` | `1` | `7` | `1` | `0B` | accepted + reachable |
| `43` | `0039` | `0120/0010` | `288/16` | `0` | `8` | `1` | `7` | `1` | `0C` | accepted + reachable |
| `44` | `0049` | `0108/0000` | `264/0` | `0` | `8` | `1` | `7` | `1` | `0D` | accepted + reachable |
| `45` | `0047` | `0118/0000` | `280/0` | `0` | `8` | `1` | `7` | `1` | `0E` | accepted + reachable |
| `64` | `0513` | `0038/0050` | `56/80` | `0` | `8` | `1` | `0` | `1` | `01` | accepted + reachable |
| `65` | `0512` | `0028/0050` | `40/80` | `0` | `8` | `1` | `0` | `1` | `02` | accepted + reachable |
| `66` | `0511` | `0020/0040` | `32/64` | `0` | `8` | `1` | `0` | `1` | `03` | accepted + reachable |
| `67` | `0516` | `0018/0070` | `24/112` | `0` | `8` | `1` | `0` | `1` | `04` | accepted + reachable |

The stable reachable SAT chain for gameplay frames `637`, `891`, and `1498` is:

```text
slot chain:   0 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12 -> 13 -> 14 -> 1 -> 2 -> 3 -> 4 -> 0
record chain: 22, 23, 24, 25, 34, 35, 36, 43, 44, 45, 64, 65, 66, 67
```

## Coded But Rejected Records

At frame 637, the other coded records are all `code=0x002A` and are rejected by the current decode/filter as `offscreen_y`:

| recs | code | reason |
|---|---:|---|
| `26,27` | `002A` | raw Y `0x0110`, decoded Y `272`, opaque Y span `264..270`, outside viewport |
| `28..33` | `002A` | raw Y `0x0000`, opaque Y span `-8..-2`, outside viewport |
| `37..42` | `002A` | raw Y `0x0000`, opaque Y span `-8..-2`, outside viewport |

This is the first place where the current runtime differs from the older “24 drawable” premise: the candidate/representation path does not skip these records; the decoder rejects them as non-drawable.

## Candidate Bits And Dirty Handling

Stable gameplay snapshots show `pc090oj_candidate_bitset == 0` and `pc090oj_mirror_dirty == 0`. That is expected after processing, not proof of an unprocessed dirty frame:

- `SET_ALL_ENTRY/EXIT` occurred `13` times across the run.
- `PROC_CAND` occurred `2048` times.
- Accepted gameplay records each show `sync_called_total=8`.
- Stable frames have no pending candidate bits because the represented set has converged.

Current Build 0162 source already implements the dirty resweep in `vdp_prepare_sprites`; therefore the old “mirror_dirty is written but ignored” boundary is not current.

## SAT Tile Field Note

Gameplay SAT attrs include slot-keyed tile indices in the `0x400+` range. That alone does **not** prove stale title tile content, because current `.Lpc090oj_place_record_in_slot` deliberately encodes `SPRITE_TILE_BASE + slot*4` (`pc090oj_hooks.s:1497..1501`). The representation trace proves record/slot activation; whether the corresponding slot tile graphics are correct belongs to the later tile-DMA/VRAM/SAT-commit/visual path, not candidate activation.

## Classification

Primary classification: **F - wrong boundary**.

The current Build 0162 representation boundary is functioning for every record the current decoder accepts:

- `vdp_prepare_sprites` runs during gameplay VBlank.
- Dirty/bootstrap resweep is present in source and observed by `SET_ALL` events.
- Candidate processing calls sync and clears bits.
- Accepted gameplay records are represented.
- The reachable SAT chain includes exactly the accepted gameplay records at the stable sampled frames.
- Free-slot/count/waiting overflow is not observed.

Therefore no Build 0163 candidate-bit, dirty-bit, free-slot, or stale-title-activation patch is justified by this evidence.

## Working Hypothesis

The remaining sprite-visible failure is downstream of representation activation or in the decode/filter premise itself:

- Downstream possibility: tile DMA residency/worklist, VRAM sprite tile contents, SAT commit timing, or visual composition is wrong even though the represented record chain is correct.
- Decode/filter possibility: records previously counted as drawable are currently rejected as `offscreen_y`; proving that as a bug requires an arcade-vs-Genesis decode/viewport comparison for those specific `0x002A` records, not a candidate-bit fix.

## Recommended Smallest Next Boundary

Do not implement candidate-bit or `.Lpc090oj_set_all_candidates` changes from this trace.

Smallest next diagnostic boundary:

1. Pick one accepted gameplay record with a visible expected sprite, preferably record `64` (`code 0x0513`, slot `01`) or record `65` (`code 0x0512`, slot `02`).
2. Trace `record -> staged SAT slot -> tile DMA worklist -> sprite tile resident code -> VRAM tile data -> SAT DMA` for the same stable gameplay frame.
3. Separately, if the team still needs the “24 drawable” claim, compare the rejected `0x002A` records against original arcade viewport/opaque-span behavior before changing the Genesis filter.

## Build Decision

No build was produced. A/B/C/D were not proven, so a bounded implementation is not authorized by this task.

## Open / Closed Issues Impact

Open issues touched: OPEN-024, OPEN-017, OPEN-001. New issues opened: NONE. Issues closed: NONE. Intentionally deferred: VINT/vector/SR/VDP register ownership, collision, palettes, PC080SN/FG_SRC, player state, camera/scroll, D00298, Exodus/audio, hardcoded sprites/SAT, second renderer.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. This trace narrows the active PC090OJ boundary, but the durable visual-failure mechanism remains to be proven in a downstream tile-DMA/VRAM/SAT-commit or decode/filter comparison task.

## STOP

STOP triggered: NO. Evidence was captured and classified. No source change or build was authorized.
