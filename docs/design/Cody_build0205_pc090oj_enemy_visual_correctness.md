# Cody - Build 0205 PC090OJ Enemy Visual Correctness / Palette / Tile Residency

**Date:** 2026-07-17  
**Type:** Analysis-first runtime evidence; no build produced  
**Build inspected:** Build 0204, `dist/rastan-direct/rastan_direct_video_test_build_0204.bin`  
**Build 0204 SHA256:** `0e1925b2934e2d2614bb6c90de82c78ea07bc62819b58fe345fb83f8e5deb083`  
**Trace directory:** `states/traces/build0205_enemy_visual_correctness_20260717_214210/`  
**Scope:** PC090OJ record-46 visual correctness, SAT ownership, tile/residency, palette route. No source/spec/tool/ROM/build changes. No PC080SN, black-bar, sky, player-control, collision, D00298, or sibling-block implementation work.

## Phase 0 / Recovery

Classification: **EXTENDING** OPEN-017 / OPEN-024, with OPEN-001 as graphics context. Relevant priors loaded: KF-047 (PC090OJ dirty/candidate output budget), KF-048/KF-049 (mirror size and safe floor), KF-050/KF-051 (player record composition and duplicate suppression), KF-053 (candidate/dirty fast path), KF-060/KF-061/KF-062/KF-063 (enemy records 46/57/96/140, engine safety on valid actors, Build 0204 record-46 output). No contradiction of a CONFIRMED/STRONG finding detected.

Recovered repo/build state:

- Current build counter before this task: `204`.
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`.
- Rolling ROM SHA256: `0e1925b2934e2d2614bb6c90de82c78ea07bc62819b58fe345fb83f8e5deb083`.
- Build 0204 exists and is preserved: `dist/rastan-direct/rastan_direct_video_test_build_0204.bin`.
- Build 0204 size: `1583248` bytes; counter `204`.
- Build 0205 exists before task: **NO**.
- Build 0206 exists before task: **NO**.
- Makefile mirror default: `PC090OJ_MIRROR_RECORDS ?= 256`.
- Generated mirror config: `PC090OJ_MIRROR_RECORDS=256` in `apps/rastan-direct/out/pc090oj_config.inc`.
- opcode_replace count: `214`.
- coverage invariant: `0x182890` in both canonical verifier files.
- `RULES.md` contains the Numbered ROM Artifact Preservation Rule.
- Source currently contains Build 0204 changes: `genesistan_hook_text_writer_3c950` destination split and `genesistan_pc090oj_hook_target_41dae` record-46 path are present.

Architecture compliance: **CONFIRMED**. This task did not change the arcade program, did not add a second renderer/SAT path, did not force records/SAT, and did not build a diagnostic ROM.

## Evidence Inspected

Source/static:

- `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, recent `AGENTS_LOG.md` tail.
- `apps/rastan-direct/src/pc090oj_hooks.s`.
- `apps/rastan-direct/src/vdp_comm.s`.
- `apps/rastan-direct/out/symbol.txt`.
- `build/rastan-direct/address_map.json`.

Runtime/evidence artifacts created:

- `states/traces/build0205_enemy_visual_correctness_20260717_214210/enemy_visual_trace.lua`.
- `states/traces/build0205_enemy_visual_correctness_20260717_214210/genesis_enemy_visual_samples.csv`.
- `states/traces/build0205_enemy_visual_correctness_20260717_214210/arcade_enemy_visual_samples.csv`.
- `states/traces/build0205_enemy_visual_correctness_20260717_214210/enemy_visual_reduced.md`.
- `states/traces/build0205_enemy_visual_correctness_20260717_214210/enemy_visual_reduced.json`.
- `states/traces/build0205_enemy_visual_correctness_20260717_214210/genesis_enemy_visual_record_writes.csv`.
- `states/traces/build0205_enemy_visual_correctness_20260717_214210/arcade_enemy_visual_record_writes.csv`.
- `states/traces/build0205_enemy_visual_correctness_20260717_214210/snaps_genesis/genesis_f0786.png`.
- `states/traces/build0205_enemy_visual_correctness_20260717_214210/snaps_genesis/genesis_f0900.png`.
- `states/traces/build0205_enemy_visual_correctness_20260717_214210/snaps_arcade/arcade_f0785.png`.
- `states/traces/build0205_enemy_visual_correctness_20260717_214210/snaps_arcade/arcade_f0900.png`.

Both runtime trace runs exited normally. No source/spec/tool/build artifacts were modified by the runs.

## Question 1 - Gray Asterisk / Record Ownership

Proven Build 0204 Genesis record-46 path:

| Frame | Record 46 words | Visible | Represented | Slot | SAT words | SAT tile | Palette line | Resident code |
|---:|---|---:|---:|---:|---|---:|---:|---:|
| `785` | `0000 0069 0275 0070` | `1` | `0` | `255` | `0000 0000 0000 0000` | `0000` | `0` | `FFFF` |
| `786` | `0000 0069 0275 0070` | `1` | `1` | `16` | `00E1 0502 C440 00F0` | `0440` | `2` | `0275` |
| `900` | `0000 0069 0277 006B` | `1` | `1` | `16` | `00E1 0502 C440 00EB` | `0440` | `2` | `0277` |
| `1800` | `0000 0069 0277 009B` | `1` | `1` | `16` | `00E1 0502 C440 011B` | `0440` | `2` | `0277` |

