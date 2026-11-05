TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0080

# R1-S2 Palette/Bestiary Source Handoff for Andy

Research/documentation only. No Palette Composer, generator, `Test.json`, palette-decision registry,
production source, ROM, or build-counter change was made.

## Scope and Evidence

This supplements, rather than replaces, Andy's Bestiary. Authority was applied in this order: original
arcade 68000 instructions/tables, maintained decompilation, the preserved **ORIGINAL ARCADE** R1 castle
actor sweep, then screenshots as a cross-check. The principal durable inputs are:

- `build/maincpu.disasm.txt` and `analysis/ghidra/rastan_arcade/exports/linear_disassembly.tsv`;
- `analysis/decompilation/c/raw/00040ccc.c`, the state dispatcher at `$040BAA`, and original routines
  `$042EF8`, `$04684E`, `$047140`, and `$0473B8`;
- `analysis/enemy_sprite_lexicon/evidence/arcade_sweep/round1_castle/observations.csv`;
- `tools/graphics_optimizer/compositor_vm.py` over original `maincpu`/PC090OJ regions;
- `analysis/actor_decompilation/h21_hazard_census.tsv` and the R1-S2 Plane-A corpus at
  `analysis/graphics_optimizer/subround_corpus/PAL-R1-S2-PLANEA-CASTLE/`;
- Palette Decision `PAL-PC090OJ-R1S2-GREEN-SWORD-KNIGHT-001` (consulted, not changed).

Existing project tools reused: the committed compositor VM, actor sweep, maintained decompilation, Ghidra
exports, and Plane-A corpus. New tooling created: none. No trace was run.

For any later native implementation, the semantic cut is **arcade actor state/animation selection or
identified map-hazard state -> final Genesis pattern/palette realization**. The retired chip tail is the
PC090OJ compositor/SAT or PC080SN tile/name-RAM realization below that semantic decision. This report does
not recommend a chip shadow, hardware emulation layer, or global graphics recolor.

Status words below mean exactly `PROVEN`, `STRONGLY SUPPORTED`, or `UNRESOLVED`.

## Green Sword Warrior Identity

**PROVEN:** R1-S2 uses the family-2 visual domain with base graphics `$033E`; the canonical existing
semantic name remains `object:castle.green_sword_knight`, and its existing decision is
`PAL-PC090OJ-R1S2-GREEN-SWORD-KNIGHT-001`. Do not rename it in the Composer.

The original compositor proves a detail that the current single-green-line preview obscures. The program
tables contain these **bit-6-clear defaults**; with the gameplay PC090OJ high bank `$30`, their embedded
control nibbles would become effective banks `$30+nibble`:

- normal and state-`$1F` programs split the sword pieces onto nibble 3 / effective bank `$33` and the body
  onto nibble 7 / effective bank `$37`;
- airborne `$20-$23` uses nibble 7 / bank `$37`;
- short reaction `$71-$73` uses nibble C / bank `$3C`;
- the shared rope-sheet programs use `$30`, `$34`, or `$39`.

They are not, however, the final selector for the preserved R1 sweep. **PROVEN:** every observed `$033E`
record has creation attribute `$44` or `$41` (960 and 326 observations respectively), with bit 6 set.
Original `$3C9E8/$3C902` therefore overrides every piece's low byte with that actor attribute. The emitted
records use line nibble 4 or 1 uniformly (native effective bank `$34` or `$31` under the `$30` colbank),
not the table's weapon/body split. The table split remains relevant to bit-6-clear transformed/reaction
instances and must not be erased from provenance.

The existing registry decision records the authoring reference as R1 line 3 -> pool `$0C` and runtime
bank `$33`. That decision was not altered here. It does not match the `$44/$41` selectors in the preserved
sweep; PROMT-ID-0069 already calls the field-CRAM relationship unresolved. This report records the conflict
instead of silently redefining the canonical mapping. Andy must retain both the actor override and the
embedded defaults in evidence, and must not infer that every pose actually emits bank `$33`.

Turning/facing is performed by the compositor's facing/flip branch and does not create a new animation
program or a second palette decision. Ordinary death changes to the shared base `$0A73` death family; it
is not another `$033E` pose and remains colored through the owning-enemy death semantics documented in the
Bestiary.

## Complete Warrior Pose / Animation Matrix

