# Andy — Build 0234 Graphics Reachability & 68000 Optimization Research

**Date:** 2026-07-24 · **Mode:** research/documentation only — NO source/tool/ROM/counter change (verified at end). Baseline **Build 0234** (`24dc953ed0301c91…`, counter 234). Nothing optimized or removed.

**Evidence routes:** (1) static call graph from `apps/rastan-direct/src/pc090oj_hooks.s` + siblings; (2) install table `specs/rastan_direct_remap.json` (`opcode_replace` ×216, `required_symbols`) + `apps/rastan-direct/out/symbol.txt`; (3) runtime counters on Build 0234 (`states/traces/build0234_bat_stale_*/hot.txt`, `proj.txt`).

---

## 1. Active current graphics architecture (Build 0234)
**Sprite (PC090OJ) path — the live pipeline:**
```
arcade producers (opcode_replace jsr) ─┐
  hook_target_41dae [gameplay] → pc090oj_stage_block2c8 (recs 140-238)
                                → .Lpc090oj_stage_record46_validated (recs 46-56)
                                → pc090oj_native_emit_pass          ← HOT
  hook_target_41f5e / 45dfa / 3b902/3b926/3b930 [frontend]
  hook_score_digit_3b802, _status_sprite_5a098, _sprite_update_54810,
  _copy_56114, _slot_init_54052, _zero_fill_56440, _init_priority_3ad84,
  _sprite_decay_5607c  ──────────────► pc090oj_object_ram (256 rows, arcade store)
                                              │
pc090oj_native_emit_pass ── ONE ascending 256-row scan/frame ──► .Lpc090oj_decode_record
   (viewport clip, code-keyed residency 32set×4way, ≤80 SAT) ──► staged_sprite_sat[/_b] (double-buffered)
                                              │  (VBlank, vdp_comm.s _vblank_service)
vdp_prepare_sprites (frontend fallback) / vdp_commit_sprites ──► .Lvcs_tile_dma + .Lnative_pal_fixup + .Lvcs_sat_dma → VDP
```
**Runtime shape (mode-0 frontend, measured):** `native_emit_pass` ≈ **0.6–0.8 completions/frame** (frontend uses the VBlank fallback; gameplay `41dae` drives it ≈1/frame); **16–48 SAT entries/frame**; **~18–28 producer record-writes/frame**; residency **dropped=2 total**, **oob=0**. The 256-row scan runs essentially every frame regardless of how few rows are populated.

**Plane/tilemap path:** `genesistan_hook_3ad44_dispatch` routes VDP-window fills to `genesistan_hook_tilemap_bg_fill/fg_fill` and `_pc080sn_bg/fg_scroll_fill` (tilemap_hooks.s); scroll committed in vdp_comm.s. **Palette:** `genesistan_palette_hook_*` stage into `staged_palette_words`; `.Lnative_pal_fixup` applies the display-latched colbank per SAT entry at commit. **Scene:** `scene_load.s` loads tilesets on scene change.

---

## 2. Reachability classification
### Confirmed hot (per-frame, multi-iteration)
| Routine | Freq | Cost driver |
|---|---|---|
| `pc090oj_native_emit_pass` | ~1/frame | **256-row scan** + per-drawable decode/residency/emit |
| `.Lpc090oj_decode_record` | ≤256 calls/frame | called per non-HUD row (incl. empties); ~6 insn empty early-out, ~40 insn drawable (opaque clip) |
| `.Lnative_pal_fixup` | 1/frame | ≤80 iterations, per-entry `palette_route_lookup` |
| `.Lvcs_tile_dma` / `.Lvcs_sat_dma` | 1/frame | ≤12 pattern DMAs + 640B SAT DMA |
| `pc090oj_stage_block2c8` | 1/frame (gameplay) | 9 entries × up to 19 records via engine `0x3D254`; per-record `.Lb2c8_yfix` loop |
| `.Lpc090oj_stage_record46_validated` | 1/frame (gameplay) | 11 actors × engine call |
| `.Lpc090oj_family_apply_record` / `.Lpc090oj_emit_slot` | ~20/frame | per-record movem-guarded write |
| vdp_comm.s `_vblank_service` + plane row-DMA | 1/frame | scroll commit + bounded plane DMA |
| tilemap_hooks scroll/plane fills | per scroll (gameplay) | column/row fills |

