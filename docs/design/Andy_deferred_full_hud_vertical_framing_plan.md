# Andy — Deferred Full Gameplay HUD / 240→224 Vertical Framing Preservation & Restart Plan

**Date:** 2026-10-17 · **Agent:** Andy · **Type:** READ-ONLY architecture/history/code-preservation
planning. **No** production source, Makefile, generator, verifier, spec, ROM, build-number, counter,
branch, commit, tag, MAME run, or rope benchmark was changed or produced. Phase D/E not started.

Output of this task: this document + one append-only `AGENTS_LOG.md` entry.

> **STATUS BANNER — READ FIRST.** Production source is **currently at the Build-0437 state**
> (verified in the working tree, §4). The active HUD / vertical-framing effort is being
> **intentionally postponed**, not abandoned. The intended production return baseline is **Build
> 0434**. **It is NOT yet safe to return production source to Build 0434.** A separate Cody
> code-preservation task (§17) must first create and verify a durable Git recovery point for the
> complete post-0434 work, because — see §4 — **none of builds 0427–0437 is committed anywhere**.

---

## 1. Decision and scope

The gameplay-HUD restoration and the arcade-240 → Genesis-224 vertical-framing experiments
(Builds 0435, 0436, 0437, and the post-0437 regression isolation) are **deferred**. The work is
sound and valuable; it is being parked so production can return to the last hardware-accepted
baseline while the remaining architecture and framing choices are decided deliberately later.

This document is the **authoritative record** of: why the work exists, what was learned, what each
build did, what code changed, what still needs doing, and how to restart safely. It is written so
the work can resume months later without rediscovering facts or reconstructing lost code.

What this document does **not** do: it does not modify, revert, build, benchmark, or commit
anything. It does not itself preserve the code — see the **hard gate** in §3/§17.

### Why Build 0434 is the return baseline

| Build | Canonical rope | Role |
|---|---:|---|
| 0433 | 803 fr / 13,400.588 ms | superseded by 0434 |
| **0434** | **803 fr / 13,400.588 ms** | **last Tighe-accepted (real Genesis) baseline; general vertical paired-row optimization** |
| 0435 | 803 fr / 13,400.588 ms (canonical); `_full_hud` 854 | begins upper-HUD restoration; `_full_hud` incomplete (no lower HUD) |
| 0436 | 807 fr | runtime-origin split experiment (rejected architecture) |
| 0437 | 806 fr | compile-time-origin correction (not accepted; regression reduced, not resolved) |

0434 and 0435 tie at 803 canonical frames, but **0434 is chosen** because: it contains the accepted
general vertical paired-row optimization that supersedes 0433 (per
`Cody_general_vertical_scroll_player_hud_optimization.md` — 124–128 general resolver entries removed
per paired row crossing, static equivalence PASS); Tighe accepted it on real Genesis hardware; and
it is the last accepted baseline **before** the HUD/vertical-framing campaign began. 0435 begins the
restoration campaign and its `_full_hud` is incomplete; 0436/0437 are unaccepted vertical-origin
experiments.

**Builds 0435, 0436, 0437 must NOT be deleted, renamed, rewritten, invalidated, or erased.** Their
numbers are consumed forever and their ROM artifacts and reports remain valuable historical and
implementation evidence (per the standing "Every Build Gets a Number" imperative). This deferral is a
forward return to 0434's *implementation*, not an erasure of later history.

---

## 2. Locked historical results

All rope figures are the established **GENESIS NTSC MAME** deterministic rope-attach benchmark
(3 trials, deterministic). Arcade silver standard = **771 fr / 12,850.000 ms**.

| Build | Canonical | `_full_hud` | Full-HUD penalty | Notes |
|---|---:|---:|---|---|
| 0434 | 803 / 13,400.588 ms | — (`_full_hud` artifact = 803, **not a valid full-HUD baseline** — HUD not actually present) | — | **Accepted by Tighe on real Genesis. Intended return baseline.** |
| 0435 | 803 / 13,400.588 ms | 854 / 14,251.684 ms | +51 fr / +851.096 ms / +6.351% | Restored **upper** gameplay HUD only; lower HUD absent → NOT a complete full HUD. |
| 0436 | 807 / 13,467.341 ms | 861 / 14,368.501 ms | +54 fr / +901.160 ms / +6.691% | Independent frontend/gameplay origins via **runtime** `native_active_y_origin`. Architecture **rejected**. |
| 0437 | 806 / 13,450.653 ms | 859 / 14,335.125 ms | — | Removed runtime origin state; **compile-time** immediates. Regression **reduced, not eliminated**. |

ROM artifacts (all 2,698,936 bytes; canonical SHA-256):

