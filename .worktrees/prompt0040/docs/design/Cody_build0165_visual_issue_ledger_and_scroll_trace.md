# Cody - Build 0165 Visual Issue Ledger + Vertical Scroll Direction Trace

**Date:** 2026-07-13
**Type:** Issue-ledger update + focused runtime/static trace + bounded implementation
**Build 0165 ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0165.bin`
**Build 0165 SHA256:** `dd2e4d63ece2b7862b58da33b9c662114a27659844f5ef4154b2cf3a55986c4c`
**Build 0166 ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0166.bin`
**Build 0166 SHA256:** `a74365146eef4fdf0e9b429d7e66d63186023e3541f36fc1fa9b2703eed62ff5`
**Scope:** Document Build 0165 visual/runtime issues, then work only the vertical-scroll direction issue. No collision, input, D00298, player-source, LUT, scene-loader, VDP sprite DMA, continue/game-over, or broad VBlank work.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-010 (BG/FG plane mapping), KF-011 (arcade VBlank owns progression), KF-015 (full-plane scroll model), KF-024/OPEN-017 gameplay rendering state, KF-043/KF-044 WRAM source-population context, OPEN-024 PC090OJ sprite subsystem. Rediscovery-hazard findings touched: KF-015 and KF-044; no contradiction detected.

Open issues touched: OPEN-017 and OPEN-024. Closed issues touched: none. OPEN-015 was not touched.

Architecture compliance: **CONFIRMED**. The fix, where applied, is inside the existing Genesis VBlank scroll-commit helper. Arcade code still owns gameplay progression; Genesis code remains hardware service/staging/commit only.

## Build 0165 Milestone

