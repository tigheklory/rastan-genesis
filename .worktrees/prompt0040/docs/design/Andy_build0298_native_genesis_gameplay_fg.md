# Andy — Build 0298 Native Genesis Gameplay FG: Pre-Implementation Audit → STOP (No ROM)

**Type:** Implementation attempt → **STOP after mandatory pre-implementation audit.** **No ROM produced;
Build 0298 number NOT consumed (counter stays 297).** Baseline: Build 0297.

## 1. Phase-0 baseline
- **Relevant priors:** KF-010 (FG→Plane A base 0xE000) STRONG, KF-014 (tile LUT) STRONG, KF-015 (full-plane
  scroll +8) STRONG, KF-011 (arcade VBlank owns progression) STRONG/HIGH — all apply.
- **Rediscovery-Hazard HIGH:** KF-011 (respected).
- **Deferred appendix:** none relevant.
- **Task classification:** EXTENDING (the native FG producer already exists; this task would extend/replace
  it).
- **Open/Closed issues touched:** OPEN-001/018 (native FG/map incomplete), OPEN-017 (FG/collision, rope
  collision).
- **Contradiction of CONFIRMED/STRONG finding:** NONE. (But the **task premise** — "the native producer does
  not yet exist and must be implemented" — is contradicted by the current tree; see §2. This is a premise
  correction, not a KF contradiction.)

## 2. The STOP finding: the producer this task specifies is ALREADY IMPLEMENTED and ACTIVE in Build 0297
The mandatory Phase-2/3/5 audits show the exact native gameplay-FG Plane-A producer, at the exact semantic
cut this prompt specifies, **already exists and is the active gameplay path** in the accepted Build 0297:

| This prompt's requirement | Current Build-0297 reality | Evidence |
|---|---|---|
| Replace `FUN_00055968` (selector-0 chip writer) with a native producer | **Done** — arcade_pc 0x055968 → `genesistan_hook_tilemap_plane_a_selector0_native` (Build 0242) | remap 0x055968 `4ef9{…selector0_native}` |
| Replace `FUN_00055990` (selector-1/2/4/5/6 chip writer) with a native producer | **Done** — arcade_pc 0x055990 → `genesistan_hook_tilemap_plane_a_selector12_native` (Build 0245) | remap 0x055990 note: "retains a5@0x10A8/0x10CA/0x10CC, descriptor rebuild tables, scroll-derived resident window; replaces the complete PC080SN C-window/collision tail with direct Genesis Plane-A staging + collision side-channel" |
| Replace pan-up/down chip realization | **Done** — 0x055704/0x055790 → `genesistan_plane_a_pan_publish_entering_rows_down/up` (Build 0247) | remap 0x055704/0x055790 |
| Write final `staged_fg_buffer` (64×32) not a C-window | **Done** — staged_fg_buffer = 2048 words = 64×32; hooks write it directly | vdp_comm.s:552; tilemap_hooks selector0/12 |
| Write the terrain collision ring | **Done** — hooks write `ARCADE_COLLISION_MAP_BASE = 0x00FF1E00` (= arcade 0x10DE00, the Part-2-proven base) | tilemap_hooks.s:93 + selector0/12 collision writes |
| Arcade retains state machine (FUN_00055650/directional/dispatch/cursor/selector/scroll) | **Done** — only the strip-tail bodies are replaced; the BSR/dispatch/cursor stay arcade | remap notes "preserve the original BSR at 0x055950/0x05595A" |
| Remove the tall-FG / projection compatibility path | **Done** — removed in **Build 0257** ("dead FG_SRC tall staging … removed; its consumer projector is gone") | tilemap_hooks.s:865/1139/3179 |
| One runtime gameplay FG renderer, no stage-specific hybrid | **Done** — selector 0 → selector0_native; 1/2/4/5/6 → selector12_native; single path | remap + FUN_00055948 dispatch |
| Selector 4/5/6 handled by the same (row) producer | **Done** — selector12_native handles all selector≠0 with parity `~idx&3` unless ==2 | tilemap_hooks.s selector12 body |

Therefore **every Build-0298 "success" criterion in Phase 17 is already satisfied by Build 0297.** The
producer exists, is active, writes final Plane-A + collision at the proven base, the tall/projection is gone,
and the chip writers `FUN_00055968/55990/559b2/55a14` are already off the gameplay path.

## 3. Why I am NOT producing a Build 0298
Producing a ROM now would be one of two prohibited things:
1. **Redundant reimplementation** of an existing, active producer — no delta; the numbered build would be a
   pointless number consumption representing no real change (violates the sequential-numbering intent that
   each numbered build is a distinct change).
2. **A defect fix without a proven boundary.** The only genuine remaining FG work is *defect resolution*, not
   *producer implementation* — and the principal known FG defect has an explicit prior STOP:
   - **Rope/terrain collision source-block divergence (OPEN-017):** Build 0228 proved the Genesis FG producer
     selects source block `0x3888` where original arcade selects `0x2648`/`0x1C14`; the writer/control path
     that makes the Genesis slot select `0x3888` is **not proven**, and prior work concluded **"no
     patch-safe correction boundary exists"** and did NOT build. Attempting a fix now would require guessing
     the source-block selection — a **STOP condition** (global rule 1: NO GUESSING; and the prompt's own STOP
     "exact source ordering would have to be guessed").
   - **Remaining "gray/wrong lower-block terrain"** (Build 0215 note, OPEN-001) — a visual/source defect, also
     not a producer-implementation task.
