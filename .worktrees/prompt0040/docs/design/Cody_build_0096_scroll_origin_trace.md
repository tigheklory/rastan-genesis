# Cody - Build 0096 Scroll / Display-Origin Runtime Trace

**Date:** 2026-06-24
**Type:** Bounded runtime trace / documentation only
**Build:** 0096, `rastan-direct`
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0096.bin`
**Scope:** Read-only runtime trace of shared scroll/display-origin hypothesis after Andy's Build 0096 title coordinate-origin audit. No source/spec/tool/Makefile/ROM/invariant changes. No build. No implementation. No bookmark cycle.

## Phase 0

Classification: **EXTENDING** (OPEN-001). Relevant priors loaded: `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, `docs/design/Andy_build_0096_title_coordinate_origin_audit.md`, and `docs/design/Cody_build_0096_title_bg_blockcopy_staging_impl.md`.

Architecture compliance: **CONFIRMED**. This task treats the arcade program as authoritative and the Genesis side as helper/hardware-service only. The trace is diagnostic-only; it does not patch, seed, bypass, or modify execution.

Contradiction detected: **NO**. The trace narrows Andy's shared-origin hypothesis by measuring the raw scroll words and Genesis commit behavior; it does not establish a new fix.

## Evidence Artifacts

- Genesis Build 0096 trace: `states/traces/build_0096_scroll_origin_trace_20260624_162530/`
- Original arcade trace: `states/traces/original_arcade_scroll_origin_trace_20260624_162530/`
- Genesis command file: `states/traces/build_0096_scroll_origin_trace_20260624_162530/mame_build_0096_scroll_origin.cmd`
- Genesis raw trace: `states/traces/build_0096_scroll_origin_trace_20260624_162530/native_debug_trace.log`
- Genesis staging dumps at `0x3AC88`:
  - `states/traces/build_0096_scroll_origin_trace_20260624_162530/fg_at_3ac88.txt`
  - `states/traces/build_0096_scroll_origin_trace_20260624_162530/bg_at_3ac88.txt`
- Original arcade command file: `states/traces/original_arcade_scroll_origin_trace_20260624_162530/mame_original_arcade_scroll_origin.cmd`
- Original arcade raw trace: `states/traces/original_arcade_scroll_origin_trace_20260624_162530/native_debug_trace.log`
- Reduced summary JSON: `states/traces/build_0096_scroll_origin_trace_20260624_162530/scroll_origin_reduced_summary.json`
- Reduced summary note: `states/traces/build_0096_scroll_origin_trace_20260624_162530/scroll_origin_reduced_analysis.md`

The Genesis run completed without a crash in the measured window. The original arcade trace reached the title kick boundary and exited from the debugger script.

## Address Mapping Discipline

Arcade-to-Genesis code addresses used here were checked against `build/rastan-direct/address_map.json`; arithmetic offset was not used as proof.

| Arcade address | Genesis address | Map segment | Context |
|---|---|---:|---|
| `0x03AA88` | `0x03AC88` | 27 | title kick / boundary sample |
| `0x03AA54` | `0x03AC54` | 27 | title handler context |
| `0x03ABBA` | `0x03ADBA` | 32 | redirected scroll clear site |
| `0x03ABC0` | `0x03ADC0` | 33 | redirected scroll clear site |
| `0x03B098` | `0x03B298` | 95 | redirected Y-scroll clear site; watchpoint post-PC `0x03B2A0` |
| `0x03B09E` | `0x03B29E` | 96 | redirected X-scroll clear site; watchpoint post-PC `0x03B2A6` |
| `0x055AB4` | `0x055CB4` | 156 | scroll helper replacement entry; not reached in the bounded arcade title sample |
| `0x05A38E` | `0x05A58E` | 171 | title BG block-copy caller context |
| `0x05A4DE` | `0x05A6DE` | 172 | title BG block-copy replacement |

## Genesis Build 0096 Measurements

### Event Counts

