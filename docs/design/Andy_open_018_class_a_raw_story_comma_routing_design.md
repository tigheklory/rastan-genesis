# Andy — OPEN-018 Class A: Route Raw Story-Comma PC080SN Write (Design Only)

**Author:** Andy
**Date:** 2026-06-26
**Build:** 0106 canonical (`dist/rastan-direct/rastan_direct_video_test_build_0106.bin`, SHA256 `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`). rastan-direct.
**Scope:** DESIGN only. No source/spec/ROM/build/bookmark/diagnostic changes; no implementation. Outputs: this doc + one AGENTS_LOG entry. All instruction-PC correlation via `build/rastan-direct/address_map.json` (no ±0x200 as authority). Address spaces labeled. Labels: **[OBS]** verified this task; **[INT]** interpretation.

**Class scope:** Class A (raw PC080SN write bypassing staging) only — **KF-032**, **OPEN-018**. Class B low-code glyph LUT (KF-033/OPEN-019/OPEN-020) is explicitly NOT designed here.

---

## Phase 0 — Baseline

**Classification:** EXTENDING (OPEN-018, OPEN-001). **Context:** KF-032 (route, do not no-op), KF-033/OPEN-019/020 (Class B, context only), OPEN-005/OPEN-017 (strict-target crash family). **OPEN-015 not touched.** **Contradiction:** NONE. **Architecture compliance:** the design replaces one verbatim-copied arcade write with an opcode-replacement `jsr` into a Genesis helper that routes arcade intent to staging and returns via `rts` — no Genesis-owned loop/lifecycle.

---

## 1. Target site — confirmed [OBS]

```
runtime_genesis_pc 0x0003ACEA:  33fc 2749 00c0 9172   move.w #0x2749, 0x00C09172
```
JSON: `runtime_genesis_pc 0x0003ACEA` ∈ segment `0x03AB20..0x03AD00`, kind `arcade_copy`, **`arcade_pc 0x0003AAEA`** (verified). Effective: word `0x2749` → `HW_ADDRESS 0x00C09172` (PC080SN FG C-window code word; paired attr at `0x00C09170`=`0x0000`). Decode: FG row 17, col 28, cell index `0x045C`, tile `0x2749`, color bank 0, no flip. Build 0106 mapping: tile `0x2749 → Genesis slot 0x0039` (LUT verified) — **not a mapping/preload problem; the defect is the raw write path.** [OBS]

**Surrounding context (lone inline write inside a glyph sequence):** [OBS]
```
3ace4: moveq #70,%d0 ; bsr 0x3bd48     ; glyph renderer (genesistan_hook_glyph_renderer_3bd48), chars 0x40-0x46
3acea: move.w #0x2749, 0x00C09172      ; RAW comma write  ◄── target
3acf2: move.w #0x00A0, 44(%a5)         ; state write (a5 = WRAM base 0x00FF0000)
3acf8: move.w #0x0002, 4(%a5)
3acfe: rts
```
The arcade itself emits the comma as a direct PC080SN write (the surrounding glyphs route through the text/glyph dispatch arcade `0x3BB48` → patched `genesistan_hook_glyph_renderer_3bd48`); the verbatim copy kept it raw. [OBS+INT]

**Liveness across the site** [OBS]: CCR set by the comma write is **dead** — immediately overwritten by `move.w #0x00A0,44(%a5)` at `0x3ACF2`. `%a5` is live after but **not touched** by the comma write. `%d0`/`%d1`/`%a0` are not read between `0x3ACEA` and the `rts`. ⇒ no condition-code dependency; the replacement must preserve registers conservatively to be safe across the routine boundary.

---

## 2. Current staging mechanics (Task 1) [OBS]

