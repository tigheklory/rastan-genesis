# Cody: Original Arcade Sword, Thrust, and Lizardman Semantic Model

Date: 2026-08-12  
Baseline for later comparison: Build 0279  
Build/counter effect: no build; counter remains 279  
Task classification: EXTENDING (original-arcade static analysis and address correlation)

Every conclusion below is labeled **PROVEN**, **HYPOTHESIS**, or **DISPROVEN**. Unless an
address is explicitly labeled otherwise, it must not be treated as interchangeable with an
address in another address space.

## GOVERNANCE READ

**PROVEN:** The current versions of `PROMPT_TEMPLATE.md`, `RULES.md`, `AGENTS.md`,
`CLAUDE.md`, `ARCHITECTURE.md`, and `specs/palette_decisions.json` were read before this
analysis. The current native-replacement policy, issue/finding ledgers, current remap, and
the two task-specific Build 0280 evidence documents were also consulted.

Relevant priors are KF-044 (PC090OJ artwork/code identity), KF-066 (Stage-1 Lizardman bank
`0x36` carrier decision), KF-074 (native player BODY/FRONT semantic lanes), OPEN-006, and
OPEN-024. No CONFIRMED/STRONG prior was contradicted. Several interpretations in the
pre-model capture report are corrected below; the captured observations themselves remain
valid.

## ADDRESS-MAPPING SOURCES

The following current sources were used:

- `build/rastan-direct/address_map.json`: authoritative Build 0279 correlation between
  `arcade_pc`/`arcade ROM/data` and current `runtime_genesis_pc`/`genesis_runtime_data`.
- `specs/rastan_direct_remap.json`: current replacement sites and shift-replacement intent.
- `tools/translation/postpatch_startup_rom.py` and the current shift/reflow tooling: checked
  to distinguish relocated original instructions from Genesis-only helpers.
- `apps/rastan-direct/out/symbol.txt`: Genesis-only helper symbols; such helpers do not have
  an `arcade_pc`.

Blind `+0x200` mapping used: **NO**. Some map results happen to differ by `0x200`, but each
correlation below was resolved from the current JSON map. Reflowed sites do not generally
retain that difference.

## GHIDRA COVERAGE AUDIT

### Starting condition

The prior export contained only 181 functions and did not sufficiently define the attack,
BODY, auxiliary-player, or family-0 actor paths. Raw disassembly existed, but that did not
meet the semantic-decompilation requirement.

### Newly recovered/decompiled

`analysis/ghidra/rastan_arcade/scripts/RastanArcadeSeed.java` now seeds and labels:

- `arcade_pc 0x051090` player main update;
- `arcade_pc 0x051CA0` attack initialization;
- `arcade_pc 0x051D32` attack phase advance;
- `arcade_pc 0x051E24` crouch entry;
- `arcade_pc 0x0540CC` BODY constructor and its piece-construction region;
- `arcade_pc 0x0547C0` auxiliary state update;
- `arcade_pc 0x054810` auxiliary piece constructor;
- `arcade_pc 0x03D054` family-0 actor renderer;
- `arcade_pc 0x03C902` generic actor-record expander;
- the player phase/mapping tables and class-`0x17`/`0x18` descriptor data.

The regenerated export contains 257 functions, 5,717 instructions, `0x501C` classified code
bytes, and 5.22% byte coverage. The low global percentage is expected because the 384-KiB
image contains extensive data and because this was a bounded recovery, not a claim that the
whole game is decompiled.

### Corrected labels and disproof

The path at `arcade_pc 0x045342` was initially considered as a possible Lizardman constructor.
Raw table verification at `arcade ROM/data 0x045592` proves that its observed record selects
tile base `0x0129` and class `0x30`, not Stage-1 Lizardman tile base `0x004B` and classes
`0x17/0x18`. The symbols were therefore retained only as neutral
`paired_actor_init_45342`, `paired_actor_activate_453a2`, and `actor_record_table_45592`.

**DISPROVEN:** `arcade_pc 0x045342` is the Stage-1 Lizardman class-`0x17/0x18` selector.

## SEMANTIC ADDRESS CORRELATION

