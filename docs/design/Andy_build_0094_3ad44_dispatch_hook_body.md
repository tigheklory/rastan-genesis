# Andy — Build 0094 `genesistan_hook_3ad44_dispatch` Hook-Body Read

**Author:** Andy
**Date:** 2026-06-23
**Build:** 0094 (`dist/rastan-direct/rastan_direct_video_test_build_0094.bin`)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No build. No runtime probing. Narrow resume (mapping settled; not re-done). No implementation.

Mapping authority (already settled, `build/rastan-direct/address_map.json`): arcade `0x03AD44` → Genesis `0x03AF44` (patched_site → `JSR 0x00071618`); `0x03AE64`→`0x3B064`, `0x03AE74`→`0x3B074` (arcade_copy); `0x03AA82`→`0x3AC82`, `0x03AAAE`→`0x3ACAE`. Labels: [STATIC] = proven from source/disasm; [INFERENCE] = reasoned.

---

## Phase 0 — Baseline

**Relevant priors:** KF-028 (title-text producer→staging — STRONG), KF-010 (FG→Plane A, BG→Plane B — STRONG), KF-013/011, KF-004/006. **Task classification:** EXTENDING (OPEN-001). **Issues:** OPEN-001 active, OPEN-016 context, OPEN-015 do-not-touch. **Contradiction:** NONE. **Architecture compliance:** CONFIRMED (recommended fix is a staging-routed helper correctness change; no Genesis control-flow ownership).

This read corrects the prior `Andy_build_0094_fg_text_lifecycle_static_map.md` conclusion ("no FG clear in attract path"): the clear **is** translated; the defect is inside the translation.

---

## 1. The clear path and dispatch (source-confirmed)

Arcade clear-path entry (Genesis `0x3B064`/`0x3B074` = arcade `0x3AE64`/`0x3AE74`, arcade_copy) calls the fill loop twice:
```
3b064: lea 0xc00100,%a0 ; movew #1900,%d1 ; moveq #32,%d0 ; bsrw 0x3af44   ; BG clear
3b074: lea 0xc08100,%a0 ; movew #1900,%d1 ; moveq #32,%d0 ; bsrw 0x3af44   ; FG clear
```
`0x3AF44` (= arcade `0x3AD44`, patched_site) = `jsr 0x71618` (`genesistan_hook_3ad44_dispatch`) `; rts`.

`genesistan_hook_3ad44_dispatch` (`pc090oj_hooks.s:353`):
```
move.l %a0,%d2
cmpi.l #0x00C00000,%d2 ; blo .Lcheck_pc090oj
cmpi.l #0x00C10000,%d2 ; blo .Lhook_3ad44_tilemap     ; A0 in [0xC00000,0xC10000) -> tilemap
...
.Lhook_3ad44_tilemap:
    bsr genesistan_hook_tilemap_bg_fill                ; <-- UNCONDITIONAL: both BG and FG go here
    bra .Lhook_3ad44_finish
```

**[STATIC] Both the BG clear (A0=0xC00100) and the FG clear (A0=0xC08100) are routed to `genesistan_hook_tilemap_bg_fill`** — there is no BG-vs-FG split.

---

## 2. `genesistan_hook_tilemap_bg_fill` is BG-only (the defect)

