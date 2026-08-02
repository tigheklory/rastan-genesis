# Cody Build 0247 Native Plane A No-Publish Vertical Routing

## Baseline

- Forward-development baseline: Build 0246, counter `246`.
- Candidate produced: Build 0247, counter `247`.
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0247.bin`.
- SHA-256: `30212e73bfbe43396847140bd464f8d800985935a43af3518e7469643a1f2098`.
- Size: `1589332` bytes.
- Rolling artifact: `apps/rastan-direct/dist/rastan_direct_video_test.bin`, same SHA-256 and size.

## Source And Remap Changes

Production/source changes:

- `apps/rastan-direct/src/tilemap_hooks.s`
  - Added native no-publication wrappers:
    - `genesistan_plane_a_pan_publish_entering_rows_up`
    - `genesistan_plane_a_pan_publish_entering_rows_down`
  - Added shared semantic row core `.Lplane_a_publish_logical_row_native`.
  - Added local `strip_src_table[16]` constants from the original Rastan semantic map proof.

Remap/spec changes:

- `specs/rastan_direct_remap.json`
  - Added required helper symbols.
  - Added two byte-neutral `opcode_replace` entries at arcade PCs `0x055704` and `0x055790`.
  - Bumped expected opcode replacement count to `218`.

Canonical verification constants updated:

- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

The canonical opcode replacement count is now `218`; total Genesis byte coverage is now `0x184054` because Build 0247 adds two byte-neutral copied-program routes and `0x208` bytes of Genesis-only helper code.

## Address Table

All arcade/runtime distinctions below are from the generated manifest/disassembly, not arithmetic assumptions.

| Purpose | Arcade PC | Runtime Genesis PC | Replacement/continuation |
|---|---:|---:|---|
| Down no-publication route | `0x055704` | `0x055904` | `jmp 0x000707B2`, `nop`; returns to `0x05590C` |
| Up no-publication route | `0x055790` | `0x055990` | `jmp 0x00070762`, `nop`; returns to `0x055998` |
| Existing descriptor rebuild | `0x055904` | `0x055B04` | unchanged, `jmp 0x00072180` |
| Existing selector-1/2 route | `0x055990` | `0x055B90` | unchanged, `jsr 0x0007061A` |
| Existing selector-0 route | `0x055968` | `0x055B68` | unchanged, `jmp 0x000704E8` |

The manifest shows the new entries as arcade PCs `0x055704` and `0x055790`, with runtime ROM PCs `0x055904` and `0x055990`. It separately retains the older arcade `0x055904` and `0x055990` patched sites at runtime `0x055B04` and `0x055B90`.

## Native Row Contract

The new helper preserves the native replacement policy boundary:

```text
arcade vertical-scroll decision
  -> byte-neutral arcade-PC replacement
  -> bounded Genesis-native semantic row helper
  -> final staged_fg_buffer words
  -> fg_row_dirty
  -> existing VBlank commit
  -> arcade scroll tail
