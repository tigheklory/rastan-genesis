# Cody — Build 0362 Round-1 Segment-5 swinging-rope visibility

> **REJECTED / NOT ACCEPTED (Tighe BlastEm result, 2026-09-22):** the swinging rope remained
> completely absent.  Build 0362 corrected a real animation-index bug, but it did **not** satisfy
> the visibility task.  The pre-test causal conclusion below is superseded: the earlier
> `native_stage_dispatch_41dae` gate still discarded every actor with `actor+0x03 != 0`, while the
> arcade routes those actors through its state-based visibility classifier at `0x3EFBE`.  The
> Segment-5 rope retains `actor+0x03 == 1`, so it never reached the corrected compositor.  Build
> 0363 ports that general classifier.  This report remains as Build-0362 provenance, not acceptance.

## Result and evidence boundary

Build 0362 removes the native compositor's invalid rejection of animation/program index `0x00`.
That index is the first legal swinging-rope mapping, not an inactive marker. The same correction is
applied to Build 0361's direct contact-coordinate reconstruction, so visual expansion and gameplay
contact now resolve the same retained mapping program.

The ROM passes the canonical gate and the automated GENESIS NTSC gameplay-entry gate. The automated
run does not reach Segment 5, so visible rope motion, the Segment 4 -> 5 -> 6 traversal, and the
absence of the former `0xD00462` fault at that boundary remain **USER MUST VERIFY in BlastEm**. This
report does not claim a BlastEm observation that Tighe has not made.

## Build identity

| Item | Value |
|---|---|
| Agent / task | Cody / Round-1 Segment-5 swinging-rope visibility |
| Baseline | Build 0361 |
| Produced build | Build 0362 |
| ROM | `dist/rastan-direct/rastan_direct_video_test_build_0362.bin` |
| SHA-256 | `caedc8b93397e1760c86e71e5ae76f3aeac5feb98aa42c0d7a9374c91fdee0d0` |
| Size | 1,719,992 bytes |
| Counter | 361 -> 362 |
| Canonical opcode-replacement sites | 227 |
| Canonical Genesis-byte coverage | `0x1A3EB8` |
| Canonical gate | PASS |
| Gameplay-entry gate | PASS |
| Seven-epoch gate | FAIL (pre-existing automated gate result; artifact preserved) |
| Rack-advance variant | `rastan_direct_video_test_build_0362_c.bin`, SHA-256 `b7d959f958beeee2258b9984cb1d4b735ee6df7e5c3b65618ce064540949c7f9`, 1,719,992 bytes |

## Exact actor identity

The Segment-5 object is the `A5+0x02C8` actor-slot-zero chain whose visible base is `0x00F4`.
This is proven rather than inferred from the Bestiary:

1. Original-arcade marker dispatch at `0x41362` routes marker `'H'` (`0x48`) through
   `0x41B6C`, assigning state `0x1E`, initial animation `0x70`, and the round-dependent position
   from `0x41B90`.
2. State `0x1E` at arcade PC `0x40E88` rechecks the stored marker-cell address. At Round-1
   Segment-5 progression (`A5+0x013E == 5`, therefore `<0x18`), disappearance of `'H'` calls
   `0x4103A`, assigns base `0x00F4`, and retargets to marker `'O'` (`0x4F`).
3. The latent scanner sees `'O'` and `0x41BCA` assigns state `0x20`, positions the actor, and calls
   `0x41BEE` to register its nine-piece contact source.
4. The existing ORIGINAL ARCADE user-driven capture records, in Section/Segment 5 at frame 2631,
   active actor `0x10C2C8` with animation `0x00`, state `0x20`, mode flag `+0x03 == 1`, compositor selector
   `0`, variant `0`, attribute override `0`, and base `0x00F4`. At frame 2632 the corresponding
   PC090OJ band emits records 140..148 as a nine-piece vertical chain. Later captured forms bend the
   individual pieces as the retained state advances its animation program.
5. The graphics corpus independently classifies owner `actor_2c8/0x00F4` as
   `object:hazard.swinging_rope` and records it only in R1/P1 Segment 5.

The initial visible state at Segment 5 is therefore:

```text
marker H
  -> state 0x1E / anim 0x70
  -> marker-chain transform at 0x40E88
  -> base 0x00F4 / retarget O
  -> state 0x20 / anim 0x00 / selector 0 / variant 0
  -> animated swinging rope
```

