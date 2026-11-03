# Andy — Build 0105 HV-Counter Root Cause + Fix Design (raw PC080SN fill into VDP mirror)

**Author:** Andy
**Date:** 2026-06-25
**Build:** 0105 canonical (`dist/rastan-direct/rastan_direct_video_test_build_0105.bin`, byte-identical to 0097). rastan-direct.
**Scope:** Static attribution + fix **DESIGN only**. No source/spec/tool/ROM/build/bookmark/sanitizer changes. No implementation. Disassembly from the canonical 0105 ROM (`m68k-elf-objdump`) + ELF symbols; addresses are **runtime_genesis_pc = ROM file offset**. All arcade↔Genesis correlation via `build/rastan-direct/address_map.json` (no ±0x200 arithmetic as authority). Labels: **[OBS]** observable; **[INT]** interpretation; **[MAME]** from in-repo MAME reference.

---

## Phase 0 — Baseline

**Classification:** EXTENDING, OPEN-017. **Context:** OPEN-005 (historical HV), OPEN-001 (title render). **OPEN-015 not touched.**

**Contradiction status (superseded priors, acknowledged):**
- The prior `0x70000..0x70244` bisection bracket (my `Andy_build_0104_hv_counter_cluster_decode.md`) is **superseded** by the user's Build-0105 BlastEm single-step trace.
- The prior **0x7186C audit-guard theory is withdrawn** — the user's single-step proves `0x7186C` is *not reached* before the fatal. (The audit-guard HV read is real code but is **not** this crash.)
- The new evidence identifies the fatal raw-write path at **runtime_genesis_pc 0x3AF3C**, called from **0x3B152** with A0=0xC04000. This report confirms it statically and designs the fix.

---

## 1. Address mapping (all via address_map.json — exact) [OBS]

| runtime_genesis_pc | gen segment (start..end) | kind | arcade_pc | confidence |
|---|---|---|---|---|
| 0x3B152 | 0x3B152..0x3B172 | arcade_copy | 0x3AF52 | exact |
| 0x3B158 | 0x3B152..0x3B172 | arcade_copy | 0x3AF58 | exact |
| 0x3B15C | 0x3B152..0x3B172 | arcade_copy | 0x3AF5C | exact |
| 0x3B15E | 0x3B152..0x3B172 | arcade_copy | 0x3AF5E | exact |
| 0x3AF3C | 0x3AF2E..0x3AF44 | arcade_copy | 0x3AD3C | exact |
| 0x3AF3E | 0x3AF2E..0x3AF44 | arcade_copy | 0x3AD3E | exact |
| 0x3AF40 | 0x3AF2E..0x3AF44 | arcade_copy | 0x3AD40 | exact |
| 0x3AF44 | 0x3AF44..0x3AF4C | **patched_site** | 0x3AD44 | exact |
| 0x3AF4A | 0x3AF44..0x3AF4C | **patched_site** | 0x3AD4A | exact |
| 0x717D8 | 0x70000..0x17CD28 | genesis_only | — | `genesistan_hook_3ad44_dispatch` |
| 0x70588 | 0x70000..0x17CD28 | genesis_only | — | `genesistan_hook_tilemap_bg_fill` |
| 0x7065E | 0x70000..0x17CD28 | genesis_only | — | `genesistan_hook_tilemap_fg_fill` |

For genesis_only addresses the symbol comes from the 0105 ELF symbol table. **No mapping guessed.**

---

## 2. Raw fill (0x3AF3C) vs hooked dispatch (0x3AF44) [OBS]

Disassembly (canonical 0105):
```
; --- raw word-fill primitive (arcade_copy = arcade 0x3AD3C) ---
3AF3C: 30c0        move.w d0,(a0)+
3AF3E: 5341        subq.w #1,d1
3AF40: 66fa        bne.s  0x3AF3C
3AF42: 4e75        rts
; --- patched dispatch entry (patched_site = arcade 0x3AD44) ---
3AF44: 4eb9 0007 17d8   jsr 0x717D8     ; genesistan_hook_3ad44_dispatch
3AF4A: 4e75            rts
```
- **0x3AF3C is the raw arcade word-fill primitive** (fill d1 words of value d0 through `(a0)+`). It is `arcade_copy` — copied verbatim, **never hooked**. [OBS]
- **0x3AF44 is the patched dispatch entry** used by the sibling clears — it `jsr`s `genesistan_hook_3ad44_dispatch` (0x717D8), which routes by A0 into staging. [OBS]
- They are **adjacent but distinct routines** (the raw loop ends with `rts` at 0x3AF42; the patched site begins at 0x3AF44). They are **not** two entry points of one routine. [OBS]

