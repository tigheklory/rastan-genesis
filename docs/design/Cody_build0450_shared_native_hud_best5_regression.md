# Cody — Build 0450 Shared Native HUD + BEST-5 Regression Correction

## Scope and result

Build 0449 remains rejected. Build 0450 preserves its native title Plane A/B art package and corrects two independent regressions:

1. The title-private HUD SAT chain used `index + 2` as the Genesis link, skipping alternating records. Its title-active predicate also suppressed the established frontend HUD through the story/throne portion of scene 0. The same private glyph allocation occupied normal sprite-residency slots without a durable frontend reservation.
2. The BEST-5 SCORE/ROUND and NAME producers retained pre-reflow Genesis literals `0x03C57C` and `0x03C654`. The current address map places the original arcade tables at `0x03C560` and `0x03C638` respectively.

The correction introduces one generated shared HUD package and one runtime FRONTEND_FULL owner. The established gameplay `1UP + P1` hot path remains the GAMEPLAY_REDUCED_P1 policy adapter and is otherwise unchanged.

## Semantic cut

The HUD cut is:

`arcade semantic P1/P2/high-score/credit state -> generated fixed HUD layout and glyph assets -> final Genesis SAT records`

The removed chip tail is generic PC090OJ HUD record construction/interpretation. No PC090OJ record RAM, generic glyph interpreter, or full-SAT comparison is reintroduced.

## Shared generated assets

`gen_native_hud.py` generates:

- 11 fixed label SAT records for `1UP`, `HIGH SCORE`, and `2UP`;
- 19 dynamic positions: six P1 digits, six P2 digits, six high-score digits, and one credit digit;
- hidden plus digits 0–9 as complete native SAT variants;
- one 20-cell fixed frontend glyph-pattern package at sprite cells 1339–1418;
- a correct sequential SAT chain: record 0 links to 1, through record 28 linking to 29, with record 29 terminating at zero.

`gen_native_title.py` now emits only title-specific planes, palette, and Plane A/B patterns. It no longer owns or duplicates HUD SAT records or sprite glyphs.

## Runtime ownership and performance

`hud_native.s` provides FRONTEND_FULL activation, semantic change detection, changed-group publication, credit publication, fixed frontend pattern residency, and clean transition back to gameplay residency.

- Stable frontend: ten semantic-byte comparisons; no SAT rebuild and no HUD publication.
- Changed score: only the affected six SAT records are replaced in both staged banks and live VRAM.
- Changed credit: only one SAT record is replaced.
- Transient item screens append after shared HUD record 29; cells 0–19 remain reserved for HUD patterns.
- Leaving frontend invalidates the fixed HUD residency contract once before the existing gameplay finalizer allocates its normal 49-cell pool.

The existing gameplay reduced adapter remains `.Lnq_project_p1_hud` under `RASTAN_GAMEPLAY_HUD_SPRITES == 2`. It continues to emit only `1UP + P1`, using the established fast native sprite path. Full gameplay HUD was not enabled.

## Consumer coverage matrix

| Consumer | Mode | Labels/digits/credit owner | SAT owner | Pattern owner |
|---|---|---|---|---|
| Title | FRONTEND_FULL | shared native HUD | shared HUD records 0–29 | shared fixed HUD package |
| Story / throne | FRONTEND_FULL | shared native HUD | shared HUD records 0–29 | shared fixed HUD package |
| BEST-5 / ranking top row | FRONTEND_FULL | shared native HUD | shared HUD records 0–29 | shared fixed HUD package |
| BEST-5 row templates | OTHER / Plane A | retained glyph renderer | staged Plane A | Plane-A scene residency |
| BEST-5 SCORE/ROUND | OTHER / Plane A | `genesistan_hook_number_renderer_3c2e2` | staged Plane A | Plane-A scene residency |
| BEST-5 NAME | OTHER / Plane A | `genesistan_hook_highscore_fg_producer` | staged Plane A | Plane-A scene residency |
| Item-description | FRONTEND_FULL | shared native HUD | shared HUD plus transient suffix | shared fixed HUD package plus remaining transient residency |
| Coined-up / credit | FRONTEND_FULL | shared native HUD | shared HUD records 0–29 | shared fixed HUD package |
| ROUND / READY | FRONTEND_FULL until gameplay scene ownership begins | shared native HUD | shared HUD records 0–29 | shared fixed HUD package |
| Gameplay | GAMEPLAY_REDUCED_P1 | established native reduced adapter | gameplay native finalizer | normal gameplay sprite residency |