The existing PROMT-ID-0078 report's claim that 17 programs are the complete displayed domain is
**superseded**. The preserved ORIGINAL ARCADE R1 castle sweep displays 12 additional state-`$1F` programs.
It contains 1,286 `$033E` observations: `$20-$23`, `$93-$95`, `$97-$9C`, and `$A1-$A6`. In particular,
232 observations are state `$1F`. The current Composer/generator list contains only the earlier 17-program
set and omits both state-`$1F` sequences.

| Status / semantic domain | Actor state or condition | Programs and original selector | Final PC090OJ pattern codes by embedded default nibble (before `+$27` bit-6 override) | Current Composer |
|---|---|---|---|---|
| **PROVEN**, normal moving/facing domain; exact idle/walk names are not individually pinned | common engines `$47140/$473B8`; sweep states `$01/$02`, one `$10`; state-$11` family 2 also selects the range | `$93-$96`; `$4684E` selects `$93+{1,2,3}`, common engines select the normal phase | `$93`: p3 `26B,26C`; p7 `341,33F,365,340,33E,364,356,363`. `$94`: p3 `26B,26C`; p7 `345,343,365,344,342,364,356,363`. `$95`: p3 `26B,26C`; p7 `349,347,365,348,346,364,356,363`. `$96`: p3 `26B,26C`; p7 `385,383,365,382,387,356,386,388` | **YES** |
| **PROVEN**, passive/turning airborne domain; human pose name only strongly supported | states `$0D/$0E`, `$473B8`, family 2 | `$20 + {0,1,2,3}` from table `$47562` | p7 only: `$20` `36B,369,367,36C,36A,368,366`; `$21` `372,370,36E,373,371,36F,36D`; `$22` `379,377,375,37A,378,376,374`; `$23` `36B,37E,37C,36C,36A,37D,37B` | **YES** |
| **PROVEN**, short mode-driven reaction/effect; **not proven to mean crouch** | state `$0F`, mode `+$03 != 0`, `$40E0E`; six-tick steps, SFX `$17`, ends after phase 3 | `$71,$72,$73` (`$70 + ++phase`) | pC: `$71` `345,343,344,342`; `$72` `349,347,348,346`; `$73` `34D,34B,34C,34A` | **YES**, but mislabeled “crouch” as a fact |
| **PROVEN shared-sheet family-8 programs**, visually the climbing warrior; **not the family-2 record changing to family 8** | state `$11`, `$4684E`, `actor+$3E == 8` | `$4D,$56-$5A`; table `$468C8={09,0D,0D,0C,0B,0A,09,00}` | `$4D` p0 `343,344,345,348,349` (duplicates emitted); `$56` p4 `293,341,33F,292,340,33E,291,294,342`; `$57` p9 `344,340,343,33F,33E,345,341,342`; `$58` p9 `34F,349,34E,348,34D,347,34C,346,350,34A,351,34B`; `$59` p9 `358,354,357,353,35B,356,352,359,355,35A`; `$5A` p9 `365,360,364,35F,35C,363,35E,366,361,35D,367,362` | **YES** |
| **PROVEN displayed**, state-`$1F` normal table; **STRONGLY SUPPORTED** as a low/weapon-action sequence | state `$1F`, `$42EF8`, family 2, `actor+$21 bit2 == 0` | table `$42FBC={00,0E,0F,10,11,12,13,13,12,11,0F,0E}` + `$93` -> `$93,$A1,$A2,$A3,$A4,$A5,$A6,$A6,$A5,$A4,$A2,$A1` | `$A1-$A6` sword p3 respectively `26B/26C`, `26E/26D`, `26F/270`, `271`, `272`, `273/274`; p7 body respectively `357,356,358`; `359,356,35A`; `35B,356,35C`; `35D,356,35E`; `35F,356,360`; `361,356,362`, each also using the stationary body group `341,33F,340,33E` | **NO** |
| **PROVEN displayed**, state-`$1F` alternate table; **STRONGLY SUPPORTED** as the second low/weapon-action sequence | state `$1F`, `$42EF8`, family 2, `actor+$21 bit2 != 0`; also writes `+$37=$61` | table `$42FD4={04,04,05,06,07,08,09,09,08,07,05,04}` + `$93` -> `$97,$97,$98,$99,$9A,$9B,$9C,$9C,$9B,$9A,$98,$97` | p3 sword sequence is the same `26B-274`; p7 body: `$97` `38C,38A,38B,389`; `$98` `390,38E,38F,38D`; `$99` `394,392,393,391`; `$9A` `398,396,397,395`; `$9B` `39C,39A,39B,399`; `$9C` `3A0,39E,39F,39D` | **NO** |

The 12 omitted programs add 32 codes not present in the current 17-program set:
`26D-274` and `389-3A0`. The corrected union is **29 programs / 109 distinct codes**, not 17/77.

Program `$74` needs careful treatment. `$468E8-$46910` can produce `$71-$74` for the generic
non-family-2/non-family-8 state-$11` branch using `$46916={05,06,04,03,03,04,06,05}`. Separately,
the proven R1 torch transform installs base `$0DAB` with program `$74`. Neither path proves `$74` is a
family-2 green-warrior pose. Do not add `$74` to this semantic object without a runtime record showing
base `$033E` and program `$74` together.

