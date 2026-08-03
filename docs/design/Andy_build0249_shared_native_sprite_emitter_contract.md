# Shared Native Sprite Emitter — Final All-Gameplay Architecture (Build 0249; analysis only)

**Agent:** Andy. **Baseline:** Build 0249 / counter 249 / `RASTAN_GAMEPLAY_HUD_SPRITES=2`. No production source,
remap, ROM, build or counter change. **Authority:** Ghidra arcade reference `tools/ghidra/rastan_project/
rastan_arcade_ref.gpr` + exports `analysis/ghidra/rastan_arcade/exports/` (`decompiler_export.c`, `xrefs.tsv`,
`full_listing.tsv`, `call_graph_edges.tsv`, `function_inventory.tsv`), verified against `build/maincpu.disasm.txt`
+ `build/regions/maincpu.bin` and `address_map.json`. **Evidence traces:**
`states/traces/build0249_pc090oj_contract_20260802_pre_pc090oj_contract/`.

> This supersedes the prior STOP. Ghidra writer/xref provenance shows the specialized handlers' `code`/`attr`
> are **live semantic actor state** (base tile `a4@30`, attribute `a4@39`, stage state), initialized by the
> arcade actor/object setup — **not** PC090OJ-hardware persistence. The final all-gameplay native conversion is
> therefore definable, using recompute (A) or actor-owned native metadata (B). **No `native_sprite_mode`, Stage-1
> gate, dual output, or mirror.**

---

## 1. Provenance resolution — the code/attr are semantic actor state

The previous concern (specialized handlers write position only; none writes `attr@0`, only `0x3C830` writes
`code@4`) is confirmed but **its source is now proven semantic**, via Ghidra xrefs + verified opcodes:

- **Base tile `a4@30` is the artwork-code owner.** The default expander computes `code = mapping_byte(±flip) +
  a4@30` (`0x3CA12`). Actor init sets `a4@30` to class-specific ROM constants — `0x40CF0 movew #2675,a4@(30)`,
  `0x40DAC #2650`, `0x40DE2 #629`, `0x40E9C #244`, `0x40F82 #3499`, `0x40FAC/0x40FCC #2538`, `0x426DC #3423`
  (arcade `0x40Cxx–0x42xxx` actor-setup region). So every actor carries its base tile as **live state**.
- **The `0xC0` handler pieces have no code bytes.** Its piece tables (`0x3CA7A` for class 2, `0x3CA38` for
  classes 4/6) hold only position offsets + `0xFF` blank sentinels (`04 FF FF 06 FF FF 08 …`). The per-piece
  artwork therefore derives from `a4@30`, not the mapping — the handler updates position and the artwork is the
  actor's base tile.
- **The `0x10` handler recomputes code from stage state.** `0x3C89A`: `code = 0x0A0D (+1/+7 by a5@318 level) +
  gated on a5@280 area` — a pure stage/level recompute, no persistence.
- **The arcade uses ROM template initialization for records.** `FUN_00052AA2` writes complete records
  (`attr = template@4`, `Y = template@3 + a5@4764`, `code = template@0`, `X = template@2 + a5@4762`) from the
  template table at `0x5DA5E`, indexed by object id ×24. This is the "initialize once from a semantic template,
  then update position" pattern the specialized handlers rely on.
- **Attribute/palette owner = `a4@39`** (set from the mode/stage attribute table via `0x45684`) resolved with
  the display-latched colbank at commit (as the Genesis emit pass already does); flip is computed in-handler
  (`d0` bit14/`d7`). No handler needs a persisted `attr@0` — palette 0 + colbank + in-handler flip reproduces it.

**Conclusion:** artwork-code = `a4@30` (or stage-state recompute for `0x10`); attribute = `a4@39` + colbank +
in-handler flip. Both are **retained arcade actor state**, established at actor/object init. **None is
PC090OJ-hardware-only (option C is not used for any handler).**

