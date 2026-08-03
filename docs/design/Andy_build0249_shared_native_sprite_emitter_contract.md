# Shared Native Sprite Emitter — Mode-Safe Producer Contract (Build 0249; analysis only)

**Agent:** Andy. **Baseline:** Build 0249 / counter 249 / `RASTAN_GAMEPLAY_HUD_SPRITES=2`. No production source,
remap, ROM, build or counter change. **Authority:** `address_map.json`, `pc090oj_hooks.s`, `tilemap_hooks.s`,
`out/symbol.txt`, arcade `build/maincpu.disasm.txt`, `build/genesis_postpatch.disasm.txt`, MAME
`pc090oj.cpp`/`rastan.cpp`. **Evidence:** `states/traces/build0249_pc090oj_contract_20260802_pre_pc090oj_contract/`
(`callers*.txt`, `player.txt`, `lizpack.txt`, `mid.txt`, `midsnap.txt`, `lizcost.txt`, `modes.txt`, `spec.txt`,
`spec2.txt`). Record ranges are **oracle ordering evidence only**, never runtime ownership.

> Single current contract. It corrects the previous version's two unsafe assumptions: (a) the default-only
> proof was **mode-0 only** — it does not license a global `.L3c950_sprite_direct` replacement across modes;
> and (b) the finalizer must **not** skip records 57–95 (the active player block at 92–95). The delivered build
> is **mode-gated**, not global.

---

## 1. The shared mechanism + the mode caveat

`.L3c950_sprite_direct` (`tilemap_hooks.s:2364`), reached via the redirect `0x3CB50 jsr 0x717F4`, is where every
**default-type (0x00)** engine piece assembles the four PC090OJ record words. **Proof scope:** over 46 s of
**Stage-1 (mode 0)** play the type dispatch executed **14507×** and **every** specialized handler
(`0x3C4D2/550/586/636/6DC/75C/7A4/830`) executed **0×** (`spec2.txt`). **This proves mode 0 only.** It does
**not** prove that mode-1 or mode-2 stages are default-only — those stages have different actor content whose
mappings can select specialized handlers. A global conversion of `sprite_direct` **plus** native-band
exclusion would therefore **hide any specialized-handler output in an unproven mode** — the failure this
contract avoids.

## 2. Mode-by-mode coverage

Dispatcher select at `0x41F4E`: mode word **`a5@(0x2A2)`** `==2 → 0x45DFA`, else `0x41DAE`. Mode is set in the
stage/scene-init routine (`0x452F6`=1, `0x45334`=2 → scene-init `0x501E2`) → **stage-dependent**. The mode gate
`0x45684` only rewrites the per-actor **attribute** byte `a4@39` from a mode-specific table (`0x45722` vs
`0x4576A`) — it does **not** change piece-type routing; mode-1 vs mode-0 differ by **stage content**, not
structure.

| Mode | `a5@0x2A2` | Dispatcher | Stages (evidence) | Active groups | Type routing | Genesis status |
|---|---|---|---|---|---|---|
| **0** | 0 | `0x41DAE` | Stage 1 (traced, `modes.txt`) | middle `a5+0x5C8`, enemies `a5+0x2C8`, effects `a5+0x748`; players1 `a5+0x508` inactive | **all 0x00 (proven 14507/0)** | enemies+effects preserved; **middle OMITTED**; players1 omitted |
| **1** | 1 | `0x41DAE` (same groups) | set when `(stage_ctr mod 23) ≥ 16` — **not reached in traces** | same tables as mode 0 | **UNPROVEN** (different stage enemies → may hit specialized handlers) | same staging as mode 0 (mode-blind) → same omissions + possible unhandled specialized content |
| **2** | 2 | `0x45DFA` | `0x45334` path — **not reached in traces** | enemies `a5+0x5C8`, effects `a5+0x748`, middle `a5+0x8C8` (repurposed) | **UNPROVEN** | `hook_45dfa` skips in gameplay; Genesis staging is **mode-blind** (runs `0x41DAE` tables) → **wrong/missing sprites** |

Static bounds are known for all groups (§5); only the mode-1/2 **type routing, lane confirmation and stage
selection** are unproven, and cannot be resolved from Stage-1 traces (no later-stage savestate; forcing the
mode word desyncs the actor tables).

## 3. PLAYER_FRONT resolution (records 57–95)

Band 57–95 has **two** distinct producers:

- **`a5+0x508` group1** (`0x41DAE` group `0x41DD2`, records 57–91, 2 slots, `d2`=13): **inactive** in Stage 1
  (`modes.txt` g1[0,0] every sample). High-priority, player-sized composite; most likely the **P2 / alternate-
  mode player** slot. Ownership PLAYER_FRONT; activation = a 2-player / specific-mode state (unproven); type
  routing unproven (never dispatched). **Stopped** — but it is a real arcade producer, not vestigial.
