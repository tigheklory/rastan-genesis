# Andy — Arcade FG Decompile, Part 2: Semantic-Contract Verification

**Type:** Analysis / decompilation. **Production changes: NONE. ROM: NONE.** Accepted baseline: Build 0297.
Scope: arcade Plane-A/FG semantics + the FG→collision-map contract. Evidence: Ghidra
`analysis/ghidra/rastan_arcade/exports/` (decompiler, full listing, xrefs, call graph). Addresses `arcade_pc`
/ arcade WRAM `a5@0xNNN` (a5 = 0x0010C000).

## 1. Phase-0 priors
- **CONFIRMED/STRONG:** KF-010 (FG→Plane A / BG→Plane B), KF-014 (tile LUT, code domain 0x0000..0x3FFF),
  KF-015 (full-plane scroll, raw-Y negation +8 bias, no per-line), KF-011 (arcade Level-5 VBlank owns
  progression). Memory map: PC080SN C-window 0xC00000-0xC0FFFF; a5 base 0x10C000.
- **Rediscovery-Hazard HIGH:** KF-011, KF-020/21 (contaminated plane/sprite evidence — avoided).
- **OPEN:** OPEN-001/018 (native map/level incomplete), OPEN-017 (FG/BG progression, hardware, collision).
- **Task classification:** EXTENDING (closes Part-1 unknowns).
- **CONFIRMED/STRONG contradiction:** NONE. (One census *label* correction — `DEST_BG_OFFSET=0x10A0` — see §7;
  that is a Genesis-symbol naming issue, not a KF contradiction.)

## 2. Part-1 accepted findings (unchanged)
Gameplay FG family `player_main_update_51090 → FUN_00055650 → {55696 down / 0572e up / 057ba right / 05854
left} → FUN_00055948 → {55968→559b2 / 55990→55a14} + 558a2/558c6/55904/558e0`. Terminal writers publish FG
cells AND the collision map. State: 0x10D0 direction bitmask, 0x10CA strip idx, 0x10CC group, 0x10A8
selector, 0x10A0/A4 dest, 0x10AE/B0 FG X/Y scroll, 0x10D000 source table.

## 3. FG source-table initialization chain (arcade)
`FUN` at **arcade 0x0503A0** (the stage FG map-source setup) — proven from `full_listing.tsv`:
```
0x503A0 move.w 0x1386(a5),d1     ; a5@0x1386 = FG map table index
0x503A4 move.w #6,d0 ; lsl ; mulu.w d1,d0   ; index * stride
0x503AC move.l #0x0003951C,d0 ; add.l d1,d0 ; → 0x3951C + index*stride
0x503B4 move.l d0,0x10FC(a5)    ; a5@0x10FC = descriptor-walker base (ROM 0x3951C family)
0x503BC movea.l #0x00050EE0,a1
0x503C2 move.w 0x13E(a5),d1      ; a5@0x13E = STAGE id
0x503C6 lea 0x1000(a1,d1),a1 ; move.b (a1),d1   ; stage → byte from ROM table 0x50EE0+0x1000
0x503CE move.l #0x00050F6B,d0 ; add.l d1,d0
0x503D6 move.l d0,0x10C6(a5)    ; a5@0x10C6 = FG map PAGE pointer (ROM 0x50F6B + stage byte)
```
**Semantic chain:** stage id `a5@0x13E` + FG-map index `a5@0x1386` → ROM descriptor table **0x0003951C**
(→ `a5@0x10FC`) and ROM page-pointer tables **0x00050EE0 / 0x00050F6B** (→ `a5@0x10C6`). Thereafter
`FUN_000558e0` (page wrap) and `FUN_00055904` (rebuild) walk `a5@0x10C6` to (re)populate the 16-entry source
pointer table `a5@0x10D000..0x10D03C` → derived word arrays `0x10D040` (attr) / `0x10D080` (tile) and
`0x10D0A8 = **(a5@0x10C6)`. So: **stage/map semantic choice → ROM source table selection → per-page source
pointer population → FG publication.**

## 4. ROM / data-table ownership
- **0x0003951C** — FG/plane descriptor table base (index by `a5@0x1386`). (Census called this
  `PLANE_B_DESC_TABLE_ARCADE_BASE`; it is the shared descriptor base used here for FG-walker `a5@0x10FC`.)
