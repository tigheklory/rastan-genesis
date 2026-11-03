# Cody: Pre-Trace Static Reconciliation

## Scope and baseline

- Accepted baseline: Build 0279; counter 279.
- Task: bounded static reconciliation only.
- No MAME, user gameplay, build, ROM, source, spec-implementation, or palette-implementation
  change was performed.
- Address correlations below come from `build/rastan-direct/address_map.json`. Data addresses
  are handled separately; no arithmetic relocation is used as authority for a PC mapping.
- Canonical palette decision `PAL-PC090OJ-GAMEPLAY-RASTAN-SWORD-001` is unchanged.

## THRUST TIP RECONCILIATION

At `arcade_pc 0x0543AE`, variant 1 selects the phase table at arcade ROM/data `0x05BB10`.
`arcade_pc 0x0543B4` doubles the phase before reading its selector. The selector indexes the
big-endian word-offset table at `0x05BD40`; adding that offset to `0x05BD40` locates the
primary descriptor. Its record is `{code16,xoff8,yoff8,attr16}`.

| Phase | selector | descriptor address | raw 6 bytes | code | xoff | yoff | attr |
|---|---:|---:|---|---:|---:|---:|---:|
| 0-1 | `0x00` | `0x05BDD6` | `00 8E F8 E0 00 03` | `0x008E` | `-8` | `-32` | `0x0003` |
| 2-5 | `0x19` | `0x05BFE8` | `01 01 F8 E0 00 03` | `0x0101` | `-8` | `-32` | `0x0003` |
| 6-9 | `0x1A` | `0x05BFFC` | `01 04 F8 E0 00 03` | `0x0104` | `-8` | `-32` | `0x0003` |
| 10-23 | `0x1B` | `0x05C010` | `01 04 F8 E8 00 03` | `0x0104` | `-8` | `-24` | `0x0003` |

Final proven code: `0x0104` is the extended downward-thrust primary piece 0 from phase 6
through phase 23. `0x008E` is only the phase 0-1 recovery/startup record for this table.

- Prior Cody result correct: **YES**.
- Andy decode correct for the extended phase: **NO**. The `0x008E` record is real but belongs
  to phases 0-1, not phase 6+.
- Durable arcade model updated with the raw chain: **YES**.

## NATIVE ANCHOR

### Publisher semantics

The single publisher call site is the shift replacement for original BODY inline piece X
store at `arcade_pc 0x05464A`, mapped exactly to `runtime_genesis_pc 0x05481A`. It calls
`native_player_body_anchor_piece` at `runtime_genesis_pc 0x072890`.

The retained BODY inline constructor begins at `arcade_pc 0x0545BA`. Its first iteration is
the original Block-A tuple-0 semantic piece. On that first iteration D2 is 4, so the helper
publishes:

- D4 -> `A5+0x129A`: X computed from signed descriptor X offset, facing transform, and
  player base `A5+0x10BE`;
- D6 -> `A5+0x129C`: Y computed from signed descriptor Y offset, player base
  `A5+0x10C0`, and the original +1 bias.

Both coordinates have already passed `ANDI.W #0x01FF` in the retained arcade constructor.
The helper then emits that same piece into PLAYER_BODY. Blank tuple 0 calls
`native_player_body_anchor_blank`; inactive/all-blank BODY paths call
`native_player_body_anchor_clear`. Normal gameplay player updates invoke BODY and therefore
publish or clear deterministic anchor state. States taking those inactive/all-blank paths do
not publish a piece, but they clear the anchor rather than preserving an arbitrary value.

Attack phase 11 calls `arcade_pc 0x051DAE` before the current frame's BODY call. This is
intentional prior-frame-anchor behavior: original `arcade_pc 0x051E00` copied the previous
Block-A tuple-0 position into a newly activated auxiliary record; BODY later rebuilt tuple 0,
and the later auxiliary update/render used the object record. The current `arcade_pc
0x051E00` replacement at `runtime_genesis_pc 0x052006` likewise reads the retained native
anchor once at activation. Re-anchoring an already active object every frame would not match
that lifecycle.

### Why `0xCCCC` occurs

