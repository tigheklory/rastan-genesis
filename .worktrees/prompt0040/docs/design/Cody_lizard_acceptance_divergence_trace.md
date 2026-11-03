# Cody - Build 0205 Lizard-Man Acceptance Divergence Trace

**Date:** 2026-07-18
**Type:** Analysis / runtime verification only
**Build context:** Build 0205/256, `rastan-direct`
**Trace directory:** `states/traces/lizard_acceptance_divergence_20260718_214314/`
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0205.bin`
**SHA256:** `4238d2ffcd226c45f1251ccbe4e7e64fa9b642acb18c4957ab85e1fd888b4aee`
**Scope:** Evidence only. No source/spec/tool/Makefile/gate/invariant/ROM changes. No Build 0206.

## Phase 0

Relevant priors from `KNOWN_FINDINGS.md`:

- KF-060: enemy PC090OJ record production can diverge before SAT/VRAM; applies as historical enemy-output context.
- KF-061: invalid actor data can make the expansion engine unsafe; respected by Build 0205's valid/nonzero/special gates.
- KF-062: actor population and staging/expansion are separate boundaries; directly applicable to lizard-count interpretation.
- KF-063: `0x3D254` / arcade `0x3D054` is safe for validated actors after the shared `0x3C950` destination-aware fix; Build 0205 relies on this.
- KF-064: visible lizard ownership is block `A5+0x02C8` / composite records `140..229`, not record 46; primary target of this trace.
- KF-065: Build 0205 implements the selected block `A5+0x02C8` whole-block scratch/flush design; this trace validates acceptance symptoms after that implementation.

Rediscovery Hazard HIGH findings touched: PC090OJ mirror/candidate/represented flow, arcade-owned lifecycle/VBlank staging, lizard ownership. No contradiction of a CONFIRMED/STRONG finding detected.

Deferred-appendix entries relevant: none identified.

Task classification: **EXTENDING** - runtime acceptance analysis of the Build 0205 lizard composite staging implementation.

Open/Closed issues touched: OPEN-017 and OPEN-024 active; OPEN-001 graphics context. No closed issue contradicted.

Architecture compliance: **CONFIRMED**. The task used emulator observation only and did not add code, scaffolding, alternate renderer/SAT path, forced actors, forced candidates, or Genesis-owned gameplay flow.

## Recovered State

- Build counter: `205`.
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`.
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0205.bin`.
- Build 0205 SHA256: `4238d2ffcd226c45f1251ccbe4e7e64fa9b642acb18c4957ab85e1fd888b4aee`.
- Build 0205 size: `1583440` bytes.
- Rolling ROM byte-identical to numbered Build 0205: yes (`cmp=0`).
- Build 0204 preserved: yes.
- Build 0206 produced: **NO**.
- Makefile default and generated config: `PC090OJ_MIRROR_RECORDS = 256`.
- Canonical opcode_replace / coverage: `214` / `0x182950`.

## Evidence Captured

Files created under `states/traces/lizard_acceptance_divergence_20260718_214314/`:

- `lizard_acceptance_trace.lua` - trace-local MAME Lua harness.
- `arcade_summary.csv`, `arcade_actors.csv`, `arcade_records.csv`, `arcade_events.log`.
- `genesis_summary.csv`, `genesis_actors.csv`, `genesis_records.csv`, `genesis_events.log`.
- `lizard_acceptance_reduced.json`, `lizard_acceptance_reduced.md`.
- Screenshots: `snaps/arcade_f0720.png`, `snaps/arcade_f0840.png`, `snaps/arcade_f0960.png`, `snaps/arcade_f1080.png`, `snaps/arcade_f1320.png`, `snaps/arcade_f1500.png`, `snaps/arcade_f1680.png`, `snaps/genesis_f0720.png`, `snaps/genesis_f0840.png`, `snaps/genesis_f0960.png`, `snaps/genesis_f1080.png`.

Runs completed with exit code `0` for both original arcade `rastan` and Genesis Build 0205.

## Address Mapping Discipline

Address mappings below use `build/rastan-direct/address_map.json` where an arcade mapping exists.

- `runtime_genesis_pc 0x0003D254` maps to `arcade_pc 0x0003D054` (`arcade_copy`).
- `runtime_genesis_pc 0x0003A208` maps to `arcade_pc 0x0003A008` (`arcade_copy`).
- `runtime_genesis_pc 0x0003A27E` maps to `arcade_pc 0x0003A07E` (`arcade_copy`).
- `runtime_genesis_pc 0x000700C2`, `0x00071A8A`, and `0x00071BB8` are `genesis_only` wrapper/helper addresses and have no arcade_pc mapping.
- Runtime addresses in the shifted `0x041xxx` segment were not used as proof of arcade identity unless JSON-mapped; source comments may preserve old labels and are not authority.

## Matched Encounter Summary

The trace used deterministic boot/start/right input for both original arcade and Build 0205. The runs are matched by state/actor/mirror behavior, not absolute frame. The Genesis run uses `scene_id=0x20` while the arcade source uses original state bytes directly.

Representative matched window:

| Field | Arcade frame 720 | Genesis frame 720 |
|---|---:|---:|
| State | `2/3/0` | `2/3/0` |
| Player X/Y | `0x002B/0x0070` | `0x0027/0x0070` |
| Scroll X | `0x0000` | `0x0000` |
| Valid block-0x2C8 actors | `4` | `1` |
| Composite windows nonzero | `4` | `1` |
| Visible lizard records | `32` | `8` |
| Genesis represented records | N/A | `8` |
| Genesis waiting records | N/A | `0` |

## Visible-Lizard Count Boundary

Observed maxima in this trace:

| Metric | Original arcade | Genesis Build 0205 |
|---|---:|---:|
| Valid `A5+0x02C8` actors | `5` | `1` |
| Nonzero composite actor windows | `5` | `1` |
| Nonzero records in `140..238` | `48` | `10` |
| Visible records in `140..238` | `46` | `10` |
| Represented records | N/A | `10` |
| Waiting records | N/A | `0` |

First Genesis milestones:

- First valid actor: frame `563`.
- First nonzero block record: frame `564`.
- First visible block record: frame `564`.
- First represented block record: frame `571`.

Conclusion: Build 0205 does **not** lose the visible lizard at candidate, represented, waiting, or SAT-slot boundaries. It stages one valid lizard actor window and represents the visible records in that window. The first count divergence is **actor population/eligibility**: the original arcade run reaches up to five valid block-0x2C8 lizard actors/windows; the matched Build 0205 run reaches only one.

Count classification: **A/F hybrid**. For this matched run, only one lizard actor is populated/eligible on Genesis; additional arcade actors are absent from the Genesis actor block, not lost later. Whether that is legitimate progression/timing or a remaining stage-progression/spawn divergence requires a narrower spawn/progression trace.

Count root cause confirmed: **NO**. Boundary confirmed; upstream cause not confirmed.

Smallest potential fix boundary: actor population/progression feeding `Genesis-WRAM 0x00FF02C8..0x00FF0507`, not PC090OJ representation/SAT.

## Eight-Pixel Y Boundary

Selected component: composite record `220`, lizard code family `0x0066/0x0069`, actor entry 8 / group 8.

Representative Y samples:

| Sample | Raw word1 | Decoder pre-offset Y | Configured offset | Final screen Y | SAT Y |
|---|---:|---:|---:|---:|---:|
| Arcade frame 720 rec220 | `0x0079` | `121` | N/A | `121` | N/A |
| Genesis frame 720 rec220 | `0x0081` | `129` | `-8` | `121` | `0x00F9` |
| Arcade frame 840 rec220 | `0x007A` | `122` | N/A | `122` | N/A |
| Genesis frame 840 rec220 | `0x0082` | `130` | `-8` | `122` | `0x00FA` |
| Arcade frame 864 rec220 | `0x0079` | `121` | N/A | `121` | N/A |
| Genesis frame 864 rec220 | `0x0082` | `130` | `-8` | `122` | `0x00FA` |

The raw Genesis tuple is about `+8/+9` compared with the arcade raw tuple, and the related actor field `field1a` is `0x0081` in Genesis versus `0x0079` in comparable arcade walking samples. However, the existing decoder applies `PC090OJ_TO_GENESIS_Y_OFFSET = -8`, yielding final screen Y values that match the arcade selected component within 0-1 px.

Y classification: **A at raw tuple/input boundary, but compensated by the current decoder for this selected component**. The trace does not prove a final sprite-pipeline +8 error for record 220; it suggests Tighe's visual low-lizard observation may involve ground/plane relation, component geometry, or a different pose/component than this selected record.

Global offset change justified: **NO**.

Y root cause confirmed: **NO** for final visual low placement. Raw +8 provenance is confirmed, but final visual +8 is not confirmed by this trace.

Smallest potential fix boundary: no implementation boundary is safe yet. If pursued, next trace should correlate visible feet pixels against the foreground ground row and actor/sprite component bbox for the exact BlastEm screenshot pose.

## Palette Boundary

Selected visible lizard records use `word0=0x4046` and codes in `0x004B..0x0069`.

Genesis Build 0205 representative record 220:

- Tuple word0: `0x4046`.
- Low bank nibble participates: yes, low nibble `0x6`.
- `pc090oj_sprite_ctrl_shadow`: `0x0060` during the encounter.
- Effective arcade bank as used by the current Genesis selector: `(0x4046 & 0x000F) | ((0x0060 & 0x00E0) >> 1) = 0x36`.
- Current Genesis palette-line selection: general path `(0x36 >> 4) & 3 = 3`.
- SAT palette bits: line `3` (`sat_attr_tile` examples `0xEC44`, `0xEC50`, `0xEC5C`).
- Staged line 3 words sampled from Build 0205: `08AE 0000 0EEE 08AE 044A 0246 0008 0006 00EE 006E 0080 0060 0888 0666 0040 000E`.

Original arcade trace rows report the same low nibble `0x6` on `word0=0x4046` lizard records. The current Build 0205 Genesis path therefore does not drop SAT palette bits: it selects line 3 consistently from effective bank `0x36`. Tighe's visual report that the lizard uses pale/red/white colors is consistent with **correctly delivered but wrong-carrier palette line for this bank**, or a simultaneous palette-line conflict, not with missing lizard representation.

Committed CRAM: not independently dumped in this run. The staged line and SAT palette bits were captured; prior MAME palette APIs support CRAM dumps, but this harness did not include the palette-device readback. Do not treat committed CRAM as proven here.

Palette classification: **B/G candidate** - effective bank calculation appears mechanically coherent (`0x36`), but current Genesis line mapping sends it to line 3; whether line 3 is wrong for lizard bank `0x36` or conflicts with another sprite family needs arcade bank-to-CRAM provenance before a palette remap.

Palette root cause confirmed: **PARTIAL**. First boundary confirmed at bank-to-line carrier selection; exact intended Genesis carrier for bank `0x36` is not proven in this run.

Smallest potential fix boundary: palette bank `0x36` ownership/mapping audit; no palette patch yet.

## Lizard To Player Damage Boundary

Accepted user observation from BlastEm Build 0205:

- Rastan can attack and kill the lizard.
- The lizard does not kill or damage Rastan.

This trace does **not** prove the first lizard-to-player damage divergence. The automated input run did not reproduce a controlled lizard contact/attack window: the Genesis valid lizard actor disappears from the sampled actor block after frame `1088`, while the scripted attack/contact window was later. No player HP/hurt/invulnerability fields were field-resolved through disassembly in this task, and no player-damage writer was identified.

Combat classification: **UNRESOLVED / G possible**. In this trace, lizard-to-player damage was not exercised; the failure may be attack-state timing, hitbox data, overlap test, player invulnerability, or damage writer routing. Visual overlap from Tighe's screenshot is not sufficient proof of attack-active contact.

Visual Y error related to collision: **UNRESOLVED**. Current trace suggests selected lizard component screen Y is compensated correctly, and collision likely uses actor coordinates rather than final sprite pixels, but this was not proven at the damage routine.

Combat root cause confirmed: **NO**.

Smallest potential fix boundary: a dedicated arcade-vs-Genesis lizard contact trace that first resolves player HP/hurt/invulnerability and lizard attack-state fields from disassembly, then logs the exact original arcade player-damage writer and Genesis equivalent path.

## Synthesis

Independent roots found:

1. Visible-lizard count: first divergence at actor population/eligibility, upstream of Build 0205 staging/SAT.
2. Y: raw Genesis tuple is +8/+9 relative to arcade, but the current global `-8` offset compensates selected record 220; final visual +8 remains unproven.
3. Palette: lizard records use effective bank `0x36`; current Genesis selector maps it to line 3. Palette carrier/provenance remains the next boundary.
4. Combat: Tighe's observation is recorded, but this trace did not reproduce/resolve lizard-to-player damage flow.

Recommended fix order:

1. Count/progression/spawn boundary for missing additional lizard actors, because it is upstream and affects enemy presence.
2. Palette bank `0x36` provenance/mapping, because the visible lizard is recognizable but obviously wrong-colored.
3. Feet/ground visual-Y correlation for the exact BlastEm pose, without changing the global offset.
4. Dedicated lizard-to-player damage trace after fields/routines are resolved.

Next single implementation task: **NO implementation yet**. The next task should be evidence/design, not a build: trace actor-population/progression for block `A5+0x02C8` entries beyond entry 8, comparing original arcade and Genesis through the first multi-lizard encounter. If the team prioritizes visual correctness over additional actors, run a bank `0x36` arcade-palette-to-Genesis-carrier audit first.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-024, OPEN-001 context.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: Build 0206, global Y-offset patch, palette remap, forced lizards/candidates/SAT, collision/player HP changes, bat palette, black bar/VBlank, record 132, FG/sky/HUD/D00298/continue-game-over.

## KNOWN_FINDINGS Impact

Option A - no new finding/update. This task produces acceptance divergence evidence and boundaries, but not a complete durable root cause suitable for a new or revised KF entry. KF-065 remains the Build 0205 implementation prior; OPEN-017 carries the new acceptance results.

## STOP

STOP triggered: **YES, limited**.

STOP reason: the lizard-to-player damage boundary could not be safely pinned from this trace; the automated run did not reproduce a resolved attack/contact/damage window, and player/lizard combat fields were not disassembly-resolved. No fix is safe from this evidence.
