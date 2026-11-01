# PROMPT-ID-0046 — Round 1 Arcade Scroll Semantics, Sprite Identity & Palette Source Research

**Author:** Andy · **Date:** 2026-11-01 · **Method:** static original-arcade reverse engineering (maintained
C decompilation + Ghidra exports + ROM data). **READ-ONLY.** Reference Genesis build: 0525. Concurrent: Cody
PROMPT-ID-0045.

**No implementation.** No Genesis ASM/C/remap-spec/build-tool/audio/graphics-asset/authored-palette/`Test.json`/
Bestiary/ROM change. No ROM built, no build number consumed. Deliverable: this report + an append-only
`AGENTS_LOG.md` entry.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0046`

---

## 0. Screenshot evidence status (READ FIRST)

**The prompt states Tighe will provide original-arcade MAME and BlastEm Genesis screenshots. None were
attached to this task message.** Every screenshot-dependent step below (independent placement oracle §5,
the armored-enemy pixel diagnosis §9, the R1-S1 border and R1-S3 palette visual confirmation) is therefore
completed **to the limit of source evidence** and the remaining visual-confirmation step is explicitly marked
**PENDING IMAGES**. All P0/P1/P2 *source* analysis is complete and does not depend on the images; the images
are needed only to pin specific pixel/landmark correspondences, not to establish the arcade semantics.

---

## 1. Executive summary

- **P0 (root of R1-S2 vertical misplacement):** The original arcade foreground plane is a **64×64-tile
  (512 px) vertical ring**; the live Y-scroll `A5+0x10AE` selects the visible rows as
  `ring_row = (Yscroll & 0x1FF) / 8 ∈ [0,63]`, and a **new map row is streamed on every 8-px scroll
  crossing** (`A5+0x10B2` sub-row accumulator → `0x406A4`). The **Genesis Plane A is configured 64×32
  (VDP reg16 = `0x9001`, `PLANE_NAME_WORDS = 2048`) — a 256-px, 32-row ring, half the arcade's vertical
  extent.** This is the single strongest, source-backed divergence candidate for "misplacement during
  castle traversal that realigns near the end": whenever the arcade logical row leaves the low 32-row band
  (`Yscroll` in the 256–511 px half), it has no distinct physical home in a 32-row Genesis ring and collides
  with the low band. It realigns when the traversal returns `Yscroll` to the low half. **This is a
  placement/geometry defect, not a palette defect** (consistent with the prompt's instruction).
- **P1 (sprites/palettes):** The **"armored man" = base `0x0A73`** is specifically the **state-0x0F
  death/impact animation** (comp 2), *not confirmed* as the identity of the walking armored enemy — do not
  conflate. The **"wizard"/spellcaster enemy is NOT present anywhere in the current decompilation,
  manifest, or Bestiary** — it is unidentified (unresolved route). The **R1-S3 boss body = base `0x061D`**
  (rectype `0x0E`, compositor 1, slot `A5+0x708`), palette **pool 11** via `0x3BA88[0][15] → 0x4FD02+11*32`.
- **P2 (armored corruption):** Multi-piece actor sprites use **signed `int8_t` piece offsets** with
  facing-negation (`boss_offsets_43484`, and the state-0x0F compositor-2 layout). A single corrupted instance
  "extending into the floor" alongside a correct instance points to an **instance/state-dependent piece-Y
  or coordinate-sign fault**, not invalid sprite assets. Source-backed diagnostic plan in §9.

---

## 2. Exact sources examined

**Screenshots:** none supplied this task (see §0).

**Maintained C decompilation (authoritative reconstructions):**
- `analysis/decompilation/c/rastan_world_scroll.c` — H23 vertical/horizontal scroll contract.
- `analysis/decompilation/c/rastan_scene_map.c` — H11/H12/H13 scene/descriptor/collision chain.
- `analysis/decompilation/c/rastan_actor_behavior.c` — state 0x0F (`actor_armored_40ccc` @ `0x40CCC`),
  specialized death `0x42ABC`, boss component `0x4684E`.
- `analysis/decompilation/c/rastan_actor_lifecycle.c` — impact/lethal → state 0x0F path.
- `analysis/decompilation/c/rastan_actor_tables.c` — record-type table `0x45592`, per-round boss table
  `0x444E0`, family tables.
- `analysis/decompilation/c/rastan_boss_composite.c` — boss multi-record placement + palette direction.
- `analysis/decompilation/c/rastan_actor_creation.c` — creators, boss component creator `0x423B2`.

**Ghidra exports:** `analysis/ghidra/rastan_arcade/exports/function_inventory.tsv` (call graph for the scroll
family `0x55650/0x55696/0x5572E/0x557BA/0x55854/0x55948/0x558A2/0x55904/0x55990/0x406A4`).

**ROM/geometry:** `apps/rastan-direct/src/fg_tile_cache.s` (`PLANE_NAME_WORDS=2048`),
`apps/rastan-direct/src/crash_handler.s` + `bk_crash_handler.s` (reg16 `0x9001` = 64×32),
`docs/design/rastan_actor_graphics_manifest.json` (roster/boss map/subround-2 rosters).

---

## 3. P0 — Original arcade R1-S2 vertical-scroll state machine (A. handoff)

### 3.1 State fields (PROVEN, `rastan_world_scroll.c` H23)

| Field | Meaning |
|---|---|
| `A5+0x10AE` | **FG Y scroll** (px) → PC080SN `0xC40002` (commit `0x55ACC`); **wrap mod 512** |
| `A5+0x10EC` | FG X scroll (px) → `0xC40000`; wrap mod 512, **half-rate** |
| `A5+0x10B0` | Y scroll companion (init pair; zeroed at scene transition `0x561A0`) |
| `A5+0x10BE` | player screen-Y, band-clamped `[32,304]`, target ~80 (`0x539C2`) |
| `A5+0x10DC` | per-frame scroll delta = `min(pending,4)` px (`0x51880`) |
| `A5+0x1266 / 0x1268` | pending scroll amount UP / DOWN (fed by player motion/climb) |
| `A5+0x10B8` | direction accumulator (≥0 up, <0 down); **upper limit 160 (0xA0)** |
| `A5+0x10B2` | **sub-row 8-px accumulator** (bit3 ⇒ row boundary ⇒ stream a row) |
| `A5+0x10D0` | scroll flags: bit6 up-limit reached, bit7 down |
| `A5+0x13D0` | row-stream direction mode (**2 up / 3 down**) |
| `A5+0x10A8` | **section-kind gate** (≠0 ⇒ castle/Phase-2; enables the 160 accumulator limit) |
| `A5+0x013E` | progression record (scene index source) |
| `A5+0x10CA` | descriptor **strip** counter 0..3 (`0x558A2`) |
| `A5+0x132C` | **saved completed-fill selector** (retained across the post-fill boundary) |

### 3.2 Per-frame decision order (PROVEN)

1. Player motion `0x51880` queues vertical motion into `A5+0x1266`(up)/`A5+0x1268`(down), dispenses ≤4
   px/frame into `A5+0x10DC`, calls clamp controller `0x539C2`.
2. Clamp `0x539C2` keeps `A5+0x10BE` in `[32,304]` (center 80), setting step `A5+0x10D8` and flags.
3. Scroll dispatch `0x557BA` (Y) / `0x55B3C` (X): if `A5+0x10B8 ≥ 160` **and** section-kind gate
   `A5+0x10A8 ≠ 0`, **stop** (set `A5+0x10D0` bit6). Else accumulate `A5+0x10B2` by the step; **each 8-px
   crossing streams one new map ROW** via `0x406A4` using direction `A5+0x13D0`. Then `A5+0x10AE` +step
   (up `0x55854`) or −step (down `0x55832`), wrapped mod 512.
4. Commit `0x55AB4` writes `A5+0x10AE → 0xC40002` (Y) and `A5+0x10EC → 0xC40000` (X).

### 3.3 Which source determines the streamed row (PROVEN, `rastan_scene_map.c` + inventory)

The row streamer `0x406A4` is fed by the descriptor machine:
`0x55948 → 0x558A2` cycles **strip `A5+0x10CA` 0..3**; **every 4 strips the 16 column pointers advance +4**
(next 4-byte descriptor entry) and **`0x55904` rebuilds** the 16 `{tile-word, collision-record-pointer}`
entries. Per-column descriptor page:
`0x10D000[col] = 0x1691C + col*0x22C0 + (A5+0x013E)*0x40`. The **background metatile stream** is decompressed
by `0x563A6` into the name table; `word0 → 0x10D080[col]` (tile word), `word1 → 0x10D040[col]` (collision
record pointer). **The scene index `A5+0x013E` advances only after a full 0x40-byte page (16 entries) is
consumed** — i.e., progression is a *consequence* of consuming columns, while **vertical row advancement is
camera/scroll-driven** (the 8-px crossing), answering P0 question 5: **row-group advancement is tied to
camera/scroll position, with progression `0x013E` advancing as a downstream side effect of column
consumption, not driving row choice.**

### 3.4 Answers to the 10 P0 questions

1. **Logical row selected to display:** `map_row = (Yscroll & 0x1FF)/8`, a 64-row ring; visual origin
   `A5+0x10AE`. Collision shares the same origin (`0x461CE` projection, `0x53A2E` probe) — no separate offset.
2. **Source determining that row:** the per-column descriptor page (`0x1691C + col*0x22C0 + 0x013E*0x40`) +
   decompressed metatile stream (`0x563A6`); streamed per row by `0x406A4`.
3. **Selector-0 → 1/2 transitions:** the arcade's control is the **section-kind gate `A5+0x10A8`** (0
   outdoor / ≠0 castle) plus the **saved fill selector `A5+0x132C`** retained at the post-fill boundary
   (`0x550482`/`0x0558E8`). The native "selector 0/1/2" terms in `tilemap_hooks.s` (Builds 0424/0439) are the
   *Genesis* entering-column categories; the arcade analogue is the gate + saved selector, not a 3-way state.
4. **Source-pointer advance/rebuild:** strip 0..3 (`A5+0x10CA`); +4 pointer advance every 4 strips; rebuild
   `0x55904`.
5. **Row-group advancement tied to:** **camera/scroll** (8-px crossing), not progression; `0x013E` advances
   downstream (§3.3).
6. **Up vs down:** direction mode `A5+0x13D0` (2 up / 3 down); dispatch `0x557BA`/`0x55854` (+step) vs
   `0x55832` (−step); accumulator `A5+0x10B8` sign.
7. **64-row wrap:** `Yscroll` wraps mod 512; `ring_row = (Yscroll&0x1FF)/8 ∈ [0,63]`; name table 64×64 =
   512×512 px.
8. **Checkpoint reconstruction:** scene transition `0x561A0` zeroes `A5+0x10AE/0x10B0/0x10EC/0x10EE`; scene
   scroll init `0x504FA` re-loads the 12-byte record `scene_scroll_table_50850[A5+0x013E]`
   (R1 Phase-2 climb records → Yscroll init `0x0160`=352, screen-Y `0x78`=120); the scene fill `0x0503DC`
   replays the descriptor producer to repopulate the ring. (Build 0525 mirrors this — §6.)
9. **Why correct at entry AND near the end:** at entry the full ring is reconstructed from scratch; near the
   subround end the traversal returns the logical extent to a band the current Genesis projection can
   represent, so it realigns.
10. **Transitions/resets that could cause temporary displacement:** the **64-row→32-row ring mismatch**
    (§4) and the mod-512→mod-256 scroll-origin phase difference.

---

## 4. P0 — Arcade↔Genesis divergence candidates (B. handoff)

| Arcade (PROVEN) | Genesis 0525 (to assess) | Divergence risk |
|---|---|---|
| FG plane **64×64** tiles (512 px vert), `ring_row=(Yscroll&0x1FF)/8 ∈[0,63]` | Plane A **64×32** (reg16 `0x9001`, `PLANE_NAME_WORDS=2048`), 256 px vert | **HIGH** — only 32 of the 64 logical rows have a distinct physical home |
| Y scroll wraps **mod 512** | Genesis VSRAM scroll + 32-row ring wraps **mod 256** | **HIGH** — phase doubling; a 512-px logical scene maps onto a 256-px ring |
| New row streamed per **8-px crossing**, direction `A5+0x13D0` | entering-row publisher re-streams on camera move | assess whether the publisher streams the *correct logical row → correct physical row* across the 256-px boundary |
| Scene index `0x013E` advances after a full column page | native reseed keyed to records | assess residency vs. logical-row identity |
| Collision origin = **same** `A5+0x10AE` (mod 512) | collision works per Tighe | **collision is authoritative** and correct; only the *visual* row mapping diverges — consistent with "placement wrong, collision fine" |

**Leading hypothesis (not yet proven to root):** the Genesis 32-row plane cannot represent the arcade's
64-row vertical ring, so during the R1-S2 climb (which initialises `Yscroll=0x0160`=352 px, i.e. **already in
the upper 256–511 band**) the visible rows map to physical rows that alias the low band, producing persistent
misplacement until the traversal brings `Yscroll` back into `[0,255]`, where arcade and Genesis rings coincide
and the picture realigns. This matches every reported symptom (correct at init/checkpoint, wrong mid-climb,
correct near the end, collision unaffected). **It must be confirmed** by instrumenting whether the entering-row
publisher writes arcade `ring_row ∈ [32,63]` content into a correct 32-row physical window or aliases it; see
§5/§6.

**What this implies for a fix (for Cody to design, not me):** either (a) promote Plane A to 64×64 (reg16
`0x9003`, 4096-word name table) so the Genesis ring equals the arcade ring, or (b) keep 64×32 but make the
entering-row publisher track the full 512-px logical `Yscroll` and map `ring_row` into a correctly-phased
32-row sliding window (publishing the 32 rows around the camera, mod-256 phase derived from the mod-512
logical row). Option (a) is the cleaner native-equivalence; (b) is smaller but must get the phase exactly
right. **I am not recommending which — that is Cody's implementation call.**

---

## 5. P0 — Independent arcade placement oracle (C. handoff) — METHOD + PENDING IMAGES

**Goal:** an arcade-authoritative row/landmark table, *not* derived from Cody's native compiler.

**Source-derivable now (no image):** for a given `A5+0x013E` and `Yscroll`, the exact visible rows and their
tile words are fully determined by §3.3: `ring_row=(Yscroll&0x1FF)/8`, and each column's tile word is
`word0` of `descriptor_page(col, 0x013E)` after the strip advance. A compact oracle row is:

`{ progression 0x013E, selector(gate 0x10A8 / saved 0x132C), Yscroll (→ ring_row), descriptor page addr
0x1691C+col*0x22C0+0x013E*0x40, tile word0, collision word1, logical (col,ring_row) }`.

**PENDING IMAGES (to bind to landmarks):** with the arcade MAME screenshots I can tie specific landmarks
(stonework/block transitions, platforms/ledges, windows/arches, passage boundaries) to `(col, ring_row)` and
confirm the expected spatial relationship. **Recommended minimal read-only capture if screenshots alone are
insufficient:** a watchpoint log of `A5+0x10AE`, `A5+0x013E`, `A5+0x10CA`, and `A5+0x10B8` sampled per frame
across one full R1-S2 climb (ORIGINAL ARCADE `rastan`, using the existing `tools/mame/run_rastan_trace_*`
harness — no new tooling, no gameplay-code change). That produces a frame-accurate `(Yscroll, ring_row,
progression, strip)` trail to align against the images. **Do not** assert pixel-comparability between an arcade
and a BlastEm shot unless their `Yscroll`/world positions match.

---

## 6. P0 — Comparison with Build 0525 strategy (what Cody must preserve)

Build 0525 (per PROMPT-ID-0043/0044) builds the initial Plane A via live native descriptor-producer replay
with the original 16×4 source advancement cadence, the saved scene-fill selector, restored retained post-fill
state, and residency-resolved name words. That correctly reconstructs the **initial** ring (hence correct at
entry/checkpoint — consistent with the R1-S1 0525 fix). The **incremental vertical-scroll publisher** is the
separate component to assess, specifically:
- **Logical vs physical row:** does it map arcade `ring_row ∈ [0,63]` into a phase-correct 32-row window, or
  does it wrap `ring_row & 31` (which aliases the upper half)? (§4 — the key check.)
- **Scroll-origin phase:** arcade `Yscroll` mod 512 vs Genesis mod 256.
- **Descriptor-source progression / strip cadence:** must keep the 16×4 cadence and `A5+0x13D0` direction
  during scroll, not only at fill.
- **Timing:** row must become resident *before* the scroll register exposes it (the 8-px crossing precedes
  the commit `0x55AB4` in arcade order).

Exact arcade semantics Cody needs are §3. **I did not modify Cody's implementation.**

---

## 7. P1 — R1-S2 / R1-S3 sprite inventory (D. handoff)

**Legend:** ✔ in manifest/Bestiary · ✖ absent · ? identity provisional.

| Actor | Base | Source/ref | Palette | In Bestiary | In Composer | Status |
|---|---|---|---|---|---|---|
| **"Armored man" (sword) — DEATH/impact anim** | `0x0A73` | state 0x0F `actor_armored_40ccc` @ `0x40CCC`, comp 2; entered via impact/lethal (`rastan_actor_lifecycle.c`) | per-round `0x3BA88→0x4FD02` | partial | ✖ for this base | **?** base confirmed as the *death/impact presentation*, NOT confirmed as the walking enemy's live base — **do not conflate** |
| **Walking armored enemy (R1-S2 on screen)** | **UNRESOLVED** | candidate among subround-2 family bases (`0x004B,0x00D0,0x02E8,0x0420,0x01CB,0x03B3,0x043A,0x0241,0x06E2,0x0889,0x0400`) | per-round | — | — | **UNRESOLVED** — needs the BlastEm shot + a targeted static decode of the R1-S2 schedule family that renders the walking armored sprite |
| **"Wizard"/spellcaster** | **NOT FOUND** | no `wizard/spell/mage/staff/caster` token anywhere in `analysis/`, manifest, or Bestiary | — | ✖ | ✖ | **UNRESOLVED / UNIDENTIFIED** — the enemy Tighe calls "wizard" has no identified arcade actor in the current corpus; missing source relationship = which R1-S2/S3 schedule family + base produces it |
| Family-12 reward/drop | `0x0A5A` | transform path in `0x40CCC` | family 12 | partial | ✖ | ? presentation base |
| Burst-child (0x0275 path) | `0x0275` | `0x40DD8` sub-path / Flying Demon 8/9 run `0x9D-0xA0` | — | ✔ | ✔ (0x0275 present) | established |
| **R1-S3 boss body** | **`0x061D`** | rectype `0x0E` (`boss_round_rectype_444e0[0]`), base via `0x45592[6]`; comp 1; slot `A5+0x708`; trigger `0x45330→0x4449E`; update `0x46BE0→0x4CE6C` | **pool 11**: `0x3BA88[0][15]→0x4FD02+11*32` | ✔ (R1 render+palette Cody-verified) | check | established (body); components `type15/0x061D via 0x457D0` |

**R1-S2 field families (subround-2, STATIC schedule decode, identity PENDING where noted):** family bases
`0:0x004B 1:0x00D0 2:0x033E(route) 3:0x02E8 4:0x0420 5:0x01CB 6:0x03B3 7:0x043A 8:0x0241 9:0x06E2 10:0x0889
11:0x0400` (`subround2_13e = 0x11–0x16`, boss boundary `0x16`). These are **technical bases**, not
human-verified species names — per the manifest's own `_authority` caveat (static decode, not MAME).

**Key P1 conclusions:**
- The **wizard is genuinely missing** from the corpus — this is the most important P1 gap. Recommend a
  dedicated static decode: enumerate which R1-S2/R1-S3 schedule family + base drives the spellcasting actor,
  starting from the subround-2 schedule (`analysis/actor_subround2/subround2_schedule_rosters.json`) and the
  state dispatcher `0x40BAA`, cross-checked against the BlastEm shot once supplied.
- The **armored man base `0x0A73` must not be registered as the walking enemy** until its live (non-death)
  base is confirmed; registering the death-anim base as the species would be the exact "conflate" error the
  prompt warns against.

---

## 8. P1 — R1-S3 Plane A/B and boss palettes (E. handoff)

R1-S3 is the Phase-2/boss scene (castle). Source-derived palette facts:

- **Boss palette (PROVEN direction, `rastan_boss_composite.c`):** `0x3A2D0` is `move.w (A0)+,(A1)+`, so
  `0x45D7C`/`0x45DC4` publish **`A5+0x1600` → CRAM** (not the reverse). With `sprite_ctrl=0x60` the PC090OJ
  combines compositor nibble F with bank base 0x30 → physical bank `0x3F`; `0x45DC4` maps working line 15 →
  that bank (48+15=63). **R1 boss source = `0x3BA88[0][15] → 0x4FD02 + 11*32`** (pool 11).
- **Plane A/B castle graphics** come from the same metatile chain as §3 (`0x562CA[round]` background table →
  `0x563A6` decompress; per-column descriptor pages). The R1-S3 Plane A tile vocabulary is the castle/boss
  interior; Plane B is the castle backdrop vocabulary.
- **Scene-entry vs active palette:** scene transition `0x561A0` + `0x504FA` re-init precede active gameplay;
  the boss palette is published on boss creation (`0x45330→0x4449E` trigger). No scripted per-frame palette
  cycling was found for R1-S3 in the current corpus (unresolved whether any exists — see §11).

**Composer integration recommendation (no implementation here):** expose, as a new **R1-S3 scene context**
(e.g. `PAL-R1-S3-PLANEA-BOSS` / `-PLANEB-`), the arcade *source* palettes — Plane A/B metatile source colors
via the existing `0x3BA88→0x4FD02` route, and the boss sprite palette pool 11 — **as source references for
Tighe to author against**, reusing the shared graphics libraries rather than duplicating a full library per
scene (mirrors the existing R1-S2 castle context pattern). **Do not** guess intended colors from Genesis
output; present arcade source colors and let Tighe author the Genesis approximation.

---

## 9. P2 — Armored-enemy sprite corruption (F. handoff) — source-backed diagnostic plan

**Source facts (PROVEN):**
- State-0x0F presentation (`actor_armored_40ccc`): sets `comp = 2` (2-piece compositor), `base = 0x0A73`,
  drives an anim sequence from table `0x40DCE` (`{02,01,00,01,02,03,04,05,06,07}` + 11). Alternate paths:
  `mode≠0` → `0x40E0E` (sound #23); `field_39≠0` → `0x40DD8` base `0x0275`.
- `0x42ABC` (specialized state-0x0F) applies a **coordinate adjustment for type 12** and double phase
  increments for types 10–13/18/28 — i.e. **piece/coordinate handling is per-type and per-state**.
- Multi-piece assembly uses **signed `int8_t` offsets** with facing-negation
  (`boss_offsets_43484`, `boss_place_component_43458`: `child->x = parent->x ± dx`,
  `child->y = parent->y + dy`). The sign convention and facing negation are the exact places a Genesis
  translation can drop/overflow a byte.

**Why one instance is correct and one "extends into the floor":** a correct-and-corrupt pair in the *same
scene* means the sprite assets are shared and valid; the fault is **instance/state-dependent**. The downward
extension "into the floor/empty area" is the signature of a **piece-Y offset or actor-Y coordinate applied
with the wrong sign/overflow**, or a **state-specific piece layout** (e.g. one instance in the state-0x0F
death/impact or a vertical-position-adjusted state, the other in the ordinary walk state) that the Genesis
PC090OJ compositor assembles with a different (incorrect) piece-Y base.

**Recommended Genesis diagnostics for Cody (no fix here):**
1. Capture the two instances' arcade actor records: `+0x01 anim`, `+0x05 state`, `+0x08/0x09 anim phase/cd`,
   `+0x1E base`, `+0x38 comp`, `+0x39 field_39`, and world `x/y` — to confirm whether they are in different
   states/variants (prediction: the corrupted one is in a state with a vertical adjustment or a
   `comp`/base that the Genesis path mis-lays).
2. On the Genesis side, compare the PC090OJ piece-Y projection for that `base/anim/comp` against the arcade
   piece table's **signed** `dy` — specifically test for a sign-extension/overflow in the piece-Y add and in
   the facing negation.
3. Confirm whether the Genesis compositor uses the arcade's per-type coordinate adjustment (`0x42ABC` type-12
   path) or a single generic layout.

**Boundary statement:** preserve the arcade **signed piece-offset + facing-negation + per-type coordinate
adjustment** semantics; the Genesis-specific fault to investigate is the piece-Y projection sign/width in the
PC090OJ translation. **A single correct instance does not prove the assets are valid globally** — it proves
the fault is state/instance-selective.

---

## 10. Secondary findings

**R1-S1 gray border (after Build 0508):** This is a **Genesis presentation** matter (VDP **backdrop color**,
reg `0x87`, selecting a CRAM index for the area outside the active window), not arcade metatile placement.
The arcade's area above/below the active picture is non-active display (effectively black). Useful arcade
note: the arcade does not place scenery in that region, so the correct Genesis target is a **black backdrop**;
gray means the backdrop reg points at a non-black CRAM entry (or the border palette entry was changed by the
palette authoring). **Documentation only — Cody to verify reg 0x87 / the border CRAM index.** No arcade
source change needed.

**R1-S3 missing boss music:** The sound entry point `0x3A0EC` (`play_sfx`) handles **SFX** (e.g. #23 in
`0x40E0E`). The **boss music** is a *music* request, distinct from `0x3A0EC` SFX; I did **not** locate the
specific R1 boss-music command/trigger in the current corpus. Candidate location: the boss creation/scene
transition path (`0x45330→0x4449E` boss trigger, and the Phase-2 scene transition `0x561A0`). **Unresolved —
recommend a short follow-up decode of the boss-trigger path to find the music command write** (secondary; do
not delay P0/P1). No Genesis audio change.

---

## 11. Unresolved issues (explicit)

- **Wizard/spellcaster enemy: UNIDENTIFIED** in the entire corpus (§7). Missing relationship: which R1-S2/S3
  schedule family+base renders it.
- **Walking armored enemy live base: UNRESOLVED** (distinct from the `0x0A73` death-anim base) (§7).
- **R1-S2 vertical misplacement root cause: NOT PROVEN to root.** The 64→32 row-ring geometry mismatch (§4)
  is the leading, strongly source-backed candidate but requires the entering-row publisher residency check
  (§6) and/or the per-frame scroll trail (§5) to confirm. I am **not** declaring equivalence from
  compiler-derived checks.
- **R1-S3 scripted palette effects: UNKNOWN** — none found; absence not proven.
- **R1 boss-music command: NOT LOCATED** (§10).
- All **screenshot-bound** confirmations are **PENDING IMAGES** (§0, §5, §9, §10).

---

## 12. Recommended implementation order for Cody (G. handoff)

1. **P0 R1-S2 vertical scroll (highest).** Confirm the §4 geometry/phase hypothesis via the §6 residency
   check (does the entering-row publisher alias `ring_row∈[32,63]`?). Then choose plane-size promotion to
   64×64 **or** a phase-correct 32-row sliding window. **Validation:** full R1-S2 climb on GENESIS NTSC MAME
   (`genesis`, not PAL) matches the arcade placement oracle (§5) at ≥3 landmarks across the upper band; R1-S1
   (already correct in 0525) unregressed; collision unchanged. Risk: plane-size change affects VRAM map/DMA
   budget — measure against the central `dma.s` VBlank budget.
2. **P1 wizard + walking-armored identification (static decode).** Resolve the two unresolved bases (§7)
   before any Composer/Bestiary registration. **Validation:** base→schedule-family→scene provenance cited
   from source, cross-checked to the BlastEm shot. Risk: registering the death-anim base as a species.
3. **P1 R1-S3 palette source contexts.** Expose arcade source palettes (§8) as new R1-S3 contexts for Tighe
   to author; reuse shared libraries. **Validation:** contexts load real source colors; `Test.json` and all
   existing decisions untouched.
4. **P2 armored-enemy piece-Y diagnosis.** Run the §9 diagnostics; classify as a Genesis PC090OJ piece-Y
   sign/width fault vs a state-layout fault **before** any fix. Risk: "fixing" valid assets.
5. **Secondary:** R1-S1 backdrop reg (§10), R1 boss-music command locate (§10) — only after 1–4.

**Separation of confidence:** §3 (P0 state machine), §7 boss `0x061D`/palette pool 11, §9 signed-offset
semantics = **established from source**. §4 geometry hypothesis = **likely root, not proven**. Wizard/walking-
armored identity, R1-S3 scripted palettes, boss-music command, all pixel confirmations = **unresolved/pending**.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0046`
