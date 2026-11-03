# Andy — Build 0119 Item-Page Strip Destination Pointer / HV Write (Design Only)

**Author:** Andy
**Date:** 2026-06-29
**Baseline:** Build 0119 (`dist/rastan-direct/rastan_direct_video_test_build_0119.bin`, SHA256 `e1d74a2514a2142a1ad56b54bedc49c6d39570ee5d5ca9da1bb7c9f9ce8d46c4`). rastan-direct.
**Scope:** DESIGN only. No source/spec/tool/Makefile/ROM/build/implementation; no runtime probing (existing evidence + static ROM/JSON only). Output: this doc + one AGENTS_LOG entry. Code PC via `address_map.json`; work-RAM via KF-036. Labels: **[OBS]** verified this task; **[CODY]** Cody evidence; **[INT]** interpretation. **Class: KF-032** (raw PC080SN write bypassing Genesis staging) — destination side, item-page BG strip producer; same family as the C00828 item-desc producer route (OPEN-022) and the high-score producer route. Predecessor/fixed layers: KF-036 (slot rebase), KF-028/OPEN-016 (source + strip-pointer relocation, Build 0118/0119).

---

## Phase 0 — Baseline

**Classification:** EXTENDING (KF-032 raw-PC080SN-write; item-page BG strip producer destination side). **Contradiction:** NONE. Build 0119 fixed the source/strip-pointer relocation (`0x00FF1100 = 0x0000D31C`, old `0x55E8E` ADDRESS ERROR gone). The consumer now reaches its copy loop, but writes the strip **raw** to the PC080SN BG destination `0x00C00008` → on Genesis `0xC00008 & 0x1F = 8` = HV-counter/VDP port → BlastEm/Nomad-strict fatal.

**Authoritative writer [CODY]:** `runtime_genesis_pc 0x00055E7C` (`arcade_pc 0x00055C7C`), `move.w %a1@,%a0@+`, A0=`0x00C00008`, A1=`0x00FF1104` (value `0x0002`), A2=`0x0000D31C`, A5=`0x00FF0000`. (Cody did not reproduce the Exodus descending-fill pattern in MAME — not designed around.)

---

## 1. Destination pointer provenance + `0x00FF10F8` lifecycle [OBS]

`0x00FF10F8` (= `%a5@(4344)`, A5=0xFF0000) is the BG strip **destination cursor**, computed (not a raw literal, not a relocation gap):
```
0x55D76: d0 = %a5@(4340) << 6          ; row * 64
0x55D80: d1 = %a5@(4342) << 2          ; col * 4
0x55D82: d0 += d1
0x55D84: d0 += 0x00C00000              ; d0 = 0x00C00000 + row*64 + col*4  (PC080SN BG C-window address)
0x55D8A: %a5@(4344) = d0               ; 0x00FF10F8 = BG dest cursor
...
0x55E74: %a5@(4344) = a0               ; cursor advanced after the column copy
```
For the crash, `row*64 + col*4 = 8` → col 2, row 0 → `0x00C00008`. **The value is arcade-native and correct** — a computed PC080SN BG C-window destination (`base 0xC00000 + cell offset`). It is NOT a wrong seed, NOT an unrelocated pointer. [OBS]

---

## 2. `0x00C00008` semantic classification + plane / PC080SN region [OBS]

`0x00C00008` ∈ the **PC080SN BG C-window** `[0x00C00000, 0x00C04000)` (the project's BG tilemap window; FG is `[0x00C08000,0x00C0C000)`). `cell = (0xC00008 − 0xC00000) >> 2 = 2` → **BG row 0, col 2**. The seed adds the **BG base `0x00C00000`** (the item page's BG dest base, matching the `0x505EC` setup that wrote BG base `0xC00000` / FG base `0xC08000`). **Plane = BG (Plane B).** Not scroll RAM (`0xC04000+`), not FG. [OBS]

**Consumer write pattern (proven):** per iteration `d2` (0..63):
```
0x55E7C: move.w (a1),(a0)+   ; attr  = (0x00FF1104) = 0x0002   -> cell attr word @ a0;  a0 += 2
0x55E8A: a6 = a2 + d7        ; d7 = d2*32 + %a5@(4342)*2 ; a2 = 0x0000D31C (relocated strip src)
0x55E8E: d0 = (a6)           ; strip word (PC080SN tile code, e.g. 0x04A6)
0x55E90: move.w d0,(a0)      ; code  -> cell code word @ a0+2
0x55E92: a0 += 254           ; +256 total = +0x40 cells = +1 BG row (same col)
```
So each iteration writes **one BG cell** `{attr=0x0002, code=strip_word}` at (row d2, col 2); 64 iterations = a **vertical column** (col 2, rows 0–63). All raw PC080SN BG writes. `0xC00008 & 0x1F = 8` → HV port → fatal on the first write. [OBS]

