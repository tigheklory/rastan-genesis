# Build 0458 — Attract-Demo Plane-B Ring Initialization Fix

**Agent/task:** Cody — reject Build 0457, remove its regression, and fix the actual attract-demo
Plane-B ring initialization defect  
**Date:** 2026-10-19  
**Status:** CANDIDATE — PENDING TIGHE REAL-GENESIS ACCEPTANCE  
**Issue:** OPEN-031  
**Accepted baseline:** Build 0456, source `66dd550555a4dbfc76e94c7bcf64334513e3a489`  
**ROM-producing source:** `e4545426`

## Outcome

Build 0458 removes the rejected Build-0457 repeated scene lifecycle and restores accepted-0456
cache/startup behavior. It fixes the actual attract-only ownership gap: the native item-screen
teardown now reproduces the original arcade scroll/ring-origin reset before clearing the planes.
Patterns remain resident and are not reloaded on a valid cache hit.

This is statically proven and emulator-gated, but attract visual correctness and real-hardware
timing remain pending Tighe's test.

## Build 0457 rejection and exact blackout mechanism

Original `0x0503DC` initializes `A5+0x10AA` to 64 at `0x05042C`. The loop calls `0x055948` and
`0x055C4A`, decrements the word once at `0x050472`, and repeats until zero before returning at
`0x050482`. Each `0x055C4A` call reaches `genesistan_hook_itempage_strip_blit`. Thus `0x10AA` owns
64 column/strip publications; it does not identify the first call.

Build 0457 put the nonzero test before the cache hit. Every iteration consequently:

1. wrote `genesistan_scene_present_pending = 1`;
2. called `load_scene_tiles(1)`;
3. wrote display off;
4. reloaded the 1,002-tile gameplay manifest;
5. reset the foreground/package cache and installed gameplay palette/package state.

Publication/display-on remained owned by the one `0x050482` completion boundary. The countdown
still progressed, but 64 × 1,002 × 16 = 1,026,048 pattern-word writes plus repeated cache/package
work were inserted before that return. This explains the hardware-observed 30+ second black screen.
The same retained fill is reused by normal entry and next-life entry, explaining both regressions.
The old verifier checked only that rejected ordering, so its PASS restated the bug. The gameplay
entry gate's incomplete post-entry assertions should not have been accepted as positive evidence.

## Arcade provenance and actual root

The shared R1 initializer is unchanged:

```text
0x04529C -> 0x0501E2 -> 0x0503DC -> 0x050482
```

`0x0501E2` establishes stage/record data, clears Plane-A group/index at `0x10CC/0x10CA` and
Plane-B group/subcolumn at `0x10F4/0x10F6`, installs the Plane-B descriptor pointer at `0x10FC`,
installs the selector stream at `0x10C6`, and starts the 64-column fill. It does not own the
frontend item's teardown reset of `0x10EE`.

The attract item page starts with the generic clear at `0x055E22 -> 0x0561A0`, then scrolls for
1,488 frames. `0x05607C` decrements `A5+0x10EE` on every fourth frame, so 372 decrements leave:

```text
A5+0x10EE = (0 - 372) & 511 = 140
```

At state 8, `0x055F0E` calls original `0x056440`; its final `BSR 0x0561A0` zeroes
`A5+0x10AE`, `0x10B0`, `0x10EC`, and `0x10EE`, publishes those scroll values through `0x055AB4`,
and then clears both planes. Build 0453 replaced the complete `0x056440` body with
`genesistan_pc090oj_hook_zero_fill_56440`, but that helper retired item sprites and called only
`genesistan_hook_cwindow_clear`. It omitted all four retained scroll clears and native scroll
publication.

That omission is attract-specific and precedes the otherwise shared R1 initializer. It does not
occur on normal gameplay entry or death/next-life, which explains the exact original asymmetry.

## Row/ring proof

Gameplay Plane B derives its visible logical top as:

```text
visible_top = (((-A5+0x10EE) + 8) & 511) >> 3
physical_row = logical_row & 31
```

| State | Correct fresh R1 | Rejected pre-0458 attract handoff |
|---|---:|---:|
| `A5+0x10EE` | 0 | 140 (item residue) |
| `staged_scroll_y_bg` | 0 | 140 |
| visible logical top | 1 | 47 |
| physical top | 1 | 15 |
| resident logical rows | 1..32 | 47..63, 0..14 |
| physical rows | logical `&31` | logical `&31` |

Each of the 64 countdown iterations publishes one Plane-B column and examines source logical rows
0..63. With a correct origin, logical row 0 is the offscreen seam, the first resident source row is
1, and it stages to physical row 1; logical row 32 stages to physical row 0. With item residue, the
native filter instead treats logical row 47 as the top and places it at physical row 15. The rows
and their patterns are individually valid, but the 64-logical-to-32-physical window is rotated to
the previous scene's phase. That matches Tighe's hardware observation of present patterns with
wrong/mixed rows.