Decoded SAT word 2 `0xC440`:

- priority: `1`.
- palette line: `2`.
- hflip: `0`.
- vflip: `0`.
- tile index: `0x0440`.
- slot math: `SPRITE_TILE_BASE 0x0400 + slot16 * 4 = 0x0440`.

Visual capture:

- Genesis MAME snapshot at frame `786`: record 46 is represented in slot 16, but no distinct enemy is visible in the composite at the recorded screen coordinate.
- Genesis MAME snapshot at frame `900`: record 46 remains represented, but no distinct arcade-equivalent enemy is visible in the composite.
- Tighe's Exodus report shows a gray/pixel-clump style sprite in a related Build 0204 visual run, but this task did not have synchronized Exodus debugger state for that exact visual frame.

Classification:

- Record/SAT owner of the newly represented actor output: **record 46 / slot 16 PROVEN**.
- Exact owner of Tighe's gray asterisk/pixel-clump: **UNKNOWN / not fully proven by this MAME-only trace**. It is plausibly related to record 46/slot 16 because that is the newly represented enemy output, but the synchronized visual evidence required to prove the gray asterisk itself was not captured.
- Not enough evidence to classify it as stale record 132, another record, SAT residue, or non-PC090OJ output.

## Question 2 - Arcade Comparison

Arcade MAME was run with `-rompath roms` and the same deterministic input drive. The run reached gameplay and sampled PC090OJ records 46..56.

Representative arcade record 46 samples:

| Frame | Record 46 words | Code | Screen X/Y | Visible | Actor count |
|---:|---|---:|---|---:|---:|
| `780` | `0000 0061 0275 0039` | `0275` | `57,89` | `1` | `1` |
| `785` | `0000 0061 0277 0039` | `0277` | `57,89` | `1` | `2` |
| `900` | `0000 0061 0276 00C1` | `0276` | `193,89` | `1` | `1` |
| `1500` | `0000 0061 0277 007B` | `0277` | `123,89` | `1` | `2` |

Arcade snapshots at frames `785` and `900` show visible green enemy actors using the same `0x0275/0x0276/0x0277` code family. Genesis samples use the same code family but are not frame/camera-identical: Genesis record 46 has `yraw=0x0069`, while arcade samples show `yraw=0x0061`; X/timing also differs.

Classification: **partially A / not exact-match complete**.

- Proven: Genesis record 46 emits the same PC090OJ code family (`0x0275/0x0277`) as the arcade enemy path.
- Not proven: exact same actor/camera state equivalence. The deterministic runs are close enough to show code-family intent, but not enough to claim byte-identical record words at a matched camera state.
- Practical consequence: do not treat this as a spawn/wrong-record proof. The next issue is downstream visual/tile residency, not another actor-population proof.

## Question 3 - Tile / Art Mapping

Static path:

- `.Lpc090oj_place_record_in_slot` queues tile DMA for the slot at `pc090oj_hooks.s:1750..1754` using `d1 = code & 0x0FFF`.
- `.Lpc090oj_worklist_set` compares requested code against `sprite_tile_resident_code[slot]` and reserves/cancels worklist entries at `pc090oj_hooks.s:1580..1627`.
- `.Lvcs_tile_dma` commits worklist entries at `pc090oj_hooks.s:2095..2175`, using source `rastan_pc090oj + (code & 0x0FFF) * 128` and destination `(SPRITE_TILE_BASE + slot*4) * 32`.
- `_vblank_service` calls `vdp_prepare_sprites` before DISPLAY_OFF and `vdp_commit_sprites_vram` inside the commit section (`vdp_comm.s:178..192`).

Runtime facts for record 46 / slot 16:

- SAT tile index: `0x0440`.
- Expected VRAM byte address: `0x0440 * 0x20 = 0x8800`.
- `sprite_tile_resident_code[16]`: `0x0275` at frame `786`, `0x0277` by frame `900`.
- Source address for code `0x0277`: `rastan_pc090oj + 0x0277 * 128 = 0x0872C2`.
- Source bytes for code `0x0277`: nonzero (`28/128` bytes nonzero; checksum `836`).
- `pc090oj_tile_dma_count` was `1` during the code transition around frame `800`, then `0` after resident code caught up.

VDP VRAM evidence limitation:

- MAME Lua `:gen_vdp` `videoram` space reads returned zero for all sampled addresses, including the expected sprite tile at `0x8800` and in earlier historical probes. This conflicts with visible-render evidence in other contexts, so it is recorded as **tool-limited**, not automatically as true VRAM zero.
- A Lua write tap on `HW_ADDRESS 0x00C00004` did not fire in this environment, matching prior experience that VDP-port tracing usually requires native debugger watchpoints rather than Lua address-space taps.

