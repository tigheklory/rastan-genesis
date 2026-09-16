# Cody R1/P1 Targeted Arcade Sprite Semantic Hooks

## Method and address discipline

This is a targeted static pass over the canonical original-arcade Ghidra exports. Every current
runtime address below was resolved through `build/rastan-direct/address_map.json`; no fixed offset
was assumed. `arcade_copy` means the listed arcade instruction is currently copied at that runtime
location. `patched_site` means the semantic site has a generated replacement segment and the
listed runtime start is the mapped current site.

No Ghidra project, export, source, ROM, or build was changed.

## Semantic-event map

| Semantic event | Original arcade PC | Containing function / state | Trigger or proof status | Current runtime Genesis PC / map proof | Future Genesis owner |
|---|---:|---|---|---:|---|
| PHASE_EXIT | **UNRESOLVED** | Candidate progression chain `FUN_000558a2 -> FUN_000558e0`; `A5+0x10CA/0x10CC/0x10C6/0x013E` | `0x0558E0` advances progression, but is not proven to be phase exit | candidate `0x0559C0`, `arcade_copy` | phase context compiler/loader |
| PHASE_SPRITE_CONTEXT_REPLACE_SAFE | **UNRESOLVED / DISTRIBUTED** | actor-block and special-pair reset sequence not isolated | no point yet proves all prior actors dead | n/a | phase context loader |
| PHASE_GAMEPLAY_START | **UNRESOLVED** | new phase dispatcher not isolated | requires ordered reset/start proof | n/a | copied gameplay dispatcher plus context loader |
| HURRYUP_TIMER_TRIGGER | **UNRESOLVED** | timer/state unknown | natural codes `0x0268..0x026A` do not identify the requesting timer | n/a | copied semantic trigger |
| HURRYUP_BAT_SPAWN | **UNRESOLVED** | Small-Bat-family creation path not separated from normal spawn | exact caller and maximum live count unknown | n/a | generated Small-Bat package selector |
| HURRYUP_STATE_RESET | **UNRESOLVED** | progress-sensitive reset unknown | no exact writer proved | n/a | copied semantic reset |
| FLYING_DEMON_PRELOAD_POINT | **UNRESOLVED** | calls preceding paired init at `0x045FAC/0x045FE4/0x046124` | present exports do not identify the two encounter table entries | mapped callers require event classification first | encounter package loader |
| FLYING_DEMON_SPAWN_COMMITTED | **CANDIDATE `0x045342`** | `paired_actor_init_45342`; fixed slots around `A5+0x0508/0x0548`, variant `A5+0x0C5A` | initializes both members only when `A5+0x0548` inactive; demon identity not fully proved | `0x045542`, `arcade_copy` | copied trigger plus native package selection |
| FLYING_DEMON_ACTIVE | **CANDIDATE `0x0453A2`** | `paired_actor_activate_453a2`; actor `A4`, loader `0x04543E` | writes timer `+0x1C=1`, active `+0=1`, mode `+5=3`, Y `+0x1A=0x180`, then loads record | `0x0455A2`, `arcade_copy`; loader `0x04563E`, `arcade_copy` | native semantic actor state |
| FLYING_DEMON_RESIDENCY_RELEASE_SAFE | **UNRESOLVED** | paired body/wings cleanup | neither joint nor independent retirement is proved | n/a | encounter package lifetime owner |
| RECURRING_SPAWN_WINDOW_ENTER | **PARTIAL `0x041180`** | `actor_spawn_ground_and_activate_41180`; `A4+0x1C/+0x30/+3/+0x0D`, `A5+0x013E/+0x0118/+0x10CC`, camera/collision marker | exact marker/progression eligibility differs by class; family table decode incomplete | `0x041380`, `arcade_copy` | copied scheduler selecting generated family context |
| RECURRING_SPAWN_WINDOW_EXIT | **UNRESOLVED** | same scheduler plus actor retirement | spawn eligibility end is not active-actor retirement | n/a | generated context lifetime logic |
| PLAYER_GRAPHICS_FRAME_SELECTED | `0x054326` | `FUN_00054326`; mode `A5+0x10E8`, animation `+0x10EA/+0x12F2/+0x12F4`, attack `+0x1108/+0x1116/+0x110A`, frame outputs `+0x1244/+0x1246` | exact selection path; calls body/weapon expansion `0x054492` and secondary expansion `0x0546A8` | `0x05446E`, `arcade_copy`; expansion `0x0545DA`, `patched_site` | generated frame-map selector |
| DEMON_BODY_GRAPHICS_FRAME_SELECTED | **UNRESOLVED** | paired actor state/mapping table not decoded | no exact animation-to-piece selector proved | n/a | generated demon body frame map |
| DEMON_WINGS_GRAPHICS_FRAME_SELECTED | **UNRESOLVED** | paired actor state/mapping table not decoded | no exact animation-to-piece selector proved | n/a | generated demon wings frame map |
| LIZARDMAN_GRAPHICS_FRAME_SELECTED | **UNRESOLVED** | material recurring actor mapping chain | family identity and tables incomplete | n/a | generated Lizardman frame map |
| LARGE_BAT_GRAPHICS_FRAME_SELECTED | **UNRESOLVED** | material recurring actor mapping chain | ordinary versus hurry-up producer separation incomplete | n/a | generated Large-Bat frame map |
| FOUR_ARMED_INSECT_GRAPHICS_FRAME_SELECTED | **UNRESOLVED** | material recurring actor mapping chain | table incomplete | n/a | generated insect frame map |
| CHIMERA_GRAPHICS_FRAME_SELECTED | **UNRESOLVED** | material recurring actor mapping chain | table incomplete | n/a | generated Chimera frame map |
| VALKYRIE_GRAPHICS_FRAME_SELECTED | **UNRESOLVED** | material recurring actor mapping chain | table incomplete | n/a | generated Valkyrie frame map |