- **0x00050EE0 (+0x1000)** — per-stage byte table (index by stage `a5@0x13E`).
- **0x00050F6B** — FG map page-pointer base (+ stage byte → `a5@0x10C6`).
- **0x10D000..0x10D03C** — WRAM 16-entry source pointer table (rebuilt per page).

## 5. Initial-state field table (at stage FG init / page wrap)
| Field | Init | By |
|---|---|---|
| a5@0x10C6 | ROM 0x50F6B + stage byte (page pointer) | 0x503D6 |
| a5@0x10FC | ROM 0x3951C + index*stride (descriptor walker) | 0x503B4 |
| a5@0x10CA (strip idx) | 0 | FUN_000558e0 (0x10CA=0) |
| a5@0x10CC (group/page) | 0 | FUN_000558e0 |
| a5@0x10D0A8 | `**(a5@0x10C6)` | FUN_000558e0/55904 |
| a5@0x132C | = a5@0x10A8 (selector snapshot) | FUN_000558e0 |
| a5@0x10AE/0x10B0 (FG X/Y scroll) | accumulate from deltas (0-init at stage load) | 55696/0572e/057ba/05854 |
| a5@0x10A8 (selector) | set by scene/map setup (value ∈ {0,1,2,4,5,6}) | scene/map (§6) |

## 6. Selector `a5@0x10A8` semantics — PARTIAL
- **Value set is {0,1,2,4,5,6}** (not just {0,1,2}) — `FUN_00052732`:
  `if (0x10A8 ∈ {4,5,6}) a5@0x10E8 = 7;`. So there are **two families**: `{0,1,2}` (standard) and `{4,5,6}`
  (sets FG traversal-mode flag `a5@0x10E8=7` — a distinct scroll/geometry mode).
- **Writer orientation (proven):** dispatch `FUN_00055948`: selector `==0` → `FUN_00055968` (4-tile vertical
  column, stride 0x80); `else` (1/2/4/5/6) → `FUN_00055990`→`FUN_00055a14` (4-tile horizontal row, stride 2)
  with strip-index parity `~idx & 3` applied unless selector `==2`.
- **Unproven (design-sufficient, not blocking):** the exact per-scene *assignment* of which stage sets which
  selector value, and the precise downstream geometric effect of `a5@0x10E8=7`. This is not required for the
  native design because the producer reads `a5@0x10A8`/`a5@0x10E8` **at runtime** and realizes whatever value
  is present — but "fully understood" is therefore **NO** on the per-scene mapping.

## 7. `a5@0x10A0` / `a5@0x10A4` ownership — RESOLVED (Resolution A)
Both are **FG (0xC08000) destinations** in the gameplay FG chain (decompiler lines 7980/8013/8054/8219):
- `a5@0x10A4 = 0xC08000 + geometry` set by `FUN_00055696` (down) and `FUN_0005572e` (up); consumed by the
  selector-≠0 writer `FUN_00055990`.
- `a5@0x10A0 = 0xC08000 + geometry` set by `FUN_000557ba` (right); consumed by the selector-0 writer
  `FUN_00055968` (which also updates it with the post-write A0).
The true BG (Plane B) destination is a **separate** field `a5@0x10F8 = 0xC00000 + geometry` in the
`FUN_00055AD6/55b3c` chain. **Conclusion:** the Genesis symbol `ARCADE_PC080SN_DEST_BG_OFFSET = 0x10A0` is a
**misnomer** for the gameplay FG context — 0x10A0 is an FG dest there. (No production rename in this task.)

## 8. Original-arcade runtime verification — NOT PERFORMED (static-conclusive)
Per CLAUDE.md's static-first mandate, this task settled the model from Ghidra decompilation/xrefs/call-graph;
the static evidence is internally consistent and conclusive for the design-critical contracts (§3, §7, §10,
§11, §12). **No ARCADE MAME run was performed** — I am not asserting runtime evidence I did not capture. The
one genuinely-dynamic item that would benefit from targeted ARCADE MAME confirmation is the **selector
value per stage** (§6) and the accumulator thresholds/page-wrap timing; recommended as a short, focused
follow-up (sample `a5@0x10A8/0x10E8/0x10CA/0x10CC/0x10D0/0x10BA/0x10B8` across a Stage-1 scroll + a stage
transition). No static/runtime contradiction is known.