| Event | Count |
|---|---:|
| `VDP_COMMIT_SCROLL_ENTRY` | 546 |
| `HSCROLL_FG_WRITE` | 546 |
| `HSCROLL_BG_WRITE` | 546 |
| `VSRAM_FG_WRITE` | 546 |
| `VSRAM_BG_WRITE` | 546 |
| `VBLANK_HANDOFF` | 546 |
| `STAGED_SCROLL_WRITE` | 16 |
| `TITLE_3AC88` | 1 |
| `TITLE_STATE4_TO_2` | 1 |

### Staged Scroll Values

All observed `vdp_commit_scroll` entries had:

| Value | Observed |
|---|---:|
| `staged_scroll_x_bg` (`0xFF4012`) | `0x0000` |
| `staged_scroll_x_fg` (`0xFF4014`) | `0x0000` |
| `staged_scroll_y_bg` (`0xFF4016`) | `0x0000` |
| `staged_scroll_y_fg` (`0xFF4018`) | `0x0000` |

The title boundary sample at `0x3AC88` also had all four staged scroll words equal to `0x0000`:

```text
EVENT TITLE_3AC88 cyc=6004738 pc=03AC8A sr=2700 s0=0000 s2=0001 s4=0000 xbg=0000 xfg=0000 ybg=0000 yfg=0000 bg_dirty=007FFFF8 fg_dirty=15800000
```

The state-4-to-2 sample at `0x3ACF8` likewise had all four scroll words equal to zero:

```text
EVENT TITLE_STATE4_TO_2 cyc=34056692 pc=03ACFA sr=2700 s0=0000 s2=0001 s4_before=0001 xbg=0000 xfg=0000 ybg=0000 yfg=0000
```

### VDP Scroll Commit Behavior

`vdp_commit_scroll` ran repeatedly and wrote zero to all four Genesis scroll outputs every observed commit:

| Commit event | Count | Written value |
|---|---:|---|
| HScroll FG / Plane A | 546 | `0x0000` |
| HScroll BG / Plane B | 546 | `0x0000` |
| VSRAM FG / Plane A | 546 | `0x0000` |
| VSRAM BG / Plane B | 546 | `0x0000` |

Representative first commit:

```text
EVENT VDP_COMMIT_SCROLL_ENTRY cyc=4493202 pc=0701F2 sr=2614 s0=0000 s2=0000 s4=0000 xbg=0000 xfg=0000 ybg=0000 yfg=0000
EVENT HSCROLL_FG_WRITE cyc=4493380 pc=0701FC sr=2610 value=0000 xbg=0000 xfg=0000
EVENT HSCROLL_BG_WRITE cyc=4493408 pc=070206 sr=2614 value=0000 xbg=0000 xfg=0000
EVENT VSRAM_FG_WRITE cyc=4493464 pc=07021A sr=2610 value=0000 ybg=0000 yfg=0000
EVENT VSRAM_BG_WRITE cyc=4493492 pc=070224 sr=2614 value=0000 ybg=0000 yfg=0000
```

### Staged Scroll Writers

Only zero writes to staged scroll were observed:

| Writer PC | Address | Value | Count | Interpretation |
|---|---|---:|---:|---|
| `0x00031A` | `0xFF4012` | `0x0000` | 1 | boot/init clear |
| `0x000320` | `0xFF4014` | `0x0000` | 1 | boot/init clear |
| `0x000326` | `0xFF4016` | `0x0000` | 1 | boot/init clear |
| `0x00032C` | `0xFF4018` | `0x0000` | 1 | boot/init clear |
| `0x03B2A0` | `0xFF4016` | `0x0000` | 3 | redirected arcade Y-scroll clear, post-PC |
| `0x03B2A0` | `0xFF4018` | `0x0000` | 3 | redirected arcade Y-scroll clear, post-PC |
| `0x03B2A6` | `0xFF4012` | `0x0000` | 3 | redirected arcade X-scroll clear, post-PC |
| `0x03B2A6` | `0xFF4014` | `0x0000` | 3 | redirected arcade X-scroll clear, post-PC |

No nonzero staged-scroll write was observed.

