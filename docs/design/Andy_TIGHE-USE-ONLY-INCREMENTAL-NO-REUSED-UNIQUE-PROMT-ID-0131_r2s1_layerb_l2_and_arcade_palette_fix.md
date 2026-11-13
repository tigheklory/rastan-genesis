# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0131 — R2-S1 Layer-B L2 tile fix + arcade palette re-derivation

> **CORRECTION (PROMT-ID-0132, 2026-11-12, after Tighe tested Build 0566 in natural gameplay):**
> **Part 1 (offline Plane-B tile → L2) is ACCEPTED by Tighe and preserved.** **Part 2's conclusion is
> DISPROVEN:** the "direct-start harness artifact" hypothesis was wrong — natural R1→R2-S1 also shows wrong L2
> colours, so there IS a production defect. The specific error was a false premise in §6–§8 below: the claim
> that the per-stage loader "writes arcade bank 2 for every round." It does not — the destination bank is
> round-dependent (`0x59E8C`: R1=2, **R2=3**, R3=9, R4=8, R5=1, R6=4), matching each round's Plane-B tile
> `attr&3`. The Genesis hook only routed bank 2 → L2, so R2's bank-3 Layer-B write was misrouted to Line 1 and
> gameplay-gate rejected, leaving L2 stale. Root cause and fix: see
> `Andy_...PROMT-ID-0132_r2s1_l2_palette_content_root_cause_and_fix.md`. Treat §6–§11 below as superseded.

**Author:** Andy · **Date:** 2026-11-12 · **Baseline:** HEAD `f8b07a84` (branch `rastan-direct-proposal`),
uncommitted 0113–0126 work preserved. Build 0564 (throne baseline) and Build 0565 (diagnostic) untouched.
MAME is environment-blocked in this sandbox (wedges at init); automated static gates are supporting evidence,
Tighe's BlastEm test is authoritative.

## 1. Starting state
- HEAD `f8b07a84`, branch `rastan-direct-proposal`.
- Build counter 565 before this task; next numbered = **0566**.
- Working tree: 34 modified, 12 untracked (preserved 0113–0126 work); not reset/cleaned.

## 2. Two separate systems, as the prompt frames them

- **(A) Which palette line a Plane-B tile selects** — static tile-attribute metadata. This is the L2/L3
  split Tighe sees in the Exodus Plane Viewer. **Fixed offline (Part 1).**
- **(B) What colors are stored in L2** — the retained arcade palette logic. **Re-derived (Part 2); no
  production divergence proven — see §6.**

## Part 1 — all R2-S1 Plane-B tiles select L2 (implemented, offline)

### 2a. Exact cause of the initial-vs-scroll L2/L3 split
Four runtime producers write gameplay Plane B. Three already forced Genesis Line 2:
- scene-entry fill `genesistan_plane_b_scene_fill_maps` (baked L2 by `compile_pc080sn_genesis.py`);
- the cell/entering-column producer `.Lplane_b_stage_gameplay_producer_cell_native` → `.Lplane_b_native_attr_from_word` (`moveq #2`);
- the three shared BG producers, 0124-gated on `scene_id==1` → `moveq #2`.

