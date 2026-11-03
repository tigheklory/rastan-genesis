# Builds 0337–0339 — Diagnostic Build Variants + the Performance Optimization Program

**Type:** Infrastructure / Tooling / Analysis. Diagnostic ROMs produced; no gameplay behavior change in the release ROMs. Classification: **INFRASTRUCTURE**.
**Scope:** everything since the "Build 0336 — Sonic-Style CRAM DMA Publication" section of
`Andy_palette_composer_v2_complete_pose_powerup_water_architecture.md` (the previous design-folder write):
the shift from feature work to a **measure-then-optimize** performance program, the in-ROM diagnostic
build variants, the dual/triple-build convention, and the `OPTIMIZATIONS.md` registry.

## 1. Why: the performance turn
After Build 0336 (palette publication → unconditional VBlank CRAM DMA), Tighe reported the recurring
problems that feature work wasn't fixing: the game runs **too slow and has been getting slower over
time**, and the **noise band** returns on water screens. Two decisions followed:
1. Stop guessing about speed — build **objective measurement**.
2. Track optimizations as a **program of accumulated small cuts** ("life by a thousand cuts"), not a
   single hero fix.

### Root-cause framing (the fixed performance fact)
The arcade offloaded tilemap + sprite rendering to dedicated chips (PC080SN, PC090OJ) that the arcade
68000 fed with **cheap register/RAM writes**. The Genesis has no such chips, so **our 68000 does that
work in software**. The arcade **game logic is translated byte-for-byte** and costs the same on both
machines; therefore the **entire per-frame cost delta is our native production code + DMA**. The
suspected #1 cost is **DMA-halt cycles**: a 68k→VRAM/CRAM DMA **halts the 68000** for the whole
transfer, and we DMA planes + SAT + palette **every frame** with the display left ON (Build 0227),
where DMA is far slower per word — so this is *cycles*, not instructions.

### The noise band, restated correctly
The vertical/horizontal noise band is **CRAM being written during active display** (the display stays
ON since Build 0227; VRAM DMA is display-on-safe, CRAM writes are not). Event-driven commits (Builds
0329–0333) committed rarely → the band was almost never seen; the Build-0336 unconditional DMA
commits **every frame** → the band became **constant** on water screens. Frequency changed how often
it shows; the real cause is **timing** — the CRAM transfer landing on active scanlines because the
servicing overruns the vblank window. This is the original deferred vertical-noise root cause.

## 2. Sonic 1 reference (local, gitignored)
Cloned `github.com/sonicretro/s1disasm` → `docs/reference/s1disasm/` (37 MB, `.gitignore`d — never
committed to this project). It answers "how do Genesis games animate palettes cheaply / avoid the band":
- **Cycle producer** `PalCycle_GHZ` (`_inc/PaletteCycle.asm:44`): writes only a few color words into a
  **RAM palette buffer** (line 3, entries 8–B); no CRAM touch, no dirty flag.
- **Publication** `writeCRAM` macro (`Macros.asm:35`): a **68k→CRAM DMA** of the whole palette buffer,
  done in V-blank with the Z80 stopped (`sonic.asm:736`), **unconditionally every frame**.
This validated the Build-0336 architecture (event-driven staging + whole-buffer DMA) and confirmed the
fix direction: the CRAM DMA must land inside the vblank window (OPT-004). *Correction on record:* I
earlier wrongly claimed Mesen 2 emulates the Genesis — it does not (SMS/GG, not Mega Drive); use
BlastEm/Exodus, or our own in-ROM diagnostics below.

