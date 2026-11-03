# Rastan Genesis ROM Variant Audit (Andy, read-only)

**Date:** 2026-10-15 · **Type:** READ-ONLY static investigation. No build, no ROM, no emulator, no
source/config/git change. Only this report + the governance `AGENTS_LOG` entry were written. Evidence
is current working-tree source (note: `apps/rastan-direct/Makefile` is currently modified by Cody's
0428 WIP, but the variant recipes/defines audited here are long-standing — Build 0337/0338/0344/0360
— and are not part of Cody's WIP; conclusions are unaffected). Cody's 0428–0432 work was not touched.

**Evidence tags:** [SRC] = source-confirmed behavior (code present); [INFER] = reasoned from code,
not runtime-verified; [DOC] = stated in Makefile/comments. No runtime functionality is claimed from
static evidence.

## The five variants come from four build defines (release = all off)

`apps/rastan-direct/Makefile:196-226` defines the variant set; `:391` generates
`out/pc090oj_config.inc` with the four `.equ` flags. The `release` target builds the numbered `.bin`
with all flags 0, then recursively builds each suffixed variant as a **postpatch-only copy that
reuses the release's build number** (`:199-214`, `diag-variant`/`score-variant`/`do-variant`/
`cheat-variant`), and `verify-variant-set` (`:219-226`) asserts all five `("" _d _s _do _c)` exist.

## Comparison table

| Variant | Intended purpose [DOC] | Distinguishing config | Implementation (file:line, label) | Expected observation | Source-confirmed behavior / status |
|---|---|---|---|---|---|
| **`.bin`** | Standard numbered release gameplay ROM; owns counter/gates/ledger | all four flags **0** (`Makefile:62,68,71,75`) | normal `dma_publish_frame` path; no diag code assembled | ordinary gameplay | [SRC] release; all `.if` blocks excluded |
| **`_d.bin`** | Diagnostic **CPU-load raster bar** (VBlank publication cost) | `RASTAN_DIAG_CPU_BAR=1` (`Makefile:60-62,200,570-573`) | `vdp_comm.s:185-190` sets CRAM entry 0 = **bright green `0x00E0`** *before* `dma_publish_frame`; `:199-203` restores **black `0x0000`** *after* | backdrop band coloured for the duration of the publication phase; if the green reaches into the active picture, publication overran VBlank | [SRC] implemented. Brackets **only `dma_publish_frame`** (publication), not the whole IRQ6/worker |
| **`_s.bin`** | Diagnostic **numeric overrun metric** shown via the P1 score HUD | `RASTAN_DIAG_SCORE_METRIC=1` (`Makefile:67-68,201,597-600`) | metric compute: `vdp_comm.s:205-...` (read VDP V-counter `0xC00008`, V<0xE0 → overran to line V, keep MAX `diag_servicing_peak`, → 3-digit BCD `diag_score_bcd`); display: `pc090oj_hooks.s:2450-2456` overwrites P1 score `0xFF011E/1F/20` **inside `native_frontend_hud_emit`** | 1UP/score HUD shows a number = worst-case overrun scanlines | [SRC] implemented; **[DOC] "NEVER shipped; corrupts the score"** (`Makefile:67`). Likely non-functional *in gameplay* — see §_s below |
| **`_do.bin`** | **Display-off VBlank publication** variant (Rainbow model); forced-blank during publication | `RASTAN_VBLANK_DISPLAY_OFF=1` (`Makefile:69-71,202,611-626`) | `dma.s:72-78` writes reg1 **display-OFF `0x8134`** before the publication phase; `:92-94` writes **display-ON `0x8174`** after | publication runs under forced blank; an overrun shows as a **black band** in the active picture | [SRC] implemented. **[DOC] "NOT a diagnostic overlay"** (`Makefile:607`) — a real publication-model variant |
| **`_c.bin`** | **P1 six-button MODE rack-advance CHEAT** (opt-in debug navigation) | `RASTAN_MODE_RACK_ADVANCE=1` (`Makefile:72-75,203,214`) | `tilemap_hooks.s:4143-4148` completes the Mega Drive six-button handshake (phases 2/3) and `bsr .Lmode_rack_advance_poll`; consumes P1 **MODE** to advance; also `:4217,:4896` | pressing P1 MODE on a 6-button pad advances the stage/subround | [SRC] implemented. **Purpose CONFIRMED** = rack-advance cheat (was "unconfirmed" in the task) |

