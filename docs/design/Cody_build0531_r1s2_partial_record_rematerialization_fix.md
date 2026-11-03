# Build 0531 R1-S2 partial-record rematerialization fix

Date: 2026-11-03

Build 0531 corrects the first bad Plane-A write captured from Build 0530. During a genuine 32-row
alias reuse, Build 0530 selected the completed predecessor for rows already authored by the current
partial selector-1 record. The original arcade, the generated record-17 pan rows, and Genesis rows
before alias reuse agree cell-for-cell.

The native row materializer now derives partial ownership from the existing selector and strip/group
front. Selector 1 owns `[63-front,63]`; selector 2 owns `[0,front]`. Alias misses within that range
use the current record's existing pan-row asset. All other misses retain the completed predecessor
path. Exact-owner preservation from Build 0530 remains unchanged. No new map, shadow tilemap,
duplicate graphics buffer, hardware layer, coordinate exception, collision change, or gameplay
change was introduced.

Source/verifier commit: `244d219ff8fead00fdc84920be5ecdb89db00a45`.

## Artifacts

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0531.bin` | 3,792,568 | `d0161ef288d67d73b54bd9afc50a6d5adf0aace5676d9158a085decde0a3d568` |
| `dist/rastan-direct/rastan_direct_video_test_build_0531_S1-2.bin` | 3,792,568 | `ca6985bf52f2af3534d9647debe594ccf1d0a54ef50f8046a215d41d7531e953` |
| `dist/rastan-direct/rastan_direct_video_test_build_0531_invincible_S1-2.bin` | 3,792,568 | `9264ea27e548f40851beb5c3de434bbf7b37bc6bcc6648e4097d26ac4d3da2e7` |

Counter/ledger: 0531.

## Verification

- full-span background coherence: PASS;
- selector-0 and selector-1/2 runtime equivalence: PASS;
- native scene-fill/pan/predecessor assets: PASS;
- canonical gate: PASS;
- gameplay-entry and Round-1 epoch/package gates: PASS;
- mandatory Genesis NTSC 30-second trace: PASS;
- complete numbered configuration family: PASS;
- normal R1-S2 direct start: PASS at frame 412, stage 16, record 17, package 5, map misses 0/0;
- invincible R1-S2 direct start: same result, PASS.

The regression gate exhaustively checks both vertical selectors at every front and row and includes
the captured record-17 rows 44-46 / aliases 12-14 sequence. Gameplay acceptance remains Tighe's:
repeat ordinary climbing and the aggressive jump-assisted reversal route on the invincible R1-S2
artifact. Build 0531 is a candidate until that test passes.

Full evidence and first-write chronology:
`docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0062_r1s2_first_bad_write_diagnosis.md`.
