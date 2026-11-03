# Cody Status-Sprite Producer 0x05A098 Native Conversion

## BASELINE

- **PROVEN:** Accepted forward baseline is Build 0282,
  `dist/rastan-direct/rastan_direct_video_test_build_0282.bin`, SHA-256
  `61b2b1268362f309c64939c1a6d226df5a4a26a95f95b560071701266d694316`,
  1,590,912 bytes, counter 282.
- **PROVEN:** The baseline artifact was preserved and was not overwritten.
- **PROVEN:** This task changes only the `arcade_pc 0x05A098` replacement and
  the ownership of the existing native HUD queue across the later gameplay
  frame boundary. It does not alter PC080SN, collision, actor positioning,
  sword state, or any other PC090OJ producer family.
- **PROVEN:** Address correlations in this report come from segment containment
  in `build/rastan-direct/address_map.json`, not arithmetic relocation
  assumptions.

## ORIGINAL ARCADE STATUS-SEMANTIC PRODUCER

- **PROVEN:** `arcade_pc 0x05A098` is called at `arcade_pc 0x051054` from
  `FUN_0005100A`. The address map resolves the caller to
  `runtime_genesis_pc 0x051254`. `FUN_0005100A` is called at
  `arcade_pc 0x041F0E` by the gameplay main loop.
- **PROVEN:** This is the player energy/status renderer, not a title, throne,
  story, high-score, or other frontend producer. It consumes the player energy
  word at `A5+0x013A` and produces an ordered horizontal status row.
- **PROVEN:** The semantic row uses PC090OJ-space Y `0x00E8` and X positions
  beginning at `0x0010`, increasing by 16 pixels per piece. Local attribute
  word zero means no producer-local flip or colbank override; the shared native
  finalizer retains the established global PC090OJ control and colbank rules.
- **PROVEN:** The leading animated indicator is selected from codes `0x03CA`
  and `0x03CB` by the retained `A5+0x12A4`, `A5+0x12A6`, `A5+0x1306`, and
  `A5+0x130A` state machine.
- **PROVEN:** When the refresh gate `A5+0x12FC == 1`, the remaining row is a
  left cap (`0x03CC`) and six energy cells. Each eight energy units yields a
  full cell (`0x03CD`). Remainders 1 through 7 select `0x03D4` through
  `0x03CE`; empty cells use `0x03D5`. Energy is clamped to 48 units.
- **PROVEN:** Low energy (`A5+0x1328 == 1`) blinks the first energy cell between
  the remembered partial/empty code at `A5+0x132A` and `0x03D5`, driven by
  `A5+0x1308`.
- **PROVEN:** The inline helper at `arcade_pc 0x05A244` updates low/normal
  lifecycle fields `A5+0x13CE` and `A5+0x13D2`. The sound transitions call
  `arcade_pc 0x03A0EC` with command 6 and `arcade_pc 0x03A116` with command
  `0x29`; the address map resolves these to `runtime_genesis_pc 0x03A2EC` and
  `runtime_genesis_pc 0x03A316`.
- **PROVEN:** The maximum semantic output is eight ordered positions: optional
  animated indicator, left cap, and six energy cells. A skipped indicator is a
  semantic hole at the first position, not a request to repack later pieces.

## PC090OJ-SPECIFIC CUT POINT

- **PROVEN:** The first PC090OJ-specific operation is the load of hardware
  destination `HW_ADDRESS 0x00D00048` at `arcade_pc 0x05A0AE`. The semantic
  decisions that choose code, X, Y, visibility, and lifecycle are retained;
  the following `A0` destination arithmetic and four-word/eight-byte record
  stores are retired.
- **PROVEN:** Hardware stores begin at `arcade_pc 0x05A11A`, `0x05A13E`,
  `0x05A188`, `0x05A1AC`, and `0x05A1D0`. The low-energy post-build mutation at
  `arcade_pc 0x05A1EC..0x05A20C` is also hardware-tail behavior and is replaced
  by a direct update to semantic HUD output index 2.
- **PROVEN:** The exact retained semantic cut is:

  `energy/status state decision -> {attribute, Y, code, X, ordered position}`

  The removed tail is:

  `HW_ADDRESS 0x00D00048 -> PC090OJ record address/gap arithmetic -> record stores/mutation`.
- **DISPROVEN:** PC090OJ record indices or Genesis virtual slots are semantic
  ownership. They are hardware/compatibility realization details only.

## AFFECTED FRONTEND STATES

- **PROVEN:** No frontend state calls `arcade_pc 0x05A098`. Its sole static
  caller is the gameplay update at `arcade_pc 0x051054`.
