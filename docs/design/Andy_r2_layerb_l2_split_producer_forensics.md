# R2 Layer-B palette-line split (L2 vs L3) — producer/generator forensics

**Author:** Andy · **Date:** 2026-11-12 · **Type:** READ-ONLY forensics. No source changed, no build
produced. Build 0564 (Tighe-accepted throne/frontend recovery) is the baseline under inspection, untouched.

## Symptom (Tighe, BlastEm VDP Plane Viewer, Build 0564 direct-start R2-S1)

In Round 2 Subround 1, the Layer-B (Plane B) nametable shows **two different palette lines at once**: some
Plane-B tiles resolve on Genesis CRAM **Line 2** (correct), others on **Line 3** (wrong). Tighe's own read was:
"the tiles in the *initial scene load* use L2, and the Layer-B tiles loaded *after* the scene load use L3." That
read is correct. This document proves the exact mechanism.

In R1 the whole of Layer B is uniformly on L2 and looks correct, so the question driving the forensics was:
*how is R1 Layer B connected to L2, and why doesn't that same connection hold in R2?*

## Discovery 1 — the arcade data itself differs by round (measured, not assumed)

The arcade PC080SN background descriptors carry a 2-bit palette-select field (`attr & 3`). Measured directly
from `build/regions/maincpu.bin` over the Plane-B descriptor table (`PLANE_B_DESC_TABLE = 0x3951C`,
stride 6, `{attr16, src32}`), across the decoded per-record descriptor spans:

```
R1 records 0..22 : attr&3 histogram = {2: 48}   -> every R1 Plane-B descriptor is PC080SN bank 2
R2 records 23..45: attr&3 histogram = {3: 48}   -> every R2 Plane-B descriptor is PC080SN bank 3
```

So the arcade program authored **R1 Layer B on palette bank 2 and R2 Layer B on palette bank 3.** This is the
root fact everything else follows from. (Reproduce: decode `decode_plane_b_progression(mc, 0)` +
`(mc, 23)` from `tools/translation/compile_pc080sn_genesis.py`, walk each record's `descriptor_before` span,
read `attr&3` for descriptors with a valid `src`.)

## Discovery 2 — the shared attr LUT is a 1:1 identity passthrough bank -> line

`tools/translation/precompute_pc080sn_attr_lut.py` builds `genesistan_pc080sn_attr_lut` (32 entries). The
palette line is taken straight from the arcade bank with no remapping:

```python
# precompute_pc080sn_attr_lut.py:12-20
pal = key & 0x03                                   # arcade PC080SN palette-select (attr&3)
values.append((prio << 15) | (pal << 13) | (vflip << 12) | (hflip << 11))
```

`pal << 13` places the bank number directly into the Genesis palette-line field. The mapping is identity:

| arcade bank (`attr&3`) | Genesis CRAM line |
|---|---|
| 0 | Line 0 |
| 1 | Line 1 |
| **2** | **Line 2** |
| **3** | **Line 3** |

Consequence: any Plane-B path that resolves its palette line *through this LUT* reproduces the arcade bank as
the Genesis line — **Line 2 for R1 (bank 2), Line 3 for R2 (bank 3).** There is no round awareness in the LUT.

## Discovery 3 — there is an explicit "force Line 2" rule, added by PROMT-ID-0118, but it lives in only ONE of the two Plane-B generators

The semantic rule "gameplay Plane B is the owner of CRAM Line 2 in **every** round, regardless of the arcade
bank" was introduced in 0118. It overrides the identity passthrough. It is present in the **scene-fill**
generator and **absent** from the **visual-records** generator.

Plane B is fed by two independent generators:

| Generator | Produces | Consumed by (runtime) | Palette-line logic |
|---|---|---|---|
| `tools/translation/compile_pc080sn_genesis.py` | `plane_b_scene_fill_maps.bin` | the scene-entry fill (`genesistan_plane_b_scene_fill_maps`, [tilemap_hooks.s:1003](../../apps/rastan-direct/src/tilemap_hooks.s#L1003)) | **explicit force** |
| `tools/translation/gen_pc080sn_plane_b_visual_records.py` | `pc080sn_plane_b_visual_records.bin` | the row / vertical-pan producer (`.Lplane_b_publish_logical_row_native`, [tilemap_hooks.s:1965](../../apps/rastan-direct/src/tilemap_hooks.s#L1965)) | **passthrough only** |

Scene-fill generator — forces Line 2 for any real tile, every round:

```python
# compile_pc080sn_genesis.py:1268-1272
plane_b_line = PLANE_B_PALETTE_LINE if slot else (attr & 0x0003)   # PLANE_B_PALETTE_LINE = 2
native_attr = ((((attr >> 13) & 1) << 15) | (plane_b_line << 13) | ...)
```

Visual-records generator — no force; it looks the native attribute up in the identity LUT, keyed by the arcade
bank:

```python
# gen_pc080sn_plane_b_visual_records.py:39-56
def attr_key(word): return (word & 0x0003) | (((word>>14)&1)<<2) | (((word>>15)&1)<<3) | (((word>>13)&1)<<4)
...
key = attr_key(attr)                     # preserves attr&3
native_attr = be16(attr_lut, key * 2)    # identity LUT -> bank becomes line
```

So the visual-records blob bakes **Line 2 for R1** (bank 2) and **Line 3 for R2** (bank 3). It has no
knowledge of the Line-2 ownership rule.

## Discovery 4 — the runtime side mirrors the generator split: three producers normalize, one does not

| Plane-B runtime producer | Where | Line source | R1 | R2 |
|---|---|---|---|---|
| Scene-entry fill | `genesistan_plane_b_scene_fill_maps` ([:1003](../../apps/rastan-direct/src/tilemap_hooks.s#L1003)) | baked by scene-fill generator (forced L2) | L2 | **L2** |
| Streamed cell / entering column | `.Lplane_b_stage_gameplay_producer_cell_native` ([:2082](../../apps/rastan-direct/src/tilemap_hooks.s#L2082)) | calls `.Lplane_b_native_attr_from_word` -> `moveq #2` ([:2116](../../apps/rastan-direct/src/tilemap_hooks.s#L2116)) | L2 | **L2** |
| Three shared BG producers (fill / blockcopy / desc-loop) | [:2909](../../apps/rastan-direct/src/tilemap_hooks.s#L2909) / [:3277](../../apps/rastan-direct/src/tilemap_hooks.s#L3277) / [:2490](../../apps/rastan-direct/src/tilemap_hooks.s#L2490) | gated `scene_id==1` -> `moveq #2` (PROMT-ID-0124) | L2 | **L2** |
| **Row / vertical-pan refresh** | `.Lplane_b_publish_logical_row_native` ([:1965](../../apps/rastan-direct/src/tilemap_hooks.s#L1965)) | reads baked attr straight from `plane_b_visual_records` ([:2035](../../apps/rastan-direct/src/tilemap_hooks.s#L2035)), ORs it in ([:2059](../../apps/rastan-direct/src/tilemap_hooks.s#L2059)); **never calls `.Lplane_b_native_attr_from_word`** | L2 | **L3** |

`.Lplane_b_native_attr_from_word` ([tilemap_hooks.s:301-310](../../apps/rastan-direct/src/tilemap_hooks.s#L301))
is the asm that unconditionally forces `moveq #2`. The row producer is the single Plane-B path that bypasses it
and instead trusts the baked `plane_b_visual_records` attribute.

## Why R1 is uniformly L2 and R2 splits — the synthesis

In **R1** the arcade bank (2) and the forced rule (2) are the **same number**, so every path agrees:

- the force-L2 paths (scene-fill, cell producer, shared producers) emit Line 2;
- the passthrough path (row producer / visual-records) *also* emits Line 2, because R1's bank is 2.

There is no way to distinguish "forced" from "passthrough" in R1 — both land on Line 2. (This is also why the
0118 change verified **byte-identical** for R1: forcing 2 over an already-2 value changes nothing.)

In **R2** the arcade bank (3) and the forced rule (2) **disagree**:

- the force-L2 paths emit Line 2 (the fix doing its job);
- the passthrough path emits **Line 3**, faithfully reproducing bank 3.

That disagreement is exactly the visible split. The tiles placed at scene load (scene-fill / cell / shared
producers) are L2; the tiles refreshed afterward by the row / vertical-pan producer carry the baked R2 Line 3 —
which matches Tighe's "initial load L2, after load L3" observation precisely.

### Direct answer to the two framing questions
- **"How is R1 Layer B connected to L2?"** Two ways that happen to coincide: the scene-fill generator
  *explicitly* forces Line 2, and the arcade data *already* uses bank 2 which the identity LUT passes through to
  Line 2. R1 is correct on every path because data and rule agree at the value 2.
- **"Why didn't that work in R2?"** The *explicit* force-L2 rule was only wired into one generator (scene-fill)
  and three of the four runtime producers. The fourth path (row producer + `gen_pc080sn_plane_b_visual_records.py`)
  has no rule and only ever produced L2 for R1 by coincidence of bank==line. R2's bank is 3, so that unguarded
  path produces Line 3.

## Fix direction (NOT implemented here)

One coherent normalization closes the gap — make the row-producer family obey the same Line-2 ownership rule
the rest already do. Either, equivalently:

1. **Generator side (preferred, matches the scene-fill generator):** in
   `gen_pc080sn_plane_b_visual_records.py`, replace the identity-LUT lookup with the slot-based force so a real
   Plane-B tile emits Line 2 regardless of `attr&3` — mirroring `compile_pc080sn_genesis.py:1268`. This keeps R1
   byte-identical (R1 already 2) and corrects R2.
2. **Runtime side:** have `.Lplane_b_publish_logical_row_native` route its attribute word through
   `.Lplane_b_native_attr_from_word` (as the cell producer already does at
   [tilemap_hooks.s:2116](../../apps/rastan-direct/src/tilemap_hooks.s#L2116)) instead of ORing the baked bits
   directly.

Option 1 is the cleaner cut: it fixes the data at the one generator that still lacks the semantic rule, keeping
the Line-2 ownership decision in the compile stage with its sibling. This is the known-deferred R2 Layer-B item;
Build 0564 is to remain untouched until Tighe authorizes the change.

## RESOLUTION (PROMT-ID-0131, 2026-11-12, Build 0566)

### A. Offline Plane-B L2 tile fix (the L2/L3 split) — IMPLEMENTED
The split's single remaining cause (Discovery 3/4: the row/vertical-pan producer's generator never applied
the Line-2 ownership rule) is fixed **entirely offline**, in
`tools/translation/gen_pc080sn_plane_b_visual_records.py`:

```python
# force the palette-line field to Line 2 for every real tile, preserving prio/Hflip/Vflip/source:
native_attr = (native_attr & 0x9FFF) | (0x2 << 13)
```

`verify_pc080sn_plane_b_visual_records.py` now asserts `((native_attr >> 13) & 3) == 2` for every valid
record — a standalone proof of the rule, not mere generator self-consistency. Regeneration result:
- NEW valid-record palette-line histogram: **{2: 392}** (was {0:63, 1:107, 2:93, 3:129}).
- **299 records changed** (arcade banks 0/1/3 → L2); **0 bank-2 (R1 Plane-B) records changed → R1 byte-identical.**

Combined with the already-correct L2 forcing in the other three Plane-B producers (scene-fill maps; the
cell/column producer `.Lplane_b_native_attr_from_word`; the three 0124-gated shared BG producers), **all
gameplay Plane-B paths now select Genesis L2 in every round.**

### B. Runtime conversion removals — NONE (correct)
Per the review that shaped PROMT-ID-0131, the live-fed producers (cell/column at
[tilemap_hooks.s:5369](../../apps/rastan-direct/src/tilemap_hooks.s#L5369)→2116; the three shared BG
producers, 0124-gated) consume **live arcade attribute words** and cannot be moved offline; their runtime L2
force is retained. The row producer never had a runtime conversion to remove. So the fix is 100% the offline
generator; zero runtime palette-line conversion was removed, and the 0124 throne gating is untouched.

### C. R2-S1 L2 color CONTENTS — separate system; no production divergence proven
Re-derived from the arcade program (Ghidra exports, decompiler): the retained per-stage Layer-B palette
loader `FUN_00059de8` stages the per-stage outdoor palette to Genesis **L2** via `genesistan_palette_hook_59ad4`
(arcade bank 2 → Line 2, proven routing at [palette_hooks.s:204-230](../../apps/rastan-direct/src/palette_hooks.s#L204)).
It runs only when `a5@0x13b0 == 1` (set by `FUN_00055c22`) and selects by `a5@0x118` (1-based stage). **Every
link in this chain except the one proven-correct hook is original retained arcade code.** There is therefore
no R2-specific divergence in the production path: if the reload fires with `a5@0x118 == 2`, the R2 palette
reaches L2 with no port change.

All of Tighe's wrong-color evidence is from the **direct-start** R2-S1 ROM, which patches only the
stage-decode selector byte and does not reproduce the natural `a5@0x118=2` + `a5@0x13b0=1` reload sequence.
The wrong R2-S1 L2 colors are therefore **most likely a direct-start harness artifact, not a production bug.**
Per the prompt's "natural progression is authority" rule, no production palette change was made. The decisive
confirmation is a runtime read of `a5@0x118`, `a5@0x13b0` and L2 contents at R2-S1 (natural vs direct-start);
MAME is environment-blocked here, so this is handed to Tighe (play natural R1→R2 and compare) before any
production palette change. See the PROMT-ID-0131 report for the full chain and the two outcome branches.

## Evidence index
- `build/regions/maincpu.bin` — attr&3 histograms R1={2:48}, R2={3:48} (Discovery 1).
- `tools/translation/precompute_pc080sn_attr_lut.py:19` — identity `pal << 13` (Discovery 2).
- `tools/translation/compile_pc080sn_genesis.py:1268-1272` — scene-fill force-L2 (Discovery 3).
- `tools/translation/gen_pc080sn_plane_b_visual_records.py:39-56` — visual-records passthrough (Discovery 3).
- `apps/rastan-direct/src/tilemap_hooks.s` — producer map, esp. `:1965` (row producer, L3 leak), `:2035/:2059`
  (baked-attr OR), `:2116` (cell producer forces L2), `:301-310` (`.Lplane_b_native_attr_from_word`).