## Warrior Weapon Semantics

The warrior weapon is an **attached piece in the same PC090OJ compositor program**, not a separately
allocated sprite object, for every source-proven `$033E` frame above. In normal program `$93`, the upright
sword is codes `26B,26C`; state-`$1F` rotates that weapon through `26D-274`. The program defaults give the
sword nibble 3 and body nibble 7, but the preserved R1 actors' `$44/$41` creation attributes override the
whole composite to line 4 or 1. This two-stage selection is the source-backed reason Andy must neither
flatten the provenance to one embedded nibble nor treat the preview's single green line as runtime proof.

The player held-weapon path is separate: `analysis/actor_decompilation/h24_player_weapon_cells.tsv`
derives Rastan's sword/axe/hammer/flame-sword pieces from tables `$5CD8A/$5D346/$5D666/...`, all under the
player bank-`$33` context. A code-set comparison finds **zero PC090OJ code overlap** between those player
weapon pieces and the complete 29-program `$033E` domain. Therefore the prompt's conditional warning is
resolved as follows: the warrior and Rastan share human weapon *types*, but the currently proven sword
artwork is not the same pattern-code identity. Never recolor Rastan's weapon object globally to color the
warrior sword.

## Sword

**PROVEN.** Canonical suggested context: `object:castle.green_sword_knight.weapon.sword`, as a child
semantic context of the existing warrior object, not a new independent actor palette decision.

- Upright/reference frame: program `$93`, pieces `26B,26C`.
- Complete moving-weapon artwork: `26B-274`, exercised by `$97-$9C` and `$A1-$A6`.
- Embedded bit-6-clear default: sword nibble 3 / `$33`; body nibble 7 / `$37`.
- Preserved R1 sweep: actor attribute `$44` or `$41` overrides the entire composite, yielding line 4 or 1
  (native effective bank `$34` or `$31` under the `$30` colbank).
- Representative previews: `$93` (upright), `$A3` (middle action), `$A6` (action extreme), `$99` and
  `$9C` (alternate low/action sequence). All underlying programs/codes must be covered even if only those
  representatives are shown.

One warrior decision is sufficient if the Composer supports sub-parts/pose groups beneath the existing
object. A separate sword decision is unnecessary unless Tighe chooses a genuinely different mapping.

## Hammer

**UNRESOLVED in original-program provenance for this R1-S2 family.** Tighe's gameplay observation that
warriors can carry hammers is valuable reachability evidence, but no inspected `$033E` selector or frame
table chooses the player hammer table, and the complete known `$033E` pattern set does not intersect the
player hammer codes. Do not label any `$033E` program “hammer” from silhouette alone.

Smallest missing evidence: an **ORIGINAL ARCADE** capture while the hammer warrior is visible containing
the owning actor record (`+$01,+$05,+$1E,+$21,+$27,+$38,+$3E`) and its emitted PC090OJ records. The first
writer of the distinguishing selector then identifies the source table. Andy may reserve a disabled
`weapon.hammer` placeholder, but must not author or generate it as proven coverage.

## Axe

**UNRESOLVED in original-program provenance for this R1-S2 family**, for the same reason as Hammer. The
known `$033E` domain has zero overlap with Rastan's player axe codes (`485-490` among the ordinary frames).
The same smallest capture/writer proof is required. Keep a future warrior-axe semantic variant separate
from `object:weapon.axe`; do not recolor the player axe globally.

## Flame Sword Eligibility

**UNRESOLVED, with no positive source evidence; exclude it.** The player has a proven flame-sword table,
but no inspected warrior selector reaches it and no known `$033E` code overlaps it. Tighe also does not
recall a warrior using it. Andy must not expose Flame Sword as an eligible warrior weapon unless an original
arcade selector/writer or a captured owning warrior record proves that path.