### Confirmed live but infrequent
`hook_score_digit_3b802`, `hook_status_sprite_5a098`, `hook_sprite_update_54810`, `hook_copy_56114`, `hook_slot_init_54052`, `hook_init_priority_3ad84` (once/frame when their arcade caller fires); `genesistan_palette_hook_*` (per palette update/scene); `scene_load.s` (per scene transition); `.Lpc090oj_mode2_project_p1_hud` (1/frame gameplay, small).

### Hook-live but body obsolete / near-no-op
- `genesistan_pc090oj_hook_target_45dfa` — **gameplay path skips** (scene==1 → `.Lhook_45dfa_skip`, does nothing); only frontend runs the copy.
- `genesistan_pc090oj_hook_sprite_decay_5607c` — its decay loop walks `staged_sprite_descriptor_table`, now a **4-byte zeroed BSS stub** (§ below), so the emit body reads defunct memory and effectively never emits; it **retains a live side effect** (`clr.w 0x10AE/0x10B0(a5)` BG-scroll-accumulator reset). Classify hook-live, decay body dead.
- `genesistan_pc090oj_hook_zero_fill_56440`, `_hook_target_3b926` — clear helpers, fire per caller.

### Compatibility export (symbol retained, no runtime consumer)
The BSS block labeled *"Legacy exported stubs (symbols retained; no runtime consumers)"* aliases **one shared `.space 4`** to: `staged_sprite_descriptor_table`, `pc090oj_candidate_bitset`, `record_to_slot`, `represented_records`, `waiting_records`, `used_sat_slots`, `worklist_entry_for_slot`. Also symbol-only: `staged_sprite_dirty`, `staged_sprite_active_count`. Diagnostic counters that are declared/exported but unused by the live path: `pc090oj_candidate_count`, `_decoded_count`, `_code_zero_skipped_count`, `_blank_skipped_count`, `_unmapped_skipped_count`, `_offscreen_skipped_count`, `_scan_colbank`, `_scan_active`, `_mirror_dirty`, `_represented_count`, `_bootstrap_pending`. (`_emitted_count`, `_dropped_count`, `_producer_write_count`, `_producer_oob_count`, `_drawable_count` ARE written and useful.)

### Legacy/diagnostic (reachable only on fault/self-test)
`genesistan_pc090oj_dma_self_test` (required_symbols but NOT hooked — a VRAM DMA self-test, runs only if explicitly invoked); `genesistan_pc090oj_hook_audit_guard` + the `.Lhook_3ad44_audit` halt path (fire only on an unmapped VDP access → heartbeat halt); **crash_handler.s** (fires on fault). Not hot; must remain for diagnosis.

### Confirmed unreachable / orphan
- **`pc090oj_slot_lut`** — 256-byte incbin in pc090oj_assets.s with **no consumer** anywhere in src (N1 uses code-keyed `sprite_tile_resident_code`, not a slot LUT). Pure orphan ROM data.

---

## 3. Largest credible optimization opportunities (ranked by executed-instruction payoff)
Estimates use the measured envelope: emit pass ~1/frame, 256 rows scanned, ~20–48 drawable, ~20 producer writes/frame, 60 fps.

**#1 — `native_emit_pass` scans all 256 rows every frame; populated rows are sparse & clustered.**
Producers populate only rows **0-8, 30-56, 120-137, 140-238** (measured); rows 57-119 and 239-255 are permanently empty yet decoded every frame. Even the empty early-out costs a per-row `bsr .Lpc090oj_decode_record` + `move.w %d5,-(sp)`/pop (~8 insns) plus decode's 4 loads + code test (~6). ≈256 rows × ~10 insns ≈ **2,560 insn/frame** floor, most of it on empty rows.
- *Cheapest safe win:* inline a `move.w code(row); beq skip` pre-test in `.Lnep_loop` BEFORE the `bsr`, so empty rows never pay the call. Saves ~(200 empty rows × ~8 insn) ≈ **1,600 insn/frame** (~96k insn/s). Preserves ascending-priority order and implicit retirement exactly.
- *Larger win (more risk):* maintain a producer-updated high-water mark or active-row list and scan only populated spans → scan ~80 rows not 256. Saves an additional ~1,000 insn/frame. Risk: MEDIUM (must keep ascending order + implicit blank-row retirement — the mechanism Build 0234 depends on).
**Payoff: LARGE (runtime). Risk: LOW (pre-test) / MEDIUM (active-list).**