---

## 3. Relationship to existing helpers [OBS]

`genesistan_hook_tilemap_bg_fill` already accepts a BG C-window HW address and stages a composed cell: `IN A0 = BG HW addr, D0 = (attr<<16)|code, D1 = count`; range-gate `[0xC00000,0xC04000)`; compose `tile_vram_lut[code & 0x3FFF] | attr_lut[attr-bits]`; store `staged_bg_buffer + row*128 + col*2`; `bset #row, bg_row_dirty`. The strip words (`0x04A6…`) are PC080SN tile codes → `tile_vram_lut`; attr `0x0002` → `attr_lut` (color bank 2). So each strip cell maps cleanly to one `bg_fill(A0=a0, D0=(0x0002<<16)|strip, D1=1)` call. This is the **same producer-route pattern** as the C00828 item-desc BG producer and the high-score FG producer (CLOSED-016 family) — a function-level hook on the producer that delegates per-cell to the existing fill helper. [OBS+INT]

---

## 4. Root cause [OBS]

The item-page BG strip producer (`0x55E5E`/`0x55E7A`) writes its 64-cell column **raw** to the PC080SN BG C-window (`A0 = 0x00C00008…`). On Genesis those addresses are the VDP mirror (`0xC00008 & 0x1F = 8` = HV port) → strict-emulator/HW fatal. The destination cursor and strip source are both correct (BG C-window address; relocated strip src `0xD31C`); the defect is purely the **un-routed raw PC080SN write** (KF-032), the destination-side analog of the already-fixed source-side relocations. This is **option (1)/(3)** from the task (route the strip writes through BG staging), **not** (2) a seed/populator bug, **not** (5) a wrong seed.

---

## 5. Proposed fix shape for Cody — **function-level producer hook routing each cell through `bg_fill` (option 1 + 3)**

Patch the strip producer entry `0x55E5E` and let a genesis_only hook reimplement the column copy, routing each cell through the existing BG staging helper:
- **Entry patch:** overwrite `0x55E5E` (8 bytes: `moveal %a5@(4344),a0` (4B) + `moveal #0x00FF1104,a1` (first 4B)) → `jsr genesistan_hook_itempage_strip_blit` (6B) + `rts` (2B). Byte-neutral; consumer body `0x55E66..0x55EA0` becomes dead (no external branch targets it; the inner loop `0x55E7A` is only `bsr`-reached from `0x55E70`, which is in the dead body). Caller (`0x55E52 bsr 0x55E5E`) reaches the hook → `rts` → caller.
- **Hook behavior (reproduces the producer with staging):**
  ```
  a0 = (0x00FF10F8)                 ; BG dest cursor (computed BG C-window addr; arcade-native)
  a2 = (0x00FF1100)                 ; relocated strip source (0xD31C; Build 0119)
  attr = (0x00FF1104).w             ; 0x0002 (cell attr / color bank)
  col  = (0x00FF10F6).w             ; %a5@(4342)
  for d2 in 0..63:
      d7   = d2*32 + col*2
      code = (a2 + d7).w            ; strip word (PC080SN tile code)
      bg_fill(A0 = a0, D0 = (attr<<16)|code, D1 = 1)   ; compose + stage + dirty (NO raw write)
      a0 += 256                     ; next BG row, same col
  (0x00FF10F8) = a0                 ; write back advanced cursor (mirror 0x55E74)
  rts
  ```
