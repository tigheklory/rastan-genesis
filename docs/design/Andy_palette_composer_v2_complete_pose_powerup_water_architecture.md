# Palette Composer V2 — Complete Pose Corpus + Power-Ups + Authored Line-3 Water Animation

**Type:** Analysis / Architecture / Tooling (living document, maintained across tiers).
**This turn delivers:** mandatory build-number hardening (tooling-only, no ROM) + Tier 0 editor/compiler audit + the arcade waterfall palette-animation proof (Tier 5 mechanism). Authoring-dependent implementation tiers are scoped, not yet built.

## 1. Phase 0
- **Relevant priors:** KF-028 (embedded pointer relocation; the gameplay palette/BG/layout pointer tables incl. `0x059EC8` → `genesistan_palette_hook_59ad4`); Build-0331 partial-dynamic Line 2; Build-0333 Rastan bank-0x33 → route-lookup → Line 0. No CONFIRMED/STRONG contradiction.
- **Classification:** INFRASTRUCTURE (this turn: tooling hardening + architecture proof; no ROM behavior change).
- **OPEN/CLOSED impact:** advances OPEN-006 (enemy/Rastan palettes) architecture; none closed.
- **Contradiction status:** none.

## 2. Build-number overwrite hardening (DONE, verified)
**Root gap:** the Makefile release path wrote the counter but never recorded the produced number in `consumed_build_numbers.txt`, so a produced-then-deleted number could be reused (deleted file → overwrite guard passes; not in ledger → counter-behind guard passes). Two guards already existed and are correct: (a) refuse if `build_NNNN.bin` exists (line 303), (b) refuse if counter < max(existing files, ledger) (lines 288–298).
**Fix (tooling-only, no ROM behavior change):** the release recipe now appends `"<tag> PRODUCED <date> auto-recorded-by-release"` to the ledger immediately after writing the counter. Session builds 0330–0333 backfilled. **Verified:** with the ledger holding `0333` and a stale counter `332`, the counter-behind guard now REFUSES (`counter 332 behind consumed 0333`). Every future consumed number is permanent regardless of the counter or the file's later fate.

## 3. Terminology (locked, per Tighe)
- **Actor / Rastan "animation"** = distinct PC090OJ tile-piece **assemblies** (stand, walk frames, squat, jump/fall, up-thrust, down-thrust, attack, death). NOT palette cycling.
- **Water "animation"** = Layer-A tiles unchanged while selected **CRAM colors** cycle (palette animation).

## 4. Genesis palette ownership (preserve)
| Line | Owner | Notes |
|---|---|---|
| 0 | Test sprite | event-installed static |
| 1 | Test sprite | event-installed static |
| 2 | Layer B | partial-dynamic, arcade-authoritative (sunset). **Not for the waterfall.** |
| 3 | Layer A | 0–11 static Test; **12–15 = waterfall subset** (to become partial-dynamic authored) |

## 5. Tier 0 — editor/compiler audit
- **Editor:** `tools/graphics_editor/server.py` (1228 lines, model/API), `app.js` (582, UI). Current concepts: profile, sprite bank, sprite code, target Genesis line, source colors, authored entries, reindexed pattern, Layer-A segment/tile authoring, sprite palette authoring, ΔE/OKLab. Test snapshot at `build/rastan-direct/build0314/Test.snapshot.json`.
- **Compiler:** `gen_reindexed_pc090oj.py` (131) → `pc090oj_editor.bin` + manifest; `gen_reindexed_region.py`/`compile_editor_layera.py` (Layer A); `export_palette_policy.py` (161).
- **Current representation model is CODE-indexed** (not `(code,bank)`): manifest holds **124 codes across 7 banks** (0x32:8, 0x33:29, 0x34:11, 0x35:26, 0x36:35, 0x3A:10, 0x3E:5). Bank 0x30 (items, death burst) and the full player vocabulary are **not** represented. This is the additive gap: introduce first-class **Actor → Pose → (code,bank) pieces**, **Power-ups**, and **palette-animation** representations; move the compiler to `(code,bank)` variants with an O(1) runtime selector.
- **Additive-only requirement:** existing profile/decisions/IDs/exports/Test-snapshot must load unchanged; new schema extends `specs/palette_decisions.json` with stable IDs.

