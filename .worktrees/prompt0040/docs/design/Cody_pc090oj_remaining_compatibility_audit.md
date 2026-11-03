# Cody - Current PC090OJ Compatibility Audit / Removal Plan

## BUILD0282 BASELINE

**PROVEN**

- Accepted baseline: Build 0282.
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0282.bin`.
- SHA-256: `61b2b1268362f309c64939c1a6d226df5a4a26a95f95b560071701266d694316`.
- Size: 1,590,912 bytes.
- Build counter: 282.
- `apps/rastan-direct/out/pc090oj_config.inc` sets
  `RASTAN_GAMEPLAY_HUD_SPRITES=0`.
- No ROM was built and no production source, remap, specification, or generated
  artifact was changed for this audit.

The current source, current symbols, `specs/rastan_direct_remap.json`, and
`build/rastan-direct/address_map.json` are authoritative. Historical reports
were used only as provenance. In particular, old reports which describe the
`0x41DAE`, `0x41F5E`, or `0x45DFA` non-gameplay branches as object-table
publishers are superseded by the current immediate `rts` branches in
`pc090oj_hooks.s`.

The accepted Build 0282 collision grounding, actor logical Y, sword rendering,
Build 0280 auxiliary-array correction, player movement, and shift-aware
relocation are outside this audit and remain unchanged.

## GAMEPLAY ARCHITECTURE PROOF

### Scene identity

**PROVEN:** `load_scene_tiles` records the physical tileset ID separately. It
normalizes physical cave tileset 3 to logical scene 1 before writing
`genesistan_current_scene_id` (`scene_load.s:85-95`). Outdoor and cave gameplay
therefore take the same sprite architecture branch.

### Gameplay control path

**PROVEN:** the current gameplay path is:

```text
retained arcade semantic actor/player state
  -> native_stage_dispatch_41dae / native_stage_dispatch_45dfa
     and native main-loop PLAYER_FRONT / PLAYER_BODY staging
  -> native_sprite_emit
  -> one of six native {attr,Y,code,X} queues
  -> pc090oj_native_emit_pass::.Lnq_gameplay
  -> .Lnq_emit_lane / .Lnq_emit_entry
  -> staged_sprite_sat or staged_sprite_sat_b (Genesis SAT words)
  -> vdp_commit_sprites_vram
  -> Genesis VDP tile DMA and SAT DMA
