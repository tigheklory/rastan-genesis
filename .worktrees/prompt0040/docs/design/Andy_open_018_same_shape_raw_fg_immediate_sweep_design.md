# Andy — OPEN-018 Follow-up: Same-Shape Raw FG Immediate-Write Sweep (Design Only)

**Author:** Andy
**Date:** 2026-06-26
**Build:** 0106 canonical (`dist/rastan-direct/rastan_direct_video_test_build_0106.bin`, SHA256 `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`). rastan-direct.
**Scope:** DESIGN only. No source/spec/ROM/build/bookmark/diagnostic/implementation. Outputs: this doc + one AGENTS_LOG entry. All instruction-PC correlation via `build/rastan-direct/address_map.json` (no ±0x200 as authority). Address spaces labeled. Labels: **[OBS]** verified this task; **[INT]** interpretation.

**Class scope:** Class A (raw PC080SN write bypassing staging) only — **KF-032**, **OPEN-018**. Builds directly on `docs/design/Andy_open_018_class_a_raw_story_comma_routing_design.md` (the comma template). Class B (KF-033/OPEN-019/OPEN-020) NOT designed here.

---

## Phase 0 — Baseline

**Classification:** EXTENDING (OPEN-018). **Context:** KF-032 (route, don't no-op), KF-033/OPEN-019/020 (Class B, context only), OPEN-005/OPEN-017 (strict-target crash family). **OPEN-015 not touched.** **Contradiction:** NONE — refines the comma design's §6 sibling list into an implementable sweep. **Architecture compliance:** each fix replaces one verbatim-copied arcade write with an opcode-replacement `jsr` into a Genesis trampoline that delegates to `genesistan_hook_tilemap_fg_fill` and returns via `rts`.

**Template (proven):** comma `runtime_genesis_pc 0x0003ACEA` / `arcade_pc 0x0003AAEA` → `genesistan_hook_inline_fg_write_3acea` → `fg_fill(A0=0xC09170, D0=0x00002749, D1=1)`. This sweep applies the identical pattern to the three same-shape siblings.

---

## 1. Per-site decode [OBS]

`genesistan_hook_tilemap_fg_fill` (`runtime_genesis_pc 0x0007065E`): IN `A0`=FG HW addr, `D0`=(attr<<16)|code, `D1`=count; `movem.l d0-d7/a0-a6` save/restore (caller-safe); LUT-translate `D0.w & 0x3FFF`, compose attr, store `staged_fg_buffer + row*128 + col*2`, `bset #row, fg_row_dirty`. LUT `genesistan_pc080sn_tile_vram_lut` (`0x000F213C`); attr LUT `genesistan_pc080sn_attr_lut` (`0x000FA13C`); `staged_fg_buffer` WRAM `0x00FF501A`; `fg_row_dirty` WRAM `0x00FF4006`.

### Site 0x3A550

| Field | Value |
|---|---|
| runtime_genesis_pc | `0x0003A550` |
| arcade_pc (JSON) | `0x0003A350` (`arcade_copy` seg incl. this addr) |
| instruction bytes | `33fc 0032 00c0 8a52` (6) |
| instruction text | `move.w #0x0032, 0x00C08A52` |
| HW_ADDRESS (code) | `0x00C08A52` |
| paired attr address | `0x00C08A50` |
| paired attr value | `0x0000` (inferred — FG clear; no nearby attr write) [INT] |
| immediate code word | `0x0032` |
| FG row / col / cell | 10 / 20 / `0x028A` |
| A0 to pass | `0x00C08A50` (cell base) |
| packed D0 | `0x00000032` |
| D1 | `1` |
| live LUT result | `genesistan_pc080sn_tile_vram_lut[0x0032] = 0x000A` (**nonzero**) [OBS] |
| preloaded/mapped | YES (slot 0x000A; nonblank ROM pattern) [OBS] |
| content meaning | title/story FG decoration glyph (conditional on `42(a5)`) [INT] |
| reachability | conditional write in the title-text handler (executed only if `tst.w 42(a5) != 0`); same handler neighborhood as the comma; static — exact runtime order unconfirmed [OBS/INT] |

Context [OBS]: `3a54a: tst.w 42(a5) ; beq.s 0x3a558` guards the write; `3a558` is exactly the post-write fall-through. `%d0` is reassigned at `0x3a55e (moveq #26,d0)` → **dead** across the write; `%a5` live, untouched; CCR dead (overwritten by `tst.w 18(a5)` at `0x3a558`).

### Site 0x3A8FE

| Field | Value |
|---|---|
| runtime_genesis_pc | `0x0003A8FE` |
| arcade_pc (JSON) | `0x0003A6FE` |
| instruction bytes | `33fc 2744 00c0 8e7a` (6) |
| instruction text | `move.w #0x2744, 0x00C08E7A` |
| HW_ADDRESS (code) | `0x00C08E7A` |
| paired attr address | `0x00C08E78` |
| paired attr value | `0x0000` (inferred — FG clear) [INT] |
| immediate code word | `0x2744` (mapped high-code of `0x21 '!'`) |
| FG row / col / cell | 14 / 30 / `0x039E` |
| A0 to pass | `0x00C08E78` |
| packed D0 | `0x00002744` |
| D1 | `1` |
| live LUT result | `lut[0x2744] = 0x0034` (**nonzero**) [OBS] |
| preloaded/mapped | YES (slot 0x0034; nonblank ROM pattern) [OBS] |
| content meaning | title text decoration `!` glyph, branch A (`40(a5)!=0`) [INT] |
| reachability | conditional branch-A write, followed by the glyph renderer; title-text path [OBS] |

### Site 0x3A908

| Field | Value |
|---|---|
| runtime_genesis_pc | `0x0003A908` |
| arcade_pc (JSON) | `0x0003A708` |
| instruction bytes | `33fc 2744 00c0 8e66` (6) |
| instruction text | `move.w #0x2744, 0x00C08E66` |
| HW_ADDRESS (code) | `0x00C08E66` |
| paired attr address | `0x00C08E64` |
| paired attr value | `0x0000` (inferred — FG clear) [INT] |
| immediate code word | `0x2744` (mapped high-code of `0x21 '!'`) |
| FG row / col / cell | 14 / 25 / `0x0399` |
| A0 to pass | `0x00C08E64` |
| packed D0 | `0x00002744` |
| D1 | `1` |
| live LUT result | `lut[0x2744] = 0x0034` (**nonzero**) [OBS] |
| preloaded/mapped | YES [OBS] |
| content meaning | title text decoration `!` glyph, branch B (`40(a5)==0`) [INT] |
| reachability | conditional branch-B write, followed by the glyph renderer [OBS] |

**0x3A8FE / 0x3A908 are the two branches of one conditional** (`3a8ee: tst.w 40(a5) ; beq 0x3a908`): branch A writes `!` at row14/col30, branch B at row14/col25. Both write the same mapped tile `0x2744`. [OBS]

> **CRITICAL register-liveness difference vs the comma** [OBS]: at `0x3A8FE`/`0x3A908`, **`%d0` is LIVE across the write** — it holds the glyph char (`4`/`5` on branch A from `0x3a8f4`/`0x3a8fc`; `56` on branch B from `0x3a8ec`) that the glyph renderer at `0x3a910` (`bsr 0x3bd48`) consumes. The raw `move.w #imm,abs` does not touch `%d0`, so it currently survives; **the routing helper MUST preserve `%d0`.** The comma helper's full-`movem` (`d0-d7/a0-a6`) preserves it — safe — but unlike the comma (where `%d0` was dead), here `%d0`-preservation is load-bearing. CCR dead at both (`0x3a906` is `bra.s`; `0x3a910` is `bsr` — neither reads CCR). `%a5` live, untouched.

---

## 2. LUT / Class-B entanglement classification [OBS]

| Site | Code | LUT result | Classification |
|---|---|---|---|
| 0x3A550 | 0x0032 | `0x000A` nonzero | **CLEAN CLASS A** |
| 0x3A8FE | 0x2744 | `0x0034` nonzero | **CLEAN CLASS A** |
| 0x3A908 | 0x2744 | `0x0034` nonzero | **CLEAN CLASS A** |

None is Class-B-entangled. Note: `0x2744` is the **mapped high-code** form of low code `0x21 '!'` — the arcade writes the mapped tile **directly** (not the low code `0x21`), so `fg_fill` resolves a real preloaded slot; the Class-B low-code gap (KF-033) does **not** apply to these writes. `0x0032` is a low code but is **not** in the missing 8-key set and is preloaded (slot `0x000A`). All three route → crash fixed **and** visible tile expected. [OBS]

---

## 3. Include / defer decisions

| Site | Decision |
|---|---|
| 0x3A550 | **INCLUDE** (CLEAN CLASS A) — gated on attr-confirm (§3a) |
| 0x3A8FE | **INCLUDE** (CLEAN CLASS A) — gated on attr-confirm; `%d0`-preservation load-bearing |
| 0x3A908 | **INCLUDE** (CLEAN CLASS A) — gated on attr-confirm; `%d0`-preservation load-bearing |

All meet the INCLUDE criteria: same 6-byte inline immediate absolute shape; PC080SN FG C-window target; code word is a real PC080SN tile code; **live LUT resolves to a nonzero slot**; `fg_fill` routes it semantically; register/CCR safety matches or is explicitly proven (with the `%d0`-liveness caveat handled by full `movem`).

### 3a. Attr-confirmation gate [INT]

The paired attr (`0x00C08A50` / `0x00C08E78` / `0x00C08E64`) is **inferred `0x0000`** (single code-word writes leaving the FG-cleared attr; identical model to the comma) but — unlike the comma, which Cody dump-confirmed — **not independently runtime-dumped for these three cells.** Embedding attr `0x0000` is architecturally correct (the arcade relies on the cleared attr for a code-only write). **Required gate:** Cody confirms attr `= 0x0000` at each of `0x00C08A50/0x00C08E78/0x00C08E64` via a runtime PC080SN-FG dump before/at implementation. If any is nonzero, that single site reverts to **DEFER** (the other two still INCLUDE). This keeps the INCLUDE honest without blocking the sweep.

### Out-of-scope (remain DEFER, different shape) [OBS]

- `0x3A92A` (`move.w %d0,0xC08C62`), `0x3D24C` (`move.w %d1,0xC08C66`) — **register absolute**; routable in spirit but the source register's value/semantics need a per-site decode (confirm it holds a PC080SN tile code at that PC). DEFER as separate OPEN-018-class follow-up.
- `0x3B3CC`, `0x3B7F6`, `0x3B7F8` (`move.w dN,(aN)` in loops) — **producer loop**; different shape, needs loop routing (akin to the scroll-clear C-lite). DEFER.

---

## 4. Helper plan

**One dedicated helper per site (4 total incl. the comma); shared helper not feasible byte-neutrally.** [INT] Each site has a distinct `A0` and code baked into its instruction; the byte-neutral 6-byte `jsr` cannot pass parameters, so a single shared helper would require register setup at the site (>6 bytes → byte growth → arcade relocation). Each trampoline is tiny and delegates **all** translation/staging/dirty to the shared `fg_fill` worker.

```
; genesistan_hook_inline_fg_write_3a550   (template identical for _3a8fe / _3a908)
genesistan_hook_inline_fg_write_3a550:
    movem.l %d0-%d7/%a0-%a6, -(%sp)      ; conservative; preserves the LIVE %d0 at 3a8fe/3a908
    lea     0x00C08A50, %a0             ; cell base (attr word); fg_fill derives row/col from A0
    move.l  #0x00000032, %d0            ; attr 0x0000 << 16 | code 0x0032 (LIVE LUT resolves slot)
    moveq   #1, %d1
    bsr     genesistan_hook_tilemap_fg_fill
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts
;   _3a8fe: lea 0x00C08E78,a0 ; move.l #0x00002744,d0
;   _3a908: lea 0x00C08E64,a0 ; move.l #0x00002744,d0
```

Each helper: preserves all registers (full `movem`, covers the load-bearing `%d0` liveness at 3a8fe/3a908); sets `A0`=aligned cell base, `D0`=attr<<16|code, `D1`=1; delegates to `fg_fill` (live LUT, never embeds a literal slot); returns to the post-write instruction. If the assembler places a helper >32 KB from `fg_fill`, use `jsr genesistan_hook_tilemap_fg_fill` (+2 bytes). [INT]

---

## 5. Patch-site mechanics

| Site | Replacement | Return addr | Site byte delta |
|---|---|---|---|
| 0x3A550 | `33fc 0032 00c0 8a52` → `jsr genesistan_hook_inline_fg_write_3a550` (`4eb9 + 4`) | `0x0003A558` | **0** |
| 0x3A8FE | `33fc 2744 00c0 8e7a` → `jsr genesistan_hook_inline_fg_write_3a8fe` | `0x0003A906` | **0** |
| 0x3A908 | `33fc 2744 00c0 8e66` → `jsr genesistan_hook_inline_fg_write_3a908` | `0x0003A910` | **0** |

- **Replacement shape:** 6-byte `jsr abs.l` (byte-neutral); `bsr.w` can't reach `genesis_only`. Conditional-branch structure preserved (each guard `beq`/`bra` already targets the post-write fall-through, which equals the helper's `rts` return).
- **opcode_replace delta:** **+3** for this sweep (3 sibling patched sites); **+4 total** for the OPEN-018 pass including the comma `0x3AAEA`.
- **genesis_only growth:** +3 trampolines (~22 B each, ~66 B; ~72 if `jsr` to fg_fill); +the comma trampoline = ~88 B total. `total_genesis_bytes_covered` increases by exactly the helpers' size; `genesis_only`-internal addresses after the helpers shift (standard re-relocation, OPEN-016 class); arcade space unaffected.
- **Register/CCR concern:** full `movem` per helper preserves all registers (including the **load-bearing `%d0`** at 3a8fe/3a908); CCR dead at every site. STOP if any site's post-write fall-through differs from the table.
- **STOP conditions for Cody:** any site byte delta ≠ 0; opcode_replace delta ≠ +4 (comma + 3); any genesis_only growth beyond the four trampolines; attr-confirm (§3a) shows a nonzero attr at a routed cell (that site DEFERs, not STOP, but must be reported); any unexpected arcade-space byte change.