- 0434 `178838c4eed65f920a78718c63fe1086e55ab0aeb567177f2918898b0ac1d5ca`
- 0435 `eb6c27991ca49ef49c13c3da9a1b9b3f869455c43d57c4518629e3737f6a31c2` (`_full_hud` `14a14317512e0305096a9ad2061430c0a3a0b1915a170265434fa84775773a04`)
- 0436 `af98cd46add652b031d22c11af4655387a655ada596b9a190ab746f0ad8d3dd0` (`_full_hud` `aca6f611bbc6414ea7b49976527feb765d69a560752c394518d033412e0c597a`)
- 0437 `cadfef11f2e87621d087874335f03278041665acbeec79cadb10a57dfdd1d2e1` (`_full_hud` `c8bd7ca39a719ad2645a4264f45932fcf59a78403fc5389f047b9869ee277a36`)

### 0435→0437 regression isolation (proven)

Per `Cody_0435_vs_0437_remaining_rope_regression_isolation.md`, the residual deterministic rope
regression is **owned by the Build-0437 native SAT-origin hot path**, not by the Plane A/B change:

- SAT pass entry: **+8 cycles / gameplay `pc090oj_native_emit_pass` invocation** (0435 `beq.w`
  taken = 10c; 0437 `bne.s`+`bra.w` = 18c). Pass-count dependent.
- SAT per-piece Y realization (duplicated bit-14 fixed-screen test + selection branches):
  **+20 cycles / ordinary piece**, **+28 cycles / bit-14 fixed-HUD piece**. Sprite-count dependent;
  full HUD emits more bit-14 pieces → amplifies the loss from +3 to +5 frames.
- Plane A/B `ADDQ.W #8,D0` → `ADDI.W #8,D0`: **+4 cycles each, +8 cycles per complete scroll
  commit**, once per VBlank. Real static cost but **did not account for a measurable rope frame**.
- **Control A** (unnumbered): restoring *only* the 0435 SAT pass-entry + per-piece instruction shape,
  leaving 0437 Plane A/B intact, returned canonical to **803** and full HUD to **854** — exactly the
  accepted 0435 results. This proves the SAT-origin hot path owns the entire measured regression.
- **Final correction is feasible but deliberately unimplemented:** for equal origins, conditional
  assembly can emit the exact 0435 runtime shape (single `ADDI.W #-origin,D2`; `ADDQ.W #origin,D0`
  where 1..8) while keeping both Makefile constants, with domain-selection branches only in
  unequal-origin builds. No origin RAM, runtime domain branch, or reconvergence branch needed for
  equal origins.

---

## 3. HARD GATE — code preservation before any rollback

> **Documentation alone is NOT preservation.** This document records *why/what/how*. The **actual
> deferred source** is preserved only by a separate Cody Git task (§17).

The required order is **absolute**:

```
CURRENT POST-0437 WORKING TREE
   -> (this) Andy preservation/design document
   -> Cody exact Git code preservation   [branch/ref + commit SHA + file verification + 0434→deferred patch]
   -> VERIFY NOTHING IS MISSING
   -> return active production source to the Build-0434 implementation
   -> continue forward development
```

Production source must **NOT** be returned to Build 0434 until Cody reports **all** of:

- 0435 source changes recoverable: YES
- 0436 source changes recoverable: YES
- 0437 source changes recoverable: YES
- post-0437 isolation/research changes recoverable: YES
- preservation verified before rollback: YES

Recommended preservation ref: **`archive/deferred-hud-framing-0437`** (rename only if it already
exists). Forbidden as "preservation": `git stash`, reflog, destructive `clean`, history-erasing
`reset`, or any plan to manually reconstruct this work later.

---

## 4. Git / code-history provenance — CRITICAL FINDING

Read-only inspection (`git status`, `git log --all`, `git branch -a`, `git diff --stat HEAD`,
`git tag`, `git ls-files`) establishes the following. **This materially changes the shape of the
preservation task.**

| Fact | Value |
|---|---|
| Current branch | `rastan-direct-proposal` |
| Current HEAD | `9982f7cd70581d1e1196cc02f33831c3af2be006` — commit message **"Build 426"** |
| Tags | **none** (0 tags in repo) |
| Build-0434 Git reference | **NOT IDENTIFIED — no commit or tag for 0434** |
| Build-0435 Git reference | **NOT IDENTIFIED — no commit or tag for 0435** |
| Build-0436 Git reference | **NOT IDENTIFIED — no commit or tag for 0436** |
| Build-0437 Git reference | **NOT IDENTIFIED — no commit or tag for 0437** |

**The highest numbered commit in history is "Build 426."** Builds **0427 through 0437** — including
the entire Build-0428 player-native work, the Build-0433/0434 vertical optimization, and the
Build-0435/0436/0437 HUD/framing campaign — exist **only as uncommitted working-tree modifications on
top of HEAD (Build 426)**. The working tree vs HEAD differs by 44 files (the large insertion/deletion
count is dominated by regenerated artifacts such as disassembly/address-map/manifests).

**Consequences the preservation task MUST account for (do not guess around these):**

1. There is **no commit to `git checkout` for Build 0434**. "Return to the Build-0434 implementation"
   is a **source reconstruction**, not a checkout. It means reversing the 0435/0436/0437 source edits
   within the co-mingled working tree while preserving the 0427–0434 work that is also uncommitted.