- **PROVEN:** The affected visible state is gameplay scene 1 player
  energy/status. Title, throne, story, high-score, insert-coin, and attract
  frontend states are non-consumers and must remain unchanged.
- **DISPROVEN:** The older compatibility audit description of this producer as
  “frontend/shared status” and its recommendation to use frontend ownership.
  Current original-ROM caller evidence supersedes that classification.

## OLD HARDWARE-OUTPUT TAIL

- **PROVEN:** Original arcade output begins at PC090OJ record 9 because
  `0x48 / 8 == 9`. This is arcade hardware provenance only.
- **PROVEN:** The Build 0282 compatibility helper instead looped over Genesis
  virtual slots 30 through 43 and called `.Lpc090oj_emit_slot`. Those slot
  numbers came from the historical compatibility allocator; they were neither
  original arcade record indices nor semantic status identities.
- **PROVEN:** Build 0282 gameplay already bypasses the frontend object-RAM
  scanner/decoder, so this compatibility output was not the gameplay native
  owner. The conversion removes the status producer's dependence on
  `.Lpc090oj_emit_slot`, `pc090oj_object_ram`, record packing, scanner, and
  decoder.

## NATIVE OWNERSHIP

- **PROVEN:** `native_queue_hud` is the existing gameplay semantic HUD lane.
  `pc090oj_native_emit_pass` consumes this lane first, then the existing
  FRONT_EFFECT, PLAYER_FRONT, MIDDLE, PLAYER_BODY, and BACK_ENEMY lanes, and
  emits final Genesis SAT entries through `.Lnq_emit_entry`.
- **PROVEN:** The lane bound is nine entries; this producer needs at most eight.
- **PROVEN:** Main-loop ordering is status producer at `arcade_pc 0x051054`,
  native frame begin at the replacement reached from `arcade_pc 0x041F4A`, and
  native finalizer at the replacement reached from `arcade_pc 0x041F58`.
  Therefore the old HUD clear in `native_sprite_frame_begin` would erase the
  status row after publication and before finalization.
- **PROVEN:** `FUN_0005100A` can skip the status update while its state gates are
  active. Original hardware records persist on skipped frames. The direct
  native HUD lane therefore preserves its previous semantic row until the
  original producer refreshes it; the later frame-begin clear is removed only
  for this lane.
- **PROVEN:** This is direct semantic output into an existing native lane, not a
  PC090OJ-shaped object table, virtual chip RAM, scanner input, or pack/unpack
  representation.

## IMPLEMENTATION

- **PROVEN:** `genesistan_pc090oj_hook_status_sprite_5a098` now reproduces the
  original energy validation, indicator animation, six-cell full/partial/empty
  construction, low-energy blink, lifecycle fields, and sound transitions.
- **PROVEN:** `.Lstatus_store_piece` writes the final native semantic tuple
  directly to `native_queue_hud`. It does not call `.Lpc090oj_emit_slot` and
  does not address `pc090oj_object_ram` or `HW_ADDRESS 0x00D0xxxx`.
- **PROVEN:** `native_sprite_frame_begin` no longer clears only
  `native_hud_count`; all other gameplay lanes retain their existing clear
  behavior. The status producer owns HUD refresh/retention before the single
  gameplay finalizer.
- **PROVEN:** The remap remains a proper function-body replacement at
  `arcade_pc 0x05A098`; its note now records the direct-native semantic owner.
  No bypass, NOP-only fix, state forcing, or second SAT path was introduced.
- **PROVEN:** The modified assembly passes a direct GNU m68k assembler check,
  and `specs/rastan_direct_remap.json` parses successfully before the numbered
  build.

## DEAD COMPATIBILITY CODE

- **PROVEN:** The status-family loop that assigned virtual slots 30 through 43
  and called `.Lpc090oj_emit_slot` is removed.
- **PROVEN:** The status-family uses of PC090OJ record address arithmetic,
  eight-byte packing, parking/gap semantics, and post-build record mutation are
  removed from the replacement helper.
- **PROVEN:** `.Lpc090oj_emit_slot`, `.Lpc090oj_clear_slot`,
  `pc090oj_object_ram`, the frontend scanner, and the generic decoder are
  intentionally retained because other compatibility producer families still
  reference them.

## FRONTEND VALIDATION

- **PROVEN static non-interference:** Original xrefs show no frontend caller of
  `arcade_pc 0x05A098`. The implementation changes no title/frontend branch,
  frontend native HUD producer, object-RAM scan branch, scene selector, frontend
  queue, or frontend palette path.
- **PROVEN source-level result:** Build 0282 and the candidate have identical
  ownership for title, throne, story, high-score, insert-coin, and attract
  frontend states. Visible piece count, art, position, flip, palette, order,
  lifecycle, and scene transitions in those non-consumer states are therefore
  unaffected by this replacement.
