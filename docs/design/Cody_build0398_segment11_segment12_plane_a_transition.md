# Build 0398 — corrected post-Segment-11 Plane-A transition

Baseline: accepted Build 0397. Tighe's video
`OPEN_ISSUE-Build 396 tiles_lost (approx 5 seconds in).mp4` visibly shows a
large still-visible terrain region changing/disappearing at a transition.

## Correct transition identity

The initial literal record-11 -> record-12 test was the wrong boundary: both records use
stable epoch/package 3, so it has no residency switch and loses zero identities. Reviewing
the video and current generated sequence identifies the next actual residency boundary as
arcade progression **record 12 -> record 13**, selector 0:

`stable package 3 -> stable package 4`.

There was no overlap package at this boundary in Build 0397.

## Proven failure and repair

| Set | Count |
|---|---:|
| Record-12 complete identities | 225 |
| Record-13 complete identities | 218 |
| Exact identities shared by complete records | 97 |
| Record-12 identities still visible during overlap | 217 |
| Retained by the former direct stable-package switch | 115 |
| Lost/reassigned too early | 102 |
| Record-13 incoming identities during overlap | 217 |
| Exact shared overlap identities | 89 |
| Required transition union | 346 |
| Plane-A capacity / remaining margin | 676 / 330 |

Build 0398 adds generated overlap package 9, producing:

`stable 3 -> overlap 9 -> stable 4`.

The package contains the exact 346-identity union. The existing atomic exact-identity
name remapper moves 100 conflicting outgoing identities. Generated descriptor metadata
performs the existing generic column-45 handoff to stable package 4. There is no runtime
record/coordinate special case, per-frame search, LRU, or new representation.

Stable package 3 remains byte-identical to Build 0397
(`616389bb1016326afa76929590fc44180148894c81e2b88e37b97b12026da446`).
Stable package 4 remains byte-identical
(`2666dd7251959d364b119d1a55de24d010dbdb96ea79a943f1a487f736d8f648`).
Accepted Segment-10 -> Segment-11 overlap package 8 remains byte-identical
(`4bd3c8a2ddb7606e67c985b6bc3b1ae65fc0368706554216d1672d6a46a55fae`).

## Architecture and gates

Semantic cut: retain arcade progression record, selector, source-map cells, scrolling, and
publication decisions; compile their exact physical identities into final Genesis Plane-A
residency/name mappings. The retired PC080SN name-RAM/address-walk tail remains retired.
No PC080SN emulation, chip RAM, runtime allocator, or compatibility representation was added.

Transition gate passes with zero missing identities, collisions, incoming stable-slot changes,
or handoff omissions. Canonical and gameplay-entry gates pass. The complete canonical, `_d`,
`_s`, `_do`, and `_c` family exists. The pre-existing Phase-1 seven-epoch warning remains.

Canonical Build 0398:

- SHA-256: `afa543a0c77ea8a7b8ed3bb930cbfecd5dbfa0ec6a574ad3a86c192b07625716`
- Size: `1,756,856` bytes
- Counter: `398`

Tighe must verify the corrected transition visually in BlastEm.