---

## 6. Validation plan (covers comma + 3 siblings)

1. **Build / invariants:** build succeeds; **opcode_replace +4** (comma + 3 siblings); byte invariants pass.
2. **Site byte-neutrality:** each of `0x3ACEA / 0x3A550 / 0x3A8FE / 0x3A908` = `jsr <helper>` (6 bytes); arcade space otherwise unchanged; `genesis_only` grew only by the 4 trampolines. Any other delta = STOP.
3. **Attr-confirm gate (§3a):** runtime PC080SN-FG dump shows attr `= 0x0000` at `0xC09170 / 0xC08A50 / 0xC08E78 / 0xC08E64`. Any nonzero → that site DEFERs.
4. **Raw HW watchpoints (no raw fire):** `0x00C09172`, `0x00C08A52`, `0x00C08E7A`, `0x00C08E66`.
5. **Staging checks (live-LUT slot | attr, not literal):** per routed cell —

   | Site | staged_fg_buffer offset | row,col | expected composed = `lut[code] | attr_lut[0]` | dirty bit |
   |---|---|---|---|---|
   | 0x3ACEA | `0x08B8` | 17,28 | `lut[0x2749]` (0x0039) | row 17 |
   | 0x3A550 | `0x0528` | 10,20 | `lut[0x0032]` (0x000A) | row 10 |
   | 0x3A8FE | `0x073C` | 14,30 | `lut[0x2744]` (0x0034) | row 14 |
   | 0x3A908 | `0x0732` | 14,25 | `lut[0x2744]` (0x0034) | row 14 |

   (offset = row*128 + col*2.)
