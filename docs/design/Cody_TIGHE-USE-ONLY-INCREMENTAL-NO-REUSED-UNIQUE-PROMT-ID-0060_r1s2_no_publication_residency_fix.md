# R1-S2 Plane A no-publication residency fix

Date: 2026-11-03

Agent: Cody

Assignment: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0060`

Baseline: Build 0528 production / Build 0529 gameplay evidence

Candidate: Build 0530

## Result

Build 0530 corrects the confirmed destructive Plane A overwrite without adding a shadow tilemap,
full-scene backing map, hardware-emulation layer, or duplicate graphics buffer.

The existing `staged_fg_buffer` remains the one final native 64x32 Plane A resident image. A new
32-byte provenance vector, `plane_a_resident_logical_rows`, records which logical row (0..63) owns
each physical row (0..31). Values are stored as logical row+1 so zero remains invalid.

On original arcade no-publication movement:

- if the requested logical row already owns its physical slot, the Genesis helper now returns
  without changing staged words or setting `fg_row_dirty`;
- if the slot contains the N+32 alias or is invalid, the existing predecessor/current materializer
  still builds the genuinely required row, marks it dirty, and then changes its provenance;
- ordinary selector-1/2 row publication changes provenance only after its complete 64-cell row has
  run;
- scene/checkpoint reseed establishes all 32 identities from the final post-`$0504FA` camera after
  the existing bounded replay.

The candidate therefore preserves already-correct current rows while retaining initial scene
construction, predecessor materialization, both scroll directions, reversals, and checkpoint
reseed behavior. It is pending Tighe's conventional and jump-assisted R1-S2 gameplay acceptance.

## Original arcade justification and semantic cut

The canonical Ghidra export shows:

- `$055704/$055708` updates `A5+$10BA` on one no-publication direction;
- `$055790/$055794` updates `A5+$10BA` on the other direction;
- control continues into the scroll-Y store tail without calling the ordinary `$055A14` name-RAM
  author;
- `$0558E0..$0558E8` advances the record and preserves the completed selector, but it does not
  erase the per-physical-row history already resident in PC080SN name RAM.

The semantic cut remains:

`arcade semantic publish/no-publish decision -> final Genesis Plane A resident words`

The retired chip tail is the C08000/name-RAM authoring mechanism. A semantic no-publication event
must preserve exact resident contents. Genesis still needs explicit materialization only when its
32-row plane maps a newly requested logical row over the other 64-row logical alias.

## Exact assembly correction

Source commit: `974dc0b0c9f3c351536d982e1f0e9dfa2cc45d38`.

Changes in `apps/rastan-direct/src/tilemap_hooks.s`:

1. `:775-789` records the logical-row owner after an ordinary selector-1/2 row completes.
2. `:878-895` installs the 32 logical owners after scene/checkpoint replay using the final live
   `A5+$10B0` visible top.
3. `:1442-1452` compares the requested logical row+1 with the physical slot's provenance before
   any source selection. An exact match branches directly to the balanced return.
4. `:1605-1618` marks a genuinely materialized row dirty and changes its owner only after all row
   words are complete.
5. `:5366-5372` allocates the 32-byte identity vector beside existing native state.

This is provenance only: 32 bytes versus the 4,096-byte existing final name-word buffer. It contains
no tile words, metatiles, attributes, scene graphics, or PC080SN address image.

## Confirmed bad-sequence regression

`tools/translation/verify_bg_a_incremental_background.py` now models scene seeding, ordinary row
ownership, exact-logical no-publication retention, and N/N+32 alias materialization. It explicitly
covers every row demonstrated by the Build 0529 traces:

- record 17 logical rows 44-46;
- record 17 logical rows 12-14;
- record 21 logical rows 60-62;
- record 21 logical rows 35-42.

For each case, the verifier installs current-record contents through the ordinary publisher, runs a
no-publication event for the same logical row, and requires both the content and owner to remain
unchanged. Separate rows 1, 12, 31, 44, and 63 test the opposite case: an N+32 alias must invoke
predecessor materialization and acquire the requested identity.

The existing trace hashes remain the runtime evidence for why the retention branch is required.
For example:

| Record / logical row | Current hash destroyed in Build 0529 | Wrong later predecessor hash |
|---|---:|---:|
| 17 / 44 | `DACFC3EC` | `2E41754F` |
| 17 / 45 | `1455A5FE` | `5E85E216` |
| 17 / 46 | `753F8C6F` | `A55C3DE9` |
| 17 / 12 | `E30C302B` | `CC9C8DAB` |
| 17 / 13 | `C2EA740F` | `B005C791` |
| 17 / 14 | `9615797B` | `E7B13175` |
| 21 / 60 | `68862F2B` | `F78C9F9D` |
| 21 / 61 | `6816070F` | `3B256D05` |
| 21 / 62 | `DB5D887B` | `50EE7F45` |

Build 0530's provenance match suppresses those later writes because the ordinary current row still
owns the same logical identity. The captured Build 0529 trace directories were not modified or
rerun.

## Verification

Completed checks:

- assembly of `tilemap_hooks.s`: PASS;
- full-span background coherence gate: PASS, including current-row retention and N/N+32
  predecessor materialization;
- selector-0 equivalence: PASS, 163,840 coordinate/front cases and 934,928 descriptor cases;
- selector-1/2 equivalence: PASS, 128 destination-row, 1,869,856 visual/attribute, 1,869,856
  descriptor, and 4,096 row/top residency cases;
- scene/checkpoint/pan gate: PASS, including 16,384 predecessor cells and 1,138,688 authored
  descriptor cells;
- native PC080SN metatiles, Plane B visual records, collision/visual separation, palette families,
  sprites, title, HUD, item screen, boot guards, branch reflow, and relocation gates: PASS;
- canonical gate: PASS;
- gameplay-entry gate: PASS;
- six Round-1 epoch/package cases: PASS;
- mandatory Genesis NTSC trace: PASS, 1,798 frames, no address/bus/illegal/crash faults;
- complete canonical/diagnostic/score/display-off/cheat/full-HUD/invincible family: PASS;
- normal R1-S2 Genesis NTSC functional start: PASS at frame 412, stage `$0010`, record `$0011`,
  both planes 2,048 nonzero words, Plane A/B misses 0;
- invincible R1-S2 functional start: same PASS state.

No Plane B, PC090OJ sprite, collision, movement, palette, audio engine, checkpoint, or gameplay
source was changed. The direct-start variants make the existing two expected build-time changes:
stage selector `$FF->$DF` at ROM `$05FF9F` and natural R1-S2 music command `$25->$27` at
`$0508A3`.

## Build 0530 artifacts

All artifacts are 3,792,568 bytes and use source commit `974dc0b0`. Counter and consumed ledger
advanced 0529 -> 0530; the ledger records canonical/gameplay-entry/epoch PASS.

| Artifact | Purpose | SHA-256 |
|---|---|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0530.bin` | normal candidate | `dbbc1377286e37a7d61b3ac75df613db6a2f9734a009f0f58e7e02b74c0a248b` |
| `dist/rastan-direct/rastan_direct_video_test_build_0530_S1-2.bin` | normal R1-S2 direct start | `bfb3ed8ffc0e6cfe24cac80a6a1be0523f49cec299393ce4c3f7409ae936a23d` |
| `dist/rastan-direct/rastan_direct_video_test_build_0530_d.bin` | VBlank raster diagnostic | `1e8d6a71480a1aa655264f3a3e3de2705a02360037156bd8292b7d87b60b0549` |
| `dist/rastan-direct/rastan_direct_video_test_build_0530_s.bin` | score metric diagnostic | `21304e341036909c6bf7536e31366c6c27fd280ed890d0844ab03a2430955201` |
| `dist/rastan-direct/rastan_direct_video_test_build_0530_do.bin` | display-off diagnostic | `2f0028fdd83355176decd74e761c2a7c2462121b8c25eaaa3005d07ae2d61a17` |
| `dist/rastan-direct/rastan_direct_video_test_build_0530_c.bin` | rack-advance diagnostic | `554fe972bac2edd45589db43d7b6da77c6c651b87e923c72c983c2907cb59661` |
| `dist/rastan-direct/rastan_direct_video_test_build_0530_full_hud.bin` | full-HUD comparison | `a5c6fc416f242d7e1133f4ae37a0019fe030a9a4ff90a4291803fe54928be967` |
| `dist/rastan-direct/rastan_direct_video_test_build_0530_invincible.bin` | arcade-gate invincibility | `a0fff14f83a848f91e63d1413f7a2373581e4a4fc30d129f7b8e5cb4cf74a4e2` |
| `dist/rastan-direct/rastan_direct_video_test_build_0530_invincible_S1-2.bin` | repeat of Build 0529 manual test | `6f2afedca192b275bf3068c9e83b534320ca81cc9c6938940093ef78616c65b3` |

## Bounded remaining uncertainty and acceptance

Build 0530 directly fixes the demonstrated current-row destruction. It does **not** prove that the
sparse predecessor-only corruption markers are fixed. Their first N/N+32 materialization still uses
the Build 0528 predecessor source logic, because the existing traces lack the pre-write resident
row/cell oracle needed to disprove that content path.

The provenance correction can prevent repeated reconstruction of an already-resident predecessor
row, but that is not claimed as resolution of its initial content. If sparse corruption remains
after Tighe's gameplay test, investigation should compare the first predecessor materialization
against exact arcade resident cells rather than altering this confirmed retention rule.

Build 0530 remains a candidate until Tighe completes conventional and jump-assisted R1-S2 climbing,
including vertical reversals and the record transitions.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0060`
