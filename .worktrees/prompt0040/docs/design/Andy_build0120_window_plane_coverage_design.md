# Andy — Build 0120 Window Plane Coverage (Analysis / Design Only)

**Author:** Andy
**Date:** 2026-07-01
**Baseline:** Build 0120 (`dist/rastan-direct/rastan_direct_video_test_build_0120.bin`, SHA256 `80404f3a5b158f003692a20e84fe23ab05351f0639ac6bcd7d7594b93a0146ad`). rastan-direct.
**Scope:** ANALYSIS / DESIGN only. No source/spec/tool/Makefile/ROM/build/bookmark/diagnostic/implementation. Code correlation via `address_map.json`. Labels: **[OBS]** verified this task; **[CODY]** Cody evidence; **[INT]** interpretation.

> **HEADLINE:** The leading Window-coverage hypothesis is **REFUTED**. `reg17=0x00 / reg18=0x00` is the **Window-OFF** state (SGDK's own `VDP_setWindowOff()` writes exactly these values). The Window is **not composited** in Build 0120, so its garbage `0xF000` VRAM is **inert** and **cannot** produce the pommel artifact. The old "Window Plane Disable Fix" prior had the semantics **inverted** and was **never validated**. **Do NOT apply the `0x00→0x80` patch** — it is based on inverted semantics, is effectively a no-op (0x80 is also pos=0 = zero-size), and would not fix the artifact. Re-attribute the pommel artifact to sprite/SAT (OPEN-024).

---

## PHASE 0

**Relevant priors:** KF-032 (raw PC080SN writes — context, not this artifact); the Build-327-era "Window Plane Disable Fix" / "Attract Mode vs Visible Plane A Audit" (AGENTS_LOG; `docs/design/build327_attract_mode_vs_visible_plane_a_audit.md`); Cody Build 0120 attribution docs. SGDK VDP source `tools/sgdk/src/vdp.c`. **High-rediscovery hazards:** the **inverted Window register semantics** in the old prior (claims `0x00=full-screen`, `0x80=off`) — HIGH hazard; it has already misled Cody's Build 0120 attribution. **Task classification:** EXTENDING (OPEN-001 title/attract; OPEN-023 Window path) / CONTRADICTING the old Window prior. **Contradiction detected:** YES — the old prior's Window-register semantics contradict SGDK's own `VDP_setWindowOff()` source (§Prior Reconciliation). **Architecture compliance:** analysis-only; no changes.

---

## PRIOR RECONCILIATION

**Old Window-off finding (Build 326/327, SGDK `apps/rastan/src/main.c`, Window base VRAM 0xD000):** [OBS]
- Claimed root cause `WINDOW_PLANE_FULL_SCREEN_COVERAGE`: `reg17=0x00` = "right-of-col-0 = full width", `reg18=0x00` = "down-from-row-0 = full height" → Window covers entire screen, hiding Plane A.
- Claimed fix: `reg17 0x00→0x80`, `reg18 0x00→0x80` = "Window OFF".
- Claimed `VDP_setWindowOff()` writes `reg17=0x80, reg18=0x80`.
- **Validation status: NEVER CONFIRMED** — the log entry marks "Plane A visible on actual display: **USER MUST VERIFY**", "No regressions observed: **USER MUST VERIFY**".

**SGDK ground truth (`tools/sgdk/src/vdp.c:783-814`) — the semantics are INVERTED in the old prior:** [OBS]
```c
void VDP_setWindowHPos(u16 right,u16 pos){ ... *pw = 0x9100 | v; }   // v = (right<<7)|(pos&0x1F)
void VDP_setWindowVPos(u16 down, u16 pos){ ... *pw = 0x9200 | v; }
void VDP_setWindowOff(){ VDP_setWindowVPos(false,0); VDP_setWindowHPos(false,0); }
```
`VDP_setWindowOff()` → `setWindowHPos(false,0)` → `reg17 = 0x9100 | 0` → **reg17 value = 0x00**; `setWindowVPos(false,0)` → **reg18 value = 0x00**. **SGDK's canonical Window-OFF is `reg17=0x00, reg18=0x00`.** The window's horizontal/vertical *size* is `pos` (× cells); `pos=0` (which both `0x00` and `0x80` encode) → **zero-size window = OFF**, regardless of the `right`/`down` anchor bit.

**Reconciliation:**
- The old prior is **wrong on three counts**: (1) it inverted the register meaning (`0x00` is OFF, not full-screen); (2) it mis-stated `VDP_setWindowOff()` as writing `0x80/0x80` (SGDK writes `0x00/0x00`); (3) it was **never validated**. It is also from a **different build line** (SGDK `apps/rastan/`, Window base `0xD000`), not rastan-direct.
- **Build 0120 Window X/Y state:** `reg17 = 0x00`, `reg18 = 0x00` — i.e. **exactly SGDK's `VDP_setWindowOff()` values**. [OBS]
- **Does the old prior apply? NO.** Its inverted semantics do not describe the hardware; its build/VRAM base differ; it was never confirmed.
- **Longstanding vs regression:** The user is correct that this is not a regression — but the correct reading is that the **Window has been OFF all along** (`0x00/0x00` = SGDK off), so the persistent pommel artifact is **not** caused by the Window. Not a regression; also not the Window.
- **Contradiction resolved as:** the old prior's `0x00 = full-screen` claim is **false** (inverted). `0x00/0x00 = Window OFF` per SGDK source. The Window hypothesis for the pommel artifact is **refuted**.

---

## BUILD 0120 WINDOW WRITE AUDIT

Every VDP reg 3 / 17 / 18 write [OBS]:

| reg | site | value | space / mapping | note |
|---|---|---|---|---|
| 3 (WINDOW base) | `vdp_comm.s:77-79` `vdp_boot_setup` | `0x3C` → VRAM `0xF000` | Genesis-only helper (`genesis_only`; not arcade-mapped) | Window nametable base 0xF000 |
| 3 (WINDOW base) | `crash_handler.s:273` `move.w #0x833C,VDP_CTRL` | `0x3C` → VRAM `0xF000` | Genesis-only helper (crash path only) | only runs on exception; irrelevant to title |
| 17 (WINDOW_X) | `vdp_comm.s:117-119` `vdp_boot_setup` | `0x00` | Genesis-only helper | `setWindowHPos(false,0)` equivalent → pos=0 → **0-width** |
| 18 (WINDOW_Y) | `vdp_comm.s:121-123` `vdp_boot_setup` | `0x00` | Genesis-only helper | `setWindowVPos(false,0)` equivalent → pos=0 → **0-height** |

- **Post-boot overwrites of Window X/Y: NONE** — the only reg17/18 writes are the boot-setup `0x00/0x00`; no source path (and Cody's prior audit) writes reg17/18 after boot. [OBS+CODY]
- **Last effective Window X/Y:** `reg17=0x00, reg18=0x00`.
- **Effective Window coverage:** `pos=0` horizontally and vertically → **zero-size window → NONE (Window OFF)**. Window base `0xF000` is set but the plane is never displayed. `vdp_boot_setup` is `genesis_only` translation/init code (not an arcade-mapped site).

---

## MECHANICAL EXPLANATION

- **Plane B exoneration [CODY]:** the sword hilt/pommel graphics are clean in the Layer B viewer → Plane B tile/pattern data is not the direct artifact source. Preserved.
- **Window VRAM garbage/overlap [CODY]:** the Window nametable (`0xF000`) contains patterned garbage and its configured footprint overlaps SAT (`0xF800..0xFA7F`) and H-scroll (`0xFC00`); no Window clear/producer/commit path exists (OPEN-023).
- **Can the Window explain the pommel artifact? NO.** The Window plane is **OFF** (`reg17=0x00/reg18=0x00` = zero-size, SGDK-canonical off). A disabled Window is **never composited**, so whatever garbage sits in `0xF000` is **inert** — it is displayed **nowhere**. The "garbage in the Window viewer" is expected regardless of display state (the viewer dumps the nametable VRAM, not the composite). **The Window cannot obscure the pommel because it is not on the screen.** [OBS+INT]
- **Confidence:** HIGH that the Window is OFF (proven from SGDK `VDP_setWindowOff` source + the boot register values + no post-boot writes). The single residual is that no synchronized **runtime composite + VDP-register** dump was captured (Cody's already-flagged missing evidence); but the register values are definitionally the Window-off state, so a dump would confirm, not overturn, this.
- **Re-attribution [INT]:** with Plane B clean, Plane A showing only lower text (no top-pommel overlap per Cody), and the Window OFF, the remaining live candidate for a pommel-region overlay is **sprite/SAT (OPEN-024 / PC090OJ)** — sprites render above all planes, the SAT is an unfinished subsystem, and Cody's Sprite pane showed a box (though not a perfect positional match). The horizontal-stripe visual class Cody described could be a sprite/SAT artifact. This is the leading candidate now; the Window is exonerated.

---

## DESIGN

**Selected design: NONE — do NOT design or apply a Window-off patch.** The premise (visible/full-screen Window coverage) is refuted: Build 0120's Window is already OFF (`reg17=0x00/reg18=0x00` = SGDK-canonical off).

Per the task's explicit branch — *"If Build 0120 does not have visible/full-screen Window coverage: Do not design a Window-off patch. Report why and state the next evidence needed."* — that branch applies.

**Why the expected `0x00→0x80` candidate is wrong (do not implement):** [OBS+INT]
- `reg17=0x00`/`reg18=0x00` already = Window OFF (SGDK `VDP_setWindowOff`). Changing to `0x80/0x80` sets `pos=0` with the opposite anchor bit — still a **zero-size window** → still OFF. So the patch is at best a **no-op**, at worst it perturbs behavior with no benefit; it is grounded in the old prior's **inverted** semantics.
- It would **not** fix the pommel artifact (the Window is not the cause).
- Answers to the task's design sub-questions, since the branch is "do not patch":
  1. **Files/labels to change:** NONE.
  2/3. **Old/new values:** N/A (no change).
  4. **Production-intent:** N/A — no patch.
  6. **Window nametable clear needed?** NO — the Window is off; `0xF000` garbage is never displayed. (If OPEN-023 later implements a visible Window, clearing would matter then; not now.)
  7. **reg3 = 0x3C keep or move?** KEEP `0x3C` (Window base `0xF000`) — harmless while the Window is off. Moving it is unnecessary and out of scope. (Note: `0xF000` overlapping SAT `0xF800`/H-scroll `0xFC00` is a latent VRAM-layout concern for a *future* visible Window / SAT-DMA — flag under OPEN-023/OPEN-024, do not fix here.)
  8. **Expected visual effect of the proposed patch:** the pommel artifact would **remain** (Window is not the cause) — evidence the patch is misdirected.

**Next evidence needed (to confirm + re-attribute):** [INT]
- The synchronized **title-frame VDP register dump** Cody already flagged as missing — confirming `reg17=0x00/reg18=0x00` (Window off) at the composite frame. (Expected: confirms Window off.)
- The **title-frame SAT / active sprite list** over the pommel region (OPEN-024) — the leading re-attribution candidate. A sprite covering the pommel-region rows would be the horizontal-stripe overlay.
- Cross-check Plane A composite at the pommel (Cody says Plane A is lower text; confirm no top-pommel overlap).

**Recommendation:** do not spend a build on the Window patch. Direct the next investigation at sprite/SAT (OPEN-024). Correct the inverted-semantics prior in the record (see KNOWN_FINDINGS impact) so it stops misleading attributions.

---

## Open / Closed Issues Impact

- **Open issues touched:**
  - **OPEN-023** (Window layer path unimplemented / garbage): context — the Window nametable IS unimplemented/garbage, but the Window is **OFF**, so this garbage is **not player-visible** and is **not** the pommel artifact. Not closed; re-scoped: "Window unimplemented" is real but latent (inert while off). The `0xF000`/SAT/H-scroll VRAM overlap is a latent layout concern for any future visible Window.
  - **OPEN-024** (PC090OJ sprite subsystem incomplete / garbage): elevated — now the **leading** candidate for the pommel artifact (sprites render above all planes; SAT unfinished). Not resolved; not claimed fixed.
  - **OPEN-001** (title/attract graphics incomplete): context — the pommel artifact belongs here; re-attributed away from the Window toward sprite/SAT.
  - **OPEN-006** (sprite palette/high-bank): context via OPEN-024. OPEN-015 (crash-handler numeric fields): not relied on (used WRAM/register evidence + static source). OPEN-021: not touched.
- **Closed issues touched:** NONE.
- **New issues opened:** NONE (recommend correcting the inverted Window-semantics prior in the record).
- **Issues closed:** NONE.
- **Issues intentionally deferred:** implementation (no patch); OPEN-024 sprite/SAT re-attribution (needs the SAT dump); the `0xF000`/SAT/H-scroll VRAM-layout concern (latent, future visible-Window/SAT scope); any Window staging system (out of scope — do not build).

## KNOWN_FINDINGS impact

**Recommend (assess-only; not edited here):** record a durable finding that **Genesis VDP Window OFF = `reg17=0x00, reg18=0x00`** (SGDK `VDP_setWindowOff()` writes these; `pos=0` = zero-size = disabled, regardless of the RIGT/DOWN anchor bit), and that the Build-327-era "Window Plane Disable Fix" prior recorded these semantics **inverted** and was never validated. HIGH rediscovery hazard — it has already misdirected a Build 0120 attribution. This should be canonicalized so the inverted reading is not re-used.

## STOP status

**NO** — analysis complete. The Window hypothesis is **REFUTED** (Window is OFF per SGDK-proven register semantics); **no patch designed** (the proposed `0x00→0x80` is declined as inverted-semantics / no-op / non-fix). Next evidence and re-attribution (sprite/SAT, OPEN-024) stated. (RULES/ARCHITECTURE: no changes made.)