2. The 0435/0436/0437 deferred work is **not git-separable from 0427–0434** today; all of it is one
   uncommitted blob. The preservation ref must therefore first capture the **entire current working
   tree** (which = Build 0437 state) so nothing from 0427–0437 is lost.
3. The authoritative guide for reconstructing 0434 source from the 0437 tree is the per-build reports
   (§5), which give exact, localized deltas: 0435 added Mode-1 HUD code (canonical Mode-2 bytes
   identical to 0434 except header checksum + build string); 0436 added the origin constants/runtime
   word; 0437 replaced that with compile-time immediates. The reverse of 0435+0436+0437's source
   edits yields the 0434 implementation.
4. `build/rastan-direct/build_counter.txt` = **437** (verified). The counter is correct and must not
   be rolled back; a forward production build that restores the 0434 implementation takes the **next**
   number (0438+). 0435–0437 numbers remain consumed and must never be reused.

---

## 5. Per-build implementation history

### Build 0434 — accepted baseline (general vertical-scroll optimization)

Source: `Cody_general_vertical_scroll_player_hud_optimization.md` (baseline 0433, classification
EXTENDING). Optimized the already-native vertical-row producer: hoisted per-row invariant context
(live source-row pointer, physical staging row base, active residency-LUT base, ring-front column)
out of the sixteen four-cell Plane-A blocks and the Plane-B 64-cell loop; replaced scene-aware
resolver calls with inline active-LUT/miss lookups except the one authoritative ring-seam block.
Removed **124–128 general resolver entries per paired row crossing**; retained all 64 Plane-A and 64
Plane-B logical cells, the seam fallback, miss behavior, dirty bits, DMA, and collision ownership
unchanged. Static equivalence PASS (16,384 tile codes; all rows/cols/ring-fronts; selector-0/1/2).
Files changed: `tilemap_hooks.s`, `fg_tile_cache.s`, `Makefile` (generated-constant dep), gate
`verify_bg_a_incremental_background.py`. Rope 803/803/803 = 0 delta vs 0433. **Accepted by Tighe on
real Genesis.**

### Build 0435 — upper gameplay HUD restoration

Source: `Cody_build0435_genesis_native_full_gameplay_hud_restoration.md` (baseline 0434). Gave
`RASTAN_GAMEPLAY_HUD_SPRITES` its permanent 3-mode contract: `0` suppressed; `1` complete native
gameplay HUD; `2` accepted reduced 1UP/current-score HUD (canonical default). Mode 1 uses retained
arcade score/player/high-score/energy state → purpose-built native HUD tuples → `native_queue_hud` →
existing native SAT finalizer → VDP. It restored the **upper** HUD (1UP/P1, HIGH SCORE, 2UP, plus the
retained `0x05A098` energy/status family) but **NOT the lower arcade HUD**. No PC090OJ object RAM,
records, scanning, or chip-address writes were restored. Mode-2 `.text` proven **byte-identical**
(7,378 bytes, SHA `9824922a…`); whole canonical 0435 differs from 0434 at exactly **two bytes**
(header checksum `0x00018F`; build string `0x2928DB` `0434`→`0435`). New verifier
`verify_gameplay_hud_modes.py` (PASS). `_full_hud` penalty +51 fr / +6.351%. **Visual acceptance
PENDING.**

Score/geometry facts preserved by that report (gameplay template `0x03B950` + `0x03B802` digit
records; active selector `A5+0x002A`; active score `A5+0x011C..0x011E` MSB at `+0x11E`; inactive P1
`A5+0x009C..0x009E`, inactive P2 `A5+0x00DC..0x00DE`; leading-zero suppression rule).

### Build 0436 — runtime-origin split (REJECTED architecture)

Source: `Cody_build0436_vertical_origin_split.md` (baseline 0435). Added two build-time logical
origins `RASTAN_FRONTEND_Y_ORIGIN ?= 8` / `RASTAN_GAMEPLAY_Y_ORIGIN ?= 8` (range 0..224), but
**implemented selection through a runtime WRAM word `native_active_y_origin`** written once per
sprite pass and read per non-fixed sprite; the plane commit likewise selected one domain origin for
both planes. Default 8/8 behaviorally identical to 0435. Scene split: scene 1 → gameplay origin;
scene 0/2 → frontend origin. Top HUD kept bit-14 fixed-screen `-8`, independent of either origin.
Collision/world/camera/rope reference neither origin. Alternate 8/0 compile proof PASS. The
**runtime-state approach was rejected** as the desired architecture (it adds per-sprite RAM work).
Rope: canonical 807 (+4 vs 0435), `_full_hud` 861 (+7). Files changed: `Makefile`,
`pc090oj_hooks.s`, `vdp_comm.s` (+ BSS word), config receipt `out/pc090oj_config.inc`, variant
receipts, `verify-variant-set`.

### Build 0437 — compile-time-origin correction (current source state)