### Executable code

| Semantic identity | arcade_pc | runtime_genesis_pc | Mapping source / status |
|---|---:|---:|---|
| Sprite control/colbank writer | `0x03A1CC` | `0x03A3CC` | current `address_map.json`, copied arcade code |
| Generic actor-record expander | `0x03C902` | `0x03CB02` | current map, copied arcade code |
| Family-0 actor renderer/class lookup | `0x03D054` | `0x03D254` | current map, copied arcade code feeding native actor output |
| Player main update | `0x051090` | `0x051296` | current map, copied arcade code |
| Attack initialization | `0x051CA0` | `0x051EA6` | current map; input literal is a current remap replacement |
| Attack phase advance | `0x051D32` | `0x051F38` | current map, copied arcade code |
| Crouch entry | `0x051E24` | `0x052024` | current map, copied arcade code |
| BODY state/table selection | `0x0540CC` | `0x0542CC` | current map; function entry has a shift replacement |
| BODY mapping selection | `0x054326` | `0x054504` | current map, copied/reflowed arcade semantics |
| BODY primary decision | `0x05438E` | `0x05456C` | current map, copied/reflowed arcade semantics |
| BODY secondary decision | `0x0543B4` | `0x054592` | current map, copied/reflowed arcade semantics |
| BODY primary piece constructor | `0x054492` | `0x054670` | current map; tuple sink replaced by native PLAYER_BODY lane |
| BODY secondary piece constructor | `0x0546A8` | `0x05487E` | current map; tuple sink replaced by native PLAYER_BODY lane |
| Auxiliary state update | `0x0547C0` | `0x05498C` | current map; obsolete Block-A anchor-copy prologue retired |
| Auxiliary piece constructor | `0x054810` | `0x0549C6` | current map; complete function body replaced |
| FRONT/alternate weapon overlay | `0x059F92` | `0x05A148` | current map; native PLAYER_FRONT tuple sink |

### Original data

| Semantic data | arcade ROM/data | genesis_runtime_data | Mapping source |
|---|---:|---:|---|
| Family-0 class-offset table | `0x03D09E` | `0x03D29E` | current `address_map.json` data segment |
| Class `0x17` descriptor | `0x03D5EB` | `0x03D7EB` | current map |
| Class `0x18` descriptor | `0x03D60C` | `0x03D80C` | current map |
| Upward attack primary phase table | `0x05BAE0` | `0x05BCB0` | current map |
| Downward-thrust primary phase table | `0x05BB10` | `0x05BCE0` | current map |
| Primary piece descriptors | `0x05BD40` | `0x05BF10` | current map |
| Secondary piece descriptors | `0x05C466` | `0x05C636` | current map |
| Auxiliary `0x54810` piece table | `0x05DA5E` | `0x05DC2E` | current map |

`genesistan_pc090oj_hook_sprite_update_54810` is Genesis-only code at
`runtime_genesis_pc 0x072E2C`; it has no `arcade_pc`. The replaced original entry and current
continuation are the `0x054810 -> 0x0549C6` row above.

## ATTACK STATE MODEL

### State fields

| Original arcade field | Proven role |
|---|---|
| `arcade WRAM A5+0x10E8` | broad player action/mode used by BODY table selection; `0` standing, `2/3` downward-motion states, `5` crouch, `8` death |
| `arcade WRAM A5+0x1116` | attack variant: `0` upward, `1` downward thrust, `4` horizontal/default |
| `arcade WRAM A5+0x1108` | attack-active flag (`1` while attack sequence is active); **not** the crouch flag |
| `arcade WRAM A5+0x1114` | attack facing/directional selector; value `2` uses unmirrored descriptors, the opposite direction uses the mirrored transform |
| `arcade WRAM A5+0x110A` | attack animation phase, initialized to zero and advanced by `arcade_pc 0x051D32` |
| `arcade WRAM A5+0x110C` | attack timing/substate initialized to `1` |
| `arcade WRAM A5+0x1390` | attack terminal phase (normally initialized to 24; another proven path writes 15) |
| `arcade WRAM 0x10D37A` | active-low per-frame input sampled by attack initialization |