- **`a5+0x170` block** (records 92–95, 4 records): copied every frame by `0x41F5E` (`lea a5@(0x170),a1=0xD002E0`)
  — the **active** player-front element (weapon/secondary). This is a **custom block-copy packer** (stays
  compat), and it is **live** in normal play.

**∴ records 57–95 must remain emitted as compatibility** (they carry the active 92–95 block). The finalizer
**must not skip 57–95**. Only the native-owned bands (46–56, 96–119, 140–238) may be excluded, and only while
the native path is active (§6).

## 4. Corrected finalizer order (one consistent order)

Front → back, with native lanes spliced at their bands and **all** compat records emitted:

```
compat HUD           records 0..45
native FRONT_EFFECT   (band 46..56)
compat PLAYER_FRONT  records 57..95        <-- MUST be emitted (active 92..95 block)
native MIDDLE         (band 96..119)
compat PLAYER_BODY   records 120..139
native BACK_ENEMY     (band 140..238)
```

One continuous SAT link chain; `NATIVE_SAT_MAX=80` across the whole merge (drop-tail = backmost first).
Residency for every emitted entry (compat or native) via the existing `.Lnep_res_ok`/32-set×4-way/`cell_used`/
12-entry DMA path, in merge order. VBlank `vdp_commit_sprites` (`0x7349C`) unchanged.

## 5. Priority lanes + exact per-dispatcher bounds

| Lane | Band | `0x41DAE` bound | `0x45DFA` bound | **Queue size** |
|---|---:|---:|---:|---:|
| FRONT_EFFECT | 46–56 | 11 (11×1) | **36 (6×6)** | **36** |
| MIDDLE | 96–119 | 24 (6×4) | 20 (5×4) | **24** |
| BACK_ENEMY | 140–238 | **99 (8×10+19)** | 70 (5×10+20) | **99** |
| PLAYER_FRONT | 57–95 | 26 (2×13) group1 + 4 block | — | (compat) |

Size the native queues at the **max** (FRONT_EFFECT **36**, not 11). Enqueue can't overflow; the 80-cap drops
the backmost at finalize.

## 6. Safe mode-gated first build (the delivered design)

A single mode-owned flag makes the conversion safe in every mode:

- **`native_sprite_mode`** = (`a5@0x2A2 == 0`) — set once per frame at the top of `hook_target_41dae`
  (`0x72A98`), after reset. (Mode 0 is the only proven default-only mode.)
- **`.L3c950_sprite_direct`** branches on it: **native mode** → the four per-piece fields go to
  `native_sprite_emit(X,Y,artwork_code,pal_route,flipH,flipV,lane)` and **no** mirror write; **compat mode** →
  the original four `(%a1)+` record stores, byte-identical. (The C-window tilemap branch is untouched.)
- **Native-band exclusions** (46–56, 96–119, 140–238) in `native_emit_pass` apply **only** while
  `native_sprite_mode` is set; in compat mode the emit pass runs the full unmodified scan.
- **Compatibility records 57–95 and 120–139 are always emitted** (never excluded), in both modes.
- **No stale/cross-mode queue state:** the lane counts are reset every frame at the hook top; queues are
  spliced only when `native_sprite_mode` is set; on any mode-1/2 frame the queues are empty and unused.

In mode 0 this is exact (proven zero specialized pieces → mirror native-bands are empty; nothing to hide). In
mode 1/2 the game runs the **unchanged** compat path — no native emission, no exclusion, no suppression risk.

**Removal boundary (temporary → permanent):** the gate is removed when modes 1 and 2 are proven. For each: if
its groups are also default-only, extend the gate (and add the mode-2 `0x45DFA` staging with its lanes/bounds);
if any group uses a specialized handler, convert that handler to `native_sprite_emit` too. Once all modes are
native, `native_sprite_mode` is always true, the mirror + `0x3AD44`/`0x56xxx`/`0x5607C`/`0x59F5E` fills/decay
and the compat scan are deleted, and the finalizer becomes pure lane concatenation.

## 7. RETAIN / REPLACE / DELETE

- **RETAIN:** actor traversal/lifecycle/animation/mapping selection (`a0`)/coords/palette/flips/visibility/
  priority; the mode select (`a5@0x2A2`) and each dispatcher's group→lane assignment.
