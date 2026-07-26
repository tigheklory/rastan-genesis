# PC080SN Gameplay Control — A5-Relative State Fields (canonical)

`a5 = 0x10C000`; absolute = a5 + displacement. Confidence: **P**=proven from opcodes, **R**=runtime-confirmed, **?**=inferred.

| Dec | Hex disp | Absolute | Field role (neutral) | R/W sites | Conf | HW/coord link |
|---|---|---|---|---|---|---|
| 4256 | 0x10A0 | 0x10D0A0 | cursor for horizontal publish (sel 0, strip_A); also tilemap0 via 0x055E54 | W 0x05581E/0x0503EC/0x055E54; R 0x055968 | P | tilemap1 dest 0xC08000 |
| 4260 | 0x10A4 | 0x10D0A4 | cursor for vertical publish (sel 1/2, strip_B) | W 0x0556F8/0x055784/0x050400; R 0x055990 | P | tilemap1 dest 0xC08000 |
| 4264 | 0x10A8 | 0x10D0A8 | **selector/direction** (map-data byte) | W 0x0558F8 (=`*(a5@0x10C6)`); R dispatch/cells | P/R | 0=horiz,1/2=vert,4/5/6 other scenes |
| 4270 | 0x10AE | 0x10D0AE | scroll accum updated by sel-0 (−= delta, &511) | W 0x05583E; R 0x055AB4 | P | → 0xC40002 (layer-B Y) |
| 4272 | 0x10B0 | 0x10D0B0 | scroll accum updated by sel-1(+=)/sel-2(−=) (&511) | W 0x055718/0x0557A4; R 0x055AB4 | P | → 0xC20002 (layer-A Y) |
| 4274 | 0x10B2 | 0x10D0B2 | horizontal tile-boundary accum (sel 0; += a5@0x10D8; `btst #3`) | RW 0x0557EC/0x0557F4/0x055802 | P | 8px tile-cross trigger |
| 4276 | 0x10B4 | 0x10D0B4 | vertical tile-boundary accum (sel 1; += a5@0x10DA; `btst #3`) | RW 0x0556BE… | P | 8px tile-cross trigger |
| 4278 | 0x10B6 | 0x10D0B6 | vertical tile-boundary accum (sel 2; += a5@0x10DA; `btst #3`) | RW 0x055750… | P | 8px tile-cross trigger |
| 4280 | 0x10B8 | 0x10D0B8 | accum (4th-direction path; checked `<160` 0x0557BA, `<0` 0x05585C) | RW 0x05582E/0x05587C | P | 4th direction |
| 4282 | 0x10BA | 0x10D0BA | accum (checked `>=8` 0x05572E; `−=delta` 0x055790) | RW 0x055708/0x055794 | P | direction gate |
| 4294 | 0x10C6 | 0x10D0C6 | **map source pointer** (advanced +1 by 0x558E0; selector byte read from `*(this)`) | RW 0x0558E4/0x0558F0 | P | map-data stream |
| 4298 | 0x10CA | 0x10D0CA | column sub-index **0→3** (++ per publish; reset at 4) | ++ 0x055954/0x05595E; clr 0x0558DA | P | ring col (×4 with 0x10CC = 64) |
| 4300 | 0x10CC | 0x10D0CC | row/group index **0→15** (++ at CA==4; reset at 16) | ++ 0x0558B2; clr 0x0558E0 | P | ring group (16×4 = 64) |
| 4304 | 0x10D0 | 0x10D0D0 | pending-direction bitmask (bit4/5/6/7 set when a direction ≠ active selector) | RW 0x0556B6/0x055748/0x0557D4/0x05586C | P | deferred-direction latch |
| 4312 | 0x10D8 | 0x10D0D8 | horizontal scroll delta | R 0x0557F0/0x055832… | P | per-frame camera step |
| 4314 | 0x10DA | 0x10D0DA | vertical scroll delta | R 0x0556C2/0x055754… | P | per-frame camera step |
| 4332 | 0x10EC | 0x10D0EC | layer-B X scroll | R 0x055AB4 | P | → 0xC40000 |
| 4334 | 0x10EE | 0x10D0EE | layer-A X scroll | R 0x055AB4 | P | → 0xC20000 |
| 4908 | 0x136C | 0x10D36C | flag copied from selector (0x0558EC); gates horizontal path 0x0557DC | RW | P | scene/step flag |
| 5072 | 0x13D0 | 0x10D3D0 | direction code (0/1/3) set before `jsr 0x406a4` | W 0x05571C/0x0557A8/0x055842 | P | passes dir to 0x406a4 |
| 318 | 0x13E | 0x10C13E | publish counter (++ 0x0558FE) | W | P | — |
| 524 | 0x20C | 0x10C20C | flag checked at 0x055854 (4th-dir gate) | R | ? | — |

**Descriptor/source tables (WRAM, not A5-relative):** `0x10D000` = base-pointer array (16 longs, advanced +4/group by 0x558C6); `0x10D040` = descriptor-pointer table (16 longs, rebuilt by 0x055904, walked by publishers as `a3`); `0x10D080` = source-word table (16 words, rebuilt by 0x055904, read by publishers as `a1`). **(Corrects the earlier "0x10D1C0/0x10D200" arithmetic slip.)**

## Tilemap0 + scene-init + selector-command fields (this checkpoint)
| Dec | Hex disp | Absolute | Role | Conf |
|---|---|---|---|---|
| 4266 | 0x10AA | 0x10D0AA | scene-fill loop counter (=64) | P |
| 4342 | 0x10F6 | 0x10D0F6 | tilemap0 column index (++ 0x55C56; ×2 in tile offset) | P |
| 4344 | 0x10F8 | 0x10D0F8 | **tilemap0 cursor** (=0xC00000; seeded 0x0503F6/0x05040C) | P |
| 4348 | 0x10FC | 0x10D0FC | tilemap0 aux (copied to a5@0x1126 by 0x55C4A) | P |
| 4390 | 0x1126 | 0x10D126 | tilemap0 aux (from 0x10FC) | P |
| 4286 | 0x11DE | 0x10D1DE | position/counter gating selector-4/5 events (0x05127C) | P |
| 4328 | 0x10E8 | 0x10D0E8 | state set to 7 by 0x527CC on selector 4/5/6 | P |
Tilemap0 tables (WRAM): `0x10D100` = descriptor-pointer table, `0x10D104` = source words (distinct from tilemap1's 0x10D040/0x10D080).
