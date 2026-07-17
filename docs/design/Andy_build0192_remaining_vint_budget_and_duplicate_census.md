# Andy — Build 0192 Remaining VINT Budget + All-Sprite Duplicate Census + Metadata Audit

**Date:** 2026-07-16
**Type:** Analysis (fine-grained VINT timing + chart + arcade-vs-Genesis duplicate census + structured-metadata audit). No new build (no new class-C duplicate proven safe). Repo mirror default 256.
**Baseline:** Build 0192 `42f0b662d0886bbc1a4e1ec5fa2759e9b5c2785911ea404c20dc98b8500eafc1`, size 1,582,860, counter 192.

## User visual result recorded (BlastEm)
Faster; Rastan left + coherent; title/throne/READY render; rolling black bars still occur; one gameplay frame shows a large black band / partial-frame presentation. Improvement candidate, not a full 60 Hz fix.

## Metadata audit (Part 0)
1. Build 0192 suppression documented in structured metadata? **Initially NO.**
2. Owner file: **`specs/rastan_direct_remap.json`** (`opcode_replace` entries for 0x041DAE / 0x041F5E / 0x045DFA) — the source-of-truth.
3. Format: JSON source spec -> generated `build/rastan-direct/rastan_direct_patch_manifest.json` and `build/rastan-direct/address_map.json`.
4. Generator: `tools/translation/postpatch_startup_rom.py` (via `make release`).
5. Build 0192 present there? Was **missing** (notes still said "Helper emits Block-A 18-sprite frame to SAT slots 0..17").
6. Fixed: appended a Build 0192 clause to the `note` for 0x041DAE and 0x045DFA in the spec, documenting the gameplay-gated skip of the spurious A5+0x11B2->records 0..17 copy, the arcade proof (records 0..17 empty), the preserved canonical route (41f5e -> 120..137/92..95), scene gate, visual result, and perf result. Rebuilt -> the note now appears in the generated manifest + address_map; ROM SHA unchanged (metadata-only).
7. No new registry created — the spec is the existing owner.

Going forward, nop/skip/suppress/redirect/helper-substitution changes are recorded in both human docs (design note/AGENTS_LOG/KNOWN_FINDINGS) AND the spec `note` (which regenerates manifest/address_map).

## Part 1 — Build 0192 VINT service budget (measured, MAME, gameplay F>=560, 653 services)
Total service = **26.554 ms/service = 1.59 frames**. 60 Hz budget = 16.667 ms. **Overrun ≈ 9.9 ms (0.59 frame).** Effective VINT-service rate 0.588 (~35 Hz).

| Section | ms/service | % of service | 60Hz frame frac |
|---|---:|---:|---:|
| arcade VINT + main loop | 15.523 | 58.5% | 0.931 |
| vdp_prepare_sprites (PC090OJ) | 10.299 | 38.8% | 0.618 |
| vdp_commit_sprites_vram | 0.273 | 1.0% | 0.016 |
| vdp_reassert_fg_bank3 | 0.163 | 0.6% | 0.010 |
| update_inputs | 0.071 | 0.3% | 0.004 |
| scroll commit | 0.058 | 0.2% | 0.003 |
| bg_project | 0.047 | 0.2% | 0.003 |
| fg_project | 0.047 | 0.2% | 0.003 |
| fg_narrow commit | 0.043 | 0.2% | 0.003 |
| bg_commit | 0.012 | 0.0% | 0.001 |
| commit_tiles | 0.004 | 0.0% | 0.000 |
| palette commit | 0.004 | 0.0% | 0.000 |

**display-off window (off->on) = 0.401 ms/service** (tiny — the VRAM commits are cheap now via Build 0178 tile-DMA cache + Build 0180 SAT gating + Build 0192 half-sprite set).

Chart: `docs/design/build0192_vint_budget_breakdown.png` (horizontal bars, 16.667 ms budget marker).