The state-`0x20` decompilation historically calls this registration a torch/light source. The
Segment-5 dynamic owner, the nine-piece chain output, and the captured graphics identify this
specific Round-1 instance as the swinging rope; the generic state/registration naming is not a
contradiction.

## Swinging rope versus stationary climbable rope

These are separate visual systems:

| Object | Semantic/visual owner | Rendering form |
|---|---|---|
| Segment-5 swinging grab-able rope | retained `A5+0x02C8` actor, base `0x00F4`, state chain `0x1E -> 0x20` | PC090OJ sprite artwork in arcade; native Genesis sprite queue/SAT in Build 0362 |
| Earlier stationary/climbable rope terrain | PC080SN Plane-B map records 2/3, sources `0xD31C/0xF31C`, attr `0x0002`, with a separate collision channel | background name-table cells; its 12 retained tile identities and wide Y envelope are unrelated to this patch |

No Plane-B rope residency rule was changed.

## Mapping, pieces, graphics, and palette

Selector `0` at arcade `0x3D054` chooses table `0x3D09E`. Animation `0x00` reads table offset
`0x01FA`, yielding mapping program `0x3D298`. Its first legal representation is nine ordinary
four-byte mapping pieces followed by `0xFF`:

```text
control/Y/code/X:
00/0B/00/00  00/15/00/00  00/20/00/00
00/2B/00/00  00/35/00/00  00/40/00/00
00/4B/00/00  00/55/00/00  00/60/00/00  FF
```

Thus the rope is not a single large sprite and not a hard-coded line. It is a nine-piece composite
of 16x16 cells. The state-`0x20` animation schedule at `0x40FE0` selects further legal programs,
which produce the bending/swinging forms. The ordinary mapping-program semantics already supported
by `.Lnative_emit_actor_common` supply each piece's retained actor-relative Y, tile delta, and X.

Artwork comes from PC090OJ cell codes rooted at `0x00F4`; the captured corpus covers physical cells
`0x0F4..0x0FF`. None is blank (the adjacent blank sentinels are `0x0F3` and `0x100`). The existing
native PC090OJ cell loader/finalizer maps those retained codes to Genesis sprite patterns.

The real arcade records carry word-0 palette nibble `0`. With the sprite color-bank base, that is
effective arcade bank `0x30`; Round 1 loads palette-pool block 11 from ROM source `0x4FE62`. The
existing `current_sprite_palette_map` route converts that semantic bank to a Genesis CRAM line when
the native SAT word is finalized. `specs/palette_decisions.json` was inspected; no palette decision
changes in this task, so no Palette Decision ID or registry entry is affected.

## Arcade and Genesis chains

Original arcade:

```text
H marker -> state 0x1E -> base 0x00F4 / O retarget -> state 0x20 update
-> animation byte +0x01 -> selector-0 table -> 0x3D298/following mapping programs
-> 0x3C902 composite expansion -> PC090OJ records D00460..D004A7
-> visible nine-piece swinging chain
```

Genesis Build 0361 before this fix:

```text
same marker/materialization/state/update (live)
-> same animation selector and mapping program (live)
-> native_stage_dispatch_41dae (live)
-> .Lnative_emit_actor_common
-> rejects actor because +0x01 == 0
-> no native queue pieces -> no SAT rope
```

Genesis Build 0362:

```text
same retained actor semantics
-> same selector-0 animation program, including legal index 0
-> native composite expansion (up to the actor's ten-piece budget; program terminates at nine)
-> native back/enemy semantic queue
-> resident PC090OJ cells + palette route
-> Genesis SAT entries
```

This was an incomplete pre-test diagnosis.  The animation-zero gate was invalid, but the first
observed loss for this rope occurred one level earlier: the native dispatcher's broad `+0x03`
rejection prevented descriptor selection and queue/SAT emission.

## Root cause and patch

`A5 actor + 0x01` is the animation/mapping-program index. The native compositor incorrectly treated
zero as an inactive/class sentinel:

```asm
tst.b  1(a4)
beq    return_without_emission
```

The original `0x41DAE` renderer tests actor activity at `+0x00` and state at `+0x05`; it does not
reject animation zero before calling `0x3D054`. The `0x00F4` rope's first program is explicit proof
that zero is valid.