```

Evidence:

- `genesistan_pc090oj_hook_target_41f5e` starts the native frame only for
  logical scene 1 (`pc090oj_hooks.s:359-365`).
- `genesistan_pc090oj_hook_target_41dae` and
  `genesistan_pc090oj_hook_target_45dfa` dispatch native families and invoke
  the native finalizer only for logical scene 1 (`pc090oj_hooks.s:343-374`).
- `pc090oj_native_emit_pass` branches scene 1 directly to `.Lnq_gameplay`
  (`pc090oj_hooks.s:1391-1403`).
- `.Lnq_gameplay` reads only native queue bases and counts; it does not read
  `pc090oj_object_ram` (`pc090oj_hooks.s:1593-1629`).
- `vdp_prepare_sprites` calls the same finalizer only when a producer has not
  already made a frame ready; VBlank then commits tile work and the completed
  SAT bank (`pc090oj_hooks.s:2264-2287`).

**DISPROVEN:** gameplay rendering does not follow
`semantic producer -> PC090OJ record -> object-RAM scanner -> decoder -> SAT`.
The frontend scanner at `.Lnq_frontend_object_scan` is unreachable from the
scene-1 branch.

### Gameplay producer families

| Gameplay producer family | Current output representation | Native direct? | Legacy write still has an executable route? | Gameplay legacy consumer? |
|---|---|---:|---:|---:|
| HUD lane | Native `{attr,Y,code,X}` queue; HUD disabled by current mode 0 unless a native producer contributes | YES | Some old fixed-record maintenance remains | NO |
| Front effects | `native_queue_front_effect` | YES | Shared/state-gated old record tails remain | NO |
| PLAYER_FRONT | `native_queue_player_front` from corrected main-loop semantic state | YES | `0x59F5E` still clears compatibility records 9-16 | NO |
| Middle actors/items | `native_queue_middle` | YES | Descriptor-style compatibility helpers remain reachable by retained callers | NO |
| PLAYER_BODY | `native_queue_player_body` from main-loop semantic state | YES | `0x54052` still initializes compatibility records 72-75 | NO |
| Back enemies, including lizard men and bats | `native_queue_back_enemy` | YES | No enemy-population object-table scan or decode feeds the gameplay SAT | NO |

**PROVEN:** legacy writers that execute in scene-1 setup or state-gated shared
paths produce a **DEAD HARDWARE-OUTPUT TAIL**. Their writes cannot reach the
gameplay SAT because the scene-1 finalizer consumes only native queues.

**PROVEN static reachability, not dynamic frequency:** the following twelve
compatibility writer identities have retained scene-1/transition-capable call
routes or shared initialization routes: the PC090OJ branch of `0x03AD44`,
`0x03AD84`, `0x03B926`, `0x054052`, `0x059F5E`, `0x054810`, `0x05607C`,
`0x056114`, `0x056440`, `0x05A098`, `0x05A502`, and copied raw writer
`0x052AA2`. Their exact dynamic hit count in a Build 0282 play session is not
claimed because this task forbids MAME.

## EXECUTABLE COMPATIBILITY INVENTORY

| Component/function | Executable? | Caller/route | Scene(s) | What it actually does | Compatibility machinery? |
|---|---:|---|---|---|---:|
| `.Lpc090oj_emit_slot` / `.Lpc090oj_clear_slot` | YES | Called by the retained helper families below | Shared setup/frontend; some gameplay dead tails | Packs or parks an 8-byte PC090OJ-format record in `pc090oj_object_ram` | YES |
| `.Lpc090oj_mirror_write_word_a1_d0` | Linked; current live caller not established | Generic `0x03B930` body only in current source | None proven | Translates HW_ADDRESS `0xD00000..0xD007FF` into virtual-table offsets | YES |
| `.Lpc090oj_mirror_write_byte_a1_d0` | Linked; no executable caller | Former `0x03B802` path is now `rts` | None | Byte form of the same hardware-address adapter | YES, dead body |
| `genesistan_pc090oj_hook_target_3b902` | YES boundary, no record output | Eight retained frontend callers may enter it | Frontend | Immediate return; credit records 17-21 are natively owned | NO active compatibility output |
| `genesistan_pc090oj_hook_target_3b926` | YES | arcade_pc `0x03A9C6` and `0x03A9D4` callers | Setup/transition | Parks records 5-13 through the virtual table | YES |
| `genesistan_pc090oj_hook_target_3b930` | Linked, no current executable caller | Former callers `0x03B8B0` and `0x03B902` are retired | None proven | Generic packed-byte source to PC090OJ record copier | YES, dead body |
| `genesistan_pc090oj_hook_target_41dae` | YES | arcade dispatcher | Gameplay only; non-gameplay returns | Native family dispatch plus one finalizer | NO |
| `genesistan_pc090oj_hook_target_41f5e` | YES | arcade dispatcher | Gameplay only; non-gameplay returns | Starts one native queue frame | NO |
| `genesistan_pc090oj_hook_target_45dfa` | YES | arcade dispatcher | Gameplay only; non-gameplay returns | Native alternate family dispatch plus finalizer | NO |
| `genesistan_pc090oj_hook_target_59f5e` | YES | arcade_pc `0x051266` | Shared player lifecycle | Parks compatibility records 9-16; retired PLAYER_FRONT tuple rebuild is absent | YES |
| PC090OJ control setters | YES | Replacements for original control writes | All applicable scenes | Capture global flip and sprite colbank semantic latches | NO final-device emulation; semantic state |
| PC090OJ branch of `genesistan_hook_3ad44_dispatch` | YES | Original long-fill callers | Setup/transition | Converts a `0xD00000..0xD007FF` destination into a virtual-table fill | YES |
| Tilemap branches of `genesistan_hook_3ad44_dispatch` | YES | Original long-fill callers | PC080SN paths | Dispatches PC080SN name/scroll fills | NO PC090OJ debt; preserve |
| `genesistan_pc090oj_hook_init_priority_3ad84` | YES | Original initialization control flow | Setup/transition | Emits records 76-79 | YES |
| `genesistan_pc090oj_hook_score_digit_3b802` | YES boundary, no output | Retained score call sites | Frontend/gameplay HUD semantics | Immediate return; score/credit digits have native owners | NO active compatibility output |
| `genesistan_pc090oj_hook_slot_init_54052` | YES | arcade_pc `0x051260` | Player setup/shared | Emits compatibility records 72-75 | YES |
| `genesistan_pc090oj_hook_sprite_update_54810` | YES | arcade_pc `0x0547EE` and `0x054804` | Player auxiliary update | Uses original table/state to pack records 44-47 | YES; dead in gameplay, potentially live in frontend fallback |
| `genesistan_pc090oj_hook_sprite_decay_5607c` | YES | arcade_pc `0x055E92` | Shared transient effects | Mutates a descriptor-shaped compatibility alias and emits records 56-63 | YES |
| `genesistan_pc090oj_hook_copy_56114` | YES | arcade_pc `0x05604C` and `0x056076` | Shared transient effects | Copies up to four tuples to records 64-67 | YES |
| `genesistan_pc090oj_hook_zero_fill_56440` | YES | arcade_pc `0x055F0E` and `0x055FFA` | Shared transient effects | Parks records 68-71 | YES |
| `genesistan_pc090oj_hook_status_sprite_5a098` | YES | arcade_pc `0x051054` | Shared status/setup states | Emits fixed records 30-43 | YES |
| Audit guard replacing `0x0510EA/0x0510F4` | YES if reached | Original raw `0xD00698` sites | Shared exceptional path | Captures state and halts instead of writing raw hardware | Diagnostic, not a renderer |
| Redirected `0x05A502` family | YES | arcade_pc `0x05104E` | Frontend/shared setup | Writes records 83-90 to `pc090oj_object_ram + 0x298/+0x2B0` | YES; live mapped compatibility producer |
| Copied `FUN_00052AA2` | YES, state-gated | `player_main_update_51090 -> 0x052732 -> 0x052A64 -> 0x052AA2` | Player state path | Writes PC090OJ records 0-3 directly to HW_ADDRESS `0x00D00000` | YES; dead output and latent strict-target hazard |
| Copied arcade_pc `0x0510C8` raw routine | No executable caller found | No Ghidra xref/caller | None | Loads `0x00D00000`, writes a record, then loops | YES, but no current route |
| `.Lnq_frontend_object_scan` | YES | `pc090oj_native_emit_pass` for scene != 1 except active title state | Frontend/non-gameplay | Scans 256 virtual PC090OJ records, performs residency, and builds native SAT | YES |
| `.Lpc090oj_decode_record` | YES | Frontend scanner | Frontend/non-gameplay | Decodes PC090OJ word format, clipping, flips, code, and colbank | YES |
| Native SAT builder, tile worklist, palette fixup, and commit | YES | Native gameplay/title paths and compatibility frontend scan | All rendered scenes | Produces and commits Genesis-native SAT/pattern output | NO; retain |

The comment above `pc090oj_object_ram` calls it “arcade state.” Under the current
canonical native-replacement policy, that characterization is **DISPROVEN as a
final-architecture classification**: the table is laid out as 256 PC090OJ
hardware records and is scanned/decoded as such. Original tuple values inside
it remain useful semantics, but the virtual chip-shaped container does not.

## FRONTEND / NON-GAMEPLAY PRODUCERS

### Current scene routing

**PROVEN:**

- Logical scene 1, including cave, uses only native gameplay queues.
- Logical scene 0 with `Genesis-WRAM 0xFF0118 == 0` uses the direct-native title
  HUD branch `.Lnq_title` and does not scan object RAM.
- Logical scene 0 after that state advances, and every logical scene other than
  0 or 1, uses `.Lnq_frontend_object_scan`.
- `native_frontend_hud_emit` directly owns scores, credit, and fixed HUD labels
  in every frontend scanner invocation. The old `0x03B8B0`, `0x03B902`, and
  `0x03B802` HUD record tails are retired.

**HYPOTHESIS bounded by route evidence:** title substates, story/throne,
high-score, credits, continue/game-over, round/transition screens, and attract
subscreens which satisfy the non-gameplay branch can display remaining
compatibility records. This audit proves the route, not that every listed
producer is visible on every named screen; runtime per-screen population was
not requested or permitted.

### Remaining producer families

| Producer family | Scene(s) | Arcade semantic entry/cut point | Legacy hardware tail | Legacy consumer | Native replacement complexity |
|---|---|---|---|---|---|
| Status row records 30-43 | Shared/frontend status states | arcade_pc `0x05A098`: state-derived status decision before record packing | `.Lpc090oj_emit_slot` loop | Frontend scanner/decoder | LOW: fixed bounded family and one replacement boundary |
| Player auxiliary records 44-47 | Shared player/frontend states; dead output in gameplay | arcade_pc `0x054810`: original table selection plus player X/Y before destination packing | Four PC090OJ records; related copied `0x052AA2` writes records 0-3 raw | Frontend scanner where populated; none in gameplay | MEDIUM: unify retained semantic table/state with existing native player lanes and prove substate coverage |
| Transient descriptor family 56-63 | Shared effect states | arcade_pc `0x05607C`: active/timer tuple before record encoding | Descriptor mutation plus eight virtual records | Frontend scanner | HIGH: current helper mixes timer/state mutation with a stale descriptor-shaped alias |
| Transient copy family 64-67 | Shared effect states | arcade_pc `0x056114`: input tuple stream at A0 | Copies four PC090OJ records | Frontend scanner | MEDIUM: bounded stream but all callers/states need native ownership |
| Transient clear family 68-71 | Shared effect lifecycle | arcade_pc `0x056440`: semantic lifecycle event before hardware clearing | PC090OJ park records | Frontend scanner state retirement | LOW after the 56-67 native family exists |
| Slot-init family 72-75 | Player/setup transitions | arcade_pc `0x054052`: setup state after retired PLAYER_BODY initialization | Four PC090OJ records | Frontend scanner if nonzero later | LOW: currently initialized blank, but lifecycle dependencies must be verified |
| Priority/init family 76-79 | Setup/transition | arcade_pc `0x03AD84`: priority/flip semantic inputs before record layout | Four PC090OJ priority records | Frontend scanner | MEDIUM: preserve ordering intent directly in native lane order |
| Fixed/shared records 83-90 | Attract/frontend/shared setup | arcade_pc `0x05A502` before the two destination immediates at `0x05A51E` and `0x05A554` | Record writes redirected to virtual offsets `0x298` and `0x2B0` | Frontend scanner | LOW/MEDIUM: bounded family; identify direct semantic tuples and emit natively |
| Generic bulk clear/park maintenance (infrastructure, not a producer family) | Setup/transitions | Original lifecycle decision before `0x03AD44`, `0x03B926`, and `0x059F5E` | Hardware-address fill or record park | Only meaningful while other compatibility producers remain | LOW, but delete only after affected native families own retirement |

This yields eight live or executable compatibility producer-family groups,
plus shared clear/park maintenance. Neither that maintenance nor the generic
scanner is counted as another semantic producer; they are infrastructure used
by the eight groups.

## pc090oj_* STATE CLASSIFICATION

Classification is by behavior, not name.

| State/symbol | Class | Current writers | Current readers | Scope and removal decision |
|---|---|---|---|---|
| `pc090oj_object_ram` | **A. LEGACY HARDWARE-COMPATIBILITY STATE** | Boot clear, emit/clear/mirror helpers, `0x03AD44` branch, redirected `0x05A502` | Frontend scanner and decoder | Required until the final non-gameplay record producer is native; then delete |
| `pc090oj_mirror_dirty`, candidate/decoded/skip/drawable/represented/bootstrap/scan counters and flags | **A** | Mostly boot clear; a subset is diagnostic or historical | No current rendering decision depends on most of them | Remove by xref after producer conversion; do not confuse with native frame-ready state |
| `pc090oj_candidate_bitset`, `record_to_slot`, `represented_records`, `waiting_records`, `used_sat_slots` | **A** | No current functional writers | No current functional readers | Exported aliases are dead compatibility names; remove after separating the live alias below |
| `staged_sprite_descriptor_table` | **A** | No valid 12-byte table allocation is established | Compatibility decay helper `0x05607C` | Replace the 56-63 producer first; then remove this alias |
| `pc090oj_producer_write_count`, `pc090oj_producer_oob_count` | **A** | Legacy producer adapters | Diagnostics only | Delete with the adapters they measure |
| `staged_sprite_sat`, `staged_sprite_sat_b` | **B. NATIVE GENESIS STAGING WITH HISTORICAL NAME** | Native gameplay/title finalizer and frontend compatibility scanner | VBlank commit | Keep; these are final Genesis SAT double buffers |
| `pc090oj_sat_bank`, `pc090oj_sat_front`, `pc090oj_sat_frame_ready` | **B** | Native finalizer/commit | Native finalizer/commit | Keep; native double-buffer ownership and publish handshake |
| `pc090oj_sat_nibble` | **B** | Native and compatibility SAT builders | Commit-time native palette fixup | Keep; it carries arcade palette semantics to final Genesis CRAM-line selection |
| `pc090oj_sat_force_line` | **B** | Build-mode-2 code only | Build-mode-2 palette fixup only | Current Build 0282 mode 0 compiles no functional use; audit build variants before deleting |
| `pc090oj_cell_used`, `sprite_tile_resident_code` | **B** | Native and frontend SAT builders | Native residency selection | Keep; native Genesis tile-residency state |
| `pc090oj_tile_dma_worklist`, `pc090oj_tile_dma_count` | **B** | Native and frontend SAT builders | VBlank tile DMA | Keep; native Genesis work queue |
| `worklist_entry_for_slot` | **B** | VBlank reset writes | VBlank tile-reservation reset | Keep its required storage. It aliases several dead A-class names, so alias deletion must not delete this live backing state |
| Native queues, native lane/counts | **B** | Native gameplay semantic producers | `.Lnq_gameplay` | Keep; this is the target architecture |
| `pc090oj_emitted_count`, `pc090oj_dropped_count` | **B** | Native and compatibility finalizers | Native palette fixup/diagnostics | Keep emitted count; dropped count may be removed only after independent diagnostic review |
| `pc090oj_sat_dirty` | **B** | Finalizers and commit | No functional reader found | Historically named native staging residue; safe-removal candidate only after a focused xref proof |
| `pc090oj_ctrl_shadow` | **D. ORIGINAL ARCADE SEMANTIC STATE STILL REQUIRED** | Original PC090OJ control-write replacements | Native emitter and compatibility decoder | Preserve global-flip semantics; eventually rename away from the chip name |
| `pc090oj_sprite_ctrl_shadow` | **D** | Original sprite-control/colbank replacements | Native commit palette fixup and compatibility decoder | Preserve colbank semantics; eventually rename |

**C. TEMPORARY BRIDGE:** no independent `pc090oj_*` state object qualifies as a
healthy final temporary bridge. The producer hooks are transitional code, but
their shared table is A-class legacy state. Native tuple queues are B-class,
not bridges.

## 0xD00000 / HARDWARE-WRITE AUDIT

All PC correlations below are JSON-derived from
`build/rastan-direct/address_map.json`; no arithmetic offset is used as proof.

| Arcade identity | runtime_genesis_pc | Current classification | Evidence/result |
|---|---:|---|---|
| arcade_pc `0x03AD44` | `0x0003AF44` | Still required by a live compatibility path for D-range input; other branches are PC080SN | Patched dispatcher translates D-range fills into `pc090oj_object_ram`; C-range branches must remain |
| arcade_pc `0x03AD84` | `0x0003AF84` | Still required by compatibility | Patched priority-record producer emits virtual records 76-79 |
| arcade_pc `0x03B902` | `0x0003BB02` | Replaced by direct native output | Current helper returns; native frontend HUD owns the family |
| arcade_pc `0x03B926` | `0x0003BB26` | Still executes, output is compatibility/dead in gameplay | Parks records 5-13 |
| arcade_pc `0x03B930` | `0x0003BB30` | No executable route found | Body remains linked, but its two producer callers are retired |
| arcade_pc `0x041DAE` | `0x00041FAE` | Replaced by direct native output | Gameplay dispatch/finalize; non-gameplay return |
| arcade_pc `0x041F5E` | `0x0004215E` | Replaced by direct native output | Gameplay frame begin; non-gameplay return |
| arcade_pc `0x045DFA` | `0x00045FFA` | Replaced by direct native output | Gameplay alternate dispatch/finalize; non-gameplay return |
| arcade_pc `0x0510C8` | `0x000512CE` | No executable route found | Copied raw writer body has no current caller |
| arcade_pc `0x0510EA` | `0x000512F0` | Replaced by audit guard | Original `move.w #2,0x00D00698` does not execute as a raw write |
| arcade_pc `0x0510F4` | `0x000512FA` | Replaced by audit guard | Original clear of `0x00D00698` does not execute as a raw write |
| arcade_pc `0x052AA2` | `0x00052CA2` | Still executes on a state-gated route, but output is dead | Copied `movea.l #0x00D00000,a1`; native gameplay does not consume it |
| arcade_pc `0x054052` | `0x00054252` | Still required by compatibility lifecycle | Replacement writes virtual records 72-75 |
| arcade_pc `0x054810` | `0x000549C6` | Still required by compatibility/dead gameplay tail | Replacement writes virtual records 44-47 |
| arcade_pc `0x05607C` | `0x00056232` | Still required by compatibility | Replacement writes virtual records 56-63 |
| arcade_pc `0x056114` | `0x000562CA` | Still required by compatibility | Replacement writes virtual records 64-67 |
| arcade_pc `0x056440` | `0x000565F6` | Still required by compatibility lifecycle | Replacement parks records 68-71 |
| arcade_pc `0x059F5E` | `0x0005A114` | Still executes, output dead in gameplay | Replacement parks records 9-16 |
| arcade_pc `0x05A098` | `0x0005A268` | Still required by compatibility | Replacement writes virtual records 30-43 |
| arcade_pc `0x05A502` | `0x0005A6D2` | Still required by compatibility | Destination immediates at arcade_pc `0x05A51E` and `0x05A554` are patched at runtime_genesis_pc `0x0005A6EE` and `0x0005A724` into virtual records 83-90 |

