# Build 0280 — Rastan Sword + Lizardman Club Piece Rendering (WORKING REPORT)

**Agent:** Andy · **Baseline:** Build 0279 (accepted) · **Counter:** 279 · **Status:** INVESTIGATION IN
PROGRESS — **NO numbered build produced** (prove-first / no-churn gate NOT yet satisfied).

### CURRENT AUTHORITATIVE GATE STATUS (Cody static reconciliation — supersedes Session 7)
| Required proof | Status |
|---|---|
| Standing/crouch/thrust sword displacement | **PROVEN** — the retained update, activation, and renderer still use raw `0x0010D338`; in Build 0279 that resolves to ROM bytes beginning `CCCC EEEC`, not Genesis WRAM. The renderer consumes those bytes as malformed aux-piece coordinates. |
| Root of the garbage coords | **PROVEN** — the native anchor publisher is valid, but activation never reaches its one-time anchor copy because ROM word `0xCCCC` is treated as an already-active record. The semantic auxiliary array belongs at `A5+0x1338` / Genesis-WRAM `0x00FF1338`. |
| Missing-tip identity | **PROVEN** — original arcade table `0x05BB10` selects code `0x0104` for primary piece 0 at phases 6–23. Code `0x008E` belongs only to phases 0–1. The existing capture did not exercise the thrust state, but no static identity contradiction remains. |
| Sword palette-flash cause | **NOT PROVEN** — the runtime SAT/metadata handoff is coherent through fixup and DMA. The existing frame-done diagnostic can pair the displayed SAT bank with metadata already reused for the next build bank, so its nibble-3→line-0 rows do not prove a runtime metadata race. |
| Lizardman club | **ACTOR-SCOPED NO DEFECT FOUND** — actor 5, class `0x17`, at marked frame 10168 has all eight expected pieces, exact coordinates, and matching converted art/SAT output. This does not invalidate the user's visible observation; it bounds that observation outside this actor's captured queue/art/transform. |
| Exact bounded correction | **BOUNDED FOR AUX OBJECT ONLY** — redirect all three semantic acquisitions of raw `0x0010D338` to `A5+0x1338`, preserving one-time activation anchoring and the original update/render lifecycle. Do not restore Block-A tuple staging or re-anchor active records every frame. No palette correction is justified by current evidence. |

The auxiliary-object correction is statically bounded, but this reconciliation task authorizes no
implementation or build. The residual sword palette cause remains the only optional irreducible dynamic fact;
the existing capture does not justify a production palette correction.

Authoritative reconciliation: `docs/design/Cody_pretrace_static_reconciliation.md`. Session 6/7 prose below
is retained as investigation history; where it conflicts with this status block or Cody's semantic model, it is
superseded.

### SUPERSEDED earlier conclusions (do NOT treat as current truth)
- **SUPERSEDED:** "action-state = a5@0x10E8 distinguishes attacks" — corrected: attack TYPE is a5@0x1116 (0/1/4) +
  a5@0x1108 (crouch) + a5@0x1114 (facing); Cody's model gives standing=action0/var4, crouch=action5/var4,
  thrust=action2·3/var1.
- **SUPERSEDED:** "0x54810 aux = the sword / owns the tip" — DISPROVEN (Cody: 0x54810 blank on sampled attack;
  the displaced sword is the 0x5475A three-piece segment, and the tip is BODY primary piece 0).
- **SUPERSEDED:** "sprite_ctrl shadow drops to 0 → palette flash" — DISPROVEN (shadow/colbank constant 0x0060).
- **SUPERSEDED:** "Lizardman club piece identity unresolved / possibly shares sword cause" — resolved: complete
  0x17/0x18 pose known, composition correct, no defect, separate from sword.
- **SUPERSEDED:** "aux reads stale block-A tuple-0 directly" (Session 6 wording) — refined: 0x547C0/0x51E00
  block-A reads were already retired; the aux sub-object now takes its anchor from a5@0x129A/0x129C, which is the
  invalid value. Same net effect (garbage), corrected source.

This is the durable working report. Findings are labelled **PROVEN / HYPOTHESIS / DISPROVEN**. If a session
limit interrupts, the "CONTINUATION BOUNDARY" section states exactly where to resume without re-deriving.

---

## Methodology note
Primary authority = ORIGINAL ARCADE static provenance (Ghidra exports + `build/maincpu.disasm.txt` +
`build/regions/maincpu.bin` ROM tables). Runtime MAME used only to confirm the arcade player action-state
values actually produced (block-A capture) — that capture is already collected; no further broad tracing.

---

## PROVEN — arcade player sprite structure
- **BODY producer** = arcade `0x540CC` (called `jsr 0x5151C`), builds block A (a5+0x11B2, up to 18 tuples
  `{word0,Y,code,X}`). State machine dispatches on **a5@0x10E8** (player action state).
- **FRONT/weapon producer** = arcade `0x59F92` (called `jsr 0x51060`), builds block B (a5+0x170, 4 tuples) =
  thrown/special weapon overlay.
