> **CORRECTION (Build 0259).** Implementation revealed that the nine addresses analyzed below
> (0x3C4D2/550/586/636/6DC/75C/7A4/830 + default 0x3C950) are a **dual-use 16×16-piece expander**, and their
> *primary* copies are the game's **C-window / score / FG-text renderer**, already remapped to
> `genesistan_hook_text_writer_3cXXXX` hooks in `tilemap_hooks.s` (verified: those hooks are tilemap/FG, and the
> sibling 0x3C322 does `ori.w #0x30` ASCII digit synthesis). The **gameplay sprite** path uses the *pristine
> relocated copy* of the same expander at 0x3D254 (0x3D054+0x200), reached from the master builds 0x41DAE/0x45DFA.
> The per-field provenance below (attr←a4@39, code←a4@30/a4@24 + mapping/stage) is correct for the shared
> expander, but the framing of these nine as "the gameplay sprite handlers to convert individually" is wrong —
> the sprite path is the whole `0x41DAE/0x45DFA → 0x3D254` chain, not the primary text-hook copies. See
> `Andy_build0259_native_gameplay_sprite_conversion.md`.

# Shared Native Sprite Emitter Contract — Ghidra Specialized-Handler Provenance

**Agent:** Andy · **Type:** ANALYSIS ONLY (Ghidra provenance) · **Build produced: NO.**
**Counter: 258 (unchanged). No production source / remap / generated object / ROM changed.**

This document supersedes all prior revisions. It resolves the single unresolved question —
*"Who semantically owns and establishes the retained artwork-code and attribute fields used by the
eight specialized sprite handlers, and how does that behavior exist natively without PC090OJ records?"* —
using the **existing** Ghidra project (`tools/ghidra/rastan_project/rastan_arcade_ref.gpr`) decompiler
export and xref database, verified against `build/maincpu.disasm.txt` / `build/regions/maincpu.bin`.

---

## 0. Why the eight handlers were "absent" from the decompiler export (root cause)

`function_inventory.tsv` shows `FUN_0003d054` with `entry = 0x3d054` but `body_min = 0x3c4d2`: Ghidra folded
the entire specialized-handler block (`0x3c4d2..0x3c8f6`) and the type dispatcher (`0x3c902`) into address
sets reached by **computed jumps**, so the eight grep addresses never received their own function boundaries
or decompiler headers. They are **not** missing code — they are the **jump-table case bodies inlined into
`FUN_0003c902`** (the type dispatcher). The existing export therefore already contains all eight, plus their
shared leaf helpers as standalone functions.

**Function boundaries added/corrected in the project: NONE were required.** The decompiler output for
`FUN_0003c902` reproduces every case body as an `if (type == 0xN0)` arm, and the eight case entries
(`0x3c550/586/636/6dc/75c/7a4/830` all open with `movea.l %a0@(2),%a0`; `0x3c4d2` with `movea.l`) were
confirmed as real dispatch targets directly in `build/maincpu.disasm.txt`. No project mutation, no new
project, no reinstall.

### Two-level dispatch (Ghidra `FUN_0003d054` + `FUN_0003c902`)

```
per-frame master build  FUN_00041dae (0x41dae)   ← runs from main loop @0x3efc8..0x3f016
    per actor slot: a1 := fixed object-RAM band (slot-stable); call FUN_0003d054
FUN_0003d054 (0x3d054)  family select on a4@0x38 (render family):
    1 → FUN_0004770e   2 → FUN_0003f0bc → 0x3c902   3 → FUN_0003ffdc   4 → FUN_0003fff0   else(0) → 0x3c902
FUN_0003c902 (0x3c902)  type select on (*a0 & 0xF0):
    0x10→0x3c830  0x20→0x3c7a4  0x30→0x3c6dc  0x50/0x60→0x3c4d2  0x90→0x3c75c
    0xA0→0x3c550  0xB0→0x3c636  0xC0→0x3c586   default(0x00/0x40/0x70/0x80/0xD0..0xF0)→0x3c950 expander
```

