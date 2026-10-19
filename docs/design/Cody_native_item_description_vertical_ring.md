# Build 0453: Native Item-Description Vertical Ring

## Baseline and scope

Tighe's Build 0452 acceptance was recorded before this implementation. The locked source is `8cf04c693a1299ac818e653de501a92bb8af8117`, `refs/accepted/build-0452` points to that exact commit, the canonical ROM SHA-256 is `7dc9230c1e18cb71900986fc3f06fe2e680622b7e4020d805ce1e67a2057f48e`, and the `_invincible` SHA-256 is `594550b61de2bb3a7fd0d03af9b4a29580de00f7f2d3a2a6ed6a0235cd7141f2`. Its accepted deterministic rope result is 798/798/798 frames, median 13,317.147 ms.

Build 0453 changes only the scrolling item-description attract presentation. Title, story/throne, BEST-5, gameplay HUD policy, attract timing, credit/Start handling, and gameplay systems are unchanged.

## Semantic cut

The retained arcade item dispatcher and state remain authoritative. The address-map-authoritative entry cut is arcade `0x05602C` -> Genesis `0x056090`; it now calls `genesistan_item_description_enter` at `0x073A2C` and returns. The tick cut is arcade `0x05607C` -> Genesis `0x0560E2`; it calls `genesistan_pc090oj_hook_sprite_decay_5607c` at `0x074AB8` and returns. Both are proper size-changing shift replacements.

Semantic boundary:

> Retained arcade scroll/dwell/attract/item-visibility state at the `0x5602C`/`0x5607C` boundary -> final native Genesis Plane-B/SAT output.

The item-specific runtime `0x563A6` decompression output, `0x560DA` PC080SN C-window row stream/rebuild, generic C-window projection, and PC090OJ tuple-copy interpretation are no longer executed for native item output. Shared routines remain available to their other consumers. The old padded `0x5607C` opcode replacement was retired; the replacement uses no NOP, trampoline, shadow chip RAM, runtime fallback, or separate Genesis timer/scroll counter.

## Generated presentation

`gen_native_item_description.py` decodes the authoritative arcade text streams at `0x05672A` and `0x05697E` into a complete 64-row x 64-word (4,096-word) final Plane-B logical map. It also emits 27 deduplicated text patterns, final native icon templates derived from the 17 page-A descriptors at `0x056226` and three page-B descriptors at `0x0562B0`, and the corresponding fixed 16x16 icon patterns.

The physical Plane B remains 64x32. At entry, logical rows 4..35 populate physical rows `logical & 31`. The retained `A5+0x10EE` counter decrements one pixel every fourth frame modulo 512. On an eight-pixel crossing, the native tick copies exactly one precomputed 64-word row and sets exactly one Plane-B dirty bit. The invariant is:

```text
physical_row = logical_row & 31
entering_logical_row = (35 + ((-A5+0x10EE & 0x1ff) / 8)) & 63
```

Thus N and N+32 deliberately replace one another, logical 63->0 and physical 31->0 wrap without a rebuild, and pixel motion remains the established VSRAM path. `staged_scroll_y_bg` is copied directly from live `A5+0x10EE`; `vdp_commit_scroll` applies the established `-value + 8` display-origin transform.

Item patterns are installed once on entry. Plane patterns use slots 1..27. Icon ownership is derived at build time from the current sprite owner's `SPRITE_TILE_BASE`/`NATIVE_CELLS` and `native_hud_report.json`: FRONTEND_FULL retains cells 0..19, while the 20 item icon cells use cells 20..39 / pattern slots 1419..1498. These remain below slot 1536 and do not overlap Plane B at `0xC000`, Plane A at `0xE000`, SAT, HScroll, or the shared HUD. The screen uses the existing frontend palette semantics; no new palette package or recurring palette publication was introduced.

The native icon emitter retains the arcade scroll-relative Y, retirement at Y<=16, order, priority, and the page-B replacement of page-A records 0..2 at 96 pixels. Runtime icon work is limited to visibility/Y and final SAT records; no PC090OJ source tuple is interpreted at runtime.

## Verification and cost

`verify_native_item_description.py` independently reconstructs the arcade map and icon data and proves:

- 64x64 final logical dimensions and exact source-pattern bytes;
- every logical top row 0..63 projected into the 32-row ring;
- N/N+32 ownership, logical and physical wrap, and one-row/one-bit crossing work;
- current HUD-derived VRAM ownership and no name-table boundary overlap;
- exact native icon patterns/semantic records;
- the two shift-reflow cuts and removal of the padded item tick replacement.

Steady no-scroll frames do zero item-plane generation, row DMA, decompression, glyph conversion, metatile interpretation, static pattern work, and palette work. Pixel-only scroll frames update VSRAM. Eight-pixel crossings copy/publish one 64-word row plus VSRAM. The 512-pixel wrap performs no full-plane rebuild.

All normal gates passed: item verifier, title, shared HUD, BEST-5, assembly/link, 75-site shift reflow, canonical gate, gameplay-entry gate, seven-epoch gate, fixed 30-second Genesis NTSC MAME validation, complete seven-ROM family verification, and invincibility verification. No new route, Lua script, manual gameplay, or benchmark was created.

## Artifact

- Build: 0453
- ROM-producing source: `d5bae39b67f5df6d5ff3499adfa6972bdf111942`
- Canonical: `dist/rastan-direct/rastan_direct_video_test_build_0453.bin`
- Size: 2,735,800 bytes
- Canonical SHA-256: `628f3025dfffe09a6b2188b0ecc14f5134683b93efdbc3482275dd489fd4a36e`
- `_invincible` SHA-256: `8e680621a80948d96ad86fda0f0f367c5fed270d98ccddbfeb3a7756888b1f10`
- Counter: 453
- Real-hardware acceptance: pending Tighe
