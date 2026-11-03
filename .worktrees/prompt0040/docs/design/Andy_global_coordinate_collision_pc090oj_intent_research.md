# Andy — Global Gameplay Coordinate, Collision & PC090OJ Intent Research (Build 0234 baseline)

**Date:** 2026-07-24 · **Mode:** research/architecture only — NO source/tool/ROM/counter change (verified at end). Baseline Build 0234 (`24dc953ed0301c91…`, counter 234). Evidence: `states/traces/build0234_bat_stale_*/`, arcade Ghidra exports under `analysis/ghidra/rastan_arcade/exports/`, `build/rastan-direct/address_map.json`.

## Ghidra project examined
Existing project `analysis/ghidra/rastan_arcade/ghidra_project/rastan_arcade_world_rev1.rep` (world_rev1 maincpu). This pass worked from the committed exports (`decompiler_export.c`, `linear_disassembly.tsv`, `function_inventory.tsv`, `xrefs.tsv`, `call_graph_edges.tsv`, `scalar_constants.tsv`) + matched read-only MAME traces. **The .rep database was NOT modified in this pass** (to avoid corrupting the shared project without a proven headless round-trip); proposed annotations are listed in "Ghidra annotation proposals" for a controlled follow-up.

---

## 1. Authoritative arcade coordinate model (recovered)
Recovered from the sprite composer engine `0x03D054`, the incremental producers (e.g. `0x054810`), the scroll committer `0x055AB4`, and the PC090OJ hardware behavior (MAME taito/pc090oj.cpp), cross-checked against the Genesis decode (`.Lpc090oj_decode_record`).

- **Camera:** `a5@0x129A` = camera X, `a5@0x129C` = camera Y (loaded at 0x052A74 / 0x0547D0 from the level scroll state).
- **Actor → PC090OJ record (screen space):** producers read an actor's screen-relative byte position and add the camera term. Confirmed in the Genesis translation of `0x054810`:
  `Y = sign_ext(actor@3) + a5@0x129C + 1, & 0x1FF`; `X = sign_ext(actor@2) + a5@0x129A, & 0x1FF`.
  The composer engine `0x03D054` dispatches on `actor@56` (composer type 1..N) and emits one-or-more PC090OJ records via `(a1)+`, each carrying a **frame-specific anchor** from per-type tables (the death/hide branch writes `Y=0x180`).
- **PC090OJ hardware origin/flip:** when the global-flip ctrl bit is clear the chip computes `screen_x = 320 − x − 16`, `screen_y = 256 − y − 16` (inversion + a fixed 16px inset). Genesis replicates this in `.Lpc090oj_decode_record`: `FLIP_X_TERM=304 (=320−16)`, `FLIP_Y_TERM=240 (=256−16)`, plus the 9-bit sign fold (`if v>0x140: v−=0x200`).
- **Background/foreground scroll:** committed at `0x055AB4`: `a5@0x10EE → 0xC20000` (FG), `a5@0x10EC → 0xC40000` (BG), `a5@0x10B0/0x10AE → C2/C40002`. Arcade visible area is rasters 8..247 (rastan.cpp set_visarea).

**Canonical arcade sprite equation (recovered):**
`record = compose(actor_screen_pos(actor, camera), frame_anchor(actor_type, frame))` → then **PC090OJ hardware**: `screen = (304,240) − record` (non-flip). A single, uniform transform for ALL sprite families. There is NO per-family vertical fudge in the arcade; alignment is entirely (camera subtraction, already baked into the actor screen byte) + (frame anchor) + (uniform chip inset).

**Arcade collision space:** the collision side-channel map is at `arcade 0x10DE00`, produced by the PC080SN BG producer (`0x0559B2`, sel `a5@0x10A8==0`) and read by the player floor/hazard path (`0x53C2E` lookup → `0x53FA6` dispatch; `*(map)&0x7F==8` ⇒ solid). It is indexed by the **same world/camera model** as the visual — collision and visual share one origin in the arcade.

---