At `arcade_pc 0x051CA0`, the input/state decision is:

1. active-low input bit 2: variant `4`, facing `2`;
2. otherwise active-low bit 3: variant `4`, facing `3`;
3. otherwise broad action `4`, `6`, or `9`: variant `4`;
4. otherwise active-low bit 0: variant `0` (upward attack);
5. otherwise broad action `2` or `3` plus active-low bit 1: variant `1` (downward thrust);
6. otherwise variant `4`.

The initializer then writes `A5+0x110C=1`, `A5+0x110A=0`, and `A5+0x1108=1`.
`arcade_pc 0x051D32` advances the phase and clears/ends the sequence at the configured terminal
phase. Variant `1` while broad action is `3` has a special final-phase hold/repeat path.
`arcade_pc 0x051E24` establishes broad action `5`, proving crouch independently of the
attack-active flag.

| Visible attack | Selector conditions | Arcade code path | Mapping/table path | Animation/index fields |
|---|---|---|---|---|
| Standing horizontal sword | broad action `0`, attack active, variant `4` | `arcade_pc 0x051CA0`, BODY `0x0540CC` | primary `arcade ROM/data 0x05B6A0`; secondary `0x05BA78` | phase `A5+0x110A` |
| Crouching horizontal sword | broad action `5`, attack active, variant `4` | crouch entry `0x051E24`, attack init `0x051CA0`, BODY `0x0540CC` | primary `0x05B978`; secondary `0x05B948` | phase `A5+0x110A` |
| Downward thrust | broad action `2` or `3`, attack active, variant `1` | attack init `0x051CA0`, BODY decisions `0x05438E/0x0543B4` | primary `0x05BB10`; secondary action-2 `0x05B740`, action-3 `0x05B7E8` | phase `A5+0x110A` |

**DISPROVEN:** broad action `8` denotes downward thrust. It is selected by the death path
(including the health-depleted setter at `arcade_pc 0x0517E6`).

## SHARED BODY PIECE FORMAT AND FLIP CONTRACT

The primary descriptor bank at `arcade ROM/data 0x05BD40` and secondary bank at
`arcade ROM/data 0x05C466` contain fixed four-record maps. Each record is six bytes:
`{code16, xoff8, yoff8, attr16}`. Code zero blanks that record and the remaining output slot.
All attack records in scope carry source attr `0x0003`.

For facing value `2`, the constructor emits the descriptor without horizontal mirroring. For
the opposite facing it ORs `0x4000` into the attribute and computes the mirrored X as
`-xoff-16`. Y is `baseY + sign_extend(yoff) + 1`, masked to nine bits; X is similarly based
on the player anchor and masked to nine bits. Thus final word0 is `0x0003` or `0x4003`; the
source palette nibble remains `3` in either direction.

## STANDING SWORD ORIGINAL ARCADE POSE

### Phase-to-selector path

Primary table `arcade ROM/data 0x05B6A0`:

| Phase | Selector |
|---|---:|
| 0 | `0x00` |
| 1 | `0x01` |
| 2 | `0x02` |
| 3 | `0x03` |
| 4-5 | `0x04` |
| 6-13 | `0x05` |
| 14-15 | `0x04` |
| 16-17 | `0x03` |
| 18-19 | `0x02` |
| 20-21 | `0x01` |
| 22-23 | `0x00` |

Secondary table `arcade ROM/data 0x05BA78` selects map `0x00` for phases 0-1 and map
`0x11` for phases 2-23.

### Complete primary maps

All rows have attr `0x0003` before facing flip.

| Selector | Piece | Code | Xoff | Yoff | Provable role |
|---:|---:|---:|---:|---:|---|
| `00` | 0/1/2 | `08E/08F/090` | `-8/-16/0` | `-32/-16/-16` | complete standing upper/body composite; `08E` is the sword-bearing top piece |
| `01` | 0/1/2 | `08E/091/092` | `-8/-16/0` | `-32/-16/-16` | standing attack transition |
| `02` | 0/1/2 | `08E/093/094` | `-8/-16/0` | `-32/-16/-16` | standing attack transition |
| `03` | 0/1/2 | `095/096/097` | `-8/-16/0` | `-32/-16/-16` | extended standing attack |
| `04` | 0/1/2 | `098/099/09A` | `-8/-16/0` | `-32/-16/-16` | extended standing attack |
| `05` | 0/1/2 | `09B/09D/09C` | `-8/-8/-24` | `-32/-16/-16` | maximum standing extension |

