# Cody - PC090OJ Per-SAT-Slot Sprite Tile-DMA Residency Cache, Build 0132

**Date:** 2026-07-02
**Type:** Narrow production implementation + build + runtime evidence
**Baseline:** Build 0131, SHA `da5c4492602e643679df4a3fee176eb531ccd2ab64023edf097066dfc921bd7f`
**Produced build:** Build 0132, SHA `989b17e8b065ae678764e5901c45cf156fd4c37bf2a128d8686f4f493b611832`
**Scope:** PC090OJ sprite tile-DMA residency only. No PC080SN artifact changes, no `scene_load.s`, no `tilemap_hooks.s`, no `vdp_comm.s`, no bookmark, no diagnostic ROM code, no fake sprites.

## Phase 0

Classification: **EXTENDING** OPEN-024 / OPEN-001. Relevant priors loaded: KF-010, KF-011, KF-014, KF-021, KF-026, KF-032, KF-036, and KF-038 as context. OPEN-015 was context only and not touched.

No contradiction detected. Architecture compliance: the arcade PC090OJ object RAM mirror remains canonical sprite state; the new cache is render-side VRAM residency state only.

## Gate 1 - PC080SN Ownership

Evidence files:

- `states/traces/pc090oj_persistent_sprite_tile_dma_cache_build0132_20260702_210813/gate1_pc080sn_ownership.md`
- `states/traces/pc090oj_persistent_sprite_tile_dma_cache_build0132_20260702_210813/gate1_pc080sn_ownership.json`

Result: **PASS**. The Phase 1 PC080SN ownership relocation still reserves sprite VRAM slots `1024..1343`; no PC080SN preload/LUT assignment overlaps that range.

Key values:

| Source | Entries / assigned | Destination range | Overlap with `1024..1343` |
|---|---:|---|---:|
| `title` | `845` | `0..844` | `0` |
| `gameplay` | `829` | `0..828` | `0` |
| `endround` | `1067` | `0..1003`, `1344..1406` | `0` |
| `vram_preload` | `845` | `0..844` | `0` |
| tile LUT nonzero slots | `2331` | `1..1003`, `1344..1406` | `0` |

## Gate 2 - Cache Initialization

BSS/WRAM zeroing is **not** generic in this ROM. `_bootstrap_clear_staging` explicitly clears the video staging and PC090OJ structures, so the residency cache needed an explicit boot clear.

Implemented one boot-time clear in `apps/rastan-direct/src/boot/boot.s`:

```asm
lea     sprite_tile_resident_code, %a0
move.w  #(80 - 1), %d7
.Lboot_sprite_tile_resident_clear:
    clr.w   (%a0)+
    dbra    %d7, .Lboot_sprite_tile_resident_clear
```

Generated disassembly proof:

```asm
0x000002F6: lea 0xff674a,%a0
0x000002FC: move.w #79,%d7
0x00000300: clr.w (%a0)+
0x00000302: dbf %d7,0x300
```

## Implementation

Added `sprite_tile_resident_code`, an 80-word render-side cache in `apps/rastan-direct/src/pc090oj_hooks.s`:

- Symbol: `sprite_tile_resident_code = WRAM 0x00FF674A`
- Size: `80 * 2` bytes
- Sentinel: `0x0000` means cold/no resident tile
- Ownership: render-side VRAM residency only, not canonical sprite state

Changed `.Lpc090oj_emit_slot` so valid emitted sprites compare the masked tile code (`d3 & 0x0FFF`) against `sprite_tile_resident_code[slot]`. It sets descriptor bit `0x0004` only on mismatch. It does **not** write the cache.

Changed `.Lvcs_tile_dma` so the existing valid and changed gates remain intact. After the VDP DMA command is launched, it writes `sprite_tile_resident_code[slot] = dma_code`, then clears descriptor bit `0x0004` as before.

`.Lvcs_clear_generated_sprite_state` still clears only per-frame SAT/descriptors/dirty/active state. It intentionally does **not** clear `sprite_tile_resident_code`.

Invalid, blank, offscreen, skipped, or code-zero sprites do not update the residency cache.

## Static Verification

Symbols:

- `staged_sprite_sat = 0x00FF6104`
- `staged_sprite_descriptor_table = 0x00FF6384`
- `staged_sprite_dirty = 0x00FF6744`
- `staged_sprite_active_count = 0x00FF6748`
- `sprite_tile_resident_code = 0x00FF674A`
- `pc090oj_object_ram = 0x00FF67EA`

Emit-side cache compare, generated disassembly:

```asm
0x00071896: move.w %d3,%d6
0x00071898: andi.w #0x0fff,%d6
0x0007189C: move.w %d0,%d5
0x0007189E: add.w %d5,%d5
0x000718A2: lea 0xff674a,%a2
0x000718A8: move.w (0,%a2,%d5.w),%d5
0x000718AE: cmp.w %d6,%d5
0x000718B0: beq 0x718b8
0x000718B2: move.w #0x8005,%d5
0x000718B8: move.w #0x8001,%d5
0x000718BC: move.w %d5,(%a0)
```

DMA-side cache update, generated disassembly:

```asm
0x00072272: move.l %d1,(%a3)          ; VDP DMA command
0x00072278: lea 0xff674a,%a1
0x0007227E: move.w %d6,(0,%a1,%d0.w) ; cache[slot] = dma_code
0x00072282: andi.w #-5,(%a0)          ; clear tile-code-changed bit
```

## Build Verification

Release command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

- Counter: `131 -> 132`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0132.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Build 0132 SHA: `989b17e8b065ae678764e5901c45cf156fd4c37bf2a128d8686f4f493b611832`
- Rolling vs numbered: byte-identical (`cmp=0`)
- Build 0131 SHA differs as expected
- Boot guard: PASS
- Canonical gate: PASS (`GATE_PASS`)
- `opcode_replace` patched-site count: `133` unchanged
- `total_genesis_bytes_covered`: `0x17D47C -> 0x17D4A4`

The first release invocation stopped at the canonical coverage invariant with observed `0x17D4A4`. The invariant was then updated in the two canonical verification tools only:

- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

No spec, PC080SN generated artifact, ROM artifact, or source file outside the allowed set was changed for that adjustment.

## Runtime Evidence

Evidence directory:

`states/traces/pc090oj_persistent_sprite_tile_dma_cache_build0132_20260702_210813/`

Key files:

- `sprite_resident_write_lua.log`
- `sprite_resident_write_analysis.md`
- `sprite_resident_write_analysis.json`
- `capture_build0132_sprite_resident_writes.lua`
- release trace: `states/traces/rastan_direct_video_test_build_0132_mame_30s_20260702_211245/`

The Lua runtime observer installed a host-side write tap on `WRAM 0x00FF674A..0x00FF67E9` (`sprite_tile_resident_code`). This is a precise proxy for successful sprite tile DMA completion because the cache is written only in `.Lvcs_tile_dma` after the VDP DMA command.

Reduced result:

```text
SUMMARY frames=1800 total_cache_writes=124 final_state=0002/0002/0006 active=0020 decoded=0100 zero=00DA blank=0000 unmapped=0000 offscreen=0006 drawable=0020 emitted=0020 dropped=0000 resident_nonzero=39
FRAME frame=0 cache_writes=80
FRAME frame=33 cache_writes=27
FRAME frame=43 cache_writes=17
PC_COUNT pc=000304 count=80
PC_COUNT pc=072282 count=44
```

Interpretation:

- Frame `0`: 80 writes from the boot cold-clear loop (`runtime_genesis_pc 0x00000304`).
- Frames `33` and `43`: 44 total runtime cache updates from the post-DMA cache update site (`runtime_genesis_pc 0x00072282`).
- Frames `44..1800`: **0 additional residency-cache writes**.
- At frame 1800, sprite work is still active: `active=0x20`, `drawable=0x20`, `emitted=0x20`, `resident_nonzero=39`.

This proves the cache warms during early sprite presentation and then suppresses repeated per-frame tile DMA for unchanged SAT slots. In the final sampled state, 32 sprites are still emitted, but no repeat tile-DMA cache updates occur after frame 43.

A secondary VDP-control write-PC classifier was attempted and retained as an artifact, but it is not used for the final DMA count because MAME reports VDP control-port writer PCs in a way that was too indirect for the tile-DMA command classification. The residency-cache write tap is the authoritative runtime measurement for this task.

## Non-Actions

- No `tools/translation/precompute_pc080sn_tile_lut.py` edit.
- No PC080SN generated artifact change.
- No `scene_load.s`, `tilemap_hooks.s`, or `vdp_comm.s` edit.
- No `SPRITE_TILE_BASE`, VDP base, or PC090OJ object-RAM semantic change.
- No SAT/descriptors made canonical.
- No broad emitter split, shared allocator, fake sprite path, or 30 FPS fallback.
- No bookmark cycle.
- No OPEN issue closed.

## OPEN / KNOWN_FINDINGS Impact

OPEN-024 remains open pending visual/runtime follow-up on the broader PC090OJ sprite subsystem. OPEN-001 remains open as rendering context. OPEN-015 was not touched.

KNOWN_FINDINGS impact: Option A, no update. This task implements a known design slice and produces Build 0132 evidence; it does not by itself establish a new durable architectural finding.

## STOP

STOP triggered: **NO**.