Source: `Cody_build0437_compile_time_vertical_origin.md` (baseline 0436). **Removed the runtime
`native_active_y_origin` word, stores, load, BSS allocation, and symbol completely** (verified absent
from current source, §4). For equal origins, conditional assembly emits one shared `subi.w #8,d2` in
the SAT finalizer and `addi.w #8,d0` in each plane; unequal origins emit tiny per-domain immediate
paths reconverging at `.Lnq_y_origin_ready`. Fixed top-HUD branch keeps `PC090OJ_FIXED_HUD_Y_OFFSET
= -8` before the configurable path. Alternate 8/0 compile proof PASS. Rope reduced vs 0436 (canonical
806, `_full_hud` 859) **but not back to 0435** — regression partially reduced, **not resolved**.
Files changed: `pc090oj_hooks.s`, `vdp_comm.s`. **Current working-tree source = this state**
(verified: `pc090oj_hooks.s:3052-3066`, `vdp_comm.s:365-394` use the `.if RASTAN_FRONTEND_Y_ORIGIN ==
RASTAN_GAMEPLAY_Y_ORIGIN` conditional-assembly shape; `native_active_y_origin` absent).

### Post-0437 — 0435↔0437 regression isolation (no numbered build)

Source: `Cody_0435_vs_0437_remaining_rope_regression_isolation.md`. Analysis + temporary unnumbered
controls only; production source unchanged (remains 0437); counter stays 437. Findings in §2. Key
takeaway: the residual regression is isolated to the SAT-origin hot path and the fix is feasible and
unimplemented.

---

## 6. Deferred implementation code inventory (minimum preservation checklist)

> Cody must still independently inspect Git before preserving/reverting. This is the **minimum**
> list of what the preservation ref must contain and what a 0434 restoration must reverse. All paths
> below are **modified or new in the working tree vs HEAD (Build 426)** and therefore uncommitted.

### Production source (`apps/rastan-direct/src/`, `apps/rastan-direct/Makefile`)

| File | Kind | HUD/framing builds that touched it | Also carries 0427–0434 work? |
|---|---|---|---|
| `apps/rastan-direct/Makefile` | build/configuration | 0435 (expected-delta `-0x1000`→`0`; HUD-mode flag family), 0436 (origin constants + receipts), 0434 (generated-constant dep) | **YES** |
| `apps/rastan-direct/src/pc090oj_hooks.s` | production source | 0435 (Mode-1 full HUD projector), 0436 (runtime origin read), 0437 (compile-time immediates) | likely (earlier sprite work) |
| `apps/rastan-direct/src/vdp_comm.s` | production source | 0436 (plane origin select), 0437 (compile-time plane immediates) | possibly |
| `apps/rastan-direct/src/tilemap_hooks.s` | production source | **0434** vertical optimization | **YES (0434 baseline work — must be KEPT on rollback)** |
| `apps/rastan-direct/src/fg_tile_cache.s` | production source | **0434** vertical optimization | **YES (0434 baseline work — must be KEPT on rollback)** |
| `apps/rastan-direct/src/pc090oj_assets.s` | production source | pre-0435 (0427–0434 range) | **YES** |

> **Rollback caution:** `tilemap_hooks.s` and `fg_tile_cache.s` are the accepted **0434**
> optimization — they must be **retained**, not reverted, when returning to the 0434 implementation.
> Only the 0435/0436/0437-specific edits in `pc090oj_hooks.s`, `vdp_comm.s`, and the Makefile
> HUD/origin additions are the deferred delta. `pc090oj_assets.s` changes predate 0435 and are not
> part of this deferral.

### Generators / verifiers / tooling (`tools/translation/`)

| File | Kind | Status |
|---|---|---|
| `tools/translation/verify_gameplay_hud_modes.py` | verifier (**new, untracked**) | 0435 HUD-mode static proof — **preserve** |
| `tools/translation/verify_bg_a_incremental_background.py` | verifier | 0434 vertical-row equivalence (modified) |
| `tools/translation/postpatch_startup_rom.py` | generator/transformer | modified (range 0427–0437; verify before assuming HUD-specific) |
| `tools/translation/precompute_pc090oj_frame_table.py` | generator | modified |
| `tools/translation/verify_canonical_rom.py` | verifier | modified (1-line) |
| `tools/translation/verify_pc090oj_direct_dispatch.py` | verifier | modified |
| `tools/translation/verify_pc090oj_frame_table.py` | verifier | modified |

### Generated / reproducible artifacts (regenerate from source; preserve for exactness anyway)

`apps/rastan-direct/out/pc090oj_config.inc` (origin + HUD receipts), `out/full_hud_patch_manifest.json`
(**new**), `out/variant_configs/` (**new dir**), `out/*.o`, `out/*.elf`, `out/symbol.txt`,
`out/address_map.json`, `out/*_patch_manifest.json`, `build/rastan-direct/*`,
`build/genesis_postpatch.disasm.txt`. These are build outputs; they must not be hand-edited, but the
preservation ref should capture them so the exact deferred state is byte-reproducible.

### Documentation (preserve; these ARE the recovery knowledge)

