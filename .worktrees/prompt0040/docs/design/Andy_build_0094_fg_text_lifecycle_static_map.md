# Andy — Build 0094 FG/Plane-A Text Lifecycle Static Map

**Author:** Andy
**Date:** 2026-06-23
**Build:** 0094 (`dist/rastan-direct/rastan_direct_video_test_build_0094.bin`)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No build. No runtime probing. Hypothesis set + watch list for the parallel Cody runtime task; runtime reachability/contradiction resolution is Cody's.

Labels (Rule 3): `runtime_genesis_pc` = patched-ROM offset / runtime PC (= `arcade_pc + 0x200`, KF-006); `WRAM` = Genesis work RAM; `HW` = hardware. **Each finding is tagged [STATIC] (proven from disasm/source) or [INFERENCE] (deferred to Cody).**

---

## Phase 0 — Baseline statement

**Relevant priors:** KF-028 (title-text producer→staging arc — STRONG), KF-013 (text dispatch inside VBlank — STRONG), KF-011 (arcade VBlank owns the lifecycle — STRONG), KF-010 (FG→Plane A `0xE000` — STRONG), KF-003/KF-001 (`%a5@(44)` dual-use frame-delay/watchdog counter — STRONG/CONFIRMED), KF-004/006 (PC↔offset — CONFIRMED).
**Rediscovery-Hazard HIGH touched:** KF-028, KF-013, KF-011, KF-010, KF-003, KF-001 — respected; none contradicted.
**Task classification:** EXTENDING (OPEN-001).
**Open/Closed issues touched:** OPEN-001 (active — additive FG text), OPEN-016 (context — producer/staging chain), OPEN-015 (do-not-touch).
**Contradiction of CONFIRMED/STRONG KF:** NONE.
**Architecture compliance:** CONFIRMED. Any recommended clear is an arcade-semantic page-replacement translated into the staging layer; no Genesis-owned control flow.

---

## 1. Producer map (PCs + caller relationships) — [STATIC]

The attract/title text lifecycle is **three** master-state machines selected by the master dispatch at `0x3A256` reading `%a5@(0)`; each is counter-gated on `%a5@(44)` then dispatches on `%a5@(2)` via a PC-relative jump table:

- **Master `%a5@(0)=0` → `0x3ABFE`** (title sub-state; table `0x3AC20` on `%a5@(2)`):
  - `%a5@(2)=0` → inner dispatch `0x3AC26` (table `0x3AC3C` on `%a5@(4)`):
    - `=0` → **`0x3AC40`** producer (`bsrw 0x3afd8/0x3af4c/0x3b05a`; `%a5@(4)←1`).
    - `=1` → **`0x3AC54`** producer (`jsr 0x5a556`; glyph IDs `30/12/32/18/19` via `bsrw 0x3BD48`; **conditional `cmpiw #1,0x5fffe`** at `0x3AC5C` — a coin/credit-style flag; `clrw %a5@(4)`; `movew #1,%a5@(2)`; **kick `movew #208,%a5@(44)`** at `0x3AC88`).
  - `%a5@(2)=1` → **`0x3AC90`** (dispatch on `%a5@(4)`):
    - `=0` → `0x3AC9E` setup (`bsrw 0x3af4c/0x3b05a`; `%a5@(4)←1`).
    - `=1` → **`0x3ACAE`** glyph producer (`jsr 0x5a5de`; glyph IDs `17/63/64/65/66/67/68/69/70` via `bsrw 0x3BD48`; the lone direct writer `0x3ACEA movew #0x2749,0xC09172` [out of scope]; kick `#160`; `%a5@(4)←2`).
    - `=2` → `0x3AD00` steady (`jsr 0x712B4` = `genesistan_palette_hook_03ab00`; palette only).
  - Further sub-states reach **`0x3AD08`** producer (glyph IDs `60/61/62`; clears the `%a5@(256)` WRAM buffer; **`movew #2,%a5@(0)`** master→2; `clrw %a5@(2)/%a5@(4)`), **`0x3AD12`**, and **`0x3AD5E`** (`movew #512,%a5@(44)`; `clrw %a5@(2)/%a5@(4)`).
- **Master `%a5@(0)=1` → `0x3AAAC`** (counter-gated; table `0x3AACE` on `%a5@(2)`) — a further attract page set (producers via the same `bsrw 0x3BD48` glyph path).
- **Master `%a5@(0)=2` → `0x3A35A`** (counter-gated; table `0x3A37C` on `%a5@(2)`) — a further attract page set.
- **Master `%a5@(0)=3` → `0x3AD6E` → `braw 0x3A180`** (watchdog; KF-001 — not a text page).

**Every text producer draws via `bsrw 0x3BD48`** (the glyph/string renderer, opcode-replaced to the FG staging hook `genesistan_hook_glyph_renderer_3bd48`). The producers write FG cells **additively, per glyph** (descriptor glyph-byte loop), not full-page.

---

## 2. Page/state mapping — [STATIC structure / page-identity INFERENCE → Cody]

