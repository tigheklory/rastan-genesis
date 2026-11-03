# Cody Build 0428 — Rastan Player Genesis-Native Sprite Optimization

## Result

Build 0428 replaces the remaining generalized per-piece work in the normal-gameplay
Rastan primary and secondary presentation loops with generated Genesis-native player
records and direct bounded queue appends. The accepted Build 0426 common-enemy/generic
path is unchanged.

The complete five-ROM Build 0428 family passed the normal mechanical gates. The
established rope benchmark improved deterministically from 806 frames / 13,450.653 ms
to 803 frames / 13,400.588 ms. Real Genesis visual/gameplay acceptance remains **USER
MUST VERIFY**.

## Native-replacement boundary

- **Semantic cut retained:** arcade player state has already selected the effective
  primary body selector, equipped weapon or finite Fire Sword phase, secondary selector,
  and orientation. Player gameplay, animation, position, weapon state, and ordering remain
  arcade-owned.
- **Chip-specific tail retired:** for every generated reachable key, the primary
  compositor at arcade `0x054492` and secondary compositor at arcade `0x0546A8` do not
  build PC090OJ object records. Their complete graphics tail is replaced by direct native
  player queue production and the existing residency/SAT finalizer.
- **Transitional compatibility retained:** the pre-existing unresolved-selector fallback
  remains isolated behind the generated-key validity checks. The verifier proves zero
  unresolved keys in the reachable primary domain. Removing the fallback still requires
  broader reachability authority and was not part of this optimization. No mirror, shadow,
  object-record scanner, range dispatcher, or parallel gameplay renderer was added.

## Source audit

The authoritative inputs remain the original main-CPU tables plus:

- `analysis/actor_decompilation/h24_player_frame_cells.tsv`
- `analysis/actor_decompilation/h24_player_weapon_cells.tsv`
- `analysis/actor_decompilation/h24_player_leg_cells.tsv`
- the existing variant/palette inputs already consumed by the generator

Field classification across the complete generated domain:

| Work/value | Classification |
|---|---|
| body/weapon/fire/secondary composition | build-time constant |
| oriented `dx/dy`, piece order/count, fixed 16×16 size | build-time constant |
| finalized pattern/residency identity | build-time constant |
| weapon-anchor ownership and relative coordinate | build-time constant |
| selector key, player base X/Y | frame-level runtime |
| player queue context and initial append cursor | frame-level runtime |
| attribute | frame-level in 1,172/1,200 primary keys and 416/416 secondary keys |
| attribute in 28 primary keys with real body/weapon priority differences | per-piece |
| X/Y addition, Y-hide test, capacity, append | genuinely per-piece runtime |
| residency slot, first-use upload, SAT link/order | retained shared finalizer runtime |

## Representation before and after

Before, both player paths indexed six-byte frame descriptors and walked shared 10-byte
pieces:

```text
{ s16 dx, s16 dy, u16 finalized_key, u16 attr, u8 size, u8 flags }
```

Every piece loaded its attribute, tested the anchor flag in the primary path, called
`native_sprite_emit_fast`, revalidated the already-finalized identity, reconstructed the
queue cursor, checked clipping/capacity, and returned.

After, both player indexes use one 12-byte descriptor:

```text
{ u32 offset, u8 count, u8 format, u16 frame_attr,
  s16 anchor_dx, s16 anchor_dy }
```

`anchor_dx = 0x8000` means no anchor. Format 1 uses:

```text
{ s16 dx, s16 dy, u16 finalized_key }              // 6 bytes
```

Format 2 exists only for the 28 proven mixed-priority primary keys and uses:

```text
{ s16 dx, s16 dy, u16 finalized_key, u16 attr }    // 8 bytes
```

Generated sizes are:

- primary index: 14,400 bytes, 1,172 compact + 28 mixed records;
- secondary index: 4,992 bytes, all 416 compact records;
- dedicated player piece table: 19,428 bytes;
- canonical ROM: 2,694,840 bytes, 4,096 bytes smaller than Build 0426.

## Primary body, weapons, and anchor

`native_player_frame_try` still derives the key from the effective body selector,
NONE/SWORD/AXE/HAMMER/FIRE SWORD variant, finite Fire Sword phase, and orientation. The
generator continues to compile body and weapon pieces into one ordered presentation frame;
there is no separate weapon renderer or registry.

The primary path clears `A5+0x129A/A5+0x129C` at the same successful native-frame boundary.
When a weapon anchor exists, the descriptor's generated relative X/Y is added to the live
player base and masked to nine bits before publication. This occurs before visibility and
queue-capacity rejection, matching the accepted per-piece anchor flag's ordering. The
independent verifier checks zero/one anchor ownership and resulting coordinates for several
wrap-sensitive base positions for all 1,200 keys.

The runtime selects compact versus mixed format once. Both loops establish queue context
and the append cursor once, then directly append the final `(attr,Y,key,X)` tuple. They do
not call the generalized fast emitter.

## Secondary / legs

All 416 secondary keys have a frame-wide attribute. `native_player_secondary_frame`
therefore loads the attribute once and walks only compact six-byte pieces. It establishes
the queue cursor once and performs the same direct bounded tuple append. Finite phase
substitution, orientation, order, coordinates, identity, visibility, and queue ordering are
unchanged.

