# Andy/Opus — Lizard-Man Composite PC090OJ Staging Design (Design only, NO BUILD)

**Date:** 2026-07-18
**Type:** Implementation-ready design. **No source/spec/Makefile/gate/ROM change. No build. No counter change.**
**Target:** block A5+0x2C8 → composite PC090OJ records 140..238 (the first visible Stage-1 lizard men, KF-064).

## Phase 0 baseline
Relevant priors from KNOWN_FINDINGS:
- KF-060 — enemy writers 0x41DAE/0x45DFA NOPped; staging-gap root. **Applicability:** block 0x2C8 is a block of that same NOPped 0x41DAE writer.
- KF-061 — engine unsafe on INVALID (code-0) actors; **scoped** by KF-063 to invalid actors only. **Applicability:** block 0x2C8 e0 is exactly such an invalid actor — the load-bearing hazard.
- KF-062 — Genesis populates the actor blocks (camera/scroll spawn works). **Applicability:** block 0x2C8 valid lizard actors exist on Genesis.
- KF-063 — engine safe on VALIDATED actors (active + nonzero code + a4@(0x36)==0); Build 0204 fixed the shared 0x3C950 empty-output. **Applicability:** the safety gate and the 0x3C950 fix are directly reused.
- KF-064 — corrected lizard ownership: block A5+0x2C8 → composite records ~140..229, codes 0x004B-0x0069; record 46 is a distinct non-lizard sprite. **Present; current wording matches.**
Rediscovery Hazard HIGH findings touched: KF-060, KF-061, KF-062, KF-063, KF-064.
Task classification: EXTENDING (block-0x2C8 ownership → implementation-ready staging design).
Open/Closed issues touched: OPEN-017, OPEN-024, OPEN-001 (graphics context).
Contradiction of CONFIRMED/STRONG finding: NONE.

## Recovered repository state (verified, matches authoritative)
counter 204; rolling Build 0204/256 SHA `0e1925b2934e2d2614bb6c90de82c78ea07bc62819b58fe345fb83f8e5deb083` size 1583248; Makefile default 256; config 256; opcode_replace 214; coverage 0x182890; Build 0203 preserved (rejected); Build 0202 consumed/deleted; Build 0205/0206 absent. No discrepancy. No changes made by this task.

## KF-064 hygiene result
KF-064 **is present/merged** in KNOWN_FINDINGS.md as a distinct ownership finding (not a duplicate of KF-060). The prior report's label "Option A — added KF-064" was procedurally wrong (adding a new entry is **Option B**), but the executed action and the entry content are correct and consistent. **Disposition:** no ledger inconsistency, no renumbering, no history change. The label error is noted here; KF-064 stands as-is.

