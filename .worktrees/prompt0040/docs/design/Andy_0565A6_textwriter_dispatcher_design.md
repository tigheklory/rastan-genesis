# Andy — Shared Text-Writer (0x0565A6) Entry Dispatcher: Route by Destination Through Staging (Design Only)

**Author:** Andy
**Date:** 2026-06-28
**Baseline:** Build 0112 (`dist/rastan-direct/rastan_direct_video_test_build_0112.bin`, SHA256 `024241b2378dba68102637c368bc92d5edc41b2b30776363a96144146dfe215d`). rastan-direct.
**Scope:** DESIGN only. No source/spec/tool/ROM/build/bookmark/diagnostic/implementation. Static from Cody's census + CLOSED-016 template. Output: this doc + one AGENTS_LOG entry. Code-PC correlation via `address_map.json` (no ±0x200 as authority). Labels: **[OBS]** verified this task; **[CODY]** census evidence; **[INT]** interpretation.

**Supersedes** the call-site recommendation in `docs/design/Andy_C00828_itemdesc_bg_producer_route_design.md` §3: Cody's census (Classification A) proved all 6 callers target BG C-window with the identical writer shape, so one **writer-entry dispatcher** fixes the whole class (incl. the confirmed sibling `0x056266` and future callers) instead of per-call-site patches. **Class:** KF-032 / OPEN-022.

---

## Phase 0 — Baseline

**Classification:** EXTENDING (OPEN-022, KF-032 family). **Contradiction:** NONE (refines the call-site design into the census-validated dispatcher). **Out of scope:** sprite/PC090OJ path (OPEN-024); high-score (CLOSED-015/016/017); Class B; OPEN-018 other sites; zero/blank-table family.

**JSON mappings (exact)** [OBS]: writer entry `runtime 0x0565A6` = `arc 0x0563A6`; substitution sub `runtime 0x0565CE`; 6 callers `0x05623C / 0x056266 / 0x0563F8 / 0x056420 / 0x0576FC / 0x05A6CE`.

**Census (Cody, Classification A)** [CODY]: exactly 6 direct callers; ALL resolved dests are BG C-window `[0x00C00000,0x00C03FFF]` (no FG, no non-C-window in the current ROM); identical writer shape (attr `%d1` → sub → code `%d0`; `0xFF` dest+=0x200; `0x00` term); five callers attr `%d1=0`, **`0x05A6CE` uses table-driven non-zero attrs `0x0003/0x0004/0x0005`**; source always ROM text. **Caveat:** only `0x05623C` runtime-observed; the other 5 by static table decode → complete for the current direct-call surface, **not** a promise no other text-writer use exists (gameplay/later/indirect). The dispatcher must be robust to dests beyond the 6.

---

## 1. The writer (reference) [OBS]

Entry bytes at `0x0565A6`: `2449 4240 1018 0C00 0000 671A 0C00 00FF 670A 32C1 6100 0012 32C0 60E6 D5FC 0000 0200 224A 60DC 4E75` =
```
565A6 movea.l a1,a2 ; 565A8 clr.w d0 ; 565AA move.b (a0)+,d0
565AC cmpi.b #0,d0  ; beq 565CC          ; 0x00 terminate
565B2 cmpi.b #-1,d0 ; beq 565C2          ; 0xFF advance
565B8 move.w d1,(a1)+ ; *** RAW attr     ; 565BA bsr 565CE (sub d0→d0) ; 565BE move.w d0,(a1)+ ; *** RAW code
565C0 bra 565A8
565C2 adda.l #0x200,a2 ; 565C8 movea.l a2,a1 ; bra 565A8   ; 0xFF advance
565CC rts
565CE (substitution sub, SEPARATE routine) 0x21→0x2744 … 0x3F→0x274B ; pure d0→d0 ; → rts at 5663E
```
Inputs: `a0`=ROM source, `a1`=dest HW addr (BG C-window), `d1`=attr word. The sub `0x565CE` is a separate routine after the writer's `rts` — **not** part of the entry-patch region; reusable. [OBS]

---

## 2. Approach + patch shape

**Replace the writer entry `0x0565A6` with a dispatcher** (genesis_only hook `genesistan_hook_textwriter_dispatch`) that reimplements the writer loop but **stages each composed cell via the staging path keyed by the live `%a1` destination range**, instead of raw HW writes. All 6 callers keep their `bsr.w/jsr 0x0565A6` unchanged and now reach the dispatcher.