```

For each logical row `0..63`, the helper:

- computes physical resident row as `logical_row & 31`;
- derives source row segment as `logical_row >> 2`;
- derives source row byte offset as `(logical_row & 3) << 3`;
- derives horizontal source base from arcade-owned FG X scroll:
  `source_col_base = (((-a5@0x10AE) & 0x01FF) >> 3) & 0x3F`;
- for each logical destination column `0..63`, uses:
  `source_col = (logical_dest_col + source_col_base) & 63`;
- selects descriptor entry:
  `E = strip_src_table[row >> 2] + (source_col >> 2) * 4`;
- reads semantic attr and metatile pointer from `E` after converting the arcade ROM data address into the generated Genesis ROM data copy range;
- reads the raw tile from `0x200 + dp + ((row & 3) << 3) + ((source_col & 3) << 1)`;
- reuses `.Lplane_a_native_attr_from_word` for the existing palette-correct Plane A attribute conversion;
- writes the final Genesis nametable word directly into `staged_fg_buffer[(row & 31)][logical_dest_col]`;
- marks `fg_row_dirty` for the physical row.

The helper does not use `a5@0x13E` as the arbitrary-row source segment. That is intentional: Andy's Build 0246 pan proof showed `a5@0x13E=1` during the opening pan while source segment zero matched the arcade. Horizontal source is derived from X scroll instead.

## Wrapper Behavior

Up wrapper `genesistan_plane_a_pan_publish_entering_rows_up`:

- full `movem.l %d0-%d7/%a0-%a6` preservation;
- reproduces displaced `10BA -= 10DA`;
- computes old/new `visible_top` from old `10B0` and `(10B0 - 10DA) & 0x01FF`;
- publishes each crossed entering row as `(crossed_visible_top + 31) & 63`;
- jumps to runtime `0x055998` so the original arcade tail stores `10B0`.

Down wrapper `genesistan_plane_a_pan_publish_entering_rows_down`:

- full `movem.l %d0-%d7/%a0-%a6` preservation;
- reproduces displaced `10BA += 10DA`;
- computes old/new `visible_top` from old `10B0` and `(10B0 + 10DA) & 0x01FF`;
- publishes each crossed entering row as `crossed_visible_top & 63`;
- jumps to runtime `0x05590C` so the original arcade tail stores `10B0`.

No persistent previous-scroll state or Genesis-owned frame watcher is introduced.

## Static Verification

Manifest proof:

- `0x055704 -> runtime 0x055904`: `4EF9000707B24E71`.
- `0x055790 -> runtime 0x055990`: `4EF9000707624E71`.
- opcode replacement count: `218`.
- expected total Genesis bytes covered: `0x184054`.

Symbol proof:

- `genesistan_plane_a_pan_publish_entering_rows_up = 0x00070762`.
- `genesistan_plane_a_pan_publish_entering_rows_down = 0x000707B2`.
- existing selector-0 helper remains at `0x000704E8`.
- existing selector-1/2 helper remains at `0x0007061A`.

Final disassembly proof:

```text
55904: 4ef9 0007 07b2  jmp 0x707b2
5590a: 4e71            nop
5590c: 322d 10b0       movew %a5@(4272),%d1
...
55990: 4ef9 0007 0762  jmp 0x70762
55996: 4e71            nop
55998: 322d 10b0       movew %a5@(4272),%d1
```

Helper returns:

```text
707ac: 4ef9 0005 5998  jmp 0x55998
707f4: 4ef9 0005 590c  jmp 0x5590c
```

Compatibility-path audit for the new helper:

- No production `C08000` reads/writes in the new route.
- No `staged_fg_tall_buffer` dependency in the new route.
- No tall-FG projector dependency in the new route.
- No C-window compatibility helper dependency in the new route.
- No collision writes in the new no-publication route.
- Existing legacy/frontend compatibility paths in `tilemap_hooks.s` remain out of scope and are not inputs to this gameplay-native route.

## Build Verification

Command used:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result observed from the release build:

- `GATE_PASS`.
- Numbered artifact produced as `rastan_direct_video_test_build_0247.bin`.
- Build counter advanced to `247`.
- Numbered and rolling ROM SHA-256 match: `30212e73bfbe43396847140bd464f8d800985935a43af3518e7469643a1f2098`.
- Numbered and rolling ROM size match: `1589332` bytes.

The normal release run also produced a stock 30-second MAME trace at:

- `states/traces/rastan_direct_video_test_build_0247_mame_30s_20260801_190014/`

That stock trace reached `frames=1798`, reported no unmapped memory addresses, and showed `fg_cwindow_live count=0`, but it is not a no-publication-row proof.

## Runtime Trace Attempt

Focused trace artifacts are preserved at:

- `states/traces/build0247_plane_a_no_publish_vertical_runtime/`

Runs performed:

- `build0247_no_publish_vertical_trace.tsv`
- `build0247_scroll_path_census.tsv`
- `build0247_10b0_writers.tsv`
- `build0247_scroll_field_writers.tsv`

Important result:

- The automated MAME Genesis startup reached gameplay state `2/3/0` and sampled final FG Y scroll `10B0=0x0149`.
- The focused code-fetch taps did not observe execution of `0x055904`, `0x055990`, `0x070762`, or `0x0707B2` in that automated path.
- Expanded scroll-field write watches observed the startup clear at `0x03B0FE` but did not observe the later mapped scroll movement writes, despite sampled `10B0` reaching `0x0149`.

Therefore, the automated trace does not prove the required opening-pan no-publication row sequence for Build 0247. It also does not disprove the implemented route; it shows that this local MAME Lua watch configuration/path did not capture the requested runtime boundary. The implementation is statically wired and build-verified, but the following runtime items remain user/next-agent verification targets:

- opening pan no-publication hooks execute;
- visible_top `1 -> 23` publishes logical rows `33 -> 54`;
- physical rows `1 -> 22` become nonzero in `staged_fg_buffer`;
- `fg_row_dirty` bits are set before VBlank;
- initial Plane A is coherent immediately after the pan;
- horizontal walking still streams correct columns;
- palette remains correct;
- no exception/reset/freeze/reg corruption occurs.

## User Test Scope

Use Build 0247 for a focused visual/runtime check:

1. Start Stage 1.
2. Watch the opening pan settle before moving horizontally.
3. Confirm the foreground does not require column-by-column repair after the pan.
4. Walk right briefly to confirm horizontal streaming still behaves normally.
5. Confirm Plane A palette and title/frontend remain stable.

## Conclusion

Build 0247 implements the requested byte-neutral native no-publication routes and shared semantic row helper without adding PC080SN compatibility state. Static manifest, symbol, and final disassembly checks pass. Runtime automation did not exercise or capture the no-publication sites, so visual/manual validation remains required before accepting the build as fixing the opening-pan Plane A starvation.
