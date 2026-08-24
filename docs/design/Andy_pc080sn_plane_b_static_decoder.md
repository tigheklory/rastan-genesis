# Andy/Cody - PC080SN Plane-B Static Decoder (arcade RE)

**Type:** bounded original-arcade observation followed by static decoder closure.  
**Baseline:** Build 0301; no ROM produced; Build 0302 not consumed.  
**Production inputs:** `build/regions/maincpu.bin`, `build/regions/pc080sn.bin`, and static
arcade semantics only. **Production trace dependencies: 0.**  
**Evidence trace:**
`states/traces/original_arcade_plane_b_progression_20260821_161624/` (proof only).

## Status

The bounded observation and static route correction are complete. The previous first-event cutoff,
Plane-B Y ownership, and descriptor layout claims are corrected below. The descriptor cursor is now
fully static and deterministic for physical Stage 1.

The **real per-epoch Plane-B residency model is not complete**. Static RE now closes the camera
machine, including initialization, dead zones, four-pixel displacement cap, selector gates, and
the conservative row sets that follow from those gates. That evidence-safe camera-machine model
already overflows the shared Plane-A/Plane-B VRAM budget in nine Stage-1 records. It is not,
however, an exact terrain-constrained reachability model: collision geometry determines which
requests can actually be produced in each record. No persistent sub-record camera-zone transition
exists at the camera gates. Consequently, neither a boundary-only failure nor a dynamic cache is
yet proven. The transitional 320-slot placeholder remains and no canonical epoch assets were
regenerated.

## 1. Bounded original-arcade observation

### Coverage (observation)

- Original arcade Rastan under MAME 0.276, 9,921 external frames, 278 semantic events.
- Attract gameplay ran first and is supplementary evidence. It covered route segments 1 through 6
  before death/reset.
- Tighe then coined up and manually played through the first cave section. This is the authoritative
  user-controlled sample and covered route segments 1 through 3 before exit.
- Neither sample reached the first trailing event byte at record 15. Event continuation is therefore
  a **static code/data proof**, not a claim about observed runtime coverage.

### Descriptor observations

At initial scene fill, the producer selected descriptor indices 0, 1, 2, 3 with sources:

| Descriptor | Source |
|---:|---:|
| 0 | `arcade_ROM/data 0x0000D11C` |
| 1 | `arcade_ROM/data 0x0000D91C` |
| 2 | `arcade_ROM/data 0x0000F11C` |
| 3 | `arcade_ROM/data 0x0000F11C` |

Runtime then entered segment 1 with descriptor cursor 4. Every completed horizontal 512-pixel
record advanced the cursor by exactly two entries:

| Segment transition | Cursor before -> after | Observed sources |
|---|---:|---|
| segment 1 | 4 -> 6 | `D11C`, `E11C` |
| segment 2 | 6 -> 8 | `D11C`, `D91C` |
| segment 3 | 8 -> 10 | `E11C`, `F11C` |
| segment 4 | 10 -> 12 | `E91C`, `E91C` |
| segment 5 | 12 -> 14 | `D11C`, `D91C` |
| segment 6 | 14 -> 16 | `D91C`, `D91C` |

This confirms the static half-rate parallax rule and the four-descriptor scene fill. The observed Y
values varied while selector `0` remained active (for example `0x0149`, `0x0105`, `0x015D`, and
`0x01E9`). Those values are evidence that Y is player/camera-driven, **not compiler inputs**.

## 2. Corrections to earlier conclusions

### Plane-B descriptor layout is row-major

`arcade_pc 0x00055C7A` reads:

```text
source + (column * 2) + (row * 0x20)
```

Each source is 16 columns x 64 rows x 2 bytes = `0x800` bytes, but its layout is **row-major**:

```text
word_address = source + row * 32 + column * 2
tile_code    = word & 0x3FFF
```

The earlier `column-major` wording was wrong.

### Plane-B Y is `a5+0x10EE`, not `a5+0x10B0`

`arcade_pc 0x00055AB4` publishes:

| Arcade work RAM | Hardware address | Layer meaning |
|---|---|---|
| `a5+0x10EE` | `HW_ADDRESS 0x00C20000` | Plane B Y |
| `a5+0x10EC` | `HW_ADDRESS 0x00C40000` | Plane B X |
| `a5+0x10B0` | `HW_ADDRESS 0x00C20002` | Plane A/FG Y |
| `a5+0x10AE` | `HW_ADDRESS 0x00C40002` | Plane A/FG X |