Build 0165 is recorded as a major player-visibility milestone, not an accepted-build change unless Tighe explicitly accepts it:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0165.bin`
- SHA256: `dd2e4d63ece2b7862b58da33b9c662114a27659844f5ef4154b2cf3a55986c4c`
- Counter: `165`
- `0x00FF11B2` populated.
- Player records `120/121/124/125/126/128/129/130/131` receive player-cluster codes, become represented, and reach staged SAT.
- Tighe visually confirmed Rastan appears on screen.
- Build 0163 forced-refresh remains included.

## Visual Issue Ledger

Recorded in `OPEN_ISSUES.md` under OPEN-017, with OPEN-024 cross-reference for sprite-specific follow-up:

1. Vertical scroll direction appeared reversed during Round 1 fall.
2. Rastan burns/dies as if on lava/fire, repeating for all lives. Deferred collision/death/surface-state issue.
3. Player seems uncontrollable; down+attack downward thrust not available. Deferred input/player-state/timing issue.
4. Apparent VBlank overrun / rolling black bar when Rastan is visible. Deferred VBlank budget/display-off timing issue.
5. Game appears slow, especially while Rastan burns. Deferred runtime/timing/load issue.
6. ROUND 1 / READY sprite flicker, brief blank, missing header sprites. Deferred sprite/header lifecycle issue.
7. Continue/game-over screens have wrong tiles loaded after the three deaths. Deferred scene/tile lifecycle issue.
8. D00298 attract-demo issue remains a demo-control-flow issue; not addressed here.
9. Suspicious PC090OJ records `132..134` remain sprite-source/content follow-up.

## Evidence Artifacts

- Build 0165 arcade trace: `states/traces/build0165_scroll_direction_20260713_223304/arcade/arcade_scroll_trace.csv`
- Build 0165 Genesis trace: `states/traces/build0165_scroll_direction_20260713_223304/genesis/genesis_scroll_trace.csv`
- Build 0165 trace scripts/events: `states/traces/build0165_scroll_direction_20260713_223304/`
- Build 0166 Genesis validation trace: `states/traces/build0166_scroll_direction_validation_20260713_223550/genesis/genesis_scroll_trace.csv`
- Build 0166 trace scripts/events: `states/traces/build0166_scroll_direction_validation_20260713_223550/`
- Static code inspected: `apps/rastan-direct/src/vdp_comm.s`, `apps/rastan-direct/src/tilemap_hooks.s`, `build/genesis_postpatch.disasm.txt`, `apps/rastan-direct/out/symbol.txt`.

MAME commands used `-video none`, auto coin/start, and exited normally. The Lua VDP-port write tap did not observe VDP writes through the Genesis driver program-space tap, so committed VSRAM values are reported as **inferred from static disassembly plus staged values**, not direct VDP memory readback.

## Scroll Trace Results

### Arcade Runtime

Original arcade active gameplay begins at external frame `307` in the trace. BG/FG Y source values (`a5+0x10EE` / `a5+0x10B0`) are equal and trend downward after the player lands:

| active-relative frame | player Y | FG Y source | BG Y source | mode | vcorr |
|---:|---:|---:|---:|---:|---:|
| `0` | `0x0030` | `0x0000` | `0x0000` | `0x0003` | `0x0000` |
| `30` | `0x006E` | `0x0000` | `0x0000` | `0x0003` | `0x0000` |
| `40` | `0x0070` | `0x01E4` | `0x01E4` | `0x0003` | `0x0003` |
| `60` | `0x0070` | `0x01A8` | `0x01A8` | `0x0003` | `0x0003` |
| `90` | `0x0070` | `0x014E` | `0x014E` | `0x0003` | `0x0003` |
| `93` | `0x0070` | `0x0149` | `0x0149` | `0x0000` | `0x0002` |

The earlier Build 0159 summary that arcade scroll stayed zero was superseded by this more targeted Build 0165 comparison window; the original arcade runtime does animate the raw scroll source during this active gameplay/fall/landing sequence.

### Build 0165 Runtime

Build 0165 active gameplay begins at external frame `534`. Genesis source values (`0xFF10EE` / `0xFF10B0`) match the same raw PC080SN direction as arcade, but later due to different frontend/timing path. Genesis staging (`0xFF409A` / `0xFF409C`) receives the raw values with a small frame delay:

| active-relative frame | player Y | FG/BG Y source | staged FG/BG Y | inferred VSRAM FG/BG before fix | mode | vcorr |
|---:|---:|---:|---:|---:|---:|---:|
| `0` | `0x0030` | `0x0000` | `0x0000` | `0x0008` | `0x0003` | `0x0000` |
| `60` | `0x0070` | `0x01FC` | `0x0000` | `0x0008` | `0x0003` | `0x0004` |
| `70` | `0x0070` | `0x01F0` | `0x01F4` | `0x01FC` | `0x0003` | `0x0004` |
| `160` | `0x0070` | `0x018B` | `0x018F` | `0x0197` | `0x0003` | `0x0004` |
| `220` | `0x0070` | `0x0147` | `0x0147` | `0x014F` | `0x0003` | `0x0004` |
| `231` | `0x0070` | `0x0141` | `0x0141` | `0x0149` | `0x0008` | `0x0002` |

Interpretation: Genesis source/staged values are **arcade-equivalent raw PC080SN Y values**, not already Genesis VSRAM values. The divergence is at publication: `vdp_commit_scroll` committed `raw + 8`, but documented PC080SN-to-Genesis conversion is `-raw + 8`.

### Static Commit Proof

Before the fix, `apps/rastan-direct/src/vdp_comm.s` committed vertical scroll as:

```asm
move.w  staged_scroll_y_fg, %d0
addq.w  #VDP_DISPLAY_ORIGIN_Y_BIAS, %d0
move.w  %d0, VDP_DATA
move.w  staged_scroll_y_bg, %d0
addq.w  #VDP_DISPLAY_ORIGIN_Y_BIAS, %d0
move.w  %d0, VDP_DATA
```

That preserved the raw arcade sign. `docs/design/build317_scroll_wram_staging_and_single_commit.md` records the intended vertical conversion as `-(int16_t)raw + 8`.

## Classification

**Vertical scroll classification:** bounded VDP-scroll conversion sign defect.

Answers to the prompt questions:

1. Arcade BG/FG vertical scroll values during the fall are raw PC080SN values that transition from `0x0000` to approximately `0x01E4 -> 0x0149` in the sampled active window.
2. Genesis Build 0165 source/staged values follow the same raw direction (`0x01FC -> 0x0141` sampled), with a frame-delay between source and staging.
3. Genesis staged values are **not inverted before VDP commit**; they are raw PC080SN values.
4. The commit convention was inverted/missing: Genesis VSRAM was receiving `raw + 8` instead of `-raw + 8`.
5. BG and FG invert together: both source fields and both staged fields are equal in the sampled window.
6. The wrong scroll is adjacent to, but does not explain away, the fire/death trigger. Build 0166 still reaches mode `0x0008` in the scripted trace.
7. The issue is a vertical-scroll sign-convention bug at commit, not a wrong source field, wrong bias, or player-source divergence.

## Fix Applied

Build 0166 adds `neg.w %d0` before the existing `+8` vertical display-origin bias for both FG and BG VSRAM words in `vdp_commit_scroll`.

Changed source:

```asm
move.w  staged_scroll_y_fg, %d0
neg.w   %d0
addq.w  #VDP_DISPLAY_ORIGIN_Y_BIAS, %d0
move.w  %d0, VDP_DATA
move.w  staged_scroll_y_bg, %d0
neg.w   %d0
addq.w  #VDP_DISPLAY_ORIGIN_Y_BIAS, %d0
move.w  %d0, VDP_DATA
```

No source/spec/tool changes outside this bounded scroll fix and the mechanical canonical invariant bump were made intentionally.

## Build Verification

Build 0166 release result:

- Build produced: YES
- Numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0166.bin`
- Rolling artifact: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `a74365146eef4fdf0e9b429d7e66d63186023e3541f36fc1fa9b2703eed62ff5`
- Size: `1,581,272` bytes
- Counter: `166`
- Canonical gate: `GATE_PASS`
- Boot guard: PASS
- `opcode_replace` patched-site count: `142` unchanged
- `total_genesis_bytes_covered`: `0x1820D4 -> 0x1820D8` mechanical `+0x4`