The fourth — the **row / vertical-pan producer** `.Lplane_b_publish_logical_row_native`
([tilemap_hooks.s:1965](../../apps/rastan-direct/src/tilemap_hooks.s#L1965)) — reads its attribute straight
from the offline artifact `pc080sn_plane_b_visual_records.bin`
([:2035](../../apps/rastan-direct/src/tilemap_hooks.s#L2035)/[:2059](../../apps/rastan-direct/src/tilemap_hooks.s#L2059))
and never normalizes. That artifact's generator, `gen_pc080sn_plane_b_visual_records.py`, looked the native
attribute up in the shared identity LUT keyed by the arcade bank (`attr&3`), so R2 Plane-B descriptors
(`attr&3==3`) baked **Line 3** while R1 (`attr&3==2`) baked Line 2. Initially-filled rows were L2; rows
refreshed by vertical scrolling pulled the baked R2 Line 3. That is the exact split.

### 3. Exact offline tile-attribute fix
`tools/translation/gen_pc080sn_plane_b_visual_records.py`, in `accepted_0422_record`, after the proven LUT
lookup (which still supplies priority/H/V-flip):

```python
native_attr = (native_attr & 0x9FFF) | (0x2 << 13)   # force palette-line field (bits 14:13) to Line 2
```

- Preserves: tile identity (separate tile-block pointer), priority (bit 15), V flip (bit 12), H flip (bit 11),
  source/pointer semantics.
- Does NOT modify the shared `precompute_pc080sn_attr_lut.py` LUT (other owners), Plane A, or frontend
  palette selection.
- Semantic-ownership rule (every real gameplay Plane-B tile → L2, every round), not an `if round==2`.

`tools/translation/verify_pc080sn_plane_b_visual_records.py` now asserts `((native_attr>>13)&3)==2` for every
valid record — standalone proof of the rule.

### 4. Proof every R2-S1 gameplay Plane-B path selects L2
- Regenerated artifact, verifier **PASS** (392 descriptors; all 16 subcolumns / 64 ring placements / dynamic
  contexts / boundaries exact; new L2 assertion holds).
- Valid-record palette-line histogram: **NEW {2: 392}** (OLD {0:63, 1:107, 2:93, 3:129}).
- **299 records changed** (arcade banks 0/1/3 → L2); **0 bank-2 records changed.**
- Bank-2 = R1 Plane-B → **R1 Plane-B byte-identical** (proven: 0 changed bank-2 records).
- Row/vertical-pan path now baked L2; scene-fill, cell/column, and shared producers already L2 ⇒ all four
  gameplay Plane-B paths select L2 in R2 (and all rounds).

### 5. Runtime conversion removed: NONE (deliberate)
The three live-fed producers (cell/column at [tilemap_hooks.s:5369](../../apps/rastan-direct/src/tilemap_hooks.s#L5369)→2116;
the three 0124-gated shared BG producers) consume **live arcade attribute words** and cannot be precomputed;
their runtime L2 force is correctly retained. The row producer had no runtime conversion to remove. So **zero**
runtime palette-line conversion was removed, the 0124 throne gating is intact, and no broader runtime cleanup
was attempted (explicitly out of scope).

## Part 2 — re-derived original-arcade Layer-B palette chain (no previous doc trusted as authority)

### 6. R1-S1 and R2-S1 Layer-B palette chains (from arcade disassembly / Ghidra)
The retained arcade per-stage Layer-B palette loader is `FUN_00059de8`:

```c
FUN_00059de8:  if (a5@0x13b0 == 1) {                 // scene-reload-pending GATE (set by FUN_00055c22)
                 FUN_00059e1e(); FUN_00059e36();      // per-stage setup, indexed by a5@0x118 (1-based stage)
                 do { FUN_00059e6c(); FUN_00059e50();  // palette source = PTR_DAT_00059e8c[D5*2 + (a5@0x118-1)*8]
                      FUN_00059ad4(); } while(++i != a5@0x13d6);   // FUN_00059ad4 == genesistan_palette_hook_59ad4
               }  a5@0x13b0 = 0xff;
```

- Chain: arcade stage/round state → per-stage palette-source table indexed by `a5@0x118` → `FUN_00059ad4`
  (the Genesis hook) → staged into `staged_palette_words` **Line 2** → VBlank CRAM publication at `0x200000`.
- Genesis destination of a Layer-B (bank 2) write = **Line 2**, proven at
  [palette_hooks.s:159-230](../../apps/rastan-direct/src/palette_hooks.s#L159): bank 2 matches none of the
  frontend/sprite branches, is `< 4`, falls to `.L59_dest_ready` with d0=2, and (gameplay `scene_id==1`) only
  destination line 2 is staged — so bank 2 → L2.
- R1-S1 live Layer-B behavior (sky progression, water) flows through the same hook (e.g. the type-9 water
  route, arcade banks 0x1A–0x1D). Preserved — no change to `palette_hooks.s`.

### 7/8. Physical palette destinations
- The per-stage outdoor palette is loaded via arcade **bank 2** for *every* stage (the loader passes a
  constant bank into `FUN_00059ad4`), indexed by stage `a5@0x118`. R1 uses entry[stage1], R2 uses entry[stage2].
- Plane-B **tile attribute** banks differ by round (R1 `attr&3==2`, R2 `attr&3==3`) — that is the tile
  palette-select field (Part 1), a different system from the palette-load bank. The palette *load* for both
  rounds is bank 2 → Genesis L2.

### 9. Was the previous `$59EC8`/`$5DC4E`/bank-48 documentation correct?
- **Correct:** `0x59EC8` is the per-stage outdoor palette pointer table feeding the hook with bank 2 → L2;
  `0x5DC4E` = its stage-2 entry (R2); arcade BG/Layer-B bank 48 → Genesis Line 2 (route table,
  [palette_hooks.s:59](../../apps/rastan-direct/src/palette_hooks.s#L59)). These reproduce from
  `rastan_direct_remap.json` and the Ghidra decompiler and are **re-confirmed**, not merely trusted.
- **Clarified:** `0x5DC4E` is an *oracle* (what the arcade program should select), never a value to hardcode.

### 10. Exact Genesis palette-routing defect found
**None in the production path.** Every link from arcade stage state to Genesis L2 is retained arcade code
except `genesistan_palette_hook_59ad4`, which correctly routes bank 2 → L2. There is no R2-specific rejection,
no R1-only bank assumption that drops R2, and no scene-1 gate that blocks the Layer-B (line-2) write.

### 11. Exact production fix
**No production palette change was made.** The wrong R2-S1 L2 colors are seen only in the **direct-start**
R2-S1 ROM, which patches only the stage-decode selector byte (`build_subround_variant.py`) and does not
reproduce the natural `a5@0x118=2` + `a5@0x13b0=1` reload sequence that drives `FUN_00059de8` to load the
stage-2 palette. Per the prompt ("natural progression is authority; if direct-start state differs, correct
the harness separately; do not fix production for a direct-start artifact"), the correct next step is to
confirm the symptom in **natural R1→R2** before any production change. Two branches:
  - **If natural R2-S1 colors are correct** (expected, since the whole chain is retained arcade + one proven
    hook): the defect is the direct-start harness — correct `build_subround_variant.py` to also set the stage
    index and re-trigger the per-stage palette reload, as a *test-harness* change, not production.
  - **If natural R2-S1 colors are also wrong:** capture `a5@0x118`, `a5@0x13b0`, and L2 CRAM at R2-S1 via the
    documented bookmark cycle (Insert → Tighe observation → Revert) to locate the real divergence, then fix it.

This is deliberately **not** guessed: changing the retained palette logic to "fix" a non-bug would risk
breaking natural progression and R1's live Layer-B behavior.

### 12. No hardcoded R2 palette
No `$5DC4E` copy, no static R2 CRAM, no `if round==2`, no Palette Composer asset, no frozen L2. **This task
edited only two files** — `tools/translation/gen_pc080sn_plane_b_visual_records.py` (+12) and
`tools/translation/verify_pc080sn_plane_b_visual_records.py` (+9). `palette_hooks.s` and the arcade palette
logic were **not touched by PROMT-ID-0131**; `palette_hooks.s`'s diff vs HEAD is entirely the pre-existing
0119/0124 work carried in the preserved working tree (part of the accepted 0564 lineage), not this task.

### 13. Runtime color conversion NOT redesigned
`genesistan_palette_hook_59ad4` and `.Lxbgr555_to_cram` are unchanged; the live arcade→CRAM conversion
remains. The only preprocessing change is the Plane-B **tile-attribute** artifact (Part 1). Offline
color pre-conversion is documented as future work only
(`Andy_layerb_palette_offline_color_preconversion_long_term_goal.md`).

### 14. R1 dynamic Layer-B behavior preserved
`palette_hooks.s` unchanged; the R1 progression/water palette path (hook_59ad4, type-9 water route) is intact.
R1 Plane-B tiles byte-identical (§4). No regression to the R1 live Layer-B path.

### 15/16. Lines 0/1/3 and throne/frontend preserved
This task made no edit to `palette_hooks.s` or `tilemap_hooks.s`, so the 0119 L0/L1/L3 protection and the three
0124-gated BG producers (the throne/frontend fix) are carried through byte-for-byte from the preserved tree.
Lines 0/1/3 remain Test-2.0-owned; throne/frontend remains 0564-equivalent in behavior. R1 Plane-B is
byte-identical (§4), so R1 rendering is unchanged.

## 17–19. Build artifacts
Build **0566**, GATE_PASS, canonical state. (MAME entry/epoch gates environment-blocked as before — static
canonical/boot-guard/Plane-B/scene-fill gates PASS.)

- Normal candidate: `dist/rastan-direct/rastan_direct_video_test_build_0566.bin`
  SHA-256 `54eb2558bf1030cc64469c6b066ffc23c6c250c7fb4064c039568b5a5a376806`
- R2-S1 direct-start: `dist/rastan-direct/rastan_direct_video_test_build_0566_R2-S1.bin`
  SHA-256 `ffa157efe800bf4c8b10d5597d1828eee515cd7567cdd34dc911a45396ce2680`
- R1-S1 direct-start: `dist/rastan-direct/rastan_direct_video_test_build_0566_R1-S1.bin`
  SHA-256 `54eb2558bf1030cc64469c6b066ffc23c6c250c7fb4064c039568b5a5a376806`
  (selector 0xFF = the default R1-S1 start, so this ROM is byte-identical to the normal candidate — R1-S1 is the normal boot.)
- Build 0564 (`869054a3…`) and Build 0565 diagnostics: untouched on disk.

## 20/21. Test order and docs
- **Test first:** `rastan_direct_video_test_build_0566.bin` (natural progression) — this is the semantic
  authority for the L2 color question.
- Report: this file. Forensics updated with a resolution section. Future-work doc:
  `docs/design/Andy_layerb_palette_offline_color_preconversion_long_term_goal.md`.

## What Tighe should verify
- R2-S1: all Plane-B tiles on L2, before and after vertical/horizontal scroll (the split should be gone).
- **R2-S1 L2 colors in NATURAL R1→R2 progression** (not the direct-start ROM) — this decides whether a
  production palette change is even warranted.
- R1-S1 unchanged incl. live Layer-B color changes / water animation; Lines 0/1/3; throne/frontend; R2 Plane A.

Not claimed visually accepted until Tighe tests it.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0131`
