# Andy — Producer-Local Narrow FG Strip Presentation Path Design (Design / Static Only)

**Author:** Andy
**Date:** 2026-07-05
**Baseline:** Build 0138, `dist/rastan-direct/rastan_direct_video_test_build_0138.bin`, SHA256 `719a9af2e8a4afebed793af30687c19e31d6817ea0a8f50b71d9756988044615`.
**Authoritative mapping:** `build/rastan-direct/address_map.json`.
**Priors:** `Cody_pc080sn_operation_census.md`; `Cody_fg_vertical_strip_current_path_audit.md`; `Cody_fg_vertical_strip_same_frame_overlap_audit.md`.
**Scope:** DESIGN + static analysis only. No implementation/source/spec/tool/Makefile/ROM/build/bookmark/runtime/VBlank-order/DISPLAY-OFF/frame-pipeline changes. All arcade↔Genesis mappings from `address_map.json`, no arithmetic. Labels **[OBS]** verified from Build 0138 source this task; **[EVID]** Cody trace; **[INT]** interpretation.

---

## 1. Executive decision

**Outcome A — implementation-ready**, with one mandatory **geometry correction**: the selected producer does **not** write four *contiguous* 16-word spans. It writes **16 columns at column-stride 4** (per descriptor `dest += 0x400`, `col d2 = (d2+4)&0x3F`), offset by the strip index — an **every-4th-column × 4-contiguous-row interleave** (16 vertical 4-cell runs). The narrow presentation is therefore **4 strided runs (VDP autoincrement `0x08`, 16 words each) = 64 words**, replacing the current 4 full-row commits (256 words). Design = **Option 1 (fixed-capacity descriptor list)**, 2-byte descriptor `{base_row, col_offset_x2}`, capacity 64, read final values from `staged_fg_buffer`, suppress this producer's broad `fg_row_dirty`, two-phase append-or-broad-fallback, no frame-model change. **75% presentation-word reduction (256→64) for one valid strip.**

> **CORRECTION (2026-07-05): narrow eligibility requires `col_offset_x2 + 120 < 128`.**
> The producer masks each descriptor column with `andi.w #0x003F,%d2` (source line 400), so a producer column that reaches 64 **wraps back to the start of the same logical Plane-A row** (`& 0x3F`). The narrow presenter's linear byte progression `col_offset_x2 + 8*k` instead **spills into the following row**. These are equivalent **only when the whole run stays within the 64-cell row**, i.e. `col_offset_x2 + 120 < 128` (equivalently `base_col + strip ≤ 3`). This first implementation therefore uses the **strict within-row eligibility `col_offset_x2 + 120 < 128`**; every shape with `col_offset_x2 + 120 >= 128` (any wrap/spill) uses the **broad-row fallback** `fg_row_dirty |= pending_rows`. No masked per-word addressing, no wrapped-segment split, no larger descriptor. The earlier `>= 256` threshold and any claim that "linear spill into the next row is equivalent to the producer's masked-column behavior" are **removed as incorrect**.

---

## 2. Evidence basis

- **Census [EVID]:** arcade `0x0559B8`/`0x055A06` FG vertical-strip family = 163,072 raw PC080SN writes = 36.273% of manual gameplay traffic; 1,274 strip units @ 128 raw words; up to ~5 units/frame.
- **Current-path audit [EVID]:** static shape = 16 descriptors × 4 row-cells = 64 composed cells; 4 dirty rows; general FG commit = 64 words/dirty row → **256 words for 64 cells = 4.0×**. General commit is CPU (`0x0701B2 move.w (a0)+,0x00C00000`), not DMA.
- **Overlap audit [EVID]:** selected producer reached in native frame 1133; **64 wrapper entries, 1 valid (all 16 descriptors valid), 63 range-rejected**; valid strip did 64 staging stores + 64 `fg_row_dirty` sets → mask `0x0000000F` (rows 0..3); next VBlank committed rows 0/1/2/3 at VRAM 0xE000/E080/E100/E180; **no other FG producer shared those rows before VBlank** (BG blockcopy `0x070640` touches `staged_bg_buffer` only). → broad-row suppression is safe for this producer.
- **Geometry [OBS+EVID]:** valid entry `dest_fg=0x00C08000, strip=0` → base cell index 0 → base_row 0, base_col 0. VBlank row-0..3 first words `0x60D8, 0x60DC, 0x60E0, 0x60E4` (Δ=4) = descriptor-0's single 4-row vertical run in **column 0**; the other 48 columns of each row were stale — proving the written columns are **every 4th (0,4,8,…,60)**, not contiguous.

---

## 3. Execution-state limitation

Build 0138 does **not** reach playable Genesis gameplay. The overlap evidence is from the **frontend/attract** sequence (state `2/2/5`), one native frame, one valid strip (strip 0). It is **not** gameplay/Stage-1/validation. The design must stay safe if later execution contains additional FG producers or multiple valid strips per frame (handled in §15/§18). The original arcade census included partial Stage-1; the Build 0138 trace did not.

---

## 4. Selected producer contract [OBS `tilemap_hooks.s:243-402`; `address_map.json`]

