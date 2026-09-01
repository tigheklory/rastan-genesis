# Andy — Test-Palette → R1/P1 Layer-A Production Path: Pre-Implementation Requirements

**Type:** Analysis / requirements review. No implementation, no ROM. Build 0324 baseline.

## 1. Phase 0

**Relevant KNOWN_FINDINGS / HIGH rediscovery hazards**
- **KF-043 (durable palette-ownership rule):** current gameplay CRAM ownership is bank 48→**Line 2**, bank 51 (sprites)→**Line 3**. So **Line 3 is presently the sprite palette.** Putting Layer-A on Line 3 (the Test-profile target) requires relocating the sprite palette off Line 3. This is the single biggest hazard/scope tension.
- **KF (Build 0173/0174 FG palette lifetime):** the Stage-1 FG terrain bank (arcade `0x0003`) can be converted, but its Genesis carrier line **does not survive to gameplay** — frontend `0x59AD4` line writes overwrite it. Any shared Layer-A line must be re-asserted at the gameplay boundary (the existing `fg_bank3` carrier/re-assert path is the mechanism). Do not rediscover this as a tile/LUT/row-depth failure.
- **KF-042/044 raw-WRAM immediate class** — unrelated here; no action.

**Deferred:** vertical-scroll / wrong-tile suspicion (OPEN, deferred until colors are sane). Not in scope.

**Classification:** EXTENDING (continues the Build 0315–0324 offline Palette-Composer Layer-A line).
**Issues touched:** none changed (analysis only). Related: OPEN palette-lifetime item, KF-043.
**Contradiction status:** one architectural contradiction to resolve — **Test profile designates Layer-A → Line 3, but the runtime currently uses Line 1 as the FG carrier and Line 3 for sprites.**

## 2. Existing inputs (already in repo — do NOT re-request)

| Input | Location | Status |
|---|---|---|
| Frozen Test profile | `build/rastan-direct/build0314/Test.snapshot.json` | SHA `deb696452d7456b3…`; 1576 usage maps; `target_palette_lines`, `line_owners`, `reserved_lines`=[2] |
| Authored **Line-3** palette (authority) | `Test.snapshot.json` `target_palette_lines[3]` | `[_,0x028C,0x044C,0x0026,0x0004,0x0002,0x0424,0x0624,0x0402,0x0202,0x0200,0x0422,0x0440,0x0660,0x0AA6,0x0884]` |
| Line ownership | `Test.snapshot.json` `line_owners` | 0,1,3 = editor-editable; **2 = Layer B, arcade, PROTECTED** |
| Assembly Layer-A palette table | `palette_hooks.s:482 editor_layera_palette` | **Byte-exact match** to Test Line-3 palette (confirmed) |
| Per-usage index maps | `Test.snapshot.json` `context_policies[gameplay.r01.p01].plane_usage_palette_mappings` (1576) | e.g. LA-0458 |
| Source arcade patterns | `build/regions/pc080sn.bin` | raw 8×8 4bpp @ code*32 |
| Authoritative Layer-A segment map | `tools/graphics_editor/server.py::layera_map(seg)` (from `maincpu.bin` tables) | per-cell (code,bank,hf,vf); same source the tool renders |
| Offline per-usage transformer | `tools/graphics_editor/compile_editor_layera.py` | emits `line3_cram.bin`, `layera_patterns.bin`, `manifest.json`; targets `target_palette_lines[3]` |
| Production region (Build 0324) | `build/regions/pc080sn_editor_layera.bin` via `gen_reindexed_region.py` | code-indexed, dominant-map collapse |
| Boundary/package compiler | `tools/translation/compile_pc080sn_genesis.py` | code-keyed slot allocation |
| Runtime routing/staging | `palette_hooks.s` (`palette_route_table`, `.L59`, `fg_bank3_line_cache`), `vdp_comm.s` | Line-1 carrier model |
| Runtime symbols | `apps/rastan-direct/out/symbol.txt` | `staged_fg_buffer` 0xFF50E4, `staged_palette_words` 0xFF60E4, publishers |
| Cave save states | `~/.mame/sta/genesis/quick.sta`, `~/.mame/sta/rastan/quick.sta` | after-drop cave frame |
| Address map | `build/rastan-direct/address_map.json` | arcade↔genesis pc |

## 3. First cave proof usage (identified)

- **usage / stable id:** `LA-0458`
- **source tile code:** `0x070`
- **source palette bank:** `0x004` (cave-interior rock)
- **Test index_map:** `{1→9, 2→11, 3→6}` (source pixel index → Line-3 target entry); **single-map** for this code (no dominant-collapse ambiguity)
- **expected final 32-byte pattern:** sha `888a34a5fc2e5272`, hex `66669999666699996669b9996699b999699bb999999bbb9999bbbb999bbbbbb9` — **already byte-present** in `pc080sn_editor_layera.bin` at code 0x70 (verified match)
- **expected target line:** **Line 3** (Test profile)
- **target palette authority:** `Test.snapshot.json target_palette_lines[3]` (= `editor_layera_palette`). Entries 9/11/6 = `0x0202 / 0x0422 / 0x0424` → dark purple/mauve cave rock.