- **Player action states (a5@0x10E8)** and their setters (writers of a5@(4328)):
  - `1` walk (0x52574…), `2` run/walk (0x520FA…0x52352), `3` (0x50562/0x5242A…/0x5558C — flipY head pose),
    `4` **attack** (0x51E54 — sets reach X via 0x51E80, resets frame, a5@0x1112=16, a5@0x1120=255),
    `5` **attack** (0x51E28 — sets facing a5@0x1114 from input bits at 0x10D37A btst #2/#3),
    `6` (0x51B9A), `7` (0x52066/0x527CC/0x53F0C/0x54038), `8` (0x517EE/0x53E0C/0x54EBE/0x553E6/0x577F0),
    `9` (0x516EE).

## PROVEN — arcade block-A pieces per state (already-collected arcade capture)
Tuple = `{word0,Y,code,X}`. word0: bit15=flipY, bit14=flipX, low-nibble=palette bank. All non-blank pieces
carry **palette nibble 3**. Representative:
- st=1 walk: 9E,9F(head) 8E,8F,90(torso) 76,77(legs) — all word0=**0x4003** (flipX only).
- st=2 walk-variant: …10B,10C legs — word0=0x4003.
- st=3: **word0=0xC003 (flipX+flipY)** on head pieces 9E/9F + 104,105,106 + 10B–10E.
- st=4 attack: 10F–114 (6 pieces, no head) — word0=0x4003.
- st=5 attack: A0,A1 + B0–B3 — word0=0x4003.
- st=8: 4DB–4E0 (special high tiles) — word0=0x4003.
- **The `0x0010` word0 values seen earlier are ONLY on blank/code-0 park tuples (t12/t13). DISPROVEN as sword
  palette evidence** (per Tighe's correction — confirmed).

## PROVEN — native transform is faithful for standard (flipX) body pieces
- Build 0274 redirected every block-A expander write (`0x54492`, `0x545BA`, `0x546A8`, `0x5475A` aux three-piece,
  `0x54576` blank) to `native_player_piece` (spec `shift_replacements`), preserving `{word0,Y,code,X}` in
  d1/d6/d3/d4. `native_sprite_emit` stores them; commit realizes bit14→hflip(0x0800), bit15→vflip(0x1000),
  palette from low-nibble+colbank. **Legacy decode `.Lpc090oj_decode_record` uses the SAME bit14/bit15 flip
  semantics** (pc090oj_hooks.s:2357 confirms "vflip = post-flip word0 bit 15") — so flip interpretation is
  consistent between paths.
- Attack states 4/5 body pieces are word0=0x4003 (flipX only) — the **same** transform proven correct by
  working walking. ⇒ **the swing BODY pieces themselves are not mis-transformed.**

## PROVEN — the 0x54810 auxiliary player piece producer is ORPHANED in Genesis gameplay
- Arcade `0x547C0 → 0x547EE/0x54804 → 0x54810` writes 4 pieces **directly to 0xD00000 (PC090OJ object RAM)**,
  player-anchored via **a5@0x129A (X) / a5@0x129C (Y)**, index **a5@0x1298**, gated by **a5@0x129E** (init at
  0x5506C → a5@0x129E = 1 or 4). Source table = **0x5DA5E** (24 bytes/entry, 4×6-byte pieces).
- Static decode of table `0x5DA5E` (from `build/regions/maincpu.bin`): codes **0x0275–0x02AC**, attr **0x0003**
  (palette nibble 3, no flip). idx 0–2 = single pieces (0x275/0x276/0x277); idx 4–8 = 32×32 four-piece groups
  (X/Y offsets ±8) codes 0x278–0x287, 0x2A9–0x2AC.
- **Genesis gameplay finalizer `.Lnq_gameplay` (pc090oj_hooks.s:1596–1632) emits ONLY the six native lanes
  (HUD, FRONT_EFFECT, PLAYER_FRONT, MIDDLE, PLAYER_BODY, BACK_ENEMY). It does NOT scan pc090oj_object_ram.**
  `pc090oj_native_emit_pass` only takes the object-RAM path for scene≠1 (frontend). ⇒ **every 0x54810 piece
  written to 0xD00000 is produced but never rendered during gameplay.** This aux was NOT redirected to a native
  lane by Build 0274 (spec `shift_replacements` covers 0x5475A but NOT 0x54810).

## HYPOTHESIS (strong) — the 0x54810 aux is the sword overlay (missing tip / wrong swing)
- The block-A walk pieces contain NO sword tile (head/torso/legs only) ⇒ the sword must be a separate overlay.
  The 0x54810 aux is the only player-anchored separate overlay producer, and it is animated (a5@0x1298 cycles),
  consistent with a swing animation. If it is the sword (or its extended tip), being orphaned explains
  "swing geometry wrong" (body swings, sword piece missing/misplaced) and "downward-thrust tip missing".
- **NOT YET PROVEN:** that tile codes 0x275–0x2AC are specifically the sword artwork, and the exact mapping
  of a5@0x1298 index → standing/crouch/thrust swing frames. (Needs: identify a5@0x1296/0x1298/0x129E semantic
  owner + confirm codes 0x275–0x2AC are sword tiles. See CONTINUATION BOUNDARY.)
- **Update (aux is a general player SUB-OBJECT system, not obviously the sword):** the aux producer is dispatched
  from a workram sub-object array at **0x10D2C8** (4 entries × 4 words `{type_d0, subtype_d1, X, Y}`; builder at
  arcade 0x54B18–0x54BF2). type=1/subtype=0 → aux-init `0x5506C` → sets a5@0x1296=1 & a5@0x129E; the piece
  emitter is `0x54810`. a5@0x1296 (aux-active) is ALSO set at `0x529D4`, inside a player action that plays sound
  #38 and applies `subi #64, a5@(0x13A)` (an upward/jump-like impulse) — i.e. the sub-object is tied to a
  jump/special action, **not unambiguously the melee sword**. ⇒ the "aux = sword" hypothesis is **NOT proven**;
  it may be a jump/special-weapon effect. Per prompt, this hypothesis must be proven (which exact attack/table/
  piece) or closed before any fix touches 0x54810.

## OPEN — sword palette flash
- Arcade sword/aux attr nibble = 3 (static). If the sword is the orphaned aux, "palette flash" may be a
  secondary effect of intermittent/none rendering rather than a palette-route bug. Palette-route mechanism not
  yet traced to a proven flash cause. **UNRESOLVED.**

## OPEN — Lizardman club cross-check
- Enemy pieces decode via `.Lnative_emit_actor_common` (default expander). That path sets flipX via 0x4000 OR
  **code-negation** (type 0x40 → `neg code`, selects mirrored artwork); it NEVER sets flipY (0x8000). The club
  is a piece in the Lizardman actor stream. **Club producer/piece bytes NOT yet identified statically.**
  Shared-vs-separate cause **UNDETERMINED**.

---

## CONTINUATION BOUNDARY (resume here)
1. Prove the semantic identity of the 0x54810 aux: read the a5@0x1296/0x1298/0x129E owner (dispatch table at
   arcade `0x550A8`: handlers 0x551CC/0x5520E/0x55250/0x55292/0x552D4/0x55316/0x551B0/0x55346). Confirm whether
   tiles 0x275–0x2AC are the sword (cross-ref player art tile ranges) and map a5@0x1298 → swing frames.
2. If aux = sword: bounded fix = redirect `0x54810` output to a native lane (PLAYER_FRONT or PLAYER_BODY) the
   same way Build 0274 redirected 0x5475A — i.e. replace the 4× `move.w …,0xD00000` writes with
   `native_player_piece` calls under the correct lane, via spec `shift_replacements`. This removes legacy
   0xD00000 usage (aligns with the native-replacement mandate) instead of re-enabling an object-RAM scan.
3. Resolve club statically: identify Lizardman family/class (a4@0x38 family, a4@1 class) and its piece stream;
   compare code/attr/flip to Genesis. Determine same-vs-separate cause.
4. Resolve palette flash once aux identity is known.
5. Only after 1–4 are PROVEN: ONE Makefile-owned Build 0280.

---

## SESSION 3 static findings (Q1–Q5 continued)

### Q1 — 0x54810 identity (refined)
- **PROVEN:** 0x547C0→0x54810 is called **every frame** from the main sprite loop at `0x5154A` (right after BODY
  `0x5151C`). It is a persistent player-anchored producer. Anchor a5@0x129A/0x129C = copied from block-A tuple-0
  (0x547C8) i.e. the player's first body-piece position.
- **PROVEN:** It is one branch of a player **sub-object / weapon** system. The dispatcher at `0x54B04–0x54B16`
  reads a workram sub-object array `0x10D2C8` `{type,subtype,X,Y}` and, when weapon-type a5@0x1388==3, indexes
  the **longword jump table at 0x550A8** (12 entries → handlers 0x551CC/0x5520E/0x55250/0x55292/0x552D4/0x55316/
  0x551B0/0x55346/0x551B0/0x55376/0x551B0/0x553A6). a5@0x1388 = weapon type (0/1/2/3, 255=none); FRONT builder
  0x59F92 turns type into codes 0x0A6A–0x0A6D.
- **PROVEN:** aux source table `0x5DA5E` codes 0x275–0x2AC, attr 0x0003 (nibble 3, no flip); idx = a5@0x1298>>2
  (animation). It is an **animated player-attached overlay** (weapon/slash/effect).
- **NOT the primary visible sword blade** — see Q2 deduction. Remains the strongest candidate for the
  **missing thrust TIP / a missing slash-extension piece** (orphaned: writes 0xD00000, gameplay finalizer skips
  the object-RAM scan). Exact attack/frame binding of a5@0x1298 still unproven statically.

### Q2 — the visible sword blade is block A, faithfully transformed (KEY DEDUCTION)
- **PROVEN:** attack states 4/5/8 block-A pieces are all word0=**0x4003** (flipX + nibble 3) — identical
  transform class to correctly-rendered walking. The swing arm+blade artwork is carried in these body tiles
  (st4 10F–114, st5 A0/A1/B0–B3, st8 4DB–4E0).
- **PROVEN:** FRONT/block-B (0x59F92) is the **thrown-weapon/projectile display** (codes 0x0A64–0x0A6D at fixed
  X 0xA0–0xD0, Y 0xE8) — **NOT** the melee sword. (Full builder read.)
- **DEDUCTION (from Tighe's report that the sword is visibly present but wrong):** the blade IS rendered ⇒ it is
  the block-A path, whose transform is faithful. Therefore the "swing geometry wrong" is **not** a block-A
  coordinate/flip transform defect. Residual candidates, in order: (a) a **missing companion piece** (the aux
  slash/tip, orphaned) that makes the swing read as malformed; (b) **tile residency / arcade-code→Genesis-tile
  mapping** for the attack-specific codes; (c) **palette-line routing** (see Q4). These distinguish only by
  observing the Genesis SAT (tile+palette+flip) during a controlled attack.

### Q4 — palette flash (static boundary)
- **PROVEN:** every player/aux sword piece carries palette **nibble 3**; the body carries nibble 3 too. A pure
  colbank change would flash the WHOLE player, not just the sword ⇒ the flash is **not** a global colbank swing
  on a nibble-3 body piece. Arcade palette-line loading uses 0x59AD4 → 0x200000 (16-entry RGB copy).
- **UNRESOLVED statically:** whether the arcade **cycles/animates the sword's specific palette line** (an effect)
  that the native commit-time `palette_route_lookup`(nibble 3 + display-latched colbank) fails to reproduce, or
  whether the flashing sword piece is actually the aux (different rendered path). Needs the per-frame
  nibble+resolved-line for the sword pieces during a controlled swing.

### Q5 — Lizardman club (static boundary)
- **PROVEN (mechanism):** enemy pieces decode via `.Lnative_emit_actor_common`; that path uses flipX (attr
  0x4000) OR **code-negation** (control type 0x40 → `neg code`, selects mirrored-artwork tile) and **never sets
  flipY**. The player path never uses code-negation. ⇒ sword and club use **different flip mechanisms**; a single
  shared flip-transform defect is **not supported** (trending SEPARATE causes).
- **UNRESOLVED statically:** the Lizardman actor's family (a4@0x38) / class (a4@1) / base tile (a4@30) and its
  club piece control-byte are not identifiable without knowing which on-screen actor is the Lizardman (enemy
  spawn tables are unlabeled). Needs the Lizardman actor record.

---

## CONTROLLED TRACE REQUIRED FROM CODY (bounded; Andy cannot control these gameplay states)

**Request A — player attack rendering (settles swing geometry, missing tip, palette flash):**
- State/action: perform, facing RIGHT then LEFT, (1) standing sword attack, (2) crouch (Down) + attack,
  (3) jump then Down+attack (downward thrust). Hold each ~1s.
- Why static can't decide: need the Genesis-side realized SAT (tile + palette line + flip) and the aux fate to
  distinguish "missing companion/tip piece" vs "tile-residency mapping" vs "palette-route" — all rendering-side.
- Capture (bounded set), each attack frame:
  - a5@0x10E8 state, a5@0x110A sub, a5@0x1114 facing, a5@0x1298/0x129E (aux), a5@0x1388 (weapon type).
  - native_queue_player_body @0xFF6BDA (count @0xFF68BE) and native_queue_player_front @0xFF6A2A
    (count @0xFF68BA): entries {word0,Y,code,X}.
  - pc090oj_object_ram: the 4 aux records the arcade 0x54810 would write (to confirm they land there and are
    NOT in any native lane).
  - staged_sprite_sat: for each player-body entry, the resolved {palette line, hflip/vflip, Genesis tile} — to
    compare arcade code→expected vs Genesis tile, and watch the sword piece's palette line across frames.
- One question each: (geometry) does any arcade block-A/aux sword piece fail to appear in a native lane, or map
  to a wrong Genesis tile? (tip) which exact arcade piece is absent from all native lanes during the thrust?
  (palette) does the sword piece's resolved palette LINE change across swing frames while its nibble stays 3?

**Request B — Lizardman club actor (settles club identity):**
- State/action: reach the first Lizardman in stage 1 and stand next to it while it raises the club.
- Capture (bounded): the Lizardman actor record — a4@0x00(active) a4@0x01(class) a4@0x02(facing) a4@0x16(baseX)
  a4@0x1A(baseY) a4@0x1E(base tile) a4@0x27(attr) a4@0x38(family); AND its emitted native MIDDLE/BACK_ENEMY
  queue entries {word0,Y,code,X} for the club-raised frame.
- One question: what are the club piece's code / attr / X/Y / flip-or-code-negation values, so the arcade club
  piece can be identified in the family table and compared to Build 0279's native output?

Both are single bounded captures; no broad enumeration.

---

---

## SESSION 4 — tile-art priority, attack reconstruction, palette root cause

### USER OBSERVATION — one-tile-width sword displacement
- **Interpretation (PROVEN boundaries):** every static art path is byte-coherent, so the displacement is NOT a
  global art/decompose bug:
  - Region assembly (`build_rastan_regions.py`): pc090oj = b04-05/06 interleaved (0x00000–0x3FFFF) + b04-07/08
    (0x40000–0x7FFFF). 0x40000/128 = 2048 codes per half. **All** sword codes (0xA0,0x10F,0x4DB,0x4E0) AND all
    walking codes (0x76–0x114) are < 2048 ⇒ **same half, uniform assembly** — no half-boundary offset.
  - `preconvert_pc090oj_tiles.py`: 16×16 → TL,BL,TR,BR (Genesis column-major 16×16 order) — **correct**, and
    globally applied (walking proves it).
  - Residency + DMA: SAT tile = cell_byte_off*2 + SPRITE_TILE_BASE; DMA dest = slot*4 + SPRITE_TILE_BASE with
    slot = cell_byte_off>>1 ⇒ **identical** target (Cody-confirmed coherent). Source art = `rastan_pc090oj +
    code*128`.
- **CONCLUSION:** SAT coordinate NOT proven wrong; resident-art layout NOT proven wrong; adjacent-code NOT proven
  (Cody: queue code matches). The one-tile displacement is **not reproduced by any statically checkable path** for
  the ONE attack pose Cody captured (action-5). It must therefore be either pose-specific (a crouch/thrust table
  Cody never labeled) or a piece Cody didn't sample. **Requires a correctly-labeled capture (below).**

### ATTACK STATE/MAPPING RECONSTRUCTION (PROVEN)
Input word a5@0x10D37A drives attack init at **0x51CA0–0x51D30**:
- bit 2 = **attack (sword) button** (gates the whole block); bit 0 = **down/crouch**; bits 1/3 = variant.
- The visible attack TYPE is encoded **not** in a5@0x10E8 but in:
  - **a5@0x1116** = 0 (standing), 1 or 4 (down variants / thrust);
  - **a5@0x1108** = 1 (crouch);
  - **a5@0x1114** = facing (2/3).
- BODY builder 0x540CC selects the table from these: 0x5438E checks a5@0x1116==4 → 0x543B4; a5@0x1108==1 →
  crouch branch; `a2 = 0x5BAE0` when a5@0x1116==0 (standing, phase bytes 0x0C–0x0E) else `a2 = 0x5BB10`
  (down/thrust, phase bytes 0x19–0x1B / 0x25–0x28). **Standing and thrust use DIFFERENT animation tables.**
- **This explains Cody's "only action 5":** his logger keyed on a5@0x10E8 (which stays at the base action during
  an attack); it never sampled a5@0x1116/0x1108/0x1114, so standing/crouch/thrust were indistinguishable in the
  log. It is NOT evidence Tighe didn't perform them.

### PALETTE 3→0→3 ROOT CAUSE (PROVEN)
Data-flow: sword nibble = 3 (stable). Commit colbank d7 = (pc090oj_sprite_ctrl_shadow & 0x00E0) >> 1.
`.Lnative_palsel`: d0 = 3 | d7. Normal render d7=0x30 ⇒ d0=0x33 ⇒ **inline line 3**. At the flash frame the
shadow's 0x00E0 bits are 0 (colbank d7=0) ⇒ d0=0x03 ⇒ `.Lnp_general` → `palette_route_lookup(scene1,
PC090OJ, bank 0x03)`. **palette_route has NO entry for bank 0x03** (only `1,PC090OJ,0x33→3` and
`1,PC090OJ,0x36→carrier`) ⇒ returns −1 ⇒ generic fallback `(0x03>>4)&3 = 0` → **line 0**. The shadow is a
faithful mirror of the arcade sprite_ctrl write (`genesistan_pc090oj_sprite_ctrl_write_d0`), so the transient
colbank drop originates in the arcade write stream.
- **Bounded fix candidates (choice depends on WHY colbank momentarily reads 0):**
  (a) if the drop is a real arcade transient the arcade doesn't render (timing), latch/hold the last-valid
  non-zero colbank at commit; (b) add a `palette_route` entry mapping (scene1, PC090OJ, bank 0x03) → line 3 so
  nibble 3 stays on the sword line across the transient (targeted, not a blanket freeze). **Not yet chosen** —
  needs the colbank-drop trigger (recoverable from arcade attract sprite_ctrl writes, which is a permitted
  non-interactive observation, or from the callers of `genesistan_pc090oj_sprite_ctrl_write_d0`).

### DOWNWARD-THRUST TIP (static boundary)
Thrust table = 0x5BB10 (phases 0x19–0x1B/0x25–0x28), a two-level index → a3/a4 6-byte piece records. Fully
resolving the tip piece requires tracing the a3/a4 record bases for the thrust phase (multi-level). **Tip piece
not yet isolated statically.** 0x54810 aux is DOWNGRADED as tip owner (Cody: aux blank/inactive on the sampled
attack).

### SHARED/SEPARATE (updated)
Sword and club use different flip mechanisms (ruled out shared FLIP bug — Cody). A shared arcade-code→resident-art
/ source-offset / decomposition bug is **DISPROVEN as a global effect** (walking + Cody's action-5 both coherent;
region uniform). A pose-specific art issue remains possible only pending the labeled capture. Club sampled piece
(code 0x004E, control 0x01, H1/V0, no code-negation) is arcade-faithful per Cody ⇒ **no club patch justified.**

---

## REFINED CONTROLLED CAPTURE REQUEST (Cody) — supersedes Request A
Andy cannot control these states. The capture must **key on the attack-type fields**, not a5@0x10E8:
- Perform, facing RIGHT then LEFT: (1) standing attack (a5@0x1116==0), (2) crouch+attack (a5@0x1108==1),
  (3) jump→down+attack / thrust (a5@0x1116==4). Hold each ~1 s.
- Label each sampled frame with **a5@0x10E8, a5@0x1116, a5@0x1108, a5@0x1114, a5@0x110A**.
- Capture per frame: native_queue_player_body {word0,Y,code,X} (count @0xFF68BE), native_queue_player_front
  (count @0xFF68BA), the 4 aux object-RAM records, and each body entry's resolved SAT {palette line, hflip,
  vflip, Genesis tile}.
- Questions answered: (geometry) for each labeled pose, do the native codes/X/Y match the arcade block-A for that
  pose, and does any map to a wrong Genesis tile (the one-tile displacement)? (tip) which arcade thrust piece is
  absent from all native lanes? (palette) confirm colbank/line at the flash frame.

**Colbank-drop micro-question — RESOLVED STATICALLY:** the arcade **always** writes colbank **0x60** during
gameplay. Primary writer 0x3A1CC: `moveq #96,d0` (0x60) `; andiw #15,a5@0x14 ; orw a5@0x14,d0 ; movew d0,0x380000`
⇒ sprite_ctrl bits 0x00E0 = 0x60 every frame. Effect writers 0x3EF28/0x3EF48 only set/clear **bit 3 (0x08)** —
inside the low nibble, NOT the 0x00E0 colbank. `clrw 0x380000` (0x3AE9C) is the level/init **reset** routine
(also clears 0x200000 palette RAM, 0xD01BFE, 0x10C000 workram), not per-frame. ⇒ On Genesis, d7 should be
(0x60&0xE0)>>1 = 0x30 every gameplay frame, giving d0=0x33 → **inline line 3**. **Therefore the observed 3→0→3
is a Genesis-side defect: `pc090oj_sprite_ctrl_shadow` (or the value the commit latches) is momentarily 0/stale
when the arcade value is 0x60.** Candidate Genesis causes to check: (i) a spurious
`genesistan_pc090oj_sprite_ctrl_clear` invocation; (ii) commit/`.Lnative_pal_fixup` latching the shadow across a
partial update; (iii) shadow not re-asserted after some scene/state event. **Bounded fix once (i/ii/iii) is
identified:** ensure the commit uses the last-valid 0x60 colbank (never a transient 0). Do NOT freeze the sword
line. **Irreducible remaining fact:** the value of `pc090oj_sprite_ctrl_shadow` (0xFF…) at the F1947 commit —
recoverable from Cody's next capture (add `pc090oj_sprite_ctrl_shadow` to the sampled set) or a bounded arcade
check; NO speculative patch until known.

---

---

## SESSION 6 — CAPTURE-BACKED ROOT CAUSES (Cody's corrected controlled capture)

Capture: `states/traces/build0279_user_controlled_sword_lizardman_corrected_20260812_092432/`
(final_sat.csv has per-slot `source_nibble`+`palette_line`; native_queues.csv has per-piece word0/code/x/y;
lizard_actors.csv full actor state). No new capture run by Andy.

### GEOMETRY — one-tile / displaced sword — ROOT CAUSE **PROVEN**
- At the STANDING marker frame (5263) the Genesis PLAYER_BODY queue = 9 valid body pieces (torso 8E/8F/90,
  head 9E/9F, legs 76–79) **plus 3 malformed pieces**: `code=09D9/09DA/09DB`, `word0=0x0010`,
  `x=0xCCCC/0xEEEC`, `y=0xCCCC` (UNMASKED, > 0x1FF). Across the whole capture these 3 codes appear ~2.5k× each,
  **always** with 0xCC-fill coords.
- Source (proven by disasm): the **aux three-piece segment** `arcade_pc 0x5475A` (redirected to PLAYER_BODY;
  postpatch `runtime_genesis_pc 0x5492A+`). It emits `word0=0x0010`, `code=0x09D9 + a5@0x1364` (Genesis WRAM
  counter), and `X=a0@2 / Y=a0@4` where `a0 = 0x10D338` (Genesis WRAM sub-object array). Gate: skip when
  `a0@0 == 255`.
- **Why garbage on Genesis:** the attack sub-object at `0x10D338` takes its anchor X/Y from **block-A tuple 0
  (0x10D1B2)** via `arcade_pc 0x51E00` / `0x51DAE` / `0x547C0`. Build 0274 **retired the block-A writes** (native
  lanes replace them), so `0x10D1B2` is now stale/uninitialised (0xCC), and `a0@0 ≠ 255` so the segment is NOT
  skipped → 3 garbage sprites at 0xCC coords every frame. This is exactly the **auxiliary-anchor review debt**
  (0x129A/0x129C/0x547C0/0x51E00) flagged in earlier sessions.
- **Note:** the native BODY primary/secondary constructors (0x54492/0x546A8) DO mask X/Y (`andi #0x1FF`) and are
  correct in the postpatched ROM (table pointer relocated 0x5C466→`0x5C636`). The bug is ONLY the aux-anchor path.
- **Bounded fix direction (PROVEN target, not yet implemented/validated):** source the aux sub-object anchor from
  the **native anchor a5@0x129A/0x129C** (published by `native_player_body_anchor_piece`) instead of the retired
  block-A tuple 0; OR keep block-A tuple 0 alive solely for this anchor; OR gate the aux segment on the native
  anchor validity. Must preserve movement/landing and not resurrect block-A tuple staging broadly.

### PALETTE 3→0→3 — PARTIALLY PROVEN
- Capture (final_sat, frames 9167–9200): most nibble-3 slots resolve to line 3, but intermittently specific high
  PLAYER_BODY slots resolve to **line 0 or line 2**. `source_nibble` there is read straight from
  `pc090oj_sat_nibble[slot]`.
- **The line-2 cases are the garbage aux pieces** (word0=0x0010 → nibble 0; nibble0|colbank0x30 = 0x30 → line 2).
  So fixing the aux-anchor geometry bug ALSO removes the line-2 pollution.
- **Line-0 on genuine nibble-3 pieces still unexplained:** with shadow=0x0060 (colbank d7=0x30) and stored
  nibble 3, `.Lnative_palsel` must give 0x33→line 3. The intermittent line-0 (e.g., frame 9181 slots 11/12,
  hf=0) contradicts the static path. `pc090oj_sat_force_line` can only be 0xFF/3 (never 0). Remaining candidates:
  a fixup-coverage/emitted_count vs SAT double-buffer race for high slots. **Irreducible fact needed:**
  `pc090oj_emitted_count` and `pc090oj_sat_nibble[slot]` vs the DISPLAYED bank at the exact line-0 frame — NOT in
  the current capture (it logs post-fixup SAT + nibble, not emitted_count-vs-slot alignment per bank). Small,
  bounded.

### DOWNWARD-THRUST TIP 0x0104 — NOT CAPTURED (gap)
- Code `0x0104` is **absent from every native lane in all 16,256 frames**. The DOWN_THRUST marker window
  (frame 15617 ±) shows action=0, attack_type=4, **anim_phase stuck at 0x18** = STANDING config (per Cody's model
  standing=action0/var4), NOT thrust (action2/3, var1). So the thrust animation (phases 6–23 with 0x0104) was
  **never in the capture** — the instrumentation gap Cody noted. Statically, 0x0104 is not blank-marked and its
  art is non-blank, so IF produced it would render; whether Build 0279's retained thrust path produces 0x0104 is
  **unverified** (needs a correctly-labeled thrust capture, keyed on action∈{2,3} + variant 1).

### LIZARDMAN — composition CORRECT in capture (no code-level defect found)
- Bad-club frames (10007–10385): actors class **0x17 and 0x18**, family 0, base_tile 0x4B, attr 0x46. At frame
  10168 the BACK_ENEMY queue contains the **complete** composition — 0x004B,0x004C,0x004D,0x004E AND
  0x0063,0x0064,0x0065,0x0066,0x0069 (+0x5E–0x60) — every piece with **valid coords** (x 0xB4–0xCC, y 0x5A–0x7A)
  and **word0=0x4046** (flipX + nibble 6 → bank 0x36 → carrier line 0, per PAL-PC090OJ-STAGE1-LIZARDMAN-001).
- ⇒ ordering, count, coords, flip and palette of the club are all correct in the native queue; Cody proved the
  transform faithful. **No club code/geometry defect is evident in the data.** The "rotated" perception, if real,
  would require an arcade-vs-Genesis resident-ART content comparison (tile bitmaps), not a queue/transform fix.
  **No club patch justified** (matches Cody). Lizardman palette unchanged.

### DISPROVEN this session
- "Blank-bitset drops the tip/sword": DISPROVEN (0x104 and all sword/club codes are not blank-marked).
- "Colbank shadow drops to 0": DISPROVEN (shadow=0x0060; arcade always writes 0x60).
- "Secondary constructor emits garbage / table pointer unrelocated": DISPROVEN (masked + relocated correctly).

---

## Scope guards (must hold)
- Do NOT touch large-bat / small-bat / Axe / four-armed-enemy palettes.
- Do NOT restore PC090OJ player tuple staging.
- Do NOT alter Lizardman palette.
- Preserve Build 0279 movement/landing.

---

## SESSION 8 — VIDEO-BACKED BACKSWING GEOMETRY

### USER VISUAL CONTRACT (Build_279_sword_flash.mp4, reviewed frame-by-frame)
- Sword should ANGLE BACKWARD from the hilt during the backswing.
- Build 0279 shows the blade at the WRONG angle (vertical), floating up-left of the raised hand.
- Blade visibly DISCONNECTED from the hilt/hand.
- A vertical-looking frame is NOT correct just because it is coherent.
- Sword continuously changes black/white/gray during the attack (palette instability — REAL, out of scope here).

### WHAT THE AUX 0x09Dx PIECES ACTUALLY ARE — PROVEN
- Rendered from `build/pc090oj_genesis.bin`: codes 0x09D9=4-point star, 0x09DA=round ball, 0x09DB=4-point star
  = **sword GLINT/sparkle effects**, NOT blade art.
- In the capture their SAT screen position is fixed at ~**(204,196)** (from ROM `0xCCCC/0xEEEC` & 0x1FF), i.e.
  mid/lower-screen, FAR from the player (player pieces at sx 16–32). So the garbage glints are a real defect but
  are **not** the "vertical disconnected blade near the player."

### BACKSWING COMPOSITION (capture, exact)
- Peak backswing (frame 3240, primary sel 05): 09B/09D/09C + head A6/A7(nib6) + legs 76-79 + 3 garbage 09D9.
  Rendered composite = arm+sword roughly connected; head abuts body at +24. Individual flips (body flipX / head
  no-flip) MATCH correctly-rendered walking.
- **Secondary attack pieces 0109/010A NEVER appear** in the whole capture, though the primary reaches sel 05.
  Decoded secondary table 0x5BA78→0x5C466: index 0x00 (phases 0-3)=76-79 legs; index 0x11 (phases 4-23)=**0109@
  (-16,+8),010A@(0,+8)** (attack legs). Build 0279 keeps emitting 76-79. Real defect, but affects the LEG stance,
  not the blade/hilt connection.

### PIXEL CONNECTION TEST
- Expected arcade: blade angles back over the shoulder, connected to the hand.
- Build 0279: blade vertical/disconnected (video) — reproduced partially in static composites but NOT cleanly to
  the exact vertical pose; my composites of sel 01/05 show connected diagonal/horizontal swords, so the exact
  vertical-disconnected frame is not fully reproduced from the static offset model I could reconstruct.

### ROOT CAUSE (this session)
- **Aux garbage contributes: YES** — floating glints at (204,196) + continuous appearance change. **PROVEN,
  FIXED this build.**
- **Legitimate BODY composition also wrong: SUSPECTED, NOT PROVEN to a bounded correction** — the exact
  blade-angle/hilt-connection defect could not be isolated to a single bounded source (flip matches walking;
  offsets match Cody's model; the vertical pose was not cleanly reproduced statically). The secondary 0109/010A
  omission is proven but is legs, not blade.
- **Flip-specific defect: NOT PROVEN** — body flipX matches correct walking; no speculative Hflip change made.

### CROSS-POSE IMPACT
- Standing / Crouch / Downward thrust: all three share the same aux sub-object array (0x10D338) → all fixed by
  the raw-address correction. The blade-angle question is standing-specific and remains open for all three.

### CORRECTION IMPLEMENTED (Build 0280)
- **ONLY the proven aux raw-WRAM-address correction**: `movea.l #0x0010D338` → `movea.l #0x00FF1338` at arcade
  0x051650 / 0x051DB6 / 0x054754 (byte-neutral opcode_replace, count 217→220). The aux sub-object now reads WRAM
  0x00FF1338 (init to 255=inactive), so the garbage glints vanish and the glint activates at the native anchor
  (sword tip) only when legitimately active. **No BODY sword-composition change** (blade cause not bounded), **no
  palette change**, no speculative Hflip. One-time activation-anchor lifecycle preserved; no Block-A staging.
- Build 0280: SHA-256 1c129ff84a4fc228df5702cca008dad23f90c5b47e1d204db5c8e7ce48a7f69b, size 1591520,
  counter 279→280, GATE_PASS, 30s Genesis-NTSC smoke clean (1021% speed, no crash).

### REMAINING OPEN (for a follow-up task)
- The vertical/disconnected blade ANGLE (BODY composition) is not yet bounded. The one irreducible remaining
  question: an ORIGINAL-ARCADE pixel reference of the standing backswing composite (or the exact head/primary
  offset+facing handling for A6/A7 and the sel-progression) to determine whether the blade angle is a flip,
  offset, or missing-piece (0109/010A) defect. The palette black/white/gray instability is separately real and
  out of scope here.

---

## SESSION 9 — DIRECTIONAL SWORD MIRROR CLOSURE

### BUILD 0280 USER TEST
- LEFT standing: PASS · RIGHT standing: FAIL · LEFT crouch: PASS · RIGHT crouch: FAIL · Down thrust: FAIL
- Aux garbage sprites: FIXED · Sword palette cycling: STILL PRESENT

### VISIBLE FACING SEMANTICS (PROVEN from capture)
| Visible direction | a5@0x1114 | body path | word0 |
|---|---|---|---|
| VISIBLE_LEFT | **2** | direct (no mirror, `cmpi #2` == → skip flipX) | 0x0003 (no flip) |
| VISIBLE_RIGHT | **3** (and 0) | mirror: X = −Xoff−16, set flipX 0x4000 | 0x4003 |
Walking-right uses the same mirror and is correct ⇒ the mirror path itself is sound.

### A6/A7 ARE THE EXTENDED SWORD BLADE (not the head)
Rendered from the art blob: **0x00A6 = horizontal sword blade**, 0x00A7 = tip/hilt. They come from the BODY
**inline-segment expander** (arcade 0x54598; tables 0x5CD8A/0x5D068/0x5D346/0x5D666 by a5@0x12FA). In the
capture they alone carry **mirrored X but NO flipX** (nibble 4 LEFT / 6 RIGHT) while every other piece flips.

### FIRST EXACT RIGHT-FACING MISMATCH — ROOT CAUSE (PROVEN)
Arcade inline loop: 0x545EE stores word0 = attr|flipX to Block A, THEN 0x54602 reuses **D1** as the
`a5@0x1308` code-selection index `((a5@0x1308>>1)&3)<<1` (safe on arcade — word0 already stored). The native
redirect put word0 into **D1** (0x545EE→`movew d0,d1`); the retained 0x54602 then **clobbers D1**, so
`native_player_piece` (emit at 0x5464A) receives the index, not word0 → **flipX + descriptor nibble 3 lost**.
- VISIBLE_LEFT (facing 2): needs no flip → geometry correct despite the clobber (POSITIVE CONTROL).
- VISIBLE_RIGHT (facing 3): flipX lost → blade mirrored in position but unflipped art → **gap + wrong
  orientation**. This is a register-lifetime defect in the inline redirect (same class as Build 0275).

### STANDING / CROUCH / DOWN-THRUST — SHARED
All three drive the SAME inline segment for the blade, so all lose flipX facing right. **Shared correction.**
(The down-thrust *vertical* displacement and the secondary 0109/010A leg-stance omission are SEPARATE, still
open — not addressed in this build.)

### BOUNDED CORRECTION (Build 0281)
Move the inline code-selection index from **D1 → free D7** at the computation (arcade 0x54602/06/08/0C) and its
four alternate-table uses (0x5465E/6A/76/82) — 8 byte-neutral opcode_replace (register-field only). D1 now
preserves the correct word0 (nibble 3 + flipX). D7 is scratch (native_sprite_emit saves d0-d7; not a native
input; unused elsewhere in the inline loop). Restores blade flip AND descriptor nibble 3 as a direct
consequence of preserving word0 — **not** a palette-routing change; PAL decisions untouched. No BODY
table/offset change, no Hflip toggle, no aux change (0x00FF1338 preserved).
- Verified in ROM: `movew a5@(0x1308),d7` + `addaw d7,a2`; d1 untouched from word0-realization to emit.
- Build 0281: SHA-256 8f4997566386f30c0c3dd37f922762d7f6b0677f8bbd9c4a8995046dfb9ab790, size 1591520,
  counter 280→281, opcode_replace 220→228, GATE_PASS, 30s Genesis-NTSC smoke clean.

### STILL OPEN (follow-ups, not in this build)
- Down-thrust VERTICAL displacement (separate Y cause).
- Secondary 0109/010A attack-leg omission (retains 0076-0079).
- Sword palette black/white/gray cycling (out of scope; a5@0x1308-nibble corruption on A6/A7 is now removed,
  which may reduce — but not necessarily eliminate — the flashing).