These are distinct from "implement the native producer," which is done. This task's scope does not authorize a
guessed defect fix, and none of the FG defects has a proven, patch-safe correction boundary yet.

## 4. Mandatory audit results (for the record)
- **Phase 2 geometry:** Genesis Plane A = **64×32** (planesize reg 16; base VRAM 0xE000); `staged_fg_buffer`
  = 2048 words (one word/cell). The arcade 64-row FG column maps into the 64×32 Genesis plane; the existing
  producers already resolve this (rows masked into the 32-row plane; the tall/projection intermediary was
  removed in Build 0257). No ambiguity remains that a *new* implementation would resolve.
- **Phase 3 commit path:** `staged_fg_buffer` + `staged_scroll_fg` + `vdp_commit_scroll` +
  `vdp_commit_fg_strips_if_dirty`/`_narrow_strips` already commit final Plane-A geometry via the arcade-owned
  VBlank — FINAL NATIVE.
- **Phase 4 descriptor-rebuild sharing:** `genesistan_hook_pc080sn_descriptor_rebuild` is the arcade-owned
  source-table rebuild (arcade 0x055904) shared by the FG producers; retained (not a Build-0298 target).
- **Phase 5 cut:** already exactly as specified (retain FUN_00055650/directional/FUN_00055948/558a2/558c6/
  55904/558e0; replace FUN_00055968/55990/559b2/55a14 + C-window dest). Confirmed already in place.
- **Standing-rule note:** the existing FG-native routes (Builds 0242/0245/0247) are byte-neutral
  `4ef9{sym}4e71…` (JMP + NOP padding). Those NOPs are **pre-existing accepted history**, not introduced here.
  This task adds none.

## 5. Semantic cut / PC080SN policy (§9 checklist)
- **Semantic cut (already implemented):** retain the arcade FG state machine (map/source/cursor/selector/
  scroll); replace only the PC080SN chip realization at 0x055968/0x055990/pan.
- **Chip tail removed (already):** `FUN_00055968/55990` selector writers, `FUN_000559b2/55a14` terminal
  C-window writers, the `a5@0x10A0/0x10A4 = 0xC08000+geometry` dest, and (Build 0257) the tall/projection.
- **Transitional compatibility retained:** none for gameplay-FG production; the physical arcade chip-writer
  bytes remain unreached (behind the native JMP), for later zero-debt retirement. Removal boundary = the
  planned final FG zero-debt task (after the FG *defects* are resolved).

## 6. Recommendation (evidence-backed)
The FG analysis chain (Parts 1/2/2B/design/addendum) is valuable and correct, but it characterized a producer
that **already exists**. The next real work is **not** a producer reimplementation; it is a **targeted,
proof-driven defect investigation** of the two concrete, currently-unresolved FG defects:
1. the **collision/FG source-block selection divergence** (Genesis 0x3888 vs arcade 0x2648/0x1C14) — resolve
   the source-table/descriptor writer that selects the wrong block (the prior Build-0228 STOP boundary), and
2. the remaining **lower-block terrain** correctness.
Only once a *proven, patch-safe* correction boundary exists for a specific defect should a numbered build
(Build 0298) be produced to fix exactly that. I recommend re-scoping the next task to that defect
investigation rather than a redundant producer implementation.

## 7. Final statements
- Native gameplay FG producer implemented: **YES — already, in Build 0297** (Builds 0242/0245/0247).
- Arcade FG progression still owns state/cursor: **YES.**
- Rastan publication unit preserved at 64 cells: **YES** (selector0/12 producers loop the 16×4 = 64-cell
  entering edge).
- Native Plane-A geometry proven: **YES** (64×32).
- No C-window destination required by native producer: **YES** (already direct Plane-A).
- Native collision ring synchronized with visual publication: **YES** (base 0x00FF1E00 = arcade 0x10DE00).
- Initial resident FG population native: **YES** (existing native staging; tall/projection removed 0257).
- Runtime gameplay FG renderer count: **1.**
- Stage-specific hybrid renderer present: **NO.**
- Frontend/text Plane-A preserved: **YES** (untouched by this task).
- PC080SN gameplay-FG zero debt achieved: **NO** (physical chip-writer bytes remain unreached for later
  retirement; and FG *defects* remain).
- **Build 0298 produced: NO** (premise already satisfied; no proven, patch-safe delta to implement).
- Ready for Build 0299 validation/broadening task: **N/A** — recommend re-scoping to the FG defect
  investigation (§6) instead.

**STOP triggered: YES** — the specified implementation already exists; the only remaining FG work is defect
resolution with no proven patch-safe boundary (Build-0228 prior STOP). Asking Tighe for direction.