`docs/design/Cody_build0435_genesis_native_full_gameplay_hud_restoration.md`,
`Cody_build0436_vertical_origin_split.md`, `Cody_build0437_compile_time_vertical_origin.md`,
`Cody_0435_vs_0437_remaining_rope_regression_isolation.md`,
`Cody_general_vertical_scroll_player_hud_optimization.md`,
`Andy_vertical_origin_history_and_buildtime_constantization.md`,
`Andy_full_gameplay_hud_native_restoration_contract.md`, `Andy_hud_suppression_history_audit.md`,
`Cody_arcade_bottom_hud_lives_round_decompilation.md`,
`Cody_arcade_bottom_hud_energy_item_decompilation.md`,
`Cody_status_sprite_5a098_native_conversion.md`, and this document (all currently untracked).

### Decompilation evidence (lower-HUD semantics)

`analysis/decompilation/c/rastan_player_hud.c` (**new**) and raws
`analysis/decompilation/c/raw/{0003a6b2,0003a860,0003b802,0003bb48,00042abc,00044804,0004527e,0005100a,00059f92,0005a098}.c`
(**new**). These encode the recovered lower-HUD semantics (§7) and must be preserved.

### Benchmark / trace evidence (`states/traces/`)

`build0435_rope_attach_benchmark_reduced_hud/`, `build0435_rope_attach_benchmark_full_hud/`,
`build0436_rope_attach_benchmark_reduced_hud/`, `build0436_rope_attach_benchmark_full_hud/`,
`build0437_origin_isolation_A/`, `build0437_origin_isolation_A_full_hud/`, and the fixed 30s MAME
traces for 0434–0437. Also the aggregate `states/traces/historical_rope_benchmark/` now carries
0420–0437 canonical and 0434–0437 `_full_hud` rows.

---

## 7. Full lower-HUD semantics to preserve (arcade authoritative)

All coordinates below are **raw arcade PC090OJ** coordinates; every piece is 16×16; `event` = shown
on init/show/award/round-transition, **not** per-frame. Source:
`Cody_arcade_bottom_hud_lives_round_decompilation.md` (Pass 2) + energy/item Pass 1. This is the
complete lower gameplay HUD that Build 0435 did **not** restore.

### Reserve lives (one piece)

- Source: low byte of active player word `A5+0x0102` (read as byte `A5+0x0103`), selector 4.
- Producer: `0x3B802` (digit family). Raw **Y=0xE4**, raw **X=0x00**, control `0x0000`,
  code `0x002A + (reserve & 0x0F)`.
- Semantics: it is a **reserve** count (allotment − 1): a 3-life allotment displays `2`. Reserve 0 is
  a visible `0` (not blanked). Y-high byte `0` = visible, `1` = hidden. Extra-life path
  `0x3B798/0x3B79C` increments and refreshes selector 4. Group template `0x3B984`; restore/refresh
  `0x3B8EE`; show/hide owner `0x3B902` (`D1=0` show, `D1=1` hide records 17..21). Shown via
  `0x3A64C` when `A5+0x0034 != 0`. **Event-driven, not per-frame.**

### Energy / status (`0x05A098` family, raw Y=0xE8)

| Element | Source | Raw X | Code |
|---|---|---:|---|
| indicator | `A5+0x12A4/0x12A6/0x1306/0x130A` | `0x10` | `0x03CA/0x03CB` |
| left cap | `A5+0x12FC == 1` | `0x20` | `0x03CC` |
| energy cell 0 | high byte `A5+0x013A` | `0x30` | `0x03CD` / partial / `0x03D5` |
| energy cells 1..5 | same `A5+0x013A` | `0x40,0x50,0x60,0x70,0x80` | same family |

Preserve full/partial/empty tile semantics, low-cell **blink**, lifecycle, and sound transitions from
`Cody_status_sprite_5a098_native_conversion.md`. **This family IS already restored natively in Build
0435 Mode 1** (producer naturally reachable from `0x051054`, runtime-mapped `0x051254`; Mode 1
reserves queue entries 5..12). It is listed here for completeness of the lower-HUD row at Y=0xE8.

### Four pickup / status slots (producer `0x59F92`, all raw Y=0xE8)

| Slot | Source | Raw X | Code | Local attr | Visibility |
|---|---|---:|---|---:|---|
| 0 | `A5+0x1388` | `0xA0` | `0x0A6A..0x0A6D` | `0x0003` | source 0..3; hidden at `0xFF` |
| 1 | `A5+0x140E` | `0xB0` | `0x0A68` | `0x0080` | visible unless `0xFF` |
| 2 | `A5+0x1410` | `0xC0` | `0x0A66` | `0x0080` | visible unless `0xFF` |
| 3 | `A5+0x140C` | `0xD0` | `0x0A64` | `0x0080` | visible unless `0xFF` |

Slots are independent and may coexist. `0x59F92` output is semantically selected before being placed
in chip-shaped WRAM records — a future Genesis implementation reproduces the **semantic** selection,
not that intermediary.

### Persistent ROUND (PC090OJ — NOT the PC080SN ROUND/READY transition text)

- Fixed label pieces (template `0x3B984`): `(X=0x100, Y=0xE8, code 0x0034)`,
  `(X=0x110, 0xE8, 0x0035)`, `(X=0x120, 0xE8, 0x0036)`, all control `0x0000`.
