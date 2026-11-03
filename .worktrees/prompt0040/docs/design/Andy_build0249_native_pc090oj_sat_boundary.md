# Build 0249 — Native PC090OJ→SAT Producer Boundary (research; no source/build)

**Agent:** Andy. **Type:** focused sprite architecture + runtime census.
**Production source / remap spec / ROM / build / counter:** UNCHANGED (Build 0249 / counter 249;
`RASTAN_GAMEPLAY_HUD_SPRITES=2`). **Authority:** `address_map.json` (segment-membership; no fixed-offset
inference), `specs/rastan_direct_remap.json`, `rastan_direct_patch_manifest.json`, Build 0249
`pc090oj_hooks.s`/symbols, arcade opcodes, MAME `pc090oj.cpp` (oracle). **Evidence:**
`states/traces/build0249_pc090oj_census_20260802/` (`census.txt`). PC090OJ object RAM used **only as oracle**.

## Native-hardware-replacement acknowledgement (policy §4/§12)

- **Retain (arcade-owned):** actor lifecycle, animation/sprite code, X/Y, size/composition, flip, palette,
  priority, visibility, ordering, retirement — all decided by the arcade actor logic and its sprite builder.
- **Replace + prune (chip tail):** the PC090OJ object-RAM record production, the **faithful object-RAM
  mirror** (`pc090oj_object_ram`), record→slot indirection, and any generic record scan/decoder.
- **Finding:** Build 0249's live gameplay sprite path is the **forbidden pattern** — arcade writers → a
  faithful 256-record object-RAM mirror → record→slot SAT build → SAT DMA. This report inventories it,
  censuses its per-frame cost, and identifies the semantic boundary — then **scoped-STOPs implementation
  planning** because the single common producer, composite expansion, and ordering are not yet proven (§7).

---

## 1. Current architecture (Build 0249) — the forbidden mirror pattern

```
arcade actor logic (unpatched)
  → arcade sprite builder 0x03C902 (arcade_copy; builds 8-byte records in workram: attr,Y,code,X)
  → chip-write / block-copy functions (PATCHED, "Strategy A" body replacement)
        → pc090oj_object_ram  (FAITHFUL 256-record MIRROR, 0xD00000-mapped, 0xFFA8BC, 0x800 bytes)
  → record→slot mapping (record_to_slot / represented_records / used_sat_slots)
  → staged_sprite_sat (0xFFA1D4) → vdp_commit_sprites → VDP SAT DMA (VRAM 0xF800)
```

The mirror is a chip-shaped object-RAM reproduction (8-byte records: `word0`=attr[flipY b15, flipX b14,
palette b3:0], `word1`=Y[9-bit; 0x180=off-screen], `word2`=code[13-bit], `word3`=X[9-bit]; 256 max; first =
highest priority — validated vs MAME `pc090oj.cpp`). Per policy §8 this mirror is prohibited as **final**
authority; it exists here as the production authority — the target to remove.

## 2. Live route inventory + address-map / remap table

| Route (helper) | Arcade PC | Genesis PC | Kind | Class | Produces final SAT? |
|---|---:|---:|---|---|:--:|
| `hook_target_3b902` (main writer) | `0x03B902` | `0x03BB02` | patched_site (0x00072A06) | gameplay | NO — mirror |
| `hook_target_3b926` | `0x03B926` | `0x03BB26` | patched_site (0x00072A40) | gameplay | NO — mirror clear |
| `hook_target_3b930` (faithful record) | `0x03B930` | `0x03BB30` | patched_site (0x00072A58) | gameplay | NO — mirror |
| `hook_target_41dae` | `0x041DAE` | `0x041FAE` | patched_site (0x00072A98) | gameplay | NO — mirror |
| `hook_target_41f5e` (workram→OJ block copy) | `0x041F5E` | `0x04215E` | patched_site (0x00072AB6) | gameplay | NO — mirror |
| `hook_target_45dfa` | `0x045DFA` | `0x045FFA` | patched_site (0x00072ABC) | gameplay | NO — mirror |
| `hook_target_59f5e` | `0x059F5E` | `0x05A15E` | patched_site (0x00072C08) | gameplay/effect | NO — mirror |
| `hook_init_priority_3ad84` | `0x03AD84` | `0x03AF84` | patched_site (0x00072D62) | init/priority | NO — mirror |
| `hook_score_digit_3b802` | `0x03B802` | `0x03BA02` | patched_site (0x00072D98) | **HUD** | NO — mirror |
| `hook_slot_init_54052` | `0x054052` | `0x054252` | patched_site (0x00072E84) | gameplay slot init | NO — mirror |
| `hook_sprite_update_54810` | `0x054810` | `0x054A10` | patched_site | gameplay | NO — mirror |
| `hook_sprite_decay_5607c` | `0x05607C` | `0x05627C` | patched_site | gameplay decay | NO — mirror |
| `hook_copy_56114` | `0x056114` | `0x056314` | patched_site | gameplay | NO — mirror |
| `hook_zero_fill_56440` | `0x056440` | `0x056640` | patched_site | clear | NO — mirror |
| `hook_status_sprite_5a098` | `0x05A098` | `0x05A298` | patched_site | HUD/status | NO — mirror |
| `hook_3ad44_dispatch` (bulk-clear + tilemap) | `0x03AD44` | `0x03AF44` | patched_site | bulk-clear | NO — mirror clear |
| ctrl/sprite_ctrl shadow captures | `0x03AE06/1E/8E`, `0x03A1D8/…` | — | patched_site | register shadow | n/a (ctrl only) |
| audit guard | `0x0510EA/0x0510F4` | — | patched_site | guard (0 hits observed) | n/a |
| **arcade sprite builder** | `0x03C902` (+ Y-sub `0x3CA12`) | `0x03CB02` | **arcade_copy (unpatched)** | semantic producer | builds workram records |
| SAT build/commit | — | `0x0007348E` `vdp_prepare_sprites` / `0x0007349C` `vdp_commit_sprites` | Genesis-only | all | reads mirror → SAT |

