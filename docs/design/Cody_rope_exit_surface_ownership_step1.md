# Cody — Rope Exit Surface Ownership, Step 1

## Scope

Static analysis only against Build 0398. This step asks only whether the supplied
record-2 and record-14 rope-exit anchors are bit-7 collision surfaces handled by
arcade `collision_map_surface_postprocess_5a29c` (`0x05A29C`) and
`collision_map_surface_mark_5a2ee` (`0x05A2EE`). No Genesis destination conversion,
runtime trace, patch, or build was performed.

## Static decode

Both supplied source entries are byte-identical:

| Record / anchor | Source entry | Entry words |
|---|---:|---|
| record 2, X48/Y40 | `0x02C54C` | `0x0003, 0x2120` |
| record 14, X44/Y36 | `0x02A588` | `0x0003, 0x2120` |

The shared descriptor at `0x002120` contains its 16 visual tile words at
`0x002120..0x00213F`; its upper-left visual word is `0x0438`. The collision
section begins at descriptor `+0x20`:

```text
0x002140: 0x00FF
0x002142: 0x0001
```

The retained arcade collision producers `0x0559B2` / `0x055A14` interpret
`descriptor+0x20 == 0x00FF` as the uniform-collision form and publish
`descriptor+0x22` for every logical cell in the 4x4 descriptor. Therefore the
pre-postprocess collision value at both anchors is `0x0001`. Bit 7 is clear.

`0x05A29C` calls `0x05A2EE` only when bit 7 of the scanned collision word is set.
Consequently neither supplied anchor can invoke `0x05A2EE`, and its four-cell
mutation/`0x25C7` visual tail does not own either platform.

## Collision-ring mapping

The ordinary collision-ring address is:

```text
0x0010DE00 + ((Y * 64 + X) * 2)
```

For record 2 X48/Y40, the anchor maps to `A0 = 0x0010F260`; the four
top-row logical cells of the supplied metatile are `(48,40)..(51,40)` at
`0x0010F260, 0x0010F262, 0x0010F264, 0x0010F266`.

For record 14 X44/Y36, the anchor maps to `A0 = 0x0010F058`; the four
top-row logical cells are `(44,36)..(47,36)` at `0x0010F058, 0x0010F05A,
0x0010F05C, 0x0010F05E`.

These are normal descriptor-owned cells, not `0x05A2EE` affected cells. The
complete descriptor spans X48..51/Y40..43 and X44..47/Y36..39 respectively,
with ordinary collision value `0x0001` throughout.

## Result and stop

Ownership by `0x05A29C -> 0x05A2EE`: **NO**.

The immediately evident owner is the normal descriptor/metatile publication
path using shared descriptor `0x2120`, not the special bit-7 surface mechanism.
The next single bounded question is where descriptor `0x2120`'s ordinary visual
and collision outputs first diverge or disappear on Genesis at these two exact
anchors.

No ROM was built. Counter remains 398.
