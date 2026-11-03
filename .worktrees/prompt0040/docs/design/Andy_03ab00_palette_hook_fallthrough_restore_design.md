# Andy — Restore High-Score Fall-Through at 0x03AB00 (Palette-Hook RTS Suppression) — Design Only

**Author:** Andy
**Date:** 2026-06-27
**Baseline:** Build 0108 (`dist/rastan-direct/rastan_direct_video_test_build_0108.bin`, SHA256 `bd0c7faa187f6d9aded904638e8d7cb8c9e3df6304c5178a36ec02e6c8bbad09`). rastan-direct.
**Scope:** DESIGN only. No source/spec/tool/ROM/build/bookmark/diagnostic/implementation. Static design from existing evidence. Output: this doc + one AGENTS_LOG entry. Address-PC correlation via `address_map.json` (no ±0x200 as authority). Labels: **[OBS]** verified this task; **[CODY]** Cody evidence; **[INT]** interpretation.

---

## Phase 0 — Baseline

**Classification:** EXTENDING (high-score fall-through; one-site). **Contradiction:** NONE. **Root cause (pinned by Cody, re-verified statically here):** the Build 0108 palette-hook replacement at `runtime_genesis_pc 0x03AD00` terminates with an `rts` at `0x03AD06`, returning to the caller and **skipping the intact high-score setup tail at `0x03AD08+`** — palette changes, but the story isn't cleared, the high-score table isn't rendered, and the timer `FF002C`/`%a5@(44)` never reloads. One-site fix; safe siblings (`0x059AD4`, `0x045DB8`, `0x03BA64`) **not** touched [CODY]. Long-standing latent suppression exposed (not introduced) by Build 0108's rendering progress.

**JSON mapping (exact)** [OBS]: `runtime_genesis_pc 0x03AD00` = `arcade_pc 0x03AB00` (patched_site); `0x03AD06` = `arcade_pc 0x03AB06` (patched_site); `0x03AD08` = `arcade_pc 0x03AB08` (**arcade_copy** — the intact tail); `0x000714F4` = `genesis_only` (`genesistan_palette_hook_03ab00`).

---

## 1. Patch site [OBS]

- **Original 8 bytes** (arcade `move.w #0x03FF, 0x00200022` = opcode 2 + imm 2 + abs.L 4): `33FC 03FF 0020 0022`.
- **Current Build 0108 replacement 8 bytes** (`runtime_genesis_pc 0x03AD00..0x03AD07`): `4EB9 0007 14F4 4E75` = `jsr 0x000714F4` (6B) + `rts` (4E75, 2B). Verified via `xxd` and objdump.
- **Byte budget:** exactly **8 bytes**, ending at `0x03AD08`, where the intact tail begins. Any replacement must be exactly 8 bytes so execution flows into `0x03AD08`.
- **Tail at 0x03AD08 (intact, arcade_copy)** [OBS]: `0x03AD08 bsr.w 0x03B05A` (clear) → `0x03AD0C bsr.w 0x03B8BE` (init) → `0x03AD10/12/18/1E` glyph lines 60/61/62 via `bsr 0x03BD48` → `0x03AD22 move.w #0x00A0, %a5@(44)` (timer reload) → `…` → `0x03AD48 move.w #0x0002, %a5@(0)` (master advance) → `0x03AD4E clr.w %a5@(2)`.

### Recommended shape — (i) `jsr` + `nop` fall-through

**Designed 8 bytes:** `4EB9 0007 14F4 4E71` = `jsr 0x000714F4` (6B) + **`nop` (4E71, 2B)**. Only the final 2 bytes change: **`4E75` (rts) → `4E71` (nop)**.

Flow: `jsr 0x714F4` runs the palette hook → hook `rts` returns to `0x03AD06` → **`nop` executes (no-op)** → falls through to `0x03AD08` (the tail). [INT]

**Why (i) over (ii)/(iii):**
- **(i) nop fall-through — CHOSEN.** Byte-neutral (`4E75→4E71`, same 2 bytes), minimal, and the **same approved "nop as fall-through padding" idiom** used for the OPEN-018 comma fix. The hook still returns to `0x03AD06`; the nop simply lets control fall into `0x03AD08`. [INT]
- **(ii) jsr/bsr + `bra` to 0x03AD08 — REJECTED.** `0x03AD08` is the *immediate next byte* after `0x03AD06`; a `bra.s` from `0x03AD06` to `0x03AD08` would need displacement 0 (PC+2 already = `0x03AD08`), which is degenerate. A `nop` achieves the same fall-through in the same 2 bytes with no branch. Pointless. [OBS+INT]
- **(iii) trampoline that does palette work then `jmp 0x03AD08` — REJECTED.** Unnecessary: (i) fits in the 8-byte budget and is register/flag-safe (§2). A trampoline would add helper growth for no benefit. [INT]

**Invariant impact:**
- **opcode_replace count: UNCHANGED** [INT]. The patched_site segment `0x03AD00..0x03AD08` already exists; changing the `rts` byte to `nop` is a within-segment byte edit, not a new patched site. (If the tooling models it as an edited entry, it is still the same site — no count delta.)
- **total_genesis_bytes_covered: UNCHANGED** (8→8 bytes; the hook `genesistan_palette_hook_03ab00` is unchanged → no helper growth).
- Byte-neutral. If any invariant would change beyond `4E75→4E71`, that is a STOP for Cody.

---

## 2. Register / flag preservation (correctness gate)

