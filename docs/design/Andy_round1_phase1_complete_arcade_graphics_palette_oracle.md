# Andy — R1/P1 Original-Arcade Graphics/Palette Oracle (Layer A/B attribution + editor schema, 2026-08-26)

ANALYSIS ONLY. No production change, no ROM, Build counter 313, Build 0314 not consumed. ORIGINAL ARCADE ONLY
(maincpu/pc080sn/pc090oj ROM + analyzer dataset + saved captures). NO Genesis evidence used.

## Phase 0
- Relevant KF: KF-028/153 (plane palette scene loader), KF-1214/1220 (round-1 index 0x3BA88 -> pool 0x4FD02 loader,
  validated) — the analyzer's plane palettes use exactly this proven indirect loader. KF-050/051 (player block).
- HIGH hazard: reuse the analyzer dataset (plane_a_uses/plane_b_uses/palette_states) rather than re-decoding maps.
- Task classification: EXTENDING. Open/Closed impact: none changed. Contradiction: none.
- Session scope (Tighe's choice): **Layer A/B per-tile attribution + all plane bank 16-color values + editor schema**.
  Weapons/items/item-page/HUD-life-meter deferred to later sessions.

## Source of the attribution (already decoded, verified here)
- `analysis/graphics_optimizer/round1_phase1/plane_a_uses.json` — 1581 logical Layer-A (FG) uses, each with
  `physical_pattern` (sha256), **`palette_bank`**, `flip`, `priority_bits`, `map_cell_count`, records, coords.
- `plane_b_uses.json` — 854 Layer-B (BG) uses, all `palette_bank: 2`.
- `palette_states.json` — 15 banks with 16 `entries` each: `arcade_xbgr555`, `arcade_rgb` (exact RGB8), `lab`,
  plus loader `source` string proving the round-1 index path (e.g. bank 3 = `record@0x3BA8B block 12 @0x4FE82`).

## LAYER A (FG) — CLOSED
- **1581 logical uses; 1315 distinct physical patterns; 199 patterns used with >1 palette bank** (multi-bank supported).
- **11 palette banks**: 0x003(458), 0x004(80), 0x005(59), 0x006(16), 0x007(20), 0x017(203), 0x018(139),
  0x01A(183), 0x01B(163), 0x01C(147), 0x01D(113). Matches the prior-to-verify list exactly.
- Every use carries flip + priority_bits. Per-tile bank in `layer_a_palette_usage.csv`; all-16-color values per bank
  in `plane_palette_banks.json`; swatches in `contact_sheets/r1p1_plane_palettes.png`.
- Epoch: single (epoch_00) — plane banks 0..31 filled once at scene load; Layer B timeline shows a single distinct
  state across records 0..15, and Layer A's multi-bank is spatial (different tiles), not temporal.

## LAYER B (BG) — CLOSED
- **854 uses, ALL bank 0x002** (proven from attributes; corrects the stale `layer_b_tiles.csv` "bank48" label).
- Single vocabulary, single epoch. Full 16 colors of bank 0x002 in `plane_palette_banks.json`.

## Palette values (Parts G/I) — CLOSED for planes
All 12 plane banks (11 Layer A + Layer B 0x002) have full 16-entry values: index, arcade_xBGR555, exact MAME RGB8
(xBGR_555 pal5bit; 5-bit channel = source nibble*2), lab (for future close-color work), + loader/source provenance.

## Editor-ready normalized schema — `analysis/graphics_optimizer/arcade_graphics_oracle/`
Generalized, whole-game-ready (type-based contexts; round/phase/segment optional):
- `contexts.json` — GAME > GAMEPLAY > R1 > P1 > 16 segments; ITEM_PAGE stub; 17 context types enum.
- `context_transitions.json` — R1/P1 segment progression (record N->N+1), proof-linked.
- `patterns.json` — stable `pattern:pc080sn:<sha16>` IDs (thin index; canonical bytes stay in analyzer/corpus).
- `palettes.json` — stable `palette:arcade.r01p01.plane.bank_0xNNN.epoch_00` IDs -> plane_palette_banks.json.
- `usages.json` — context<->pattern<->palette usage (-> the usage CSVs).
- `coexistence.json` — plane banks live in R1/P1 (evidence only; NO Genesis consolidation).
- `manifest.json` — declares canonical authorities + ID schemes; lists FUTURE editable layers NOT created here.
Stable IDs are deterministic, order-independent, separate physical vs semantic identity, and support multi-context /
multi-bank / multi-object without duplication. Provenance retained for reverse "why is this color here?" lookups.

## NOT closed this session (deferred, honest)
Player/weapon epochs, gameplay items, scrolling item-page lexicon, HUD/life-meter decomposition, sprite-domain
migration into the oracle schema, palette-epoch census across sprites, static negative-coverage over the whole
graphics domain. These are separate sessions; the schema already accepts them without redesign.

## Closure matrix — see AGENTS_LOG + final response.

## Session 2 (2026-08-26): two plane corrections + sprite-domain progress

### Correction 1 — Layer-B selector vs effective palette-RAM bank (RESOLVED, not contradiction)
`pc080sn.cpp get_tile_info`: `tileinfo.set(0, code, attr & 0x1ff, TILE_FLIPYX((attr&0xc000)>>14))`. The PC080SN
tile color = `attr & 0x1ff` is a **direct** palette group (no layer base offset). Therefore Layer-B tile selector
`0x002` = **effective palette-RAM bank 0x002**. The prior "bank 48 (0x30)" is a **separately-loaded** bank
(FUN_0003b9f8 @0x4FE62; also the sprite colbank base 0x30) — a real load, but NOT what R1/P1 BG tiles select.
Both facts preserved; `plane_palette_banks.json` now carries `pc080sn_color_selector` + `effective_palette_ram_bank`.
No prior marked "wrong". Layer-B stays bank 0x002 (correct).

### Correction 2 — content epoch vs usage/coexistence epoch
`palette_content_epoch = epoch_00` (16-color words never change in R1/P1; stage-load; Layer B single distinct
state across records 0-15). Separately, `palette_usage_epoch` = **per-segment active-bank set** derived from the
tile `records` fields. Max simultaneous Layer-A banks in any R1/P1 segment = **6** (NOT the union of 11).
Recorded in oracle `coexistence.json` (`layer_a_active_banks_per_segment`). The earlier "all 11 coexist" (union)
is corrected to per-segment ACTIVE sets, so future CRAM planning uses real simultaneity.

### Sprite-domain progress (partial)
- Remaining producers: **0x0234 / 0x0236 / 0x0266 = NOT REACHABLE IN R1/P1** (appear only at section 0x11 /
  record 17 = Phase-3 boss area; Tighe continued past Phase 1). **0x0DAB** = actor_2c8 enemy at sections 6-11,
  UNRESOLVED pending owned-record isolation.
- Oracle `objects.json` created: 20 stable-ID sprite objects (7 enemies + Rastan + 4 weapons + 3 hazards +
  1 effect + 0x0DAB + 3 out-of-scope). Enemies/player/hazards/effect PROVEN; weapon names captured but cell-
  separation OPEN.

### NOT closed this session (honest boundary — real remaining work)
- **Weapon cell separation** (sword/axe/flame_sword/flail): the blade cells are interleaved with Rastan's
  animation cells; clean separation requires the **arcade equipped-weapon state variable** (a WRAM value) to bin
  frames by weapon. That variable is not in the saved capture and was not located in a bounded Ghidra pass.
- **Gameplay item pickups**: same dependency (weapon-state + pickup-actor isolation).
- **Item-page lexicon**: requires a FRONTEND/attract capture (item page is not in the R1/P1 gameplay capture).
- **HUD/life-meter decomposition**: records 0-45 located; life-meter element not yet isolated.
- **Static negative sprite coverage**: not performed.
These are the next session's work; the oracle schema already accepts them.

## Session 3 (2026-08-26): 0x0DAB correction + Layer-B usage completion

### Invalid 0x0DAB render WITHDRAWN
`producer_0DAB.png` was rendered from OBJ records 140-239 (a multi-actor broad composite) — INVALID as 0x0DAB
evidence. Quarantined to `contact_sheets/producer_0DAB_INVALID_broad_composite_140-239.png`.

### 0x0DAB exact ownership + corrected classification
From `owners.csv`: base 0x0DAB = actor_2c8 **slot 0** (addr 0x10C2C8), **state 00, attr27 00**, sections 0x06-0x0F.
Slot-0 owned OBJ records = **140-149**. Rendering ONLY those records at every 0x0DAB frame yields **zero nonzero
on-screen records** — records 140-149 are blank whenever slot 0 holds base 0x0DAB. Therefore **0x0DAB emits NO
graphics** in R1/P1: it is an actor_2c8 slot-0 dormant/pending state, NOT a graphics-bearing sprite object.
Oracle: `object:enemy.dab_0dab` → `object:unresolved.slot0_state_0dab`, category OTHER, non-rendering. Prior ENEMY
classification WITHDRAWN (it came only from the invalid broad composite).

### Layer-B usage/coexistence completed
`layer_b_active_banks_per_segment` populated from `plane_b_state_timeline`: all 16 segments → `[0x002]`.
Union fields renamed unambiguously: `layer_a_legal_banks_union` (all 11 banks used SOMEWHERE, NOT simultaneous),
`layer_a_active_banks_per_segment` (≤6 simultaneous), and the Layer-B equivalents. Terminology note added.

### Sprite closure continuation — status
Player compositor located: `FUN_00041f5e` (arcade 0x041F5E) copies the player block A5+0x170/0x11B2 → OBJ records
via `FUN_00041f7a`. The equipped-weapon graphic selection is UPSTREAM in the player animation state machine that
fills A5+0x11B2; the equipped-weapon state variable requires a dedicated state-machine trace (not completed this
session). Weapons/items/item-page/HUD/life-meter/static-coverage remain OPEN — genuine remaining work, not fabricated.

## Session 4 (2026-08-26): equipped-weapon state variable PROVEN
Traced backward from the player producer (FUN_00041f5e / player_body_constructor_540cc @0x540CC). The equipped-
weapon selector is **A5+0x138C**: player_body_constructor_540cc branches `cmpi.w #0x2/#0x3/#0x1,(0x138c,A5)` to
select weapon sprite-table sets — value 0 (else) -> 0x5BB40/0x5BB80, value 1 -> 0x5BCC0/0x5BD00, value 3 ->
0x5BC40/0x5BC80, value 2 -> branch@0x540DE. Values 0-3 = four weapons. An immediate writer sets #0x2 at 0x519F6.
Secondary player pose sub-tables (0x5B640/0x5B660/0x5B6D0.. selected by A5+0x12F0/0x111A) are direction/crouch, not weapon.

**Consequence:** weapon/body cell separation is now STATICALLY tractable — decode the 4 weapon sprite-table sets at
0x5BB40 / 0x5BCC0 / 0x5BC40 / (0x540DE branch) and render each to map value->weapon-name (sword/axe/flame_sword/flail)
and extract weapon-specific vs shared body cells. This is the precise next step (bounded static decode; the owners.csv
capture did NOT record A5+0x138C, so the static table decode — not the capture — is the path). Oracle weapon objects
updated with this provenance; status upgraded from "needs weapon-state var" to "var proven, table decode pending".

### Honest continuation state
Remaining sprite domains still OPEN: weapon-table decode + value->name mapping; gameplay item pickups; item-page
lexicon (frontend capture); HUD decomposition; life meter; static negative coverage. The weapon-variable unblock
(A5+0x138C + the 4 table addresses) is the irreplaceable evidence from this session.

## Canonical Original-Arcade Weapon Terminology (2026-08-26, LOCKED)
Canonical equipped weapons: **SWORD · AXE · HAMMER · FIRE SWORD**. Terminology corrections (LOCKED by Tighe +
item-information page): **Flame Sword → FIRE SWORD**, **Flail → HAMMER**. "Mace" is never canonical. Legacy names
kept only as `legacy_aliases` provenance. A semantic item and its representations (item-page / gameplay pickup /
equipped / HUD / projectile) are distinct and not assumed to share physical patterns. Oracle IDs canonicalized:
`object:weapon.sword|axe|hammer|fire_sword`; `object:weapon.flame_sword`→`fire_sword`, `object:weapon.flail`→`hammer`.
Historical AGENTS_LOG entries left unchanged (append-only). `terminology_corrections.json` records the mapping.

## Equipped Weapon Static Closure
Selector **A5+0x138C** (reader `player_body_constructor_540cc` 0x0540CC). Value→graphics-table (each A3/A4 pair 0x40
apart, consumed by FUN_00054326 as an **anim-frame-INDEX** table: byte `(0,A3,anim_ctr)` → A5+0x1244 → FUN_00054492):
- **value 0 → 0x5BB40/0x5BB80**, distinctive frames {0x25,0x26} — **SWORD** (PROVEN: default/else branch, start weapon)
- **value 1 → 0x5BCC0/0x5BD00**, frames {0x40}
- **value 2 → 0x5BBC0/0x5BC00**, frames {0x49,0x4A,0x46} (value-2 path RESOLVED; writer 0x0519F6 `btst #9,D0`)
- **value 3 → 0x5BC40/0x5BC80**, frames {0x47,0x48,0x3B}
Writer ledger: only one immediate writer found (0x519F6 → value 2, via a flag bit). Values 1/3 are set by pickup
handlers not fully enumerated this session; value 0 is init/default.
**Value→canonical-name mapping:** value 0 = SWORD PROVEN. Values 1/2/3 = AXE/HAMMER/FIRE SWORD in unproven order —
tables + distinctive frames are proven, but the numeric→name assignment needs either the pickup-handler item-identity
trace (flag-bit → item) or decoding the frame→composite table (A5+0x1244 → 0x54492) and rendering. NOT completed.
`player_weapon_states.json` records the proven mapping + pending name status. Capture epochs UNAVAILABLE (owners.csv
did not record A5+0x138C). Common-body vs weapon-cell separation and per-weapon palette follow once names are mapped.

## Equipped Weapon — composite format decoded; blade producer still open (2026-08-26)
`FUN_00054492` (0x54492) composite format PROVEN: base **0x5BD40**, frame N → `offset=u16(0x5BD40+N*2)` → piece list;
4 pieces × 6 bytes `[code(2), X(1), Y(1), attr(2)]`; flip 0x4000; Y += A5+0x10C0; code masked 0x3FFF.
Decoding the A5+0x138C distinctive frames yields: common body cells **0x4DB-0x4E6**; val1 adds 0x59E/0x59F; val3 adds
0x582/0x583; val2 adds nothing distinct. **Rendering shows these "extra" cells are alternate BODY poses, not weapon
blades.** Conclusion: the A5+0x138C tables drive the player's per-weapon body ANIMATION (swing/thrust pose), while the
actual equipped-weapon BLADE graphic appears to be a **separate attachment producer** not present in this player body
composite. Therefore value→canonical-name (1/2/3 → AXE/HAMMER/FIRE SWORD) is NOT resolved this session, and per-weapon
blade cells/palette are not closed. Value 0 = SWORD remains proven (default/init). EQUIPPED WEAPONS = NO.
Next: locate the equipped-weapon blade producer (separate from the player body composite) — trace the OBJ records the
attack emits beyond the body block, or the weapon-attachment routine keyed on A5+0x138C.

## Bad Item-Image Reference Quarantine (2026-08-26)
User-supplied item-information-page images contain KNOWN wrong palettes and/or wrong tiles. They are **NOT** graphics
authority and MUST NOT source any palette/pattern/tile/selector/composition/equivalence evidence. They may seed
canonical NAMES only (separate evidence domain). Real item-page graphics must be recovered independently from original
arcade ROM/code/MAME. Recorded in `bad_item_images_quarantine.json`.

## Equipped Weapon — writer ledger (2026-08-26)
Only ONE literal store to A5+0x138C exists in ROM: **0x0519F6** `move.w #2,(0x138c,A5)` gated by `btst #9,D0`
(weapon-flag decoder). Value 0 = init/default (BSS zero) = SWORD. Values **1 and 3 have NO literal writer** — set via
an unlocated computed/flag path or unreachable. This blocks the preferred item→value→name proof for values 1/2/3, and
(with last session's finding that the blade is a separate producer) means EQUIPPED WEAPONS cannot be honestly closed
this session. Terminology remains canonical (SWORD/AXE/HAMMER/FIRE SWORD); value 0 = SWORD proven.
