# Cody - Build 0158 Player/Floor Trace Targets

**Date:** 2026-07-10  
**Type:** Analysis / bounded runtime evidence capture only  
**Build context:** Build 0157 accepted ROM, `dist/rastan-direct/rastan_direct_video_test_build_0157.bin`  
**Build 0157 SHA256:** `725c36a27a4ea55a4a99bcbca4bd5dde3bbaf00cffe6b5005b8997b90cdd2c4a`  
**Scope:** Identify player/floor trace targets and capture a short arcade-vs-Genesis timeline. No source/spec/tool/Makefile/ROM changes. No build. No implementation. No broad gameplay/rendering work.

## 1. Phase 0 Result

Relevant priors loaded from `KNOWN_FINDINGS.md`:

- KF-010: Genesis visible layers flow through BG/FG/sprite staging and VBlank commits.
- KF-011: arcade frame/VBlank lifecycle owns progression; Genesis VBlank is service/commit.
- KF-032: PC080SN writes must be routed through staging rather than raw VDP/PC080SN access.
- KF-039: mapped work-RAM base issues are high risk; distinguish arcade work RAM, Genesis WRAM, and absolute hardware/mapped windows.
- KF-040: PC080SN row aliasing remains architectural context for gameplay text/scroll content, not this player/floor trace.
- KF-041: opcode replacement must preserve arcade tail flow; no bypass-style success claims.

Rediscovery Hazard HIGH findings touched: KF-010, KF-011, KF-032, KF-039, KF-041. No contradiction detected.

Task classification: **EXTENDING**. This extends the Build 0157 player death/fall analysis and OPEN-001 gameplay/rendering thread.

Open/Closed issues touched:

- OPEN-001: gameplay/rendering still under investigation.
- OPEN-024: PC090OJ/sprite context only; not reworked here.
- OPEN-017: BlastEm/HV/debug context only; not touched.
- Closed issues touched: none.

Contradiction of CONFIRMED/STRONG finding: **NONE**.

## 2. Baseline

Observed before evidence capture:

- Branch: `rastan-direct-proposal`
- HEAD: `e4297f4`
- Build: accepted Build 0157
- Genesis ROM: `dist/rastan-direct/rastan_direct_video_test_build_0157.bin`
- ROM SHA256: `725c36a27a4ea55a4a99bcbca4bd5dde3bbaf00cffe6b5005b8997b90cdd2c4a`
- Counter context: Build 0157 accepted; no new build was run.
- Git status already dirty before this task: `AGENTS_LOG.md`, `OPEN_ISSUES.md`, `build/mame/home/genesistrace/genesis_exec_trace.log`, and untracked `docs/design/Cody_player_death_fall_analysis.md`.

This task created trace artifacts and this design note only.

## 3. Address Mapping Method

PC mappings use `build/rastan-direct/address_map.json` as authority. All listed mappings below are exact segment hits in `kind=arcade_copy`, `source=whole_maincpu_copy`; no `+0x200` arithmetic is used as proof.