**Entry patch shape** [OBS+INT]: overwrite the first 8 bytes at `0x0565A6` with
```
0565A6  jsr genesistan_hook_textwriter_dispatch   (4EB9 + 4 = 6 bytes)
0565AC  rts                                        (4E75, 2 bytes)
```
A caller's `bsr/jsr 0x0565A6` → `jsr dispatch` (dispatcher runs with the caller's `a0/a1/d1`) → dispatcher `rts` → returns to `0x0565AC` → `rts` → returns to the caller. The remaining writer body `0x0565AE..0x0565CC` becomes **dead** (unreachable, harmless). The substitution sub `0x0565CE` is **untouched and reused** by the dispatcher. Byte-neutral at the entry (in-place 8-byte overwrite; writer is longer, rest dead). **opcode_replace +1** (new patched_site `0x0565A6` / `arc 0x0563A6`).

---

## 3. Guarded range policy (binding — no silent drop, no raw pass-through)

Per cell, the dispatcher classifies the live `%a1` (masked to 24 bits) and routes:

- **BG C-window `[0x00C00000, 0x00C04000)` → `genesistan_hook_tilemap_bg_fill`.** [covers all 6 known callers] — the proven BG staging path.
- **FG C-window `[0x00C08000, 0x00C0C000)` → `genesistan_hook_tilemap_fg_fill`.** **Route (not defer)** [INT]: `fg_fill` has the byte-identical interface and composed-cell contract to `bg_fill` (`A0`=FG HW addr, `D0`=(attr<<16)|code, `D1`=count; same `tile_vram_lut` + `attr_lut` compose; FG buffer/window/`fg_row_dirty`) — confirmed from source. No current caller targets FG, but routing it costs one branch and makes the dispatcher robust to a future FG text caller with zero added risk (the contract is proven identical). Deferring would re-expose the same KF-032 freeze if an FG caller appears.
- **OUTSIDE both C-windows (incl. the BG-scroll gap `[0x00C04000,0x00C08000)` and anything ≥ `0x00C0C000` or below `0x00C00000`) → FAIL-LOUD TRAP/REPORT.** [INT] **Not** silent drop (would hide a future caller's bug and mis-render); **not** raw pass-through (a raw write to an illegitimate dest still freezes real Genesis / BlastEm — pass-through is not a safe default). The dispatcher records the offending dest (and caller return PC) to a WRAM diagnostic slot (audit-guard convention) and halts / reports, so an unexpected future destination becomes **visible evidence**. The per-cell check happens **before** `bg_fill`/`fg_fill` so an out-of-range dest cannot be silently NO-OP-dropped by their internal range gates.

Per-cell evaluation (not once-at-entry) so a stream whose `0xFF` advance walks past a window boundary traps instead of silently dropping. [INT]

---

## 4. Writer intent preserved (in the dispatcher)

- **ROM source walk** [OBS]: `a3 = a0` (source kept in `a3` to avoid colliding with `bg_fill`'s `A0` dest arg); `byte = (a3)+`.
- **attr from `%d1` — PRESERVED, including non-zero** [OBS, critical]: the dispatcher keeps the caller's `%d1` (attr word) in `d3` and composes `D0 = (d3 << 16) | code` per cell. It **does NOT hardcode attr 0** (unlike the FG high-score producer, which always used 0). `bg_fill`/`fg_fill` extract the PC080SN attr from `D0`'s high word and index `attr_lut` from attr bits {0,1,13,14,15}; for `0x05A6CE`'s attrs this yields `0x0003 → attr_lut[3]=0x6000`, `0x0004 → attr_lut[0]=0x0000`, `0x0005 → attr_lut[1]=0x2000` (palette-line bits reach the staged cell). The dispatcher's responsibility is to **forward `%d1` unchanged**; the attr-word→palette-line mapping is `bg_fill`/`attr_lut`'s existing model, identical to how every BG cell's attr is translated. (If the `0x0004→line0` collapse turns out wrong for the item-rank colors, that is a pre-existing `attr_lut` fidelity question, NOT a dispatcher defect — flagged in validation.)
- **`0x565CE` substitution reused** [OBS]: `jsr 0x000565CE` per cell (pure `d0→d0`, the 8 punctuation keys → `0x2744..0x274B`; no raw writes; touches only `d0`, preserves `a1/a2/a3/d3`). No reimplementation → no substitution-fidelity risk.
- **`0xFF` advance / `0x00` terminate** [OBS]: `0xFF → a2 += 0x200; a1 = a2`; `0x00 → end loop → rts`. (`a2` mirrors the writer's row base.)
- **attr/code pairing** [OBS]: one composed cell per `bg_fill`/`fg_fill` call (attr `d3` hi word, code lo word), matching the writer's attr-then-code pair per cell.

---

## 5. %a1 → staging-offset translation [OBS]

- **bg_fill interface (confirmed from source):** `A0`=BG HW addr, `D0`=(attr<<16)|code, `D1`=count; `movem.l d0-d7/a0-a6` save/restore; range-gate `[0xC00000,0xC04000)`; compose `tile_vram_lut[D0.w & 0x3FFF] | attr_lut[<bits from D0 high word>]`; store `staged_bg_buffer`; `bset #row, bg_row_dirty`. `fg_fill` is identical with FG base/buffer/dirty.
- **Formula:** `cell = ((A0 & 0xFFFFFF) − base) >> 2`; `col = cell & 0x3F`; `row = (cell >> 6) & 0x1F`; `staged-WRAM-offset = staged_{bg,fg}_buffer + row*128 + col*2`.
- **Compose with live attr:** `D0 = (%d1 << 16) | code` per cell (live `%d1`, non-zero preserved).
- **`0xFF` advance in staging terms:** after `a1 = a2 + n*0x200`, the next `bg_fill(A0=a1)` derives the correct row/col from the new `a1` (the `0x200` step = 0x80 cells = 2 BG rows). No special staging-offset math — `bg_fill` maps each `a1` to its cell.
- **Dirty/commit:** `bg_fill`/`fg_fill` set `bg_row_dirty`/`fg_row_dirty` per row → VBlank BG/FG commit propagates the staged cells.

---

## 6. Register / flag / byte mechanics

- **Entry patch (callers still land on dispatcher):** all 6 callers `bsr.w/jsr 0x0565A6`; the entry is patched to `jsr dispatch; rts`, so every caller reaches the dispatcher and returns correctly (dispatcher `rts` → `0x0565AC rts` → caller). [OBS]
- **Registers preserved for callers + loop state** [OBS+INT]: the original writer returns via `rts` and clobbers `d0/d1/a0/a1/a2`; the census shows callers re-establish `a0/a1/d1` each call → they do not depend on writer-output registers, so the dispatcher may clobber the same set (conservatively `movem`-save/restore). Loop state lives in `a3`(source)/`a1`(dest)/`a2`(rowbase)/`d3`(attr) — **not** `bg_fill`/`fg_fill` arg registers (`A0/D0/D1`); `bg_fill`/`fg_fill` `movem`-preserve them, and `0x565CE` touches only `d0`. (Same discipline as CLOSED-016.)
- **Flags:** writer returns via `rts`; callers don't consume writer-set CCR. No flag dependency.
- **Invariant impact:** `opcode_replace` **+1** (`0x0565A6` / `arc 0x0563A6`); `total_genesis_bytes_covered` **+ dispatcher hook size** (est. ~140–200 bytes — larger than the single-producer hooks due to the 3-way range dispatch + FG branch + fail-loud trap). Arcade space byte-neutral (in-place 8-byte entry overwrite; writer body `0x0565AE..0x0565CC` dead; `0x565CE` preserved). Relocation: genesis_only-internal. Pre-authorize: +1 opcode_replace; genesis_only grows by exactly the dispatcher; any other delta = STOP.
- **Dead-body handling:** writer body `0x0565AE..0x0565CC` unreachable (harmless); substitution sub `0x0565CE` live and reused.

---

## 7. Why this matches arcade intent (not literal opcodes)

The writer's **intent** is to emit ROM text as PC080SN attr/code cells (with `0xFF` row advance, `0x00` terminate, punctuation substitution, caller-supplied attr). The arcade does it with raw PC080SN word writes — correct on arcade hardware, fatal on Genesis (VDP-mirror; KF-032). The dispatcher reproduces the **intent** — same source walk, same substitution (reused), same `0xFF`/`0x00` control, same cells, **same attr including the non-zero `0x05A6CE` ranks** — through the Genesis staging path keyed by destination, and turns any unexpected destination into visible evidence rather than a silent corruptor. Reproduce intent, not opcodes; content unchanged (same ROM read), only the write path changes. [INT]

---

## 8. Validation plan for Cody (full six-caller surface; equivalence mismatch=0; non-zero attr; guarded range)

- Build; canonical gate; new build/SHA.
- **Byte-neutral entry:** only `0x0565A6` first 8 bytes changed (`jsr dispatch + rts`); `opcode_replace` +1; `total_genesis_bytes_covered` grows by exactly the dispatcher; writer body dead, `0x565CE` unchanged. Any other delta = STOP.
- **Strict target (BlastEm/real) — runtime-observed path:** NO freeze at the item-description page (`C00828`, caller `0x05623C`); zero raw producer writes to BG C-window from this writer.
- **PRODUCER-EQUIVALENCE GATE (mismatch count = 0) for ALL SIX callers** (runtime for `0x05623C`; static/synthetic decode-and-compare for the rest — do not require runtime-hitting all six):
  - `0x05623C` BG attr 0 — same cells/codes/row-col as the raw producer (runtime).
  - `0x056266` BG attr 0 — sibling `C00028`, same cells.
  - `0x0563F8` BG attr 0, selector-varying dests (table `0x564CA`) — validate each selector case.
  - `0x056420` BG attr 0, selector-varying dests (table `0x564FA`) — validate each selector case.
  - `0x0576FC` BG attr 0, source first byte `0x00` — validate it emits **no cells** (no-op), no raw write.
  - `0x05A6CE` BG **non-zero attrs 0x0003/0x0004/0x0005** — validate the composed staged cells carry the forwarded attr (the `attr_lut`-mapped palette-line bits reach the staged cell); the dispatcher forwards `%d1` unchanged.
- **`0xFF` advance + `0x00` terminate** handled across each caller's full source stream.
- **VISUAL:** item-description BG text renders (AXE/HAMMER/FIRE SWORD/SHIELD/MANTLE/ARMATURE/MEDICINE/POISON/GOLD SHEEP/JEWEL …); `C00028` sibling page text renders if reached. Sprite garbage on these pages is EXPECTED (OPEN-024). For `0x05A6CE`, spot-check that the non-zero-attr cells render in the intended palette line (if they look wrong, it's an `attr_lut`-mapping question, not a dispatcher bug — open separately).
- **Guarded-range policy (code-review acceptable if not exercised at runtime):** confirm an out-of-range destination hits the **fail-loud trap/report** path — NOT silent drop, NOT raw pass-through; confirm the FG branch routes to `fg_fill` with the same compose contract.
- **No regression:** title, TAITO, story, parens, high-score (CLOSED), OPEN-018 comma, and ALL 6 callers behave correctly (the shared entry change is the highest-blast-radius part — validate every caller).

---

## 9. Risks / STOP

| Risk | Mitigation |
|---|---|
| Shared-entry blast radius (all 6 callers) | Per-cell route by live `%a1`; equivalence gate validates all 6 caller configs (mismatch=0); FG branch + trap make non-BG dests safe. |
| Non-zero attr `0x05A6CE` lost | Dispatcher forwards `%d1` unchanged into `D0` high word; `bg_fill` `attr_lut` maps it; validation checks the staged attr bits. |
| Silent drop / raw pass-through of an unexpected dest | Explicit fail-loud trap on out-of-range; per-cell check before `bg_fill` so its internal NO-OP gate is never the silent-drop path. |
| Substitution fidelity | Reuse `0x565CE` (pure transform), no reimplementation. |
| Loop count/state clobbered by staging call | Loop state in `a3/a1/a2/d3` (non-arg, `movem`-preserved); same as CLOSED-016. |
| FG contract assumption | Confirmed `fg_fill` interface byte-identical to `bg_fill`; routing FG is zero-risk vs deferring. |
| Census incompleteness (indirect/future callers) | Dispatcher routes by live `%a1` → handles any caller; out-of-range traps loudly → future surprises become evidence. |

## Open / Closed Issues Impact

- Open issues touched: **OPEN-022** (shared text-writer raw writes — dispatcher design routing all 6 callers + future callers; not closed pending implementation + the full six-caller equivalence validation), KF-032 class (this dispatcher is the class-level fix for the 0x0565A6 writer), OPEN-001 (context — item/page visual completeness). OPEN-024 (sprite path — out of scope). OPEN-015 not touched.
- New issues opened: NONE (recommend opening an `attr_lut` fidelity item only if `0x05A6CE`'s non-zero-attr cells validate wrong-colored — pre-existing `bg_fill`/`attr_lut` behavior, not this dispatcher).
- Issues closed: NONE.
- Intentionally deferred: implementation; any `attr_lut` palette-line fidelity question for non-zero attrs; the sprite/PC090OJ path (OPEN-024); the zero/blank-table family.

## STOP triggered

NO (the dispatcher routes all known callers — and future ones by live `%a1` — preserving full writer intent: ROM walk, live attr incl. non-zero, `0x565CE` substitution, `0xFF` advance, `0x00` terminate; with a fail-loud guarded-range policy).