**Why siblings call 0x3AF44 but the failing clears call 0x3AF3C** [OBS+INT]: in the original arcade these are *two different primitives* — arcade `0x3AD44` is the **tilemap fill** routine (writes nametable cells → needs staging → was hooked), arcade `0x3AD3C` is a **generic word-fill** (used for assorted memory, including scroll RAM and WRAM → left raw). The translation hooked the tilemap-fill primitive but not the generic word-fill. The defect is that the generic word-fill is *also* used to clear PC080SN scroll RAM at `0xC04000`/`0xC0C000`, which on Genesis is VDP mirror space.

---

## 3. The four title-init clears (one site, full quartet) [OBS]

```
3B12C: lea 0xC00000,a0 ; #4096,d1 ; #32,d0  ; bsr 0x3AF44   ; BG tilemap names → HOOKED  ✓ clean
3B13C: lea 0xC08000,a0 ; #4096,d1 ; #32,d0  ; bsr 0x3AF44   ; FG tilemap names → HOOKED  ✓ clean
3B152: lea 0xC04000,a0 ; #8192,d1 ; clr.l d0; bsr 0x3AF3C   ; C04000 → RAW  ◄── FATAL (proven)
3B162: lea 0xC0C000,a0 ; #8192,d1 ; clr.l d0; bsr 0x3AF3C   ; C0C000 → RAW  ◄── LATENT (fatals next)
```
Live setup at the fatal (matches the user trace): A0=0xC04000, D1=0x2000, D0=0, loop walks `0xC04000..0xC08000`. [OBS]

---

## 4. What 0xC04000 / 0xC0C000 are — PC080SN per-line SCROLL RAM [MAME]

`pc080sn.cpp:104-164`:
```
PC080SN_RAM_SIZE = 0x10000
m_bg_ram[0]       = m_ram + 0x0000   →  68k 0xC00000-0xC03FFF : BG tilemap[0]   (word_w marks tilemap[0] dirty)
m_bgscroll_ram[0] = m_ram + 0x4000   →  68k 0xC04000-0xC07FFF : BG per-line SCROLL RAM (no dirty mark)
m_bg_ram[1]       = m_ram + 0x8000   →  68k 0xC08000-0xC0BFFF : FG tilemap[1]   (word_w marks tilemap[1] dirty)
m_bgscroll_ram[1] = m_ram + 0xC000   →  68k 0xC0C000-0xC0FFFF : FG per-line SCROLL RAM (no dirty mark)
```
So the quartet is: **BG names (C00000) + BG scroll RAM (C04000) + FG names (C08000) + FG scroll RAM (C0C000).** The two *hooked* clears are the tilemap nametables; the two *raw* clears are the **per-line scroll RAM**. [MAME+INT]

This aligns with the project's C-window model (`tilemap_hooks.s:42-44`): `CWINDOW_BASE_BG=0xC00000`, `CWINDOW_BASE_FG=0xC08000`, `CWINDOW_BYTES=0x4000` — i.e. the staged BG/FG windows are exactly `[0xC00000,0xC04000)` and `[0xC08000,0xC0C000)`. `0xC04000-0xC08000` and `0xC0C000-0xC10000` lie **outside** the staged windows. [OBS]

> **Staging target for the C04000/C0C000 clears:** *none.* They are PC080SN **per-line scroll RAM**, which the Genesis port does **not** translate — KF-015's full-plane scroll model (single `staged_scroll_x/y_bg/fg`, committed by `vdp_commit_scroll`) has no per-line scroll table, and boot already clears `staged_scroll_*` to 0 (`boot.s:226-229`). The arcade "clear per-line scroll RAM to 0" therefore maps to "full-plane scroll = 0", which is already the Genesis state. [OBS+INT]
> *Confirm-before-implement (one item):* MAME's internal pointer setup overlaps the BG code-plane read (`get_tile_info<0>` reads `m_bg_ram[0][tile_index+0x2000]`) with `m_bgscroll_ram[0]`. The project's working render treats `0xC00000-0xC04000` as the full BG cell window (bg_fill consumes the fill value as the *tile code* via `tile_vram_lut`), so `0xC04000` is **not** the active code source in the project's model. Confidence HIGH that 0xC04000 = scroll RAM; if the team wants certainty, confirm against the PC080SN datasheet. The fix below is **safe either way** (§6).

---

## 5. Does the existing dispatch hook support a C04000/C0C000 path? [OBS]

`genesistan_hook_3ad44_dispatch` (`pc090oj_hooks.s:353-406`) routes `A0 ∈ [0xC00000,0xC10000)` to the tilemap path, splitting at `0xC08000`: `< 0xC08000 → bg_fill`, `≥ 0xC08000 → fg_fill`. But both fill helpers **range-gate to the C-windows only**:
- `genesistan_hook_tilemap_bg_fill` (0x70588): accepts `[0xC00000,0xC04000)`; `cmpi #0xC04000 ; bhs .Lbg_fill_done` → **NO-OP for A0 ≥ 0xC04000**.
- `genesistan_hook_tilemap_fg_fill` (0x7065E): accepts `[0xC08000,0xC0C000)`; `bhs .Lfg_fill_done` → **NO-OP for A0 ≥ 0xC0C000**.