6. **Live LUT checks:** confirm each staged value tracks the live LUT (not an embedded slot).
7. **Strict-target check (BlastEm / Nomad / real HW):** the four routed HW addresses no longer fault. **Honest caveat:** register-absolute (`0x3A92A`, `0x3D24C`) and producer-loop (`0x3B3CC`, `0x3B7F6`, `0x3B7F8`) raw writes remain **out of scope** and may still fault — if the strict target still crashes, capture the fault HW address; a deferred sibling is the likely culprit and the next OPEN-018-class target.
8. **Per-site expected outcome:**

   | Site | Expected |
   |---|---|
   | 0x3ACEA | crash fixed + visible tile expected |
   | 0x3A550 | crash fixed + visible tile expected |
   | 0x3A8FE | crash fixed + visible tile expected |
   | 0x3A908 | crash fixed + visible tile expected |

   (All CLEAN CLASS A — LUT nonzero. None is "crash-fixed-only / blank pending Class B.")
9. **Visual:** glyph `d0` rendering at `0x3a910` still correct (proves `%d0` preserved); `!`/decoration tiles appear at their routed cells.
10. **Out of scope (do NOT claim fixed):** Class B low-code glyphs (parens / TAITO); register-absolute and producer-loop raw writes; title/INSERT-COIN completeness.

