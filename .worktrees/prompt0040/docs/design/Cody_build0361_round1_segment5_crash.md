# Cody — Build 0361 Round-1 Segment-5 BlastEm crash

## A. User-observed failure and evidence boundary

Tighe supplied the BlastEm screenshot and the exact failure observation:

> Round 1, Sub-Round 1, entering Segment 5: machine freeze due to read from `0xD00462`.

This task is static analysis and a test build. I cannot run BlastEm, ran no MAME, and make no
claim about a faulting runtime PC or register values. The address `0xD00462` and scene timing are
user-provided evidence. Older repository traces are reused only to correlate the human segment
number with retained arcade progression state.

## B. Exact Segment-5 progression/state

Round 1 Sub-Round 1 uses `A5+0x013E` as the progression/map-record selector. Human Segment 5 is
exactly `A5+0x013E == 0x0005`. The neighboring states are:

| Human segment | `A5+0x013E` | scene index (`0x50EE0`) | section kind (`0x50F6B`) |
|---:|---:|---:|---:|
| 4 | `0x0004` | 4 | 0 (Phase 1) |
| 5 | `0x0005` | 5 | 0 (Phase 1) |
| 6 | `0x0006` | 6 | 0 (Phase 1) |

Durable Build-0348 trace evidence first sampled records 4/5/6 at frames 3132/4286/5415. This is
prior evidence, not a new run. Segment 5 changes residency package 6→2; Segment 6 remains in package
2. Current offline preload counts are 1123/1002/1153 tiles for Segments 4/5/6. Those tile/map
differences are real but cannot form a `0xD0xxxx` effective address: their consumers remain the
PC080SN plane/collision pipelines.

The first relevant actor-side difference forced by the observed effective address is a live
materialized contact source. An `O`/`P`/`Q` marker routes through `0x41BCA`, which assigns actor
state `0x20` and calls `0x41BEE`. That function makes the contact-source table live:

```text
A5+0x1280 = 1
entry = A5+0x1282 + 6*actor.variant_2f
entry.active = 1
entry.token = 0xD00460 + 0x50*(A5+0x0214 actor iteration)
```

The exact `D00462` read proves that one such registration is active when the user enters Segment 5,
because this is the only statically identified constructor/consumer chain for that address. The
per-scene marker roster is not independently enumerated, so this report does not claim which
Segment-5 cell first materialized it or exclude carry-in state. It does prove that the stale reader,
not a malformed Segment-5 BG/FG pointer, is the invalid Genesis operation.

## C. Segment 4/5/6 data comparison

| Surface | Segment 4 | Segment 5 | Segment 6 | Crash relevance |
|---|---|---|---|---|
| Progression | `0x0004` | `0x0005` | `0x0006` | selects distinct map/marker record |
| Section kind | 0 | 0 | 0 | no Phase-2 dispatcher change |
| Residency package (prior trace) | 6 | 2 | 2 | graphics residency only |
| Plane preload size | 1123 | 1002 | 1153 | PC080SN data; cannot make `D00462` |
| Contact registration | no live failing observation | active registration is implied by exact `D00462` read | later progression continues | activates `A5+0x1280/1282` reader |
| Registered token | inactive/unused on the observed route | `D00460 + 0x50*n` | same format when registered | exact PC090OJ object-RAM address class |

No Segment-5 BG/FG descriptor, scroll-table entry, ROM pointer, sign extension, byte swap, or
code relocation produces the high word `0x00D0`. The only exact formation is the original arcade
PC090OJ record-band contract described below.

## D. Exact formation of `0xD00462`

Formation is **PROVEN statically** from original instructions:

1. Arcade `0x41BEE` computes `0xD00460 + 0x50*actor_index` and stores it in an active six-byte
   registration at `A5+0x1282`.
2. Arcade `0x51AB6` loads that long token into `A0` at `0x51AE8`.
3. Its nine-record loop begins with `addq.l #2,A0` at `0x51AF0`.
4. It reads the Y word with `move.w (A0),(A1)+` at `0x51AF2`.
5. For actor index zero: `0xD00460 + 2 == 0xD00462`.

The loop then adds four, reads X at record offset `+6`, and adds two to reach the next eight-byte
record. This proves both the address and its intended field: Y of the first PC090OJ object record.
No literal `D00462`, corrupted pointer, or runtime-PC inference is needed.

## E. Relevant arcade functions decompiled

The previously uncovered functions are now complete in auditable C:

- `raw/00051ab6.c`: three registrations → 27 `{Y,X}` gameplay coordinate pairs.
- `raw/00051b04.c`: unchanged player/world contact consumer and the `0x51B74` source-third
  classifier.
- `rastan_player_world_contact.c`: semantic producer/consumer contract and native cut.

`raw/00041bee.c` was corrected to identify `0xD00460` as PC090OJ object RAM (ten eight-byte records
per `0x50` band), not a ROM/graphics table.

## F. Original arcade intended pointer/data

On arcade hardware, `0xD00000..0xD03FFF` is live PC090OJ object RAM. The intended chain is:

```text
retained actor + compositor mapping program
  -> PC090OJ records at D00460 + actor_index*0x50
  -> 0x51AB6 reads record Y@+2 and X@+6
  -> A5+0x1134 contains 27 gameplay-owned Y/X pairs
  -> 0x51B04 performs player/world contact selection
```

Thus `D00462` is correct and mapped on the arcade. It is a hardware-data address, not code and not
a ROM data pointer eligible for ordinary address relocation.

## G. Genesis divergence

The Genesis renderer now cuts at retained actor semantics and emits final native queue/SAT entries.
The PC090OJ record-construction/readback tail is retired; there is intentionally no object-RAM
mirror or D-window device. However, the producer `0x41BEE` still retained the old band token for
source identity, and copied arcade `0x51AB6` still dereferenced it. Build 0346 only rebased the
registration-table base from arcade WRAM `0x10D280` to Genesis WRAM `0xFF1280`; that exposed the
correct stored token but left the obsolete chip-tail read intact.

Before Build 0361, authoritative mapping placed arcade `0x51AB6` at Genesis `0x51CC2`, with the
first hardware read later in the copied body. After Build 0361, `address_map.json` maps:

| Arcade PC | Build-0361 Genesis PC | Meaning |
|---:|---:|---|
| `0x41BEE` | `0x41DEE` | contact-source registration |
| `0x51AB6` | `0x51CC2` | patched `JSR 0x7337E; RTS` |
| `0x51B04` | `0x51CCA` | unchanged contact consumer |
| `0x51B74` | `0x51D3A` | unchanged third classifier |

The new negative shift at `0x51AB6` is `-70` bytes. Downstream references were reflowed by the
shift-table patcher; no fixed `+0x200` assumption was used.

## H. Root cause

The root cause is a surviving PC090OJ chip-tail consumer below an already-retired rendering
boundary. Segment 5 merely activates it. `0xD00462` is neither random nor a bad relocated ROM
pointer: it is the exact first word the arcade is supposed to read from real object RAM. On Genesis,
that object RAM no longer exists, so copied `0x51AB6` violates the direct-native architecture.

## I. Exact patch

The complete original `0x51AB6..0x51B02` function (78 bytes) is a `shift_replacements` entry:

```text
old: arcade PC090OJ registration/record walker (78 bytes)
new: JSR genesistan_native_contact_coords_51ab6; RTS (8 bytes)
```

The native helper:

1. reads the retained registration table at `A5+0x1282`;
2. decodes `(token - 0xD00460) / 0x50` to the owning actor in `A5+0x2C8`;
3. resolves the same compositor-selector/animation mapping program used by native sprite output;
4. computes the first nine semantic Y/X pairs directly into the existing gameplay-owned
   `A5+0x1134` list;
5. writes the original `0x01FF/0x01FF` parked pairs for inactive/terminated entries.

The downstream contact consumer is unchanged. There is no D-window read handler, shadow RAM,
PC090OJ tuple, NOP padding, RTS bypass, fallback path, or `segment == 5` condition. The semantic cut
is actor mapping program → gameplay contact coordinates; the removed chip tail is actor program →
PC090OJ records → PC090OJ readback → gameplay contact coordinates.

## J. Files changed by this task

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `specs/rastan_direct_remap.json`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- `analysis/decompilation/c/raw/00041bee.c`
- `analysis/decompilation/c/raw/00051ab6.c`
- `analysis/decompilation/c/raw/00051b04.c`
- `analysis/decompilation/c/rastan_player_world_contact.c`
- `analysis/decompilation/c/function_coverage.csv`
- `analysis/decompilation/c/README.md`
- this report and `AGENTS_LOG.md`

Generated Makefile-owned manifests, maps, disassembly, counter/ledger state, and ROM artifacts were
regenerated. Protected bestiary/graphics-manifest/Claude/boss/palette files were not touched by this
task; pre-existing worktree changes in those files were preserved.

## K. Static validation and user test

Static validation:

- assembly: PASS;
- decompilation coverage guard: PASS (88 rows, 74 COMPLETE);
- decompilation fidelity guard: PASS;
- C syntax over semantic + raw tree: PASS;
- shift reflow: PASS (70 replacements, 7214 branch fixes, 630 absolute-long fixes);
- pre/post boot guards: PASS;
- canonical gate: `GATE_PASS`;
- final replacement bytes at `0x51CC2`: `4EB90007337E4E75`;
- final ROM contains no literal `0x00D00462`;
- MAME/runtime validation: NOT RUN, by directive.

Build artifact:

```text
dist/rastan-direct/rastan_direct_video_test_build_0361.bin
size: 1,719,992 bytes
SHA-256: b8cc28d75d07e50fc194171a91a446adc649626f8296415b839a8f617bd4fa62
counter: 361
ledger: canonical=PASS, entry=FAIL, epoch=FAIL (both runtime gates deliberately skipped: NO MAME)
```

Tighe must validate in BlastEm by playing Round 1 Sub-Round 1 through the Segment-4→5 boundary,
then continuing into Segment 6. Confirm: no `D00462` freeze, normal movement/contact behavior around
the Segment-5 marker object, and no new visual or collision regression. Runtime success is not
claimed until that test is complete.