So **A0=0xC04000 → bg_fill → NO-OP**, and **A0=0xC0C000 → fg_fill → NO-OP** (both still inside `[0xC00000,0xC10000)`, so **no** audit fall-through, **no** fatal). [OBS]

> **The dispatch already absorbs the scroll-RAM ranges correctly** (clean NO-OP, no VDP write). This is *not* the prohibited "drop a tilemap clear": the NO-OP'd ranges are **scroll RAM**, which has no Genesis nametable target — absorbing equals the faithful full-plane translation (scroll 0). Contrast Build 0094, where a NO-OP'd **FG nametable** clear *was* a real drop. [INT]

---

## 6. Fix shape — Candidate A (repoint), recommended

**Repoint the two raw call sites to the existing hooked dispatch**, matching the sibling pattern:
```
0x3B15E:  bsr 0x3AF3C  (6100 fddc)  →  bsr 0x3AF44  (6100 fde4)     ; C04000 clear
0x3B16E:  bsr 0x3AF3C  (6100 fdcc)  →  bsr 0x3AF44  (6100 fdd4)     ; C0C000 clear
```
(Displacements: 0x3AF44−0x3B160 = −0x21C = 0xFDE4; 0x3AF44−0x3B170 = −0x22C = 0xFDD4.) [OBS-derived]

After repointing, each clear enters the dispatch with A0=0xC04000 / 0xC0C000 → bg_fill / fg_fill → clean NO-OP (§5). The crash is removed; arcade intent (per-line scroll → 0) is preserved by the full-plane model. The mismatched `d0=0`/`d1=8192` are irrelevant (range gate NO-OPs before consuming them). **The fix is safe whether 0xC04000 is scroll RAM or (worst case) an inactive code plane** — either way it no longer raw-writes VDP mirror, and the project's render is driven from the `[0xC00000,0xC04000)`/`[0xC08000,0xC0C000)` windows that remain hooked.

**Rejected — Candidate B (hook the raw primitive 0x3AF3C):** the primitive has a **legitimate WRAM caller** at `0x3AB9E` (`lea %a5@(128),%a0` → A0=0xFF0080, D1=96 — a normal Genesis WRAM clear). Hooking/redirecting 0x3AF3C would corrupt or burden that legal use. [OBS]

**Optional — Candidate C (explicit scroll-RAM branch in the dispatch):** add documented branches in `genesistan_hook_3ad44_dispatch` for `[0xC04000,0xC08000)` and `[0xC0C000,0xC10000)` that explicitly absorb (rts) the scroll-RAM clear (and become the natural home if per-line scroll is ever translated to the Genesis HSCROLL table). Adds helper code → relocation/byte growth. Higher cost; recommend only if the team prefers explicit intent over relying on the fill helpers' gates.

### Exact named locus (Candidate A)
- Call site 1: runtime `0x3B15E` / arcade `0x3AF5E` — the `bsr` displacement word.
- Call site 2: runtime `0x3B16E` / arcade `0x3AF6E` — the `bsr` displacement word.
- File: the build's opcode-replacement manifest for these arcade sites (same mechanism that produced the `0x3AF44 = jsr hook` patched_site). No `.s` helper changes for Candidate A.

