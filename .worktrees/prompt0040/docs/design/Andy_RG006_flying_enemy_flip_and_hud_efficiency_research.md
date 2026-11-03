# Andy — RG-006: Flying-Enemy Nativization, Tile-Flip Audit, HUD Update-Efficiency Research

**PROMPT RG-006** · **Agent:** Andy (Opus) · **Date:** 2026-10-20 · **Type:** research / static analysis
/ decomp-completion / optimization design. **No production Genesis ASM / remap / frame-generator / HUD /
Test.json / palette / audio / ROM / build-number change.** Baseline Build 0466 (counter 467) untouched;
Cody RG-005 (1UP/score vertical placement) and audio/palette work preserved (clean tree at start).
Evidence tags: **VERIFIED** (ROM/disasm/source) · **CALCULATED** · **INFERRED**. No measured cycle counts
are claimed as measured.

---

## HEADLINE (answers Tighe's core questions up front)

1. **Are we software-flipping pixels or storing duplicate pre-flipped graphics for flying enemies (or
   anywhere)?** **NO.** The native sprite path and the Plane A/B path both already express mirroring with
   **VDP H/V attribute bits** over the **same** tile pattern. The only per-orientation "duplication" is a
   small precomputed 8-byte frame *record* (relative geometry) — legitimate Case-2, not pixel data. So
   **there is no CPU/ROM/VRAM flip-optimization win to capture** — it is already optimal.
2. **Why do bats cause the biggest slowdowns?** **Volume, not per-actor inefficiency.** Bats spawn as
   swarms (batch creator 0x4CD50 → block 0x748); cost scales with simultaneous sprite *pieces* through
   the shared per-piece finalizer + SAT fill + per-frame SAT DMA. Per-actor the native path is already
   O(1) (universal interpreter retired Build 0407; cached residency; VDP flip).
3. **Biggest real levers:** (a) the per-piece finalizer micro-cost (one duplicate bbox/source
   derivation), and (b) the **HUD**, which rebuilds all 6 score digits + labels **every frame even when
   unchanged** — a clean change-driven win.

---

## SECTION 1 — BAT DECOMP COMPLETENESS

Bat actor identities (VERIFIED, `rastan_actor_tables.c`): **Large Bat base 0x03F6, pool/family 0x0A**
(record `{0x03F6,0x01,0xB6,0x0002,0x0002}` → state 1 airborne, 2 pieces); **Small Bat base 0x0268,
pool/family 0x0B** (`{0x0268,0x01,0xB9,0x0001,0x0001}` → 1 piece). Both also appear in the scripted
table (f8/f9).

| Function | PC | Role | Status |
|---|---|---|---|
| actor table | `rastan_actor_tables.c` | base/state/anim/pieces | **present** |
| airborne engine | **0x473B8** `actor_flying_engine_473b8` | main update (states 1,2,0D,0E); family 0x0A branch | **present, anim tail PARTIAL** |
| anim/motion core | 0x3CEB0 `arcade_3ceb0` | frame advance + motion integration | **present, COMPLETE** |
| airborne anim-rate pre-step | **0x4734A** | halve +0x08 flap duration (min 1) when +0x741/+0x2B set | **NEWLY DECOMPILED (RG-006)** |
| per-state config load | **0x41CFA** | config from 0x41D26[state] | **STUB (raw only) — still PARTIAL** |
| death (specialized) | 0x42ABC `actor_specialized_death_42abc` | bat types 10/11 → base 0x0275 anim 0xA8, one frame, retire 0x4092E | **present, COMPLETE** (`raw/00042abc.c`) |
| batch/swarm creator | 0x4CD50 `batch_create_4cd50` | free-slot batch into block 0x748 (base 0x0D56 swarm) | **present, COMPLETE** |

- **Newly decompiled:** `actor_airborne_anim_rate_prestep_4734a` added to `rastan_actor_behavior.c`
  (coverage `0004734a` STUB→COMPLETE). It corrects the earlier "vertical/hover" stub label: the code
  does **not** move the actor; it conditionally halves the wing-flap animation duration. Movement/flight
  is handled by the shared core `arcade_3ceb0` + the engine; the arcade owns all of it.
