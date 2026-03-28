# Build 271 - Title Logo Sprite Translation (Pre-Coin Only)

## Objective
Render RASTAN title-logo sprites from the real pre-coin path only:
- producer: `0x03AAF2 -> 0x05A174`
- renderer: `0x03AAEC -> 0x202B80 -> 0x2005C4`

No launcher/config/debug/exception output used as success proof.

## State Proof (Pre-Coin)
Source: [build271_logo_proof.txt](/home/tighe/projects/rastan-genesis/docs/research/artifacts/build271_logo_proof.txt)

Observed state:
- `screen=00000004`
- `state=0001/0000/0000`
- `credits=0000`

This is pre-coin title state (not coin-up).

## Exact Translation Changes Implemented
File changed: [startup_title_remap.json](/home/tighe/projects/rastan-genesis/specs/startup_title_remap.json)

Build 271 kept/implemented:
1. Stable 0x059F90 extension (no descriptor constant overwrite):
- `arcade_pc 0x059F90`
- `replacement_bytes: 61000124610000044E75`

2. Producer base-address alignment to renderer A5-relative descriptor ownership:
- `0x059F62`: `... -> 0xE0FF11FE`
- `0x059F76/0x059F9A/0x059FDE`: `... -> 0xE0FF01BC`
- `0x059FFC/0x05A014`: `... -> 0xE0FF01C4`
- `0x05A032/0x05A04A`: `... -> 0xE0FF01CC`
- `0x05A068/0x05A080`: `... -> 0xE0FF01D4`
- `0x05A0AE/0x05A1EC`: `... -> 0xE0FF11FE`

Why this is translation (not manual SAT injection):
- It aligns producer-owned descriptor writes to the renderer’s actual consumer address contract (`A5+offset`) instead of hardcoding SAT rows or fake coordinates.

## Execution Proof
Source: [build271_logo_proof.txt](/home/tighe/projects/rastan-genesis/docs/research/artifacts/build271_logo_proof.txt)

Hit counts:
- `HIT 03AAF2 1`
- `HIT 05A174 1`
- `HIT 202B80 2`
- `HIT 2005C4 161`

## Descriptor Proof
Source: [build271_logo_proof.txt](/home/tighe/projects/rastan-genesis/docs/research/artifacts/build271_logo_proof.txt)

At frame 673:
- producer-legacy windows are zero:
  - `A@FF11B2=0000 0000 0000 0000`
  - `B@FF0170=0000 0000 0000 0000`
- renderer-consumed A5-relative windows are nonzero:
  - `A@FF11FE=0080 FEAB 03CA 0000`
  - `B@FF01BC=0003 00E8 0A6A 00A0`

This confirms producer output is now landing in renderer-owned descriptor windows.

## VRAM / SAT / Payload Proof
Source: [build271_logo_proof.txt](/home/tighe/projects/rastan-genesis/docs/research/artifacts/build271_logo_proof.txt)

- VRAM writes: `1028`
- VRAM nonzero words: `766`
- SAT-range writes observed by command decode probe: `0`
- SAT nonzero words observed by command decode probe: `0`
- sprite decode staging remains empty in sampled buffer:
  - `sprite_code0=0000`
  - `tilebuf_nonzero=0/2048`

Additional timing proof:
- [build270_desc_vs_renderer_timeline.txt](/home/tighe/projects/rastan-genesis/docs/research/artifacts/build270_desc_vs_renderer_timeline.txt)
- [build270_spritecode_write_probe.txt](/home/tighe/projects/rastan-genesis/docs/research/artifacts/build270_spritecode_write_probe.txt)

These show descriptor windows become nonzero late, but sprite decode/tile staging for logo cells is still not produced.

## Visual Proof
Pre-exception frame:
- [build271_preexception_frame11_2.png](/home/tighe/projects/rastan-genesis/docs/research/artifacts/build271_preexception_frame11_2.png)

Exception frame (for exclusion reference):
- [build271_exception_frame11_4.png](/home/tighe/projects/rastan-genesis/docs/research/artifacts/build271_exception_frame11_4.png)

Observed pre-exception result:
- visible text fragment (`CREDI`) only
- no visible RASTAN logo sprite pixels proven before exception

## Result Classification
`NOT_COMPLETE` for this task.

What is now true:
- real pre-coin logo producer and renderer paths execute
- descriptor writes are aligned to renderer-owned A5-relative windows

What is not yet true:
- logo sprite tile decode/staging is not materializing (`sprite_code0=0`, tile staging empty)
- visible pre-exception logo sprite output is not yet proven

## Remaining Issues
1. Producer->consumer timing/selection inside `0x2005C4` still leaves logo sprite decode path non-productive for the captured pre-coin window.
2. SAT-visible logo output before exception is still missing.
3. Further work should stay in this same pre-coin producer/renderer chain and avoid launcher/exception/debug proof paths.