## 9. Static-vs-runtime corrections
None (no runtime run). Two Part-1 refinements from deeper static analysis: (a) selector set is
{0,1,2,4,5,6} not {0,1,2}; (b) 0x10A0 is an FG dest (census label corrected).

## 10. FG collision-map WRITE contract (§5A)
The terminal writers `FUN_000559b2` (col) and `FUN_00055a14` (row) each write, per published cell:
- **Plane (visual):** `*A0 = tile_word` (from source), `A0[1] = attr_word` (descriptor).
- **Collision:** `*(collision_map_ring + ((A0 − 0x604000) >> 1)) = descriptor_word` — the collision **value**
  is a descriptor word (from the FG source block A2 at `A2+0x20+strip_index*2+i*8`, or `A2+0x22` when the
  block is a `0xFF`-terminated run), i.e. **the same source table drives both the visible tile and its
  collision value.**
- **Geometry:** the collision entry position is derived from the FG **destination** geometry (same ring as
  the plane). All 4 cells emitted by each terminal writer produce collision entries. Selector/parity affects
  the source index (`~idx&3` unless ==2) identically for plane and collision. A `0xFF`-terminated descriptor
  selects the `A2+0x22` run value (blank/uniform) for both.

## 11. Collision-map lifecycle (§5B)
- **Indexing / lookup:** `collision_map_lookup_53a2e` returns a ring index = `((D2y + (~a5@0x10B0+1 & 0x1FF))
  & 0x1F8)*0x20 + (((D1x + (~a5@0x10AE+1 & 0x1FF))>>1)+8 & 0xFC)) >> 1` — a **64-wide word ring** addressed
  by (actor position + FG scroll registers 0x10AE/0x10B0). So the map is a **screen-space ring** locked to
  the FG scroll; entries are **overwritten in place** as the FG scrolls (publication == retirement via ring
  geometry — no separate clear). This means graphical clearing and collision clearing are the **same** ring
  overwrite, driven by FG publication. Stage/scene reset is via the FG source re-init (§3) + the C-window/
  plane clear fills; the collision ring re-fills as the new stage's FG publishes.

## 12. Principal collision consumers (§5C)
`collision_map_lookup_53a2e` is called by the terrain-collision family:
`player_collision_probe_family_53a6e`, `player_ground_contact_probe_family_53b34` (player floor/wall),
`actor_velocity_and_map_collision_42e38`, `actor_spawn_ground_and_activate_41180`,
`actor_surface_marker_find_41064`, `actor_map_collision_variant_45d10/4736a` (enemies). **Value
interpretation (proven, `player_collision_probe_family_53a6e`):** `*A0 & 0x7F` = terrain type —
**1 = floor/ground, 2 = solid/wall, 0 = empty/passable** (sets a5@0x10CE bits 0x02 / 0x20). So the contract
is: **FG descriptor word → collision ring value → `&0x7F` terrain class → player & enemy floor/wall/ground
tests.** Both player and actors consume it.

## 13. BG relationship to the collision map (§5D)
The BG/Plane-B publisher (`FUN_00055AD6 → FUN_00055b3c → FUN_00055c4a/55c5e/55c7a`, dest 0xC00000) writes
**only plane data — NO collision-map write** (verified: none of those functions reference the collision ring
or the `0x604000` derivation). **Terrain collision is FG-exclusive.** BG (Plane B) is background scenery
only; it shares the strip/descriptor *machinery* but not collision ownership. (BG not further decompiled.)

## 14. Semantic cut-boundary revalidation
**Recommended boundary: `FUN_00055650`** (Part-1 recommendation holds, now evidence-backed):
1. It preserves all arcade-owned state-machine decisions (direction bitmask 0x10D0, accumulators, cursor
   0x10CA/0x10CC, source table 0x10D000, page pointer 0x10C6, selector 0x10A8, mode 0x10E8, scroll regs
   0x10AE/0x10B0, and the advance/rebuild/page-wrap `558c6/55904/558e0`) — all Category-D input.
2. A native Plane-A producer can operate purely from that state without reconstructing game logic (the arcade
   still owns movement, source progression, and scroll).