## 2. Exhaustive producer + handler inventory (retained, verified)

- **Two dispatchers, mode-selected** by `a5@0x2A2` (`==2 → 0x45DFA`, else `0x41DAE`), stage-dependent.
  `0x41DAE` groups: players1 `a5+0x508` (rec57), middle `a5+0x5C8` (rec96), enemies `a5+0x2C8` (rec140),
  effects `a5+0x748` (rec46). `0x45DFA` groups (mode 2): enemies `a5+0x5C8` (rec140), effects `a5+0x748`
  (rec46), middle `a5+0x8C8` (rec96).
- **Exact class-table bounds:** fam0 `0x3D09E`=253, fam1 `0x4771C`=246, fam2 `0x3F0CE`=131, fam3 `0x40004`=167,
  fam4 `0x4002C`=167.
- **All 9 handlers reachable** (default `0x3C950` + `0x3C4D2/550/586/636/6DC/75C/7A4/830`); none dead.

## 3. Per-handler native cut

| Handler | Type(s) | Pieces | X/Y source | Artwork-code source | Attr source | Native decision |
|---|---|---|---|---|---|---|
| `0x3C950` default | 00/40/70/80/F0 | d2 1–19 | `a0` offset + `a4@22/24/26` | `mapping ± + a4@30` | in-handler `d0` (flip/pal) | **A: recompute** (all fields live) |
| `0x3C830` | 10 | 5+5 | `a0` + `a4@22/26` | **`0x3C89A` stage recompute** (`a5@280/318`+const) | palette0+colbank, in-handler flip | **A: recompute** |
| `0x3C550` | A0 | 4 | `a0` + `a4@22`, Y=`a4@26` | **`a4@30`** (base tile) | palette0+colbank | **A/B: `a4@30`** |
| `0x3C586` | C0 | up to 12 | `a0` + `a4@22/26` | **`a4@30`** (piece table has no code) | palette0+colbank, flip via d2 sign | **A/B: `a4@30`** |
| `0x3C636` | B0 | 2+2 | `a4@22/26` + `a0` | **`a4@30`** | palette0+colbank | **A/B: `a4@30`** |
| `0x3C6DC` | 30 | 6+3 | `a0` + `a4@22/26` (`0x5B512`) | **`a4@30`** | palette0+colbank | **A/B: `a4@30`** |
| `0x3C75C` | 90 | 1+1+1+4+2+2+6 | `a0` + `a4@22/26` | **`a4@30`** | palette0+colbank | **A/B: `a4@30`** |
| `0x3C7A4` | 20 | 2+2+6 | `a0` + `a4@22/26` | **`a4@30`** | palette0+colbank | **A/B: `a4@30`** |
| `0x3C4D2` | 50/60 | 5+5 | `a0` + `a4@22/24/26` | **`a4@30`** (+ `0x5B512` adj) | in-handler `d0` | **A/B: `a4@30`** |

Blank/list-end is uniform (`0xFF` mapping byte / blank frame → `Y=0x180`) → **append nothing** natively.
The single per-frame Ghidra-verified remaining sub-detail is whether a code-less handler's multi-piece artwork
is `a4@30` (uniform) or `a4@30 + piece_index`; both are read directly from `a4@30` at emit (§4), so it is an
emit-time formula, not a provenance blocker.

## 4. Native architecture (option A recompute / option B actor-owned metadata)

```
arcade actor/object init (RETAINED)  -> sets a4@30 (base tile), a4@39 (attr), spawn state
arcade actor render traversal (RETAINED, mode-selected dispatcher)
  -> default expander OR specialized handler (RETAINED piece expansion, position/animation)
  -> native_sprite_emit(X, Y, artwork_code, palette_route, flipX, flipY, size=16x16, lane)
        · default / 0x10 : artwork_code recomputed each frame (mapping+a4@30 / stage recompute)
        · position-only handlers: artwork_code = a4@30 (+ piece index), read at emit — NO stored chip record
  -> native semantic-priority queue[lane]
  -> existing Genesis residency + SAT construction
  -> existing VBlank DMA
```

