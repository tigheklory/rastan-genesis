# Andy — VBlank Commit Audit & Corrected Spec (Build 0033)

**Status:** SPEC COMPLETE — §16 of prior design doc is **OBSOLETE**. Cody's STOP was correct.
**Scope:** Analysis only. No source changes.
**Build Context:** Build 0033, `rastan-direct`.

---

## 1. Summary

Cody's STOP in `docs/design/Cody_bg_fg_dirty_flag_implementation.md` is correct: the
functions named in §16 of
`docs/design/Andy_rastan_direct_display_tightening_against_rainbow.md`
(`vdp_commit_bg`, `vdp_commit_fg`) do not exist in the current source. They
have been **superseded** by strip-level commit functions
`vdp_commit_bg_strips_if_dirty` and `vdp_commit_fg_strips_if_dirty`, which
**already carry the dirty-flag guard** the prior §16 was trying to introduce —
but at finer (per-strip) granularity using a 32-bit bitmap
(`bg_row_dirty`, `fg_row_dirty`).

**Corrected spec: no implementation required.** Adding coarse `bg_dirty`/
`fg_dirty` byte flags would be scaffolding (PRIME DIRECTIVE violation): they
would duplicate a guard that already exists at finer granularity, gate
nothing that isn't already gated, and add two new dirty sources that must be
kept consistent with the existing bitmap. §16's 4-step recipe is therefore
retired.

The remaining VBlank concerns — worst-case overrun when many strips are dirty,
and the absence of DMA — are orthogonal to flag granularity and are addressed
in the later sections of the prior design doc (§5 onward, the Rainbow Islands
strip model). Those items are out of scope for this audit.

---

## 2. Current Commit Function Inventory

Source: `apps/rastan-direct/src/main_68k.s` (1201 lines, read in full).

| Function | Start line | Has guard? | Guard kind | What it writes | Approx. cycle cost (no work) | Approx. cycle cost (full work) |
|----------|-----------|------------|------------|----------------|------------------------------|--------------------------------|
| `vdp_commit_tiles_if_dirty` | 667 | YES | `tst.b tiles_dirty / beq.s .Ltiles_done` at 668–669; `clr.b tiles_dirty` at 680 | 48 tile words to VRAM `0x00000020` | ~20 cycles (tst+beq+rts) | ~700 cycles (48×14 + setup) |
| `vdp_commit_bg_strips_if_dirty` | 684 | YES | `move.l bg_row_dirty, %d6 / beq.s .Lbg_done` at 685–686; per-strip `bclr` and final `move.l %d6, bg_row_dirty` at 710–711 | Up to 32 strips × 64 words to Plane B `0xC000` | ~24 cycles (move.l+beq+rts) | ~29,400 cycles (32×900) |
| `vdp_commit_fg_strips_if_dirty` | 721 | YES | `move.l fg_row_dirty, %d6 / beq.s .Lfg_done` at 722–723; per-strip `bclr` and final `move.l %d6, fg_row_dirty` at 747–748 | Up to 32 strips × 64 words to Plane A `0xE000` | ~24 cycles | ~29,400 cycles |
| `vdp_commit_palette` | 758 | NO (internal) — guarded at **call site** | Call-site `tst.b palette_dirty / beq.s .Lskip_palette` at 94–95; `clr.b palette_dirty` at 97 | 64 palette words to CRAM | ~0 cycles when skipped (guard is external) | ~900 cycles |
| `vdp_commit_scroll` | 768 | NO | — | HScroll table + VSRAM scroll Y (4 words total) | — (always runs) | ~104 cycles |

All three "plane-like" commits (`tiles`, `bg_strips`, `fg_strips`) already
implement a correct guard-early-exit-clear pattern. The only structural
difference is that `tiles_dirty` is a `.byte` flag while `bg_row_dirty` /
`fg_row_dirty` are 32-bit bitmaps — each bit gates one strip commit.

