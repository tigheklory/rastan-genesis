# Build 0407 Native Sprite Performance Optimization

**Agent:** Cody  
**Input baseline:** accepted Build 0406  
**Output:** Build 0407 full ROM family  
**Human acceptance:** required

## Pure-native closeout

The remaining `native_player_piece` entries came from one mechanically captured
caller: return `0x05483E`, call site original arcade `0x054742`, inside the
`0x0546A8` secondary/legs compositor for `A5+0x1246`. The capture contained 36
entries from that sole site, four per active update. Its runtime descriptor walk
was replaced at the whole-producer semantic boundary with an offline-generated
52-selector × four-phase × two-orientation index (416 records). The fixed FRONT
and three-record auxiliary producers also emit direct pieces.

The completion manifest now reports 49 `NATIVE_COMPLETE`, zero
`NATIVE_PARTIAL`, and zero reachable `UNRESOLVED`. Runtime routes report player
fallback `0`, generic fallback `0`, and player adapter `0`. Specialized native
execution is proven by 27,204 hits on the established Build-0406 natural route
and 28,236 on the Build-0407 candidate route. The obsolete player adapter and
native general descriptor/piece parser are removed; Genesis performs no runtime
PC090OJ descriptor or piece-stream interpretation.

## Optimization and semantic gate

The measured Build-0406 queue path cost 399.45 cycles/piece and 13,135.84
cycles/completed finalizer. It saved/restored eleven registers and redispatched
an unchanged lane for every generated piece.

Build 0407 resolves the lane once per generated frame. Its minimal enqueue
retains the identical hidden/blank/code-zero filters, bound check, queue count,
and ordered `(attr, Y, finalized identity, X)` tuple. The common finalizer still
owns dynamic attributes, H/V flip, priority, O(1) residency, miss worklist,
queue/lane ordering, SAT links, and DMA. The build-integrated verifier passes
all six lane mappings and this complete queue-to-finalizer contract.

Measured optimized fast enqueue: 172.11 cycles/piece and 3,940.43
cycles/completed finalizer. That recovers 227.34 cycles/piece (56.91%) and
9,195.41 cycles/completed update (70.00%) on the optimized generated path.

## Objective timing

Both runs use the same GENESIS NTSC MAME deterministic record-2 route, cold
boot, energy hold, and 1,200 rendered gameplay frames. The measured candidate
is byte-identical to numbered Build `0407_c`.

| Metric | Build 0406 | Build 0407 | Delta |
|---|---:|---:|---:|
| workers/rendered frame | 0.6567 | 0.8342 | +0.1775 (+27.03%) |
| worker avg/update | 186,855.31 | 145,865.23 | -40,990.08 (-21.94%) |
| worker median / p95 / max | 188,320 / 285,794 / 422,728 | 136,644 / 263,984 / 334,158 | median -27.44% |
| IRQ avg/update | 193,172.71 | 151,515.14 | -41,657.57 (-21.56%) |
| IRQ median / p95 / max | 193,491 / 298,915 / 435,529 | 141,169 / 267,985 / 345,941 | median -27.04% |
| graphics avg/update | 122,333.29 | 85,793.42 | -36,539.87 (-29.87%) |
| graphics median / p95 / max | 128,480 / 178,890 / 219,610 | 84,208 / 113,548 / 143,892 | median -34.46% |
| IRQ updates >128,009 | 99.5% | 79.1% | -20.4 percentage points |
| frames without completed worker | 412 | 199 | -213 (-51.70%) |

Build 0407 remains 17,856.23 average worker cycles and 23,506.14 average IRQ
cycles above the 128,009-cycle NTSC frame budget. The equal-emitted-count
control across 270 common samples is deliberately narrower: worker -1.145%,
IRQ -1.061%, graphics -0.596%. Actor composition and completed-update/scene
distribution differ even at the same piece count, so the large whole-route gain
must not be attributed to enqueue instructions alone.

The next largest measured active native cost center is the common finalizer at
48,591.61 cycles/call (35,026.46 cycles/rendered frame on this route). No second
optimization was attempted.

## Gates and evidence

- Generator and independent frame verifier: PASS (1,200 primary, 416 secondary,
  38 Level-B, 1,898 universal general, 24 universal specialized).
- Finalized-pattern/palette, direct-dispatch, residency, and fast-enqueue gates:
  PASS.
- Completion manifest: 49 complete / 0 partial; reachable unresolved: 0.
- Assembler/link, boot guards, canonical ROM, gameplay-entry, and five-family
  artifact gates: PASS.
- Gameplay-entry exceptions: address `0`, bus `0`, illegal `0`, crash handler
  `0`; normal trace: 1,798 frames, no unmapped address.
- VDP ownership: PASS, no write outside the publication bracket.
- Existing unrelated seven-epoch PC080SN route remains its pre-existing labeled
  warning; this task made no PC080SN or scheduling change.

Evidence directories:

- `states/traces/build0406_native_performance_baseline/`
- `states/traces/build0406_native_cost_buckets/`
- `states/traces/build0406_native_sprite_fullgame_closeout/`
- `states/traces/build0406_native_sprite_rack_to_progress11/`
- `states/traces/build0407_zero_adapter_broad/`
- `states/traces/build0407_retired_parser_performance/`
- `states/traces/build0407_retired_parser_cost/`
- `states/traces/build0407_retired_parser_broad/`
- `states/traces/build0407_gameplay_entry_gate_20261008_211230/`

## ROM family

All files are 1,998,520 bytes.

| Variant | SHA-256 |
|---|---|
| canonical | `a152dfbf2e436f13234d668d37a9bc5cb897072d122e3bf4babab3eafd5ecaab` |
| `_c` | `44ac73d7f32d311997df70fcfe20cbaf61b3ced3023213b5aa059581a77d8b4f` |
| `_d` | `b7e607a2c2ff614330be1a4acc716e3b6873acd632b011569a21f9c030ef2c7b` |
| `_do` | `8b5ee1dd9071947bc1130f4c2462a7d83a9ca7d815c526568d438c46293de89a` |
| `_s` | `fe58c4bec056aacd957a9cf21051473f905d2e8f81b09af83e6faf7746cff45e` |

Tighe should validate overall speed; ordinary R1/P1 and heavy bat/hurry-up
scenes; Rastan FRONT/BODY ordering and animation; all weapons including fire
sword; specialized enemies; ropes/contact; bosses/subobjects; geometry, flips,
palettes, damage/death, scrolling/transitions, and crashes/corruption.
