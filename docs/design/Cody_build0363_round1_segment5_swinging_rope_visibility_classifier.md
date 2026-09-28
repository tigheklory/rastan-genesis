# Cody — Build 0363 Round-1 Segment-5 swinging-rope visibility classifier

## Result

Build 0363 replaces the native enemy dispatcher's incorrect blanket rejection of retained actors
whose byte `+0x03` is nonzero with the original arcade's complete state-based visibility decision
from `0x3EFBE..0x3F080`.  The Round-1 Segment-5 swinging rope is state `0x20`, so it now takes the
arcade common wrapped-X predicate and can reach the existing native composite expander and Genesis
SAT queue.

Build 0362 is explicitly rejected: Tighe's BlastEm screenshots showed no rope.  Its animation-zero
correction remains necessary, but was insufficient because the rope was discarded before that code.
Build 0363 passes the automated canonical and GENESIS NTSC gameplay-entry gates.  The automated path
does not reach Segment 5, so final rope visibility and motion remain **USER MUST VERIFY in BlastEm**.

## Build identity

| Item | Value |
|---|---|
| Baseline | Build 0362 (rejected for rope visibility) |
| Produced build | Build 0363 |
| Canonical ROM | `dist/rastan-direct/rastan_direct_video_test_build_0363.bin` |
| Canonical SHA-256 | `414418f307febd88945dec9a9a2b60836bd68cad74ed9362f94a80ffddd1949a` |
| Size | 1,719,992 bytes |
| Counter | 362 -> 363 |
| Canonical opcode-replacement sites | 227 |
| Canonical Genesis-byte coverage | `0x1A3EB8` |
| Canonical gate | PASS |
| GENESIS NTSC gameplay-entry gate | PASS; 240 post-entry frames; zero address/bus/illegal/crash-handler events |
| Seven-epoch gate | FAIL (pre-existing automated gate result; numbered artifact preserved) |
| Standard trace | GENESIS NTSC, 30 seconds; does not reach Segment 5 |

All required same-number artifacts were produced and verified by the default Makefile target:

| Variant | SHA-256 | Size |
|---|---|---|
| canonical | `414418f307febd88945dec9a9a2b60836bd68cad74ed9362f94a80ffddd1949a` | 1,719,992 |
| `_d` | `6d74d0fa22d0902e6f005a6b7de8bd3c7e4a08b5bca3f9772a581921936aee47` | 1,719,992 |
| `_s` | `367eb1830338f87a64cb782895034619902b0da9d03ec872e69cde774f8d15b0` | 1,719,992 |
| `_do` | `57cb754e2b529ba21a289b8ada6caa2b401c2bf6ab9cc0e1d362d33a0acdde57` | 1,719,992 |
| `_c` | `8956e846d85aced2cbb0b6e2ed5772e7bda310579351ba10a91a51a4eeebee40` | 1,719,992 |

## Corrected root cause

The original enemy loop at `0x41E30` checks active byte `+0x00` and state byte `+0x05`.  When
`actor+0x03 == 0`, it renders directly.  When `actor+0x03 != 0`, it branches to `0x3EFBE`, which
applies state-specific visibility rules and then rejoins rendering at `0x41E48` or parks that
actor's fixed PC090OJ band at `0x41EDE`.

The native `native_stage_dispatch_41dae` had reduced that entire decision to:

```asm
tst.b  3(a4)
bne    skip_actor
```

The rope initialization at `0x4103A` sets `actor+0x03 = 1`; materialization as state `0x20` does
not clear it.  Consequently Build 0362 never called `.Lnative_emit_actor_common` for the rope,
irrespective of its now-valid animation index zero, mapping program, artwork, or palette.

Tighe's comparison images match this boundary exactly: ORIGINAL ARCADE MAME shows the curved
nine-piece chain across successive swing frames, while Genesis Build 0362 shows no rope pieces at
all, even though contact remains live.

## Faithful visibility decision

Build 0363 ports the general arcade classifier, not a rope special case:

| State | Original arcade decision retained by the native dispatcher |
|---|---|
| `0x17` | render for `+0x34` bit 7 or wrapped X `< 0x180`; otherwise skip |
| `0x1A` | choose the original progress/flag predicate using `A5+0x13E`, `+0x34`, `+0x32`, and parallel slot flag `+0x742` |
| `0x20` | use the same wrapped-X predicate as state `0x17` |
| `0x13` | render for animation bit 0 or `+0x34` bit 7; otherwise skip |
| `0x22` | preserve the original variant and unsigned `+0x34` window checks |
| `0x15` | preserve the original progress `0x71` and X-sign predicate |
| all other nonzero-`+3` states | render, matching the original default branch |

Skipped actors still advance their fixed semantic band exactly as before.  Admitted actors enter
the unchanged direct-native composite expansion.  Build 0362's removal of the invalid
animation-index-zero rejection is retained, so state `0x20`, animation `0` resolves the nine-piece
rope mapping at arcade `0x3D298` rather than returning empty.

## Architecture boundary

**Semantic cut:** retained arcade actor lifecycle, state, position, animation, priority, palette,
flip, visibility, and fixed ordering.  The new code consumes those retained actor fields and ports
the arcade visibility choice made before object-record generation.

**Chip-specific tail removed:** the original `0x41DAE -> 0x3D054 -> 0x3C902` expansion into
PC090OJ records and PC090OJ hardware consumption remains bypassed.  Admitted actors expand directly
into the native semantic queue and final Genesis SAT entries.

**Transitional compatibility introduced:** none.  No PC090OJ object RAM, D-window read/write,
mirror, shadow, generic chip-address translation, fixed rope coordinates, manually drawn line,
scene check, fallback, NOP, or RTS bypass was added.

Policy checklist:

- semantic rather than chip-write cut: YES;
- complete PC090OJ record-production tail remains bypassed: YES;
- consumes retained arcade semantic state: YES;
- new mirror/shadow/virtual device/projector: NO;
- arcade still owns lifecycle, gameplay, frame progression, and VBlank: YES;
- native helper generates direct Genesis queue/SAT output: YES;
- superseded compatibility introduced or retained by this change: NO.

`specs/palette_decisions.json` was consulted.  No palette decision changes and no affected Palette
Decision IDs exist for this task; the established sprite-bank route is unchanged.

## Validation and limits

- Static arcade authority: canonical Ghidra exports and `build/maincpu.disasm.txt` establish the
  `0x41E40 -> 0x3EFBE` decision and every branch through `0x3F080`.
- ORIGINAL ARCADE MAME evidence: the supplied sequence shows the expected multi-segment curved rope;
  existing user-driven capture ties it to state `0x20`, base `0x00F4`, selector 0, and nine pieces.
- Build pipeline: assembly, 70 shift replacements, 7,214 branch fixes, 630 absolute-long fixes,
  pre/post boot guards, canonical gate, and complete five-ROM artifact-set check pass.
- GENESIS NTSC gameplay-entry gate: PASS through 240 post-entry frames with a valid stack and zero
  address errors, bus errors, illegal instructions, or crash-handler entries.
- GENESIS NTSC standard trace: completed, but does not reach Segment 5 and is not visibility proof.
- BlastEm Build 0363: not run by Cody; final acceptance remains Tighe's test.

Existing project tooling was reused; no new trace, debugger, input, or instrumentation tool was
created.

## Files changed for Build 0363

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `docs/design/Cody_build0362_round1_segment5_swinging_rope.md` (rejection correction)
- `docs/design/Cody_build0363_round1_segment5_swinging_rope_visibility_classifier.md`
- `AGENTS_LOG.md`
- Makefile-owned generated artifacts, manifests, maps, disassembly, counter/ledger, and traces

The Build-0362 Makefile change guaranteeing canonical/`_d`/`_s`/`_do`/`_c` output is retained and
proved by this build.  Pre-existing unrelated working-tree changes were preserved.

## USER MUST VERIFY

In BlastEm, test the canonical Build 0363 through Round 1 Segment 5:

1. Confirm the swinging rope is visible as the same multi-piece curved chain shown in ORIGINAL
   ARCADE MAME, including the initially straighter and later bent swing phases.
2. Confirm the visible chain tracks the grabbable object without blinking, disappearing, or leaving
   detached pieces through a full swing.
3. Confirm grabbing/contact still works and the former `D00462` read freeze does not return.
4. Confirm nearby enemies/effects remain visible and Segment 6 is reachable.
5. Report detach/jump-off behavior separately; this build changes visibility admission only.

