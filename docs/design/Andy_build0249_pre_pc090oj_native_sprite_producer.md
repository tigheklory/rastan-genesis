# Build 0249 — Pre-PC090OJ Native Sprite Producer + Corrected SAT Contract (research; no source/build)

**Agent:** Andy. **Type:** sprite semantic-producer proof + SAT contract + HUD ownership (v2, corrected).
**Production source / remap spec / ROM / build / counter:** UNCHANGED (Build 0249 / counter 249;
`RASTAN_GAMEPLAY_HUD_SPRITES=2`). **Authority:** `address_map.json` (segment membership; never fixed-offset
inference), `specs/rastan_direct_remap.json`, manifest, Build 0249 `pc090oj_hooks.s`, arcade opcodes
(`build/maincpu.disasm.txt`), MAME `pc090oj.cpp`/`rastan.cpp` (oracle). **Evidence:**
`states/traces/build0249_pc090oj_contract_20260802_pre_pc090oj_contract/` (`contract.txt` arcade census/
snapshots/dispatch/retire; `gdrop.txt` Genesis drop identity; `title.txt` attract/frontend). PC090OJ object
RAM used **only as oracle**.

## Native-hardware-replacement acknowledgement (policy §4/§12)
- **Semantic cut (RETAIN, arcade-owned):** actor lifecycle/active flag, animation frame, position, palette,
  flip, visibility (retire/blank/clip), and the fixed per-category **object-RAM record band** that fixes
  priority. This lives in the arcade actor logic + its render traversal + piece expander.
- **Chip tail (REPLACE, then prune):** the PC090OJ object-RAM record packing, the faithful 256-record
  object-RAM **mirror** (`pc090oj_object_ram`), and any generic record decoder. The native tail is a shared
  SAT append primitive fed by the piece expander, consuming register-level `x,y,tile,pal,flip` — never an
  8-byte PC090OJ record.
- **Transitional compatibility retained during migration:** the mirror + the ascending `native_emit_pass`
  remain as the isolated production authority until each family is converted; producers/consumers and the
  removal boundary are in §8/§11.

> This v2 **corrects** the prior v1 report. Do not carry v1's broad conclusions forward. The corrections are
> flagged **[C1]**–**[C6]** and are the substance of this task.

---

## 0. Corrections at a glance (what v1 got wrong)

- **[C1] Append order is NOT "traversal order."** It is **object-RAM record-index order = priority**. Actor
  categories own **fixed record bands** that are **not monotonic with the processing order** (§2, §3).
- **[C2] There is NO "2 dropped/frame SAT overflow."** `pc090oj_dropped_count` is a **lifetime** counter; it
  reaches **2 total at F=28 (cold start) and never moves**. Those 2 are **HUD tile-DMA-queue misses**, not a
  gameplay/SAT-slot overflow (§5, §5a).
- **[C3] The `0x0180` Y sentinel is downstream, not the decision.** The upstream visibility decision is the
  actor **active flag `a4@0`**, the **retire flag `a4@3` (+ `a4@26=0x180`)**, and the **blank frame `a4@11`**
  (§4). Native contract: visibility-false → **do not append** (no park record).
- **[C4] HUD ownership is reversed from v1.** Score/1UP → **reserved direct-SAT**; life/lives/ROUND/status →
  **bottom Window band**; the single Window carries only the **bottom** band (§7).
- **[C5] The main producer writes DIRECTLY to object RAM** (`a1=0xD00xxx` via `a1@+`); some categories use a
  workram→OJ block-copy (`0x41F5E`). Both are pre-mirror; v1's "workram is THE boundary" was only half true.
- **[C6] Priority direction is proven from MAME source**, not assumed from Sonic (§3).

---

## 1. Boundary classification (retained, refined)

- **`0x03C902` output (8-byte records in `a1`/object RAM) = PC090OJ-shaped oracle**: it already carries the
  chip word layout (`word0` attr/flip/palette, `word1` Y incl. the `0x0180` sentinel, `word2` code, `word3`
  X) and record index. Not a permitted final boundary.
- **The semantic boundary is BEFORE record packing:** the per-actor render traversal + the type-handler
  **piece expander**, whose inputs are the **actor struct `a4`** and **mapping descriptor `a0`**, and whose
  per-piece `X,Y,code,attr` exist in registers before the `a1@+` store.

## 2. Producer families + the fixed record-band ordering [C1][C5]

**Master gameplay build `0x41DAE`** (`hook_target_41dae`) walks fixed actor groups, each `lea`-ing its own
`a4` (actor table) and its own **fixed `a1` object-RAM base** (= fixed record band = fixed priority), then
calling the per-actor dispatcher `0x3D054`:

| Proc. order | actor table `a5+` | count | `a1` base | **record band** | `d2` budget | runtime class (this trace) |
|---:|---|---:|---|---:|---:|---|
| 1 | `0x508` | 2 | `0xD001C8` | **57** | 13 | players (idle slot; live player is the block, below) |
| 2 | `0x5C8` | 6 | `0xD00300` | **96** | 4 | mid enemies/objects |
| 3 | `0x2C8` | 9 | `0xD00460` | **140** | 10 / 19 | **lizard-men** (retire via `a4@3`→`0x3EFBE`) |
| 4 | `0x748` | 11 | `0xD00170` | **46** | 1 | **bats / effects / items** (1 piece each) |

Plus a workram→OJ **block-copy `0x41F5E`** (`lea %a5@(0x11B2),%a0; lea 0xD003C0,%a1`, 18 records = **rec 120**)
which is the **live player composite** in this trace, and dedicated HUD producers (`0x3B802` score, `0x5A098`
status). **Per-actor dispatcher `0x3D054`** reads render family `a4@(56)` → `0x4770E/3F0BC/3FFDC/3FFF0` or the
pc-rel table → **type dispatcher `0x03C902`** (type nibble `*(a0)&0xF0` → 9 handlers
`0x3C4D2/3C550/3C586/3C636/3C6DC/3C75C/3C7A4/3C830/3CA26`). Piece loop `0x3C516`/`0x3C960`:
`Y = pieceYoff + a4@(26) + a4@(24)`, `X = a4@(22) + col-offset`, `d2/d4` = piece count.

**[C1] Priority is the record index, not the processing order.** Processing order is grp1,2,3,4 but the record
bands are **46 (grp4) < 57/120 (players) < 96 (grp2) < 140 (grp3)**. So the front-to-back order is
**grp4 (bats/effects) → player → grp2 → grp3 (lizards, backmost)**. A native producer that appended in *call
order* would put the player in front of the bats — **wrong**. The append order must follow the **record band**
(which is exactly what the Genesis `native_emit_pass` already does: ascending record scan, §5a).