## Phase 1 — Exact arcade block-0x2C8 writer reconstruction (arcade_pc 0x00041E22)
The block is the third of four in arcade routine `arcade_pc 0x00041DAE`:
```
arcade_pc 0x00041E22  lea   %a5@(0x2C8),%a4      ; actor block base A5+0x2C8
arcade_pc 0x00041E26  clrw  %a5@(0x214)          ; entry index counter (A5+0x214)
arcade_pc 0x00041E2A  lea   0xD00460,%a1         ; dest = PC090OJ record 140 (0xD00460/8)
.entry:
arcade_pc 0x00041E30  tstb  %a4@(0)  ; beq blank   (active gate)
arcade_pc 0x00041E38  tstb  %a4@(5)  ; beq blank   (secondary active gate)
arcade_pc 0x00041E40  tstb  %a4@(3)  ; bne 0x3EFBE (special path -> NOT engine)
arcade_pc 0x00041E48  moveb %a4@(1),%d0           ; actor code
arcade_pc 0x00041E4C  moveb %a4@(0x20),%d6        ; attr/Y source
arcade_pc 0x00041E50  moveb %a4@(2),%d7           ; attr/X source
arcade_pc 0x00041E54  moveq #10,%d2               ; record budget
arcade_pc 0x00041E56  cmpiw #8,%a5@(0x214); bne .call; moveq #19,%d2   ; entry 8 -> d2=19
arcade_pc 0x00041E60  bsr   0x3D054               ; engine (writes EXACTLY d2 records via a1@+)
arcade_pc 0x00041E64  adda.l #64,%a4              ; next 64-byte actor
arcade_pc 0x00041E6A  addqw #1,%a5@(0x214) ; cmpiw #9 ; bne .entry   (9 entries, idx 0..8)
.blank (0x41EDE): movew #384,%d0 ; d2=10 (19 if idx8) ; { movew %d0,%a1@(2); addq.l #8,%a1 } x d2
```
Established semantics (address-labeled):
- **Actor-block base:** A5+0x2C8 = `HW_ADDRESS/68k-WRAM 0x0010C2C8` (arcade) / `0x00FF02C8` (Genesis).
- **Actor-entry size:** 64 bytes.
- **Entry count:** 9 (indices 0..8).
- **Initial destination record:** 140 (`0xD00460 / 8`).
- **Destination-address calc:** `%a1` set ONCE to record 140; advanced by the engine/blank-fill.
- **d2 semantics:** record budget/count; engine writes EXACTLY d2 records (loop `subql #1,%d2` at `arcade_pc 0x0003C9A0/0x0003C9E2`), so `%a1` advances by exactly d2 per entry. d2 = 10 for entries 0..7, **19 for entry 8**.
- **Actor fields read:** a4@(0) active flag; a4@(1) actor code (→ engine dispatch/layout); a4@(2) X-attr (→d7); a4@(3) "special" flag (nonzero → 0x3EFBE, bypasses engine); a4@(5) secondary active gate; a4@(0x20) Y-attr (→d6); a4@(0x36) checked by the shared KF-063 gate (record-46 route) — here the arcade gate set is {a4@(0), a4@(5), a4@(3)}.
- **Validity gates:** active = a4@(0)!=0 AND a4@(5)!=0; if a4@(3)!=0 → special (not engine).
- **Inactive/blank behavior:** blank-fill d2 records with word1(Y)=0x0180 (off-screen), leaving word0/2/3 as-is; advances `%a1` by exactly d2.
- **Maximum tuples per actor:** exactly d2 = **10** (entries 0..7) / **19** (entry 8).
- **Maximum tuples per block:** 8×10 + 1×19 = **99 records**, span **records 140..238** (last record 238 = byte 238*8).
- **Tuple counts:** fixed per entry (= d2), NOT actor-code dependent for the a1 stride (the engine pads to d2; nonzero-vs-blank content within the d2 window is code-dependent).
- **Unused records blanked:** yes — the engine/blank-fill writes the full d2 window each frame (real tiles + blank padding), so stale content within the block span is overwritten every invocation.
- **Overlap/overwrite:** entries write strictly sequential, non-overlapping d2 windows; block output is bounded within records 140..238.
- **Final destination boundary:** record 238 (byte offset 238*8 = 0x770 from PC090OJ base; genesis mirror `0x00FFA9D8 + 0x770`).
- **Registers/side effects:** the arcade routine uses A5+0x214 (transient loop counter, shared with sibling sprite routines, non-persistent); the engine preserves a4/a5, advances a1, clobbers d0-d7/a0. No persistent A5-relative game-state side effects on this path.

**Observed Genesis/arcade record layout (arcade F900):** records 140-143 nonzero (entry 0, special 0x3EFBE, code 0x017C — NON-lizard); 150-179 blank (entries 1-3 inactive); **180-229 nonzero = the visible lizard bodies** (entries 4-8, codes 0x006D/0x0069); 230-238 blank padding (entry 8 d2=19). This is the deterministic d2-stride: entry N base = 140 + (sum of prior d2).

## Phase 2 — Composite engine paths (arcade_pc 0x0003D054 / runtime_genesis_pc 0x0003D254)
For valid lizard actor codes 0x17/0x18/0x1C-0x1F (and 0x70 where reachable):
- Dispatch on a4@(0x38) (=0, for these actors) → PC-relative jump-table path → `runtime_genesis_pc 0x0003CB02` shared expansion body.
- The body writes records through `%a1@+` only (no a5-relative/absolute writes; the earlier apparent a5@ hits are misdisassembled layout data). It reads a4@(0x16/0x18/0x1A/0x1E/0x27/0x03), the PC-relative sprite-layout tables, and d6/d7.
- **Number of (%a1)+ writes = exactly d2** (real tile records + blank padding), so output is bounded by the caller's d2 and never exceeds the per-entry window.
- **Shared 0x3C950 writer:** the default shape path reaches `arcade_pc 0x0003C950` / `runtime_genesis_pc 0x0003CB50`, replaced by `genesistan_hook_text_writer_3c950`. Build 0204 made it **destination-aware**: `%a1` in the C-window (0x00C00000..0x00C10000) → PC080SN FG staging; otherwise → `.L3c950_sprite_direct` preserving the original `a1@+` sprite-record writes. Since the block-0x2C8 scratch lives in WRAM (NOT the C-window), the sprite-direct path is taken and every composite write is preserved. **Compatible — no change needed.**
- **Relocation:** engine jmp targets relocated +0x200 (0x4790E/0x3F2BC/0x401DC/0x401F0/0x3CB02) and PC-relative dispatch tables self-relocate (verified in KF-063 work). No unrelocated sub-engine pointer.
- **Unsafe paths:** ONLY the invalid-actor dispatch (code 0 + a4@(0x38)/a4@(3) garbage → wild jump). Prevented by the KF-063 validity gate. **No other unsafe path found.** The a4@(3)!=0 special (0x3EFBE) is out of the engine path and is gated out here.