**Palette hook `genesistan_palette_hook_03ab00`** (`palette_hooks.s:92-102`) [OBS]:
```
movem.l %d0-%d3/%a0,-(%sp)
move.w #0x03FF,%d0 ; bsr .Lxbgr555_to_cram
lea staged_palette_words,%a0 ; move.w %d1,34(%a0) ; move.b #1,palette_dirty
movem.l (%sp)+,%d0-%d3/%a0
rts
```
`.Lxbgr555_to_cram` (`palette_hooks.s`) uses only `%d0`(in)/`%d1`(out)/`%d2`/`%d3` — all within the saved set; no address registers. **`%a4`/`%a5`/`%a6` appear nowhere in `palette_hooks.s`.** [OBS]

1. **FLAGS — does `0x03AD08+` consume the original `move.w`'s condition codes?** **NO.** `0x03AD08` is `bsr.w 0x03B05A` — an unconditional subroutine call that does not read incoming CCR and whose callee clobbers it. The original `move.w #0x03FF,abs` set N=0/Z=0, but the tail never reads them. The `nop` doesn't change flags; the hook's last flag-affecting op is irrelevant. **No flag dependency.** [OBS]
2. **A5 — hook leaves `%a5` untouched?** **YES, provably.** The hook saves/restores only `%d0-%d3/%a0`, uses `%d0/%d1/%a0`, and calls `.Lxbgr555_to_cram` (d-regs only). No `%a5` reference exists anywhere in `palette_hooks.s`. The tail's heavy `%a5@(...)` accesses (timer `%a5@(44)`, master `%a5@(0)`, `%a5@(256/258/2)`) therefore see the caller's intact `%a5`. [OBS]
3. **Other registers / hook internal rts.** The hook preserves `%d0-%d3/%a0`. The tail reloads everything it needs fresh: `%a0`/`%a1` via `lea %a5@(256/258)` (0x03AD28/0x03AD30), `%d0` via `moveq #60/61/62` and `moveq #31`. It does not rely on any register left by the hook. The hook's internal `rts` returns to `0x03AD06` (= `0x03AD00 + 6`, the jsr's return address), which is the `nop`. [OBS]

> **CORRECTNESS GATE: YES.** With the `nop`-fall-through, the high-score tail at `0x03AD08+` executes correctly: flags are irrelevant (tail starts with `bsr`), `%a5` is preserved (hook never touches it), and the tail reloads its own working registers. [OBS+INT]

---

## 3. Arcade-intent rationale (intent, not opcodes)

The arcade instruction at `arcade_pc 0x03AB00` had a **two-part intent**: (1) write `0x03FF` to the CLCS/`HW_ADDRESS 0x00200022` palette RAM (xBGR_555, bank 1 entry 1) — a color effect — and (2) **fall through** into the high-score setup tail. On Genesis there is no `0x00200022` palette hardware; reproducing the literal bus write would be wrong (the project routes such writes to staging, never to arcade HW addresses). `genesistan_palette_hook_03ab00` correctly reproduces part (1) as **intent**: convert xBGR_555 → Genesis CRAM, stage at `staged_palette_words+34`, set `palette_dirty` (port-correct, Cody-validated). The Build 0108 `rts` dropped part (2). Restoring the fall-through (`rts`→`nop`) completes the **full arcade intent — palette effect + continue into high-score setup — without** reproducing the literal arcade opcode. This is the project principle: reproduce arcade intent, not arcade opcodes. [INT]

---

## 4. Validation plan for Cody (after implementation)

- Build ROM (expect new build number); canonical gate passes.
- **Byte-neutral confirmed:** the only byte change is `runtime_genesis_pc 0x03AD06` `4E75 → 4E71`; `opcode_replace` count unchanged; `total_genesis_bytes_covered` unchanged.
- No-input attract loop **reaches the high-score screen**.
- **Palette still changes** at the story→high-score transition (hook still runs).
- **Story screen CLEARS** (`0x03AD08 bsr 0x03B05A` runs).
- **High-score table RENDERS** (init `0x03AD0C` + glyph render lines 60/61/62 run).
- **`FF002C` reloads to `0x00A0`** (timer reload `move.w #0x00A0,%a5@(44)` runs — the value the user watched stuck at 0).
- **Master state advances at `0x03AD48`** (`%a5@(0)` → 2; `%a5@(2)` cleared).
- Attract loop continues past high-score (no longer repeats the palette hook / stuck loop).
- **No regression:** title, red TAITO logo, story text, INSERT COIN(S) parens (Class B), OPEN-018 comma/sibling routing — all unchanged.

---

## 5. Risks / STOP

- The fix is a single 2-byte edit within an existing patched_site; the only correctness dependency (the tail's reliance on `%a5` + flag-independence) is statically proven satisfied (§2). No STOP condition encountered — the design preserves **both** the palette-hook effect **and** the fall-through within the 8-byte budget.
- STOP (for Cody) only if: the change is not byte-neutral, `opcode_replace`/`total_genesis_bytes_covered` shift, or the hook source differs from `palette_hooks.s:92-102` at build time.

## Open / Closed Issues Impact

- Open issues touched: high-score fall-through (this one-site fix; if tracked under an OPEN id, mark design-complete pending implementation), OPEN-001 (context — attract/high-score completeness). OPEN-007 (context — palette helpers `0x59AD4`/`0x03AB00`/`0x045DB8` activation; `0x03AB00` now active and its fall-through is the fix). OPEN-015 not touched.
- New issues opened: NONE.
- Issues closed: NONE (implementation + validation required first).
- Intentionally deferred: implementation; Class B (parens/TAITO); OPEN-018 raw-write follow-ups; the safe sibling palette hooks (confirmed safe, not in scope).

## STOP triggered

NO.