## 3. Controlled SAT priority-direction proof [C6]

**Arcade ground truth (`pc090oj.cpp` + `rastan.cpp` + MAME drawgfx):**
- `rastan.cpp:461` sets `set_colpri_callback` and `colpri_cb` returns **`pri_mask = 0`** ("sprites over
  everything"). So `draw_sprites` takes the **priority branch**: `start=0; end=0x400; inc=+4` → it iterates
  **record 0 → 255 (forward)** calling `prio_transpen`.
- MAME `gfx_element::prio_transpen` OR-s **bit 31 into the mask** and marks each drawn pixel's priority to 31.
  With `pri_mask=0` the effective test is "draw only where no sprite has drawn yet." Therefore **the first
  record to paint a pixel wins** ⇒ **record 0 = frontmost** (matches the chip header "First sprite has highest
  priority"). Lower record index = in front.

**Genesis VDP:** sprites are evaluated in link order from slot 0; on overlap the **earlier slot (lower link
index) is displayed in front** ⇒ **SAT slot 0 = frontmost**.

**Controlled comparison (three known, differently-coloured, overlapping records):** take a front bat
(`rec≈48`, its own pal), the player (`rec120`, **pal3**), and a lizard (`rec180`, **pal6**); arcade overlap
draws **bat over player over lizard** (ascending index = front→back).

| Model | slot mapping | resulting front→back | vs arcade |
|---|---|---|---|
| **Forward append** (record i → cursor slot in ascending scan) | bat<player<lizard | bat, player, lizard | **MATCH** |
| Reversed append (descending) | lizard<player<bat | lizard, player, bat | **INVERTED — wrong** |

**Conclusion:** **forward append in ascending record-index order reproduces arcade overlap; reversed inverts
it.** **Highest priority = the LOW end of the record range (record 0).** On the 80-entry SAT cap **or** the
Genesis per-scanline limit, the pieces that must **survive are the low-index (front) ones**; the **high-index
(back) pieces drop** — i.e. **drop-tail in record-index order** (already implemented, §5a line 1489). This is
proven from the two hardware models, not copied from Sonic.

## 4. Upstream visibility / retirement — backward from every `0x0180` [C3]

Every `movew #384,%a1@(2)` (Y=`0x0180`) write is **downstream** of one of three arcade-owned decisions:

| `0x0180`/park site(s) | Upstream decision (the real boundary) | Native contract |
|---|---|---|
| **Inactive-actor blank-fill** `0x41EB6/0x41ECA/0x41EDE` (master loop fills the whole band with Y=0x180) | **`a4@(0)==0`** — actor slot not active (`tstb %a4@(0); beqw` at `0x41DBC/0x41DF6/0x41E30/0x41E84`) | actor inactive → append nothing for the band |
| **Deferred-special blank** `0x41EDE` via `0x3EFBE` | **`a4@(3)!=0`** retire flag (`0x41E40 tstb %a4@(3)`) + `a4@(5)` death sub-state (`0x3EFBE cmpi #23`) | actor retired → append nothing |
| **Actor base-Y parked** `0x4105C/0x45276/0x453B4/0x4A0C0` writing **`a4@(26)=0x180`** alongside `a4@(3)=a4@(4)=a4@(28)=a4@(32)=1` | the actor **deactivation routine** (retire block) | same as above — one decision, `a4@(3)` |
| **Blank-frame park** `0x3C4EA` (and `0x3C610/6B6/712/7DE/874`) when `a4@(11)==` blank value (e.g. `cmpi #32` at `0x3C4E2`) | **`a4@(11)` = current animation frame == blank/dead frame** | blank frame → emit zero pieces |
| **Per-piece list end** `0x3C9F6` when the mapping byte `0xFF` sets `d5` (`0x3CA00`) | **piece-list terminator in `a0`** | stop appending at list end (no pad) |

**Bat retirement proven at this boundary (Build 0234 authoritative capture,
`states/traces/build0234_bat_stale_20260723_161930/arc_bat.txt`):** the hurry-up bats are **group-4 actors,
object records 48–56, codes `0x268/0x269/0x26A`, death frame `0x276`.** On the arcade a killed bat's record
goes to code `0x276` for ~1 frame, then **Y=`0x0180` by ~3 frames** and stays hidden — i.e. the arcade turns
the **death sub-state** into a park. The v1/Genesis divergence was exactly failing to hide it. In the native
model there is **no park record at all**: the bat's death sub-state makes visibility false → **`sat_append`
is simply not called** for that actor, so the corpse cannot persist. This is the correct upstream contract:
**semantic-visibility-false → no SAT entry**, never "append a Y=0x180 sentinel."

This trace re-observed the retirement mechanism live at `0x4A0C0/0x45276/0x4105C` (writing `a4@(26)=0x180`) for
group-3 actors dying/leaving during Stage 1 (`contract.txt` RETIRE LOG, F=675/708/715/740/1030/1079…).

## 5. Named producer-class coverage (individually captured)

From `contract.txt` snapshots (arcade oracle, Stage 1 F=430/700/1000) + dispatch/retire logs + Build 0234 +
`title.txt` (attract):

| Class | Actor / producer | Family / dispatch | Mapping/frame | Pieces (16×16) | Piece-loop PC | Visibility decision | Record band = priority | Pal |
|---|---|---|---|---|---|---|---|---|
| **Rastan (player)** | live composite via block-copy `0x41F5E` (workram `a5+0x11B2`) | actor expander → workram | frame `a4@11`, mapping `a0` | ~9–13 (codes 138–159) | `0x3C516` | active/frame | **rec 120–137** (in front of enemies) | 3 |
| **Lizard-man** | group-3 `a5+0x2C8` (9 slots) | `0x3D054`→type disp `0x3C902` | `a0@(2)`, `d2=10/19` | 8 (2 col × 4 row, codes 75–109) | `0x3C516`/`0x3C960` | active `a4@0`, retire `a4@3`→`0x3EFBE` | **rec 140–238** (backmost) | 6 |
| **Hurry-up bat** | group-4 `a5+0x748` | `0x3D054` (`d2=1`) | codes `0x268–0x26A`, death `0x276` | 1 | type handler | **death sub-state** → hide (Build 0234) | **rec 48–56** (near front) | — |
| **Item / pickup** | group-4 `a5+0x748` | `0x3D054` (`d2=1`) | mapping `a0` | 1 | type handler | active/frame | **rec 46–56** | — |
| **Weapon / effect** | group-4 / projectile | `0x3D054` (`d2=1`) | mapping `a0` | 1–2 | type handler | active/frame | **rec 46–56** (front) | var |
| **P1 score / 1UP** | `hook_score_digit 0x3B802` | HUD producer | digit code | 5 (codes 0x3A–0x3E) | digit loop | scene-id gated, always in gameplay | **rec 4–8** (absolute front) | 0 |
| **Life / status / ROUND** | `hook_status_sprite 0x5A098` (+bars) | HUD producer | bar/text code | ~37 (codes 42–73, 970–981) | status loop | scene-id gated | **rec 9–45** (front) | 0 |
| **Title / story** | tilemap (PC080SN); sprites = HUD family only | none (frontend) | — | 0 gameplay sprites | — | **scene-id ≠ gameplay** gate | HUD band only, no gameplay family | 0 |

**Frontend separation proven:** attract/title (`title.txt`, F40–150) shows **only the 42 HUD records (rec
4–45, pal0)** in object RAM — no gameplay family. The title logo/story is tilemap. The Genesis emit pass gates
HUD/gameplay on `genesistan_current_scene_id == PC090OJ_SCENE_GAMEPLAY_ID` (`pc090oj_hooks.s:1287/1304/1337`),
so frontend and gameplay producers are scene-separated at the source level.

## 5a. Corrected runtime cycle census [C2]

**Arcade producer truth (`contract.txt`):** drawable object records/frame = **67 (F430), 83 (F700), 74
(F1000)**. Of these, **~42 are HUD/status (rec 4–45, pal0)** and the rest are gameplay (player pal3 +
lizards pal6). Object-RAM writes/frame are dominated by a per-frame **band clear + rebuild** (PC-band `0x41xxx`
≈ 145–190 word writes/frame; that includes the clear, not just live records — v1 mis-labelled raw writes as
"records").

**Genesis emit + drop truth (`gdrop.txt`, Build 0249 runtime):**
- `native_emit_pass` scans `pc090oj_object_ram` **records 0→255 ascending** and appends one 16×16 SAT entry
  per drawable record, cursor = SAT slot (link = cursor+1). **Slot order = record order = priority.** Cap
  `NATIVE_SAT_MAX=80` (`pc090oj_hooks.s:1489`) → drop-tail past 80.
- **`emitted_count` (per frame, set not accumulated): 14 (F900) → 34 (F1250).** Well under 80. **No SAT-80
  overflow occurs in normal Stage-1 play.**
- **`pc090oj_dropped_count` is cleared only at boot (`0x386`)** and only incremented (`0x732DA`, `0x73314`).
  It reaches **2 and never changes** across the whole run. **It is a lifetime total, not per-frame.** v1's
  "2 dropped/frame budget overflow" is **false**.

## 5b. Identified dropped pieces [C2]

The **only two** drops in the entire session (both at **F=28**, cold start, PC `0x73314` = tile-DMA queue
full):

```
DROP F=28 rec=44 band=HUD_status(9-45) code=0x49 pal=0 x=264 y=0
DROP F=28 rec=45 band=HUD_status(9-45) code=0x47 pal=0 x=280 y=0
```

**Ownership: two HUD-status glyph records (rec 44/45), palette 0** — not gameplay actors. **Cause:** the 12-
entry per-frame tile-DMA queue (`pc090oj_hooks.s:1394`) saturated on the first HUD-heavy frame before the
residency cache warmed; after F28, **zero drops** (the HUD tiles are resident). **Priority:** these are HUD
front-band records, but the drop is a **cold-start VRAM-residency** event, not a priority/overflow event. No
gameplay piece is ever dropped in this run. (SAT-80 drop-tail would, if ever triggered, take the **highest-
index enemy tail** — e.g. the last lizard's rec 225–227 at F700 in the arcade-slot view — i.e. the lowest-
priority pieces, never the player or HUD.)

## 6. Native piece geometry + packing study

**Geometry (arcade records → Genesis):** every arcade object record is a **16×16 4bpp sprite**
(`gfx_16x16x4_packed_msb`). The Genesis `native_emit_pass` already maps **one record → one 16×16 Genesis
sprite** (size word `0x0500`), tile = `SPRITE_TILE_BASE + cell*4` where `cell` comes from a **32-set × 4-way
code-keyed residency cache** (`pc090oj_hooks.s:1364–1404`). **Cache cells are assigned per code and are NOT
VRAM-contiguous across records.**

Representative composites (from `contract.txt`, per-piece X,Y,code,pal,flip):
- **Rastan** (rec120-131, pal3): vertical pairs share X and step Y by 16 with consecutive codes
  (`x144 y73 c158 / x144 y89 c159`), and horizontal pairs share Y and step X by 16 with consecutive codes
  (`x144 c141 / x160 c140` at y129). Both are **merge-eligible geometry** (16×32 vertical, 32×16 horizontal).
- **Lizard-man** (rec180-187, pal6): two X columns (`x483`,`x499`) each 4 rows Y `89/105/105/121` → two
  **16×64-eligible columns**.
- **Bat** (rec48-56): single 16×16 per actor — **not mergeable** (independent lifecycles/positions).

| Model | Rule | Rastan SAT | Lizard SAT | Bat swarm SAT | Correctness |
|---|---|---:|---:|---:|---|
| **A (1:1, DEFAULT)** | one Genesis 16×16 per arcade record | 9–13 | 8 | 9 | **Always correct** (matches current emit pass) |
| **B (merge)** | fuse vertically/horizontally-adjacent pieces with equal pal/flip/pri into 16×32/32×16/32×32 | ~5–7 | ~2–4 | 9 | Correct **only if** the merged pieces' Genesis tiles are VRAM-contiguous |

**Load (measured, Stage 1):** worst SAT entries observed ≈ **34 emitted** (max historic ≈50), vs the 80 cap →
ample headroom. Worst per-scanline ≈ **10–14** 16×16 sprites on the enemy row (multiple lizards at y≈105), vs
the Genesis **20/line (H40)** limit. A dense hurry-up swarm (9 bats + lizards on one band) can approach the
per-scanline limit; **Model B would roughly halve the enemy per-scanline count** (2-col lizard → one 32-wide
sprite).

**Recommendation: Model A first (correctness).** Model B is an **optional per-scanline optimisation** for
swarms, and is admissible **only** with a residency variant that allocates **contiguous** VDP tiles for a
merged piece-group with identical palette/flip/priority/lifecycle. Do not force merging where the residency
cache cannot guarantee contiguity — it would corrupt art. Total SAT count is not the constraint (Model A stays
well under 80); the only real motivation for B is per-scanline relief in swarms.

## 7. Corrected HUD ownership [C4]

The single Genesis Window plane can occupy **one** vertical band (top-anchored **or** bottom-anchored), never
both. Given that, and the census (score band = 5 records, status band = ~37 records):

- **P1 score + 1UP → small reserved direct-SAT producer (DECIDED).** Records 4–8 (≤9 slots) are a tiny fixed
  block; keeping them on the SAT is cheap, keeps exact arcade glyph fidelity, and leaves the Window free for
  the larger band. This also **removes the two cold-start HUD drops** (rec44/45 are in the status band; see
  below) only if the whole HUD leaves SAT — score alone does not, so score stays a small resident block.
- **Life bar + lives + ROUND + status → bottom Window band (DECIDED).** Records 9–45 (~37 records) are the
  larger, mostly-static bottom region — the idiomatic Window tenant. Moving them to a tilemap band frees ~37
  SAT records **and** removes their tile-DMA residency demand — which is exactly what the two F=28 drops were
  (HUD-status tiles). So the bottom-band-to-Window move is what **eliminates the two lifetime drops**.
- **Single-Window constraint honoured:** only the **bottom** band is on the Window; the top score/1UP is
  reserved SAT. No top+bottom double-Window is proposed. **Plane A carries no fixed HUD ownership.**

**Bottom-band-is-HUD verification (partial, this trace):** the bottom status records (rec 9–16, y≈232/248)
sit at **identical screen X across F430/F700/F1000** while the camera and player moved — i.e. they are a
**camera-fixed HUD region, not scrolling terrain sprites**. **Open verification for implementation:** confirm
the exact Window rows do not overlap required Plane A/B **terrain** at the screen bottom across all stages
(the sprites are fixed HUD, but the tiles beneath the chosen Window rows must be checked). Do **not** finalise
the band height until that Plane A/B check is done.

## 8. Final native model + retirement plan

```
arcade actor traversal + mapping decision         [ARCADE-OWNED, unchanged]
  → family-specific native piece expansion (reads a4 actor + a0 mapping; per piece x,y,tile,pal,flip,pri)
  → sat_append_piece(x, y, gtile, size, pal, flip, pri)   [SHARED primitive — NEVER an 8-byte record]
       · appends into the family's SAT band position (record-index order = priority)
       · visibility-false (inactive a4@0 / retired a4@3 / blank frame a4@11) => NOT CALLED (no park entry)
       · bounded to NATIVE_SAT_MAX; drop-tail (drops the back/high-index pieces)
  → link finalize (last link = 0)
  → existing arcade-owned VBlank SAT DMA (VRAM 0xF800)
```

| Structure | Retire after… | Note |
|---|---|---|
| `pc090oj_object_ram` mirror (256-rec) | all families converted | the removal target |
| record packing / block-copy `0x41F5E` | family converted | replaced by direct append |
| `native_emit_pass` mirror scan | last family converted | its ascending-scan **ordering logic is correct and is reused conceptually** by the append order |
| tile-DMA worklist + residency cache | **KEEP** | VRAM residency ≠ SAT; still needed (and is where the 2 cold drops live) |
| ctrl/sprite_ctrl shadows | **KEEP** | register/colbank state |

The append primitive **must never accept or decode an 8-byte PC090OJ record.**

## 9. Smallest first Cody slice (one complete gameplay family, independently testable)

**Convert the group-3 lizard-man family (rec 140–238, the backmost gameplay band).** It is (a) always present
in Stage 1 (immediately testable), (b) a real composite (8 pieces, exercises the piece loop + `d2`), (c) has
real retirement (`a4@3`→`0x3EFBE`, testable by killing a lizard), and (d) is the **tail band**, so its native
append lands **after** the emit pass's other records — preserving global priority with no interleaving.

Slice:
1. Add `sat_append_piece(x,y,gtile,size,pal,flip,pri)` — sequential append into the SAT staging, link=next,
   bounded to `NATIVE_SAT_MAX`, drop-tail; per-frame reset/finalize. (Reuse the emit pass's residency/DMA and
   bias logic; do **not** re-implement tile residency.)
2. Hook the group-3 dispatch/type-handler so its piece expander computes each piece's `x,y,tile,pal,flip` from
   `a4`/`a0` and calls `sat_append_piece` **instead of** writing `a1` object-RAM records; when the actor is
   inactive/retired/blank-frame, **append nothing** (no `0x0180`).
3. Make `native_emit_pass` **skip mirror records 140–238** (that band is now native-appended) and let it
   continue the cursor so the lizard entries follow in order.
4. **Do NOT** combine with the Window HUD in this slice (the lizard conversion is independently testable
   without it). **Do NOT** touch Plane A/B, collision, rope, reset.

Validate: lizards render with correct composite/position, **behind** the player (rec120 < rec140), and a
**killed lizard disappears** (visibility-false → no append) with no stale corpse. Follow-on slices: group-4
bats/effects (also delivers the Build 0234 retirement fix), the player block-copy family, then retire the
mirror; the bottom-band Window HUD is a **separate** slice.

## 10. STOP status

**STOP not triggered.** The five STOP conditions are resolved: (1) **no family needs PC090OJ packing state** —
the boundary is the piece expander (`x,y,tile,pal,flip` in registers); (2) **priority direction proven** from
MAME source (forward append, record 0 = front, drop-tail); (3) **visibility no longer depends on `0x0180`** —
it is `a4@0`/`a4@3`/`a4@11` upstream; (4) **dropped-piece ownership known** — 2 lifetime cold-start HUD-status
tile-DMA misses (rec44/45), not a gameplay overflow; (5) **the selected first family (group-3 lizards) is
independently testable** in the same ROM. HUD owners are decided with the single-Window constraint honoured.

---

# Part II — Native Genesis sprite architecture + first migration slice (finalized)

> This part supersedes §8's single-global-cursor sketch. Producer **execution order ≠ final priority order**,
> so a producer cannot always append to one global SAT cursor. The final architecture uses **semantic priority
> queues** concatenated front-to-back at finalization. HUD/Window redesign is **deferred** (§18) — score, 1UP,
> life bar, lives, ROUND and frontend all remain sprites for now.

## 11. Semantic priority classes (replace record-range ownership) [correction]

PC090OJ record ranges are **oracle evidence only** — they must **not** become runtime ownership. They map to
these named semantic classes (front → back), owned by the original arcade producers:

| # | Semantic class | Arcade producer ownership | Oracle band (evidence only) | Runtime state |
|---:|---|---|---:|---|
| 0 | **Fixed front HUD** | score/1UP `0x3B802`; status/life/ROUND `0x5A098` | rec 0–45 | native sprites (unchanged this task) |
| 1 | **Front effects / bats / items** | group-4 `A5+0x748` (`d2=1`) | rec 46–56 | compatibility (mirror) |
| 2 | **Player** | block-copy `0x41F5E` (`A5+0x11B2`) + player group-1 | rec 92–95 / 120–137 | compatibility (mirror) |
| 3 | **Middle objects** | group-2 `A5+0x5C8` | rec 96–119 | compatibility (mirror) |
| 4 | **Back enemies (lizards)** | group-3 `A5+0x2C8` (`d2=10`, 19 for slot 8) | rec 140–238 | **native queue (this slice)** |

Class order 0→4 is the **front-to-back priority order**. Records 239–255 carry **no producer** (verified: no
staging routine writes them; the arcade snapshot shows nothing drawable above rec 227), so class 4 is the true
**tail** — which is exactly why it is the safe first conversion.

## 12. Producer execution order vs final SAT order [the reason for queues]

The master build `0x41DAE` processes producers in the order **grp1(players)=57 → grp2=96 → grp3(lizards)=140
→ grp4(effects)=46**, but the **priority (record index)** order is **46 → 57 → 96 → 140**. Execution order is
**not** priority order (grp4 runs last but is frontmost; grp3 runs before grp4 but is backmost). A native
producer that appended to a single global cursor **in execution order** would mis-order priority. Therefore:

**Each semantic class enqueues into its own compact queue; the finalizer concatenates the queues in the fixed
front-to-back class order (§11), regardless of the order the producers ran.** For a class that is a strict
band tail (class 4), that concatenation degenerates to "append after everything else" — the only reason this
first slice is simple. General families require the class-queue mechanism.

## 13. Native queue format + ownership

`back_enemy_queue`: a compact array of **native Genesis SAT-oriented entries**, count `back_enemy_queue_count`.
Each entry holds only **target-shaped** fields:

```
entry { Y9 ; sizebits(16x16) ; attrword(pri|flipX|flipY|code) ; X9 }   ; palette-nibble parallel byte (colbank resolved at commit, as today)
```

The queue entry **must not** contain any of: an 8-byte PC090OJ record; a PC090OJ address; a PC090OJ record
number; an object-RAM cursor; a `0x0180`/blank sentinel. (An entry is only ever created for a **visible** piece,
so there is no sentinel to carry — see §16.) Ownership: the **native sprite subsystem** owns the queue and its
count; the arcade still owns actor traversal, lifecycle, animation, mapping selection, coordinates and
visibility. There is **no** Genesis actor loop, renderer scheduler or lifecycle manager.

## 14. Queue reset + concatenation boundaries (existing arcade-owned points)

- **Reset boundary:** the top of `genesistan_pc090oj_hook_target_41dae` (runtime `0x00072A98`), which the arcade
  master build `0x41DAE` calls once per frame — the existing **sprite-preparation** boundary. Set
  `back_enemy_queue_count = 0` there, **before** `pc090oj_stage_block2c8` runs. **No new scheduler.**
- **Concatenation / finalization boundary:** the existing `pc090oj_native_emit_pass` (runtime `0x000731E4`),
  called from the same hook at `pc090oj_hooks.s:454`. It becomes the **hybrid finalizer** (§15).
- **VBlank boundary:** unchanged — `vdp_commit_sprites` (`0x0007349C`) DMAs `staged_sprite_sat` → VRAM `0xF800`
  in VBlank, after the mainline hook has built it. Order proven: mainline `0x41DAE`→hook builds SAT → VBlank
  commit DMAs it. (`vdp_prepare_sprites` `0x0007348E` is the inactive legacy candidate scan — counters 0.)

## 15. Hybrid lizard migration — exact frame order

```
[mainline, arcade 0x41DAE → hook_target_41dae 0x72A98]
  0. back_enemy_queue_count = 0                     ; RESET at the sprite-prep boundary
  1. pc090oj_stage_block2c8 (converted):            ; class 4 producer -> NATIVE QUEUE, no mirror writes
       for each of 9 group-3 actors (A5+0x2C8, +64):
         active(a4@0!=0) & a4@5!=0 & a4@3==0 & a4@1!=0 ?
            NO  -> enqueue NOTHING                    ; inactive/retired/blank => invisible (§16)
            YES -> expand pieces (arcade-owned engine 0x3D254 into a transient 8-byte scratch),
                   for each nonzero piece: translate (Y-8 KF067, X, code, pal/flip) -> native entry,
                   append to back_enemy_queue          ; NEVER writes pc090oj_object_ram 140..238
  2. .Lpc090oj_stage_record46_validated              ; class 1 (compat) -> mirror, UNCHANGED
  3. pc090oj_native_emit_pass (hybrid finalizer):
       a. ascending scan records 0..255 but SKIP 140..238 (class 4 owns the queue) -> emit compat SAT
          slots for classes 0,1,2,3 in record order (residency+DMA as today); DO NOT terminate the chain yet
       b. walk back_enemy_queue front-to-back -> for each entry resolve residency (same helper) and emit the
          next SAT slot, continuing the link chain                    ; class 4 lands AFTER classes 0..3
       c. terminate: last emitted slot link = 0; store emitted_count / sat_dirty
[VBlank] vdp_commit_sprites 0x7349C : DMA staged_sprite_sat -> VRAM 0xF800   ; UNCHANGED
```

Because class 4 is the tail, step 3b simply continues the cursor after 3a — global priority is preserved with
no interleave. (The general class-queue finalizer would instead concatenate all class queues in §11 order.)

## 16. Duplicate-output prevention + visibility

- **Producer side:** the converted `stage_block2c8` writes **zero** `pc090oj_object_ram` records in 140–238
  (it enqueues instead). Its inactive/retired/blank branches (`.Lb2c8_blank`/`.Lb2c8_skip`, which today write
  `Y=0x180` / skip) enqueue **nothing** → no sprite (the correct visibility-false contract; also removes any
  stale-corpse possibility for lizards).
- **Finalizer side:** the emit pass **excludes records 140–238** from its ascending scan (a single range
  guard, symmetric with the existing HUD `#46`/`#9` guards at `pc090oj_hooks.s:1302/1309`).
- **∴ every lizard piece is emitted exactly once** (through the queue) and **no** record in 140–238 is emitted
  by both paths. There is no window in which both fire (both run inside the same single hook invocation, in the
  fixed order of §15).

## 17. SAT link construction + tile-residency interface

- **One continuous link chain:** the emit pass already writes `link = cursor+1` per entry (`pc090oj_hooks.s:
  1444–1448`) and patches the final link to 0 (`1503–1506`). The hybrid change: step 3a must **not** write the
  terminator; step 3b continues emitting at the same cursor `d5` (links stay contiguous); step 3c writes the
  terminator on the **last** entry actually emitted (queue tail, or the last compat entry if the queue is
  empty). The `NATIVE_SAT_MAX=80` cap (`1489`) applies across **both** phases (shared cursor) → drop-tail still
  drops the lowest-priority (back-enemy) pieces first.
- **Tile residency is reused, not duplicated.** The queue append calls the **same** residency + slot-write path
  the emit pass uses (`.Lnep_res_ok`/`.Lnep_hit`, the 32-set×4-way code cache, `pc090oj_cell_used` reference
  protection, the 12-entry `pc090oj_tile_dma_worklist`). Residency for a lizard piece is resolved in step 3b,
  i.e. **after** the higher-priority classes 0–3 have referenced/protected their cells in 3a — preserving the
  exact eviction ordering of the current single ascending pass. **No second residency/DMA implementation.**

## 18. HUD scope (deferred — recorded note only)

- HUD/status (score, 1UP, life bar, lives, ROUND) and frontend **may remain entirely native sprites**.
- Window-plane or Plane A alternatives are **reconsidered only after** complete PC090OJ removal and real
  sprite-limit (SAT/per-scanline) measurements on the finished native system. **No HUD placement work in this
  task or the first Cody slice.** (This supersedes §7's ownership decision, which is now deferred, not adopted.)

## 19. Recurring cost comparison (measured basis, `lizcost.txt`)

Genesis Build 0249, Stage 1, per-frame writes to the lizard mirror band `0xFFAD1C–0xFFB033` (records 140–238):

| Window | active-lizard load (emitted total) | lizard-band **mirror word-writes/frame** |
|---|---|---:|
| F700–800 | heavy (emitted 40–50) | **~132–154** |
| F800–900 | medium (emitted 22–40) | **~92–132** |
| F1000–1100 | light (emitted 14) | **~54** |

**Current lizard path (recurring):** (1) arcade engine `0x3D254` expansion; (2) **~54–154 mirror word-writes/
frame** packing 8-byte records into `object_ram[140..238]`; (3) the KF-067 `Y-=8` read-modify-write pass over
each written record; (4) the emit pass's **99-record pre-scan** of the band (code pre-test each, even the
~67 blank rows) plus **~32 full 8-byte decodes** (mask `0x1FFF`/`0x180`/bitset) + residency + SAT write.

**Native queue path (recurring):** (1) the **same** arcade engine expansion (transitional — into a discarded
scratch, not the mirror); (2) translate + enqueue ~32 entries (`~128` queue word-writes/frame); (3) finalizer
walks **32** queue entries (not 99), residency + SAT write **unchanged**.

**Derived recurring delta (honest):** the engine expansion, residency lookups and SAT writes are **unchanged**,
so this is **not** a large speedup. What is eliminated per frame is the **mirror round-trip for the band** — the
~54–154 band writes **and** their re-read — the **separate KF-067 Y-fix pass** (~32 read-modify-writes), the
**99-record blank pre-scan**, and the **~32 8-byte decodes**. Order-of-magnitude ≈ **~150–300 fewer memory
ops/frame** at heavy load, with the dominant per-piece cost (engine + residency + SAT DMA) unchanged. **No
speed claim beyond this measured/derived basis.** The primary win is architectural (the mirror stops being the
authority for class 4), not throughput. Boot-only tile DMA and the inactive candidate scan are **excluded**
from this comparison (they are not recurring gameplay cost).

## 20. Complete PC090OJ retirement sequence (final-compatible)

1. **Slice 1 (this task):** class 4 (back enemies / lizards) → native queue; mirror band 140–238 excluded.
2. **Slice 2:** class 1 (front effects/**bats**/items, `stage_record46`) → its own front queue; also delivers the
   Build 0234 dead-bat retirement fix for free (visibility-false → no entry). Concatenate front-queue **before**
   the compat scan.
3. **Slice 3:** class 2 (player, `0x41F5E` block) and class 3 (middle, group-2) → queues.
4. **Slice 4:** class 0 (HUD score/status) → its own front-most queue (still sprites; Window/Plane A only
   reconsidered here per §18).
5. **Slice 5 (removal):** with every class native, delete `pc090oj_object_ram`, the `0xD00000` translation,
   record packing, `record_to_slot`/represented/waiting state, mirror scans/decoders, the chip clear/copy/decay
   helpers (`0x3B902/26/30`, `0x41F5E` block-copy, `0x5607C`, `0x56xxx`, `0x59F5E`, `0x3AD44`), the `Y=0x180`
   representation, and PC090OJ-only BSS/symbols/remap routes. The finalizer becomes pure class-queue
   concatenation. Keep `staged_sprite_sat`, residency and tile DMA, but **rename/own them under the native
   sprite subsystem** and feed them from native requirements only. Retain sprite-`ctrl`/colbank shadows **only**
   if independently proven semantic (colbank is display-latch state consumed at commit — proven; keep).

## 21. Exact first Cody task (compact)

**Convert class 4 (group-3 lizards) to the native back-enemy queue; leave every other class on the mirror.**

1. Add BSS `back_enemy_queue` (≤99 entries × the §13 fields) + `back_enemy_queue_count`.
2. In `genesistan_pc090oj_hook_target_41dae` (`0x72A98`), gameplay path: set `back_enemy_queue_count=0`
   **before** `pc090oj_stage_block2c8`.
3. Rewrite `pc090oj_stage_block2c8` (`0x72B6C`): keep the 9-actor walk and the exact active/blank/skip gates
   (`a4@0`,`a4@5`,`a4@3`,`a4@1`) and the arcade engine call `0x3D254` into a **transient scratch** (not the
   mirror). For each nonzero scratch piece, apply the KF-067 `Y-=8`, translate to a native entry (§13) and
   append to `back_enemy_queue`. **Inactive/retired/blank → append nothing.** **Write no `object_ram` 140–238.**
4. In `pc090oj_native_emit_pass` (`0x731E4`): add a range guard `if 140 ≤ record ≤ 238: skip`; after the
   ascending scan (do **not** terminate there), walk `back_enemy_queue` front-to-back and emit each via the
   **existing** `.Lnep_res_ok` residency/slot path, continuing the cursor + link chain; then terminate on the
   last emitted slot. Keep the `NATIVE_SAT_MAX` cap across both phases.
5. Reuse residency/DMA and `staged_sprite_sat`; **do not** add a second residency implementation.
6. **Do not** touch Plane A/B, collision, rope, reset, or any other sprite class.

Validate: lizards render with correct composite/position, **behind** the player; killed/retired lizards vanish
with no corpse; no lizard drawn twice; `emitted_count` unchanged in aggregate; one terminated SAT link chain.

## 22. STOP status (Part II)

**STOP not triggered.** (a) The lizard path needs **no PC090OJ record packing as runtime authority** — the
engine's transient scratch is arcade-owned piece expansion consumed at the boundary and discarded; the queue is
native. (b) Runtime ownership depends on **semantic class**, not record numbers. (c) Duplicate output is
**impossible** (§16: producer enqueues + finalizer excludes 140–238). (d) Priority is **preserved** across
native and compat families (class 4 is the tail; general case = §11/§12 concatenation). (e) Reset/finalization
ordering is **proven** at existing arcade-owned points (§14). (f) Tile residency is **reused**, not duplicated
(§17). (g) **No** Genesis actor traversal or scheduler is introduced. The slice is minimal and independently
testable.

---

# Part II-B — Shared piece emitter (SUPERSEDES the lizard-only slice, §15/§21)

> **Correction:** the migration unit is the **shared default piece emitter**, not one actor family. Lizards
> are a validation witness. The single Genesis convergence point already exists (below); converting it routes
> **every** default-expander sprite family (back enemies, effects/bats/items, middle objects) to native queues
> at once. Player and HUD are genuinely different **custom packers** and stay on compatibility.

## 23. Current state of the default expander (already half-native)

The arcade default expander (`0x3C950`, paths A `0x3C960` / B `0x3C9A6`) is **already redirected** on Genesis:
type dispatcher `0x3CB02` (arcade `0x3C902`+0x200) keeps the 9 specialized handlers, but its default
fall-through is `0x3CB50: jsr 0x717F4` (`genesistan_hook_text_writer_3c950`, `tilemap_hooks.s:2164`) with the
entire arcade default body `0x3CB58–0x3CC30` **NOP-padded**. That helper natively re-implements both loops and:
- **C-window (tilemap) case** (`a1 ∈ [0xC00000,0xC10000)`): fully native → `.Ltw_store_*` (done long ago).
- **sprite case** (`.L3c950_sprite_direct`, `tilemap_hooks.s:2364`): still **packs the four PC090OJ record
  words** to `a1` — this is the last chip tail on the shared path.

So the shared native emitter is a **small edit to one existing function**, not new infrastructure.

## 24. Complete default-expander caller inventory (arcade oracle, `callers.txt`/`callers2.txt`)

Every live producer reaching the shared default expander in Stage 1, and the custom packers that do **not**:

| Producer | Arcade→runtime | Wrapper→handler | Reaches default expander? | Semantic class | Path | Active/retire/blank |
|---|---|---|:--:|---|---|---|
| **Back enemies (lizards)** | `0x41E22`/`stage_block2c8 0x72B6C` | fam 0/2 → `0x3C902` type 0x00 → default | **YES** | back-enemy | A+B (facing) | `a4@0`/`a4@3`/`a4@5`/`a4@1` gates → skip = no piece |
| **Effects / bats / items** | `0x41E76`/`stage_record46 0x72A98` | fam 0 → type 0x00 → default | **YES** | front-effect | A+B | `a4@0`/`a4@36` gates; bat death → no piece |
| **Middle objects** | `0x41E48`(grp2) | fam 0 → type 0x00 → default | **YES** (arcade; verify Genesis staging) | middle | A+B | actor gates |
| Player (Rastan) | `0x544D0–0x547A0` → workram `a5+0x11B2` → block-copy `0x41F5E` (`0x41F7E` stores) | **dedicated composer**, never `0x3C902` | **NO** | player | — | custom |
| HUD score/1UP | `0x3B802` | dedicated | **NO** | HUD | — | custom |
| HUD status/life/ROUND | `0x5A098` | dedicated | **NO** | HUD | — | custom |
| Specialized types (0x10–0xC0) | handlers `0x3C4D2/550/586/636/6DC/75C/7A4/830` (own loops `0x3C516/606/742`) | `0x3C902` typed | **NO** (own loops) | varies | — | not reached in Stage 1 |

**Path A vs B is per-invocation (facing), not per-family** — both fire ~equally (17599 vs 17553) and both serve
all default-expander families. **Class is NOT the a1/record band** — it must be set by the producer (§26).

## 25. Shared pre-store boundary (exact)

In `.L3c950_sprite_direct` (both `.L3c950_sprite_primary_loop` path A and `.L3c950_sprite_alt_loop` path B),
per piece the four native fields are computed and then written as the record:

| Field | Register at store | Source |
|---|---|---|
| attr (flip+palette-route+vis) | `d0` → `move.w %d0,(%a1)+` | `0x40→d7flip`, `0x80→d0|=0x4000`, `0x3C950_apply_attr_gate` (`a4@39` b6) |
| Y | `d1` → `move.w %d1,(%a1)+` | `signext((a0)+) + a4@26` (`+a4@24` if type 0x70) |
| code (source artwork) | `d4` → `move.w %d4,(%a1)+` | `compute_next_attr`: `signext((a0)+)` ∓ (flip) `+ a4@30` |
| X | `d7` → `move.w %d7,(%a1)+` | path A `signext((a0)+)+a4@22`; path B `a4@22 − signext((a0)+) − 16` |

**The native cut is these four `(%a1)+` stores.** Replace them (both loops) with **one** call to the shared
emitter passing the four register values directly. The `0xFF` opcode sentinel (`.L3c950_read_opcode`, `d5=1`)
and the `.L3c950_sprite_sentinel_primary` blank (Y=0x180) path append **nothing** — visibility-false.

## 26. Semantic-class selection contract

The class is chosen by the **higher-level producer before it enters the engine**, never derived from `a1`/
`0xD00000`/record range. A global `native_sprite_class` (1 byte) is set by each staging caller immediately
before its `jsr 0x0003D254`, and consumed by the shared emitter:

```
stage_record46  (0x72A98 path): native_sprite_class = CLASS_FRONT_EFFECT   ; before each jsr 0x3D254
stage_block2c8  (0x72B6C):       native_sprite_class = CLASS_BACK_ENEMY
(middle staging, if live):       native_sprite_class = CLASS_MIDDLE
```

The class carries a compile-time **priority rank** and its finalizer splice position (§28) — a semantic
constant, not a runtime record number.

## 27. Shared native emitter contract

```
native_sprite_emit(X, Y, artwork_code, palette_route, flipH, flipV, size=16x16, class=native_sprite_class)
  → append one entry to queue[class]
```

Inputs are the §25 register values (`X=d7`, `Y=d1`, `artwork_code=d4`, `attr=d0` → `palette_route=d0&0xF`,
`flipH=d0 b14`, `flipV=d0 b15`). It **must not** receive or construct a PC090OJ record, an object-RAM address,
a record number, an `a1` cursor, or a Y=0x180 sentinel. `artwork_code` stays a **source** code — the finalizer
resolves it to a Genesis tile via the existing residency cache (never call it a final SAT tile index before
residency). One emitter serves **every** class assigned to it; there is **no** lizard-specific emitter or queue.

## 28. Queue + finalizer architecture (multi-class merge)

Per-class compact queues (`{X, Y, artwork_code, pal_route, flipH, flipV, size}` + count). Priority bands
(front→back) **interleave native and compat**, so the finalizer merges by rank at existing arcade-owned points:

```
[reset]  hook_target_41dae 0x72A98 top: clear all native queue counts (before staging)
[stage]  stage_record46 (class FRONT_EFFECT) + stage_block2c8 (class BACK_ENEMY) [+ middle] -> native_sprite_emit
[finalize] native_emit_pass 0x731E4 = ascending record scan with splice points:
    records 0..45  (HUD, compat mirror)   -> emit
    << splice queue[FRONT_EFFECT] >>       (band 46..56)      ; native
    records 57..95 (compat)               -> emit
    << splice queue[MIDDLE] >>             (band 96..119)     ; native (if live)
    records 120..139 (player, compat)     -> emit
    << splice queue[BACK_ENEMY] >>         (band 140..238)    ; native (tail)
    terminate the single link chain on the last emitted slot
[VBlank] vdp_commit_sprites 0x7349C : DMA staged_sprite_sat -> VRAM 0xF800   ; unchanged
```

One continuous link chain; `NATIVE_SAT_MAX=80` cap spans the whole merge (drop-tail = drop the backmost).
Residency resolved per emitted entry via the **existing** `.Lnep_res_ok`/cell-cache/12-entry DMA path, in
merge order (front classes protect cells first) — **no second residency implementation**.

## 29. Compatibility exclusions (duplicate-output prevention)

- Converted producers write **zero** mirror records for their bands (the shared emitter appends to queues; the
  `a1` stores are gone). `stage_record46`'s scratch+flush and `stage_block2c8`'s mirror writes are removed.
- `native_emit_pass` **excludes** the native bands from mirror reads at the splice points: **46–56**
  (FRONT_EFFECT), **96–119** (MIDDLE, if live), **140–238** (BACK_ENEMY). HUD (0–45) and player (120–139) stay
  compat.
- Every piece is emitted exactly once (queue for native bands, mirror for compat bands); both run in the one
  hook invocation in fixed order → no duplicate.

## 30. Remaining custom-packer inventory (defines the next slices)

Still packing PC090OJ records after the shared emitter lands, grouped by mechanism:

| Mechanism | Site(s) | Class | Next-slice note |
|---|---|---|---|
| Player composer + block copy | `0x544D0–0x547A0` → `0x41F5E`/`0x41F7E` | player | dedicated composer → its own native queue |
| HUD score digits | `0x3B802` | HUD | native HUD queue (still sprites) |
| HUD status / life / ROUND | `0x5A098` | HUD | native HUD queue |
| Specialized type handlers | `0x3C4D2/3C550/3C586/3C636/3C6DC/3C75C/3C7A4/3C830` (loops `0x3C516/3C606/3C742`) | boss/other | convert per handler when their content is exercised (not live in Stage 1) |
| Clear / copy / decay | `0x3AD44`, `0x56xxx`, `0x5607C`, `0x59F5E` | — | delete with the mirror at the end |

## 31. Revised recurring-work comparison

Converting the shared emitter removes the mirror pack for **all three** default-expander bands at once (not
just the lizard band). Measured lizard-band writes were **~54–154 word-writes/frame** (`lizcost.txt`); the
effect band (46–56) and middle band (96–119) add more. The shared emitter replaces every default-expander
piece's **4 `(%a1)+` record stores** with one queue append (fewer fields, no 8-byte layout), and removes
`stage_record46`'s scratch+flush and `stage_block2c8`'s KF-067 Y-fix pass and the emit-pass decode/blank-scan
for **three** bands. The arcade engine expansion (mapping walk, `a0`/`a4` reads) and residency+SAT DMA are
**unchanged**. No throughput claim beyond eliminating the record round-trip for the converted bands; the win is
architectural (the shared default emitter stops producing chip records at all).

## 32. Exact Cody task (shared emitter family — supersedes §21)

1. Add the native-queue framework: per-class queues `{X,Y,artwork_code,pal_route,flipH,flipV,size}` + counts
   for `FRONT_EFFECT`, `MIDDLE`, `BACK_ENEMY` (+ a `native_sprite_class` byte). Reset counts at the top of
   `genesistan_pc090oj_hook_target_41dae` (`0x72A98`).
2. Add `native_sprite_emit(X,Y,artwork_code,pal_route,flipH,flipV)` appending to `queue[native_sprite_class]`.
3. In `genesistan_hook_text_writer_3c950`'s **sprite branch** (`.L3c950_sprite_direct`, both
   `.L3c950_sprite_primary_loop` and `.L3c950_sprite_alt_loop`): replace the four `move.w …,(%a1)+` record
   stores with one `native_sprite_emit` call (fields per §25); the `0xFF` sentinel / blank path appends
   nothing. Leave the C-window (tilemap) branch untouched.
4. Set `native_sprite_class` in each converted staging caller before its `jsr 0x3D254`: `stage_record46` →
   FRONT_EFFECT, `stage_block2c8` → BACK_ENEMY (and the middle-object staging → MIDDLE if it is a live Genesis
   producer; if not, note it as arcade-only). Remove those callers' mirror writes / scratch+flush.
5. Convert `pc090oj_native_emit_pass` (`0x731E4`) into the §28 splice finalizer: exclude bands 46–56, 96–119,
   140–238 from mirror reads and splice each class queue at its band position; one terminated link chain;
   `NATIVE_SAT_MAX` across the merge; residency via the existing path.
6. Reuse the existing residency, tile DMA and `vdp_commit_sprites`. Leave player, HUD, specialized handlers and
   all other packers on the mirror. **Do not** create a lizard-specific queue/emitter. **Do not** touch Plane
   A/B, collision, rope, reset.

**Validate on one ROM:** Rastan (player, compat) + lizard composite + at least one more enemy + effect/item,
with animation, flips, correct front-to-back priority (effects in front of player, enemies behind), death/
retirement with no stale sprite, and no duplicated compatibility output.

## 33. STOP status (Part II-B)

**STOP not triggered.** The two common store tails (`.L3c950_sprite_primary_loop`/`_alt_loop`) can be replaced
without changing semantics for any live caller: **all** their live callers (back-enemy, effect, middle) want
the identical native treatment (16×16 pieces, class-tagged queue append), the specialized type handlers use
**separate** loops (unaffected), and the sentinel/blank path already means "no piece." No caller needs the
8-byte record kept. Player and HUD are separated as custom packers, not split per-actor. Class is producer-
selected (§26), priority preserved by the merge (§28), residency reused (§28), duplicates impossible (§29).