## Phase 3 — Scratch-storage proof → **Selected: Pattern B (whole-block scratch)**
The 8-byte record-46 scratch is insufficient (d2 up to 19). Selection:
- **Pattern C (direct mirror a1) — REJECTED:** engine `a1@+` into the mirror bypasses `.Lpc090oj_family_apply_record` change-detection/candidate bookkeeping (forbidden) and risks writing past record 238.
- **Pattern A (per-actor scratch, 19 records) — REJECTED:** requires re-deriving each entry's cumulative record base and separately blanking inactive spans; more failure surface; does not naturally reproduce the cross-entry a1 progression.
- **Pattern B (whole-block scratch) — SELECTED:** a contiguous scratch representing records 140..238; `%a1` starts at scratch[0] (=record 140) and the exact arcade iteration advances it by d2 per entry (engine for valid, blank-fill for inactive/invalid). This reproduces the arcade a1 progression and blanking EXACTLY, then the whole window is applied to the mirror via the existing change-detecting path. Safest (bounded, no mirror overflow) and most faithful.

Selected design specifics:
- **Scratch base symbol:** new `pc090oj_block2c8_scratch` in `.bss`.
- **Exact byte size:** 100 records × 8 = **800 bytes** (covers the 99-record max; 1-record margin).
- **Alignment:** `.align 2` (word).
- **WRAM placement:** `.bss`, adjacent to the existing pc090oj mirror region (current: staged_sprite_sat 0xFFA1B0 / pc090oj_object_ram 0xFFA9D8 / pc090oj_mirror_shadow 0xFFB1D8 / pc090oj_candidate_bitset 0xFFB9D8). Place BEFORE staged_sprite_sat or after candidate_bitset — either way a fresh 800-byte `.bss` reservation.
- **Neighboring symbols / overlap proof:** a new `.bss` symbol gets its own linker-assigned range; it cannot overlap the mirror (0xFFA9D8..0xFFB1D8), shadow, candidate bitset, or player WRAM (0xFF0000-region) because those are distinct `.bss`/WRAM symbols. Stack independence: the 68k stack is at high WRAM (top of 0xFFxxxx), far above the pc090oj `.bss` cluster; 800 bytes does not approach it.
- **Compile-time assertions:** `.if (8*10 + 19) > 100 ; .error ; .endif` (max span ≤ scratch records); assert scratch record count ≤ PC090OJ_MIRROR_RECORDS is NOT required (scratch is fixed 100, independent of mirror cap) but the FLUSH must OOB-guard record indices ≥ PC090OJ_MIRROR_RECORDS (family_apply_record already does).
- **Maximum write endpoint:** scratch[99] byte 99*8+7 = offset 799; within 800.
- **Bounds checks:** the iteration writes at most 99 records; a runtime guard `a1 <= scratch + 100*8` before each engine call is specified as defense-in-depth.
- **Behavior on invalid actors (e0, code 0 / a4@(3)!=0):** DO NOT engine-call; blank-fill its d2 window (records 140-149). (Loses the non-lizard 0x3EFBE code-0x017C sprite at 140-143; deferred, documented.)
- **Behavior on inactive actors (a4@(0)==0 or a4@(5)==0):** blank-fill d2 window (matches arcade).
- **Behavior when output shrinks frame-to-frame:** the whole 99-record scratch is rebuilt each frame (engine/blank-fill overwrite the full d2 windows), so a lizard that disappears leaves its window blank-filled → the mirror record transitions to blank → represent drops it. No stale tuples.

If no safe bounded layout could be proven → STOP. It IS proven → continue.