| Arcade PC | Genesis runtime PC | Mapping source | Confidence |
|---:|---:|---|---|
| `0x03A79C` | `0x03A99C` | `address_map.json`, `arcade_copy` | high |
| `0x03A7FA` | `0x03A9FA` | `address_map.json`, `arcade_copy` | high |
| `0x03A832` | `0x03AA32` | `address_map.json`, `arcade_copy` | high |
| `0x03A860` | `0x03AA60` | `address_map.json`, `arcade_copy` | high |
| `0x03A614` | `0x03A814` | `address_map.json`, `arcade_copy` | high |
| `0x03A6B2` | `0x03A8B2` | `address_map.json`, `arcade_copy` | high |
| `0x041F0E` | `0x04210E` | `address_map.json`, `arcade_copy` | high |
| `0x051024` | `0x051224` | `address_map.json`, `arcade_copy` | high |
| `0x0504FA` | `0x0506FA` | `address_map.json`, `arcade_copy` | high |
| `0x05052E` | `0x05072E` | `address_map.json`, `arcade_copy` | high |
| `0x050534` | `0x050734` | `address_map.json`, `arcade_copy` | high |
| `0x0505FC` | `0x0507FC` | `address_map.json`, `arcade_copy` | high |
| `0x05126E` | `0x05146E` | `address_map.json`, `arcade_copy` | high |
| `0x0512C8` | `0x0514C8` | `address_map.json`, `arcade_copy` | high |
| `0x0517FA` | `0x0519FA` | `address_map.json`, `arcade_copy` | high |
| `0x052816` | `0x052A16` | `address_map.json`, `arcade_copy` | high |
| `0x05283E` | `0x052A3E` | `address_map.json`, `arcade_copy` | high |
| `0x0528CA` | `0x052ACA` | `address_map.json`, `arcade_copy` | high |
| `0x053850` | `0x053A50` | `address_map.json`, `arcade_copy` | high |
| `0x0538EA` | `0x053AEA` | `address_map.json`, `arcade_copy` | high |
| `0x053956` | `0x053B56` | `address_map.json`, `arcade_copy` | high |
| `0x0539C2` | `0x053BC2` | `address_map.json`, `arcade_copy` | high |
| `0x053A2E` | `0x053C2E` | `address_map.json`, `arcade_copy` | high |
| `0x053A6E` | `0x053C6E` | `address_map.json`, `arcade_copy` | high |
| `0x055DDC` | `0x055FDC` | `address_map.json`, `arcade_copy` | high |
| `0x0447B6` | `0x0449B6` | `address_map.json`, `arcade_copy` | high |
| `0x0449B4` | `0x044BB4` | `address_map.json`, `arcade_copy` | high |
| `0x0428B2` | `0x042AB2` | `address_map.json`, `arcade_copy` | high |
| `0x040B66` | `0x040D66` | `address_map.json`, `arcade_copy` | high |
| `0x0420E6` | `0x0422E6` | `address_map.json`, `arcade_copy` | high |

Work RAM mapping used in the trace:

- Arcade A5/work RAM base: `arcade_work_ram 0x0010C000`.
- Genesis A5/work RAM base: `Genesis-WRAM 0x00FF0000`.
- Direct offset mapping for A5-relative fields: `arcade 0x0010C000 + offset` corresponds to `Genesis-WRAM 0x00FF0000 + offset`.
- Absolute map/collision lookup window: code computes/uses `0x0010DE00 + derived_offset`; this remains labeled separately from `Genesis-WRAM` because Build 0157 code still contains absolute `0x0010DE00` references in the copied arcade helper path.

## 4. Files / Evidence Inspected