- **arcade_pc 0x055990 → runtime_genesis_pc 0x055B90** (`patched_site`), replacement bytes `4eb9000703ea4e71…` = `jsr 0x0703EA` + NOP pad → **genesistan_hook_tilemap_fg** (`runtime_genesis_pc 0x0703EA`, `genesis_only`). Wrapper bytes are UNCHANGED by this design.
- **Callers:** the arcade FG dispatcher around `arcade_pc 0x055948` (selects `0x055968`/`0x055990` via `%a5@(4264)`); it invokes the wrapper repeatedly per frame (64× observed, mostly out-of-range).
- **Entry/return:** `movem.l %d0-%d7/%a0-%a6` save/restore → all caller registers preserved; `rts`.
- **Input state:** `%a5=0xFF0000`; strip index `%a5@(STRIP_INDEX_FG_OFFSET=4298)`→`d7`; FG dest `%a5@(DEST_FG_OFFSET=4260)`→`d5`; descriptor list `%a5@(DESC_FG_LIST_OFFSET=4096)`; ROM base `0x00000200`; LUTs `genesistan_pc080sn_tile_vram_lut`/`_attr_lut`; scene A0 range for the preamble slow path.
- **Output/updated state:** on valid completion stores updated `d5` → `%a5@(4260)` (`+0x400` per descriptor); writes `staged_fg_buffer` + `fg_row_dirty`.
- **Preserved/clobbered:** externally all regs preserved (movem); internally d0-d7/a0-a6 used.
- **Destination pointer source:** `%a5@(4260)` (d5). **Strip index source:** `%a5@(4298)` (d7). **Descriptor source:** list at `%a5@(4096)`, each entry a ROM offset; tile words read at `ROM_BASE + desc_offset + strip*2`.
- **Validation rules:** dest masked `&0xFFFFFF` ∈ `[CWINDOW_BASE_FG (0xC08000), +CWINDOW_BYTES (…0xC0C000))` AND 4-byte aligned (`d4&3==0`); per-descriptor: `btst #0` clear, `≤0x0005FFFC`, tile-word `≤0x7FE0`.
- **Range-rejection:** dest fail → `.Lfg_hook_dest_invalid` (runtime `0x07057C`) → no staging, return. (63/64 observed.)
- **Successful completion point:** `0x070572` (valid-done) after all 16 descriptors.
- **Staging write:** `0x070532` `move.w %d3, 0(%a6,%d0.w)` with `d0 = base_row*128 + 2*(d2+strip)`; one composed word/cell.
- **Dirty write:** `0x07053E` `move.l %d0, fg_row_dirty` after `bset %d1` per cell.
- **Row progression:** inner row loop 4× (`d4=3..0`), `d1 = (d1+1)&0x1F` → 4 **contiguous** rows base_row..base_row+3 (mod 32); each marked dirty.
- **Column progression:** per descriptor `d2 = (d2+4)&0x3F`, `d5 += 0x400` → **columns base_col + 4·k (k=0..15)**, offset by strip → **stride-4 every-4th-column**.
- **Width 16 invariant:** the descriptor loop is fixed `moveq #15` (16 iterations) → 16 columns. **Height 4 invariant:** row loop fixed `moveq #3` (4 rows). Both **invariant** for a fully-valid invocation. A per-descriptor invalid entry (`.Lfg_hook_invalid_desc`) skips its column (advances col by 4, writes nothing) → a **gap**; not the proven full shape (handled by §14 fallback).
- **Can a valid op wrap a Plane-A row?** The producer masks `d2 = (d2+4)&0x3F` per descriptor (line 400), so once `base_col + 4k` reaches 64 the producer column **wraps to the start of the same row**; the added strip can further push the final staging column past 63. Either way the producer's cells for such a run land at columns the **linear** presenter formula does not reproduce (the linear formula spills into the next row instead of wrapping). Observed base_col=0,strip=0 → cols 0..60, **no wrap**. Therefore a run is narrow-eligible **only when it cannot wrap or spill**: `col_offset_x2 + 120 < 128` (`base_col + strip ≤ 3`); all other shapes take the broad fallback (§14/§17). The narrow linear formula is exact **only** under this within-row condition.
- **Multiple valid ops/frame:** structurally possible (arcade renders strips 0..3, and census shows multi-unit frames); **not observed** in Build 0138 (1 valid). **Max statically-possible valid ops before VBlank:** bounded by the per-frame wrapper-call count (64 observed); true absolute bound needs arcade-loop analysis → design caps at 64 with broad fallback.
- **Order between valid ops:** irrelevant to final pixels — every commit reads *final* `staged_fg_buffer` values (§15/§18).
- **Can valid regions overlap?** Different strips write disjoint columns of the same rows; the same strip re-run overwrites its own cells with final values. Overlap is value-consistent.
- **Can later same-frame producers update the same staged cells?** Yes in principle (other FG hooks). Reading *final* staging at VBlank absorbs any later update (§10/§15).