Evidence of the bitmap-as-guard design elsewhere in the source:
- `genesistan_hook_tilemap_plane_a` sets bits via `bset %d1, bg_row_dirty` at line 343.
- `genesistan_hook_tilemap_fg` sets bits at line 515.
- `genesistan_hook_tilemap_bg_fill` sets bits at line 624.
- `genesistan_hook_cwindow_clear` sets all 32 bits via
  `move.l #0xFFFFFFFF, bg_row_dirty` and
  `move.l #0xFFFFFFFF, fg_row_dirty` at lines 661–662.
- `init_staging_state` clears both bitmaps at lines 949–950
  (`clr.l bg_row_dirty`, `clr.l fg_row_dirty`).

---

## 3. Mismatch Resolution

**What changed between the prior design doc and the current source:**

The prior doc's §3 cycle accounting (`docs/design/Andy_rastan_direct_display_tightening_against_rainbow.md:79–85`)
describes `vdp_commit_bg` as a single 2048-word unconditional CPU loop:

```
Inner loop: move.w (%a0)+, VDP_DATA / dbra %d7, .Lbg_copy — 2048 iterations.
Total inner loop: 2048 × 24 cycles = 49,152 cycles.
```

The current source no longer has this shape. Instead
`vdp_commit_bg_strips_if_dirty` (line 684–719) iterates 32 strip rows, tests
one bit of `bg_row_dirty` per row, and commits only the 64 words of the strip
whose bit is set. When `bg_row_dirty == 0` the function returns after the
opening `move.l` + `beq.s` — roughly 24 cycles.

**Evidence of the change (no git archaeology needed — source is self-describing):**

1. The function name itself: `vdp_commit_bg_strips_if_dirty`. "`_strips_`"
   indicates per-strip granularity; "`_if_dirty`" indicates guarded.
2. The early-exit guard is present as the first instruction pair of the
   function body (`main_68k.s:685–686`).
3. The commit loop uses `btst %d5, %d6` gating (`main_68k.s:690`) — a
   per-strip test, not an unconditional copy.
4. The loop bound is 32 strips (`cmpi.w #32, %d5` at line 716), not 2048 words.
5. `bg_row_dirty` is declared as a `.long` implicitly in `.bss` — line 1151
   declares the label and line 1153 declares the paired `fg_row_dirty` label
   with trailing `.byte` space. Size is 4 bytes per label (confirmed by hook
   usage: `move.l bg_row_dirty, %d0` at line 342 — longword load).

**Prior doc §16 wrote against a snapshot that did not have the strip split.**
That earlier snapshot may have existed in a pre-Build 0029 source, or §16 may
have been written against a mental model of the older monolithic commit. In
either case, the current source has moved past §16's starting premise.

**Implication:** §16's 4-step recipe is applying a coarse guard where a fine
guard already exists. Cody's STOP correctly refuses to proceed.

---

## 4. VBlank Handler Audit

Source: `_VINT_handler` at `apps/rastan-direct/src/main_68k.s:81–109`.

### 4.1 Handler linear sequence

| Line | Instruction | Purpose |
|------|-------------|---------|
| 82 | `movem.l %d0-%d7/%a0-%a6, -(%sp)` | Save all registers. |
| 84 | `move.w VDP_CTRL, %d0` | VDP status read (clears pending). |
| 86–88 | `moveq #VDP_REG_MODE2 / moveq #VDP_MODE2_DISPLAY_OFF / bsr vdp_set_reg` | **Display OFF** bracket opens. |
| 90 | `bsr vdp_commit_tiles_if_dirty` | Tiles commit (guarded). |
| 91 | `bsr vdp_commit_bg_strips_if_dirty` | BG plane strips commit (guarded). |
| 92 | `bsr vdp_commit_fg_strips_if_dirty` | FG plane strips commit (guarded). |
| 94–98 | `tst.b palette_dirty / beq.s .Lskip_palette / bsr vdp_commit_palette / clr.b palette_dirty / .Lskip_palette:` | Palette commit (call-site guard). |
| 100–102 | `moveq #VDP_REG_MODE2 / moveq #VDP_MODE2_DISPLAY_ON / bsr vdp_set_reg` | **Display ON** bracket closes. |
| 104 | `bsr vdp_commit_scroll` | Scroll commit (unconditional). |
| 106 | `addq.w #1, frame_counter` | Frame counter tick. |
| 108 | `movem.l (%sp)+, %d0-%d7/%a0-%a6` | Restore. |
| 109 | `rte` | Return from exception. |

