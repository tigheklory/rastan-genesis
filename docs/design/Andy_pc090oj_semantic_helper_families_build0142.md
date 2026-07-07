# Andy — PC090OJ Semantic Helper Families and First Migration Target (Design / Evidence Only)

**Author:** Andy
**Date:** 2026-07-06
**Baseline:** Build 0141 (`cebd389e8114b316881188623b41d4b71808b5738a39d2cd4a773163bc8aa04c`); recovery checkpoint `560084e` (working tree clean, branch `rastan-direct-proposal`, HEAD `560084e`).
**Scope:** Design + evidence only. **No** production source/ROM/build/tool/spec/Makefile/bookmark/branch/commit change. Arcade↔Genesis correlations from `build/rastan-direct/address_map.json`; no arithmetic. Labels **[OBS]** source-verified (`pc090oj_hooks.s`, Build 0141); **[EVID]** runtime (Build 0141 native evidence / prior profiling); **[INT]** interpretation.

> **BOTTOM LINE — SUPERSEDED by the 2026-07-06 REVISION below (Outcome A).** The original conclusion (Outcome C) correctly identified the blocker — the per-frame clear+rebuild+repack overwrites helper-published SAT state and the packed SAT slot is not a stable identity — and recommended a persistent record→slot foundation as the fix. **The owner has adopted exactly that fix as a fixed decision: retain the original PC090OJ record identity and translate it through a compact LUT to sparse, stably-owned Genesis SAT slots, threading priority through the SAT link chain (not packing).** That resolves the Outcome-C conflict. The design is now **Outcome A**: LUT + deterministic allocator + retained state + one complete converted semantic family (the workram-block sprite family `{0x41DAE, 0x41F5E, 0x45DFA}`) + compatibility path, all implementation-ready. See **§9 REVISION**. Sections 1–8 below are retained as the family census and the original blocker analysis (still valid as motivation); §9 is the governing design.

---

## 1. Producer-family census

### Table A — PC090OJ producer families [OBS `pc090oj_hooks.s`; address_map.json]

| Family | Arcade entry PCs → helper | Callers | Record offsets written | Writes / logical op | Field-local or structural | Frontend freq | Gameplay freq | Current Genesis handling |
|---|---|---|---|---|---|---|---|---|
| **F1 Bulk init / clear** | `0x03AD44`→`3ad44_dispatch`; `0x03B902`, `0x03B926`, `0x056440`, `0x059F5E`, `0x054052`, `0x03AD84` (init/clear hooks) | scene/lifecycle init, score-frame setup, priority ladder | word0/1/2/3 = 0 (clear) or fixed init tuple, over a **range** of records/slots | tens–hundreds of records as **one** bulk op | **Structural** (active-set membership) | on scene/state change (bursty) | on stage/round change | writes mirror (0 / init) + sets candidate; scan decodes each → code-zero → clears candidate |
| **F2 Frontend multi-field build** | `0x03B930` (title score objects), `0x041DAE`/`0x041F5E`/`0x045DFA` (22 workram-block sprites), `0x056114` (copy), `0x05A098` (status) | title/attract/score/status build | word0(flip/color), word1(Y), word2(code), word3(X) per object | 4 words × N objects, **one build event** | **Multi-field structural build** | **dominant frontend sprite source** (title score, status) | title-only | producers write mirror (bridge) + candidate; scan rebuilds SAT each frame |
| **F3 Score-digit field update** | `0x03B802`→`hook_score_digit_3b802` | score/HUD digit refresh | +2/+3 attr/Y byte, +4 digit code word | ~2–6 digits, byte+word each | **Field-local** (code/attr) | title/score (score is 0 in reachable frontend → low churn) | HUD score | writes mirror bytes/words + candidate; scan re-decodes digit records each frame |
| **F4 Gameplay sprite update** | `0x054810`→`hook_sprite_update_54810` | main gameplay sprite processor | Y (from workram scroll+ROM), X, code, per object | position+code+attr, 1 record × N objects/frame | **Field-local + combined** | **not exercised** (0 producer writes in stable frontend) [EVID] | **dominant per-frame gameplay producer** | writes mirror + candidate; scan re-decodes every frame |
| **F5 Sprite decay** | `0x05607C`→`hook_sprite_decay_5607c` | timed sprite decay | Y −1, tile→0 at threshold | position + conditional code-clear | **Field-local** | rare | gameplay effects | reads descriptor, decrements, emits |
| **F6 Control state** | `ctrl_set_0/1`, `sprite_ctrl_write/clear` | screen-flip / sprite-ctrl | shadow words (`pc090oj_ctrl_shadow`, `pc090oj_sprite_ctrl_shadow`) | 1 register word | Global state | init/flip | flip | shadow captured; consumed by scan colbank/global-flip |

**Logical-operation vs raw-write note:** F1/F2 are single **bulk/build** logical operations that touch many records; F3/F4/F5 are per-object field operations. Frontend evidence [EVID Build 0141]: stable frames have **0 producer writes** yet the scan re-decodes ~42 candidates and rebuilds 23–32 SAT entries + links **every frame** — the dominant waste is per-frame **rediscovery of unchanged state**, not producer activity. Gameplay per-frame producer activity (F4/F5) is **not measurable** without the unresolved Stage-1 replay.

---

## 2. Semantic helper contracts

### Table B — Helper contracts (target design)

| Helper | Preserved mirror writes | Published semantic data | Persistent state touched | VBlank work | Build 0141 worklist interaction | Structural effect |
|---|---|---|---|---|---|---|
| `pc090oj_update_code` (F3-shape) | digit/code word + attr byte at record (readback intact) | record index, new code, new attr | record→slot map (read) | patch SAT word2 of mapped slot; no repack | **append worklist iff new code ≠ resident[slot]** | none |
| `pc090oj_update_position` (F4-shape, field part) | Y/X words at record | record index, new Y/X | record→slot map (read) | patch SAT word0/word3 of mapped slot | none (position ≠ pattern) | none |
| `pc090oj_update_attributes` | word0 (flip/color) | record index, attr/palette/flip | record→slot map | patch SAT word2 palette/flip bits | none | none |
| `pc090oj_activate_object` (F1/F2/F4) | full record init | record index, initial fields | active-set + record→slot map + slot ownership | insert into packed set, assign slot, link-heal predecessor | append worklist for the new code | **membership +1, bounded relink** |
| `pc090oj_deactivate_object` | code→0 (or Y sentinel) | record index | active-set + map | remove slot, predecessor-link→successor, terminator | none (slot freed; residency stale-but-unreachable) | **membership −1, bounded relink** |
| `pc090oj_bulk_initialize` / `_clear` (F1) | range init/clear (readback) | record range + per-record init tuple (or clear) | active-set + map (range) | **one** bounded repack of the range from the maintained set | append worklist for changed codes only | **bulk membership event** |

**Every helper (target) must:** (1) do the exact arcade mirror write(s); (2) preserve ordering/side effects; (3) publish only that op's Genesis work; (4) not scan unrelated records; (5) not diff desired-vs-committed contents; (6) introduce no one-frame latency; (7) preserve packed SAT ordering; (8) feed the Build 0141 worklist only when a pattern code changes. **Field-local helpers patch one mapped slot; structural helpers do a bounded relink from the maintained active set — never a 256-record rediscovery.**

**The blocking prerequisite (see §3/§7):** every helper in Table B reads or writes a **record→SAT-slot map** and a **persistent decoded active-set** that do not exist today, and its SAT patch would be **erased** by the next frame's `clear_generated` + rebuild.

---

## 3. Incremental migration analysis — and why it is blocked

To migrate family X while unconverted producers continue, the design must prove nine properties (task §3). Testing them against the **current** Build 0141 structure:

- *Converted ops not re-processed by the generic scan* — **FAILS today.** The scan iterates the candidate bitset over 256 records and **rebuilds every drawable's SAT slot from the mirror each frame.** A converted record that a helper published would be **re-decoded and its SAT re-emitted** (or, if excluded from the scan, its slot would be **wiped by `clear_generated` and never rebuilt**). There is no per-record "already-owned-by-helper, skip" state.
- *Helper publication cannot be lost between main loop and VBlank* — **FAILS for SAT.** Any SAT/descriptor a helper writes in the main loop is unconditionally **cleared** by `.Lvcs_clear_generated_sprite_state` at the top of the next VBlank scan. (Only the **residency cache** survives — that is why Build 0141's worklist model works and is the template.)
- *Structural events update slot ownership safely* — **no ownership state exists.** SAT slot = `emitted_count` **packing order** (dynamic), not a stable record identity [OBS + Phase-1 §11a]. Two sources (helper-owned + scan-packed) cannot share one packed SAT without a record→slot map and a merge/relink rule.
- *Field-only events do not force a 256-scan* — **FAILS.** A field change to one record still triggers the full per-frame scan (it runs unconditionally for all candidates).

**Minimal persistent state that the semantic model requires (task §3 list), justified:**
- **Persistent decoded active-set** — so VBlank applies changes instead of rebuilding (removes per-frame rediscovery). *Required — this is the core.*
- **record→SAT-slot map** + **SAT-slot→record ownership** — so field-local helpers patch the right slot and structural helpers relink; makes the SAT slot a stable identity. *Required.*
- **structural-dirty flag / field-pending list** — so a stable frame with no ops does **no** VBlank sprite work. *Required.*
- Build 0141 **residency cache + worklist** — *already persistent; reused unchanged.*

**Conclusion:** none of these exist, and the per-frame clear+rebuild+repack actively overwrites them. Therefore incremental semantic helpers cannot be added on top of the current structure — **the structure must change first** (Outcome C).

### Table C — Migration impact (per family, against current structure)

| Family | Current rediscovery work | Work removed when migrated | Work that remains | Implementation risk | Validation method |
|---|---|---|---|---|---|
| F4 gameplay update | per-frame decode+emit+relink of every moving object, every frame | field patch replaces full re-decode/re-emit of that object | scan for unconverted records until all migrate | **High** (field+structural mix; needs persistent SAT + map) | **blocked — needs Stage-1 replay** |
| F3 score digit | per-frame re-decode of digit records | direct code-field patch + worklist | scan for other records | Medium (needs persistent SAT for digit slots) | frontend (but score static → low signal) |
| F2 frontend build | **per-frame re-decode+re-emit+relink of static title sprites (0 changes)** | one-time build → stable frames do ~0 sprite work | scan for unconverted | Medium-High (multi-record build + persistence) | **frontend (highest signal)** |
| F1 bulk init/clear | per-record candidate-set + code-zero decode | one bulk membership op | scan for others | High (structural, ranges) | frontend (scene change) |
| F5 decay | per-frame re-decode | field patch | scan | Medium | gameplay-blocked |

**Every row's "work removed" is gated on the persistent decoded-SAT + record→slot foundation.**

---

## 4. Field-local vs structural

- **Field-local** (position, code, attributes, palette/flip): do **not** change membership or packed ordering. *Target:* patch the single mapped SAT slot (word0/2/3) + append worklist iff code changed. *Requires:* record→slot map + persistent SAT. **Cannot be done today** (SAT is rebuilt/wiped).
- **Structural** (activation, deactivation, ordering, bulk init): change membership/packing/links/ownership. *Target:* update the maintained active-set + a **bounded relink from that set** (predecessor→successor link-heal on deactivation; insert+assign+link on activation) — never a 256-record membership rediscovery. *Requires:* the active-set + map + ownership state. **Cannot be done today** (no maintained set; packing is dynamic).

The current model conflates both into one per-frame rebuild — which is exactly the dependency to remove.

---

## 5. First-implementation-family selection

### Table D — Build 0142 selection

| Candidate family | Evidence strength | Expected payoff | Risk | Selected / deferred + reason |
|---|---|---|---|---|
| F4 gameplay update (`0x54810`) | source PROVEN; runtime **not measurable frontend** | **highest per-frame** | High | **DEFER** — validation requires the unresolved original-arcade Stage-1 replay (Phase-1 open dependency); cannot be responsibly validated now |
| F2 frontend build (`0x3B930`/`41DAE`/…) | source PROVEN; frontend runtime PROVEN [EVID] | **high (kills per-frame rescan of static title sprites)** | Med-High | **DEFER as a family** — its payoff *is* the persistent-SAT foundation; converting the producers only pays off once the SAT is persistent |
| F3 score digit (`0x3B802`) | source PROVEN | Low (score static in reachable frontend) | Medium | **DEFER** — low signal; still needs the foundation |
| F1 bulk init/clear | source PROVEN | Medium | High (structural ranges) | **DEFER** — structural; needs the foundation |
| F5 decay (`0x5607C`) | source PROVEN | Low | Medium | **DEFER** — gameplay-blocked |
| **Persistent decoded-SAT + record→slot foundation** | derived from Build 0141 evidence | **enables all families; kills per-frame rebuild in stable frames** | Medium | **RECOMMENDED first Build 0142 step (not a producer family)** |

**No producer family can be selected as an implementation-ready single Build 0142 conversion,** because each is blocked by the persistent-SAT foundation (all) and/or the Stage-1 replay (F4/F5). The responsible first step is the **foundation** itself.

---

## 6. Expected payoff of the recommended first step (foundation)

Making the decoded SAT + record→slot map **persistent** and converting VBlank to **apply-pending** (with a bounded rebuild-from-maintained-active-set only on a structural-dirty signal):
- **Stable frontend frames (0 producer writes) [EVID]:** eliminate the per-frame candidate traversal (~31.6k cyc pre-DISPLAY_OFF), decode (~12.6k), and link rebuild (~12.8k) — i.e. the ~77k pre-DISPLAY_OFF sprite cost drops toward the cost of "no pending ops." (Estimates from prior profiling; **no exact cycle claim without measurement.**)
- **Build 0141 DISPLAY_OFF worklist:** unchanged (already ~1426 cyc stable [EVID]); the foundation targets the **pre-DISPLAY_OFF** rebuild, not the DISPLAY_OFF window.
- **On change frames:** cost proportional to the number of changed records (apply-pending), not 256.
- The payoff comes from **removing per-frame rediscovery/rebuild of unchanged state** (the directive's exact goal), not from speeding up the scan.

---

## 7. Exact Build 0142 boundary (recommended foundation — since no family is migratable yet)

**Smallest permanent step that unblocks semantic helpers, frontend-validatable, no producer-family conversion yet:**
- **Persistent state added (WRAM):** `pc090oj_active_records[]` (maintained active-record list), `pc090oj_record_to_slot[256]` (record→SAT-slot map), `pc090oj_slot_to_record[80]` (ownership), `pc090oj_structural_dirty` (word). Est. ~256·2 + 80·2 + 512 + 2 ≈ **~1.2 KB** (final sizes TBD). Reuse Build 0141 residency + worklist unchanged.
- **VBlank change:** replace unconditional `clear_generated` + full rebuild with: if `structural_dirty` OR any candidate set → decode only the touched (candidate) records and **apply** into the persistent SAT + map (insert/patch/remove + bounded relink); else **skip** (stable frame → no rebuild). `.Lvcs_link_chain_build` runs only on structural change, from the maintained active set. SAT DMA + Build 0141 worklist **unchanged**.
- **Producers:** **unchanged** in this step (still write mirror + candidate). The scan becomes the transitional populator of the persistent state; helper families migrate in **later** builds by publishing directly into the persistent state and clearing their candidate contribution.
- **Obsolete work removed immediately:** the per-frame `clear_generated` full wipe + full re-decode + full relink in stable frames.
- **Work that must remain:** the candidate-driven decode for changed records; the mirror (readback); Build 0141 worklist.
- **Interaction with Build 0141 worklist:** worklist remains the **only** sprite-pattern-DMA publication path; the apply-pending path feeds it exactly as the scan does today (residency compare on changed records).
- **Files expected to change (later, not now):** `apps/rastan-direct/src/pc090oj_hooks.s` only.
- **Runtime evidence required:** frontend native capture proving stable frames do **0** decode/relink (only apply-pending no-op), SAT byte-identical to Build 0141 (parity), active/link/ordering unchanged, worklist behavior unchanged, no crash; pre-DISPLAY_OFF cycle reduction measured via the `-debugger qt` + `totalcycles` harness.
- **User-visible expectation:** identical sprites; possibly a smaller pre-DISPLAY_OFF VBlank cost (not the black-strip DISPLAY_OFF window, which Build 0141 already addressed).

**Excluded (per task):** PC080SN, palette/score/position fixes, stray-sprite debug, generic scan micro-opt, generic table-clear opt, complete rewrite, one-frame pipeline, committed-shadow.

**After the foundation:** the **first producer FAMILY** to migrate is **F4 gameplay sprite update (`0x54810`)** — highest per-frame payoff, cleanly field-local+structural — **once (a) the foundation exists and (b) the original-arcade Stage-1 replay/save-state is available** to validate it. The frontend build family (F2) can validate the foundation itself.

---

## 8. Outcome (ORIGINAL — superseded by §9)

**Outcome C (original) — the current producer structure cannot support incremental semantic helpers without first changing a named architectural dependency.** *(Retained for the blocker analysis; the owner's LUT decision in §9 makes the change, moving the design to Outcome A.)*
- **Exact conflict:** the per-frame `.Lvcs_clear_generated_sprite_state` wipe + `.Lvcs_mirror_scan` full rebuild-from-mirror + `.Lvcs_link_chain_build` emission-order repack (a) overwrite any helper-published SAT/descriptor state every frame and (b) make the SAT slot a dynamic packing-derived identity with no stable record→slot ownership.
- **Proven behavior making a family conversion unsafe:** [OBS] `clear_generated` unconditionally zeroes the 80-SAT + 80-descriptor tables each VBlank; the scan re-emits packed order from `emitted_count`; [EVID] stable frontend frames rebuild 23–32 SAT entries with **0 producer writes** — a converted family's published state would be erased and/or double-processed, and could not coexist with packed scan output.
- **Safer permanent direction:** introduce the **persistent decoded active-set + record→SAT-slot map** (extending Build 0141's persistent-residency pattern to the SAT) and convert VBlank from "rebuild every frame" to "apply pending semantic operations, bounded rebuild-from-maintained-set on structural change." This is the recommended Build 0142 step (§7). Only then can producer families (F4 first, gameplay-replay permitting; F2 to validate the foundation) migrate to semantic helpers without double-processing or lost publication.

## Next implementation task (recommended)
**Build 0142 — PC090OJ persistent decoded-SAT + record→slot foundation** (apply-pending VBlank; producers unchanged; frontend-validated SAT parity + pre-DISPLAY_OFF cycle reduction). This is the enabling foundation, **not** a producer-family conversion. The first family conversion (F4 `0x54810`) follows in a later build after the foundation and the Stage-1 replay dependency are both resolved.

**Confirmation:** no production source, ROM, build output, tool, spec, Makefile, bookmark, branch, commit, or pipeline change was made — one design document and one AGENTS_LOG entry only (no evidence files were needed beyond existing traces).

---

# 9. REVISION (2026-07-06): Retained Identity + LUT — Governing Design (Outcome A)

The owner fixes the architecture: **retain the original PC090OJ record index (0..255) as sprite identity; translate it through a compact LUT to a sparse, stably-owned Genesis SAT slot; thread PC090OJ priority through the SAT link chain rather than by packing.** This is the persistent record→slot foundation §3/§7 required, and it is delivered **together with one complete converted semantic family** in Build 0142.

> **SUPERSEDED FOR STATE + ALGORITHMS by §9-C (2026-07-07 FINAL CORRECTION).** The retained-identity decision and the selected family `{0x041DAE, 0x041F5E, 0x045DFA}` stand, but the *state model and algorithms* below (§9.2 `active_sorted`, `structural_dirty`, full relink, word-wide `slot_to_record`, maintained high-water mark) are **replaced** by the lean record-driven bitmap + local-link-splice model in **§9-C**. Read §9-C as governing; §9.1/§9.7–9.12/§9.14–9.17 concepts carry over as refined in §9-C.

## 9.1 LUT layout and byte cost [design]
```
record_to_slot[256]   .space 256   ; byte per PC090OJ record: 0x00..0x4F = owned SAT slot; 0xFF = no slot
slot_to_record[80]    .space 80    ; byte per SAT slot: owning PC090OJ record (0..255... but 256 needs a word)
```
- **Empty/unassigned encoding:** `record_to_slot[N] = 0xFF` ⇒ record N has no SAT slot. `slot_to_record[S] = 0xFF` ⇒ slot S free. (0xFF is a valid sentinel: records 0..255 are valid indices, but a slot only ever owns a *renderable* record; 0xFF marks free. For record indices, `slot_to_record` must hold 0..255 → **use a word per slot** (`80·2 = 160 B`) to represent record indices up to 255 plus the 0xFFFF free sentinel.)
- **Byte cost (corrected):** `record_to_slot[256]` = 256 B + `slot_to_record[80]` word-wide = 160 B = **416 B** (the nominal 336 B assumed a byte-wide reverse map; record indices 0..255 need a word-wide reverse map — this is the one refinement to the owner's 336 B figure; if a byte reverse map is required, restrict it to 0..254 with 0xFF free, losing record 255 — not recommended). **Recommended: 416 B.**

## 9.2 Additional persistent state (minimum) [design]
| Symbol | Size | Purpose |
|---|---:|---|
| `pc090oj_active_sorted[80]` (word) | 160 B | active records **sorted by index (priority)** — the link-chain source; insert/remove on structural events (bounded ≤80) |
| `pc090oj_active_count` (word) | 2 B | length of the sorted active list |
| `pc090oj_free_slot_stack[80]` (byte) + top (word) | 82 B | O(1) slot alloc/free (push freed, pop lowest at boot) |
| `pc090oj_structural_dirty` (byte) | 1 B | set on any activate/deactivate/priority change → VBlank relinks; clear = stable |
| `pc090oj_sat_dirty` (byte) | 1 B | set on any SAT patch → VBlank issues SAT DMA; clear = skip DMA |
| `pc090oj_max_used_slot` (byte) | 1 B | highest allocated slot → SAT DMA length bound |
| reuse Build 0141 `sprite_tile_resident_code` + worklist | — | unchanged |
**Total new WRAM:** 416 (LUT) + ~247 (above) ≈ **~663 B**. Justified per-item by a proven semantic need (§3 list); no convenience tables.

## 9.3 Free-slot management [9.3]
Boot: push slots 79..0 onto `free_slot_stack` (so pop yields lowest first) OR pop lowest via the stack ordering; `record_to_slot[*]=0xFF`, `slot_to_record[*]=0xFFFF`, `active_count=0`, `max_used_slot=0`. **Alloc** = pop (lowest-numbered free) → keeps slots dense (SAT-DMA-friendly). **Free** = push. O(1), no scanning.

## 9.4 Active-record + priority representation [9.4]
Priority = ascending PC090OJ record index (record 0 = highest priority). `pc090oj_active_sorted[]` holds active record indices in ascending order. Activation inserts (bounded shift ≤80); deactivation removes. The **SAT link chain** is rebuilt from this list on `structural_dirty` (§9.5), so a record's SLOT is independent of its priority position.

## 9.5 SAT link maintenance [9.5]
Sparse slots + link chain (NOT packing). On `structural_dirty`: walk `pc090oj_active_sorted[0..active_count-1]`; for each active record i, `slot_i = record_to_slot[rec_i]`; set `staged_sprite_sat[slot_i].word1 = 0x0500 | slot_{i+1}` (link to the NEXT active record's slot, in priority order); last active slot link = 0 (terminator); chain **starts at `slot_0`** — write the SAT start index (the link register / first-slot) so the VDP begins at the highest-priority record's slot. Bounded by `active_count` (≤80), **never 256**. Field-only updates do **not** relink.

## 9.6 Stable slots sparse? [9.6] YES.
Slots are stably owned; priority is carried by links, not slot order. **Ordinary field updates keep the same slot** (no reshuffle, no relink). This is the explicit preference (task: stable ownership + link changes over shifting later sprites). Genesis SAT permits sparse chains (link jumps to any slot 0..79), so no packing is required. **SAT DMA length = `(max_used_slot+1)*4`** (lowest-free alloc keeps this ≈ `active_count*4`; worst-case fragmentation → up to 320 words = the pre-0137 full SAT, still correct).

## 9.7 Activation [9.7]
`apply_object(record, word0, Y, code, X)` decodes renderability using the **existing scan predicates** (code-zero, blank-bitset, unmapped ≥0x1000, offscreen Y/X bounds, global-flip) — not invented rules. If renderable and `record_to_slot[record]==0xFF`: pop a free slot; set `record_to_slot`/`slot_to_record`; insert record into `active_sorted`; `structural_dirty=1`; write the SAT entry (Y/attr/tile-from-slot/X per emit_slot); append the Build 0141 worklist iff `(code&0xFFF) != resident[slot]`; `sat_dirty=1`; update `max_used_slot`.

## 9.8 Deactivation [9.8]
If the decode is **non-renderable** (code-zero / blank / unmapped / offscreen) and the record currently owns a slot: clear `record_to_slot`/`slot_to_record`; push the slot free; remove record from `active_sorted`; `structural_dirty=1`. The freed slot is unlinked (unreachable) and set Y-offscreen so any residual DMA of it is invisible. **No eviction based on elapsed frames** — only on a proven non-renderable decode or explicit clear.

## 9.9 Offscreen / non-renderable [9.9]
Reuse the **proven** scan predicates verbatim: code `&0x1FFF == 0` (code-zero), blank-code bitset, code `≥0x1000` (unmapped), Y/X out of `[-16,320)`/`[-16,224)` after global-flip. Established note: leading-zero score digits are made non-renderable by the arcade via the **Y high byte** (Y≥256 → offscreen) [OBS `hook_score_digit_3b802` visflag]; this is the same offscreen predicate, not a coordinate invention. A record failing any predicate ⇒ deactivate (§9.8).

## 9.10 Overflow > 80 eligible [9.10]
Deterministic by priority: on activation with an empty free stack, compare the new record's index to `active_sorted[active_count-1]` (the lowest-priority = highest-index active). If `new_index < that` (higher priority): deactivate the lowest-priority record (free its slot, remove from list) and assign it to the new record; else **drop** the new activation (record retains arcade mirror state but gets no slot — matching the current `dropped_count` 80-cap semantics). Deterministic, priority-ordered, no per-frame 256-scan.

## 9.11 Residency / Build 0141 worklist [9.11]
Unchanged Build 0141 model. Any activation or code-changing field update appends `{slot, code}` to the worklist iff `(code&0xFFF) != sprite_tile_resident_code[slot]`; the DISPLAY_OFF worklist commit + post-DMA residency update are **unchanged**. Slot reuse (freed slot reassigned to a different record/code) self-corrects: the new code ≠ resident[slot] ⇒ worklist append ⇒ re-DMA (exactly the Build 0141 slot-keyed behavior). **The worklist remains the only sprite-pattern-DMA publication path.**

## 9.12 Interrupt safety [9.12]
Helpers run in the main loop (producers); VBlank consumes. Each helper operation (field patch of an SAT entry, or a structural alloc/free + list edit + `structural_dirty` set) executes in a **short VINT-masked critical section** (save SR, `ori #0x0700,sr`, mutate, restore) — as in the Build 0141 worklist append — so VBlank never observes a half-patched SAT entry, a torn LUT/list, or a `structural_dirty` set without its list edit. VBlank (already IRQ context) snapshots and applies. Repeated field updates to the same record simply overwrite the same SAT entry (natural last-write coalescing; no queue). A producer preempted before its critical section defers that op to the next frame (matching the existing frame boundary; no extra latency).

## 9.13 Minimum additional state beyond the LUT
Per §9.2: sorted active list (160), active_count (2), free stack (82), structural_dirty/sat_dirty/max_used_slot (3). ~247 B. No decoded-per-record cache beyond the SAT itself (the SAT *is* the persistent decoded state); no field-pending queue (direct patch + coalesce).

## 9.14 Selected Build 0142 family
**The workram-block sprite family: `{arcade 0x041DAE, 0x041F5E, 0x045DFA}`** — all three route through the identical shared helper `.Lpc090oj_emit_slots_0_21_from_workram` (emit 22 objects from work-RAM at `A5+0x11B2` (18) and `A5+0x0170` (4)). **Statically proven equivalent** (same operation, same helper, records 0..21). Frontend-exercised (contributes to the reachable ~23-active title/attract set [EVID]); validatable on the frontend without the Stage-1 replay. **Rationale:** the cleanest *proven-equivalent, complete, single-operation* family, exercising the full mechanism (activation, alloc, priority link, retained identity, LUT, worklist, offscreen). It is preferred over: F4 gameplay `0x54810` (higher per-frame value but validation needs the unresolved Stage-1 replay → SAT parity is a *frontend* check, which F4 records cannot satisfy); F2's mixed builders `0x3B930`/`0x5A098`/`0x56114` (not *identical* operations → not one equivalent family); F1 bulk-clear (structural range, higher risk); F3 `0x3B802` digits (single producer but score is largely static → weak per-op signal).

## 9.15 Every equivalent producer in the family
`0x041DAE`, `0x041F5E`, `0x045DFA` → all call `.Lpc090oj_emit_slots_0_21_from_workram`. Build 0142 converts that shared helper to call `pc090oj_apply_object(record=0..21, word0, Y, code, X)` for each of the 22 objects (records 0..21), and to **not** set the legacy dirty-candidate for records 0..21 (so the transitional scan skips them). Any future producer proven to emit the same workram-block objects routes through the same helper.

## 9.16 Exact generic work removed after this family is converted
- Records 0..21's per-change **decode + emit + residency-compare** move out of the scan into the direct helper (no double-processing — candidate suppressed for 0..21).
- Combined with the foundation (candidate = "dirty since last VBlank", cleared each scan; persistent SAT; apply-pending): **stable frames (no producer writes, no structural change) do 0 scan / 0 decode / 0 relink / 0 SAT wipe** — only a gated SAT DMA (skippable if `sat_dirty` clear). The prior per-frame rediscovery of the ~42 active candidates (candidate traversal ~31.6k + decode ~12.6k + relink ~12.8k pre-DISPLAY_OFF [EVID prior profiling]) is eliminated in stable frames.
- Build 0141 DISPLAY_OFF worklist commit is unchanged (~1426 cyc stable).
- *No exact cycle reduction claimed without measurement (validation §9.18).*

## 9.17 Compatibility path (no two renderers) [9.17]
One renderer: the persistent LUT + SAT. Two **input** paths into it: (a) converted helpers (`apply_object`, records 0..21) — direct; (b) the transitional scan — for unconverted records that set the dirty-candidate. **Double-processing prevention:** the converted helper does **not** set the dirty-candidate for records 0..21 (and clears any stale bit), so the scan's candidate walk never re-decodes them; `record_to_slot`/`slot_to_record` are the single ownership source both paths honor. Proof obligation for implementation: assert no candidate bit is ever set for records 0..21 by the converted path, and the scan's decode count excludes 0..21.

## 9.18 Validation plan (later implementation must prove)
Frontend native capture (`-debugger qt` + `totalcycles` harness, Build 0141 method): correct `record_to_slot`/`slot_to_record` ownership and reverse-consistency for records 0..21; stable ownership across ordinary field/code/attr updates (same slot); **zero scan-decode of records 0..21** (no legacy double-processing); SAT link chain in exact ascending-record (priority) order; **no eviction by elapsed frames** (only proven non-renderable/clear); correct slot release + reuse (freed slot reassigned, residency re-DMAs); **SAT byte-identical to Build 0141 in equivalent frontend states** (0/1/0, 0/1/2, 2/2/6); **no full scan/wipe/decode/relink on stable no-work frames** (structural_dirty clear ⇒ 0 relink; 0 dirty-candidates ⇒ 0 decode); Build 0141 tile-DMA/worklist behavior unchanged; no crash; pre-DISPLAY_OFF cycle reduction measured.

## 9.19 Exact Build 0142 implementation boundary
- **Files:** `apps/rastan-direct/src/pc090oj_hooks.s` only.
- **Add:** the LUT (`record_to_slot[256]`, `slot_to_record[80]` word) + §9.2 state; `pc090oj_apply_object` (decode via existing predicates → activate/deactivate/field-patch via LUT + allocator + link, VINT-masked); free-slot stack + sorted-active-list primitives.
- **Convert:** `.Lpc090oj_emit_slots_0_21_from_workram` (the shared helper of `0x41DAE/0x41F5E/0x45DFA`) to call `pc090oj_apply_object` for records 0..21 and suppress their dirty-candidate.
- **Foundation change:** VBlank sprite path: make the candidate a **per-frame dirty** bit (cleared each scan, re-set by unconverted producers on write); replace `clear_generated` full wipe + full rebuild with **apply-pending into the persistent SAT** (decode only dirty candidates; activate/patch/deactivate via the LUT/allocator); relink only on `structural_dirty` from `active_sorted`; SAT DMA gated by `sat_dirty`, length `(max_used_slot+1)*4`.
- **Preserve:** arcade mirror writes + order (readback intact); Build 0141 residency + worklist + DISPLAY_OFF commit; sprite priority via links; no one-frame latency; no committed-shadow; no packing.
- **Removable immediately:** per-frame `clear_generated` full wipe + full re-decode/relink in stable frames; the 80-slot rebuild.
- **Must remain until later families migrate:** the transitional scan-apply for unconverted records (F1/F2-rest/F3/F4/F5).
- **WRAM cost:** ~663 B (416 LUT + ~247 state).
- **Excluded (per task):** PC080SN, palette/score/position fixes, stray-sprite debug, generic scan micro-opt, generic table-clear opt, complete rewrite, one-frame pipeline, committed-shadow.

## 9.20 Outcome A
**The LUT, deterministic allocator, retained state, one complete converted semantic family (`{0x041DAE, 0x041F5E, 0x045DFA}` via the shared `emit_slots_0_21` helper → `pc090oj_apply_object`), the compatibility path, and the Build 0142 boundary are implementation-ready.** One refinement to the owner's figure: the reverse map `slot_to_record` needs word width (record indices 0..255), making the LUT **416 B** (not 336 B) — otherwise the design adopts the retained-identity + LUT + sparse-slot + link-priority model exactly as directed. Higher-value families (F4 gameplay `0x54810`) follow once the frontend-proven foundation lands and the Stage-1 replay dependency is resolved.

**Confirmation:** no production source, ROM, build output, tool, spec, Makefile, bookmark, branch, commit, or pipeline change was made — this is a design amendment only.

---

# 9-C. FINAL CORRECTION (2026-07-07): Lean record-driven bitmap + local SAT splicing — GOVERNING

Retained identity + LUT + family `{0x041DAE, 0x041F5E, 0x045DFA}` stand. The state model and algorithms are replaced by this lean form: **`record_to_slot` forward LUT + three bitmaps + bounded bit-scans for priority ordering + local link splicing.** No `slot_to_record`, no `active_sorted`, no `structural_dirty`, no maintained high-water mark.

> **CORRECTED by §9-D (2026-07-07 FINAL SYNC CORRECTION).** §9-C's verbatim 8-byte head-move copy, the "records 0..21 never enter the candidate path" claim, `BFFFO`, the empty-chain DMA, and worklist cancellation are **fixed in §9-D**, which governs for those six points.

## 9-C.1 Final state layout and byte cost
| Symbol | Size | Justification |
|---|---:|---|
| `record_to_slot[256]` (byte) | **256 B** | 0x00..0x4F = owned SAT slot; **0xFF = unrepresented**. The single forward ownership map. |
| `represented_records` (256-bit) | **32 B** | bit r set ⇒ record r owns a slot. Source of prev/next/head/tail via bounded bit-scan. |
| `waiting_records` (256-bit) | **32 B** | bit r set ⇒ record r is eligible (renderable in mirror) but has no slot (overflow). |
| `used_sat_slots` (80-bit) | **10 B** | bit s set ⇒ slot s occupied. Free-slot alloc + highest-used computed from here. |
| `worklist_entry_for_slot[80]` (byte) | **80 B** | 0xFF = none; else index of this slot's single pending Build 0141 worklist entry (coalescing). |
| `pc090oj_represented_count` (word), `sat_dirty` (byte) | **~3 B** | chain length hint + SAT-DMA gate. |
| *(reuse)* Build 0141 `sprite_tile_resident_code` + tile-DMA worklist + count | — | unchanged. |
| **Total new** | **~413 B** | — |
**Dropped and why unnecessary:** `slot_to_record` — every operation is keyed by *record* (forward LUT) or scans `represented_records`/`used_sat_slots`; no operation needs slot→record (deletion frees `record_to_slot[R]`; predecessor found by bit-scan; promotion picks lowest-index waiting bit; eviction picks highest-index represented bit; SAT DMA length from `used_sat_slots`). `active_sorted`/`structural_dirty` — replaced by bit-scan ordering + per-op local splice. High-water mark — computed from `used_sat_slots` on `sat_dirty` frames (no stale state).

**Bounded bit-scan helpers** (over the 32-byte bitmaps, `bfffo`/byte loop): `next_rep(r)` = first set > r; `prev_rep(r)` = last set < r; `head` = first set (lowest index = highest priority); `tail` = last set (lowest priority); `lowest_free_nonzero` = first clear in `used_sat_slots[1..79]`; `highest_used` = last set in `used_sat_slots`. All bounded ≤256/80, invoked only on structural ops (not per frame).

## 9-C.2 Slot-0 / head invariant and algorithms
**Invariant:** if any record is represented, the head (lowest-index represented record) **owns slot 0** (the VDP always starts the chain at slot 0). All other represented records own **sparse nonzero** slots, stably.

- **First activation (chain empty):** assign the record **slot 0**; `record_to_slot[R]=0`; set `represented`/`used_sat_slots` bit 0; write SAT[0]; link = 0 (terminator).
- **Ordinary insertion (R is not the new head; P=prev_rep(R) exists, S=next_rep(R) may exist):** alloc `s = lowest_free_nonzero`; `record_to_slot[R]=s`; set bits; write SAT[s]; `SAT[s].link = S? record_to_slot[S] : 0`; `SAT[record_to_slot[P]].link = s`. **Local:** predecessor link + inserted slot only.
- **Ordinary deletion (R not head; P=prev_rep, S=next_rep):** `SAT[record_to_slot[P]].link = S? record_to_slot[S] : 0`; free `record_to_slot[R]` (clear bits); `record_to_slot[R]=0xFF`. **Local:** predecessor link + freed slot only.
- **New record R becomes the priority head (R < current head H):** alloc `s_H = lowest_free_nonzero`; **copy** H's 8-byte SAT entry slot 0 → `s_H`; `record_to_slot[H]=s_H` (its link unchanged — still points to H's old successor); place R at **slot 0** (`record_to_slot[R]=0`); write SAT[0]=R; `SAT[0].link = s_H`. Nothing pointed to the head, so no other link changes. **Moves:** slot 0 ← R, one nonzero slot ← old head.
- **Deletion of the current head H (slot 0):** `H' = next_rep(H)` (new head). If none: clear slot 0, chain empty. Else: **copy** H' entry from `record_to_slot[H']` → slot 0; `record_to_slot[H']=0`; free H''s old slot; `SAT[0].link` = H''s old link (unchanged, points to its successor). Old head pointed to H', now H' *is* slot 0, so no other link changes. **Moves:** slot 0 ← new head, free its old slot.
- **Head replacement while all 80 occupied (R < head, `used_sat_slots` full):** first evict the tail `L = tail()` → `waiting`, free `record_to_slot[L]`, fix `SAT[record_to_slot[prev_rep(L)]].link = 0` (new terminator); then run **new-head** (old head → the just-freed nonzero slot, R → slot 0). Bounded (evict + head move).

## 9-C.3 Local SAT link splicing — ascending-priority proof
For represented records `r0<r1<…<rk`: `SAT[slot(r0)=0].link=slot(r1)`, `SAT[slot(ri)].link=slot(r{i+1})`, `SAT[slot(rk)].link=0`. Traversal from slot 0 visits `r0,r1,…,rk` in **ascending record index = ascending PC090OJ priority**. Insertion (P→R→S with P<R<S) rewrites only `SAT[slot(P)].link` and `SAT[slot(R)]`; deletion rewrites only `SAT[slot(P)].link`; head ops move ≤2 slots with no third-party link fix (nothing points to the head). **Every ordinary op is O(1) links + one bit-scan for P/S; the full chain is never rebuilt.** Priority order is preserved by construction after each op.

## 9-C.4 Overflow / waiting / promotion
- **Activate R, all 80 used:** if `R < tail()` (higher priority): evict tail L → set `waiting[L]`, free its slot (splice out), then represent R (§9-C.2, as head or ordinary). Else: set `waiting[R]` (R keeps its mirror state; no slot).
- **A slot frees (deactivation with waiting non-empty):** promote `W = first set in waiting_records` (highest priority waiting); **re-decode W from its current PC090OJ mirror state** (its retained arcade record); if still renderable, represent it (alloc/splice); clear `waiting[W]`. If W is no longer renderable, clear `waiting[W]` (it deactivated while waiting).
- **No permanent loss:** a record is dropped only into `waiting` (never forgotten); it is promoted from mirror state as soon as a slot frees or a higher-priority eviction occurs. Not evicted by elapsed frames — only by a higher-priority arrival under a full SAT.

## 9-C.5 Free-slot allocation
Slot 0 is **reserved for the current head** whenever any sprite is represented. Ordinary records get `lowest_free_nonzero` (first clear bit in `used_sat_slots[1..79]`). On `sat_dirty` frames, the **SAT-DMA length = `(highest_used + 1) * 4`** words, `highest_used` = last set bit in `used_sat_slots` (computed, not maintained). Lowest-free-nonzero allocation keeps slots dense ⇒ `highest_used ≈ represented_count` ⇒ SAT DMA ≈ `represented_count*4` (worst-case fragmentation ≤ 320 words, still correct).

## 9-C.6 Build 0141 worklist coalescing
`worklist_entry_for_slot[80]` (byte, 0xFF=none). On a code change for slot `s` where `(code&0xFFF) != resident[s]`: if `worklist_entry_for_slot[s] != 0xFF`, **overwrite** that worklist entry's code (single pending entry per slot — repeated changes converge to the final code); else append `{s, code}`, set `worklist_entry_for_slot[s] = new_index`. On worklist reset (after the DISPLAY_OFF commit consumes it), clear `worklist_entry_for_slot[*]=0xFF` and count=0. **The Build 0141 worklist remains the only sprite-pattern-DMA mechanism**; commit + post-DMA residency update are unchanged.

## 9-C.7 Complete family helper + private sync primitive
- **Public family helper** `pc090oj_workram_block_sprites` — the complete 22-object work-RAM block operation used by `0x041DAE`, `0x041F5E`, `0x045DFA` (all three call it; it reads work-RAM at `A5+0x11B2` (18) and `A5+0x0170` (4), preserving the exact mirror writes/order for records 0..21). It is the **only** exposed semantic producer interface for this family.
- **Private per-record primitive** `.Lpc090oj_sync_record(record, word0, Y, code, X)` — internal: preserve the mirror write; decode renderability via the **existing scan predicates** (code-zero/blank/unmapped/offscreen Y-X, incl. leading-zero-via-Y-high-byte); then **activate / delete / field-patch** the record via §9-C.2 splice + §9-C.6 worklist. Not exposed as a generic public helper.
- **Converted records 0..21 never enter the candidate path** — `pc090oj_workram_block_sprites` does not set (and clears any stale) dirty-candidate bit for records 0..21.

## 9-C.8 Transitional producers (one renderer)
Unconverted producers set per-record **dirty candidates** (per-frame dirty semantics: set on write, cleared each VBlank after processing). VBlank iterates only dirty records and runs each through the **same** `.Lpc090oj_sync_record` primitive, then clears its candidate bit. There is **one** persistent LUT/SAT renderer; the family helper and the transitional scan are two *inputs* to it, disjoint by record (0..21 helper-owned, others candidate-driven). Double-processing is impossible because 0..21 never set a candidate.

## 9-C.9 Global operations
A real PC090OJ global flip / control change performs **one bounded re-evaluation of the affected represented records** — iterate set bits of `represented_records` (bounded ≤80) and re-derive their flipped Y/X/attr into their existing SAT slots (no slot moves; links unchanged if membership is unchanged). Operation-driven, not a per-frame scan.

## 9-C.10 Interrupt safety
Each `.Lpc090oj_sync_record` op (mirror write + decode + splice + SAT patch + worklist coalesce) executes in a **short VINT-masked critical section** (Build 0141 precedent) so VBlank never observes a torn LUT/bitmap/SAT/worklist. Repeated field/code updates to the same record overwrite the same SAT entry and coalesce the single worklist entry (no queue). A producer preempted before its critical section defers to the next frame — no extra latency.

## 9-C.11 Validation (implementation must prove)
Frontend native capture (`-debugger qt` + `totalcycles`): slot 0 always owns the highest-priority represented record; `record_to_slot` ↔ `represented_records`/`used_sat_slots` consistency; each represented record appears **exactly once** in the SAT chain; chain priority = ascending record index; ordinary insert/delete change **only local links**; head changes move **only** slot 0 ↔ one nonzero slot; waiting records promoted correctly from mirror state; **no duplicate worklist entry per slot**; records 0..21 **never** processed by the candidate path; **stable no-work frames perform no scan/decode/relink/SAT-wipe/SAT-DMA**; sprite output byte-identical to Build 0141 in `0/1/0`, `0/1/2`, `2/2/6`; no crash.

## 9-C.12 Exact Build 0142 boundary + WRAM
- **Files:** `apps/rastan-direct/src/pc090oj_hooks.s` only.
- **Add:** `record_to_slot[256]`, `represented_records`/`waiting_records` (32 B each), `used_sat_slots` (10 B), `worklist_entry_for_slot[80]`, `represented_count`/`sat_dirty`; bounded bit-scan helpers; `.Lpc090oj_sync_record` (decode → splice → worklist); the public `pc090oj_workram_block_sprites`.
- **Convert:** `.Lpc090oj_emit_slots_0_21_from_workram` → `pc090oj_workram_block_sprites` (records 0..21; suppress their candidate).
- **Foundation:** candidate = per-frame dirty (set on write, cleared each VBlank); replace `clear_generated` full-wipe + full-rebuild with **apply-pending** — VBlank runs `.Lpc090oj_sync_record` for dirty candidates only, splices locally, SAT DMA gated by `sat_dirty` with length from `used_sat_slots`; **no full relink**.
- **Preserve:** arcade mirror writes/order; Build 0141 residency + worklist + DISPLAY_OFF commit; priority via links; no packing; no one-frame latency; no committed-shadow.
- **Removable immediately:** per-frame full SAT wipe + full re-decode + full relink in stable frames (now 0-work).
- **Remains until later families migrate:** candidate-driven `.Lpc090oj_sync_record` for unconverted records.
- **WRAM new:** **~413 B** (§9-C.1).
- **Excluded (per task):** PC080SN, palette/score/position fixes, stray-sprite debug, generic scan micro-opt, generic table-clear opt, complete rewrite, one-frame pipeline, committed-shadow.

## 9-C.13 Outcome A
The lean **record-driven bitmap + local-splice** model — `record_to_slot[256]` + `represented`/`waiting`/`used-slot` bitmaps + `worklist_entry_for_slot[80]` (**~413 B**, no `slot_to_record`/`active_sorted`/`structural_dirty`/high-water), slot-0 head invariant with bounded head/insert/delete/promotion algorithms, O(1) local link splicing with an ascending-priority proof, deterministic overflow/waiting/promotion, the single public family helper `pc090oj_workram_block_sprites` over `{0x041DAE, 0x041F5E, 0x045DFA}` with a private `.Lpc090oj_sync_record`, the one-renderer transitional path, and worklist coalescing — is **implementation-ready**. **Outcome A.**

**Confirmation:** no production source, ROM, build, tool, spec, Makefile, bookmark, branch, commit, or pipeline change was made — design amendment only.

---

# 9-D. FINAL SYNCHRONIZATION CORRECTION (2026-07-07): close six pre-implementation gaps — GOVERNING for these points

Architecture unchanged (retained identity, `record_to_slot`, represented/waiting/used-slot bitmaps, sparse stable slots, local splice, family `{0x041DAE,0x041F5E,0x045DFA}`, one renderer). The six fixes below govern.

## 9-D.1 Slot moves REGENERATE the destination — never a verbatim 8-byte copy
The SAT **tile-index field** (word2 low 11 bits = `(SPRITE_TILE_BASE + slot*4) & 0x07FF`) and Build 0141 pattern **residency** are **slot-keyed**, so a byte-copy would leave the wrong VRAM tile pointer and stale residency. Every move re-derives the destination from the moved record's **mirror** via one primitive:

`.Lpc090oj_place_record_in_slot(record, dest_slot, link)`:
1. Read the record's retained arcade state from `pc090oj_object_ram[record]` (word0/Y/code/X); decode `Y,X,attr(color/flip),code` exactly as `.Lvcs_mirror_scan`/`emit_slot` (identity + code preserved).
2. Write staged `SAT[dest_slot]`: word0=Y(+bias), word1 = `0x0500 | link`, word2 = `priority|palette|flip` **| tile-index re-derived for `dest_slot`** (`(SPRITE_TILE_BASE+dest_slot*4)&0x07FF`), word3=X(+bias).
3. **Queue the destination's pattern DMA:** if `(code&0x0FFF) != sprite_tile_resident_code[dest_slot]` → coalesce a worklist entry `{dest_slot, code}` (§9-D.4). (Post-DMA residency update stays Build 0141.)
4. `record_to_slot[record]=dest_slot`; set `represented[record]`, `used_sat_slots[dest_slot]`; `sat_dirty=1`.

`.Lpc090oj_free_slot(slot)`: clear `used_sat_slots[slot]`; **cancel** its pending worklist entry (§9-D.4); `worklist_entry_for_slot[slot]=0xFF`.

Head cases (each step VINT-masked, atomic w.r.t. VBlank):
- **New higher-priority head R (R<head H):** `s_H=lowest_free_nonzero`; `place_record_in_slot(H, s_H, H_old_link)`; `place_record_in_slot(R, 0, s_H)`. (Nothing pointed to the head, so no third-party link fix.) H's old slot **was** slot 0 → now owned by R (residency[0] re-queued for R); s_H is newly allocated → residency stale → re-queued for H (step 3). No source slot leaks a stale worklist entry.
- **Deletion of head H (slot 0):** `H'=next_rep(H)`; if none → **empty-chain** (§9-D.3); else `place_record_in_slot(H', 0, H'_old_link)`; `free_slot(H'_old_slot)`. (`H'` was pointed to only by H, now `H'` **is** slot 0 → no third-party fix.)
- **Full-SAT head replacement (R<head, all 80 used):** `L=tail()`; splice L out (`SAT[slot(prev_rep(L))].link=0` terminator or, if L had a successor, to it); `free_slot(record_to_slot[L])`; `waiting[L]=1`, `represented[L]=0`, `record_to_slot[L]=0xFF`; then run **new-head R** using the just-freed slot for H.

Ordinary (non-head) insert/delete keep every other record's slot stable and touch only the predecessor link + the one inserted/freed slot (§9-C.3 proof unchanged).

## 9-D.2 Overlap-safe candidate rules (producer-ordered, NOT a permanent 0..21 partition)
**Writer audit for records 0..21 [OBS]:** the converted family `emit_slots_0_21` (0..21) **and** unconverted `0x03B902` (clears records 0..4), `0x03B926` (5..13), `0x059F5E` (0..7), `0x03B930` (title-score records 17..21 via 0xD00088), and `0x03AD44` (bulk range, may include 0..21) all write records in 0..21. So records 0..21 are **not** exclusively family-owned — the "never enter the candidate path" claim is withdrawn.

**Ordering rule (last-writer-wins, exactly-once):**
- The converted family, when it directly synchronizes record N, **does not set** N's candidate and **atomically clears** N's candidate (its complete write now reflects the final mirror state in the SAT). Sync + candidate-clear are one VINT-masked step.
- Any unconverted producer that writes N (before or after) sets N's candidate as today (all mirror writers already do — §9-D.6).
- VBlank processes each set candidate via the shared `.Lpc090oj_sync_record`, then clears it.
- **Result:** family-then-unconverted → candidate re-set by unconverted → VBlank re-syncs N from mirror (final) → not lost. Unconverted-then-family → family syncs N (final) + clears candidate → VBlank skips N → not double-processed. Either order, the **final mirror state** is applied exactly once per net change. No pending unconverted update is lost; no converted op is redundantly processed.

## 9-D.3 Empty-chain commit
When the last represented sprite is removed (`represented_count → 0`, `used_sat_slots` empty): write staged `SAT[0]` as **hidden** (Y set fully offscreen, e.g. Y raw ≥ `224+bias`), `word1` link = 0 (terminator), other words 0; `used_sat_slots[0]` **left clear** but the commit still uploads slot 0; `sat_dirty=1`.
**SAT-DMA length rule:** `words = max(highest_used+1, 1) * 4`, where `highest_used` = last set bit in `used_sat_slots` (or −1 if empty ⇒ the `max(...,1)` yields **4 words = slot 0 only**). This is the Build 0141 `max(active,1)` guarantee generalized: **never zero-length** (which the VDP would read as 0x10000 words), and the empty case overwrites the old VDP chain start with an invisible terminating slot 0 → nothing remains visible.

## 9-D.4 Worklist cancellation / reassignment
`worklist_entry_for_slot[80]` (byte, 0xFF=none). Rules before VBlank:
- **Repeated code change for slot s:** if `worklist_entry_for_slot[s]!=0xFF`, **overwrite** that entry's code; else append `{s,code}`, set the map.
- **Slot s freed** (`free_slot`): if it has a pending entry, **cancel** it — set that worklist entry's slot field to the sentinel `0xFF` (commit skips sentinel entries) and `worklist_entry_for_slot[s]=0xFF`. No DMA remains for an unreachable free slot.
- **Slot s reassigned** (freed then allocated to a new owner): the free already canceled the old entry; the new owner's `place_record_in_slot` queues a fresh `{s, new_code}` (only if `new_code!=resident[s]`).
- **Record moves slot 0 ↔ nonzero:** the move frees the old slot (cancel its entry) and `place_record_in_slot` queues the new slot's entry — so each physical slot's single pending entry always names its **final owner's final code**.
- **Commit (DISPLAY_OFF, Build 0141) change:** the worklist loop **skips entries whose slot == 0xFF** (canceled). After commit, reset all `worklist_entry_for_slot[*]=0xFF` and count=0 with the worklist.
Guarantee: at commit every non-sentinel entry describes the final required code for its slot's final owner; no obsolete DMA to a free slot.

## 9-D.5 68000-compatible bitmap scan (no BFFFO)
`BFFFO` is 68020+ — **removed**. Base-68000 method: scan the bitmap byte-by-byte with `tst.b`/`dbra`; on the first nonzero byte, resolve the bit with an 8-step `btst`/`dbra` loop (or a 256-byte `first_set_lut`/`last_set_lut` if a later profile shows it matters — not required, scans are structural-only, not per-frame).
- `head` = forward byte scan of `represented_records` (32 B) → first nonzero byte `i` → lowest set bit `j` (btst 0..7) → record `i*8+j`.
- `tail` = backward byte scan → highest set bit.
- `next_rep(r)`: byte `r>>3`, mask bits `≤ r&7`, then forward. `prev_rep(r)`: byte `r>>3`, mask bits `≥ r&7`, then backward.
- `lowest_free_nonzero` = forward scan of `used_sat_slots` (10 B) for the first **clear** bit from bit 1.
- `highest_used` = backward scan for the last set bit.
Bounded (≤32×8 / ≤10×8), early-exit on the first non-empty byte, invoked only on structural ops.

## 9-D.6 Dirty-producer completeness audit [OBS `pc090oj_hooks.s`]
Every path that writes `pc090oj_object_ram` **currently sets the per-record candidate**:
- `.Lpc090oj_mirror_write_word_a1_d0` / `_byte` → `.Lpc090oj_candidate_set_offset_d2` (covers `0x3B930`, `0x3B802`).
- `.Lpc090oj_emit_slot` mirror bridge (`scan_active==0`) → `.Lpc090oj_candidate_set_d0` (covers `0x3B902`, `0x3B926`, `0x59F5E`, `0x3AD84`, `0x54052`, `0x54810`, `0x5607C`, `0x56114`, `0x5A098`, and today `0x41DAE/41F5E/45DFA`).
- `.Lhook_3ad44_pc090oj_long_fill_loop` → `.Lpc090oj_candidate_set_offset_d2` per word (bulk).
→ **No mirror writer bypasses candidate publication** under the current 133-site postpatch coverage. **Adaptation required:** (a) the converted family stops setting and instead clears its records' candidate (§9-D.2); (b) the bulk/clear producers (`0x3B902/0x3B926/0x59F5E/0x3AD44`) must set the candidate for **every** record they touch (they do today, per the audit) so apply-pending deactivates them — verify no clear path zeroes the mirror without a candidate set. **STOP condition:** any future or presently-unrouted raw write to `0x00D00000..0x00D007FF` that bypasses these helpers — the apply-pending model is unsafe if any mirror writer skips candidate/semantic publication; the postpatch opcode-replace coverage must keep every arcade PC090OJ write routed.

## 9-D.7 Revised exact Build 0142 boundary (supersedes §9-C.12 where it conflicts)
- **Files:** `apps/rastan-direct/src/pc090oj_hooks.s` only.
- **Add:** `record_to_slot[256]`, `represented_records`/`waiting_records` (32 B), `used_sat_slots` (10 B), `worklist_entry_for_slot[80]`, `represented_count`/`sat_dirty`; base-68000 bit-scan helpers (§9-D.5); `.Lpc090oj_place_record_in_slot` + `.Lpc090oj_free_slot` (§9-D.1); `.Lpc090oj_sync_record` (decode → activate/delete/field-patch via local splice + place/free); the public `pc090oj_workram_block_sprites`; empty-chain hidden slot 0 (§9-D.3); worklist cancel/skip-sentinel + the SAT-DMA `max(highest_used+1,1)*4` rule.
- **Convert:** `.Lpc090oj_emit_slots_0_21_from_workram` → `pc090oj_workram_block_sprites` (records 0..21; **clear**, do not set, their candidate).
- **Foundation:** candidate = per-frame dirty (set on write by unconverted producers, cleared each VBlank after `sync_record`); replace `clear_generated` full-wipe + full-rebuild + full-relink with **apply-pending local splice** over dirty records only; SAT DMA gated by `sat_dirty`, length `max(highest_used+1,1)*4`.
- **Preserve:** arcade mirror writes/order; Build 0141 residency + worklist commit + post-DMA residency; priority via links; no packing; no one-frame latency; no committed-shadow.
- **WRAM new:** **~413 B** (§9-C.1, unchanged).
- **Excluded (per task):** PC080SN, palette/score/position fixes, stray-sprite debug, generic scan micro-opt, generic table-clear opt, complete rewrite, one-frame pipeline, committed-shadow.
- **Validation adds:** head-move destinations carry the correct **re-derived tile-index** and a correctly-queued pattern DMA (no stale VRAM tile after a move); records 0..21 candidate is **cleared by the family and re-set by any unconverted writer** (ordering test); empty-chain frame uploads a hidden self-terminating slot 0 (4 words) with nothing visible; no worklist entry survives for a freed slot; all scans use base-68000 instructions; no mirror writer bypasses candidate.

## 9-D.8 Outcome A
All six corrections are implementation-ready: (1) slot moves regenerate the destination (re-derived tile-index + queued pattern DMA + source-slot cancel), (2) producer-ordered candidate coexistence with an audited 0..21 writer set (family clears, unconverted re-sets), (3) empty-chain hidden self-terminating slot 0 with a `max(highest_used+1,1)*4` never-zero DMA rule, (4) worklist cancel/reassign so every commit entry names its slot's final owner's final code, (5) base-68000 byte/bit scans (no `BFFFO`), (6) a complete dirty-producer audit proving no current mirror writer bypasses candidate publication (with the raw-write STOP condition). **Outcome A.**

**Confirmation:** no production source, ROM, build, tool, spec, Makefile, bookmark, branch, commit, or pipeline change was made — design amendment only.

---

# 9-E. FINAL CONTRACT ADDENDUM (2026-07-07): bounded reuse, resident-cancel, mirror-driven sync, global flip, bootstrap — GOVERNING for these points

§9-D architecture accepted and unchanged. The cases below correct the final synchronization contract and govern where they conflict with §9-C/§9-D.

## 9-E.1 Bounded worklist-entry reuse (worklist count ≤ 80, always)
**Corrects §9-D.4's free-cancel.** §9-D.4 set `worklist_entry_for_slot[s]=0xFF` on free, which would let a later re-allocation of the same slot **append a new physical entry** — repeated free/reassign of one slot could append many entries and overflow the 80-entry list. Fixed model:

**State:** `worklist_entry_for_slot[80]` byte = the *reserved physical entry index* for that slot (`0xFF` = none reserved yet). Each physical worklist entry is `{slot(word), code(word)}`; **canceled is encoded as `code = 0xFFFF`** (impossible for a real ≤12-bit code — no extra WRAM).

**Rules (per publication interval, i.e. between two worklist resets):**
- **First need** — a slot with `worklist_entry_for_slot[s]==0xFF` that needs a DMA: append one physical entry at index `count`, `count+=1`, set `worklist_entry_for_slot[s]=that index`. **This is the only operation that appends / increments `count`.**
- **Reserved thereafter** — once `s` has an index it is **retained until the next worklist reset**, across any number of code changes, frees, moves, and reassignments.
- **Code change** — overwrite the reserved entry's `code` (no append).
- **Free** — mark the reserved entry canceled (`code=0xFFFF`); **keep** `worklist_entry_for_slot[s]` (do **not** clear to 0xFF).
- **Reassign before commit** — the reserved entry is overwritten with the final `{s, final_code}` (or canceled by 9-E.2), reusing the same index (no append).
- **Reset** (after DISPLAY_OFF commit) — set every `worklist_entry_for_slot[*]=0xFF` and `count=0`; the physical table is now empty for the next interval.

**Commit** iterates entries `0..count-1`, **skipping any with `code==0xFFFF`**.

**Proof `count ≤ 80` for any sequence of updates/frees/moves/reassigns before VBlank:** `count` increments **only** on the `0xFF → index` first-need transition, and that transition occurs **at most once per slot** per interval (once reserved, the slot never returns to `0xFF` until the reset that also zeroes `count`). There are exactly 80 physical slots, so at most 80 distinct first-need transitions ⇒ at most 80 increments ⇒ `count ≤ 80`, independent of how many times any slot is recoded, freed, moved, or reassigned. ∎

## 9-E.2 Final code equal to resident code ⇒ cancel
On **every** mutation of a slot's reserved entry (code change, move, reassignment), compare the new code to `sprite_tile_resident_code[s]` (residency is stable within an interval — it is only updated post-DMA at commit, §Build 0141):
- `new_code != resident[s]` → entry active, `code = new_code`.
- `new_code == resident[s]` → entry **canceled** (`code=0xFFFF`), mapping retained.

So a slot whose code goes `A(resident) → B → A` ends canceled — no obsolete `B` DMA survives. Final publication state is exactly one of: **(final ≠ resident) → one pending DMA entry**, or **(final = resident) → no active entry.** An obsolete pending code is never left merely because the final update needs no new DMA.

## 9-E.3 Final `sync_record_from_mirror(record)` contract (replaces `sync_record(record,word0,Y,code,X)`)
The private synchronization primitive takes **only the record index** and:
1. **Reads** the completed retained PC090OJ record from `pc090oj_object_ram[record]` (word0/Y/code/X).
2. Decodes and updates **LUT** (`record_to_slot`), **bitmaps** (`represented`/`waiting`/`used_sat_slots`), **SAT links** (local splice, §9-C.3), **SAT fields** (via `place_record_in_slot`, §9-D.1 — re-derives slot-keyed tile-index), and **worklist** (§9-E.1/9-E.2).
3. **Never writes the PC090OJ mirror.**
4. **Never sets another candidate.**

**Producer contracts:**
- **Converted work-RAM family** (`pc090oj_workram_block_sprites`, records 0..21): performs the **exact arcade mirror writes once**, then for each written record calls `sync_record_from_mirror(record)` and **clears** that record's candidate — mirror-write + sync + candidate-clear in one VINT-masked step.
- **Unconverted producers:** write the mirror and **set** the candidate (unchanged, §9-D.6). VBlank walks set candidates, calls `sync_record_from_mirror(record)`, and **clears** each consumed candidate.

**Proof — no duplicate mirror write, no candidate re-publication:**
- *Mirror writes:* the mirror for record N is written **once**, by whichever single producer ran (family store, or unconverted store). `sync_record_from_mirror` only **reads** the mirror (contract 3). Therefore total mirror writes = total producer writes; the synchronization path contributes **zero** additional mirror writes. ∎
- *Candidates:* `sync_record_from_mirror` never sets a candidate (contract 4); the family clears the candidate for the record it just synced; VBlank clears each candidate it consumes. The only thing that ever **sets** a candidate is a genuine unconverted producer mirror write. Hence a candidate is consumed at most once and is never re-published by the render path — the family's direct-sync path leaves **no** candidate for VBlank, and VBlank's sync leaves none either. Each net mirror change is synchronized **exactly once**. ∎

## 9-E.4 Global flip reevaluation
A **real global flip** (a control write that can change *renderability* — flipscreen, global sprite enable/disable, or any control feeding the on-screen/blank/offscreen-Y/X activation predicate) can make a currently **unrepresented, offscreen** record become renderable (or vice-versa). It therefore **must reevaluate all 256 retained records.**

Define `.Lpc090oj_reevaluate_all_records`: `for record in 0..255: sync_record_from_mirror(record)`. It is **operation-driven** — invoked only from the flip control's opcode-replace site — and is **not** a per-frame scan (bounded 256×sync, rare; runs VINT-masked or across a guarded critical section).

**Renderability-affecting vs not (documented distinction):** a control alters renderability iff it changes any predicate used in the activation decision (global enable, flipscreen that moves sprites on/off screen). Such controls ⇒ full 256 reevaluation. A control that provably **cannot** change renderability (e.g. a global attribute that only re-tints already-represented sprites without moving any record on/off screen) ⇒ may reevaluate **only the represented records** (`represented_records` bit-scan). Any control whose renderability impact is uncertain is treated as flip (full 256) — never the represented-only path.

## 9-E.5 Startup / reset / bootstrap
BSS is zero at reset, but two arrays default to a **non-zero** empty value, so an explicit `.Lpc090oj_renderer_init` (run once, at the same one-time point the old `.Lvcs_clear_generated_sprite_state`-equivalent state was first established, guarded by `pc090oj_renderer_initialized`) sets:

| State | Init value |
|---|---|
| `record_to_slot[256]` | fill **0xFF** (all unrepresented) |
| `represented_records` (32 B) | 0 |
| `waiting_records` (32 B) | 0 |
| `used_sat_slots` (10 B) | 0 |
| `worklist_entry_for_slot[80]` | fill **0xFF** (none reserved) |
| `represented_count` | 0 |
| `sat_dirty` | 1 (force first upload) |
| `pc090oj_tile_dma_count` | 0 |
| staged `SAT[0]` | **hidden + terminating:** word0 = Y offscreen (≥ `224+bias`), word1 link = 0, word2 = 0, word3 = 0 |

**Populating existing mirror state without losing pre-init records and without a per-frame scan:** the PC090OJ mirror is retained RAM the arcade writes into during boot, possibly **before** the renderer initializes. On init, request a **one-time bootstrap sweep** — set **all 256 candidates once** (a single full-set). The **first VBlank** after init then runs `sync_record_from_mirror(record)` over every record, populating LUT/bitmaps/SAT/worklist from whatever the mirror currently holds → any record written before init is captured (subsumes any pre-init candidate). This is a **one-shot** bootstrap: candidates are cleared as consumed and thereafter only real producer writes re-set them — no recurring scan is introduced. Until that first sweep completes, the staged hidden empty `SAT[0]` (above) is what the first commit uploads, so nothing spurious is shown. After the sweep the renderer runs purely on dirty candidates + the converted family's direct sync.

## 9-E.6 Revised validation additions
Add proof that:
- **Worklist count never exceeds 80** — `count` increments only on the once-per-slot `0xFF→index` transition (9-E.1); stress with repeated free/reassign of one slot and confirm a single reserved entry, `count` unchanged.
- **≤ one reserved entry per slot per interval** — `worklist_entry_for_slot[s]` transitions `0xFF→index` at most once until reset; assert never re-appends.
- **Return-to-resident cancels DMA** — drive `A→B→A`; assert the reserved entry ends `code==0xFFFF` and commit issues **no** DMA for `s`.
- **`sync_record_from_mirror` purity** — instrument: it performs **zero** writes to `0x00D00000..0x00D007FF` and **zero** candidate sets; only reads the mirror.
- **No duplicate mirror write / no candidate re-publication** — per record, producer mirror-writes == 1 and candidate consumed ≤ 1 (9-E.3).
- **Global flip activates/deactivates previously-unrepresented records** — an offscreen unrepresented record becomes represented (and the reverse) after `.Lpc090oj_reevaluate_all_records`.
- **Initialization** — before the first sweep the committed SAT is the hidden empty slot 0 (nothing visible); the first valid mirror state is synchronized **exactly once** by the one-shot bootstrap; `record_to_slot`/`worklist_entry_for_slot` are all `0xFF`, all bitmaps clear.

## 9-E.7 Revised implementation boundary (supersedes §9-D.7 where it conflicts)
- **File:** `apps/rastan-direct/src/pc090oj_hooks.s` only.
- **Private primitive:** `.Lpc090oj_sync_record_from_mirror(record)` — reads mirror, updates LUT/bitmaps/SAT links+fields/worklist; **never** writes mirror, **never** sets a candidate (9-E.3). Replaces the `(record,word0,Y,code,X)` form.
- **Worklist:** `worklist_entry_for_slot[80]` is the **persistent reserved-index map** (not cleared on free); canceled entry encoded `code=0xFFFF`; append only on first-need; resident-equal ⇒ cancel (9-E.1/9-E.2). Build 0141 worklist remains the only pattern-DMA path; commit skips `code==0xFFFF`.
- **Add:** `.Lpc090oj_reevaluate_all_records` (256-record, flip-driven, not per-frame — 9-E.4); `.Lpc090oj_renderer_init` + `pc090oj_renderer_initialized` guard + one-shot 256-candidate bootstrap (9-E.5).
- **Convert:** family `emit_slots_0_21` → `pc090oj_workram_block_sprites`: exact arcade mirror writes once → `sync_record_from_mirror` per record → clear (not set) that candidate.
- **Preserve:** §9-D.1 regenerate-from-mirror + slot-keyed tile-index; §9-D.3 empty-chain `max(highest_used+1,1)*4`; §9-D.5 base-68000 scans; §9-D.6 audit + raw-write STOP; Build 0141 residency/commit; no packing; no one-frame latency; no committed-shadow.
- **WRAM:** unchanged **~413 B** (canceled state folded into the existing `code` field via the `0xFFFF` sentinel — no new array).
- **Excluded (per task):** PC080SN, palette/score/position/stray-sprite fixes, generic-scan/table-clear micro-opt, complete rewrite, one-frame pipeline, committed-shadow.

## 9-E.8 Outcome A
All six corrections are implementation-ready: (1) bounded reuse with a persistent reserved-index map proven `count ≤ 80`; (2) resident-equal cancellation leaving exactly one-or-zero active entry per slot; (3) `sync_record_from_mirror(record)` that only reads the mirror and never republishes a candidate, with the no-duplicate/no-republish proof; (4) flip-driven 256-record reevaluation with the renderability-affecting distinction documented; (5) an exact init table + one-shot bootstrap sweep that loses no pre-init record and restores no per-frame scan; (6) the revised validation set. **Outcome A.**

**Confirmation:** no production source, ROM, build, tool, spec, Makefile, bookmark, branch, commit, or pipeline change was made — design amendment only.