**PROVEN:** there is no gameplay consumer for raw HW_ADDRESS `0x00D00000`
output. Raw copied writer `0x052AA2` is therefore a dead output tail, not a
required hardware contract. It should be retired at its semantic producer
boundary rather than redirected through another address emulator.

**PROVEN:** mapped D-compatible virtual output still has frontend consumers.
The scanner/decoder cannot be deleted until those producer families are
converted.

## DEAD SUBSYSTEM DEPENDENCY GRAPH

```text
status state at arcade_pc 0x05A098
  -> records 30-43 writer
  -> pc090oj_object_ram
  -> .Lnq_frontend_object_scan
  -> .Lpc090oj_decode_record
  -> native SAT builder

player auxiliary semantic table/state at arcade_pc 0x054810 / 0x052AA2
  -> records 44-47 virtual writer and records 0-3 raw writer
  -> virtual table or unconsumed HW_ADDRESS
  -> frontend scanner only for virtual rows

transient semantic descriptors at arcade_pc 0x05607C / 0x056114
  -> records 56-67 plus 0x056440 park lifecycle
  -> pc090oj_object_ram
  -> frontend scanner/decoder

setup semantic state at arcade_pc 0x054052 / 0x03AD84
  -> records 72-79
  -> pc090oj_object_ram
  -> frontend scanner/decoder

shared state at arcade_pc 0x05A502
  -> mapped records 83-90
  -> pc090oj_object_ram
  -> frontend scanner/decoder

legacy lifecycle at 0x03AD44 / 0x03B926 / 0x059F5E
  -> fill/park virtual records
  -> relevant only while a producer family still owns those rows
```