## Phase 4 — Clear/stale-record semantics
- Arcade clears/overwrites the FULL 99-record block span every invocation (engine writes exactly d2 records incl. blank padding; blank-fill for inactive). The design mirrors this: rebuild the whole scratch window each frame.
- Records persisting unchanged (a stationary lizard) produce identical scratch tuples → `.Lpc090oj_family_apply_record` fast-path (Build 0193) skips them → **no candidate churn**.
- Records blanked when an actor disappears: its d2 window becomes blank in scratch → family_apply_record detects the change → mirror record cleared + candidate set once → represent drops it.
- Each entry owns a FIXED d2 sub-window (deterministic base). Variable *content* (nonzero vs blank within the window) is handled by the engine; the window length is fixed.
- Transitions (no lizard / one / several / animation change / death/off-screen) are all expressed as scratch-window content changes flushed through the existing change-detecting path.
- Prohibited: leaving stale tuples; blanket-blanking every frame unconditionally (the scratch IS rebuilt but the *mirror* only changes where content changed, via fast-path); marking all records changed every frame; flushing code-0 placeholders as "changed" when they were already blank (fast-path prevents this).

## Phase 5 — Candidate/representation design
Application path (unchanged pipeline): scratch record → `.Lpc090oj_family_apply_record` (d0=record 140+i, d1..d4 = scratch tuple) → change-compare vs mirror → on change: write mirror + set candidate bit + set mirror_dirty → VBlank `process_candidates` → represent → SAT → tile-DMA worklist → VDP commit.
- Reuse `.Lpc090oj_family_apply_record` exactly (the proven Build 0157/0177/0193 path). No second candidate mechanism, no blanket candidate set, no forced SAT, no tile-residency bypass.
- Unchanged records avoid churn via the fast-path tuple compare (identical tuple → no candidate, no mirror write). This is exactly how Build 0204 keeps represented count stable at 17 for record 46; the same mechanism bounds block-0x2C8 churn to only genuinely-changed lizard records.
- Build 0203 regression avoidance: Build 0203's churn came from flushing an EMPTY/uninitialized scratch and mis-scoped writes; here the scratch is fully rebuilt to arcade-faithful content and only real changes propagate.

## Phase 6 — Capacity / hardware-budget analysis (measured)
- **Max simultaneously nonzero lizard composite records (measured, arcade F900):** records 180-229 = **50** nonzero (entries 4-8). (Entry-0 span 140-143 is skipped/blanked in this design → not counted.)
- **Pre-lizard represented count (measured, Build 0204):** 17.
- **Expected represented total:** ≈ 17 + up-to-50 = **≈ 67**.
- **Genesis 80-entry SAT limit:** 67 < 80 → **FITS** (18% headroom). No SAT-cap change.
- **20-sprites-per-scanline (H40):** lizards stand on the ground in a shared Y band; each lizard ≈ 8-10 records spread over ~2-3 scanline rows. At the captured scene (2-3 visible lizards) ≈ 8-12 sprites/scanline < 20 → fits. **Risk:** if 5+ lizards cluster at the same Y, a scanline could exceed 20 and the VDP would drop the lowest-priority sprites on that line (arcade has no such limit). This is a measure-in-validation risk, not a hard STOP at the captured scene.
- **Rastan lower-body risk:** Rastan = records 120-131 (unchanged); lizard records 140-238 are disjoint and all < 256. The mirror cap stays 256 (NOT changed), so the 128-experiment truncation does not apply. Rastan's body is unaffected.
- **256-record candidate scan cost:** the full 256-record candidate scan already runs each VBlank; adding ≤50 changed records/frame adds ≤50 record syncs. Lizard TILE data is cached by the tile-residency worklist (only new tiles DMA), so per-frame cost is dominated by ≤50 cheap SAT updates. **Expected VBlank effect:** small increase; must be measured against the existing budget in validation (no new suppression authorized).
- **Hardware-capacity STOP:** NOT triggered at the captured scene (67 < 80 SAT). Per-scanline clustering flagged for validation measurement.