`arcade_pc 0x00055B28` and `arcade_pc 0x00055B32` copy `a5+0x10B0` into `a5+0x10EE` during
vertical camera updates. That copy explains why both values matched in the bounded capture; it does
not make `0x10B0` the Plane-B owner.

### The 12-byte structure is a pair of 6-byte descriptors

The producer consumes adjacent 6-byte records `{attr16, source32}`. Scene selection at
`arcade_pc 0x000503A8` computes:

```text
descriptor_cursor = 0x3951C + (tm0 * 12)
```

Thus each `tm0` selects a **pair-aligned start** (`descriptor_index = tm0 * 2`); it is not one
12-byte descriptor.

## 3. Correct physical Stage-1 progression

`arcade_pc 0x000452A8` multiplies the round selector by 23. Therefore one physical round owns 23
stage/checkpoint records. For Stage 1 the exact route is records 0 through 22:

```text
0..14 : selector 0
15    : selector 0, trailing event 4
16    : selector 0 (scene seed/fill)
17    : selector 1 (vertical)
18..20: selector 0
21    : selector 1, trailing event 6
22    : selector 0, trailing event 7 (scene seed/fill)
```

The former `segments 0..15 = Stage 1` scope is corrected. Record 15's event 4 is an **intra-round
transition**, not the end of physical Stage 1.

### Event-4 continuation mechanism (static proof)

1. Record 15 completes its 64-publication selector-0 cycle. The stream pointer advances onto the
   trailing event byte `4`; publication freezes there.
2. `arcade_pc 0x00052732` maps selectors 4/5/6 to player mode 7.
3. The outer controller tests that mode at `arcade_pc 0x0003A7D2`.
4. At `arcade_pc 0x0003A7DA`, it copies the already-advanced segment value 16 into `a5+0x1242`.
5. The controller re-enters scene initialization. `stage_table[16] = 16`, so the stream is reseeded
   at record 16 and `tm0_table[16] = 18` selects descriptor index 36.

This is the missing event-completion -> reseed path. It supersedes the earlier report that this call
chain was unresolved.

## 4. Exact Plane-B descriptor progression

The cursor law is now complete:

- scene initialization fills four descriptors (64 columns);
- each normal horizontal selector-0 record moves Plane A 512 pixels and Plane B 256 pixels, consuming
  two 16-column descriptors;
- selector 1/2 vertical records consume zero descriptors;
- an event-triggered scene re-entry seeds from `tm0 * 2` and fills four descriptors.

For Stage 1:

| Records | Action | Descriptor cursor |
|---|---|---:|
| 0 seed/fill | four descriptors | 0 -> 4 |
| 1..15 horizontal | two each | 4 -> 34 |
| event 4 / record 16 seed/fill | reseed at `18*2`, four | 36 -> 40 |
| 17 vertical | none | 40 -> 40 |
| 18..20 horizontal | two each | 40 -> 46 |
| 21 vertical / event 6 | none | 46 -> 46 |
| record 22 seed/fill | reseed at `26*2`, four | 52 -> 56 |

The attr-`0x0003` run starts at descriptor 56; physical Stage 1's final seed/fill stops at that
boundary. This explains why the 56-entry attr-`0x0002` run is longer than the pre-event horizontal
prefix without changing the proven two-descriptor consumption rate.

## 5. Selector-0 camera subsystem (static closure)

### Scene initialization and camera tuple

`arcade_pc 0x000504FA`, called by the scene initialization path at `arcade_pc 0x0005020A`,
indexes `arcade_ROM/data 0x00050850 + (a5+0x013E)*12`. The root is `0x50850`, not the
previously reported `0x508D0`. Each six-word record initializes:

| Word | Arcade work-RAM field | Meaning |
|---:|---:|---|
| 0 | `a5+0x10AE` and `a5+0x10EC` | Plane-A X and Plane-B X |
| 1 | `a5+0x10B0` and `a5+0x10EE` | Plane-A Y and Plane-B Y |
| 2 | `a5+0x10B8` | horizontal world/camera accumulator |
| 3 | `a5+0x10BA` | vertical world/camera accumulator |
| 4 | `a5+0x10BE` | player screen X |
| 5 | `a5+0x10C0` | player screen Y |

The decoded Stage-1 tuples are:

| Record | X A/B | Y A/B | world X | world Y | screen X | screen Y |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | `0000` | `0000` | `0000` | `0000` | `0000` | `0000` |
| 1 | `0000` | `0000` | `0000` | `0100` | `0020` | `0030` |
| 2 | `0160` | `0000` | `00A0` | `0100` | `0078` | `0080` |
| 3 | `0160` | `0000` | `00A0` | `0100` | `0078` | `0080` |
| 4 | `0160` | `0000` | `00A0` | `0100` | `0038` | `0080` |
| 5 | `0000` | `0000` | `0000` | `0100` | `0020` | `0030` |
| 6..8 | `0160` | `0000` | `00A0` | `0100` | `0078` | `0080` |
| 9 | `0000` | `0000` | `0000` | `0100` | `0020` | `0030` |
| 10..12 | `0160` | `0000` | `00A0` | `0100` | `0078` | `0080` |
| 13 | `0000` | `0000` | `0000` | `0100` | `0020` | `0030` |
| 14..16 | `0160` | `0000` | `00A0` | `0100` | `0078` | `0080` |
| 17 | `0000` | `0100` | `0000` | `0000` | `0020` | `0080` |
| 18..19 | `0000` | `0159` | `0000` | `0059` | `0020` | `00A0` |
| 20 | `0000` | `0100` | `0000` | `0000` | `0040` | `00C0` |
| 21 | `0000` | `0100` | `0000` | `0000` | `0060` | `0030` |
| 22 | `0000` | `0000` | `0000` | `0000` | `0030` | `0020` |

`arcade_pc 0x000504FA` initializes the tuple selected by `a5+0x013E`; the selector itself is
loaded from the Stage-1 scene table. Initial scene fill starts from record 0, then advances the
active segment to record 1 before observed gameplay camera motion. This reconciles the trace:
record 1 enters at Plane-A Y `0x0000` with vertical accumulator `0x0100`, then downward movement
decrements both modulo 512 and produces the later observed Y `0x0149`.

Every normal Stage-1 tuple in records 1..21 satisfies:

```text
(initial Plane-A Y - initial vertical accumulator) & 0x01FF = 0x0100
```

Accepted selector-0 motion preserves that relation. Records 0 and 22 contain zero tuples; they are
seed/terminal table states and are not evidence for the live record-1..21 relation.

### Player request and dead-zone rules

The player movement owner caps each pending displacement at four pixels before calling the camera
request path:

- `arcade_pc 0x00051830..0x00051844`: upward displacement -> `a5+0x10DE`, maximum 4;
- `arcade_pc 0x00051850..0x00051864`: downward displacement -> `a5+0x10DE`, maximum 4.

Collision probes at `arcade_pc 0x00053A6E` and `0x00053B34` can reduce that displacement one pixel
at a time. They cannot enlarge it. `arcade_pc 0x00053896..0x000538D6` uses player screen Y
`a5+0x10C0` with an upper follow line of 64 pixels. `arcade_pc 0x00053904..0x00053942` uses a
lower follow line of 112 pixels. Motion on the player side of those lines changes local screen Y;
the excess sets request bit 0/1 in `a5+0x10D0` and stores its magnitude in `a5+0x10DA`.
The local player-Y movement gates are 8 and 256; the same four-pixel displacement cap permits
one-step overshoot to `4..259` before the next request is blocked.

### Camera gates and invariants

`arcade_pc 0x00055696` accepts the upward request while signed `a5+0x10BA < 0x0100`. It adds the
same 1..4-pixel delta to `0x10BA` and `0x10B0`. If the accumulator is already at or above
`0x0100` and selector is not 1, it sets defer bit 5 and returns without moving the camera.

`arcade_pc 0x0005572E` accepts the downward request while signed `a5+0x10BA >= 8`. It subtracts
the same delta from `0x10BA` and `0x10B0`. Below 8, selector other than 2 sets defer bit 4 and
returns. Because the displacement cap is four, the selector-0 camera-machine accumulator domain is
`0x0004..0x0103` inclusive: 256 values. The initialized `0x0100` boundary is already within that
domain. During accepted selector-0 vertical motion:

```text
(a5+0x10B0 - a5+0x10BA) & 0x01FF = constant
```

`arcade_pc 0x00055AD6` copies accepted Plane-A Y to Plane-B Y through `0x55B28/0x55B32`.
Thus `a5+0x10EE` remains the Plane-B owner, while its accepted selector-0 values follow the same
modulo-512 relation.