## Proven targeted paths

### Recurring scheduler

`actor_spawn_ground_and_activate_41180` at `arcade_pc 0x041180` maps to
`runtime_genesis_pc 0x041380` in an `arcade_copy` segment. It decrements actor-local
`A4+0x1C`, reloads it to 2, calls `actor_surface_marker_find_41064`, evaluates actor flags,
camera/player coordinates, progression `A5+0x013E`, stage/subphase `A5+0x0118`, and
`A5+0x10CC`, then scans collision markers and activates an actor. This proves that eligibility
is semantic state plus marker/camera driven. It does not prove one phase-wide window for each
named family, nor that graphics can be released when a marker window closes.

### Paired actor initializer

`paired_actor_init_45342` at `arcade_pc 0x045342` maps to
`runtime_genesis_pc 0x045542` (`arcade_copy`). It guards on `A5+0x0548 == 0`, selects pair
types 8 or 9 from `A5+0x0C5A`, marks both halves, and calls activation twice.
`paired_actor_activate_453a2` at `arcade_pc 0x0453A2` maps to
`runtime_genesis_pc 0x0455A2`; it makes each actor active and calls
`actor_record_loader_4543e` (`0x04543E -> 0x04563E`). Calls to the initializer exist at
`0x045FAC`, `0x045FE4`, and `0x046124`, but their containing semantic function is fragmented in
the current export. This is strong structural evidence for a paired special actor, not sufficient
proof that any particular caller is encounter 1 or 2 of Flying Demon.

### Progression increment is not a reset hook

`FUN_000558a2` at `arcade_pc 0x0558A2` maps to `runtime_genesis_pc 0x055982`. Under
`A5+0x10CA == 4`, it advances `A5+0x10CC`; at 16 it calls `FUN_000558e0`.
`FUN_000558e0` (`0x0558E0 -> 0x0559C0`) clears `+0x10CC`, increments the long pointer/state
at `+0x10C6`, copies `+0x10A8` to `+0x132C`, writes the selected byte to arcade WRAM
`0x10D0A8`, and increments progression `+0x013E` at `arcade_pc 0x0558FE`
(`runtime_genesis_pc 0x0559DE`, patched site). This proves a progression event, but not the
ordered actor wipe, package replacement-safe point, or gameplay restart.

### Player animation to pieces

`player_body_constructor_540cc` maps `0x0540CC -> 0x054236` (patched site). Mode 7 clears
the player piece lists; other modes call `FUN_00054326` (`0x054326 -> 0x05446E`). The latter
selects body and secondary frame IDs from mode, attack, weapon selector, and animation indices,
storing them at `A5+0x1244/0x1246`. `FUN_00054492` (`0x054492 -> 0x0545DA`, patched site)
uses a 16-bit offset table rooted around `0x05BD40`, expands four six-byte body descriptors into
`0x10D1D2`, and selects weapon tables at `0x05CD8A`, `0x05D068`, `0x05D346`, or `0x05D666`
to expand four descriptors into `0x10D1B2`. Coordinates, flip-dependent attributes, and dynamic
weapon-code substitutions remain semantic inputs. This is enough to define the future player
compiler shape, but not enough to emit a complete generated map until all table entries and
weapon states are extracted and cross-checked.

## Exact unresolved boundary

The requested implementation hooks are not yet complete. Targeted Ghidra work still must repair
or identify only these concrete boundaries:

1. the dispatcher containing the `0x045FAC/0x045FE4/0x046124` calls and its encounter-table data;
2. paired actor death/retirement readers and writers;
3. the hurry-up request timer, threshold, spawn call, reset writer, and actor-slot bound;
4. the distributed phase transition's old-actor invalidation and new-gameplay start sequence;
5. each material recurring family's table identity and animation/frame/piece chain.

Until those are proved, there is no legal encounter overlay, recurring-family alias, exact DPLC
reservation, or generated aggregate DMA bound. This report intentionally records UNKNOWN rather
than converting plausible structural correspondence into a production hook.