Secondary map `0x00` is codes `076,077,078,079` at offsets `(-16,0)`, `(0,0)`,
`(-16,16)`, `(0,16)`. Secondary map `0x11` is codes `109,10A` at `(-16,8)`, `(0,8)`.
Together the primary and secondary maps are the complete original standing composition.

## CROUCHING SWORD ORIGINAL ARCADE POSE

Primary and secondary phase tables use selectors `06,07,08,09,0A,0B` on exactly the same
phase ranges as standing selectors `00..05` above.

| Selector | Primary codes | Primary offsets | Secondary codes | Secondary offsets | Attr / role |
|---:|---|---|---|---|---|
| `06` | `0AC,0AD` | `(-16,-8),(0,-8)` | `0AE,0AF` | `(-16,8),(0,8)` | `0003`; crouch start, sword/body complete |
| `07` | `0B0,0B1` | same | `0B2,0B3` | same | `0003`; crouch transition |
| `08` | `0B4,0B5` | same | `0B6,0B7` | same | `0003`; crouch transition |
| `09` | `0B8,0B9` | same | `0BA,0BB` | same | `0003`; crouch extension |
| `0A` | `0BC,0BD` | same | `0BE,0BF` | same | `0003`; crouch extension |
| `0B` | `0C0,0C1` | `(-24,-8),(-8,-8)` | `0C2,0C3` | `(-16,8),(0,8)` | `0003`; maximum crouch extension |

Facing applies only the proven BODY mirror contract; no alternate crouch palette exists.

## DOWNWARD-THRUST ORIGINAL ARCADE POSE

Primary table `arcade ROM/data 0x05BB10` selects:

The selector byte is read at `0x05BB10 + phase*2`. The selector indexes a big-endian word
offset table at `0x05BD40`; adding that offset to `0x05BD40` locates the descriptor. These
raw bytes settle the prior `0x008E` versus `0x0104` wording unambiguously:

| Phase | selector | descriptor address | raw primary piece-0 bytes | code | xoff | yoff | attr |
|---|---:|---:|---|---:|---:|---:|---:|
| 0-1 | `0x00` | `0x05BDD6` | `00 8E F8 E0 00 03` | `0x008E` | `-8` | `-32` | `0x0003` |
| 2-5 | `0x19` | `0x05BFE8` | `01 01 F8 E0 00 03` | `0x0101` | `-8` | `-32` | `0x0003` |
| 6-9 | `0x1A` | `0x05BFFC` | `01 04 F8 E0 00 03` | `0x0104` | `-8` | `-32` | `0x0003` |
| 10-23 | `0x1B` | `0x05C010` | `01 04 F8 E8 00 03` | `0x0104` | `-8` | `-24` | `0x0003` |

The complete primary maps are therefore:

| Phase | Primary selector | Primary complete piece set (code @ x,y; attr) |
|---|---:|---|
| 0-1 | `00` | `08E@-8,-32`, `08F@-16,-16`, `090@0,-16`; `0003` |
| 2-5 | `19` | `101@-8,-32`, `102@-16,-16`, `103@0,-16`; `0003` |
| 6-9 | `1A` | `104@-8,-32`, `105@-16,-16`, `106@0,-16`; `0003` |
| 10-23 | `1B` | `104@-8,-24`, `107@-16,-8`, `108@0,-8`; `0003` |

For broad action `2`, secondary table `arcade ROM/data 0x05B740` supplies selector `0x0C`
for phases 0-9 and `0x11` for phases 10-23. Broad action `3` uses the equivalent table at
`0x05B7E8`.

- Secondary selector `0x0C`: `10B@-16,0`, `10C@0,0`, `10D@-16,16`, `10E@0,16`.
- Secondary selector `0x11`: `109@-16,8`, `10A@0,8`.