- `RULES.md`
- `ARCHITECTURE.md`
- `AGENTS.md`
- `AGENTS_LOG.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- `docs/design/Cody_player_death_fall_analysis.md`
- `docs/reverse-engineering/player_input_trace.md`
- `docs/reverse-engineering/startup_mode_reference.md`
- `docs/reverse-engineering/mode_flow_reference.md`
- `docs/reverse-engineering/disassembly_reference.md`
- `docs/reverse-engineering/02c8_reference.md`
- `docs/reverse-engineering/02c8_state_reference.md`
- `docs/reverse-engineering/02c8_frame_reference.md`
- `docs/reverse-engineering/02c8_constructor_reference.md`
- `docs/reverse-engineering/0508_reference.md`
- `build/maincpu.disasm.txt`
- `build/genesis_postpatch.disasm.txt`
- `build/rastan-direct/address_map.json`
- `apps/rastan-direct/out/symbol.txt`
- `states/traces/build_0157_gameplay_sprites/`
- New bounded trace directory: `states/traces/build_0158_player_floor_trace_targets_20260710_230533/`

## 5. Player Object Candidates

### Candidate 1: A5-relative player global cluster

Status: **strongest confirmed player state**, high confidence.

| Field | Arcade work RAM | Genesis WRAM | Evidence |
|---|---:|---:|---|
| player X | `0x0010D0BE` (`a5+0x10BE`) | `0x00FF10BE` | setup writes at arcade `0x05052E`; movement routines update/read it |
| player Y | `0x0010D0C0` (`a5+0x10C0`) | `0x00FF10C0` | setup writes at arcade `0x050534`; movement/fall path updates/read it |
| collision/contact flags | `0x0010D0CE` (`a5+0x10CE`) | `0x00FF10CE` | consulted/set by `0x053A6E` and related movement probes |
| movement/collision bitfield | `0x0010D0D0` (`a5+0x10D0`) | `0x00FF10D0` | consumed by arcade `0x0512C8`; set by movement helper tails |
| horizontal collision amount | `0x0010D0D8` (`a5+0x10D8`) | `0x00FF10D8` | written by left/right helper tails |
| vertical collision amount | `0x0010D0DA` (`a5+0x10DA`) | `0x00FF10DA` | written by up/down helper tails |
| player mode/state-ish word | `0x0010D0E8` (`a5+0x10E8`) | `0x00FF10E8` | active samples show `0x0003`, exit samples show `0x0008` |
| staged entry X/Y | `0x0010D354/0x0010D356` | `0x00FF1354/0x00FF1356` | `0x052816` copies staged coords into live X/Y |
| entry command | `0x0010D37A` | `0x00FF137A` | active timeline diverges between arcade and Genesis |
| death/round controller | `0x0010D394/0x0010D3AA` | `0x00FF1394/0x00FF13AA` | `0x055DDC` controller cluster / death-stage context |

Key static evidence:

- Arcade `0x05052E` / `0x050534` initialize `a5+0x10BE/0x10C0` from the stage setup table.
- Arcade `0x052816` copies `a5+0x1354/0x1356` into `a5+0x10BE/0x10C0`.
- Arcade `0x0517FA` transforms movement accumulators into calls to `0x053850`, `0x0538EA`, `0x053956`, and `0x0539C2`.
- Those movement helpers update `a5+0x10BE/0x10C0` and set `a5+0x10CE/0x10D0/0x10D8/0x10DA` collision/result flags.

Trace support:

- Arcade active sample sequence: player `0x0020/0x0030` at active+0, `0x0020/0x0037` at active+10, `0x0020/0x006E` at active+30, `0x0020/0x0070` at active+60.
- Genesis active sample sequence: player `0x0020/0x0030` at active+0, `0x0020/0x003C` at active+10, `0x0020/0x005C` at active+30, `0x0020/0x0070` at active+60.

Interpretation: the A5-relative player cluster is confirmed enough to be the primary player/fall trace target. It is not, by itself, the final visible sprite object.

### Candidate 2: `0x02C8` actor list

Status: **strong visible-body candidate**, medium confidence.

- Arcade base: `arcade_work_ram 0x0010C2C8`.
- Genesis base: `Genesis-WRAM 0x00FF02C8`.
- Entry size: `0x40` bytes.
- Count used by the documented top-level update pass: 9 entries.
- Important fields: active `+0x00`, state `+0x05`, class `+0x06`, X `+0x16`, Y `+0x1A`, display Y `+0x30`, display X `+0x32`, animation selector `+0x3E`.

Evidence:

- Arcade `0x0447B6` copies player X/Y into a `0x02C8` actor: `a5+0x10BE -> a4+0x32`, `a5+0x10C0 -> a4+0x30`, then clears `a4+0x07`.
- Arcade `0x0449B4` iterates the `0x02C8` list and calls the actor handler family.
- Trace samples show `0x02C8` entries active in both arcade and Genesis during active gameplay, but sampled display X/Y did not yet identify a main body actor.

Limit:

- The trace did not prove which concrete `0x02C8` entry is the player body.
- Several active entries remain helper/environment-like (`x=0, y=0x0180`, display `0/0`) in the sampled window.

### Candidate 3: `0x0508` actor list

Status: **player-linked upstream/control candidate**, medium-low confidence as final body.

- Arcade base: `arcade_work_ram 0x0010C508`.
- Genesis base: `Genesis-WRAM 0x00FF0508`.
- Entry size: `0x40` bytes.
- Count: 20 entries.

Evidence:

- Arcade `0x0428B2` copies player X and player Y-16 into a `0x0508` actor display coordinate pair.
- `docs/reverse-engineering/0508_reference.md` marks it as player-linked but not proven as the final visible body.

Trace support:

- The bounded no-input Stage 1 trace did not show active `0x0508` entries in active gameplay samples.

Interpretation: keep `0x0508` as an upstream ownership/control candidate, not the primary visible-body object.

## 6. Collision / Floor / Death Routine Candidates

### Player update / active gameplay frame anchor

- Arcade PC: `0x041F0E`
- Genesis runtime PC: `0x04210E`
- Role: active gameplay loop entry.
- Evidence: documented main gameplay update path.

### Active gameplay frame body

- Arcade PC: `0x051024`
- Genesis runtime PC: `0x051224`
- Role: per-frame active gameplay body; calls side-entry threshold, event, movement, render-related subsystems.
- Evidence: disassembly shows calls through `0x05126E`, `0x052BB6`, `0x052B38`, `0x052B4A`, `0x054A2C`, `0x0512C8`, `0x05132A`, and other update helpers.

### Movement accumulator to coordinate updater

- Arcade PC: `0x0517FA`
- Genesis runtime PC: `0x0519FA`
- Role: converts movement accumulators at `a5+0x1262/1264/1266/1268` into step amounts and calls the four movement helpers.
- Evidence: static disassembly plus `player_input_trace.md`.

### Four movement/fall helpers

| Role | Arcade PC | Genesis runtime PC | Key fields |
|---|---:|---:|---|
| vertical/up-style path | `0x053850` | `0x053A50` | reads step `a5+0x10DE`, updates Y / flags |
| vertical/down-style path | `0x0538EA` | `0x053AEA` | reads step `a5+0x10DE`, updates Y / flags |
| horizontal/right-style path | `0x053956` | `0x053B56` | reads step `a5+0x10DC`, updates X / flags |
| horizontal/left-style path | `0x0539C2` | `0x053BC2` | reads step `a5+0x10DC`, updates X / flags |

Evidence:

- These routines update `a5+0x10BE/0x10C0` directly or set the correction bitfield and amounts consumed by `0x0512C8`.
- They consult `a5+0x10CE` bits after calling collision probes.

### Collision/map pointer helper

- Arcade PC: `0x053A2E`
- Genesis runtime PC: `0x053C2E`
- Role: computes `a0 = 0x0010DE00 + derived_offset` from camera/origin and input probe coordinates in `d1/d2`.
- Inputs: `a5+0x10AE`, `a5+0x10B0`, `d1`, `d2`.
- Output: `a0` points into the `0x0010DE00` map/collision lookup window.
- Evidence: static disassembly.

### Collision/contact probe wrapper

- Arcade PC: `0x053A6E`
- Genesis runtime PC: `0x053C6E`
- Role: reads player X/Y, subtracts vertical probe amount, calls `0x053A2E` up to three times, reads `a0@`, masks `& 0x007F`, compares tile values `1` and `2`, and sets `a5+0x10CE` bits. On tile `2`, saves `a0` to `a5+0x111C`.
- Evidence: static disassembly.

### Collision correction consumer

- Arcade PC: `0x0512C8`
- Genesis runtime PC: `0x0514C8`
- Role: consumes bits in `a5+0x10D0`; calls helper tails `0x053934`, `0x0538C8`, `0x0539A0`, `0x053A0C` with amounts loaded from `0x0010D0DA` / `0x0010D0D8`.
- Evidence: static disassembly.

### Death / round / life-loss controller

- Arcade PC: `0x055DDC`
- Genesis runtime PC: `0x055FDC`
- Role: death/game-over/continue/stage-presentation controller keyed by `a5+0x1394` / `a5+0x13AA`.
- Evidence: `mode_flow_reference.md` documents states `1..8` as death/game-over/continue and `9..13` as round/stage presentation.

## 7. Trace Method

Trace directory:

- `states/traces/build_0158_player_floor_trace_targets_20260710_230533/`

Files:

- `capture_arcade_player_floor.lua`
- `capture_genesis_player_floor.lua`
- `arcade_player_floor_trace.log`
- `genesis_player_floor_trace.log`

Method:

- Both traces use the same coin/start schedule as prior short traces.
- Arcade run: original MAME `rastan` with `roms/` as ROM path.
- Genesis run: MAME `genesis` with Build 0157 ROM.
- Both runs sample scene/state words, player cluster, camera/scroll, entry/death words, and `0x02C8` / `0x0508` actor candidates.
- Both scripts installed narrow write/read taps for the player cluster and map lookup window. The scripts exited at active-state exit or frame cap.

Trace limitation:

- The timeline samples were captured successfully.
- The write/read taps did **not** report post-start player-coordinate writes or map reads in this run (`cluster_writes=0`, `map_reads=0` after the refined filter), even though sampled player Y changed over time. This means the runtime trace did not prove the exact PC-at-write or collision/floor lookup entry/exit. The static candidates above remain supported; the exact runtime collision/floor call is not yet proven.

## 8. Arcade Timeline

Original arcade MAME run summary:

- First active `2/3/0` frame: frame `307`.
- Active-state exit: frame `895`, state `2/4/0`.
- No death/life-loss state was captured in the bounded window.
- Map-read tap count: `0`.

Key samples:

| Logical sample | Frame | State | Player X/Y | FG camera | BG camera | flags | move | d8/da | entry cmd | death words |
|---|---:|---|---|---|---|---|---|---|---|---|
| setup frame | `250` | `2/2/7` | `0000/0000` | `0000/0000` | `0000/0000` | `0000` | `0000` | `0000/0000` | `0000` | `00FF/0001` |
| active +0 | `307` | `2/3/0` | `0020/0030` | `0000/0000` | `0000/0000` | `0000` | `0000` | `0000/0000` | `0000` | `00FF/0001` |
| active +10 | `317` | `2/3/0` | `0020/0037` | `0000/0000` | `0000/0000` | `0000` | `0000` | `0000/0000` | `00FF` | `00FF/0001` |
| active +30 | `337` | `2/3/0` | `0020/006E` | `0000/0000` | `0000/0000` | `0000` | `0000` | `0000/0000` | `00FF` | `00FF/0001` |
| ready frame | `340` | `2/3/0` | `0020/0070` | `0000/01F9` | `0000/01F9` | `0000` | `0002` | `0000/0003` | `00FF` | `00FF/0001` |
| active +60 | `367` | `2/3/0` | `0020/0070` | `0000/01A8` | `0000/01A8` | `0000` | `0002` | `0000/0003` | `00FF` | `00FF/0001` |
| active exit | `895` | `2/4/0` | `0020/0070` | `0001/0149` | `0000/0149` | `0004` | `0000` | `0001/0002` | `00FF` | `00FF/0001` |

## 9. Genesis Timeline

Genesis Build 0157 MAME run summary:

- First active `2/3/0` frame: frame `533`.
- Active-state exit: frame `846`, state `2/4/0`.
- No death/life-loss state was captured in the bounded window.
- Map-read tap count: `0`.

Key samples:

| Logical sample | Frame | State | Player X/Y | FG camera | BG camera | flags | move | d8/da | entry cmd | death words |
|---|---:|---|---|---|---|---|---|---|---|---|
| setup frame | `250` | `2/2/7` | `0000/0000` | `0000/0000` | `0000/0000` | `0000` | `0000` | `0000/0000` | `0000` | `00FF/0001` |
| ready frame | `340` | `2/2/7` | `0000/0000` | `0000/0000` | `0000/0000` | `0000` | `0000` | `0000/0000` | `0000` | `00FF/0001` |
| active +0 | `533` | `2/3/0` | `0020/0030` | `0000/0000` | `0000/0000` | `0000` | `0000` | `0000/0000` | `0000` | `00FF/0001` |
| active +10 | `543` | `2/3/0` | `0020/003C` | `0000/0000` | `0000/0000` | `0000` | `0000` | `0000/0000` | `5553` | `00FF/0001` |
| active +30 | `563` | `2/3/0` | `0020/005C` | `0000/0000` | `0000/0000` | `0000` | `0000` | `0000/0000` | `5553` | `00FF/0001` |
| active +60 | `593` | `2/3/0` | `0020/0070` | `0000/01E8` | `0000/01E8` | `0000` | `0002` | `0000/0004` | `5553` | `00FF/0001` |
| active exit | `846` | `2/4/0` | `0020/0070` | `0000/0147` | `0000/0147` | `0200` | `0000` | `0000/0004` | `5553` | `00FF/0001` |

## 10. First Divergence

First death/fall/life-loss divergence: **not proven**.

First sampled player/fall trajectory divergence: **active +10**.

- Arcade active+10: player Y `0x0037`, entry command `0x00FF`.
- Genesis active+10: player Y `0x003C`, entry command `0x5553`.

Additional divergence by active+30:

- Arcade player Y `0x006E`.
- Genesis player Y `0x005C`.

By active+60 both have player Y `0x0070`, but scroll/camera and correction amounts differ:

- Arcade: camera `0000/01A8`, `move=0002`, `d8/da=0000/0003`.
- Genesis: camera `0000/01E8`, `move=0002`, `d8/da=0000/0004`.

Active-state exit differs:

- Arcade exits active at frame `895`, flags `0x0004`, d8/da `0001/0002`.
- Genesis exits active at frame `846`, flags `0x0200`, d8/da `0000/0004`.

Interpretation: the bounded trace proves an early player/entry-command trajectory mismatch, but it does **not** yet prove the first death/fall/life-loss divergence or identify the exact collision/floor lookup result that caused the mismatch.

## 11. Readiness Classification

Classification: **B - More analysis needed: player object found but collision/floor routine not runtime-proven.**

Why not A:

- The player global cluster is identified and traceable.
- Static collision/floor candidates are identified.
- The bounded trace captured an early trajectory divergence.
- However, no map-read/collision-tile read events were captured, and no exact PC-at-write for the post-start player-coordinate updates was captured. Therefore the first causal collision/floor divergence is not proven and no Build 0158 implementation boundary is safe yet.

Why not C:

- The player state cluster is stronger than the collision/floor runtime proof, not the other way around.

## 12. Exact Next Implementation Boundary If Ready

Not ready. No implementation boundary is authorized from this evidence.

Next evidence boundary, not implementation: instrument or trace the current active-gameplay player update path narrowly enough to catch:

- writes to `a5+0x10BE/0x10C0` after active gameplay begins;
- reads from the `0x0010DE00` map/collision lookup window;
- entries/exits for mapped PCs `0x053A50`, `0x053AEA`, `0x053B56`, `0x053BC2`, `0x053C2E`, `0x053C6E`, and `0x0514C8` on the Genesis side;
- same arcade PCs for comparison.

## 13. Future Tooling Note

Do not create this in the current task.

A small `tools/translation/addr_xlat.py` helper would reduce repeated manual JSON inspection. Minimum useful behavior:

- read `build/rastan-direct/address_map.json`;
- map `arcade_pc -> runtime_genesis_pc` and inverse for `arcade_copy` and `patched_site` segments;
- label mapping kind/source;
- handle A5-relative work-RAM offsets (`arcade 0x0010C000+off` to `Genesis-WRAM 0x00FF0000+off`);
- explicitly refuse hardware-window mappings unless supplied a known hardware translation rule.

## 14. Architecture Compliance

Confirmed.

- Arcade code remains the program.
- Genesis-side behavior is treated as helper/opcode replacement and staging/commit service.
- No source/spec/tool/Makefile/ROM/build changes were made.
- No implementation or fix design was performed.
- No unrelated systems were chased beyond the player/floor trace target.

## 15. Open / Closed Issues Impact

- Open issues touched: OPEN-001 (gameplay/rendering), OPEN-024 (sprite context only), OPEN-017 (context only).
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: continue/game-over, D00298, Exodus, audio, tilemaps, general rendering, and sprite/SAT handoff.

No issue ledger update was required by this documentation/evidence-only task.

## 16. KNOWN_FINDINGS Impact

Option A - no new finding to index.

Rationale: this task establishes player/floor trace targets and a bounded early divergence, but it does not prove a durable root-cause mechanism or safe fix boundary. KF update should wait until the exact collision/floor/player-state causality is proven.

## 17. STOP Conditions

STOP triggered: **NO**.

Limits encountered:

- Bounded trace did not capture map-read callbacks or player-coordinate write callbacks in the active window.
- First death/fall/life-loss divergence remains unproven.

These are evidence limits, not architecture violations.