The X subsystem is analogous. `arcade_pc 0x000557BA` uses a world-X gate at `0x00A0`,
`0x55854` blocks reverse motion below zero (and in state `a5+0x020C == 1`), and the four-pixel
cap permits overshoot to `-4..0x00A3`. For selector 0, the primary horizontal stream continues
through all 512 modulo-X positions; Plane B advances at half rate through `0x55B3C/0x55BB6`.

### No persistent camera-zone boundary

The gate crossings are not usable graphics-epoch transitions. `arcade_pc 0x000517E0` clears
`a5+0x10D0` each update; request and defer bits are then rebuilt for that frame. The player can move
back across the same gate. No persistent camera-zone ID, top/bottom table, or one-way sub-record
mode transition was found in the xrefs that write `0x10B0`, `0x10BA`, or `0x10EE`. The only
discrete persistent boundaries proven here remain map records and event/reseed transitions.

## 6. Authoritative native plane-pattern ownership

The 940-versus-960 discrepancy is resolved from live VDP ownership, not from the transitional cache
array size.

| Tile slots | VRAM bytes | Owner / rule |
|---:|---:|---|
| 0..63 | `0x0000..0x07FF` | Reserved plane/system band. Tile 0 is blank; the current fixed-tile upload begins at byte `0x0020` and remains inside this band. |
| 64..1023 | `0x0800..0x7FFF` | Final native shared Plane-A/Plane-B pattern band. |
| 1024..1535 | `0x8000..0xBFFF` | PC090OJ native sprite patterns (`SPRITE_TILE_BASE = 1024`). |
| n/a | `0xC000..0xDFFF` | Plane-B name table and following reserved VRAM. |
| n/a | `0xE000..0xF7FF` | Plane-A name table and following reserved VRAM. |
| n/a | `0xF800..0xFBFF` | SAT. |
| n/a | `0xFC00..0xFFFF` | horizontal-scroll table / reserved tail. |

`vdp_boot_setup` programs Plane B at `0xC000`, Plane A at `0xE000`, SAT at `0xF800`, and
HScroll at `0xFC00`. `pc090oj_hooks.s` adds tile 1024 to every native sprite pattern and documents
the sprite residency interval as 1024..1535. The normal fixed-tile uploader writes only 48 words
from byte `0x0020`. No source, symbol, preload owner, alignment rule, or sentinel claims plane tile
slots 1004..1023.

The earlier 1003 ceiling comes from `fg_tile_cache.s`: its transitional runtime cache arrays contain
1004 entries indexed 0..1003. Reserving 0..63 leaves 940 runtime-cache entries. It is an array-size
policy inherited from the old two-band cache design, not a YM7101 boundary. For the final offline
compiler the authoritative constants are now:

```text
safe_plane_slot_first = 64
safe_plane_slot_last  = 1023
safe_plane_slot_count = 960
```

`tools/translation/compile_pc080sn_genesis.py` names these constants explicitly. Its current
transitional Plane-A allocator still subtracts the unresolved 320-slot Plane-B placeholder, so this
ownership correction is byte-neutral for generated output. The Build-0301 runtime cache remains
unchanged and transitional; a future native runtime must consume the same 64..1023 contract when
the static model is complete.

## 7. Terrain/collision reachability result

### Exact coordinate transform

`arcade_pc 0x00053A2E` computes the collision-map address from a player probe `(D1,D2)`:

```text
ring_x_px = (-a5@0x10AE + D1) & 0x01FF
ring_y_px = (-a5@0x10B0 + D2) & 0x01FF
column    = (((ring_x_px >> 1) + 8) & 0x00FC) >> 2
row       = (ring_y_px & 0x01F8) >> 3
address   = arcade_WRAM 0x0010DE00 + row*0x80 + column*2
```

The collision surface is therefore a 64-column x 64-row ring of 8x8-pixel logical cells. `D1/D2`
are player-local screen probes derived from `a5+0x10BE/a5+0x10C0`, adjusted by the player half
sizes `a5+0x112E/a5+0x1130` and the pending displacement in `D6`. The map-local player position is
`(screen - Plane-A scroll) mod 512`; it is not the same value as either screen position or scroll.

For normal selector-0 records the proven camera invariant remains:

```text
Plane-A Y = (vertical accumulator + 0x0100) mod 512
Plane-B Y = Plane-A Y after an accepted vertical camera update
```