## Part 2 — Remaining black-bar explanation (measured)
1. Still overrunning 60 Hz budget? **YES** — 26.55 ms = 1.59 frames (overrun ~9.9 ms).
2. Display-off landing during active display? **YES, but only ~0.40 ms (~6 scanlines).** Display-off is issued ~10.4 ms into the service (after vdp_prepare_sprites), which lands ~line 124 mid-screen (VINT entry is at VBlank ~line 224; +10.4 ms ≈ +162 lines). So a small (~6-line) band appears mid-screen and ROLLS because the service period (1.59 frames) is non-integer and prepare_sprites time varies.
3. Rolling black bars still explained by VINT overrun / display-off timing? **YES** — the small rolling band is the mid-screen 0.40 ms display-off; the "large black band" frame is a heavier-service overrun spilling more.
4. Section dominating the overrun: **arcade VINT + main loop (58.5%, 15.5 ms)**, then vdp_prepare_sprites (38.8%, 10.3 ms).
5. Bottleneck shifted? **YES — from PC090OJ prep to the arcade VINT / main-loop.** In earlier builds PC090OJ prep dominated (~2 frames); after Builds 0177/0178/0180/0192 the commits and prep shrank, and the arcade VINT+main-loop is now the largest single cost. Reducing black bars/slowdown further requires (a) cutting the arcade-VINT/main-loop cost (the injected tilemap/palette/PC090OJ hooks running there) and/or (b) moving display-off to VBlank or eliminating it since the commit window is only 0.4 ms — both are VBlank-ordering / hook-cost work, NOT duplicate suppression, so deferred (this task builds only for proven class-C duplicates).

## Part 3 — All-sprite duplicate census (arcade F1100 vs Genesis Build 0192 F1200, matched Stage 1)
Genesis Build 0192 represents 15 records; arcade has 60+ coded (Genesis represents a subset — missing sprites are the separate frozen-progression issue, not duplicates).

| Cluster / object | Genesis records | Arcade records | tile codes | screen X/Y | pal | SAT slots | class | producer/helper | safe to suppress? | metadata entry req? | metadata updated? | reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Rastan (canonical player) | 120,121,124,125,128,129 | 120,121,124,125,126,128,129,130,131 | 009E/009F/00AC/00AD/00AE/00AF | sx 16..32 | 3 | 6 | A | hook_target_41f5e | no (canonical) | no | n/a | matches arcade player; arcade-equivalent multi-sprite composition |
| Rastan low duplicate 0..17 (already fixed Build 0192) | (removed) | (empty in arcade) | player codes | was sx 16..32 | 3 | 0 (was 9) | C — FIXED | hook_target_41dae/45dfa default | done (0192) | yes | spec+manifest+address_map | Genesis-only wrong-helper duplicate; suppressed in gameplay |
| ground/terrain cluster | 17,22,23,24,25 | 17,22,23,24,25 | 002B/002C/002D/0031 | sx 0..168 | 2 | 5 | A | arcade-faithful producer | no | no | n/a | match arcade record indices/codes/positions exactly |
| item/decoration pair | 44,45 | 44,45 | 0049/0047 | sx 264..280 | 2 | 2 | A | arcade-faithful | no | no | n/a | match arcade r44/r45 |
| offscreen stale records | 133,134 | (none in arcade) | 09DB | offscreen (Y=ECCC) | 2 | 2 | E (not a visible duplicate) | hook_target_41f5e block-A over-copy (records 132..137 of the 18-record block hold stale 09DB; arcade's are empty) | NO | no | n/a | offscreen/culled, no visible output, not a duplicate of a visible sprite; suppressing would require altering the canonical 41f5e player producer's block size -> risks Rastan; 2 wasted SAT slots not worth the risk |

Arcade repeated tile codes (03CD x6, 002A x14, 002B x3, 0039 x2) are **legitimate multi-instance decoration/terrain** at distinct positions — class A/B, NOT duplicates.

**Class-C duplicates found (new): NONE.** The only class-C was Rastan's low copy, already fixed in Build 0192. The r133/r134 stale-record pair is class E (offscreen, not a visible duplicate, unsafe to touch). **No build produced.**

## Build decision
STOP / no build — no new class-C duplicate is proven safe to suppress. The remaining budget problem is the arcade-VINT/main-loop cost (58.5%) and the mid-screen display-off timing, both outside this task's duplicate-suppression build scope.

## Not touched
Build 0192 suppression, Build 0180 SAT-dirty gating, Build 0178 tile-DMA cache, Build 0175 palette route, 0171/0172 projections, configurable mirror/default 256 — all preserved. No input/collision/enemy-forcing/sky/D00298/continue/Exodus work.