---

## 7. Risk assessment (delta vs the comma design)

| Risk | Notes / mitigation |
|---|---|
| `%d0` clobber at 3a8fe/3a908 (NEW vs comma) | `%d0` is live (glyph char for `0x3a910`); full `movem` preserves it. **Load-bearing — call out in implementation.** |
| Inferred (not dumped) attr at 3 cells | attr `0x0000` is architecturally correct (FG-clear default for code-only writes); §3a gate requires Cody dump-confirm; nonzero → DEFER that site. |
| Stale literal slot | ELIMINATED — live LUT via `fg_fill`. |
| Wrong row/col | `fg_fill` derives from `A0`; cells decode-verified. |
| Conditional-branch structure broken | Each guard already targets the post-write fall-through = helper return; byte-neutral `jsr` keeps it. |
| Cell overwrite vs glyph renderer | Routed cells differ from the renderer's target cells; last-writer-wins per cell (same as arcade). LOW. |
| Hidden remaining siblings | register-absolute + producer-loop still raw; enumerated; validation §7 captures the fault address. |

---

## Final notes / honest scope

This sweep raises the OPEN-018 implementation pass to **4 byte-neutral routed sites** (comma + 3 same-shape siblings), all CLEAN CLASS A (crash-fixed + visible). It does **not** complete strict-target closure on its own: the register-absolute and producer-loop raw FG writes remain and may still fault — they are the next OPEN-018-class follow-ups. Recommend Cody implement the comma and these three together (one opcode_replace +4 pass) with the §3a attr gate and §5 STOP conditions.

## Open / Closed Issues Impact

- Open issues touched: **OPEN-018** (active — comma + 3 same-shape siblings designed for one implementation pass; not closed pending implementation + the register-absolute/producer-loop follow-ups). OPEN-001/OPEN-005/OPEN-017 context. OPEN-015 not touched.
- New issues opened: NONE (recommend tracking the register-absolute `0x3A92A`/`0x3D24C` and producer-loop `0x3B3CC`/`0x3B7F6`/`0x3B7F8` as explicit OPEN-018-class follow-ups if Tighe wants).
- Issues closed: NONE.
- Intentionally deferred: register-absolute and producer-loop raw writes; Class B (KF-033/OPEN-019/OPEN-020); implementation.

## STOP triggered

NO.