The captured object was not a correctly mapped Genesis-WRAM object retaining a bad native
anchor. Three retained instructions still acquire the auxiliary array through raw arcade
address `0x0010D338`:

| Purpose | arcade_pc | runtime_genesis_pc | retained instruction |
|---|---:|---:|---|
| update/collision | `0x051650` | `0x051856` | `movea.l #0x0010D338,A1` |
| activation | `0x051DB6` | `0x051FBC` | `movea.l #0x0010D338,A0` |
| three-piece rendering | `0x054754` | `0x054930` | `movea.l #0x0010D338,A0` |

Build 0279 leaves the global raw-WRAM-immediate relocation gate disabled. Consequently
`0x0010D338` addresses ROM, not mapped work RAM. The numbered ROM bytes there begin:

```text
CC CC EE EC CC CC EE EC CC CC CC CC CC CC CC CC
```

The activation loop tests record word 0 against `0x00FF`. ROM word `0xCCCC` fails that test
as though the record were already active, so the `arcade_pc 0x051E00` replacement is never
reached and no native anchor is copied. The renderer then consumes ROM words `0xCCCC` and
`0xEEEC` as object coordinates, producing the malformed `0x09Dx` entries. This exactly
explains the captured values without finding a defect in `native_player_body_anchor_piece`.

The correct mapped semantic object array is `A5+0x1338`, because original arcade WRAM
`0x10D338` is offset `0x1338` from the `A5=0x10C000` base; with current Genesis A5 it is
Genesis-WRAM `0x00FF1338`.

- Native anchor publisher valid: **YES**.
- Can `A5+0x129A/0x129C` be arbitrary after a BODY invocation: **NO**; live/blank/inactive
  paths publish or clear it. It can precede the first BODY invocation during startup, but
  that is not the source of the captured `0xCCCC`.
- Exact bounded correction: replace all three semantic acquisitions of the one auxiliary
  array with `A5+0x1338` / Genesis-WRAM `0x00FF1338`, preserving activation, one-time anchor
  copy, update, and render order. Do not restore Block-A tuple staging and do not re-anchor
  active records every frame.

## PALETTE BUFFER OWNERSHIP

Build 0279 has two SAT buffers, selected for construction by `pc090oj_sat_bank` and selected
for fixup/DMA by `pc090oj_sat_front`. It has one metadata set:
`pc090oj_sat_nibble[80]`, `pc090oj_sat_force_line[80]`, and
`pc090oj_emitted_count`.

| Lifecycle stage | SAT bank | Metadata ownership | Same bank as fixup target? |
|---|---|---|---|
| mainline emit | current `pc090oj_sat_bank` | each emitted slot writes nibble and force-line; finalizer writes count and ready | **YES** |
| ready, before VBlank | same build bank | immutable for that ready pass unless the same bank is rebuilt before commit; such a rebuild rewrites both SAT and metadata coherently | **YES** |
| `vdp_prepare_sprites` | does not rebuild when ready is set | unchanged | **YES** |
| commit publish/flip | `front=bank`, then `bank^=1`, then ready cleared | still describes the just-finished front bank | **YES** |
| `.Lnative_pal_fixup` | selects `pc090oj_sat_front` | loops exactly `pc090oj_emitted_count`, using the corresponding nibble/force-line entries | **YES** |
| SAT DMA | selects the same `pc090oj_sat_front` | fixup is complete | **YES** |
| after VBlank return | displayed front remains old front; next mainline may reuse the single metadata set for the opposite build bank | metadata is no longer a durable description of the displayed bank | **NO**, but fixup is not using it in this stage |

The 68000 VBlank handler is non-preempted by mainline code between bank publication, palette
fixup, and SAT DMA. Thus the single metadata set is sufficient for the current producer ->
commit handoff. The double-buffer metadata race theory is **DISPROVEN** for runtime palette
fixup.

The first ownership mismatch is instead in the corrected-capture diagnostic. At frame-done,
`capture_corrected.lua` selects SAT A/B from `pc090oj_sat_front` but reads
`pc090oj_emitted_count` and `pc090oj_sat_nibble[index]` from the single metadata set. After
commit those metadata bytes may already describe the next build bank. Therefore a CSV row
that pairs displayed line 0 with source nibble 3 does not prove those values belonged to the
same SAT pass.