3. It can reproduce BOTH final Plane-A publication AND the collision ring — because both derive from the same
   source descriptors + FG scroll geometry it reads.
4. It does NOT bypass source progression / strip-group-page / selector / scroll / collision — those remain
   arcade-owned state the producer consumes.
5. No better boundary: lower (selector writers) fragments the producer (the current defect); higher
   (FUN_00052732/state machine) would move game logic into Genesis (violates KF-011).
**Caveat for design:** the native producer MUST (a) handle all six selector values (0/1/2 column/row +
4/5/6 with the a5@0x10E8=7 mode), and (b) reproduce the FG-exclusive collision ring (value = descriptor word,
`&0x7F` terrain semantics, ring geometry via FG scroll), or player/enemy terrain collision breaks.

## 15. Remaining unknowns
1. Per-stage **selector value assignment** and the exact geometric effect of `a5@0x10E8=7` (mode for
   selectors 4/5/6) — design-sufficient (runtime-read) but not "fully understood"; targeted ARCADE MAME
   confirmation recommended.
2. The line-by-line `FUN_000558e0` per-page fill of `0x10D000` (role proven; exact loop not transcribed).
3. Runtime confirmation of accumulator thresholds / page-wrap timing (static values: Y boundary 0x100/8,
   X boundary 0xA0, fine `&8`, group wrap 0x10).

## 16. Observation vs interpretation
All §3–§13 statements above are OBSERVED from decompiler/listing/xrefs; INTERPRETATION is confined to the
semantic labels (e.g. "terrain type", "page pointer") which follow directly from the consumer code (§12) and
the init math (§3). No runtime observations are claimed.

## 17. Open/Closed Issues impact
OPEN-017 (collision / FG progression): materially advanced — the terrain-collision producer contract is now
proven (FG-exclusive, value `&0x7F`, ring geometry). Not closed (implementation pending; consumer breadth is
gameplay-critical). OPEN-001/018 (native map/FG): the FG source-selection + cut boundary are now proven,
enabling a single native Plane-A design. No issue closed by analysis.

## 18. KNOWN_FINDINGS impact
Recommend **Option A (new finding)**, to Tighe review — durable, high-value: *the arcade PC080SN FG terminal
writers (FUN_000559b2/55a14) are the sole producers of the gameplay terrain collision map; the collision
value is the FG descriptor word, interpreted `&0x7F` (1=floor,2=wall,0=empty) by the player/actor collision
family; the map is a 64-wide screen-space ring locked to the FG scroll registers 0x10AE/0x10B0; BG/Plane-B
writes no collision. Any native Plane-A producer must reproduce this side-channel.* Separates proven-static
from the runtime-recommended selector-per-scene item.

---

**FG stage initialization fully understood: YES** (stage/index → ROM 0x3951C/0x50EE0/0x50F6B → 0x10C6/0x10FC
→ per-page 0x10D000 rebuild).
**FG selector semantics fully understood: NO** — value set {0,1,2,4,5,6}, two families, writer orientation,
and the a5@0x10E8=7 mode flag are proven; the **per-stage value assignment** and the exact 0x10E8 geometry
effect are not fully traced (design-sufficient, runtime-confirmable).
**FG destination-field ownership fully understood: YES** (0x10A0 & 0x10A4 both FG/0xC08000; BG dest = 0x10F8;
Genesis DEST_BG label is a misnomer).
**FG collision side-channel fully understood: YES** (value = descriptor word; ring geometry via FG scroll).
**FG collision consumer contract fully understood: YES** (`&0x7F`: 1 floor / 2 wall / 0 empty; player + actor
terrain family).
**FG state-machine runtime model verified: NO** — analysis was static (Ghidra-first); static-conclusive; a
targeted ARCADE MAME confirmation of the selector-per-scene values + accumulator thresholds is recommended
and was not performed.
**Recommended native FG semantic boundary: `FUN_00055650`** (arcade retains the state machine + source table
+ scroll + selector/mode as input; one native producer writes staged_fg_buffer + the collision ring).
**Ready to design one native Genesis Plane-A producer: YES** — design-sufficient, provided the design handles
all six selector values + the 0x10E8 mode and reproduces the FG-exclusive collision ring; the two runtime
items in §15 are confirmations, not blockers.