## Phase 7 — Register / control-flow contract
Proposed helper `pc090oj_stage_block2c8` (replacing the block-0x748 body target of the gameplay 41dae hook, or added alongside — see blueprint):
- **Entry point:** called from `genesistan_pc090oj_hook_target_41dae` gameplay branch (same site Build 0204 uses for record 46). Arcade remains the caller and frame owner.
- **Return path:** `rts` directly back to arcade 0x41DAE flow. No Genesis loop/lifecycle/scheduler introduced.
- **Preserved:** all regs via `movem.l %d0-%d7/%a0-%a6,-(%sp)` / restore (as the record-46 helper does).
- **Clobbered (internally):** d0-d7, a0-a4, a6 (restored on exit).
- **Stack usage:** one movem frame (60 bytes) + engine's own frames.
- **%a4:** actor pointer, `lea 0x02C8(%a5),%a4`, advanced +64 per entry.
- **%a1:** output pointer into `pc090oj_block2c8_scratch` (record 140 origin), advanced by engine/blank-fill.
- **d0/d2/d6/d7 setup per active entry:** d0=a4@(1), d6=a4@(0x20), d7=a4@(2), d2=10 (19 for entry 8).
- **Scene gating:** gameplay-only (scene 1), same as the current 41dae gameplay branch — preserves Build 0192 duplicate-Rastan intent and the non-gameplay path.
- **Actor validation:** active (a4@(0)!=0 AND a4@(5)!=0) AND nonzero code (a4@(1)!=0) AND a4@(3)==0. Fails → blank-fill window (never engine-call).
- **Iteration bounds:** exactly 9 entries; a1 bounded to scratch (100 records).
- **Exit:** after 9 entries, flush 99-record window; restore regs; rts.
Proven: arcade stays caller/frame-owner; helper returns directly; no lifecycle/boot re-entry; no forced gameplay state; no blocking/scheduling.