**Proven vs assumed:** PROVEN — addresses/mappings, 16×4-with-stride-4 geometry, contiguous rows, staging/dirty stores, single-strip dirty ownership. ASSUMED (static, not runtime-observed in 0138) — multi-strip-per-frame behavior and narrow-per-strip coverage correctness (argued by construction in §15/§18).

---

## 5. Interpretation of 64 entries and 63 rejections

The arcade FG dispatcher calls the wrapper **64 times in one frame**, walking progressively out-of-range destinations (`0xC0C000 … 0xD04000`). Structurally this is a **dispatcher/plane-scan pattern**: one logical FG update attempt is issued against many candidate destinations/pages; only the destination that lands in the FG C-window `[0xC08000,0xC0C000)` passes the range gate (1 valid), the other 63 are range-rejected before any staging write. **The 64 wrapper entries are NOT 64 valid queue candidates** — at most a small number are valid FG strips (1 observed). The queue is fed only by the valid-completion path.

---

## 6. Output-shape proof

One fully-valid invocation = **16 vertical runs** (one per descriptor), each **4 contiguous rows** (base_row..base_row+3, mod 32) in a **single column**; consecutive runs step the column by **+4** (offset by strip) → columns `base_col+strip, +4, …, +60`. Total **64 cells** occupying **4 rows × 16 every-4th columns**. Staging byte offset of cell (row r, run k) = `((base_row+r)&0x1F)*128 + 2*(base_col+strip+4k)`. `staged_fg_buffer` and Plane A share this exact linear layout (128 bytes/row, 2 bytes/cell, row-major, base VRAM 0xE000).

---

## 7. Design alternatives considered

- **Option 1 — fixed-capacity descriptor list:** append `{base_row, col_offset_x2}` per valid full-shape strip; VBlank reads final staging and commits exact strided spans. **CHOSEN** — smallest, matches proven shape, no merging assumptions, exact ordering-independent output.
- **Option 2 — producer-specific merged pending state:** rejected — merging multiple strips into one representation requires proving no operation/order loss across strips; not statically established (multi-strip unobserved). Higher risk, no size win over a 2-byte list.
- **Option 3 — precise span masks (row+horizontal extent):** rejected — the extent is a strided (every-4th) set, so a "span mask" is no simpler than the descriptor and less exact than reading final staging.

No general graphics-job system, no operation-type field, no speculative fields.

---

## 8. Selected producer-local design

Append, on each **fully-valid** invocation, one 2-byte descriptor to `fg_narrow_desc_table[fg_narrow_desc_count++]`, and **suppress** this producer's broad `fg_row_dirty` writes. At VBlank, a new `vdp_commit_fg_narrow_strips` reads each descriptor, and for its 4 rows emits a 16-word strided (autoinc `0x08`) run sourced from `staged_fg_buffer` to Plane A. `staged_fg_buffer` remains the authoritative composed state; the narrow path changes only the *presentation transfer* and the dirty accounting for this producer.

---

## 9. Producer transaction ordering

Exact sequence for one invocation (two-phase success/fallback):

1. **Validate dest** (range + 4-align). Fail → `.Lfg_hook_dest_invalid` (unchanged) → return, no staging, no descriptor.
2. Capture `base_row = d1_init`, `col_offset_x2 = 2*(d2_init + d7)` into locals (WRAM temp / preserved reg). Init `any_invalid_desc = 0`, `pending_rows = 0`.
3. **Staging loop** (unchanged staging stores at `0x070532`): write all valid descriptors' cells to `staged_fg_buffer`. **Replace** the in-loop `fg_row_dirty` bset (`0x070536/0x07053E`) with `bset %d1` into the **local `pending_rows`** (no `fg_row_dirty` write yet). On a per-descriptor invalid entry (`.Lfg_hook_invalid_desc`), set `any_invalid_desc = 1`.
4. **Decide:** `narrow_eligible = (any_invalid_desc == 0) AND (col_offset_x2 + 120 < 128 strict within-row guard, §14/§17) AND (fg_narrow_desc_count < CAP)`.
5. **If narrow_eligible:** write descriptor **contents** `{base_row, col_offset_x2}` to `table[count]`, **then** `count += 1` (content-before-count). Do **not** write `fg_row_dirty`.
6. **Else (fallback):** `fg_row_dirty |= pending_rows` (broad). Do **not** append a descriptor.
7. Update `%a5@(4260)` dest state (unchanged), `rts`.

This prevents: descriptor-for-incomplete-staging (staging precedes append); count-advance-before-content (content first); neither-nor-both (exactly one of append/broad); overflow drop (full → broad); partial-op-after-failure (invalid → broad, staging still committed). **Capacity is checked after staging, committed content-then-count** (no pre-reservation needed because staging is unconditional to `staged_fg_buffer`).

---

## 10. Descriptor byte layout

`fg_narrow_desc_table`: array of 2-byte descriptors.

| Offset | Width | Field | Meaning | Source | Valid range |
|---:|---:|---|---|---|---|
| +0 | 1 byte | `base_row` | starting Plane-A row of the 4-row runs | `d1` at loop entry (`(dest_idx)&0x1F`) | 0..31 |
| +1 | 1 byte | `col_offset_x2` | within-row **byte** offset of column-0 run = `2*(base_col+strip)` | `2*(d2_init + d7)` | 0..132 |