Tile/root classification:

- **A tile-DMA-not-queued:** not supported; worklist count/resident transition indicate the slot/code path is active.
- **B wrong source code:** not supported for record 46; source code follows `0x0275 -> 0x0277`, matching arcade code family.
- **C wrong destination tile index:** not supported by SAT math; slot 16 correctly maps to tile `0x0440`.
- **D resident cache falsely thinks wrong tile is already resident:** not supported by sampled resident values after code transition, but true VRAM residency remains unproven.
- **E SAT points to stale tile index:** not supported; SAT tile is slot-derived and stable by design.
- **F/G decode/coverage wrong for enemy range:** not proven; source bytes exist for the codes.
- **H tile data correct, palette wrong:** not proven because true VRAM tile bytes could not be read.

Current best classification: **tile/residency boundary unresolved; no bounded fix proven**.

## Question 4 - Palette Route

Runtime values:

- `pc090oj_sprite_ctrl_shadow = 0x0060` during record-46 samples.
- `.Lpc090oj_decode_record` derives `d7 = (sprite_ctrl_shadow & 0x00E0) >> 1`, so `0x0060 -> 0x0030`.
- Record 46 `word0 = 0x0000`, so effective arcade bank is `(word0 & 0x000F) | 0x0030 = 0x0030`.
- `.Lpc090oj_place_record_in_slot` special-cases effective bank `0x30` to Genesis palette line `2`.
- SAT word2 `0xC440` confirms Genesis line `2`.

Staged palette line 2 sampled for record 46:

```text
0000 0642 0644 0644 0646 0644 0868 0668 066A 068C 068E 0AAC 0E00 0AEE 0E80 0CC0
```

Interpretation:

- The palette selector route is internally consistent with the Build 0175/0144-style bank-48 route: effective PC090OJ bank `0x30` maps to Genesis line `2`.
- Arcade snapshots show green enemy actors for the same code family; the sampled Genesis line 2 is green/brown-capable, so palette alone does not explain the MAME composite absence.
- Tighe's Exodus report that bats appear green/wrong is not resolved here. Bats were not captured as a separate synchronized actor/record owner in this task.

Palette classification: **B / unresolved until tile data is proven visible**. Do not patch palette first.

## Question 5 - Interaction / Collision

No collision implementation or interaction trace was run. Since the MAME composite did not show a distinct record-46 enemy while the arcade did, interaction cannot be classified from this evidence.

Classification: **F - more evidence needed**.

Do not add collision behavior in response to the gray asterisk report. First prove whether the visual object is the intended record-46 enemy, a small animation/effect, or tile/VRAM residue.

## Question 6 - Bat Spawn / Respawn

Bats were not captured in this trace. The task did not identify their actor block, record number, SAT slot, palette line, or respawn state.

Classification: **more evidence needed / deferred**.

The bat report remains useful user evidence, but it is not yet tied to record 46. Do not chase full bat respawn logic before the record-46 tile/visual path is proven.

## Build Decision

Build 0205 produced: **NO**.

Reason: the bounded-build gate was not met. Record 46/SAT ownership is proven, and the arcade code family is supported, but the actual downstream visual defect is not pinned to a single source line. The evidence points to a **tile-DMA / true-VRAM residency / VDP command visibility boundary**, but Lua could not prove true VDP VRAM contents or VDP control-port commands. A source patch now would be speculative.

## Recommended Next Task

One narrow debugger-side runtime trace, not a fix:

- Use native MAME debugger watchpoints or Exodus VDP monitor, not Lua VDP `videoram`, to capture the VDP DMA command sequence from `.Lvcs_tile_dma` while record 46 transitions `0x0275 -> 0x0277` in slot 16.
- Capture `pc090oj_tile_dma_count`, worklist entry `{slot=16, code=0x0277}`, VDP DMA source registers `0x93..0x97`, VDP destination control longword, and a true VRAM dump of `0x8800..0x887F` after the DMA.
- Compare true VRAM bytes against `rastan_pc090oj + 0x0277*128`.

Expected decision split:

- If true VRAM at `0x8800` remains zero or stale while resident says `0x0277`: fix `.Lvcs_tile_dma` / VDP DMA command/resident-update ordering.
- If true VRAM matches code `0x0277` but composite remains wrong/invisible: investigate sprite decode/size/priority/palette display path.
- If true VRAM matches and composite is visible but wrong colors: then investigate PC090OJ bank `0x30` palette delivery/CRAM line 2.

## OPEN / KNOWN_FINDINGS Impact

Open issues touched: OPEN-017, OPEN-024, OPEN-001 context. No new issue opened. No issue closed.

KNOWN_FINDINGS impact: **Option C - refine KF-063**. Build 0204's record-46 SAT reach is not sufficient for visual acceptance; downstream true-VRAM/tile-residency evidence remains unresolved.

## STOP

STOP triggered: **YES** - bounded implementation was not safely placeable. The exact visual-correctness fault was not proven from current evidence.