All carry source attr `0x0003`, with the normal BODY facing transform.

For completeness, variant `0` is the separate upward attack: primary table
`arcade ROM/data 0x05BAE0` selects `00` at phases 0-1, `0C` at 2-5 and 20-23, `0D` at
6-9 and 18-19, and `0E` at 10-17. It is not the downward thrust.

## DOWNWARD-THRUST TIP IDENTITY

**PROVEN:** The downward-thrust sword tip belongs to the BODY primary composition, not to
`arcade_pc 0x054810` and not to FRONT.

| Property | Original arcade identity |
|---|---|
| Attack selector | variant `1`, broad action `2` or `3`, attack-active `A5+0x1108=1` |
| Producer | BODY at `arcade_pc 0x0540CC`, primary constructor at `arcade_pc 0x054492` |
| Mapping path | phase table `arcade ROM/data 0x05BB10` -> primary descriptor bank `0x05BD40` |
| Piece index | primary piece 0 (top/sword-bearing piece) |
| Phase 0-1 | code `0x008E`, attr `0x0003`, X `-8`, Y `-32` |
| Phase 2-5 | code `0x0101`, attr `0x0003`, X `-8`, Y `-32` |
| Phase 6-9 | code `0x0104`, attr `0x0003`, X `-8`, Y `-32` |
| Phase 10-23 | code `0x0104`, attr `0x0003`, X `-8`, Y `-24` |

Thus code `0x0104` is the persistent fully extended thrust-tip art from phase 6 onward; at
phase 10 the same art moves eight pixels downward with the rest of the late thrust pose.
Facing changes only the proven horizontal flip/X transform.

## `0x54810` SEMANTIC ROLE

`arcade_pc 0x0547C0` updates state words `A5+0x1296`, `A5+0x1298`, and `A5+0x129E`, then
calls `arcade_pc 0x054810`. The constructor indexes `arcade ROM/data 0x05DA5E` in 24-byte
maps of four six-byte records:

- mode 1: phase limit 12, table indices 0-2, one nonblank source code `0x0275`, `0x0276`,
  or `0x0277`;
- mode 4: phase limit 20, table indices 4-8, four-piece effects using codes
  `0x0278..0x0287` and `0x02A9..0x02AC`.

Owner code at `arcade_pc 0x0529CC` activates this state with sound command `0x26` and
player-reaction/vertical-motion state. Dispatch around `arcade_pc 0x05506C` and the table at
`arcade ROM/data 0x0550A8` selects mode 1 or 4 for the associated player subobject. A sibling
producer at `arcade_pc 0x052A64` uses the same state/table family.

Direct tile decode of `build/regions/pc090oj.bin` shows these codes are compact effect art,
whereas the melee sword is visibly integrated into the BODY codes listed above.

**PROVEN:** `arcade_pc 0x054810` is a player-attached effect/subobject family and does not
participate in standing sword, crouching sword, or downward-thrust sword-tip construction.

**PROVEN:** `arcade_pc 0x059F92` is the separate FRONT thrown/special-weapon overlay
(codes `0x0A64..0x0A6D`), not the normal melee sword.

**HYPOTHESIS:** the exact player event names for every mode-1/mode-4 effect (spark, slash,
impact, or reaction) remain less certain than their ownership and non-melee classification.
No Genesis trace is needed to establish the current task's important boundary: they are not
the missing thrust tip.

## LIZARDMAN ORIGINAL ARCADE POSE MODEL

### Executable renderer and record format

At `arcade_pc 0x03D054`, family byte `A4+0x38` selects specialized families 1-4 or the
family-0 class-offset table at `arcade ROM/data 0x03D09E`. The class byte is supplied in D0,
masked to eight bits, doubled, and used to select a signed descriptor offset. The resulting
descriptor is expanded by `arcade_pc 0x03C902`.

The normal descriptor record is four bytes:

```text
control8, yoff8, code_offset8, xoff8
```