## Original Arcade Runtime Measurements

At original arcade title boundary `0x03AA88`, the runtime A5 scroll/window fields were all zero:

```text
EVENT ARCADE_TITLE_03AA88 cyc=1802895 pc=03AA8A sr=2700 a5=0010C000 s0=0000 s2=0001 s4=0000 cnt=0000 bg_x_10ec=0000 bg_y_10ee=0000 fg_x_10ae=0000 fg_y_10b0=0000
```

The original arcade also wrote zero to PC080SN scroll hardware before the title boundary:

```text
EVENT ARCADE_PC080SN_YSCROLL_WRITE cyc=1657094 pc=03B0A0 addr=00C20002 size=16 data=00000000 sr=2704 a5=0010C000 bg_y_10ee=0000 fg_y_10b0=0000
EVENT ARCADE_PC080SN_YSCROLL_WRITE cyc=1657094 pc=03B0A0 addr=00C20000 size=16 data=00000000 sr=2704 a5=0010C000 bg_y_10ee=0000 fg_y_10b0=0000
EVENT ARCADE_PC080SN_XSCROLL_WRITE cyc=1657122 pc=03B0A6 addr=00C40002 size=16 data=00000000 sr=2704 a5=0010C000 bg_x_10ec=0000 fg_x_10ae=0000
EVENT ARCADE_PC080SN_XSCROLL_WRITE cyc=1657122 pc=03B0A6 addr=00C40000 size=16 data=00000000 sr=2704 a5=0010C000 bg_x_10ec=0000 fg_x_10ae=0000
```

The bounded arcade trace did **not** hit the `0x055AB4` scroll helper before exiting at title boundary. That helper is still mapped in Build 0096, but this trace does not prove its runtime values for the sampled title page.

## Staging Row / Viewport Evidence

At Genesis `0x3AC88`, the BG title block-copy region is staged at rows `3..22`, cols `10..37`:

- BG nonzero words: `560`
- BG nonzero rows: each row `3..22`, `28` words per row, first col `10`, last col `37`

FG staging at `0x3AC88` contains these nonzero rows:

| FG row | Nonzero words | First col | Last col | Notes |
|---:|---:|---:|---:|---|
| 23 | 7 | 18 | 26 | descriptor idx 18 symbol row |
| 24 | 8 | 18 | 26 | descriptor idx 19 symbol row |
| 26 | 22 | 9 | 34 | `@ TAITO AMERICA CORP. 1987` |
| 28 | 17 | 12 | 30 | `ALL RIGHTS RESERVED` |
| 30 | 8 | 33 | 41 | `CREDIT   ` |

Descriptor-derived row references from Build 0096:

| Descriptor idx | Text | Dest | Row | Col |
|---:|---|---|---:|---:|
| 2 | `CREDIT   ` | `0x00C09E84` | 30 | 33 |
| 12 | `@ TAITO AMERICA CORP. 1987` | `0x00C09A24` | 26 | 9 |
| 17 | `INSERT COIN(S)` | `0x00C08840` | 8 | 16 |
| 18 | symbol row | `0x00C09744` | 23 | 17 |
| 19 | symbol row | `0x00C09844` | 24 | 17 |
| 32 | `ALL RIGHTS RESERVED` | `0x00C09C30` | 28 | 12 |
| 65 | `OTHERWISE I COULD NOT` | `0x00C0914C` | 17 | 19 |
| 70 | `DAYS FULL OF ADVENTURE.` | `0x00C09B4C` | 27 | 19 |

Interpretation:

- `ALL RIGHTS RESERVED` at row 28 and `CREDIT` at row 30 are outside a 28-row / 224-pixel visible window if rows `0..27` are displayed. Their invisibility can be explained by true 320x240-to-320x224 clipping without requiring a measured nonzero scroll origin.
- A vertical display-origin policy could still compound clipping, but this trace measured raw arcade and Genesis scroll words as zero.
- The top `1UP / HIGH SCORE / 2UP` HUD line was not present in the captured title FG staging rows `0..2`; this trace does not prove it is shifted above the boundary. It is more safely classified as not staged in this captured title-page snapshot or produced by a separate path.
- The large red TAITO logo row is not semantically isolated by this trace. Rows 23/24 contain symbol descriptors, but treating those as the red logo would be inference, not proof.

