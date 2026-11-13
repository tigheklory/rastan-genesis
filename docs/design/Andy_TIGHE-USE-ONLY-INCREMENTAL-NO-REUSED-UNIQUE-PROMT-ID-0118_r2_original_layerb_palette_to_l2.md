# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0118 — R2 original Layer-B palette to Genesis L2 (incomplete session record)

**Author:** Andy · **Date:** 2026-11-10/11 · **Status:** INCOMPLETE — session stopped before a candidate was built.
Continued and completed under PROMT-ID-0119. This document records what was actually done and found in 0118.

## Context / correction from 0117

0118 superseded an earlier mis-direction (PROMT-ID-0115 follow-up / 0562) in which I was about to install a
**static** copy of candidate arcade palette data at `$5DC4E` onto Genesis CRAM Line 2. 0118 explicitly forbade
that: no hardcoded R2 palette, no static blob, no `$5DC4E` copy, no `record>=23` palette-line rule. The correct
architecture is semantic:

    ALL gameplay Plane-B tiles -> Genesis CRAM Line 2
    original arcade palette code -> selects the active Layer-B palette for the round/scene
    existing arcade->Genesis translation -> Genesis CRAM Line 2

I abandoned the static-install approach immediately.

## What 0118 established (findings)

1. **Build 0562 was a Round-2 special case and is rejected.** 0562 forced the generated
   `plane_b_scene_fill_maps.bin` Plane-B tiles to Line 2 only for `record >= 23`. That is a round-number rule,
   not semantic ownership, and it only fixed the *initial* scene-fill path — the later *streamed* Plane-B path
   still used the arcade `attr&3` bits (Line 3 for R2), which is why Tighe saw the initialized screen and the
   newly-streamed background use two different wrong colour sets.

2. **Plane-B palette-line derivation.** Native Plane B takes its Genesis palette line from the arcade PC080SN
   `attr&3` bank-select: R1 background tiles carry `attr&3==2` (Genesis Line 2, the dedicated background line);
   R2 background tiles carry `attr&3==3` (Genesis Line 3). PROMT-ID-0115 put the authored Layer-A palette on
   Line 3, so R2's background was drawn with the foreground palette (the "purple trees" in 0561, then the R1-sky
   colours in 0562 once the tiles were moved to Line 2 but Line 2 still held Round 1's palette).

3. **The runtime attr LUT is shared.** `genesistan_pc080sn_attr_lut` (32 words, pal|flip|prio -> name-word attr)
   is consumed by ~18 sites across Plane A, Plane B, text, HUD and glyph renderers, so it cannot be globally
   rewritten. The correct fix is Plane-B-specific normalization (force the palette-line index to 2) at each
   gameplay Plane-B producer.

4. **Authored Lines 0/1/3 gate defect (sprite-colour timing).** The retained arcade palette producers
   (`genesistan_palette_hook_59ad4`, `_3ba64`, `_45dae`) protect the Test-2.0-authored Lines 0/1/3 only when
   `genesistan_current_scene_id==1` AND `A5+0x1242 (stage) < 23`. The `< 23` term is an R1-only artifact: Round 2
   (same authored scene_id==1) falls through and the producer overwrites authored Lines 0/1/3 with arcade
   colours -> wrong mapped-sprite colours at R2 entry, "repaired" only when a later authored install re-runs
   (reseed / epoch boundary / respawn). This was diagnosed, not yet repaired, in 0118.

5. **R1 Layer-B chain (partial).** The arcade per-round outdoor palette table (arcade `0x59EC8`, 6 entries) is
   consumed by the gameplay scene loader and passed to `genesistan_palette_hook_59ad4` with D0(bank)=2, which the
   Genesis hook translates to CRAM Line 2. `genesistan_palette_hook_3ba64` additionally routes arcade palette-RAM
   bank 48 -> Line 2. The BG fade path (arcade `0x45dc4` -> `0x200600` via the plain memcpy `0x3a2d0`) is NOT one
   of the hooked conversion routines, so those writes are dropped on Genesis. `$5DC4E` is `0x59EC8[1]` (the
   round-2 entry of that table) — candidate oracle data only; whether the original program selects it for R2 at
   gameplay entry was not proven statically and needs runtime (MAME) measurement of `A5+0x118`.

## What 0118 changed in the working tree (staged, not built)

- `compile_pc080sn_genesis.py`: scene-fill Plane-B line rule (initially `record>=23`, later revised toward
  semantic in 0119).
- `verify_plane_a_scene_fill_maps.py`: mirror of the generator rule.
- `tilemap_hooks.s`: began forcing the gameplay Plane-B palette-line index to 2 in the streamed helper
  `.Lplane_b_native_attr_from_word`, `genesistan_hook_tilemap_bg_fill`, `genesistan_hook_tilemap_bg_blockcopy`.

## What 0118 did NOT finish (handed to 0119)

- Full audit of every `genesistan_pc080sn_attr_lut` consumer.
- The authored Lines 0/1/3 gate repair.
- Converting the scene-fill rule from `record>=23` to true semantic ownership.
- Building a candidate.
- This report and the 0119 report.

## Environment blocker (persisted from 0115 onward)

MAME wedges at init in this sandbox (0% CPU, ignores its own `timeout`), so no runtime acceptance, no
`A5+0x118` measurement, and no staged-L2 before/after capture were possible. Build gates that launch MAME
(entry, epoch, post-number 30s trace) had to be killed to let builds number, exactly as for 0560/0561/0562.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0118`