No tile payload, no operation-type, no width/height (invariant 16/4), no speculative fields. **Staging and VRAM coordinates derive from these two fields:** for run r∈0..3, k∈0..15 → `byte = ((base_row+r)&0x1F)*128 + col_offset_x2 + 8k`; **staging read** = `staged_fg_buffer + byte`; **VRAM write** = `0xE000 + byte`. One stored `col_offset_x2` suffices because the 16 columns are a fixed +4 (=+8 bytes) progression and the strip offset is folded in. This linear formula reproduces the producer's masked columns **only** under the narrow-eligibility guarantee `col_offset_x2 + 120 < 128` (§14): then `col_offset_x2 + 8k < 128` for all k, so the producer's `(base_col+4k)&0x3F` never wraps and no cell leaves row `(base_row+r)&0x1F` (staging and Plane A share the same 128-byte/row linear layout **within a row**; the correction forbids relying on cross-row spill equivalence).

---

## 11. Capacity calculation

- Static max valid ops/frame ≤ per-frame wrapper-call ceiling = **64** [EVID observed]; arcade census shows ≤~5 valid strip units/frame in gameplay.
- **Selected capacity: 64 descriptors.** Reasoning: equals the observed wrapper-call ceiling (so overflow is structurally improbable in the observed dispatch), comfortably above the ≤~5 census units, sized for unreached gameplay, and cheap.
- **Descriptor size:** 2 bytes. **Total:** `64*2 = 128` bytes table + `2` bytes count = **130 bytes** (+ 2-byte `fg_narrow_pending_rows` temp).
- **Alignment:** 2 (word). **Count width:** 16-bit (word). **Max representable count:** 65535 (bounded to CAP=64 by the overflow check). **Overflow detection:** `count >= 64` at §9.4 → broad fallback. **No-wrap guarantee:** count only increments on successful append and is reset to 0 once per VBlank (§19); it never exceeds CAP because the append is gated by `count < 64`.

---

## 12. WRAM allocation

Current Genesis BSS high-water ≈ `0x00FF7106` [OBS symbol.txt: `genesistan_scene_a0_hi` 0xFF7102]; free Genesis WRAM extends to the stack (~0xFFF800) ≈ **~34 KB**. New fields (append in the tilemap/FG `.bss`, linker-assigned; expected region ≈ 0xFF7108+):

| Symbol | Size | Align | Purpose |
|---|---:|---:|---|
| `fg_narrow_desc_table` | 128 B | 2 | 64 × `{base_row, col_offset_x2}` |
| `fg_narrow_desc_count` | 2 B | 2 | pending valid-strip count |
| `fg_narrow_pending_rows` | 2 B | 2 | producer-local row-bit accumulator (fallback) |

**Neighbors:** immediately above the existing `pc090oj_*`/scene BSS (≤0xFF7106); well below the stack. **Overlap proof:** total added = 132 bytes ≪ ~34 KB free; no existing symbol lies in the appended region; linker guarantees non-overlap. **Required symbols:** the three above (all `.global` as needed for cross-file reference between `tilemap_hooks.s` producer and `vdp_comm.s` presenter). If the build proves < ~8 KB stack margin remains → **blocked outcome** (not the case here).

---

## 13. Overflow fallback

If `fg_narrow_desc_count >= 64` at decision time (§9.4): **do not append**; instead `fg_row_dirty |= fg_narrow_pending_rows` (the exact 4 row bits this invocation would have set), preserving the current broad-row behavior. Guarantees: all `staged_fg_buffer` writes preserved (staging is unconditional); same broad rows set as the current path; no invalid/partial descriptor appended; no earlier descriptor overwritten; identical producer state contract (`%a5@(4260)` updated), `rts`. **Method: check-after-staging + content-then-count append** (chosen over pre-reservation because staging must occur regardless and the count is single-writer within the non-reentrant producer).

---

## 14. Unsupported-shape fallback

Any invocation that is not the proven full, non-wrapping 16×4 shape falls back to the **current broad path** (`fg_row_dirty |= pending_rows`, no descriptor):
- **any per-descriptor invalid** (`.Lfg_hook_invalid_desc` taken) → `any_invalid_desc=1` → broad (a gapped column set is not the proven shape).
- **any wrap/spill** — `col_offset_x2 + 120 >= 128` (i.e. `base_col + strip >= 4`) → broad. This is the decisive correction: the producer masks its column with `& 0x3F` (line 400), so a run reaching column 64 **wraps to the start of the same row**, which the narrow presenter's linear `col_offset_x2 + 8k` progression does not reproduce (it would spill into the next row). Only `col_offset_x2 + 120 < 128` guarantees no wrap and no cross-row spill, so only that range is narrow-eligible.
- Dest range/align failure is the pre-existing reject (not a fallback — no staging occurs).

No legitimate arcade operation is silently dropped: every case either narrow-commits (within-row) or broad-commits the same staged cells. Because the broad path uploads the full 64-cell rows exactly as Build 0138 does, wrapping operations are presented **identically to the current behavior** — no correctness regression, only no narrowing for those shapes.