There is no separate persistent Genesis ring-front variable. Relevant native state is
`staged_scroll_y_bg`, the final 32-row `staged_bg_buffer`, row/column dirty masks, and transient
`plane_b_column_mode`; row identity derives from the retained `A5+0x10EE` plus `logical&31`.
Package/LUT identity and pattern residency are independent and were already correct.

## Exact correction

At the existing semantic item teardown helper only:

- clear retained `A5+0x10AE/0x10B0/0x10EC/0x10EE`;
- clear matching native staged FG/BG X/Y scroll words;
- then call the existing native two-plane clear;
- restore accepted-0456 ordering in the gameplay strip hook so a valid tileset cache hit skips
  loading and nonzero `A5+0x10AA` cannot force 64 scene reloads.

No pattern reload, cache/package reset, prolonged blanking, map-coordinate special case, palette
change, gameplay/next-life special case, fallback, new shadow, NOP bypass, or RTS bypass was added.

## Native semantic cut

The retained arcade semantic boundary is item-screen end-of-life (`0x056440 -> 0x0561A0`): retire
item sprites, reset the retained scroll/ring origin, and clear the presentation surfaces. The native
helper realizes that decision directly as staged scroll state and final Genesis Plane-A/B names.
The removed chip tail remains PC090OJ object-RAM clearing, PC080SN C-window name-RAM clearing, and
PC080SN scroll-register writes. No software PC080SN/PC090OJ device or chip-address projection was
introduced.

## Durable verifier

`verify_attract_demo_plane_b_scene_entry.py` was rewritten. It now rejects the 0457 forced-reload
ordering, requires the accepted cache hit before the multi-call countdown, and requires all four
retained and four native staged scroll origins to be reset before the item teardown clears planes.
Because the reset exists only inside the item teardown helper, normal start and next-life retain
their accepted lifecycle.

## Validation

| Check | Result |
|---|---|
| Root ring-origin verifier | PASS |
| Assembly/link + postpatch/reflow | PASS — 76 shift replacements; 7,203 branch fixes; 628 absolute-long fixes |
| Canonical gate | PASS — 229 opcode-replacement sites; coverage through `0x29CEB8` |
| Gameplay-entry gate | PASS — 563 frames; all 240 post-entry frames; no exception |
| Seven-epoch gate | PASS — seven targets / records 0,3,4,5,11,13 |
| Build-0456 selector-stream verifier | PASS — operand/map `0x051155`, 157 bytes |
| Build-0455 native item verifier | PASS — 64x64 logical / 64x32 physical / 64 crossings |
| Native title verifier | PASS |
| Shared HUD verifier | PASS |
| BEST-5 verifier | PASS |
| Genesis NTSC MAME fixed30 | PASS — 1,798 frames |
| Seven-ROM family | PASS |
| `_invincible` verifier | PASS — 66/66 damage entries; zero unrelated ROM differences |
| Genesis NTSC MAME deterministic rope | PASS — `798/798/798`, median `13,317.147 ms`, deterministic YES |

No new gameplay trace, Lua route, save state, manual navigation, or attract diagnostic route was
created or run.

## Artifacts

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0458.bin`
- SHA-256: `b8e6784dc0f2eb0c2cf9c9021d9cb53204d89731a759213a05646c733a386699`
- `_invincible` SHA-256: `750e9611a2aa6bd308f406b8b46ff99080a1e0a51ae7a53d79ed8b131cc3ab2f`
- Size: 2,739,896 bytes each
- Counter: 457 -> 458
- Fixed30: `states/traces/rastan_direct_video_test_build_0458_mame_30s_20261019_234833/`
- Rope: `states/traces/build0458_rope_attach_benchmark_invincible/`
- Gameplay entry: `states/traces/build0458_gameplay_entry_gate_20261019_234822/`
- Epoch: `states/traces/build0458_phase1_epoch_gate_20261019_234825/`

## Files changed

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/Makefile`
- `specs/rastan_direct_remap.json`
- `tools/translation/verify_attract_demo_plane_b_scene_entry.py`
- this report, Build-0457 rejection report, OPEN_ISSUES, and AGENTS_LOG

## USER MUST VERIFY

On real Genesis hardware, Tighe must verify:

1. Attract demo begins without prolonged black and Segment-0 Plane-B rows are correct/not mixed;
   subsequent scrolling remains correct.
2. Normal game start matches Build 0456 timing and Plane B remains correct.
3. Death/next-life resumes without prolonged black.
4. R1 reaches its true end and Subround 2 remains reachable (Build-0456 selector behavior).
5. Build-0455 item screen and title/story/BEST-5 remain unchanged.

Build 0458 remains a candidate until this hardware acceptance. Phase D and Phase E were not
started. STOP.