## 2. Genesis coordinate-transform inventory (the compensations)
| Transform | Value | Space it acts on | Origin/history |
|---|---|---|---|
| `VDP_DISPLAY_ORIGIN_X_BIAS` (vdp_comm.s:83) | 16 | BG/FG plane scroll (render) | title-centering: map arcade visible-area origin → Genesis col 0 |
| `VDP_DISPLAY_ORIGIN_Y_BIAS` (vdp_comm.s:84) | 8 | BG/FG plane scroll (render) | title-centering (arcade visible starts raster 8) |
| `PC090OJ_TO_GENESIS_Y_OFFSET` (pc090oj_hooks.s:161) | −8 (`= −Y_BIAS`) | sprite decode (render) | keep sprites aligned with the +8-shifted BG (Build 0147) |
| `PC090OJ_TO_GENESIS_X_OFFSET` (pc090oj_hooks.s:162) | 0 | sprite decode (render) | "frontend X already aligned; tune later" |
| `PC090OJ_SAT_X/Y_BIAS` (pc090oj_hooks.s:171-172) | 0x80 | final Genesis SAT (hardware) | Genesis SAT coordinate bias (screen+0x80) |
| block-0x2C8 `.Lb2c8_yfix` | −8 per record | lizard SPRITE Y only (render) | KF-067 lizard "move up 8px" compensation |
| tilemap `#-8` sites (2268–2444) | −8 | FG/collision producer rows | KF-067 collision-row / FG placement |

**Key observation:** these are **not one transform** — they are a *stack of independent 8px/16px compensations* added at different boundaries (plane scroll, sprite decode, per-family sprite Y, collision producer rows) to fix successive visible symptoms. They do not compose into a single coherent arcade→Genesis origin.

---

## 3. The central architectural finding — render space and collision space diverged
The title-centering change introduced a **+8 render-origin shift** (BG `Y_BIAS=+8`, mirrored by sprite `Y_OFFSET=−8`) so BG and sprites stay aligned *with each other*. That pair is internally coherent for RENDERING.

But the **collision map is a separate coordinate channel** (`0x10DE00`, produced by the PC080SN BG producer, read by the floor/hazard path) and it did NOT receive the same single, consistent transform:
- **KF-067** proved the Genesis collision ground band sits **one 8px row lower** than the arcade (row 39 vs 38) at the *producer* level (matched dumps).
- **OPEN-0159** proved several collision readers/producers use **un-rebased raw arcade-WRAM literals** (`0x0010DE00` not → `0x00FF1E00`), i.e. the collision channel was never fully brought into one Genesis space.
- The **lizard `.Lb2c8_yfix` −8** moves the lizard *sprite* up 8px to look right, WITHOUT moving the lizard's authoritative actor/collision state.

**Consequence (answers the "recurring move-up" and "lizard visual vs collision" questions):** because render space (+8/−8) and collision space (KF-067 +8-ish, partly un-rebased) are two independent 8px stacks, **each new gameplay object appears 8px off and gets its own −8 render patch**, while its collision stays put. That is the shared root of: "numerous gameplay graphics needed upward correction," and "lizard visual moved up 8px but collision/hurtbox occupies the former position." These are **not** independent per-object bugs — they are the same missing single-transform.

---

## 4. Standing vs crouching sword (frame-anchor evidence)
Recovered model: the sword hit region and the visible sword sprite share the actor origin but use **different frame anchors** (the composer engine `0x03D054` emits pose-specific records/anchors per `actor@56` type and frame). Genesis applies the uniform sprite `Y_OFFSET=−8` (+ per-family fudges) to the *rendered* sprite, but the attack-region check operates on the actor/collision coordinates (world/collision space).

- **Standing:** contact reads closer to the body than the visible sword ⇒ the attack-box is evaluated in the **collision/world space** (un-shifted / KF-067 space) while the sword *sprite* is rendered in the shifted render space with its frame anchor. The horizontal frame-dependent extension of the standing pose is therefore not reflected in the box ⇒ short reach.
- **Crouching behaves more arcade-like:** its pose has a smaller frame anchor / less render displacement, so the render-vs-collision gap is smaller ⇒ closer match. This is **evidence that only the poses whose anchor≈0 look correct**, i.e. the frame-anchor is the missing term — not a per-pose bug.