## Phase 8 — Exact implementation blueprint (for Cody)
**Files to modify:** `apps/rastan-direct/src/pc090oj_hooks.s` ONLY (helper + hook wiring + `.bss` scratch). Paired coverage-invariant update in `tools/translation/postpatch_startup_rom.py` and `verify_canonical_rom.py` (source growth only). NO spec/opcode change expected (source-only; opcode_replace stays 214).
**Symbols to reuse:** `.Lpc090oj_family_apply_record`, `genesistan_current_scene_id`, `PC090OJ_SCENE_GAMEPLAY_ID`, engine `0x0003D254`, existing candidate/represent pipeline.
**New symbols (unavoidable):** `pc090oj_block2c8_scratch` (.bss, 800 bytes), `pc090oj_stage_block2c8` (.text).
**Hook to modify:** `genesistan_pc090oj_hook_target_41dae` gameplay branch — call `pc090oj_stage_block2c8` (block 0x2C8, records 140+) IN ADDITION TO the existing record-46 route (block 0x748). Do NOT touch the 41f5e player path or reintroduce `pc090oj_workram_block_sprites`.
**Assembly-level pseudocode:**
```
pc090oj_stage_block2c8:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    ; clear whole scratch (100 records)
    lea pc090oj_block2c8_scratch,%a0 ; move.w #(800/4-1),%d0 ; .clr: clr.l (%a0)+ ; dbra %d0,.clr
    lea pc090oj_block2c8_scratch,%a1      ; a1 = record-140 origin
    lea 0x02C8(%a5),%a4
    clr.w  %a5@(0x214)                    ; entry index (arcade-faithful)
.entry:
    ; compute d2 for this entry (10, or 19 if index==8)
    moveq #10,%d2 ; cmpi.w #8,%a5@(0x214) ; bne .haved2 ; moveq #19,%d2
.haved2:
    ; validate
    tst.b (%a4)      ; beq .blank
    tst.b 5(%a4)     ; beq .blank
    tst.b 3(%a4)     ; bne .blank        ; invalid/special -> blank (defer 0x3EFBE)
    tst.b 1(%a4)     ; beq .blank        ; code 0 -> blank (KF-063 guard)
    ; bounds guard: ensure a1 + d2*8 <= scratch end (defensive)
    move.b 1(%a4),%d0 ; move.b 0x20(%a4),%d6 ; move.b 2(%a4),%d7
    jsr 0x0003D254                        ; engine writes exactly d2 records via a1@+
    bra .next
.blank:
    ; blank-fill d2 records: { move.w #0x0180,2(%a1) ; addq.l #8,%a1 } x d2  (clr others already 0)
.next:
    adda.l #64,%a4 ; addq.w #1,%a5@(0x214) ; cmpi.w #9,%a5@(0x214) ; bne .entry
    ; flush 99-record window to mirror
    lea pc090oj_block2c8_scratch,%a2 ; move.w #140,%d0
.flush:  ; for i in 0..98: family_apply_record(record=d0, tuple=scratch[i]); a2+=8; d0++
    move.w (%a2),%d1 ; move.w 2(%a2),%d2 ; move.w 4(%a2),%d3 ; move.w 6(%a2),%d4
    bsr .Lpc090oj_family_apply_record
    adda.l #8,%a2 ; addq.w #1,%d0 ; cmpi.w #(140+99),%d0 ; blo .flush
    movem.l (%sp)+,%d0-%d7/%a0-%a6 ; rts
```
(Note: after the engine call, `%a1` is already advanced by exactly d2; the blank path advances it explicitly. Both keep a1 aligned to the next entry's window. The flush iterates the fixed 99-record span, so even a defensive engine overrun within scratch is not propagated beyond record 238.)
**Output-length handling:** fixed per entry (= d2); flush covers the fixed 99-record span.
**Clearing:** whole scratch cleared each frame; blank-fill for inactive/invalid; family_apply_record fast-path avoids re-marking unchanged records.
**Changed-record application / candidate behavior:** via `.Lpc090oj_family_apply_record` only.
**Required bounds assertions:** `.if (8*10+19) > 100 ; .error "block2c8 span" ; .endif`; runtime a1 bound guard before engine call.
**Gate/invariant updates:** paired `CANONICAL_TOTAL_GENESIS_BYTES_COVERED` bump for the source growth (value = the build's reported "got"); opcode_replace unchanged (214).
**Expected opcode_replace impact:** none (source-only). **Expected coverage impact:** +~0x2xx (helper + scratch); paired update both gate scripts.
**Prohibited shortcuts:** no direct mirror `a1@+`; no engine call on code-0/a4@(3)!=0; no blanket candidate set; no whole-range unconditional "changed"; no mirror-cap change; no per-scanline heuristic; no bat/palette/collision work; no 0x3EFBE forcing.

## Future Build 0205 validation matrix
Pre-build gates: Build 0204 baseline recovered; 0203 preserved; 0202 consumed; counter 204 pre-release; no unrelated dirty; mirror default 256; scratch bounds statically asserted; invalid e0 proven not to reach the engine.
ROM: only after approval, one 256 main = Build 0205 (advance counter to 204→build 0205; NO 192 build unless Tighe requests); preserve 0205 even if rejected; rolling changes only on pass.
Runtime correctness (arcade vs 0204 vs 0205 at matched state): valid lizard actors populated; invalid e0/code-0 never enters engine; records 180-229 become nonblank where arcade is nonblank; tuples/codes match arcade intent (codes 0x004B-0x0069); records clear on actor disappearance; lizard records enter candidate pipeline; reach SAT; tile-DMA generated; **true VDP VRAM contains lizard tile data** (debugger/Exodus, not Lua :gen_vdp); lizard men visibly recognizable; no hardcoded data.
Regression: Rastan controllable (walk/attack/jump/fall/scroll); full body visible; record-46 output intact; timed bat swarm still spawns; underground bat route unchanged; no duplicate Rastan; record 132 unchanged; title/story/BEST5/item/READY/Stage-1 entry OK; BG/FG/palette no regress; no new exception/reset/lock; represented count no Build-0203 collapse; SAT terminates; no WRAM sentinel/neighbor corruption; VBlank within measured budget.
USER MUST VERIFY (future implementation): first Stage-1 lizard men visibly appear in Exodus; recognizable artwork; Rastan controllable; can attack/kill a lizard; no lower-body loss; timed bat swarm still appears. (Lizard palette accuracy separately deferred unless grossly wrong.)

## Open/Closed Issues Impact
Open touched: OPEN-017 (implementation-ready lizard staging design for block 0x2C8), OPEN-024. New: NONE. Closed: NONE. Deferred: entry-0 0x3EFBE special (non-lizard code-0x017C sprite), bat palette, per-scanline clustering measurement, lizard true-VRAM (post-implementation).

## KNOWN_FINDINGS impact
**Option B** — proposed new entry KF-065 (design record): the block-0x2C8 lizard writer semantics (9 entries, d2=10/19, deterministic d2-stride, records 140..238, engine writes exactly d2/actor, invalid e0 gated to 0x3EFBE) and the selected whole-block-scratch staging design. Does not modify KF-060..064. (Proposal only; not merged by this design task unless approved.)

## STOP status
STOP triggered: NO (design complete, bounded, capacity fits). Implementation authorized only after approval → Build 0205.
