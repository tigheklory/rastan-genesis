# Cody - Build 0356 Direct Palette Emit Performance

## Classification and baseline

- Task classification: **EXTENDING / ARCHITECTURE LANDING / PERFORMANCE**.
- Diagnostic timing baseline: Build 0354.
- Ownership-only comparison: Build 0355.
- Direct-palette result: Build 0356.
- Architecture rule: Python and the Palette Editing Tool decide static mapping offline; native 68000 code consumes that decision directly at sprite emission.

No prior arcade-semantic finding was contradicted. For this task, the explicit authority was the current Tighe-authored Palette Editing Tool arrangement. Historical values in `specs/palette_decisions.json` were documentation context and did not override that current packing. The registry was not edited, and its later reconciliation remains separate work.

## Palette authority used

Authoritative current input:

- `analysis/graphics_optimizer/editor_policy/Test.json`
- SHA-256: `deb696452d7456b323fd4cadfa982a40a57ccf7eb5997f9e750c511f0a82df0c`

The build-owned immutable input is:

- `build/rastan-direct/build0314/Test.snapshot.json`
- SHA-256: `deb696452d7456b323fd4cadfa982a40a57ccf7eb5997f9e750c511f0a82df0c`

The two artifacts are byte-identical. The saved profile's `usage_palette_mappings` authors these current R1/P1 effective-bank mappings:

| Effective bank | Genesis palette line |
|---:|---:|
| `0x32` | 0 |
| `0x33` | 0 |
| `0x34` | 0 |
| `0x35` | 1 |
| `0x36` | 1 |
| `0x3A` | 1 |
| `0x3E` | 0 |

Unknown future sprite identities were not assigned invented mappings. For inputs not authored by the current Tool profile, generation retains the current renderer's route/special/fallback result, making the performance landing behavior-complete without claiming new palette semantics.

## Retired transitional path

Build 0354/0355 performed this work after emission:

1. Store each emitted entry's palette nibble in `pc090oj_sat_nibble`.
2. Store the semantic HUD force in `pc090oj_sat_force_line`.
3. Iterate every emitted SAT entry in `.Lnative_pal_fixup`.
4. Reconstruct the effective bank from the nibble and dynamic colbank.
5. Call `.Lnative_palsel`, which could invoke the linear `palette_route_lookup` scan.
6. Read-modify-write SAT word 2 with the chosen palette line.

Build 0356 removes the normal-gameplay route search and complete later SAT palette pass. It also removes both 80-byte metadata arrays and `.Lnative_pal_fixup`.

## Direct emit architecture

`tools/translation/gen_pc090oj_palsel_lut.py` generates `apps/rastan-direct/out/pc090oj_palsel_lut.inc` as four scene rows of 128 one-byte entries:

- Scenes: 4
- Entries per scene: 128
- Total table size: 512 bytes
- Lookup complexity: `O(1)`

`pc090oj_select_palette_map` selects a row when `load_scene_tiles` commits `genesistan_current_scene_id`. The selected row address is stored in the four-byte `current_sprite_palette_map` pointer. Scene selection is therefore outside the emitted-piece hot path.

At emission, the native 68000 code:

1. Retains dynamic priority, vertical flip, horizontal flip, and resident pattern index in SAT word 2.
2. Forms the existing seven-bit effective-bank key from the semantic low nibble and `pc090oj_sprite_ctrl_shadow` colbank contribution.
3. Reads the palette line directly from `current_sprite_palette_map[effective_bank]`.
4. ORs the line into bits 14:13 of the final SAT word 2 before storing it.

HUD mode 2 keeps its established semantic bit-15 tag and applies line 3 directly during emission. It no longer transports that decision through a SAT-slot metadata array.

## Machine equivalence

Machine-readable proof:

- `build/rastan-direct/pc090oj_direct_palette_equivalence.json`
- Result: `PASS`
- Direct mapping cases: 512
- Mapping mismatches: 0
- Hand-anchor failures: 0
- Exhaustive SAT word-2 cases: 16,777,216
- SAT word-2 mismatches: 0

