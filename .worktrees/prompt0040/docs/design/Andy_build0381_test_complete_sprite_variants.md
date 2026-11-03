# Andy — Build 0381: Test Profile + Complete (code,bank) Sprite Variant Pipeline

**Agent:** Andy · Implementation / Build / Static Verification. **Gameplay baseline: Build 0380.**
**Andy performed NO gameplay/visual verification — authority: TIGHE.** No H25.

> **Build-number note (standing imperative):** this task produced three numbered builds. Build **0381**
> and **0382** are preserved on disk as `canonical=FAIL` evidence (0381: a stale-object/working-tree
> boundary artifact + the coverage invariant; 0382: the coverage invariant, clean). Build **0383** is the
> `canonical=PASS` candidate after both duplicate coverage invariants were updated. No numbered artifact was
> deleted, withheld, or reused. The prompt explicitly authorizes advancing 0381→0382→0383 when another
> candidate is needed.

## 1. Phase 0 baseline
Read `PROMPT_TEMPLATE.md`, `RULES.md`, `ARCHITECTURE.md`, `CLAUDE.md`,
`PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`, then `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`,
`CLOSED_ISSUES.md` (ledgers known stale; used as priors, current state from AGENTS_LOG + Sept design docs).

Relevant priors: **KF-043** (sprite bank 0x33→CRAM line ownership), **KF-046** (scene,bank→line route table),
**KF-068/KF-069/KF-070/KF-074** (native sprite pipeline: code-keyed 49-cell residency, emit-on-miss,
double-buffered SAT; colbank/effective-bank resolved at emit from `pc090oj_sprite_ctrl_shadow`), **KF-077**
(gameplay PC090OJ output is native). No CONFIRMED/STRONG finding contradicted.
**Classification: EXTENDING** (extends the offline reindex asset + the native residency selection at the same
emit boundary; adds no chip mirror/emulation). **KNOWN_FINDINGS impact: Option A** (no new durable
system-behavior finding; the runtime mechanism is captured in the manifest/`.inc` + this doc).

## 2. Build-0380 baseline
Build 0380 Rastan body palette USER-ACCEPTED. `object:player.rastan` and CRAM must not change.

## 3. Test.json source + SHA (Step 1 freeze)
- Editable source: `analysis/graphics_optimizer/editor_policy/Test.json`, **SHA-256
  `31dedf43a15994ca65cfd26f6f130f58e44dfe2c8be46dd8304fe24c50819fa1`**, profile_id `Test`, **revision 25**.
- Frozen Build-0381 snapshot: `build/rastan-direct/build0381/Test.snapshot.json`, **same SHA
  `31dedf43…`**. Editable Test.json NOT mutated during the build. Makefile `EDITOR_LAYERA_SNAPSHOT` now points
  at the build0381 snapshot; the palsel-LUT generator and both reindex generators consume it.
- Prior (Build-0380 input) snapshot: `build/rastan-direct/build0379/Test.snapshot.json`, SHA
  `2c6630a0…`.

## 4. Exact Test policy changes vs Build 0380 (Step 2)
Authoritative diff of the two snapshots (not screenshots):
- **A. CRAM (`target_palette_lines`): UNCHANGED.**
- **B. source-index mappings: no existing map changed.** Every enemy map, `object:player.rastan`,
  `cave_block`, and all plane mappings are byte-identical.
- **C. newly authored weapon objects (ADDED):** `object:weapon.sword` (line 0, 4-entry map),
  `object:weapon.axe` (line 0, 8), `object:weapon.hammer` (line 0, 6), `object:weapon.fire_sword` (line 0, 5).
- **D. enemy mapping changes: NONE.**
- **E. context-local overrides (`context_policies`): UNCHANGED.**

Tighe's only authoring change since Build 0380 is **adding the four equipped-weapon palettes.**

## 5. Rastan retention proof (Step 3)
- Test-profile `object:player.rastan` map is byte-identical to Build 0380 (§4B).
- Rastan target CRAM entries unchanged (§4A).
- Complete 344-cell player-body transform re-resolves; independent verifier reports **rastan base codes 344,
  mismatched 0**.