Deletion consequences:

- After native conversion of `0x05A098`, its record loop becomes dead, but the
  scanner, decoder, and object RAM remain required by the other families.
- After player auxiliary conversion, the `0x054810` packer and raw `0x052AA2`
  output tail become dead. The latter removes the remaining proven state-gated
  raw D-base write route.
- After transient 56-71 conversion, the stale
  `staged_sprite_descriptor_table` compatibility alias and three record helpers
  become dead. The live `worklist_entry_for_slot` storage must be separated
  before deleting its co-located dead aliases.
- After setup/priority conversion, `0x054052`, `0x03AD84`, and corresponding
  park maintenance become dead.
- After records 83-90 conversion, the two `0x05A502` mapped destination patches
  become dead.
- Only after every producer above is native can the frontend scanner, decoder,
  `pc090oj_object_ram`, D-range address adapters, boot clear, and legacy
  diagnostics be deleted together.
- Native queues, native SAT banks, tile residency/worklist, palette fixup, flip
  latch, and colbank latch remain after that final deletion.

## RECOMMENDED PRODUCER-BY-PRODUCER REMOVAL ORDER

| Order | Producer family | Scenes affected | Exact semantic cut point | Machinery made dead | Expected task size |
|---:|---|---|---|---|---|
| 1 | Status records 30-43 | Frontend/shared status states | arcade_pc `0x05A098`, before fixed PC090OJ record packing | `genesistan_pc090oj_hook_status_sprite_5a098` record loop for this family | SMALL |
| 2 | Player auxiliary/raw records 0-3 and 44-47 | Shared player/frontend; gameplay dead tail | arcade_pc `0x054810` table/state tuple and caller state before destination selection; include the `0x052AA2` state-gated raw tail | `0x054810` virtual packer and copied raw `0x052AA2` hardware writer | MEDIUM |
| 3 | Fixed/shared records 83-90 | Attract/frontend/shared setup | arcade_pc `0x05A502` before destination immediates | Both D00298-family mapped destination patches and that record writer | SMALL |
| 4 | Transient copy family 64-71 | Frontend/shared transient states | arcade_pc `0x056114` input tuple stream; lifecycle event at `0x056440` | Copy and park helpers for records 64-71 | MEDIUM |
| 5 | Transient decay family 56-63 | Frontend/shared transient states | arcade_pc `0x05607C` after semantic timer/active decision but before PC090OJ encoding | Decay record writer and `staged_sprite_descriptor_table` compatibility alias | LARGE |
| 6 | Setup/priority and legacy park/fill maintenance | Frontend/setup/transitions | semantic setup/lifecycle decisions before `0x054052`, `0x03AD84`, `0x03B926`, `0x059F5E`, and the D branch of `0x03AD44` | Records 5-16 and 72-79 writers; D-range fill branch; generic `0x03B930` and mirror adapters after final xref | MEDIUM |
| 7 | Final compatibility infrastructure retirement | All non-gameplay scenes, after visual regression proof | `pc090oj_native_emit_pass` scene dispatch: replace the remaining fallback with direct native producers | `pc090oj_object_ram`, boot clear, 256-record scanner, decoder, hardware-address translation, legacy counters/aliases, and obsolete remap entries | MEDIUM |