The exhaustive domain covers palette line, priority, vertical flip, horizontal flip, pattern index, and HUD-force behavior. Thus the generated path preserves all currently supported mapping results and every dynamic SAT word-2 field.

Static xref inspection after linking confirms that normal sprite publication no longer references `.Lnative_pal_fixup`, `palette_route_lookup`, `pc090oj_sat_nibble`, or `pc090oj_sat_force_line`.

## Physical-beam timing method

The same corrected MAME physical-beam method used for Build 0354 was reused. The logger records a monotonic tuple of external frame, physical beam Y, and beam X at section boundaries. Elapsed dots are computed across real frame boundaries and converted using 488 dots per scanline. It does not use the invalid 8-bit V-counter `% 262` reconstruction.

Candidate-ROM addresses and shifted WRAM symbols are supplied as environment overrides to `tools/mame/scripts/build0354_vblank_independent_audit.lua`; Build 0354 remains that script's default profile. The existing reducer was rerun without changing its accounting model.

Evidence:

- Build 0355 trace: `states/traces/build0355_vblank_physical_beam_20260912/`
- Build 0356 trace: `states/traces/build0356_vblank_physical_beam_20260912/`
- Comparison: `states/traces/build0356_vblank_physical_beam_20260912/build0354_0355_0356_performance_comparison.json`

Each candidate trace sampled 1,800 external frames and completed with exit status 0. The Build 0355 run observed 1,168 publications, including 920 gameplay publications. Build 0356 observed 1,257 publications, including 1,009 gameplay publications. The differing counts show that gameplay advanced differently in equal external time; they are not interpreted as a publisher-frequency regression.

Publisher entry during active display remained observable:

| Build | All publication starts | Gameplay publication starts |
|---|---:|---:|
| 0355 | 815/1,168 = 69.78% | 807/920 = 87.72% |
| 0356 | 877/1,257 = 69.77% | 870/1,009 = 86.22% |

## Representative measurements

All durations below are physical scanlines. `DMA` is actual pattern-DMA entry count. The stationary, horizontal, and sprite-heavy reductions use matched emitted-count/DMA workloads. The vertical representative differs by one emitted sprite. The worst-observed rows are not identical workloads; Build 0356's row includes 12 pattern DMAs versus 2 in Build 0354, so its reduction is conservative but not a controlled exact-workload comparison.

| Workload | Build | Emitted | DMA | Total | Plane B | Plane A | Sprites | Sprite tile | Palette pass | SAT DMA |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Stationary | 0354 | 28 | 0 | 54.451 | 0.094 | 1.439 | 50.303 | 0.154 | 48.246 | 1.004 |
| Stationary | 0355 | 28 | 0 | 54.451 | 0.094 | 1.422 | 50.320 | 0.154 | 48.232 | 1.006 |
| Stationary | 0356 | 28 | 0 | 6.201 | 0.092 | 1.422 | 2.035 | 0.170 | 0.000 | 1.004 |
| Horizontal | 0354 | 46 | 0 | 93.109 | 0.094 | 1.422 | 88.959 | 0.154 | 86.867 | 1.025 |
| Horizontal | 0355 | 46 | 0 | 93.109 | 0.094 | 1.422 | 88.959 | 0.154 | 86.867 | 1.025 |
| Horizontal | 0356 | 46 | 0 | 6.201 | 0.092 | 1.422 | 2.035 | 0.170 | 0.000 | 1.004 |
| Vertical/jump | 0354 | 19 | 0 | 46.932 | 0.094 | 13.162 | 31.059 | 0.154 | 28.949 | 1.004 |
| Vertical/jump | 0356 | 20 | 0 | 17.924 | 0.094 | 13.162 | 2.037 | 0.152 | 0.000 | 1.006 |
| Sprite-heavy | 0354 | 51 | 10 | 118.289 | 0.094 | 1.422 | 114.139 | 16.135 | 96.066 | 1.025 |
| Sprite-heavy | 0356 | 51 | 10 | 22.203 | 0.092 | 1.422 | 18.039 | 16.152 | 0.000 | 1.025 |
| Worst observed | 0354 | 46 | 2 | 134.033 | 37.852 | 1.420 | 92.125 | 3.361 | 86.846 | 1.004 |
| Worst observed | 0356 | 49 | 12 | 63.115 | 37.836 | 1.420 | 21.207 | 19.340 | 0.000 | 1.004 |

