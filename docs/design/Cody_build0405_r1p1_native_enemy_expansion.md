# Cody — Build 0405 R1/P1 Native Enemy Expansion and Direct Dispatch

## Result

Build 0405 expands the accepted Build-0404 generic native producer from 8 to
38 orientation-specific direct frame records. It adds exact partial native
coverage for Lizardman, Large Bat, and Small Bat while preserving fallback for
every selector or retained-state tuple outside the proven domains.

The Build-0404 eight-record linear lookup is removed. Runtime classification is
now:

```text
retained actor base
  -> generated 4096-byte base LUT
  -> one generated semantic-usage descriptor
  -> normalized selector + orientation
  -> one 6-byte direct frame-index record
  -> native frame or immediate UNRESOLVED fallback
```

Lookup cost is bounded and does not grow with the total native frame count.

## Scope and semantic cut

- Input baseline: accepted Build 0404.
- Produced build: 0405.
- Build counter: 404 -> 405.
- Semantic cut: retained arcade actor state, AI, movement, lifecycle, animation
  selector, position, and mirror predicate remain arcade-owned. The native path
  attaches after those decisions and replaces only the proven PC090OJ mapping
  program expansion with final Genesis-native pieces.
- Chip-specific tail removed for exact hits: the retained general PC090OJ
  descriptor interpreter is no longer executed for the listed exact native
  tuples.
- Legacy intentionally remaining: the complete accepted generic interpreter
  remains the first-class fallback for every UNKNOWN or rejected tuple.
- No PC080SN, IRQ6 scheduling, controller, watchdog/IPL, WORK/READY/DISPLAYED,
  scrolling, or Phase-D ownership changes were made.

## Static selector proof and coverage

The source program is compositor table 0 at arcade `0x03D09E`. Each listed
program was decoded through its selector table entry, through the `0xFF`
terminator, in exact piece order. Both orientations preserve the original
three-field mirror predicate and actor-relative X transformation.

| Usage | Exact retained identity | Selectors | Programs/pieces | Bank | Status |
|---|---|---|---|---|---|
| Cave block | base `0179`, raw `+05=1E`, comp 0, `+27.bit6=0` | `70` | `03E1C0` / 4 | `3C` | NATIVE_COMPLETE, preserved |
| Burst | base `0275`, raw `+05=0F`, comp 0, `+27.bit6=0` | `9E..A0` | `03E732`/8, `03E753`/9, `03E778`/10 | `30` | NATIVE_COMPLETE, preserved |
| Lizardman | base `004B`, family `+3E=00`, comp 0, `+27.bit6=1` | `17..1F` | `03D5EB..03D6FB`, 8/10 pieces | `36` | NATIVE_PARTIAL |
| Large Bat | base `03F6`, raw record type `+06=0A`, comp 0, `+27.bit6=0` | `B6..B8` | `03E932`/4, `03E943`/2, `03E94C`/4 | `3E` | NATIVE_PARTIAL |
| Small Bat | base `0268`, raw record type `+06=0B`, comp 0, `+27.bit6=0` | `B9..BB` | `03E95D`, `03E962`, `03E967`; 1 piece | `3E` | NATIVE_PARTIAL |

The Lizardman mapping controls contain embedded low nibble 1, but original
arcade `0x03C9E8` replaces the mapping word's low byte from `actor+0x27` when
bit 6 is set. Build 0405 reproduces that dynamic replacement after loading the
baked piece, while retaining baked H/V state. Bats, cave, and burst require bit
6 clear and retain their embedded mapping attributes.

The generated `(code,effective_bank) -> finalized vi` mapping is used for every
palette-divergent source. This protects the shared `0x0A73` Lizardman art from
the distinct Chimera/Four-Armed bank identities. Residency keys remain
finalized vi, not raw arcade code.

### GEN-KU-1

- Lizardman base `004B` is static inside the exact family-0 selector domain.
- Large Bat base `03F6` is static inside the exact raw record-type-`0A` domain.
- Small Bat base `0268` is static inside the exact raw record-type-`0B` domain.
- Cave `0179` and burst `0275` retain their already-proven static identities.
- No runtime `(code,bank)` reconstruction is retained for these exact frames;
  palette-divergent cells are finalized offline.

### GEN-KU-4

Base tile is only a coarse LUT key. Exact acceptance also requires the generated
raw discriminator, compositor, selector range, effective-bank high bits,
actor-attribute policy, and—when `+0x27.bit6` is set—the override low nibble.
`actor+0x38` is never treated as globally unique identity.

## Explicit fallback coverage

- Lizardman selectors outside `17..1F`, wrong family, wrong compositor, wrong
  bank, or missing `+27.bit6` override: fallback.
- Bat creation routes not carrying exact raw `+06=0A/0B`, selectors outside
  their three-value domains, or any other mismatch: fallback.
- Flying Demon, Four-Armed Insect, Chimera, and Valkyrie: all fallback; their
  selector-to-semantic identities were not mechanically closed to the same
  threshold in this bounded task.
- Player fire sword: all 150 keys remain explicit UNRESOLVED fallback.

## Generated artifacts and verification

The existing generator now emits:

