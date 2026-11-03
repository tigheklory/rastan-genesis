# Cody — Third-chain vertical-scroll comparison resolution

**Task:** Resume the Build-0378 third-chain investigation at the claimed foreground-Y
divergence.  **Result:** the claimed divergence is a frame-pairing error.  No production patch
or ROM was produced; the Makefile-owned counter remains 378 and the next build remains 0379.

## Authoritative field and producer

The foreground Y scroll is `A5+0x10B0`:

- ORIGINAL ARCADE RAM: `0x0010D0B0` (`A5=0x0010C000`);
- Genesis WRAM: `0x00FF10B0` (`A5=0x00FF0000`);
- original `0x055AC4` publishes it to PC080SN Y-scroll register `HW_ADDRESS 0x00C20002`;
- current runtime `0x055B54` publishes the same retained field to native staged-scroll word
  `0x00FF409E`.

`A5+0x10AE` is foreground X.  This is independently fixed by the collision lookup at original
`0x053A2E`, which combines D1/X with `+0x10AE` and D2/Y with `+0x10B0`.  A contemporaneous H23
document labels these axes oppositely; that naming is not used here because the instructions and
hardware operands above are decisive.

The vertical producer family is retained arcade logic:

| Contract | Original arcade PC | Current Genesis runtime PC | Semantics |
|---|---:|---:|---|
| clear per-frame direction flags | `0x0517E0` | `0x0519E8` | clears `A5+0x10D0` before motion decisions |
| first vertical motion controller | `0x053850` | `0x05396C` | consumes capped displacement from `A5+0x10DE`; uses player screen Y `A5+0x10C0` and the 64-pixel band |
| set bit 0 / step | `0x0538D6` | `0x0539F2` | sets `A5+0x10D0 bit 0`; writes `A5+0x10DA` |
| opposite vertical controller | `0x0538EA` | `0x053A06` | consumes the opposite vertical displacement; uses the 112-pixel band |
| set bit 1 / step | `0x053942` | `0x053A5E` | sets `A5+0x10D0 bit 1`; writes `A5+0x10DA` |
| Y dispatcher | `0x055650` | `0x0556DE` | dispatches bit 0 to `0x055696` and bit 1 to `0x05572E` |
| bit-0 Y update | `0x055696` | `0x055724` | increases `+0x10B0` by `+0x10DA`, modulo `0x200` |
| bit-0 final store | `0x055718` | `0x0557A6` | writes `A5+0x10B0` |
| bit-1 Y update | `0x05572E` | `0x0557BC` | decreases `+0x10B0` by `+0x10DA`, modulo `0x200` |
| bit-1 final store | `0x0557A4` | `0x055832` | writes `A5+0x10B0` |

The vertical boundary accumulator is `A5+0x10BA`.  The bit-0 path accepts ordinary updates while
it is below `0x0100`; at/above that bound, selector `A5+0x10A8 == 1` selects the wrapped/streamed
case, otherwise bit 5 is set and the update is clamped.  The bit-1 path accepts ordinary updates
while the accumulator is at least 8; below that bound, selector 2 selects the wrapped/streamed
case, otherwise bit 4 is set and the update is clamped.  Both paths update `+0x10B0` only after
the applicable decision.

The Build-0247 hooks at original `0x055704` and `0x055790` replace only the raw entering-row
publication portions.  Current address-map authority maps their retained continuations to
`0x05579A` and `0x055826`; final helper jumps target those addresses, so the original
`+0x10B0` arithmetic and stores still execute.

## Narrow stale-absolute audit

The only absolute `0x0010xxxx` reads in this producer/feedback family are the four feedback reads
at original `0x0512D2`, `0x0512E8`, `0x0512FE`, and `0x05131C`.  The current spec already rebases
them to `0x00FF10DA`/`0x00FF10D8`.  Final disassembly confirms those mapped operands at runtime
`0x0514DA`, `0x0514F0`, `0x051506`, and `0x051524`.  No stale absolute foreground-Y operand was
found in the bounded family.

