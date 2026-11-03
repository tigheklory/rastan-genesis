# Cody - Build 0174 PC080SN FG Arcade Palette Source Candidate

**Date:** 2026-07-15
**Type:** Analysis-first implementation candidate + runtime evidence
**Build context:** Build 0173 visually rejected; Build 0174 candidate produced and validation-tested
**Build 0173 ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0173.bin`
**Build 0173 SHA256:** `1f8711ac3132481f4e953b2965e09480e3cdb4b1d85d512d2a43b9ed1368d410`
**Build 0174 ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0174.bin`
**Build 0174 SHA256:** `faca6b14b18add340828db00b1c080f602b227d5db05b2ee46b38d4d3c30d7aa`
**Scope:** PC080SN FG arcade palette source / attr / color-bank mapping. No input/control fix, no slowdown fix, no sky-reset fix, no horizontal-FG fix unless proven through the same palette path.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-010 (BG/FG staging and full-plane VDP commit), KF-032 (raw PC080SN writes must route through staging), KF-036 (mapped work-RAM base), KF-043 (Stage 1 visual/input/scroll symptom ledger), KF-045 (Stage 1 FG palette carrier, now corrected by this task), OPEN-001 (rendering), OPEN-017 (active Stage 1 visual/gameplay bring-up), OPEN-022/OPEN-023/OPEN-024 (PC080SN/tall-map contexts), and OPEN-015 (do-not-touch crash-handler context only).

Rediscovery-hazard findings touched: KF-010, KF-032, KF-036, KF-043, KF-045. No contradiction of a CONFIRMED or STRONG finding was accepted silently; KF-045 is explicitly refined because the Build 0174 evidence corrects the earlier Build 0173 palette-line interpretation.

Architecture compliance: **CONFIRMED**. The arcade code remains the program. The Genesis-side changes are helper/palette-routing and staging-path support only. No second renderer, scaffold renderer, diagnostic ROM, or Genesis-owned gameplay control flow was added.

## User Visual Observations Recorded

Tighe's Build 0173 visual observations are recorded as runtime acceptance criteria/context:

- Build 0172 proved the FG 64-row path was active/useful.
- Build 0173 did not fix the FG palette.
- FG tiles are still right, but colors are still wrong.
- Build 0173 foreground colors are not arcade brown/rock/ground; they look purple/blue/white/pink-ish.
- As the screen scrolls right, FG tiles are not updating horizontally to match arcade.
- Rastan remains uncontrollable.
- At the first sky-palette-change point, Genesis resets Rastan to the level start; arcade changes sky palette for time/sunset without resetting.
- Slowdown is still present and deferred.

Only the FG palette-source issue was pursued here.

## Authoritative PC080SN Decode

Source used: `docs/reference/mame/rastan/src/mame/taito/pc080sn.cpp`.

The PC080SN standard tile decode uses a pair of words per cell:

```text
code = m_bg_ram[layer][2 * tile_index + 1] & 0x3fff
attr = m_bg_ram[layer][2 * tile_index]
tileinfo.set(0, code, attr & 0x1ff, TILE_FLIPYX((attr & 0xc000) >> 14))
```

Therefore the low 9 bits of `attr` are the arcade color/palette index. The visible Stage 1 FG samples must be interpreted through the attr word, not guessed from Genesis CRAM line assignment.

## Evidence Artifacts

Trace directory:

`states/traces/build0174_fg_palette_source_20260715_195606/`

Key files:

- `arcade_pc080sn_samples.csv`
- `arcade_palette_banks.csv`
- `genesis_build0173_palette_lines.csv`
- `genesis_build0173_plane_line_usage.csv`
- `genesis_build0174_palette_lines.csv`
- `genesis_build0174_plane_line_usage.csv`
- `genesis0174_palette_line_writers.csv`
- `genesis0174_palette_line1_regtrace.csv`
- `genesis0174_frontend_line_usage.csv`

## Arcade Runtime Findings

Original arcade Stage 1 visible FG samples use attr/color bank `0x0003`. Representative samples:

| HW address | attr | code |
|---|---:|---:|
| `0x00C0A500` | `0x0003` | `0x0420` |
| `0x00C0A608` | `0x0003` | `0x0426` |
| `0x00C0A838` | `0x0003` | `0x00BF` |
| `0x00C0A968` | `0x0003` | `0x00C3` |
| `0x00C08F80` | `0x0003` | `0x0020` |
| `0x00C09000` | `0x0003` | `0x041C` |

Converted original arcade bank 3 at the sampled Stage 1 frame is:

```text
0000 0868 0846 0646 0624 0424 0402 0202 0202 028C 044C 0226 0004 0002 0222 0424
```

This is the palette family the Stage 1 FG terrain is requesting.

## Build 0173 Findings

Build 0173 routed FG cells to Genesis palette line 2. Runtime capture showed:

- BG32/BG64 all use Genesis line 2.
- FG32/FG64 also use Genesis line 2.
- Genesis line 2 exactly matches original arcade bank 2, not arcade bank 3.
- Genesis line 1 matches neither the dumped arcade bank 3 nor the expected terrain palette at gameplay time.

So Build 0173 did not supply the arcade FG bank. It made FG share the BG bank-2 carrier.

## Build 0174 Candidate Applied

A narrow candidate was attempted:

- `apps/rastan-direct/src/tilemap_hooks.s`: `FG_PLANE_ATTR_HI` changed from line 2 to line 1.
- `apps/rastan-direct/src/palette_hooks.s`: palette bank 3 was routed to Genesis line 1 in the inspected palette hooks.
- Canonical invariants updated for the mechanical opcode coverage delta: `0x182490 -> 0x1824A4`; opcode_replace count stayed `151`.

Build 0174 was produced:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0174.bin`
- SHA256: `faca6b14b18add340828db00b1c080f602b227d5db05b2ee46b38d4d3c30d7aa`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Rolling/numbered comparison: byte-identical
- Counter: `173 -> 174`

## Build 0174 Validation Result

Build 0174 correctly moved FG cell attributes to Genesis line 1:

- BG remained on line 2.
- FG moved to line 1.

However, line 1 did **not** contain arcade bank 3 by gameplay time. The candidate therefore did not satisfy the palette-source requirement.

## Exact Divergence

Runtime provenance shows the correct arcade bank 3 values are briefly written into Genesis line 1 by `genesistan_palette_hook_3ba64` at `runtime_genesis_pc 0x00071E0A` around frame 15.

The source for that bank maps through `build/rastan-direct/address_map.json` as:

- `runtime_genesis_rom_offset 0x0004ED56`
- mapped arcade copy source: `arcade_pc/ROM offset 0x0004EB56`

The line-1 values at that point match arcade bank 3:

```text
0000 0868 0846 0646 0624 0424 0402 0202 0202 028C 044C 0226 0004 0002 0222 0424
```

Later, `genesistan_palette_hook_59ad4` writes line 1 again at `runtime_genesis_pc 0x00071CEE` around frames 53 and 130, replacing the bank-3 terrain palette before gameplay. Gameplay then uses FG cells on line 1, but line 1 now contains the later frontend/coined-up palette payload, not arcade bank 3.

## Frontend Constraint

Frontend/title/story screens also use Genesis line 1 for BG content. The trace shows line-1 usage before gameplay, so globally blocking or skipping `0x59AD4` line-1 writes would be unsafe and could regress already-working frontend visuals.

## Classification

**Candidate mechanically valid, visually/source-invalid.**

The arcade Stage 1 FG terrain requests PC080SN color bank 3. The Build 0174 candidate proved that bank 3 can be converted into a Genesis CRAM line and that FG can be pointed at that line. The failure is carrier lifetime: the chosen line is overwritten before gameplay and not restored when Stage 1 FG is drawn.

This is not a tile-code problem, not a 64-row projection problem, and not proof that FG should return to line 2 or line 3.

## Recommended Next Boundary

The next implementation should preserve frontend line-1 behavior and restore/load the arcade bank-3 terrain palette at a gameplay-appropriate FG palette boundary.

Recommended narrow boundary for a future build:

- Source the 16 arcade bank-3 words from `runtime_genesis_rom_offset 0x0004ED56` / JSON-mapped arcade `0x0004EB56`.
- Convert them through the same established palette conversion path used by `genesistan_palette_hook_3ba64`.
- Write the converted values into the Genesis line used by Stage 1 FG cells.
- Set `palette_dirty`.
- Guard the operation or place it at a proven gameplay/Stage-1 palette boundary so frontend line-1 writes remain intact.

A global `0x59AD4` line-1 suppression is not recommended.

## Deferred / Non-Actions

No input/control fix was attempted. No slowdown fix was attempted. No sky-palette reset fix was attempted. No horizontal FG update fix was attempted. No collision, sprite, D00298, crash-handler, or OPEN-015 work was performed.

## OPEN / KNOWN_FINDINGS Impact

OPEN-017 remains open. OPEN-001 remains open. OPEN-015 remains deferred. No issue was closed.

KNOWN_FINDINGS impact: **Option C - KF-045 refined**. The prior Build 0173 wording is corrected to record that Stage 1 FG uses arcade bank 3, not Genesis line 2 as a final carrier. The line-2 interpretation was a candidate artifact, not the arcade-intent palette source.

## STOP

STOP triggered: **YES, limited**. Build 0174 was produced, but validation showed the candidate does not deliver the correct arcade FG palette into gameplay. Further implementation should wait for a follow-up directive targeting the proven line-1 carrier lifetime / gameplay-bank-3 restore boundary.
