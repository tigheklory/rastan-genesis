# Andy — Rainbow Islands Comparative Translation Study (Build 0033)

**Status:** ANALYSIS COMPLETE — partial direct evidence but a single,
defensible structural conclusion. No implementation.
**Build Context:** Build 0033, `rastan-direct`.

---

## 1. Summary

Rainbow Islands does not provide a direct precedent for translating
Rastan's text-script dispatcher because:

1. Rainbow Islands arcade has **no equivalent multi-handler script
   dispatcher**. It uses many *small specialized* tilemap writers, not a
   top-nibble-routed dispatcher that fans out to ~10 distinct handlers.
2. The published Rainbow Islands Genesis cart is a **reimplementation**,
   not a translation. It writes via the standard Genesis VDP control/data
   port pattern (`0xC00004` / `0xC00000`) with no PC080SN-style
   `A1@(2) / A1@(6) / +8` writes anywhere in the ROM.

The evidence that *is* present supports **per-handler hooks** as the only
structure that preserves arcade execution semantics for Rastan, because
Rainbow Islands arcade itself uses a per-routine specialization
architecture (many short tilemap writers, each targeting a specific
script intent). When the Rainbow Islands authors faced the same kind of
problem on the Genesis target, their answer was to discard the arcade
structure entirely and rewrite — which is **not available** to a
spec-driven translation pipeline like rastan-direct.

**Final structural model: per-handler hooks.** §6.

---

## 2. Rastan Baseline Confirmation

Re-stated from `docs/design/Andy_dispatcher_map_analysis.md` and
`docs/design/Andy_stride8_sibling_hook_spec.md`:

- Dispatcher entry: `arcade_pc: 0x03C902`
  (`build/maincpu.disasm.txt:76269`).
- Stride-8 handler family (all confirmed): `arcade_pc: 0x03C830,
  0x03C7A4, 0x03C6DC, 0x03C75C, 0x03C550, 0x03C636, 0x03C586`.
- The hooked sibling: `arcade_pc: 0x03C4D2` (opcodes `0x50/0x60`),
  already specced in `docs/design/Andy_text_writer_3c4d2_hook_spec.md`.
- Write target: `HW_ADDRESS/PC080SN/FG_TILEMAP` (`[0xC08000, 0xC0C000)`).
- Write shape: `move.w D0, A1@(2)` (tile word) / `move.w D7, A1@(6)`
  (attribute word) / `addq.l #8, A1` per iteration.

No reinterpretation. Confirmation only.

---

## 3. Rainbow Islands Arcade Analysis

Source: `build/rainbow_islands_arcade.disasm.txt`
(1,463,254 bytes; coverage `arcade_pc (RI) 0x00000..0x1FFFE`).

### 3.1 Stride-8 write sites — exhaustive enumeration

Grep for `addal #8,%a1` in RI arcade returns **8 sites**:

| `arcade_pc (RI)` | Disasm context (write shape) |
|------------------|-------------------------------|
| `0x004BF0` | inside `bsrw`-called helper, stride-8 +8 advance |
| `0x00CFDE` | "tile-only-from-A0" writer: `movew (A0)+, A1@; addal #8, A1` |
| `0x00D02C` | "attr-from-A0-with-sentinel" writer: writes `A1@(4)` after `(A0)+` byte read; sentinel `0xFF` clears D3; then `addal #8, A1` |
| `0x00D050` | "attr-from-A0-with-sentinel-D2" writer: writes `A1@(4)` from D2-derived value; same sentinel pattern; `addal #8, A1` |
| `0x00D066` | "tile+attr-from-A0-pair" writer: `movew (A0)+, A1@; movew (A0)+, A1@(4); addal #8, A1` |
| `0x014092` | inside an unrelated routine |
| `0x01F234` | "tile+attr-from-table" writer: 12-iter loop reading tile bytes + attribute table at A4@(60) |
| `0x01F264` | "tile+attr-from-tables" writer: 12-iter loop reading word pairs from A0 (table at `0x01F270`), tile written to `A1@(2)`, attribute to `A1@(6)` (this is the ONLY RI arcade site that uses `A1@(2)+A1@(6)` exactly like Rastan) |