Statically, distinct producers exist for distinct sub-states across master 0/1/2, each rendering a fixed glyph-ID set (`0x3AC54`: 30/12/32/18/19; `0x3ACAE`: 17/63–70; `0x3AD08`: 60/61/62; etc.). **Which producer renders which named page** (TAITO/copyright, story/insert-coin, ranking/high-score, coin prompt, game-start) requires decoding the descriptor strings for those IDs and runtime reachability — **deferred to Cody**. The reference lifecycle's ranking/high-score page is a pre-coin attract page (master 0/1/2 text), not the game-start path. Observable static anchor: `0x3AC54`'s `0x5fffe` conditional is consistent with a coin/credit-gated page (coin-prompt or credit display) — [INFERENCE], Cody to confirm.

---

## 3. State variables / gates — [STATIC]

- `%a5@(0)` (`WRAM 0xFF0000`) — **master page selector**; writers: `0x3A45A` (#1), `0x3A9DE`/`0x3AB48` (#2), `0x3AD48` (#2), plus `clrw` resets.
- `%a5@(2)` (`WRAM 0xFF0002`) — **sub-page selector**; writers incl. `0x3AB8E`/`0x3AC88`-region, `0x3AD4E`/`0x3AD64`, plus `clrw` resets.
- `%a5@(4)` (`WRAM 0xFF0004`) — **producer-phase selector** within a sub-page; writers `0x3AC4C`(#1)/`0x3AC76`/`0x3ACF8`(#2)/`0x3AD52`/`0x3AD68`.
- `%a5@(44)` (`WRAM 0xFF002C`) — **frame-delay + watchdog counter** (KF-001/KF-003 dual-use); each master dispatcher decrements it and only advances the page when it reaches 0; producers reload it (kicks `#160/#208/#512`).

A "page transition" is a write to `%a5@(0)` and/or `%a5@(2)` (and the dependent `%a5@(4)` reset) — these are **state resets, not FG-tilemap clears**.

---

## 4. Clear / fill / replacement routines — found vs absent — [STATIC]

**The only translated FG clear is `genesistan_hook_cwindow_clear`** (`runtime_genesis_pc 0x710D8`). Per `specs/rastan_direct_remap.json` it replaces **arcade_pc `0x0561B6`** — an inline PC080SN C-window fill loop (`original_bytes` blank-fill `0x00000020` to **both** `0xC08000` FG and `0xC00000` BG, `0x1000` iterations). The hook "fills `staged_bg_buffer` and `staged_fg_buffer` with LUT-translated blank tile and marks all rows dirty." **STATIC.**

**That clear is reached only from the game-scene path:** the routine `0x563A0` (`clrw` scroll regs `%a5@(4270/4272/4332/4334)` → `jsr 0x55cb4` → `jsr 0x710D8` cwindow_clear) is called from `0x56022`, `0x56164`, `0x561CA` — all in the `0x560xx` game-scene setup region. **STATIC.**

**No FG C-window clear exists anywhere in the attract text state machine (master 0/1/2, `0x3A35A`/`0x3AAAC`/`0x3ABFE`–`0x3AD60`).** A full scan of that region finds no write loop to `0xC08000–0xC0BFFF`, no `staged_fg_buffer` fill, and no call to `cwindow_clear`/`0x561B6` — only `%a5@(…)` state-variable resets and the single out-of-scope direct write `0x3ACEA`. (`0x3b13c lea 0xc08000` is the one-time boot VRAM clear, not per-page.) **STATIC.**

**Conclusion [STATIC fact + INFERENCE]:** the translated attract text path renders additively (per-glyph staging) and contains **no FG page-replacement clear**; the only such clear is wired to the game-scene lifecycle phase. This is consistent with the suspected additive-FG symptom (earlier pages persist in `staged_fg_buffer`, which the commit does not clear — Classification C — so new pages overlay old). **Whether the arcade originally cleared the FG between consecutive attract text pages (a boundary the translation dropped) or relied on full-page overwrite (and the per-glyph hook under-writes blanks) is [INFERENCE] for Cody to resolve at runtime.**

---

## 5. Is `0x3ACAE` a complete page boundary? — NO [STATIC]

`0x3ACAE` is **one producer** for one sub-state (`%a5@(2)=1, %a5@(4)=1`) inside master 0. It is not a page boundary. A clear attached to `0x3ACAE` alone would address only that sub-state, not the master-0/1/2 page set. The page-replacement boundary is the **dispatcher/state-transition that begins a new attract page** (the `%a5@(0)`/`%a5@(2)` transition points), not any single producer.

---

## 6. Ranking-page producer — exists; route via dispatch; reachability = Cody [STATIC + deferred]

A ranking/high-score producer **exists statically** as one of the master-0/1/2 text producers (the renderer + descriptor machinery is present and reachable through the master/sub-state dispatch). Identifying the exact producer (and confirming its runtime reach) requires decoding the descriptor strings and a runtime trace — **deferred to Cody per the task contract**. Do not infer its reachability from visual presence/absence.

---

## 7. Is `0x710D8`/`0x563A0` relevant to title-attract replacement? — Only as the correct MECHANISM, wrong phase [STATIC]

`cwindow_clear` (`0x710D8`) is the **correct clear mechanism** (blanks `staged_fg_buffer` + marks rows dirty), but it is bound to the **game-scene** lifecycle (caller `0x563A0`, reached from `0x560xx`), **not** attract page replacement. For attract page replacement, the same mechanism (or an FG-only variant) must be invoked at the attract page boundary; it currently is not.

---

## 8. PRIORITY — Cody runtime watch list

To confirm/refute the additive-no-clear hypothesis and pin the boundary, watch (during the no-input attract loop):

1. **Page-transition timeline (decisive):** write-watchpoint on `WRAM 0xFF0000..0xFF0005` (`%a5@(0)/(2)/(4)`); log `(frame, writing PC, value)`. Maps when each attract page begins and from which PC.
2. **FG staging accumulation (decisive):** write-watchpoint on `staged_fg_buffer` `WRAM 0xFF501A..0xFF601A`; log `(frame, writing PC, offset, value)`. At each page transition, confirm whether prior-page cells **persist** (additive) vs are overwritten/blanked. Also dump the full FG buffer immediately before and after each page transition.
3. **Clear absence:** breakpoint `runtime_genesis_pc 0x710D8` (cwindow_clear). Confirm it does **not** fire during attract text pages (expected: fires only in game-scene). If it never fires in attract, the no-FG-clear hypothesis holds.
4. **Producer execution per page:** breakpoints `0x3AC40`, `0x3AC54`, `0x3ACAE`, `0x3AD08`, `0x3AD12`, and the master-1 (`0x3AAAC→…`) / master-2 (`0x3A35A→…`) producers — count + frame, with `%a5@(0)/(2)/(4)` at hit.
5. **Glyph content:** breakpoint `0x3BD48`; log `%d0` (glyph ID) per call per page → maps page text.
6. **Dirty-row marking + commit:** watch `fg_row_dirty` `WRAM 0xFF4006`; breakpoint the FG commit `0x70182` — confirm staged FG is committed each frame (so persistence is staging-level, not commit-level).

Decision the watch list yields: if (2) shows prior-page cells surviving across a (1) transition with (3) never firing → confirms additive-FG with a missing attract page-replacement clear; the (1) transition PC marks the boundary where the clear belongs.

---

## 9. Recommended boundary (statically justified) — with Cody dependency

**[STATIC-justified]** The FG page-replacement clear belongs at the **attract page-start** — the master/sub-state transition that begins a new attract text page (the `%a5@(0)`/`%a5@(2)` transition dispatchers in master 0/1/2), invoked **before** the new page's producers draw. The clear should reuse the `cwindow_clear` mechanism (blank `staged_fg_buffer` + mark all FG rows dirty), as an FG-scoped invocation at the attract boundary.

**[Cody dependency]** The exact boundary instruction(s) and granularity (per-major-page master transition vs per-sub-page) must be pinned by watch-list items (1)+(2): the specific `%a5@(0)/(2)` transition PC that precedes each *visible* page change, where FG staging is confirmed to still hold the prior page. If Cody's trace instead shows the producers *do* attempt full-page blanks that are lost (a descriptor/hook under-write), the boundary recommendation is superseded by that finding (runtime wins).

Not a STOP: static evidence is sufficient to recommend the boundary *region* and the mechanism; only the exact transition PC and granularity await Cody.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 (active — additive FG text localized to a missing attract-path FG clear; boundary region named; not closed), OPEN-016 (context — same producer/staging chain), OPEN-015 (not touched).
- New issues opened: NONE. Issues closed: NONE.
- Intentionally deferred: the post-Start exception (OPEN-015), OPEN-017, sprites/palette/scroll/BG logo/sword/TAITO-logo completeness, per-frame/per-glyph clearing, page-identity decoding, ranking-producer runtime reachability (all → Cody / out of scope).

## KNOWN_FINDINGS impact

**Option C — proposed refinement to KF-028** (assess only; do not edit `KNOWN_FINDINGS.md`; Tighe/Chad Sr. approve). Proposed addition:

> The Genesis translation's only FG C-window clear is `genesistan_hook_cwindow_clear` (`0x710D8`), replacing arcade `0x0561B6`'s BG+FG blank-fill loop; it is reached only from the game-scene setup routine `0x563A0` (callers `0x560xx`). The attract/title text state machine (master `%a5@(0)`=0/1/2: `0x3ABFE`/`0x3AAAC`/`0x3A35A` and producers `0x3AC40/0x3AC54/0x3ACAE/0x3AD08/0x3AD12`) renders FG text additively via the glyph renderer `0x3BD48` and contains **no FG clear**, so attract pages overlay in `staged_fg_buffer` (which the commit does not clear). The page-replacement boundary belongs at the attract page-start `%a5@(0)`/`%a5@(2)` transition.

Confidence: STRONG for the static structure (proven); the additive-FG *causation* is WORKING_HYPOTHESIS pending Cody's runtime confirmation. Cross-ref OPEN-001, KF-010/013.

## STOP triggered

NO.