- Rastan cells (0x076–0x610) are disjoint from the divergent variant block (0xA73–0xAA2) and from all weapon
  cells, so the variant machinery cannot touch Rastan. **Rastan mapping retained: YES. Rastan palette
  retained: YES. No shared CRAM entry changed.**

## 6. Complete enemy semantic corpus (Step 8)
Consumed `analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv` (complete, valid cells): Lizardman 91
(0x36), Valkyrie 18 (0x32), Four-Armed Insect 106 (0x3A), Chimera 148 (0x34), Flying Demon 112 (0x35, two
components), Small Bat 3 (0x3E), Large Bat 14 (0x3E). No representative-subset regression.

## 7. Weapon authored mappings (Step 9)
Consumed `h24_player_weapon_cells.tsv`. Genuine (non-artifact) unique cells: SWORD 10, AXE 12, HAMMER 17,
FIRE SWORD 10, each baked under bank 0x33 with its authored `object:weapon.*` map (weapon pixels use the
weapon map, never Rastan's body map). Weapon codes are disjoint from Rastan and enemy codes.

## 8. Fire Sword vertical-flame investigation (Step 9 sub)
Inspected the proven weapon corpus/render contract. The corpus contains no additional vertical-state flame
component that is mechanically provable from the existing arcade weapon tables and uses the already-authored
Fire Sword palette. No flame cells were invented and no palette choice was changed. If a vertical flame is a
genuinely separate semantic object/palette, it requires new user authoring. **Result: unresolved auxiliary
effect, documented follow-up (OPEN-006 context); the build was NOT blocked on it.**

## 9. Fire Sword "frame 69" investigation (Step 9 sub) — RESOLVED (case B, mechanical corpus fix)
The weapon browser's trailing "frame 69" is a **decode artefact**, not a canonical weapon frame:
- It is the only frame after a 54→69 gap (frames 0..54 then 69), i.e. not part of the contiguous animation.
- **HAMMER frame 69 = three copies of code 0x0003** (the known blank/contamination tile) — degenerate.
- SWORD/AXE/FIRE SWORD frame 69 cells alias **player-body** codes (0x0B2/0x0B8/0x0BE/0x10C match Rastan
  leg/torso slots 7/9/10/12) and enemy-shared codes (0x0D0/0x0DC/0x0EE/0x130).
- With frame 69 INCLUDED, those four body-aliased codes produce **4 unresolvable same-(code,bank 0x33)
  collisions** between `object:player.rastan` and the weapons (identical runtime identity, different maps).
- With frame 69 EXCLUDED, **zero unresolvable collisions remain**, and the group-A codes vanish from bank
  0x33 entirely (they were only frame-69 artefacts).

**Mechanical fix:** `gen_reindexed_pc090oj.py` excludes `frame_index == 69` from the weapon corpus (case B).
This is the underlying player-slot overrun the browser mislabels as "frame 69"; it is not a real 43rd weapon
frame. Tighe's palette choices were not changed. The prompt's "43 frames" count therefore includes this one
artefact frame; the genuine weapon frames number 42.

## 10. Cross-bank collisions (Steps 4/11) — under Tighe's actual authored maps
Computed every (code, effective_bank) transform from the complete corpus + Test.json + raw pixels:
- **52 multi-bank codes with frame 69; 48 without.** All 48 are the single contiguous **enemy anim block
  0xA73–0xAA2** under banks **0x34 (chimera) / 0x36 (lizardman) / 0x3A (four_armed_insect)**.
- **All 48 diverge** (0 dedup): each code's three per-bank transforms are byte-distinct (verified all-distinct
  = 48/48). lizardman(0x36) and four_armed(0x3A) share CRAM line 1 but differ in index_map → distinct bytes,
  so four_armed genuinely needs its own variant.
- **0 unresolvable collisions** after the frame-69 fix; every divergent pair is distinguishable by effective
  bank at emit time.