- Digit (selector 3 at `0x3B89C`): `X=0x128, Y=0xE8`, code `0x002A + low-nibble(A5+0x0117)`,
  control `0x0000`; zero not blanked.
- Stage state: authoritative `A5+0x0118`; display mirror `A5+0x0117`. One-based init at
  `0x4527E..0x4529A` (`((~word[0x5FF9E]) & 7) + 1`); increment `0x3A878/0x3A87C`; at 7 the display
  mirror is forced back to 6 (`0x3A888`); ordinary displayed range 1..6.
- **Do not confuse** with the round-start `ROUND … READY` **PC080SN/text** overlay (descriptor
  `0x3C16E`, name cells row 12 cols 18..22, digit at row 12 col 24, text selectors 55/56, PLAYER 1/2
  READY selectors 4/5) built once by the transition state.

---

## 8. 240-line arcade vs 224-line Genesis geometry

Preserve the fundamental fact (source `Andy_vertical_origin_history_and_buildtime_constantization.md`
§2; arcade `rastan.cpp set_visarea 8..247`):

- Arcade visible raster = **Y 8..247 inclusive = 240 lines**.
- Genesis target = **224 lines**. **Do NOT propose a 240-line Genesis mode.** The problem is purely
  *which 224-line window of the 240-line arcade composition* gameplay presents.
- Historical frontend framing: **origin = 8** maps arcade 8 → Genesis 0 and shows arcade ~8..231.
  **Good for title/attract; remains the frontend default.** But it **drops the bottom** of the
  composition.
- Consequence for the lower HUD (current origin 8), per the decomp report's mapping table:

| Component | Arcade raw Y | Current mapped Y (origin 8) | Result |
|---|---:|---:|---|
| reserve-lives digit | `0xE4` (228) | `0xDC` (220) | only top 4 of 16 lines in-frame |
| energy / pickups / ROUND | `0xE8` (232) | `0xE0` (224) | **outside** the 0..223 viewport |

This is exactly why the lower arcade gameplay HUD disappears at origin 8.

---

## 9. Desired gameplay framing (FUTURE CANDIDATE — not accepted)

Tighe's explicit desire: **preserve the bottom of the arcade 240-line image; if cropping is needed,
crop the TOP during gameplay.** The exact bottom-aligned 224-line window is **arcade 24..247 →
Genesis 0..223**, i.e.:

- `RASTAN_GAMEPLAY_Y_ORIGIN = 24` (candidate), while `RASTAN_FRONTEND_Y_ORIGIN = 8` (unchanged).
- Lower HUD then fits: energy/pickups/ROUND `0xE8 (232) − 24 = 208` → occupies **208..223** exactly;
  reserve lives `0xE4 (228) − 24 = 204` → **204..219**, fully in-frame.

**Origin 24 is recorded as a FUTURE CANDIDATE only.** No real-Genesis acceptance of gameplay origin
24 has occurred. Produce unnumbered candidates (origin 16 / 20 / 24, frontend 8) for Tighe's
real-hardware visual selection before any numbered build.

---

## 10. Critical future performance requirement (stronger than before)

The 0436/0437 implementation approach is **not** the desired final architecture. The requirement is
now stronger than "origin selection happens at compile time":

> **Changing the build-time vertical framing must not increase runtime instruction count in the
> normal native sprite hot path.** The Genesis 68000 must not perform per-sprite presentation-origin
> arithmetic that is statically knowable at build time — and more broadly, it must not perform
> coordinate arithmetic the original arcade 68000 did not perform merely because the original PC090OJ
> hardware handled that presentation transform.

Target: **zero additional per-sprite runtime coordinate instructions** solely for frontend/gameplay
framing. The 0437 residual (the +8/pass, +20/piece, +28/HUD-piece bit-14 duplication) violates this
even at equal origins; the isolation report's feasible equal-origin shape (§2) is the minimum bar,
and the future audit (§12) should push further toward folding the fixed framing into already-required
work or generated data.

---

## 11. Offline / generated-data opportunity

The project already precomputes native sprite presentation data offline (piece geometry,
orientation-specific dx/dy, finalized pattern identity, invariant attributes, native frame records).
Future work should investigate folding **statically known** presentation work into generated records,
already-required coordinate additions, final baked SAT constants, or clip constants — rather than
executing separate runtime arithmetic.

**Caution:** do **not** simply offset every generated `dy` by −24. `dy` is **relative frame
geometry**; gameplay origin is a **presentation/window** property. Before implementing, prove exactly
where fixed presentation constants can be folded while preserving the distinction between: actor/world
Y, relative piece geometry, viewport framing, and Genesis SAT coordinates.

---

## 12. FUTURE FIRST TASK — arcade-vs-Genesis coordinate-cost audit (READ-ONLY)

When this work resumes, the **first** task is read-only. Compare original arcade 68000
sprite-coordinate work against current Genesis native sprite-coordinate work, classifying every
runtime Y-coordinate operation as one of: original arcade CPU semantic work · work formerly done by
PC090OJ hardware · Genesis SAT-format requirement · Genesis 224-line crop/framing requirement ·
accidental translation-layer overhead · still genuinely dynamic.

