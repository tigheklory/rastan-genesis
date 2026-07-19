# Andy/Opus — Gameplay HUD Suppression + Lizard Palette (task "Build 0208" → delivered as **Build 0210**)

**Date:** 2026-07-19
**Type:** Implementation. Two rejected in-task iterations consumed numbers 0208/0209 (preserved); the corrected candidate is **Build 0210/256**.
**Trace dir:** `states/traces/gameplay_hud_suppression_lizard_palette_20260719_124512/`

## ⚠ Build-number deviation (disclosed up front)
The task requested "Build 0208". The first release (iteration 1) consumed 0208, and validation then exposed two implementation gaps; the release guard correctly refused counter reuse ("counter 207 is behind consumed build 0208"), so per the Numbered ROM Artifact Preservation Rule each fix iteration consumed the next number:
- **Build 0208** `df1e6d8fa5e71d9289d3dc2609bbe2a263ef450497a76b731a4b9afd3fb1429f` (1,583,784) — **REJECTED / NOT ACCEPTED**: HUD records already represented at gameplay entry never retired (no scene-transition sweep); bank-0x36 palette never reached the hooks (wrong capture path). Preserved.
- **Build 0209** `44bb7db0836520858dc73a0726be36aa4ae75ec98226701f728904c7ef3a3057` (1,583,828) — **REJECTED / NOT ACCEPTED**: `palette_route_lookup` returns flags in d3, clobbering the decoded sprite code → every lizard slot tile-DMA'd code 0x0001 (resident=0001, bodies invisible, only thin green bars). Preserved.
- **Build 0210** `6dbe8ec35c04f52dcca503e6958c1da5bf622bd6a6fee9409d87e14c22b7806e` (1,583,828, counter 210) — **the corrected candidate**; rolling ROM (byte-identical to the numbered artifact). GATE_PASS.
No numbered ROM was deleted or overwritten across iterations; 0207 remains consumed/lost per its ledger entry.

## Test environments (explicit)
1. **MAME running the original arcade Rastan ROM set** (`-rompath roms`): authoritative bank-0x36 palette + write timing.
2. **MAME running Genesis Build 0206** (`98dc3a1b…`): baseline behavior (banks, HUD representation, lizard SAT lines, shapes).
3. **MAME running Genesis Build 0208/0209/0210** after implementation.

## Proven palette boundary (runtime-confirmed this task)
- MAME/Genesis 0206: `pc090oj_sprite_ctrl_shadow=0x0060` → colbank d7=0x30 → effective banks: HUD records 0x30, Rastan 0x33 → line 3, **lizards 0x36 → (0x36>>4)&3 = line 3 collision** (Genesis WRAM `0x00FFB9FA` shadow; decode at pc090oj_hooks `.Lpc090oj_decode_record`).
- MAME/arcade: PC090OJ palette RAM bank 0x36 (HW arcade `0x2006C0..0x2006DF`) = `0000 4318 00C0 0246 01C0 030E 2948 318A 6356 6B9A 10D2 2996 210A 380E 01CE 39CE` (xBGR-555), written **once at stage load (F100–F300)** and never again; bank 0 also never written during gameplay.
- The bank-0x36 write reaches Genesis through the **sprite-palette SOURCE buffer** path (Build 0161 precedent for bank 51): a5+0x1600 + (bank−0x30)*0x20 → bank 0x36 = Genesis WRAM `0x00FF16C0..0x00FF16DF`, then memcpy to palette RAM (dropped). The palette-RAM-path catch alone (iteration 1) never fired — confirmed by `pc090oj_bank36_cache_valid=0` in 0208 and =1 in 0209/0210 after adding the source-buffer window.