---

## 15. Dirty ownership rules

- The producer **never** writes `fg_row_dirty` during the staging loop; it accumulates its 4 row bits in `fg_narrow_pending_rows` (local).
- **Narrow success:** `fg_row_dirty` is left untouched by this producer (narrow path owns presentation) — suppression is scoped to this producer's own rows.
- **Fallback (overflow/unsupported):** `fg_row_dirty |= pending_rows` (OR, never assign) — sets exactly the same bits the current path would, without disturbing other producers' bits.
- **Never** globally clear `fg_row_dirty`; **never** clear a bit set by another producer; **never** clear another producer's update. If another producer dirties a shared row, that bit remains set and the general commit uploads the full row (redundant with the narrow strided cells — same final staged values — which is safe).
- Reading **final** `staged_fg_buffer` at VBlank protects against later same-frame updates: whatever the last writer stored is what both narrow and broad commits upload.

---

## 16. Narrow VDP presentation algorithm

`vdp_commit_fg_narrow_strips` (new, `genesis_only`, in `vdp_comm.s`):
```
save regs (movem)
if fg_narrow_desc_count == 0: restore, rts
set VDP autoincrement reg 0x0F = 0x08        ; 4-cell horizontal stride
for i in 0 .. count-1:
    base_row      = table[i].base_row
    col_off_x2    = table[i].col_offset_x2
    for r in 0 .. 3:
        row  = (base_row + r) & 0x1F
        byte = row*0x80 + col_off_x2
        vdp_set_vram_write_addr(0xE000 + byte)    ; VRAM write-address command
        a0 = staged_fg_buffer + byte
        repeat 16: move.w (a0), VDP_DATA ; adda #8, a0   ; dest auto-advances +8
set VDP autoincrement reg 0x0F = 0x02        ; restore default
fg_narrow_desc_count = 0                      ; consume
restore regs (movem); rts
```
- **VDP address commands:** `4 rows × count` (one per run). **Words/run:** 16. **Total words:** `64 × valid_strip_count`.
- **Source progression:** `staged_fg_buffer + byte`, stride 8 bytes. **Destination progression:** VDP autoincrement `0x08` (4 cells). **Plane-A base:** 0xE000. **Row byte stride:** 0x80. **Autoincrement:** set 0x08, restore 0x02 (so the unchanged general FG/BG commits keep their word-sequential behavior).
- **Register use:** movem-preserved; a0=source, address-command regs, a data-port register. **State restoration:** autoinc reg restored to 0x02; no persistent VRAM latch assumptions leaked (each general-commit row re-issues its own address).
- **Transfer choice: CPU strided writes**, not DMA — the source is stride-8 in `staged_fg_buffer` (a memory-to-VRAM DMA reads contiguous source, so it cannot reproduce the strided source→strided dest without a contiguous copy step; 16 words is too small to warrant it). **Cycle/word reduction:** 256→64 committed words = **75%** fewer VDP data writes per strip.

---

## 17. Plane wrapping

A 16-word run occupies byte range `[row*0x80 + col_offset_x2, +120]`. **A run is narrow-eligible only when it stays entirely within one Plane-A row: `col_offset_x2 + 120 < 128`** (equivalently `base_col + strip ≤ 3`; always true for the observed base_col=0, strip=0). Under this condition the producer's masked column `(base_col+4k)&0x3F` never reaches 64, so no `& 0x3F` wrap occurs, and the linear presenter formula `col_offset_x2 + 8k` equals the producer's staging offset for every cell — byte-correct within the row.

**Wrapping is NOT handled by the narrow path and is NOT equivalent to a linear spill.** The producer's `andi.w #0x003F,%d2` (line 400) wraps an over-64 column back to the **start of the same logical row**; a linear byte progression that crosses 128 would instead write the **next row**. These place different cells, so the earlier "identical linear spill" claim is withdrawn. Any run with `col_offset_x2 + 120 >= 128` (`base_col + strip >= 4`) is therefore **routed to the broad-row fallback** (§14), which uploads the full 64-cell rows exactly as Build 0138 does — the wrapped columns are presented correctly by the existing full-row commit. There is **no first/second-segment split, no masked per-word addressing, and no larger descriptor** in this first implementation; the single within-row threshold fully specifies the behavior and leaves no wrap decision for Cody.

---

### 17a. Column-wrap static proof [OBS `tilemap_hooks.s`]