Generated disassembly confirms the vertical negation:

```asm
70228: 3039 00ff 409c  movew 0xff409c,%d0
7022e: 4440            negw %d0
70230: 5040            addqw #8,%d0
70232: 33c0 00c0 0000  movew %d0,0xc00000
70238: 3039 00ff 409a  movew 0xff409a,%d0
7023e: 4440            negw %d0
```

## Build 0166 Trace Validation

Build 0166 scripted MAME trace still reached active gameplay and the first death/fire boundary without a new fatal address in that sampled path. Source/staged raw scroll behavior stayed equivalent; inferred committed VSRAM changed to the negated convention:

| active-relative frame | raw staged FG/BG Y | inferred VSRAM FG/BG after fix |
|---:|---:|---:|
| `70` | `0x01F4` | `0xFE14` |
| `100` | `0x01D0` | `0xFE38` |
| `160` | `0x018F` | `0xFE79` |
| `220` | `0x0147` | `0xFEC1` |
| `230` | `0x013F` | `0xFEC9` |

This validates the mechanical sign-conversion change. Visual correctness still requires Tighe emulator verification.

## Non-Scroll Issue Status

- Rastan still appears: not visually rechecked by Cody; Build 0166 scripted state still reaches active gameplay.
- Fire/death: still occurs in scripted Build 0166 trace (`mode=0x0008` after active-relative frame ~224). Not fixed.
- Input/down+attack: not checked. Deferred.
- VBlank/rolling black bar: not checked. Deferred.
- ROUND 1 / READY flicker/header sprites: not checked. Deferred.
- Continue/game-over wrong tiles: not checked. Deferred.
- D00298 attract-demo: not checked. Deferred.
- Records `132..134`: not checked. Deferred.
- Palette lines `0..3`: not revalidated in this task; this task did not touch palette code.

## OPEN / CLOSED Issues Impact

- Open issues touched: OPEN-017, OPEN-024.
- New issues opened: none; the visual issues were recorded as Build 0165 addenda under existing open issues.
- Issues closed: none.
- Issues intentionally deferred: collision/death/fire surface state, input/down+attack, VBlank budget/rolling black bar, ROUND 1 / READY sprite/header lifecycle, continue/game-over tile lifecycle, D00298 attract-demo, suspicious PC090OJ records `132..134`, broader PC080SN/PC090OJ work.

## KNOWN_FINDINGS Impact

Option C: KF-015 refined. It now explicitly records the vertical `-raw + 8` conversion requirement and Build 0166 verification.

## STOP

STOP triggered: **NO**. A bounded scroll fix was proven and Build 0166 was produced. Remaining visual/runtime issues are explicitly deferred.