## 3. Build 0337 — in-ROM CPU-load raster bar + dual-build
- **`RASTAN_DIAG_CPU_BAR` build flag** (`vdp_comm.s` `_vblank_service`): sets the VDP backdrop (CRAM
  entry 0) bright green **after** `vdp_commit_palette` (so the palette DMA doesn't clobber it), across
  the sprite + plane + scroll VDP commits/DMA, then clears it to black before the arcade handler. The
  on-screen coloured band's extent = the **Genesis servicing** cost; if it reaches into the active
  picture, servicing **overran vblank**. It captures DMA-halt time (backdrop stays bright while a DMA
  stalls the CPU), needs no external debugger, and is visible in any emulator or a screenshot.
- **Dual-build convention:** every `make all`/`release` now emits the numbered release ROM
  (`_NNNN.bin`, bar off) **and** a same-numbered diagnostic ROM (`_NNNN_d.bin`, bar on). The `_d` is a
  **postpatch-only copy** built via a recursive `diag-variant` invocation with `RASTAN_DIAG_CPU_BAR=1`;
  it reuses the release's number and is **never numbered/ledgered** itself.
- Verified: release `0337` byte-identical to `0336` except the build stamp → the diagnostic plumbing
  does not touch the shipped code.

## 4. Build 0338 — numeric score metric + triple-build
- **`RASTAN_DIAG_SCORE_METRIC` build flag** (`vdp_comm.s` `_vblank_service`): reads the VDP **V-counter**
  at the end of servicing. `V ≥ 0xE0` → still in vblank → overran 0 scanlines; `V < 0xE0` → servicing
  bled into active display line `V` → overran `V` scanlines. Keeps a **self-initialising running max**
  (a value > 223 is impossible → treated as garbage/init), converts to 3-digit BCD.
- **Metric = peak active-display scanlines the Genesis servicing overran.** `0` = fits entirely in
  vblank; `N` = worst-case overran `N` scanlines — the numeric companion to the 0337 bar.
- **Triple-build:** `make` now emits **three** ROMs per number: `_NNNN.bin` (release), `_NNNN_d.bin`
  (bar), `_NNNN_s.bin` (metric). `_d`/`_s` are postpatch-only copies (separate diag/score manifests),
  reuse the release number, never ledgered.

## 5. Build 0339 — score-metric display fix (the real fix)
Build 0338's metric did **not** display — writing the P1 score (`0xFF011E`) in `_vblank_service` was
**clobbered by the arcade's own score update** in the arcade handler (jmp `0x3A208`) *before* the HUD
read it, so the 1UP kept showing the game score. Fix:
- `_vblank_service` now stores the 3-byte metric BCD in a BSS var **`diag_score_bcd`** (defined only
  under `RASTAN_DIAG_SCORE_METRIC`).
- The HUD emitter copies `diag_score_bcd → 0xFF011E` (memory-to-memory, no registers) **at the exact
  read point**, in both `.Lnq_project_p1_hud` (gameplay) and `native_frontend_hud_emit` (frontend), so
  the metric **wins over** the arcade score update.
- `pc090oj_hooks.s` carries an unconditional `.extern diag_score_bcd`; harmless in release/`_d` builds
  because the copy instructions are `.if RASTAN_DIAG_SCORE_METRIC`-gated (symbol never referenced →
  no link error).
- Verified: release `0339` differs from `0338` by only the build stamp (2 bytes).

## 6. The dual/triple-build convention (Makefile)
- `RASTAN_DIAG_CPU_BAR ?= 0`, `RASTAN_DIAG_SCORE_METRIC ?= 0` — flow into `pc090oj_config.inc`
  (regenerated each build via `FORCE_ASM_REBUILD`, so the current flag value always applies).
- `all: dual-build` runs `$(MAKE) $(BIN)` (normal, owns counter/gates/ledger) then
  `$(MAKE) diag-variant RASTAN_DIAG_CPU_BAR=1` and `$(MAKE) score-variant RASTAN_DIAG_SCORE_METRIC=1`.
- `$(DIAG_ROM)`/`$(SCORE_ROM)` are **postpatch-only** targets (boot-guard → copy prepatch →
  build_rastan_regions → postpatch → boot-guard, separate manifests) — **no** numbered-release/counter
  logic. `diag-variant`/`score-variant` copy them to `_NNNN_d.bin`/`_NNNN_s.bin` using the current
  counter, without advancing it.
- Result each `make`: `_NNNN.bin` (ledgered once), `_NNNN_d.bin`, `_NNNN_s.bin`.
- **Flaky gate note:** the seven-epoch gameplay-entry gate failed transiently once (epoch 2/record 4)
  during 0337, then passed on byte-identical code — the injection-based gate is occasionally flaky;
  not a regression, worth hardening later.

## 7. OPTIMIZATIONS.md registry (repo root)
Created a living registry (parallel to `OPEN_ISSUES.md`/`KNOWN_FINDINGS.md`): add on discovery, flip to
`IMPLEMENTED` with build + SHA + measured effect, keep a **cumulative cycles/frame-saved tracker**
against the ~127,840-cycle frame budget (7.67 MHz ÷ 60 Hz). Strategy section: prioritise **per-frame
recurring** cuts (compound 60×/sec) and **zero-risk subtractive** cuts (prebaking — faster runtime +
smaller ROM). Entries:
- **OPT-001** (palette) prebake static xBGR-555→CRAM offline — `.Lxbgr555_to_cram` (20 instr/color, 7
  sites) shouldn't run for ROM-sourced palettes. LOW–MED.
- **OPT-002** (palette) collapse runtime 2-step `0RGB444→xBGR555→CRAM` to 1 step. LOW.
- **OPT-003** (sprites) prebake the per-piece palette line — `.Lnative_palsel` (`pc090oj_hooks.s:1208`)
  linear-scans the route table **per emitted piece** (~28 avg/72 max/frame); bake `code→line` into the
  reindex. MED–HIGH; folds into the `(code,bank)` work. **Recommended first real cut.**
- **OPT-004** (vblank/DMA) reduce DMA-halt cost — minimise word volume + land the CRAM/plane DMA in
  vblank (also kills the noise band). HIGH (suspected #1). `MEASURING`.
- **OPT-005** (vblank) Tighe's split — short essential-vblank handler (VDP transfers) then the arcade
  logic runs after, 1-frame lag, no new RAM. HIGH *if* VINT-deferred; otherwise noise-fix + smoother
  degradation only (reordering can't create cycles). `MEASURING`.
- **OPT-006** (sprites) prebake fixed per-descriptor coordinate offsets. LOW.
- **OPT-007** (tooling) the profiler/visualization — **PARTIAL** (bar 0337, metric 0339 done; full-frame
  variant, game-logic-fps metric, and scripted headless meter still pending).

## 8. Trace tooling changes (non-production)
- `tools/mame/scripts/trace_line2_progression.lua` — made STAGED/SCENE/TILESET addresses
  **env-overridable** (BSS symbols shifted when the palette scaffolding was removed in 0336;
  `staged_palette_words` 0xFF60E4→0xFF60A0, `scene_id` 0xFFC0AC→0xFFC068).
- `tools/mame/scripts/trace_staged_palette_writers.lua` — added (write-provenance; note: MAME's DRC
  bypasses opcode/write taps, so full per-instruction tracing is not feasible — hence the in-ROM bar/
  metric approach).

## 9. Honest caveats (carried in OPTIMIZATIONS.md)
- The bar (`_d`) and metric (`_s`) currently measure the **Genesis servicing window only**
  (post-palette-DMA → end of commits), **not** the full frame including the arcade game logic — a
  full-frame version needs hooking the arcade idle/rte point.
- Both are **relative/visual** indicators (they perturb timing by a few instructions), not
  cycle-exact; the `_s` build also **overwrites the P1 score**, so read it while not actively scoring.
- Instruction count alone is misleading (DMA-halt is cycles); rank by cycles, measure first.

## 10. Current diagnostic artifacts
Latest good trio: **`build_0339.bin`** (release, SHA `c4bca09c…`), **`build_0339_d.bin`** (bar, SHA
`7b04ffbd…`), **`build_0339_s.bin`** (metric, SHA `d6f23afefd…`). Ledger recorded 0339 once; counter 339.
Builds 0337/0338 superseded (0338's metric didn't display; 0339 fixed it).

## 11. USER MUST VERIFY
- `build_0339_d` on an R1/P1 water screen: the coloured band shows servicing/overrun; band into the
  active picture = vblank overrun.
- `build_0339_s`: the 1UP score reads the **metric** (peak servicing-overrun scanlines), not the game
  score; it should track the bar's overrun. (Don't actively score while reading it.)
- Release `build_0339.bin` plays exactly as `0336` (byte-identical to `0338` minus stamp; both diag
  flags off).

## 12. Next steps
1. Optionally extend both diagnostics to the **full frame** (include arcade logic) and add a
   **game-logic-fps** metric + scripted headless meter (OPT-007 remainder) to auto-feed the tracker.
2. Take the first real cut — **OPT-003** (prebake per-piece palette line) — and watch `_s` drop.
3. Then measure/target **OPT-004** (DMA-halt) and evaluate **OPT-005** (vblank split) with the data.