**Route classification (task §1 buckets):**
1. **Direct native SAT routes:** none for gameplay (all go via the mirror).
2. **Routes writing the mirror:** all 16 writer helpers above.
3. **Generic scans/decoders:** `vdp_prepare_sprites` (candidate/decode counters exist) — but **not the active
   path** at runtime (§3: candidate/decoded=0); the active build is the record→slot mapping.
4. **Linked-but-unreachable:** the audit guard (`0x0510EA/F4`, 0 hits); the candidate-scan path (counters 0).
5. **Frontend-only:** high-score FG producer `0x03C3FE`; title/story sprite routes flow through the same
   builder+mirror gated by scene id (not separately isolated in the mirror path — see §6).

## 3. Runtime execution census (Build 0249 Stage 1, `census.txt`)

Reached Stage-1 gameplay (P1 A/Start), walked right + jumped to spawn enemies; sampled the subsystem's own
counters over F300–1500.

| Metric | Observed | Interpretation |
|---|---|---|
| `producer_write_count` | 4891→32516 (cumulative) | **≈23 mirror writes / frame** (27625 over 1200 frames) |
| `emitted_count` (per frame) | 10,15,30,46,22,14,14,30,42 (max **50**) | 14–50 SAT sprites emitted/frame |
| `dropped_count` | **2**/frame | SAT budget overflow (2 sprites dropped) |
| `candidate_count` / `decoded` / `drawable` | **0** at frame boundary | full 256-record generic scan is **not** the active build path |
| `represented_count` | 384 (cumulative) | record→slot representation active |
| `hud_suppressed_count` | 384 (cumulative) | HUD-mode-2 suppression active (mode 2 preserved) |
| `used_sat_slots` | 0xFF00 | sentinel/mask (not a clean live count in this read) |

**Cost summary:** the recurring per-frame gameplay cost is **≈23 faithful object-RAM mirror writes** plus the
record→slot SAT build (emitting 14–50 sprites, dropping 2). The expensive full 256-record generic scan is
**not** executing (candidate/decoded=0). So the removal target is primarily the **mirror + record→slot
indirection**, not a live generic scan. (Exact within-frame scan cost needs an instruction-level measurement;
the counters are read at frame boundary.)

## 4. Descriptor / SAT semantics (validated — reused, not re-derived)

8-byte record → Genesis SAT: `flipY=word0 b15`, `flipX=word0 b14`, `palette=word0 b3:0`, `Y=word1&0x1FF`
(`0x180`=off-screen sentinel), `code=word2&0x1FFF`, `X=word3&0x1FF`; **256 max, record order = priority
(first highest)**. Genesis SAT base VRAM `0xF800` (`VDP_REG_SAT=0x7C`). Matches MAME `draw_sprites` +
`Andy_pc090oj_reconciliation_v2.md`.

## 5. Candidate semantic producer boundary

- The arcade **sprite builder `0x03C902`** (arcade_copy, **unpatched**) writes `word0=attr`, `word1=Y` (via
  `0x3CA12`), `word2=code`, `word3=X` into **arcade workram** sprite records — this is the highest point where
  the actor's semantic sprite parameters exist, **above** any object-RAM destination. The block-copy
  `0x41F5E` (patched) then moves workram records to the mirror.