`tilemap_hooks.s:388`:
```
genesistan_hook_tilemap_bg_fill:
    movem.l save
    movea.l %a0,%a4 ; move.l %a4,%d2 ; andi.l #0xFFFFFF,%d2
    cmpi.l #ARCADE_PC080SN_CWINDOW_BASE_BG, %d2          ; 0xC00000
    blo .Lbg_fill_done
    cmpi.l #(ARCADE_PC080SN_CWINDOW_BASE_BG+ARCADE_PC080SN_CWINDOW_BYTES), %d2  ; 0xC04000
    bhs .Lbg_fill_done                                   ; <-- A0 >= 0xC04000 -> NO-OP
    ...
    lea staged_bg_buffer, %a6                            ; BG target only
    ... (d0=0x20 -> tile_vram_lut[32] | attr_lut -> blank cell d3)
.Lbg_fill_loop:
    ... subi.l #ARCADE_PC080SN_CWINDOW_BASE_BG, %d2 ...  ; base 0xC00000 only
    move.w %d3, 0(%a6,%d0.w)                             ; write staged_bg_buffer
    move.l bg_row_dirty,%d0 ; bset %d5,%d0 ; move.l %d0,bg_row_dirty   ; BG dirty only
    adda.l #4,%a4 ; subq.w #1,%d6 ; bne .Lbg_fill_loop   ; d6 = d1 = 1900
.Lbg_fill_done:
    rts
```

**[STATIC]** Its accepted range is `[0xC00000, 0xC04000)` (BG C-window), base `0xC00000`, target `staged_bg_buffer`, dirty `bg_row_dirty`. `ARCADE_PC080SN_CWINDOW_BYTES = 0x4000`; FG C-window is `[0xC08000, 0xC0C000)`.

---

## Answers to Q1–Q6

**Q1 — A0 tilemap-range branch:** YES [STATIC]. `genesistan_hook_3ad44_dispatch` branches on `A0 ∈ [0xC00000, 0xC10000)` to `.Lhook_3ad44_tilemap → bsr genesistan_hook_tilemap_bg_fill` (`pc090oj_hooks.s:361-365, 398-400`).

**Q2 — FG (A0=0xC08100): writes `staged_fg_buffer`?** **NO** [STATIC]. `bg_fill`'s second gate `cmpi.l #0xC04000,%d2 ; bhs .Lbg_fill_done` rejects `0xC08100` (≥ 0xC04000) → immediate no-op. The FG clear writes nothing — not `staged_fg_buffer`, not anywhere. The FG clear is **dropped**.

**Q3 — BG (A0=0xC00100): writes `staged_bg_buffer`?** **YES** [STATIC]. `0xC00100 ∈ [0xC00000, 0xC04000)` → accepted. Offset = `(0xC00100 − 0xC00000) >> 2 = 0x40` cells (the 0x100 page offset preserved), row/col computed, written to `staged_bg_buffer`; loop runs `d6=d1=1900` longwords (`0xC00100 + 1900*4 = 0xC01EB0 < 0xC04000`, so the full extent fits). The 1900-extent is handled for BG.

**Q4 — fill value 0x20 translated?** **YES** (for BG) [STATIC]. `d0=0x00000020` is consumed as a PC080SN tile cell: `andi.w #0x3FFF,%d3 → tile_vram_lut[32]`, plus attr bits via `attr_lut`, producing the staged blank-cell — same translation as `cwindow_clear`. (N/A for FG, which is dropped before this.)

**Q5 — dirty marking?** BG: **YES** (`bset %d5, bg_row_dirty` per row). FG: **N/A / NO** — the FG clear is dropped before any write, so `fg_row_dirty` is not marked. [STATIC]

**Q6 — Bug classification: (b) hook reached but writes wrong/no staging range.** [STATIC] The dispatch reaches `genesistan_hook_tilemap_bg_fill` for the FG clear, but that helper is BG-only (range `[0xC00000,0xC04000)`, target `staged_bg_buffer`, `bg_row_dirty`); the FG clear (A0=0xC08100) is rejected and does nothing. The BG attract clear works; the **FG attract clear is silently dropped → `staged_fg_buffer` is never cleared at this boundary → additive FG text** (matching the symptom). Not (a) — the hook IS reached. Not (c) — BG stages+dirties correctly. Not (d) — the FG failure is right here. Not (e) — statically determinable.

---

## Summary table