### 4.2 Explicit call chains from VBlank to every commit function

Every chain is one hop (VBlank handler → commit function directly); no commit
is reached through an intermediate dispatcher.

| Chain | Path | Already gated? |
|-------|------|----------------|
| VBlank → tiles | `_VINT_handler@81` → `bsr@90` → `vdp_commit_tiles_if_dirty@667` | YES (internal `.b` flag) |
| VBlank → BG strips | `_VINT_handler@81` → `bsr@91` → `vdp_commit_bg_strips_if_dirty@684` | YES (internal bitmap, 32 bits) |
| VBlank → FG strips | `_VINT_handler@81` → `bsr@92` → `vdp_commit_fg_strips_if_dirty@721` | YES (internal bitmap, 32 bits) |
| VBlank → palette | `_VINT_handler@81` → call-site `tst.b @94` → `bsr@96` → `vdp_commit_palette@758` | YES (call-site `.b` flag; palette function itself is unguarded but unreachable when flag clear) |
| VBlank → scroll | `_VINT_handler@81` → `bsr@104` → `vdp_commit_scroll@768` | NO — always executes |

Every commit function in the source is reachable from VBlank; no dead commit
functions exist. The display OFF/ON bracket surrounds the three
VRAM-destined commits (tiles, BG, FG) and the palette CRAM commit; scroll
runs after display ON (matches Rainbow Islands pattern per prior doc §5).

### 4.3 Display OFF/ON bracket status

- **Present and correctly ordered:** Display OFF at line 86–88 before all
  VRAM/CRAM commits; Display ON at line 100–102 before scroll.
- **Unchanged from prior doc:** the bracket was correct in §3/§4 of the prior
  doc and is still correct. No edit needed.

---

## 5. Current VBlank Budget Assessment

Budget: NTSC 224-line mode, approximately **7,400 cycles** (unchanged).

### 5.1 Steady-state cost when nothing is dirty

| Component | Cycles | Source |
|-----------|--------|--------|
| Register save | ~108 | line 82 |
| VDP status read | ~8 | line 84 |
| Display OFF | ~40 | lines 86–88 |
| `vdp_commit_tiles_if_dirty` early-exit | ~20 | lines 668–669, 682 |
| `vdp_commit_bg_strips_if_dirty` early-exit | ~24 | lines 685–686, 719 |
| `vdp_commit_fg_strips_if_dirty` early-exit | ~24 | lines 722–723, 756 |
| `palette_dirty` check skip | ~16 | lines 94–95 |
| Display ON | ~40 | lines 100–102 |
| `vdp_commit_scroll` | ~104 | line 104 |
| Frame counter + overhead | ~40 | line 106 |
| Register restore + RTE | ~128 | lines 108–109 |
| **Total steady state (nothing dirty)** | **~552 cycles** | |

**Overrun status — steady state:** **NOT PRESENT.** 552 cycles ≪ 7,400
budget. The guards are already in place and working.

### 5.2 Worst-case cost when all strips dirty both planes

If `bg_row_dirty == 0xFFFFFFFF` AND `fg_row_dirty == 0xFFFFFFFF` in the same
frame (e.g., the frame right after `genesistan_hook_cwindow_clear` runs,
which sets all 64 bits at lines 661–662), the two commits run 32 strips each:

- 32 strips × 64 words × ~14 cycles/word × 2 planes ≈ 57,344 cycles for the
  writes alone, plus per-strip setup.
- Total: comparable to the ~59,268 cycles that §3 of the prior doc
  attributed to `vdp_commit_bg`/`vdp_commit_fg` in the unconditional-copy era.

**Overrun status — worst case after full-plane dirty event:** **STILL
POSSIBLE.** But this is **not** a flag-granularity problem — it is a "what
writes 64 dirty bits in a single frame" problem. Adding coarse `bg_dirty`/
`fg_dirty` byte flags **cannot fix this case** because those flags would
still be set whenever the bitmap is non-zero, so the full commit would still
run.