Pay special attention to: actor base Y, camera Y, generated piece `dy`, 9-bit wrapping/sign handling,
PC090OJ flip/inversion, gameplay viewport crop, Genesis SAT `+0x80` coordinate convention, and opaque
bounding-box clipping. **Goal:** identify which operations can be baked into generated records, folded
into an already-required operation, replaced by build-time constants, or removed entirely. **Do not
implement until this classification is complete.**

### Ideal future hot-path target (TARGET, not proven)

For a proven native gameplay piece, the ideal runtime Y path approaches:

```
arcade-equivalent dynamic base Y  +  generated final native relative Y  ->  final Genesis SAT Y
```

with piece geometry, orientation, fixed gameplay framing, fixed SAT convention, and the fixed
viewport relationship precomputed. Changing `RASTAN_GAMEPLAY_Y_ORIGIN` from 16 to 24 should alter
generated/build-time data and constants but **add no runtime instructions** to the normal gameplay
sprite hot path.

---

## 13. Top HUD is a separate presentation domain (preserve)

The top HUD (1UP, P1 score, HIGH SCORE, 2UP) is **native screen-fixed presentation** and must **not**
move with gameplay framing. It takes the finalizer's bit-14 fixed-screen marker and keeps
`PC090OJ_FIXED_HUD_Y_OFFSET = -8`. Top-HUD coordinates must not depend on either configurable origin.
The **lower** arcade HUD, by contrast, is part of the arcade gameplay composition and **follows
gameplay framing** (inherits `screen_y = rawY − RASTAN_GAMEPLAY_Y_ORIGIN`).

---

## 14. Background / VSRAM question (analyze before implementing)

Do not assume an extra `ADDI #24` per plane is the final architecture just because its cost is small
(the 0437 Plane A/B `ADDQ`→`ADDI` already cost +8c/scroll commit without owning a rope frame). When
resuming, compare the original arcade scroll-producing CPU work against the Genesis VSRAM realization
and determine whether the build-time gameplay origin can be folded into an already-required scroll
calculation/representation without adding an operation. If an added operation is genuinely required by
the Genesis hardware contract, document exactly why. **Analyze first, implement second.**

---

## 15. What must not be lost

Builds 0435/0436/0437 and the post-0437 isolation are **not dead ends**. They established:

- upper-HUD semantics and native restoration behavior (0435);
- that lower-HUD visibility is fundamentally a **viewport/framing** problem, not a producer problem;
- that frontend and gameplay need **independently selectable** framing;
- that runtime origin RAM state is **unnecessary** (0436 rejected → 0437);
- that compile-time configuration is **viable** (0437);
- that careless compile-time splitting **still** adds per-piece overhead (the 0437 residual);
- that the SAT hot-path overhead **explains** the measured 0435→0437 regression (isolation);
- that an equal-origin control returned **exactly** to 803/854;
- that the likely bottom-aligned gameplay candidate is **origin 24**;
- that a **zero-extra-runtime-coordinate-work** architecture is the desired bar.

The **source** implementing these experiments must remain recoverable — hence §3/§17.

---

## 16. (reserved)

---

## 17. Mandatory future code-preservation step (separate Cody task)

Before any return to Build 0434 production source, a separate Cody task must:

1. Inspect `git status`, `git diff`, `git diff --cached`, and relevant untracked files (note §4: the
   deferred work is **entirely uncommitted** on top of HEAD "Build 426"; there are no 0427–0437
   commits or tags).
2. Identify the exact current deferred implementation state (= Build 0437 working tree).
3. Create a durable preservation Git branch/ref, preferably **`archive/deferred-hud-framing-0437`**.
4. Commit all relevant current uncommitted implementation/research state onto that ref — **the whole
   working tree (0427–0437), since none of it is committed** — so nothing is lost.
5. Record the exact preservation commit SHA.
6. Verify every file in §6 is recoverable from that preservation point.
7. Generate an exact Git-derived patch from the Build-0434 implementation to the preserved deferred
   implementation, preferred path **`docs/design/deferred_hud_framing_0434_to_0437.patch`**. (Because
   0434 is not a commit — §4 — Cody must first reconstruct the 0434 source reference by reversing the
   localized 0435/0436/0437 edits per §5, keeping the 0427–0434 work, then diff.)
8. Update **this** document with: preservation branch/ref, preservation commit SHA, the Build-0434
   reference actually used, the patch path, and the verified changed-file inventory.
9. **STOP if anything relevant is missing.**

Forbidden as preservation: `stash`, reflog, destructive `clean`, history-erasing `reset`, or manual
future reconstruction.

### Filled in by the Cody preservation / Build-0438 rebaseline task

- Preservation branch/ref: `archive/deferred-hud-framing-0437`.
- Original complete deferred-state commit SHA:
  `8b0d8659f5a62a70b11af0c92af0d57fee0e527b`.