**#2 — Per-record helper calls with movem guards inside producer loops.**
`.Lpc090oj_family_apply_record` and `.Lpc090oj_emit_slot` each `movem` save/restore (d5-d6/a0) + bounds-check + `rts` per call; called ~20-130×/frame across block2c8, record46, workram, decay, copy, status, score. Inlining the 4-word store (+ one bounds compare) into the hot producer loops removes a `bsr`+movem+`rts` per record. Saves ~(50-130 calls × ~10 insn) ≈ **500–1,300 insn/frame**.
**Payoff: MEDIUM (runtime). Risk: LOW (mechanical). Cost: static code-size growth (inlined bodies).**

**#3 — Score/HUD digit producers write byte-at-a-time through movem-guarded mirror helpers.**
`hook_score_digit_3b802` calls `.Lpc090oj_mirror_write_byte/word_a1_d0` (each `movem a2` + range check) per byte/word of every digit. The addresses are known-in-range HUD records; a direct `move.b/move.w` to the object row (as `.Lpc090oj_mode2_project_p1_hud` already does) removes the guard overhead. Modest (score producer ~1/frame). **Payoff: SMALL-MEDIUM. Risk: LOW.**

**#4 — `.Lnative_pal_fixup` runs `palette_route_lookup` per emitted entry every frame.**
≤80 entries/frame each doing a palette-route table search at commit. If the per-code→line mapping is stable within a frame, a small per-frame memo (cache last code→line) or hoisting the invariant colbank shift out of the loop trims the per-entry work. **Payoff: SMALL-MEDIUM (runtime). Risk: LOW-MED (palette correctness must be identical).**

**#5 — Orphan/static cleanup: `pc090oj_slot_lut` (256 B) + legacy stub symbols + unused counters.**
Static ROM/BSS only, **zero runtime effect**. Removing `pc090oj_slot_lut` reclaims 256 B ROM; retiring the dead counter words trims BSS. **Payoff: STATIC ONLY (~256 B ROM). Risk: LOW** — but verify `required_symbols`/verification tools don't assert their presence before deleting (they are listed in `required_symbols`, so the linker/verifier expects them; this is a coordinated change, not a free delete).

