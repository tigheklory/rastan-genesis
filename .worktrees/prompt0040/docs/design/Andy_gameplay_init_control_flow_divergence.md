# Andy — Gameplay-Init Control-Flow Divergence: Unrelocated Scene-Asset Pointer Table (Outcome D, no build)

**Agent:** Andy (temporary runtime-evidence role). **Type:** evidence-only analysis. **No source, no ROM, no build.**
**Baseline:** `rastan-direct-proposal` @ `804a6df` (Build 0152 accepted, `454add2`). Build 0152 ROM
`3d805331815588576a3fdeef732a7b094f3c15997b66c76830827adfc2f35214`. Working tree clean.
**Evidence dir:** `states/traces/build_0153_stage1_outside_scene_assets/`.

## Outcome
**Outcome D — pointer translation is wrong.** The gameplay scene-asset loader **does execute** during gameplay
(correcting the earlier "not executed" hypothesis), but its asset source pointers are **not relocated**: the gameplay
asset pointer table at Genesis `0x0005A0C8` (arcade `0x00059EC8`) contains absolute arcade addresses
(`0x0005DB4E`, `0x0005DC4E`, `0x0005DD4E`) that the post-patch relocation does not rewrite by `+0x200`. The palette/BG
loaders therefore read arcade-offset data (mostly zeros) instead of the copied Stage 1 outside data → blank scene.
This is the **KF-028 / OPEN-016 embedded-data-pointer relocation class**. No build was produced (see "why no build").

## Control-flow: last-matching vs first-divergent
The gameplay palette caller chain (captured in arcade MAME at `0x059AD4` during gameplay, state `2/3/0`, stack):
`0x03B07E → 0x041F0E → 0x0510A2 → 0x059E06 → 0x059AD4` (palette producer, already patched →
`genesistan_palette_hook_59ad4`, runtime `0x00059CD4`). All are `arcade_copy` (+0x200) except the patched palette hook.

Genesis Build 0152 execution counts over a 150-frame gameplay window (state `2/3/0`):
| routine (Genesis PC) | arcade PC | hits/150 frames |
|---|---|---|
| `0x004210E` (calls next) | `0x041F0E` | **140** |
| `0x00512A2` (calls R_c) | `0x0510A2` | **140** |
| `0x0059FE8` = **R_c** (scene-asset loader) | `0x00059DE8` | runs (flag-gated) |
| `0x005A006` (palette call inside R_c) | `0x00059E06` | **1** (per-scene) |
| `0x0059CD4` (palette hook) | `0x00059AD4` | **≈1–3** (per-scene) |

**Last matching:** the dispatch chain runs identically down to and including **R_c** (`0x0059FE8`) — it is entered and,
with its gate flag `a5@(0x13B0) = 0`, executes the asset-load loop (it is **not** skipped).
**First divergence is not a skipped branch** — it is the *data* R_c's loaders read.

## R_c (Genesis `0x0059FE8`, arcade `0x00059DE8`) — the gameplay scene-asset loader
```
59fe8: (gate) tst a5@(0x13B0);  bne 0x5a016   ; load once per scene, else skip
59ff0: bsr 0x5a01e ; bsr 0x5a036              ; sub-loaders (BG/tile setup)
59ffa: bsr 0x5a06c ; bsr 0x5a050              ; build asset source pointers (from tables)
5a002: move.w a5@(0x13AE),d1                  ; row/bank arg
5a006: jsr  0x59cd4                           ; -> palette hook (0x59AD4)
5a00c: addq #1,d5 ; cmp a5@(0x13D6),d5 ; bne 0x59ffa   ; loop over banks
5a016: move.w #0xFF,a5@(0x13B0) ; rts         ; mark scene loaded
```
Runtime at the gameplay load: gate `a5@(0x13B0) = 0x00` (runs), loop count `a5@(0x13D6) = 1`, and the palette hook is
called with **`D0(bank)=2`, `D1(row)=0`, `A0(source)=0x0005DB4E`, `A5=0x00FF0000`** — a valid bank (bank 2 → line 2 is
accepted by `genesistan_palette_hook_59ad4`). So the hook *would* stage line 2 — but the source is wrong.