1. **Where the column is masked to `0x3F`:** `.Lfg_hook_desc_done`, **line 400** `andi.w #0x003F, %d2` (the `d2 += 4` at line 399 is immediately masked).
2. **After every descriptor?** YES. Valid descriptors reach `.Lfg_hook_desc_done` via `bra.s .Lfg_hook_desc_done` (line 391); invalid descriptors reach it by fall-through from `.Lfg_hook_invalid_desc` (lines 393-397). Both run lines 398-402, so `d2` is masked `&0x3F` after each of the 16 descriptor iterations. The per-cell staging column used in the offset is `d2 + strip` (lines 374-379: offset `= row*128 + 2*d2 + 2*strip`), with `d2` the masked value and `strip` added linearly.
3. **Exact sequence for starts 0,1,2,3,4** (start = `base_col + strip`, i.e. `col_offset_x2/2`; producer per-descriptor `d2_k = (base_col + 4k) & 0x3F`, staging column `= d2_k + strip`):
   - start 0 (base_col 0, strip 0): `d2_k = 0,4,…,60` (all ≤63, no mask effect); columns `0,4,…,60`; max byte `2*60=120 < 128`.
   - start 1 (base_col 1, strip 0): columns `1,5,…,61`; max byte `122 < 128`.
   - start 2: columns `2,6,…,62`; max byte `124 < 128`.
   - start 3: columns `3,7,…,63`; max byte `126 < 128`.
   - start 4 (e.g. base_col 4, strip 0): `d2_15 = (4+60)&0x3F = 64&0x3F = 0` → producer writes **column 0 of the same row**; the linear formula gives `col_offset_x2 + 8*15 = 8 + 120 = 128` = **row+1, column 0** — a different cell.
4. **Why starts 0–3 are non-wrapping:** `base_col + 4k ≤ start + 60 ≤ 63` for all k≤15, so `(base_col+4k)&0x3F = base_col+4k` (no mask change) and the final staging column `≤ 63` (max byte `≤ 126 < 128`) stays in the row.
5. **Why start 4 wraps on the 16th descriptor:** at k=15, `base_col + 60 = 64`, and `64 & 0x3F = 0`, so the producer's 16th column resets to 0 within the same row instead of advancing to 64.
6. **Why the linear VBlank formula is safe only for starts 0–3:** the linear formula never applies `& 0x3F`; it equals the producer's masked offset iff `base_col + 4k` never reaches 64 (k≤15 ⇒ `base_col ≤ 3`) **and** the run never spills the 128-byte row (`start ≤ 3`). The single condition `col_offset_x2 + 120 < 128` (`start ≤ 3`) enforces both.
7. **Why broad fallback exactly preserves current presentation for wrapping cases:** for `start ≥ 4` the invocation still writes all its cells to `staged_fg_buffer` (staging is unchanged), and the fallback ORs the same 4 row bits into `fg_row_dirty`. The unchanged `vdp_commit_fg_strips_if_dirty` then uploads the full 64-cell rows from `staged_fg_buffer` — byte-for-byte the Build 0138 behavior. The wrapped cells are thus presented correctly by the existing full-row commit; the only difference vs a hypothetical narrow path is the absence of narrowing, not any pixel change.

## 18. Multiple-operation behavior

- **Processing order:** append order (0..count-1); correctness-independent because every run reads **final** `staged_fg_buffer`.
- **Overlap:** descriptors may target the same rows (different strips = disjoint columns) or re-target (same strip, later value) — all resolve to the final staged value; redundant same-value writes are safe.
- **Later descriptors "win":** yes, implicitly, via final staged values (no explicit last-writer logic needed).
- **Dedup/merge:** **not implemented** — not worth the code; duplicate strided runs write identical final values.
- **Count reset:** once, at the end of `vdp_commit_fg_narrow_strips` each VBlank.

Per-strip narrow commit is correct by construction: `staged_fg_buffer` changes only via producer hooks; each valid strip narrow-uploads exactly the cells it changed; unchanged interleaved columns retain their correct VRAM from the frame their strip last ran; any row also touched by another producer is additionally covered by the general broad commit.

---

## 19. VBlank insertion point [OBS `vdp_comm.s:159-186`]

Current FG phase: `… bsr vdp_commit_bg_strips_if_dirty ; bsr vdp_commit_fg_strips_if_dirty ; bsr vdp_commit_sprites_vram …` (inside DISPLAY_OFF).