*(Static vs runtime: #1, #2, #4 are executed-instruction savings; #3 minor runtime; #5 is code-size only.)*

---

## 4. Areas that should NOT be touched
- **The 256-row object store + implicit-retirement contract.** Build 0234's bat fix depends on a blanked row (`Y=0x180`) emitting nothing on the *next ascending scan*. Any active-list optimization (#1 larger form) must preserve ascending order AND still visit rows a producer blanked. Get this wrong and residue/priority bugs return.
- **`.Lpc090oj_decode_record` opaque-geometry viewport clip.** It trades CPU for SAT/scanline budget deliberately (Build 0147). Not a perf defect.
- **crash_handler.s, audit-guard, dma_self_test.** Diagnostic safety nets; keep.
- **Palette line resolution at commit** (`.Lnative_pal_fixup`) — the colbank is display-latched *after* producers run, so it must stay at commit time; only micro-optimize inside it (#4).
- **The `.Lb2c8_yfix`/origin offsets** — these are the coordinate-model compensations analyzed in the companion report `Andy_global_coordinate_collision_pc090oj_intent_research.md`; they are a correctness question, not a perf target, and should be resolved there (single transform), not "optimized" away here.

---

## 5. Recommended order for any future optimization work
1. **#1 pre-test empty rows** in `.Lnep_loop` (largest safe runtime win, minimal risk, no architecture change).
2. **#2 inline the per-record store** in the two hottest producer loops (block2c8, record46) — measure, then extend.
3. **#4 hoist/memoize** the pal-fixup per-entry invariants.
4. **#3 direct HUD digit writes.**
5. **#1 larger (active-row scan)** only after a regression harness proves ascending-order + retirement invariants (highest risk).
6. **#5 static cleanup** last, coordinated with `required_symbols`/verification-tool updates (never a blind delete).

Each step should be validated against Build 0234 output byte-for-byte (SAT + tile DMA) plus a natural gameplay pass (bats retire, no new residue, HUD/lizard/score intact).

---

## 6. MEASUREMENT ADDENDUM (2026-07-24) — cycle-ranked, Stage 1 gameplay
Prior §3 ranked from source-instruction counts measured in **attract** (scene≠1). Attract does **not** run the tall projectors (they are `scene==1`-gated), so §3 omitted the single largest gameplay cost. This addendum re-ranks using **measured Stage 1 gameplay frequency** (reached scene=1 at F=2643; trace `states/traces/build0234_bat_stale_*/measure.txt`) and **estimated 68000 cycles** (Genesis 68000 @ 7.67 MHz ≈ **127,800 cycles/frame** at 60 fps).

### Tall projectors (`vdp_project_bg/fg_tall_if_dirty`, gameplay-only)
- **Entries/frame:** called every gameplay frame from `_vblank_service` (2 calls/frame), but the **copy body** runs only when the projection base changed (`d0≠project_base`) OR the dirty flag is set.
- **Full copies:** each copy = **32 rows × 64 words = 2048 `move.w (a2)+,(a1)+`** + 2048 `dbra`. Cycle est: 2048×12 + 2048×~10 + 32 row-setups ≈ **~45,000 cycles per full copy**.
- **Trigger:** **100% base-change** in the measurement (`bgCopy==bgBaseChg`, `fgCopy==fgBaseChg` every interval) — i.e. driven by the **vertical-scroll row** (`staged_scroll_y>>3`) crossing an 8px boundary. **Zero dirty-only copies observed.**
- **Frequency:** during vertical motion ≈ **0.08–0.18 copies/frame per projector**; **both BG+FG copied ~0.08/frame** (measured `both=10/120f`). When vertical scroll is static (typical horizontal Stage 1 travel) → **0 copies**.
- **Cycles/frame:** avg during vertical motion ≈ 0.18×45k×2 ≈ **~16,000 cyc/frame**; **worst case (both copy every frame) ≈ ~90,000 cyc/frame ≈ 70% of the whole frame budget** — a frame-drop hazard on vertical falls/climbs; static horizontal travel ≈ 0.
- **Direct-DMA feasibility (do NOT implement):** the 32 visible rows are a rotated window of the 64-row tall buffer starting at `base` (mod 64). They can be DMAed **straight to the plane** — **ONE transfer when `base ≤ 32` (contiguous), TWO when it wraps** (`base..63` then `0..base-33`). The strip-commit already DMAs those same 2048 words, so direct DMA **removes the ~45k-cycle copy entirely at no added DMA cost** (net saving ≈ the full copy). Feasible because plane rows are linear; needs careful wrap + VSRAM-residual validation.

### Sprite pipeline (measured gameplay)
- **Rows scanned/frame:** 256, minus the gameplay HUD-skip of records 9–45 (37 rows branch to `.Lnep_next` without decode) ⇒ **~219 decoder calls/frame** (records 0–8 + 46–255).
- **Nonzero-code rows:** **~82–90 of 256** (measured `nzRows`), of which **16–56 in records ≥46**. ⇒ drawable-decoded ≈ 65/frame; **empty rows that still call the decoder ≈ ~154/frame**.
- **Helper-call reconciliation:** `producer_write_count` delta = **~19–27 calls/frame** in gameplay — this **is** the internal-writer call count, confirming the prior "18–28 writes/frame" and **refuting the "50–130 helper calls" estimate**. Inactive block2c8/record46 entries take the blank path (`.Lb2c8_blank`/`.Lrecord46_blank` write `Y=0x180` directly, **not** through `family_apply`), so the 99-record worst case never materializes.
- **Empty-row pretest saving:** each empty-row decode call ≈ ~150 cyc (push/bsr/4 loads/code test/rts/pop/branch); an inline `move.w code(row);andi;beq` pretest ≈ ~24 cyc ⇒ save ~126 cyc × ~154 rows = **~19,000 cyc/frame, EVERY frame (constant, not scroll-dependent).**
- **Record-writer inline saving:** removing the `movem`+`bsr`/`rts` guard (~82 cyc) × ~25 calls = **~2,000 cyc/frame.**

### Corrected ranking (by cycles + risk)
| Rank | Opportunity | Avg cyc/frame | Worst case | Risk |
|---|---|---|---|---|
| **1** | **Empty-row pretest** (sprite scan) | **~19,000 (constant)** | ~19,000 | **LOW** (inline test before bsr; no architecture change) |
| **2** | **Tall-buffer direct DMA** (eliminate 45k copy) | **~16,000 (vertical-scroll only)** | **~90,000 (both-copy frame)** | **HIGH** (wrap logic, plane/VSRAM validation) |
| **3** | **Record-writer inline** | ~2,000 | ~2,000 | LOW (code-size cost) |

**Which to investigate first:** **the empty-row pretest** — it is the best risk-adjusted win (a steady ~19k cyc/frame, ~15% of the frame budget, on *every* frame, with zero change to the object-store/retirement contract). **The tall-buffer direct DMA is the higher *peak* win** (it removes a ~90k-cycle both-copy spike that can drop vertical-scroll frames) and should be the **next design investigation**, but it carries real risk (wrap handling, VSRAM sub-row residual, dirty-row partial DMA) and must be validated against Build 0234 plane output byte-for-byte. **Record-writer cleanup is last** (small, and partly subsumed once the pretest removes most decode calls).

**Net correction vs §3:** the tall projectors — invisible to the attract-only §3 — are the dominant *worst-case* gameplay cost; the sprite empty-row pretest remains the best *average/constant* and lowest-risk win. Do the pretest first, design the tall-DMA second.

---

## 7. BUILD 0235 — code-zero pretest IMPLEMENTED & VERIFIED (2026-07-24)
Implemented opportunity #1 (empty-row pretest) only. **Build 0235:** `dist/rastan-direct/rastan_direct_video_test_build_0235.bin`, SHA256 `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`, size 1,588,440 (+20 B), counter 235, GATE_PASS, opcode 216, coverage 0x183CC4→0x183CD8. Builds 0228–0234 preserved.

**Exact change** (`pc090oj_native_emit_pass`, `.Lnep_loop`, before the `bsr .Lpc090oj_decode_record`):
```
    move.w  %d6, %d0
    lsl.w   #3, %d0
    lea     pc090oj_object_ram, %a0
    move.w  4(%a0,%d0.w), %d0
    andi.w  #0x1FFF, %d0
    beq     .Lnep_next
```
Reproduces exactly the decoder's first rejection (`andi #0x1FFF; beq .Ldecode_notdraw` ⇒ returns d0=0 ⇒ scan does `beq .Lnep_next`), using only scratch d0/a0. Full 256-row ascending scan, row indexing, retirement (Y=0x180), decoder, HUD, opaque clip, palette, residency/DMA, tall-buffer, record-writers all unchanged.

**Verification (external MAME + production counters only):**
- **Output equivalence — injection test (definitive):** at each emit-pass entry, an identical deterministic object_ram (rows 46–255, mixing code-0 rows and nonzero drawable codes) was injected into BOTH ROMs via a write-tap trigger; the freshly-emitted SAT bank was hashed and joined by injection index. **500/500 injected frames: SAT hash + emit count byte-identical** — active decode, zero and nonzero rows, timing-independent. (Cross-run natural play cannot be compared past ~19 frames because two different binaries drift in the arcade game's own RNG/timer state; the 19-frame identical-state window did show SAT/residency/worklist/counts identical.)
- **Decode-call reduction:** full-scan gameplay frames **197 → 36 decoder calls/frame = 161 eliminated (82%)**; averaged over all gameplay frames ~134 → ~35. Est. **~18,400 cycles/frame saved** on a full-scan frame (~114 net cyc/empty row after the ~56-cyc pretest), ≈14% of the 127,800-cyc frame budget.
- **Regression:** gameplay sustained to F9000 (no crash/lock); HUD score digits + white `1UP` (0x39/0x48/0x46) intact throughout; hurry-up swarm spawns and animates; **no frozen corpse (maxCorpseVisibleFrames=0)**; residency/worklist identical in the matched window. Bat retirement is Y-driven (code stays 0x0276 nonzero ⇒ never skipped by the code-zero pretest), so the Build 0234 fix is structurally untouched. Build/boot-guard/canonical gates PASS.

STOP: NO — output equivalence proven, Build 0235 produced.

## Compliance
Build 0235 produced (counter 235). The code-zero pretest is the only source change (pc090oj_hooks.s), plus the paired coverage invariants; no other source, tool, or spec changed. All numbered ROM artifacts preserved.