## Floor Spikes

**UNRESOLVED identity.** Andy's current Bestiary/hazard census correctly records `floor_spears` as pending:
it has not pinned a marker, actor state, graphics base, animation table, or palette bank. The screenshots
show multiple raised/lowered visual frames, but appearance alone cannot decide whether they are an actor,
PC080SN tile replacement, or mixed collision/visual state.

Do not equate these with the `$0DAB` torch/light transform or with generic state `$1E/$20` merely because
those handlers were earlier listed as candidates. Suggested eventual semantic name:
`object:hazard.r1s2.floor_spikes`, status disabled/unresolved. Smallest missing evidence: correlate one
ORIGINAL ARCADE screenshot position to its record-16..21 world cell, then capture writes to that cell and
the collision word while the spikes cycle. That single capture distinguishes PC080SN versus PC090OJ and
reveals all selected tile/program frames and banks.

## Wooden Moving Door / Gate

**UNRESOLVED identity.** The screenshot-visible yellow/green moving wooden gate is not source-proven to be
the stage-transition door. The only proven generic “door” fact in the Bestiary is collision type `$7E` ->
`A5+$10E8=7` -> screen wipe (`$53F0C/$54038`); it has no proven graphics identity and must not be reused as
the moving-gate name.

Suggested eventual name: `object:hazard.r1s2.moving_wood_gate`. Its movement frames, codes, bank, and
reuse are presently unresolved. The same world-cell/write capture described for floor spikes is the
smallest evidence. If the object proves to be PC090OJ instead, capture the owning actor record and emitted
pieces. Do not choose a Genesis destination mapping from the screenshot colors.

## Spiked Traps

**UNRESOLVED and kept separate from floor spikes.** The current hazard census separately tracks rising
floor spears and stalagmite/rising-spike candidates, but neither has a pinned original owner. Screenshot
traps suspended/moving above the floor must therefore remain a separate prospective semantic family
`object:hazard.r1s2.moving_spiked_trap`; do not merge it with `floor_spikes` or the moving gate.

Minimum proof is one owning-cell/actor capture through a complete motion cycle. Required output is: original
state writer, all programs or tile codes, embedded/source banks, collision coupling, and whether multiple
trap geometries share one state table.

## Falling-Water Trap

**UNRESOLVED for the R1-S2 screenshot object.** A different mechanism is already proven for the R1-S1
outdoor waterfall: original `$59AD4`, type-9 counter at `A5+$12EA`, four frames every eight ticks, palette
banks `$1A-$1D`, cycling indices 14/15. That evidence must **not** be assigned to the R1-S2 falling-water
trap without a source link.

The R1-S2 object could be tile animation, palette cycling, sprite composition, or a combination; current
durable evidence does not decide it. Suggested eventual semantic unit:
`object:hazard.r1s2.falling_water`, with separate subparts only if the capture proves falling column and
pool/splash use different palette resources. Minimum proof: record the relevant PC080SN cell writes and
palette writes for one full cycle and follow their caller/table in the original program.

## Animated Pit Flames

**UNRESOLVED for the screenshot pit animation.** Static orange window/lava scenery and animated foreground
flame tongues must remain separate prospective contexts. Neither the torch's 90-frame table at `$40FE0`
nor the R1-S1 waterfall palette cycle proves the R1-S2 pit mechanism.

Suggested names: `scene:r1s2.pit_lava_static` and `object:hazard.r1s2.pit_flame_animation`. Minimum proof is
one full-cycle PC080SN/PC090OJ/palette-write capture tied back to the original caller and frame table. If
only CRAM entries change, Andy should expose one graphics object plus a palette-animation state, not fake
multiple graphics frames.

## Shared Graphics / Effective-Bank Conflicts

1. **PROVEN:** the newly discovered state-`$1F` codes add 32 patterns and are absent from the current
   green-warrior coverage. Leaving them out guarantees raw/fallback colors when those actions display.
2. **PROVEN:** normal/state-`$1F` program defaults are multi-bank: sword `$33`, body `$37`. Reaction
   `$71-$73` defaults to `$3C`; airborne to `$37`; rope-sheet frames to `$30/$34/$39`. **Also proven:**
   the preserved R1 `$44/$41` actor attributes override all piece defaults to `$34/$31`. A preview that
   deletes either the embedded nibble or actor override is not proof of runtime bank identity.