- Double-buffer metadata race proven: **NO**.
- Exact first ownership/lifetime defect: **diagnostic association only**; post-commit
  displayed SAT is banked, while sampled metadata is unbanked and reusable.
- Bounded correction: no production correction is justified by this theory. A future
  diagnostic must snapshot `{front bank, emitted count, nibble, force line, pre/post tile
  word}` at `.Lnative_pal_fixup`, or bank the diagnostic metadata. Canonical mapping remains
  unchanged.
- Exact value static code cannot decide: the nibble and force-line byte belonging to the
  visibly flashing sword slot at entry to `.Lnative_pal_fixup` for that same front bank.

## LIZARDMAN ACTOR-SCOPED CHECK

Marked frame: `10168` (authoritative `BAD_LIZARD_CLUB` event 13).

Selected actor: index 5, class `0x17`, family 0, facing 0, base X/Y
`0x00CC/0x0081`, base code `0x004B`, attr `0x46`.

| Piece | expected code | expected native X/Y | native code | native X/Y | SAT/art result |
|---:|---:|---:|---:|---:|---|
| 0 | `0x0066` | `0x00BC/0x007A` | `0x0066` | `0x00BC/0x007A` | SAT 25, tile 1128, match |
| 1 | `0x0064` | `0x00BC/0x006A` | `0x0064` | `0x00BC/0x006A` | SAT 26, tile 1096, match |
| 2 | `0x004E` | `0x00BC/0x006A` | `0x004E` | `0x00BC/0x006A` | SAT 27, tile 1256, match |
| 3 | `0x004C` | `0x00BC/0x005A` | `0x004C` | `0x00BC/0x005A` | SAT 28, tile 1216, match |
| 4 | `0x0065` | `0x00CC/0x007A` | `0x0065` | `0x00CC/0x007A` | SAT 29, tile 1112, match |
| 5 | `0x0063` | `0x00CC/0x006A` | `0x0063` | `0x00CC/0x006A` | SAT 30, tile 1072, match |
| 6 | `0x004D` | `0x00CC/0x006A` | `0x004D` | `0x00CC/0x006A` | SAT 31, tile 1244, match |
| 7 | `0x004B` | `0x00CC/0x005A` | `0x004B` | `0x00CC/0x005A` | SAT 32, tile 1200, match |

The expected Y values include the established native BACK_ENEMY `-8` semantic-lane bias so
they are compared in the same coordinate space. SAT raw X/Y apply only the normal `+0x80`
SAT bias. Each SAT tile is the recorded resident tile for that queue code. Runtime DMA uses
`rastan_pc090oj + code*128`; the build-time converter performs only a lossless TL/BL/TR/BR
reordering of the same 128-byte source cell.

- Complete eight-piece correlation: **YES**.
- First mismatch: **none**.
- Classification: **B**. This exact actor pose and converted art are fully identical; no
  queue/art/transform defect was found for actor 5 at the marked frame. The user's visible
  defect remains valid but is not explained by this selected actor's recorded representation.
- Stage-1 Lizardman palette decision changed: **NO**.

## FINAL GATE

- Thrust-tip static contradiction resolved: **YES**.
- Native anchor root cause fully proven: **YES**.
- Exact anchor correction fully bounded: **YES**.
- Residual nibble3->line0 source cause proven: **NO**. The existing same-row association is
  invalidated by diagnostic lifetime; the actual same-bank fixup-time metadata value is not
  present in the capture.
- Lizardman actor-scoped existing-trace comparison complete: **YES**.
- New user gameplay capture justified after this static reconciliation: **YES, only if the
  sword palette flash is pursued**. The one irreducible dynamic fact is the same-front-bank
  sword slot's nibble/force-line and pre/post tile word at `.Lnative_pal_fixup` entry. No new
  Lizardman capture is justified by this check.
- No MAME: **YES**.
- No user gameplay: **YES**.
- No implementation changes: **YES**.
- Build produced: **NO**.
- Counter: **279**.