Thus, for a probe at screen Y `S`, its collision-ring Y is
`(S - vertical_accumulator - 0x0100) mod 512`. The record number and scene/reseed tuple supply the
non-modulo semantic interval; modulo coordinates alone do not identify a physically continuous
route.

### Collision semantics decoded

The static producer decoder agrees with the existing PC080SN collision contract: Plane-A
metatiles publish both graphics and collision words into the 64x64 ring. The player probe families
at `arcade_pc 0x00053A6E` and `0x00053B34` mask each word to code `0x00..0x7F` and distinguish:

| Code | Proven effect in player collision code |
|---:|---|
| `0x01` | ordinary blocking/contact bits; invokes the common surface correction |
| `0x02` | side/special contact bit `0x20`; saves the collision-cell pointer in `a5+0x111C` |
| `0x03` | contact plus surface variant `a5+0x13D4 = 1` |
| `0x04` | contact plus status bit `0x40` |
| `0x06` | status bit `0x0200` |
| `0x07` | contact plus status bit `0x0100` |
| `0x08` | lethal: sets status bit `0x0200` and player mode `a5+0x10E8 = 8` |
| `0x7E` | special status bit `0x0080` |

These effects are exact; names such as slope, rope, ladder, or platform are not assigned where the
code/data proof does not uniquely establish them.

The initial Stage-1 collision surfaces decode from the same Plane-A source blocks used by the
graphics compiler. The table below is a static inventory, **not** a legal-player envelope. `Rows`
lists rows containing at least one nonzero collision word; `bit7` counts source cells that can
trigger the mutation path; `codes` counts nonzero low-7-bit classifications.

| Rec | Rows | bit7 | Nonzero collision codes |
|---:|---|---:|---|
| 0 | 0..63 | 0 | `01:1696` |
| 1 | 40..63 | 0 | `01:1072` |
| 2 | 28..63 | 0 | `01:786, 02:25` |
| 3 | 36..63 | 0 | `01:1344, 03:16, 06:312, 08:108` |
| 4 | 8..63 | 0 | `01:2241, 02:23` |
| 5 | 16..63 | 0 | `01:1344` |
| 6 | 28..63 | 0 | `01:1393, 02:23` |
| 7 | 40..63 | 0 | `01:1104` |
| 8 | 40..63 | 0 | `01:880` |
| 9 | 40..63 | 0 | `01:896` |
| 10 | 8..63 | 0 | `01:1345, 02:23, 03:10, 06:202, 08:40` |
| 11 | 8..63 | 0 | `01:1010, 02:23, 03:26, 06:1166, 08:200` |
| 12 | 32..63 | 0 | `01:1120` |
| 13 | 28..63 | 0 | `01:1312` |
| 14 | 24..63 | 0 | `01:1074, 02:27` |
| 15 | 32..63 | 0 | `01:1336, 7E:40` |
| 16 | 0..63 | 48 | `01:1488, 02:68` |
| 17 | 0..63 | 32 | `01:1408, 02:84` |
| 18 | 0..63 | 0 | `01:896, 07:1728` |
| 19 | 0..63 | 0 | `01:2609, 02:96` |
| 20 | 0..63 | 32 | `01:1556, 02:52, 06:96, 08:24` |
| 21 | 0..63 | 48 | `01:1456, 02:80, 7E:32` |
| 22 | 0..63 | 0 | `01:720, 03:40` |

### Why the initial collision map is not an exact terrain graph

The collision ring is mutable gameplay state. `arcade_pc 0x0005A29C..0x0005A354`, called from
`player_main_update_51090`, runs when `a5+0x1330 == 1` and selector `a5+0x10A8 == 1`. It scans 16
cells, and a source word with bit 7 invokes `collision_map_surface_mark_5a2ee`, which:

- replaces four current-row collision words with code `1`;
- rewrites four cells five rows earlier with high byte `0x34` while preserving their low byte;
- rewrites the corresponding PC080SN graphics cells to word `0x25C7`.

The collision lookup is also called by actor routines `0x041064`, `0x041180`, `0x042E38`,
`0x045D10`, and `0x04736A`. Player legality therefore depends on dynamic actor/platform contact in
addition to the ring. The player update contains mode, velocity, jump/fall, contact flags, saved
collision pointers, input, lethal mode changes, and record/event progression. A node keyed only by
`(record, collision row, collision column)` merges states with different legal successors.

