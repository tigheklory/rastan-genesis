# Cody Build 0435 Genesis-Native Full Gameplay HUD Restoration

Date: 2026-10-16  
Accepted baseline: Build 0434  
Produced candidate: Build 0435

## Result

`RASTAN_GAMEPLAY_HUD_SPRITES` now has its intended permanent contract:

- `0`: gameplay HUD suppressed;
- `1`: complete Genesis-native gameplay HUD;
- `2`: accepted reduced Genesis-native 1UP/current-score HUD.

Mode 1 uses retained arcade gameplay state, purpose-built native HUD tuples,
`native_queue_hud`, the existing native SAT finalizer, and the VDP. It does not
restore PC090OJ object RAM, records, scanning, decoding, chip-address writes, or
frontend ownership.

## Phase-0 static confirmations

### P2 / 2UP score source

Original `0x03B802` selects its left or right score column with `A5+0x002A`, but
both table entries read the active player's packed-BCD score from
`A5+0x011C..0x011E` (MSB at `A5+0x011E`). The digit order is high nibble then low
nibble at `+0x11E`, then `+0x11D`, then `+0x11C`.

The player-swap routines establish the persistent sources needed to draw both
columns simultaneously:

- inactive P1: `A5+0x009C..0x009E`, MSB at `A5+0x009E`;
- inactive P2: `A5+0x00DC..0x00DE`, MSB at `A5+0x00DE`;
- active player: `A5+0x011C..0x011E`;
- active selector: `A5+0x002A` (`0` P1, nonzero P2).

Thus Mode 1 uses live P1 plus saved P2 while P1 is active, and saved P1 plus
live P2 while P2 is active. Both 1UP and 2UP columns remain present. Leading
zeroes follow the accepted reduced-HUD rule: suppress digits until the first
nonzero digit; an all-zero value emits no digit sprites.

### Exact gameplay geometry

The authoritative source is the original gameplay template at `0x03B950` plus
the digit records used by `0x03B802`, not the frontend layout.

| Group | Original semantic tuples / positions |
|---|---|
| HIGH label | `(Y,code,X)`: `(00,3B,88)`, `(00,3A,78)`, `(00,3C,98)`, `(00,3D,A8)`, `(08,3E,B8)` |
| HIGH digits | `Y=0x10`; MSD-to-LSD `X=0x80,0x88,0x90,0x98,0xA0,0xA8` |
| 2UP label | `(10,39,120)`, `(00,49,108)`, `(00,47,118)` |
| 2UP digits | `Y=0x10`; MSD-to-LSD `X=0xE8,0xF0,0xF8,0x100,0x108,0x110` |

All score/label pieces use the existing HUD-white direct-identity tag and
Genesis palette line 3. Mode-1 queue priority is HIGH label, retained energy
status, HIGH digits, accepted Mode-2 P1/1UP group, then 2UP digits/label. The
Mode-1 P1/1UP tuples deliberately preserve Mode 2's current placement,
including its known common label Y placement; this task does not correct that
separate presentation issue.

### Energy producer reachability

`genesistan_pc090oj_hook_status_sprite_5a098` remains naturally reachable from
the retained normal-gameplay caller at original `0x051054` (current mapped
runtime `0x051254`), itself reached by the gameplay main loop. No second call or
old transport was added.

Mode 1 reserves queue entries 5..12 for this producer's eight persistent native
status pieces. Its existing `A5+0x013A` state, six-cell energy mapping,
indicator/caps, low-energy blink, lifecycle, and sound transitions are
unchanged. A Mode-1-only validity word distinguishes a genuinely published
status group from score entries left in the persistent queue.

### Other bottom/status elements

- lives: **NOT GAMEPLAY HUD** as a separate sprite producer;
- stage/round: **FRONTEND/TRANSITION ONLY** for this inventory;
- item icons: **NOT GAMEPLAY HUD**;
- weapon/status icons: **NOT GAMEPLAY HUD**;
- other status sprites: **NONE PROVEN** beyond the `0x05A098` energy/status
  family.

The old record-range descriptions had overclassified the `0x05A098` family.
No unproven component was fabricated.

## Native implementation

The semantic cut is:

```text
retained score/player/high-score/energy state
  -> purpose-built Genesis-native gameplay HUD producers
  -> native_queue_hud
  -> existing native SAT finalizer
  -> VDP
```

Mode 1 adds `.Lnq_project_full_hud`, a compact packed-BCD score emitter, fixed
native label tuples, a 37-entry compile-time HUD bound, and an offset for the
already-native energy entries. The old `0x03B802` and `0x05A098` PC090OJ record
transport tails remain retired. Mode 2 retains its original
`.Lnq_project_p1_hud` assembly. Mode 0's compiled path and nine-entry queue
shape remain unchanged.

