# Build 0449 — Fully Prebaked Native Title

## Scope and result

Build 0449 replaces the title screen's historical physical-slot and generic
sprite-residency dependencies with a purpose-built Genesis package.  This task
does not implement the item-description screen or any later attract screen.
Automated validation passes; visual and real-hardware acceptance remain with
Tighe.

The semantic cut remains the arcade title producer at `0x03AA54`.  Below that
cut, the title-specific native path owns final Genesis Plane A, Plane B, pattern,
palette, and SAT data.  It does not emulate the PC080SN or PC090OJ chip tails.

## Generated package

`gen_native_title.py` now emits:

- complete 64x32 Plane A and Plane B name tables;
- an invincible-variant Plane A table;
- the title palette row;
- a deterministic pattern package allocated only into slots free in the
  existing title preload;
- a complete static SAT for `HIGH SCORE`, `1UP`, and `2UP`;
- 18 dynamic digit positions, each with hidden and `0` through `9` native SAT
  records; and
- the retained generic frontend-label include used only by later screens.

Allocation is deterministic first-use order.  Only exact 32-byte-identical
patterns are deduplicated.  The package contains 216 unique Plane patterns and
20 sprite glyph identities (80 Genesis 8x8 patterns), for 296 uploaded pattern
tiles total.  Plane patterns use free slots below the established sprite band;
sprite glyphs use slots 1339 through 1418.  Title entry invalidates the sprite
residency metadata before later reuse.

There is no special case or dependency on physical slots `0x0349` through
`0x034C`.  The full 20-cell TAITO artwork is generated and verified like every
other static Plane-A cell.

## Runtime ownership

Title entry performs one bounded install:

1. install the generated pattern records;
2. copy the complete generated Plane A and Plane B tables to staging;
3. stage the generated palette;
4. copy the complete static SAT to the current back bank;
5. populate the 18 digit records from semantic score state; and
6. request the initial map, palette, and SAT publications.

The title-active generic sprite enqueue path returns without rebuilding title
SAT.  The VBlank preparation path compares nine semantic score bytes.  An
unchanged frame performs no title publication.  A changed six-digit group
copies and publishes only its six precomputed SAT records (48 bytes).

The score sources are now distinct:

- active P1: `A5+0x011E`; inactive saved P1: `A5+0x009E`;
- active P2: `A5+0x011E`; inactive saved P2: `A5+0x00DE`;
- high score: `A5+0x0142`; and
- active-player selector: `A5+0x002A`.

This removes the Build-0446 defect in which the right-hand `2UP` column reused
the P1 score path.

## Stable-frame contract

On an unchanged title frame the native path performs zero PC080SN title draws,
tile translations, static map generation, static glyph rendering, SAT rebuilds,
residency searches, Plane A/B DMA, SAT DMA, palette DMA, pattern DMA, per-cell
comparison loops, or full-SAT comparison loops.  Only the bounded nine-byte
semantic change check remains.

## Static verification

`verify_native_title.py` independently reconstructs every generated artifact
and checks all 646 authored static cells from authoritative source identity
through final map word and uploaded pattern bytes.  It verifies plane location,
palette bits, flips, slot existence, exact pattern bytes, all 20 TAITO cells,
the 29-record SAT chain (11 static plus 18 dynamic slots), distinct 1UP/2UP
ownership, all dynamic variants, allocation legality/non-overlap, source/runtime
contracts, and the shift-aware `0x03BB7C` table target.

Result:

`NATIVE_TITLE_VERIFY_PASS cells=646 taito=20 patterns=296 static_sat=11 dynamic=18x11`

## Address and reflow safety

The retained glyph semantic replacement around arcade `0x03BB48` remains a
shift replacement and resolves arcade table `0x03BB7C` through declared
shift-aware relocation.  The downstream expected original branch byte was
updated from `0x60` to `0x62` because the revised contraction is two bytes
smaller than the prior WIP; its semantics are unchanged.  Generated assets are
referenced by linker symbols.  The canonical ROM coverage endpoint grows from
`0x295EB8` to `0x298EB8` to cover the linked generated package.

Builds 0447 and 0448 were numbered and preserved but rejected by the canonical
incbin-byte gate: first because the new asset anchors were local, then because
the gate requires the label and `.incbin` on separate source lines.  Exporting
the seven anchors in the gate's established source form fixed the metadata
contract without changing asset bytes or runtime behavior.

## Stray `3`

The title one-shot install writes the complete 64x32 Plane-A staging table, so
no pre-existing Plane-A cell survives the installed title.  The reported `3`
is absent on that fully installed title and reappears on the credit/throne
presentation.  Its owner is therefore the later credit/throne Plane-A frontend
producer, not the title package.  The exact later-screen cell and writer were
not proven inside this title-only task.  Repair is deliberately deferred; no
cell-specific mask or clear was added.

## Build and gates

- Build: 0449 (2,723,512 bytes)
- Native title composition/pattern/SAT verifier: PASS
- VRAM allocation/non-overlap: PASS
- Assembly/link: PASS
- Postpatch/reflow: PASS (`73` shifts, `3` jump-table fixes, `7203` branch
  fixes, `629` absolute-long fixes)
- Canonical gate: PASS
- Gameplay-entry gate: PASS, zero address/bus/illegal/crash-handler events
- Seven-epoch gate: PASS
- Fixed 30-second Genesis NTSC trace: PASS (`1798` frames; no unmapped access)
- Complete seven-ROM family/configuration verification: PASS

Artifacts:

- canonical SHA-256:
  `22f5efaecbd8bba8724b477f100e718c2a591f987ea4cb7cf55fd47c05dd705c`
- `_d` SHA-256:
  `8c2f0152342f948dd7fc5c04180b55ccea889d26d2fcb453df11429e88f3567f`
- `_do` SHA-256:
  `c325ad4ea37b135c4e6174de42ba5adfc8f490411ba07cbf8f7df1e66624ae13`
- `_invincible` SHA-256:
  `0ae7252323c091a1f9bba58ee5557a6b11c95184e65748d6c72f307dc4a5f24b`

Real-hardware acceptance is pending Tighe.  No rope race was rerun because the
bounded title presentation changes do not affect gameplay execution or the
rope-race performance path.