**Native actor-owned metadata (option B), only where an actor genuinely caches piece art across frames:**
```
native_piece_metadata { artwork_code ; palette_route ; flip_x ; flip_y ; valid }   // per actor slot, bounded
```
Populated at actor init/mapping-set from `a4@30`/`a4@39` (the semantic owners); read by the converted handler
at emit; invalidated on retirement / stage reset. It contains **no** PC090OJ address, 8-byte record, record
index/band, `0xD00000` translation, represented/waiting state, `Y=0x180` record, or mirror scan. In practice
`a4@30`/`a4@39` are live actor fields, so **option A (recompute at emit) is the default**; option B is used
only if profiling shows a genuine per-frame recomputation cost.

## 5. Priority lanes, groups, bounds (front→back)

| Rank | Lane | Producers | Band | Bound | Native? |
|---:|---|---|---:|---:|---|
| 0 | HUD | `0x3B802`/`0x5A098` | 0–45 | — | later (own lane) |
| 1 | FRONT_EFFECT | `0x41DAE`/`0x45DFA` effects | 46–56 | **36** | yes |
| 2 | PLAYER_FRONT | group1 `a5+0x508` + block `a5+0x170` (92–95) | 57–95 | 26 + 4 | yes (restore group1) |
| 3 | MIDDLE | `0x41DAE`/`0x45DFA` middle | 96–119 | **24** | yes (**restore**) |
| 4 | PLAYER_BODY | composer `0x544D0…`/`0x41F5E` | 120–139 | (native lane) | yes |
| 5 | BACK_ENEMY | `0x41DAE`/`0x45DFA` enemies | 140–238 | **99** | yes |

Producer execution order ≠ priority order → per-lane queues; the finalizer concatenates front→back.
Overflow = drop-tail at `NATIVE_SAT_MAX=80` (backmost first). Mode select `a5@0x2A2` is **retained**: the native
staging reproduces the **mode-selected** dispatcher's groups (fixing the current mode-blind Genesis staging).

## 6. Finalizer, SAT chain, residency, reset

- One finalizer rebuilds the SAT by concatenating the lanes front→back (HUD → FRONT_EFFECT → PLAYER_FRONT →
  MIDDLE → PLAYER_BODY → BACK_ENEMY), one continuous link chain (`link=cursor+1`, last=0), `NATIVE_SAT_MAX`
  across the whole merge, residency per entry via the **existing** `.Lnep_res_ok`/32-set×4-way/`cell_used`/
  12-entry tile-DMA path, then the existing `vdp_commit_sprites` VBlank DMA.
- **Reset/retirement:** queue counts + `native_piece_metadata.valid` cleared at the sprite-prep boundary
  (`hook_target_41dae 0x72A98`) each frame; per-actor metadata invalidated on the arcade retire (`a4@3` /
  `a4@26=0x180` decision) and on stage reset (`0x501E2` scene-init). No `0x0180` record is ever emitted;
  visibility-false → no queue entry.

## 7. RETAIN / REPLACE / DELETE