## 11. (code,bank) generator implementation (Steps 4/5/6)
`tools/graphics_editor/gen_reindexed_pc090oj.py` (rewritten, durable pipeline, not a parallel generator):
- Base region: one 128-byte base cell per code at `code*128`; for the divergent block the base bank is **0x36
  (lizardman = Round-1, the common case that needs no runtime variant path)**. All non-divergent codes
  (incl. all 344 Rastan cells and all weapon cells) are byte-identical to the code-indexed model.
- Appends **96 variant cells** (48 chimera 0x34 + 48 four_armed 0x3A) after the 4096-cell base region. Cell
  model preserved: `code*128`, 16×16 = four 8×8 subtiles, index 0 transparent, full-cell transform.
- Divergent variants are never collapsed/overwritten; identical transforms would deduplicate (0 here).
- Fails the build loudly if the divergent set is not a single contiguous block under the expected banks
  (guards the compact runtime index).
- Region grows 524288→536576 bytes (4096→4192 cells, +0x3000).

## 12. Semantic variant index (Step 6) + runtime O(1) selector (Step 7)
Generated **`apps/rastan-direct/out/pc090oj_sprite_variants.inc`** (constants + a 128-byte
`pc090oj_variant_bank_slot` table: effective_bank→variant-slot base, 0xFF = base cell) and machine-readable
`build/regions/pc090oj_variant_index.json`.

Runtime selection in `pc090oj_hooks.s` (native SAT emit path, `.Lnq_emit_entry`), bounded **O(1)**, no
linear scan, no string lookup, no actor branching, no per-pixel work:
1. Reuses the **same effective-bank** the palette-line lookup uses at `.Lnq_hit`:
   `bank = (attr & 0x0F) | ((pc090oj_sprite_ctrl_shadow & 0x00E0) >> 1)` — the existing PC090OJ palette
   selection identity (no second bank oracle).
2. One range test (`SPRITE_VARIANT_LO..HI`) + one `pc090oj_variant_bank_slot[bank]` byte.
3. On a variant, folds it into the residency key / tile-DMA worklist code as `SPRITE_VARIANT_KEY_MARK(0x2000)
   | vi`; the residency reverse key normalizes to the free `SPRITE_VARIANT_KEY_NORM(0x1080) + vi` directory
   range (no directory resize — 512 entries still cover it, no HUD-white overlap); the VBlank tile-DMA
   sources the appended cell at `rastan_pc090oj + SPRITE_VARIANT_REGION_OFF + vi*128`.

**No runtime recolor / no nibble rewrite** — variant bytes are pre-transformed offline. **No PC090OJ
emulation / object-RAM mirror / device.** Because the residency key is variant-specific, two on-screen
sprites sharing a code under different banks occupy distinct VRAM cells (no wrong-art aliasing — KF-069/070
hazard respected). Confirmed present in the built ROM by disassembly:
`lea 0x8127c <pc090oj_variant_bank_slot>`, `btst #13` marker checks, `addi.w #4224` (0x1080) at the remap +
the three reverse-key normalization sites.

## 13. Independent verifier (Step 10)
`tools/graphics_editor/verify_reindexed_pc090oj.py` (rewritten) recomputes every base and variant cell from
raw pixels + the frozen maps and asserts equality against the built region. Result on the Build-0383 region:
`total (code,bank) requirements 889 · unique codes 793 · base cells 793 · variant cells 96 · dedup 0 ·
cross-bank divergent 48 (all-distinct 48, bad 0) · mismatched 0 · incomplete 0 · unexpectedly-raw 0 · stray 0
· RASTAN base 344 mismatched 0`. **VERIFY: PASS.**

## 14. Complete coverage counts (Step 11)