- The cursor stays a **BG C-window address** (the hook passes it as `A0`; `bg_fill` decodes the cell `(A0−0xC00000)>>2` → row/col → `staged_bg_buffer`). **No raw write to `0x00C00008`.** The strip is staged to Plane B and committed at VBlank via `bg_row_dirty`.
- **Why this shape:** the destination is a per-cell BG producer writing distinct codes (not a single-value fill) → a function-level hook delegating to `bg_fill` per cell (CLOSED-016 family), not `bg_fill` called directly with a count. **Not** option 2 (the seed is correct). **Not** option 4 (replacing the cursor with a raw staging-buffer pointer bypasses the C-window decode and the architecture's HW-addr→staged-cell mapping; `bg_fill` is the sanctioned route). **Not** masking/suppression. **Not** chosen because prior fixes used hooks — chosen because the lifecycle is a raw per-cell BG producer.
- **Guard:** `bg_fill` range-gates `[0xC00000,0xC04000)`; if a future cursor walks out of the BG window, it NO-OPs (consistent with the existing helper). (Optionally the hook can fail-loud on out-of-BG-window `a0`; not required for this fix since the cursor is computed within BG.)
- **Register discipline:** the hook keeps loop state (`a0`/`a2`/`d2`/`attr`/`col`) in registers `bg_fill` preserves (it `movem`-saves all); set only `A0/D0/D1` for the call; same CLOSED-016 discipline.
- **Invariant impact:** `opcode_replace` **+1** (new patched_site `0x55E5E` / arcade `0x55C5E`); `total_genesis_bytes_covered` **+ hook size** (genesis_only, est. ~60–90 bytes); entry byte-neutral; relocation genesis_only-internal. Any other delta = STOP.

---

## 6. Validation plan for Cody

- Build canonical gate passes; new build/SHA.
- BlastEm/Nomad-strict: **NO HV/VDP-port fatal** at the item page — **zero raw writes to the BG C-window `0x00C00000..0x00C03FFF`** from this producer (watchpoint the range / `0xC00008`).
- The 64 strip cells route through `bg_fill` → composed cells in `staged_bg_buffer` (col 2, rows 0–63), `bg_row_dirty` set for rows 0–63; committed at VBlank to Plane B.
- **Producer-equivalence:** the staged cells carry `attr = 0x0002` (color bank 2 via `attr_lut`) and `tile_vram_lut[strip_word]` for each row's strip code (`0x04A6…`-class) — same cells the raw producer would have written, now via staging.
- Cursor `0x00FF10F8` still advances (write-back) as a BG C-window address; Build 0119 source/strip relocations (`0x00FF1100 = 0x0000D31C`) remain valid.
- Item-page state progresses farther than Build 0119; a new later crash is acceptable progress — report exact PC/state.
- No title/story/high-score regression; no dispatcher/LUT/VDP-commit regression.
- Document `opcode_replace` +1 and genesis_only growth.

---

## 7. Out of scope (enforced)

- NO KF-038 item-scroll/staging-size (note only: the column's visual placement/scroll is KF-038's domain; this fix only routes the writes, it does not adjust scroll/size).
- NO `bg_fill` rewrite (reused as-is); NO PC080SN render-loop changes beyond this producer.
- NO sprites/HUD/Window/gameplay; NO systemic ROM-wide KF-036 postpatcher pass.
- NO fake data, skip/bypass, broad runtime mirror, address masking, or write suppression; NO diagnostic scaffolding.

---

## 8. Risks / open questions

| Item | Note |
|---|---|
| Is `0x00C00008` really BG (not FG/scroll)? | PROVEN: `∈ [0xC00000,0xC04000)` BG C-window; seed adds BG base `0xC00000`. Not FG (`0xC08000`), not scroll (`0xC04000+`). |
| Wrong-seed possibility | REFUTED: cursor computed `0xC00000 + row*64 + col*4` (arcade-native); the value is correct, the write path is the bug. |
| Header `0x0002` as attr | `attr_lut[color bank 2]` composes palette line 2; if the column renders wrong-colored, that is the existing `attr_lut` mapping (pre-existing), not this fix — flag, don't bundle. |
| Cursor walks out of BG window | `bg_fill` range-gate NO-OPs out-of-window; cursor is computed within BG; optional fail-loud. |
| KF-038 placement | The strip's on-screen position/scroll is KF-038 (deferred); this fix makes it render via staging without crashing. |

## Cody evidence needed if STOP

**None — no STOP.** Destination semantics proven statically (seed computation `0xC00000 + row*64 + col*4`; BG C-window membership; per-cell `{attr,code}` column; `bg_fill` interface). Root cause and fix shape are proven.

## Open / Closed Issues Impact

- Open issues touched: **KF-032 class / OPEN-022** (item-page raw PC080SN writes — new destination-side BG strip-producer instance; not closed pending implementation + §6 validation), KF-036 (predecessor/fixed: slot rebase), KF-028/OPEN-016 (predecessor/fixed: source + strip pointer relocation), OPEN-001 (context — item-page progression). KF-038 noted-deferred. OPEN-015 not touched. **Not OPEN-023** (Window/HUD).
- New issues opened: NONE.
- Issues closed: NONE.
- Intentionally deferred: implementation; KF-038 item-scroll/staging-size + on-screen placement; systemic ROM-wide KF-036 postpatcher pass; downstream crash from progress.

## STOP triggered

NO (destination = correct arcade-native PC080SN BG C-window address written raw = KF-032; fix routes the 64-cell strip column through the existing `bg_fill` BG staging via a function-level producer hook; statically proven, no invented data).