The restored Mode-1 code filled the formerly absent aligned ROM coverage page,
so the exact `_full_hud` postpatch receipt is now `0x292EB8`, equal to canonical
coverage. The Makefile's exact expected delta was factually updated from
`-0x1000` to `0`; the six-target machinery, flags, receipts, and verifier were
not weakened or redesigned.

## Static verification

New verifier:

`tools/translation/verify_gameplay_hud_modes.py`

It proves:

- original `0x03B802` source/destination table bytes;
- exact HIGH/P1/2UP gameplay template and digit geometry;
- all digits `0..9` in all six positions for P1, HIGH and 2UP;
- leading-zero and six-digit ordering behavior;
- energy units `0..48`, six-cell full/partial/empty mapping, and retained blink
  state references;
- Mode-1 native source addresses and fixed glyphs;
- absence of legacy scanner/object-RAM/chip-address dependencies in the new
  projector.

Result: **PASS**.

The protected Mode-2 `pc090oj_hooks.o` `.text` was captured before the edit and
compared with the final Mode-2 assembly:

```text
bytes:   7,378
SHA-256: 9824922a687767da3cf280788941c7dfc7510284bf6a92b50a2ce2e362bcb80c
result:  byte-identical
```

Whole canonical Build 0435 differs from Build 0434 at only two bytes:

- ROM offset `0x00018F`: Genesis header checksum;
- ROM offset `0x2928DB`: build string `0434` -> `0435`.

Therefore production gameplay/HUD bytes for Mode 2 are unchanged.

## Build 0435 family

All artifacts are 2,698,936 bytes.

| Artifact | HUD mode | SHA-256 |
|---|---:|---|
| `rastan_direct_video_test_build_0435.bin` | 2 | `eb6c27991ca49ef49c13c3da9a1b9b3f869455c43d57c4518629e3737f6a31c2` |
| `rastan_direct_video_test_build_0435_d.bin` | 2 | `3bd9948dc39a7e6a0dceb9f4da38c3101c04695ccfb7b20d1839d89a65f3451e` |
| `rastan_direct_video_test_build_0435_s.bin` | 2 | `d6c3ffc25b749f88d4c8eb3b9296cba4684f25388fdfa2a4c37cbd7f08f62e60` |
| `rastan_direct_video_test_build_0435_do.bin` | 2 | `babc5117d9831241bd191ea94b66dfcccdd3203bed11989bbdfa111e29814e6a` |
| `rastan_direct_video_test_build_0435_c.bin` | 2 | `1bce4ab6e5faffaf22d8aebfe54f0ae41de808f2b8bf65112e70aae06ea2dcd0` |
| `rastan_direct_video_test_build_0435_full_hud.bin` | 1 | `14a14317512e0305096a9ad2061430c0a3a0b1915a170265434fa84775773a04` |

Configuration receipts verify Mode 2 for canonical/`_d`/`_s`/`_do`/`_c` and
Mode 1 for `_full_hud`: **PASS**. Boot guards, canonical gate, gameplay-entry
gate, native metatile/selector/collision/DMA/static gates, and family check
passed. The existing phase-epoch gate retained its recent baseline warning
(`epoch=FAIL` after observing target record/epoch 0); the Makefile preserved the
candidate exactly as it did for accepted Builds 0433 and 0434.

## Allowed runtime validation

No gameplay was driven manually and no new route, trace script, save state, or
diagnostic harness was created.

- canonical fixed 30-second validation: **PASS**, 1,798 frames;
- full-HUD fixed 30-second validation: **PASS**, 1,798 frames;
- canonical rope: `803 / 803 / 803`, median `13,400.588 ms`, deterministic;
- full-HUD rope: `854 / 854 / 854`, median `14,251.684 ms`, deterministic.

The Mode-1 result is `+51 frames / +851.096 ms / +6.351%` versus canonical and
the accepted 0434 reference. This is a measured full-HUD overhead on the route,
not a claim about visual correctness. Per task scope, no HUD optimization was
performed.

Evidence:

- `states/traces/rastan_direct_video_test_build_0435_mame_30s_20261016_151028/`;
- `states/traces/rastan_direct_video_test_build_0435_full_hud_mame_30s_20261016/`;
- `states/traces/build0435_rope_attach_benchmark_reduced_hud/`;
- `states/traces/build0435_rope_attach_benchmark_full_hud/`.

## User acceptance required

Tighe must visually test both canonical and especially `_full_hud` on real
Genesis/Exodus. Confirm 1UP/current score, HIGH SCORE, 2UP, energy/status,
overall gameplay presentation, no duplicate/missing HUD, and no frontend
regression. Build 0435 full-HUD visual acceptance remains **PENDING**.

Phase D: **NO**.  
Phase E: **NO**.