## 6. Tier 1A — Rastan census (STARTED; completion scoped)
- **Current coverage:** bank 0x33, **29 codes** — `138–159, 267–270, 629–631`. Correct poses (per Build-0333 playtest: neutral fall, one walk frame) use these.
- **Gap:** up-thrust, down-thrust, squat, standing lower-body render wrong → their piece codes are **not** in the 29-code set (or use a different effective bank). The player is **not** in `analysis/enemy_sprite_lexicon/families.json` (enemy-focused), so his complete vocabulary must come from a **direct Ghidra decode of the player PC090OJ representation/animation descriptors** (the player render path around the `.Lnea_fam_bases` player entry). **Next step:** enumerate every player pose → emitted piece codes + effective bank + flip, and diff against the 29 covered codes to produce the 100%-coverage table. Do NOT infer from screenshots or a gameplay trace.

## 7. Tier 2/3 — power-up + actor censuses (scoped)
- Enemy actors ARE enumerated in `families.json` (66 families, Ghidra-sourced: `representative_codes`, `proven_effective_palette_banks`, `animation_state_values`, `composer_tables`, `round_phase_presence`) — the authoritative source for the full R1/P1 pose set per actor and for power-up/effect codes. Power-ups (gems, potions, mantle, armor, shield, gold sheep, ring, rod, necklace) and the enemy-death burst are **bank 0x30**, not in the reindex; author from arcade palette data, never screenshots.

## 8. Sprite color budget (hard constraint)
Only Lines 0/1 are sprite lines. Every pose/power-up/effect + all of Rastan must pack into L0/L1 (15 entries each). The compiler must solve packing per `(code,bank)`; never silently merge two simultaneously-used distinct colors — STOP and report the conflict (grayscale/alt offered to Tighe, never auto-chosen).

## 9. Tier 5 — arcade waterfall palette-animation mechanism (PROVEN)
The PC080SN has **no palette**; colors live in system palette RAM (`0x200000`, xBGR-555) written by the 68000. The waterfall is software palette cycling:
- **Driver:** ticked each gameplay frame from render dispatch `FUN_00041F30` → `FUN_00059882`/`FUN_0005988C` → **type 8** `FUN_00059962` / **type 9** `FUN_000599B2`. Animation **type** selector at `a5+0x12EE` (8/9), frame counters at `a5+0x12E8`/`0x12EA`. Update **every 8 game-frames** (`counter & 7 == 0`); type 9 updates **4 banks**. Counters wrap → **3 frames (type 8) / 4 frames (type 9)**.
- **Loader `FUN_00059AD4` = our `genesistan_palette_hook_59ad4`.** Inputs `D0`=palette bank, `D1`=frame index (`counter>>3`), `A0`=ROM frame table. Loads 16 words `A0 + frame*0x20`, converts 0RGB444→xBGR555, writes bank `0x200000 + bank*0x20`.
- **`0xFFFF` = keep-mask:** frame entries equal to `0xFFFF` are skipped → only the animated indices change (partial-dynamic, encoded in ROM data). Our hook already honors this (`cmpi.w #0xFFFF; beq`).
- **ROM data:** per-segment target bank(s) `0x59A98` (type 8, 1 word/seg: `0x14,0x0F,0x16,0x03,0x07,0x09…`) and `0x59AA4` (type 9, 4 banks/seg: `0x1A–0x1D…`); frame color tables `0x59B1A` (type 8) / `0x59B7A` (type 9); segment index from `a5+0x118`.

## 10. Tier 5B — current Genesis disconnection (PROVEN)
The arcade water animation still calls `hook_59ad4` every 8 frames with the water bank, but `hook_59ad4` **rejects banks ≥ 4** (`cmpi.w #4,%d0; bcc .L59_done`) — and every water bank except `0x03` is ≥ 4; `0x03→Line 1` is additionally blocked by the post-0332 scene-1 Line-2-only gate. So the arcade's per-frame water writes are discarded and Line-3 indices 12–15 hold their static installed values → frozen waterfall. **First divergence: producer rejection in `hook_59ad4` (banks ≥ 4 unrouted).**

