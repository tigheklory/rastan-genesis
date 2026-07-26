# PC080SN Core Publishers — Address Index

`a5 = 0x10C000`. Confidence: **P**=proven from opcodes, **R**=runtime-confirmed, **?**=deferred.

| Arcade PC | Name (neutral) | Destination layer | Role | Collision side effect | Conf | Ref |
|---|---|---|---|---|---|---|
| `0x055948` | `pc080sn_publish_dispatch` | tilemap1_0xC08000 | dispatch: `a5@0x10A8==0 → 0x055968` else `0x055990`; `a5@0x10CA++`; then `0x558A2` | none directly | P | asm §1, c §1 |
| `0x055968` | `pc080sn_publish_strip_A` | tilemap1_0xC08000 (cursor `a5@0x10A0`) | walk 16 descriptors (tbl `0x10D1C0`) + source `0x10D200`, call `0x0559B2` per cell; save cursor | via 0x0559B2 | P | asm §2, c §2 |
| `0x055990` | `pc080sn_publish_strip_B` | tilemap1_0xC08000 (cursor `a5@0x10A4`) | same walk, call `0x055A14` per cell; cursor NOT saved | via 0x055A14 | P | asm §3, c §3 |
| `0x0559B2` | `pc080sn_cell_forward` | tilemap1_0xC08000 | write cell (word0=`*(a1)`, word1=`desc[0+…]`), 4 sub-cells | **YES** → `0x10DE00+(dest−0xC08000)/2` | P/R | asm §4, c §4 |
| `0x055A14` | `pc080sn_cell_dir_aware` | tilemap1_0xC08000 | same, sub-index reversed (`notw` when `a5@0x10A8≠2`); sets `a5@0x1330` | **YES** → `0x10DE00…` + a 2nd wrapped write | P | asm §5, c §5 |
| `0x055904` | `pc080sn_descriptor_rebuild` | tbl `0x10D1C0`/`0x10D200` | (referenced) supplies the 16 descriptor pointers consumed above | none | P(partial) | asm §6 |
| `0x055E54` | (tilemap0 cursor set) | **tilemap0_0xC00000** (`=0xC00400`) | state-gated (`a5@0x139A==2`) — separate path, NOT the core publishers | — | ? | unresolved |

**Layer proof summary:** the two gameplay triggers (`0x055808` horizontal → `a5@0x10A0`, `0x0556E0` vertical → `a5@0x10A4`) both compute `dest = 0xC08000 + …` → the core publishers write **tilemap1_0xC08000**. `pc080sn_tilemap0_0xC00000` is set only by the separate `0x055E54` path. Collision index `0x10DE00 + (dest−0xC08000)/2` is therefore anchored to tilemap1.