| Aspect | BG (A0=0xC00100) | FG (A0=0xC08100) |
|---|---|---|
| Reaches `bg_fill` | yes | yes (but rejected) |
| Stages buffer | **staged_bg_buffer — YES** | **staged_fg_buffer — NO (dropped)** |
| 0x100 page offset preserved | YES (cell 0x40) | N/A (dropped) |
| 1900-longword extent | YES | N/A (dropped) |
| 0x20 blank translated | YES | N/A (dropped) |
| Dirty marked | bg_row_dirty — YES | fg_row_dirty — NO |

---

## Recommended fix target [STATIC-justified]

**Fix locus:** the dispatch tilemap branch `.Lhook_3ad44_tilemap` (`pc090oj_hooks.s:398`) + an FG-fill helper. The branch must split on `A0`: BG C-window `[0xC00000,0xC04000)` → `genesistan_hook_tilemap_bg_fill` (unchanged); FG C-window `[0xC08000,0xC0C000)` → a **mirror FG fill** that uses `ARCADE_PC080SN_CWINDOW_BASE_FG (0xC08000)`, `staged_fg_buffer`, and `fg_row_dirty` (identical structure to `bg_fill`, only the base/buffer/dirty-flag differ). Equivalently, generalize `bg_fill` to select base/buffer/dirty-flag from `A0`. This faithfully reproduces the arcade's FG clear (A0=0xC08100, 1900 longwords, fill 0x20, starting cell 0x40 → FG `0xC08100..0xC09EB0`) into `staged_fg_buffer` with dirty marking, so the VBlank FG commit propagates the cleared cells.

**Scope: FG+BG** (BG already correct; the fix ADDS the missing FG path — do not touch the working BG path). Do not over-clear: preserve the 0x100 (cell-0x40) page offset and the 1900-longword extent; the leading 0x100 region of each page is intentionally left uncleared by the arcade (the producer redraws from cell 0x40 onward).

**Safe to hand to Cody: YES** [INFERENCE, high-confidence]. The defect is precisely localized (FG clear dropped because the dispatch routes FG to BG-only `bg_fill`), and the fix mirrors an existing, working helper. Byte-size note: adding an FG-fill helper + a dispatch branch grows the Genesis-native region → shifts subsequent `runtime_genesis_pc` addresses and `total_genesis_bytes_covered`, requiring the standard invariant-update / re-relocation handling (OPEN-016 class). Cody should carry that invariant pre-authorization.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 (active — additive FG text root cause proven: FG attract clear dropped by BG-only `bg_fill`; fix locus named; not closed), OPEN-016 (context — same staging/relocation class), OPEN-015 (not touched).
- New issues opened: NONE. Issues closed: NONE.
- Intentionally deferred: implementation, exception/OPEN-015/OPEN-017, sprites/palette/logo/sword, generalization beyond this boundary.

## KNOWN_FINDINGS impact

**Option C — proposed refinement to KF-028** (assess only; not edited; Tighe/Chad Sr. approve). Proposed addition:

> Build 0094 attract FG additive-text root cause: the arcade attract page-clear (clear-path `0x3B064`/`0x3B074`, fill loop arcade `0x3AD44` → patched `0x3AF44` = `jsr genesistan_hook_3ad44_dispatch` `0x71618`) routes BOTH the BG clear (A0=0xC00100) and FG clear (A0=0xC08100) to `genesistan_hook_tilemap_bg_fill`, which is BG-only (range `[0xC00000,0xC04000)`, `staged_bg_buffer`, `bg_row_dirty`). The FG clear (A0=0xC08100 ≥ 0xC04000) is rejected and dropped, so `staged_fg_buffer` is never cleared between attract pages → additive FG text. (Distinct from `cwindow_clear`/`0x710D8`, which is the game-scene clear and correctly does not fire here.) Fix: dispatch the FG C-window range `[0xC08000,0xC0C000)` to an FG-fill mirror (`staged_fg_buffer`, base `0xC08000`, `fg_row_dirty`). Confidence STRONG (source/disasm proven; arcade-runtime-corroborated intent).

## STOP triggered

NO.
