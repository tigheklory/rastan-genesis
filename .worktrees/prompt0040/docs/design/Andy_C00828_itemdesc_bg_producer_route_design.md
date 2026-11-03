# Andy — Route the Item-Description BG Text Producer (C00828) Through BG Staging (Design Only)

**Author:** Andy
**Date:** 2026-06-28
**Baseline:** Build 0112 (`dist/rastan-direct/rastan_direct_video_test_build_0112.bin`, SHA256 `024241b2378dba68102637c368bc92d5edc41b2b30776363a96144146dfe215d`). rastan-direct.
**Scope:** DESIGN only. No source/spec/tool/ROM/build/bookmark/diagnostic/implementation. Static from Cody evidence + CLOSED-016 template. Output: this doc + one AGENTS_LOG entry. Address-PC correlation via `address_map.json` (no ±0x200 as authority). Labels: **[OBS]** verified this task; **[CODY]** Cody evidence; **[INT]** interpretation.

**Class:** KF-032 raw-PC080SN-write family; BG analog of the CLOSED-016 FG high-score producer route. **Out of scope:** sprite/PC090OJ path (0xD00170 / 0x56314 = OPEN-024), high-score (CLOSED-015/016/017), Class B, OPEN-018 other sites, score/round (OPEN-021), the zero/blank-table family.

---

## Phase 0 — Baseline

**Classification:** EXTENDING (OPEN-022, KF-032 family). **Contradiction:** NONE. **Root (Cody, re-verified):** the item-description attract page (`%a5@(0)=2,%a5@(2)=2,%a5@(4)=6`) runs a BG text producer that does **raw PC080SN BG writes** to `HW_ADDRESS 0x00C00828..0x00C03E2A` (BG C-window), freezing BlastEm/real-Genesis. Source is ROM text (not work-RAM) → **no KF-036 work-RAM-base risk**; the defect is purely the raw destination writes.

**JSON mappings (exact)** [OBS]: writer entry `runtime 0x0565A6` = `arc 0x0563A6`; raw stores `0x0565B8`=`arc 0x0563B8` (attr), `0x0565BE`=`arc 0x0563BE` (code); substitution sub `0x0565CE`; item-desc call site `0x0005623C`=`arc 0x0005603C`; ROM text source `runtime 0x0005692A` = `arc 0x0005672A`; all `arcade_copy`.

---

## 1. The shared writer, decoded [OBS]

```
565A6 movea.l a1,a2            ; a2 = dest row base
565A8 clr.w d0
565AA move.b (a0)+,d0          ; source byte
565AC cmpi.b #0,d0  ; beq 565CC ; 0x00 → terminate
565B2 cmpi.b #-1,d0 ; beq 565C2 ; 0xFF → row advance
565B8 move.w d1,(a1)+          ; *** RAW STORE 1: ATTR word (d1)
565BA bsr 565CE               ; substitute d0 → code (pure d0 transform)
565BE move.w d0,(a1)+          ; *** RAW STORE 2: CODE word (d0)
565C0 bra 565A8
565C2 adda.l #0x200,a2 ; 565C8 movea.l a2,a1 ; bra 565A8   ; 0xFF: row base += 0x200, a1 = base
565CC rts
565CE (substitution) 0x21→0x2744 0x22→0x2745 0x27→0x2746 0x28→0x2747
      0x29→0x2748 0x2C→0x2749 0x2D→0x274A 0x3F→0x274B ; all → rts at 565CE..5663E; touches only d0
```
Per cell = 2 raw PC080SN words (attr `d1`, then code `d0` post-substitution); `a1 += 4`/cell. `0xFF` advances `a2` by `0x200` and resets `a1=a2`. `0x00` terminates. The substitution sub `0x565CE` is a **pure d0→d0 transform** (no raw writes, no other registers). [OBS]

---

## 2. Caller census of the shared writer 0x565A6 — **SHARED (case B)** [OBS]

| caller (runtime) | arcade_pc | source (a0) | dest (a1) | attr (d1) | plane |
|---|---|---|---|---|---|
| **0x0005623C** (item-desc) | 0x0005603C | 0x0005692A | **0x00C00828** | 0 | **BG C-window (PROVEN — the freeze)** |
| 0x00056266 | — | 0x00056B7E | **0x00C00028** | 0 | **BG C-window (confirmed same-class sibling)** |
| 0x000563F8 | — | indirect (tbl 0x564CA) | indirect | 0 | **UNKNOWN** (table-driven) |
| 0x00056420 | — | indirect (tbl 0x564FA) | indirect | 0 | **UNKNOWN** (table-driven) |
| 0x000576FC | — | indirect (tbl 0x57B08) | indirect | 0 | **UNKNOWN** (table-driven) |
| 0x0005A6CE | — | indirect (tbl 0x5A7AC) | indirect | **table-driven (a3@0)** | **UNKNOWN** (attr may be ≠0) |