### 5.3 Typical-gameplay cost (few strips dirty)

When the arcade tick dirties a handful of strips per frame (e.g., 2–4 strips
per plane during scrolling), cost is approximately:

- 4 strips × 64 words × ~14 cycles × 2 planes ≈ 7,168 cycles + ~200 overhead
  ≈ 7,400 cycles.

This is **at budget**, not over. Once the arcade ROM is integrated and real
PC080SN hook traffic runs, this is the regime to monitor.

### 5.4 Overrun summary

| Scenario | Cycles | Over 7,400-cycle budget? |
|----------|--------|--------------------------|
| Nothing dirty (steady) | ~552 | NO |
| Few strips dirty (normal gameplay) | ~7,400 | AT BUDGET |
| All 64 strips dirty (frame after cwindow_clear) | ~57,000 | YES, ~7.7× |

**Verdict: overrun still present = PARTIAL.** The steady-state overrun the
prior doc's §16 was trying to fix is already resolved by the strip-level
guard. The remaining worst-case overrun is a **strip-count / one-shot clear
event** problem, unrelated to flag granularity.

---

## 6. Corrected Implementation Specification for Cody

**Zero design decisions remain.**

### 6.1 Action required

**NONE.** Do not add `bg_dirty` or `fg_dirty` flags.

Justification traces to the PRIME DIRECTIVE: coarse `.b` flags on top of the
existing 32-bit bitmap guards would be scaffolding. They would:

- Duplicate a guard that already exists at finer granularity.
- Add two dirty sources (the byte flag AND the bitmap) that must be kept
  consistent across every hook site, creating a maintenance surface for zero
  functional benefit.
- Not change steady-state cost (both paths early-exit at ~24 cycles).
- Not fix worst-case cost (when bitmap is non-zero the byte flag would also
  be set and the commit would run anyway).

### 6.2 What Cody should do next

1. **Close** Cody's STOP report
   (`docs/design/Cody_bg_fg_dirty_flag_implementation.md`) by noting that the
   STOP was correct and that the task has been retired by this audit.
2. **Do not modify** `apps/rastan-direct/src/main_68k.s`. No lines added or
   changed.
3. **Do not modify** `specs/rastan_direct_remap.json`,
   `build/rastan-direct/rastan_direct_patch_manifest.json`,
   `build/rastan-direct/address_map.json`. The task has no ROM implication.
4. **No build required.** No trace required.

### 6.3 Follow-up scope that is **not** this task

If the user wants to attack the remaining worst-case overrun (§5.2), the
correct next step is **not** adding a coarse flag. It is one of:

- Investigating whether `genesistan_hook_cwindow_clear` should actually mark
  all 32 strips dirty in one frame, or whether the clear should be staged
  over several frames to amortize the commit cost.
- Moving plane commits to VDP DMA (addressed in prior doc §5 onward — not
  recommended as the next step per the prior doc's own conclusion).
- Limiting the per-VBlank commit count (commit at most N strips per frame).

Each of these is a separate design task and requires its own prompt.

---

## 7. Next-Step Impact

- Cody's blocked task is now **retired** rather than unblocked. No further
  implementation attempt should happen against §16 of the prior doc.
- The prior design doc
  (`docs/design/Andy_rastan_direct_display_tightening_against_rainbow.md`)
  §16 is marked OBSOLETE by this document. §3 worst-case numbers are
  superseded by §5 of this document.
- VBlank steady-state correctness: **confirmed working.** The source uses
  the Rainbow Islands-style per-strip guard the prior doc advocated for in
  its later sections.
- If a regression ever re-introduces a "full plane commit every frame" path,
  the correct fix is to re-audit the specific commit function and restore
  the `_strips_if_dirty` pattern — not to add a coarse byte flag.

---

## 8. STOP Conditions

None triggered. All required analysis sections are complete, all five
commit functions are inventoried, every call chain is mapped, and the
corrected spec is a closed "do nothing, document the retirement" outcome.