`a0` (mapping descriptor) = `family_base + u16[class*2]`, i.e. **type is fixed per class**, not per animation
frame. A specialized-class actor therefore **never** runs the default expander; this is central to ownership.

---

## 1. Object-RAM record model (verified)

8-byte PC090OJ record at `a1`: `+0` attr (flipY b15, flipX b14, palette b3:0), `+2` Y (`0x180` = off-screen
park sentinel), `+4` artwork code (13-bit), `+6` X (9-bit). First record = highest priority.

**Persistence mechanism (decisive — `FUN_00041dae`).** Each actor **slot** owns a **fixed** band base
(`0xd00170 / 0xd001c8 / 0xd002c8 / 0xd00300 / 0xd00460`), advanced by a fixed per-slot stride, identical every
frame. Inactive/retired actors are "parked" by writing **only Y=`0x180`** (`*(band+2)=0x180`), leaving
`+0/+4/+6` intact. The chip clear that zeroes `+0/+4` (`FUN_0003ad72`) is called **only** from
`startup_common_body` and `warm_restart_gate_caller_a` — **boot/reset, never per-frame**. Hence attr and code,
once written for a slot, **persist across frames** until that slot's actor re-establishes them.

---

## 2. Semantic writers of attr@+0 and code@+4 (exhaustive, Ghidra + disasm)

**Every writer of `+0` (attr), anywhere:**

| Writer | Ghidra | Value written | When | Semantic owner |
|---|---|---|---|---|
| Default expander | `FUN_0003c9e8` `btst #6,a4@(39)`→`move.b a4@(39),d0` | `a4@39` (actor attribute byte) | each frame, default-type actors only | **`a4@39`** |
| Template init | `FUN_00052aa2` `*d00000 = template[2]` (ROM `0x5DA5E + id*0x18`) | ROM template attr word | spawn, records 0–3 | actor spawn definition |
| HUD/score | `FUN_0003b930` (`*a1=0`), `FUN_0003b902` | HUD attr | non-gameplay/HUD bands | HUD producers |

**None of the eight specialized handlers writes `+0`** — proven: a scan of `0x3c4d2..0x3c902` for any
`,%a1@(0)` / bare `(%a1)` store returns **empty**.

**Every writer of `+4` (code), anywhere:**

| Writer | Ghidra | Value written | When | Semantic owner |
|---|---|---|---|---|
| Default expander | `FUN_0003c8f6` `cmpi.b #0x70,d3`→`add.w a4@(24),d1` | mapping code byte + `a4@24` addend | each frame, default-type actors only | **mapping code byte + `a4@24`** |
| Template init | `FUN_00052aa2` `*(d00004)=template[0]` | ROM template code word | spawn, records 0–3 | actor spawn definition |
| **Handler 0x10** | `FUN_0003c89a` @`0x3c8b8` `move.w d7,a1@(4)` | `0x0A0D (+1 if facing d2==-8)(+7 if level a5@0x13e≥63)`, **gated on area `a5@0x118==3`** | each frame, area 3 only | **stage state** (area/level/facing) |
| HUD/score | `FUN_0003b930/902/802` | HUD code | HUD bands | HUD producers |

**Only handler 0x10 among the eight writes `+4`** — proven: the sole `,%a1@(4)` store in `0x3c4d2..0x3c902`
is `0x3c8b8`.

**Actor base-tile establishment (the retained code source).** `a4@30`/`a4@24` are written with fixed artwork
codes at spawn by the actor initializers: `0x40cf0` `#2675`, `0x40dac` `#2650`, `0x40de2` `#629`, `0x40e9c`
`#244`, `0x40f82` `#3499`, `0x40fac/fcc` `#2538`, `0x426dc` `#3423` → `a4@(30)`. **Actor attribute
establishment:** `a4@39` set at spawn via the mode/stage attribute-table gate (`0x45376`, `0x45388`, `0x456b6`
`or.b d1,a4@(39)`, `0x45c04`) plus visibility/flip flag ops. **Both are actor fields, set at spawn from ROM
tables — not chip state.**