- **PROVEN runtime non-interference:** The mandatory Build 0283 MAME trace ran
  1,798 external frames and completed with no unique unmapped-memory address.
  Evidence is preserved in
  `states/traces/rastan_direct_video_test_build_0283_mame_30s_20260816_111150/`.
  This validates frontend reachability/non-interference; it does not reclassify
  this gameplay-only producer as frontend ownership.
- **PROVEN:** No title, throne, story, high-score, insert-coin, or attract
  producer/source path changed. Frontend semantic validation is therefore PASS.

## GAMEPLAY REGRESSION

- **PROVEN contract:** The existing gameplay finalizer consumes the
  HUD lane directly and does not call the frontend object-RAM scanner. The
  status helper no longer populates compatibility records.
- **PROVEN non-interference:** Collision-map source reads, actor
  logical coordinates, player movement/attack state, and all non-HUD native
  sprite producers are byte/source unchanged by this task.
- **PROVEN runtime lifecycle:** The focused Build 0283 debugger run observed
  393 gameplay status-helper entries, 394 gameplay frame-begin entries, and 395
  gameplay finalizer entries. Once the first status-helper call published its
  row, every later sampled frame begin and finalizer retained `hud_count=8`.
  There were zero post-publication count mismatches and zero unexpected code
  tuples. The full-energy tuple was indicator `0x03CA` (the alternate semantic
  state is `0x03CB`), cap `0x03CC`, and six `0x03CD` cells.
- **PROVEN lifecycle boundary:** Three scene-1 finalizers occur during gameplay
  transition before the first original status-producer invocation; their HUD
  count is zero. This is pre-publication state, not a stale/missing native row.
  After original publication, no stale or missing status piece was observed.
- **PROVEN runtime reachability:** Exact debugger breakpoints at
  `runtime_genesis_pc 0x000736C6` (frontend compatibility scanner) and
  `runtime_genesis_pc 0x00073960` (compatibility record decoder) recorded zero
  gameplay hits. The native status helper at `runtime_genesis_pc 0x00072F4A`
  publishes before frame begin at `runtime_genesis_pc 0x00072842`; finalization
  begins at `runtime_genesis_pc 0x000731EA` and takes the scene-1 native branch.
- **PROVEN movement:** Controlled Stage-1 input moved player X from 81 to 160.
  Controlled jump input moved Y from 112 through apex 76 and returned to 112,
  proving jump and landing.
- **PROVEN attacks:** The standing run entered attack-active state and advanced
  phases 0..9; the crouch run retained action `0x0005`, entered attack-active
  state, and advanced phases 0..10. Standing and crouching attack regressions
  PASS.
- **PROVEN actor grounding:** Both controlled runs observed class `0x17/0x18`
  Lizardmen at logical Y 121. The unchanged BACK_ENEMY native expansion emitted
  their lower cells through screen/visible bottom 129. The established Build
  0282 grounding result is preserved.
- **PROVEN evidence:** Focused files are under
  `states/traces/build0283_status_sprite_native_validation_20260816_111503/`.

## BUILD AND VERIFICATION

- **PROVEN:** Exactly one Makefile-owned numbered candidate was produced:
  Build 0283 at
  `dist/rastan-direct/rastan_direct_video_test_build_0283.bin`.
- **PROVEN:** SHA-256 is
  `d421e8c6f4067d5555d41175ce50401d08aefe2fb109e47e49fed29484ddcf90`;
  size is 1,591,376 bytes; counter transition is 282 -> 283. The rolling ROM is
  byte-identical to the numbered artifact.
- **PROVEN:** Canonical verification reports `GATE_PASS`. The helper adds
  `0x1D0` measured canonical bytes (`0x184680 -> 0x184850`) while retaining 228
  opcode replacements. Two address-map-resolved sound calls raise the expected
  Genesis-only maincpu reference count from 5 to 7.
- **PROVEN:** Build 0282 remains preserved with its accepted SHA-256. No
  numbered artifact was deleted or overwritten.

## REMAINING PC090OJ COMPATIBILITY DEBT

- **PROVEN:** Remaining families include player auxiliary/raw output, transient
  decay records 56-63, transient copy records 64-67, transient clear records
  68-71, slot/setup initialization, priority initialization, the fixed/shared
  83-90 family, and generic frontend compatibility infrastructure.
- **PROVEN:** None of those families is converted, deleted, or behaviorally
  changed by this task. This conversion retires one original semantic
  producer's hardware-specific tail; it does not retire the full compatibility
  subsystem.
