# Cody - Player Auxiliary / Raw Producer Native Conversion

## BASELINE

**PROVEN**

- Accepted baseline: Build 0283, ROM
  `dist/rastan-direct/rastan_direct_video_test_build_0283.bin`, SHA-256
  `d421e8c6f4067d5555d41175ce50401d08aefe2fb109e47e49fed29484ddcf90`,
  size 1,591,376 bytes, counter 283.
- Current source, `specs/rastan_direct_remap.json`, and
  `build/rastan-direct/address_map.json` are the implementation and address
  authorities. No numeric relocation offset is used as proof.
- Build 0282 collision-source displacement `0x20`, logical actor grounding,
  removal of the BACK_ENEMY render-only `-8`, Build 0281 sword geometry,
  Build 0280 `A5+0x1338`, and Build 0283 native status output are preserved.

## ORIGINAL ARCADE PLAYER AUXILIARY SEMANTICS

**PROVEN**

- `arcade_pc 0x0529CC` is in the player damage/reaction progression. It
  activates the auxiliary state, changes player vertical/reaction state, and
  issues sound command `0x26`.
- The retained owner at `arcade_pc 0x0547C0` uses active field `A5+0x1296`,
  phase `A5+0x1298`, and subtype `A5+0x129E`.
- Subtype 1 uses phase/4 indices 0..2 and retires at phase 12. Each frame has
  one nonblank code: `0x0275`, `0x0276`, or `0x0277`.
- Subtype 4 uses phase/4 indices 4..8 and retires at phase 20. Each frame has
  four pieces using `0x0278..0x0287` or `0x02A9..0x02AC`.
- The source is `arcade_rom/data 0x05DA5E`, arranged as 24-byte frames of four
  six-byte semantic pieces: code word, signed X byte, signed Y byte, and
  attribute word. The constructor anchors X/Y to `A5+0x129A/0x129C`, adds one
  to Y as the original code does, masks coordinates to nine bits, and carries
  source attribute nibble 3. No source-frame flip bit is introduced.
- Low PC090OJ record numbers historically gave this player-attached effect
  front priority. The existing native `FRONT_EFFECT` lane has the same
  semantic ownership and priority.

**DISPROVEN**

- This family is not the standing, crouching, or downward-thrust melee sword.
  Those pieces are owned by the BODY constructor at `arcade_pc 0x0540CC`.
- The historical record numbers 0..3 and 44..47 are not semantic identities.

**HYPOTHESIS**

- Direct tile inspection identifies compact effect art, but the exact visual
  noun for every phase (impact, glint, spark, or reaction) is not established.
  The behavior-level identity and complete tuple construction are established
  and are sufficient for the native cut.

## 0x054810 PRODUCER

**PROVEN**

- `arcade_pc 0x054810` is the final constructor called by the retained
  `0x0547C0` state machine. It receives the selected frame index, chooses the
  24-byte frame at `arcade_rom/data 0x05DA5E`, and constructs four PC090OJ
  records.
- The semantic cut is after table/frame selection and before loading
  `HW_ADDRESS 0x00D00000`, selecting records 44..47, or packing an eight-byte
  device record.
- The replacement retains the original table operand and frame selection in
  copied arcade code. Shift-table relocation, not arithmetic, repairs that
  operand in the generated ROM.

## 0x052AA2 RAW PRODUCER

**PROVEN**

- `arcade_pc 0x052A64` calls `arcade_pc 0x052AA2` after the same phase update
  used by this damage/reaction state. Its constructor and four source tuples
  are byte-for-byte the same frame/table realization as `0x054810`, but it
  writes records 0..3 through raw `HW_ADDRESS 0x00D00000`.
- The normal main-loop path later reaches `0x0547C0/0x054810`, which publishes
  the same selected state after the update. Gameplay has no object-table
  consumer, and the later producer is the authoritative single publication.
- The `0x052AA2` output therefore has no additional visible semantic piece or
  lifecycle owner. The call and now-unreferenced duplicate constructor can be
  deleted while retaining the phase update.
- The phase terminator contained two unrebased absolute writes to
  `arcade_WRAM 0x0010D296`. They are corrected to the authoritative
  A5-relative active field `A5+0x1296`; this preserves retirement instead of
  writing a Genesis ROM address.