Recommended total: seven independently testable implementation tasks.

Task 1 is first because it is a single bounded producer with a known semantic
state input and no shared state mutation. Its conversion does not prematurely
force deletion of shared infrastructure. Each task must report the retained
arcade semantic cut, complete PC090OJ-specific tail removed, and any remaining
transitional compatibility, as required by the canonical policy.

## PERFORMANCE ACCOUNTING

- **Does a PC090OJ compatibility scanner execute during gameplay? PROVEN NO.**
  Scene 1 branches to `.Lnq_gameplay`, not `.Lnq_frontend_object_scan`.
- **Does a virtual object-RAM decode execute during gameplay? PROVEN NO.**
  `.Lpc090oj_decode_record` is called only by the frontend scanner.
- **Does dead PC090OJ record construction still have executable gameplay/shared
  routes? PROVEN YES.** Twelve identities are listed in the gameplay section;
  exact runtime hit frequency was not measured under the no-MAME constraint.
- **Does remaining compatibility machinery plausibly scale with enemy count?
  PROVEN NO for the compatibility scanner/decoder; NOT PROVEN for total game
  cost.** The enemy population uses native family queues. Remaining legacy
  loops are fixed-size or state-specific (4, 8, 14, or bounded record groups),
  not one scan/decoder pass per enemy.