An exact static reachability state would minimally require:

```text
(record/event/reseed state,
 mutable 64x64 collision ring,
 player X/Y and screen X/Y,
 camera X/Y accumulators,
 player mode and velocities,
 contact/status flags and saved collision pointer,
 input state,
 participating actor/platform states)
```

Exploring that transition system is a frame/gameplay emulator under another name, which this task
explicitly forbids. No smaller explicit ROM camera-limit table, persistent terrain-region ID, or
one-way camera-zone state was found that soundly abstracts those dimensions. Consequently the
initial collision inventory can reject neither all unreachable camera-machine values nor prove all
legal jump/climb/platform routes.

This closes the static RE question with an exact boundary: **the available static terrain data is
insufficient to derive the requested exact legal envelope without modeling mutable gameplay
state**. Platform semantics, climb/rope semantics, and fall/drop transitions are not sufficiently
abstracted to a record-local graph. Record 22 also remains unproven as a live playable interval;
it is a terminal event/reseed publication state in the current evidence.

### Legal-envelope consequence

The camera machine has a finite, statically derived envelope. Terrain does not yet provide a sound
smaller exact subset per record. There is no authorization to discard any value from the safe
camera-machine set merely because it did not appear in the initial collision inventory.

The following table is consequently an evidence-safe camera-machine **superset**, not an invented
terrain-exact result. It is suitable for a safety pressure test, but not for declaring the final
epoch model complete.

| Records | Selector | Exact primary X behavior / safe X set | Gate-derived Y set | Visible BG source rows | Exact terrain subset |
|---|---:|---|---|---|---|
| 0 | 0/seed | initial publication only | `{0}` | 28 rows; excludes 28..63 | not a demonstrated live camera interval |
| 1..16 | 0 | complete modulo span `0..511` | `260..511 U 0..3` | 61 rows; excludes 60..62 | unresolved |
| 17 | 1 | safe X superset `349..511 U 0..4`; no horizontal stream | full modulo Y `0..511` | all 64 | full Y proven by selector-1 record |
| 18..20 | 0 | complete modulo span `0..511` | `260..511 U 0..3` | 61 rows; excludes 60..62 | unresolved |
| 21 | 1/event 6 | safe X superset `349..511 U 0..4`; no horizontal stream | full modulo Y `0..511` | all 64 | full Y proven by selector-1 record |
| 22 | 0/terminal | complete modulo span `0..511` | conservative `0..259` | 61 rows; excludes 28..30 | active terrain interval unresolved |

Normal live selector-0 records have variable Y. Record 0 is a seed publication rather than a
proven live camera interval. The live selector-0 gate-derived set contains 256 modulo-scroll values
and exposes 61 of 64 source rows after 28/29-row window expansion. This is derived from code and
initialization data, not from trace extrema. It remains a safe superset until terrain reachability
is decoded.

## 8. Static residency pressure test

This test removes the *conceptual* placeholder when counting capacity, so the real plane range is
slots 64..1023: 960 safe plane slots below the PC090OJ sprite base. It does **not** modify the
compiler or generated assets. Pattern code zero is excluded. A horizontal interval includes the
four resident descriptors plus the two incoming descriptors because old and newly published
columns coexist during replacement; seed/vertical intervals use their active four descriptors.