- **~~Still PARTIAL/unresolved~~ RESOLVED under RG-007 (`Andy_RG007_complete_bat_airborne_decomp.md`):**
  0x473B8 (states 0x0D/0x0E = passive airborne; per-family anim tail incl. bat family-0x0A anim
  0x2D+direction) and 0x41CFA (per-state config from table 0x41D26) are now **COMPLETE**, along with the
  dependency functions 0x4205C (camera tracking) and 0x4736A (ground/landing probe). The bat call graph
  has no remaining STUB/PARTIAL. Neither changed the RG-006 cost/flip conclusions.

## SECTION 2 — FLYING ENEMY INVENTORY

Airborne update class = state dispatch 0x40BAA states **1,2,0D,0E → 0x473B8** (VERIFIED,
`rastan_actor_dispatch.c`). Proven airborne enemy families:

| Family | Base / pool | Main update | Anim/motion | Pieces | Palette bank | Orientation/flip | Genesis native status | Generic work remaining | Native opportunity |
|---|---|---|---|---|---|---|---|---|---|
| **Small Bat** | 0x0268 / 0x0B | 0x473B8 (fam 0x0A path) + 0x3CEB0 | engine-seeded +0x08, pre-step 0x4734A | **1** | 0x36 (shares Lizardman block) | normal+mirror via VDP H-flip | native frame records + cached residency | finalizer per-piece bbox dup | low (near floor) |
| **Large Bat** | 0x03F6 / 0x0A | same | same | **2** | 0x36 | normal+mirror via VDP H-flip | native frame records | finalizer per-piece bbox dup ×2 | low |
| **Flying Demon** | 0x0129 (two components 0x0129 + 0x0275) | scripted init 0x45342; states vary | compositor VM | 6-9/component | 0x35 | normal+mirror via VDP H-flip | native frame records | same finalizer cost | low |

Projectiles/transient burst (base 0x0275 effects) are a **different** update class (state 0x0F /
0x43F52 pool driver) and are **excluded** per the task (not the airborne-enemy class).

## SECTION 3 — BAT / FLYING FRAME PIPELINE (per family)

```
arcade actor state (a4: state +0x05, family +0x3E, anim +0x01, dur +0x08, X +0x16, Y +0x1A, flip/orient)
  -> 0x473B8 airborne engine + 0x3CEB0 core  [ARCADE-OWNED: AI, movement, timing, anim advance]
  -> anim phase -> selector  [arcade sets a4@0x01]
  -> frame identity: native DIRECT 8-byte frame record  [O(1) index; universal interpreter RETIRED Build 0407]
  -> orientation: normal | mirrored = two precomputed records (geometry only)
  -> flip semantics: mirrored record carries attr|0x4000 (flipX) + dx=-dx-16  [NO pixel work]
  -> arcade PC090OJ rep: per-piece [control,Y,code,X]; default expander 0x3C950 (100% of Stage-1 actors)
  -> Genesis native path: profile_native_variant_entry (O(1) group_base + bank_slot residency) ->
     .Lnq_emit_entry finalizer (per piece: X=sext(mapX)+a4@22 or mirror a4@22-mapX-0x10; Y; code;
       flip bit -> SAT; viewport clip; residency; SAT word)
  -> SAT output (word0 Y, word1 size/link, word2 = priority<<15 | line<<13 | vflip<<12 | hflip<<11 | tile)
```

**Interpreted/recomputed every frame (VERIFIED):** per piece the finalizer derives X (add/mirror), Y,
code, the SAT flip bit (read from the precomputed attr — not computed), clip, residency key, and the SAT
word. Frame *selection* is a direct index (not interpreted). The one avoidable per-piece item is the
**duplicate opaque-bbox / source derivation** (flagged earlier, Build-0409 note) — it recomputes a bbox
index per rendered piece that the finalized-vi record could carry.

## SECTION 4 — SOFTWARE FLIP / VDP ATTRIBUTE AUDIT (explicit)