The expander combines `A4+0x1E` (base code), `A4+0x1A` (base Y), `A4+0x16` (base X),
orientation state, and `A4+0x27` (actor attr/control). If actor attr bit 6 is set, the emitted
low attribute byte is copied from that field; the Stage-1 value `0x46` therefore preserves
source nibble 6. Mirroring adds word0 `0x4000` and applies the corresponding 16-pixel X
transform. Descriptor high-nibble `0x40` requests code-offset negation; neither class in
scope uses it. Their record control is `0x01` throughout.

### Complete class compositions

| Lizardman class/frame | Piece | Code | Control | Xoff | Yoff | Expected orientation/role |
|---|---:|---:|---:|---:|---:|---|
| `0x17` | 0 | `0x0066` | `0x01` | 0 | +1 | lower/right pose constituent |
| `0x17` | 1 | `0x0064` | `0x01` | 0 | -15 | middle/right pose constituent |
| `0x17` | 2 | `0x004E` | `0x01` | 0 | -15 | common upper/body-and-club silhouette constituent |
| `0x17` | 3 | `0x004C` | `0x01` | 0 | -31 | upper/right constituent |
| `0x17` | 4 | `0x0065` | `0x01` | -16 | +1 | lower/left pose constituent |
| `0x17` | 5 | `0x0063` | `0x01` | -16 | -15 | middle/left pose constituent |
| `0x17` | 6 | `0x004D` | `0x01` | -16 | -15 | common upper/body-and-club silhouette constituent |
| `0x17` | 7 | `0x004B` | `0x01` | -16 | -31 | upper/left constituent |
| `0x18` | 0 | `0x0069` | `0x01` | 0 | 0 | alternate lower/right pose constituent |
| `0x18` | 1 | `0x0067` | `0x01` | 0 | -16 | alternate middle/right constituent |
| `0x18` | 2 | `0x004E` | `0x01` | 0 | -16 | common upper/body-and-club silhouette constituent |
| `0x18` | 3 | `0x004C` | `0x01` | 0 | -32 | upper/right constituent |
| `0x18` | 4 | `0x0068` | `0x01` | -16 | 0 | alternate lower/left constituent |
| `0x18` | 5 | `0x0063` | `0x01` | -16 | -16 | middle/left constituent |
| `0x18` | 6 | `0x004D` | `0x01` | -16 | -16 | common upper/body-and-club silhouette constituent |
| `0x18` | 7 | `0x004B` | `0x01` | -16 | -32 | upper/left constituent |

Class `0x18` is therefore not a palette or flip variant of class `0x17`. It changes lower
overlay codes (`66/64/65` to `69/67/68`) and shifts the common upper group by one pixel.
Both are complete eight-piece poses. Actor facing `0` follows the mirrored actor path in the
existing evidence; the descriptor data itself does not request code negation or vertical
flip.

Direct artwork inspection proves that codes `0x004B..0x004E` collectively form the common
upper/body-and-club silhouette while codes `0x0063..0x0069` complete the lower/pose-specific
overlay. It is unsafe to call `0x004E` alone “the club” or to repair it independently.

**PROVEN:** the complete original class-`0x17` and class-`0x18` compositions, record width,
piece order, offsets, control, code arithmetic, attr source, flip behavior, and lack of code
negation are known.

### Existing-trace actor-scoped check

The corrected Build 0279 capture supplies the previously missing one-frame correlation. At
authoritative bad-pose marker frame `10168`, actor index 5 is family 0, class `0x17`, facing
0, base X/Y `0x00CC/0x0081`, base code `0x004B`, and attr `0x46`. Its output is exactly
BACK_ENEMY queue entries 0-7. Applying the class-`0x17` descriptor, facing transform, and the
established BACK_ENEMY Y bias gives the following complete actor-specific result:

| Piece | expected code | expected native X/Y | native code | native X/Y | SAT/art result |
|---:|---:|---:|---:|---:|---|
| 0 | `0x0066` | `0x00BC/0x007A` | `0x0066` | `0x00BC/0x007A` | SAT 25, tile 1128, exact converted code |
| 1 | `0x0064` | `0x00BC/0x006A` | `0x0064` | `0x00BC/0x006A` | SAT 26, tile 1096, exact converted code |
| 2 | `0x004E` | `0x00BC/0x006A` | `0x004E` | `0x00BC/0x006A` | SAT 27, tile 1256, exact converted code |
| 3 | `0x004C` | `0x00BC/0x005A` | `0x004C` | `0x00BC/0x005A` | SAT 28, tile 1216, exact converted code |
| 4 | `0x0065` | `0x00CC/0x007A` | `0x0065` | `0x00CC/0x007A` | SAT 29, tile 1112, exact converted code |
| 5 | `0x0063` | `0x00CC/0x006A` | `0x0063` | `0x00CC/0x006A` | SAT 30, tile 1072, exact converted code |
| 6 | `0x004D` | `0x00CC/0x006A` | `0x004D` | `0x00CC/0x006A` | SAT 31, tile 1244, exact converted code |
| 7 | `0x004B` | `0x00CC/0x005A` | `0x004B` | `0x00CC/0x005A` | SAT 32, tile 1200, exact converted code |

All eight queue records use `word0=0x4046`; all eight SAT records preserve hflip, resolve to
line 0 under the established Stage-1 Lizardman decision, and reference the resident tile
recorded for the same source code. `preconvert_pc090oj_tiles.py` is a lossless 128-byte
reordering (TL, BL, TR, BR), and runtime DMA addresses `rastan_pc090oj + code*128`; there is
no alternate art lookup between source code and these SAT tiles.

Result **B**: this exact marked actor's pose and converted art are fully identical to the
class-`0x17` model. No queue/art/transform defect was found for actor 5 at frame 10168. This
does not dispute the user-visible defect; it means that defect is not explained by the
recorded representation of this selected actor.

## ORIGINAL ARCADE PALETTE SEMANTICS

### Global gameplay sprite control

At `arcade_pc 0x03A1CC`, the original writes D0=`0x0060`, preserves the low nibble of
`A5+0x14`, ORs it into D0, writes the result to arcade PC090OJ sprite control
`arcade HW 0x00380000`, and stores the shadow back at `A5+0x14`. The gameplay captures and
source both establish colbank bits `0x0060`. Effective bank is source nibble OR the colbank
contribution: `(0x60 >> 1) = 0x30`.

### Rastan / melee sword

Palette Decision ID: `PAL-PC090OJ-GAMEPLAY-RASTAN-SWORD-001` (`proven`).

- source attr nibble: `0x3`;
- sprite control / colbank: `0x0060`;
- effective arcade bank: `0x33`;
- all standing, crouching, and thrust BODY descriptors in this report use attr `0x0003`;
- facing only adds horizontal-flip bit `0x4000`;
- no attack type or phase changes the arcade palette identity.

### Stage-1 Lizardman

Palette Decision ID: `PAL-PC090OJ-STAGE1-LIZARDMAN-001` (`decided` for its Genesis carrier;
the underlying arcade semantics are established).

- actor attr/source nibble: `0x6` (`A4+0x27 = 0x46` in the relevant family-0 actor);
- sprite control / colbank: `0x0060`;
- effective arcade bank: `0x36`;
- current Genesis realization intentionally carries bank `0x36` on CRAM line 0 in Stage 1.

This evidence is Stage-1/scene-1 specific. Reused artwork or an actor-family number does not
authorize a global palette identity in another stage. No registry mapping was changed by
this task.

## EXISTING BUILD 0279 COMPARISON

This section uses the completed arcade model above, the current remap/source, and only then
the already-preserved corrected Build 0279 capture.

### Current implementation boundaries

| Semantic function | arcade_pc | runtime_genesis_pc | Current implementation status |
|---|---:|---:|---|
| Attack selection/phase | `0x051CA0/0x051D32` | `0x051EA6/0x051F38` | arcade state machine retained; input literal rebased to Genesis WRAM |
| BODY selection | `0x0540CC` | `0x0542CC` | original state/table decisions retained; register preservation added |
| BODY primary/secondary expansion | `0x054492/0x0546A8` | `0x054670/0x05487E` | original map/code/attr/coordinate calculations retained; final tuple stores replaced by native PLAYER_BODY queue emission |
| Auxiliary effect family | `0x054810` | `0x0549C6` | original body replaced by Genesis-only helper `runtime_genesis_pc 0x072E2C`; compatibility-slot output is not part of the native gameplay finalizer |
| Family-0 Lizardman selection/expansion | `0x03D054/0x03C902` | `0x03D254/0x03CB02` | original class descriptor semantics retained; output adapted to native BACK_ENEMY lane |
| Sprite control writer | `0x03A1CC` | `0x03A3CC` | original arcade writer retained; Genesis palette route consumes its semantics |