| Rec | Sel | Descriptor union | Plane A | Plane B | Shared | A U B | Excess over 960 |
|---:|---:|---|---:|---:|---:|---:|---:|
| 0 | 0 | 0..3 | 49 | 427 | 0 | 476 | 0 |
| 1 | 0 | 0..5 | 125 | 854 | 0 | 979 | 19 |
| 2 | 0 | 2..7 | 237 | 854 | 0 | 1091 | 131 |
| 3 | 0 | 4..9 | 333 | 854 | 0 | 1187 | 227 |
| 4 | 0 | 6..11 | 210 | 854 | 0 | 1064 | 104 |
| 5 | 0 | 8..13 | 89 | 854 | 0 | 943 | 0 |
| 6 | 0 | 10..15 | 240 | 660 | 0 | 900 | 0 |
| 7 | 0 | 12..17 | 155 | 663 | 0 | 818 | 0 |
| 8 | 0 | 14..19 | 133 | 663 | 0 | 796 | 0 |
| 9 | 0 | 16..21 | 79 | 854 | 0 | 933 | 0 |
| 10 | 0 | 18..23 | 369 | 854 | 0 | 1223 | 263 |
| 11 | 0 | 20..25 | 484 | 854 | 0 | 1338 | 378 |
| 12 | 0 | 22..27 | 226 | 833 | 0 | 1059 | 99 |
| 13 | 0 | 24..29 | 218 | 642 | 0 | 860 | 0 |
| 14 | 0 | 26..31 | 251 | 833 | 0 | 1084 | 124 |
| 15 | 0 | 28..33 | 350 | 851 | 0 | 1201 | 241 |
| 16 | 0 | 36..39 | 220 | 663 | 0 | 883 | 0 |
| 17 | 1 | 36..39 | 70 | 663 | 0 | 733 | 0 |
| 18 | 0 | 36..41 | 54 | 663 | 0 | 717 | 0 |
| 19 | 0 | 38..43 | 54 | 663 | 0 | 717 | 0 |
| 20 | 0 | 40..45 | 85 | 663 | 0 | 748 | 0 |
| 21 | 1 | 42..45 | 116 | 663 | 1 | 778 | 0 |
| 22 | 0 | 52..55 | 219 | 576 | 0 | 795 | 0 |

Nine records (1, 2, 3, 4, 10, 11, 12, 14, and 15) exceed 960 slots under the only currently
evidence-safe selector-0 row envelope. Peak Plane A is 484, peak Plane B is 854, peak shared is 1,
and peak combined is 1,338 at record 11, leaving a 378-slot deficit.

This does **not** prove `BOUNDARY_ONLY_RESIDENCY_INSUFFICIENT`: the pressure test uses the complete
camera-machine superset because the collision/terrain subset is unresolved. Conversely, it is not
safe to discard rows merely to make the records fit. There is no proven persistent sub-record
semantic boundary at which to split the over-budget records. A terrain/collision reachability
decoder (including platform/climb/fall constraints) is the exact remaining boundary.

## 9. Compiler and artifact decision

`tools/translation/compile_pc080sn_genesis.py` now contains the authoritative ownership constants
`SAFE_PLANE_SLOT_FIRST = 64`, `SAFE_PLANE_SLOT_LAST = 1023`, and
`SAFE_PLANE_SLOT_COUNT = 960`. This changes no generated byte because the existing transitional
allocator still subtracts `BG_RESERVE = 320`.

Encoding the 61-row safety superset as if it were exact would produce nine over-budget records;
encoding a narrower unproven subset would risk missing legitimate graphics. Therefore:

- the diagnostic epoch count remains 8; no real A+B epochs were generated;
- the temporary 320-slot reservation remains;
- canonical generated assets were not replaced;
- no transition/DMA metrics are claimed for a nonexistent valid allocation;
- two fresh independent `/tmp` diagnostic generations were byte-identical and each reported
  `23 segments -> 8 epochs`, `627/640` transitional occupancy, and self-validation PASS;
- deterministic diagnostic rebuild remains PASS, but this does not promote the placeholder model
  to a final terrain-exact model;
- production trace dependencies remain 0;
- no per-frame cache/residency architecture was added or authorized.

## 10. Acceptance status

- Original arcade observation: preserved as validation evidence only.
- Camera initialization, owners, dead zones, displacement cap, gates, and modulo invariants: complete.
- Selector/direction versus camera-axis freedom: explicitly separated.
- Descriptor structure, consumption, and source progression: complete.
- Selector-1/2 full modulo-Y progression: complete.
- Selector-0 camera-machine envelope: complete as a conservative code-derived superset.
- Initial Stage-1 collision surfaces and collision-map coordinate transform: complete.
- Dynamic collision mutation and player collision-code effects: identified.
- Selector-0 terrain-constrained legal subset: incomplete; exact state dimensions documented.
- Platform/climb/fall legal transition abstraction: incomplete.
- Proven persistent sub-record graphics boundary: none.
- `BOUNDARY_ONLY_RESIDENCY_INSUFFICIENT`: **not proven**.
- Dynamic cache necessity: **not proven**.
- Real per-epoch Plane-B sets: not generated.
- 320-slot placeholder: retained.
- PC090OJ: untouched.
- Genesis production runtime: untouched.
- ROM/counter: unchanged; counter remains 301.

**PLANE-B MODEL COMPLETE: NO**  
**READY FOR PC090OJ FINAL COMPILER SUBSYSTEM: NO**