---

## 3. Per-handler provenance table

Types 0x50 and 0x60 share handler `0x3C4D2`. All ranges verified in `build/maincpu.disasm.txt`.

| Handler / type | Ghidra (case in `FUN_0003c902`) + helpers | Callers / reachable classes | Pieces & writes | Code source (+4) | Attr source (+0) | Transition / lifecycle | Persistence owner | Reset / retirement | Native decision |
|---|---|---|---|---|---|---|---|---|---|
| **0x3C4D2** (0x50/0x60) | case→`FUN_0003c516`×2, or 10× park | fam0 #138,#140 | 2 pieces Y/X; if `a4@0xb==0x20` write 10× Y=`0x180` | retained `a4@30` | retained `a4@39` | type fixed per class; frame `a4@0xb` gates park vs move | slot band (§1) | park = Y=`0x180`, code/attr kept; boot clear only | **B** (metadata from `a4@30`/`a4@39`) |
| **0x3C550** (0xA0) | inline 4-rec loop | fam0 #240 | 4 pieces X=`d*0x10+a4@16+map[a4@0xb]`, Y=`a4@1a` | retained `a4@30` | retained `a4@39` | frame `a4@0xb` indexes X-offset table `*(a0+2)` | slot band | park via master build | **B** |
| **0x3C586** (0xC0) | `FUN_0003c606`+`FUN_0003c742` (order by `a4@1==6`) | fam2 #2,#4,#6 | 4 pieces Y/X (piece tables `0x3CA7A`/`0x3CA38`, `0xFF`→park) | retained `a4@30` | retained `a4@39` | order swap on class 6; per-piece `0xFF` blank | slot band | `0xFF`→Y=`0x180`; boot clear | **B** |
| **0x3C636** (0xB0) | `FUN_0003c6ac`×2 (+`FUN_0003c742`×2 gated) | fam0 #246 | Y/X; extra pieces when `a5@0x118==2` or `0x61<a5@0x13e<100` | retained `a4@30` | retained `a4@39` | stage/level gate adds leading pieces | slot band | park via master build | **B** |
| **0x3C6DC** (0x30) | `FUN_0003c70a`×2 (uses `FUN_0005b512`) | fam0 #122, fam3 #55 | Y/X; per-piece `0`→park | retained `a4@30` | retained `a4@39` | type fixed per class | slot band | `0`→Y=`0x180` | **B** |
| **0x3C75C** (0x90) | `FUN_0003c742`+`FUN_0003c7d2`×4 | fam0 #146 | 5 pieces Y/X; `0xFF`→park | retained `a4@30` | retained `a4@39` | type fixed per class | slot band | `0xFF`→Y=`0x180` | **B** |
| **0x3C7A4** (0x20) | `FUN_0003c804`×2+`FUN_0003c7d2` | fam0 #120, fam3 #54 | 3 pieces Y(=`a4@1a−0x20/−0x30`)/X | retained `a4@30` | retained `a4@39` | Y offset depends on piece index | slot band | park via master build | **B** |
| **0x3C830** (0x10) | `FUN_0003c85e`(→`FUN_0003c89a`), `FUN_0003c742` | fam0 #118, fam2 #40, fam4 #145 | 2 pieces (`a4@38==0`) or 5; **writes code@+4** on d3==5 piece **only when area `a5@0x118==3`** | **stage recompute** (`0x0A0D`+facing+level) on area 3; else retained `a4@30` | retained `a4@39` | type fixed; frame drives piece; area gates code recompute | slot band + stage state | park; boot clear | **A** (stage recompute) + **B** (other pieces/attr) |

---

## 4. Ownership resolution