## 11. Tier 5A/5C — SEGMENT-11 WATERFALL INSTANCE (PROVEN)
Distinct from §9 (general engine): the R1/P1 waterfall is proven to be the **type-9** animation.
- **Type = 9** (teal). Proof: the type-9 frame table `0x59B7A` decodes to teal/cyan (`0x08cc=R8GcBc`, `0x0488=R4G8B8`, `0x06aa=R6GaBa` in 0RGB444 = low-R/high-G/high-B); the type-8 table `0x59B1A` is warm/fire (`0x0f70=RfG7B0`, `0x0fff` white). Water is unambiguously type 9.
- **Counter:** `a5+0x12EA`; **interval:** every 8 game-frames (`& 7 == 0`); **frames:** 4 (`counter>>3 & 3`, wrap 0x1F).
- **Bank table:** `0x59AA4` (type 9, 4 banks/segment). Water banks are `0x1A,0x1B,0x1C,0x1D` (the type-9 driver reloads all four every step; some segments substitute the first bank). **Frame table:** `0x59B7A`.
- **Only arcade palette indices 14 and 15 animate** — NOT 12–15. Indices 0–13 are `0xFFFF` (keep). Exact 4-step values (0RGB444):
  | Step | arcade idx14 | arcade idx15 |
  |---:|---|---|
  | 0 | 0x08cc | 0x0488 |
  | 1 | 0x06aa | 0x06aa |
  | 2 | 0x0488 | 0x08cc |
  | 3 | 0x06aa | 0x06aa |
  A 2-color teal shimmer swapping idx14↔idx15 (steps 0/2 opposite; 1/3 identical mid-teal). **So the authored Genesis animated set is 2 entries, not 4** — 12/13 are static water base; only two entries cycle.
- **Current Genesis disconnection (PROVEN):** `hook_59ad4` rejects banks ≥ 4 (`cmpi.w #4,%d0; bcc .L59_done`); all water banks (`0x1A–0x1D`) are ≥ 4 → the arcade's per-frame water writes are discarded → Line-3 stays static. First divergence = producer-side bank rejection.
- **Source→target mapping — BLOCKED at an authoring boundary (STOP for the water tier).** The offline Layer-A reindex applies a **per-tile `index_map`** (`compile_editor_layera.py`: `tpx = im.get(v,v)`), and those maps are **inconsistent across water tiles** — e.g. `LA-0578 {9→15,10→13,15→12}`, `LA-0582 {10→13,11→15,12→14,15→12}`. So the arcade's animated source entries 14/15 do **not** map to a single fixed Genesis Line-3 entry across the water tiles. There is therefore **no clean `arcade 14/15 → Genesis L3 X/Y` correspondence in the current reindex**, so the runtime cannot yet be wired without re-authoring the water tiles with a **consistent** index_map that sends arcade 14/15 to two fixed Genesis Line-3 entries. This is a genuine authoring/re-reindex decision for Tighe (Build D), not something to invent.

## 12. Runtime water design (scoped, no native timer)
Arcade owns timing (the 8-frame counter + frame index reach `hook_59ad4` for free). Enable water = route the proven Segment-11 water bank(s) to **Line 3** in `hook_59ad4` (past the ≥4 rejection and scene-1 gate) as a **partial-dynamic subset** (only the mapped 12–15, `0xFFFF` preserves 0–11), then either pass arcade colors or substitute Palette-Composer authored per-step colors keyed to `D1`. Change-detection commits only real changes (Sonic-style). **No Genesis-native water timer, no full-line rewrite, ≤4 target entries, O(1).**

## 13. 512-color picker (scoped)
Genesis CRAM `0BBB0GGG0RRR0` = 512 legal colors. Add an additive picker exposing all 512, showing the current authored CRAM word + RGB + **the arcade reference color/provenance** alongside. Authoring authority = Tighe (any of 512); reference authority = arcade data (never screenshots). Preserve existing hex/RGB/HSL/ΔE/OKLab.