Consequently the reported slowdown with many enemies should be audited in the
native actor expansion, queue emission, sprite tile residency/DMA, SAT load, or
unrelated gameplay logic. It should not be attributed to a gameplay execution
of the legacy 256-record scanner, because that execution count is zero.

## FINAL REMAINING PC090OJ HARDWARE-SEMANTIC DEBT

**PROVEN remaining debt:**

1. Eight producer-family groups still construct, clear, or preserve PC090OJ
   hardware records for frontend/shared states.
2. A 2 KiB virtual 256-record `pc090oj_object_ram` remains required by those
   producers.
3. A generic 256-record frontend scan and PC090OJ record decoder remain live.
4. D-range translation/fill helpers and mapped destination patches remain.
5. Copied arcade_pc `0x052AA2` retains a state-gated raw HW_ADDRESS
   `0x00D00000` output tail with no gameplay consumer.
6. Several dead candidate/representation/scan-era symbols and one uncalled
   generic copier body remain linked.

**DISPROVEN as debt:** original sprite codes, piece offsets, flip/priority
decisions, colbank semantics, preconverted sprite art, native tuple queues,
native SAT double-buffering, native tile residency/DMA, and VBlank SAT commit.
Those are required game semantics or direct Genesis realization.

**HYPOTHESIS requiring implementation-task validation:** exact visible ownership
of every compatibility record on every frontend sub-screen. Current static
routing and producer dependencies are sufficient for the removal order, but
each producer conversion must capture or otherwise prove its affected states
before deleting its old tail.

No additional Ghidra coverage was needed. Existing current Ghidra exports
established the bounded semantic entry/caller relationships used here.