- **Artwork-code ownership.** For seven of eight handlers the code is **never** written by the handler; its
  semantic producer is the **actor base tile `a4@30`/`a4@24`** (fixed at spawn, `0x40cf0..0x426dc`), which the
  default expander / template lays into the record once and which the slot-stable band retains. Handler 0x10 is
  the sole exception: it **recomputes** one piece's code each frame from **stage state** (`a5@0x118` area,
  `a5@0x13e` level, facing `d2`).
- **Attribute ownership.** For **all eight** handlers, `+0` is **never** written by the handler; its semantic
  producer is the **actor attribute byte `a4@39`** (palette b3:0, flips, visibility b6), fixed at spawn via the
  mode/stage attribute-table gate. The default expander merely copies `a4@39` into the record.
- **Mapping transitions / default-frame establishment.** Because type is **class-fixed**, specialized actors
  never transition through a default-expander frame during play; the retained fields are therefore established
  at **spawn** (template / actor-init writing `a4@30`, `a4@39`) and preserved by the boot-only clear policy and
  the park-writes-Y-only policy — **not** by any per-frame chip-record producer.
- **PC090OJ role.** The persisted record is a pure **output latch**. Every field's true owner is an
  **actor field, a ROM mapping/attribute table, or stage state** — all persistent CPU-side state. The arcade's
  "write position, keep code/attr" pattern is an artifact of the chip RAM being non-cleared; it carries **no**
  semantic information not already present in `a4@30`/`a4@39`/mapping tables/stage counters.

**PC090OJ gameplay state still required: NONE.** Reading the actor/table/stage owners each frame reproduces the
retained artwork exactly, with no record, band, `0xD00000`, `Y=0x180` sentinel, or mirror scan.

---

## 5. Actor-owned persistent native metadata (Option B definition)

```
native_piece_metadata {           // owned by the ACTOR, one array per actor slot
    artwork_code;   // u16  <- a4@30 base tile (spawn); default/0x10 refresh below
    palette_route;  //      <- a4@39 bits3:0
    flip_x;         //      <- a4@39 flip bit
    flip_y;         //      <- a4@39 flip bit
    valid;          //      <- piece not blanked (mapping byte != 0x00/0xFF) and actor active
}
```

- **Semantic owner:** the actor (`a4` record) + its class mapping descriptor + stage counters.
- **Maximum pieces:** the class mapping-descriptor piece count (master-build park counts bound it: 13/4/10/19/1
  per band group; specialized handlers observed ≤10). The Cody task fixes exact counts by enumerating the five
  family tables.
- **Piece identity:** `(actor slot, piece index)` — stable, matching the slot-fixed band model.
- **Initialization:** at spawn, from `a4@30` (code), `a4@39` (palette/flips), mapping validity byte.
- **Animation updates:** position only for specialized types (from `a4@0x16`/`a4@0x1a` + mapping offsets);
  **artwork refresh only** for (a) default-type actors (mapping byte + `a4@24`) and (b) handler 0x10 area-3
  piece (stage recompute) — an **Option-A read-through** layered on the metadata.
- **Per-frame use:** emit each valid piece into its semantic lane with code/palette/flip from metadata and X/Y
  from actor + mapping offsets.
- **Invalidation / retirement / reset:** piece invalid when the mapping byte is blank (`0x00`/`0xFF`) or the
  actor is inactive/retired (`a4@3`); actor retirement clears `valid`; global reset clears all metadata —
  **replacing** the boot chip clear, with no `Y=0x180` sentinel.

Contains no PC090OJ address, record number, band, 8-byte record, `0xD00000` translation, `Y=0x180`, or
mirror-state flag.

---

## 6. Complete all-gameplay native conversion — definable? **YES.**