## Per-variant detail

### `_d` — CPU-load raster bar (what the green means)
`vdp_comm.s:185-203`. The backdrop (CRAM index 0) is set **bright green `0x00E0` for the entire
publication phase every frame** and black afterward — it is a **timing bracket, not a conditional
overrun detector**. [SRC] The green is invisible while the bracket runs inside VBlank; a green band
**intruding into the active picture means `dma_publish_frame` bled past VBlank into active scanlines**
(a real publication overrun). [INFER on the interpretation] Important scope: it brackets **only the
publication phase**, not the gameplay worker that runs later in IRQ6 — so `_d` visualizes
*publication* cost, not total frame/worker cost.

### `_s` — numeric score metric (why it likely "never worked")
Two source parts, both present [SRC]: (1) `vdp_comm.s:205+` computes a worst-case overrun scanline
count from the VDP V-counter into `diag_score_bcd`; (2) `pc090oj_hooks.s:2450-2456` overwrites the P1
score bytes with that BCD **inside `native_frontend_hud_emit`**. **Static reason it may not display
during gameplay [INFER, not runtime-verified]:** `native_frontend_hud_emit` is the **frontend/title
HUD producer** (reached via `pc090oj_native_emit_pass` for scene 0/2), whereas **gameplay (scene 1)
renders the score through the separate `.Lnq_gameplay` HUD path**, which does **not** apply the
`diag_score_bcd` overwrite. So during actual gameplay — where overruns happen and the metric would be
read — the gameplay HUD shows the arcade score, not the metric; the overwrite only lands on the
frontend/attract HUD. Makefile `:67` labels it "NEVER shipped; corrupts the score," and `:581` notes
it "no longer adds a coverage page," consistent with a degraded/partly-wired diagnostic. **Not
repaired; cause is a static hypothesis requiring runtime confirmation.**

### `_do` — display-off publication (what's disabled; measurement impact)
`dma.s:72-94`. [SRC] What is disabled: the **active display is blanked** (reg1 → `0x8134`) for the
whole `dma_publish_frame` phase, then re-enabled (`0x8174`). Effect: VRAM/CRAM writes run at full
forced-blank bandwidth, and a publication that overruns VBlank appears as a **black band** (the
forced-blank region) rather than tearing/corrupting. **Measurement caveat [INFER]:** because `_do`
changes VDP bandwidth/timing during publication (full-bandwidth blanked DMA) and forces blank on
overrun, its timing and visible artifacts are **not directly comparable** to the display-on release;
`_do` is best read as "does the publication fit the blank window?" (clean) vs "black band = overran,"
not as a cycle-equivalent of the shipped ROM.

### `_c` — MODE rack-advance cheat
`tilemap_hooks.s:4143-4148` (+ `:4217,:4896`). [SRC] Completes the 6-button handshake and consumes P1
MODE to advance the rack (stage/subround) — an **opt-in cheat/debug-navigation ROM**. This is the ROM
the `_c` 18-subround closeout automation drives via MODE presses. Confirmed purpose.

## Dependencies

- `_d`: none emulator-specific — plain backdrop CRAM writes (works on hardware and emulators). [SRC]
- `_s`: reads VDP V-counter `0xC00008` (available on hardware and emulators); display correctness
  depends on the HUD producer path (the suspected defect), not on an emulator facility. [SRC/INFER]
- `_do`: real VDP display-enable register toggle (hardware and emulators). [SRC]
- `_c`: requires a **six-button controller** (or emulator 6-button pad) and the MODE button. [SRC]
- None of the five depends on a debugger/trace facility to run; `_d`/`_s`/`_do` are
  self-contained instrumentation/variant behaviors in the ROM.

---

*Read-only audit. Source-confirmed vs inferred behavior distinguished above; no runtime functionality
asserted from static evidence. No ROM built, no emulator run, no source/config/git change, Cody's
0428–0432 WIP untouched.*
