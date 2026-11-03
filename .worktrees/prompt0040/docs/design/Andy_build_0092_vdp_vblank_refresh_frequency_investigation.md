# Andy — Build 0092 VDP/VBlank Refresh-Frequency Investigation Design

**Author:** Andy
**Date:** 2026-06-20
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0092.bin` (SHA `4cc782854a40ccf3333ec8ecbe40f71a7617201576c124b60b49e5008fdd20e2`)
**Scope:** Investigation design / static analysis only. No source/spec/tool/Makefile/ROM modifications. No build run. No runtime probing (prior video read as documentation only). No bookmark cycle. No fix. Designs the measurement Cody will run.

Address labels (Rule 3): `runtime_genesis_pc` = patched-ROM file offset / runtime PC; `HW` = hardware; `WRAM` = Genesis work RAM.

---

## Phase 0 — Baseline statement

**Relevant priors from KNOWN_FINDINGS:**
- KF-028 (input-shim/title-text arc; Build 0091 helper-crash → Build 0092 fix; graphics still fail downstream).
- KF-013 (text dispatch inside VBlank — expected; not a violation).
- KF-011 (frame ownership: arcade Level-5 VBlank owns progression; Genesis VBlank servicing-only).
- KF-010 (FG → Plane A `0xE000`; BG → Plane B `0xC000`).
- KF-004 (runtime PC = ROM file offset), KF-006 (identity_offset 0x200).
- KF-001 (watchdog/reset routine `0x3A180..0x3A1AC`: counter countdown + bootstrap re-entry; it does **not** write the VDP — referenced, not rediscovered).

**Rediscovery-Hazard HIGH touched:** KF-028, KF-013, KF-011, KF-001, KF-004 — none contradicted.

**Deferred-appendix entries relevant:** none.

**Task classification:** EXTENDING (downstream investigation of OPEN-001 / OPEN-016 graphics-output failure).

**Open/Closed issues touched:** OPEN-016 (active), OPEN-001 (active — the sparse-dot symptom this addresses), OPEN-015 (context only).

**Contradiction detected:** NO.

**Architecture compliance:** CONFIRMED. The investigation treats the violation criterion as *Genesis-visible VDP state churn*, not arcade-VBlank-context execution. The arcade VBlank handler is the frame producer; that is correct.

---

## Phase 1 — VDP write-path map (Build 0092)

`VDP_DATA = HW 0x00C00000`, `VDP_CTRL = HW 0x00C00004` (`vdp_comm.s:30-31`). On Genesis the VDP decodes `HW 0xC00000–0xDFFFFF`, so arcade PC080SN (`0xC00000–0xC0FFFF`), PC080SN scroll (`0xC20000`/`0xC40000`), and PC090OJ sprite RAM (`0xD00000–0xD03FFF`) all alias VDP ports.

| Path | runtime_genesis_pc | Module | Writes | In `_vblank_service`? | Guard | Cadence |
|---|---|---|---|---|---|---|
| Boot VDP register init | `vdp_boot_setup` (low ROM) | `vdp_comm.s:62-121` | all VDP regs (planes, mode, SAT, autoinc, size…) | NO | — | once, cold boot |
| Display blank (MODE2 off) | within `0x700C2` | `vdp_comm.s:159-161` | reg1 `0x34` | YES | — | once/frame |
| Commit tiles | `0x70106` | `vdp_commit_tiles_if_dirty` | VRAM patterns → `0xc00000` | YES | `tiles_dirty` | ≤1/frame |
| Commit BG strips | `0x70130` (data `0x70122`) | `vdp_commit_bg_strips_if_dirty` | Plane B nametable | YES | `bg_row_dirty` (`0xFF4002`) | ≤1/frame |
| Commit FG strips | `0x7017e` (data `0x70160`) | `vdp_commit_fg_strips_if_dirty` | Plane A nametable | YES | `fg_row_dirty` (`0xFF4006`) | ≤1/frame |
| Commit sprites | `0x719b0` (data `0x71d48`) | `vdp_commit_sprites` | SAT/sprites ← `staged_sprite_sat` | YES | sprite staging | 1/frame |
| Commit palette | `0x701cc` (data `0x701e4`) | `vdp_commit_palette` | CRAM | YES | `palette_dirty` | ≤1/frame |
| Commit scroll | `0x701ec` (data `0x701fa/0x70204/0x70218/0x70222`) | `vdp_commit_scroll` | VSRAM/HSCROLL ← `staged_scroll_*` | YES | — | 1/frame |
| Display unblank (MODE2 on) | within `0x700C2` | `vdp_comm.s:176-178` | reg1 `0x74` | YES | — | once/frame |
| Crash VDP reinit/render | `0x520+`, `0x594+`, `0xA16` | `crash_handler.s` | all regs + CRAM + Plane A | NO | — | crash only (not per-frame) |
| Hooked arcade writers (~102 `opcode_replace`) | various `arcade_pc` | `tilemap_hooks.s` / `pc090oj_hooks.s` | **redirect to WRAM staging** (`staged_bg/fg_buffer`, `staged_sprite_sat`, `staged_scroll_*`), validated against C-window ranges (`0xC00000–0xC03FFF` BG, `0xC08000–0xC0BFFF` FG) — **not the VDP** | NO (run from arcade VBlank) | C-window range check | per producer call |
| **UNHOOKED arcade register-indirect writers** to `0xC0/0xC2/0xC4/0xD0` | **not statically enumerable** | arcade-translated | raw VDP if any exist | NO | UNKNOWN | **runtime question** |

**Key static facts (STATICALLY_PROVEN / DOCUMENTED):**
- The direct VDP-port data writes (`,0xc00000`, 15 sites) are almost all inside the `_vblank_service` commit helpers (`0x70122/0x70160/0x701ae/0x701e4/0x701fa/0x70204/0x70218/0x70222`) plus boot/crash. The 22 control-port writes (`,0xc00004`) are register sets in boot/crash + the per-frame MODE2 toggle.
- Arcade PC080SN/scroll/sprite writes are **register-indirect** (`movew %d2,(%a1)+` etc., pointer = `0xC0xxxx`), so they do **not** appear in absolute-address greps and **cannot be exhaustively enumerated statically**. The ~102 hooks intercept *specific known writer functions* and redirect them to staging; any writer function not in that set writes raw to the VDP. **This is the load-bearing gap.**

---

## Phase 2 — Canonical "one commit per VBlank" contract

`_vblank_service` (`vdp_comm.s:156`, runtime `0x700C2`, installed on the Genesis Level-6 vector, `boot.s:92`) runs **once per VBlank**:
```
movem save → MODE2 DISPLAY_OFF → commit tiles → commit bg → commit fg → commit sprites
→ (palette_dirty? commit palette) → commit scroll → MODE2 DISPLAY_ON → movem restore → jmp 0x3A208
```
- `vdp_commit_*` and `vdp_set_reg` are called **only from within `vdp_comm.s`** (boot setup + `_vblank_service`); grep finds **no external callers** in source. So the commit cycle fires once per VBlank by construction. **STATICALLY_PROVEN.**
- Display enable (reg 1) is toggled **once** per frame (off before commits, on after) — the standard Genesis blank-during-bulk-write pattern.
- Plane bases, mode, SAT base, autoincrement, plane size are set **once at boot**, not per frame.
- All visible-plane content is sourced from WRAM staging (`staged_bg_buffer`/`staged_fg_buffer`/`staged_sprite_sat`/`staged_scroll_*`) populated by the hooked producers; the commit DMAs/streams them to VRAM/CRAM/VSRAM.

This contract is Genesis-compatible. The hypothesis is therefore **not** about `_vblank_service` itself — it is about whether anything *outside* this path also touches the VDP per frame.

---

## Phase 3 — Suspect paths (potential contract violators)

- **S1 (primary) — Unhooked register-indirect writers to VDP-aliased hardware.** Any arcade writer to `0xC00000–0xC0FFFF` (PC080SN tilemap), `0xC20000`/`0xC40000` (scroll), or `0xD00000–0xD03FFF` (sprites) that is **not** in the ~102-hook set writes raw to the VDP every frame → uncontrolled data-port writes with no address setup → sparse dots. This is the deferred "unhooked-writer survey." **NOT statically enumerable** (register-indirect). HYPOTHESIS-CONSISTENT.
- **S2 — Commit re-entry / extra commit cycles.** Static: no external callers of `vdp_commit_*`, so >1 cycle/frame is not visible statically; confirm at runtime that exactly one display-off→commit→display-on cycle occurs per VBlank.
- **S3 — Extra display-enable toggles.** Static: only `_vblank_service` toggles MODE2 per frame; confirm no other per-frame reg-1 writes (which would churn display mid-active-scan).
- **S4 (FAIL-alternative) — Bad staged data, not churn.** If S1–S3 are clean (one coherent commit/frame, no raw VDP writes), the sparse dots are explained by *wrong staged content*: descriptor/LUT math producing garbage cells (cf. the Build 0091 hook register-setup bug — `%a3`/`%a5`/`%a6` correctness), wrong plane base, wrong/empty palette, or missing tile patterns. A different investigation, not the refresh-frequency hypothesis.
- **Watchdog/reset routine `0x3A180`** (KF-001): a counter countdown + bootstrap re-entry; it does **not** write the VDP. Not a VDP-churn suspect. (Referenced per KF-001; not rediscovered.)

**Anti-drift:** none of these is suspect merely for running inside arcade VBlank. S1–S3 are about Genesis-visible VDP state being written **outside the single staged commit** or **more than once per frame**.

---

## Phase 4 — Measurement specification for Cody (runtime, read-only)

Use the emulator debugger (Exodus and/or MAME) as a **read-only observer** over a no-input steady-state window (≥10 consecutive frames after the title settles) — consistent with prior video/register captures, no source scaffolding:

- **M1 — VDP-port write trace.** Set write-watchpoints on the VDP ports `HW 0xC00000–0xC00007` (verify the emulator also catches mirror writes across `0xC00000–0xDFFFFF`; if not, add watchpoints on `0xC08000`, `0xC20000`, `0xC40000`, `0xD00000`). Log `(frame#, writing PC, target port/sub-address, value)` for the window.
- **M2 — Classify each writing PC** as **canonical** (the `_vblank_service` set: `0x700C2` MODE2 toggles; data writers `0x70122/0x70160/0x701ae/0x701e4/0x701fa/0x70204/0x70218/0x70222`; sprite `0x71d48`) vs **non-canonical** (anything else, especially arcade region `0x200–0x6FFFF`).
- **M3 — Per-frame counters:** (a) total VDP-port writes; (b) distinct writer PCs; (c) non-canonical writer count; (d) reg-1 / MODE2 (display-enable) control writes; (e) number of full display-off→commit→display-on cycles.
- **M4 — Top-N non-canonical writer call sites** (PC + writes/frame) to name any specific unhooked writer.
- **M5 — Coherence corroboration (distinguishes S1–S3 from S4):** at VBlank exit for 2–3 frames, dump Plane A nametable (`VRAM 0xE000–0xEFFF`), Plane B (`0xC000–0xCFFF`), CRAM, and `staged_fg_buffer`/`staged_bg_buffer`. Check whether the *staged* content is coherent text/tiles (→ S4 commit/data problem) or whether VRAM shows mid-frame-churned garbage inconsistent with a single staged commit (→ S1–S3).

---

## Phase 5 — Pass/fail criteria

**PASS (refresh-frequency hypothesis supported)** if any of: >1 display-off→commit→display-on cycle per frame (M3e); nametable/CRAM/scroll/display written repeatedly within one frame (M1/M5); non-canonical VDP-port writes, especially from the arcade region (M2/M4); repeated reg-1/display-enable toggles per frame (M3d); multiple producers racing on the same visible region within a frame.

**FAIL (hypothesis ruled out)** if: exactly one commit cycle per frame; no non-canonical VDP-port writes; display-enable and plane bases stable; nametable/CRAM/scroll staged and committed once. If FAIL, M5 points to the **S4 alternative** — bad staged data (descriptor/LUT/`%a3`/`%a5` correctness, wrong plane base, wrong palette, or missing tile patterns) — to scope a separate data-correctness investigation.

---

## Phase 6 — Bounded recommendation

**Static evidence is NOT sufficient to rule out the hypothesis.** The canonical one-commit-per-VBlank contract is proven, but unhooked register-indirect VDP-aliased writers are not statically enumerable, so the refresh-frequency question requires runtime measurement.

**Recommended next task (Cody, runtime, read-only):** execute the M1–M5 VDP-write profiling above over a no-input steady-state window and report the per-frame counters + top-N non-canonical writers + the M5 coherence dump. The result selects the next investigation: PASS → identify and hook the offending unhooked writer(s) (extending the existing hook pattern); FAIL → S4 staged-data-correctness investigation (starting with the FG glyph path's `%a3`/`%a5` LUT bases and plane base/palette). No fix designed here.

---

## KNOWN_FINDINGS impact

**Option A — no update.** This is investigation design; it proves no new durable mechanism (the one-commit-per-VBlank contract is already implied by KF-011/ARCHITECTURE). A KF refinement waits on Cody's measurement (PASS → unhooked-writer mechanism; FAIL → staged-data mechanism). `KNOWN_FINDINGS.md` not modified.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-016 (active — may need further work beyond Part 2 depending on PASS/FAIL; not closed), OPEN-001 (active — the sparse-dot rendering symptom; not closed), OPEN-015 (context only).
- Closed issues touched: NONE. New issues opened: NONE. Issues closed: NONE.
- Intentionally deferred: Start→C→A crash, OPEN-015 crash-handler fix.

## STOP triggered

NO.
