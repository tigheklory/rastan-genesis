# Andy — R1 Subround-1 0442→0446 Root Cause

**Date:** 2026-10-19 · **Type:** READ-ONLY root-cause investigation. No production source/ROM/MAME/
trace/counter change; Phase D/E not started; Cody's in-flight work and the working tree untouched.
**Evidence authority:** Tighe's real Sega Genesis hardware results are input facts; this document
explains them and never attempts to prove them wrong. Static evidence that conflicts with hardware is
treated as an incomplete static model. Deliverable + AGENTS_LOG + OPEN-037 update (not closed, not
duplicated). Supersedes prior R1-Subround-1 regression assumptions where they conflict with the
hardware timeline below.

---

## 0. Corrected build↔artifact mapping (the error that invalidated prior static work)

Only **0442 (`c7ca1439`)** and **0446 (`f9686893`)** have source commits. **0443/0444/0445 were
produced but never committed** — their only authoritative evidence is the preserved `dist/` ROM
artifacts. The earlier regression audit diffed *commits* and mislabelled an intermediate commit state
as "0445"; that comparison was not 0445 at all. This investigation uses the **ROM artifacts** in
`dist/rastan-direct/rastan_direct_video_test_build_04NN.bin` (and `_invincible`) as the authority.

Artifact facts (base ROMs):

| Build | size (bytes) | sha1[:12] | vs 0442 | gate ledger |
|---|---|---|---|---|
| 0442 | 2,698,936 | 5f4f6a2f078c | baseline (no native-title pkg) | entry=PASS |
| 0443 | 2,711,224 | 647762981f6d | +0x3000 (native-title pkg) | canonical=FAIL entry=FAIL |
| 0444 | 2,711,224 | 2a54735eb0d9 | +0x3000 | entry=FAIL |
| 0445 | 2,711,224 | b23e2a1e0be2 | +0x3000 | entry=FAIL |
| 0446 | 2,711,224 | 685c64248c79 | +0x3000 | entry=PASS |

The +0x3000 is **appended native-title data at the ROM tail** (≈0x72000, 0x84a88, 0x2958bc), not growth
of the copied arcade region. The copied arcade region after the title cut is **shifted −30 bytes** in
0446 vs 0442 (verified: 446[X−30] = 442[X] across 0x3C000–0x5A000).

---

## HARDWARE FACTS

- **Build 0442:** GOOD — full R1 Subround 1 → true end extent → Subround 2. Behavioral control.
- **Build 0443:** REAL-HARDWARE CRASH. Crash GEN PC **0x000721AA**, FAULT **0xBEA80003**.
- **Build 0444:** REAL-HARDWARE CRASH.
- **Build 0445:** PLAYABLE — reaches R1 Subround-1; map stops early ≈ **Segment 11**; scripted
  auto-walk-right begins as if the subround ended; true end door/extent not reached.
- **Build 0446:** PLAYABLE — same premature-end class, false endpoint ≈ **Segment 13**; true end
  ≈ Segment 15 before legitimate end + Subround-2 transition.
- Normal ROM affected: **YES.** `_invincible` ROM affected: **YES** (both base and `_invincible`
  artifacts carry the identical native-title package; `_invincible` is not the root class).