- **Runtime sprite pixel flipping:** **NO.** No read-rows/reverse-nibbles/upload-mirror path exists; the
  flip is a SAT attribute bit. (`gen_pc090oj_palsel_lut.py` sat_word2 `(hflip&1)<<11 | (vflip&1)<<12`;
  finalizer `attr@0 = type 0x80 ? 0x4000 : 0`.)
- **Runtime Plane A/B pixel flipping:** **NO.** `tilemap_hooks.s:249-255` maps PC080SN H-flip (bit 14) →
  Genesis nametable **0x0800**, V-flip (bit 15) → **0x1000**. Attribute flip, not pixel.
- **Duplicate pre-flipped sprite patterns:** **NO.** Both orientations use the **same** tile `code`
  (`precompute_pc090oj_frame_table.py`: mirrored sets `attr|0x4000` and `dx=-dx-16`, code unchanged).
- **Duplicate pre-flipped Plane A/B patterns:** **NO** (attribute path above).
- **VDP H/V attribute paths already used correctly:** sprites (SAT word2 bits 11/12); planes (0x0800/
  0x1000). Both already optimal.
- **Small Bat flip model:** pixel data **canonical** (not mirrored); geometry **mirrored** (precomputed
  dx=-dx-16; 1 piece so trivial); **H-flip bit used**; **runtime flip cost ≈ 0** (read from record).
- **Large Bat flip model:** identical, 2 pieces (precomputed mirrored piece offsets); H-flip used; cost ≈ 0.
- **Other flying-enemy flip models:** Flying Demon — same precomputed normal/mirror records + H-flip.
- **Unnecessary flip work found:** **NONE.** **Canonical-tile + VDP-flip opportunity: already realized.**
- **Estimated savings — CPU 0, ROM 0, VRAM 0, DMA 0** (the flip is already attribute-based; the only
  per-orientation ROM cost is the 8-byte geometry records, which are required Case-2 and should NOT be
  removed — they encode mirrored piece X offsets the VDP flip bit alone cannot provide for multi-piece
  actors).

**Orientation-specific native frames "mean":** separate **geometry** (relative piece X via dx=-dx-16) +
separate **SAT flip bit**, over the **same tile identity** and **same pixel data**. They are **not**
duplicated pixels and **not** runtime-transformed pixels.

## SECTION 5 — FLYING-ENEMY PERFORMANCE PLAN

Ranked by likely CPU benefit × (low complexity, low semantic risk):

1. **Finalizer per-piece bbox/source consolidation** (rope-relevant, all enemies incl. bats). Bake the
   opaque-bbox index into the finalized-vi record so `.Lnq_emit_entry` reads it instead of re-deriving
   per piece. CPU: small per rendered piece (scales with swarm size). ROM ~0, VRAM 0, DMA 0. Semantic
   risk: none (SAT-record equivalence provable). *This is the only real native-enemy micro-win.*