- `build/pc090oj_frame_table.bin`: 20,620 bytes;
- `build/pc090oj_frame_index.bin`: 4,500 bytes (600 player native, 150 player
  UNRESOLVED);
- `build/pc090oj_generic_base_lut.bin`: 4,096 bytes;
- `build/pc090oj_generic_usage_table.bin`: 50 bytes / five descriptors;
- `build/pc090oj_generic_frame_index.bin`: 228 bytes / 38 direct records;
- `build/pc090oj_frame_residency.bin`: 13,568 bytes.

Independent frame verification proves every native record's program, ordered
geometry, orientation, source/finalized pattern identity, attributes, size,
and residency set. The new direct-dispatch verifier proves valid hits and
wrong discriminator, selector, compositor, bank, attribute policy, and UNKNOWN
fallbacks. It also rejects any reintroduction of the old scan labels or `DBRA`
inside the generic dispatcher.

The largest newly native frame has 10 distinct requirements, within the
existing bounded 12-item DMA worklist. The existing O(1) reverse-residency map,
reservation/eviction policy, emit-on-miss behavior, and allocator are unchanged.

## Bounded performance sanity

Build 0404's common all-base-miss gate cost approximately 832–856 cycles per
active unresolved actor because it scanned all eight records. Standard MC68000
instruction timing for Build 0405's common in-range/LUT-zero miss—including
caller BSR/miss test, ten-register save/restore, LUT load, and return—is about
302 cycles. An out-of-range base rejects in about 270 cycles. Neither cost
depends on the number of generated native frames.

No Phase-C runtime timing campaign was run. Per the task gate, that comparison
waits for Tighe to accept Build 0405 gameplay and visuals.

## Gates

- frame generator: PASS;
- Layer-1 palette/finalized-pattern verifier: PASS (916 requirements, 0
  mismatches/incomplete/stray writes);
- Layer-2 frame verifier: PASS (600 player native, 38 generic native, 150 player
  UNRESOLVED);
- direct-dispatch verifier: PASS;
- assembler/linker and boot guards: PASS;
- canonical gate: PASS, 231 opcode-replacement sites, Genesis coverage
  `0x1B7EB8`, no gaps/overlaps;
- gameplay-entry gate, GENESIS NTSC MAME: PASS, 240/240 post-entry frames and
  player control observed;
- address errors: 0;
- bus errors: 0;
- illegal instructions: 0;
- crash-handler entries: 0;
- normal GENESIS NTSC MAME trace: 1,798 frames completed;
- VDP ownership: PASS structurally; the new producer only appends through the
  accepted native queue/finalizer/publication path and adds no direct VDP write
  or scheduling ownership;
- five-ROM family verification: PASS;
- Phase-1 seven-epoch Make gate: labeled FAIL because the automated route did
  not complete all seven epochs; its captured target record/epoch installation
  reported PASS. No PC080SN or epoch logic changed in this task.

## Artifacts

All Build-0405 ROMs are 1,801,912 bytes.
Canonical ROM path:
`dist/rastan-direct/rastan_direct_video_test_build_0405.bin`.

| Artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0405.bin` | `af0024630475af16c8e784b88050dcf633180db450c57f8da6f44f8e4549e055` |
| `rastan_direct_video_test_build_0405_d.bin` | `01957e59f49cc0492fbc1ab6370310aed48362be87cae7bd1dba75f186aebdc2` |
| `rastan_direct_video_test_build_0405_s.bin` | `7f0adf284945407f3a4fa3a6ce1b160c90c5a12b4e5e082e34acea976c8521d8` |
| `rastan_direct_video_test_build_0405_do.bin` | `b42f6f6efdca8b4eb4b3f0eda13f183c79ae7214cf54f1953498accfde3f0785` |
| `rastan_direct_video_test_build_0405_c.bin` | `4fb5b9d890011b72e516bfff826be5ab866e4b79aae3bb9cc83f371181032fd3` |

## Files changed

- `apps/rastan-direct/Makefile`
- `apps/rastan-direct/src/pc090oj_assets.s`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `tools/translation/precompute_pc090oj_frame_table.py`
- `tools/translation/verify_pc090oj_frame_table.py`
- `tools/translation/verify_pc090oj_direct_dispatch.py` (new durable verifier)
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- this report and `AGENTS_LOG.md`

Existing project tools reused: the established frame generator/verifier,
Palette-Composer variant index and Layer-1 verifier, canonical build/gates,
gameplay-entry gate, Genesis NTSC MAME trace, address map, and original arcade
Ghidra/decompilation exports.

New tooling created: one durable direct-dispatch verifier integrated into the
normal Makefile dependency chain.

Why new tooling was necessary: the former verifier proved frame payloads but
could not prove bounded lookup semantics, negative dispatch cases, or removal
of the linear scan required by this task.

## Open validation

Tighe must validate ordinary Round-1 gameplay, Lizardman and both bat families
(including heavy/hurry-up conditions), cave block, burst, Rastan, all weapons
including fire-sword fallback, palettes, flips, piece coherence, transitions,
damage/death, and crashes. The accepted Build-0404 first-frame demon-burst
palette defect is unchanged and its cause remains unproven.