| Object | Required variants | Generated | Missing | Mismatch | Raw non-identity |
|---|---|---|---|---|---|
| Rastan (object:player.rastan) | 344 | 344 | 0 | 0 | 0 |
| Sword / Axe / Hammer / Fire Sword | 10 / 12 / 17 / 10 | same | 0 | 0 | 0 |
| Lizardman (0x36) | 91 | 91 | 0 | 0 | 0 |
| Valkyrie (0x32) | 18 | 18 | 0 | 0 | 0 |
| Four-Armed Insect (0x3A) | 106 | 106 | 0 | 0 | 0 |
| Chimera (0x34) | 148 | 148 | 0 | 0 | 0 |
| Flying Demon (0x35) | 112 | 112 | 0 | 0 | 0 |
| Small Bat (0x3E) | 3 | 3 | 0 | 0 | 0 |
| Large Bat (0x3E) | 14 | 14 | 0 | 0 | 0 |

Cross-bank divergent: 48 codes (0xA73–0xAA2), 96 appended variant cells (chimera + four_armed), all distinct.

## 15. Manifest correction (Step 13)
`docs/design/rastan_actor_graphics_manifest.json` → `authoritative_keys.player_composer` updated to the full
H24 architecture: `0x540CC → 0x54326`; UPPER `A5+0x1244→0x54492→0x5BD40`; LOWER `A5+0x1246→0x546A8→0x5C466`;
WEAPON overlay `A5+0x12FA→0x54598→0x5CD8A/0x5D346/0x5D666/0x5D068`. The detailed `player_render_architecture`
data was not altered.

## 16. Build 0380 → 0383 diff (Step 16)
Fixed-offset byte comparison is dominated by two effects: (a) the appended 96 variant cells shift the entire
arcade program after `rastan_pc090oj` (0x812fc) by +0x3000, so all downstream bytes "differ" as pure
relocation; (b) the working tree carried **pre-existing uncommitted tooling changes from prior sessions**
(confirmed by the session-start `git status`; e.g. `compile_pc080sn_genesis.py`, `shift_table_patcher.py`,
`tilemap_hooks.s`, `palette_hooks.s`, `fg_tile_cache.s`), so a raw 0380-artifact↔0383-artifact diff includes
drift predating this task. Classified by intent:
1. **Authored CRAM changes:** none (Test.json CRAM unchanged).
2. **Authored index-map changes:** weapons added (bank 0x33 base cells); enemy coverage completed.
3. **Offline sprite variants:** +96 appended cells (0x3000).
4. **(code,bank) variant index/table:** `pc090oj_sprite_variants.inc` + `pc090oj_variant_bank_slot`.
5. **Bounded runtime selector:** `pc090oj_hooks.o` variant remap + reverse-key/DMA edits.
6. **Generated manifests/provenance:** editor manifest, variant index, palsel LUT (re-derived from the new
   snapshot; bank→line routing unchanged since only bank-0x33/line-0 weapons were added).
7. **Build/header/checksum:** header/checksum bytes.
8. **Manifest documentation correction:** §15.
9. **Other:** region relocation shift (+0x3000) and pre-existing working-tree tooling drift.

**Coverage invariant:** `CANONICAL_TOTAL_GENESIS_BYTES_COVERED` updated `0x1A4EB8 → 0x1A7EB8` (+0x3000, the 96
variant cells) in both `postpatch_startup_rom.py` and `verify_canonical_rom.py`. `opcode_replace` count
**unchanged at 230** (no new opcode_replace; no NOP/RTS).
**This task modified NO gameplay-logic source** (no movement/collision/rope/scroll/scene/animation-selection);
the only `apps/rastan-direct/src` file this task edited is `pc090oj_hooks.s`.

## 17. Complete five-ROM family (Build 0383 — canonical=PASS candidate)