2. **SAT/DMA volume for swarms** — the dominant cost is simply many pieces. Options are limited without
   changing gameplay (can't drop bats): ensure the SAT publication is already change-gated where
   possible; no per-actor semantic cut helps. **Low upside; do not over-invest.**
3. **Flip/canonical-pattern optimization: NOT APPLICABLE** — already optimal (Section 4). Do not spend
   effort here.

**Recommended next Cody phase:** the finalizer bbox consolidation (item 1) — it is the single
evidence-backed per-piece reduction and benefits every enemy, bats included. **Not implemented here.**

## SECTION 6 — HUD CURRENT COST

**Simplified (reduced) gameplay HUD** — producer `.Lnq_project_p1_hud` (`pc090oj_hooks.s`), run **every
gameplay frame** (VERIFIED):
- `clr native_hud_count`, set HUD lane, fast context.
- Reads the 3 BCD score bytes at `0x00FF011E/1F/20` and emits **6 score-digit sprites** via
  `.Lnq_emit_hud_digit` (one SAT record each) at fixed X = 0x08/0x10/0x18/0x20/… Y=0x10.
- Emits the **3 static labels** (`0x39/0x46/0x48`, the 1UP/P1 text).
- All of this is rebuilt **unconditionally** — even when the BCD score is byte-identical to last frame.
- **Per-frame work:** 6 digit conversions + 6 digit SAT records + 3 label SAT records + the HUD lane
  into the SAT chain → DMA'd with the frame regardless of change.

**Full HUD** — `gen_native_hud.py`-generated frontend SAT + `native_frontend_hud_emit`
(`0x74B1A`, writes 0xFF011E/0142, reads 0xFF0117). Largely **static SAT** (labels + digit cells at fixed
cells 1359-1418); the score digits are the only dynamic part. Change frequency: labels never change;
digits change only when the BCD score changes.

**Change frequency vs update frequency:** both HUDs update **every frame** but the displayed values
change only on scoring events (and labels never). So the repeated work while unchanged = the full digit
rebuild + SAT emission + its share of SAT DMA, every frame the score is static.

## SECTION 7 — HUD OPTIMIZATION PLAN

Per-element classification (VERIFIED authoritative source = arcade BCD `A5+0x011E` / HUD state):

| Element | Source | Changes | Model |
|---|---|---|---|
| 1UP / P1 labels (0x39/0x46/0x48) | static | **never** (per scene) | **STATIC — prebuild once**, never rebuild |
| score digits (6, BCD) | A5+0x011E..0x0120 | on scoring events | **last-value compare** (3 bytes) → skip rebuild+emit when identical |
| high score / 2UP (full HUD) | static values | rarely | last-value compare (rare) |
| round / energy / weapon (if present) | arcade state | on event | dirty-at-writer or last-value compare |

- **Recommended simplified HUD:** **field-level dirty via last-value compare** — cache the 3 rendered
  BCD bytes + a "labels built" flag; emit labels once; re-emit digits only when the 3 BCD bytes differ
  from the cached copy. When unchanged, re-emit the cached SAT records (or skip if the SAT chain is
  retained), eliminating the 6 digit conversions + rebuild per static frame.
- **Recommended full HUD:** **prebuilt static templates** for labels + a **last-value compare** on the
  digit BCD; it is already mostly static, so the win is smaller than the reduced HUD.
- **Ownership rule honored:** the cache stores only the **last-rendered** BCD/value for change detection;
  the arcade BCD remains the sole authoritative source. **No GenesisScore/Lives/Health**; this is
  presentation caching, not a second state model.

## SECTION 8 — IMPLEMENTATION SEQUENCING

Derived from the findings (biggest certain win first, no wasted effort on the already-optimal flip):

1. **HUD change-driven update (simplified HUD first, then full HUD).** Highest certain CPU+DMA reduction
   per static frame; low risk (presentation-only); visually unchanged. Files (future, Cody):
   `pc090oj_hooks.s` `.Lnq_project_p1_hud` + a small presentation cache; full HUD `gen_native_hud.py` /
   `native_frontend_hud_emit`. Validation: SAT-record equivalence when BCD unchanged; RG-005 corrected
   appearance preserved; hardware acceptance (1UP/score correct, no flicker).
2. **Finalizer per-piece bbox/source consolidation** (flying enemies + all enemies). Modest per-piece
   CPU; benefits bat swarms. Files: `.Lnq_emit_entry` + the finalized-vi generator. Validation:
   SAT byte-equivalence vs Build 0466.
3. **Flip/canonical-pattern optimization: SKIP** — proven already optimal (Section 4).

**Phase D/E relationship:** (1) HUD change-driven and (2) finalizer bbox consolidation are presentation-
layer, **usable now** and **survive Phase D/E** (they don't depend on the plane/DMA republish
architecture and don't conflict with it). The flip avenue is moot. No proposed item is likely to be
thrown away.

---

## FILES

- C decomp added: `analysis/decompilation/c/rastan_actor_behavior.c` — new
  `actor_airborne_anim_rate_prestep_4734a` (0x4734A). Coverage: `analysis/decompilation/c/function_coverage.csv`
  (0x4734A STUB→COMPLETE).
- Research doc: this file.
- **Production files changed: NONE.** No ROM, no build number, no Test.json/palette/audio/remap/
  frame-generator/HUD/flip production change. Baseline Build 0466 untouched.