## Correct same-state comparison

The earlier comparison paired different revolutions of the 512-pixel name-table ring.  The
authoritative same-state pair already exists in the retained traces:

| Field | ORIGINAL ARCADE frame 4494 | GENESIS NTSC Build 0378 frame 2147 |
|---|---:|---:|
| stage | `0x01` | `0x01` |
| progression | `0x0011` | `0x0011` |
| player X | `0x0122` | `0x0122` |
| player Y | `0x003E` | `0x003E` |
| player state | `0x0004` | `0x0004` |
| foreground X (`A5+0x10AE`) | `0x0160` | `0x0160` |
| foreground Y (`A5+0x10B0`) | `0x010D` | `0x010D` |
| vertical request | implied by continued `+0x10B0` advance | `A5+0x10D0 bit 0 = 1` |
| effective vertical step | 1 pixel/frame over the sampled interval | 1 pixel/frame (`0x0106 -> 0x010D`) |
| vertical screen target | `0x0040` from the retained `0x053850` controller | `0x0040`, same retained controller |
| selector (`A5+0x10A8`) | not logged by the bounded arcade script | `0x0000` |
| strip / group | `0x0000 / 0x0000` | `0x0000 / 0x0000` |

Genesis frames 2140..2147 advance foreground Y `0x0106 -> 0x010D`, one pixel per retained update.
This is the same update direction and semantic progression seen in the arcade trace.

The cited Genesis `0x0026` state is later: the retained route shows `0x0100 -> 0x0126 -> 0x0166
-> 0x01E9 -> 0x0000 -> 0x0021 -> 0x0026`, while strip/group advances from `0/0` to `1/1`.
Thus `0x0026` is a post-wrap revisit of the same screen-relative player coordinates, not the
arcade frame-4494 logical map state.  Screen X/Y, progression, and player state alone do not name
a unique world-ring epoch.

## Result and remaining dependency

There is no first divergent vertical-scroll decision in the compared same-state frames.  Failure
classification is `OTHER: TRACE_FRAME_PAIRING_ERROR`.  Forcing `0x010D`, changing a clamp, or
patching the retained writer would corrupt a contract that already matches the arcade.

Build 0378's collision publication correction is independently valid and remains retained: it
makes gameplay collision publication resolve the same live/ring-unwrapped descriptor as the
native Plane-A visual resolver.  Its post-build 72-cell corridor contains zero collision
mismatches, including the eight cells that differed before the correction.  This does not mean
it solves traversal; Tighe's BlastEm result remains **forward traversal FAIL**.

The exact unresolved dependency is now outside the Y-scroll producer: identify the first gameplay
decision that differs after the matched `strip/group 0/0`, `fgy 0x010D` attachment epoch and before
the arcade reaches its upper route.  That comparison must retain the ring epoch/strip/group so a
later `1/1` revisit is not paired with the first `0/0` attachment.

## Tool and validation record

- Existing project tools reused: canonical Ghidra exports/full listing, `build/maincpu.disasm.txt`,
  `build/genesis_postpatch.disasm.txt`, generated `build/rastan-direct/address_map.json`, and the
  existing Build-0378 `arcade_exit_route.tsv`, `player_probe_events.tsv`, and route TSVs.
- New tooling created: **NONE**.
- Why new tooling was necessary: **not applicable**; retained evidence directly contains the exact
  matching state.
- Runtime platforms: ORIGINAL ARCADE MAME for frame 4494; GENESIS NTSC MAME for Build-0378 frame
  2147.  No new emulator run was performed in this continuation.
- Production files changed: **NONE**.
- ROM/build: **NONE**; counter remains 378.
- STOP status: stopped at the exact unresolved post-attachment gameplay decision boundary; no
  unsupported scroll patch was made.