## The unrelocated pointer (proven)
The sub-loader `0x5a06c` builds `A0` from the pointer table at immediate `#0x0005A0C8` (`movea.l #0x0005A0C8,a0;
movea.l (a0…),a0`). That table (Genesis `0x0005A0C8`) reads:
```
0x0005A0C8: 0005 DB4E  0005 DC4E  0005 DD4E …   (absolute arcade pointers, step 0x100)
```
These are **arcade** addresses. The copied data lives at **+0x200**. Reading the arcade offset vs the correct one:
```
Genesis 0x0005DB4E (what the hook reads): 0000 0000 0000 0000 0000 0000 0000 0491   (zeros)
Genesis 0x0005DD4E (= 0x5DB4E + 0x200)   : 0000 0357 0457 0547 0647 0557 0968 0977   (real Stage 1 palette)
```
So the palette hook stages from a zero window → CRAM collapses to ~1 nonzero word (the reported "nearly all black,
one pink entry"). The BG/tile sub-loaders (`0x5a050` builds from `#0x0005A08C`) are the same shape and read the same
class of unrelocated sources, so the background planes are also blank.

**Why the post-patch missed it:** `specs/rastan_direct_remap.json` `rom_absolute_call_relocation` rewrites absolute
longwords only when they are **instruction operands** of the listed opcodes (`0x207C`, `0x4EB9`, …). The gameplay
sources here are **absolute longwords embedded in a data table** at `0x5A0C8`, not instruction operands — exactly the
KF-028 / OPEN-016 "embedded absolute descriptor-pointer table not relocated" gap. Frontend palette sources are reached
through instruction-operand immediates (which *are* relocated), which is why the frontend palette works and gameplay
does not.

## Answers to the required questions
- **Last matching routine:** `0x0510A2` / R_c (`0x0059FE8`) — the dispatch and loader execute on both machines.
- **First arcade routine Genesis does not faithfully execute:** none is *skipped*; the first divergence is the **data
  R_c's asset loaders dereference** — the pointer table at `0x0005A0C8` (arcade `0x00059EC8`) holds unrelocated
  arcade pointers, so the palette/BG loaders read `+0` instead of `+0x200`.
- **Caller chain to `0x059AD4`:** `0x03B07E → 0x041F0E → 0x0510A2 → 0x059E06 → 0x059AD4`.
- **BG descriptor producer + caller chain:** R_c's `0x5a06c`/`0x5a050` (arcade `0x59E6C`/`0x59E50`), same caller chain,
  building source pointers from the `0x5A0C8`/`0x5A08C` tables.
- **Outcome:** **D** (incorrect translated pointer). Root cause: unrelocated embedded data-table asset pointers
  (KF-028/OPEN-016 class).

## Why no build this round
A one-pointer patch is unsafe here: R_c loads the Stage 1 outside **palette, BG tile patterns, and tilemap** from a
*family* of embedded pointer tables (`0x5A0C8`, `0x5A08C`, and any siblings the sub-loaders index). Relocating only
the palette table would produce a partial/known-wrong visual build, which the task forbids. The correct fix is a
bounded **relocation** design, not an independent trigger. The smallest next task is defined below.

## Smallest next architecture task (bounded)
1. Enumerate the complete set of gameplay scene-asset pointer tables that R_c and its sub-loaders index — starting at
   Genesis `0x5A0C8` (palette sources `0x5DB4E…`) and `0x5A08C`, and following `0x5a01e`/`0x5a036`/`0x5a050`/`0x5a06c`
   to every `#imm`-loaded table that yields a `0x0005xxxx`/`0x0004xxxx` ROM source; record each table's base, entry
   count, stride, and value range.
2. Relocate those embedded absolute pointers by the arcade-copy delta (`+0x200`) using the **existing OPEN-016
   embedded-pointer relocation mechanism** (extend the post-patch data-table relocation to cover these gameplay
   tables), not a new loader or a hand-edited table. Preserve instruction-operand relocation unchanged.
3. Validate that R_c then stages the Stage 1 outside palette (line 2 = the `0x5DD4E` colours) and that the BG/tile
   sources resolve to copied data; only then decide whether the resulting BG tilemap population also needs the
   existing PC080SN staging route (a separate check, since gameplay BG writes may still target the raw C-window like
   the `0xC08C62` case Build 0152 handled).

## Confirmation
No scene/palette forcing was added: `load_scene_tiles(1)` was **not** called manually, no scene ID was forced, no
palette/tiles were preloaded, no state was advanced, no source/ROM/build was produced. Stale PC090OJ sprites,
item-scroll, and `0x03D04C` were not touched.

## Open issue impact
- **OPEN-017 (ROM does not run on real hardware / gameplay):** advanced — the blank Stage 1 outside is root-caused to
  unrelocated embedded gameplay asset pointers (`0x5A0C8` table, arcade `0x59EC8`), the KF-028/OPEN-016 relocation
  class, consumed by the gameplay scene loader R_c (arcade `0x59DE8`). Bounded relocation design task defined. Not
  closed; no duplicate.