| Mechanism | Symbol / value |
|---|---|
| FG staging buffer | `staged_fg_buffer` (WRAM `0x00FF501A`) |
| FG staged row/col index | `staged_fg_buffer + (row*128 + col*2)` (`lsl #7` row + `col*2`) |
| PC080SN code→slot LUT | `genesistan_pc080sn_tile_vram_lut` (`0x000F213C`); `slot = lut[code & 0x3FFF]` (u16, byte index `code*2`) |
| PC080SN attr→Genesis attr LUT | `genesistan_pc080sn_attr_lut` (`0x000FA13C`); composed from attr bits (palette/flip) |
| FG dirty marking | `fg_row_dirty` (WRAM `0x00FF4006`); `bset #row` per staged row |
| FG C-window base / size | `ARCADE_PC080SN_CWINDOW_BASE_FG = 0x00C08000`, `CWINDOW_BYTES = 0x4000` → `[0xC08000,0xC0C000)` |

**Reusable worker — `genesistan_hook_tilemap_fg_fill` (`runtime_genesis_pc 0x0007065E`)** [OBS]:
- **Signature:** `A0` = PC080SN FG HW address; `D0` = packed cell value (low word = tile code, high word = attr word); `D1` = cell count.
- **Body:** `movem.l %d0-%d7/%a0-%a6,-(%sp)` (saves/restores **all** registers — caller-safe) → range-gate `[0xC08000,0xC0C000)` → compose once: `D3 = tile_vram_lut[D0.w & 0x3FFF] | attr_lut[attr-bits-from-high-word-of-D0]` → per cell: decode `cell=(A0&0xFFFFFF − 0xC08000)>>2`, `col=cell&0x3F`, `row=(cell>>6)&0x1F`, store `D3 → staged_fg_buffer + row*128 + col*2`, `bset #row, fg_row_dirty`, `A0+=4`, `D1−=1`.
- **Verified single-cell behavior for the comma:** `A0=0xC09170, D0=0x00002749, D1=1` → `D3 = lut[0x2749] (0x0039) | attr_lut[0]`; cell `0x45C` → row 17, col 28 → `staged_fg_buffer + 0x8B8`; `fg_row_dirty` bit 17 set. **Exactly the comma's arcade intent, via the live LUT.** [OBS+INT]

The prompt's `0x70952 / 0x70984.. / 0x709A4..` are local store/compose/range fragments *inside* `genesistan_hook_tilemap_fg_fill` (the glyph path `genesistan_hook_glyph_renderer_3bd48` at `0x70D4E` shares the same `tile_vram_lut`/`attr_lut`/`staged_fg_buffer`/`fg_row_dirty` primitives). Reusing `fg_fill` as a whole is cleaner than reaching into its internals. The Build 0106 scroll-clear C-lite helpers are a separate path (BG/FG scroll RAM) and not applicable here. [OBS+INT]

---

## 3. Patch-site design (Task 2)

**Replace the 6-byte inline write with a 6-byte `jsr` (byte-neutral):** [OBS-derived]
```
3ACEA: 33fc 2749 00c0 9172   move.w #0x2749,0x00C09172      (6 bytes)
   →   4eb9 00 07 xx xx      jsr  genesistan_hook_inline_fg_write_3acea   (6 bytes, jsr abs.l)
```
- **Why `jsr abs.l`, not `bsr.w`:** the helper lives in `genesis_only` (`0x70000+`), out of `bsr.w` ±32 KB range from `0x3ACEA`; `jsr abs.l` is exactly 6 bytes → **byte delta = 0** at the site (no arcade-space relocation). A `bsr.w` (4 bytes) would also under-fill the slot by 2 bytes and can't reach the helper.
- **Return:** helper ends `rts` → returns to **`runtime_genesis_pc 0x0003ACF2`** (the instruction after the 6-byte `jsr`), identical to the original fall-through. Stack is balanced (`jsr` pushes 4, helper `rts` pops 4). [OBS]
- **No fall-through / CC dependency:** none (§1 — CCR dead, `%a5` untouched). [OBS]
- **Register/flag preservation:** the helper preserves all registers (§4); CCR on return is unspecified but **dead** at the site. Conservative full-register preservation is recommended (no proof needed that a smaller clobber set is safe, and it removes all doubt).
- **Map effect:** `arcade_pc 0x0003AAEA` flips `arcade_copy → patched_site`; **opcode_replace +1**. Site byte delta 0; `genesis_only` grows by the helper only (see §5).