## Work removed or hoisted

Moved offline:

- fixed size and static flags;
- orientation geometry;
- finalized pattern identity;
- weapon and Fire Sword composition;
- anchor ownership and relative anchor coordinate.

Hoisted once per frame:

- lane queue base/count/end context;
- initial append cursor;
- player base X/Y;
- frame attribute where invariant;
- format selection and weapon-anchor publication.

Removed from each piece:

- fixed-size transport;
- static anchor-flag test;
- already-finalized identity validation;
- queue cursor reconstruction;
- `BSR/RTS native_sprite_emit_fast`;
- repeated attribute load for all compact frames.

Per-piece runtime now consists of relative X/Y loads and base addition, finalized-key load,
the retained Y-hide test, one queue-end comparison, and the four-word append. The 28 mixed
primary keys additionally load the exact per-piece attribute.

## Semantic equivalence and gates

The independent generator/verifier proves:

- 1,200/1,200 primary keys native, zero unresolved;
- 416/416 secondary keys native;
- every body selector, weapon, Fire Sword phase, secondary phase, and orientation;
- exact piece count/order, geometry, identity, attribute, anchor, and residency set;
- 38/38 accepted Build 0426 compact generic records unchanged in coverage;
- 1,898 universal general and 24 universal specialized records still pass.

Normal validation passed:

- canonical gate / `GATE_PASS`;
- pre/post-patch boot guards;
- gameplay-entry gate (564 frames, player control observed, zero exceptions);
- native frame-table and direct-dispatch gates;
- PC080SN background, selector, collision/visual, and transition gates;
- VDP DMA boundary gate;
- mandatory 1,798-frame Genesis NTSC MAME trace;
- complete canonical, `_d`, `_s`, `_do`, `_c` family verification.

The standing seven-epoch gate warning remains unchanged: epoch 0 passes and the numbered
artifact is preserved for evaluation.

## Performance

The existing deterministic rope runner was reused without modification.

| Build | Trials | Frames | Emulated ms |
|---|---:|---:|---:|
| accepted 0426 | 3 | 806 | 13,450.653 |
| candidate 0428 | 3 | 803 | 13,400.588 |
| arcade Silver Standard | 5 | 771 | 12,850.000 |

Build 0428 is 3 frames / 50.065 ms / **0.372%** faster than Build 0426. It remains
32 frames / 550.588 ms behind the arcade benchmark. Build 0428 trials were exactly
`803,803,803` frames.

Evidence: `states/traces/build0428_rope_attach_benchmark/` and
`states/traces/rastan_direct_video_test_build_0428_mame_30s_20261014_231555/`.

## Build artifacts

Only Build/reference label **0428** was produced for this implementation. The earlier
assembler and invariant stops occurred before numbered publication and did not consume a
label.

- final candidate: `dist/rastan-direct/rastan_direct_video_test_build_0428.bin`
- complete family: canonical, `_d`, `_s`, `_do`, `_c`
- size: 2,694,840 bytes each
- canonical SHA-256: `b54b076debab195cc766c1cd81506047e139db25d65913ade7732cf24824a080`
- counter: 428

## Files changed

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/pc090oj_assets.s`
- `apps/rastan-direct/Makefile`
- `tools/translation/precompute_pc090oj_frame_table.py`
- `tools/translation/verify_pc090oj_frame_table.py`
- `tools/translation/verify_pc090oj_direct_dispatch.py`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- `docs/design/Cody_build0428_rastan_player_genesis_native_optimization.md`
- `AGENTS_LOG.md` (append only)

No enemy path, Build 0426 generic loop, gameplay/collision, rope, Plane A/B, palette, HUD,
frontend, damage, sound, scheduler, Phase D, or Phase E code changed.

## Policy review

- Semantic rather than chip-write cut: **YES**.
- Complete reachable player PC090OJ compositor tails bypassed: **YES**.
- Consumes retained arcade semantic state, not chip-shaped state: **YES**.
- New mirror/shadow/virtual device/range dispatcher/projector: **NO**.
- Existing compatibility isolated and temporary: **YES**, unresolved-key fallback only;
  removal requires broader reachability proof.
- Arcade retains gameplay/frame/VBlank ownership: **YES**.
- Native helper directly produces final native queue data for the SAT finalizer: **YES**.
- Superseded compatibility retirement path documented: **YES**.

Established tools were reused: the existing player compiler/verifiers, Makefile-owned build
and family gates, mandatory Genesis NTSC trace, and rope benchmark. No new tracing or
profiling framework was created.

## Project ledger impact

**KNOWN_FINDINGS impact: Option A — no update.** This implementation confirms and refines
KF-074/KF-077/KF-089 without changing their durable architecture or meaning.

### Open/Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-024
- New issues opened: NONE
- Issues closed: NONE
- Issues intentionally deferred: OPEN-026 and all unrelated existing issues

## Hardware acceptance

**USER MUST VERIFY** standing/walking/running/jumping/crouching/climbing, left/right,
SWORD/AXE/HAMMER/FIRE SWORD placement, hand/body anchor alignment, legs/body synchronization,
missing pieces, flicker/corruption, and rope-race feel on real Genesis hardware.

Phase D started: **NO**.  
Phase E started: **NO**.