Build 0362 removes that invalid check from the general native actor compositor. It also removes the
same copied assumption from `genesistan_native_contact_coords_51ab6`, ensuring Build 0361's
PC090OJ-free contact reconstruction resolves animation zero instead of parking its coordinates.
This second removal is inseparable semantic consistency, not a detach/jump-off change.

No Segment-5 test, rope identity test, fixed coordinate, manual sprite, actor-state override,
PC090OJ shadow, D-window access, fallback, NOP, or RTS bypass was added. Player release behavior was
not modified.

## Architecture and legacy status

The semantic cut remains:

```text
retained arcade actor/state/animation
-> retained mapping/compositor semantics
-> native Genesis queue/SAT
```

The removed chip tail remains the original mapping expansion into PC090OJ object records and their
hardware consumption. Build 0362 does not restore any part of that tail and introduces no object
RAM. This is a correctness repair inside the already-native compositor; no additional shared
legacy producer is retired in this build. Existing non-gameplay PC090OJ compatibility noted by
earlier architecture reports remains intentionally outside this task.

## Validation

Static/original-arcade evidence:

- canonical Ghidra exports and original disassembly prove the marker, state, renderer, and mapping
  control flow;
- existing ORIGINAL ARCADE user-driven full capture proves the Segment-5 actor fields and nine
  emitted records;
- copied ROM bytes at final Build-0362 offset `0x3D498` match the complete animation-0 rope program;
- the final canonical ROM contains no instance of the removed active-plus-animation-zero rejection
  sequence;
- JSON syntax checks pass for the remap and palette registries;
- assembly, shift reflow (70 shift replacements, 7,214 branch fixes, 630 absolute-long fixes),
  pre/post boot guards, and canonical gate pass.

Runtime evidence:

- **ORIGINAL ARCADE MAME (`rastan`)**, pre-existing Tighe-driven capture: R1/P1 Segment 5 actor
  `0x00F4`, state `0x20`, animation `0`, and nine PC090OJ pieces observed.
- **GENESIS NTSC MAME (`genesis`)**, Build 0362 automated gameplay-entry gate: PASS through 240
  post-entry frames; zero address errors, bus errors, illegal instructions, or crash-handler entries;
  stack valid.
- **GENESIS NTSC MAME (`genesis`)**, standard 30-second execution trace: 1,798 frames recorded and
  live VDP writes observed. This trace does not reach Segment 5 and is not rope-visibility proof.
- **BlastEm, Build 0362 (Tighe): FAIL.** The object remained grabbable but the swinging rope was not
  visible in any supplied frame.  This rejects Build 0362 as the requested visibility fix.

The default Makefile preserved Build 0362 after canonical and gameplay-entry PASS. Its first
rack-advance attempt exposed an obsolete `+0x1000` variant-coverage adjustment: Build 0361's helper
growth had already moved canonical and cheat configurations into the same aligned coverage page.
The Makefile now applies the common `0x1A3EB8` invariant to both, successfully produced Build
0362 `_c`, and ends every default/release build with a mandatory check for the complete canonical,
`_d`, `_s`, `_do`, and `_c` artifact set. The standard seven-epoch gate remains failed, as on recent
baselines; it is not presented as rope evidence.

Existing project tools reused:

- canonical Ghidra exports, `build/maincpu.disasm.txt`, and reconstructed actor C;
- `analysis/graphics_optimizer/round1_phase1_corpus/full_capture/` and the arcade graphics oracle;
- Makefile-owned canonical build/gates and standard GENESIS NTSC trace;
- existing gameplay-entry and sprite/palette corpus outputs.

New tooling created: none.

Why new tooling was necessary: not applicable.

## Files changed by Build 0362

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/Makefile`
- `docs/design/Cody_build0362_round1_segment5_swinging_rope.md`
- `AGENTS_LOG.md`
- Makefile-owned generated artifacts, maps, manifests, disassembly, counter/ledger, and traces

Pre-existing uncommitted Build-0361, boss/decompilation, Bestiary, graphics-manifest, and unrelated
workspace changes were preserved and are not attributed to Build 0362.

## User validation result

**FAILED:** Tighe's screenshots show the Genesis Build-0362 scene with no rope, versus the ORIGINAL
ARCADE MAME sequence showing the curved nine-segment chain throughout its swing.  Do not use or
accept Build 0362 for this task.  Build 0363 is the corrected successor requiring visual validation.