## SEMANTIC RELATIONSHIP

**PROVEN:** `0x052AA2` and `0x054810` are duplicate hardware-output
realizations of the same player damage/reaction auxiliary state. They are not
two different effects merely sharing an anchor. One native publication from
the retained `0x0547C0` owner represents the family completely.

## PC090OJ-SPECIFIC CUT POINTS

```text
retained arcade damage/reaction activation and phase update
  -> retained subtype/index decision and 0x05DA5E frame selection
  -> CUT
  -> removed D00000 destination, record-number choice, and 8-byte packing
  -> native FRONT_EFFECT semantic tuples
```

**PROVEN:** no virtual device address, hardware record index, object-RAM
adapter, record parking, scanner, or decoder is needed after this cut.

## NATIVE OWNERSHIP

**PROVEN:** `NATIVE_LANE_FRONT_EFFECT` is the existing correct owner. The
effect is player-attached, is not player BODY art, and had front-priority
records in the original PC090OJ ordering. `PLAYER_BODY` and `PLAYER_FRONT`
remain unchanged.

## IMPLEMENTATION

**PROVEN source implementation**

- `genesistan_pc090oj_hook_player_aux_native_54810` accepts `A0` at the
  selected four-piece source frame and sends each `{attr,Y,code,X}` tuple to
  `native_sprite_emit` with `NATIVE_LANE_FRONT_EFFECT` ownership.
- The shift replacement at `arcade_pc 0x054810` retains the original
  `arcade_rom/data 0x05DA5E` pointer and index multiplication, then calls the
  native helper before returning.
- The earlier call at `arcade_pc 0x052742` and duplicate constructor
  `0x052A64..0x052AF5` are deleted. The phase updater remains live.
- The two terminal stores at `arcade_pc 0x052B0E` and `0x052B2A` now write
  `#0x00FF` to `A5+0x1296`.
- The Build 0280 semantic auxiliary array at `A5+0x1338` is untouched. No old
  Block-A tuple dependency is restored.

## DEAD HARDWARE OUTPUT

**PROVEN source result**

- This family no longer calls `.Lpc090oj_emit_slot` or writes
  `pc090oj_object_ram`.
- Virtual records 44..47 and raw records 0..3 cease to exist as output
  identities for this family.
- The executable raw `HW_ADDRESS 0x00D00000` load in the duplicated
  `0x052AA2` tail is deleted rather than redirected through another adapter.
- Other compatibility helpers, object RAM, frontend scanner, and decoder are
  intentionally retained for later producer families.

## AUTOMATED VALIDATION

**PROVEN mechanical candidate result**

- The one authorized Makefile invocation produced and permanently consumed
  Build 0284:
  `dist/rastan-direct/rastan_direct_video_test_build_0284.bin`, SHA-256
  `99942d043d81a65970a238d3ec7cdf67760423ddef7797f2a6ac24d8171a65dd`,
  1,591,348 bytes; counter 283 -> 284. The rolling ROM is byte-identical.
- Its canonical gate passed, and its mandatory 1,798-frame MAME trace at
  `states/traces/rastan_direct_video_test_build_0284_mame_30s_20260816_122150/`
  completed with 47,265 VDP live writes and no unique unmapped-memory address.

**DISPROVEN candidate correctness**

- The post-build address-discipline audit rejected Build 0284. At
  `runtime_genesis_pc 0x05492A`, its replacement loaded
  `runtime_genesis/data 0x05DC5E`, while
  `build/rastan-direct/address_map.json` maps the required
  `arcade_rom/data 0x05DA5E` exactly to `runtime_genesis/data 0x05DB52`.
  The intended table bytes exist at `0x05DB52`; `0x05DC5E` is unrelated data.
- Therefore Build 0284 is a mechanically passing but semantically invalid,
  rejected artifact. It remains preserved and is not an accepted forward
  baseline. No second numbered ROM was produced because the prompt authorized
  exactly one Makefile-owned candidate.

**PROVEN corrected source/tool result (unnumbered validation only)**

- `relocate_after_shift` now supports an optional suffix around its deferred
  interior `abs.l` operand. The `arcade_pc 0x054810` replacement expresses
  `arcade_rom/data 0x05DA5E` as `operand_arcade_target`, rather than embedding
  an arithmetic-derived Genesis address.
