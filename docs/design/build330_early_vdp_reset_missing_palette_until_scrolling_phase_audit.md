# Build 330 Early VDP Reset / Missing Palette Until Scrolling Phase Audit

## 1. Executive Summary
The launcher-to-game handoff does clear CRAM to black and does not apply an immediate post-reset palette. However, palette production is reactivated very early in arcade runtime through `0x59AD4` (CLCS capture) plus `_VINT_arcade_mode -> genesistan_palette_commit_asm` (CLCS->CRAM). The long black period is therefore not explained by reset-time CRAM clear alone. The later scrolling/items-looking phase aligns with a state transition that activates heavy `0x5A4DE` block-write traffic (patched to `genesistan_bulk_tilemap_commit`), which matches the rolling/corrupted presentation symptom.

## 2. Launcher-Side VDP Reset / Init Sequence
Launcher-to-game sequence (in order):

1. `request_start_rastan()` in `apps/rastan/src/main.c`
2. `genesistan_init_workram_direct(...)`
3. `restore_launcher_vdp_state()` (launcher palettes/fonts/sprites)
4. `VDP_clearPlane(BG_A/B, TRUE)` + `genesistan_sync_title_vdp_layout()`
5. `force_clean_vram_init()`
   - clears VRAM
   - clears CRAM to `0x0000`
   - clears VSRAM
   - resets key VDP registers (planes/window/sat/scroll baseline)
6. `genesistan_preload_scene_tiles(GENESISTAN_SCENE_TITLE)`
7. `genesistan_run_title_init_sequence()`
8. `arcade_vblank_active = 1` (arcade VBlank ownership begins)

CRAM behavior in this sequence:
- `force_clean_vram_init()` explicitly writes black to all 64 CRAM words.
- No replacement palette is applied immediately after that reset function.

## 3. Is There a Usable Palette Immediately After Reset
Immediate post-reset usable palette applied: **NO**.

`force_clean_vram_init()` ends with CRAM fully black and no immediate follow-up CRAM load in the same handoff sequence. Palette only resumes through arcade VBlank path after ownership flips to `_VINT_arcade_mode`.

## 4. First Runtime Path That Produces Visible CRAM
First visible palette source identified: **YES**.

Earliest palette-producing runtime chain:
1. Arcade code calls `0x59AD4` (palette converter writing to `0x200000`, remapped to `genesistan_palette_clcs` by spec).
2. `_VINT_arcade_mode` in `apps/rastan/src/boot/sega.s` runs each frame and calls `genesistan_palette_commit_asm`.
3. `genesistan_palette_commit_asm` in `apps/rastan/src/startup_trampoline.s` scans CLCS blocks and writes converted values to CRAM.

Earliest concrete callsite in the startup/title flow:
- `0x3AA54 -> jsr 0x5A356 -> jsr 0x59AD4` (see `build/maincpu.disasm.txt`).

Interpretation for timing:
- Reset-time CRAM is black.
- CRAM population can begin once `0x59AD4` has executed and VBlank commit runs.
- This is early runtime, not an SGDK-era pre-handoff palette.

## 5. State Transition Into Scrolling / Items Phase
Scrolling/items phase transition identified: **YES**.

Observed debug state (`M:0000 0001 0002`) maps to:
- `A5@(0)=0` (main state)
- `A5@(2)=1` (sub-state)
- `A5@(4)=2` (inner step)

Transition into the later phase:
- At `0x3AB00` path, code executes:
  - `movew #2,%a5@(0)`
  - `clrw %a5@(2)`
  - `clrw %a5@(4)`
- This is a high-level state transition to state `2`.
- The immediate state-2 handler at `0x3AB58` calls `0x5A474`.

## 6. Rendering Path That Becomes Active There
Primary rendering path active there: **`genesistan_bulk_tilemap_commit`**.

Why:
- `0x5A474` drives table-based content setup and calls routines that funnel through `0x5A4DE`.
- `0x5A4DE` is opcode-replaced in `specs/startup_title_remap.json` to jump to `genesistan_bulk_tilemap_commit`.
- The previously-audited crash site (`move.w (%a0)+,%d4`) is inside this same function, linking this phase to the known unstable presentation path.

## 7. Is Rolling Output Best Explained as Broken Scroll/Text Presentation
**YES.**

The rolling/corrupted-looking output is most consistent with real later-phase presentation data being pushed through a partially translated block-write/presentation path (`0x5A4DE` replacement path), not a simple "nothing is rendering" condition.

## 8. Is a Test Palette After Reset a Valid Next Proof
**YES.**

What it proves:
- Whether the early black period is caused by having no usable CRAM immediately after reset.
- Whether forcing non-black CRAM right after `force_clean_vram_init()` changes early visibility.

What it does not prove:
- Correctness of later scrolling/items rendering.
- Correctness/safety of the `genesistan_bulk_tilemap_commit` path.
- Root cause of rolling/corruption once later phase starts.

## 9. Single Root Cause
**EARLY_BLACK_SCREEN_AND_LATER_ROLLING_SHARE_ONE_UNTRANSLATED_PRESENTATION_PATH**

## 10. Single Next Implementation Target
**force known test palette immediately after VDP reset**

## 11. Final Verdict
The reset path does leave CRAM black with no immediate palette reapply, but that is only the opening condition. Palette flow is reintroduced by arcade runtime (`0x59AD4` -> CLCS -> `genesistan_palette_commit_asm`). The later scrolling/items transition is where the heavy `0x5A4DE` replacement path dominates output, and that same path is already implicated in unstable/rolling behavior.