## Answers to Required Questions

### 1. Genesis staged scroll values in the steady title window

**Proven:** `staged_scroll_x_bg`, `staged_scroll_y_bg`, `staged_scroll_x_fg`, and `staged_scroll_y_fg` are all `0x0000` at `0x3AC88`, at `0x3ACF8`, and at every observed scroll commit in the trace.

### 2. Does `vdp_commit_scroll` run, and what does it write?

**Proven:** Yes. `vdp_commit_scroll` ran `546` times. It wrote `0x0000` for Plane A HScroll, Plane B HScroll, Plane A VSRAM, and Plane B VSRAM on every observed commit.

### 3. Original arcade matching title scroll/window values

**Proven:** At original arcade `0x03AA88`, the sampled A5 scroll/window fields were all `0x0000`:

- BG X `a5+0x10EC`: `0x0000`
- BG Y `a5+0x10EE`: `0x0000`
- FG X `a5+0x10AE`: `0x0000`
- FG Y `a5+0x10B0`: `0x0000`

### 4. Original arcade `0xC20000` / `0xC40000` writes and Build 0096 handling

**Proven:** The original arcade runtime wrote zero to `0xC20000/0xC20002` and `0xC40000/0xC40002` before title boundary, from post-instruction PCs `0x03B0A0` and `0x03B0A6`.

**Proven by spec/map:** The corresponding Build 0096 sites are redirected through the existing remap to staged scroll variables (`0x03B098 -> 0x03B298`, `0x03B09E -> 0x03B29E`). The Genesis trace observed the corresponding post-PCs `0x03B2A0` and `0x03B2A6` writing zero to the staged scroll words.

**Bounded gap:** The `0x055AB4` scroll helper is mapped to Genesis `0x055CB4`, but it did not fire in this bounded arcade title-boundary sample. No nonzero scroll helper behavior was observed.

### 5. X/Y separate

**Proven:** The measured raw scroll values are zero for both X and Y on both planes in the sampled title state.

**Inference:** The user-visible shared +1 col / +1 row symptom is therefore not explained by a missing nonzero raw A5 scroll word in this trace. A vertical `+8` display policy may still exist as a fixed viewport/display-origin policy rather than as a raw scroll value; horizontal shift remains unresolved by raw scroll evidence.

### 6. Exact measured offset between arcade intended and Build 0096

**Proven in scroll-word space:**

| Plane | X delta | Y delta |
|---|---:|---:|
| Layer A / Plane A | `0` | `0` |
| Layer B / Plane B | `0` | `0` |

**Not proven in visual-pixel space:** This trace did not capture a visual overlay or VRAM plane comparison against arcade output. It cannot independently measure the on-screen +1/+1 pixel/tile offset; it only rules out a missing nonzero raw scroll word in the measured title state.

### 7. Row indices for title elements

**Proven from staging/descriptor data:**

- BG title art block: rows `3..22`, cols `10..37`.
- `@ TAITO AMERICA CORP. 1987`: row `26`, col `9`.
- `ALL RIGHTS RESERVED`: row `28`, col `12`.
- `CREDIT`: row `30`, col `33`.
- Story text examples after the title transition: rows `13`, `15`, `17`, `19`, `21`, `23`, `25`, `27`.

**Not proven:** top `1UP / HIGH SCORE / 2UP` and large red TAITO logo row/col placement from this trace. They were not safely isolated as current staged rows in the captured title boundary dump.

### 8. ALL RIGHTS / CREDIT classification

**Proven:** `ALL RIGHTS RESERVED` is staged on row `28`, and `CREDIT` is staged on row `30`.

**Inference:** With a 224-pixel / 28-row visible Genesis display, rows `28` and `30` are clipped even when scroll is zero. Therefore their absence is primarily consistent with 320x240-to-320x224 clipping, not with the measured raw scroll values. A fixed display-origin policy could compound this, but it is not required to explain those two rows being absent.