- A fresh unnumbered postpatch maps `arcade_rom/data 0x05DA5E` exactly to
  `runtime_genesis/data 0x05DB52` and emits at
  `runtime_genesis_pc 0x05492A`:
  `207C0005DB52C0FC0018D0C04EB900072E1A4E75`.
- The corrected unnumbered ROM is 1,591,348 bytes with SHA-256
  `79b6e8c9c563f9cbe068459a90d9447eb7adb7a16e00348e3ac49f829bf7983b`
  and passes the complete canonical verifier (`GATE_PASS`). It is validation
  material, not a numbered release candidate.
- Durable corrected evidence is under
  `states/traces/build0284_player_aux_corrected_unnumbered_validation_20260816_122834/`,
  including the patch manifest, address map, relocation report, mapping proof,
  gate result, and controlled gameplay traces.
- Static generated-code inspection confirms the corrected family has no
  `HW_ADDRESS 0x00D00000` destination and no records 0..3 or 44..47. The two
  terminal stores map exactly to A5-relative `A5+0x1296` writes.
- The 1,200-frame owner-state run did not naturally activate this damage state
  (`A5+0x1296 == 1` occurred for zero frames). `0x00FF` is the inactive
  sentinel, not an active state. Accordingly, effect-specific lifecycle and
  visual placement remain static original-code proof; no RAM was seeded to
  manufacture runtime coverage.

## GAMEPLAY REGRESSION

**PROVEN on the corrected unnumbered image**

- Two controlled 900-frame Genesis NTSC MAME runs reached Stage 1 with no
  state seeding. Walking moved player logical X 81 -> 160.
- Jump/landing moved player logical Y 112 -> 76 -> 112. The crouch run stayed
  grounded at Y 112.
- Standing attack and crouching attack were each observed in their respective
  controlled run.
- Stage-1 Lizardman classes `0x17/0x18` retained logical Y 121 and the current
  native rendering contract's visible bottom 129.
- Source control flow remains decisive for compatibility exclusion:
  scene 1 enters the native queue finalizer and branches around
  `.Lnq_frontend_object_scan`; `.Lpc090oj_decode_record` is reachable only from
  that non-gameplay compatibility scan. Thus gameplay scanner executions and
  generic decoder executions remain zero. The Lua instruction-read taps are
  not used as count evidence because the same mechanism also missed the known
  frame-begin/finalizer PCs in this MAME configuration.
- No detached auxiliary garbage was observed in either bounded run. Because
  the damage auxiliary did not naturally activate, user visual verification
  of its active lifecycle remains required on a valid numbered candidate.

## DOCUMENTATION UPDATES

- `CLOSED_ISSUES.md` records the prior Build 0282 grounding/sword correction
  and Build 0283 status conversion. This auxiliary family is not closed because
  no valid numbered candidate exists.
- `KNOWN_FINDINGS.md` records the current native ownership and remaining-family
  count.
- `GRAPHICS_STATUS.md` records current user-observed progress without claiming
  PC080SN completion.
- `OPEN_ISSUES.md` retains map/hazard, palette, gameplay exception/demon,
  slowdown, the unreleased corrected auxiliary conversion, and remaining
  compatibility work.

## REMAINING PC090OJ COMPATIBILITY DEBT

The accepted numbered baseline remains Build 0283 because Build 0284 was
rejected. The corrected source retires this family, but needs a newly
authorized numbered candidate. Once that corrected source is released, the
approved sequence contains five units:

1. fixed/shared producer around `arcade_pc 0x05A502`;
2. transient copy/clear family;
3. transient decay family;
4. setup/priority plus legacy maintenance;
5. final frontend compatibility infrastructure retirement.

No later family is modified by this task.

## STOP BOUNDARY

The implementation and corrected unnumbered validation are complete, but the
single authorized numbered candidate was consumed before the address-mapping
defect was found. The exact remaining boundary is authorization to produce one
new Makefile-owned candidate from the corrected source. Until then, Build 0283
is the accepted baseline, Build 0284 is preserved/rejected, and no user test is
requested against Build 0284.