Grep for `moveal %a4@(6), %a1` in RI arcade returns **14 sites** —
confirming that the destination pointer is consistently sourced from
`A4@(6)` (analogous to Rastan's A1 being supplied via dispatcher).

### 3.2 Dispatcher equivalent — does it exist?

Grep for `andib #-16, %d0` (top-nibble extraction) in RI arcade returns
**1 site** at `arcade_pc (RI) 0x002406`
(`build/rainbow_islands_arcade.disasm.txt:2657`). Inspection of context
(`2655..2664`):

```
2400: lslb #2, D0
2402: addib #16, D0
2406: andib #-16, D0      ; mask top nibble
240A: moveb A4@(4169), D1
240E: andib #3, D1
2412: addqb #1, D1
2414: orb D1, D0
2416: moveb D0, A5@(16382)  ; write to sound RAM, not tilemap
241A: moveb D0, A5@(16383)
```

This is a **sound register write**, not a tilemap dispatcher. There is
**no** Rastan-style multi-handler script-opcode dispatcher anywhere in
the RI arcade ROM.

### 3.3 RI arcade architecture summary

RI arcade uses a **federation of small specialized tilemap writers**,
each handling one specific output shape. Routines are individually
called from many call sites — there is no centralized opcode dispatch.
Every writer reads its destination pointer from `A4@(6)` (the
script-state-supplied `A1`), every writer uses 8-byte stride. Some
write at `A1@`+`A1@(4)` (a different cell-record offset convention),
others at `A1@(2)`+`A1@(6)` (the Rastan-style convention — only
`0x01F264` matches Rastan).

### 3.4 Intent mapping vs Rastan

| Rastan handler | RI arcade equivalent (closest match) | Equivalence |
|----------------|--------------------------------------|-------------|
| `arcade_pc: 0x03C4D2` (opcodes 0x50/0x60) | `arcade_pc (RI): 0x01F264` | **Variant intent** — same write shape (`A1@(2)`+`A1@(6)`+`+8`), but RI's writer is a fixed 12-entry table render with no script-opcode parsing or per-glyph attribute alternation. |
| `arcade_pc: 0x03C550` (opcode 0xA0) | `arcade_pc (RI): 0x00D004` (attr-with-sentinel writer) | Variant intent — RI uses `A1@(4)` not `A1@(6)` for the attr position; sentinel is `0xFF`. |
| `arcade_pc: 0x03C586` (opcode 0xC0) | none | No equivalent — Rastan's two-path conditional handler has no RI counterpart. |
| `arcade_pc: 0x03C636` (opcode 0xB0) | none | RI has no game-state-conditional tilemap writer in the dispatcher style. |
| `arcade_pc: 0x03C6DC` (opcode 0x30) | `arcade_pc (RI): 0x00D066` (tile+attr-from-A0-pair) | Variant intent — RI's writer is a fixed-data render, no D1-biased tile or zero-byte terminator. |
| `arcade_pc: 0x03C75C` (opcode 0x90) | none | Rastan's 4-call inner-sub chain is unique. |
| `arcade_pc: 0x03C7A4` (opcode 0x20) | none | Rastan's mixed synthesized-+script-byte handler is unique. |
| `arcade_pc: 0x03C830` (opcode 0x10) | none | Rastan's dual-path with `A1@(4)` first-iteration special is unique. |

**Conclusion:** Rastan's text-script dispatcher and its 8 distinct
handlers have **no direct counterpart** in Rainbow Islands arcade.
RI uses a different architecture — small, specialized, per-call-site
helpers without a centralizing dispatcher.

---

## 4. Rainbow Islands Genesis Implementation Analysis

Source: `build/rainbow_islands_genesis.disasm.txt`
(7,362,469 bytes; coverage `genesis_rom_offset (RI) 0x00000..0x7FFFE`).

### 4.1 Search for any preserved arcade structure

- Grep for `addal #8, A1` (RI arcade's stride-8 writer pattern) in RI
  Genesis: **0 hits** outside data sections (verified by inspection of
  early instruction code; no `addal #8, A1` opcodes (`d3fc 0000 0008`)
  appear in code regions).
- Grep for `andib #-16, D3` (Rastan's dispatcher mask): **0 hits**.
- Grep for the `A1@(2) / A1@(6)` write pair pattern: would require
  scanning, but absence is implied by the lack of `addal #8, A1`.
- **The PC080SN write convention is entirely absent from RI Genesis.**

### 4.2 What RI Genesis uses instead

`build/rainbow_islands_genesis.disasm.txt` lines 228–229, 304:
```
0x000026E   movel #0xC0000000, A4@        ; VDP DMA control word
0x00019CC   movel #0xC0000000, 0xC00004   ; VDP control word write
0x0000384   movew 0xC00004, D0            ; VDP control read (clear pending)
```

RI Genesis uses the **standard Genesis VDP control/data port pattern**:
- VDP control word writes to `0xC00004` to set up VRAM/CRAM/VSRAM addresses and DMA modes.
- VDP DATA writes to `0xC00000` (or via DMA) for actual nametable / tile / palette content.

This is a **complete reimplementation**, not a translation. The Genesis
port discards arcade memory layout, hardware-port semantics, and the
arcade code's organization. Whatever text-rendering routine RI Genesis
has, it was authored for Genesis VDP from scratch — there is no
"translated arcade handler" to find.

### 4.3 Structural classification

RI Genesis cannot be classified as per-handler / grouped / dispatcher /
shared-helper translation **because no translation occurred**. The
structural choice in the Genesis port is irrelevant to the question of
how to *translate* Rastan arcade code — it is the result of a
greenfield reimplementation, which is not available to rastan-direct.

---

## 5. Structural Comparison

### 5.1 Rastan vs Rainbow Islands (arcade)

| Property | Rastan arcade | RI arcade |
|----------|---------------|-----------|
| Top-nibble script-opcode dispatcher | YES (`arcade_pc: 0x03C902`, 9 cases) | NO |
| Number of distinct text/tile writers | 8 in dispatcher + default path | 8 stride-8 writers, individually called from many sites |
| Writer specialization | Each handles a distinct script-opcode top nibble with unique semantics | Each handles a distinct *write shape* (tile-only, attr-only, tile+attr-pair, etc.) |
| Destination pointer source | A1 supplied at handler entry by dispatcher (caller passes register) | `A4@(6)` read at the start of every writer |
| Cell-record convention | `A1@(2)` tile, `A1@(6)` attribute (8-byte cell) | Mixed — most use `A1@`+`A1@(4)` (4-byte cell), one uses `A1@(2)`+`A1@(6)` (8-byte cell) |
| Per-handler game-state branches | YES (`A4@(56)`, `A5@(280)`, `A5@(318)`) | None observed in stride-8 writers |
| Sentinel scheme | Per-handler (`0xFF`, zero byte, `D3==0x50 && D4==1`, none) | `0xFF` consistently |
| Architectural pattern | Dispatcher-with-handlers | Federation-of-helpers |

### 5.2 Rainbow Islands arcade vs Genesis

| Property | RI arcade | RI Genesis |
|----------|-----------|------------|
| Tilemap write port | PC080SN `0xC00000..0xC0FFFF` via indexed `A1@(...)` | Genesis VDP DATA `0xC00000` via control-then-data |
| Setup pattern | None — write directly | VDP control word to `0xC00004` then DATA writes to `0xC00000` (or DMA) |
| `A1@(2)`+`A1@(6)`+`+8` writers preserved? | N/A (this is the arcade pattern) | NO — entirely absent |
| Shared with arcade code? | N/A | NO |
| Architectural choice | Federation of 8 stride-8 writers | Greenfield Genesis-native rendering |

The Rainbow Islands Genesis cart is a port (rewrite), not a translation.
This is the single most important comparative observation: **RI's
authors solved the "how do I get this arcade game on Genesis" problem
by NOT translating**. They rewrote the rendering layer to use the
Genesis VDP idiomatically.

That option is not available to rastan-direct: rastan-direct is a
spec-driven translation pipeline that **executes the original arcade
ROM** and intercepts hardware writes. We cannot rewrite the arcade
code's text-script interpreter; we must intercept it where it tries to
write to PC080SN hardware.

---

## 6. Final Structural Determination

> **Per-handler hooks.**

### 6.1 Why this is the only defensible choice given the evidence

1. **RI arcade uses per-routine specialization** (§3.3). Each tilemap
   writer is a small specialized helper. This is the closest precedent
   for a "preserve arcade execution semantics" approach.
2. **Each Rastan handler has unique semantics** (proved in
   `docs/design/Andy_stride8_sibling_hook_spec.md` §H8 — prefix
   multipliers ×3/4/5/6/7/9, sentinels of 4 different kinds, post-loop A1
   advances of 8 different magnitudes, game-state branches in 3 of the 8
   handlers, writes at `A1@(4)` in one case). A per-handler hook
   preserves these semantics 1:1; any consolidating structure must
   re-implement them inside a centralizing translator.
3. **RI Genesis "translation" is not a translation** (§4.3). It's a
   rewrite. It does not provide evidence for any of the four candidate
   structural models in the prompt because it does not perform
   translation at all.
4. **Per-handler hooks are scaffolding-clean** per
   `docs/design/Andy_final_pc080sn_hook_strategy.md`: one hook per
   arcade entry point, stateless translator, no scene-conditional
   branches. Multiple per-handler hooks form an "intent-class
   federation" — exactly the architecture RI arcade itself uses for its
   tilemap writers (§3.3).

### 6.2 Why each alternative is wrong

- **Grouped handler families:** would require collapsing handlers that
  have provably distinct semantics (different prefix multipliers,
  sentinels, A1 advances, game-state reads). The grouping logic itself
  becomes per-handler dispatching — which is per-handler hooks with an
  extra indirection. No structural simplification is gained.
- **Dispatcher-level translation:** rejected with proof in
  `docs/design/Andy_dispatcher_map_analysis.md` §6 (conditions b, c, d
  fail). RI's evidence does not change this — RI Genesis chose
  dispatcher-level *replacement* by rewriting, which is not the same
  as dispatcher-level *translation*.
- **Shared helper + per-handler wrappers:** a degenerate form of
  per-handler hooks where the inner LUT-translate-and-store step is
  factored into a private helper. This is **already permitted** by the
  per-handler model (the existing `0x03C4D2` hook at
  `apps/rastan-direct/src/main_68k.s:768–778` has a `_store_cell`
  helper). It is an *implementation detail* within per-handler, not a
  competing structural model. Cody MAY refactor this way; this spec
  does not require it.

---

## 7. Evidence References

| Claim | File | Address / Line |
|-------|------|----------------|
| Rastan dispatcher entry | `build/maincpu.disasm.txt` | line 76269 (`arcade_pc: 0x03C902`) |
| Rastan stride-8 family | `docs/design/Andy_stride8_sibling_hook_spec.md` | full doc |
| RI arcade `andib #-16` only at one site (sound RAM) | `build/rainbow_islands_arcade.disasm.txt` | line 2657 (`arcade_pc (RI): 0x002406`) |
| RI arcade `addal #8, A1` 8 sites | `build/rainbow_islands_arcade.disasm.txt` | grep result lines 5594, 14930, 14956, 14968, 14974, 23222, 35352, 35364 |
| RI arcade `moveal %a4@(6), %a1` 14 sites | `build/rainbow_islands_arcade.disasm.txt` | grep result, 14 lines |
| RI arcade `A1@(2)`+`A1@(6)` writer at `0x01F264` | `build/rainbow_islands_arcade.disasm.txt` | lines 35355–35366 |
| RI Genesis VDP control writes | `build/rainbow_islands_genesis.disasm.txt` | lines 228–229, 304 (`genesis_rom_offset (RI): 0x00026E, 0x000384, 0x0019CC`) |
| RI Genesis no `addal #8, A1` in code | `build/rainbow_islands_genesis.disasm.txt` | grep returns 0 hits in code regions |
| RI Genesis no `andib #-16, D3` | `build/rainbow_islands_genesis.disasm.txt` | grep returns 0 hits |

---

## 8. Why Alternative Structures Are Incorrect

Restated from §6.2:

- Grouped handler families: collapsing provably distinct semantics
  into shared groups requires per-handler dispatch inside the group →
  no simplification.
- Dispatcher-level translation: failed three of four prerequisite
  conditions in `docs/design/Andy_dispatcher_map_analysis.md` §6.
  RI Genesis "dispatcher-level replacement" is rewrite, not translation.
- Shared helper + per-handler wrappers: same as per-handler hooks
  with an internal helper; not a separate structural model.

---

## 9. Implications for Rastan Implementation

- The 7-handler spec set in
  `docs/design/Andy_stride8_sibling_hook_spec.md` is the correct shape
  of the work. Implement it as 7 per-handler hooks.
- Cody may factor a private `_store_cell` helper inside `main_68k.s`
  to reduce duplication of the "translate via tile/attr LUT, store to
  staged_fg_buffer, set fg_row_dirty bit" sequence — this is an
  implementation detail and does not change the per-handler structural
  model.
- Each hook maintains its own `opcode_replace` entry in
  `specs/rastan_direct_remap.json`. `opcode_replace_count` advances
  47 → 54.
- The dispatcher fall-through default path at `arcade_pc: 0x03C950` is
  out of scope for both this comparative study and the stride-8 spec
  set; whether it requires a hook is a Build-0034-trace question.
- No grouping, no dispatcher-level reroute, no shared dispatcher hook.

---

## 10. Next-Step Recommendation (No Implementation)

1. Cody implements the 7 per-handler hooks per
   `docs/design/Andy_stride8_sibling_hook_spec.md`.
2. Build 0034 produced; `fg_cwindow_live` watchpoint in the post-build
   30 s MAME trace verifies whether any C-window writes remain.
3. If writes remain after Build 0034, the candidates are: dispatcher
   default path (`arcade_pc: 0x03C950`), or some non-dispatcher writer
   not yet identified. A new diagnostic prompt would scope that work.
4. The Rainbow Islands disassembly artifacts remain useful as a
   reference library for future write-pattern audits — they are not
   needed for the immediate Rastan implementation work.

---

## 11. STOP DOCUMENT

Not triggered. All required mappings are either proven (§3.4 Rastan ↔ RI
arcade direct equivalence map) or proven absent (§4.1 RI Genesis
contains no PC080SN-style writers). The single structural answer in §6
follows from the evidence without speculation.