**Verdict: the writer 0x565A6 is a generic PC080SN text writer used by ≥6 callers.** Two write known BG C-window dests (`0x5623C`→0xC00828, `0x56266`→0xC00028, both attr 0); four use **indirect/table-driven** dests (and `0x5A6CE` a table-driven attr) whose plane cannot be proven statically. [OBS]

> **Patching the writer ENTRY (0x565A6) is UNSAFE** [INT]: it would reroute the four indirect-dest callers (and the table-driven-attr caller) through BG staging. If any targets FG (0xC08000) or a non-C-window destination, that breaks them (FG would mis-stage; a non-C-window dest would be NO-OP-dropped by `bg_fill`'s range gate). Statically unprovable for the four indirect dests → do not patch the entry.

---

## 3. Recommended approach & patch site

**Approach: FUNCTION-LEVEL replacement at the item-description CALL SITE (not the writer entry).** Route ONLY the proven item-description BG producer; leave the shared writer 0x565A6 entirely untouched for its other five callers.

- **Route-stores in-place — REJECTED** [OBS]: the raw stores `0x0565B8`/`0x0565BE` are 2-byte `move.w (%a1)+` (no room for a call), and BG staging is per-cell composed (incompatible with per-raw-word routing). Same as CLOSED-016.
- **Patch the writer entry — REJECTED** (§2: shared, unsafe).
- **Patch the call site — RECOMMENDED** [INT]: replace the item-description setup+call block with a `jsr` to a genesis_only hook that reimplements the producer for this invocation and stages each cell via `genesistan_hook_tilemap_bg_fill`. Bounded (zero risk to the other 5 callers), matches the CLOSED-016 shape, BG-side.

**Patch-site mechanics** [OBS+INT]: the call-site setup+call block is `runtime 0x0005622C..0x0005623F` (20 bytes):
```
5622C movea.l #0x0005692A,a0   (6)   ; source
56232 movea.l #0x00C00828,a1   (6)   ; BG dest
56238 move.w #0,d1             (4)   ; attr 0
5623C bsr.w 0x565A6            (4)   ; → shared writer
```
The 4-byte `bsr.w` cannot reach a genesis_only hook (>32 KB), so the redirect cannot be the bsr alone. Replace the **whole 20-byte block** with:
```
5622C jsr genesistan_hook_itemdesc_bg_producer   (4EB9 + 4 = 6 bytes)
56232 nop × 7                                     (14 bytes)
```
The hook `rts` returns to `0x56232` → 7 nops → falls through to `0x56240` (the sprite-path setup, unchanged). **Byte-neutral (20→20).** The hook **hardcodes** the three constants the block set (source `0x0005692A`, dest `0x00C00828`, attr `0`) — faithful, since they were literals.

> **Address-discipline note** [INT]: the hook references the ROM text source by its **mapped runtime address `0x0005692A`** (= `arc 0x0005672A` per `address_map.json`). This is `arcade_copy` ROM data; its runtime address is stable unless the map relocates. If a future build relocates `arcade_copy`, the hook's source/dest constants must be regenerated from the map (maintenance dependency — flag for Cody).

---

## 4. Raw writers routed

| raw writer | route |
|---|---|
| `0x0565B8` attr (`move.w d1,(a1)+`) | **Eliminated.** Hook folds attr (`d1`=0) into the per-cell `bg_fill` `D0` high word; no raw attr write. |
| `0x0565BE` code (`move.w d0,(a1)+`) | **Eliminated.** Hook passes the post-substitution code as `bg_fill` `D0` low word; no raw code write. |
| (no other raw store in the producer) | — (the substitution sub `0x565CE` does no writes). |

The shared writer 0x565A6 and its raw stores stay in the ROM, **unexecuted by the item-description path** (the call site now jsr's the hook), but **still live for the other five callers** (untouched).

---

## 5. Producer intent preserved (in the hook)

The hook reimplements the producer outer loop, reusing the arcade substitution sub:
- **ROM text source walk** [OBS]: `a3 = 0x0005692A`; `byte = (a3)+` (source pointer kept in `a3` to avoid colliding with `bg_fill`'s `A0` dest arg).
- **attr/code pairing** [OBS]: per cell, compose one BG cell from `attr=0` (hi word) + `code` (lo word).
- **0xFF row-advance** [OBS]: `a2 += 0x200; a1 = a2` (next BG row pair); `bg_fill` re-derives row/col from the new `a1`.
- **0x00 terminate** [OBS]: end loop → `rts`.
- **Glyph substitution** [OBS]: **reuse the arcade sub `jsr 0x000565CE`** (pure d0→d0; maps the 8 punctuation keys → 0x2744..0x274B; preserves a1/a2/a3/d-loop-state). No reimplementation of the substitution table → no fidelity risk. (Alternative: reimplement the 8-entry table; rejected as higher-risk.)
- **Full dest range** [OBS]: `a1` starts `0x00C00828`, walks to `0x00C03E2A` across the 568 cells / 27 `0xFF` advances — all within BG C-window `[0xC00000,0xC04000)` (`0xC03E2A < 0xC04000`), so `bg_fill` accepts every cell.

---

## 6. %a1 → BG staging-offset translation [OBS]

- **BG staging hook + interface:** `genesistan_hook_tilemap_bg_fill` (genesis_only) — IN `A0`=BG HW addr, `D0`=(attr<<16)|code, `D1`=count; `movem.l d0-d7/a0-a6` save/restore (caller-safe); range-gate `[0xC00000,0xC04000)`; composes `tile_vram_lut[code & 0x3FFF] | attr_lut[attr-bits]`; stores `staged_bg_buffer`; `bset #row, bg_row_dirty`.
- **Formula (BG HW addr → bg staging offset):** `cell = ((A0 & 0xFFFFFF) − 0x00C00000) >> 2`; `col = cell & 0x3F`; `row = (cell >> 6) & 0x1F`; `staged-WRAM-offset = staged_bg_buffer + row*128 + col*2`.
- **No separate translator needed** — the hook calls `bg_fill(A0 = a1, D0 = (0<<16)|code, D1 = 1)` per cell, then `a1 += 4`.
- **0xFF row-advance in staging terms:** setting `a1 = a2 + n*0x200` and calling `bg_fill(A0=a1)` lands the next cells at the BG row(s) `0x200` bytes (= 0x80 cells = 2 BG rows) ahead — `bg_fill` derives the correct row/col from `a1`, so the staged cells match the raw producer's destination exactly.
- **attr/code pairing + BG dirty/commit:** one composed `staged_bg_buffer` cell per `bg_fill` call (attr 0 → `attr_lut[0]=0` → bare slot); `bg_fill` sets `bg_row_dirty` per row; the VBlank BG commit reads `staged_bg_buffer` for dirty rows → cells commit.

---

## 7. Register / flag / byte mechanics

- **Registers preserved across staging calls** [INT]: `bg_fill` (and the sub `0x565CE`) preserve all registers for the hook. The hook keeps loop state in registers **not** used as `bg_fill` args (`A0/D0/D1`): source ptr in `a3`, dest in `a1`, row base in `a2`, attr in (e.g.) `d3`. It sets `A0=a1, D0=(d3<<16)|code, D1=1` only for each `bg_fill` call; `bg_fill` restores `a1/a2/a3/d3` to their pre-call values. `0x565CE` touches only `d0`. (Same discipline as CLOSED-016: keep loop state out of the call arg registers.)
- **Flags:** the producer returns via `rts`; the caller (`0x56240+`) does not consume producer-set CCR. No flag dependency. The 7 nops don't affect flags.
- **Patch shape + byte budget + byte-neutral:** one patch — the 20-byte call-site block `0x5622C..0x5623F` → `jsr hook` (6) + `nop`×7 (14). Byte-neutral 20→20.
- **Dead-body handling:** the shared writer `0x565A6` and its stores remain (live for the other 5 callers — **not** dead). The only "dead" bytes are the 7 nops at `0x56232..0x5623F` (skipped via fall-through after the hook returns).
- **Invariant impact:** `opcode_replace` **+1** (new patched_site at `0x5622C` / `arc 0x5603C`); `total_genesis_bytes_covered` **+ hook size** (genesis_only growth, est. ~70–110 bytes for the reimplemented loop). Arcade space byte-neutral except the 20-byte block (in place). Relocation: genesis_only-internal. Pre-authorize: +1 opcode_replace; genesis_only grows by exactly the hook; any other delta = STOP.

---

## 8. Why this matches arcade intent (not literal opcodes)

The producer's **intent** is to emit the item-description text's attr/code cells onto the PC080SN BG plane (with `0xFF` row-advance, `0x00` terminate, punctuation substitution). The arcade does it with raw PC080SN BG word writes — correct on arcade hardware, but on Genesis those addresses are VDP-mirror space (raw writes freeze strict targets; KF-032). The hook reproduces the **intent** — same source walk, same substitution (reusing the arcade sub), same `0xFF`/`0x00` control, same cells, same attr-0 — through the **Genesis BG staging path** (`bg_fill` → `staged_bg_buffer` → `bg_row_dirty` → VBlank commit). Reproduce intent, not opcodes. The text **content** is unchanged (same ROM source read); only the **write path** changes. [INT]

---

## 9. Validation plan for Cody (incl. producer-equivalence mismatch-count gate)

- Build; canonical gate; new build/SHA.
- **Byte-neutral:** only the `0x5622C..0x5623F` block changed (`jsr hook` + 7 nops); `opcode_replace` +1; `total_genesis_bytes_covered` grows by exactly the hook; shared writer `0x565A6` bytes unchanged. Any other delta = STOP.
- **Strict target (BlastEm/Nomad):** NO freeze at the item-description page — **zero raw producer writes to BG C-window `0x00C00000..0x00C03FFF` from this path** (watchpoint the BG C-window range).
- **PRODUCER-EQUIVALENCE GATE (mismatch count must be 0):** capture the original Build 0112 raw producer's per-cell output for the item-description invocation (dest addr, attr, code, row/col, and `0xFF`/`0x00` control handling) AND the new hook's staged cells; diff cell-by-cell. The item text (AXE / HAMMER / FIRE SWORD / SHIELD / MANTLE / ARMATURE / MEDICINE / POISON / GOLD SHEEP / JEWEL …) must stage the **same cells at the same BG rows/cols**. **Mismatch count = 0.**
- **`0xFF` row-advance + `0x00` terminate** handled across the full 568-cell stream (27 row advances).
- **VISUAL:** the item-description BG text renders. **Sprite garbage on the page is EXPECTED** (OPEN-024, separate) — not a failure of this fix.
- **No regression:** title, TAITO, story, parens, high-score (CLOSED-015/016/017), OPEN-018 comma, and **all five other callers of the shared writer `0x565A6`** (untouched — confirm unchanged).
- **Text content UNCHANGED** (same ROM source read); routing changes only the write path.

---

## 10. Strict-target closure note (siblings — do not silently assume one fix suffices)

This fix routes only the **proven** item-description call site (`0x5623C`). **`0x56266` is a confirmed same-class BG sibling** (dest `0xC00028`, raw, attr 0) that **will freeze** when its page renders — it needs the same call-site treatment (its own hook with hardcoded source `0x56B7E` / dest `0xC00028`, or a shared parameterized approach). The four **indirect-dest** callers (`0x563F8`, `0x56420`, `0x576FC`, `0x5A6CE`) need a **runtime destination census** — they are likely PC080SN C-window text writers (this writer's purpose) and thus latent KF-032 freezes, but their planes are not statically provable. **Recommended follow-up:** census the runtime dests of all six callers; if all are PC080SN C-window (BG/FG), a **dispatcher at the writer entry `0x565A6`** (route by `a1` range: BG→`bg_fill`, FG→`fg_fill`) would fix all six in one shot (including the table-driven attr at `0x5A6CE` via the compose path). That is the complete strict-target closure for this writer — but it requires the census first (cannot be proven statically now). Do not adopt it blind.

## Open / Closed Issues Impact

- Open issues touched: **OPEN-022** (item-description BG raw write — designed to route via call-site patch; not closed pending implementation **and** the sibling/census follow-up for full strict-target closure), KF-032 class, OPEN-001 (context — item-page visual completeness). OPEN-024 (sprite path — explicitly out of scope). OPEN-015 not touched.
- New issues opened: NONE (recommend tracking the `0x56266` confirmed BG sibling + the 4 indirect callers' census as an OPEN-022 follow-up / dispatcher option).
- Issues closed: NONE.
- Intentionally deferred: implementation; `0x56266` + the 4 indirect-dest callers (sibling sweep / dispatcher pending census); the sprite/PC090OJ path (OPEN-024); the zero/blank-table family.

## STOP triggered

NO (the design routes the full item-description producer — all raw writers + `0xFF`/`0x00` control + substitution — while preserving intent, without touching the shared writer's other callers).