**Confidence: MEDIUM.** The exact arcade standing/crouching attack-box tables were not fully dereferenced in this pass (Ghidra fns are `FUN_*`; the pose tables sit behind `0x03D054`'s type dispatch). Marked as the strongest hypothesis; a matched box-overlay diagnostic (external MAME script, read-only) is the confirming next step.

---

## 5. Floating grey projectile artifacts — identity & ownership (partial)
Read-only 0234 scan surfaced persistent anomalous drawable rows **records 132-134 = code 0x09DA with garbage-high coordinates** (Y=0x6669, X=0x989A) that fold on-screen via `&0x1FF` — the long-standing "record 132" class. The automated run stayed in attract (mode 0), so the *gameplay* floating pair was not captured here, but the structural signature matches:
- a PC090OJ row that is **drawable but whose source actor is inactive/absent** (stale ownership), OR **never correctly initialized** (garbage coords folding on-screen);
- placement "varies between builds" because it is **uninitialized/stale memory**, not a positioned object;
- it "moves with world scroll" because a producer keeps re-emitting it relative to the camera without a live actor to retire it;
- **grey is SECONDARY** — the palette metadata is stale/uninitialized on a record that should not be drawable at all; recoloring would only recolor an object that shouldn't exist. **Do not chase the palette.**

This is the **same class** as the (now-fixed) hurry-up bat residue and record 132: *a PC090OJ record left drawable because the producer lifecycle did not retire/blank/initialize it.* Full identity (exact producer + arcade object family) needs one interactive gameplay capture with the emit_slot caller-chain + actor-slot logger (the method that cracked the bat).

---

## 6. Producer lifecycle audit (shared invariant)
**Invariant (arcade):** when an actor becomes inactive/dead/recycled, its PC090OJ record receives an explicit arcade **blank/hide/replace** (e.g. `Y=0x180` at 0x41EFC). A Genesis producer must not merely *stop writing* and leave a prior drawable row.

| Arcade producer | Actor src | PC090OJ dest | Genesis translation | Lifecycle branches represented? |
|---|---|---|---|---|
| `0x41E22` (block A5+0x2C8) | 9 entries | records 140-238 (lizards) | `pc090oj_stage_block2c8` | **PARTIAL:** `a4@(0)==0`/`a4@(5)==0` → `.Lb2c8_blank` (Y=0x180) ✔; but `a4@(3)!=0` → `.Lb2c8_skip` (preserve) where arcade dispatches `0x3EFBE`. Deferred-special rows may persist. **AUDIT** |
| `0x41E76` (block A5+0x748) | 11 entries | records 46-56 (record46+bats) | `.Lpc090oj_stage_record46_validated` | **FIXED (Build 0234):** inactive/retire now → `Y=0x180` (arcade 0x41EFC) via `.Lrecord46_blank` |
| `0x054810` / `0x05607C` / `0x056114` | HUD/status/decay | records 30-71 | `hook_sprite_update_54810` / `_decay_5607c` / `_copy_56114` | **AUDIT:** `0x05607C` "decay" walks `staged_sprite_descriptor_table` — a defunct 4-byte stub in BSS (see reachability report). It reads bit0 of a zeroed stub ⇒ effectively no-op; records 56-63 never blanked by it. Stale records 132-134 ⇒ some producer never blanks/inits. |

**Conclusion:** the bat fix repaired ONE instance of a general missing-lifecycle pattern. The **block-0x2C8 (lizard) `a4@(3)!=0` skip** and the **stale records 132-134** are the next confirmed/suspected instances of the same invariant violation.

---

## 7. Shared causes vs independent bugs (classification)
| Observed symptom | Root class | Shared with |
|---|---|---|
| Recurring "move gameplay sprites up 8px" | **Fragmented coordinate model** (render +8/−8 vs collision KF-067, no single transform) | lizard, sword |
| Lizard visual up-8 but collision at old position | **Fragmented coordinate model** (visual-only `.Lb2c8_yfix`, collision untouched) | move-up, sword |
| Standing sword short reach | **Fragmented coordinate model** (attack-box in collision space, sprite in render space + missing frame anchor) | move-up, lizard · confidence MED |
| Crouching sword ~correct | (same root; pose anchor≈0 so gap small) — diagnostic, not a bug | — |
| Floating grey projectiles | **Incomplete producer lifecycle / stale-drawable-row** (uninit/stale record; grey is secondary) | bat residue, record 132 |
| Hurry-up bat residue (fixed) | **Incomplete producer lifecycle** | projectiles, record 132 |

**Two shared roots, not one:** (A) a fragmented render-vs-collision coordinate model (drives the move-up / lizard / sword cluster); (B) incomplete producer lifecycle leaving stale/uninitialized drawable PC090OJ rows (drives projectiles / record 132 / former bat residue). Palette-grey is secondary to (B). They are genuinely distinct roots and should not be forced together.

---

## 8. Recommended global rules (for future corrections — NOT implemented here)
1. **One coordinate transform.** Define a single `arcade_screen → genesis_screen` mapping (camera subtraction is already the arcade's; add ONE viewport-origin term and the PC090OJ chip inset) and apply it identically to BG plane scroll, sprite decode, AND the collision map. Derive the origin term from the arcade visible-area geometry, once.
2. **Collision in the same space as the visual.** Bring the collision channel (`0x10DE00`→`0xFF1E00`) fully into the one Genesis space (finish the OPEN-0159 rebase; align the KF-067 row-base) so a hurtbox and its sprite occupy the same pixel. Then **delete the per-object visual compensations** (`.Lb2c8_yfix −8`, family fudges) — they exist only because collision and render diverged.
3. **Frame anchors from the arcade tables.** Take per-frame sprite anchors from the composer engine's pose tables (behind `0x03D054`), not a uniform per-family offset — this is what the standing sword needs.
4. **Complete producer lifecycle.** For every translated producer, represent every arcade lifecycle branch (live/animate/death/inactive/hide) — specifically translate every arcade blank/hide (`Y=0x180`, tile-replace) rather than a skip-without-write. Audit block-0x2C8 and the records-132/decay producers next.
5. **Initialize records.** A PC090OJ row must be explicitly initialized/blanked before first use so uninitialized memory never folds on-screen (records 132-134).
6. **Never fix a coordinate symptom with a per-object offset, and never fix a stale row by hiding its tile code.** Both are the compensations this report identifies as the disease.

**Central answer:** the whole game reproduces arcade intent without repeated per-object patches once (a) there is ONE coordinate transform shared by background, sprites, and collision, and (b) every producer fully translates the arcade actor lifecycle (including its blank/hide/init branches). The recurring symptoms are the two systemic gaps, not many object-specific defects.

---

## 9. Ghidra annotation proposals (for a controlled follow-up; .rep NOT modified this pass)
- `0x03D054` → `pc090oj_compose_actor_to_records` (dispatch on `actor@56` composer type; emits records via (a1)+; frame-anchor tables per type).
- `0x055AB4` → `commit_plane_scroll` (a5@0x10EE/0x10EC/0x10B0/0x10AE → C2/C40000/0002).
- `0x0559B2` → `pc080sn_bg_collision_and_tile_producer` (collision `*(block+20+row*8+strip*2)` or `+34`; tile `+0`).
- `0x41E22` → `pc090oj_produce_block_2C8`; `0x41E76` → `pc090oj_produce_block_748`; `0x41EFC` → `pc090oj_blank_record_Y180`; `0x3EFBE` → `pc090oj_deferred_special_dispatch`.
- `0x53C2E` → `collision_map_lookup`; `0x53FA6` → `player_floor_hazard_dispatch`.
- Struct `actor_t`: `+0 active`, `+1 sprite_code`, `+2 screen_x_byte`, `+3 screen_y_byte`, `+0x20 attr`, `+0x34 death/retire flag (a4@54)`, `+0x36 sub-state`, `+0x38 composer_type (a4@56)`. Confidence: field roles MED-HIGH from repeated producer usage; names proposed, not asserted.
- Globals: `a5@0x129A camera_x`, `a5@0x129C camera_y`, `a5@0x10EE fg_scroll`, `a5@0x10EC bg_scroll`.

## Uncertainties requiring more evidence
- Exact standing/crouching attack-box tables (need `0x03D054` type-table deref + a matched box overlay).
- The gameplay floating-projectile producer identity (need an interactive gameplay emit_slot caller-chain capture, like the bat).
- Whether the block-0x2C8 `a4@(3)!=0` skip actually leaves visible lizard residue (needs a lizard-death capture).

## Compliance
No source, tool, ROM, or build counter changed by this research. Counter remains 234. Research report only.