Build 0355 matches Build 0354 at the exact 28/0 and 46/0 workloads. This isolates the Stage-2 speed change from the Stage-1 WRAM repair.

## Measured reductions

| Workload | Total reduction | Total reduction | Sprite reduction | Sprite reduction |
|---|---:|---:|---:|---:|
| Stationary, 28/0 exact | 23,546 dots / 48.250 lines | 88.61% | 23,555 dots / 48.268 lines | 95.95% |
| Horizontal, 46/0 exact | 42,411 dots / 86.908 lines | 93.34% | 42,419 dots / 86.924 lines | 97.71% |
| Vertical/jump, representative | 14,156 dots / 29.008 lines | 61.81% | 14,163 dots / 29.023 lines | 93.44% |
| Sprite-heavy, 51/10 exact | 46,890 dots / 96.086 lines | 81.23% | 46,897 dots / 96.100 lines | 84.20% |
| Worst observed, non-identical | 34,608 dots / 70.918 lines | 52.91% | 34,608 dots / 70.918 lines | 76.98% |

The measured palette section falls from 48.246, 86.867, 28.949, 96.066, and 86.846 scanlines in the selected Build 0354 rows to zero in Build 0356. Remaining sprite cost is principally bounded pattern DMA plus the approximately one-scanline fixed SAT DMA. The direct lookup cost is folded into emission and is below the old logger's removed palette-section boundary; this evidence does not claim a separately isolated sub-scanline lookup duration.

## Build 0356

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0356.bin`
- SHA-256: `94afa3811b675e43a8e77b12e84b815cca4096617ffc3dd0be0951427fb8b760`
- Size: 1,666,744 bytes
- Counter after publication: 356
- Canonical result: `GATE_PASS`
- Mandatory Genesis NTSC MAME smoke: gameplay entry passed; 564 external frames completed without a fatal or unique unmapped-memory error.
- WRAM ownership invariant: still `PASS`.
- Existing seven-epoch Phase-1 evaluation warning: unchanged and outside this performance landing.

Automated equivalence proves preservation of the current mapping and SAT composition. Visual acceptance for Rastan, sword/player auxiliary, Lizardman, bats, HUD, item drops, and effects remains **USER MUST VERIFY** because a smoke trace cannot replace human color comparison.

## Unchanged systems

- Build 0353 best visual baseline artifact: preserved.
- Arcade frame authority: unchanged.
- Plane A and Plane B producers/residency: unchanged.
- Sprite pattern residency/allocation: unchanged.
- `D00462`: unchanged.
- CRAM animation semantics: unchanged.
- Gameplay logic, scrolling, collision, input, and audio: unchanged.
- Palette Editing Tool expansion to all sprites and Layer A: deferred.
- Layer B dedicated arcade-derived palette line: deferred.

## Conclusion and next boundary

The speed problem is materially improved. At exact no-pattern-DMA workloads, sprite publication fell by 95.95% to 97.71%; at the exact 51-sprite/10-DMA workload it fell by 84.20%. The runtime semantic route scan and second emitted-SAT palette pass are gone.

The remaining measured sprite bottleneck is pattern DMA when the worklist is populated, followed by the fixed SAT DMA. Outside sprites, a heavy Plane B publication remains approximately 37.8 scanlines and a vertical Plane A publication approximately 13.2 scanlines.

With the direct-bank architecture proven, expanding the Palette Editing Tool to all sprites and Plane A now has a viable runtime consumer. That expansion and Layer B palette work remain separate future tasks rather than scope added to this performance landing.

