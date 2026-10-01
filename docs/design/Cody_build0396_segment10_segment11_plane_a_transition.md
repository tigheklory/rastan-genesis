# Segment 10 -> Segment 11 Plane-A transition (Build 0396/0397)

Baseline was accepted Build 0395, counter 395. Build 0396 was consumed after its
canonical and `_d` artifacts passed, but `_s` exposed a mechanical coverage-delta
change. It was preserved and not reused. The complete five-ROM result is Build 0397.

## Proven failure

Current progression records are Segment 10 / record 10 / selector 0 and Segment 11 /
record 11 / selector 0. Record 10 uses stable package 2. Before this repair, record 11
selected stable package 3 directly; there was no overlap package. Plane A has 676 slots.

| Set | Patterns |
|---|---:|
| Segment-10 complete identity set | 369 |
| Segment-11 complete identity set | 483 |
| Exact identities shared by complete records 10/11 | 198 |
| Segment-10 identities still visible during overlap | 304 |
| Retained by the old direct switch to stable package 3 | 202 |
| Lost/reassigned too early | 102 |
| Incoming Segment-11 identities required during overlap | 469 |
| Exact identities shared by the two overlap-visible sets | 167 |
| Required overlap union | 607 |
| Plane-A capacity / remaining margin | 676 / 69 |

Thus the first sufficient cause is proven: 102 physical identities were still named by
visible outgoing Segment-10 cells when the direct stable-package switch retired them.

## Repair and guards

The offline compiler now emits transition package 8 for record 10 -> 11, producing the
sequence `stable 2 -> overlap 8 -> stable 3`. Package 8 contains the 607-pattern union.
The existing atomic exact-identity name remap moves 99 conflicting outgoing identities;
no per-frame search, runtime coordinate/segment special case, LRU, shadow, or PC080SN
emulation was added. Generated descriptor metadata supplies the stable handoff target at
logical column 45, replacing the former runtime record-specific handoff branches.

Segment 11 remains authoritative. Its stable package-3 map/upload/identity payload is
byte-for-byte unchanged from Build 0395, SHA-256
`616389bb1016326afa76929590fc44180148894c81e2b88e37b97b12026da446`.
The editor profile, map/reference inputs, Build-0324 substitution policy, pattern identity
set, stable residency mapping, and palette/index mappings are unchanged. The transition
gate reports zero missing identities, zero collisions, zero incoming stable-slot changes,
and zero handoff omissions.

## Build result

Complete Build 0397 family: canonical, `_d`, `_s`, `_do`, `_c`. Canonical gate,
gameplay-entry gate, transition-retention gate, boot guards, palette equivalence, and
complete-family verification pass. The pre-existing Phase-1 seven-epoch warning remains.
Tighe must verify the Segment-10 -> Segment-11 presentation in gameplay.