## Objective 1 — gameplay HUD-sprite build option
**Option:** `RASTAN_GAMEPLAY_HUD_SPRITES ?= 1` (Makefile, emitted into the generated `pc090oj_config.inc` alongside PC090OJ_MIRROR_RECORDS). Build 0210 is configured with **0** (suppressed).
**Implementation boundary (all `.if RASTAN_GAMEPLAY_HUD_SPRITES == 0` gated; option=1 compiles to the exact prior code):**
- `.Lpc090oj_sync_record_from_mirror`: during scene 1 (gameplay) force draw=0 for **records 0..45** (record 46 = first enemy). Already-represented HUD records retire through the normal `.Lsync_deactivate` path; new ones never activate. Counter `pc090oj_hud_suppressed_count` records suppressions (evidence).
- `vdp_prepare_sprites`: on any scene-id transition (shadow byte `.Lhud_scene_shadow`), request a full candidate sweep via the existing `.Lpc090oj_set_all_candidates` so records represented under the previous scene's rules re-sync under the new scene's — this retires title/READY-era HUD records at gameplay entry and restores them on exit. No record state is forced; only the existing sweep/sync machinery is used.
**Runtime results (MAME/Genesis 0210):** F400 (frontend): HUD records 22-25/34-36/43-45 represented (non-gameplay presentation preserved). F650+ (gameplay): HUD represented set = **empty**, `hud_suppressed_count`=12→14 (retirement-time only — no per-frame churn). **SAT entries saved: 6–10 slots** during gameplay. VBlank workload: reduced (fewer represented records to place/sync); scene-sweep cost only at transitions. **No arcade HUD/score/life/timer state touched** (suppression is representation-only; mirror writes continue).

