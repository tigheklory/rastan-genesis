# Pure-Publisher Audit, Palette Gating, and the OPT-003 Blocker

**Author:** Andy
**Date:** 2026-09-05
**Builds:** 0347 (throwaway), 0348 (clean baseline == 0346 behavior)
**Status:** Execution-order refactor found already-implemented; palette gating + dirty-row
coalescing BLOCKED on OPT-003; reverted to a clean gate-passing tree.
**Related:** `Andy_central_vblank_dma_publisher_brief.md` (Builds 0343–0346),
`OPTIMIZATIONS.md` (OPT-003).

---

## 1. Task and its premise

The task ("MOVE ALL GRAPHICS PRODUCTION OUT OF VBLANK / MAKE `dma_publish_frame` A PURE
PUBLISHER") assumed that meaningful graphics *production* still runs inside the VBlank
publication interval, and that this is why the display-off (`_do`) build shows large black
bands. It asked to move producers before the next VBlank and leave `dma_publish_frame` a
bounded publisher.

**Audit result: the premise did not match the code.** The produce-then-publish execution
order already exists.

---

## 2. Old ordering vs. actual current ordering

The intended "target" ordering the task describes is already what runs:

```
VINT (VBlank N):
  _vblank_service:
    rastan_direct_update_inputs
    vdp_prepare_sprites          ; producer GUARD (no DMA); no-op in gameplay (SAT already staged)
    dma_publish_frame            ; THE single publication phase (transfers frame N-1 staged state)
    jmp (0x3A208)                ; -> arcade tick == the PRODUCERS for frame N
                                 ;    (arcade semantic processing + native Genesis hooks
                                 ;     fill staged_* buffers through the rest of the frame)
... arcade tick runs until ...
VINT (VBlank N+1): publish frame N. Repeat.
```

The arcade tick is reached by an unconditional `jmp`, not a call — so producer work runs
*after* the current publication and *before* the next VBlank, exactly as required. There is
no second game loop and arcade frame authority is unchanged.

---

## 3. Where each producer actually runs (all BEFORE the next VBlank)

| Producer | Execution point | Writes |
|---|---|---|
| SAT / sprite pieces | arcade-tick hooks `genesistan_pc090oj_hook_target_41dae` / `_45dfa` → `pc090oj_native_emit_pass` (sets `pc090oj_sat_frame_ready`) | staged SAT (double-buffered) |
| Sprite pattern requests | same emit pass | `pc090oj_tile_dma_worklist` |
| Plane A / Plane B | tilemap hooks → `staged_fg_buffer` / `staged_bg_buffer` | plane name words + `fg_row_dirty` / `bg_row_dirty` |
| Layer-A package decision | `fg_boundary_install` (record-driven, at epoch transition) | `fg_boundary_active_lut`, resident VRAM |
| Palette | `palette_hooks` (arcade palette writes) + `vdp_install_test_lines` (scene load) | `staged_palette_words` |
| Scroll | arcade-tick scroll hooks | `staged_scroll_x/y_bg/fg` |
| Tiles | tile hook | `staged_tile_words` + `tiles_dirty` |

`vdp_prepare_sprites` builds the SAT only as a *fallback* when the tick did not (non-gameplay
frames); in gameplay `pc090oj_sat_frame_ready` is already set, so it is a no-op guard. **SAT
construction is therefore already complete before the VBlank that publishes it.**

---

## 4. `dma_publish_frame` is already a bounded publisher

Evidence table — every commit path consumes already-completed staged state; none creates
graphics output:

| routine | staged state consumed | producer work in commit? | bounded interpretation | DMA (bound) | PIO (bound) |
|---|---|---|---|---|---|
| `vdp_commit_palette` | `staged_palette_words` | NO | (was: none — unconditional) | 1 CRAM DMA (64 w) | — |
| `vdp_commit_tiles_if_dirty` | `staged_tile_words` | NO | `tst tiles_dirty` | — | 48 words |
| `vdp_commit_bg_strips_if_dirty` | `staged_bg_buffer` | NO | walk 32-bit `bg_row_dirty` | ≤32 row DMAs (64 w) | — |
| `vdp_commit_fg_narrow_strips` | `staged_fg_buffer` + `fg_narrow_desc_table` | NO | walk desc table | ≤32 row DMAs | ≤ (desc×3×16) words |
| `vdp_commit_sprites_vram` | staged SAT + tile worklist | NO | worklist walk | ≤12 tile DMAs + 1 SAT DMA (320 w) | — |
| `vdp_commit_scroll` | `staged_scroll_*` | NO | scene-id branch | — | HScroll + VSRAM |

**Conclusion:** "If the routine only transfers already-decided final state, it is publication
work." All six qualify. The only non-pure item was that palette DMA'd **unconditionally** every
frame.

---

## 5. The `_do` black band is transfer VOLUME, not producer work

The black band = time from display-OFF to display-ON = time to run the six commits. Its cost
is dominated by **plane transfer volume** (up to 32 dirty BG rows + 32 dirty FG rows of 64
words each), which is legitimate publication. It shrinks by:

- **Dirty-row coalescing** — merge contiguous dirty rows into fewer, larger DMAs (removes
  per-DMA setup overhead; does NOT reduce underlying plane byte volume). In scope, deferred
  by OPT-003 (see §7).
- **Seam/edge model** — transfer only newly revealed rows instead of ≤32. Explicitly out of
  scope for this task.

Moving production out of the interval cannot shrink the band, because production is already
outside it.

---

## 6. Palette semantic flag (Part E) — implemented, then reverted

Implemented the Rainbow-style flag:

- New `palette_pending` byte (BSS in `vdp_comm.s`).
- Every genuine producer that changes `staged_palette_words` sets it: the four palette hooks
  (`genesistan_palette_hook_59ad4` / `_03ab00` / `_45dae` / `_3ba64`, using their existing
  `d5` "changed" accumulators), `vdp_install_test_lines` (scene activation), and boot.
- `dma_publish_frame` publishes the whole 64-word staged palette **only** when the flag is
  set, then clears it. No 64-entry compare, no reassert, no unconditional DMA.

The code is correct and complete, but it **fails the canonical seven-epoch gate** — see §7 —
so it was reverted. Unchanged-frame CRAM cost would have been 0.

---

## 7. OPT-003 — the blocker (investigated under Tighe's authorization)

Both palette gating (skips a DMA → faster publication) and dirty-row coalescing (fewer DMA
setups → faster publication) **change publication timing**, and any such change trips the
canonical `build0310_epoch_gate` at `active_lut[0x034C]`.

### What the gate does
It cannot trigger the Layer-A installer naturally (MAME's DRC bypasses its instruction taps),
so it **injects** a synthetic epoch-0→5 transition: it writes `target_record` to `a5+0x013E`,
pushes the interrupted PC, and jumps the CPU to `fg_boundary_install`. It then samples
`verify_maps()` once at the first frame the target package is active and holds
`required_survival_frames` (8). It asserts `active_lut[0x034C] == 0x0420` (package-5 map
index 308).

### What I established
- Code **0x034C sits at the exact conflict-range boundary**
  (`CONFLICT_CODE_FIRST 0x031A + COUNT 0x0032 = 0x034C`, exclusive) → it is the first *dense*
  code after the conflict block. Both the gate and the installer's `.Lactive_lut_address`
  treat it as dense (consistent; no conflict/dense mismatch).
- `FG_BOUNDARY_LUT_WORDS = 10240`, so 0x034C (844) is in range and not skipped by the
  map-loop bound.
- Package 0's map has **no** 0x034C (its epoch-0 value 0x0420 persists from the fixed-B
  install); package 5's map has it exactly **once** (index 308, slot 0x0420). No duplicate to
  overwrite it.
- `active_lut` is written **only** by `fg_boundary_install` (initial-clear / clear-old /
  maps). The per-tile resolver (`fg_boundary_resolve_a/b`) reads only (returns 0 on a miss,
  never writes). No per-frame writer exists.
- The install runs **interrupt-masked + display-off** (atomic) and is deterministic given the
  static package data, so it *should* leave 0x034C = 0x0420. Yet the runtime samples 0.

### Why it is a blocker
It is **timing-fragile**, not a static bug:
- Unconditional palette (0346 timing) → gate PASS, `active_lut[0x034C]=0x0420`.
- Palette-skip (0347 timing, faster publication) → gate FAIL, `active_lut[0x034C]=0`.
- Adding a **single debug instruction** flipped the result (a Heisenbug).
- `verify_maps` (sampled once at `install_frame`) and independent **per-frame reads of the
  same address** disagree — so the clobber is **sub-frame**, entangled with the DRC-bypassing
  injection and the long masked install spanning emulated frames.

The exact clobber resisted isolation within a responsible budget (this investigation already
overspent). It is the OPT-003 phenomenon previously deferred.

### RESOLUTION (2026-09-05, gate-methodology route) — SYNTHETIC GATE ARTIFACT

Built a valid-transition test that reaches the SAME record 2(pkg0)→3(pkg5) epoch transition
through **natural arcade progression** (drive P1 Start, then hold P1 Right so the player
scrolls and the arcade's own `fg_boundary_advance_segment` boundary — the replacement for
arcade 0x0558FE — advances the record and calls the real installer). **Zero injection, no
forced record write, no PC hijack.** Tools: `tools/mame/scripts/opt003_natural_transition.lua`
+ `tools/mame/run_opt003_natural_wsl.sh`.

Validation matrix (record advances 0→1→2→3 naturally; records 0/1/2 all map to package 0, so
0x034C=0 there is CORRECT; only record 3 = package 5 uses 0x034C):

| Config | reached record 3 | `active_lut[0x034C]` after install | +24 frames | exceptions |
|---|---|---|---|---|
| Build 0348 (unconditional palette) | frame 5277 | **0x0420 CORRECT** | stable 0x0420 | 0 |
| Palette-gated (faster publication) | frame 5276 | **0x0420 CORRECT** | stable 0x0420 | 0 |

**Under a semantically valid transition the failure does not reproduce, in either timing.**
Additionally, the synthetic gate showed a *stale* `active_lut[0x034C]=0x0420` while package 0
was active (its no-scroll/attract-residue starting state), where natural progression correctly
shows `0`. So the synthetic gate begins its 0→5 injection from a corrupted LUT and hijacks an
arbitrary mid-frame PC — that invalid context, not `fg_boundary_install`, is what produces the
timing-fragile 0/0x0420 flip at the conflict-boundary code 0x034C.

**Classification: SYNTHETIC GATE ARTIFACT.** `fg_boundary_install` is NOT modified. The
timing-fragile assertion is a property of the synthetic build0310_epoch_gate injection, not of
production code.

### Consequence
- `palette_pending` is correct and restored; it produces correct graphics under real
  gameplay (proven above).
- The canonical `build0310_epoch_gate` mid-frame injection must be replaced with a valid
  transition mechanism (natural progression, or invoking `fg_boundary_advance_segment` from a
  clean epoch-0 state) before `make all` accepts publication-timing changes. Its OTHER checks
  (fixed-B LUT, slot validity, exceptions, sp) remain valid; only the injected active-LUT
  assertion is the artifact. The specific corruption is the stale starting LUT (force a clean
  epoch-0 install before the transition, or reach package 0 by scroll).
- With the gate corrected, palette gating and Plane-A/Plane-B dirty-row coalescing are
  unblocked.

---

## 8. Display-OFF black band — before/after

No net change this task (the palette flag was reverted; coalescing was not implemented).
Baseline 0348 == 0346. Measuring/reducing the band is gated behind OPT-003.

---

## 9. Builds and status

- **0347** — THROWAWAY. Published during a debug-bypass run; functionally unconditional
  palette (== 0346) but carries dead palette-flag/debug cruft. Do not use.
- **0348** — CLEAN baseline. All gates PASS (seven-epoch PASS, canonical GATE_PASS, boot
  guard). Functionally identical to the user-confirmed 0346.
  - `0348` SHA256 `fac088eb0f8e9d374af80d9381aeecfe20be2ec6138ab688cfc6d0c45db1bf6b`
  - `0348_do` SHA256 `f9524159fc93fd8beb6be73525d2368fe6ec641bb5c7686aab8581711aa9f630`
  - counter = 348

Automated gate: PASS (0348). User gameplay verification: PENDING. Build status: UNVERIFIED
pending Tighe.

---

## 10. Open items (observations, NOT actioned this task)

- **NEW Segment-5 `_do` crash — read from `0xD00462` (BlastEm).** Observed by Tighe on the
  display-off build at Segment 5. `0xD00xxx` is the arcade **PC090OJ** chip-address region;
  this is a *second, different* unrebased absolute-literal hit (the first, `0x10D280`, was
  fixed in Build 0346). Same class as `project_arcade_workram_overlap` / the missed-WRAM-literal
  pattern: an absolute arcade chip/work-RAM address that aliases unmapped space on Genesis and
  is reached only under display-off timing. NOT investigated or fixed here per Tighe's
  instruction. Candidate for the crash-capture tool
  (`tools/mame/run_genesis_crash_capture_wsl.sh`) when reopened.
- OPT-003 is now open/active per Tighe's authorization; §7 is the handoff.
- The score `9`, `1UP`, castle red-pixel, and title-art defects remain out of scope
  (observation is not scope).