Every visible group has one final owner. The assembly-false Build-0273 frontend implementation is retained only as local provenance and emits no code; it is not a runtime owner.

## Why Build 0449 failed

Build 0449's generated SAT encoded each link as `index + 2`. Genesis SAT links name the next zero-based record, so record 0 must link to 1. The faulty chain displayed records 0, 2, 4, and so on, producing fragmented labels and scores.

The scene-0/title-active split then kept that title-private owner selected through story/throne. BEST-5 and item pages crossed into the generic frontend branch, so their top HUD recovered. That branch also rebuilt the whole HUD every pass and competed with the normal sprite residency band. Build 0450 removes the state split: every non-gameplay state selects the same FRONTEND_FULL owner and reserves its fixed pattern cells.

## BEST-5 reflow correction

The ranking WRAM contract remains intact: SCORE/ROUND read the established A5-relative `0x0140..0x0156` data and NAME reads the adjacent name fields. No values are seeded or hard-coded.

Two build-time tables now copy authoritative bytes from original `maincpu.bin` into linker-addressed native symbols:

- numeric descriptor source: original arcade `0x03C37C`, 130 bytes;
- name descriptor source: original arcade `0x03C454`, 48 bytes.

The historical `0x03C57C` value was the former Genesis location of the numeric table, not its original arcade address. Build 0450's address map resolves:

- arcade `0x03C37C` -> current Genesis `0x03C560`;
- arcade `0x03C454` -> current Genesis `0x03C638`.

The two producers now address generated linker symbols, so later opcode reflow cannot stale these operands. `genesistan_hook_number_renderer_3c2e2` still computes `a5 + (source - 0x0010C000)` and still gates leading-zero suppression with `cmpi.w #6,(a0)`.

The known rows (`273100/3/COB`, etc.) remain verifier oracles only; they are not production constants.

## Title preservation

The title-specific package retains the complete RASTAN logo, sword, red TAITO art, copyright, first-use Plane pattern allocation, exact-byte deduplication, and the absence of the historical `0x0349–0x034C` dependency. Stable title Plane A, Plane B, and pattern work remains zero.

## Verification

- Native title verifier: PASS (`646` cells, `20` TAITO art cells, `216` title-plane patterns).
- Shared HUD verifier: PASS (`30` SAT records, correct sequential links, `19 x 11` dynamic variants).
- HUD consumer coverage: PASS (matrix above; one runtime frontend owner).
- BEST-5 reflow verifier: PASS (`0x03C560`, `0x03C638`, A5 base `0x0010C000`).
- Assembly/link: PASS.
- Postpatch/reflow: PASS (73 shifts, 3 jump-table repairs, 7203 branch repairs, 629 absolute-long repairs).
- Canonical gate: PASS.
- Gameplay-entry gate: PASS.
- Seven-epoch gate: PASS.
- Standard fixed 30-second MAME validation: PASS; trace `states/traces/rastan_direct_video_test_build_0450_mame_30s_20261018_174458`.
- Seven-member family/configuration verification: PASS.

## Artifact

- Build: 0450
- Canonical ROM: `dist/rastan-direct/rastan_direct_video_test_build_0450.bin`
- Size: 2,723,512 bytes
- SHA-256: `38880ca84030ca16e2f2e5cac8cc1699d6dcfd65b9b4a3809f7e6ed0740f383e`
- `_d`: `2816e7dbee451f5bc9ec8ccf001e0bd2a6f3dde85135f26821e6c6b1237579d8`
- `_do`: `29703ae279db1c43bc855241584f97b7374799cb728c9b31dee2d83ac0246c4e`
- `_invincible`: `b2a93f17fdd0f2e8c8dfa6b328f8a4d39dc7f8628c97c66614cdad7c98d9ff6e`
- Counter: 450
- ROM-producing source commit: `79f05b5e`
- Visual/hardware acceptance: pending Tighe.

No item-description ring conversion, stray-3 repair, full gameplay HUD restoration, Phase D, or Phase E work was started.