## Objective 2 — bank 0x36 → line 0 through the shared architecture
1. **Route table row** (palette_hooks.s, gated): `scene 1, PROUTE_OWNER_PC090OJ, 0x36 → line 0, PROUTE_FLAG_CARRIER`.
2. **PC090OJ palette-line selection** (`.Lpc090oj_place_record_in_slot` palsel): explicit fast checks for banks 0x30→2 and 0x33→3 preserved unchanged; the general path now first consults `palette_route_lookup(current_scene, PC090OJ, effective_bank)` — a hit uses the table line, a miss falls through to the existing `(bank>>4)&3`. d1/d2/**d3** preserved around the call (d3 = decoded sprite code, consumed by the tile-DMA queue — the 0209 lesson).
3. **Palette capture** (palette_hooks.s): bank-0x36 writes are **cached, never staged directly** — windows in `genesistan_palette_hook_3ba64` (source buffer `0x00FF16C0..DF` — the path that actually fires — plus palette-RAM `0x2006C0` bank id) and `genesistan_palette_hook_59ad4` (bank 0x36 row-copy) convert via the existing `.Lxbgr555_to_cram` into `pc090oj_bank36_line0_cache` + `pc090oj_bank36_cache_valid`.
4. **Carrier** (vdp_comm.s): `vdp_reassert_bank36_line0`, called each VBlank next to the FG bank-3 reassert — scene-1-gated, cache-valid-gated, resolves the line via `palette_route_lookup` honoring PROUTE_FLAG_CARRIER, compare-then-restore into `staged_palette_words` + `palette_dirty`. Frontend (scene 0) line 0 is never touched — verified: F400 line 0 = frontend white `0EEE…`, F650+ line 0 = converted bank 0x36.
5. **Converted CRAM line 0 (verified staged):** `0000 08CC 0020 0082 0060 00C6 0444 0664 0CCA 0CEC 0228 046A 0444 0606 0066 0666` — hand-checked conversions (0x4318→0x08CC, 0x00C0→0x0020, 0x0246→0x0082) match the arcade source. Transparent index 0 preserved (entry 0 = 0). Lizard indices 1..12 reference the converted colors.
6. **Preserved routes:** FG bank 3→line 1 (carrier), BG 48→2, Rastan 0x33→3 (verified: line 3 = `08AE 0000 0EEE 08AE…` unchanged, SAT L3=9 Rastan records), HUD bank-0 white in frontend, existing bank 0x30→2 fast path.
No colors hard-coded by record; no lizard-only CRAM write outside the shared staged/commit path; no LUT duplication; no forced SAT palette bits; no FG/BG carrier suppression.

## Validation (MAME running Genesis Build 0210)
- Lizards spawn naturally (lizrep 8→24), composite bodies coherent — **full green lizard men matching the arcade reference artwork** (snap210/genesis/0001.png vs arcade snapshot). Iteration-2's thin-bars defect (d3 clobber) resolved: SAT geometry identical to 0206 (positions/sizes/links), only palette line differs (3→0).
- Lizards select **SAT palette line 0** (SAT histogram L0=8→28 during gameplay; slot dump pal=0 for all lizard slots; resident codes now the real lizard tile codes).
- Rastan correct on line 3 (9 records, palette line 3, CRAM line 3 unchanged).
- FG/BG colors unchanged (lines 1/2 untouched; screenshots normal).
- Gameplay HUD sprites suppressed; frontend/title/READY presentation preserved (F400 HUD represented, line-0 white).
- Arcade score/life state untouched (no gameplay-state writes in the change; suppression is represent-layer only).
- Record 46 not regressed (represented true during gameplay, F1000+).
- Movement/jump/attack functional (mode 0→1, pX 0x20→0xA0, B/C inputs accepted); after the F1050 attack, lizrep 24→16 — consistent with a lizard kill; combat code untouched by this change (representation/palette only). The long-stall run shows a lizard closing in and engaging Rastan, rendered correctly.
- No mode lock, no player corruption, no unmapped access, GATE_PASS.
- Represented count healthy 18→35 (no Build-0203-style collapse; fast-path prevents candidate churn).

## Hurry-up bats
The swarm did **not** trigger in the MAME stall runs (up to F3400), so its effective arcade bank remains **unconfirmed** in this validation. No bat-specific override was added. If the swarm's records carry word0 nibble 6 under colbank 0x30 (effective 0x36 — consistent with Tighe's observation that the swarm sprites render in the same green family), the identical line-0 carrier corrects them with no further work; if they use a different bank, their palette remains unresolved and would need its own route/carrier decision. Deferred to Exodus verification (USER MUST VERIFY).

## Deferred (unchanged, per task)
Lizard-to-Rastan damage correction; lizard vertical alignment; rolling black bar; window-layer HUD; white-only HUD; bat behavior; record 132; FG layout/sky/HUD redesign/D00298/continue/game-over.

## Reporting summary
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0210.bin`, SHA `6dbe8ec35c04f52dcca503e6958c1da5bf622bd6a6fee9409d87e14c22b7806e`, size 1,583,828, counter 210, rolling byte-identical.
- Config: PC090OJ_MIRROR_RECORDS=256, RASTAN_GAMEPLAY_HUD_SPRITES=0.
- opcode_replace: 215 → 215 (unchanged; no spec edits). Coverage: 0x182950 → 0x182AD4 (source growth; paired in both gate scripts).
- Artifact guard: enforced consumed numbers (refused counter reuse after 0208); 0206/0208/0209/0210 all preserved; 0207 remains consumed/lost.

## USER MUST VERIFY (Sega Nomad / Exodus)
1. Stage 1 lizard men appear **green** (arcade-like), full bodies, recognizable artwork.
2. Rastan's own colors unchanged (line 3).
3. Gameplay HUD sprites absent during gameplay; title/READY screens still show their sprites.
4. Arcade score/lives still advance (state alive even though HUD sprites are hidden).
5. Rastan can attack and kill a lizard man.
6. No lower-body sprite loss on Rastan.
7. Stall until the hurry-up bat swarm appears: report whether the swarm's colors are now correct (shared bank 0x36) or still wrong (different bank — report for a follow-up route).

## Files changed
apps/rastan-direct/Makefile; apps/rastan-direct/src/pc090oj_hooks.s; apps/rastan-direct/src/palette_hooks.s; apps/rastan-direct/src/vdp_comm.s; tools/translation/postpatch_startup_rom.py + verify_canonical_rom.py (coverage pair); this doc; ledgers.

## STOP status
STOP not triggered — all STOP conditions avoided (HUD suppressed without touching arcade state; line 0 free after suppression; bank 0x36 carried through the existing architecture; no direct SAT injection; guard conflicts resolved by consuming numbers per the rules).