3. **PROVEN:** Rastan's player weapon code sets do not overlap the 29-program warrior code set. Share the
   weapon-type taxonomy, not a global code recolor or one player object mapping.
4. **UNRESOLVED:** whether future proven hammer/axe warrior variants reuse any player patterns. If the same
   `(code,effective-bank)` later needs two different index maps, the current identity is insufficient and
   must gain a semantic variant key; never let last-writer/global recoloring decide it.
5. **PROVEN corpus boundary:** the R1-S2 Plane-A corpus covers records 16-21 with 520 distinct
   `(tile_code,palette_bank,flip)` usages and 24,576 map cells, across banks
   `03,08-14,1F` (hex, with gaps exactly as the corpus records). It is valid scene-wide authoring evidence,
   but it does not label which subset is a spike, gate, water, or flame. Do not manufacture those subsets.

## Palette Composer Implementation Requirements for Andy

1. Correct the green-warrior completeness claim: add the source/runtime-proven `$97-$9C` and `$A1-$A6`
   groups to the existing object. The complete known union is 29 programs / 109 codes.
2. Show pose groups and representative previews, but apply coverage to every listed production code.
3. Label `$71-$73` “short reaction/effect (crouch visual pending)” until runtime semantics are proven;
   exclude `$74` from the warrior.
4. Label state `$1F` sequences as “low/weapon action A/B” until the precise crouch/attack names and the
   meaning of `+$21 bit2` are proven.
5. Preserve both per-piece default nibbles and the actor `+$27` bit-6 override in evidence and previews.
   Do not use a stripped single green line as the runtime provenance model. Surface the existing
   registry-bank-`$33` versus observed-attribute-`$34/$31` conflict for resolution; do not silently choose.
6. Treat the embedded sword as a warrior sub-context. Keep player sword/axe/hammer/flame-sword objects
   untouched.
7. Do not expose hammer, axe, or flame sword as proven warrior variants until the missing original capture
   identifies their selector and codes. Flame sword remains excluded.
8. Keep floor spikes, moving wooden gate, moving spiked traps, falling water, static pit lava, and animated
   pit flame as separate semantic candidates. Do not assign codes or palettes merely from screenshots.
9. Reuse the existing R1-S2 scene corpus and original palette data once a world-cell correlation identifies
   a hazard subset. Do not create a second palette registry; any eventual mapping decision belongs only in
   `specs/palette_decisions.json` and requires Tighe's decision.
10. Do not change production ROM code as part of the Composer update. The tool should export semantic
    evidence/mappings for later production integration.

## Unresolved Evidence

- Exact gameplay labels for normal `$93-$96` phases (idle versus individual walk/turn frames).
- Exact human semantics of state `$1F` and `actor+$21 bit2`; source and runtime prove both sequences display,
  but do not name them.
- Whether `$71-$73` is the duck pose Tighe observed or a separate short reaction/effect.
- Original selector/graphics for warrior hammer and axe; no positive warrior Flame Sword path.
- Object owner, code/frame table, palette bank, and mechanism for every requested R1-S2 trap/hazard.

The smallest next evidence action is **one reusable ORIGINAL ARCADE capture**, not separate probes: at a
user-marked frame, record active actor records plus emitted PC090OJ records, and record PC080SN cell/CRAM
writes with world coordinates. Mark frames for (a) duck/weapon variant, and (b) one complete cycle of each
trap. That resolves actor versus tilemap ownership first; only then follow the observed writer/table in the
existing Ghidra/decompilation workflow.

## Exact Andy Handoff

Implement the Composer-side correction only after reading this report:

- immediately add the **proven missing state-`$1F` programs** `$97-$9C,$A1-$A6` and their 32 new codes to
  `object:castle.green_sword_knight` coverage;
- preserve the original per-piece defaults **and** the observed `$44/$41` actor override instead of
  treating `$33` as universal;
- keep `$71-$73` and state-`$1F` labels honest, and keep `$74` out;
- provide sword representatives `$93,$A3,$A6,$99,$9C` while covering all underlying codes;
- do **not** implement warrior hammer, axe, or flame sword from the current evidence;
- do **not** fabricate named trap subsets from the scene-wide Plane-A corpus. First obtain the one combined
  original-arcade owner/write capture described above, then bind codes/banks to separate semantic objects;
- do not alter Tighe's existing `Test.json` mapping or `PAL-PC090OJ-R1S2-GREEN-SWORD-KNIGHT-001` while
  merely extending proven pose coverage.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0080