## 14. Tier roadmap (delivery)
- **Build A:** editor schema (Actor→Pose→(code,bank)) + complete Rastan corpus + `(code,bank)` compiler variants + O(1) selector.
- **Build B:** power-ups + enemy-death burst first-class representations.
- **Build C:** remaining R1/P1 actor poses.
- **Build D:** Segment-11 proof + partial-dynamic Line-3 authored waterfall + 512-picker + water-step matrix UI.
Each tier: sequential numbered build, all gates PASS, prior fixes preserved, STOP-for-authoring allowed.

## 15. USER MUST VERIFY (this turn)
Nothing visual changed (no ROM produced). The only change is the Makefile release path (auto-records consumed numbers) — the next numbered build will exercise it and append to the ledger.

## 16. Deferred / preserved
Build-0328 terminators, event-driven Lines 0/1/3, Layer-B sunset, `59ad4` bank-2 partial-dynamic, no every-VBlank reassert, Rastan bank-0x33 route, Segment-11 pattern reuse policy, seven Plane-A epochs, HUD mode 2 — all preserved. Vertical-noise, late lizard, cave/Segment-7 — deferred (observation ≠ scope).

## Experimental Genesis Waterfall Trial (Build 0334)
- **Build:** 0334, SHA `61730a60b81d4b03b3d14b3893f031e1660b33dec3354a3637604d5b5751a261`. **Experimental status:** NOT a permanent mapping; no Palette Composer policy change; no KNOWN_FINDING promotion.
- **Arcade type-9 event:** driver `FUN_00041F30 → FUN_000599B2 → FUN_00059AD4` (= `hook_59ad4`); counter `a5+0x12EA`, every 8 game-frames, 4 frames, frame table `0x59B7A`; only arcade indices 14/15 change; `0xFFFF` keep elsewhere.
- **Candidate source→target mapping (identity, evidence-picked):** arcade idx14 → **Genesis L3:14**; arcade idx15 → **Genesis L3:15**. Rationale: among the Test Layer-A usages, source 14 maps to L3:14 in 307 usages (next 208) and source 15 to L3:15 in 254 (next 218) — identity is the dominant authored correspondence. Fallback (swap 14→15/15→14) reserved for Build 0335 if the phase looks wrong.
- **Implementation location:** `palette_hooks.s` `genesistan_palette_hook_59ad4`, new `.L59_water` route. Recognizes only scene 1 + banks `0x1A–0x1D`; branches BEFORE the general (compacting) staging loop. Reads frame source `a0 + d1*0x20` entries 14/15 positionally, converts arcade 0RGB444→CRAM (`.L59_water_cvt` → `.Lxbgr555_to_cram`), writes ONLY Line-3 offsets 0x1C/0x1E (indices 14/15), change-detected. Did NOT relax the `≥4` reject generally; did NOT touch the general loop, Line 2, or Lines 0/1.
- **Line-3 entries modified:** 14 and 15 only. **Line-3 0–13 / Line 2 / Lines 0/1:** untouched.
- **Commit behavior:** arcade animation step → value differs → two staged words updated → `palette_dirty` once → VBlank commit. No Genesis timer, no polling, no every-VBlank dirty.
- **Automated results:** canonical GATE_PASS; seven-epoch PASS; Plane-A/B LUT PASS; drops 0; exceptions/address/bus 0; MAME smoke clean; HUD mode 2; Line-2 sunset byte-identical to 0333 (verified `states/traces/build0334_water`); release ledger auto-recorded 0334.
- **USER MUST VERIFY (play to the R1/P1 waterfall):** does it visibly cycle; at arcade speed; plausible colors; do any UNRELATED Layer-A tiles pulse (would mean L3:14/15 are shared incompatibly); static surrounding water correct; Layer-B/sunset still correct.
- **Permanent-mapping status:** still NOT proven (this trial does not change §11's authoring-boundary conclusion).

## Build 0336 — Sonic-Style CRAM DMA Publication
- **Classification:** INFRASTRUCTURE (authorized publication-contract change). Baseline source 0335; visual water target 0334.
- **Old publication:** `vdp_commit_palette` = 64-word CPU PIO loop (`move.w (a0)+, VDP_DATA` x64), gated by `palette_dirty`, run late in `_vblank_service` -> CRAM-write noise band + CPU cost.
- **New publication:** `vdp_commit_palette` = one 68k->CRAM DMA of `staged_palette_words` (64 words / 128 bytes) to CRAM word 0, autoinc 2, mode 68k->VDP, trigger `0xC0000080`. Source-address encoding mirrors the proven `vdp_dma_words_to_vram`. Called **unconditionally, early** in `_vblank_service` (right after `rastan_direct_update_inputs`, before the plane/sprite DMAs). No `palette_dirty`.
- **Sonic reference:** cycle producers write only a few RAM words (`_inc/PaletteCycle.asm` `PalCycle_GHZ`: line 3 entries 8-B); V-blank DMAs the whole buffer to CRAM via `writeCRAM` (`Macros.asm:35`) unconditionally, Z80 stopped (`sonic.asm:736`). Rastan Build 0336 adopts the DMA-every-VBlank publication; it does NOT copy Sonic's cycle timer (the arcade owns Rastan's animation timing).
- **Z80 bus decision:** NOT stopped. Evidence: the existing production plane DMAs (`vdp_dma_words_to_vram`, used by tiles/bg/fg/sprite commits, sourced from WRAM) use no Z80 bus-request and have shipped correctly for many builds. Following that established project convention; adding Sonic-style Z80 stop was not required and was not added.
- **palette_dirty retired:** removed the `_vblank_service` gate/clear, the BSS symbol, boot.s init, and all writers (`vdp_install_test_lines`, `genesistan_palette_hook_3ba64/_59ad4/_45dae/_03ab00`, the water route). Clean link confirms zero remaining references.
- **Dead scaffolding removed:** `vdp_reassert_fg_bank3_line`, `vdp_reassert_bank36_line0` (no callers since 0325) and their carrier caches `fg_bank3_line_cache`, `fg_bank3_cache_valid`, `fg_bank3_route_seen`, `pc090oj_bank36_line0_cache`, `pc090oj_bank36_cache_valid`, plus the hooks' cache-write side paths (fg-bank3 snapshot tails, bank-0x36 cache handlers). `palette_route_lookup` retained (live: Rastan route + tilemap).
- **Semantics preserved:** `vdp_install_test_lines` still installs Lines 0/1/3 once at scene activation; Layer-B (bank 2 -> Line 2) sunset producer unchanged; waterfall `.L59_water` route unchanged (scene 1, banks 0x1A-0x1D, arcade frame index, source 14/15 -> Genesis L3:14/15, no Genesis timer). All producers just update `staged_palette_words`; the unconditional VBlank DMA publishes it.
- **Layer-B regression:** PASS. Build 0336 staged Line-2 progression byte-identical to the 0333/0328 reference (gameplay sky at f387 `0000 0642 0644...0CC0`; sunset step at f1577 `...066A...0E26 08EE 0E68 0AA8`); Lines 0/1/3 static (`l013=0xC480`). (BSS shifted: `staged_palette_words` 0xFF60E4->0xFF60A0, `scene_id` 0xFFC0AC->0xFFC068; the non-production `trace_line2_progression.lua` was made env-overridable to observe the new addresses.)
- **Verification:** canonical GATE_PASS; seven-epoch PASS; Plane-A/B LUT PASS; drops 0; exceptions/address/bus 0; MAME smoke clean; HUD mode 2. ROM SHA `a83d48b8f43cff9a326ad5499823e693b9695409837e41170a003caaab9f065e`; ledger auto-recorded 0336.
- **USER MUST VERIFY:** waterfall animates as in 0334 (L3:14/15 cycling, arcade speed); water-screen noise band gone; game speed restored; Layer B + sunset correct; no unrelated Layer-A color changes; Rastan/known sprite defects unchanged; Build-0328 terminator intact.
- **Deferred:** if the water-screen band persists after the DMA conversion, it is a separate plane/VRAM lifecycle issue (not the palette commit) and is deferred, not investigated here.