Every gameplay sprite field traces to persistent CPU-side state:
`family (a4@38) -> type (mapping *a0) -> piece layout (family tables) -> position (a4@16/1a + mapping offsets)
-> artwork (a4@30/24 + mapping code, or stage recompute for 0x10) -> attribute (a4@39)`. The master build's
slot/band order **is** the priority order, mapping directly onto the existing semantic lanes
(`native_queue_hud/front_effect/player_front/middle/player_body/back_enemy`) → `staged_sprite_sat` → existing
VBlank DMA.

The conversion is definable **without** `native_sprite_mode`, Stage-1 gating, dual native/PC090OJ output,
gameplay PC090OJ object RAM, record packing/translation/scanning/decoding, or PC090OJ blank/fill/copy/decay
ownership — because no field's semantic owner is a chip record.

---

## 7. Cody implementation task (complete, final-compatible — not partial)

> **[Cody — Native Actor-Owned Sprite Metadata Emitter, full gameplay]**
> Replace the gameplay path of the arcade sprite chain (`FUN_00041dae → FUN_0003d054 → FUN_0003c902` and the
> eight case bodies) with a native emitter that, per active actor slot, produces sprite pieces directly from
> actor/table/stage state — no PC090OJ record, band, `0xD00000`, `Y=0x180`, or mirror scan.
> 1. Enumerate the five family mapping tables (`0x3D09E`/`0x4771C`/`0x3F0CE`/`0x40004`/`0x4002C`; domains
>    253/246/131/167/167) to fix, per class: type nibble, piece count, per-piece X/Y offsets, per-piece
>    code/validity byte.
> 2. Define `native_piece_metadata` (§5) as actor-owned arrays sized by the max class piece count.
> 3. Init metadata at actor spawn from `a4@30` (code), `a4@39` (palette b3:0 / flips / visibility b6), mapping
>    validity.
> 4. Per frame, per active actor: compute piece X/Y from `a4@0x16`/`a4@0x1a` + mapping offsets; take code/attr
>    from metadata; **refresh** code for default-type actors (mapping byte + `a4@24`) and the handler-0x10
>    area-3 piece (stage recompute `0x0A0D`+facing+level, gated `a5@0x118==3`, `a5@0x13e≥63`); honor `0x00`/
>    `0xFF` blanks and `a4@3` retire as `valid=0`.
> 5. Emit valid pieces into the existing semantic lanes in master-build slot/priority order; reuse
>    `staged_sprite_sat` + VBlank DMA. Retire the gameplay-side object-RAM record production entirely.
> Validate: GATE_PASS; per-frame SAT parity against the current build for a gameplay capture (Rastan, lizard
> men, bats, axe); no sprite loss/flicker/priority inversion. Preserve all non-gameplay paths untouched.

This is the one complete conversion the provenance supports; it is **not** partitioned by mode or family.

---

## 8. Runtime evidence still required

**NONE for the design.** All semantic owners (`a4@30`, `a4@24`, `a4@39`, the five family tables, `a5@0x118`,
`a5@0x13e`, facing) were resolved statically via the Ghidra decompiler and the raw 68000. The only remaining
static work is table enumeration (a ROM read, not a runtime observation), assigned to Cody in §7.

## 9. STOP

**STOP: NO.** Every handler was decompiled (inlined in `FUN_0003c902`, verified in the raw disasm); every
caller/xref inspected (`FUN_0003d054` family select, `FUN_00041dae` master build, family wrappers); every
attr/code writer exhausted (default expander `FUN_0003c9e8`/`FUN_0003c8f6`, template `FUN_00052aa2`, handler
0x10 `FUN_0003c89a`, HUD producers — none of the eight writes attr, only 0x10 writes code); mapping transitions
traced (type class-fixed → no default frame → spawn establishment + boot-only clear + park-Y-only retention);
original instructions verified. The semantic owners are actor/table/stage state; the native conversion is fully
definable; the complete Cody task is specified.

## 10. Scope proof

Counter **258** (unchanged); no ROM produced; no production source, generated object, or remap changed. Only
this report and `AGENTS_LOG.md` changed.