| Variant | Path | Size | SHA-256 |
|---|---|---|---|
| base | dist/rastan-direct/rastan_direct_video_test_build_0383.bin | 1736376 | 7dc486a426397c819a8a1816fc38ea6d6d84e7707e009ec81a2a2cdf637ca3a7 |
| _c | …_0383_c.bin | 1736376 | 639085bba3ff531e0b73e80cdf54245d560895573b42a2d3186f298bde920fea |
| _d | …_0383_d.bin | 1736376 | 08ee6dd7910a700f28eb417c57050270c5a2e2f0c39f2037564665a9bc1a5bfc |
| _do | …_0383_do.bin | 1736376 | d17845182862b63e150661308065471367deebdeeb28703895eddb91d27cd1bf |
| _s | …_0383_s.bin | 1736376 | 9bcaf2dabb96f1c048e630af32a2506eb2a6fa60cec7570598f07e67d4fee10c |

Preserved failing evidence (per the standing imperative, not deleted):
- **0381** `canonical=FAIL entry=PASS epoch=FAIL` — five variants, 1736376 B (base SHA
  `dd711298564533f553d6d730f0a77f20f463e55cf91f9595b2220af5e5d3f674`). Failure: a working-tree
  `fg_tile_cache.o`/boundary staleness (unrelated PC080SN artifact) plus the un-updated coverage invariant.
- **0382** `canonical=FAIL entry=PASS epoch=FAIL` — five variants (base SHA
  `…` recorded in ledger). Failure: coverage invariant only (clean build; boundary consistent).
`verify-variant-set` PASS for all three. Counter 380 → 383.

## 17b. Gates (Step 15)
Build 0383: canonical gate **GATE_PASS**; boot guard PASS (pre & post); start-to-gameplay **entry=PASS**;
`verify-variant-set` PASS; independent reindex verifier PASS. **`epoch=FAIL`** = the Phase-1 seven-epoch gate,
which is FAIL on every recent build (0378–0382) — a pre-existing gate state, not introduced by this task; the
ROM is numbered + preserved per the standing imperative. A 30s Genesis-NTSC smoke trace ran as part of the
standard release process (build sanity only; Andy performed no manual gameplay verification).

## 18. Architecture compliance (policy §9 checklist)
- Semantic boundary, not chip-write level: **yes** — the variant is selected at the existing native
  actor→SAT emit boundary from arcade-owned effective-bank state.
- Complete chip-specific block bypassed: the PC090OJ object-RAM record/scan tail remains retired (KF-074); no
  new chip mirror/shadow/device/projector introduced.
- Consumes arcade semantic state (effective bank + code), not chip-shaped state: **yes.**
- Mirrors/shadows/virtual RAM/dispatchers/projectors introduced or retained: **none.**
- Retained transitional compatibility: **none new** (frontend `pc090oj_object_ram` unchanged).
- Arcade owns gameplay/frame/VBlank: **yes** (selector is an emit-time helper returning normally).
- Genesis helper directly generates final SAT/VRAM output: **yes.**
No Genesis loop / frame authority / boot re-entry / lifecycle / scaffolding / runtime recolor. **CONFIRMED.**

## 19. USER MUST VERIFY — TIGHE
Load a Build-0383 variant and verify: (1) Rastan body unchanged/correct; (2) Sword/Axe/Hammer/Fire-Sword
palettes during swings; (3) Fire Sword held vertically (flame still absent — documented unresolved auxiliary
effect); (4) Flying Demon complete animation; (5) Small/Large Bat; (6) Four-Armed Insect + Chimera across
animations (the 0xA73 shared-anim block now bank-correct); (7) other enemies across frame changes.

## 20. Open/Closed Issues Impact
- **OPEN-006** (enemy/weapon palettes) advanced (complete enemy coverage + (code,bank) variants + weapons
  baked); not closed pending Tighe's visual verification.
- New OPEN item recorded: **Fire Sword vertical-state flame** is an unresolved auxiliary component requiring
  either arcade provenance of a separate flame producer or new user authoring (documented follow-up).
- None closed/deferred.

## 21. KNOWN_FINDINGS impact
**Option A — No new finding to index.** EXTENDING task; extends the offline reindex asset and the existing
native residency/emit selection (KF-068/069/074) at the same boundary. The (code,bank) variant mechanism and
the frame-69 corpus correction are captured in the generated manifest/`.inc`/index and this design doc.