### 9. SCORE / 1UP / 2UP classification

**Proven:** The top HUD labels were not present in rows `0..2` of the captured FG staging dump at `0x3AC88`.

**Inference:** This trace does not support classifying them as merely shifted above the boundary. They remain a separate staging/producer-path question.

## Classification

### Result: Raw scroll-word hypothesis not supported by this trace

The Genesis scroll commit path is active and writes the staged values every observed commit. The staged values are zero. The original arcade title boundary sampled here also has zero raw scroll/window values and zero scroll hardware writes. Therefore, the measured evidence does **not** support a fix that simply wires in a missing nonzero scroll word from the sampled A5 fields.

### Remaining likely class: fixed viewport/display-origin policy, not proven enough to patch

The shared Layer A / Layer B visual shift reported by Andy and Tighe remains a real visual symptom, but this trace says it is not caused by a nonzero raw scroll word missing from Build 0096 in the measured title state. The remaining plausible class is a fixed viewport/display-origin policy or visible-window policy, potentially including the known 240-to-224 crop and/or a fixed PC080SN-to-Genesis origin convention.

Implementation is **not safely placeable from this trace alone**. A follow-up visual-correlated VRAM/plane capture is needed before applying any origin correction. That follow-up should compare arcade runtime title output and Build 0096 VRAM/Plane A/B cell positions at the same visible frame, then decide whether the correction belongs in plane base, scroll commit bias, viewport crop policy, or producer staging origin.

## Recommended Next Step

Do not patch `staged_scroll_*` values based on this trace.

Recommended next diagnostic, if Claude/Tighe want to continue this thread: a video/VRAM-correlated origin trace that captures, at the same title frame, the arcade PC080SN visible tilemap window and Build 0096 Plane A/B VRAM nametable output. The goal should be to measure the visual cell delta directly rather than infer it from scroll words. If that proves a fixed +1/+1 viewport convention, then the implementation target can be chosen deliberately.

## Non-Actions

- Source changes: NO
- Spec changes: NO
- Tool changes: NO
- Makefile changes: NO
- ROM changes: NO
- Build run: NO
- Bookmark cycle: NO
- Runtime instrumentation ROM: NO
- Crash/OPEN-015 work: NO
- Start/C/A work: NO

## OPEN / CLOSED Issues Impact

- OPEN-001: touched; active. This trace narrows the shared-origin hypothesis but does not close the graphics issue.
- OPEN-016: context only.
- OPEN-015: not touched.
- New issues opened: NONE.
- Issues closed: NONE.

## KNOWN_FINDINGS Impact

Option A - no `KNOWN_FINDINGS.md` update. The trace does not establish a durable fix mechanism; it rules out one candidate explanation in raw scroll-word space and points to a follow-up visual-origin measurement.

## STOP

STOP triggered: **NO** for the diagnostic task. The measurement completed and is documented.

Implementation safety: **NO**. A fix is not safely placeable yet because the exact visual-origin correction is not proven by this trace.

---

## CORRECTION - User Overlay Supersedes Rough +1/+1 Wording

**Date:** 2026-06-24  
**Correction type:** Documentation correction only.

Tighe later provided authoritative user evidence for Build 0096 display mode and placement:

- Live Exodus VDP register 12 / Mode Set 4 = `0x81`, RS1 set, confirming H40 / `320x224`.
- The prior Cody `256x224` native-MAME AVI size is classified as a capture-path artifact, not ROM display mode.
- User addition-blend overlay measures the real placement offset as `+16 px` X (`+2 cols`) and `+8 px` Y (`+1 row`) versus arcade.

This supersedes this trace's rough references to a `+1/+1` visual symptom. The trace's raw-scroll conclusion remains valid: it measured zero arcade and Genesis title-state scroll words, so the corrected `+2/+1` placement bug is still not explained by a missing nonzero raw scroll word. OPEN-001 remains open.