## 4. Current Build-0324 chain for LA-0458

| # | Stage | Status | Evidence |
|---|---|---|---|
| 1 | Source semantic usage | **CORRECT** | code 0x70/bank 0x4 present in records [1,2,7,8] |
| 2 | Test mapping lookup | **CORRECT** | `{1:9,2:11,3:6}`, single-map |
| 3 | Offline final pattern | **CORRECT (this usage)** | region bytes == expected `888a34a5`. *General caveat:* `gen_reindexed_region.py` collapses multi-`(code,bank)` codes to the dominant map (PROVEN BROKEN class, though not for code 0x70) |
| 4 | Pattern/package residency | **NOT YET PROVEN** | boundary reads the reindexed region (Build 0316), but the specific slot's residency in the cave epoch for code 0x70 is unverified |
| 5 | Runtime target selection | **CORRECT (single-map) / BROKEN (general)** | code→slot delivers the right pattern for single-map codes; no `(code,bank)` selection for multi-map |
| 6 | Plane-A palette-line bits | **PROVEN BROKEN** | `.Lplane_a_native_attr_from_word`: only arcade bank 3 routes to the carrier; bank 0x4 → `bank&3` → **Line 0** (green). Shared-Layer-A-line model not implemented |
| 7 | Line-3 CRAM staging | **PROVEN BROKEN** | `editor_layera_palette` is staged into `fg_bank3_line_cache` = **Line 1** (carrier), gated on `fg_bank3_route_seen`; **Line 3 currently holds sprite bank 51 (KF-043)**. Values are correct; physical line and reachability are wrong |

**First real divergence:** stage 6/7 — routing + carrier line. Stages 1–3 are correct for the proof usage. The green cave rock is fully explained by (6) bank 0x4 → Line 0 and (7) the editor palette living on Line 1 (bank-3-gated), not on a line the cave rock reaches.

## 5. Required implementation authorization (for the next prompt)

The next implementation prompt MUST explicitly authorize:

1. **Shared-Layer-A-line routing (the core fix):** route **all** R1/P1 Layer-A FG source banks (0x3,0x4,0x5,0x6,0x7,0x17,0x18,0x1A–0x1D) to **one** shared Layer-A target line — a single rule, removing the `bank & 3` fallback. **Not** per-bank `bank→line` routing (that is the forbidden hybrid).
2. **Carrier-line reconciliation (decision required):** the Test profile designates **Line 3**; the runtime currently uses **Line 1** as the FG carrier and **Line 3 for sprites (KF-043)**. Choose one:
   - (a) **Adopt Line 3** per profile + Tighe's plan → this **requires relocating the sprite palette (bank 51) off Line 3** (to lines 0/1). That makes bounded sprite-palette line work **in scope** and must be authorized explicitly (it collides with "unrelated sprite work out of scope").
   - (b) **Keep Line 1** as the shared Layer-A carrier for the proof (values already staged there) and treat the profile's "Line 3" as slot identity, deferring the sprite move. Lower risk; not the final line plan.
3. **Line CRAM staging + survival:** stage the shared line's CRAM from the frozen Test profile and **re-assert it at the gameplay boundary** so frontend `0x59AD4` writes don't overwrite it (KF Build-0174 hazard); reuse the existing carrier/re-assert path.
4. **Full `(code,bank)` target-pattern generation:** REQUIRED **in general** to replace the code-indexed dominant region (multi-map codes). The **cave proof code 0x70 is single-map**, so the cave can be proven end-to-end **without** full `(code,bank)` — authorize whether the first proof isolates routing/staging (recommended) and defers `(code,bank)` generation + bank-aware O(1) runtime selection to the follow-up.
5. **Build-system + provenance:** any new offline artifact (e.g. a faithful `(code,bank)` pattern set) becomes a normal Make dependency with recorded SHA, mirroring the Build-0324 reuse-policy pattern.

## 6. Must remain out of scope
`specs/pattern_reuse_policy.json` (approved Segment-11 substitutions); Layer B / Line 2 (protected); vertical scrolling; gameplay/collision; later rounds/phases; sprite work **except** the specific Line-3-freeing relocation if option 5.2(a) is chosen.

## 7. User-driven evidence required
**None before implementation.** All offline inputs exist; the cave `(code,bank)` chain is verifiable statically; the existing Genesis cave save state supports before/after runtime verification. Post-implementation in-game verification (playing to the cave) is a separate step.

## 8. Blockers / STOP conditions
No hard blocker. One decision gate: **the Line-3-vs-Line-1 carrier choice (5.2)**, because Line 3 currently belongs to sprites (KF-043) and choosing Line 3 pulls a bounded sprite-palette relocation into scope. This must be decided in the implementation prompt, not discovered mid-build.