- **REPLACE (mode-0 now; other modes at the removal boundary):** the four `sprite_direct` `(%a1)+` stores →
  gated `native_sprite_emit`; the mode-0 staging → set lane + reproduce all `0x41DAE` groups (incl. the
  **restored middle**); the emit pass → the §4 gated rank-merge.
- **DELETE (PC090OJ-only, at the removal boundary):** `pc090oj_object_ram` mirror + `0xD00000` addressing,
  record packing, `record_to_slot`/represented/waiting, mirror scans/decoders, `Y=0x180` fills,
  `0x3AD44`/`0x56xxx`/`0x5607C`/`0x59F5E` fills/clears/copies/decay, the `stage_record46` scratch, audit guard
  + inactive candidate scan. Keep + rename `staged_sprite_sat`/residency/tile-DMA/`vdp_commit_sprites`/colbank.
  **Nothing is deleted while any mode still uses it** (the mirror stays until modes 1/2 are native).

## 8. Remaining custom / compat mechanisms

Player composer + block copy (`0x544D0–0x547A0`/`0x41F5E`, incl. the 92–95 block); HUD `0x3B802`/`0x5A098`;
specialized type handlers (`0x3C4D2/550/586/636/6DC/75C/7A4/830`); `workram_block_sprites`; and the mirror for
all compat bands and all mode-1/2 frames. Each is replaced at the §6 removal boundary or when its content is
proven.

## 9. Exact Cody task (mode-0-gated shared conversion, restore MIDDLE)

1. Add native lanes at the **§5 max bounds** (FRONT_EFFECT **36**, MIDDLE **24**, BACK_ENEMY **99**), each
   `{X,Y,artwork_code,attr}` + count, plus `native_sprite_lane` and `native_sprite_mode`. At the top of
   `genesistan_pc090oj_hook_target_41dae` (`0x72A98`): reset all lane counts, then set
   `native_sprite_mode = (a5@0x2A2 == 0)`.
2. Add `native_sprite_emit(X,Y,artwork_code,pal_route,flipH,flipV,lane)` → `queue[lane]` (per-lane Y-bias:
   BACK_ENEMY −8, else 0).
3. In `.L3c950_sprite_direct` (both `.L3c950_sprite_primary_loop`/`_alt_loop`): if `native_sprite_mode` →
   `native_sprite_emit` (no mirror write); else → the original four `(%a1)+` stores unchanged. Sentinel/blank →
   append nothing in native mode. Leave the C-window branch.
4. Set `native_sprite_lane` before each `jsr 0x3D254`: `stage_block2c8` → BACK_ENEMY; `stage_record46` →
   FRONT_EFFECT; add a **middle stager** (reproduce `0x41E0C`: `a5+0x5C8`, 6 slots, `d2`=4) → MIDDLE. These run
   in gameplay regardless of mode, but `sprite_direct` only diverts to native when `native_sprite_mode` is set,
   so mode-1/2 frames keep writing the mirror (compat) exactly as today. In native mode, drop the
   `stage_block2c8` KF-067 fix loop and the `stage_record46` scratch/flush (fold the −8 into the emitter).
5. Make `pc090oj_native_emit_pass` (`0x731E4`) the §4 order **only when `native_sprite_mode`**: emit compat
   0–45 → splice FRONT_EFFECT → emit compat **57–95** → splice MIDDLE → emit compat 120–139 → splice
   BACK_ENEMY; exclude only bands 46–56/96–119/140–238; one terminated chain; `NATIVE_SAT_MAX` across the merge;
   residency via the existing path. When `native_sprite_mode` is clear, run the unmodified full compat scan.
6. Reuse residency/tile-DMA/`vdp_commit_sprites`. Delete nothing. **Do not** touch Plane A/B, collision, rope,
   reset.

**Validate on one ROM:** Stage 1 (mode 0) — Rastan + lizard composite + another enemy + effect/item + **a
middle object now appearing** + the player-front 92–95 element still present, correct front-to-back priority,
death/retirement with no stale sprite, no duplicate output; and confirm a later-mode transition still renders
via the untouched compat path.

## 10. STOP status

**STOP: YES for a global (all-mode) conversion** — it could suppress unconverted specialized-handler output in
mode 1 or mode 2, whose type routing is unproven. The **delivered build is the mode-0-gated design** (§6/§9),
which is safe in all modes: native emission and band exclusion happen only when `native_sprite_mode` is set
(proven mode 0), compat records 57–95 and 120–139 are always emitted, and modes 1/2 run the unchanged compat
path. The temporary gate has an explicit removal boundary (§6). Remaining evidence to lift it and go all-mode:
a mode-1 and a mode-2 stage capture confirming each group's type routing/lanes, plus the fix for the mode-blind
Genesis staging.