- Tighe hardware observations challenged: **NO.** (The gate ledger independently corroborates: 0442
  entry=PASS; 0443 canonical+entry FAIL; 0446 entry=PASS. 0445 entry-gate=FAIL yet plays on hardware —
  a static-gate/hardware gap, resolved in hardware's favor.)

---

## 0443 CRASH

- **Exact owner:** the new native glyph worker `genesistan_hook_glyph_renderer_3bd48` worker body at
  Genesis **0x72196** (the crash PC 0x721AA is inside it). Call site = native stub at arcade/Genesis
  **0x3BD48** (`jsr 0x072196` at 0x3BD56).
- **Known glyph/title crash family:** **YES** — this is the native-title glyph address-error family.
- **Root fault:** in 0443 the glyph worker obtained its descriptor-table base from an **absolute**
  `movea.l #0x0003BD7C, a0` (bytes `207c 0003bd7c` present at the crash region in 0443). The native-
  title reflow invalidated that fixed address; `adda.w d0,a0; movea.l (a0),a0` then dereferenced a
  garbage/misaligned pointer → 68000 address error on an odd address (0xBEA80003 is odd), matching the
  0x0003BExx pointer table read out of alignment. Proven from 0443 bytes
  (`…4e75 3200 0240007f e548 207c 0003bd7c d0c0 2050 2258…`).
- **Repair build/state:** repaired in **0445** — the absolute load was removed and the base is now set
  by a **PC-relative** `lea (d16,pc), a0` in the caller stub at 0x3BD52. 0445 no longer crashes but
  the displacement is `+8` → base 0x3BD5C (the `rts` opcode + table, **off by 2 bytes**). **0446** sets
  the displacement to `+10` → base 0x3BD5E = correct table start (`0003be7a …`).
- **Relationship to later progression defect:** **RELATED to the 0445→0446 endpoint movement**
  (see below), **but not the whole early-end** (0446 has the correct glyph base and still early-ends).
  So: same subsystem (native-title glyph system), same regression vector (native-title package), but
  the crash and the *persistent* early-end are distinct effects of that one package.
- **Proof:** byte-level disassembly of 0443/0445/0446 at 0x3BD48 and 0x72196; the glyph stub signature
  `2402 3200 0240007f e548 41fa` is **absent in 0442** and present in 0446 at 0x3BD48 — i.e. the native
  glyph/title/HUD renderer is **new at the 0443 native-title package**.

---

## END-OF-SUBROUND CONDITION

The retained arcade progression owner (proven previously in
`Andy_scene_phase_state_machine.md`, re-confirmed here):

- **Master section index:** `A5+0x1242` → start of `A5+0x13E` via ROM table **0x5073A[A5+0x1242]`**.
- **Map-stream pointer:** `A5+0x10C6`, advanced by **FUN_000558E0** (0x558E0), selected byte →
  `0x10D0A8`. This is the "map extent / where the subround ends" producer.
- **Scroll column:** `A5+0x10F6`. **Round boundaries:** ROM **0x502AC** = {0x16,0x2D,0x44,0x5B,0x72,
  0x89}. **Phase-transition-active flag:** `A5+0x1394` (0xFF idle/gameplay, 1 transition running); the
  transition sequencer at 0x55DFE drives the screen-wipe + auto-walk + next-scene load and ends by
  writing `A5+0x13E = A5+0x13B8 − 1`, `A5+0x1394 = 0xFF`.
- **Arcade PC of the owner:** section-start/extent at 0x3A614/0x3A63A region + map-stream FUN_000558E0;
  transition sequencer 0x55DFE+. (These are arcade PCs; Genesis runtime PCs are these −30 in 0446.)
- **Camera-stop / auto-walk / Subround-2 connection:** when the map-stream reaches its subround
  end-marker, the world stops advancing and the transition sequencer runs the scripted auto-walk and
  the Subround-2 handoff. The visible symptom (stop + auto-walk + missing end door) is exactly "the
  map-stream reached end early."

**Critical finding — these inputs are NOT broken by the reflow statically:**
- `0x5073A`, `0x502AC`, `0x558E0` have **no absolute-long references anywhere** in either ROM — they
  are reached base-register-relative (A5 / An), so the reflow cannot misrelocate them.
- The scene-descriptor table `0x3951C` (below the title cut, **unshifted**) is referenced absolutely at
  0x505AE (gameplay) and in native tail code; all those references correctly keep value 0x3951C in
  0446 (the target didn't move). ✓

| build | end-condition input references | verdict |
|---|---|---|
| 0442 | base-register / correct absolute | correct |
| 0445 | identical to 0446 except the glyph LEA byte | correct (references) |
| 0446 | base-register / correct absolute | correct |

---

## BACKWARD SLICE (static)

Exhaustive checks of the end-condition input chain between 0442 and 0446 (0446 aligned −30):

- **Input: gameplay absolute-long pointers (code 0x44000–0x5A000).** 546 in-range pointers relocated
  correctly (−0x1E / −30 low-byte signature); the remaining "unchanged" longs are A5-relative EA
  displacements (prevword `0c6d`/`0c40`/`0c2d` = `cmpi.w`/`move` to d16(a5)) and code misread as longs
  (e.g. `6100 0044 4e75` → false "0x00044E75"), not pointers. **Verdict: SAME** (relocation complete).
- **Input: cross-boundary PC-relative address loads (gameplay → pre-cut region).** `lea/pea/movea
  (d16,pc)` from the −30 gameplay region into the unshifted pre-cut region: **zero found.**
  **Verdict: SAME.**
- **Input: section table 0x5073A / boundaries 0x502AC / map-stream FUN_000558E0.** No absolute refs;
  base-register addressed. **Verdict: SAME.**
- **Input: scene descriptor 0x3951C references.** Correctly unchanged (unshifted target).
  **Verdict: SAME.**
- **Input: native title/glyph BSS vs arcade progression WRAM.** native-title BSS = 0xFFB2C4 /
  0xFFB884 / 0xFFB890 (sat cache, hud count/queue); arcade A5 progression fields ≈ 0xFF32xx.
  **No overlap. Verdict: SAME** (no BSS collision).
- **Input: native glyph worker (0x72196) / `native_frontend_hud_emit` (0x74B1A) memory writes.** They
  write only 0xFF011E / 0xFF0142 / read 0xFF0117 (score/HUD fields) and glyph pixels; **no write into
  the map-stream / progression WRAM.** **Verdict: SAME** (no direct progression corruption in 0446).

---

## FIRST WRONG SEMANTIC VALUE

- **Pinned (as a unique static site):** **NO.** All static end-condition code/data inputs above are
  semantically equivalent between 0442, 0445 and 0446. There is **no stale gameplay pointer, no cross-
  boundary PC-rel address load, no BSS/WRAM collision, and no progression-WRAM write** from the native
  title/HUD path. The static gameplay progression is equivalent.
- **The one proven functional divergence 0445↔0446:** exactly **3 bytes** (confirmed by full byte diff
  of the real artifacts): `0x00018F` 0x40→0x43 (label char), `0x2958DB` 0x35→0x36 (build-number digit
  in `crash_title` string), and **`0x03BD55` 0x08→0x0A — the glyph stub's `lea (d16,pc)` displacement**.
  Only the last is functional. **This single instruction byte is the sole static cause of the endpoint
  moving ≈Segment 11 → ≈Segment 13.** Because it is the *only* functional difference, the Seg11↔Seg13
  movement must be mediated by this glyph reference.
- **Why 0445 endpoint ≈11:** glyph stub base off by 2 (0x3BD5C) → the worker walks **wrong descriptor
  records** (`movea.l (a0)+,a1; move.w (a0)+,d2; … move.b (a0)+,d0; beq`) with wrong destination
  pointers and a **wrong byte-count before the zero terminator** → different per-call work and a wrong
  write destination `a1`.
- **Why 0446 endpoint ≈13:** glyph base correct (0x3BD5E) → correct descriptors/destinations/loop
  length → different (correct) per-call behavior than 0445, hence a different endpoint, **but the
  underlying early-end still present.**
- **First build/state introducing the early-end:** the **native-title package at 0443** (the glyph
  stub signature is absent in 0442, present from 0443). The early end is masked by the crash in
  0443/0444 and first observable in 0445.

---

## CAUSAL CHAIN

- **First wrong input:** not a static data value — the **native-title package's runtime behavior**
  introduced at 0443 (new native glyph/title/HUD subsystem + ROM reflow). It is present and effectively
  identical in 0445 and 0446 (they differ by one glyph byte only).
- **Map/stream consequence:** the map-stream reaches its Subround-1 end-marker at a smaller world
  extent than in 0442 (observed: stop at ≈Seg 11/13 instead of ≈15).
- **End-condition consequence:** the retained progression logic correctly reacts to the (early) map-
  stream end — it is faithful; its runtime *input timing/state* is what differs.
- **Camera-stop / auto-walk / missing-end-door consequences:** follow directly from the early map-
  stream end (the true final records are never streamed in).
- **Causality proven:** **PARTIAL.** Vector (native-title package at 0443) and the glyph-byte coupling
  to the endpoint are proven; the exact runtime field that makes the map-stream end early is **not**
  statically pinned (all static inputs are equivalent), so the final link is a runtime-state link,
  specified below.

---

## MAP VS PROGRESSION

- **First subsystem wrong:** **MAP/STREAM** (the subround believes it ended because the map-stream
  reached its end-marker early; the progression/end logic is faithful and merely reacts). Classified as
  order **A** (map/streaming extent becomes wrong first → progression reacts to a truncated extent).
- **Proof:** the progression end/round tables and the map-stream producer are statically correct and
  base-register addressed; the symptom is "map stops + no end door," i.e. the extent producer, not the
  end comparator, is the first-wrong subsystem. (Ownership proven; the exact runtime perturbation of
  the stream is the open item.)

---

## 0442 → 0443 → 0444 → 0445 → 0446

- **0442→0443:** native-title package added (+0x3000 tail data; −30 reflow of the copied region; new
  native glyph/title/HUD subsystem: stub 0x3BD48 + worker 0x72196 + PC-relative descriptor table).
  Introduces BOTH the glyph crash and the early-end vector.
- **0443→0444:** glyph crash still present (entry gate still FAIL; hardware still crashes).
- **0444→0445:** glyph worker converted from absolute `movea.l #0x3BD7C` to PC-relative
  `lea (d16,pc),a0` → **crash removed, gameplay resumes**; displacement left at +8 (base off by 2).
- **0445→0446:** glyph displacement +8→+10 (base corrected) + 2 cosmetic bytes — the only functional
  change; endpoint moves ≈11→≈13.
- **Why playable at 0445:** the absolute→PC-relative conversion stopped the address-error crash.
- **Why progression still wrong:** the early-end vector (native-title package) is independent of that
  crash repair and remains in 0445 and 0446.
- **Why endpoint changes again at 0446:** the glyph base correction changes the worker's descriptor
  walk (destinations + loop length), which is the only functional delta and therefore the mediator of
  the endpoint shift.

---

## CURRENT BUILD 0455

- **Historical bad owner still present:** **YES / CHANGED FORM.** The native glyph stub + worker are
  still present (current `genesistan_hook_glyph_renderer_3bd48` worker at 0x72188; the subsystem and
  ROM reflow persist). The early-end class persists (Tighe reports later builds keep the premature end
  near the later endpoint).
- **Current source owner:** `apps/rastan-direct/src/tilemap_hooks.s` `genesistan_hook_glyph_renderer_3bd48`
  (stub + worker); `pc090oj_hooks.s` / `native_frontend_hud_emit` HUD path; the native-title package
  generator and `specs/rastan_direct_remap.json` `shift_replacements` (0x03AA54/0x03BB48) that drive
  the reflow.
- **Current bad state/source:** the runtime interaction between the native-title/glyph/HUD subsystem
  and the arcade Subround-1 map-stream — not a single static byte.

---

## FUTURE CODY FIX

- **Exact file/function/table:** cannot be reduced to one line yet because the exact runtime link is
  not pinned (see evidence request). The durable-repair *locus* is the native-title/glyph/HUD subsystem
  and the reflow that introduced it, not the arcade progression code (which is faithful).
- **Exact correction (once the runtime field is captured):** restore the original arcade runtime
  conditions for the map-stream across the native-title package — e.g. ensure the native glyph/HUD
  subsystem does not alter the per-frame/ setup conditions the map-stream advance depends on, and that
  every `(d16,pc)` data reference the native-title package introduced is relocation-durable (the shift
  patcher repairs branches and absolute-long operands but **not** `(d16,pc)` data references — that
  gap is exactly why the glyph LEA needed a hand fix). The fix restores arcade semantics; it does not
  touch the progression/extent logic.
- Hard-coded segment count: **NO.** Forced camera max: **NO.** Auto-walk workaround: **NO.**
  Per-build numeric delta: **NO.** Arcade gameplay semantics changed: **NO.**

---

## IF ROOT CAUSE NOT PINNED

- **All static semantic end-condition inputs equivalent (0442/0445/0446):** **YES** (within the
  exhaustive checks above: relocation, cross-boundary PC-rel, section/boundary/map-stream tables,
  scene descriptor, BSS overlap, glyph/HUD WRAM writes).
- **Earliest runtime field requiring comparison:** the **map-stream state at the Subround-1 end
  trigger** — `A5+0x10C6` (map-stream pointer) together with `A5+0x10F6` (scroll column), captured at
  the single frame `A5+0x1394` leaves 0xFF (gameplay) to begin the Subround-1 end/auto-walk transition.
- **Owner/writer:** `A5+0x10C6` written by FUN_000558E0 (map-stream advance); `A5+0x1394` written by
  the transition sequencer (0x55DFE / 0x3A614 region).
- **Exact semantic event:** the first frame the Subround-1 end transition arms (A5+0x1394: 0xFF→1 /
  auto-walk start).
- **Single bounded evidence request:** On a GENESIS NTSC run of **0446** and a GENESIS NTSC run of
  **0442**, capture `A5+0x10C6`, `A5+0x10F6`, and `A5+0x1394` **at that one event**. If 0446 reaches
  the map-stream end-marker (`A5+0x10C6`) at a **smaller `A5+0x10F6`** than 0442, the map-stream is
  advancing/terminating early (extent/stream desync — order A confirmed, and the comparison localizes
  whether the stream pointer over-advances or the end-marker is read early). This is one bounded capture
  of three related fields at one event.
- **Broad trace required:** **NO.**

---

## OPEN/CLOSED ISSUES

- **Issue updated:** OPEN-037 — corrected hardware timeline (0442 GOOD; 0443 crash GEN PC 0x721AA /
  FAULT 0xBEA80003; 0444 crash; 0445 ≈Seg11; 0446 ≈Seg13); corrected build↔artifact mapping (443/444/
  445 uncommitted); 0443 crash pinned (glyph absolute-pointer); 0445→0446 endpoint-move pinned (glyph
  `(d16,pc)` displacement); static gameplay inputs proven equivalent; root = native-title-package
  runtime vector at 0443; earliest runtime field + single bounded evidence request recorded. Prior
  "frontend-only, unrelated glyph" framing corrected: the glyph system **does** reach gameplay
  progression (proven by the 0445→0446 single-byte endpoint move).
- **New issue:** NONE. **Closed issue:** NONE.

---

PRODUCTION MODIFIED: NO · ROM BUILT: NO · MAME RUN: NO · TRACE CREATED: NO · BUILD NUMBER CONSUMED: NO ·
PHASE D: NO · PHASE E: NO.

STOP.