- **The clean native boundary is the workram sprite record (builder output / block-copy input), not the chip
  writers.** Emitting SAT from the workram records would eliminate the mirror and the record→slot indirection.
- This is the sprite analog of the tilemap semantic cut, and matches the `reconciliation_v2` "Option A
  (workram intercept)" recommendation that the current implementation did **not** adopt (it intercepted the
  lower chip-write functions instead).

## 6. HUD / frontend separation (partial)

- **HUD mode 2** is handled via `hook_score_digit_3b802` + `hook_status_sprite_5a098` + a suppression counter
  (`hud_suppressed_count`=384) — preserved. Build 0233 P1 score/1UP and Build 0234 bat retirement live here.
- **Frontend/title/story** sprites flow through the **same** builder+mirror path, gated by scene id, plus the
  high-score FG producer `0x03C3FE`. They are **not** cleanly isolated from gameplay in the mirror path — a
  native boundary must separate them by scene id + producer identity (unproven at the record level here).

## 7. STOP — semantic boundary + composite/ordering not yet proven

Per the task's STOP conditions, implementation planning is **STOPPED** because:
- **Single common gameplay producer is UNPROVEN.** There are **16 distinct writer routes** plus 15 documented
  workram call sites; the reconciliation itself established that runtime PC090OJ writes are **not statically
  enumerable** (pointer/indirect writes). Whether one bounded producer (or the `0x03C902` builder) covers
  player + enemies + deaths + item drops + effects — as required for a shared boundary — is **not** proven by
  runtime evidence.
- **Composite/multi-tile expansion is UNPROVEN.** How arcade multi-tile actors (Rastan, lizard-man, bats)
  expand into Genesis sprites was not traced from the semantic source (only the mirror-record count is known).
- **Ordering/priority reproduction is UNPROVEN.** The mirror uses record order = priority; whether the
  semantic-boundary producer preserves that order without the mirror is not shown.
- **Per-class lifecycle/retirement + frontend/HUD isolation** from the semantic record stream are not proven
  (§6).

This is not ambiguity about the *format* (§4 is solid) or the *cost* (§3) or the *route inventory* (§2) — it
is that the **direct-SAT contract** (one producer, composite rules, ordering, lifecycle) required before any
implementation is not yet backed by runtime evidence. Proceeding would risk a generic decoder or a broken
per-class model.

## 8. Retirement candidates (after the native boundary is proven + implemented)

| Structure | Gameplay-executing? | Est. cost | Replaceable by direct producer? | Still needed by frontend/HUD? |
|---|---|---|---|---|
| `pc090oj_object_ram` mirror (256 rec) | YES (~23 writes/frame) | ~23 record writes/frame | YES | no (frontend can use same producer) |
| record→slot mapping (`record_to_slot`, `represented_records`) | YES | per-frame build | YES | no |
| `vdp_prepare_sprites` candidate scan | **NO** (counters 0) | ~0 (not active) | already inactive | no |
| audit guard `0x0510EA/F4` | NO (0 hits) | 0 | delete | no |
| ctrl/sprite_ctrl shadows | YES (register captures) | trivial | keep (register state) | keep |
| tile-DMA worklist (`pc090oj_tile_dma_worklist`) | YES | per-frame | keep (VRAM residency ≠ SAT) | keep |

Do not claim speed gains from deleting the inactive candidate scan (it does not execute). The real recurring
cost is the mirror writes + record→slot build.

## 9. Deliverable status vs task

Delivered: route inventory (§2), address-map/remap table (§2), direct-native-vs-compat classification (§1–§2),
runtime census (§3), descriptor/SAT semantics (§4), semantic-boundary candidate (§5), HUD/frontend note (§6),
retirement candidates (§8), cost (§3). **Not delivered (STOP, §7):** proven single-producer boundary,
composite-expansion rules, ordering/priority proof, per-class lifecycle/retirement proof, final SAT ownership
model — these require the follow-up runtime proof below before an implementation task can be written.

## 10. Required follow-up (to unblock implementation)

A focused runtime trace on Build 0249 Stage 1 that, from the **workram sprite records** (builder `0x03C902`
output / block-copy `0x41F5E` input — object RAM as oracle only): (a) captures per-frame the full live actor
set (player, ≥1 lizard-man, ≥1 bat through death/retirement, item drop, weapon/effect, HUD digits, one title
route) with attr/Y/code/X/composite membership; (b) proves whether one producer/boundary emits all gameplay
classes; (c) proves composite expansion (how each actor maps to N SAT entries); (d) proves ordering == record
priority; (e) proves lifecycle/retirement (off-screen sentinel / clear) and HUD/frontend isolation by scene
id. Only then is the direct-SAT ownership model + the smallest common-producer Cody task provable.