### Expected invariant impact (Candidate A)
- **opcode_replace count:** 96 → **98** (two arcade call sites become patched displacement edits). [INT — confirm against the build tooling's accounting]
- **total_genesis_bytes_covered:** **unchanged** — both edits are in-place 2-byte displacement changes (same `bsr.w` opcode, same length). **No relocation** of subsequent `runtime_genesis_pc` addresses.
- **Helper growth:** **none** (reuses the existing dispatch). (Candidate C *would* grow helpers.)
- **Changes existing vs adds new:** adds two new patched sites within the formerly-`arcade_copy` segment `[0x3B152,0x3B172)` (likely splitting that segment in the map).
- **Risks:** title graphics — **none** (scroll RAM, not nametable; BG/FG nametable staging at C00000/C08000 untouched); BG/FG plane staging — unaffected; dirty bits — unaffected (NO-OP path doesn't touch them). The only behavioral change is the removal of the illegal VDP-mirror writes.

---

## 7. Other unhooked raw writes to VDP/sprite space (required scan) [OBS]

Full-ROM scan results:

| site | target | mechanism | hooked? | risk | disposition |
|---|---|---|---|---|---|
| **0x3B15E** | A0=0xC04000 (BG scroll RAM) | `bsr 0x3AF3C` raw fill | **NO** | **PROVEN FATAL** | Candidate A repoint |
| **0x3B16E** | A0=0xC0C000 (FG scroll RAM) | `bsr 0x3AF3C` raw fill | **NO** | **LATENT (next)** | Candidate A repoint |
| 0x3AB9E | A0=0xFF0080 (WRAM) | `bsr 0x3AF3C` raw fill | n/a (WRAM) | **SAFE** | leave (legal Genesis WRAM clear) |
| 0x3B12C / 0x3B13C | C00000 / C08000 (names) | `bsr 0x3AF44` | YES | safe | none |
| 0x3B064 / 0x3B074 | C00100 / C08100 (attract clr) | `bsr 0x3AF44` | YES | safe | none |
| 0x3AF4C-0x3AF76 | D00000 / D00170 (PC090OJ) | `bsr 0x3AF44` / 0x3AF72 | YES | safe | none |
| 0x3BAB4 / 0x3BACC / 0x3BADC | D00020/D000E0/D00128 (sprites) | `bsr 0x3BB30 → jsr 0x7173A` | YES | safe | none |
| **0x3B392 (producer)** | A0=0xC09376+row (FG tilemap) | inline `move.w d0,(a0)` loop | **NO** | **LATENT FATAL** | same class, *different mechanism* — see below |

**Same defect class, distinct sub-type — the title-text producer at 0x3B392** [OBS+INT]: it writes characters directly with `move.w d0,(a0)` to `0xC09376+row*512` (FG tilemap space; `0xC09376 & 0x1F = 0x16`, an HV/PSG-region alias) — a raw, un-hooked producer (includes the `SEX`→`AHA` censor at 0x3B3E0). It runs **after** the clears, so BlastEm never reached it (it fataled at 0x3B152 first); on MAME its raw writes hit VDP mirror (a likely contributor to title mis-render). **Fixing the clears will expose this on BlastEm.** Its fix is *not* a call-site repoint (it is inline, not via the fill primitive) — it must route through the FG store/glyph staging hook, and is a **separate design task**. There are ~3 raw `move.w dN,(aN)` stores in the `0x3B380..0x3B800` producer window to audit alongside it.

> **Conclusion on completeness:** fixing only 0x3B152 is **not** complete. The minimal *crash-class for the init clears* requires **both** 0x3B152 **and** 0x3B16E (Candidate A). Beyond that, the producer raw-writes (0x3B392 et al.) are the **next** exposure and need their own routing pass.

---

## Answers to the required questions

1. **Address mapping confirmed** via JSON — YES, all exact (§1).
2. **0x3AF3C vs 0x3AF44** — distinct adjacent routines: 0x3AF3C = raw word-fill primitive (arcade_copy, unhooked); 0x3AF44 = patched dispatch entry (`jsr 0x717D8`). (§2)
3. **0xC04000 = PC080SN BG/Plane-B region?** — it is the **BG per-line SCROLL RAM** (`m_bgscroll_ram[0]`), associated with BG/tilemap[0] but **not** the BG nametable window; no Genesis staging target (full-plane model). 0xC0C000 = FG scroll RAM. (§4)
4. **Dispatch hook already supports a C04000/C0C000 path?** — it **routes** them (into bg_fill/fg_fill) and they cleanly **NO-OP** (range-gated); it does not *stage* them, which is correct because they are scroll RAM. So: **supported as a safe absorb, YES; as a staging path, N/A.** (§5)
5. **Fix shape** — **repoint the call sites (Candidate A)**; no new hook path strictly required (Candidate C optional for explicit intent). Not Candidate B (raw primitive has a legit WRAM caller). (§6)
6. **Other unhooked raw fills** — **YES:** 0x3B16E (C0C000, same class, latent) and the inline producer 0x3B392 (same class, different mechanism, latent). 0x3AB9E is safe (WRAM). Sprites are hooked. (§7)

---

## Proposed KNOWN_FINDINGS entry (verbatim; not edited — rules do not authorize Andy to edit KNOWN_FINDINGS.md)

> **KF-XXX: Raw arcade PC080SN/PC090OJ fills must route through staging, not Genesis VDP mirror space**
>
> **Confidence:** STRONG (proven by Build 0105 BlastEm single-step trace + static disasm/JSON). **Rediscovery hazard:** HIGH (MAME-tolerant, BlastEm/Nomad/HW-fatal — symptom hides on the common dev emulator).
>
> **Proven instance (Build 0105):** runtime_genesis_pc `0x3B152` sets A0=0x00C04000; `0x3B158` D1=0x2000; `0x3B15C` clr D0; `0x3B15E` `bsr 0x3AF3C` (raw word-fill `move.w d0,(a0)+ ; subq #1,d1 ; bne`); the loop walks 0xC04000..0xC08000 and BlastEm fatals **"Illegal write to HV Counter port 8"** at the first address whose low port bits select the HV counter — `0xC04008`, where `(address & 0x1F) == 0x08`. The arcade meaning is a legal PC080SN per-line scroll-RAM clear (`m_bgscroll_ram[0]`); on Genesis 0xC0xxxx is VDP mirror.
>
> **General rule:** arcade PC080SN/PC090OJ tilemap/scroll/sprite fills or clears to 0xC00000-class or 0xD00000-class addresses must **never** execute as raw Genesis 68000 writes. They must route through the PC080SN/PC090OJ dispatch/staging path (`0x3AF44 → genesistan_hook_3ad44_dispatch`, or the sprite staging hook), or a site-specific staging equivalent, preserving arcade intent. Sibling routed paths prove the pattern: C00000 and C08000 clears go through `0x3AF44`; C04000 and C0C000 were left on the raw primitive `0x3AF3C` and must be repointed. **Do not** fix by sanitizing VDP ports, suppressing 0xC00008 writes, mirroring hardware, mimicking MAME tolerance, or dropping a *nametable* clear. (Absorbing a *scroll-RAM* clear is correct only because the full-plane scroll model has no per-line target.)
>
> **Detection signature:** symptom = BlastEm "Illegal write to HV Counter port 8" / Nomad / strict-HW black screen, while MAME appears tolerant. First thing to check = a raw arcade fill/clear loop (`move.w`/`move.l` through `(aN)+`) or inline producer store with Ax in 0xC00000..0xC10000 or 0xD00000..0xD00800 whose call path did **not** route through the dispatch/staging hook. **Scan for all such sites** — fixing one exposes the next. Known same-class latent sites in Build 0105: `0x3B16E` (C0C000 scroll-RAM clear) and the inline title-text producer at `0x3B392` (writes 0xC093xx FG tilemap raw).

---

## Required final response (summary)

- **Root cause confirmed:** YES.
- **Root cause:** raw arcade fill 0x3AF3C from 0x3B152, A0=0xC04000 walking into the HV mirror — **YES**.
- **JSON mapping:** all segments recorded, exact — **YES**.
- **3AF3C raw vs 3AF44 hooked:** distinct adjacent routines (raw word-fill vs patched dispatch `jsr 0x717D8`).
- **Why 0x3B152 raw while siblings hooked:** arcade used two primitives (tilemap-fill 0x3AD44 hooked; generic word-fill 0x3AD3C left raw); the scroll-RAM clears call the generic one.
- **0xC04000 staging target:** confirmed — **PC080SN per-line scroll RAM**, no Genesis nametable target (full-plane model); 0xC0C000 = FG scroll RAM.
- **Dispatch hook has a C04000/C0C000 path:** routes + clean NO-OP (absorb) — staging path **N/A** (correct).
- **Fix shape:** **repoint call sites 0x3B15E + 0x3B16E from 0x3AF3C to 0x3AF44** (Candidate A); Candidate C optional.
- **Exact named locus:** runtime 0x3B15E/0x3B16E, arcade 0x3AF5E/0x3AF6E, the `bsr.w` displacement words.
- **Expected invariant impact:** opcode_replace 96→98; total_genesis_bytes_covered unchanged; no helper growth; no relocation.
- **Other unhooked raw fills found:** YES — 0x3B16E (latent, same class), 0x3B392 producer (latent, different mechanism); 0x3AB9E safe (WRAM); sprites hooked.
- **Complete cause:** PARTIAL — both 0x3B152 and 0x3B16E for the clear class; producer 0x3B392 is the next exposure.
- **Genesis-bug vs arcade-intent:** **Genesis translation bug** (arcade code is a faithful, legal PC080SN clear; the translation failed to route two raw-fill call sites through staging). Not arcade-intent, not a VDP command-word defect.
- **Safe-to-implement-as-designed:** YES for Candidate A (byte-neutral, reuses proven dispatch; one confirm item in §4 does not block — fix is safe either way).
- **KNOWN_FINDINGS proposal:** included verbatim (title + body + detection signature + other-instances list); KNOWN_FINDINGS.md NOT edited (rules do not authorize Andy).
- **STOP status:** NO.

---

## Open / Closed Issues Impact

- Open issues touched: **OPEN-017** (active — HV crash root cause confirmed = raw PC080SN scroll-RAM fill into VDP mirror at 0x3B152/0x3AF3C; fix designed; not closed pending implementation + the producer-class follow-up). OPEN-005 (context — distinct from historical HV). OPEN-001 (context — producer raw-writes likely also affect title render on MAME).
- New issues opened: NONE (recommend logging "raw PC080SN/PC090OJ writes bypassing staging" as a tracked class, and a separate item for the 0x3B392 producer). Issues closed: NONE.
- Intentionally deferred: the title-text producer raw-write fix (0x3B392 et al. — separate routing design), per-line-scroll translation (future, if needed), implementation.

## KNOWN_FINDINGS impact

Option C proposed (new KF-XXX above); KNOWN_FINDINGS.md **not** edited (Andy not authorized).

---

# REVISION — Candidate A → Candidate C-lite (intent-preserving named scroll-RAM home)

**Date:** 2026-06-25 (revision). **Type:** fix-design revision (user decision authoritative). **Root cause UNCHANGED** (raw fill 0x3AF3C from 0x3B152/0x3B16E walks PC080SN per-line scroll RAM 0xC04000/0xC0C000 into the Genesis VDP HV mirror → BlastEm fatal). **Classification:** EXTENDING, OPEN-017. **Contradiction:** NONE — this REFINES §6 (Candidate A), it does not change the proven root cause or the call-site repoint target.

## R0. What changes and why

§6 Candidate A removed the crash by repointing the two call sites to the existing dispatch, where the scroll-RAM ranges fell into the bg_fill/fg_fill **silent range-gate NO-OP**. **The user rejects the silent absorb.** The arcade intent (clear BG/FG PC080SN per-line scroll RAM) is real; the full-plane scroll model (KF-015) merely doesn't *render* per-line scroll *yet*. The operation may be visually inert today, but it must have a **named, input-preserving semantic home** in the Genesis helper layer — not vanish into an unrelated tilemap range gate. [user decision]

**Unchanged from Candidate A:** the call-site repoint *target* (0x3AF44) and *bytes* are identical (§R3). **Changed:** the dispatch no longer relies on the bg_fill/fg_fill gate to absorb scroll ranges — it gains **explicit named branches** that call **named scroll-RAM handlers** receiving A0/D0/D1.

## R1. Revised fix shape (C-lite)

Three parts:

**(a) Named scroll-RAM handlers** — new genesis_only helpers (file: `apps/rastan-direct/src/tilemap_hooks.s`, alongside `bg_fill`/`fg_fill`):

```
; genesistan_hook_pc080sn_bg_scroll_fill
;   Intent: arcade PC080SN BG per-line scroll-RAM fill/clear (m_bgscroll_ram[0]).
;   IN:  A0 = target (0xC04000-class)   D0 = fill value (word)   D1 = word count
;   BG/FG identity: BG (this handler); A0 in [0xC04000,0xC08000).
;   FUTURE HOME (KF-015 full-plane scroll model): translate per-line scroll into the
;     Genesis HSCROLL table, OR reduce a uniform per-line scroll to the full-plane
;     staged_scroll_x/y_bg. CURRENT: full-plane model renders no per-line scroll, so
;     this is visually inert — but the intent is received and represented here.
;   MUST NOT raw-write 0xC04000 / touch VDP ports.
genesistan_hook_pc080sn_bg_scroll_fill:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    ; stub: A0/D0/D1 intent received; no staging emitted under the full-plane model.
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

; genesistan_hook_pc080sn_fg_scroll_fill  — same, FG (m_bgscroll_ram[1]), A0 in [0xC0C000,0xC10000).
```

Two named handlers (mirrors the `bg_fill`/`fg_fill` sibling pattern) are preferred over one identity-parameterized handler, because the dispatch already separates BG/FG by A0 range, so each branch calls its specific handler with no extra identity plumbing. (A single `genesistan_hook_pc080sn_scroll_fill` deriving BG/FG from A0 is an acceptable equivalent.)

**(b) Explicit named branches in the dispatch** — replace the implicit "everything in [0xC00000,0xC10000) → bg/fg name-fill (which silently NO-OPs the scroll ranges)" with an explicit 4-way split matching the real PC080SN layout (names | scroll | names | scroll). In `genesistan_hook_3ad44_dispatch` (`pc090oj_hooks.s`), revise `.Lhook_3ad44_tilemap`:

```
.Lhook_3ad44_tilemap:                 ; d2 = A0, known in [0xC00000,0xC10000)
    cmpi.l  #0x00C04000, %d2
    blo.s   .Lhook_3ad44_bg_names     ; [C00000,C04000) BG nametable  -> bg_fill
    cmpi.l  #0x00C08000, %d2
    blo.s   .Lhook_3ad44_bg_scroll    ; [C04000,C08000) BG scroll RAM -> bg_scroll_fill  [NEW NAMED]
    cmpi.l  #0x00C0C000, %d2
    blo.s   .Lhook_3ad44_fg_names     ; [C08000,C0C000) FG nametable  -> fg_fill
    bra.s   .Lhook_3ad44_fg_scroll    ; [C0C000,C10000) FG scroll RAM -> fg_scroll_fill  [NEW NAMED]
.Lhook_3ad44_bg_names:
    bsr     genesistan_hook_tilemap_bg_fill
    bra     .Lhook_3ad44_finish
.Lhook_3ad44_bg_scroll:
    bsr     genesistan_hook_pc080sn_bg_scroll_fill
    bra     .Lhook_3ad44_finish
.Lhook_3ad44_fg_names:
    bsr     genesistan_hook_tilemap_fg_fill
    bra     .Lhook_3ad44_finish
.Lhook_3ad44_fg_scroll:
    bsr     genesistan_hook_pc080sn_fg_scroll_fill
    bra     .Lhook_3ad44_finish
```

A0/D0/D1 are intact at each `bsr` (the dispatch only consumes `d2 = copy of A0`), so every handler receives the arcade operands. **No silent fall-through; every range has a named destination.** [OBS — dispatch consumes only d2; INT — branch design]

**(c) Call-site repoint** — same as §6 (route the two raw sites to the dispatch at 0x3AF44 so they reach the named branches).

## R2. Dispatch mechanism choice — new named branch INSIDE the existing dispatch (not a new entry)

Chosen: **new named branches inside `genesistan_hook_3ad44_dispatch`** (reached via the existing patched site 0x3AF44). Rationale: (1) matches the sibling pattern exactly — the name clears already reach the dispatch via 0x3AF44; (2) `bsr.w` from the call sites can reach arcade-space 0x3AF44 byte-neutrally but **cannot** reach a genesis_only entry (0x70000+) without changing the instruction length (4→6 bytes → relocation) — so a "new dedicated entry called directly from the call site" is rejected as non-byte-neutral; (3) keeps one unified PC080SN/PC090OJ fill dispatcher. [OBS+INT]

## R3. Exact call-site repoint mechanism + bytes (unchanged from §6)

In-place 2-byte `bsr.w` displacement edits (same opcode/length), arcade_copy → patched_site:
- runtime **0x3B15E** / arcade **0x3AF5E**: `6100 FDDC` (→0x3AF3C) → **`6100 FDE4`** (→0x3AF44). [disp 0x3AF44−0x3B160 = −0x21C]
- runtime **0x3B16E** / arcade **0x3AF6E**: `6100 FDCC` (→0x3AF3C) → **`6100 FDD4`** (→0x3AF44). [disp 0x3AF44−0x3B170 = −0x22C]

Both still pass A0=0xC04000/0xC0C000, D0=0, D1=0x2000 to the dispatch → routed by the new named branches to the scroll handlers. [OBS-derived]

## R4. Invariant impact (revised — helper growth now EXPECTED)

- **opcode_replace count:** +2 (the two call-site repoints) → 96 → **98**. (Confirm against build tooling accounting; the dispatch/handler edits are genesis_only, not opcode_replace.)
- **total_genesis_bytes_covered:** **INCREASES** (helper growth) — cause: the new `.Lhook_3ad44_tilemap` 4-way split (~3 added `cmpi.l` + branches) plus two new stub handlers (~`movem`/`movem`/`rts` each). Order ~50–90 bytes of new genesis_only code (exact at assembly time; design only). Pre-state category: genesis_only helper region (segment 0x70000..0x17CD28).
- **Helper growth:** **YES** (intended — this is the named-home cost the user accepted).
- **Relocation risk:** confined to **genesis_only internal addresses** after the edit points (the dispatch and any helpers placed after it shift; e.g. `genesistan_hook_3ad44_dispatch`'s own address and downstream symbols, and the absolute `jsr 0x717D8` in the patched site 0x3AF44 must be re-resolved). **Arcade space (0x200–0x70000) is unaffected** (call-site edits are byte-neutral in place). Standard re-link + re-relocation + `address_map.json` regen (OPEN-016 class). To minimize churn, place the new stub handlers at the **end** of the genesis_only helper region so existing helper addresses don't move; only the in-place dispatch growth shifts symbols after it.

## R5. Shared primitive 0x3AF3C — UNTOUCHED

Confirmed: the fix never modifies 0x3AF3C (the raw word-fill primitive). Its legitimate WRAM caller at **0x3AB9E** (A0=0xFF0080, D1=96) keeps using it unchanged. [OBS]

## R6. 0x3B392 producer — SEPARATE next task (restated)

The inline title-text producer at 0x3B392 (raw `move.w d0,(a0)` to 0xC093xx FG tilemap; same defect *class*, different *mechanism* — inline producer, not the fill primitive) is **out of scope for this design**. It needs its own routing pass (through the FG store/glyph staging hook) and will surface on BlastEm once these clears are fixed. [OBS]

## R7. Final response (revision)

- **Revision done:** YES. **Root cause unchanged:** YES.
- **Fix shape = named scroll-RAM stub handlers receiving A0/D0/D1 + call-site repoint (NOT NO-OP):** YES.
- **Handler name(s) + file + signature:** `genesistan_hook_pc080sn_bg_scroll_fill` and `genesistan_hook_pc080sn_fg_scroll_fill`, in `apps/rastan-direct/src/tilemap_hooks.s`; signature IN: A0=target range, D0=fill word, D1=word count; BG/FG identity by handler + A0 range; stub bodies (movem save/restore, no VDP write).
- **Dispatch: new branch vs new entry:** **new named branches inside `genesistan_hook_3ad44_dispatch`** (4-way names|scroll|names|scroll split in `.Lhook_3ad44_tilemap`), reached via existing patched site 0x3AF44.
- **Call-site repoint mechanism + exact bytes:** in-place `bsr.w` displacement edit — 0x3B15E `6100 FDDC`→`6100 FDE4`; 0x3B16E `6100 FDCC`→`6100 FDD4`.
- **Inputs preserved (A0/D0/D1 + BG/FG identity):** YES (dispatch consumes only d2=A0 copy; handlers get original A0/D0/D1; BG/FG by range/handler).
- **0x3AF3C untouched (WRAM caller preserved):** YES.
- **Invariant impact:** opcode_replace +2 (→98); total_genesis_bytes_covered INCREASES (helper growth ~50–90 B, genesis_only); helper growth YES; relocation risk = genesis_only-internal only, arcade space unaffected, standard regen (OPEN-016).
- **KF-015 future-home documented in handler:** YES (per-line-scroll → Genesis HSCROLL table, or uniform-per-line → full-plane reduction).
- **0x3B392 restated as separate task:** YES.
- **Safe-to-implement-as-revised:** YES (crash fix identical; intent now has a named, input-preserving home; relocation is the standard helper-growth class).
- **KNOWN_FINDINGS proposal updated:** YES (see below).

## R8. KNOWN_FINDINGS proposal — UPDATED (supersedes §"Proposed KNOWN_FINDINGS entry"; verbatim; not edited into KNOWN_FINDINGS.md — Andy not authorized)

> **KF-XXX: Raw arcade PC080SN/PC090OJ fills must route through staging, not Genesis VDP mirror space**
>
> **Confidence:** STRONG (Build 0105 BlastEm single-step + static disasm/JSON). **Rediscovery hazard:** HIGH (MAME-tolerant; BlastEm/Nomad/HW-fatal).
>
> **Proven instance (Build 0105):** runtime 0x3B152 A0=0xC04000, 0x3B158 D1=0x2000, 0x3B15C D0=0, 0x3B15E `bsr 0x3AF3C` (raw `move.w d0,(a0)+ ; subq #1,d1 ; bne`); walks 0xC04000..0xC08000; BlastEm fatals "Illegal write to HV Counter port 8" at the first HV alias 0xC04008 (`address & 0x1F == 0x08`). Arcade meaning: legal PC080SN BG per-line scroll-RAM clear (`m_bgscroll_ram[0]`); 0xC0C000 is the FG equivalent (`m_bgscroll_ram[1]`).
>
> **General rule:** arcade PC080SN/PC090OJ tilemap/scroll/sprite fills/clears to 0xC00000-class or 0xD00000-class addresses must never execute as raw Genesis 68000 writes; route through the dispatch/staging path (`0x3AF44 → genesistan_hook_3ad44_dispatch`) or the sprite hook. Sibling routed paths prove it (C00000/C08000 name clears via 0x3AF44; C04000/C0C000 scroll clears were left raw on 0x3AF3C and must be repointed). Do NOT fix by VDP-port sanitizer, suppressing 0xC00008, hardware mirroring, MAME-tolerance mimicry, globally hooking the shared primitive 0x3AF3C (it has a valid WRAM caller at 0x3AB9E), or dropping the operation.
>
> **Scroll-RAM intent is NOT a no-op.** PC080SN per-line scroll-RAM clears (0xC04000/0xC0C000) must route to **named, input-preserving** handlers (`genesistan_hook_pc080sn_bg_scroll_fill` / `_fg_scroll_fill`) that receive A0/D0/D1 + BG/FG identity. They may be documented **stubs** while the full-plane scroll model (KF-015) renders no per-line scroll, but they are the **named semantic home** for the future intent-based implementation (translate per-line scroll into the Genesis HSCROLL table, or reduce uniform per-line scroll to the full-plane `staged_scroll_*`). Routing arcade hardware intent into a silent range-gate absorb is rejected — visually inert today must not mean architecturally invisible.
>
> **Detection signature:** symptom = BlastEm "Illegal write to HV Counter port 8" / Nomad / strict-HW black screen while MAME appears tolerant. First check = a raw arcade fill/clear loop (`move.w`/`move.l` via `(aN)+`) or inline producer store with Ax in 0xC00000..0xC10000 or 0xD00000..0xD00800 whose call path did not route through the dispatch/staging hook. Scan for ALL such sites — fixing one exposes the next. Known same-class latent sites in Build 0105: 0x3B16E (C0C000 FG scroll-RAM clear, same mechanism) and the inline title-text producer 0x3B392 (raw 0xC093xx FG tilemap writes, different mechanism).

## STOP triggered

NO.
