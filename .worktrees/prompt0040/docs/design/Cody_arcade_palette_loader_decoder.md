# Cody — FUN_0003ba20 Palette Assembler: FULLY DECODED + real CRAM emitted

**Type:** static RE + compiler impl. No runtime change, no ROM, Build 0302 not consumed.

## FUN_0003ba20 — fully decoded from 68000 disassembly (0x3ba20–0x3ba86)
```
lea 0x4FD02,a3 ; lea 0x3BA88,a1 ; lea a5@0x1600,a0(staging DEST)
d0 = a5@0x118 (scene); a1 = 0x3BA88 + (scene-1)*32           ; 32-byte scene record
loop i=0..31: d0 = record_byte(i); bsr 0x3ba56 ; write 16 words to staging
0x3ba56: a3 = 0x4FD02 + d0*32 (colour block); 16x: word = xform(pool word)
```
- **Scene record** `0x3BA88 + (scene-1)*32`, **32 bytes**; **record byte `i` → palette bank `i`**; the
  byte VALUE `B` = **colour-block id** in the pool.
- **Colour pool** base `0x4FD02`, block = `0x4FD02 + B*32` = **16 words**, each **0RGB nibble-packed**
  (`S[8:11]=R, S[4:7]=G, S[0:3]=B`).
- **Transform (0x3ba64):** nibble×2 → **arcade xBGR-555** = `R=(S>>8&0xF)*2, G=(S>>4&0xF)*2, B=(S&0xF)*2`
  → word `(B<<10)|(G<<5)|R`. Proven by hand-following the shifts/masks; verified on real data.
- **Banks per call:** 32 · **colours/bank:** 16 · colours copied directly (transformed), no defaults/skips.
- **Genesis conversion (proven, prior):** xBGR-555 `>>2`/channel → `0000 BBB0 GGG0 RRR0`.

## Compiler implementation (tools/translation/compile_pc080sn_genesis.py)
`decode_pool_block()` + `decode_scene_arcade_palettes(scene)` implement the exact algorithm; the compiler
emits **real** `cram_epochs.bin` (**512 CRAM words = 32 banks × 16**, converted) + provenance in `report.json`
(per bank: scene-record byte, pool block address, 16 arcade xBGR-555 words, 16 Genesis CRAM words).
Deterministic rebuild PASS; 0 trace deps. Example: bank 3 (FG) = record byte 12 → pool `0x4FE82` → Genesis
`0EEE(white) 08AE 044A …`; bank 0 = block 11 → `0x4FE62`.

## Remaining sub-edge (narrow, honest)
The 32 scene banks are palette-RAM banks **0–31**. The registry "effective banks" **48 (BG), 51/0x33, 54/0x36
(sprites)** are **> 31** and are placed into palette RAM by the *loaders* (`FUN_00045dc4` → `0x200600`=bank 48,
via the `a5@3152`-indexed staging offset) and the sibling entry `FUN_0003ba04` (pools `0x4EAF6`/`0x4FE62`), not
by the scene record directly. So the **staging-bank → palette-RAM-bank offset mapping for banks >31** is the
last edge for those specific BG/sprite banks. FG bank 3 (in 0–31) is fully covered now. Scene index assumed
= 1 for Stage-1 gameplay (registry "scene 1"); if the live `a5@0x118` differs the record index shifts (a
parameter, not a semantic gap).

## palette_decisions.json untouched (policy only). No colours guessed; source = arcade ROM.

## ADDENDUM (Andy) — >31 bank path decoded (bank 48 closed; sprites remaining)
- **FUN_0003b9f8** (startup, from `startup_common_body`): `d3=768; lea 0x200000,a0; lea 0x4EAF6,a3;
  bsr 0x3ba64` → transforms **768 words from pool `0x4EAF6` → palette banks 0..47** (nibble*2 xBGR-555,
  same transform), then **16 words from `0x4FE62` → bank 48** (PC080SN BG).
- **FUN_00045dc4 / a5@3152**: `a5@3152` = a 1..8 chunk counter; source `a5@0x1600 + (a5@3152-1)*128`,
  dest `0x200600 + (a5@3152-1)*128`, 64 words/chunk via `0x3a2d0` → copies scene staging banks into
  palette-RAM banks 48+ (bank 48 = scene block 11 = `0x4FE62`, consistent with the startup base).
- **Generic decoder** `decode_arcade_palette_bank(mc,bank,scene)`: bank<32 scene-record→0x4FD02;
  32..47 startup base 0x4EAF6; 48 BG 0x4FE62; **49..127 UNRESOLVED (PC090OJ sprite-palette path)**.
- Validation: **bank 3 (FG) @0x4FE82** real, **bank 48 (BG) @0x4FE62** real (`0008 004E 008E 00EE…`).
  `cram_epochs.bin` now includes bank 48. Deterministic PASS.
- **Remaining edge:** PC090OJ sprite banks 49..127 (**51/0x33, 54/0x36**) — their colours come from the
  sprite-palette load path (object attr a4@39 → sprite palette staging → banks 49+), NOT the tile-plane
  startup/scene pools. Tracing that is the sprite-palette subsystem (overlaps the deferred coexistence
  decoder). FG+BG (tile-plane) palette source is now fully decoded; sprite palette source remains.