- Final archive HEAD (adds only the safety artifact):
  `5a886bb4cbd9e9b5f45bf1c5496d17d480201b83`.
- Build-0434 reference used: selectively reconstructed by reversing only the documented
  0435 Mode-1 HUD and 0436/0437 origin deltas while retaining all 0427–0434 source. The resulting
  Build-0438 canonical and `_full_hud` ROMs are each byte-identical to their preserved Build-0434
  counterparts except the header checksum and build-string byte.
- Secondary safety patch: `docs/design/deferred_hud_framing_preserved_state.patch`, SHA-256
  `ce1c69d896fb7780cf2af3fe5c0b1ec8ff5a6b205693832bda13ecb89c4b4033`. This is accurately the
  Git-derived Build-0426-base-to-complete-deferred-state diff, not a claimed 0434 commit diff;
  the archive branch is authoritative.
- Verified changed-file inventory confirmed: **YES**. Production source, generators/verifiers,
  decompilation/research, reports, AGENTS_LOG history, generated state, canonical and `_full_hud`
  ROMs for 0434–0437, fixed traces, rope benchmarks, and post-0437 isolation evidence are all
  recoverable from the archive.

---

## 18. Return-to-baseline plan

```
CURRENT POST-0437 WORKING TREE (uncommitted; counter=437)
   -> Andy preservation/design document (this file)          [DONE]
   -> Cody exact Git code preservation                        [REQUIRED, not yet done]
        - preservation branch/ref (archive/deferred-hud-framing-0437)
        - preservation commit SHA
        - complete §6 file verification
        - exact 0434 -> deferred patch
   -> VERIFY NOTHING IS MISSING
   -> forward production change restoring the Build-0434 implementation (next number 0438+)
   -> future development
```

Preferred historical shape: `0434 accepted → 0435 HUD → 0436 runtime-origin → 0437 compile-time →
post-0437 isolation → exact deferred preservation point → forward change restoring 0434 → future`.
Build numbers **0435–0437 remain historical and must never be reused.** Do not delete later history,
delete branches, pretend 0435–0437 never existed, rely on stash/reflog, or plan manual reconstruction.

---

## 19. WHEN THIS WORK RESUMES

1. Start from the then-current accepted production baseline descended from the restored 0434
   implementation.
2. Re-read this document and all cited reports (§ "Source material").
3. Locate and verify the preserved Git recovery point (`archive/deferred-hud-framing-0437` + SHA).
4. Use the preserved source as the implementation reference.
5. Perform the read-only **arcade-vs-Genesis coordinate-cost audit** (§12) — first.
6. Freeze the **minimum-runtime** framing architecture (§10): zero extra per-sprite runtime
   coordinate instructions wherever statically possible.
7. Restore the complete native **lower-HUD** semantics from §7 / the decompilation — **without**
   resurrecting PC090OJ object RAM, records, scanning, or chip-address writes.
8. Produce **unnumbered** framing candidates: gameplay origin 16 / 20 / 24, frontend origin 8.
9. Require build-time framing to add **zero** per-sprite runtime coordinate instructions where
   statically possible (apply the isolation report's feasible equal-origin shape, §2, as the floor).
10. Tighe performs real-Genesis visual framing selection.
11. Only after framing is selected, perform performance validation.
12. Require **no regression** vs the appropriate clean baseline except costs proven unavoidable from
    actually rendering additional HUD content.
13. Number a production build **only after** architecture, presentation, and performance are accepted.

---

## Source material read for this task

Read in full: `Cody_build0435_genesis_native_full_gameplay_hud_restoration.md`,
`Cody_build0436_vertical_origin_split.md`, `Cody_build0437_compile_time_vertical_origin.md`,
`Cody_0435_vs_0437_remaining_rope_regression_isolation.md`,
`Cody_general_vertical_scroll_player_hud_optimization.md`,
`Andy_vertical_origin_history_and_buildtime_constantization.md`,
`Cody_arcade_bottom_hud_lives_round_decompilation.md`. Consulted: `AGENTS_LOG.md`, current working-tree
source (`apps/rastan-direct/Makefile`, `src/pc090oj_hooks.s`, `src/vdp_comm.s`), read-only Git
(`status`/`log --all`/`branch -a`/`diff --stat HEAD`/`tag`), `build/rastan-direct/build_counter.txt`,
and `dist/rastan-direct/` ROM identities. Related (not re-read in full):
`Andy_full_gameplay_hud_native_restoration_contract.md`, `Andy_hud_suppression_history_audit.md`,
`Cody_arcade_bottom_hud_energy_item_decompilation.md`, `Cody_status_sprite_5a098_native_conversion.md`.

**Tool reuse (RULES §18):** Existing project tools reused — read-only `git`, repository design reports,
current source. New tooling created — none. Why new tooling necessary — not applicable (read-only
preservation/planning task).

**Production modified: NO. Makefile/generators/verifiers modified: NO. ROM built: NO. MAME run: NO.
Rope benchmark run: NO. Build number consumed: NO. Build counter changed: NO. Git branch/commit/tag:
NO. Phase D: NO. Phase E: NO.**