- **Insert `bsr vdp_commit_fg_narrow_strips` immediately BEFORE `bsr vdp_commit_fg_strips_if_dirty`.** Function immediately before = `vdp_commit_bg_strips_if_dirty`; immediately after = `vdp_commit_fg_strips_if_dirty` (unchanged, still commits all *other* FG producers' broad rows).
- **Narrow commits before the general FG row commit.** **Descriptor count clears at the end of the narrow routine** (before the general commit). Order is correctness-neutral (redundant same-value on shared rows); narrow-before-broad is chosen to group the new logic and guarantee autoincrement is restored to `0x02` before the unchanged general routine runs.
- **Register preservation:** narrow routine movem-preserves d0-d7/a0-a6. **VDP state on entry:** display off, autoinc 0x02. **On exit:** autoinc restored 0x02; `fg_narrow_desc_count=0`.
- Do **not** reorder any other phase; do **not** move DISPLAY_OFF/ON; broad FG commit for all other producers is preserved intact.

---

## 20. Register and VDP-state contracts

- **Producer (`genesistan_hook_tilemap_fg`):** unchanged external movem contract; internally adds local `pending_rows`/`any_invalid_desc` tracking (reuse a preserved data reg or the `fg_narrow_pending_rows` WRAM temp) and the two-phase decision; **staging stores byte-identical**; net effect on caller regs = none.
- **Narrow presenter:** movem-preserves all; sets/restores VDP autoinc reg 0x0F (0x08→0x02); uses VDP_CTRL address commands + VDP_DATA writes; leaves display state untouched.
- **Invariant used:** `staged_fg_buffer` (0xFF501A) ↔ Plane A (0xE000) identical linear layout (0x80/row, 2/cell); FG dirty owner `fg_row_dirty` (0xFF4006) untouched on narrow success.

---

## 21. Exact source-file change plan

**`apps/rastan-direct/src/tilemap_hooks.s` — `genesistan_hook_tilemap_fg` (0x0703EA):**
- ADD: capture `base_row`, `col_offset_x2 = 2*(d2_init + d7)` before the descriptor loop; local `any_invalid_desc`.
- REMOVE: in-loop `fg_row_dirty` read/bset/store (current `0x070536/0x07053E`).
- ADD: in-loop `bset %d1` into local `pending_rows`; in `.Lfg_hook_invalid_desc`, set `any_invalid_desc=1`.
- ADD (after loop, at valid-done `0x070572`): decision (§9.4–9.6) — content-then-count append to `fg_narrow_desc_table`/`fg_narrow_desc_count` with dirty suppression, else `fg_row_dirty |= pending_rows`.
- New symbols referenced: `fg_narrow_desc_table`, `fg_narrow_desc_count`, `fg_narrow_pending_rows`, `FG_NARROW_CAP=64`.
- Register contract: unchanged externally; fallback branch = broad OR.

**`apps/rastan-direct/src/vdp_comm.s`:**
- ADD routine `vdp_commit_fg_narrow_strips` (§16).
- ADD `bsr vdp_commit_fg_narrow_strips` in `_vblank_service` immediately before `bsr vdp_commit_fg_strips_if_dirty` (§19). `vdp_commit_fg_strips_if_dirty` itself UNCHANGED.
- Uses existing `vdp_set_vram_write_addr`, `vdp_set_reg` (for autoinc), `VDP_DATA`, `staged_fg_buffer`.

**WRAM `.bss`** (in whichever existing FG/tilemap `.bss` owns `staged_fg_buffer`/`fg_row_dirty`): add the three symbols (§12). No new architecture file.

**`apps/rastan-direct/src/boot/boot.s`:** clear `fg_narrow_desc_count = 0` (and `fg_narrow_pending_rows`) in the existing bootstrap-clear path.

No spec (`specs/rastan_direct_remap.json`) change — the `0x055990` mapping and the `0x055B90` wrapper bytes are untouched.

---

## 22. Expected opcode/address-map effects

- **`0x055B90` wrapper bytes: UNCHANGED** (`jsr 0x0703EA` + pad).
- **Only Genesis-only bodies change:** `genesistan_hook_tilemap_fg` grows; `_vblank_service` gains one `bsr`; new `vdp_commit_fg_narrow_strips` added. All `genesis_only`.
- **No `patched_site` length change** (no arcade-mapped site edited).
- **`address_map.json` category changes:** `genesis_only` region grows; `total_genesis_bytes_covered` increases by the helper/routine growth (pre-authorized byte-delta class). **No-change regions:** all `patched_site`/`arcade_copy` entries, `opcode_replace` count (stays **133**).
- **Predictable/pre-authorized byte-delta:** growth of `genesistan_hook_tilemap_fg`, `_vblank_service`, and the new FG-narrow routine; new `.bss` symbols.
- **STOP-triggering byte-delta:** any change to `opcode_replace` count, any `patched_site`/`arcade_copy` byte change, or any change to the `0x055B90` wrapper. Do not guess final addresses for the new Genesis-only code — the linker fixes them.

---

## 23. Expected performance reduction

Per one valid strip:

| | current | proposed |
|---|---:|---:|
| VDP address setups | 4 | 4 (× strips) + 1 autoinc set + 1 restore |
| committed words | 256 (4×64) | 64 (4×16) |

- **Word reduction:** 256 → 64 = **192 fewer (75%)**.
- **Descriptor-management overhead:** ~a few instructions/invocation (capture + decision + 2-byte append) + a small per-descriptor VBlank loop.
- **VDP address-command overhead:** unchanged count per row (4/strip) + one autoinc set/restore per VBlank.
- **Net benefit:** strong for the common case (75% fewer FG-strip data writes); **CPU strided writes** selected (not DMA).
- This alone does **not** fix the full black horizontal band; it reduces one producer's FG presentation cost within the existing frame model.

---

## 24. Cody acceptance criteria

- Same 64 `staged_fg_buffer` values as Build 0138 (staging stores byte-identical).
- Same producer state updates (`%a5@(4260)` progression) and same range-reject behavior (63/64).
- Descriptor appended only for complete valid 16×4 invocations (content-then-count).
- Zero `fg_row_dirty` writes by this producer on narrow success.
- Broad fallback (`fg_row_dirty |= pending_rows`) on capacity overflow, on any invalid descriptor, and on any wrap/spill shape (`col_offset_x2 + 120 >= 128`, i.e. `base_col + strip >= 4`); narrow path taken only when `col_offset_x2 + 120 < 128`.
- All other FG dirty writers unchanged; `vdp_commit_fg_strips_if_dirty` unchanged.
- Narrow commit = 4 strided (autoinc 0x08) 16-word runs per descriptor = 64 Plane-A words/strip, VRAM 0xE000+byte matching staging byte.
- `fg_narrow_desc_count` consumed (reset 0) each VBlank; no cross-frame descriptor lifetime.
- No direct active-display VDP writes; no frame-model change; no VBlank-order change; no DISPLAY_OFF/ON movement.
- `opcode_replace`=133; address-map coverage complete; only `genesis_only` growth.
- Frontend/attract progression reaches at least the same point as Build 0138 (state `2/2/5`). **Gameplay validation not required** (unreachable).

---

## 25. Revert criteria

Revert if any of: `staged_fg_buffer` result mismatch vs 0138; rejected-path behavior change; any lost FG update (missing cells vs full-row baseline); a cleared dirty bit belonging to another producer; descriptor count exceeding CAP or overrunning the table; a descriptor surviving into an unintended frame; VDP state corruption (autoinc not restored / wrong Plane-A rows); any new exception/crash; frontend/attract regression; unexpected `address_map.json` change (opcode_replace≠133 or any patched_site byte change); or the change proving to require the one-frame-lag pipeline.

---

## 26. Outcome

**Outcome A — corrected implementation-ready design.** The `< 128` within-row eligibility rule resolves the column-wrap problem without any new dependency: narrow-eligible runs (`col_offset_x2 + 120 < 128`, `base_col + strip ≤ 3`) provably match the producer's masked columns (§17a), and every wrap/spill shape is presented by the unchanged broad path exactly as Build 0138 (§14/§17). All required elements remain resolved: geometry correction (§1), transaction ordering (§9), descriptor (§10, unchanged 2 bytes), WRAM (§12, unchanged), capacity (§11, unchanged 64), overflow (§13), unsupported/wrap fallback (§14/§17), dirty ownership (§15), VBlank insertion (§19), overlap/multiple-op (§15/§18), VDP transfer shape (§16, unchanged autoinc 0x08 CPU strided), register/VDP contract (§20), mapping effects (§22), acceptance/revert (§24/§25), column-wrap static proof (§17a). The single-strip dirty-ownership dependency is resolved (overlap Outcome A); multi-strip correctness holds by construction (§18). No additional static or runtime dependency (not Outcome B).

---

## 27. Ordered Cody implementation checklist

1. Verify Build 0138 baseline SHA `719a9af2…044615`; verify `0x055990→0x055B90`, `0x0703EA`, `0x070532/0x07053E` from `address_map.json`.
2. Add `.bss` symbols `fg_narrow_desc_table` (128 B), `fg_narrow_desc_count` (2 B), `fg_narrow_pending_rows` (2 B); `.global` as needed; `FG_NARROW_CAP=64`.
3. Clear `fg_narrow_desc_count`/`fg_narrow_pending_rows` in the boot bootstrap-clear.
4. In `genesistan_hook_tilemap_fg`: capture `base_row`/`col_offset_x2`; replace in-loop `fg_row_dirty` bset with local `pending_rows`; flag `any_invalid_desc`; keep staging stores identical.
5. After the descriptor loop, implement the two-phase decision (§9.4–9.6): narrow append (content-then-count, suppress dirty) only when `any_invalid_desc==0 AND col_offset_x2 + 120 < 128 AND fg_narrow_desc_count < 64`; otherwise broad fallback (`fg_row_dirty |= pending_rows`). Do NOT split or mask-address wrapping runs.
6. Add `vdp_commit_fg_narrow_strips` (§16): autoinc 0x08; per descriptor, 4 rows × 16 strided writes from `staged_fg_buffer` to `0xE000+byte`; restore autoinc 0x02; reset count.
7. Insert `bsr vdp_commit_fg_narrow_strips` immediately before `bsr vdp_commit_fg_strips_if_dirty` in `_vblank_service`; leave the general FG commit and all other phases unchanged.
8. Build; confirm `opcode_replace`=133, only `total_genesis_bytes_covered` grows (update the two canonical invariant tools if the gate stops), `0x055B90` bytes unchanged.
9. Static-verify: staging stores identical; narrow routine emits 64 words/strip at the strided VRAM offsets; count reset each VBlank.
10. Runtime (frontend/attract, MAME + native debugger; user handles BlastEm visual): reach ≥ state `2/2/5`; confirm the selected valid strip produces the same staged values, appends one descriptor, sets no `fg_row_dirty`, and its 4 rows commit as 4 strided 16-word runs; no ghost/lost cells; no other FG producer's dirty bit cleared.
11. Apply revert criteria (§25) on any mismatch.

---

## AGENTS_LOG

(one concise entry appended)

**Outcome:** A (implementation-ready, with mandatory geometry correction). **Confirmation:** no source, spec, tool, Makefile, ROM, build, bookmark, runtime, VBlank-order, DISPLAY_OFF/ON, or frame-pipeline change was made — design document only.