### Classified discrepancies

1. **PROVEN:** The corrected capture's crouch rows (broad action `5`, variant `4`) match the
   arcade crouch selector family, including codes `0x0C0..0x0C3` at maximum extension.
   Changing their BODY geometry or flip is not supported.
2. **PROVEN:** The corrected capture's authoritative downward-thrust marker at external frame
   15617 did not retain the later action rows because action onset fell outside the 90-frame
   window. The arcade model nevertheless identifies the exact thrust-tip piece without a new
   capture: BODY primary piece 0, code `0x0104` from phase 6 onward.
3. **DISPROVEN:** `arcade_pc 0x054810` supplies the normal sword or downward-thrust tip. It is
   a separate player-attached effect family. Its current orphaned compatibility realization
   may omit those effects, but cannot explain a missing BODY thrust tip.
4. **CORRECTED DIAGNOSTIC INTERPRETATION:** The capture contains rows that pair displayed SAT
   line 0 with `source_nibble=3`, but its frame-done sampler reads the displayed SAT bank and
   the single metadata array after that metadata is reusable for the next build. Those two
   fields are not guaranteed to describe the same bank at capture time. The current source
   keeps metadata coherent with the bank during commit-time palette fixup; therefore the
   recorded same-row nibble/line pairing is not proof of a runtime palette-routing mismatch.
5. **PROVEN:** During the bad-Lizardman markers, family 0, classes `0x17/0x18`, base
   `0x004B`, attr `0x46`, and code `0x004E` reach the native queue/residency/SAT with the
   expected mirrored transform. Flipping, negating, moving, or recoloring `0x004E` is not
   supported.
6. **PROVEN:** Actor 5 at marked frame 10168 is an actor-scoped, complete class-`0x17`
   eight-piece match through queue, residency, SAT, and deterministic converted art.
7. **UNRESOLVED USER-VISIBLE RESULT:** The selected actor's recorded representation does not
   explain the bad pose the user observed. This is not evidence that the observation did not
   occur; it bounds the remaining issue outside this actor's captured queue/art/transform.

## STOP / NEXT-STEP GATE

- Governance read: **YES**
- `PROMPT_TEMPLATE.md` followed: **YES**
- `RULES.md` followed: **YES**
- `AGENTS.md` followed: **YES**
- `CLAUDE.md` followed: **YES**
- `ARCHITECTURE.md` followed: **YES**
- `build/rastan-direct/address_map.json` consulted: **YES**
- `specs/rastan_direct_remap.json` consulted where relevant: **YES**
- Blind `+0x200` address assumptions used: **NO**
- Arcade attack code sufficiently decompiled: **YES**
- Standing arcade pose fully known: **YES**
- Crouching arcade pose fully known: **YES**
- Downward-thrust arcade pose fully known: **YES**
- Exact thrust-tip piece known: **YES**
- `0x54810` semantic role known: **YES** for ownership and non-melee classification
- Complete Lizardman bad-pose arcade composition known: **YES** for both observed classes
- Arcade palette semantics for current scope known: **YES**
- Current `arcade_pc` <-> `runtime_genesis_pc` correlations proven from current mapping data:
  **YES**
- Existing Build 0279 evidence sufficient for an actor-scoped Lizardman comparison: **YES**
- Selected marked actor differs from its original class model: **NO**
- Existing Build 0279 frame-done metadata sufficient to prove nibble-3 -> line-0 routing:
  **NO**; it pairs a displayed SAT bank with reusable single-buffer metadata.

- No MAME run: **YES**
- No new user gameplay requested: **YES**
- Gameplay implementation changes: **NO**
- Build produced: **NO**
- Counter: **279**