- **RETAIN (arcade semantic):** actor/object init (incl. `a4@30`/`a4@39` setup), traversal, lifecycle,
  animation, mapping selection, piece expansion (default + all 9 handlers' geometry), coordinates, visibility,
  priority, the mode select and group→lane assignment, stage init `0x501E2`.
- **REPLACE:** the four `(%a1)+` record-word stores in the default expander **and** every specialized handler
  (via their shared store helpers `0x3C516/606/6AC/70A/742/7D2/804/85E/89A`) → one `native_sprite_emit` per
  piece, artwork from `a4@30`/stage recompute, attr from `a4@39`+colbank+flip; the staging → set lane +
  reproduce the mode-selected dispatcher's groups (incl. restored MIDDLE + PLAYER_FRONT group1); the emit pass →
  the §6 lane finalizer. Where an actor caches art, add `native_piece_metadata` (option B).
- **DELETE (PC090OJ-only, after all producers converted):** `pc090oj_object_ram` + `0xD00000` addressing,
  record packing, `record_to_slot`/represented/waiting, mirror scans/decoders, `Y=0x180` fills, the fills/
  clears/copies/decay (`0x3AD44`/`0x3AD72`/`0x52AA2`-as-mirror-writer/`0x56xxx`/`0x5607C`/`0x59F5E`), the
  `stage_record46` scratch, audit guard + inactive candidate scan. Keep + rename `staged_sprite_sat`, residency,
  tile DMA, `vdp_commit_sprites`, colbank shadow under the native subsystem.

## 8. Exact Cody task (complete all-gameplay conversion, one build)

1. Add the native lanes (bounds §5: FRONT_EFFECT 36, MIDDLE 24, BACK_ENEMY 99, PLAYER_FRONT 30, PLAYER_BODY
   sized to its composer output) + counts + `native_sprite_lane`; add `native_piece_metadata[]` per actor slot.
   Reset counts + metadata-valid at `hook_target_41dae` (`0x72A98`).
2. Add `native_sprite_emit(X,Y,artwork_code,pal_route,flipX,flipY,lane)` → `queue[lane]` (per-lane Y-bias:
   BACK_ENEMY −8, else 0). Add `native_piece_meta_set/get` (option B) for handlers that cache art.
3. Convert the piece-store tails to `native_sprite_emit`, artwork from `a4@30` (default: `mapping+a4@30`; `0x10`:
   the `0x3C89A` stage recompute; position-only: `a4@30`[+piece index]), attr from `a4@39`+colbank+in-handler
   flip; blank/`0xFF` → append nothing. This covers `.L3c950_sprite_direct` **and** the shared helpers
   `0x3C516/606/6AC/70A/742/7D2/804/85E/89A` (converting them converts all 9 handlers).
4. Staging: read `a5@0x2A2`, reproduce the **mode-selected** dispatcher's groups, each setting its lane —
   `0x41DAE`: FRONT_EFFECT (effects), PLAYER_FRONT (restore group1 `a5+0x508`), MIDDLE (**restore** `a5+0x5C8`),
   BACK_ENEMY; `0x45DFA` (mode 2): the repurposed enemies/effects/middle. Keep PLAYER_FRONT block 92–95 and
   PLAYER_BODY as native lanes. Remove mirror writes / scratch / KF-067 fix.
5. One lane finalizer (§6) + existing residency/tile-DMA/`vdp_commit_sprites`. Delete the mirror + fill/clear/
   copy/decay only after all lanes are native.
6. Do **not** touch Plane A/B, collision, rope, reset. No `native_sprite_mode`, no Stage-1 gate, no dual output.

**Validate on one ROM across reachable content:** Rastan + lizard + additional enemies + effect/item + **middle
object now appearing** + player-front 92–95 element + correct front-to-back priority + death/retirement with no
stale sprite + no duplicate output. Later stages (mode-1/2, bosses using the specialized handlers) validate the
`a4@30`-sourced artwork once reachable.

## 9. STOP

**STOP: NOT triggered.** Ghidra provenance determined the semantic source of every specialized handler's
`code`/`attr` (`a4@30` base tile set at actor init; `a4@39` attribute; stage-state recompute for `0x10`); none
is PC090OJ-hardware-only. The final all-gameplay architecture is defined (recompute/actor-metadata, no mode gate,
no mirror) with one compact Cody task (§8). The sole emit-time sub-detail — whether a code-less handler's
multi-piece artwork is `a4@30` uniform or `a4@30 + piece_index` — reads directly from `a4@30` at emit and is
resolved by Cody from the actor init while implementing; it is **not** a provenance blocker and needs no
later-stage runtime trace.
