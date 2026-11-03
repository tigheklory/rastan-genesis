# Cody - Title Wrong Sprites and Missing Score Semantic Trace

**Date:** 2026-07-02
**Type:** Evidence / attribution only
**Build:** rastan-direct Build 0126
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0126.bin`
**ROM SHA256:** `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921`
**Trace directory:** `states/traces/title_wrong_sprites_and_missing_score_semantic_trace_20260702_115645/`
**Scope:** No source/spec/tool/Makefile/ROM/build changes. No rebuild. No implementation. No sprite suppression. No D00298, PC080SN, Window, or black-cover fix.

## Phase 0

**Relevant priors:** KF-032/KF-038 context for PC080SN/PC090OJ routed output, OPEN-001, OPEN-024, OPEN-015 context only; prior Build 0126 reports `Cody_title_screen_arcade_vs_genesis_sprite_delta_baseline.md`, `Cody_title_topscore_pc090oj_producer_to_mirror_trace.md`, `Cody_genesis_sat_link_chain_termination_audit.md`, `Cody_temp_sprite_sat_suppression_black_cover_test.md`, `Cody_pc090oj_blank_bitset_unmapped_guard_implementation.md`, `Cody_pc090oj_object_ram_phase1_implementation.md`, and `Andy_pc090oj_object_ram_to_genesis_sat_architecture.md`.

**High-rediscovery hazards:** arcade title top-score strip is PC090OJ sprite output; RASTAN logo/sword and CREDIT are not PC090OJ sprite output in the audited title frame; Build 0126 SAT link-chain termination is valid and not the current title sprite cause; legacy PC090OJ helpers remain helper-owned/partial, not object-RAM faithful.

**Task classification:** EXTENDING, evidence only.

**Contradiction detected:** None. This pass corrects wording from "no sprites" to "a few wrong SAT-reachable sprite objects; the expected 27 arcade title-score sprites are missing."

**Open/Closed pre-check:** OPEN-001 and OPEN-024 touched. OPEN-015 context only. No closed issues touched. No issue opened or closed.

**Address mapping discipline:** `build/rastan-direct/address_map.json` was loaded and used for every arcade-to-Genesis code correlation in this report. Arithmetic offset was not used as proof.

## Exodus Visual Facts

User-provided full-resolution Exodus title screenshots show:

- The Sprite layer viewer shows about three visible sprite graphics at high magnification.
- The sprites are small/dark/purple-ish artifacts.
- They are not the arcade title top-score strip and are not positioned like `1UP / HIGH SCORE / 2UP`.
- The final VDP Image composite does not meaningfully show those sprites.
- Plane A and Plane B title content is present and coherent.
- Sprite outline boxes and Window-boundary boxes are Exodus UI overlays, not game pixels.

Terminology used here:

- **SAT-reachable:** present in a valid Genesis SAT link chain.
- **on-screen SAT bounding box:** SAT x/y puts the object within the nominal visible screen bounds.
- **nontransparent sprite pixels:** source/conversion cell has nonzero pen pixels.
- **visible in Sprite layer viewer:** observed in the Exodus Sprite layer viewer.
- **visible in final composite:** observed in the final VDP Image output. This is **not** proven for the wrong small artifacts.

## Wrong Genesis Sprite Decode

Authoritative post-commit native debugger evidence from `states/traces/genesis_sat_link_chain_termination_audit_20260702_111140/` shows Build 0126 title handoff 60 has a structurally valid chain `0 -> 1 -> 2 -> 3 -> 0`. Reduced decode: `states/traces/title_wrong_sprites_and_missing_score_semantic_trace_20260702_115645/decoded_sat/wrong_genesis_title_sprite_decode.csv` and `states/traces/title_wrong_sprites_and_missing_score_semantic_trace_20260702_115645/decoded_sat/wrong_genesis_title_sprite_decode.json`.

| slot | SAT raw | screen bbox | attr | tile base | pal | link | descriptor raw | mirror entry | mirror words | PC090OJ code | expected score code? |
|---:|---|---|---|---|---:|---:|---|---:|---|---|---|
| 0 | `0080 0501 E400 0080` | `(0, 0, 15, 15)` | `0xE400` | `0x0400` | 3 | 1 | `0001 0000 0000 0000 0001 0004` | 4 | `0000 0000 0001 0000` | `0x0001` | no |
| 1 | `0080 0502 E404 00AA` | `(42, 0, 57, 15)` | `0xE404` | `0x0404` | 3 | 2 | `0001 0000 002A 0000 0110 000E` | 14 | `0000 0000 0110 002A` | `0x0110` | no |
| 2 | `0100 0503 E408 0080` | `(0, 128, 15, 143)` | `0xE408` | `0x0408` | 3 | 3 | `0001 0080 0000 0000 0080 0010` | 16 | `0000 0080 0080 0000` | `0x0080` | no |
| 3 | `0100 0500 E40C 0081` | `(1, 128, 16, 143)` | `0xE40C` | `0x040C` | 3 | 0 | `0001 0080 0001 0000 0080 0011` | 17 | `0000 0080 0080 0001` | `0x0080` | no |

**Why Exodus shows about three objects:** slots 2 and 3 use the same PC090OJ code `0x0080` and nearly overlap at screen x `0` and `1`, so four SAT-reachable entries can visually collapse into about three visible Sprite-layer artifacts. This is an interpretation from the SAT geometry plus user-provided Exodus observation.

**Final composite visibility:** not proven for these artifacts. Tighe observed that the VDP Image Window does not meaningfully show them.

## Tile / Pixel / Palette Identity

Tile renders copied into `states/traces/title_wrong_sprites_and_missing_score_semantic_trace_20260702_115645/tiles/` from prior PC090OJ conversion evidence:

- `arcade_pc090oj_code_0001.png`, `genesis_converted_pc090oj_code_0001.png`
- `arcade_pc090oj_code_0080.png`, `genesis_converted_pc090oj_code_0080.png`
- `arcade_pc090oj_code_0110.png`, `genesis_converted_pc090oj_code_0110.png`
- `title_relevant_pc090oj_cells_contact.png`

Prior transparency analysis on the same generated PC090OJ assets reports:

| slot | source entry | code | index-0 pixels | nonzero pixels | near-black nonzero | source == converted |
|---:|---:|---|---:|---:|---:|---|
| 0 | 4 | `0x0001` | 210 | 46 | 0 | True |
| 1 | 14 | `0x0110` | 171 | 85 | 24 | True |
| 2 | 16 | `0x0080` | 202 | 54 | 12 | True |
| 3 | 17 | `0x0080` | 202 | 54 | 12 | True |

These are real converted PC090OJ cells with nonzero pixels, but they are not score glyph cells and do not match the expected arcade title-score codes or positions. They are visually capable of producing small/dark/purple Sprite-layer artifacts. They do not by themselves prove final-composite visibility.

## Missing 27 Arcade Title Sprites

Original arcade title baseline has 27 visible PC090OJ sprites, all in the top-score strip. Expected code set:

`0x002A, 0x002B, 0x002C, 0x002D, 0x0031, 0x0039, 0x003A, 0x003B, 0x003C, 0x003D, 0x003E, 0x0046, 0x0047, 0x0048, 0x0049`.

Build 0126 wrong slots use `0x0001`, `0x0110`, and `0x0080`; none are in the expected score-code set.

Reduced target comparison: `states/traces/title_wrong_sprites_and_missing_score_semantic_trace_20260702_115645/mirror/title_score_target_entry_comparison.csv`.

Summary:

- Required title-score codes present in wrong reachable SAT entries: **no**.
- Correct title-score positions present in wrong reachable SAT entries: **no**.
- Exact arcade target-entry matches in Genesis mirror at frame 60: **0 / 27**.
- Genesis final SAT nonzero target slots for the 27 title-score entries: **0 / 27** in the prior title top-score comparison.
- Lost stage: the 27 arcade title-score entries are already absent/mismatched in the Build 0126 `pc090oj_object_ram` mirror; they are not a later descriptor/SAT link-chain loss.

## 0x3B930 / 0x3B802 Helper Semantics

Exact address-map correlations are in `states/traces/title_wrong_sprites_and_missing_score_semantic_trace_20260702_115645/helper_semantics/address_map_exact_correlations.json` and `states/traces/title_wrong_sprites_and_missing_score_semantic_trace_20260702_115645/helper_semantics/reduced_sprite_semantic_data.md`.

| arcade_pc | runtime_genesis_pc | genesis_rom_offset | kind |
|---|---|---|---|
| `0x03B8B0` | `0x03BAB0` | `0x03BAB0` | `arcade_copy` |
| `0x03B8BC` | `0x03BABC` | `0x03BABC` | `arcade_copy` |
| `0x03B930` | `0x03BB30` | `0x03BB30` | `patched_site` |
| `0x03B936` | `0x03BB36` | `0x03BB36` | `patched_site` |
| `0x03B93C` | `0x03BB3C` | `0x03BB3C` | `patched_site` |
| `0x03B942` | `0x03BB42` | `0x03BB42` | `patched_site` |
| `0x03B94C` | `0x03BB4C` | `0x03BB4C` | `patched_site` |
| `0x03B802` | `0x03BA02` | `0x03BA02` | `patched_site` |

**Arcade semantics:** the `0x03B930` table-copy routine is caller-owned: caller supplies `A0` source, `A1` PC090OJ object-RAM destination, and `D1` count. The title setup at copied `runtime_genesis_pc 0x03BAB0` reaches the patched `0x03BB30` wrapper from an arcade setup that used `A1=HW_ADDRESS 0x00D00020` and `D1=24` in the earlier provenance pass.

**Genesis Build 0126 helper semantics:** `genesistan_pc090oj_hook_target_3b930` at `runtime_genesis_pc 0x071A12`:

- does **not** use caller `A1` as the PC090OJ destination;
- starts from helper-owned slot `14`;
- copies `D1` into `D6` but clamps the count to at most `4`;
- emits via `.Lpc090oj_emit_slot`, which bridges to `pc090oj_object_ram` only at slot-indexed mirror locations;
- therefore cannot populate the arcade title's 24-entry `A1=0x00D00020` destination span.

**Score digit helper:** `genesistan_pc090oj_hook_score_digit_3b802` maps destination progression to helper-owned slots `22..29`, only a partial slot mapping, not a general object-RAM-faithful preservation of arcade destination semantics.

Classification: **not equivalent / helper-owned slot emission / partial preservation**, not object-RAM faithful.

## Fresh Genesis Runtime Proof Attempt

Method attempted: MAME Genesis driver with Qt debugger forced offscreen, debug script breakpoints at `runtime_genesis_pc 0x03BB30`, `0x071A12`, and `0x071A2A`.

Artifacts:

- `states/traces/title_wrong_sprites_and_missing_score_semantic_trace_20260702_115645/runtime_trace/mame_debug_title_sprite_semantics.cmd`
- `states/traces/title_wrong_sprites_and_missing_score_semantic_trace_20260702_115645/runtime_trace/mame_debug_stdout.log`
- `states/traces/title_wrong_sprites_and_missing_score_semantic_trace_20260702_115645/runtime_trace/mame_debug_stderr.log`

Result: MAME ran for 7 seconds, but emitted no breakpoint printf events. This pass therefore did **not** add fresh runtime hit proof. Static/source/disassembly and prior runtime dump conclusions remain separate from this failed/limited runtime attempt.

## Failure Classification

**Title score failure:** producer path is mapped to a patched helper whose semantics ignore caller `A1` and clamp caller `D1`; the missing title score set is already absent/mismatched in `pc090oj_object_ram`, so the loss is at producer-to-mirror/helper semantics, not descriptor rejection, SAT link-chain termination, or final SAT traversal.

**Wrong small sprite classification:** helper-owned slot artifacts / unrelated converted PC090OJ cells. They are SAT-reachable and have on-screen bounding boxes/nontransparent pixels, but they do not match arcade title-score codes or positions, and final-composite visibility is not proven.

**Confidence:** STRONG for the semantic mismatch and missing-score lost stage; MODERATE for attributing the exact Exodus three visible artifacts to the four SAT entries because that part uses screenshot observation plus SAT geometry rather than direct Exodus-exported SAT capture.

## Relation To Story-Page Black Cover

- The helper-owned slot model explains the missing title score sprites.
- It plausibly fits the broader class of wrong sprite products, but this report does **not** directly prove the story-page black-cover mechanism.
- The Build 0125 temporary suppression result remains consistent with sprites/SAT being able to affect the composite, but it is not a fix and not title-score proof.
- Story-page black-cover attribution still requires canonical Build 0126 story-page SAT-producing-chain evidence tied to the exact story frame/layer symptom.

## Terminology Correction

Avoid the old ambiguous phrase **visible sprite** unless final composite visibility is proven.

Use these terms instead:

- SAT-reachable
- on-screen SAT bounding box
- nontransparent sprite pixels
- visible in Sprite layer viewer
- visible in final composite

## Classification

Final classification: **producer executes through patched PC090OJ helper semantics that are not object-RAM faithful; title score sprites are lost at the producer-to-mirror/helper stage, while wrong helper-owned slots remain SAT-reachable.**

What this proves:

- Build 0126 has a valid short SAT chain for the title sample.
- The reachable Genesis title sprites are the wrong cells/positions and not the arcade title top-score set.
- The 27 arcade title top-score entries are absent/mismatched before SAT generation.
- The current `0x03B930` and `0x03B802` replacements are helper-owned/partial rather than object-RAM faithful.

What remains unresolved:

- Fresh runtime breakpoint proof at `0x03BB30/0x071A12` remains uncaptured by this MAME debugger attempt.
- Exact final-composite visibility of the tiny Exodus Sprite-layer artifacts is not proven.
- Story-page black-cover mechanism remains separate.

Next recommended target: a bounded design/evidence pass for an object-RAM-faithful replacement of `0x03B930` / score-digit destination semantics, before implementation. Do not implement from this report alone without the state-causality/fix directive.

## Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-024.
- Closed issues touched: none.
- New issues opened: none.
- Issues closed: none.
- Deferred: story-page black-cover proof, D00298, PC080SN/Window, OPEN-015.

## STOP

STOP triggered: NO. Runtime breakpoint proof attempt was limited, but the evidence-only task completed with source/static/prior-runtime artifacts and explicit limitation.