---

## 4. Routing helper design (Task 3) + shape choice (Task 3B)

**Chosen shape: Option 1 (dedicated site helper) that DELEGATES to the existing generalized worker `genesistan_hook_tilemap_fg_fill` (Option 3 reuse for the actual staging).** [INT]

```
; genesistan_hook_inline_fg_write_3acea
;   Routes the raw arcade comma write (arcade_pc 0x3AAEA / runtime 0x3ACEA):
;     move.w #0x2749, 0x00C09172   (PC080SN FG row17/col28, attr 0x0000)
;   into Genesis FG staging via the live tile LUT. KF-032 (Class A).
genesistan_hook_inline_fg_write_3acea:
    movem.l %d0-%d7/%a0-%a6, -(%sp)      ; conservative: preserve all (CCR is dead at the site)
    lea     0x00C09170, %a0             ; FG cell base (attr word) for row17/col28; fg_fill derives row/col from A0
    move.l  #0x00002749, %d0            ; high word = attr 0x0000 ; low word = PC080SN code 0x2749 (LUT-resolved at runtime)
    moveq   #1, %d1                     ; one cell
    bsr     genesistan_hook_tilemap_fg_fill   ; live-LUT translate + compose + stage + dirty
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts
```

- **Translate code how:** `fg_fill` resolves `genesistan_pc080sn_tile_vram_lut[0x2749]` **at runtime** (currently `0x0039`) and composes attr via `genesistan_pc080sn_attr_lut`. **The literal slot `0x0039` is NOT embedded** — satisfies Constraint 2. [OBS]
- **Stage where:** `staged_fg_buffer + 0x8B8` (row 17, col 28), derived by `fg_fill` from `A0` (no hardcoded staged offset). [OBS]
- **Dirty mark how:** `fg_fill` sets `fg_row_dirty` bit 17. [OBS]
- **Dedicated vs reusable vs reused-existing:** **dedicated entry (Option 1) + reused generalized worker (Option 3).** Why: the byte-neutral 6-byte `jsr` leaves no room to set up `A0/D0/D1` at the site, so a directly-called reusable helper (Option 2) would force >6 bytes at the site → byte growth + arcade relocation. The dedicated entry supplies only the two values intrinsic to this exact site (`HW_ADDRESS 0x00C09170`, code `0x2749`) and delegates **all** translation/staging/dirty to the proven `fg_fill` — which itself derives row/col from `A0` (not hardcoded) and uses the live LUT. Best of both: byte-neutral site + no fragile register assumptions + live-LUT + reuse. [INT]
- **Attr source:** attr `0x0000` is embedded (high word of `D0`), matching the decode-confirmed paired attr at `0x00C09170`. (Risk if that cell's arcade attr were ever nonzero — see §7; it is decode-confirmed 0 and this is a fixed story glyph.)
- **`bsr` reach:** the helper sits in `genesis_only` near `fg_fill` (`0x7065E`); `bsr genesistan_hook_tilemap_fg_fill` is in `bsr.w` range. If the assembler places it >32 KB away, use `jsr genesistan_hook_tilemap_fg_fill` (the only effect is +2 helper bytes). [INT]
- **A0 note:** `0x00C09170` (cell base) is used; `fg_fill`'s `(A0−base)>>2` truncates the low 2 bits, so `0x00C09172` would resolve to the same cell `0x45C` — `0x00C09170` is specified for unambiguous cell alignment.

---

## 5. Expected byte delta (for Cody pre-authorization)

- **Arcade space (`0x200..0x70000`):** site `0x3ACEA` 6→6 bytes → **delta 0**; no other arcade bytes change.
- **`genesis_only`:** `+` one helper `genesistan_hook_inline_fg_write_3acea` (~22 bytes with full `movem`; ~24 if `jsr` to fg_fill). `total_genesis_bytes_covered` increases by exactly the helper size; `genesis_only`-internal addresses after the helper shift (standard re-relocation, OPEN-016 class); arcade space unaffected.
- **opcode_replace count:** +1 (arcade `0x3AAEA`).
- **Predictable**: site delta 0 + one new helper. **Any other delta = STOP.**

---

## 6. Sibling raw-write scan (Task 4) [OBS]

Bounded static scan of `arcade_copy` (`0x200..0x70000`) for raw PC080SN **C-window** writes (`0xC08000..0xC0FFFF`). The 0xC00000/0xC00004 hits at runtime `0x306..0xADE` are **legal VDP data/control-port** writes (boot init), not C-window — excluded.

| runtime_pc | arcade_pc | HW_ADDRESS | FG row/col | value source | shape | disposition |
|---|---|---|---|---|---|---|
| **0x3ACEA** | **0x3AAEA** | **0xC09172** | **17,28** | imm `0x2749` | inline immediate absolute | **THIS FIX** |
| 0x3A550 | 0x3A350 | 0xC08A52 | 10,20 | imm `0x0032` | inline immediate absolute | same shape — DEFER (decode first) |
| 0x3A8FE | 0x3A6FE | 0xC08E7A | 14,30 | imm `0x2744` | inline immediate absolute | same shape — DEFER |
| 0x3A908 | 0x3A708 | 0xC08E66 | 14,25 | imm `0x2744` | inline immediate absolute | same shape — DEFER |
| 0x3A92A | 0x3A72A | 0xC08C62 | 12,24 | reg `%d0` | register absolute | similar — DEFER (confirm %d0 is a tile code) |
| 0x3D24C | 0x3D04C | 0xC08C66 | 12,25 | reg `%d1` | register absolute | similar — DEFER |
| 0x3B3CC | 0x3B1CC | (a0)=0xC093xx | producer | reg `%d0` | producer loop store `move.w d0,(a0)` | DIFFERENT shape — DEFER (loop routing) |
| 0x3B7F6/0x3B7F8 | 0x3B5F6/0x3B5F8 | (a0/a2) | producer | reg | producer loop store | DIFFERENT shape — DEFER |

**Include siblings in THIS fix? NO.** [INT] Rationale: (1) only the comma is fully decoded (attr/code/row/col/reachability proven); the other absolutes need a per-site decode (attr value, color bank, whether reached on the title/story path) before routing; (2) the register-absolute sites need confirmation that the source register holds a PC080SN tile code at that point; (3) the producer-loop writes are a different shape requiring loop routing (akin to the scroll-clear C-lite design), not a single-cell trampoline. Keep the implementation target limited to `0x3ACEA`.

**But this materially affects OPEN-018 closure** [INT]: the comma is **one of ≥6 reachable raw FG writes**. Routing only `0x3ACEA` removes the `0xC09172` raw write but **may not stop the strict-target crash** if a sibling (`0x3A550`/`0x3A8FE`/`0x3A908`/`0x3A92A`/`0x3D24C`) is reached first and faults on its own VDP-mirror write. **Recommended:** treat `0x3ACEA` as the proven instance + **template**, then sweep the same-shape immediate-absolute siblings (`0x3A550`, `0x3A8FE`, `0x3A908`) with identical dedicated-trampoline→`fg_fill` helpers (each preceded by a quick attr/reachability decode), and design the register-absolute and producer-loop siblings separately. OPEN-018's "strict target no longer crashes" closure realistically depends on routing all *reachable* raw FG writes — file the siblings as the next OPEN-018-class work.

---

## 7. Validation plan for Cody (Task 5)

1. **Build succeeds**; `opcode_replace` count = prior + 1; byte invariants pass.
2. **ROM/SHA:** new build (not byte-identical to 0106 — intentional code change); verify per project expectations.
3. **No unexpected byte deltas:** site `0x3ACEA` = `jsr <helper>` (6 bytes), arcade space otherwise unchanged; `genesis_only` grew only by the helper (§5). Any other delta = STOP.
4. **Raw HW watchpoint (MAME Genesis driver):** a write watchpoint on `HW_ADDRESS 0x00C09172` **no longer fires** as a raw HW write during the story page.
5. **Staging check:** `staged_fg_buffer + 0x8B8` (row 17, col 28) = composed word = `genesistan_pc080sn_tile_vram_lut[0x2749]` (currently `0x0039`) `| genesistan_pc080sn_attr_lut[0]`; `fg_row_dirty` bit 17 set. (Confirm the value tracks the **live** LUT, not a literal `0x0039`.)
6. **Strict-target check (BlastEm / Nomad / real HW):** the `0xC09172`-specific raw write no longer faults. **HONEST caveat:** if the strict target still crashes, capture **which** HW address it faults on — a sibling raw write (§6) is the likely culprit; that is the next OPEN-018-class target, not a regression of this fix.
7. **Visual check:** the story comma/special glyph appears at FG row 17, col 28 where the arcade intends.
8. **Out of scope (do NOT claim fixed):** title screen and `INSERT COIN(S)` parens (Class B / OPEN-019); the sibling raw writes `0x3A550/0x3A8FE/0x3A908/0x3A92A/0x3D24C` and producer loops (still raw — strict-target latent).
9. **Class B** low-code glyph LUT defects remain out of scope.

---

## 8. Risk assessment (Task 6)

| Risk | Likelihood | Mitigation |
|---|---|---|
| Stage raw `0x2749` instead of LUT slot | LOW | Design delegates translation to `fg_fill` (live LUT); never store the raw code. Validation §7.5 checks the composed value. |
| Embed stale literal slot `0x0039` | ELIMINATED | Design forbids embedding; `fg_fill` resolves the live LUT at runtime — survives future Class B/LUT/preload changes. |
| Wrong row/col staging | LOW | `fg_fill` derives row/col from `A0=0xC09170`; decode-verified cell `0x45C` = row17/col28. |
| Fail to mark dirty | LOW | `fg_fill` sets `fg_row_dirty` bit 17 unconditionally per staged cell. |
| Clobber live registers | LOW | Helper full-`movem` save/restore; `fg_fill` also `movem`-preserves all; `%a5` (the only live reg across the site) is never touched. |
| Condition-code side effects | NONE | Site CCR is dead (overwritten by `0x3ACF2`). |
| Wrong attr (embedded 0x0000) | LOW | Decode-confirmed paired attr at `0xC09170`=`0x0000`; fixed story glyph. If ever nonzero, the embedded 0 would mis-color — a future reusable helper could read the staged/arcade attr instead. |
| Accidentally change Class B behavior | NONE | This site is a Class-A raw absolute write; it does not touch the glyph-renderer/LUT-coverage path. |
| Hidden sibling raw writes | CONFIRMED (≥5) | §6 enumerates them; validation §7.6 captures the actual fault address; siblings filed as next OPEN-018-class targets. |
| Helper too special-case | ACCEPTED | Dedicated entry is intentional (byte-neutral); the *worker* (`fg_fill`) is generalized. Template reused for siblings. |
| Mismatch with VBlank/staging lifecycle | LOW | Routes into the same `staged_fg_buffer`/`fg_row_dirty` the VBlank FG commit already consumes; no new lifecycle. |
| Byte growth / relocation | LOW (managed) | Site byte-neutral; `genesis_only` helper growth is the standard re-relocation class (§5). |

---

## Open / Closed Issues Impact

- Open issues touched: **OPEN-018** (active — Class-A comma routing fully designed; not closed pending implementation **and** the sibling sweep needed for strict-target closure), OPEN-001 (context — story glyph correctness), OPEN-005/OPEN-017 (context — strict-target crash family). OPEN-015 not touched.
- New issues opened: NONE (recommend filing the sibling raw-FG-write sweep — `0x3A550/0x3A8FE/0x3A908` same-shape, `0x3A92A/0x3D24C` register-absolute, `0x3B3CC/0x3B7F6/0x3B7F8` producer-loop — as OPEN-018-class follow-ups if Tighe wants explicit tracking).
- Issues closed: NONE.
- Intentionally deferred: all sibling raw writes (§6); Class B (KF-033/OPEN-019/OPEN-020); implementation.

## STOP triggered

NO.
