# Cody Build 0499 — Native stage graphics and level data

**Agent / task:** Cody, RG-021 — Implement Native Genesis Stage Graphics and Level Data  
**Architecture handoff:** `docs/design/Andy_RG020_native_stage_audit_cody_handoff.md` at `14310d96`  
**Baseline:** Build 0495; Build 0492 remains the accepted gameplay/audio baseline  
**Candidate:** Build 0499 — **NOT ACCEPTED; Tighe hardware/visual verification pending**  
**Exact ROM-producing source:** `d7cb40bbbe6ec0ccf7a8d6ae965efad4c7193ae6`

## Artifact and build state

- Normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0499.bin`
- SHA-256: `215e8759c84ba8dd340b21146ac6221281e5305cf1bcffca06f12e387553d2b0`
- Size: 3,399,352 bytes
- Build counter: 0495 → 0496 → 0497 → 0498 → 0499; final counter 499.
- Canonical gate: PASS; gameplay-entry gate: PASS; established R1 epoch gate: PASS.
- Opcode-replacement sites: 228 (unchanged).
- Canonical Genesis coverage: exact `0x33DEB8`; the prior `0x335EB8` expectation was extended by the intentional 32 KiB Round-2 native corpus.
- Standard family: canonical, `_d`, `_s`, `_do`, `_c`, `_full_hud`, `_invincible` all generated and configuration-verified.
- Optional selector family: all 18 `_S1-1` through `_S6-3` artifacts generated; each differs from canonical only at the established selector byte `0x05FF9F`.

Intermediate numbered artifacts are preserved:

| Build | SHA-256 | Size | Status / reason |
|---|---|---:|---|
| 0496 | `a8b0a0120608ce6a663fadede95a2826463652fb80a374b45e690ef428f8a71f` | 3,399,352 | **REJECTED / DIAGNOSTIC ONLY.** S1-3's retained post-fill cursor selected Round 2; initial gate failures were also caused by a missing legacy verifier alias. |
| 0497 | `69b8e5f1dec8a503226793d4fe9476e111829133172a3561508d7ce0152c278c` | 3,399,352 | **REJECTED / DIAGNOSTIC ONLY.** Round ownership fixed, but S2-1/S2-3 showed 149/237 Plane-A misses. |
| 0498 | `993415e600d8e6384951b48e7f1eb186789f53ee367e36fbd28bb916a6318356` | 3,399,352 | **REJECTED / DIAGNOSTIC ONLY.** Proved initial record ordering was not the remaining cause; the same map misses remained. |
| 0499 | `215e8759c84ba8dd340b21146ac6221281e5305cf1bcffca06f12e387553d2b0` | 3,399,352 | **CANDIDATE / USER MUST VERIFY.** Complete A-package counts preserved through fixed-B installation; R1/R2 probes have zero A/B misses. |

## Semantic cut and retired chip tail

The retained arcade program remains authoritative for stage/checkpoint selection (`a5+0x1242`), map-record progression (`a5+0x013E`), selector/strip-source decisions, Plane-B descriptor progression, scroll, collision, and scene lifecycle. The offline compiler consumes those original semantic records and emits exact Genesis pattern packages, direct code-to-slot LUT entries, per-round fixed Plane-B vocabularies, and scene-entry DMA data. Runtime work is a bounded package selection/install at the existing semantic scene/record boundary.

For records newly covered here, the retired tail is PC080SN name-RAM/C-window execution and R1-only/absent-content behavior. Records 21–45 now reach final Genesis pattern/name ownership directly; no PC080SN software device, chip-address walk, shadow name RAM, generic runtime tile search, LRU, per-frame conversion, framebuffer, fallback renderer, NOP, RTS bypass, or equal-length patch hack was added.

Legacy intentionally remaining: the retained arcade gameplay/state/scroll/collision producers; the existing native staging/VBlank publication pipeline; compatibility behavior for Rounds 3–6, which this assignment explicitly classifies but does not convert.

## Implementation

### Round 1 castle and boss tail

Static decoding of `STAGE_TABLE 0x5073A`, `SEED_TABLE 0x50EE0`, stream `0x50F6B`, `TM0_TABLE 0x507C5`, and `PLANE_B_DESC_TABLE 0x3951C` establishes the physical Round-1 group as records 0–22. Castle starts at stage/record 16; its field tail occupies records 16–20. Boss-tail records 21–22 were absent from the prior native epoch. Package 5 now owns the exact union for records 16–22 instead of reusing the small-cave subset.

S1-2 starts with stage 16 and reaches active record 17/package 5; S1-3 starts with stage 22, retains Round-1 ownership despite the post-fill cursor reaching 23, and uses record 22/package 5. Both report zero A/B misses. Existing R1 packages 0–4 and transition packages 8–11 retain their prior payload hashes; only the intentional castle/boss package expands.

### General Round-2 data path

`compile_pc080sn_genesis.py` now emits one canonical multi-round binary from the original tables rather than a copied per-round script:

- 46 records (Round 1 records 0–22; Round 2 records 23–45);
- eight stable Plane-A epochs with 283, 334, 640, 584, 640, 542, 630, and 544 exact patterns;
- per-round fixed Plane-B vocabularies: Round 1 descriptors 0–55 / 854 patterns; Round 2 descriptors 56–111 / 460 patterns;
- 12 total packages, including the four established R1 overlap packages;
- 83,280-byte binary, zero compiler drops, zero transition collisions;
- unchanged R1 gameplay/cave preload inputs (`68ee659b…`, `ec0cee7c…`).

The final generated resource hashes are:

- `boundary_packages.bin`: `a6b39edd9b0df06fdfb2df1eabdfb89fc57ab500f5805f6b215dc86e59077ff4`
- `boundary_constants.inc`: `09cbc5cc97aeb459e25759cc72d2a555dea20c0bc9b434e92be3ec21499fd206`
- `boundary_report.json`: `897c6a2543ed75e37a20523433037030b7c6a282a412108a6455bb72a0273552`
- `slot_patterns_debug.json`: `9c2ac1e8897e516ded541a40cda658af7d77b0ea62ddefc5a7c1982e906b79fa`

The runtime installer tracks active/pending round, selects the authoritative stage index for the first scene-entry package, clamps only the known boss post-fill cursor to its owning round, and changes the fixed Plane-B vocabulary only at a round/scene boundary. A diagnostic on Builds 0497–0498 found package codes `0x0D12`, `0x0D15`, and `0x0F2D` present offline but absent from the live LUT. Root cause was D5/D6 reuse: the fixed-B loop overwrote the selected Plane-A map/upload counts. Build 0499 preserves those counts, eliminating all measured R2 misses without adding fallback logic.

R2 was already recognized as gameplay by the original strip-source range (`scene_id=1`); broadening that range was therefore neither required nor safe. The correction supplies the previously absent Round-2 content through the established `scene_load.s`, native staging, DMA, and VBlank path.

### Palette integration boundary

No RG-022 scene-specific export contract/assets exist in this repository state. Palette Composer, its persistence logic, and `specs/palette_decisions.json` were not modified. Genesis integration now prevents the Round-1 Test palette from being silently installed or protected for stage index 23 and later. Round 2 therefore retains the original finite arcade palette conversion until Tighe-approved RG-022 assets are exported. This is an integration guard, not a new palette decision or competing registry.

## Static proof

- Canonical build/gate PASS; 228 opcode sites and exact `0x33DEB8` coverage.
- Native metatile generator: 4,733 records, exact gate PASS.
- Plane-B visual records: 392 valid, collision NO.
- Native package compiler: 46-record contiguous cover, eight epochs, zero drops.
- Transition retention gate: rope 12 and waterfall 224 retained; peaks 395/479/607/346 ≤ 676; missing 0; collisions 0.
- Existing R1 package payload identity locked for every unchanged package.
- All seven configurations verified; all 18 selector variants statically verified.
- `git diff --check` passed for every changed source/tool file.

## Runtime validation

Platform for all runtime tests: **MAME `genesis` USA/NTSC driver**, not PAL `megadriv` and not BlastEm.

The maintained credit/start initialization probe reports:

| Variant | Stage / post-fill segment | Active native owner | A/B misses | Terminal real-MD VRAM names |
|---|---|---|---:|---|
| canonical / S1-1 | 0 / 1 | record 1, package 0, round 1 | 0 / 0 | gameplay entry PASS |
| S1-2 | 16 / 17 | record 17, package 5, round 1 | 0 / 0 | Plane A 2048 nonzero words; Plane B 2048 |
| S1-3 | 22 / 23 | record 22, package 5, round 1 | 0 / 0 | Plane A 2048; Plane B 2048 |
| S2-1 | 23 / 24 | record 24, package 6, round 2 | 0 / 0 | Plane A 2048; Plane B 2048 |
| S2-2 | 39 / 40 | record 40, package 7, round 2 | 0 / 0 | package selection/miss gate PASS |
| S2-3 | 45 / 46 | record 45, package 7, round 2 | 0 / 0 | package selection/miss gate PASS |

The VRAM values are terminal 68000 VDP data-port reads immediately before emulator exit; MAME's 16 KiB compatibility `videoram` Lua space was explicitly not used as Mega Drive VRAM evidence. These checks prove publication/nonblank ownership, not visual correctness.

Later-round classification, using all maintained `_Sx-y` initializers:

- R3-S1/S2/S3: **Mode B**, scene not recognized (`scene_id=0`).
- R4-S1/S2/S3: **Mode A**, scene recognized (`scene_id=1`) but no native package (`FFFF`; 4032 A / 2048 B misses).
- R5-S1/S2/S3: **Mode B**, scene not recognized (`scene_id=0`).
- R6-S1/S2/S3: **Mode B**, scene not recognized (`scene_id=0`).
- No additional initialization failure class was observed.

Performance used the established deterministic `_invincible` rope-attach workflow, three trials per build:

| Build | Frames | Median |
|---|---|---:|
| 0495 baseline | 795 / 795 / 795 | 13,267.083 ms |
| 0499 candidate | 795 / 795 / 795 | 13,267.083 ms |

Result: deterministic YES; change 0 frames / 0.000 ms. This is an equivalent-route regression check, not a universal CPU-cycle claim.

Audio source/dispatch was not modified. The current nine-song system and standard ROM-family configuration remain in the canonical build.

## Unresolved limitations

- Visual/collision correctness cannot be accepted from static packages, miss counters, or VRAM reads. Hardware review is pending.
- The exact R1-S2 impassable location was not supplied. To separate readiness, collision-side-channel, and segment-transition causes, Tighe need only report the location (or screenshot) and whether the camera also stops scrolling there.
- There is no established deterministic boss-defeat input fixture. The bounded S1-3 initializer proves the boss-room package, and the converted R2 package supplies the independently proven missing next-round content, but the live boss-death → outer-controller → next-scene sequence remains a required hardware observation. No speculative boss progression rewrite was made.
- RG-022 scene-specific palette assets/contract are not present. Round 2 uses retained arcade palette conversion rather than invented or unapproved colors.
- Rounds 3–6 remain deliberately unconverted after classification.

## Files changed

- `apps/rastan-direct/src/fg_tile_cache.s`
- `apps/rastan-direct/src/palette_hooks.s`
- `apps/rastan-direct/src/scene_load.s`
- `tools/translation/compile_pc080sn_genesis.py`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- `tools/translation/verify_build0311_transition_retention.py`
- `tools/mame/run_build0310_epoch_gate.sh`
- `tools/mame/run_subround_functional_verify.sh`
- `tools/mame/scripts/subround_start_probe.lua`

No Palette Composer, audio source, palette-decision registry, gameplay logic, collision bypass, or unrelated concurrent file was changed by the source commit.

## USER MUST VERIFY

On real Genesis hardware, test Build 0499 normal ROM and specifically:

1. `_S1-2`: the entire castle background uses castle art (not small-cave/residual art), Plane A/B remain coherent while moving, the known impassable point is either fixed or report its exact location plus whether camera scrolling stops, and palette discrepancies are identified for later RG-022 authoring.
2. `_S1-3`: the complete boss-room background is present and stable, the original boss fight/gameplay remains intact, defeating the boss advances through the original transition, backgrounds do not vanish, and the next stage/interstitial becomes playable.
3. `_S2-1`: real Round-2 Plane A/B graphics appear rather than blank or residual Round-1 content; scroll, collision, player, enemies, sprites, HUD, and music continue normally.
4. Normal R1-S1: title/READY/gameplay entry, ropes, waterfall/epoch crossings, HUD, death/Continue, and audio still match the accepted behavior.
5. If checking S2-2/S2-3, confirm their shared Round-2 packages also remain coherent; their palettes are not yet RG-022-approved.

## Status

Implementation checkpoint: **COMPLETE**.  
Visual/gameplay acceptance: **PENDING TIGHE**.  
Build 0499 accepted baseline: **NO**.  
STOP: no Rounds 3–6 conversion and no Palette Composer work started.
