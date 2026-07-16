# Cody - Build 0173 PC080SN FG Palette / Attribute Correction Candidate

**Date:** 2026-07-15  
**Type:** Implementation-first, bounded build + runtime evidence  
**Baseline:** Build 0172 `dist/rastan-direct/rastan_direct_video_test_build_0172.bin`  
**Baseline SHA256:** `c2ed780af704737ed813704a414a7609ed2e7f4629b243108c8934273da15ac9`  
**Produced build:** Build 0173 `dist/rastan-direct/rastan_direct_video_test_build_0173.bin`  
**Produced SHA256:** `1f8711ac3132481f4e953b2965e09480e3cdb4b1d85d512d2a43b9ed1368d410`  
**Scope:** Gameplay PC080SN FG palette/attribute correction only. No collision, input, player-state, PC090OJ, VBlank budget, slowdown, D00298, continue/game-over, or tile-source change.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-038 (long PC080SN row-depth / Build 0172 FG parity), KF-043 (bank-51/line-3 palette ownership), KF-010 (FG -> Plane A), OPEN-017 (current gameplay/hardware visual bring-up), OPEN-001/OPEN-003 context only. Rediscovery-hazard findings touched: KF-038 and KF-043. No contradiction detected: KF-043 remains true for bank-51/source-buffer ownership and sprites; this task refines the gameplay FG_SRC terrain line selection so it does not incorrectly reuse that green line.

Architecture compliance: **CONFIRMED**. The arcade code remains the program; the change is a helper-side staging attribute correction inside the existing gameplay FG_SRC replay and still flows through `staged_fg_tall_buffer` -> rolling projection -> `staged_fg_buffer` -> VBlank commit -> Plane A.

## User Visual Observations Recorded

Tighe's Build 0172 visual correction is controlling for this task:

- Build 0172 loads/projects the FG tiles vertically.
- The foreground/floor/terrain tiles are visibly present.
- The tiles appear to be the right foreground/floor/terrain tiles.
- The failure is color: green shades instead of arcade brown/rock/ground shades.
- As the screen scrolls right, the foreground still falls apart visually.
- Rastan is still uncontrollable.
- Rastan can fall down into what appears to be the arcade cave path.
- Slowdown is still present and intentionally deferred.

The user-provided prompt images were used as visual context: Build 0172 shows green repeated foreground where the arcade reference shows brown/rock terrain. The exact local arcade reference image path was not provided as a filesystem file in this task, so the proof below relies on runtime palette/cell evidence plus the prompt's visual comparison.

## Static Path Inspection

`genesistan_stage_fg_src_column` replays the Stage-1 gameplay FG_SRC family from ROM and routes each cell through `genesistan_hook_tilemap_fg_fill_tall`.

Before this task, the helper forced every emitted gameplay FG cell to attr `0x0003`:

```asm
move.l  #FG_PLANE_ATTR_HI, %d1   ; Build 0172 FG_PLANE_ATTR_HI = 0x00030000
move.w  %d0, %d1                 ; D1 = attr<<16 | tile code
bsr     genesistan_hook_tilemap_fg_fill_tall
```

The attr LUT generator maps PC080SN attr key low palette bits directly to Genesis nametable palette bits:

- `attr 0x0002 -> attr_lut[2] = 0x4000` (Genesis palette line 2)
- `attr 0x0003 -> attr_lut[3] = 0x6000` (Genesis palette line 3)

So Build 0172's forced `FG_PLANE_ATTR_HI=0x00030000` necessarily creates `0x6xxx` Plane-A words for nonzero gameplay FG terrain cells.

## Build 0172 Runtime Evidence

Trace: `states/traces/build0173_fg_palette_attr_probe_20260715_191427/`.

The first palette probe in `states/traces/build0173_fg_palette_attr_probe_20260715_191339/` used a stale palette base from an older script and is intentionally discarded; the symbol-correct base is `staged_palette_words = WRAM 0x00FFA0A6`.

At gameplay frames `571`, `820`, `1081`, and `1400`, Build 0172 had stable palette residency and all nonzero gameplay FG cells selected line 3:

```text
pal_nz=15/14/15/15
fg attr lines=0,0,0,2016
tall=0,0,0,4032
PAL2 0000 0642 0644 0644 0646 0644 0868 0668 066A 068C 068E 0AAC 0E00 0AEE 0E80 0CC0
PAL3 08AE 0000 0EEE 08AE 044A 0246 0008 0006 00EE 006E 0080 0060 0888 0666 0040 000E
```

Existing Build 0172 FG sample trace shows representative projected words at frame `1081`:

```text
0x6065, 0x6000, 0x603F, 0x6043, 0x604E, 0x6051
```

The low tile-slot bits are nonzero and stable; the high `0x6000` palette bits select line 3. This matches Tighe's visual report: correct-looking terrain shape, wrong green palette family.

## Classification

Classification: **H. Correct brown palette exists in CRAM, but FG selects the green palette line.**

Rationale:

- Not wrong tiles: sampled low tile IDs survive and the user visual correction says the tiles are correct enough to treat as foreground/floor/terrain.
- Not missing CRAM: all four staged palette lines are populated during gameplay.
- Not line-3 CRAM corruption only: Build 0172 deliberately selects line 3 for every gameplay FG terrain cell through the forced attr constant.
- The brown/earth-compatible line 2 palette is resident while the Build 0172 FG cells select line 3.

Scroll-right breakup remains unresolved. It may be a separate FG horizontal source/window issue, FG scroll/projection issue, or VBlank/render timing issue; this task does not prove it is caused by the same palette-line root.

## Fix Applied

File: `apps/rastan-direct/src/tilemap_hooks.s`

Only the gameplay FG forced attribute constant changed:

```asm
.equ FG_PLANE_ATTR_HI, 0x00020000
```

The comment was updated from `attr = 0x0003` to `attr = 0x0002`.

Preserved unchanged:

- `staged_fg_tall_buffer`
- `genesistan_hook_tilemap_fg_fill_tall`
- 16 segments / 64 rows
- rolling FG projection via `vdp_project_fg_tall_if_dirty`
- gameplay FG residual VSRAM Y scroll `& 0x0007`
- non-gameplay 32-row FG path
- Build 0171 BG tall projection

## Build Verification

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

- Build counter: `172 -> 173`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0173.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `1f8711ac3132481f4e953b2965e09480e3cdb4b1d85d512d2a43b9ed1368d410`
- Size: `1,582,224`
- Numbered/rolling comparison: `cmp=0`
- Canonical gate: `GATE_PASS`
- Release trace: `states/traces/rastan_direct_video_test_build_0173_mame_30s_20260715_191533/`

Static ELF disassembly confirms the helper now loads `#0x00020000`:

```asm
00070520 <genesistan_stage_fg_src_column>:
...
70584: 223c 0002 0000  movel #131072,%d1
7058a: 3200            movew %d0,%d1
7059c: 6100 04b4       bsrw 70a52 <genesistan_hook_tilemap_fg_fill_tall>
```

## Build 0173 Runtime Validation

Trace: `states/traces/build0173_fg_palette_attr_validation_20260715_191624/`.

Build 0173 preserved counts but moved gameplay FG cells to line 2:

```text
FRAME 571 first_gameplay ... fg attr lines=0,0,2016,0 tall=0,0,4032,0
FRAME 820 falling        ... fg attr lines=0,0,2016,0 tall=0,0,4032,0
FRAME 1081 grounded      ... fg attr lines=0,0,2016,0 tall=0,0,4032,0
FRAME 1400 right_scroll  ... fg attr lines=0,0,2016,0 tall=0,0,4032,0
```

Trace: `states/traces/build0173_fg64_sample_validation_20260715_191644/`.

Representative frame `1081` samples preserve tile IDs while switching from `0x6xxx` to `0x4xxx`:

| Screen sample | Build 0172 | Build 0173 | Meaning |
|---|---:|---:|---|
| `screen_col=4,row=15` | `0x6065` | `0x4065` | same slot `0x0065`, line 3 -> line 2 |
| `screen_col=16,row=17` | `0x603F` | `0x403F` | same slot `0x003F`, line 3 -> line 2 |
| `screen_col=28,row=18` | `0x6043` | `0x4043` | same slot `0x0043`, line 3 -> line 2 |
| `screen_col=20,row=22` | `0x604E` | `0x404E` | same slot `0x004E`, line 3 -> line 2 |
| `screen_col=20,row=27` | `0x6051` | `0x4051` | same slot `0x0051`, line 3 -> line 2 |

This validates the bounded mechanism: tile identity/projection preserved, palette-line bits corrected.

## No-Regression Scope

Checked / preserved by code shape and runtime counters:

- Build 0172 FG tall backing and projection remain active (`fg_tall_nz=4032`, `fg_nz=2016`).
- Build 0171 BG tall projection code unchanged.
- Non-gameplay FG paths still use the existing 32-row helper and are not routed through this constant.
- Palette line contents are not rewritten by this task.
- PC090OJ/Rastan sprites are not modified.

Not validated here and intentionally deferred:

- Tighe visual/hardware acceptance of Build 0173 colors.
- Scroll-right foreground breakup.
- Remaining black/blank band timing.
- Input/control/crouch/down-held behavior.
- Cave/fall/collision/layout behavior.
- Slowdown/VBlank budget.
- Continue/game-over, D00298, Exodus loop, and suspicious PC090OJ records `132..134`.

## OPEN / KNOWN FINDINGS Impact

Open issues touched: OPEN-017, OPEN-001 context.  
New issues opened: NONE.  
Issues closed: NONE.  
Issues intentionally deferred: control/input, collision/cave/fall, slowdown/VBlank budget, scroll-right breakup, remaining black/blank bands, PC090OJ/READY/header, continue/game-over, D00298, Exodus loop.

KNOWN_FINDINGS impact: **Option B — new KF-045 added.** It records the durable palette-line rediscovery guard: Build 0172's Stage-1 gameplay FG terrain can be tile-correct but color-wrong when forced onto Genesis palette line 3.

## STOP

STOP triggered: **NO**.
